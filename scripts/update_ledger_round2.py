"""Bring outputs/apixaban_acs_correction_ledger.json into line with the round-2 revision.

Records the cross-family gate outcome, corrects the two false explanatory claims in
place, and keeps the round-1 wording visible so the errors are named rather than
quietly overwritten.
"""
import io
import json
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

P = "outputs/apixaban_acs_correction_ledger.json"
d = json.load(open(P, encoding="utf-8"))

d["status"] = (
    "REVISED 2026-07-30 after a cross-family gate (Codex gpt-5.5 + Gemini, both verified to "
    "source). Committed locally, NOT PUSHED. Awaiting re-gate and Mahmood's explicit go."
)

d["cross_family_gate_round_1"] = {
    "outcome": "Arithmetic and sign flip SURVIVED. Two explanatory claims did NOT.",
    "survived": (
        "Codex gpt-5.5 reproduced OR 1.9748 (1.0411-3.7458), p=0.037 digit for digit. "
        "Direction = harm confirmed, and judged UNDER-claimed rather than over-claimed."
    ),
    "rejected_and_corrected": [
        {
            "claim_that_was_false": (
                "APPRAISE-2 'reports neither arm of the pooled outcome / neither is the ISTH "
                "major/CRNM composite pooled here'."
            ),
            "why_false": (
                "ClinicalTrials.gov NCT00831441 posts, as a SECONDARY outcome, 'Event Rate of "
                "Confirmed Major Bleeding or Clinically Relevant Non-Major Bleeding (CRNM) Using "
                "ISTH Criteria During the Treatment Period - Treated Participants': Placebo 2.29, "
                "Apixaban 5 mg BID 6.15, unit 'percentage of participants/100-pt years', "
                "denominators 3643 and 3672. Re-read live from the API this session."
            ),
            "corrected_to": (
                "The endpoint IS reported; it is the MEASURE that bars it. Posted only as an "
                "incidence RATE over person-time, so per-arm counts cannot be recovered without "
                "repeating the rate-as-count error being corrected. Excluded from the COUNT-based "
                "pool on that ground, and carried instead as a rate-based sensitivity comparison."
            ),
            "severity": "An unverified assertion of exactly the class the fix existed to remove.",
        },
        {
            "claim_that_was_false": "AUGUSTUS's denominator 1153 'matches no arm of the trial'.",
            "why_false": (
                "NCT02415400 participant flow and baseline denominators are 1153 / 1153 / 1154 / "
                "1154 (total 4614) - the four cells of the 2x2 factorial. 1153 is the randomised "
                "size of each APIXABAN cell. It is a real registry denominator."
            ),
            "corrected_to": (
                "A LEVEL-OF-AGGREGATION mismatch: a factorial-CELL denominator (1153) paired with "
                "a FACTOR-LEVEL marginal rate (24.66 and 35.79 belong to the apixaban and VKA "
                "factor levels, analysed on 2290 and 2259). Compounding it, the apixaban-side cell "
                "denominator was applied to the VKA arm too, whose cells are 1154."
            ),
            "severity": "Same class. The arithmetic reproduction was right; the explanation was not.",
        },
    ],
    "also_addressed": [
        "Pooled total events (41) and N (1065) added to the VISIBLE badge - previously absent.",
        (
            "Gemini flagged circularity: the only phase-3 trial was excluded, then the phase-2 "
            "guard was disabled because only phase-2 trials remained. Addressed explicitly on the "
            "badge - the restriction follows from the MEASURE (APPRAISE-2 reports this endpoint as "
            "a rate, and no count-based estimator can consume a rate without person-time), not "
            "from a judgement about phase 3; and it is not a favourable subset, because the "
            "excluded phase-3 trial points the same way harder (rate ratio 2.686 vs pooled OR "
            "1.975)."
        ),
        (
            "Over-claims softened: 'root cause, proven' -> 'arithmetic origin', quantified as a "
            "measured maximum deviation of 0.341 across the four reproductions; and the APPRAISE-2 "
            "early termination is no longer phrased so that a terminating finding is attributed to "
            "a pool that excludes APPRAISE-2."
        ),
    ],
}

d["external_corroboration"] = {
    "same_endpoint_rate_ratio": {
        "trial": "APPRAISE-2 (NCT00831441), phase 3, NOT in the pool",
        "endpoint": (
            "ISTH major or clinically relevant non-major bleeding - IDENTICAL definition to the "
            "pooled endpoint"
        ),
        "posted": "placebo 2.29 vs apixaban 6.15 per 100 patient-years, denominators 3643 and 3672",
        "rate_ratio": 2.686,
        "ci": None,
        "ci_note": (
            "No interval is computable from posted rates alone - person-time is not posted and the "
            "counts are not recoverable. The point estimate is quoted without one rather than derived."
        ),
        "why_it_matters": (
            "Stronger corroboration than the TIMI major bleeding HR 2.59 cited in round 1, because "
            "it is the same endpoint definition rather than a narrower one. It also defuses the "
            "phase-2 circularity objection: the excluded phase-3 trial agrees with, and exceeds, "
            "the pooled estimate."
        ),
        "source": "ClinicalTrials.gov NCT00831441 posted results, read 2026-07-30",
    },
    "other_appraise2_rates": {
        "ISTH_major_only_rate_ratio": 2.515,
        "TIMI_major_published_HR": "2.59 (1.50-4.46), P=0.001",
    },
}

d["source_discordances_recorded_not_resolved"] = [
    {
        "item": "APPRAISE-2 TIMI major bleeding denominators",
        "publication": "46/3673 apixaban and 18/3642 placebo (PMID 21780946)",
        "registry": "safety denominators 3672 apixaban and 3643 placebo (NCT00831441 posted results)",
        "gap": "One patient per arm, in opposite directions. Unexplained.",
        "materiality": (
            "Immaterial to every estimate on the page - TIMI major bleeding is not pooled. Recorded "
            "because an unexplained one-patient gap is exactly what this audit exists to surface."
        ),
    }
]

for t in d["per_trial"]:
    if t["nct"] == "NCT00831441":
        t["quarantine_reason"] = (
            "MEASURE, not endpoint. This trial DOES report the pooled endpoint - ClinicalTrials.gov "
            "posts it as a SECONDARY outcome (ISTH major or CRNM bleeding: placebo 2.29 vs apixaban "
            "6.15 per 100 patient-years on 3643 and 3672). It is excluded from the COUNT-based pool "
            "because that endpoint is posted only as an incidence RATE, so recovering per-arm counts "
            "would repeat the exact error this correction removes. Carried instead as a rate-based "
            "sensitivity comparison, rate ratio 2.686."
        )
        t["ROUND_1_ERROR_CORRECTED"] = (
            "Round 1 stated: 'Reports neither arm of the pooled outcome. Its co-primaries are an "
            "ISCHAEMIC composite and TIMI-defined major bleeding; neither is the ISTH major/CRNM "
            "composite pooled in this app.' That was FALSE and is retained here so the error is "
            "visible, not overwritten."
        )
        t["corrected_values_recorded"].insert(
            0,
            {
                "outcome": "ISTH major or CRNM bleeding (SECONDARY) - the pooled endpoint",
                "unit": "percentage of participants/100-pt years",
                "placebo": "2.29 on 3643",
                "apixaban": "6.15 on 3672",
                "rate_ratio": 2.686,
                "counts_recoverable": False,
                "source": "ClinicalTrials.gov NCT00831441 posted results, read 2026-07-30",
            },
        )
        t["note"] = (
            "APPRAISE-2 was terminated early for excess major bleeding with apixaban without a "
            "counterbalancing reduction in ischaemic events. That termination is a finding about "
            "APPRAISE-2, which is NOT in this pool - external corroboration of the pooled result's "
            "direction, not the pooled result itself."
        )
    if t["nct"] == "NCT02415400":
        t["why_the_previous_values_were_wrong"] = {
            "root_cause": "A level-of-aggregation mismatch, compounded by a rate read as a proportion.",
            "arithmetic_origin": (
                "1153 x 24.66/100 = 284.33 -> the ledger 284; 1153 x 35.79/100 = 412.66 -> the "
                "ledger 413. Across all four reproductions (both trials) the maximum deviation is "
                "0.341. A measured reproduction, not a claim about intent."
            ),
            "the_denominator": (
                "1153 is a REAL registry denominator. NCT02415400 randomised 1153 / 1153 / 1154 / "
                "1154 across the four cells of its 2x2 factorial (total 4614), so 1153 is the size "
                "of each APIXABAN cell. The defect is that a factorial-CELL denominator was paired "
                "with a FACTOR-LEVEL marginal rate: the posted 24.66 and 35.79 ('Percentage per "
                "year') belong to the apixaban and VKA factor levels, analysed on 2290 and 2259. "
                "Compounding it, the apixaban-side cell denominator was applied to the VKA arm as "
                "well, whose cells are 1154."
            ),
            "ci_defect": "The ledger's upper CI was 0.82; the publication states 0.81.",
        }
        t["ROUND_1_ERROR_CORRECTED"] = (
            "Round 1 stated the denominator 1153 'corresponds to no randomised arm' and was "
            "'invented'. That was FALSE - it is a factorial-cell denominator. Retained here so the "
            "error is visible."
        )

d["pooled_result"]["after"]["events"] = 41
d["pooled_result"]["after"]["n"] = 1065
d["pooled_result"]["after"]["p"] = 0.0372
d["pooled_result"]["phase2_restriction_justification"] = (
    "The count-based pool is phase-2-only. This follows from the MEASURE available, not from a "
    "judgement that phase-3 evidence should be dropped: the phase-3 trial reports this endpoint as "
    "a rate, and a count-based estimator cannot consume a rate without person-time or counts. It "
    "does not select a favourable subset - on the identical endpoint the excluded phase-3 trial "
    "gives a rate ratio of 2.686, larger than the pooled OR of 1.975. Restricting to phase 3 would "
    "leave no count-based estimate at all."
)
d["pooled_result"]["sign_change"] = (
    "The correction reverses the conclusion from benefit to harm. This is a PROVENANCE CORRECTION, "
    "not a result that got worse - the evidence did not change; the app was wrong. The direction is "
    "independently corroborated on the identical endpoint by APPRAISE-2 (rate ratio 2.686), a trial "
    "not in the pool."
)

d["not_done_and_not_claimed"].insert(
    0,
    "Round 1 of this correction shipped two false explanatory claims (see "
    "cross_family_gate_round_1). They were caught by cross-family review, not by this session. Both "
    "are corrected, and both are named on the page rather than silently replaced.",
)

json.dump(d, open(P, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
json.load(open(P, encoding="utf-8"))
print(f"{P}: updated and valid JSON")
