# -*- coding: utf-8 -*-
"""Record ASPIRE's own primary report as evidence for three RoB 2 signalling questions.

⭐ NO ACCESS EXCEPTION WAS NEEDED, AND CHECKING SAVED ONE. I was about to ask for the
firewalled-paper exception for both dapivirine primaries. ASPIRE's carries PMC4993693 with
`isOpenAccess=N` -- the NIH AUTHOR-MANUSCRIPT case: free to read at PMC, no reuse licence.
Europe PMC's fullTextXML returns 404 for it because that API serves only the OA subset, and
reading that 404 as "paywalled" would have been this project's own rule applied backwards:
OPEN ACCESS IS A LICENCE, NOT A RETRIEVAL STATUS. Fetched instead: 200,220 bytes.

⚠️ WHAT THIS DOES NOT DO, AND THE FIRST VERSION OF THIS DOCSTRING GOT IT WRONG. It said the
domain "still refuses". It does not. Both assessors AGREE on SOME_CONCERNS at the OVERALL
level, so `grade_engine` already resolves risk of bias to a one-level downgrade and the
NO_INFORMATION lift path is never reached on this topic. The NO_INFORMATION sits at the
SIGNALLING-QUESTION level -- 1.2, 2.6, 3.1 -- underneath a verdict the assessors could still
reach. The claim was checked by running the engine after writing, which is the only reason
it was caught before anyone read it.

⇒ The value here is the EVIDENCE, recorded and sourced, not a changed rating. Writing it
now means that when the second trial is answered the lift is a one-line addition rather
than a fresh investigation -- and it means the object states what is known about ASPIRE
instead of carrying NO_INFORMATION for facts that are in a free document.

⚠️ AND THE DOCUMENT CLASS IS `trial_publication`, NOT A REGULATORY ONE. A trial's own report
is the investigators' account; a regulatory review is an independent assessor reading their
dossier. Those are different evidence and the class says which. The store key remains
`regulatory_evidence` because three surfaces read it, and that name is now a misnomer --
named in the module rather than left to be discovered.
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

TOPIC = "agyw-hiv-prep-review"
TRIAL = "NCT01617096"              # ASPIRE / MTN-020. VERIFIED AGAINST THE REGISTRY.
# ⛔ THIS SCRIPT IS SUPERSEDED and must not be re-run. It was written when the object
# labelled the two trials the wrong way round, so it wrote Baeten's ASPIRE evidence
# against NCT01539226 -- which is IPM 027, The Ring Study. The constant above is
# corrected so the file does not carry a false identity, but the store it writes was
# rebuilt wholesale by scripts/fix_dapivirine_trial_labels_2026_08_30.py, which keys
# both trials from ClinicalTrials.gov. Re-running this would undo that.
UTC = datetime.datetime.now(datetime.timezone.utc).isoformat()

DOC = ("Baeten JM et al. Use of a Vaginal Ring Containing Dapivirine for HIV-1 Prevention "
       "in Women. N Engl J Med 2016. PMID 26900902, PMC4993693.")
URL = "https://pmc.ncbi.nlm.nih.gov/articles/PMC4993693/"

ANSWERS = [
    ("1.2", "YES", R.INFERRED, "Study Procedures",
     "with the exception of staff members at the central statistical and data management "
     "center, investigators and participants were unaware of the randomization "
     "assignments"),
    ("2.6", "YES", R.STATED, "Statistical Analysis",
     "The primary analysis of HIV-1 protection was performed according to the "
     "intention-to-treat principle"),
    ("3.1", "YES", R.STATED, "Follow-up and Adherence",
     "with 2614 participants (99.4%) completing at least one post-randomization HIV-1 "
     "test"),
]

SOURCE_TEXT = "F:/claude-temp/rm-dapivirine-2026-08-31/ft/ASPIRE_PMC4993693.txt"


def _norm(s):
    return " ".join(str(s or "").split()).lower()


def main(apply_changes=False):
    # ⚠️ EVERY QUOTE IS CHECKED AGAINST THE SAME BYTES THE ASSESSOR READ. A quote that
    # cannot be found in the document it names is not evidence, and this project has
    # already recorded a case where a checker searched different bytes than the reader saw
    # and scored true quotes as fabrications.
    if not os.path.exists(SOURCE_TEXT):
        print("SOURCE TEXT MISSING: %s" % SOURCE_TEXT)
        return 1
    text = _norm(open(SOURCE_TEXT, encoding="utf-8", errors="replace").read())

    built, rejected = {}, []
    for q, resp, tier, where, quote in ANSWERS:
        if _norm(quote) not in text:
            rejected.append((q, quote[:70]))
            continue
        built[q] = R.answer(q, resp, tier, quote, DOC, section=where, url=URL,
                            retrieved_utc=UTC, document_class="trial_publication")
    if rejected:
        print("REFUSED -- quote not found in the source text:")
        for q, s in rejected:
            print("   %s %r" % (q, s))
        return 1
    print("all %d quotes verified present in the source text" % len(built))

    path = os.path.join(_HERE, "..", "ssot", TOPIC, "%s.json" % TOPIC)
    with open(path, encoding="utf-8") as fh:
        obj = json.load(fh)
    rb = obj.setdefault("risk_of_bias", {})
    store = rb.setdefault(R.STORE_KEY, {})
    store.setdefault("by_trial", {})[TRIAL] = built
    store.update({
        "recorded_utc": UTC,
        "n_assessors": 1,
        "adjudicated": False,
        "assessor": "GPT-5 Codex (openai family), via codex exec, one read",
        "store_key_is_a_misnomer": (
            "This key is named `regulatory_evidence` because three surfaces read it, but "
            "it now also holds evidence from a trial's OWN primary report. Check "
            "`document_class` on each answer: `trial_publication` is the investigators' "
            "account, an FDA class is an independent assessor reading their dossier."),
        "coverage_within_this_topic": (
            "ASPIRE / MTN-020 (NCT01617096) only. The Ring Study / IPM 027 (NCT01539226, "
            "PMID 27959766, N Engl J Med) has NO PMC record and its questions 1.2, 2.6 and "
            "3.1 remain unanswered."),
        "what_this_changes_and_what_it_does_not": (
            "It does not change the risk-of-bias VERDICT: both assessors agree on "
            "SOME_CONCERNS, so the domain already resolved and the NO_INFORMATION lift "
            "path is not invoked here. What it changes is what the object KNOWS -- three "
            "signalling questions that were NO_INFORMATION for ASPIRE are now answered "
            "from a free document with verbatim quotes, while the Ring Study's three "
            "remain unanswered."),
    })
    print("recorded %d answers for %s" % (len(built), TRIAL))
    if not apply_changes:
        print("dry run -- pass --apply to write")
        return 0
    n = aw.write_json(path, obj)
    print("WRITTEN %d bytes, newline preserved" % n)
    return 0


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.exit(main(apply_changes="--apply" in sys.argv))
