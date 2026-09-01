# -*- coding: utf-8 -*-
"""TURN "no notion of term specificity" FROM A DIAGNOSIS INTO A NUMBER.

Three condition axes have been measured and none adopted -- literal title words, MeSH-
expanded, AACT registry-sourced. All three fail the same way, and the evidence for that was
a single anecdote: `disease` matched 207 of 1,186 reviews and was a term for EVERY one of the
twenty topics. ⇒ This measures the property that anecdote points at, for every candidate term
of all three axes.

WHAT IS MEASURED, per term:
    df          documents in the frame containing it (of 1,186 reviews)
    df_frac     df / 1,186
    topics      how many of the twenty use it -- a term every topic uses distinguishes
                nothing, whatever its df
    idf         ln(N / df), the standard weight, reported so a PROPOSAL can be scored

⛔ NOTHING IS ADOPTED. A weighting scheme is a novel method and goes in ALONGSIDE the
incumbent with its regression defined first. This file measures the property and states what
a proposal WOULD do; it changes no axis and no published count.

⚠️ THE TWO FAILURE DIRECTIONS ARE THE SAME DEFECT. A term with df=0 (`hypercholesterolemia`)
and a term with df=207 (`disease`) are both non-discriminating, and a matcher that counts
terms equally cannot tell either from a term with df=4. Reporting only the dead ones -- which
is what a zero-count naturally surfaces -- hides half of it.
"""
import io
import json
import math
import os
import sys
from collections import Counter, OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.chdir(HERE)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                              line_buffering=True)
from rekey_rule import contains                                          # noqa: E402
from axis_match import prepare, sha_set                                  # noqa: E402

FRAME = "F:/claude-temp/pend/cdsr_frame_cardiology.jsonl"
AX = "../../evidence/2026-08-31-axis/axis_states_twenty.json"
MESH = "../../evidence/2026-08-31-axis/condition_mesh_v2_twenty.json"
AACT = "../../evidence/2026-08-31-axis/aact_condition_axis_twenty.json"
OUT = "../../evidence/2026-08-31-axis/term_specificity.json"

# Declared BEFORE the numbers are read: a term above this share of the frame is treated as
# NON-DISCRIMINATING by the proposal in section 4. 10% of 1,186 is 119 documents.
PROPOSED_CUTOFF = 0.10


def axis_terms():
    """-> {axis_name: {app_id: [terms]}} for all three condition axes."""
    out = OrderedDict()
    ax = json.load(io.open(AX, encoding="utf-8"))["topics"]
    out["literal"] = {t["app_id"]: list(t.get("condition_terms") or []) for t in ax}
    m = json.load(io.open(MESH, encoding="utf-8"))["topics"]
    out["mesh_v2"] = {t["app_id"]: list(t.get("terms_v2") or []) for t in m}
    a = json.load(io.open(AACT, encoding="utf-8"))["topics"]
    out["aact"] = {t["app_id"]: list(t.get("aact_terms") or []) for t in a}
    return out


def main():
    rows, reviews = prepare(FRAME)
    N = float(len(reviews))
    axes = axis_terms()

    print("=== REF ===")
    print("   frame %s   N = %d reviews" % (sha_set(r["cd_base"] for r in rows)[:16], int(N)))
    print("   axes  literal (title words) · mesh_v2 (verified records) · aact (registry)")
    print("   ⛔ NOTHING ADOPTED. This measures a property and prices a proposal.")
    print("")

    # df is a property of the TERM and the FRAME, not of the axis -- computed once.
    all_terms = set()
    for a in axes.values():
        for ts in a.values():
            all_terms.update(ts)
    df = {}
    for t in sorted(all_terms):
        df[t] = sum(1 for r in reviews if contains(r["_all"], t))
    print("=== DOCUMENT FREQUENCY, computed once over %d distinct candidate terms ===" % len(df))

    detail = {}
    for axis, per_topic in axes.items():
        used = Counter()
        for app, ts in per_topic.items():
            for t in set(ts):
                used[t] += 1
        vals = [df[t] for ts in per_topic.values() for t in ts]
        if not vals:
            continue
        dead = sum(1 for v in vals if v == 0)
        promisc = sum(1 for v in vals if v / N > PROPOSED_CUTOFF)
        detail[axis] = {
            "terms": len(vals), "distinct": len(set(t for ts in per_topic.values() for t in ts)),
            "df_zero": dead, "df_over_cutoff": promisc,
            "median_df": sorted(vals)[len(vals) // 2],
            "max_df": max(vals),
        }
        print("")
        print("   --- %s ---" % axis)
        print("      terms used (with repeats across topics) : %d" % len(vals))
        print("      DEAD, df = 0                            : %d  (%.0f%%)"
              % (dead, 100.0 * dead / len(vals)))
        print("      PROMISCUOUS, df > %.0f%% of the frame     : %d  (%.0f%%)"
              % (100 * PROPOSED_CUTOFF, promisc, 100.0 * promisc / len(vals)))
        print("      median df %d   max df %d" % (sorted(vals)[len(vals) // 2], max(vals)))
        top = sorted(set(t for ts in per_topic.values() for t in ts),
                     key=lambda t: (-df[t], t))[:6]
        for t in top:
            print("         %-38s df %4d  (%4.1f%%)  used by %2d topics  idf %.2f"
                  % (t[:38], df[t], 100.0 * df[t] / N, used[t],
                     math.log(N / df[t]) if df[t] else float("inf")))

    print("")
    print("=== ⭐ THE TERMS THAT DISTINGUISH NOTHING -- used by MANY topics ===")
    shared = Counter()
    for axis, per_topic in axes.items():
        for app, ts in per_topic.items():
            for t in set(ts):
                shared[(axis, t)] += 1
    worst = sorted((c, a, t) for (a, t), c in shared.items() if c >= 5)
    worst.sort(reverse=True)
    print("   %-10s %-34s %7s %7s %8s" % ("axis", "term", "topics", "df", "df_frac"))
    for c, a, t in worst[:12]:
        print("   %-10s %-34s %7d %7d %7.1f%%" % (a, t[:34], c, df[t], 100.0 * df[t] / N))
    print("   ⇒ a term used by many topics AND matching a large share of the frame is")
    print("     carrying no information in either direction.")

    # ---------------------------------------------------------------- THE PROPOSAL
    print("")
    print("=== 4. THE PROPOSAL, PRICED -- NOT ADOPTED ===")
    print("   Rule: a term with df > %.0f%% of the frame CONTRIBUTES a match but does NOT"
          % (100 * PROPOSED_CUTOFF))
    print("   COUNT toward the `need` threshold. Only specific terms can satisfy a topic.")
    print("")
    print("   %-46s %8s %8s %s" % ("app_id", "terms", "specific", "would the axis still fire?"))
    priced = []
    lit = axes["literal"]
    ax = {t["app_id"]: t for t in json.load(io.open(AX, encoding="utf-8"))["topics"]}
    for app in sorted(lit):
        ts = lit[app]
        spec = [t for t in ts if df[t] and df[t] / N <= PROPOSED_CUTOFF]
        need_now = min(2, len(ts)) if ts else 0
        need_new = min(2, len(spec)) if spec else 0
        verdict = ("REFUSED -- no specific term" if not spec else
                   "unchanged" if len(spec) == len(ts) else
                   "narrower (need %d of %d specific)" % (need_new, len(spec)))
        priced.append({"app_id": app, "terms": len(ts), "specific": len(spec),
                       "verdict": verdict,
                       "incumbent_state": ax[app]["state"]})
        print("   %-46s %8d %8d %s" % (app, len(ts), len(spec), verdict))

    lost = [p for p in priced if p["specific"] == 0 and p["terms"] > 0]
    print("")
    print("   topics that would LOSE their condition axis entirely: %d   %s"
          % (len(lost), ", ".join(p["app_id"] for p in lost)))
    print("   ⛔ THAT is the price, and it is why this is a proposal and not a change.")
    print("")
    print("   ⭐ REGRESSION THAT WOULD HAVE TO BE DEFINED FIRST, if it were ever adopted:")
    print("      S1  no topic currently MATCHED may lose its verified set")
    print("      S2  the 4 judged CDSR counterparts survive, hashed as a SET")
    print("      S3  precision at the verified stage must not fall")
    print("      S4  the cutoff is declared BEFORE the run and never tuned to the result")
    print("      S5  ALONGSIDE -- both weighted and unweighted columns published")

    json.dump({"N": int(N), "cutoff": PROPOSED_CUTOFF, "df": df,
               "per_axis": detail, "priced": priced},
              io.open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("")
    print("   written: %s" % OUT)


if __name__ == "__main__":
    main()
