# Python scipy Reproducibility Check (externally-benchmarked apps)

**Date:** 2026-04-20
**Scope:** 11 externally-benchmarked apps (benchmark_type = external_IPD or external_aggregate)
**Check:** Independent DL random-effects pool on log-scale (k>=3) or FE log-scale (k=2), computed with numpy on the app's own per-trial HR/OR/RR or MD+SE from the realData block. Must match the app's displayed pool within 3% relative difference.

- **MATCH (<3% rel):**  3
- **CLOSE (<10% rel):** 3
- **DIFFER (>=10%):**   1

| App | Status | scipy pool | App pool | Rel diff |
|---|---|---|---|---|
| BEMPEDOIC_ACID_REVIEW.html | NO-TRIALS | None | 0.87 | None |
| CANGRELOR_PCI_REVIEW.html | DIFFER | 0.894 | 0.81 | 0.1039 |
| DOAC_AF_REVIEW.html | MATCH | 0.789 | 0.81 | 0.0264 |
| FINERENONE_REVIEW.html | NO-TRIALS | None | 0.86 | None |
| GLP1_CVOT_REVIEW.html | MATCH | 0.863 | 0.88 | 0.0198 |
| INCLISIRAN_REVIEW.html | CLOSE | -47.441 | -50.7 | 0.0643 |
| JAK_UC_REVIEW.html | MATCH | 3.294 | 3.2 | 0.0294 |
| PCSK9_REVIEW.html | NO-TRIALS | None | 0.85 | None |
| SGLT2_CKD_REVIEW.html | NO-TRIALS | None | 0.68 | None |
| SGLT2_HF_REVIEW.html | CLOSE | 0.745 | 0.77 | 0.0328 |
| TAVR_LOWRISK_REVIEW.html | CLOSE | 0.644 | 0.69 | 0.067 |
