"""Task D rerun with pub-type-aware filter.

Fix from v1: instead of filtering by title keywords (which accidentally
excluded the trial-named "PERSPECTIVE" because "perspective" was a
keyword), use the PubMed `publication_types` field. This correctly tags
Review / Editorial / Comment / Letter / Case Reports / etc. as
non-primary, while leaving "Perspective"-acronym trial papers alone.

Also: don't fall back to first-result when all candidates are filtered.
If the filter rejects everything, return None (means primary publication
is not yet PubMed-indexed under that NCT, e.g. still in press).
"""
from __future__ import annotations
import json
import sys
import time
import io
import urllib.request
import urllib.parse
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

OUT_DIR = Path(__file__).parent
RAW = OUT_DIR / "hf_outcomes_raw.json"
PUB_OUT = OUT_DIR / "hf_publications_22_v2.json"

ESEARCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
ESUMMARY = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
EFETCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

FLAGSHIP_JOURNALS = [
    "N Engl J Med", "Lancet", "JAMA", "Circulation", "J Am Coll Cardiol",
    "Eur Heart J", "JAMA Cardiol", "Nat Med", "JAMA Intern Med", "BMJ",
    "Eur J Heart Fail", "JACC Heart Fail", "NEJM Evid",
]

# PubMed publication types that disqualify a paper as the primary results paper.
# https://www.nlm.nih.gov/mesh/pubtypes.html
NON_PRIMARY_PUB_TYPES = {
    "Review", "Editorial", "Comment", "Letter", "Case Reports",
    "Practice Guideline", "Guideline", "Meta-Analysis", "Systematic Review",
    "Historical Article", "News", "Biography", "Lecture", "Address",
    "Personal Narrative", "Published Erratum", "Comparative Study",
    # Note: do NOT exclude "Comparative Study" actually — it's often applied to RCTs.
}
# Correct: don't exclude Comparative Study. Trim:
NON_PRIMARY_PUB_TYPES = {
    "Review", "Editorial", "Comment", "Letter", "Case Reports",
    "Practice Guideline", "Guideline", "Meta-Analysis", "Systematic Review",
    "Historical Article", "News", "Biography", "Lecture", "Address",
    "Personal Narrative", "Published Erratum",
}

# Title-keyword fallback for cases like "Rationale and design" that publish in
# the same journal as the eventual primary results. Title-keyword filter only;
# does NOT use trial-acronym words.
NON_PRIMARY_TITLE_KW = [
    "rationale and design", "study design",
    "post hoc", "post-hoc",
    "secondary analysis", "subgroup",
    "rationale", "protocol", "exploratory",
]

EXCLUDE = {"NCT03473223", "NCT02809131", "NCT04415658"}  # non-HF


def esearch_pmids(nct: str, max_results: int = 20) -> list[str]:
    params = {"db": "pubmed", "term": f"{nct}[All Fields]", "retmax": str(max_results),
              "retmode": "json", "sort": "relevance"}
    url = ESEARCH + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "outcome-switching-MA/1.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r).get("esearchresult", {}).get("idlist", [])


def esummary(pmids: list[str]) -> list[dict]:
    if not pmids:
        return []
    params = {"db": "pubmed", "id": ",".join(pmids), "retmode": "json"}
    url = ESUMMARY + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "outcome-switching-MA/1.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        data = json.load(r)
    out = []
    for pmid in pmids:
        rec = data.get("result", {}).get(pmid, {})
        out.append({
            "pmid": pmid,
            "title": rec.get("title", ""),
            "journal": rec.get("source", ""),
            "pubdate": rec.get("pubdate", ""),
            "publication_types": rec.get("pubtype", []),
        })
    return out


def efetch_abstract(pmid: str) -> str:
    params = {"db": "pubmed", "id": pmid, "rettype": "abstract", "retmode": "text"}
    url = EFETCH + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "outcome-switching-MA/1.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read().decode("utf-8", errors="replace")


def is_primary(meta: dict) -> bool:
    """Eligibility test using publication_types + targeted title keywords."""
    pubtypes = set(meta.get("publication_types") or [])
    if pubtypes & NON_PRIMARY_PUB_TYPES:
        return False
    title_lower = (meta.get("title") or "").lower()
    if any(kw in title_lower for kw in NON_PRIMARY_TITLE_KW):
        return False
    return True


def pick_primary_publication(meta: list[dict]) -> dict | None:
    """Score by flagship-journal rank, exclude non-primary types. NO fallback to
    first result if all filtered — returns None instead."""
    candidates = []
    for m in meta:
        if not is_primary(m):
            continue
        try:
            rank = FLAGSHIP_JOURNALS.index(m.get("journal", ""))
        except ValueError:
            rank = 99
        candidates.append((rank, m))
    if not candidates:
        return None  # primary publication not yet PubMed-indexed
    candidates.sort(key=lambda x: x[0])
    return candidates[0][1]


def main() -> int:
    cur = json.load(open(RAW, "r", encoding="utf-8"))
    primary_pool = [t for t in cur["trials"] if t.get("nct_id") not in EXCLUDE]

    rows = []
    for i, t in enumerate(primary_pool, 1):
        nct = t["nct_id"]
        try:
            pmids = esearch_pmids(nct, max_results=20)
            time.sleep(0.4)
            meta = esummary(pmids)
            time.sleep(0.4)
            primary = pick_primary_publication(meta)
            if primary:
                pmid = primary["pmid"]
                abstract = efetch_abstract(pmid)
                time.sleep(0.4)
            else:
                pmid, abstract = None, None
            row = {
                "nct_id": nct,
                "acronym": t.get("acronym"),
                "current_registered_primary": [
                    {"measure": p["measure"], "timeFrame": p["timeFrame"]}
                    for p in (t.get("registered_primary") or [])
                ],
                "n_pmids_found": len(pmids),
                "candidate_pmids": pmids,
                "primary_pmid": pmid,
                "primary_journal": primary["journal"] if primary else None,
                "primary_title": primary["title"] if primary else None,
                "primary_pubdate": primary["pubdate"] if primary else None,
                "primary_pubtypes": primary.get("publication_types") if primary else None,
                "primary_abstract": abstract,
            }
            print(f"[{i:2d}/{len(primary_pool)}] {nct} ({t.get('acronym') or '?'}): pmid={pmid} | {primary['journal'] if primary else 'NONE_FOUND'}", flush=True)
        except Exception as e:
            row = {"nct_id": nct, "error": str(e)}
            print(f"[{i:2d}/{len(primary_pool)}] {nct} FAIL {e}", flush=True)
        rows.append(row)

    json.dump({"extracted_at": "2026-04-30", "n": len(rows), "trials": rows},
              open(PUB_OUT, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print()
    n_found = sum(1 for r in rows if r.get("primary_pmid"))
    print(f"Wrote {PUB_OUT} ({n_found}/{len(rows)} primary publications found)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
