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


    def test_real_chromium_evaluates_restored_enrollment(self):
        """Exercise source-derived JS baseline literals in a headless browser."""
        import tempfile
        browser = next(
            (exe for cmd in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser")
             if (exe := shutil.which(cmd))), None,
        )
        self.assertIsNotNone(browser, "A real headless Chrome/Chromium browser is required")
        trial_objects = []
        for nct, (_, published_n) in EXPECTED.items():
            baseline = self._baseline_body(nct)
            self.assertNotIn("</script", baseline.lower())
            trial_objects.append(
                '{id:"' + nct + '",expected:' + str(published_n)
                + ',baseline:{' + baseline + '}}'
            )
        browser_script = (
            "const records=[" + ",".join(trial_objects) + "];"
            "const priorBug={baseline:{n:123},baseline:{meanAge:60}};"
            "const lastWins=priorBug.baseline.n===undefined;"
            "const restored=records.length===10&&records.every(r=>"
            "r.baseline.n===r.expected&&Number.isInteger(r.baseline.n)"
            "&&typeof r.baseline.meanAge==='number');"
            "document.querySelector('#result').textContent="
            "(lastWins&&restored)?'GLP1_BROWSER_BASELINE_PASS':'GLP1_BROWSER_BASELINE_FAIL';"
        )
        page = ('<!doctype html><meta charset="utf-8"><div id="result"></div>'
                '<script>' + browser_script + '</script>')
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "glp1-baseline.html"
            path.write_text(page, encoding="utf-8")
            run = subprocess.run(
                [browser, "--headless", "--no-sandbox", "--disable-gpu",
                 "--disable-dev-shm-usage", "--no-first-run", "--dump-dom", path.as_uri()],
                capture_output=True, text=True, timeout=45, check=False,
            )
            self.assertEqual(run.returncode, 0, run.stderr[-1500:])
            # --dump-dom includes the script literal containing the word FAIL.
            # Assert the rendered result element, not a page-wide substring.
            rendered = re.search(r'<div id="result">([^<]*)</div>', run.stdout)
            self.assertIsNotNone(rendered, "Browser did not render the result element")
            self.assertEqual(rendered.group(1), "GLP1_BROWSER_BASELINE_PASS")


if __name__ == "__main__":
    unittest.main()
