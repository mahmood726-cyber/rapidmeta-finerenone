"""Build the two AACT-derived sidecar maps the generators consume.

Outputs:
    outputs/pmid_resolver/nct_to_pmid.json
        NCT -> {pmid, type}. Picking rule: smallest PMID among RESULT+DERIVED
        per NCT (oldest primary publication; extensions get higher PMIDs).
        BACKGROUND-typed refs are excluded to keep wrong-paper false positives
        out — see commit 4917069b8 lite-page mismatch findings.

    outputs/pmid_resolver/nct_design.json
        NCT -> {allocation, masking, intervention_model, primary_purpose,
                subject_masked, caregiver_masked, investigator_masked,
                outcomes_assessor_masked}. Used as a defensible RoB-2 heuristic
        by both `enrich_trials_with_aact_design.py` (retroactive) and
        `bulk_clone_audit_first.py` (forward).

Reads from F:\\AACT-storage\\AACT\\2026-04-12\\{study_references.txt,designs.txt}.
"""
from __future__ import annotations
import csv
import json
import sys
import io
from pathlib import Path
from collections import Counter

if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

csv.field_size_limit(50_000_000)

HERE = Path(__file__).resolve().parent.parent
AACT = Path(r"F:\AACT-storage\AACT\2026-04-12")
OUT = HERE / "outputs" / "pmid_resolver"
OUT.mkdir(parents=True, exist_ok=True)


def build_pmid_map():
    ref = AACT / "study_references.txt"
    result_pmids: dict[str, list[str]] = {}
    derived_pmids: dict[str, list[str]] = {}
    type_of: dict[tuple[str, str], str] = {}
    n_rows = n_bg = 0

    with ref.open(encoding="utf-8", errors="replace") as f:
        rd = csv.reader(f, delimiter="|")
        next(rd)
        for row in rd:
            if len(row) < 4:
                continue
            n_rows += 1
            nct = row[1].strip()
            pmid = row[2].strip()
            rtype = row[3].strip()
            if not pmid.isdigit() or not nct.startswith("NCT"):
                continue
            type_of[(nct, pmid)] = rtype
            if rtype == "RESULT":
                result_pmids.setdefault(nct, []).append(pmid)
            elif rtype == "DERIVED":
                derived_pmids.setdefault(nct, []).append(pmid)
            else:
                n_bg += 1

    out: dict[str, dict] = {}
    for nct in set(result_pmids) | set(derived_pmids):
        pool = result_pmids.get(nct, []) + derived_pmids.get(nct, [])
        if not pool:
            continue
        best = min(pool, key=lambda x: int(x))
        out[nct] = {"pmid": best, "type": type_of[(nct, best)]}

    p = OUT / "nct_to_pmid.json"
    p.write_text(json.dumps(out), encoding="utf-8")
    print(f"  nct_to_pmid.json: {len(out):,} NCTs (BACKGROUND-only skipped: {n_bg:,} rows)")
    print(f"  type breakdown:", Counter(v["type"] for v in out.values()))


def build_design_map():
    ref = AACT / "designs.txt"
    out: dict[str, dict] = {}
    with ref.open(encoding="utf-8", errors="replace") as f:
        rd = csv.DictReader(f, delimiter="|")
        for row in rd:
            nct = (row.get("nct_id") or "").strip()
            if not nct.startswith("NCT"):
                continue
            out[nct] = {
                "allocation": (row.get("allocation") or "").strip(),
                "masking": (row.get("masking") or "").strip(),
                "intervention_model": (row.get("intervention_model") or "").strip(),
                "primary_purpose": (row.get("primary_purpose") or "").strip(),
                "subject_masked": (row.get("subject_masked") or "").strip(),
                "caregiver_masked": (row.get("caregiver_masked") or "").strip(),
                "investigator_masked": (row.get("investigator_masked") or "").strip(),
                "outcomes_assessor_masked": (row.get("outcomes_assessor_masked") or "").strip(),
            }
    p = OUT / "nct_design.json"
    p.write_text(json.dumps(out), encoding="utf-8")
    print(f"  nct_design.json: {len(out):,} NCTs")
    print(f"  allocation:", Counter(v["allocation"] for v in out.values()).most_common(5))
    print(f"  masking:", Counter(v["masking"] for v in out.values()).most_common(7))


def main():
    print("Building NCT -> PMID map...")
    build_pmid_map()
    print("Building NCT -> design map...")
    build_design_map()


if __name__ == "__main__":
    main()
