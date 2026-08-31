# -*- coding: utf-8 -*-
"""Record FDA Integrated Review answers to RoB 2 signalling questions, per trial.

WHAT THIS WRITES, AND WHAT IT REFUSES TO WRITE.

Two FDA Integrated Reviews were fetched, their text extracted, and one assessor answered
five RoB 2 signalling questions against each with a verbatim quote. This records those
answers on the SSOT objects so `grade_engine` can re-derive the risk-of-bias domain
through the published algorithm instead of refusing.

⚠️ TRIAL COVERAGE IS VERIFIED, NOT ASSUMED. A regulatory review covers an APPLICATION,
which need not be every trial a topic pools. Checked before writing:

    sotagliflozin NDA216203  SCORED and SOLOIST-WHF both named in the review -> BOTH
    finerenone    NDA215341  FIDELIO 81 mentions; FIGARO exactly ONE, and it reads
                             "The Applicant also has an on-going ... trial (17530)
                             (FIGARO-DKD)" -- an ONGOING trial is not a reviewed one.
                             ⇒ FIDELIO (NCT02540993) ONLY. NCT02545049 gets nothing.

Attaching these answers to FIGARO would have been a real finding recorded against the
wrong trial, which is the failure this project has met before under the heading "a name
match is a filter, not an identity". Neither review contains any NCT identifier at all --
FDA writes acronyms and protocol numbers -- so the join is by acronym, checked by hand,
and recorded here rather than inferred at read time.

⚠️ ONE ASSESSOR, AND THE STORE SAYS SO. The corpus's own risk-of-bias assessments are dual
with an adjudication step. This is a single read of a named document, and it is recorded
as `n_assessors: 1` with `adjudicated: false` so no surface can mistake it for the
two-assessor product. It supplements a stored assessment; it does not replace one.

⚠️ AND BOTH CONCEALMENT ANSWERS ARE **INFERRED**, WHICH CORRECTS AN EARLIER REPORT. I had
described finerenone's as a clean STATED answer because it names the mechanism outright --
"Randomization was managed centrally using an interactive voice and web response system".
Under the tier definition actually written down, STATED means the document states the
PROPERTY, and neither review says allocation was concealed; both describe the mechanism.
So it is 0 of 2 STATED, 2 of 2 INFERRED. The two are still not equally direct -- one is a
sentence about how randomisation was run, the other mentions an IRT in passing inside a
sentence about a stratification discrepancy -- and the two-tier scheme does not capture
that difference. Recorded as a known limitation rather than resolved by widening a tier.
"""
import datetime
import hashlib
import io
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "ssot"))

import regulatory_evidence as R  # noqa: E402

UTC = datetime.datetime.now(datetime.timezone.utc).isoformat()

# Verbatim from the assessor's output; quotes checked to appear in the source text below.
EXTRACTED = {
    "finerenone": {
        "document": "FDA Integrated Review, NDA 215341 (KERENDIA, finerenone), 2021",
        "url": ("https://www.accessdata.fda.gov/drugsatfda_docs/nda/2021/"
                "215341Orig1s000IntegratedR.pdf"),
        "text": "F:/claude-temp/rm-dapivirine-2026-08-31/fda/finerenone_integratedR.txt",
        "trials": ["NCT02540993"],          # FIDELIO-DKD only. FIGARO is ongoing.
        "topic": "finerenone-cv",
        "answers": [
            ("1.1", "YES", R.STATED, "Design",
             "FIDELIO-DKD was a randomized, double-blind, parallel-group, event-driven "
             "trial comparing finerenone 10 mg or 20 mg once daily with placebo."),
            ("1.2", "YES", R.INFERRED, "Study Procedures",
             "Randomization was managed centrally using an interactive voice and web "
             "response system."),
            ("1.3", "NO", R.STATED, "Demographics and Baseline Clinical Characteristics",
             "Baseline demographics were well-balanced between the two treatment arms"),
            ("2.6", "PROBABLY_YES", R.STATED, "Efficacy Analyses",
             "Primary and secondary efficacy analyses for time to event variables were to "
             "be based on the FAS dataset."),
            ("3.1", "NO", R.STATED, "Missing Data and Sensitivity Analyses",
             "A total of 863 (15%) patients were missing complete data on the primary "
             "endpoint"),
            ("2.1", "NO", R.STATED, "Study Procedures",
             "The study was double-blinded using matching tablets in size, shape, and "
             "color for finerenone and placebo."),
            ("2.2", "NO", R.STATED, "Study Procedures",
             "to maintain the blinding of the investigator's team and patients"),
            ("2.3", "NA", R.INFERRED, "routed by RoB 2 from 2.1/2.2", ""),
            ("2.4", "NA", R.INFERRED, "routed by RoB 2 from 2.3", ""),
            ("2.5", "NA", R.INFERRED, "routed by RoB 2 from 2.4", ""),
            ("2.7", "NA", R.INFERRED, "routed by RoB 2 from 2.6", ""),
            ("3.2", "PROBABLY_YES", R.STATED, "Missing Data and Sensitivity Analyses",
             "the primary endpoint results were robust to various assumptions about the "
             "missing data"),
            ("3.3", "NA", R.INFERRED, "routed by RoB 2 from 3.2", ""),
            ("3.4", "NA", R.INFERRED, "routed by RoB 2 from 3.3", ""),
            ("4.1", "NO", R.INFERRED, "Efficacy Endpoints",
             "were both defined by evidence of at least two or more consecutive "
             "laboratory assessments"),
            ("4.2", "NO", R.INFERRED, "Study Procedures",
             "Endpoint assessments were performed at every visit starting with Visit 2"),
            ("4.3", "NO", R.STATED, "Study Procedures",
             "A Clinical Event Committee (CEC), which was blinded to study treatment "
             "assignment, adjudicated all events"),
            ("4.4", "NA", R.INFERRED, "routed by RoB 2 from 4.3", ""),
            ("4.5", "NA", R.INFERRED, "routed by RoB 2 from 4.4", ""),
        ],
    },
    "sotagliflozin": {
        "document": "FDA Integrated Review, NDA 216203 (sotagliflozin), 2023",
        "url": ("https://www.accessdata.fda.gov/drugsatfda_docs/nda/2023/"
                "216203Orig1s000IntegratedR.pdf"),
        "text": "F:/claude-temp/rm-dapivirine-2026-08-31/fda/sotagliflozin_integratedR.txt",
        "trials": ["NCT03315143", "NCT03521934"],   # SCORED and SOLOIST-WHF, both named.
        "topic": "sotagliflozin-hf",
        "answers": [
            ("1.1", "YES", R.STATED, "5.2.1. Trial Design",
             "subjects were randomized to sotagliflozin or matching placebo in a 1:1 "
             "ratio"),
            ("1.2", "PROBABLY_YES", R.INFERRED, "5.2.2. Statistical Analysis Plan",
             "discrepancy in stratum assignment between Interactive Response Technology "
             "(IRT) and eCRF occurred in more than 5% of patients"),
            ("1.3", "NO", R.STATED, "5.3. Results of Analyses of Clinical Trials",
             "patient baseline demographic and characteristics were generally balanced "
             "between treatment groups"),
            ("2.6", "YES", R.STATED, "5.2.2. Statistical Analysis Plan",
             "All efficacy analyses were performed based on the intention-to-treat (ITT) "
             "population"),
            ("3.1", "YES", R.STATED, "5.3. Results of Analyses of Clinical Trials",
             "the rate of missing data due to discontinuation of treatment/study and lost "
             "to follow-up appeared to be reasonably low in both trials"),
            ("2.1", "NO", R.INFERRED, "5.2.1. Trial Design",
             "SOLOIST and SCORED were randomized, placebo-controlled, parallel-group, "
             "multi-center, double-blind, trials comparing sotagliflozin to placebo"),
            ("2.2", "NO", R.INFERRED, "5.2.1. Trial Design",
             "SOLOIST and SCORED were randomized, placebo-controlled, parallel-group, "
             "multi-center, double-blind, trials comparing sotagliflozin to placebo"),
            ("2.3", "NA", R.INFERRED, "routed by RoB 2 from 2.1/2.2", ""),
            ("2.4", "NA", R.INFERRED, "routed by RoB 2 from 2.3", ""),
            ("2.5", "NA", R.INFERRED, "routed by RoB 2 from 2.4", ""),
            ("2.7", "NA", R.INFERRED, "routed by RoB 2 from 2.6", ""),
            ("3.2", "NA", R.INFERRED, "routed by RoB 2 from 3.1", ""),
            ("3.3", "NA", R.INFERRED, "routed by RoB 2 from 3.2", ""),
            ("3.4", "NA", R.INFERRED, "routed by RoB 2 from 3.3", ""),
            ("4.1", "NO", R.STATED, "5.3. Results of Analyses of Clinical Trials",
             "investigator-reported events was reasonable and is sufficient to establish "
             "substantial evidence of effectiveness"),
            ("4.2", "NO", R.INFERRED, "5.2.1. Trial Design",
             "Early termination of the trials for business decisions did not impact "
             "successful randomization, stratification or blinding"),
            ("4.3", "NO", R.STATED, "5.2.1. Trial Design",
             "SOLOIST and SCORED were randomized, placebo-controlled, parallel-group, "
             "multi-center, double-blind, trials comparing sotagliflozin to placebo"),
            ("4.4", "NA", R.INFERRED, "routed by RoB 2 from 4.3", ""),
            ("4.5", "NA", R.INFERRED, "routed by RoB 2 from 4.4", ""),
        ],
    },
}


def _norm(s):
    return " ".join(str(s or "").split()).lower()


def build(drug, spec, verify_quotes=True):
    """Build the store for one drug, refusing any quote not present in the source text.

    ⚠️ THE QUOTE GATE IS THE POINT. An assessor's quote that cannot be found in the
    document it names is not evidence, and this project has already recorded a case where
    a quoted span was scored as a fabrication because the checker searched different bytes
    than the reader saw. Here the checker reads the SAME extracted text file the assessor
    was given, so a miss is a real miss.
    """
    text = ""
    if verify_quotes:
        p = spec["text"]
        if not os.path.exists(p):
            return None, "SOURCE_TEXT_MISSING: %s" % p
        text = _norm(open(p, encoding="utf-8", errors="replace").read())

    per_trial, rejected = {}, []
    for q, resp, tier, where, quote in spec["answers"]:
        if verify_quotes and _norm(quote) not in text:
            rejected.append((q, quote[:60]))
            continue
        a = R.answer(q, resp, tier, quote, spec["document"], section=where,
                     url=spec["url"], retrieved_utc=UTC,
                     document_class="fda_integrated_review")
        for t in spec["trials"]:
            per_trial.setdefault(t, {})[q] = a
    if rejected:
        return None, ("QUOTE_NOT_IN_SOURCE: " +
                      "; ".join("%s %r" % r for r in rejected))
    return {
        "by_trial": per_trial,
        "recorded_utc": UTC,
        "n_assessors": 1,
        "adjudicated": False,
        "assessor": "GPT-5 Codex (openai family), via codex exec, one read",
        "what_this_is_not": (
            "This is a SINGLE read of a named regulatory document, not the two-assessor "
            "adjudicated assessment this corpus uses for its own risk-of-bias work. It "
            "supplements a stored assessment by answering signalling questions the "
            "registry record could not, and it never replaces a judgement an assessor "
            "made."),
        "trial_coverage_verified": (
            "The review's own text was searched for each trial before any answer was "
            "attached. Answers are recorded ONLY against trials the review covers."),
        "source_sha256_16": hashlib.sha256(
            text.encode("utf-8", "replace")).hexdigest()[:16] if text else None,
    }, "OK"


def main(apply_changes=False):
    root = os.path.join(_HERE, "..")
    for drug, spec in EXTRACTED.items():
        store, st = build(drug, spec)
        print("%-14s %-22s trials=%s" % (drug, st, ",".join(spec["trials"])))
        if store is None:
            continue
        path = os.path.join(root, "ssot", spec["topic"], "%s.json" % spec["topic"])
        if not os.path.exists(path):
            print("   OBJECT NOT FOUND: %s" % path)
            continue
        with open(path, encoding="utf-8") as fh:
            obj = json.load(fh)
        rb = obj.setdefault("risk_of_bias", {})
        before = json.dumps(rb.get(R.STORE_KEY), sort_keys=True)
        rb[R.STORE_KEY] = store
        after = json.dumps(store, sort_keys=True)
        print("   %s  %d trial(s), %d answer(s)%s"
              % (spec["topic"], len(store["by_trial"]),
                 sum(len(v) for v in store["by_trial"].values()),
                 "" if before != after else "  (unchanged)"))
        if apply_changes:
            # USE THE PROJECT'S OWN WRITER. The first version of this script opened
            # the temp file with a plain open(path, 'w'), which on Windows turns a
            # bare line feed into a carriage-return line-feed pair -- so both
            # objects were rewritten from LF to CRLF and EVERY LINE CHANGED. The
            # content was semantically identical (checked: parsed equality
            # CHANGED. The content was semantically identical (checked: parsed equality
            # excluding the added block, and the non-ascii character counts unchanged),
            # but the diff was 9,256 lines for a 470-line addition, which hides a real
            # change inside noise nobody will read.
            #
            # `atomic_write.write_json` detects the file's EXISTING newline -- the module
            # notes alirocumab is CRLF while others are LF, so this is per-file and cannot
            # be assumed -- serialises completely before touching disk, and replaces
            # atomically. It exists because an applier once truncated an object to zero
            # bytes between the open and the write.
            import atomic_write as _aw
            n = _aw.write_json(path, obj)
            print("   WRITTEN (%d bytes, newline preserved)" % n)
        else:
            print("   dry run -- pass --apply to write")


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    main(apply_changes="--apply" in sys.argv)
