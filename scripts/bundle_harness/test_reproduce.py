"""Offline test suite shipped inside every RapidMeta bundle.

Run:  python -m pytest test_reproduce.py -q      (or: python reproduce.py)

These are the checks a skeptic runs in a clean room. They pass ONLY if the
review reproduces from its own shipped data and nothing has been tampered with.
Pure standard library — no network, no model, no third-party packages.
"""
import hashlib
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, 'harness'))
from pool import dl_pool                              # noqa: E402
from consistency import consistent, implied_rr        # noqa: E402

TOL = 1e-9


def _load(name):
    with open(os.path.join(HERE, 'data', name), encoding='utf-8') as f:
        return f.read()


def _sha(t):
    return hashlib.sha256(t.encode('utf-8')).hexdigest()


def _result():
    return json.loads(_load('result.json'))


def _manifest():
    return json.loads(open(os.path.join(HERE, 'MANIFEST.json'), encoding='utf-8').read())


# --- reproduction ---------------------------------------------------------

def test_pool_logeffect_bit_for_bit():
    r = _result()
    pool = dl_pool([{'y': t['y'], 'v': t['v']} for t in r['trials']])
    assert abs(pool['logEffect'] - r['pooled_DL']['logEffect']) <= TOL


def test_pool_se_bit_for_bit():
    r = _result()
    pool = dl_pool([{'y': t['y'], 'v': t['v']} for t in r['trials']])
    assert abs(pool['se'] - r['pooled_DL']['se']) <= TOL


def test_tau2_bit_for_bit():
    r = _result()
    pool = dl_pool([{'y': t['y'], 'v': t['v']} for t in r['trials']])
    assert abs(pool['tau2'] - r['pooled_DL']['tau2']) <= TOL


def test_at_least_two_trials():
    assert len(_result()['trials']) >= 2


def test_all_variances_positive():
    assert all(t['v'] > 0 for t in _result()['trials'])


def test_ci_ordering():
    r = _result()['pooled_DL']
    assert r['lci'] < r['logEffect'] < r['uci']


# --- count/effect consistency (per trial) ---------------------------------

def test_counts_consistent_with_effect_direction():
    r = _result()
    measure = r['measure']
    if measure not in ('OR', 'RR', 'HR', 'IRR'):
        return  # non-ratio measure: nothing to check
    for t in r['trials']:
        if None in (t.get('tE'), t.get('tN'), t.get('cE'), t.get('cN')):
            continue
        ratio = math.exp(t['y'])
        assert consistent(t['tE'], t['tN'], t['cE'], t['cN'], measure, ratio) is not False, \
            f"{t['id']} counts contradict {measure}={ratio:.3f}"


def test_no_impossible_counts():
    for t in _result()['trials']:
        for a, b in (('tE', 'tN'), ('cE', 'cN')):
            if t.get(a) is not None and t.get(b) is not None:
                assert 0 <= t[a] <= t[b]


# --- tamper detection -----------------------------------------------------

def test_manifest_data_intact():
    man = _manifest()
    for fn, want in man.get('sha256', {}).items():
        assert _sha(_load(fn)) == want, f"{fn} tampered"


def test_tamper_is_detected():
    """A flipped digit in the data must break the manifest hash."""
    man = _manifest()
    raw = _load('realData.json')
    assert _sha(raw) == man['sha256']['realData.json']
    assert _sha(raw.replace('0', '9', 1)) != man['sha256']['realData.json']


def test_result_and_realdata_same_trial_ids():
    r = _result()
    rd = json.loads(_load('realData.json'))
    ids_rd = set(rd.keys()) if isinstance(rd, dict) else set()
    ids_res = set(t['id'] for t in r['trials'])
    assert ids_res.issubset(ids_rd) or not ids_rd


def test_implied_rr_matches_recorded_direction():
    r = _result()
    if r['measure'] not in ('OR', 'RR', 'HR', 'IRR'):
        return
    for t in r['trials']:
        if None in (t.get('tE'), t.get('tN'), t.get('cE'), t.get('cN')):
            continue
        rr = implied_rr(t['tE'], t['tN'], t['cE'], t['cN'])
        if rr is None:
            continue
        # both should sit on the same side of 1 (allowing the neutral band)
        eff = math.exp(t['y'])
        if (rr - 1) * (eff - 1) < 0:
            assert abs(rr - 1) < 0.15 or abs(eff - 1) < 0.15, \
                f"{t['id']}: implied {rr:.3f} vs effect {eff:.3f} opposite sides"
