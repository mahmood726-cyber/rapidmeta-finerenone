# Exhaustive paging, and a delegated adjudication that measured my rubric

Every claim is marked **[MEASURED]** with the command that produced it, or **[INFERRED]**.

    REF.rule    604ed6957a1adf17   ⛔ FROZEN throughout
    REF.paging  scripts/rekey20/oa_page_all.py      -> oa_paged_twenty.json
    REF.judge   scripts/rekey20/oa_judge_delegate.py -> oa_judgements_delegated.json
    REF.judge2  codex.cmd (GPT-5), liveness proven by an exec returning ALIVE
    REF.pre     PREDICTION-FULL-PAGING.md, written before the pager existed

---

# 1 PAGING — every topic exhausted **[MEASURED]**

    fetched                           19,263      exhausted 20/20, zero lower bounds
    excluded as protocols by contract     148      (18 at the old 100-row cap)
    condition axis                      1,880
    VERIFIED PAIRS                        558

`apixaban-af-review` went 2 → **103** verified pairs, `warfarin-af` → **102**,
`enoxaparin-vte` → **76**. The thirteen control topics are no longer windows.

**[MEASURED] Prediction scored:** I said 600–1,500 verified pairs; observed **558** — a miss,
low. The deciding mechanism is the one I named as least certain: I extrapolated a 7%
verification rate from a **relevance-ordered head** to the tail; the true overall rate is
**2.9%** (558/19,263).

## 1.1 ⛔ The ceiling is 18, not 20, and the blocker is object data **[MEASURED]**

    apixaban-vte-prophylaxis   "Apixaban thromboprophylaxis: four trials, four different
                                primary composites, and one estimand…"   condition_span: None
    evolocumab-ascvd-auto2     "Evolocumab Ascvd Auto2"                  condition_span: None

Neither title contains a condition connective, so neither ever had a query. Exhaustive
paging changed nothing for them. **[INFERRED]** Under the frozen rule they are unreachable,
and the defect is in the objects' titles. ⛔ I will not author a condition span to reach a
number.

---

# 2 THE DELEGATION — and three silent failures in my own harness

Codex (GPT-5) judges because **I built the matcher and was the sole labeller of its output**,
recorded as a real weakness. A second pass by me cannot fix that; a different lab can.

**Scope declared before the run:** only the 10 topics at zero can move the headline, so only
those are sent — 25 pairs each in **oa_id sort order, not relevance**, so a slice cannot be
cherry-picked. Anything not found is reported as a **lower bound**.

## 2.1 The three failures, each of which looked like something else

| # | symptom | actual cause | what I would have reported |
|---|---|---|---|
| 1 | exit 0, **zero output** | no `if __name__ == "__main__"` — `main()` never ran | "Codex returned nothing" |
| 2 | `WinError 2` | `codex` resolves to the npm **bash shim**; Python needs `codex.cmd` | "Codex unavailable" |
| 3 | **16 of 16 slices UNPARSEABLE** | `codex.cmd` is a batch file; **cmd.exe caps argv at 8191 chars**, so a ~15 KB prompt was silently cut to the rubric alone | **"Codex: 0 scoreable"** |

⭐ **Failure 3 is the one that matters.** Codex's raw reply was
*"Send me the topic and the systematic review details"* — **it received the instructions and
zero pairs.** Same defect class as the 100-row retrieval cap, committed inside my own
delegation: the evidence was a window, here an empty one, and the judge was asked about a
population.

⛔ **It was caught only because the harness keeps raw output on failure.** A harness storing
just the verdict cannot tell a model that refused from a prompt that never arrived — and
this project has already published "codex 105 unparseable, 0 scoreable" once, wrongly.

Fixed by passing the slice **by file reference**, never in argv, plus a runner liveness gate
that refuses to send anything unless a real exec returns `ALIVE`.

## 2.2 ⛔ A fourth failure that every control passed

The first clean-looking run reported 129 judgements, **both known-answer controls OK in all
16 slices**, gate refusing only 1, and `5 of 7 topics gain`. **[MEASURED]** counting
distinct pairs:

    judgement rows                  128
    DISTINCT (topic, review) pairs   89     <- not 129
    pairs judged more than once      31
    same pair, DIFFERENT labels       2

**A race on a shared filename.** All four chunks of a topic wrote to `slice_<app>.txt` with
no chunk index and ran concurrently, so each chunk judged whichever write landed last. The
reported "25 examined of 103" was false.

⭐⭐ **No control could have caught this, and that is the lesson.** A control injected into
all 16 slices is *by construction* immune to a bug that makes slices identical, and the gate
passed because the quotes were real — just quotes about the wrong eight pairs. **It took
counting the denominator**, which is the habit that has caught something every time tonight.

⭐ **The bug also produced an unplanned test–retest of the judge:** 31 pairs judged twice or
more by the same model in separate calls, **2 flipped label** — `dabigatran-af`/PMC3633898
and `warfarin-af`/PMC12425454. **[MEASURED]** ~6.5% intra-judge instability, collected by
accident and worth keeping.

## 2.3 The clean run **[MEASURED]**

    rows kept 129 · DISTINCT pairs 129 · repeated 0
    per topic: 25, 25, 25, 25, 25, 2, 2  — exactly as declared
    labels: NOT_COUNTERPART 94 · COUNTERPART 35
    both controls OK in all 16 slices · gate refused 1 of 129
    topics gaining a counterpart: 5 of 7 sent

---

# 3 ⛔ THE HEADLINE DOES NOT MOVE, AND THE REASON IS MY RUBRIC

I read all 35 delegated `COUNTERPART` calls myself. **[MEASURED]** — I would accept **4**.

The disagreement is almost entirely one clause. Codex accepted, and I refuse:

    PMC10727327  "…in OLDER PATIENTS with atrial fibrillation"
    PMC10755581  "…for patients with atrial fibrillation ON DIALYSIS"
    PMC11262503  "…concomitant atrial fibrillation and END-STAGE RENAL DISEASE"
    PMC11631065  "DEVICE-DETECTED atrial fibrillation"
    PMC11253745  "SEX-SPECIFIC comparative outcomes…"
    PMC12115550  "Usual On-therapy Ranges of DRUG CONCENTRATIONS…"
    PMC3395868   "PREDICTORS OF WARFARIN USE in atrial fibrillation…"
    PMC6641826   "Effect and safety of LCZ696…"   ⛔ LCZ696 is sacubitril/valsartan, not olmesartan

**[MEASURED]** My CDSR judgements refuse on exactly this ground — CD001100 (treatment where
the topic is prevention), PMC11039558 (connective-tissue-disease PAH), PMC5761307 (PAH due
to congenital heart disease). **A restricted sub-population is a different population.**

⛔ **And that clause is NOT IN THE RUBRIC I HANDED CODEX.** The rubric names a different
disease, a harm signal, a dose-vs-dose comparison and a head-to-head — it never says a
restricted sub-population disqualifies.

⇒ ⭐⭐ **I judged the delegate against a rule it was never given. The inter-rater
disagreement measures MY RUBRIC before it measures either rater**, and reporting it as
"Codex over-calls" would have been a wrong belief about a tool with my own under-specified
prompt as its cause.

## 3.1 The position, stated with both figures and their definitions

    MEASURED, unchanged            10 of 20 topics, 17 distinct reviews
    delegated, rubric-as-written    +5 topics -> 15 of 20   (Codex, 35/129 COUNTERPART)
    my reading of the same 35        +3 topics -> 13 of 20   (dabigatran-af,
                                                              dabigatran-stroke, olmesartan-htn)

⛔ **I am not claiming 15, and I am not claiming 13.** The two numbers differ because the
rubric is incomplete, and the honest next step is to add the restricted-population clause,
re-run the delegation, and report a figure both raters were asked the same question to
produce. ⭐ **The standing measured position remains 10 of 20.**

⚠️ Even under my stricter reading, three topics do gain, each on a call I independently
accept: `dabigatran-af` → PMC13133535 *"Direct oral anticoagulants for stroke prevention in
patients with atrial fibrillation: a network meta-analysis"*; `dabigatran-stroke` →
PMC3808395; `olmesartan-htn` → PMC11149579 *"angiotensin receptor blockers for nocturnal
blood pressure reduction"* (class containing olmesartan, narrower outcome — allowed).

---

# 4 PREDICTIONS SCORED

| prediction | result | |
|---|---|---|
| verified pairs 600–1,500 | **558** | MISS, low — via the mechanism I flagged |
| ceiling is 18, not 20 | confirmed after exhaustive paging | **HIT** |
| 2–4 of 8 topics gain | **5** (Codex) / **3** (mine) | mine HIT, delegated MISS-low |
| judging becomes the bottleneck | it did — and the harness failed 4 ways first | **HIT** |
| precision falls below 39% | **not computable** — see §3 | — |

**[INFERRED]** Three of the last four predictions have missed LOW. Having over-corrected
after fifteen optimistic misses, I am now under-shooting; the fix is not another constant
adjustment but to state a mechanism and predict from it, which is what worked for the 558.

---

# 5 STILL OPEN

* The rubric's missing restricted-population clause, and a re-run of the delegation with it.
* `apixaban-af-review` and `warfarin-af`: **0 of 25 examined** accepted by me, out of 103 and
  102 verified — reported as **lower bounds**, not zeros.
* The `ae` normalisation in `mesh_lookup.record_matches` (named, deferred).
* Infectious disease, untouched.
