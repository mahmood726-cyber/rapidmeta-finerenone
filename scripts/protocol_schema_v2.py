# -*- coding: utf-8 -*-
"""Advanced, machine-readable meta-analysis protocol: a typed schema the gates read.

Every field exists because a real defect occurred without it (19 external reviews). A field that
is prose documents intent; a field that is typed becomes a gate input and the error becomes
impossible. validate() REFUSES a protocol that reproduces a known defect, and _selftest() proves
each refusal can fire (a gate that only passes proves nothing).

Written here rather than delegated after Codex produced exit 0 with zero artefacts three times.
"""
from __future__ import annotations
import io, re, sys

# ---- typed enumerations ------------------------------------------------------------------
ANALYSIS_POPULATION = ("mITT", "ITT", "per_protocol", "as_randomised")
ANALYSIS_VARIANT = ("ITT_IMPUTED", "OBSERVED_CASE", "COMPLETER")       # inclisiran -53.97 vs -50.54
EFFECT_MEASURE = ("log_HR", "log_RR", "log_OR", "MD", "RD")            # CAB-LA HR-vs-RR; never "log effect scale"
COMPARATOR_KIND = ("placebo", "active", "deferred_active")            # PLATFORM was placebo during PCI
POOLABLE_INPUT = ("two_by_two_counts", "effect_ci_measure")           # cangrelor/bococizumab: effect+CI IS poolable
ROB2_SOURCE = ("manuscript", "SAP", "regulatory")                     # never registry_design
SOURCE_HIERARCHY = ("primary_publication", "supplement", "regulatory", "registry")  # registry never primary

_DATABASE_NAMES = re.compile(r"clinicaltrials\.gov|ct\.gov|\bAACT\b|isrctn|chictr|"
                             r"registered (?:on|in) (?:a )?(?:trial )?registr", re.I)  # gate 51
# Outcome-as-ELIGIBILITY = the criterion makes admission DEPEND on the trial reporting/measuring an
# outcome (the Cochrane-forbidden mechanism). It must NOT fire on the bare word 'outcome' in a
# DESIGN descriptor -- 'cardiovascular outcome trial' is a trial TYPE, not a screen on an outcome.
# (This false-refusal was caught by the SGLT2 loop's first pass; a schema that false-refuses is as
# dangerous as one that false-passes, because it trains us to loosen a real refusal.)
_OUTCOME_WORDS = re.compile(
    r"(report|measur|provid|record|carr|yield|includ|present)\w*\s+(?:[a-z]+\s+){0,4}"
    r"(outcome|endpoint|mortality|\bMACE\b|hospitali[sz]|primary result|response rate|hazard ratio|\bHR\b)"
    r"|(outcome|endpoint|result|\bHR\b)\s+(?:is\s+|be\s+|were\s+|are\s+)?"
    r"(available|reported|present|extractable|measured|recorded)"
    r"|exclud\w*\s+on\s+(?:the\s+)?outcome", re.I)


def template(review_id):
    return {
        "review_id": review_id,
        "estimands": [{"outcome": None, "timepoint": None, "analysis_population": None,
                       "missing_data_model": None, "analysis_variant": None, "effect_measure": None}],
        "source_hierarchy": list(SOURCE_HIERARCHY),
        "primary_source_of_record": "primary_publication",
        "poolable_input_types": list(POOLABLE_INPUT),
        "harmonisation_rule": {"on_differing_definitions": "declare_harmonised",
                               "harmonised_endpoint": None, "source": None},
        "eligibility": {"population": None, "intervention": None, "comparator": None,
                        "comparator_kind": None, "design": None, "reproduces_exclusions": False},
        "statistics": {"tau2_estimator": None, "small_k_ci_rule": None,
                       "disclosure_clause": {"answers_known_at_authoring": False, "text": None},
                       "zero_cell_rule": {"double_zero_excluded_from_rr_or": True,
                                          "continuity_correct_double_zero": False}},
        "mandatory_outputs": {"absolute_effect": {"ARR": None, "NNT": None, "control_risk_source": None},
                              "harms": [], "rob2_source": None},
        "governance": {"authored_utc": None, "registering_commit_sha": None, "retrospective": True,
                       "prospective": False, "prospective_evidence": None,
                       "supersedes": None, "supersedes_why": None, "amendment_trail": [],
                       "method_declared_once": True, "freeze_date": None, "dated_content": []},
    }


def validate(p):
    e = []
    if not isinstance(p, dict):
        return False, ["not an object"]
    # ESTIMAND
    for i, es in enumerate(p.get("estimands") or []):
        if es.get("effect_measure") not in EFFECT_MEASURE:
            e.append("estimand[%d].effect_measure %r not in %s (the CAB-LA HR-vs-RR class)"
                     % (i, es.get("effect_measure"), EFFECT_MEASURE))
        if es.get("analysis_variant") not in ANALYSIS_VARIANT:
            e.append("estimand[%d].analysis_variant missing -- %s required (inclisiran -53.97 vs -50.54)"
                     % (i, ANALYSIS_VARIANT))
        if es.get("analysis_population") not in ANALYSIS_POPULATION:
            e.append("estimand[%d].analysis_population %r not typed" % (i, es.get("analysis_population")))
    if not (p.get("estimands")):
        e.append("no estimand defined")
    # SOURCE HIERARCHY
    if p.get("primary_source_of_record") == "registry":
        e.append("registry named as primary_source_of_record -- registry is never primary (bempedoic)")
    # POOLABLE INPUTS
    pit = set(p.get("poolable_input_types") or [])
    if pit == {"two_by_two_counts"}:
        e.append("poolable_input_types is counts-only -- a published effect+CI is poolable (cangrelor/bococizumab)")
    # HARMONISATION
    hr = p.get("harmonisation_rule") or {}
    if hr.get("on_differing_definitions") not in ("declare_harmonised", "refuse"):
        e.append("harmonisation_rule.on_differing_definitions must be declare_harmonised|refuse")
    # ELIGIBILITY
    el = p.get("eligibility") or {}
    for f in ("population", "intervention", "comparator", "design"):
        val = el.get(f)
        if not val:
            e.append("eligibility.%s missing" % f)
        elif f != "comparator" and _OUTCOME_WORDS.search(str(val)):
            e.append("eligibility.%s screens on an OUTCOME (%r) -- outcomes are reporting-only"
                     % (f, _OUTCOME_WORDS.search(str(val)).group(0)))
        if val and _DATABASE_NAMES.search(str(val)):
            e.append("eligibility.%s is DATABASE-SCOPED (%r) -- 'registered in DB X' is geographic bias, "
                     "not a clinical criterion (gate 51, LEAP-China)"
                     % (f, _DATABASE_NAMES.search(str(val)).group(0)[:30]))
    if el.get("comparator") and el.get("comparator_kind") not in COMPARATOR_KIND:
        e.append("eligibility.comparator_kind must be one of %s, stated precisely (PLATFORM was placebo)" % (COMPARATOR_KIND,))
    # STATISTICS
    st = p.get("statistics") or {}
    zc = st.get("zero_cell_rule") or {}
    if zc.get("continuity_correct_double_zero"):
        e.append("zero_cell_rule permits continuity-correcting a double-zero -- forbidden (CLEAR Tranquility 0/181 vs 0/87)")
    # MANDATORY OUTPUTS
    mo = p.get("mandatory_outputs") or {}
    if mo.get("rob2_source") not in ROB2_SOURCE:
        e.append("mandatory_outputs.rob2_source must be %s, never registry_design" % (ROB2_SOURCE,))
    if not (mo.get("harms")):
        e.append("mandatory_outputs.harms empty -- named specific harms required, not 'adverse events'")
    # GOVERNANCE
    g = p.get("governance") or {}
    if g.get("prospective") and not g.get("prospective_evidence"):
        e.append("governance.prospective:true without prospective_evidence -- backdated prospectiveness refused")
    fz, dated = g.get("freeze_date"), g.get("dated_content") or []
    if fz and any(str(dc) > str(fz) for dc in dated):
        e.append("governance: content dated after freeze_date %s -- a document changed after freezing was never frozen (bempedoic v1.1)" % fz)
    return (not e), e


def _selftest():
    ok, rows = True, []

    def chk(name, cond):
        nonlocal ok
        ok &= bool(cond); rows.append((name, "OK" if cond else "*** FAIL ***"))

    good = template("demo")
    good["estimands"] = [{"outcome": "MACE", "timepoint": "median 40.6mo", "analysis_population": "ITT",
                          "missing_data_model": "multiple imputation, Rubin", "analysis_variant": "ITT_IMPUTED",
                          "effect_measure": "log_HR"}]
    good["eligibility"] = {"population": "adults with ASCVD", "intervention": "bempedoic acid",
                           "comparator": "placebo", "comparator_kind": "placebo",
                           "design": "randomised controlled trial", "reproduces_exclusions": True}
    good["statistics"]["tau2_estimator"] = "REML"; good["statistics"]["small_k_ci_rule"] = "HKSJ t_{k-1}, floor 1"
    good["mandatory_outputs"]["harms"] = ["new-onset diabetes", "myalgia"]
    good["mandatory_outputs"]["rob2_source"] = "manuscript"
    good["governance"]["authored_utc"] = "2026-09-06T00:00:00+00:00"
    okg, eg = validate(good)
    chk("a correct protocol validates", okg and not eg)

    def bad(mut):
        import copy
        b = copy.deepcopy(good); mut(b); return not validate(b)[0]

    chk("missing effect_measure refused", bad(lambda b: b["estimands"][0].__setitem__("effect_measure", None)))
    chk("vague 'log effect scale' refused", bad(lambda b: b["estimands"][0].__setitem__("effect_measure", "log effect scale")))
    chk("missing analysis_variant refused", bad(lambda b: b["estimands"][0].__setitem__("analysis_variant", None)))
    chk("registry as primary source refused", bad(lambda b: b.__setitem__("primary_source_of_record", "registry")))
    chk("counts-only poolable refused", bad(lambda b: b.__setitem__("poolable_input_types", ["two_by_two_counts"])))
    chk("outcome-as-eligibility refused", bad(lambda b: b["eligibility"].__setitem__("population", "adults reporting MACE")))
    chk("outcome-as-eligibility refused (excludes on outcome)", bad(lambda b: b["eligibility"].__setitem__("intervention", "the drug, excluded on outcome if the HR is not reported")))

    # PERMITTED-INPUT fixtures: the schema must NOT refuse these (caught by the SGLT2 loop).
    import copy
    def permits(mut):
        g = copy.deepcopy(good); mut(g); return validate(g)[0]
    chk("'cardiovascular outcome trial' design PERMITTED", permits(lambda b: b["eligibility"].__setitem__("design", "randomised, double-blind, placebo-controlled cardiovascular outcome trial")))
    chk("'reported an eligible dose' PERMITTED", permits(lambda b: b["eligibility"].__setitem__("population", "adults with an outcome-trial-eligible risk profile")))
    chk("database-scoped eligibility refused (gate 51)", bad(lambda b: b["eligibility"].__setitem__("population", "adults randomized in trials registered on ClinicalTrials.gov")))
    chk("continuity-correct double-zero refused", bad(lambda b: b["statistics"]["zero_cell_rule"].__setitem__("continuity_correct_double_zero", True)))
    chk("rob2 from registry refused", bad(lambda b: b["mandatory_outputs"].__setitem__("rob2_source", "registry_design")))
    chk("named harms required", bad(lambda b: b["mandatory_outputs"].__setitem__("harms", [])))
    chk("backdated prospectiveness refused", bad(lambda b: b["governance"].update({"prospective": True, "prospective_evidence": None})))
    chk("content after freeze refused", bad(lambda b: b["governance"].update({"freeze_date": "2026-04-19", "dated_content": ["2026-04-20"]})))
    return ok, rows


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    good, rows = _selftest()
    print("protocol_schema_v2 selftest")
    for n, v in rows:
        print("  %-52s %s" % (n, v))
    print("\n%s" % ("ALL PASS" if good else "FAILURES ABOVE"))
    raise SystemExit(0 if good else 1)
