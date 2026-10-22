"""Exercise the distributable plugin and its one-source release boundary."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

import yaml


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("plugin_release", ROOT / "tools" / "build_release.py")
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class PluginReleaseTests(unittest.TestCase):
    def test_ascii_archive_runs_init_with_chinese_output_names(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _target, archive = builder.build_plugin(root / "build", archive=True)
            installed = root / "installed"
            with zipfile.ZipFile(archive) as handle:
                self.assertTrue(all(name.isascii() for name in handle.namelist()))
                # Even an importer that ignores the UTF-8 flag must preserve
                # these internal resource paths. Output names are separate.
                self.assertEqual(handle.namelist(), [name.encode("utf-8").decode("cp437") for name in handle.namelist()])
                handle.extractall(installed)
            script = installed / "skills/zuihan-kanshu/scripts/research-workbench.py"
            project = root / "project"
            initialized = subprocess.run([sys.executable, str(script), "init-project", str(project), "--name", "中文项目", "--goal", "核对定义", "--reference", "参考资料"], capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(0, initialized.returncode, initialized.stderr)
            roles = {"数学主稿", "计算草稿", "研究日志", "下一次入口", "参考资料台账"}
            self.assertEqual({f"中文项目_{role}_v1.0.0.md" for role in roles}, {path.name for path in project.glob("*.md")})
            for path in project.glob("*.md"):
                self.assertNotIn("{{", path.read_text(encoding="utf-8"))
            checked = subprocess.run([sys.executable, str(script), "validate-project", str(project)], capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(0, checked.returncode, checked.stderr)

    def test_zip_contains_exactly_the_single_skill_and_portable_metadata(self):
        with tempfile.TemporaryDirectory() as temporary:
            target, archive = builder.build_plugin(Path(temporary), archive=True)
            icon_paths = {
                "assets/icon-256.png",
                "assets/icon-1024.png",
                "assets/icon-dark-256.png",
                "assets/icon-dark-1024.png",
            }
            expected = {"plugin.json", "LICENSE", "NOTICE"} | icon_paths | {
                "skills/zuihan-kanshu/" + str(relative)
                for relative in builder.manifest_paths()
            }
            self.assertEqual(expected, {p.relative_to(target).as_posix() for p in target.rglob("*") if p.is_file()})
            with zipfile.ZipFile(archive) as handle:
                self.assertIsNone(handle.testzip())
                self.assertEqual(expected, set(handle.namelist()))
                manifest = json.loads(handle.read("plugin.json"))
                self.assertEqual("zuihan-kanshu", manifest["name"])
                self.assertEqual((ROOT / "VERSION").read_text().strip(), manifest["version"])
                extension = manifest["extensions"]["com.openai"]
                self.assertIn("interface", extension)
                self.assertEqual("瑞般观珠", extension["interface"]["displayName"])
                for field in ("composerIcon", "composerIconDark", "logo", "logoDark"):
                    self.assertIn(extension["interface"][field].removeprefix("./"), expected)
                for field in ("brandColor", "brandColorDark"):
                    self.assertRegex(extension["interface"][field], r"^#[0-9A-Fa-f]{6}$")
                metadata = yaml.safe_load(handle.read("skills/zuihan-kanshu/agents/openai.yaml"))
                self.assertEqual({"CHAT", "CODEX"}, set(metadata["policy"]["products"]))
                self.assertIs(metadata["policy"]["allow_implicit_invocation"], True)
                self.assertEqual("瑞般观珠", metadata["interface"]["display_name"])
                for field in ("icon_small", "icon_large"):
                    self.assertIn("skills/zuihan-kanshu/" + metadata["interface"][field].removeprefix("./"), expected)
                for relative in builder.manifest_paths():
                    self.assertEqual((builder.SKILL / relative).read_bytes(), handle.read("skills/zuihan-kanshu/" + str(relative)))
                for name in ("LICENSE", "NOTICE"):
                    self.assertEqual(handle.read(name), handle.read("skills/zuihan-kanshu/" + name))
                for path in icon_paths:
                    icon = handle.read(path)
                    size = 256 if "256" in path else 1024
                    self.assertEqual(b"\x89PNG\r\n\x1a\n", icon[:8])
                    self.assertEqual((size, size), (int.from_bytes(icon[16:20], "big"), int.from_bytes(icon[20:24], "big")))
                    self.assertLessEqual(len(icon), 5 * 1024 * 1024)
                    self.assertEqual((builder.SKILL / path).read_bytes(), icon)
            other, second_archive = builder.build_plugin(Path(temporary) / "second", archive=True)
            self.assertEqual(archive.read_bytes(), second_archive.read_bytes())

    def test_both_formats_build_beside_each_other_in_one_output_directory(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "releases"
            for package_format in ("skill", "plugin"):
                command = [
                    sys.executable, str(ROOT / "tools" / "build_release.py"),
                    "--format", package_format, "--output-dir", str(output),
                ]
                if package_format == "plugin":
                    command.append("--zip")
                result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8")
                self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            package_name = f"zuihan-kanshu-v{builder.release_version()}"
            skill = output / "skill" / package_name
            plugin = output / "plugin" / package_name
            self.assertEqual({"skill", "plugin"}, {path.name for path in output.iterdir()})
            self.assertTrue((plugin.parent / (package_name + ".zip")).is_file())
            self.assertEqual(
                {relative.as_posix() for relative in builder.manifest_paths()},
                {path.relative_to(skill).as_posix() for path in skill.rglob("*") if path.is_file()},
            )
            for relative in builder.manifest_paths():
                self.assertEqual(
                    (skill / relative).read_bytes(),
                    (plugin / "skills" / "zuihan-kanshu" / relative).read_bytes(),
                )

    def test_bad_template_or_undeclared_runtime_file_cannot_publish(self):
        with tempfile.TemporaryDirectory() as temporary:
            temporary = Path(temporary)
            template = temporary / "template.json.in"
            template.write_text(builder.PLUGIN_TEMPLATE.read_text(encoding="utf-8").replace('"interface": {', '"hooks": "./hooks.json", "interface": {'), encoding="utf-8")
            with mock.patch.object(builder, "PLUGIN_TEMPLATE", template):
                with self.assertRaisesRegex(builder.ReleaseError, "only skills"):
                    builder.build_plugin(temporary / "out")
            self.assertFalse((temporary / "out").exists())
            runtime = temporary / "runtime"
            runtime.mkdir()
            (runtime / "README.md").write_text("maintenance content")
            with mock.patch.object(builder, "SKILL", runtime):
                with self.assertRaisesRegex(builder.ReleaseError, "extra: README.md"):
                    builder.build_plugin(temporary / "out")
            self.assertFalse((temporary / "out").exists())

    def test_icon_path_escape_missing_asset_and_wrong_size_cannot_publish(self):
        with tempfile.TemporaryDirectory() as temporary:
            temporary = Path(temporary)
            template = temporary / "template.json.in"
            original = builder.PLUGIN_TEMPLATE.read_text(encoding="utf-8")
            for path, error in (
                ("./assets/../outside.png", "contained PNG asset path"),
                ("./assets/missing.png", "absent from the runtime manifest"),
                ("./assets/icon-1024.png", "256 x 256"),
            ):
                template.write_text(original.replace("./assets/icon-256.png", path), encoding="utf-8")
                with mock.patch.object(builder, "PLUGIN_TEMPLATE", template):
                    with self.assertRaisesRegex(builder.ReleaseError, error):
                        builder.build_plugin(temporary / "out")
                self.assertFalse((temporary / "out").exists())

    def test_existing_package_and_runtime_source_are_protected(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            target = output / "plugin" / f"zuihan-kanshu-v{builder.release_version()}"
            target.mkdir(parents=True)
            sentinel = target / "keep.txt"
            sentinel.write_text("keep this")
            with self.assertRaisesRegex(builder.ReleaseError, "already exists"):
                builder.build_plugin(output, archive=True)
            self.assertEqual("keep this", sentinel.read_text())
            with self.assertRaisesRegex(builder.ReleaseError, "inside the runtime source"):
                builder.build_plugin(builder.SKILL / "tmp")
            self.assertFalse((builder.SKILL / "tmp").exists())


if __name__ == "__main__":
    unittest.main()
