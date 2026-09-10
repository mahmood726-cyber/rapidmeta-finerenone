# -*- coding: utf-8 -*-
r"""GATE: a vaccine/treatment EFFICACY percentage must never be computed as 1 - odds ratio.

THE DEFECT. Vaccine efficacy is 1 - RR, 1 - IRR, or 1 - HR. It is NEVER 1 - OR. The rotavirus
review pooled ODDS RATIOS and reported "~51% efficacy" as 1 - 0.4941. For an outcome that is
not rare that is a category error that biases the efficacy figure, and it manufactured the
very caveat the page was built around. The page is now withdrawn; this gate is what stops the
class returning on the next vaccine review the corpus grows.

WHAT IT FIRES ON, PRECISELY. A rendered page whose pooled MEASURE is OR and which also states
an efficacy PERCENTAGE that numerically equals (1 - pooled OR) x 100 within display rounding.
Both conditions are required: "efficacy" as the NAME of an outcome ("the efficacy outcome was
death") is not a finding, and a page reporting 1 - RR is correct and must pass. Requiring the
number to reconcile is what keeps this off the 19 corpus objects that merely pool OR and use
the word "efficacy".

FORWARD-LOOKING, AND THAT IS THE DESIGN, NOT A WEAKNESS. This is a vaccine-specific error; with
the one live instance withdrawn, the corpus offers nothing to find today. gate 21 makes the
same argument in full: a control anchored to a live defect retires the day it is fixed, so
discrimination is proven by SYNTHETIC pages every run -- one that computes 1 - OR (must fire),
one that computes 1 - RR (must not), one that pools OR but claims no efficacy percentage (must
not). The gate is VACUOUS unless all three are decided correctly and BROKEN if the positive
does not fire. It will still be able to fail long after the corpus stops giving it anything.

WITHDRAWAL NOTICES ARE EXEMPT. A page declaring pooled-estimate=NONE publishes no current
pool; the withdrawn rotavirus notice QUOTES its own 1 - OR error to explain the withdrawal,
and policing that quote would be a category error. Skipped by the meta tag, counted in kinds.

RATCHETED at whatever it finds live (0 today). A PASS means no NEW instance, never "clean".

Exit codes are the harness's: 0 PASS, 1 FAIL, 2 VACUOUS, 3 BROKEN.
"""
from __future__ import annotations

import glob
import html
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _harness as H                                                        # noqa: E402

FREEZE = "VE_FROM_ODDS_RATIO_BASELINE.json"
POOL_NONE_RE = re.compile(r'name="rapidmeta:pooled-estimate"\s+content="NONE"', re.I)
TAG_RE = re.compile(r"(?s)<[^>]+>")

# a pooled odds ratio stated as such
POOLED_OR_RE = re.compile(
    r"\bpooled\b[^.;<>]{0,40}?\b(?:OR|odds ratio)\b[^.;<>]{0,20}?(-?\d+\.\d+)"
    r"|\b(?:OR|odds ratio)\b[^.;<>]{0,20}?(-?\d+\.\d+)[^.;<>]{0,30}?\bpool", re.I)
# an efficacy PERCENTAGE (not "efficacy outcome")
EFFICACY_PCT_RE = re.compile(
    r"(?:(\d{1,2}(?:\.\d+)?)\s*%\s*(?:vaccine\s+)?efficac|"
    r"(?:vaccine\s+)?efficac\w*[^.;<>]{0,40}?(\d{1,2}(?:\.\d+)?)\s*%)", re.I)


def _text(src):
    return re.sub(r"\s+", " ", html.unescape(TAG_RE.sub(" ", src)))


def _pooled_ors(text):
    out = []
    for m in POOLED_OR_RE.finditer(text):
        v = m.group(1) or m.group(2)
        if v:
            out.append(float(v))
    return out


def _efficacy_pcts(text):
    out = []
    for m in EFFICACY_PCT_RE.finditer(text):
        v = m.group(1) or m.group(2)
        if v:
            out.append(float(v))
    return out


def page_ve_from_or(src):
    """Reason string if an efficacy % reconciles to 1-(pooled OR), else ''."""
    text = _text(src)
    ors = _pooled_ors(text)
    if not ors:
        return ""
    pcts = _efficacy_pcts(text)
    for orv in ors:
        implied = (1.0 - orv) * 100.0
        for pct in pcts:
            if abs(pct - implied) <= 1.0:            # display rounding tolerance
                return ("efficacy %.3g%% reconciles to 1-(pooled OR %.4g)=%.3g%% -- "
                        "efficacy is 1-RR/IRR/HR, never 1-OR" % (pct, orv, implied))
    return ""


# -- synthetic, permanent discrimination controls -----------------------------------
_POS = ("<p>Across three trials the pooled odds ratio was OR 0.4941 (0.35 to 0.70). "
        "This corresponds to a vaccine efficacy of 51%.</p>")
_NEG_RR = ("<p>Across three trials the pooled risk ratio was RR 0.4941 (0.35 to 0.70), "
           "a vaccine efficacy of 51% (1 - RR).</p>")
_NEG_NOPCT = ("<p>The pooled odds ratio was OR 0.4941 (0.35 to 0.70) for the primary "
              "efficacy outcome, severe gastroenteritis.</p>")


def main(argv):
    plant = "--plant" in argv
    gate = H.Gate("VE NOT FROM ODDS RATIO",
                  "a vaccine/treatment efficacy percentage is never computed as 1 - odds ratio")
    named = gate.expect_case(
        "discriminates",
        "three SYNTHETIC pages -- 1-OR efficacy (must fire), 1-RR efficacy (must not), OR "
        "pooled with no efficacy percentage (must not) -- decided correctly, every run")
    gate.requires_control()

    pos_fires = bool(page_ve_from_or(_POS))
    neg_rr_clean = not page_ve_from_or(_NEG_RR)
    neg_nopct_clean = not page_ve_from_or(_NEG_NOPCT)
    if pos_fires and neg_rr_clean and neg_nopct_clean:
        gate.saw(named)
    if not pos_fires:
        gate.broken("positive control did not fire -- the 1-OR detector is inert")
    fp = (0 if neg_rr_clean else 1) + (0 if neg_nopct_clean else 1)
    ex = ([] + ([] if neg_rr_clean else ["1-RR page flagged"])
          + ([] if neg_nopct_clean else ["OR-with-no-efficacy-% page flagged"]))
    gate.control(2, fp, ex, accuses=True)

    repo = H.repo_root()
    pages = sorted(glob.glob(os.path.join(repo, "*_REVIEW.html")))
    flagged, withdrawn = {}, 0
    for p in pages:
        src = open(p, encoding="utf-8", errors="replace").read()
        if POOL_NONE_RE.search(src):
            withdrawn += 1
            continue
        reason = page_ve_from_or(src)
        if reason:
            flagged[os.path.basename(p)] = reason

    if plant:
        flagged["__planted_ve_from_or__.html"] = "PLANT: efficacy 51% = 1-(OR 0.49)"

    gate.kinds({
        "*_REVIEW.html pages scanned": len(pages),
        "  withdrawal notices (pooled-estimate=NONE) -- exempt": withdrawn,
        "  efficacy % reconciles to 1-(pooled OR) -- the finding": len(flagged),
    })
    gate.coverage(len(pages) - withdrawn, len(pages),
                  "withdrawal notices quote their own 1-OR error to explain the withdrawal; "
                  "policing that quote would be a category error")

    new = H.ratchet(gate, FREEZE, sorted(flagged),
                    "rendered pages presenting an efficacy percentage computed as 1 - odds ratio",
                    escalated="out/ESCALATIONS.jsonl")
    for name in sorted(flagged):
        gate.note(("NEW " if name in new else "frozen ") + name + " -- " + flagged[name])
    for name in new:
        gate.finding("ve-from-or", "%s: %s" % (name, flagged[name]),
                     numerator=1, denominator=len(pages) - withdrawn)

    return gate.report(denominator="%d pages (%d exempt withdrawals)" % (len(pages), withdrawn))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
