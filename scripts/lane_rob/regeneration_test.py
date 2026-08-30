# -*- coding: utf-8 -*-
"""THE SCALABILITY TEST, made executable: can the harness regenerate a page's winning state?

MAHMOOD'S RULE, AND IT REPLACES THE ONE I WAS USING. Every improvement lands in the harness;
all pages are then REGENERATED and judged again. If a page cannot be regenerated to its winning
state, the improvement was not in the harness.

⇒ That cannot be gamed. Labelling a section "bespoke" relies on the author's honesty;
regeneration relies on nothing. I was measuring the bespoke fraction BY DECLARATION and put it
at 15-25%. Measured by destroying and rebuilding, it is 100%.

⚠️ AND KEYWORD PRESENCE IS NOT THE TEST -- this is the second instrument on this page to learn
it. A first pass scored the harness at 5 of 13 features present. All five were FALSE POSITIVES:
every one matched inside a sentence saying the review LACKS that thing. "number needed to treat"
appeared in "what this review does not give a clinician: ... any absolute effect or number
needed to treat". A detector that cannot tell an assertion from its negation will score a
confession as a capability.

⇒ So every feature carries a NEGATION GUARD: a match inside a lacking-clause does not count,
and the surrounding text is printed so a reader can see what matched rather than trusting a
tick.
"""
import io
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
os.chdir(REPO)
sys.path.insert(0, HERE)
import document_kind as DK  # noqa: E402

# A match that sits inside one of these clauses is the page CONFESSING the gap, not filling it.
NEGATION = re.compile(
    r"does not (?:give|provide|report|carry|include)|no (?:absolute|measure|systematic)|"
    r"not adjudicated|cannot be|is absent|were not|lacks|limitations", re.I)

FEATURES = [
    # ⚠️ THIS WAS A PROXY FOR THE CAPABILITY AND WAS WEAKER THAN IT.
    #
    # The first version searched for the literal word "estimand". A component then landed that
    # states the pooled quantity and its kind on every page -- "Pooled as RR ... binary counts"
    # -- and the test still read ABSENT, because the component uses plainer words than the
    # detector's proxy.
    #
    # The WRONG fix is to make the page print "estimand" to satisfy the test: that is content
    # written for a detector, which is the thing this project refuses. So the detector now
    # requires SUBSTANCE -- the page must say what it pooled AND what kind of quantity that is.
    # A page cannot pass by printing one word, and it passes when it does the real thing.
    ("states the pooled quantity and its kind",
     r"pooled as.{0,400}?(binary counts|time to event|continuous measure)"),
    ("binary-versus-time-to-event stated", r"time[- ]to[- ]event"),
    # ⚠️ ANOTHER PROXY THAT WAS WEAKER THAN THE CAPABILITY, and the third time this file has
    # learned it. The old pattern required the literal phrase "per 1000 women". The component
    # that landed prints a table headed "Risk per 1,000, control" and "Absolute reduction per
    # 1,000" -- the real thing, in the words a table uses -- and scored ABSENT.
    #
    # ⛔ THE PAGE WAS NOT CHANGED TO SATISFY THE DETECTOR. The replacement was PLANTED BOTH WAYS
    # against a genuine pre-change build of this same object (built from the unmodified harness,
    # 56,396 rendered characters): it matches NOTHING there and matches the new table. A pattern
    # that fires on the old page would be measuring the renderer's vocabulary, not its output.
    ("absolute effects per 1000",
     r"(?:risk|reduction|events?|infections?)[^.<]{0,40}per 1,?000"),
    ("number needed to treat", r"number needed to treat|\bNNT\b"),
    # ⚠️ SAME SHAPE. "21 or younger" is the phrasing of ASPIRE's ABSTRACT; the component reads
    # the RESULTS section, where the strata are "18 to 21 years" and "under 25 years" -- and the
    # under-25 split is the PRESPECIFIED one, which the hand-built page mislabelled "18 to 24".
    # A detector keyed to the hand-built wording would have scored the more accurate page as
    # missing the feature. Planted both ways against the pre-change build: no match there.
    ("age-stratified efficacy",
     r"(?:by age|age[- ]stratified|age stratum)[\s\S]{0,800}?\b\d{2} (?:years|to \d{2})"),
    ("safety outcomes", r"serious adverse event|grade 3 adverse"),
    ("other STI outcomes", r"gonorrh|chlamyd|trichomon|syphilis"),
    ("currency: what changed since", r"since (?:the|these)[^.]{0,40}(?:search|synthes)"),
    ("clinical reading", r"what a clinician|should take from this"),
    ("adjudicated versus registry counts", r"adjudicated (?:counts|publication)"),
    ("audit trail / provenance", r"audit trail|sha256"),
    ("integrity section", r"What was checked before"),
    ("modified HKSJ named", r"modified[^.]{0,30}(?:hartung|knapp)"),
]

# ⛔ SCORED SEPARATELY, AND DELIBERATELY NOT ADDED TO FEATURES ABOVE.
#
# These are the axes the COMPARATOR won, named by all six blinded judges. Folding them into
# FEATURES would change the denominator of the acceptance bar, and "13 of 13" and "14 of 14"
# would then mean different things while looking like progress. The bar is about reproducing
# what WON; this list is about closing what LOST. Two questions, two denominators.
LOSING_AXES = [
    ("formal GRADE certainty for our own estimate",
     r"certainty in this estimate is|starting at .{0,20}for randomised evidence"),
    ("the certainty is derived, not asserted",
     r"recomputed from the table"),
    ("search breadth: ICTRP run", r"ICTRP"),
]


def present(text, pat):
    """True only if a match exists OUTSIDE a clause confessing the gap."""
    for m in re.finditer(pat, text, re.I):
        window = text[max(0, m.start() - 220):m.end() + 60]
        if not NEGATION.search(window):
            return True, re.sub(r"\s+", " ", window)[-150:]
    m = re.search(pat, text, re.I)
    if m:
        w = text[max(0, m.start() - 200):m.end() + 60]
        return False, "ONLY inside a negation: ..." + re.sub(r"\s+", " ", w)[-120:]
    return False, "not found at all"


def regenerate(obj_path, out_path):
    r = subprocess.run([sys.executable, os.path.join("ssot", "build_tabbed.py"),
                        obj_path, out_path], capture_output=True, timeout=1200)
    return r.returncode, r.stdout.decode("utf-8", "replace")[-300:]


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                                  line_buffering=True)
    obj = sys.argv[1] if len(sys.argv) > 1 else "ssot/agyw-hiv-prep-review/agyw-hiv-prep-review.json"
    # ⛔ ONE OUTPUT PATH PER OBJECT, and the shared path was a real defect in this test.
    #
    # Every topic used to write to regen_test.html. The manuscript guard then compared THIS
    # topic's build against the LAST topic's page and refused a 48% "shrink" that was simply a
    # shorter review -- so the score depended on the order the topics were run in. Dapivirine
    # measured 2 of 13 when it ran first and REFUSED TO BUILD AT ALL when it ran second.
    #
    # A measurement that changes with run order is not a measurement, and this one failed in the
    # direction that looks like a regression in the thing being tested rather than a fault in
    # the instrument -- the same shape as the adjudicator that searched a different haystack
    # than it displayed.
    out = os.path.join(r"F:\claude-temp\pend\out",
                       "regen_" + re.sub(r"[^A-Za-z0-9_-]", "_",
                                         os.path.splitext(os.path.basename(obj))[0]) + ".html")
    rc, tail = regenerate(obj, out)
    if rc != 0 or not os.path.exists(out):
        print("REFUSED: the harness could not build %s (rc=%d)\n%s" % (obj, rc, tail))
        return 2
    t = DK.rendered(io.open(out, encoding="utf-8", errors="replace").read())
    # ⛔ THE INTEGRITY SECTION IS EXCLUDED FROM THE BODY BEING SCORED, and this is not tidiness.
    #
    # That section NAMES the defect classes -- "binary counts pooled where both trials analysed
    # time to event", "a pooled quantity presented without naming what it estimates". A feature
    # detector searching the whole page then finds those phrases and credits the page with
    # HAVING the feature, when what it actually has is a description of the feature's absence.
    #
    # Measured: wiring the integrity section into the harness moved this test from 0 of 13 to
    # "3 of 13" -- and two of the three were the checker describing the defect. Zero occurrences
    # of "estimand" or "time-to-event" in the page body; three and one inside the section.
    #
    # A checker whose own output raises the score of the thing it checks is a closed loop. The
    # features must be present in the REVIEW, not in the list of things that could be wrong
    # with it.
    # AND THE INTEGRITY FEATURE ITSELF IS SCORED ON THE FULL PAGE, because truncating at the
    # marker also removed the only evidence that the section exists. The first attempt at this
    # exclusion took 3 of 13 to 0 of 13 by deleting the one real capability along with the two
    # false ones. Body for twelve features; whole page for the thirteenth.
    marker = "What was checked before this page was published"
    full = t
    i = t.find(marker)
    if i >= 0:
        t = t[:i]
    print("")
    print("REGENERATION TEST -- %s" % os.path.basename(obj))
    print("  harness output: %d rendered characters" % len(t))
    print("")
    have = 0
    for name, pat in FEATURES:
        ok, ctx = present(full if name == "integrity section" else t, pat)
        have += ok
        print("  %-36s %s" % (name, "PRESENT" if ok else "ABSENT"))
        if not ok:
            print("        %s" % ctx[:130])
    print("")
    print("  LOSING AXES -- what the comparator had and we did not. Separate denominator.")
    lose = 0
    for name, pat in LOSING_AXES:
        ok, ctx = present(t, pat)
        lose += ok
        print("  %-36s %s" % (name, "PRESENT" if ok else "ABSENT"))
        if not ok:
            print("        %s" % ctx[:130])
    print("  HARNESS NOW COVERS %d of %d losing axes" % (lose, len(LOSING_AXES)))
    print("")
    print("  HARNESS REPRODUCES %d of %d winning features" % (have, len(FEATURES)))
    print("  bespoke fraction of the winning margin: %.0f%%"
          % (100.0 * (len(FEATURES) - have) / len(FEATURES)))
    if have < len(FEATURES):
        print("")
        print("  ⇒ This page cannot be regenerated to its winning state, so the improvements")
        print("    are not in the harness. Under the acceptance rule that is a FAIL, whatever")
        print("    the judges said.")
    return 0 if have == len(FEATURES) else 1


if __name__ == "__main__":
    raise SystemExit(main())
