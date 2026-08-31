# -*- coding: utf-8 -*-
"""Answer RoB 2 signalling questions from a trial's own full text, quote-first.

⭐ WHY THIS IS A CAPABILITY AND NOT A DAPIVIRINE PATCH. Twenty-seven of this corpus's
fifty-four live pooled results have NO risk-of-bias assessment, and the assessments that
exist were made from ClinicalTrials.gov registration records, which do not report an
allocation-concealment mechanism, an analysis population, or how missing data were handled.
The registry is the wrong document. The trial's own report is the right one, it is free for
both dapivirine primaries, and it is free for a large share of the corpus. What was missing
was not the documents but a repeatable way to read them into typed answers.

⛔ THE QUOTE IS EXTRACTED, NEVER TRANSCRIBED. Every answer names an ANCHOR -- a regular
expression -- and the quote is the exact sentence the anchor matched, cut from the document
by the code. An author cannot paraphrase, cannot drift a word, and cannot quote a sentence
that is not there, because the quote is not authored at all. This closes by construction the
failure this project has already recorded twice: a checker that searched different bytes
than the reader saw, and an edit verified against source rather than rendered text.

⛔ AND AN ANCHOR THAT DOES NOT MATCH IS A REFUSAL, NOT A DEFAULT. If the paper does not say
it, the question is returned UNANSWERED and the domain stays blocked. That is the whole
discipline the GRADE engine is built on -- "where a domain lacks input, REFUSE rather than
default" -- applied one level down, at the signalling question. A tool that fills a gap with
its best guess produces a rating that cannot be told apart from one built on evidence.

⚠️ ROUTING IS NOT ANSWERING, AND THE DIFFERENCE IS RECORDED. RoB 2 makes some questions NOT
APPLICABLE given earlier answers: a double-blind trial routes 2.3-2.5 to NA, an appropriate
ITT analysis routes 2.7 to NA, and outcome data available for nearly all participants routes
3.2-3.4 to NA. Those are answers the TOOL supplies, not the paper, so they carry no quote
and are marked `routed` -- because "the paper said so" and "the algorithm says the question
does not arise" are different provenance and a later reader must be able to tell them apart.
"""
import io
import json
import os
import re
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "ssot"))

import regulatory_evidence as R    # noqa: E402

MAX_QUOTE_WORDS = 60
R_NO_INFO = "NO_INFORMATION"


def sentences(text):
    """The document as sentences. The unit a quote is cut to.

    ⚠️ A CHARACTER RADIUS IS THE WRONG BOUNDARY and this project has now measured that
    twice: 110 characters read an adjacent list as a swap, and a sibling lane found 44
    characters called a correct pair wrong while 1200 swept in ordinary prose. A sentence
    is declared by the text itself, so there is nothing to tune.
    """
    t = " ".join(str(text or "").split())
    # Do not split on an abbreviation or a decimal.
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z(])", t)
    return [p.strip() for p in parts if p.strip()]


def looks_like_flattened_table(s):
    """A CONSORT flow diagram, flattened by PDF extraction, is not a sentence.

    ⛔ FOUND BY READING THE OUTPUT, NOT BY THE CODE. Anchored on "were lost to follow-up",
    this module returned for the Ring Study:

        "379 Discontinued trial 50 Withdrew consent 44 Were lost to follow-up 8 Did not
         adhere to protocol 2 Died 1 Had protocol violation 274 Had other reasons ..."

    That is the trial's flow diagram with its layout removed. It is VERBATIM, it CONTAINS
    the anchor, and it is worthless as evidence -- a reader cannot tell which arm any number
    belongs to, because the columns that carried that meaning are gone. The paper's real
    sentence, two lines away, is "A total of 61 of 1959 participants (3.1%) were lost to
    follow-up."

    ⚠️ THE GENERAL POINT, AND IT IS WHY THIS GUARD EXISTS RATHER THAN A TIGHTER ANCHOR:
    VERBATIM IS NECESSARY AND NOT SUFFICIENT. Every check this project had built asks
    whether a quote is REALLY IN the document. None asked whether the span is a SENTENCE
    that supports the claim. A flattened table passes the first test perfectly.
    """
    # ⚠️ LENGTH IS PART OF THE TEST, AND LEAVING IT OUT MADE THIS GUARD REJECT THE EXACT
    # SENTENCE IT WAS WRITTEN TO RECOVER. On numeric density alone, "A total of 61 of 1959
    # participants (3.1%) were lost to follow-up." is 25% numbers -- a short sentence
    # reporting a proportion always is -- so the guard threw away the good quote and left
    # the question UNANSWERED. A flattened table is long AND dense; a numeric sentence is
    # short and dense. Third guard today whose first version accused something correct, and
    # the pattern in all three is the same: a threshold applied to one dimension of
    # something that needs two.
    toks = s.split()
    if len(toks) < 25:
        return False
    numeric = sum(1 for t in toks if re.fullmatch(r"[\d,.%()]+", t))
    return numeric / float(len(toks)) > 0.20


def find_quote(sents, anchor):
    """The exact sentence matching `anchor`, or None. Never a constructed string."""
    rx = re.compile(anchor, re.I)
    for s in sents:
        if rx.search(s) and not looks_like_flattened_table(s):
            words = s.split()
            if len(words) > MAX_QUOTE_WORDS:
                # Keep the anchor inside the cut rather than truncating blindly.
                m = rx.search(s)
                head = len(s[:m.start()].split())
                lo = max(0, head - MAX_QUOTE_WORDS // 2)
                return " ".join(words[lo:lo + MAX_QUOTE_WORDS])
            return s
    return None


def answer_from(text, spec):
    """spec: list of (question, response, tier, section, anchor_or_None).

    anchor None means the answer is ROUTED by the RoB 2 algorithm from earlier answers and
    has no sentence behind it.
    """
    sents = sentences(text)
    answered, unanswered = {}, []
    for question, response, tier, section, anchor in spec:
        if anchor is None:
            # ⚠️ THREE KINDS OF ANSWER-WITHOUT-A-QUOTE, AND COLLAPSING THEM WOULD HIDE THE
            # ONLY ONE THAT MATTERS. `routed` is the RoB 2 algorithm saying the question
            # does not arise given an earlier answer -- that is an ANSWER. `no_evidence` is
            # the document being silent -- that is a REFUSAL, and it must not be dressed as
            # routing, because a reader counting completed domains would then count a gap
            # as a finding. The third kind, an anchor that fails to match, never reaches
            # here at all: it is returned as UNANSWERED and exits non-zero.
            is_gap = str(response).strip().upper() == R_NO_INFO
            answered[question] = {"question": question,
                                  "question_text": R.QUESTION_TEXT[question],
                                  "response": response, "tier": tier, "quote": "",
                                  "routed": not is_gap,
                                  "no_evidence": is_gap,
                                  ("no_evidence_because" if is_gap else "routed_because"):
                                      section}
            continue
        q = find_quote(sents, anchor)
        if not q:
            unanswered.append((question, anchor))
            continue
        answered[question] = {"question": question, "response": response, "tier": tier,
                              "quote": q, "section": section, "routed": False,
                              "anchor": anchor}
    return answered, unanswered


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", required=True, help="JSON spec file")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    spec = json.load(open(a.spec, encoding="utf-8"))
    out = {}
    rc = 0
    for trial, cfg in spec.items():
        text = open(cfg["text"], encoding="utf-8", errors="replace").read()
        rows = [(q["q"], q["response"], q.get("tier", R.STATED), q.get("section", ""),
                 q.get("anchor")) for q in cfg["questions"]]
        answered, unanswered = answer_from(text, rows)
        out[trial] = {"document": cfg["document"], "url": cfg.get("url"),
                      "answers": answered, "unanswered": unanswered}
        print("%s: %d answered, %d UNANSWERED" % (trial, len(answered), len(unanswered)))
        for q, anc in unanswered:
            print("   ⛔ %s -- anchor found no sentence: %s" % (q, anc[:70]))
            rc = 1
    if a.out:
        json.dump(out, open(a.out, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
        print("written %s" % a.out)
    # ⚠️ Non-zero when any anchor missed: an unanswered question is a REFUSAL that must be
    # seen, not a quiet gap that leaves a domain silently unrateable.
    return rc


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.exit(main())
