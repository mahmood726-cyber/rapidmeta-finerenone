"""Portfolio-wide data-integrity regression gate.

Runs scripts/data_integrity_audit.py across every *_REVIEW*.html and enforces:

  * HARD-corruption classes must stay at ZERO. These encode the defect classes
    fixed in review (impossible 2x2 counts, None/null-leaked numbers, inverted
    CIs, malformed NCT/PMID/DOI). They are gone portfolio-wide; this stops any
    regeneration/extraction run from quietly reintroducing them.

  * Known quality defects are BASELINE-LOCKED (cannot grow). The additively
    symmetric ratio CIs (a derivation bug) and the implausible-ratio mislabels
    are tracked for source-verified remediation; the gate fails if a new app
    introduces more of them, so the count can only go down.
"""
import importlib.util
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Classes that must always be zero. ratio_on_continuous / additive_ratio_ci were
# the 175-trial "continuous-as-ratio" defect (a ratio value on an MD outcome);
# they were nulled portfolio-wide via scripts/fix_continuous_as_ratio.py and must
# never come back.
HARD_ZERO = ("impossible_2x2", "none_leak", "inverted_ci", "bad_nct", "bad_pmid",
             "bad_doi", "ratio_on_continuous", "additive_ratio_ci")
# Known-defect baselines. Lower is better; must not increase. The single residual
# implausible_ratio is the EBOLA ring-vaccine RR=0 (a genuine zero-cell, not
# corruption); locked so a regeneration can't add new ones.
BASELINE_MAX = {"implausible_ratio": 1}


def _audit_counts():
    spec = importlib.util.spec_from_file_location(
        "dia", ROOT / "scripts" / "data_integrity_audit.py")
    dia = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(dia)
    import glob
    findings = []
    for p in sorted(glob.glob(str(ROOT / "*_REVIEW*.html"))):
        findings.extend(dia.audit_app(p))
    return Counter(f["class"] for f in findings), findings


def test_no_hard_data_corruption():
    counts, findings = _audit_counts()
    offenders = {c: counts[c] for c in HARD_ZERO if counts.get(c)}
    if offenders:
        sample = [f for f in findings if f["class"] in offenders][:10]
        detail = "\n".join(f"  [{f['class']}] {f['app']} :: {f['trial']} -- {f['detail']}"
                           for f in sample)
        raise AssertionError(
            f"Hard data-corruption reintroduced: {offenders}\n{detail}")


def test_known_defects_do_not_grow():
    counts, _ = _audit_counts()
    grown = {c: (counts.get(c, 0), mx) for c, mx in BASELINE_MAX.items()
             if counts.get(c, 0) > mx}
    assert not grown, (
        f"Known-defect classes grew beyond baseline (class: actual>baseline): {grown}. "
        f"A regeneration/extraction added new defects -- fix at source.")
