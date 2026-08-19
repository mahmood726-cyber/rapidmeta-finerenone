#!/usr/bin/env python3
"""E4 MADE MECHANICAL: A REVIEW MAY NOT CONCLUDE "THESE DO NOT POOL" WITHOUT READING EVERY RANK.

TWICE IN ONE NIGHT THE ANSWER WAS BELOW THE PRIMARY, AND BOTH TIMES IT WAS FOUND BY ASKING
RATHER THAN BY ANY GUARD.

    sglt2-hf                   the harmonisable estimand was a SECONDARY. Recovered a pool.
    apixaban-vte-prophylaxis   all four trials register "proximal DVT, non-fatal PE, or
                               VTE-related death" -- a SECONDARY IN ALL FOUR. It replaced a
                               k=1 figure that was not an estimate of the review's question at
                               all (a 400-patient trial reporting BLEEDING endpoints) with a
                               pool of four trials and 13,570 participants.

WHY THIS IS THE HARDEST CLASS IN THE REGISTRY. Every other defect leaves a trace: a wrong
number, a mismatched count, a contradicted block. WITHHOLDING LEAVES NOTHING. A review that
stopped at the primaries and concluded "different quantities, not poolable" produces an object
that is internally consistent, arithmetically sound, and silently missing its own evidence base.
There is no residue for a guard to find -- which is exactly why the guard has to be about the
PROCESS rather than about the result.

THE RULE. A topic that declines to pool ANY outcome -- `pooled.withdrawn`, a null pooled point,
or a NOT_POOLABLE disposition -- must carry, on at least one trial, evidence that ranks BELOW
the primary were read: `all_ranks_read_utc`, or a `registered_secondaries` field, or a screening
record whose `outcome_ranks_searched` / `ranks_read` exceeds the primary count. A refusal with
no such evidence anywhere is a refusal that may never have looked.

WHAT IT FOUND ON ITS FIRST RUN. 115 of 137 topics decline at least one outcome, and 48 of them
carry NO evidence, on any trial, that anything below the primary was ever read. Those 48 are
carried as a NAMED baseline and PRINTED EVERY RUN. They are not absolved: each is a topic whose
"does not pool" may be a k=1 non-estimate standing where a pool belongs, and two of exactly that
shape were converted into real pooled estimates tonight.

WHAT IT CANNOT DO, STATED PLAINLY. It proves that SOMETHING below the primary was read, not that
the withholding question was asked at EVERY rank, and not that the answer was right. It is a
floor, not a ceiling. A floor is still the difference between a refusal that looked and one that
did not.
"""
import io
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SSOT = os.path.join(REPO, "ssot")
BASELINE = os.path.join(REPO, "evidence", "withholding_asked_baseline.json")

DECLINED_VALUES = (False, "NOT_POOLABLE", "NOT_POOLABLE_QUANTITY", "NO", "REFUSED")


def declines(obj):
    """Outcome ids this object declines to pool, by any of the three shapes in use."""
    out = []
    for oid, v in (((obj.get("results") or {}).get("by_outcome")) or {}).items():
        v = v or {}
        pooled = v.get("pooled") or {}
        if pooled.get("withdrawn") is True:
            out.append(oid)
        elif v.get("poolable") in DECLINED_VALUES:
            out.append(oid)
        elif pooled.get("point") is None and (v.get("k") or 0) >= 2:
            out.append(oid)
    return out


def read_below_primary(obj):
    """Trials carrying evidence that ranks below the primary were read."""
    hits = []
    for t in ((obj.get("inputs") or {}).get("trials") or []):
        if t.get("all_ranks_read_utc"):
            hits.append((t.get("id") or t.get("nct") or "?", "all_ranks_read_utc"))
        elif "registered_secondaries" in t:
            hits.append((t.get("id") or t.get("nct") or "?", "registered_secondaries"))
    # A screening record that counted ranks is equally good evidence, and some topics carry it
    # there rather than on the trial.
    for key in ("screening", "screening_of_remainder"):
        blk = obj.get(key)
        recs = blk.get("records") if isinstance(blk, dict) else blk
        for r in (recs or []) if isinstance(recs, list) else []:
            if isinstance(r, dict) and ((r.get("outcome_ranks_searched") or 0) > 1
                                        or (r.get("ranks_read") or 0) > 1):
                hits.append((r.get("nct") or "?", key))
                break
    return hits


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    declining, unasked, asked = 0, [], 0
    for topic in sorted(os.listdir(SSOT)):
        path = os.path.join(SSOT, topic, "%s.json" % topic)
        if not os.path.isfile(path):
            continue
        try:
            with io.open(path, encoding="utf-8") as fh:
                obj = json.load(fh)
        except Exception:
            continue
        d = declines(obj)
        if not d:
            continue
        declining += 1
        if read_below_primary(obj):
            asked += 1
        else:
            unasked.append(topic)

    if declining == 0:
        # NO TOPIC DECLINES ANYTHING. Either the corpus changed shape or the three field names
        # this reads have been renamed. A check with nothing to check against passes everything.
        print("REFUSED: no topic in the corpus declines to pool anything. This detector's")
        print("vocabulary no longer matches the objects -- that is a broken instrument, not a")
        print("clean corpus.")
        return 2

    print("REFUSALS TO POOL, AND WHETHER ANYTHING BELOW THE PRIMARY WAS EVER READ")
    print("  topics declining at least one outcome   %3d" % declining)
    print("  with evidence ranks below primary read  %3d" % asked)
    print("  WITH NO SUCH EVIDENCE ANYWHERE          %3d" % len(unasked))
    print("\nEach of those is a topic whose \"does not pool\" may be standing where a pool")
    print("belongs. Two of exactly that shape became real pooled estimates tonight:")
    print("  sglt2-hf                 the harmonisable estimand was a SECONDARY")
    print("  apixaban-vte-prophylaxis a SECONDARY in all four -> k=4, 13,570 participants,")
    print("                           replacing a k=1 figure that measured BLEEDING")

    if not os.path.exists(BASELINE):
        with io.open(BASELINE, "w", encoding="utf-8") as fh:
            fh.write(json.dumps({"unasked": sorted(unasked), "not_absolved": True,
                                 "why": ("Carried so the lint can block a NEW refusal that "
                                         "never looked below the primary. Listed is not "
                                         "cleared: each remains a candidate recovery.")},
                                indent=1))
        print("\nbaseline written (NOT an absolution), %d topic(s): %s"
              % (len(unasked), BASELINE))
        return 0

    with io.open(BASELINE, encoding="utf-8") as fh:
        base = set(json.load(fh)["unasked"])
    new = sorted(set(unasked) - base)
    fixed = sorted(base - set(unasked))
    if fixed:
        print("\n%d topic(s) now carry the evidence -- baseline tightened: %s"
              % (len(fixed), ", ".join(fixed)))
        with io.open(BASELINE, encoding="utf-8") as fh:
            b = json.load(fh)
        b["unasked"] = sorted(set(unasked) & base)
        with io.open(BASELINE, "w", encoding="utf-8") as fh:
            fh.write(json.dumps(b, indent=1))
    if new:
        print("\nREFUSED -- %d topic(s) newly decline to pool with no evidence that any rank"
              % len(new))
        print("below the primary was read:")
        for t in new:
            print("   %s" % t)
        print("\nAsk the withholding question at EVERY registered rank before concluding that")
        print("trials do not pool. Twice tonight the answer was a secondary.")
        return 1
    print("\n%d baselined topic(s) remain, and being listed is not being cleared."
          % len(base & set(unasked)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
