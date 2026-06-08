"""Resolve PMIDs for NCTs missing from the AACT pmid_resolver map, with
structured verification to avoid misattribution.

For each unresolved NCT:
  1. esearch PubMed for the NCT (All Fields) -> candidate PMIDs.
  2. efetch each candidate; accept ONLY if the NCT appears in the article's
     <DataBankList> (ClinicalTrials.gov AccessionNumber) AND the article is a
     primary trial type (not review/comment/letter/editorial/erratum).
  3. Among accepted, prefer the earliest publication year (primary results).

Writes outputs/pmid_resolver/nct_to_pmid_recovered.json (verified only). Never
guesses. Run apply_recovered_pmids() / the --apply flag to inject into apps.
"""
from __future__ import annotations
import io, json, re, sys, time
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.parse import quote
import xml.etree.ElementTree as ET

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
REPO = Path(__file__).resolve().parent.parent
EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
NONPRIMARY = re.compile(r"review|comment|letter|editorial|erratum|retraction|"
                        r"meta-analysis|systematic review", re.I)


def _get(url, tries=3):
    for i in range(tries):
        try:
            req = Request(url, headers={"User-Agent": "rapidmeta-pmid-resolver"})
            return urlopen(req, timeout=20).read()
        except Exception:
            time.sleep(1.5 * (i + 1))
    return b""


def esearch(nct):
    url = f"{EUTILS}/esearch.fcgi?db=pubmed&retmode=json&retmax=15&term={quote(nct)}"
    try:
        return json.loads(_get(url))["esearchresult"].get("idlist", [])
    except Exception:
        return []
    finally:
        time.sleep(0.34)


def verify(pmid, nct):
    """Return (year:int) if pmid's DataBankList registers nct and it's a
    primary trial type, else None."""
    url = f"{EUTILS}/efetch.fcgi?db=pubmed&id={pmid}&retmode=xml"
    raw = _get(url)
    time.sleep(0.34)
    if not raw:
        return None
    try:
        root = ET.fromstring(raw)
    except ET.ParseError:
        return None
    accs = [e.text for e in root.iter("AccessionNumber")]
    if nct not in (accs or []):
        return None
    ptypes = " ".join(e.text or "" for e in root.iter("PublicationType"))
    title = " ".join(e.text or "" for e in root.iter("ArticleTitle"))
    if NONPRIMARY.search(ptypes) or NONPRIMARY.search(title):
        return None
    yr = root.find(".//PubDate/Year")
    return int(yr.text) if (yr is not None and yr.text and yr.text.isdigit()) else 9999


def resolve(ncts):
    recovered = {}
    for i, nct in enumerate(ncts):
        cands = esearch(nct)
        best = None
        for pmid in cands[:10]:
            yr = verify(pmid, nct)
            if yr is not None and (best is None or yr < best[1]):
                best = (pmid, yr)
        if best:
            recovered[nct] = {"pmid": best[0], "year": best[1], "source": "pubmed-databank-verified"}
            print(f"  [{i+1}/{len(ncts)}] {nct} -> {best[0]} ({best[1]})")
        else:
            print(f"  [{i+1}/{len(ncts)}] {nct} -> (no verified primary paper)")
    return recovered


def main():
    ncts = json.loads((REPO / "outputs/pmid_resolver/unresolved_ncts.json").read_text())
    rec = resolve(ncts)
    out = REPO / "outputs/pmid_resolver/nct_to_pmid_recovered.json"
    out.write_text(json.dumps(rec, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"\nRecovered {len(rec)}/{len(ncts)} verified PMIDs -> {out}")


if __name__ == "__main__":
    main()
