#!/usr/bin/env python3
"""Mechanical preflight for a clean mathematical PDF.

The script detects deterministic defects and renders every page. It does not
replace human inspection of the rendered pages.
"""

from __future__ import annotations

import argparse
import json
import logging
import math
import os
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


RENDER_DPI = 180


@dataclass
class Issue:
    severity: str
    check: str
    message: str
    pages: list[int] | None = None


def add(
    issues: list[Issue],
    severity: str,
    check: str,
    message: str,
    pages: list[int] | None = None,
) -> None:
    issues.append(Issue(severity, check, message, pages))


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    # Some PDF tools return zero after omitting fonts/text they could not read.
    if result.returncode == 0 and "Syntax Error:" in result.stderr:
        result.returncode = 1
    return result


def require(name: str, issues: list[Issue]) -> bool:
    if shutil.which(name):
        return True
    add(issues, "ERROR", "dependency", f"required command is unavailable: {name}")
    return False


def exclusive_write(path: Path, data: bytes, issues: list[Issue]) -> bool:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        descriptor = os.open(path, flags, 0o644)
    except FileExistsError:
        add(issues, "ERROR", "report", f"output already exists: {path}")
        return False
    except OSError as exc:
        add(issues, "ERROR", "report", f"cannot create {path}: {exc}")
        return False
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        return True
    except Exception as exc:
        path.unlink(missing_ok=True)
        add(issues, "ERROR", "report", f"cannot write {path}: {exc}")
        return False


def parse_info(output: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for line in output.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            fields[key.strip()] = value.strip()
    return fields


def inspect_build_log(path: Path | None, issues: list[Issue]) -> None:
    if path is None:
        add(issues, "WARN", "build-log", "no compiler log was supplied")
        return
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        add(issues, "ERROR", "build-log", f"cannot read compiler log: {exc}")
        return

    run_markers = list(re.finditer(
        r"(?m)^(?:\[makePDF\] Run #\d+|\[final-pdf-build\] Final XeLaTeX log)\s*$",
        text,
    ))
    final_pass = text[run_markers[-1].start() :] if run_markers else text

    patterns = [
        (
            "ERROR",
            r"(?mi)^!\s+(?:(?:LaTeX|pdfTeX|LuaTeX|XeTeX)\s+)?Error\b|^!\s+(?:Package|Class)\s+\S+\s+Error\b",
            "compiler error",
            False,
        ),
        ("ERROR", r"(?i)Emergency stop|Fatal error|Undefined control sequence", "fatal compiler condition", False),
        ("ERROR", r"(?i)Missing character: There is no", "missing glyph", False),
        (
            "ERROR",
            r"(?i)There were undefined (?:references|citations)|Reference .* undefined|Citation .* undefined",
            "unresolved reference or citation",
            True,
        ),
        (
            "ERROR",
            r"(?i)(?:Package\s+biblatex\s+Warning:.*(?:rerun|\(re\)run)\s+(?:Biber|LaTeX)|Please\s+(?:rerun|\(re\)run)\s+(?:Biber|LaTeX)|Rerun\s+to\s+get\s+cross-references\s+right)",
            "incomplete bibliography or cross-reference rerun",
            True,
        ),
        ("WARN", r"(?i)Overfull \\hbox|Overfull \\vbox", "overfull box", True),
    ]
    for severity, pattern, label, final_only in patterns:
        matches = re.findall(pattern, final_pass if final_only else text)
        if matches:
            add(issues, severity, "build-log", f"{label}: {len(matches)} occurrence(s)")
    # Package warnings need not contain "Font" (xeCJK's unknown-family warning
    # is one example). Keep the actual message, including wrapped continuation
    # lines, and deduplicate repeated final-pass messages. Info is not Warning.
    warning_start = re.compile(r"^(?:LaTeX(?: Font)?|(?:Package|Class)\s+\S+(?: Font)?) Warning:\s*", re.I)
    lines = final_pass.splitlines()
    seen: set[str] = set()
    for index, line in enumerate(lines):
        if not warning_start.match(line):
            continue
        parts = [line.strip()]
        for continuation in lines[index + 1:]:
            if not continuation.strip() or warning_start.match(continuation):
                break
            if not re.match(r"^(?:\([\w.-]+\)\s+|\s+\S)", continuation):
                break
            parts.append(re.sub(r"^\([\w.-]+\)\s*", "", continuation).strip())
        message = " ".join(parts)
        if message in seen:
            continue
        seen.add(message)
        # The stronger unresolved-reference / rerun diagnostics above already
        # classify these messages as errors; do not count them again as warnings.
        if any(severity == "ERROR" and final_only and re.search(pattern, message)
               for severity, pattern, _label, final_only in patterns):
            continue
        add(issues, "WARN", "build-log", message)


def parse_fonts(output: str) -> Iterable[tuple[str, str, str, str]]:
    row = re.compile(
        r"^(.*?)\s{2,}(.*?)\s{2,}(.*?)\s+(yes|no)\s+(yes|no)\s+"
        r"(yes|no)\s+\d+\s+\d+\s*$"
    )
    for line in output.splitlines():
        match = row.match(line)
        if match:
            name, font_type, _encoding, embedded, _subset, unicode_map = match.groups()
            yield name.strip(), font_type.strip(), embedded, unicode_map


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def inspect_bbox(pdf: Path, issues: list[Issue]) -> list[int]:
    result = run(["pdftotext", "-bbox", str(pdf), "-"])
    if result.returncode:
        add(issues, "ERROR", "page-boundary", result.stderr.strip() or "bbox extraction failed")
        return []
    try:
        root = ET.fromstring(result.stdout)
    except ET.ParseError as exc:
        add(issues, "ERROR", "page-boundary", f"cannot parse bbox output: {exc}")
        return []

    bad_pages: list[int] = []
    samples: list[str] = []
    for page_number, page in enumerate(
        (node for node in root.iter() if local_name(node.tag) == "page"), start=1
    ):
        width = float(page.attrib.get("width", "0"))
        height = float(page.attrib.get("height", "0"))
        bad: list[str] = []
        for word in (node for node in page.iter() if local_name(node.tag) == "word"):
            x_min = float(word.attrib.get("xMin", "0"))
            x_max = float(word.attrib.get("xMax", "0"))
            y_min = float(word.attrib.get("yMin", "0"))
            y_max = float(word.attrib.get("yMax", "0"))
            if (
                x_min < -0.5
                or x_max > width + 0.5
                or y_min < -0.5
                or y_max > height + 0.5
            ):
                value = " ".join("".join(word.itertext()).split())
                bad.append(
                    f"{value!r} x=[{x_min:.1f}, {x_max:.1f}]/{width:.1f}, "
                    f"y=[{y_min:.1f}, {y_max:.1f}]/{height:.1f}"
                )
        if bad:
            bad_pages.append(page_number)
            samples.append(f"p.{page_number}: {bad[0]}")
    if bad_pages:
        add(
            issues,
            "ERROR",
            "page-boundary",
            "word bounding boxes cross page boundaries: " + "; ".join(samples[:10]),
            bad_pages,
        )
    return bad_pages


def scan_patterns(
    text: str,
    source: str,
    patterns: list[str],
    issues: list[Issue],
    severity: str = "ERROR",
    page_texts: list[str] | None = None,
) -> None:
    for pattern in patterns:
        try:
            count = len(re.findall(pattern, text, re.IGNORECASE | re.MULTILINE))
        except re.error as exc:
            add(issues, "ERROR", "forbidden-pattern", f"invalid regex /{pattern}/: {exc}")
            continue
        if count:
            pages = None
            if page_texts is not None:
                pages = [
                    index + 1
                    for index, page in enumerate(page_texts)
                    if re.search(pattern, page, re.IGNORECASE | re.MULTILINE)
                ]
            add(
                issues,
                severity,
                "engineering-residue",
                f"{source} contains /{pattern}/: {count} occurrence(s)",
                pages,
            )


_C2PA_STORE = bytes.fromhex("6332706100110010800000aa00389b71")
_C2PA_MANIFESTS = {
    bytes.fromhex(prefix + "00110010800000aa00389b71")
    for prefix in ("63326d61", "6332756d", "63326d64", "6332636d")
}


def _jumb_boxes(data: bytes, start: int, end: int, *, to_eof: bool = False) -> list[tuple]:
    """Read ISO box boundaries, without interpreting claims or signatures."""
    boxes = []
    while start < end:
        if end - start < 8:
            raise ValueError("truncated JUMBF box header")
        length = int.from_bytes(data[start:start + 4], "big")
        kind = data[start + 4:start + 8]
        header = 8
        extends = length == 0
        if extends:
            if not to_eof:
                raise ValueError("zero-length child requires a zero-length parent")
            length = end - start
        elif length == 1:
            if end - start < 16:
                raise ValueError("truncated JUMBF extended length")
            length = int.from_bytes(data[start + 8:start + 16], "big")
            header = 16
        if length < header or length > end - start:
            raise ValueError("invalid or out-of-bounds JUMBF box length")
        boxes.append((kind, start + header, start + length, extends))
        start += length
    return boxes


def _jumb_description(data: bytes, start: int, end: int) -> tuple[bytes, str | None]:
    if end - start < 17:
        raise ValueError("truncated JUMBF description")
    uuid = data[start:start + 16]
    toggles = data[start + 16]
    position = start + 17
    label = None
    if toggles & 2:
        terminator = data.find(b"\0", position, end)
        if terminator < 0:
            raise ValueError("unterminated JUMBF label")
        label = data[position:terminator].decode("utf-8")
        position = terminator + 1
    position += (4 if toggles & 4 else 0) + (32 if toggles & 8 else 0)
    if position > end:
        raise ValueError("truncated optional JUMBF description field")
    if toggles & 16:
        if len(_jumb_boxes(data, position, end)) != 1:
            raise ValueError("invalid JUMBF private description box")
        position = end
    if toggles & 0xE0 or position != end:
        raise ValueError("invalid JUMBF description fields")
    return uuid, label


def _check_c2pa_container(data: bytes) -> None:
    """Recognize a bounded C2PA store container, not authenticity or claim validity.

    C2PA 2.4 sections 11.1.4.2 and A.4; ISO/IEC 19566-5 box framing.
    Accept multiple manifests and extensions, including legacy/updated/compressed
    manifest types. CBOR, compressed content, signatures and trust are not validated.
    """
    top = _jumb_boxes(data, 0, len(data), to_eof=True)
    if len(top) != 1 or top[0][0] != b"jumb":
        raise ValueError("expected one complete JUMBF store")
    budget = 10000

    def container(box, depth=0):
        nonlocal budget
        budget -= 1
        if depth > 32 or budget < 0:
            raise ValueError("JUMBF container nesting or count limit exceeded")
        _kind, start, end, extends = box
        children = _jumb_boxes(data, start, end, to_eof=extends)
        if not children or children[0][0] != b"jumd":
            raise ValueError("JUMBF description must be the first box")
        if sum(child[0] == b"jumd" for child in children) != 1:
            raise ValueError("duplicate JUMBF description")
        if sum(child[0] == b"free" for child in children) > 1:
            raise ValueError("duplicate JUMBF padding box")
        if not any(child[0] not in (b"jumd", b"free") for child in children):
            raise ValueError("JUMBF container has no content")
        uuid, label = _jumb_description(data, children[0][1], children[0][2])
        nested = [container(child, depth + 1) for child in children[1:] if child[0] == b"jumb"]
        return uuid, label, nested

    uuid, label, manifests = container(top[0])
    if uuid != _C2PA_STORE or label != "c2pa":
        raise ValueError("JUMBF store UUID or label is not C2PA")
    if not any(kind in _C2PA_MANIFESTS and name for kind, name, _children in manifests):
        raise ValueError("C2PA store contains no recognized manifest container")


def inspect_pdf_objects(pdf: Path, patterns: list[str], issues: list[Issue]) -> dict:
    """Check the document's navigation and attachments using the available Python runtime."""
    result = {"backend": "pypdf", "complete": False, "outlines": 0,
              "named_destinations": 0, "internal_links": 0, "embedded_files": 0,
              "file_attachment_annotations": 0, "associated_files": 0,
              "attachment_filespecs": 0, "content_credentials": 0,
              "ordinary_attachments": 0, "attachment_details": [],
              "credential_validation": "container-structure-only; authenticity, claims and trust unchecked"}
    try:
        from pypdf import PdfReader
        from pypdf.generic import NameObject
    except ImportError:
        add(issues, "ERROR", "dependency", "pypdf is unavailable; PDF objects were not inspected")
        return result

    class Diagnostics(logging.Handler):
        def emit(self, record):
            add(issues, "WARN", "pdf-objects", record.getMessage())

    logger = logging.getLogger("pypdf")
    handler = Diagnostics(logging.WARNING)
    logger.addHandler(handler)
    reader = None
    try:
        reader = PdfReader(pdf, strict=True)
        destinations = reader.named_destinations
        page_count = len(reader.pages)

        def resolve(value):
            return value.get_object() if hasattr(value, "get_object") else value

        def object_identity(value):
            reference = value if hasattr(value, "idnum") else getattr(value, "indirect_reference", None)
            if reference is not None:
                return ("indirect", reference.idnum, reference.generation)
            return ("direct", id(value))

        filespecs = {}

        def collect_filespec(value, source):
            resolved = resolve(value)
            identity = object_identity(value if hasattr(value, "idnum") else resolved)
            item = filespecs.setdefault(identity, {"spec": resolved, "sources": []})
            if source not in item["sources"]:
                item["sources"].append(source)

        def collect_af(owner, source):
            entries = resolve(owner.get("/AF", []))
            if not isinstance(entries, (list, tuple)):
                raise ValueError("associated-file entry is not an array")
            result["associated_files"] += len(entries)
            for entry in entries:
                collect_filespec(entry, source)

        def is_credential(spec):
            try:
                relationship = resolve(spec.get("/AFRelationship")) if isinstance(spec, dict) else None
                if not isinstance(relationship, NameObject) or relationship != "/C2PA_Manifest":
                    return False, "missing C2PA Filespec relationship"
                embedded = resolve(spec.get("/EF"))
                if not isinstance(embedded, dict) or not embedded:
                    return False, "missing embedded-file streams"
                streams = set()
                for value in embedded.values():
                    stream = resolve(value)
                    identity = object_identity(value if hasattr(value, "idnum") else stream)
                    if identity in streams:
                        continue
                    streams.add(identity)
                    mime = resolve(stream.get("/Subtype")) if isinstance(stream, dict) else None
                    if not callable(getattr(stream, "get_data", None)) or not isinstance(mime, NameObject) or mime != "/application/c2pa":
                        return False, "embedded-file stream is missing the C2PA MIME name"
                    _check_c2pa_container(stream.get_data())
                return True, "C2PA container structure; authenticity, claims and trust unchecked"
            except Exception as exc:
                return False, f"invalid C2PA container: {exc}"

        def destination_page(value):
            value = resolve(value)
            if isinstance(value, str):
                target = destinations.get(value)
                return reader.get_destination_page_number(target) if target is not None else None
            if isinstance(value, dict) and "/D" in value:
                value = resolve(value["/D"])
            if isinstance(value, (list, tuple)) and value:
                page = resolve(value[0])
                if isinstance(page, dict) and page.get("/Type") == "/Page":
                    return reader.get_page_number(page)
            return None

        def check_destination(value, label, pages=None):
            number = destination_page(value)
            if number is None or not 0 <= number < page_count:
                add(issues, "ERROR", "navigation", f"unresolved PDF destination: {label}", pages)

        for name, destination in destinations.items():
            number = reader.get_destination_page_number(destination)
            result["named_destinations"] += 1
            if number is None or not 0 <= number < page_count:
                add(issues, "ERROR", "navigation", f"unresolved named destination: {name}")

        # Read actual outline actions: a heading without an action is valid,
        # whereas a broken /Dest must not become a synthetic first-page target.
        seen = set()

        def outlines(first):
            node = resolve(first)
            while node:
                identity = id(node)
                if identity in seen:
                    raise ValueError("cyclic or repeated outline node")
                seen.add(identity)
                result["outlines"] += 1
                title = str(node.get("/Title", ""))
                scan_patterns(title, "PDF outline", patterns, issues)
                if "/Dest" in node:
                    check_destination(node["/Dest"], f"outline {title!r}")
                elif "/A" in node:
                    action = resolve(node["/A"])
                    if action.get("/S") == "/GoTo":
                        check_destination(action.get("/D"), f"outline {title!r}")
                if "/First" in node:
                    outlines(node["/First"])
                node = resolve(node.get("/Next"))

        root = reader.root_object
        outline_root = resolve(root.get("/Outlines"))
        if outline_root:
            outlines(outline_root.get("/First"))
        result["embedded_files"] = len(list(reader.attachment_list))
        names = resolve(root.get("/Names", {}))
        embedded_root = resolve(names.get("/EmbeddedFiles")) if isinstance(names, dict) else None
        seen_name_nodes = set()

        def embedded_names(node):
            node = resolve(node)
            identity = object_identity(node)
            if identity in seen_name_nodes:
                return
            seen_name_nodes.add(identity)
            entries = resolve(node.get("/Names", []))
            if len(entries) % 2:
                raise ValueError("invalid embedded-file name tree")
            for index in range(1, len(entries), 2):
                collect_filespec(entries[index], "EmbeddedFiles")
            for child in resolve(node.get("/Kids", [])):
                embedded_names(child)

        if embedded_root is not None:
            embedded_names(embedded_root)
        collect_af(root, "document AF")
        for number, page in enumerate(reader.pages, 1):
            collect_af(page, f"page {number} AF")
            for ref in resolve(page.get("/Annots", [])):
                annotation = resolve(ref)
                if annotation.get("/Subtype") == "/FileAttachment":
                    result["file_attachment_annotations"] += 1
                    # A malformed annotation with no /FS remains an ordinary
                    # attachment, even when no EmbeddedFiles name tree exists.
                    collect_filespec(annotation.get("/FS", annotation), f"page {number} annotation")
                if annotation.get("/Subtype") != "/Link":
                    continue
                if "/Dest" in annotation:
                    result["internal_links"] += 1
                    check_destination(annotation["/Dest"], "internal link", [number])
                elif "/A" in annotation:
                    action = resolve(annotation["/A"])
                    if action.get("/S") == "/GoTo":
                        result["internal_links"] += 1
                        check_destination(action.get("/D"), "internal link", [number])
        result["attachment_filespecs"] = len(filespecs)
        for identity, item in filespecs.items():
            credential, reason = is_credential(item["spec"])
            result["content_credentials" if credential else "ordinary_attachments"] += 1
            result["attachment_details"].append({
                "filespec_identity": ":".join(map(str, identity)),
                "kind": "content-credential" if credential else "ordinary-attachment",
                "sources": item["sources"], "reason": reason,
            })
        if result["ordinary_attachments"]:
            add(issues, "ERROR", "attachments", f"PDF contains {result['ordinary_attachments']} ordinary or unrecognized attachment(s)")
        if result["content_credentials"]:
            add(issues, "INFO", "content-credentials", f"{result['content_credentials']} C2PA content credential(s); container structure only, not signature or trust verification")
        result["complete"] = True
    except Exception as exc:
        add(issues, "ERROR", "pdf-objects", f"PDF object inspection did not complete: {exc}")
    finally:
        if reader is not None:
            reader.close()
        logger.removeHandler(handler)
    return result


def natural_page_key(path: Path) -> tuple[int, str]:
    match = re.search(r"(\d+)(?=\.[^.]+$)", path.name)
    return (int(match.group(1)) if match else math.inf, path.name)


def create_contact_sheets(images: list[Path], render_dir: Path, issues: list[Issue]) -> list[Path]:
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        if shutil.which("montage") and images:
            target = render_dir / "contact-sheet.png"
            result = run(
                [
                    "montage",
                    *[str(image) for image in images],
                    "-thumbnail",
                    "220x312",
                    "-tile",
                    "4x",
                    "-geometry",
                    "+6+20",
                    str(target),
                ]
            )
            if result.returncode == 0:
                return [target]
        add(issues, "WARN", "contact-sheet", "Pillow and a usable montage command are unavailable")
        return []

    columns = 4
    rows = 15
    tile_width = 240
    tile_height = 340
    per_sheet = columns * rows
    sheets: list[Path] = []
    for chunk_start in range(0, len(images), per_sheet):
        chunk = images[chunk_start : chunk_start + per_sheet]
        used_rows = math.ceil(len(chunk) / columns)
        sheet = Image.new("RGB", (columns * tile_width, used_rows * tile_height), "white")
        draw = ImageDraw.Draw(sheet)
        for offset, image_path in enumerate(chunk):
            page_number = chunk_start + offset + 1
            with Image.open(image_path) as page:
                thumbnail = page.convert("RGB")
                thumbnail.thumbnail((220, 310))
                x = (offset % columns) * tile_width + (tile_width - thumbnail.width) // 2
                y = (offset // columns) * tile_height + 20
                sheet.paste(thumbnail, (x, y))
                draw.text((x, 3), f"p.{page_number}", fill="black")
        target = render_dir / f"contact-sheet-{len(sheets) + 1:03d}.png"
        sheet.save(target)
        sheets.append(target)
    return sheets


def render_pages(pdf: Path, render_dir: Path, issues: list[Issue]) -> tuple[list[Path], list[Path]]:
    if not require("pdftoppm", issues):
        return [], []
    if render_dir.exists():
        add(issues, "ERROR", "render", f"render directory already exists: {render_dir}")
        return [], []
    try:
        render_dir.mkdir(parents=True, exist_ok=False)
    except FileExistsError:
        add(issues, "ERROR", "render", f"render directory was created concurrently: {render_dir}")
        return [], []
    except OSError as exc:
        add(issues, "ERROR", "render", f"cannot create render directory {render_dir}: {exc}")
        return [], []
    prefix = render_dir / "page"
    result = run(["pdftoppm", "-png", "-r", str(RENDER_DPI), str(pdf), str(prefix)])
    if result.returncode:
        add(issues, "ERROR", "render", result.stderr.strip() or "page rendering failed")
        return [], []
    images = sorted(render_dir.glob("page-*.png"), key=natural_page_key)
    if not images:
        add(issues, "ERROR", "render", "no rendered page images were produced")
        return [], []
    sheets = create_contact_sheets(images, render_dir, issues)
    if not sheets:
        add(issues, "WARN", "contact-sheet", "no contact sheet was produced")
    return images, sheets


def inspect_rendered_edges(images: list[Path], issues: list[Issue]) -> list[int]:
    """Flag raster ink touching a physical page edge, including vector content."""
    try:
        from PIL import Image
    except ImportError:
        add(issues, "WARN", "render-edge", "Pillow is unavailable; raster page edges were not inspected")
        return []

    risky: list[int] = []
    band = 2
    for page_number, image_path in enumerate(images, start=1):
        with Image.open(image_path) as source:
            image = source.convert("L")
            width, height = image.size
            pixels = image.load()
            nonwhite = 0
            for x in range(width):
                for y in range(min(band, height)):
                    nonwhite += pixels[x, y] < 245
                    nonwhite += pixels[x, height - 1 - y] < 245
            for y in range(height):
                for x in range(min(band, width)):
                    nonwhite += pixels[x, y] < 245
                    nonwhite += pixels[width - 1 - x, y] < 245
            if nonwhite:
                risky.append(page_number)
    if risky:
        add(
            issues,
            "WARN",
            "render-edge",
            "rendered ink touches a physical page edge; inspect for clipped text or vector math",
            risky,
        )
    return risky


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--build-log", type=Path)
    parser.add_argument("--render-dir", type=Path, required=True)
    parser.add_argument("--expected-version")
    parser.add_argument("--forbidden-pattern", action="append", default=[])
    parser.add_argument("--require-font", action="append", default=[])
    parser.add_argument("--json-report", type=Path)
    args = parser.parse_args()

    issues: list[Issue] = []
    custom_patterns: list[str] = []
    for pattern in args.forbidden_pattern:
        try:
            re.compile(pattern)
        except re.error as exc:
            add(issues, "ERROR", "forbidden-pattern", f"invalid regex /{pattern}/: {exc}")
        else:
            custom_patterns.append(pattern)
    report: dict[str, object] = {
        "pdf": str(args.pdf),
        "visual_review_required": True,
    }

    required = ["pdfinfo", "pdffonts", "pdftotext"]
    if not args.pdf.is_file():
        add(issues, "ERROR", "input", f"PDF not found: {args.pdf}")
    dependencies_ready = all([require(tool, issues) for tool in required])
    if dependencies_ready and args.pdf.is_file():
        inspect_build_log(args.build_log, issues)

        info_result = run(["pdfinfo", "-enc", "UTF-8", "-isodates", str(args.pdf)])
        if info_result.returncode:
            add(issues, "ERROR", "pdfinfo", info_result.stderr.strip() or "pdfinfo failed")
            info_text = ""
            fields: dict[str, str] = {}
        else:
            info_text = info_result.stdout
            fields = parse_info(info_text)

        fonts_result = run(["pdffonts", str(args.pdf)])
        if fonts_result.returncode:
            add(issues, "ERROR", "fonts", fonts_result.stderr.strip() or "pdffonts failed")
        else:
            fonts = list(parse_fonts(fonts_result.stdout))
            if not fonts:
                add(issues, "WARN", "fonts", "no fonts were parsed from pdffonts output")
            unembedded = [name for name, _kind, embedded, _unicode in fonts if embedded != "yes"]
            type3 = [name for name, kind, _embedded, _unicode in fonts if "Type 3" in kind]
            without_unicode = [name for name, _kind, _embedded, unicode_map in fonts if unicode_map != "yes"]
            if unembedded:
                add(issues, "ERROR", "fonts", "unembedded fonts: " + ", ".join(unembedded))
            if type3:
                add(issues, "ERROR", "fonts", "Type 3 fonts require replacement: " + ", ".join(type3))
            if without_unicode:
                add(
                    issues,
                    "WARN",
                    "fonts",
                    "fonts without a Unicode map require extraction review: " + ", ".join(without_unicode),
                )
            for required_font in args.require_font:
                if not any(required_font.casefold() in name.casefold() for name, _kind, _embedded, _unicode in fonts):
                    add(issues, "ERROR", "fonts", f"required font is absent: {required_font}")

        text_result = run(["pdftotext", "-layout", str(args.pdf), "-"])
        if text_result.returncode:
            add(issues, "ERROR", "text-extraction", text_result.stderr.strip() or "pdftotext failed")
            extracted = ""
            pages: list[str] = []
            sparse_pages: list[int] = []
            blank_pages: list[int] = []
        else:
            extracted = text_result.stdout
            if "\ufffd" in extracted:
                add(issues, "ERROR", "text-extraction", "extracted text contains replacement characters")
            if not re.sub(r"\s+", "", extracted):
                add(
                    issues,
                    "ERROR",
                    "text-extraction",
                    "PDF has no extractable text and is not searchable/copyable",
                )
            pages = extracted.split("\f")
            if pages and not pages[-1].strip():
                pages = pages[:-1]
            blank_pages = [index + 1 for index, page in enumerate(pages) if not page.strip()]
            sparse_pages = [
                index + 1
                for index, page in enumerate(pages)
                if page.strip() and len(re.sub(r"\s+", "", page)) < 80
            ]
            if blank_pages:
                add(issues, "WARN", "page-density", f"text-empty pages: {blank_pages}", blank_pages)
            if sparse_pages:
                add(issues, "WARN", "page-density", f"low-text-density pages: {sparse_pages}", sparse_pages)

        residue_patterns = [
            re.escape("<!-- BEGIN:BUILD_PROFILE -->"),
            re.escape("<!-- END:BUILD_PROFILE -->"),
            *custom_patterns,
        ]
        scan_patterns(
            extracted,
            "extracted PDF text",
            residue_patterns,
            issues,
            page_texts=pages,
        )
        scan_patterns(info_text, "PDF metadata", residue_patterns, issues)

        meta_result = run(["pdfinfo", "-meta", str(args.pdf)])
        if meta_result.returncode == 0:
            scan_patterns(meta_result.stdout, "PDF XMP metadata", residue_patterns, issues)
        else:
            add(issues, "WARN", "metadata", meta_result.stderr.strip() or "XMP metadata inspection failed")

        if args.expected_version:
            variants = [re.escape(args.expected_version), re.escape(args.expected_version.replace(".", "_"))]
            version_pattern = rf"(?:^|[_-])(?:{'|'.join(variants)})$"
            if not re.search(version_pattern, args.pdf.stem):
                add(issues, "ERROR", "version", f"{args.expected_version} is absent from the PDF filename")

        boundary_pages = inspect_bbox(args.pdf, issues)
        report["objects"] = inspect_pdf_objects(args.pdf, residue_patterns, issues)
        images, sheets = render_pages(args.pdf, args.render_dir, issues)
        edge_pages = inspect_rendered_edges(images, issues)

        page_count = int(fields.get("Pages", "0") or 0)
        if images and page_count and len(images) != page_count:
            add(
                issues,
                "ERROR",
                "render",
                f"rendered page count {len(images)} differs from PDF page count {page_count}",
            )

        issue_pages = [page for issue in issues for page in (issue.pages or [])]
        risk_pages = sorted(set(blank_pages + sparse_pages + boundary_pages + edge_pages + issue_pages))
        report.update(
            {
                "page_count": page_count,
                "page_size": fields.get("Page size", "unknown"),
                "title_metadata": fields.get("Title", ""),
                "rendered_page_count": len(images),
                "render_dpi": RENDER_DPI,
                "contact_sheets": [str(path) for path in sheets],
                "risk_pages": risk_pages,
            }
        )

    order = {"ERROR": 0, "WARN": 1, "INFO": 2}
    issues.sort(key=lambda issue: (order.get(issue.severity, 9), issue.check, issue.message))
    report["issues"] = [asdict(issue) for issue in issues]
    report["errors"] = sum(issue.severity == "ERROR" for issue in issues)
    report["warnings"] = sum(issue.severity == "WARN" for issue in issues)

    if args.json_report:
        exclusive_write(
            args.json_report,
            (json.dumps(report, ensure_ascii=False, indent=2) + os.linesep).encode("utf-8"),
            issues,
        )

    issues.sort(key=lambda issue: (order.get(issue.severity, 9), issue.check, issue.message))
    report["issues"] = [asdict(issue) for issue in issues]
    report["errors"] = sum(issue.severity == "ERROR" for issue in issues)
    report["warnings"] = sum(issue.severity == "WARN" for issue in issues)
    for issue in issues:
        suffix = f" pages={issue.pages}" if issue.pages else ""
        print(f"[{issue.severity}] {issue.check}: {issue.message}{suffix}")
    print(json.dumps({key: value for key, value in report.items() if key != "issues"}, ensure_ascii=False))

    return 1 if any(issue.severity == "ERROR" for issue in issues) else 0


if __name__ == "__main__":
    sys.exit(main())
