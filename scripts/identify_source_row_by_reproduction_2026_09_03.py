"""IDENTIFY A SOURCE ROW BY REPRODUCING THE STORED VALUE FROM IT.

THE METHOD, NAMED. A stored estimate says it came from a registry. Which posted row? A
keyword search over outcome titles answers that only as well as the searcher's vocabulary,
and a vocabulary is exactly the thing with an unmeasured error rate. So do not search.
ENUMERATE EVERY POSTED OUTCOME MEASURE WITH NO FILTER AT ALL, recompute the stored estimate
from each candidate row under a closed, declared set of conventions, and let the arithmetic
name the row.

    one reproducing row   -> IDENTIFIED. registry, table and row_identifier are evidence.
    zero reproducing rows -> A FINDING, and a bigger one than a provenance gap.
    two or more           -> GENUINE AMBIGUITY. Stop and name them; do not choose.

WHY BOTH WITNESSES. The point alone is not enough. On NCT00423319 SIX unrelated rows
reproduce the stored point 1.2158 to within 0.2% -- "Bloody discharge", "Hypoaesthesia",
"Monocytes (absolute), high", "Neutrophils (absolute), low", "Glucose, fasting serum, high"
and a non-fatal PE rate. NOT ONE of them reproduces the interval. The 95% interval is a
second, independent witness and it discards all six.

THIS INSTRUMENT'S OWN FAILURES, KEPT BECAUSE EACH ONE ALMOST BECAME A PUBLISHED ABSENCE:

  1. A KEYWORD PASS SEARCHED `bleed` AND MISSED "Number of Participants With Major
     HEMORRHAGE". That is the whole argument for enumerating instead of searching.
  2. THE FIRST FULL PASS RETURNED ZERO ROWS FOR FOUR OF SEVEN REGISTRATIONS AND WAS WRONG
     ABOUT ALL FOUR. Two conventions were missing:
       - the registry posts RATES, and the stored count is round(rate% x n). 0.47% of 3184
         is 14.96; the arithmetic uses 15. From 14.96 the ratio is 2.474 against a stored
         2.5259 and reproduces nothing.
       - the zero-cell correction adds 0.5 to the EVENTS ONLY, denominators untouched.
         events+0.5 with n+1 gives 0.19512 where 0.19500 is stored.
     Reported as NOT_ASSESSABLE rather than as an absence, and the caution was right:
     all four are exactly reproducible.
  3. A REWRITE SILENTLY DROPPED A CONVENTION THAT HAD ALREADY IDENTIFIED A ROW -- counts
     carried in a class title, "Major bleeding (n=9, 14)" -- turning NCT00452530 from
     IDENTIFIED back into a zero. A CONVENTION THAT HAS EVER IDENTIFIED A ROW MUST NOT BE
     LOST IN A REWRITE.
  4. A negative variance was passed to sqrt when e == n. A negative variance is not a narrow
     interval; it is a slice that is not a 2x2 table, and it is skipped.

    ⭐ AN INSTRUMENT WITH A KNOWN MISS AND NO MEASURED ERROR RATE CANNOT ASSERT AN ABSENCE.
    ⭐ NOT_ASSESSABLE IS NOT "DID NOT COME FROM THE REGISTRY".

WHERE THE METHOD IS BLIND, MEASURED NOT GUESSED. When both arms have ZERO events every
zero-zero outcome in the trial yields the identical continuity-corrected ratio, so they are
numerically indistinguishable. On NCT02829957 (n=19) six rows all reproduce 0.7273
(0.0161 to 32.9244) from 0/11 against 0/8 -- among them "Major Hemorrhage", "Venous
Thromboembolism" and "Discontinued Planned Drug Administration". THE AMBIGUITY IS IN THE
DATA, NOT IN THIS SCRIPT, and no amount of enumeration resolves it.

RESULT ON THE SEVEN LEGACY-PROVENANCE ROWS, 2026-09-03: IDENTIFIED 6 of 7; 1 AMBIGUOUS.
Full table in out/provenance_row_identification_2026_09_03.json.

Usage: python scripts/identify_source_row_by_reproduction_2026_09_03.py [--cache FILE]
Exit 1 unless every registration resolves to exactly one row.
"""

import json, io, math, os, re, sys

# GUARDED, because a module-scope rebind closes the caller's stdout on import. This file
# carried the unguarded form and scripts/lint_recurring_traps.py refused the commit -- the
# same trap this repository has been bitten by before, caught by the instrument that exists
# for it.
if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
Z = 1.959963984540054
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(REPO, "evidence", "2026-09-03-provenance-rows",
                     "ctgov_outcomes.json")


def load():
    """Registry outcome tables. The committed cache is the default so the result is
    reproducible offline; --live re-fetches and is how the cache was made."""
    if "--live" in sys.argv:
        import urllib.request
        out = {}
        for n in STORED:
            out[n] = json.load(urllib.request.urlopen(
                "https://clinicaltrials.gov/api/v2/studies/%s?format=json" % n, timeout=120))
        return out
    return json.load(io.open(CACHE, encoding="utf-8"))
STORED = {
 "NCT00457002": (2.5259, 0.9813, 6.5018), "NCT00423319": (1.2158, 0.6537, 2.2615),
 "NCT00371683": (0.4975, 0.2421, 1.0225), "NCT00452530": (0.6459, 0.2804, 1.4876),
 "NCT03266783": (0.1574, 0.0615, 0.4028), "NCT01780987": (0.1950, 0.0097, 3.9330),
 "NCT02829957": (0.7273, 0.0161, 32.9244)}
PTOL, CTOL = 0.0015, 0.005
NPAT = re.compile(r"n\s*=\s*(\d+)\s*,\s*(?:n\s*=\s*)?(\d+)", re.I)

def num(x):
    try: return float(str(x).replace(",", ""))
    except Exception: return None

def denoms(o):
    d = {}
    for dn in o.get("denoms") or []:
        for c in dn.get("counts") or []:
            v = num(c.get("value"))
            if v is not None: d.setdefault(c.get("groupId"), v)
    return d

def eff(e1, n1, e2, n2):
    out = []
    if None in (e1, n1, e2, n2) or n1 <= 0 or n2 <= 0: return out
    if e1 < 0 or e2 < 0 or e1 > n1 or e2 > n2: return out
    def add(lab, pt, v):
        # A NEGATIVE VARIANCE IS NOT A NARROW INTERVAL, IT IS A NON-2x2 CELL SET.
        # e == n makes 1/(e+0.5) - 1/n negative; such a slice is skipped, never sqrt'd.
        if v is None or v <= 0 or pt <= 0: return
        se = math.sqrt(v)
        out.append((lab, pt, pt*math.exp(-Z*se), pt*math.exp(Z*se)))
    if e1 > 0 and e2 > 0:
        add("RR", (e1/n1)/(e2/n2), 1/e1 - 1/n1 + 1/e2 - 1/n2)
        if e1 < n1 and e2 < n2:
            add("OR", (e1/(n1-e1))/(e2/(n2-e2)),
                1/e1 + 1/(n1-e1) + 1/e2 + 1/(n2-e2))
    a1, a2 = e1+0.5, e2+0.5           # 0.5 to EVENTS only; denominators untouched
    add("RR+0.5ev", (a1/n1)/(a2/n2), 1/a1 - 1/n1 + 1/a2 - 1/n2)
    b1, b2 = n1-e1+0.5, n2-e2+0.5
    if b1 > 0 and b2 > 0:
        add("OR+0.5ev", (a1/b1)/(a2/b2), 1/a1 + 1/b1 + 1/a2 + 1/b2)
    return out

def scan(nct):
    tgt, tlo, thi = STORED[nct]
    oms = ((D[nct].get("resultsSection") or {}).get("outcomeMeasuresModule") or {}).get("outcomeMeasures") or []
    hits, tried = [], 0
    for oi, o in enumerate(oms):
        gids = [g["id"] for g in o.get("groups", [])]
        gname = {g["id"]: g.get("title", "") for g in o.get("groups", [])}
        odn = denoms(o)
        for cl in o.get("classes") or [{}]:
            ct = cl.get("title") or ""
            m = NPAT.search(ct)
            cdn = {gids[0]: float(m.group(1)), gids[1]: float(m.group(2))} if (m and len(gids) > 1) else {}
            for cat in cl.get("categories") or [{}]:
                vals = {}
                for mm in cat.get("measurements") or []:
                    v = num(mm.get("value"))
                    if v is not None: vals[mm.get("groupId")] = v
                if len(vals) < 2: continue
                dn = dict(odn); dn.update(cdn)
                sets = [("posted value read as an EVENT COUNT", vals)]
                # RESTORED: pass 1 identified NCT00452530 through counts carried in the
                # class title -- 'Major bleeding (n=9, 14)'. Dropping that convention when
                # the instrument was rewritten turned an identified row back into a zero.
                # A convention that has ever identified a row must not be silently lost.
                if m and len(gids) > 1:
                    sets.append(("counts read from the class title",
                                 {gids[0]: float(m.group(1)), gids[1]: float(m.group(2))}))
                pct = {g: round(v*dn[g]/100.0) for g, v in vals.items()
                       if g in dn and 0 <= v <= 100}
                if len(pct) >= 2:
                    sets.append(("round(posted rate%% x denominator) -> events", pct))
                for how, ev in sets:
                    dn_use = odn if how.startswith("counts read from the class title") else dn
                    ids = [g for g in ev if g in dn_use]
                    for a in ids:
                        for b in ids:
                            if a == b: continue
                            for lab, pt, lo, hi in eff(ev[a], dn_use[a], ev[b], dn_use[b]):
                                tried += 1
                                if (abs(pt-tgt)/abs(tgt) <= PTOL
                                        and abs(lo-tlo)/max(abs(tlo),1e-12) <= CTOL
                                        and abs(hi-thi)/max(abs(thi),1e-12) <= CTOL):
                                    hits.append({"oi": oi, "outcome": o.get("title",""),
                                        "class": ct, "how": how, "conv": lab,
                                        "num": "%s %g/%g" % (gname.get(a,a), ev[a], dn_use[a]),
                                        "den": "%s %g/%g" % (gname.get(b,b), ev[b], dn_use[b]),
                                        "pt": pt, "lo": lo, "hi": hi})
    return hits, tried, len(oms)

D = load()
print("BOTH WITNESSES REQUIRED: the point AND the 95%% interval must reproduce")
print("point tol %.4f rel, interval tol %.3f rel\n" % (PTOL, CTOL))
res = {}
for nct in STORED:
    tgt, tlo, thi = STORED[nct]
    hits, tried, n = scan(nct)
    uniq = {}
    for h in hits: uniq.setdefault((h["oi"], h["class"]), h)
    res[nct] = len(uniq)
    print("=== %s  stored %.4f (%.4f to %.4f)" % (nct, tgt, tlo, thi))
    print("    %d outcome measures enumerated (no keyword filter), %d computations" % (n, tried))
    print("    ROWS REPRODUCING POINT AND INTERVAL: %d" % len(uniq))
    for h in uniq.values():
        print("      outcome[%d] %r" % (h["oi"], h["outcome"][:76]))
        if h["class"]: print("        class %r" % h["class"][:60])
        print("        %s ; %s" % (h["num"], h["den"]))
        print("        %s, %s -> %.4f (%.4f to %.4f)" % (h["conv"], h["how"], h["pt"], h["lo"], h["hi"]))
    print()
print("SUMMARY")
ok = 0
for k, v in res.items():
    s = "ZERO -- FINDING" if v == 0 else "IDENTIFIED" if v == 1 else "AMBIGUOUS (%d)" % v
    ok += (v == 1)
    print("   %-13s %s" % (k, s))
print("\n   IDENTIFIED %d of %d" % (ok, len(res)))
sys.exit(0 if ok == len(res) else 1)
