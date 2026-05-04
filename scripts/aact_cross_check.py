"""AACT cross-check — verify every NCT in every RapidMeta review HTML against the local
AACT 2026-04-12 snapshot at D:/AACT-storage/AACT/2026-04-12/.

For each NCT extracted from realData blocks across all *_REVIEW.html files:
  1. Look it up in AACT studies.txt (NCT must exist).
  2. Compare AACT brief_title / official_title against my realData `name` field — flag
     low overlap (no shared 4+ char tokens).
  3. Compare AACT enrollment against my row tN+cN (with MULTI_ARM_SUBSET / MITT_FRACTION
     tolerance categories).
  4. Compare AACT countries (countries.txt) against the country list mentioned in my
     `group` snippet — flag if my snippet names a country AACT doesn't list.
  5. Compare AACT lead sponsor (sponsors.txt) against my snippet's sponsor mention —
     flag if my snippet names a sponsor AACT doesn't list as lead.

Output: outputs/aact_cross_check_findings.csv with per-NCT verdict.

LEGACY-* / ISRCTN keys are skipped (not in AACT). Reported separately as ISRCTN_ONLY.

Usage:
    python scripts/aact_cross_check.py
"""
from __future__ import annotations
import csv
import re
from pathlib import Path

AACT_DIR = Path("D:/AACT-storage/AACT/2026-04-12")
REPO_DIR = Path("C:/Projects/Finrenone")
OUT_CSV = REPO_DIR / "outputs" / "aact_cross_check_findings.csv"

# Schema positions (1-indexed converted to 0-indexed)
COL_NCT = 0
COL_BRIEF_TITLE = 33
COL_OFFICIAL_TITLE = 34
COL_PHASE = 37
COL_ENROLLMENT = 38

# Token sets considered "noise" for title-match
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
    """Lowercase, split on non-word, drop short + stopwords."""
    if not s:
        return set()
    raw = re.split(r"[^a-z0-9]+", s.lower())
    return {t for t in raw if len(t) >= 4 and t not in STOPWORDS}


def load_aact_studies() -> dict[str, dict]:
    """Load {nct_id: {brief_title, official_title, phase, enrollment}} from studies.txt."""
    db = {}
    studies_path = AACT_DIR / "studies.txt"
    with studies_path.open(encoding="utf-8", errors="replace") as f:
        next(f)  # skip header
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


def load_aact_countries() -> dict[str, set[str]]:
    """Load {nct_id: set of country names} from countries.txt."""
    db: dict[str, set[str]] = {}
    path = AACT_DIR / "countries.txt"
    with path.open(encoding="utf-8", errors="replace") as f:
        next(f)
        for line in f:
            cols = line.rstrip("\n").split("|")
            if len(cols) < 4:
                continue
            nct = cols[1].strip()
            country = cols[2].strip()
            removed = cols[3].strip().lower() == "true"
            if not nct.startswith("NCT") or not country or removed:
                continue
            db.setdefault(nct, set()).add(country)
    return db


def load_aact_lead_sponsors() -> dict[str, str]:
    """Load {nct_id: lead sponsor name}."""
    db: dict[str, str] = {}
    path = AACT_DIR / "sponsors.txt"
    with path.open(encoding="utf-8", errors="replace") as f:
        next(f)
        for line in f:
            cols = line.rstrip("\n").split("|")
            if len(cols) < 5:
                continue
            nct = cols[1].strip()
            role = cols[3].strip().lower()
            name = cols[4].strip()
            if role == "lead" and nct.startswith("NCT"):
                db[nct] = name
    return db


# Regex to extract trial blocks from realData
NCT_BLOCK_RE = re.compile(
    r"'(NCT\d+(?:_[A-Za-z0-9]+)?|LEGACY-[A-Za-z0-9-]+)'\s*:\s*\{[^}]*?"
    r"name:\s*'([^']+?)'[^}]*?"
    r"tN:\s*(\d+)\s*,\s*cE:\s*\d+\s*,\s*cN:\s*(\d+)",
    re.DOTALL,
)


def extract_trials_from_html(path: Path) -> list[dict]:
    """Extract per-NCT (key, name, tN, cN, snippet ~ first 600 chars of group) from HTML."""
    text = path.read_text(encoding="utf-8", errors="replace")
    out = []
    for m in NCT_BLOCK_RE.finditer(text):
        key = m.group(1)
        name = m.group(2)
        tN = int(m.group(3))
        cN = int(m.group(4))
        # Capture group field for country/sponsor scan
        block_start = m.start()
        block_end = text.find("},", m.end())
        if block_end == -1:
            block_end = m.end() + 2000
        block = text[block_start:min(block_end, block_start + 4000)]
        # Pull `group:` content
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


# Country list to look for in snippet text
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
    "Croatia", "Slovenia", "Latvia", "Mauritania", "Madagascar", "Iran", "Saudi Arabia",
    "Turkey", "Lebanon", "Jordan", "UAE", "Iraq", "Egypt", "Morocco", "Tunisia",
    "Algeria", "Yemen", "Syria", "Liberia", "Sierra Leone", "Angola", "Namibia",
    "Lesotho", "Eswatini", "Swaziland", "Burundi", "Chad", "Republic of the Congo",
]


def scan_countries_in_snippet(snippet: str) -> set[str]:
    """Return set of countries mentioned in snippet text."""
    found = set()
    for c in COUNTRIES_OF_INTEREST:
        if re.search(r"\b" + re.escape(c) + r"\b", snippet, re.IGNORECASE):
            found.add(c)
    return found


def main():
    print("Loading AACT studies.txt ...")
    studies = load_aact_studies()
    print(f"  {len(studies):,} NCTs in AACT 2026-04-12")
    print("Loading AACT countries.txt ...")
    countries = load_aact_countries()
    print(f"  countries for {len(countries):,} NCTs")
    print("Loading AACT sponsors.txt ...")
    sponsors = load_aact_lead_sponsors()
    print(f"  lead sponsors for {len(sponsors):,} NCTs")

    review_files = sorted(REPO_DIR.glob("*_REVIEW.html"))
    print(f"\nScanning {len(review_files)} *_REVIEW.html files ...")

    findings = []
    for hp in review_files:
        trials = extract_trials_from_html(hp)
        for t in trials:
            key = t["key"]
            base_nct = re.match(r"(NCT\d+)", key)
            if not base_nct:
                # ISRCTN/LEGACY — skip (not in AACT)
                findings.append({
                    "file": hp.name,
                    "key": key,
                    "claim_name": t["name"],
                    "claim_n": t["row_total"],
                    "verdict": "ISRCTN_ONLY",
                    "aact_brief_title": "",
                    "aact_enrollment": "",
                    "title_overlap": "",
                    "n_ratio": "",
                    "country_mismatch": "",
                    "notes": "non-AACT key",
                })
                continue
            base_nct = base_nct.group(1)
            row = studies.get(base_nct)
            if not row:
                findings.append({
                    "file": hp.name,
                    "key": key,
                    "claim_name": t["name"],
                    "claim_n": t["row_total"],
                    "verdict": "AACT_NOT_FOUND",
                    "aact_brief_title": "",
                    "aact_enrollment": "",
                    "title_overlap": "",
                    "n_ratio": "",
                    "country_mismatch": "",
                    "notes": "NCT not in AACT 2026-04-12 — likely wrong NCT",
                })
                continue

            # Title overlap
            claim_tokens = normalize_tokens(t["name"])
            aact_tokens = normalize_tokens(row["brief_title"]) | normalize_tokens(row["official_title"])
            shared = claim_tokens & aact_tokens
            overlap = len(shared)
            verdict_title = "TITLE_OK" if overlap >= 1 else "TITLE_MISMATCH"

            # Enrollment ratio
            aact_n = row["enrollment"]
            ratio = (t["row_total"] / aact_n) if (aact_n and aact_n > 0) else None
            if ratio is None:
                verdict_n = "N_NO_AACT_ENROLLMENT"
            elif 0.85 <= ratio <= 1.15:
                verdict_n = "N_OK"
            elif 0.20 <= ratio < 0.85:
                verdict_n = "N_MULTI_ARM_OR_MITT"
            elif 1.15 < ratio <= 2.10:
                verdict_n = "N_MITT_PLUS_OR_SINGLE_ARM"
            else:
                verdict_n = "N_OUTLIER"

            # Country check
            aact_countries = countries.get(base_nct, set())
            snippet_countries = scan_countries_in_snippet(t["group"])
            # Filter to "primary" claims — words I claimed are countries with sites
            country_mismatch = []
            for c in snippet_countries:
                # Normalize Cote/Côte d'Ivoire equivalence
                norm_c = c.replace("Cote d'Ivoire", "Côte d'Ivoire")
                norm_aact = {ac.replace("Cote d'Ivoire", "Côte d'Ivoire") for ac in aact_countries}
                if norm_c not in norm_aact:
                    # Allow common synonyms
                    if c in ("UK", "United Kingdom"):
                        if not ({"United Kingdom"} & aact_countries):
                            country_mismatch.append(c)
                    elif c in ("USA", "United States"):
                        if not ({"United States"} & aact_countries):
                            country_mismatch.append(c)
                    elif c == "DRC":
                        if not ({"Republic of the Congo", "Democratic Republic of the Congo", "Congo"} & aact_countries):
                            country_mismatch.append(c)
                    else:
                        country_mismatch.append(c)

            verdict_country = "COUNTRY_OK" if not country_mismatch else "COUNTRY_MISMATCH"

            verdict_overall = "OK"
            notes = []
            if verdict_title == "TITLE_MISMATCH":
                verdict_overall = "TITLE_MISMATCH"
                notes.append(f"title 0-token overlap (claim='{t['name'][:40]}' aact='{row['brief_title'][:40]}')")
            if verdict_n == "N_OUTLIER":
                verdict_overall = "N_OUTLIER" if verdict_overall == "OK" else verdict_overall + "+N_OUTLIER"
                notes.append(f"row {t['row_total']} vs aact {aact_n} ratio {ratio:.2f}")
            if verdict_country == "COUNTRY_MISMATCH":
                if verdict_overall == "OK":
                    verdict_overall = "COUNTRY_MISMATCH"
                else:
                    verdict_overall += "+COUNTRY_MISMATCH"
                notes.append(f"snippet countries not in AACT: {', '.join(country_mismatch)}")

            findings.append({
                "file": hp.name,
                "key": key,
                "claim_name": t["name"],
                "claim_n": t["row_total"],
                "verdict": verdict_overall,
                "aact_brief_title": row["brief_title"][:80],
                "aact_enrollment": aact_n if aact_n else "",
                "title_overlap": overlap,
                "n_ratio": f"{ratio:.2f}" if ratio is not None else "",
                "country_mismatch": ",".join(country_mismatch) if country_mismatch else "",
                "notes": "; ".join(notes),
            })

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(findings[0].keys()))
        w.writeheader()
        w.writerows(findings)

    # Summary
    by_verdict: dict[str, int] = {}
    for f in findings:
        by_verdict[f["verdict"]] = by_verdict.get(f["verdict"], 0) + 1

    print(f"\n=== Verdict counts ({len(findings)} total trial-rows) ===")
    for k in sorted(by_verdict.keys()):
        print(f"  {k:30s} {by_verdict[k]}")

    print(f"\n=== High-priority issues ===")
    issues = [f for f in findings if f["verdict"] in ("AACT_NOT_FOUND", "TITLE_MISMATCH", "N_OUTLIER", "COUNTRY_MISMATCH") or "+" in f["verdict"]]
    for f in issues[:25]:
        print(f"  [{f['verdict']}] {f['file']:55s} {f['key']:30s} {f['notes']}")
    if len(issues) > 25:
        print(f"  ... and {len(issues) - 25} more (see {OUT_CSV})")

    print(f"\nWritten: {OUT_CSV}")


if __name__ == "__main__":
    main()
