"""Round-3 ledger wording fixes. NO NUMBER CHANGES.

Strips every cross-scale magnitude comparison between APPRAISE-2's rate ratio and
the pooled odds ratio, restates the reproduction bound as <= 0.3413, and records
the re-gate outcome. Directional corroboration and the endpoint-alignment
argument are kept - they are what actually refute favourable-subset selection.
"""
import io
import json
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

P = "outputs/apixaban_acs_correction_ledger.json"
d = json.load(open(P, encoding="utf-8"))

NONCOMPARABLE = (
    "Direction only: a rate ratio over person-time and an odds ratio over a fixed follow-up are "
    "different estimands on different scales, so the two magnitudes are not comparable and none "
    "is claimed."
)

d["status"] = (
    "RE-GATED 2026-07-30 (Codex gpt-5.5 + Gemini, both verified to the live registry). Substance "
    "PASSED; four wording defects fixed in round 3 with no number changed. Committed locally, "
    "NOT PUSHED. Queued release-ready pending Mahmood's go."
)

d["preliminary"] = {
    "status": "PRELIMINARY / exploratory - NOT a definitive safety estimate",
    "why": (
        "k=2, 41 events across 1065 participants, both pooled trials phase 2, fragility index 1, "
        "HKSJ-adjusted interval crossing 1, 2-source verification only."
    ),
    "what_it_supports": (
        "That the page's previous claim of BENEFIT was wrong, and that the direction of effect "
        "is HARM."
    ),
    "what_it_does_not_support": (
        "A precise magnitude. It must not be cited as a headline safety conclusion for apixaban "
        "in ACS."
    ),
    "flagged_by": "Both model families, as the standing caveat before any main-branch push.",
}

d["cross_family_gate_round_2_regate"] = {
    "outcome": "Substance PASSED. Four wording defects fixed; no number changed.",
    "verified_verbatim_to_source": [
        "The APPRAISE-2 ISTH-secondary rewrite (2.29 / 6.15 on 3643 / 3672, rate ratio 2.686, "
        "no fabricated CI).",
        "The 'ltapixaban factorial cell' rewrite for AUGUSTUS's 1153.",
        "Pooled OR 1.9748 unchanged. No round-1 false claim live.",
    ],
    "wording_defects_fixed": [
        {
            "defect": "CROSS-SCALE OVER-CLAIM",
            "was": (
                "'its rate ratio 2.69 which agrees with and EXCEEDS the pooled OR 1.97'; 'points "
                "the SAME WAY, HARDER'; 'restricting to phase 2 yields the SMALLER of the two "
                "effects'."
            ),
            "why_wrong": (
                "An odds ratio and a rate ratio are different estimands on different scales over "
                "different follow-up. The comparison of DIRECTION is valid; the comparison of "
                "MAGNITUDE is unsupported."
            ),
            "now": (
                "All magnitude words removed. The directional-agreement point is kept - it is "
                "what refutes favourable-subset selection - and so is the endpoint-alignment "
                "argument (identical endpoint definition, not a narrower proxy). The "
                "non-comparability is stated explicitly wherever the rate ratio appears."
            ),
        },
        {
            "defect": "FALSE PRECISION BOUND",
            "was": "'reproduces all four to within 0.341'",
            "why_wrong": "The measured maximum deviation is 0.3413 (AUGUSTUS/VKA: 413 - 412.6587), "
                         "so 'within 0.341' is strictly false.",
            "now": "'to within <= 0.3413', which holds with equality.",
        },
        {
            "defect": "MISSING PRELIMINARY FRAMING",
            "was": "The badge headlined the corrected estimate without an explicit exploratory caveat.",
            "now": "A dedicated PRELIMINARY block sits directly under the headline result on both "
                   "the full page and the stub, and window.__verdict carries preliminary: true "
                   "plus a preliminary_note.",
        },
        {
            "defect": "RETENTION-LABEL MISMATCH",
            "was": "The commit framing and this ledger used ROUND_1_ERROR_CORRECTED; the HTML "
                   "used correction_note.",
            "now": "ROUND_1_ERROR_CORRECTED everywhere - ledger, window.__quarantinedTrials, and "
                   "the framing.",
        },
    ],
}

ec = d["external_corroboration"]["same_endpoint_rate_ratio"]
ec["strength_of_claim"] = "QUALITATIVE, directional corroboration only. " + NONCOMPARABLE
ec["why_it_matters"] = (
    "Its value is endpoint ALIGNMENT, not magnitude: it is the same endpoint definition as the "
    "pooled one, whereas the TIMI major bleeding HR 2.59 cited in round 1 is a narrower endpoint. "
    "It also refutes favourable-subset selection, because the excluded phase-3 trial points the "
    "same way rather than the opposite way. No magnitude comparison with the pooled odds ratio is "
    "drawn."
)
d["external_corroboration"]["other_appraise2_rates"]["note"] = (
    "Recorded for completeness. No magnitude comparison with the pooled odds ratio is drawn from "
    "any of them."
)

d["pooled_result"]["phase2_restriction_justification"] = (
    "The count-based pool is phase-2-only. This follows from the MEASURE available, not from a "
    "judgement that phase-3 evidence should be dropped: the phase-3 trial reports this endpoint "
    "as a rate, and a count-based estimator cannot consume a rate without person-time or counts. "
    "It does not select a favourable subset - on the identical endpoint the excluded phase-3 "
    f"trial shows harm in the SAME DIRECTION. {NONCOMPARABLE} Restricting to phase 3 instead "
    "would leave no count-based estimate at all."
)
d["pooled_result"]["sign_change"] = (
    "The correction reverses the conclusion from benefit to harm. This is a PROVENANCE "
    "CORRECTION, not a result that got worse - the evidence did not change; the app was wrong. "
    "The direction is independently corroborated on the identical endpoint by APPRAISE-2 (rate "
    f"ratio 2.686, same direction), a trial not in the pool. {NONCOMPARABLE}"
)
d["pooled_result"]["after"]["interpretation_status"] = (
    "PRELIMINARY / exploratory - see the 'preliminary' block. Supports the reversal and the "
    "direction, not a precise magnitude."
)

fixed = 0
for t in d["per_trial"]:
    if t["nct"] == "NCT00831441":
        t["quarantine_reason"] = (
            "MEASURE, not endpoint. This trial DOES report the pooled endpoint - "
            "ClinicalTrials.gov posts it as a SECONDARY outcome (ISTH major or CRNM bleeding: "
            "placebo 2.29 vs apixaban 6.15 per 100 patient-years on 3643 and 3672). It is "
            "excluded from the COUNT-based pool because that endpoint is posted only as an "
            "incidence RATE, so recovering per-arm counts would repeat the exact error this "
            f"correction removes. Carried instead as directional corroboration, rate ratio "
            f"2.686 on the identical endpoint. {NONCOMPARABLE}"
        )
        for o in t.get("corrected_values_recorded", []):
            if o.get("rate_ratio") == 2.686:
                o["comparability"] = NONCOMPARABLE
        fixed += 1
    if t["nct"] == "NCT02415400":
        w = t["why_the_previous_values_were_wrong"]
        w["arithmetic_origin"] = (
            "1153 x 24.66/100 = 284.33 -> the ledger 284; 1153 x 35.79/100 = 412.66 -> the "
            "ledger 413. Across all four reproductions (both trials) the maximum deviation is "
            "0.3413, so the bound stated on the page is <= 0.3413. A measured reproduction, not "
            "a claim about intent."
        )
        fixed += 1
assert fixed == 2, fixed

d["not_done_and_not_claimed"].insert(
    0,
    "This page states a DIRECTION of harm, not a definitive magnitude. See the 'preliminary' "
    "block: k=2, 41 events, phase-2-only, fragility index 1, HKSJ crossing 1, 2-source "
    "verification.",
)

json.dump(d, open(P, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
json.load(open(P, encoding="utf-8"))
print(f"{P}: updated and valid JSON")
