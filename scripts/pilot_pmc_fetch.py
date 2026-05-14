"""PMC full-text fetch pilot.

For each PMID:
  1. PMID -> PMCID via NCBI idconv
  2. Fetch PMC XML body via efetch (db=pmc)
  3. Strip to plain text
  4. Run V2 + loose-match extractor
  5. Report whether full text yields a HR/OR/RR/MD that the abstract didn't.
"""
from __future__ import annotations
import json, sys, io, time, urllib.request, urllib.parse, re
import xml.etree.ElementTree as ET
from pathlib import Path

if hasattr(sys.stdout, "buffer") and getattr(sys.stdout, "encoding", "").lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path("C:/Projects/rct-extractor-v2/src").resolve()))
from core.enhanced_extractor_v3 import EnhancedExtractor, to_dict  # noqa: E402
sys.path.insert(0, str(Path(__file__).parent))
from backfill_published_hr import loose_match, pick_best_extraction, PREFERRED_TYPES  # noqa: E402

HERE = Path(__file__).resolve().parent.parent
PMC_CACHE = HERE / "outputs" / "extraction_audit" / "pmc_cache"
PMC_CACHE.mkdir(parents=True, exist_ok=True)


def pmid_to_pmcid(pmid):
    url = (f"https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/?ids={pmid}"
           f"&format=json&tool=rapidmeta&email=mahmood726@gmail.com")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "rapidmeta/1.0"})
        with urllib.request.urlopen(req, timeout=20) as r:
            d = json.loads(r.read())
        recs = d.get("records") or []
        if not recs: return None
        return recs[0].get("pmcid")
    except Exception:
        return None


def fetch_pmc_text(pmcid):
    """Fetch PMC XML and extract plain text from the body."""
    cache = PMC_CACHE / f"{pmcid}.txt"
    if cache.exists():
        return cache.read_text(encoding="utf-8")
    pmcid_num = pmcid.replace("PMC", "")
    url = ("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?"
           + urllib.parse.urlencode({"db": "pmc", "id": pmcid_num,
                                        "rettype": "xml", "retmode": "xml"}))
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "rapidmeta/1.0"})
        with urllib.request.urlopen(req, timeout=60) as r:
            xml_data = r.read()
        root = ET.fromstring(xml_data)
        # Body text
        body = root.find(".//body")
        if body is None:
            # Try abstract + body alternate
            body = root.find(".//article")
        if body is None: return None
        # Strip all XML tags, keep whitespace
        text = "".join(body.itertext())
        text = re.sub(r"\s+", " ", text)
        cache.write_text(text, encoding="utf-8")
        return text
    except Exception as e:
        return None


def best_published_extraction(text, ext):
    """Run V2, fall back to loose; return best or None."""
    extractions = ext.extract(text)
    best = pick_best_extraction(extractions)
    if best:
        return best, "v2"
    loose = loose_match(text)
    if loose:
        by_t = {}
        for x in loose:
            if x["type"] not in by_t: by_t[x["type"]] = x
        for pt in PREFERRED_TYPES:
            if pt in by_t: return by_t[pt], "loose"
    return None, None


def main():
    pmid_list = Path("/tmp/_pilot_pmids.txt").read_text(encoding="utf-8").splitlines()
    pmid_list = [p.strip() for p in pmid_list if p.strip()]
    ext = EnhancedExtractor()
    print(f"Piloting {len(pmid_list)} PMIDs from M=1.0 reviews\n")

    abstract_hits = 0
    pmc_hits = 0
    pmc_new_hits = 0  # PMC found an effect that abstract didn't
    pmc_unavailable = 0

    for pmid in pmid_list:
        # Abstract
        abs_cache = HERE / "outputs" / "extraction_audit" / "pubmed_cache" / f"{pmid}.json"
        abst_text = ""
        if abs_cache.exists():
            d = json.loads(abs_cache.read_text(encoding="utf-8"))
            abst_text = (d.get("title", "") + "\n" + (d.get("abstract") or ""))
        abst_best, abst_src = (None, None)
        if abst_text:
            abst_best, abst_src = best_published_extraction(abst_text, ext)
        if abst_best: abstract_hits += 1

        # PMC
        pmcid = pmid_to_pmcid(pmid)
        time.sleep(0.4)
        if not pmcid:
            pmc_unavailable += 1
            print(f"PMID {pmid}: abstract={'YES' if abst_best else 'no'}  PMC=unavailable")
            continue
        pmc_text = fetch_pmc_text(pmcid)
        time.sleep(0.4)
        if not pmc_text:
            pmc_unavailable += 1
            print(f"PMID {pmid} ({pmcid}): abstract={'YES' if abst_best else 'no'}  PMC=fetch-failed")
            continue
        pmc_best, pmc_src = best_published_extraction(pmc_text, ext)
        if pmc_best:
            pmc_hits += 1
            if not abst_best: pmc_new_hits += 1
            print(f"PMID {pmid} ({pmcid}, {len(pmc_text):,}c): abstract={'YES' if abst_best else 'no'}  "
                  f"PMC={pmc_best['type']}={pmc_best['effect_size']} "
                  f"[{pmc_best['ci_lower']},{pmc_best['ci_upper']}] via {pmc_src}")
        else:
            print(f"PMID {pmid} ({pmcid}, {len(pmc_text):,}c): abstract={'YES' if abst_best else 'no'}  PMC=no-extraction")

    print()
    print(f"Summary on {len(pmid_list)} pilot PMIDs:")
    print(f"  Abstract-only hits:                {abstract_hits}/{len(pmid_list)}")
    print(f"  PMC hits (regardless of abstract): {pmc_hits}/{len(pmid_list)}")
    print(f"  PMC NEW hits (abstract was empty): {pmc_new_hits}/{len(pmid_list)}")
    print(f"  PMC unavailable / fetch failed:    {pmc_unavailable}/{len(pmid_list)}")


if __name__ == "__main__":
    main()
