# -*- coding: utf-8 -*-
"""Controls for `audit_trial_label_identity`, including the one that rejected a tightening.

⛔ WHY THIS FILE EXISTS. The label audit was tightened three times in one session against
the same nine cases, which is fitting an instrument to its own validation set. Two of those
tightenings were right and ONE WAS NOT -- and the only reason the bad one did not ship is
that a control asserted DETECTION OF THE REAL SWAP rather than merely the absence of false
positives.

⭐ THE REJECTED TIGHTENING, kept here because the reasoning was good and the result was
wrong. "A swap is reciprocal: A wears B's name AND B wears A's" is exactly what `swapped`
means, and requiring it cleared both remaining false positives. It also reported ZERO on the
agyw swap -- the defect the module was written from -- because both dapivirine records
contain the word "Ring" (they are both vaginal RING trials), so "The Ring Study" fits each
equally and the reciprocal half can never be strict. A TEST THAT SILENCES ITS FOUNDING CASE
IS NOT A STRICTER TEST, IT IS A BROKEN ONE.

⇒ A control suite for a detector needs BOTH arms. Absence-of-false-positives alone is
satisfied perfectly by a detector that returns nothing, and every tightening moves toward
exactly that.

⚠️ AND CONTROL 1 EXPECTS 1, NOT 2, WHICH IS A MEASURED LIMIT AND NOT A CONVENIENCE.
The agyw defect occupied two sites. Only one is detectable from the registry:

    NCT01539226 labelled "ASPIRE / MTN-020"  -> caught. Neither `aspire` nor `mtn-020`
                                                appears in IPM 027's record; both appear
                                                in the sibling's. Unambiguous.
    NCT01617096 labelled "The Ring Study"    -> NOT caught, and cannot be. After generic
                                                words are removed the label reduces to the
                                                single token `ring`, which appears in BOTH
                                                records -- "Dapivirine Vaginal Matrix Ring"
                                                and "Dapivirine Vaginal Ring". The registry
                                                does not distinguish them on that word.

So this instrument detects a swapped OBJECT, not a swapped SITE, and the coverage claim
must be written that way. Raising the expectation to 2 would mean loosening the test until a
non-discriminating token counted as evidence, which is how the eight false positives were
produced in the first place.

Run: python scripts/control_label_audit.py
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import audit_trial_label_identity as A   # noqa: E402

# ClinicalTrials.gov values, read 2026-08-30. SYNTHETIC ONLY IN THE SENSE THAT THEY ARE
# PINNED: a control anchored to a live fetch retires itself the moment the registry edits a
# title, and then either fails for the wrong reason or passes for the wrong reason.
RECS = {
    "NCT01539226": {"brief": "Safety and Efficacy Trial of a Dapivirine Vaginal Matrix "
                             "Ring in Healthy HIV-Negative Women",
                    "acronym": "", "org": "IPM 027",
                    "countries": "South Africa Uganda"},
    "NCT01617096": {"brief": "Phase 3 Safety and Effectiveness Trial of Dapivirine Vaginal "
                             "Ring for Prevention of HIV-1",
                    "acronym": "ASPIRE", "org": "MTN-020",
                    "countries": "Malawi South Africa Uganda Zimbabwe"},
    "NCT02585713": {"brief": "Apixaban or Dalteparin in Reducing Blood Clots in Patients "
                             "With Cancer Related Venous Thromboembolism",
                    "acronym": "", "org": "RU221501I", "countries": "United States"},
    "NCT02583191": {"brief": "Rivaroxaban in the Treatment of Venous Thromboembolism (VTE) "
                             "in Cancer Patients",
                    "acronym": "", "org": "CONKO-011", "countries": "Germany"},
    "NCT00809965": {"brief": "An Efficacy and Safety Study for Rivaroxaban in Patients With "
                             "Acute Coronary Syndrome",
                    "acronym": "", "org": "CR014710", "countries": "many"},
    "NCT00402597": {"brief": "Rivaroxaban in Combination With Aspirin Alone or With Aspirin "
                             "and a Thienopyridine in Acute Coronary Syndromes",
                    "acronym": "", "org": "CR013417", "countries": ""},
}

CASES = [
    # (name, rows, expected inverted count, why this expectation)
    ("REAL agyw swap -- the founding defect",
     [("agyw-hiv-prep-review", "NCT01539226", "ASPIRE / MTN-020", "$.a"),
      ("agyw-hiv-prep-review", "NCT01617096", "The Ring Study", "$.b")], 1,
     "DETECTION ARM. One of the two sites is registry-distinguishable; see the module "
     "docstring. A change that drops this to 0 has broken the instrument, however many "
     "false positives it removes."),
    ("agyw after the correction",
     [("agyw-hiv-prep-review", "NCT01539226", "The Ring Study / IPM 027", "$.a"),
      ("agyw-hiv-prep-review", "NCT01617096", "ASPIRE / MTN-020", "$.b")], 0,
     "The fixed object must be clean, or the audit accuses its own repair."),
    ("ADAM VTE -- registry-settled CORRECT",
     [("doac-cancer-vte-review", "NCT02585713", "ADAM VTE", "$.a"),
      ("doac-cancer-vte-review", "NCT02583191", "CONKO-011", "$.b")], 0,
     "CT.gov spells out 'Venous Thromboembolism' for this trial and never abbreviates it, "
     "while a sibling's title contains the literal '(VTE)'. Without the topic-derived stop "
     "list the comparison is decided by the one token the whole review shares."),
    ("ATLAS ACS 2 -- registry-settled CORRECT",
     [("rivaroxaban-acs-review", "NCT00809965", "ATLAS ACS 2", "$.a"),
      ("rivaroxaban-acs-review", "NCT00402597", "ATLAS ACS TIMI 46", "$.b")], 0,
     "CT.gov lists the ATLAS acronym for neither trial, so the label's only distinguishing "
     "token is absent from both records and `acs` is the review's own subject."),
]


def main():
    A.registry = lambda ncts, chunk=40: {k: v for k, v in RECS.items() if k in ncts}
    ok = True
    print("CONTROLS FOR audit_trial_label_identity")
    print()
    for name, rows, expect, why in CASES:
        A.collect = lambda root=".", _r=rows: _r
        got = len(A.audit(".")["inverted"])
        good = got == expect
        ok = ok and good
        print("  %-42s inverted=%d expect=%d  %s"
              % (name[:42], got, expect, "PASS" if good else "FAIL"))
        if not good:
            print("      %s" % why)
    print()
    if not ok:
        print("REFUSED: a control failed. If the DETECTION arm failed, a tightening has")
        print("silenced the real swap -- absence of false positives is satisfied perfectly")
        print("by a detector that never reports anything.")
        return 1
    print("all controls pass -- both the detection arm and the three settled false positives")
    return 0


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.exit(main())
