#!/usr/bin/env python3
"""Unsubstituted template tokens in SSOT prose -- `{res.by_outcome...i2}` left in a sentence.

FOUND ON alirocumab-lipid, 2026-08-19, in prose the page renders:

    "Between-trial variation is high: I-squared is
     {res.by_outcome.ldlc_pct_change_wk24.heterogeneity.i2} per cent."

The token was never substituted. Ten in that object; 27 across three topics.

LATENT, NOT LIVE, AND THE DISTINCTION IS STATED RATHER THAN BLURRED: the current page builder
resolves or drops these, so no shipped page carries one today -- checked, not assumed. That
makes this a defect in the SSOT rather than in the rendering, which is worse in one specific
way: THE OBJECT IS THE SOURCE OF TRUTH, and any second consumer written against it would leak
what the first consumer happens to hide.

A RATCHET, because the three known topics need their prose rewritten with real values, which is
per-topic work and not a lint's job. The known set is baselined and ANY NEW ONE REFUSES.
"""
import io
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SSOT = os.path.join(REPO, "ssot")
BASELINE = 2          # covid19-vaccines, prevnar15-pneumo
# TIGHTENED from 3 on 2026-08-19 when alirocumab-lipid's tokens were substituted.
# A ratchet that never tightens is a ceiling, not a ratchet: it would let a future
# regression re-fill the slot the fix just emptied.

# A dotted path inside braces. Deliberately NOT matching `{}` or `{0}` or JSON-ish braces:
# the signature is a FIELD PATH left in a sentence.
TOKEN = re.compile(r"\{[a-zA-Z_][\w]*(?:\.[\w]+)+\}")


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    hits, scanned = [], 0
    for d in sorted(os.listdir(SSOT)):
        p = os.path.join(SSOT, d, d + ".json")
        if not os.path.exists(p):
            continue
        scanned += 1
        try:
            blob = io.open(p, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        toks = sorted(set(TOKEN.findall(blob)))
        if toks:
            hits.append((d, toks))

    for d, toks in hits:
        print("%s  %d unsubstituted token(s)" % (d, len(toks)))
        for t in toks[:4]:
            print("      %s" % t)
        if len(toks) > 4:
            print("      ... and %d more" % (len(toks) - 4))
    print()
    print("topic objects scanned        %d" % scanned)
    print("with unsubstituted tokens    %d   (baseline %d)" % (len(hits), BASELINE))
    if len(hits) > BASELINE:
        print()
        print("REFUSED: %d topic(s) carry unsubstituted template tokens, above the baseline "
              "of %d." % (len(hits), BASELINE))
        print("FIX: substitute the value, or delete the sentence. A field path is not prose.")
        return 1
    if hits:
        print()
        print("HELD at baseline: %d known topic(s), listed above rather than hidden. Their "
              "prose needs rewriting with real values; any NEW one refuses." % len(hits))
    print()
    print("NOT CHECKED: whether a substituted value is CORRECT. This finds the token that was")
    print("never filled, not the number that was filled wrongly.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
