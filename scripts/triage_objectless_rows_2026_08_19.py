#!/usr/bin/env python3
"""TRIAGE THE OBJECTLESS VALUE-SERVING ROWS -- cheap checks that need no SSOT object.

THE SITUATION. 600 dashboard rows serve a pooled value with no SSOT object to support or
contradict them, because for 539 of them NO OBJECT EXISTS. Building those objects is a large
project and Mahmood's decision. This turns "600 unchecked" into a triaged list he can decide
against, using only what the row itself carries.

THE CHECKS, and every one is INTERNAL to the row -- none needs an object, a registry or a
publication:

    INTERVAL EXCLUDES THE POINT      ci_low > point, or ci_high < point. Arithmetically
                                     impossible for any interval estimator.
    K IS 1 WITH A POOLED ESTIMATE    a pool of one study is not a pool.
    K IS 0 OR ABSENT                 a pooled value with no stated number of studies.
    RATIO OUT OF PLAUSIBLE RANGE     an odds ratio below 0.01 or above 100 is not a clinical
                                     effect; it is a unit or transform error.
    INTERVAL SPANS FOUR ORDERS       ci_high/ci_low > 10,000 -- an interval that wide is not an
                                     estimate.
    NEGATIVE OR ZERO ON A RATIO      an odds ratio cannot be <= 0.
    I2 OUT OF RANGE                  outside 0-100.

WHAT A FLAG IS AND IS NOT. A flagged row is ARITHMETICALLY OR STRUCTURALLY IMPOSSIBLE on its own
terms. AN UNFLAGGED ROW IS NOT VERIFIED -- it means these seven checks found nothing, and the
TAF-versus-TAF row would have passed every one of them: 0.913 with an interval spanning 1 and
k=2 is unremarkable in every respect except that the comparator arm was absent, which no
row-internal check can see.

    THESE CHECKS FIND THE IMPOSSIBLE, NOT THE WRONG. The wrong looks exactly like the right.

USAGE
    python scripts/triage_objectless_rows_2026_08_19.py [--apply]
"""
import io
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SNAP = os.path.join(REPO, "outputs", "portfolio_index.json")
OUT = os.path.join(REPO, "evidence", "2026-08-19-batch1", "objectless_row_triage.json")

CARDIO = ("statin", "pcsk9", "sglt2", "arni", "sacubitril", "apixaban", "rivaroxaban",
          "edoxaban", "dabigatran", "warfarin", "clopidogrel", "ticagrelor", "prasugrel",
          "aspirin", "heart", "cardi", "coronar", "atrial", "af_", "_af", "stroke", "hf_",
          "_hf", "hypertens", "lipid", "cholester", "angina", "infarct", "ablation",
          "anticoag", "antiplatelet", "amiodarone", "digoxin", "beta_block", "valve",
          "aortic", "mitral", "pah", "pulmonary_hyper", "colchicine", "finerenone",
          "empagliflozin", "dapagliflozin", "evolocumab", "alirocumab", "inclisiran",
          "bempedoic", "icosapent", "omecamtiv", "mavacamten", "vericiguat", "tafamidis")
ID = ("covid", "hiv", "tubercul", "_tb", "tb_", "malaria", "cdiff", "cdi_", "hepatit",
      "influenza", "vaccin", "sepsis", "pneumo", "infect", "antibiot", "cmv", "mpox",
      "ebola", "cholera", "dengue", "crypto", "candid", "aspergill", "bacter", "viral",
      "antimicrob", "meningit", "antiviral", "remdesivir", "molnupiravir", "nirmatrelvir",
      "bamlanivimab", "casirivimab", "sotrovimab", "tecovirimat", "maribavir", "delamanid",
      "bedaquiline", "fidaxo", "eravacycline", "lefamulin", "ceftolozane", "ertapenem",
      "moxifloxacin", "raltegravir", "dolutegravir", "bezlotoxumab", "rotavirus", "prep_",
      "_prep", "zoster", "rsv", "pertussis", "typhoid", "polio", "measles")


def area(row):
    s = ((row.get("file") or "") + " " + (row.get("display_name") or "")).lower()
    c = any(k in s for k in CARDIO)
    i = any(k in s for k in ID)
    if c and not i:
        return "cardiology"
    if i and not c:
        return "infectious disease"
    if c and i:
        return "both terms present"
    return "other or unclassified"


def checks(r):
    out = []
    p, lo, hi, k = (r.get("pooled_OR"), r.get("ci_low"), r.get("ci_high"), r.get("k"))
    num = lambda v: isinstance(v, (int, float))
    if num(p) and num(lo) and num(hi):
        if lo > p or hi < p:
            out.append("INTERVAL_EXCLUDES_THE_POINT")
        if lo > 0 and hi / lo > 10000:
            out.append("INTERVAL_SPANS_FOUR_ORDERS")
    if num(p):
        if p <= 0:
            out.append("RATIO_ZERO_OR_NEGATIVE")
        elif p < 0.01 or p > 100:
            out.append("RATIO_OUT_OF_PLAUSIBLE_RANGE")
    if k == 1:
        out.append("K_IS_1_WITH_A_POOLED_ESTIMATE")
    if k in (0, None):
        out.append("K_IS_ZERO_OR_ABSENT")
    i2 = r.get("I2")
    if num(i2) and (i2 < 0 or i2 > 100):
        out.append("I2_OUT_OF_RANGE")
    return out


def run(apply_it):
    snap = json.load(io.open(SNAP, encoding="utf-8"))
    rows = [r for r in snap["rows"]
            if r.get("ssot_state") == "UNMAPPED"
            and isinstance(r.get("pooled_OR"), (int, float))]
    print("objectless rows serving a pooled value: %d\n" % len(rows))

    by_area, by_flag, flagged = {}, {}, []
    for r in rows:
        a = area(r)
        by_area[a] = by_area.get(a, 0) + 1
        f = checks(r)
        if f:
            flagged.append({"file": r.get("file"), "display_name": r.get("display_name"),
                            "area": a, "flags": f, "k": r.get("k"),
                            "pooled_OR": r.get("pooled_OR"), "ci_low": r.get("ci_low"),
                            "ci_high": r.get("ci_high"), "I2": r.get("I2")})
            for x in f:
                by_flag[x] = by_flag.get(x, 0) + 1

    print("BY AREA")
    for a, n in sorted(by_area.items(), key=lambda kv: -kv[1]):
        print("   %-26s %4d" % (a, n))
    print("\nROWS FAILING AT LEAST ONE ROW-INTERNAL CHECK: %d of %d (%.1f%%)"
          % (len(flagged), len(rows), 100.0 * len(flagged) / max(1, len(rows))))
    for f, n in sorted(by_flag.items(), key=lambda kv: -kv[1]):
        print("   %-34s %4d" % (f, n))

    fa = {}
    for x in flagged:
        fa[x["area"]] = fa.get(x["area"], 0) + 1
    print("\nFLAGGED BY AREA")
    for a, n in sorted(fa.items(), key=lambda kv: -kv[1]):
        print("   %-26s %4d of %d" % (a, n, by_area.get(a, 0)))

    print("\nworst 12 by flag count:")
    for x in sorted(flagged, key=lambda y: -len(y["flags"]))[:12]:
        print("   %-50s k=%-4s OR=%-10s [%s, %s]  %s"
              % (x["file"][:50], x["k"], x["pooled_OR"], x["ci_low"], x["ci_high"],
                 ",".join(x["flags"])))

    doc = {
        "triaged_utc": "2026-08-19",
        "scope": ("dashboard rows serving a pooled value with ssot_state UNMAPPED -- no object "
                  "exists to support or contradict them"),
        "n_rows": len(rows),
        "by_area": by_area,
        "n_flagged": len(flagged),
        "flags_counted": by_flag,
        "flagged_by_area": fa,
        "what_a_flag_means": (
            "The row is ARITHMETICALLY OR STRUCTURALLY IMPOSSIBLE on its own terms -- an "
            "interval excluding its point, a pool of one study, a ratio outside any clinical "
            "range. No object, registry or publication is needed to see it."),
        "what_an_UNFLAGGED_row_means": (
            "NOT verified. It means these seven checks found nothing. The TAF-versus-TAF row "
            "would have passed EVERY ONE: 0.913, interval spanning 1, k=2 -- unremarkable in "
            "every respect except that the comparator arm was absent, which no row-internal "
            "check can see. THESE CHECKS FIND THE IMPOSSIBLE, NOT THE WRONG."),
        "area_classification_is_by_keyword": (
            "on the page filename and display name; 'both terms present' and 'other or "
            "unclassified' are reported rather than forced into a bucket"),
        "flagged": sorted(flagged, key=lambda y: -len(y["flags"])),
    }
    if apply_it:
        with io.open(OUT, "w", encoding="utf-8", newline="") as fh:
            fh.write(json.dumps(doc, indent=1, ensure_ascii=False))
        print("\nwrote %s" % os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.exit(run("--apply" in sys.argv))
