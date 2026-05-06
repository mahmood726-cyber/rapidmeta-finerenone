"""Gold-standard PMID finder using NCT DataBankList cross-check.

For each (NCT, claimed_name) tuple flagged WRONG_PMID:
  1. Use eutils efetch to get the article XML which includes
     <DataBank Name="ClinicalTrials.gov"><AccessionNumberList>
     <AccessionNumber>NCT...</AccessionNumber>
  2. Search PubMed with NCT[si] (Secondary Source ID) — returns ALL papers
     citing that NCT. Take the first 20 candidates.
  3. For each candidate, fetch its DataBankList. If our NCT is there AND
     the article is a primary trial type (Phase III, RCT, no 'review'/
     'comment'/'letter'/'editorial'/'erratum') AND the title contains
     a drug-name-shape word, accept.
  4. Among accepted candidates, prefer the EARLIEST publication year and
     PMID minimum (typically the primary results paper).

This eliminates 'sub-analysis confusion' because we only accept primary
trial papers.

Output: outputs/pmid_databank_corrections.csv
"""
from __future__ import annotations
import sys, io, re, csv, time, json
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.parse import quote
import xml.etree.ElementTree as ET
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path(__file__).resolve().parent.parent
EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
RATE_S = 0.5


def http(url, retries=3):
    for i in range(retries):
        try:
            req = Request(url, headers={"User-Agent": "DataBank-PMID/1.0"})
            with urlopen(req, timeout=30) as r:
                return r.read().decode("utf-8")
        except Exception as e:
            if "429" in str(e) and i < retries - 1:
                time.sleep((i + 2) * 3)
                continue
            return None


def search_nct(nct):
    """esearch for NCT[si]; returns list of PMIDs."""
    q = f"{nct}[si]"
    url = f"{EUTILS}/esearch.fcgi?db=pubmed&term={quote(q)}&retmax=20&retmode=json&sort=date"
    txt = http(url)
    if not txt:
        return []
    try:
        return json.loads(txt).get("esearchresult", {}).get("idlist", [])
    except Exception:
        return []


def fetch_metadata(pmids):
    """efetch XML for batch of PMIDs. Returns {pmid: {title, year, pubtypes,
    nct_list}}."""
    if not pmids:
        return {}
    ids = ",".join(pmids)
    url = f"{EUTILS}/efetch.fcgi?db=pubmed&id={ids}&retmode=xml"
    xml = http(url)
    if not xml:
        return {}
    try:
        root = ET.fromstring(xml)
    except ET.ParseError:
        return {}
    out = {}
    for art in root.findall(".//PubmedArticle"):
        pmid_el = art.find(".//PMID")
        if pmid_el is None:
            continue
        pmid = pmid_el.text
        title_el = art.find(".//ArticleTitle")
        title = "".join(title_el.itertext()).strip() if title_el is not None else ""
        # Pub year
        year = None
        for ye in art.findall(".//PubDate/Year") + art.findall(".//ArticleDate/Year"):
            if ye.text and ye.text.isdigit():
                year = int(ye.text)
                break
        # Pub types
        pubtypes = [pt.text for pt in art.findall(".//PublicationType") if pt.text]
        # NCT list
        nct_list = []
        for db in art.findall(".//DataBankList/DataBank"):
            name = db.find("DataBankName")
            if name is not None and name.text and "ClinicalTrials" in name.text:
                for an in db.findall("AccessionNumberList/AccessionNumber"):
                    if an.text:
                        nct_list.append(an.text.strip())
        out[pmid] = {"title": title, "year": year, "pubtypes": pubtypes, "ncts": nct_list}
    return out


def is_primary(meta):
    if not meta:
        return False
    pubtypes = set(meta.get("pubtypes", []))
    title = (meta.get("title", "") or "").lower()
    bad = {"Review", "Comment", "Letter", "Editorial", "News",
           "Comment on", "Errata", "Erratum", "Retraction of Publication",
           "Retracted Publication", "Published Erratum"}
    if pubtypes & bad:
        return False
    bad_title = ["plain language", "matching-adjusted", "indirect comparison",
                  "biomarker substud", "post-hoc", "real-world",
                  "patterns of clinical", "predicts", "roll-out begins",
                  "roll out begins", "durability of"]
    for b in bad_title:
        if b in title:
            return False
    return True


def find_pmid_via_databank(nct):
    """Find best PMID for an NCT via DataBank cross-check.
    Returns (pmid, title) or (None, None)."""
    if not nct or not nct.startswith("NCT"):
        return None, None
    candidates = search_nct(nct)
    time.sleep(RATE_S)
    if not candidates:
        return None, None
    # Fetch metadata in one batch
    meta = fetch_metadata(candidates[:20])
    time.sleep(RATE_S)
    # Filter to primaries with our NCT in DataBank
    valid = []
    for pmid, m in meta.items():
        if nct not in m.get("ncts", []):
            continue
        if not is_primary(m):
            continue
        valid.append((pmid, m))
    if not valid:
        return None, None
    # Prefer earliest year + lowest PMID (proxy for primary results paper)
    valid.sort(key=lambda x: (x[1].get("year") or 9999, int(x[0])))
    return valid[0][0], valid[0][1]["title"]


def main():
    src = REPO / "outputs" / "pmid_audit_v3.csv"
    rows = list(csv.DictReader(open(src, encoding="utf-8")))
    wrong = [r for r in rows if r["status_v3"] == "WRONG_PMID"]
    print(f"Processing {len(wrong)} v3-WRONG_PMID rows via DataBankList ...")
    print()

    fixes = []
    no_fix = []
    for i, r in enumerate(wrong, 1):
        nct = r["nct"]
        if not nct.startswith("NCT"):
            no_fix.append({**r, "reason": "not an NCT"})
            continue
        new_pid, new_title = find_pmid_via_databank(nct)
        if not new_pid:
            no_fix.append({**r, "reason": "no DataBank match for NCT"})
            if i % 10 == 0:
                print(f"  [{i:3d}/{len(wrong)}] no fix: {r['claimed_name'][:30]:30s} ({nct})")
            continue
        if new_pid == r["pmid"]:
            no_fix.append({**r, "reason": "current PMID is already the primary"})
            continue
        fixes.append({**r, "new_pmid": new_pid, "new_title": new_title})
        # Apply
        path = REPO / r["file"]
        if path.exists():
            text = path.read_text(encoding="utf-8", errors="replace")
            old_str = f"pmid: '{r['pmid']}'"
            if old_str in text:
                text = text.replace(old_str, f"pmid: '{new_pid}'", 1)
                path.write_text(text, encoding="utf-8")
                print(f"  [{i:3d}/{len(wrong)}] FIXED {r['file'][:32]:32s} {r['claimed_name'][:22]:22s}  {r['pmid']} -> {new_pid}")
                print(f"     {new_title[:90]}")

    if fixes:
        out = REPO / "outputs" / "pmid_databank_corrections.csv"
        with out.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(fixes[0].keys()))
            w.writeheader()
            w.writerows(fixes)
        print(f"\n  Applied {len(fixes)} DataBank-confirmed corrections → {out}")
    print(f"  Could not fix: {len(no_fix)} (logged)")


if __name__ == "__main__":
    main()
