#!/usr/bin/env python3
"""Offline contracts for the informal TheoremSearch / TheoremGraph adapter."""

from __future__ import annotations

import contextlib
import http.client
import importlib.util
import io
import json
import pathlib
import tempfile
import unittest
import urllib.error
import urllib.parse
from unittest import mock


ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "theorem_search", ROOT / "skill/zuihan-kanshu/scripts/theorem-search-client.py"
)
assert SPEC is not None and SPEC.loader is not None
client = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(client)


def paper():
    return {"paper_id": "paper-uuid", "source": "arXiv", "title": "Example paper",
            "link": "https://arxiv.org/abs/example", "extra": "preserved"}


def statement(index=1):
    return {"statement_id": f"statement-{index}", "name": f"Theorem {index}",
            "formality": "informal", "body": f"正文-{index}", "slogan": "自动摘要",
            "source": "arXiv", "title": "Example paper"}


def search_response(count=1):
    return {"theorems": [{"theorem_id": i, "name": f"Theorem {i}", "body": f"正文-{i}",
                          "paper": paper(), "extra": "kept"} for i in range(1, count + 1)]}


def graph_response(operation):
    edges = [
        {"src_id": "statement-1", "dep_id": "statement-2", "methods": ["heuristic"],
         "location": "pre_context", "extra": "kept"},
        {"src_id": "statement-1", "dep_id": None, "cite_id": "citation-3", "cite_key": "Ref3"},
    ]
    if operation == "graph-search":
        return {"results": [statement()]}
    if operation == "neighbors":
        return {"root": {"statement_id": "statement-1", "statement": statement(), "paper": paper()},
                "nodes": [statement(2)], "edges": edges}
    return {"paper": paper(), "statements": [statement(), statement(2)], "edges": edges}


def http_response(value):
    response = mock.MagicMock()
    response.__enter__.return_value.read.return_value = json.dumps(value, ensure_ascii=False).encode("utf-8")
    return response


class TheoremSearchClientTests(unittest.TestCase):
    def test_search_post_uses_current_fields_and_default_breadth(self):
        args = client.build_parser().parse_args([
            "search", "  紧致空间的连续像  ", "--source", "arXiv", "--source", "Stacks Project",
            "--category", "math.GN", "--author", "A", "--type", "theorem", "--db-top-k", "120",
            "--paper-filter", "Example", "--timeout", "12.5",
        ])
        response = search_response()
        with mock.patch.object(client.urllib.request, "urlopen", return_value=http_response(response)) as opener:
            result = client.run_query(args)
        request = opener.call_args.args[0]
        self.assertEqual("https://api.theoremsearch.com/search", request.full_url)
        self.assertEqual("POST", request.get_method())
        self.assertEqual({"query": "紧致空间的连续像", "n_results": 50, "citation_weight": 0.0,
                          "sources": ["arXiv", "Stacks Project"], "authors": ["A"],
                          "types": ["theorem"], "tags": ["math.GN"], "db_top_k": 120,
                          "paper_filter": "Example"}, json.loads(request.data))
        self.assertEqual({"timeout": 12.5}, opener.call_args.kwargs)
        self.assertEqual(response, result["response"])
        self.assertEqual(json.loads(request.data), result["request"]["json"])

    def test_graph_requests_force_informal_full_and_repeat_filters(self):
        args = client.build_parser().parse_args([
            "graph-search", "α ≤ β", "--author", "A", "--author", "B", "--category", "math.CO",
            "--category", "math.PR", "--paper-filter", "Example & title", "--num-results", "100",
        ])
        with mock.patch.object(client.urllib.request, "urlopen", return_value=http_response(graph_response("graph-search"))) as opener:
            client.run_query(args)
        request = opener.call_args.args[0]
        query = urllib.parse.parse_qs(urllib.parse.urlparse(request.full_url).query)
        self.assertEqual("GET", request.get_method())
        self.assertIsNone(request.data)
        self.assertEqual(["informal"], query["formality"])
        self.assertEqual(["full"], query["mode"])
        self.assertEqual(["A", "B"], query["authors"])
        self.assertEqual(["math.CO", "math.PR"], query["categories"])
        self.assertEqual(["Example & title"], query["paper_filter"])
        self.assertEqual(["α ≤ β"], query["query"])

    def test_neighbors_direction_and_paper_source_are_not_ambiguous(self):
        for direction in (None, "src", "dep", "both"):
            argv = ["neighbors", "root-id"] + ([] if direction is None else ["--direction", direction])
            method, url, payload = client.build_request(client.build_parser().parse_args(argv))
            query = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
            self.assertIn("/graph/statement/root-id?", url)
            self.assertEqual([direction or "src"], query["direction"])
            self.assertEqual(["informal"], query["formality"])
            self.assertEqual(("GET", None), (method, payload))
        _, url, _ = client.build_request(client.build_parser().parse_args(["paper", "math/1234567v2"]))
        query = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
        self.assertEqual(["math/1234567v2"], query["external_id"])
        self.assertEqual(["arXiv"], query["sources"])
        self.assertEqual(["full"], query["mode"])

    def test_invalid_inputs_are_rejected_before_network(self):
        cases = [["search", "  "], ["search", "x", "--num-results", "0"],
                 ["graph-search", "x", "--num-results", "101"],
                 ["graph-search", "x", "--source", "Stacks Project"],
                 ["search", "x", "--citation-weight", "nan"],
                 ["search", "x", "--timeout", "0"], ["search", "x", "--db-top-k", "0"]]
        with mock.patch.object(client.urllib.request, "urlopen") as opener:
            for argv in cases:
                with self.subTest(argv=argv), contextlib.redirect_stderr(io.StringIO()):
                    self.assertEqual(2, client.main(argv))
        opener.assert_not_called()

    def test_schema_failures_are_not_empty_success_or_silently_filtered(self):
        cases = [("search", {}), ("search", {"theorems": [None]}),
                 ("search", {"theorems": [{"name": "X", "body": "Y", "paper": {}}]}),
                 ("neighbors", {"root": None, "nodes": [], "edges": []})]
        formal = graph_response("graph-search")
        formal["results"][0]["formality"] = "formal"
        cases.append(("graph-search", formal))
        invalid_edge = graph_response("paper")
        invalid_edge["edges"][0]["src_id"] = None
        cases.append(("paper", invalid_edge))
        for operation, response in cases:
            with self.subTest(operation=operation), self.assertRaises(client.SearchError) as caught:
                client.validate_response(operation, response)
            self.assertEqual("response", caught.exception.kind)
        self.assertEqual({"theorems": []}, client.validate_response("search", {"theorems": []}))
        self.assertEqual({"results": []}, client.validate_response("graph-search", {"results": []}))

    def test_saved_graph_keeps_unresolved_edges_and_extraction_annotations(self):
        for operation in ("neighbors", "paper"):
            response = graph_response(operation)
            result = {"operation": operation, "request": {}, "response": response}
            with tempfile.TemporaryDirectory() as directory:
                file = pathlib.Path(directory) / "graph.json"
                client.save_result(file, result)
                loaded = client.load_result(file)
            self.assertEqual(result, loaded)
            preview = client.format_preview(loaded, section="edges")
            self.assertIn("statement-1 uses statement-2", preview)
            self.assertIn("statement-1 uses citation-3", preview)
            self.assertIn("heuristic", preview)
            self.assertIn("pre_context", preview)
            self.assertNotIn("edge_type", response["edges"][0])

    def test_default_preview_and_paging_do_not_limit_saved_candidates(self):
        with tempfile.TemporaryDirectory() as directory:
            file = pathlib.Path(directory) / "search.json"
            with mock.patch.object(client.urllib.request, "urlopen", return_value=http_response(search_response(50))), \
                    contextlib.redirect_stdout(io.StringIO()) as out:
                self.assertEqual(0, client.main(["search", "x", "--output", str(file)]))
            self.assertIn("50 theorems; showing 10", out.getvalue())
            self.assertIn("[10]", out.getvalue())
            self.assertNotIn("[11]", out.getvalue())
            self.assertNotIn("正文", out.getvalue())
            self.assertEqual(50, len(client.load_result(file)["response"]["theorems"]))
            with mock.patch.object(client.urllib.request, "urlopen") as opener, contextlib.redirect_stdout(io.StringIO()) as out:
                self.assertEqual(0, client.main(["preview", str(file), "--start", "11", "--limit", "10"]))
            opener.assert_not_called()
            self.assertIn("[11]", out.getvalue())
            self.assertIn("[20]", out.getvalue())
            self.assertNotIn("[10]", out.getvalue())
            with mock.patch.object(client.urllib.request, "urlopen") as opener, contextlib.redirect_stdout(io.StringIO()) as out:
                self.assertEqual(0, client.main(["show", str(file), "20"]))
            opener.assert_not_called()
            self.assertIn("正文-20", out.getvalue())
            self.assertNotIn("正文-19", out.getvalue())

    def test_show_can_read_root_or_one_edge_without_network(self):
        result = {"operation": "neighbors", "request": {}, "response": graph_response("neighbors")}
        with tempfile.TemporaryDirectory() as directory:
            file = pathlib.Path(directory) / "graph.json"
            client.save_result(file, result)
            for section, expected in (("root", result["response"]["root"]), ("edges", result["response"]["edges"][0])):
                with mock.patch.object(client.urllib.request, "urlopen") as opener, contextlib.redirect_stdout(io.StringIO()) as out:
                    self.assertEqual(0, client.main(["show", str(file), "--section", section]))
                self.assertEqual(expected, json.loads(out.getvalue()))
                opener.assert_not_called()

    def test_existing_output_is_not_overwritten_or_queried(self):
        with tempfile.TemporaryDirectory() as directory:
            file = pathlib.Path(directory) / "saved.json"
            file.write_text("existing", encoding="utf-8")
            with mock.patch.object(client.urllib.request, "urlopen") as opener, contextlib.redirect_stderr(io.StringIO()) as err:
                self.assertEqual(1, client.main(["search", "x", "--output", str(file)]))
            self.assertIn("file:", err.getvalue())
            self.assertEqual("existing", file.read_text(encoding="utf-8"))
            opener.assert_not_called()

    def test_failed_requests_do_not_save_empty_success_or_retry(self):
        failures = [(urllib.error.HTTPError(client.BASE_URL, 503, "Unavailable", None, None), "http"),
                    (urllib.error.URLError("unavailable"), "network"), (TimeoutError("timeout"), "timeout"),
                    (http.client.IncompleteRead(b"{", 4), "network")]
        with tempfile.TemporaryDirectory() as directory:
            file = pathlib.Path(directory) / "failed.json"
            for failure, kind in failures:
                with self.subTest(kind=kind), mock.patch.object(client.urllib.request, "urlopen", side_effect=failure) as opener, \
                        contextlib.redirect_stdout(io.StringIO()) as out, contextlib.redirect_stderr(io.StringIO()) as err:
                    self.assertEqual(1, client.main(["search", "x", "--output", str(file)]))
                self.assertEqual("", out.getvalue())
                self.assertIn(f"theorem-search: {kind}:", err.getvalue())
                self.assertFalse(file.exists())
                opener.assert_called_once()

    def test_invalid_utf8_or_non_json_is_a_response_error(self):
        for raw in (b"\xff", b"<html>unavailable</html>", b'{"x":"\\ud800"}'):
            with self.subTest(raw=raw), self.assertRaises(client.SearchError) as caught:
                client.decode_json(raw)
            self.assertEqual("response", caught.exception.kind)


if __name__ == "__main__":
    unittest.main()
