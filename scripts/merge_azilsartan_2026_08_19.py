#!/usr/bin/env python3
"""MERGE the executed search and screen into `azilsartan-chlorthalidone-vs-olmesartan-hctz`.

A MERGE, NEVER A WHOLESALE WRITE. Every top-level key present before must be present after.

WHAT DOES NOT CHANGE, AND WHY THAT IS THE POINT. k stays 2. The pooled mean difference stays
-5.6912 mmHg. No trial joins and none leaves. THE SEARCH CONFIRMED THE EVIDENCE BASE, and
before it was run nobody could tell a correct included set from an unexamined one -- which is
the same finding bococizumab produced by a different route on the same day, and the third
direction the withholding pair established.

WHAT DOES CHANGE IS EVERYTHING AROUND THE NUMBER: an executed search, a cascade, 57 records
screened to a disposition, criteria auditable against registry fields, and TWO FURTHER
HEAD-TO-HEADS named -- NCT00996281 (n=837) and NCT01309828 (n=153) -- which share both arms of
this review's contrast and register no blood-pressure change outcome at any rank. They are
ELIGIBLE and NOT POOLABLE, and saying so is a stronger statement than never having looked.

Run: python scripts/merge_azilsartan_2026_08_19.py
"""
import io
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "ssot"))
import azl_topic_data as D                                              # noqa: E402

TOPIC = "azilsartan-chlorthalidone-vs-olmesartan-hctz"
DEST = os.path.join(REPO, "ssot", TOPIC, "%s.json" % TOPIC)
EV = os.path.join(REPO, "evidence", "2026-08-19-batch1")


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    with io.open(DEST, encoding="utf-8") as fh:
        obj = json.load(fh)
    before = set(obj)
    with io.open(os.path.join(EV, "azilsartan_screening.json"), encoding="utf-8") as fh:
        screen = json.load(fh)

    obj["search"] = D.AZL_SEARCH
    obj["prisma_flow"] = D.AZL_PRISMA
    obj["k_cascade"] = D.AZL_CASCADE
    obj["extraction"] = D.AZL_EXTRACTION
    obj["screening"] = {
        "search_note": ("Executed 2026-08-19. 57 registrations surfaced -- the WHOLE azilsartan "
                        "programme -- and screened to a disposition; remainder ZERO."),
        "eligibility": (
            "POPULATION: adults with essential or primary hypertension, read from the coded "
            "conditions field. WHERE THAT FIELD NAMES A STUDY OBJECTIVE RATHER THAN A DISEASE "
            "-- NCT01309828 declares `conditions: ['Safety']` -- it is NOT_ASSESSABLE for this "
            "limb and the verdict falls back to the registered TITLE, saying on its face which "
            "it rests on. INTERVENTION: azilsartan medoxomil TOGETHER WITH chlorthalidone in "
            "the same arm; azilsartan monotherapy is a different intervention and azilsartan "
            "with amlodipine is another. COMPARATOR: olmesartan medoxomil TOGETHER WITH "
            "hydrochlorothiazide. ESTIMAND, which governs POOLABILITY and not eligibility: "
            "change from baseline in clinic systolic blood pressure, detected structurally at "
            "every rank. Criteria are DERIVED POST HOC and say so. THEY ARE NARROW BECAUSE THE "
            "QUESTION IS -- one fixed-dose combination against one other -- and narrowness is "
            "a defect only when derived backwards from the trials already present, which is "
            "why the screen ran over the whole programme rather than a shortlist."),
        "eligibility_provenance": D.AZL_CRITERIA,
        "tally": screen["tally"],
        "dispositions_reached_zero_times": screen["dispositions_reached_zero_times"],
        "records": screen["rows"],
        "duplicate_screening": {
            "performed": False,
            "state": "OWED, AND RECORDED AS OWED RATHER THAN DESCRIBED",
            "what_is_owed": "independent duplicate screening by a second reader.",
            "what_was_NOT_done": "No second model family read this screen.",
        },
    }
    wq = dict(screen["withholding_question"])
    wq["per_trial"] = {
        r["nct"]: {"name": r["acronym"],
                   "two_component": "%d rank(s) read" % r["ranks_read"],
                   "three_component": "; ".join(
                       "[%s] %s" % (h["rank"], h["measure"][:90])
                       for h in r["bp_change_at_ranks"]) or
                       "NO blood-pressure change outcome at any rank"}
        for r in wq["per_trial"]}
    wq["answer"] = (
        "YES FOR THE TWO INCLUDED TRIALS AND NO FOR THE OTHER TWO. Four registrations in the "
        "whole azilsartan programme carry both arms of this contrast. Two register a "
        "blood-pressure change outcome and are pooled; two register none at any rank and are "
        "ELIGIBLE, NOT POOLABLE. Both of those are long-term open-label SAFETY studies -- "
        "n=837 and n=153 -- and their absence from the pool is an estimand fact, not a "
        "population one.")
    wq["why_before_deciding"] = (
        "Asked at EVERY registered rank and detected STRUCTURALLY -- a blood-pressure term "
        "plus a change term -- rather than by the two incumbents' registered phrase, which "
        "would have found the two that already agree and nothing else.")
    obj["withholding_question"] = wq
    obj["screening_of_remainder"] = {
        "unscreened_remainder": 0,
        "recovered_sharing_both_arms": 2,
        "of_those_that_joined_the_pool": 0,
        "and_the_included_set_did_not_change": (
            "k stays 2. THAT IS A RESULT OF THE SEARCH AND NOT AN ASSUMPTION IT STARTED FROM. "
            "Before 2026-08-19 this review had no executed search, so its two trials were the "
            "two somebody put on a page; they are now the two the whole 57-record programme "
            "supports."),
        "the_two_that_share_both_arms_and_cannot_contribute": {
            "NCT00996281": ("n=837, open-label, long-term safety and tolerability of AZL-CLD "
                            "against OLM-HCTZ. TWO registered outcomes, neither a "
                            "blood-pressure change."),
            "NCT01309828": ("n=153, long-term safety of AZL-CLD against OLM-HCTZ in "
                            "hypertensive subjects with moderate renal impairment. FOUR "
                            "registered outcomes, none a blood-pressure change. Its coded "
                            "condition is `Safety`, and reading that field literally would "
                            "have excluded it on POPULATION -- a different and weaker "
                            "statement than the true one, which is that it measured something "
                            "else."),
        },
    }
    obj["protocol"] = {
        "prespecified": False, "permanently_refused": True,
        "why": ("A protocol specified before data collection is a HISTORICAL FACT ABOUT THE "
                "PAST and cannot be created retrospectively."),
        "what_was_actually_done": ("Eligibility criteria were derived POST HOC on 2026-08-19, "
                                   "when this review's search was executed for the first "
                                   "time."),
        "authority_permitting_it": "MECIR R107, provided they are declared as such.",
        "forward_remedy": "For topics not yet built, register a protocol BEFORE the search.",
    }
    obj["risk_of_bias"] = {
        "tool": "RoB 2", "state": "NOT_ASSESSED_FOR_THIS_REVIEW",
        "why": ("No result-level RoB 2 assessment has been performed for either contributing "
                "result. RECORDED AS UNASSESSED, NEVER AS ABSENT OF BIAS."),
        "consequence_carried_into_grade": "GRADE rates down one level for risk of bias.",
        "what_would_close_it": ("RoB 2 per RESULT on the week-8 clinic SBP outcome in "
                                "NCT00846365 and NCT01033071."),
    }
    b = obj["results"]["by_outcome"]["sbp_change_wk8"]
    b["poolable_reason"] = (
        "TWO TRIALS RANDOMISE THE SAME FIXED-DOSE COMBINATION AGAINST THE SAME COMPARATOR AND "
        "REGISTER THE SAME CONTINUOUS ENDPOINT. Nothing had to be harmonised: this review's "
        "question was already a question, its estimand was already shared, and its arms "
        "already matched. WHAT IT LACKED WAS ANY EVIDENCE THAT THESE WERE THE ONLY TWO, and "
        "the executed search of 2026-08-19 supplies it -- 57 registrations screened, 53 "
        "excluded, and only FOUR carrying both arms of the contrast at all. The other two are "
        "long-term open-label SAFETY studies that register no blood-pressure change outcome at "
        "any rank, so they are ELIGIBLE AND NOT POOLABLE rather than absent.")
    b["what_the_check_changed"] = {
        "headline": "NOTHING MOVED, AND THAT IS THE RESULT.",
        "old": {"k": 2, "n": 2156, "md": b["pooled"]["point"],
                "ci_low": b["pooled"]["ci_low"], "ci_high": b["pooled"]["ci_high"],
                "i2": (b.get("heterogeneity") or {}).get("i2")},
        "new": {"k": 2, "n": 2156, "md": b["pooled"]["point"],
                "ci_low": b["pooled"]["ci_low"], "ci_high": b["pooled"]["ci_high"],
                "i2": (b.get("heterogeneity") or {}).get("i2")},
        "what_moved": ("No trial joined and none left. The pooled estimate is unchanged to "
                       "every digit."),
        "why_that_is_a_finding_and_not_a_null_result": (
            "BEFORE THE SEARCH, THIS REVIEW'S TWO TRIALS WERE THE TWO SOMEBODY PUT ON A PAGE. "
            "They are now the two that the whole 57-record azilsartan programme supports, and "
            "the difference between those two states is invisible from the outside -- a "
            "correct included set and an unexamined one look identical. The check is what "
            "distinguishes them, and it is worth the same when it confirms."),
        "the_third_direction": (
            "Second instance in one day, by a different route. bococizumab's evidence base was "
            "checked and gained a trial; this one was checked and gained none; apixaban's "
            "withholding question moved one poolable set UP and another DOWN. A procedure "
            "whose answers were always convenient would be indistinguishable from no "
            "procedure."),
    }

    # P22: SHARING, COMPUTED AGAINST THE WHOLE CORPUS. Both of this review's trials are
    # head-to-heads of two named combinations, so they are naturally also the evidence base of
    # the OTHER drug's topic. Legitimate, and unrecorded sharing is not -- a corpus-level k
    # obtained by summing per-topic k double-counts them.
    ssot_dir = os.path.join(REPO, "ssot")
    mine = [t.get("nct") for t in obj["inputs"]["trials"] if t.get("nct")]
    found, checked = {}, 0
    for d in sorted(os.listdir(ssot_dir)):
        if d == TOPIC:
            continue
        p2 = os.path.join(ssot_dir, d, d + ".json")
        if not os.path.exists(p2):
            continue
        checked += 1
        try:
            with io.open(p2, encoding="utf-8") as fh:
                o2 = json.load(fh)
        except (ValueError, OSError):
            continue
        their = {t.get("nct") for t in ((o2.get("inputs") or {}).get("trials") or [])}
        for n in mine:
            if n in their:
                found.setdefault(n, []).append(d)
    obj["shared_with_other_topics"] = {
        "computed": True,
        "computed_against": ("every other topic object under ssot/ -- %d checked -- by reading "
                             "each one's inputs.trials. Not asserted." % checked),
        "shared": {n: {"also_in": ts,
                       "why": ("A HEAD-TO-HEAD OF TWO NAMED COMBINATIONS IS THE EVIDENCE BASE "
                               "OF BOTH DRUGS' TOPICS. The sharing is a property of the trial "
                               "design, not of two reviews independently reaching for the same "
                               "record, and it is recorded on this side whether or not the "
                               "other side records it.")}
                   for n, ts in sorted(found.items())},
        "summing_per_topic_k_double_counts": (
            "A CORPUS-LEVEL k OBTAINED BY SUMMING PER-TOPIC k DOUBLE-COUNTS. %d of this "
            "review's %d trials are also held elsewhere -- which for a two-trial review is "
            "the whole of it." % (len(found), len(mine))),
    }

    after = set(obj)
    lost = before - after
    if lost:
        raise SystemExit("REFUSED: merging would drop top-level key(s) %s." % sorted(lost))
    with io.open(DEST, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(obj, indent=1))
    print("top-level keys before %d, after %d, lost %d" % (len(before), len(after), len(lost)))
    print("k unchanged at %s   MD unchanged at %s" % (b["k"], b["pooled"]["point"]))
    print("wrote %s" % DEST)
    return 0


if __name__ == "__main__":
    sys.exit(main())
