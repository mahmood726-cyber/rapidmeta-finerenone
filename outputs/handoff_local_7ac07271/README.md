# Handoff → lane `local_7ac07271` (RapidMeta as delivery channel)

For bundling the harness into the app download. **Do not duplicate this work — import these.** All are self-contained, offline-safe (no external calls), and deterministic.

## Provenance records (what was changed, and why — ship these with the corpus)
- `count_provenance_2026-07-12.json` — every count re-derived-or-blanked, with source + recomputed-vs-displayed effect.
- `year_provenance_2026-07-12.json` — 422 year corrections (displayed → PubMed pub year).
- `label_pmid_provenance_2026-07-12.json` — trial labels + backfilled PMIDs.

## Reusable code (single source of truth — import, don't re-implement)
| File | Use |
|---|---|
| `count_consistency.py` | the invariant: counts must imply the ratio effect's direction. `consistent()`, `implied_rr()`, `orient_to_effect()`. |
| `build_gate.py` | the MANDATORY build gate — `gate_file(path) -> (hard, warn)`. HARD blocks the ship; run it on every app before bundling. |
| `assert_count_effect_consistency.py` | top-level realData walker (handles NCT/PMID/single-quoted/JSON keys, leading-dot decimals) + the count/effect gate. |
| `classify_corpus.py` | per-app status: verified / provenance-ok / flagged / delist:{k1,no-source,non-poolable}. |
| `inject_verification_banner.py` | the in-app verification banner (offline-safe, additive, idempotent). |
| `inject_cochrane_panel.py` | the in-app "Published MA comparison" panel — pass a config list (see below). |
| `preregister_protocol.py` + `protocol_diff.py` | protocol pre-registration by git commit + protocol-as-registered vs analysis-as-run diff. |

## DTA demo-app Cochrane-panel configs (ready to inject)
Feed these to `inject_cochrane_panel.py` for the demo lane's DTA dashboards. Numbers are computed/verified (2026-07-13).

**TB Xpert MTB/RIF DTA** (the killer slide — matches Cochrane):
```
{ "app":"<TB_XPERT_APP>.html",
  "question":"Xpert MTB/RIF vs culture for pulmonary TB (initial test)",
  "measure_label":"Sensitivity / Specificity",
  "published":[{"ref":"Cochrane Steingart 2014 (CD009593.pub3)","doi":"10.1002/14651858.CD009593.pub3",
                "their":"89% / 99%","their_ci":"(85-92) / (98-99)","k_theirs":22}],
  "ours":"85.8% / 97.8%","ours_ci":"(83.6-87.7) / (97.2-98.2)","k_ours":17,
  "they_have_we_dont":"5 additional studies","we_have_they_dont":"a narrower recent set (more smear-negative)",
  "verdict":"MATCH — same direction & conclusion; ~3pp lower Se / ~1pp lower Sp, CIs overlap. Explained by study set.",
  "verdict_color":"#0a7d33",
  "note":"Cross-vendor unanimous (Codex + agy-Gemini): defensible study-set difference, not an error." }
```

**Malaria HRP-2 RDT DTA** — RESOLVED 2026-07-13 with source-READ 2×2s (see `C:\Projects\DEMO-RDT-DTA-RESOLVED-2026-07-13.md`). The three 2×2s below are read from each paper's directly-reported Se/Sp/N/prevalence/PPV (PubMed), NOT PPV-reconstructed. Rwanda + the reconstructed SD-Bioline are DROPPED.

Source-verified 2×2s (TP/FP/FN/TN):
- Orimadegun 2021 SD-Bioline, ref=microscopy, PMID 33851670: **87/27/2/74** (Se 97.8% / Sp 73.3%)
- Batwala 2010 Paracheck, ref=**PCR**, PMID 21126328: **81/29/8/182** (Se 91.0% / Sp 86.3%)
- Adebisi 2018 CareStart, ref=microscopy, PMID 30574261: **53/27/3/287** (Se 94.6% / Sp 91.4%)

Re-pool (DL logit): Se **94.3%** (88.2–97.4) I²=41%; Sp **85.1%** (72.9–92.4) **I²=90%**. Cross-vendor (Codex-A + Codex-B): show pooled Se (reproduces Cochrane ~94.8%); show Sp **per-study, NOT pooled** (I²=90% + mixed reference standards make a single Sp indefensible as a headline).
```
{ "app":"<MALARIA_RDT_APP>.html",
  "question":"HRP-2 malaria RDT — sensitivity reproduces Cochrane; specificity is heterogeneous",
  "measure_label":"Sensitivity (pooled) / Specificity (per-study)",
  "published":[{"ref":"Cochrane Abba 2011 (CD008122.pub2), HRP-2 — RE-VERIFY vs review","doi":"10.1002/14651858.CD008122.pub2",
                "their":"Se ~94.8% / Sp ~95.2%","their_ci":"(93.1-96.1) / (93.2-96.7)","k_theirs":71}],
  "ours":"Se 94.3% / Sp 73-91% (per-study)","ours_ci":"Se (88.2-97.4); Sp I2=90%","k_ours":3,
  "they_have_we_dont":"68 more studies, many older / mixed settings",
  "we_have_they_dont":"3 recent high-transmission African studies, all 2x2s read DIRECTLY from source",
  "verdict":"Se MATCHES Cochrane. Specificity is HETEROGENEOUS (73-91%, I2=90%) and setting-dependent, sometimes well below Cochrane's ~95% — consistent with HRP-2 persistence + submicroscopic parasitaemia, but NOT a uniform effect (k=3, mixed reference standards). Show Sp per-study, not as one pooled number.",
  "verdict_color":"#b8860b",
  "note":"Cross-vendor (Codex-A+B) confirmed. REQUIRED: drop Rwanda + the PPV-reconstructed SD-Bioline; use the three source-read 2x2s above; add the reference-standard column (Batwala=PCR); RE-VERIFY the Cochrane Abba 2011 numbers against the actual review before demo." }
```

## The one rule
**Every displayed number must be traceable to source; if it cannot be, it does not contribute — blank it or exclude it, and say so on the app's face.** `build_gate.py` enforces the count/effect half of this automatically.
