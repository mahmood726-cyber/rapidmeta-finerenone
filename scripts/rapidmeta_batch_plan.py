#!/usr/bin/env python
"""
Build the Phase-2 batch list from RAPIDMETA_ERROR_SWEEP.json.

The batch order is DERIVED from the sweep, not hand-authored: apps are scored by
severity x prevalence, with the live-harm classes forced to the front. Re-running this after a
fresh sweep re-derives the plan, so the plan cannot drift from the evidence.

    python scripts/rapidmeta_batch_plan.py            # writes outputs/rapidmeta_batch_list.json
    python scripts/rapidmeta_batch_plan.py --md       # also prints the markdown tables
"""
from __future__ import annotations

import argparse
import io
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

if not getattr(sys.stdout, "_rm_wrapped", False):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    try:
        sys.stdout._rm_wrapped = True
    except AttributeError:
        pass

ROOT = Path(__file__).resolve().parent.parent

SEV_WEIGHT = {"P0": 10, "P1": 4, "P2": 1}

# Types that Phase 1 fixes STRUCTURALLY by patching the shared engine. They are excluded from the
# Phase-2 scoring so the batch order reflects DATA work only — otherwise every app scores the same
# and the ordering carries no information.
PHASE1_STRUCTURAL = {
    "RM-A02", "RM-A05", "RM-A14", "RM-B01", "RM-B02", "RM-B03",
    "RM-F01", "RM-F02", "RM-F03", "RM-F04", "RM-F05", "RM-F06", "RM-F07",
    "RM-G01", "RM-H01", "RM-H02", "RM-H03", "RM-H04", "RM-H05",
    "RM-I01", "RM-J01", "RM-J02", "RM-J05", "RM-D07",
    # Added after the 52-detector sweep: these are TEMPLATE strings or ENGINE logic, not per-app
    # data, and their >60% prevalence is the signature of that. Phase 1 owns them.
    "RM-A14",   # the escalc generator builds ai/ci across every trial regardless of endpoint
    "RM-D08",   # the registry-status assertions are boilerplate
    "RM-G03",   # the RoB chip renderer disagrees with the extraction evidence structurally
    "RM-J07",   # the integrity gate itself must become fail-closed
}

# Forced to the front regardless of score: these change what a reader would DO.
LIVE_HARM = ["RM-I01", "RM-I02", "RM-A12", "RM-A10", "RM-C03", "RM-C04", "RM-V01"]
CONTAMINATION = ["RM-E03", "RM-E02", "RM-E01"]
WRONG_IDENTITY = ["RM-D01", "RM-D06", "RM-D10", "RM-D02", "RM-D12"]
COMPLETENESS = ["RM-B08", "RM-B05", "RM-A13", "RM-A01", "RM-A03"]

PRIORITY_LANES = [
    ("L1-live-harm", LIVE_HARM,
     "direction inversion, an effect that contradicts its own 2x2, a KM risk rendered as a count, "
     "arm reversal, or a fixture-verified value error. A reader acting on these acts wrongly."),
    ("L2-contamination", CONTAMINATION,
     "a live monitoring watchlist or claim-bearing slot carrying another drug class."),
    ("L3-wrong-identity", WRONG_IDENTITY,
     "a wrong NCT importing foreign eligibility text, a duplicate/NULLED ghost row, a wrong "
     "citation, or a filename that names a different subject."),
    ("L4-completeness", COMPLETENESS,
     "an omitted eligible trial, k far below a known synthesis, or composites pooled across "
     "different component sets."),
]

SOURCE_NEED = {
    "RM-D01": "ClinicalTrials.gov API v2 (resolve every NCT; compare title/condition/phase/arms)",
    "RM-D02": "PubMed (resolve every PMID; confirm it reports THIS randomisation)",
    "RM-D12": "PubMed esummary (volume/issue/pages) + CrossRef for the DOI",
    "RM-D03": "PubMed article_types (reject Clinical Trial Protocol as a source for counts)",
    "RM-A06": "CT.gov posted results: read unitOfMeasure before using any value",
    "RM-A10": "the primary publication: is the % a KM estimate or events/N?",
    "RM-C03": "CT.gov armGroups: bind by TITLE, never index",
    "RM-C04": "CT.gov armGroups + the publication's own arm sizes",
    "RM-C02": "CT.gov results baseline module, Total row (not an arm row)",
    "RM-B05": "a benchmark synthesis + a registry search; record include/exclude per eligible trial",
    "RM-B08": "the benchmark synthesis's own trial list",
    "RM-A13": "each trial's registered primary endpoint component set",
    "RM-V01": "already source-verified: tests/fixtures/rapidmeta_error_fixtures.json",
}


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def score(hits, prevalence):
    """severity x (1 - prevalence): a P0 that is RARE is a per-app data defect and ranks high;
    a P0 present in 95% of apps is structural and Phase 1 owns it."""
    s = 0.0
    for eid in hits:
        if eid in PHASE1_STRUCTURAL:
            continue
        sev = SEV_WEIGHT.get(prevalence.get(eid, {}).get("severity", "P1"), 4)
        pct = float(prevalence.get(eid, {}).get("pct_of_apps", 50)) / 100.0
        s += sev * (1.0 - min(pct, 0.99))
    return round(s, 2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sweep", default=str(ROOT / "RAPIDMETA_ERROR_SWEEP.json"))
    ap.add_argument("--size", type=int, default=8, help="apps per batch")
    ap.add_argument("--batches", type=int, default=24, help="how many batches to schedule now")
    ap.add_argument("--md", action="store_true")
    args = ap.parse_args()

    sweep = load(Path(args.sweep))
    prevalence = sweep["prevalence"]
    apps = sweep["apps"]

    fixtures = {}
    fp = ROOT / "tests" / "fixtures" / "rapidmeta_error_fixtures.json"
    if fp.exists():
        fixtures = {k: v for k, v in load(fp).items() if not k.startswith("_")}

    rows = []
    for path, rec in apps.items():
        hits = list(rec.get("hits", {}).keys())
        if not hits:
            continue
        lanes = [name for name, ids, _ in PRIORITY_LANES if any(i in hits for i in ids)]
        data_hits = [h for h in hits if h not in PHASE1_STRUCTURAL]
        rows.append({
            "path": path,
            "app": rec.get("app", path),
            "k": rec.get("k", 0),
            "score": score(hits, prevalence),
            "lanes": lanes,
            "lane_rank": min([i for i, (n, ids, _) in enumerate(PRIORITY_LANES)
                              if any(x in hits for x in ids)] or [len(PRIORITY_LANES)]),
            "data_error_types": sorted(data_hits),
            "n_data_errors": len(data_hits),
            "fixture": rec.get("app") in fixtures,
            "source_needs": sorted({SOURCE_NEED[h] for h in data_hits if h in SOURCE_NEED}),
        })

    # fixtures first (their truth is already verified), then lane rank, then score
    rows.sort(key=lambda r: (not r["fixture"], r["lane_rank"], -r["score"], r["app"]))

    batches = []
    for i in range(0, min(len(rows), args.size * args.batches), args.size):
        chunk = rows[i:i + args.size]
        dom = Counter()
        for r in chunk:
            dom.update(r["data_error_types"])
        needs = sorted({n for r in chunk for n in r["source_needs"]})
        lanes = sorted({l for r in chunk for l in r["lanes"]})
        batches.append({
            "batch": len(batches) + 1,
            # PATHS, not basenames: 17 basenames occur twice (root app + a stale
            # e156-submission copy) and both need the fix - a fix applied to one variant is not
            # applied to the app (CARDIO_UPGRADE_RECIPE 0.2).
            "apps": [r["app"] for r in chunk],
            "paths": [r["path"] for r in chunk],
            "lanes": lanes,
            "dominant_error_types": [f"{e} ({n})" for e, n in dom.most_common(6)],
            "source_needs": needs,
            "has_verified_fixture": [r["app"] for r in chunk if r["fixture"]],
            "mean_k": round(sum(r["k"] for r in chunk) / max(1, len(chunk)), 1),
            "est_hours": round(sum(1.6 + 0.33 * r["k"] + 0.08 * r["n_data_errors"] for r in chunk), 1),
        })

    out = {
        "generated_from": str(Path(args.sweep).name),
        "corpus": sweep["corpus"],
        "apps_with_data_errors": len(rows),
        "apps_scheduled": sum(len(b["apps"]) for b in batches),
        "batch_size": args.size,
        "phase1_structural_types": sorted(PHASE1_STRUCTURAL),
        "priority_lanes": [{"lane": n, "ids": ids, "why": why} for n, ids, why in PRIORITY_LANES],
        "batches": batches,
        "unscheduled_backlog": len(rows) - sum(len(b["apps"]) for b in batches),
    }
    dest = ROOT / "outputs" / "rapidmeta_batch_list.json"
    dest.parent.mkdir(exist_ok=True)
    dest.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"apps with >=1 DATA (non-Phase-1) error: {len(rows)}")
    print(f"scheduled: {out['apps_scheduled']} in {len(batches)} batches of {args.size}; "
          f"backlog {out['unscheduled_backlog']}")
    print(f"wrote {dest.relative_to(ROOT)}")

    if args.md:
        print("\n| # | apps | lanes | dominant data-error types | est h |")
        print("|---|---|---|---|---:|")
        for b in batches:
            print(f"| {b['batch']} | " + "<br>".join(f"`{a}`" for a in b["paths"]) + " | " +
                  ", ".join(b["lanes"]) + " | " + ", ".join(b["dominant_error_types"]) +
                  f" | {b['est_hours']} |")
    return 0


if __name__ == "__main__":
    sys.exit(main())
