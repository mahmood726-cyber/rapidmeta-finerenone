"""Path A — Fetch PMC OAI full-text for trials with empty evidence[].

Pipeline:
  Stage 1 — identify target trials: PMID present, evidence[] empty
  Stage 2 — elink: PMID → PMC ID (~25-30% of PMIDs are in PMC OA)
  Stage 3 — efetch full-text XML for PMC IDs found
  Stage 4 — parse XML, extract sentences containing trial values
  Stage 5 — inject evidence[] entries with PMC sourceUrl

This script handles stages 1-3; stage 4-5 are in `pmc_inject_evidence.py`.

NCBI rate limits: 3 req/sec without API key, 10/sec with. We batch elink at
50 PMIDs/call (~1 req/batch) and fetch full-text sequentially with 0.4s
sleep between (2.5 req/sec).

Cache:
  outputs/extraction_audit/pmc_cache/pmid_to_pmc.json — PMID → PMC ID (or null)
  outputs/extraction_audit/pmc_cache/<pmc_id>.xml      — full-text XML
"""
from __future__ import annotations
import json, sys, io, time, re
from pathlib import Path
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET

if hasattr(sys.stdout, "buffer") and getattr(sys.stdout, "encoding", "").lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent.parent
OUT = HERE / "outputs" / "extraction_audit"
DATA = OUT / "data"
PMC_CACHE = OUT / "pmc_cache"
PMC_CACHE.mkdir(parents=True, exist_ok=True)

ELINK = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/elink.fcgi"
EFETCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
PMID_TO_PMC_FILE = PMC_CACHE / "pmid_to_pmc.json"
HEADERS = {"User-Agent": "rapidmeta-finerenone-audit/1.0"}

# ───── Stage 1: identify target trials ─────
target = []
for json_p in sorted(DATA.glob("*.json")):
    if json_p.name.startswith("_"): continue
    rv = json_p.stem
    try: d = json.loads(json_p.read_text(encoding="utf-8"))
    except: continue
    rd = d.get("realData") or {}
    if not isinstance(rd, dict): continue
    for nct, t in rd.items():
        if not isinstance(t, dict): continue
        if nct.startswith("NULLED:"): continue
        if t.get("evidence"): continue  # has evidence
        pmid = (t.get("pmid") or "").strip()
        if not pmid.isdigit() or not (6 <= len(pmid) <= 9): continue
        target.append({"review": rv, "nct": nct, "pmid": pmid})

target_pmids = sorted({t["pmid"] for t in target})
print(f"Trials with PMID but no evidence: {len(target)}")
print(f"Unique PMIDs: {len(target_pmids)}")

# ───── Stage 2: elink PMID → PMC ID (batched) ─────
pmid_to_pmc = {}
if PMID_TO_PMC_FILE.exists():
    pmid_to_pmc = json.loads(PMID_TO_PMC_FILE.read_text(encoding="utf-8"))
    print(f"Loaded cached PMID→PMC for {len(pmid_to_pmc)} PMIDs")

to_query = [p for p in target_pmids if p not in pmid_to_pmc]
print(f"PMIDs needing elink: {len(to_query)}")

BATCH_SIZE = 50
SLEEP = 0.4
for i in range(0, len(to_query), BATCH_SIZE):
    batch = to_query[i:i+BATCH_SIZE]
    params = {
        "dbfrom": "pubmed", "db": "pmc",
        "id": ",".join(batch),
        "retmode": "xml",
        "cmd": "neighbor",
    }
    url = ELINK + "?" + urllib.parse.urlencode(params)
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=60) as r:
            xml_data = r.read()
    except Exception as e:
        print(f"  batch {i//BATCH_SIZE + 1}: error {e}")
        for p in batch: pmid_to_pmc[p] = None
        continue
    # Parse: LinkSet/IdList/Id is the PMID, LinkSetDb/Link/Id are PMC IDs
    try:
        root = ET.fromstring(xml_data)
        for linkset in root.findall(".//LinkSet"):
            pmid_el = linkset.find(".//IdList/Id")
            if pmid_el is None: continue
            pmid = pmid_el.text
            pmc_ids = []
            for ldb in linkset.findall(".//LinkSetDb"):
                dbname = (ldb.findtext("DbTo") or "").strip()
                if dbname != "pmc": continue
                for link in ldb.findall(".//Link/Id"):
                    if link.text: pmc_ids.append(link.text)
            pmid_to_pmc[pmid] = pmc_ids[0] if pmc_ids else None
        # PMIDs not in result also get null
        for p in batch:
            if p not in pmid_to_pmc: pmid_to_pmc[p] = None
    except Exception as e:
        print(f"  batch {i//BATCH_SIZE + 1}: parse error {e}")
        for p in batch:
            if p not in pmid_to_pmc: pmid_to_pmc[p] = None
    print(f"  batch {i//BATCH_SIZE + 1}: done ({sum(1 for p in batch if pmid_to_pmc.get(p))}/{len(batch)} mapped to PMC)")
    time.sleep(SLEEP)

PMID_TO_PMC_FILE.write_text(json.dumps(pmid_to_pmc, indent=2), encoding="utf-8")
mapped = {p: v for p, v in pmid_to_pmc.items() if v}
print(f"\nTotal PMIDs in PMC OA: {len(mapped)}/{len(target_pmids)} ({100*len(mapped)/max(len(target_pmids),1):.1f}%)")

# ───── Stage 3: fetch full-text XML for PMC IDs ─────
pmc_to_fetch = [pmc for pmc in set(mapped.values()) if pmc and not (PMC_CACHE / f"PMC{pmc}.xml").exists()]
print(f"PMC IDs needing full-text fetch: {len(pmc_to_fetch)}")

if "--limit" in sys.argv:
    idx = sys.argv.index("--limit")
    lim = int(sys.argv[idx+1])
    pmc_to_fetch = pmc_to_fetch[:lim]
    print(f"  Limiting to first {lim}")

n_ok = n_fail = 0
for i, pmc_id in enumerate(pmc_to_fetch):
    params = {"db": "pmc", "id": pmc_id, "rettype": "xml", "retmode": "xml"}
    url = EFETCH + "?" + urllib.parse.urlencode(params)
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=120) as r:
            data = r.read()
        # Sanity: must contain pmc-articleset or article element
        if b"<article" in data or b"<pmc-articleset" in data:
            (PMC_CACHE / f"PMC{pmc_id}.xml").write_bytes(data)
            n_ok += 1
        else:
            (PMC_CACHE / f"PMC{pmc_id}.error").write_bytes(data[:500])
            n_fail += 1
    except Exception as e:
        n_fail += 1
        if i % 50 == 0:
            print(f"  [{i}] PMC{pmc_id}: error {e}")
    if (i + 1) % 50 == 0:
        print(f"  [{i+1}/{len(pmc_to_fetch)}] ok={n_ok} fail={n_fail}")
    time.sleep(SLEEP)

print(f"\nFull-text fetch: ok={n_ok}  fail={n_fail}")
print(f"Cache: {PMC_CACHE}")
