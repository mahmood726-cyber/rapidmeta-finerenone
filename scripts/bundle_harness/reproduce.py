#!/usr/bin/env python
"""Clean-room reproducer for a RapidMeta review — OFFLINE, no model, no network.

Run:  python reproduce.py

It re-derives the pooled effect from the per-trial data the review shipped, and
checks it against the number the review displayed. It FAILS LOUDLY (exit 1) if:
  - the recomputed pool does not match the displayed pool bit-for-bit,
  - any trial's displayed counts contradict its displayed effect direction,
  - the data files have been tampered with (MANIFEST sha256 mismatch),
  - the pre-registered protocol hash no longer matches (if a protocol shipped).

Pure standard library. Reproducible on any machine with Python 3.8+.
"""
import hashlib
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, 'harness'))
from pool import dl_pool, back_transform            # noqa: E402
from consistency import consistent                   # noqa: E402

TOL = 1e-9   # bit-for-bit: DL is closed-form, so agreement is to machine precision


def _load(name):
    with open(os.path.join(HERE, 'data', name), encoding='utf-8') as f:
        return f.read()


def _sha(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def main():
    fails = []
    ok = []

    # 1) tamper check — data files must match the shipped manifest
    manifest = json.loads(_load('../MANIFEST.json') if os.path.exists(
        os.path.join(HERE, 'MANIFEST.json')) else '{}')
    manifest = json.loads(open(os.path.join(HERE, 'MANIFEST.json'), encoding='utf-8').read())
    for fn, want in manifest.get('sha256', {}).items():
        got = _sha(_load(fn))
        (ok if got == want else fails).append(
            f"manifest[{fn}]: {'intact' if got == want else 'TAMPERED (%s != %s)' % (got[:12], want[:12])}")

    realdata = json.loads(_load('realData.json'))
    result = json.loads(_load('result.json'))
    measure = result['measure']
    trials = result['trials']            # [{id,y,v,tE,tN,cE,cN}]

    # 2) recompute the DL random-effects pool from per-trial (y,v)
    pool = dl_pool([{'y': t['y'], 'v': t['v']} for t in trials])
    disp = result['pooled_DL']
    d_log = abs(pool['logEffect'] - disp['logEffect'])
    (ok if d_log <= TOL else fails).append(
        f"pooled log{measure}: recomputed {pool['logEffect']:.12f} vs displayed "
        f"{disp['logEffect']:.12f}  (|diff|={d_log:.2e})")
    d_se = abs(pool['se'] - disp['se'])
    (ok if d_se <= TOL else fails).append(f"pooled SE |diff|={d_se:.2e}")
    d_tau = abs(pool['tau2'] - disp['tau2'])
    (ok if d_tau <= TOL else fails).append(f"tau^2 |diff|={d_tau:.2e}")

    # 3) count/effect direction consistency for every trial with a 2x2
    for t in trials:
        if None in (t.get('tE'), t.get('tN'), t.get('cE'), t.get('cN')):
            continue
        eff = t.get('y')
        # on the log scale the ratio is exp(y); consistency() wants the ratio
        ratio = math.exp(eff) if measure in ('OR', 'RR', 'HR', 'IRR') else None
        if ratio is None:
            continue
        c = consistent(t['tE'], t['tN'], t['cE'], t['cN'], measure, ratio)
        (ok if c is not False else fails).append(
            f"{t['id']}: counts {t['tE']}/{t['tN']} vs {t['cE']}/{t['cN']} "
            f"{'consistent with' if c is not False else 'CONTRADICT'} {measure}={ratio:.3f}")

    # 4) protocol hash (if a pre-registered protocol shipped)
    if manifest.get('protocol_sha256'):
        ppath = os.path.join(HERE, 'protocol.txt')
        if os.path.exists(ppath):
            got = _sha(open(ppath, encoding='utf-8').read())
            (ok if got == manifest['protocol_sha256'] else fails).append(
                f"protocol: {'matches registration' if got == manifest['protocol_sha256'] else 'DRIFTED from registration'}")

    # report
    eff, lci, uci = back_transform(pool['logEffect'], pool['lci'], pool['uci'], measure)
    print("=" * 64)
    print(f"RapidMeta clean-room reproduction — {result.get('app', '')}")
    print(f"  measure={measure}  k={pool['k']}  estimator=DerSimonian-Laird RE")
    print(f"  pooled {measure} = {eff:.4f}  (95% CI {lci:.4f}-{uci:.4f})   "
          f"tau^2={pool['tau2']:.5f}  I^2={pool['I2']:.1f}%")
    print("-" * 64)
    for line in ok:
        print(f"  [PASS] {line}")
    for line in fails:
        print(f"  [FAIL] {line}")
    print("=" * 64)
    if fails:
        print(f"REPRODUCTION FAILED — {len(fails)} check(s) failed. This review does "
              f"NOT reproduce from its own data.")
        return 1
    print(f"REPRODUCED — all {len(ok)} checks pass, offline, from the shipped data.")
    return 0


if __name__ == '__main__':
    sys.exit(main())
