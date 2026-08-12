#!/usr/bin/env python3
"""Build cardio_acm_extraction.json from what was actually read this round.

Every count here was READ from the source named in its `pointer`. Nothing was
computed. Cells that could not be recovered carry not_recovered_reason; cells
whose retrieval was refused carry `obstacle` instead.
"""
import json

CTG = lambda nct, where: {"tier": "T2", "pointer": f"CT.gov {nct} results, {where}",
                          "url": f"https://clinicaltrials.gov/study/{nct}"}
AE = lambda nct: {"tier": "T2", "pointer": f"CT.gov {nct} adverseEventsModule deathsNumAffected",
                  "url": f"https://clinicaltrials.gov/study/{nct}"}

cells = []


def pair(trial, nct, t_arm, c_arm, t, c, pop, reason, sources, hr,
         t_pct=None, c_pct=None, selected=None, outcome="all_cause_death", notes_extra=""):
    """t and c are (events, analysed, randomised)."""
    for arm, (ev, an, rn), pct, role in ((t_arm, t, t_pct, "treatment"),
                                         (c_arm, c, c_pct, "control")):
        notes = f"stored_hr={hr} arm_role={role}"
        if notes_extra:
            notes += " " + notes_extra
        cells.append(dict(
            trial=trial, nct=nct, arm=arm, outcome=outcome, events=ev, analysed=an,
            randomised=rn, population_label=pop, denominator_reason=reason,
            printed_percent=pct, provenance="read", sources=sources,
            identifier_provenance="lookup", registry_units="participants",
            selected=selected, notes=notes))


# ---------------------------------------------------------------- efficacy ACM
NEJM_PARADIGM = {"tier": "T1", "pointer": "NEJM 2014;371:993-1004 Results text",
                 "url": "https://doi.org/10.1056/NEJMoa1409077"}
pair("PARADIGM-HF", "NCT01035255", "sacubitril/valsartan", "enalapril",
     (711, 4187, 4209), (835, 4212, 4233), "FAS",
     "37 randomised at sites closed for serious GCP violations + 6 mis-randomised (trial-wide)",
     [NEJM_PARADIGM, CTG("NCT01035255", "Outcome 2 all-cause mortality")], 0.84,
     17.0, 19.8, selected=True)
# the duplicate population that the registry also posts
for arm, ev, n in (("sacubitril/valsartan", 714, 4209), ("enalapril", 837, 4233)):
    cells.append(dict(trial="PARADIGM-HF", nct="NCT01035255", arm=arm,
                      outcome="all_cause_death", events=ev, analysed=n, randomised=n,
                      population_label="randomised (adjudicated cause-of-death table)",
                      denominator_reason=None, provenance="read",
                      sources=[CTG("NCT01035255", "Outcome 3 adjudicated primary causes of death")],
                      identifier_provenance="lookup", registry_units="participants",
                      selected=False,
                      notes="alternate population, recorded so the duplicate stays visible"))

pair("PARAGON-HF", "NCT01920711", "sacubitril/valsartan", "valsartan",
     (342, 2407, 2419), (349, 2389, 2403), "FAS",
     "NOT STATED in the registry results module; 12 and 14 participants excluded from the FAS "
     "respectively, reason not given — open item for primary verification",
     [CTG("NCT01920711", "Outcome 5 All-cause Mortality")], 0.97, selected=True)

pair("DAPA-HF", "NCT03036124", "dapagliflozin 10 mg", "placebo",
     (276, 2373, 2373), (329, 2371, 2371), "randomised",
     None, [CTG("NCT03036124", "Outcome 6 all-cause mortality")], 0.83, selected=True)

pair("SPRINT", "NCT01206062", "intensive SBP control", "standard SBP control",
     (155, 4678, 4678), (210, 4683, 4683), "randomised",
     None, [CTG("NCT01206062", "Outcome 2 Number of Participants With All-cause Mortality")],
     0.73, selected=True)

pair("ACCORD (glycemia)", "NCT00000620", "intensive glycaemic control", "standard glycaemic control",
     (391, 5128, 5128), (327, 5123, 5123), "randomised (glycemia trial)",
     None, [CTG("NCT00000620", "Outcome 2 Death From Any Cause in the Glycemia Trial")],
     1.19, selected=True)

pair("DECLARE-TIMI 58", "NCT01730534", "dapagliflozin 10 mg", "placebo",
     (529, 8582, 8582), (570, 8578, 8578), "randomised",
     None, [CTG("NCT01730534", "Outcome 4 all-cause mortality")], 0.93, selected=True)

NEJM_ODYSSEY = {"tier": "T1", "pointer": "NEJM 2018;379:2097-2107 Results text",
                "url": "https://doi.org/10.1056/NEJMoa1801174"}
pair("ODYSSEY OUTCOMES", "NCT01663402", "alirocumab", "placebo",
     (334, 9462, 9462), (392, 9462, 9462), "randomised",
     None, [NEJM_ODYSSEY], 0.85, 3.5, 4.1, selected=True)

NEJM_EMPAK = {"tier": "T1", "pointer": "NEJM 2023;388:117-127 Table 2 'Death from any cause'",
              "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC7614055/"}
pair("EMPA-KIDNEY", "NCT03594110", "empagliflozin 10 mg", "placebo",
     (148, 3304, 3304), (167, 3305, 3305), "randomised",
     None, [NEJM_EMPAK], 0.87, 4.5, 5.1, selected=True)

# ------------------------------------------- adverse-events-module alternates
# Recorded so the duplicate is visible (CHK003) and so CHK013 has something to
# point at. NONE of these is the efficacy endpoint.
for trial, nct, t_arm, c_arm, t, c, tn, cn in (
        ("ODYSSEY OUTCOMES", "NCT01663402", "alirocumab", "placebo", 238, 278, 9451, 9443),
        ("EMPA-KIDNEY", "NCT03594110", "empagliflozin 10 mg", "placebo", 314, 353, 3304, 3305),
        ("DAPA-HF", "NCT03036124", "dapagliflozin 10 mg", "placebo", 286, 333, 2368, 2368),
        ("PARAGON-HF", "NCT01920711", "sacubitril/valsartan", "valsartan", 347, 357, 2419, 2402),
):
    for arm, ev, n in ((t_arm, t, tn), (c_arm, c, cn)):
        cells.append(dict(trial=trial, nct=nct, arm=arm, outcome="all_cause_death",
                          events=ev, analysed=n, randomised=n,
                          population_label="safety population (adverse events module)",
                          provenance="read", sources=[AE(nct)],
                          identifier_provenance="lookup", registry_units="participants",
                          selected=False,
                          notes="adverse-events-module death count; different population and "
                                "collection window from the efficacy endpoint"))

# ------------------------------------------------------------ HEART-FID: open
# Two registry values, neither labelled as the efficacy all-cause mortality
# endpoint, and they disagree by a factor of ~2.7. Deliberately left unresolved
# so the harness blocks it rather than a human picking silently.
for arm, ev12, evAE, n in (("ferric carboxymaltose", 131, 354, 1532),
                           ("placebo", 158, 367, 1533)):
    cells.append(dict(trial="HEART-FID", nct="NCT03037931", arm=arm, outcome="all_cause_death",
                      events=ev12, analysed=n, randomised=n, population_label="ITT, 12-month window",
                      provenance="read", sources=[CTG("NCT03037931", "Outcome 1 Number of Deaths")],
                      identifier_provenance="lookup", registry_units="participants",
                      notes="stored_hr=0.95 arm_role=" + ("treatment" if "ferric" in arm else "control")))
    cells.append(dict(trial="HEART-FID", nct="NCT03037931", arm=arm, outcome="all_cause_death",
                      events=evAE, analysed=n, randomised=n,
                      population_label="safety population (adverse events module), 67.5 months",
                      provenance="read", sources=[AE("NCT03037931")],
                      identifier_provenance="lookup", registry_units="participants",
                      notes="stored_hr=0.95 arm_role=" + ("treatment" if "ferric" in arm else "control")))

# ------------------------------------------------ not recovered, with reasons
PCT_ONLY = ("registry results module posts this outcome as a percentage / KM estimate only; "
            "no integer count is printed anywhere in the module. Derivation is prohibited "
            "(CHK004). Count must come from the primary publication.")
NO_OUTCOME = "registry results module posts no death-titled outcome measure."
NO_MODULE = "no results module posted on the registry."

for trial, nct, arms, ns, reason in (
        ("FOURIER", "NCT01764633", ("evolocumab", "placebo"), (13784, 13780), PCT_ONLY),
        ("LEADER", "NCT01179048", ("liraglutide", "placebo"), (4668, 4672), PCT_ONLY),
        ("GLOBAL LEADERS", "NCT01813435", ("ticagrelor monotherapy", "reference strategy"),
         (7980, 8011), PCT_ONLY),
        ("ATLAS ACS 2", "NCT00809965", ("rivaroxaban low dose", "placebo"), (5174, 5176), PCT_ONLY),
        ("TWILIGHT", "NCT02270242", ("ticagrelor monotherapy", "ticagrelor + aspirin"),
         (3555, 3564), NO_OUTCOME),
        ("COMMANDER HF", "NCT01877915", ("rivaroxaban 2.5 mg", "placebo"), (2507, 2515), PCT_ONLY),
        ("CREDENCE", "NCT02065791", ("canagliflozin", "placebo"), (2202, 2199), PCT_ONLY),
        ("EMPEROR-Reduced", "NCT03057977", ("empagliflozin 10 mg", "placebo"), (1863, 1867), PCT_ONLY),
        ("SUSTAIN-6", "NCT01720446", ("semaglutide", "placebo"), (1648, 1649), PCT_ONLY),
        ("AMPLITUDE-O", "NCT03496298", ("efpeglenatide", "placebo"), (2717, 1359), NO_OUTCOME),
        ("SOLOIST-WHF", "NCT03521934", ("sotagliflozin", "placebo"), (608, 614), PCT_ONLY),
        ("EMPA-REG OUTCOME", "NCT01131676", ("empagliflozin pooled", "placebo"), (4687, 2333), PCT_ONLY),
        ("CANVAS Program", "NCT01032629", ("canagliflozin pooled", "placebo"), (None, None),
         PCT_ONLY + " Additionally the registry record covers CANVAS only, while the pooled "
                    "'CANVAS Program' entity in the atlas also includes CANVAS-R (NCT01989754) "
                    "— entity mismatch must be resolved before extraction."),
        ("VERTIS-CV", "NCT01986881", ("ertugliflozin pooled", "placebo"), (5499, 2747), PCT_ONLY),
        ("VADT", "NCT00032487", ("intensive glycaemic control", "standard glycaemic control"),
         (899, 892), NO_OUTCOME),
        ("ADVANCE", "NCT00145925", ("intensive glycaemic control", "standard glycaemic control"),
         (None, None), NO_MODULE),
):
    for arm, n in zip(arms, ns):
        cells.append(dict(trial=trial, nct=nct, arm=arm, outcome="all_cause_death",
                          events=None, analysed=n, randomised=n,
                          population_label="randomised", provenance="read",
                          sources=[CTG(nct, "results module scanned for death-titled outcomes")],
                          identifier_provenance="lookup",
                          registry_units="percentage of participants"
                          if reason is PCT_ONLY else "participants",
                          not_recovered_reason=reason,
                          notes="registry route exhausted; publication retrieval is the next step"))

with open("cardio_acm_extraction.json", "w", encoding="utf-8") as fh:
    json.dump({"cells": cells}, fh, indent=1)
print(f"wrote {len(cells)} cells")
