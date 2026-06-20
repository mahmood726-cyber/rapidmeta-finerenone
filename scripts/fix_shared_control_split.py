#!/usr/bin/env python
"""Codemod: split shared control arms in RapidMeta pairwise dashboards (Class-1 fix).

A multi-arm parent trial (or a trial that borrowed another's placebo as an external
control) was extracted as >=2 rows that each REPEAT the same control (cE,cN). Naive
pairwise pooling then double-counts those control patients/events, under-states the
variance, and double-counts N/events in the ARD/NNT aggregates.

Cochrane Handbook v6.5 sec.23.3.4 remedy for a shared control across m comparisons:
divide the control group size (and events) by m so it is counted once in total. The
control EVENT RATE is preserved (so each contrast's point estimate is unchanged) while
the smaller control n inflates each contrast's variance to reflect the shared evidence.

Each arm carries the control in TWO inline spots: the trial-level `cE:..,cN:..` and the
`allOutcomes` PRIMARY `cE:..` (the engine overwrites t.data.cE from the selected
outcome). Both are split here. Idempotent: a replacement whose old string is absent is
reported `already/na` and skipped.

Usage:
  python fix_shared_control_split.py --dry-run
  python fix_shared_control_split.py --apply
"""
import argparse, io, os, sys

# file -> list of (old, new). Splits chosen so events/N halve with remainder to arm 1,
# preserving the control event RATE in each contrast.
FIXES = {
    # ADVANCE 3-arm RCT (Venter NEJM 2019, PMID 31339677): one EFV control 282/351
    # shared by DTG/TAF and DTG/TDF. Different NRTI backbones => split (not combine).
    "HIV_ART_FIRSTLINE_REVIEW.html": [
        ("tE:310,tN:351,cE:282,cN:351", "tE:310,tN:351,cE:141,cN:176"),  # DTG/TAF trial-level
        ('tE:310,cE:282,type:"PRIMARY', 'tE:310,cE:141,type:"PRIMARY'),   # DTG/TAF outcome-level
        ("tE:315,tN:351,cE:282,cN:351", "tE:315,tN:351,cE:141,cN:175"),  # DTG/TDF trial-level
        ('tE:315,cE:282,type:"PRIMARY', 'tE:315,cE:141,type:"PRIMARY'),   # DTG/TDF outcome-level
    ],
    # NMOSD: CHAMPION-NMOSD (ravulizumab, PMID 38356884) reused PREVENT's placebo
    # (eculizumab, PMID 31050279) as an external control 20/47. Different drugs => split.
    "NMOSD_BIOLOGICS_REVIEW.html": [
        ("tE:3,tN:96,cE:20,cN:47", "tE:3,tN:96,cE:10,cN:24"),    # PREVENT trial-level
        ('tE:3,cE:20,type:"PRIMARY', 'tE:3,cE:10,type:"PRIMARY'),  # PREVENT outcome-level
        ("tE:0,tN:58,cE:20,cN:47", "tE:0,tN:58,cE:10,cN:23"),    # CHAMPION trial-level
        ('tE:0,cE:20,type:"PRIMARY', 'tE:0,cE:10,type:"PRIMARY'),  # CHAMPION outcome-level
    ],
    # KEN-SHE single-dose HPV 3-arm trial: bivalent + nonavalent share control 38/758.
    # Different vaccines => split. NOTE: the nonavalent row PMID 35693867 is misattributed
    # (resolves to an unrelated phototherapy paper) -- flagged for a Class-2 pass, not fixed here.
    "HPV_DOSE_REDUCTION_REVIEW.html": [
        ("tE:0,tN:758,cE:38,cN:758", "tE:0,tN:758,cE:19,cN:379"),  # bivalent trial-level
        ('tE:0,cE:38,type:"PRIMARY', 'tE:0,cE:19,type:"PRIMARY'),   # bivalent outcome-level
        ("tE:4,tN:760,cE:38,cN:758", "tE:4,tN:760,cE:19,cN:379"),  # nonavalent trial-level
        ('tE:4,cE:38,type:"PRIMARY', 'tE:4,cE:19,type:"PRIMARY'),   # nonavalent outcome-level
    ],
    # Same PREVENT/CHAMPION borrowed-placebo 20/47 as NMOSD_BIOLOGICS, here inside the
    # C5-inhibitor NMA. Splitting de-double-counts the placebo node; both arms still
    # connect to placebo so network connectivity is preserved.
    "COMPLEMENT_C5_BROAD_NMA_REVIEW.html": [
        ("tE:3,tN:96,cE:20,cN:47", "tE:3,tN:96,cE:10,cN:24"),    # PREVENT-NMOSD trial-level
        ('tE:3,cE:20,type:"PRIMARY', 'tE:3,cE:10,type:"PRIMARY'),  # PREVENT-NMOSD outcome-level
        ("tE:0,tN:58,cE:20,cN:47", "tE:0,tN:58,cE:10,cN:23"),    # CHAMPION-NMOSD trial-level
        ('tE:0,cE:20,type:"PRIMARY', 'tE:0,cE:10,type:"PRIMARY'),  # CHAMPION-NMOSD outcome-level
    ],
}


def apply_file(path, repls, apply):
    with io.open(path, encoding="utf-8") as f:
        src = f.read()
    out = src
    log = []
    for old, new in repls:
        n = out.count(old)
        if n == 1:
            out = out.replace(old, new)
            log.append("OK:%s->%s" % (old, new))
        elif n == 0:
            tag = "already" if new in out else "NOT-FOUND"
            log.append("%s:%s" % (tag, old))
        else:
            log.append("AMBIGUOUS(%d):%s" % (n, old))
    changed = out != src
    if apply and changed:
        with io.open(path, "w", encoding="utf-8", newline="") as f:
            f.write(out)
    return changed, log


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--dir", default=".")
    a = ap.parse_args()
    apply = a.apply and not a.dry_run
    bad = 0
    for fn, repls in FIXES.items():
        p = os.path.join(a.dir, fn)
        if not os.path.exists(p):
            print("MISSING:", p); bad += 1; continue
        changed, log = apply_file(p, repls, apply)
        tag = "APPLIED" if (apply and changed) else ("WOULD-CHANGE" if changed else "no-change")
        print("[%s] %s" % (tag, fn))
        for l in log:
            print("    ", l)
            if "NOT-FOUND" in l or "AMBIGUOUS" in l:
                bad += 1
    print("\n%s" % ("DRY-RUN (no writes)" if not apply else "APPLIED"))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
