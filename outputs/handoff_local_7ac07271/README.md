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

**Malaria HRP-2 RDT DTA** (a real finding — show WITH the mechanism):
```
{ "app":"<MALARIA_RDT_APP>.html",
  "question":"HRP-2 malaria RDT vs microscopy",
  "measure_label":"Sensitivity / Specificity",
  "published":[{"ref":"Cochrane Abba 2011 (CD008122.pub2), HRP-2 type","doi":"10.1002/14651858.CD008122.pub2",
                "their":"94.8% / 95.2%","their_ci":"(93.1-96.1) / (93.2-96.7)","k_theirs":71}],
  "ours":"93.7% / 84.9%","ours_ci":"(88.0-96.8) / (72.7-92.2)","k_ours":3,
  "they_have_we_dont":"68 more studies, many older / mixed settings",
  "we_have_they_dont":"3 recent high-transmission African studies, all 2x2s read DIRECTLY",
  "verdict":"Se MATCHES. Sp ~10pp lower — a REAL finding, not an artifact: HRP-2 antigen persists after treatment + asymptomatic parasitaemia in high-transmission Africa lowers specificity.",
  "verdict_color":"#b8860b",
  "note":"Cross-vendor unanimous: show WITH the antigen-persistence explanation and a strong small-n caveat (k=3). REQUIRED: drop the non-indexed Rwanda study; use the DIRECTLY-READ SD-Bioline 2x2 (Orimadegun 2021, PMID 33851670, TP87/FP27/FN2/TN74) — never a PPV-reconstructed 2x2." }
```

## The one rule
**Every displayed number must be traceable to source; if it cannot be, it does not contribute — blank it or exclude it, and say so on the app's face.** `build_gate.py` enforces the count/effect half of this automatically.
