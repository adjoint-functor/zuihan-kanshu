#!/usr/bin/env python3
"""Positive release-surface tests for zuihan-kanshu."""

from __future__ import annotations

import json
import pathlib
import re
import subprocess
import sys
import tempfile
import unittest


REPOSITORY_ROOT = pathlib.Path(__file__).resolve().parents[1]
ROOT = REPOSITORY_ROOT / "skill" / "zuihan-kanshu"
WORKBENCH = ROOT / "scripts" / "research-workbench.py"
VERSIONED_OUTPUT = ROOT / "scripts" / "versioned-output.py"
DERIVE_READER = ROOT / "scripts" / "derive-clean-reader-view.py"
FINAL_PDF_BUILD = ROOT / "scripts" / "final-pdf-build.py"

CORE_FILES = {
    "数学主稿.md",
    "计算草稿.md",
    "研究日志.md",
    "下一次入口.md",
    "参考资料台账.md",
}
TEMPLATE_FILES = {"main.md.tmpl", "scratch.md.tmpl", "log.md.tmpl", "entry.md.tmpl", "ledger.md.tmpl"}
CURRENT_REFERENCES = {
    "usage-guide.md",
    "mathematical-inquiry.md",
    "mathematical-judgment.md",
    "document-roles.md",
    "writing-style.md",
    "matlas.md",
    "theorem-search.md",
    "working-draft.md",
    "structure-consistency-review.md",
    "introduction-writing.md",
    "research-workbench.md",
    "literature.md",
    "research-roles.md",
    "chinese-translation.md",
    "translation-glossary-en-zh.md",
    "japanese-names-places-zh.md",
    "final-output.md",
    "final-pdf-build-profile.md",
    "pdf-environment.md",
}
EXPECTED_RELEASE_FILES = {
    "LICENSE",
    "NOTICE",
    "SKILL.md",
    "agents/openai.yaml",
    "assets/icon-1024.png",
    "assets/icon-256.png",
    "assets/icon-dark-1024.png",
    "assets/icon-dark-256.png",
    "assets/pdf-environment/baseline.json",
    "assets/pdf-environment/smoke.md",
    "assets/final-pdf/v1/ams-mathbb.tex",
    "assets/final-pdf/v1/pandoc-defaults.yaml",
    *{f"assets/research-project/{filename}" for filename in TEMPLATE_FILES},
    *{f"references/{filename}" for filename in CURRENT_REFERENCES},
    "scripts/derive-clean-reader-view.py",
    "scripts/final-pdf-build.py",
    "scripts/matlas-client.py",
    "scripts/theorem-search-client.py",
    "scripts/preflight-pdf.py",
    "scripts/pdf-environment.py",
    "scripts/research-workbench.py",
    "scripts/versioned-output.py",
}
EXPECTED_RELEASE_DIRECTORIES = {
    "agents",
    "assets",
    "assets/final-pdf",
    "assets/final-pdf/v1",
    "assets/research-project",
    "assets/pdf-environment",
    "references",
    "scripts",
}
WORKBENCH_COMMANDS = {
    "init-project",
    "inspect-project",
    "validate-project",
    "begin-revision",
    "append-log",
    "prepare-session",
    "finalize-revision",
}
OUTPUT_COMMANDS = {
    "ensure-output-dir",
    "inspect",
    "begin-revision",
    "finalize-revision",
}


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def public_commands(help_text: str) -> set[str]:
    match = re.search(r"\{([^{}\n]+)\}", help_text)
    if match is None:
        raise AssertionError("command set is missing from CLI help")
    return set(match.group(1).split(","))


class SkillSurfaceTests(unittest.TestCase):
    def test_version_and_declared_entrypoints(self):
        skill = read("SKILL.md")
        agent = read("agents/openai.yaml")

        self.assertRegex(skill, r"(?m)^name:\s*zuihan-kanshu\s*$")
        version_match = re.search(r"(?m)^# .+ v(\d+\.\d+\.\d+)\s*$", skill)
        self.assertIsNotNone(version_match)
        current_version = version_match.group(1)  # type: ignore[union-attr]
        self.assertIn("$zuihan-kanshu", agent)
        self.assertIn("allow_implicit_invocation: true", agent)
        for filename in CURRENT_REFERENCES:
            self.assertTrue((ROOT / "references" / filename).is_file(), filename)
            self.assertIn(f"references/{filename}", skill)

        for script in (WORKBENCH, VERSIONED_OUTPUT, FINAL_PDF_BUILD):
            result = subprocess.run(
                [sys.executable, str(script), "--version"],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual(current_version, result.stdout.strip())

    def test_release_tree_matches_the_declared_current_files(self):
        actual = {
            path.relative_to(ROOT).as_posix()
            for path in ROOT.rglob("*")
            if path.is_file()
            and "__pycache__" not in path.parts
            and path.suffix not in {".pyc", ".pyo"}
        }
        self.assertEqual(EXPECTED_RELEASE_FILES, actual)
        actual_directories = {
            path.relative_to(ROOT).as_posix()
            for path in ROOT.rglob("*")
            if path.is_dir() and "__pycache__" not in path.parts
        }
        self.assertEqual(EXPECTED_RELEASE_DIRECTORIES, actual_directories)

        repository = subprocess.run(
            ["git", "-C", str(ROOT), "rev-parse", "--show-toplevel"],
            check=False,
            capture_output=True,
            text=True,
        )
        if repository.returncode == 0:
            repository_root = pathlib.Path(repository.stdout.strip())
            skill_prefix = ROOT.relative_to(repository_root).as_posix()
            tracked_result = subprocess.run(
                [
                    "git",
                    "-c",
                    "core.quotepath=false",
                    "-C",
                    str(repository_root),
                    "ls-files",
                    "--",
                    skill_prefix,
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            tracked = {
                pathlib.PurePosixPath(line).relative_to(skill_prefix).as_posix()
                for line in tracked_result.stdout.splitlines()
                if line
            }
            self.assertEqual(EXPECTED_RELEASE_FILES, tracked)

    def test_five_file_topology_is_research_only(self):
        skill = read("SKILL.md")
        workbench = read("references/research-workbench.md")
        ordinary = read("references/working-draft.md")

        for filename in CORE_FILES:
            role = filename.removesuffix(".md")
            self.assertIn(f"<项目名>_{role}_vMAJOR.MINOR.PATCH.md", workbench)
        self.assertIn("普通文稿保持灵活", skill)
        self.assertIn("独立控制 Markdown、干净正文 Markdown", ordinary)
        self.assertIn("不套用研究五文件结构", ordinary)
        for directory in ("download/", "old/", "tmp/"):
            self.assertIn(f"`{directory}`", skill)
        self.assertIn("同目录", ordinary)
        self.assertIn("上一版", ordinary)

    def test_template_resource_names_are_ascii_and_output_roles_stay_chinese(self):
        template_dir = ROOT / "assets" / "research-project"
        actual = {path.name for path in template_dir.iterdir() if path.is_file()}
        expected = TEMPLATE_FILES
        self.assertTrue(all(name.isascii() for name in actual))
        self.assertEqual(expected, actual)
        entry = (template_dir / "entry.md.tmpl").read_text(encoding="utf-8")
        for placeholder in (
            "{{CURRENT_VERSION}}",
            "{{MAIN_FILE}}",
            "{{SCRATCH_FILE}}",
            "{{LOG_FILE}}",
            "{{ENTRY_FILE}}",
            "{{LEDGER_FILE}}",
        ):
            self.assertIn(placeholder, entry)
        for phrase in (
            "## 当前近期计划",
            "## 必要读取",
            "## 待人决策与暂停",
        ):
            self.assertIn(phrase, entry)
        main = (template_dir / "main.md.tmpl").read_text(encoding="utf-8")
        self.assertIn("## 条件性结果", main)
        self.assertIn("## 当前研究前沿与数学依赖", main)
        established = main.split("## 已建立的数学内容", 1)[1].split(
            "## 条件性结果", 1
        )[0]
        self.assertNotIn("条件性结果", established)
        log = (template_dir / "log.md.tmpl").read_text(encoding="utf-8")
        self.assertIn("有保留价值的失败路线", log)
        self.assertIn("停止原因", log)

    def test_research_entry_and_scratch_contracts_are_explicit(self):
        entry = read("assets/research-project/entry.md.tmpl")
        scratch = read("assets/research-project/scratch.md.tmpl")

        for heading in (
            "## 当前五文件",
            "## 必要读取",
            "## 当前近期计划",
        ):
            self.assertIn(heading, entry)
        self.assertIn("可删除、合并、压缩和重排", scratch)
        self.assertIn("## 当前问题包", scratch)
        for obsolete in ("唯一状态迁移", "PATCH 已占用", "最大风险与硬停止"):
            self.assertNotIn(obsolete, scratch)
        for obsolete in ("周期回顾：", "PATCH 占用", "唯一状态迁移"):
            self.assertNotIn(obsolete, entry)

    def test_research_review_and_evidence_paths_are_documented(self):
        roles = read("references/research-roles.md")
        workbench = read("references/research-workbench.md")

        self.assertIn("复查", roles)
        self.assertIn("独立核验", roles)
        judgment = read("references/mathematical-judgment.md")
        self.assertIn("mathematical-judgment.md", roles)
        self.assertIn("tmp/blind-check/<核验编号>/input/", judgment)
        self.assertIn("evidence/", workbench)
        self.assertIn("old/evidence/", workbench)


    def test_workbench_documents_candidate_check_and_persistent_save(self):
        workbench = read("references/research-workbench.md")
        self.assertIn("validate-project <项目目录> --candidate", workbench)
        self.assertIn("只操作本地文件系统", workbench)
        self.assertIn("具备 Work/Library 云端保存能力时按 Library 技能处理", workbench)
        self.assertIn("确认五个新文件的保存结果全部成功，再将上一版五文件移入相应项目目录的 `old/`", workbench)

    def test_current_project_directory_contract_is_complete(self):
        skill = read("SKILL.md")
        workbench = read("references/research-workbench.md")
        for directory in ("download/", "old/", "tmp/"):
            self.assertIn(f"`{directory}`", skill)
            self.assertIn(f"`{directory}`", workbench)

    def test_download_filename_and_preprint_update_rules_are_declared(self):
        skill = read("SKILL.md")
        review = read("references/literature.md")
        self.assertIn("references/literature.md", skill)
        for phrase in (
            "以下条款均为规范性定义",
            'FILE_NAME := "[" + KEY + "] " + TITLE',
            "KEY := AUTHOR_YEAR_KEY | SERIES_KEY",
            "AUTHOR_YEAR_KEY := STEM + YY + DISAMBIG",
            "SERIES_KEY := SERIES + VOLUME",
            "BibTeX `alpha.bst`",
            "BibLaTeX `alphabetic`",
            "精确人数算法是本项目规范",
            "不声称等同于可配置的 BibLaTeX `alphabetic` 默认值",
            "权威元数据",
            "Unicode NFKD",
            "缺少该转写时停止命名",
            "`N = 1`",
            "`2 ≤ N ≤ 4`",
            "`N ≥ 5`",
            "不得重新编号",
            "规范化责任者和稳定来源标识排序",
            "`aa` 至 `az`",
            "当且仅当文件属于出版者定义的正式丛书",
            "只保留 ASCII 字母和数字",
            "稳定 `KEY` 优先于这项首次命名规则",
            "arXiv-<ID>v<N>",
            "非 arXiv 预印本",
            "不得静默覆盖",
            "tmp/download-incoming/",
            "superseded-<UTCSTAMP>",
            "责任者少于四名时直接停止命名",
            "若归档目标已存在",
            "old/download/",
            "精确本地文件名",
        ):
            self.assertIn(phrase, review)
        self.assertIn("不是出版社、国家或国际组织制定的统一文件名标准", review)

        naming_section = review.split("## 网络下载文献与文件名规范", 1)[1].split(
            "## 完成条件", 1
        )[0]
        self.assertNotRegex(
            naming_section,
            r"\[[A-Za-z+]{1,12}\d{1,4}[a-z]?\]",
            "规范章节不得用具体方括号键承担规则定义",
        )

        ledger_template = read("assets/research-project/ledger.md.tmpl")
        for field in ("精确本地文件名", "来源标识", "取得时间", "实际使用版本"):
            self.assertIn(field, ledger_template)

    def test_cli_help_declares_exactly_the_current_commands(self):
        workbench_help = subprocess.run(
            [sys.executable, str(WORKBENCH), "--help"],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, workbench_help.returncode, workbench_help.stderr)
        self.assertEqual(WORKBENCH_COMMANDS, public_commands(workbench_help.stdout))

        output_help = subprocess.run(
            [sys.executable, str(VERSIONED_OUTPUT), "--help"],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, output_help.returncode, output_help.stderr)
        self.assertEqual(OUTPUT_COMMANDS, public_commands(output_help.stdout))



    def test_final_output_separates_control_from_reader_artifacts(self):
        final_output = read("references/final-output.md")
        for path in (
            "tmp/finished_v1.0.1.md",
            "tmp/finished_v1.0.1.control.md",
            "tmp/finished_v1.0.1.reader.md",
            "tmp/finished_v1.0.1.pdf",
            "tmp/finished_v1.0.1.tex",
            "tmp/finished_v1.0.1.log",
            "tmp/final-build-v1.0.1.json",
        ):
            self.assertIn(path, final_output)
        self.assertIn("--control", final_output)
        self.assertIn("--tex", final_output)
        self.assertIn("不要求重编未变 PDF", final_output)
        self.assertIn(".resources/", final_output)

    def test_translation_tables_are_clean_runtime_resources(self):
        skill = read("SKILL.md")
        module = read("references/chinese-translation.md")
        english = read("references/translation-glossary-en-zh.md")
        japanese = read("references/japanese-names-places-zh.md")

        for filename in ("translation-glossary-en-zh.md", "japanese-names-places-zh.md"):
            self.assertIn(f"references/{filename}", skill)
            self.assertIn(filename, module)
        for forbidden in (
            "提案",
            "复核日期",
            "尚未实装",
            "核验来源",
            "已核实",
            "变更审计",
            "维护规则",
            "语义版本",
            "http://",
            "https://",
        ):
            self.assertNotIn(forbidden, english)
            self.assertNotIn(forbidden, japanese)
        for phrase in (
            "命中后直接采用表中形式，不为每次出现重复查网",
            "先匹配最长的完整术语",
            "禁止子串替换和全局替换",
            "参考文献列表及 BibTeX/CSL 数据是只读保护区",
        ):
            self.assertIn(phrase, module)
        for phrase in (
            "| cocharacter | 余特征标 |",
            "| coweight | 余权 |",
            "| normalized induction | 归一化诱导 |",
            "| normalized intertwining operator | 归一化交织算子 |",
            "| pseudo-Eisenstein series | 伪Eisenstein级数 |",
            "| principal series representation | 主系列表示 |",
        ):
            self.assertIn(phrase, english)
        for phrase in (
            "| Iwasawa decomposition | 岩泽分解 |",
            "| Tamagawa measure | 玉河测度 |",
            "| Ichino–Ikeda formula | 市野–池田公式 |",
            "| Asai $L$-function | 浅井 $L$-函数 |",
            "保护区可以用于消歧正文身份，但只能读、不能写",
        ):
            self.assertIn(phrase, japanese)

    def test_writing_style_is_routed_directly(self):
        skill = read("SKILL.md")
        module = read("references/writing-style.md")
        self.assertIn("references/writing-style.md", skill)
        self.assertIn("标题默认使用客观、描述性的对象名、命题或主题", module)
        self.assertIn("用户明确指定的问答、访谈等文种或标题风格优先", module)
        self.assertIn("候选命中只供语义复核，不授权批量替换", module)

    def test_final_output_declares_single_source_profile_and_mathbb_contract(self):
        skill = read("SKILL.md")
        final_output = read("references/final-output.md")
        profile = read("references/final-pdf-build-profile.md")
        header = read("assets/final-pdf/v1/ams-mathbb.tex")
        self.assertIn("references/final-pdf-build-profile.md", skill)
        for phrase in (
            "成品 Markdown 是唯一可编辑的文档正文源",
            "不从旧 PDF 或生成过的 LaTeX 恢复内容",
            "短小、无编号、无需回引且只作为句法成分",
            "MSBM10",
            "不得把编译成功说成视觉通过",
        ):
            self.assertIn(phrase, final_output)
        for phrase in (
            "final-pdf-build/v1",
            "zh-math-xelatex/v1",
            "拒绝未知键和重复键",
            "绝对路径、`..` 越界",
            "不读取同目录旧 PDF、旧 LaTeX",
        ):
            self.assertIn(phrase, profile)
        self.assertIn("{U}{msb}{m}{n}", header)
        self.assertIn("\\let\\mathbb\\mathbbAMS", header)

    def test_writing_style_preserves_mathematical_scope(self):
        skill = read("SKILL.md")
        module = read("references/writing-style.md")
        self.assertIn("不自行改变数学实质", module)
        self.assertIn("普通来源在已有数学修订授权内处理", module)
        self.assertIn("活动研究项目回研究工作台", skill)
        self.assertIn("普通来源则在已授权的数学修订范围内处理", skill)

    def test_current_modules_are_substantive_and_routed(self):
        skill = read("SKILL.md")
        for filename in CURRENT_REFERENCES:
            path = ROOT / "references" / filename
            self.assertGreater(len(path.read_text(encoding="utf-8").strip()), 200, filename)
            self.assertIn(f"references/{filename}", skill)


if __name__ == "__main__":
    unittest.main()
