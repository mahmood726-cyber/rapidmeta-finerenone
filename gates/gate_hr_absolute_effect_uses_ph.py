# -*- coding: utf-8 -*-
"""GATE: an absolute risk reduction derived from a HAZARD RATIO must use the proportional-hazards
conversion, never the risk-ratio form B*(1-HR).

Defect (2026-09-07, reviewer-found, and it had owner endorsement): the generator rendered
ARR = B*(1-HR), which treats a hazard ratio as a risk ratio. Under proportional hazards the treated
risk at a horizon is 1-(1-B)^HR, so ARR = B - [1-(1-B)^HR]. At B=0.20, HR=0.77 the wrong form gives
4.58% (NNT 22) and the correct one 4.20% (NNT 24). Declaring the formula transparently does not make it
correct; this gate makes the error impossible to reship.

Two legs, because pages differ:
  NUMERIC  when the page states a baseline B and a numeric ARR for an HR, recompute BOTH forms; if the
           stated ARR matches the risk-ratio form B*(1-HR) and not the PH form, that is the defect -> FAIL.
  FORMULA  when the page states no baseline (ours declares none), the absolute-effect prose for an HR
           must present the PH form (1-(1-B)^HR) and must NOT present B*(1-HR) as THE ARR.
Registered in run_all.py (gate 8: a gate nothing runs is VACUOUS).
"""
from __future__ import annotations
import io, os, re, json, glob, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _harness as H  # noqa: E402

_EMBED = re.compile(r'<script[^>]*id="ssot-current"[^>]*>(.*?)</script>', re.S | re.I)
_ABS_SECTION = re.compile(r'<h2>[^<]*[Aa]bsolute effect.*?(?=<h2>|<script|\Z)', re.S)
# "baseline risk of 20.0% ... absolute risk reduction of 4.58 percentage points"
_NUMERIC = re.compile(r'baseline risk of\s*([0-9.]+)\s*%.*?absolute risk reduction of\s*([0-9.]+)\s*percentage', re.S | re.I)


def _measure(page_html):
    m = _EMBED.search(page_html)
    if not m:
        return None
    try:
        obj = json.loads(m.group(1).replace("<\\/", "</"))
    except Exception:
        return None
    for o in ((obj.get("results") or {}).get("by_outcome") or {}).values():
        pooled = (o or {}).get("pooled") or {}
        if pooled.get("point") is not None:
            return str(pooled.get("measure") or o.get("measure") or "").upper(), float(pooled["point"])
    return None


def check_page(page_html):
    """('OK'|'FAIL'|'NA', detail). NA = not an HR page / no absolute-effect section to judge."""
    mi = _measure(page_html)
    if not mi or mi[0] != "HR":
        return "NA", {"reason": "not an HR page"}
    hr = mi[1]
    sec = _ABS_SECTION.search(page_html)
    if not sec:
        return "NA", {"reason": "no absolute-effect section"}
    text = sec.group(0)
    # NUMERIC leg
    nm = _NUMERIC.search(re.sub(r"<[^>]+>", " ", text))
    if nm:
        b = float(nm.group(1)) / 100.0
        stated = float(nm.group(2)) / 100.0
        wrong = b * (1 - hr)
        correct = b - (1 - (1 - b) ** hr)
        if abs(stated - wrong) < 5e-4 and abs(stated - correct) > 5e-4:
            return "FAIL", {"leg": "numeric", "baseline": b, "stated_arr": stated,
                            "risk_ratio_form": round(wrong, 4), "ph_form": round(correct, 4)}
        return "OK", {"leg": "numeric", "stated_arr": stated, "ph_form": round(correct, 4)}
    # FORMULA leg: PH marker must be present; the naive risk-ratio ARR must not be the stated form.
    flat = re.sub(r"<[^>]+>", "", text)
    ph_present = ("(1-(1-B)" in flat.replace("&minus;", "-").replace(" ", "")
                  or "1-(1-B)" in flat.replace("&minus;", "-").replace(" ", ""))
    naive_as_arr = re.search(r'ARR\s*=\s*B\s*[x×*]\s*\(\s*1\s*[-−]\s*(HR|effect)', flat, re.I)
    if not ph_present or naive_as_arr:
        return "FAIL", {"leg": "formula", "ph_present": ph_present,
                        "naive_as_arr": bool(naive_as_arr)}
    return "OK", {"leg": "formula"}


# Synthetic controls, pinned in code.
_EMBED_HR = ('<script type="application/json" id="ssot-current">'
             '{"results":{"by_outcome":{"primary":{"pooled":{"point":0.77,"measure":"HR","ci_low":0.70,"ci_high":0.85}}}}}</script>')
_SYNTH_BAD = ('<h2>Absolute effect</h2><p>At a baseline risk of 20.0%, this HR of 0.77 implies an '
              'absolute risk reduction of 4.58 percentage points (NNT 22).</p>' + _EMBED_HR)
_SYNTH_OK = ('<h2>Absolute effect</h2><p>At a baseline risk of 20.0%, this HR of 0.77 implies an '
             'absolute risk reduction of 4.20 percentage points (NNT 24), by the HR conversion.</p>' + _EMBED_HR)


def controls():
    return check_page(_SYNTH_BAD)[0] == "FAIL", check_page(_SYNTH_OK)[0] == "OK"


def main(argv):
    gate = H.Gate("HR ABSOLUTE EFFECT USES PROPORTIONAL HAZARDS",
                  "an ARR from a hazard ratio uses 1-(1-B)^HR, never the risk-ratio form B*(1-HR)")
    named = gate.expect_case("__synthetic_risk_ratio_form__",
                             "a page stating ARR = B*(1-HR) for an HR must be flagged")
    gate.requires_control()
    pos, neg = controls()
    if pos:
        gate.saw(named)
    gate.control(1, 0 if neg else 1, [] if neg else ["correct PH-form page was flagged"], accuses=True)
    if not pos:
        gate.broken("the positive control (stated 4.58% = B*(1-HR)) did NOT fire")

    repo = H.repo_root()
    pages = sorted(glob.glob(os.path.join(repo, "out", "generated", "*.html")))
    checked = 0
    na = 0
    for p in pages:
        try:
            html = io.open(p, encoding="utf-8", errors="replace").read()
        except Exception:
            continue
        v, d = check_page(html)
        if v == "OK":
            checked += 1
        elif v == "FAIL":
            gate.finding(os.path.basename(p), "HR page derives ARR by the risk-ratio form (%s)" % d)
        else:
            na += 1
    gate.kinds({"HR page CHECKED (ARR uses PH)": checked,
                "HR page FAIL (risk-ratio form)": gate.n_findings(),
                "not an HR absolute-effect page": na})
    gate.coverage(checked + gate.n_findings(), len(pages),
                  "%d generated page(s) are not HR absolute-effect pages" % na)
    return gate.report(denominator="%d generated page(s) under out/generated/" % len(pages))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
