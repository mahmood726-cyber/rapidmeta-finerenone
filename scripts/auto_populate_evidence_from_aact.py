"""Auto-populate static Demographics + Eligibility evidence rows for every NCT
trial-row in the corpus, from AACT 2026-04-12 baseline_measurements.txt + eligibilities.txt.

Closes the corpus-wide gap detected by evidence_completeness_audit.py: 638/638
trial-rows lacked these rows in their static realData evidence array.

For each NCT block in each *_REVIEW.html:
  1. Look up AACT eligibilities row → generate Eligibility evidence text
     (gender, age range, healthy_volunteers, first 400 chars of criteria).
  2. Look up AACT baseline_measurements rows for Age, Sex, Race → generate
     Demographics evidence text.
  3. Insert both rows at the end of the existing `evidence: [...]` array
     (only if not already present per heuristic).

Skips: LEGACY-* keys (no AACT data), trials with NCT not in AACT.

Output: in-place edit of *_REVIEW.html files; outputs/auto_populate_log.csv with per-trial action.

Idempotency: checks for existing 'AACT-derived' marker in evidence labels
before inserting. Safe to re-run.
"""
from __future__ import annotations
import sys, io, csv, re
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

AACT_DIR = Path("D:/AACT-storage/AACT/2026-04-12")
REPO_DIR = Path("C:/Projects/Finrenone")
LOG_CSV = REPO_DIR / "outputs" / "auto_populate_log.csv"


def load_eligibilities() -> dict[str, dict]:
    """{nct: {gender, min_age, max_age, healthy_volunteers, criteria_short}}"""
    db = {}
    path = AACT_DIR / "eligibilities.txt"
    with path.open(encoding="utf-8", errors="replace") as f:
        next(f)
        for line in f:
            cols = line.rstrip("\n").split("|")
            if len(cols) < 9:
                continue
            nct = cols[1].strip()
            if not nct.startswith("NCT"):
                continue
            criteria = cols[8].replace("\n", " ").replace("|", "/").strip()
            # Trim to first ~500 chars, escape JS single-quotes
            short = criteria[:500].replace("'", "\\'") + ("..." if len(criteria) > 500 else "")
            db[nct] = {
                "gender": cols[3].strip(),
                "min_age": cols[4].strip(),
                "max_age": cols[5].strip(),
                "healthy_volunteers": cols[6].strip(),
                "criteria_short": short,
            }
    return db


def load_baseline_demographics() -> dict[str, dict]:
    """{nct: {age, sex, race}} where each is a short summary string."""
    db: dict[str, dict] = {}
    path = AACT_DIR / "baseline_measurements.txt"
    # Schema: id|nct_id|result_group_id|ctgov_group_code|classification|category|title|description|units|param_type|param_value|...
    with path.open(encoding="utf-8", errors="replace") as f:
        next(f)
        for line in f:
            cols = line.rstrip("\n").split("|")
            if len(cols) < 12:
                continue
            nct = cols[1].strip()
            classification = cols[4].strip()
            category = cols[5].strip()
            title = cols[6].strip()
            param_type = cols[9].strip()
            param_value = cols[10].strip()
            units = cols[8].strip()

            if not nct.startswith("NCT"):
                continue

            row = db.setdefault(nct, {"age_total": [], "sex_total": [], "race_total": []})

            # Age: title or category contains "Age"
            if (title.lower() == "age" or "age, continuous" in title.lower() or category.lower() == "age, continuous") and param_type == "Mean":
                if param_value and units.lower() in ("years", "year", ""):
                    if not row["age_total"]:
                        row["age_total"].append(f"{param_value} {units}")

            # Sex
            if title.lower() in ("sex", "gender", "sex/gender, customized") or category.lower() == "sex":
                if classification.lower() == "female" and param_value:
                    row["sex_total"].append(f"Female {param_value}")
                elif classification.lower() == "male" and param_value:
                    row["sex_total"].append(f"Male {param_value}")

            # Race
            if title.lower() in ("race", "race/ethnicity", "ethnicity", "race (nih/omb)", "race and ethnicity, customized"):
                if classification and param_value:
                    if len(row["race_total"]) < 5:
                        row["race_total"].append(f"{classification} {param_value}")
    return db


# Regex to find each NCT block start
NCT_KEY_RE = re.compile(r"'(NCT\d+(?:_[A-Za-z0-9]+)?)'\s*:\s*\{", re.MULTILINE)


def find_evidence_array_end(text: str, block_start: int, block_end: int) -> int | None:
    """Find the position just before the closing `]` of `evidence: [...]` within block."""
    block = text[block_start:block_end]
    em = re.search(r"evidence:\s*\[", block)
    if not em:
        return None
    # Walk forward from after `[` to find matching `]`
    abs_pos = block_start + em.end()
    depth = 1
    while abs_pos < block_end:
        c = text[abs_pos]
        if c == "[":
            depth += 1
        elif c == "]":
            depth -= 1
            if depth == 0:
                return abs_pos  # position of the closing `]`
        abs_pos += 1
    return None


def find_block_end(text: str, key_match_end: int) -> int:
    """Find end of current trial object (matching `}` at depth 0)."""
    i = text.find("{", key_match_end - 1)
    if i == -1:
        return key_match_end
    depth = 0
    while i < len(text):
        c = text[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return len(text)


def has_aact_marker(block: str) -> bool:
    """Skip if already auto-populated (idempotency check)."""
    return "AACT-derived (auto-populated 2026-05-04)" in block


def build_eligibility_row(elig: dict) -> str:
    parts = []
    if elig["gender"]:
        parts.append(f"Sex: {elig['gender']}")
    if elig["min_age"]:
        parts.append(f"min age {elig['min_age']}")
    if elig["max_age"]:
        parts.append(f"max age {elig['max_age']}")
    if elig["healthy_volunteers"]:
        parts.append(f"healthy volunteers: {elig['healthy_volunteers']}")
    summary = "; ".join(parts) if parts else "(no structured eligibility metadata in AACT)"
    text = f"AACT-derived (auto-populated 2026-05-04). {summary}. CRITERIA: {elig['criteria_short']}"
    return f"{{ label: 'Eligibility (AACT-derived)', source: 'AACT 2026-04-12 eligibilities.txt', text: '{text}', highlights: ['AACT-derived'] }}"


def build_demographics_row(demo: dict) -> str:
    parts = []
    if demo["age_total"]:
        parts.append(f"Age: mean {demo['age_total'][0]}")
    if demo["sex_total"]:
        parts.append(f"Sex: {', '.join(demo['sex_total'][:3])}")
    if demo["race_total"]:
        parts.append(f"Race: {', '.join(demo['race_total'][:5])}")
    if not parts:
        return ""  # no demographics to add
    summary = "; ".join(parts)
    text = f"AACT-derived (auto-populated 2026-05-04). {summary}. NOTE: figures are total-arms aggregate from CT.gov baseline-measurements module; per-arm breakdown available in AACT raw data. RACE caveat: review trial-population racial composition for external-validity considerations.".replace("'", "\\'")
    return f"{{ label: 'Demographics (AACT-derived)', source: 'AACT 2026-04-12 baseline_measurements.txt', text: '{text}', highlights: ['AACT-derived'] }}"


def main():
    print("Loading AACT eligibilities ...")
    elig_db = load_eligibilities()
    print(f"  {len(elig_db):,} NCTs with eligibility metadata")
    print("Loading AACT baseline_measurements (this is large, ~30s) ...")
    demo_db = load_baseline_demographics()
    print(f"  {len(demo_db):,} NCTs with baseline-measurement data")

    review_files = sorted(REPO_DIR.glob("*_REVIEW.html"))
    print(f"\nProcessing {len(review_files)} review HTMLs ...")

    log_rows = []
    files_modified = 0

    for hp in review_files:
        text = hp.read_text(encoding="utf-8", errors="replace")
        original = text
        modified = False

        # Find all NCT blocks (process in reverse so insertions don't shift earlier offsets)
        nct_keys = []
        for m in NCT_KEY_RE.finditer(text):
            nct = m.group(1)
            block_start = m.start()
            block_end = find_block_end(text, m.end())
            nct_keys.append((nct, block_start, block_end))

        for nct, bs, be in reversed(nct_keys):
            base_nct = re.match(r"NCT\d+", nct).group()
            block = text[bs:be]
            if has_aact_marker(block):
                log_rows.append({"file": hp.name, "nct": nct, "action": "ALREADY_POPULATED"})
                continue

            arr_end = find_evidence_array_end(text, bs, be)
            if arr_end is None:
                log_rows.append({"file": hp.name, "nct": nct, "action": "NO_EVIDENCE_ARRAY"})
                continue

            elig = elig_db.get(base_nct)
            demo = demo_db.get(base_nct)
            new_rows = []
            if elig:
                new_rows.append(build_eligibility_row(elig))
            if demo and any([demo["age_total"], demo["sex_total"], demo["race_total"]]):
                drow = build_demographics_row(demo)
                if drow:
                    new_rows.append(drow)

            if not new_rows:
                log_rows.append({"file": hp.name, "nct": nct, "action": "NO_AACT_DATA"})
                continue

            # Determine if existing array has trailing comma or content
            arr_content_before = text[text.find("[", bs):arr_end]
            has_existing = bool(re.search(r"\{[^}]+\}", arr_content_before))
            insert_str = ("," if has_existing else "") + "\n                        " + ",\n                        ".join(new_rows) + "\n                    "

            text = text[:arr_end] + insert_str + text[arr_end:]
            modified = True
            log_rows.append({"file": hp.name, "nct": nct, "action": f"ADDED_{len(new_rows)}_ROWS"})

        if modified:
            hp.write_text(text, encoding="utf-8")
            files_modified += 1
            print(f"  {hp.name}: modified")

    LOG_CSV.parent.mkdir(parents=True, exist_ok=True)
    with LOG_CSV.open("w", newline="", encoding="utf-8") as f:
        if log_rows:
            w = csv.DictWriter(f, fieldnames=list(log_rows[0].keys()))
            w.writeheader()
            w.writerows(log_rows)

    by_action: dict[str, int] = {}
    for r in log_rows:
        by_action[r["action"]] = by_action.get(r["action"], 0) + 1

    print(f"\n=== Summary ===")
    print(f"  Files modified: {files_modified}/{len(review_files)}")
    print(f"  Trial-rows by action:")
    for k, v in sorted(by_action.items(), key=lambda x: -x[1]):
        print(f"    {k:30s} {v}")
    print(f"\nLog: {LOG_CSV}")


if __name__ == "__main__":
    main()
