"""Tests for protocol pre-registration by git commit (E2, staged)."""
import os, sys, json
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(REPO, 'scripts'))
import preregister_protocol as pre
import protocol_diff as pdiff
import inject_protocol_badge as badge

GOOD = {
    "review_id": "TEST_RV",
    "pico": {"population": "adults", "intervention": "drug X",
             "comparator": "placebo", "outcomes": ["primary: death"]},
    "primary_outcome": "All-cause mortality at 12 months",
    "planned_analysis": {"model": "random-effects", "effect_measure": "OR"},
    "search": {"databases": ["ClinicalTrials.gov"], "date_run": None, "strategy": "x"},
}


def test_validate_rejects_incomplete():
    bad = {"review_id": "X"}
    assert pre.validate(bad)                      # missing fields -> errors
    assert pre.validate(GOOD) == []               # complete -> no errors


def test_lock_and_tamper_detection(tmp_path):
    p = tmp_path / "TEST_RV.json"
    p.write_text(json.dumps(GOOD), encoding='utf-8')
    r = pre.lock(str(p), now_utc="2026-07-12T00:00:00Z")
    assert r['ok'] and len(r['lock']['protocol_sha256']) == 64
    # unchanged -> check passes
    assert pre.check(str(p))['ok'] is True
    # tamper the pre-specified primary outcome -> check must FAIL
    tampered = dict(GOOD); tampered['primary_outcome'] = "Something else entirely"
    p.write_text(json.dumps(tampered), encoding='utf-8')
    c = pre.check(str(p))
    assert c['ok'] is False and 'CHANGED' in c['reason']


def test_diff_detects_primary_switch(tmp_path, monkeypatch):
    # a fake app whose PRIMARY is a different outcome than the registered one
    app = tmp_path / "APP_REVIEW.html"
    app.write_text('<html><script>const a={realData:{"NCT1":{name:"T",'
                   'allOutcomes:[{title:"Progression-free survival (primary)",'
                   'type:"PRIMARY",estimandType:"HR"}]}}};</script></html>', encoding='utf-8')
    p = tmp_path / "TEST_RV.json"
    p.write_text(json.dumps(GOOD), encoding='utf-8')
    pre.lock(str(p), now_utc="2026-07-12T00:00:00Z")
    d = pdiff.diff(str(p), str(app))
    assert d['verdict'] == 'DRIFT'
    assert any(f['code'] == 'primary_outcome_switch' for f in d['findings'])


def test_diff_concordant_on_matching_primary(tmp_path):
    app = tmp_path / "APP2_REVIEW.html"
    app.write_text('<html><script>const a={realData:{"NCT1":{name:"T",'
                   'allOutcomes:[{title:"All-cause mortality at 12 months (primary)",'
                   'type:"PRIMARY",estimandType:"OR"}]}}};</script></html>', encoding='utf-8')
    p = tmp_path / "TEST_RV.json"
    p.write_text(json.dumps(GOOD), encoding='utf-8')
    pre.lock(str(p), now_utc="2026-07-12T00:00:00Z")
    d = pdiff.diff(str(p), str(app))
    assert not any(f['code'] == 'primary_outcome_switch' for f in d['findings'])


def test_underspecified_primary_flagged(tmp_path):
    # a vague primary ("clinical efficacy") must be flagged as ungameable-drift
    app = tmp_path / "APP4_REVIEW.html"
    app.write_text('<html><script>const a={realData:{"NCT1":{name:"T",'
                   'allOutcomes:[{title:"Overall survival (primary)",type:"PRIMARY",'
                   'estimandType:"HR"}]}}};</script></html>', encoding='utf-8')
    vague = dict(GOOD); vague['primary_outcome'] = "clinical efficacy"
    p = tmp_path / "TEST_RV.json"
    p.write_text(json.dumps(vague), encoding='utf-8')
    pre.lock(str(p), now_utc="2026-07-12T00:00:00Z")
    d = pdiff.diff(str(p), str(app))
    assert any(f['code'] == 'underspecified_primary' for f in d['findings'])

def test_committed_before_search_requires_head_content(tmp_path):
    # a protocol outside the repo (or not at HEAD) must NOT be marked committed
    p = tmp_path / "TEST_RV.json"
    p.write_text(json.dumps(GOOD), encoding='utf-8')
    r = pre.lock(str(p), now_utc="2026-07-12T00:00:00Z")
    assert r['lock']['committed_before_search'] is False

def test_badge_injects_idempotently(tmp_path):
    app = tmp_path / "APP3_REVIEW.html"
    app.write_text('<html><body><h1>x</h1></body></html>', encoding='utf-8')
    p = tmp_path / "TEST_RV.json"
    p.write_text(json.dumps(GOOD), encoding='utf-8')
    pre.lock(str(p), now_utc="2026-07-12T00:00:00Z")
    badge.inject(str(p), str(app), apply=True)
    badge.inject(str(p), str(app), apply=True)   # second time must not duplicate
    assert open(str(app), encoding='utf-8').read().count('data-rapidmeta-prereg-badge') == 1
