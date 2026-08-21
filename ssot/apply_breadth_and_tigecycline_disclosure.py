"""Two disclosures a reader is owed, rendered beside the estimates they qualify.

ONE -- THE BREADTH DEFICIT, ON THE FOUR TOPICS WHERE IT IS ESTABLISHED.

Class 82 measured it: across 18 topics with a published comparison, 9 appraised reviews
state a trial count, and OURS IS LOWER ON FOUR AND HIGHER ON NONE. Until now a reader met
our estimate with no indication that a larger evidence base exists. THAT IS THE WITHHOLDING
FAILURE IN ITS MOST CONSEQUENTIAL FORM -- not a refusal we hid, but a SCOPE we did not
disclose.

    topic                     ours   theirs   set
    sglt2-mace-cvot-review      2      3      IDENTIFIED -- the third is CANVAS, named in
                                              the title of Kluger et al. 2018
    incretin-hfpef-review       2      4      counted, NOT identified
    nirsevimab-infant-rsv       2      6      counted, NOT identified
    attr-pn-review              3     10      counted, NOT identified

THE WORDING IS DELIBERATE AND DOES NOT SAY WHAT WE DO NOT KNOW. On three of the four the
abstract names no trials and no included-study table was read, so the difference is A
DIFFERENCE IN STATED COUNTS AND NOTHING MORE. Writing "four trials we missed" would assert
an identification nobody has made. Only sglt2-mace-cvot names its extra trial.

TWO -- TIGECYCLINE, WHERE OUR OWN STATED METHOD CONTRADICTS OUR OWN DELIVERED CLAIM.

Three facts, and together they mean the page's conclusion is not supported by this project's
own rule:

    the delivered interval        RR 0.9351 (0.8885 to 0.9842) -- EXCLUDES no difference
    this project's own Hartung-   RR 0.9351 (0.8327 to 1.0501) on t = 4.3027, 2 df --
      Knapp interval at k = 3       INCLUDES no difference
    a fifteen-study network       "No differences in clinical and microbiological outcomes
      (PMID 31577763)               were observed between different carbapenems and TGC"

The house rule already says Hartung-Knapp is shown BESIDE the unadjusted interval where k is
small, because that is the honest width. On this topic the two intervals disagree about the
conclusion, and only the reassuring one was reaching the reader.

    THIS IS THE CLASS WHERE WE HAVE BEEN PENALISING HONEST PAGES WHILE LETTING AN UNEARNED
    CONCLUSION STAND. A page that refuses is marked incomplete; a page that concludes more
    than its method supports has been passing.

NO STORED NUMBER IS CHANGED BY EITHER DISCLOSURE.
"""
import io
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "ssot"))
import atomic_write

TODAY = "2026-08-21"
STAMP = TODAY.replace("-", "_")

BREADTH = {
    "sglt2-mace-cvot-review": {
        "outcome": "primary", "ours": 2, "theirs": 3, "identified": True,
        "citation": ("Kluger et al., Reviews in Cardiovascular Medicine 2018, PMID 31032602, "
                     "'Cardiorenal Outcomes in the CANVAS, DECLARE-TIMI 58, and EMPA-REG "
                     "OUTCOME Trials'"),
        "extra": ("THE THIRD TRIAL IS NAMED: the CANVAS Program. It is in the title of the "
                  "review and is not carried by this object. THIS IS THE ONLY TOPIC IN THE "
                  "CORPUS WHERE A TRIAL WE DO NOT POOL CAN BE NAMED."),
    },
    "incretin-hfpef-review": {
        "outcome": "primary", "ours": 2, "theirs": 4, "identified": False,
        "citation": ("Musa & Musa, BMC Cardiovascular Disorders 2026, PMID 41906074, a "
                     "prospectively registered systematic review (CRD420251237462)"),
        "extra": None,
    },
    "nirsevimab-infant-rsv-review": {
        "outcome": "primary", "ours": 2, "theirs": 6, "identified": False,
        "citation": ("Lien et al., Pediatrics and Neonatology 2026, PMID 41314935, six "
                     "randomised trials totalling 12,086 participants"),
        "extra": None,
    },
    "attr-pn-review": {
        "outcome": "primary", "ours": 3, "theirs": 10, "identified": False,
        "citation": ("Karimi et al., Frontiers in Neurology 2024, PMID 39286810, ten studies "
                     "across 756 patients"),
        "extra": ("SEPARATELY, this pool is already REFERRED on an obstacle in the evidence: "
                  "a published feasibility assessment found a network meta-analysis of these "
                  "treatments NOT FEASIBLE on cross-trial heterogeneity."),
    },
}


def main():
    dry = "--apply" not in sys.argv

    for topic, spec in sorted(BREADTH.items()):
        path = os.path.join(REPO, "ssot", topic, topic + ".json")
        obj = json.load(io.open(path, encoding="utf-8"))
        blk = ((obj.get("results") or {}).get("by_outcome") or {}).get(spec["outcome"])
        if not isinstance(blk, dict):
            sys.exit("REFUSED: %s has no `%s`." % (topic, spec["outcome"]))
        declared = [d.get("id") for d in (obj.get("outcomes") or []) if isinstance(d, dict)]
        if spec["outcome"] not in declared:
            sys.exit("REFUSED: `%s` is not declared on %s, so a finding attached to it would "
                     "not render." % (spec["outcome"], topic))

        f = {
            "a_a_published_synthesis_carried_more_trials_than_this_pool": (
                "A PUBLISHED SYNTHESIS OF THIS QUESTION INCLUDED %d TRIALS WHERE THIS POOL "
                "CARRIES %d. Source: %s."
                % (spec["theirs"], spec["ours"], spec["citation"])),
            "b_whether_the_extra_trials_can_be_named": (
                spec["extra"] if spec["identified"] and spec["extra"] else
                ("WHICH TRIALS ARE ABSENT IS NOT ESTABLISHED. The published abstract names "
                 "none of its included studies and no included-study table was read, so this "
                 "is A DIFFERENCE IN STATED COUNTS AND NOTHING MORE. It is NOT a claim that "
                 "%d specific trials were missed, and nobody here has identified them."
                 % (spec["theirs"] - spec["ours"]))),
            "c_what_this_means_for_the_estimate_above": (
                "The estimate above is computed from the trials this object carries and is "
                "not withdrawn or altered by this note. What a reader is owed is the SCOPE: "
                "a larger evidence base on this question exists in the literature, and "
                "whether this review's search should be widened is a decision that has not "
                "been made."),
        }
        if spec["extra"] and not spec["identified"]:
            f["d_also_recorded"] = spec["extra"]

        prior = blk.get("POOL_FINDINGS_%s" % STAMP) or {}
        prior.update(f)
        blk["POOL_FINDINGS_%s" % STAMP] = prior
        obj.setdefault("display_change_announced", []).append({
            "date": TODAY,
            "change": "the breadth deficit now renders beside the estimate",
            "values_moved": "NONE",
            "what_changed": "a published synthesis carried %d trials against this pool's %d"
                            % (spec["theirs"], spec["ours"]),
            "why": ("A reader met the estimate with no indication that a larger evidence "
                    "base exists. Class 82."),
        })
        print("%-32s breadth disclosed: ours %d, theirs %d, %s"
              % (topic[:32], spec["ours"], spec["theirs"],
                 "IDENTIFIED" if spec["identified"] else "counted only"))
        if not dry:
            atomic_write.write_json(path, obj, indent=1)

    # ---- TIGECYCLINE ---------------------------------------------------------------------
    path = os.path.join(REPO, "ssot", "tigecycline-ciai", "tigecycline-ciai.json")
    obj = json.load(io.open(path, encoding="utf-8"))
    blk = ((obj.get("results") or {}).get("by_outcome") or {}).get("cure_toc_me")
    hk = blk.get("pooled_hartung_knapp") or {}
    p = blk.get("pooled") or {}
    prior = blk.get("POOL_FINDINGS_%s" % STAMP) or {}
    prior.update({
        "e_the_inferiority_reading_does_not_survive_this_project_s_own_adjustment": (
            "READ THIS BEFORE THE INTERVAL ABOVE. The estimate is %s (%s to %s), which "
            "EXCLUDES no difference and reads as tigecycline being inferior on clinical "
            "cure. THIS PROJECT'S OWN HARTUNG-KNAPP INTERVAL AT k = 3 IS 0.8327 to 1.0501, "
            "on a t critical value of 4.3027 with 2 degrees of freedom, AND IT INCLUDES NO "
            "DIFFERENCE. The house rule already requires the adjusted interval to be shown "
            "beside the unadjusted one where k is small, because that is the honest width; "
            "on this pool the two disagree about the conclusion."
            % (p.get("point"), p.get("ci_low"), p.get("ci_high"))),
        "f_and_a_fifteen_study_network_reached_the_same_conclusion_as_the_adjusted_interval": (
            "Yu et al., Medicine 2019, PMID 31577763, a Bayesian network meta-analysis of "
            "FIFTEEN STUDIES and 6,745 participants, concluded: 'No differences in clinical "
            "and microbiological outcomes were observed between different carbapenems and "
            "TGC.' THE ADJUSTED INTERVAL AND THE LARGER LITERATURE AGREE WITH EACH OTHER AND "
            "NOT WITH THE UNADJUSTED READING."),
        "g_what_has_and_has_not_been_done": (
            "THE STORED ESTIMATE IS NOT CHANGED. Withdrawing or restating a published number "
            "is a content decision. What has been done is to put the adjusted interval and "
            "the disagreement where a reader meets the number, because a page that concludes "
            "more than its own stated method supports had been passing while pages that "
            "refuse honestly are marked incomplete."),
    })
    blk["POOL_FINDINGS_%s" % STAMP] = prior
    obj.setdefault("display_change_announced", []).append({
        "date": TODAY,
        "change": "the small-sample sensitivity interval now renders beside the estimate",
        "values_moved": "NONE",
        "what_changed": ("the unadjusted interval excludes no difference and the "
                         "Hartung-Knapp interval at k=3 includes it"),
        "why": "Our own stated method contradicted our own delivered conclusion.",
    })
    print("%-32s sensitivity interval disclosed (HK %s to %s)"
          % ("tigecycline-ciai", hk.get("ci_low", "0.8327"), hk.get("ci_high", "1.0501")))
    if dry:
        print("DRY RUN -- pass --apply to write")
        return
    atomic_write.write_json(path, obj, indent=1)


if __name__ == "__main__":
    main()
