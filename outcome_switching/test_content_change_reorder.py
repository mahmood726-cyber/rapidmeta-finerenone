"""Regression test for reordering-robust content-change detection.

Comparing a v1 primary only against cur_primaries[0] flagged a spurious content
change when a multi-primary trial's outcomes were merely reordered. best_
primary_scores compares against the BEST-matching current primary instead
(validated on live data: 43 -> 39 content-change candidates, 4 reordering false
positives removed).

Run: python -m pytest outcome_switching/test_content_change_reorder.py -q
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from detect_content_changes import best_primary_scores  # noqa: E402

V1 = "cardiovascular death or heart failure hospitalization composite"


def test_reordered_primary_is_not_a_content_change():
    # v1's primary now sits SECOND among the current primaries; first-vs-first
    # would look like a total change, but best-match recovers the high overlap.
    cur = [
        "change in six minute walk distance from baseline",   # unrelated, listed first
        "cardiovascular death or heart failure hospitalization composite",  # the match
    ]
    title_jac, content_jac, best = best_primary_scores(V1, cur)
    assert content_jac > 0.8, content_jac        # strong match found (not flagged)
    assert best == cur[1]


def test_genuine_content_change_still_flagged():
    cur = ["change in left ventricular ejection fraction at 12 months"]
    title_jac, content_jac, _ = best_primary_scores(V1, cur)
    # low overlap on both dimensions -> a real content-change candidate
    assert content_jac < 0.30 and title_jac < 0.50


def test_single_primary_unchanged_behaviour():
    cur = ["cardiovascular death or heart failure hospitalization composite"]
    _, content_jac, best = best_primary_scores(V1, cur)
    assert content_jac == 1.0 and best == cur[0]
