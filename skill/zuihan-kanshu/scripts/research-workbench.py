#!/usr/bin/env python3
"""Local filesystem workbench; Library saving and archiving are separate operations."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import shutil
import stat
import sys
from pathlib import Path
from typing import Iterable, NamedTuple, Sequence


VERSION = "8.4.0"
INITIAL_PROJECT_VERSION = "1.0.0"
ASSET_DIR = Path(__file__).resolve().parents[1] / "assets" / "research-project"

CORE_ROLES = (
    "数学主稿",
    "计算草稿",
    "研究日志",
    "下一次入口",
    "参考资料台账",
)
PROJECT_DIRS = ("download", "old", "tmp")
TEMPLATES = {
    "数学主稿": ASSET_DIR / "main.md.tmpl",
    "计算草稿": ASSET_DIR / "scratch.md.tmpl",
    "研究日志": ASSET_DIR / "log.md.tmpl",
    "下一次入口": ASSET_DIR / "entry.md.tmpl",
    "参考资料台账": ASSET_DIR / "ledger.md.tmpl",
}
ACTIVE_REVISION_DIR = "active-revision"
REVISION_RECORD_FILE = "revision.json"

_ROLE_PATTERN = "|".join(re.escape(role) for role in CORE_ROLES)
VERSIONED_FILE_RE = re.compile(
    rf"^(?P<project>.+)_(?P<role>{_ROLE_PATTERN})_v"
    r"(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\."
    r"(?P<patch>0|[1-9]\d*)\.md$"
)
UNVERSIONED_ROLE_RE = re.compile(rf"^(?:.+_)?(?:{_ROLE_PATTERN})\.md$")
SEMVER_RE = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")

ROUND_TYPES = {
    "substantive": "实质研究轮",
    "review": "研究回顾轮",
    "maintenance": "规范维护轮",
}
REVIEW_OUTCOMES = {
    "continue": "继续",
    "rewrite": "改写分支",
    "return": "返回上层主线",
    "stop": "停止",
}
_CODE_LOCATOR = r"`[^`\r\n]+`"
ENTRY_LOCATOR_RE = re.compile(
    rf"(?:{_CODE_LOCATOR}(?:\s*的\s*台账行\s*{_CODE_LOCATOR})?|"
    r"(?:第\s*)?\d+(?:\s*[-–—]\s*\d+)?\s*页|"
    r"§\s*[0-9A-Za-z.\-]+|"
    r"(?:定理|命题|引理|定义|公式|表|段落?|页码?)\s*"
    r"[0-9A-Za-z一二三四五六七八九十百零.\-（）()]+)"
)
RAW_HTML_BLOCK_TAGS = frozenset(
    "address article aside base basefont blockquote body caption center col colgroup "
    "dd details dialog dir div dl dt fieldset figcaption figure footer form frame "
    "frameset h1 h2 h3 h4 h5 h6 head header hr html iframe legend li link main "
    "menu menuitem nav noframes ol optgroup option p param pre script search section "
    "style summary table tbody td textarea tfoot th thead title tr track ul".split()
)
HTML_TAG_NAMES = frozenset(
    "a abbr acronym address applet area article aside audio b base basefont bdi bdo big "
    "blockquote body br button canvas caption center cite code col colgroup data datalist "
    "dd del details dfn dialog dir div dl dt em embed fieldset figcaption figure font "
    "footer form frame frameset h1 h2 h3 h4 h5 h6 head header hgroup hr html i iframe img "
    "input ins kbd label legend li link main map mark menu menuitem meta meter nav noframes "
    "noscript object ol optgroup option output p param picture pre progress q rb rp rt rtc "
    "ruby s samp script search section select slot small source span strike strong style sub "
    "summary sup table tbody td template textarea tfoot th thead time title tr track tt u ul "
    "var video wbr".split()
)
_HTML_TAG_PATTERN = "|".join(
    sorted((re.escape(tag) for tag in HTML_TAG_NAMES), key=len, reverse=True)
)
CONTROL_MARKUP_RE = re.compile(
    rf"(?:<!--|-->|<!\[CDATA\[|<\?|<![A-Z]|"
    rf"</?(?:{_HTML_TAG_PATTERN})(?=[\s/>])[^>\n]*>)",
    re.I,
)
CONTROL_FENCE_RE = re.compile(r"^[ \t]*(?:`{3,}|~{3,})", re.M)
CONTROL_LINE_TAG_RE = re.compile(
    r"^[ \t]{0,3}</?[A-Za-z][A-Za-z0-9-]*(?=[\s/>])", re.M
)
RAW_HTML_SPECIAL_START_RE = re.compile(
    r"^[ \t]{0,3}<(?P<tag>pre|script|style|textarea)\b", re.I
)
RAW_HTML_TYPE6_START_RE = re.compile(
    r"^[ \t]{0,3}</?(?P<tag>[A-Za-z][A-Za-z0-9-]*)(?=[\s/>])", re.I
)
RAW_HTML_COMPLETE_TAG_LINE_RE = re.compile(
    r"^[ \t]{0,3}</?[A-Za-z][A-Za-z0-9-]*"
    r"(?:\s+[^<>\n]*)?/?>[ \t]*(?:\n)?$",
    re.I,
)
LOG_HEADING_RE = re.compile(r"^##\s+(\d{4}-\d{2}-\d{2})｜(.+?)\s*$", re.M)

class WorkbenchError(Exception):
    """A user-correctable workbench error."""


class ProjectState(NamedTuple):
    """One coherent five-file generation in a directory."""

    project: str
    version: str
    files: dict[str, Path]


def _today() -> str:
    return dt.date.today().isoformat()


def _is_calendar_date(value: str | None) -> bool:
    if value is None or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return False
    try:
        dt.date.fromisoformat(value)
    except ValueError:
        return False
    return True


def _clean_inline(value: str, field: str) -> str:
    value = " ".join(value.split())
    if not value:
        raise WorkbenchError(f"{field}不能为空")
    return value


def _clean_project_name(value: str) -> str:
    value = _clean_inline(value, "项目名")
    if value in {".", ".."} or "/" in value or "\\" in value:
        raise WorkbenchError("项目名不能含路径分隔符，也不能是 . 或 ..")
    return value


def _escape_table_cell(value: str) -> str:
    return _clean_inline(value, "参考材料").replace("|", "\\|")


def _parse_version(value: str) -> tuple[int, int, int]:
    match = SEMVER_RE.fullmatch(value)
    if not match:
        raise WorkbenchError(f"版本号必须是 MAJOR.MINOR.PATCH：{value}")
    return tuple(int(part) for part in match.groups())  # type: ignore[return-value]


def _bump_version(value: str, bump: str) -> str:
    major, minor, patch = _parse_version(value)
    if bump == "major":
        return f"{major + 1}.0.0"
    if bump == "minor":
        return f"{major}.{minor + 1}.0"
    if bump == "patch":
        return f"{major}.{minor}.{patch + 1}"
    raise WorkbenchError(f"未知升版类型：{bump}")


def _normalize_round_type(value: str) -> str:
    if value not in ROUND_TYPES:
        raise WorkbenchError("修订类型必须是 substantive、review 或 maintenance")
    return value





def _filename_map(project: str, version: str) -> dict[str, str]:
    project = _clean_project_name(project)
    _parse_version(version)
    return {role: f"{project}_{role}_v{version}.md" for role in CORE_ROLES}


def _parse_versioned_filename(path: Path) -> tuple[str, str, str] | None:
    match = VERSIONED_FILE_RE.fullmatch(path.name)
    if not match:
        return None
    version = f"{match.group('major')}.{match.group('minor')}.{match.group('patch')}"
    return match.group("project"), match.group("role"), version


def _is_regular_file(path: Path) -> bool:
    return path.is_file() and not path.is_symlink()


def _render_template(path: Path, replacements: dict[str, str]) -> str:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise WorkbenchError(f"无法读取模板：{path}") from exc
    for key, value in replacements.items():
        text = text.replace("{{" + key + "}}", value)
    unresolved = re.findall(r"\{\{[A-Z_]+\}\}", text)
    if unresolved:
        raise WorkbenchError(f"模板仍有未替换字段：{', '.join(unresolved)}")
    return text.rstrip() + "\n"


def _replace_section(text: str, heading: str, body: str) -> str:
    pattern = re.compile(
        rf"^##\s+{re.escape(heading)}\s*$.*?(?=^##\s+|\Z)", re.M | re.S
    )
    replacement = f"## {heading}\n\n{body.strip()}\n\n"
    structural_text = _without_noncontent_blocks(text)
    match = pattern.search(structural_text)
    if match:
        return (text[: match.start()] + replacement + text[match.end() :]).rstrip() + "\n"
    anchor = re.search(
        r"^##\s+当前问题与最近进展\s*$", structural_text, re.M
    )
    if anchor:
        return (text[: anchor.start()] + replacement + text[anchor.start() :]).rstrip() + "\n"
    return (text.rstrip() + "\n\n" + replacement).rstrip() + "\n"


def _set_document_metadata(
    text: str,
    version: str,
    filename: str,
    *,
    include_current_file: bool = True,
) -> str:
    """Set mutable version metadata; the clean main omits its own filename."""
    version_line = f"- 项目版本：v{version}"
    current_line = f"- 当前文件：`{filename}`"
    structural_text = _without_noncontent_blocks(text)
    version_match = re.search(
        r"^-\s*项目版本\s*[：:].*$", structural_text, re.M
    )
    if version_match:
        text = (
            text[: version_match.start()]
            + version_line
            + text[version_match.end() :]
        )
    else:
        title = re.search(r"^#\s+.+$", structural_text, re.M)
        if not title:
            raise WorkbenchError(f"文件缺少一级标题，无法写入版本信息：{filename}")
        text = text[: title.end()] + "\n\n" + version_line + text[title.end() :]
    if not include_current_file:
        structural_text = _without_noncontent_blocks(text)
        current_match = re.search(
            r"^-\s*当前文件\s*[：:].*\n?", structural_text, re.M
        )
        if current_match:
            text = text[: current_match.start()] + text[current_match.end() :]
        return text.rstrip() + "\n"
    structural_text = _without_noncontent_blocks(text)
    current_match = re.search(
        r"^-\s*当前文件\s*[：:].*$", structural_text, re.M
    )
    if current_match:
        text = (
            text[: current_match.start()]
            + current_line
            + text[current_match.end() :]
        )
    else:
        structural_text = _without_noncontent_blocks(text)
        version_match = re.search(
            r"^-\s*项目版本\s*[：:].*$", structural_text, re.M
        )
        if not version_match:
            raise WorkbenchError(f"文件缺少项目版本，无法写入当前文件：{filename}")
        text = text[: version_match.end()] + "\n" + current_line + text[version_match.end() :]
    return text.rstrip() + "\n"


def _set_entry_metadata(
    text: str,
    version: str,
    filenames: dict[str, str],
    previous_filenames: dict[str, str] | None = None,
) -> str:
    """Write the shared version and exact five filenames into the entry."""
    if previous_filenames is not None:
        for role in CORE_ROLES:
            text = text.replace(previous_filenames[role], filenames[role])

    project = _parse_versioned_filename(Path(filenames["下一次入口"]))[0]
    title = re.search(r"^#\s+[^\n]+", _without_noncontent_blocks(text), re.M)
    if title is None:
        text = f"# {project}：下一次入口\n\n" + text
    else:
        text = text[:title.start()] + f"# {project}：下一次入口" + text[title.end():]
    text = _set_document_metadata(text, version, filenames["下一次入口"])
    structural_text = _without_noncontent_blocks(text)
    updated_match = re.search(
        r"^-\s*最近更新\s*[：:].*$", structural_text, re.M
    )
    if updated_match is None:
        text = text.rstrip() + f"\n\n- 最近更新：{_today()}\n"
    else:
        text = (
            text[: updated_match.start()]
            + f"- 最近更新：{_today()}"
            + text[updated_match.end() :]
        )
    project = _parse_versioned_filename(Path(filenames["下一次入口"]))[0]
    defaults = {"项目": project}
    for key, value in defaults.items():
        if _metadata_value(text, key) is None:
            title_end = text.find("\n")
            text = text[:title_end] + f"\n\n- {key}：{value}" + text[title_end:]
    body = "\n".join(f"- {role}：`{filenames[role]}`" for role in CORE_ROLES)
    return _replace_section(text, "当前五文件", body)


def _build_initial_documents(
    name: str,
    goal: str,
    references: Sequence[str],
    version: str,
) -> tuple[dict[str, str], dict[str, str]]:
    name = _clean_project_name(name)
    goal = _clean_inline(goal, "研究目标")
    _parse_version(version)
    cleaned_references = [_escape_table_cell(item) for item in references]
    reading_lines = ""
    literature_rows = ""
    if cleaned_references:
        literature_rows = "\n".join(
            f"| R{index:03d} | {item} | 参考材料 | 身份待核 | 待验证 | 按研究目标确定 | 待确定 |  |"
            for index, item in enumerate(cleaned_references, start=1)
        )
    filenames = _filename_map(name, version)
    if cleaned_references:
        reading_lines = (
            f"- `{filenames['参考资料台账']}` → `## 文献条目` 的台账行 `R001`："
            "取得台账行"
        )
    replacements = {
        "PROJECT_NAME": name,
        "RESEARCH_GOAL": goal,
        "CURRENT_DATE": _today(),
        "CURRENT_VERSION": f"v{version}",
        "REFERENCE_READING": reading_lines,
        "LITERATURE_ROWS": literature_rows,
        "MAIN_FILE": filenames["数学主稿"],
        "SCRATCH_FILE": filenames["计算草稿"],
        "LOG_FILE": filenames["研究日志"],
        "ENTRY_FILE": filenames["下一次入口"],
        "LEDGER_FILE": filenames["参考资料台账"],
    }
    rendered = {
        role: _render_template(template, replacements)
        for role, template in TEMPLATES.items()
    }
    for role in CORE_ROLES:
        if role in {"研究日志", "下一次入口"}:
            continue
        rendered[role] = _set_document_metadata(
            rendered[role],
            version,
            filenames[role],
            include_current_file=role != "数学主稿",
        )
    rendered["下一次入口"] = _set_entry_metadata(
        rendered["下一次入口"], version, filenames
    )
    return filenames, rendered


def _unversioned_research_files(project_dir: Path) -> list[str]:
    result: list[str] = []
    for path in project_dir.glob("*.md"):
        if (
            _parse_versioned_filename(path) is None
            and UNVERSIONED_ROLE_RE.fullmatch(path.name)
        ):
            result.append(path.name)
    return sorted(result)


def _versioned_research_files(project_dir: Path) -> list[str]:
    return sorted(
        path.name
        for path in project_dir.glob("*.md")
        if _parse_versioned_filename(path) is not None
    )


def _discover_state(project_dir: Path) -> tuple[ProjectState | None, list[str]]:
    records: list[tuple[str, str, str, Path]] = []
    issues: list[str] = []
    for path in project_dir.glob("*.md"):
        parsed = _parse_versioned_filename(path)
        if parsed:
            if not _is_regular_file(path):
                issues.append(f"研究文件路径不是普通文件：{path.name}")
                continue
            project, role, version = parsed
            records.append((project, role, version, path))
    if not records:
        issues.append("项目顶层没有发现带项目名和版本号的研究五文件")
        return None, issues
    identities = {(project, version) for project, _, version, _ in records}
    if len(identities) != 1:
        labels = "、".join(
            f"{project} v{version}" for project, version in sorted(identities)
        )
        issues.append(f"项目顶层必须只保留一套同版本研究文件；当前发现：{labels}")
        return None, issues
    project, version = next(iter(identities))
    files: dict[str, Path] = {}
    for _, role, _, path in records:
        if role in files:
            issues.append(f"当前版本出现重复角色：{role}")
        files[role] = path
    missing = [role for role in CORE_ROLES if role not in files]
    if missing:
        issues.append("当前版本缺少研究文件：" + "、".join(missing))
    expected = _filename_map(project, version)
    for role, path in files.items():
        if path.name != expected[role]:
            issues.append(f"研究文件名不符合统一命名：{path.name}")
    if issues:
        return None, issues
    return ProjectState(project, version, files), []


def _require_state(project_dir: Path) -> ProjectState:
    if project_dir.is_symlink():
        raise WorkbenchError(f"项目目录不得是符号链接：{project_dir}")
    if not project_dir.is_dir():
        raise WorkbenchError(f"项目目录不存在：{project_dir}")
    state, issues = _discover_state(project_dir)
    if issues or state is None:
        raise WorkbenchError("项目目录无法确定唯一当前版本：" + "；".join(issues))
    return state


def _ensure_project_dirs(project_dir: Path) -> None:
    if project_dir.is_symlink():
        raise WorkbenchError(f"项目目录不得是符号链接：{project_dir}")
    try:
        for dirname in PROJECT_DIRS:
            path = project_dir / dirname
            if path.exists() or path.is_symlink():
                if path.is_symlink() or not path.is_dir():
                    raise WorkbenchError(
                        f"项目管理目录必须是项目内的普通目录：{dirname}/"
                    )
                continue
            path.mkdir()
        active = project_dir / "tmp" / ACTIVE_REVISION_DIR
        if active.exists() or active.is_symlink():
            if active.is_symlink() or not active.is_dir():
                raise WorkbenchError(
                    f"进行中升版目录必须是项目内的普通目录："
                    f"tmp/{ACTIVE_REVISION_DIR}/"
                )
    except OSError as exc:
        raise WorkbenchError(f"无法建立项目目录：{project_dir}") from exc


def _managed_directory_issues(project_dir: Path) -> list[str]:
    issues: list[str] = []
    if project_dir.is_symlink():
        return [f"项目目录不得是符号链接：{project_dir}"]
    for dirname in PROJECT_DIRS:
        path = project_dir / dirname
        if path.is_symlink():
            issues.append(f"项目管理目录不得是符号链接：{dirname}/")
        elif not path.is_dir():
            issues.append(f"缺少项目目录：{dirname}/")
    active = project_dir / "tmp" / ACTIVE_REVISION_DIR
    if active.exists() or active.is_symlink():
        if active.is_symlink() or not active.is_dir():
            issues.append(
                f"进行中升版目录必须是项目内的普通目录："
                f"tmp/{ACTIVE_REVISION_DIR}/"
            )
    return issues


def _require_managed_directories(project_dir: Path) -> None:
    issues = _managed_directory_issues(project_dir)
    if issues:
        raise WorkbenchError("项目管理目录不合法：" + "；".join(issues))


def init_project(
    project_dir: Path,
    name: str,
    goal: str,
    references: Sequence[str],
    version: str = INITIAL_PROJECT_VERSION,
) -> None:
    """Create a versioned five-file workbench without overwriting."""
    filenames, rendered = _build_initial_documents(name, goal, references, version)
    if project_dir.is_symlink():
        raise WorkbenchError(f"项目目录不得是符号链接：{project_dir}")
    if project_dir.exists() and not project_dir.is_dir():
        raise WorkbenchError(f"项目路径不是目录：{project_dir}")
    if project_dir.is_dir():
        versioned = _versioned_research_files(project_dir)
        unversioned = _unversioned_research_files(project_dir)
        collisions = [
            filename for filename in filenames.values() if (project_dir / filename).exists()
        ]
        if versioned or unversioned or collisions:
            names = sorted(set(versioned + unversioned + collisions))
            raise WorkbenchError(
                "为避免覆盖，初始化已停止；项目中已有研究文件：" + "、".join(names)
            )

    template_issues: list[str] = []
    _validate_main(
        rendered["数学主稿"],
        template_issues,
        expected_project=_clean_project_name(name),
    )
    _validate_scratch(rendered["计算草稿"], template_issues)
    _validate_entry(
        rendered["下一次入口"],
        template_issues,
        expected_files=filenames,
        expected_version=version,
        expected_project=_clean_project_name(name),
        expected_anchor_texts={
            "必读主稿": rendered["数学主稿"],
            "必读计算草稿": rendered["计算草稿"],
            "参考材料": rendered["参考资料台账"],
        },
    )
    if template_issues:
        raise WorkbenchError("初始化内容不符合工作台约束：" + "；".join(template_issues))

    created: list[Path] = []
    try:
        project_dir.mkdir(parents=True, exist_ok=True)
        _ensure_project_dirs(project_dir)
        for role in CORE_ROLES:
            target = project_dir / filenames[role]
            with target.open("x", encoding="utf-8", newline="\n") as handle:
                handle.write(rendered[role])
            created.append(target)
    except (OSError, WorkbenchError) as exc:
        for path in reversed(created):
            try:
                path.unlink()
            except OSError:
                pass
        if isinstance(exc, WorkbenchError):
            raise
        raise WorkbenchError(f"无法建立项目工作台：{project_dir}") from exc


def _read_text(path: Path, label: str, issues: list[str]) -> str | None:
    if not path.is_file():
        issues.append(f"缺少{label}：{path.name}")
        return None
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        issues.append(f"{label}必须是可读取的 UTF-8 文本：{path.name}")
        return None


def _section_map(text: str) -> dict[str, str]:
    text = _without_noncontent_blocks(text)
    matches = list(re.finditer(r"^##\s+(.+?)\s*$", text, re.M))
    result: dict[str, str] = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        result[match.group(1).strip()] = text[match.end() : end].strip()
    return result


def _without_fenced_blocks(text: str) -> str:
    """Remove Markdown fenced blocks while preserving their line boundaries."""
    visible: list[str] = []
    fence_character: str | None = None
    fence_length = 0
    for line in text.splitlines(keepends=True):
        marker = re.match(r"^\s*(`{3,}|~{3,})", line)
        if fence_character is None:
            if marker is None:
                visible.append(line)
                continue
            fence_character = marker.group(1)[0]
            fence_length = len(marker.group(1))
        elif re.match(
            rf"^\s*{re.escape(fence_character)}{{{fence_length},}}\s*$", line
        ):
            fence_character = None
            fence_length = 0
        visible.append("".join("\n" if char == "\n" else " " for char in line))
    return "".join(visible)


def _erase_preserving_lines(match: re.Match[str]) -> str:
    return "".join("\n" if char == "\n" else " " for char in match.group(0))


def _without_html_comments(text: str) -> str:
    return re.sub(
        r"<!--.*?(?:-->|$)",
        _erase_preserving_lines,
        text,
        flags=re.S,
    )


def _without_raw_html_blocks(text: str) -> str:
    for pattern in (
        r"<!\[CDATA\[.*?(?:\]\]>|$)",
        r"<\?.*?(?:\?>|$)",
        r"<![A-Z].*?(?:>|$)",
    ):
        text = re.sub(pattern, _erase_preserving_lines, text, flags=re.I | re.S)

    visible: list[str] = []
    active_special_tag: str | None = None
    active_until_blank = False
    for line in text.splitlines(keepends=True):
        if active_special_tag is not None:
            visible.append(
                "".join("\n" if char == "\n" else " " for char in line)
            )
            if re.search(rf"</{re.escape(active_special_tag)}\s*>", line, re.I):
                active_special_tag = None
            continue
        if active_until_blank:
            if not line.strip():
                visible.append(line)
                active_until_blank = False
            else:
                visible.append(
                    "".join("\n" if char == "\n" else " " for char in line)
                )
            continue

        special = RAW_HTML_SPECIAL_START_RE.match(line)
        if special is not None:
            tag = special.group("tag").casefold()
            visible.append(
                "".join("\n" if char == "\n" else " " for char in line)
            )
            if not re.search(rf"</{re.escape(tag)}\s*>", line[special.end() :], re.I):
                active_special_tag = tag
            continue

        type6 = RAW_HTML_TYPE6_START_RE.match(line)
        standard_block = (
            type6 is not None
            and type6.group("tag").casefold() in RAW_HTML_BLOCK_TAGS
        )
        complete_or_custom_tag = type6 is not None and ">" in line
        if (
            standard_block
            or complete_or_custom_tag
            or RAW_HTML_COMPLETE_TAG_LINE_RE.fullmatch(line)
        ):
            visible.append(
                "".join("\n" if char == "\n" else " " for char in line)
            )
            active_until_blank = True
            continue
        visible.append(line)
    return "".join(visible)


def _locator_has_canonical_form(locator: str) -> bool:
    return ENTRY_LOCATOR_RE.fullmatch(locator.strip()) is not None


def _without_noncontent_blocks(text: str) -> str:
    text = _without_fenced_blocks(text)
    text = _without_html_comments(text)
    return _without_raw_html_blocks(text)


def _visible_prose_without_markup(text: str) -> str:
    text = _without_fenced_blocks(text)
    text = _without_html_comments(text)
    for tag in ("pre", "script", "style", "textarea"):
        text = re.sub(
            rf"<{tag}\b[^>]*>.*?(?:</{tag}\s*>|$)",
            _erase_preserving_lines,
            text,
            flags=re.I | re.S,
        )
    for pattern in (
        r"<!\[CDATA\[.*?(?:\]\]>|$)",
        r"<\?.*?(?:\?>|$)",
        r"<![A-Z].*?(?:>|$)",
    ):
        text = re.sub(pattern, _erase_preserving_lines, text, flags=re.I | re.S)
    return re.sub(
        r"</?[A-Za-z][A-Za-z0-9-]*(?=[\s/>])[^>\n]*>",
        _erase_preserving_lines,
        text,
        flags=re.I,
    )


def _validate_main(
    text: str,
    issues: list[str],
    *,
    expected_project: str | None = None,
) -> None:
    structural_text = _without_noncontent_blocks(text)
    first_nonempty = next(
        (line.strip() for line in structural_text.splitlines() if line.strip()), ""
    )
    if expected_project is not None and first_nonempty != f"# {expected_project}：数学主稿":
        issues.append(f"数学主稿的一级标题必须绑定项目：{expected_project}")
    elif not re.search(r"^#\s+.+数学主稿\s*$", structural_text, re.M):
        issues.append("数学主稿缺少清晰的一级标题")


def _validate_scratch(text: str, issues: list[str]) -> None:
    """Research organization is reviewed as prose, not inferred from keywords."""
    if not text.strip():
        issues.append("计算草稿不能为空")

def _metadata_values(text: str, key: str) -> list[str]:
    text = _without_noncontent_blocks(text)
    return [
        match.strip()
        for match in re.findall(
            rf"^-\s*{re.escape(key)}\s*[：:]\s*(.+?)\s*$", text, re.M
        )
    ]


def _metadata_value(text: str, key: str) -> str | None:
    values = _metadata_values(text, key)
    return values[0] if values else None


def _validate_project_title(
    text: str, issues: list[str], *, project: str, role: str
) -> None:
    visible = _without_noncontent_blocks(text)
    first_nonempty = next(
        (line.strip() for line in visible.splitlines() if line.strip()), ""
    )
    if first_nonempty != f"# {project}：{role}":
        issues.append(f"{role}的一级标题必须绑定项目：{project}")


def _entry_locator_and_purpose(line: str) -> tuple[str, str]:
    if "→" not in line:
        return "", ""
    right = line.split("→", 1)[1].strip()
    in_code = False
    for index, character in enumerate(right):
        if character == "`":
            in_code = not in_code
        elif character in {"：", ":"} and not in_code:
            return right[:index].strip(), right[index + 1 :].strip()
    return right, ""


def _normalized_anchor(value: str) -> str:
    value = re.sub(r"[`*_#]+", "", value)
    return re.sub(r"\s+", "", value).casefold()


def _anchor_candidates(locator: str) -> list[str]:
    if not _locator_has_canonical_form(locator):
        return []
    candidates = re.findall(r"`([^`]+)`", locator)
    if candidates:
        return list(dict.fromkeys(item.strip() for item in candidates if item.strip()))
    return [locator.strip()]


def _anchor_resolves(candidate: str, target_text: str) -> bool:
    target_text = _without_noncontent_blocks(target_text)
    normalized = _normalized_anchor(candidate)
    if not normalized:
        return False
    headings = {
        _normalized_anchor(match.group(1))
        for match in re.finditer(r"^#{1,6}\s+(.+?)\s*$", target_text, re.M)
    }
    if normalized in headings:
        return True
    if re.fullmatch(r"[A-Za-z]+\d+[A-Za-z0-9.-]*", candidate.strip()):
        return bool(
            re.search(
                rf"(?m)^\|\s*{re.escape(candidate.strip())}\s*\|",
                target_text,
            )
        )
    if re.search(r"(?:§|定理|命题|引理|定义|公式|页|表|段)", candidate):
        structured_matches = 0
        for line in target_text.splitlines():
            structural_line = re.sub(
                r"^\s*(?:#{1,6}\s+|[-*+]\s+)?(?:\*\*|__)?",
                "",
                line,
            )
            normalized_line = _normalized_anchor(structural_line)
            remainder = normalized_line[len(normalized) :]
            has_label_boundary = (
                not remainder
                or (
                    remainder[0] in "：:（([。；;，,—-"
                    and not (
                        remainder[0] in ".—-"
                        and len(remainder) > 1
                        and remainder[1].isdigit()
                    )
                )
            )
            if normalized_line.startswith(normalized) and has_label_boundary:
                structured_matches += 1
        return structured_matches == 1
    return False


def _anchors_exist(locator: str, target_text: str) -> bool:
    candidates = _anchor_candidates(locator)
    if not candidates:
        return False
    return all(_anchor_resolves(candidate, target_text) for candidate in candidates)


def _validate_entry(
    text: str,
    issues: list[str],
    expected_files: dict[str, str] | None = None,
    expected_version: str | None = None,
    expected_project: str | None = None,
    expected_anchor_texts: dict[str, str] | None = None,
    entry_root: Path | None = None,
    *,
    warnings: list[str] | None = None,
) -> None:
    """Check explicit metadata and locators, leaving research prose to readers."""
    for key in ("项目", "项目版本", "当前文件", "最近更新"):
        if len(_metadata_values(text, key)) > 1:
            issues.append(f"下一次入口的“{key}”字段只能出现一次")
    project = _metadata_value(text, "项目")
    version = _metadata_value(text, "项目版本")
    if project and expected_project and project != expected_project:
        issues.append(f"下一次入口的项目应为“{expected_project}”，实际为“{project}”")
    if version and expected_version and version != f"v{expected_version}":
        issues.append(f"下一次入口版本应为 v{expected_version}，实际为 {version}")
    if not project:
        issues.append("下一次入口缺少项目字段")
    updated = _metadata_value(text, "最近更新")
    if not _is_calendar_date(updated):
        issues.append("下一次入口缺少合法 YYYY-MM-DD 日历日期")
    elif dt.date.fromisoformat(updated) > dt.date.fromisoformat(_today()):
        issues.append("下一次入口的最近更新日期不得晚于当前日期")
    if not version or not re.fullmatch(r"v\d+\.\d+\.\d+", version):
        issues.append("下一次入口缺少 vMAJOR.MINOR.PATCH 格式的项目版本")
    sections = _section_map(text)
    # Structured locators can be checked exactly. Free-form reading notes and
    # purposes remain ordinary research prose; no purpose vocabulary is imposed.
    reading_sections = ("必要读取",)
    item_pattern = re.compile(r"^\s*-\s*`([^`]+)`\s*→\s*(.+?)\s*$")
    by_filename = {}
    if expected_files and expected_anchor_texts:
        for section, role in (("必读主稿", "数学主稿"), ("必读计算草稿", "计算草稿"), ("参考材料", "参考资料台账")):
            by_filename[expected_files[role]] = expected_anchor_texts[section]
    for section_name in reading_sections:
        for line in sections.get(section_name, "").splitlines():
            match = item_pattern.fullmatch(line)
            if match is None:
                continue
            filename = match.group(1)
            locator, _ = _entry_locator_and_purpose(line)
            if not _locator_has_canonical_form(locator):
                continue
            target_text = by_filename.get(filename)
            if target_text is None and entry_root is not None and (not expected_files or filename not in expected_files.values()):
                relative = Path(filename)
                if relative.is_absolute() or ".." in relative.parts:
                    issues.append(f"下一次入口的读取路径须位于项目内：{filename}")
                    continue
                target = entry_root / relative
                if not _is_regular_file(target) or any(part.is_symlink() for part in target.parents if part != entry_root.parent):
                    if warnings is not None:
                        warnings.append(f"读取前需取得参考文件并核对定位：{filename}")
                    continue
                if target.suffix.casefold() in {".md", ".markdown", ".txt", ".rst"}:
                    try:
                        target_text = target.read_text(encoding="utf-8")
                    except (OSError, UnicodeError):
                        issues.append(f"无法读取 UTF-8 文本锚点：{filename}")
            if target_text is not None and not _anchors_exist(locator, target_text):
                issues.append(f"下一次入口的“{section_name}”没有可在目标文件中定位的锚点：{filename}")

def _validate_state_content(
    state: ProjectState, *,
    warnings: list[str] | None = None,
) -> list[str]:
    issues: list[str] = []
    texts = {
        role: _read_text(state.files[role], role, issues) for role in CORE_ROLES
    }
    for role, text in texts.items():
        if text is not None and not text.strip():
            issues.append(f"长期文件不能为空：{state.files[role].name}")
        if text is not None:
            _validate_project_title(text, issues, project=state.project, role=role)
        if text is not None and role != "研究日志":
            version_values = _metadata_values(text, "项目版本")
            current_file_values = _metadata_values(text, "当前文件")
            version = _metadata_value(text, "项目版本")
            current_file = _metadata_value(text, "当前文件")
            if len(version_values) != 1:
                issues.append(
                    f"{state.files[role].name} 的内部项目版本必须且只能出现一次"
                )
            if version != f"v{state.version}":
                issues.append(
                    f"{state.files[role].name} 的内部项目版本应为 v{state.version}"
                )
            if role == "数学主稿" and current_file_values:
                issues.append("数学主稿不得包含“当前文件”身份行")
            elif role != "数学主稿" and len(current_file_values) != 1:
                issues.append(
                    f"{state.files[role].name} 的内部当前文件必须且只能出现一次"
                )
            elif role != "数学主稿" and current_file != f"`{state.files[role].name}`":
                issues.append(
                    f"{state.files[role].name} 的内部当前文件名与实际文件名不一致"
                )
    log_text = texts["研究日志"]
    if log_text is not None and (
        _metadata_value(log_text, "项目版本")
        or _metadata_value(log_text, "当前文件")
    ):
        issues.append("研究日志不得保存随升版变化的内部版本或当前文件字段")
    if texts["数学主稿"] is not None:
        _validate_main(
            texts["数学主稿"] or "",
            issues,
            expected_project=state.project,
        )
    if texts["计算草稿"] is not None:
        _validate_scratch(texts["计算草稿"] or "", issues)
    if texts["下一次入口"] is not None:
        entry_parent = state.files["下一次入口"].parent
        entry_root = (
            entry_parent.parent.parent
            if entry_parent.name == ACTIVE_REVISION_DIR
            and entry_parent.parent.name == "tmp"
            else entry_parent
        )
        _validate_entry(
            texts["下一次入口"] or "",
            issues,
            expected_files={role: state.files[role].name for role in CORE_ROLES},
            expected_version=state.version,
            expected_project=state.project,
            expected_anchor_texts={
                "必读主稿": texts["数学主稿"] or "",
                "必读计算草稿": texts["计算草稿"] or "",
                "参考材料": texts["参考资料台账"] or "",
            },
            entry_root=entry_root,
            warnings=warnings,
        )
    return issues


def validate_project(
    project_dir: Path, *, candidate: bool = False,
    warnings: list[str] | None = None,
) -> list[str]:
    """Check published files by default, or the candidate's local publish conditions."""
    if project_dir.is_symlink():
        return [f"项目目录不得是符号链接：{project_dir}"]
    if not project_dir.is_dir():
        return [f"项目目录不存在：{project_dir}"]
    issues = _managed_directory_issues(project_dir)
    if candidate:
        if issues:
            return issues
        try:
            _validated_revision(project_dir, warnings=warnings)
        except WorkbenchError as exc:
            return [str(exc)]
        return []
    unversioned = _unversioned_research_files(project_dir)
    if unversioned:
        issues.append("项目顶层存在未版本化的研究角色文件：" + "、".join(unversioned))
    state, state_issues = _discover_state(project_dir)
    issues.extend(state_issues)
    if state is not None:
        issues.extend(
            _validate_state_content(state, warnings=warnings)
        )
    return issues


def _active_dir(project_dir: Path) -> Path:
    return project_dir / "tmp" / ACTIVE_REVISION_DIR


def _revision_record_path(project_dir: Path) -> Path:
    return _active_dir(project_dir) / REVISION_RECORD_FILE


def _write_revision_record(path: Path, payload: dict[str, object]) -> None:
    """Create the preparation record exclusively before any candidate copy."""
    try:
        with path.open("x", encoding="utf-8", newline="\n") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
    except OSError as exc:
        raise WorkbenchError(f"无法建立升版说明：{path}") from exc


def _replace_revision_record(path: Path, payload: dict[str, object]) -> None:
    """Atomically advance an existing internal preparation record."""
    temporary = path.with_name(path.name + ".next")
    if path.is_symlink() or not path.is_file():
        raise WorkbenchError(f"升版说明必须是普通文件：{path}")
    if temporary.is_symlink() or (
        temporary.exists() and not temporary.is_file()
    ):
        raise WorkbenchError(f"升版说明的临时路径不是普通文件：{temporary}")
    try:
        if temporary.exists():
            temporary.unlink()
        with temporary.open("x", encoding="utf-8", newline="\n") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        temporary.replace(path)
    except OSError as exc:
        raise WorkbenchError(f"无法更新升版说明：{path}") from exc


def _read_revision_record(project_dir: Path) -> dict[str, object]:
    _require_managed_directories(project_dir)
    path = _revision_record_path(project_dir)
    if path.is_symlink() or not path.is_file():
        raise WorkbenchError("没有可读取的进行中升版；请先运行 begin-revision")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise WorkbenchError("没有可读取的进行中升版；请先运行 begin-revision") from exc
    required = {
        "status",
        "completed_roles",
        "project",
        "base_version",
        "new_version",
        "base_files",
        "candidate_files",
        "round_type",
    }
    allowed = required | {"log_append_record"}
    if (
        not isinstance(payload, dict)
        or not required.issubset(payload)
        or not set(payload).issubset(allowed)
    ):
        raise WorkbenchError("进行中升版的说明不完整")
    if not isinstance(payload["base_files"], dict) or not isinstance(
        payload["candidate_files"], dict
    ):
        raise WorkbenchError("进行中升版的文件清单不合法")
    if payload["status"] not in {"PREPARING", "READY"}:
        raise WorkbenchError("进行中升版的状态不合法")
    completed = payload["completed_roles"]
    if (
        not isinstance(completed, list)
        or any(not isinstance(role, str) for role in completed)
        or len(set(completed)) != len(completed)
        or not set(completed).issubset(CORE_ROLES)
    ):
        raise WorkbenchError("进行中升版的已完成角色清单不合法")
    if payload["status"] == "READY" and set(completed) != set(CORE_ROLES):
        raise WorkbenchError("READY 升版的已完成角色清单必须包含全部五文件")
    if payload["round_type"] not in ROUND_TYPES:
        raise WorkbenchError("进行中升版的轮次类型不合法")
    log_append_record = payload.get("log_append_record")
    if log_append_record is not None:
        current_log_fields = {
                "date",
                "previous_date",
                "date_correction",
                "round_type",
                "review_outcome",
        }
        if not isinstance(log_append_record, dict):
            raise WorkbenchError("进行中升版的日志追加记录不合法")
        log_field_set = frozenset(log_append_record)
        if log_field_set != frozenset(current_log_fields):
            raise WorkbenchError("进行中升版的日志追加记录不合法")
        if (
            not _is_calendar_date(log_append_record.get("date"))
            or (
                log_append_record.get("previous_date") is not None
                and not _is_calendar_date(log_append_record.get("previous_date"))
            )
            or not isinstance(log_append_record.get("date_correction"), bool)
        ):
            raise WorkbenchError("进行中升版的日志追加记录不合法")
        if log_field_set == frozenset(current_log_fields) and (
            log_append_record.get("round_type") not in ROUND_TYPES
            or (
                log_append_record.get("review_outcome") is not None
                and log_append_record.get("review_outcome") not in REVIEW_OUTCOMES
            )
        ):
            raise WorkbenchError("进行中升版的日志追加记录不合法")
    project = payload["project"]
    base_version = payload["base_version"]
    new_version = payload["new_version"]
    if not isinstance(project, str) or not isinstance(base_version, str) or not isinstance(
        new_version, str
    ):
        raise WorkbenchError("进行中升版的项目名和版本必须是字符串")
    if _clean_project_name(project) != project:
        raise WorkbenchError("进行中升版的项目名不是规范形式")
    if _parse_version(new_version) <= _parse_version(base_version):
        raise WorkbenchError("进行中升版的新版本必须高于上一版本")
    _revision_file_names(payload, "base_files", project, base_version)
    _revision_file_names(payload, "candidate_files", project, new_version)
    return payload


def _revision_file_names(
    payload: dict[str, object], key: str, project: str, version: str
) -> dict[str, str]:
    raw = payload[key]
    if not isinstance(raw, dict) or set(raw) != set(CORE_ROLES):
        raise WorkbenchError(f"进行中升版的 {key} 清单不完整")
    expected = _filename_map(project, version)
    result: dict[str, str] = {}
    for role in CORE_ROLES:
        value = raw.get(role)
        if not isinstance(value, str) or Path(value).name != value:
            raise WorkbenchError(f"进行中升版的 {key} 文件名不合法：{role}")
        if value != expected[role]:
            raise WorkbenchError(f"进行中升版的 {key} 文件名不一致：{value}")
        result[role] = value
    return result


def _revision_round_type(payload: dict[str, object]) -> str:
    return _normalize_round_type(str(payload["round_type"]))


def _locate_revision_files(
    names: dict[str, str], directories: Sequence[Path], label: str
) -> dict[str, Path]:
    result: dict[str, Path] = {}
    for role in CORE_ROLES:
        matches = [directory / names[role] for directory in directories]
        invalid = [
            path
            for path in matches
            if path.is_symlink() or (path.exists() and not path.is_file())
        ]
        if invalid:
            raise WorkbenchError(
                f"{label}的{role}路径不是普通文件："
                + "、".join(str(path) for path in invalid)
            )
        existing = [path for path in matches if _is_regular_file(path)]
        if not existing:
            raise WorkbenchError(f"{label}缺少{role}：{names[role]}")
        if len(existing) > 1 and not all(existing[0].samefile(item) for item in existing[1:]):
            raise WorkbenchError(
                f"{label}的{role}同时出现在多个位置："
                + "、".join(str(path) for path in existing)
            )
        result[role] = existing[0]
    return result


def _copy_candidate_role(
    source: Path,
    target: Path,
    role: str,
    new_version: str,
    candidate_files: dict[str, str],
    base_files: dict[str, str],
) -> None:
    """Build one candidate through a disposable partial file."""
    partial = target.with_name(target.name + ".partial")
    if target.is_symlink() or (target.exists() and not target.is_file()):
        raise WorkbenchError(f"候选目标不是普通文件：{target}")
    if target.exists():
        raise WorkbenchError(f"未登记完成的候选目标已经存在，已保留；请先核对：{target}")
    if partial.is_symlink() or (partial.exists() and not partial.is_file()):
        raise WorkbenchError(f"候选临时路径不是普通文件：{partial}")
    try:
        if partial.exists():
            partial.unlink()
        with source.open("rb") as input_handle, partial.open("xb") as output_handle:
            shutil.copyfileobj(input_handle, output_handle)
        if role != "研究日志":
            text = partial.read_text(encoding="utf-8")
            if role == "下一次入口":
                text = _set_entry_metadata(
                    text, new_version, candidate_files, base_files
                )
            else:
                text = _set_document_metadata(
                    text,
                    new_version,
                    candidate_files[role],
                    include_current_file=role != "数学主稿",
                )
            partial.write_text(text, encoding="utf-8", newline="\n")
        _move_without_overwrite(partial, target)
    except (OSError, UnicodeError, WorkbenchError) as exc:
        raise WorkbenchError(
            f"复制{role}时中断；PREPARING 候选已保留，处理同名冲突后可再次运行 begin-revision"
        ) from exc


def begin_revision(
    project_dir: Path, bump: str = "patch", round_type: str = "substantive"
) -> dict[str, object]:
    """Create or idempotently resume the next generation under PREPARING."""
    state = _require_state(project_dir)
    _ensure_project_dirs(project_dir)
    # A candidate is the place to repair content. Structural file checks above
    # protect copying; the content and appended log are checked before publish.
    round_type = _normalize_round_type(round_type)
    active = _active_dir(project_dir)
    new_version = _bump_version(state.version, bump)
    base_files = {role: state.files[role].name for role in CORE_ROLES}
    candidate_files = _filename_map(state.project, new_version)
    collisions = [
        project_dir / candidate_files[role]
        for role in CORE_ROLES
        if (project_dir / candidate_files[role]).exists()
    ]
    collisions.extend(
        project_dir / "old" / filename
        for filename in list(base_files.values()) + list(candidate_files.values())
        if (project_dir / "old" / filename).exists()
    )
    if collisions:
        raise WorkbenchError(
            "下一版本文件已存在，升版已停止："
            + "、".join(path.name for path in collisions)
        )

    expected: dict[str, object] = {
        "status": "PREPARING",
        "completed_roles": [],
        "project": state.project,
        "base_version": state.version,
        "new_version": new_version,
        "base_files": base_files,
        "candidate_files": candidate_files,
        "round_type": round_type,
    }
    record_path = active / REVISION_RECORD_FILE
    if active.exists():
        if not active.is_dir() or not record_path.is_file():
            raise WorkbenchError(
                f"升版目录缺少可读取的 PREPARING 说明：{active}"
            )
        payload = _read_revision_record(project_dir)
        for key in (
            "project",
            "base_version",
            "new_version",
            "base_files",
            "candidate_files",
        ):
            if payload[key] != expected[key]:
                raise WorkbenchError("已有升版说明与本次 base/new 文件清单不一致")
        if payload["round_type"] != round_type:
            raise WorkbenchError("已有升版说明与本次轮次类型不一致")
        if payload["status"] == "READY":
            _candidate_state(project_dir)
            return payload
    else:
        try:
            active.mkdir()
            _write_revision_record(record_path, expected)
        except (OSError, WorkbenchError) as exc:
            try:
                active.rmdir()
            except OSError:
                pass
            if isinstance(exc, WorkbenchError):
                raise
            raise WorkbenchError("无法排他建立 PREPARING 升版说明") from exc
        payload = expected

    completed = list(payload["completed_roles"])
    for role in list(completed):
        if not (active / candidate_files[role]).is_file():
            completed.remove(role)
    if completed != payload["completed_roles"]:
        payload["completed_roles"] = completed
        _replace_revision_record(record_path, payload)
    for role in CORE_ROLES:
        if role in completed:
            continue
        _copy_candidate_role(
            state.files[role],
            active / candidate_files[role],
            role,
            new_version,
            candidate_files,
            base_files,
        )
        completed.append(role)
        payload["completed_roles"] = completed
        _replace_revision_record(record_path, payload)

    candidate_state, candidate_issues = _discover_state(active)
    if candidate_state is None:
        raise WorkbenchError("下一版本候选结构不合法：" + "；".join(candidate_issues))
    payload["status"] = "READY"
    _replace_revision_record(record_path, payload)
    return payload


def _candidate_state(project_dir: Path) -> ProjectState:
    revision_record = _read_revision_record(project_dir)
    if revision_record["status"] != "READY":
        raise WorkbenchError(
            "候选仍处于 PREPARING；请再次运行 begin-revision 完成可恢复复制"
        )
    active = _active_dir(project_dir)
    state, issues = _discover_state(active)
    if state is None or issues:
        raise WorkbenchError("进行中的候选文件不完整：" + "；".join(issues))
    if (
        state.project != revision_record["project"]
        or state.version != revision_record["new_version"]
    ):
        raise WorkbenchError("候选文件名或版本与升版说明不一致")
    return state


def _valid_log_dates(text: str) -> list[dt.date]:
    dates: list[dt.date] = []
    for value, _ in LOG_HEADING_RE.findall(_without_noncontent_blocks(text)):
        try:
            dates.append(dt.date.fromisoformat(value))
        except ValueError:
            continue
    return dates


def _validate_appended_log(
    old_text: str,
    new_text: str,
    log_append_record: object | None = None,
) -> list[str]:
    issues: list[str] = []
    raw_suffix = new_text[len(old_text) :]
    if (
        CONTROL_MARKUP_RE.search(raw_suffix)
        or CONTROL_FENCE_RE.search(raw_suffix)
        or CONTROL_LINE_TAG_RE.search(raw_suffix)
    ):
        issues.append("候选研究日志的新增记录不得包含围栏代码、HTML 或疑似注释控制标记")
    suffix = _without_noncontent_blocks(raw_suffix)
    headings = list(re.finditer(r"^##\s+(.+?)\s*$", suffix, re.M))
    if len(headings) != 1:
        return issues + ["候选研究日志每次发布必须且只能追加一条日期记录"]
    if suffix[: headings[0].start()].strip():
        return issues + ["候选研究日志的新增内容必须全部属于唯一日期记录"]
    match = LOG_HEADING_RE.fullmatch(headings[0].group(0))
    if match is None:
        return issues + ["候选研究日志的新记录标题必须是 ## YYYY-MM-DD｜摘要"]
    try:
        new_date = dt.date.fromisoformat(match.group(1))
    except ValueError:
        return issues + ["候选研究日志的新记录日期不是合法日历日期"]
    current_date = dt.date.fromisoformat(_today())
    if new_date > current_date:
        issues.append("候选研究日志的新记录日期晚于当前日期")
    old_dates = _valid_log_dates(old_text)
    if old_dates and new_date < old_dates[-1]:
        correction = (
            isinstance(log_append_record, dict)
            and log_append_record.get("date") == new_date.isoformat()
            and log_append_record.get("previous_date")
            == old_dates[-1].isoformat()
            and log_append_record.get("date_correction") is True
            and "日期勘误" in match.group(2)
        )
        if not correction:
            issues.append("候选研究日志的新记录日期早于上一条有效记录")
    body = suffix[headings[0].end() :]
    if not re.search(r"(?m)^-\s*本次目标与结果：[ \t]*\S", body):
        issues.append("候选研究日志的新记录缺少非空的目标与结果")
    if not re.search(
        r"(?m)^-\s*(?:阅读|主稿变化|理由|未决)："
        r"(?:[ \t]*\S.*|[ \t]*\n[ \t]+-\s+\S)",
        body,
    ):
        issues.append("候选研究日志的新记录至少需要一项阅读、主稿变化、理由或未决事项")
    if isinstance(log_append_record, dict) and "round_type" in log_append_record:
        round_type = log_append_record.get("round_type")
        expected_round_label = ROUND_TYPES.get(str(round_type))
        labels = [expected_round_label]
        if expected_round_label is None or sum(
            body.count(f"- 轮次类型：{label}") for label in labels
        ) != 1:
            issues.append("候选研究日志的轮次类型与升版说明不一致")
        if round_type == "review":
            outcome = log_append_record.get("review_outcome")
            expected_outcome = REVIEW_OUTCOMES.get(str(outcome))
            if expected_outcome is None or body.count(
                f"- 回顾结论：{expected_outcome}"
            ) != 1:
                issues.append("研究回顾日志缺少合法回顾结论")
        elif log_append_record.get("review_outcome") is not None:
            issues.append("非回顾轮不得填写回顾结论")
    return issues


def append_log(
    project_dir: Path,
    summary: str,
    readings: Sequence[str],
    changed: Sequence[str],
    reasons: Sequence[str],
    unresolved: Sequence[str],
    review_outcome: str | None = None,
) -> None:
    """Append a record to the active candidate, never to the current log."""
    state = _candidate_state(project_dir)
    log_path = state.files["研究日志"]
    summary = _clean_inline(summary, "本次摘要")
    revision_record = _read_revision_record(project_dir)
    round_type = _revision_round_type(revision_record)
    if round_type == "review":
        if review_outcome not in REVIEW_OUTCOMES:
            raise WorkbenchError("研究回顾日志必须填写合法的 review outcome")
    elif review_outcome is not None:
        raise WorkbenchError("只有研究回顾轮可以填写回顾结论")
    fields: list[tuple[str, Sequence[str]]] = [
        ("阅读", readings),
        ("主稿变化", changed),
        ("理由", reasons),
        ("未决", unresolved),
    ]
    if not any(values for _, values in fields):
        raise WorkbenchError("研究日志除摘要外至少需要一项阅读、主稿变化、理由或未决事项")
    try:
        existing_log = log_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise WorkbenchError(f"无法读取研究日志候选：{log_path}") from exc
    project = revision_record["project"]
    base_version = revision_record["base_version"]
    assert isinstance(project, str)
    assert isinstance(base_version, str)
    base_names = _revision_file_names(
        revision_record, "base_files", project, base_version
    )
    base_log_path = _locate_revision_files(
        base_names, (project_dir, project_dir / "old"), "上一版本"
    )["研究日志"]
    try:
        base_log = base_log_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise WorkbenchError(f"无法读取上一版本研究日志：{base_log_path}") from exc
    if not existing_log.startswith(base_log):
        raise WorkbenchError("候选研究日志已改写上一版本内容")
    if existing_log[len(base_log) :].strip():
        raise WorkbenchError("候选研究日志已经追加本次发布记录，不得再次追加")

    current_date = dt.date.fromisoformat(_today())
    existing_dates = _valid_log_dates(existing_log)
    if existing_dates and current_date < existing_dates[-1]:
        correction = (
            existing_dates[-1] > current_date and "日期勘误" in summary
        )
        if not correction:
            raise WorkbenchError(
                "当前日期早于研究日志上一条有效记录；若旧记录误写为未来日期，"
                "请在摘要中写明“日期勘误”"
            )
    lines = [
        "",
        f"## {current_date.isoformat()}｜{summary}",
        "",
        f"- 本次目标与结果：{summary}",
        f"- 轮次类型：{ROUND_TYPES[round_type]}",
    ]
    if round_type == "review":
        assert review_outcome is not None
        lines.append(f"- 回顾结论：{REVIEW_OUTCOMES[review_outcome]}")
    for label, values in fields:
        cleaned = [_clean_inline(value, label) for value in values]
        if cleaned:
            lines.append(f"- {label}：")
            lines.extend(f"  - {value}" for value in cleaned)
    entry = "\n".join(lines).rstrip() + "\n"
    try:
        with log_path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(entry)
        revision_record["log_append_record"] = {
            "date": current_date.isoformat(),
            "previous_date": (
                existing_dates[-1].isoformat() if existing_dates else None
            ),
            "date_correction": bool(
                existing_dates and current_date < existing_dates[-1]
            ),
            "round_type": round_type,
            "review_outcome": review_outcome,
        }
        _replace_revision_record(
            _revision_record_path(project_dir), revision_record
        )
    except (OSError, WorkbenchError) as exc:
        try:
            log_path.write_text(existing_log, encoding="utf-8", newline="\n")
        except OSError as rollback_exc:
            raise WorkbenchError(
                f"无法保存日志追加记录，且候选文件回退失败：{log_path}"
            ) from rollback_exc
        raise WorkbenchError(f"无法追加研究日志候选：{log_path}") from exc


def _validated_revision(
    project_dir: Path, *,
    warnings: list[str] | None = None,
) -> tuple[dict[str, object], ProjectState, ProjectState]:
    """Read-only checks shared by --candidate and local finalization."""
    revision_record = _read_revision_record(project_dir)
    if revision_record["status"] != "READY":
        raise WorkbenchError(
            "候选仍处于 PREPARING；请再次运行 begin-revision 完成复制和检查"
        )
    project = revision_record["project"]
    base_version = revision_record["base_version"]
    new_version = revision_record["new_version"]
    if not isinstance(project, str) or not isinstance(base_version, str) or not isinstance(
        new_version, str
    ):
        raise WorkbenchError("进行中升版的项目或版本字段不合法")
    _parse_version(base_version)
    _parse_version(new_version)
    base_names = _revision_file_names(
        revision_record, "base_files", project, base_version
    )
    candidate_names = _revision_file_names(
        revision_record, "candidate_files", project, new_version
    )
    _require_managed_directories(project_dir)
    old_dir = project_dir / "old"
    active = _active_dir(project_dir)
    allowed_active_names = {
        REVISION_RECORD_FILE,
        *candidate_names.values(),
    }
    try:
        extra_active_names = sorted(
            path.name for path in active.iterdir() if path.name not in allowed_active_names
        )
    except OSError as exc:
        raise WorkbenchError(f"无法读取进行中的候选目录：{active}") from exc
    if extra_active_names:
        raise WorkbenchError(
            "候选目录含有工作台不管理的额外文件，发布已停止："
            + "、".join(extra_active_names)
        )
    base_paths = _locate_revision_files(
        base_names, (project_dir, old_dir), "上一版本"
    )
    candidate_paths = _locate_revision_files(
        candidate_names, (active, project_dir), "候选版本"
    )
    current = ProjectState(project, base_version, base_paths)
    candidate = ProjectState(project, new_version, candidate_paths)
    try:
        old_log = current.files["研究日志"].read_text(encoding="utf-8")
        new_log = candidate.files["研究日志"].read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise WorkbenchError("无法检查研究日志的追加关系") from exc
    if not new_log.startswith(old_log):
        raise WorkbenchError("候选研究日志改写了旧内容；研究日志只能在原文末尾追加")
    if len(new_log) == len(old_log):
        raise WorkbenchError("候选研究日志尚未追加本次发布记录")
    issues = _validate_state_content(candidate, warnings=warnings)
    if issues:
        raise WorkbenchError("候选版本未通过发布检查：" + "；".join(issues))
    log_issues = _validate_appended_log(
        old_log,
        new_log,
        revision_record.get("log_append_record"),
    )
    if log_issues:
        raise WorkbenchError("候选研究日志未通过发布检查：" + "；".join(log_issues))
    return revision_record, current, candidate


def _same_regular_file(source: Path, target: Path) -> bool:
    """Recognize a real hard-link pair without following symbolic links."""
    try:
        left, right = source.lstat(), target.lstat()
    except FileNotFoundError:
        return False
    return (
        stat.S_ISREG(left.st_mode)
        and stat.S_ISREG(right.st_mode)
        and (left.st_dev, left.st_ino) == (right.st_dev, right.st_ino)
    )


def _move_without_overwrite(source: Path, target: Path) -> None:
    """Publish a regular file without a check-then-overwrite race."""
    if _same_regular_file(source, target):
        source.unlink()  # Resume a POSIX link/unlink interrupted after linking.
        return
    if os.name == "nt":
        # Windows rename fails atomically if the destination already exists.
        source.rename(target)
    else:
        os.link(source, target)
        source.unlink()


def finalize_revision(project_dir: Path) -> dict[str, object]:
    """Finalize and archive locally; this does not save or move Library files."""
    warnings: list[str] = []
    revision_record, current, candidate = _validated_revision(project_dir, warnings=warnings)
    project = current.project
    base_version = current.version
    new_version = candidate.version
    base_names = {role: current.files[role].name for role in CORE_ROLES}
    candidate_names = {role: candidate.files[role].name for role in CORE_ROLES}
    round_type = _revision_round_type(revision_record)
    old_dir = project_dir / "old"
    active = _active_dir(project_dir)
    root_targets = [project_dir / candidate_names[role] for role in CORE_ROLES]
    archive_targets = [old_dir / base_names[role] for role in CORE_ROLES]

    archived: list[tuple[Path, Path]] = []
    published: list[tuple[Path, Path]] = []
    try:
        for role in CORE_ROLES:
            source = candidate.files[role]
            target = project_dir / candidate_names[role]
            if source == target:
                continue
            _move_without_overwrite(source, target)
            published.append((source, target))
        for role in CORE_ROLES:
            source = current.files[role]
            target = old_dir / base_names[role]
            if source == target:
                continue
            _move_without_overwrite(source, target)
            archived.append((source, target))
    except OSError as exc:
        rollback_errors: list[str] = []
        for source, target in reversed(archived):
            try:
                _move_without_overwrite(target, source)
            except OSError:
                rollback_errors.append(target.name)
        for source, target in reversed(published):
            try:
                _move_without_overwrite(target, source)
            except OSError:
                rollback_errors.append(target.name)
        detail = ""
        if rollback_errors:
            detail = "；以下文件需要人工恢复：" + "、".join(rollback_errors)
        raise WorkbenchError("发布过程中断，已尝试恢复原状态" + detail) from exc

    record_path = _revision_record_path(project_dir)
    try:
        remaining = sorted(path.name for path in active.iterdir())
    except OSError as exc:
        raise WorkbenchError("新版本已发布，但无法核对 tmp 中的升版说明") from exc
    if remaining != [REVISION_RECORD_FILE]:
        raise WorkbenchError(
            "新版本已发布，但候选目录仍有额外内容；升版说明已保留，可核对后重试"
        )
    record_removed = False
    try:
        record_path.unlink()
        record_removed = True
        active.rmdir()
    except OSError as exc:
        restore_error = ""
        if record_removed and active.is_dir() and not record_path.exists():
            try:
                _write_revision_record(record_path, revision_record)
            except WorkbenchError:
                restore_error = "；升版说明未能自动恢复，需要人工核对"
        raise WorkbenchError(
            "新版本已发布，但 tmp 中的升版说明未能清理；可再次运行 finalize-revision"
            + restore_error
        ) from exc
    return {
        "storage_scope": "local-filesystem",
        "project": project,
        "old_version": base_version,
        "current_version": new_version,
        "round_type": round_type,
        "current_files": [path.name for path in root_targets],
        "archived_files": [path.name for path in archive_targets],
        "warnings": warnings,
    }


def inspect_project(project_dir: Path) -> dict[str, object]:
    _require_managed_directories(project_dir)
    active: dict[str, object] | None = None
    if _revision_record_path(project_dir).is_file():
        revision_record = _read_revision_record(project_dir)
        project = revision_record["project"]
        base_version = revision_record["base_version"]
        new_version = revision_record["new_version"]
        assert isinstance(project, str)
        assert isinstance(base_version, str)
        assert isinstance(new_version, str)
        base_names = _revision_file_names(
            revision_record, "base_files", project, base_version
        )
        candidate_names = _revision_file_names(
            revision_record, "candidate_files", project, new_version
        )
        base_paths = _locate_revision_files(
            base_names, (project_dir, project_dir / "old"), "上一版本"
        )
        candidate_paths = _locate_revision_files(
            candidate_names, (_active_dir(project_dir), project_dir), "候选版本"
        )
        publish_complete = (
            all(path.parent == project_dir / "old" for path in base_paths.values())
            and all(path.parent == project_dir for path in candidate_paths.values())
        )
        state = (
            ProjectState(project, new_version, candidate_paths)
            if publish_complete
            else ProjectState(project, base_version, base_paths)
        )
        active = {
            "status": revision_record["status"],
            "base_version": base_version,
            "new_version": new_version,
            "round_type": revision_record.get("round_type"),
            "candidate_files": candidate_names,
            "base_locations": {
                role: path.relative_to(project_dir).as_posix()
                for role, path in base_paths.items()
            },
            "candidate_locations": {
                role: path.relative_to(project_dir).as_posix()
                for role, path in candidate_paths.items()
            },
            "publish_complete": publish_complete,
            "transition_state": (
                "published-cleanup-pending" if publish_complete else "in-progress"
            ),
        }
    else:
        state = _require_state(project_dir)
    return {
        "storage_scope": "local-filesystem",
        "project": state.project,
        "current_version": state.version,
        "current_files": {role: state.files[role].name for role in CORE_ROLES},
        "current_locations": {
            role: path.relative_to(project_dir).as_posix()
            for role, path in state.files.items()
        },
        "project_directories": list(PROJECT_DIRS),
        "active_revision": active,
    }


def _working_state(project_dir: Path) -> ProjectState:
    if _revision_record_path(project_dir).is_file():
        return _candidate_state(project_dir)
    return _require_state(project_dir)


def _session_summary(project_dir: Path) -> dict[str, object]:
    _require_managed_directories(project_dir)
    state = _working_state(project_dir)
    entry_path = state.files["下一次入口"]
    try:
        text = entry_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise WorkbenchError(f"无法读取下一次入口：{entry_path.name}") from exc
    if not text.strip():
        raise WorkbenchError("下一次入口为空；请从当前主稿和最近日志恢复入口")
    return {
        "storage_scope": "local-filesystem",
        "project": state.project,
        "version": state.version,
        "current_files": {role: state.files[role].name for role in CORE_ROLES},
        "entry_text": text,
    }

def prepare_session(project_dir: Path, output_format: str) -> str:
    """Read the entry once, preserving its context without loading manuscripts."""
    payload = _session_summary(project_dir)
    if output_format == "json":
        return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    return str(payload["entry_text"])


def _add_common_path(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "project_dir", type=Path, help="研究项目目录；目录整体移动后传入新位置即可"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", action="version", version=VERSION)
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser(
        "init-project", help="建立带 v1.0.0 的五文件研究工作台"
    )
    _add_common_path(init_parser)
    init_parser.add_argument("--name", required=True, help="项目名称，也是版本化文件名前缀")
    init_parser.add_argument("--goal", required=True, help="项目当前研究目标")
    init_parser.add_argument(
        "--reference", action="append", default=[], help="参考稿或参考材料；可重复"
    )

    inspect_parser = subparsers.add_parser(
        "inspect-project", help="识别当前版本、精确文件名和进行中升版"
    )
    _add_common_path(inspect_parser)

    validate_parser = subparsers.add_parser(
        "validate-project", help="检查版本化五文件和项目目录"
    )
    _add_common_path(validate_parser)
    validate_parser.add_argument("--json", action="store_true", help="输出 JSON")
    validate_parser.add_argument(
        "--candidate", action="store_true",
        help="检查进行中候选的完整本地发布条件；默认检查已发布根目录版本",
    )

    begin_parser = subparsers.add_parser(
        "begin-revision", help="在 tmp 中复制并建立下一版本候选"
    )
    _add_common_path(begin_parser)
    begin_parser.add_argument(
        "--bump",
        choices=("patch", "minor", "major"),
        required=True,
        help="按数学变化显式选择 patch、minor 或 major",
    )
    begin_parser.add_argument(
        "--round-type",
        choices=tuple(ROUND_TYPES),
        required=True,
        help="显式选择 substantive、review 或 maintenance",
    )

    append_parser = subparsers.add_parser(
        "append-log", help="只在进行中的研究日志候选末尾追加记录"
    )
    _add_common_path(append_parser)
    append_parser.add_argument("--summary", required=True, help="本次目标与结果的短摘要")
    append_parser.add_argument(
        "--read", action="append", default=[], help="实际阅读的章节或资料；可重复"
    )
    append_parser.add_argument(
        "--changed", action="append", default=[], help="数学主稿变化；可重复"
    )
    append_parser.add_argument(
        "--reason", action="append", default=[], help="关键推导、反例或取舍理由；可重复"
    )
    append_parser.add_argument(
        "--unresolved", action="append", default=[], help="未决问题或下一步；可重复"
    )
    append_parser.add_argument(
        "--review-outcome",
        choices=tuple(REVIEW_OUTCOMES),
        help="仅研究回顾轮填写：continue、rewrite、return 或 stop",
    )
    session_parser = subparsers.add_parser(
        "prepare-session", help="读取当前入口原文以恢复会话"
    )
    _add_common_path(session_parser)
    session_parser.add_argument(
        "--format", choices=("markdown", "json"), default="markdown"
    )

    finalize_parser = subparsers.add_parser(
        "finalize-revision", help="仅在本地发布候选并把上一版移入 old；不表示 Library 已保存或归档"
    )
    _add_common_path(finalize_parser)
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(list(argv) if argv is not None else None)
    try:
        if args.command == "init-project":
            init_project(args.project_dir, args.name, args.goal, args.reference)
            print(f"已建立本地研究工作台：{args.project_dir}（尚不表示已保存到 Library）")
            return 0
        if args.command == "inspect-project":
            print(json.dumps(inspect_project(args.project_dir), ensure_ascii=False, indent=2))
            return 0
        if args.command == "validate-project":
            warnings: list[str] = []
            issues = validate_project(args.project_dir, candidate=args.candidate, warnings=warnings)
            if args.json:
                print(
                    json.dumps(
                        {
                            "valid": not issues, "issues": issues, "warnings": warnings,
                            "target": "candidate" if args.candidate else "published",
                            "storage_scope": "local-filesystem",
                        },
                        ensure_ascii=False,
                        indent=2,
                    )
                )
            elif issues:
                print("项目检查未通过：", file=sys.stderr)
                for issue in issues:
                    print(f"- {issue}", file=sys.stderr)
            else:
                print("本地候选检查通过。" if args.candidate else "本地已发布项目检查通过。")
            if not args.json:
                for warning in warnings:
                    print(f"提醒：{warning}", file=sys.stderr)
            return 0 if not issues else 1
        if args.command == "begin-revision":
            payload = begin_revision(args.project_dir, args.bump, args.round_type)
            print(
                json.dumps(
                    dict(payload, storage_scope="local-filesystem", warnings=[]),
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return 0
        if args.command == "append-log":
            append_log(
                args.project_dir,
                args.summary,
                args.read,
                args.changed,
                args.reason,
                args.unresolved,
                args.review_outcome,
            )
            print("研究日志候选已追加。")
            return 0
        if args.command == "prepare-session":
            sys.stdout.write(prepare_session(args.project_dir, args.format))
            return 0
        if args.command == "finalize-revision":
            print(
                json.dumps(
                    finalize_revision(args.project_dir), ensure_ascii=False, indent=2
                )
            )
            return 0
    except WorkbenchError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
