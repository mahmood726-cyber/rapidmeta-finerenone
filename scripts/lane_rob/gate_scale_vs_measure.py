# -*- coding: utf-8 -*-
"""GATE: a ratio measure must never be rendered "on the natural scale".

TWO INSTRUMENTS, DIFFERENT OWNERS, DIFFERENT LAYERS -- and the distinction matters, because
"it's guarded" meaning two different things is how a class comes back.

  chk_scale_vs_measure   lives in the blind-review harness at F:/claude-temp/blind-review.
                         A DETECTOR. It reads served bytes from outside and reports a
                         regression after the fact. It is not in this repository and cannot
                         block anything here.

  this gate              lives in the projector repository. A GATE. It runs against
                         delivered pages in the tree and refuses, and its fix commit is
                         registered on REQUIRED_GENERATOR_COMMITS so no rebuilt page can
                         ship without the derive-or-refuse patch.

WHAT IT CATCHES. `outcome.get('effect_scale', 'natural')` defaulted to the MINORITY value --
stored corpus-wide as log 70, natural 10, linear 2, none 1 -- so an absent field rendered as
the less likely truth. On sglt2-hf's harmonised_cvdeath_or_hhf, which stores measure HR and
no scale, the page said "reported on the natural scale". A hazard ratio is a log-scale
quantity, and both sibling outcomes on that page store 'log', so the page contradicted itself
across three rows.

READ-ONLY. Verdict on stdout, never in the exit status alone.
"""
import glob
import html
import io
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                              line_buffering=True)
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
os.chdir(REPO)

RATIO = r"(HR|OR|RR|IRR|SHR|SMR)"
# The rendered sentence pairs a measure with a scale within one table row.
NATURAL = re.compile(r"(pooled|combined|reported)\s+on the natural scale", re.I)
# ANCHORED ON BOTH SIDES, AND EVERY MATCH REPORTED RATHER THAN THE FIRST. The first version
# wrote RATIO + r"\b" with no LEADING boundary, so a ratio token could match inside a longer
# uppercase word, and it named whichever matched first. On SGLT2_HF it reported the measure
# as "OR" while the object stores "HR" -- the right page found on the wrong evidence, which
# is the same name-versus-identifier failure as the acronym-to-NCT mapping.
MEASURE_NEAR = re.compile(r"\b" + RATIO + r"\b")


def rendered(raw):
    t = re.sub(r"(?is)<(script|style).*?</\1>", " ", raw)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", t)))


def scan(pages):
    bad, seen = [], 0
    for p in sorted(pages):
        try:
            t = rendered(open(p, "rb").read().decode("utf-8", "replace"))
        except OSError:
            continue
        hits = list(NATURAL.finditer(t))
        if not hits:
            continue
        seen += 1
        for m in hits:
            # the measure is named in the same row, within a short window
            window = t[max(0, m.start() - 320):m.end() + 120]
            found = sorted(set(MEASURE_NEAR.findall(window)))
            if found:
                bad.append((p, "/".join(found), re.sub(r"\s+", " ", window[-170:])))
    return seen, bad


def main():
    argv = [a for a in sys.argv[1:] if not a.startswith("-")]
    pages = argv or glob.glob("*.html")
    seen, bad = scan(pages)
    print("")
    print("GATE -- a ratio measure rendered 'on the natural scale'")
    print("")
    print("  pages examined                                %4d  == the denominator"
          % len(pages))
    print("  pages saying 'on the natural scale' at all    %4d" % seen)
    print("  of those, beside a ratio measure              %4d" % len({p for p, _, _ in bad}))
    print("")
    for p, meas, ctx in bad[:20]:
        print("   REFUSE  %-40s measure %s" % (p[:40], meas))
        print("           ...%s" % ctx[-140:])
    print("")
    if bad:
        print("VERDICT: REFUSED. %d page(s) state a natural scale for a ratio measure, "
              "which is a log-scale quantity." % len({p for p, _, _ in bad}))
        return 1
    print("VERDICT: PASS. No page pairs a ratio measure with a natural-scale claim.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
