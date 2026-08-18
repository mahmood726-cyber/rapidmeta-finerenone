# Vacuity Sweep - 2026-08-19 Corpus

Scope: source-only survey in `F:/rapidmeta-ssot-shell`; no network.

## How I Found The Checks

- Scanned `ssot/**/*.py`, `scripts/**/*.py`, and `.githooks/**` with an AST/name-pattern sweep. Files considered: 597. Parse failures: 1.
- Expanded runtime registries rather than relying on names alone: 30 NAFIS checks, 8 registered preconditions, and 41 `validate_v2.DETECTORS`.
- Total row count reported below: 364. This deliberately includes static candidates whose runtime applicability is UNKNOWN, because reporting UNKNOWN is safer than silently treating them as sound.

Parse failures from the static sweep:
- `scripts/audit_structural.py: SyntaxError: invalid escape sequence '\s' (<unknown>, line 6)`

## Calibration

- `ctgov_transport.require_raw_v2()` is the reference transport pattern: it asserts `protocolSection.armsInterventionsModule` and raises `WrongPayloadShape` before role reading.
- Current `ssot/preconditions.py` registers eight preconditions, not seven: the source says `inclusion_criteria_auditable` split into `criteria_stated` and `criteria_predefined` on 2026-08-19. All eight were scored shape-asserting because they route reads through `assessment.read`/`judge` or explicit `read_scalar`, and `contributes_a_randomised_contrast` refuses unknown arm-role vocabulary.
- Precondition corpus run: 137 candidate directories, 135 readable objects, 2 absent pseudo-topics. Batch1 known-answer comparison matched: True.

## Main Ranking: Measured PASS-Style Gaps

This ranking includes only checks/gates where this sweep measured both emissions and adjudications and the gap can surface as a clean/pass-style result. Explicit NOT_ASSESSABLE or INVALID gaps are listed separately below, because those are not the CHK024 failure shape.

| rank | check | emissions | adjudicated | gap | pass-without-predicate? | note |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | NAFIS aggregate gate: harness_gate aggregate process PASS | 302 | 294 | 8 | yes at process level: exits 0 while child INVALID results are present | process exit 0 with child INVALID results below the ceiling |
| 2 | NAFIS CHK registry: CHK021_MEASURE_SCALE_MISMATCH | 70 | 65 | 5 | yes | 5 vacuous PASSes on RATE_RATIO/WIN_RATIO rows in iv-iron-hf |

Measured non-pass gaps, retained so the emissions/adjudications accounting is visible:

| rank | check | emissions | adjudicated | gap | state |
| --- | --- | --- | --- | --- | --- |
| 1 | registered precondition: eligibility_met | 137 | 0 | 137 | explicit NOT_ASSESSABLE/INVALID, not PASS |
| 2 | registered precondition: criteria_predefined | 137 | 36 | 101 | explicit NOT_ASSESSABLE/INVALID, not PASS |
| 3 | registered precondition: criteria_stated | 137 | 42 | 95 | explicit NOT_ASSESSABLE/INVALID, not PASS |
| 4 | registered precondition: arm_role_resolved | 137 | 49 | 88 | explicit NOT_ASSESSABLE/INVALID, not PASS |
| 5 | registered precondition: contributes_a_randomised_contrast | 137 | 49 | 88 | explicit NOT_ASSESSABLE/INVALID, not PASS |
| 6 | registered precondition: comparators_identified_and_consistent | 137 | 74 | 63 | explicit NOT_ASSESSABLE/INVALID, not PASS |
| 7 | NAFIS CHK registry: CHK016_PRECISION_SAMPLE_MISMATCH | 38 | 35 | 3 | explicit NOT_ASSESSABLE/INVALID, not PASS |
| 8 | registered precondition: estimand_named | 137 | 135 | 2 | explicit NOT_ASSESSABLE/INVALID, not PASS |
| 9 | registered precondition: population_stated | 137 | 135 | 2 | explicit NOT_ASSESSABLE/INVALID, not PASS |

## Current NAFIS Corpus Measurement

`build-artefacts/*.json`: 115 artefacts, 302 emissions, 294 adjudicated, 294 PASS, 0 FAIL, 8 INVALID.

CHK021 vacuous examples:
- `build-artefacts/iv-iron-hf.json` `NCT02937454::hfh_cvd_recurrent` terms=['back_transform', 'stored_scale']: PASS is vacuous -- verdict survived forcing back_transform, stored_scale to its flipping value, so the check does not depend on the term it claims to observe
- `build-artefacts/iv-iron-hf.json` `NCT02937454::hfh_recurrent` terms=['back_transform', 'stored_scale']: PASS is vacuous -- verdict survived forcing back_transform, stored_scale to its flipping value, so the check does not depend on the term it claims to observe
- `build-artefacts/iv-iron-hf.json` `NCT02642562::hfh_cvd_recurrent` terms=['back_transform', 'stored_scale']: PASS is vacuous -- verdict survived forcing back_transform, stored_scale to its flipping value, so the check does not depend on the term it claims to observe
- `build-artefacts/iv-iron-hf.json` `NCT03036462::hfh_recurrent` terms=['back_transform', 'stored_scale']: PASS is vacuous -- verdict survived forcing back_transform, stored_scale to its flipping value, so the check does not depend on the term it claims to observe
- `build-artefacts/iv-iron-hf.json` `NCT03037931::hierarchical_primary` terms=['back_transform', 'stored_scale']: PASS is vacuous -- verdict survived forcing back_transform, stored_scale to its flipping value, so the check does not depend on the term it claims to observe

## `validate_v2` Measurement

Direct per-detector invocation over 136 `ssot/*/*.json` files produced block/no-block counts, but not reliable actual adjudication counts. The CLI probe failed before a complete pass:

- `python -W error ssot/validate_v2.py ssot/iv-iron-hf/iv-iron-hf.json` exit 1: VALIDATING (schema v2) iv-iron-hf.json Traceback (most recent call last): File "F:\rapidmeta-ssot-shell\ssot\validate_v2.py", line 3806, in <module> sys.exit(main()) ~~~~^^ File "F:\rapidmeta-ssot-shell\ssot\validate_v2.py", line 3788, in main rep = validate(p) File "F:\rapidmeta-ssot-shell\ssot\validate_v2.py", line 3775, in validate fn(canon, rep) ~~^^^^^^^^^^^^ File "F:\rapidmeta-ssot-shell\ssot\validate_v2.py", line 3211, in check_overassertion_class from overassertion_rules import check_...

Highest pass-producing `validate_v2` rows, ranked by no-block pass emissions:

| detector | passes | blocks | raises | pass-without-predicate risk |
| --- | --- | --- | --- | --- |
| `self-reference` | 136 | 0 | 0 | yes |
| `removal-grounds` | 136 | 0 | 0 | yes |
| `network` | 136 | 0 | 0 | yes |
| `ve-consistency` | 135 | 0 | 1 | yes |
| `trial-scoped-refs` | 135 | 0 | 1 | UNKNOWN |
| `superseded` | 135 | 0 | 1 | unclear |
| `subgroup-recompute` | 135 | 0 | 1 | unclear |
| `source-category-binding` | 135 | 0 | 1 | yes |
| `shared-control-double-count` | 135 | 0 | 1 | unclear |
| `identifier-anchoring` | 135 | 0 | 1 | yes |
| `arm-role-vs-registry` | 135 | 0 | 1 | UNKNOWN |
| `arm-completeness` | 135 | 0 | 1 | yes |
| `regimen-homogeneity` | 134 | 0 | 2 | UNKNOWN |
| `estimand-storage-form` | 134 | 8 | 1 | unclear |
| `reference-consistency` | 134 | 3 | 1 | UNKNOWN |
| `quoted-group-disclosure` | 134 | 3 | 1 | UNKNOWN |
| `outcome-coverage` | 134 | 1 | 1 | UNKNOWN |
| `analysed-scope` | 130 | 27 | 1 | unclear |
| `per-trial-recompute` | 124 | 12 | 8 | unclear |
| `log-effect-consistency` | 123 | 0 | 13 | unclear |

## Runnable Selftests

Each command was invoked as `python -W error <script> --selftest` with a 60 second timeout. Warnings are reported as defects in the warning policy even when Python printed them at shutdown and returned exit 0.

| script | exit | warning? | tail |
| --- | --- | --- | --- |
| `scripts/withdrawal_reason_gate.py` | 0 | False | ing neither family is NOT_APPLICABL -> NOT_APPLICABLE (want NOT_APPLICABLE ) correct OVER-FIRE BOUND: 'efficacy' alone, with no safety term, is not a -> NOT_APPLICABLE (want NOT_APPLICABLE ) correct WHAT A FAILURE WOULD LOOK LIKE: the two founding cases returning the same verdict. They carry the ... |
| `scripts/verdict.py` | 0 | False | sless PASS refused correct PASS with a witness accepted correct FAIL without a witness accepted correct INVALID without a witness accepted correct a PASS w b INVALID selftest 2 checks: 1 PASS, 0 FAIL, 1 INVALID RUN NOT GREEN: 1 check(s) could not be run in a state where they could have failed. An... |
| `scripts/text_match.py` | 0 | False | ok case+tags ok entity ok double entity ok bracketed abbreviation ok whitespace + abbrev ok MUST STAY DIFFERENT -- rate is not a proportion ok MUST STAY DIFFERENT -- one letter, two quantities ok substring: contains() is deliberately permissive -- use equivalent() for identity ok identity is not ... |
| `scripts/absence_reason_gate.py` | 0 | False | same sentence on an AUTHORED page -> PASS correct NEGATIVE converted reason on a CONVERTED page -> PASS correct POSITIVE converted reason on an AUTHORED page -> FAIL correct NEGATIVE a BUILD-MODE-NEUTRAL reason on either page -> PASS correct NEGATIVE a page with no absence panels -> UNCHECKABLE c... |
| `scripts/analyze_poolability.py` | 0 | False | === selftest (thresh=0.5) === [OK] OMALIZUMAB (4 distinct): max_cluster=1 poolable=False (expect False) [OK] Shared PFS x3 (poolable): max_cluster=3 poolable=True (expect True) [OK] Mixed type same words (not poolable - type differs): max_cluster=1 poolable=False (expect False) [OK] ACR spelled-o... |
| `scripts/subject_match_gate.py` | 0 | True | shell\\ARNI_HF_REVIEW.html' mode='r' encoding='utf-8'> Exception ignored in: <_io.FileIO name='F:\\rapidmeta-ssot-shell\\SOTAGLIFLOZIN_HF_REVIEW.html' mode='rb' closefd=True> Traceback (most recent call last): File "F:\rapidmeta-ssot-shell\scripts\subject_match_gate.py", line 70, in check html = ... |
| `scripts/banner_anchor.py` | 0 | False | v1 projector, implied body -> v1-projector (implied body) correct bare body -> bare-body correct v1 with TWO style blocks has no safe anchor -> None correct WHAT A FAILURE WOULD LOOK LIKE: the two-style case returning an anchor. That would insert a banner between two stylesheets on a page whose s... |
| `scripts/subject_is_experimental_gate.py` | 0 | False | ASS (want PASS ) correct a topic whose registrations declare no arms is UNRESOLVED, never a pass -> UNRESOLVED (want UNRESOLVED ) correct WHAT A FAILURE WOULD LOOK LIKE: the two founding cases returning the SAME verdict. They are THE SAME TWO TRIALS under two different subject names, so a check t... |
| `scripts/alignment_gate.py` | 0 | False | expected=FAIL correct verbatim block differing by its own k FAIL expected=FAIL correct a section in the model that reached neither surface FAIL expected=FAIL correct NEGATIVE: the same heading text at two different levels PASS expected=PASS correct NEGATIVE: an arrow that is XML-escaped in the .d... |
| `scripts/ssot_net_deletion_check.py` | 0 | False | a net addition passes -> 0 (want 0) correct a net DELETION refuses -> 1 (want 1) correct equal counts pass -> 0 (want 0) correct mixed: one offender is enough to refuse -> 1 (want 1) correct WHAT A FAILURE WOULD LOOK LIKE: the 203-over-2422 case passing. That is the prevnar15 write exactly, and t... |
| `scripts/arm_identity_gate.py` | 0 | True | me='F:\\E156\\outputs\\codex-corpus-scan\\extract\\full_run\\FINERENONE_REVIEW.html.canonical.json' mode='rb' closefd=True> Traceback (most recent call last): File "F:\rapidmeta-ssot-shell\scripts\arm_identity_gate.py", line 225, in page_verdict d = json.loads(open(path, encoding="utf-8", errors=... |
| `scripts/silent_exclusion_screen.py` | 0 | False | (want DROPPED , 1 dropped) correct a page whose included trials all carry counts -> COMPLETE (want COMPLETE , 0 dropped) correct a page with no include list is UNREAD, never COMPLETE -> UNREAD (want UNREAD , 0 dropped) correct WHAT A FAILURE WOULD LOOK LIKE: the last case reporting COMPLETE. A pa... |
| `scripts/section_manifest_gate.py` | 0 | True | F_REVIEW.html' mode='r' encoding='utf-8'> Exception ignored in: <_io.FileIO name='F:\\rapidmeta-ssot-shell\\ssot\\arni-hfref\\manuscript_docmodel.json' mode='rb' closefd=True> Traceback (most recent call last): File "F:\rapidmeta-ssot-shell\scripts\section_manifest_gate.py", line 104, in selftest... |
| `scripts/search_recall_gate.py` | 0 | True | archrun\\abstracts.txt' mode='r' encoding='utf-8'> Exception ignored in: <_io.FileIO name='F:\\claude-temp\\searchrun\\SEARCH_sotagliflozin.json' mode='rb' closefd=True> Traceback (most recent call last): File "F:\rapidmeta-ssot-shell\scripts\search_recall_gate.py", line 80, in selftest r = json.... |
| `scripts/screen_harness.py` | 0 | True | sotagliflozin\\abstracts.txt' mode='r' encoding='utf-8'> Exception ignored in: <_io.FileIO name='F:\\E156\\outputs\\pilot-sotagliflozin\\abstracts.txt' mode='rb' closefd=True> Traceback (most recent call last): File "F:\rapidmeta-ssot-shell\scripts\screen_harness.py", line 60, in parse_records t ... |
| `scripts/build_stamp_gate.py` | 0 | True | sot-shell\\ARNI_HF_REVIEW.html' mode='r' encoding='utf-8'> Exception ignored in: <_io.FileIO name='F:\\rapidmeta-ssot-shell\\FINERENONE_CV_REVIEW.html' mode='rb' closefd=True> Traceback (most recent call last): File "F:\rapidmeta-ssot-shell\scripts\build_stamp_gate.py", line 54, in selftest v, wh... |
| `scripts/clone_contamination_gate.py` | 0 | False | ead inline handler blocks ok defined handler does NOT block (over-block control) ok verdict inherited byte-identical from base -> detected ok verdict recomputed (counts differ) -> NOT flagged (over-block control) ok inherited but non-green verdict -> not flagged (only green misleads) ok claim-bea... |
| `scripts/corpus/corpus_detectors.py` | 1 | False | ctly silent (this page already states it is NOT equivalent to PROSPERO -- a negated mention is not the claim) GLP1_CVOT_REVIEW.html C-T6 correctly silent (its headline trace already reads REML; the DL-labelled series is a real DerSimonian-Laird fit from state._dlResult) ==========================... |
| `scripts/registration_identity_gate.py` | 0 | False | Recorded rather than quietly corrected, because picking a threshold that excludes your own fixture is the exact shape of a check built to pass. WHAT A FAILURE WOULD LOOK LIKE: the SELECT-D row passing -- which is what identity_by_registration_gate does today, because it asks whether a registratio... |
| `scripts/rebuild_guard.py` | 0 | False | at ADDS lines is allowed -> OK (want OK ) correct (-0/+1) a write that REMOVES more than it adds REFUSES -> REFUSE (want REFUSE ) correct (-59/+0) an untracked path has NO BASELINE and is not a pass -> NO_BASELINE (want NO_BASELINE ) correct (-0/+0) WHAT A FAILURE WOULD LOOK LIKE: the halving cas... |
| `scripts/extraction_table_gate.py` | 1 | True | shell\\ARNI_HF_REVIEW.html' mode='r' encoding='utf-8'> Exception ignored in: <_io.FileIO name='F:\\rapidmeta-ssot-shell\\FINERENONE_CV_REVIEW.html' mode='rb' closefd=True> Traceback (most recent call last): File "F:\rapidmeta-ssot-shell\scripts\extraction_table_gate.py", line 133, in selftest v, ... |
| `scripts/export_artefact.py` | 0 | True | ozin-hf\\sotagliflozin-hf.json' mode='r' encoding='utf-8'> Exception ignored in: <_io.FileIO name='F:\\rapidmeta-ssot-shell\\ssot\\iv-iron-hf\\iv-iron-hf.json' mode='rb' closefd=True> Traceback (most recent call last): File "F:\rapidmeta-ssot-shell\scripts\export_artefact.py", line 400, in selfte... |
| `scripts/declared_contrast_gate.py` | 0 | False | egistered comparison and not the difference between any two of the four arm means the trial reports. NOTE ON THE BERSON ROW: it returns UNCHECKABLE rather than FAIL, and that is correct and worth keeping. Its stored labels ('Atorvastatin (Q2W)') are the PROTOCOL arm titles while the registry's RE... |
| `scripts/protocol_subject_gate.py` | 0 | True | le <_io.TextIOWrapper name='F:\\claude-temp\\tmpv34lu3oz.html' mode='r' encoding='utf-8'> Exception ignored in: <_io.FileIO name='F:\\claude-temp\\tmpum511_61.html' mode='rb' closefd=True> Traceback (most recent call last): File "F:\rapidmeta-ssot-shell\scripts\protocol_subject_gate.py", line 168... |
| `scripts/estimand_definition_gate.py` | 0 | True | ode='r' encoding='utf-8'> Exception ignored in: <_io.FileIO name='F:\\rapidmeta-ssot-shell\\ssot\\finerenone-cv\\finerenone-cv.json' mode='rb' closefd=True> Traceback (most recent call last): File "F:\rapidmeta-ssot-shell\scripts\estimand_definition_gate.py", line 574, in selftest v6, n6 = check(... |
| `scripts/prose_claim_gate.py` | 0 | False | tement of a null result PASS expected=PASS correct says no query recorded while the object holds one FAIL expected=FAIL correct NEGATIVE: the same sentence when it is true PASS expected=PASS correct no pooled interval -> INVALID, not PASS INVALID expected=INVALID correct NEGATIVE: benefit claim w... |
| `scripts/durable_artefact_gate.py` | 0 | False | POSITIVE a real file inside an IGNORED directory -> FAIL (IGNORED) correct POSITIVE a declared artefact that is absent -> FAIL (MISSING) correct NEGATIVE the real manifest as it stands now -> PASS correct WHAT A FAILURE WOULD LOOK LIKE: the ignored register passing, which is the exact state the w... |
| `scripts/count_provenance_gate.py` | 0 | False | never a pass -> UNCHECKABLE (want UNCHECKABLE ) correct a row that does not say which outcome it counts cannot be co -> UNCHECKABLE (want UNCHECKABLE ) correct WHAT A FAILURE WOULD LOOK LIKE: the founding row passing. Its denominators are the registry's primary-outcome denominators exact to the p... |
| `scripts/double_escape_gate.py` | 0 | False | ct: a real entity, encoded once -> PASS (want PASS ) correct correct: a literal em dash character needs no entity -> PASS (want PASS ) correct correct: an escaped ampersand in ordinary prose -> PASS (want PASS ) correct NOT a hit: an escaped ampersand followed by a word and a -> PASS (want PASS )... |
| `scripts/project_index_cards.py` | 0 | False | ed note is carried, not generated correct two outcomes and no declared headline -> REFUSES to guess correct the declared headline outcome is the one projected correct no value and no withdrawal projects NOTHING, not a blank correct WHAT A FAILURE WOULD LOOK LIKE: a card emitting a bare number. A ... |
| `scripts/precision_sample_gate.py` | 0 | True | F:\\E156\\outputs\\codex-corpus-scan\\extract\\full_run\\MITRAL_FUNCMR_REVIEW.html.canonical.json' mode='rb' closefd=True> Traceback (most recent call last): File "F:\rapidmeta-ssot-shell\scripts\precision_sample_gate.py", line 122, in selftest d = json.loads(open(mp, encoding="utf-8", errors="re... |
| `scripts/citation_year_gate.py` | 0 | False | ssue, declared, cited at issue year PASS expected=PASS correct epub ahead of issue but no basis recorded FAIL expected=FAIL correct NEGATIVE: an ordinary article with no epub split PASS expected=PASS correct trial row and citation block disagree FAIL expected=FAIL correct no trials at all -> INVA... |
| `scripts/card_alignment_gate.py` | 1 | True | ='F:\\rapidmeta-ssot-shell\\SGLT2_HF_REVIEW.html' mode='r' encoding='utf-8'> Exception ignored in: <_io.FileIO name='F:\\rapidmeta-ssot-shell\\SGLT2_HF_REVIEW.html' mode='rb' closefd=True> Traceback (most recent call last): File "F:\rapidmeta-ssot-shell\scripts\card_alignment_gate.py", line 419, ... |
| `scripts/pooled_value_gate.py` | 2 | False | usage: pooled_value_gate.py [-h] --object OBJECT --page PAGE [--selftest] pooled_value_gate.py: error: the following arguments are required: --object, --page |
| `scripts/poolability.py` | 0 | True | ne-cv.json' mode='r' encoding='utf-8'> Exception ignored in: <_io.FileIO name='F:\\rapidmeta-ssot-shell\\ssot\\sotagliflozin-hf\\sotagliflozin-hf.json' mode='rb' closefd=True> Traceback (most recent call last): File "F:\rapidmeta-ssot-shell\scripts\poolability.py", line 188, in selftest mut = jso... |
| `scripts/identity_by_registration_gate.py` | 0 | False | SWER-HF' -- a covering label accepted as identity NEGATIVE the same id with its own name -> PASS correct POSITIVE a trial keyed by NAME ALONE -> FAIL correct POSITIVE one id carrying two different names -> FAIL correct NEGATIVE an object with no trials -> UNCHECKABLE correct (not a pass) WHAT A F... |
| `scripts/headline_reproducible_gate.py` | 0 | False | correct UNCHECKABLE: one row and nothing to pool -> UNCHECKABLE (want UNCHECKABLE ) correct WHAT A FAILURE WOULD LOOK LIKE: the colchicine case reporting REPRODUCED. Its published 0.75 (0.61-0.91) was checked by hand against 33 candidate pools and fits none of them. AND THE OPPOSITE FAILURE MATTE... |
| `scripts/index_markup_gate.py` | 0 | True | d index failing, because a gate nobody can satisfy gets bypassed and then rots. -> SELFTEST PASS Exception ignored in: <_io.FileIO name='F:\\rapidmeta-ssot-shell\\index.html' mode='rb' closefd=True> Traceback (most recent call last): File "F:\rapidmeta-ssot-shell\scripts\index_markup_gate.py", li... |
| `scripts/identity_gate.py` | 0 | True | extIOWrapper name='F:\\claude-temp\\tmp9rs5cm8t\\empty.txt' mode='w' encoding='utf-8'> Exception ignored in: <_io.FileIO name='F:\\claude-temp\\tmp9rs5cm8t\\empty.txt' mode='rb' closefd=True> Traceback (most recent call last): File "F:\rapidmeta-ssot-shell\scripts\identity_gate.py", line 49, in c... |
| `scripts/k_consistency_gate.py` | 0 | True | eWarning: unclosed file <_io.TextIOWrapper name='F:\\claude-temp\\tmpxejvn9vi.json' mode='w' encoding='utf-8'> Exception ignored in: <_io.FileIO name='F:\\claude-temp\\tmpxejvn9vi.json' mode='rb' closefd=True> Traceback (most recent call last): File "F:\rapidmeta-ssot-shell\scripts\k_consistency_... |
| `scripts/gate_integrity.py` | 0 | True | me='F:\\claude-temp\\finerenone-pre-push.BROKEN.bak' mode='r' encoding='utf-8'> Exception ignored in: <_io.FileIO name='F:\\rapidmeta-ssot-shell\\.githooks\\pre-push' mode='rb' closefd=True> Traceback (most recent call last): File "F:\rapidmeta-ssot-shell\scripts\gate_integrity.py", line 430, in ... |

Selftests that failed or emitted warnings:
- `scripts/subject_match_gate.py` exit=0 warning=True: shell\\ARNI_HF_REVIEW.html' mode='r' encoding='utf-8'> Exception ignored in: <_io.FileIO name='F:\\rapidmeta-ssot-shell\\SOTAGLIFLOZIN_HF_REVIEW.html' mode='rb' closefd=True> Traceback (most recent call last): File "F:\rapidmeta-ssot-shell\scripts\subject_match_gate.py", line 70, in check html = ...
- `scripts/arm_identity_gate.py` exit=0 warning=True: me='F:\\E156\\outputs\\codex-corpus-scan\\extract\\full_run\\FINERENONE_REVIEW.html.canonical.json' mode='rb' closefd=True> Traceback (most recent call last): File "F:\rapidmeta-ssot-shell\scripts\arm_identity_gate.py", line 225, in page_verdict d = json.loads(open(path, encoding="utf-8", errors=...
- `scripts/section_manifest_gate.py` exit=0 warning=True: F_REVIEW.html' mode='r' encoding='utf-8'> Exception ignored in: <_io.FileIO name='F:\\rapidmeta-ssot-shell\\ssot\\arni-hfref\\manuscript_docmodel.json' mode='rb' closefd=True> Traceback (most recent call last): File "F:\rapidmeta-ssot-shell\scripts\section_manifest_gate.py", line 104, in selftest...
- `scripts/search_recall_gate.py` exit=0 warning=True: archrun\\abstracts.txt' mode='r' encoding='utf-8'> Exception ignored in: <_io.FileIO name='F:\\claude-temp\\searchrun\\SEARCH_sotagliflozin.json' mode='rb' closefd=True> Traceback (most recent call last): File "F:\rapidmeta-ssot-shell\scripts\search_recall_gate.py", line 80, in selftest r = json....
- `scripts/screen_harness.py` exit=0 warning=True: sotagliflozin\\abstracts.txt' mode='r' encoding='utf-8'> Exception ignored in: <_io.FileIO name='F:\\E156\\outputs\\pilot-sotagliflozin\\abstracts.txt' mode='rb' closefd=True> Traceback (most recent call last): File "F:\rapidmeta-ssot-shell\scripts\screen_harness.py", line 60, in parse_records t ...
- `scripts/build_stamp_gate.py` exit=0 warning=True: sot-shell\\ARNI_HF_REVIEW.html' mode='r' encoding='utf-8'> Exception ignored in: <_io.FileIO name='F:\\rapidmeta-ssot-shell\\FINERENONE_CV_REVIEW.html' mode='rb' closefd=True> Traceback (most recent call last): File "F:\rapidmeta-ssot-shell\scripts\build_stamp_gate.py", line 54, in selftest v, wh...
- `scripts/corpus/corpus_detectors.py` exit=1 warning=False: ctly silent (this page already states it is NOT equivalent to PROSPERO -- a negated mention is not the claim) GLP1_CVOT_REVIEW.html C-T6 correctly silent (its headline trace already reads REML; the DL-labelled series is a real DerSimonian-Laird fit from state._dlResult) ==========================...
- `scripts/extraction_table_gate.py` exit=1 warning=True: shell\\ARNI_HF_REVIEW.html' mode='r' encoding='utf-8'> Exception ignored in: <_io.FileIO name='F:\\rapidmeta-ssot-shell\\FINERENONE_CV_REVIEW.html' mode='rb' closefd=True> Traceback (most recent call last): File "F:\rapidmeta-ssot-shell\scripts\extraction_table_gate.py", line 133, in selftest v, ...
- `scripts/export_artefact.py` exit=0 warning=True: ozin-hf\\sotagliflozin-hf.json' mode='r' encoding='utf-8'> Exception ignored in: <_io.FileIO name='F:\\rapidmeta-ssot-shell\\ssot\\iv-iron-hf\\iv-iron-hf.json' mode='rb' closefd=True> Traceback (most recent call last): File "F:\rapidmeta-ssot-shell\scripts\export_artefact.py", line 400, in selfte...
- `scripts/protocol_subject_gate.py` exit=0 warning=True: le <_io.TextIOWrapper name='F:\\claude-temp\\tmpv34lu3oz.html' mode='r' encoding='utf-8'> Exception ignored in: <_io.FileIO name='F:\\claude-temp\\tmpum511_61.html' mode='rb' closefd=True> Traceback (most recent call last): File "F:\rapidmeta-ssot-shell\scripts\protocol_subject_gate.py", line 168...
- `scripts/estimand_definition_gate.py` exit=0 warning=True: ode='r' encoding='utf-8'> Exception ignored in: <_io.FileIO name='F:\\rapidmeta-ssot-shell\\ssot\\finerenone-cv\\finerenone-cv.json' mode='rb' closefd=True> Traceback (most recent call last): File "F:\rapidmeta-ssot-shell\scripts\estimand_definition_gate.py", line 574, in selftest v6, n6 = check(...
- `scripts/precision_sample_gate.py` exit=0 warning=True: F:\\E156\\outputs\\codex-corpus-scan\\extract\\full_run\\MITRAL_FUNCMR_REVIEW.html.canonical.json' mode='rb' closefd=True> Traceback (most recent call last): File "F:\rapidmeta-ssot-shell\scripts\precision_sample_gate.py", line 122, in selftest d = json.loads(open(mp, encoding="utf-8", errors="re...
- `scripts/card_alignment_gate.py` exit=1 warning=True: ='F:\\rapidmeta-ssot-shell\\SGLT2_HF_REVIEW.html' mode='r' encoding='utf-8'> Exception ignored in: <_io.FileIO name='F:\\rapidmeta-ssot-shell\\SGLT2_HF_REVIEW.html' mode='rb' closefd=True> Traceback (most recent call last): File "F:\rapidmeta-ssot-shell\scripts\card_alignment_gate.py", line 419, ...
- `scripts/pooled_value_gate.py` exit=2 warning=False: usage: pooled_value_gate.py [-h] --object OBJECT --page PAGE [--selftest] pooled_value_gate.py: error: the following arguments are required: --object, --page
- `scripts/poolability.py` exit=0 warning=True: ne-cv.json' mode='r' encoding='utf-8'> Exception ignored in: <_io.FileIO name='F:\\rapidmeta-ssot-shell\\ssot\\sotagliflozin-hf\\sotagliflozin-hf.json' mode='rb' closefd=True> Traceback (most recent call last): File "F:\rapidmeta-ssot-shell\scripts\poolability.py", line 188, in selftest mut = jso...
- `scripts/index_markup_gate.py` exit=0 warning=True: d index failing, because a gate nobody can satisfy gets bypassed and then rots. -> SELFTEST PASS Exception ignored in: <_io.FileIO name='F:\\rapidmeta-ssot-shell\\index.html' mode='rb' closefd=True> Traceback (most recent call last): File "F:\rapidmeta-ssot-shell\scripts\index_markup_gate.py", li...
- `scripts/identity_gate.py` exit=0 warning=True: extIOWrapper name='F:\\claude-temp\\tmp9rs5cm8t\\empty.txt' mode='w' encoding='utf-8'> Exception ignored in: <_io.FileIO name='F:\\claude-temp\\tmp9rs5cm8t\\empty.txt' mode='rb' closefd=True> Traceback (most recent call last): File "F:\rapidmeta-ssot-shell\scripts\identity_gate.py", line 49, in c...
- `scripts/k_consistency_gate.py` exit=0 warning=True: eWarning: unclosed file <_io.TextIOWrapper name='F:\\claude-temp\\tmpxejvn9vi.json' mode='w' encoding='utf-8'> Exception ignored in: <_io.FileIO name='F:\\claude-temp\\tmpxejvn9vi.json' mode='rb' closefd=True> Traceback (most recent call last): File "F:\rapidmeta-ssot-shell\scripts\k_consistency_...
- `scripts/gate_integrity.py` exit=0 warning=True: me='F:\\claude-temp\\finerenone-pre-push.BROKEN.bak' mode='r' encoding='utf-8'> Exception ignored in: <_io.FileIO name='F:\\rapidmeta-ssot-shell\\.githooks\\pre-push' mode='rb' closefd=True> Traceback (most recent call last): File "F:\rapidmeta-ssot-shell\scripts\gate_integrity.py", line 430, in ...

## Specific Verdict-Without-Reading Paths

### CHK021 unknown measure falls through to PASS

```python
 396: _RATIO_MEASURES = {"OR", "RR", "HR", "IRR"}
 397: _DIFF_MEASURES = {"MD", "SMD", "RD"}
```
```python
 668:     xf = p.get("back_transform")
 669:     if not measure or not scale:
 670:         return make_invalid(cid, inst, "measure or stored scale not declared")
 671: 
 672:     if measure in _DIFF_MEASURES:
 673:         if scale != "natural" or xf not in (None, "identity"):
 674:             return make_fail(cid, inst,
 675:                              f"{measure} is a difference on the natural scale but is "
 676:                              f"stored as {scale!r} with back_transform {xf!r}",
 677:                              observed=f"measure={measure} scale={scale!r} "
 678:                                       f"back_transform={xf!r}"
 679:                                       + (f"; rendered value {p.get('rendered_value')}"
 680:                                          if p.get("rendered_value") is not None else ""),
 681:                              locator=str(p.get("row_id")),
 682:                              opposite_would_be=f"{measure} stored on the natural "
 683:                                                "scale with no back-transform",
 684:                              measure=measure, scale=scale, back_transform=xf)
 685:     elif measure in _RATIO_MEASURES:
 686:         if scale == "log" and xf != "exp":
 687:             return make_fail(cid, inst,
 688:                              f"{measure} stored on the log scale with back_transform "
 689:                              f"{xf!r}; it will render as a log value",
 690:                              observed=f"measure={measure} scale=log back_transform={xf!r}",
 691:                              locator=str(p.get("row_id")),
 692:                              opposite_would_be="an exp back-transform on a "
 693:                                                "log-scale ratio",
 694:                              measure=measure, scale=scale, back_transform=xf)
 695:         if scale == "natural" and xf == "exp":
 696:             return make_fail(cid, inst,
 697:                              f"{measure} already on the natural scale is being "
 698:                              "exponentiated again",
 699:                              observed=f"measure={measure} scale=natural back_transform=exp",
 700:                              locator=str(p.get("row_id")),
 701:                              opposite_would_be="no back-transform on a natural-scale "
 702:                                                "ratio",
 703:                              measure=measure, scale=scale, back_transform=xf)
 704:     return make_pass(cid, inst,
 705:                      observed=f"{measure} on the {scale} scale with back_transform "
 706:                               f"{xf!r}",
 707:                      locator=str(p.get("row_id")),
 708:                      opposite_would_be="a difference measure exponentiated, or a "
```
Measured effect: `RATE_RATIO` and `WIN_RATIO` are in neither vocabulary set, so neither branch adjudicates the scale rule before the unconditional `make_pass()`.

### `validate_v2.validate()` converts no block into a pass

```python
3770: 
3771: def validate(path: Path, verbose=True) -> Report:
3772:     canon = json.loads(path.read_text(encoding="utf-8"))
3773:     rep = Report()
3774:     for name, fn in DETECTORS:
3775:         before = len(rep.blocks)
3776:         fn(canon, rep)
3777:         fired = len(rep.blocks) - before
3778:         if verbose:
3779:             print(f"  [{'BLOCK' if fired else ' ok  '}] {name}"
3780:                   + (f"  ({fired})" if fired else ""))
3781:         if not fired:
3782:             rep.passes.append(name)
```

### `validate_v2.check_network()` returns before checking when `network` is absent

```python
2981: 
2982: def check_network(canon, rep):
2983:     """A network's claims about its own shape must follow from its edges.
2984: 
2985:     Added with the first network object. The claim that matters is whether an
2986:     INDIRECT comparison is supportable, and that turns on whether the graph
2987:     contains a closed loop -- the Handbook measures incoherence as a difference
2988:     between direct and indirect estimates around one. A star of edges meeting at
2989:     a single comparator has none, so consistency there is untestable rather than
2990:     satisfied, and an object must not present it as satisfied.
2991: 
2992:     This checks the graph against the object's own count, not against a
2993:     judgement: loops are recomputed from the edges.
2994:     """
2995:     net = canon.get("network")
2996:     if not net:
2997:         return
```
With the wrapper above, this early return becomes a `network` pass for non-network objects.

### Source-cache detectors return when the source cache is absent

```python
2039: 
2040: def check_arm_completeness(canon, rep, sources_root=None):
2041:     """Every arm the SOURCE posts must be declared or explicitly set aside.
2042: 
2043:     check_arm_roles requires a disclosure when a trial DECLARES more than one
2044:     treatment arm. A reviewer showed that is the wrong hinge: delete the second
2045:     V114 arm from the object entirely, drop the note, and use one formulation's
2046:     own numbers. Every remaining cell then matches the source, the pool
2047:     recomputes, and nothing fires -- because a detector that reads the declared
2048:     arms cannot see an arm that was never declared. Confirmed by executing it.
2049: 
2050:     The fix has to come from outside the object. This enumerates the arms the
2051:     registry actually posts for the cited outcome and requires each one to be
2052:     either used or named in arms_not_used, so dropping an arm becomes a visible
2053:     act rather than an absence.
2054:     """
2055:     root = pathlib.Path(sources_root or "sources") / canon["app_id"]
2056:     if not root.is_dir():
2057:         return
```
`check_source_category_binding`, `check_identifier_anchoring`, `check_reference_consistency`, `check_arm_completeness`, and related source-backed detectors share this pattern: source cache absence is owned elsewhere, but the individual detector still records as passed when `validate()` sees no block from that detector.

### `validate_v2.check_cross_engine()` notes a skip, then the wrapper records a pass

```python
3465: 
3466: def check_cross_engine(canon, rep):
3467:     """Recompute every pooled estimate in metafor and block on disagreement.
3468: 
3469:     Our pooling is implemented independently of whatever produced the recorded
3470:     number, but it is still OUR arithmetic checking OUR arithmetic. metafor is a
3471:     third party: different authors, different code, published and widely used.
3472: 
3473:     WHAT IT BLOCKS ON: point, ci_low, ci_high and tau2, outside 1e-4 on the
3474:     ratio scale. The observed disagreement on a real pool was 6.2e-06, so the
3475:     tolerance sits far above the noise and far below any error worth catching.
3476: 
3477:     WHAT IT DOES NOT BLOCK ON: I2. Ours is the Higgins I2 from Q and df,
3478:     metafor's is relative to the REML tau2 -- on the tigecycline pool ours is
3479:     7.29% and metafor's 1.18%. Two quantities, one name. A single engine can
3480:     never surface that, and forcing agreement would silently change published I2
3481:     values across the batch. Both are RECORDED, labelled, side by side.
3482: 
3483:     WHEN R IS UNREACHABLE it records a NOTE naming the cause and does not pass
3484:     silently. A numerical witness that skips on a missing prerequisite and is
3485:     counted as a pass is a failure this repo has already shipped once.
3486: 
3487:     Runs on the generic-inverse-variance shape, which is what most of this batch
3488:     stores: a published effect with an interval, whose log point and log
3489:     standard error are what our own estimators consume. Rows without those are
3490:     skipped WITH a note rather than quietly ignored.
3491:     """
3492:     import r_bridge
3493: 
3494:     exe, why = r_bridge.find_rscript()
3495:     pooled_ids = [oid for oid, res in
3496:                   (canon.get("results", {}).get("by_outcome") or {}).items()
3497:                   if res.get("pooled")]
3498:     if not pooled_ids:
3499:         return
3500:     if exe is None:
3501:         rep.note("cross-engine-skipped",
3502:                  f"no independent recompute was performed for "
3503:                  f"{len(pooled_ids)} pooled outcome(s): {why}. This is a SKIP, "
3504:                  f"not agreement.")
```

### `validate_v2.check_grade()` skips absent grade blocks

```python
3597: 
3598: def check_grade(canon, rep):
3599:     """GRADE certainty: every domain backed, and the certainty COMPUTED.
3600: 
3601:     ADDITIVE AND SILENT BY DEFAULT. An outcome with no `grade` block is not
3602:     touched, because the nine objects already live were built before this rule
3603:     existed and backfilling them is a separate pass Mahmood asked to keep
3604:     separate. Requiring the block from them would be a retroactive block with
3605:     nothing wrong behind it -- the same reasoning `estimand-undeclared` and
3606:     `shared-control-unkeyed` already use.
3607: 
3608:     What it enforces where a block IS present:
3609: 
3610:       * every one of the five downgrade domains is present and carries EXACTLY
3611:         one backing -- a computed value in this object, staged source text, or a
3612:         stated reason. A rating with none of the three is the
3613:         identity-without-basis defect wearing a GRADE hat.
3614:       * a `derived_from` domain's stored value equals the value computed here,
3615:         so a domain cannot drift from the field it claims to come from.
3616:       * the stored certainty equals the certainty computed from the domains.
3617:         This is `sameness-not-derived` for GRADE: the number follows the
3618:         structure, never the other way round.
3619:       * the rating vocabulary is 14.2.2's, and 'extremely serious' is rejected
3620:         on randomised evidence because the Handbook offers it only for
3621:         ROBINS-I-assessed non-randomised studies.
3622:       * the sections cited are recorded. Inconsistency in particular needs BOTH
3623:         14.2.2 (which governs the domain and gives no bands) and 10.10.2 (which
3624:         gives the bands) -- citing only the first is the "section governs the
3625:         measure, not the decision" error the self-audit checklist already names.
3626:     """
3627:     import grade as G
3628: 
3629:     for oid, res in (canon.get("results", {}).get("by_outcome") or {}).items():
3630:         g = res.get("grade")
3631:         if not g:
3632:             continue
3633: 
3634:         domains = g.get("domains") or {}
3635:         for d in G.DOMAINS:
3636:             entry = domains.get(d)
3637:             if not isinstance(entry, dict):
```

### `topic_identity.locate()` reads raw-v2 fields without enforcing raw-v2 shape

```python
  77: def locate(study, syns):
  78:     """Where does the topic drug appear? Reads the INTERVENTION LIST and the registration's
  79:     own name records -- never the arm label alone.
  80: 
  81:     Returns (role, evidence). Role is NOT_ASSESSABLE when the drug cannot be located in any
  82:     eligible field, which is a different state from having been excluded.
  83:     """
  84:     ps = study.get("protocolSection") or {}
  85:     ai = ps.get("armsInterventionsModule") or {}
  86:     idm = ps.get("identificationModule") or {}
  87:     arms = ai.get("armGroups") or []
  88:     intrs = ai.get("interventions") or []
```
```python
 130:     # 4. Named ONLY in the title/registration record. NCT02789917 is exactly this case.
 131:     if matches(title_blob):
 132:         if not arms:
 133:             return NOT_ASSESSABLE, "named in the registration title; no armGroups to assign a role"
 134:         types = [str(a.get("type") or "").upper() for a in arms]
 135:         if "EXPERIMENTAL" in types:
 136:             return (EXPERIMENTAL,
 137:                     "named in the registration TITLE only; arms are labelled by regimen, "
 138:                     "and the EXPERIMENTAL arm is taken as the topic arm")
 139:         return NOT_ASSESSABLE, "named in the registration title; arm roles do not identify it"
 140: 
 141:     # 5. Genuinely not found anywhere eligible.
 142:     return NOT_ASSESSABLE, ("topic drug not located in interventions, arms, or registration "
```
A flattened MCP ClinicalTrials.gov record has none of these raw-v2 role fields, so the assessor can return a verdict-shaped `not_assessable` cascade instead of raising.

### The reference guard that does raise

```python
  67: def is_raw_v2(study):
  68:     """Does this record carry the fields role reading requires? No inference."""
  69:     if not isinstance(study, dict):
  70:         return False
  71:     ps = study.get("protocolSection")
  72:     if not isinstance(ps, dict):
  73:         return False
  74:     return isinstance(ps.get("armsInterventionsModule"), dict)
  75: 
  76: 
  77: def require_raw_v2(study, nct_id=None):
  78:     """Fail closed before any role is read. Returns the study when it is readable."""
  79:     if is_raw_v2(study):
  80:         return study
  81:     keys = sorted(study)[:8] if isinstance(study, dict) else type(study).__name__
  82:     raise WrongPayloadShape(
  83:         f"{nct_id or '<unknown>'}: record carries no protocolSection.armsInterventionsModule "
  84:         f"(top-level keys: {keys}). This is the FLATTENED MCP shape, which contains no arm "
  85:         f"types at all. Reading roles from it returns not_assessable for every trial -- a "
  86:         f"silent all-refusal cascade. Fetch the raw v2 record via fetch_raw() instead.")
```

## Static-Vs-Dynamic Hardcode Disclosure

| item | static/dynamic | disclosure |
| --- | --- | --- |
| Check discovery roots | static | `ssot`, `scripts`, `.githooks` per task scope. |
| Selftest file list | static | Fixed in this helper from `rg -l "def selftest|--selftest" scripts ssot`, excluding `figure_audit.py --selftest-structure` because it requires two explicit pages. |
| NAFIS/precondition/validate registries | dynamic | Imported from current source at run time. |
| Metrics | dynamic | Computed from current `build-artefacts/*.json` and `ssot/*/*.json`; no network. |
| Adjudication for `validate_v2` | unknown | The validator exposes block/no-block, not predicate-run witnesses. Rows are not reported as sound. |

## Full Inventory

Summary: 364 rows. Shape-asserting yes: 23; shape-asserting no: 46; PASS-without-predicate risk yes: 147; vacuity UNKNOWN: 168.

### NAFIS CHK registry

| name | file:line | depends on | shape assert? | PASS without predicate? | consumes | emissions | adjudicated | passes | fail/block | invalid/raise | basis |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| NAFIS CHK registry: CHK001_RETRIEVAL_ABSENCE | scripts/nafis_harness/probes.py:53 | http_status, result_count | partial (registered harness controls; not emitted here) | UNKNOWN (no corpus emission) | retrieval-scoped wrapper payload; not build-artefact runnable | 0 | 0 | 0 | 0 | 0 | executed harness against build-artefacts |
| NAFIS CHK registry: CHK002_TOKEN_MATCH | scripts/nafis_harness/probes.py:117 | pattern, field_scoped, hits | partial (registered harness controls; not emitted here) | UNKNOWN (no corpus emission) | build-artefacts/*.json via payloads_for adapter | 0 | 0 | 0 | 0 | 0 | executed harness against build-artefacts |
| NAFIS CHK registry: CHK003_ACTION_EFFECT | scripts/nafis_harness/probes.py:189 | observed_effect_field, pre_state, post_state | partial (registered harness controls; not emitted here) | UNKNOWN (no corpus emission) | retrieval-scoped wrapper payload; not build-artefact runnable | 0 | 0 | 0 | 0 | 0 | executed harness against build-artefacts |
| NAFIS CHK registry: CHK004_LIVENESS | scripts/nafis_harness/probes.py:250 | probe, host_os, stdout, corroborated | partial (registered harness controls; not emitted here) | UNKNOWN (no corpus emission) | retrieval-scoped wrapper payload; not build-artefact runnable | 0 | 0 | 0 | 0 | 0 | executed harness against build-artefacts |
| NAFIS CHK registry: CHK005_EXTERNAL_REFERENT | scripts/nafis_harness/probes.py:334 | row, external_referent | partial (registered harness controls; not emitted here) | UNKNOWN (no corpus emission) | build-artefacts/*.json via payloads_for adapter | 0 | 0 | 0 | 0 | 0 | executed harness against build-artefacts |
| NAFIS CHK registry: CHK006_IDENTITY_KEY | scripts/nafis_harness/probes.py:524 | registration_id, source_document_ids, registry_acronym, registry_enrolment | partial (registered harness controls; not emitted here) | UNKNOWN (no corpus emission) | build-artefacts/*.json via payloads_for adapter | 0 | 0 | 0 | 0 | 0 | executed harness against build-artefacts |
| NAFIS CHK registry: CHK007_ABSENCE_SCREEN | scripts/nafis_harness/probes.py:640 | screen, findings | partial (registered harness controls; not emitted here) | UNKNOWN (no corpus emission) | retrieval-scoped wrapper payload; not build-artefact runnable | 0 | 0 | 0 | 0 | 0 | executed harness against build-artefacts |
| NAFIS CHK registry: CHK008_FRAME_DENOMINATOR | scripts/nafis_harness/probes.py:704 | denominator, denominator_source, claim_scope | partial (registered harness controls; not emitted here) | UNKNOWN (no corpus emission) | build-artefacts/*.json via payloads_for adapter | 0 | 0 | 0 | 0 | 0 | executed harness against build-artefacts |
| NAFIS CHK registry: CHK009_POOL_IDENTITY | scripts/nafis_harness/probes.py:767 | headline_k, headline_outcome, panel_rows | partial (harness controls and witness required) | no by harness vacuity run | build-artefacts/*.json via payloads_for adapter | 17 | 17 | 17 | 0 | 0 | executed harness against build-artefacts |
| NAFIS CHK registry: CHK010_CHAIN_EXHAUSTION | scripts/nafis_harness/probes.py:856 | declared_hops, hop_log, conclusion | partial (registered harness controls; not emitted here) | UNKNOWN (no corpus emission) | retrieval-scoped wrapper payload; not build-artefact runnable | 0 | 0 | 0 | 0 | 0 | executed harness against build-artefacts |
| NAFIS CHK registry: CHK011_CORRECTION_BURDEN | scripts/nafis_harness/probes.py:921 | correcting_source_id, original_source_id, original_rechecked_at_source | partial (registered harness controls; not emitted here) | UNKNOWN (no corpus emission) | retrieval-scoped wrapper payload; not build-artefact runnable | 0 | 0 | 0 | 0 | 0 | executed harness against build-artefacts |
| NAFIS CHK registry: CHK012_LAYER_MATCH | scripts/nafis_harness/probes.py:1041 | claim_layer, observation_layer, observed | partial (registered harness controls; not emitted here) | UNKNOWN (no corpus emission) | retrieval-scoped wrapper payload; not build-artefact runnable | 0 | 0 | 0 | 0 | 0 | executed harness against build-artefacts |
| NAFIS CHK registry: CHK013_FIELD_SEMANTICS | scripts/nafis_harness/probes.py:1101 | source_field, field_semantics | partial (registered harness controls; not emitted here) | UNKNOWN (no corpus emission) | build-artefacts/*.json via payloads_for adapter | 0 | 0 | 0 | 0 | 0 | executed harness against build-artefacts |
| NAFIS CHK registry: CHK014_FILTER_FIRED | scripts/nafis_harness/probes.py:1165 | declared_filter, returned_urls | partial (registered harness controls; not emitted here) | UNKNOWN (no corpus emission) | retrieval-scoped wrapper payload; not build-artefact runnable | 0 | 0 | 0 | 0 | 0 | executed harness against build-artefacts |
| NAFIS CHK registry: CHK015_HIT_COUNT_SANITY | scripts/nafis_harness/probes.py:1242 | hits, expected_order_of_magnitude, corpus_size | partial (registered harness controls; not emitted here) | UNKNOWN (no corpus emission) | retrieval-scoped wrapper payload; not build-artefact runnable | 0 | 0 | 0 | 0 | 0 | executed harness against build-artefacts |
| NAFIS CHK registry: CHK026_WRONG_REASON_ABSENCE_PANEL | scripts/nafis_harness/probes_build.py:56 | absence_reason_id, reason_valid_for, page_provenance | partial (registered harness controls; not emitted here) | UNKNOWN (no corpus emission) | build-artefacts/*.json via payloads_for adapter | 0 | 0 | 0 | 0 | 0 | executed harness against build-artefacts |
| NAFIS CHK registry: CHK027_SENTINEL_LEAK | scripts/nafis_harness/probes_build.py:141 | reader_text, sentinels | partial (registered harness controls; not emitted here) | UNKNOWN (no corpus emission) | build-artefacts/*.json via payloads_for adapter | 0 | 0 | 0 | 0 | 0 | executed harness against build-artefacts |
| NAFIS CHK registry: CHK028_DISQUALIFIED_REFERENT_PROMOTED | scripts/nafis_harness/probes_build.py:216 | card, object | partial (registered harness controls; not emitted here) | UNKNOWN (no corpus emission) | build-artefacts/*.json via payloads_for adapter | 0 | 0 | 0 | 0 | 0 | executed harness against build-artefacts |
| NAFIS CHK registry: CHK029_SIGN_NORMALISATION | scripts/nafis_harness/probes_build.py:328 | raw, naive_value | partial (registered harness controls; not emitted here) | UNKNOWN (no corpus emission) | build-artefacts/*.json via payloads_for adapter | 0 | 0 | 0 | 0 | 0 | executed harness against build-artefacts |
| NAFIS CHK registry: CHK030_BUILD_MODE_BLIND_TEXT | scripts/nafis_harness/probes_build.py:411 | asserts_rationale, valid_for_paths, build_path | partial (registered harness controls; not emitted here) | UNKNOWN (no corpus emission) | build-artefacts/*.json via payloads_for adapter | 0 | 0 | 0 | 0 | 0 | executed harness against build-artefacts |
| NAFIS CHK registry: CHK016_PRECISION_SAMPLE_MISMATCH | scripts/nafis_harness/probes_corpus.py:77 | ci_low, ci_high, events_t, n_t, events_c, n_c | partial (harness controls and witness required) | no by harness vacuity run | build-artefacts/*.json via payloads_for adapter | 38 | 35 | 35 | 0 | 3 | executed harness against build-artefacts |
| NAFIS CHK registry: CHK017_DUP1_BIT_EQUALITY | scripts/nafis_harness/probes_corpus.py:235 | entries, pooled_estimate | partial (harness controls and witness required) | no by harness vacuity run | build-artefacts/*.json via payloads_for adapter | 15 | 15 | 15 | 0 | 0 | executed harness against build-artefacts |
| NAFIS CHK registry: CHK018_MIXED_POOLING | scripts/nafis_harness/probes_corpus.py:400 | entries.measure, entries.direction_of_benefit, composite_endpoint | partial (harness controls and witness required) | no by harness vacuity run | build-artefacts/*.json via payloads_for adapter | 14 | 14 | 14 | 0 | 0 | executed harness against build-artefacts |
| NAFIS CHK registry: CHK019_INERT_ENGINE | scripts/nafis_harness/probes_corpus.py:534 | engine_trial_ids, data_trial_ids | partial (harness controls and witness required) | no by harness vacuity run | build-artefacts/*.json via payloads_for adapter | 29 | 29 | 29 | 0 | 0 | executed harness against build-artefacts |
| NAFIS CHK registry: CHK020_ORPHAN_POOLED_RESULT | scripts/nafis_harness/probes_corpus.py:601 | displayed_pooled_estimate, engine_can_pool | partial (harness controls and witness required) | no by harness vacuity run | build-artefacts/*.json via payloads_for adapter | 119 | 119 | 119 | 0 | 0 | executed harness against build-artefacts |
| NAFIS CHK registry: CHK021_MEASURE_SCALE_MISMATCH | scripts/nafis_harness/probes_corpus.py:665 | measure, stored_scale, back_transform | no (predicate vocabulary not fully asserted) | yes | build-artefacts/*.json via payloads_for adapter | 70 | 65 | 65 | 0 | 5 | executed harness against build-artefacts |
| NAFIS CHK registry: CHK022_RATIO_FROM_PERCENTAGE | scripts/nafis_harness/probes_corpus.py:767 | extracted_measure, source_text | partial (registered harness controls; not emitted here) | UNKNOWN (no corpus emission) | retrieval-scoped wrapper payload; not build-artefact runnable | 0 | 0 | 0 | 0 | 0 | executed harness against build-artefacts |
| NAFIS CHK registry: CHK023_CROSS_AGENT_POOLING | scripts/nafis_harness/probes_corpus.py:836 | entries.intervention, declared_class | partial (registered harness controls; not emitted here) | UNKNOWN (no corpus emission) | build-artefacts/*.json via payloads_for adapter | 0 | 0 | 0 | 0 | 0 | executed harness against build-artefacts |
| NAFIS CHK registry: CHK024_FALSE_METHOD_CLAIM | scripts/nafis_harness/probes_corpus.py:898 | claimed_method, network_edges | partial (registered harness controls; not emitted here) | UNKNOWN (no corpus emission) | build-artefacts/*.json via payloads_for adapter | 0 | 0 | 0 | 0 | 0 | executed harness against build-artefacts |
| NAFIS CHK registry: CHK025_MULTI_SURFACE_DISAGREEMENT | scripts/nafis_harness/probes_corpus.py:958 | surfaces | partial (registered harness controls; not emitted here) | UNKNOWN (no corpus emission) | build-artefacts/*.json via payloads_for adapter | 0 | 0 | 0 | 0 | 0 | executed harness against build-artefacts |

### NAFIS aggregate gate

| name | file:line | depends on | shape assert? | PASS without predicate? | consumes | emissions | adjudicated | passes | fail/block | invalid/raise | basis |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| NAFIS aggregate gate: harness_gate aggregate process PASS | scripts/harness_gate.py:50 | build-artefact payloads, child Result.verdict, invalid-ceiling | partial (zero executions exit 2; invalids allowed below ceiling) | yes at process level: exits 0 while child INVALID results are present | build-artefacts/*.json via payloads_for adapter | 302 | 294 | 1 process PASS; 294 child PASS | 0 | 8 | derived from executed harness run; confirmed by harness_gate CLI |

### assessment helper

| name | file:line | depends on | shape assert? | PASS without predicate? | consumes | emissions | adjudicated | passes | fail/block | invalid/raise | basis |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| assessment helper: assessment.read | ssot/assessment.py:75 | dotted path | yes | no (reader only; no PASS emitted) | dict object | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | static read; selected support surface |
| assessment helper: assessment.judge | ssot/assessment.py:111 | Reading.state/value | yes | no (predicate called only for present Reading) | Reading wrapper | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | static read; selected support surface |
| assessment helper: assessment.assess | ssot/assessment.py:157 | dotted path | yes | no (delegates to read/judge) | dict object | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | static read; selected support surface |
| assessment helper: assessment.inclusion_criteria_auditable | ssot/assessment.py:302 | screening.eligibility | yes | no observed; delegates to judge(read()) | cached object | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | static read; selected support surface |
| assessment helper: assessment.eligibility_met | ssot/assessment.py:307 | screening.eligibility, full_text_read | yes | no; returns NOT_ASSESSABLE without full text | cached object | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | static read; selected support surface |
| assessment helper: assessment.require_named_intervention | ssot/assessment.py:359 | topic, intervention, condition | yes | no PASS emitted; raises on malformed query | query wrapper | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | static read; selected support surface |

### assessor registry gate

| name | file:line | depends on | shape assert? | PASS without predicate? | consumes | emissions | adjudicated | passes | fail/block | invalid/raise | basis |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| assessor registry gate: Registry.register duplicate-path guard | ssot/assessor_registry.py:206 | declared reads, function source, unit_source | yes | no PASS emitted; raises AssessorRejected | assessor registration wrapper | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | static read; selected support surface |
| assessor registry gate: Registry.type_guard | ssot/assessor_registry.py:245 | accepts map, declared reads | yes | no PASS emitted; returns NOT_ASSESSABLE on type mismatch | assessor/cached object | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | static read; selected support surface |
| assessor registry gate: Registry.identical_tally_alarm | ssot/assessor_registry.py:268 | assessor result tallies | partial | yes if fewer than two assessors; caller must not count [] as clean evidence | assessor results | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | static read; selected support surface |

### estimand assessor

| name | file:line | depends on | shape assert? | PASS without predicate? | consumes | emissions | adjudicated | passes | fail/block | invalid/raise | basis |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| estimand assessor: estimand_identity.compare | ssot/estimand_identity.py:107 | estimand definition strings | partial | no PASS label; SAME only after string comparison | object fields | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | static read; selected support surface |
| estimand assessor: estimand_identity.compare_all | ssot/estimand_identity.py:131 | estimand definition list | partial | no PASS label; <2 definitions returns UNDECIDABLE | object fields | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | static read; selected support surface |

### hook gate

| name | file:line | depends on | shape assert? | PASS without predicate? | consumes | emissions | adjudicated | passes | fail/block | invalid/raise | basis |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hook gate: .githooks/README.md | .githooks/README.md:1 | changed files, build artefacts, regression pages, process exit codes | partial | yes for scoped no-op branches; output labels them as scoped, not corpus clean | git hook/process status/wrapper commands | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | static shell read; not executed to avoid pre-push side effects |
| hook gate: .githooks/pre-commit | .githooks/pre-commit:1 | changed files, build artefacts, regression pages, process exit codes | partial | yes for scoped no-op branches; output labels them as scoped, not corpus clean | git hook/process status/wrapper commands | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | static shell read; not executed to avoid pre-push side effects |
| hook gate: .githooks/pre-commit-staging | .githooks/pre-commit-staging:1 | changed files, build artefacts, regression pages, process exit codes | partial | yes for scoped no-op branches; output labels them as scoped, not corpus clean | git hook/process status/wrapper commands | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | static shell read; not executed to avoid pre-push side effects |
| hook gate: .githooks/pre-push | .githooks/pre-push:1 | changed files, build artefacts, regression pages, process exit codes | partial | yes for scoped no-op branches; output labels them as scoped, not corpus clean | git hook/process status/wrapper commands | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | static shell read; not executed to avoid pre-push side effects |

### invariant

| name | file:line | depends on | shape assert? | PASS without predicate? | consumes | emissions | adjudicated | passes | fail/block | invalid/raise | basis |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| invariant: invariants.identical_output_alarm | ssot/invariants.py:17 | mapping of inputs to outputs | partial | yes if caller treats [] over <2 inputs as pass | cache/comparison wrapper | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | static read; selected support surface |
| invariant: invariants.cache_is_valid | ssot/invariants.py:44 | cache file path | yes | no PASS emitted; boolean helper | cache file | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | static read; selected support surface |

### journal profile

| name | file:line | depends on | shape assert? | PASS without predicate? | consumes | emissions | adjudicated | passes | fail/block | invalid/raise | basis |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| journal profile: journal_profile.check_abstract | ssot/journal_profile.py:88 | abstract text/list | partial | UNKNOWN | journal profile dict | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | static read; selected support surface |
| journal profile: journal_profile.check_keywords | ssot/journal_profile.py:125 | keywords list | partial | UNKNOWN | journal profile dict | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | static read; selected support surface |
| journal profile: journal_profile.check_title_words | ssot/journal_profile.py:135 | title words | partial | UNKNOWN | journal profile dict | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | static read; selected support surface |
| journal profile: journal_profile.enforce | ssot/journal_profile.py:142 | journal profile checks | partial | no PASS emitted; raises ProfileViolation | journal profile dict | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | static read; selected support surface |

### projector gate

| name | file:line | depends on | shape assert? | PASS without predicate? | consumes | emissions | adjudicated | passes | fail/block | invalid/raise | basis |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| projector gate: projectors.readiness | ssot/projectors.py:185 | attestations, registration, results.by_outcome, screening | no | unclear; can emit READY if blocking/outstanding lists stay empty | cached object | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | static read; selected support surface |
| projector gate: projectors.verdict_card | ssot/projectors.py:288 | preconditions/verdict blocks | partial | UNKNOWN | cached object/html renderer | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | static read; selected support surface |
| projector gate: projectors2.screening_cards | ssot/projectors2.py:250 | screening/absent_from_source | partial | UNKNOWN | cached object/html renderer | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | static read; selected support surface |
| projector gate: projectors2.rob2_card | ssot/projectors2.py:735 | rob2/trials | no | no PASS emitted; silently returns empty HTML when subject absent | cached object/html renderer | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | static read; selected support surface |
| projector gate: projectors2.published_comparison_card | ssot/projectors2.py:908 | published_comparison/checks denominator | no | no PASS emitted; silently returns empty HTML when checks/denominator absent | cached object/html renderer | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | static read; selected support surface |

### registered precondition

| name | file:line | depends on | shape assert? | PASS without predicate? | consumes | emissions | adjudicated | passes | fail/block | invalid/raise | basis |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| registered precondition: population_stated | ssot/preconditions.py:110 | question, title | yes (assessment.read/judge path; registry type guard where declared) | no observed PASS without predicate; NOT_ASSESSABLE is explicit | ssot/<topic>/<topic>.json cached object | 137 | 135 | 135 | 0 | 2 | executed corpus_assess.build_report without writing corpus_assess.json |
| registered precondition: arm_role_resolved | ssot/preconditions.py:139 | inputs.trials | yes (assessment.read/judge path; registry type guard where declared) | no observed PASS without predicate; NOT_ASSESSABLE is explicit | ssot/<topic>/<topic>.json cached object | 137 | 49 | 49 | 0 | 88 | executed corpus_assess.build_report without writing corpus_assess.json |
| registered precondition: comparators_identified_and_consistent | ssot/preconditions.py:182 | outcomes.comparator, outcomes.comparator_type | yes (assessment.read/judge path; registry type guard where declared) | no observed PASS without predicate; NOT_ASSESSABLE is explicit | ssot/<topic>/<topic>.json cached object | 137 | 74 | 70 | 4 | 63 | executed corpus_assess.build_report without writing corpus_assess.json |
| registered precondition: estimand_named | ssot/preconditions.py:225 | outcomes.estimand, outcomes.definition | yes (assessment.read/judge path; registry type guard where declared) | no observed PASS without predicate; NOT_ASSESSABLE is explicit | ssot/<topic>/<topic>.json cached object | 137 | 135 | 135 | 0 | 2 | executed corpus_assess.build_report without writing corpus_assess.json |
| registered precondition: criteria_stated | ssot/preconditions.py:279 | screening.eligibility | yes (assessment.read/judge path; registry type guard where declared) | no observed PASS without predicate; NOT_ASSESSABLE is explicit | ssot/<topic>/<topic>.json cached object | 137 | 42 | 6 | 36 | 95 | executed corpus_assess.build_report without writing corpus_assess.json |
| registered precondition: criteria_predefined | ssot/preconditions.py:299 | screening.eligibility_provenance, absent_from_source.protocol | yes (assessment.read/judge path; registry type guard where declared) | no observed PASS without predicate; NOT_ASSESSABLE is explicit | ssot/<topic>/<topic>.json cached object | 137 | 36 | 0 | 36 | 101 | executed corpus_assess.build_report without writing corpus_assess.json |
| registered precondition: eligibility_met | ssot/preconditions.py:343 | screening.eligibility, sources | yes (assessment.read/judge path; registry type guard where declared) | no observed PASS without predicate; NOT_ASSESSABLE is explicit | ssot/<topic>/<topic>.json cached object | 137 | 0 | 0 | 0 | 137 | executed corpus_assess.build_report without writing corpus_assess.json |
| registered precondition: contributes_a_randomised_contrast | ssot/preconditions.py:440 | inputs.trials.arms | yes (assessment.read/judge path; registry type guard where declared) | no observed PASS without predicate; NOT_ASSESSABLE is explicit | ssot/<topic>/<topic>.json cached object | 137 | 49 | 49 | 0 | 88 | executed corpus_assess.build_report without writing corpus_assess.json |

### static candidate

| name | file:line | depends on | shape assert? | PASS without predicate? | consumes | emissions | adjudicated | passes | fail/block | invalid/raise | basis |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| static candidate: ParseGateError | scripts/_js_parse_gate.py:33 | UNKNOWN | UNKNOWN | UNKNOWN | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: assert_js_parse_ok | scripts/_js_parse_gate.py:118 | UNKNOWN | partial | UNKNOWN | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: check | scripts/absence_reason_gate.py:49 | UNKNOWN | UNKNOWN | UNKNOWN | HTML/page surface | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: selftest | scripts/absence_reason_gate.py:88 | search, paper | UNKNOWN | UNKNOWN | HTML/page surface | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: jscheck | scripts/add_offline_download.py:20 | UNKNOWN | UNKNOWN | UNKNOWN | process/hook status | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: audit_nct_in_topic | scripts/add_topic_audit_first.py:246 | A_aact_exists, aact_title, brief_title, aact_acronym, acronym, start_date, primary_completion_date, B_drug_in_intvs, aact_intvs, C_condition_in_aact, aact_conditions, pmid | UNKNOWN | yes | MCP/ClinicalTrials.gov payload | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: audit_nct | scripts/add_topic_autodiscover.py:5507 | A_aact_exists, aact_title, brief_title, aact_acronym, acronym, start_date, primary_completion_date, B_drug_in_intvs, C_condition_in_aact, aact_intvs, aact_conditions, pmid | UNKNOWN | yes | MCP/ClinicalTrials.gov payload | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: check_presentation | scripts/alignment_gate.py:169 | font, line_spacing, tables, tbl_header, over_measure, tbl_styles, measure_in | UNKNOWN | yes | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: check | scripts/alignment_gate.py:187 | text, n, tables, figures, heads, pres, caption, kind, head_levels | UNKNOWN | UNKNOWN | HTML/page surface | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: selftest | scripts/alignment_gate.py:262 | tables, figures, heads, pres, text | UNKNOWN | yes | HTML/page surface | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: classify | scripts/analyze_poolability.py:182 | UNKNOWN | UNKNOWN | UNKNOWN | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: selftest | scripts/analyze_poolability.py:199 | UNKNOWN | UNKNOWN | UNKNOWN | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: assess | scripts/arm_identity_gate.py:118 | role, intervention, control, arms, label | UNKNOWN | yes | HTML/page surface | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: page_verdict | scripts/arm_identity_gate.py:224 | _raw, _schema | UNKNOWN | yes | HTML/page surface | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: selftest | scripts/arm_identity_gate.py:242 | UNKNOWN | UNKNOWN | yes | cached/json file or build artefact; HTML/page surface | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: classify | scripts/artefact_registry.py:81 | UNKNOWN | UNKNOWN | UNKNOWN | cached/json file or build artefact | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: grim_check | scripts/audit_12methods.py:103 | UNKNOWN | UNKNOWN | yes | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: audit_review | scripts/audit_12methods.py:134 | realData, pmid, year, tE, tN, cE, cN, publishedHR, hrLCI, hrUCI, singleArm, baseline | UNKNOWN | yes | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: check_01_python_none_in_js | scripts/audit_40_checks.py:54 | UNKNOWN | UNKNOWN | UNKNOWN | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: check_02_python_True_False_in_js | scripts/audit_40_checks.py:66 | UNKNOWN | UNKNOWN | UNKNOWN | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: check_03_unmatched_script_tag | scripts/audit_40_checks.py:76 | UNKNOWN | UNKNOWN | yes | HTML/page surface | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: check_04_div_balance | scripts/audit_40_checks.py:111 | UNKNOWN | UNKNOWN | yes | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: check_05_broken_local_links | scripts/audit_40_checks.py:122 | UNKNOWN | UNKNOWN | yes | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: check_06_unpopulated_placeholders | scripts/audit_40_checks.py:138 | UNKNOWN | UNKNOWN | UNKNOWN | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: check_07_empty_pmid_link | scripts/audit_40_checks.py:156 | UNKNOWN | UNKNOWN | yes | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: check_08_event_count_consistency | scripts/audit_40_checks.py:167 | tE, tN, cE, cN | UNKNOWN | UNKNOWN | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: check_09_rob_array_length | scripts/audit_40_checks.py:193 | UNKNOWN | UNKNOWN | UNKNOWN | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: check_10_nct_in_auto_include_vs_realdata | scripts/audit_40_checks.py:209 | UNKNOWN | UNKNOWN | yes | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: check_11_duplicate_html_ids | scripts/audit_40_checks.py:226 | UNKNOWN | UNKNOWN | yes | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: check_12_truncated_outcome_titles | scripts/audit_40_checks.py:237 | UNKNOWN | UNKNOWN | UNKNOWN | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: check_13_hardcoded_local_paths | scripts/audit_40_checks.py:252 | UNKNOWN | UNKNOWN | UNKNOWN | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: check_14_invalid_pmid_format | scripts/audit_40_checks.py:262 | UNKNOWN | UNKNOWN | UNKNOWN | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: check_15_outcome_special_chars | scripts/audit_40_checks.py:275 | UNKNOWN | UNKNOWN | UNKNOWN | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: check_16_external_cdn_inside_csp | scripts/audit_40_checks.py:284 | UNKNOWN | UNKNOWN | yes | MCP/ClinicalTrials.gov payload | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: check_17_year_plausibility | scripts/audit_40_checks.py:305 | UNKNOWN | UNKNOWN | UNKNOWN | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: check_18_viewport_meta | scripts/audit_40_checks.py:320 | UNKNOWN | UNKNOWN | yes | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: check_19_inline_script_size | scripts/audit_40_checks.py:327 | UNKNOWN | UNKNOWN | UNKNOWN | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: check_20_localStorage_key_collision | scripts/audit_40_checks.py:339 | UNKNOWN | UNKNOWN | UNKNOWN | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: check_21_meta_description | scripts/audit_40_checks.py:351 | UNKNOWN | UNKNOWN | yes | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: check_22_outcome_title_dupe | scripts/audit_40_checks.py:358 | UNKNOWN | UNKNOWN | yes | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: check_23_svg_invalid_coords | scripts/audit_40_checks.py:367 | UNKNOWN | UNKNOWN | UNKNOWN | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: check_24_orphan_close_tag | scripts/audit_40_checks.py:390 | UNKNOWN | UNKNOWN | UNKNOWN | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: check_25_orphan_anchor_with_no_text | scripts/audit_40_checks.py:402 | UNKNOWN | UNKNOWN | UNKNOWN | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: check_26_inconsistent_acronyms | scripts/audit_40_checks.py:412 | UNKNOWN | UNKNOWN | UNKNOWN | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: check_27_huge_file | scripts/audit_40_checks.py:427 | UNKNOWN | UNKNOWN | yes | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: check_28_tiny_file | scripts/audit_40_checks.py:435 | UNKNOWN | UNKNOWN | yes | HTML/page surface | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: check_29_dashboard_link_orphan | scripts/audit_40_checks.py:443 | UNKNOWN | UNKNOWN | yes | HTML/page surface | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: check_30_double_quoted_attr_with_unescaped_quote | scripts/audit_40_checks.py:449 | UNKNOWN | UNKNOWN | UNKNOWN | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: check_31_window_global_unset | scripts/audit_40_checks.py:459 | UNKNOWN | UNKNOWN | yes | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: check_32_no_h1 | scripts/audit_40_checks.py:472 | UNKNOWN | UNKNOWN | yes | HTML/page surface | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: check_33_pmid_link_mismatch_with_realdata | scripts/audit_40_checks.py:479 | UNKNOWN | UNKNOWN | UNKNOWN | HTML/page surface | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: check_34_screening_template_old | scripts/audit_40_checks.py:504 | UNKNOWN | UNKNOWN | yes | MCP/ClinicalTrials.gov payload; HTML/page surface | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: check_35_robots_no_robots | scripts/audit_40_checks.py:512 | UNKNOWN | UNKNOWN | yes | HTML/page surface | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: check_36_target_blank_no_noopener | scripts/audit_40_checks.py:519 | UNKNOWN | UNKNOWN | UNKNOWN | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: check_37_inconsistent_drug_name | scripts/audit_40_checks.py:531 | UNKNOWN | UNKNOWN | yes | HTML/page surface | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: check_38_nesting_via_template_literal | scripts/audit_40_checks.py:546 | UNKNOWN | UNKNOWN | UNKNOWN | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: check_39_aria_label_missing_on_button | scripts/audit_40_checks.py:560 | UNKNOWN | UNKNOWN | UNKNOWN | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: check_40_orphan_pubmed_link | scripts/audit_40_checks.py:574 | UNKNOWN | UNKNOWN | UNKNOWN | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: audit_one | scripts/audit_app_quality.py:28 | UNKNOWN | UNKNOWN | yes | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: audit_file | scripts/audit_data_integrity.py:118 | nct, header, name | UNKNOWN | UNKNOWN | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: audit_first_pages | scripts/audit_first_poolability_triage.py:192 | UNKNOWN | UNKNOWN | UNKNOWN | cached/json file or build artefact; HTML/page surface | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: audit | scripts/audit_multiarm.py:38 | inc, pmid, name, cE, cN | UNKNOWN | yes | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: audit_file | scripts/audit_or_vs_rr.py:60 | UNKNOWN | UNKNOWN | yes | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: audit_file | scripts/audit_outcome_types.py:60 | estimandType, type, has_md, has_se, has_tE, has_cE | UNKNOWN | yes | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: audit_file | scripts/audit_review_arm_counts.py:55 | UNKNOWN | UNKNOWN | yes | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: classify | scripts/audit_rob2_completeness.py:37 | UNKNOWN | UNKNOWN | yes | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: PARSE-FAILED | scripts/audit_structural.py:1 | UNKNOWN | UNKNOWN | UNKNOWN | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST parse failed: SyntaxError: invalid escape sequence '\s' (<unknown>, line 6) |
| static candidate: check_file | scripts/audit_v65_engine_coverage.py:61 | fail_count, failed | UNKNOWN | yes | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: jscheck | scripts/backfill_pmids.py:26 | UNKNOWN | UNKNOWN | UNKNOWN | process/hook status | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: _classify_loose | scripts/backfill_published_hr.py:55 | UNKNOWN | UNKNOWN | UNKNOWN | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: selftest | scripts/banner_anchor.py:59 | UNKNOWN | UNKNOWN | UNKNOWN | HTML/page surface | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: classify | scripts/build_aact_counts_with_param_type.py:66 | UNKNOWN | UNKNOWN | UNKNOWN | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: check | scripts/build_stamp_gate.py:31 | UNKNOWN | UNKNOWN | yes | HTML/page surface | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: selftest | scripts/build_stamp_gate.py:46 | UNKNOWN | UNKNOWN | yes | HTML/page surface | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: required | scripts/buildability_check.py:38 | UNKNOWN | UNKNOWN | yes | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: check | scripts/card_alignment_gate.py:171 | UNKNOWN | UNKNOWN | yes | HTML/page surface | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: audit_vocabulary | scripts/card_alignment_gate.py:213 | UNKNOWN | UNKNOWN | yes | HTML/page surface | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: selftest | scripts/card_alignment_gate.py:335 | UNKNOWN | UNKNOWN | yes | HTML/page surface | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: classify | scripts/census_render_verify.py:42 | UNKNOWN | UNKNOWN | UNKNOWN | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: check_trial | scripts/citation_year_gate.py:50 | year, epub_date, name, id, pmid, citation_year_basis | UNKNOWN | yes | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: check | scripts/citation_year_gate.py:93 | trials, citations, inputs | partial | yes | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: selftest | scripts/citation_year_gate.py:101 | UNKNOWN | partial | UNKNOWN | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: screen | scripts/class4_external_comparator_screen.py:84 | error, primaries, groups, has_results, arms, title | UNKNOWN | yes | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: classify | scripts/classify_nma_drops.py:57 | cfg_ncts, treatments | UNKNOWN | yes | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: _check_text | scripts/clone_contamination_gate.py:349 | UNKNOWN | UNKNOWN | UNKNOWN | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: _scan_app_integrity | scripts/clone_contamination_gate.py:518 | UNKNOWN | UNKNOWN | UNKNOWN | HTML/page surface | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: verdict_payload | scripts/clone_contamination_gate.py:551 | UNKNOWN | UNKNOWN | UNKNOWN | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: verdict_grade | scripts/clone_contamination_gate.py:557 | UNKNOWN | UNKNOWN | UNKNOWN | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: is_green_verdict | scripts/clone_contamination_gate.py:562 | UNKNOWN | UNKNOWN | UNKNOWN | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: inherited_verdict | scripts/clone_contamination_gate.py:567 | UNKNOWN | UNKNOWN | UNKNOWN | HTML/page surface | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: assert_no_silent_skip | scripts/clone_contamination_gate.py:609 | UNKNOWN | partial | UNKNOWN | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: assert_clean | scripts/clone_contamination_gate.py:643 | UNKNOWN | UNKNOWN | UNKNOWN | HTML/page surface | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: selftest | scripts/clone_contamination_gate.py:691 | UNKNOWN | UNKNOWN | yes | HTML/page surface | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: check | scripts/content_gate.py:88 | UNKNOWN | UNKNOWN | yes | HTML/page surface | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: selftest | scripts/corpus/corpus_detectors.py:503 | UNKNOWN | UNKNOWN | yes | HTML/page surface | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: _gate_protocol_date | scripts/corpus/corpus_wave.py:247 | UNKNOWN | UNKNOWN | UNKNOWN | HTML/page surface | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: _gate_pagination_callsite | scripts/corpus/corpus_wave.py:292 | UNKNOWN | UNKNOWN | UNKNOWN | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: _gate_benchmark_keys | scripts/corpus/corpus_wave.py:300 | UNKNOWN | UNKNOWN | UNKNOWN | HTML/page surface | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: reconcile | scripts/corpus/corpus_wave.py:963 | UNKNOWN | UNKNOWN | UNKNOWN | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: census | scripts/corpus/run_rollout.py:80 | UNKNOWN | UNKNOWN | yes | HTML/page surface | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: assert_safe_branch | scripts/corpus/run_rollout.py:123 | UNKNOWN | partial | UNKNOWN | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: guards_for | scripts/corpus/w7_guards.py:85 | AUTO_INCLUDE | UNKNOWN | yes | HTML/page surface | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: assess | scripts/count_provenance_gate.py:96 | registration_primary_counts, outcome_definition, treatment_events, control_events, treatment_n, control_n, registration_other_outcome_counts, counts, title, matched_on, by_outcome | UNKNOWN | yes | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: check | scripts/count_provenance_gate.py:211 | trials, by_outcome, headline_outcome, inputs, results, nct, name | UNKNOWN | yes | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: selftest | scripts/count_provenance_gate.py:231 | UNKNOWN | UNKNOWN | yes | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: classify | scripts/cross_check_external.py:254 | measure, k, OR, est, source | UNKNOWN | UNKNOWN | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: audit_app | scripts/data_integrity_audit.py:142 | UNKNOWN | UNKNOWN | yes | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: assess | scripts/declared_contrast_gate.py:74 | registration_arm_count, registration_declared_contrasts, label, arms, role | UNKNOWN | yes | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: check | scripts/declared_contrast_gate.py:117 | trials, inputs, nct, name | UNKNOWN | yes | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: selftest | scripts/declared_contrast_gate.py:139 | UNKNOWN | UNKNOWN | yes | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: check | scripts/double_escape_gate.py:60 | UNKNOWN | UNKNOWN | yes | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: selftest | scripts/double_escape_gate.py:74 | UNKNOWN | UNKNOWN | yes | HTML/page surface | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: check | scripts/durable_artefact_gate.py:85 | UNKNOWN | UNKNOWN | yes | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: selftest | scripts/durable_artefact_gate.py:141 | UNKNOWN | UNKNOWN | UNKNOWN | cached/json file or build artefact | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: check | scripts/estimand_definition_gate.py:309 | trials, by_outcome, pooled, withdrawn, k, point, name, nct, endpoint_rank, source_quotes, inputs, results | UNKNOWN | yes | HTML/page surface | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: selftest | scripts/estimand_definition_gate.py:477 | k, endpoint_rank, outcome_definition, o, outcome_definition_source, trials, by_outcome, pooled, withdrawn, previous_values, inputs, results | UNKNOWN | UNKNOWN | MCP/ClinicalTrials.gov payload; cached/json file or build artefact | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: selftest | scripts/export_artefact.py:337 | by_outcome, pool_capability, trials, point, row_id, NCT01453608::six_min_walk_24w, inputs, poolable, pooled, engine_can_pool, engine_block_reason, measure | UNKNOWN | yes | cached/json file or build artefact; wrapper/adapter payload | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: check | scripts/extraction_table_gate.py:42 | missing, resolution | UNKNOWN | yes | HTML/page surface | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: selftest | scripts/extraction_table_gate.py:118 | missing | UNKNOWN | yes | HTML/page surface | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: audit | scripts/figure_audit.py:166 | _n, _sig, circles, rects, title, aria, geom, caption | partial | UNKNOWN | cached/json file or build artefact; HTML/page surface | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: fix_screening_template | scripts/fix_audit40_findings.py:162 | UNKNOWN | UNKNOWN | UNKNOWN | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: build_verdict | scripts/fix_false_green_zero_data.py:46 | UNKNOWN | UNKNOWN | UNKNOWN | HTML/page surface | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: jscheck | scripts/fix_method_drift_v2.py:42 | UNKNOWN | UNKNOWN | UNKNOWN | process/hook status | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: replace_verdict | scripts/fix_mislabelled_apps.py:113 | UNKNOWN | UNKNOWN | UNKNOWN | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: check_shell | scripts/gate_integrity.py:328 | UNKNOWN | UNKNOWN | UNKNOWN | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: check_scope | scripts/gate_integrity.py:339 | UNKNOWN | UNKNOWN | yes | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: check_python_gate | scripts/gate_integrity.py:368 | UNKNOWN | partial | yes | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: selftest | scripts/gate_integrity.py:413 | UNKNOWN | UNKNOWN | UNKNOWN | process/hook status | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: assess_outcome | scripts/headline_reproducible_gate.py:136 | pooled, withdrawn, point, ci_low, ci_high | UNKNOWN | yes | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: check | scripts/headline_reproducible_gate.py:241 | by_outcome, id, measure, outcomes, results, pooled | UNKNOWN | yes | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: selftest | scripts/headline_reproducible_gate.py:259 | UNKNOWN | UNKNOWN | yes | HTML/page surface | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: check | scripts/identity_by_registration_gate.py:38 | nct, name | UNKNOWN | yes | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: selftest | scripts/identity_by_registration_gate.py:78 | UNKNOWN | UNKNOWN | UNKNOWN | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: check_document | scripts/identity_gate.py:42 | UNKNOWN | partial | yes | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: check_object | scripts/identity_gate.py:74 | trials, nct, name, id, inputs | partial | yes | cached/json file or build artefact; HTML/page surface | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: selftest | scripts/identity_gate.py:130 | UNKNOWN | partial | UNKNOWN | MCP/ClinicalTrials.gov payload | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: check | scripts/index_markup_gate.py:97 | UNKNOWN | UNKNOWN | UNKNOWN | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: selftest | scripts/index_markup_gate.py:124 | UNKNOWN | UNKNOWN | UNKNOWN | HTML/page surface | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: write_audit_csv | scripts/inject_e156_claim_buttons.py:122 | num, title | UNKNOWN | UNKNOWN | HTML/page surface | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: check | scripts/jscheck.py:28 | UNKNOWN | UNKNOWN | yes | process/hook status | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: check_outcome | scripts/k_consistency_gate.py:154 | per_trial, k, panels, _STALE, fit, count_panels, pooled, ci_low, ci_high, _prose | UNKNOWN | yes | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: check_object | scripts/k_consistency_gate.py:197 | manuscript, pooled, ci_low, ci_high, k, by_outcome, per_trial, results | UNKNOWN | UNKNOWN | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: selftest | scripts/k_consistency_gate.py:237 | UNKNOWN | UNKNOWN | UNKNOWN | cached/json file or build artefact | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: Check | scripts/nafis_harness/check.py:88 | ok, misbehaved, vacuous_terms, reason, mutants_run, terms, verdict, _mutant_label, fired, silent, unexercised_terms, fixture | partial | yes | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: guarded_at_class_level | scripts/nafis_harness/ledger.py:58 | UNKNOWN | UNKNOWN | UNKNOWN | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: effective_guard_state | scripts/nafis_harness/ledger.py:589 | UNKNOWN | UNKNOWN | yes | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: unguarded_queue | scripts/nafis_harness/ledger.py:648 | UNKNOWN | UNKNOWN | UNKNOWN | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: Verdict | scripts/nafis_harness/verdict.py:36 | UNKNOWN | partial | UNKNOWN | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: classify | scripts/overclaim_detector.py:63 | UNKNOWN | UNKNOWN | yes | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: classify | scripts/page_family_and_emptiness.py:48 | UNKNOWN | UNKNOWN | UNKNOWN | HTML/page surface | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: classify | scripts/pending_vs_impossible.py:45 | k, topic_state, which_limb_fails, DUPLICATION_NOTICE, primary, poolable, poolable_reason, by_outcome, results | UNKNOWN | UNKNOWN | HTML/page surface | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: classify | scripts/poolability.py:51 | I2, canonical, estimand, k, pooled, outcome_definition, point, by_outcome, withdrawn, results, withdrawn_reason | UNKNOWN | yes | HTML/page surface | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: selftest | scripts/poolability.py:156 | trials, inputs, outcome_definition, source_quotes, by_outcome, provenance | UNKNOWN | yes | cached/json file or build artefact | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: selftest | scripts/pooled_value_gate.py:107 | UNKNOWN | partial | UNKNOWN | cached/json file or build artefact; HTML/page surface | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: _classify | scripts/populate_pmids.py:236 | UNKNOWN | UNKNOWN | UNKNOWN | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: assess_trial | scripts/precision_sample_gate.py:59 | variance, effect, measure, scale, role, intervention, control, events, n, arms | UNKNOWN | yes | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: selftest | scripts/precision_sample_gate.py:104 | trials, canonical, label, identity | UNKNOWN | UNKNOWN | cached/json file or build artefact; HTML/page surface | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: selftest | scripts/project_index_cards.py:200 | headline_outcome, results | UNKNOWN | yes | HTML/page surface | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: check | scripts/prose_claim_gate.py:100 | ci_low, ci_high, pooled, by_outcome, results, point | partial | yes | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: selftest | scripts/prose_claim_gate.py:174 | manuscript, search, pooled, o, by_outcome, results | partial | UNKNOWN | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: check | scripts/protocol_subject_gate.py:167 | UNKNOWN | UNKNOWN | yes | HTML/page surface | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: selftest | scripts/protocol_subject_gate.py:234 | UNKNOWN | UNKNOWN | yes | HTML/page surface | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: null_screening_ids | scripts/prove_vanish_invariant.py:52 | records, nct, pmid, screening | UNKNOWN | UNKNOWN | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: screen | scripts/published_synthesis_screen.py:98 | abstract, decision, estimand_sentence_in_abstract, title, year, journal, why, pmid | UNKNOWN | yes | cached/json file or build artefact | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: jscheck | scripts/quarantine_apps.py:35 | UNKNOWN | UNKNOWN | UNKNOWN | process/hook status | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: classify_outcome | scripts/r24_design_outcomes.py:87 | UNKNOWN | UNKNOWN | UNKNOWN | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: check_c1 | scripts/r6_internal_consistency.py:125 | publishedHR, tE, tN, cE, cN, estimandType | UNKNOWN | yes | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: check_c2 | scripts/r6_internal_consistency.py:157 | tE, tN, cE, cN, publishedHR | UNKNOWN | yes | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: check_c3 | scripts/r6_internal_consistency.py:191 | UNKNOWN | UNKNOWN | yes | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: check_c4 | scripts/r6_internal_consistency.py:227 | publishedHR, hrLCI, hrUCI, estimandType | UNKNOWN | yes | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: check_c5 | scripts/r6_internal_consistency.py:258 | year | UNKNOWN | yes | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: check_c6 | scripts/r6_internal_consistency.py:289 | name | UNKNOWN | yes | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: check_c7 | scripts/r6b_more_internal_checks.py:108 | pmid | UNKNOWN | yes | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: check_c8 | scripts/r6b_more_internal_checks.py:139 | baseline, n, tN, cN | UNKNOWN | yes | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: check_c9 | scripts/r6b_more_internal_checks.py:163 | publishedHR, hrLCI, hrUCI | UNKNOWN | yes | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: check_c10 | scripts/r6c_more_internal_checks.py:108 | name | UNKNOWN | yes | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: check_c13 | scripts/r6c_more_internal_checks.py:136 | publishedHR, estimandType | UNKNOWN | UNKNOWN | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: check_c14 | scripts/r6c_more_internal_checks.py:180 | year | UNKNOWN | UNKNOWN | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: check_c16 | scripts/r6c_more_internal_checks.py:204 | publishedHR, estimandType | UNKNOWN | yes | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: check_c19 | scripts/r6c_more_internal_checks.py:237 | nctAcronyms, realData, name | UNKNOWN | yes | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: already_validated | scripts/r_validate_common.py:57 | UNKNOWN | UNKNOWN | yes | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: validate_index_entry | scripts/r_validate_common.py:107 | stem, has_realData | UNKNOWN | UNKNOWN | cached/json file or build artefact | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: validate_r_output | scripts/r_validate_common.py:115 | fit_ok, engine | UNKNOWN | yes | wrapper/adapter payload | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: assess | scripts/rebuild_guard.py:64 | UNKNOWN | UNKNOWN | UNKNOWN | HTML/page surface | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: guard_write | scripts/rebuild_guard.py:89 | UNKNOWN | partial | UNKNOWN | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: selftest | scripts/rebuild_guard.py:107 | UNKNOWN | UNKNOWN | UNKNOWN | cached/json file or build artefact; HTML/page surface | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: reclassify | scripts/reclassify_pmid_audit.py:176 | esummary_title, claimed_name, file | UNKNOWN | yes | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: classify | scripts/reclassify_pmid_v3.py:62 | esummary_title, claimed_name, file, nct | UNKNOWN | yes | HTML/page surface | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: classify | scripts/recompute_audit_bands.py:59 | publishedHR, tE, tN, cE, cN | UNKNOWN | yes | HTML/page surface | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: check | scripts/registration_identity_gate.py:110 | trials, by_outcome, identity_conflict, registration_enrolment, registration_arm_count, name, nct, inputs, results, arms, role | UNKNOWN | yes | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: selftest | scripts/registration_identity_gate.py:184 | registration_enrolment, identity_conflict | UNKNOWN | yes | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: _assert_server_identity | scripts/regression_check.py:82 | UNKNOWN | partial | UNKNOWN | HTML/page surface | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: check | scripts/regression_guard.py:161 | app, k, values, apps | UNKNOWN | yes | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: check_all | scripts/regression_guard.py:240 | apps, app_id, verdict, lost, kind, reason | UNKNOWN | yes | cached/json file or build artefact; HTML/page surface | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: verify | scripts/resolve_unresolved_pmids.py:48 | UNKNOWN | UNKNOWN | yes | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: ScreenFailure | scripts/screen_harness.py:54 | UNKNOWN | UNKNOWN | UNKNOWN | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: assert_recall | scripts/screen_harness.py:76 | nct, name | partial | yes | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: assert_coverage | scripts/screen_harness.py:90 | pmid | partial | UNKNOWN | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: assert_no_drift | scripts/screen_harness.py:99 | UNKNOWN | partial | yes | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: assert_writes_in_cwd | scripts/screen_harness.py:110 | UNKNOWN | partial | yes | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: selftest | scripts/screen_harness.py:119 | ids, pubmed, ctgov, pmid | UNKNOWN | yes | MCP/ClinicalTrials.gov payload; cached/json file or build artefact | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: check | scripts/search_recall_gate.py:42 | UNKNOWN | UNKNOWN | yes | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: selftest | scripts/search_recall_gate.py:71 | ctgov | UNKNOWN | yes | MCP/ClinicalTrials.gov payload; cached/json file or build artefact | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: check | scripts/section_manifest_gate.py:82 | UNKNOWN | UNKNOWN | UNKNOWN | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: selftest | scripts/section_manifest_gate.py:93 | blocks | UNKNOWN | UNKNOWN | cached/json file or build artefact; HTML/page surface | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: assess | scripts/silent_exclusion_screen.py:125 | tE, cE, name, hr, tN, cN | UNKNOWN | UNKNOWN | HTML/page surface | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: selftest | scripts/silent_exclusion_screen.py:145 | UNKNOWN | UNKNOWN | yes | HTML/page surface | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: check | scripts/ssot_net_deletion_check.py:70 | UNKNOWN | UNKNOWN | UNKNOWN | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: classify | scripts/ssot_signals.py:24 | UNKNOWN | UNKNOWN | UNKNOWN | HTML/page surface | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: sig_no_verdict | scripts/ssot_signals.py:65 | UNKNOWN | UNKNOWN | yes | HTML/page surface | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: sig_constant_verdict | scripts/ssot_signals.py:82 | UNKNOWN | UNKNOWN | UNKNOWN | HTML/page surface | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: sig_k_asserted_settled | scripts/ssot_signals.py:230 | UNKNOWN | UNKNOWN | UNKNOWN | HTML/page surface | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: assess | scripts/subject_is_experimental_gate.py:104 | UNKNOWN | UNKNOWN | yes | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: selftest | scripts/subject_is_experimental_gate.py:142 | UNKNOWN | UNKNOWN | yes | HTML/page surface | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: check | scripts/subject_match_gate.py:69 | UNKNOWN | UNKNOWN | UNKNOWN | HTML/page surface | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: selftest | scripts/subject_match_gate.py:123 | UNKNOWN | UNKNOWN | UNKNOWN | cached/json file or build artefact; HTML/page surface | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: classify_trial | scripts/sweep_synthetic_fixtures.py:58 | pmid, year, tN, baseline, n | UNKNOWN | UNKNOWN | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: test_fix_audit40_findings_is_idempotent | scripts/tests/test_idempotency.py:130 | UNKNOWN | UNKNOWN | UNKNOWN | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: test_js_parse_gate_accepts_valid_realdata | scripts/tests/test_idempotency.py:218 | UNKNOWN | UNKNOWN | UNKNOWN | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: test_js_parse_gate_rejects_python_none | scripts/tests/test_idempotency.py:224 | UNKNOWN | UNKNOWN | UNKNOWN | MCP/ClinicalTrials.gov payload | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: test_propagate_pi_k1_idempotent | scripts/tests/test_idempotency_v2.py:97 | UNKNOWN | UNKNOWN | UNKNOWN | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: test_fix_integrity_badge_contrast_idempotent | scripts/tests/test_idempotency_v2.py:109 | UNKNOWN | UNKNOWN | UNKNOWN | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: selftest | scripts/text_match.py:80 | UNKNOWN | UNKNOWN | UNKNOWN | HTML/page surface | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: Verdict | scripts/verdict.py:49 | UNKNOWN | partial | UNKNOWN | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: selftest | scripts/verdict.py:88 | UNKNOWN | partial | UNKNOWN | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: check | scripts/verdict_gate.py:86 | UNKNOWN | UNKNOWN | yes | cached/json file or build artefact; HTML/page surface | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: checks | scripts/verify_decontamination.py:28 | UNKNOWN | UNKNOWN | UNKNOWN | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: assess | scripts/withdrawal_reason_gate.py:138 | by_outcome, pooled, withdrawn, results | UNKNOWN | yes | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: selftest | scripts/withdrawal_reason_gate.py:171 | UNKNOWN | UNKNOWN | yes | HTML/page surface | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: assess | ssot/assessment.py:157 | UNKNOWN | yes | UNKNOWN | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: inclusion_criteria_auditable | ssot/assessment.py:302 | UNKNOWN | yes | UNKNOWN | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: require_named_intervention | ssot/assessment.py:359 | UNKNOWN | partial | yes | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: _selftest | ssot/assessor_registry.py:83 | UNKNOWN | partial | UNKNOWN | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: AssessorRejected | ssot/assessor_registry.py:99 | UNKNOWN | UNKNOWN | UNKNOWN | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: check_unit | ssot/assessor_registry.py:182 | UNKNOWN | partial | yes | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: assessor | ssot/assessor_registry.py:239 | UNKNOWN | UNKNOWN | UNKNOWN | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: type_guard | ssot/assessor_registry.py:245 | UNKNOWN | yes | yes | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: not_assessable_verdicts | ssot/corpus_assess.py:89 | UNKNOWN | UNKNOWN | UNKNOWN | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: run_precondition | ssot/corpus_assess.py:96 | UNKNOWN | UNKNOWN | UNKNOWN | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: run_preconditions | ssot/corpus_assess.py:105 | UNKNOWN | UNKNOWN | UNKNOWN | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: tally_preconditions | ssot/corpus_assess.py:178 | verdicts | UNKNOWN | UNKNOWN | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: batch1_known_answer_check | ssot/corpus_assess.py:191 | topics | UNKNOWN | UNKNOWN | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: validate_cascade_entry | ssot/corpus_reconcile.py:81 | roles | partial | UNKNOWN | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: reconcile_topic | ssot/corpus_reconcile.py:131 | k3_experimental, experimental_ids, k0_surfaced_raw | partial | yes | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: require_raw_v2 | ssot/ctgov_transport.py:77 | UNKNOWN | yes | UNKNOWN | MCP/ClinicalTrials.gov payload | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: check_abstract | ssot/journal_profile.py:88 | abstract_sections, abstract_max_words, abstract_allows_citations | UNKNOWN | yes | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: check_keywords | ssot/journal_profile.py:125 | keywords_max | UNKNOWN | yes | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: check_title_words | ssot/journal_profile.py:135 | UNKNOWN | UNKNOWN | UNKNOWN | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: enforce | ssot/journal_profile.py:142 | name | partial | UNKNOWN | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: readiness | ssot/projectors.py:185 | by_outcome, attestations, registration, results, is_lower_bound, screening, screening_names_unresolved, commits, ordering, verdict, publication_bias, rating | UNKNOWN | yes | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: verdict_card | ssot/projectors.py:288 | blocking, outstanding, limitations, leave_one_out_finding, state, by_outcome, results, label, detail, what, sensitivity, why | UNKNOWN | UNKNOWN | HTML/page surface | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: screening_cards | ssot/projectors2.py:250 | trials, screening, inputs, inclusion_provenance, records, disposition, criteria_failed, note, pmid, evidence_basis, name, id | UNKNOWN | UNKNOWN | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |
| static candidate: classify_record | ssot/synthesis_reconcile.py:105 | year, ncts, abstract, pubtypes, journal | UNKNOWN | UNKNOWN | local object/source | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AST name-pattern scan; not all candidates are runtime gates |

### synthesis assessor

| name | file:line | depends on | shape assert? | PASS without predicate? | consumes | emissions | adjudicated | passes | fail/block | invalid/raise | basis |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| synthesis assessor: synthesis_reconcile.select_included_table | ssot/synthesis_reconcile.py:50 | tables/title/header/ids | partial | no PASS label; returns NOT-ASSESSABLE/REFUSED on no/multiple candidates | PDF/table extraction wrapper | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | static read; selected support surface |
| synthesis assessor: synthesis_reconcile.classify_record | ssot/synthesis_reconcile.py:105 | trial id/status/category | partial | no PASS label; unknowns become UNCATEGORISED | source/corpus record | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | static read; selected support surface |
| synthesis assessor: synthesis_reconcile.rate_is_quotable | ssot/synthesis_reconcile.py:153 | classification counts | yes | no PASS label; fail-closed on zero total or high uncategorised share | classification tally | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | static read; selected support surface |

### topic assessor

| name | file:line | depends on | shape assert? | PASS without predicate? | consumes | emissions | adjudicated | passes | fail/block | invalid/raise | basis |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| topic assessor: topic_identity.locate | ssot/topic_identity.py:77 | protocolSection.armsInterventionsModule.armGroups/interventions | no | yes for verdict-shaped NOT_ASSESSABLE on flattened MCP shape | MCP/ClinicalTrials.gov payload | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | static read; selected support surface |

### transport guard

| name | file:line | depends on | shape assert? | PASS without predicate? | consumes | emissions | adjudicated | passes | fail/block | invalid/raise | basis |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| transport guard: ctgov_transport.require_raw_v2 | ssot/ctgov_transport.py:77 | protocolSection.armsInterventionsModule | yes | no PASS emitted; raises WrongPayloadShape | MCP/ClinicalTrials.gov raw-v2 payload | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | static read; selected support surface |

### validate_v2 detector

| name | file:line | depends on | shape assert? | PASS without predicate? | consumes | emissions | adjudicated | passes | fail/block | invalid/raise | basis |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| validate_v2 detector: against-sources | ssot/validate_v2.py:222 | trials, app_id, staged_as, inputs, nct, source_outcome_title, effect, sources, by_outcome, provenance, derived_from, source_quotes | no common schema guard; per-detector run raised on malformed/missing shapes | unclear | ssot/<topic>/<topic>.json cached object; some source-cache helpers | 136 | UNKNOWN | 0 | 135 | 1 | executed detector directly with exceptions captured; validate() CLI aborts on missing modules |
| validate_v2 detector: k-derived | ssot/validate_v2.py:589 | by_outcome, k, results, trials, inputs, effect, treatment, control | no common schema guard; per-detector run raised on malformed/missing shapes | UNKNOWN | ssot/<topic>/<topic>.json cached object; some source-cache helpers | 136 | UNKNOWN | 102 | 33 | 1 | executed detector directly with exceptions captured; validate() CLI aborts on missing modules |
| validate_v2 detector: estimator-labels | ssot/validate_v2.py:609 | by_outcome, results, estimator_used, estimator, model | no common schema guard; per-detector run raised on malformed/missing shapes | unclear | ssot/<topic>/<topic>.json cached object; some source-cache helpers | 136 | UNKNOWN | 119 | 32 | 1 | executed detector directly with exceptions captured; validate() CLI aborts on missing modules |
| validate_v2 detector: per-trial-recompute | ssot/validate_v2.py:662 | by_outcome, per_trial, id, results, trials, trial_id, treatment, control, point, measure, ci_level, inputs | no common schema guard; per-detector run raised on malformed/missing shapes | unclear | ssot/<topic>/<topic>.json cached object; some source-cache helpers | 136 | UNKNOWN | 124 | 12 | 8 | executed detector directly with exceptions captured; validate() CLI aborts on missing modules |
| validate_v2 detector: pooled-recompute | ssot/validate_v2.py:753 | pooled, trials, by_outcome, measure, inputs, effect, heterogeneity, results, treatment, control, estimator_used, DL | no common schema guard; per-detector run raised on malformed/missing shapes | unclear | ssot/<topic>/<topic>.json cached object; some source-cache helpers | 136 | UNKNOWN | 97 | 20 | 31 | executed detector directly with exceptions captured; validate() CLI aborts on missing modules |
| validate_v2 detector: superseded | ssot/validate_v2.py:865 | superseded, trial_ids, by_outcome, effect, estimator_used, DL, results, trials, outcomes, inputs, measure, id | no common schema guard; per-detector run raised on malformed/missing shapes | unclear | ssot/<topic>/<topic>.json cached object; some source-cache helpers | 136 | UNKNOWN | 135 | 0 | 1 | executed detector directly with exceptions captured; validate() CLI aborts on missing modules |
| validate_v2 detector: outcome-coverage | ssot/validate_v2.py:914 | trials, id, by_outcome, inputs, outcomes, results | no common schema guard; per-detector run raised on malformed/missing shapes | UNKNOWN | ssot/<topic>/<topic>.json cached object; some source-cache helpers | 136 | UNKNOWN | 134 | 1 | 1 | executed detector directly with exceptions captured; validate() CLI aborts on missing modules |
| validate_v2 detector: heterogeneity-and-k | ssot/validate_v2.py:928 | by_outcome, poolable, heterogeneity, pooled, results, k, not_poolable_reason | no common schema guard; per-detector run raised on malformed/missing shapes | UNKNOWN | ssot/<topic>/<topic>.json cached object; some source-cache helpers | 136 | UNKNOWN | 23 | 153 | 1 | executed detector directly with exceptions captured; validate() CLI aborts on missing modules |
| validate_v2 detector: removal-disclosure | ssot/validate_v2.py:958 | build_mode, removed_citations, cited_total, categories, removed, total_cited, quarantine, trials, count, retained, detail, inputs | no common schema guard; per-detector run raised on malformed/missing shapes | UNKNOWN | ssot/<topic>/<topic>.json cached object; some source-cache helpers | 136 | UNKNOWN | 10 | 126 | 0 | executed detector directly with exceptions captured; validate() CLI aborts on missing modules |
| validate_v2 detector: trial-scoped-refs | ssot/validate_v2.py:1019 | trials, inputs, id | no common schema guard; per-detector run raised on malformed/missing shapes | UNKNOWN | ssot/<topic>/<topic>.json cached object; some source-cache helpers | 136 | UNKNOWN | 135 | 0 | 1 | executed detector directly with exceptions captured; validate() CLI aborts on missing modules |
| validate_v2 detector: source-ids | ssot/validate_v2.py:1044 | sources | no common schema guard; per-detector run raised on malformed/missing shapes | UNKNOWN | ssot/<topic>/<topic>.json cached object; some source-cache helpers | 136 | UNKNOWN | 113 | 40 | 0 | executed detector directly with exceptions captured; validate() CLI aborts on missing modules |
| validate_v2 detector: arm-roles | ssot/validate_v2.py:1070 | trials, inputs, role, arms_not_used, arms, id, arm_selection_note | no common schema guard; per-detector run raised on malformed/missing shapes | UNKNOWN | ssot/<topic>/<topic>.json cached object; some source-cache helpers | 136 | UNKNOWN | 53 | 0 | 83 | executed detector directly with exceptions captured; validate() CLI aborts on missing modules |
| validate_v2 detector: role-label-agreement | ssot/validate_v2.py:1117 | trials, inputs, arms, comparator_type, role, id, label | no common schema guard; per-detector run raised on malformed/missing shapes | UNKNOWN | ssot/<topic>/<topic>.json cached object; some source-cache helpers | 136 | UNKNOWN | 30 | 61 | 83 | executed detector directly with exceptions captured; validate() CLI aborts on missing modules |
| validate_v2 detector: prose-numerals | ssot/validate_v2.py:1195 | UNKNOWN | no common schema guard; per-detector run raised on malformed/missing shapes | unclear | ssot/<topic>/<topic>.json cached object; some source-cache helpers | 136 | UNKNOWN | 52 | 1508 | 0 | executed detector directly with exceptions captured; validate() CLI aborts on missing modules |
| validate_v2 detector: direction-anchor | ssot/validate_v2.py:1333 | pooled, direction_of_benefit, favours, null_value, by_outcome, ci_high, results, measure, ci_low, outcomes, per_trial, reference_efficacy_percent | no common schema guard; per-detector run raised on malformed/missing shapes | yes | ssot/<topic>/<topic>.json cached object; some source-cache helpers | 136 | UNKNOWN | 12 | 111 | 14 | executed detector directly with exceptions captured; validate() CLI aborts on missing modules |
| validate_v2 detector: counts-sane | ssot/validate_v2.py:1406 | trials, inputs, enrolled, effect, by_outcome, ci_level, treatment, control, n, id, ci_low, point | no common schema guard; per-detector run raised on malformed/missing shapes | unclear | ssot/<topic>/<topic>.json cached object; some source-cache helpers | 136 | UNKNOWN | 16 | 176 | 38 | executed detector directly with exceptions captured; validate() CLI aborts on missing modules |
| validate_v2 detector: source-category-binding | ssot/validate_v2.py:1502 | trials, app_id, inputs, nct, outcomeMeasures, source_outcome_title, source_category_title, outcomeMeasuresModule, by_outcome, provenance, id, groupId | no common schema guard; per-detector run raised on malformed/missing shapes | yes | ssot/<topic>/<topic>.json cached object; some source-cache helpers | 136 | UNKNOWN | 135 | 0 | 1 | executed detector directly with exceptions captured; validate() CLI aborts on missing modules |
| validate_v2 detector: subgroup-recompute | ssot/validate_v2.py:1698 | by_outcome, subgroups, id, results, trials, trial_ids, effect, inputs, treatment, control, k, estimator_used | no common schema guard; per-detector run raised on malformed/missing shapes | unclear | ssot/<topic>/<topic>.json cached object; some source-cache helpers | 136 | UNKNOWN | 135 | 0 | 1 | executed detector directly with exceptions captured; validate() CLI aborts on missing modules |
| validate_v2 detector: arm-completeness | ssot/validate_v2.py:2039 | trials, app_id, inputs, outcomeMeasures, outcomeMeasuresModule, by_outcome, provenance, nct, resultsSection, title, groups, label | no common schema guard; per-detector run raised on malformed/missing shapes | yes | ssot/<topic>/<topic>.json cached object; some source-cache helpers | 136 | UNKNOWN | 135 | 0 | 1 | executed detector directly with exceptions captured; validate() CLI aborts on missing modules |
| validate_v2 detector: identifier-anchoring | ssot/validate_v2.py:2091 | trials, app_id, inputs, nct, pmid, id, by_outcome, per_trial, results, trial_id, nctId, identificationModule | no common schema guard; per-detector run raised on malformed/missing shapes | yes | ssot/<topic>/<topic>.json cached object; some source-cache helpers | 136 | UNKNOWN | 135 | 0 | 1 | executed detector directly with exceptions captured; validate() CLI aborts on missing modules |
| validate_v2 detector: per-trial-source-fields | ssot/validate_v2.py:2150 | app_id, id, trials, by_outcome, per_trial, nct, crude_analysis_population, inputs, results, trial_id, treatment, control | no common schema guard; per-detector run raised on malformed/missing shapes | unclear | ssot/<topic>/<topic>.json cached object; some source-cache helpers | 136 | UNKNOWN | 110 | 2 | 25 | executed detector directly with exceptions captured; validate() CLI aborts on missing modules |
| validate_v2 detector: removal-grounds | ssot/validate_v2.py:2198 | removed_citations, trials, app_id, inputs, categories, protocolSection, nct, removed_ids, briefTitle, officialTitle, reason, conditions | no common schema guard; per-detector run raised on malformed/missing shapes | yes | ssot/<topic>/<topic>.json cached object; some source-cache helpers | 136 | UNKNOWN | 136 | 0 | 0 | executed detector directly with exceptions captured; validate() CLI aborts on missing modules |
| validate_v2 detector: quoted-group-disclosure | ssot/validate_v2.py:2273 | trials, inputs, by_outcome, source_quotes, provenance, label, arms, id, arms_not_used | no common schema guard; per-detector run raised on malformed/missing shapes | UNKNOWN | ssot/<topic>/<topic>.json cached object; some source-cache helpers | 136 | UNKNOWN | 134 | 3 | 1 | executed detector directly with exceptions captured; validate() CLI aborts on missing modules |
| validate_v2 detector: estimand-storage-form | ssot/validate_v2.py:2424 | trials, id, family, inputs, outcomes, effect, estimand, by_outcome, events | no common schema guard; per-detector run raised on malformed/missing shapes | unclear | ssot/<topic>/<topic>.json cached object; some source-cache helpers | 136 | UNKNOWN | 134 | 8 | 1 | executed detector directly with exceptions captured; validate() CLI aborts on missing modules |
| validate_v2 detector: estimand-homogeneity | ssot/validate_v2.py:2465 | id, trials, by_outcome, estimand_id, inputs, per_trial, results, measure, outcomes, estimand, trial_id | no common schema guard; per-detector run raised on malformed/missing shapes | unclear | ssot/<topic>/<topic>.json cached object; some source-cache helpers | 136 | UNKNOWN | 97 | 110 | 2 | executed detector directly with exceptions captured; validate() CLI aborts on missing modules |
| validate_v2 detector: shared-control-double-count | ssot/validate_v2.py:2518 | trials, by_outcome, inputs, control_arm_key, id, carried_contrasts, results, effect, arms, excluded_from_pool_because, trial_id, role | no common schema guard; per-detector run raised on malformed/missing shapes | unclear | ssot/<topic>/<topic>.json cached object; some source-cache helpers | 136 | UNKNOWN | 135 | 0 | 1 | executed detector directly with exceptions captured; validate() CLI aborts on missing modules |
| validate_v2 detector: regimen-homogeneity | ssot/validate_v2.py:2572 | by_outcome, regimen, subgroups, results, type, pooled, regimen_collapse_prespecified, outcomes, per_trial, id, regimen_collapse_reason | no common schema guard; per-detector run raised on malformed/missing shapes | UNKNOWN | ssot/<topic>/<topic>.json cached object; some source-cache helpers | 136 | UNKNOWN | 134 | 0 | 2 | executed detector directly with exceptions captured; validate() CLI aborts on missing modules |
| validate_v2 detector: log-effect-consistency | ssot/validate_v2.py:2599 | trials, inputs, effect, ci_level, point, by_outcome, scale, ci_low, ci_high, id, log_point, log_se | no common schema guard; per-detector run raised on malformed/missing shapes | unclear | ssot/<topic>/<topic>.json cached object; some source-cache helpers | 136 | UNKNOWN | 123 | 0 | 13 | executed detector directly with exceptions captured; validate() CLI aborts on missing modules |
| validate_v2 detector: ve-consistency | ssot/validate_v2.py:2635 | outcomes, id, trials, pooled, comparator_type, inputs, per_trial, pooled_ve_percent, by_outcome, subgroups, effect, published_ve_percent | no common schema guard; per-detector run raised on malformed/missing shapes | yes | ssot/<topic>/<topic>.json cached object; some source-cache helpers | 136 | UNKNOWN | 135 | 0 | 1 | executed detector directly with exceptions captured; validate() CLI aborts on missing modules |
| validate_v2 detector: analysed-scope | ssot/validate_v2.py:2703 | trials, id, measure, inputs, outcomes, effect, analysed, by_outcome, enrolled, analysed_scope | no common schema guard; per-detector run raised on malformed/missing shapes | unclear | ssot/<topic>/<topic>.json cached object; some source-cache helpers | 136 | UNKNOWN | 130 | 27 | 1 | executed detector directly with exceptions captured; validate() CLI aborts on missing modules |
| validate_v2 detector: pool-uniformity | ssot/validate_v2.py:2743 | pool_uniformity, by_outcome, pooled, estimand, results, state, note, outcomes, id, poolable_reason, heterogeneity_status, interpretation_caveat | no common schema guard; per-detector run raised on malformed/missing shapes | unclear | ssot/<topic>/<topic>.json cached object; some source-cache helpers | 136 | UNKNOWN | 99 | 76 | 4 | executed detector directly with exceptions captured; validate() CLI aborts on missing modules |
| validate_v2 detector: handbook-citation | ssot/validate_v2.py:2894 | methodological_authority, id, sections_relied_on, handbook, outcomes, section, by_outcome, sections, estimand, results, pooled, used_for | no common schema guard; per-detector run raised on malformed/missing shapes | unclear | ssot/<topic>/<topic>.json cached object; some source-cache helpers | 136 | UNKNOWN | 97 | 80 | 1 | executed detector directly with exceptions captured; validate() CLI aborts on missing modules |
| validate_v2 detector: network | ssot/validate_v2.py:2981 | network, edges, multi_arm_studies, id, outcome_id, closed_loops, treatments, is_reference, outcomes, treatment_node, comparator_node, connected | no common schema guard; per-detector run raised on malformed/missing shapes | yes | ssot/<topic>/<topic>.json cached object; some source-cache helpers | 136 | UNKNOWN | 136 | 0 | 0 | executed detector directly with exceptions captured; validate() CLI aborts on missing modules |
| validate_v2 detector: self-reference | ssot/validate_v2.py:3137 | UNKNOWN | no common schema guard; per-detector run raised on malformed/missing shapes | yes | ssot/<topic>/<topic>.json cached object; some source-cache helpers | 136 | UNKNOWN | 136 | 0 | 0 | executed detector directly with exceptions captured; validate() CLI aborts on missing modules |
| validate_v2 detector: over-assertion | ssot/validate_v2.py:3204 | UNKNOWN | no common schema guard; per-detector run raised on malformed/missing shapes | UNKNOWN | ssot/<topic>/<topic>.json cached object; some source-cache helpers | 136 | UNKNOWN | 0 | 0 | 136 | executed detector directly with exceptions captured; validate() CLI aborts on missing modules |
| validate_v2 detector: cascade-coverage | ssot/validate_v2.py:3232 | source_links_enforced, cascade, primary_source, checked, status, divergences, url, checked_on, reason, yielded, primary_not_best_because, agreement_note | no common schema guard; per-detector run raised on malformed/missing shapes | yes | ssot/<topic>/<topic>.json cached object; some source-cache helpers | 136 | UNKNOWN | 116 | 0 | 20 | executed detector directly with exceptions captured; validate() CLI aborts on missing modules |
| validate_v2 detector: source-links | ssot/validate_v2.py:3354 | trials, source_links_enforced, source_url, source_tier, SSOT_CHECK_LINKS, inputs, effect, treatment, control, records, by_outcome, single_tier_because | no common schema guard; per-detector run raised on malformed/missing shapes | yes | ssot/<topic>/<topic>.json cached object; some source-cache helpers | 136 | UNKNOWN | 116 | 0 | 20 | executed detector directly with exceptions captured; validate() CLI aborts on missing modules |
| validate_v2 detector: cross-engine-recompute | ssot/validate_v2.py:3465 | trials, ci_level, measure, i2, pooled, by_outcome, inputs, effect, results, treatment, control, outcomes | no common schema guard; per-detector run raised on malformed/missing shapes | yes when optional dependency/grade subject is absent or skipped; CLI currently raises here | ssot/<topic>/<topic>.json cached object; some source-cache helpers | 136 | UNKNOWN | 0 | 0 | 136 | executed detector directly with exceptions captured; validate() CLI aborts on missing modules |
| validate_v2 detector: grade-certainty | ssot/validate_v2.py:3597 | grade, derived_from, domains, pooled, imprecision, point, ci_low, ci_high, inconsistency, i2, computed_bands, starting_point | no common schema guard; per-detector run raised on malformed/missing shapes | yes when optional dependency/grade subject is absent or skipped; CLI currently raises here | ssot/<topic>/<topic>.json cached object; some source-cache helpers | 136 | UNKNOWN | 0 | 0 | 136 | executed detector directly with exceptions captured; validate() CLI aborts on missing modules |
| validate_v2 detector: arm-role-vs-registry | ssot/validate_v2.py:3739 | UNKNOWN | no common schema guard; per-detector run raised on malformed/missing shapes | UNKNOWN | ssot/<topic>/<topic>.json cached object; some source-cache helpers | 136 | UNKNOWN | 135 | 0 | 1 | executed detector directly with exceptions captured; validate() CLI aborts on missing modules |
| validate_v2 detector: reference-consistency | ssot/validate_v2.py:3751 | UNKNOWN | no common schema guard; per-detector run raised on malformed/missing shapes | UNKNOWN | ssot/<topic>/<topic>.json cached object; some source-cache helpers | 136 | UNKNOWN | 134 | 3 | 1 | executed detector directly with exceptions captured; validate() CLI aborts on missing modules |
