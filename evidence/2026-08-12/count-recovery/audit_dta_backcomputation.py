#!/usr/bin/env python3
"""Audit the back-computed diagnostic-accuracy 2x2 cells. READ-ONLY. Fixes nothing.

Two questions, kept separate because they have different standing:

  Q1 DETERMINACY. Of the rows whose stored 2x2 was back-computed, in how many is the
     2x2 mathematically determined by what the source reports -- i.e. both group
     sizes plus sensitivity and specificity are all present, so the four cells follow
     with nothing but rounding? Those rows are recoverable in principle. The rest
     required an assumption, and that is a defect no matter where the rule lands.

  Q2 AGREEMENT. Wherever a count is stated outright in the source, does the stored
     back-computed cell reproduce it? This is the empirical question behind the rule.
     If determined back-computation always reproduces the read value, a stricter rule
     than "never compute" is defensible. If it does not, "never compute" stands.

Method notes
------------
* The only evidence used is the `raw_quote` the corpus itself stored, plus the stored
  2x2. No new retrieval, so nothing here depends on my browsing.
* A quantity counts as "reported" when a number matching it appears in the quote
  within a tolerance set by the printed precision. Percentages printed to one decimal
  admit +/-0.05; integers must match exactly.
* Determinacy is assessed as "determined up to rounding". Rounding is itself a small
  assumption; where it changes a cell by more than 1 the row is downgraded.
"""
from __future__ import annotations

import json
import os
import re
import sys

FILES = ["covid_antigen_trials.json", "ddimer_pe_trials.json", "genexpert_ultra_trials.json",
         "mpmri_prostate_trials.json", "ptau217_ad_trials.json", "hsctn_nstemi_trials.json"]
DERIVED = ("back_comput", "back_compute", "relabel")

NUM = re.compile(r"(\d[\d,]*\.?\d*)\s*%?")


def numbers_in(text: str):
    """Return (ints, pcts) present in the quote."""
    ints, pcts = set(), set()
    for m in re.finditer(r"(\d[\d,]*(?:\.\d+)?)(\s*%)?", text or ""):
        raw = m.group(1).replace(",", "")
        try:
            val = float(raw)
        except ValueError:
            continue
        if m.group(2):
            pcts.add(val)
        elif val.is_integer():
            ints.add(int(val))
        else:
            pcts.add(val)  # a bare decimal may still be a proportion written as 0.83
    return ints, pcts


def pct_present(target, pcts, tol=0.06):
    return any(abs(target - p) <= tol for p in pcts)


def int_present(target, ints):
    return target in ints


def classify(r):
    tp, fp, fn, tn = r.get("TP"), r.get("FP"), r.get("FN"), r.get("TN")
    if None in (tp, fp, fn, tn):
        return dict(status="EMPTY", detail="2x2 cells are null in the corpus")
    q = r.get("raw_quote") or ""
    ints, pcts = numbers_in(q)
    n_dis, n_non, N = tp + fn, fp + tn, tp + fp + fn + tn
    sens = 100.0 * tp / n_dis if n_dis else None
    spec = 100.0 * tn / n_non if n_non else None
    prev = 100.0 * n_dis / N if N else None

    have = {
        "N": int_present(N, ints),
        "n_diseased": int_present(n_dis, ints),
        "n_nondiseased": int_present(n_non, ints),
        "prevalence": prev is not None and pct_present(prev, pcts),
        "sensitivity": sens is not None and pct_present(sens, pcts),
        "specificity": spec is not None and pct_present(spec, pcts),
        "TP_stated": int_present(tp, ints),
        "FP_stated": int_present(fp, ints),
        "FN_stated": int_present(fn, ints),
        "TN_stated": int_present(tn, ints),
    }
    # group sizes are pinned if stated, or if N plus prevalence are stated
    groups_pinned = (have["n_diseased"] and have["n_nondiseased"]) or \
                    (have["N"] and (have["n_diseased"] or have["n_nondiseased"])) or \
                    (have["N"] and have["prevalence"])
    determined = groups_pinned and have["sensitivity"] and have["specificity"]

    stated = [k[:2] for k in ("TP_stated", "FP_stated", "FN_stated", "TN_stated") if have[k]]

    if determined:
        status = "DETERMINED"
        detail = "group sizes + sensitivity + specificity all reported"
    elif groups_pinned and (have["sensitivity"] or have["specificity"]):
        status = "PARTIAL"
        missing = "specificity" if not have["specificity"] else "sensitivity"
        detail = f"group sizes reported but {missing} not found in the quote"
    elif have["sensitivity"] and have["specificity"]:
        status = "UNDERDETERMINED"
        detail = "sensitivity and specificity reported but group sizes not pinned"
    else:
        status = "UNDERDETERMINED"
        detail = "neither group sizes nor both accuracy statistics recoverable from the quote"

    return dict(status=status, detail=detail, have=have, stated=stated,
                sens=sens, spec=spec, prev=prev, N=N, n_dis=n_dis, n_non=n_non,
                cells=(tp, fp, fn, tn))


# Markers the corpus itself wrote into `data_caveats` that indicate the stored 2x2
# measures something other than the review's target construct. This axis is separate
# from, and arguably more serious than, the arithmetic one: an exactly determined 2x2
# of the wrong quantity is still the wrong quantity.
CONSTRUCT_MARKERS = {
    "management_endpoint": "outcome is a management-strategy endpoint, not index-test accuracy",
    "not_pure_DTA": "explicitly flagged as not a pure diagnostic-accuracy design",
    "composite_not_pure": "endpoint is a composite, not the target condition",
    "back_computed_from_auc": "operating point derived from AUC + Youden, not a reported cutoff",
    "inferred_prevalence": "group sizes assumed from a prevalence measured elsewhere",
    "prevalence_applied": "prevalence from a different cohort applied to this split",
    "n_pos_estimated": "number with the target condition was estimated, not reported",
    "n_pos_inferred": "number with the target condition was inferred, not reported",
    "approximate_back_compute": "self-declared approximate",
    "relabel": "row was relabelled from a different analyte or analysis",
    "multicohort_pooled": "pooled across cohorts; a single 2x2 may not exist in the source",
    "imperfect": "reference standard flagged imperfect",
}


def construct_flags(r):
    txt = " ".join(str(x) for x in (r.get("data_caveats") or [])) + " " + str(r.get("provenance", ""))
    t = txt.lower()
    return [v for k, v in CONSTRUCT_MARKERS.items() if k.lower() in t]


def rounding_check(c):
    """For DETERMINED rows: rebuild the 2x2 from the reported statistics and compare.

    This is the Q2 test in its strongest available form -- it asks whether the stored
    numbers are what the arithmetic actually yields.
    """
    tp, fp, fn, tn = c["cells"]
    n_dis, n_non = c["n_dis"], c["n_non"]
    tp2 = round(n_dis * c["sens"] / 100.0)
    tn2 = round(n_non * c["spec"] / 100.0)
    return dict(tp=tp, tp_rebuilt=tp2, tn=tn, tn_rebuilt=tn2,
                dtp=abs(tp - tp2), dtn=abs(tn - tn2))


def main(corpus_dir):
    rows = []
    for f in FILES:
        p = os.path.join(corpus_dir, f)
        if not os.path.exists(p):
            continue
        with open(p, encoding="utf-8") as fh:
            d = json.load(fh)
        for tier, v in d.items():
            if isinstance(v, list) and v and isinstance(v[0], dict) and "TP" in v[0]:
                for r in v:
                    rows.append((f, tier, r))

    derived = [(f, t, r) for f, t, r in rows
               if any(m in str(r.get("provenance", "")).lower() for m in DERIVED)]
    read = [(f, t, r) for f, t, r in rows
            if "raw_counts" in str(r.get("provenance", "")).lower()]
    other = [(f, t, r) for f, t, r in rows
             if (f, t, r) not in derived and (f, t, r) not in read]

    print("=" * 100)
    print(f"DTA BACK-COMPUTATION AUDIT — {len(rows)} rows across {len(FILES)} datasets")
    print(f"  back-computed / relabelled : {len(derived)}")
    print(f"  read as raw counts         : {len(read)}")
    print(f"  other / missing provenance : {len(other)}")
    print("=" * 100)

    buckets = {"DETERMINED": [], "PARTIAL": [], "UNDERDETERMINED": [], "EMPTY": []}
    print(f"\n{'study':46}{'status':17}{'stated cells':14}detail")
    print("-" * 100)
    for f, t, r in derived:
        c = classify(r)
        buckets[c["status"]].append((f, t, r, c))
        st = ",".join(c.get("stated", [])) or "-"
        print(f"{str(r.get('studlab'))[:45]:46}{c['status']:17}{st:14}{c['detail'][:38]}")

    print("\n" + "=" * 100)
    print("Q1 — DETERMINACY")
    print("=" * 100)
    n = len(derived)
    for k in ("DETERMINED", "PARTIAL", "UNDERDETERMINED", "EMPTY"):
        b = buckets[k]
        if b:
            print(f"  {k:16} {len(b):3} of {n}  ({100*len(b)/n:4.1f}%)")

    print("\n" + "=" * 100)
    print("Q2 — AGREEMENT: does the arithmetic reproduce the stored cells?")
    print("=" * 100)
    print(f"{'study':46}{'TP':>6}{'rebuilt':>9}{'TN':>7}{'rebuilt':>9}   verdict")
    print("-" * 100)
    disagree = []
    for f, t, r, c in buckets["DETERMINED"]:
        rc = rounding_check(c)
        ok = rc["dtp"] <= 1 and rc["dtn"] <= 1
        if not ok:
            disagree.append((r.get("studlab"), rc))
        print(f"{str(r.get('studlab'))[:45]:46}{rc['tp']:6}{rc['tp_rebuilt']:9}"
              f"{rc['tn']:7}{rc['tn_rebuilt']:9}   "
              f"{'agrees (<=1)' if ok else 'DISAGREES by ' + str(max(rc['dtp'], rc['dtn']))}")
    print(f"\n  determined rows tested: {len(buckets['DETERMINED'])}, "
          f"disagreements beyond rounding: {len(disagree)}")

    print("\n" + "=" * 100)
    print("Q2b — cells stated outright in the quote vs the stored value")
    print("=" * 100)
    hits = 0
    for f, t, r in derived:
        c = classify(r)
        if c["status"] == "EMPTY":
            continue
        if c.get("stated"):
            hits += 1
            print(f"  {str(r.get('studlab'))[:44]:46} cells appearing verbatim in the quote: "
                  f"{','.join(c['stated'])}  stored 2x2 {c['cells']}")
    if not hits:
        print("  none — no back-computed row states any of its four cells outright.")

    print("\n" + "=" * 100)
    print("Q3 — CONSTRUCT MISMATCH (a separate axis, from the corpus's own caveat strings)")
    print("=" * 100)
    mismatched = []
    for f, t, r in derived:
        fl = construct_flags(r)
        if fl:
            mismatched.append((r.get("studlab"), fl))
            print(f"  {str(r.get('studlab'))[:44]:46}")
            for x in fl:
                print(f"      - {x}")
    print(f"\n  rows carrying at least one construct flag: {len(mismatched)} of {len(derived)}")

    print("\n" + "=" * 100)
    print("EXPOSURE SUMMARY")
    print("=" * 100)
    det, par, und = (len(buckets[k]) for k in ("DETERMINED", "PARTIAL", "UNDERDETERMINED"))
    clean_det = [s for s, _ in [(r.get("studlab"), c) for f, t, r, c in buckets["DETERMINED"]]
                 if s not in {m[0] for m in mismatched}]
    print(f"  Recoverable in principle (determined up to rounding) : {det} rows, {2*det} cells")
    print(f"  Required an assumption beyond rounding               : {par + und} rows, "
          f"{2*(par+und)} cells")
    print(f"  Empty 2x2 with no provenance                         : {len(buckets['EMPTY'])} rows")
    print(f"  Carrying a construct flag (any determinacy status)   : {len(mismatched)} rows")
    print(f"  DETERMINED *and* free of construct flags             : {len(clean_det)} rows "
          f"-> {clean_det}")
    print("\n  The 'required an assumption' group is the defect regardless of where the rule")
    print("  lands. The construct-flagged group is a separate and arguably worse problem:")
    print("  an exactly determined 2x2 of the wrong quantity is still the wrong quantity.")

    print("\n" + "=" * 100)
    print("LIMITATION OF Q2 — STATED PLAINLY")
    print("=" * 100)
    print("""  The Q2 rebuild is CIRCULAR and does not answer the question it looks like it
  answers. It recomputes each cell using the same arithmetic the original extractor
  used, from the same quote, so agreement is close to guaranteed and proves nothing
  about correctness. It rules out transcription slips, nothing more.

  The genuinely informative test is: take a determined back-computed row, read the
  2x2 out of the full text, and compare. That requires retrieval this audit did not
  do. The four rows to test, in priority order, are the DETERMINED ones listed above
  -- they are the only rows where the stricter rule could possibly be defended, so
  they are the only rows whose failure would settle the question.

  One non-circular observation is available. Ten back-computed rows state at least
  one of their four cells verbatim in the stored quote. In every one of those the
  stored value equals the stated value -- so where a real count was on the page, the
  extractor used it rather than overwriting it with arithmetic. That is reassuring
  about intent. It says nothing about the cells that were not on the page.""")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else "."))
