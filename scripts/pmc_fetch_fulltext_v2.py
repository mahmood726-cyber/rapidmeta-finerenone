"""Path A v2 — use NCBI idconv API for reliable PMID↔PMC ID conversion.

idconv endpoint: https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/
Accepts up to 200 IDs per call, returns JSON.
"""
from __future__ import annotations
import json, sys, io, time, re
from pathlib import Path
import urllib.request
import urllib.parse

if hasattr(sys.stdout, "buffer") and getattr(sys.stdout, "encoding", "").lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent.parent
OUT = HERE / "outputs" / "extraction_audit"
DATA = OUT / "data"
PMC_CACHE = OUT / "pmc_cache"
PMC_CACHE.mkdir(parents=True, exist_ok=True)

IDCONV = "https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/"
EFETCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
PMID_TO_PMC_FILE = PMC_CACHE / "pmid_to_pmc.json"
HEADERS = {"User-Agent": "rapidmeta-finerenone-audit/1.0"}

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
        if t.get("evidence"): continue
        pmid = (t.get("pmid") or "").strip()
        if not pmid.isdigit() or not (6 <= len(pmid) <= 9): continue
        target.append({"review": rv, "nct": nct, "pmid": pmid})
target_pmids = sorted({t["pmid"] for t in target})
print(f"PMIDs needing PMC lookup: {len(target_pmids)}")

# Reset cache (previous run had unreliable elink results)
pmid_to_pmc = {}

# idconv batch (up to 200 at once)
BATCH = 200
for i in range(0, len(target_pmids), BATCH):
    batch = target_pmids[i:i+BATCH]
    params = {
        "ids": ",".join(batch),
        "format": "json",
        "tool": "rapidmeta-finerenone-audit",
        "email": "test@example.com",
    }
    url = IDCONV + "?" + urllib.parse.urlencode(params)
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=60) as r:
            payload = json.loads(r.read())
    except Exception as e:
        print(f"  batch {i//BATCH+1}: error {e}")
        for p in batch: pmid_to_pmc[p] = None
        continue
    records = payload.get("records", [])
    n_with_pmc = 0
    for rec in records:
        pmid = rec.get("pmid")
        pmcid = rec.get("pmcid")  # e.g., "PMC12345"
        if pmid is None: continue
        pmid_str = str(pmid)  # API returns int; normalize to str to match target_pmids
        if pmcid:
            pmid_to_pmc[pmid_str] = pmcid.replace("PMC", "")
            n_with_pmc += 1
        else:
            pmid_to_pmc[pmid_str] = None
    for p in batch:
        if p not in pmid_to_pmc:
            pmid_to_pmc[p] = None
    print(f"  batch {i//BATCH+1}: {n_with_pmc}/{len(batch)} mapped to PMC OA")
    time.sleep(0.4)

PMID_TO_PMC_FILE.write_text(json.dumps(pmid_to_pmc, indent=2), encoding="utf-8")
mapped = {p: v for p, v in pmid_to_pmc.items() if v}
print(f"\nPMIDs in PMC: {len(mapped)}/{len(target_pmids)} ({100*len(mapped)/max(len(target_pmids),1):.1f}%)")

# Fetch full-text for mapped PMC IDs
pmc_to_fetch = [pmc for pmc in set(mapped.values()) if not (PMC_CACHE / f"PMC{pmc}.xml").exists()]
print(f"PMC full-texts to fetch: {len(pmc_to_fetch)}")

n_ok = n_fail = 0
for i, pmc_id in enumerate(pmc_to_fetch):
    params = {"db": "pmc", "id": pmc_id, "rettype": "xml", "retmode": "xml"}
    url = EFETCH + "?" + urllib.parse.urlencode(params)
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=120) as r:
            data = r.read()
        if (b"<article" in data or b"<pmc-articleset" in data) and len(data) > 1000:
            (PMC_CACHE / f"PMC{pmc_id}.xml").write_bytes(data)
            n_ok += 1
        else:
            (PMC_CACHE / f"PMC{pmc_id}.error").write_bytes(data[:1000])
            n_fail += 1
    except Exception as e:
        n_fail += 1
    if (i + 1) % 20 == 0:
        print(f"  [{i+1}/{len(pmc_to_fetch)}] ok={n_ok} fail={n_fail}")
    time.sleep(0.4)

print(f"\nFull-text fetch: ok={n_ok}  fail={n_fail}")
print(f"Cache: {PMC_CACHE}")
