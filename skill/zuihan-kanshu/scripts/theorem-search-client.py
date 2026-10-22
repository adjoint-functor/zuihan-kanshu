#!/usr/bin/env python3
"""Query TheoremSearch and informal TheoremGraph; read saved results locally."""

from __future__ import annotations

import argparse
import http.client
import json
import math
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


BASE_URL = "https://api.theoremsearch.com"
DEFAULT_TIMEOUT = 30.0
DEFAULT_NUM_RESULTS = 50
DEFAULT_PREVIEW = 10
SEARCH_SOURCES = (
    "arXiv", "Stacks Project", "ProofWiki", "CRing Project", "HoTT Book",
    "Open Logic Project", "An Infinitely Large Napkin",
)
COLLECTIONS = {
    "search": ("theorems",),
    "graph-search": ("results",),
    "neighbors": ("nodes", "edges"),
    "paper": ("statements", "edges"),
}


class SearchError(Exception):
    def __init__(self, kind: str, message: str):
        super().__init__(message)
        self.kind = kind


def nonempty(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SearchError("input", f"{name} must be a nonempty string")
    return value.strip()


def positive_int(value: Any, name: str, maximum: int | None = None) -> int:
    if type(value) is not int or value < 1 or (maximum is not None and value > maximum):
        bound = f" from 1 to {maximum}" if maximum is not None else " greater than zero"
        raise SearchError("input", f"{name} must be an integer{bound}")
    return value


def finite_number(value: Any, name: str, *, positive: bool = False) -> float:
    if (isinstance(value, bool) or not isinstance(value, (int, float))
            or not math.isfinite(value) or value < 0 or (positive and value == 0)):
        raise SearchError("input", f"{name} must be a finite {'positive' if positive else 'nonnegative'} number")
    return value


def decode_json(raw: bytes) -> Any:
    try:
        text = raw.decode("utf-8")
        value = json.loads(text)
        json.dumps(value, ensure_ascii=False).encode("utf-8")
        return value
    except (UnicodeError, ValueError) as exc:
        raise SearchError("response", "expected valid UTF-8 JSON") from exc


def request_json(method: str, url: str, payload: dict | None, timeout: float) -> Any:
    finite_number(timeout, "timeout", positive=True)
    data = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(url, data=data, method=method, headers={
        "Accept": "application/json", "Content-Type": "application/json; charset=utf-8",
        "User-Agent": "zuihan-kanshu/theorem-search-client",
    })
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except urllib.error.HTTPError as exc:
        raise SearchError("http", f"HTTP {exc.code}: {exc.reason}") from exc
    except urllib.error.URLError as exc:
        kind = "timeout" if isinstance(exc.reason, TimeoutError) else "network"
        raise SearchError(kind, str(exc.reason)) from exc
    except TimeoutError as exc:
        raise SearchError("timeout", str(exc) or "request timed out") from exc
    except (OSError, http.client.HTTPException) as exc:
        raise SearchError("network", str(exc)) from exc
    return decode_json(raw)


def build_request(args: argparse.Namespace) -> tuple[str, str, dict | None]:
    operation = args.command
    if operation in ("search", "graph-search"):
        query = nonempty(args.query, "query")
        count = positive_int(args.num_results, "num-results", 100 if operation == "graph-search" else None)
        weight = finite_number(args.citation_weight, "citation-weight")
        params: dict[str, Any] = {"query": query, "n_results": count, "citation_weight": weight}
        for option, key in (("source", "sources"), ("author", "authors"), ("type", "types"),
                            ("category", "tags" if operation == "search" else "categories")):
            values = getattr(args, option)
            if values:
                params[key] = [nonempty(v, option) for v in values]
        if args.paper_filter is not None:
            params["paper_filter"] = nonempty(args.paper_filter, "paper-filter")
        if operation == "search":
            if args.db_top_k is not None:
                params["db_top_k"] = positive_int(args.db_top_k, "db-top-k")
            return "POST", BASE_URL + "/search", params
        if args.source and any(source != "arXiv" for source in args.source):
            raise SearchError("input", "the informal graph currently supports the arXiv source")
        params.update(formality="informal", mode="full")
        return "GET", BASE_URL + "/graph/embedding?" + urllib.parse.urlencode(params, doseq=True), None
    if operation == "neighbors":
        statement_id = nonempty(args.statement_id, "statement-id")
        params = {"direction": args.direction, "formality": "informal", "mode": "full"}
        url = BASE_URL + "/graph/statement/" + urllib.parse.quote(statement_id, safe="")
    else:
        params = {"external_id": nonempty(args.external_id, "external-id"),
                  "sources": "arXiv", "mode": "full"}
        url = BASE_URL + "/graph/paper"
    return "GET", url + "?" + urllib.parse.urlencode(params), None


def require_object(value: Any, label: str) -> dict:
    if not isinstance(value, dict):
        raise SearchError("response", f"{label} must be an object")
    return value


def require_string(item: dict, key: str, label: str) -> None:
    if not isinstance(item.get(key), str):
        raise SearchError("response", f"{label}.{key} must be a string")


def validate_response(operation: str, value: Any) -> dict:
    require_object(value, "response")
    if operation not in COLLECTIONS:
        raise SearchError("response", "unknown saved operation")
    if operation == "neighbors":
        root = require_object(value.get("root"), "root")
        require_string(root, "statement_id", "root")
        paper = require_object(root.get("paper"), "root.paper")
        if paper.get("source") != "arXiv":
            raise SearchError("response", "expected an informal arXiv root")
    elif operation == "paper":
        paper = require_object(value.get("paper"), "paper")
        require_string(paper, "paper_id", "paper")
        if paper.get("source") != "arXiv":
            raise SearchError("response", "expected an arXiv paper")
    for collection in COLLECTIONS[operation]:
        rows = value.get(collection)
        if not isinstance(rows, list):
            raise SearchError("response", f"{collection} must be an array")
        for index, item in enumerate(rows, 1):
            label = f"{collection}[{index}]"
            require_object(item, label)
            if collection == "edges":
                require_string(item, "src_id", label)
                # An unresolved dependency can have a null/missing dep_id.
                for field in ("dep_id", "cite_id", "cite_key", "edge_type"):
                    if item.get(field) is not None:
                        require_string(item, field, label)
            elif operation == "search":
                for field in ("name", "body"):
                    require_string(item, field, label)
                paper = require_object(item.get("paper"), label + ".paper")
                for field in ("title", "source", "link"):
                    require_string(paper, field, label + ".paper")
                if paper["source"] not in SEARCH_SOURCES:
                    raise SearchError("response", f"{label}: unexpected source {paper['source']!r}")
            else:
                require_string(item, "statement_id", label)
                if operation == "graph-search" and item.get("formality") != "informal":
                    raise SearchError("response", f"{label}: expected informal full metadata")
                if item.get("formality") not in (None, "informal"):
                    raise SearchError("response", f"{label}: unexpected formality")
    return value  # Keep every returned field, including extraction annotations.


def run_query(args: argparse.Namespace) -> dict:
    method, url, payload = build_request(args)
    response = validate_response(args.command, request_json(method, url, payload, args.timeout))
    return {"operation": args.command, "request": {"method": method, "url": url, "json": payload},
            "response": response}


def save_result(path: Path, result: dict) -> None:
    try:
        text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
        with path.open("x", encoding="utf-8") as stream:
            stream.write(text)
    except (OSError, UnicodeError, ValueError) as exc:
        raise SearchError("file", f"cannot save {path}: {exc}") from exc


def load_result(path: Path) -> dict:
    try:
        value = decode_json(path.read_bytes())
    except OSError as exc:
        raise SearchError("file", f"cannot read {path}: {exc}") from exc
    require_object(value, "saved result")
    operation = value.get("operation")
    if not isinstance(operation, str) or operation not in COLLECTIONS:
        raise SearchError("response", "unknown saved operation")
    require_object(value.get("request"), "request")
    validate_response(operation, value.get("response"))
    return value


def compact(value: Any, limit: int = 180) -> str:
    text = " ".join(str(value if value is not None else "").split())
    return text if len(text) <= limit else text[:limit - 1] + "…"


def select_section(result: dict, section: str | None) -> tuple[str, Any]:
    section = section or COLLECTIONS[result["operation"]][0]
    if section not in result["response"]:
        raise SearchError("input", f"section {section!r} is not present")
    return section, result["response"][section]


def format_preview(result: dict, limit: int = DEFAULT_PREVIEW, start: int = 1,
                   section: str | None = None) -> str:
    positive_int(start, "start")
    if type(limit) is not int or limit < 0:
        raise SearchError("input", "limit must be a nonnegative integer")
    section, rows = select_section(result, section)
    if not isinstance(rows, list):
        raise SearchError("input", "preview needs an array section; use show for root or paper")
    selected = rows[start - 1:start - 1 + limit]
    lines = [f"TheoremSearch {result['operation']}: {len(rows)} {section}; "
             f"showing {len(selected)} from {start}; bodies and summaries omitted."]
    if result["operation"] in ("neighbors", "paper"):
        lines.append("Graph edges are extracted candidates: src_id uses dep_id; unresolved targets stay unresolved.")
        lines.append(f"Saved sections: {', '.join(result['response'])}")
    for index, item in enumerate(selected, start):
        if section == "edges":
            target = item.get("dep_id") or item.get("cite_id") or item.get("cite_key") or "[unresolved]"
            lines.append(f"[{index}] {compact(item.get('src_id'), 80)} uses {compact(target, 100)}")
            annotations = {key: item[key] for key in ("edge_type", "methods", "location") if key in item}
            if annotations:
                lines.append("    " + compact(json.dumps(annotations, ensure_ascii=False), 220))
            continue
        paper = item.get("paper") or result["response"].get("paper") or {}
        title = item.get("title") or paper.get("title")
        source = item.get("source") or paper.get("source")
        identifier = item.get("statement_id", item.get("theorem_id", ""))
        link = item.get("link") or item.get("url") or paper.get("link") or paper.get("url")
        lines.append(f"[{index}] {compact(item.get('name'), 100)} | id={compact(identifier, 80)}")
        if title or source:
            lines.append("    " + compact(f"{source or ''} | {title or ''}", 220))
        if link:
            lines.append("    " + compact(link, 250))
    return "\n".join(lines)


def format_detail(result: dict, index: int = 1, section: str | None = None) -> str:
    section, value = select_section(result, section)
    if isinstance(value, list):
        positive_int(index, "index")
        if index > len(value):
            raise SearchError("input", f"index must be from 1 to {len(value)}")
        value = value[index - 1]
    elif index != 1:
        raise SearchError("input", "root and paper have no row index")
    return json.dumps(value, ensure_ascii=False, indent=2)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in COLLECTIONS:
        sub = commands.add_parser(name)
        if name in ("search", "graph-search"):
            sub.add_argument("query")
            sub.add_argument("--num-results", type=int, default=DEFAULT_NUM_RESULTS,
                             help="returned candidates (default: 50; graph maximum: 100)")
            sub.add_argument("--source", action="append", choices=SEARCH_SOURCES)
            sub.add_argument("--author", action="append")
            sub.add_argument("--type", action="append")
            sub.add_argument("--category", action="append")
            sub.add_argument("--paper-filter")
            sub.add_argument("--citation-weight", type=float, default=0.0)
            if name == "search":
                sub.add_argument("--db-top-k", type=int)
        elif name == "neighbors":
            sub.add_argument("statement_id")
            sub.add_argument("--direction", choices=("src", "dep", "both"), default="src",
                             help="src: what this uses; dep: what uses this; both: union")
        else:
            sub.add_argument("external_id", help="arXiv identifier from a returned paper")
        sub.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT)
        sub.add_argument("--preview", type=int, default=DEFAULT_PREVIEW)
        sub.add_argument("--output", type=Path, help="save the full response and request; never overwrite")
    preview = commands.add_parser("preview", help="read saved metadata without networking")
    preview.add_argument("result", type=Path)
    preview.add_argument("--start", type=int, default=1)
    preview.add_argument("--limit", type=int, default=DEFAULT_PREVIEW)
    preview.add_argument("--section", choices=("theorems", "results", "statements", "nodes", "edges"))
    show = commands.add_parser("show", help="read one saved item without networking")
    show.add_argument("result", type=Path)
    show.add_argument("index", nargs="?", type=int, default=1)
    show.add_argument("--section", choices=("theorems", "results", "statements", "nodes", "edges", "root", "paper"))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "preview":
            print(format_preview(load_result(args.result), args.limit, args.start, args.section))
        elif args.command == "show":
            print(format_detail(load_result(args.result), args.index, args.section))
        else:
            if args.preview < 0:
                raise SearchError("input", "preview must be nonnegative")
            if args.output is not None and args.output.exists():
                raise SearchError("file", f"output already exists: {args.output}")
            result = run_query(args)
            if args.output is not None:
                save_result(args.output, result)
            print(format_preview(result, args.preview))
            if args.output is not None:
                print(f"Saved complete result: {args.output}")
    except SearchError as exc:
        print(f"theorem-search: {exc.kind}: {exc}", file=sys.stderr)
        return 2 if exc.kind == "input" else 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
