"""Validate the trial-identity rule against the REAL mismatches, not three exemplars.

MAHMOOD: "Validate against all 33 known mismatches, not just the three: a matcher that passes
its three exemplars and fails the other 30 would be the vocabulary-versus-property error
again."

AND THE SWEEP'S LABELS ARE NOT THE REFERENCE STANDARD. An earlier version of this file
validated the rule against the ROLE labels the sweep assigned. Those labels are unverified
model output, and at least one is wrong: the sweep called apixaban the COMPARATOR in RAMBLE,
where the registry shows two ACTIVE_COMPARATOR arms and apixaban as the hypothesised better
one. The sweep got the right verdict for the wrong reason -- RAMBLE does not belong on an
apixaban VTE page because it measures MENSTRUAL BLOOD LOSS. Validating an arm-role rule
against that label would have written the error into a gate permanently.

SO THE CASES BELOW USE ARM STRUCTURES READ FROM ClinicalTrials.gov API v2 ON 2026-08-25,
copied verbatim, and each expected answer is a fact that can be checked by opening the
registration. That is a reference standard that has itself been audited.
"""
import io
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "ssot"))
sys.path.insert(0, os.path.join(REPO, "scripts"))
import trial_identity as T
import instrument_controls

SWEEP = os.path.join(REPO, "outputs", "trial_identity_sweep_2026_08_25.jsonl")


# Arm structures copied VERBATIM from ClinicalTrials.gov API v2 on 2026-08-25:
#   GET /api/v2/studies/<NCT>?fields=protocolSection.armsInterventionsModule
# Each is a fact a reader can check by opening the registration.
REAL_ARMS = {
    "NCT02270242": [  # TWILIGHT
        ("ACTIVE_COMPARATOR", ["Drug: Aspirin", "Drug: ticagrelor"]),
        ("PLACEBO_COMPARATOR", ["Drug: Placebo", "Drug: ticagrelor"])],
    "NCT02829957": [  # RAMBLE
        ("ACTIVE_COMPARATOR", ["Drug: Rivaroxaban"]),
        ("ACTIVE_COMPARATOR", ["Drug: Apixaban"])],
    "NCT03840148": [  # cefepime/taniborbactam
        ("EXPERIMENTAL", ["Drug: Cefepime/VNRX-5133 (taniborbactam)"]),
        ("ACTIVE_COMPARATOR", ["Drug: Meropenem"])],
    "NCT03630081": [  # WCK 4282 -- the CORRECT cefepime-tazobactam trial
        ("EXPERIMENTAL", ["Drug: WCK 4282 (FEP-TAZ) 4 g"]),
        ("ACTIVE_COMPARATOR", ["Drug: Meropenem"])],
    "NCT00391872": [  # PLATO
        ("ACTIVE_COMPARATOR", ["Drug: Clopidogrel"]),
        ("EXPERIMENTAL", ["Drug: Ticagrelor"])],
}


def arms(nct):
    return [{"type": t, "interventionNames": n} for t, n in REAL_ARMS[nct]]


NAMED = [
    ("BACKGROUND -- TWILIGHT gives ticagrelor in both arms",
     ["ticagrelor"], "NCT02270242", False),
    ("TWILIGHT's real contrast, aspirin, must still pass",
     ["aspirin"], "NCT02270242", True),
    ("HEAD-TO-HEAD -- RAMBLE has no EXPERIMENTAL arm; apixaban IS studied",
     ["apixaban"], "NCT02829957", True),
    ("HEAD-TO-HEAD -- and so is rivaroxaban",
     ["rivaroxaban"], "NCT02829957", True),
    # EXPECTATION CHANGED 2026-08-25, and the reason is recorded because changing a test
    # until it passes is the easiest way to launder a bad rule.
    #
    # This case originally expected False, from a rule that rejected ANY combination
    # containing the pattern. Run over the corpus that rule rejected 9 of 12 combination
    # cases WRONGLY -- sacubitril against "Sacubitril/valsartan" (ARNI's own drug),
    # ceftolozane against "Ceftolozane/tazobactam", casirivimab against
    # "casirivimab+imdevimab", delamanid against "Delamanid + OBR". Each rejection would
    # have deleted real evidence.
    #
    # The principle that explains all twelve: a combination CONTAINING the subject drug IS a
    # trial of that drug; what is not is a combination with a DIFFERENT PARTNER from the one
    # the topic specifies. A bare "cefepime" specifies no partner, so it conflicts with
    # nothing and correctly matches here.
    #
    # CEFEPIME_TAZ's real defect therefore is NOT in this rule. It is in TOPICS, which
    # supplies the pattern "cefepime" for a topic whose drug is cefepime-TAZOBACTAM. The
    # next case pins that down, so the defect stays visible rather than being absorbed.
    ("bare 'cefepime' specifies no partner, so it legitimately matches any cefepime combination",
     ["cefepime"], "NCT03840148", True),
    ("...and the CORRECT pattern rejects it, which is why CEFEPIME_TAZ's fault is its TOPICS entry",
     ["cefepime tazobactam"], "NCT03840148", False),
    ("COMBINATION -- taniborbactam is not tazobactam",
     ["cefepime tazobactam"], "NCT03840148", False),
    ("the CORRECT trial matches through its code name",
     ["wck 4282"], "NCT03630081", True),
    ("ordinary case -- PLATO's experimental arm",
     ["ticagrelor"], "NCT00391872", True),
    # EXPECTATION CHANGED 2026-08-25, second time, and again with the reason inline.
    #
    # This expected False: clopidogrel sits in PLATO's ACTIVE_COMPARATOR arm, so it is not
    # what PLATO tests. That reading is correct for PLATO and unsafe as a RULE, because the
    # arm-type label demonstrably does not track which drug is under test:
    #
    #   NCT00423319  labels the ENOXAPARIN arm EXPERIMENTAL and the APIXABAN arm
    #                ACTIVE_COMPARATOR, on a trial whose title calls apixaban the
    #                investigational drug.
    #   NCT00468923  HOPE-3 labels its real rosuvastatin arm PLACEBO_COMPARATOR.
    #
    # The field is right sometimes, which is worse than always wrong because it invites a
    # rule like the one I wrote. Comparator-only is now UNDECIDABLE: 16 verdicts given up to
    # avoid accusing a page on a field that lies. The one class needing no label survives --
    # a drug in EVERY arm is background whatever the arms are called.
    ("COMPARATOR -- unsafe to call from arm type, so UNDECIDABLE not False",
     ["clopidogrel"], "NCT00391872", None),
]


def main():
    print("== CASES, on arm structures read from the live registry")
    failed = []
    for label, pats, nct, want in NAMED:
        got, why = T.studies_subject(pats, arms(nct))
        ok = (got is None) if want is None else (got == want)
        print("  %-4s %-58s %s" % ("PASS" if ok else "FAIL", label, why[:56]))
        if not ok:
            failed.append(label)

    got, why = T.studies_subject(["dabigatran"], None)
    print("  %-4s %-58s %s" % ("PASS" if got else "FAIL",
                               "UNKNOWN arms must not be read as NO", why[:56]))
    if not got:
        failed.append("unknown-is-not-no")

    if failed:
        print()
        print("REFUSED: %d case(s) failed: %s. NO further claim is made about the rule."
              % (len(failed), "; ".join(failed)))
        return 1

    instrument_controls.require_controls(
        "trial-identity-rule",
        ("nine cases spanning background, head-to-head, combination, comparator and "
         "unknown, each checkable against its registration", len(failed), 0),
        ("a plain experimental-arm match, which must NOT be rejected",
         T.studies_subject(["ticagrelor"], arms("NCT00391872"))[0], False))

    print()
    print("VALIDATED ON: nine registry-checked cases plus the unknown-arms guard.")
    print("NOT VALIDATED ON: the corpus. Doing that needs arm structures for all 349 NCT")
    print("ids the objects name. Those are fetchable from the same public API -- no AACT")
    print("snapshot and no credentials -- and that fetch is the next step, not a blocker.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
