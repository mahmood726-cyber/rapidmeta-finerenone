#!/usr/bin/env python3
# sentinel:skip-file — developer tool; hardcoded ROOT is intentional (local Finrenone checkout only)
"""
Populate `pmid:` fields in every RapidMeta _REVIEW.html realData block.

Pipeline:
  1. scan   — walk all _REVIEW.html, extract (NCT, name, year, has_pmid) per file.
  2. lookup — for each unique NCT without a PMID, query Europe PMC
              (the same endpoint AutoExtractEngine.fetchAbstract already uses),
              score each candidate article, pick the best, assign a confidence
              class: HIGH / MED / LOW.
  3. apply  — write back high-confidence PMIDs into realData (after `name: '...'`).
              MED/LOW matches are reported but NOT written; they need human review.

Idempotent: skips NCTs that already have `pmid:` populated.
Cache: results/pmid_lookup_cache.json is read/written so repeat runs don't
re-hit the Europe PMC API.

Usage:
    python scripts/populate_pmids.py --scan             # phase 1 only, writes scan.json
    python scripts/populate_pmids.py --lookup           # phases 1+2, writes lookup.json
    python scripts/populate_pmids.py --dry-run          # phases 1+2+3 report, no writes
    python scripts/populate_pmids.py --apply            # phases 1+2+3 with writes

Flags:
    --min-confidence {high,med,low}  What to write back (default: high)
    --no-cache                       Ignore and overwrite the cache
"""
from __future__ import annotations
import argparse, json, pathlib, re, sys, time, urllib.parse, urllib.request

ROOT = pathlib.Path(r"C:\Projects\Finrenone")
RESULTS_DIR = ROOT / "scripts" / "pmid_results"
RESULTS_DIR.mkdir(exist_ok=True)
CACHE_FILE = RESULTS_DIR / "pmid_lookup_cache.json"
SCAN_FILE = RESULTS_DIR / "scan.json"
LOOKUP_FILE = RESULTS_DIR / "lookup.json"
APPLY_REPORT_FILE = RESULTS_DIR / "apply_report.json"

EUROPEPMC_SEARCH = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
RATE_LIMIT_SECONDS = 0.30  # 3+ req/s is safe for Europe PMC per their guide

# Tier-1 journals get a bonus — primary trial publications usually land here.
TIER1_JOURNALS = {
    "new england journal of medicine", "n engl j med", "nejm",
    "the lancet", "lancet",
    "jama", "journal of the american medical association",
    "circulation", "jama cardiology", "lancet oncology",
    "lancet respiratory medicine", "lancet diabetes endocrinology",
    "bmj", "european heart journal",
}

# ---------------------------------------------------------------------------
# PHASE 1 — scan
# ---------------------------------------------------------------------------

NCT_RE = re.compile(r"'(NCT\d{7,8})'\s*:\s*\{")
NAME_RE = re.compile(r"name\s*:\s*'([^']*)'")
YEAR_RE = re.compile(r"year\s*:\s*(\d{4})")
PMID_RE = re.compile(r"pmid\s*:\s*'(\d+)'")
SNIPPET_RE = re.compile(r"snippet\s*:\s*'([^']*)'")


def scan_file(path: pathlib.Path) -> list[dict]:
    """Return list of {nct, name, year, has_pmid, snippet, char_offset} per NCT."""
    text = path.read_text(encoding="utf-8", newline="")
    out = []
    for m in NCT_RE.finditer(text):
        nct = m.group(1)
        # The entry body can span thousands of chars (allOutcomes arrays etc.),
        # but name/year/pmid/snippet land within the first ~2 KB.
        window = text[m.end(): m.end() + 2500]
        # Confine to the first '},' at brace-depth zero (rough but effective).
        depth = 1
        end_ix = None
        for i, ch in enumerate(window):
            if ch == "{": depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    end_ix = i
                    break
        body = window[:end_ix] if end_ix is not None else window
        name_m = NAME_RE.search(body)
        year_m = YEAR_RE.search(body)
        pmid_m = PMID_RE.search(body)
        snip_m = SNIPPET_RE.search(body)
        out.append({
            "nct": nct,
            "name": name_m.group(1) if name_m else None,
            "year": int(year_m.group(1)) if year_m else None,
            "has_pmid": bool(pmid_m),
            "snippet": snip_m.group(1)[:300] if snip_m else None,
        })
    return out


def phase_scan() -> dict:
    """Walk all _REVIEW.html, write scan.json. Return the scan dict."""
    scan: dict = {"files": {}, "unique_ncts": {}}
    for p in sorted(ROOT.glob("*_REVIEW.html")):
        entries = scan_file(p)
        scan["files"][p.name] = entries
        for e in entries:
            nct = e["nct"]
            cur = scan["unique_ncts"].setdefault(nct, {
                "nct": nct, "names": set(), "years": set(),
                "has_pmid_anywhere": False, "apps": [], "snippet_sample": None,
            })
            if e["name"]: cur["names"].add(e["name"])
            if e["year"]: cur["years"].add(e["year"])
            if e["has_pmid"]: cur["has_pmid_anywhere"] = True
            if e["snippet"] and not cur["snippet_sample"]: cur["snippet_sample"] = e["snippet"]
            cur["apps"].append(p.name)
    # Convert sets to sorted lists for JSON serialisation
    for nct, cur in scan["unique_ncts"].items():
        cur["names"] = sorted(cur["names"])
        cur["years"] = sorted(cur["years"])
    SCAN_FILE.write_text(json.dumps(scan, indent=2), encoding="utf-8")
    print(f"[scan] {len(scan['files'])} apps  |  {len(scan['unique_ncts'])} unique NCTs  |  "
          f"{sum(1 for c in scan['unique_ncts'].values() if not c['has_pmid_anywhere'])} need PMID lookup")
    return scan


# ---------------------------------------------------------------------------
# PHASE 2 — Europe PMC lookup
# ---------------------------------------------------------------------------

def _http_get_json(url: str, retries: int = 3) -> dict | None:
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "rapidmeta-pmid-lookup"})
            with urllib.request.urlopen(req, timeout=20) as r:
                if r.status != 200: return None
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:
            if attempt == retries - 1:
                print(f"  ! HTTP error (giving up) {e}")
                return None
            time.sleep(1.0 * (attempt + 1))
    return None


def _score_candidate(art: dict, trial: dict) -> tuple[int, dict]:
    """Score how likely `art` is the primary publication for `trial`.

    Key insight: acronym-in-title is a WEAK primary-paper signal. NEJM titles
    are generic ("Lumacaftor-Ivacaftor in Patients with..."); secondary
    analyses commonly include the acronym to refer back to the parent trial.
    Citation count + tier-1 journal + year match are the dominant signals."""
    score = 0
    reasons = {}
    title = (art.get("title") or "").strip()
    # Europe PMC nests journal info: journalInfo.journal.title
    journal = ((art.get("journalInfo") or {}).get("journal") or {}).get("title") or ""
    journal_lc = journal.strip().lower()
    pub_year = str(art.get("pubYear") or "").strip()
    pub_types = ((art.get("pubTypeList") or {}).get("pubType") or [])
    pub_types_lc = " ".join(p.lower() for p in pub_types if p)
    citations = int(art.get("citedByCount") or 0)
    title_lc = title.lower()

    # Citation tiers — single strongest signal for "this is the primary".
    if citations >= 2000:
        score += 6; reasons["cit_2000+"] = citations
    elif citations >= 500:
        score += 4; reasons["cit_500+"] = citations
    elif citations >= 100:
        score += 3; reasons["cit_100+"] = citations
    elif citations >= 30:
        score += 1; reasons["cit_30+"] = citations

    # Tier-1 journal bonus.
    if any(j in journal_lc for j in TIER1_JOURNALS):
        score += 3
        reasons["tier1_journal"] = journal

    # Clinical-trial pubType bonus — primary publications carry this MeSH tag.
    if "clinical trial" in pub_types_lc or "randomized controlled trial" in pub_types_lc:
        score += 2
        reasons["pub_type_ct"] = True

    # Year match (trial year = start; primary pub same or +1-3).
    if trial["years"] and pub_year.isdigit():
        ty = min(trial["years"])
        diff = int(pub_year) - ty
        if -1 <= diff <= 4:
            score += 3 - min(2, max(0, diff - 1))
            reasons["year_diff"] = diff

    # Acronym match — modest positive (often present in primary, often present
    # in secondaries too; not strongly discriminative).
    for n in trial["names"]:
        if n and len(n) >= 3 and n.lower() in title_lc:
            score += 2
            reasons["acronym_match"] = n
            break

    # Heavy penalty for clearly-secondary papers. The "association between" /
    # "predictors of" / "in subgroup" patterns are signature secondary-analysis
    # title openings. Catch them aggressively — false negatives are tolerable
    # because the cache is reviewable; false positives ship wrong PMIDs.
    SECONDARY_MARKERS = (
        "post hoc", "post-hoc", "subgroup", "subanalysis", "sub-analysis",
        "follow-up analysis", "long-term follow-up", "extended follow-up",
        "editorial", "comment on", "letter:", "correspondence",
        "review:", "meta-analysis", "systematic review", "narrative review",
        "questionnaire", "validation of", "translation of",
        "quality of life", "patient-reported", "health-related quality",
        "machine learning", "prediction model", "predictors of",
        "association between", "relationship between", "correlation between",
        "biomarker", "imaging marker", "aspects score",
        "cost-effectiveness", "economic evaluation", "budget impact",
        "rationale and design", "study design", "study protocol",
        "baseline characteristics", "design and rationale",
    )
    for bad in SECONDARY_MARKERS:
        if bad in title_lc:
            score -= 8
            reasons[f"penalty_{bad.replace(' ', '_').replace('-', '_').replace(':', '')}"] = True
            break

    # Pediatric / sub-population secondary papers ("X in children", "X in adolescents").
    if any(s in title_lc for s in (" in children", " in adolescent", " in pediatric")):
        score -= 4
        reasons["penalty_subpopulation"] = True

    # Must have an abstract — otherwise hydration can't use it anyway.
    if not (art.get("abstractText") or "").strip():
        score -= 2
        reasons["no_abstract"] = True

    return score, reasons


def _classify(score: int) -> str:
    # Typical primary paper: cit_500+(4) + tier1(3) + CT(2) + year(3) = 12 → HIGH
    # Strong primary: cit_2000+(6) + tier1(3) + CT(2) + year(3) = 14 → HIGH
    # Marginal primary: cit_100+(3) + tier1(3) + CT(2) + year(3) = 11 → HIGH
    # Weak: tier1(3) + CT(2) + year(3) = 8 → MED (low citations is suspicious)
    # No primary signal beyond a single match: 3-5 → LOW
    if score >= 10: return "HIGH"
    if score >= 6: return "MED"
    return "LOW"


def lookup_nct(nct: str, trial: dict) -> dict:
    """Query Europe PMC, score candidates, return best match + classification."""
    query = f'"{nct}" AND SRC:MED'
    # Sort by citation count (CITED desc) — primary trial publications are
    # almost always the most-cited article associated with the NCT ID.
    url = (f"{EUROPEPMC_SEARCH}?query={urllib.parse.quote(query)}"
           f"&resultType=core&pageSize=25&sort=CITED%20desc&format=json")
    data = _http_get_json(url) or {}
    candidates = (data.get("resultList") or {}).get("result") or []

    best, best_score, best_reasons = None, -999, {}
    for art in candidates:
        s, r = _score_candidate(art, trial)
        if s > best_score:
            best, best_score, best_reasons = art, s, r

    result = {
        "nct": nct,
        "candidate_count": len(candidates),
        "best_pmid": (best or {}).get("pmid"),
        "best_title": (best or {}).get("title"),
        "best_journal": ((best or {}).get("journalInfo") or {}).get("journal", {}).get("title"),
        "best_year": (best or {}).get("pubYear"),
        "best_citations": (best or {}).get("citedByCount"),
        "score": best_score if best else None,
        "confidence": _classify(best_score) if best else "NONE",
        "reasons": best_reasons,
    }
    return result


def phase_lookup(scan: dict, use_cache: bool = True) -> dict:
    cache: dict = {}
    if use_cache and CACHE_FILE.exists():
        cache = json.loads(CACHE_FILE.read_text(encoding="utf-8"))

    lookup = {"by_nct": {}, "stats": {"HIGH": 0, "MED": 0, "LOW": 0, "NONE": 0, "cached": 0, "fetched": 0, "skipped_has_pmid": 0}}
    to_lookup = [c for c in scan["unique_ncts"].values() if not c["has_pmid_anywhere"]]
    for trial in to_lookup:
        nct = trial["nct"]
        if nct in cache and use_cache:
            lookup["by_nct"][nct] = cache[nct]
            lookup["stats"]["cached"] += 1
        else:
            result = lookup_nct(nct, trial)
            cache[nct] = result
            lookup["by_nct"][nct] = result
            lookup["stats"]["fetched"] += 1
            time.sleep(RATE_LIMIT_SECONDS)
        lookup["stats"][lookup["by_nct"][nct]["confidence"]] += 1

    for c in scan["unique_ncts"].values():
        if c["has_pmid_anywhere"]:
            lookup["stats"]["skipped_has_pmid"] += 1

    CACHE_FILE.write_text(json.dumps(cache, indent=2), encoding="utf-8")
    LOOKUP_FILE.write_text(json.dumps(lookup, indent=2), encoding="utf-8")
    print(f"[lookup] fetched={lookup['stats']['fetched']}  cached={lookup['stats']['cached']}  "
          f"skipped={lookup['stats']['skipped_has_pmid']}")
    print(f"         confidence: HIGH={lookup['stats']['HIGH']}  MED={lookup['stats']['MED']}  "
          f"LOW={lookup['stats']['LOW']}  NONE={lookup['stats']['NONE']}")
    return lookup


# ---------------------------------------------------------------------------
# PHASE 3 — apply
# ---------------------------------------------------------------------------

CONF_RANK = {"HIGH": 3, "MED": 2, "LOW": 1, "NONE": 0}


def apply_pmids(scan: dict, lookup: dict, min_confidence: str, dry_run: bool) -> dict:
    """For every (file, NCT) without a PMID, write back `pmid: 'XXXXX', `
    immediately after `name: '...'` if the lookup confidence passes the bar."""
    bar = CONF_RANK[min_confidence.upper()]
    report = {"files": {}, "stats": {"files_touched": 0, "pmids_written": 0, "skipped_low_conf": 0, "skipped_has_pmid": 0}}

    for fname, entries in scan["files"].items():
        path = ROOT / fname
        text = path.read_text(encoding="utf-8", newline="")
        new_text = text
        file_writes = []
        for e in entries:
            nct = e["nct"]
            if e["has_pmid"]:
                report["stats"]["skipped_has_pmid"] += 1
                continue
            look = lookup["by_nct"].get(nct)
            if not look or CONF_RANK.get(look["confidence"], 0) < bar:
                report["stats"]["skipped_low_conf"] += 1
                continue

            # Inject `pmid: 'X', ` after the NCT's `name: '...'` literal.
            # Pairwise apps have `baseline: {...}` on a line BEFORE `name:`, so the
            # regex must allow arbitrary NCT-object content (including ONE level of
            # `{...}` nesting for the baseline dict) between `'NCT': {` and `name:`.
            injection_re = re.compile(
                r"('" + re.escape(nct) + r"'\s*:\s*\{(?:[^{}]|\{[^{}]*\})*?name\s*:\s*'[^']*',)\s*(?!pmid\s*:)",
                re.DOTALL,
            )
            replacement = r"\1 pmid: '" + look["best_pmid"] + "', "
            new_text, n = injection_re.subn(replacement, new_text, count=1)
            if n == 1:
                file_writes.append({"nct": nct, "pmid": look["best_pmid"], "confidence": look["confidence"]})
            else:
                file_writes.append({"nct": nct, "pmid": None, "error": f"injection pattern matched {n} times"})

        applied = [w for w in file_writes if w.get("pmid")]
        if applied and new_text != text:
            report["stats"]["files_touched"] += 1
            report["stats"]["pmids_written"] += len(applied)
            report["files"][fname] = file_writes
            if not dry_run:
                path.write_text(new_text, encoding="utf-8", newline="")

    APPLY_REPORT_FILE.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"[apply {'dry-run' if dry_run else 'WRITE'}] files_touched={report['stats']['files_touched']}  "
          f"pmids_written={report['stats']['pmids_written']}  "
          f"skipped_low_conf={report['stats']['skipped_low_conf']}  "
          f"skipped_has_pmid={report['stats']['skipped_has_pmid']}")
    return report


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--scan", action="store_true")
    ap.add_argument("--lookup", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--min-confidence", default="high", choices=["high", "med", "low"])
    ap.add_argument("--no-cache", action="store_true")
    args = ap.parse_args()

    if not any([args.scan, args.lookup, args.dry_run, args.apply]):
        ap.error("pass --scan, --lookup, --dry-run, or --apply")

    scan = phase_scan()
    if args.scan and not (args.lookup or args.dry_run or args.apply):
        return

    lookup = phase_lookup(scan, use_cache=not args.no_cache)
    if args.lookup and not (args.dry_run or args.apply):
        return

    if args.dry_run or args.apply:
        apply_pmids(scan, lookup, args.min_confidence, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
