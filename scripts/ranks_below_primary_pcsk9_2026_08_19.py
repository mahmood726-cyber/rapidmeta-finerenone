#!/usr/bin/env python3
"""ASK THE WITHHOLDING QUESTION AT EVERY RANK for `pcsk9-inhibitors-cv-review`.

WHY. The pooled estimate here was withdrawn because FOURIER and ODYSSEY OUTCOMES register
composites differing on which deaths, which strokes, and whether coronary revascularisation is
counted. That is a correct refusal ON THE PRIMARY -- and `lint_withholding_asked.py` refused the
commit because a refusal on the primary alone is a WITHHOLDING (P17). Twice tonight the
harmonisable estimand turned out to be a SECONDARY.

The question is especially live here: BOTH trials report the composite's components separately.
If they register the same component endpoint, the refusal to pool the composite does not carry
over to it.

MATCHING IS EXACT ON NORMALISED TITLE TEXT -- case-folded, whitespace-collapsed, nothing looser.
Comparing endpoints by looser name-matching is the error P37 names, and it is the error this
whole withdrawal turns on. So the answer is a LOWER BOUND, and a shared title is a CANDIDATE
rather than a pool: the components still have to be read and no estimate is computed here.
"""
import io
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "ssot"))
import ctgov_transport as X                                             # noqa: E402

TOPIC = "pcsk9-inhibitors-cv-review"
PATH = os.path.join(REPO, "ssot", TOPIC, TOPIC + ".json")
TRIALS = {"NCT01764633": "FOURIER", "NCT01663402": "ODYSSEY OUTCOMES"}


def norm(t):
    return " ".join((t or "").lower().split())


def read_ranks(nct):
    st, s, detail = X.fetch_raw(nct, fields="protocolSection")
    if st != X.OK:
        return {"nct": nct, "state": "UNREACHABLE", "why": str(detail)[:160]}
    om = ((s.get("protocolSection") or {}).get("outcomesModule") or {})
    out = {"nct": nct, "state": "READ", "all_ranks_read_utc": "2026-08-19", "ranks_read": 3,
           "source_field": "protocolSection.outcomesModule (all ranks)",
           "source_url": "https://clinicaltrials.gov/study/%s" % nct}
    for key, field in (("registered_primaries", "primaryOutcomes"),
                       ("registered_secondaries", "secondaryOutcomes"),
                       ("registered_other_outcomes", "otherOutcomes")):
        out[key] = [o.get("measure") for o in (om.get(field) or [])]
    return out


def run(apply_it):
    ranks = {n: read_ranks(n) for n in sorted(TRIALS)}
    for n, r in sorted(ranks.items()):
        if r["state"] != "READ":
            print("REFUSED: %s unreadable -- %s" % (n, r.get("why")))
            return 1
        print("  %-13s %-18s primaries=%d secondaries=%d other=%d"
              % (n, TRIALS[n], len(r["registered_primaries"]),
                 len(r["registered_secondaries"]), len(r["registered_other_outcomes"])))

    seen = {}
    for n, r in ranks.items():
        for k in ("registered_primaries", "registered_secondaries",
                  "registered_other_outcomes"):
            for t in r[k] or []:
                if norm(t):
                    seen.setdefault(norm(t), {})[n] = k.replace("registered_", "")
    shared = {t: v for t, v in seen.items() if len(v) == len(TRIALS)}

    print("\n  endpoints shared by BOTH trials at ANY rank: %d" % len(shared))
    for t, where in sorted(shared.items()):
        print("     %-72s %s" % (t[:72], ", ".join("%s:%s" % (k, v)
                                                   for k, v in sorted(where.items()))))
    if not shared:
        print("     NOTHING is shared at any rank on EXACT normalised title text.")
        print("     That does NOT mean no common quantity exists -- both trials report the")
        print("     composite's components, and they may be titled differently. It means no")
        print("     shared endpoint is establishable WITHOUT reading the component")
        print("     definitions, which is a human act and is not performed here.")

    block = {
        "asked_utc": "2026-08-19",
        "why": ("A refusal to pool on the PRIMARY alone is a withholding (P17). Both trials "
                "report the composite's components separately, so the question is live."),
        "matching": ("EXACT normalised title -- case-folded, whitespace-collapsed. Looser "
                     "matching would compare endpoints by name, which is the error P37 names "
                     "and the error this withdrawal turns on. Therefore a LOWER BOUND."),
        "n_endpoints_shared_at_any_rank": len(shared),
        "shared": [{"title": t, "rank_in_each_trial": w} for t, w in sorted(shared.items())],
        "state": "CANDIDATES_FOUND" if shared else "NOTHING_SHARED_ON_EXACT_TITLE",
        "what_this_is_not": ("A shared title at a shared comparator is a CANDIDATE, not a pool. "
                             "Both trials randomise against PLACEBO, so the comparator does "
                             "not separate them -- but the components still have to be read "
                             "and NO ESTIMATE IS COMPUTED HERE."),
    }

    if not apply_it:
        print("\nDRY RUN -- nothing written. Re-run with --apply.")
        return 0

    with io.open(PATH, "r", encoding="utf-8") as fh:
        o = json.load(fh)
    pr = o["results"]["by_outcome"]["primary"]
    pr["the_withholding_question_asked_at_every_rank"] = block
    by_nct = {t.get("nct"): t for t in (o.get("inputs") or {}).get("trials") or []}
    for n, r in ranks.items():
        t = by_nct.get(n)
        if t is None:
            print("REFUSED: %s is not on the object; refusing to invent a trial row." % n)
            return 1
        for k in ("registered_primaries", "registered_secondaries",
                  "registered_other_outcomes", "all_ranks_read_utc", "ranks_read"):
            t[k] = r[k]
    with io.open(PATH, "w", encoding="utf-8", newline="") as fh:
        fh.write(json.dumps(o, indent=1, ensure_ascii=False))
    print("\n  written; both trials now carry every registered rank")
    return 0


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.exit(run("--apply" in sys.argv))
