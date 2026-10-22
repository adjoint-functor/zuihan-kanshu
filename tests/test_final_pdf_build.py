#!/usr/bin/env python3
"""Tests for the closed final PDF build profile."""

from __future__ import annotations

import argparse
import base64
import importlib.util
import json
import os
import pathlib
import re
import runpy
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


REPOSITORY_ROOT = pathlib.Path(__file__).resolve().parents[1]
ROOT = REPOSITORY_ROOT / "skill" / "zuihan-kanshu"
BUILDER = ROOT / "scripts" / "final-pdf-build.py"
PREFLIGHT = ROOT / "scripts" / "preflight-pdf.py"
DERIVE = ROOT / "scripts" / "derive-clean-reader-view.py"
BUILD_COMMANDS = ("pandoc", "latexmk", "xelatex", "pdffonts", "fc-match")
YAML_AVAILABLE = importlib.util.find_spec("yaml") is not None
INSPECT_AVAILABLE = YAML_AVAILABLE and all(shutil.which(command) for command in ("pandoc", "fc-match"))


def profile_yaml(*, extra: str = "", figures: str = "[]") -> str:
    return f"""build_profile:
  schema: final-pdf-build/v1
  profile: zh-math-xelatex/v1
  engine: xelatex
  fonts:
    latin_main: DejaVu Sans
    cjk_main: DejaVu Sans
    math_main: Latin Modern Math
  layout:
    paper: a4
    margins:
      top: 25mm
      right: 25mm
      bottom: 25mm
      left: 25mm
  resources:
    figures: {figures}
    bibliography: null
  document:
    class: article
    fontsize: 11pt
    toc: false
    number_sections: true
  typography:
    mathbb_uppercase: ams-msbm
    mathbb_nonuppercase: explicit-only
{extra}"""


def control_text(*, profile: str | None = None, narrative: str = "Control record.") -> str:
    return (
        f"# 文稿控制\n\n{narrative}\n\n"
        "<!-- BEGIN:BUILD_PROFILE -->\n```yaml\n"
        + (profile if profile is not None else profile_yaml())
        + "\n```\n<!-- END:BUILD_PROFILE -->\n"
    )


class FinalPdfBuildTests(unittest.TestCase):
    def test_cjk_font_channels_select_available_families_and_reach_pandoc(self):
        builder = runpy.run_path(str(BUILDER))
        validate = builder["validate_fonts"]
        profile = {"fonts": {"latin_main": "Latin", "math_main": "Math", "cjk_main": "Body"},
                   "layout": {"paper": "a4", "margins": {}},
                   "document": {"class": "article", "fontsize": "11pt", "toc": False, "number_sections": False}}
        available = {"Latin", "Math", "Body", "Source Han Sans SC", "Noto Sans Mono CJK SC"}
        issues = []
        with mock.patch.dict(validate.__globals__, font_available=lambda family: family in available):
            validate(profile, "中文", issues)
        self.assertFalse(issues)
        self.assertEqual("Source Han Sans SC", profile["fonts"]["cjk_sans"])
        command = builder["pandoc_command"](pathlib.Path("body.md"), pathlib.Path("out.tex"), profile,
                    {"root": pathlib.Path("."), "figures": [], "bibliography": None}, "中文")
        self.assertIn("CJKsansfont:Source Han Sans SC", command)
        self.assertIn("CJKmonofont:Noto Sans Mono CJK SC", command)

    def test_cjk_font_metadata_is_preserved_and_conflicts_are_reported(self):
        builder = runpy.run_path(str(BUILDER))
        validate = builder["validate_fonts"]
        profile = {"fonts": {"latin_main": "Latin", "math_main": "Math", "cjk_main": "Body"}}
        issues = []
        with mock.patch.dict(validate.__globals__, font_available=lambda family: True):
            validate(profile, "中文", issues, {"cjk_sans": "Document Sans", "cjk_mono": "Document Mono"})
            self.assertFalse(issues)
            self.assertEqual("Document Sans", profile["fonts"]["cjk_sans"])
            validate(profile, "中文", issues, {"cjk_sans": "Other Sans"})
        self.assertTrue(any("conflicting font choices" in issue.message for issue in issues))

    def test_missing_cjk_mono_is_an_error_without_serif_substitution(self):
        builder = runpy.run_path(str(BUILDER))
        validate = builder["validate_fonts"]
        profile = {"fonts": {"latin_main": "Latin", "math_main": "Math", "cjk_main": "Body", "cjk_sans": "Sans"}}
        issues = []
        with mock.patch.dict(validate.__globals__, font_available=lambda family: family != "Noto Sans Mono CJK SC"):
            validate(profile, "中文", issues)
        self.assertEqual(1, len(issues))
        self.assertEqual("ERROR", issues[0].severity)
        self.assertIn("cjk_mono", issues[0].message)
        self.assertNotIn("cjk_mono", profile["fonts"])

    def test_non_cjk_document_does_not_require_cjk_channels(self):
        builder = runpy.run_path(str(BUILDER))
        validate = builder["validate_fonts"]
        issues = []
        with mock.patch.dict(validate.__globals__, font_available=lambda family: family in {"Latin", "Math"}):
            validate({"fonts": {"latin_main": "Latin", "math_main": "Math", "cjk_main": "Missing"}}, "English", issues)
        self.assertFalse(issues)

    @unittest.skipUnless(YAML_AVAILABLE, "PyYAML required")
    def test_profile_accepts_optional_cjk_channels_but_rejects_unknown_keys(self):
        builder = runpy.run_path(str(BUILDER))
        configured = profile_yaml().replace("    math_main:", "    cjk_sans: Chosen Sans\n    cjk_mono: Chosen Mono\n    math_main:")
        issues = []
        parsed = builder["parse_profile"](control_text(profile=configured), issues)
        self.assertFalse(issues)
        self.assertEqual("Chosen Mono", parsed["fonts"]["cjk_mono"])
        builder["parse_profile"](control_text(profile=configured.replace("cjk_mono:", "cjk_monospace:")), issues)
        self.assertTrue(any("unknown keys" in issue.message for issue in issues))

    def test_preflight_captures_wrapped_xecjk_and_other_final_warnings(self):
        preflight = runpy.run_path(str(PREFLIGHT))
        with tempfile.TemporaryDirectory() as directory:
            log = pathlib.Path(directory) / "build.log"
            warning = "Package xeCJK Warning: Unknown CJK family `\\CJKsfdefault'\n(xeCJK)                is being ignored.\n\n"
            final = warning * 2 + "Package xeCJK Warning: Unknown CJK family `\\CJKttdefault' is being ignored.\n\n"
            final += "LaTeX Font Warning: Font shape unavailable.\n\nClass article Warning: Example class warning.\n\nPackage hyperref Info: Normal diagnostic.\n"
            log.write_text("Package old Warning: Resolved.\n\n[final-pdf-build] Final XeLaTeX log\n" + final, encoding="utf-8")
            issues = []
            preflight["inspect_build_log"](log, issues)
            self.assertEqual(4, len(issues))
            self.assertTrue(all(issue.severity == "WARN" for issue in issues))
            self.assertIn("is being ignored.", issues[0].message)
            self.assertFalse(any("Resolved" in issue.message or "Info:" in issue.message for issue in issues))

    def run_builder(self, *arguments: str, cwd: pathlib.Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(BUILDER), *arguments],
            cwd=cwd,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

    def make_body_control(self, root: pathlib.Path, body: str, *, profile: str | None = None):
        temporary = root / "tmp"
        temporary.mkdir(exist_ok=True)
        source = temporary / "finished_v1.0.1.md"
        source.write_text(body, encoding="utf-8", newline="")
        control = temporary / "finished_v1.0.1.control.md"
        control.write_text(control_text(profile=profile), encoding="utf-8")
        return source, control

    def run_derive(self, *arguments: str, cwd: pathlib.Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(DERIVE), *arguments], cwd=cwd, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
        )

    def test_current_body_is_preserved_with_all_mathematical_dependencies(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            source, reader, report = (root / name for name in ("body.md", "reader.md", "reader.json"))
            original = (
                "# Mathematics in engineering\n\n"
                "\\newcommand{\\Field}{\\mathbb{Q}}\n\n"
                "The field is $\\Field$. See \\eqref{eq:identity} and [details](#details).[^note]\n\n"
                "## Details {#details}\n\n"
                "\\begin{equation}\\label{eq:identity}x=x\\end{equation}\n\n"
                "[^note]: A mathematical explanation needed by the reader.\n\n \t\n"
            ).replace("\n", "\r\n").encode("utf-8")
            source.write_bytes(original)
            result = self.run_derive(str(source), str(reader), "--json-report", str(report), cwd=root)
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            self.assertEqual(original, source.read_bytes())
            self.assertEqual(original, reader.read_bytes())
            payload = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual("clean-body", payload["input_format"])
            self.assertEqual("PASS", payload["math_delimiters"])
            self.assertEqual(1, payload["latex_label_count"])
            self.assertEqual(1, payload["latex_reference_count"])
            self.assertEqual(1, payload["markdown_footnote_count"])

    def test_current_body_validation_keeps_formula_and_reference_checks(self):
        cases = {
            "unclosed formula": ("Text $x=1.\n", "unclosed math delimiter"),
            "missing label": ("Text \\eqref{missing}.\n", "unresolved LaTeX references"),
            "duplicate label": ("\\label{same}\n\\label{same}\n", "duplicate LaTeX labels"),
            "missing anchor": ("See [details](#missing).\n", "unresolved Markdown anchors"),
            "missing footnote": ("Text.[^missing]\n", "unresolved Markdown footnotes"),
        }
        for label, (body, expected) in cases.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory() as directory:
                root = pathlib.Path(directory)
                source, reader, report = (root / name for name in ("body.md", "reader.md", "reader.json"))
                source.write_text(body, encoding="utf-8")
                original = source.read_bytes()
                result = self.run_derive(str(source), str(reader), "--json-report", str(report), cwd=root)
                self.assertNotEqual(0, result.returncode)
                self.assertIn(expected, result.stderr)
                self.assertEqual(original, source.read_bytes())
                self.assertFalse(reader.exists())
                self.assertFalse(report.exists())

    def test_current_body_outputs_must_be_distinct_and_new(self):
        for existing in ("reader", "report", "source-alias", "output-alias"):
            with self.subTest(existing=existing), tempfile.TemporaryDirectory() as directory:
                root = pathlib.Path(directory)
                source, reader, report = (root / name for name in ("body.md", "reader.md", "reader.json"))
                source.write_text("# Body\n\nThe identity is $x=x$.\n", encoding="utf-8")
                if existing == "reader":
                    reader.write_text("KEEP READER", encoding="utf-8")
                elif existing == "report":
                    report.write_text("KEEP REPORT", encoding="utf-8")
                elif existing == "source-alias":
                    reader = source
                else:
                    report = reader
                originals = {path: path.read_bytes() for path in (source, reader, report) if path.exists()}
                result = self.run_derive(str(source), str(reader), "--json-report", str(report), cwd=root)
                self.assertNotEqual(0, result.returncode)
                for path in (source, reader, report):
                    if path in originals:
                        self.assertEqual(originals[path], path.read_bytes())
                    else:
                        self.assertFalse(path.exists())

    @unittest.skipUnless(INSPECT_AVAILABLE, "PyYAML/Pandoc/fontconfig inspection dependencies are unavailable")
    def test_control_narrative_is_not_a_build_input(self):
        builder = runpy.run_path(str(BUILDER))
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            body = "# Demonstration\n\nThe field is $\\mathbb{Q}$.\n"
            source, control = self.make_body_control(root, body)
            first, issues, first_reader = builder["inspect_source"](source, False, control)
            self.assertFalse([issue for issue in issues if issue.severity == "ERROR"])
            control.write_text(control_text(narrative=(
                "Changed review notes. $\\mathbb{1}$\n\\input{CONTROL_MUST_NOT_BE_READ.tex}\n"
                "unclosed mathematics $ and label \\label{archive-label}"
            )), encoding="utf-8")
            second, issues, second_reader = builder["inspect_source"](source, False, control)
            self.assertFalse([issue for issue in issues if issue.severity == "ERROR"])
            self.assertEqual(body, first_reader)
            self.assertEqual(first_reader, second_reader)
            self.assertEqual(first["profile"], second["profile"])
            self.assertEqual("body-and-control", second["input_format"])

    def test_control_requires_one_profile_and_rejects_embedded_ambiguity(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            source, control = self.make_body_control(root, "# Body\n\nText.\n")
            missing = self.run_builder("inspect", str(source), cwd=root)
            self.assertNotEqual(0, missing.returncode)
            self.assertIn("--control", missing.stderr)
            control.write_text("# Control\n\nNo profile supplied.\n", encoding="utf-8")
            absent = self.run_builder("inspect", str(source), "--control", str(control), cwd=root)
            self.assertNotEqual(0, absent.returncode)
            self.assertIn("expected one <!-- BEGIN:BUILD_PROFILE -->, found 0", absent.stdout)
            control.write_text(control_text() + control_text(), encoding="utf-8")
            duplicate = self.run_builder("inspect", str(source), "--control", str(control), cwd=root)
            self.assertNotEqual(0, duplicate.returncode)
            self.assertIn("expected one <!-- BEGIN:BUILD_PROFILE -->, found 2", duplicate.stdout)
            control.write_text(control_text(), encoding="utf-8")
            source.write_text("# Body\n\nText.\n" + control_text(), encoding="utf-8")
            ambiguous = self.run_builder("inspect", str(source), "--control", str(control), cwd=root)
            self.assertNotEqual(0, ambiguous.returncode)
            self.assertIn("ambiguous build_profile", ambiguous.stdout)

    @unittest.skipUnless(INSPECT_AVAILABLE, "PyYAML/Pandoc/fontconfig inspection dependencies are unavailable")
    def test_chinese_language_default_preserves_explicit_document_language(self):
        builder = runpy.run_path(str(BUILDER))
        for metadata, expected in (("", "zh-CN"), ("---\nlang: en-US\n---\n\n", "en-US")):
            with self.subTest(metadata=metadata), tempfile.TemporaryDirectory() as directory:
                root = pathlib.Path(directory)
                source, control = self.make_body_control(root, metadata + "# 中文标题\n\n数学正文 $x=1$。\n")
                # This is an AST/language fixture, not a glyph or PDF test.
                configured = profile_yaml().replace("    math_main:", "    cjk_sans: DejaVu Sans\n    cjk_mono: DejaVu Sans Mono\n    math_main:")
                control.write_text(control_text(profile=configured), encoding="utf-8")
                report, issues, _reader = builder["inspect_source"](source, False, control)
                self.assertFalse([issue for issue in issues if issue.severity == "ERROR"])
                self.assertEqual(expected, report["effective_language"])

    @unittest.skipUnless(INSPECT_AVAILABLE, "PyYAML/Pandoc/fontconfig inspection dependencies are unavailable")
    def test_inspect_accepts_profile_and_reports_review_candidates(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            source, control = self.make_body_control(root, "A sentence.\n\n$$x=y$$\n\n## 为什么成立")
            configured = profile_yaml().replace("    math_main:", "    cjk_sans: DejaVu Sans\n    cjk_mono: DejaVu Sans Mono\n    math_main:")
            control.write_text(control_text(profile=configured), encoding="utf-8")
            report = root / "tmp" / "inspect.json"
            result = self.run_builder(
                "inspect",
                str(source),
                "--control",
                str(control),
                "--third-party-headings",
                "--json-report",
                str(report),
                cwd=root,
            )
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            payload = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(0, payload["errors"])
            self.assertGreaterEqual(payload["review_items"], 2)
            self.assertIn("x=y", payload["display_candidates"])
            self.assertIn("为什么成立", payload["heading_candidates"])

    @unittest.skipUnless(INSPECT_AVAILABLE, "PyYAML/Pandoc/fontconfig inspection dependencies are unavailable")
    def test_cjk_metadata_round_trips_through_pandoc_inspection(self):
        builder = runpy.run_path(str(BUILDER))
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            source, control = self.make_body_control(root,
                "---\nCJKsansfont: DejaVu Sans\nCJKmonofont: DejaVu Sans Mono\n---\n\n# 中文标题\n")
            report, issues, _reader = builder["inspect_source"](source, False, control)
            self.assertFalse([issue for issue in issues if issue.severity == "ERROR"])
            self.assertEqual("DejaVu Sans", report["profile"]["fonts"]["cjk_sans"])
            self.assertEqual("DejaVu Sans Mono", report["profile"]["fonts"]["cjk_mono"])

    @unittest.skipUnless(YAML_AVAILABLE, "PyYAML is unavailable")
    def test_duplicate_unknown_and_escaping_profile_fields_fail(self):
        cases = {
            "duplicate": (profile_yaml(extra="  engine: xelatex"), "duplicate YAML key"),
            "unknown": (profile_yaml(extra="  arbitrary: true"), "unknown keys"),
            "escape": (profile_yaml(figures="[../outside]"), "resource path must stay relative"),
        }
        for label, (profile, expected) in cases.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory() as directory:
                root = pathlib.Path(directory)
                source, control = self.make_body_control(root, "Text.", profile=profile)
                result = self.run_builder("inspect", str(source), "--control", str(control), cwd=root)
                self.assertNotEqual(0, result.returncode, result.stdout + result.stderr)
                self.assertIn(expected, result.stdout)

    @unittest.skipUnless(INSPECT_AVAILABLE, "PyYAML/Pandoc/fontconfig inspection dependencies are unavailable")
    def test_nonuppercase_and_opaque_mathbb_are_blocked(self):
        for expression in (r"$\mathbb{1}$", r"$\mathbb{k}$", r"$\mathbb{AB}$", r"$\mathbb{\Field}$",
                           r"\(\mathbb{k}\)", r"\[\mathbb{1}\]"):
            with self.subTest(expression=expression), tempfile.TemporaryDirectory() as directory:
                root = pathlib.Path(directory)
                source, control = self.make_body_control(root, expression)
                result = self.run_builder("inspect", str(source), "--control", str(control), cwd=root)
                self.assertNotEqual(0, result.returncode, result.stdout + result.stderr)
                self.assertIn("mathbb", result.stdout)

    @unittest.skipUnless(INSPECT_AVAILABLE, "PyYAML/Pandoc/fontconfig inspection dependencies are unavailable")
    def test_mathbb_code_examples_do_not_become_rendered_math(self):
        builder = runpy.run_path(str(BUILDER))
        examples = (
            "Literal `\\mathbb{k}` and `` ` \\mathbb{1} ``.\n\n"
            "```latex\n\\mathbb{AB}\n\\mathbb{Q}\n```\n\n"
            "~~~text\n\\mathbb{\\Field}\n~~~\n\n"
            "    \\mathbb{k}\n\n"
        )
        for actual in ("", r"The field is $\mathbb{Q}$."):
            with self.subTest(actual=actual), tempfile.TemporaryDirectory() as directory:
                root = pathlib.Path(directory)
                source, control = self.make_body_control(root, examples + actual)
                report, issues, reader = builder["inspect_source"](source, False, control)
                self.assertFalse([issue for issue in issues if issue.severity == "ERROR"], issues)
                self.assertEqual(int(bool(actual)), report["mathbb_uppercase_uses"])
                self.assertEqual(examples + actual, reader)

    @unittest.skipUnless(INSPECT_AVAILABLE, "PyYAML/Pandoc/fontconfig inspection dependencies are unavailable")
    def test_mathbb_raw_tex_and_metadata_are_still_checked(self):
        cases = (
            "`\\mathbb{k}`{=latex}\n",
            "```{=tex}\n\\mathbb{1}\n```\n",
            "---\nheader-includes: |\n  \\newcommand{\\bad}{\\mathbb{k}}\n---\n\nText.\n",
        )
        for body in cases:
            with self.subTest(body=body), tempfile.TemporaryDirectory() as directory:
                root = pathlib.Path(directory)
                source, control = self.make_body_control(root, body)
                result = self.run_builder("inspect", str(source), "--control", str(control), cwd=root)
                self.assertNotEqual(0, result.returncode, result.stdout + result.stderr)
                self.assertIn("mathbb", result.stdout)

    def test_preflight_uses_the_actual_final_compiler_log(self):
        preflight = runpy.run_path(str(PREFLIGHT))
        for marker in ("[makePDF] Run #2", "[final-pdf-build] Final XeLaTeX log"):
            with self.subTest(marker=marker), tempfile.TemporaryDirectory() as directory:
                log = pathlib.Path(directory) / "build.log"
                earlier = "LaTeX Warning: Reference `eq:a' undefined.\nRerun to get cross-references right.\n"
                log.write_text(earlier + marker + "\nClean final pass.\n", encoding="utf-8")
                issues = []
                preflight["inspect_build_log"](log, issues)
                self.assertFalse(issues)
                log.write_text(earlier + marker + "\n" + earlier, encoding="utf-8")
                preflight["inspect_build_log"](log, issues)
                self.assertTrue(any(issue.severity == "ERROR" for issue in issues))

    def test_font_tool_syntax_errors_cannot_pass_as_success(self):
        diagnostic = "Syntax Error: Missing language pack for 'Adobe-GB1' mapping\n"
        builder = runpy.run_path(str(BUILDER))
        with mock.patch.object(shutil, "which", return_value="pdffonts"), mock.patch.object(
            subprocess, "run", return_value=subprocess.CompletedProcess(["pdffonts"], 0, "", diagnostic),
        ):
            issues = []
            builder["check_pdf_fonts"](pathlib.Path("sample.pdf"), False, issues)
            self.assertTrue(any(issue.severity == "ERROR" for issue in issues))
        preflight = runpy.run_path(str(PREFLIGHT))
        with mock.patch.object(
            subprocess, "run", return_value=subprocess.CompletedProcess(["pdffonts"], 0, "", diagnostic),
        ):
            result = preflight["run"](["pdffonts", "sample.pdf"])
            self.assertNotEqual(0, result.returncode)
            self.assertEqual(diagnostic, result.stderr)
        font_table = "name type encoding emb sub uni object ID\n---\nDemo CID Type 0C Identity-H no yes yes 6 0\n"
        with mock.patch.object(shutil, "which", return_value="pdffonts"), mock.patch.object(
            subprocess, "run", return_value=subprocess.CompletedProcess(["pdffonts"], 0, font_table, ""),
        ):
            issues = []
            builder["check_pdf_fonts"](pathlib.Path("sample.pdf"), False, issues)
            self.assertTrue(any("unembedded font" in issue.message for issue in issues))

    @unittest.skipUnless(
        YAML_AVAILABLE and all(shutil.which(command) for command in BUILD_COMMANDS + ("pdftotext",)),
        "PyYAML or PDF/TeX build dependencies are unavailable",
    )
    def test_control_build_exports_the_compiled_tex_and_only_used_portable_resources(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            figures = root / "figures"
            figures.mkdir()
            png = base64.b64decode(
                "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVR4nGM4IacBAALAAQ/aQIG5AAAAAElFTkSuQmCC"
            )
            (figures / "used.png").write_bytes(png)
            (figures / "unused.png").write_bytes(png)
            (root / "macros.tex").write_text(r"\newcommand{\field}{\mathbb{Q}}" + "\n", encoding="utf-8")
            (root / "unused.tex").write_text("UNUSED RESOURCE", encoding="utf-8")
            bibliography = root / "references.bib"
            bibliography.write_text(
                "@book{demo, title={A Demonstration}, author={Tester, A.}, year={2024}}\n",
                encoding="utf-8",
            )
            profile = profile_yaml(figures="[figures, macros.tex]").replace("bibliography: null", "bibliography: references.bib")
            body = (
                "---\nheader-includes: |\n  \\input{macros.tex}\n---\n\n"
                "# Demonstration\n\n"
                "The fields are $\\field$ and $\\mathbb{Q}$.\n\n"
                "\\begin{equation}\\label{eq:a}x=1\\end{equation}\n\n"
                "Equation \\eqref{eq:a} is recorded in [@demo].\n\n"
                "![Used figure](figures/used.png){width=12mm}\n"
            )
            source, control = self.make_body_control(root, body, profile=profile)
            control.write_text(control_text(profile=profile, narrative=(
                "CONTROL_MUST_NOT_APPEAR\n\\input{MISSING_CONTROL_RESOURCE.tex}\n$\\mathbb{1}$"
            )), encoding="utf-8")
            temporary = root / "tmp"
            reader, pdf, tex = (temporary / name for name in (
                "finished_v1.0.1.reader.md", "finished_v1.0.1.pdf", "finished_v1.0.1.tex",
            ))
            log, report = temporary / "build.log", temporary / "build.json"
            builder = runpy.run_path(str(BUILDER))
            handler = builder["command_build"]
            original_run = handler.__globals__["run"]
            compiled_inputs = []

            def capture_compiled_tex(command, *, cwd=None):
                if command[0] == "latexmk":
                    compiled_inputs.append((cwd / command[-1]).read_bytes())
                return original_run(command, cwd=cwd)

            arguments = argparse.Namespace(
                source=source, control=control, reader=reader, pdf=pdf,
                build_log=log, json_report=report, tex=tex, third_party_headings=False,
            )
            with mock.patch.dict(handler.__globals__, {"run": capture_compiled_tex}), mock.patch("builtins.print"):
                status = handler(arguments)
            log_text = log.read_text(encoding="utf-8") if log.exists() else ""
            self.assertEqual(0, status, log_text)
            self.assertEqual([tex.read_bytes()], compiled_inputs)
            self.assertEqual(body, reader.read_text(encoding="utf-8"))
            tex_text = tex.read_text(encoding="utf-8")
            self.assertIn(r"\begin{document}", tex_text)
            self.assertIn("finished_v1.0.1.resources/", tex_text)
            self.assertNotIn(str(root), tex_text)
            self.assertNotIn("CONTROL_MUST_NOT", tex_text)
            resources = tex.with_suffix(".resources")
            self.assertEqual(
                {"figures/used.png", "macros.tex"},
                {path.relative_to(resources).as_posix() for path in resources.rglob("*") if path.is_file()},
            )
            payload = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(str(tex), payload["tex"])
            self.assertEqual(2, len(payload["tex_resources"]))
            self.assertIn("[final-pdf-build] Final XeLaTeX log", log_text)
            issues = []
            runpy.run_path(str(PREFLIGHT))["inspect_build_log"](log, issues)
            self.assertFalse([issue for issue in issues if issue.severity == "ERROR"])

            # Archive the pair, then remove original dependencies. Rebuilding
            # proves the exported TeX has no dependency on its initial location.
            old = root / "old"
            old.mkdir()
            shutil.move(str(tex), old / tex.name)
            shutil.move(str(resources), old / resources.name)
            shutil.rmtree(figures)
            (root / "macros.tex").unlink()
            bibliography.unlink()
            rebuilt = subprocess.run(
                ["latexmk", "-norc", "-xelatex", "-interaction=nonstopmode", "-halt-on-error", tex.name],
                cwd=old, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
            )
            self.assertEqual(0, rebuilt.returncode, rebuilt.stdout + rebuilt.stderr)
            self.assertTrue((old / pdf.name).is_file())

    @unittest.skipUnless(
        YAML_AVAILABLE and all(shutil.which(command) for command in BUILD_COMMANDS + ("kpsewhich",)),
        "PyYAML or PDF/TeX build dependencies are unavailable",
    )
    def test_tex_export_distinguishes_nested_toolchain_from_undeclared_project_macros(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            tree = root / "tmp" / "pdf-env" / "texmf"
            package = tree / "tex" / "latex" / "candidateenv" / "candidateenv.sty"
            package.parent.mkdir(parents=True)
            package.write_text("\\ProvidesPackage{candidateenv}\n\\newcommand{\\cachevalue}{C}\n")
            macro = root / "macros.tex"
            macro.write_text("\\newcommand{\\projectvalue}{P}\n")
            body = "---\nheader-includes: |\n  \\usepackage{candidateenv}\n  \\input{macros.tex}\n---\n\n# Portable export\n\n$\\cachevalue+\\projectvalue$.\n"
            source, control = self.make_body_control(root, body, profile=profile_yaml(figures="[macros.tex]"))
            temporary = root / "tmp"
            tex = temporary / "nested_v1.0.1.tex"
            arguments = argparse.Namespace(
                source=source, control=control, reader=temporary / "nested.reader.md",
                pdf=temporary / "nested.pdf", build_log=temporary / "nested.log",
                json_report=temporary / "nested.json", tex=tex, third_party_headings=False,
            )
            previous = subprocess.run(["kpsewhich", "-var-value=TEXMFHOME"], capture_output=True, text=True, check=True).stdout.strip()
            environment = {"TEXMFHOME": str(tree) + (os.pathsep + previous if previous else "")}
            builder = runpy.run_path(str(BUILDER))
            with mock.patch.dict(os.environ, environment), mock.patch("builtins.print"):
                status = builder["command_build"](arguments)
                self.assertEqual(0, status, arguments.build_log.read_text())
                self.assertEqual(["macros.tex"], [p.relative_to(tex.with_suffix(".resources")).as_posix() for p in tex.with_suffix(".resources").rglob("*") if p.is_file()])
                detached = root / "detached"
                detached.mkdir()
                shutil.move(str(tex), detached / tex.name)
                shutil.move(str(tex.with_suffix(".resources")), detached / tex.with_suffix(".resources").name)
                macro.unlink()
                rebuilt = subprocess.run(["latexmk", "-norc", "-xelatex", "-interaction=nonstopmode", "-halt-on-error", tex.name], cwd=detached, capture_output=True, text=True)
                self.assertEqual(0, rebuilt.returncode, rebuilt.stdout + rebuilt.stderr)
                # Other files under tmp remain project resources and cannot use
                # the configured TEXMF exception to bypass declaration.
                undeclared = temporary / "undeclared.tex"
                undeclared.write_text("unregistered project macro")
                recorder = temporary / "check.fls"
                recorder.write_text(f"INPUT {package}\nINPUT {undeclared}\n")
                issues = []
                builder["recorded_resources"](recorder, detached, root, issues)
                self.assertEqual(1, len(issues))
                self.assertIn("undeclared.tex", issues[0].message)

    @unittest.skipUnless(
        YAML_AVAILABLE and all(shutil.which(command) for command in BUILD_COMMANDS),
        "PyYAML or PDF/TeX build dependencies are unavailable",
    )
    def test_tex_export_preserves_a_used_project_symlink_alias(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            shared = root / "shared"
            shared.mkdir()
            macro = r"\newcommand{\field}{\mathbb{Q}}" + "\n"
            (shared / "base.tex").write_text(macro, encoding="utf-8")
            try:
                (root / "macros.tex").symlink_to(pathlib.Path("shared") / "base.tex")
            except OSError as exc:
                self.skipTest(f"creating a file symlink is unavailable: {exc}")
            source, control = self.make_body_control(
                root, "# Body\n\n\\input{macros.tex}\n\nThe field is $\\field$ and $\\mathbb{Q}$.\n",
                profile=profile_yaml(figures="[macros.tex]"),
            )
            temporary = root / "tmp"
            pdf, tex, log = (temporary / name for name in (
                "finished_v1.0.1.pdf", "finished_v1.0.1.tex", "build.log",
            ))
            result = self.run_builder(
                "build", str(source), "--control", str(control), "--reader", str(temporary / "reader.md"),
                "--pdf", str(pdf), "--build-log", str(log), "--json-report", str(temporary / "build.json"),
                "--tex", str(tex), cwd=root,
            )
            self.assertEqual(0, result.returncode, result.stdout + result.stderr + log.read_text(encoding="utf-8"))
            resources = tex.with_suffix(".resources")
            exported_macro = resources / "macros.tex"
            self.assertEqual(macro, exported_macro.read_text(encoding="utf-8"))
            self.assertFalse(exported_macro.is_symlink())
            old = root / "old"
            old.mkdir()
            shutil.move(str(tex), old / tex.name)
            shutil.move(str(resources), old / resources.name)
            (root / "macros.tex").unlink()
            shutil.rmtree(shared)
            rebuilt = subprocess.run(
                ["latexmk", "-norc", "-xelatex", "-interaction=nonstopmode", "-halt-on-error", tex.name],
                cwd=old, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
            )
            self.assertEqual(0, rebuilt.returncode, rebuilt.stdout + rebuilt.stderr)
            self.assertTrue((old / pdf.name).is_file())

    def test_tex_export_refuses_existing_file_and_resource_directory(self):
        for existing in ("tex", "resources"):
            with self.subTest(existing=existing), tempfile.TemporaryDirectory() as directory:
                root = pathlib.Path(directory)
                source, control = self.make_body_control(root, "# Body\n\nText.\n")
                temporary = root / "tmp"
                tex, reader = temporary / "finished_v1.0.1.tex", temporary / "reader.md"
                if existing == "tex":
                    tex.write_text("KEEP ME", encoding="utf-8")
                else:
                    tex.with_suffix(".resources").mkdir()
                    (tex.with_suffix(".resources") / "keep").write_text("KEEP ME", encoding="utf-8")
                result = self.run_builder(
                    "build", str(source), "--control", str(control), "--reader", str(reader),
                    "--pdf", str(temporary / "finished_v1.0.1.pdf"),
                    "--build-log", str(temporary / "build.log"), "--json-report", str(temporary / "build.json"),
                    "--tex", str(tex), cwd=root,
                )
                self.assertNotEqual(0, result.returncode)
                self.assertFalse(reader.exists())
                preserved = tex if existing == "tex" else tex.with_suffix(".resources") / "keep"
                self.assertEqual("KEEP ME", preserved.read_text(encoding="utf-8"))

    @unittest.skipUnless(
        YAML_AVAILABLE and all(shutil.which(command) for command in BUILD_COMMANDS + ("pdftotext", "kpsewhich")),
        "PyYAML or Chinese PDF build dependencies are unavailable",
    )
    def test_chinese_build_localizes_the_toc_and_explicit_today(self):
        builder = runpy.run_path(str(BUILDER))
        xecjk = subprocess.run(["kpsewhich", "xeCJK.sty"], text=True, capture_output=True, check=False)
        cjk_font = next((font for font in ("Noto Serif CJK SC", "SimSun", "FandolSong")
                         if builder["font_available"](font)), None)
        if xecjk.returncode or cjk_font is None:
            self.skipTest("xeCJK or a supported test CJK font is unavailable")
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            profile = profile_yaml().replace(
                "latin_main: DejaVu Sans", "latin_main: Latin Modern Roman",
            ).replace("cjk_main: DejaVu Sans", f"cjk_main: {cjk_font}").replace("toc: false", "toc: true")
            body = (
                "---\ntitle: 中文数学文稿\ndate: '\\today'\n---\n\n"
                "# 记号与问题\n\n设 $x\\in\\mathbb{Q}$。\n\n"
                "\\begin{equation}\\label{eq:identity}x=x\\end{equation}\n\n"
                "恒等式 \\eqref{eq:identity} 保持不变。\n\n"
                "行内公式 \\(x+1\\) 与陈列公式：\n\n"
                "\\[f(x)=\\begin{cases}x,&x\\geq0,\\\\-x,&x<0.\\end{cases}\\]\n"
            )
            source, control = self.make_body_control(root, body, profile=profile)
            temporary = root / "tmp"
            pdf, tex, log = (temporary / name for name in (
                "finished_v1.0.1.pdf", "finished_v1.0.1.tex", "build.log",
            ))
            result = self.run_builder(
                "build", str(source), "--control", str(control), "--reader", str(temporary / "reader.md"),
                "--pdf", str(pdf), "--build-log", str(log), "--json-report", str(temporary / "build.json"),
                "--tex", str(tex), cwd=root,
            )
            self.assertEqual(0, result.returncode, result.stdout + result.stderr + log.read_text(encoding="utf-8"))
            extracted = subprocess.run(
                ["pdftotext", str(pdf), "-"], text=True, capture_output=True, check=True,
            ).stdout
            compact = re.sub(r"\s+", "", extracted)
            self.assertIn("中文数学文稿", compact)
            self.assertIn("目录", compact)
            self.assertRegex(compact, r"\d{4}年\d{1,2}月\d{1,2}日")
            self.assertNotIn("??", extracted)
            self.assertNotIn("Contents", extracted)
            self.assertIn("pdflang={zh-CN}", tex.read_text(encoding="utf-8"))

    @unittest.skipUnless(
        YAML_AVAILABLE and all(shutil.which(command) for command in BUILD_COMMANDS),
        "PyYAML or PDF build dependencies are unavailable",
    )
    def test_clean_build_ignores_stale_derivatives_and_embeds_msbm(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            source, control = self.make_body_control(root, r"The field is $\mathbb{Q}$.")
            (root / "stale.tex").write_text("THIS MUST NOT BE READ", encoding="utf-8")
            (root / "stale.pdf").write_bytes(b"not a PDF")
            reader = root / "tmp" / "finished_v1.0.1.reader.md"
            pdf = root / "tmp" / "finished_v1.0.1.pdf"
            log = root / "tmp" / "finished_v1.0.1.log"
            report = root / "tmp" / "build.json"
            result = self.run_builder(
                "build",
                str(source),
                "--control",
                str(control),
                "--reader",
                str(reader),
                "--pdf",
                str(pdf),
                "--build-log",
                str(log),
                "--json-report",
                str(report),
                cwd=root,
            )
            log_text = log.read_text(encoding="utf-8") if log.exists() else ""
            self.assertEqual(0, result.returncode, result.stdout + result.stderr + log_text)
            self.assertTrue(pdf.is_file())
            self.assertEqual(source.read_bytes(), reader.read_bytes())
            fonts = subprocess.run(
                ["pdffonts", str(pdf)],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            ).stdout
            self.assertIn("MSBM10", fonts.upper())
            self.assertNotIn("Type 3", fonts)
            payload = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(0, payload["errors"])
            preflight_report = root / "tmp" / "preflight.json"
            preflight = subprocess.run(
                [
                    sys.executable,
                    str(PREFLIGHT),
                    str(pdf),
                    "--build-log",
                    str(log),
                    "--render-dir",
                    str(root / "tmp" / "rendered"),
                    "--expected-version",
                    "v1.0.1",
                    "--require-font",
                    "MSBM10",
                    "--json-report",
                    str(preflight_report),
                ],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            self.assertEqual(0, preflight.returncode, preflight.stdout + preflight.stderr)


if __name__ == "__main__":
    unittest.main()
