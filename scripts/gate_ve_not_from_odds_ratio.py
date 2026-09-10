#!/usr/bin/env python3
"""GATE: vaccine efficacy must not be computed as 1 - OR.

WHY THIS EXISTS. ROTAVIRUS_VACCINE_AFRICA_REVIEW published "roughly 51% efficacy" as
1 - 0.4941, where 0.4941 is a pooled ODDS RATIO. Vaccine efficacy is 1 - RR, 1 - IRR or
1 - HR, NEVER 1 - OR: the registry record we read even states the measure explicitly
(paramType "Efficacy = 1-Relative Risk"), and two of the three trials computed efficacy
from person-time incidence rates. Reading the field and then pooling an odds ratio, then
subtracting it from 1, is a category error that biases the efficacy figure.

THE RULE. If a review's served page presents a VACCINE-EFFICACY / "% efficacy" claim, its
pooled effect measure MUST be RR, IRR or HR -- not OR. A page that presents efficacy while
the object pools an odds ratio is flagged.

MEASURED PRECISION. Routed through instrument_controls.require_controls with a real
positive (rotavirus: efficacy claim + measure OR -> MUST flag) and a real negative (a
measure-OR review that makes NO efficacy claim -> must NOT flag). Prints that it EXECUTED.
"""
import glob
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "scripts"))
from instrument_controls import require_controls, ControlFailed  # noqa: E402

VE_RX = re.compile(r"\befficac(?:y|ies)\b", re.I)
PCT_RX = re.compile(r"\d{1,3}\s?%\s*(?:efficac|vaccine efficac)|efficac[^.]{0,40}?\d{1,3}\s?%", re.I)


def _pooled_measure(obj):
    try:
        return obj["results"]["by_outcome"]["primary"]["pooled"].get("measure")
    except Exception:
        m = obj.get("outcomes") or []
        return (m[0].get("measure") if m and isinstance(m[0], dict) else None)


def page_for(objpath):
    # PAGE_MAP maps page -> object; invert to find the served page for this object.
    pm = json.load(open(os.path.join(REPO, "ssot", "PAGE_MAP.json"), encoding="utf-8"))
    rel = os.path.relpath(objpath, REPO).replace("\\", "/")
    for page, op in pm.items():
        if op.replace("\\", "/") == rel:
            p = os.path.join(REPO, page)
            return page, (open(p, encoding="utf-8", errors="replace").read()
                          if os.path.exists(p) else "")
    return None, ""


def flags(objpath):
    """True if this review presents a vaccine-efficacy claim while pooling an OR."""
    try:
        obj = json.load(open(objpath, encoding="utf-8"))
    except Exception:
        return False
    if (_pooled_measure(obj) or "").upper() != "OR":
        return False
    page, html = page_for(objpath)
    if not html:
        return False
    return bool(PCT_RX.search(html)) or (bool(VE_RX.search(html))
                                         and "vaccine" in html.lower())


def main():
    objs = sorted(glob.glob(os.path.join(REPO, "ssot", "*", "*.json")))
    print("EXECUTED gate_ve_not_from_odds_ratio over %d ssot objects." % len(objs))

    roto = [o for o in objs if "rotavirus-vaccine-africa" in o.replace("\\", "/")]
    # a real measure-OR review that makes no efficacy claim, as the negative control:
    neg = None
    for o in objs:
        if "rotavirus" in o.replace("\\", "/"):
            continue
        try:
            m = (_pooled_measure(json.load(open(o, encoding="utf-8"))) or "").upper()
        except Exception:
            continue
        if m == "OR":
            _, h = page_for(o)
            if h and not PCT_RX.search(h) and not VE_RX.search(h):
                neg = o
                break
    try:
        require_controls(
            "ve-not-from-or",
            positive=("ROTAVIRUS_VACCINE_AFRICA (efficacy claim + pooled OR) is flagged",
                      bool(roto) and flags(roto[0]), True),
            negative=(("%s (measure OR, no efficacy claim) is flagged"
                       % (os.path.basename(os.path.dirname(neg)) if neg else "none")),
                      flags(neg) if neg else False, True))
    except ControlFailed as exc:
        print(str(exc))
        return 1

    hits = [o for o in objs if flags(o)]
    print("FINDINGS: %d review(s) present vaccine efficacy while pooling an odds ratio:" % len(hits))
    for o in hits:
        print("  FAIL: %s -- VE presented but pooled measure is OR; VE is 1-RR/IRR/HR, never 1-OR."
              % os.path.basename(os.path.dirname(o)))
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
