"""
Auto-propose PMID corrections for HIGH-CONFIDENCE wrong-PMID rows
identified by audit_citation_consistency.py.

Strategy (per row):
  1. Parse the dashboard's snippet for: author surname, initials,
     year, journal token, trial acronym (from the `name` field).
  2. Build a PubMed esearch query that combines these signals plus
     the trial acronym (often the strongest single signal).
  3. ESummary each result (top 5).
  4. Score each candidate against the snippet's claimed metadata:
       +3 if first-author surname matches
       +2 if year matches (±1 tolerance)
       +2 if journal token matches PubMed fulljournalname
       +2 if trial acronym appears in PubMed title
       -2 if pubtype is editorial/correction/letter (not the trial)
  5. Propose the top candidate ONLY when:
       - top score >= 6 (multiple signals aligned)
       - top score - second score >= 3 (clear winner)
     Otherwise mark AMBIGUOUS.

Output: outputs/pmid_corrections.csv with columns
  dashboard, trial_name, current_pmid, proposed_pmid, status,
  proposed_author, proposed_year, proposed_journal, proposed_title,
  candidates (top 3 with scores), reason

Usage:
  python scripts/propose_pmid_corrections.py
  python scripts/propose_pmid_corrections.py --offline  # cache only
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
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AUDIT_CSV = ROOT / "outputs" / "citation_audit.csv"
OUT_CSV = ROOT / "outputs" / "pmid_corrections.csv"
CACHE_PATH = ROOT / "outputs" / "_pubmed_cache.json"
CACHE_TTL_SEC = 24 * 60 * 60

ESEARCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
ESUMMARY = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"


def strip_accents(s: str) -> str:
    nfkd = unicodedata.normalize('NFKD', s or "")
    return ''.join(c for c in nfkd if not unicodedata.combining(c))


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


def cache_get(cache: dict, key: str):
    rec = cache.get(key)
    if not rec:
        return None
    if int(time.time()) - rec.get("_t", 0) > CACHE_TTL_SEC:
        return None
    return rec.get("v")


def cache_put(cache: dict, key: str, value) -> None:
    cache[key] = {"_t": int(time.time()), "v": value}


def esearch_pmids(query: str, cache: dict, offline: bool = False) -> list[str]:
    key = f"esearch_{query}"
    cached = cache_get(cache, key)
    if cached is not None:
        return cached
    if offline:
        return []
    url = f"{ESEARCH}?db=pubmed&term={urllib.parse.quote(query)}&retmax=10&retmode=json"
    try:
        with urllib.request.urlopen(url, timeout=15) as r:
            data = json.loads(r.read().decode("utf-8"))
        ids = data.get("esearchresult", {}).get("idlist", [])
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError):
        ids = []
    cache_put(cache, key, ids)
    return ids


def esummary_one(pmid: str, cache: dict, offline: bool = False) -> dict | None:
    key = f"esummary_{pmid}"
    cached = cache_get(cache, key)
    if cached is not None:
        return cached
    if offline:
        return None
    url = f"{ESUMMARY}?db=pubmed&id={pmid}&retmode=json"
    try:
        with urllib.request.urlopen(url, timeout=15) as r:
            data = json.loads(r.read().decode("utf-8"))
        rec = data.get("result", {}).get(pmid)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError):
        rec = None
    cache_put(cache, key, rec)
    return rec


# ---- snippet parsing ----

SNIPPET_AUTHOR_RE = re.compile(
    r"(?:Source:\s*)?([A-Z][a-zA-Z'\-]+)\s+([A-Z]{1,3})(?:[A-Z\s,]*)?(?:\s+et\s+al)?",
)
JOURNAL_TOKEN_PATTERNS = {
    'NEJM': 'n engl j med',
    'N Engl J Med': 'n engl j med',
    'Lancet Oncol': 'lancet oncol',
    'Lancet Rheumatol': 'lancet rheumatol',
    'Lancet Respir': 'lancet respir',
    'Lancet Haematol': 'lancet haematol',
    'Lancet Infect': 'lancet infect',
    'Lancet Neurol': 'lancet neurol',
    'Lancet Diabetes': 'lancet diabetes',
    'Lancet Glob Health': 'lancet global health',
    'Lancet HIV': 'lancet hiv',
    'Lancet Digital': 'lancet digital',
    'Lancet': 'lancet',
    'JAMA Oncol': 'jama oncol',
    'JAMA Cardiol': 'jama cardiol',
    'JAMA Neurol': 'jama neurol',
    'JAMA Intern': 'jama intern',
    'JAMA Network': 'jama network',
    'JAMA': 'jama',
    'Circulation': 'circulation',
    'Eur Heart J': 'eur heart j',
    'Ann Intern Med': 'ann intern med',
    'Ann Rheum Dis': 'ann rheum dis',
    'Ann Oncol': 'ann oncol',
    'JCO': 'j clin oncol',
    'J Clin Oncol': 'j clin oncol',
    'BMJ': 'bmj',
    'Ophthalmology': 'ophthalmology',
    'Diabetes Care': 'diabetes care',
    'Hypertension': 'hypertension',
    'JAMA Dermatol': 'jama dermatol',
    'JAMA Ophthalmol': 'jama ophthalmol',
    'Blood': 'blood',
    'Kidney Int': 'kidney int',
    'Hepatology': 'hepatology',
    'Gut': 'gut',
    'Gastroenterology': 'gastroenterology',
    'Am J Hematol': 'am j hematol',
    'Stroke': 'stroke',
    'JACC': 'j am coll cardiol',
    'J Am Coll Cardiol': 'j am coll cardiol',
}


def parse_snippet(snippet: str) -> dict:
    """Returns dict with surname, initials, year, journal_token (lowercased PubMed-style)."""
    out = {"surname": None, "initials": None, "year": None, "journal_token": None,
           "raw_journal": None}
    if not snippet:
        return out
    # author
    m = SNIPPET_AUTHOR_RE.search(snippet)
    if m:
        s = m.group(1)
        # Skip "Source" / "Et" false positives
        if s.lower() not in ("source", "et", "the"):
            out["surname"] = s
            out["initials"] = m.group(2)
    # year
    yr = re.search(r"\b(20\d\d|19\d\d)\b", snippet)
    if yr:
        out["year"] = int(yr.group(1))
    # journal: longest matching token
    snippet_lower = snippet.lower()
    best_match = ("", "", 0)  # (raw, pubmed_token, length)
    for raw, tok in JOURNAL_TOKEN_PATTERNS.items():
        if raw.lower() in snippet_lower:
            if len(raw) > best_match[2]:
                best_match = (raw, tok, len(raw))
    if best_match[0]:
        out["raw_journal"] = best_match[0]
        out["journal_token"] = best_match[1]
    return out


# ---- candidate scoring ----

def score_candidate(meta: dict, parsed: dict, trial_acronym: str | None) -> tuple[int, list[str]]:
    if not meta:
        return -100, ["no_meta"]
    score = 0
    reasons = []
    pubmed_first_author = (meta.get("sortfirstauthor") or "").split(" ")[0]
    pubmed_year = ""
    yr = re.match(r"(\d{4})", meta.get("pubdate") or "")
    if yr:
        pubmed_year = yr.group(1)
    pubmed_journal = (meta.get("fulljournalname") or "").lower()
    pubmed_title = (meta.get("title") or "").lower()
    pubtypes = [pt.lower() for pt in (meta.get("pubtype") or [])]

    if parsed["surname"] and pubmed_first_author:
        if strip_accents(parsed["surname"]).lower() == strip_accents(pubmed_first_author).lower():
            score += 3
            reasons.append("author+3")
    if parsed["year"] and pubmed_year:
        if abs(int(pubmed_year) - parsed["year"]) <= 1:
            score += 2
            reasons.append("year+2")
    if parsed["journal_token"] and pubmed_journal:
        if parsed["journal_token"] in pubmed_journal:
            score += 2
            reasons.append("journal+2")
    if trial_acronym and pubmed_title:
        # Strip non-alphanumeric for fuzzy compare; allow partial.
        ta_clean = re.sub(r"[^a-z0-9]", "", trial_acronym.lower())
        pt_clean = re.sub(r"[^a-z0-9]", "", pubmed_title)
        if ta_clean and ta_clean in pt_clean:
            score += 2
            reasons.append("acronym_in_title+2")
    # Penalize editorial/correction/letter pubtypes
    bad_types = {"editorial", "comment", "letter", "correction", "published erratum",
                 "retraction of publication", "expression of concern"}
    if any(any(bt in pt for bt in bad_types) for pt in pubtypes):
        score -= 4
        reasons.append("badtype-4")
    return score, reasons


def build_query(parsed: dict, trial_acronym: str | None) -> str | None:
    parts = []
    if trial_acronym and len(trial_acronym) >= 3:
        parts.append(f'"{trial_acronym}"[Title/Abstract]')
    if parsed["surname"]:
        parts.append(f'{parsed["surname"]}[Author]')
    if parsed["year"]:
        parts.append(f'{parsed["year"]}[PDAT]')
    if not parts:
        return None
    return " AND ".join(parts)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--audit-csv", type=Path, default=AUDIT_CSV)
    ap.add_argument("--out-csv", type=Path, default=OUT_CSV)
    ap.add_argument("--offline", action="store_true")
    ap.add_argument("--throttle", type=float, default=0.4)
    ap.add_argument("--limit", type=int, default=0, help="cap number of rows processed (0=all)")
    args = ap.parse_args()

    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)

    cache = load_cache()

    with args.audit_csv.open(encoding="utf-8") as fh:
        all_rows = list(csv.DictReader(fh))
    high_conf = [r for r in all_rows if r["issues"].count(";") >= 1]
    if args.limit:
        high_conf = high_conf[:args.limit]
    print(f"Processing {len(high_conf)} high-confidence wrong-PMID rows")

    out_rows = []
    for i, row in enumerate(high_conf, 1):
        snippet = row["snippet"]
        trial_name = row["trial_name"]
        parsed = parse_snippet(snippet)
        query = build_query(parsed, trial_name)
        proposal = {
            "dashboard": row["dashboard"],
            "trial_name": trial_name,
            "current_pmid": row["pmid"],
            "snippet": snippet[:200],
            "parsed_surname": parsed["surname"] or "",
            "parsed_year": parsed["year"] or "",
            "parsed_journal": parsed["raw_journal"] or "",
            "query": query or "",
            "proposed_pmid": "",
            "proposed_author": "",
            "proposed_year": "",
            "proposed_journal": "",
            "proposed_title": "",
            "top_score": 0,
            "second_score": 0,
            "status": "",
            "candidates": "",
            "reason": "",
        }
        if not query:
            proposal["status"] = "INSUFFICIENT_SNIPPET"
            proposal["reason"] = "snippet has no parsable author/year"
            out_rows.append(proposal)
            continue

        ids = esearch_pmids(query, cache, offline=args.offline)
        if not args.offline:
            time.sleep(args.throttle)

        if not ids:
            proposal["status"] = "NO_PUBMED_HITS"
            proposal["reason"] = f"esearch returned 0 hits for: {query}"
            out_rows.append(proposal)
            continue

        # Score each candidate
        scored = []
        for pid in ids[:8]:
            meta = esummary_one(pid, cache, offline=args.offline)
            if not args.offline and meta is None:
                time.sleep(args.throttle)
                meta = esummary_one(pid, cache, offline=args.offline)
            if not meta:
                continue
            score, reasons = score_candidate(meta, parsed, trial_name)
            scored.append({
                "pmid": pid,
                "score": score,
                "reasons": reasons,
                "author": (meta.get("sortfirstauthor") or "").split(" ")[0],
                "year": (re.match(r"(\d{4})", meta.get("pubdate") or "") or [None, ""])[1] if meta.get("pubdate") else "",
                "journal": meta.get("fulljournalname") or "",
                "title": (meta.get("title") or "")[:120],
            })
        scored.sort(key=lambda c: c["score"], reverse=True)
        if not scored:
            proposal["status"] = "ALL_LOOKUPS_FAILED"
            out_rows.append(proposal)
            continue

        top = scored[0]
        second_score = scored[1]["score"] if len(scored) > 1 else -100
        proposal["top_score"] = top["score"]
        proposal["second_score"] = second_score
        proposal["candidates"] = " | ".join(
            f"{c['pmid']}({c['score']},{c['author']},{c['year']})" for c in scored[:3]
        )
        # Decision: UNAMBIGUOUS only when top score >= 6 AND clear winner
        if top["score"] >= 6 and (top["score"] - second_score) >= 3:
            proposal["status"] = "UNAMBIGUOUS"
            proposal["proposed_pmid"] = top["pmid"]
            proposal["proposed_author"] = top["author"]
            proposal["proposed_year"] = top["year"]
            proposal["proposed_journal"] = top["journal"]
            proposal["proposed_title"] = top["title"]
            proposal["reason"] = ";".join(scored[0]["reasons"])
        elif top["score"] >= 4:
            proposal["status"] = "PROBABLE"
            proposal["proposed_pmid"] = top["pmid"]
            proposal["proposed_author"] = top["author"]
            proposal["proposed_year"] = top["year"]
            proposal["proposed_journal"] = top["journal"]
            proposal["proposed_title"] = top["title"]
            proposal["reason"] = f"top score {top['score']} but second is {second_score} (delta only {top['score']-second_score})"
        else:
            proposal["status"] = "AMBIGUOUS"
            proposal["reason"] = f"top score {top['score']} is too weak (need >=4)"
        out_rows.append(proposal)
        if i % 10 == 0:
            save_cache(cache)
            print(f"  {i}/{len(high_conf)} processed")

    save_cache(cache)

    args.out_csv.parent.mkdir(parents=True, exist_ok=True)
    fields = ["dashboard", "trial_name", "current_pmid", "snippet",
              "parsed_surname", "parsed_year", "parsed_journal", "query",
              "proposed_pmid", "proposed_author", "proposed_year",
              "proposed_journal", "proposed_title",
              "top_score", "second_score", "status", "candidates", "reason"]
    with args.out_csv.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(out_rows)

    by_status = {}
    for r in out_rows:
        by_status[r["status"]] = by_status.get(r["status"], 0) + 1
    print()
    print("Proposal status breakdown:")
    for k, v in sorted(by_status.items(), key=lambda x: -x[1]):
        print(f"  {k:24} {v}")
    print()
    print(f"Output: {args.out_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
