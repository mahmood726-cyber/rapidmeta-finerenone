"""Second-stage APIXABAN_ACS fixes - both found by rendering the page, not by the file gate.

R1. The prediction-interval cell is guarded by `k>=3` but its fallback text reads
    "N/A (k < 2)". At the corrected k=2 that label is a false statement on a live
    page. Same off-by-one in the QA7 checklist row. The HKSJ cell's identical
    string is CORRECT (its guard really is k<2) and is left alone.

R2. The page's own analysis panel flags "Discordant: consider HKSJ more reliable
    for small k" - the HKSJ-adjusted interval crosses 1 while the primary
    interval does not. A badge claiming nominal significance without saying so
    would contradict the page it sits on. Disclosed in the badge.
"""
import io
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

FULL = "APIXABAN_ACS_AUTO_FULL_REVIEW.html"

s = open(FULL, encoding="utf-8").read()
before = len(s)
done = []

# ---- R1a: the res-pi fallback label ---------------------------------------
old = (
    'document.getElementById("res-pi").innerText=c.k>=3&&Number.isFinite(c.piLCI)?'
    '`${c.piLCI.toFixed(2)} — ${c.piUCI.toFixed(2)}`:"N/A (k < 2)"'
)
assert s.count(old) == 1, f"res-pi anchor count = {s.count(old)}"
s = s.replace(
    old,
    'document.getElementById("res-pi").innerText=c.k>=3&&Number.isFinite(c.piLCI)?'
    '`${c.piLCI.toFixed(2)} — ${c.piUCI.toFixed(2)}`:"N/A (k < 3)"',
    1,
)
done.append('res-pi fallback label "N/A (k < 2)" -> "N/A (k < 3)" (guard is k>=3)')

# ---- R1b: the QA7 checklist detail ----------------------------------------
old = '"PI: "+r.piLCI+"—"+r.piUCI:"Not available (k < 2)"'
assert s.count(old) == 1, f"QA7 anchor count = {s.count(old)}"
s = s.replace(old, '"PI: "+r.piLCI+"—"+r.piUCI:"Not available (k < 3)"', 1)
done.append('QA7 detail "Not available (k < 2)" -> "(k < 3)"')

# ---- R2: HKSJ discordance disclosed in the badge --------------------------
anchor = (
    "At k=2, publication bias, small-study effects and "
    "prediction intervals are not assessable."
)
assert s.count(anchor) == 1, f"badge limits anchor count = {s.count(anchor)}"
s = s.replace(
    anchor,
    "At k=2, publication bias, small-study effects and prediction intervals are not "
    "assessable. <strong>The significance is fragile and the page says so:</strong> the "
    "HKSJ-adjusted interval (t with df=k&minus;1=1) is 0.03&ndash;124.7 and <em>crosses "
    "1</em>, the analysis panel flags the discordance, and the fragility index is "
    "<strong>1</strong> &mdash; a single event overturns nominal significance. The "
    "direction (harm) is robust and is corroborated independently by APPRAISE-2&rsquo;s "
    "TIMI major bleeding HR 2.59 (1.50&ndash;4.46); the <em>p-value</em> is not robust. "
    "The on-page panel pools by inverse-variance random effects (&tau;&sup2;=0, so DL and "
    "Paule-Mandel coincide) and reads 1.97 (1.04&ndash;3.74); the Mantel-Haenszel figure "
    "quoted above is 1.975 (1.041&ndash;3.746). They agree to the displayed precision.",
    1,
)
done.append("badge discloses HKSJ discordance, FI=1, and the two estimators' agreement")

open(FULL, "w", encoding="utf-8", newline="").write(s)
print(f"{FULL}: {before} -> {len(s)} bytes")
for d in done:
    print("  -", d)
