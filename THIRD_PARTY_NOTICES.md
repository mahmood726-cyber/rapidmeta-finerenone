# Third-Party Notices

The RapidMeta portfolio (77 pairwise + 4 NMA apps + tooling) depends on and redistributes outputs from several third-party projects. This notice documents each with license + attribution.

Main project license: **MIT** (see `LICENSE`).

---

## R packages (statistical computing)

| Package | Version | License | Role |
|---|---|---|---|
| **netmeta** | 3.2.0 | **GPL (≥ 2)** | Frequentist network meta-analysis engine (authoritative) |
| **meta** | 8.2.1 | GPL (≥ 2) | Pairwise meta-analysis dependency of netmeta |
| **MASS** | 7.3-65 | GPL-2/3 | `mvrnorm` for multivariate normal MC sampling |
| **jsonlite** | 2.0.0 | MIT | JSON I/O |
| **metafor** | (WebR fallback) | GPL (≥ 2) | Edge-level validation in-browser fallback |

**GPL implications:** we redistribute *outputs* of netmeta (the printed HRs, τ², I², etc.) in our `*_netmeta_results.*` artifacts. Under GPL-2 this is permitted with attribution. The `*.R` scripts in `nma/validation/` are the source that produced those outputs; running them on any R 4.5.x install with netmeta 3.2.0 will byte-reproduce the artifacts. We do **not** modify or redistribute the netmeta/meta source code.

Citations:
- Rücker G, Krahn U, König J, Efthimiou O, Davies A, Papakonstantinou T, Schwarzer G (2025). **netmeta: Network Meta-Analysis using Frequentist Methods.** R package version 3.2.0. https://CRAN.R-project.org/package=netmeta
- Balduzzi S, Rücker G, Schwarzer G (2019). **How to perform a meta-analysis with R: a practical tutorial.** Evidence-Based Mental Health 22:153–160.

## JavaScript / WebAssembly

| Package | Version | License | Role |
|---|---|---|---|
| **Plotly.js** (basic) | 2.35.2 | MIT | Network plot + forest + funnel rendering (inlined in NMA apps) |
| **WebR** | latest | MIT | In-browser R runtime (for "Run netmeta in browser" button) |
| **coi-serviceworker** (pattern) | — | MIT | COOP/COEP injection SW; pattern origin https://github.com/gzuidhof/coi-serviceworker |
| **living-meta NMA library** | 2.0.0 | MIT | JS NMA engine (draft; see peer-review-response.md for known limitations) |

## Python tooling

| Package | Version | License | Role |
|---|---|---|---|
| **Playwright** | — | Apache 2.0 | Headless-Chromium smoke tests |

## Canonical dataset sources (trial-level, used for RCT effect extraction)

All trial-level data are from peer-reviewed publications + ClinicalTrials.gov registry. CT.gov data is in the public domain. Publisher-copyright abstracts are cited with source URLs in each app's `evidence[]` and `sourceUrl` fields.

Named canonical datasets cited in peer-review:
- Hasselblad 1998 smoking cessation (netmeta example data) — public domain
- Lu–Ades 2004 thrombolytics — public domain

## Methodology references (non-code)

- PRISMA-NMA 2020: Hutton B, Salanti G, Caldwell DM, et al. Ann Intern Med 2015;162:777–784
- CINeMA: Papakonstantinou T et al. F1000Res 2020;9:39
- Lu G, Ades AE. J Am Stat Assoc 2004;99:287–300
- White IR et al. Res Synth Methods 2012;3:111–125
- Higgins JPT et al. Stats Med 2012;31:3805–3820
- Dias S et al. Stats Med 2010;29:932–944

## Attribution requirements for downstream users

If you fork, redistribute, or build derivatives of this repository:
1. Preserve the MIT `LICENSE` and this `THIRD_PARTY_NOTICES.md`
2. Preserve the GPL-2 attribution for netmeta/meta in any redistributed R output
3. Cite netmeta + meta in any publication that uses the `*_netmeta_results.*` outputs

---

Last updated: 2026-04-21
