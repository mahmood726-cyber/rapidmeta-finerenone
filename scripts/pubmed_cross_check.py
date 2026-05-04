"""PubMed cross-check — verify every PMID claimed in every review HTML against the
PubMed E-utilities API (efetch). Detects:

  1. PMID doesn't exist (silent corruption — bibliographic ghost).
  2. PMID exists but year doesn't match snippet claim (off-by-year transcription error).
  3. PMID exists but title shares no tokens with claim_name AND no shared authors —
     potential trial-PMID misalignment.

Approach:
  - Extract all (file, key, name, pmid, year, snippet) tuples from realData blocks.
  - Batch PMIDs in groups of 200, call esummary, parse XML.
  - Compare each PMID record against the snippet's claim.

Output: outputs/pubmed_cross_check.csv

Usage:
    python scripts/pubmed_cross_check.py
"""
from __future__ import annotations
import csv
import re
import time
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path

REPO_DIR = Path("C:/Projects/Finrenone")
OUT_CSV = REPO_DIR / "outputs" / "pubmed_cross_check.csv"

PMID_BLOCK_RE = re.compile(
    r"'(NCT\d+(?:_[A-Za-z0-9]+)?|LEGACY-[A-Za-z0-9-]+)'\s*:\s*\{[^}]*?"
    r"name:\s*'([^']+?)'[^}]*?"
    r"pmid:\s*'(\d+)'[^}]*?"
    r"year:\s*(\d+)",
    re.DOTALL,
)

STOPWORDS = {
    "a", "an", "the", "of", "in", "for", "to", "and", "or", "with", "vs", "versus",
    "study", "trial", "phase", "randomized", "randomised", "double", "blind",
    "open", "label", "controlled", "placebo", "comparison", "evaluation",
    "efficacy", "safety", "treatment", "patients", "patient", "subjects",
    "evaluate", "compare", "assess", "single", "multicentre", "multicenter",
    "multi", "centre", "center", "international", "global",
}


def normalize_tokens(s: str) -> set[str]:
    if not s:
        return set()
    raw = re.split(r"[^a-z0-9]+", s.lower())
    return {t for t in raw if len(t) >= 3 and t not in STOPWORDS}


def extract_pmids_from_html(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8", errors="replace")
    out = []
    for m in PMID_BLOCK_RE.finditer(text):
        # Pull the surrounding group block to get authors / journal mention from snippet
        block_start = m.start()
        block_end = text.find("},", m.end())
        if block_end == -1:
            block_end = m.end() + 4000
        block = text[block_start:min(block_end, block_start + 4000)]
        gm = re.search(r"group:\s*'([^']+)'", block, re.DOTALL)
        group_text = gm.group(1) if gm else ""
        out.append({
            "key": m.group(1),
            "name": m.group(2),
            "pmid": m.group(3),
            "year": int(m.group(4)),
            "group": group_text,
        })
    return out


def fetch_pubmed_batch(pmids: list[str]) -> dict[str, dict]:
    """Call NCBI esummary for up to 200 PMIDs. Return {pmid: {title, pubdate, source, authors}}."""
    if not pmids:
        return {}
    url = (
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
        "?db=pubmed&retmode=xml&id=" + ",".join(pmids)
    )
    req = urllib.request.Request(url, headers={"User-Agent": "FinrenoneAuditTool/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            data = r.read()
    except Exception as e:
        print(f"  ERROR fetching batch: {e}")
        return {}

    root = ET.fromstring(data)
    out = {}
    for doc in root.findall("DocSum"):
        pmid_el = doc.find("Id")
        if pmid_el is None:
            continue
        pmid = pmid_el.text
        rec = {"title": "", "pubdate": "", "source": "", "authors": []}
        for item in doc.findall("Item"):
            n = item.get("Name")
            if n == "Title":
                rec["title"] = (item.text or "").strip()
            elif n == "PubDate":
                rec["pubdate"] = (item.text or "").strip()
            elif n == "Source":
                rec["source"] = (item.text or "").strip()
            elif n == "AuthorList":
                rec["authors"] = [a.text for a in item.findall("Item") if a.text]
        out[pmid] = rec
    return out


def extract_year_from_pubdate(pubdate: str) -> int | None:
    m = re.match(r"(\d{4})", pubdate)
    return int(m.group(1)) if m else None


def authors_in_snippet(snippet: str, authors: list[str]) -> int:
    """Count authors whose surname appears as a whole-word in snippet."""
    count = 0
    for a in authors[:5]:  # check first 5 authors
        # PubMed author format: "Lastname FM"
        last = a.split()[0] if a else ""
        if len(last) >= 3 and re.search(r"\b" + re.escape(last) + r"\b", snippet):
            count += 1
    return count


def main():
    review_files = sorted(REPO_DIR.glob("*_REVIEW.html"))
    print(f"Scanning {len(review_files)} review HTMLs ...")

    all_records = []
    for hp in review_files:
        for r in extract_pmids_from_html(hp):
            r["file"] = hp.name
            all_records.append(r)
    print(f"  extracted {len(all_records)} (file, NCT/key, PMID, year) records")

    unique_pmids = sorted({r["pmid"] for r in all_records})
    print(f"  {len(unique_pmids)} unique PMIDs")

    # Batch-fetch PubMed data
    pmid_db = {}
    BATCH = 200
    for i in range(0, len(unique_pmids), BATCH):
        batch = unique_pmids[i:i+BATCH]
        print(f"  fetching batch {i//BATCH + 1}/{(len(unique_pmids) + BATCH - 1)//BATCH} ({len(batch)} PMIDs) ...")
        pmid_db.update(fetch_pubmed_batch(batch))
        time.sleep(0.4)  # polite: NCBI rate limit 3/sec without API key

    print(f"  PubMed returned {len(pmid_db)} records ({len(unique_pmids) - len(pmid_db)} missing)")

    # Cross-check
    findings = []
    for r in all_records:
        pmid = r["pmid"]
        rec = pmid_db.get(pmid)
        verdict_parts = []

        if rec is None:
            verdict_parts.append("PMID_NOT_FOUND")
            pubmed_title = ""
            pubmed_year = None
            pubmed_journal = ""
            pubmed_first_author = ""
            year_diff = ""
            title_overlap = ""
            authors_in_snip = ""
        else:
            pubmed_title = rec["title"]
            pubmed_year = extract_year_from_pubdate(rec["pubdate"])
            pubmed_journal = rec["source"]
            pubmed_first_author = rec["authors"][0] if rec["authors"] else ""

            # Year check: allow ±1 year (publication-date vs trial-completion date)
            if pubmed_year is None:
                year_diff = "NA"
            else:
                year_diff = pubmed_year - r["year"]
                if abs(year_diff) > 1:
                    verdict_parts.append("YEAR_MISMATCH")

            # Title vs claim_name token check
            claim_tokens = normalize_tokens(r["name"])
            pmt_tokens = normalize_tokens(pubmed_title)
            title_overlap = len(claim_tokens & pmt_tokens)

            # Author-in-snippet check (more reliable when title is acronym-only)
            authors_in_snip = authors_in_snippet(r["group"], rec["authors"])

            # Verdict: trial likely WRONG-PMID if title 0 overlap AND 0 authors match snippet
            if title_overlap == 0 and authors_in_snip == 0:
                verdict_parts.append("TRIAL_PMID_MISALIGNED")

        verdict = "+".join(verdict_parts) if verdict_parts else "OK"

        findings.append({
            "file": r["file"],
            "key": r["key"],
            "claim_name": r["name"],
            "claim_year": r["year"],
            "pmid": pmid,
            "verdict": verdict,
            "pubmed_title": pubmed_title[:100],
            "pubmed_year": pubmed_year if pubmed_year is not None else "",
            "pubmed_journal": pubmed_journal[:40],
            "pubmed_first_author": pubmed_first_author,
            "year_diff": year_diff,
            "title_token_overlap": title_overlap,
            "authors_in_snippet": authors_in_snip,
        })

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(findings[0].keys()))
        w.writeheader()
        w.writerows(findings)

    by_verdict: dict[str, int] = {}
    for f in findings:
        by_verdict[f["verdict"]] = by_verdict.get(f["verdict"], 0) + 1

    print(f"\n=== Verdict counts (n={len(findings)}) ===")
    for k in sorted(by_verdict.keys()):
        print(f"  {k:40s} {by_verdict[k]}")

    # Real defects only
    issues = [f for f in findings if f["verdict"] != "OK"]
    print(f"\n=== {len(issues)} non-OK findings ===\n")
    for f in issues[:30]:
        print(f"  [{f['verdict']:30s}] {f['file']:50s} {f['key']:20s} pmid={f['pmid']}")
        print(f"     claim: {f['claim_name'][:50]:50s} year={f['claim_year']}")
        print(f"     pubmed: {f['pubmed_title'][:80]}")
        print(f"     pubmed_year={f['pubmed_year']} year_diff={f['year_diff']} title_overlap={f['title_token_overlap']} authors_in_snip={f['authors_in_snippet']}")
        print()
    if len(issues) > 30:
        print(f"  ... and {len(issues) - 30} more in {OUT_CSV}")


if __name__ == "__main__":
    main()
