"""Regression test: review printout shows a p-value of 0.0 (P2, if-value drops-0).

Run: python -m pytest test_review_pvalue.py -q
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import review_extractions as R  # noqa: E402

BASE = {
    "primary_outcome_title": "CV death or HF hospitalization",
    "extracted": {"measure": "HR", "estimate": 0.86, "lci": 0.77, "uci": 0.96},
}


def test_zero_pvalue_is_shown(capsys):
    p = dict(BASE, extracted=dict(BASE["extracted"], pValue=0.0))
    R.print_extraction(p)
    out = capsys.readouterr().out
    assert "p-value" in out, out          # 0.0 must NOT be hidden by truthiness


def test_nonzero_pvalue_is_shown(capsys):
    p = dict(BASE, extracted=dict(BASE["extracted"], pValue=0.001))
    R.print_extraction(p)
    assert "p-value" in capsys.readouterr().out


def test_missing_pvalue_is_omitted(capsys):
    p = dict(BASE, extracted=dict(BASE["extracted"]))  # no pValue key
    R.print_extraction(p)
    assert "p-value" not in capsys.readouterr().out
