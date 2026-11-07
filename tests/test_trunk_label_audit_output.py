"""Regression: audit_trial_label_identity must not default its report to one machine's scratch.

Root cause this pins: the default for LABEL_AUDIT_OUT was a dated directory under F:/claude-temp.
On any machine without that directory the audit finished its work and then died in json.dump
with FileNotFoundError, so hook-chain recorded exit=1 and its real verdict was never reached.
"""
import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "scripts", "audit_trial_label_identity.py")


class LabelAuditOutput(unittest.TestCase):
    def setUp(self):
        with open(SCRIPT, encoding="utf-8") as fh:
            self.src = fh.read()

    def test_default_output_is_not_a_hard_coded_drive_path(self):
        self.assertIsNone(re.search(r'LABEL_AUDIT_OUT"\s*,\s*"[A-Za-z]:/', self.src))

    def test_env_override_still_decides_the_path(self):
        self.assertIn('LABEL_AUDIT_OUT', self.src)
        self.assertIn('default_report_path()', self.src)

    def test_default_path_has_an_existing_parent(self):
        ns = {}
        block = re.search(r"^def default_report_path\(\):\n(?:[ \t]+.*\n)+", self.src, re.M)
        self.assertIsNotNone(block)
        exec("import os\nimport tempfile\n" + block.group(0), ns)
        self.assertTrue(os.path.isdir(os.path.dirname(ns["default_report_path"]())))


if __name__ == "__main__":
    unittest.main()
