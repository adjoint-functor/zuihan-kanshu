"""Focused recovery tests; real tool installation and PDF builds are separate."""

import argparse
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


SCRIPT = Path(__file__).resolve().parents[1] / "skill/zuihan-kanshu/scripts/pdf-environment.py"
SPEC = importlib.util.spec_from_file_location("pdf_environment", SCRIPT)
ENV = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ENV)


class EnvironmentTests(unittest.TestCase):
    def test_one_missing_macro_extends_the_existing_engine_only(self):
        with tempfile.TemporaryDirectory() as directory:
            prefix = Path(directory)
            args = argparse.Namespace(baseline_tools=False, private_tex=False, extra_tex_package=[],
                                      font_dir=[], tex_repository=None, cjk_main=None)
            def file(name, env):
                return "" if name == "xeCJK.sty" else "/host/" + name
            with mock.patch.object(ENV, "which", side_effect=lambda n, e: "/host/bin/" + n), \
                 mock.patch.object(ENV, "importable", return_value=(True, "host-version")), \
                 mock.patch.object(ENV, "tex_file", side_effect=file), \
                 mock.patch.object(ENV, "font_path", return_value="/host/font.otf"), \
                 mock.patch.object(ENV, "configure_fonts"), \
                 mock.patch.object(ENV, "extend_tex") as extend, \
                 mock.patch.object(ENV, "tex_inventory", return_value={"year": 2023}), \
                 mock.patch.object(ENV, "check", return_value={"missing": []}), \
                 mock.patch.object(ENV, "download") as download, mock.patch.object(ENV, "unpack") as unpack:
                self.assertEqual(0, ENV.restore_new(args, prefix, "Linux-x86_64"))
                self.assertEqual(["xeCJK.sty"], extend.call_args.args[3])
                download.assert_not_called()
                unpack.assert_not_called()
            config = ENV.load_config(prefix / "environment.json")
            self.assertEqual(sys.executable, config["python"])
            self.assertFalse(config["python_paths"] and str(prefix / "python") in config["python_paths"])

    def test_explicit_font_is_not_replaced_by_an_available_candidate(self):
        with tempfile.TemporaryDirectory() as directory:
            prefix = Path(directory)
            args = argparse.Namespace(baseline_tools=False, private_tex=False, extra_tex_package=[],
                                      font_dir=[], tex_repository=None, cjk_main="Chosen Family")
            with mock.patch.object(ENV, "which", return_value="/host/bin/tool"), \
                 mock.patch.object(ENV, "importable", return_value=(True, "host-version")), \
                 mock.patch.object(ENV, "tex_file", return_value="/host/file"), \
                 mock.patch.object(ENV, "font_path", side_effect=lambda family, env: None if family == "Chosen Family" else "/host/font.otf"), \
                 mock.patch.object(ENV, "configure_fonts"), \
                 mock.patch.object(ENV, "tex_inventory", return_value={"year": 2023}), \
                 mock.patch.object(ENV, "check", return_value={"missing": ["font Chosen Family"]}), \
                 mock.patch.object(ENV, "download") as download:
                self.assertEqual(1, ENV.restore_new(args, prefix, "Linux-x86_64"))
                download.assert_not_called()
            self.assertEqual("Chosen Family", ENV.load_config(prefix / "environment.json")["fonts"]["cjk_main"])

    def test_font_recovery_downloads_only_missing_channels(self):
        with tempfile.TemporaryDirectory() as directory:
            config = {"fonts": ENV.BASELINE["fonts"].copy()}
            args = argparse.Namespace(baseline_tools=False, font_dir=[])
            with mock.patch.object(ENV, "configure_fonts"), \
                 mock.patch.object(ENV, "font_path", side_effect=lambda family, env: "/host/font.otf" if family == "Source Han Sans SC" or family == "Noto Serif CJK SC" else None), \
                 mock.patch.object(ENV, "download") as download:
                ENV.restore_fonts(config, args, Path(directory))
            self.assertEqual("Source Han Sans SC", config["fonts"]["cjk_sans"])
            self.assertEqual(ENV.BASELINE["cjk_fonts"]["cjk_mono"]["urls"], [call.args[0] for call in download.call_args_list])
            self.assertTrue(all(call.args[1].name == "cjk_mono" for call in download.call_args_list))

    def test_explicit_sans_and_mono_are_not_replaced_or_downloaded(self):
        with tempfile.TemporaryDirectory() as directory:
            config = {"fonts": ENV.BASELINE["fonts"] | {"cjk_sans": "Custom Sans", "cjk_mono": "Custom Mono"}}
            args = argparse.Namespace(baseline_tools=False, font_dir=[], cjk_sans="Custom Sans", cjk_mono="Custom Mono")
            with mock.patch.object(ENV, "configure_fonts"), \
                 mock.patch.object(ENV, "font_path", side_effect=lambda family, env: None if family.startswith("Custom") else "/host/font.otf"), \
                 mock.patch.object(ENV, "download") as download:
                ENV.restore_fonts(config, args, Path(directory))
            download.assert_not_called()
            self.assertEqual("Custom Mono", config["fonts"]["cjk_mono"])
            self.assertEqual("Custom Sans", config["fonts"]["cjk_sans"])

    def test_user_tree_install_uses_matching_year_and_leaves_host_paths(self):
        with tempfile.TemporaryDirectory() as directory:
            prefix = Path(directory)
            config = {"variables": {}, "bin_dirs": []}
            args = argparse.Namespace(extra_tex_package=["xurl"], tex_repository=None)
            output = subprocess.CompletedProcess([], 0, "installed", "")
            with mock.patch.object(ENV, "tex_inventory", return_value={"year": 2023,"TEXMFHOME": "/old/user-tree"}), \
                 mock.patch.object(ENV, "which", return_value="/host/bin/tlmgr"), \
                 mock.patch.object(ENV, "tex_repository", return_value="https://example.org/2023") as repository, \
                 mock.patch.object(ENV, "tex_file", return_value="/new/xeCJK.sty"), \
                 mock.patch.object(ENV, "run", return_value=output) as commands:
                ENV.extend_tex(config, args, prefix, ["xeCJK.sty"])
            self.assertEqual(2023, repository.call_args.args[1])
            for call in commands.call_args_list:
                self.assertIn("--usermode", call.args[0])
                self.assertNotIn("update", call.args[0])
                self.assertNotIn("--all", call.args[0])
            self.assertIn("--no-depends", commands.call_args_list[-1].args[0])
            self.assertEqual([], config["bin_dirs"])
            self.assertEqual(["xecjk", "xurl"], config["tex"]["packages"])
            self.assertTrue(config["variables"]["TEXMFHOME"].endswith(os.pathsep + "/old/user-tree"))

    def test_repository_failure_is_preserved_and_does_not_install(self):
        with tempfile.TemporaryDirectory() as directory:
            args = argparse.Namespace(tex_repository="https://example.org/wrong-year")
            response = subprocess.CompletedProcess([], 1, "", "local TeX Live is older than remote")
            with mock.patch.object(ENV, "run", return_value=response) as commands:
                with self.assertRaisesRegex(RuntimeError, "TeX Live 2023"):
                    ENV.tex_repository(args, 2023, ["tlmgr"], {}, Path(directory), "xecjk")
            self.assertEqual(1, commands.call_count)
            self.assertIn("older than remote", (Path(directory) / "tex-repository-probes.txt").read_text())
            self.assertNotIn("install", commands.call_args.args[0])

    def test_run_uses_selected_environment_and_propagates_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = root / "environment.json"
            output = root / "observed.json"
            config.write_text(json.dumps({
                "schema": ENV.SCHEMA, "python": sys.executable,
                "variables": {"MATH_PDF_PROBE": "chosen"},
            }), encoding="utf-8")
            parent = os.environ.copy()
            parent["MATH_PDF_PARENT"] = "inherited"
            result = subprocess.run([
                sys.executable, str(SCRIPT), "run", "--config", str(config), "--", "python",
                "-c", "import os,json,sys; open(sys.argv[1],'w').write(json.dumps("
                "[os.getenv('MATH_PDF_PROBE'),os.getenv('MATH_PDF_PARENT'),sys.executable]));sys.exit(7)",
                str(output),
            ], env=parent, capture_output=True, text=True)
            self.assertEqual(result.returncode, 7, result.stderr)
            values = json.loads(output.read_text())
            self.assertEqual(values[:2], ["chosen", "inherited"])
            self.assertEqual(Path(values[2]).resolve(), Path(sys.executable).resolve())
            self.assertNotIn("MATH_PDF_PROBE", os.environ)

    def test_fontconfig_substitution_does_not_satisfy_requested_font(self):
        response = subprocess.CompletedProcess([], 0, "Different Family\n/fallback.otf\n", "")
        with mock.patch.object(ENV, "which", return_value="fc-match"), mock.patch.object(ENV, "run", return_value=response):
            self.assertIsNone(ENV.font_path("Requested Family", {}))

    def test_missing_linux_native_layer_stops_before_download(self):
        with tempfile.TemporaryDirectory() as directory:
            prefix = Path(directory) / "new"
            args = argparse.Namespace(prefix=prefix, baseline_tools=False, extra_tex_package=[])
            with mock.patch.object(ENV, "platform_key", return_value="Linux-x86_64"), \
                 mock.patch.object(ENV.platform, "system", return_value="Linux"), \
                 mock.patch.object(ENV, "which", return_value=None), \
                 mock.patch.object(ENV, "download") as download:
                with self.assertRaisesRegex(RuntimeError, "native Linux tools"):
                    ENV.restore(args)
                download.assert_not_called()
            self.assertFalse(prefix.exists())

    def test_partial_restore_is_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            prefix = Path(directory)
            evidence = prefix / "failure.log"
            evidence.write_text("previous failure", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "new/empty prefix"):
                ENV.restore(argparse.Namespace(prefix=prefix))
            self.assertEqual(evidence.read_text(), "previous failure")

    def test_installation_failure_is_saved_in_the_partial_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            prefix = Path(directory) / "new"
            args = argparse.Namespace(prefix=prefix, baseline_tools=False, extra_tex_package=[])
            with mock.patch.object(ENV, "platform_key", return_value="Windows-x86_64"), \
                 mock.patch.object(ENV.platform, "system", return_value="Windows"), \
                 mock.patch.object(ENV, "restore_new", side_effect=RuntimeError("installer diagnostic")):
                with self.assertRaisesRegex(RuntimeError, "installer diagnostic"):
                    ENV.restore(args)
            self.assertIn("installer diagnostic", (prefix / "failure.txt").read_text())

    def test_existing_configuration_is_rechecked_without_reinstall(self):
        with tempfile.TemporaryDirectory() as directory:
            prefix = Path(directory)
            ENV.write_json(prefix / "environment.json", {"schema": ENV.SCHEMA})
            with mock.patch.object(ENV, "check", return_value={"missing": ["lost tool"]}), \
                 mock.patch.object(ENV, "download") as download:
                self.assertEqual(ENV.restore(argparse.Namespace(prefix=prefix)), 1)
                download.assert_not_called()

    def test_failed_probe_leaves_diagnostic_without_building_sample(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "sample"
            with mock.patch.object(ENV, "check", return_value={"missing": ["xelatex"]}), \
                 mock.patch.object(ENV, "run") as run:
                with self.assertRaisesRegex(RuntimeError, "environment check failed"):
                    ENV.smoke({}, output)
                run.assert_not_called()
            self.assertEqual(json.loads((output / "environment-check.json").read_text())["missing"], ["xelatex"])
            self.assertFalse(list(output.rglob("*.pdf")))


if __name__ == "__main__":
    unittest.main()
