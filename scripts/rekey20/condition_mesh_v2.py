# -*- coding: utf-8 -*-
"""THE CONDITION AXIS, v2: SPAN-LEVEL, RECORD-VERIFIED, TREE-BROADENED. Alongside, never
instead.

⛔ THE RULE IS FROZEN. `rekey_rule.py` and `axis_states.py` are untouched; the intervention
axis is byte-identical to the incumbent's. This adds a SECOND CONDITION COLUMN and publishes
both.

WHAT v1 GOT WRONG ABOUT ITSELF. `REPORT-CONDITION-MESH.md` §3.1 blamed the UNIT -- words
expanded where a phrase was meant. Measured since, the phrase queries fail too:
`pulmonary arterial hypertension` free-text returns `Familial Primary Pulmonary
Hypertension`, and `paroxysmal supraventricular tachycardia` returns `Tachycardia,
Ventricular`. ⇒ THE ROOT CAUSE IS AN UNVERIFIED RECORD. v1's section stands in the record;
this supersedes it.

THE THREE CHANGES, each measured before this file was written:
  1. `[MeSH Terms]`-bound lookup      -- fixes 5 of 8 probe terms outright
  2. RECORD-IDENTITY VERIFICATION     -- the descriptor's own name must answer the query,
                                         else the concept is REFUSED and contributes nothing
  3. BROADER TERMS via the tree       -- `Hypercholesterolemia` -> `Hyperlipidemias`

⭐ #2 IS THE SEMANTIC CRITERION the v1 report named as missing. R1-R4 were all quantitative
and none of them could see `supraventricular -> ventricular tachycardia`. This one can,
because it asks a question the numbers cannot: is this the record I asked for?

⚠️ v2 IS NOT UNIFORMLY LOOSER, and the comparison must not be smuggled. The incumbent takes
min(2, n) of the span's WORDS; v2 requires the whole PHRASE (or a verified synonym or
broader term). It is stricter on the phrase and wider on vocabulary, so it can LOSE rows.
That is why R1 is a real risk and why both columns are published.
"""
import io
import json
import os
import sys
from collections import OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.chdir(HERE)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                              line_buffering=True)
from rekey_rule import norm, contains                                   # noqa: E402
from axis_match import prepare, terms_for, sha_set                      # noqa: E402
from axis_states import MATCHED                                         # noqa: E402
import mesh_lookup as M                                                 # noqa: E402

FRAME = "F:/claude-temp/pend/cdsr_frame_cardiology.jsonl"
CORR = "../../evidence/2026-08-31-rekey/corrected"
INCUMBENT = "../../evidence/2026-08-31-axis/axis_states_twenty.json"
CACHE = "../../evidence/2026-08-31-axis/mesh_v2_cache.json"
OUT = "../../evidence/2026-08-31-axis/condition_mesh_v2_twenty.json"

MUST_SURVIVE = ["CD004434", "CD006681", "CD014808", "CD015003"]
R3_FLOOR = 6.0 / 14.0
R4_MAX_FRACTION = 0.25


def main():
    rows, reviews = prepare(FRAME)
    twenty = json.load(io.open(os.path.join(CORR, "twenty.json"), encoding="utf-8"))["topics"]
    inc = {t["app_id"]: t for t in json.load(io.open(INCUMBENT, encoding="utf-8"))["topics"]}
    cache = M.load_cache(CACHE)

    print("=== REF ===")
    print("   frame        %s   %d reviews" % (sha_set(r["cd_base"] for r in rows)[:16],
                                               len(reviews)))
    print("   rule         FROZEN -- a COLUMN, not a rule change")
    print("   incumbent    span WORDS, need = min(2, n)")
    print("   v2           PHRASE on {span} u verified entry terms u verified broader terms")
    print("")
    # ⛔ THE LOOKUP'S OWN CONTROL, BEFORE ANY TOPIC. `[MeSH Tree Number]` returns count=0
    # silently; a broadening step that can never return a parent would make every dead term
    # stay dead and read as "MeSH holds no broader concept".
    ok, desc = M.tree_field_works(cache=cache)
    print("=== CONTROL: can the broadening step return a POSITIVE at all? ===")
    print("   C18.452.584.500.500.396 -> parent -> %r   %s" % (desc, "PASS" if ok else "FAIL"))
    if not ok:
        print("   REFUSING: the tree field resolves nothing, so every 'no broader term' "
              "below would be a property of the harness, not of MeSH. NO COUNT PRINTED.")
        M.save_cache(cache, CACHE)
        sys.exit(1)
    print("")

    out, refused, term_hits = [], [], []
    for t in sorted(twenty, key=lambda x: x["app_id"]):
        app = t["app_id"]
        dt, ct, _ = terms_for(t.get("drug") or {})
        iterms = sorted(set(dt) | set(ct))
        cterms = t.get("condition_terms") or []
        span = (t.get("condition_span") or "").strip()
        rec = {"app_id": app, "condition_span": span or None,
               "incumbent_state": inc[app]["state"],
               "incumbent_verified": (inc[app].get("verified") or {}).get("bases", [])
               if inc[app].get("verified") else []}

        if not span or not iterms or not cterms:
            rec.update({"v2_state": "REFUSED_NO_TERMS", "expanded": False,
                        "axis_condition_v2": None, "verified_v2": [], "terms_v2": []})
            out.append(rec)
            continue

        r = M.lookup(span, cache=cache)
        terms = [norm(span).strip()]
        if r["verified"]:
            for e in r["entry_terms"]:
                v = norm(e).strip()
                if v and v not in terms:
                    terms.append(v)
            for _tn, d in M.broader(r["tree_numbers"], cache=cache):
                v = norm(d).strip()
                if v and v not in terms:
                    terms.append(v)
        else:
            # ⛔ AN UNVERIFIED RECORD CONTRIBUTES NOTHING. This is the whole semantic gate.
            refused.append((app, span, r["descriptor"], r["status"]))

        ch = [x for x in reviews if any(contains(x["_all"], tm) for tm in terms)]
        ih = [x for x in ch if any(contains(x["_all"], it) for it in iterms)]
        ver = [x["cd_base"] for x in ih
               if x["_obj"] is not None
               and any(contains(x["_obj"], it) for it in iterms)
               and any(contains(x["_obj"], tm) for tm in terms)]

        for tm in terms:
            term_hits.append((app, tm, sum(1 for x in reviews if contains(x["_all"], tm))))

        rec.update({"expanded": True, "record_verified": r["verified"],
                    "record_descriptor": r["descriptor"], "record_status": r["status"],
                    "terms_v2": terms,
                    "axis_condition_v2": {"n": len(ch),
                                          "frac": round(len(ch) / float(len(reviews)), 4)},
                    "verified_v2": sorted(ver), "verified_v2_sha": sha_set(ver),
                    "v2_state": MATCHED if ver else "not_matched"})
        out.append(rec)

    M.save_cache(cache, CACHE)

    print("=== literal -> MeSH v2, PER TOPIC. Both columns published. ===")
    print("   %-46s %-22s %11s %11s  %s" % ("app_id", "incumbent state", "condC inc",
                                            "condC v2", "verified inc -> v2"))
    for r in out:
        a = (inc[r["app_id"]].get("axis_condition") or {})
        if not r["expanded"]:
            print("   %-46s %-22s %11s %11s   (no span to expand)"
                  % (r["app_id"], r["incumbent_state"], "-", "-"))
            continue
        b = r["axis_condition_v2"]
        print("   %-46s %-22s %5s %5s %5d %4.0f%%  %d -> %d%s"
              % (r["app_id"], r["incumbent_state"], a.get("n", "-"), "",
                 b["n"], 100 * b["frac"],
                 len(r["incumbent_verified"]), len(r["verified_v2"]),
                 "" if not r.get("record_verified") is False else "   [RECORD REFUSED]"))

    print("")
    print("=== ⭐ THE SEMANTIC GATE -- concepts REFUSED because the record was not the one asked for ===")
    print("   refused: %d" % len(refused))
    for app, span, desc, st in refused:
        print("      %-40s %-34s -> %-30s %s" % (app, span[:34], str(desc)[:30], st))
    if not refused:
        print("      ⚠️ NONE refused. A semantic gate that never fires is not yet evidence "
              "of anything; v1 needed it for `supraventricular`.")

    print("")
    print("=== EVERY v2 TERM WITH ITS OWN HIT COUNT ===")
    live = [x for x in term_hits if x[2] > 0]
    print("   terms: %d   live: %d   dead: %d" % (len(term_hits), len(live),
                                                  len(term_hits) - len(live)))
    for app, tm, n in sorted(live, key=lambda x: -x[2])[:14]:
        print("      %-40s %-38s %5d" % (app, tm[:38], n))

    print("")
    print("=== ⛔ REGRESSION R1-R5 ===")
    trips = []
    for r in out:
        if not r["expanded"]:
            continue
        if r["incumbent_state"] == MATCHED and not r["verified_v2"]:
            trips.append(("R1", "%s was MATCHED and is not under v2" % r["app_id"]))
        lost = set(r["incumbent_verified"]) - set(r["verified_v2"])
        keep = [b for b in MUST_SURVIVE if b in lost]
        if keep:
            trips.append(("R2", "%s loses %s" % (r["app_id"], ", ".join(keep))))
        if r["axis_condition_v2"]["frac"] > R4_MAX_FRACTION:
            trips.append(("R4", "%s condition axis is %.0f%% of the frame"
                          % (r["app_id"], 100 * r["axis_condition_v2"]["frac"])))
    print("   R1 no MATCHED topic may become unmatched")
    print("   R2 CD004434 CD006681 CD014808 CD015003 must all survive")
    print("   R3 precision must not fall below %.0f%% -- NOT COMPUTABLE without judging "
          "every new pair" % (100 * R3_FLOOR))
    print("   R4 no condition axis above %.0f%% of the frame" % (100 * R4_MAX_FRACTION))
    print("   R5 NEW, SEMANTIC: no unverified MeSH record may contribute a term "
          "-- enforced by construction, %d concept(s) refused" % len(refused))
    print("")
    if trips:
        print("   ⛔ TRIPPED %d:" % len(trips))
        for k, m in trips:
            print("      %-3s %s" % (k, m))
        print("")
        print("   ⇒ v2 IS NOT ADOPTED. The incumbent literal axis stands.")
    else:
        print("   no criterion tripped.")
        print("   ⚠️ STILL NOT AN ADOPTION. R3 needs a judgement on every new verified pair, "
              "so the verdict is PUBLISHED ALONGSIDE, PENDING R3.")

    json.dump({"trips": trips, "refused_records": refused, "topics": out},
              io.open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("")
    print("   written: %s" % OUT)


if __name__ == "__main__":
    main()
