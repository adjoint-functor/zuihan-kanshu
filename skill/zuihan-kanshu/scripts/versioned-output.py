#!/usr/bin/env python3
"""Manage versioned ordinary drafts and paired reader artifacts without overwriting."""

from __future__ import annotations

import argparse
import ctypes
import errno
import json
import os
import re
import shutil
import stat
import sys
from pathlib import Path
from typing import Sequence


VERSION = "8.6.0"
PLAN_NAME = "version-revision-plan.json"
PLAN_STAGING_NAME = "version-revision-plan.next.json"
PLAN_SCHEMA = "versioned-output-plan/2.0"
PLAN_PHASES = {"PREPARING", "EDITING", "FINALIZING"}
VERSION_RE = re.compile(
    r"^(?P<prefix>.+)_v(?P<major>0|[1-9]\d*)\."
    r"(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)"
    r"(?P<extension>(?:\.[^./]+)+)$"
)


class VersionedOutputError(RuntimeError):
    """Raised when a requested version transition is unsafe or ambiguous."""


def _present(path: Path) -> bool:
    return path.exists() or path.is_symlink()


def _same_file(first: Path, second: Path) -> bool:
    try:
        first_stat, second_stat = first.lstat(), second.lstat()
    except FileNotFoundError:
        return False
    return (
        stat.S_ISREG(first_stat.st_mode)
        and stat.S_ISREG(second_stat.st_mode)
        and os.path.samestat(first_stat, second_stat)
    )


def _rename_directory_without_overwrite(source: Path, target: Path) -> None:
    """Use an atomic no-replace rename; never fall back to POSIX rename()."""
    if os.name == "nt":
        source.rename(target)
        return
    try:
        libc = ctypes.CDLL(None, use_errno=True)
        if sys.platform == "linux":
            rename = libc.renameat2
            rename.argtypes = [
                ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p,
                ctypes.c_uint,
            ]
            # AT_FDCWD and RENAME_NOREPLACE; absolute paths ignore the dirfds.
            arguments = (-100, os.fsencode(source), -100, os.fsencode(target), 1)
        elif sys.platform == "darwin":
            rename = libc.renamex_np
            rename.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint]
            arguments = (os.fsencode(source), os.fsencode(target), 0x00000004)  # RENAME_EXCL
        else:
            raise AttributeError("no atomic no-replace directory rename")
    except (AttributeError, OSError) as error:
        raise OSError(errno.ENOTSUP, "系统不支持不覆盖目标的目录移动", str(target)) from error
    rename.restype = ctypes.c_int
    if rename(*arguments) != 0:
        error_number = ctypes.get_errno()
        raise OSError(error_number, os.strerror(error_number), str(target))


def _move_without_overwrite(source: Path, target: Path) -> None:
    """Move within the output directory without replacing an occupied path."""
    if source.is_dir():
        _rename_directory_without_overwrite(source, target)
        return
    if _same_file(source, target):
        source.unlink()
        return
    if os.name == "nt":
        source.rename(target)  # Windows rename rejects every existing target.
        return
    target.hardlink_to(source)
    try:
        source.unlink()
    except OSError:
        try:
            target.unlink()
        except OSError:
            pass  # Both links remain recognizable when finalization resumes.
        raise


def _write_plan(path: Path, plan: dict[str, object], *, exclusive: bool) -> None:
    text = json.dumps(plan, ensure_ascii=False, indent=2) + "\n"
    try:
        if exclusive:
            with path.open("x", encoding="utf-8", newline="\n") as handle:
                handle.write(text)
            return
        staging = path.with_name(PLAN_STAGING_NAME)
        staging.unlink(missing_ok=True)
        with staging.open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
        staging.replace(path)
    except OSError as error:
        raise VersionedOutputError(f"无法写入版本候选计划：{error}") from error


def _copy_candidate(source: Path, candidate: Path) -> None:
    """Copy one candidate through a temporary path so interruption is resumable."""
    partial = candidate.with_name(candidate.name + ".part")
    try:
        partial.unlink(missing_ok=True)
        shutil.copy2(source, partial)
        _move_without_overwrite(partial, candidate)
    except OSError as error:
        raise VersionedOutputError(
            f"候选复制中断；保留计划，重新运行同一 begin-revision 可续作：{candidate.name}"
        ) from error


def normalize_version(value: str) -> str:
    candidate = value.strip()
    if not candidate.startswith("v"):
        candidate = "v" + candidate
    if not re.fullmatch(r"v(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)", candidate):
        raise VersionedOutputError(f"版本必须采用 vMAJOR.MINOR.PATCH：{value}")
    return candidate


def version_tuple(value: str) -> tuple[int, int, int]:
    normalized = normalize_version(value)
    return tuple(int(part) for part in normalized[1:].split("."))  # type: ignore[return-value]


def parse_versioned_name(name: str) -> tuple[str, str, str]:
    match = VERSION_RE.fullmatch(name)
    if match is None:
        raise VersionedOutputError(f"当前文件缺少 _vMAJOR.MINOR.PATCH 版本：{name}")
    version = f"v{match.group('major')}.{match.group('minor')}.{match.group('patch')}"
    return match.group("prefix"), version, match.group("extension")


def ensure_output_dir(output_dir: Path, dry_run: bool = False) -> dict[str, object]:
    output_dir = output_dir.resolve()
    if output_dir.exists() and not output_dir.is_dir():
        raise VersionedOutputError(f"输出位置不是目录：{output_dir}")
    created: list[str] = []
    for path in (output_dir, output_dir / "old", output_dir / "tmp"):
        if not path.exists():
            created.append(path.name if path != output_dir else str(path))
            if not dry_run:
                path.mkdir(parents=True, exist_ok=False)
        elif not path.is_dir():
            raise VersionedOutputError(f"预期目录实际不是目录：{path}")
    return {"output_dir": str(output_dir), "created": created, "dry_run": dry_run}


def _root_file(output_dir: Path, supplied: str, *, allow_directory: bool = False) -> Path:
    path = Path(supplied)
    if not path.is_absolute():
        path = output_dir / path
    if path.is_symlink():
        raise VersionedOutputError(f"当前文件路径不是普通文件：{supplied}")
    resolved = path.resolve()
    if resolved.parent != output_dir:
        raise VersionedOutputError(f"当前文件必须直接位于输出目录：{supplied}")
    if not resolved.is_file() and not (allow_directory and resolved.is_dir()):
        raise VersionedOutputError(f"当前文件不存在：{resolved}")
    return resolved


def begin_revision(
    output_dir: Path,
    current_files: Sequence[str],
    next_version: str,
    dry_run: bool = False,
    *,
    regenerate_files: Sequence[str] = (),
    add_files: Sequence[str] = (),
) -> dict[str, object]:
    output_dir = output_dir.resolve()
    if not current_files and not regenerate_files:
        raise VersionedOutputError("至少需要一个 --current 或 --regenerate 文件")
    ensure_output_dir(output_dir, dry_run=dry_run)
    normalized_next = normalize_version(next_version)
    plan_path = output_dir / "tmp" / PLAN_NAME
    existing_plan: dict[str, object] | None = None
    if plan_path.exists():
        _existing_path, existing_plan = _load_plan(output_dir)

    rows: list[dict[str, str]] = []
    seen_sources: set[str] = set()
    seen_targets: set[str] = set()
    current_versions: set[str] = set()
    existing_files = [("copy", supplied) for supplied in current_files]
    existing_files.extend(("regenerate", supplied) for supplied in regenerate_files)
    for mode, supplied in existing_files:
        source = _root_file(output_dir, supplied, allow_directory=mode == "regenerate")
        if source.name in seen_sources:
            raise VersionedOutputError(f"当前文件重复：{source.name}")
        seen_sources.add(source.name)
        prefix, current_version, extension = parse_versioned_name(source.name)
        current_versions.add(current_version)
        candidate_name = f"{prefix}_{normalized_next}{extension}"
        candidate = output_dir / "tmp" / candidate_name
        target = output_dir / candidate_name
        archived = output_dir / "old" / source.name
        for path, label in ((target, "新版本"), (archived, "old 归档")):
            if _present(path):
                raise VersionedOutputError(f"{label}路径已经存在，禁止覆盖：{path}")
        if existing_plan is None and _present(candidate):
            raise VersionedOutputError(f"候选路径已经存在，禁止覆盖：{candidate}")
        seen_targets.add(candidate_name)
        rows.append(
            {
                "mode": mode,
                "source": source.name,
                "candidate": f"tmp/{candidate_name}",
                "target": candidate_name,
                "archived": f"old/{source.name}",
            }
        )

    for name in add_files:
        if Path(name).name != name or Path(name).is_absolute():
            raise VersionedOutputError(f"新增文件必须是新版文件名 basename：{name}")
        _prefix, added_version, _extension = parse_versioned_name(name)
        if added_version != normalized_next:
            raise VersionedOutputError(f"新增文件版本必须等于 --next-version：{name}")
        if name in seen_targets:
            raise VersionedOutputError(f"新版本文件重复：{name}")
        seen_targets.add(name)
        target = output_dir / name
        candidate = output_dir / "tmp" / name
        if _present(target):
            raise VersionedOutputError(f"新版本路径已经存在，禁止覆盖：{target}")
        if existing_plan is None and _present(candidate):
            raise VersionedOutputError(f"候选路径已经存在，禁止覆盖：{candidate}")
        rows.append({"mode": "add", "candidate": f"tmp/{name}", "target": name})

    if len(current_versions) != 1:
        raise VersionedOutputError("同一次修订的当前文件必须使用同一版本")
    current_version = next(iter(current_versions))
    if version_tuple(normalized_next) <= version_tuple(current_version):
        raise VersionedOutputError(
            f"新版本必须高于当前版本：{current_version} -> {normalized_next}"
        )

    plan: dict[str, object] = {
        "schema": PLAN_SCHEMA,
        "phase": "PREPARING",
        "current_version": current_version,
        "next_version": normalized_next,
        "files": rows,
    }
    if existing_plan is not None:
        expected = {**plan, "phase": existing_plan["phase"]}
        if existing_plan != expected:
            raise VersionedOutputError(
                "已有候选计划与本次 begin-revision 不一致；请按原命令续作"
            )
        if existing_plan["phase"] != "PREPARING":
            raise VersionedOutputError(f"已有未完成的版本候选：{plan_path}")
    if not dry_run:
        if existing_plan is None:
            _write_plan(plan_path, plan, exclusive=True)
        for row in rows:
            candidate = output_dir / row["candidate"]
            allow_directory = row["mode"] != "copy"
            if candidate.is_symlink() or (
                candidate.exists()
                and not candidate.is_file()
                and not (allow_directory and candidate.is_dir())
            ):
                raise VersionedOutputError(f"候选路径不是允许的普通文件或目录：{candidate}")
            if row["mode"] == "copy" and not candidate.exists():
                _copy_candidate(output_dir / row["source"], candidate)
        plan["phase"] = "EDITING"
        _write_plan(plan_path, plan, exclusive=False)
    return {**plan, "dry_run": dry_run, "plan": f"tmp/{PLAN_NAME}"}


def _load_plan(output_dir: Path) -> tuple[Path, dict[str, object]]:
    plan_path = output_dir / "tmp" / PLAN_NAME
    if plan_path.exists() and not plan_path.is_file():
        raise VersionedOutputError(f"版本候选计划路径不是普通文件：{plan_path}")
    if not plan_path.is_file():
        raise VersionedOutputError(f"没有待发布的版本候选：{plan_path}")
    try:
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise VersionedOutputError(f"无法读取版本候选计划：{error}") from error
    if not isinstance(plan, dict):
        raise VersionedOutputError("版本候选计划必须是 JSON 对象")
    if set(plan) != {"schema", "phase", "current_version", "next_version", "files"}:
        raise VersionedOutputError("版本候选计划字段不完整或含未知字段")
    if (
        not isinstance(plan["schema"], str)
        or plan["schema"] != PLAN_SCHEMA
        or not isinstance(plan["phase"], str)
        or plan["phase"] not in PLAN_PHASES
        or not isinstance(plan["files"], list)
        or not plan["files"]
    ):
        raise VersionedOutputError("版本候选计划格式不受支持")
    if not isinstance(plan["current_version"], str) or not isinstance(
        plan["next_version"], str
    ):
        raise VersionedOutputError("版本候选计划的版本字段必须是字符串")
    try:
        current_version = normalize_version(plan["current_version"])
        next_version = normalize_version(plan["next_version"])
    except VersionedOutputError as error:
        raise VersionedOutputError(f"版本候选计划包含非法版本：{error}") from error
    if current_version != plan["current_version"] or next_version != plan["next_version"]:
        raise VersionedOutputError("版本候选计划必须使用规范的 vMAJOR.MINOR.PATCH 版本")
    if version_tuple(next_version) <= version_tuple(current_version):
        raise VersionedOutputError("版本候选计划的新版本必须高于当前版本")
    seen: dict[str, set[str]] = {
        "source": set(),
        "candidate": set(),
        "target": set(),
        "archived": set(),
    }
    has_existing = False
    for raw in plan["files"]:
        if (
            not isinstance(raw, dict)
            or any(not isinstance(value, str) or not value for value in raw.values())
        ):
            raise VersionedOutputError("版本候选计划中的文件条目不合法")
        mode = raw.get("mode")
        if mode not in {"copy", "regenerate", "add"}:
            raise VersionedOutputError("版本候选计划中的文件操作不受支持")
        expected_keys = {"mode", "candidate", "target"}
        if mode != "add":
            expected_keys.update({"source", "archived"})
        if set(raw) != expected_keys:
            raise VersionedOutputError("版本候选计划中的文件条目不合法")
        if mode == "add":
            target_name = raw["target"]
            if Path(target_name).name != target_name or Path(target_name).is_absolute():
                raise VersionedOutputError("版本候选计划的新增文件必须是根目录 basename")
            _prefix, added_version, _extension = parse_versioned_name(target_name)
            if added_version != next_version:
                raise VersionedOutputError("版本候选计划的新增文件版本不一致")
            expected = {"candidate": f"tmp/{target_name}", "target": target_name}
        else:
            has_existing = True
            source_name = raw["source"]
            if Path(source_name).name != source_name or Path(source_name).is_absolute():
                raise VersionedOutputError("版本候选计划的当前文件必须是根目录 basename")
            try:
                prefix, source_version, extension = parse_versioned_name(source_name)
            except VersionedOutputError as error:
                raise VersionedOutputError(f"版本候选计划的当前文件名不合法：{error}") from error
            if source_version != current_version:
                raise VersionedOutputError("版本候选计划的当前文件版本不一致")
            target_name = f"{prefix}_{next_version}{extension}"
            expected = {
                "source": source_name,
                "candidate": f"tmp/{target_name}",
                "target": target_name,
                "archived": f"old/{source_name}",
            }
        expected["mode"] = mode
        if raw != expected:
            raise VersionedOutputError("版本候选计划的文件映射与版本字段不一致")
        for key, value in raw.items():
            if key == "mode":
                continue
            if value in seen[key]:
                raise VersionedOutputError(f"版本候选计划的 {key} 路径重复：{value}")
            seen[key].add(value)
    if not has_existing:
        raise VersionedOutputError("版本候选计划至少需要一个当前文件")
    return plan_path, plan


def finalize_revision(output_dir: Path, dry_run: bool = False) -> dict[str, object]:
    output_dir = output_dir.resolve()
    ensure_output_dir(output_dir, dry_run=dry_run)
    plan_path, plan = _load_plan(output_dir)
    if plan["phase"] == "PREPARING":
        raise VersionedOutputError("候选仍在复制准备中；请重新运行同一 begin-revision 续作")
    rows = plan["files"]
    assert isinstance(rows, list)
    resuming = plan["phase"] == "FINALIZING"
    resolved_rows: list[tuple[Path | None, Path, Path, Path | None]] = []
    for raw in rows:
        assert isinstance(raw, dict)  # _load_plan validates every mapping.
        source = output_dir / str(raw["source"]) if "source" in raw else None
        candidate = output_dir / str(raw["candidate"])
        target = output_dir / str(raw["target"])
        archived = output_dir / str(raw["archived"]) if "archived" in raw else None
        allow_directory = raw["mode"] != "copy"
        for path, label in (
            (source, "当前文件"),
            (candidate, "候选文件"),
            (target, "发布文件"),
            (archived, "归档文件"),
        ):
            if path is None:
                continue
            if path.is_symlink() or (
                path.exists()
                and not path.is_file()
                and not (allow_directory and path.is_dir())
            ):
                raise VersionedOutputError(f"{label}路径不是普通文件：{path}")
        if candidate.exists() and target.exists():
            if not resuming or not _same_file(candidate, target):
                raise VersionedOutputError(f"候选与目标同时存在，停止以避免歧义：{target.name}")
        if not candidate.exists() and not target.exists():
            raise VersionedOutputError(f"候选文件缺失：{candidate}")
        if not resuming and target.exists():
            raise VersionedOutputError(f"发布路径已经存在，禁止覆盖：{target}")
        if source is not None and archived is not None:
            if source.exists() and archived.exists():
                if not resuming or not _same_file(source, archived):
                    raise VersionedOutputError(f"当前文件与归档同时存在，停止以避免覆盖：{source.name}")
            if not source.exists() and not archived.exists():
                raise VersionedOutputError(f"当前文件和归档都缺失：{source.name}")
            if not resuming and archived.exists():
                raise VersionedOutputError(f"old 归档路径已经存在，禁止覆盖：{archived}")
        resolved_rows.append((source, candidate, target, archived))

    if not dry_run:
        if plan["phase"] != "FINALIZING":
            plan["phase"] = "FINALIZING"
            _write_plan(plan_path, plan, exclusive=False)
        published: list[tuple[Path, Path]] = []
        archived_now: list[tuple[Path, Path]] = []
        try:
            for _source, candidate, target, _archived in resolved_rows:
                if candidate.exists():
                    _move_without_overwrite(candidate, target)
                    published.append((candidate, target))
            for source, _candidate, _target, archived in resolved_rows:
                if source is not None and archived is not None and source.exists():
                    _move_without_overwrite(source, archived)
                    archived_now.append((source, archived))
        except OSError as error:
            rollback_errors: list[str] = []
            for source, archived in reversed(archived_now):
                try:
                    _move_without_overwrite(archived, source)
                except OSError:
                    rollback_errors.append(archived.name)
            for candidate, target in reversed(published):
                try:
                    _move_without_overwrite(target, candidate)
                except OSError:
                    rollback_errors.append(target.name)
            detail = ""
            if rollback_errors:
                detail = "；以下文件需人工检查：" + "、".join(rollback_errors)
            raise VersionedOutputError(
                "版本切换中断，已尝试恢复本次移动；计划仍保留，可检查后续作" + detail
            ) from error
        if not all(
            target.exists()
            and not candidate.exists()
            and (archived is None or archived.exists())
            and (source is None or not source.exists())
            for source, candidate, target, archived in resolved_rows
        ):
            raise VersionedOutputError("版本切换未完整结束；保留计划以便恢复")
        try:
            plan_path.unlink()
        except OSError as error:
            raise VersionedOutputError(
                "新版本已经完整切换，但 tmp 中的计划未能清理；检查目录后再次 finalize"
            ) from error

    return {
        "status": "READY-TO-FINALIZE" if dry_run else "FINALIZED",
        "current_version": plan["next_version"],
        "published": [target.name for _source, _candidate, target, _archived in resolved_rows],
        "archived": [
            archived.name
            for _source, _candidate, _target, archived in resolved_rows
            if archived is not None
        ],
        "dry_run": dry_run,
    }


def inspect_output(output_dir: Path) -> dict[str, object]:
    output_dir = output_dir.resolve()
    if not output_dir.is_dir():
        raise VersionedOutputError(f"输出目录不存在：{output_dir}")
    versioned: list[dict[str, str]] = []
    unversioned: list[str] = []
    plan_path = output_dir / "tmp" / PLAN_NAME
    pending_phase: str | None = None
    if plan_path.exists():
        _loaded_path, plan = _load_plan(output_dir)
        phase = plan["phase"]
        assert isinstance(phase, str)
        pending_phase = phase
    for path in sorted(output_dir.iterdir(), key=lambda item: item.name):
        if path.is_symlink() or not (path.is_file() or path.is_dir()):
            continue
        try:
            prefix, version, extension = parse_versioned_name(path.name)
        except VersionedOutputError:
            if path.is_file():
                unversioned.append(path.name)
        else:
            versioned.append(
                {"file": path.name, "prefix": prefix, "version": version, "extension": extension}
            )
    return {
        "output_dir": str(output_dir),
        "old_exists": (output_dir / "old").is_dir(),
        "tmp_exists": (output_dir / "tmp").is_dir(),
        "pending_revision": pending_phase is not None,
        "pending_phase": pending_phase,
        "versioned_files": versioned,
        "other_files": unversioned,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="管理普通工作稿与成品文件的同目录版本切换，不覆盖旧文件。"
    )
    parser.add_argument("--version", action="version", version=VERSION)
    subparsers = parser.add_subparsers(dest="command", required=True)

    ensure = subparsers.add_parser("ensure-output-dir", help="检查或建立 old/ 与 tmp/")
    ensure.add_argument("output_dir", type=Path)
    ensure.add_argument("--dry-run", action="store_true")

    inspect_parser = subparsers.add_parser("inspect", help="只读列出当前版本与目录状态")
    inspect_parser.add_argument("output_dir", type=Path)

    begin = subparsers.add_parser("begin-revision", help="登记成品组并准备 tmp/ 新版本候选")
    begin.add_argument("output_dir", type=Path)
    begin.add_argument("--current", action="append", default=[], help="复制编辑的当前文件；可重复")
    begin.add_argument(
        "--regenerate", action="append", default=[],
        help="待重新生成的当前文件或目录；只登记，不复制；可重复",
    )
    begin.add_argument(
        "--add", action="append", default=[],
        help="首次新增的新版文件或目录名；只登记，不建立 old/ 归档；可重复",
    )
    begin.add_argument("--next-version", required=True)
    begin.add_argument("--dry-run", action="store_true")

    finalize = subparsers.add_parser("finalize-revision", help="发布候选并把上一版移入 old/")
    finalize.add_argument("output_dir", type=Path)
    finalize.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "ensure-output-dir":
            result = ensure_output_dir(args.output_dir, args.dry_run)
        elif args.command == "inspect":
            result = inspect_output(args.output_dir)
        elif args.command == "begin-revision":
            result = begin_revision(
                args.output_dir, args.current, args.next_version, args.dry_run,
                regenerate_files=args.regenerate, add_files=args.add,
            )
        elif args.command == "finalize-revision":
            result = finalize_revision(args.output_dir, args.dry_run)
        else:  # pragma: no cover
            parser.error("未知命令")
            return 2
    except VersionedOutputError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
