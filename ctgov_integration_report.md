# CT.gov Mining → Atlas Integration Report

**Discrepancy threshold:** 5% relative HR deviation OR non-overlapping CIs

## Summary

- Trials mined: **116**
- HR sources: **43** from CT.gov analyses, **12** Peto-derived from event counts
- Atlas confirmations (within tolerance): **31**
- **Discrepancies flagged:** **1**
- **Atlas gaps filled by mining:** **0**
- **CT.gov trials unmapped to atlas classes:** **55**

## Discrepancies (require review)

| NCT | Class | Trial | Atlas HR | Mined HR | Δ% | CIs overlap | Source |
|---|---|---|---|---|---|---|---|
| NCT02937454 | IV iron (FCM/derisom | AFFIRM-AHF | 0.930 (0.78-1.1) | 0.990 (0.75-1.31) | 6.5% | ✓ | analyses |

## Unmapped trials (55)

CT.gov trials returned by search but not currently in any atlas pool. Review for possible inclusion as new pool members or new drug classes.

- With ACM data: **1**
- Without ACM data: **54**

### Unmapped trials with ACM data

| NCT | Title | ACM HR | Source |
|---|---|---|---|
| NCT04847557 | A Study of Tirzepatide (LY3298176) in Participants With Hear | 1.245 | analyses |

## Confirmations (31)

Atlas HR within tolerance of CT.gov-mined HR.

| NCT | Class | Trial | Atlas HR | Mined HR | Δ% | Source |
|---|---|---|---|---|---|---|
| NCT01920711 | ARNI (sacubitril/val | PARAGON-HF | 0.970 | 0.970 | 0.0% | analyses |
| NCT02924727 | ARNI (sacubitril/val | PARADISE-MI | 0.880 | 0.875 | 0.6% | analyses |
| NCT02993406 | ATP-citrate lyase in | CLEAR Outcomes | 1.000 | 1.030 | 3.0% | analyses |
| NCT02551094 | Anti-inflammatory | COLCOT | 0.980 | 0.982 | 0.2% | peto_logrank |
| NCT01206062 | BP control (<120 mmH | SPRINT | 0.730 | 0.730 | 0.0% | analyses |
| NCT02929329 | Cardiac myosin activ | GALACTIC-HF | 1.000 | 1.000 | 0.0% | analyses |
| NCT00911508 | Catheter ablation | CABANA | 0.850 | 0.849 | 0.2% | peto_logrank |
| NCT03036124 | GDMT pillars (mixed) | DAPA-HF | 0.830 | 0.830 | 0.0% | analyses |
| NCT01144338 | GLP-1 receptor agoni | EXSCEL | 0.860 | 0.860 | 0.0% | analyses |
| NCT01394952 | GLP-1 receptor agoni | REWIND | 0.900 | 0.900 | 0.0% | analyses |
| NCT02692716 | GLP-1 receptor agoni | PIONEER 6 | 0.510 | 0.510 | 0.0% | analyses |
| NCT03574597 | GLP-1 receptor agoni | SELECT | 0.810 | 0.811 | 0.1% | peto_logrank |
| NCT03914326 | GLP-1 receptor agoni | SOUL | 0.910 | 0.905 | 0.6% | peto_logrank |
| NCT00000620 | Intensive glycemic c | ACCORD | 1.190 | 1.190 | 0.0% | analyses |
| NCT01776424 | Low-dose Xa inhibito | COMPASS | 0.820 | 0.820 | 0.0% | analyses |
| NCT02540993 | MRA (non-steroidal) | FIDELIO-DKD | 0.895 | 0.895 | 0.0% | analyses |
| NCT02545049 | MRA (non-steroidal) | FIGARO-DKD | 0.890 | 0.890 | 0.0% | analyses |
| NCT04435626 | MRA (non-steroidal) | FINEARTS-HF | 0.930 | 0.927 | 0.3% | peto_logrank |
| NCT01492361 | Omega-3 (EPA) | REDUCE-IT | 0.870 | 0.870 | 0.0% | analyses |
| NCT02104817 | Omega-3 (EPA) | STRENGTH | 1.130 | 1.130 | 0.0% | analyses |
| NCT01663402 | PCSK9 mAb | ODYSSEY OUTCOMES | 0.850 | 0.848 | 0.2% | peto_logrank |
| NCT01730534 | SGLT2 inhibitor | DECLARE-TIMI 58 | 0.930 | 0.930 | 0.0% | analyses |
| NCT02065791 | SGLT2 inhibitor | CREDENCE | 0.830 | 0.830 | 0.0% | analyses |
| NCT03036150 | SGLT2 inhibitor | DAPA-CKD | 0.690 | 0.690 | 0.0% | analyses |
| NCT03057951 | SGLT2 inhibitor | EMPEROR-Preserved | 1.000 | 1.000 | 0.0% | analyses |
| NCT03057977 | SGLT2 inhibitor | EMPEROR-Reduced | 0.920 | 0.920 | 0.0% | analyses |
| NCT03594110 | SGLT2 inhibitor | EMPA-KIDNEY | 0.870 | 0.870 | 0.0% | analyses |
| NCT03619213 | SGLT2 inhibitor | DELIVER | 0.940 | 0.940 | 0.0% | analyses |
| NCT01994889 | TTR stabilizer/silen | ATTR-ACT | 0.700 | 0.698 | 0.3% | analyses |
| NCT02861534 | sGC stimulator | VICTORIA | 0.950 | 0.950 | 0.0% | analyses |
| NCT05093933 | sGC stimulator | VICTOR | 0.840 | 0.840 | 0.0% | analyses |
