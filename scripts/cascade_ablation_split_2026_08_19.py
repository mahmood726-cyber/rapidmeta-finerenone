"""ARM-ROLE CASCADE for the three topics `ablation-af-review` was split into.

ONE FETCH POOL, THREE INDEPENDENT CLASSIFICATIONS, AND THE DISTINCTION MATTERS.
The three surfaced sets overlap heavily (931, 959 and 67 records over one registry on one
date), so each registration is fetched ONCE. What is NOT shared is the classification: each
topic declares its own synonym set and its own counts, and no topic's k is derived from
another's. Sharing a FETCH is a network economy; sharing a COUNT would be the contamination
class this project has now met five times.

WHY k3 AND k4 MUST BE READ TOGETHER ON THIS TOPIC, AND IT IS NOT A JUDGEMENT CALL.
Two of the three trials `ablation-af-medical-therapy` includes declare NO ARM TYPED
EXPERIMENTAL:

    CABANA   NCT00911508   ACTIVE_COMPARATOR 'Left Atrial Ablation'
                           ACTIVE_COMPARATOR 'Rate or Rhythm Control Therapy'
    RAFT-AF  NCT01420393   ACTIVE_COMPARATOR 'Rhythm Control'
                           ACTIVE_COMPARATOR 'Rate Control'

Both arms are typed the same, so the registry's typing carries no information about which side
is the intervention -- and `locate()` correctly declines to invent one. These are HEAD-TO-HEAD
STRATEGY TRIALS, which is what an ablation-versus-medical-therapy review is made of. A cascade
that reported k3 alone would put the two largest trials of the topic outside the count.

    THE REGISTRY'S ARM TYPING IS A DATA-ENTRY CONVENTION. It was already established that
    trials exist with no arm typed EXPERIMENTAL, and that one programme can type two identical
    designs oppositely (ADVANCE-2 / ADVANCE-3). Here it is not an anomaly at the edge of the
    corpus -- it is the DOMINANT shape of the topic's own pivotal evidence.
"""
import io
import json
import os
import sys
import time

REPO = "F:/rapidmeta-ssot-shell"
sys.path.insert(0, REPO + "/ssot")
sys.path.insert(0, REPO + "/scripts")
os.environ.setdefault(
    "RM_CTGOV_CACHE",
    "F:/claude-temp/claude/F--rapidmeta-ssot-shell/"
    "eb4d84e5-8a24-4c3b-afe2-34bd91c20bc7/scratchpad/.ctgov-raw-cache")

import ctgov_transport as X          # noqa: E402
import topic_identity as T           # noqa: E402

SEARCH = os.path.join(REPO, "evidence", "2026-08-19-batch1", "ablation_split_search.json")
DEST = os.path.join(REPO, "evidence", "2026-08-19-batch1", "ablation_split_cascade.json")

# Each topic's own synonym key. `catheter ablation` is already declared in
# topic_identity.TOPIC_SYNONYMS; the rhythm-control topic is a STRATEGY and its identity is
# stated here as its own declared set rather than borrowed from the ablation one.
TOPIC_KEY = {
    "ablation-af-medical-therapy": "catheter ablation",
    "early-rhythm-control-af": "rhythm control strategy",
    "ablation-af-heart-failure": "catheter ablation",
}
INCLUDED = {
    "ablation-af-medical-therapy": ["NCT00643188", "NCT00911508", "NCT01420393"],
    "early-rhythm-control-af": ["NCT00643188", "NCT00911508", "NCT01288352", "NCT01420393"],
    "ablation-af-heart-failure": ["NCT00643188", "NCT01420393"],
}


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    with io.open(SEARCH, encoding="utf-8") as fh:
        searches = json.load(fh)

    chosen = {}
    for topic, rec in searches.items():
        label = rec.get("chosen")
        q = next(q for q in rec["queries"] if q["label"] == label)
        chosen[topic] = q
        print("%-30s %-58s k0=%d" % (topic, label[:58], q["k0"]))

    pool = sorted({n for q in chosen.values() for n in q["ids"]})
    print("\nONE FETCH POOL: %d distinct registrations across the three surfaced sets "
          "(%s)\n" % (len(pool), " + ".join(str(q["k0"]) for q in chosen.values())))

    payloads, unreachable = {}, []
    for i, nct in enumerate(pool, 1):
        st, study, det = X.fetch_raw(nct)
        if st != X.OK:
            unreachable.append(nct)
            continue
        payloads[nct] = X.require_raw_v2(study, nct)
        if i % 200 == 0:
            print("   fetched %d/%d" % (i, len(pool)))
        time.sleep(0.01)
    print("   fetched %d, UNREACHABLE %d -- never read, not a verdict\n"
          % (len(payloads), len(unreachable)))

    out = {}
    for topic, q in chosen.items():
        syns = T.synonyms_for(TOPIC_KEY[topic])
        roles, evidence = {}, {}
        unr = []
        for nct in q["ids"]:
            if nct not in payloads:
                unr.append(nct)
                continue
            role, ev = T.locate(payloads[nct], syns)
            roles[nct] = role
            evidence[nct] = ev
        tally = {r: [n for n, v in roles.items() if v == r]
                 for r in (T.EXPERIMENTAL, T.COMPARATOR, T.BACKGROUND, T.NOT_ASSESSABLE)}
        k3, k4 = len(tally[T.EXPERIMENTAL]), len(tally[T.COMPARATOR])
        k5, kna = len(tally[T.BACKGROUND]), len(tally[T.NOT_ASSESSABLE])
        inc = INCLUDED[topic]
        out[topic] = {
            "topic_key": TOPIC_KEY[topic], "query_label": q["label"], "query_expr": q["expr"],
            "search_detail": q["detail"],
            "k0_surfaced": q["k0"], "k2_role_located": k3 + k4 + k5,
            "k3_experimental": k3, "k4_comparator": k4, "k5_background": k5,
            "kNA_not_assessable": kna, "kUNREACHABLE": len(unr),
            "k_included_in_object": len(inc),
            "candidate_pool_k3_plus_k4": k3 + k4,
            "experimental_ids": tally[T.EXPERIMENTAL], "comparator_ids": tally[T.COMPARATOR],
            "not_assessable_ids": tally[T.NOT_ASSESSABLE],
            "unreachable_ids": unr,
            "included": inc,
            "role_of_each_included": {n: roles.get(n, "UNREACHABLE") for n in inc},
            "evidence_for_each_included": {n: evidence.get(n) for n in inc},
        }
        print("--- %s   [%s]" % (topic, TOPIC_KEY[topic]))
        print("    k0 surfaced        %5d" % q["k0"])
        print("    k2 role located    %5d" % (k3 + k4 + k5))
        print("    k3 EXPERIMENTAL    %5d" % k3)
        print("    k4 COMPARATOR      %5d   <- read WITH k3 on this topic; see module docstring"
              % k4)
        print("    k5 background      %5d" % k5)
        print("    kNA not assessable %5d   <- could not classify, NOT excluded" % kna)
        print("    kUNREACHABLE       %5d   <- never read" % len(unr))
        print("    reconciles: %d == %d + %d + %d + %d + %d -> %s"
              % (q["k0"], k3, k4, k5, kna, len(unr),
                 q["k0"] == k3 + k4 + k5 + kna + len(unr)))
        print("    CANDIDATE POOL (k3+k4) %d, of which %d are in this object"
              % (k3 + k4, len(inc)))
        for n in inc:
            print("       %s  %-28s %s" % (n, roles.get(n, "UNREACHABLE"),
                                           (evidence.get(n) or "")[:80]))
        missing = [n for n in inc if n not in roles]
        if missing:
            print("    !! INCLUDED BUT NOT IN THE SURFACED SET: %s" % missing)
        print()

    with io.open(DEST, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(out, indent=1))
    print("wrote %s" % DEST)
    return 0


if __name__ == "__main__":
    sys.exit(main())
