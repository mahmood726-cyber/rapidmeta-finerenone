"""PubMed-NCT linkage check — authoritative cross-check via PubMed's own databanks field.

PubMed records that report clinical trials have a <DataBankList> in their XML metadata
listing the registry (ClinicalTrials.gov, ISRCTN, etc.) and the registration ID. If
my claim says PMID X is the report for trial NCT Y, then:
  - Fetch PMID X's databank list from efetch.
  - Verify NCT Y is among the registered NCTs.
  - If not → wrong PMID OR wrong NCT.

This is the most authoritative cross-check possible, short of human reading.

Output: outputs/pubmed_nct_linkage.csv
"""
from __future__ import annotations
import csv
import re
import time
import urllib.request
import defusedxml.ElementTree as ET  # noqa: N817 — security: parse untrusted PubMed XML safely
from pathlib import Path

REPO_DIR = Path("C:/Projects/Finrenone")
PRIOR_CSV = REPO_DIR / "outputs" / "pubmed_cross_check.csv"
OUT_CSV = REPO_DIR / "outputs" / "pubmed_nct_linkage.csv"


def fetch_pubmed_xml(pmids: list[str]) -> dict[str, dict]:
    """Fetch full PubMed XML for up to 200 PMIDs. Return per-PMID:
        {pmid: {title, year, journal, authors, databank_nct_ids[set], pub_types[list]}}
    """
    if not pmids:
        return {}
    url = (
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
        "?db=pubmed&retmode=xml&id=" + ",".join(pmids)
    )
    req = urllib.request.Request(url, headers={"User-Agent": "FinrenoneAuditTool/2.0"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            data = r.read()
    except Exception as e:
        print(f"  ERROR: {e}")
        return {}

    root = ET.fromstring(data)
    out = {}
    for art in root.findall(".//PubmedArticle"):
        pmid_el = art.find(".//PMID")
        if pmid_el is None:
            continue
        pmid = pmid_el.text
        title_el = art.find(".//ArticleTitle")
        title = "".join(title_el.itertext()) if title_el is not None else ""
        # Year
        year = None
        year_el = art.find(".//ArticleDate/Year")
        if year_el is None:
            year_el = art.find(".//Journal/JournalIssue/PubDate/Year")
        if year_el is not None:
            try:
                year = int(year_el.text)
            except (TypeError, ValueError):
                pass
        # Journal
        journal_el = art.find(".//Journal/Title")
        journal = journal_el.text if journal_el is not None else ""
        # Authors (first 3 surnames)
        authors = []
        for au in art.findall(".//AuthorList/Author")[:3]:
            ln = au.find("LastName")
            if ln is not None and ln.text:
                authors.append(ln.text)
        # DataBanks — registered trial IDs
        databank_ids = set()
        for db in art.findall(".//DataBank"):
            name_el = db.find("DataBankName")
            if name_el is None or not name_el.text:
                continue
            dbname = name_el.text
            for acc in db.findall(".//AccessionNumber"):
                if acc.text:
                    databank_ids.add(f"{dbname}:{acc.text.strip()}")
        # Publication types
        pub_types = [pt.text for pt in art.findall(".//PublicationType") if pt.text]

        out[pmid] = {
            "title": title,
            "year": year,
            "journal": journal,
            "authors": authors,
            "databank_ids": databank_ids,
            "pub_types": pub_types,
        }
    return out


def main():
    rows = list(csv.DictReader(PRIOR_CSV.open(encoding="utf-8")))
    print(f"Loaded {len(rows)} prior records from v1 CSV")

    # Unique PMIDs (skip ones already known not-found)
    pmids = sorted({r["pmid"] for r in rows if r["pubmed_title"]})
    print(f"Need full XML for {len(pmids)} PMIDs ...")

    db = {}
    BATCH = 150
    for i in range(0, len(pmids), BATCH):
        batch = pmids[i:i+BATCH]
        print(f"  batch {i//BATCH + 1}/{(len(pmids) + BATCH - 1)//BATCH} ({len(batch)} PMIDs)")
        db.update(fetch_pubmed_xml(batch))
        time.sleep(0.5)

    print(f"  fetched full XML for {len(db)} PMIDs")

    # Cross-check
    findings = []
    for r in rows:
        pmid = r["pmid"]
        rec = db.get(pmid)
        # Extract base NCT from r["key"]
        base_nct = None
        m = re.match(r"(NCT\d+)", r["key"])
        if m:
            base_nct = m.group(1)

        # Categorize
        if rec is None and not r["pubmed_title"]:
            # PMID not in PubMed at all
            verdict = "PMID_NOT_FOUND"
            registered_ncts = ""
            match = ""
        elif rec is None:
            verdict = "FETCH_FAILED"
            registered_ncts = ""
            match = ""
        else:
            registered_ncts_set = {x.split(":", 1)[1] for x in rec["databank_ids"] if x.startswith("ClinicalTrials.gov:")}
            registered_ncts = ",".join(sorted(registered_ncts_set))
            if not base_nct:
                verdict = "ISRCTN_KEY"
                match = ""
            elif not registered_ncts_set:
                # PubMed has no databank registration → can't verify; fall back to title check
                verdict = "NO_DATABANK"
                match = ""
            elif base_nct in registered_ncts_set:
                verdict = "OK"
                match = "YES"
            else:
                verdict = "NCT_MISMATCH"
                match = "NO"

        findings.append({
            "file": r["file"],
            "key": r["key"],
            "claim_name": r["claim_name"],
            "claim_year": r["claim_year"],
            "pmid": pmid,
            "verdict": verdict,
            "claim_nct": base_nct or "",
            "pubmed_registered_ncts": registered_ncts,
            "match": match,
            "pubmed_title": r["pubmed_title"][:100],
            "pubmed_year": r["pubmed_year"],
        })

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(findings[0].keys()))
        w.writeheader()
        w.writerows(findings)

    by_v: dict[str, int] = {}
    for f in findings:
        by_v[f["verdict"]] = by_v.get(f["verdict"], 0) + 1
    print(f"\n=== Verdict counts (n={len(findings)}) ===")
    for k in sorted(by_v.keys()):
        print(f"  {k:30s} {by_v[k]}")

    # Real defects: NCT_MISMATCH + PMID_NOT_FOUND
    defects = [f for f in findings if f["verdict"] in ("NCT_MISMATCH", "PMID_NOT_FOUND")]
    print(f"\n=== {len(defects)} authoritative real defects ===\n")
    for f in defects:
        print(f"  [{f['verdict']:18s}] {f['file'][:55]:55s} {f['key']:18s} pmid={f['pmid']}")
        print(f"     claim NCT: {f['claim_nct']}    PubMed registered NCTs: {f['pubmed_registered_ncts']}")
        print(f"     claim: {f['claim_name'][:50]}    pubmed: {f['pubmed_title'][:60]}")
        print()


if __name__ == "__main__":
    main()
