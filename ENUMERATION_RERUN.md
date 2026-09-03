# Re-running Path-A: what it resurrects, and what the raised cap actually buys

MEASURED, AACT `2026-08-30`, gate D decided against live PubMed
(198 PMIDs requested, 4 batches, 0 failed). Reproduce:
`AACT_DIR=<snapshot> python scripts/rerun_path_a_named_sample_2026_09_04.py`

## The two goods, which are not the same good

| | |
|---|---|
| NOT_VIABLE topics re-audited | **14** |
| VIABLE on the CURRENT head-8 (old cap, new matcher) | **5** |
| VIABLE on the FULL POOL (raised cap) | **5** |
| VIABLE **only** because the cap was raised | **0** |

Trials contributed by the 5 resurrected topics, and the four numbers are four different
things — none of them is "delivered 0":

| what | n |
|---|---:|
| passing trials **as production recorded them** (`n_pass_all`) | **3** |
| the delivered 8 **re-audited against today's data** | **4** |
| the CURRENT ranked head-8 (old cap, new matcher) | **15** |
| the FULL POOL (raised cap) | **44** |

The 3 -> 15 step is the matcher. The 15 -> 44 step is the bound. Only `VENETOCLAX_CLL_AUTO`
was delivered at 0, and its re-audited delivered-8 is still 0 — the eight it was judged on
do not pass today either, which is what makes the selector and not the registry the cause.

> **THE BOUND ADDS NO TOPICS. IT ADDS k INSIDE TOPICS THAT RE-RUNNING ALREADY REVIVES.**

## Per topic, all 14 named

`ovl` = overlap between the 8 the pipeline delivered and the current ranked head-8.
`del` = how many of the DELIVERED 8 pass when re-audited against today's data — the
control that separates *the selector changed* from *the registry changed*.

| topic | pool | ovl | del | head-8 | pool | verdict head-8 -> pool |
|---|---:|---:|---:|---:|---:|---|
| `VENETOCLAX_CLL_AUTO` | 460 | 0 | 0 | 5 | 26 | VIABLE -> VIABLE |
| `PALONOSETRON_CINV_AUTO` | 59 | 0 | 1 | 3 | 6 | VIABLE -> VIABLE |
| `LIPOSOMAL_BUPIVACAINE_AUTO` | 48 | 1 | 0 | 3 | 8 | VIABLE -> VIABLE |
| `PEGVISOMANT_ACROMEGALY_AUTO` | 14 | 4 | 1 | 0 | 1 | NOT_VIABLE -> NOT_VIABLE |
| `BEPIROVIRSEN_HBV_AUTO` | 10 | 7 | 2 | 2 | 2 | VIABLE -> VIABLE |
| `AVACINCAPTAD_GA_AUTO` | 8 | 6 | 1 | 2 | 2 | VIABLE -> VIABLE |
| `ICOSAPENT_CVD_AUTO` | 4 | 4 | 1 | 1 | 1 | NOT_VIABLE -> NOT_VIABLE |
| `TASIMELTEON_AUTO` | 4 | 4 | 0 | 0 | 0 | NOT_VIABLE -> NOT_VIABLE |
| `DALBAVANCIN_ABSSSI_AUTO` | 3 | 2 | 0 | 1 | 1 | NOT_VIABLE -> NOT_VIABLE |
| `ENSIFENTRINE_COPD_AUTO` | 3 | 3 | 0 | 0 | 0 | NOT_VIABLE -> NOT_VIABLE |
| `FOSTAMATINIB_ITP_AUTO` | 3 | 3 | 0 | 0 | 0 | NOT_VIABLE -> NOT_VIABLE |
| `DEXLANSOPRAZOLE_GERD_AUTO` | 2 | 2 | 0 | 0 | 0 | NOT_VIABLE -> NOT_VIABLE |
| `FLUTICASONE_UMECLIDINIUM_VILANTEROL_AUTO` | 1 | 1 | 0 | 0 | 0 | NOT_VIABLE -> NOT_VIABLE |
| `OCTREOTIDE_DUMP_AUTO` | 1 | 1 | 0 | 0 | 0 | NOT_VIABLE -> NOT_VIABLE |

## Corrections carried in this file

- An earlier offline pass reported **7 resurrections, 1 from the cap**. It could not
  decide gate D and said so — an UPPER BOUND. With abstracts fetched it is **5 and 0**.
- Zero delivered-vs-head overlap is a **VENETOCLAX and PALONOSETRON property, 2 of 14**,
  not a corpus-wide one.
- `add_topic_autodiscover.py:5285`: the old matcher returned *"the FIRST `max_per_topic`
  matches in arbitrary interventions.txt file order"*. For VENETOCLAX those eight were
  recent registrations with no posted results; all eight failed gate E and the topic was
  written off. **The cap cost candidates; the arbitrary file-order selection cost topics.**
- Staleness ruled out independently: the VENETOCLAX head-8 carries overall baseline rows
  in the April snapshot (7 of 8) and the August one (8 of 8).
