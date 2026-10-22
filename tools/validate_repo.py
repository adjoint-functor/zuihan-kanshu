#!/usr/bin/env python3
"""Validate repository/runtime boundaries without changing the skill."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skill" / "zuihan-kanshu"
VERSION_FILE = ROOT / "VERSION"

REQUIRED_TOP_LEVEL = {
    "LICENSE",
    "NOTICE",
    "SKILL.md",
    "agents",
    "assets",
    "references",
    "scripts",
}
FORBIDDEN_RUNTIME_NAMES = {
    "README.md",
    "CHANGELOG.md",
    "VERSION",
    "maintenance",
    "proposals",
    "archive",
    "tests",
}
VERSIONED_SCRIPTS = (
    SKILL / "scripts" / "research-workbench.py",
    SKILL / "scripts" / "versioned-output.py",
    SKILL / "scripts" / "final-pdf-build.py",
)
EXPECTED_TESTS = {
    "test_plugin_release.py",
    "test_final_pdf_build.py",
    "test_pdf_environment.py",
    "test_preflight_pdf_objects.py",
    "test_matlas_client.py",
    "test_theorem_search_client.py",
    "test_research_workbench.py",
    "test_v7_skill_surface.py",
    "test_versioned_output.py",
}


def fail(message: str) -> None:
    raise SystemExit(f"validation failed: {message}")


def validate_frontmatter() -> None:
    skill_md = SKILL / "SKILL.md"
    text = skill_md.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        fail("SKILL.md has no YAML frontmatter")
    try:
        frontmatter = text.split("---\n", 2)[1]
    except IndexError:
        fail("SKILL.md frontmatter is not closed")
    keys = {
        line.split(":", 1)[0].strip()
        for line in frontmatter.splitlines()
        if line.strip() and not line.lstrip().startswith("#") and ":" in line
    }
    if keys != {"name", "description"}:
        fail(f"unexpected SKILL.md frontmatter keys: {sorted(keys)}")
    if "name: zuihan-kanshu" not in frontmatter:
        fail("SKILL.md name does not match the runtime directory")


def validate_version() -> None:
    version = VERSION_FILE.read_text(encoding="utf-8").strip()
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        fail(f"invalid VERSION value: {version!r}")
    skill_text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    title_versions = re.findall(r"(?m)^# 瑞般观珠 v(\d+\.\d+\.\d+)$", skill_text)
    if title_versions != [version]:
        fail("SKILL.md title and VERSION disagree")
    for script in VERSIONED_SCRIPTS:
        text = script.read_text(encoding="utf-8")
        if f'VERSION = "{version}"' not in text:
            fail(f"{script.relative_to(ROOT)} and VERSION disagree")
        reported = subprocess.run(
            [sys.executable, str(script), "--version"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        if reported != version:
            fail(
                f"{script.relative_to(ROOT)} reports {reported!r}, "
                f"expected {version!r}"
            )


def validate_runtime_boundary() -> None:
    if not SKILL.is_dir():
        fail("runtime skill directory is missing")
    actual_top_level = {path.name for path in SKILL.iterdir()}
    if actual_top_level != REQUIRED_TOP_LEVEL:
        fail(
            "runtime top-level entries differ: "
            f"expected {sorted(REQUIRED_TOP_LEVEL)}, got {sorted(actual_top_level)}"
        )
    for path in SKILL.rglob("*"):
        if path.is_symlink():
            fail(f"runtime contains a symlink: {path.relative_to(ROOT)}")
        if path.name in FORBIDDEN_RUNTIME_NAMES:
            fail(f"maintenance material entered runtime: {path.relative_to(ROOT)}")
        if path.name == "__pycache__" or path.suffix in {".pyc", ".pyo"}:
            fail(f"runtime contains generated cache: {path.relative_to(ROOT)}")
        if path.is_file() and path.name.startswith("test_") and path.suffix == ".py":
            fail(f"repository test entered runtime: {path.relative_to(ROOT)}")


def validate_repository_tests() -> None:
    tests = ROOT / "tests"
    if not tests.is_dir():
        fail("repository tests directory is missing")
    actual = {path.name for path in tests.iterdir() if path.is_file()}
    if actual != EXPECTED_TESTS:
        fail(
            "repository tests differ: "
            f"expected {sorted(EXPECTED_TESTS)}, got {sorted(actual)}"
        )
    unexpected_directories = [path.name for path in tests.iterdir() if path.is_dir()]
    if unexpected_directories:
        fail(f"unexpected test directories: {sorted(unexpected_directories)}")


def validate_python() -> None:
    for script in sorted(SKILL.rglob("*.py")):
        compile(script.read_text(encoding="utf-8"), str(script), "exec")
    for test in sorted((ROOT / "tests").glob("test_*.py")):
        compile(test.read_text(encoding="utf-8"), str(test), "exec")


def validate_utf8() -> None:
    for path in sorted(SKILL.rglob("*")):
        if path.is_file():
            if path.suffix == ".png":
                if not path.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"):
                    fail(f"runtime PNG has an invalid signature: {path.relative_to(ROOT)}")
            else:
                path.read_text(encoding="utf-8")


def main() -> None:
    validate_runtime_boundary()
    validate_frontmatter()
    validate_version()
    validate_repository_tests()
    validate_utf8()
    validate_python()
    print("repository and runtime boundaries are valid")


if __name__ == "__main__":
    main()
