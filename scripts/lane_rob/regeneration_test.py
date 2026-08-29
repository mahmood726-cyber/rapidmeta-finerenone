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
    ("estimand named", r"\bestimand\b"),
    ("binary-versus-time-to-event stated", r"time[- ]to[- ]event"),
    ("absolute effects per 1000", r"per 1,?000 (?:women|people|patients)"),
    ("number needed to treat", r"number needed to treat|\bNNT\b"),
    ("age-stratified efficacy", r"21 or younger|age[- ]stratified"),
    ("safety outcomes", r"serious adverse event|grade 3 adverse"),
    ("other STI outcomes", r"gonorrh|chlamyd|trichomon|syphilis"),
    ("currency: what changed since", r"since (?:the|these)[^.]{0,40}(?:search|synthes)"),
    ("clinical reading", r"what a clinician|should take from this"),
    ("adjudicated versus registry counts", r"adjudicated (?:counts|publication)"),
    ("audit trail / provenance", r"audit trail|sha256"),
    ("integrity section", r"What was checked before"),
    ("modified HKSJ named", r"modified[^.]{0,30}(?:hartung|knapp)"),
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
    out = r"F:\claude-temp\pend\out\regen_test.html"
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
