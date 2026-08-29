#!/usr/bin/env python3
"""ONE STATISTIC, TWO VALUES, ONE PAGE.

lefamulin-cabp serves `Q 0.7313 on 1 df` in the result and `Q 0.7316 on 1 df` in the GRADE
inconsistency narrative -- one pool, one statistic, two values, because the GRADE prose quotes
a stored metafor log while the result renders a structured `heterogeneity.q` field. Two
surfaces, two provenances, no reconciliation.

WHAT SEPARATES THE DEFECT FROM ORDINARY DATA, and it is the whole design. A page with several
outcomes has several Q values and that is correct. What is not correct is two values of one
statistic that AGREE TO THREE SIGNIFICANT FIGURES AND THEN DISAGREE: distinct pools do not
collide to 3 s.f. by chance, while a value recomputed on slightly different inputs, or copied
from a log written at another time, differs exactly that way. So proximity IS the signal, and
a naive "same label, different number" sweep would be mostly false.

REPORTED SEPARATELY, NEVER MERGED:
  NEAR    two values agreeing to >=3 s.f. and differing      -- the stale-field signature
  WIDE    same statistic, values far apart                   -- usually several pools, NOT a
          finding on its own, counted so the denominator is visible rather than filtered away

WHAT IT CANNOT SEE: a statistic rendered into an SVG that is rasterised, and a value that is
wrong in BOTH places. It finds disagreement, never error.
"""
import collections
import glob
import html as _h
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

STAT = re.compile(
    r"(?P<stat>Q|I²|I\^2|i-squared|I-squared|τ²|tau\^2|tau2|H²|H\^2)"
    r"\s*(?:=|:)?\s*"
    r"(?P<val>-?\d+(?:\.\d+)?)"
    r"(?P<pct>\s*%)?"
    r"(?:\s*on\s*(?P<df>\d+)\s*(?:df|degrees of freedom))?")

CANON = {"I²": "I2", "I^2": "I2", "i-squared": "I2", "I-squared": "I2",
         "τ²": "tau2", "tau^2": "tau2", "tau2": "tau2",
         "H²": "H2", "H^2": "H2", "Q": "Q"}


def rendered(path):
    s = io.open(path, encoding="utf-8", errors="replace").read()
    s = re.sub(r"(?is)<(script|style).*?</\1>", " ", s)
    return re.sub(r"\s+", " ", _h.unescape(re.sub(r"<[^>]+>", " ", s)))


def sig3(x):
    """Do two values agree to three significant figures?"""
    return round(x, 3 - 1 - (len(str(int(abs(x)))) - 1 if abs(x) >= 1 else 0)) if x else 0.0


def _to3sf(x):
    if x == 0:
        return 0.0
    import math
    e = math.floor(math.log10(abs(x)))
    return round(x, -(e - 2))


def close3(a, b):
    """Do the two values agree when rounded to three significant figures?

    THE FIRST VERSION USED A 0.1% RELATIVE THRESHOLD AS A PROXY FOR THIS AND IT IS NOT ONE.
    AGYW_HIV_PREP's Q 0.1533 against 0.1535 differ by 0.13%, so the proxy rejected a pair
    that agrees to three significant figures exactly (0.153) -- the signature this detector
    exists to find. Two more pages were lost the same way. Test the property, not a stand-in
    for it.
    """
    # NEITHER "3 SIGNIFICANT FIGURES" NOR "0.1%" IS THE PROPERTY, and both were tried.
    # 3 s.f. rejects the lefamulin pair -- 0.7313 rounds to 0.731 and 0.7316 to 0.732 -- and
    # 0.1% rejects AGYW's 0.1533 against 0.1535, which differ by 0.13%. Both are the same
    # quantity computed twice. What actually separates them from two different pools is
    # ORDER OF MAGNITUDE: a stale recomputation lands within a percent, while two pools'
    # Q values differ by tens or hundreds of percent. 1% is the threshold, and every
    # finding is printed with its percentage so the choice can be argued with rather than
    # trusted.
    if a == b:
        return False
    m = max(abs(a), abs(b))
    return m != 0 and abs(a - b) / m < 0.01


def _dp(raw):
    return len(raw.split(".")[1]) if "." in raw else 0


def _is_rounding(ra, rb):
    """Is the shorter-printed value a correct rounding of the longer one?

    THIS IS THE DISCRIMINATOR THE FIRST VERSION LACKED, and without it the sweep reported 16
    pages of which most were one value shown at two precisions -- "5.16" beside "5.161",
    "90.0" beside "90.02". Nothing on those pages disagrees. The lefamulin pair survives it
    because 0.7316 rounded to four places is 0.7316, not 0.7313: two values that are both
    printed to the same precision and still differ cannot be the same number.
    """
    short, lng = (ra, rb) if _dp(ra) <= _dp(rb) else (rb, ra)
    d = _dp(short)
    try:
        return ("%.*f" % (d, float(lng))) == ("%.*f" % (d, float(short)))
    except ValueError:
        return False


def scan_text(t):
    found = collections.defaultdict(list)
    for m in STAT.finditer(t):
        stat = CANON.get(m.group("stat"), m.group("stat"))
        try:
            v = float(m.group("val"))
        except ValueError:
            continue
        if m.group("pct"):
            stat += "_pct"
        found[stat].append((v, m.group("val"), m.group("df"), m.start()))
    near, wide, rounded = [], [], 0
    for stat, vals in found.items():
        seen = {}
        for v, raw, _df, _pos in vals:
            seen.setdefault(v, raw)
        uniq = sorted(seen)
        if len(uniq) < 2:
            continue
        hit = False
        for i in range(len(uniq)):
            for j in range(i + 1, len(uniq)):
                a, b = uniq[i], uniq[j]
                if not close3(a, b):
                    continue
                if _is_rounding(seen[a], seen[b]):
                    # SAME VALUE, TWO PRECISIONS. Not a contradiction: nothing disagrees,
                    # the page is merely inconsistent about decimal places. Counted so the
                    # separation is visible, never mixed into the findings.
                    rounded += 1
                    continue
                near.append((stat, seen[a], seen[b]))
                hit = True
        if not hit and len(uniq) >= 2:
            wide.append((stat, len(uniq)))
    return near, wide, rounded



# ---------------------------------------------------------------------------------------
# DETECTOR 2: BUNDLES SHARING A DEGREES-OF-FREEDOM, WHERE ANY DIFFERENCE COUNTS.
#
# Detector 1 uses proximity as its signal, and proximity is exactly what it cannot see past.
# TIGECYCLINE_CIAI_SSOT serves I-squared 7.287% on the result line and 1.16% in the GRADE
# narrative FOR THE SAME POOL -- the narrative quotes the same tau^2 0.000025 and the same
# Q on 2 df beside it -- and a six-fold disagreement is a worse defect than a fourth-decimal
# one. Detector 1 filed it under "several pools" because the two values are far apart.
#
# So scope by `on N df` instead of by nearness. A heterogeneity bundle is the statistics
# written within a window of one "on N df"; two bundles on a page that share a df are
# describing the same pool, and then ANY disagreement is reportable, near or wide. The
# residual false positive is a page with two pools of equal k, which is why the df and the
# co-reported tau^2 are both printed with every finding rather than summarised away.
_DF = re.compile(r"on\s+(\d+)\s+(?:df|degrees of freedom)")
_INB = {
    "Q": re.compile(r"Q\s*(?:\(df\s*=\s*\d+\))?\s*[=:]?\s*(-?\d+(?:\.\d+)?)"),
    "I2": re.compile(r"(?:I²|I\^2|I-squared|i-squared)\s*[=:]?\s*(-?\d+(?:\.\d+)?)"),
    "tau2": re.compile(r"(?:τ²|tau\^2|tau2)\s*[=:]?\s*(-?\d+(?:\.\d+)?)"),
}
WINDOW = 190


def bundles(t):
    """The statistics written NEXT TO each `on N df`, not merely near it.

    THE FIRST VERSION TOOK THE FIRST MATCH IN A FIXED WINDOW AND ITS OWN POSITIVE CONTROL
    CAUGHT IT: with two df markers close together both windows covered the same text, both
    bundles picked the same first match, and two bundles that are identical by construction
    can never conflict. The control failed rather than the sweep quietly reporting zero --
    which is the only reason this is a paragraph and not an incident.

    Two corrections: the window is CLIPPED at the neighbouring df markers so bundles cannot
    overlap, and within it the statistic chosen is the one NEAREST the marker rather than the
    first, because a bundle is what was written beside a df and reading order is not distance.
    """
    marks = [m for m in _DF.finditer(t)]
    out = []
    for i, m in enumerate(marks):
        lo = max(0, m.start() - WINDOW)
        hi = min(len(t), m.end() + WINDOW)
        if i:
            lo = max(lo, marks[i - 1].end())
        if i + 1 < len(marks):
            hi = min(hi, marks[i + 1].start())
        seg, off = t[lo:hi], lo
        anchor = m.start()
        b = {}
        for k, rx in _INB.items():
            best = None
            for hit in rx.finditer(seg):
                d = abs((off + hit.start()) - anchor)
                if best is None or d < best[0]:
                    best = (d, hit.group(1))
            if best:
                b[k] = best[1]
        if b:
            out.append((m.group(1), b, m.start()))
    return out


def _distinctive(raw):
    """A value specific enough that two bundles sharing it are describing one pool.

    tau2 = 0 is the commonest value in the corpus and says nothing about identity; four
    separate k=2 pools on IV_IRON_HF all carry df=1 and several carry tau2 0, so agreement
    on it is not evidence. A non-zero value carrying three or more significant digits is.
    """
    try:
        v = float(raw)
    except ValueError:
        return False
    # NON-ZERO IS THE WHOLE TEST, and the first attempt asked for three significant digits
    # instead. That excluded tau^2 = 0.000025 -- which has two -- and so rejected the very
    # pair this detector was built for; the positive control failed and said so. Specificity
    # here is not about digit count: 0 and only 0 is the default that several unrelated pools
    # share, and excluding it is exactly what stops IV_IRON_HF's four k=2 outcomes from being
    # read as one pool.
    return v != 0


def bundle_conflicts(t):
    """Two bundles are compared only when they AGREE on something distinctive.

    df ALONE DOES NOT IDENTIFY A POOL, and the first version of this detector assumed it did.
    IV_IRON_HF holds four k=2 outcomes -- four pools, all df=1, four different Q values -- and
    it reported all six pairings as conflicts. A page with several small pools would have been
    the loudest finding in the corpus and every one of them wrong.

    The same-pool test is therefore agreement, not df: two bundles that agree on a distinctive
    statistic (non-zero, three or more significant digits) and disagree on another are one
    pool described twice. tigecycline's pair agrees on tau^2 0.000025 and disagrees on
    I-squared 7.287 vs 1.16. iv-iron's four pools agree on nothing distinctive and are not
    compared.
    """
    by_df = collections.defaultdict(list)
    for df, b, pos in bundles(t):
        by_df[df].append((b, pos))
    bad, seen = [], set()
    for df, items in by_df.items():
        if len(items) < 2:
            continue
        for x in range(len(items)):
            for y in range(x + 1, len(items)):
                ba, bb = items[x][0], items[y][0]
                shared = [k for k in _INB if k in ba and k in bb]
                agree = [k for k in shared
                         if (ba[k] == bb[k] or _is_rounding(ba[k], bb[k]))
                         and (_distinctive(ba[k]) or _distinctive(bb[k]))]
                if not agree:
                    continue
                for k in shared:
                    if k in agree:
                        continue
                    if _is_rounding(ba[k], bb[k]):
                        continue
                    key = (df, k, ba[k], bb[k])
                    if key in seen:
                        continue
                    seen.add(key)
                    bad.append((df, k, ba[k], bb[k], "same pool via %s=%s"
                                % (agree[0], ba[agree[0]])))
    return bad


def _controls():
    """POSITIVE: the lefamulin pair must be flagged NEAR.
    NEGATIVE 1: one statistic repeated with the SAME value is not a contradiction.
    NEGATIVE 2: two genuinely different pools -- Q 33.4 and Q 0.1533 -- must NOT be NEAR,
      or the sweep would report every multi-outcome page in the corpus."""
    pos = "estimator REML, k = 2. Q 0.7313 on 1 df ... inconsistency -- Q 0.7316 on 1 df, p = 0.3924"
    neg1 = "Q 0.7316 on 1 df and again below Q 0.7316 on 1 df"
    neg2 = "i-squared 91.0%, Q 33.4 on 3 degrees of freedom, and elsewhere Q 0.1533 on 1 df"
    neg3 = "Q 5.161 on 3 df and in the summary Q 5.16 on 3 df"
    bpos = ("k = 3. tau2 0.000025 I-squared 7.287% Q 2.157 on 2 df ... the stored refit gives "
            "tau^2 0.000025, Q 2.1564 on 2 df, p = 0.3402, I-squared 1.16%")
    bneg = ("k = 3. tau2 0.000025 I-squared 7.287% Q 2.157 on 2 df ... a different pool: "
            "tau^2 61.45, Q 58.4577 on 7 df, I-squared 90.02%")
    bp, bn = bundle_conflicts(bpos), bundle_conflicts(bneg)
    pn, _, _ = scan_text(pos)
    n1n, _, _ = scan_text(neg1)
    n2n, _, _ = scan_text(neg2)
    n3n, _, _ = scan_text(neg3)
    ok = (bool(pn) and not n1n and not n2n and not n3n
          and bool(bp) and not bn)
    print("CONTROLS, all three legs, every run")
    print("  POSITIVE  lefamulin 0.7313 vs 0.7316   -> NEAR : %s" % bool(pn))
    print("  NEGATIVE  same value twice             -> NEAR : %s  (must be False)" % bool(n1n))
    print("  NEGATIVE  two different pools          -> NEAR : %s  (must be False)" % bool(n2n))
    print("  NEGATIVE  5.161 vs 5.16, a rounding    -> NEAR : %s  (must be False)" % bool(n3n))
    print("  POSITIVE  same df, I2 7.287 vs 1.16    -> BUNDLE: %s" % bool(bp))
    print("  NEGATIVE  different df (2 vs 7)        -> BUNDLE: %s  (must be False)" % bool(bn))
    print("  CONTROLS PASS: %s\n" % ok)
    return ok


def main():
    if not _controls():
        print("CONTROLS FAILED -- findings below are not reportable.")
        return 3
    pages = sorted(glob.glob(os.path.join(ROOT, "*.html")))
    kinds = collections.Counter()
    findings, wides = [], 0
    bundle_findings = []
    for p in pages:
        rel = os.path.basename(p)
        try:
            t = rendered(p)
        except Exception:
            kinds["unreadable"] += 1
            continue
        near, wide, rnd = scan_text(t)
        bc = bundle_conflicts(t)
        if bc:
            bundle_findings.append((rel, bc))
        wides += len(wide)
        kinds["one value at two precisions (not a contradiction)"] += rnd
        if near:
            kinds["page with a NEAR mismatch"] += 1
            findings.append((rel, near))
        elif wide:
            kinds["page with several pools, no NEAR mismatch"] += 1
        else:
            kinds["page with no repeated statistic"] += 1
    print("KINDS BEFORE COUNTS")
    for k, v in kinds.most_common():
        print("   %-42s %d" % (k, v))
    print("   %-42s %d" % ("pages examined", len(pages)))
    print("\nNEAR MISMATCHES on %d page(s)\n" % len(findings))
    for rel, near in findings:
        print("  %s" % rel)
        for stat, a, b in near:
            fa, fb = float(a), float(b)
            print("      %-8s %s  vs  %s   (differ by %.2g%%, both printed to %d/%d dp)"
                  % (stat, a, b, 100 * abs(fa - fb) / max(abs(fa), abs(fb)), _dp(a), _dp(b)))
    print("")
    print("SAME-df BUNDLE CONFLICTS on %d page(s) -- any size of difference"
          % len(bundle_findings))
    print("")
    for rel, bc in bundle_findings:
        print("  %s" % rel)
        for df, k, a, b, why in bc:
            print("      df=%-3s %-5s %s  vs  %s     [%s]" % (df, k, a, b, why))
    print("\nWIDE groups (several pools; counted, not reported as findings): %d" % wides)
    return 1 if (findings or bundle_findings) else 0


if __name__ == "__main__":
    sys.exit(main())
