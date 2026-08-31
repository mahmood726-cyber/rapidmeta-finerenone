# PREDICTIONS — logged 2026-08-30, BEFORE any measurement

Written before running the screen, the AACT ghost count, or the citation chase.
Each prediction is falsifiable and will be scored against what actually returned.

## P1 — the bibliographic screen denominator
The executed search retrieved 374 PubMed + 1000 Europe PMC + 1 ISRCTN = 1,375
bibliographic records, and the `screen` block reports `candidates_screened: 63`,
which is the ClinicalTrials.gov set alone. I predict the 1,375 bibliographic
records were NEVER screened, and that `coverage_fraction` "2 of 2" is therefore a
REGISTRY-INTERNAL recall figure presented without saying so.

PREDICTION: screening the 1,375 bibliographic records at title level will find
**0 additional eligible trials** — but will find at least one *randomised
dapivirine ring* record whose trial is not in the 63-NCT set, most likely a
non-US-registered phase 1/2 ring study. Confidence: 0 additional ELIGIBLE trials
70%; ≥1 randomised-ring record outside the NCT set 60%.

## P2 — AACT ghost count
Registered dapivirine interventional trials in the AACT 2026-04-12 snapshot.
PREDICTION: between 12 and 30 studies; of those with an efficacy or effectiveness
primary outcome, I predict **at least 2** that are completed with no linked
publication in AACT `study_references` and no posted results — i.e. genuine
ghosts. Confidence 55%. I predict the two already-named withdrawn trials
(NCT01337570, NCT01337583) will be in the set with enrolment 0.

## P3 — participant flow closing RoB D3
AACT `milestones` / `drop_withdrawals` for NCT01539226 and NCT01617096.
PREDICTION: per-arm started/completed counts ARE present for both trials
(results were posted 2022), and therefore signalling question 3.1 ("outcome data
available for all or nearly all participants") becomes answerable from a free
machine-readable source for BOTH trials. Confidence 75%.
I predict this does NOT change the domain judgement to LOW, because 3.2–3.4
concern differential missingness and dependence on the true value, which the flow
table alone cannot answer. Confidence 80%.

## P4 — citation chasing
OpenAlex forward+backward citations from the two included trial reports.
PREDICTION: **0 additional eligible trials**. Confidence 85%. The value of the
exercise is the *measured* zero, not a discovery.

## P5 — the estimand mismatch
The two trials have different registered primary time frames (24 months vs
12–14 months). PREDICTION: a person-year rate-ratio pool will give a point
estimate within 0.05 of the RR pool (0.703) — i.e. the mismatch is real in
principle and immaterial in fact. Confidence 60%.

## P6 — what the four-reader renderings will expose
PREDICTION: building the HTA rendering will force the disclosure that the
review's comparator (placebo ring) is NOT the decision-relevant comparator in
2026 (oral TDF/FTC or CAB-LA), and that this is nowhere stated in the object
today. Confidence 90%. I predict the guideline EtD rendering will come out with
MORE EMPTY CELLS THAN FILLED — values, resources, equity, acceptability and
feasibility are all unaddressed by the store. Confidence 85%.
