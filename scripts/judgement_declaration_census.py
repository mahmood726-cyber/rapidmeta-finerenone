# -*- coding: utf-8 -*-
"""RENAMED FROM audit_judgements_corpus.py ON 2026-08-31, AND THE NAME IS THE FIX.

a CENSUS: it counts how many judgements each topic declares. 0.29 of 8 is a
measurement of the corpus, not a violation of anything, and there is no input
on which it should block.

scripts/lint_gate_can_fail.py refused this file for returning a verdict it
could not enforce. Its doctrine is right and it is worth restating: a module
that reports findings and always exits 0 is a REPORT, and reports are named
_census.py or _triage.py. A GATE THAT CANNOT FAIL IS NOT A DEFECT WHILE
NOTHING RUNS IT -- IT IS A TRAP FOR WHOEVER WIRES IT IN NEXT, who will
reasonably assume a thing called an audit can block. The behaviour here was
always correct; the name was the promise it could not keep.
"""
"""Run the judgement register over EVERY topic and report the distribution.

THIS IS THE PROOF THE REGISTER IS A GENERATOR AND NOT A DOCUMENT. A register
that only ever describes the topic it was written for cannot produce a corpus
number. This one can, and the number is the deliverable:

    of N outcome-blocks holding a pooled result, how many DECLARE each
    judgement, and how many leave it to a default nobody chose?

⚠️ THE DENOMINATOR IS STATED AND IT IS NOT THE CORPUS. Objects with no results
block are not topics with undeclared judgements -- they are topics with no
synthesis, and counting them would inflate every "undeclared" figure. They are
reported separately, by name, so the skip is visible in the coverage number
rather than shrinking the denominator silently.

    python scripts/audit_judgements_corpus.py [--json OUT.json]
"""
import glob
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "ssot"))

import topic_judgements as TJ          # noqa: E402


def main():
    out_path = None
    if "--json" in sys.argv:
        out_path = sys.argv[sys.argv.index("--json") + 1]

    root = os.path.join(os.path.dirname(HERE), "ssot")
    files = [f for f in sorted(glob.glob(os.path.join(root, "*", "*.json")))
             if not f.endswith(".striptest")]

    n_files = len(files)
    unreadable, no_results, blocks = [], [], []

    for f in files:
        name = os.path.basename(f)
        try:
            canon = json.load(open(f, encoding="utf-8"))
        except Exception as exc:
            unreadable.append((name, str(exc)[:60]))
            continue
        if not isinstance(canon, dict):
            unreadable.append((name, "not a JSON object"))
            continue
        bo = ((canon.get("results") or {}) if isinstance(canon.get("results"), dict)
              else {}).get("by_outcome")
        if not isinstance(bo, dict) or not bo:
            no_results.append(name)
            continue
        for oid, res in bo.items():
            if not isinstance(res, dict) or not res.get("pooled"):
                continue
            reg = TJ.derive(canon, oid)
            if reg:
                blocks.append((name, oid, reg))

    # ---------------------------------------------------------- report ----
    tally = {s: {TJ.DECLARED: 0, TJ.UNDECLARED: 0, TJ.NOT_APPLICABLE: 0}
             for s in TJ.SLOTS}
    per_topic_declared = []
    multi_tier = []
    for name, oid, reg in blocks:
        d = 0
        for e in reg["entries"]:
            tally[e["slot"]][e["state"]] = tally[e["slot"]].get(e["state"], 0) + 1
            if e["state"] == TJ.DECLARED:
                d += 1
            if e["slot"] == "COUNT_TIER" and len(e.get("tiers_present") or []) > 1:
                multi_tier.append((name, oid, e.get("tiers_present")))
        per_topic_declared.append((name, oid, d))

    nb = len(blocks)
    print("JUDGEMENT REGISTER -- CORPUS AUDIT")
    print()
    print("  json files found                     : %d" % n_files)
    print("  unreadable / not an object           : %d" % len(unreadable))
    print("  no results.by_outcome (NOT a topic)  : %d" % len(no_results))
    print("  OUTCOME-BLOCKS WITH A POOLED RESULT  : %d   <- the denominator" % nb)
    print()
    print("  %-24s %9s %11s %14s" % ("slot", "DECLARED", "UNDECLARED",
                                     "NOT_APPLICABLE"))
    for s in TJ.SLOTS:
        t = tally[s]
        print("  %-24s %4d/%-4d %6d/%-4d %9d/%-4d"
              % (s, t[TJ.DECLARED], nb, t[TJ.UNDECLARED], nb,
                 t[TJ.NOT_APPLICABLE], nb))
    print()
    dist = {}
    for _, _, d in per_topic_declared:
        dist[d] = dist.get(d, 0) + 1
    print("  DECLARED judgements per outcome-block (of %d slots):" % len(TJ.SLOTS))
    for k in sorted(dist):
        print("    %d declared : %3d of %d blocks" % (k, dist[k], nb))
    if per_topic_declared:
        avg = sum(d for _, _, d in per_topic_declared) / float(nb)
        print("    mean        : %.2f of %d" % (avg, len(TJ.SLOTS)))
    print()
    best = sorted(per_topic_declared, key=lambda x: -x[2])[:6]
    print("  MOST-DECLARED blocks:")
    for name, oid, d in best:
        print("    %-46s %-10s %d" % (name[:46], oid, d))
    print()
    print("  BLOCKS HOLDING MORE THAN ONE COUNT TIER: %d of %d" % (len(multi_tier), nb))
    for name, oid, tiers in multi_tier[:10]:
        print("    %-46s %-10s %s" % (name[:46], oid, tiers))
    if no_results:
        print()
        print("  SKIPPED, BY NAME (no results.by_outcome) -- first 10 of %d:"
              % len(no_results))
        for x in no_results[:10]:
            print("    %s" % x)

    if out_path:
        with open(out_path, "w", encoding="utf-8") as fh:
            json.dump({
                "denominator": {
                    "json_files": n_files,
                    "unreadable": len(unreadable),
                    "no_results_block": len(no_results),
                    "outcome_blocks_with_a_pooled_result": nb,
                    "_what_the_denominator_is_OF": (
                        "OUTCOME-BLOCKS carrying a pooled result. Not topics, "
                        "not files. A topic with three pooled outcomes "
                        "contributes three."),
                },
                "tally": tally,
                "declared_per_block": dist,
                "multi_count_tier_blocks": multi_tier,
                "skipped_no_results": no_results,
                "unreadable": unreadable,
            }, fh, indent=1, ensure_ascii=False)
        print()
        print("  written %s" % out_path)


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                  errors="replace")
    main()
