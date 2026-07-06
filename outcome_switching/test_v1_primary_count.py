"""Regression test for count_v1_primaries (compute_v1_vs_current_269).

primary_count_change previously assumed v1 had exactly one primary, so it
false-flagged every current trial with != 1 primary (even when v1 had the same
count) and missed real reductions to one primary. Counting the v1 primaries from
the block fixes both directions (validated on the live 269-pool: 79 -> 33 flags,
46 false positives removed).

Run: python -m pytest outcome_switching/test_v1_primary_count.py -q
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from compute_v1_vs_current_269 import count_v1_primaries  # noqa: E402

SINGLE = (
    "Primary Outcome Measures\n"
    "Difference in flow-mediated vasodilatation (FMD)\n"
    "Difference in FMD between groups at the final visit\n"
    "[Time Frame: Baseline, 3 months]\n"
)
TWO = (
    "Primary Outcome Measures\n"
    "CV death or HF hospitalization\n"
    "composite endpoint\n"
    "[Time Frame: Up to 24 months]\n"
    "All-cause mortality\n"
    "death from any cause\n"
    "[Time Frame: Up to 24 months]\n"
)
TWO_WITH_SECONDARY = TWO + (
    "Secondary Outcome Measures\n"
    "KCCQ score\n"
    "[Time Frame: 12 months]\n"
)


def test_counts_single_primary():
    assert count_v1_primaries(SINGLE) == 1


def test_counts_multiple_primaries():
    assert count_v1_primaries(TWO) == 2


def test_secondary_section_not_counted():
    # The secondary [Time Frame:] must not inflate the primary count.
    assert count_v1_primaries(TWO_WITH_SECONDARY) == 2


def test_empty_block():
    assert count_v1_primaries("") == 0
