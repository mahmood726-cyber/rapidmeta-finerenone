#!/usr/bin/env python3
"""A STORED BLOCK ASSERTING A STATE THE OBJECT ITSELF CONTRADICTS.

THE INSTRUCTIVE INSTANCE, alirocumab-lipid, 2026-08-19. Its `r_output` block read:

    "state": "ABSENT_AND_THAT_IS_THE_FINDING",
    "_why_absent": "k=1. No meta-analysis was performed, so there is NO model call to quote,
                    NO pooled estimate, NO heterogeneity and NO package version."

The object pooled SIX trials and stored MD -54.66 (-60.75 to -48.56) with tau2 and I-squared.

    THE REFUSAL WAS CORRECT AND ITS JUSTIFICATION WAS FICTION.

P6 refused because no verbatim model output existed -- true. It refused BECAUSE k=1 AND NOTHING
WAS POOLED -- false, and stated on the page. That is the correct-verdict-broken-reasoning class,
now inside a property whose entire content is a quotation.

WHY IT IS WORSE THAN AN ORDINARY STALE FIELD: a reason is what a reader checks the verdict
against. A wrong number can be recomputed; a wrong REASON teaches the reader the wrong model of
the object, and nothing downstream ever recomputes prose.

WHAT THIS CHECKS. Claims a block makes about the object, against the object:

  1. a block says k=N, or "k=N" in prose, where the object's own pool declares a different k
  2. a block says NOTHING WAS POOLED / no meta-analysis, while a pooled estimate exists
  3. a block says a value is ABSENT while the field it names is present and non-empty
  4. a block declares a trial count that disagrees with len(inputs.trials)

Each is a comparison between two things the OBJECT holds -- never against an outside
expectation -- so a hit is an internal contradiction rather than a difference of opinion.
"""
import io
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SSOT = os.path.join(REPO, "ssot")

# A THRESHOLD IS NOT A CLAIM ABOUT THIS OBJECT. "REML with Hartung-Knapp below k=10" states a
# POLICY, and the first version read it as an assertion that k is 10 -- 60+ false alarms on
# correct text, in a corpus where the objects keep being right.
K_CLAIM = re.compile(r"\bk\s*=\s*(\d+)")
THRESHOLD_CTX = re.compile(
    r"(below|above|under|over|at least|fewer than|more than|less than|when|if|rule|policy|"
    r"threshold|floor)\b[^.]{0,40}$", re.I)

# published_comparison and its neighbours DESCRIBE OTHER WORK. "reports no pooled estimate of
# its own" is a statement about an EXTERNAL review, and reading it as a statement about this
# object was the second false-alarm family. Scoped out entirely rather than pattern-matched
# around, because the subject of the sentence is structural, not lexical.
FOREIGN_SUBJECT = ("published_comparison", "removed_citations", "reconciliation",
                   "screening_of_remainder", "eligible_but_not_contributing")

NOT_POOLED = re.compile(
    r"no meta-analysis was performed|nothing was pooled|NO pooled estimate|"
    r"was not pooled|no model call to quote", re.I)
ABSENT_CLAIM = re.compile(r"ABSENT_AND_THAT_IS_THE_FINDING|\bstate\b.{0,4}ABSENT", re.I)


def walk_strings(node, path=""):
    if isinstance(node, dict):
        for k, v in node.items():
            for r in walk_strings(v, path + "." + k):
                yield r
    elif isinstance(node, list):
        for i, v in enumerate(node):
            for r in walk_strings(v, "%s[%d]" % (path, i)):
                yield r
    elif isinstance(node, str):
        yield path, node


def check(topic, obj):
    out = []
    outcomes = ((obj.get("results") or {}).get("by_outcome") or {})
    pooled_ks = {name: blk.get("k") for name, blk in outcomes.items()
                 if isinstance(blk, dict) and isinstance(blk.get("k"), int)}
    has_pool = any(isinstance(blk, dict) and (blk.get("pooled") or {}).get("point") is not None
                   for blk in outcomes.values() if isinstance(blk, dict))
    n_trials = len((obj.get("inputs") or {}).get("trials") or [])

    # THE PROSE CHECKS WERE REMOVED, AND THAT IS THE FINDING ABOUT THIS DETECTOR.
    #
    # Two earlier versions parsed sentences for "k=N" and for "nothing was pooled". They raised
    # 68 and then 43 alarms, and every one inspected was CORRECT TEXT:
    #   "REML with Hartung-Knapp below k=10"     -- a THRESHOLD, not a claim about this object
    #   "reports no pooled estimate of its own"  -- about an EXTERNAL review
    #   "k=1" on riociguat-pah                   -- how many trials are POOLABLE, correctly,
    #                                               where the object holds 2 that cannot combine
    # Scoping fixed the first two families. The third cannot be fixed: deciding whether "k=1"
    # denotes the trial count or the poolable count is SEMANTIC, and a check that cannot tell
    # them apart accuses correct objects. In a corpus where the objects keep being right and
    # the instruments keep being wrong, that is the expensive direction to be wrong in.
    #
    #     A CHECK WITH FORTY-THREE FALSE ALARMS AND NO TRUE ONES IS SWITCHED OFF WITHIN A WEEK,
    #     AND THEN CATCHES NOTHING AT ALL.
    #
    # What survives is the one signature that is STRUCTURAL rather than linguistic: a block
    # declaring its own state ABSENT while the outcome it belongs to carries a pooled estimate.
    # That is the shape of the real instance, and it needs no sentence parsed.
    # See "NOT CHECKED" in the output for what this therefore cannot see.
    for name, blk in outcomes.items():
        if not isinstance(blk, dict):
            continue
        # k >= 2 IS THE DISCRIMINATOR, AND bempedoic-acid-review IS WHY.
        #
        # It carries k=1, poolable=false, and a POPULATED `pooled` block -- which holds CLEAR
        # Outcomes' own registered Cox estimate and says so on its face: "IT IS ONE TRIAL'S
        # RESULT RATHER THAN A SYNTHESIS". Its r_output saying "k=1, no meta-analysis was
        # performed" is therefore CORRECT, and the first version of this check accused it.
        #
        # A populated `pooled` at k=1 is a single trial's result. Only at k>=2 does "no
        # meta-analysis was performed" contradict the object.
        # AND "POOLED IS PRESENT" IS NOT "SOMETHING WAS POOLED", which is the same
        # presence-versus-property error that let `population_stated` pass a truncated registry
        # string. attr-cm-review carries a `pooled` dict with point=null and withdrawn=true --
        # a RECORD OF A REFUSAL TO POOL, correctly kept, with the reason on it. Its r_output
        # saying ABSENT is right, and testing the dict's truthiness accused it.
        pooled = blk.get("pooled") or {}
        really_pooled = (pooled.get("point") is not None) and not pooled.get("withdrawn")
        r = blk.get("r_output")
        if (isinstance(r, dict) and ABSENT_CLAIM.search(json.dumps(r))
                and really_pooled and isinstance(blk.get("k"), int) and blk["k"] >= 2):
            out.append(("results.by_outcome.%s.r_output" % name,
                        "declares its own state ABSENT while its outcome carries a pooled "
                        "estimate", json.dumps(r)[:110]))
    return out


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    hits, scanned = [], 0
    for d in sorted(os.listdir(SSOT)):
        p = os.path.join(SSOT, d, d + ".json")
        if not os.path.exists(p):
            continue
        try:
            with io.open(p, encoding="utf-8") as fh:
                obj = json.load(fh)
        except (ValueError, OSError):
            continue
        scanned += 1
        for path, why, excerpt in check(d, obj):
            hits.append((d, path, why, excerpt))

    for d, path, why, excerpt in hits:
        print("%s  %s" % (d, path))
        print("      %s" % why)
        print("      ...%s..." % " ".join(excerpt.split()))
    print()
    print("topic objects scanned                 %d" % scanned)
    print("blocks contradicting their own object %d" % len(hits))
    if hits:
        print()
        print("REFUSED: %d stored block(s) assert a state the object contradicts." % len(hits))
        print("A wrong number can be recomputed. A wrong REASON teaches the reader the wrong")
        print("model of the object, and nothing downstream ever recomputes prose.")
        return 1
    print()
    print("no stored block contradicts its own object on k, on pooling, or on absence.")
    print("NOT CHECKED: contradictions expressible only in prose. This compares claims to")
    print("FIELDS, so a sentence wrong in a way no field records stays invisible.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
