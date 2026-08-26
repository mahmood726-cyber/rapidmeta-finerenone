# Name vs Predicate Audit

Scope: literal top-level `ssot/*.py` and `scripts/*.py`.

Files examined: 582 Python files.
Functions examined: 2,278 AST function definitions.
Semantic name/docline candidates triaged: 207.
Parse failures: 0.

Flagged defects: 17.
Self-disclosed presence-only checks: 9.

Empty categories: no defect is reported for checks that actually compared the candidate value against a source record, declared vocabulary, registered section list, staged payload, or computed quantity. No nested `scripts/*/*.py` files were in scope.

## Flagged Defects

Ranked by how easily a false pass could occur in real project data.

| Rank | File:line | Function or gate | Semantic word | Actual predicate | Concrete false pass |
|---:|---|---|---|---|---|
| 1 | `ssot/preconditions.py:119` | `population_stated` | `stated` | Reads `question`, falls back to `title`, and passes if the selected field is readable/non-empty. | `question = "Number of participants with first occurrence of four component major adverse cardiovascular events (MACE)..."` passes although it states an outcome measure, not the participant population. |
| 2 | `ssot/build_to_standard.py:630` | `build()` property `P8_registration_identity` | `verified` | Copies input trial `nct` values into `registration_identity.trials`, sets `verified: True`, and constructs a ClinicalTrials.gov URL; no fetch or registry comparison. | `{"inputs":{"trials":[{"nct":"NCT99999999","name":"SELECT-D"}]}}` becomes a live-verified registration identity even if the NCT is wrong or nonexistent. |
| 3 | `scripts/seed_ledger.py:31` | `auto_state` | `verified` | Regex-finds embedded `realData` blocks and records cells when required fields are present/non-null. | `tE:999999, tN:10, cE:0, cN:10, publishedHR:"banana", pmid:"12345678"` is recorded as a verified cell despite impossible counts and invalid effect content. |
| 4 | `ssot/preconditions.py:189` | `comparators_identified` | `identified` | Requires each outcome to have readable `comparator` and `comparator_type`; `"mixed"` is accepted by self-label. | `{"comparator":"placebo","comparator_type":"placebo"}` passes for a trial whose actual comparator arm is usual care. |
| 5 | `ssot/preconditions.py:353` | `criteria_stated` | `stated` | Passes if `screening.eligibility` is readable/non-empty. | `screening.eligibility = "Included studies were selected as clinically appropriate."` passes without stating usable inclusion criteria. |
| 6 | `ssot/preconditions.py:374` | `criteria_predefined` | `predefined` | Passes when `screening.eligibility_provenance.predefined` is exactly `True`; no protocol, timestamp, or source comparison. | `{"predefined": true, "state": "derived after reading the included trials"}` passes as predefined. |
| 7 | `ssot/assessment.py:302` | `inclusion_criteria_auditable` | `auditable` | Passes if `screening.eligibility` is readable/non-empty. | `screening.eligibility = "See included studies."` passes although there is nothing auditable. |
| 8 | `ssot/build_to_standard.py:433` | `build()` property `P3_inclusion_criteria` | `predefined` | Marks the property held when an eligibility provenance object exists and has a `predefined` key. | `{"screening":{"eligibility_provenance":{"predefined":"yes"}}}` passes with no protocol evidence and no criteria content. |
| 9 | `ssot/build_to_standard.py:598` | `build()` property `P7_published_comparison` | `stated` | Marks held when `published_comparison.denominator` or `published_comparison.checks` is non-empty. | `{"published_comparison":{"denominator":{"rows_checked":1},"checks":[{"verdict":"CONFIRMED"}]}}` passes even if the denominator and check were invented. |
| 10 | `ssot/build_to_standard.py:534` | `build()` property `P5_extraction_table` | `verbatim` | Counts extraction cells whose `label` is `READ`; does not require or resolve source path or verbatim text. | `{"extraction":{"cells":[{"field":"effect","label":"READ","value":"HR 0.87"}]}}` passes without a source path or quoted source text. |
| 11 | `ssot/build_to_standard.py:547` | `build()` property `P6_analysis_output` | `verbatim` | Marks held if `r_output.verbatim` is non-empty. | `{"r_output":{"verbatim":"metafor output ok"}}` passes even if the text is hand-written and not model output. |
| 12 | `scripts/partition_corpus.py:53` | `trial_has_provenance` | `provenance` | Requires a 6-8 digit PMID-shaped value plus either an NCT-shaped key or an HTTP `sourceUrl`. | `key="NCT01234567", pmid="12345678", sourceUrl="https://example.com/wrong-paper"` passes without proving the URL or PMID supports that trial. |
| 13 | `scripts/regression_guard.py:98` | `_removals_declared` | `declared` | Treats a removal as accounted for when `criterion`, `evidence`, and `adjudicated_by` are non-blank. | `{"key":"app::trial::NCT01234567","criterion":"wrong disease","evidence":"looked wrong","adjudicated_by":"MA"}` justifies a lost key without evidence verification. |
| 14 | `scripts/audit_40_checks.py:531` | `check_37_inconsistent_drug_name` | `inconsistent` | Passes when the first token of the stem appears anywhere in the page text. | A page named `SGLT2_EBOLA_REVIEW.html` passes if `sglt2` appears once in a hidden script or comment while the visible review is about Ebola. |
| 15 | `ssot/assessment.py:228` | `handbook_authority_is_verified` | `verified` | Passes when `HANDBOOK_AUTHORITY.version`, `sections`, and `verified_on` are all non-`None`. | `{"version":"6.5","sections":"23.999 invented","verified_on":"2026-08-19"}` passes as verified authority. |
| 16 | `ssot/preconditions.py:86` | `verdict_is_publishable` | `publishable` / `verified` | Passes when `handbook_authority_is_verified()` is true and `SECTION_VERIFIED_ON` is non-`None`. | Bogus Handbook metadata plus `SECTION_VERIFIED_ON = "2026-08-19"` passes publishability without validating the cited authority. |
| 17 | `ssot/invariants.py:44` | `cache_is_valid` | `valid` | Passes when a path exists and file size is greater than zero. | A non-empty truncated cache file containing `{bad` or `xxxxx` passes as valid. |

## Self-Disclosed Presence-Only Checks

These are not counted as defects because the name/docstring/comment explicitly narrows the claim to presence, shape, or a limited gate, or says it does not establish correctness.

| File:line | Function or gate | Semantic word | Disclosed narrow predicate | Concrete false pass |
|---|---|---|---|---|
| `ssot/preconditions.py:148` | `arm_role_resolved` | `resolved` | Decorator text says the gate only reads whether a role field is populated; body checks readable/non-blank arm roles. | Roles `experimental` and `experimental`, or `banana` and `controlish`, pass despite not resolving the treatment/control contrast. |
| `ssot/preconditions.py:297` | `estimand_named` | `named` | Docstring says the gate asks only whether a quantity is named at all and leaves identity to `estimand_identity.compare`. | `estimand = "risk ratio"` passes for a continuous mean-difference endpoint. |
| `ssot/assessment.py:359` | `require_named_intervention` | `named` | Query wrapper raises on blank intervention before registry search; it emits no PASS verdict. | `intervention = "therapy"` passes the non-blank requirement without naming a specific intervention. |
| `ssot/projectors.py:175` | `_attested` | `attested` | Docstring defines attestation presence as naming a person, source, and date. | `{"by":"MA","source_checked_against":"the internet","date_utc":"2026-08-19"}` passes without proving any check occurred. |
| `scripts/r_validate_common.py:107` | `validate_index_entry` | `valid` | Docstring says this is a minimal schema check on `_index.json` entries. | `{"stem":"wrong-review","has_realData":true}` passes while pointing to the wrong analysis. |
| `scripts/r_validate_common.py:115` | `validate_r_output` | `valid` | Docstring says this is a minimal schema check on R wrapper output JSON. | `{"fit_ok":true,"engine":"metafor"}` passes with no estimates, call, or provenance. |
| `scripts/ssot_signals.py:128` | `_declared_absent` | `declared` | Nearby comments disclose a minimum-character reason threshold for declared absence. | A 60-character filler string in `.absent-state` passes as a reason. |
| `scripts/identity_by_registration_gate.py:38` | `check` | `identity` | Module docstring says full pass does not establish the NCT is real or the right trial, only well-formed/unique/not contradictory to optional known acronyms. | `{"nct":"NCT99999999","name":"SELECT-D"}` passes when no `known` mapping is supplied. |
| `ssot/validate_v2.py:2894` | `check_handbook_citation` | `citation` / `governing` | Docstring says it does not adjudicate whether the decision genuinely follows the section; it checks existence, plausible section shape, and local registration. | A locally registered but wrong Handbook section can pass citation plausibility. |

## Notes On Non-Findings

Dedicated source-backed gates inspected but not counted included `scripts/declared_contrast_gate.py`, `scripts/estimand_definition_gate.py`, `scripts/subject_match_gate.py`, `scripts/protocol_subject_gate.py`, `scripts/subject_is_experimental_gate.py`, `scripts/arm_identity_gate.py`, `scripts/count_provenance_gate.py`, `scripts/registration_identity_gate.py`, and `scripts/verify_then_write_provenance.py`; their semantic predicates compare against source content, declared vocabularies, or computed quantities.

Several semantic detectors in `ssot/validate_v2.py` were also not counted because they compare to staged source payloads, registered source IDs, source-category bindings, or computed `k` values rather than only checking presence.

The disabled `scripts/audit_40_checks.py:412` function `check_26_inconsistent_acronyms` is not counted because it currently returns no findings rather than implementing a presence-only predicate.
