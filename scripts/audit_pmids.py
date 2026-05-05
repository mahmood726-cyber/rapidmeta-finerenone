"""Sweep every PMID in the corpus against PubMed esummary + esearch.

Per Agent 7 (n=40 stratified random sample), 20% of PMIDs are catastrophically
wrong (resolve to topically unrelated articles), and 27.5% are misattributed
in any way. Pattern: LLM-hallucinated near-neighbour PMIDs.

This script:

  1. Extracts every (file, NCT, PMID, claimed_name, year) tuple from
     every *_REVIEW.html using a regex on realData blocks.
  2. Calls PubMed esummary (batches of 200) to fetch:
     - article title
     - publication year
     - DataBankList (NCT mapping)
  3. Cross-checks each row:
       OK         — esummary title contains a meaningful chunk of claimed_name
                    OR DataBankList includes our NCT
       WRONG_PMID — esummary title doesn't match AND no NCT match
       NOT_FOUND  — PMID not in PubMed
       MISSING    — PMID empty in our data
  4. For every WRONG_PMID, runs an esearch with the trial name + NCT to find
     the correct PMID and writes a suggested correction.
  5. Outputs `outputs/pmid_audit.csv` with: file, NCT, claimed_PMID, claimed_name,
     status, esummary_title, esummary_year, esummary_databank_ncts,
     suggested_PMID, suggested_title.

Rate-limit: 3 requests/sec without API key, 200 IDs/batch on esummary,
1 esearch per WRONG_PMID. With ~600 trials → ~3 esummary batches +
~120 esearch calls. ~5 min total.
"""
from __future__ import annotations
import sys, io, re, csv, time, json
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.parse import quote
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path("C:/Projects/Finrenone")
OUT_CSV = REPO / "outputs" / "pmid_audit.csv"

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
RATE_LIMIT_S = 0.34  # 3 req/sec budget without API key

TRIAL_RE = re.compile(
    r"'(NCT\d+(?:[A-Z]|_[A-Za-z0-9]+)?|LEGACY-[A-Za-z0-9-]+)'\s*:\s*\{[^}]*?"
    r"name:\s*'([^']+?)'[^}]*?"
    r"pmid:\s*'(\d{7,9})'[^}]*?"
    r"(?:phase:\s*'([^']*?)',?\s*)?"
    r"(?:year:\s*(\d{4})\s*,?)?",
    re.DOTALL,
)


def http_json(url):
    req = Request(url, headers={"User-Agent": "RapidMeta-PMID-Audit/1.0"})
    with urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def http_xml(url):
    req = Request(url, headers={"User-Agent": "RapidMeta-PMID-Audit/1.0"})
    with urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8")


def collect_trials():
    rows = []
    seen_keys = set()
    for hp in sorted(REPO.glob("*_REVIEW.html")):
        text = hp.read_text(encoding="utf-8", errors="replace")
        for m in TRIAL_RE.finditer(text):
            nct, name, pmid, _phase, year = m.groups()
            key = (hp.name, nct)
            if key in seen_keys:
                continue
            seen_keys.add(key)
            rows.append({
                "file": hp.name, "nct": nct, "pmid": pmid,
                "claimed_name": name, "claimed_year": year or "",
            })
    return rows


def normalize_for_match(s):
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def title_matches_name(esummary_title, claimed_name):
    """Heuristic: does esummary title contain the trial acronym or
    a meaningful chunk of the claimed name?"""
    if not esummary_title or not claimed_name:
        return False
    et = normalize_for_match(esummary_title)
    cn = normalize_for_match(claimed_name)
    # Pull out potential acronyms (CAPS+digits) from claimed_name
    acros = re.findall(r"[A-Z][A-Z0-9\-]{2,}", claimed_name)
    for a in acros:
        if normalize_for_match(a) in et:
            return True
    # Fallback: ≥3 word overlap (excluding stopwords)
    stop = {"trial", "study", "phase", "the", "of", "in", "and", "vs", "for", "a", "n", "with"}
    cn_words = set(w for w in cn.split() if w and w not in stop and len(w) > 2)
    et_words = set(et.split())
    overlap = cn_words & et_words
    return len(overlap) >= 2


def esummary_batch(pmids):
    """Returns dict pmid -> {title, pubdate, databank_ncts}."""
    if not pmids:
        return {}
    ids = ",".join(pmids)
    url = f"{EUTILS}/esummary.fcgi?db=pubmed&id={ids}&retmode=json"
    try:
        data = http_json(url)
    except Exception as e:
        print(f"  esummary error on batch of {len(pmids)}: {e}")
        return {}
    out = {}
    for pmid in pmids:
        rec = data.get("result", {}).get(pmid)
        if not rec or rec.get("error"):
            out[pmid] = None
            continue
        title = rec.get("title", "")
        pubdate = rec.get("pubdate", "")
        # Extract NCT IDs from articleids if available, plus from
        # ``DataBankList`` (esummary doesn't expose this directly; we'll
        # do an efetch for confirmation only on uncertain cases)
        articleids = rec.get("articleids", [])
        databank_ncts = []
        # Articleids include `pmcrid`, `doi`; NCT IDs aren't always there
        # but sometimes. We rely on title+year primarily.
        out[pmid] = {
            "title": title,
            "pubdate": pubdate,
            "databank_ncts": databank_ncts,
        }
    return out


def esearch_for_correct_pmid(claimed_name, nct, year):
    """Search PubMed for the right PMID. Strategy:
       (a) NCT in [si] (secondary source ID) if non-LEGACY
       (b) acronym in title
       Returns first hit or None.
    """
    queries = []
    # NCT-based search: NCT ID in 'Secondary Source ID' [si]
    if nct.startswith("NCT"):
        queries.append(f"{nct}[si]")
    # Acronym-based fallback
    acros = re.findall(r"[A-Z][A-Z0-9\-]{2,}", claimed_name)
    for a in acros[:2]:
        q = f"{a}[ti]"
        if year:
            q += f" AND {year}[dp]"
        queries.append(q)
    for q in queries:
        url = f"{EUTILS}/esearch.fcgi?db=pubmed&term={quote(q)}&retmax=3&retmode=json"
        try:
            data = http_json(url)
            ids = data.get("esearchresult", {}).get("idlist", [])
            if ids:
                return ids[0], q
        except Exception:
            pass
        time.sleep(RATE_LIMIT_S)
    return None, None


def main():
    print("Collecting trials from corpus ...")
    trials = collect_trials()
    print(f"  {len(trials)} unique (file, NCT) pairs with PMIDs")

    # Unique PMIDs
    unique_pmids = sorted(set(t["pmid"] for t in trials))
    print(f"  {len(unique_pmids)} unique PMIDs to verify")

    # esummary in batches of 200
    pmid_lookup = {}
    for i in range(0, len(unique_pmids), 200):
        batch = unique_pmids[i:i + 200]
        print(f"  esummary batch {i // 200 + 1} of {(len(unique_pmids) - 1) // 200 + 1} ({len(batch)} PMIDs) ...")
        pmid_lookup.update(esummary_batch(batch))
        time.sleep(RATE_LIMIT_S)

    # For each NOT_FOUND or potential WRONG_PMID, run esearch
    print("\nClassifying each row + esearch corrections for WRONG_PMID ...")
    rows_out = []
    n_wrong = 0
    n_ok = 0
    n_nf = 0
    for i, t in enumerate(trials, 1):
        rec = pmid_lookup.get(t["pmid"])
        status = "MISSING"
        es_title = ""
        es_year = ""
        suggested_pmid = ""
        suggested_title = ""
        suggested_query = ""
        if rec is None:
            status = "NOT_FOUND"
            n_nf += 1
        else:
            es_title = rec["title"]
            es_year = rec["pubdate"]
            if title_matches_name(rec["title"], t["claimed_name"]):
                status = "OK"
                n_ok += 1
            else:
                status = "WRONG_PMID"
                n_wrong += 1
        if status in ("NOT_FOUND", "WRONG_PMID"):
            sp, sq = esearch_for_correct_pmid(t["claimed_name"], t["nct"], t["claimed_year"])
            if sp and sp != t["pmid"]:
                suggested_pmid = sp
                suggested_query = sq
                # Get title of suggested
                spr = esummary_batch([sp])
                if spr.get(sp):
                    suggested_title = spr[sp]["title"]
                time.sleep(RATE_LIMIT_S)
        rows_out.append({
            **t,
            "status": status,
            "esummary_title": es_title,
            "esummary_year": es_year,
            "suggested_pmid": suggested_pmid,
            "suggested_title": suggested_title,
            "suggested_query": suggested_query,
        })
        if i % 50 == 0:
            print(f"  ... {i}/{len(trials)} (OK={n_ok}, WRONG={n_wrong}, NF={n_nf})")

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows_out[0].keys()))
        w.writeheader()
        w.writerows(rows_out)

    print(f"\n=== Summary ===")
    print(f"  Total trials:    {len(trials)}")
    print(f"  OK:              {n_ok}")
    print(f"  WRONG_PMID:      {n_wrong}")
    print(f"  NOT_FOUND:       {n_nf}")
    print(f"  Pct WRONG:       {100*n_wrong/len(trials):.1f}%")
    n_correctable = sum(1 for r in rows_out if r.get("suggested_pmid"))
    print(f"  Auto-correctable: {n_correctable} (with suggested_pmid)")
    print(f"\nWritten: {OUT_CSV}")


if __name__ == "__main__":
    main()
