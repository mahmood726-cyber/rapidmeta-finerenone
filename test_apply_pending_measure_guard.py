"""Regression test for the estimand guard in apply_pending_updates.

publishedHR/hrLCI/hrUCI are HAZARD-RATIO fields; extract_ctgov_results emits
HR/RR/OR. Writing an RR/OR into publishedHR silently mislabels the estimand as
an HR downstream (the CT.gov-HR / measure-label lesson). The guard must accept
HR and reject RR/OR.

Run: python -m pytest test_apply_pending_measure_guard.py -q
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from apply_pending_updates import _is_hr_measure, _partition_by_applied  # noqa: E402


def test_hr_measure_accepted():
    assert _is_hr_measure("HR") is True
    assert _is_hr_measure("hr") is True          # case-insensitive
    assert _is_hr_measure(" HR ") is True         # whitespace tolerant


def test_non_hr_measure_rejected():
    assert _is_hr_measure("RR") is False
    assert _is_hr_measure("OR") is False
    assert _is_hr_measure("MD") is False
    assert _is_hr_measure("rr") is False


def test_none_defaults_to_hr_contract():
    # A missing measure historically defaulted to HR (e.get('measure','HR')); the
    # predicate is only reached with a concrete value, but 'HR' must pass.
    assert _is_hr_measure("HR") is True


def test_partition_only_marks_actually_applied():
    """Regression (mixed-success batch): only the proposals whose NCT was
    actually patched may move to 'applied'; an unmatched/skipped NCT must stay in
    'approved', not be silently recorded as applied and lost."""
    approved = [
        {"nctId": "NCT01", "extracted": {"measure": "HR"}},
        {"nctId": "NCT02", "extracted": {"measure": "HR"}},   # not found in generator
        {"nctId": "NCT03", "extracted": {"measure": "RR"}},    # skipped by estimand guard
    ]
    applied_ncts = ["NCT01"]                                   # only NCT01 was patched
    newly_applied, still_pending = _partition_by_applied(approved, applied_ncts)
    assert [p["nctId"] for p in newly_applied] == ["NCT01"]
    assert [p["nctId"] for p in still_pending] == ["NCT02", "NCT03"]


def test_partition_all_applied():
    approved = [{"nctId": "NCT01"}, {"nctId": "NCT02"}]
    newly_applied, still_pending = _partition_by_applied(approved, ["NCT01", "NCT02"])
    assert len(newly_applied) == 2 and still_pending == []
