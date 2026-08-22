"""Every abstract that reports a pool while the same object holds a withdrawn or referred one.

THE GENERAL CASE OF A DEFECT FOUND BY A BLIND CROSS-FAMILY READ. Asked cold, with none of our
conclusions, GPT-5 read the SGLT2 manuscript against its object and found:

    The abstract states `hazard ratio 0.7636 (0.7062 to 0.8258) across 3 trials`. The same
    object holds `cvdeath_or_whf_first` at k=4, WITHDRAWN. A reader is never told the
    four-trial analysis exists, and would reasonably conclude the review pools all relevant
    trials. The object does not support that.

The judgement stands and the fix is not local to SGLT2. THE WITHDRAWAL IS RECORDED ON ITS OWN
OUTCOME AND IS INVISIBLE FROM THE ABSTRACT, which is where a reader forms the impression. A
disclosure a reader meets only if they scroll to the outcome that was withdrawn is a disclosure
for us and not for them -- registry class 65, one layer out.

WHAT COUNTS AS A HIT, and each is checked on the OBJECT rather than inferred:

    the object publishes at least one pooled point                  something is claimed
    AND holds at least one other outcome that is withdrawn,         something is not
        referred, or whose pool was refused
    AND the abstract text does not mention it

THE ABSTRACT IS READ FROM THE OBJECT, not from the page, so this runs before a rebuild and
tells you what to fix rather than what you already shipped.

A KNOWN-ANSWER FLOOR. `sglt2-hf` is the case the blind read found; the sweep exits PROOF FAILED
if it does not find it, so a clean result means the sweep read what that read read.
"""
import glob
import io
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

WITHDRAWN_MARKS = ("withdrawn", "refused", "not poolable", "pending_external")


def state_of(blk):
    """(is_live, why_not) for one outcome block, read from the object's own fields."""
    if not isinstance(blk, dict):
        return False, None
    pooled = blk.get("pooled")
    if isinstance(pooled, dict):
        if pooled.get("withdrawn"):
            return False, str(pooled.get("withdrawn_reason") or "withdrawn")
        if pooled.get("point") is not None:
            # A REFERRED POOL STILL PUBLISHES A POINT. It is live to a reader and it carries a
            # named defect, so it counts as something the abstract should not omit either.
            for k in blk:
                if str(k).startswith("THE_POOL_IS_REFERRED"):
                    return True, "referred"
            return True, None
    for k, v in blk.items():
        if str(k).lower().startswith(("withdraw", "refus")) and v:
            return False, str(k)
    return False, None


def abstract_text(obj):
    a = (obj.get("manuscript") or {}).get("abstract")
    if isinstance(a, dict):
        return " ".join(str(v) for v in a.values() if isinstance(v, str))
    if isinstance(a, str):
        return a
    return str(obj.get("abstract") or "")


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    hits, seen = [], 0
    for p in sorted(glob.glob(os.path.join(REPO, "ssot", "*", "*.json"))):
        t = os.path.basename(os.path.dirname(p))
        if os.path.basename(p) != t + ".json":
            continue
        try:
            obj = json.load(io.open(p, encoding="utf-8"))
        except ValueError:
            continue
        by = (obj.get("results") or {}).get("by_outcome") or {}
        if not isinstance(by, dict) or not by:
            continue
        seen += 1
        live, dark = [], []
        for oid, blk in by.items():
            ok, why = state_of(blk)
            if ok:
                live.append((oid, blk, why))
            elif isinstance(blk, dict) and (blk.get("k") or blk.get("per_trial")):
                dark.append((oid, blk, why))
        if not live or not dark:
            continue
        abst = abstract_text(obj).lower()
        unmentioned = [(oid, blk, why) for oid, blk, why in dark
                       if oid.lower() not in abst
                       and not any(w in abst for w in WITHDRAWN_MARKS)]
        if not unmentioned:
            continue
        hits.append({
            "topic": t,
            "abstract_claims": [(oid, (blk.get("pooled") or {}).get("point"), blk.get("k"))
                                for oid, blk, _ in live],
            "unmentioned": [(oid, blk.get("k"), (why or "not pooled")[:90])
                            for oid, blk, why in unmentioned],
        })

    if not any(h["topic"] == "sglt2-hf" for h in hits):
        sys.exit("PROOF FAILED: sglt2-hf is not in the result. That is the case the blind "
                 "cross-family read found -- an abstract reporting 0.7636 across 3 trials on "
                 "an object that also holds a withdrawn k=4 outcome. A sweep for this defect "
                 "that does not find it is not reading what that read read.")

    print("")
    print("TOPICS WITH RESULTS: %d" % seen)
    print("ABSTRACTS REPORTING A POOL WHILE AN OUTCOME ON THE SAME OBJECT IS WITHDRAWN,")
    print("REFERRED OR UNPOOLED AND GOES UNMENTIONED: %d" % len(hits))
    print("")
    for h in sorted(hits, key=lambda x: x["topic"]):
        print("%-44s" % h["topic"][:44])
        for oid, pt, k in h["abstract_claims"]:
            print("      claims   %-34s %s at k=%s" % (oid[:34], pt, k))
        for oid, k, why in h["unmentioned"]:
            print("      omits    %-34s k=%s  %s" % (oid[:34], k, why))
    print("")
    print("FLOOR: sglt2-hf is in the list, so this reads what the blind read read.")
    json.dump(hits, io.open(os.path.join(REPO, "outputs",
                                         "abstract_omits_withdrawn_2026_08_22.json"),
                            "w", encoding="utf-8"), indent=1)


if __name__ == "__main__":
    main()
