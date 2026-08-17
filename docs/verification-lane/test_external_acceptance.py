"""The REAL acceptance: the benchmark lane's mutant set, run against this harness.

`mutation_suite.py` is author-inherited -- I wrote it to grade my own fixes,
which is the authorship blind spot TAXONOMY.md Sec 4.1 names. This module runs
the set I did not write, and it is the one that counts.

It has already earned its place twice in a single sitting. Against my own suite
the harness scored 0 survivors and looked finished. Against this one it scored
**2/7 on Arm A, down from 7/7** -- my provenance fix had broken the honest
caller -- and it surfaced a survivor my set had no mutant for (M5b, an off-by-one
enrolment inside CHK006's tolerance band). Neither was visible to review, to the
unit tests, or to the suite I built.

PROVENANCE
----------
`external/mutation_test_current_harness.py` is a VERBATIM copy of
    ...\\local_81e534fd-bb88-45a1-8c07-0ce35d224d3d\\outputs\\mutation_test_current_harness.py
taken 16 August 2026, sha256 recorded alongside it in
`external/mutation_test_current_harness.sha256`. Not one line was edited -- in
particular its hardcoded `sys.path.insert` for another session's mount is left
in place (it resolves to nothing and is harmless). Editing a test to make it
pass is the oldest way to make a check that cannot fail.

Vendored rather than referenced because an external dependency that cannot be
reached would make this test skip, and a skipped acceptance reads as a passed
one -- EB-024, `CLEAN` absorbing "unchecked", 54 apps. If the original changes,
the checksum test below fails and the copy must be re-synced deliberately.
"""

from __future__ import annotations

import io
import os
import re
import contextlib
import hashlib
import runpy
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
EXTERNAL = os.path.join(HERE, "external", "mutation_test_current_harness.py")
CHECKSUM = os.path.join(HERE, "external", "mutation_test_current_harness.sha256")

# The upstream path, recorded so a re-sync does not require archaeology.
UPSTREAM = (r"C:\Users\mahmo\AppData\Roaming\Claude\local-agent-mode-sessions"
            r"\bdc5772c-ca03-473f-9464-80d37a7559d2"
            r"\44788c9b-d162-4f2e-b3c2-d89031e65ab6"
            r"\local_81e534fd-bb88-45a1-8c07-0ce35d224d3d\outputs"
            r"\mutation_test_current_harness.py")


def _run_external() -> str:
    if HERE not in sys.path:
        sys.path.insert(0, HERE)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        runpy.run_path(EXTERNAL, run_name="__external_acceptance__")
    return buf.getvalue()


class TestExternalAcceptance(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.out = _run_external()

    def test_the_vendored_copy_is_unmodified(self):
        with open(CHECKSUM, encoding="utf-8") as fh:
            expected = fh.read().strip()
        with open(EXTERNAL, "rb") as fh:
            actual = hashlib.sha256(fh.read()).hexdigest()
        self.assertEqual(actual, expected,
                         "the vendored acceptance script has been modified. Editing "
                         "the test rather than the harness is how a check stops "
                         f"being able to fail. Upstream: {UPSTREAM}")

    def test_arm_a_is_seven_of_seven(self):
        """The honest caller must not be broken by a provenance requirement."""
        m = re.search(r"ARM A \(referent keyed correctly\):\s*(\d)/7", self.out)
        self.assertIsNotNone(m, self.out[-800:])
        self.assertEqual(m.group(1), "7",
                         "Arm A regressed. A keyed referent without provenance "
                         "metadata must still report a disagreement: agreement "
                         "authenticates nothing, only disagreement is informative.")

    def test_no_mutant_survives_in_any_arm(self):
        """SURVIVED means a planted defect was certified as clean. Zero, always.

        Includes M5b, which is outside the headline denominator in the upstream
        script but is still a PASS on a mutated value, and so still a survivor.
        """
        survivors = [ln.strip() for ln in self.out.splitlines() if "SURVIVED" in ln
                     and "all mutants SURVIVED" not in ln]
        self.assertEqual(survivors, [],
                         "planted defects certified as clean:\n" + "\n".join(survivors))

    def test_arms_b_and_c_certify_nothing(self):
        """2/7 is the correct score, and it is not a failure to improve.

        A number-bag and a referent omitting the mutated field cannot support a
        verdict on those fields. The upstream headline counts only FAIL as a
        kill, so both arms read 2/7 -- the two identity mutants. What changed is
        that the other five moved PASS -> INVALID: refused, not certified.
        """
        for arm in ("ARM B (referent as number-bag)",
                    "ARM C (referent key omitted)"):
            m = re.search(re.escape(arm) + r":\s*(\d)/7", self.out)
            self.assertIsNotNone(m, self.out[-800:])
            self.assertEqual(m.group(1), "2", f"{arm} moved unexpectedly")

    def test_identity_mutants_are_killed(self):
        m = re.search(r"identity mutants killed: (\d)/2", self.out)
        self.assertIsNotNone(m, self.out[-800:])
        self.assertEqual(m.group(1), "2")


if __name__ == "__main__":
    print(_run_external())
