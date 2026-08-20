"""P47: a manuscript whose reader-facing sections are refusals is not complete.

WHY THIS EXISTS. On 2026-08-20 Mahmood opened SGLT2_HF_REVIEW.html#paper and called it
incomplete. Measured against ARNI:

                                  SGLT2_HF     ARNI
    paper sections (h3)                 27       29
    words in the paper               5,111   11,182

THE SECTION COUNT WAS ESSENTIALLY EQUAL AND THE SUBSTANCE WAS 2.2x APART, which is exactly
why ssot/manuscript_guard.py could not see it: that guard knows delivered LENGTH and
SECTION COUNT, and both of those said the two pages were siblings.

The distribution was the finding, not the total. The four sections a reader of a paper
opens first came to 219 WORDS AND EIGHT REFUSALS between them --

    Abstract        83 words
    Introduction    50 words   2 refusals
    Discussion      43 words   2 refusals
    Conclusions     43 words   2 refusals

-- while Certainty of the evidence ran to 651 and Methods-synthesis to 550. THE MANUSCRIPT
WAS HEAVIEST WHERE A READER IS LEAST LIKELY TO START AND THINNEST WHERE THEY ARE.

And the refusals were CORRECT. The object holds no discussion and no conclusions, so the
projector refused them by name, as the standard requires. That is the finding rather than
the excuse: A TOPIC CAN SATISFY ALL FOUR P46 CRITERIA AND STILL RENDER A PAPER WITH NOTHING
IN THE SECTIONS A READER READS. P46 counts artefacts an object HOLDS; it says nothing about
whether the manuscript those artefacts project can be read as a paper.

THE ONE-SENTENCE DIAGNOSIS, because it is what the totals concealed: ARNI IS ORGANISED
AROUND FINDINGS AND THIS IS ORGANISED AROUND THE OBJECT'S FIELD STRUCTURE. ARNI's discussion
is seven named findings -- Principal findings, Interpreting the estimate, Heterogeneity, The
leave-one-out finding, Why the risk-of-bias rating did not change, Comparison with other
evidence, Strengths. Its "Where our result differs from theirs" runs to 1,559 words against
this page's comparison section at 29 words and a refusal. That is the difference between a
paper and a rendered record.

WEIGHTED BY SECTION, NOT BY PAGE, deliberately. A page total cannot express this: 5,111
words is not a small manuscript, and the whole point is that the total was never the
problem.

This is a REPORTER with a ratchet. It does not block: 22 of 24 projectable topics fail it
today, and a gate that refuses everything gets deleted rather than satisfied. It states the
number, names the sections, and refuses only on a RISE.
"""
import io
import json
import os
import re
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SSOT = os.path.join(REPO, "ssot")

# The sections a reader of a paper opens first. Keys as ssot/paper_projector.py emits them.
READER_FACING = ("abstract", "introduction", "discussion", "conclusions")
MIN_WORDS = 60          # below this a section is a stub whether or not it refuses


def main():
    sys.path.insert(0, SSOT)
    import paper_projector as PP

    rows = []
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
        if not ((obj.get("results") or {}).get("by_outcome")):
            continue
        try:
            secs = PP.project(obj)
        except Exception as e:
            rows.append((name, None, "PROJECTION FAILED: %s" % str(e)[:60]))
            continue
        bykey = {getattr(s, "key", None): s for s in secs}
        bad = []
        for key in READER_FACING:
            s = bykey.get(key)
            if s is None:
                bad.append("%s: absent" % key)
                continue
            words = sum(len(str(t).split()) for t, _ in s.paras)
            if s.refusals and not s.paras:
                bad.append("%s: refused" % key)
            elif words < MIN_WORDS:
                bad.append("%s: %d words" % (key, words))
        rows.append((name, len(bad), "; ".join(bad)))

    projectable = [r for r in rows if r[1] is not None]
    if not projectable:
        print("NOT_ASSESSABLE: no topic projected a manuscript. A checker with nothing to "
              "check has not passed.")
        return 2
    failing = [r for r in projectable if r[1] > 0]

    print("topics projecting a manuscript          %d" % len(projectable))
    print("topics with a stub or refused           %d" % len(failing))
    print("reader-facing sections examined         %d" % (len(projectable) * len(READER_FACING)))
    print()
    print("%-46s %5s  %s" % ("topic", "bad", "which"))
    print("-" * 130)
    for name, nbad, detail in sorted(projectable, key=lambda r: (-(r[1] or 0), r[0])):
        print("%-46s %5s  %s" % (name[:46], nbad, detail[:74]))

    baseline_path = os.path.join(REPO, "evidence", "reader_facing_sections_baseline.json")
    if "--baseline" in sys.argv:
        with io.open(baseline_path, "w", encoding="utf-8", newline="\n") as fh:
            json.dump({"measured_utc": "2026-08-20", "failing_topics": len(failing),
                       "projectable_topics": len(projectable),
                       "reader_facing": list(READER_FACING), "min_words": MIN_WORDS,
                       "measured_by": os.path.basename(__file__),
                       "_what_a_pass_means": (
                           "That no ADDITIONAL topic renders a paper with stubs or refusals "
                           "in the four sections a reader opens first. It does NOT mean the "
                           "existing ones are acceptable -- most of the corpus fails this "
                           "today and the number is the work item.")}, fh, indent=1)
            fh.write("\n")
        print("\nbaseline written: %d failing of %d" % (len(failing), len(projectable)))
        return 0
    if not os.path.exists(baseline_path):
        print("\nNOT_ASSESSABLE: no baseline. Run with --baseline.")
        return 2
    base = json.load(io.open(baseline_path, encoding="utf-8"))["failing_topics"]
    if len(failing) > base:
        print("\nREFUSED: %d topics render a paper whose reader-facing sections are stubs or "
              "refusals, up from %d." % (len(failing), base))
        return 1
    print("\nREPORTED, NOT PASSED: %d of %d topics fail P47 against a baseline of %d, none "
          "new. A MANUSCRIPT WHOSE READER-FACING SECTIONS ARE REFUSALS IS NOT COMPLETE "
          "REGARDLESS OF ITS TOTALS, and %d topics are in that state right now."
          % (len(failing), len(projectable), base, len(failing)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
