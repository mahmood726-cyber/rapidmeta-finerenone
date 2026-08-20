"""Does each refusal name a FACT ABOUT THE OBJECT, or a LIMIT OF THE RENDERER?

THE MECHANISM, STATED GENERALLY. A refusal names the thing that could not be done. It does
not, unless it is written to, name the REASON it could not be done -- and a reader,
INCLUDING US, will attribute a blank section to the input.

    "the Discussion -- the object records no interpretive text"
    "the Discussion -- this projector cannot render the text the object holds"

produce the SAME blank section and are OPPOSITE FINDINGS. On 2026-08-20 the first sentence
was on ARNI's projection while the object held seven authored paragraphs. It was quoted for
a week as evidence that OBJECTS lack substance. The true reason was that the paragraphs
carried `[[k]]`-style substitution tokens this projector could not resolve. Correcting it
moved the reproduction figure from ~11% to 26.2%.

SO EVERY REFUSAL IS CHECKED AGAINST THAT DISTINCTION. This is a bounded sweep: the
projector's refusal strings are finite and enumerable.

  OBJECT   -- names a fact about the input. "no per-trial estimates are stored".
  RENDERER -- names a limit here. "cannot be rendered by this projector".
  UNMARKED -- says only that something is absent, WITHOUT saying which side is at fault.
              These are the dangerous ones: they are read as OBJECT by default, and if the
              real cause is RENDERER the misreading is invisible and durable.

THIS IS A WARN, NOT A BLOCK. Whether an UNMARKED refusal is wrong depends on the object it
fires against, which this cannot know. It surfaces them for a human to read, which is the
same standing this project gives the empty-DataFrame rule.
"""
import io
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from instrument_controls import require_controls          # noqa: E402

TARGET = os.path.join(REPO, "ssot", "paper_projector.py")

# Phrases that ATTRIBUTE the absence to one side or the other.
OBJECT_WORDS = re.compile(
    r"no .{0,40}(?:is|are) (?:recorded|stored|held|carried)|does not carry|not on this "
    r"object|th(?:is|e) object (?:records|carries|holds|stores) no|is absent from|no field "
    r"of this object|carries no|holds none|records none|stores no|no .{0,30}stored", re.I)
RENDERER_WORDS = re.compile(
    r"cannot be rendered|this projector|the renderer|not rendered here|cannot be "
    r"resolved|no change to this projector|rendering one", re.I)


def refusals(src):
    """Every literal appended to a Section's refusals, with its line."""
    out = []
    for m in re.finditer(r"refusals\.append\(", src):
        seg = src[m.start():m.start() + 2200]
        depth, end = 0, None
        for i, ch in enumerate(seg):
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth == 0:
                    end = i
                    break
        block = seg[:end + 1] if end else seg
        strings = re.findall(r'"((?:[^"\\]|\\.)*)"', block)
        text = " ".join(strings).strip()
        if text:
            out.append((src[:m.start()].count("\n") + 1, text))
    return out


def classify(text):
    o = bool(OBJECT_WORDS.search(text))
    r = bool(RENDERER_WORDS.search(text))
    if o and r:
        return "BOTH"
    if r:
        return "RENDERER"
    if o:
        return "OBJECT"
    return "UNMARKED"


def main():
    gate = "--gate" in sys.argv
    require_controls(
        "audit_refusal_names_object_or_renderer",
        positive=("a refusal naming a renderer limit is classified RENDERER",
                  classify("the Discussion -- this projector cannot render it") == "RENDERER",
                  True),
        negative=("a refusal naming an object fact is classified RENDERER",
                  classify("the Discussion -- no interpretive text is recorded on this "
                           "object") == "RENDERER", True))

    # THE FOUNDING CASE, AS A KNOWN-ANSWER CONTROL. This exact sentence shipped on ARNI
    # while the object held seven authored paragraphs, so it must classify as making an
    # OBJECT claim -- it does, and it was WRONG. A classifier that cannot see the object
    # claim in the refusal that caused the incident is not measuring the incident.
    _founding = ("the Discussion -- this is a CONTENT gap. The object records no "
                 "interpretive text, and none is generated here: a discussion written by "
                 "the renderer would be an argument no field supports")
    if classify(_founding) not in ("OBJECT", "BOTH"):
        sys.exit("PROOF FAILED: the founding case classifies as %r, and it makes an "
                 "explicit claim about the object." % classify(_founding))
    print("    known-answer control: the founding ARNI refusal classifies as %s -- it DOES "
          "claim\n    something about the object, and on ARNI that claim was FALSE."
          % classify(_founding))

    src = io.open(TARGET, encoding="utf-8").read()
    rows = [(ln, classify(t), t) for ln, t in refusals(src)]
    if not rows:
        print("NOT_ASSESSABLE: no refusal literals were found in %s. That is a broken "
              "reader, not a clean file." % os.path.relpath(TARGET, REPO))
        return 2

    buckets = {}
    for ln, c, t in rows:
        buckets.setdefault(c, []).append((ln, t))

    print("")
    print("REFUSALS READ FROM %s: %d" % (os.path.relpath(TARGET, REPO), len(rows)))
    for c in ("OBJECT", "RENDERER", "BOTH", "UNMARKED"):
        print("   %-9s %d" % (c, len(buckets.get(c, []))))

    print("")
    print("UNMARKED -- says something is absent without saying WHICH SIDE is at fault.")
    print("A reader attributes these to the OBJECT by default. Where the real cause is the")
    print("RENDERER, the misreading is invisible and durable -- that is the ~11%% figure.")
    for ln, t in buckets.get("UNMARKED", []):
        print("   line %-5d %s" % (ln, t[:150]))

    print("")
    print("RENDERER -- correctly attributed, and these are the ones worth copying:")
    for ln, t in buckets.get("RENDERER", []) + buckets.get("BOTH", []):
        print("   line %-5d %s" % (ln, t[:150]))

    print("")
    print("WARN, NOT BLOCK. Whether an UNMARKED refusal is WRONG depends on the object it")
    print("fires against, which this file cannot know. It surfaces them to be read.")
    if gate:
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
