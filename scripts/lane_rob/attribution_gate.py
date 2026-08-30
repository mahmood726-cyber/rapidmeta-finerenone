# -*- coding: utf-8 -*-
"""Does a verdict attribute to a document a property that document does not have?

⛔ THE GROUNDING GATE CHECKS QUOTED STRINGS AND MISSED THIS ENTIRELY. A judge credited our page
with cautioning that "real-world effectiveness will be lower than trial efficacy due to
adherence factors". The page never says it -- `real world` and `in practice` occur ZERO times --
and the sentence carried no quotation marks, so nothing checked it.

⚠️ AND IT WAS AN OVER-CREDIT INSIDE A VERDICT IN OUR FAVOUR. A gate that only catches criticism
is not a gate; it is a lawyer. This one is deliberately run against praise as well, because a
hallucinated virtue inflates a result we intend to publish.

WHAT IT MEASURES, AND WHAT IT CANNOT. It takes each sentence attributing something to A or to B,
extracts DISTINCTIVE technical terms, and asks whether each is present in that document. It
therefore catches attributed VOCABULARY, not attributed MEANING: a judge that paraphrases a real
property in entirely different words is not caught, and a judge that uses a term the document
uses in a different sense is not caught either. It is a floor on the error rate, never a ceiling.
"""
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(os.path.dirname(HERE)), "wt-regen", "out", "judge-r3")
if not os.path.isdir(OUT):
    OUT = os.path.join(os.getcwd(), "out", "judge-r3")

# Terms that are claims ABOUT a document's content rather than generic review vocabulary.
STOP = set("""document better because whereas while these those which their there other
report reports reported reporting provide provides provided including included include
analysis analyses review reviews trial trials study studies result results evidence
outcome outcomes clinical however although explicit explicitly clearly overall
between across within about above below given single common general specific
""".split())


def terms(sentence):
    """Distinctive multi-word and technical terms a sentence attributes."""
    out = set()
    for m in re.finditer(r"\b([a-z]{4,}[- ][a-z]{4,}(?:[- ][a-z]{4,})?)\b", sentence.lower()):
        p = m.group(1)
        if not any(w in STOP for w in re.split(r"[- ]", p)):
            out.add(p)
    return out


def norm(s):
    return re.sub(r"[^a-z0-9 ]", " ", re.sub(r"\s+", " ", (s or "").lower())).strip()


def check(verdict, ours, theirs, mapping):
    """-> list of (which_doc, sentence, unlocatable_terms)."""
    docs = {"a": norm(ours if mapping["A"] == "ours" else theirs),
            "b": norm(ours if mapping["B"] == "ours" else theirs)}
    bad = []
    for sent in re.split(r"(?<=[.!?])\s+", verdict):
        s = sent.strip()
        if len(s) < 40:
            continue
        # sentences naming exactly ONE document, so the attribution is unambiguous
        na = len(re.findall(r"\b(?:document\s+)?A\b", s))
        nb = len(re.findall(r"\b(?:document\s+)?B\b", s))
        if (na > 0) == (nb > 0):
            continue
        which = "a" if na else "b"
        miss = sorted(t for t in terms(s) if norm(t) not in docs[which])
        # a sentence is only flagged when it attributes SEVERAL absent terms; one stray
        # bigram is the judge's own phrasing, not a claim about the document
        if len(miss) >= 3:
            bad.append((which.upper(), s[:150], miss[:6]))
    return bad


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    import json
    mapping = json.load(io.open(os.path.join(OUT, "r3_mapping.json"), encoding="utf-8"))
    ours = io.open(os.path.join(OUT, "r3_ours.txt"), encoding="utf-8").read()
    theirs = io.open(os.path.join(OUT, "r3_theirs.txt"), encoding="utf-8").read()
    print("ATTRIBUTION GATE -- properties a verdict assigns to a document that it does not have")
    print("")
    n_with = 0
    for tag, m in sorted(mapping.items()):
        p = os.path.join(OUT, "%s.txt" % tag)
        if not os.path.exists(p):
            continue
        v = io.open(p, encoding="utf-8", errors="replace").read()
        bad = check(v, ours, theirs, m)
        n_with += bool(bad)
        print("  %-26s %d sentence(s) with >=3 unlocatable attributed terms" % (tag, len(bad)))
        for which, s, miss in bad[:2]:
            print("      -> about %s: %s" % (which, s[:110]))
            print("         absent from it: %s" % ", ".join(miss))
    print("")
    print("  VERDICTS WITH AT LEAST ONE UNLOCATABLE ATTRIBUTION: %d of %d"
          % (n_with, sum(1 for t in mapping if os.path.exists(os.path.join(OUT, "%s.txt" % t)))))
    print("  \u26a0\ufe0f This is a property of the JUDGES, not of either document, and it is a")
    print("     FLOOR: paraphrased attributions are invisible to a vocabulary check.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
