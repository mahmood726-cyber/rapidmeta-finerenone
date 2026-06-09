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

# Classes that must always be zero (genuine hard corruption + the two
# clinical-data defects that were previously baseline-locked and are now
# source-remediated to zero portfolio-wide):
#   implausible_ratio: was EBOLA ring-vaccine RR=0 -- that trial now carries the
#     real zero-cell 2x2 (tE:0,tN:2119,cE:16,cN:2041) with publishedHR:null, so
#     the pooled RR is computed with continuity correction, not a hardcoded 0.
#   additive_ratio_ci: was OUD NCT00604682 HR 7.0 [3,11] -- the impossible
#     additive ratio CI has been nulled (publishedHR/CI:null).
# Both verified 0 across all *_REVIEW*.html; the gate now ENFORCES zero rather
# than permitting a known defect. (A ratio value on a CONTINUOUS outcome is NOT
# flagged -- publishedHR is a generic effect field and MD/RD CIs are additive.)
HARD_ZERO = ("impossible_2x2", "none_leak", "inverted_ci", "bad_nct", "bad_pmid",
             "bad_doi", "implausible_ratio", "additive_ratio_ci")
# No known-permitted defects remain. Kept as a forward guard: any future
# tracked-but-not-yet-remediated class can be added here with a max count.
BASELINE_MAX = {}


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


def _load_dia():
    spec = importlib.util.spec_from_file_location(
        "dia", ROOT / "scripts" / "data_integrity_audit.py")
    dia = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(dia)
    return dia


def test_detects_nulle_exponent_corruption(tmp_path):
    # Regression: `tN:nulle4` (a `null` fused with an exponent) must be caught,
    # not silently read as a valid `null`. The extraction alternation used to put
    # `null` before the `nulle<digits>` token, so the `e4` was never seen.
    dia = _load_dia()
    html = ('<script>const x={realData:{"NCT02048007":{name:"M",tE:null,'
            'tN:nulle4,cE:null,cN:nulle4,publishedHR:null}}};</script>')
    f = tmp_path / "BROKEN_REVIEW.html"
    f.write_text(html, encoding="utf-8")
    findings = dia.audit_app(str(f))
    leaks = [x for x in findings if x["class"] == "none_leak"]
    assert leaks, f"nulle4 corruption not detected; findings={findings}"
    assert any("nulle4" in x["detail"] for x in leaks)


def test_plain_null_and_minified_var_not_flagged(tmp_path):
    # `null` is valid; the minified variable name `null0` (no `e`) is not corruption.
    dia = _load_dia()
    assert dia.is_bad_token("null") is False
    assert dia.is_bad_token("null0") is False
    assert dia.is_bad_token("nulle4") is True


def test_known_defects_do_not_grow():
    counts, _ = _audit_counts()
    grown = {c: (counts.get(c, 0), mx) for c, mx in BASELINE_MAX.items()
             if counts.get(c, 0) > mx}
    assert not grown, (
        f"Known-defect classes grew beyond baseline (class: actual>baseline): {grown}. "
        f"A regeneration/extraction added new defects -- fix at source.")
