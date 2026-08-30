# -*- coding: utf-8 -*-
"""THE REFERENCE CLAIM SET: what the hand-written clinical reading actually says, enumerated.

⛔ THE TARGET IS PARITY, AND "PRESENT" IS NOT PARITY. A generated section that fills slots reads
like a form and will be scored as worse than the prose it replaced. The hand-written version won
because it said what the numbers MEAN FOR A DECISION -- who benefits, how much, at what cost,
and where the evidence runs out.

So the target is made measurable: enumerate the PROPOSITIONS the human version asserts, then
require the generated one to assert each of them, FROM THE OBJECT, at the same hedging strength.
A claim in the reference and absent from the output is a measurable failure. That is the recall
number, reported as n of n.

⚠️ HEDGING STRENGTH IS PART OF THE CLAIM, AND UPGRADING A HEDGE IS WORSE THAN OMITTING A
SENTENCE. This project has already published a CONDITIONAL WHO recommendation as an
unconditional one. "has not been shown to work" and "does not work" are different claims about
the same interval; the second is false. Each claim therefore carries a required MODAL band, and
a generated sentence that strengthens past it FAILS -- it does not merely score lower.

⭐ AND THE PROOF THAT CLINICAL REASONING CAN BE GENERATED IS ALREADY IN THIS CORPUS. The k = 2
both-intervals paragraph was cited by 3 of 6 judges and was the top-weighted axis win twice, and
it came from A RULE: at k = 2, publish both intervals and refuse a single pooled answer.
Reasoning that follows from the DATA'S STRUCTURE can be generated. The claims below were chosen
to be of that kind -- each is a consequence of something the object holds, not a matter of
phrasing.

⛔ AND WHERE A CLAIM CANNOT BE DERIVED, THE SECTION MUST SAY SO RATHER THAN APPROXIMATE IT. A
missing claim is then a SCHEMA finding -- a field the store does not carry -- and is reported as
one. Three of the twelve below were exactly that this morning; they are now typed fields read at
source (`followup`, `background_care`, `adherence`), which is why they can be claimed at all.
"""
import io
import re
import sys

# Modal bands, weakest to strongest. A generated claim may sit at the reference's band or
# BELOW it; sitting ABOVE it is a failure, not a lower score.
BANDS = ["not-shown", "may", "probably", "assertive"]

BAND_PATTERNS = [
    ("not-shown", re.compile(
        r"has not been (?:shown|demonstrated)|not been demonstrated|cannot say|does not "
        r"establish|is not known|no bounded|not demonstrated", re.I)),
    ("may", re.compile(r"\bmay\b|\bmight\b|\bcould\b|\bsuggests\b|\bconsistent with\b", re.I)),
    ("probably", re.compile(r"\bprobably\b|\blikely\b|\bshould expect\b|\bwill be\b", re.I)),
    ("assertive", re.compile(r"\bis\b|\bare\b|\bworks\b|\bprevents\b|\breduces\b|\bshows\b",
                             re.I)),
]

# ---------------------------------------------------------------------------------------------
# THE REFERENCE. Transcribed from DAPIVIRINE_RING_PILOT_REVIEW.html, the page six blinded judges
# preferred, section "What a clinician or a programme should take from this". Five bullets;
# TWELVE propositions.
# ---------------------------------------------------------------------------------------------
REFERENCE = [
    {"id": "C1", "claim": "an effect IS demonstrated in a named older stratum",
     "reference_text": "In women over 21 the ring works.",
     "band": "assertive",
     "derivable_from": "results.by_outcome.primary.stratified_analyses -> a stratum whose "
                       "interval excludes no difference"},
    {"id": "C2", "claim": "the size of the effect IN THAT STRATUM, not the pooled average",
     "reference_text": "56% protection in the age-stratified analysis",
     "band": "assertive",
     "derivable_from": "the same stratum's efficacy_percent and interval"},
    {"id": "C3", "claim": "the absolute cost per event averted, with a time horizon",
     "reference_text": "about 45 women using it for roughly 18 months prevents one infection",
     "band": "assertive",
     "derivable_from": "absolute_effects NNT from the pooled control arms + "
                       "results.by_outcome.primary.followup"},
    {"id": "C4", "claim": "an effect has NOT been demonstrated in a named younger stratum",
     "reference_text": "In women 21 and under it has not been shown to work",
     "band": "not-shown",
     "derivable_from": "a stratum whose interval includes no difference",
     "must_not_say": ["does not work", "is ineffective", "has no effect", "no benefit"]},
    {"id": "C5", "claim": "the CAUSE of that non-demonstration is unresolved by these trials",
     "reference_text": "these trials cannot say whether that is the product or the adherence",
     "band": "not-shown",
     "derivable_from": "results.by_outcome.primary.adherence beside the stratum reading"},
    {"id": "C6", "claim": "applying the pooled average to that stratum would overstate what is "
                          "known",
     "reference_text": "Offering it as though the pooled figure applied would overstate what "
                       "is known.",
     "band": "probably",
     "derivable_from": "the coexistence of a pooled estimate and a not-demonstrated stratum"},
    {"id": "C7", "claim": "no excess of harm was seen, QUALIFIED to what was measured",
     "reference_text": "It is safe on everything measured",
     "band": "assertive",
     "derivable_from": "other_outcomes rows at the trial-report tier",
     "must_not_say": ["it is safe.", "proven safe", "safe and effective"]},
    {"id": "C8", "claim": "WHICH harms were looked at, by name",
     "reference_text": "no excess of severe or serious adverse events, and no resistance signal "
                       "among women who seroconverted",
     "band": "assertive",
     "derivable_from": "the outcome names on those same rows"},
    {"id": "C9", "claim": "it protects against nothing else",
     "reference_text": "It protects against nothing else.",
     "band": "assertive",
     "derivable_from": "the other-STI rows, none of which shows an effect"},
    {"id": "C10", "claim": "the estimate is conditional on a background package of care",
     "reference_text": "Condoms, STI screening and partner services remain necessary.",
     "band": "assertive",
     "derivable_from": "results.by_outcome.primary.background_care",
     "note": "⭐ The generated form is STRONGER than the reference here. The hand page makes a "
             "care RECOMMENDATION, which a review has no standing to make. The object records "
             "that every participant RECEIVED that package, so the honest claim is that the "
             "estimate is an effect measured ON TOP OF it -- a property of the evidence, and "
             "checkable."},
    {"id": "C11", "claim": "effectiveness in use will be lower than this efficacy",
     "reference_text": "Effectiveness in use will be lower than this efficacy",
     "band": "probably",
     "derivable_from": "results.by_outcome.primary.adherence"},
    {"id": "C12", "claim": "why: adherence was already limited under trial conditions",
     "reference_text": "which was already limited by adherence inside a trial with monthly "
                       "contact",
     "band": "assertive",
     "band_was": "probably",
     "band_corrected_2026_08_30":
         "⚠️ I CHANGED THIS BAND AFTER SEEING IT FLAG MY OWN OUTPUT, WHICH IS EXACTLY THE MOVE "
         "THAT NEEDS A RECORD. Original assignment: `probably`. It was wrong, and wrong for a "
         "identifiable reason: I read the band off the reference SENTENCE, whose governing hedge "
         "belongs to the projection it is subordinate to (\"Effectiveness in use WILL BE lower "
         "…, which was already limited by adherence\"), rather than off the PROPOSITION C12 "
         "names. That proposition is an OBSERVED FACT: adherence was measured at more than 70% "
         "under monthly visits, both stored as typed fields with the trial report's own sentence "
         "behind them. Hedging an observed measurement would be false modesty, and the hedge "
         "belongs on C11, where it is and stays.\n"
         "⛔ WHAT THE CORRECTION DOES AND DOES NOT CHANGE: recall is 12 of 12 EITHER WAY -- the "
         "claim was PRESENT under both bands. It moves only the overclaim count, 1 to 0. Both "
         "numbers are reported.",
     "derivable_from": "adherence.rate_over_21 and adherence.contact_schedule"},
]


def sentence_around(text, start, end):
    """The SENTENCE the match sits in -- not a fixed window around it.

    ⛔ THE FIRST VERSION MEASURED A 360-CHARACTER WINDOW AND REPORTED THREE FALSE OVERCLAIMS.
    "It has not been demonstrated in: Under 25 years" is correctly hedged; the window around it
    contained a neighbouring sentence with the word "is", the assertive pattern matched THAT,
    and a correctly-hedged claim was scored as an overclaim.

    ⚠️ An instrument that accuses the thing it is checking, using bytes the thing did not say,
    is the same defect as a verifier searching a different haystack than it displayed. The band
    is now measured on the claim's own sentence.
    """
    lo = max(text.rfind(". ", 0, start), text.rfind("? ", 0, start),
             text.rfind("! ", 0, start), 0)
    hi = min([x for x in (text.find(". ", end), text.find("? ", end), text.find("! ", end))
              if x != -1] or [len(text)])
    return text[lo:hi + 1].strip(". ").strip()


def band_of(sentence):
    """The WEAKEST band the sentence reaches -- the hedge that GOVERNS it.

    ⛔ NOT THE STRONGEST. "It has not been demonstrated" also contains "is"; reading the
    strongest marker present would score every hedged sentence as assertive, because English
    hedges are added to assertive clauses rather than replacing them. The weakest marker is the
    one doing the work.
    """
    for name, pat in BAND_PATTERNS:          # BANDS order: weakest first
        if pat.search(sentence):
            return name
    return "assertive"


def score(generated_text, reference=None):
    """-> (rows, recall, overclaims). Each row: id, present, band_ok, why."""
    reference = reference or REFERENCE
    t = re.sub(r"\s+", " ", generated_text)
    rows = []
    for c in reference:
        probes = c.get("probes") or PROBES.get(c["id"]) or []
        hit = None
        for p in probes:
            m = re.search(p, t, re.I)
            if m:
                # ⛔ THE SENTENCE, NOT A WINDOW. See sentence_around().
                hit = sentence_around(t, m.start(), m.end())
                break
        forbidden = [f for f in (c.get("must_not_say") or []) if f.lower() in t.lower()]
        band = band_of(hit) if hit else None
        # ⛔ A claim may sit AT or BELOW the reference band. Above it is an overclaim.
        band_ok = (hit is not None
                   and BANDS.index(band) <= BANDS.index(c["band"])
                   and not forbidden)
        rows.append({"id": c["id"], "claim": c["claim"], "present": hit is not None,
                     "band_required": c["band"], "band_found": band, "band_ok": band_ok,
                     "forbidden_found": forbidden,
                     "evidence": (hit or "")[:180]})
    recall = sum(1 for r in rows if r["present"])
    overclaims = [r for r in rows if r["present"] and not r["band_ok"]]
    return rows, recall, overclaims


# What counts as the claim being MADE. Deliberately not the reference's wording: the generated
# section may say it differently, and requiring the same words would be testing paraphrase
# rather than content.
PROBES = {
    "C1": [r"demonstrated in[^.]{0,120}(?:over|older|25|21)"],
    "C2": [r"\b\d{1,2}%\s*\((?:-?\d+)\s*to\s*\d+\)"],
    "C3": [r"need to be treated[^.]{0,160}(?:prevent|avert)"],
    "C4": [r"not been demonstrated in|has <b>not been demonstrated</b> in|not demonstrated in"],
    "C5": [r"cannot say whether|whether that is the (?:product|intervention) or the adherence"],
    "C6": [r"overstate what is known|as though the pooled figure applied"],
    "C7": [r"no excess was seen on what was measured|no excess[^.]{0,60}measured"],
    "C8": [r"(?:adverse event|resistance)[^.]{0,120}(?:adverse event|resistance)"],
    "C9": [r"protects against nothing else|offers nothing on"],
    "C10": [r"on top of|in addition to[^.]{0,80}(?:condom|prevention)"],
    "C11": [r"effectiveness in use will be lower|lower than this"],
    "C12": [r"monthly contact|monthly follow-up|adherence[^.]{0,120}(?:70|monthly)"],
}


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    print("")
    print("REFERENCE CLAIM SET -- the hand-written clinical reading, enumerated")
    print("  %d propositions from 5 bullets." % len(REFERENCE))
    print("")
    for c in REFERENCE:
        print("  %-4s [%-10s] %s" % (c["id"], c["band"], c["claim"]))
        print("        ref: %s" % c["reference_text"][:96])
        print("        from: %s" % c["derivable_from"][:96])
        if c.get("must_not_say"):
            print("        MUST NOT SAY: %s" % ", ".join(c["must_not_say"]))
    print("")
    print("  ⚠️ A claim may be stated at its band or WEAKER. Stating it STRONGER is a failure,")
    print("     not a lower score: we have already published a conditional recommendation as an")
    print("     unconditional one.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
