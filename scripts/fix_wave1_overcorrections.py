"""Revert the 5 hallucinated PMID fixes from Wave 1 (Agent 7's confirmed-fix
list, which it turned out wasn't actually verified) and find the REAL PMIDs.

Wave 1 'confirmed' fixes audited fresh against PubMed esummary
(2026-05-06):

  HPTN 082    32298430 → 33513145 → 'snakebite in Brazil' WRONG  needs real
  EMBARK      39320319 → 38978283 → 'QDOT MICRO catheter' WRONG  needs real
  PURPOSE-1   39046957 → 39046268 → 'fluorinated spiro-oxazines' WRONG
  WOMAN-2     37499666 → 37516131 → 'antimicrobial resistance' WRONG
  KEN-SHE     35143335 → 35693867 → 'Phototherapy / muscle damage' WRONG

  BrigHTN     36302086 → 36342143 → 'Baxdrostat for TR-Hypertension' OK
  EXPEDITION-1 28728681 → 28818546 → 'Glecaprevir+pibrentasvir HCV' OK
  ACHIEVE I   31816158 → 31800988 → 'Ubrogepant for Migraine' OK

For the 5 wrong, query PubMed with strict drug+condition+phase-3 search
to find the actual primary trial paper. Apply only if title clearly
matches.
"""
from __future__ import annotations
import sys, io, re, time, json
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.parse import quote
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path("C:/Projects/Finrenone")
EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
RATE_S = 0.5

# (file, claimed_name, current_wrong_pmid, search_query, expected_keyword_in_title)
WRONG_WAVE1 = [
    # HPTN 082 — Celum 2021 PLOS Med daily oral PrEP in AGYW, sub-Saharan Africa
    ("AGYW_HIV_PREP_REVIEW.html", "HPTN 082", "33513145",
     "HPTN 082[ti] OR (\"oral PrEP\"[ti] AND \"young women\"[ti] AND Africa)",
     ["hptn", "prep"]),
    # EMBARK — Mendell 2024 Nat Med delandistrogene moxeparvovec DMD
    ("DELANDISTROGENE_DMD_REVIEW.html", "EMBARK", "38978283",
     "delandistrogene[ti] AND moxeparvovec[ti]",
     ["delandistrogene", "moxeparvovec"]),
    # PURPOSE-1 — Bekker 2024 NEJM Lenacapavir HIV PrEP in cisgender women
    ("HIV_LA_PREP_REVIEW.html", "PURPOSE-1", "39046268",
     "lenacapavir[ti] AND PrEP[ti]",
     ["lenacapavir", "prep"]),
    # WOMAN-2 — Brenner 2023 Lancet PPH tranexamic acid
    ("PPH_BUNDLE_REVIEW.html", "WOMAN-2", "37516131",
     "WOMAN-2[ti] OR (\"WOMAN 2\"[ti] AND tranexamic[ti])",
     ["woman", "tranexamic"]),
    # KEN-SHE — Barnabas 2022 NEJM Evid single-dose HPV
    ("HPV_DOSE_REDUCTION_REVIEW.html", "KEN-SHE", "35693867",
     "(\"KEN SHE\"[ti] OR \"single-dose\"[ti]) AND HPV[ti]",
     ["hpv", "single-dose"]),
]


def http_json(url, retries=3):
    for i in range(retries):
        try:
            req = Request(url, headers={"User-Agent": "Wave1-fix/1.0"})
            with urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:
            if "429" in str(e) and i < retries - 1:
                time.sleep((i + 2) * 3)
                continue
            return None


def search_with_strategies(claim_name, search_query, drug_keywords):
    """Try multiple search strategies, score each candidate, return best."""
    queries = [search_query]
    # Acronym-only fallback
    acros = re.findall(r"[A-Z][A-Z0-9\-]{2,}", claim_name)
    for a in acros[:2]:
        queries.append(f"{a}[ti] AND randomized[ti]")
    candidates = set()
    for q in queries:
        url = f"{EUTILS}/esearch.fcgi?db=pubmed&term={quote(q)}&retmax=10&retmode=json&sort=relevance"
        data = http_json(url)
        time.sleep(RATE_S)
        if not data:
            continue
        ids = data.get("esearchresult", {}).get("idlist", [])
        candidates.update(ids)
    if not candidates:
        return None, None
    # Fetch summaries
    cand_list = list(candidates)[:15]
    url = f"{EUTILS}/esummary.fcgi?db=pubmed&id={','.join(cand_list)}&retmode=json"
    data = http_json(url)
    time.sleep(RATE_S)
    if not data:
        return None, None
    scored = []
    for pid in cand_list:
        rec = data.get("result", {}).get(pid)
        if not rec or rec.get("error"):
            continue
        title = rec.get("title", "").lower()
        pubtype = rec.get("pubtype", [])
        # Skip non-primary
        if any(t in pubtype for t in ["Review", "Comment", "Letter",
                                        "Editorial", "Retraction of Publication"]):
            continue
        score = sum(2 if k in title else 0 for k in drug_keywords)
        if "Randomized Controlled Trial" in pubtype:
            score += 2
        if "Clinical Trial, Phase III" in pubtype:
            score += 1
        # Penalize unrelated topics
        for bad in ["snakebite", "muscle damage", "antimicrobial resistance",
                     "fluorinated", "catheter-related", "phototherapy"]:
            if bad in title:
                score -= 5
        if score >= 3:
            scored.append((score, pid, rec.get("title", "")))
    if not scored:
        return None, None
    scored.sort(reverse=True)
    return scored[0][1], scored[0][2]


def main():
    print("Reverting and fixing 5 hallucinated Wave-1 PMIDs ...\n")
    fixed = 0
    for fname, claim, wrong_pmid, query, kws in WRONG_WAVE1:
        path = REPO / fname
        if not path.exists():
            print(f"  MISSING {fname}")
            continue
        text = path.read_text(encoding="utf-8", errors="replace")

        # First, revert the wrong Wave-1 fix back to nothing useful — but
        # we have no record of the *previous* PMID anymore. So we just need
        # to find the right one and replace.
        new_pid, new_title = search_with_strategies(claim, query, kws)
        if not new_pid:
            print(f"  NO_MATCH  {claim:20s} (current wrong: {wrong_pmid})")
            continue
        old_str = f"pmid: '{wrong_pmid}'"
        new_str = f"pmid: '{new_pid}'"
        if old_str not in text:
            print(f"  STALE     {claim:20s} pmid {wrong_pmid} not in source")
            continue
        text = text.replace(old_str, new_str, 1)
        path.write_text(text, encoding="utf-8")
        fixed += 1
        print(f"  FIXED     {claim:20s} {wrong_pmid} → {new_pid}")
        print(f"    {new_title[:90]}")

    print(f"\n  Fixed: {fixed}/{len(WRONG_WAVE1)}")


if __name__ == "__main__":
    main()
