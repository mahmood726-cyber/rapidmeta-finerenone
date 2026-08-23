"""Stored prose must not carry a punctuation seam. Five patterns, each proven on a planted defect.

# no-control: a source-shaped gate whose control is the planted-defect proof below -- each of
# the five patterns is run against a fixture that contains it and a fixture that does not, and
# the gate refuses to report on real data unless every pattern fires on its own defect and
# stays quiet on the clean text.

WHY THIS EXISTS. English lead-ins replaced bare field keys in stored prose on 2026-08-23, and
the join that had been correct for two days became wrong the moment the tail changed shape:

    "... on the dates recorded on each entry; This object's verification rests on ..."

A semicolon followed by a capital. 111 instances, none of which any check would have caught,
because every check in the repository was looking at WHICH WORDS appeared rather than at how
they were joined. Scanning for it also found 16 double full stops and a capitalised opener
embedded mid-clause -- "this review does not claim That any event count was checked" -- neither
of which anyone had reported.

THE GENERAL POINT: a change that alters the SHAPE of generated text invalidates every join
around it, and the joins are invisible in a diff of the generator. So the seams are asserted
over the corpus rather than reasoned about.

RUNS IN THE PRE-COMMIT CHAIN, over `ssot/**/*.json`, in about a second.
"""
from __future__ import annotations

import glob
import io
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# name -> (pattern, text that MUST match, text that MUST NOT)
def _lead_in_openers():
    """The first words of every lead-in, read from the map the fix itself uses.

    A BARE `;\\s+[A-Z]` IS NOT THE DEFECT AND THE FIRST VERSION OF THIS GATE SAID IT WAS. It
    flagged `antimalarial-act` on "... artemether-lumefantrine; Artesunate-amodiaquine against
    ..." -- a legitimate list of capitalised DRUG NAMES. A semicolon before a proper noun is
    ordinary English; a semicolon before a SENTENCE is the seam.

    So the pattern is keyed to the sentences that actually caused it, and read from
    `ssot/field_lead_ins.json` so the gate and the generator cannot drift -- the same rule that
    fixed the selector: define the population from the source the fix reads.
    """
    p = os.path.join(REPO, "ssot", "field_lead_ins.json")
    try:
        m = json.load(io.open(p, encoding="utf-8"))
    except Exception:
        return ["This object", "This review", "The bar", "The basis", "What this object"]
    out = []
    for spec in (m.get("by_key") or {}).values():
        for form in (spec.get("present"), spec.get("absent")):
            if isinstance(form, str) and form[:1].isupper():
                out.append(" ".join(form.split()[:2]).rstrip(":,"))
    return sorted(set(out)) or ["This object"]


_OPENERS = "|".join(re.escape(o) for o in _lead_in_openers())

SEAMS = {
    "semicolon then a lead-in sentence": (
        re.compile(r";\s+(?:%s)" % _OPENERS),
        "read on each entry; This object's verification rests on a record.",
        "artemether-lumefantrine; Artesunate-amodiaquine against chloroquine."),
    "double full stop": (
        re.compile(r"\.\s*\."),
        "at every registered rank.. This review does not claim anything.",
        "at every registered rank. This review does not claim anything."),
    "capitalised opener mid-clause": (
        re.compile(r"does not claim [A-Z]"),
        "This review does not claim That any event count was checked.",
        "This review does not claim that any event count was checked."),
    "stranded connective": (
        re.compile(r"(?:;|,)\s*\."),
        "the trials agreed; .",
        "the trials agreed."),
    "space before a full stop": (
        re.compile(r"\S\s+\."),
        "the estimate was pooled .",
        "the estimate was pooled."),
}

FIELDS = ("bookkeeping_2026_08_21", "manuscript")


def prove():
    """Every pattern fires on its own defect and stays quiet on the clean form."""
    bad = []
    for name, (pat, planted, clean) in SEAMS.items():
        if not pat.search(planted):
            bad.append("%s does not fire on its own planted defect" % name)
        if pat.search(clean):
            bad.append("%s fires on text that is clean" % name)
    if bad:
        sys.exit("PROOF FAILED, nothing reported:\n   " + "\n   ".join(bad))


def texts(o):
    for f in FIELDS:
        v = o.get(f)
        if isinstance(v, dict):
            for k, s in v.items():
                if isinstance(s, str) and not str(k).startswith("_"):
                    yield f + "." + str(k), s


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    prove()
    hits, read = [], 0
    for p in sorted(glob.glob(os.path.join(REPO, "ssot", "*", "*.json"))):
        t = os.path.basename(os.path.dirname(p))
        if os.path.basename(p) != t + ".json":
            continue
        try:
            o = json.load(io.open(p, encoding="utf-8"))
        except ValueError:
            continue
        read += 1
        for where, s in texts(o):
            for name, (pat, _pl, _cl) in SEAMS.items():
                m = pat.search(s)
                if m:
                    hits.append((t, where, name,
                                 re.sub(r"\s+", " ", s[max(0, m.start() - 50):m.start() + 40])))
    print("GRAMMAR SEAMS in stored prose, %d object(s)   (proof passed: every pattern fires "
          "on its planted defect)" % read)
    if not hits:
        print("   none.")
        return
    seen = set()
    for t, where, name, ctx in hits[:20]:
        print("   %-28s %-42s %s" % (t[:28], where[:42], name))
        if name not in seen:
            print("        ...%s..." % ctx.strip())
            seen.add(name)
    sys.exit("REFUSED: %d grammar seam(s) in stored prose. A change that alters the SHAPE of "
             "generated text invalidates the joins around it, and the joins are invisible in "
             "a diff of the generator." % len(hits))


if __name__ == "__main__":
    main()
