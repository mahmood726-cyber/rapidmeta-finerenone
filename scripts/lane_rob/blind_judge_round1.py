# -*- coding: utf-8 -*-
"""ROUND 1: our dapivirine page against the best published comparator, blind, three families.

⚠️ FORMAT IS A TELL, so both documents are rendered to PLAIN TEXT. Ours is styled HTML and the
comparator is extracted text; presenting them in different formats would let a judge identify
the newer document by its typography rather than its content, and every axis score would then
be partly a score of the stylesheet.

⚠️ CITING THE COMPARATOR IS ALSO A TELL. Our page cites Cochrane guidance on small-k intervals.
A document that cites Cochrane is presumably not Cochrane, so that phrase is neutralised along
with the branding. The regeneration command is removed for the same reason -- it identifies the
document as machine-generated.

PICO MATCHED: the comparator contributes only its DAPIVIRINE section, not the five-class parent
review. Judging our two-trial review against a five-class parent would be a PICO mismatch in our
favour, which is the mirror of the error we refuse elsewhere.

⛔ THE VERDICT IS PUBLISHED WHICHEVER WAY IT GOES, with the axes we lost on. Recorded here so
that condition is part of the instrument rather than a promise about it.

INTERNAL NOTE, WRITTEN BEFORE THE RUN so the result stays interpretable: two of the strongest
sections in our document -- the currency section and the clinical reading -- are HAND-WRITTEN
and have no component behind them yet. The verdict therefore measures our CEILING with those
written by hand, not what the recipe currently reaches.
"""
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
os.chdir(REPO)
sys.path.insert(0, HERE)
import blind_judge_control as C  # noqa: E402

OUT = C.OUT
OURS_HTML = "DAPIVIRINE_RING_PILOT_REVIEW.html"

# Tells specific to our document: the regeneration command, script paths, and the fact that it
# cites the comparator's own guidance.
# ⚠️ LINE-BOUNDED, NOT [^<]*. The first version used `Regenerate with[^<]*`, applied AFTER
# entity conversion -- so it ran from the stamp to the first `<` remaining in the text, which
# was the `P<0.001` in the age table far below, and DELETED THE ENTIRE MIDDLE OF THE DOCUMENT:
# the estimand statement, the included studies, the result, the absolute effects and the
# interval methods. The judges would have scored a truncated page and the round would have been
# void without anyone knowing why. Caught because the rendered output looked wrong, not by
# reading the pattern.
OUR_TELLS = [
    (re.compile("Regenerate with[^\n]*", re.I), "Regenerated from source data."),
    (re.compile(r"Systematic review · single comparison · pilot", re.I),
     "Systematic review · single comparison"),
    (re.compile(r"scripts?/[\w/]+\.py"), "the analysis script"),
    (re.compile(r"Cochrane'?s guidance", re.I), "standard methodological guidance"),
    (re.compile(r"\bCochrane\b", re.I), "a standard handbook"),
]


def ours_as_text():
    raw = io.open(OURS_HTML, encoding="utf-8").read()
    raw = re.sub(r"(?is)<style.*?</style>", " ", raw)
    # keep block structure as line breaks so the plain text is readable, not a wall
    raw = re.sub(r"(?i)</(h1|h2|h3|p|tr|li|div)>", "\n", raw)
    raw = re.sub(r"(?i)</t[dh]>", " | ", raw)
    t = re.sub(r"<[^>]+>", "", raw)
    t = (t.replace("&mdash;", "—").replace("&ndash;", "–").replace("&minus;", "−")
          .replace("&lt;", "<").replace("&gt;", ">").replace("&rsquo;", "'")
          .replace("&amp;", "&"))
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\n\s*\n\s*\n+", "\n\n", t)
    for pat, rep in OUR_TELLS:
        t = pat.sub(rep, t)
    return C.blind(t.strip())


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                                  line_buffering=True)
    os.makedirs(OUT, exist_ok=True)
    ours = ours_as_text()
    theirs = C.cochrane_dapivirine()
    print("ours   %6d chars   residual marks: %d" % (len(ours), len(C.BRAND.findall(ours))))
    print("theirs %6d chars   residual marks: %d" % (len(theirs), len(C.BRAND.findall(theirs))))
    for n, d in (("ours", ours), ("theirs", theirs)):
        io.open(os.path.join(OUT, "r1_%s.txt" % n), "w", encoding="utf-8").write(d)

    judges = [("codex", "", "openai", ("theirs", "ours")),
              ("agy", "gemini-3.1-pro-high", "google", ("ours", "theirs")),
              ("agy", "claude-opus-4-6-thinking", "anthropic", ("theirs", "ours"))]
    txt = {"ours": ours, "theirs": theirs}
    mapping = {}
    for worker, model, family, (a, b) in judges:
        tag = "r1_%s" % family
        p = os.path.join(OUT, "prompt_%s.txt" % tag)
        io.open(p, "w", encoding="utf-8").write(C.PROMPT % (txt[a], txt[b]))
        mapping[tag] = {"A": a, "B": b, "family": family, "worker": worker, "model": model}
        print("  %-16s A=%-6s B=%-6s prompt %d chars" % (tag, a, b, os.path.getsize(p)))
    json.dump(mapping, io.open(os.path.join(OUT, "r1_mapping.json"), "w",
                               encoding="utf-8"), indent=1)
    print("")
    print("position randomised: 2 judges see the comparator first, 1 sees ours first.")
    print("mapping -> r1_mapping.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
