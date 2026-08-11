#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""Brace-matched extraction of the per-page data spans, and a fail-closed check.

WHY THIS EXISTS. corpus_wave.py's guard 2 declares that realData, allOutcomes,
outcomeKeys, TRIALS, evidence and AUTO_INCLUDE_TRIAL_IDS are byte-identical across a
wave. It implemented that with six regexes. Three of them -- `realData=\{.*?\n`,
`window.RapidMeta.outcomeKeys\s*=\s*\{...\};` and `\bTRIALS\s*=\s*\[...\];` -- match
ZERO times on all 863 pages, because the corpus writes `realData:{"NCT..."` as an object
PROPERTY, not as an assignment.

A span that matches nothing contributes (0, 0, 0) to the fingerprint on both sides of the
edit. It therefore always compares equal. The guard could not fail for those spans, and
the strongest claim in the whole safety model -- "the extracted trial records cannot be
corrupted, and here is the mechanical proof" -- was being carried by the three spans that
did match. realData, the primary per-page trial data, was not among them.

So: brace-matched extraction, which does not care how the value is introduced, plus
`require=True`, which makes a span that is expected and absent an ERROR rather than a
silent pass. A gate that cannot fail is not a gate.

Usage:
    python data_spans.py PAGE.html                 # show what is found
    python data_spans.py --verify-git origin/main  # every page, before vs after
"""
from __future__ import annotations

import argparse
import io
import pathlib
import subprocess
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# name -> (introducer literal, opening bracket, required-on-every-template-page)
#
# The `required` column is measured, not assumed: each of the five marked True was
# confirmed present on 863/863 eligible pages. TRIALS is marked False because it is
# present on ZERO of them -- the constant does not exist in this corpus, and demanding
# it would make every page fail for the absence of something that was never there.
# That distinction is the entire point: a span that is expected and missing is an
# error, and a span that was never part of this lineage is not.
SPANS = [
    ("realData",     'realData:',                    "{", True),
    ("allOutcomes",  'allOutcomes:',                 "[", True),
    ("outcomeKeys",  'outcomeKeys',                  "{", True),
    ("TRIALS",       'TRIALS',                       "[", False),
    ("evidence",     'evidence:',                    "[", True),
    ("AUTO_INCLUDE", 'AUTO_INCLUDE_TRIAL_IDS',       "[", True),
]

CLOSING = {"{": "}", "[": "]"}


def _match_from(s: str, i: int, opener: str) -> int:
    """Index just past the bracket group starting at s[i] == opener.

    String- and escape-aware: the corpus data is full of braces and brackets inside
    quoted titles, and a naive depth counter closes the object in the middle of one.
    """
    closer = CLOSING[opener]
    depth = 0
    quote = None
    n = len(s)
    while i < n:
        c = s[i]
        if quote:
            if c == "\\":
                i += 2
                continue
            if c == quote:
                quote = None
        elif c in "\"'":
            quote = c
        elif c == opener:
            depth += 1
        elif c == closer:
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    return -1


def extract(s: str) -> dict:
    """name -> list of raw span texts (possibly empty)."""
    out = {}
    for name, lit, opener, _req in SPANS:
        spans = []
        start = 0
        while True:
            j = s.find(lit, start)
            if j < 0:
                break
            k = s.find(opener, j)
            # The opener must follow closely, or this is an unrelated mention of the
            # name. The tolerance is 14 rather than 4 because AUTO_INCLUDE_TRIAL_IDS
            # is introduced as `= new Set([`, which puts 11 characters between the
            # name and its bracket. At 4 it silently found nothing -- the same class
            # of failure this module exists to fix.
            if k < 0 or k - (j + len(lit)) > 14:
                start = j + len(lit)
                continue
            end = _match_from(s, k, opener)
            if end < 0:
                start = j + len(lit)
                continue
            spans.append(s[k:end])
            start = end
        out[name] = spans
    return out


def fingerprint(s: str):
    """(fingerprint, missing_required). A missing required span is an error."""
    ex = extract(s)
    fp = {}
    missing = []
    for name, _lit, _op, req in SPANS:
        hits = ex[name]
        fp[name] = (len(hits), sum(len(h) for h in hits),
                    hash(tuple(hits)) if hits else 0)
        if req and not hits:
            missing.append(name)
    return fp, missing


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("page", nargs="?")
    ap.add_argument("--verify-git", metavar="REF",
                    help="compare every eligible page's data spans against REF")
    ap.add_argument("--root", default=".")
    a = ap.parse_args()

    root = pathlib.Path(a.root).resolve()

    if a.verify_git:
        sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
        import corpus_wave as W
        import corpus_detectors as CD
        names = []
        for p in sorted(root.glob("*.html")):
            if W.is_excluded(p.name):
                continue
            t = p.read_text(encoding="utf-8", errors="replace")
            if CD.is_template_page(t):
                names.append(p.name)
        print(f"verifying {len(names)} pages against {a.verify_git}\n")
        changed, missing_now, absent_ref, ok = [], [], [], 0
        for i, n in enumerate(names, 1):
            cur = (root / n).read_text(encoding="utf-8", errors="replace")
            r = subprocess.run(["git", "show", f"{a.verify_git}:{n}"], cwd=str(root),
                               capture_output=True)
            if r.returncode != 0:
                absent_ref.append(n)
                continue
            ref = r.stdout.decode("utf-8", errors="replace")
            fa, ma = fingerprint(cur)
            fb, _mb = fingerprint(ref)
            if ma:
                missing_now.append((n, ma))
            if fa != fb:
                diff = [k for k in fa if fa[k] != fb[k]]
                changed.append((n, diff))
            else:
                ok += 1
            if i % 200 == 0:
                print(f"  {i}/{len(names)}...")
        print(f"\nidentical      {ok}")
        print(f"CHANGED        {len(changed)}")
        for n, d in changed[:25]:
            print(f"   {n}: {d}")
        print(f"missing span   {len(missing_now)}")
        for n, d in missing_now[:15]:
            print(f"   {n}: {d}")
        print(f"absent in ref  {len(absent_ref)}")
        return 1 if (changed or missing_now) else 0

    s = pathlib.Path(a.page).read_text(encoding="utf-8", errors="replace")
    ex = extract(s)
    for name, _l, _o, req in SPANS:
        hits = ex[name]
        tot = sum(len(h) for h in hits)
        flag = "  <-- REQUIRED AND ABSENT" if (req and not hits) else ""
        print(f"  {name:14s} n={len(hits):3d}  bytes={tot:9,d}{flag}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
