"""Regression: run_hook_chain must read what a hook RUNS, not what its comments quote.

Root cause this pins: .githooks/pre-push line 16 is a comment recording the OLD invocation,
`#   1.  python "$SCRIPT" 2>&1 | tail -15`. invocations() matched it, so the chain ran a bare
scripts/regression_check.py that no hook runs. In CI that died on `import playwright`
(exit=1, FAILED); with Playwright present it would be the full corpus walk the hook's real
`--only $CHANGED` scope exists to prevent.
"""
import importlib.util
import io
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location(
    "run_hook_chain_under_test", os.path.join(ROOT, "gates", "run_hook_chain.py"))
chain = importlib.util.module_from_spec(spec)
_stdout = sys.stdout
spec.loader.exec_module(chain)
sys.stdout = _stdout


class CommentsAreNotInvocations(unittest.TestCase):
    HOOK = ('SCRIPT="$REPO_ROOT/scripts/regression_check.py"\n'
            '#   1.  python "$SCRIPT" 2>&1 | tail -15\n'
            '  # python "$R/scripts/commented_out.py"\n'
            'python "$SCRIPT" --port "$PORT" --only $CHANGED > "$LOG" 2>&1\n'
            'python "$R/scripts/real_gate.py" --flag\n')

    def test_commented_invocation_is_not_collected(self):
        found = chain.invocations(self.HOOK)
        rels = [rel for rel, _ in found]
        self.assertNotIn("scripts/commented_out.py", rels)
        bare = [a for rel, a in found if rel == "scripts/regression_check.py"
                and "--only" not in a]
        self.assertEqual(bare, [], "a comment produced a bare regression_check run")

    def test_real_invocations_survive(self):
        found = chain.invocations(self.HOOK)
        rels = [rel for rel, _ in found]
        self.assertIn("scripts/real_gate.py", rels)
        self.assertTrue(any(rel == "scripts/regression_check.py" and "--only" in a
                            for rel, a in found))

    def test_the_real_prepush_still_runs_scoped_regression_check(self):
        with io.open(os.path.join(ROOT, ".githooks", "pre-push"), encoding="utf-8",
                     errors="replace") as fh:
            found = chain.invocations(fh.read())
        args = [a for rel, a in found if rel == "scripts/regression_check.py"]
        self.assertTrue(args, "the real regression_check invocation vanished")
        self.assertTrue(all("--only" in a for a in args), args)


if __name__ == "__main__":
    unittest.main()
