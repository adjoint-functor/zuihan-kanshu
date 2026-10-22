#!/usr/bin/env python3
"""Build the selected current Markdown body using a separate control profile."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


VERSION = "8.3.0"
PROFILE_BEGIN = "<!-- BEGIN:BUILD_PROFILE -->"
PROFILE_END = "<!-- END:BUILD_PROFILE -->"
PROFILE_SCHEMA = "final-pdf-build/v1"
PROFILE_NAME = "zh-math-xelatex/v1"
PANDOC_FROM = "markdown+tex_math_dollars+tex_math_single_backslash+raw_tex+fenced_divs"
CJK_PATTERN = re.compile(
    "[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\U00020000-\U0002fa1f]"
)
LENGTH_PATTERN = re.compile(r"^(?:0|[1-9]\d*)(?:\.\d+)?(?:mm|cm|in|pt)$")
CJK_VARIABLES = {"cjk_main": "CJKmainfont", "cjk_sans": "CJKsansfont", "cjk_mono": "CJKmonofont"}
FONT_BASELINE = json.loads((Path(__file__).resolve().parents[1] / "assets/pdf-environment/baseline.json").read_text(encoding="utf-8"))


@dataclass
class Issue:
    severity: str
    check: str
    message: str


def add(issues: list[Issue], severity: str, check: str, message: str) -> None:
    issues.append(Issue(severity, check, message))


class UniqueKeyLoaderError(ValueError):
    pass


def load_yaml_unique(text: str) -> Any:
    try:
        import yaml
    except ImportError as exc:  # pragma: no cover - environment failure
        raise UniqueKeyLoaderError("PyYAML is required to parse build_profile") from exc

    class UniqueKeyLoader(yaml.SafeLoader):
        pass

    def construct_mapping(loader: Any, node: Any, deep: bool = False) -> dict[Any, Any]:
        mapping: dict[Any, Any] = {}
        for key_node, value_node in node.value:
            key = loader.construct_object(key_node, deep=deep)
            if key in mapping:
                raise UniqueKeyLoaderError(f"duplicate YAML key: {key}")
            mapping[key] = loader.construct_object(value_node, deep=deep)
        return mapping

    UniqueKeyLoader.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
        construct_mapping,
    )
    try:
        return yaml.load(text, Loader=UniqueKeyLoader)
    except UniqueKeyLoaderError:
        raise
    except yaml.YAMLError as exc:
        raise UniqueKeyLoaderError(f"invalid YAML: {exc}") from exc


def exact_mapping_keys(
    value: Any,
    expected: set[str],
    label: str,
    issues: list[Issue],
    optional: set[str] | None = None,
) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        add(issues, "ERROR", "build-profile", f"{label} must be a mapping")
        return None
    keys = set(value)
    missing = sorted(expected - keys)
    unknown = sorted(keys - expected - (optional or set()))
    if missing:
        add(issues, "ERROR", "build-profile", f"{label} missing keys: {missing}")
    if unknown:
        add(issues, "ERROR", "build-profile", f"{label} has unknown keys: {unknown}")
    return value


def parse_profile(control_text: str, issues: list[Issue]) -> dict[str, Any] | None:
    markers = (PROFILE_BEGIN, PROFILE_END)
    for marker in markers:
        count = control_text.count(marker)
        if count != 1:
            add(issues, "ERROR", "build-profile", f"expected one {marker}, found {count}")
            return None
        if sum(line.strip() == marker for line in control_text.splitlines()) != 1:
            add(issues, "ERROR", "build-profile", f"marker must occur alone on its line: {marker}")
            return None
    p_begin = control_text.index(PROFILE_BEGIN)
    p_end = control_text.index(PROFILE_END)
    if p_begin >= p_end:
        add(issues, "ERROR", "build-profile", "BUILD_PROFILE END marker must follow BEGIN")
        return None
    raw = control_text[p_begin + len(PROFILE_BEGIN) : p_end].strip()
    match = re.fullmatch(r"```ya?ml\s*\n([\s\S]*?)\n```", raw)
    if match is None:
        add(issues, "ERROR", "build-profile", "profile markers must contain exactly one fenced YAML block")
        return None
    try:
        loaded = load_yaml_unique(match.group(1))
    except UniqueKeyLoaderError as exc:
        add(issues, "ERROR", "build-profile", str(exc))
        return None
    if not isinstance(loaded, dict) or set(loaded) != {"build_profile"}:
        add(issues, "ERROR", "build-profile", "YAML root must contain only build_profile")
        return None

    profile = exact_mapping_keys(
        loaded["build_profile"],
        {"schema", "profile", "engine", "fonts", "layout", "resources", "document", "typography"},
        "build_profile",
        issues,
    )
    if profile is None:
        return None
    if profile.get("schema") != PROFILE_SCHEMA:
        add(issues, "ERROR", "build-profile", f"unsupported schema: {profile.get('schema')!r}")
    if profile.get("profile") != PROFILE_NAME:
        add(issues, "ERROR", "build-profile", f"unsupported profile: {profile.get('profile')!r}")
    if profile.get("engine") != "xelatex":
        add(issues, "ERROR", "build-profile", "engine must be xelatex")

    fonts = exact_mapping_keys(
        profile.get("fonts"),
        {"latin_main", "cjk_main", "math_main"},
        "fonts",
        issues,
        optional={"cjk_sans", "cjk_mono"},
    )
    if fonts is not None:
        for key, value in fonts.items():
            if not isinstance(value, str) or not value.strip():
                add(issues, "ERROR", "build-profile", f"fonts.{key} must be a nonempty string")

    layout = exact_mapping_keys(profile.get("layout"), {"paper", "margins"}, "layout", issues)
    if layout is not None:
        if layout.get("paper") not in {"a4", "letter"}:
            add(issues, "ERROR", "build-profile", "layout.paper must be a4 or letter")
        margins = exact_mapping_keys(
            layout.get("margins"),
            {"top", "right", "bottom", "left"},
            "layout.margins",
            issues,
        )
        if margins is not None:
            for key, value in margins.items():
                if not isinstance(value, str) or LENGTH_PATTERN.fullmatch(value) is None:
                    add(issues, "ERROR", "build-profile", f"layout.margins.{key} has an invalid length")

    resources = exact_mapping_keys(
        profile.get("resources"),
        {"figures", "bibliography"},
        "resources",
        issues,
    )
    if resources is not None:
        figures = resources.get("figures")
        if not isinstance(figures, list) or any(not isinstance(item, str) or not item for item in figures):
            add(issues, "ERROR", "build-profile", "resources.figures must be a list of nonempty relative paths")
        bibliography = resources.get("bibliography")
        if bibliography is not None and (not isinstance(bibliography, str) or not bibliography):
            add(issues, "ERROR", "build-profile", "resources.bibliography must be a relative path or null")

    document = exact_mapping_keys(
        profile.get("document"),
        {"class", "fontsize", "toc", "number_sections"},
        "document",
        issues,
    )
    if document is not None:
        if document.get("class") not in {"article", "report", "book"}:
            add(issues, "ERROR", "build-profile", "document.class is unsupported")
        if document.get("fontsize") not in {"10pt", "11pt", "12pt"}:
            add(issues, "ERROR", "build-profile", "document.fontsize is unsupported")
        for key in ("toc", "number_sections"):
            if not isinstance(document.get(key), bool):
                add(issues, "ERROR", "build-profile", f"document.{key} must be boolean")

    typography = exact_mapping_keys(
        profile.get("typography"),
        {"mathbb_uppercase", "mathbb_nonuppercase"},
        "typography",
        issues,
    )
    if typography is not None:
        if typography.get("mathbb_uppercase") != "ams-msbm":
            add(issues, "ERROR", "build-profile", "typography.mathbb_uppercase must be ams-msbm")
        if typography.get("mathbb_nonuppercase") != "explicit-only":
            add(issues, "ERROR", "build-profile", "typography.mathbb_nonuppercase must be explicit-only")
    return profile


def project_root(source: Path) -> Path:
    parent = source.resolve().parent
    return parent.parent if parent.name == "tmp" else parent


def resolve_resource(root: Path, supplied: str, issues: list[Issue]) -> Path | None:
    path = Path(supplied)
    if path.is_absolute() or ".." in path.parts:
        add(issues, "ERROR", "resource", f"resource path must stay relative to the output root: {supplied}")
        return None
    resolved = (root / path).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError:
        add(issues, "ERROR", "resource", f"resource escapes the output root: {supplied}")
        return None
    if not resolved.exists():
        add(issues, "ERROR", "resource", f"declared resource is missing: {supplied}")
        return None
    # Preserve the declared name, including a project-local file alias. The
    # content is copied into the build workspace under this same relative name.
    return root / path


def validate_resources(source: Path, profile: dict[str, Any], issues: list[Issue]) -> dict[str, Any]:
    root = project_root(source)
    resolved_figures: list[Path] = []
    resources = profile.get("resources")
    if isinstance(resources, dict):
        figures = resources.get("figures")
        if isinstance(figures, list):
            for supplied in figures:
                if isinstance(supplied, str):
                    path = resolve_resource(root, supplied, issues)
                    if path is not None:
                        resolved_figures.append(path)
        bibliography_value = resources.get("bibliography")
        bibliography = (
            resolve_resource(root, bibliography_value, issues)
            if isinstance(bibliography_value, str)
            else None
        )
    else:
        bibliography = None
    return {"root": root, "figures": resolved_figures, "bibliography": bibliography}


def run(command: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command, cwd=cwd, text=True, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, check=False,
    )


def derive_reader(source: Path, reader: Path, issues: list[Issue]) -> bool:
    script = Path(__file__).with_name("derive-clean-reader-view.py")
    result = run([sys.executable, str(script), str(source), str(reader)])
    if result.returncode:
        add(issues, "ERROR", "reader-derivation", result.stderr.strip() or result.stdout.strip())
        return False
    return True


def scan_mathbb(text: str, issues: list[Issue]) -> int:
    uppercase_count = 0
    for match in re.finditer(r"\\mathbb\b", text):
        cursor = match.end()
        while cursor < len(text) and text[cursor].isspace():
            cursor += 1
        if cursor >= len(text) or text[cursor] != "{":
            add(issues, "ERROR", "mathbb", "\\mathbb must use one braced Latin uppercase letter")
            continue
        depth = 0
        end = cursor
        nested = False
        while end < len(text):
            char = text[end]
            if char == "{":
                depth += 1
                if depth > 1:
                    nested = True
            elif char == "}":
                depth -= 1
                if depth == 0:
                    break
            end += 1
        if end >= len(text) or depth != 0:
            add(issues, "ERROR", "mathbb", "unclosed \\mathbb argument")
            continue
        argument = text[cursor + 1 : end].strip()
        if nested or re.fullmatch(r"[A-Z]", argument) is None:
            add(
                issues,
                "ERROR",
                "mathbb",
                f"\\mathbb argument must be one explicit Latin uppercase letter, found {argument!r}",
            )
        else:
            uppercase_count += 1
    return uppercase_count


def inline_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "".join(inline_text(item) for item in value)
    if not isinstance(value, dict):
        return ""
    tag = value.get("t")
    content = value.get("c")
    if tag in {"Str", "Code"} and isinstance(content, str):
        return content
    if tag in {"Space", "SoftBreak", "LineBreak"}:
        return " "
    if tag == "Math" and isinstance(content, list) and len(content) == 2:
        return str(content[1])
    return inline_text(content)


def inspect_ast(reader: Path, third_party: bool, issues: list[Issue]) -> dict[str, Any]:
    if shutil.which("pandoc") is None:
        add(issues, "ERROR", "dependency", "pandoc is unavailable")
        return {"display_candidates": [], "heading_candidates": []}
    result = run(["pandoc", str(reader), f"--from={PANDOC_FROM}", "--to=json"])
    if result.returncode:
        add(issues, "ERROR", "pandoc-ast", result.stderr.strip() or "Pandoc AST conversion failed")
        return {"display_candidates": [], "heading_candidates": []}
    try:
        ast = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        add(issues, "ERROR", "pandoc-ast", f"invalid Pandoc JSON: {exc}")
        return {"display_candidates": [], "heading_candidates": []}

    displays: list[str] = []
    headings: list[str] = []
    mathbb_count = 0
    structural = re.compile(
        r"\\(?:begin|frac|dfrac|tfrac|sum|prod|coprod|int|iint|iiint|lim|left|right|label|tag|notag)\b|\\\\|&"
    )
    question = re.compile(
        r"[?？]|为什么|为何|是否|能否|怎么|怎样|什么|谁|哪里|何时|不是.+而是|^(?:请|注意|记住|试着|来看)"
    )

    def walk(node: Any) -> None:
        nonlocal mathbb_count
        if isinstance(node, list):
            for item in node:
                walk(item)
            return
        if not isinstance(node, dict):
            return
        tag = node.get("t")
        content = node.get("c")
        if tag == "Math" and isinstance(content, list) and len(content) == 2:
            kind = content[0]
            formula = str(content[1])
            mathbb_count += scan_mathbb(formula, issues)
            if isinstance(kind, dict) and kind.get("t") == "DisplayMath":
                compact = re.sub(r"\s+", "", formula)
                if "\n" not in formula and len(compact) <= 60 and structural.search(formula) is None:
                    displays.append(formula)
        elif tag in {"RawInline", "RawBlock"} and isinstance(content, list) and len(content) == 2:
            if content[0] in {"tex", "latex"}:
                mathbb_count += scan_mathbb(str(content[1]), issues)
        elif third_party and tag == "Header" and isinstance(content, list) and len(content) == 3:
            heading = re.sub(r"\s+", " ", inline_text(content[2])).strip()
            if heading and question.search(heading):
                headings.append(heading)
        if content is not None:
            walk(content)
        else:
            for value in node.values():
                walk(value)

    walk(ast)
    for formula in displays:
        add(issues, "REVIEW", "display-math", f"short unnumbered display candidate: {formula}")
    for heading in headings:
        add(issues, "REVIEW", "heading-tone", f"heading requires third-party prose review: {heading}")
    metadata = ast.get("meta", {})
    language = inline_text(metadata.get("lang")).strip() if isinstance(metadata, dict) else ""
    return {
        "display_candidates": displays, "heading_candidates": headings,
        "document_language": language or None, "mathbb_uppercase_uses": mathbb_count,
        "cjk_font_metadata": {
            role: inline_text(metadata[variable]).strip()
            for role, variable in CJK_VARIABLES.items()
            if isinstance(metadata, dict) and variable in metadata
        },
    }


def font_available(name: str) -> bool:
    if shutil.which("fc-match") is None:
        return False
    result = run(["fc-match", "-f", "%{family[0]}\n", name])
    if result.returncode:
        return False
    returned = result.stdout.strip().casefold()
    requested = name.strip().casefold()
    return returned == requested


def validate_fonts(
    profile: dict[str, Any], reader_text: str, issues: list[Issue],
    metadata: dict[str, str] | None = None,
) -> None:
    fonts = profile.get("fonts")
    if not isinstance(fonts, dict):
        return
    for key in ("latin_main", "math_main"):
        value = fonts.get(key)
        if isinstance(value, str) and not font_available(value):
            add(issues, "ERROR", "font", f"configured font is unavailable without fallback: {key}={value}")
    if CJK_PATTERN.search(reader_text):
        for role, variable in CJK_VARIABLES.items():
            declared = (metadata or {}).get(role)
            value = fonts.get(role)
            if declared is not None:
                if not declared:
                    add(issues, "ERROR", "font", f"document {variable} must name a font family")
                    continue
                if value is not None and value != declared:
                    add(issues, "ERROR", "font", f"conflicting font choices: fonts.{role}={value}, document {variable}={declared}")
                    continue
                value = declared
            if value is None:
                value = next((family for family in FONT_BASELINE["cjk_fonts"][role]["candidates"]
                              if font_available(family)), None)
            if not isinstance(value, str) or not font_available(value):
                add(issues, "ERROR", "font", f"CJK font unavailable: {role}={value or '(unselected)'}. "
                    "Use pdf-environment.py restore or supply an available family; inspect again before building.")
            else:
                fonts[role] = value


def inspect_source(
    source: Path, third_party: bool, control: Path,
) -> tuple[dict[str, Any], list[Issue], str]:
    issues: list[Issue] = []
    try:
        with source.open(encoding="utf-8", newline="") as handle:
            source_text = handle.read()
    except (OSError, UnicodeError) as exc:
        add(issues, "ERROR", "input", f"cannot read source: {exc}")
        return {}, issues, ""
    if control.resolve() == source.resolve():
        add(issues, "ERROR", "build-profile", "body and control must be different files")
    if any(marker in source_text for marker in (PROFILE_BEGIN, PROFILE_END)):
        add(issues, "ERROR", "build-profile", "ambiguous build_profile: body has embedded profile markers and --control is supplied")
    try:
        control_text = control.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        add(issues, "ERROR", "input", f"cannot read control: {exc}")
        profile = None
    else:
        profile = parse_profile(control_text, issues)
    resources: dict[str, Any] = {}
    if profile is not None:
        resources = validate_resources(source, profile, issues)

    reader_text = ""
    ast_report: dict[str, Any] = {"display_candidates": [], "heading_candidates": []}
    with tempfile.TemporaryDirectory(prefix="final-pdf-inspect-") as temporary:
        reader = Path(temporary) / "reader.md"
        if derive_reader(source, reader, issues):
            with reader.open(encoding="utf-8", newline="") as handle:
                reader_text = handle.read()
            ast_report = inspect_ast(reader, third_party, issues)
            if profile is not None:
                validate_fonts(profile, reader_text, issues, ast_report.get("cjk_font_metadata"))
    report: dict[str, Any] = {
        "source": str(source),
        "control": str(control),
        "input_format": "body-and-control",
        "profile": profile,
        "output_root": str(resources.get("root", "")),
        "mathbb_uppercase_uses": 0,
        **ast_report,
    }
    report["effective_language"] = ast_report.get("document_language") or (
        "zh-CN" if CJK_PATTERN.search(reader_text) else None
    )
    return report, issues, reader_text


def safe_output(path: Path, root: Path, label: str, issues: list[Issue]) -> None:
    resolved = path.resolve()
    expected = (root / "tmp").resolve()
    if resolved.parent != expected:
        add(issues, "ERROR", "output", f"{label} must be directly inside {expected}")
    if resolved.exists():
        add(issues, "ERROR", "output", f"{label} already exists; overwrite is forbidden: {resolved}")


def pandoc_command(
    reader: Path,
    tex: Path,
    profile: dict[str, Any],
    resources: dict[str, Any],
    reader_text: str,
    language: str | None = None,
) -> list[str]:
    skill_root = Path(__file__).resolve().parents[1]
    asset_root = skill_root / "assets" / "final-pdf" / "v1"
    command = [
        "pandoc",
        str(reader),
        "--defaults",
        str(asset_root / "pandoc-defaults.yaml"),
        "--pdf-engine=xelatex",
        "--to=latex",
        "--verbose",
        "--output",
        str(tex),
    ]
    fonts = profile["fonts"]
    command.extend(["--variable", f"mainfont:{fonts['latin_main']}"])
    command.extend(["--variable", f"mathfont:{fonts['math_main']}"])
    if CJK_PATTERN.search(reader_text):
        for role, variable in CJK_VARIABLES.items():
            command.extend(["--variable", f"{variable}:{fonts[role]}"])
    if language:
        command.extend(["--metadata", f"lang:{language}"])
    layout = profile["layout"]
    command.extend(["--variable", f"papersize:{layout['paper']}"])
    for side, value in layout["margins"].items():
        command.extend(["--variable", f"geometry:{side}={value}"])
    document = profile["document"]
    command.extend(["--variable", f"documentclass:{document['class']}"])
    command.extend(["--variable", f"fontsize:{document['fontsize']}"])
    if document["toc"]:
        command.append("--toc")
    if document["number_sections"]:
        command.append("--number-sections")
    resource_paths = [resources["root"]]
    for path in resources["figures"]:
        resource_paths.append(path if path.is_dir() else path.parent)
    command.extend(["--resource-path", os.pathsep.join(str(path) for path in resource_paths)])
    if resources["bibliography"] is not None:
        command.extend(["--bibliography", str(resources["bibliography"])])
        command.append("--citeproc")
    return command


TEX_PATH_ARGUMENT = re.compile(
    r"(\\(?:includegraphics\*?|input|include|verbatiminput|lstinputlisting|"
    r"addbibresource|usepackage|RequirePackage|documentclass|LoadClass)"
    r"(?:\[[^\]]*\])?\s*\{)"
    r"([^{}\r\n]+)(\})"
)
FINAL_LOG_MARKER = "[final-pdf-build] Final XeLaTeX log"


def portable_tex(
    text: str, resource_name: str, resources: dict[str, Any], issues: list[Issue],
) -> str:
    """Use a relative resource prefix in the exact TeX that will be compiled."""
    root = resources["root"].resolve()

    def replace_path(match: re.Match[str]) -> str:
        supplied = Path(match.group(2))
        if not supplied.is_absolute():
            if ".." in supplied.parts:
                add(issues, "ERROR", "tex-resource", f"TeX resource must stay relative to the project root: {supplied}")
            return match.group(0)
        try:
            relative = supplied.absolute().relative_to(root)
        except ValueError:
            add(issues, "ERROR", "tex-resource", f"absolute TeX resource is outside the project root: {supplied}")
            return match.group(0)
        return match.group(1) + f"{resource_name}/{relative.as_posix()}" + match.group(3)

    text = TEX_PATH_ARGUMENT.sub(replace_path, text)
    paths = [resource_name + "/"]
    for resource in resources["figures"]:
        directory = resource if resource.is_dir() else resource.parent
        relative = directory.relative_to(root)
        path = f"{resource_name}/{relative.as_posix()}/" if relative.parts else resource_name + "/"
        if path not in paths:
            paths.append(path)
    if any(re.search(r"[\s{}\\%#$&^~]", path) for path in paths):
        add(issues, "ERROR", "tex-resource", "resource directory names must not contain TeX-special characters or whitespace")
        return text
    search_paths = "".join("{" + path + "}" for path in paths)
    input_preamble = (
        "% Project resources are relative to this standalone TeX file.\n"
        "\\makeatletter\n"
        f"\\def\\input@path{{{search_paths}}}\n"
        "\\makeatother\n"
    )
    mathbb_header = (
        Path(__file__).resolve().parents[1] / "assets" / "final-pdf" / "v1" / "ams-mathbb.tex"
    ).read_text(encoding="utf-8")
    graphic_preamble = mathbb_header.rstrip() + "\n" + (
        "\\usepackage{graphicx}\n"
        f"\\graphicspath{{{search_paths}}}\n"
    )
    boundary = r"\begin{document}"
    if text.count(boundary) != 1:
        add(issues, "ERROR", "tex", "Pandoc must produce exactly one standalone document")
        return text
    # Set input paths before the document class and YAML header-includes, which
    # may themselves load project macros. Graphics is configured after packages.
    return input_preamble + text.replace(boundary, graphic_preamble + boundary, 1)


def stage_resources(resources: dict[str, Any], destination: Path) -> None:
    """Copy declared resources without requiring directory-symlink privileges."""
    root = resources["root"].resolve()
    declared = list(resources["figures"])
    if resources["bibliography"] is not None:
        declared.append(resources["bibliography"])
    files: dict[Path, Path] = {}
    for resource in declared:
        candidates = resource.rglob("*") if resource.is_dir() else [resource]
        for source in candidates:
            if source.is_relative_to(destination.parent) or not source.is_file():
                continue
            if not source.resolve().is_relative_to(root):
                raise OSError(f"declared resource escapes the project root: {source}")
            files[source.relative_to(root)] = source
    destination.mkdir()
    for relative, source in files.items():
        copy_exclusive(source, destination / relative)


def recorded_resources(
    recorder: Path, work: Path, root: Path, issues: list[Issue],
) -> list[tuple[Path, Path]]:
    """Return project files actually opened by XeLaTeX, excluding its outputs."""
    if not recorder.is_file():
        add(issues, "ERROR", "tex-resource", "XeLaTeX recorder output is missing")
        return []
    files: dict[Path, Path] = {}
    resource_root = work / recorder.with_suffix(".resources").name
    # A minimal TeX environment may live under the project's tmp directory.
    # Its configured TEXMF files remain toolchain dependencies, not manuscript
    # resources. Ask Kpathsea for its actual trees; do not exempt tmp wholesale.
    toolchain_roots = []
    if shutil.which("kpsewhich"):
        probe = run(["kpsewhich", "-expand-path=$TEXMF"])
        if probe.returncode == 0:
            for value in probe.stdout.strip().split(os.pathsep):
                tree = Path(value.removeprefix("!!"))
                if value and tree.is_absolute() and tree.is_dir():
                    tree = tree.resolve()
                    if tree != root.resolve() and tree.is_relative_to(root.resolve()):
                        toolchain_roots.append(tree)
    for line in recorder.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.startswith("INPUT "):
            continue
        supplied = Path(line[6:])
        logical = work / supplied if not supplied.is_absolute() else supplied
        absolute = logical.resolve()
        logical = Path(os.path.abspath(logical))
        if logical.is_relative_to(resource_root) and absolute.is_file():
            files[logical.relative_to(resource_root)] = absolute
        elif absolute.is_relative_to(work.resolve()):
            continue
        elif any(absolute.is_relative_to(tree) for tree in toolchain_roots):
            continue
        elif absolute.is_relative_to(root.resolve()):
            add(issues, "ERROR", "tex-resource", f"project resource bypasses the declared resource copy; declare it and use a relative TeX input: {supplied}")
    return [(relative, files[relative]) for relative in sorted(files)]


def copy_exclusive(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        with source.open("rb") as incoming, target.open("xb") as outgoing:
            shutil.copyfileobj(incoming, outgoing)
    except Exception:
        # Only remove a file if this call created it.
        if "outgoing" in locals():
            target.unlink(missing_ok=True)
        raise


def export_tex(
    tex: Path, target: Path, project_files: list[tuple[Path, Path]], issues: list[Issue],
) -> list[str]:
    directory = target.with_suffix(".resources")
    created_directory = False
    created_tex = False
    try:
        if project_files:
            directory.mkdir(exist_ok=False)
            created_directory = True
            for relative, source in project_files:
                copy_exclusive(source, directory / relative)
        copy_exclusive(tex, target)
        created_tex = True
        return [str(directory / relative) for relative, _source in project_files]
    except OSError as exc:
        if created_tex:
            target.unlink(missing_ok=True)
        if created_directory:
            shutil.rmtree(directory)
        add(issues, "ERROR", "tex-export", f"cannot export standalone TeX and resources: {exc}")
        return []


def check_pdf_fonts(pdf: Path, require_msbm: bool, issues: list[Issue]) -> None:
    if shutil.which("pdffonts") is None:
        add(issues, "ERROR", "dependency", "pdffonts is unavailable")
        return
    result = run(["pdffonts", str(pdf)])
    if result.returncode or "Syntax Error:" in result.stderr:
        add(issues, "ERROR", "pdf-font", result.stderr.strip() or "pdffonts failed")
        return
    lines = result.stdout.splitlines()[2:]
    if require_msbm and not any("MSBM10" in line.upper() for line in lines):
        add(issues, "ERROR", "pdf-font", "uppercase mathbb is used but MSBM10 is not embedded")
    if any("Type 3" in line for line in lines):
        add(issues, "ERROR", "pdf-font", "Type 3 font found in PDF")
    for line in lines:
        columns = line.split()
        if len(columns) >= 6 and columns[-5].lower() == "no":
            add(issues, "ERROR", "pdf-font", f"unembedded font: {columns[0]}")


def report_payload(report: dict[str, Any], issues: list[Issue]) -> dict[str, Any]:
    order = {"ERROR": 0, "REVIEW": 1, "WARN": 2, "INFO": 3}
    issues.sort(key=lambda issue: (order.get(issue.severity, 9), issue.check, issue.message))
    return {
        **report,
        "issues": [asdict(issue) for issue in issues],
        "errors": sum(issue.severity == "ERROR" for issue in issues),
        "review_items": sum(issue.severity == "REVIEW" for issue in issues),
        "visual_review_required": True,
    }


def write_exclusive(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="") as handle:
        handle.write(text)


def print_report(payload: dict[str, Any]) -> None:
    for issue in payload["issues"]:
        print(f"[{issue['severity']}] {issue['check']}: {issue['message']}")
    print(json.dumps({key: value for key, value in payload.items() if key != "issues"}, ensure_ascii=False))


def command_inspect(args: argparse.Namespace) -> int:
    report, issues, _reader_text = inspect_source(args.source, args.third_party_headings, args.control)
    payload = report_payload(report, issues)
    if args.json_report is not None:
        try:
            write_exclusive(args.json_report, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
        except OSError as exc:
            print(f"cannot write report: {exc}", file=sys.stderr)
            return 1
    print_report(payload)
    return 1 if payload["errors"] else 0


def command_build(args: argparse.Namespace) -> int:
    report, issues, reader_text = inspect_source(args.source, args.third_party_headings, args.control)
    profile = report.get("profile")
    root = project_root(args.source)
    outputs = [
        (args.reader, "reader"),
        (args.pdf, "PDF"),
        (args.build_log, "build log"),
        (args.json_report, "JSON report"),
    ]
    if args.tex is not None:
        outputs.extend(((args.tex, "TeX"), (args.tex.with_suffix(".resources"), "TeX resources")))
        if args.tex.suffix != ".tex":
            add(issues, "ERROR", "output", "--tex must name a .tex file")
    identities = [path.resolve() for path, _label in outputs]
    if len(set(identities)) != len(identities):
        add(issues, "ERROR", "output", "all output paths must be different")
    for path, label in outputs:
        safe_output(path, root, label, issues)
    tex_name = args.tex.name if args.tex is not None else args.pdf.with_suffix(".tex").name
    if re.search(r'[\s{}\\%#$&^~"]', tex_name) or tex_name.startswith("-"):
        add(issues, "ERROR", "output", "TeX/PDF basename must not contain whitespace or TeX-special characters")
    for dependency in ("pandoc", "latexmk", "xelatex", "pdffonts"):
        if shutil.which(dependency) is None:
            add(issues, "ERROR", "dependency", f"required command is unavailable: {dependency}")
    if any(issue.severity == "ERROR" for issue in issues) or not isinstance(profile, dict):
        payload = report_payload(report, issues)
        print_report(payload)
        return 1

    resources = validate_resources(args.source, profile, issues)
    if any(issue.severity == "ERROR" for issue in issues):
        payload = report_payload(report, issues)
        print_report(payload)
        return 1
    try:
        write_exclusive(args.reader, reader_text)
    except OSError as exc:
        add(issues, "ERROR", "reader-derivation", f"cannot write reader: {exc}")
        payload = report_payload(report, issues)
        print_report(payload)
        return 1

    build_log = ""
    try:
        with tempfile.TemporaryDirectory(prefix="final-pdf-build-", dir=root / "tmp") as temporary:
            work = Path(temporary)
            tex = work / tex_name
            resource_name = tex.with_suffix(".resources").name
            stage_resources(resources, work / resource_name)
            command = pandoc_command(
                args.reader.resolve(), tex, profile, resources, reader_text,
                report.get("effective_language"),
            )
            result = run(command, cwd=root)
            build_log += "[final-pdf-build] Pandoc standalone TeX\n" + result.stdout + result.stderr
            if result.returncode or not tex.is_file():
                add(issues, "ERROR", "build", f"Pandoc TeX generation failed with exit code {result.returncode}")
            else:
                text = portable_tex(tex.read_text(encoding="utf-8"), resource_name, resources, issues)
                tex.write_text(text, encoding="utf-8", newline="\n")
                if not any(issue.severity == "ERROR" for issue in issues):
                    result = run([
                        "latexmk", "-norc", "-xelatex", "-interaction=nonstopmode",
                        "-halt-on-error", "-file-line-error", "-recorder", tex.name,
                    ], cwd=work)
                    build_log += "\n[final-pdf-build] latexmk\n" + result.stdout + result.stderr
                    final_log = tex.with_suffix(".log")
                    if final_log.is_file():
                        build_log += "\n" + FINAL_LOG_MARKER + "\n" + final_log.read_text(
                            encoding="utf-8", errors="replace",
                        )
                    built_pdf = tex.with_suffix(".pdf")
                    if result.returncode:
                        add(issues, "ERROR", "build", f"latexmk/XeLaTeX failed with exit code {result.returncode}")
                    elif not built_pdf.is_file():
                        add(issues, "ERROR", "build", "build returned success but PDF is missing")
                    else:
                        copy_exclusive(built_pdf, args.pdf)
                        check_pdf_fonts(args.pdf, report.get("mathbb_uppercase_uses", 0) > 0, issues)
                        if args.tex is not None:
                            project_files = recorded_resources(tex.with_suffix(".fls"), work, root, issues)
                            if not any(issue.severity == "ERROR" for issue in issues):
                                report["tex_resources"] = export_tex(tex, args.tex, project_files, issues)
                                if args.tex.is_file():
                                    report["tex"] = str(args.tex)
    except (OSError, UnicodeError) as exc:
        add(issues, "ERROR", "build", str(exc))
    try:
        write_exclusive(args.build_log, build_log)
    except OSError as exc:
        add(issues, "ERROR", "build-log", f"cannot write build log: {exc}")

    report["reader"] = str(args.reader)
    report["pdf"] = str(args.pdf)
    report["build_log"] = str(args.build_log)
    payload = report_payload(report, issues)
    try:
        write_exclusive(args.json_report, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    except OSError as exc:
        print(f"cannot write report: {exc}", file=sys.stderr)
        return 1
    print_report(payload)
    return 1 if payload["errors"] else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", action="version", version=VERSION)
    subparsers = parser.add_subparsers(dest="command", required=True)

    inspect_parser = subparsers.add_parser("inspect", help="validate the current body and its separate control profile")
    inspect_parser.add_argument("source", type=Path, help="Selected current reader Markdown")
    inspect_parser.add_argument("--control", type=Path, required=True, help="Separate control Markdown containing one build_profile block")
    inspect_parser.add_argument("--third-party-headings", action="store_true")
    inspect_parser.add_argument("--json-report", type=Path)
    inspect_parser.set_defaults(handler=command_inspect)

    build_parser = subparsers.add_parser("build", help="derive and build one PDF without overwriting")
    build_parser.add_argument("source", type=Path, help="Selected current reader Markdown")
    build_parser.add_argument("--control", type=Path, required=True, help="Separate control Markdown containing one build_profile block")
    build_parser.add_argument("--reader", type=Path, required=True)
    build_parser.add_argument("--pdf", type=Path, required=True)
    build_parser.add_argument("--build-log", type=Path, required=True)
    build_parser.add_argument("--json-report", type=Path, required=True)
    build_parser.add_argument("--third-party-headings", action="store_true")
    build_parser.add_argument("--tex", type=Path, help="Export the compiled standalone TeX and its actual project resources")
    build_parser.set_defaults(handler=command_build)

    args = parser.parse_args()
    return args.handler(args)


if __name__ == "__main__":
    sys.exit(main())
