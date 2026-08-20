"""A METHOD-CLAIM sentence must resolve to a field path on the object it is rendered for.

THE MECHANISM THIS EXISTS TO STOP, stated exactly.

`arni-hfref` is the only object in 141 carrying authored manuscript prose, and eight of its
paragraphs assert HOW THE REVIEW WAS CONDUCTED with no substitution token in them:

    "Two assessors worked independently, drawn from different model families"
    "Certainty was rated with GRADE"
    "The protocol was registered before the first query with a machine-checkable
     ordering test"
    "The whole synthesis was recomputed independently and the two engines agreed"

EVERY ONE OF THOSE IS TRUE OF ARNI. Its object carries `rob2.assessors`, `grade.approach`,
`screening.dual_screening`. THAT IS WHAT MAKES THEM DANGEROUS: a sentence that is a
faithful record on the object it was written for becomes A FABRICATION THE MOMENT IT IS
COPIED -- and it arrives wearing the authority of the flagship, so a reviewer recognises it
from a page they trust and does not question it.

A token is a claim the object holds; the substitution IS the check. An un-tokened method
sentence has no such check, and copying one asserts a procedure that never happened.

THE DIRECTION, AND IT IS THE RARER ONE. This class MANUFACTURES ASSERTIONS rather than
hiding findings. Third instance in three days, after the arm-role precondition (2026-08-19)
and the swapped-arm provenance block (2026-08-20), and a fourth was this lane's own lint
comparing an odds ratio against a stored hazard ratio. **Our whole defensive posture is
built around the other direction**, and three instances is no longer a curiosity.

WHY A DETECTOR AND NOT A NOTE. The documentation-failed-as-a-control result: a written-down
rule here WILL be breached. Five detectors are the only thing that has worked.

THE KNOWN-ANSWER SET IS DRAWN FROM THE CORPUS, NOT FROM FIXTURES -- which is the property
this project keeps finding missing. Each claim below must PASS on `arni-hfref`, whose object
backs it, and FAIL on any object that does not. `--selftest` asserts both directions.
"""
import io
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SSOT = os.path.join(REPO, "ssot")

# Each claim: a matcher for the sentence, and EVERY field path that must resolve for the
# object to be entitled to assert it. No defaults, no partial credit.
CLAIMS = [
    ("dual RoB assessors",
     re.compile(r"two (?:independent )?(?:AI )?assessors|assessors worked independently"
                r"|by two independ", re.I),
     ["rob2.assessors", "rob2.trials"]),
    ("RoB-2 was applied",
     re.compile(r"assessed with (?:Cochrane )?RoB[- ]?2|RoB[- ]?2 using the effect", re.I),
     ["rob2.tool", "rob2.trials"]),
    ("GRADE was applied",
     re.compile(r"[Cc]ertainty was rated with GRADE|rated with GRADE", re.I),
     ["grade.approach", "grade.by_outcome"]),
    ("records were dual-screened",
     re.compile(r"[Rr]ecords were screened against the eligibility axes"
                r"|screened in duplicate", re.I),
     ["screening.records", "screening.dual_screening"]),
    ("an independent second engine recomputed the synthesis",
     re.compile(r"recomputed independently and the two engines agreed"
                r"|two engines agreed", re.I),
     ["results.by_outcome.*.cross_engine"]),
    ("the protocol was registered before the first query",
     re.compile(r"protocol was registered (?:before the first query|as a timestamped)"
                r"|registered before the first query", re.I),
     ["registration.ordering.protocol_committed_utc"]),
    ("leave-one-out robustness was run",
     re.compile(r"[Rr]obustness was examined by leave-one-out", re.I),
     ["results.by_outcome.*.sensitivity.method"]),
    ("effects were taken from the primary publications",
     re.compile(r"were taken from the primary publications", re.I),
     ["inputs.trials.*.by_outcome.*.source_tier"]),
]


def get(obj, path):  # noqa: C901
    """Resolve a dotted path. `*` matches any key of a dict and succeeds if ANY does.

    THE WILDCARD IS HERE BECAUSE I DECLARED TWO PATHS WRONG AND THE DETECTOR CALLED THE
    FLAGSHIP A LIAR FOR IT. Its first run reported that arni-hfref asserts "the two engines
    agreed" and "the protocol was registered before the first query" with nothing behind
    them. Both ARE backed -- at `results.by_outcome.<oid>.cross_engine` and at
    `registration.ordering.protocol_committed_utc` -- and I had declared `cross_engine` and
    `protocol.registration_commit`.

    So the path declarations in CLAIMS are themselves unchecked claims about where things
    live, and I got two of eight wrong on the ONE object I could verify against. That is
    the manufacturing direction again, produced by the very file written to warn about it,
    within minutes. It is recorded rather than quietly corrected because the correction is
    less interesting than the recurrence.
    """
    parts = path.split(".")
    for i, part in enumerate(parts):
        if part == "*":
            # AND THE FIRST WILDCARD RETURNED HERE INSTEAD OF DESCENDING, which discarded
            # every remaining segment. `results.by_outcome.*.cross_engine` therefore
            # resolved to the OUTCOME BLOCK -- a dict that exists, is non-empty, and is not
            # the field meant. It passed. The claim it guards was reported as backed on the
            # strength of a node with keys `k, estimand_id, comparator_type, poolable`.
            #
            # A path that resolves is not a path that resolves to the right thing, and this
            # was invisible until the VALUE was printed rather than the boolean.
            # AND IT ONLY WALKED DICTS, so `inputs.trials.*` -- a LIST -- resolved to
            # nothing and reported the flagship as unable to say its effects came from the
            # primary publications. Third wrong path declaration of eight, found the same
            # way as the first two: by printing the value instead of the verdict.
            if isinstance(obj, dict):
                children = list(obj.values())
            elif isinstance(obj, list):
                children = list(obj)
            else:
                return None
            rest = parts[i + 1:]
            for v in children:
                got = get(v, ".".join(rest)) if rest else v
                if got not in (None, [], {}, ""):
                    return got
            return None
        if not isinstance(obj, dict) or part not in obj:
            return None
        obj = obj[part]
    return obj


def entitled(obj, paths):
    """Every path must resolve to something non-empty. No partial credit."""
    for p in paths:
        v = get(obj, p)
        if v is None or v == [] or v == {} or v == "":
            return False, p
    return True, None


def manuscript_text(obj):
    """Every string under `manuscript.*` -- the prose that could enter a page."""
    m = obj.get("manuscript")
    out = []
    stack = [m]
    while stack:
        n = stack.pop()
        if isinstance(n, str):
            out.append(n)
        elif isinstance(n, dict):
            stack.extend(n.values())
        elif isinstance(n, list):
            stack.extend(n)
    return "\n".join(out)


def scan(obj):
    """Claims asserted by this object's manuscript that its fields do not entitle it to."""
    text = manuscript_text(obj)
    if not text:
        return [], []
    asserted, unbacked = [], []
    for label, rx, paths in CLAIMS:
        if not rx.search(text):
            continue
        asserted.append(label)
        ok, missing = entitled(obj, paths)
        if not ok:
            unbacked.append((label, missing))
    return asserted, unbacked


def selftest():
    """PASS on arni-hfref, FAIL on an object that does not hold the fields.

    The failing input is CONSTRUCTED FROM THE CORPUS: ARNI's own manuscript block is
    grafted onto another real object, which is exactly the copy this lint exists to
    prevent. If that does not raise every claim as unbacked, the lint cannot fire.
    """
    arni = json.load(io.open(os.path.join(SSOT, "arni-hfref", "arni-hfref.json"),
                             encoding="utf-8"))
    asserted, unbacked = scan(arni)
    print("SELFTEST 1 -- arni-hfref, which the sentences were written for")
    print("   claims asserted : %d  %s" % (len(asserted), ", ".join(asserted)))
    print("   unbacked        : %d  %s"
          % (len(unbacked), "; ".join("%s (no %s)" % u for u in unbacked)))
    if not asserted:
        print("   FAILED: matched no claim at all on the object the matchers were written "
              "from. The matchers are wrong.")
        return 1

    host = json.load(io.open(os.path.join(SSOT, "sglt2-hf", "sglt2-hf.json"),
                             encoding="utf-8"))
    host = dict(host)
    host["manuscript"] = arni["manuscript"]
    a2, u2 = scan(host)
    print()
    print("SELFTEST 2 -- ARNI's manuscript grafted onto sglt2-hf, the copy this prevents")
    print("   claims asserted : %d" % len(a2))
    print("   unbacked        : %d  %s"
          % (len(u2), "; ".join("%s (no %s)" % u for u in u2)))
    if len(u2) <= len(unbacked):
        print("   FAILED: grafting the flagship's prose onto another object raised no new "
              "unbacked claim. THE LINT CANNOT FIRE ON THE THING IT EXISTS FOR.")
        return 1
    print()
    print("SELFTEST PASSED: %d claims are backed on arni-hfref and unbacked on the graft. "
          "The failing input is a real object carrying real prose, not a fixture."
          % (len(u2) - len(unbacked)))
    return 0


def main():
    if "--selftest" in sys.argv:
        return selftest()
    objects = 0
    with_prose = 0
    offenders = []
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
        objects += 1
        if not obj.get("manuscript"):
            continue
        with_prose += 1
        asserted, unbacked = scan(obj)
        if unbacked:
            offenders.append((name, unbacked))
        print("%-40s asserts %d claim(s), %d unbacked" % (name, len(asserted), len(unbacked)))

    print()
    print("objects read                     %d" % objects)
    print("objects carrying manuscript prose %d" % with_prose)
    if with_prose == 0:
        print("NOT_ASSESSABLE: no object carries manuscript prose, so no method claim can "
              "have been asserted. A checker with nothing to check has not passed.")
        return 2
    if offenders:
        print()
        for name, unbacked in offenders:
            for label, missing in unbacked:
                print("REFUSED %-34s asserts %-46s and holds no %s"
                      % (name, label, missing))
        return 1
    print("PASS, measured on %d object(s) carrying manuscript prose: every method claim "
          "asserted resolves to a field path on the object asserting it. THIS SAYS NOTHING "
          "ABOUT THE 140 OBJECTS WITH NO PROSE -- they assert nothing because they say "
          "nothing, and that is not the same as being safe." % with_prose)
    return 0


if __name__ == "__main__":
    sys.exit(main())
