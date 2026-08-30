# -*- coding: utf-8 -*-
"""Complete the dapivirine risk-of-bias assessment from the two trials' own free reports.

⛔ WHAT WAS WRONG, AND IT WAS NOT EFFORT. Both trials carried NO_INFORMATION on D1, D2 and
D3 -- three of five domains, on both trials -- because the assessments were made from
ClinicalTrials.gov registration records. A registration does not state a concealment
mechanism, an analysis population, or how missing outcome data were handled. THE REGISTRY IS
THE WRONG DOCUMENT FOR THIS QUESTION, and no amount of re-reading it would have helped.

⭐ THE RIGHT DOCUMENTS WERE FREE THE WHOLE TIME. ASPIRE at PMC4993693, and The Ring Study's
publisher PDF. Both were fetched, and 28 signalling-question answers were extracted from
them by `answer_rob_from_fulltext`, which cuts each quote out of the paper rather than
letting an author type it.

⚠️ AND THE ROUTE THAT DID NOT WORK IS RECORDED, BECAUSE A SOURCE THAT FAILS IS A FINDING.
WHO prequalification was checked first, by discovery rather than guessing: the product is
listed at `extranet.who.int/prequal/medicines/ema-art-58-h-w-002168`, Status Prequalified,
INN "Dapivirine Vaginal ring 25mg". But the Basis of listing is **Alternative Listing via
EMA Article 58**, which means WHO performed NO INDEPENDENT ASSESSMENT -- it relied on EMA's.
There is no WHOPAR attached, and the page's WHOPAR reference block returns HTTP 403. So WHO
PQ answers a REGISTRATION question ("is this product prequalified, and on what basis") and
cannot answer a RISK-OF-BIAS question. That is a property of the alternative-listing route,
not of WHO PQ generally, and the distinction is the same one this project already recorded
for FDA reviews: a claim about a document class is a claim about a VERSION or ROUTE of it.

⚠️ THREE ANSWERS ARE STILL REFUSALS AND THEY STAY REFUSALS. 1.3 on both trials, and 1.2 on
The Ring Study. Neither paper states in prose whether baseline characteristics were balanced
-- both print a table, and a table is not a sentence -- and the Ring Study describes
randomisation and stratification without any concealment mechanism.

⭐ AND THE TWO REFUSALS COST DIFFERENT AMOUNTS, WHICH IS THE ARGUMENT FOR MAKING THEM.
ASPIRE still reaches D1 = LOW: Table 4 row 1 accepts 1.3 = NI outright, so the missing
baseline statement changes nothing there. The Ring Study reaches D1 = SOME CONCERNS, and the
reason is 1.2 alone -- Table 4 sends 1.2 = NI with 1.3 = N/PN/NI to Some concerns. So one
refusal was free and one was not, and typing "probably no" for either would have bought a
LOW that no sentence in either paper supports. An earlier draft of this docstring asserted
SOME CONCERNS for BOTH trials; the derivation contradicted it and the derivation is right.
"""
import datetime
import io
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "ssot"))

import atomic_write as aw          # noqa: E402
import regulatory_evidence as R    # noqa: E402
import rob2_algorithm as A         # noqa: E402

TOPIC = "agyw-hiv-prep-review"
UTC = datetime.datetime.now(datetime.timezone.utc).isoformat()
ANSWERS = "F:/claude-temp/rob_answers.json"

DOMAIN_KEY = {"D1": "D1_randomisation_process",
              "D2": "D2_deviations_from_intended_intervention",
              "D3": "D3_missing_outcome_data"}


def main(apply_changes=False):
    src = json.load(open(ANSWERS, encoding="utf-8"))
    path = os.path.join(_HERE, "..", "ssot", TOPIC, "%s.json" % TOPIC)
    obj = json.load(open(path, encoding="utf-8"))

    store = obj.setdefault("risk_of_bias", {}).setdefault(R.STORE_KEY, {})
    by_trial = store.setdefault("by_trial", {})
    derived = {}

    for nct, cfg in src.items():
        built, responses, refusals = {}, {}, []
        for q, a in cfg["answers"].items():
            # R.answer refuses a substantive answer without a >=4-word verbatim quote, and
            # refuses to demand one for a routed or absent answer. Both directions matter.
            built[q] = R.answer(q, a["response"], a.get("tier") or R.STATED,
                                a.get("quote") or "", cfg["document"],
                                section=(a.get("section") or a.get("routed_because")
                                         or a.get("no_evidence_because")),
                                url=cfg.get("url"), retrieved_utc=UTC,
                                document_class="trial_publication")
            built[q]["routed_by_the_tool_not_the_paper"] = bool(a.get("routed"))
            if a.get("no_evidence"):
                built[q]["the_document_is_silent"] = True
                refusals.append(q)
            # ⛔ THE ALGORITHM TAKES ITS OWN CODING, NOT OUR STRINGS. `d1`/`d2`/`d3`
            # compare against 'Y/PY', 'N/PN', 'NI', 'NA'; handed "YES" they match no row
            # and return UNDERIVABLE -- which reads exactly like a genuine gap in the
            # evidence. The first run of this script reported all six domains underivable
            # on 28 answers that were complete, and nothing in that output said the fault
            # was ours. `code()` returns None for an unrecognised response rather than
            # coercing, so an untranslatable answer still refuses.
            responses[q] = A.code(a["response"])
            if responses[q] is None:
                raise ValueError("response %r for %s on %s is not one the RoB 2 coding "
                                 "recognises" % (a["response"], q, nct))
        by_trial[nct] = built

        d1 = A.d1(responses)
        d2 = A.d2(responses)
        d3 = A.d3(responses)
        # Each is (verdict, reason). A None verdict is UNDERIVABLE and must stay so.
        derived[nct] = {"D1": d1[0], "D2": d2[0], "D3": d3[0],
                        "why": {"D1": d1[1], "D2": d2[1], "D3": d3[1]},
                        "refusals": refusals, "n_answers": len(built)}

    # ---- write the derived judgements back onto the per-trial domains ----------------
    for oc, per in ((obj.get("risk_of_bias") or {}).get("by_outcome") or {}).items():
        for nct, rec in (per or {}).items():
            if nct not in derived or not isinstance(rec, dict):
                continue
            doms = rec.setdefault("domains", {})
            for short, key in DOMAIN_KEY.items():
                d = doms.setdefault(key, {})
                was = d.get("judgement")
                d["judgement_before_2026_08_30"] = was
                d["judgement"] = derived[nct][short]
                d["signalling_questions"] = {
                    q: by_trial[nct][q]["response"]
                    for q in sorted(by_trial[nct])
                    if q.startswith(short[-1])}
                d["derived_because"] = derived[nct]["why"][short]
                d["derived_by"] = (
                    "rob2_algorithm.%s applied to answers read from the trial's own primary "
                    "report, quotes extracted by answer_rob_from_fulltext. Previous value "
                    "%r came from the ClinicalTrials.gov registration, which does not report "
                    "these properties." % (short.lower(), was))

    store.update({
        "recorded_utc": UTC,
        "completed_from_trial_reports_2026_08_30": (
            "28 signalling-question answers, 14 per trial, read from the two primaries. "
            "Both are free: ASPIRE at PMC4993693, The Ring Study from the publisher. Every "
            "substantive answer carries a quote CUT FROM the paper by code rather than "
            "typed, and every NOT-APPLICABLE says which earlier answer routed it."),
        "who_prequalification_checked_and_cannot_answer_this": (
            "The ring is WHO prequalified (extranet.who.int/prequal/medicines/"
            "ema-art-58-h-w-002168, Status Prequalified, INN 'Dapivirine Vaginal ring "
            "25mg'). The Basis of listing is ALTERNATIVE LISTING via EMA Article 58, so WHO "
            "made no independent assessment, no WHOPAR is attached, and the page's WHOPAR "
            "reference block returns HTTP 403. WHO PQ settles a registration question and "
            "not a risk-of-bias one. Recorded because a source that was checked and does "
            "not answer is a finding; leaving it out would make the next reader check it "
            "again."),
        "what_is_still_refused": (
            "1.3 on both trials (neither paper states in prose whether baseline "
            "characteristics were balanced -- both print a table, and this instrument reads "
            "sentences) and 1.2 on The Ring Study (randomisation and stratification are "
            "described; no concealment mechanism is). These keep D1 at SOME CONCERNS on "
            "both trials rather than LOW."),
    })

    print("DERIVED FROM THE PAPERS")
    for nct, d in derived.items():
        print("  %s  D1=%-14s D2=%-14s D3=%-14s  (%d answers, refusals: %s)"
              % (nct, d["D1"], d["D2"], d["D3"], d["n_answers"],
                 ", ".join(d["refusals"]) or "none"))
    if not apply_changes:
        print("dry run -- pass --apply to write")
        return 0
    n = aw.write_json(path, obj)
    print("WRITTEN %d bytes" % n)
    return 0


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.exit(main(apply_changes="--apply" in sys.argv))
