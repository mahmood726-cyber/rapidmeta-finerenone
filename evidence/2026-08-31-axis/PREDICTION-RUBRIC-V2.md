# Prediction: the rubric with its missing clause. Written before the re-run.

## Why this is a RESTORATION, not a post-hoc adjustment — and it is checkable

⛔ Adding a clause to a rubric after seeing which cases it caught is normally how a gate
stops measuring anything. This one is different and the difference is verifiable:

**[MEASURED]** `git log -1 -- evidence/2026-08-31-axis/oa_judgements.json` -> `2b8029a3b`,
committed BEFORE the delegation existed. Nine judgements in that commit refuse on exactly
this ground:

    CDSR     bosentan-pah-children   CD015824      "adults and adolescents with group 1 …"
    CDSR     enoxaparin-vte          CD006650      "for the long-term treatment of …"
    OA-mine  riociguat-pah           PMC11039558   "connective tissue diseases"
    OA-mine  riociguat-pah           PMC5761307    "congenital heart disease"
    OA-mine  riociguat-pah           PMC11831188   "Chronic Thromboembolic Pulmonary Hypertension"
    OA-mine  evolocumab-dyslipidemia PMC12812102   "in chronic kidney disease"
    … 9 in total

⇒ The clause was in force when the CDSR and my own OA judgements were made. **I failed to
TRANSMIT it, and then scored a delegate against it.** Stating it now asks both raters the
same question for the first time.

## THE PREDICTION, from a stated mechanism

Of Codex's 35 `COUNTERPART` calls I could name a disqualifying restriction in roughly 31 —
older patients, dialysis, end-stage renal disease, device-detected AF, sex-specific
outcomes, drug concentrations, predictors of use. If the clause is transmitted, those go.

| | predicted |
|---|---|
| Codex `COUNTERPART` calls, was 35 | **4 to 12** |
| of the previously-accepted 35, now refused | **≥ 25** |
| topics gaining a counterpart, was 5 of 7 | **3 of 7** — dabigatran-af, dabigatran-stroke, olmesartan-htn |
| resulting position | **13 of 20** |
| both known-answer controls still pass | **yes** — neither control involves a restricted population |

⚠️ **The control that matters is the NEGATIVE one.** A clause that says "refuse restricted
populations" makes refusal cheaper, so a judge could pass the negative control by refusing
everything. If `COUNTERPART` drops below 4 — fewer than I accept myself — that is
over-refusal induced by my own clause, and it is a defect in the clause, not a result.

## Which way I expect to miss

The last three predictions all missed LOW after I over-corrected from fifteen optimistic
ones. So I am predicting from the mechanism rather than from a direction: I counted the
restrictions in the 35 by hand, and 3 of 7 is my own adjudication of the same evidence. If
I miss, I expect it to be because Codex reads "coherent class containing the drug" more
generously than I do on the class-level network meta-analyses (PMC4054633, PMC4244213,
PMC3951387), which I called borderline and could defensibly have accepted.
