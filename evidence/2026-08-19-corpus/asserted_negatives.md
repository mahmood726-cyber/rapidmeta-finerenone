# Asserted Negatives Sweep - 2026-08-19 Corpus

Scope: `ssot/<topic>/<topic>.json` only; no network; SSOT JSON objects were not modified.

## Method

- A hit is a leaf value equal to `false`, `[]`, `{}`, `0`, `"none"`, `"no"`, `"clean"`, `"n/a"`, or `"not applicable"`.
- The leaf is reportable only when the leaf key or immediate parent key contains one of the requested check/comparison/reconciliation signals.
- A sibling counts as computed evidence when it names a method, date, source file/path, or count. Rows without such a sibling are ranked first.

## Static vs Dynamic Disclosure

| item | type | source |
| --- | --- | --- |
| negative leaf values | static | task instruction |
| check-name signal substrings | static | task instruction |
| sibling-evidence cue regexes | static heuristic | task instruction, applied conservatively to direct relevant siblings |
| canonical object list, hits, counts, and NCT sets | dynamic | parsed `ssot/<topic>/<topic>.json` files |

## Coverage

| item | count |
| --- | ---: |
| canonical object files found | 135 |
| parsed objects | 135 |
| NOT_ASSESSABLE parse/read failures | 0 |
| immediate ssot directories without `<dir>.json` | 2 |

## Known-Answer Check

| check | returned |
| --- | --- |
| `status` | `COMPUTED` |
| `path` | `registration_identity.duplicate_seeding_check` |
| `state` | `CHECKED` |
| `checked_against` | `evidence/2026-08-19-corpus/reconcile.json` |
| `n_trials_checked` | `4` |
| `shared_with_other_topics` | `True` |
| `negative_hits_under_block` | `0` |
| `asserted_hits_under_block` | `[]` |

## Bucket Counts

| bucket | count |
| --- | ---: |
| hits WITH a method/date/source/count sibling (probably computed) | 103 |
| hits WITHOUT such a sibling (probably asserted) | 422 |
| bare hits with no evidence sibling and no prose sibling | 52 |
| hits whose sibling is PROSE ONLY, naming no file/count/date/method evidence | 370 |
| fields with sibling prose mentioning off-object NCT IDs | 16 |

## Cross-Contamination Signature

| topic | dotted path | value | off-object NCT IDs | sibling prose source |
| --- | --- | --- | --- | --- |
| arni-hfref | `screening.dual_screening.disagreements[72].b_axis` | `"NONE"` | `NCT04688294` | record_id: NCT04688294 |
| arni-hfref | `screening.dual_screening.disagreements[73].b_axis` | `"NONE"` | `NCT04397302` | record_id: NCT04397302 |
| arni-hfref | `screening.dual_screening.disagreements[74].b_axis` | `"NONE"` | `NCT05164653` | record_id: NCT05164653 |
| arni-hfref | `screening.dual_screening.disagreements[75].b_axis` | `"NONE"` | `NCT02916160` | record_id: NCT02916160 |
| arni-hfref | `screening.dual_screening.disagreements[76].b_axis` | `"NONE"` | `NCT02887183` | record_id: NCT02887183 |
| arni-hfref | `screening.dual_screening.disagreements[77].b_axis` | `"NONE"` | `NCT05963282` | record_id: NCT05963282 |
| arni-hfref | `screening.dual_screening.disagreements[78].b_axis` | `"NONE"` | `NCT05613140` | record_id: NCT05613140 |
| arni-hfref | `screening.dual_screening.disagreements[80].b_axis` | `"NONE"` | `NCT05021419` | record_id: NCT05021419 |
| arni-hfref | `screening.dual_screening.disagreements[82].b_axis` | `"NONE"` | `NCT05989503` | record_id: NCT05989503 |
| arni-hfref | `screening.dual_screening.disagreements[83].b_axis` | `"NONE"` | `NCT07341893` | record_id: NCT07341893 |
| arni-hfref | `screening.dual_screening.disagreements[84].b_axis` | `"NONE"` | `NCT02816736` | record_id: NCT02816736 |
| arni-hfref | `screening.dual_screening.disagreements[85].b_axis` | `"NONE"` | `NCT04218435` | record_id: NCT04218435 |
| arni-hfref | `screening.dual_screening.disagreements[87].b_axis` | `"NONE"` | `NCT02924727` | record_id: NCT02924727 |
| arni-hfref | `screening.dual_screening.disagreements[88].b_axis` | `"NONE"` | `NCT05637853` | record_id: NCT05637853 |
| arni-hfref | `screening.dual_screening.disagreements[89].b_axis` | `"NONE"` | `NCT05168787` | record_id: NCT05168787 |
| arni-hfref | `screening.dual_screening.disagreements[90].b_axis` | `"NONE"` | `NCT06029712` | record_id: NCT06029712 |

## All Hits

| topic | dotted path | value | sibling recording how checked? |
| --- | --- | --- | --- |
| ablation-af-review | `screening_names_unresolved` | `[]` | NO: no method/date/source/count sibling |
| acs-antiplatelet-review | `screening_names_unresolved` | `[]` | NO: no method/date/source/count sibling |
| antimalarial-act | `inputs.trials[0].arms[0].failures` | `0` | NO: no method/date/source/count sibling |
| antimalarial-act | `results.by_outcome.dp_vs_al.per_trial[0].treatment_failures` | `0` | NO: no method/date/source/count sibling |
| apixaban-acs-review | `screening_names_unresolved` | `[]` | NO: no method/date/source/count sibling |
| apixaban-af-review | `screening_names_unresolved` | `[]` | NO: no method/date/source/count sibling |
| arni-hfref | `citations.41923142.traces_to_screening_record` | `false` | NO: no method/date/source/count sibling |
| arni-hfref | `reconciliation.trial_list_diffs[0].clean` | `false` | NO: no method/date/source/count sibling |
| arni-hfref | `reconciliation.trial_list_diffs[1].clean` | `false` | NO: no method/date/source/count sibling |
| arni-hfref | `rob2.trials[0].domains[4].agreed` | `false` | NO: no method/date/source/count sibling |
| arni-hfref | `rob2.trials[0].overall_agreed` | `false` | NO: no method/date/source/count sibling |
| arni-hfref | `rob2.trials[1].domains[0].agreed` | `false` | NO: no method/date/source/count sibling |
| arni-hfref | `rob2.trials[1].domains[4].agreed` | `false` | NO: no method/date/source/count sibling |
| arni-hfref | `rob2.trials[1].overall_agreed` | `false` | NO: no method/date/source/count sibling |
| arni-hfref | `rob2.trials[2].domains[0].agreed` | `false` | NO: no method/date/source/count sibling |
| arni-hfref | `rob2.trials[2].domains[4].agreed` | `false` | NO: no method/date/source/count sibling |
| attr-cm-review | `screening_names_unresolved` | `[]` | NO: no method/date/source/count sibling |
| attr-pn-review | `screening_names_unresolved` | `[]` | NO: no method/date/source/count sibling |
| bempedoic-acid-review | `screening_names_unresolved` | `[]` | NO: no method/date/source/count sibling |
| bococizumab-lipid-review | `screening_names_unresolved` | `[]` | NO: no method/date/source/count sibling |
| cangrelor-pci-review | `screening_names_unresolved` | `[]` | NO: no method/date/source/count sibling |
| colchicine-cvd-review | `screening_names_unresolved` | `[]` | NO: no method/date/source/count sibling |
| dabigatran-vte-review | `screening_names_unresolved` | `[]` | NO: no method/date/source/count sibling |
| doac-af-review | `screening_names_unresolved` | `[]` | NO: no method/date/source/count sibling |
| doac-cancer-vte-review | `screening_names_unresolved` | `[]` | NO: no method/date/source/count sibling |
| empagliflozin-hf-auto-full-review | `screening_names_unresolved` | `[]` | NO: no method/date/source/count sibling |
| evolocumab-dyslipidemia-review | `screening_names_unresolved` | `[]` | NO: no method/date/source/count sibling |
| evolocumab-mixed-dyslipidemia-auto-full-review | `screening_names_unresolved` | `[]` | NO: no method/date/source/count sibling |
| fcm-hf-review | `screening_names_unresolved` | `[]` | NO: no method/date/source/count sibling |
| finerenone-cv | `screening_names_unresolved` | `[]` | NO: no method/date/source/count sibling |
| finerenone-review | `screening_names_unresolved` | `[]` | NO: no method/date/source/count sibling |
| hepatitis-b-taf-tdf-review | `screening_names_unresolved` | `[]` | NO: no method/date/source/count sibling |
| icosapent-lipid-auto-full-review | `screening_names_unresolved` | `[]` | NO: no method/date/source/count sibling |
| inclisiran-lipid-kidney-auto-full-review | `screening_names_unresolved` | `[]` | NO: no method/date/source/count sibling |
| incretin-hfpef-review | `screening_names_unresolved` | `[]` | NO: no method/date/source/count sibling |
| intensive-bp-review | `screening_names_unresolved` | `[]` | NO: no method/date/source/count sibling |
| iv-iron-hf | `screening_names_unresolved` | `[]` | NO: no method/date/source/count sibling |
| mavacamten-hcm-review | `screening_names_unresolved` | `[]` | NO: no method/date/source/count sibling |
| mavacamten-ohcm-review | `screening_names_unresolved` | `[]` | NO: no method/date/source/count sibling |
| mitral-funcmr-review | `screening_names_unresolved` | `[]` | NO: no method/date/source/count sibling |
| netarsudil-ocular-hypertension-auto-full-review | `screening_names_unresolved` | `[]` | NO: no method/date/source/count sibling |
| pcsk9-inhibitors-cv-review | `screening_names_unresolved` | `[]` | NO: no method/date/source/count sibling |
| pcsk9-review | `screening_names_unresolved` | `[]` | NO: no method/date/source/count sibling |
| pitavastatin-auto-full-review | `screening_names_unresolved` | `[]` | NO: no method/date/source/count sibling |
| rivaroxaban-acs-review | `screening_names_unresolved` | `[]` | NO: no method/date/source/count sibling |
| rivaroxaban-vasc-review | `screening_names_unresolved` | `[]` | NO: no method/date/source/count sibling |
| rosuvastatin-auto-full-review | `screening_names_unresolved` | `[]` | NO: no method/date/source/count sibling |
| rotavirus-vaccine-africa-review | `screening_names_unresolved` | `[]` | NO: no method/date/source/count sibling |
| sglt2-ckd-review | `screening_names_unresolved` | `[]` | NO: no method/date/source/count sibling |
| sglt2-hf | `screening_names_unresolved` | `[]` | NO: no method/date/source/count sibling |
| sglt2-mace-cvot-review | `screening_names_unresolved` | `[]` | NO: no method/date/source/count sibling |
| sotagliflozin-hf | `screening_names_unresolved` | `[]` | NO: no method/date/source/count sibling |
| ablation-af-review | `scope_decisions.SCOPE:drug-wide-pivotal-not-heart-failure.sections` | `[]` | PROSE ONLY: decision=not recorded on the page this object was extracted from; conformance=not recorded on the page this object was extracted from |
| ablation-af-review | `screening.excluded` | `[]` | PROSE ONLY: search_note=not recorded on the page this object was extracted from; eligibility=not recorded on the page this object was extracted from |
| ablation-af-review | `screening.records` | `[]` | PROSE ONLY: search_note=not recorded on the page this object was extracted from; eligibility=not recorded on the page this object was extracted from |
| acs-antiplatelet-review | `scope_decisions.SCOPE:drug-wide-pivotal-not-heart-failure.sections` | `[]` | PROSE ONLY: decision=not recorded on the page this object was extracted from; conformance=not recorded on the page this object was extracted from |
| acs-antiplatelet-review | `screening.excluded` | `[]` | PROSE ONLY: search_note=not recorded on the page this object was extracted from; eligibility=not recorded on the page this object was extracted from |
| acs-antiplatelet-review | `screening.records` | `[]` | PROSE ONLY: search_note=not recorded on the page this object was extracted from; eligibility=not recorded on the page this object was extracted from |
| apixaban-acs-review | `reconciliation.corrections` | `[]` | PROSE ONLY: why_this_step_exists=not recorded on the page this object was built from; clean_because=not recorded on the page this object was built from |
| apixaban-acs-review | `reconciliation.matches` | `[]` | PROSE ONLY: why_this_step_exists=not recorded on the page this object was built from; clean_because=not recorded on the page this object was built from |
| apixaban-acs-review | `reconciliation.trial_list_diffs` | `[]` | PROSE ONLY: why_this_step_exists=not recorded on the page this object was built from; clean_because=not recorded on the page this object was built from |
| apixaban-acs-review | `reconciliation.unresolved` | `[]` | PROSE ONLY: why_this_step_exists=not recorded on the page this object was built from; clean_because=not recorded on the page this object was built from |
| apixaban-af-review | `reconciliation.corrections` | `[]` | PROSE ONLY: why_this_step_exists=not recorded on the page this object was built from; clean_because=not recorded on the page this object was built from |
| apixaban-af-review | `reconciliation.matches` | `[]` | PROSE ONLY: why_this_step_exists=not recorded on the page this object was built from; clean_because=not recorded on the page this object was built from |
| apixaban-af-review | `reconciliation.trial_list_diffs` | `[]` | PROSE ONLY: why_this_step_exists=not recorded on the page this object was built from; clean_because=not recorded on the page this object was built from |
| apixaban-af-review | `reconciliation.unresolved` | `[]` | PROSE ONLY: why_this_step_exists=not recorded on the page this object was built from; clean_because=not recorded on the page this object was built from |
| arni-hfref | `screening.corpus[106].screener_b.axis_failed` | `"NONE"` | PROSE ONLY: decision=undetermined; reported_instead=NONE |
| arni-hfref | `screening.corpus[106].screener_b.reported_instead` | `"NONE"` | PROSE ONLY: decision=undetermined; axis_failed=NONE |
| arni-hfref | `screening.corpus[107].screener_b.axis_failed` | `"NONE"` | PROSE ONLY: decision=undetermined; reported_instead=NONE |
| arni-hfref | `screening.corpus[107].screener_b.reported_instead` | `"NONE"` | PROSE ONLY: decision=undetermined; axis_failed=NONE |
| arni-hfref | `screening.corpus[108].screener_b.axis_failed` | `"NONE"` | PROSE ONLY: decision=undetermined; reported_instead=NONE |
| arni-hfref | `screening.corpus[108].screener_b.reported_instead` | `"NONE"` | PROSE ONLY: decision=undetermined; axis_failed=NONE |
| arni-hfref | `screening.corpus[10].screener_b.axis_failed` | `"NONE"` | PROSE ONLY: decision=undetermined; reported_instead=unclear |
| arni-hfref | `screening.corpus[112].screener_b.axis_failed` | `"NONE"` | PROSE ONLY: decision=undetermined; reported_instead=NONE |
| arni-hfref | `screening.corpus[112].screener_b.reported_instead` | `"NONE"` | PROSE ONLY: decision=undetermined; axis_failed=NONE |
| arni-hfref | `screening.corpus[119].screener_b.axis_failed` | `"NONE"` | PROSE ONLY: decision=undetermined; reported_instead=NONE |
| arni-hfref | `screening.corpus[119].screener_b.reported_instead` | `"NONE"` | PROSE ONLY: decision=undetermined; axis_failed=NONE |
| arni-hfref | `screening.corpus[11].screener_b.axis_failed` | `"NONE"` | PROSE ONLY: decision=undetermined; reported_instead=unclear |
| arni-hfref | `screening.corpus[123].screener_b.axis_failed` | `"NONE"` | PROSE ONLY: decision=undetermined; reported_instead=NONE |
| arni-hfref | `screening.corpus[123].screener_b.reported_instead` | `"NONE"` | PROSE ONLY: decision=undetermined; axis_failed=NONE |
| arni-hfref | `screening.corpus[125].screener_b.axis_failed` | `"NONE"` | PROSE ONLY: decision=undetermined; reported_instead=NONE |
| arni-hfref | `screening.corpus[125].screener_b.reported_instead` | `"NONE"` | PROSE ONLY: decision=undetermined; axis_failed=NONE |
| arni-hfref | `screening.corpus[126].screener_b.axis_failed` | `"NONE"` | PROSE ONLY: decision=undetermined; reported_instead=NONE |
| arni-hfref | `screening.corpus[126].screener_b.reported_instead` | `"NONE"` | PROSE ONLY: decision=undetermined; axis_failed=NONE |
| arni-hfref | `screening.corpus[128].screener_b.axis_failed` | `"NONE"` | PROSE ONLY: decision=undetermined; reported_instead=NONE |
| arni-hfref | `screening.corpus[128].screener_b.reported_instead` | `"NONE"` | PROSE ONLY: decision=undetermined; axis_failed=NONE |
| arni-hfref | `screening.corpus[129].screener_b.axis_failed` | `"NONE"` | PROSE ONLY: decision=undetermined; reported_instead=NONE |
| arni-hfref | `screening.corpus[129].screener_b.reported_instead` | `"NONE"` | PROSE ONLY: decision=undetermined; axis_failed=NONE |
| arni-hfref | `screening.corpus[130].screener_b.axis_failed` | `"NONE"` | PROSE ONLY: decision=undetermined; reported_instead=NONE |
| arni-hfref | `screening.corpus[130].screener_b.reported_instead` | `"NONE"` | PROSE ONLY: decision=undetermined; axis_failed=NONE |
| arni-hfref | `screening.corpus[131].screener_b.axis_failed` | `"NONE"` | PROSE ONLY: decision=undetermined; reported_instead=NONE |
| arni-hfref | `screening.corpus[131].screener_b.reported_instead` | `"NONE"` | PROSE ONLY: decision=undetermined; axis_failed=NONE |
| arni-hfref | `screening.corpus[132].screener_b.axis_failed` | `"NONE"` | PROSE ONLY: decision=undetermined; reported_instead=NONE |
| arni-hfref | `screening.corpus[132].screener_b.reported_instead` | `"NONE"` | PROSE ONLY: decision=undetermined; axis_failed=NONE |
| arni-hfref | `screening.corpus[135].screener_b.axis_failed` | `"NONE"` | PROSE ONLY: decision=undetermined; reported_instead=NONE |
| arni-hfref | `screening.corpus[135].screener_b.reported_instead` | `"NONE"` | PROSE ONLY: decision=undetermined; axis_failed=NONE |
| arni-hfref | `screening.corpus[138].screener_b.axis_failed` | `"NONE"` | PROSE ONLY: decision=undetermined; reported_instead=NONE |
| arni-hfref | `screening.corpus[138].screener_b.reported_instead` | `"NONE"` | PROSE ONLY: decision=undetermined; axis_failed=NONE |
| arni-hfref | `screening.corpus[140].screener_b.axis_failed` | `"NONE"` | PROSE ONLY: decision=undetermined; reported_instead=NONE |
| arni-hfref | `screening.corpus[140].screener_b.reported_instead` | `"NONE"` | PROSE ONLY: decision=undetermined; axis_failed=NONE |
| arni-hfref | `screening.corpus[141].screener_b.axis_failed` | `"NONE"` | PROSE ONLY: decision=undetermined; reported_instead=NONE |
| arni-hfref | `screening.corpus[141].screener_b.reported_instead` | `"NONE"` | PROSE ONLY: decision=undetermined; axis_failed=NONE |
| arni-hfref | `screening.corpus[142].screener_b.axis_failed` | `"NONE"` | PROSE ONLY: decision=undetermined; reported_instead=NONE |
| arni-hfref | `screening.corpus[142].screener_b.reported_instead` | `"NONE"` | PROSE ONLY: decision=undetermined; axis_failed=NONE |
| arni-hfref | `screening.corpus[144].screener_b.axis_failed` | `"NONE"` | PROSE ONLY: decision=undetermined; reported_instead=NONE |
| arni-hfref | `screening.corpus[144].screener_b.reported_instead` | `"NONE"` | PROSE ONLY: decision=undetermined; axis_failed=NONE |
| arni-hfref | `screening.corpus[145].screener_b.axis_failed` | `"NONE"` | PROSE ONLY: decision=undetermined; reported_instead=NONE |
| arni-hfref | `screening.corpus[145].screener_b.reported_instead` | `"NONE"` | PROSE ONLY: decision=undetermined; axis_failed=NONE |
| arni-hfref | `screening.corpus[146].screener_b.axis_failed` | `"NONE"` | PROSE ONLY: decision=undetermined; reported_instead=NONE |
| arni-hfref | `screening.corpus[146].screener_b.reported_instead` | `"NONE"` | PROSE ONLY: decision=undetermined; axis_failed=NONE |
| arni-hfref | `screening.corpus[147].screener_b.axis_failed` | `"NONE"` | PROSE ONLY: decision=undetermined; reported_instead=NONE |
| arni-hfref | `screening.corpus[147].screener_b.reported_instead` | `"NONE"` | PROSE ONLY: decision=undetermined; axis_failed=NONE |
| arni-hfref | `screening.corpus[148].screener_b.axis_failed` | `"NONE"` | PROSE ONLY: decision=undetermined; reported_instead=NONE |
| arni-hfref | `screening.corpus[148].screener_b.reported_instead` | `"NONE"` | PROSE ONLY: decision=undetermined; axis_failed=NONE |
| arni-hfref | `screening.corpus[151].screener_b.axis_failed` | `"NONE"` | PROSE ONLY: decision=undetermined; reported_instead=NONE |
| arni-hfref | `screening.corpus[151].screener_b.reported_instead` | `"NONE"` | PROSE ONLY: decision=undetermined; axis_failed=NONE |
| arni-hfref | `screening.corpus[154].screener_b.axis_failed` | `"NONE"` | PROSE ONLY: decision=undetermined; reported_instead=NONE |
| arni-hfref | `screening.corpus[154].screener_b.reported_instead` | `"NONE"` | PROSE ONLY: decision=undetermined; axis_failed=NONE |
| arni-hfref | `screening.corpus[155].screener_b.axis_failed` | `"NONE"` | PROSE ONLY: decision=undetermined; reported_instead=NONE |
| arni-hfref | `screening.corpus[155].screener_b.reported_instead` | `"NONE"` | PROSE ONLY: decision=undetermined; axis_failed=NONE |
| arni-hfref | `screening.corpus[156].screener_b.axis_failed` | `"NONE"` | PROSE ONLY: decision=undetermined; reported_instead=NONE |
| arni-hfref | `screening.corpus[156].screener_b.reported_instead` | `"NONE"` | PROSE ONLY: decision=undetermined; axis_failed=NONE |
| arni-hfref | `screening.corpus[157].screener_b.axis_failed` | `"NONE"` | PROSE ONLY: decision=undetermined; reported_instead=NONE |
| arni-hfref | `screening.corpus[157].screener_b.reported_instead` | `"NONE"` | PROSE ONLY: decision=undetermined; axis_failed=NONE |
| arni-hfref | `screening.corpus[159].screener_b.axis_failed` | `"NONE"` | PROSE ONLY: decision=undetermined; reported_instead=NONE |
| arni-hfref | `screening.corpus[159].screener_b.reported_instead` | `"NONE"` | PROSE ONLY: decision=undetermined; axis_failed=NONE |
| arni-hfref | `screening.corpus[162].screener_b.axis_failed` | `"NONE"` | PROSE ONLY: decision=undetermined; reported_instead=NONE |
| arni-hfref | `screening.corpus[162].screener_b.reported_instead` | `"NONE"` | PROSE ONLY: decision=undetermined; axis_failed=NONE |
| arni-hfref | `screening.corpus[163].screener_b.axis_failed` | `"NONE"` | PROSE ONLY: decision=undetermined; reported_instead=NONE |
| arni-hfref | `screening.corpus[163].screener_b.reported_instead` | `"NONE"` | PROSE ONLY: decision=undetermined; axis_failed=NONE |
| arni-hfref | `screening.corpus[165].screener_b.axis_failed` | `"NONE"` | PROSE ONLY: decision=undetermined; reported_instead=NONE |
| arni-hfref | `screening.corpus[165].screener_b.reported_instead` | `"NONE"` | PROSE ONLY: decision=undetermined; axis_failed=NONE |
| arni-hfref | `screening.corpus[166].screener_b.axis_failed` | `"NONE"` | PROSE ONLY: decision=undetermined; reported_instead=NONE |
| arni-hfref | `screening.corpus[166].screener_b.reported_instead` | `"NONE"` | PROSE ONLY: decision=undetermined; axis_failed=NONE |
| arni-hfref | `screening.corpus[167].screener_b.axis_failed` | `"NONE"` | PROSE ONLY: decision=undetermined; reported_instead=NONE |
| arni-hfref | `screening.corpus[167].screener_b.reported_instead` | `"NONE"` | PROSE ONLY: decision=undetermined; axis_failed=NONE |
| arni-hfref | `screening.corpus[168].screener_b.axis_failed` | `"NONE"` | PROSE ONLY: decision=undetermined; reported_instead=NONE |
| arni-hfref | `screening.corpus[168].screener_b.reported_instead` | `"NONE"` | PROSE ONLY: decision=undetermined; axis_failed=NONE |
| arni-hfref | `screening.corpus[169].screener_b.axis_failed` | `"NONE"` | PROSE ONLY: decision=undetermined; reported_instead=NONE |
| arni-hfref | `screening.corpus[169].screener_b.reported_instead` | `"NONE"` | PROSE ONLY: decision=undetermined; axis_failed=NONE |
| arni-hfref | `screening.corpus[170].screener_b.axis_failed` | `"NONE"` | PROSE ONLY: decision=undetermined; reported_instead=NONE |
| arni-hfref | `screening.corpus[170].screener_b.reported_instead` | `"NONE"` | PROSE ONLY: decision=undetermined; axis_failed=NONE |
| arni-hfref | `screening.corpus[172].screener_b.axis_failed` | `"NONE"` | PROSE ONLY: decision=undetermined; reported_instead=NONE |
| arni-hfref | `screening.corpus[172].screener_b.reported_instead` | `"NONE"` | PROSE ONLY: decision=undetermined; axis_failed=NONE |
| arni-hfref | `screening.corpus[176].screener_b.axis_failed` | `"NONE"` | PROSE ONLY: decision=undetermined; reported_instead=NONE |
| arni-hfref | `screening.corpus[176].screener_b.reported_instead` | `"NONE"` | PROSE ONLY: decision=undetermined; axis_failed=NONE |
| arni-hfref | `screening.corpus[183].screener_b.axis_failed` | `"NONE"` | PROSE ONLY: decision=undetermined; reported_instead=unclear from title |
| arni-hfref | `screening.corpus[190].screener_b.axis_failed` | `"NONE"` | PROSE ONLY: decision=undetermined; reported_instead=unclear from title |
| arni-hfref | `screening.corpus[205].screener_b.axis_failed` | `"NONE"` | PROSE ONLY: decision=undetermined; reported_instead=unclear from title |
| arni-hfref | `screening.corpus[210].screener_b.axis_failed` | `"NONE"` | PROSE ONLY: decision=undetermined; reported_instead=unclear from title |
| arni-hfref | `screening.corpus[214].screener_b.axis_failed` | `"NONE"` | PROSE ONLY: decision=undetermined; reported_instead=unclear from title |
| arni-hfref | `screening.corpus[222].screener_b.axis_failed` | `"NONE"` | PROSE ONLY: decision=undetermined; reported_instead=unclear from title |
| arni-hfref | `screening.corpus[25].screener_b.axis_failed` | `"NONE"` | PROSE ONLY: decision=undetermined; reported_instead=unclear |
| arni-hfref | `screening.corpus[26].screener_b.axis_failed` | `"NONE"` | PROSE ONLY: decision=undetermined; reported_instead=unclear |
| arni-hfref | `screening.corpus[274].screener_b.axis_failed` | `"NONE"` | PROSE ONLY: decision=undetermined; reported_instead=NONE |
| arni-hfref | `screening.corpus[274].screener_b.reported_instead` | `"NONE"` | PROSE ONLY: decision=undetermined; axis_failed=NONE |
| arni-hfref | `screening.corpus[283].screener_b.axis_failed` | `"NONE"` | PROSE ONLY: decision=undetermined; reported_instead=NONE |
| arni-hfref | `screening.corpus[283].screener_b.reported_instead` | `"NONE"` | PROSE ONLY: decision=undetermined; axis_failed=NONE |
| arni-hfref | `screening.corpus[290].screener_b.axis_failed` | `"NONE"` | PROSE ONLY: decision=undetermined; reported_instead=NONE |
| arni-hfref | `screening.corpus[290].screener_b.reported_instead` | `"NONE"` | PROSE ONLY: decision=undetermined; axis_failed=NONE |
| arni-hfref | `screening.corpus[293].screener_b.axis_failed` | `"NONE"` | PROSE ONLY: decision=undetermined; reported_instead=NONE |
| arni-hfref | `screening.corpus[293].screener_b.reported_instead` | `"NONE"` | PROSE ONLY: decision=undetermined; axis_failed=NONE |
| arni-hfref | `screening.corpus[302].screener_b.axis_failed` | `"NONE"` | PROSE ONLY: decision=undetermined; reported_instead=NONE |
| arni-hfref | `screening.corpus[302].screener_b.reported_instead` | `"NONE"` | PROSE ONLY: decision=undetermined; axis_failed=NONE |
| arni-hfref | `screening.corpus[308].screener_b.axis_failed` | `"NONE"` | PROSE ONLY: decision=undetermined; reported_instead=NONE |
| arni-hfref | `screening.corpus[308].screener_b.reported_instead` | `"NONE"` | PROSE ONLY: decision=undetermined; axis_failed=NONE |
| arni-hfref | `screening.corpus[311].screener_b.axis_failed` | `"NONE"` | PROSE ONLY: decision=undetermined; reported_instead=NONE |
| arni-hfref | `screening.corpus[311].screener_b.reported_instead` | `"NONE"` | PROSE ONLY: decision=undetermined; axis_failed=NONE |
| arni-hfref | `screening.corpus[327].screener_b.axis_failed` | `"NONE"` | PROSE ONLY: decision=include; reported_instead=NONE |
| arni-hfref | `screening.corpus[327].screener_b.reported_instead` | `"NONE"` | PROSE ONLY: decision=include; axis_failed=NONE |
| arni-hfref | `screening.corpus[32].screener_b.axis_failed` | `"NONE"` | PROSE ONLY: decision=undetermined; reported_instead=unclear |
| arni-hfref | `screening.corpus[332].screener_b.axis_failed` | `"NONE"` | PROSE ONLY: decision=undetermined; reported_instead=NONE |
| arni-hfref | `screening.corpus[332].screener_b.reported_instead` | `"NONE"` | PROSE ONLY: decision=undetermined; axis_failed=NONE |
| arni-hfref | `screening.corpus[338].screener_b.axis_failed` | `"NONE"` | PROSE ONLY: decision=undetermined; reported_instead=NONE |
| arni-hfref | `screening.corpus[338].screener_b.reported_instead` | `"NONE"` | PROSE ONLY: decision=undetermined; axis_failed=NONE |
| arni-hfref | `screening.corpus[344].screener_b.axis_failed` | `"NONE"` | PROSE ONLY: decision=undetermined; reported_instead=NONE |
| arni-hfref | `screening.corpus[344].screener_b.reported_instead` | `"NONE"` | PROSE ONLY: decision=undetermined; axis_failed=NONE |
| arni-hfref | `screening.corpus[346].screener_b.axis_failed` | `"NONE"` | PROSE ONLY: decision=undetermined; reported_instead=NONE |
| arni-hfref | `screening.corpus[346].screener_b.reported_instead` | `"NONE"` | PROSE ONLY: decision=undetermined; axis_failed=NONE |
| arni-hfref | `screening.corpus[362].screener_b.axis_failed` | `"NONE"` | PROSE ONLY: decision=undetermined; reported_instead= |
| arni-hfref | `screening.corpus[363].screener_b.axis_failed` | `"NONE"` | PROSE ONLY: decision=undetermined; reported_instead= |
| arni-hfref | `screening.corpus[36].screener_b.axis_failed` | `"NONE"` | PROSE ONLY: decision=undetermined; reported_instead=unclear |
| arni-hfref | `screening.corpus[375].screener_b.axis_failed` | `"NONE"` | PROSE ONLY: decision=undetermined; reported_instead= |
| arni-hfref | `screening.corpus[379].screener_b.axis_failed` | `"NONE"` | PROSE ONLY: decision=undetermined; reported_instead= |
| arni-hfref | `screening.corpus[383].screener_b.axis_failed` | `"NONE"` | PROSE ONLY: decision=undetermined; reported_instead= |
| arni-hfref | `screening.corpus[385].screener_b.axis_failed` | `"NONE"` | PROSE ONLY: decision=undetermined; reported_instead= |
| arni-hfref | `screening.corpus[386].screener_b.axis_failed` | `"NONE"` | PROSE ONLY: decision=undetermined; reported_instead= |
| arni-hfref | `screening.corpus[392].screener_b.axis_failed` | `"NONE"` | PROSE ONLY: decision=undetermined; reported_instead= |
| arni-hfref | `screening.corpus[397].screener_b.axis_failed` | `"NONE"` | PROSE ONLY: decision=undetermined; reported_instead= |
| arni-hfref | `screening.corpus[399].screener_b.axis_failed` | `"NONE"` | PROSE ONLY: decision=undetermined; reported_instead= |
| arni-hfref | `screening.corpus[400].screener_b.axis_failed` | `"NONE"` | PROSE ONLY: decision=undetermined; reported_instead= |
| arni-hfref | `screening.corpus[401].screener_b.axis_failed` | `"NONE"` | PROSE ONLY: decision=undetermined; reported_instead= |
| arni-hfref | `screening.corpus[409].screener_b.axis_failed` | `"NONE"` | PROSE ONLY: decision=undetermined; reported_instead= |
| arni-hfref | `screening.corpus[40].screener_b.axis_failed` | `"NONE"` | PROSE ONLY: decision=undetermined; reported_instead=unclear |
| arni-hfref | `screening.corpus[419].screener_b.axis_failed` | `"NONE"` | PROSE ONLY: decision=undetermined; reported_instead= |
| arni-hfref | `screening.corpus[421].screener_b.axis_failed` | `"NONE"` | PROSE ONLY: decision=undetermined; reported_instead= |
| arni-hfref | `screening.corpus[43].screener_b.axis_failed` | `"NONE"` | PROSE ONLY: decision=undetermined; reported_instead=unclear |
| arni-hfref | `screening.corpus[45].screener_b.axis_failed` | `"NONE"` | PROSE ONLY: decision=undetermined; reported_instead=unclear |
| arni-hfref | `screening.corpus[50].screener_b.axis_failed` | `"NONE"` | PROSE ONLY: decision=undetermined; reported_instead=unclear |
| arni-hfref | `screening.corpus[53].screener_b.axis_failed` | `"NONE"` | PROSE ONLY: decision=undetermined; reported_instead=unclear |
| arni-hfref | `screening.corpus[55].screener_b.axis_failed` | `"NONE"` | PROSE ONLY: decision=undetermined; reported_instead=unclear |
| arni-hfref | `screening.corpus[56].screener_b.axis_failed` | `"NONE"` | PROSE ONLY: decision=undetermined; reported_instead=unclear |
| arni-hfref | `screening.corpus[5].screener_b.axis_failed` | `"NONE"` | PROSE ONLY: decision=undetermined; reported_instead=unclear |
| arni-hfref | `screening.corpus[60].screener_b.axis_failed` | `"NONE"` | PROSE ONLY: decision=undetermined; reported_instead=unclear |
| arni-hfref | `screening.corpus[71].screener_b.axis_failed` | `"NONE"` | PROSE ONLY: decision=undetermined; reported_instead=unclear |
| arni-hfref | `screening.corpus[87].screener_b.axis_failed` | `"NONE"` | PROSE ONLY: decision=undetermined; reported_instead=unclear |
| arni-hfref | `screening.corpus[90].screener_b.axis_failed` | `"NONE"` | PROSE ONLY: decision=undetermined; reported_instead=NONE |
| arni-hfref | `screening.corpus[90].screener_b.reported_instead` | `"NONE"` | PROSE ONLY: decision=undetermined; axis_failed=NONE |
| arni-hfref | `screening.corpus[92].screener_b.axis_failed` | `"NONE"` | PROSE ONLY: decision=undetermined; reported_instead=NONE |
| arni-hfref | `screening.corpus[92].screener_b.reported_instead` | `"NONE"` | PROSE ONLY: decision=undetermined; axis_failed=NONE |
| arni-hfref | `screening.corpus[94].screener_b.axis_failed` | `"NONE"` | PROSE ONLY: decision=undetermined; reported_instead=NONE |
| arni-hfref | `screening.corpus[94].screener_b.reported_instead` | `"NONE"` | PROSE ONLY: decision=undetermined; axis_failed=NONE |
| arni-hfref | `screening.corpus[95].screener_b.axis_failed` | `"NONE"` | PROSE ONLY: decision=undetermined; reported_instead=NONE |
| arni-hfref | `screening.corpus[95].screener_b.reported_instead` | `"NONE"` | PROSE ONLY: decision=undetermined; axis_failed=NONE |
| arni-hfref | `screening.corpus[96].screener_b.axis_failed` | `"NONE"` | PROSE ONLY: decision=undetermined; reported_instead=NONE |
| arni-hfref | `screening.corpus[96].screener_b.reported_instead` | `"NONE"` | PROSE ONLY: decision=undetermined; axis_failed=NONE |
| arni-hfref | `screening.dual_screening.disagreements[0].b_axis` | `"NONE"` | PROSE ONLY: record_id=41910669; title=You evaluation of the PARACHUTE-HF trial: role of sacubitril/valsartan |
| arni-hfref | `screening.dual_screening.disagreements[10].b_axis` | `"NONE"` | PROSE ONLY: record_id=38842957; title=Sacubitril/Valsartan in Patients With Heart Failure and Deterioration |
| arni-hfref | `screening.dual_screening.disagreements[11].b_axis` | `"NONE"` | PROSE ONLY: record_id=38635062; title=Efficacy of early administration of sacubitril/valsartan after coronar |
| arni-hfref | `screening.dual_screening.disagreements[12].b_axis` | `"NONE"` | PROSE ONLY: record_id=38588927; title=Effects of Sacubitril/Valsartan Across the Spectrum of Renal Impairmen |
| arni-hfref | `screening.dual_screening.disagreements[13].b_axis` | `"NONE"` | PROSE ONLY: record_id=37989299; title=Efficacy and Safety of Sacubitril/Valsartan in Japanese Patients Accor |
| arni-hfref | `screening.dual_screening.disagreements[14].b_axis` | `"NONE"` | PROSE ONLY: record_id=36943907; title=Urinary cGMP/BNP Ratio, Sacubitril/Valsartan, and Outcomes in HFrEF: A |
| arni-hfref | `screening.dual_screening.disagreements[15].b_axis` | `"NONE"` | PROSE ONLY: record_id=36062622; title=Sacubitril/Valsartan in Patients With Heart Failure and Concomitant En |
| arni-hfref | `screening.dual_screening.disagreements[16].b_axis` | `"NONE"` | PROSE ONLY: record_id=35874853; title=The comparative effects of sacubitril/valsartan versus enalapril on pu |
| arni-hfref | `screening.dual_screening.disagreements[17].b_axis` | `"NONE"` | PROSE ONLY: record_id=35772853; title=Tolerability of Sacubitril/Valsartan in Patients With Advanced Heart F |
| arni-hfref | `screening.dual_screening.disagreements[18].b_axis` | `"NONE"` | PROSE ONLY: record_id=35717169; title=Effects of sacubitril/valsartan on glycemia in patients with diabetes |
| arni-hfref | `screening.dual_screening.disagreements[19].b_axis` | `"NONE"` | PROSE ONLY: record_id=35654526; title=Clinical Outcomes Related to Background Diuretic Use and New Diuretic |
| arni-hfref | `screening.dual_screening.disagreements[1].b_axis` | `"NONE"` | PROSE ONLY: record_id=41396086; title=Sacubitril-Valsartan vs Enalapril in Heart Failure Due to Chagas Disea |
| arni-hfref | `screening.dual_screening.disagreements[20].b_axis` | `"NONE"` | PROSE ONLY: record_id=35560696; title=Changes in cardiac biomarkers in association with alterations in cardi |
| arni-hfref | `screening.dual_screening.disagreements[21].b_axis` | `"NONE"` | PROSE ONLY: record_id=35027945; title=Long-Term Mortality and Morbidity Related to CHFrEF in Palestinian Pat |
| arni-hfref | `screening.dual_screening.disagreements[22].b_axis` | `"NONE"` | PROSE ONLY: record_id=34988519; title=Heart failure treatment in patients with cardiac implantable electroni |
| arni-hfref | `screening.dual_screening.disagreements[23].b_axis` | `"NONE"` | PROSE ONLY: record_id=34969175; title=Effect of sacubitril/valsartan on investigator-reported ventricular ar |
| arni-hfref | `screening.dual_screening.disagreements[24].b_axis` | `"NONE"` | PROSE ONLY: record_id=34758252; title=Angiotensin Receptor-Neprilysin Inhibition in Acute Myocardial Infarct |
| arni-hfref | `screening.dual_screening.disagreements[25].b_axis` | `"NONE"` | PROSE ONLY: record_id=34591356; title=A randomized clinical trial on the short-term effects of 12-week sacub |
| arni-hfref | `screening.dual_screening.disagreements[26].b_axis` | `"NONE"` | PROSE ONLY: record_id=34428592; title=Sleep Outcomes From AWAKE-HF: A Randomized Clinical Trial of Sacubitri |
| arni-hfref | `screening.dual_screening.disagreements[27].b_axis` | `"NONE"` | PROSE ONLY: record_id=34350772; title=Clinical Effectiveness of Sacubitril/Valsartan Among Patients Hospital |
| arni-hfref | `screening.dual_screening.disagreements[28].b_axis` | `"NONE"` | PROSE ONLY: record_id=34101308; title=Effect of sacubitril/valsartan vs enalapril on changes in heart failur |
| arni-hfref | `screening.dual_screening.disagreements[29].b_axis` | `"NONE"` | PROSE ONLY: record_id=34101002; title=Development and external validation of prognostic models to predict su |
| arni-hfref | `screening.dual_screening.disagreements[2].b_axis` | `"NONE"` | PROSE ONLY: record_id=41335448; title=Sacubitril/Valsartan vs Enalapril in Heart Failure Due to Chagas Disea |
| arni-hfref | `screening.dual_screening.disagreements[30].b_axis` | `"NONE"` | PROSE ONLY: record_id=33997628; title=Renal Outcomes in Patients with Systolic Heart Failure Treated With Sa |
| arni-hfref | `screening.dual_screening.disagreements[31].b_axis` | `"NONE"` | PROSE ONLY: record_id=33992607; title=Sacubitril/valsartan versus enalapril on exercise capacity in patients |
| arni-hfref | `screening.dual_screening.disagreements[32].b_axis` | `"NONE"` | PROSE ONLY: record_id=33984319; title=Days alive out of hospital in heart failure: Insights from the PARADIG |
| arni-hfref | `screening.dual_screening.disagreements[33].b_axis` | `"NONE"` | PROSE ONLY: record_id=33879733; title=A study of the sequential treatment of acute heart failure with sacubi |
| arni-hfref | `screening.dual_screening.disagreements[34].b_axis` | `"NONE"` | PROSE ONLY: record_id=33822031; title=Renal protection in chronic heart failure: focus on sacubitril/valsart |
| arni-hfref | `screening.dual_screening.disagreements[35].b_axis` | `"NONE"` | PROSE ONLY: record_id=33731544; title=Efficacy and Safety of Sacubitril/Valsartan in Japanese Patients With |
| arni-hfref | `screening.dual_screening.disagreements[36].b_axis` | `"NONE"` | PROSE ONLY: record_id=33663237; title=Hemodynamic Effects of Sacubitril-Valsartan Versus Enalapril in Patien |
| arni-hfref | `screening.dual_screening.disagreements[37].b_axis` | `"NONE"` | PROSE ONLY: record_id=33624080; title=Sinergy between drugs and devices in the fight against sudden cardiac |
| arni-hfref | `screening.dual_screening.disagreements[38].b_axis` | `"NONE"` | PROSE ONLY: record_id=33530704; title=Efficacy and Safety of Sacubitril/Valsartan in High-Risk Patients in t |
| arni-hfref | `screening.dual_screening.disagreements[39].b_axis` | `"NONE"` | PROSE ONLY: record_id=33522249; title=Clinical Characteristics and Outcomes of Patients With HFrEF and Chron |
| arni-hfref | `screening.dual_screening.disagreements[3].b_axis` | `"NONE"` | PROSE ONLY: record_id=40265590; title=Comprehensive Analysis of the Effects of Sacubitril/Valsartan Accordin |
| arni-hfref | `screening.dual_screening.disagreements[40].b_axis` | `"NONE"` | PROSE ONLY: record_id=33489085; title=Potential mechanisms of beneficial effect of sacubitril/valsartan on g |
| arni-hfref | `screening.dual_screening.disagreements[41].b_axis` | `"NONE"` | PROSE ONLY: record_id=33357641; title=Efficacy and safety of sacubitril/valsartan compared with enalapril in |
| arni-hfref | `screening.dual_screening.disagreements[42].b_axis` | `"NONE"` | PROSE ONLY: record_id=33314487; title=OUTSTEP-HF: randomised controlled trial comparing short-term effects o |
| arni-hfref | `screening.dual_screening.disagreements[43].b_axis` | `"NONE"` | PROSE ONLY: record_id=33292750; title=Use of Sacubitril/valsartan in patients with cardio toxicity and heart |
| arni-hfref | `screening.dual_screening.disagreements[44].b_axis` | `"NONE"` | PROSE ONLY: record_id=33211601; title=Sacubitril-valsartan improves conduit vessel function and functional c |
| arni-hfref | `screening.dual_screening.disagreements[45].b_axis` | `"NONE"` | PROSE ONLY: record_id=33189630; title=Improvement of Health Status Following Initiation of Sacubitril/Valsar |
| arni-hfref | `screening.dual_screening.disagreements[46].b_axis` | `"NONE"` | PROSE ONLY: record_id=33155868; title=Association of Sacubitril/Valsartan with Metabolic Parameters in Patie |
| arni-hfref | `screening.dual_screening.disagreements[47].b_axis` | `"NONE"` | PROSE ONLY: record_id=33068250; title=Management of patients with chronic heart failure and type 2 diabetes |
| arni-hfref | `screening.dual_screening.disagreements[48].b_axis` | `"NONE"` | PROSE ONLY: record_id=32978755; title=The AWAKE-HF Study: Sacubitril/Valsartan Impact on Daily Physical Acti |
| arni-hfref | `screening.dual_screening.disagreements[49].b_axis` | `"NONE"` | PROSE ONLY: record_id=32919915; title=Angiotensin-Neprilysin Inhibition in Black Americans: Data From the PI |
| arni-hfref | `screening.dual_screening.disagreements[4].b_axis` | `"NONE"` | PROSE ONLY: record_id=40088233; title=Effects of Sacubitril/Valsartan According to Natriuretic Peptide Level |
| arni-hfref | `screening.dual_screening.disagreements[50].b_axis` | `"NONE"` | PROSE ONLY: record_id=32919914; title=Similar Yet Different: Examining the Effects of Sacubitril/Valsartan b |
| arni-hfref | `screening.dual_screening.disagreements[51].b_axis` | `"NONE"` | PROSE ONLY: record_id=32854838; title=Angiotensin Receptor-Neprilysin Inhibition Based on History of Heart F |
| arni-hfref | `screening.dual_screening.disagreements[52].b_axis` | `"NONE"` | PROSE ONLY: record_id=32848403; title=Cardiovascular Outcomes with Sacubitril-Valsartan in Heart Failure: Em |
| arni-hfref | `screening.dual_screening.disagreements[53].b_axis` | `"NONE"` | PROSE ONLY: record_id=32809261; title=Serum potassium in the PARADIGM-HF trial |
| arni-hfref | `screening.dual_screening.disagreements[54].b_axis` | `"NONE"` | PROSE ONLY: record_id=32801725; title=Impact of Sacubitril/Valsartan on Patient Outcomes in Heart Failure: E |
| arni-hfref | `screening.dual_screening.disagreements[55].b_axis` | `"NONE"` | PROSE ONLY: record_id=32800511; title=Efficacy and Safety of Sacubitril/Valsartan by Dose Level Achieved in |
| arni-hfref | `screening.dual_screening.disagreements[56].b_axis` | `"NONE"` | PROSE ONLY: record_id=32800508; title=NT-proBNP Response to Sacubitril/Valsartan in Hospitalized Heart Failu |
| arni-hfref | `screening.dual_screening.disagreements[57].b_axis` | `"NONE"` | PROSE ONLY: record_id=32648251; title=Feasibility of sacubitril/valsartan initiation early after acute decom |
| arni-hfref | `screening.dual_screening.disagreements[58].b_axis` | `"NONE"` | PROSE ONLY: record_id=32407608; title=Liver function and prognosis, and influence of sacubitril/valsartan in |
| arni-hfref | `screening.dual_screening.disagreements[59].b_axis` | `"NONE"` | PROSE ONLY: record_id=32153122; title=Sacubitril/valsartan in patients with heart failure with reduced eject |
| arni-hfref | `screening.dual_screening.disagreements[5].b_axis` | `"NONE"` | PROSE ONLY: record_id=39563094; title=Effects of sacubitril/valsartan according to background beta-blocker t |
| arni-hfref | `screening.dual_screening.disagreements[60].b_axis` | `"NONE"` | PROSE ONLY: record_id=31838035; title=Comparative Effectiveness of Sacubitril-Valsartan Versus ACE/ARB Thera |
| arni-hfref | `screening.dual_screening.disagreements[61].b_axis` | `"NONE"` | PROSE ONLY: record_id=31172710; title=Sacubitril/Valsartan in Asian Patients with Heart Failure with Reduced |
| arni-hfref | `screening.dual_screening.disagreements[62].b_axis` | `"NONE"` | PROSE ONLY: record_id=31078482; title=Outcomes and Effect of Treatment According to Etiology in HFrEF: An An |
| arni-hfref | `screening.dual_screening.disagreements[63].b_axis` | `"NONE"` | PROSE ONLY: record_id=30955360; title=Clinical Outcomes in Patients With Acute Decompensated Heart Failure R |
| arni-hfref | `screening.dual_screening.disagreements[64].b_axis` | `"NONE"` | PROSE ONLY: record_id=30415601; title=Angiotensin-Neprilysin Inhibition in Acute Decompensated Heart Failure |
| arni-hfref | `screening.dual_screening.disagreements[65].b_axis` | `"NONE"` | PROSE ONLY: record_id=28158398; title=Systolic blood pressure, cardiovascular outcomes and efficacy and safe |
| arni-hfref | `screening.dual_screening.disagreements[66].b_axis` | `"NONE"` | PROSE ONLY: record_id=27618854; title=Effects of Sacubitril/Valsartan in the PARADIGM-HF Trial According to |
| arni-hfref | `screening.dual_screening.disagreements[67].b_axis` | `"NONE"` | PROSE ONLY: record_id=27395349; title=Efficacy of Sacubitril/Valsartan Relative to a Prior Decompensation: T |
| arni-hfref | `screening.dual_screening.disagreements[68].b_axis` | `"NONE"` | PROSE ONLY: record_id=27283779; title=Efficacy of sacubitril/valsartan vs enalapril at lower than target dos |
| arni-hfref | `screening.dual_screening.disagreements[69].b_axis` | `"NONE"` | PROSE ONLY: record_id=26915374; title=Influence of Ejection Fraction on Outcomes and Efficacy of Sacubitril/ |
| arni-hfref | `screening.dual_screening.disagreements[6].b_axis` | `"NONE"` | PROSE ONLY: record_id=39387766; title=Race in Heart Failure: A Pooled Participant-Level Analysis of the Glob |
| arni-hfref | `screening.dual_screening.disagreements[70].b_axis` | `"NONE"` | PROSE ONLY: record_id=26541915; title=Comparing LCZ696 with enalapril according to baseline risk using the M |
| arni-hfref | `screening.dual_screening.disagreements[71].b_axis` | `"NONE"` | PROSE ONLY: record_id=26231885; title=Efficacy and safety of LCZ696 (sacubitril-valsartan) according to age: |
| arni-hfref | `screening.dual_screening.disagreements[72].b_axis` | `"NONE"` | PROSE ONLY: record_id=NCT04688294; title=The Bio-Clinical Effects of the Sacubitril-Valsartan Combination on Pa |
| arni-hfref | `screening.dual_screening.disagreements[73].b_axis` | `"NONE"` | PROSE ONLY: record_id=NCT04397302; title=Role of Sacubitril/Valsartan in the Improvement of Heart Failure With |
| arni-hfref | `screening.dual_screening.disagreements[74].b_axis` | `"NONE"` | PROSE ONLY: record_id=NCT05164653; title=Program of Angiotensin-Neprilysin Inhibition in Admitted Patients With |
| arni-hfref | `screening.dual_screening.disagreements[75].b_axis` | `"NONE"` | PROSE ONLY: record_id=NCT02916160; title=Sacubitril-valsartan and Heart Failure Patients: the ENTRESTO-SAS Stud |
| arni-hfref | `screening.dual_screening.disagreements[76].b_axis` | `"NONE"` | PROSE ONLY: record_id=NCT02887183; title=Effects of Sacubitril/Valsartan Therapy on Biomarkers, Myocardial Remo |
| arni-hfref | `screening.dual_screening.disagreements[77].b_axis` | `"NONE"` | PROSE ONLY: record_id=NCT05963282; title=Comparative Effectiveness of Entresto Versus ACEi/ARB in de Novo Heart |
| arni-hfref | `screening.dual_screening.disagreements[78].b_axis` | `"NONE"` | PROSE ONLY: record_id=NCT05613140; title=Sacubitril/Valsartan Treated Adult Patients With Chronic Heart Failure |
| arni-hfref | `screening.dual_screening.disagreements[79].b_axis` | `"NONE"` | PROSE ONLY: record_id=NCT02468232; title=Study of Efficacy and Safety of LCZ696 in Japanese Patients With Chron |
| arni-hfref | `screening.dual_screening.disagreements[7].b_axis` | `"NONE"` | PROSE ONLY: record_id=39262640; title=Influenza Vaccination and Cardiovascular Events in Japanese Patients W |
| arni-hfref | `screening.dual_screening.disagreements[80].b_axis` | `"NONE"` | PROSE ONLY: record_id=NCT05021419; title=Efficacy of a Streamlined Heart Failure Optimization Protocol |
| arni-hfref | `screening.dual_screening.disagreements[81].b_axis` | `"NONE"` | PROSE ONLY: record_id=NCT04023227; title=Efficacy and Safety of Sacubitril/Valsartan Compared With Enalapril on |
| arni-hfref | `screening.dual_screening.disagreements[82].b_axis` | `"NONE"` | PROSE ONLY: record_id=NCT05989503; title=Initiation of ARNi and SGLT2i in Patients With HFrEF |
| arni-hfref | `screening.dual_screening.disagreements[83].b_axis` | `"NONE"` | PROSE ONLY: record_id=NCT07341893; title=Sacubitril-valsartan in Patients With Heart Failure |
| arni-hfref | `screening.dual_screening.disagreements[84].b_axis` | `"NONE"` | PROSE ONLY: record_id=NCT02816736; title=Entresto (LCZ696) In Advanced Heart Failure (LIFE Study) |
| arni-hfref | `screening.dual_screening.disagreements[85].b_axis` | `"NONE"` | PROSE ONLY: record_id=NCT04218435; title=Impact of Sacubitril/Valsartan on Quality of Life and Mortality of CKD |
| arni-hfref | `screening.dual_screening.disagreements[86].b_axis` | `"NONE"` | PROSE ONLY: record_id=NCT01035255; title=This Study Will Evaluate the Efficacy and Safety of LCZ696 Compared to |
| arni-hfref | `screening.dual_screening.disagreements[87].b_axis` | `"NONE"` | PROSE ONLY: record_id=NCT02924727; title=Prospective ARNI vs ACE Inhibitor Trial to DetermIne Superiority in Re |
| arni-hfref | `screening.dual_screening.disagreements[88].b_axis` | `"NONE"` | PROSE ONLY: record_id=NCT05637853; title=Telemonitored Fast Track Medical Sequencing for Heart Failure With Red |
| arni-hfref | `screening.dual_screening.disagreements[89].b_axis` | `"NONE"` | PROSE ONLY: record_id=NCT05168787; title=Efficacy and Safety of Sacubitril/Valsartan in African American Patien |
| arni-hfref | `screening.dual_screening.disagreements[8].b_axis` | `"NONE"` | PROSE ONLY: record_id=39215531; title=In-hospital initiation of angiotensin receptor-neprilysin inhibition i |
| arni-hfref | `screening.dual_screening.disagreements[90].b_axis` | `"NONE"` | PROSE ONLY: record_id=NCT06029712; title=Heart Failure Polypill at a Safety Net Hospital |
| arni-hfref | `screening.dual_screening.disagreements[9].b_axis` | `"NONE"` | PROSE ONLY: record_id=39163041; title=Sacubitril-Valsartan in Patients Requiring Hemodialysis |
| arni-hfref | `screening.dual_screening.unmatched` | `0` | PROSE ONLY: status=COMPLETE -- two independent cross-family screeners, disagreements unadjudicated; denominator=records matched between the two runs, not the 423-record corpus |
| attr-cm-review | `reconciliation.corrections` | `[]` | PROSE ONLY: why_this_step_exists=not recorded on the page this object was built from; clean_because=not recorded on the page this object was built from |
| attr-cm-review | `reconciliation.matches` | `[]` | PROSE ONLY: why_this_step_exists=not recorded on the page this object was built from; clean_because=not recorded on the page this object was built from |
| attr-cm-review | `reconciliation.trial_list_diffs` | `[]` | PROSE ONLY: why_this_step_exists=not recorded on the page this object was built from; clean_because=not recorded on the page this object was built from |
| attr-cm-review | `reconciliation.unresolved` | `[]` | PROSE ONLY: why_this_step_exists=not recorded on the page this object was built from; clean_because=not recorded on the page this object was built from |
| attr-pn-review | `scope_decisions.SCOPE:drug-wide-pivotal-not-heart-failure.sections` | `[]` | PROSE ONLY: decision=not recorded on the page this object was extracted from; conformance=not recorded on the page this object was extracted from |
| attr-pn-review | `screening.excluded` | `[]` | PROSE ONLY: search_note=not recorded on the page this object was extracted from; eligibility=not recorded on the page this object was extracted from |
| attr-pn-review | `screening.records` | `[]` | PROSE ONLY: search_note=not recorded on the page this object was extracted from; eligibility=not recorded on the page this object was extracted from |
| bempedoic-acid-review | `prisma_flow.screened.pubmed_screened` | `0` | PROSE ONLY: why_pubmed_zero=The topic's included set is keyed on REGISTRATION IDs, and screening ran on the registr... |
| bempedoic-acid-review | `reconciliation.corrections` | `[]` | PROSE ONLY: why_this_step_exists=not recorded on the page this object was built from; clean_because=not recorded on the page this object was built from |
| bempedoic-acid-review | `reconciliation.matches` | `[]` | PROSE ONLY: why_this_step_exists=not recorded on the page this object was built from; clean_because=not recorded on the page this object was built from |
| bempedoic-acid-review | `reconciliation.trial_list_diffs` | `[]` | PROSE ONLY: why_this_step_exists=not recorded on the page this object was built from; clean_because=not recorded on the page this object was built from |
| bempedoic-acid-review | `reconciliation.unresolved` | `[]` | PROSE ONLY: why_this_step_exists=not recorded on the page this object was built from; clean_because=not recorded on the page this object was built from |
| bococizumab-lipid-review | `reconciliation.corrections` | `[]` | PROSE ONLY: why_this_step_exists=not recorded on the page this object was built from; clean_because=not recorded on the page this object was built from |
| bococizumab-lipid-review | `reconciliation.matches` | `[]` | PROSE ONLY: why_this_step_exists=not recorded on the page this object was built from; clean_because=not recorded on the page this object was built from |
| bococizumab-lipid-review | `reconciliation.trial_list_diffs` | `[]` | PROSE ONLY: why_this_step_exists=not recorded on the page this object was built from; clean_because=not recorded on the page this object was built from |
| bococizumab-lipid-review | `reconciliation.unresolved` | `[]` | PROSE ONLY: why_this_step_exists=not recorded on the page this object was built from; clean_because=not recorded on the page this object was built from |
| cangrelor-pci-review | `reconciliation.corrections` | `[]` | PROSE ONLY: why_this_step_exists=not recorded on the page this object was built from; clean_because=not recorded on the page this object was built from |
| cangrelor-pci-review | `reconciliation.matches` | `[]` | PROSE ONLY: why_this_step_exists=not recorded on the page this object was built from; clean_because=not recorded on the page this object was built from |
| cangrelor-pci-review | `reconciliation.trial_list_diffs` | `[]` | PROSE ONLY: why_this_step_exists=not recorded on the page this object was built from; clean_because=not recorded on the page this object was built from |
| cangrelor-pci-review | `reconciliation.unresolved` | `[]` | PROSE ONLY: why_this_step_exists=not recorded on the page this object was built from; clean_because=not recorded on the page this object was built from |
| colchicine-cvd-review | `reconciliation.corrections` | `[]` | PROSE ONLY: why_this_step_exists=not recorded on the page this object was built from; clean_because=not recorded on the page this object was built from |
| colchicine-cvd-review | `reconciliation.matches` | `[]` | PROSE ONLY: why_this_step_exists=not recorded on the page this object was built from; clean_because=not recorded on the page this object was built from |
| colchicine-cvd-review | `reconciliation.trial_list_diffs` | `[]` | PROSE ONLY: why_this_step_exists=not recorded on the page this object was built from; clean_because=not recorded on the page this object was built from |
| colchicine-cvd-review | `reconciliation.unresolved` | `[]` | PROSE ONLY: why_this_step_exists=not recorded on the page this object was built from; clean_because=not recorded on the page this object was built from |
| dabigatran-vte-review | `reconciliation.corrections` | `[]` | PROSE ONLY: why_this_step_exists=not recorded on the page this object was built from; clean_because=not recorded on the page this object was built from |
| dabigatran-vte-review | `reconciliation.matches` | `[]` | PROSE ONLY: why_this_step_exists=not recorded on the page this object was built from; clean_because=not recorded on the page this object was built from |
| dabigatran-vte-review | `reconciliation.trial_list_diffs` | `[]` | PROSE ONLY: why_this_step_exists=not recorded on the page this object was built from; clean_because=not recorded on the page this object was built from |
| dabigatran-vte-review | `reconciliation.unresolved` | `[]` | PROSE ONLY: why_this_step_exists=not recorded on the page this object was built from; clean_because=not recorded on the page this object was built from |
| doac-af-review | `scope_decisions.SCOPE:drug-wide-pivotal-not-heart-failure.sections` | `[]` | PROSE ONLY: decision=not recorded on the page this object was extracted from; conformance=not recorded on the page this object was extracted from |
| doac-af-review | `screening.excluded` | `[]` | PROSE ONLY: search_note=not recorded on the page this object was extracted from; eligibility=not recorded on the page this object was extracted from |
| doac-af-review | `screening.records` | `[]` | PROSE ONLY: search_note=not recorded on the page this object was extracted from; eligibility=not recorded on the page this object was extracted from |
| doac-cancer-vte-review | `scope_decisions.SCOPE:drug-wide-pivotal-not-heart-failure.sections` | `[]` | PROSE ONLY: decision=not recorded on the page this object was extracted from; conformance=not recorded on the page this object was extracted from |
| doac-cancer-vte-review | `screening.excluded` | `[]` | PROSE ONLY: search_note=not recorded on the page this object was extracted from; eligibility=not recorded on the page this object was extracted from |
| doac-cancer-vte-review | `screening.records` | `[]` | PROSE ONLY: search_note=not recorded on the page this object was extracted from; eligibility=not recorded on the page this object was extracted from |
| empagliflozin-hf-auto-full-review | `scope_decisions.SCOPE:drug-wide-pivotal-not-heart-failure.sections` | `[]` | PROSE ONLY: decision=not recorded on the page this object was extracted from; conformance=not recorded on the page this object was extracted from |
| empagliflozin-hf-auto-full-review | `screening.excluded` | `[]` | PROSE ONLY: search_note=not recorded on the page this object was extracted from; eligibility=not recorded on the page this object was extracted from |
| empagliflozin-hf-auto-full-review | `screening.records` | `[]` | PROSE ONLY: search_note=not recorded on the page this object was extracted from; eligibility=not recorded on the page this object was extracted from |
| evolocumab-dyslipidemia-review | `reconciliation.corrections` | `[]` | PROSE ONLY: why_this_step_exists=not recorded on the page this object was built from; clean_because=not recorded on the page this object was built from |
| evolocumab-dyslipidemia-review | `reconciliation.matches` | `[]` | PROSE ONLY: why_this_step_exists=not recorded on the page this object was built from; clean_because=not recorded on the page this object was built from |
| evolocumab-dyslipidemia-review | `reconciliation.trial_list_diffs` | `[]` | PROSE ONLY: why_this_step_exists=not recorded on the page this object was built from; clean_because=not recorded on the page this object was built from |
| evolocumab-dyslipidemia-review | `reconciliation.unresolved` | `[]` | PROSE ONLY: why_this_step_exists=not recorded on the page this object was built from; clean_because=not recorded on the page this object was built from |
| evolocumab-mixed-dyslipidemia-auto-full-review | `scope_decisions.SCOPE:drug-wide-pivotal-not-heart-failure.sections` | `[]` | PROSE ONLY: decision=not recorded on the page this object was extracted from; conformance=not recorded on the page this object was extracted from |
| evolocumab-mixed-dyslipidemia-auto-full-review | `screening.excluded` | `[]` | PROSE ONLY: search_note=not recorded on the page this object was extracted from; eligibility=not recorded on the page this object was extracted from |
| evolocumab-mixed-dyslipidemia-auto-full-review | `screening.records` | `[]` | PROSE ONLY: search_note=not recorded on the page this object was extracted from; eligibility=not recorded on the page this object was extracted from |
| fcm-hf-review | `scope_decisions.SCOPE:drug-wide-pivotal-not-heart-failure.sections` | `[]` | PROSE ONLY: decision=not recorded on the page this object was extracted from; conformance=not recorded on the page this object was extracted from |
| fcm-hf-review | `screening.excluded` | `[]` | PROSE ONLY: search_note=not recorded on the page this object was extracted from; eligibility=not recorded on the page this object was extracted from |
| fcm-hf-review | `screening.records` | `[]` | PROSE ONLY: search_note=not recorded on the page this object was extracted from; eligibility=not recorded on the page this object was extracted from |
| finerenone-cv | `scope_decisions.SCOPE:drug-wide-pivotal-not-heart-failure.sections` | `[]` | PROSE ONLY: decision=not recorded on the page this object was extracted from; conformance=not recorded on the page this object was extracted from |
| finerenone-cv | `screening.excluded` | `[]` | PROSE ONLY: search_note=not recorded on the page this object was extracted from; eligibility=not recorded on the page this object was extracted from |
| finerenone-cv | `screening.records` | `[]` | PROSE ONLY: search_note=not recorded on the page this object was extracted from; eligibility=not recorded on the page this object was extracted from |
| finerenone-review | `scope_decisions.SCOPE:drug-wide-pivotal-not-heart-failure.sections` | `[]` | PROSE ONLY: decision=not recorded on the page this object was extracted from; conformance=not recorded on the page this object was extracted from |
| finerenone-review | `screening.excluded` | `[]` | PROSE ONLY: search_note=not recorded on the page this object was extracted from; eligibility=not recorded on the page this object was extracted from |
| finerenone-review | `screening.records` | `[]` | PROSE ONLY: search_note=not recorded on the page this object was extracted from; eligibility=not recorded on the page this object was extracted from |
| hepatitis-b-taf-tdf-review | `scope_decisions.SCOPE:drug-wide-pivotal-not-heart-failure.sections` | `[]` | PROSE ONLY: decision=not recorded on the page this object was extracted from; conformance=not recorded on the page this object was extracted from |
| hepatitis-b-taf-tdf-review | `screening.excluded` | `[]` | PROSE ONLY: search_note=not recorded on the page this object was extracted from; eligibility=not recorded on the page this object was extracted from |
| hepatitis-b-taf-tdf-review | `screening.records` | `[]` | PROSE ONLY: search_note=not recorded on the page this object was extracted from; eligibility=not recorded on the page this object was extracted from |
| icosapent-lipid-auto-full-review | `scope_decisions.SCOPE:drug-wide-pivotal-not-heart-failure.sections` | `[]` | PROSE ONLY: decision=not recorded on the page this object was extracted from; conformance=not recorded on the page this object was extracted from |
| icosapent-lipid-auto-full-review | `screening.excluded` | `[]` | PROSE ONLY: search_note=not recorded on the page this object was extracted from; eligibility=not recorded on the page this object was extracted from |
| icosapent-lipid-auto-full-review | `screening.records` | `[]` | PROSE ONLY: search_note=not recorded on the page this object was extracted from; eligibility=not recorded on the page this object was extracted from |
| inclisiran-lipid-kidney-auto-full-review | `scope_decisions.SCOPE:drug-wide-pivotal-not-heart-failure.sections` | `[]` | PROSE ONLY: decision=not recorded on the page this object was extracted from; conformance=not recorded on the page this object was extracted from |
| inclisiran-lipid-kidney-auto-full-review | `screening.excluded` | `[]` | PROSE ONLY: search_note=not recorded on the page this object was extracted from; eligibility=not recorded on the page this object was extracted from |
| inclisiran-lipid-kidney-auto-full-review | `screening.records` | `[]` | PROSE ONLY: search_note=not recorded on the page this object was extracted from; eligibility=not recorded on the page this object was extracted from |
| incretin-hfpef-review | `reconciliation.corrections` | `[]` | PROSE ONLY: why_this_step_exists=not recorded on the page this object was built from; clean_because=not recorded on the page this object was built from |
| incretin-hfpef-review | `reconciliation.matches` | `[]` | PROSE ONLY: why_this_step_exists=not recorded on the page this object was built from; clean_because=not recorded on the page this object was built from |
| incretin-hfpef-review | `reconciliation.trial_list_diffs` | `[]` | PROSE ONLY: why_this_step_exists=not recorded on the page this object was built from; clean_because=not recorded on the page this object was built from |
| incretin-hfpef-review | `reconciliation.unresolved` | `[]` | PROSE ONLY: why_this_step_exists=not recorded on the page this object was built from; clean_because=not recorded on the page this object was built from |
| intensive-bp-review | `reconciliation.corrections` | `[]` | PROSE ONLY: why_this_step_exists=not recorded on the page this object was built from; clean_because=not recorded on the page this object was built from |
| intensive-bp-review | `reconciliation.matches` | `[]` | PROSE ONLY: why_this_step_exists=not recorded on the page this object was built from; clean_because=not recorded on the page this object was built from |
| intensive-bp-review | `reconciliation.trial_list_diffs` | `[]` | PROSE ONLY: why_this_step_exists=not recorded on the page this object was built from; clean_because=not recorded on the page this object was built from |
| intensive-bp-review | `reconciliation.unresolved` | `[]` | PROSE ONLY: why_this_step_exists=not recorded on the page this object was built from; clean_because=not recorded on the page this object was built from |
| mavacamten-hcm-review | `reconciliation.corrections` | `[]` | PROSE ONLY: why_this_step_exists=not recorded on the page this object was built from; clean_because=not recorded on the page this object was built from |
| mavacamten-hcm-review | `reconciliation.matches` | `[]` | PROSE ONLY: why_this_step_exists=not recorded on the page this object was built from; clean_because=not recorded on the page this object was built from |
| mavacamten-hcm-review | `reconciliation.trial_list_diffs` | `[]` | PROSE ONLY: why_this_step_exists=not recorded on the page this object was built from; clean_because=not recorded on the page this object was built from |
| mavacamten-hcm-review | `reconciliation.unresolved` | `[]` | PROSE ONLY: why_this_step_exists=not recorded on the page this object was built from; clean_because=not recorded on the page this object was built from |
| mavacamten-ohcm-review | `reconciliation.corrections` | `[]` | PROSE ONLY: why_this_step_exists=not recorded on the page this object was built from; clean_because=not recorded on the page this object was built from |
| mavacamten-ohcm-review | `reconciliation.matches` | `[]` | PROSE ONLY: why_this_step_exists=not recorded on the page this object was built from; clean_because=not recorded on the page this object was built from |
| mavacamten-ohcm-review | `reconciliation.trial_list_diffs` | `[]` | PROSE ONLY: why_this_step_exists=not recorded on the page this object was built from; clean_because=not recorded on the page this object was built from |
| mavacamten-ohcm-review | `reconciliation.unresolved` | `[]` | PROSE ONLY: why_this_step_exists=not recorded on the page this object was built from; clean_because=not recorded on the page this object was built from |
| mitral-funcmr-review | `reconciliation.corrections` | `[]` | PROSE ONLY: why_this_step_exists=not recorded on the page this object was built from; clean_because=not recorded on the page this object was built from |
| mitral-funcmr-review | `reconciliation.matches` | `[]` | PROSE ONLY: why_this_step_exists=not recorded on the page this object was built from; clean_because=not recorded on the page this object was built from |
| mitral-funcmr-review | `reconciliation.trial_list_diffs` | `[]` | PROSE ONLY: why_this_step_exists=not recorded on the page this object was built from; clean_because=not recorded on the page this object was built from |
| mitral-funcmr-review | `reconciliation.unresolved` | `[]` | PROSE ONLY: why_this_step_exists=not recorded on the page this object was built from; clean_because=not recorded on the page this object was built from |
| netarsudil-ocular-hypertension-auto-full-review | `scope_decisions.SCOPE:drug-wide-pivotal-not-heart-failure.sections` | `[]` | PROSE ONLY: decision=not recorded on the page this object was extracted from; conformance=not recorded on the page this object was extracted from |
| netarsudil-ocular-hypertension-auto-full-review | `screening.excluded` | `[]` | PROSE ONLY: search_note=not recorded on the page this object was extracted from; eligibility=not recorded on the page this object was extracted from |
| netarsudil-ocular-hypertension-auto-full-review | `screening.records` | `[]` | PROSE ONLY: search_note=not recorded on the page this object was extracted from; eligibility=not recorded on the page this object was extracted from |
| pcsk9-inhibitors-cv-review | `scope_decisions.SCOPE:drug-wide-pivotal-not-heart-failure.sections` | `[]` | PROSE ONLY: decision=not recorded on the page this object was extracted from; conformance=not recorded on the page this object was extracted from |
| pcsk9-inhibitors-cv-review | `screening.excluded` | `[]` | PROSE ONLY: search_note=not recorded on the page this object was extracted from; eligibility=not recorded on the page this object was extracted from |
| pcsk9-inhibitors-cv-review | `screening.records` | `[]` | PROSE ONLY: search_note=not recorded on the page this object was extracted from; eligibility=not recorded on the page this object was extracted from |
| pcsk9-review | `scope_decisions.SCOPE:drug-wide-pivotal-not-heart-failure.sections` | `[]` | PROSE ONLY: decision=not recorded on the page this object was extracted from; conformance=not recorded on the page this object was extracted from |
| pcsk9-review | `screening.excluded` | `[]` | PROSE ONLY: search_note=not recorded on the page this object was extracted from; eligibility=not recorded on the page this object was extracted from |
| pcsk9-review | `screening.records` | `[]` | PROSE ONLY: search_note=not recorded on the page this object was extracted from; eligibility=not recorded on the page this object was extracted from |
| pitavastatin-auto-full-review | `scope_decisions.SCOPE:drug-wide-pivotal-not-heart-failure.sections` | `[]` | PROSE ONLY: decision=not recorded on the page this object was extracted from; conformance=not recorded on the page this object was extracted from |
| pitavastatin-auto-full-review | `screening.excluded` | `[]` | PROSE ONLY: search_note=not recorded on the page this object was extracted from; eligibility=not recorded on the page this object was extracted from |
| pitavastatin-auto-full-review | `screening.records` | `[]` | PROSE ONLY: search_note=not recorded on the page this object was extracted from; eligibility=not recorded on the page this object was extracted from |
| rivaroxaban-acs-review | `reconciliation.corrections` | `[]` | PROSE ONLY: why_this_step_exists=not recorded on the page this object was built from; clean_because=not recorded on the page this object was built from |
| rivaroxaban-acs-review | `reconciliation.matches` | `[]` | PROSE ONLY: why_this_step_exists=not recorded on the page this object was built from; clean_because=not recorded on the page this object was built from |
| rivaroxaban-acs-review | `reconciliation.trial_list_diffs` | `[]` | PROSE ONLY: why_this_step_exists=not recorded on the page this object was built from; clean_because=not recorded on the page this object was built from |
| rivaroxaban-acs-review | `reconciliation.unresolved` | `[]` | PROSE ONLY: why_this_step_exists=not recorded on the page this object was built from; clean_because=not recorded on the page this object was built from |
| rivaroxaban-vasc-review | `reconciliation.corrections` | `[]` | PROSE ONLY: why_this_step_exists=not recorded on the page this object was built from; clean_because=not recorded on the page this object was built from |
| rivaroxaban-vasc-review | `reconciliation.matches` | `[]` | PROSE ONLY: why_this_step_exists=not recorded on the page this object was built from; clean_because=not recorded on the page this object was built from |
| rivaroxaban-vasc-review | `reconciliation.trial_list_diffs` | `[]` | PROSE ONLY: why_this_step_exists=not recorded on the page this object was built from; clean_because=not recorded on the page this object was built from |
| rivaroxaban-vasc-review | `reconciliation.unresolved` | `[]` | PROSE ONLY: why_this_step_exists=not recorded on the page this object was built from; clean_because=not recorded on the page this object was built from |
| rosuvastatin-auto-full-review | `scope_decisions.SCOPE:drug-wide-pivotal-not-heart-failure.sections` | `[]` | PROSE ONLY: decision=not recorded on the page this object was extracted from; conformance=not recorded on the page this object was extracted from |
| rosuvastatin-auto-full-review | `screening.excluded` | `[]` | PROSE ONLY: search_note=not recorded on the page this object was extracted from; eligibility=not recorded on the page this object was extracted from |
| rosuvastatin-auto-full-review | `screening.records` | `[]` | PROSE ONLY: search_note=not recorded on the page this object was extracted from; eligibility=not recorded on the page this object was extracted from |
| rotavirus-vaccine-africa-review | `scope_decisions.SCOPE:drug-wide-pivotal-not-heart-failure.sections` | `[]` | PROSE ONLY: decision=not recorded on the page this object was extracted from; conformance=not recorded on the page this object was extracted from |
| rotavirus-vaccine-africa-review | `screening.excluded` | `[]` | PROSE ONLY: search_note=not recorded on the page this object was extracted from; eligibility=not recorded on the page this object was extracted from |
| rotavirus-vaccine-africa-review | `screening.records` | `[]` | PROSE ONLY: search_note=not recorded on the page this object was extracted from; eligibility=not recorded on the page this object was extracted from |
| sglt2-ckd-review | `scope_decisions.SCOPE:drug-wide-pivotal-not-heart-failure.sections` | `[]` | PROSE ONLY: decision=not recorded on the page this object was extracted from; conformance=not recorded on the page this object was extracted from |
| sglt2-ckd-review | `screening.excluded` | `[]` | PROSE ONLY: search_note=not recorded on the page this object was extracted from; eligibility=not recorded on the page this object was extracted from |
| sglt2-ckd-review | `screening.records` | `[]` | PROSE ONLY: search_note=not recorded on the page this object was extracted from; eligibility=not recorded on the page this object was extracted from |
| sglt2-mace-cvot-review | `scope_decisions.SCOPE:drug-wide-pivotal-not-heart-failure.sections` | `[]` | PROSE ONLY: decision=not recorded on the page this object was extracted from; conformance=not recorded on the page this object was extracted from |
| sglt2-mace-cvot-review | `screening.excluded` | `[]` | PROSE ONLY: search_note=not recorded on the page this object was extracted from; eligibility=not recorded on the page this object was extracted from |
| sglt2-mace-cvot-review | `screening.records` | `[]` | PROSE ONLY: search_note=not recorded on the page this object was extracted from; eligibility=not recorded on the page this object was extracted from |
| ablation-af-review | `published_comparison.denominator.errors_in_the_literature` | `0` | YES: rows_checked (count-key) |
| ablation-af-review | `reconciliation.corrections` | `[]` | YES: target_source_id (source-key) |
| ablation-af-review | `reconciliation.matches` | `[]` | YES: target_source_id (source-key) |
| ablation-af-review | `reconciliation.trial_list_diffs` | `[]` | YES: target_source_id (source-key) |
| ablation-af-review | `reconciliation.unresolved` | `[]` | YES: target_source_id (source-key) |
| acs-antiplatelet-review | `reconciliation.corrections` | `[]` | YES: target_source_id (source-key) |
| acs-antiplatelet-review | `reconciliation.matches` | `[]` | YES: target_source_id (source-key) |
| acs-antiplatelet-review | `reconciliation.trial_list_diffs` | `[]` | YES: target_source_id (source-key) |
| acs-antiplatelet-review | `reconciliation.unresolved` | `[]` | YES: target_source_id (source-key) |
| alirocumab-lipid | `published_comparison.denominator.errors_in_the_literature` | `0` | YES: rows_checked (count-key) |
| arni-hfref | `reconciliation.clean` | `false` | YES: target_source_id (source-key) |
| arni-hfref | `screening.records[12].criteria_failed` | `[]` | YES: checked_on (date-key, date-value) |
| attr-pn-review | `reconciliation.corrections` | `[]` | YES: target_source_id (source-key) |
| attr-pn-review | `reconciliation.matches` | `[]` | YES: target_source_id (source-key) |
| attr-pn-review | `reconciliation.trial_list_diffs` | `[]` | YES: target_source_id (source-key) |
| attr-pn-review | `reconciliation.unresolved` | `[]` | YES: target_source_id (source-key) |
| bempedoic-acid-review | `k_cascade.k_unscreened_remainder` | `0` | YES: k_included_in_object (count-key); k_unscreened_remainder_note (date-value, method-value) |
| bempedoic-acid-review | `registration_identity.duplicate_seeding_check.shared_with_other_topics` | `false` | YES: checked_against (date-value, file-value, source-key) |
| doac-af-review | `reconciliation.corrections` | `[]` | YES: target_source_id (source-key) |
| doac-af-review | `reconciliation.matches` | `[]` | YES: target_source_id (source-key) |
| doac-af-review | `reconciliation.trial_list_diffs` | `[]` | YES: target_source_id (source-key) |
| doac-af-review | `reconciliation.unresolved` | `[]` | YES: target_source_id (source-key) |
| doac-cancer-vte-review | `reconciliation.corrections` | `[]` | YES: target_source_id (source-key) |
| doac-cancer-vte-review | `reconciliation.matches` | `[]` | YES: target_source_id (source-key) |
| doac-cancer-vte-review | `reconciliation.trial_list_diffs` | `[]` | YES: target_source_id (source-key) |
| doac-cancer-vte-review | `reconciliation.unresolved` | `[]` | YES: target_source_id (source-key) |
| empagliflozin-hf-auto-full-review | `reconciliation.corrections` | `[]` | YES: target_source_id (source-key) |
| empagliflozin-hf-auto-full-review | `reconciliation.matches` | `[]` | YES: target_source_id (source-key) |
| empagliflozin-hf-auto-full-review | `reconciliation.trial_list_diffs` | `[]` | YES: target_source_id (source-key) |
| empagliflozin-hf-auto-full-review | `reconciliation.unresolved` | `[]` | YES: target_source_id (source-key) |
| evolocumab-mixed-dyslipidemia-auto-full-review | `reconciliation.corrections` | `[]` | YES: target_source_id (source-key) |
| evolocumab-mixed-dyslipidemia-auto-full-review | `reconciliation.matches` | `[]` | YES: target_source_id (source-key) |
| evolocumab-mixed-dyslipidemia-auto-full-review | `reconciliation.trial_list_diffs` | `[]` | YES: target_source_id (source-key) |
| evolocumab-mixed-dyslipidemia-auto-full-review | `reconciliation.unresolved` | `[]` | YES: target_source_id (source-key) |
| fcm-hf-review | `reconciliation.corrections` | `[]` | YES: target_source_id (source-key) |
| fcm-hf-review | `reconciliation.matches` | `[]` | YES: target_source_id (source-key) |
| fcm-hf-review | `reconciliation.trial_list_diffs` | `[]` | YES: target_source_id (source-key) |
| fcm-hf-review | `reconciliation.unresolved` | `[]` | YES: target_source_id (source-key) |
| finerenone-cv | `reconciliation.corrections` | `[]` | YES: target_source_id (source-key) |
| finerenone-cv | `reconciliation.matches` | `[]` | YES: target_source_id (source-key) |
| finerenone-cv | `reconciliation.trial_list_diffs` | `[]` | YES: target_source_id (source-key) |
| finerenone-cv | `reconciliation.unresolved` | `[]` | YES: target_source_id (source-key) |
| finerenone-review | `reconciliation.corrections` | `[]` | YES: target_source_id (source-key) |
| finerenone-review | `reconciliation.matches` | `[]` | YES: target_source_id (source-key) |
| finerenone-review | `reconciliation.trial_list_diffs` | `[]` | YES: target_source_id (source-key) |
| finerenone-review | `reconciliation.unresolved` | `[]` | YES: target_source_id (source-key) |
| hepatitis-b-taf-tdf-review | `reconciliation.corrections` | `[]` | YES: target_source_id (source-key) |
| hepatitis-b-taf-tdf-review | `reconciliation.matches` | `[]` | YES: target_source_id (source-key) |
| hepatitis-b-taf-tdf-review | `reconciliation.trial_list_diffs` | `[]` | YES: target_source_id (source-key) |
| hepatitis-b-taf-tdf-review | `reconciliation.unresolved` | `[]` | YES: target_source_id (source-key) |
| icosapent-lipid-auto-full-review | `reconciliation.corrections` | `[]` | YES: target_source_id (source-key) |
| icosapent-lipid-auto-full-review | `reconciliation.matches` | `[]` | YES: target_source_id (source-key) |
| icosapent-lipid-auto-full-review | `reconciliation.trial_list_diffs` | `[]` | YES: target_source_id (source-key) |
| icosapent-lipid-auto-full-review | `reconciliation.unresolved` | `[]` | YES: target_source_id (source-key) |
| inclisiran-lipid-kidney-auto-full-review | `reconciliation.corrections` | `[]` | YES: target_source_id (source-key) |
| inclisiran-lipid-kidney-auto-full-review | `reconciliation.matches` | `[]` | YES: target_source_id (source-key) |
| inclisiran-lipid-kidney-auto-full-review | `reconciliation.trial_list_diffs` | `[]` | YES: target_source_id (source-key) |
| inclisiran-lipid-kidney-auto-full-review | `reconciliation.unresolved` | `[]` | YES: target_source_id (source-key) |
| iv-iron-hf | `published_comparison.denominator.errors` | `0` | YES: rows_checked (count-key) |
| iv-iron-hf | `published_comparison.denominator.errors_in_the_literature` | `0` | YES: rows_checked (count-key) |
| iv-iron-hf | `published_comparison.denominator.errors_in_this_review` | `0` | YES: rows_checked (count-key) |
| iv-iron-hf | `reconciliation.clean` | `false` | YES: target_source_id (source-key); access_limitation (method-value); what_the_benchmarks_show (method-key) |
| iv-iron-hf | `results.by_outcome.hfh_cvd_first.sensitivity.between_study_variance_method_comparison.interval_methods_agree` | `false` | YES: methods (method-key) |
| iv-iron-hf | `results.by_outcome.hfh_cvd_recurrent.sensitivity.between_study_variance_method_comparison.interval_methods_agree` | `false` | YES: methods (method-key) |
| iv-iron-hf | `results.by_outcome.hfh_recurrent.sensitivity.between_study_variance_method_comparison.interval_methods_agree` | `false` | YES: methods (method-key) |
| netarsudil-ocular-hypertension-auto-full-review | `reconciliation.corrections` | `[]` | YES: target_source_id (source-key) |
| netarsudil-ocular-hypertension-auto-full-review | `reconciliation.matches` | `[]` | YES: target_source_id (source-key) |
| netarsudil-ocular-hypertension-auto-full-review | `reconciliation.trial_list_diffs` | `[]` | YES: target_source_id (source-key) |
| netarsudil-ocular-hypertension-auto-full-review | `reconciliation.unresolved` | `[]` | YES: target_source_id (source-key) |
| pcsk9-inhibitors-cv-review | `reconciliation.corrections` | `[]` | YES: target_source_id (source-key) |
| pcsk9-inhibitors-cv-review | `reconciliation.matches` | `[]` | YES: target_source_id (source-key) |
| pcsk9-inhibitors-cv-review | `reconciliation.trial_list_diffs` | `[]` | YES: target_source_id (source-key) |
| pcsk9-inhibitors-cv-review | `reconciliation.unresolved` | `[]` | YES: target_source_id (source-key) |
| pcsk9-review | `reconciliation.corrections` | `[]` | YES: target_source_id (source-key) |
| pcsk9-review | `reconciliation.matches` | `[]` | YES: target_source_id (source-key) |
| pcsk9-review | `reconciliation.trial_list_diffs` | `[]` | YES: target_source_id (source-key) |
| pcsk9-review | `reconciliation.unresolved` | `[]` | YES: target_source_id (source-key) |
| pitavastatin-auto-full-review | `reconciliation.corrections` | `[]` | YES: target_source_id (source-key) |
| pitavastatin-auto-full-review | `reconciliation.matches` | `[]` | YES: target_source_id (source-key) |
| pitavastatin-auto-full-review | `reconciliation.trial_list_diffs` | `[]` | YES: target_source_id (source-key) |
| pitavastatin-auto-full-review | `reconciliation.unresolved` | `[]` | YES: target_source_id (source-key) |
| rosuvastatin-auto-full-review | `reconciliation.corrections` | `[]` | YES: target_source_id (source-key) |
| rosuvastatin-auto-full-review | `reconciliation.matches` | `[]` | YES: target_source_id (source-key) |
| rosuvastatin-auto-full-review | `reconciliation.trial_list_diffs` | `[]` | YES: target_source_id (source-key) |
| rosuvastatin-auto-full-review | `reconciliation.unresolved` | `[]` | YES: target_source_id (source-key) |
| rotavirus-vaccine-africa-review | `reconciliation.corrections` | `[]` | YES: target_source_id (source-key) |
| rotavirus-vaccine-africa-review | `reconciliation.matches` | `[]` | YES: target_source_id (source-key) |
| rotavirus-vaccine-africa-review | `reconciliation.trial_list_diffs` | `[]` | YES: target_source_id (source-key) |
| rotavirus-vaccine-africa-review | `reconciliation.unresolved` | `[]` | YES: target_source_id (source-key) |
| sglt2-ckd-review | `reconciliation.corrections` | `[]` | YES: target_source_id (source-key) |
| sglt2-ckd-review | `reconciliation.matches` | `[]` | YES: target_source_id (source-key) |
| sglt2-ckd-review | `reconciliation.trial_list_diffs` | `[]` | YES: target_source_id (source-key) |
| sglt2-ckd-review | `reconciliation.unresolved` | `[]` | YES: target_source_id (source-key) |
| sglt2-hf | `reconciliation.clean` | `false` | YES: target_source_id (source-key); access_limitation (method-value); what_the_benchmarks_show (method-key) |
| sglt2-hf | `screening_of_remainder.eligible_and_poolable` | `[]` | YES: screened_on (date-value); n_screened (count-key); screened_against (method-value); k_after_screening (count-key) |
| sglt2-mace-cvot-review | `reconciliation.corrections` | `[]` | YES: target_source_id (source-key) |
| sglt2-mace-cvot-review | `reconciliation.matches` | `[]` | YES: target_source_id (source-key) |
| sglt2-mace-cvot-review | `reconciliation.trial_list_diffs` | `[]` | YES: target_source_id (source-key) |
| sglt2-mace-cvot-review | `reconciliation.unresolved` | `[]` | YES: target_source_id (source-key) |
| sotagliflozin-hf | `published_comparison.denominator.errors` | `0` | YES: rows_checked (count-key) |
| sotagliflozin-hf | `published_comparison.denominator.errors_in_the_literature` | `0` | YES: rows_checked (count-key) |
| sotagliflozin-hf | `published_comparison.denominator.errors_in_this_review` | `0` | YES: rows_checked (count-key) |
| sotagliflozin-hf | `reconciliation.clean` | `false` | YES: clean_because (method-value); target_source_id (source-key) |

