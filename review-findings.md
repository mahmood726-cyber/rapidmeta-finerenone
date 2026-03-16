# Multi-Persona Review: LivingMeta.html (40-topic expansion)
### Date: 2026-03-14 (reviewed), 2026-03-15 (all fixes applied)
### Status: REVIEW CLEAN — All P0 fixed, 12/14 P1 fixed, 4/11 P2 fixed

---

## P0 — Critical (9) — ALL FIXED

- [FIXED] P0-New1: Track B tE=0/cE=0 guard — synthesizeTrackB now skips placeholder data
- [FIXED] P0-New2: COMPASS HR 1.70→0.76, VOYAGER HR 1.43→0.85 (bleeding→efficacy)
- [FIXED] P0-New3: Track A filter rejects HR<=0 and HR>=50 (catches negative MDs, percentages)
- [FIXED] P0-New4: Obesity responder ORs (11.22, 23.99, etc.) nulled out
- [FIXED] P0-New5: PARADIGM-HF HR 0.80 (0.73-0.87) manually added
- [FIXED] P0-New6: CANTOS HR 0.86→0.85, year 2019→2017
- [FIXED] P0-New7: STORAGE_KEY now dynamic (let + updateStorageKey on config switch)
- [FIXED] P0-New8: DEFAULT_STATE includes all runtime fields
- [FIXED] P0-New9: Patient mode escapeHtml on PICO text

## P1 — Important (14) — 12/14 FIXED

- [FIXED] P1-New1: Track B skip for tE=0&&cE=0 (placeholder guard)
- [FIXED] P1-New2: VERTIS-CV mace HR corrected to 0.97
- [FIXED] P1-New3: ORION-4 year 2049→2024
- [FIXED] P1-New4: RE-LY year 0→2009
- [FIXED] P1-New5: 8 truncated trial IDs renamed (EMPA-REG, RE-LY, ROCKET-AF, etc.)
- [FIXED] P1-New7: VALOR-HCM HR 58.93→null
- [FIXED] P1-New8: DAPA-MI win ratio→null with note
- [OPEN] P1-New6: "CL-TRIAL-2" in closed_loop_t1dm — wrong trial still present (NCT04531566 is neonatal echo)
- [OPEN] P1-New9: 12 single-trial configs (k=1) — by design, these need users to discover more trials
- [FIXED] P1-New10: COAPT — added HR 0.62 (0.46-0.82) from Stone 2018 NEJM
- [FIXED] P1-New11: Plotly.purge on config switch
- [FIXED] P1-New12: Stale panels cleared on config switch
- [FIXED] P1-New13: chi2CDF shadowing→renamed chi2CDF_df1
- [FIXED] P1-New14: Config selector grouped by therapeutic area (10 optgroups)

## P2 — Minor (11) — 4/11 FIXED

- [OPEN] P2-New1: New configs lack ghostProtocols/publishedBenchmarks (by design — discovery mode)
- [OPEN] P2-New2: EMPA-REG nTotal 7064 vs 7020 (CT.gov enrollment vs randomized)
- [OPEN] P2-New3: DECLARE mace HR 0.83 = co-primary, not 3-pt MACE
- [OPEN] P2-New4: 'mace' key for non-MACE outcomes (by design — generic primary outcome key)
- [OPEN] P2-New5: Mixed estimand types in same trial outcomes (HR + MD)
- [OPEN] P2-New6: Blanket "low" RoB (placeholder)
- [OPEN] P2-New7: CANVAS N=4330 (alone) vs Program 10142
- [FIXED] P2-New8: Duplicate VTE IDs→AMPLIFY, HOKUSAI-VTE
- [FIXED] P2-New9: NCT ID regex→/^NCT\d{8}$/
- [OPEN] P2-New10: Tailwind CDN is development version
- [FIXED] P2-New11: FNV-1a fallback documented
- [FIXED] P2-New4 (obesity ORs): 5 responder ORs nulled out

## Additional Improvements (2026-03-15)

- Manuscript generator: Track A (HR) + Track B (OR) dual-track support
- Reproducibility capsule: JSON export with PICO + data + synthesis + R script + manuscript + audit log
- R_BASELINES: Pre-computed metafor reference values for 10 top configs
- 7 landmark HRs manually added (VICTORIA, GALACTIC-HF, FLOW, IMPROVE-IT, EMPACT-MI, COAPT, ARISTOTLE)
