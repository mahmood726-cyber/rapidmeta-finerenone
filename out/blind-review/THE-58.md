# The 58 pages needing a human ruling

51 unclassified legacy pages + 7 unclassified stubs. Every other served page is
accounted for: 141 attributed, 744 unpopulated app shells, 506 redirect/withdrawal
notices, 14 current-generation without a store.

Each row carries what I think it is and the evidence for it. Nothing here is a guess
dressed as a finding — where I could not tell, the row says so.

---

## A. The six that actually matter: real reviews with real results, entirely unaudited

All ~280 KB, all carrying sensitivity/specificity values, percentage CIs and study counts.
**These are genuine diagnostic-accuracy reviews presenting real claims to a reader, and no
instrument has ever examined one** — my harness has no DTA parser at all, so they were
NOT-ASSESSABLE for structural reasons, not because they are empty.

| page | bytes | subject |
|---|---|---|
| `PTAU217_AD_DTA_REVIEW.html` | 276,339 | Plasma p-tau217 for Alzheimer's |
| `HSCTN_NSTEMI_DTA_REVIEW.html` | 277,280 | hs-cTn 0/1h for NSTEMI rule-out |
| `COVID_ANTIGEN_DTA_REVIEW.html` | 278,483 | SARS-CoV-2 rapid antigen tests |
| `MPMRI_PROSTATE_DTA_REVIEW.html` | 280,372 | Multiparametric MRI (PI-RADS) |
| `GENEXPERT_ULTRA_TB_DTA_REVIEW.html` | 296,762 | GeneXpert MTB/RIF Ultra for TB |
| `DDIMER_PE_DTA_REVIEW.html` | 301,251 | D-dimer for PE rule-out |

**Two are squarely in the cardiology/ID remit this night was about** — hs-cTn for NSTEMI, and
GeneXpert for TB. **Recommendation: these six are the audit target, not the 795.**

---

## B. Tools mislabelled only by convention (5) — naming question, no claims

| page | what it is |
|---|---|
| `AutoGRADE.html` | GRADE certainty assessor. No numeric results at all. |
| `AutoManuscript.html` | Manuscript generator. |
| `TrialRadar.html` | Trial surveillance tool. No numeric results. |
| `LivingMeta.html` | The living-meta engine itself (949 KB). |
| `MetaExtract.html` | Effect-estimate extractor. |

None is named `*_REVIEW.html`, so the misleading-URL problem does **not** apply. The only
question is whether a reader arriving cold understands these are tools. I'd leave them.

---

## C. Site infrastructure (10) — not reviews, but one carries claims

| page | what it is |
|---|---|
| `index.html` | Portfolio index — **and it surfaces 106 formatted effect estimates** |
| `META_DASHBOARD.html`, `dashboard.html` | Portfolio dashboards, no results of their own |
| `NMA_INDEX.html` | NMA portfolio index |
| `portfolio_pools.html` (575 KB) | Pool listing, carries CI pairs |
| `audit_table.html` (893 KB) | Data-integrity index |
| `what_changed.html`, `withdrawn_audit_rows.html` | Integrity/change logs |
| `EVIDENCE_GAPS.html` | Gap listing (no `<title>`) |
| `cardiology_mortality_atlas.html` | Atlas, carries CI pairs |

**`index.html` is the one to look at.** It is the site's front door and it republishes 106
effect estimates. If any of those are drawn from pages we have since corrected, the index is
a fourth surface that can go stale — the same class as the visual abstract, one level up.
I have not checked it; flagging rather than asserting.

---

## D. Dose-response reviews (8) — study counts but no interval pairs found

`BRODALUMAB_PSORIASIS_AMAGINE`, `ERENUMAB_MIGRAINE_PHASE3`, `FINERENONE_ARTS_DN`,
`SEMAGLUTIDE_T2D_SUSTAIN`, `SGLT2I`, `TIRZEPATIDE_OBESITY_SURMOUNT`,
`TIRZEPATIDE_T2D_SURPASS` (all `_DOSE_RESP_REVIEW.html`), plus `ALCOHOL_BC_DOSE_RESP_REVIEW.html`
and the `dose_response_landing.html` pack page.

27–39 KB each. They report study counts but my regexes found no interval pairs, which for a
dose-response slope may be correct rather than empty. **I cannot tell these apart from
outside; one human look at one page settles all eight.**

---

## E. Single-topic reviews carrying interval pairs (16)

`AVACOPAN_ANCA`, `ELRANATAMAB_MM`, `MARALIXIBAT_PFIC`, `MIRVETUXIMAB_OVARIAN`,
`SELPERCATINIB_RET`, `SUTIMLIMAB_CAD`, `TEZEPELUMAB_ASTHMA`, `ZURANOLONE_PPD_MDD`,
`PREDICTION_MODEL_KFRE`, `PROGNOSTIC_HSTN_PAD`, `MALARIA_VACCINES_SSOT`, and the "(broader)"
variants `AVACINCAPTAD_GA_AUTO_2`, `LIGELIZUMAB_URTICARIA_AUTO_2`, `MOMELOTINIB_MF_AUTO_2`,
`RELUGOLIX_FIBROIDS_AUTO_2`, `VOXELOTOR_SCD_AUTO_2`.

20–95 KB. Titled "audit-first" or "(audited)". Mostly outside cardiology/ID.
`PROGNOSTIC_HSTN_PAD` and `PREDICTION_MODEL_KFRE` are cardiology-adjacent.

## F. Single-topic reviews with no interval pairs found (8)

`DACOMITINIB_LUNG_AUTO_2`, `NEMOLIZUMAB_PRURIGO`, `ODEVIXIBAT_PFIC`, `OLUTASIDENIB_AML`,
`PACRITINIB_MF_AUTO_2`, `PEMBROLIZUMAB_KIDNEY_ADJ_AUTO_2`, `TOFERSEN_SOD1_ALS`,
`VAMOROLONE_DMD`. Same shape as D — cannot distinguish sparse from empty from outside.

---

## G. Already honestly labelled (3) — no action

| page | why no action |
|---|---|
| `auto-gallery.html` | Self-describes: *"Automated, unvalidated outputs. These pages were produced by the automated pipeline and pool fewer than two…"* |
| `mission_open_syntheses.html` | Malaria & HIV open-sourced syntheses landing |
| `tb_tpt_open_synthesis.html` | TB preventive therapy open synthesis |

`COVID19_VACCINES_SSOT.html` (15 KB) is an SSOT summary page for a topic we already hold.

---

## What I would put to Mahmood, in order

1. **The six DTA reviews are the real audit gap.** Six pages, ~1.7 MB of genuine reader-facing
   claims, zero instrument coverage. Two are cardiology/ID.
2. **`index.html` republishes 106 estimates** and is a staleness surface nobody has checked.
3. **The naming decision on the 744 app shells** — a tool a reader is invited to run, served
   under a URL that says review.
4. **D and F (16 pages) need one human look each**, and one look probably settles each group.
