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
                 mock.patch.object(ENV, "install_private_tex_packages") as private_install, \
                 mock.patch.object(ENV, "download") as download, mock.patch.object(ENV, "unpack") as unpack:
                self.assertEqual(0, ENV.restore_new(args, prefix, "Linux-x86_64"))
                self.assertEqual(["xeCJK.sty"], extend.call_args.args[3])
                download.assert_not_called()
                unpack.assert_not_called()
                private_install.assert_not_called()
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

    def private_manager_fixture(self, prefix, mode):
        script = prefix / "tlmgr-fixture.py"
        script.write_text('''import json, os, pathlib, sys
root = pathlib.Path(os.environ["MATH_TEX_FIXTURE_DIR"])
args = sys.argv[1:]
with (root / "commands.jsonl").open("a", encoding="utf-8") as stream:
    stream.write(json.dumps(args) + "\\n")
if args[0] == "info":
    print("xecjk,1")
    sys.exit(0)
repository = args[args.index("--repository") + 1]
action = args[args.index("--repository") + 2]
mode = os.environ["MATH_TEX_FIXTURE_MODE"]
if action == "update":
    print("selected repository: " + repository)
    if mode == "self-update-fails":
        print("manager update unavailable", file=sys.stderr)
        sys.exit(2)
    if "--all" not in args:
        (root / "manager-updated").write_text("updated", encoding="utf-8")
    print("manager refreshed")
elif action == "install":
    print("tlmgr: package repository " + repository + " (verified)")
    if mode == "ordinary-error":
        print("package repository unavailable", file=sys.stderr)
        sys.exit(2)
    if mode == "repeat-self" or not (root / "manager-updated").exists():
        print("tlmgr itself needs to be updated. Please do this via tlmgr update --self", file=sys.stderr)
        sys.exit(255)
    packages = args[args.index("install") + 1:]
    (root / "installed.json").write_text(json.dumps(packages), encoding="utf-8")
    print("packages installed")
else:
    sys.exit("unexpected fixture operation")
''', encoding="utf-8")
        env = ENV.environment({})
        env.update(MATH_TEX_FIXTURE_DIR=str(prefix), MATH_TEX_FIXTURE_MODE=mode)
        return [sys.executable, script], env

    def test_private_restore_recovers_when_successful_baseline_update_is_not_enough(self):
        with tempfile.TemporaryDirectory() as directory:
            prefix = Path(directory)
            manager, fixture_env = self.private_manager_fixture(prefix, "recover")
            private_bin = prefix / "tex" / "bin"
            args = argparse.Namespace(baseline_tools=False, private_tex=True, extra_tex_package=["xurl"],
                                      font_dir=[], tex_repository=None)
            actual_run = ENV.run
            def run_private(argv, env, **kwargs):
                self.assertEqual(private_bin, Path(argv[0]).parent)
                env = env | {name: fixture_env[name] for name in ("MATH_TEX_FIXTURE_DIR", "MATH_TEX_FIXTURE_MODE")}
                return actual_run([*manager, *argv[1:]], env, **kwargs)
            with mock.patch.object(ENV, "which", side_effect=lambda name, env: "/host/bin/" + name), \
                 mock.patch.object(ENV, "importable", return_value=(True, "host-version")), \
                 mock.patch.object(ENV, "download"), mock.patch.object(ENV, "unpack"), \
                 mock.patch.object(ENV, "find_tool", return_value=private_bin), \
                 mock.patch.object(ENV, "tex_repository", return_value="https://example.org/verified-texlive"), \
                 mock.patch.object(ENV, "restore_fonts"), \
                 mock.patch.object(ENV, "check", return_value={"missing": []}), \
                 mock.patch.object(ENV, "run", side_effect=run_private):
                self.assertEqual(0, ENV.restore_new(args, prefix, "Linux-x86_64"))
            self.assertEqual("private", ENV.load_config(prefix / "environment.json")["tex"]["mode"])
            self.assertEqual([*ENV.BASELINE["tex_packages"], "xurl"], json.loads((prefix / "installed.json").read_text()))
            commands = [json.loads(line) for line in (prefix / "commands.jsonl").read_text().splitlines()]
            self.assertEqual(["update", "--self", "--all"], commands[0][2:])
            self.assertEqual(5, len(commands))
            self.assertIn("manager refreshed", (prefix / "tex-update.txt").read_text())
            self.assertIn("xecjk,1", (prefix / "tex-packages.txt").read_text())

    def test_private_install_recovers_an_explicit_self_update_request_once(self):
        with tempfile.TemporaryDirectory() as directory:
            prefix = Path(directory)
            manager, env = self.private_manager_fixture(prefix, "recover")
            repository = "https://example.org/verified-texlive"
            ENV.install_private_tex_packages(manager, repository, env, prefix, ["xecjk", "xurl"])
            self.assertEqual(["xecjk", "xurl"], json.loads((prefix / "installed.json").read_text()))
            commands = [json.loads(line) for line in (prefix / "commands.jsonl").read_text().splitlines()]
            self.assertEqual(["install", "update", "install"], [command[2] for command in commands])
            self.assertTrue(all(command[:2] == ["--repository", repository] for command in commands))
            self.assertEqual(["--self"], commands[1][3:])
            self.assertEqual(commands[0], commands[2])
            log = (prefix / "tex-install.txt").read_text()
            self.assertIn("tlmgr itself needs to be updated", log)
            self.assertIn("packages installed", log)
            self.assertIn("manager refreshed", (prefix / "tex-self-update.txt").read_text())

    def test_private_install_does_not_retry_unrelated_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            prefix = Path(directory)
            manager, env = self.private_manager_fixture(prefix, "ordinary-error")
            with self.assertRaisesRegex(RuntimeError, "private TeX packages failed.*2"):
                ENV.install_private_tex_packages(manager, "https://example.org/verified-texlive", env, prefix, ["xecjk"])
            self.assertEqual(1, len((prefix / "commands.jsonl").read_text().splitlines()))
            self.assertFalse((prefix / "tex-self-update.txt").exists())
            self.assertFalse((prefix / "installed.json").exists())
            self.assertIn("package repository unavailable", (prefix / "tex-install.txt").read_text())

    def test_private_install_stops_when_manager_self_update_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            prefix = Path(directory)
            manager, env = self.private_manager_fixture(prefix, "self-update-fails")
            with self.assertRaisesRegex(RuntimeError, "private TeX manager self-update failed.*2"):
                ENV.install_private_tex_packages(manager, "https://example.org/verified-texlive", env, prefix, ["xecjk"])
            self.assertEqual(2, len((prefix / "commands.jsonl").read_text().splitlines()))
            self.assertFalse((prefix / "installed.json").exists())
            self.assertIn("manager update unavailable", (prefix / "tex-self-update.txt").read_text())

    def test_private_install_stops_after_one_self_update_and_retry(self):
        with tempfile.TemporaryDirectory() as directory:
            prefix = Path(directory)
            manager, env = self.private_manager_fixture(prefix, "repeat-self")
            with self.assertRaisesRegex(RuntimeError, "private TeX packages failed.*255"):
                ENV.install_private_tex_packages(manager, "https://example.org/verified-texlive", env, prefix, ["xecjk"])
            self.assertEqual(3, len((prefix / "commands.jsonl").read_text().splitlines()))
            self.assertFalse((prefix / "installed.json").exists())
            self.assertEqual(2, (prefix / "tex-install.txt").read_text().count("tlmgr itself needs to be updated"))

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
