"""Source-recheck suspect trial counts against the ClinicalTrials.gov API v2.

Motivation (2026-05-31): a portfolio scan found 154 *_REVIEW apps whose
realData carries arithmetically impossible 2x2 counts (tE>tN or cE>cN), plus
single-arm phase-I/II studies wrongly cast as 2-arm RCTs. Numbers cannot be
"patched" without a source; this tool fetches the authoritative ctgov record
for every suspect trial and CLASSIFIES it so we know what is salvageable
before any destructive edit.

Classification per trial:
  EXCLUDE_SINGLE_ARM   arms<=1 / allocation NA  -> not poolable, quarantine app
  RECLASS_CONTINUOUS   primary outcome is a mean/%-change (continuous)  -> not 2x2
  FIXABLE_BINARY       >=2 randomized arms with posted binary event counts
  NEEDS_MANUAL         RCT but no usable structured binary results posted
  FETCH_ERROR          ctgov lookup failed

Network etiquette: on-disk JSON cache (resumable), polite rate-limit, bounded
retries with backoff, fail-closed on malformed payloads. DRY-RUN by default --
emits a report and writes NOTHING to the HTML. `--apply` is a separate,
explicit step handled downstream once the report is reviewed.

Usage:
  python scripts/ctgov_recheck_counts.py                 # scan all suspect apps, dry-run report
  python scripts/ctgov_recheck_counts.py --limit 25      # first 25 suspect trials only
  python scripts/ctgov_recheck_counts.py --apps A.html B.html
"""
from __future__ import annotations
import argparse, io, json, sys, time, urllib.request, urllib.error
import importlib.util
from pathlib import Path

if hasattr(sys.stdout, "buffer") and getattr(sys.stdout, "encoding", "").lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent.parent
CACHE_DIR = HERE / "outputs" / "ctgov_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
REPORT = HERE / "outputs" / "ctgov_recheck_report.json"

# Reuse the validator's realData parser so we read exactly what it pools.
_spec = importlib.util.spec_from_file_location("vv", HERE / "validate_living_ma_portfolio.py")
vv = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(vv)

CONTINUOUS_HINTS = ("change from baseline", "percent change", "mean ", "least squares mean",
                    "ls mean", "score", "ldl-c", "hba1c", "egfr", "mmhg", "reduction in")


def fetch_study(nct, retries=3):
    """Return the ctgov study JSON (cached), or None on hard failure."""
    cache = CACHE_DIR / f"{nct}.json"
    if cache.exists():
        try:
            return json.loads(cache.read_text(encoding="utf-8"))
        except ValueError:
            pass  # corrupt cache -> refetch
    url = f"https://clinicaltrials.gov/api/v2/studies/{nct}"
    backoff = 1.0
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "rapidmeta-ctgov-recheck"})
            raw = urllib.request.urlopen(req, timeout=30).read()
            data = json.loads(raw)  # fail closed if not JSON
            if "protocolSection" not in data:
                return None
            cache.write_text(json.dumps(data), encoding="utf-8")
            return data
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return {"_notfound": True}
            time.sleep(backoff); backoff *= 2
        except (urllib.error.URLError, ValueError, TimeoutError):
            time.sleep(backoff); backoff *= 2
    return None


def classify(nct, study):
    if study is None:
        return {"nct": nct, "verdict": "FETCH_ERROR"}
    if study.get("_notfound"):
        return {"nct": nct, "verdict": "NEEDS_MANUAL", "note": "ctgov 404 (NCT not found)"}
    ps = study.get("protocolSection", {})
    dm = ps.get("designModule", {})
    arms = ps.get("armsInterventionsModule", {}).get("armGroups", [])
    alloc = dm.get("designInfo", {}).get("allocation")
    n = dm.get("enrollmentInfo", {}).get("count")
    title = ps.get("identificationModule", {}).get("briefTitle", "")
    base = {"nct": nct, "title": title[:80], "n": n, "arms": len(arms), "allocation": alloc}

    if len(arms) <= 1 or alloc == "NA":
        return {**base, "verdict": "EXCLUDE_SINGLE_ARM"}

    oms = study.get("resultsSection", {}).get("outcomeMeasuresModule", {}).get("outcomeMeasures", [])
    primary = next((o for o in oms if o.get("type") == "PRIMARY"), oms[0] if oms else None)
    if primary is None:
        return {**base, "verdict": "NEEDS_MANUAL", "note": "no posted results"}
    ptitle = (primary.get("title") or "").lower()
    punit = (primary.get("unitOfMeasure") or "").lower()
    if any(h in ptitle for h in CONTINUOUS_HINTS) or "%" in punit or "change" in punit or "mean" in punit:
        return {**base, "verdict": "RECLASS_CONTINUOUS", "primary": primary.get("title", "")[:60]}
    # count-shaped primary across >=2 groups => fixable
    if primary.get("paramType") in ("COUNT_OF_PARTICIPANTS", "NUMBER") or len(primary.get("groups", [])) >= 2:
        return {**base, "verdict": "FIXABLE_BINARY", "primary": primary.get("title", "")[:60]}
    return {**base, "verdict": "NEEDS_MANUAL", "primary": primary.get("title", "")[:60]}


def suspect_trials(app_files):
    """Yield (app, nct) for every trial with an impossible/implausible count."""
    seen = set()
    for f in app_files:
        html = Path(f).read_text(encoding="utf-8", errors="replace")
        for nct, d in vv.extract_real_data(html).items():
            tE, tN, cE, cN = d.get("tE"), d.get("tN"), d.get("cE"), d.get("cN")
            bad = ((tN and tE and tE > tN) or (cN and cE and cE > cN)
                   or (tN and 0 < tN <= 5) or (cN and 0 < cN <= 5))
            if bad and (f, nct) not in seen:
                seen.add((f, nct))
                yield f, nct


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apps", nargs="*", help="explicit app HTML files (default: all *_REVIEW.html)")
    ap.add_argument("--limit", type=int, default=0, help="cap number of suspect trials (0 = all)")
    ap.add_argument("--sleep", type=float, default=0.34, help="seconds between live API calls")
    args = ap.parse_args()

    app_files = args.apps or sorted(str(p) for p in HERE.glob("*_REVIEW.html"))
    pairs = list(suspect_trials(app_files))
    if args.limit:
        pairs = pairs[:args.limit]
    print(f"suspect (app, trial) pairs: {len(pairs)}  across {len({a for a,_ in pairs})} apps")

    results, counts = [], {}
    fetched_live = 0
    for i, (app, nct) in enumerate(pairs, 1):
        was_cached = (CACHE_DIR / f"{nct}.json").exists()
        study = fetch_study(nct)
        if not was_cached and study is not None:
            fetched_live += 1
            time.sleep(args.sleep)
        v = classify(nct, study)
        v["app"] = Path(app).name
        results.append(v)
        counts[v["verdict"]] = counts.get(v["verdict"], 0) + 1
        if i % 20 == 0:
            print(f"  …{i}/{len(pairs)} (live fetches: {fetched_live})")

    REPORT.write_text(json.dumps({"results": results, "summary": counts}, indent=2), encoding="utf-8")
    print("\n=== VERDICT SUMMARY (dry-run, no HTML modified) ===")
    for k in ("FIXABLE_BINARY", "RECLASS_CONTINUOUS", "EXCLUDE_SINGLE_ARM", "NEEDS_MANUAL", "FETCH_ERROR"):
        print(f"  {k:20s}: {counts.get(k, 0)}")
    print(f"\nreport -> {REPORT.relative_to(HERE)}")


if __name__ == "__main__":
    main()
