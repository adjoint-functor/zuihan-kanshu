#!/usr/bin/env python3
"""Behavioral tests for the current versioned research workbench."""

from __future__ import annotations

import importlib.util
import json
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


REPOSITORY_ROOT = pathlib.Path(__file__).resolve().parents[1]
ROOT = REPOSITORY_ROOT / "skill" / "zuihan-kanshu"
SCRIPT = ROOT / "scripts" / "research-workbench.py"
SPEC = importlib.util.spec_from_file_location("research_workbench", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
rw = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(rw)


class ResearchWorkbenchTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.temporary.name)
        self.project = self.root / "project"

    def tearDown(self):
        self.temporary.cleanup()

    def make_symlink(self, source, target, **kwargs):
        try:
            source.symlink_to(target, **kwargs)
        except OSError as exc:
            if isinstance(exc, PermissionError) or getattr(exc, "winerror", None) == 1314:
                self.skipTest(f"Host does not permit creating symbolic links: {exc}")
            raise

    def init_research(self):
        rw.init_project(
            self.project,
            "测试项目",
            "研究一个尚未预设答案的数学问题。",
            [],
        )


    def current(self, role: str, version: str = "1.0.0") -> pathlib.Path:
        return self.project / f"测试项目_{role}_v{version}.md"

    def candidate(self, role: str, version: str = "1.0.1") -> pathlib.Path:
        return (
            self.project
            / "tmp"
            / rw.ACTIVE_REVISION_DIR
            / f"测试项目_{role}_v{version}.md"
        )

    def begin_and_log(self, bump: str = "patch"):
        payload = rw.begin_revision(self.project, bump)
        rw.append_log(
            self.project,
            "完成定义核对",
            ["数学主稿‘研究目标’；论文 P001 定理 1"],
            ["补充定义 1"],
            ["记号采用 A；路线 B 与反例冲突"],
            ["论文 P001 的具体应用仍待验证"],
        )
        return payload

    def publish_round(
        self,
        round_type: str = "substantive",
        bump: str = "patch",
        *,
        readings: list[str] | None = None,
        review_outcome: str | None = None,
    ):
        payload = rw.begin_revision(self.project, bump, round_type)
        rw.append_log(
            self.project,
            f"发布{rw.ROUND_TYPES[round_type]}",
            readings or [],
            [],
            [],
            ["继续核对"],
            review_outcome,
        )
        return payload, rw.finalize_revision(self.project)

    def test_init_creates_shared_v100_files_and_required_directories(self):
        self.init_research()
        expected = {
            f"测试项目_{role}_v1.0.0.md" for role in rw.CORE_ROLES
        }
        self.assertEqual(expected, {path.name for path in self.project.glob("*.md")})
        self.assertEqual(("download", "old", "tmp"), rw.PROJECT_DIRS)
        for dirname in rw.PROJECT_DIRS:
            self.assertTrue((self.project / dirname).is_dir())
        self.assertEqual([], rw.validate_project(self.project))
        main = self.current("数学主稿").read_text(encoding="utf-8")
        self.assertIn("研究一个尚未预设答案的数学问题。", main)
        self.assertIn("- 项目版本：v1.0.0", main)
        self.assertNotIn("- 当前文件：", main)
        self.assertNotIn("研究日志", main)
        self.assertIn("## 条件性结果", main)
        self.assertIn("## 当前研究前沿与数学依赖", main)
        established = main.split("## 已建立的数学内容", 1)[1].split(
            "## 条件性结果", 1
        )[0]
        self.assertNotIn("条件性结果", established)

        entry = self.current("下一次入口").read_text(encoding="utf-8")
        self.assertIn("- 项目版本：v1.0.0", entry)
        for filename in expected:
            self.assertIn(f"`{filename}`", entry)



    def test_existing_project_lifecycle_does_not_read_initial_templates(self):
        self.init_research()
        original_log = self.current("研究日志").read_bytes()
        with mock.patch.object(rw, "_render_template", side_effect=AssertionError("unexpected template read")):
            entry = json.loads(rw.prepare_session(self.project, "json"))
            self.assertIn("测试项目_数学主稿_v1.0.0.md", entry["entry_text"])
            self.begin_and_log()
            self.assertEqual([], rw.validate_project(self.project, candidate=True))
            rw.finalize_revision(self.project)
            self.assertEqual([], rw.validate_project(self.project))
            self.assertTrue(self.current("研究日志", "1.0.1").read_bytes().startswith(original_log))
            self.assertEqual(5, len(list((self.project / "old").glob("*.md"))))

    def test_common_mathematical_angle_brackets_are_not_html(self):
        for index, goal in enumerate(
            (
                "研究向量 <x,y> 的内积。",
                "研究生成子群 <g,h>。",
                "研究序列 <x_n> 的极限。",
                "研究算子 <T^n x>。",
            )
        ):
            with self.subTest(goal=goal):
                project = self.root / f"angle-goal-{index}"
                rw.init_project(project, "角括号数学", goal, [])
                self.assertEqual([], rw.validate_project(project))


    def test_project_name_and_purpose_prose_do_not_trigger_broad_locator_scan(self):
        rw.init_project(
            self.project,
            "全文分析",
            "研究一个有界问题。",
            [],
        )
        entry = self.project / "全文分析_下一次入口_v1.0.0.md"
        entry.write_text(
            entry.read_text(encoding="utf-8").replace(
                "：核对总目标与唯一状态迁移。",
                "：无需阅读全稿，只核对总目标与唯一状态迁移。",
                1,
            ),
            encoding="utf-8",
        )
        self.assertEqual([], rw.validate_project(self.project))

    def test_ordinary_markdown_is_allowed_and_does_not_block_init(self):
        self.project.mkdir()
        source = self.project / "用户原始研究报告.md"
        source.write_text("普通参考稿，不是研究五文件。\n", encoding="utf-8")
        self.init_research()
        self.assertEqual("普通参考稿，不是研究五文件。\n", source.read_text(encoding="utf-8"))
        self.assertEqual([], rw.validate_project(self.project))

    def test_init_rejects_existing_research_role_files(self):
        self.project.mkdir()
        existing = self.project / "数学主稿.md"
        existing.write_text("用户内容\n", encoding="utf-8")
        with self.assertRaises(rw.WorkbenchError):
            self.init_research()
        self.assertEqual("用户内容\n", existing.read_text(encoding="utf-8"))

        existing.rename(self.project / "任意项目_数学主稿_v3.2.1.md")
        with self.assertRaises(rw.WorkbenchError):
            self.init_research()

    def test_validate_reports_missing_directory_and_current_role(self):
        self.init_research()
        (self.project / "download").rmdir()
        self.current("计算草稿").unlink()
        issues = rw.validate_project(self.project)
        self.assertTrue(any("download/" in issue for issue in issues))
        self.assertTrue(any("计算草稿" in issue for issue in issues))

    def test_validate_rejects_two_current_versions(self):
        self.init_research()
        shutil.copyfile(
            self.current("数学主稿"), self.current("数学主稿", "1.0.1")
        )
        issues = rw.validate_project(self.project)
        self.assertTrue(any("只保留一套同版本" in issue for issue in issues))



    def test_long_entry_preserves_plan_conditions_without_length_gate(self):
        self.init_research()
        entry = self.current("下一次入口")
        conditions = "\n".join(f"- 情形 {i}：使用时保留当前参数条件。" for i in range(100))
        plan = "阶段目标：完成全部参数分类。\n" + conditions + "\n最后一项：分类完成后停止。"
        entry.write_text(rw._replace_section(entry.read_text(), "当前近期计划", plan))
        rw.begin_revision(self.project)
        payload = json.loads(rw.prepare_session(self.project, "json"))
        self.assertIn(plan, payload["entry_text"])
        rw.append_log(self.project, "保留必要入口信息", [], [], [], ["继续研究"])
        warnings = []
        self.assertEqual([], rw.validate_project(self.project, candidate=True, warnings=warnings))
        self.assertEqual([], warnings)
        result = rw.finalize_revision(self.project)
        self.assertEqual("1.0.1", result["current_version"])
        self.assertEqual([], result["warnings"])
        self.assertIn(plan, rw.prepare_session(self.project, "markdown"))

    def test_research_prose_is_not_classified_by_keywords(self):
        self.init_research()
        main = self.current("数学主稿")
        main.write_text(main.read_text() + "\n这里研究日志函数的迭代，不是流程指令。\n")
        self.assertEqual([], rw.validate_project(self.project))

    def test_computational_terms_are_not_misclassified_as_process_noise(self):
        self.init_research()
        path = self.current("数学主稿")
        path.write_text(
            path.read_text(encoding="utf-8")
            + "\n## 运行结果\n\n模型输出的误差上界为 $10^{-6}$。\n",
            encoding="utf-8",
        )
        self.assertEqual([], rw.validate_project(self.project))


    def test_scratch_accepts_existing_organization_without_fixed_fields(self):
        self.init_research()
        scratch = self.current("计算草稿")
        text = scratch.read_text().replace("## 当前问题包", "## 本题的已知条件")
        scratch.write_text(text + "\n## 第三轮研究\n\n保留的一段旧推导。\n")
        entry = self.current("下一次入口")
        entry.write_text(entry.read_text().replace("`## 当前问题包`", "`## 本题的已知条件`"))
        self.assertEqual([], rw.validate_project(self.project))
        self.begin_and_log()
        self.assertEqual("1.0.1", rw.finalize_revision(self.project)["current_version"])

    def test_structured_anchors_are_checked_and_free_reading_notes_are_allowed(self):
        self.init_research()
        path = self.current("下一次入口")
        base = path.read_text()
        path.write_text(base.replace("→ `## 研究目标`：恢复总体问题与完成尺度", "：按当前问题查阅主稿相关部分", 1))
        self.assertEqual([], rw.validate_project(self.project))
        path.write_text(base.replace("`## 研究目标`", "`## 不存在的标题`", 1))
        self.assertTrue(any("定位的锚点" in i for i in rw.validate_project(self.project)))
        path.write_text(rw._replace_section(base, "必要读取", "- `download/needed.pdf` → 第 3 页：读取原始条件"))
        warnings = []
        self.assertEqual([], rw.validate_project(self.project, warnings=warnings))
        self.assertTrue(any("needed.pdf" in i for i in warnings))
        other = self.project / "other.md"
        other.write_text("# 文献摘录\n\n## 已有结果\n\n条件完整。\n")
        path.write_text(rw._replace_section(base, "必要读取", "- `other.md` → `## 不存在`：查找条件"))
        self.assertTrue(any("定位的锚点" in i for i in rw.validate_project(self.project)))

    def test_reading_purpose_and_expansion_notes_are_free_prose(self):
        self.init_research()
        entry = self.current("下一次入口")
        entry.write_text(entry.read_text().replace("恢复总体问题与完成尺度", "Decide whether the available hypotheses fit the current goal"))
        self.assertEqual([], rw.validate_project(self.project))
        self.assertNotIn("## 扩读条件", entry.read_text())
        self.begin_and_log()
        rw.finalize_revision(self.project)


    def test_entry_anchor_cannot_resolve_only_inside_a_fenced_block(self):
        self.init_research()
        main = self.current("数学主稿")
        main.write_text(
            main.read_text(encoding="utf-8")
            + "\n```markdown\n## 围栏内伪锚点\n```\n",
            encoding="utf-8",
        )
        entry = self.current("下一次入口")
        entry.write_text(
            entry.read_text(encoding="utf-8").replace(
                "`## 研究目标`", "`## 围栏内伪锚点`", 1
            ),
            encoding="utf-8",
        )
        self.assertTrue(
            any("没有可在目标文件中定位" in issue for issue in rw.validate_project(self.project))
        )


    def test_entry_anchor_cannot_resolve_only_inside_an_html_comment(self):
        self.init_research()
        main = self.current("数学主稿")
        main.write_text(
            main.read_text(encoding="utf-8")
            + "\n<!--\n## 注释内伪锚点\n-->\n",
            encoding="utf-8",
        )
        entry = self.current("下一次入口")
        entry.write_text(
            entry.read_text(encoding="utf-8").replace(
                "`## 研究目标`", "`## 注释内伪锚点`", 1
            ),
            encoding="utf-8",
        )
        self.assertTrue(
            any(
                "没有可在目标文件中定位" in issue
                for issue in rw.validate_project(self.project)
            )
        )

    def test_entry_anchor_cannot_resolve_only_inside_raw_html(self):
        for index, (opening, closing) in enumerate(
            (
                ("<pre>", "</pre>"),
                ('<script type="text/plain">', "</script>"),
                ("<style>", "</style>"),
            )
        ):
            with self.subTest(opening=opening):
                project = self.root / f"raw-anchor-{index}"
                rw.init_project(project, "原始块锚点", "检查锚点。", [])
                main = project / "原始块锚点_数学主稿_v1.0.0.md"
                main.write_text(
                    main.read_text(encoding="utf-8")
                    + f"\n{opening}\n## 原始块内伪锚点\n{closing}\n",
                    encoding="utf-8",
                )
                entry = project / "原始块锚点_下一次入口_v1.0.0.md"
                entry.write_text(
                    entry.read_text(encoding="utf-8").replace(
                        "`## 研究目标`", "`## 原始块内伪锚点`", 1
                    ),
                    encoding="utf-8",
                )
                self.assertTrue(
                    any(
                        "没有可在目标文件中定位" in issue
                        for issue in rw.validate_project(project)
                    )
                )

    def test_target_anchor_cannot_resolve_inside_commonmark_raw_html_blocks(self):
        fragments = (
            "</div>\n## 隐藏伪锚点\n不是可见标题",
            "<span>\n## 隐藏伪锚点\n不是可见标题",
            "</span>\n## 隐藏伪锚点\n不是可见标题",
        )
        for index, fragment in enumerate(fragments):
            with self.subTest(fragment=fragment.splitlines()[0]):
                project = self.root / f"commonmark-anchor-{index}"
                rw.init_project(project, "原始块目标", "检查目标锚点。", [])
                main = project / "原始块目标_数学主稿_v1.0.0.md"
                main.write_text(
                    main.read_text(encoding="utf-8") + fragment + "\n",
                    encoding="utf-8",
                )
                entry = project / "原始块目标_下一次入口_v1.0.0.md"
                entry.write_text(
                    entry.read_text(encoding="utf-8").replace(
                        "`## 研究目标`", "`## 隐藏伪锚点`", 1
                    ),
                    encoding="utf-8",
                )
                self.assertTrue(
                    any(
                        "没有可在目标文件中定位" in issue
                        for issue in rw.validate_project(project)
                    )
                )

    def test_prose_denial_does_not_create_a_structured_theorem_anchor(self):
        self.init_research()
        main = self.current("数学主稿")
        main.write_text(
            main.read_text(encoding="utf-8")
            + "\n这里仅说明并不存在定理 999，也没有为其编号。\n",
            encoding="utf-8",
        )
        entry = self.current("下一次入口")
        entry.write_text(
            entry.read_text(encoding="utf-8").replace(
                "`## 研究目标`", "定理 999", 1
            ),
            encoding="utf-8",
        )
        self.assertTrue(
            any(
                "没有可在目标文件中定位" in issue
                for issue in rw.validate_project(self.project)
            )
        )

    def test_structured_anchor_numbers_require_an_exact_token_boundary(self):
        self.init_research()
        main = self.current("数学主稿")
        main.write_text(
            main.read_text(encoding="utf-8")
            + "\n定理 9999：这是唯一的不同编号。\n",
            encoding="utf-8",
        )
        entry = self.current("下一次入口")
        entry.write_text(
            entry.read_text(encoding="utf-8").replace(
                "`## 研究目标`", "定理 999", 1
            ),
            encoding="utf-8",
        )
        self.assertTrue(
            any(
                "没有可在目标文件中定位" in issue
                for issue in rw.validate_project(self.project)
            )
        )

        main.write_text(
            self.current("数学主稿").read_text(encoding="utf-8")
            + "\n公式 (2)：$x=y$。\n",
            encoding="utf-8",
        )
        entry.write_text(
            self.current("下一次入口").read_text(encoding="utf-8").replace(
                "定理 999", "公式 (1)", 1
            ),
            encoding="utf-8",
        )
        self.assertTrue(
            any(
                "没有可在目标文件中定位" in issue
                for issue in rw.validate_project(self.project)
            )
        )



    def test_reorganized_mathematics_publishes_with_updated_real_locators(self):
        self.init_research()
        old_main = self.current("数学主稿").read_bytes()
        rw.begin_revision(self.project)
        candidate = self.candidate("数学主稿")
        text = (
            "# 测试项目：数学主稿\n\n- 项目版本：v1.0.1\n\n"
            "## 问题与范围\n\n研究实数平方的非负性及其应用。\n\n"
            "## 平方非负\n\n对实数 x，有 x²≥0，因为两个同号实数之积非负。\n\n"
            "## 应用的未决前提\n\n拟取 x=a；a 是否为实数尚待确认。\n"
        )
        candidate.write_text(text, encoding="utf-8")
        rw.append_log(self.project, "按实际论证重组主稿", [], [], [], ["确认 a 的定义域"])
        issues = rw.validate_project(self.project, candidate=True)
        self.assertTrue(issues, "stale entry locator should still block publication")
        with self.assertRaises(rw.WorkbenchError):
            rw.finalize_revision(self.project)
        entry = self.candidate("下一次入口")
        entry.write_text(
            entry.read_text(encoding="utf-8").replace("`## 研究目标`", "`## 问题与范围`"),
            encoding="utf-8",
        )
        self.assertEqual([], rw.validate_project(self.project, candidate=True))
        self.assertEqual("1.0.1", rw.finalize_revision(self.project)["current_version"])
        self.assertEqual(text, self.current("数学主稿", "1.0.1").read_text(encoding="utf-8"))
        self.assertEqual(old_main, (self.project / "old" / "测试项目_数学主稿_v1.0.0.md").read_bytes())

    def test_entry_project_identity_and_calendar_date_are_validated(self):
        self.init_research()
        entry = self.current("下一次入口")
        base = entry.read_text(encoding="utf-8")
        entry.write_text(base.replace("- 项目：测试项目", "- 项目：其他项目"), encoding="utf-8")
        self.assertTrue(any("项目应为" in issue for issue in rw.validate_project(self.project)))

        entry.write_text(
            re.sub(r"(?m)^- 最近更新：.*$", "- 最近更新：2026-02-30", base),
            encoding="utf-8",
        )
        self.assertTrue(any("合法 YYYY-MM-DD" in issue for issue in rw.validate_project(self.project)))

        with mock.patch.object(rw, "_today", return_value="2026-08-20"):
            entry.write_text(
                re.sub(r"(?m)^- 最近更新：.*$", "- 最近更新：2099-01-01", base),
                encoding="utf-8",
            )
            self.assertTrue(any("不得晚于" in issue for issue in rw.validate_project(self.project)))
            prepared = rw.begin_revision(self.project)
        self.assertEqual("READY", prepared["status"])

    def test_duplicate_entry_identity_and_mismatched_titles_are_rejected(self):
        self.init_research()
        entry = self.current("下一次入口")
        entry.write_text(
            entry.read_text(encoding="utf-8")
            + "\n- 项目：其他项目\n- 最近更新：2099-01-01\n",
            encoding="utf-8",
        )
        issues = rw.validate_project(self.project)
        self.assertTrue(any("“项目”字段只能出现一次" in issue for issue in issues))
        self.assertTrue(any("“最近更新”字段只能出现一次" in issue for issue in issues))

        entry.write_text(
            entry.read_text(encoding="utf-8").replace(
                "# 测试项目：下一次入口", "# 其他项目：下一次入口"
            ),
            encoding="utf-8",
        )
        main = self.current("数学主稿")
        main.write_text(
            main.read_text(encoding="utf-8").replace(
                "# 测试项目：数学主稿", "# 其他项目：数学主稿"
            ),
            encoding="utf-8",
        )
        issues = rw.validate_project(self.project)
        self.assertTrue(any("一级标题必须绑定项目" in issue for issue in issues))

    def test_visible_metadata_is_the_metadata_updated_during_begin_revision(self):
        for index, role in enumerate(("数学主稿", "计算草稿")):
            with self.subTest(role=role):
                project = self.root / f"visible-metadata-{index}"
                rw.init_project(project, "可见元数据", "检查可见字段。", [])
                path = project / f"可见元数据_{role}_v1.0.0.md"
                text = path.read_text(encoding="utf-8")
                first_line_end = text.index("\n") + 1
                path.write_text(
                    text[:first_line_end]
                    + "\n```text\n- 项目版本：v9.9.9\n```\n"
                    + text[first_line_end:],
                    encoding="utf-8",
                )
                self.assertEqual([], rw.validate_project(project))
                rw.begin_revision(project)
                candidate = (
                    project
                    / "tmp"
                    / rw.ACTIVE_REVISION_DIR
                    / f"可见元数据_{role}_v1.0.1.md"
                )
                self.assertEqual(
                    "v1.0.1",
                    rw._metadata_value(candidate.read_text(encoding="utf-8"), "项目版本"),
                )

        project = self.root / "entry-hidden-metadata"
        rw.init_project(project, "入口控制语法", "检查入口控制语法。", [])
        entry = project / "入口控制语法_下一次入口_v1.0.0.md"
        text = entry.read_text(encoding="utf-8")
        entry.write_text(
            text + "\n```text\n- 项目版本：v9.9.9\n```\n",
            encoding="utf-8",
        )
        self.assertEqual([], rw.validate_project(project))
        self.assertEqual("v1.0.0", rw._metadata_value(entry.read_text(), "项目版本"))

    def test_calculation_scratch_can_remove_obsolete_material_before_publish(self):
        self.init_research()
        current = self.current("计算草稿")
        marker = "应在下一版整理掉的机械输出"
        current.write_text(
            current.read_text(encoding="utf-8") + f"\n{marker}\n",
            encoding="utf-8",
        )
        rw.begin_revision(self.project)
        candidate = self.candidate("计算草稿")
        candidate.write_text(
            candidate.read_text(encoding="utf-8").replace(marker, ""),
            encoding="utf-8",
        )
        rw.append_log(self.project, "整理当前工作集", [], [], [], ["继续计算"])
        rw.finalize_revision(self.project)
        self.assertNotIn(
            marker,
            self.current("计算草稿", "1.0.1").read_text(encoding="utf-8"),
        )

    def test_validate_rejects_current_file_metadata_in_clean_main(self):
        self.init_research()
        path = self.current("数学主稿")
        text = path.read_text(encoding="utf-8")
        path.write_text(
            text.replace(
                "- 项目版本：v1.0.0",
                "- 项目版本：v1.0.0\n- 当前文件：`测试项目_数学主稿_v1.0.0.md`",
            ),
            encoding="utf-8",
        )
        issues = rw.validate_project(self.project)
        self.assertTrue(any("数学主稿不得包含" in issue for issue in issues))



    def test_candidate_validation_is_explicit_read_only_and_checks_ready_to_finalize(self):
        self.init_research()
        rw.begin_revision(self.project)
        self.assertTrue(
            any("尚未追加" in issue for issue in rw.validate_project(self.project, candidate=True))
        )
        rw.append_log(self.project, "完成候选修改", [], [], [], ["继续研究"])
        main = self.candidate("数学主稿")
        valid_main = main.read_text(encoding="utf-8")
        main.write_text(valid_main.replace("v1.0.1", "v9.9.9"), encoding="utf-8")
        before = {
            path.relative_to(self.project): path.read_bytes()
            for path in self.project.rglob("*") if path.is_file()
        }
        self.assertEqual([], rw.validate_project(self.project))
        self.assertTrue(
            any("版本" in issue for issue in rw.validate_project(self.project, candidate=True))
        )
        for candidate, expected_return, target in ((False, 0, "published"), (True, 1, "candidate")):
            command = [sys.executable, str(SCRIPT), "validate-project", str(self.project), "--json"]
            if candidate:
                command.append("--candidate")
            result = subprocess.run(command, capture_output=True, text=True, check=False)
            self.assertEqual(expected_return, result.returncode, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(target, payload["target"])
            self.assertEqual("local-filesystem", payload["storage_scope"])
            self.assertIn("warnings", payload)
        after = {
            path.relative_to(self.project): path.read_bytes()
            for path in self.project.rglob("*") if path.is_file()
        }
        self.assertEqual(before, after)
        main.write_text(valid_main, encoding="utf-8")
        self.assertEqual([], rw.validate_project(self.project, candidate=True))
        self.assertEqual("1.0.1", rw.finalize_revision(self.project)["current_version"])

    def test_begin_revision_copies_all_files_and_keeps_root_unchanged(self):
        self.init_research()
        before = {
            role: self.current(role).read_text(encoding="utf-8")
            for role in rw.CORE_ROLES
        }
        payload = rw.begin_revision(self.project, "minor")
        self.assertEqual("1.1.0", payload["new_version"])
        for role in rw.CORE_ROLES:
            self.assertTrue(self.candidate(role, "1.1.0").is_file())
            self.assertEqual(before[role], self.current(role).read_text(encoding="utf-8"))
        entry = self.candidate("下一次入口", "1.1.0").read_text(encoding="utf-8")
        self.assertIn("- 项目版本：v1.1.0", entry)
        self.assertNotIn("_v1.0.0.md", entry)
        candidate_main = self.candidate("数学主稿", "1.1.0").read_text(
            encoding="utf-8"
        )
        self.assertIn("- 项目版本：v1.1.0", candidate_main)
        self.assertNotIn("- 当前文件：", candidate_main)
        repeated = rw.begin_revision(self.project, "minor")
        self.assertEqual("READY", repeated["status"])
        self.assertEqual(list(rw.CORE_ROLES), repeated["completed_roles"])

    def test_begin_revision_resumes_after_candidate_copy_interruption(self):
        self.init_research()
        real_copy = rw.shutil.copyfileobj
        calls = 0
        saw_preparing_before_copy = False

        def interrupted_copy(source, destination, *args, **kwargs):
            nonlocal calls, saw_preparing_before_copy
            calls += 1
            revision_record = json.loads(
                (
                    self.project
                    / "tmp"
                    / rw.ACTIVE_REVISION_DIR
                    / rw.REVISION_RECORD_FILE
                ).read_text(encoding="utf-8")
            )
            saw_preparing_before_copy = saw_preparing_before_copy or (
                revision_record["status"] == "PREPARING"
            )
            if calls == 3:
                raise OSError("模拟候选复制中断")
            return real_copy(source, destination, *args, **kwargs)

        with mock.patch.object(rw.shutil, "copyfileobj", new=interrupted_copy):
            with self.assertRaisesRegex(rw.WorkbenchError, "可再次运行 begin-revision"):
                rw.begin_revision(self.project)
        self.assertTrue(saw_preparing_before_copy)
        record_path = (
            self.project
            / "tmp"
            / rw.ACTIVE_REVISION_DIR
            / rw.REVISION_RECORD_FILE
        )
        preparing = json.loads(record_path.read_text(encoding="utf-8"))
        self.assertEqual(
            {
                "status",
                "completed_roles",
                "project",
                "base_version",
                "new_version",
                "base_files",
                "candidate_files",
                "round_type",
            },
            set(preparing),
        )
        self.assertEqual("PREPARING", preparing["status"])
        self.assertEqual(list(rw.CORE_ROLES[:2]), preparing["completed_roles"])
        for role in rw.CORE_ROLES:
            self.assertTrue(self.current(role).is_file())

        resumed = rw.begin_revision(self.project)
        self.assertEqual("READY", resumed["status"])
        self.assertEqual(list(rw.CORE_ROLES), resumed["completed_roles"])
        candidate = rw._candidate_state(self.project)
        self.assertEqual("1.0.1", candidate.version)
        self.assertEqual([], rw._validate_state_content(candidate))

    def test_resume_rejects_symlinked_partial_and_record_staging_files(self):
        for index, staging_kind in enumerate(("partial", "record-next")):
            with self.subTest(staging_kind=staging_kind):
                case = self.root / f"staging-link-{index}"
                rw.init_project(case, "分期路径", "检查内部分期文件。", [])
                with mock.patch.object(
                    rw.shutil, "copyfileobj", side_effect=OSError("模拟首次复制中断")
                ):
                    with self.assertRaises(rw.WorkbenchError):
                        rw.begin_revision(case)

                active = case / "tmp" / rw.ACTIVE_REVISION_DIR
                external = self.root / f"staging-sentinel-{index}.txt"
                external.write_text("不得改写\n", encoding="utf-8")
                if staging_kind == "partial":
                    staging = active / "分期路径_数学主稿_v1.0.1.md.partial"
                    self.assertTrue(staging.is_file())
                    staging.unlink()
                    expected_message = "候选临时路径"
                else:
                    staging = active / (rw.REVISION_RECORD_FILE + ".next")
                    expected_message = "升版说明的临时路径"
                self.make_symlink(staging, external)

                with self.assertRaisesRegex(rw.WorkbenchError, expected_message):
                    rw.begin_revision(case)
                self.assertEqual("不得改写\n", external.read_text(encoding="utf-8"))

    def test_append_log_changes_only_candidate_and_preserves_prefix(self):
        self.init_research()
        rw.begin_revision(self.project)
        current_log = self.current("研究日志")
        candidate_log = self.candidate("研究日志")
        before = current_log.read_text(encoding="utf-8")
        rw.append_log(
            self.project,
            "完成定义核对",
            [],
            ["补充定义 1"],
            [],
            ["继续验证"],
        )
        after = candidate_log.read_text(encoding="utf-8")
        self.assertEqual(before, current_log.read_text(encoding="utf-8"))
        self.assertTrue(after.startswith(before))
        self.assertIn("完成定义核对", after[len(before) :])

    def test_append_log_refuses_a_second_record_without_changing_the_candidate(self):
        self.init_research()
        rw.begin_revision(self.project)
        rw.append_log(self.project, "第一条候选记录", [], [], [], ["继续核对"])
        log = self.candidate("研究日志")
        before = log.read_text(encoding="utf-8")
        with self.assertRaisesRegex(rw.WorkbenchError, "不得再次追加"):
            rw.append_log(self.project, "第二条", [], [], [], ["不应写入"])
        self.assertEqual(before, log.read_text(encoding="utf-8"))

    def test_finalize_requires_log_append_and_rejects_log_rewrite(self):
        self.init_research()
        rw.begin_revision(self.project)
        with self.assertRaisesRegex(rw.WorkbenchError, "尚未追加"):
            rw.finalize_revision(self.project)
        log = self.candidate("研究日志")
        log.write_text("改写旧日志\n", encoding="utf-8")
        with self.assertRaisesRegex(rw.WorkbenchError, "只能在原文末尾追加"):
            rw.finalize_revision(self.project)
        self.assertTrue(self.current("研究日志").is_file())

    def test_finalize_requires_one_valid_dated_log_record(self):
        cases = {
            "invalid-date": (
                "\n## 2026-02-30｜非法日期\n\n- 本次目标与结果：测试。\n",
                "合法日历日期",
            ),
            "two-records": (
                "\n## 2026-08-19｜记录一\n\n- 本次目标与结果：一。\n"
                "\n## 2026-08-20｜记录二\n\n- 本次目标与结果：二。\n",
                "只能追加一条",
            ),
        }
        for index, (label, (suffix, expected)) in enumerate(cases.items()):
            with self.subTest(label=label):
                project = self.root / f"log-case-{index}"
                rw.init_project(project, "日志项目", "检查发布日志。", [])
                rw.begin_revision(project)
                log = (
                    project
                    / "tmp"
                    / rw.ACTIVE_REVISION_DIR
                    / "日志项目_研究日志_v1.0.1.md"
                )
                log.write_text(
                    log.read_text(encoding="utf-8") + suffix, encoding="utf-8"
                )
                with self.assertRaisesRegex(rw.WorkbenchError, expected):
                    rw.finalize_revision(project)

    def test_finalize_rejects_a_heading_only_or_category_free_log_record(self):
        cases = {
            "heading-only": "\n## 2026-08-20｜只有标题\n",
            "no-category": (
                "\n## 2026-08-20｜只有目标\n\n"
                "- 本次目标与结果：完成一项检查。\n"
            ),
        }
        for index, (label, suffix) in enumerate(cases.items()):
            with self.subTest(label=label):
                project = self.root / f"log-body-{index}"
                rw.init_project(project, "日志正文", "检查日志正文。", [])
                rw.begin_revision(project)
                log = (
                    project
                    / "tmp"
                    / rw.ACTIVE_REVISION_DIR
                    / "日志正文_研究日志_v1.0.1.md"
                )
                log.write_text(log.read_text(encoding="utf-8") + suffix, encoding="utf-8")
                with self.assertRaisesRegex(rw.WorkbenchError, "目标与结果|至少需要一项"):
                    rw.finalize_revision(project)

    def test_finalize_rejects_log_body_hidden_in_noncontent_blocks(self):
        wrappers = {
            "comment": ("<!--", "-->"),
            "fence": ("```text", "```"),
            "script": ('<script type="text/plain">', "</script>"),
            "cdata": ('<![CDATA[', ']]>'),
            "processing": ("<?opaque", "?>"),
            "declaration": ("<!DOCTYPE opaque [", "]>"),
            "div": ("<div>", "</div>"),
        }
        for index, (label, (opening, closing)) in enumerate(wrappers.items()):
            with self.subTest(label=label):
                project = self.root / f"hidden-log-body-{index}"
                rw.init_project(project, "隐藏日志", "检查可见日志。", [])
                rw.begin_revision(project)
                log = (
                    project
                    / "tmp"
                    / rw.ACTIVE_REVISION_DIR
                    / "隐藏日志_研究日志_v1.0.1.md"
                )
                log.write_text(
                    log.read_text(encoding="utf-8")
                    + f"\n## {rw._today()}｜可见标题\n\n{opening}\n"
                    + "- 本次目标与结果：隐藏内容。\n- 未决：隐藏内容。\n"
                    + f"{closing}\n",
                    encoding="utf-8",
                )
                with self.assertRaisesRegex(
                    rw.WorkbenchError, "目标与结果|至少需要一项"
                ):
                    rw.finalize_revision(project)

    def test_finalize_rejects_text_outside_the_single_new_log_record(self):
        self.init_research()
        rw.begin_revision(self.project)
        log = self.candidate("研究日志")
        log.write_text(
            log.read_text(encoding="utf-8")
            + f"\n游离于日期记录的文本。\n\n## {rw._today()}｜合法标题\n\n"
            + "- 本次目标与结果：核对日志归属。\n"
            + "- 未决：\n  - 继续。\n",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(rw.WorkbenchError, "全部属于唯一日期记录"):
            rw.finalize_revision(self.project)

    def test_new_log_date_cannot_move_backward(self):
        self.init_research()
        with mock.patch.object(rw, "_today", return_value="2026-08-20"):
            self.begin_and_log()
            rw.finalize_revision(self.project)
        with mock.patch.object(rw, "_today", return_value="2026-08-21"):
            rw.begin_revision(self.project)
        log = self.candidate("研究日志", "1.0.2")
        log.write_text(
            log.read_text(encoding="utf-8")
            + "\n## 2026-08-19｜倒退日期\n\n- 本次目标与结果：测试。\n",
            encoding="utf-8",
        )
        with mock.patch.object(rw, "_today", return_value="2026-08-21"):
            with self.assertRaisesRegex(rw.WorkbenchError, "早于上一条"):
                rw.finalize_revision(self.project)

    def test_future_log_date_can_be_corrected_and_published_later(self):
        self.init_research()
        log = self.current("研究日志")
        log.write_text(
            log.read_text(encoding="utf-8")
            + "\n## 2099-01-01｜旧记录误写为未来日期\n\n"
            + "- 本次目标与结果：保留历史。\n"
            + "- 轮次类型：规范维护轮\n"
            + "- 未决：\n  - 日期待勘误。\n",
            encoding="utf-8",
        )
        with mock.patch.object(rw, "_today", return_value="2026-08-20"):
            rw.begin_revision(self.project)
            rw.append_log(
                self.project,
                "日期勘误：记录实际发布日",
                [],
                [],
                [],
                ["旧记录保持不变"],
            )
        with mock.patch.object(rw, "_today", return_value="2026-08-21"):
            result = rw.finalize_revision(self.project)
        self.assertEqual("1.0.1", result["current_version"])

    def test_future_date_correction_remains_valid_after_delayed_finalize(self):
        self.init_research()
        log = self.current("研究日志")
        log.write_text(
            log.read_text(encoding="utf-8")
            + "\n## 2026-08-21｜旧记录误写为次日\n\n"
            + "- 本次目标与结果：保留历史。\n"
            + "- 轮次类型：规范维护轮\n"
            + "- 未决：\n  - 日期待勘误。\n",
            encoding="utf-8",
        )
        with mock.patch.object(rw, "_today", return_value="2026-08-20"):
            rw.begin_revision(self.project)
            rw.append_log(
                self.project,
                "日期勘误：记录实际追加日",
                [],
                [],
                [],
                ["旧记录保持不变"],
            )
        with mock.patch.object(rw, "_today", return_value="2026-08-22"):
            result = rw.finalize_revision(self.project)
        self.assertEqual("1.0.1", result["current_version"])

    def test_past_log_date_cannot_be_mislabelled_as_a_future_date_correction(self):
        old_text = (
            "# 日志\n\n## 2026-08-10｜既有记录\n\n"
            "- 本次目标与结果：既有。\n- 未决：继续。\n"
        )
        new_text = (
            old_text
            + "\n## 2026-08-09｜日期勘误：故意倒退\n\n"
            + "- 本次目标与结果：倒退。\n- 未决：继续。\n"
        )
        with mock.patch.object(rw, "_today", return_value="2026-08-20"):
            issues = rw._validate_appended_log(old_text, new_text)
        self.assertTrue(any("早于上一条" in issue for issue in issues))

    def test_append_log_stops_when_local_date_is_earlier_than_last_record(self):
        self.init_research()
        with mock.patch.object(rw, "_today", return_value="2026-08-20"):
            self.begin_and_log()
            rw.finalize_revision(self.project)
        with mock.patch.object(rw, "_today", return_value="2026-08-21"):
            rw.begin_revision(self.project)
        with mock.patch.object(rw, "_today", return_value="2026-08-19"):
            with self.assertRaisesRegex(rw.WorkbenchError, "当前日期早于"):
                rw.append_log(self.project, "不得倒退", [], [], [], ["日期测试"])

    def test_noncontent_date_examples_do_not_control_log_chronology(self):
        wrappers = (
            ("```text", "```"),
            ("<!--", "-->"),
            ("<pre>", "</pre>"),
        )
        for index, (opening, closing) in enumerate(wrappers):
            with self.subTest(opening=opening):
                project = self.root / f"log-date-example-{index}"
                rw.init_project(project, "日志日期示例", "检查日志日期。", [])
                log = project / "日志日期示例_研究日志_v1.0.0.md"
                log.write_text(
                    log.read_text(encoding="utf-8")
                    + f"\n{opening}\n## 2099-01-01｜代码示例\n{closing}\n",
                    encoding="utf-8",
                )
                with mock.patch.object(rw, "_today", return_value="2026-08-20"):
                    rw.begin_revision(project)
                    rw.append_log(
                        project,
                        "正常记录",
                        [],
                        [],
                        [],
                        ["继续"],
                    )

    def test_finalize_publishes_new_set_and_moves_old_set_without_overwrite(self):
        self.init_research()
        old_contents = {
            role: self.current(role).read_text(encoding="utf-8")
            for role in rw.CORE_ROLES
        }
        self.begin_and_log()
        result = rw.finalize_revision(self.project)
        self.assertEqual("1.0.1", result["current_version"])
        self.assertEqual("local-filesystem", result["storage_scope"])
        self.assertEqual([], rw.validate_project(self.project))
        for role in rw.CORE_ROLES:
            self.assertTrue(self.current(role, "1.0.1").is_file())
            archived = self.project / "old" / self.current(role).name
            self.assertEqual(old_contents[role], archived.read_text(encoding="utf-8"))
        self.assertFalse((self.project / "tmp" / rw.ACTIVE_REVISION_DIR).exists())

    def test_finalize_rename_failure_rolls_back_without_overwrite(self):
        for failing_call in (3, 7):
            with self.subTest(failing_call=failing_call):
                case = self.root / f"rollback-{failing_call}"
                rw.init_project(
                    case,
                    "回滚项目",
                    "验证发布中断可以回滚。",
                    [],
                )
                rw.begin_revision(case)
                rw.append_log(case, "记录候选", [], [], [], ["继续验证"])
                base_names = {
                    role: f"回滚项目_{role}_v1.0.0.md" for role in rw.CORE_ROLES
                }
                base_text = {
                    role: (case / base_names[role]).read_text(encoding="utf-8")
                    for role in rw.CORE_ROLES
                }
                real_rename = rw._move_without_overwrite
                calls = 0

                def flaky_rename(source, target):
                    nonlocal calls
                    calls += 1
                    if calls == failing_call:
                        raise OSError("模拟 rename 中断")
                    return real_rename(source, target)

                with mock.patch.object(rw, "_move_without_overwrite", new=flaky_rename):
                    with self.assertRaisesRegex(rw.WorkbenchError, "已尝试恢复原状态"):
                        rw.finalize_revision(case)

                for role in rw.CORE_ROLES:
                    current = case / base_names[role]
                    candidate = (
                        case
                        / "tmp"
                        / rw.ACTIVE_REVISION_DIR
                        / f"回滚项目_{role}_v1.0.1.md"
                    )
                    self.assertEqual(base_text[role], current.read_text(encoding="utf-8"))
                    self.assertTrue(candidate.is_file())
                    self.assertFalse((case / "old" / base_names[role]).exists())
                    self.assertFalse((case / candidate.name).exists())

    def test_finalize_resumes_a_partially_completed_move(self):
        self.init_research()
        self.begin_and_log()
        active = self.project / "tmp" / rw.ACTIVE_REVISION_DIR
        # Simulate a process ending after two candidates were published and one
        # previous-generation file was archived.
        for role in rw.CORE_ROLES[:2]:
            self.candidate(role).rename(self.project / self.candidate(role).name)
        self.current(rw.CORE_ROLES[0]).rename(
            self.project / "old" / self.current(rw.CORE_ROLES[0]).name
        )
        self.assertTrue(active.is_dir())
        before_inspect = sorted(
            path.relative_to(self.project).as_posix()
            for path in self.project.rglob("*")
        )
        inspected = rw.inspect_project(self.project)
        self.assertEqual("1.0.0", inspected["current_version"])
        self.assertFalse(inspected["active_revision"]["publish_complete"])
        self.assertEqual("in-progress", inspected["active_revision"]["transition_state"])
        for role in rw.CORE_ROLES[:2]:
            self.assertEqual(
                self.candidate(role).name,
                inspected["active_revision"]["candidate_locations"][role],
            )
        self.assertTrue(
            inspected["active_revision"]["base_locations"][rw.CORE_ROLES[0]].startswith(
                "old/"
            )
        )
        after_inspect = sorted(
            path.relative_to(self.project).as_posix()
            for path in self.project.rglob("*")
        )
        self.assertEqual(before_inspect, after_inspect)
        result = rw.finalize_revision(self.project)
        self.assertEqual("1.0.1", result["current_version"])
        self.assertEqual([], rw.validate_project(self.project))

    def test_inspect_rejects_duplicate_candidate_location_without_writing(self):
        self.init_research()
        self.begin_and_log()
        duplicate = self.project / self.candidate("数学主稿").name
        shutil.copyfile(self.candidate("数学主稿"), duplicate)
        before = sorted(
            path.relative_to(self.project).as_posix()
            for path in self.project.rglob("*")
        )
        with self.assertRaisesRegex(rw.WorkbenchError, "多个位置"):
            rw.inspect_project(self.project)
        after = sorted(
            path.relative_to(self.project).as_posix()
            for path in self.project.rglob("*")
        )
        self.assertEqual(before, after)

    def test_finalize_rejects_extra_active_file_before_moving(self):
        self.init_research()
        self.begin_and_log()
        active = self.project / "tmp" / rw.ACTIVE_REVISION_DIR
        extra = active / "用户临时说明.txt"
        extra.write_text("保留\n", encoding="utf-8")

        with self.assertRaisesRegex(rw.WorkbenchError, "额外文件"):
            rw.finalize_revision(self.project)
        for role in rw.CORE_ROLES:
            self.assertTrue(self.current(role).is_file())
            self.assertTrue(self.candidate(role).is_file())
        self.assertTrue((active / rw.REVISION_RECORD_FILE).is_file())
        self.assertEqual("保留\n", extra.read_text(encoding="utf-8"))

        extra.unlink()
        result = rw.finalize_revision(self.project)
        self.assertEqual("1.0.1", result["current_version"])

    def test_cleanup_failure_restores_revision_record_for_retry(self):
        self.init_research()
        self.begin_and_log()
        active = self.project / "tmp" / rw.ACTIVE_REVISION_DIR
        record = active / rw.REVISION_RECORD_FILE
        real_rmdir = pathlib.Path.rmdir
        failed = False

        def fail_active_once(path):
            nonlocal failed
            if path == active and not failed:
                failed = True
                raise OSError("模拟候选目录清理失败")
            return real_rmdir(path)

        with mock.patch.object(pathlib.Path, "rmdir", new=fail_active_once):
            with self.assertRaisesRegex(rw.WorkbenchError, "可再次运行 finalize-revision"):
                rw.finalize_revision(self.project)
        self.assertTrue(record.is_file())
        for role in rw.CORE_ROLES:
            self.assertTrue(self.current(role, "1.0.1").is_file())
            self.assertTrue((self.project / "old" / self.current(role).name).is_file())

        inspected = rw.inspect_project(self.project)
        self.assertEqual("1.0.1", inspected["current_version"])
        self.assertTrue(inspected["active_revision"]["publish_complete"])
        self.assertEqual(
            "published-cleanup-pending",
            inspected["active_revision"]["transition_state"],
        )
        for location in inspected["current_locations"].values():
            self.assertFalse(location.startswith("old/"))

        result = rw.finalize_revision(self.project)
        self.assertEqual("1.0.1", result["current_version"])
        self.assertFalse(active.exists())

    def test_root_research_symlink_is_rejected_before_revision(self):
        self.init_research()
        main = self.current("数学主稿")
        external = self.root / "外部主稿.md"
        shutil.copyfile(main, external)
        main.unlink()
        self.make_symlink(main, external)
        issues = rw.validate_project(self.project)
        self.assertTrue(any("不是普通文件" in issue for issue in issues))
        before = sorted(
            path.relative_to(self.project).as_posix()
            for path in self.project.rglob("*")
        )
        with self.assertRaises(rw.WorkbenchError):
            rw.begin_revision(self.project)
        after = sorted(
            path.relative_to(self.project).as_posix()
            for path in self.project.rglob("*")
        )
        self.assertEqual(before, after)
        self.assertTrue(main.is_symlink())
        self.assertTrue(external.is_file())

    def test_project_and_managed_directory_symlinks_are_rejected(self):
        real_project = self.root / "real-project"
        rw.init_project(real_project, "目录链接", "检查目录边界。", [])
        project_link = self.root / "project-link"
        self.make_symlink(project_link, real_project, target_is_directory=True)
        self.assertTrue(any("项目目录不得是符号链接" in item for item in rw.validate_project(project_link)))
        with self.assertRaisesRegex(rw.WorkbenchError, "项目目录不得是符号链接"):
            rw.begin_revision(project_link)

        for index, dirname in enumerate(rw.PROJECT_DIRS):
            with self.subTest(dirname=dirname):
                case = self.root / f"managed-link-{index}"
                rw.init_project(case, "管理目录", "检查管理目录。", [])
                managed = case / dirname
                managed.rmdir()
                external = self.root / f"external-managed-{index}"
                external.mkdir()
                self.make_symlink(managed, external, target_is_directory=True)
                issues = rw.validate_project(case)
                self.assertTrue(any(dirname in issue and "符号链接" in issue for issue in issues))
                with self.assertRaisesRegex(rw.WorkbenchError, "普通目录|符号链接"):
                    rw.begin_revision(case)
                self.assertEqual([], list(external.iterdir()))

    def test_active_revision_directory_symlink_is_rejected_before_append(self):
        self.init_research()
        rw.begin_revision(self.project)
        active = self.project / "tmp" / rw.ACTIVE_REVISION_DIR
        external = self.root / "external-active"
        active.rename(external)
        self.make_symlink(active, external, target_is_directory=True)
        before = {
            path.name: path.read_text(encoding="utf-8")
            for path in external.iterdir()
            if path.is_file()
        }
        self.assertTrue(any("active-revision" in issue for issue in rw.validate_project(self.project)))
        with self.assertRaisesRegex(rw.WorkbenchError, "进行中升版目录"):
            rw.append_log(self.project, "不应写入", [], [], [], ["停止"])
        after = {
            path.name: path.read_text(encoding="utf-8")
            for path in external.iterdir()
            if path.is_file()
        }
        self.assertEqual(before, after)

    def test_finalize_rejects_symlinked_base_or_candidate_before_moving(self):
        for index, kind in enumerate(("base", "candidate")):
            with self.subTest(kind=kind):
                case = self.root / f"symlink-{index}"
                rw.init_project(
                    case,
                    "链接项目",
                    "验证研究文件必须是普通文件。",
                    [],
                )
                rw.begin_revision(case)
                rw.append_log(case, "记录候选", [], [], [], ["继续验证"])
                base = case / "链接项目_数学主稿_v1.0.0.md"
                candidate = (
                    case
                    / "tmp"
                    / rw.ACTIVE_REVISION_DIR
                    / "链接项目_数学主稿_v1.0.1.md"
                )
                replaced = base if kind == "base" else candidate
                external = self.root / f"外部副本-{index}.md"
                shutil.copyfile(replaced, external)
                replaced.unlink()
                self.make_symlink(replaced, external)

                with self.assertRaisesRegex(rw.WorkbenchError, "不是普通文件"):
                    rw.finalize_revision(case)
                self.assertTrue(replaced.is_symlink())
                self.assertTrue(external.is_file())
                self.assertTrue(
                    (case / "tmp" / rw.ACTIVE_REVISION_DIR / rw.REVISION_RECORD_FILE).is_file()
                )
                self.assertEqual([], list((case / "old").iterdir()))
                for role in rw.CORE_ROLES:
                    current = case / f"链接项目_{role}_v1.0.0.md"
                    active_candidate = (
                        case
                        / "tmp"
                        / rw.ACTIVE_REVISION_DIR
                        / f"链接项目_{role}_v1.0.1.md"
                    )
                    if current != replaced:
                        self.assertTrue(current.is_file())
                    if active_candidate != replaced:
                        self.assertTrue(active_candidate.is_file())

                replaced.unlink()
                shutil.copyfile(external, replaced)
                result = rw.finalize_revision(case)
                self.assertEqual("1.0.1", result["current_version"])

    def test_revision_record_rejects_nonincreasing_version(self):
        self.init_research()
        self.begin_and_log()
        record_path = (
            self.project
            / "tmp"
            / rw.ACTIVE_REVISION_DIR
            / rw.REVISION_RECORD_FILE
        )
        record = json.loads(record_path.read_text(encoding="utf-8"))
        record["new_version"] = record["base_version"]
        record_path.write_text(
            json.dumps(record, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(rw.WorkbenchError, "必须高于"):
            rw.inspect_project(self.project)
        for role in rw.CORE_ROLES:
            self.assertTrue(self.current(role).is_file())

    def test_begin_refuses_old_directory_collision(self):
        self.init_research()
        collision = self.project / "old" / self.current("数学主稿").name
        collision.write_text("不得覆盖\n", encoding="utf-8")
        with self.assertRaisesRegex(rw.WorkbenchError, "目标.*存在|升版已停止"):
            rw.begin_revision(self.project)
        self.assertEqual("不得覆盖\n", collision.read_text(encoding="utf-8"))

    def test_extra_user_directory_is_preserved_through_revision(self):
        self.init_research()
        user_directory = self.project / "用户补充材料"
        user_directory.mkdir()
        user_file = user_directory / "用户文件.txt"
        user_file.write_text("保留\n", encoding="utf-8")
        self.assertEqual([], rw.validate_project(self.project))
        self.begin_and_log()
        rw.finalize_revision(self.project)
        self.assertEqual("保留\n", user_file.read_text(encoding="utf-8"))

    def test_moving_whole_project_during_revision_is_supported(self):
        self.init_research()
        self.begin_and_log()
        moved = self.root / "用户改名后的目录"
        self.project.rename(moved)
        self.project = moved
        result = rw.finalize_revision(self.project)
        self.assertEqual("1.0.1", result["current_version"])
        self.assertEqual([], rw.validate_project(self.project))

    def test_prepare_session_reads_only_active_entry_and_no_mathematical_body(self):
        self.init_research()
        rw.begin_revision(self.project)
        main = self.candidate("数学主稿")
        main.write_text(main.read_text() + "\n正文唯一标记。\n")
        entry = self.candidate("下一次入口")
        entry_text = entry.read_text().replace("## 当前五文件", "用户要求：暂不公开结果。\n\n## 当前五文件", 1)
        entry_text = rw._replace_section(entry_text, "当前近期计划", "阶段目标：一般分类；必要工作：检查退化参数。暂缓可选特例。")
        entry.write_text(entry_text + "\n## 本项目约定\n\n本轮只核对参数，不改目标。\n\n## 停止条件\n\n本轮完成后停止。\n")
        original = pathlib.Path.read_text
        read_paths = []
        def track(path, *args, **kwargs):
            read_paths.append(path)
            return original(path, *args, **kwargs)
        with mock.patch.object(pathlib.Path, "read_text", track):
            payload = json.loads(rw.prepare_session(self.project, "json"))
        self.assertEqual("1.0.1", payload["version"])
        self.assertIn("必要工作：检查退化参数", payload["entry_text"])
        self.assertIn("本轮只核对参数", payload["entry_text"])
        self.assertIn("暂不公开结果", payload["entry_text"])
        self.assertIn("本轮完成后停止", payload["entry_text"])
        self.assertNotIn("正文唯一标记", json.dumps(payload, ensure_ascii=False))
        role_reads = [path for path in read_paths if path.suffix == ".md"]
        self.assertEqual([self.candidate("下一次入口")], role_reads)



    def test_multiple_rounds_preserve_complete_history(self):
        self.init_research()
        original_log = self.current("研究日志").read_bytes()
        for number in range(1, 6):
            _, result = self.publish_round()
            self.assertEqual(f"1.0.{number}", result["current_version"])
        entry = self.current("下一次入口", "1.0.5").read_text()
        self.assertNotIn("周期回顾：", entry)
        self.assertNotIn("PATCH 占用", entry)
        log = self.current("研究日志", "1.0.5").read_bytes()
        self.assertTrue(log.startswith(original_log))
        self.assertEqual(5, log.decode().count("- 轮次类型：实质研究轮"))
        self.assertEqual(25, len(list((self.project/"old").glob("*.md"))))

    def test_review_can_add_results_without_a_no_upgrade_declaration(self):
        self.init_research()
        rw.begin_revision(self.project, "patch", "review")
        with self.assertRaisesRegex(rw.WorkbenchError, "review outcome"):
            rw.append_log(self.project, "回顾主线", [], [], [], ["继续核对"])
        rw.append_log(self.project, "回顾并纳入新结果", [], ["补全相关证明"], ["转向一般情形"], [], "continue")
        log = self.candidate("研究日志").read_text()
        self.assertNotIn("向上数学状态迁移：无", log)
        self.assertIn("补全相关证明", log)
        rw.finalize_revision(self.project)

    def test_maintenance_round_records_actual_type(self):
        self.init_research()
        self.publish_round()
        self.publish_round("maintenance", "minor")
        state = rw._require_state(self.project)
        self.assertIn("- 轮次类型：规范维护轮", state.files["研究日志"].read_text())
        self.assertNotIn("周期回顾：", state.files["下一次入口"].read_text())













    def test_historical_irregular_log_does_not_block_new_append(self):
        self.init_research()
        log = self.current("研究日志")
        log.write_text(log.read_text() + "\n## 2026-08-20｜记录一\n\n- 轮次类型：实质研究轮\n\n## 2026-08-19｜旧式记录\n\n一段自由格式历史。\n")
        before = log.read_bytes()
        self.begin_and_log()
        rw.finalize_revision(self.project)
        self.assertTrue(self.current("研究日志", "1.0.1").read_bytes().startswith(before))

    def test_reference_notes_and_entry_prose_do_not_require_review_tables(self):
        rw.init_project(self.project, "测试项目", "理解给定命题【初步分析】。", ["paper.pdf"])
        ledger = self.current("参考资料台账")
        ledger.write_text(ledger.read_text(encoding="utf-8") + "\n## 具体使用\n\n按定理 2 的假设核对。\n", encoding="utf-8")
        before = ledger.read_bytes()
        entry = self.current("下一次入口")
        entry.write_text(rw._replace_section(entry.read_text(encoding="utf-8"), "当前五文件", "按上方入口和实际目录定位。"), encoding="utf-8")
        self.assertEqual([], rw.validate_project(self.project))
        rw.begin_revision(self.project)
        rw.append_log(self.project, "核对文献条件", ["paper.pdf 定理 2"], [], [], ["检查紧性假设"])
        candidate_before = self.candidate("参考资料台账").read_bytes()
        rw.finalize_revision(self.project)
        self.assertEqual(before, (self.project/"old"/ledger.name).read_bytes())
        self.assertEqual(candidate_before, self.current("参考资料台账", "1.0.1").read_bytes())

    def test_preparing_keeps_completed_but_unrecorded_candidate(self):
        self.init_research()
        replace = rw._replace_revision_record
        def interrupt(path, payload):
            if payload["completed_roles"]:
                raise rw.WorkbenchError("interrupted after candidate copy")
            return replace(path, payload)
        with mock.patch.object(rw, "_replace_revision_record", interrupt):
            with self.assertRaises(rw.WorkbenchError):
                rw.begin_revision(self.project)
        candidate = self.candidate("数学主稿")
        candidate.write_bytes(candidate.read_bytes() + b"\nNew work after interruption.\n")
        saved = candidate.read_bytes()
        with self.assertRaisesRegex(rw.WorkbenchError, "未登记完成的候选目标"):
            rw.begin_revision(self.project)
        self.assertEqual(saved, candidate.read_bytes())

    def test_copy_race_keeps_competing_candidate_and_source(self):
        self.init_research()
        before = self.current("数学主稿").read_bytes()
        move = rw._move_without_overwrite
        def inject(source, target):
            target.write_bytes(b"competing candidate")
            return move(source, target)
        with mock.patch.object(rw, "_move_without_overwrite", inject):
            with self.assertRaises(rw.WorkbenchError):
                rw.begin_revision(self.project)
        self.assertEqual(b"competing candidate", self.candidate("数学主稿").read_bytes())
        self.assertEqual(before, self.current("数学主稿").read_bytes())

    def test_link_shaped_competitor_is_not_treated_as_recovery(self):
        source = self.root / "source.md"
        target = self.root / "target.md"
        source.write_bytes(b"candidate content")
        target.write_bytes(b"existing target")
        original_lstat = pathlib.Path.lstat
        def pretend_link(item):
            info = original_lstat(source)
            if item == target:
                values = list(info)
                values[0] = 0o120777  # symlink pointing to source, same inode fields
                return rw.os.stat_result(values)
            return original_lstat(item)
        with mock.patch.object(pathlib.Path, "lstat", pretend_link), mock.patch.object(pathlib.Path, "samefile", return_value=True):
            with self.assertRaises(OSError):
                rw._move_without_overwrite(source, target)
        self.assertEqual(b"candidate content", source.read_bytes())
        self.assertEqual(b"existing target", target.read_bytes())

    def test_publish_and_archive_races_preserve_competing_file(self):
        for archive in (False, True):
            with self.subTest(archive=archive), tempfile.TemporaryDirectory() as directory:
                project = pathlib.Path(directory)/"race"
                rw.init_project(project, "竞争项目", "检查保存完整性。", [])
                rw.begin_revision(project)
                rw.append_log(project, "保存候选", [], [], [], ["继续"])
                original_move = rw._move_without_overwrite
                collision = []
                def inject(source, target):
                    if not collision and (target.parent == project/"old") == archive:
                        target.write_bytes(b"competing writer")
                        collision.append(target)
                    return original_move(source, target)
                with mock.patch.object(rw, "_move_without_overwrite", inject):
                    with self.assertRaises(rw.WorkbenchError):
                        rw.finalize_revision(project)
                self.assertEqual(b"competing writer", collision[0].read_bytes())
                self.assertTrue((project/"tmp"/rw.ACTIVE_REVISION_DIR/rw.REVISION_RECORD_FILE).is_file())
                collision[0].unlink()
                self.assertEqual("1.0.1", rw.finalize_revision(project)["current_version"])

    @unittest.skipIf(sys.platform == "win32", "POSIX link/unlink recovery")
    def test_linked_candidate_resumes_after_unlink_interruption(self):
        self.init_research()
        self.begin_and_log()
        source = self.candidate("数学主稿")
        target = self.project/source.name
        rw.os.link(source, target)
        self.assertEqual("1.0.1", rw.finalize_revision(self.project)["current_version"])
        self.assertFalse(source.exists())
        self.assertTrue(target.is_file())

    def test_cli_lifecycle(self):
        created = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "init-project",
                str(self.project),
                "--name",
                "命令行项目",
                "--goal",
                "验证版本化工作台。",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, created.returncode, created.stderr)
        for command in (
            ["validate-project", str(self.project), "--json"],
            ["inspect-project", str(self.project)],
            [
                "begin-revision",
                str(self.project),
                "--bump",
                "patch",
                "--round-type",
                "substantive",
            ],
            [
                "append-log",
                str(self.project),
                "--summary",
                "完成首次检查",
                "--unresolved",
                "继续核对",
            ],
            ["prepare-session", str(self.project), "--format", "json"],
            ["finalize-revision", str(self.project)],
        ):
            result = subprocess.run(
                [sys.executable, str(SCRIPT), *command],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, result.returncode, result.stderr)
        inspected = json.loads(
            subprocess.run(
                [sys.executable, str(SCRIPT), "inspect-project", str(self.project)],
                check=True,
                capture_output=True,
                text=True,
            ).stdout
        )
        self.assertEqual("1.0.1", inspected["current_version"])

    def test_cli_requires_an_explicit_version_choice(self):
        self.init_research()
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "begin-revision", str(self.project)],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(2, result.returncode)
        self.assertIn("--bump", result.stderr)
        self.assertIn("--round-type", result.stderr)
        self.assertFalse((self.project / "tmp" / rw.ACTIVE_REVISION_DIR).exists())


if __name__ == "__main__":
    unittest.main()
