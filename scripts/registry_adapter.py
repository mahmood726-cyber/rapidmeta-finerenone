"""Filtered registry adapter: ENUMERATE the candidate set, then screen it.

Replaces hand-typed trial ingestion. For each topic this writes the two artefacts
the corpus currently has for zero topics:

  1. EXECUTED SEARCH RECORD  -- the query as run, the source, the snapshot's
     DATA DATE (not its folder name), and the resolved result count. This is the
     search, not a description of one.
  2. SCREENING LEDGER        -- every candidate the registry returned, each with
     an include/exclude decision and a reason. A `k` with no denominator is the
     defect one level down, so the denominator is the ledger's length and is
     never the post-filter count.

WHAT THIS DOES NOT DO
  It does not pick trials. Eligibility here is entirely a function of AACT
  STRUCTURED FIELDS (intervention name, condition name, study_type, phase,
  enrollment, allocation). No prose regex: prose regex has negative value at
  this layer. The one judgement call -- PICO mapping per trial -- is left to a
  downstream labelling step and written as data.

  It does not touch the citation-chasing path. Comparator reference-list seeding
  and the FOUND_VIA_COMPARATOR tag belong to a different lane. Both lanes meet
  at inputs.trials; this one writes only the registry side.

DETERMINISM (read this before trusting a diff)
  Every iteration order here is `sorted()`, and the final ordering key ends in
  the NCT id. Measured over two runs on one snapshot: the SCREENING LEDGER is
  byte-identical, and the SEARCH RECORD differs in exactly one line,
  `executed_at_utc`, which is the field whose whole job is to differ. So diff a
  ledger, not a record.

  That establishes STABILITY, not correctness -- a stable wrong filter is still
  a wrong filter, and it will look reassuringly reproducible. Correctness of
  each filter is established separately, by POSITIVE_CONTROLS below: a filter is
  not trusted until a case that MUST pass it has been shown to pass it. A zero
  from an unproven filter is NOT_FOUND, never ABSENT.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

csv.field_size_limit(1 << 30)

HERE = Path(__file__).resolve().parent.parent
AACT_ROOT = Path(os.environ.get("AACT_ROOT", "F:/AACT-storage/AACT"))

# Snapshot folder -> the date its DATA is actually current to, measured as
# max(last_update_submitted_qc_date) in studies.txt. A folder name is a label;
# the data is the fact, and the label always overstates it in the ghost
# direction. Mirrors F:/AACT-storage/aact_snapshot_guard.py::SNAPSHOTS --
# keep the two in step.
SNAPSHOT_DATA_DATE = {
    "2026-04-12": "2026-04-08",
    "2026-08-30": "2026-08-27",
}

# --- matching helpers, lifted verbatim from scripts/add_topic_autodiscover.py --
# That module indexes AACT at import time and reassigns sys.stdout, so it cannot
# be imported; these are copied rather than re-derived, so the matcher that was
# validated at 90% recall against 13 published meta-analyses is the one running.
DRUG_SYNS = {
    "tofacitinib": ["cp-690,550", "cp 690,550", "cp690550"],
    "olaparib": ["azd2281", "azd 2281"],
    "baricitinib": ["ly3009104", "incb028050"],
    "upadacitinib": ["abt-494"],
    "filgotinib": ["glpg0634"],
}
COND_SYNS = {
    "hiv": ["human immunodeficiency virus"],
    # Added 2026-09-02 because the APIXABAN_VTE positive controls FAILED.
    # AMPLIFY (NCT00643201) and AMPLIFY-EXT (NCT00633893) -- the two pivotal
    # apixaban VTE trials -- are registered under the condition "Venous
    # Thrombosis". Token-subset matching cannot bridge that:
    # {venous, thromboembolism} is not a subset of {venous, thrombosis}.
    # Without the control this topic would have reported 56 included trials
    # while silently missing the two that matter most, and it would have looked
    # entirely healthy. This is why a filter's zero is not trusted until a case
    # that MUST match has been shown to match.
    "venous thromboembolism": ["venous thrombosis", "venous thrombo embolism"],
    "deep vein thrombosis": ["deep venous thrombosis"],
    "pulmonary embolism": ["pulmonary thromboembolism"],
}
LATE_PHASES = frozenset({"phase3", "phase4", "phase2/phase3"})


def _norm(s):
    """Lowercase; hyphen/comma/slash -> space; collapse whitespace."""
    return re.sub(r"\s+", " ", re.sub(r"[-,/]", " ", s.lower())).strip()


def _expand_syns(patterns, synmap):
    out = []
    for p in patterns:
        out.append(p)
        if synmap:
            out.extend(synmap.get(p, []))
    return out


def _match_blob(patterns, blob, token_subset=False, synmap=None):
    """True if any (synonym-expanded, normalized) pattern matches `blob`.
    token_subset=True also matches when a pattern's word tokens are a subset of
    the blob's tokens (MeSH inversion). Use token_subset ONLY for conditions."""
    nblob = _norm(blob)
    ntokens = set(nblob.split())
    for p in _expand_syns(patterns, synmap):
        np = _norm(p)
        if not np:
            continue
        if np in nblob:
            return True
        if token_subset:
            pt = set(np.split())
            if pt and pt <= ntokens:
                return True
    return False


# --- eligibility filter, declared as data so the search record can quote it ---
ELIGIBILITY = {
    "version": "1.0",
    "clauses": [
        {"id": "F1_intervention",
         "field": "interventions.name",
         "rule": "synonym-expanded, punctuation-normalized substring match "
                 "against any declared drug pattern"},
        {"id": "F2_condition",
         "field": "conditions.name",
         "rule": "synonym-expanded substring OR token-subset match (MeSH "
                 "inversion) against any declared condition pattern"},
        {"id": "F3_interventional",
         "field": "studies.study_type",
         "rule": "EXCLUDE when study_type is present and does not start with "
                 "'interv'. Blank/unknown is KEPT, not dropped -- a missing "
                 "field is not an observational study."},
        {"id": "F4_randomised",
         "field": "designs.allocation",
         "rule": "EXCLUDE when allocation is present and starts with "
                 "'Non-Random'. Blank is KEPT."},
    ],
    "ranking": "pivotal_score DESC (late-phase +2, registry results posted +1), "
               "then enrollment DESC, then nct_id ASC (total order; no ties)",
    "truncation": "NONE. The full eligible set is written to the ledger. Any cap "
                  "applied downstream must be recorded there, by name.",
    "not_an_eligibility_criterion": [
        "registry_results_posted -- a trial with no POSTED registry results may "
        "still have a full primary journal publication. Registry results and "
        "journal publication are different things. This field RANKS candidates; "
        "it never excludes one.",
    ],
}

# A filter is not trusted until a case that MUST match has been shown to match.
# Each entry: topic stem -> NCTs the published literature places squarely inside
# that topic, so a filter returning zero for them is broken, not empty.
# These are anchored to registry ids, which are immutable, rather than to any
# live artefact of ours that a later fix could quietly retire.
POSITIVE_CONTROLS = {
    "SGLT2_HF": ["NCT03036124", "NCT03057977", "NCT03057951",
                 "NCT03619213", "NCT03521934"],
    "FINERENONE_CKD": ["NCT02540993", "NCT02545049"],
    "APIXABAN_VTE": ["NCT00643201", "NCT00633893"],
}

TOPICS = {
    "SGLT2_HF": {
        "name": "SGLT2 inhibitors in heart failure",
        "drug_patterns": ["dapagliflozin", "empagliflozin", "sotagliflozin",
                          "canagliflozin", "ertugliflozin"],
        "condition_patterns": ["heart failure"],
    },
    "FINERENONE_CKD": {
        "name": "Finerenone in chronic kidney disease",
        "drug_patterns": ["finerenone", "bay 94-8862"],
        "condition_patterns": ["chronic kidney", "diabetic nephropathy",
                               "diabetic kidney"],
    },
    "APIXABAN_VTE": {
        "name": "Apixaban for venous thromboembolism",
        "drug_patterns": ["apixaban", "bms-562247"],
        "condition_patterns": ["venous thromboembolism", "deep vein thrombosis",
                               "pulmonary embolism"],
    },
}


def resolve_snapshot(root: Path, folder=None):
    """Return (folder, data_date). Refuses a folder whose data date has never
    been measured rather than falling back to the folder name."""
    if not root.exists():
        raise SystemExit(
            "NOT_FOUND: AACT root %s does not resolve. This is NOT_FOUND, never "
            "ABSENT -- set AACT_ROOT rather than concluding we have no registry "
            "snapshot." % root)
    if folder is None:
        known = sorted(d.name for d in root.iterdir()
                       if d.is_dir() and d.name in SNAPSHOT_DATA_DATE)
        if not known:
            raise SystemExit("NOT_FOUND: no snapshot under %s has a measured "
                             "data date. Measure it first." % root)
        # supersession is by DATA date, not by folder name
        folder = max(known, key=lambda f: SNAPSHOT_DATA_DATE[f])
    if folder not in SNAPSHOT_DATA_DATE:
        raise SystemExit(
            "REFUSED: snapshot folder %r has no measured data date. Its folder "
            "name is a label, not a fact. Measure "
            "max(last_update_submitted_qc_date) and add it to "
            "SNAPSHOT_DATA_DATE before querying it." % folder)
    return folder, SNAPSHOT_DATA_DATE[folder]


def build_index(snap: Path, verbose=True):
    """Stream the AACT tables we filter on. Returns a dict of maps."""
    def log(m):
        if verbose:
            print(m, file=sys.stderr, flush=True)

    intv = defaultdict(list)
    log("  indexing interventions.txt ...")
    with open(snap / "interventions.txt", encoding="utf-8", errors="replace") as f:
        for row in csv.DictReader(f, delimiter="|"):
            nct = (row.get("nct_id") or "").strip().upper()
            if nct:
                intv[nct].append(row.get("name") or "")

    cond = defaultdict(list)
    log("  indexing conditions.txt ...")
    with open(snap / "conditions.txt", encoding="utf-8", errors="replace") as f:
        for row in csv.DictReader(f, delimiter="|"):
            nct = (row.get("nct_id") or "").strip().upper()
            if nct:
                cond[nct].append(row.get("name") or "")

    stype, enroll, phase, posted, title = {}, {}, {}, {}, {}
    log("  indexing studies.txt ...")
    with open(snap / "studies.txt", encoding="utf-8", errors="replace") as f:
        for row in csv.DictReader(f, delimiter="|"):
            nct = (row.get("nct_id") or "").strip().upper()
            if not nct:
                continue
            stype[nct] = (row.get("study_type") or "").strip().lower()
            phase[nct] = _norm(row.get("phase") or "").replace(" ", "")
            title[nct] = (row.get("brief_title") or "").strip()
            try:
                enroll[nct] = int(float(row.get("enrollment") or 0))
            except (TypeError, ValueError):
                enroll[nct] = 0
            # Registry results EXIST iff a results date is recorded. This is
            # registry posting only and is used for RANKING, never exclusion.
            posted[nct] = bool((row.get("results_first_submitted_date") or "").strip())

    alloc = {}
    dpath = snap / "designs.txt"
    if dpath.exists():
        log("  indexing designs.txt ...")
        with open(dpath, encoding="utf-8", errors="replace") as f:
            for row in csv.DictReader(f, delimiter="|"):
                nct = (row.get("nct_id") or "").strip().upper()
                if nct:
                    alloc[nct] = (row.get("allocation") or "").strip()
    else:
        log("  designs.txt NOT PRESENT -- F4_randomised cannot fire. This is "
            "NOT_FOUND, not 'all trials are randomised'.")

    log("  indexed: %s NCT with interventions, %s studies" % (f"{len(intv):,}", f"{len(stype):,}"))
    return dict(intv=intv, cond=cond, stype=stype, enroll=enroll, phase=phase,
                posted=posted, title=title, alloc=alloc,
                _designs_present=dpath.exists())


def screen_topic(stem, spec, idx):
    """Enumerate + screen. Returns (search_record, ledger).

    The denominator is len(ledger). Every NCT that passed the intervention
    clause appears in the ledger with a verdict -- excluded candidates are
    RECORDED, not dropped, because a count that silently loses its rejects is a
    reach figure wearing a coverage figure's clothes.
    """
    drugs = [d.lower() for d in spec["drug_patterns"]]
    conds = [c.lower() for c in spec["condition_patterns"]]

    ledger = []
    # sorted() -> deterministic iteration. Establishes STABILITY, not correctness.
    for nct in sorted(idx["intv"]):
        blob = " | ".join(idx["intv"][nct])
        if not _match_blob(drugs, blob, token_subset=False, synmap=DRUG_SYNS):
            continue  # F1 fail: never a candidate, so not a screened exclusion

        cond_blob = " | ".join(idx["cond"].get(nct, []))
        row = {
            "nct_id": nct,
            "brief_title": idx["title"].get(nct, ""),
            "study_type": idx["stype"].get(nct, ""),
            "phase": idx["phase"].get(nct, ""),
            "enrollment": idx["enroll"].get(nct, 0),
            "allocation": idx["alloc"].get(nct, ""),
            "registry_results_posted": idx["posted"].get(nct, False),
        }

        if not _match_blob(conds, cond_blob, token_subset=True, synmap=COND_SYNS):
            row["decision"] = "EXCLUDE"
            row["reason_code"] = "F2_condition"
            row["reason"] = ("conditions %r match no declared condition pattern %s"
                             % (cond_blob[:120], conds))
            ledger.append(row)
            continue

        st = row["study_type"]
        if st and not st.startswith("interv"):
            row["decision"] = "EXCLUDE"
            row["reason_code"] = "F3_interventional"
            row["reason"] = "study_type=%r is not interventional" % st
            ledger.append(row)
            continue

        al = row["allocation"]
        if al and al.lower().startswith("non-random"):
            row["decision"] = "EXCLUDE"
            row["reason_code"] = "F4_randomised"
            row["reason"] = "allocation=%r" % al
            ledger.append(row)
            continue

        row["decision"] = "INCLUDE"
        row["reason_code"] = "eligible"
        row["reason"] = "matched all declared clauses"
        row["pivotal_score"] = ((2 if row["phase"] in LATE_PHASES else 0)
                                + (1 if row["registry_results_posted"] else 0))
        ledger.append(row)

    ledger.sort(key=lambda r: (r["decision"] != "INCLUDE",
                               -r.get("pivotal_score", 0),
                               -r["enrollment"], r["nct_id"]))

    included = [r for r in ledger if r["decision"] == "INCLUDE"]
    by_reason = defaultdict(int)
    for r in ledger:
        by_reason[r["reason_code"]] += 1

    record = {
        "topic_stem": stem,
        "topic_name": spec["name"],
        "source": "AACT (ClinicalTrials.gov bulk export), local snapshot",
        "snapshot_folder": idx["_snapshot_folder"],
        "snapshot_data_date": idx["_snapshot_data_date"],
        "snapshot_data_date_note": (
            "Measured as max(last_update_submitted_qc_date) in studies.txt. The "
            "folder name overstates this by days; a trial that posted results "
            "inside that window reads as silent here."),
        "executed_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "query_as_run": {
            "drug_patterns": drugs,
            "condition_patterns": conds,
            "drug_synonyms_expanded": {d: DRUG_SYNS[d] for d in drugs if d in DRUG_SYNS},
            "condition_synonyms_expanded": {c: COND_SYNS[c] for c in conds if c in COND_SYNS},
            "eligibility": ELIGIBILITY,
            "designs_table_present": idx.get("_designs_present"),
        },
        "resolved_counts": {
            "candidates_returned": len(ledger),
            "included": len(included),
            "excluded": len(ledger) - len(included),
            "excluded_by_reason": dict(sorted(by_reason.items())),
        },
        "determinism": {
            "property_established": "STABILITY",
            "how": "every iteration is sorted(); the ordering key ends in nct_id "
                   "so the sort is a total order with no hash-order ties",
            "property_NOT_established": "CORRECTNESS -- see positive_controls",
        },
    }
    return record, ledger


def check_controls(stem, ledger):
    """Point the filter at cases that MUST match before trusting its zero."""
    controls = POSITIVE_CONTROLS.get(stem)
    if not controls:
        return {"status": "NO_CONTROL_DECLARED",
                "note": "a zero from this topic is NOT_FOUND, not ABSENT"}
    seen = {r["nct_id"]: r for r in ledger}
    out = []
    for nct in controls:
        r = seen.get(nct)
        out.append({"nct_id": nct,
                    "in_ledger": r is not None,
                    "decision": r["decision"] if r else None,
                    "reason_code": r["reason_code"] if r else "NOT_RETURNED"})
    passed = sum(1 for c in out if c["decision"] == "INCLUDE")
    return {"status": "PASS" if passed == len(controls) else "FAIL",
            "passed": passed, "of": len(controls), "controls": out}


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--topics", nargs="*", default=sorted(TOPICS))
    ap.add_argument("--snapshot", default=None,
                    help="AACT folder name; default = latest by measured DATA date")
    ap.add_argument("--out", default=str(HERE / "outputs" / "registry_adapter"))
    args = ap.parse_args()

    folder, data_date = resolve_snapshot(AACT_ROOT, args.snapshot)
    snap = AACT_ROOT / folder
    print("snapshot folder    : %s" % folder, file=sys.stderr)
    print("snapshot data date : %s  (NOT the folder name)" % data_date, file=sys.stderr)

    idx = build_index(snap)
    idx["_snapshot_folder"] = folder
    idx["_snapshot_data_date"] = data_date

    outdir = Path(args.out)
    outdir.mkdir(parents=True, exist_ok=True)

    summary = []
    for stem in args.topics:
        if stem not in TOPICS:
            print("  ! unknown topic %s" % stem, file=sys.stderr)
            continue
        record, ledger = screen_topic(stem, TOPICS[stem], idx)
        record["positive_controls"] = check_controls(stem, ledger)

        (outdir / ("%s.search_record.json" % stem)).write_text(
            json.dumps(record, indent=2), encoding="utf-8")
        (outdir / ("%s.screening_ledger.json" % stem)).write_text(
            json.dumps({"topic_stem": stem,
                        "snapshot_folder": folder,
                        "snapshot_data_date": data_date,
                        "denominator": len(ledger),
                        "candidates": ledger}, indent=2), encoding="utf-8")

        rc = record["resolved_counts"]
        summary.append({"topic": stem,
                        "returned": rc["candidates_returned"],
                        "included": rc["included"],
                        "controls": record["positive_controls"]["status"]})
        print("  %-16s returned=%5d included=%4d controls=%s"
              % (stem, rc["candidates_returned"], rc["included"],
                 record["positive_controls"]["status"]), file=sys.stderr)

    (outdir / "_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
