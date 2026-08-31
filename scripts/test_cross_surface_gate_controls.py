#!/usr/bin/env python
"""Synthetic controls for scripts/check_cross_surface_consistency.py.

An audit that cannot produce a zero has not been shown to measure anything, and
an instrument that only ever rejects is not an instrument.  The gate carries
~390 standing findings against the live corpus, so this file supplies the two
things that number alone cannot:

  1. a CLEAN synthetic surface pair the gate must PASS (exit 0);
  2. one targeted perturbation per rule, each of which must make exactly that
     rule fire.

The controls are SYNTHETIC and generated in-code on every run.  They are not
anchored to any live artefact, so fixing a defect in the corpus can never
silently retire them, and they can never leak into a count of real reviews:
every synthetic review is namespaced `__CONTROL_`.

Exit 0 = clean pair passes and every rule fires when provoked.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile

sys.path.insert(0, "scripts")
import check_cross_surface_consistency as gate  # noqa: E402

ok = True


def say(sym, msg):
    print("  {} {}".format(sym, msg))


def assert_(cond, msg):
    global ok
    say("PASS" if cond else "FAIL", msg)
    if not cond:
        ok = False


def clean_pair():
    """A synthetic pair that satisfies every rule."""
    cards = []
    rows = []
    spec = [("A", 4, 0.75, 0.60, 0.94), ("B", 6, 1.20, 1.05, 1.37)]
    for name, k, est, lo, hi in spec:
        f = "__CONTROL_{}_REVIEW.html".format(name)
        cards.append(
            '<a href="{}" class="card ready"><span class="name">Control {}</span>'
            '<span class="pub">Pooled: OR {} ({} to {}), k={}</span></a>'.format(
                f, name, est, lo, hi, k))
        rows.append({
            "file": f, "topic": "__CONTROL_{}".format(name),
            "display_name": "Control {}".format(name),
            "title": "Control {}".format(name), "type": "Pairwise",
            "ncts": ["NCT{:08d}".format(i) for i in range(k)],
            "n_trials": k, "n_treatments": None, "k": k,
            "pooled_OR": est, "ci_low": lo, "ci_high": hi,
            "I2": 12.5 if name == "A" else 30.0, "tau2": 0.0,
            "integrity_flags": 0, "n_with_baseline": k, "stats_pending": False,
            "bucket": "Other", "last_modified": "2026-08-31T00:00:00+01:00",
        })
    html = "<html><body>" + "\n".join(cards) + "</body></html>"
    doc = {"generated": "2026-08-31T00:00:00", "n_total": len(rows),
           "n_pairwise": len(rows), "n_nma": 0, "rows": rows}
    return html, doc


def run(html, doc, tmp):
    ip = os.path.join(tmp, "index.html")
    pp = os.path.join(tmp, "portfolio_index.json")
    with open(ip, "w", encoding="utf-8") as fh:
        fh.write(html)
    with open(pp, "w", encoding="utf-8") as fh:
        json.dump(doc, fh)
    fail, _, _ = gate.check(ip, pp)
    return fail


# Each mutation targets ONE rule.  (code, description, mutate(html, doc))
def m_measure(html, doc):
    return html.replace("Pooled: OR 0.75", "Pooled: HR 0.75"), doc


def m_k(html, doc):
    return html.replace("k=4", "k=9"), doc


def m_estimate(html, doc):
    doc["rows"][0]["pooled_OR"] = 0.41
    return html, doc


def m_interval(html, doc):
    doc["rows"][0]["ci_high"] = 0.88
    return html, doc


def m_pooled_without_k(html, doc):
    doc["rows"][0]["k"] = 1
    return html.replace("k=4", "k=1"), doc


def m_unusable_interval(html, doc):
    doc["rows"][0]["ci_low"] = 0.0
    doc["rows"][0]["ci_high"] = 5.2e31
    return html, doc


def m_nct_harvest(html, doc):
    for r in doc["rows"]:
        r["ncts"] = []
        r["n_trials"] = 0
    return html, doc


def m_derived_count(html, doc):
    doc["rows"][0]["n_trials"] = 99
    return html, doc


def m_counter_rows(html, doc):
    doc["n_total"] = 960
    return html, doc


def m_type_title(html, doc):
    doc["rows"][0]["title"] = "Control A NMA"
    return html, doc


def m_duplicate(html, doc):
    import copy
    dup = copy.deepcopy(doc["rows"][0])
    dup["file"] = "__CONTROL_C_REVIEW.html"
    dup["topic"] = "__CONTROL_C"
    doc["rows"].append(dup)
    doc["n_total"] = len(doc["rows"])
    doc["n_pairwise"] = len(doc["rows"])
    return html, doc


MUTATIONS = [
    ("MEASURE_MISMATCH", "landing page declares HR where portfolio serves OR", m_measure),
    ("K_MISMATCH", "same measure, k=9 on one surface and k=4 on the other", m_k),
    ("ESTIMATE_MISMATCH", "portfolio estimate moved off the published one", m_estimate),
    ("INTERVAL_MISMATCH", "portfolio upper bound moved off the published one", m_interval),
    ("POOLED_WITHOUT_K", "pooled estimate over a single study", m_pooled_without_k),
    ("UNUSABLE_INTERVAL", "CI spanning 30+ orders of magnitude", m_unusable_interval),
    ("NCT_HARVEST_EMPTY", "ncts empty on every row beside live estimates", m_nct_harvest),
    ("DERIVED_COUNT_MISMATCH", "n_trials disagrees with len(ncts)", m_derived_count),
    ("COUNTER_ROWS_MISMATCH", "header says 960 over a 2-row array", m_counter_rows),
    ("TYPE_TITLE_MISMATCH", 'title says NMA while typed "Pairwise"', m_type_title),
    ("DUPLICATE_ANALYSIS", "one analysis shipped as two reviews", m_duplicate),
]


def main():
    print("synthetic controls for the cross-surface gate")
    print("=" * 72)

    with tempfile.TemporaryDirectory() as tmp:
        # ---- 1. the gate must be able to PASS ---------------------------
        print("\n[1] NEGATIVE CONTROL - a clean synthetic pair must PASS")
        html, doc = clean_pair()
        fail = run(html, doc, tmp)
        assert_(fail == [],
                "clean pair returns 0 findings"
                + ("" if not fail else "  got: {}".format([f[:2] for f in fail])))

        # ---- 2. every rule must be able to FIRE -------------------------
        print("\n[2] POSITIVE CONTROLS - one perturbation per rule")
        for code, desc, mutate in MUTATIONS:
            html, doc = clean_pair()
            html, doc = mutate(html, doc)
            fail = run(html, doc, tmp)
            codes = {c for c, _, _ in fail}
            assert_(code in codes,
                    "{:24s} fires on: {}{}".format(
                        code, desc,
                        "" if code in codes else "   [got {}]".format(sorted(codes))))

    print("\n" + "=" * 72)
    print("CONTROLS PROVEN: the gate passes clean input and every rule can fire."
          if ok else "CONTROLS FAILED: see FAIL lines above.")
    return 0 if ok else 1


if __name__ == "__main__":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.exit(main())
