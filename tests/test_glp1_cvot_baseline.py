"""Regression tests for source-checked enrollment in GLP-1 CVOT trial baselines.

The published total N is a baseline descriptor, not a replacement for arm
denominators. These tests do not independently validate clinical outcomes.
"""
import re
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "GLP1_CVOT_REVIEW.html"

# Trial enrollment totals checked against original trial reports on 2026-10-17.
# The unchanged tN/cN and published effect fields remain independently auditable.
EXPECTED = {
    "NCT01147250": ("ELIXA", 6068),
    "NCT01179048": ("LEADER", 9340),
    "NCT01720446": ("SUSTAIN-6", 3297),
    "NCT01144338": ("EXSCEL", 14752),
    "NCT02465515": ("HARMONY Outcomes", 9463),
    "NCT01394952": ("REWIND", 9901),
    "NCT02692716": ("PIONEER 6", 3183),
    "NCT03574597": ("SELECT", 17604),
    "NCT03496298": ("AMPLITUDE-O", 4076),
    "NCT03914326": ("SOUL", 9650),
}


class GLP1CVOTBaselineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = HTML.read_text(encoding="utf-8")
        cls.realdata = cls.source.split("realData:{", 1)[1]

    def _trial_prefix(self, nct):
        needle = nct + ':{name:"'
        # Other components on this page re-use the NCT key (e.g. Phase3CTgovData).
        # The FIRST occurrence following realData:{ is the source trial object.
        self.assertIn(needle, self.realdata)
        begin = self.realdata.index(needle)
        end = self.realdata.index("allOutcomes:[", begin)
        prefix = self.realdata[begin:end]
        self.assertLess(len(prefix), 3000, nct)
        return prefix

    def _baseline_body(self, nct):
        prefix = self._trial_prefix(nct)
        matches = re.findall(r"\bbaseline:\{([^}]*)\}", prefix)
        self.assertEqual(len(matches), 1, f"{nct} must have one baseline, not a shadowed duplicate")
        return matches[0]

    def test_exactly_ten_original_trials(self):
        first = self.realdata.split("allOutcomes:[", 1)[0]
        self.assertIn("NCT01147250", first)
        for nct in EXPECTED:
            self.assertIn(nct + ':{name:"', self.realdata)

    def test_baseline_properties_are_unique(self):
        for nct in EXPECTED:
            with self.subTest(nct=nct):
                baseline = self._baseline_body(nct)
                self.assertEqual(len(re.findall(r"(?:^|,)n:\d+(?:,|$)", "," + baseline)), 1)
                self.assertNotRegex(baseline, r"(?:^|,)age:")

    def test_source_checked_enrollment_matches_two_arm_denominators(self):
        for nct, (trial_name, expected_n) in EXPECTED.items():
            with self.subTest(nct=nct, trial=trial_name):
                prefix = self._trial_prefix(nct)
                baseline = self._baseline_body(nct)
                enrolled = re.search(r"(?:^|,)n:(\d+)(?:,|$)", baseline)
                self.assertIsNotNone(enrolled)
                self.assertEqual(int(enrolled.group(1)), expected_n)
                t = re.search(r"\btN:(\d+)", prefix)
                c = re.search(r"\bcN:(\d+)", prefix)
                self.assertIsNotNone(t)
                self.assertIsNotNone(c)
                self.assertEqual(int(t.group(1)) + int(c.group(1)), expected_n)

    def test_effective_demographic_fields_remain_in_same_baseline(self):
        for nct in EXPECTED:
            with self.subTest(nct=nct):
                b = self._baseline_body(nct)
                for required in ("meanAge:", "pctMale:", "meanBMI:", "meanHbA1c:"):
                    self.assertIn(required, b)

    @unittest.skipUnless(shutil.which("node"), "Node.js needed for JS syntax validation")
    def test_each_baseline_is_valid_javascript_syntax(self):
        # Node --check parses without evaluating any source-derived expression.
        program = []
        for i, nct in enumerate(EXPECTED):
            body = self._baseline_body(nct)
            program.append(f"const baseline_{i} = {{{body}}};")
        completed = subprocess.run(
            ["node", "--check"], input="\n".join(program), text=True,
            capture_output=True, check=False, timeout=20,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)


if __name__ == "__main__":
    unittest.main()
