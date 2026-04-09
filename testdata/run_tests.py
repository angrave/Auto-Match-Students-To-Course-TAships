#!/usr/bin/env python3
"""Run tamatch.py against all test cases and compare with expected output."""
import subprocess
import sys
import os
import glob
import pandas as pd

SCRIPT = os.path.join(os.path.dirname(__file__), "..", "tamatch.py")
TEST_DIR = os.path.dirname(__file__)


def compare(expected_path, actual_path, test_name):
    """Compare expected and actual xlsx, return (pass, message)."""
    exp = pd.read_excel(expected_path)
    act = pd.read_excel(actual_path)

    # Sort both by (course, student) for stable comparison
    sort_cols = ["course", "student"]
    exp = exp.sort_values(sort_cols).reset_index(drop=True)
    act = act.sort_values(sort_cols).reset_index(drop=True)

    if list(exp.columns) != list(act.columns):
        return False, f"Column mismatch: expected {list(exp.columns)}, got {list(act.columns)}"

    if len(exp) != len(act):
        return False, f"Row count mismatch: expected {len(exp)}, got {len(act)}"

    diffs = []
    for i in range(len(exp)):
        for col in exp.columns:
            e, a = exp.at[i, col], act.at[i, col]
            if str(e) != str(a):
                diffs.append(f"  row {i} col '{col}': expected '{e}', got '{a}'")

    if diffs:
        return False, "Value mismatches:\n" + "\n".join(diffs)

    return True, "OK"


def main():
    # Find all test cases by looking for *_student.xlsx
    patterns = sorted(glob.glob(os.path.join(TEST_DIR, "*_student.xlsx")))
    if not patterns:
        print("No test cases found. Run create_tests.py first.")
        sys.exit(1)

    passed = 0
    failed = 0

    for spath in patterns:
        prefix = spath.replace("_student.xlsx", "")
        name = os.path.basename(prefix)
        cpath = prefix + "_courses.xlsx"
        epath = prefix + "_expected.xlsx"
        opath = prefix + "_actual.xlsx"

        if not os.path.exists(cpath) or not os.path.exists(epath):
            print(f"SKIP  {name} (missing courses or expected file)")
            continue

        result = subprocess.run(
            [sys.executable, SCRIPT, spath, cpath, opath],
            capture_output=True, text=True,
        )

        if result.returncode != 0:
            print(f"FAIL  {name} (script error)")
            print(f"  stderr: {result.stderr.strip()}")
            failed += 1
            continue

        ok, msg = compare(epath, opath, name)
        if ok:
            print(f"PASS  {name}")
            passed += 1
        else:
            print(f"FAIL  {name}")
            print(msg)
            failed += 1

    print(f"\n{passed} passed, {failed} failed, {passed + failed} total")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
