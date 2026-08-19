# Reference list — composite-endpoint finding, F1000Research submission

**Resolved 2026-08-19. Every field below comes from a lookup and none from recall.**

- **Registration identifiers** — read from the SSOT objects that hold each trial, or from a
  ClinicalTrials.gov search performed today, then re-fetched from the registry.
- **Acronyms** — read back from each registration's own `identificationModule.acronym` and
  compared against the name used in the paper. Mismatches and absences are flagged below.
- **Candidate publications** — from each registration's `referencesModule`.
- **Author, year, journal, volume, issue, pages, DOI** — from PubMed.

*According to PubMed.* Bibliographic detail retrieved via the PubMed API on 2026-08-19.

> **Why the rule is absolute here.** *Identifiers from recall* is a defect class this project
> has hit repeatedly — most recently a PMID recorded as LoDoCo2 that is in fact EAST-AFNET 4, an
> atrial-fibrillation trial, while the same corpus cited that PMID correctly on two other pages
> (DEFECT-REGISTRY class 22). This list is a citation someone will check.

---

## Primary publications

| # | Trial | Registration | First author | Year | Journal | Vol(Issue):pages | PMID | DOI |
|---|---|---|---|---|---|---|---|---|
| 1 | AMPLIFY | NCT00643201 | Agnelli G | 2013 | N Engl J Med | 369(9):799–808 | 23808982 | 10.1056/NEJMoa1302507 |
| 2 | AMPLIFY-EXT | NCT00633893 | Agnelli G | 2012 | N Engl J Med | 368(8):699–708 | 23216615 | 10.1056/NEJMoa1207541 |
| 3 | ADOPT | NCT00457002 | Goldhaber SZ | 2011 | N Engl J Med | 365(23):2167–77 | 22077144 | 10.1056/NEJMoa1110899 |
| 4 | ADVANCE-1 | NCT00371683 | Lassen MR | 2009 | N Engl J Med | 361(6):594–604 | 19657123 | 10.1056/NEJMoa0810773 |
| 5 | ADVANCE-2 | NCT00452530 | Lassen MR | 2010 | Lancet | 375(9717):807–15 | 20206776 | 10.1016/S0140-6736(09)62125-5 |
| 6 | ADVANCE-3 | NCT00423319 | Lassen MR | 2010 | N Engl J Med | 363(26):2487–98 | 21175312 | 10.1056/NEJMoa1006885 |
| 7 | CASTLE-AF | NCT00643188 | Marrouche NF | 2018 | N Engl J Med | 378(5):417–27 | 29385358 | 10.1056/NEJMoa1707855 |
| 8 | CABANA | NCT00911508 | Packer DL | 2019 | JAMA | 321(13):1261–74 | 30874766 | 10.1001/jama.2019.0693 |
| 9 | RAFT-AF | NCT01420393 | Parkash R | 2022 | Circulation | 145(23):1693–1704 | 35313733 | 10.1161/CIRCULATIONAHA.121.057095 |
| 10 | DAPA-HF | NCT03036124 | McMurray JJV | 2019 | N Engl J Med | 381(21):1995–2008 | 31535829 | 10.1056/NEJMoa1911303 |
| 11 | EMPEROR-Reduced | NCT03057977 | Packer M | 2020 | N Engl J Med | 383(15):1413–24 | 32865377 | 10.1056/NEJMoa2022190 |
| 12 | EMPEROR-Preserved | NCT03057951 | Anker SD | 2021 | N Engl J Med | 385(16):1451–61 | 34449189 | 10.1056/NEJMoa2107038 |
| 13 | DELIVER | NCT03619213 | Solomon SD | 2022 | N Engl J Med | 387(12):1089–98 | 36027570 | 10.1056/NEJMoa2206286 |
| 14 | CLEAR Outcomes | NCT02993406 | Nissen SE | 2023 | N Engl J Med | 388(15):1353–64 | 36876740 | 10.1056/NEJMoa2215024 |
| 15 | **SPIRE-1 and SPIRE-2 (one joint report)** | NCT01975376 · NCT01975389 | Ridker PM | 2017 | N Engl J Med | 376(16):1527–39 | 28304242 | 10.1056/NEJMoa1701488 |
| 16 | EARLY (bosentan) | NCT00091715 | Galiè N | 2008 | Lancet | 371(9630):2093–100 | 18572079 | 10.1016/S0140-6736(08)60919-8 |
| 17 | COMPASS-2 | NCT00303459 | McLaughlin V | 2015 | Eur Respir J | 46(2):405–13 | 26113687 | 10.1183/13993003.02044-2014 |
| 18 | CLEAR SYNERGY / OASIS-9 (colchicine report) | NCT03048825 | Jolly SS | 2024 | N Engl J Med | 392(7):633–42 | 39555823 | 10.1056/NEJMoa2405922 |
| 19 | COLCOT | NCT02551094 | Tardif JC | 2019 | N Engl J Med | 381(26):2497–2505 | 31733140 | 10.1056/NEJMoa1912388 |
| 20 | CONVINCE | NCT02898610 | Kelly P | 2024 | Lancet | 404(10448):125–33 | 38857611 | 10.1016/S0140-6736(24)00968-1 |
| 21 | LoDoCo2 | **ACTRN12614000093684** (ANZCTR) | Nidorf SM | 2020 | N Engl J Med | 383(19):1838–47 | 32865380 | 10.1056/NEJMoa2021372 |

### Notes that belong with specific rows

- **15 — SPIRE-1 and SPIRE-2 share one primary publication.** Both registrations list PMID
  28304242 and neither has a separate primary report; both were terminated early. The acronyms
  were confirmed from the registrations' own `acronym` fields — `SPIRE-1` = NCT01975376
  (n=16,784), `SPIRE-2` = NCT01975389 (n=10,564). **Cite one reference for both trials.**
- **18 — CLEAR SYNERGY reported its two randomisations in two papers on the same day.** The
  colchicine report is PMID **39555823** (`10.1056/NEJMoa2405922`); the **spironolactone**
  report is PMID **39555814** (`10.1056/NEJMoa2405923`), differing by one digit in both
  identifiers. Citing the wrong one attributes a mineralocorticoid-antagonist result to
  colchicine.
- **21 — LoDoCo2 is not registered on ClinicalTrials.gov.** Its registration is ANZCTR
  `ACTRN12614000093684`, quoted from the trial's own abstract. **That registry was not searched
  in this work**, so the identifier is reported as the publication states it and is not verified
  against ANZCTR.

### Acronym checks — read back from the registrations

Nine registrations **declare no acronym at all**: AMPLIFY, AMPLIFY-EXT, ADVANCE-1, ADVANCE-3,
EMPEROR-Reduced, EMPEROR-Preserved, EARLY. For these the trial name used in the paper is
supported by the **publication's own group authorship** (`AMPLIFY Investigators`,
`AMPLIFY-EXT Investigators`, `ADVANCE-3 Investigators`) or by the official title, not by the
registry acronym field. `COMPASS-2` is declared as `Compass-2` (case differs only).

---

## Nothing here is unresolved

Every trial named in the paper resolved to a primary publication. **No citation on this list is
approximated**, and no row was completed from memory. If a further trial is added to the paper,
it must go through the same route before it is cited.

### One methodological caveat, because it affects reuse of this method

**The registry's reference typing does not reliably mark the primary publication.** Only
**CONVINCE** carries a sponsor-typed `RESULT` reference; every other trial's primary report is
typed `DERIVED`. And **CLEAR Outcomes' main report (PMID 36876740) is typed `BACKGROUND`** —
filtering on reference type would have missed the primary publication of that trial entirely.
Each row above was identified by reading the citation strings, not by selecting on type or by
position.

---

## Search-recall examples — exact registration identifiers

| example in the paper | registration | confirmed detail |
|---|---|---|
| **the two trials registering phase `NA`**, one of them n=2,204 | **NCT00911508** (CABANA, **n=2,204**) and **NCT01420393** (RAFT-AF, n=411) | both declare `phases: ["NA"]`. A `phase=(PHASE3 OR PHASE4)` filter took recall on `ablation-af-review` from **4/4 to 2/4** while cutting the surfaced set from 931 to 143. |
| **the trial dropped by a condition term one word narrow** | **NCT00168805** (RE-MODEL, n=2,101) | coded `conditions: ["Arthroplasty, Replacement, Knee", "Thromboembolism"]`. A query asking for *venous* thromboembolism does not match the broader coded term. |
| **the 7,264-participant trial concealed by an unexhausted cursor** | **NCT03048825** (CLEAR SYNERGY / OASIS-9, **n=7,264**) | surfaced on **page 2 only** of a 137-record search. A screen stopped at page 1 would have reported a complete-looking cascade missing the largest trial in its own included set. |
| **the pair registered twice under separate identifiers** | **NCT04906720** and **NCT06731595** | *Post-Ablation Pericarditis Reduction Study*, identical official title, enrolment **248**, status, dates and conditions; org identifiers `R20200174` and `PAPERS`. The `briefTitle`s differ only by the suffix `(PAPERS)`. |

**Note on the phase example.** If the paper describes CABANA and RAFT-AF as *"registering phase
NA"*, that is exact. If it describes them as *"not declaring a phase"*, that is not — the
registrations declare the value `NA`, which is a declared value and not an absence, and the
distinction is the point the example is making.
