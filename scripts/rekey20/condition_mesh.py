# -*- coding: utf-8 -*-
"""THE CONDITION VOCABULARY, RUN ALONGSIDE THE INCUMBENT. Never instead of it.

⛔ THE RULE IS FROZEN. `rekey_rule.py` is not touched. This file adds a SECOND column and
publishes both; the incumbent literal-word axis keeps running exactly as it does today.

THE DEFECT BEING ADDRESSED, measured on CDSR:

    dabigatran-stroke   ['stroke']                 198 / 1,186   PROMISCUOUS
    olmesartan-htn      ['hypertension']            95 / 1,186   PROMISCUOUS
    pitavastatin        ['hypercholesterolemia']     0 / 1,186   DEAD

⚠️ THE 198 IS AS MUCH A DEFECT AS THE 0, and only one of them looks like one. A dead term
returns an obvious zero; a promiscuous term returns a plausible number and manufactures the
false positives adjudication then has to kill by hand.

⭐ THE EXPANSION IS PER CONCEPT, NOT PER TERM, AND THAT IS THE WHOLE DESIGN.
The incumbent treats each condition WORD as a concept and requires `min(2, n)` of them.
Adding MeSH synonyms as extra TERMS would inflate `n` and make the threshold easier --
which would look like a recall gain and be a threshold change. So: the CONCEPT COUNT AND
THE THRESHOLD ARE UNCHANGED, and each concept simply gains synonyms. A concept is satisfied
if ANY of its synonyms appears. The only thing that can change is which rows satisfy a
concept, never how many concepts are needed.

⭐ EVERY SYNONYM GETS ITS OWN HIT COUNT. A disjunction is green as soon as one branch fires;
a synonym list is the same shape. Dead synonyms are named, not hidden inside a concept's
total.

⛔ REGRESSION IS PRE-REGISTERED (PRE-REGISTRATION-OA-FRAME-AND-CONDITION-VOCAB.md B.3) and
is applied here mechanically. R1-R4 were written before the first query.
"""
import io, json, os, sys, time
from collections import OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
os.chdir(HERE)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                              line_buffering=True)
from rekey_rule import norm, contains, split_title, STOP, ABBREV, _stem  # noqa: E402
from axis_match import prepare, terms_for, sha_set                       # noqa: E402
from axis_states import MATCHED                                          # noqa: E402
import search_topic as ST                                                # noqa: E402

FRAME = "F:/claude-temp/pend/cdsr_frame_cardiology.jsonl"
CORR = "../../evidence/2026-08-31-rekey/corrected"
INCUMBENT = "../../evidence/2026-08-31-axis/axis_states_twenty.json"
CACHE = "../../evidence/2026-08-31-axis/mesh_cache.json"
OUT = "../../evidence/2026-08-31-axis/condition_mesh_twenty.json"

# R2 -- the counterparts that must survive, by cd_base, hashed as a SET.
MUST_SURVIVE = ["CD004434", "CD006681", "CD014808", "CD015003"]
R3_FLOOR = 6.0 / 14.0            # the incumbent's verified-stage precision
R4_MAX_FRACTION = 0.25           # a term matching a quarter of everything is not a condition


def surface_concepts(cond_span):
    """The condition's concepts with their SURFACE form kept.

    ⚠️ The incumbent's `condition_terms()` returns STEMMED, spelling-normalised tokens --
    `venou`, `hypercholesterolemia`. Sending `venou` to MeSH would return nothing and the
    expansion would look empty for a reason that has nothing to do with MeSH. So the
    surface word is kept beside the stem and the LOOKUP uses the surface form.
    """
    out = OrderedDict()
    import re as _re
    for w in _re.sub(r"[^a-zA-Z0-9]+", " ", cond_span or "").lower().split():
        if w in ABBREV:
            for x in ABBREV[w].split():
                k = _stem(norm(x).strip())
                out.setdefault(k, x)
        elif w not in STOP and len(w) > 2:
            k = _stem(_re.sub(r"[^a-z0-9]", "", norm(w).strip()))
            out.setdefault(k, w)
    return OrderedDict((k, v) for k, v in out.items() if k)


def mesh_for(word, cache):
    if word in cache:
        return cache[word]
    terms, st = ST.mesh_entry_terms(word)
    cache[word] = {"terms": terms, "status": st}
    time.sleep(0.4)
    return cache[word]


def main():
    rows, reviews = prepare(FRAME)
    twenty = json.load(io.open(os.path.join(CORR, "twenty.json"), encoding="utf-8"))["topics"]
    inc = {t["app_id"]: t for t in json.load(io.open(INCUMBENT, encoding="utf-8"))["topics"]}
    cache = json.load(io.open(CACHE, encoding="utf-8")) if os.path.exists(CACHE) else {}

    print("=== REF ===")
    print("   frame      %s   %d reviews" % (sha_set(r["cd_base"] for r in rows)[:16], len(reviews)))
    print("   rule       FROZEN -- rekey_rule.py untouched; this adds a COLUMN, not a rule")
    print("   incumbent  literal condition words, need=min(2,n)")
    print("   candidate  same concepts, same threshold, each concept gains MeSH synonyms")
    print("   R1-R4      pre-registered before the first query")
    print("")

    out, syn_report = [], []
    for t in sorted(twenty, key=lambda x: x["app_id"]):
        app = t["app_id"]
        dt, ct, _ = terms_for(t.get("drug") or {})
        iterms = sorted(set(dt) | set(ct))
        cterms = t.get("condition_terms") or []
        rec = {"app_id": app, "condition_terms": cterms,
               "incumbent_state": inc[app]["state"]}
        if not cterms or not iterms:
            # ⛔ Expanding nothing yields nothing. `norm([])` is still `[]`, and a topic with
            # no condition span has no span to expand. Predicted in B.4 and asserted here.
            rec.update({"mesh_state": "REFUSED_NO_TERMS", "expanded": False,
                        "axis_condition_incumbent": None, "axis_condition_mesh": None})
            out.append(rec)
            continue

        concepts = surface_concepts(t.get("condition_span") or "")
        # Fall back to the stem as its own surface form if the span could not be re-derived.
        for k in cterms:
            concepts.setdefault(k, k)
        syn = OrderedDict()
        for stem_k, surface in concepts.items():
            if stem_k not in cterms:
                continue
            m = mesh_for(surface, cache)
            s = [stem_k] + [x for x in (norm(y).strip() for y in m["terms"]) if x and x != stem_k]
            syn[stem_k] = {"surface": surface, "synonyms": s, "mesh_status": m["status"]}

        need = min(2, len(cterms))

        def hits(use_syn):
            keep = []
            for r in reviews:
                sat = 0
                for k in cterms:
                    pool = syn[k]["synonyms"] if (use_syn and k in syn) else [k]
                    if any(contains(r["_all"], p) for p in pool):
                        sat += 1
                if sat >= need:
                    keep.append(r)
            return keep

        inc_rows, mesh_rows = hits(False), hits(True)

        def verified(chosen):
            v = []
            for r in chosen:
                if r["_obj"] is None or not any(contains(r["_obj"], x) for x in iterms):
                    continue
                sat = sum(1 for k in cterms
                          if any(contains(r["_obj"], p)
                                 for p in (syn[k]["synonyms"] if k in syn else [k])))
                if sat >= need:
                    v.append(r)
            return v

        i_hits = [r for r in inc_rows if any(contains(r["_all"], x) for x in iterms)]
        m_hits = [r for r in mesh_rows if any(contains(r["_all"], x) for x in iterms)]
        v_inc = [r["cd_base"] for r in verified(i_hits)]
        v_mesh = [r["cd_base"] for r in verified(m_hits)]

        rec.update({
            "expanded": True, "need": need,
            "axis_condition_incumbent": {"n": len(inc_rows),
                                         "frac": round(len(inc_rows) / float(len(reviews)), 4)},
            "axis_condition_mesh": {"n": len(mesh_rows),
                                    "frac": round(len(mesh_rows) / float(len(reviews)), 4)},
            "verified_incumbent": sorted(v_inc), "verified_mesh": sorted(v_mesh),
            "verified_incumbent_sha": sha_set(v_inc), "verified_mesh_sha": sha_set(v_mesh),
            "mesh_state": MATCHED if v_mesh else "not_matched",
            "synonyms": {k: v["synonyms"] for k, v in syn.items()}})
        out.append(rec)

        for k, v in syn.items():
            for s in v["synonyms"]:
                if s == k:
                    continue
                syn_report.append((app, k, s, sum(1 for r in reviews if contains(r["_all"], s))))

    json.dump(cache, io.open(CACHE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    print("=== literal -> MeSH, PER TOPIC. Both columns published. ===")
    print("   %-46s %-22s %11s %11s %s" % ("app_id", "incumbent state", "condC lit",
                                           "condC mesh", "verified lit -> mesh"))
    for r in out:
        if not r["expanded"]:
            print("   %-46s %-22s %11s %11s   (no condition span to expand)"
                  % (r["app_id"], r["incumbent_state"], "-", "-"))
            continue
        a, b = r["axis_condition_incumbent"], r["axis_condition_mesh"]
        print("   %-46s %-22s %5d %4.0f%% %5d %4.0f%%   %d -> %d%s"
              % (r["app_id"], r["incumbent_state"], a["n"], 100 * a["frac"],
                 b["n"], 100 * b["frac"], len(r["verified_incumbent"]),
                 len(r["verified_mesh"]),
                 "" if a["n"] == b["n"] else "   <- CHANGED"))

    print("")
    print("=== EVERY SYNONYM WITH ITS OWN HIT COUNT. A dead one cannot hide in a total. ===")
    live = [s for s in syn_report if s[3] > 0]
    print("   synonyms added: %d   live on this frame: %d   dead: %d"
          % (len(syn_report), len(live), len(syn_report) - len(live)))
    for app, k, s, n in sorted(live, key=lambda x: -x[3])[:15]:
        print("      %-30s %-22s -> %-34s %5d" % (app, k, s, n))
    if not live:
        print("      ⛔ NOT ONE ADDED SYNONYM MATCHES ANY ROW. The expansion is inert on "
              "this frame, and a change that cannot move a number is not an improvement.")

    print("")
    print("=== ⛔ REGRESSION, PRE-REGISTERED B.3, APPLIED MECHANICALLY ===")
    trips = []
    for r in out:
        if not r["expanded"]:
            continue
        if r["incumbent_state"] == MATCHED and not r["verified_mesh"]:
            trips.append(("R1", "%s was MATCHED and is not under MeSH" % r["app_id"]))
        lost = set(r["verified_incumbent"]) - set(r["verified_mesh"])
        keep = [b for b in MUST_SURVIVE if b in lost]
        if keep:
            trips.append(("R2", "%s loses %s" % (r["app_id"], ", ".join(keep))))
        if r["axis_condition_mesh"]["frac"] > R4_MAX_FRACTION:
            trips.append(("R4", "%s condition axis is %.0f%% of the frame (max %.0f%%)"
                          % (r["app_id"], 100 * r["axis_condition_mesh"]["frac"],
                             100 * R4_MAX_FRACTION)))
    tot_v = sum(len(r["verified_mesh"]) for r in out if r["expanded"])
    print("   R1 no MATCHED topic may become unmatched")
    print("   R2 CD004434 CD006681 CD014808 CD015003 must all survive")
    print("   R3 verified-stage precision must not fall below %.0f%% -- NOT COMPUTABLE here"
          % (100 * R3_FLOOR))
    print("      (it needs a judgement on every new verified pair; %d verified pairs under "
          "MeSH vs %d under the incumbent)"
          % (tot_v, sum(len(r["verified_incumbent"]) for r in out if r["expanded"])))
    print("   R4 no condition axis may exceed %.0f%% of the frame" % (100 * R4_MAX_FRACTION))
    print("")
    if trips:
        print("   ⛔ TRIPPED %d:" % len(trips))
        for k, m in trips:
            print("      %-3s %s" % (k, m))
        print("")
        print("   ⇒ MeSH EXPANSION IS NOT ADOPTED. The incumbent literal axis stands.")
    else:
        print("   no criterion tripped.")
        print("   ⚠️ AND THAT IS STILL NOT AN ADOPTION. R3 is not computable without "
              "adjudicating every new verified pair, so the honest verdict is PUBLISHED "
              "ALONGSIDE, PENDING R3 -- not adopted.")

    json.dump({"trips": trips, "topics": out}, io.open(OUT, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("")
    print("   written: %s" % OUT)


if __name__ == "__main__":
    main()
