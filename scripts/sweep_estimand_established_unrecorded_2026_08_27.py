#!/usr/bin/env python3
"""HOW MANY POOLS CAN WE CALL LIKE-FOR-LIKE. The honest bound.

`estimand_established: True` asserts that every contributing trial measures the same
quantity. On `incretin-hfpef-review/kccq_css_change` it asserted that while the object
contained ZERO occurrences of "treatment policy", "trial product", "efficacy estimand" or
"on-treatment". It asserted sameness along an axis it did not record.

    IT HAPPENED TO BE TRUE. Nothing in the object made it true, and nothing would have
    caught it had it been false.

Measured on that one outcome, the axis carries a 20% effect: the three trials' own
on-treatment alternatives (8.8, 9.8, 8.6) pool to about 9.0 against our 7.38, with every
individual number remaining quotable and correct.

THREE POPULATIONS, COUNTED SEPARATELY, because collapsing them is how a reassuring number
gets made:

    A  outcomes asserting `estimand_established: True`
    B  of those, how many RECORD an estimand anywhere
    C  of those, how many ACTUALLY POOL -- k>=2 with a pooled point

C is the one that matters. An unrecorded estimand on an outcome that pools nothing is a
documentation gap. An unrecorded estimand on a pool is a claim that the pool is like-for-like
with nothing behind it.

VOCABULARY, NOT A SINGLE SPELLING. The corpus proved on this very outcome that one strategy
carries three labels -- "treatment policy", "treatment-regimen", and the on-treatment
contrasts "trial product" and "efficacy estimand". A sweep keyed to one phrase would report a
comfortable number and be wrong, which is the defect this project has produced five times in
one night. The structured `estimand_axis` block counts too, and is counted separately from
prose mentions so the two are never conflated.
"""
import io
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SSOT = os.path.join(REPO, "ssot")

# Every wording seen in this corpus or in the ICH E9(R1) literature it cites. Deliberately
# broad: a FALSE POSITIVE here understates the problem, which is the direction that flatters
# us, so the list errs toward finding an estimand rather than missing one.
VOCAB = re.compile(
    r"(treatment[- ]policy|treatment[- ]regimen|trial[- ]product|efficacy estimand|"
    r"on[- ]treatment|per[- ]protocol|intention[- ]to[- ]treat|intent[- ]to[- ]treat|"
    r"\bITT\b|as[- ]treated|hypothetical estimand|while[- ]on[- ]treatment|"
    r"composite estimand|principal stratum|in[- ]trial period|estimand strategy)", re.I)


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    total_outcomes = 0
    asserted = []        # A
    recorded_struct = [] # B, structured
    recorded_prose = []  # B, prose only
    unrecorded = []
    for t in sorted(os.listdir(SSOT)):
        p = os.path.join(SSOT, t, t + ".json")
        if not os.path.isdir(os.path.join(SSOT, t)) or not os.path.exists(p):
            continue
        with io.open(p, encoding="utf-8") as fh:
            obj = json.load(fh)
        for oid, b in ((obj.get("results") or {}).get("by_outcome") or {}).items():
            if not isinstance(b, dict):
                continue
            total_outcomes += 1
            if b.get("estimand_established") is not True:
                continue
            rows = b.get("per_trial") or []
            pooled = (b.get("pooled") or {})
            pools = (pooled.get("point") is not None) and (int(b.get("k") or 0) >= 2)
            struct = sum(1 for r in rows if isinstance(r, dict) and r.get("estimand_axis"))
            blob = json.dumps(b)
            prose = bool(VOCAB.search(blob))
            rec = {"topic": t, "outcome": oid, "k": b.get("k"), "pools": pools,
                   "rows": len(rows), "rows_with_estimand_axis": struct,
                   "prose_mentions_an_estimand": prose}
            asserted.append(rec)
            if struct:
                recorded_struct.append(rec)
            elif prose:
                recorded_prose.append(rec)
            else:
                unrecorded.append(rec)

    unrec_pooling = [r for r in unrecorded if r["pools"]]
    print("OUTCOME BLOCKS IN THE CORPUS: %d" % total_outcomes)
    print()
    print("A  assert `estimand_established: True`            %4d" % len(asserted))
    print("B  of those, record the estimand STRUCTURALLY     %4d" % len(recorded_struct))
    print("   of those, mention one only in PROSE            %4d" % len(recorded_prose))
    print("   of those, record NOTHING                       %4d" % len(unrecorded))
    print()
    print("C  THE ONE THAT MATTERS -- assert sameness, record nothing, AND POOL:")
    print("       %d of %d outcomes that assert it" % (len(unrec_pooling), len(asserted)))
    print("       across %d topic(s)" % len({r["topic"] for r in unrec_pooling}))
    print()
    if unrec_pooling:
        print("%-34s %-24s %-4s %s" % ("topic", "outcome", "k", "rows"))
        for r in sorted(unrec_pooling, key=lambda x: (x["topic"], x["outcome"])):
            print("%-34s %-24s %-4s %d" % (r["topic"][:34], r["outcome"][:24],
                                           r["k"], r["rows"]))
    print()
    print("PROSE-ONLY IS NOT RECORDED. A block whose text happens to contain 'intention to "
          "treat' somewhere has not recorded WHICH ESTIMAND EACH CONTRIBUTING TRIAL USED, "
          "which is the thing sameness is asserted about. They are listed separately rather "
          "than counted as compliant.")
    dest = os.path.join(REPO, "outputs", "estimand_established_sweep_2026_08_27.json")
    if not os.path.isdir(os.path.dirname(dest)):
        os.makedirs(os.path.dirname(dest))
    with io.open(dest, "w", encoding="utf-8") as fh:
        fh.write(json.dumps({"total_outcomes": total_outcomes,
                             "asserted": asserted,
                             "recorded_structurally": recorded_struct,
                             "prose_only": recorded_prose,
                             "unrecorded": unrecorded,
                             "unrecorded_and_pooling": unrec_pooling,
                             "DONE": True}, indent=1))
    print("wrote %s" % dest)
    return 0


if __name__ == "__main__":
    sys.exit(main())
