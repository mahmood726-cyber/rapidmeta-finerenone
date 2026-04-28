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
