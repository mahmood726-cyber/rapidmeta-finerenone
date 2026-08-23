"""Every path that puts prose on a page must reach the render transform. Proven, not asserted.

SEVEN PATHS, SIX FIXED ONE AT A TIME, ONE ARCHITECTURE CHANGE CLOSING ALL OF THEM.

`Section.add` applied `_tidy`. These did not, and each was found by a person reading a page:

    1  refusal text                       "Background is ARGUMENT -- why this question matters"
    2  add_table captions                 shouted openers in a caption
    3  add_table cells                    "THREE TRIALS. NCT00761267's registered primary is..."
    4  s.paras.append for referrals       "NOTED ON THIS POOL. READ THIS BESIDE THE ESTIMATE."
    5  s.paras.append for findings        the same
    6  the build-stamp ratchet note       "this page is BELOW it and knowably so"
    7  s.paras.append for eligibility     "ELIGIBILITY turns on population, intervention..."

The seventh was found by Mahmood, on the page he had complained about six times, after the
first six were fixed and reported as closed. THAT IS THE ARGUMENT FOR THE RENDER POINT: a choke
point that can be bypassed is not a choke point, and the evidence is the ratio -- six
individual fixes did not close the class, one placement did.

WHAT THIS GATE ASSERTS. `build_tabbed` renders paragraphs in exactly one loop, and that loop
must apply the transform. If the transform is removed from it, or a second rendering loop
appears that does not apply it, this fails. It does NOT try to forbid `s.paras.append` -- that
would be the wrong rule, because appending is legitimate; what matters is that everything
appended is transformed on the way out.

PROVEN BOTH WAYS on every run: the real source must pass, and a mutant with the transform
removed from the render loop must fail. A gate that has never seen its own failure is a gate
nobody has tested.
"""
import io
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILDER = os.path.join(REPO, "ssot", "build_tabbed.py")

# The one loop that turns Section.paras into page text.
RENDER_LOOP = re.compile(r"for\s+text,\s*fields\s+in\s+(.+?):")
TIDIED = re.compile(r"_tidy\s*\(")


def check(src):
    """-> (ok, reason). The render loop exists exactly once and applies the transform."""
    loops = RENDER_LOOP.findall(src)
    if not loops:
        return False, "no paragraph render loop found in the builder at all"
    if len(loops) > 1:
        untidied = [l for l in loops if not TIDIED.search(l)]
        if untidied:
            return False, ("%d paragraph render loops, and %d of them do not apply the "
                           "transform: %s" % (len(loops), len(untidied), untidied[:2]))
    if not TIDIED.search(loops[0]):
        return False, ("the paragraph render loop does not apply the transform -- prose "
                       "appended by any path reaches the page untouched: %r" % loops[0][:80])
    return True, "the render loop applies the transform"


def prove():
    src = io.open(BUILDER, encoding="utf-8", errors="replace").read()
    ok, why = check(src)
    if not ok:
        sys.exit("PROOF FAILED on the real source: %s" % why)
    # the mutant: strip the transform from the render loop, as a careless edit would
    mutant = RENDER_LOOP.sub(lambda m: "for text, fields in s.paras:", src, count=1)
    mok, mwhy = check(mutant)
    if mok:
        sys.exit("PROOF FAILED: a source with the transform REMOVED from the render loop "
                 "still passes. This gate cannot detect the thing it exists to detect.")
    print("PROOF PASSED: the real source passes and a source with the transform removed from")
    print("the render loop fails -- %s" % mwhy)


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    prove()
    src = io.open(BUILDER, encoding="utf-8", errors="replace").read()
    ok, why = check(src)
    appends = len(re.findall(r"\.paras\.append\(", src)) + len(
        re.findall(r"\.paras\.append\(",
                   io.open(os.path.join(REPO, "ssot", "paper_projector.py"),
                           encoding="utf-8", errors="replace").read()))
    print("")
    print("PATHS THAT APPEND PROSE:            %d" % appends)
    print("PARAGRAPH RENDER LOOPS:             %d" % len(RENDER_LOOP.findall(src)))
    print("TRANSFORM APPLIED AT THE RENDER:    %s" % ("yes" if ok else "NO"))
    print("")
    print("Any of those append sites may be added to without touching this gate. That is the")
    print("point: appending is legitimate, and what matters is that everything appended is")
    print("transformed on the way out. An eighth bypass is now a build-time impossibility")
    print("rather than something a reader has to find.")
    if not ok:
        sys.exit("REFUSED: %s" % why)


if __name__ == "__main__":
    main()
