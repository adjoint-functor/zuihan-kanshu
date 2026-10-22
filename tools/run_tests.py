#!/usr/bin/env python3
"""Run repository tests, optionally requiring every test to execute."""

from __future__ import annotations

import argparse
import json
import sys
import unittest
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--require-no-skips", action="store_true")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    suite = unittest.defaultTestLoader.discover(str(root / "tests"), pattern="test_*.py")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    summary = {
        "tests_run": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "skipped": [{"test": str(test), "reason": reason} for test, reason in result.skipped],
        "expected_failures": len(result.expectedFailures),
        "unexpected_successes": len(result.unexpectedSuccesses),
        "require_no_skips": args.require_no_skips,
    }
    if args.report:
        with args.report.open("x", encoding="utf-8") as handle:
            json.dump(summary, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
    if args.require_no_skips and result.skipped:
        print("Full validation requires every test to run; see skipped tests above.", file=sys.stderr)
    return int(not result.wasSuccessful() or (args.require_no_skips and bool(result.skipped)))


if __name__ == "__main__":
    raise SystemExit(main())
