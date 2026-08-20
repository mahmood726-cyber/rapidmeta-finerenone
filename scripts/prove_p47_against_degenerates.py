"""Does P47 -- the standard we wrote tonight -- pass a degenerate manuscript?

P47 IS NOT A REPORT. It is in `PAGE-STANDARD.md`, it ratchets, and it is the criterion the
remaining 133 topics will be built to. So it is a metric that GUARDS SOMETHING, and class 60
says: before a metric guards anything, ask what a degenerate artefact scores on it.

Class 60 arrived from a guard that restored a blank page over a real manuscript. This file
asks the same question of the rule written to prevent that class of problem in the first
place, because the worst outcome available is 133 topics built to a standard that a
content-free page satisfies.

P47's PREDICATE, read from `lint_reader_facing_sections.py` rather than described:

    for each of abstract / introduction / discussion / conclusions:
        absent                          -> bad
        refusals and no paragraphs      -> bad
        fewer than MIN_WORDS (60) words -> bad

THREE DEGENERATES ARE SCORED AGAINST IT, using the real Section shape the projector emits:

    EMPTY        no sections at all
    REFUSALS     every reader-facing section present and correctly refused
    BOILERPLATE  every reader-facing section present, 60+ words of true, generic,
                 content-free prose that names no finding and no field

The first two are what P47 was written to catch. THE THIRD IS THE QUESTION.
"""
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "ssot"))
from instrument_controls import require_controls
import lint_reader_facing_sections as P47


class FakeSection(object):
    """The shape paper_projector emits: .key, .paras [(text, fields)], .refusals."""

    def __init__(self, key, paras=(), refusals=()):
        self.key = key
        self.paras = list(paras)
        self.refusals = list(refusals)


# 63 words. True of any systematic review, specific to none. Names no finding, no
# estimate, no trial, no field. A reader learns nothing; P47 counts words.
FILLER = (
    "This section forms part of the standard structure of a systematic review report and "
    "is presented here in the conventional position so that the document may be read in "
    "the order readers expect. The material it covers is described in accordance with "
    "established reporting practice for evidence syntheses of this kind, and is set out "
    "with the aim of supporting a clear and orderly presentation of the work undertaken "
    "throughout this review overall."
)

REAL = (
    "Four randomised outcome trials of SGLT2 inhibitors in chronic heart failure report "
    "cardiovascular death or a worsening heart failure event as a time-to-first hazard "
    "ratio. Two of them count an urgent heart-failure visit that the other two do not, so "
    "the four-trial pool combined quantities that are not the same quantity and it stands "
    "withdrawn on this page with its reason. A harmonised two-component endpoint was "
    "available at secondary rank in a registration already read, and it is pooled here "
    "across three trials at 0.76."
)


def score(label, sections):
    bad = []
    bykey = dict((s.key, s) for s in sections)
    for key in P47.READER_FACING:
        s = bykey.get(key)
        if s is None:
            bad.append("%s: absent" % key)
            continue
        words = sum(len(str(t).split()) for t, _ in s.paras)
        if s.refusals and not s.paras:
            bad.append("%s: refused" % key)
        elif words < P47.MIN_WORDS:
            bad.append("%s: %d words" % (key, words))
    return bad


def main():
    empty = []
    refusals = [FakeSection(k, refusals=[("the %s" % k, ["manuscript.%s" % k])])
                for k in P47.READER_FACING]
    boilerplate = [FakeSection(k, paras=[(FILLER, ["manuscript.%s" % k])])
                   for k in P47.READER_FACING]
    real = [FakeSection(k, paras=[(REAL, ["manuscript.%s" % k])])
            for k in P47.READER_FACING]

    cases = [("EMPTY", empty), ("REFUSALS", refusals), ("BOILERPLATE", boilerplate),
             ("REAL", real)]
    results = dict((n, score(n, s)) for n, s in cases)

    require_controls(
        "prove_p47_against_degenerates",
        positive=("P47 catches a manuscript of pure refusals -- the case it was written "
                  "for", bool(results["REFUSALS"]), True),
        negative=("P47 fails a real manuscript", bool(results["REAL"]), True))

    print("")
    print("MIN_WORDS = %d; reader-facing sections = %s"
          % (P47.MIN_WORDS, ", ".join(P47.READER_FACING)))
    print("")
    print("%-14s %-8s %s" % ("artefact", "P47", "why"))
    print("-" * 96)
    for name, _s in cases:
        bad = results[name]
        print("%-14s %-8s %s" % (name, "FAILS" if bad else "PASSES",
                                 "; ".join(bad) if bad else "every reader-facing section "
                                 "carries at least %d words and does not refuse"
                                 % P47.MIN_WORDS))

    print("")
    if not results["BOILERPLATE"]:
        print("P47 IS SATISFIED BY A PAGE THAT SAYS NOTHING.")
        print("")
        print("The boilerplate manuscript names no finding, no estimate, no trial and no")
        print("field. Every sentence in it is TRUE of any systematic review and specific to")
        print("none. It carries %d words per reader-facing section and does not refuse, so"
              % len(FILLER.split()))
        print("P47 passes it -- while correctly failing the refusals page, which is HONEST.")
        print("")
        print("SO THE STANDARD PREFERS FILLER TO A REFUSAL. That is the class-60 shape")
        print("inside the rule written tonight to fix the class-60 shape, and it matters")
        print("because 133 topics have not been built yet and P47 is what they will be")
        print("built to.")
    else:
        print("P47 refuses the boilerplate page: %s" % "; ".join(results["BOILERPLATE"]))

    print("")
    print("AND THE DEEPER STATEMENT, WHICH ARRIVED FROM THE METRICS SIDE RATHER THAN THE")
    print("EVIDENCE SIDE:")
    print("")
    print("    OUR ENTIRE DEFENSIVE ETHIC PRODUCES ARTEFACTS THAT OUR ENTIRE MEASUREMENT")
    print("    APPARATUS REWARDS.")
    print("")
    print("Refusing by name is REQUIRED behaviour here. A page that does nothing but refuse")
    print("is honest, carries no machine vocabulary, no unglossed statistics and no field")
    print("paths in prose, and scores at or near the top of every readability measure")
    print("written tonight. It is also worthless to a reader. P47 catches that page -- and")
    print("the page it lets through instead is one that says nothing at greater length.")


if __name__ == "__main__":
    main()
