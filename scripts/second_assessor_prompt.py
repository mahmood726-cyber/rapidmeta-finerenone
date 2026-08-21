"""Build a BLIND RoB 2 prompt for a second assessor, from the registry facts an object records.

MAHMOOD'S SPECIFICATION IS TWO ASSESSORS FROM DIFFERENT MODEL FAMILIES. This file produces the
input for the second one, and its entire job is to emit FACTS AND NOT JUDGEMENTS.

WHAT IS EMITTED -- only fields whose content came off the registry:

    nct, trial name, registered enrolment, registered masking, registered sites,
    registered primary outcome, which registered rank the pooled result holds,
    registered comparator, and the name of the result being assessed.

WHAT IS NEVER EMITTED, and the check that enforces it: every `domains.*.judgement`,
every `domains.*.reason`, every `overall`, every `overall_reason`, and every key added by the
first assessor to explain itself. A blind assessment shown the first assessment's reasoning is
not blind, and the resulting agreement would measure deference.

    THE GUARD IS POSITIVE, NOT NEGATIVE: the prompt is assembled from an ALLOW-LIST of factual
    field names, so a judgement field cannot leak by being forgotten. A deny-list would have to
    anticipate every key the first assessor might invent, and it invented eleven this run.

AND THE PROMPT CARRIES THE HOUSE CEILING RULE, deliberately. The second assessor is being asked
to apply THIS PROJECT'S convention -- NO_INFORMATION never LOW -- not its own house style, so
that a disagreement is about the evidence rather than about which convention each model reached
for. That is the difference between measuring judgement and measuring dialect.
"""
import io
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# THE ALLOW-LIST WAS TOO NARROW AND IT CONTAMINATED THE FIRST NINE TOPICS.
#
# The first version emitted nine fields. Reconciling the replies showed that several D4 and D5
# disagreements were not judgement differences at all: the FIRST assessment's stated reason
# rested on facts the prompt DID NOT CARRY. On ceftaroline the first assessor's D5 reason is
# "two register MITTE and one registers CE" -- an analysis-population split recorded in
# `registered_analysis_population`, which was not on the list. The second assessor could not
# have known, so its LOW is not a disagreement about the evidence; it is an assessment of
# LESS evidence.
#
# A BLIND ASSESSMENT GIVEN FEWER FACTS IS NOT A COMPARABLE ASSESSMENT, and a disagreement rate
# computed over one is measuring the prompt. Every registry-sourced field any assessment
# actually used is on the list now.
FACT_FIELDS = [
    ("trial", "trial"),
    ("cohort_id", "cohort"),
    ("registered_enrolment", "registered enrolment"),
    ("registered_masking", "registered masking"),
    ("registered_sites", "registered sites"),
    ("registered_comparator", "registered comparator"),
    ("registered_arm_count", "number of registered arms"),
    ("registered_primary_count", "number of registered PRIMARY outcomes"),
    ("registered_primary_outcome", "registered PRIMARY outcome"),
    ("registered_analysis_population", "registered analysis population"),
    ("rank_of_the_result_this_review_pools", "the rank the pooled result holds"),
    ("result_assessed", "the result being assessed"),
    ("participants_this_object_pools", "participants this review pools"),
    ("enrolment_minus_pooled", "registered enrolment minus participants pooled"),
]

JUDGEMENT_WORDS = re.compile(
    r"\b(LOW|HIGH|SOME_CONCERNS|SOME CONCERNS|NO_INFORMATION|NOT_ASSESSABLE)\b")

HEADER = """You are performing Cochrane RoB 2 assessments. Assess PER RESULT (Handbook 8.2).

Answer ONLY from the facts below. Do not look anything up, do not open files, do not use tools.

HOUSE RULE YOU MUST APPLY: a domain that cannot be judged from the facts given is
NO_INFORMATION, never LOW. Do not score LOW by default and do not score HIGH by default.
An overall judgement cannot be LOW while any domain is NO_INFORMATION or SOME_CONCERNS.

THE ONLY SOURCE READ FOR THESE TRIALS IS ClinicalTrials.gov -- the design module, the
eligibility and location modules, and the registered outcome lists. No trial publication was
read. The registry carries nothing on deviations from the intended intervention, on the
analysis population actually used, or on missing outcome data.
"""

FOOTER = """
For EACH result above give LOW, HIGH, SOME_CONCERNS or NO_INFORMATION for each of the five
RoB 2 domains, plus an overall.

  D1 randomisation process
  D2 deviations from intended intervention
  D3 missing outcome data
  D4 measurement of the outcome
  D5 selection of the reported result

Output EXACTLY one line per result, in this form, and NOTHING else -- no preamble, no
explanation, no markdown:

<RESULT_ID> D1=<x> D2=<x> D3=<x> D4=<x> D5=<x> OVERALL=<x>

The result ids, in order, are:
%s
"""


def facts_for(topic):
    path = os.path.join(REPO, "ssot", topic, topic + ".json")
    obj = json.load(io.open(path, encoding="utf-8"))
    rob = obj.get("risk_of_bias") or {}
    by = rob.get("by_outcome") or {}
    out, ids = [], []
    for oid, per in sorted(by.items()):
        if not isinstance(per, dict):
            continue
        for rid, j in sorted(per.items()):
            if not isinstance(j, dict):
                continue
            if not j.get("registered_masking"):
                continue
            rid_short = (j.get("nct") or rid).split("::")[0]
            label = "%s__%s" % (rid_short, oid)
            lines = ["  RESULT ID: %s" % label, "  outcome pooled: %s" % oid]
            for key, words in FACT_FIELDS:
                v = j.get(key)
                if isinstance(v, (str, int)) and str(v).strip():
                    lines.append("  %s: %s" % (words, v))
            out.append("\n".join(lines))
            ids.append(label)
    return obj, out, ids


def build(topic):
    obj, blocks, ids = facts_for(topic)
    if not blocks:
        return None, []
    body = "\n\n".join(blocks)

    # POSITIVE GUARD, CHECKED. No emitted line may contain a RoB 2 verdict word: those appear
    # only in judgement fields, and none of those is on the allow-list. If one shows up, a
    # factual field is carrying a judgement in its text and the prompt is refused rather than
    # sent.
    leak = JUDGEMENT_WORDS.search(body)
    if leak:
        sys.exit("REFUSED: the assembled prompt for %s contains the verdict word %r. A blind "
                 "assessment shown the first assessment's verdicts is not blind.\n  context: "
                 "...%s..." % (topic, leak.group(1),
                               body[max(0, leak.start() - 90):leak.end() + 90]))
    prompt = "%s\n%s\n%s" % (HEADER, body, FOOTER % "\n".join("  " + i for i in ids))
    return prompt, ids


if __name__ == "__main__":
    t = sys.argv[1]
    p, ids = build(t)
    if not p:
        sys.exit("REFUSED: %s records no registry facts on its risk-of-bias entries, so a "
                 "blind prompt cannot be built without re-reading the registrations." % t)
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    print(p)
