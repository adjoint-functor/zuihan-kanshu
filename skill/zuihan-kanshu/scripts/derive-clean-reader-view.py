#!/usr/bin/env python3
"""Validate and copy the selected current reader Markdown without filtering it."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path


PROFILE_MARKERS = ("<!-- BEGIN:BUILD_PROFILE -->", "<!-- END:BUILD_PROFILE -->")


def formula_sequence(text: str) -> list[str]:
    pattern = re.compile(
        r"(?<!\\)\$\$(.*?)(?<!\\)\$\$"
        r"|\\\[(.*?)\\\]"
        r"|\\\((.*?)\\\)"
        r"|(?<!\\)\$(?!\$)(.*?)(?<!\\)\$(?!\$)",
        re.DOTALL,
    )
    formulas: list[str] = []
    for match in pattern.finditer(text):
        formulas.append(next(group for group in match.groups() if group is not None))
    return formulas


def heading_sequence(text: str) -> list[str]:
    return [
        line.rstrip("\r\n")
        for line in text.splitlines(keepends=True)
        if re.match(r"^#{1,6}\s+\S", line)
    ]


def fail(message: str) -> "None":
    raise ValueError(message)


def strip_code(text: str) -> str:
    """Remove fenced and inline code from delimiter analysis, preserving lines."""
    output: list[str] = []
    fence_char: str | None = None
    fence_length = 0
    for line in text.splitlines(keepends=True):
        match = re.match(r"^\s*(`{3,}|~{3,})", line)
        if fence_char is None and match:
            fence = match.group(1)
            fence_char = fence[0]
            fence_length = len(fence)
            output.append("\n" if line.endswith("\n") else "")
            continue
        if fence_char is not None:
            closing = re.match(rf"^\s*{re.escape(fence_char)}{{{fence_length},}}\s*$", line.rstrip("\r\n"))
            if closing:
                fence_char = None
                fence_length = 0
            output.append("\n" if line.endswith("\n") else "")
            continue
        output.append(line)
    if fence_char is not None:
        fail("unclosed fenced code block")
    without_fences = "".join(output)
    return re.sub(r"`+[^`\n]*`+", "", without_fences)


def is_escaped(text: str, index: int) -> bool:
    count = 0
    cursor = index - 1
    while cursor >= 0 and text[cursor] == "\\":
        count += 1
        cursor -= 1
    return count % 2 == 1


def validate_math_delimiters(text: str) -> None:
    cleaned = strip_code(text)
    state: str | None = None
    index = 0
    while index < len(cleaned):
        if cleaned.startswith("$$", index) and not is_escaped(cleaned, index):
            if state is None:
                state = "$$"
            elif state == "$$":
                state = None
            else:
                fail(f"nested or mismatched $$ delimiter at character {index}")
            index += 2
            continue

        token = cleaned[index : index + 2]
        if token in {r"\[", r"\]", r"\(", r"\)"} and not is_escaped(cleaned, index):
            opener_to_state = {r"\[": r"\[", r"\(": r"\("}
            closer_to_state = {r"\]": r"\[", r"\)": r"\("}
            if token in opener_to_state:
                if state is not None:
                    fail(f"nested math delimiter {token} at character {index}")
                state = opener_to_state[token]
            else:
                expected = closer_to_state[token]
                if state != expected:
                    fail(f"unmatched math delimiter {token} at character {index}")
                state = None
            index += 2
            continue

        if cleaned[index] == "$" and not is_escaped(cleaned, index):
            if state is None:
                state = "$"
            elif state == "$":
                state = None
            else:
                fail(f"inline $ nested in {state} math at character {index}")
        index += 1

    if state is not None:
        fail(f"unclosed math delimiter: {state}")


def pandoc_implicit_identifier(raw_heading: str) -> str:
    """Approximate Pandoc's auto_identifier extension for ATX headings."""
    text = re.sub(r"\s+#+\s*$", "", raw_heading.strip())
    text = re.sub(r"\s+\{[^{}]*\}\s*$", "", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"!\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"`+([^`]*)`+", r"\1", text)
    text = re.sub(r"(?<!\w)_([^_]+)_(?!\w)", r"\1", text)
    text = text.replace("*", "").replace("~", "")
    text = re.sub(r"\\([\\`*{}\[\]()#+.!_-])", r"\1", text)
    text = text.lower()

    output: list[str] = []
    started = False
    pending_hyphen = False
    for character in text:
        if character.isspace():
            if started:
                pending_hyphen = True
            continue
        if not started:
            if not character.isalpha():
                continue
            started = True
        if character.isalnum() or character in "_-.":
            if pending_hyphen and output and output[-1] != "-":
                output.append("-")
            output.append(character)
            pending_hyphen = False
    return "".join(output).rstrip("-") or "section"


def explicit_markdown_identifiers(text: str) -> list[str]:
    identifiers: list[str] = []
    for attributes in re.findall(r"\{([^{}\n]*)\}", text):
        identifiers.extend(
            re.findall(
                r"(?:^|\s)#([A-Za-z0-9_.:-]+)(?=\s|$)",
                attributes,
            )
        )
    return identifiers


def implicit_heading_identifiers(text: str, explicit: list[str]) -> list[str]:
    used = set(explicit)
    identifiers: list[str] = []
    for line in text.splitlines():
        match = re.match(r"^ {0,3}#{1,6}\s+(.+?)\s*$", line)
        if not match:
            continue
        heading = match.group(1)
        attributes = re.search(r"\{([^{}\n]*)\}\s*$", heading)
        if attributes and re.search(
            r"(?:^|\s)#[A-Za-z0-9_.:-]+(?=\s|$)",
            attributes.group(1),
        ):
            continue
        base = pandoc_implicit_identifier(heading)
        candidate = base
        suffix = 1
        while candidate in used:
            candidate = f"{base}-{suffix}"
            suffix += 1
        used.add(candidate)
        identifiers.append(candidate)
    return identifiers


def validate_labels_and_references(text: str) -> dict[str, int]:
    cleaned = re.sub(r"<!--.*?-->", "", strip_code(text), flags=re.DOTALL)
    labels = re.findall(r"\\label\s*\{([^{}]+)\}", cleaned)
    duplicates = sorted(label for label, count in Counter(labels).items() if count > 1)
    if duplicates:
        fail("duplicate LaTeX labels: " + ", ".join(duplicates))

    raw_references = re.findall(
        r"\\(ref|eqref|autoref|cref|Cref|pageref)\*?\s*\{([^{}]+)\}",
        cleaned,
    )
    references: list[str] = []
    for command, group in raw_references:
        values = group.split(",") if command in {"cref", "Cref"} else [group]
        references.extend(item.strip() for item in values if item.strip())
    unresolved = sorted(set(references) - set(labels))
    if unresolved:
        fail("unresolved LaTeX references: " + ", ".join(unresolved))

    identifiers = explicit_markdown_identifiers(cleaned)
    duplicate_ids = sorted(item for item, count in Counter(identifiers).items() if count > 1)
    if duplicate_ids:
        fail("duplicate explicit Markdown identifiers: " + ", ".join(duplicate_ids))
    implicit_identifiers = implicit_heading_identifiers(cleaned, identifiers)
    anchor_uses = re.findall(r"\]\(#([A-Za-z0-9_.:-]+)\)", cleaned)
    missing_anchors = sorted(
        set(anchor_uses) - set(identifiers) - set(implicit_identifiers)
    )
    if missing_anchors:
        fail("unresolved Markdown anchors: " + ", ".join(missing_anchors))

    footnote_definitions = re.findall(r"(?m)^\s*\[\^([^\]]+)\]\s*:", cleaned)
    duplicate_footnotes = sorted(
        item for item, count in Counter(footnote_definitions).items() if count > 1
    )
    if duplicate_footnotes:
        fail("duplicate Markdown footnotes: " + ", ".join(duplicate_footnotes))
    footnote_uses = re.findall(r"\[\^([^\]]+)\]", cleaned)
    missing_footnotes = sorted(set(footnote_uses) - set(footnote_definitions))
    if missing_footnotes:
        fail("unresolved Markdown footnotes: " + ", ".join(missing_footnotes))

    return {
        "latex_label_count": len(labels),
        "latex_reference_count": len(references),
        "markdown_identifier_count": len(identifiers),
        "markdown_implicit_identifier_count": len(implicit_identifiers),
        "markdown_anchor_count": len(anchor_uses),
        "markdown_footnote_count": len(footnote_definitions),
    }


def exclusive_write(path: Path, data: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    try:
        descriptor = os.open(path, flags, 0o644)
    except FileExistsError:
        fail(f"output already exists: {path}")
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
    except Exception:
        path.unlink(missing_ok=True)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Selected current reader Markdown")
    parser.add_argument("output", type=Path, help="Validated reader Markdown; never overwritten")
    parser.add_argument("--json-report", type=Path)
    args = parser.parse_args()

    created_paths: list[Path] = []
    try:
        outputs = [args.output, *([args.json_report] if args.json_report else [])]
        identities = [args.input.resolve(), *(path.resolve() for path in outputs)]
        if len(set(identities)) != len(identities):
            fail("input and all output paths must be different files")
        for path in outputs:
            if path.exists():
                fail(f"output already exists: {path}")
        with args.input.open(encoding="utf-8", newline="") as handle:
            reader = handle.read()
        if any(marker in reader for marker in PROFILE_MARKERS):
            fail("reader body must not contain build_profile markers; use a separate control file")
        if not reader.strip():
            fail("reader body is empty")

        validate_math_delimiters(reader)
        reference_counts = validate_labels_and_references(reader)

        exclusive_write(args.output, reader)
        created_paths.append(args.output)
        report = {
            "input": str(args.input),
            "output": str(args.output),
            "input_format": "clean-body",
            "formula_count": len(formula_sequence(reader)),
            "heading_count": len(heading_sequence(reader)),
            "math_delimiters": "PASS",
            **reference_counts,
            "status": "PASS",
        }
        if args.json_report:
            exclusive_write(
                args.json_report,
                json.dumps(report, ensure_ascii=False, indent=2) + os.linesep,
            )
            created_paths.append(args.json_report)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0
    except (OSError, UnicodeError, ValueError) as exc:
        for path in reversed(created_paths):
            path.unlink(missing_ok=True)
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
