"""For each NCT_MISMATCH or PMID_NOT_FOUND defect from pubmed_nct_linkage.csv,
look up the correct PMID(s) by searching PubMed with the NCT ID directly.

PubMed indexes ClinicalTrials.gov registration in [si] (secondary identifier) field.
A query like `NCT04191499[si]` returns all PubMed records that registered this trial.
For multi-PMID trials, returns multiple records (primary, follow-up, secondary).

Output: outputs/correct_pmid_suggestions.csv

Usage:
    python scripts/find_correct_pmids.py
"""
from __future__ import annotations
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
import csv
import re
import time
import urllib.request
import defusedxml.ElementTree as ET  # noqa: N817 — security: parse untrusted PubMed XML safely
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parent.parent
DEFECT_CSV = REPO_DIR / "outputs" / "pubmed_nct_linkage.csv"
OUT_CSV = REPO_DIR / "outputs" / "correct_pmid_suggestions.csv"


def esearch_nct(nct: str) -> list[str]:
    """Find PubMed records that registered this NCT via [si] field. Returns up to 20 PMIDs."""
    url = (
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        f"?db=pubmed&term={nct}[si]&retmax=20"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "FinrenoneAuditTool/2.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            data = r.read()
    except Exception as e:
        print(f"  esearch error for {nct}: {e}")
        return []
    root = ET.fromstring(data)
    return [el.text for el in root.findall(".//IdList/Id")]


def esummary_pmids(pmids: list[str]) -> dict[str, dict]:
    """Get title/year/journal for a small list of PMIDs."""
    if not pmids:
        return {}
    url = (
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
        "?db=pubmed&retmode=xml&id=" + ",".join(pmids)
    )
    req = urllib.request.Request(url, headers={"User-Agent": "FinrenoneAuditTool/2.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            data = r.read()
    except Exception as e:
        print(f"  esummary error: {e}")
        return {}
    root = ET.fromstring(data)
    out = {}
    for doc in root.findall("DocSum"):
        pmid_el = doc.find("Id")
        if pmid_el is None:
            continue
        pmid = pmid_el.text
        rec = {"title": "", "pubdate": "", "source": ""}
        for item in doc.findall("Item"):
            n = item.get("Name")
            if n == "Title":
                rec["title"] = (item.text or "").strip()
            elif n == "PubDate":
                rec["pubdate"] = (item.text or "").strip()
            elif n == "Source":
                rec["source"] = (item.text or "").strip()
        out[pmid] = rec
    return out


def main():
    rows = list(csv.DictReader(DEFECT_CSV.open(encoding="utf-8")))
    defects = [r for r in rows if r["verdict"] in ("NCT_MISMATCH", "PMID_NOT_FOUND")]
    print(f"Looking up correct PMIDs for {len(defects)} defects ...\n")

    out_rows = []
    for d in defects:
        nct = d["claim_nct"]
        if not nct:
            continue
        print(f"  {d['file'][:50]:50s} {nct}  (current bad pmid: {d['pmid']})")
        pmids = esearch_nct(nct)
        time.sleep(0.4)
        if not pmids:
            print(f"    no PubMed records found for {nct}[si]")
            out_rows.append({**d, "candidate_pmids": "", "candidate_titles": "", "best_match_pmid": "", "best_match_title": "", "best_match_year": ""})
            continue
        meta = esummary_pmids(pmids[:5])  # top 5
        time.sleep(0.4)

        # Pick best match: closest year to claim_year
        try:
            target_year = int(d["claim_year"])
        except (ValueError, TypeError):
            target_year = None

        best_pmid = ""
        best_title = ""
        best_year = ""
        best_score = 999
        for pmid, info in meta.items():
            yr_match = re.match(r"(\d{4})", info["pubdate"])
            yr = int(yr_match.group(1)) if yr_match else None
            if target_year is not None and yr is not None:
                score = abs(yr - target_year)
            else:
                score = 999
            if score < best_score:
                best_score = score
                best_pmid = pmid
                best_title = info["title"]
                best_year = yr if yr else ""

        cand_str = ",".join(pmids[:5])
        title_str = " | ".join(f'{p}:{meta.get(p, {}).get("title", "")[:40]}' for p in pmids[:5])

        print(f"    PubMed found {len(pmids)} record(s); best match: PMID {best_pmid} ({best_year}): {best_title[:60]}")
        out_rows.append({
            **d,
            "candidate_pmids": cand_str,
            "candidate_titles": title_str,
            "best_match_pmid": best_pmid,
            "best_match_title": best_title[:100],
            "best_match_year": best_year,
        })

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        if out_rows:
            w = csv.DictWriter(f, fieldnames=list(out_rows[0].keys()))
            w.writeheader()
            w.writerows(out_rows)

    print(f"\nWritten: {OUT_CSV}")


if __name__ == "__main__":
    main()
