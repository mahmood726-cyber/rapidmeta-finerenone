"""Regression: the two remainder screeners must resolve the repository from their own path.

Root cause this pins (hook-chain, trunk red since at least 2026-10-17): both screeners set
REPO = "F:/rapidmeta-ssot-shell", a path on one machine. On the CI runner that put a
non-existent directory on sys.path, `import ctgov_transport` raised ModuleNotFoundError, and
scripts/lint_criteria_fingerprint.py -- which loads both screeners -- exited 1. On the author's
machine the same line silently read another checkout's ssot/, not the tree under test.
"""
import os
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCREENERS = ("screen_ablation_medical_remainder_2026_08_19.py",
             "screen_rhythm_control_remainder_2026_08_19.py")


class ScreenerRepoPath(unittest.TestCase):
    def test_no_screener_names_one_machines_checkout(self):
        for name in SCREENERS:
            with open(os.path.join(ROOT, "scripts", name), encoding="utf-8") as fh:
                self.assertNotIn('REPO = "F:/', fh.read(), name)

    def test_fingerprint_lint_reaches_a_verdict_on_the_screeners(self):
        # Asserts the lint RAN, not merely that it exited 0: a ModuleNotFoundError is exit 1 too,
        # and a verdict of "screener drifted" must stay a failure this test does not hide.
        env = dict(os.environ, PYTHONIOENCODING="utf-8")
        proc = subprocess.run([sys.executable, os.path.join(ROOT, "scripts",
                                                            "lint_criteria_fingerprint.py")],
                              capture_output=True, text=True, encoding="utf-8",
                              errors="replace", env=env, cwd=ROOT, timeout=120)
        self.assertNotIn("ModuleNotFoundError", proc.stderr + proc.stdout)
        self.assertEqual(proc.returncode, 0, proc.stdout[-800:] + proc.stderr[-800:])


if __name__ == "__main__":
    unittest.main()
