"""GATE 18  A CORRECTION MUST RENDER

Being correctable is the claim this corpus makes. A correction a reader cannot
see does not make good on it.

TWO DIFFERENT THINGS HAVE BEEN CALLED "the corrections", and conflating them
produced a wrong brief:

  the corrections/ DIRECTORY   an append-only store; a separate lane proved by
                               plant that it survives regeneration and that no
                               served surface renders it
  in-page correction TEXT      prose in the page itself saying a previous
                               published version differed

THIS GATE IS ABOUT THE SECOND, AND ON 2026-09-01 THE IN-PAGE CORRECTIONS ALL
RENDER. Of 44 pages classed PUBLISHED_CORRECTION, 35 are assertable and all 35
appear in VISIBLE TEXT. The brief said a reader could not see a single
correction; that was false of this artefact.

HOW THREE NORMALISATIONS GAVE THREE ANSWERS ON ONE UNCHANGED CORPUS, and why
the baseline is set from a hand-read rather than from any of them:

  collapse whitespace only          29 render, 5 absent, 2 markup-only
  drop every non-alphanumeric       35 render, 0 failing
  collapse space before punctuation 35 render, 1 absent

The corpus did not change between those runs, so the metric was measuring the
INSTRUMENT. The middle one is a loosened test, not a repaired one: a phrase
absent from the page bytes must not become present because the comparison
stopped caring about commas. The third repairs exactly the defect the gate's own
control found -- a stripped inline tag leaving `otherwise , and` -- and no more.

Then every page the instrument still called failing was READ BY A HUMAN. All of
them carry their correction in plain prose. The last one, BRODALUMAB, was a
defect in the INPUT: the baseline pins a fixed 180-character slice, and that
slice cut an HTML entity in half, so the pin could never match. Blaming a page
for a flaw in the instrument is the failure this suite exists to prevent, so a
cut pin gets its own verdict, PHRASE_UNUSABLE, and is counted with the
unassertable.

MARKUP-ONLY AND ABSENT BOTH FAIL. A phrase in an attribute is visible to a
parser and not to a reader, and the claim is about readers.

UNASSERTABLE IS NOT CLEAN: 8 pages pin no phrase and 1 pins a cut one. All 9 are
named in the coverage line and never counted as passing.

CONTROLS RUN IN BOTH DIRECTIONS. Clean-input controls only prove the gate does
not accuse the innocent; they are silent on whether it has become too permissive,
and a loosened comparison passes every one of them. So three ADVERSARIAL cases --
a fragment, a one-word near-miss, and the same words reordered -- must each be
REJECTED, and the gate reports BROKEN if any is accepted.

Baseline OWED, not cleared, at 0 failing. It refuses a NEW failing page or a
rise, and must be lowered as the 9 unassertable are made assertable.
"""
from __future__ import annotations

import html as _html
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _harness as H                                                        # noqa: E402

REPO = H.repo_root()
BASELINE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "GATE18_CORRECTION_RENDERS_BASELINE.json")
INPUT = os.path.join(REPO, "scripts", "baselines", "published_corrections.json")

SCRIPT = re.compile(r"<script\b[^>]*>(.*?)</script>", re.S | re.I)
STYLE = re.compile(r"<style\b[^>]*>.*?</style>", re.S | re.I)
TAG = re.compile(r"<[^>]+>")
WS = re.compile(r"\s+")

SYN_VISIBLE = "synthetic-correction-renders"
SYN_SCRIPT = "synthetic-correction-script-only"


SPACE_BEFORE_PUNCT = re.compile(r"\s+([,.;:!?%)\]}])")


def sig(text):
    """Comparison signature: entities decoded, whitespace collapsed, and the
    space a stripped tag leaves BEFORE punctuation removed.

    THIS IS DELIBERATELY NARROW. Stripping `<strong>` leaves a space where the
    tag was, so `said otherwise</strong>, and` becomes `said otherwise , and`
    and never matches `said otherwise, and` -- the gate's own control caught
    that and refused the gate.

    The first attempt at a fix dropped EVERY non-alphanumeric instead, and all
    seven failing pages passed at once. Nothing in the corpus had changed
    between the two runs, so the metric was measuring the instrument. A phrase
    ABSENT FROM THE PAGE BYTES must not become present because the comparison
    stopped caring about commas. Repair the defect the control found; do not
    widen past it.
    """
    t = WS.sub(" ", _html.unescape(text))
    return SPACE_BEFORE_PUNCT.sub(r"\1", t).strip()


def surfaces(doc):
    """(visible text, script text, whole no-script document), all as signatures."""
    scripts = " ".join(SCRIPT.findall(doc))
    nojs = STYLE.sub(" ", SCRIPT.sub(" ", doc))
    visible = TAG.sub(" ", nojs)
    return sig(visible), sig(scripts), sig(nojs)


CUT_TAIL = re.compile(r"&[A-Za-z#][A-Za-z0-9#]*$|&$")
CUT_HEAD = re.compile(r"^([A-Za-z][A-Za-z0-9]*);")


def phrase_unusable(phrase):
    """Is the PIN itself unmatchable, rather than the page being at fault?

    The baseline pins a 180-character slice of page bytes, and a fixed-width
    slice can cut an HTML entity in half. BRODALUMAB's pin ends `...was &`
    where the page reads `was &ldquo;Papp`; unescaped, the page says `was "Papp`,
    so the pin's bare `&` cannot appear in visible text BY CONSTRUCTION. The
    correction is plainly on that page - a human read it - and the gate was
    calling the page defective for a defect in its own input.

    Blaming the artefact for a flaw in the instrument is the failure this whole
    suite exists to prevent, so it gets its own verdict and is counted with the
    unassertable, never with the passes.
    """
    if CUT_TAIL.search(phrase.strip()):
        return True
    m = CUT_HEAD.match(phrase.strip())
    if m and _html.unescape("&%s;" % m.group(1)) != "&%s;" % m.group(1):
        return True          # phrase begins with the tail of a real entity
    return False


def classify(doc, phrase):
    vis, scr, nojs = surfaces(doc)
    needle = sig(phrase)
    if not needle:
        return "NO_PHRASE_PINNED"
    if phrase_unusable(phrase):
        return "PHRASE_UNUSABLE"
    if needle in vis:
        return "RENDERS"
    if needle in scr:
        return "SCRIPT_ONLY"
    if needle in nojs:
        return "MARKUP_ONLY"
    return "ABSENT"


def main(argv):
    gate = H.Gate("18 A CORRECTION MUST RENDER",
                  "a pinned correction phrase must appear in visible text")
    gate.requires_control()

    if not os.path.exists(INPUT):
        gate.kinds({"baseline input absent": 1})
        gate.broken("scripts/baselines/published_corrections.json is not present")
        gate.coverage(0, 1, "the input that names the corrections is missing")
        return gate.report()

    # ---- named positives: SYNTHETIC, so they cannot retire ---------------
    # Anchoring a named positive to a live defect makes the gate go vacuous the
    # moment the defect is fixed, and a gate that passes because its target no
    # longer exists is indistinguishable from one that works. Proven twice in
    # this suite on 2026-08-31.
    gate.expect_case(SYN_VISIBLE, "a phrase present in visible text is classed RENDERS")
    gate.expect_case(SYN_SCRIPT, "a phrase present only inside <script> is classed SCRIPT_ONLY")
    P = "an earlier version of this sentence said otherwise, and that was wrong"
    if classify("<html><body><p>%s</p></body></html>" % P, P) == "RENDERS":
        gate.saw(SYN_VISIBLE)
    if classify('<html><body><script>var x="%s";</script></body></html>' % P, P) == "SCRIPT_ONLY":
        gate.saw(SYN_SCRIPT)

    # ---- known-negative control: markup-split phrases must still pass ----
    # These exercise the normalisation itself. A looser reimplementation scores
    # every one of them ABSENT, which is exactly how a real correction gets
    # reported as missing.
    # Each carries the SAME sentence a reader sees, in a different markup shape.
    # All four must score RENDERS. #1 is the one that caught the first version of
    # this gate: an inline tag beside punctuation left `otherwise , and`.
    negatives = [
        ("plain", "<p>%s</p>" % P),
        ("inline tag beside punctuation",
         "<p>an earlier version of this sentence <strong>said otherwise</strong>, "
         "and that was wrong</p>"),
        ("newlines inside the paragraph",
         "<p>an earlier version of this\n   sentence said otherwise, and that was\n"
         "   wrong</p>"),
        ("html entity inside the phrase",
         "<p>an earlier version of this&nbsp;sentence said otherwise, and that "
         "was wrong</p>"),
    ]
    accused = []
    for name, neg in negatives:
        got = classify("<html><body>%s</body></html>" % neg, P)
        if got != "RENDERS":
            accused.append("%s scored %s" % (name, got))

    # ---- ADVERSARIAL controls: pages the gate MUST REJECT ----------------
    # A clean-input control proves the gate does not accuse the innocent. It says
    # NOTHING about whether the gate has become too permissive, and a loosened
    # comparison passes every clean-input control there is. These are adversarial
    # to the SPECIFIC loosening a normalisation fix invites: a fragment, a
    # one-word near-miss, and the same words in a different order. Each MUST NOT
    # score RENDERS, and a failure here is counted as a false NEGATIVE and
    # reported as BROKEN rather than folded into the false-positive rate.
    adversarial = [
        ("a fragment of the phrase, not the phrase",
         "<p>an earlier version of this sentence</p>"),
        ("one word changed - a near miss",
         "<p>an earlier version of this sentence said otherwise, and that was "
         "right</p>"),
        ("the same words in a different sentence",
         "<p>that was wrong, and an earlier version of this sentence said "
         "otherwise</p>"),
    ]
    accepted = []
    for name, adv in adversarial:
        if classify("<html><body>%s</body></html>" % adv, P) == "RENDERS":
            accepted.append(name)
    if accepted:
        gate.broken("ADVERSARIAL CONTROL FAILED - the gate ACCEPTED input it must "
                    "reject, so its RENDERS verdict is not trustworthy: "
                    + "; ".join(accepted))
    gate.note("adversarial controls (must be REJECTED): %d of %d correctly rejected"
              % (len(adversarial) - len(accepted), len(adversarial)))
    gate.control(len(negatives), len(accused), accused)

    # ---- the sweep --------------------------------------------------------
    data = H.load(INPUT)
    pages = data.get("pages", {})
    pc = {p: r for p, r in pages.items() if r.get("class") == "PUBLISHED_CORRECTION"}

    results, unassertable = {}, []
    for page, rec in sorted(pc.items()):
        phrase = (rec.get("must_render") or "").strip()
        if not phrase:
            unassertable.append(page)
            continue
        path = os.path.join(REPO, page)
        if not os.path.exists(path):
            results[page] = "PAGE_MISSING"
            continue
        with open(path, encoding="utf-8", errors="replace") as fh:
            results[page] = classify(fh.read(), phrase)

    kinds = {}
    for v in results.values():
        kinds[v] = kinds.get(v, 0) + 1
    kinds["no phrase pinned - UNASSERTABLE, not clean"] = len(unassertable)
    gate.kinds(dict(sorted(kinds.items(), key=lambda kv: -kv[1])))

    # Coverage: only a page with a pinned phrase can be decided on. The 8
    # without one are NOT clean -- nothing can check them - and they are named.
    gate.coverage(len(results), len(pc),
                  "PUBLISHED_CORRECTION pages with NO pinned must_render phrase, so "
                  "nothing can be asserted about them: " + ", ".join(unassertable))

    failing = sorted(p for p, v in results.items()
                     if v in ("ABSENT", "MARKUP_ONLY", "SCRIPT_ONLY", "PAGE_MISSING"))
    unusable_pins = sorted(p for p, v in results.items() if v == "PHRASE_UNUSABLE")

    if not os.path.exists(BASELINE):
        gate.broken("no baseline at %s -- run with --write-baseline" % BASELINE)
        return gate.report()
    base = H.load(BASELINE)
    frozen = set(base.get("failing_pages", []))

    gate.note("baseline recorded %s: %d failing (%s)"
              % (base.get("recorded"), base.get("n_failing"), base.get("status")))
    gate.note("a PASS means no NEW page stopped rendering its correction, not that "
              "every correction renders: %d remain OWED" % len(failing))
    fixed = frozen - set(failing)
    if fixed:
        gate.note("now rendering since the freeze (lower the baseline): %s"
                  % ", ".join(sorted(fixed)))

    for p in sorted(set(failing) - frozen):
        gate.finding("CORRECTION-NO-LONGER-RENDERS",
                     "%s: pinned correction phrase is %s. A correction a reader "
                     "cannot see does not make good on the claim."
                     % (p, results.get(p)),
                     numerator=len(set(failing) - frozen), denominator=len(frozen))
    if len(failing) > base.get("n_failing", 0) and not (set(failing) - frozen):
        gate.finding("CORRECTION-FAILURES-ROSE",
                     "failing pages rose from %d to %d with no new page named"
                     % (base.get("n_failing"), len(failing)))

    return gate.report(denominator="%d assertable of %d PUBLISHED_CORRECTION pages"
                                   % (len(results), len(pc)))


def write_baseline():
    data = H.load(INPUT)
    pages = data.get("pages", {})
    pc = {p: r for p, r in pages.items() if r.get("class") == "PUBLISHED_CORRECTION"}
    failing, unassertable, renders = [], [], 0
    for page, rec in sorted(pc.items()):
        phrase = (rec.get("must_render") or "").strip()
        if not phrase:
            unassertable.append(page)
            continue
        path = os.path.join(REPO, page)
        if not os.path.exists(path):
            failing.append(page)
            continue
        with open(path, encoding="utf-8", errors="replace") as fh:
            v = classify(fh.read(), phrase)
        if v == "RENDERS":
            renders += 1
        elif v == "PHRASE_UNUSABLE":
            unassertable.append(page)      # input defect, not a page defect
        else:
            failing.append(page)
    payload = {
        "recorded": "2026-09-01",
        "status": "OWED - NOT CLEARED",
        "means": ("These corrections do not reach a reader and are owed. The baseline "
                  "lets the gate refuse a REGRESSION while they are fixed. It is not a "
                  "statement that any of them is acceptable, and it must be lowered as "
                  "they are fixed, never raised."),
        "n_published_correction": len(pc),
        "n_assertable": len(pc) - len(unassertable),
        "n_rendering": renders,
        "n_failing": len(failing),
        "failing_pages": failing,
        "unassertable_pages_not_clean": unassertable,
        "why_this_baseline_is_not_zero_by_default": (
            "A baseline written at 0 makes the gate permanently unable to notice the "
            "pages it was built for. This one is set from a HAND-READ of every page the "
            "instrument called failing, not from what any normalisation reported: three "
            "normalisations gave 7, 0 and 1 failures on the same unchanged corpus."),
    }
    with open(BASELINE, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)
    print("baseline written: %s" % BASELINE)
    print("  %d PUBLISHED_CORRECTION, %d assertable, %d rendering, %d FAILING"
          % (len(pc), payload["n_assertable"], renders, len(failing)))
    print("  unassertable (NOT clean): %d" % len(unassertable))
    return 0


if __name__ == "__main__":
    if "--write-baseline" in sys.argv:
        sys.exit(write_baseline())
    sys.exit(main(sys.argv[1:]))
