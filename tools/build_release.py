#!/usr/bin/env python3
"""Validate and build a skill or a portable skills-only plugin from one source."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import struct
import unicodedata
import zipfile
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skill" / "zuihan-kanshu"
MANIFEST = ROOT / "tools" / "runtime-files.txt"
VERSION_FILE = ROOT / "VERSION"
PLUGIN_TEMPLATE = ROOT / "tools" / "plugin-manifest.json.in"
PLUGIN_NAME = "zuihan-kanshu"
SKILL_NAME = "zuihan-kanshu"
PLUGIN_SCHEMA = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
DISTRIBUTION_NOTICES = ("LICENSE", "NOTICE")
PLUGIN_ICON_SIZES = {
    "composerIcon": 256,
    "composerIconDark": 256,
    "logo": 1024,
    "logoDark": 1024,
}


class ReleaseError(RuntimeError):
    pass


def release_version() -> str:
    version = VERSION_FILE.read_text(encoding="utf-8").strip()
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        raise ReleaseError(f"invalid VERSION value: {version!r}")
    return version


def manifest_paths() -> list[PurePosixPath]:
    lines = MANIFEST.read_text(encoding="utf-8").splitlines()
    if not lines or any(not line or line != line.strip() for line in lines):
        raise ReleaseError("runtime manifest must contain one exact path per line")
    if lines != sorted(set(lines)):
        raise ReleaseError("runtime manifest must be sorted and contain no duplicates")
    paths = [PurePosixPath(line) for line in lines]
    for path in paths:
        if (
            path.is_absolute()
            or "\\" in path.as_posix()
            or ".." in path.parts
            or path.as_posix() in {"", "."}
        ):
            raise ReleaseError(f"unsafe runtime path: {path}")
    return paths


def actual_runtime_files() -> set[PurePosixPath]:
    return {
        PurePosixPath(path.relative_to(SKILL).as_posix())
        for path in SKILL.rglob("*")
        if path.is_file()
        and "__pycache__" not in path.parts
        and path.suffix not in {".pyc", ".pyo"}
    }


def check_runtime() -> list[PurePosixPath]:
    expected = manifest_paths()
    expected_set = set(expected)
    actual = actual_runtime_files()
    missing = sorted(expected_set - actual, key=str)
    extra = sorted(actual - expected_set, key=str)
    if missing or extra:
        details = []
        if missing:
            details.append("missing: " + ", ".join(map(str, missing)))
        if extra:
            details.append("extra: " + ", ".join(map(str, extra)))
        raise ReleaseError("; ".join(details))
    for relative in expected:
        source = SKILL / Path(relative.as_posix())
        if source.is_symlink():
            raise ReleaseError(f"runtime file is a symlink: {relative}")
    return expected


def build_release(output_dir: Path) -> Path:
    expected = check_runtime()
    version = release_version()
    target = output_dir / "skill" / f"{SKILL_NAME}-v{version}"
    if target.exists():
        raise ReleaseError(f"release target already exists: {target}")
    if SKILL.resolve() in target.resolve().parents or target.resolve() == SKILL.resolve():
        raise ReleaseError("build output must not be inside the runtime source")
    for relative in expected:
        source = SKILL / Path(relative.as_posix())
        destination = target / Path(relative.as_posix())
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    produced = {
        PurePosixPath(path.relative_to(target).as_posix())
        for path in target.rglob("*")
        if path.is_file()
    }
    if produced != set(expected):
        raise ReleaseError("materialized release differs from the runtime manifest")
    return target


def plugin_manifest() -> dict:
    template = PLUGIN_TEMPLATE.read_text(encoding="utf-8")
    if template.count('"@VERSION@"') != 1:
        raise ReleaseError("plugin template must contain exactly one VERSION placeholder")
    manifest = json.loads(template.replace('"@VERSION@"', json.dumps(release_version())))
    if manifest.get("$schema") != PLUGIN_SCHEMA or manifest.get("name") != PLUGIN_NAME:
        raise ReleaseError("plugin schema or stable name does not match the package")
    extension = manifest.get("extensions", {}).get("com.openai", {})
    for scope in (manifest, extension):
        if any(field in scope for field in ("mcpServers", "mcp", "hooks", "commands", "agents", "lspServers")):
            raise ReleaseError("the plugin must contain only skills and presentation metadata")
    interface = extension.get("interface", {})
    if interface.get("displayName") != "瑞般观珠":
        raise ReleaseError("plugin display name must be 瑞般观珠")
    plugin_icon_paths(manifest)
    for field in ("brandColor", "brandColorDark"):
        color = interface.get(field)
        if not isinstance(color, str) or not re.fullmatch(r"#[0-9A-Fa-f]{6}", color):
            raise ReleaseError(f"plugin {field} must be a six-digit hex color")
    return manifest


def plugin_icon_paths(manifest: dict) -> dict[str, PurePosixPath]:
    interface = manifest["extensions"]["com.openai"]["interface"]
    icons = {}
    for field in PLUGIN_ICON_SIZES:
        value = interface.get(field)
        if not isinstance(value, str) or not value.startswith("./assets/"):
            raise ReleaseError(f"plugin {field} must use a contained asset path")
        relative = PurePosixPath(value[2:])
        if (
            "\\" in value
            or ".." in relative.parts
            or relative.as_posix() != value[2:]
            or relative.suffix != ".png"
        ):
            raise ReleaseError(f"plugin {field} must use a contained PNG asset path")
        icons[field] = relative
    return icons


def validate_png_icon(source: Path, expected_size: int) -> None:
    data = source.read_bytes()
    if (
        len(data) < 33
        or len(data) > 5 * 1024 * 1024
        or data[:8] != b"\x89PNG\r\n\x1a\n"
        or data[12:16] != b"IHDR"
    ):
        raise ReleaseError(f"icon must be a PNG no larger than 5 MiB: {source.name}")
    width, height = struct.unpack(">II", data[16:24])
    if width != height or width != expected_size or not 48 <= width <= 4096:
        raise ReleaseError(f"icon must be {expected_size} x {expected_size}: {source.name}")


def plugin_files() -> dict[PurePosixPath, Path | bytes]:
    expected = check_runtime()
    manifest = plugin_manifest()
    files: dict[PurePosixPath, Path | bytes] = {
        PurePosixPath("plugin.json"): (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8"),
    }
    for name in DISTRIBUTION_NOTICES:
        relative = PurePosixPath(name)
        if relative not in expected:
            raise ReleaseError(f"distribution notice is absent from the runtime manifest: {relative}")
        files[relative] = SKILL / relative
    for field, relative in plugin_icon_paths(manifest).items():
        if relative not in expected:
            raise ReleaseError(f"plugin icon is absent from the runtime manifest: {relative}")
        source = SKILL / relative
        validate_png_icon(source, PLUGIN_ICON_SIZES[field])
        files[relative] = source
    for relative in expected:
        files[PurePosixPath("skills") / SKILL_NAME / relative] = SKILL / relative
    normalized = [unicodedata.normalize("NFC", path.as_posix()).casefold() for path in files]
    if len(normalized) != len(set(normalized)):
        raise ReleaseError("plugin paths collide after Unicode or case normalization")
    return files


def build_plugin(output_dir: Path, *, archive: bool = False) -> tuple[Path, Path | None]:
    files = plugin_files()
    target = output_dir / "plugin" / f"{PLUGIN_NAME}-v{release_version()}"
    archive_path = target.parent / (target.name + ".zip") if archive else None
    if target.exists() or (archive_path and archive_path.exists()):
        raise ReleaseError(f"plugin target already exists: {target}")
    if SKILL.resolve() in target.resolve().parents or target.resolve() == SKILL.resolve():
        raise ReleaseError("build output must not be inside the runtime source")
    for relative, source in files.items():
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(source, bytes):
            destination.write_bytes(source)
        else:
            shutil.copy2(source, destination)
    produced = {PurePosixPath(path.relative_to(target).as_posix()) for path in target.rglob("*") if path.is_file()}
    if produced != set(files):
        raise ReleaseError("materialized plugin differs from its declared files")
    if archive_path:
        with zipfile.ZipFile(archive_path, "x", compression=zipfile.ZIP_DEFLATED) as handle:
            for relative in sorted(files):
                info = zipfile.ZipInfo(relative.as_posix(), date_time=(1980, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                handle.writestr(info, (target / relative).read_bytes())
    return target, archive_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true")
    group.add_argument("--output-dir", type=Path, help="write into a skill/ or plugin/ subdirectory")
    parser.add_argument("--format", choices=("skill", "plugin"), default="skill")
    parser.add_argument("--zip", action="store_true", help="also create a reproducible plugin ZIP")
    return parser.parse_args()


def main() -> int:
    arguments = parse_args()
    try:
        expected = check_runtime()
        if arguments.zip and (arguments.check or arguments.format != "plugin"):
            raise ReleaseError("--zip requires --format plugin and --output-dir")
        if arguments.format == "plugin":
            files = plugin_files()
        if arguments.check:
            print(f"runtime manifest is valid: {len(expected)} files")
            if arguments.format == "plugin":
                print(f"skills-only plugin is valid: {len(files)} files")
            return 0
        if arguments.format == "plugin":
            target, archive_path = build_plugin(arguments.output_dir, archive=arguments.zip)
            print(target)
            if archive_path:
                print(archive_path)
        else:
            print(build_release(arguments.output_dir))
        return 0
    except (OSError, ValueError, ReleaseError) as exc:
        print(f"release build failed: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
