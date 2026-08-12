#!/usr/bin/env python3
"""Adapt diagnostic-accuracy (TP/FP/FN/TN) datasets into harness cells.

Why this exists
---------------
The count harness was built for arm-pair intervention data. Diagnostic-accuracy
studies store a 2x2 of a different shape, but the discipline is identical: a count
is either read from the source or it is not, and a count reconstructed from a
published sensitivity/specificity is not read.

Mapping (lossless for the checks that matter):
    stratum "reference-positive"  -> events = TP, analysed = TP + FN
    stratum "reference-negative"  -> events = FP, analysed = FP + TN

Each stratum is a genuine denominator the study reports, so CHK002, CHK005,
CHK006, CHK008, CHK012 and CHK016 all apply unchanged.

Run from the directory holding the *_trials.json files:
    python adapt_dta_to_cells.py <corpus_dir> <out.json>
"""
import json
import os
import sys

DATASETS = [
    ("covid_antigen_trials.json", "SARS-CoV-2 rapid antigen test"),
    ("ddimer_pe_trials.json", "D-dimer for pulmonary embolism"),
    ("genexpert_ultra_trials.json", "GeneXpert MTB/RIF Ultra"),
    ("mpmri_prostate_trials.json", "mpMRI of the prostate"),
    ("ptau217_ad_trials.json", "Plasma p-tau217"),
    ("hsctn_nstemi_trials.json", "hs-cTn 0/1h algorithm"),
]

# provenance string -> (construction, note)
DERIVED_MARKERS = ("back_comput", "back_compute", "derived", "reconstruct", "relabel")


def _determinacy(r):
    """Determined only if BOTH: group sizes reported AND the rounding interval pins one integer."""
    import sys as _s
    import os as _o
    _s.path.insert(0, _o.path.dirname(_o.path.abspath(__file__)))
    from audit_dta_backcomputation import classify as _reported
    from determinacy_test import compatible_counts, printed_decimals
    tp, fp, fn, tn = r.get("TP"), r.get("FP"), r.get("FN"), r.get("TN")
    if None in (tp, fp, fn, tn):
        return False, {}
    groups_reported = _reported(r)["status"] == "DETERMINED"
    q = r.get("raw_quote") or ""
    n_dis, n_non = tp + fn, fp + tn
    sens, spec = 100.0 * tp / n_dis, 100.0 * tn / n_non
    ds, dp = printed_decimals(q, sens), printed_decimals(q, spec)
    pinned = (ds is not None and len(compatible_counts(sens, n_dis, ds)) == 1 and
              dp is not None and len(compatible_counts(spec, n_non, dp)) == 1)
    return (groups_reported and pinned), dict(sens=sens, spec=spec, n_dis=n_dis, n_non=n_non,
                                              ds=ds, dp=dp)


def classify(prov: str, r=None):
    """Return (construction, note) under the 2026-08-12 ruling.

    Determined reconstruction is permitted; underdetermined reconstruction is not.
    The distinction is tested per row, not inferred from the presence of a percentage.
    """
    p = (prov or "").lower()
    if not p:
        return None, "provenance field empty"
    if any(m in p for m in DERIVED_MARKERS):
        det, _ = _determinacy(r) if r is not None else (False, {})
        if det:
            return "derived_determined", (f"corpus provenance='{prov}'; group sizes reported and "
                                          "the rounding interval pins a unique integer")
        return "derived_underdetermined", (f"corpus provenance='{prov}'; reconstruction required an "
                                           "assumption (group size imputed and/or the rounding "
                                           "interval admits more than one integer)")
    return "read", f"corpus provenance='{prov}'"


def main(corpus_dir: str, out_path: str) -> int:
    cells = []
    for fname, test_label in DATASETS:
        path = os.path.join(corpus_dir, fname)
        if not os.path.exists(path):
            continue
        with open(path, "r", encoding="utf-8") as fh:
            d = json.load(fh)
        for tier_key, rows in d.items():
            if not (isinstance(rows, list) and rows and isinstance(rows[0], dict)
                    and "TP" in rows[0]):
                continue
            for r in rows:
                tp, fp, fn, tn = (r.get("TP"), r.get("FP"), r.get("FN"), r.get("TN"))
                construction, cnote = classify(r.get("provenance"), r)
                det_meta = _determinacy(r)[1]
                study = r.get("studlab") or "unnamed"
                pmid, doi = r.get("pmid"), r.get("ref_doi")
                srcs = []
                if pmid or doi:
                    srcs.append({"tier": "T1",
                                 "pointer": f"{fname}:{tier_key} — {r.get('provenance')}"
                                            f" | pmid {pmid} | doi {doi}"})
                caveats = r.get("data_caveats") or []
                for stratum, ev, an in (
                        ("reference-positive", tp, (tp + fn) if None not in (tp, fn) else None),
                        ("reference-negative", fp, (fp + tn) if None not in (fp, tn) else None)):
                    # One registration can carry several index-test evaluations
                    # (e.g. the APACE cohort, or clinician- vs self-collected swabs).
                    # The unit of extraction is the evaluation, so the key must include
                    # the study label; the registry id stays in `notes`.
                    reg = r.get("nctid") or (f"PMID:{pmid}" if pmid else None)
                    if construction == "derived_determined":
                        stat = det_meta["sens"] if stratum == "reference-positive" else \
                            (100.0 - det_meta["spec"])
                        gn = det_meta["n_dis"] if stratum == "reference-positive" else det_meta["n_non"]
                        deriv_inputs = {"rate_pct": round(stat, 4), "group_n": gn}
                        deriv_formula = ("events = round(group_n * rate_pct / 100); rate_pct is "
                                         + ("sensitivity" if stratum == "reference-positive"
                                            else "1 - specificity")
                                         + " as printed; determinacy verified by rounding-interval test")
                        prov = "derived_determined"
                    else:
                        deriv_inputs = deriv_formula = None
                        prov = "read"
                    cell = dict(
                        trial=f"{study}", nct=f"{reg or 'UNREGISTERED'} :: {study}",
                        arm=stratum, outcome="test_positive",
                        events=ev, analysed=an, randomised=an,
                        # population_label is the tier, NOT the stratum: the two strata
                        # are the two "arms" of the 2x2, so CHK012 must see them paired.
                        population_label=tier_key,
                        provenance=prov,
                        construction=construction,
                        derivation_inputs=deriv_inputs,
                        derivation_formula=deriv_formula,
                        sources=srcs,
                        identifier_provenance="lookup" if reg else None,
                        registry_units="participants",
                        notes=f"{test_label}. registry_id={reg}. {cnote}."
                              + (f" caveats: {','.join(caveats)}" if caveats else ""),
                    )
                    if ev is None:
                        cell["not_recovered_reason"] = (
                            "2x2 cell empty in the corpus dataset"
                            + ("" if r.get("provenance") else "; provenance field also empty"))
                    cells.append(cell)
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump({"cells": cells}, fh, indent=1)
    print(f"wrote {len(cells)} cells from {len(DATASETS)} diagnostic-accuracy datasets")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__)
        raise SystemExit(2)
    raise SystemExit(main(sys.argv[1], sys.argv[2]))
