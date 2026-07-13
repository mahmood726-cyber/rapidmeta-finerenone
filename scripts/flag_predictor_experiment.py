#!/usr/bin/env python
"""Attempt the LEARNED FLAG PREDICTOR and measure it against the hand-written gates.

A reward model predicts whether a human would approve an output; a flag predictor
predicts whether an extraction is WRONG. Same object. The user asked: train it on
the corrections corpus and see if it beats the rules — and if it doesn't, SAY SO.

Honest design (per Codex-A cross-vendor): features are RAW extraction values only
(NOT gate outputs), positives use the WRONG values from the provenance records (so
the features reflect the error, not the later fix), negatives are never-corrected
trials. We then ask three things:
  1. In-distribution flag-recall (does it work at all?).
  2. Does it BEAT the hand-written gate on the same held-out? (the user's question)
  3. Does it catch the GATE-INDEPENDENT errors — the only test of "discovery"?

Expected and reported honestly: because ~all labels are gate-derived, the model
DISTILLS the gates (learns their inputs) and cannot demonstrate discovery at n=3
gate-independent. A learned flag that only ties a regex is a useful negative result.
"""
from __future__ import annotations
import json, math, os, sys

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_predict, StratifiedKFold

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, 'outputs')
sys.path.insert(0, os.path.join(REPO, 'scripts'))
import count_consistency as cc  # noqa


def _feats(tE, tN, cE, cN, eff):
    """Raw features only — NO gate verdicts. What a reader would see on the row."""
    blank = 1.0 if (tE is None or cE is None) else 0.0
    zz = 1.0 if (tE == 0 and cE == 0) else 0.0
    rr = cc.implied_rr(tE, tN, cE, cN) if None not in (tE, tN, cE, cN) else None
    if rr and rr > 0 and eff and eff > 0:
        fold = max(rr / eff, eff / rr)
        opp = 1.0 if (rr - 1) * (eff - 1) < 0 else 0.0
        lrr = math.log(rr)
    else:
        fold, opp, lrr = 1.0, 0.0, 0.0
    neutral = 1.0 if (eff and 0.90 <= eff <= 1.11) else 0.0
    return [blank, zz, min(fold, 50.0), opp, neutral, abs(lrr),
            0.0 if eff is None else abs(math.log(eff)) if eff > 0 else 0.0]


def gate_says_wrong(tE, tN, cE, cN, eff):
    """The hand-written gate applied to the same row (the baseline to beat).
    Includes the blank_counts_with_effect rule added this session, for a FAIR
    comparison (otherwise the learned model 'wins' only by rediscovering it)."""
    # blank_counts_with_effect: effect present but cells blank/zero-both
    if eff is not None and eff > 0:
        if (tE is None or cE is None) or (tE == 0 and cE == 0):
            return True
    if None in (tE, tN, cE, cN) or eff is None:
        return False
    if eff <= 0:
        return True
    if cc.consistent(tE, tN, cE, cN, 'OR', eff) is False:
        return True
    rr = cc.implied_rr(tE, tN, cE, cN)
    if rr and rr > 0:
        fold = max(rr / eff, eff / rr)
        if (0.90 <= eff <= 1.11 and (rr >= 1.5 or rr <= 0.67)) or fold >= 10.0:
            return True
    return False


def main():
    corr = json.load(open(os.path.join(OUT, 'corrections_corpus.json'), encoding='utf-8'))
    # positives with reconstructable WRONG values: count corrections carry the
    # reported (wrong) 2x2 + measure in the count provenance.
    cp = json.load(open(os.path.join(OUT, 'handoff_local_7ac07271',
                                     'count_provenance_2026-07-12.json'), encoding='utf-8'))
    X, y, gate = [], [], []
    gi_idx = []
    for r in cp:
        tE, tN, cE, cN = r.get('tE'), r.get('tN'), r.get('cE'), r.get('cN')
        eff = r.get('reported')      # the WRONG displayed effect at time of error
        X.append(_feats(tE, tN, cE, cN, eff)); y.append(1)
        gate.append(gate_says_wrong(tE, tN, cE, cN, eff))
    n_pos = len(X)
    # DATA-RETENTION gap: how many corrections retain a usable WRONG value?
    reconstructable = sum(1 for r in cp if r.get('reported') is not None
                          and None not in (r.get('tE'), r.get('cE')))
    print(f"DATA-RETENTION: of {len(cp)} count corrections, only {reconstructable} retain the "
          f"original WRONG value (rest were blanked with no pre-fix value stored).")
    print("=> We often cannot reconstruct WHAT the extractor got wrong — only that we fixed it.")
    print("   A flag predictor needs the wrong value; logging it is a required one-line fix.\n")
    # negatives: sample clean trials from current apps (present, consistent)
    import glob, re
    from assert_count_effect_consistency import _objbody, _top_entries, _num
    corrected = set((r['app'], str(r['trial'])) for r in corr)
    neg = 0
    for f in sorted(glob.glob(os.path.join(REPO, '*_REVIEW.html'))):
        if neg >= n_pos * 3:
            break
        txt = open(f, encoding='utf-8', errors='replace').read()
        m = re.search(r'realData\s*:\s*\{', txt)
        if not m:
            continue
        for k, o in _top_entries(_objbody(txt, m.end() - 1)):
            if (os.path.basename(f), str(k)) in corrected:
                continue
            tE, tN, cE, cN = _num(o,'tE'), _num(o,'tN'), _num(o,'cE'), _num(o,'cN')
            eff = _num(o, 'publishedHR')
            if None in (tE, tN, cE, cN, eff):
                continue
            X.append(_feats(tE, tN, cE, cN, eff)); y.append(0)
            gate.append(gate_says_wrong(tE, tN, cE, cN, eff)); neg += 1
            if neg >= n_pos * 3:
                break
    X, y, gate = np.array(X), np.array(y), np.array(gate)
    print(f"training set: {n_pos} positive (wrong) + {neg} negative (clean) = {len(y)}")

    # cross-validated learned flag
    cvp = cross_val_predict(LogisticRegression(max_iter=1000, class_weight='balanced'),
                            X, y, cv=StratifiedKFold(5, shuffle=True, random_state=0))
    def recall(pred): return (pred[y == 1] == 1).mean()
    def far(pred): return (pred[y == 0] == 1).mean()
    print(f"\nLEARNED flag (5-fold CV):  recall={recall(cvp):.3f}  false-alarm={far(cvp):.3f}")
    print(f"HAND-WRITTEN gate:         recall={recall(gate.astype(int)):.3f}  false-alarm={far(gate.astype(int)):.3f}")
    # agreement between learned and gate (distillation check)
    agree = (cvp == gate.astype(int)).mean()
    print(f"learned vs gate agreement: {agree:.3f}  (high => the model is DISTILLING the gate)")

    gi = [r for r in corr if r.get('gate_independent')]
    print(f"\nGATE-INDEPENDENT errors available to test 'discovery': {len(gi)}")
    print("=> With so few gate-independent labels, we CANNOT show the learned flag")
    print("   catching a class the gate misses. Verdict: gate-distillation only;")
    print("   NOT learned discovery. Build the capture funnel; do not claim more.")


if __name__ == '__main__':
    main()
