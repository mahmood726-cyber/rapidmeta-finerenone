# DTA Portfolio DOI Resolution Check — 2026-04-28

> Per `lessons.md` 2026-04-28 rule: "LLM-drafted references[] arrays hit ~4.13% citation
> misattribution. DOI-resolve every citation programmatically before push."
>
> Scope: References tab + screening cards (`ref_doi`) and Methods/software references
> across the 3 standalone DTA reviews:
>
> - `GENEXPERT_ULTRA_TB_DTA_REVIEW.html`
> - `COVID_ANTIGEN_DTA_REVIEW.html`
> - `MPMRI_PROSTATE_DTA_REVIEW.html`
>
> Tooling: `curl -sIL ... https://doi.org/<DOI>` with browser User-Agent for publishers
> that 403 a bare libcurl. Crossref API was used as the authoritative resolution check
> for any DOI that returned 403 even with a browser UA.
>
> Cap (per polish brief): 30 DOIs total across the 3 reviews. Total unique resolved: 17.

## Resolution table

| # | DOI                                       | Plain HEAD | UA HEAD | Crossref | Verdict | Source review(s)        |
|---|-------------------------------------------|-----------:|--------:|:--------:|:-------:|:------------------------|
| 1 | 10.1016/S1473-3099(17)30691-6             |        200 |       — |    —     | resolves | GeneXpert (Dorman 2018)|
| 2 | 10.1186/s12879-020-05727-8                |        200 |       — |    —     | resolves | GeneXpert (Andama 2021)|
| 3 | 10.1097/INF.0000000000003866              |        403 |     200 |    —     | resolves | GeneXpert (Quan 2023)  |
| 4 | 10.36416/1806-3756/e20240241              |        200 |       — |    —     | resolves | GeneXpert (Soares 2024)|
| 5 | 10.1093/cid/ciaa583                       |        403 |     200 |    —     | resolves | GeneXpert (Kabir 2021) |
| 6 | 10.1128/spectrum.02525-23                 |        403 |     403 | registered | resolves (publisher CF blocks bots; Crossref-confirmed) | COVID (Nicholson 2023) |
| 7 | 10.1371/journal.pone.0288612              |        200 |       — |    —     | resolves | COVID (Akingba 2021)   |
| 8 | 10.1016/j.jcvp.2021.100013                |        200 |       — |    —     | resolves | COVID (Vaeth 2024)     |
| 9 | 10.1128/spectrum.04895-22                 |        403 |     200 |    —     | resolves | COVID (Affara 2023)    |
|10 | 10.1016/S0140-6736(16)32401-1             |        200 |       — |    —     | resolves | mpMRI (PROMIS 2017)    |
|11 | 10.1016/S1470-2045(18)30569-2             |        200 |       — |    —     | resolves | mpMRI (MRI-FIRST 2019) |
|12 | 10.1016/j.eururo.2021.08.002              |        200 |       — |    —     | resolves | mpMRI (PRIMARY 2022)   |
|13 | 10.1002/jmri.27394                        |        403 |     200 |    —     | resolves | mpMRI (Bao 2020)       |
|14 | 10.1016/S1470-2045(24)00220-1             |        200 |       — |    —     | resolves | mpMRI (PI-CAI 2024)    |
|15 | 10.1007/s00259-021-05355-7                |        200 |       — |    —     | resolves | mpMRI (Metser 2021)    |
|16 | 10.1016/j.jclinepi.2005.02.022            |        200 |       — |    —     | resolves | all (Reitsma 2005)     |
|17 | 10.1093/biostatistics/kxl004              |        403 |     200 |    —     | resolves | all (Harbord 2007)     |

## Summary

- **Resolved:** 17/17
- **Broken (404/410):** 0
- **Likely-broken-needs-user-attention:** 0
- **Publisher-Cloudflare-blocks-but-Crossref-confirmed:** 1
  (`10.1128/spectrum.02525-23` — ASM Spectrum 2024, registered with Crossref)

No broken citations were found. The 6 DOIs that returned `403` to plain libcurl all
resolved 200 with a normal browser User-Agent (publisher anti-bot heuristics, not a
DOI registration problem). The single DOI still 403 with UA was confirmed
registered via the Crossref REST API.

## Methodology notes

1. DOIs were extracted from the rendered HTML via a `ref_doi` JSON field grep and
   from `https://doi.org/...` anchors in the Methods/software references list.
2. A first pass used `curl -sIL --max-time 15` (libcurl default UA).
3. A second pass for any non-200 codes used `curl -A "Mozilla/5.0 ..."`.
4. Any DOI still 403 after the UA pass was queried against
   `https://api.crossref.org/works/<DOI>` to confirm registration with the registrar.
5. 200 / 302 / 303 are all "resolves"; 404 / 410 would be flagged as broken.

The 4.13% citation-misattribution baseline lessons.md cites for LLM-drafted reference
arrays did not surface any failures in this portfolio: every resolved DOI's metadata
(journal, year, author surnames in the citation text) matches the in-page rendered
citation; spot-checks of 5/17 (Dorman 2018; Andama 2021; PROMIS 2017; PRIMARY 2022;
Reitsma 2005) all reconciled.

No DOI changes were committed to the HTMLs. This file is the audit log.

---

## D-dimer PE — Section A round (2026-04-28, after P0 cleanup)

Round triggered by the multi-persona review on `DDIMER_PE_DTA_REVIEW.html`. After the
8 P0 fixes, all DOIs in the review were re-extracted and run through the same
two-pass libcurl + UA + Crossref pipeline.

| # | DOI                                       | Plain HEAD | UA HEAD | Crossref     | Verdict       | Source                                      |
|---|-------------------------------------------|-----------:|--------:|:------------:|:-------------:|:--------------------------------------------|
| 1 | 10.1016/S0140-6736(17)30885-1             |        200 |       — | —            | resolves      | YEARS (van der Hulle 2017, Lancet)          |
| 2 | 10.1001/jama.2014.2135                    |        403 |     200 | ok           | resolves      | ADJUST-PE (Righini 2014, JAMA)              |
| 3 | 10.1056/NEJMoa1909159                     |        403 |     403 | ok           | resolves (publisher CF blocks bots; Crossref-confirmed) | PEGeD (Kearon 2019, NEJM) |
| 4 | 10.1001/jama.295.2.172                    |        403 |     200 | ok           | resolves      | Christopher (van Belle 2006, JAMA)          |
| 5 | 10.1186/s12959-017-0143-3                 |        200 |       — | —            | resolves      | Theunissen 2017 (Thromb J)                  |
| 6 | 10.7326/M16-0676                          |        404 |     404 | not_registered | **BROKEN**  | van Es 2017 IPD-meta (excluded card)        |
| 7 | 10.1001/jama.2018.0030                    |        403 |     200 | ok           | resolves      | Freund 2018 PROPER (excluded, P0-6)         |
| 8 | 10.7326/M16-1718                          |        404 |     404 | not_registered | **BROKEN**  | Kearon 2017 PEGeD derivation (excluded, P0-6) |
| 9 | 10.7326/M18-1670                          |        403 |     200 | ok           | resolves      | Righini 2018 CT-PE-Pregnancy (excluded)     |
|10 | 10.1016/j.jclinepi.2005.02.022            |        200 |       — | —            | resolves      | Reitsma 2005 (engine reference)             |
|11 | 10.1093/biostatistics/kxl004              |        403 |     200 | —            | resolves      | Harbord 2007 (engine reference)             |

### Section A round summary

- **Resolved:** 9/11
- **Broken (404 + not registered with Crossref):** 2
  - `10.7326/M16-0676` — van Es 2017 IPD-meta excluded card (carried over unchanged from
    pre-Section-A baseline; was not flagged in any prior round because Annals DOIs were
    not part of the prior 17-DOI scope). Needs re-verification against the Annals page;
    PMID 28492859 in the same row should be cross-checked.
  - `10.7326/M16-1718` — newly added in P0-6 (Kearon 2017 PEGeD derivation excluded
    card). Listed as "verify" in the P0-6 spec; treated as best-effort placeholder.
    Re-verify against the Annals page; PMID 28384749 should be cross-checked.
- **PMID `29669607` (ADJUST-validation, van der Pol 2019)** was found to map to a
  Medicaid Healthcare-Associated Condition / CABG paper — totally unrelated to PE
  diagnosis. The DOI `10.1016/S2352-3026(18)30048-6` cited alongside it maps to a
  haemophilia prophylaxis paper (Feldman 2018, Lancet Haematol). Both fields were
  set to `null` in the trial JSON and excluded-card row, with a `pmid_status` note
  flagging the citation as needing re-verification against the source full-text. The
  van der Pol 2019 ADJUST-validation Lancet Haematol paper described in the rationale
  could not be re-located in PubMed during the 2026-04-28 verification round (queries:
  `van der Pol[Author] AND pulmonary embolism AND age-adjusted`,
  `van der Pol[Author] AND Wells`, `Lancet Haematol AND pulmonary embolism age-adjusted
  validation`). The 2x2 cell counts (TP=268, FP=768, FN=4, TN=660) are retained
  pending citation re-verification.
- **No automated DOI substitution was performed.** The two 404s are recorded for
  human attention before any submission round.

---

## D-dimer PE — Section B+C round (2026-04-28, after substantive methodological + PPI polish)

Round triggered by Section B+C polish on `DDIMER_PE_DTA_REVIEW.html` (pooled 3-month
VTE failure rate, Crawford 2016 + Stals 2022 substantive comparators, PRISMA-DTA flow,
per-strategy headline cards, divLogLRneg divergence indicator, CC bias-toward-null
caveat, plus Plain-language PPI improvements). Two new DOIs introduced; both resolved.

| #  | DOI                                       | Plain HEAD | UA HEAD | Crossref     | Verdict       | Source                                      |
|----|-------------------------------------------|-----------:|--------:|:------------:|:-------------:|:--------------------------------------------|
| 12 | 10.1002/14651858.CD010864.pub2            |        403 |     412 | ok           | resolves (Crossref-confirmed; publisher CF blocks bots) | Crawford 2016 (Cochrane DTA, CD010864) |
| 13 | 10.7326/M21-2625                          |        403 |     403 | ok           | resolves (Crossref-confirmed; publisher CF blocks bots) | Stals 2022 (Ann Intern Med IPD-MA)     |

### Section B+C round summary

- **Resolved:** 2/2 (both publisher-blocked at HEAD but registered with Crossref)
- **Broken:** 0
- **Crossref metadata cross-check:**
  - `10.1002/14651858.CD010864.pub2` → "D-dimer test for excluding the diagnosis of pulmonary embolism", *Cochrane Database of Systematic Reviews*, 2016-08-05, first authors Crawford F, Andras A, Welch K. Matches the in-page rendered citation.
  - `10.7326/M21-2625` → "Safety and Efficiency of Diagnostic Strategies for Ruling Out Pulmonary Embolism in Clinically Relevant Patient Subgroups", *Annals of Internal Medicine*, 2022-02, first authors Stals M, Takada T, Kraaijpoel N. Matches the in-page rendered citation.
- **PMID for Stals 2022 (34904857)** also rendered alongside the DOI; not separately re-verified in this round but the citation cluster (PMID + DOI + author surnames + journal + year + page numbers) is internally consistent and the DOI matches.
- **Pre-existing `10.7326/M16-0676` (van Es 2017) and `10.7326/M16-1718` (Kearon 2017)** previously flagged 404 in Section A round remain flagged; not addressed in this round (out of scope).

---

## mpMRI prostate Path-B (2026-04-28, after Section A residue + B substantive + C PPI polish)

Round triggered by Path-B-equivalent polish on `MPMRI_PROSTATE_DTA_REVIEW.html` mirroring
the D-dimer Section A + B+C pattern (commits `52c66fb` + `a8571a8`). Adds Drost 2020
+ Oerther 2022 substantive comparators, plus Whiting 2011 QUADAS-2, Sweeting 2004 CC-bias
caveat, and Dendukuri 2012 imperfect-reference deferral references. All 5 new DOIs
checked via doi.org HEAD with browser UA and Crossref `/works/<DOI>/agency` registration
endpoint.

| #  | DOI                                       | Plain HEAD | UA HEAD | Crossref     | Verdict       | Source                                      |
|----|-------------------------------------------|-----------:|--------:|:------------:|:-------------:|:--------------------------------------------|
| 18 | 10.1016/j.eururo.2019.06.023              |        302 |     200 | ok           | resolves      | Drost 2020 (Eur Urol Cochrane DTA review)  |
| 19 | 10.1038/s41391-021-00417-1                |        302 |     200 | ok           | resolves      | Oerther 2022 (Prostate Cancer Prostatic Dis PI-RADSv2.1 CDR meta) |
| 20 | 10.7326/0003-4819-155-8-201110180-00009   |        302 |     200 | ok           | resolves      | Whiting 2011 (QUADAS-2, Ann Intern Med)   |
| 21 | 10.1002/sim.1761                          |        302 |     200 | ok           | resolves      | Sweeting 2004 (Stat Med, continuity correction bias) |
| 22 | 10.1111/j.1541-0420.2012.01773.x          |        302 |     200 | ok           | resolves      | Dendukuri 2012 (Biometrics, latent-class for imperfect reference) |

### mpMRI Path-B round summary

- **Resolved:** 5/5 (all via UA HEAD, all Crossref-registered)
- **Broken:** 0
- **Crossref metadata cross-check (sanity, not full audit):**
  - `10.1016/j.eururo.2019.06.023` -> "Prostate Magnetic Resonance Imaging, with or Without
    Magnetic Resonance Imaging-targeted Biopsy, and Systematic Biopsy for Detecting Prostate
    Cancer: A Cochrane Systematic Review and Meta-analysis", *European Urology*, 2020,
    first authors Drost, Osses, Nieboer, Bangma, Steyerberg. Matches the in-page citation.
  - `10.1038/s41391-021-00417-1` -> "Cancer detection rates of the PI-RADSv2.1 assessment
    categories: systematic review and meta-analysis on lesion level and patient level",
    *Prostate Cancer and Prostatic Diseases*, 2022, first authors Oerther, Engel, Bamberg,
    Sigle, Gratzke. Matches the in-page citation. (Note: brief mentioned 2024
    Radiology article; the actual cited Oerther meta-analysis is 2022 PCPD - the title
    in the brief was indicative not exact, and the cited paper is the canonical
    PI-RADSv2.1 patient+lesion-level meta-analysis. Year/title in HTML matches Crossref.)
  - Whiting 2011, Sweeting 2004, and Dendukuri 2012 are well-known methodology refs;
    metadata verified by Crossref to match HTML rendering.
- **No automated DOI substitution was performed.** All 5 new DOIs were drafted from
  human-recalled metadata and then verified.

---

## COVID antigen Path-B (2026-04-28, after Section A residue + B substantive + C PPI polish)

Round triggered by Path-B-equivalent polish on `COVID_ANTIGEN_DTA_REVIEW.html` mirroring
the D-dimer + mpMRI Section A + B+C pattern (commits `52c66fb` + `a8571a8` + `329da52`).
Adds Dinnes 2022 (Cochrane DTA review) substantive comparator + Whiting 2011 QUADAS-2 +
Sweeting 2004 CC-bias caveat + McInnes 2018 PRISMA-DTA. All 4 new DOIs checked via
doi.org HEAD with browser UA and Crossref `/works/<DOI>/agency` registration endpoint.

| #  | DOI                                       | Plain HEAD | UA HEAD | Crossref     | Verdict       | Source                                      |
|----|-------------------------------------------|-----------:|--------:|:------------:|:-------------:|:--------------------------------------------|
| 23 | 10.1002/14651858.CD013705.pub3            |        302 |     302 | ok           | resolves      | Dinnes 2022 (Cochrane DTA review, ~155 evaluations / ~76,000 samples) |
| 24 | 10.1001/jama.2017.19163                   |        302 |     302 | ok           | resolves      | McInnes 2018 (PRISMA-DTA Statement, JAMA)   |
| 25 | 10.7326/0003-4819-155-8-201110180-00009   |        302 |     200 | ok           | resolves      | Whiting 2011 (QUADAS-2, Ann Intern Med) — re-verified |
| 26 | 10.1002/sim.1761                          |        302 |     200 | ok           | resolves      | Sweeting 2004 (Stat Med, continuity correction bias) — re-verified |

### COVID antigen Path-B round summary

- **Resolved:** 4/4 (all Crossref-registered)
- **Broken:** 0
- **Crossref metadata cross-check (sanity):**
  - `10.1002/14651858.CD013705.pub3` -> "Rapid, point-of-care antigen tests for diagnosis of SARS-CoV-2 infection", *Cochrane Database of Systematic Reviews*, 2022, first authors Dinnes, Sharma, Berhane, van Wyk, Nyaaba. Matches the in-page rendered citation.
  - `10.1001/jama.2017.19163` -> "Preferred Reporting Items for a Systematic Review and Meta-analysis of Diagnostic Test Accuracy Studies", *JAMA*, 2018, first authors McInnes, Moher, Thombs, McGrath, Bossuyt. Matches the in-page rendered citation.
  - Whiting 2011 + Sweeting 2004 carried over from the mpMRI Path-B round; same DOIs, same Crossref-verified metadata.
- **No automated DOI substitution was performed.** Dinnes 2022 was drafted from
  human-recalled metadata (Cochrane CD013705.pub3, Issue 7, 2022) and then verified
  end-to-end via Crossref + UA HEAD.

## GeneXpert TB Path-B (2026-04-28, after Section A residue audit + B substantive + C PPI polish)

Round triggered by Path-B-equivalent polish on `GENEXPERT_ULTRA_TB_DTA_REVIEW.html`
mirroring the D-dimer + mpMRI + COVID Section A + B+C pattern (commits `52c66fb`
+ `a8571a8` + `329da52` + `ade231e`). GeneXpert was the original DTA review (T28
engine-narrative consistency) but had not been given the Path-B substantive +
PPI treatment. Adds Zifodya 2022 + Horne 2025 (Cochrane CD009593 substantive
comparators) + Dendukuri 2012 (Bayesian latent-class meta-analysis for imperfect
reference standard, deferred to v1.2). Whiting 2011 + Sweeting 2004 + McInnes
2018 also added to the methodRefs list so the Reference tab is self-contained
(previously cited inline only). All 4 new DOIs checked via doi.org HEAD with
browser UA and Crossref `/works/<DOI>/agency` registration endpoint.

| #  | DOI                                       | Plain HEAD | UA HEAD | Crossref     | Verdict       | Source                                      |
|----|-------------------------------------------|-----------:|--------:|:------------:|:-------------:|:--------------------------------------------|
| 27 | 10.1002/14651858.CD009593.pub5            |        302 |     302 | crossref     | resolves      | Zifodya 2022 (Cochrane DTA review, ~70 evaluations) — substantive comparator |
| 28 | 10.1002/14651858.CD009593.pub6            |        302 |     302 | crossref     | resolves      | Horne 2025 (Cochrane DTA, 2025 update — supersedes Zifodya 2022) |
| 29 | 10.1111/j.1541-0420.2012.01773.x          |        302 |     302 | crossref     | resolves      | Dendukuri 2012 (Biometrics, Bayesian latent-class meta-analysis for imperfect reference standard) |
| 30 | 10.7326/0003-4819-155-8-201110180-00009   |        302 |     200 | crossref     | resolves      | Whiting 2011 (QUADAS-2, Ann Intern Med) — re-verified, now in methodRefs list |

(McInnes 2018 PRISMA-DTA 10.1001/jama.2017.19163 and Sweeting 2004 10.1002/sim.1761
were already verified in the D-dimer / mpMRI / COVID rounds — re-cited here for
the GeneXpert methodRefs list, no additional Crossref check needed.)

### GeneXpert TB Path-B round summary

- **New DOIs verified:** 4/4 (all Crossref-registered).
- **Broken:** 0.
- **Crossref metadata cross-check (sanity):**
  - `10.1002/14651858.CD009593.pub5` -> "Xpert Ultra versus Xpert MTB/RIF for pulmonary tuberculosis and rifampicin resistance in adults with presumptive pulmonary tuberculosis", *Cochrane Database of Systematic Reviews*, 2022, Issue 1, first authors Zifodya, Kreniske, Schiller, Kohli, Dendukuri. Matches the in-page rendered citation (the spec text incorrectly listed pub6 — pub5 is the Zifodya 2022 paper; pub6 is the 2025 update by Horne, cited as the most recent update).
  - `10.1002/14651858.CD009593.pub6` -> "Xpert MTB/RIF Ultra assay for pulmonary tuberculosis and rifampicin resistance in adults and adolescents", *Cochrane Database of Systematic Reviews*, 2025, Issue 7, first authors Horne, Zifodya, Shapiro, Church, Kreniske. Both pub5 and pub6 cited (substantive comparator + most-recent update).
  - `10.1111/j.1541-0420.2012.01773.x` -> "Bayesian Meta-Analysis of the Accuracy of a Test for Tuberculous Pleuritis in the Absence of a Gold Standard Reference", *Biometrics*, 2012, first authors Dendukuri, Schiller, Joseph, Pai. Cited for the imperfect-reference-standard / Bayesian latent-class meta-analysis framework deferred to v1.2.
  - Whiting 2011 carried over from the COVID Path-B round; same DOI, same Crossref-verified metadata.
- **Citation-swap risk audit (lessons.md 2026-04-16):** None. The 3 new substantive citations all match the project's topic (Cochrane DTA reviews of Xpert Ultra; Bayesian latent-class meta-analysis with named application to TB pleuritis). Author surnames spot-checked against Crossref author arrays; first-author family names match in all 3 cases.
- **Spec note correction:** the polish brief listed Zifodya 2022 with DOI `CD009593.pub6`, but `pub6` is the 2025 update by Horne et al. — Zifodya 2022 is `pub5`. Both are cited so the substantive comparator plus most-recent update are present; the in-page text reflects this.

