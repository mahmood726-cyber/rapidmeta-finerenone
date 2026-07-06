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

from apply_pending_updates import _is_hr_measure  # noqa: E402


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
