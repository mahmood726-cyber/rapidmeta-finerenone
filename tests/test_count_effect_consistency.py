"""Regression tests for the count-provenance fix (2026-07-12).

Guards the invariant that closes root-cause class #1: a shipped app must never
display arm counts that imply the opposite direction to its displayed ratio
effect. Covers the shared contract, the build gate, and the two confirmed
showcase trials (BARICITINIB BRAVE-AA2, CANAGLIFLOZIN CREDENCE).
"""
import os, sys, glob, re
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(REPO, 'scripts'))
import count_consistency as cc
import assert_count_effect_consistency as gate
import build_gate as bg


# ---- the shared contract ---------------------------------------------------
def test_inverted_counts_flagged():
    # original buggy BRAVE-AA2 table implied the drug fails; effect says it works
    assert cc.consistent(4, 173, 19, 174, 'OR', 7.86) is False
    # CANAGLIFLOZIN buggy table: 35>29 events implies RR>1, but HR<1
    assert cc.consistent(35, 2199, 29, 2202, 'HR', 0.70) is False

def test_correct_counts_pass():
    assert cc.consistent(27, 156, 4, 156, 'OR', 7.86) is True

def test_non_ratio_and_missing_are_undetermined():
    assert cc.consistent(10, 50, 5, 50, 'MD', 1.2) is None
    assert cc.consistent(None, 156, 4, 156, 'OR', 7.86) is None

def test_orient_swaps_inversion():
    tE, tN, cE, cN, status = cc.orient_to_effect(4, 173, 19, 174, 'OR', 7.86)
    assert status == 'swapped' and (tE, cE) == (19, 4)

def test_percentage_never_treated_as_count_via_gate_semantics():
    # a 17.3% vs 2.6% pair mis-stored as "17 events / 2 events" with placebo
    # labelled treatment is exactly the inversion the gate must catch
    assert cc.consistent(2, 156, 17, 156, 'OR', 7.86) is False

def test_zero_cell_direction_is_checkable():
    # cross-vendor hardening: a zero-event arm must not slip the gate.
    # tE=0/100 (protective) vs cE=5/100 with effect 2.0 (harm) -> contradiction
    assert cc.consistent(0, 100, 5, 100, 'OR', 2.0) is False
    # double-zero has no direction -> undetermined
    assert cc.consistent(0, 100, 0, 100, 'OR', 2.0) is None

def test_gate_walks_single_quoted_and_nonncct_keys():
    # cross-vendor coverage hardening: entries keyed by single-quoted, PMID:,
    # or LEGACY- keys must be parsed, not silently skipped.
    body = ("{'NCT01': {name:'A', tE:9, tN:100, cE:3, cN:100, publishedHR:3.0, "
            "estimandType:'OR'}, \"PMID:12345\": {name:\"B\", tE:1, tN:50, cE:10, "
            "cN:50, publishedHR:5.0, estimandType:\"OR\"}}")
    ents = dict(gate._top_entries(body))
    assert 'NCT01' in ents and 'PMID:12345' in ents
    # PMID:12345 is a contradiction (1/50 vs 10/50 implies protective; effect 5.0)
    assert cc.consistent(1, 50, 10, 50, 'OR', 5.0) is False


# ---- the corpus is clean (the whole point) ---------------------------------
def _reviews():
    return sorted(glob.glob(os.path.join(REPO, '*_REVIEW.html')))

@pytest.mark.skipif(not _reviews(), reason="no built apps present")
def test_corpus_has_no_contradictions():
    viol = gate.scan(_reviews())
    assert viol == [], f"{len(viol)} count/effect contradictions still present: " \
                       + ", ".join(f"{v['file']}:{v['nct']}" for v in viol[:10])


# ---- the two named showcase trials -----------------------------------------
def _entry(fname, nct):
    p = os.path.join(REPO, fname)
    if not os.path.exists(p):
        pytest.skip(f"{fname} not present")
    txt = open(p, encoding='utf-8', errors='replace').read()
    m = re.search(r'"?'+nct+r'"?:\{', txt)
    assert m, f"{nct} not found in {fname}"
    return txt[m.start():m.start()+400]

def test_baricitinib_brave_aa2_matches_source():
    e = _entry('BARICITINIB_ALOPECIA_AUTO_FULL_REVIEW.html', 'NCT03899259')
    # 2mg baricitinib 17.3% x156 = 27 ; placebo 2.6% x156 = 4 ; OR ~7.95 ~= 7.86
    assert 'tE:27' in e and 'cE:4' in e and 'tN:156' in e and 'cN:156' in e

def _write(tmp_path, name, body):
    p = tmp_path / name
    p.write_text(f'<html><script>const a={{realData:{{{body}}}}};</script></html>',
                 encoding='utf-8')
    return str(p)

# ---- the MANDATORY gate MUST be able to fail (a gate that can't block is theater)
def test_build_gate_blocks_count_contradiction(tmp_path):
    f = _write(tmp_path, 'BAD_REVIEW.html',
               '"NCT99999999":{name:"B",pmid:"99999999",year:2020,tE:4,tN:173,'
               'cE:19,cN:174,publishedHR:7.86,hrLCI:2.79,hrUCI:22.17,estimandType:"OR"}')
    hard, warn = bg.gate_file(f)
    assert any(h[2] == 'direction' for h in hard)
    assert bg.main(['build_gate', f]) == 1   # exit 1 => build blocked

def test_build_gate_blocks_year_contradiction(tmp_path):
    # PMID 30625070 is 2019 in the committed cache; displayed 2005 -> gap 14
    f = _write(tmp_path, 'BADYEAR_REVIEW.html',
               '"NCT02553317":{name:"X",pmid:"30625070",year:2005,tE:9,tN:72,cE:36,'
               'cN:73,publishedHR:0.5,hrLCI:0.3,hrUCI:0.8,estimandType:"HR"}')
    hard, _ = bg.gate_file(f)
    assert any(h[2] == 'year_contradicts_pubmed' for h in hard)

def test_build_gate_blocks_additive_ratio_ci(tmp_path):
    # an RD (0.085, CI additively symmetric) mislabeled OR must be blocked
    f = _write(tmp_path, 'BADCI_REVIEW.html',
               '"NCT01345929":{name:"R",pmid:"25931244",year:2015,tE:306,tN:398,'
               'cE:275,cN:402,publishedHR:0.085,hrLCI:0.023,hrUCI:0.146,estimandType:"OR"}')
    hard, _ = bg.gate_file(f)
    assert any(h[2] == 'additive_ratio_ci' for h in hard)

def test_build_gate_passes_clean_app(tmp_path):
    f = _write(tmp_path, 'GOOD_REVIEW.html',
               '"NCT03899259":{name:"G",pmid:"35334197",year:2022,tE:27,tN:156,cE:4,'
               'cN:156,publishedHR:7.86,hrLCI:2.79,hrUCI:22.17,estimandType:"OR"}')
    hard, _ = bg.gate_file(f)
    assert hard == []
    assert bg.main(['build_gate', f]) == 0

def test_canagliflozin_credence_blanked_not_contradictory():
    e = _entry('CANAGLIFLOZIN_DKD_AUTO_FULL_REVIEW.html', 'NCT02065791')
    # CT.gov reports the primary as an event-rate (no raw counts) -> counts
    # withheld; the verified HR 0.70 remains for pooling.
    assert 'tE:null' in e and 'cE:null' in e
    assert 'publishedHR:0.7' in e or 'pubHR:.7' in e or 'publishedHR:0.70' in e
