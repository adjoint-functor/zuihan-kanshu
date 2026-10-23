#!/usr/bin/env python3
"""Check and restore a disposable Work runtime for Chinese mathematics PDFs."""

from __future__ import annotations

import argparse
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tarfile
import urllib.request
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets" / "pdf-environment"
BASELINE = json.loads((ASSETS / "baseline.json").read_text(encoding="utf-8"))
TEX_TOOLS = ("xelatex", "latexmk", "kpsewhich")
FONT_TOOLS = ("fc-match", "fc-list")
PDF_TOOLS = ("pdfinfo", "pdffonts", "pdftotext", "pdftoppm")
TOOLS = ("pandoc", *TEX_TOOLS, *FONT_TOOLS, *PDF_TOOLS)
SCHEMA = "pdf-environment/v1"


def run(argv, env=None, cwd=None, timeout=120):
    return subprocess.run(
        [str(x) for x in argv], env=env, cwd=cwd, timeout=timeout,
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )


def require_success(result, label):
    if result.returncode:
        raise RuntimeError(f"{label} failed ({result.returncode}):\n{result.stdout}\n{result.stderr}")
    return result.stdout.strip()


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def load_config(path):
    if path is None:
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema") != SCHEMA:
        raise ValueError(f"unsupported environment configuration: {path}")
    return data


def environment(config):
    env = os.environ.copy()
    env["PATH"] = os.pathsep.join([*config.get("bin_dirs", []), env.get("PATH", "")])
    if config.get("python_paths"):
        env["PYTHONPATH"] = os.pathsep.join(
            [*config["python_paths"], *([env["PYTHONPATH"]] if env.get("PYTHONPATH") else [])]
        )
    env.update(config.get("variables", {}))
    env.update(PYTHONUTF8="1", PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1")
    return env


def python_path(config):
    return config.get("python", sys.executable)


def which(name, env):
    return shutil.which(name, path=env.get("PATH"))


def importable(module, config, env):
    result = run([python_path(config), "-c", f"import {module}; print({module}.__version__)"], env)
    return result.returncode == 0, result.stdout.strip()


def font_path(family, env):
    if not which("fc-match", env):
        return None
    result = run(["fc-match", "-f", "%{family[0]}\n%{file}\n", family], env)
    lines = result.stdout.strip().splitlines()
    return lines[1] if result.returncode == 0 and len(lines) >= 2 and lines[0].casefold() == family.casefold() else None


def tex_file(filename, env):
    flags = ["-engine=xetex"] if filename == "xelatex.fmt" else []
    result = run(["kpsewhich", *flags, filename], env)
    return result.stdout.strip() if result.returncode == 0 else ""


def tex_inventory(env):
    """Describe the selected installation without changing it."""
    result = {"year": None, "core_files": {}}
    if which("xelatex", env):
        version = run(["xelatex", "--version"], env)
        result["version"] = version.stdout.splitlines()[:2]
        match = re.search(r"TeX Live[^\d]*(\d{4})", version.stdout)
        if match:
            result["year"] = int(match.group(1))
    if which("kpsewhich", env):
        for variable in ("TEXMFROOT", "TEXMFDIST", "TEXMFHOME"):
            probe = run(["kpsewhich", "-var-value=" + variable], env)
            result[variable] = probe.stdout.strip() if probe.returncode == 0 else None
        for filename in ("latex.ltx", "expl3.sty", "fontspec.sty"):
            path = tex_file(filename, env)
            item = {"path": path or None}
            if path:
                with Path(path).open(encoding="utf-8", errors="replace") as stream:
                    header = stream.read(65536)
                match = re.search(r"\\(?:Provides\w*\{[^}]+\}|(?:e?def)\\fmtversion)[\s\S]{0,160}", header)
                if match:
                    item["declaration"] = match.group(0)
            result["core_files"][filename] = item
    return result


def cjk_families(env):
    if not which("fc-list", env):
        return []
    result = run(["fc-list", "-f", "%{family[0]}\n", ":lang=zh"], env)
    return sorted(set(result.stdout.splitlines())) if result.returncode == 0 else []


def check(config, control=None):
    env = environment(config)
    report = {
        "schema": SCHEMA, "platform": platform.platform(), "python": python_path(config),
        "tools": {}, "python_packages": {}, "tex_files": {}, "fonts": {},
        "missing": [], "status": "needs-attention", "actual_pdf_verified": False,
    }
    result = run([python_path(config), "-c", "import sys,json; print(json.dumps(list(sys.version_info[:3])))"], env)
    if result.returncode:
        report["missing"].append("working Python interpreter")
    else:
        report["python_version"] = json.loads(result.stdout)
        if report["python_version"] < BASELINE["python_min"]:
            report["missing"].append("Python >= 3.11.8")
    flags = {"latexmk": "-v", "fc-match": "-V", "fc-list": "-V",
             **{name: "-v" for name in PDF_TOOLS}}
    for name in TOOLS:
        path = which(name, env)
        item = {"path": path, "works": False}
        if path:
            result = run([path, flags.get(name, "--version")], env)
            item.update(works=result.returncode == 0, version_probe_exit=result.returncode,
                        version=(result.stdout or result.stderr).strip().splitlines()[:1])
        report["tools"][name] = item
        if not item["works"]:
            report["missing"].append(name)
    for name in BASELINE["python_packages"]:
        ok, version = importable(name, config, env)
        report["python_packages"][name] = {"importable": ok, "version": version}
        if not ok:
            report["missing"].append(f"Python module {name}")
    if report["tools"]["kpsewhich"]["works"]:
        for filename in BASELINE["tex_files"]:
            path = tex_file(filename, env)
            report["tex_files"][filename] = path or None
            if not path:
                report["missing"].append(filename)
    fonts = BASELINE["fonts"] | config.get("fonts", {})
    explicit_fonts = set(config.get("fonts", {}))
    if control is not None:
        # Reuse the builder's parser in the selected Python environment.
        program = (
            "import runpy,json,sys; b=runpy.run_path(sys.argv[1]); issues=[]; "
            "p=b['parse_profile'](open(sys.argv[2],encoding='utf-8').read(),issues); "
            "print(json.dumps({'fonts':p.get('fonts',{}) if p else {},"
            "'errors':[i.message for i in issues if i.severity=='ERROR']}))"
        )
        parsed = json.loads(require_success(run(
            [python_path(config), "-c", program, ROOT / "scripts/final-pdf-build.py", control], env
        ), "control profile"))
        report["missing"].extend(parsed["errors"])
        fonts.update(parsed["fonts"])
        explicit_fonts.update(parsed["fonts"])
    for role, recipe in BASELINE["cjk_fonts"].items():
        if role not in explicit_fonts:
            fonts[role] = next((family for family in recipe["candidates"] if font_path(family, env)), fonts[role])
    for role, family in fonts.items():
        path = font_path(family, env)
        report["fonts"][role] = {"family": family, "file": path}
        if path is None:
            report["missing"].append(f"font {role}={family}")
    report["tex_distribution"] = tex_inventory(env)
    report["available_cjk_families"] = cjk_families(env)
    if not report["missing"]:
        report["status"] = "dependencies-found"
    return report


def download(url, directory):
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / url.rsplit("/", 1)[-1]
    if target.is_file():
        return target
    partial = target.with_name(target.name + ".part")
    print(f"Downloading {target.name}", flush=True)
    request = urllib.request.Request(url, headers={"User-Agent": "zuihan-kanshu/pdf-environment"})
    with urllib.request.urlopen(request, timeout=60) as incoming, partial.open("wb") as outgoing:
        shutil.copyfileobj(incoming, outgoing)
        expected = incoming.headers.get("Content-Length")
    if expected and partial.stat().st_size != int(expected):
        raise RuntimeError(f"incomplete download: {target.name}")
    partial.replace(target)
    return target


def unpack(archive, destination):
    destination.mkdir(parents=True, exist_ok=True)
    if archive.suffix == ".zip":
        with zipfile.ZipFile(archive) as bundle:
            for name in bundle.namelist():
                if not (destination / name).resolve().is_relative_to(destination.resolve()):
                    raise ValueError(f"archive path escapes destination: {name}")
            bundle.extractall(destination)
    elif archive.suffix == ".exe" and os.name == "nt":
        # Official TinyTeX self-extractor: extract only, no global installer.
        require_success(run([archive, "-y"], cwd=destination, timeout=300), "TinyTeX extraction")
    else:
        with tarfile.open(archive) as bundle:
            bundle.extractall(destination, filter="data")


def find_tool(directory, name):
    filename = name + (".exe" if os.name == "nt" else "")
    paths = sorted(directory.rglob(filename))
    if not paths:
        raise RuntimeError(f"{filename} not found in {directory}")
    return paths[0].parent


def add_bin(config, directory):
    value = str(directory.resolve())
    if value not in config["bin_dirs"]:
        config["bin_dirs"].insert(0, value)


def tex_repository(args, year, manager, env, prefix, package):
    """Let tlmgr check repository/year compatibility before any package install."""
    if args.tex_repository:
        candidates = [args.tex_repository]
    else:
        historic = [url.format(year=year) for url in BASELINE["tex_historic_repositories"]]
        current = [BASELINE["tex_repository"], *BASELINE["tex_repository_fallbacks"]]
        candidates = historic if year < BASELINE["texlive_year"] else current + historic
    logs = []
    for repository in candidates:
        try:
            result = run([*manager, "--repository", repository, "info", "--only-remote",
                          "--data", "name", package], env, timeout=120)
            logs.append(f"Repository: {repository}\n{result.stdout}\n{result.stderr}\n")
            if result.returncode == 0 and package in result.stdout.splitlines():
                (prefix / "tex-repository-probes.txt").write_text("\n".join(logs), encoding="utf-8")
                return repository
        except subprocess.TimeoutExpired as exc:
            logs.append(f"Repository: {repository}\n{exc}\n")
    (prefix / "tex-repository-probes.txt").write_text("\n".join(logs), encoding="utf-8")
    raise RuntimeError(f"No usable TeX Live {year} repository; see tex-repository-probes.txt. "
                       "Use --tex-repository with a matching annual repository.")


def extend_tex(config, args, prefix, missing):
    """Install relocatable packages in a new user tree, retaining the host engine."""
    env = environment(config)
    inventory = tex_inventory(env)
    tlmgr = which("tlmgr", env)
    if not tlmgr or not inventory["year"]:
        raise RuntimeError("The existing TeX cannot be extended automatically: a recognized TeX Live "
                           "and tlmgr are required. Keep this diagnostic; prepare the needed packages "
                           "using the environment guide, or use --private-tex in a new directory.")
    packages = list(dict.fromkeys([BASELINE["tex_files"][name] for name in missing]
                                 + args.extra_tex_package))
    if not all(packages):
        raise RuntimeError("A core TeX format is missing; repair that installation or use --private-tex.")
    tree = prefix / "texmf"
    # Preserve pre-existing user trees for TeX searches. tlmgr manages only tree.
    old_home = inventory.get("TEXMFHOME")
    config["variables"]["TEXMFHOME"] = str(tree) + (os.pathsep + old_home if old_home else "")
    config["variables"]["TEXMFVAR"] = str(prefix / "texmf-var")
    config["variables"]["TEXMFCONFIG"] = str(prefix / "texmf-config")
    env = environment(config)
    manager = [tlmgr, "--usermode", "--usertree", tree]
    require_success(run([*manager, "init-usertree"], env), "TeX user-tree initialization")
    repository = tex_repository(args, inventory["year"], manager, env, prefix, packages[0])
    # Debian/Ubuntu package databases may not describe the installed core to
    # tlmgr. Install only the probed/explicit package set, not a newer core.
    result = run([*manager, "--repository", repository, "install", "--no-depends", *packages], env, timeout=900)
    (prefix / "tex-install.txt").write_text(result.stdout + result.stderr, encoding="utf-8")
    require_success(result, "TeX user-tree packages (host installation unchanged)")
    current = tex_inventory(env)
    for filename, item in inventory.get("core_files", {}).items():
        if item.get("path") and current.get("core_files", {}).get(filename) != item:
            raise RuntimeError(f"User packages shadow the existing TeX core: {filename}. "
                               "Preserve this diagnostic and revise the package selection in a new directory.")
    unresolved = [name for name in missing if not tex_file(name, env)]
    if unresolved:
        raise RuntimeError("TeX user-tree installation did not provide: " + ", ".join(unresolved))
    config["tex"] = {"mode": "user-tree", "year": inventory["year"], "repository": repository,
                     "tree": str(tree), "packages": packages}


def install_private_tex_packages(manager, repository, env, prefix, packages):
    """Recover one explicit self-update request from this private manager only."""
    command = [*manager, "--repository", repository, "install", *packages]
    result = run(command, env, timeout=900)
    install_log = prefix / "tex-install.txt"
    install_log.write_text(result.stdout + result.stderr, encoding="utf-8")
    if result.returncode and "tlmgr itself needs to be updated" in (result.stdout + result.stderr).casefold():
        print("Private tlmgr requested a self-update; updating it before one install retry", flush=True)
        updated = run([*manager, "--repository", repository, "update", "--self"], env, timeout=900)
        (prefix / "tex-self-update.txt").write_text(updated.stdout + updated.stderr, encoding="utf-8")
        require_success(updated, "private TeX manager self-update")
        result = run(command, env, timeout=900)
        with install_log.open("a", encoding="utf-8") as stream:
            stream.write("\n--- install retry after manager self-update ---\n" + result.stdout + result.stderr)
    require_success(result, "private TeX packages")


def platform_key():
    machine = platform.machine().lower()
    arch = {"amd64": "x86_64", "x86_64": "x86_64", "aarch64": "aarch64", "arm64": "aarch64"}.get(machine, machine)
    return f"{platform.system()}-{arch}"


def configure_fonts(config, prefix, extra_dirs):
    env = environment(config)
    font_dirs = {str(Path(p).resolve()) for p in extra_dirs}
    font_dirs.add(str(prefix / "fonts"))
    # Keep fonts already visible to this selected toolchain; no registry edits.
    if which("fc-list", env):
        result = run(["fc-list", "-f", "%{file}\n"], env)
        font_dirs.update(str(Path(line).parent) for line in result.stdout.splitlines() if line)
    if which("kpsewhich", env):
        result = run(["kpsewhich", "-var-value=TEXMFDIST"], env)
        if result.returncode == 0 and result.stdout.strip():
            font_dirs.add(str(Path(result.stdout.strip()) / "fonts" / "opentype"))
    cache = prefix / "font-cache"
    cache.mkdir(exist_ok=True)
    font_config = prefix / "fonts.conf"
    font_config.write_text(
        '<?xml version="1.0"?>\n<!DOCTYPE fontconfig SYSTEM "urn:fontconfig:fonts.dtd">\n<fontconfig>\n'
        + "".join(f"  <dir>{escape(Path(p).as_posix())}</dir>\n" for p in sorted(font_dirs))
        + f"  <cachedir>{escape(cache.as_posix())}</cachedir>\n</fontconfig>\n",
        encoding="utf-8",
    )
    config["variables"]["FONTCONFIG_FILE"] = str(font_config)


def restore(args):
    if list(sys.version_info[:3]) < BASELINE["python_min"]:
        raise ValueError("restore requires Python >= 3.11.8")
    prefix = args.prefix.resolve()
    if prefix.exists() and any(prefix.iterdir()):
        existing = prefix / "environment.json"
        if existing.is_file():
            config = load_config(existing)
            report = check(config)
            print(json.dumps(report, ensure_ascii=False, indent=2))
            return 0 if not report["missing"] else 1
        raise ValueError("restore requires a new/empty prefix; preserve failed diagnostics and choose a new directory")
    for package in args.extra_tex_package:
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", package):
            raise ValueError(f"invalid TeX package name: {package}")
    key = platform_key()
    if key not in BASELINE["pandoc"]:
        raise ValueError(f"automatic restoration has no recipe for {key}; use the guide and check an existing environment")
    # Linux Work runtimes normally supply these native utilities. Report their
    # absence before downloading anything; the guide gives the small OS layer.
    if platform.system() == "Linux":
        native_missing = [name for name in (*FONT_TOOLS, *PDF_TOOLS, "perl")
                          if not which(name, os.environ)]
        if native_missing:
            raise RuntimeError(
                "Missing native Linux tools: " + ", ".join(native_missing)
                + ". Prepare fontconfig, poppler-utils, poppler-data and perl "
                "in this Work runtime, then rerun; see pdf-environment.md."
            )
    prefix.mkdir(parents=True, exist_ok=True)
    try:
        return restore_new(args, prefix, key)
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as exc:
        (prefix / "failure.txt").write_text(str(exc) + "\n", encoding="utf-8")
        raise


def restore_new(args, prefix, key):
    config = {"schema": SCHEMA, "python": sys.executable, "bin_dirs": [],
              "python_paths": [p for p in os.environ.get("PYTHONPATH", "").split(os.pathsep) if p],
              "variables": {}, "fonts": BASELINE["fonts"].copy()}
    for role in config["fonts"]:
        if getattr(args, role, None):
            config["fonts"][role] = getattr(args, role)
    downloads = prefix / "downloads"
    temp = prefix / "tmp"
    temp.mkdir()
    config["variables"].update({name: str(temp) for name in ("TMPDIR", "TMP", "TEMP")})
    env = environment(config)
    packages = [spec for module, spec in BASELINE["python_packages"].items()
                if args.baseline_tools or not importable(module, config, env)[0]]
    if packages:
        target = prefix / "python"
        print("Preparing Python packages", flush=True)
        require_success(run([sys.executable, "-m", "pip", "install", "--disable-pip-version-check",
                             "--no-input", "--no-compile", "--target", target, *packages],
                            env, timeout=600), "Python package installation")
        config["python_paths"].insert(0, str(target))
    if args.baseline_tools or not which("pandoc", env):
        target = prefix / "pandoc"
        unpack(download(BASELINE["pandoc"][key], downloads), target)
        add_bin(config, find_tool(target, "pandoc"))
    env = environment(config)
    need_tex = args.baseline_tools or getattr(args, "private_tex", False) or any(
        not which(name, env) for name in ("xelatex", "kpsewhich"))
    if not need_tex and not which("latexmk", env):
        raise RuntimeError("The existing TeX engine needs latexmk; prepare that small host package "
                           "or explicitly choose --private-tex in a new directory.")
    missing_tex = [] if need_tex else [name for name in BASELINE["tex_files"] if not tex_file(name, env)]
    if "xelatex.fmt" in missing_tex:
        raise RuntimeError("Existing XeLaTeX has no usable format. Repair it or use --private-tex in a new directory.")
    if not need_tex and (missing_tex or args.extra_tex_package):
        extend_tex(config, args, prefix, missing_tex)
    if need_tex:
        print("Preparing private TinyTeX", flush=True)
        target = prefix / "tex"
        unpack(download(BASELINE["tinytex"][key], downloads), target)
        tex_bin = find_tool(target, "xelatex")
        add_bin(config, tex_bin)
        env = environment(config)
        tlmgr = tex_bin / ("tlmgr.bat" if os.name == "nt" else "tlmgr")
        repository = tex_repository(args, BASELINE["texlive_year"], [tlmgr], env, prefix, "xecjk")
        config["tex_repository"] = repository
        updated = run([tlmgr, "--repository", repository, "update", "--self", "--all"], env, timeout=900)
        (prefix / "tex-update.txt").write_text(updated.stdout + updated.stderr, encoding="utf-8")
        require_success(updated, "private TeX baseline update")
        install_private_tex_packages([tlmgr], repository, env, prefix,
                                     [*BASELINE["tex_packages"], *args.extra_tex_package])
        installed = run([tlmgr, "info", "--list", "--only-installed", "--data", "name,localrev"], env)
        require_success(installed, "TeX package inventory")
        (prefix / "tex-packages.txt").write_text(installed.stdout, encoding="utf-8")
        config["tex"] = {"mode": "private", "year": BASELINE["texlive_year"], "repository": repository}
    elif "tex" not in config:
        config["tex"] = {"mode": "host", "year": tex_inventory(environment(config))["year"]}
    env = environment(config)
    if args.baseline_tools or any(not which(name, env) for name in PDF_TOOLS):
        if os.name == "nt":
            target = prefix / "poppler"
            unpack(download(BASELINE["windows_poppler"], downloads), target)
            add_bin(config, find_tool(target, "pdftoppm"))
        elif any(not which(name, env) for name in PDF_TOOLS):
            raise RuntimeError("PDF utilities are missing: install poppler-utils and poppler-data with the host package manager; see pdf-environment.md")
    restore_fonts(config, args, prefix)
    # Preserve the selected executable directories in their effective PATH order.
    selected = {str(Path(path).parent.resolve()) for name in TOOLS
                if (path := which(name, environment(config)))}
    for directory in environment(config)["PATH"].split(os.pathsep):
        if directory and str(Path(directory).resolve()) in selected:
            value = str(Path(directory).resolve())
            if value not in config["bin_dirs"]:
                config["bin_dirs"].append(value)
    write_json(prefix / "environment.json", config)
    report = check(config)
    write_json(prefix / "check.json", report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"Configuration: {prefix / 'environment.json'}", flush=True)
    return 0 if not report["missing"] else 1


def restore_fonts(config, args, prefix):
    """Reuse each font channel independently; download only known missing families."""
    (prefix / "fonts").mkdir(exist_ok=True)
    configure_fonts(config, prefix, args.font_dir)
    env = environment(config)
    for role, recipe in BASELINE["cjk_fonts"].items():
        if not args.baseline_tools and not getattr(args, role, None):
            config["fonts"][role] = next(
                (family for family in recipe["candidates"] if font_path(family, env)),
                config["fonts"][role],
            )
        family = config["fonts"][role]
        if (args.baseline_tools or not font_path(family, env)) and family == BASELINE["fonts"][role]:
            for url in recipe["urls"]:
                download(url, prefix / "fonts" / role)
    configure_fonts(config, prefix, args.font_dir)


def smoke(config, destination):
    destination = destination.resolve()
    destination.mkdir(parents=True, exist_ok=False)
    temp = destination / "tmp"
    temp.mkdir()
    env = environment(config)
    env.update({name: str(temp) for name in ("TMPDIR", "TMP", "TEMP")})
    report = check(config)
    write_json(destination / "environment-check.json", report)
    if report["missing"]:
        raise RuntimeError("environment check failed; see environment-check.json")
    source = temp / "environment_v1.0.0.md"
    control = temp / "environment_v1.0.0.control.md"
    shutil.copyfile(ASSETS / "smoke.md", source)
    fonts = {role: item["family"] for role, item in report["fonts"].items()}
    font_lines = "\n".join(f"    {key}: {json.dumps(value, ensure_ascii=False)}" for key, value in fonts.items())
    control.write_text(
        "# 环境样稿控制\n\n<!-- BEGIN:BUILD_PROFILE -->\n\x60\x60\x60yaml\n"
        "build_profile:\n  schema: final-pdf-build/v1\n  profile: zh-math-xelatex/v1\n"
        "  engine: xelatex\n  fonts:\n" + font_lines + "\n"
        "  layout:\n    paper: a4\n    margins:\n      top: 25mm\n      right: 25mm\n      bottom: 25mm\n      left: 25mm\n"
        "  resources:\n    figures: []\n    bibliography: null\n"
        "  document:\n    class: article\n    fontsize: 11pt\n    toc: true\n    number_sections: true\n"
        "  typography:\n    mathbb_uppercase: ams-msbm\n    mathbb_nonuppercase: explicit-only\n"
        "\x60\x60\x60\n<!-- END:BUILD_PROFILE -->\n", encoding="utf-8",
    )
    pdf = source.with_suffix(".pdf")
    log = source.with_suffix(".log")
    commands = [
        [python_path(config), ROOT / "scripts/final-pdf-build.py", "build", source, "--control", control,
         "--reader", temp / "reader.md", "--pdf", pdf, "--tex", source.with_suffix(".tex"),
         "--build-log", log, "--json-report", temp / "build.json"],
        [python_path(config), ROOT / "scripts/preflight-pdf.py", pdf, "--build-log", log,
         "--render-dir", temp / "rendered", "--require-font", "MSBM10",
         "--json-report", temp / "preflight.json"],
    ]
    for number, command in enumerate(commands, 1):
        result = run(command, env, cwd=destination, timeout=600)
        (destination / f"step-{number}.txt").write_text(result.stdout + result.stderr, encoding="utf-8")
        require_success(result, f"sample step {number}")
    extracted = require_success(run(["pdftotext", "-layout", pdf, "-"], env), "Chinese text extraction")
    if not all(word in extracted for word in ("正交投影", "粗体中文", "数学字形", "无衬线中文", "等宽中文")):
        raise RuntimeError("Chinese sample text did not survive PDF extraction")
    preflight = json.loads((temp / "preflight.json").read_text(encoding="utf-8"))
    if preflight["warnings"] or preflight["errors"]:
        raise RuntimeError("Bundled sample has final preflight issues; preserve and inspect preflight.json and the build log")
    objects = preflight["objects"]
    if not objects["complete"] or objects["outlines"] < 2 or objects["internal_links"] < 1:
        raise RuntimeError(f"unexpected outline/attachment result: {objects}")
    result = {"status": "sample-built", "actual_pdf_verified": True, "visual_review_required": True,
              "pdf": str(pdf), "render_dir": str(temp / "rendered"), "objects": objects}
    write_json(destination / "sample-result.json", result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    check_parser = sub.add_parser("check", help="read-only probes; no downloads or compilation")
    check_parser.add_argument("--config", type=Path)
    check_parser.add_argument("--control", type=Path)
    check_parser.add_argument("--report", type=Path)
    restore_parser = sub.add_parser("restore", help="prepare missing dependencies in a new writable directory")
    restore_parser.add_argument("--prefix", type=Path, required=True)
    restore_parser.add_argument("--baseline-tools", action="store_true", help="prepare private Pandoc, TinyTeX and Python packages; reuse Linux native utilities")
    restore_parser.add_argument("--private-tex", action="store_true", help="prepare private TeX only; retain other usable host tools")
    restore_parser.add_argument("--extra-tex-package", action="append", default=[])
    restore_parser.add_argument("--tex-repository", help="TeX repository matching the selected engine's TeX Live year")
    restore_parser.add_argument("--font-dir", action="append", default=[])
    for role in BASELINE["fonts"]:
        restore_parser.add_argument("--" + role.replace("_", "-"), dest=role)
    smoke_parser = sub.add_parser("smoke", help="build and mechanically inspect the bundled Chinese sample")
    smoke_parser.add_argument("--config", type=Path, required=True)
    smoke_parser.add_argument("--output", type=Path, required=True)
    run_parser = sub.add_parser("run", help="run a command with the selected environment; use 'python' for its interpreter")
    run_parser.add_argument("--config", type=Path, required=True)
    run_parser.add_argument("argv", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    try:
        if args.command == "restore":
            return restore(args)
        config = load_config(args.config)
        if args.command == "check":
            report = check(config, args.control)
            if args.report:
                write_json(args.report, report)
            print(json.dumps(report, ensure_ascii=False, indent=2))
            return 0 if not report["missing"] else 1
        if args.command == "smoke":
            return smoke(config, args.output)
        argv = args.argv[1:] if args.argv[:1] == ["--"] else args.argv
        if not argv:
            raise ValueError("run requires a command after --")
        if argv[0] in {"python", "python3"}:
            argv[0] = python_path(config)
        return subprocess.call(argv, env=environment(config))
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as exc:
        print(f"pdf-environment: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
