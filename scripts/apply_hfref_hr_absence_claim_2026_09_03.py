"""HFrEF: the page said no trial supplies a hazard ratio, and eight of them do.

THE CLAIM, AS SERVED. HFREF_NMA_AUTO_FULL_REVIEW.html, Methods, Effect Measure cell:

    "No published hazard ratio enters the settled fit: no trial in this network supplies
     one, so the Primary/AUTO setting resolves to RR."

THE SAME CELL REFUTES IT TWO SENTENCES LATER, with no external source needed:

    "The HR-derived EMPEROR-Reduced input, log(0.92) with SE from the published 95% CI
     0.77-1.10, is used only by the separate calibration cell..."

EMPEROR-Reduced (HF-033) is a trial in this network. A cell that uses a trial's published
hazard ratio cannot also say no trial in the network supplies one. THIS IS THE SHARPEST
FORM OF THE CLASS scripts/lint_refusal_contradicted_by_its_own_section.py polices: a
denial refuted by its own bytes, where the refutation is one paragraph away.

AND IT IS NOT A NEAR MISS. Eight trials in the 28 supply a published all-cause-mortality
hazard ratio. Six come from the trials' OWN REGISTRY RESULTS, fetched 2026-09-03 from
ClinicalTrials.gov API v2 and stored beside this script:

    EMPHASIS-HF     NCT00232180   0.761 (0.622 to 0.932)   "First Occurrence of All-Cause
                                                            Mortality (Adjudicated)"
    J-EMPHASIS-HF   NCT01115855   1.77  (0.81  to 3.87)
    DAPA-HF         NCT03036124   0.83  (0.71  to 0.97)
    EMPEROR-Reduced NCT03057977   0.92  (0.77  to 1.10)
    GALACTIC-HF     NCT02929329   1.00  (0.92  to 1.09)
    VICTOR          NCT05093933   0.84  (0.74  to 0.97)

and two from the primary publications, read from the PubMed abstract:

    PARADIGM-HF     PMID 25176015 "hazard ratio for death from any cause, 0.84"
    DIGIT-HF        PMID 40879434 "hazard ratio, 0.86"

VICTOR's abstract also states the arm counts the page stores -- 377 (12.3%) versus 440
(14.4%) -- so the same source that supplies the hazard ratio confirms the counts the fit
uses. The trial is not obscure to this page; only its hazard ratio was.

WHAT THE CORRECTED SENTENCE SAYS, AND WHAT IT DOES NOT. It says the fit uses log RR by
CHOICE and names what that choice discards. It does NOT claim the choice is wrong -- that
is a separate question about a common estimand across unequal follow-up, handled
separately. An absence claim is replaced by a decision, which is what it always was.

TWO COPIES, AND BOTH MUST CHANGE. The sentence appears TWICE in the served bytes:

    offset 158422   static HTML, inside <td id="protocol-em-desc">
    offset 328812   inside <script>, assigned to protDesc.textContent

The second is a run-time template: it rewrites the same cell when the effect-measure
toggle resolves to AUTO. FIXING ONLY THE STATIC COPY WOULD LEAVE A PAGE THAT TELLS THE
TRUTH UNTIL THE READER TOUCHES A CONTROL, AND THEN LIES. Because the JS copy is assigned
to .textContent, an HTML entity there would render literally, and because it sits in a
double-quoted JS string a double quote there would break the script -- so the replacement
is plain ASCII with single quotes, identical in both positions.

PLANTED BOTH WAYS. The old sentence is asserted present exactly twice before and absent
after; the new sentence is asserted present exactly twice after; the page's div balance
and the JS string quoting are checked after the write.

Usage:  python scripts/apply_hfref_hr_absence_claim_2026_09_03.py [--check]
"""
from __future__ import annotations

import io
import json
import os
import re
import sys

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = os.path.join(REPO, "HFREF_NMA_AUTO_FULL_REVIEW.html")
OUT = os.path.join(REPO, "out", "hfref_published_hr_inventory_2026_09_03.json")

OLD = ("No published hazard ratio enters the settled fit: no trial in this network "
       "supplies one, so the Primary/AUTO setting resolves to RR.")

NEW = ("No published hazard ratio enters the settled fit: every contrast is rebuilt from "
       "per-arm counts, so the Primary/AUTO setting resolves to RR. That is a CHOICE, not "
       "an absence. Eight trials in this network do publish an all-cause-mortality hazard "
       "ratio -- EMPHASIS-HF 0.761 (0.622 to 0.932), J-EMPHASIS-HF 1.77 (0.81 to 3.87), "
       "DAPA-HF 0.83 (0.71 to 0.97), EMPEROR-Reduced 0.92 (0.77 to 1.10), GALACTIC-HF 1.00 "
       "(0.92 to 1.09) and VICTOR 0.84 (0.74 to 0.97) in their own ClinicalTrials.gov "
       "results, PARADIGM-HF 0.84 and DIGIT-HF 0.86 in their primary publications -- and "
       "none of them enters the fit. Until 2026-09-03 this cell read 'no trial in this "
       "network supplies one', which its own next sentence refuted by using an "
       "EMPEROR-Reduced hazard ratio.")

# Every value above, with the source it was read from. Nothing here is recalled.
INVENTORY = [
    {"id": "HF-023", "name": "EMPHASIS-HF", "hr": 0.761, "lo": 0.622, "hi": 0.932,
     "outcome": "Number of Participants With First Occurrence of All-Cause Mortality "
                "(Adjudicated)",
     "source": "https://clinicaltrials.gov/api/v2/studies/NCT00232180?format=json",
     "source_kind": "registry results", "fetched_utc": "2026-09-03"},
    {"id": "HF-024", "name": "J-EMPHASIS-HF", "hr": 1.77, "lo": 0.81, "hi": 3.87,
     "outcome": "Number of Participants With With First Occurrence of All-Cause Mortality",
     "source": "https://clinicaltrials.gov/api/v2/studies/NCT01115855?format=json",
     "source_kind": "registry results", "fetched_utc": "2026-09-03"},
    {"id": "HF-032", "name": "DAPA-HF", "hr": 0.83, "lo": 0.71, "hi": 0.97,
     "outcome": "Subjects Included in the Endpoint of All-cause Mortality.",
     "source": "https://clinicaltrials.gov/api/v2/studies/NCT03036124?format=json",
     "source_kind": "registry results", "fetched_utc": "2026-09-03"},
    {"id": "HF-033", "name": "EMPEROR-Reduced", "hr": 0.92, "lo": 0.77, "hi": 1.10,
     "outcome": "Time to All-cause Mortality",
     "source": "https://clinicaltrials.gov/api/v2/studies/NCT03057977?format=json",
     "source_kind": "registry results", "fetched_utc": "2026-09-03",
     "note": "this is the very hazard ratio the same cell says it uses for calibration"},
    {"id": "HF-034", "name": "GALACTIC-HF", "hr": 1.00, "lo": 0.92, "hi": 1.09,
     "outcome": "Time to All-cause Death",
     "source": "https://clinicaltrials.gov/api/v2/studies/NCT02929329?format=json",
     "source_kind": "registry results", "fetched_utc": "2026-09-03"},
    {"id": "HF-036", "name": "VICTOR", "hr": 0.84, "lo": 0.74, "hi": 0.97,
     "outcome": "Time to All-Cause Mortality: Participants With an Event Per 100 "
                "Patient-Years",
     "source": "https://clinicaltrials.gov/api/v2/studies/NCT05093933?format=json",
     "source_kind": "registry results", "fetched_utc": "2026-09-03",
     "note": "the same abstract states 377 (12.3%) versus 440 (14.4%), which are the arm "
             "counts this page stores"},
    {"id": "HF-030", "name": "PARADIGM-HF", "hr": 0.84, "lo": None, "hi": None,
     "outcome": "death from any cause",
     "source": "PubMed abstract, PMID 25176015: 'hazard ratio for death from any cause, "
               "0.84'",
     "source_kind": "publication abstract", "fetched_utc": "2026-09-03",
     "interval_note": "the abstract sentence this was read from does not carry the "
                      "interval; it is UNRECORDED here rather than filled in from memory"},
    {"id": "HF-037", "name": "DIGIT-HF", "hr": 0.86, "lo": None, "hi": None,
     "outcome": "death from any cause",
     "source": "PubMed abstract, PMID 40879434: 'hazard ratio, 0.86'",
     "source_kind": "publication abstract", "fetched_utc": "2026-09-03",
     "interval_note": "interval not carried in the sentence read; UNRECORDED"},
]


def read_page():
    return io.open(PAGE, encoding="utf-8", errors="replace", newline="").read()


def main(argv):
    body = read_page()
    n_old, n_new = body.count(OLD), body.count(NEW)
    print("PAGE  %s" % os.path.basename(PAGE))
    print("  the false absence claim, occurrences: %d" % n_old)
    print("  the corrected sentence, occurrences:  %d" % n_new)
    for i, m in enumerate(re.finditer(re.escape(OLD), body)):
        in_script = any(a <= m.start() < b for a, b in
                        [(x.start(), x.end())
                         for x in re.finditer(r"<script.*?</script>", body, re.S)])
        print("     occurrence %d at offset %d  %s"
              % (i + 1, m.start(), "inside <script>" if in_script else "static HTML"))

    if "--check" in argv:
        if n_old:
            print("\n-> FAILED: the false absence claim is still served in %d place(s)."
                  % n_old)
            return 1
        if n_new != 2:
            print("\n-> FAILED: the corrected sentence appears %d times; both the static "
                  "cell and the run-time template must carry it." % n_new)
            return 1
        print("\n-> ok: the claim is corrected in both places.")
        return 0

    if n_old == 0 and n_new == 2:
        print("\n-> ok: already applied; nothing to write.")
    else:
        if n_old != 2:
            print("\n  REFUSED: expected the claim in exactly 2 places, found %d. A "
                  "replacement that cannot find what it was written for must not guess."
                  % n_old)
            return 1
        body2 = body.replace(OLD, NEW)
        # PLANTED BOTH WAYS.
        fails = []
        if OLD in body2:
            fails.append("the false claim survives the replacement")
        if body2.count(NEW) != 2:
            fails.append("the corrected sentence appears %d times, expected 2"
                         % body2.count(NEW))
        if len(re.findall(r"<div[\s>]", body2)) != len(re.findall(r"</div>", body2)):
            fails.append("div balance changed")
        if '"' in NEW:
            fails.append("the replacement carries a double quote and one copy lives in a "
                         "double-quoted JS string")
        if "&" in NEW:
            fails.append("the replacement carries an entity and one copy is assigned to "
                         ".textContent, where it would render literally")
        if fails:
            for f in fails:
                print("  REFUSED: %s" % f)
            return 1
        io.open(PAGE, "w", encoding="utf-8", newline="").write(body2)
        print("\n-> rewrote both copies of the sentence in %s" % os.path.basename(PAGE))

    rec = {"utc": "2026-09-03", "page": os.path.basename(PAGE),
           "claim_removed": OLD,
           "refuted_internally_by":
               "the next sentence of the same cell, which uses the EMPEROR-Reduced "
               "published hazard ratio log(0.92), CI 0.77-1.10",
           "trials_in_network": 28,
           "trials_supplying_a_published_all_cause_mortality_HR": len(INVENTORY),
           "inventory": INVENTORY,
           "not_established":
               "This does NOT establish that the network SHOULD be fitted on hazard "
               "ratios. It establishes that the stated reason for not doing so was false."}
    io.open(OUT, "w", encoding="utf-8", newline="\n").write(json.dumps(rec, indent=1))
    print("   wrote %s  (%d of 28 trials supply a published HR)"
          % (os.path.relpath(OUT, REPO), len(INVENTORY)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
