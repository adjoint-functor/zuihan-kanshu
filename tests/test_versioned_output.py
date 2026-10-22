#!/usr/bin/env python3
"""Tests for ordinary-draft and reader-artifact version transitions."""

from __future__ import annotations

import errno
import importlib.util
import json
import pathlib
import tempfile
import unittest
from unittest import mock


REPOSITORY_ROOT = pathlib.Path(__file__).resolve().parents[1]
ROOT = REPOSITORY_ROOT / "skill" / "zuihan-kanshu"
SCRIPT = ROOT / "scripts" / "versioned-output.py"
SPEC = importlib.util.spec_from_file_location("versioned_output", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
vo = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(vo)


class VersionedOutputTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.output = pathlib.Path(self.temporary.name) / "delivery"
        self.output.mkdir()

    def tearDown(self):
        self.temporary.cleanup()

    def write_group(self, directory, version, label):
        stem = f"稿件_{version}"
        files = {
            f"{stem}.control.md": f"# 控制稿\n{label} plan\n".encode("utf-8"),
            f"{stem}.md": f"# 正文\n{label}\n![图]({stem}.resources/figures/plot.svg)\n".encode("utf-8"),
            f"{stem}.pdf": b"%PDF-1.7\n\x00" + label.encode("utf-8"),
            f"{stem}.resources/figures/plot.svg": f"<svg>{label}</svg>\n".encode("utf-8"),
        }
        for name, content in files.items():
            path = directory / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        return files

    def prepare_group(self, output):
        old = self.write_group(output, "v1.0.0", "old")
        vo.begin_revision(
            output, ["稿件_v1.0.0.control.md", "稿件_v1.0.0.md"], "v1.0.1",
            regenerate_files=["稿件_v1.0.0.pdf", "稿件_v1.0.0.resources"],
        )
        new = self.write_group(output / "tmp", "v1.0.1", "new")
        return old, new

    def assert_group(self, directory, files):
        for name, content in files.items():
            self.assertEqual(content, (directory / name).read_bytes(), name)

    def test_ensure_creates_old_and_tmp(self):
        result = vo.ensure_output_dir(self.output)
        self.assertTrue((self.output / "old").is_dir())
        self.assertTrue((self.output / "tmp").is_dir())
        self.assertIn("old", result["created"])
        self.assertIn("tmp", result["created"])

    def test_inspect_without_plan_reports_null_pending_phase(self):
        result = vo.inspect_output(self.output)
        self.assertFalse(result["pending_revision"])
        self.assertIsNone(result["pending_phase"])

    def test_markdown_revision_preserves_old_file(self):
        current = self.output / "讲义_v1.0.0.md"
        current.write_text("旧正文\n", encoding="utf-8")
        vo.begin_revision(self.output, [current.name], "v1.0.1")
        candidate = self.output / "tmp" / "讲义_v1.0.1.md"
        candidate.write_text("新正文\n", encoding="utf-8")
        result = vo.finalize_revision(self.output)
        self.assertEqual("FINALIZED", result["status"])
        self.assertEqual("新正文\n", (self.output / "讲义_v1.0.1.md").read_text(encoding="utf-8"))
        self.assertEqual("旧正文\n", (self.output / "old" / current.name).read_text(encoding="utf-8"))
        self.assertFalse(current.exists())

    def test_finished_markdown_and_pdf_move_as_one_version(self):
        md = self.output / "报告_v2.1.0.md"
        pdf = self.output / "报告_v2.1.0.pdf"
        md.write_text("old md\n", encoding="utf-8")
        pdf.write_bytes(b"old pdf")
        vo.begin_revision(self.output, [md.name, pdf.name], "2.1.1")
        (self.output / "tmp" / "报告_v2.1.1.md").write_text("new md\n", encoding="utf-8")
        (self.output / "tmp" / "报告_v2.1.1.pdf").write_bytes(b"new pdf")
        vo.finalize_revision(self.output)
        self.assertTrue((self.output / "报告_v2.1.1.md").is_file())
        self.assertTrue((self.output / "报告_v2.1.1.pdf").is_file())
        self.assertTrue((self.output / "old" / md.name).is_file())
        self.assertTrue((self.output / "old" / pdf.name).is_file())

    def test_control_markdown_pdf_and_resources_preserve_complete_history(self):
        history = self.write_group(self.output, "v1.0.0", "initial")
        current = "v1.0.0"
        for following, label in (("v1.0.1", "revision"), ("v1.1.0", "extended")):
            vo.begin_revision(
                self.output, [f"稿件_{current}.control.md", f"稿件_{current}.md"], following,
                regenerate_files=[f"稿件_{current}.pdf", f"稿件_{current}.resources"],
            )
            for extension in (".control.md", ".md"):
                self.assertEqual(
                    (self.output / f"稿件_{current}{extension}").read_bytes(),
                    (self.output / "tmp" / f"稿件_{following}{extension}").read_bytes(),
                )
            new = self.write_group(self.output / "tmp", following, label)
            ready = vo.finalize_revision(self.output, dry_run=True)
            self.assertEqual("READY-TO-FINALIZE", ready["status"])
            self.assert_group(self.output / "tmp", new)
            result = vo.finalize_revision(self.output)
            self.assertEqual("FINALIZED", result["status"])
            self.assert_group(self.output / "old", history)
            self.assert_group(self.output, new)
            self.assertEqual([], list((self.output / "tmp").iterdir()))
            self.assertEqual(
                {f"稿件_{following}{extension}" for extension in (".control.md", ".md", ".pdf", ".resources")},
                {row["file"] for row in vo.inspect_output(self.output)["versioned_files"]},
            )
            history.update(new)
            current = following

    def test_complete_group_resumes_after_each_publish_or_archive_move(self):
        for interrupted_after in range(1, 9):
            with self.subTest(interrupted_after=interrupted_after):
                output = pathlib.Path(self.temporary.name) / f"interrupted-{interrupted_after}"
                output.mkdir()
                old, new = self.prepare_group(output)
                original_move = vo._move_without_overwrite
                calls = 0

                def interrupted_move(source, target):
                    nonlocal calls
                    original_move(source, target)
                    calls += 1
                    if calls == interrupted_after:
                        raise KeyboardInterrupt("stop immediately after a completed move")

                with mock.patch.object(vo, "_move_without_overwrite", interrupted_move):
                    with self.assertRaises(KeyboardInterrupt):
                        vo.finalize_revision(output)
                self.assertEqual("FINALIZING", vo.inspect_output(output)["pending_phase"])
                for files, locations in ((old, (output, output / "old")), (new, (output / "tmp", output))):
                    for name, content in files.items():
                        surviving = [directory / name for directory in locations if (directory / name).is_file()]
                        self.assertEqual(1, len(surviving), name)
                        self.assertEqual(content, surviving[0].read_bytes(), name)

                self.assertEqual("FINALIZED", vo.finalize_revision(output)["status"])
                self.assert_group(output / "old", old)
                self.assert_group(output, new)
                self.assertEqual([], list((output / "tmp").iterdir()))

    def test_regenerated_pdf_and_first_control_and_tex_publish_as_one_group(self):
        md = self.output / "报告_v2.1.0.md"
        pdf = self.output / "报告_v2.1.0.pdf"
        md.write_text("old md\n", encoding="utf-8")
        pdf.write_bytes(b"old pdf")
        added = ["报告_v2.1.1.control.md", "报告_v2.1.1.tex"]
        vo.begin_revision(
            self.output, [md.name], "2.1.1",
            regenerate_files=[pdf.name], add_files=added,
        )
        names = ["报告_v2.1.1.md", "报告_v2.1.1.pdf", *added]
        self.assertEqual(
            {"报告_v2.1.1.md", vo.PLAN_NAME},
            {path.name for path in (self.output / "tmp").iterdir()},
        )
        for name in names:
            candidate = self.output / "tmp" / name
            if name.endswith(".pdf"):
                with candidate.open("xb") as handle:
                    handle.write(b"new pdf")
            elif name != "报告_v2.1.1.md":
                with candidate.open("x", encoding="utf-8") as handle:
                    handle.write("new artifact\n")
            else:
                candidate.write_text("new md\n", encoding="utf-8")
        result = vo.finalize_revision(self.output)
        self.assertEqual(names, result["published"])
        self.assertEqual([md.name, pdf.name], result["archived"])
        self.assertEqual("old md\n", (self.output / "old" / md.name).read_text(encoding="utf-8"))
        self.assertEqual(b"old pdf", (self.output / "old" / pdf.name).read_bytes())
        self.assertEqual(set(names), {path.name for path in self.output.iterdir() if path.is_file()})

    def test_missing_generated_candidate_blocks_the_entire_group(self):
        for index, missing in enumerate(("报告_v1.0.1.pdf", "报告_v1.0.1.control.md")):
            with self.subTest(missing=missing):
                output = pathlib.Path(self.temporary.name) / f"missing-{index}"
                output.mkdir()
                md = output / "报告_v1.0.0.md"
                pdf = output / "报告_v1.0.0.pdf"
                md.write_text("old body\n", encoding="utf-8")
                pdf.write_bytes(b"old pdf")
                vo.begin_revision(
                    output, [md.name], "v1.0.1",
                    regenerate_files=[pdf.name], add_files=["报告_v1.0.1.control.md"],
                )
                for name in ("报告_v1.0.1.pdf", "报告_v1.0.1.control.md"):
                    if name != missing:
                        (output / "tmp" / name).write_text("generated\n", encoding="utf-8")
                with self.assertRaisesRegex(vo.VersionedOutputError, "候选文件缺失"):
                    vo.finalize_revision(output)
                self.assertEqual("old body\n", md.read_text(encoding="utf-8"))
                self.assertEqual(b"old pdf", pdf.read_bytes())
                self.assertEqual([], list((output / "old").iterdir()))
                self.assertFalse((output / "报告_v1.0.1.md").exists())
                plan = json.loads((output / "tmp" / vo.PLAN_NAME).read_text(encoding="utf-8"))
                self.assertEqual("EDITING", plan["phase"])

    def test_missing_resource_directory_blocks_the_complete_group(self):
        old, new = self.prepare_group(self.output)
        resources = self.output / "tmp" / "稿件_v1.0.1.resources"
        (resources / "figures" / "plot.svg").unlink()
        (resources / "figures").rmdir()
        resources.rmdir()
        with self.assertRaisesRegex(vo.VersionedOutputError, "候选文件缺失"):
            vo.finalize_revision(self.output)
        self.assert_group(self.output, old)
        self.assertEqual([], list((self.output / "old").iterdir()))
        self.assertFalse((self.output / "稿件_v1.0.1.control.md").exists())
        self.assertEqual("EDITING", vo.inspect_output(self.output)["pending_phase"])
        self.write_group(self.output / "tmp", "v1.0.1", "new")
        vo.finalize_revision(self.output)
        self.assert_group(self.output, new)
        self.assert_group(self.output / "old", old)

    def test_regenerate_without_copy_and_cli_add_options(self):
        current = self.output / "报告_v1.0.0.pdf"
        current.write_bytes(b"old pdf")
        with mock.patch("builtins.print"):
            status = vo.main([
                "begin-revision", str(self.output), "--regenerate", current.name,
                "--add", "报告_v1.0.1.control.md", "--next-version", "v1.0.1",
            ])
        self.assertEqual(0, status)
        self.assertFalse((self.output / "tmp" / "报告_v1.0.1.pdf").exists())
        (self.output / "tmp" / "报告_v1.0.1.pdf").write_bytes(b"new pdf")
        (self.output / "tmp" / "报告_v1.0.1.control.md").write_text("control\n", encoding="utf-8")
        vo.finalize_revision(self.output)
        self.assertEqual(b"old pdf", (self.output / "old" / current.name).read_bytes())

    def test_begin_rejects_invalid_additions_and_duplicate_sources(self):
        current = self.output / "正文_v1.0.0.md"
        current.write_text("old body\n", encoding="utf-8")
        cases = [
            {"add_files": ["控制_v1.0.0.md"]},
            {"add_files": ["tmp/控制_v1.0.1.md"]},
            {"add_files": ["正文_v1.0.1.md"]},
            {"add_files": ["控制_v1.0.1.md", "控制_v1.0.1.md"]},
            {"regenerate_files": [current.name]},
        ]
        for options in cases:
            with self.subTest(options=options):
                with self.assertRaises(vo.VersionedOutputError):
                    vo.begin_revision(self.output, [current.name], "v1.0.1", **options)
                self.assertFalse((self.output / "tmp" / vo.PLAN_NAME).exists())
        with self.assertRaises(vo.VersionedOutputError):
            vo.begin_revision(self.output, [], "v1.0.1", add_files=["控制_v1.0.1.md"])

    def test_begin_rejects_occupied_generated_paths(self):
        current = self.output / "报告_v1.0.0.md"
        pdf = self.output / "报告_v1.0.0.pdf"
        current.write_text("old body\n", encoding="utf-8")
        pdf.write_bytes(b"old pdf")
        vo.ensure_output_dir(self.output)
        for name in ("报告_v1.0.1.pdf", "报告_v1.0.1.control.md"):
            with self.subTest(name=name):
                occupied = self.output / "tmp" / name
                occupied.write_text("occupied\n", encoding="utf-8")
                with self.assertRaisesRegex(vo.VersionedOutputError, "禁止覆盖"):
                    vo.begin_revision(
                        self.output, [current.name], "v1.0.1",
                        regenerate_files=[pdf.name], add_files=["报告_v1.0.1.control.md"],
                    )
                self.assertEqual("occupied\n", occupied.read_text(encoding="utf-8"))
                self.assertFalse((self.output / "tmp" / vo.PLAN_NAME).exists())
                occupied.unlink()

    def test_begin_rejects_collision_and_does_not_overwrite(self):
        current = self.output / "笔记_v1.0.0.md"
        current.write_text("current\n", encoding="utf-8")
        (self.output / "笔记_v1.0.1.md").write_text("occupied\n", encoding="utf-8")
        with self.assertRaises(vo.VersionedOutputError):
            vo.begin_revision(self.output, [current.name], "v1.0.1")
        self.assertEqual("current\n", current.read_text(encoding="utf-8"))
        self.assertEqual("occupied\n", (self.output / "笔记_v1.0.1.md").read_text(encoding="utf-8"))

    def test_begin_rejects_mixed_current_versions(self):
        first = self.output / "甲_v1.0.0.md"
        second = self.output / "乙_v1.0.1.md"
        first.write_text("a", encoding="utf-8")
        second.write_text("b", encoding="utf-8")
        with self.assertRaises(vo.VersionedOutputError):
            vo.begin_revision(self.output, [first.name, second.name], "v1.0.2")

    def test_moved_directory_remains_usable(self):
        current = self.output / "文稿_v1.0.0.md"
        current.write_text("old\n", encoding="utf-8")
        moved = self.output.parent / "renamed-delivery"
        self.output.rename(moved)
        vo.begin_revision(moved, ["文稿_v1.0.0.md"], "v1.0.1")
        vo.finalize_revision(moved)
        self.assertTrue((moved / "文稿_v1.0.1.md").is_file())
        self.assertTrue((moved / "old" / "文稿_v1.0.0.md").is_file())

    def test_finalize_resumes_after_partial_publish_without_overwrite(self):
        first = self.output / "正文_v1.0.0.md"
        second = self.output / "附录_v1.0.0.md"
        first.write_text("old body\n", encoding="utf-8")
        second.write_text("old appendix\n", encoding="utf-8")
        vo.begin_revision(self.output, [first.name, second.name], "v1.0.1")
        plan_path = self.output / "tmp" / vo.PLAN_NAME
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        plan["phase"] = "FINALIZING"
        plan_path.write_text(json.dumps(plan, ensure_ascii=False), encoding="utf-8")
        first_candidate = self.output / "tmp" / "正文_v1.0.1.md"
        first_target = self.output / "正文_v1.0.1.md"
        first_candidate.rename(first_target)
        first.rename(self.output / "old" / first.name)

        result = vo.finalize_revision(self.output)
        self.assertEqual("FINALIZED", result["status"])
        self.assertEqual("old body\n", (self.output / "old" / first.name).read_text(encoding="utf-8"))
        self.assertEqual("old appendix\n", (self.output / "old" / second.name).read_text(encoding="utf-8"))
        self.assertTrue(first_target.is_file())
        self.assertTrue((self.output / "附录_v1.0.1.md").is_file())
        self.assertFalse((self.output / "tmp" / vo.PLAN_NAME).exists())

    def test_begin_resumes_after_atomic_copy_interruption(self):
        first = self.output / "正文_v1.0.0.md"
        second = self.output / "附录_v1.0.0.md"
        first.write_text("old body\n", encoding="utf-8")
        second.write_text("old appendix\n", encoding="utf-8")
        original_copy = vo.shutil.copy2
        calls = 0

        def interrupted_copy(source, target):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError("simulated interruption")
            return original_copy(source, target)

        with mock.patch.object(vo.shutil, "copy2", side_effect=interrupted_copy):
            with self.assertRaises(vo.VersionedOutputError):
                vo.begin_revision(
                    self.output, [first.name, second.name], "v1.0.1"
                )
        plan_path = self.output / "tmp" / vo.PLAN_NAME
        self.assertTrue(plan_path.is_file())
        self.assertTrue((self.output / "tmp" / "正文_v1.0.1.md").is_file())
        self.assertFalse((self.output / "tmp" / "附录_v1.0.1.md").exists())
        interrupted = vo.inspect_output(self.output)
        self.assertTrue(interrupted["pending_revision"])
        self.assertEqual("PREPARING", interrupted["pending_phase"])

        result = vo.begin_revision(
            self.output, [first.name, second.name], "v1.0.1"
        )
        self.assertEqual("EDITING", result["phase"])
        self.assertTrue((self.output / "tmp" / "附录_v1.0.1.md").is_file())
        resumed = vo.inspect_output(self.output)
        self.assertEqual("EDITING", resumed["pending_phase"])

    def test_preparing_plan_resumes_without_overwriting_edited_candidates(self):
        first = self.output / "正文_v1.0.0.md"
        second = self.output / "附录_v1.0.0.md"
        first.write_text("old body\n", encoding="utf-8")
        second.write_text("old appendix\n", encoding="utf-8")
        vo.begin_revision(self.output, [first.name, second.name], "v1.0.1")
        plan_path = self.output / "tmp" / vo.PLAN_NAME
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        plan["phase"] = "PREPARING"
        plan_path.write_text(json.dumps(plan, ensure_ascii=False), encoding="utf-8")
        (self.output / "tmp" / "正文_v1.0.1.md").write_text("already edited\n", encoding="utf-8")
        (self.output / "tmp" / "附录_v1.0.1.md").unlink()

        result = vo.begin_revision(self.output, [first.name, second.name], "v1.0.1")
        self.assertEqual(vo.PLAN_SCHEMA, result["schema"])
        self.assertEqual("EDITING", result["phase"])
        vo.finalize_revision(self.output)
        self.assertEqual("already edited\n", (self.output / "正文_v1.0.1.md").read_text(encoding="utf-8"))
        self.assertEqual("old appendix\n", (self.output / "附录_v1.0.1.md").read_text(encoding="utf-8"))

    def test_generated_group_begin_resumes_only_with_the_same_plan(self):
        md = self.output / "报告_v1.0.0.md"
        pdf = self.output / "报告_v1.0.0.pdf"
        md.write_text("old body\n", encoding="utf-8")
        pdf.write_bytes(b"old pdf")
        options = {"regenerate_files": [pdf.name], "add_files": ["报告_v1.0.1.control.md"]}
        with mock.patch.object(vo, "_copy_candidate", side_effect=vo.VersionedOutputError("interrupted")):
            with self.assertRaises(vo.VersionedOutputError):
                vo.begin_revision(self.output, [md.name], "v1.0.1", **options)
        plan_path = self.output / "tmp" / vo.PLAN_NAME
        plan_before = plan_path.read_text(encoding="utf-8")
        with self.assertRaisesRegex(vo.VersionedOutputError, "不一致"):
            vo.begin_revision(self.output, [md.name], "v1.0.1", regenerate_files=[pdf.name])
        self.assertEqual(plan_before, plan_path.read_text(encoding="utf-8"))
        result = vo.begin_revision(self.output, [md.name], "v1.0.1", **options)
        self.assertEqual("EDITING", result["phase"])
        self.assertEqual(
            {"报告_v1.0.1.md", vo.PLAN_NAME},
            {path.name for path in (self.output / "tmp").iterdir()},
        )

    def test_resource_directories_and_tex_resume_and_archive_together(self):
        md = self.output / "报告_v1.0.0.md"
        tex = self.output / "报告_v1.0.0.tex"
        resources = self.output / "报告_v1.0.0.resources"
        md.write_text("old body\n", encoding="utf-8")
        tex.write_text("\\input{报告_v1.0.0.resources/macros.tex}\n", encoding="utf-8")
        resources.mkdir()
        (resources / "macros.tex").write_text("old macros\n", encoding="utf-8")
        added = ["报告_v1.0.1.control.md", "附加_v1.0.1.resources"]
        vo.begin_revision(
            self.output, [md.name], "v1.0.1",
            regenerate_files=[tex.name, resources.name], add_files=added,
        )
        tmp = self.output / "tmp"
        self.assertFalse((tmp / "报告_v1.0.1.resources").exists())
        self.assertFalse((tmp / "附加_v1.0.1.resources").exists())
        (tmp / "报告_v1.0.1.tex").write_text(
            "\\input{报告_v1.0.1.resources/macros.tex}\n", encoding="utf-8"
        )
        (tmp / "报告_v1.0.1.resources").mkdir()
        (tmp / "报告_v1.0.1.resources" / "macros.tex").write_text("new macros\n", encoding="utf-8")
        (tmp / added[0]).write_text("control\n", encoding="utf-8")
        (tmp / added[1]).mkdir()
        (tmp / added[1] / "figure.svg").write_text("figure\n", encoding="utf-8")
        original_move = vo._move_without_overwrite

        def interrupted_move(source, target):
            if source == resources:
                raise KeyboardInterrupt("simulated abrupt stop before old resources move")
            return original_move(source, target)

        with mock.patch.object(vo, "_move_without_overwrite", interrupted_move):
            with self.assertRaises(KeyboardInterrupt):
                vo.finalize_revision(self.output)
        self.assertEqual("FINALIZING", vo.inspect_output(self.output)["pending_phase"])
        self.assertTrue((self.output / "old" / tex.name).is_file())
        self.assertTrue(resources.is_dir())

        result = vo.finalize_revision(self.output)
        self.assertEqual([md.name, tex.name, resources.name], result["archived"])
        self.assertFalse(resources.exists())
        self.assertEqual(
            "old macros\n", (self.output / "old" / resources.name / "macros.tex").read_text(encoding="utf-8")
        )
        self.assertEqual(
            "\\input{报告_v1.0.0.resources/macros.tex}\n",
            (self.output / "old" / tex.name).read_text(encoding="utf-8"),
        )
        self.assertEqual(
            "new macros\n", (self.output / "报告_v1.0.1.resources" / "macros.tex").read_text(encoding="utf-8")
        )
        self.assertEqual("figure\n", (self.output / added[1] / "figure.svg").read_text(encoding="utf-8"))
        inspected = vo.inspect_output(self.output)
        self.assertIn("报告_v1.0.1.resources", {row["file"] for row in inspected["versioned_files"]})
        self.assertNotIn("old", inspected["other_files"])

    @unittest.skipIf(vo.os.name == "nt", "Windows uses an atomic no-replace rename")
    def test_finalizing_resumes_after_file_link_before_unlink(self):
        current = self.output / "正文_v1.0.0.md"
        current.write_text("old body\n", encoding="utf-8")
        vo.begin_revision(self.output, [current.name], "v1.0.1")
        candidate = self.output / "tmp" / "正文_v1.0.1.md"
        target = self.output / candidate.name
        original_unlink = pathlib.Path.unlink

        def interrupted_unlink(path, *args, **kwargs):
            if path == candidate:
                raise KeyboardInterrupt("simulated abrupt stop after link")
            return original_unlink(path, *args, **kwargs)

        with mock.patch.object(pathlib.Path, "unlink", interrupted_unlink):
            with self.assertRaises(KeyboardInterrupt):
                vo.finalize_revision(self.output)
        self.assertTrue(candidate.samefile(target))
        vo.finalize_revision(self.output)
        self.assertFalse(candidate.exists())
        self.assertEqual("old body\n", target.read_text(encoding="utf-8"))
        self.assertEqual("old body\n", (self.output / "old" / current.name).read_text(encoding="utf-8"))

    def test_conflicting_target_cannot_replace_a_missing_generated_candidate(self):
        current = self.output / "正文_v1.0.0.md"
        current.write_text("old body\n", encoding="utf-8")
        added = "报告_v1.0.1.resources"
        vo.begin_revision(self.output, [current.name], "v1.0.1", add_files=[added])
        occupied = self.output / added
        occupied.mkdir()
        (occupied / "keep.txt").write_text("user data\n", encoding="utf-8")
        with self.assertRaisesRegex(vo.VersionedOutputError, "禁止覆盖"):
            vo.finalize_revision(self.output)
        self.assertEqual("user data\n", (occupied / "keep.txt").read_text(encoding="utf-8"))
        self.assertTrue(current.is_file())
        self.assertFalse((self.output / "正文_v1.0.1.md").exists())

    def test_target_collision_after_preflight_does_not_overwrite(self):
        current = self.output / "正文_v1.0.0.md"
        current.write_text("old body\n", encoding="utf-8")
        vo.begin_revision(self.output, [current.name], "v1.0.1")
        target = self.output / "正文_v1.0.1.md"
        original_move = vo._move_without_overwrite

        def conflicting_move(source, destination):
            if destination == target:
                target.write_text("occupied after preflight\n", encoding="utf-8")
            return original_move(source, destination)

        with mock.patch.object(vo, "_move_without_overwrite", conflicting_move):
            with self.assertRaises(vo.VersionedOutputError):
                vo.finalize_revision(self.output)
        self.assertEqual("occupied after preflight\n", target.read_text(encoding="utf-8"))
        self.assertEqual("old body\n", current.read_text(encoding="utf-8"))
        self.assertTrue((self.output / "tmp" / target.name).is_file())
        with self.assertRaisesRegex(vo.VersionedOutputError, "同时存在"):
            vo.finalize_revision(self.output)
        target.unlink()
        self.assertEqual("FINALIZED", vo.finalize_revision(self.output)["status"])

    def test_resource_directory_collisions_after_preflight_preserve_both_groups(self):
        for location in ("published", "archived"):
            for empty in (True, False):
                with self.subTest(location=location, empty=empty):
                    output = pathlib.Path(self.temporary.name) / f"collision-{location}-{empty}"
                    output.mkdir()
                    old, new = self.prepare_group(output)
                    occupied = (
                        output / "稿件_v1.0.1.resources"
                        if location == "published"
                        else output / "old" / "稿件_v1.0.0.resources"
                    )
                    original_move = vo._move_without_overwrite

                    def conflicting_move(source, target):
                        if target == occupied:
                            occupied.mkdir()
                            if not empty:
                                (occupied / "keep.txt").write_bytes(b"user data")
                        return original_move(source, target)

                    with mock.patch.object(vo, "_move_without_overwrite", conflicting_move):
                        with self.assertRaises(vo.VersionedOutputError):
                            vo.finalize_revision(output)
                    self.assert_group(output, old)
                    self.assert_group(output / "tmp", new)
                    self.assertEqual(
                        [] if empty else ["keep.txt"],
                        [path.name for path in occupied.iterdir()],
                    )
                    if not empty:
                        self.assertEqual(b"user data", (occupied / "keep.txt").read_bytes())
                    with self.assertRaises(vo.VersionedOutputError):
                        vo.finalize_revision(output)
                    if not empty:
                        (occupied / "keep.txt").unlink()
                    occupied.rmdir()
                    vo.finalize_revision(output)
                    self.assert_group(output, new)
                    self.assert_group(output / "old", old)

    def test_directory_move_does_not_replace_an_existing_empty_target(self):
        source = self.output / "candidate.resources"
        target = self.output / "occupied.resources"
        source.mkdir()
        target.mkdir()
        (source / "keep.svg").write_bytes(b"complete resource")
        # Simulate an outdated existence check: the move itself must reject it.
        with mock.patch.object(vo, "_present", return_value=False):
            with self.assertRaises(FileExistsError):
                vo._move_without_overwrite(source, target)
        self.assertEqual(b"complete resource", (source / "keep.svg").read_bytes())
        self.assertEqual([], list(target.iterdir()))

    def test_directory_move_with_no_native_support_keeps_the_source(self):
        source = self.output / "candidate.resources"
        target = self.output / "new.resources"
        source.mkdir()
        (source / "keep.svg").write_bytes(b"complete resource")
        for platform in ("linux", "darwin"):
            with self.subTest(platform=platform):
                with (
                    mock.patch.object(vo.os, "name", "posix"),
                    mock.patch.object(vo.sys, "platform", platform),
                    mock.patch.object(vo.ctypes, "CDLL", return_value=object()),
                ):
                    with self.assertRaises(OSError) as raised:
                        vo._rename_directory_without_overwrite(source, target)
                self.assertEqual(errno.ENOTSUP, raised.exception.errno)
                self.assertEqual(b"complete resource", (source / "keep.svg").read_bytes())
                self.assertFalse(target.exists())

    def test_move_never_treats_a_late_symlink_as_a_recoverable_hardlink(self):
        source = self.output / "candidate.md"
        target = self.output / "occupied.md"
        source.write_bytes(b"only candidate copy")
        target.write_bytes(b"competing target")
        source_stat = source.lstat()
        original_lstat = pathlib.Path.lstat

        def lstat_with_competing_link(path, *args, **kwargs):
            if path == target:
                return mock.Mock(
                    st_mode=vo.stat.S_IFLNK | 0o777,
                    st_ino=source_stat.st_ino,
                    st_dev=source_stat.st_dev,
                )
            return original_lstat(path, *args, **kwargs)

        # A symlink to source makes samefile() true. Model that without requiring
        # symlink privileges, while the occupied path exercises the real move.
        with (
            mock.patch.object(pathlib.Path, "lstat", lstat_with_competing_link),
            mock.patch.object(pathlib.Path, "samefile", return_value=True),
        ):
            self.assertFalse(vo._same_file(source, target))
            with self.assertRaises(FileExistsError):
                vo._move_without_overwrite(source, target)
        self.assertEqual(b"only candidate copy", source.read_bytes())
        self.assertEqual(b"competing target", target.read_bytes())

    def test_inspect_rejects_corrupted_plan(self):
        vo.ensure_output_dir(self.output)
        plan_path = self.output / "tmp" / vo.PLAN_NAME
        plan_path.write_text("{not valid json\n", encoding="utf-8")
        with self.assertRaisesRegex(vo.VersionedOutputError, "无法读取版本候选计划"):
            vo.inspect_output(self.output)

    def test_inspect_rejects_unknown_plan_phase(self):
        current = self.output / "文稿_v1.0.0.md"
        current.write_text("old\n", encoding="utf-8")
        vo.begin_revision(self.output, [current.name], "v1.0.1")
        plan_path = self.output / "tmp" / vo.PLAN_NAME
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        plan["phase"] = "UNKNOWN"
        plan_path.write_text(
            json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        with self.assertRaisesRegex(vo.VersionedOutputError, "格式不受支持"):
            vo.inspect_output(self.output)

    def test_only_current_plan_schema_is_accepted_without_changing_files(self):
        old, new = self.prepare_group(self.output)
        plan_path = self.output / "tmp" / vo.PLAN_NAME
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        plan["schema"] = "unsupported-plan"
        plan_path.write_text(json.dumps(plan, ensure_ascii=False), encoding="utf-8")
        before = plan_path.read_bytes()
        for operation in (vo.inspect_output, vo.finalize_revision):
            with self.subTest(operation=operation.__name__):
                with self.assertRaisesRegex(vo.VersionedOutputError, "格式不受支持"):
                    operation(self.output)
                self.assert_group(self.output, old)
                self.assert_group(self.output / "tmp", new)
                self.assertEqual(before, plan_path.read_bytes())
                self.assertEqual([], list((self.output / "old").iterdir()))

    def test_plan_file_mappings_are_deterministic_and_unique(self):
        mutations = {
            "unrelated source": lambda plan, user: plan["files"][0].update(
                {"source": user.name, "archived": f"old/{user.name}"}
            ),
            "different target": lambda plan, _user: plan["files"][0].update(
                {
                    "candidate": "tmp/伪造_v1.0.1.md",
                    "target": "伪造_v1.0.1.md",
                }
            ),
            "duplicate row": lambda plan, _user: plan["files"].append(
                dict(plan["files"][0])
            ),
        }
        for index, (label, mutate) in enumerate(mutations.items()):
            with self.subTest(label=label):
                output = pathlib.Path(self.temporary.name) / f"mapping-{index}"
                output.mkdir()
                current = output / "正文_v1.0.0.md"
                user = output / "用户文件_v1.0.0.md"
                current.write_text("old body\n", encoding="utf-8")
                user.write_text("user data\n", encoding="utf-8")
                vo.begin_revision(output, [current.name], "v1.0.1")
                plan_path = output / "tmp" / vo.PLAN_NAME
                plan = json.loads(plan_path.read_text(encoding="utf-8"))
                mutate(plan, user)
                plan_path.write_text(
                    json.dumps(plan, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )
                with self.assertRaises(vo.VersionedOutputError):
                    vo.finalize_revision(output)
                self.assertEqual("old body\n", current.read_text(encoding="utf-8"))
                self.assertEqual("user data\n", user.read_text(encoding="utf-8"))
                self.assertTrue((output / "tmp" / "正文_v1.0.1.md").is_file())
                self.assertEqual([], list((output / "old").iterdir()))

    def test_finalize_rejects_candidate_directory_before_any_move(self):
        current = self.output / "正文_v1.0.0.md"
        current.write_text("old body\n", encoding="utf-8")
        vo.begin_revision(self.output, [current.name], "v1.0.1")
        candidate = self.output / "tmp" / "正文_v1.0.1.md"
        candidate.unlink()
        candidate.mkdir()

        with self.assertRaisesRegex(vo.VersionedOutputError, "不是普通文件"):
            vo.finalize_revision(self.output)
        self.assertEqual("old body\n", current.read_text(encoding="utf-8"))
        self.assertFalse((self.output / "正文_v1.0.1.md").exists())
        self.assertEqual([], list((self.output / "old").iterdir()))
        self.assertTrue((self.output / "tmp" / vo.PLAN_NAME).is_file())

        candidate.rmdir()
        candidate.write_text("new body\n", encoding="utf-8")
        result = vo.finalize_revision(self.output)
        self.assertEqual("FINALIZED", result["status"])

    def test_finalize_rejects_broken_symlink_targets_before_any_move(self):
        for index, location in enumerate(("target", "archived")):
            with self.subTest(location=location):
                output = pathlib.Path(self.temporary.name) / f"symlink-{index}"
                output.mkdir()
                current = output / "正文_v1.0.0.md"
                current.write_text("old body\n", encoding="utf-8")
                vo.begin_revision(output, [current.name], "v1.0.1")
                candidate = output / "tmp" / "正文_v1.0.1.md"
                link = (
                    output / "正文_v1.0.1.md"
                    if location == "target"
                    else output / "old" / current.name
                )
                try:
                    link.symlink_to(output / "不存在的目标")
                except OSError as error:
                    if error.errno in (errno.EACCES, errno.EPERM) or getattr(error, "winerror", None) == 1314:
                        self.skipTest("This environment does not permit creating symbolic links")
                    raise

                with self.assertRaisesRegex(vo.VersionedOutputError, "不是普通文件"):
                    vo.finalize_revision(output)
                self.assertTrue(link.is_symlink())
                self.assertEqual("old body\n", current.read_text(encoding="utf-8"))
                self.assertTrue(candidate.is_file())
                self.assertTrue((output / "tmp" / vo.PLAN_NAME).is_file())

    def test_finalize_move_failure_rolls_back_without_overwrite(self):
        first = self.output / "正文_v1.0.0.md"
        second = self.output / "附录_v1.0.0.md"
        first.write_text("old body\n", encoding="utf-8")
        second.write_text("old appendix\n", encoding="utf-8")
        vo.begin_revision(self.output, [first.name, second.name], "v1.0.1")
        original_move = vo._move_without_overwrite
        calls = 0

        def interrupted_move(path, target):
            nonlocal calls
            calls += 1
            if calls == 3:
                raise OSError("simulated interruption")
            return original_move(path, target)

        with mock.patch.object(vo, "_move_without_overwrite", interrupted_move):
            with self.assertRaises(vo.VersionedOutputError):
                vo.finalize_revision(self.output)

        for current in (first, second):
            self.assertTrue(current.is_file())
            self.assertFalse((self.output / "old" / current.name).exists())
        for candidate in ("正文_v1.0.1.md", "附录_v1.0.1.md"):
            self.assertTrue((self.output / "tmp" / candidate).is_file())
            self.assertFalse((self.output / candidate).exists())
        self.assertTrue((self.output / "tmp" / vo.PLAN_NAME).is_file())

    def test_dry_run_does_not_create_or_copy(self):
        current = self.output / "文稿_v1.0.0.md"
        current.write_text("old\n", encoding="utf-8")
        result = vo.begin_revision(self.output, [current.name], "v1.0.1", dry_run=True)
        self.assertTrue(result["dry_run"])
        self.assertFalse((self.output / "old").exists())
        self.assertFalse((self.output / "tmp").exists())


if __name__ == "__main__":
    unittest.main()
