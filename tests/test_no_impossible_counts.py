"""Guard: no app's realData may contain an arithmetically impossible 2x2.

A prior systemic extraction bug left 154 apps with tE>tN or cE>cN (event count
exceeding the arm size) -- schema-valid but semantically impossible numbers that
produced garbage pools (see findings/nonpoolable_recovery_2026-05-31.md). After
the ctgov source-recheck remediation the portfolio is clean; this test fails the
build if any impossible count is reintroduced by a future generator/injector run.
"""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("vv", ROOT / "validate_living_ma_portfolio.py")
vv = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(vv)


def _scan():
    bad = []
    for f in sorted(ROOT.glob("*_REVIEW.html")) + sorted(ROOT.glob("*_REVIEW_FULL.html")):
        html = f.read_text(encoding="utf-8", errors="replace")
        for nct, d in vv.extract_real_data(html).items():
            tE, tN, cE, cN = d.get("tE"), d.get("tN"), d.get("cE"), d.get("cN")
            if (tN and tE and tE > tN) or (cN and cE and cE > cN):
                bad.append(f"{f.name}:{nct} tE={tE} tN={tN} cE={cE} cN={cN}")
    return bad


def test_no_impossible_2x2_counts_portfolio_wide():
    bad = _scan()
    assert not bad, (
        f"{len(bad)} impossible 2x2 counts (event > arm size) found -- re-run the "
        f"ctgov recheck/apply remediation:\n  " + "\n  ".join(bad[:20])
    )
