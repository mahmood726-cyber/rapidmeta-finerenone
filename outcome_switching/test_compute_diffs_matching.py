"""Regression test for one-to-one outcome matching in compute_diffs.

Duplicate/similar titles used to let two registered primaries match the SAME
reported primary, leaving the other reported primary unmatched and falsely
flagged as an addition. Matching must be one-to-one.

Run: python -m pytest outcome_switching/test_compute_diffs_matching.py -q
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from compute_diffs import compute_trial_diff, best_match  # noqa: E402


def test_best_match_excludes_claimed_candidates():
    target = {"measure": "cardiovascular death or heart failure hospitalization"}
    cands = [
        {"title": "cardiovascular death or heart failure hospitalization"},  # 0
        {"title": "all cause mortality"},                                     # 1
    ]
    idx0, s0 = best_match(target, cands, "measure", "title")
    assert idx0 == 0 and s0 >= 0.55
    # once index 0 is claimed, the same target no longer matches it
    idx1, s1 = best_match(target, cands, "measure", "title", exclude={0})
    assert idx1 != 0


def test_duplicate_titles_do_not_create_false_addition():
    """Two registered primaries whose best match is the same reported primary
    must not both claim it — the second matches the other reported primary, so
    NO false 'addition' is raised."""
    trial = {
        "nct_id": "NCT_DUP",
        "registered_primary": [
            {"measure": "cardiovascular death or hf hospitalization"},
            {"measure": "cardiovascular death or hf hospitalisation"},  # near-dup
        ],
        "registered_secondary": [],
        "reported_primary": [
            {"title": "cardiovascular death or hf hospitalization"},
            {"title": "cardiovascular death or hf hospitalisation"},
        ],
        "reported_secondary": [],
    }
    flags = compute_trial_diff(trial)
    # Both registered primaries find a distinct reported primary -> nothing
    # left unmatched -> no additions/promotions fabricated.
    assert flags["additions"] == [], flags["additions"]
    assert flags["promotions"] == [], flags["promotions"]
