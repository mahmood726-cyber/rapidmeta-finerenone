"""Regression test for _to_int (thousands-separator count parsing).

A bare int('1,807') raises ValueError and aborts the whole CT.gov extraction
of a trial (n_per_group dict comprehension has no guard). The negated-count /
European-decimal lesson: counts may carry a thousands separator.

Run: python -m pytest test_extract_to_int.py -q
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from extract_ctgov_results import _to_int  # noqa: E402


def test_thousands_separator_count():
    assert _to_int("1,807") == 1807          # was: ValueError -> whole extraction aborts
    assert _to_int("5,050") == 5050
    assert _to_int("1807") == 1807
    assert _to_int(1807) == 1807
    assert _to_int(1807.0) == 1807


def test_non_numeric_and_missing_default():
    assert _to_int(None) == 0
    assert _to_int("") == 0
    assert _to_int("N/A") == 0
    assert _to_int("N/A", default=-1) == -1
    assert _to_int(True) == 0                 # bool excluded (isinstance(True,int) is True)


def test_float_string_count():
    assert _to_int("42.0") == 42
