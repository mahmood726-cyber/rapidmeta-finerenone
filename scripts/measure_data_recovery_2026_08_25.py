"""Can the numbers a published review extracted be recovered from OPEN sources alone?

MAHMOOD: "we have found nearly all data can be found from previous metas, fda, ema, CT.gov,
aact and other open sources. just needs looking. hard enough. occasionally we can also use a
firewalled paper if not possible any other way ... this is important as data wise we want to
be just as good as Cochrane".

THE SUBSTITUTION ARGUMENT APPLIED TO DATA, and unlike search recall it is directly
measurable. Cochrane's full-text access is a MEANS: the end is obtaining the trial's numbers.
If the same numbers are recoverable from open sources, the two routes are equal on data.

THE ANSWER KEY IS SOMEONE ELSE'S EXTRACTION. A published review's outcome table states, per
trial, the events and denominators it extracted. Those are the numbers to recover. Using our
own objects as the key would be marking our own work.

RECOVERY IS NOT BINARY, and reporting it as a single rate would hide the thing that matters.
CARMELINA is the case that settled the design: the review's table gives 209/3494 versus
226/3485, and ClinicalTrials.gov posts the primary as PERCENTAGES -- 12.1 and 12.4 -- for a
different composite, with only two outcome measures posted at all. A number was available and
it was not that number. So:

  EXACT        the same value, to rounding
  DERIVABLE    a different form of the same fact (a percentage and a denominator give the
               count) -- recovered, and recorded as reconstructed rather than read
  OTHER_FORM   the outcome is posted but as a metric that does not yield the review's number
  NOT_POSTED   the source has the trial but not this outcome
  NO_SOURCE    the trial could not be located in this tier at all

TIERS ARE RECORDED PER NUMBER, because the tier matters as much as the recovery:

  ctgov      structured, per-arm, primary evidence          strongest
  fda        Drugs@FDA statistical and medical reviews      often EXCEEDS the publication
  ema        EPARs, and a genuine cross-regulator check
  prior_meta A NUMBER IN A PRIOR META IS A CLAIM ABOUT A TRIAL, NOT THE TRIAL. Recorded as a
             lower tier and surfaced as such on any page that uses it, so a
             recovered-from-secondary number never looks like a recovered-from-primary one.
  paywalled  last resort, occasionally

THIS RUN IS TIER 1 ONLY (ctgov) and is a FIRST measurement on a small set, to get a rate
before scaling. The other tiers are where the rate should improve, and FDA is where it may
exceed the publication rather than match it.

=======================================================================================
THIS DESIGN IS INVALID AND ITS RATE MUST NOT BE QUOTED. Read before reusing any of it.
=======================================================================================

The first run reported 64 of 116 numbers (55%) recovered at tier 1. A NULL TEST then matched
THE SAME 116 NUMBERS against fourteen trials from unrelated disease areas -- anticoagulants,
antibiotics, PCSK9, ophthalmology -- and got 69 of 116 (59%).

    real trials  55%
    UNRELATED trials  59%

The rate is WORSE THAN CHANCE. It was never measuring recovery.

THE FLAW IS IN THIS FILE AND IT WAS FLAGGED IN A COMMENT WHILE BEING WRITTEN. The review
names its NCT ids but does not say which table row belongs to which trial, so this probes
EVERY named NCT and counts a number recovered if ANY of them supplies it. With event counts
like 20, 112, 209 and denominators like 3494, some value in a pool of a dozen trials'
posted outcomes will match nearly always. The comment said the approach was "GENEROUS to
us"; the null test showed it was not generous, it was empty.

WHAT A VALID DESIGN NEEDS, and none of it is optional:
  * trial label -> NCT resolved per row, not pooled across the review
  * OUTCOME-level matching: the review's HF-hospitalisation count compared against that
    trial's HF-hospitalisation measure, not against any number it posted
  * arm-level matching, so a treatment count is not satisfied by a control count
  * and the null test kept as a permanent control, because a rate that does not beat
    matching against unrelated trials is not a rate

The measurement is worth building properly. This version is kept as the record of how a
plausible 55% turned out to be noise, and of the fact that the null test -- not review, not
the passing controls above -- is what caught it.
"""
import io
import json
import os
import re
import subprocess
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "scripts"))
import instrument_controls

SCRATCH = (r"F:\claude-temp\claude\F--rapidmeta-finerenone"
           r"\e2e2a1d5-c19e-44de-90ab-690dbc5235a1\scratchpad\datarecovery")
OUT = os.path.join(REPO, "outputs", "data_recovery_2026_08_25.json")
EFETCH = ("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pmc"
          "&id=%s&retmode=xml")
CTG = ("https://clinicaltrials.gov/api/v2/studies/%s"
       "?fields=protocolSection.identificationModule,resultsSection.outcomeMeasuresModule,"
       "hasResults")

NCT = re.compile(r"NCT\d{8}")
NUM = re.compile(r"^-?\d+(?:\.\d+)?$")


# CP1252 STDOUT. Article titles carry U+2010 non-breaking hyphens and Windows' default
# console encoding cannot encode them, so the script died at the first print of a title --
# after the controls had already passed, which is the worst place to die because it looks
# like the measurement failed rather than the printing. Guarded at module scope, and NOT
# inside `if __name__`, because this module is also imported.
if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                                  write_through=True)


def curl(url, timeout=90):
    try:
        p = subprocess.run(["curl", "-sL", "-m", str(timeout), url],
                           capture_output=True, timeout=timeout + 20)
        return (p.stdout or b"").decode("utf-8", "replace")
    except Exception:
        return ""


def review_tables(pmcid):
    """(title, [ (caption, [rows-of-cells]) ], [nct ids])."""
    x = curl(EFETCH % pmcid)
    if len(x) < 3000:
        return None, [], []
    t = re.search(r"<article-title>(.*?)</article-title>", x, re.S)
    title = " ".join(re.sub(r"<[^>]+>", " ", t.group(1)).split()) if t else "?"
    tables = []
    for m in re.finditer(r"<table-wrap.*?</table-wrap>", x, re.S):
        blk = m.group(0)
        cap = re.search(r"<caption>(.*?)</caption>", blk, re.S)
        capt = " ".join(re.sub(r"<[^>]+>", " ", cap.group(1)).split()) if cap else ""
        rows = []
        for r in re.findall(r"<tr>(.*?)</tr>", blk, re.S):
            cells = [" ".join(re.sub(r"<[^>]+>", " ", c).split())
                     for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", r, re.S)]
            if cells:
                rows.append(cells)
        tables.append((capt, rows))
    return title, tables, sorted(set(NCT.findall(x)))


def outcome_rows(tables):
    """Rows from a table whose caption says it holds per-study OUTCOMES."""
    out = []
    for capt, rows in tables:
        if not re.search(r"outcome|event|result", capt, re.I):
            continue
        for cells in rows:
            nums = [c for c in cells[1:] if NUM.match(c.replace(",", ""))]
            if len(nums) >= 4:
                out.append({"label": cells[0], "numbers": nums[:4], "caption": capt})
    return out


def ctgov_values(nct):
    """(hasResults, [ (outcome title, [values]) ])."""
    raw = curl(CTG % nct)
    if not raw.strip().startswith("{"):
        return None, []
    try:
        d = json.loads(raw)
    except ValueError:
        return None, []
    oms = ((d.get("resultsSection") or {}).get("outcomeMeasuresModule") or {}
           ).get("outcomeMeasures") or []
    got = []
    for o in oms:
        vals = []
        for cl in (o.get("classes") or []):
            for cat in (cl.get("categories") or []):
                for m in (cat.get("measurements") or []):
                    if m.get("value"):
                        vals.append(str(m["value"]))
        got.append(((o.get("title") or "")[:90], vals))
    return bool(d.get("hasResults")), got


def classify(target, ctvals):
    """EXACT / DERIVABLE / OTHER_FORM / NOT_POSTED, for one extracted number."""
    if not ctvals:
        return "NOT_POSTED"
    flat = [v for _t, vs in ctvals for v in vs]
    tgt = target.replace(",", "")
    if tgt in flat:
        return "EXACT"
    try:
        f = float(tgt)
    except ValueError:
        return "OTHER_FORM"
    for v in flat:
        try:
            g = float(v)
        except ValueError:
            continue
        if g and abs(f - g) / max(abs(f), abs(g)) < 0.005:
            return "EXACT"
    return "OTHER_FORM"


def control():
    """The classifier must separate a match from a non-match, both directions."""
    vals = [("Primary", ["209", "3494"])]
    instrument_controls.require_controls(
        "data-recovery",
        ("a value present in the source is EXACT", classify("209", vals), "EXACT"),
        ("a value absent from the source must NOT be EXACT",
         classify("777", vals), "EXACT"))
    if classify("209", []) != "NOT_POSTED":
        raise instrument_controls.ControlFailed(
            "REFUSED: an empty source did not yield NOT_POSTED. NO COUNT IS PRINTED.")
    print("CONTROL (third state) an empty source -> NOT_POSTED")
    return True


def main():
    control()
    os.makedirs(SCRATCH, exist_ok=True)
    pmcids = sys.argv[1:] or ["13487462"]
    allrows = []
    for pmcid in pmcids:
        title, tables, ncts = review_tables(pmcid)
        if not title:
            print("PMC%s: could not retrieve. Recorded as a retrieval failure, not as zero."
                  % pmcid)
            continue
        rows = outcome_rows(tables)
        print()
        print("== PMC%s  %s" % (pmcid, title[:78]))
        print("   tables %d | outcome rows %d | NCT ids named %d"
              % (len(tables), len(rows), len(ncts)))
        if not rows or not ncts:
            print("   no usable answer key (needs BOTH an outcome table and NCT ids)")
            continue
        # Trial label -> NCT cannot be resolved from the table alone; the review names its
        # NCTs but not which row each belongs to. So every named NCT is probed and a row is
        # counted recovered if ANY named trial supplies its number. That is GENEROUS to us
        # and is stated as such.
        pool = []
        for n in ncts[:14]:
            has, vals = ctgov_values(n)
            pool.append((n, has, vals))
            time.sleep(0.3)
        posted = [p for p in pool if p[1]]
        print("   of %d NCTs probed, %d have posted results" % (len(pool), len(posted)))
        allvals = [(t, v) for _n, _h, vs in posted for (t, v) in vs]
        for r in rows:
            for num in r["numbers"]:
                allrows.append({"pmcid": pmcid, "label": r["label"][:40], "target": num,
                                "verdict": classify(num, allvals), "tier": "ctgov"})

    if not allrows:
        print()
        print("No numbers were tested. NO RATE IS PRINTED.")
        return 1
    import collections
    c = collections.Counter(r["verdict"] for r in allrows)
    n = len(allrows)
    print()
    print("=== TIER 1 (ClinicalTrials.gov) ONLY ===")
    print("extracted numbers tested : %d" % n)
    for k in ("EXACT", "DERIVABLE", "OTHER_FORM", "NOT_POSTED"):
        print("  %-11s %4d  (%.0f%%)" % (k, c.get(k, 0), 100.0 * c.get(k, 0) / n))
    print()
    print("RECOVERED AT TIER 1: %d of %d (%.0f%%)"
          % (c.get("EXACT", 0) + c.get("DERIVABLE", 0), n,
             100.0 * (c.get("EXACT", 0) + c.get("DERIVABLE", 0)) / n))
    print()
    print("This is ONE tier and a SMALL set. FDA, EMA and prior metas are untried, and FDA is")
    print("the tier most likely to exceed the publication rather than match it.")
    json.dump({"rows": allrows, "counts": dict(c)}, io.open(OUT, "w", encoding="utf-8"),
              indent=1)
    print("written: %s" % os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    sys.exit(main())
