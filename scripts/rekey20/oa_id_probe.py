# -*- coding: utf-8 -*-
"""Does the OPEN-ACCESS lane reach the infectious-disease topics? Retrieval only.

⭐ WHY THIS EXISTS. The ID characterisation ended on a CLAIM: *"the route for ID is the
open-access lane, which is frame-free by construction"*. A claim until run. This runs the
retrieval half and turns it into a number.

⛔ RETRIEVAL AND SCORING ONLY -- NO JUDGING. Judging is the stage measured as unstable
(27% of labels change under a refuse-only rubric tightening; ~6.5% on a straight repeat), and
adjudicating a new specialty would need its own pre-registration and its own controls. So
this reports `retrieved -> condition axis -> verified` and stops. ⚠️ `MATCHED` here is NOT a
counterpart and no counterpart is claimed.

⛔ THE RULE IS FROZEN. Terms come from `id_pool.json`, built by the same
`rekey_rule.class_terms_for_drug` the cardiology twenty used. Nothing is retuned for this
specialty.

⚠️ Verification is against an ABSTRACT, as in the cardiology OA lane, so these numbers may
not be compared with any CDSR number.

PREDICTION, recorded here before the run and scored in the report:
    topics with a live retrieval (hitCount > 0)   : predicted >= 20 of 24
    topics reaching MATCHED                       : predicted 14 to 20
    verified pairs in total                       : predicted 200 to 900
  The mechanism: ID drugs are distinctive single tokens and the antimicrobial/antiviral
  systematic-review literature is large, so I expect retrieval to be EASIER than cardiology's
  and the condition axis to be the binding constraint again -- ID conditions are short
  ("HIV", "tuberculosis", "COVID-19") and short conditions were the promiscuous end.
"""
import io
import json
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.chdir(HERE)
# ⛔ NO sys.stdout REASSIGNMENT HERE, AND THAT IS DELIBERATE. `oa_page_all` reassigns
# sys.stdout at MODULE level. Installing a wrapper here and then importing it re-wraps the
# SAME underlying buffer; when the first wrapper is dropped from sys.stdout and garbage
# collected it CLOSES that buffer, and the next print dies with
# "ValueError: I/O operation on closed file". This file hit exactly that, and the remedy is
# the documented one: when importing a module that already installed a UTF-8 wrapper, USE
# ITS WRAPPER -- do not install a second one.
from rekey_rule import norm, rule_fingerprint                            # noqa: E402
from axis_states import ALL_STATES, MATCHED                              # noqa: E402
from axis_match import sha_set                                           # noqa: E402
from oa_page_all import retrieve_all, score                              # noqa: E402
from oa_frame_contract import comparators                                # noqa: E402

ID_POOL = "../../evidence/2026-08-31-axis/id_pool.json"
OUT = "../../evidence/2026-08-31-axis/oa_id_probe.json"


def main():
    pool = json.load(io.open(ID_POOL, encoding="utf-8"))["topics"]
    keyed = [t for t in pool if not t["fail"] and t.get("drug")]

    print("=== REF ===")
    print("   rule        %s   FROZEN" % rule_fingerprint()[:16])
    print("   source      Europe PMC cursorMark, free, no key")
    print("   verify      abstract  ⛔ not comparable to any CDSR number")
    print("   population  %d drug-keyed ID topics of %d" % (len(keyed), len(pool)))
    print("   ⛔ NO JUDGING. MATCHED is not a counterpart and none is claimed.")
    print("")
    print("   %-46s %7s %7s %5s %5s %5s %s"
          % ("app_id", "hits", "fetched", "prot", "cond", "ver", "state"))

    out = []
    for t in sorted(keyed, key=lambda x: x["app_id"]):
        dt = [norm(t["drug"].get("pref_name") or "").strip()]
        iterms = sorted(set([x for x in dt if x]) | set(t.get("class_phrases") or []))
        cterms = t.get("condition_terms") or []
        rows, hit, exhausted, st, q, pages = retrieve_all(iterms)
        eligible, kinds = (comparators(rows) if rows else
                           ([], {"n_rows": 0, "n_comparators": 0, "excluded_by_kind": {}}))
        rec = score(eligible, iterms, cterms)
        rec.update({"app_id": t["app_id"], "hit_count": hit, "fetched": len(rows),
                    "exhausted": exhausted, "retrieval_status": st, "kinds": kinds,
                    "intervention_terms": iterms, "condition_terms": cterms,
                    "retrieved_sha256": sha_set(r["oa_id"] for r in rows),
                    "verification_field_kind": "abstract"})
        # ⭐ verified rows are NOT stored here: nothing will be judged, and storing 100s of
        # third-party abstracts to support a number a hash already supports is waste.
        if rec.get("verified"):
            rec["verified"] = {k: v for k, v in rec["verified"].items() if k != "rows"}
        out.append(rec)
        print("   %-46s %7s %7d %5d %5s %5s %s"
              % (t["app_id"], hit if hit is not None else st, len(rows),
                 kinds["excluded_by_kind"].get("protocol", 0),
                 "-" if rec["axis_condition"] is None else rec["axis_condition"]["n"],
                 "-" if rec["verified"] is None else rec["verified"]["n"], rec["state"]))

    print("")
    print("=== FUNNEL ===")
    live = sum(1 for r in out if (r["hit_count"] or 0) > 0)
    fetched = sum(r["fetched"] for r in out)
    prot = sum(r["kinds"]["excluded_by_kind"].get("protocol", 0) for r in out)
    ver = sum(r["verified"]["n"] for r in out if r["verified"])
    c = Counter(r["state"] for r in out)
    print("   topics with a LIVE retrieval : %d / %d" % (live, len(out)))
    print("   fetched                      : %d" % fetched)
    print("   protocols excluded           : %d" % prot)
    print("   VERIFIED PAIRS               : %d   (unjudged)" % ver)
    print("")
    for s in ALL_STATES:
        print("   %-24s %2d" % (s, c.get(s, 0)))
    print("   %-24s %2d   sums: %s" % ("TOTAL", sum(c.values()),
                                       "HOLDS" if sum(c.values()) == len(out) else "BROKEN"))
    notex = [r["app_id"] for r in out if r["hit_count"] and not r["exhausted"]]
    print("")
    print("   NOT exhausted (a LOWER BOUND): %d   %s"
          % (len(notex), ", ".join(notex) if notex else "none"))
    print("   topics MATCHED: %d / %d   ⛔ MATCHED IS NOT A COUNTERPART"
          % (c.get(MATCHED, 0), len(out)))

    json.dump({"rule_fingerprint": rule_fingerprint(), "topics": out},
              io.open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("")
    print("   written: %s" % OUT)


if __name__ == "__main__":
    main()
