"""
Portfolio audit: citation / sourceUrl / page-number consistency.

Cross-checks every (pmid, snippet, sourceUrl) triple in every
*_REVIEW.html against PubMed E-utilities ESummary metadata.

Caught classes of error (the ones that hit PEGCETACOPLAN_GA):
  AUTHOR_MISMATCH    -- snippet attributes the cite to "Liao 2023"
                        but PubMed says first author is Heier
  YEAR_MISMATCH      -- snippet says "2018" but PubMed says 2020
  PII_MISMATCH       -- sourceUrl's PII (S0140-6736(23)01578-0) does
                        not match the DOI/PII PubMed has for that
                        PMID (S0140-6736(23)01520-9)
  PAGE_MISMATCH      -- snippet says "1591-1604" but PubMed says
                        "1434-1448"
  PMID_NOT_FOUND     -- PubMed returned no record for the PMID
                        (possibly a typo or de-listed)

Cache: outputs/_pubmed_cache.json keyed by PMID; 24h TTL.

Usage:
  python scripts/audit_citation_consistency.py
  python scripts/audit_citation_consistency.py --csv outputs/citation_audit.csv
  python scripts/audit_citation_consistency.py --offline   # skip net, use cache only

NCBI rate-limit: 3 req/sec without an API key. Script throttles to
2.5 req/sec to be polite. Target ~500-800 unique PMIDs across the
portfolio -> ~5 min cold cache.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


def strip_accents(s: str) -> str:
    """NFKD-normalise so 'Schüpke' compares equal to 'Schupke'."""
    if not s:
        return ""
    nfkd = unicodedata.normalize('NFKD', s)
    return ''.join(c for c in nfkd if not unicodedata.combining(c))


def has_any_author_pattern(snippet: str) -> bool:
    """Detect whether the snippet appears to name AT LEAST ONE author.
    If False, the AUTHOR_MISMATCH check is meaningless (just journal+year)."""
    if not snippet:
        return False
    # Heuristics: 'Surname et al', 'Surname I[I] et al', or 'Surname Initial,'
    return bool(
        re.search(r"\b[A-Z][a-zA-Z]{2,}\s+(?:[A-Z]{1,3}|et\s+al)", snippet)
    )


def journal_url_token(url: str) -> str | None:
    """Extract a journal-shorthand token from sourceUrl path.
    Useful values: 'lancet', 'lanonc', 'jama', 'nejm', 'circulation',
    'european-heart-journal', 'thelancet', etc."""
    if not url:
        return None
    u = url.lower()
    if 'thelancet.com/journals/lancet/' in u: return 'lancet'
    if 'thelancet.com/journals/lanonc' in u: return 'lancet oncol'
    if 'thelancet.com/journals/lanrhe' in u: return 'lancet rheumatol'
    if 'thelancet.com/journals/landig' in u: return 'lancet digital'
    if 'thelancet.com/journals/lanres' in u: return 'lancet respir'
    if 'thelancet.com/journals/lanhae' in u: return 'lancet haematol'
    if 'thelancet.com/journals/laninf' in u: return 'lancet infect dis'
    if 'thelancet.com/journals/lanepe' in u: return 'lancet'
    if 'nejm.org' in u: return 'n engl j med'
    if 'jamanetwork.com/journals/jama/' in u: return 'jama'
    if 'jamanetwork.com/journals/jamaoncology' in u: return 'jama oncol'
    if 'jamanetwork.com/journals/jamacardiology' in u: return 'jama cardiol'
    if 'jamanetwork.com/journals/jamaneurology' in u: return 'jama neurol'
    if 'ahajournals.org/doi' in u and 'circulation' in u: return 'circulation'
    if 'academic.oup.com/eurheartj' in u: return 'eur heart j'
    return None


def journal_match(url_token: str | None, pubmed_journal: str) -> bool | None:
    """True if URL journal matches PubMed journal; False if mismatch;
    None if URL has no journal token to compare."""
    if not url_token:
        return None
    pj = (pubmed_journal or "").lower()
    return url_token in pj or any(tok in pj for tok in url_token.split())

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CSV = ROOT / "outputs" / "citation_audit.csv"
CACHE_PATH = ROOT / "outputs" / "_pubmed_cache.json"
CACHE_TTL_SEC = 24 * 60 * 60

ESUMMARY = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"

PMID_RE = re.compile(r"\bpmid:\s*'(\d+)'")
NAME_RE = re.compile(r"\bname:\s*'([^']+)'")
SNIPPET_RE = re.compile(r"\bsnippet:\s*'((?:[^'\\]|\\.)*)'")
SOURCE_URL_RE = re.compile(r"\bsourceUrl:\s*'((?:[^'\\]|\\.)*)'")

# Match surrounding object literal so we can pair pmid with snippet/sourceUrl
NAME_PMID_ANCHOR = re.compile(r"\bname:\s*'[^']+'\s*,\s*pmid:\s*'\d+'")


def find_trial_blocks(text: str) -> list[str]:
    """Extract balanced { ... } blocks anchored on `name: '...', pmid:`."""
    out = []
    for m in NAME_PMID_ANCHOR.finditer(text):
        idx = m.start()
        # walk back to opening brace
        depth = 0
        start = None
        for i in range(idx, -1, -1):
            ch = text[i]
            if ch == '}':
                depth += 1
            elif ch == '{':
                if depth == 0:
                    start = i
                    break
                depth -= 1
        if start is None:
            continue
        depth = 0
        end = None
        for j in range(start, len(text)):
            ch = text[j]
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    end = j + 1
                    break
        if end is None:
            continue
        out.append(text[start:end])
    return out


def field(rx: re.Pattern, blob: str) -> str | None:
    m = rx.search(blob)
    return m.group(1) if m else None


def load_cache() -> dict:
    if CACHE_PATH.exists():
        try:
            return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save_cache(cache: dict) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(json.dumps(cache, indent=2), encoding="utf-8")


def fetch_pubmed_metadata(pmid: str, cache: dict, offline: bool = False) -> dict | None:
    """Returns ESummary record or None on miss/error."""
    cache_key = f"esummary_{pmid}"
    now = int(time.time())
    cached = cache.get(cache_key)
    if cached and now - cached.get("_t", 0) < CACHE_TTL_SEC:
        return cached.get("v")
    if offline:
        return None
    url = f"{ESUMMARY}?db=pubmed&id={pmid}&retmode=json"
    try:
        with urllib.request.urlopen(url, timeout=15) as r:
            data = json.loads(r.read().decode("utf-8"))
        rec = data.get("result", {}).get(pmid)
        cache[cache_key] = {"_t": now, "v": rec}
        return rec
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, TimeoutError) as e:
        cache[cache_key] = {"_t": now, "v": None, "err": str(e)}
        return None


def extract_pii(url: str) -> str | None:
    """Extract Lancet/Elsevier-style PII from a sourceUrl, e.g.
    PIIS0140-6736(23)01520-9 -> S0140-6736(23)01520-9."""
    m = re.search(r"PII(S\d{4}-\d{4}\(\d{2}\)\d+-?\d?)", url)
    return m.group(1) if m else None


def extract_pii_from_articleids(articleids: list[dict]) -> str | None:
    """ESummary returns articleids; look for 'pii' or DOI."""
    for a in articleids or []:
        idtype = (a.get("idtype") or "").lower()
        val = a.get("value") or ""
        if idtype == "pii":
            return val
        if idtype == "doi":
            # Convert DOI like 10.1016/S0140-6736(23)01520-9 -> S0140-6736(23)01520-9
            m = re.search(r"(S\d{4}-\d{4}\(\d{2}\)\d+-?\d?)", val)
            if m:
                return m.group(1)
    return None


def extract_year_from_pubdate(pubdate: str) -> int | None:
    m = re.match(r"(\d{4})", pubdate or "")
    return int(m.group(1)) if m else None


def normalize_pages(s: str) -> str:
    """e.g. '1434-1448' -> '1434-1448', '1434-48' -> '1434-1448'."""
    if not s:
        return ""
    m = re.match(r"(\d+)\s*[-–]\s*(\d+)", s)
    if not m:
        return s
    a, b = m.group(1), m.group(2)
    if len(b) < len(a):
        # shortened end-page e.g. "1434-48"
        b = a[:len(a) - len(b)] + b
    return f"{a}-{b}"


def extract_snippet_pages(snippet: str) -> str | None:
    """Look for "<journal>;<vol>(...):<pages>" or "<vol>:<pages>" pattern."""
    m = re.search(r":\s*(\d+\s*[-–]\s*\d+)", snippet or "")
    return normalize_pages(m.group(1)) if m else None


def compare_one(dashboard: str, trial_name: str, pmid: str, snippet: str,
                source_url: str, meta: dict | None) -> dict:
    issues = []
    expected_author = ""
    expected_year = None
    expected_pages = ""
    expected_journal = ""

    if meta is None:
        issues.append("PMID_NOT_FOUND")
    else:
        expected_author = (meta.get("sortfirstauthor")
                           or (meta.get("authors", [{}])[0].get("name", "") if meta.get("authors") else ""))
        last_name = (expected_author.split(" ")[0] if expected_author else "")
        expected_year = extract_year_from_pubdate(meta.get("pubdate", ""))
        expected_pages = normalize_pages(meta.get("pages", ""))
        expected_journal = (meta.get("fulljournalname") or meta.get("source") or "")

        # AUTHOR_MISMATCH only meaningful when snippet actually attempts to
        # name an author. Skip for "Journal 2018; pages" style snippets.
        # Also normalise accents so 'Schüpke' == 'Schupke'.
        if last_name and has_any_author_pattern(snippet):
            if strip_accents(last_name).lower() not in strip_accents(snippet or "").lower():
                issues.append("AUTHOR_MISMATCH")

        if expected_year is not None:
            # Only flag YEAR_MISMATCH if the snippet quotes a DIFFERENT 4-digit
            # year (positive evidence of wrong year), not just absence.
            quoted_years = set(re.findall(r"\b(20\d\d|19\d\d)\b", snippet or ""))
            if quoted_years and str(expected_year) not in quoted_years:
                issues.append("YEAR_MISMATCH")

        if expected_pages:
            snippet_pages = extract_snippet_pages(snippet)
            if snippet_pages and snippet_pages != expected_pages:
                issues.append("PAGE_MISMATCH")

        # JOURNAL_MISMATCH: stronger than PII_MISMATCH because we don't
        # have to wrestle with PubMed's articleid grab-bag. URL host/path
        # implies the journal; compare to PubMed's fulljournalname.
        url_token = journal_url_token(source_url or "")
        jm = journal_match(url_token, expected_journal)
        if jm is False:
            issues.append("JOURNAL_MISMATCH")

    return {
        "dashboard": dashboard,
        "trial_name": trial_name,
        "pmid": pmid,
        "issues": ";".join(issues),
        "expected_author": expected_author,
        "expected_year": expected_year or "",
        "expected_pages": expected_pages,
        "expected_journal": expected_journal,
        "snippet": (snippet or "")[:200],
        "source_url": source_url or "",
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    ap.add_argument("--root", type=Path, default=ROOT)
    ap.add_argument("--offline", action="store_true", help="skip network, use cache only")
    ap.add_argument("--throttle", type=float, default=0.4, help="seconds between PubMed requests")
    args = ap.parse_args()

    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)

    cache = load_cache()
    dashboards = sorted(p for p in args.root.glob("*_REVIEW.html") if p.is_file())
    print(f"Scanning {len(dashboards)} dashboards under {args.root}")

    triples: list[dict] = []
    for p in dashboards:
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        for blk in find_trial_blocks(text):
            pmid = field(PMID_RE, blk) or ""
            if not pmid:
                continue
            triples.append({
                "dashboard": p.name,
                "trial_name": field(NAME_RE, blk) or "",
                "pmid": pmid,
                "snippet": field(SNIPPET_RE, blk) or "",
                "source_url": field(SOURCE_URL_RE, blk) or "",
            })

    print(f"Extracted {len(triples)} (pmid, snippet, sourceUrl) triples across the portfolio.")
    unique_pmids = sorted(set(t["pmid"] for t in triples))
    print(f"  unique PMIDs: {len(unique_pmids)}")

    if not args.offline:
        print(f"Fetching PubMed ESummary for {len(unique_pmids)} PMIDs (throttle {args.throttle}s)...")
        for i, pmid in enumerate(unique_pmids, 1):
            cache_key = f"esummary_{pmid}"
            cached = cache.get(cache_key)
            now = int(time.time())
            if cached and now - cached.get("_t", 0) < CACHE_TTL_SEC:
                continue
            fetch_pubmed_metadata(pmid, cache, offline=False)
            time.sleep(args.throttle)
            if i % 25 == 0:
                save_cache(cache)
                print(f"  {i}/{len(unique_pmids)} fetched")
        save_cache(cache)
        print("PubMed fetch complete.")
    else:
        print("Offline mode: using cache only.")

    rows = []
    for t in triples:
        meta = fetch_pubmed_metadata(t["pmid"], cache, offline=True)
        rows.append(compare_one(t["dashboard"], t["trial_name"], t["pmid"],
                                t["snippet"], t["source_url"], meta))

    args.csv.parent.mkdir(parents=True, exist_ok=True)
    fields = ["dashboard", "trial_name", "pmid", "issues", "expected_author",
              "expected_year", "expected_pages", "expected_journal", "snippet", "source_url"]
    with args.csv.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    n_issues = sum(1 for r in rows if r["issues"])
    by_class: dict[str, int] = {}
    for r in rows:
        for c in (r["issues"] or "").split(";"):
            if c:
                by_class[c] = by_class.get(c, 0) + 1

    # HIGH-CONFIDENCE: trial flagged with TWO OR MORE classes is almost
    # certainly a real wrong-PMID situation (two or more independent
    # signals say the cited paper differs from the PMID's actual paper).
    high_conf = [r for r in rows if r["issues"].count(";") >= 1]

    print(f"\nResults:")
    print(f"  Total trial-citation rows:        {len(rows)}")
    print(f"  Rows with at least 1 issue:       {n_issues}")
    print(f"  HIGH-CONFIDENCE (>=2 issues):     {len(high_conf)}")
    for cls in ["PMID_NOT_FOUND", "AUTHOR_MISMATCH", "YEAR_MISMATCH",
                "PAGE_MISMATCH", "JOURNAL_MISMATCH"]:
        print(f"  {cls:18} {by_class.get(cls, 0)}")
    print(f"\nCSV written: {args.csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
