#!/usr/bin/env python3
"""A REVIEW'S QUESTION MUST NOT BE ONE OF ITS TRIALS' REGISTRY FIELDS.

FOUND ON `ablation-af-review`, 2026-08-19, before a single build step ran. Its `question` was:

    "Number of Participants With Composite of Total Mortality, Disabling Stroke, Serious
     Bleeding, or Cardiac Arrest in Patie"

That is CABANA's (NCT00911508) registered PRIMARY OUTCOME MEASURE, **truncated at exactly 120
characters**, mid-word. So the review's stated question was one of its four trials' endpoints,
cut short -- and `population_stated` returned PASS on it.

TWO DEFECTS AT ONCE, and they compound:

  1. A REGISTRY FIELD MASQUERADING AS A REVIEW QUESTION. A question about participants was
     answered with a sentence about an outcome, belonging to ONE of four trials.
  2. SILENT TRUNCATION AT A FIXED WIDTH. Named as a missing class by an outside critic (agy,
     Gemini 3.1 Pro) minutes before it was found here -- which is the argument for asking a
     different model family what you are not looking for.

WHY THE PRECONDITION PASSED IT, which is the part worth fixing rather than deploring:
`population_stated` reads `question` and judges PRESENCE. It cannot tell a review question from
any other non-empty string.

    THE PROPERTY CLAIMED IS "POPULATION STATED". THE PROPERTY VERIFIED IS "FIELD NON-EMPTY".
    Every check in this repo should be read against that gap.

This does not make `population_stated` wrong to exist -- its own docstring already says a PASS
is not a claim the population is homogeneous. It makes it INSUFFICIENT ALONE, and this is the
companion check.

WHAT THIS CHECKS. For every topic, compare `question` against the registry text of its OWN
included trials -- primary and secondary outcome measures, brief and official titles. A match,
or a prefix match of >= 60 characters (which is how truncation presents), means the question is
a COPIED FIELD rather than a stated question.

Closed vocabulary again: it compares only against text the registry published for THIS object's
OWN trials. It does not attempt to judge whether a genuine question is a GOOD question -- that
is human judgement and is not claimed here.
"""
import io
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SSOT = os.path.join(REPO, "ssot")
CACHE = os.environ.get(
    "RM_CTGOV_CACHE",
    "F:/claude-temp/claude/F--rapidmeta-ssot-shell/"
    "eb4d84e5-8a24-4c3b-afe2-34bd91c20bc7/scratchpad/.ctgov-raw-cache")

# A RATCHET, NOT A ZERO-GATE, AND THE REASON IS STATED. Two topics currently fail, and fixing
# either needs a JUDGEMENT about what the review asks -- see BLOCKED-ablation-af-review. A
# zero-gate would block every unrelated commit until a human answers that, which is how a check
# gets switched off. A permanent non-blocking NOTE is the other failure mode: it can only warn,
# never block, which is verification theatre. So: the known set is baselined and ANY INCREASE
# REFUSES.
BASELINE = 2

PREFIX_MIN = 60           # a shared opening this long is a copy, not a coincidence
WS = re.compile(r"\s+")


def norm(s):
    return WS.sub(" ", str(s or "")).strip().lower()


def registry_texts(nct):
    """Every string from a registration that a question could have been copied from."""
    if not os.path.isdir(CACHE):
        return []
    for fn in os.listdir(CACHE):
        if fn.startswith(nct + "_") and fn.endswith(".json"):
            try:
                with io.open(os.path.join(CACHE, fn), encoding="utf-8") as fh:
                    rec = json.load(fh)
            except (ValueError, OSError):
                return []
            ps = rec.get("protocolSection") or {}
            out = []
            om = ps.get("outcomesModule") or {}
            for key in ("primaryOutcomes", "secondaryOutcomes"):
                for o in (om.get(key) or []):
                    if o.get("measure"):
                        out.append(("%s.%s.measure" % ("outcomesModule", key), o["measure"]))
            idm = ps.get("identificationModule") or {}
            for k in ("briefTitle", "officialTitle"):
                if idm.get(k):
                    out.append(("identificationModule." + k, idm[k]))
            return out
    return []


def check_topic(topic):
    p = os.path.join(SSOT, topic, topic + ".json")
    try:
        with io.open(p, encoding="utf-8") as fh:
            obj = json.load(fh)
    except (ValueError, OSError):
        return None, "unreadable"
    # FOUR FIELDS, NOT ONE. On ablation-af-review the same truncated registry string sat in
    # question, title, outcomes[0].name AND outcomes[0].definition -- the object's whole
    # identity was one trial's outcome measure. Checking only `question` would have found a
    # quarter of the defect and reported it fixed.
    fields = [("question", obj.get("question")), ("title", obj.get("title"))]
    for i, o_ in enumerate((obj.get("outcomes") or [])[:6]):
        if isinstance(o_, dict):
            fields.append(("outcomes[%d].name" % i, o_.get("name")))
            fields.append(("outcomes[%d].definition" % i, o_.get("definition")))
    fields = [(k, v) for k, v in fields if norm(v)]
    if not fields:
        return None, "no question/title/outcome text"
    trials = [t.get("nct") for t in ((obj.get("inputs") or {}).get("trials") or [])
              if t.get("nct")]
    if not trials:
        return None, "no trials with registration ids"
    looked = 0
    for nct in trials:
        texts = registry_texts(nct)
        if not texts:
            continue
        looked += 1
        for path, raw in texts:
            r = norm(raw)
            if not r:
                continue
            for fname, fval in fields:
                q = norm(fval)
                if q == r:
                    # AN OUTCOME DEFINITION QUOTING THE REGISTRY EXACTLY IS CORRECT -- that is
                    # where a definition SHOULD come from, and bempedoic-acid-review does it
                    # properly. Only a QUESTION or TITLE is wrong to be a trial's field: a
                    # review question is not one trial's endpoint. Flagging the exact quote
                    # would have accused a correct object, which is the defect this repo keeps
                    # catching in its own instruments.
                    if fname in ("question", "title"):
                        return (nct, path, "EXACT", raw, fname), None
                    continue
                if (min(len(q), len(r)) >= PREFIX_MIN
                        and q[:PREFIX_MIN] == r[:PREFIX_MIN]):
                    return (nct, path, "TRUNCATED at %d chars" % len(str(fval)),
                            raw, fname), None
    if looked == 0:
        return None, "no registration records cached for this topic's trials"
    return None, None


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    hits, checked, unchecked = [], 0, []
    for topic in sorted(os.listdir(SSOT)):
        if not os.path.exists(os.path.join(SSOT, topic, topic + ".json")):
            continue
        hit, why = check_topic(topic)
        if hit:
            hits.append((topic,) + hit)
            checked += 1
        elif why:
            unchecked.append((topic, why))
        else:
            checked += 1

    for topic, nct, path, kind, raw, fname in hits:
        print("%s" % topic)
        print("   `%s` is %s's own registry text -- %s" % (fname, nct, kind))
        print("   source field : %s" % path)
        print("   registry says: %s" % (" ".join(str(raw).split())[:110]))
        print()
    print("topics compared against their own trials' registry text   %d" % checked)
    print("questions that are a COPIED REGISTRY FIELD                %d" % len(hits))
    print("not compared (reported, never silently skipped)           %d" % len(unchecked))
    print("baseline (known, awaiting a human decision)              %d" % BASELINE)
    if len(hits) > BASELINE:
        print()
        print("REFUSED: %d topic(s) answer 'what is the question' with a registry field, "
              "above the baseline of %d." % (len(hits), BASELINE))
        print("FIX: state the review's own question. If it is derived from the object's recorded")
        print("     fields rather than pre-specified, say so on its face -- see")
        print("     bempedoic-acid-review, whose criteria block carries `predefined: false`.")
        return 1
    if hits:
        print()
        print("HELD at baseline: %d known topic(s), each blocked on a human decision about what "
              "the review asks. Listed above, not hidden. Any NEW one refuses." % len(hits))
        return 0
    print()
    print("no topic's question is a copy of its own trials' registry text.")
    print("NOT CHECKED, and named: whether a genuine question is a GOOD question. That is human")
    print("judgement and is not claimed here.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
