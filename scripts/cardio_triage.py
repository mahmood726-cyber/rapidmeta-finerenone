#!/usr/bin/env python
"""Collapse the cardio inventory to one row per app, then rank by upgrade value.

Upgrade value = clinical importance x (gap between current state and a verified
synthesis). Both factors are scored from evidence in the inventory JSON, not from
recall; every component is printed so the ranking can be argued with.

Usage: python scripts/cardio_triage.py [--json outputs/cardio_triage.json]
"""
from __future__ import annotations

import argparse
import io
import json
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Clinical importance, 1-5, by cardiology domain. Mortality-bearing, guideline-
# defining domains score highest; niche/adjacent domains lowest.
DOMAIN_IMPORTANCE = {
    "Heart failure": 5,
    "MI / ACS / IHD": 5,
    "Atrial fibrillation / arrhythmia": 4,
    "Anticoagulation / VTE": 4,
    "Lipids": 4,
    "Hypertension (systemic)": 4,
    "Valvular / structural": 3,
    "Stroke (cardioembolic/cerebrovascular)": 3,
    "Pulmonary hypertension / pulmonary vascular": 3,
    "Cardiac devices / procedures": 3,
    "CV prevention / cardiorenal CV outcomes (adjacent)": 3,
    "Pericardial / myocarditis": 2,
    "Peripheral arterial": 2,
}

# Variant preference: the file that actually carries the app, not a redirect stub.
VARIANT_ORDER = ["_AUTO_FULL_REVIEW.html", "_FULL_REVIEW.html",
                 "_AUTO_REVIEW.html", "_REVIEW.html"]


def variant_rank(fn: str, stem: str) -> int:
    for i, suf in enumerate(VARIANT_ORDER):
        if fn == stem + suf:
            return i
    return len(VARIANT_ORDER)


def collapse(apps: list[dict]) -> list[dict]:
    by_stem: dict[str, list[dict]] = {}
    for a in apps:
        by_stem.setdefault(a["stem"], []).append(a)

    out = []
    for stem, group in by_stem.items():
        real = [g for g in group if not g["is_redirect_stub"]]
        pool = real or group
        # Canonical = the richest non-stub variant; ties broken by variant order.
        canon = sorted(pool, key=lambda g: (-g["realdata_trials"], -g["bytes"],
                                            variant_rank(g["file"], stem)))[0]
        rec = dict(canon)
        rec["variants"] = sorted(g["file"] for g in group)
        rec["n_variants"] = len(group)
        rec["n_redirect_stubs"] = sum(1 for g in group if g["is_redirect_stub"])
        # Do the non-stub variants of one app agree with each other?
        tr = {g["realdata_trials"] for g in real}
        vd = {g["verdict"] for g in real}
        bt = {g["badge_trials"] for g in real}
        rec["variant_trialcount_split"] = sorted(tr) if len(tr) > 1 else None
        rec["variant_verdict_split"] = sorted(str(v) for v in vd) if len(vd) > 1 else None
        rec["variant_badgecount_split"] = sorted(str(b) for b in bt) if len(bt) > 1 else None
        rec["any_false_green"] = any(g["false_green"] for g in group)
        rec["any_count_disagree"] = any(g["counts_agree"] is False for g in group)

        # "EMPTY" hides three very different states. Separate them, because the
        # remedy differs: an orphan stub needs a target, an empty ledger needs
        # extraction, and a non-realData architecture needs a different reader.
        if not real:
            rec["state"] = "ORPHAN_STUB"       # only 1.5 KB redirect stubs exist
        elif rec["realdata_bytes"] > 0 and rec["realdata_trials"] == 0:
            rec["state"] = "EMPTY_LEDGER"      # realData:{} — template, no trials
        elif rec["realdata_bytes"] == 0:
            rec["state"] = "NON_REALDATA_ARCH"  # data lives elsewhere; reader blind
        else:
            rec["state"] = "HAS_DATA"
        out.append(rec)
    return out


def score(rec: dict) -> dict:
    """Gap score, 0-10, additive with every component named."""
    gap, why = 0, []

    # Two distinct badge-dishonesty classes, scored separately.
    # (a) flat contradiction: badge says PASSED, the machine verdict says UNCERTAIN.
    # (b) false green: badge says PASSED over non-zero P1/P2 counts or reasons.
    if rec.get("badge_verdict_mismatch"):
        gap += 4
        why.append(f"badge says PASSED while __verdict says {rec['verdict']} (+4)")
    if rec["any_false_green"]:
        gap += 3
        why.append("false-green badge over non-zero P1/P2 findings (+3)")
    if rec["verdict"] == "ABSENT":
        gap += 2
        why.append("no window.__verdict at all (+2)")
    if rec["any_count_disagree"]:
        gap += 2
        why.append("trial counts disagree across surfaces (+2)")
    if rec["variant_trialcount_split"]:
        gap += 1
        why.append(f"variants disagree on k={rec['variant_trialcount_split']} (+1)")
    if rec["variant_verdict_split"]:
        gap += 1
        why.append(f"variants disagree on verdict {rec['variant_verdict_split']} (+1)")
    if rec["filename_content_mismatch"]:
        gap += 2
        why.append("filename does not describe content (+2)")
    if rec["state"] == "EMPTY_LEDGER":
        gap += 3
        why.append("realData:{} — template with NO trials (+3)")
    elif rec["state"] == "ORPHAN_STUB":
        gap += 1
        why.append("only a redirect stub exists on this branch (+1)")
    elif rec["state"] == "NON_REALDATA_ARCH":
        gap += 1
        why.append("data not in realData — needs a bespoke reader (+1)")
    # A green badge over an EMPTY ledger is the worst class in the corpus: the
    # page asserts passed checks on trials it does not contain.
    if rec["state"] == "EMPTY_LEDGER" and rec["badge_claims_pass"]:
        gap += 3
        why.append("green badge over an EMPTY ledger (+3)")

    k = rec["realdata_trials"]
    if 0 < k <= 2:
        gap += 2
        why.append(f"k={k} — too few to pool credibly (+2)")
    elif 3 <= k <= 4:
        gap += 1
        why.append(f"k={k} — thin evidence base (+1)")
    # A PMID-less ledger cannot be source-verified at all.
    if rec["has_real_data"] and not rec["realdata_pmids"]:
        gap += 2
        why.append("ledger carries no PMIDs (+2)")
    if rec["app_class"] == "DTA/prognostic":
        why.append("DTA/prognostic — recipe applies only partly")

    gap = min(gap, 10)
    imp = DOMAIN_IMPORTANCE.get(rec["domain"], 2)
    rec["importance"] = imp
    rec["gap"] = gap
    rec["gap_why"] = why
    rec["upgrade_value"] = imp * gap
    return rec


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--inv", default=os.path.join(REPO, "outputs", "cardio_inventory.json"))
    ap.add_argument("--json", default=os.path.join(REPO, "outputs", "cardio_triage.json"))
    args = ap.parse_args()

    inv = json.load(open(args.inv, encoding="utf-8"))
    rows = [score(r) for r in collapse(inv["apps"])]
    rows.sort(key=lambda r: (-r["upgrade_value"], -r["importance"], r["stem"]))

    with open(args.json, "w", encoding="utf-8") as fh:
        json.dump({"n_apps": len(rows), "apps": rows}, fh, indent=1)

    print(f"{len(rows)} unique cardio apps ({sum(r['n_variants'] for r in rows)} files)\n")
    hdr = (f"{'#':>3} {'APP':<34} {'DOMAIN':<20} {'k':>3} {'DATA':<6} "
           f"{'VERDICT':<9} {'BADGE':<26} {'AGREE':<6} {'IMP':>3} {'GAP':>3} {'UV':>3}")
    print(hdr)
    print("-" * len(hdr))
    for i, r in enumerate(rows, 1):
        badge = (r["badge_headline"] or "(none)")[:25]
        agree = {True: "yes", False: "NO", None: "n/a"}[r["counts_agree"]]
        st = {"HAS_DATA": "real", "EMPTY_LEDGER": "EMPTY!", "ORPHAN_STUB": "stub",
              "NON_REALDATA_ARCH": "other"}[r["state"]]
        print(f"{i:>3} {r['stem'][:34]:<34} {(r['domain'] or '')[:20]:<20} "
              f"{r['realdata_trials']:>3} {st:<6} "
              f"{str(r['verdict'])[:9]:<9} {badge:<26} {agree:<6} "
              f"{r['importance']:>3} {r['gap']:>3} {r['upgrade_value']:>3}")

    print(f"\nwrote {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
