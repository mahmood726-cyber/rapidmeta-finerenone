"""AACT cross-check v2 — improved over v1.

Fixes for v1 false positives:
  - Title: now checks brief_title + official_title + brief_summary union (acronyms
    appear in summary text, not the formal title).
  - Country: uses facilities.txt (site-level) rather than countries.txt summary.
  - Honors existing audit exception lists (CLUSTER_RCT_BY_DESIGN, MULTI_TRIAL_PROGRAM,
    SINGLE_ARM_HISTORICAL_CONTROL) — these have known intentional row/AACT mismatches.

Output: outputs/aact_cross_check_v2.csv + summary.

Verdicts (priority order):
  1. AACT_NOT_FOUND       — NCT doesn't exist in AACT (definitely wrong NCT)
  2. N_OUTLIER            — row total wildly off, not on exception list
  3. COUNTRY_NOT_IN_AACT  — snippet claims a country AACT facilities.txt doesn't list
                            AND AACT has facility data (>=1 row) for the trial
  4. TITLE_LOW_OVERLAP    — title+summary share 0 tokens with my claim_name
  5. OK
  X. ISRCTN_ONLY          — non-CT.gov key, skipped
"""
from __future__ import annotations
import csv
import re
from pathlib import Path

AACT_DIR = Path("D:/AACT-storage/AACT/2026-04-12")
REPO_DIR = Path("C:/Projects/Finrenone")
OUT_CSV = REPO_DIR / "outputs" / "aact_cross_check_v2.csv"

# Schema
COL_NCT = 0
COL_BRIEF_TITLE = 33
COL_OFFICIAL_TITLE = 34
COL_PHASE = 37
COL_ENROLLMENT = 38

# Exception lists from ctgov_cross_check.py — mirror to keep in sync
CLUSTER_RCT_BY_DESIGN = {
    ("AZITHROMYCIN_CHILD_MORTALITY_REVIEW.html", "NCT04224987"),
    ("AZITHROMYCIN_CHILD_MORTALITY_REVIEW.html", "NCT02048007"),
}
SINGLE_ARM_HISTORICAL_CONTROL = {
    ("MDR_TB_SHORTENED_NMA_REVIEW.html", "NCT02333799"),
    ("HEMOPHILIA_GENE_THERAPY_NMA_REVIEW.html", "NCT03370913"),
    ("HEMOPHILIA_GENE_THERAPY_NMA_REVIEW.html", "NCT03569891"),
    ("HEMOPHILIA_GENE_THERAPY_NMA_REVIEW.html", "NCT04370054"),
}
MULTI_TRIAL_PROGRAM = {
    ("SGLT2_MACE_CVOT_REVIEW.html", "NCT01032629"),
    ("BIOLOGIC_ASTHMA_REVIEW.html", "NCT01914757"),
    ("CFTR_CF_REVIEW.html", "NCT03525548"),
    ("HIFPH_CKD_ANEMIA_REVIEW.html", "NCT02648347"),
    ("SEVERE_ASTHMA_NMA_REVIEW.html", "NCT01287039"),
    ("SPONDYLOARTHRITIS_NMA_REVIEW.html", "NCT03928704"),
    ("SPONDYLOARTHRITIS_NMA_REVIEW.html", "NCT03928743"),
    ("UC_BIOLOGICS_NMA_REVIEW.html", "NCT00488774"),
}
EXEMPT = CLUSTER_RCT_BY_DESIGN | SINGLE_ARM_HISTORICAL_CONTROL | MULTI_TRIAL_PROGRAM

STOPWORDS = {
    "a", "an", "the", "of", "in", "for", "to", "and", "or", "with", "vs", "versus",
    "study", "trial", "phase", "randomized", "randomised", "double", "blind",
    "open", "label", "controlled", "placebo", "comparison", "evaluation",
    "efficacy", "safety", "treatment", "patients", "patient", "subjects",
    "evaluate", "compare", "assess", "single", "multicentre", "multicenter",
    "multi", "centre", "center", "international", "global", "vs.", "trial.",
    "i", "ii", "iii", "iv",
}


def normalize_tokens(s: str) -> set[str]:
    if not s:
        return set()
    raw = re.split(r"[^a-z0-9]+", s.lower())
    return {t for t in raw if len(t) >= 3 and t not in STOPWORDS}


def load_aact_studies() -> dict[str, dict]:
    db = {}
    studies_path = AACT_DIR / "studies.txt"
    with studies_path.open(encoding="utf-8", errors="replace") as f:
        next(f)
        for line in f:
            cols = line.rstrip("\n").split("|")
            if len(cols) <= COL_ENROLLMENT:
                continue
            nct = cols[COL_NCT].strip()
            if not nct.startswith("NCT"):
                continue
            try:
                enroll = int(cols[COL_ENROLLMENT]) if cols[COL_ENROLLMENT].strip() else None
            except ValueError:
                enroll = None
            db[nct] = {
                "brief_title": cols[COL_BRIEF_TITLE],
                "official_title": cols[COL_OFFICIAL_TITLE],
                "phase": cols[COL_PHASE],
                "enrollment": enroll,
            }
    return db


def load_aact_brief_summaries() -> dict[str, str]:
    db: dict[str, str] = {}
    path = AACT_DIR / "brief_summaries.txt"
    with path.open(encoding="utf-8", errors="replace") as f:
        next(f)
        for line in f:
            cols = line.rstrip("\n").split("|", 3)
            if len(cols) < 3:
                continue
            nct = cols[1].strip()
            description = cols[2] if len(cols) > 2 else ""
            if nct.startswith("NCT"):
                db[nct] = description
    return db


def load_aact_facility_countries() -> dict[str, set[str]]:
    """Per-NCT set of countries from facilities.txt column 8."""
    db: dict[str, set[str]] = {}
    path = AACT_DIR / "facilities.txt"
    with path.open(encoding="utf-8", errors="replace") as f:
        next(f)
        for line in f:
            cols = line.rstrip("\n").split("|")
            if len(cols) < 8:
                continue
            nct = cols[1].strip()
            country = cols[7].strip()
            if not nct.startswith("NCT") or not country:
                continue
            db.setdefault(nct, set()).add(country)
    return db


# Same regex as v1
NCT_BLOCK_RE = re.compile(
    r"'(NCT\d+(?:_[A-Za-z0-9]+)?|LEGACY-[A-Za-z0-9-]+)'\s*:\s*\{[^}]*?"
    r"name:\s*'([^']+?)'[^}]*?"
    r"tN:\s*(\d+)\s*,\s*cE:\s*\d+\s*,\s*cN:\s*(\d+)",
    re.DOTALL,
)


def extract_trials_from_html(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8", errors="replace")
    out = []
    for m in NCT_BLOCK_RE.finditer(text):
        key = m.group(1)
        name = m.group(2)
        tN = int(m.group(3))
        cN = int(m.group(4))
        block_start = m.start()
        block_end = text.find("},", m.end())
        if block_end == -1:
            block_end = m.end() + 4000
        block = text[block_start:min(block_end, block_start + 4000)]
        gm = re.search(r"group:\s*'([^']+)'", block, re.DOTALL)
        group_text = gm.group(1) if gm else ""
        out.append({
            "key": key,
            "name": name,
            "tN": tN,
            "cN": cN,
            "row_total": tN + cN,
            "group": group_text,
        })
    return out


COUNTRIES_OF_INTEREST = [
    "South Africa", "Uganda", "Kenya", "Tanzania", "Malawi", "Zambia", "Zimbabwe",
    "Botswana", "Nigeria", "Ghana", "Mali", "Burkina Faso", "Niger", "Cameroon",
    "Mozambique", "DRC", "Senegal", "Ethiopia", "Rwanda", "Cote d'Ivoire", "Côte d'Ivoire",
    "Gabon", "Egypt", "Sudan", "USA", "United States", "Brazil", "Argentina",
    "Canada", "UK", "United Kingdom", "France", "Germany", "Spain", "Italy",
    "India", "Thailand", "Vietnam", "China", "Japan", "Australia", "Cambodia",
    "Pakistan", "Bangladesh", "Belarus", "Uzbekistan", "Russia", "Mexico",
    "Peru", "Chile", "Romania", "Bulgaria", "Sweden", "Greece", "Israel",
    "Singapore", "Indonesia", "Hong Kong", "Belgium", "Netherlands", "Denmark",
    "Norway", "Switzerland", "Austria", "Portugal", "Ireland", "Finland",
    "Korea", "Czechia", "Poland", "Slovakia", "Hungary", "Lithuania", "Estonia",
    "Croatia", "Slovenia", "Latvia", "Madagascar", "Iran", "Saudi Arabia",
    "Turkey", "Lebanon", "Jordan", "UAE", "Iraq", "Morocco", "Tunisia",
    "Algeria", "Liberia", "Sierra Leone", "Angola", "Namibia",
    "Lesotho", "Eswatini", "Burundi", "Chad", "Republic of the Congo",
    "Georgia", "Kazakhstan", "Moldova",
]

COUNTRY_SYNONYMS = {
    "USA": {"United States"},
    "United States": {"United States"},
    "UK": {"United Kingdom"},
    "United Kingdom": {"United Kingdom"},
    "DRC": {"Democratic Republic of the Congo", "Congo, The Democratic Republic of the"},
    "Hong Kong": {"China", "Hong Kong"},
    "Cote d'Ivoire": {"Côte d'Ivoire"},
    "Côte d'Ivoire": {"Côte d'Ivoire"},
    "Republic of the Congo": {"Republic of the Congo", "Congo"},
}


def scan_countries_in_snippet(snippet: str) -> set[str]:
    found = set()
    for c in COUNTRIES_OF_INTEREST:
        if re.search(r"\b" + re.escape(c) + r"\b", snippet, re.IGNORECASE):
            found.add(c)
    return found


def country_in_aact(claim: str, aact_set: set[str]) -> bool:
    """True if my snippet country claim is satisfied by AACT facilities set."""
    if claim in aact_set:
        return True
    syns = COUNTRY_SYNONYMS.get(claim, set())
    return bool(syns & aact_set)


def main():
    print("Loading AACT studies.txt ...")
    studies = load_aact_studies()
    print(f"  {len(studies):,} NCTs")
    print("Loading AACT brief_summaries.txt ...")
    summaries = load_aact_brief_summaries()
    print(f"  {len(summaries):,} brief_summaries")
    print("Loading AACT facilities.txt ...")
    facilities = load_aact_facility_countries()
    print(f"  facility countries for {len(facilities):,} NCTs")

    review_files = sorted(REPO_DIR.glob("*_REVIEW.html"))
    print(f"\nScanning {len(review_files)} *_REVIEW.html files ...\n")

    findings = []
    for hp in review_files:
        for t in extract_trials_from_html(hp):
            key = t["key"]
            base_match = re.match(r"(NCT\d+)", key)
            if not base_match:
                findings.append({
                    "file": hp.name, "key": key, "claim_name": t["name"], "claim_n": t["row_total"],
                    "verdict": "ISRCTN_ONLY", "aact_brief_title": "", "aact_enrollment": "",
                    "n_ratio": "", "title_overlap": "", "country_issues": "", "exempt": "", "notes": "",
                })
                continue
            base_nct = base_match.group(1)
            row = studies.get(base_nct)
            exempt_flag = "EXEMPT" if (hp.name, base_nct) in EXEMPT else ""

            if not row:
                findings.append({
                    "file": hp.name, "key": key, "claim_name": t["name"], "claim_n": t["row_total"],
                    "verdict": "AACT_NOT_FOUND", "aact_brief_title": "", "aact_enrollment": "",
                    "n_ratio": "", "title_overlap": "", "country_issues": "", "exempt": exempt_flag,
                    "notes": "NCT absent from AACT — likely wrong NCT",
                })
                continue

            # Title-token comparison: union of brief_title + official_title + summary
            claim_tokens = normalize_tokens(t["name"])
            aact_text = " ".join([
                row["brief_title"], row["official_title"], summaries.get(base_nct, "")
            ])
            aact_tokens = normalize_tokens(aact_text)
            overlap = len(claim_tokens & aact_tokens)
            title_ok = (overlap >= 1) if claim_tokens else True

            # N comparison
            aact_n = row["enrollment"]
            ratio = (t["row_total"] / aact_n) if (aact_n and aact_n > 0) else None
            if ratio is None or exempt_flag:
                n_ok = True
            elif 0.20 <= ratio <= 1.30:
                n_ok = True
            else:
                n_ok = False

            # Country comparison
            aact_countries = facilities.get(base_nct, set())
            snippet_countries = scan_countries_in_snippet(t["group"])
            country_issues = []
            if aact_countries:  # only check if AACT has facility data
                for c in snippet_countries:
                    if not country_in_aact(c, aact_countries):
                        country_issues.append(c)

            # Determine verdict
            verdicts = []
            if not n_ok:
                verdicts.append("N_OUTLIER")
            if country_issues:
                verdicts.append("COUNTRY_NOT_IN_AACT")
            if not title_ok:
                verdicts.append("TITLE_LOW_OVERLAP")
            verdict = "+".join(verdicts) if verdicts else "OK"

            findings.append({
                "file": hp.name,
                "key": key,
                "claim_name": t["name"],
                "claim_n": t["row_total"],
                "verdict": verdict,
                "aact_brief_title": row["brief_title"][:80],
                "aact_enrollment": aact_n if aact_n else "",
                "n_ratio": f"{ratio:.2f}" if ratio is not None else "",
                "title_overlap": overlap,
                "country_issues": ",".join(country_issues),
                "exempt": exempt_flag,
                "notes": "",
            })

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(findings[0].keys()))
        w.writeheader()
        w.writerows(findings)

    by_verdict: dict[str, int] = {}
    for f in findings:
        by_verdict[f["verdict"]] = by_verdict.get(f["verdict"], 0) + 1
    print(f"=== Verdict counts (n={len(findings)}) ===")
    for k in sorted(by_verdict.keys()):
        print(f"  {k:50s} {by_verdict[k]}")

    # Focus on real defects
    real = [f for f in findings if f["verdict"] not in ("OK", "ISRCTN_ONLY", "TITLE_LOW_OVERLAP")]
    print(f"\n=== {len(real)} non-title defects (real issues to fix) ===\n")
    for f in real:
        print(f"  [{f['verdict']:30s}] {f['file']:50s} {f['key']:18s}")
        print(f"     claim: {f['claim_name']:40s} n={f['claim_n']}")
        print(f"     aact:  {f['aact_brief_title']:60s} n={f['aact_enrollment']}  ratio={f['n_ratio']}")
        if f["country_issues"]:
            print(f"     countries claimed but not in AACT facilities: {f['country_issues']}")
        if f["notes"]:
            print(f"     notes: {f['notes']}")
        print()

    print(f"Written: {OUT_CSV}")


if __name__ == "__main__":
    main()
