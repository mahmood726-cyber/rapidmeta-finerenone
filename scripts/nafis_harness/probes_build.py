"""CHK026-CHK030 -- build-path and rendering defects. Plus CHK031, held out.

A NOTE ON VERIFICATION, BECAUSE IT IS THE POINT OF ALL THIS
-----------------------------------------------------------
I tried to verify the sentinel leak, the ARNI absence sentence and the DOAC card
against `F:\\rapidmeta-ssot-shell`. Three attempts: two bash scans timed out on
the mount and the third died on a tool failure, and a host `Grep` for
"NOT RECOVERABLE FROM THE PAGE" returned no files.

**That zero is recorded as UNVERIFIED, not as absence.** It is the exact case the
registry legislates for, twice:

    EB-021: "never use bash grep/find/cat/wc to establish a negative about
             F:\\E156. A bash zero is not a zero."
    EB-022: "...and that rule was itself wrong for ~7 hours. A directory-Grep
             zero is not a zero either." -- because a 20-second ripgrep timeout
             over a 265 MB network mount returns partial results with no
             truncation signal: "the result set is a function of clock speed,
             not of file content."

My mounts are also behind the corpus lane's working state, so the converted
pages carrying these defects may not exist here at all. Either way the honest
verdict is INVALID, and the fixtures below are marked [R] operator-relayed.
"""

from __future__ import annotations

import copy
import re
import unicodedata
from typing import Any, Mapping

from .check import Check, Fixture, Instrument
from .verdict import Result, Verdict, make_fail, make_invalid, make_pass


def _mut(payload: Mapping[str, Any], **changes) -> dict:
    d = copy.deepcopy(dict(payload))
    d.update(changes)
    return d


# =============================================================================
# CHK026 -- WRONG-REASON ABSENCE PANEL
# =============================================================================
# A page declaring a section absent FOR A REASON THAT IS FALSE OF THAT PAGE.
#
# "A panel stating the wrong reason for an absence is worse than a blank one:
#  the blank makes no claim, this makes a false one."
#
# That is the sharpest statement of the three-state principle anywhere in this
# project, and it is about rendering rather than checking. A blank panel is
# INVALID -- it asserts nothing. A panel carrying another page's rationale is a
# FAIL wearing the costume of a PASS.

def _wrong_reason_absence(p: Mapping[str, Any]) -> Result:
    cid, inst = "CHK026_WRONG_REASON_ABSENCE_PANEL", "absence-panel"
    reason_id = p.get("absence_reason_id")
    if not reason_id:
        return make_invalid(cid, inst,
                            "no absence reason recorded. A blank panel asserts "
                            "nothing and is not a defect; it is simply unfilled.")
    valid = p.get("reason_valid_for")
    if not valid:
        return make_invalid(cid, inst,
                            f"reason {reason_id!r} does not declare which page "
                            "provenances it is true of, so it cannot be checked "
                            "against this page")
    prov = p.get("page_provenance")
    if not prov:
        return make_invalid(cid, inst, "page provenance not recorded")
    if prov not in valid:
        return make_fail(cid, inst,
                         f"page provenance {prov!r} is not among {sorted(valid)}, so "
                         f"the rendered reason {reason_id!r} is false of this page",
                         observed=f"rendered: {str(p.get('reason_text'))[:180]!r} on a "
                                  f"{prov!r} page",
                         locator=str(p.get("page_id")),
                         opposite_would_be=f"a page whose provenance is one of "
                                           f"{sorted(valid)}, where that sentence is "
                                           "true",
                         page_provenance=prov, reason_valid_for=sorted(valid))
    return make_pass(cid, inst,
                     observed=f"reason {reason_id!r} is declared true of {prov!r} "
                              "pages and this page is one",
                     locator=str(p.get("page_id")),
                     opposite_would_be="the same sentence rendered on a page whose "
                                       "provenance is not in its valid set")


_ARNI_REASON = ("the included set was reconciled against published syntheses "
                "rather than produced by a database search")

CHK026 = Check(
    check_id="CHK026_WRONG_REASON_ABSENCE_PANEL",
    instrument=Instrument("absence-panel",
                          reads=("absence_reason_id", "reason_valid_for",
                                 "page_provenance")),
    fn=_wrong_reason_absence,
    description="An absence rationale must be true of the page rendering it.",
    must_fire_on=[Fixture(
        "arni_reason_on_a_converted_page",
        {"page_id": "CONVERTED_PAGE_07", "page_provenance": "converted",
         "absence_reason_id": "no-database-search",
         "reason_text": _ARNI_REASON,
         "reason_valid_for": ["authored-reconciliation"]},
        Verdict.FAIL,
        provenance="[R] corpus lane -- converted pages rendered ARNI's absence text, "
                   "true of ARNI and false of a converted page. Would have shipped "
                   "on 28 pages")],
    must_be_silent_on=[Fixture(
        "arni_reason_on_arni",
        {"page_id": "ARNI_HFREF", "page_provenance": "authored-reconciliation",
         "absence_reason_id": "no-database-search",
         "reason_text": _ARNI_REASON,
         "reason_valid_for": ["authored-reconciliation"]},
        Verdict.PASS,
        provenance="[F]-in-substance -- ARNI's included set really was reconciled "
                   "against published syntheses: 04_DEPARTURES.md and "
                   "08_REEXAMINATION_AND_REVISED_PRISMA.md in the search-and-"
                   "screening lane record exactly that process. Same sentence, same "
                   "instrument, opposite verdict -- it could fire and does not")],
    observation_terms={
        "page_provenance": lambda p: _mut(p, page_provenance="converted"),
        "reason_valid_for": lambda p: _mut(p, reason_valid_for=["something-else"]),
    },
)


# =============================================================================
# CHK027 -- SENTINEL LEAK INTO READER TEXT
# =============================================================================
# An internal marker rendered to a reader. Purely mechanical: the sentinel set is
# closed and known, so presence is decidable.
#
# The false-positive risk is prose that legitimately resembles a sentinel, which
# is why matching is on the EXACT sentinel token rather than on its words. The
# negative below is real corpus prose carrying uppercase status language that a
# looser matcher would flag.

def _sentinel_leak(p: Mapping[str, Any]) -> Result:
    cid, inst = "CHK027_SENTINEL_LEAK", "rendered-text"
    text = p.get("reader_text")
    sentinels = list(p.get("sentinels") or [])
    if text is None:
        return make_invalid(cid, inst, "no reader-visible text captured")
    if not sentinels:
        return make_invalid(cid, inst,
                            "no sentinel vocabulary declared; leakage is not "
                            "decidable without the closed set")
    found = {s: text.count(s) for s in sentinels if s in text}
    if found:
        total = sum(found.values())
        return make_fail(cid, inst,
                         f"{total} internal sentinel occurrence(s) in reader-visible "
                         f"text: {found}",
                         observed="; ".join(f"{s!r} x{n}" for s, n in
                                            sorted(found.items())),
                         locator=str(p.get("surface_id")),
                         opposite_would_be="reader text containing none of the "
                                           f"{len(sentinels)} declared sentinels",
                         occurrences=found)
    return make_pass(cid, inst,
                     observed=f"none of {len(sentinels)} declared sentinels appear in "
                              f"{len(text)} characters of reader text",
                     locator=str(p.get("surface_id")),
                     opposite_would_be="any declared sentinel appearing verbatim")


_SENTINELS = ["NOT RECOVERABLE FROM THE PAGE", "__PLACEHOLDER__", "TODO:",
              "{{", "NaN%", "undefined"]

CHK027 = Check(
    check_id="CHK027_SENTINEL_LEAK",
    instrument=Instrument("rendered-text", reads=("reader_text", "sentinels")),
    fn=_sentinel_leak,
    description="Internal markers must not reach a reader.",
    must_fire_on=[Fixture(
        "not_recoverable_sentinel_visible",
        {"surface_id": "converted-page-panel",
         "reader_text": "Per-arm counts: NOT RECOVERABLE FROM THE PAGE. "
                        "Denominators: NOT RECOVERABLE FROM THE PAGE.",
         "sentinels": _SENTINELS},
        Verdict.FAIL,
        provenance="[R] corpus lane -- 'NOT RECOVERABLE FROM THE PAGE' visible nine "
                   "times. NOT verifiable in my mount: two bash scans timed out and "
                   "a host Grep returned nothing, which per EB-022 is not a zero")],
    must_be_silent_on=[Fixture(
        "answer_hf_prose_with_uppercase_status_words",
        {"surface_id": "answer_hf_route_log",
         "reader_text": "Status as of 12 August 2026: NOT YET OBTAINED. Route list "
                        "NOT EXHAUSTED - one strong lead open. CLOSED with a "
                        "definitive negative. The counts are not obtainable through "
                        "any open mechanism.",
         "sentinels": _SENTINELS},
        Verdict.PASS,
        provenance="[F] answer_hf_route_log.md -- real reader-visible prose using "
                   "uppercase status language ('NOT YET OBTAINED', 'CLOSED') and the "
                   "words 'not obtainable'. A word-based matcher would fire on this; "
                   "exact-token matching must not")],
    observation_terms={
        "reader_text": lambda p: _mut(
            p, reader_text=p["reader_text"] + " NOT RECOVERABLE FROM THE PAGE"),
        "sentinels": lambda p: _mut(p, sentinels=[]),
    },
)


# =============================================================================
# CHK028 -- DISQUALIFIED REFERENT PROMOTED TO SOURCE
# =============================================================================
# An extractor object contradicting a card that carries a source citation.
# The sourced value wins, and the conflict is a HARD BLOCK, not a warning --
# because the object in question had already been disqualified as a referent.

def _disqualified_referent(p: Mapping[str, Any]) -> Result:
    cid, inst = "CHK028_DISQUALIFIED_REFERENT_PROMOTED", "card-vs-object"
    card, obj = p.get("card") or {}, p.get("object") or {}
    if not card or not obj:
        return make_invalid(cid, inst, "card or object value missing")
    if not card.get("source_citation"):
        return make_invalid(cid, inst,
                            "the card carries no source citation, so the "
                            "sourced-value-wins rule cannot be applied. This is a "
                            "plain conflict, not a promotion, and needs adjudication "
                            "elsewhere.")
    same_measure = card.get("measure") == obj.get("measure")
    same_value = card.get("value") == obj.get("value")
    if not (same_measure and same_value):
        return make_fail(cid, inst,
                         f"object {obj.get('measure')} {obj.get('value')} conflicts "
                         f"with source-verified card {card.get('measure')} "
                         f"{card.get('value')}"
                         + (" and the object is already disqualified as a referent"
                            if p.get("object_disqualified") else "")
                         + ". HARD BLOCK: the sourced value wins.",
                         observed=f"card {card.get('measure')}={card.get('value')} "
                                  f"[{card.get('source_citation')}] vs object "
                                  f"{obj.get('measure')}={obj.get('value')}",
                         locator=str(p.get("claim_id")),
                         opposite_would_be="the object agreeing with the card on both "
                                           "measure and value",
                         card=card, object=obj,
                         object_disqualified=bool(p.get("object_disqualified")))
    return make_pass(cid, inst,
                     observed=f"object and source-verified card agree: "
                              f"{card.get('measure')}={card.get('value')} "
                              f"[{card.get('source_citation')}]",
                     locator=str(p.get("claim_id")),
                     opposite_would_be="the object differing from the card in measure "
                                       "or in value")


CHK028 = Check(
    check_id="CHK028_DISQUALIFIED_REFERENT_PROMOTED",
    instrument=Instrument("card-vs-object", reads=("card", "object")),
    fn=_disqualified_referent,
    description="A sourced card outranks an extractor object. Conflict is a block.",
    must_fire_on=[Fixture(
        "doac_cancer_vte_object_contradicts_sourced_card",
        {"claim_id": "DOAC_CANCER_VTE",
         "card": {"measure": "HR", "value": 0.55,
                  "source_citation": "publication-verified"},
         "object": {"measure": "OR", "value": 0.7290},
         "object_disqualified": True},
        Verdict.FAIL,
        provenance="[R] corpus lane -- five pages whose extractor object contradicts "
                   "a source-verified card; this object was already disqualified as "
                   "a referent the same morning")],
    must_be_silent_on=[Fixture(
        "parachute_hf_card_and_object_agree",
        {"claim_id": "PARACHUTE-HF-composite",
         "card": {"measure": "HR", "value": 0.91,
                  "source_citation": "JAMA 2026;335(1):49-59 Table 2 via PMC12676478"},
         "object": {"measure": "HR", "value": 0.91}},
        Verdict.PASS,
        provenance="[F] 13_ERROR_LIBRARY.md N1 -- HR 0.91 (0.73-1.13) read from "
                   "Table 2. A real sourced card that could have conflicted")],
    observation_terms={
        "object": lambda p: _mut(p, object={**p["object"], "value": 9.99}),
        "card": lambda p: _mut(p, card={**p["card"], "source_citation": None}),
    },
)


# =============================================================================
# CHK029 -- NON-ASCII MINUS DEFEATING A COMPARISON
# =============================================================================
# "A comparison that silently mis-signs a number is worse than one that fails."
#
# The lane reported 7 conflicts; 2 were its own regex matching only ASCII '-',
# so &minus;71.31 read as +71.31. Normalisation must apply to a LEADING SIGN and
# must NOT rewrite an en-dash used as a RANGE SEPARATOR -- "0.73-1.13" with an
# en-dash is an interval, not a negative number. That is the false positive this
# check has to avoid, and the negative fixture is exactly that case.

_SIGN_CHARS = {
    "\u2212": "-",   # MINUS SIGN
    "\u2013": "-",   # EN DASH
    "\u2012": "-",   # FIGURE DASH
    "\u2014": "-",   # EM DASH
    "\u2796": "-",   # HEAVY MINUS SIGN
    "\uFF0D": "-",   # FULLWIDTH HYPHEN-MINUS
}
_NUM = re.compile(r"^-?\d+(?:\.\d+)?$")


def normalise_signed_number(raw: str):
    """Return a float if `raw` is a single signed number, else None.

    Entity form (&minus;) is decoded first. Only a LEADING dash-like character is
    treated as a sign; an internal one is a separator and makes this not a
    scalar, so the function returns None rather than guessing.
    """
    if raw is None:
        return None
    s = str(raw).strip()
    s = s.replace("&minus;", "\u2212").replace("&ndash;", "\u2013")
    s = unicodedata.normalize("NFKC", s)
    if s and s[0] in _SIGN_CHARS:
        s = "-" + s[1:]
    # any remaining dash-like character is internal -> a range, not a scalar
    if any(ch in _SIGN_CHARS for ch in s):
        return None
    return float(s) if _NUM.match(s) else None


def _sign_normalisation(p: Mapping[str, Any]) -> Result:
    cid, inst = "CHK029_SIGN_NORMALISATION", "numeric-parse"
    raw = p.get("raw")
    if raw is None:
        return make_invalid(cid, inst, "no raw string captured")
    if "naive_value" not in p:
        return make_invalid(cid, inst,
                            "no naive parse recorded; there is nothing to compare "
                            "the normalised parse against")
    correct = normalise_signed_number(raw)
    naive = p.get("naive_value")

    if correct is None:
        if naive is None:
            return make_pass(cid, inst,
                             observed=f"{raw!r} is not a scalar and was not parsed as "
                                      "one (internal dash treated as a separator)",
                             locator=str(p.get("field_id")),
                             opposite_would_be="an internal dash silently read as a "
                                               "sign, turning a range into a negative")
        return make_fail(cid, inst,
                         f"{raw!r} is not a single signed number, but was parsed as "
                         f"{naive!r}",
                         observed=f"raw={raw!r} naive={naive!r} normalised=not-a-scalar",
                         locator=str(p.get("field_id")),
                         opposite_would_be="the parser declining a non-scalar, as "
                                           "normalisation does")

    if naive is None or abs(float(naive) - correct) > 1e-12:
        mis_signed = naive is not None and correct == -float(naive)
        return make_fail(cid, inst,
                         f"{raw!r} parses to {correct} after sign normalisation but "
                         f"was read as {naive!r}"
                         + (" -- the sign is inverted" if mis_signed else ""),
                         observed=f"raw={raw!r} naive={naive!r} normalised={correct}",
                         locator=str(p.get("field_id")),
                         opposite_would_be="the naive parse agreeing with the "
                                           "normalised parse to within 1e-12",
                         naive=naive, normalised=correct, sign_inverted=mis_signed)

    return make_pass(cid, inst,
                     observed=f"{raw!r} parses to {correct} both naively and after "
                              "sign normalisation",
                     locator=str(p.get("field_id")),
                     opposite_would_be="a normalised parse differing from the naive "
                                       "one, e.g. a Unicode minus read as positive")


CHK029 = Check(
    check_id="CHK029_SIGN_NORMALISATION",
    instrument=Instrument("numeric-parse", reads=("raw", "naive_value")),
    fn=_sign_normalisation,
    description="Normalise Unicode sign characters before any numeric comparison.",
    must_fire_on=[Fixture(
        "html_entity_minus_read_as_positive",
        {"field_id": "mean_difference", "raw": "&minus;71.31", "naive_value": 71.31},
        Verdict.FAIL,
        provenance="[R] corpus lane -- 2 of 7 reported conflicts were the lane's own "
                   "ASCII-only regex reading &minus;71.31 as +71.31")],
    must_be_silent_on=[Fixture(
        "ascii_minus_same_value",
        {"field_id": "mean_difference", "raw": "-71.31", "naive_value": -71.31},
        Verdict.PASS,
        provenance="[R] corpus lane -- the same value in the encoding that worked. "
                   "Both encodings of one number, as required")],
    observation_terms={
        "raw": lambda p: _mut(p, raw="\u221271.31", naive_value=71.31),
        "naive_value": lambda p: _mut(p, naive_value=999.0),
    },
)


# =============================================================================
# CHK030 -- BUILD-MODE-BLIND TEXT (the general form of CHK026)
# =============================================================================
# Any string asserting WHY something is true must be conditioned on the path that
# produced it.
#
# HONEST NOTE, and it is in FIXTURE_STATUS too: this detector's positive is THE
# SAME INCIDENT as CHK026's, viewed generally. It has no independent positive.
# Two detectors firing on one incident inflates apparent coverage, so the
# duplication is declared rather than left to be discovered.

def _build_mode_blind(p: Mapping[str, Any]) -> Result:
    cid, inst = "CHK030_BUILD_MODE_BLIND_TEXT", "assertion-conditioning"
    if not p.get("asserts_rationale"):
        return make_pass(cid, inst,
                         observed=f"string {p.get('string_id')!r} asserts no "
                                  "rationale, so no conditioning is required",
                         locator=str(p.get("string_id")),
                         opposite_would_be="a string asserting why something is true "
                                           "without declaring the paths it holds on")
    valid = p.get("valid_for_paths")
    path = p.get("build_path")
    if not path:
        return make_invalid(cid, inst, "build path not recorded")
    if valid is None:
        return make_fail(cid, inst,
                         f"string {p.get('string_id')!r} asserts a rationale but "
                         "declares no build paths it is valid for: it will render "
                         "identically down every path, including the ones it is "
                         "false on",
                         observed=f"text: {str(p.get('text'))[:160]!r}; "
                                  "valid_for_paths is unset",
                         locator=str(p.get("string_id")),
                         opposite_would_be="an explicit set of build paths the "
                                           "rationale holds on")
    if path not in valid:
        return make_fail(cid, inst,
                         f"rationale is declared valid for {sorted(valid)} but this "
                         f"build took path {path!r}",
                         observed=f"build_path={path!r} not in {sorted(valid)}",
                         locator=str(p.get("string_id")),
                         opposite_would_be=f"a build path within {sorted(valid)}")
    return make_pass(cid, inst,
                     observed=f"rationale declared valid for {sorted(valid)} and this "
                              f"build took {path!r}",
                     locator=str(p.get("string_id")),
                     opposite_would_be="a build path outside the declared set, or no "
                                       "declared set at all")


CHK030 = Check(
    check_id="CHK030_BUILD_MODE_BLIND_TEXT",
    instrument=Instrument("assertion-conditioning",
                          reads=("asserts_rationale", "valid_for_paths",
                                 "build_path")),
    fn=_build_mode_blind,
    description="A rationale string must declare the build paths it holds on.",
    must_fire_on=[Fixture(
        "unconditioned_rationale_string",
        {"string_id": "absence-rationale-no-database-search",
         "text": _ARNI_REASON, "asserts_rationale": True,
         "valid_for_paths": None, "build_path": "convert"},
        Verdict.FAIL,
        provenance="[R] corpus lane -- SAME INCIDENT as CHK026, generalised. This "
                   "detector has NO INDEPENDENT POSITIVE and that is declared, not "
                   "discovered")],
    must_be_silent_on=[Fixture(
        "conditioned_rationale_string",
        {"string_id": "absence-rationale-no-database-search",
         "text": _ARNI_REASON, "asserts_rationale": True,
         "valid_for_paths": ["author"], "build_path": "author"},
        Verdict.PASS,
        provenance="[R] corpus lane -- the same string once conditioned on its path")],
    observation_terms={
        "valid_for_paths": lambda p: _mut(p, valid_for_paths=None),
        "build_path": lambda p: _mut(p, build_path="convert"),
    },
)


BUILD_CHECKS = [CHK026, CHK027, CHK028, CHK029, CHK030]


# =============================================================================
# CHK031 -- SEARCH RECALL. WRITTEN, AND DELIBERATELY NOT REGISTERED.
# =============================================================================
# Re-run a review's stated search and confirm it retrieves the studies the review
# says it included.
#
# WHY IT IS NOT IN THE REGISTRY
# -----------------------------
# It has no real positive, and I will not construct one. The corpus is explicit,
# and it is the most-repeated caveat in the whole record:
#
#   report #6 Sec 6:  "(a) Search breadth: 0 [confirmed]"  against 22 checking
#                     failures. "Twenty-two to zero."
#   report #6 Sec 9:  "Zero breadth failures remains NOT YET CAUGHT, with both
#                      instruments field-internal."
#   report #3 Sec 6:  "Hunt a breadth failure deliberately -- still 0 confirmed."
#
# So the class this detector exists for has never once been observed in our own
# work. Registering it on a constructed positive would make it a detector that
# has never been demonstrated firing on anything real -- M11, the unfired rule,
# which is the mechanism `Registry.register` exists to refuse.
#
# Mahmood expects it to fail at a measurable rate on PUBLISHED reviews, and that
# is the right first use: the positive should come from someone else's review,
# found by running this, and then it can be registered. Until then it lives here,
# executable and unadmitted.
#
# `Registry.register(CHK031)` raises InadmissibleDetector today. That is the
# admission rule working on its author, and there is a test asserting it.

def search_recall(p: Mapping[str, Any]) -> Result:
    cid, inst = "CHK031_SEARCH_RECALL", "search-rerun"
    included = set(p.get("included_study_ids") or [])
    retrieved = p.get("retrieved_ids")
    if not included:
        return make_invalid(cid, inst, "no included study identifiers recorded")
    if retrieved is None:
        return make_invalid(cid, inst,
                            "the stated search was not re-run, so recall is unknown. "
                            "Not re-running it is not the same as it passing.")
    retrieved = set(retrieved)
    missed = sorted(included - retrieved)
    if missed:
        return make_fail(cid, inst,
                         f"the review's own stated search does not retrieve "
                         f"{len(missed)} of its {len(included)} included studies: "
                         f"{missed[:6]}",
                         observed=f"|included|={len(included)} "
                                  f"|retrieved|={len(retrieved)} "
                                  f"|included\\retrieved|={len(missed)}",
                         locator=str(p.get("review_id")),
                         opposite_would_be="every included study appearing in the "
                                           "re-run of the review's own search string",
                         missed=missed)
    return make_pass(cid, inst,
                     observed=f"all {len(included)} included studies are retrieved by "
                              "the review's stated search",
                     locator=str(p.get("review_id")),
                     opposite_would_be="an included study the review's own search "
                                       "cannot find")


CHK031_UNREGISTERED = Check(
    check_id="CHK031_SEARCH_RECALL",
    instrument=Instrument("search-rerun",
                          reads=("included_study_ids", "retrieved_ids")),
    fn=search_recall,
    description="HELD OUT -- no real positive exists in our corpus (breadth "
                "failures confirmed: 0). Register it when a published review "
                "supplies one.",
    must_fire_on=[],          # deliberately empty -- this is what blocks admission
    must_be_silent_on=[Fixture(
        "arni_search_retrieves_its_own_included_set",
        {"review_id": "ARNI-HFREF",
         "included_study_ids": ["NCT01035255", "NCT02554890"],
         "retrieved_ids": ["NCT01035255", "NCT02554890", "NCT01920711"]},
        Verdict.PASS,
        provenance="[F] search-and-screening/01_SEARCH_CAPTURE.md + "
                   "02_CORPUS_AND_SCREENING.tsv -- a captured search and its "
                   "screened corpus. The negative exists; the positive does not")],
    observation_terms={
        "retrieved_ids": lambda p: _mut(p, retrieved_ids=[]),
    },
)


FIXTURE_STATUS = {
    "CHK026_WRONG_REASON_ABSENCE_PANEL": {
        "positive": "[R]", "negative": "[F]-in-substance",
        "negative_strength": "STRONG",
        "note": "ARNI's reconciliation-not-search process is file-backed in "
                "04_DEPARTURES.md and 08_REEXAMINATION_AND_REVISED_PRISMA.md, so "
                "the sentence really is true of ARNI. Same sentence, same "
                "instrument, opposite verdict."},
    "CHK027_SENTINEL_LEAK": {
        "positive": "[R] UNVERIFIED IN MOUNT", "negative": "[F]",
        "negative_strength": "STRONG",
        "note": "Positive not confirmable here: two bash scans timed out and a host "
                "Grep returned nothing, which per EB-022 is NOT a zero. The negative "
                "is real reader-visible prose from answer_hf_route_log.md carrying "
                "'NOT YET OBTAINED' and 'not obtainable' -- a word-based matcher "
                "fires on it, exact-token matching does not."},
    "CHK028_DISQUALIFIED_REFERENT_PROMOTED": {
        "positive": "[R]", "negative": "[F]",
        "negative_strength": "STRONG",
        "note": "PARACHUTE-HF's HR 0.91 with its JAMA Table 2 citation is a real "
                "sourced card that could have conflicted with its object."},
    "CHK029_SIGN_NORMALISATION": {
        "positive": "[R]", "negative": "[R]",
        "negative_strength": "MODERATE",
        "note": "Both encodings of one number, as asked. The stronger stress case -- "
                "an en-dash RANGE ('0.73-1.13') that must not become a negative -- "
                "is covered by a unit test rather than a fixture, because I have no "
                "corpus row that pairs a range with a naive parse."},
    "CHK030_BUILD_MODE_BLIND_TEXT": {
        "positive": "[R] NOT INDEPENDENT", "negative": "[R]",
        "negative_strength": "WEAK",
        "note": "*** Its positive is the SAME INCIDENT as CHK026's, generalised. "
                "This detector has no independent positive, and two detectors "
                "firing on one incident inflates apparent coverage. *** The "
                "negative is the same string once conditioned, which is a "
                "restatement of the positive rather than an independent case."},
    "CHK031_SEARCH_RECALL": {
        "positive": "NONE -- DETECTOR HELD OUT OF THE REGISTRY",
        "negative": "[F]",
        "negative_strength": "MODERATE",
        "note": "*** The only class here with NO POSITIVE AT ALL. *** Confirmed "
                "search-breadth failures in our corpus: 0, against 22 checking "
                "failures (report #6 Sec 6). Registering it on a constructed "
                "positive would make it an unfired rule -- M11 -- so "
                "Registry.register raises on it today, by design."},
}
