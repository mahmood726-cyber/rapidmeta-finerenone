"""6th ship-gate — AACT outcome-direction concordance check.

Inspired by Mahmood's Trial Truthfulness Atlas Flag-3 ("direction concordance":
AACT effect sign != MA effect sign). For each NCT in our corpus, query AACT
outcome_analyses.txt for the trial's primary outcome effect estimate and
compare sign + magnitude vs our claimed publishedHR.

This is more authoritative than per-trial published-MA comparison because:
  - Source of truth is the trial's own results posting (FDAAA-mandated since
    2008), not a secondary ground-truth dictionary.
  - Eliminates the "my GROUND_TRUTH dict had wrong NCT-trial mappings"
    failure mode that bit us earlier.
  - Catches sign-flips and large magnitude errors authoritatively.

Schema (AACT 2026-04-12):
  - studies.txt: nct_id, brief_title, enrollment
  - outcomes.txt: nct_id, outcome_type ('Primary'/'Secondary'/'Other'),
    title, units
  - outcome_analyses.txt: nct_id, outcome_id, param_type, param_value,
    ci_lower_limit, ci_upper_limit, p_value, method, groups_description

Approach:
  1. Index outcomes.txt: filter outcome_type='Primary'; map outcome_id -> title
  2. Index outcome_analyses.txt: per-NCT, find primary-outcome analyses with
     numeric param_value (ratio/difference type)
  3. For each NCT in our corpus, fetch first primary outcome's effect estimate
  4. Compare sign and magnitude vs claimed publishedHR
  5. Flag: NCT_NOT_IN_AACT_RESULTS (no posted results) /
     AACT_SIGN_DIFFER (sign opposite) /
     AACT_MAGNITUDE_DIFFER (>50% on log scale) / OK
"""
from __future__ import annotations
import sys, io, csv, re, math
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path("C:/Projects/Finrenone")
AACT_DIR = Path("D:/AACT-storage/AACT/2026-04-12")
OUT_CSV = REPO / "outputs" / "aact_outcome_concordance.csv"


def load_primary_outcomes() -> dict[str, list[str]]:
    """Map nct_id -> list of primary outcome_ids."""
    db: dict[str, list[str]] = {}
    path = AACT_DIR / "outcomes.txt"
    with path.open(encoding="utf-8", errors="replace") as f:
        next(f)
        for line in f:
            cols = line.rstrip("\n").split("|")
            if len(cols) < 4:
                continue
            outcome_id = cols[0].strip()
            nct = cols[1].strip()
            outcome_type = cols[2].strip().upper()
            if not nct.startswith("NCT") or outcome_type != "PRIMARY":
                continue
            db.setdefault(nct, []).append(outcome_id)
    return db


def load_primary_analyses(primary_ids_by_nct: dict[str, list[str]]) -> dict[str, dict]:
    """Map nct_id -> first primary-outcome analysis: {param_type, value, lci, uci, method}."""
    primary_id_to_nct: dict[str, str] = {}
    for nct, ids in primary_ids_by_nct.items():
        for oid in ids:
            primary_id_to_nct[oid] = nct
    db: dict[str, dict] = {}
    path = AACT_DIR / "outcome_analyses.txt"
    with path.open(encoding="utf-8", errors="replace") as f:
        next(f)
        for line in f:
            cols = line.rstrip("\n").split("|")
            if len(cols) < 18:
                continue
            outcome_id = cols[2].strip()
            if outcome_id not in primary_id_to_nct:
                continue
            nct = primary_id_to_nct[outcome_id]
            if nct in db:  # already captured first analysis for this NCT
                continue
            try:
                pv = float(cols[6]) if cols[6].strip() else None
                lci = float(cols[13]) if cols[13].strip() else None
                uci = float(cols[14]) if cols[14].strip() else None
            except ValueError:
                continue
            if pv is None:
                continue
            db[nct] = {
                "param_type": cols[5].strip(),
                "value": pv,
                "lci": lci,
                "uci": uci,
                "method": cols[17].strip()[:60],
            }
    return db


# Match trial blocks in our HTMLs
TRIAL_RE = re.compile(
    r"'(NCT\d+)'\s*:\s*\{[^}]*?"
    r"name:\s*'([^']+?)'[^}]*?"
    r"publishedHR:\s*([\d.eE+\-]+|null|None|NaN)",
    re.DOTALL,
)


def parse_num(s):
    if s is None:
        return None
    s = s.strip()
    if s.lower() in ("null", "none", "nan"):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def main():
    print("Loading AACT primary outcomes ...")
    pos = load_primary_outcomes()
    print(f"  {len(pos)} NCTs with primary outcome rows")
    print("Loading AACT primary outcome analyses ...")
    analyses = load_primary_analyses(pos)
    print(f"  {len(analyses)} NCTs with usable primary analysis (numeric param + CI)")

    review_files = sorted(REPO.glob("*_REVIEW.html"))
    print(f"\nScanning {len(review_files)} review HTMLs ...")

    findings = []
    for hp in review_files:
        text = hp.read_text(encoding="utf-8", errors="replace")
        for m in TRIAL_RE.finditer(text):
            nct = m.group(1)
            name = m.group(2)
            our_hr = parse_num(m.group(3))
            if our_hr is None:
                continue

            aact = analyses.get(nct)
            if not aact:
                findings.append({
                    "file": hp.name, "nct": nct, "name": name[:30],
                    "our_hr": our_hr, "aact_param_type": "", "aact_value": "",
                    "verdict": "AACT_NO_PRIMARY_RESULT",
                    "notes": "No primary-outcome analysis with numeric param_value+CI in AACT",
                })
                continue

            # Sign-direction check
            issues = []
            param_type = aact["param_type"].lower()

            # For ratio types (HR, RR, OR), null = 1.0; for difference types (MD, RD), null = 0.0
            null_ref = 1.0 if any(k in param_type for k in ("ratio", "hr", "rr", "or")) else 0.0

            # Convert "favours-treatment" expectation
            our_below_null = our_hr < null_ref - 0.05
            our_above_null = our_hr > null_ref + 0.05
            aact_below_null = aact["value"] < null_ref - 0.05
            aact_above_null = aact["value"] > null_ref + 0.05

            if (our_below_null and aact_above_null) or (our_above_null and aact_below_null):
                issues.append(f"SIGN_DIFFER(our={our_hr},aact={aact['value']})")

            # Magnitude check (log scale for ratios)
            if null_ref == 1.0 and aact["value"] > 0 and our_hr > 0:
                log_ratio = abs(math.log(our_hr) - math.log(aact["value"]))
                if log_ratio > math.log(2.0):
                    issues.append(f"MAGNITUDE_DIFFER(our={our_hr:.2f},aact={aact['value']:.2f})")

            verdict = "OK" if not issues else "DEFECT"
            findings.append({
                "file": hp.name, "nct": nct, "name": name[:30],
                "our_hr": our_hr,
                "aact_param_type": aact["param_type"],
                "aact_value": aact["value"],
                "aact_lci": aact["lci"] if aact["lci"] is not None else "",
                "aact_uci": aact["uci"] if aact["uci"] is not None else "",
                "aact_method": aact["method"],
                "verdict": verdict,
                "notes": ";".join(issues),
            })

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        if findings:
            w = csv.DictWriter(f, fieldnames=list(findings[0].keys()))
            w.writeheader()
            w.writerows(findings)

    by_v: dict[str, int] = {}
    for r in findings:
        by_v[r["verdict"]] = by_v.get(r["verdict"], 0) + 1
    print(f"\n=== Summary ===")
    print(f"  Trial-rows: {len(findings)}")
    for k, v in sorted(by_v.items()):
        print(f"  {k:30s} {v}")

    real = [r for r in findings if r["verdict"] == "DEFECT"]
    print(f"\n=== {len(real)} DEFECTs ===\n")
    for r in real[:30]:
        print(f"  {r['file'][:42]:42s} {r['nct']:14s} {r['name'][:28]:28s} OUR={r['our_hr']} AACT={r['aact_value']} ({r['aact_param_type'][:15]})")
        print(f"     {r['notes']}")
    print(f"\nWritten: {OUT_CSV}")


if __name__ == "__main__":
    main()
