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
    ("COMBINATION -- bare 'cefepime' must not match cefepime/VNRX-5133",
     ["cefepime"], "NCT03840148", False),
    ("COMBINATION -- taniborbactam is not tazobactam",
     ["cefepime tazobactam"], "NCT03840148", False),
    ("the CORRECT trial matches through its code name",
     ["wck 4282"], "NCT03630081", True),
    ("ordinary case -- PLATO's experimental arm",
     ["ticagrelor"], "NCT00391872", True),
    ("COMPARATOR -- clopidogrel holds only PLATO's control arm",
     ["clopidogrel"], "NCT00391872", False),
]


def main():
    print("== CASES, on arm structures read from the live registry")
    failed = []
    for label, pats, nct, want in NAMED:
        got, why = T.studies_subject(pats, arms(nct))
        ok = (got == want)
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
