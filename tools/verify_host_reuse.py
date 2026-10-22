#!/usr/bin/env python3
"""Assert that a recovery fixture retained working host executables and libraries."""

import json
from pathlib import Path
import sys


before = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
prefix = Path(sys.argv[2])
after = json.loads((prefix / "check.json").read_text(encoding="utf-8"))
config = json.loads((prefix / "environment.json").read_text(encoding="utf-8"))
assert not after["missing"], after["missing"]
for name, item in before["tools"].items():
    if item["works"]:
        assert after["tools"][name]["path"] == item["path"], name
        assert after["tools"][name]["version"] == item["version"], name
assert after["tex_distribution"]["core_files"] == before["tex_distribution"]["core_files"]
assert after["python"] == before["python"]
assert after["python_packages"] == before["python_packages"]
assert config["tex"]["mode"] == "user-tree", config["tex"]
assert not any((prefix / name).exists() for name in ("tex", "pandoc", "python"))
print("Host executables, TeX core and Python libraries retained; only the TeX user tree was added.")
