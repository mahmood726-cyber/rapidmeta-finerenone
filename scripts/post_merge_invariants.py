# -*- coding: utf-8 -*-
"""Assert that a MERGE did not silently revert a correction.

⛔ WHY THIS EXISTS, AND IT IS A CLASS NOT AN INCIDENT.

Hours before this was written, a gate in `ssot/topic_judgements.py` was replaced
with a stricter one. The signature changed; every caller still passed the old
argument list; the strict branch was never reached. Two corpus counts went
straight back to their pre-fix values -- ELIGIBILITY_RULE 14 -> 21 and ESTIMAND
21 -> 39, a 37% over-count returning by the back door. Nothing errored. One
census run caught it, and only because the number was being watched.

    ⭐ A STRICTER GATE THAT IS NEVER INVOKED IS LOOSER THAN THE LOOSE ONE IT
      REPLACED. A CHANGED SIGNATURE IS NOT A CHANGED GATE.

⇒ A MERGE IS A GATE REPLACEMENT IN DISGUISE. Someone else's version of a shared
file can revert a correction exactly as a signature change did, resolve without
a conflict, and leave the tree count identical. `git ls-tree | wc -l` cannot see
it. Only re-measuring can.

So this asserts the MEASUREMENTS, not the tree:

    python scripts/post_merge_invariants.py

Exit 1 on any drift, naming what moved and in which direction. Update the
expected values ONLY with a stated reason -- a baseline nobody re-reads is how
erosion starts.

⛔ AND MEASURE EVERY EXPECTED VALUE FROM A COMMIT, NEVER FROM THE WORKING TREE.
This worktree is shared: at any moment it carries other lanes' uncommitted
edits. The first version of this file baselined question_pico_declared at 4 by
reading the working tree; three of those four declarations lived only in
another lane's unsaved changes. The number was therefore unreproducible from
any commit, and the first merge this file guarded was accused of reverting a
correction that had never been committed by anyone. The instrument was right
and its baseline was fiction.
"""
import io
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "ssot"))

# Measured 2026-08-31, pre-merge, on HEAD 48cd999bc + the working tree.
# Each carries WHY it is what it is, so a later reader can tell a legitimate
# change from a regression rather than just seeing a number move.
EXPECT = {
    "eligibility_declared": (14,
        "gated by the self-negation test; 21 is the UNGATED value and its "
        "return means is_authored stopped being invoked"),
    "estimand_declared": (21,
        "same gate; 39 is the ungated value"),
    "question_pico_declared": (1,
        "ONE topic -- dapivirine -- declares all four axes with authored "
        "populations, measured from the COMMIT. This baseline read 4 until "
        "2026-08-31, and the 4 was wrong: it was measured in the shared "
        "worktree, whose working tree carried three other lanes' UNCOMMITTED "
        "stores (alirocumab-lipid, apixaban-vte-treatment, gepotidacin-uti). "
        "Those declarations exist in nobody's history, so no merge could "
        "preserve them and this invariant refused the first merge it ever "
        "guarded -- naming a regression that had not happened. "
        "A BASELINE MEASURED FROM A WORKING TREE IS NOT A BASELINE: it is "
        "anchored to state that changes under it, so it retires itself and "
        "then accuses the next change. Measure from HEAD, or from a named "
        "commit, and say which"),
    "index_entry_declared": (0,
        "no topic carries the sentence its index tile shows"),
    "dapivirine_declared": (5,
        "of 8 slots; the only block in the corpus above 2"),
    "dapivirine_proven_authored": (0,
        "__derived_from is new and nothing is annotated; ZERO IS EXPECTED and "
        "is not a regression -- but it must move to 1 under a plant, which is "
        "asserted below"),
    "tabs_in_build": (8,
        "the ruled eight in ssot/page_format_v1.json v1"),
    # ⭐ THE DENOMINATOR IS ITSELF AN INVARIANT. Every rate above is a count of
    # DECLARED slots; if a merge dropped an object, each of those counts could
    # fall and still look like a legitimate corpus change. Pinning what was
    # LOOKED AT makes a shrinking population fail loudly instead of quietly
    # improving the numerator's odds.
    "corpus_files_seen": (161,
        "ssot/*/*.json at HEAD 48cd999bc; a fall means an object was lost, a "
        "rise means a topic was added and every count below needs re-reading"),
    "pooled_blocks": (146,
        "of 175 outcome entries in the 141 objects that carry by_outcome; the "
        "denominator of every DECLARED count in this table"),
}


def fail(msgs):
    print()
    print("REFUSED: %d invariant(s) moved." % len(msgs))
    for m in msgs:
        print("   %s" % m)
    print()
    print("A merge that resolves cleanly and reverts a correction leaves the "
          "tree count identical. That is what this refuses.")
    return 1


def main():
    import topic_judgements as TJ
    errs = []
    got = {}

    # ---- corpus census, recomputed rather than read from a report ----------
    import glob
    tally = {s: 0 for s in TJ.SLOTS}
    blocks = 0

    # ⭐ EVERY MEMBER OF THE POPULATION IS COUNTED INTO A NAMED KIND. The first
    # version of this loop carried `if not isinstance(canon, dict): continue`
    # and two more like it. Each was correct and each dropped a corpus member
    # SILENTLY, so a census could shrink without any number looking wrong --
    # the exact "a scan reports where it LOOKED, not the population it claims
    # to cover" failure this file exists to catch, inside the instrument built
    # to catch it. Stated positively, every file lands in exactly one kind and
    # the kinds must sum to files_seen, which is asserted below.
    kind = {"files_seen": 0, "striptest_fixture": 0, "unparseable_json": 0,
            "json_but_not_an_object": 0, "object_without_by_outcome": 0,
            "object_with_by_outcome": 0}
    ok = {"outcome_entries": 0, "pooled_blocks": 0,
          "register_returned": 0, "register_declined": 0}

    for f in sorted(glob.glob(os.path.join(ROOT, "ssot", "*", "*.json"))):
        kind["files_seen"] += 1
        if f.endswith(".striptest"):
            kind["striptest_fixture"] += 1
            continue
        try:
            raw = json.load(open(f, encoding="utf-8"))
        except Exception:
            kind["unparseable_json"] += 1
            continue
        if isinstance(raw, dict):
            canon = raw
        else:
            kind["json_but_not_an_object"] += 1
            continue
        res_map = canon.get("results")
        bo = res_map.get("by_outcome") if isinstance(res_map, dict) else None
        if isinstance(bo, dict):
            kind["object_with_by_outcome"] += 1
        else:
            kind["object_without_by_outcome"] += 1
            continue
        for oid, res in bo.items():
            ok["outcome_entries"] += 1
            if isinstance(res, dict) and res.get("pooled"):
                ok["pooled_blocks"] += 1
            else:
                continue
            reg = TJ.derive(canon, oid)
            if reg:
                ok["register_returned"] += 1
            else:
                # ⚠️ A DECLINE IS REPORTED, NOT SKIPPED. If derive() broke and
                # declined on everything, the old loop would have reported a
                # clean corpus with a zero count.
                ok["register_declined"] += 1
                continue
            blocks += 1
            for e in reg["entries"]:
                if e["state"] == TJ.DECLARED:
                    tally[e["slot"]] += 1

    summed = sum(v for k, v in kind.items() if k != "files_seen")
    if summed != kind["files_seen"]:
        errs.append("the kinds do not sum to the files seen (%d vs %d): a "
                    "corpus member fell through every named kind, which is "
                    "the silent drop this loop was rewritten to prevent."
                    % (summed, kind["files_seen"]))
    got["_kind"] = kind
    got["_ok"] = ok
    got["corpus_files_seen"] = kind["files_seen"]
    got["pooled_blocks"] = ok["pooled_blocks"]

    got["eligibility_declared"] = tally.get("ELIGIBILITY_RULE", -1)
    got["estimand_declared"] = tally.get("ESTIMAND", -1)
    got["question_pico_declared"] = tally.get("QUESTION_PICO", -1)
    got["index_entry_declared"] = tally.get("INDEX_ENTRY", -1)

    # ---- dapivirine, the worked topic -------------------------------------
    dp = os.path.join(ROOT, "ssot", "agyw-hiv-prep-review",
                      "agyw-hiv-prep-review.json")
    canon = json.load(open(dp, encoding="utf-8"))
    reg = TJ.derive(canon, "primary")
    got["dapivirine_declared"] = sum(1 for e in reg["entries"]
                                     if e["state"] == TJ.DECLARED)
    got["dapivirine_proven_authored"] = sum(1 for e in reg["entries"]
                                            if e.get("proven_authored"))

    # ⭐ AND THE ZERO MUST BE ABLE TO MOVE. A tier that reports 0 because it is
    # broken is indistinguishable from one that reports 0 because nothing is
    # annotated. Plant an annotation and require the count to rise.
    import copy
    probe = copy.deepcopy(canon)
    probe["results"]["by_outcome"]["primary"]["question_pico__derived_from"] = {
        "inputs": [], "by": "__control_plant", "authored": True}
    moved = sum(1 for e in TJ.derive(probe, "primary")["entries"]
                if e.get("proven_authored"))
    if moved <= got["dapivirine_proven_authored"]:
        errs.append("PROVEN_AUTHORED does not move under a planted annotation "
                    "(%d -> %d): the tier cannot report anything, so its zero "
                    "means nothing." % (got["dapivirine_proven_authored"], moved))

    # ---- tabs, from the BUILT page ----------------------------------------
    page = os.path.join(ROOT, "AGYW_HIV_PREP_REVIEW.html")
    decl = os.path.join(ROOT, "ssot", "page_format_v1.json")
    if os.path.exists(page) and os.path.exists(decl):
        html = open(page, encoding="utf-8", errors="replace").read()
        body = html.split("</style>", 1)[-1]
        ids = dict(re.findall(r'<label for="rt-([a-z0-9_-]+)">([^<]+)</label>', body))
        req = json.load(open(decl, encoding="utf-8"))["required_tabs"]
        got["tabs_in_build"] = sum(
            1 for t in req
            if str(t.get("panel_id_hint") or "").replace("pn-", "") in ids)
    else:
        got["tabs_in_build"] = -1
        errs.append("cannot count tabs: page or declaration missing")

    print("POST-MERGE INVARIANTS  (%d outcome-blocks measured)" % blocks)
    print()
    print("  POPULATION BY KIND -- every file lands in exactly one, and they sum")
    print("  to files_seen. A rate quoted without these is a reach figure.")
    for k in ("files_seen", "striptest_fixture", "unparseable_json",
              "json_but_not_an_object", "object_without_by_outcome",
              "object_with_by_outcome"):
        print("    %-28s %6d%s" % (k, got["_kind"][k],
              "   <- the denominator" if k == "files_seen" else ""))
    print("  OUTCOME BLOCKS BY KIND, within the %d objects that carry by_outcome:"
          % got["_kind"]["object_with_by_outcome"])
    for k in ("outcome_entries", "pooled_blocks", "register_returned",
              "register_declined"):
        print("    %-28s %6d" % (k, got["_ok"][k]))
    print()
    print("  %-30s %8s %8s" % ("invariant", "expect", "got"))
    for k, (want, why) in EXPECT.items():
        have = got.get(k)
        ok = (have == want)
        print("  %-30s %8s %8s  %s" % (k, want, have, "" if ok else "*** MOVED ***"))
        if not ok:
            errs.append("%s: expected %s, got %s -- %s" % (k, want, have, why))

    if errs:
        return fail(errs)
    print()
    print("ALL INVARIANTS HELD. The merge did not revert a measured correction.")
    print("⚠️ This asserts MEASUREMENTS, not the tree. It cannot see a file that")
    print("   was lost without changing any of these numbers.")
    return 0


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                  errors="replace", line_buffering=True)
    sys.exit(main())
