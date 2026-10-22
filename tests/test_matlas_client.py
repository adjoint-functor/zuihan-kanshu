#!/usr/bin/env python3
"""Contract and CLI tests for the public Matlas search adapter."""

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
from unittest import mock


REPOSITORY_ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = REPOSITORY_ROOT / "skill" / "zuihan-kanshu" / "scripts" / "matlas-client.py"
SPEC = importlib.util.spec_from_file_location("matlas_client", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
matlas = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(matlas)


def result(**overrides):
    item = {
        "type": "paper", "entity_name": "Theorem 2.1", "doi": "10.example/compact",
        "title": "紧致性与极值", "authors": "Émilie 数学家", "journal": "Example Journal",
        "year": "2020", "statement": "设 X 紧致，f ∈ C(X, ℝ)，则 f 取到极值。",
        "candidate_id": "candidate-α",
    }
    item.update(overrides)
    return item


def response_with(value):
    response = mock.MagicMock()
    response.__enter__.return_value.read.return_value = json.dumps(
        value, ensure_ascii=False
    ).encode("utf-8")
    return response


class MatlasClientTests(unittest.TestCase):
    def test_search_uses_current_payload_and_preserves_paper_and_book_fields(self):
        items = [result(), result(type="book", journal="", candidate_id="book-2", extra="kept")]
        with mock.patch.object(matlas.urllib.request, "urlopen", return_value=response_with(items)) as opener:
            actual = matlas.search("  紧致空间的连续像  ", num_results=20, timeout=12.5)
        self.assertEqual(items, actual)
        self.assertEqual(set(matlas.RESULT_FIELDS), set(actual[0]))
        self.assertIsInstance(actual[0]["year"], str)
        opener.assert_called_once()
        request = opener.call_args.args[0]
        self.assertEqual("https://matlas.ai/api/search", request.full_url)
        self.assertEqual("POST", request.get_method())
        self.assertEqual({"query": "紧致空间的连续像", "num_results": 20},
                         json.loads(request.data.decode("utf-8")))
        self.assertIn("紧致空间".encode("utf-8"), request.data)
        self.assertEqual({"timeout": 12.5}, opener.call_args.kwargs)
        self.assertEqual("application/json", request.get_header("Accept"))

    def test_empty_results_are_successful(self):
        with mock.patch.object(matlas.urllib.request, "urlopen", return_value=response_with([])) as opener:
            self.assertEqual([], matlas.search("compact image"))
        self.assertEqual(50, json.loads(opener.call_args.args[0].data)["num_results"])
        with mock.patch.object(matlas, "search", return_value=[]), contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(0, matlas.main(["search", "compact image"]))
        self.assertIn("0 result(s)", out.getvalue())

    def test_invalid_search_inputs_do_not_make_a_request(self):
        cases = [
            ("  ", 10, 30), (None, 10, 30), ("x", 9, 30), ("x", 201, 30),
            ("x", True, 30), ("x", 10, 0), ("x", 10, float("nan")),
            ("x", 10, float("inf")), ("x", 10, True),
        ]
        with mock.patch.object(matlas.urllib.request, "urlopen") as opener:
            for query, count, timeout in cases:
                with self.subTest(query=query, count=count, timeout=timeout):
                    with self.assertRaises(matlas.MatlasError) as raised:
                        matlas.search(query, count, timeout)
                    self.assertEqual("input", raised.exception.kind)
        opener.assert_not_called()

    def test_response_schema_is_checked_without_silently_dropping_bad_rows(self):
        missing = result()
        del missing["candidate_id"]
        cases = [
            {}, [None], [missing], [result(authors=["A"])],
            [result(year=2020)], [result(type="thesis")], [result(statement="\ud800")],
            [result(), result(doi=None)],
        ]
        for value in cases:
            with self.subTest(value=repr(value)):
                with self.assertRaises(matlas.MatlasError) as raised:
                    matlas.validate_results(value)
                self.assertEqual("response", raised.exception.kind)

    def test_bad_utf8_and_json_are_response_failures(self):
        for raw in (b"\xff", b"<html>unavailable</html>"):
            with self.subTest(raw=raw):
                response = mock.MagicMock()
                response.__enter__.return_value.read.return_value = raw
                with mock.patch.object(matlas.urllib.request, "urlopen", return_value=response):
                    with self.assertRaises(matlas.MatlasError) as raised:
                        matlas.search("compact image")
                self.assertEqual("response", raised.exception.kind)

    def test_http_network_and_timeout_failures_are_distinct_and_not_retried(self):
        failures = [
            (urllib.error.HTTPError(matlas.SEARCH_URL, 503, "Unavailable", None, None), "http"),
            (urllib.error.URLError("name resolution failed"), "network"),
            (TimeoutError("timed out"), "timeout"),
            (urllib.error.URLError(TimeoutError("timed out")), "timeout"),
        ]
        for failure, kind in failures:
            with self.subTest(kind=kind, failure=type(failure).__name__):
                with mock.patch.object(matlas.urllib.request, "urlopen", side_effect=failure) as opener:
                    with self.assertRaises(matlas.MatlasError) as raised:
                        matlas.search("compact image")
                self.assertEqual(kind, raised.exception.kind)
                opener.assert_called_once()
                if kind == "http":
                    self.assertIn("503", str(raised.exception))

    def test_default_preview_is_bounded_and_omits_statements(self):
        items = [result(entity_name=f"Entity {index}", statement=f"private-body-{index}")
                 for index in range(1, 51)]
        preview = matlas.format_preview(items)
        self.assertIn("50 result(s); previewing 10", preview)
        self.assertIn("[10]", preview)
        self.assertNotIn("[11]", preview)
        self.assertNotIn("private-body", preview)
        self.assertNotIn("Entity 1", matlas.format_preview(items, 0))
        long_item = result(title="t" * 5000)
        self.assertLess(len(matlas.format_preview([long_item])), 500)

    def test_interrupted_http_body_is_not_saved_or_reported_as_empty_success(self):
        response = mock.MagicMock()
        response.__enter__.return_value.read.side_effect = http.client.IncompleteRead(
            b'[{"type":"book"', 10
        )
        with tempfile.TemporaryDirectory() as temporary:
            path = pathlib.Path(temporary) / "results.json"
            with mock.patch.object(matlas.urllib.request, "urlopen", return_value=response) as opener, \
                    contextlib.redirect_stderr(io.StringIO()) as err, \
                    contextlib.redirect_stdout(io.StringIO()) as out:
                self.assertEqual(1, matlas.main([
                    "search", "compact image", "--output", str(path)
                ]))
            self.assertIn("matlas: network:", err.getvalue())
            self.assertEqual("", out.getvalue())
            self.assertFalse(path.exists())
            opener.assert_called_once()

    def test_complete_unicode_results_are_saved_only_to_explicit_path(self):
        items = [result(), result(type="book", statement="第二条完整陈述", extra="完整保留")]
        with tempfile.TemporaryDirectory() as temporary:
            path = pathlib.Path(temporary) / "检索.json"
            with mock.patch.object(matlas, "search", return_value=items), contextlib.redirect_stdout(io.StringIO()) as out:
                self.assertEqual(0, matlas.main(["search", "compact image", "--output", str(path)]))
            self.assertEqual(items, json.loads(path.read_text(encoding="utf-8")))
            self.assertIn("第二条完整陈述", path.read_text(encoding="utf-8"))
            self.assertNotIn("第二条完整陈述", out.getvalue())
            with mock.patch.object(matlas, "search", return_value=items), \
                    mock.patch.object(matlas, "save_results") as save, \
                    contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(0, matlas.main(["search", "compact image"]))
            save.assert_not_called()

    def test_show_reads_only_the_selected_statement_without_network(self):
        items = [result(statement="不应显示第一条"), result(statement="应显示第二条\nα ≤ β")]
        with tempfile.TemporaryDirectory() as temporary:
            path = pathlib.Path(temporary) / "results.json"
            matlas.save_results(path, items)
            with mock.patch.object(matlas.urllib.request, "urlopen") as opener, \
                    contextlib.redirect_stdout(io.StringIO()) as out:
                self.assertEqual(0, matlas.main(["show", str(path), "2"]))
            self.assertIn("应显示第二条\nα ≤ β", out.getvalue())
            self.assertNotIn("不应显示第一条", out.getvalue())
            self.assertIn("candidate_id: candidate-α", out.getvalue())
            opener.assert_not_called()
        for index in (0, 3):
            with self.assertRaises(matlas.MatlasError) as raised:
                matlas.format_statement(items, index)
            self.assertEqual("input", raised.exception.kind)

    def test_saved_preview_can_expand_metadata_without_network(self):
        items = [result(entity_name=f"Entity {index}", statement=f"body-{index}")
                 for index in range(1, 51)]
        with tempfile.TemporaryDirectory() as temporary:
            path = pathlib.Path(temporary) / "results.json"
            matlas.save_results(path, items)
            with mock.patch.object(matlas.urllib.request, "urlopen") as opener, \
                    contextlib.redirect_stdout(io.StringIO()) as out:
                self.assertEqual(0, matlas.main(["preview", str(path), "--start", "11", "--limit", "10"]))
            self.assertIn("50 result(s); previewing 10 from 11", out.getvalue())
            self.assertIn("[11]", out.getvalue())
            self.assertIn("[20]", out.getvalue())
            self.assertNotIn("[10]", out.getvalue())
            self.assertNotIn("[21]", out.getvalue())
            self.assertNotIn("body-", out.getvalue())
            opener.assert_not_called()
            with mock.patch.object(matlas.urllib.request, "urlopen") as opener, \
                    contextlib.redirect_stdout(io.StringIO()) as out:
                self.assertEqual(0, matlas.main(["show", str(path), "20"]))
            self.assertIn("body-20", out.getvalue())
            self.assertNotIn("body-19", out.getvalue())
            opener.assert_not_called()

    def test_existing_output_is_not_overwritten_and_file_errors_are_classified(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = pathlib.Path(temporary) / "results.json"
            path.write_text("existing content", encoding="utf-8")
            with self.assertRaises(matlas.MatlasError) as raised:
                matlas.save_results(path, [result()])
            self.assertEqual("file", raised.exception.kind)
            self.assertEqual("existing content", path.read_text(encoding="utf-8"))
            with self.assertRaises(matlas.MatlasError) as raised:
                matlas.load_results(path.with_name("missing.json"))
            self.assertEqual("file", raised.exception.kind)

    def test_cli_failures_are_nonzero_and_keep_the_category(self):
        for kind in ("http", "network", "timeout", "response"):
            with self.subTest(kind=kind):
                with mock.patch.object(matlas, "search", side_effect=matlas.MatlasError(kind, "failure")), \
                        contextlib.redirect_stderr(io.StringIO()) as err, \
                        contextlib.redirect_stdout(io.StringIO()) as out:
                    self.assertEqual(1, matlas.main(["search", "compact image"]))
                self.assertIn(f"matlas: {kind}:", err.getvalue())
                self.assertEqual("", out.getvalue())


if __name__ == "__main__":
    unittest.main()
