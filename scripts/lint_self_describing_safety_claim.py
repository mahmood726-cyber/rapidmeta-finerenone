"""Find object fields whose PROSE asserts that a defect would be visible.

REGISTRY CLASS: A FIELD'S OWN PROSE NAMING ITS OWN DEFENCE, WHERE THE DEFENCE DOES NOT
EXIST.

This is distinct from an undefended claim. An undefended claim simply has no check behind
it and nobody said otherwise. THIS one names the check. It says, in the object a reader
trusts, that a particular failure "would show as a mismatch", "would be caught", "cannot
happen because" -- and a reader who meets that sentence stops looking, which is exactly
what it was written to let them do.

THE FOUNDING INSTANCE, 2026-08-20. Every `registration_primary_counts` block in this
corpus carries:

    "arm order as the registry lists it; a swapped pair would show as a mismatch rather
     than a silent pass"

It was written by whoever built the block. It was plausible. It was FALSE FOR THE ENTIRE
LIFE OF THE FIELD, because nothing in this repository ever compared that block against
`arms[]`. When a lint was finally written to make it true, it found 23 inconsistent rows
across 75 -- on two of which the block, read as labelled, said the drug was WORSE than
placebo while the effect beside it said the opposite.

THE DIRECTION IS WORTH RECORDING. This one biases toward MANUFACTURING a contradiction
rather than hiding one: a reader who did the check the sentence promised would have
concluded the ESTIMATE was wrong, when the estimate was right and the label was wrong.
That is the second instance of the rarer direction in two days -- the first being the
arm-role precondition on 2026-08-19 -- and the third followed within the hour, when THIS
FILE'S SIBLING lint manufactured four false alarms of its own by comparing an odds ratio
against a stored hazard ratio.

WHAT THIS FILE DOES. It reports every such sentence with its path, and it CANNOT decide
whether a command tests any of them -- that requires knowing what every script does. It is
a REPORTER with a ratchet, not a verifier, and it says so rather than printing PASS. The
list is the work item; each sentence is either backed by a named command or it is this
class.
"""
import io
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SSOT = os.path.join(REPO, "ssot")

# Phrases that promise a defect would be visible. Deliberately narrow: each asserts a
# DETECTION property, not merely a fact.
PATTERNS = [
    r"would show as", r"would be caught", r"would surface", r"would be visible",
    r"would fail\b", r"would refuse", r"cannot happen because", r"could not happen",
    r"rather than a silent pass", r"would not go unnoticed", r"would be detected",
    r"is guaranteed", r"guarantees that", r"ensures that no", r"makes it impossible",
]
RE = re.compile("|".join(PATTERNS), re.I)


def leaves(o, p=""):
    if isinstance(o, dict):
        for k, v in o.items():
            yield from leaves(v, p + "." + k)
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from leaves(v, p + "[%d]" % i)
    else:
        yield p, o


def main():
    objects_read = 0
    hits = []
    for name in sorted(os.listdir(SSOT)):
        d = os.path.join(SSOT, name)
        if not os.path.isdir(d):
            continue
        fp = os.path.join(d, name + ".json")
        if not os.path.exists(fp):
            continue
        try:
            obj = json.load(io.open(fp, encoding="utf-8"))
        except Exception:
            continue
        objects_read += 1
        for path, val in leaves(obj):
            if isinstance(val, str) and RE.search(val):
                m = RE.search(val)
                hits.append((name, re.sub(r"\[\d+\]", "[]", path), m.group(0),
                             val[max(0, m.start() - 70):m.end() + 90].replace("\n", " ")))

    if objects_read == 0:
        print("NOT_ASSESSABLE: read zero objects.")
        return 2

    # Group by the (path-shape, phrase) pair -- one sentence repeated across 75 trial rows
    # is ONE claim, not 75, and counting it 75 times would misdescribe the work.
    groups = {}
    for name, path, phrase, ctx in hits:
        groups.setdefault((path, phrase), {"objects": set(), "example": ctx})
        groups[(path, phrase)]["objects"].add(name)

    print("objects read                                  %d" % objects_read)
    print("field values asserting their own detection    %d" % len(hits))
    print("DISTINCT CLAIMS (path-shape x phrase)         %d" % len(groups))
    print()
    print("A claim repeated across many rows is ONE claim. The 23-row founding instance is")
    print("a single sentence on a single field shape, and counting it once is the honest")
    print("unit of work.")
    print()
    print("%-52s %-26s %6s  %s" % ("path shape", "phrase", "objs", "example"))
    print("-" * 160)
    for (path, phrase), g in sorted(groups.items(), key=lambda kv: -len(kv[1]["objects"])):
        print("%-52s %-26s %6d  %s" % (path[:52], phrase[:26], len(g["objects"]),
                                       g["example"][:70]))

    baseline_path = os.path.join(REPO, "evidence", "self_describing_safety_baseline.json")
    if "--baseline" in sys.argv:
        with io.open(baseline_path, "w", encoding="utf-8", newline="\n") as fh:
            json.dump({"measured_utc": "2026-08-20", "distinct_claims": len(groups),
                       "field_values": len(hits), "objects_read": objects_read,
                       "measured_by": os.path.basename(__file__),
                       "_what_a_pass_means": (
                           "That no NEW self-describing safety sentence appeared. It does "
                           "NOT mean the existing ones are backed by a command -- this file "
                           "cannot know that, and says so rather than printing PASS.")}, fh,
                      indent=1)
            fh.write("\n")
        print("\nbaseline written: %d distinct claim(s)" % len(groups))
        return 0
    if not os.path.exists(baseline_path):
        print("\nNOT_ASSESSABLE: no baseline. Run with --baseline.")
        return 2
    base = json.load(io.open(baseline_path, encoding="utf-8"))["distinct_claims"]
    if len(groups) > base:
        print("\nREFUSED: %d distinct self-describing safety claims, up from %d. Each new "
              "one must name the command that makes it true, or it is a sentence promising "
              "a check that nothing performs." % (len(groups), base))
        return 1
    print("\nREPORTED, NOT PASSED: %d distinct claims against a baseline of %d, none new. "
          "THIS FILE CANNOT TELL WHETHER ANY OF THEM IS BACKED BY A COMMAND -- that is the "
          "work item, and the founding instance was false for the entire life of its field."
          % (len(groups), base))
    return 0


if __name__ == "__main__":
    sys.exit(main())
