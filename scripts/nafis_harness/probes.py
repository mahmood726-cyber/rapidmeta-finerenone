"""The twelve detectors, each pinned to a real incident from this project's record.

Every detector here is deterministic CPU. None makes a model call. None touches
the network. Each carries at least one fixture drawn from an incident that
actually happened, so that the fixture cannot be deleted as synthetic noise.

Mechanism -> detector map (see TAXONOMY.md for the full record):

  A. Dead-instrument negative      CHK001 retrieval-absence, CHK004 liveness
  B. Effect assumed from no error  CHK003 action-effect
  C. Match without a referent      CHK002 token-match, CHK006 identity-key
  D. Self-consistency as proof     CHK005 external-referent
  E. Absence asserted, not screened CHK007 absence-screen
  F. Frame over-claim              CHK008 frame-denominator
  G. Right number, wrong pool      CHK009 pool-identity
  H. Chain abandoned, called blocked CHK010 chain-exhaustion
  I. Correction less reliable than original CHK011 correction-burden
  J. Layer substitution            CHK012 delivery-vs-holdings (partial -- see blind spots)
  K. Field semantics assumed       CHK013 date-field
"""

from __future__ import annotations

import copy
from typing import Any, Mapping

from .check import Check, Fixture, Instrument
from .registry import Registry
from .verdict import Result, Verdict, make_fail, make_invalid, make_pass


def _mut(payload: Mapping[str, Any], **changes) -> dict:
    d = copy.deepcopy(dict(payload))
    d.update(changes)
    return d


def _deep(payload: Mapping[str, Any], path: list, value) -> dict:
    d = copy.deepcopy(dict(payload))
    cur = d
    for k in path[:-1]:
        cur = cur[k]
    cur[path[-1]] = value
    return d


# =============================================================================
# CHK001 -- an absence may only be reported from an instrument that saw
# =============================================================================
# Incident: a 429 rate-limit response read as "no record exists". Also the
# general form behind `has_results: false` vs "the endpoint refused us".

def _retrieval_absence(p: Mapping[str, Any]) -> Result:
    cid, inst = "CHK001_RETRIEVAL_ABSENCE", "http-retrieval"
    status = p.get("http_status")
    if status is None:
        return make_invalid(cid, inst, "no HTTP status recorded: cannot tell an "
                                       "empty result set from an unanswered request")
    if status != 200:
        return make_invalid(cid, inst,
                            f"transport returned {status}, not 200. A non-200 is a "
                            "statement about the request, not about the record. "
                            "Absence is unestablished.",
                            http_status=status, endpoint=p.get("endpoint"))
    n = p.get("result_count")
    if n is None:
        return make_invalid(cid, inst, "200 received but result_count not parsed")
    if n > 0:
        return make_fail(cid, inst,
                         f"absence claimed but {n} record(s) returned",
                         observed=f"HTTP 200 with result_count={n}",
                         locator=str(p.get("endpoint")),
                         opposite_would_be="the same 200 with an empty result set, "
                                           "which is the only shape that establishes "
                                           "absence",
                         result_count=n, endpoint=p.get("endpoint"))
    return make_pass(cid, inst,
                     observed=f"HTTP 200 with an empty result set at {p.get('endpoint')}",
                     locator=str(p.get("endpoint")),
                     opposite_would_be="the same endpoint returning result_count > 0; "
                                       "a 4xx/5xx would have been INVALID, not absence")


CHK001 = Check(
    check_id="CHK001_RETRIEVAL_ABSENCE",
    instrument=Instrument("http-retrieval", reads=("http_status", "result_count"),
                          can_distinguish_absent_from_unreachable=True),
    fn=_retrieval_absence,
    description="An absence is reportable only from a 200 with a parsed empty set.",
    must_fire_on=[Fixture(
        "absence_claimed_but_record_present",
        {"endpoint": "corpus:03_PRISMA_AND_SCREENING_NOTES", "http_status": 200,
         "result_count": 1, "claim": "not encountered"},
        Verdict.FAIL,
        provenance="N2 -- 'not encountered' asserted while PMID 34395116 sat in "
                   "the corpus reporting exactly that class")],
    must_be_silent_on=[Fixture(
        "ctgov_answer_hf_no_results_module",
        {"endpoint": "clinicaltrials.gov/NCT04853758", "http_status": 200,
         "result_count": 0},
        Verdict.PASS,
        provenance="ANSWER-HF route log -- has_results:false re-verified live")],
    observation_terms={
        "http_status": lambda p: _mut(p, http_status=429),
        "result_count": lambda p: _mut(p, result_count=3),
    },
)


# =============================================================================
# CHK002 -- a match is not a match without a boundary and a scope
# =============================================================================
# Incidents: grep "1406" matching 1009 of 1243 pages because the digits sit
# inside data arrays; grep "quota" matching "quotable"; grep "fatal" matching
# "Nonfatal Myocardial Infarction".

def _token_match(p: Mapping[str, Any]) -> Result:
    cid, inst = "CHK002_TOKEN_MATCH", "text-search"
    pat = p.get("pattern", "")
    if not p.get("field_scoped"):
        return make_invalid(cid, inst,
                            f"pattern {pat!r} searched over an unscoped document. "
                            "A hit cannot be attributed to prose rather than to a "
                            "data array, so neither a hit nor a miss is informative.")
    hits = list(p.get("hits", []))
    bad = [h for h in hits if pat and pat in h and h != pat]
    if bad:
        return make_fail(cid, inst,
                         f"pattern {pat!r} matched inside larger tokens: {bad}",
                         observed=f"{len(bad)} hit(s) where {pat!r} is a proper "
                                  f"substring, e.g. {bad[0]!r}",
                         locator=f"field={p.get('field')!r}",
                         opposite_would_be="every hit an exact token match for the "
                                           "pattern",
                         substring_hits=bad)
    return make_pass(cid, inst,
                     observed=f"{len(hits)} exact-token hit(s) for {pat!r} in field "
                              f"{p.get('field')!r}",
                     locator=f"field={p.get('field')!r}",
                     opposite_would_be="a hit whose surrounding token strictly "
                                       "contains the pattern, e.g. 'Nonfatal' for "
                                       "'fatal', which would have been FAIL")


CHK002 = Check(
    check_id="CHK002_TOKEN_MATCH",
    instrument=Instrument("text-search", reads=("pattern", "field_scoped", "hits")),
    fn=_token_match,
    description="Substring search over a whole document cannot discriminate; "
                "matching must be field-scoped and token-bounded.",
    must_fire_on=[Fixture(
        "fatal_matches_nonfatal_mi",
        {"pattern": "fatal", "field": "outcome_label", "field_scoped": True,
         "hits": ["Nonfatal Myocardial Infarction", "fatal"]},
        Verdict.FAIL,
        provenance="grep 'fatal' matching 'Nonfatal Myocardial Infarction'")],
    must_be_silent_on=[Fixture(
        # CORPUS-DERIVED NEGATIVE, deliberately. validator-validation-protocol.md
        # Sec 6 warns that this class is only "partially caught -- depends on
        # fixture provenance. A synthetic negative will not contain them." So the
        # clean fixture carries the same confounding tokens as the dirty one:
        # real outcome labels from the cardiology corpus in which 'fatal' occurs
        # inside 'Nonfatal', and digits occur inside composite counts.
        "fatal_scoped_to_real_corpus_labels",
        {"pattern": "fatal", "field": "outcome_label", "field_scoped": True,
         "hits": ["fatal"],
         "field_contents_verbatim": [
             "Nonfatal Myocardial Infarction", "Nonfatal Stroke",
             "fatal", "Death from any cause, nonfatal myocardial infarction, "
                      "or nonfatal stroke"],
         "corpus_source": "TWILIGHT NEJM 2019 key secondary endpoint wording, "
                          "DEFECT_LEDGER_cardiology_mortality_atlas.md:46"},
        Verdict.PASS,
        provenance="grep 'fatal' matching 'Nonfatal Myocardial Infarction' -- the "
                   "corrected form, with the confounder retained in the fixture")],
    observation_terms={
        "field_scoped": lambda p: _mut(p, field_scoped=False),
        "hits": lambda p: _mut(p, hits=list(p.get("hits", [])) + [p["pattern"] + "able"]),
    },
)


# =============================================================================
# CHK003 -- an action counts as done only when the world changed
# =============================================================================
# Incidents: a `ref`-based click returning without error, having silently
# no-op'd; a LibKey button rendering read as proof of delivery.

def _action_effect(p: Mapping[str, Any]) -> Result:
    cid, inst = "CHK003_ACTION_EFFECT", "ui-action"
    field = p.get("observed_effect_field")
    if not field:
        return make_invalid(cid, inst,
                            f"action {p.get('action')!r} returned without error but "
                            "no post-state observation was made. Absence of an error "
                            "is not evidence of an effect.")
    pre, post = p.get("pre_state"), p.get("post_state")
    if pre == post:
        return make_fail(cid, inst,
                         f"action {p.get('action')!r} completed without error but "
                         f"{field!r} is unchanged ({pre!r}): silent no-op",
                         observed=f"{field!r} = {pre!r} before and after",
                         locator=f"action={p.get('action')!r} field={field!r}",
                         opposite_would_be=f"{field!r} holding a different value after "
                                           "the action than before it",
                         field=field, value=pre)
    return make_pass(cid, inst,
                     observed=f"{field!r} moved {pre!r} -> {post!r}",
                     locator=f"action={p.get('action')!r} field={field!r}",
                     opposite_would_be=f"{field!r} unchanged at {pre!r}, which is "
                                       "what a silent no-op looks like")


CHK003 = Check(
    check_id="CHK003_ACTION_EFFECT",
    instrument=Instrument("ui-action", reads=("observed_effect_field", "pre_state",
                                              "post_state")),
    fn=_action_effect,
    description="No error is not an effect. Require a post-state observation.",
    must_fire_on=[Fixture(
        "ref_click_silent_noop",
        {"action": "click(ref=e42)", "error": None, "observed_effect_field": "url",
         "pre_state": "https://host/search", "post_state": "https://host/search"},
        Verdict.FAIL,
        provenance="ref-based click returned without error, silently no-op'd")],
    must_be_silent_on=[Fixture(
        "click_navigated",
        {"action": "click(ref=e42)", "error": None, "observed_effect_field": "url",
         "pre_state": "https://host/search", "post_state": "https://host/article/1"},
        Verdict.PASS,
        provenance="the corrected form of the same click")],
    observation_terms={
        "post_state": lambda p: _mut(p, post_state=p.get("pre_state")),
        "observed_effect_field": lambda p: _mut(p, observed_effect_field=None),
    },
)


# =============================================================================
# CHK004 -- liveness, with the platform and corroboration declared
# =============================================================================
# Incidents: `pgrep` on Windows always returning nothing, so a liveness check
# always reported "exited"; a daemon reported killed that ran for hours
# afterwards, double-launching lanes and burning quota.

_PROBE_PLATFORMS = {"pgrep": {"Linux", "Darwin"}, "tasklist": {"Windows"},
                    "psutil": {"Linux", "Darwin", "Windows"}}


def _liveness(p: Mapping[str, Any]) -> Result:
    cid, inst = "CHK004_LIVENESS", "process-probe"
    probe, host = p.get("probe"), p.get("host_os")
    supported = _PROBE_PLATFORMS.get(probe, set())
    if host not in supported:
        return make_invalid(cid, inst,
                            f"probe {probe!r} is not meaningful on {host!r} "
                            f"(supported: {sorted(supported) or 'none'}). It returns "
                            "the same empty output for a live process and a dead one, "
                            "so it cannot report death.",
                            probe=probe, host_os=host)
    if p.get("stdout"):
        return make_pass(cid, inst,
                         observed=f"{probe} returned pid(s) {p['stdout']!r}",
                         locator=f"{probe}@{host}",
                         opposite_would_be="empty stdout together with a corroborating "
                                           "negative, e.g. an absent pidfile or a "
                                           "closed port")
    if not p.get("corroborated"):
        return make_invalid(cid, inst,
                            f"{probe} returned nothing and no second, independent "
                            "observation was made. One empty probe cannot distinguish "
                            "a dead process from a probe that never sees anything.")
    return make_fail(cid, inst,
                     f"{probe} empty and corroborated by {p.get('corroborating_probe')!r}: "
                     "process is not running",
                     observed=f"{probe} returned no pid on {host}, and "
                              f"{p.get('corroborating_probe')!r} agrees",
                     locator=f"{probe}@{host}",
                     opposite_would_be="a pid returned by the probe, or the "
                                       "corroborating observation disagreeing",
                     corroborating_probe=p.get("corroborating_probe"))


CHK004 = Check(
    check_id="CHK004_LIVENESS",
    instrument=Instrument("process-probe", reads=("probe", "host_os", "stdout",
                                                  "corroborated"),
                          can_distinguish_absent_from_unreachable=False),
    fn=_liveness,
    description="A death report needs a probe valid on this OS and a second "
                "independent observation.",
    must_fire_on=[Fixture(
        "corroborated_death",
        {"probe": "pgrep", "host_os": "Linux", "stdout": "", "corroborated": True,
         "corroborating_probe": "pidfile absent"},
        Verdict.FAIL,
        provenance="the shape a real death report must have")],
    must_be_silent_on=[Fixture(
        "pid_returned",
        {"probe": "pgrep", "host_os": "Linux", "stdout": "48213",
         "corroborated": False},
        Verdict.PASS,
        provenance="daemon reported killed that ran for hours afterwards")],
    observation_terms={
        "host_os": lambda p: _mut(p, host_os="Windows"),
        "stdout": lambda p: _mut(p, stdout="", corroborated=True,
                                 corroborating_probe="pidfile absent"),
    },
)


# =============================================================================
# CHK005 -- consistency does not authenticate
# =============================================================================
# Incident, verbatim from DEFECT_LEDGER_cardiology_mortality_atlas.md:
#   "Location B is internally consistent: 172/4614 vs 168/4603 gives RR 0.995
#    against the stored HR of 0.99. Any check that validates a row by reproducing
#    its own effect estimate passes it. Consistency does not authenticate a row."
# And from the harness report: "agreement authenticates nothing. Only
# disagreement is informative."

def _ref_entry(value, locator):
    """Build a provenanced referent cell: a value plus where it was read."""
    return {"value": value, "locator": locator}


def _unwrap(v):
    """Return (value, locator). A bare value has no locator."""
    if isinstance(v, Mapping) and "value" in v:
        return v["value"], str(v.get("locator") or "").strip()
    return v, ""


def _external_referent(p: Mapping[str, Any]) -> Result:
    """Provenance gates the AGREEMENT path only. Disagreement is always reportable.

    THE INTERFACE HOLE, AND THE OVER-CORRECTION THAT FOLLOWED IT.

    Round 1 (found by mutation testing, not review): this detector killed all
    five value mutants when handed a referent keyed by field, and PASSED all five
    when handed a flat number-bag -- the encoding validate_v2.py used, and the
    historical failure. The mechanism was fixed at the detector and left open at
    the interface: M4 operating inside the tool built to catch M4.

    Round 2 (found by running the benchmark lane's mutant set rather than my own):
    the fix -- demand a document id and a per-key locator before any verdict --
    closed the hole and BROKE THE HONEST CALLER. A caller that had extracted the
    right quantity from the right source and keyed it correctly, but carried no
    provenance metadata, went from 5 kills to 5 refusals. Arm A fell 7/7 -> 2/7.
    That is a regression, and it is M10 in my own code: the correction was worse
    than the original in one direction.

    The discriminator that fixes both is in the corpus already, in the CHK014
    caveat of cardio_acm_harness_report.md:

        "agreement authenticates nothing. Only disagreement is informative."

    So provenance is required to CLEAR a row, not to CONVICT one:

      * DISAGREEMENT  -> FAIL, provenance or not. A contradiction against any
                         referent is a real contradiction; you have found
                         something. Withholding it because the paperwork is thin
                         suppresses a true positive.
      * AGREEMENT + provenance   -> PASS.
      * AGREEMENT without provenance -> INVALID. Agreement with a referent that
                         cannot say where its numbers came from is exactly what a
                         bag echoing the row produces, and it is worthless.

    A number-bag therefore still cannot certify anything, and an honest caller
    still gets its defects reported.
    """
    cid, inst = "CHK005_EXTERNAL_REFERENT", "registry-crosscheck"
    ref = p.get("external_referent")

    # (a) no referent at all -- self-validation
    if not ref:
        return make_invalid(cid, inst,
                            "row was validated only against itself. Internal "
                            "consistency is reproducible from the row's own numbers "
                            "and therefore cannot distinguish a correct row from a "
                            "fabricated one. No external referent, no verdict.")

    row = dict(p.get("row", {}))
    under_test = list(p.get("keys_under_test") or sorted(row))

    missing_from_row = sorted(k for k in under_test if k not in row)
    if missing_from_row:
        return make_invalid(cid, inst,
                            f"keys {missing_from_row} are under test but absent from "
                            "the row itself; there is nothing to compare.",
                            missing_from_row=missing_from_row)

    # (b) MISSING KEYS ARE NOT A SILENT SKIP.
    # The original compared `for k, v in ref.items() if k in row`, so a key under
    # test that the referent did not cover was skipped rather than flagged. A
    # field nobody checked must not read as a field that passed. A referent cell
    # explicitly holding None is 'not found in the source' -- also uncovered.
    uncovered = sorted(k for k in under_test
                       if k not in ref or _unwrap(ref[k])[0] is None)
    if uncovered:
        return make_invalid(cid, inst,
                            f"keys {uncovered} are under test but not covered by the "
                            "referent. They were not checked, and unchecked is not "
                            "clean. Either source them, or narrow keys_under_test "
                            "explicitly so the omission is on the record.",
                            unchecked_keys=uncovered)

    # (c) compare -- provenance is NOT required to report a contradiction
    disagreements = {}
    for k in under_test:
        rv, loc = _unwrap(ref[k])
        if row[k] != rv:
            disagreements[k] = {"row": row[k], "referent": rv,
                                "locator": loc or "(no locator recorded)"}
    if disagreements:
        k0 = sorted(disagreements)[0]
        return make_fail(cid, inst,
                         f"row disagrees with {p.get('referent_name')} on "
                         f"{sorted(disagreements)}",
                         observed="; ".join(
                             f"{k}: row={d['row']!r} vs referent={d['referent']!r} "
                             f"read at {d['locator']}"
                             for k, d in sorted(disagreements.items())),
                         locator=f"{p.get('referent_document_id') or '(no document id)'}"
                                 f" :: {disagreements[k0]['locator']}",
                         opposite_would_be=f"every key in {sorted(under_test)} equal "
                                           "to the referent's value for that key",
                         disagreements=disagreements)

    # (d) agreement -- NOW provenance decides whether this can clear the row
    doc_id = p.get("referent_document_id")
    unlocated = sorted(k for k in under_test if not _unwrap(ref[k])[1])
    if not doc_id or unlocated:
        missing = []
        if not doc_id:
            missing.append("no referent_document_id")
        if unlocated:
            missing.append(f"no locator on {unlocated}")
        return make_invalid(cid, inst,
                            "row AGREES with the referent, but the referent cannot "
                            f"say where its values came from ({'; '.join(missing)}). "
                            "Agreement authenticates nothing: a bag of numbers "
                            "echoed out of the row agrees with it by construction. "
                            "A disagreement would still have been reported.",
                            unlocated_keys=unlocated, has_document_id=bool(doc_id))

    return make_pass(cid, inst,
                     observed=f"all of {sorted(under_test)} equal the values at their "
                              f"stated locators in {doc_id}",
                     locator=f"{doc_id} ({p.get('referent_name')})",
                     opposite_would_be="a disagreement on any key under test, against "
                                       "the value at its own recorded locator")


def _row_key_mutants(p: Mapping[str, Any]) -> list:
    """One mutant per key of the row -- not just the alphabetically first.

    The bug this replaces: `_deep(p, ["row", sorted(p["row"])[0]], -1)` swept a
    single key, so coverage depended on key spelling. Renaming `dosed` to
    `zz_dosed` moved a key out of the sweep with no change in semantics.
    """
    out = []
    for k in sorted(p.get("row", {})):
        m = copy.deepcopy(dict(p))
        v = m["row"][k]
        m["row"][k] = (v + 1) if isinstance(v, (int, float)) and not isinstance(
            v, bool) else "__MUTATED__"
        m["_mutant_label"] = f"row[{k}]"
        out.append(m)
    return out


def _flatten_referent_to_number_bag(p: Mapping[str, Any]) -> dict:
    """The historical encoding: values with the provenance stripped off."""
    m = copy.deepcopy(dict(p))
    m["external_referent"] = {k: v["value"] if isinstance(v, Mapping) else v
                              for k, v in (m.get("external_referent") or {}).items()}
    m["_mutant_label"] = "referent_provenance->number_bag"
    return m


CHK005 = Check(
    check_id="CHK005_EXTERNAL_REFERENT",
    instrument=Instrument("registry-crosscheck", reads=("row", "external_referent")),
    fn=_external_referent,
    description="A row is authenticated only against a source outside itself.",
    must_fire_on=[Fixture(
        "twilight_location_b",
        {"referent_name": "ClinicalTrials.gov NCT02270242 participant flow",
         "referent_document_id": "NCT02270242",
         "row": {"tN": 4614, "cN": 4603},
         "external_referent": {
             "tN": _ref_entry(3555, "participantFlow.STARTED, ticagrelor+placebo"),
             "cN": _ref_entry(3564, "participantFlow.STARTED, ticagrelor+aspirin")}},
        Verdict.FAIL,
        provenance="DEFECT-01 -- denominators exceed the randomised total by 2098, "
                   "while the row reproduces its own HR to three decimals")],
    must_be_silent_on=[Fixture(
        "twilight_location_a",
        {"referent_name": "ClinicalTrials.gov NCT02270242 participant flow",
         "referent_document_id": "NCT02270242",
         "row": {"tN": 3555, "cN": 3564},
         "external_referent": {
             "tN": _ref_entry(3555, "participantFlow.STARTED, ticagrelor+placebo"),
             "cN": _ref_entry(3564, "participantFlow.STARTED, ticagrelor+aspirin")}},
        Verdict.PASS,
        provenance="DEFECT-01 -- 'Location A matches the registry exactly'")],
    observation_terms={
        "external_referent": lambda p: _mut(p, external_referent=None),
        "referent_provenance": _flatten_referent_to_number_bag,
        "referent_document_id": lambda p: _mut(p, referent_document_id=None),
        "row": _row_key_mutants,          # every key, not the first alphabetically
    },
)


# =============================================================================
# CHK006 -- identity is a registration number verified in the source document
# =============================================================================
# Incidents: PARACHUTE-HF conflated with ANSWER-HF via a covering label; ORION-11
# recorded on NCT03705234, which is ORION-4 (16,124 vs 1,617 patients); "CANVAS
# Program" pointing at NCT01032629, which is CANVAS alone.

def _identity_key(p: Mapping[str, Any]) -> Result:
    cid, inst = "CHK006_IDENTITY_KEY", "registry-identity"
    rid = p.get("registration_id")
    if not rid:
        return make_invalid(cid, inst,
                            f"identity for {p.get('claimed_name')!r} rests on a "
                            "label, filename or citation string. Names are not keys: "
                            "a covering label can span two trials.")
    doc_ids = set(p.get("source_document_ids") or [])
    if rid not in doc_ids:
        return make_fail(cid, inst,
                         f"{rid} does not appear in the source document "
                         f"({sorted(doc_ids) or 'no identifiers found'})",
                         observed=f"identifiers present in source: "
                                  f"{sorted(doc_ids) or 'none'}; {rid} not among them",
                         locator=str(p.get("source_document")),
                         opposite_would_be=f"{rid} appearing verbatim among the "
                                           "source document's identifiers",
                         registration_id=rid)
    acronym = p.get("registry_acronym")
    if acronym and p.get("claimed_name") and acronym != p["claimed_name"]:
        return make_fail(cid, inst,
                         f"{rid} is registered as {acronym!r}, recorded as "
                         f"{p['claimed_name']!r}",
                         observed=f"registry acronym for {rid} is {acronym!r}",
                         locator=f"{rid} @ {p.get('source_document')}",
                         opposite_would_be=f"the registry acronym equal to the "
                                           f"recorded name {p['claimed_name']!r}",
                         registry_acronym=acronym, claimed_name=p["claimed_name"])
    enrol, weight = p.get("registry_enrolment"), p.get("row_weight")
    if enrol and weight:
        delta = abs(enrol - weight)
        tolerance = max(0.1 * enrol, 50)
        if delta > tolerance:
            return make_fail(cid, inst,
                             f"{rid} registered enrolment {enrol} vs row weight "
                             f"{weight}",
                             observed=f"registered enrolment {enrol}, row weight "
                                      f"{weight} ({delta} apart)",
                             locator=f"{rid} enrolment module",
                             opposite_would_be="row weight within 10% of the "
                                               "registered enrolment",
                             registry_enrolment=enrol, row_weight=weight)
        # A NON-ZERO DELTA INSIDE THE TOLERANCE BAND IS BELOW THIS INSTRUMENT'S
        # RESOLUTION -- so it may not be certified.
        #
        # Found by the benchmark lane's mutant set and NOT by mine: mutant M5b
        # perturbs registry_enrolment 33758 -> 33759 and this check returned
        # PASS, because 1 is far inside max(0.1*enrol, 50). The tolerance is
        # correct -- analysed N legitimately differs from randomised N -- but a
        # tolerance is a statement that the instrument CANNOT RESOLVE differences
        # of that size, and a check must not clear a dimension it cannot resolve.
        #
        # This mirrors the corpus's own CHK002_DENOMINATOR_NOT_RANDOMISED, which
        # holds PARAGON-HF open because 12 and 14 participants were excluded with
        # the reason "NOT STATED": "an unexplained exclusion is not the same as an
        # explained one." A declared explanation clears it; silence does not.
        if delta and not p.get("enrolment_delta_explained"):
            return make_invalid(cid, inst,
                                f"{rid} registered enrolment {enrol} vs row weight "
                                f"{weight}: a delta of {delta} sits inside this "
                                f"check's tolerance of {tolerance:.0f} and is "
                                "therefore below its resolution. It can neither be "
                                "convicted nor cleared here. Supply "
                                "enrolment_delta_explained (e.g. 'FAS excludes 12 "
                                "post-randomisation withdrawals'), or verify the "
                                "value with CHK005 against a provenanced referent.",
                                registry_enrolment=enrol, row_weight=weight,
                                delta=delta, tolerance=tolerance)
    return make_pass(cid, inst,
                     observed=f"{rid} present in source document; registry acronym "
                              f"{acronym!r} matches recorded name",
                     locator=f"{rid} @ {p.get('source_document')}",
                     opposite_would_be="the identifier absent from the source "
                                       "document, or a registry acronym differing "
                                       "from the recorded name")


CHK006 = Check(
    check_id="CHK006_IDENTITY_KEY",
    instrument=Instrument("registry-identity",
                          reads=("registration_id", "source_document_ids",
                                 "registry_acronym", "registry_enrolment")),
    fn=_identity_key,
    description="Key on the registration identifier, verified against the source "
                "document. Never on a name, label, filename or citation string.",
    must_fire_on=[Fixture(
        "orion11_on_orion4_nct",
        {"claimed_name": "ORION-11", "registration_id": "NCT03705234",
         "source_document": "ClinicalTrials.gov", "source_document_ids": ["NCT03705234"],
         "registry_acronym": "ORION-4", "registry_enrolment": 16124, "row_weight": 1617},
        Verdict.FAIL,
        provenance="report #6 error #14 -- a 16,124-patient CV outcomes trial "
                   "recorded as a 1,617-patient lipid trial")],
    must_be_silent_on=[Fixture(
        "orion11_correct_nct",
        {"claimed_name": "ORION-11", "registration_id": "NCT03400800",
         "source_document": "ClinicalTrials.gov", "source_document_ids": ["NCT03400800"],
         "registry_acronym": "ORION-11", "registry_enrolment": 1617, "row_weight": 1617},
        Verdict.PASS,
        provenance="report #6 -- ORION-11 @ NCT03400800 confirmed correct")],
    observation_terms={
        "registration_id": lambda p: _mut(p, registration_id=None),
        "registry_acronym": lambda p: _mut(p, registry_acronym="SOMETHING-ELSE"),
    },
)


# =============================================================================
# CHK007 -- "none found" renders only from an execution record (Rule 4 v2)
# =============================================================================

_SCREEN_FIELDS = ("screen_id", "tool_or_query", "executed_at", "input_set_size",
                  "criterion")


def _absence_screen(p: Mapping[str, Any]) -> Result:
    cid, inst = "CHK007_ABSENCE_SCREEN", "screen-record"
    screen = p.get("screen") or {}
    missing = [f for f in _SCREEN_FIELDS if not screen.get(f)]
    if missing:
        return make_invalid(cid, inst,
                            f"'none found' claimed with no execution record "
                            f"(missing: {missing}). Renders as NOT SCREENED. "
                            "Absence of a screen and absence of a finding are "
                            "different statements and may not share a cell.")
    findings = list(p.get("findings") or [])
    if findings:
        return make_fail(cid, inst,
                         f"'none found' contradicted by {len(findings)} finding(s): "
                         f"{findings}",
                         observed=f"screen {screen['screen_id']} returned "
                                  f"{len(findings)} finding(s): {findings}",
                         locator=f"{screen['screen_id']} @ {screen['executed_at']}",
                         opposite_would_be="the same screen, same criterion, same "
                                           "input set, returning zero findings",
                         findings=findings)
    return make_pass(cid, inst,
                     observed=f"screen {screen['screen_id']} ran "
                              f"{screen['tool_or_query']} over "
                              f"{screen['input_set_size']} items, 0 findings",
                     locator=f"{screen['screen_id']} @ {screen['executed_at']}",
                     opposite_would_be="the same screen returning one or more "
                                       "findings against the same criterion")


CHK007 = Check(
    check_id="CHK007_ABSENCE_SCREEN",
    instrument=Instrument("screen-record", reads=("screen", "findings")),
    fn=_absence_screen,
    description="Rule 4 v2 -- a 'none found' row may not be rendered from prose.",
    must_fire_on=[Fixture(
        "not_encountered_but_present",
        {"screen": {"screen_id": "SCR-M3-001", "tool_or_query": "corpus scan",
                    "executed_at": "2026-08-12T00:00:00Z", "input_set_size": 87,
                    "criterion": "reports composite as fixed-timepoint RR"},
         "findings": ["PMID 34395116"]},
        Verdict.FAIL,
        provenance="N2 -- 'not encountered' while PMID 34395116 reported exactly that")],
    must_be_silent_on=[Fixture(
        "screened_none_found",
        {"screen": {"screen_id": "SCR-M10-001", "tool_or_query": "GRIM screen",
                    "executed_at": "2026-08-12T00:00:00Z", "input_set_size": 21,
                    "criterion": "mean inconsistent with n"},
         "findings": []},
        Verdict.PASS,
        provenance="the compliant form Rule 4 v2 specifies")],
    observation_terms={
        "screen": lambda p: _mut(p, screen=None),
        "findings": lambda p: _mut(p, findings=["synthetic-positive"]),
    },
)


# =============================================================================
# CHK008 -- no coverage claim without a maintained denominator (Rule M4)
# =============================================================================
# Incident N3: "across 44 syntheses ... the registered search missed no
# randomised trial" -- the retrievable frame was 244. The 44 are 18% of it.

def _frame_denominator(p: Mapping[str, Any]) -> Result:
    cid, inst = "CHK008_FRAME_DENOMINATOR", "coverage-frame"
    den, src = p.get("denominator"), p.get("denominator_source")
    if den is None or src != "maintained_counter":
        return make_invalid(cid, inst,
                            f"coverage stated against denominator={den!r} from "
                            f"source={src!r}. A proportion may not render unless the "
                            "denominator is a maintained counter rather than a typed "
                            "literal.")
    num = p.get("numerator", 0)
    if p.get("claim_scope") == "complete" and num < den:
        return make_fail(cid, inst,
                         f"completeness claimed over {num}/{den} "
                         f"({num / den:.0%} of the frame)",
                         observed=f"{num} examined against a maintained frame of "
                                  f"{den} -- {num / den:.0%}",
                         locator=str(p.get("frame_name")),
                         opposite_would_be="the claim scoped to the fraction actually "
                                           "examined, or numerator equal to the frame",
                         numerator=num, denominator=den)
    return make_pass(cid, inst,
                     observed=f"claim scoped to {num}/{den} ({num / den:.0%} of the "
                              f"stated frame {p.get('frame_name')!r})",
                     locator=str(p.get("frame_name")),
                     opposite_would_be="the same numerator presented as complete "
                                       "coverage of the frame")


CHK008 = Check(
    check_id="CHK008_FRAME_DENOMINATOR",
    instrument=Instrument("coverage-frame",
                          reads=("denominator", "denominator_source", "claim_scope")),
    fn=_frame_denominator,
    description="A recall/coverage statistic requires a maintained denominator and "
                "an explicit scope.",
    must_fire_on=[Fixture(
        "n3_frame_overclaim",
        {"frame_name": "PubMed syntheses of this comparison", "numerator": 44,
         "denominator": 244, "denominator_source": "maintained_counter",
         "claim_scope": "complete"},
        Verdict.FAIL,
        provenance="N3 -- 'missed no randomised trial' over 18% of the frame")],
    must_be_silent_on=[Fixture(
        "n3_scoped_correctly",
        {"frame_name": "PubMed syntheses of this comparison", "numerator": 44,
         "denominator": 244, "denominator_source": "maintained_counter",
         "claim_scope": "scoped"},
        Verdict.PASS,
        provenance="N3 as corrected in 10_WHAT_THIS_PROCESS_DOES.md")],
    observation_terms={
        "denominator_source": lambda p: _mut(p, denominator_source="typed_literal"),
        "claim_scope": lambda p: _mut(p, claim_scope="complete"),
    },
)


# =============================================================================
# CHK009 -- every number in a panel must be about the same pool
# =============================================================================
# Incidents: a k=3 analysis panel shipped under a k=4 headline, every number
# individually correct but about different pools; TWILIGHT's composite of death,
# MI and stroke pooled in a mortality atlas.

def _pool_identity(p: Mapping[str, Any]) -> Result:
    cid, inst = "CHK009_POOL_IDENTITY", "pool-manifest"
    rows = list(p.get("panel_rows") or [])
    if not rows:
        return make_invalid(cid, inst, "no panel rows supplied")
    incomplete = [r.get("id") for r in rows
                  if not (r.get("outcome") and r.get("population") and r.get("window"))]
    if incomplete:
        return make_invalid(cid, inst,
                            f"rows {incomplete} do not record outcome, population and "
                            "window. Without them the pool's identity is unknown and "
                            "an outcome substitution is invisible.")
    k_head = p.get("headline_k")
    if k_head is not None and k_head != len(rows):
        return make_fail(cid, inst,
                         f"headline states k={k_head}, panel carries {len(rows)} rows",
                         observed=f"panel rows: {[r['id'] for r in rows]} (k="
                                  f"{len(rows)}) under a headline stating k={k_head}",
                         locator=str(p.get("panel_name")),
                         opposite_would_be=f"exactly {k_head} rows in the panel",
                         headline_k=k_head, panel_k=len(rows))
    want = p.get("headline_outcome")
    off = [r["id"] for r in rows if want and r["outcome"] != want]
    if off:
        offending = [r for r in rows if r["id"] in off]
        return make_fail(cid, inst,
                         f"rows {off} measure a different outcome from the headline "
                         f"{want!r}",
                         observed="; ".join(f"{r['id']}: outcome={r['outcome']!r} "
                                            f"population={r['population']!r} "
                                            f"window={r['window']!r}"
                                            for r in offending),
                         locator=str(p.get("panel_name")),
                         opposite_would_be=f"every row carrying outcome={want!r}",
                         offending=off)
    return make_pass(cid, inst,
                     observed=f"k={len(rows)} rows, all carrying outcome={want!r}, "
                              "population and window",
                     locator=str(p.get("panel_name")),
                     opposite_would_be="a row whose outcome, population or window "
                                       "differs from the headline, or a row count "
                                       "differing from the stated k")


CHK009 = Check(
    check_id="CHK009_POOL_IDENTITY",
    instrument=Instrument("pool-manifest", reads=("headline_k", "headline_outcome",
                                                  "panel_rows")),
    fn=_pool_identity,
    description="Individually correct numbers about different pools are a wrong panel.",
    must_fire_on=[Fixture(
        "twilight_composite_in_mortality_pool",
        {"panel_name": "classes[20] P2Y12 mono", "headline_k": 2,
         "headline_outcome": "all_cause_mortality",
         "panel_rows": [
             {"id": "NCT02270242", "outcome": "death_mi_stroke_composite",
              "population": "per_protocol", "window": "12m"},
             {"id": "NCT01813435", "outcome": "all_cause_mortality",
              "population": "randomised", "window": "24m"}]},
        Verdict.FAIL,
        provenance="DEFECT-01 escalation -- 'a composite of death, MI and stroke "
                   "masquerading as all-cause mortality'")],
    must_be_silent_on=[Fixture(
        "clean_mortality_pool",
        {"panel_name": "classes[29] SGLT2 CVOT", "headline_k": 2,
         "headline_outcome": "all_cause_mortality",
         "panel_rows": [
             {"id": "NCT01131676", "outcome": "all_cause_mortality",
              "population": "randomised", "window": "full"},
             {"id": "NCT01730534", "outcome": "all_cause_mortality",
              "population": "randomised", "window": "full"}]},
        Verdict.PASS,
        provenance="the shape the cross-cutting recommendation asks for")],
    observation_terms={
        "headline_k": lambda p: _mut(p, headline_k=(p.get("headline_k") or 0) + 1),
        "panel_rows": lambda p: _deep(p, ["panel_rows"],
                                      [{**r, "outcome": None} if i == 0 else r
                                       for i, r in enumerate(p["panel_rows"])]),
    },
)


# =============================================================================
# CHK010 -- "blocked" requires the chain to have been walked
# =============================================================================
# Incident: a four-hop retrieval chain abandoned at hop zero and written up as
# blocked. Contrast the ANSWER-HF route log, which is the compliant form: every
# route numbered, dated, and given a definitive or named-obstacle outcome.

def _chain_exhaustion(p: Mapping[str, Any]) -> Result:
    cid, inst = "CHK010_CHAIN_EXHAUSTION", "route-log"
    log = list(p.get("hop_log") or [])
    declared = p.get("declared_hops")
    if not log or declared is None:
        return make_invalid(cid, inst,
                            "no route log or no declared hop count: a blocked verdict "
                            "cannot be distinguished from an unattempted one")
    reached = max((h.get("hop", -1) for h in log), default=-1)
    if p.get("conclusion") == "blocked" and reached < declared - 1:
        return make_fail(cid, inst,
                         f"declared as blocked having reached hop {reached} of "
                         f"{declared - 1}: {declared - 1 - reached} hop(s) never "
                         "attempted",
                         observed=f"route log holds {len(log)} entr(ies), highest hop "
                                  f"{reached}, conclusion 'blocked'",
                         locator=str(p.get("target")),
                         opposite_would_be=f"a log reaching hop {declared - 1} with an "
                                           "outcome recorded for each, as the "
                                           "ANSWER-HF route log does",
                         reached=reached, declared_hops=declared)
    return make_pass(cid, inst,
                     observed=f"{len(log)} hop(s) logged, reached hop {reached} of "
                              f"{declared - 1}; conclusion {p.get('conclusion')!r}",
                     locator=str(p.get("target")),
                     opposite_would_be="a blocked conclusion with unattempted hops "
                                       "remaining in the declared chain")


CHK010 = Check(
    check_id="CHK010_CHAIN_EXHAUSTION",
    instrument=Instrument("route-log", reads=("declared_hops", "hop_log", "conclusion")),
    fn=_chain_exhaustion,
    description="A blocker is a claim about a chain, and needs the chain's log.",
    must_fire_on=[Fixture(
        "abandoned_at_hop_zero",
        {"target": "four-hop retrieval", "declared_hops": 4, "conclusion": "blocked",
         "hop_log": [{"hop": 0, "outcome": "failed"}]},
        Verdict.FAIL,
        provenance="four-hop chain abandoned at hop zero, written up as blocked")],
    must_be_silent_on=[Fixture(
        "answer_hf_route_log",
        {"target": "ANSWER-HF per-arm counts", "declared_hops": 4,
         "conclusion": "blocked",
         "hop_log": [{"hop": 0, "outcome": "ctgov has_results:false"},
                     {"hop": 1, "outcome": "Unpaywall oa_status closed"},
                     {"hop": 2, "outcome": "Europe PMC inPMC:N hasSuppl:N"},
                     {"hop": 3, "outcome": "reverse citation k=4, all closed"}]},
        Verdict.PASS,
        provenance="answer_hf_route_log.md -- the compliant form")],
    observation_terms={
        "hop_log": lambda p: _mut(p, hop_log=[]),
        "conclusion": lambda p: _mut(p, conclusion="blocked",
                                     hop_log=[{"hop": 0, "outcome": "failed"}]),
    },
)


# =============================================================================
# CHK011 -- a correction carries a heavier burden than the original
# =============================================================================
# Finding: in the ANSWER-HF episode the original extraction was right and three
# separate corrections were wrong. A correction is written under time pressure,
# against a belief that something is broken, and is rarely re-reviewed.

def _correction_burden(p: Mapping[str, Any]) -> Result:
    cid, inst = "CHK011_CORRECTION_BURDEN", "correction-gate"
    if p.get("correcting_source_id") and \
            p["correcting_source_id"] == p.get("original_source_id"):
        return make_invalid(cid, inst,
                            "the correction is sourced from the same instrument that "
                            "produced the original. It cannot adjudicate between them.")
    if not p.get("correcting_source_id"):
        return make_invalid(cid, inst, "no correcting source identified")
    if not p.get("original_rechecked_at_source"):
        return make_fail(cid, inst,
                         "correction issued without re-reading the original at its "
                         "own source. Most of this project's wrong corrections "
                         "replaced a value that was right.",
                         observed=f"proposed {p.get('original_value')!r} -> "
                                  f"{p.get('corrected_value')!r} with "
                                  "original_rechecked_at_source=False",
                         locator=str(p.get("original_source_id")),
                         opposite_would_be="the original re-read at its own source "
                                           "and found to differ",
                         original=p.get("original_value"),
                         proposed=p.get("corrected_value"))
    # The discriminating feature, measured: corrections that held were sourced
    # from a document not previously read. Corrections that failed were
    # re-interpretations of the instrument that produced the original.
    # EB-021 -> EB-022 is the case in point: the rule correcting the bash false
    # zeros was itself wrong for ~7 hours, because it re-interpreted the same
    # toolchain instead of retrieving a new one.
    if not p.get("evidence_is_newly_retrieved_source"):
        return make_fail(cid, inst,
                         "the correction's evidence is not a newly retrieved "
                         "source. A re-interpretation of already-held material is "
                         "the failing pattern; a document not previously read is "
                         "the holding one.",
                         observed=f"correcting source {p.get('correcting_source_id')!r} "
                                  "is material already held, re-interpreted",
                         locator=str(p.get("correcting_source_id")),
                         opposite_would_be="a document retrieved for this correction "
                                           "and not previously read, as the Li 2019 "
                                           "CQVIP record was",
                         original=p.get("original_value"),
                         proposed=p.get("corrected_value"))
    if not p.get("states_what_original_got_right"):
        return make_fail(cid, inst,
                         "correction does not state what the original got right, so "
                         "a regression introduced by the fix would be invisible",
                         observed="states_what_original_got_right is absent",
                         locator=str(p.get("correcting_source_id")),
                         opposite_would_be="an explicit statement of which parts of "
                                           "the original the correction preserves")
    return make_pass(cid, inst,
                     observed=f"{p.get('original_value')!r} -> "
                              f"{p.get('corrected_value')!r}, original re-read at "
                              f"{p.get('original_source_id')}, corrected against "
                              f"{p.get('correcting_source_id')}",
                     locator=str(p.get("correcting_source_id")),
                     opposite_would_be="a correction sourced from the same instrument, "
                                       "or issued without re-reading the original")


CHK011 = Check(
    check_id="CHK011_CORRECTION_BURDEN",
    instrument=Instrument("correction-gate",
                          reads=("correcting_source_id", "original_source_id",
                                 "original_rechecked_at_source")),
    fn=_correction_burden,
    description="Corrections are less reliable than originals and must clear a "
                "higher bar.",
    must_fire_on=[Fixture(
        "eb022_rule_correcting_eb021_was_itself_wrong",
        {"original_value": "a bash zero is not a zero",
         "corrected_value": "the live toolchain is therefore sound",
         "original_source_id": "bash toolchain over F:\\E156",
         "correcting_source_id": "directory-Grep over the same mount",
         "original_rechecked_at_source": True,
         "states_what_original_got_right": True,
         "evidence_is_newly_retrieved_source": False},
        Verdict.FAIL,
        provenance="EB-022 -- 'THIS RULE IS UNSAFE AS WRITTEN AND HAS BEEN "
                   "MISLEADING RUNS FOR ~7 h. Sec 1 correctly convicted bash and "
                   "then wrongly acquitted the whole live toolchain.' The "
                   "correction re-interpreted the same mount instead of "
                   "retrieving a new source")],
    must_be_silent_on=[Fixture(
        "li2019_comparator_correction",
        {"original_value": "enalapril", "corrected_value": "benazepril",
         "original_source_id": "citation-string",
         "correcting_source_id": "CQVIP record via Chrome rendering",
         "original_rechecked_at_source": True,
         "states_what_original_got_right": True,
         "evidence_is_newly_retrieved_source": True},
        Verdict.PASS,
        provenance="report #3 breach 3 -- 'flipped the verdict from undetermined to "
                   "ineligible', a correction that held, made against a document "
                   "not previously read")],
    observation_terms={
        "original_rechecked_at_source": lambda p: _mut(p,
                                                       original_rechecked_at_source=False),
        "evidence_is_newly_retrieved_source": lambda p: _mut(
            p, evidence_is_newly_retrieved_source=False),
        "correcting_source_id": lambda p: _mut(
            p, correcting_source_id=p.get("original_source_id")),
    },
)


# =============================================================================
# CHK012 -- the observation must be in the same layer as the claim (PARTIAL)
# =============================================================================
# Incidents: a holdings table in a full-text hosting database read as an
# institutional entitlement -- this one reached the spine of a paper; a LibKey
# button rendering read as proof of delivery.
#
# HONEST LIMIT. This detector fires only when the two layers are labelled. The
# original error was a failure to notice that they were different layers at all,
# and no coverage criterion or vacuity sweep touches that. See BLIND SPOTS.

_LAYERS = ("holdings", "entitlement", "delivery")


def _layer_match(p: Mapping[str, Any]) -> Result:
    cid, inst = "CHK012_LAYER_MATCH", "claim-layer"
    claim, obs = p.get("claim_layer"), p.get("observation_layer")
    if claim not in _LAYERS or obs not in _LAYERS:
        return make_invalid(cid, inst,
                            f"claim_layer={claim!r} observation_layer={obs!r}: both "
                            f"must be one of {_LAYERS}. An unlabelled layer is the "
                            "condition under which this class of error occurs.")
    if claim != obs:
        return make_fail(cid, inst,
                         f"claim is about {claim!r} but the observation is of "
                         f"{obs!r}. These are different questions; a perfectly "
                         "sensitive check on the wrong one is still wrong.",
                         observed=f"{obs!r}-layer observation: {p.get('observed')!r}",
                         locator=str(p.get("locator")),
                         opposite_would_be=f"an observation drawn from the {claim!r} "
                                           "layer itself",
                         claim_layer=claim, observation_layer=obs)
    if not p.get("observed"):
        return make_invalid(cid, inst, f"no observation recorded in layer {claim!r}")
    return make_pass(cid, inst,
                     observed=f"{claim} layer observed: {p['observed']}",
                     locator=str(p.get("locator")),
                     opposite_would_be=f"an observation drawn from a different layer, "
                                       f"or no {claim} observation at all")


CHK012 = Check(
    check_id="CHK012_LAYER_MATCH",
    instrument=Instrument("claim-layer", reads=("claim_layer", "observation_layer",
                                                "observed")),
    fn=_layer_match,
    description="PARTIAL. Fires only when both layers are labelled.",
    must_fire_on=[Fixture(
        "holdings_read_as_entitlement",
        {"claim_layer": "entitlement", "observation_layer": "holdings",
         "observed": "title listed in host database holdings table",
         "locator": "holdings table"},
        Verdict.FAIL,
        provenance="a holdings table in a full-text hosting database read as an "
                   "institutional entitlement -- reached the spine of a paper")],
    must_be_silent_on=[Fixture(
        "delivery_witnessed_by_bytes",
        {"claim_layer": "delivery", "observation_layer": "delivery",
         "observed": "application/pdf, 1,284,113 bytes, sha256 3f9c…, 26 pages",
         "locator": "downloaded artefact"},
        Verdict.PASS,
        provenance="the compliant form -- delivery witnessed by the artefact, not by "
                   "a LibKey button rendering")],
    observation_terms={
        "observation_layer": lambda p: _mut(p, observation_layer="holdings"),
        "observed": lambda p: _mut(p, observed=None),
    },
)


# =============================================================================
# CHK013 -- a field's semantics must be read, not assumed
# =============================================================================

def _date_field(p: Mapping[str, Any]) -> Result:
    cid, inst = "CHK013_FIELD_SEMANTICS", "field-semantics"
    fld, sem = p.get("source_field"), dict(p.get("field_semantics") or {})
    if fld not in sem:
        return make_invalid(cid, inst,
                            f"field {fld!r} used without its documented semantics")
    if sem[fld] != p.get("target_semantics"):
        return make_fail(cid, inst,
                         f"field {fld!r} carries {sem[fld]!r}, the claim needs "
                         f"{p.get('target_semantics')!r}",
                         observed=f"{fld!r} documented as {sem[fld]!r}",
                         locator=f"{p.get('source')} :: {fld}",
                         opposite_would_be=f"{fld!r} documented as "
                                           f"{p.get('target_semantics')!r}",
                         field=fld, field_semantics=sem[fld])
    return make_pass(cid, inst,
                     observed=f"field {fld!r} documented as {sem[fld]!r}, matching the "
                              "quantity claimed",
                     locator=str(p.get("source")),
                     opposite_would_be=f"the field documented as anything other than "
                                       f"{p.get('target_semantics')!r}")


CHK013 = Check(
    check_id="CHK013_FIELD_SEMANTICS",
    instrument=Instrument("field-semantics", reads=("source_field", "field_semantics")),
    fn=_date_field,
    description="A database field is not the quantity its name suggests.",
    must_fire_on=[Fixture(
        "epub_date_used_as_publication_year",
        {"source": "bibliographic db", "source_field": "publication_date",
         "field_semantics": {"publication_date": "epub_ahead_of_print_date",
                             "print_date": "print_publication_year"},
         "target_semantics": "print_publication_year"},
        Verdict.FAIL,
        provenance="citation year corrected from a field returning the Epub date")],
    must_be_silent_on=[Fixture(
        "print_date_used_as_publication_year",
        {"source": "bibliographic db", "source_field": "print_date",
         "field_semantics": {"publication_date": "epub_ahead_of_print_date",
                             "print_date": "print_publication_year"},
         "target_semantics": "print_publication_year"},
        Verdict.PASS,
        provenance="the corrected form")],
    observation_terms={
        "source_field": lambda p: _mut(p, source_field="publication_date"),
        "field_semantics": lambda p: _mut(p, field_semantics={}),
    },
)


# =============================================================================
# CHK014 -- a filter must be verified to have fired  (registry P34, EC-001)
# =============================================================================
# EC-001, verbatim: "WebSearch accepts an `allowed_domains` parameter. It is
# silently ignored by this backend." A search restricted to EMA's own register
# "returns chrome and no products." Two "no EMA document exists" verdicts were
# reached through it -- and were discarded only because the lane distrusted them.
#
# This implements the registry's PROPOSED detector P34 as code:
#   "a domain filter must be verified to have fired by inspecting the returned
#    URLs, or the search is recorded as UNFILTERED. Never record a negative from
#    a filtered search whose filter was not confirmed."

def _filter_fired(p: Mapping[str, Any]) -> Result:
    cid, inst = "CHK014_FILTER_FIRED", "search-filter"
    declared = p.get("declared_filter")
    if not declared:
        return make_invalid(cid, inst, "no filter declared; nothing to verify")
    urls = list(p.get("returned_urls") or [])
    if not urls:
        return make_invalid(cid, inst,
                            f"filter {declared!r} declared but no returned URLs "
                            "were inspected. An unconfirmed filter is UNFILTERED, "
                            "and a negative from it is not a negative.")
    off = [u for u in urls if declared not in u]
    if off:
        return make_fail(cid, inst,
                         f"filter {declared!r} did not fire: {len(off)} of "
                         f"{len(urls)} returned URLs are outside it, e.g. {off[0]!r}",
                         observed=f"off-domain URLs returned: {off[:3]}",
                         locator=str(p.get("query")),
                         opposite_would_be=f"every returned URL within {declared!r}",
                         off_domain=off[:5])
    return make_pass(cid, inst,
                     observed=f"all {len(urls)} returned URLs lie within {declared!r}",
                     locator=str(p.get("query")),
                     opposite_would_be="a returned URL outside the declared domain, "
                                       "which is what a silently-ignored filter "
                                       "produces")


CHK014 = Check(
    check_id="CHK014_FILTER_FIRED",
    instrument=Instrument("search-filter", reads=("declared_filter", "returned_urls")),
    fn=_filter_fired,
    description="Registry P34. Never record a negative from a filtered search "
                "whose filter was not confirmed to have fired.",
    must_fire_on=[Fixture(
        "ema_domain_filter_silently_ignored",
        {"query": "site-restricted EMA register sweep",
         "declared_filter": "ema.europa.eu",
         "returned_urls": ["https://ema.europa.eu/en/medicines",
                           "https://www.drugs.com/monograph/x",
                           "https://pubmed.ncbi.nlm.nih.gov/12345"]},
        Verdict.FAIL,
        provenance="EC-001 -- allowed_domains silently ignored; two 'no EMA "
                   "document exists' verdicts reached through it")],
    must_be_silent_on=[Fixture(
        "domain_filter_confirmed",
        {"query": "site-restricted EMA register sweep",
         "declared_filter": "ema.europa.eu",
         "returned_urls": ["https://ema.europa.eu/en/medicines",
                           "https://ema.europa.eu/en/documents/assessment"]},
        Verdict.PASS,
        provenance="EC-001 -- the compliant form, URLs inspected")],
    observation_terms={
        "returned_urls": lambda p: _mut(p, returned_urls=[]),
        "declared_filter": lambda p: _mut(p, returned_urls=list(
            p.get("returned_urls", [])) + ["https://example.org/other"]),
    },
)


# =============================================================================
# CHK015 -- an implausible hit count means the query was discarded (P33, EC-002)
# =============================================================================
# EC-002, verbatim: the CJK query was translated by PubMed to '"meta"[Journal] OR
# "meta"[All Fields]' -- "every Chinese character was discarded" -- and returned
# 471,547 hits. "The non-English search never ran, and looked exactly as though
# it had."
#
# The registry states the detector inside the record: "THE DETECTOR IS THE HIT
# COUNT ITSELF: a hit count orders of magnitude above expectation means the query
# was discarded, not that it matched. A suspiciously large number is the same
# signal as a suspiciously round one."
#
# This is also the general form of `grep "1406"` matching 1009 of 1243 pages: a
# match rate approaching the corpus size is a statement about the pattern's
# degeneracy, not about the corpus.

def _hit_count_sanity(p: Mapping[str, Any]) -> Result:
    cid, inst = "CHK015_HIT_COUNT_SANITY", "query-plausibility"
    hits, expected = p.get("hits"), p.get("expected_order_of_magnitude")
    if hits is None or expected is None:
        return make_invalid(cid, inst,
                            "hit count or declared expectation missing. Without a "
                            "prior expectation any count looks reasonable.")
    corpus = p.get("corpus_size")
    if corpus and hits / corpus >= p.get("saturation_ratio", 0.5):
        return make_fail(cid, inst,
                         f"{hits} hits over a corpus of {corpus} "
                         f"({hits / corpus:.0%}) -- the pattern is degenerate, not "
                         "the corpus uniform",
                         observed=f"{hits}/{corpus} = {hits / corpus:.0%} of the "
                                  "corpus matched",
                         locator=str(p.get("query")),
                         opposite_would_be="a match rate well below the saturation "
                                           "threshold, i.e. a pattern that "
                                           "discriminates between documents",
                         hits=hits, corpus_size=corpus)
    if expected > 0 and hits >= expected * 100:
        return make_fail(cid, inst,
                         f"{hits} hits against a declared expectation of ~{expected} "
                         f"({hits / expected:.0f}x) -- consistent with the query "
                         "having been discarded rather than matched",
                         observed=f"{hits} hits vs declared expectation ~{expected}",
                         locator=str(p.get("query")),
                         opposite_would_be=f"a count within two orders of magnitude "
                                           f"of ~{expected}",
                         hits=hits, expected=expected)
    return make_pass(cid, inst,
                     observed=f"{hits} hits, within two orders of magnitude of the "
                              f"declared expectation ~{expected}",
                     locator=str(p.get("query")),
                     opposite_would_be="a count two or more orders of magnitude "
                                       "above expectation, or one saturating the "
                                       "corpus")


CHK015 = Check(
    check_id="CHK015_HIT_COUNT_SANITY",
    instrument=Instrument("query-plausibility",
                          reads=("hits", "expected_order_of_magnitude",
                                 "corpus_size")),
    fn=_hit_count_sanity,
    description="Registry P33. An implausible hit count is evidence the query was "
                "discarded, not that it matched.",
    must_fire_on=[Fixture(
        "pubmed_discarded_cjk_query",
        {"query": "CJK: heart failure meta-analysis carvedilol",
         "hits": 471547, "expected_order_of_magnitude": 100,
         "corpus_size": None},
        Verdict.FAIL,
        provenance="EC-002 -- 'every Chinese character was discarded' and the "
                   "search 'looked exactly as though it had' run")],
    must_be_silent_on=[Fixture(
        "plausible_hit_count",
        {"query": "sacubitril valsartan Chagas", "hits": 10,
         "expected_order_of_magnitude": 20, "corpus_size": None},
        Verdict.PASS,
        provenance="answer_hf_route_log.md -- Europe PMC REST query 'ANSWER-HF' "
                   "returned 10 hits, a plausible count that was then read")],
    observation_terms={
        "hits": lambda p: _mut(p, hits=(p.get("expected_order_of_magnitude") or 1)
                               * 5000),
        "expected_order_of_magnitude": lambda p: _mut(
            p, expected_order_of_magnitude=None),
    },
)


ALL_CHECKS = [CHK001, CHK002, CHK003, CHK004, CHK005, CHK006, CHK007, CHK008,
              CHK009, CHK010, CHK011, CHK012, CHK013, CHK014, CHK015]


def build_registry() -> Registry:
    from .probes_corpus import CORPUS_CHECKS
    from .probes_build import BUILD_CHECKS
    reg = Registry()
    for c in list(ALL_CHECKS) + list(CORPUS_CHECKS) + list(BUILD_CHECKS):
        reg.register(c)
    return reg
