"""Tests for the mistake ledger.

A ledger is itself a check, so it gets the same treatment as the detectors: it
must be capable of reporting badly. The tests below fail if the ledger drifts
towards flattery -- an unsourced row, a guard named without a state, an instance
fix counted as class coverage, or the headline computed from the wrong set.
"""

from __future__ import annotations

import unittest

from nafis_harness import build_registry
from nafis_harness.ledger import (ROWS, AVAILABLE, CLASS, INSTANCE, NONE, WIRED,
                                  summarise, unguarded_queue, to_dicts)


class TestLedgerIntegrity(unittest.TestCase):

    def test_every_row_states_a_guard_or_none_explicitly(self):
        for r in ROWS:
            with self.subTest(row=r.id):
                self.assertTrue(r.guard.strip())
                self.assertIn(r.guard_state, (WIRED, AVAILABLE, NONE))
                if r.guard_state == NONE:
                    self.assertTrue(
                        r.guard == "NONE" or r.guard.startswith("NONE")
                        or "NOT a standing artefact" in r.guard,
                        f"{r.id}: guard_state NONE but guard reads {r.guard!r}")

    def test_no_row_claims_a_guard_it_does_not_name(self):
        for r in ROWS:
            with self.subTest(row=r.id):
                if r.guard_state in (WIRED, AVAILABLE):
                    self.assertNotEqual(r.guard, "NONE")

    def test_every_row_is_sourced_and_tiered(self):
        for r in ROWS:
            with self.subTest(row=r.id):
                self.assertTrue(r.source.strip(), f"{r.id} has no source")
                self.assertIn(r.tier, ("F", "R"))

    def test_operator_relayed_rows_say_so_in_their_source(self):
        """An [R] row whose source names a file would be passing itself off as
        file-backed -- the [B]/[F] confusion this project keeps legislating for."""
        for r in ROWS:
            if r.tier == "R":
                with self.subTest(row=r.id):
                    self.assertIn("operator-relayed", r.source.lower(),
                                  f"{r.id} is tier R but its source does not say so")

    def test_instance_fixes_are_not_counted_as_class_coverage(self):
        """The load-bearing field. An instance fix is how a logged mistake recurs."""
        for r in ROWS:
            if r.fix_scope == INSTANCE:
                with self.subTest(row=r.id):
                    self.assertFalse(r.guarded_at_class_level)
                    self.assertIn(r, unguarded_queue(),
                                  f"{r.id} is an instance fix and must be in the "
                                  "work queue")

    def test_named_detectors_actually_exist_in_the_registry(self):
        """A guard that names a detector nobody built is a fig leaf."""
        reg = build_registry()
        for r in ROWS:
            for tok in r.guard.replace("(", " ").replace(")", " ").split():
                if tok.startswith("CHK") and tok.rstrip(";,.") not in (
                        "CHK031_SEARCH_RECALL",):
                    cid = tok.rstrip(";,.")
                    with self.subTest(row=r.id, detector=cid):
                        self.assertIn(cid, reg,
                                      f"{r.id} names {cid}, which is not registered")

    def test_held_out_detector_is_named_as_held_out(self):
        reg = build_registry()
        held = [r for r in ROWS if "CHK031" in r.guard]
        self.assertTrue(held)
        for r in held:
            self.assertNotIn("CHK031_SEARCH_RECALL", reg)
            self.assertEqual(r.guard_state, NONE,
                             "a held-out detector is not a guard")


class TestHeadlineMeasurement(unittest.TestCase):

    def setUp(self):
        self.s = summarise()

    def test_the_headline_is_computed_from_the_full_row_set(self):
        self.assertEqual(self.s["rows"], len(ROWS))
        self.assertEqual(sum(self.s["by_guard_state"].values()), len(ROWS))
        self.assertEqual(sum(self.s["by_fix_scope"].values()), len(ROWS))

    def test_wired_and_available_are_reported_separately(self):
        """Collapsing them would count a library nobody calls as a guard --
        EB-024, `CLEAN` absorbing "unchecked", 54 apps."""
        self.assertLess(self.s["caught_today_if_wired_only"],
                        self.s["caught_today_if_harness_invoked"],
                        "if these are equal the distinction has been lost")
        self.assertIn(WIRED, self.s["by_guard_state"])
        self.assertIn(AVAILABLE, self.s["by_guard_state"])

    def test_the_autonomous_catch_rate_is_low_and_is_reported(self):
        """Most of these were caught because a human looked. That is the point."""
        self.assertLess(self.s["caught_autonomously_when_it_happened"], 0.25)
        autonomous = [r.id for r in ROWS if r.autonomous_catch]
        self.assertTrue(autonomous)
        # every autonomously-caught row must name the mechanism that caught it
        for r in ROWS:
            if r.autonomous_catch:
                with self.subTest(row=r.id):
                    self.assertTrue(r.caught_by.strip())

    def test_unguarded_queue_is_not_empty_and_is_ordered_none_first(self):
        q = unguarded_queue()
        self.assertTrue(q)
        states = [r.guard_state for r in q]
        self.assertEqual(states, sorted(states, key=lambda s: s != NONE),
                         "rows with no mechanism must sort before instance fixes")

    def test_serialisable(self):
        d = to_dicts()
        self.assertEqual(len(d), len(ROWS))
        self.assertIn("guard_state", d[0])


if __name__ == "__main__":
    unittest.main(verbosity=2)
