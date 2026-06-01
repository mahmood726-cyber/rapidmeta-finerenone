"""Guard for GLP1_CVOT_REVIEW.html — the curated GLP-1 RA CVOT meta-analysis.

Locks in the 2026-06-01 data fix. Two prior defects:
  1. LEADER / SUSTAIN-6 / AMPLITUDE-O shipped with tE:null,cE:null in realData,
     so 3 of 10 trials (16,713 patients, HR 0.73-0.87) silently dropped from any
     count-based pool or fell back to a different estimand (logHR vs logOR/RR).
  2. A transcription error swapped AMPLITUDE-O placebo MACE events (125) for its
     renal-composite count (250) in a copyable R example.

The portfolio-wide test_no_impossible_counts only catches tE>tN; null cells and
wrong-but-possible values pass it. This test asserts every included trial has a
complete 2x2 AND that the count-derived risk ratio agrees with the published HR.
"""
from pathlib import Path
import importlib.util

ROOT = Path(__file__).resolve().parent.parent
FILE = ROOT / "GLP1_CVOT_REVIEW.html"

_spec = importlib.util.spec_from_file_location("vv", ROOT / "validate_living_ma_portfolio.py")
vv = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(vv)

EXPECTED_TRIALS = {
    "ELIXA", "LEADER", "SUSTAIN-6", "EXSCEL", "HARMONY",
    "REWIND", "PIONEER 6", "SELECT", "AMPLITUDE-O", "SOUL",
}
# realData stores HARMONY under its full label
EXPECTED_TRIALS = {("HARMONY Outcomes" if t == "HARMONY" else t) for t in EXPECTED_TRIALS}


def _data():
    return vv.extract_real_data(FILE.read_text(encoding="utf-8", errors="replace"))


def test_all_ten_cvots_present():
    names = {d.get("name") for d in _data().values()}
    assert EXPECTED_TRIALS <= names, f"missing trials: {EXPECTED_TRIALS - names}"


def test_every_included_trial_has_complete_2x2():
    """No null/missing event cell — this is what silently dropped 3 trials."""
    incomplete = []
    for nct, d in _data().items():
        for k in ("tE", "tN", "cE", "cN"):
            v = d.get(k)
            if v is None or not isinstance(v, (int, float)):
                incomplete.append(f"{d.get('name', nct)}.{k}={v!r}")
    assert not incomplete, "incomplete 2x2 cells: " + ", ".join(incomplete)


def test_count_derived_rr_agrees_with_published_hr():
    """RR from the 2x2 must track publishedHR (catches transcription swaps).

    RR != HR exactly, so the tolerance is loose (0.15 absolute); the AMPLITUDE-O
    250-for-125 swap produced RR ~1.51 vs HR 0.73 -- well outside this band.
    """
    off = []
    for nct, d in _data().items():
        tE, tN, cE, cN, hr = (d.get(k) for k in ("tE", "tN", "cE", "cN", "publishedHR"))
        if not all(isinstance(x, (int, float)) for x in (tE, tN, cE, cN, hr)):
            continue
        if tN == 0 or cN == 0 or cE == 0:
            continue
        rr = (tE / tN) / (cE / cN)
        if abs(rr - hr) > 0.15:
            off.append(f"{d.get('name', nct)}: RR={rr:.3f} vs publishedHR={hr}")
    assert not off, "count-derived RR disagrees with published HR: " + "; ".join(off)
