#!/usr/bin/env python3
"""Search Matlas on demand; preview metadata and read selected statements locally."""

from __future__ import annotations

import argparse
import http.client
import json
import math
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


SEARCH_URL = "https://matlas.ai/api/search"
RESULT_FIELDS = (
    "type", "entity_name", "doi", "title", "authors", "journal", "year",
    "statement", "candidate_id",
)
DEFAULT_TIMEOUT = 30.0
DEFAULT_NUM_RESULTS = 50
DEFAULT_PREVIEW = 10


class MatlasError(Exception):
    """A classified failure, distinct from a successful empty result list."""

    def __init__(self, kind: str, message: str):
        super().__init__(message)
        self.kind = kind


def validate_results(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise MatlasError("response", "expected a JSON array of results")
    results = []
    for index, item in enumerate(value, start=1):
        if not isinstance(item, dict):
            raise MatlasError("response", f"result {index} must be an object")
        for field in RESULT_FIELDS:
            if field not in item or not isinstance(item[field], str):
                raise MatlasError(
                    "response", f"result {index}: {field} must be present and a string"
                )
            try:
                item[field].encode("utf-8")
            except UnicodeEncodeError as exc:
                raise MatlasError(
                    "response", f"result {index}: {field} contains invalid Unicode"
                ) from exc
        if item["type"] not in ("book", "paper"):
            raise MatlasError("response", f"result {index}: type must be book or paper")
        # Preserve the complete returned object, including any additional fields.
        results.append(dict(item))
    return results


def decode_results(raw: bytes) -> list[dict[str, Any]]:
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise MatlasError("response", "expected valid UTF-8 JSON") from exc
    return validate_results(value)


def search(
    query: str, num_results: int = DEFAULT_NUM_RESULTS, timeout: float = DEFAULT_TIMEOUT
) -> list[dict[str, Any]]:
    if not isinstance(query, str) or not query.strip():
        raise MatlasError("input", "query must be a nonempty string")
    if type(num_results) is not int or not 10 <= num_results <= 200:
        raise MatlasError("input", "num-results must be an integer from 10 to 200")
    if (
        isinstance(timeout, bool) or not isinstance(timeout, (int, float))
        or not math.isfinite(timeout) or timeout <= 0
    ):
        raise MatlasError("input", "timeout must be a positive finite number")
    payload = json.dumps(
        {"query": query.strip(), "num_results": num_results}, ensure_ascii=False
    ).encode("utf-8")
    request = urllib.request.Request(
        SEARCH_URL, data=payload, method="POST",
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "Accept": "application/json",
            "User-Agent": "zuihan-kanshu/matlas-client",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except urllib.error.HTTPError as exc:
        raise MatlasError("http", f"HTTP {exc.code}: {exc.reason}") from exc
    except urllib.error.URLError as exc:
        kind = "timeout" if isinstance(exc.reason, TimeoutError) else "network"
        raise MatlasError(kind, str(exc.reason)) from exc
    except TimeoutError as exc:
        raise MatlasError("timeout", str(exc) or "request timed out") from exc
    except (OSError, http.client.HTTPException) as exc:
        raise MatlasError("network", str(exc)) from exc
    return decode_results(raw)


def save_results(path: Path, results: list[dict[str, Any]]) -> None:
    try:
        text = json.dumps(results, ensure_ascii=False, indent=2) + "\n"
        with path.open("x", encoding="utf-8") as stream:
            stream.write(text)
    except (OSError, UnicodeError, ValueError) as exc:
        raise MatlasError("file", f"cannot save {path}: {exc}") from exc


def load_results(path: Path) -> list[dict[str, Any]]:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise MatlasError("file", f"cannot read {path}: {exc}") from exc
    return decode_results(raw)


def compact(value: str, limit: int) -> str:
    value = " ".join(value.split())
    return value if len(value) <= limit else value[: limit - 1] + "…"


def format_preview(results: list[dict[str, Any]], limit: int = DEFAULT_PREVIEW, start: int = 1) -> str:
    if type(limit) is not int or limit < 0:
        raise MatlasError("input", "preview must be a nonnegative integer")
    if type(start) is not int or start < 1:
        raise MatlasError("input", "start must be a positive integer")
    selected = results[start - 1:start - 1 + limit]
    lines = [f"Matlas: {len(results)} result(s); previewing {len(selected)} from {start}; statements omitted."]
    for index, item in enumerate(selected, start=start):
        lines.extend([
            f"[{index}] {item['type']} | {compact(item['entity_name'], 100)}",
            "    " + compact(
                " | ".join([item["title"], item["authors"], item["year"]]), 220
            ),
            f"    DOI: {compact(item['doi'], 80)} | "
            f"candidate_id: {compact(item['candidate_id'], 80)}",
        ])
    return "\n".join(lines)


def format_statement(results: list[dict[str, Any]], index: int) -> str:
    if type(index) is not int or not 1 <= index <= len(results):
        raise MatlasError("input", f"index must be from 1 to {len(results)}")
    item = results[index - 1]
    lines = [f"[{index}] {item['entity_name']}"]
    lines.extend(f"{field}: {item[field]}" for field in RESULT_FIELDS
                 if field not in ("entity_name", "statement"))
    lines.extend(["", "statement:", item["statement"]])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    query_parser = commands.add_parser("search", help="send one query to Matlas")
    query_parser.add_argument("query")
    query_parser.add_argument("--num-results", type=int, default=DEFAULT_NUM_RESULTS,
                              help="returned candidates (default: 50; service range: 10–200)")
    query_parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT)
    query_parser.add_argument("--preview", type=int, default=DEFAULT_PREVIEW,
                              help="number of metadata rows to print (default: 10)")
    query_parser.add_argument("--output", type=Path,
                              help="save complete results to this new UTF-8 JSON file")
    preview_parser = commands.add_parser("preview", help="preview saved metadata; no request")
    preview_parser.add_argument("results", type=Path)
    preview_parser.add_argument("--limit", type=int, default=DEFAULT_PREVIEW,
                                help="number of metadata rows to print (default: 10)")
    preview_parser.add_argument("--start", type=int, default=1,
                                help="first result index to preview (1-based)")
    show_parser = commands.add_parser("show", help="read one saved statement; no request")
    show_parser.add_argument("results", type=Path)
    show_parser.add_argument("index", type=int, help="1-based index in the saved array")
    args = parser.parse_args(argv)
    try:
        if args.command == "search":
            if args.preview < 0:
                raise MatlasError("input", "preview must be a nonnegative integer")
            results = search(args.query, args.num_results, args.timeout)
            if args.output is not None:
                save_results(args.output, results)
            print(format_preview(results, args.preview))
            if args.output is not None:
                print(f"Saved complete results: {args.output}")
        elif args.command == "preview":
            print(format_preview(load_results(args.results), args.limit, args.start))
        else:
            print(format_statement(load_results(args.results), args.index))
    except MatlasError as exc:
        print(f"matlas: {exc.kind}: {exc}", file=sys.stderr)
        return 2 if exc.kind == "input" else 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
