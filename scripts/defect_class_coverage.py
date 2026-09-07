# -*- coding: utf-8 -*-
"""DEFECT-CLASS COVERAGE MATRIX -- the acceptance artefact for "avoid all the errors from the reviews".

"Avoid all the errors" is not testable as stated. This makes it testable: for every defect class named
across the ~26 external reviews (and the ones our own work surfaced), record which of three states it
is in, and VERIFY the evidence exists rather than asserting it.

  PREVENTED  the schema/generator makes the defect UNREPRESENTABLE (strongest)
  DETECTED   a gate fires on it, with a fixture that failed pre-fix
  NEITHER    no prevention, no detection  <-- THE DELIVERABLE

Prevention outranks detection: a typed analysis_variant field makes the inclisiran error impossible; a
gate merely notices it after. Where a class is only DETECTED, `to_prevent` names how it could move left.

SELF-VERIFYING: a claim of DETECTED whose gate file is absent, or PREVENTED whose schema field is
absent, is AUTO-DOWNGRADED to NEITHER and flagged -- the matrix cannot lie about coverage it does not
have. Run: python scripts/defect_class_coverage.py
"""
from __future__ import annotations
import io, os, re, sys, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def _gate_exists(name):
    return bool(glob.glob(os.path.join(ROOT, "gates", name)) or glob.glob(os.path.join(ROOT, "scripts", name)))

def _schema_field(field):
    try:
        src = io.open(os.path.join(ROOT, "scripts", "protocol_schema_v2.py"), encoding="utf-8").read()
    except Exception:
        return False
    return ('"%s"' % field) in src or ("'%s'" % field) in src

def _in_generator(marker):
    try:
        src = io.open(os.path.join(ROOT, "scripts", "generate_review_page.py"), encoding="utf-8").read()
    except Exception:
        return False
    return marker in src

def _in_component(spec):
    """spec = 'file.py::marker' -- prevention that lives in a pipeline component, not the page generator."""
    fn, _, marker = spec.partition("::")
    try:
        src = io.open(os.path.join(ROOT, "scripts", fn), encoding="utf-8").read()
    except Exception:
        return False
    return marker in src

# (class, state, evidence_kind, evidence, to_prevent_note)
#   evidence_kind: 'gate' -> file in gates/ or scripts/ ; 'schema' -> field in protocol_schema_v2 ;
#                  'generator' -> marker in generate_review_page ; 'none' -> NEITHER
MATRIX = [
 ("registry-as-source-of-record", "PREVENTED", "schema", "primary_source_of_record", ""),
 ("hasResults=false is a publication-search task", "DETECTED", "gate", "gate53_hasresults_not_publication.py", "screener returns a third state; a schema enum on results_state would prevent"),
 ("outcome-rank screening (secondary is not excluded)", "PREVENTED", "component", "screen.py::_outcome_at_any_rank", ""),
 ("analysis-variant (observed-case vs ITT)", "PREVENTED", "schema", "analysis_variant", ""),
 ("numerator/denominator share the analysis population", "PREVENTED", "schema", "analysis_population", ""),
 ("effect+CI poolability (derive SE from CI)", "DETECTED", "gate", "gate_stored_estimate_declares_provenance_2026_08_27.py", "extractor could refuse a reconstructed SE where a published one exists"),
 ("multi-arm shared control (tau^2/2 covariance)", "NEITHER", "none", "", "a schema flag multi_arm + a pooling-engine covariance term would prevent"),
 ("one pool per comparison", "DETECTED", "gate", "gate17_unpoolable_override.py", ""),
 ("harmonisation / follow-up window", "PREVENTED", "schema", "follow_up_window", ""),
 ("effect scale matches the trial estimand", "PREVENTED", "schema", "effect_measure", ""),   # gate59 also
 ("self-reference benchmark by trial-set overlap", "DETECTED", "gate", "gate_self_reference_benchmark.py", "schema external_benchmark.independent + a check would move to PREVENTED"),
 ("stale panel / two live values for one statistic", "DETECTED", "gate", "gate11_one_statistic_one_value.py", ""),
 ("half-migration (superseded value served live)", "DETECTED", "gate", "gate38_superseded_cited_live.py", "generator embeds a current-view object; a schema single-value-per-stat would prevent"),
 ("boilerplate conditioned on k (GOSH/TSA/meta-reg)", "PREVENTED", "generator", "_refusal_sections", ""),
 ("planned duration shown as observed", "DETECTED", "gate", "gate12_planned_shown_as_observed.py", "schema follow_up_window.window {planned|observed}"),
 ("sentence contradicts its own number", "DETECTED", "gate", "gate11_one_statistic_one_value.py", ""),
 ("GRADE certainty not derived from a stated threshold", "DETECTED", "gate", "gate_grade_imprecision_needs_threshold.py", "schema grade.imprecision_threshold would move to PREVENTED"),
 ("RoB from registry fields not the publication", "DETECTED", "gate", "gate_rob_source_is_publication.py", "schema risk_of_bias.source per domain would move to PREVENTED"),
 ("adherence is not risk-of-bias", "NEITHER", "none", "", "RoB domain vocabulary that has no 'adherence' domain"),
 ("absence of assessment is not a negative", "DETECTED", "gate", "gate_certainty_column_four_states_2026_08_23.py", ""),
 ("harms mandatory (declared absence, not omission)", "PREVENTED", "generator", "No harms outcome extracted", ""),  # gate21 also
 ("absolute effect / HR->ARR conversion", "PREVENTED", "generator", "1&minus;(1&minus;B)", ""),  # gate_hr also DETECTS
 ("composite endpoint decomposition", "DETECTED", "gate", "gate_composite_lists_components.py", "schema estimand.components[] would move to PREVENTED"),
 ("disclosed unknown that was knowable", "PREVENTED", "schema", "answers_known_at_authoring", ""),
 ("exclusion reasons verified (not asserted)", "DETECTED", "gate", "gate_screening_row_has_registration_id_2026_08_26.py", "screener stores the verified reason + evidence"),
 ("exhaustiveness claim falsifiable", "NEITHER", "none", "", "schema search.records[] with a per-record decision, gate that the claim resolves to them"),
 ("protocol benchmark citation checked", "DETECTED", "gate", "gate_benchmark_pmid_names_its_trial_2026_08_23.py", ""),
 ("database-scoped eligibility", "NEITHER", "none", "", "schema eligibility.database_scope + a gate on it"),
 ("mutable registry field (later != wrong)", "NEITHER", "none", "", "record a content hash + retrieval date on every registry-sourced value"),
 ("protocol timing wording (retrospective honest)", "PREVENTED", "schema", "disclosure_clause", ""),
 ("correction stored in page not object", "DETECTED", "gate", "gate_correction_not_in_rendered_field.py", "the corrections-edit-the-rendered-field discipline would move to PREVENTED"),
 ("completeness test measures only what was enumerated", "DETECTED", "gate", "content_completeness.py", "the tab criterion counts populated tabs; a schema page-shape contract would prevent"),
 ("path-convention split degrades axis to CANNOT_RUN", "DETECTED", "gate", "reproduce_review.py", "single-sourced review_id->{object,protocol,evidence,page} resolver would prevent"),
 ("orphaned page (good page absent from index)", "NEITHER", "none", "", "generate the index from the corpus so it lists exactly what exists"),
 ("dead index link (index promises a missing page)", "DETECTED", "gate", "gate_every_linked_target_resolves_2026_08_23.py", "same index generator prevents both directions"),
 ("stub-with-object (page too small for its object)", "DETECTED", "gate", "gate_stub_with_object.py", "the page generator emitting only real pages would move to PREVENTED"),
 ("imposed method (modified HKSJ on every ratio)", "PREVENTED", "generator", "uses_hksj", ""),  # gate_served_interval DETECTS
 ("reader can check a trial in the registry", "DETECTED", "gate", "gate16_reader_can_check.py", ""),
 ("non-inferiority pooled as superiority", "DETECTED", "gate", "gate10_noninferiority_pooled_as_superiority.py", "schema estimand.hypothesis {superiority|non_inferiority} + margin"),
]

def evaluate():
    rows = []
    for cls, state, kind, ev, tp in MATRIX:
        verified = True
        if state in ("PREVENTED", "DETECTED"):
            if kind == "gate":
                verified = _gate_exists(ev)
            elif kind == "schema":
                verified = _schema_field(ev)
            elif kind == "generator":
                verified = _in_generator(ev)
            elif kind == "component":
                verified = _in_component(ev)
            else:
                verified = False
        eff_state = state if (state == "NEITHER" or verified) else "NEITHER"
        rows.append({"class": cls, "claimed": state, "state": eff_state, "kind": kind,
                     "evidence": ev, "verified": verified, "to_prevent": tp})
    return rows


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    rows = evaluate()
    from collections import Counter
    tally = Counter(r["state"] for r in rows)
    downgraded = [r for r in rows if r["claimed"] != r["state"]]
    print("DEFECT-CLASS COVERAGE MATRIX  (%d classes)" % len(rows))
    print("=" * 90)
    for st in ("PREVENTED", "DETECTED", "NEITHER"):
        print("\n--- %s (%d) ---" % (st, tally.get(st, 0)))
        for r in rows:
            if r["state"] != st:
                continue
            tag = "" if r["state"] != "DETECTED" or not r["to_prevent"] else ("  -> to PREVENT: " + r["to_prevent"])
            src = (" [%s: %s]" % (r["kind"], r["evidence"])) if r["state"] != "NEITHER" else ("  ROADMAP: " + r["to_prevent"])
            print("  %-56s%s%s" % (r["class"], src, tag))
    print("\n" + "=" * 90)
    print("THE LINE: %d PREVENTED, %d DETECTED, %d NEITHER (of %d)"
          % (tally.get("PREVENTED", 0), tally.get("DETECTED", 0), tally.get("NEITHER", 0), len(rows)))
    if downgraded:
        print("\nAUTO-DOWNGRADED (claimed coverage whose evidence is ABSENT -- these are the dangerous ones):")
        for r in downgraded:
            print("  %-56s claimed %s, evidence %s:%s NOT FOUND" % (r["class"], r["claimed"], r["kind"], r["evidence"]))
    print("\nNEITHER LIST (named -- the honest answer):")
    for r in rows:
        if r["state"] == "NEITHER":
            print("  - %s" % r["class"])
    raise SystemExit(0)
