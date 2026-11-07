"""Regression: a declared benchmark that stops counting must be NAMED, not silently absent.

Root cause this pins: `benchmarked` only increments inside `if pool:`. A benchmark whose page
disappeared, or whose page no longer yields a pool, left the numerator with no line of output,
so CI fell 14 -> 13 -> 3 -> 2 of ~1425 apps while printing only a percentage. This reports the
loss; it does not change the coverage arithmetic or the --require-coverage floor.
"""
import importlib.util
import os
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location(
    "validate_portfolio_under_test", os.path.join(ROOT, "validate_living_ma_portfolio.py"))
vp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vp)


class LostBenchmarksAreNamed(unittest.TestCase):
    BENCH = {"KEPT": {}, "GONE": {}, "OUT": {}, "EMPTY": {}, "NOPOOL": {}}
    RESULTS = [
        {"name": "KEPT", "k": 2, "trial_count": 2, "benchmark": 0.8},
        {"name": "EMPTY", "k": 0, "trial_count": 0},
        {"name": "NOPOOL", "k": 0, "trial_count": 3},
        {"name": "UNRELATED", "k": 0, "trial_count": 0},
    ]

    def test_every_uncounted_benchmark_gets_exactly_one_reason(self):
        lost = vp.lost_benchmarks(self.BENCH, self.RESULTS, excluded={"OUT"})
        self.assertEqual(lost, {
            "GONE": vp.LOST_NO_PAGE,
            "OUT": vp.LOST_EXCLUDED,
            "EMPTY": vp.LOST_NO_TRIALS_IN_PAGE,
            "NOPOOL": vp.LOST_NOT_POOLABLE,
        })

    def test_a_counted_benchmark_is_never_reported_lost(self):
        self.assertNotIn("KEPT", vp.lost_benchmarks(self.BENCH, self.RESULTS, excluded=set()))

    def test_counted_plus_lost_is_the_whole_declared_set(self):
        lost = vp.lost_benchmarks(self.BENCH, self.RESULTS, excluded={"OUT"})
        counted = {r["name"] for r in self.RESULTS if r.get("benchmark") is not None}
        self.assertEqual(set(lost) | counted, set(self.BENCH))
        self.assertEqual(set(lost) & counted, set())

    def test_the_real_declared_set_is_not_empty(self):
        self.assertGreater(len(vp.BENCHMARKS), 0)


if __name__ == "__main__":
    unittest.main()
