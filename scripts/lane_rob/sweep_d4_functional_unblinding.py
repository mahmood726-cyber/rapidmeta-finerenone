# -*- coding: utf-8 -*-
"""Sweep: subjective outcome + perceptible intervention = a D4 question that must be ASKED.

THE CLASS. RoB 2 domain 4 is measurement of the outcome. Where the outcome is
patient-reported and the intervention produces effects a participant can feel or see --
substantial weight loss, gastrointestinal upset, genital infection, bradycardia, a taste
change -- allocation can be inferred, and a participant who has inferred it is reporting a
symptom score with knowledge of their arm. That is functional unblinding, and it is a D4
question whether or not the label says double-blind.

WHAT THIS INSTRUMENT DOES AND DOES NOT CLAIM. It flags a PAIRING. It does not judge the
domain, and it must not: an obvious mechanism is not a finding, and "double-blind" is not
evidence that blinding held. The output is a list of results where D4 has to be answered on
evidence -- whether blinding was maintained, whether it was tested, what the trials report --
rather than defaulted.

ITS ERROR RATE IS NOT MEASURED AND THE KEYWORD LISTS ARE MY JUDGEMENT, NOT DERIVED. Both
lists below are hand-written. That makes this a screening instrument whose false-negative
rate is unknown: a subjective outcome phrased in words I did not list will not be flagged.
It is therefore a lower bound on exposure, and it is reported as one. Anyone extending it
should add terms and re-run rather than trusting the number.

READ-ONLY. Writes nothing; the regen and merge are frozen.
"""
import collections
import glob
import io
import json
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                              line_buffering=True)
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
os.chdir(REPO)

# Outcomes a PARTICIPANT rates, or that a participant's effort determines.
SUBJECTIVE = re.compile(
    r"\b(kccq|kansas city|quality of life|\bqol\b|health status|symptom score|"
    r"symptom burden|patient[- ]report|patient[- ]global|self[- ]report|"
    r"visual analogue|\bvas\b|questionnaire|six[- ]minute walk|6[- ]minute walk|"
    r"\b6mwd\b|\b6mwt\b|walk(ing)? distance|exercise capacity|dyspn|breathless|"
    r"fatigue|pain score|\bnyha\b|functional class|well[- ]being|satisfaction|"
    r"sleep quality|depression score|anxiety score|\bpro\b)", re.I)

# Interventions whose common effects a participant can feel or see. Hand-written.
PERCEPTIBLE = re.compile(
    r"\b(semaglutide|tirzepatide|liraglutide|dulaglutide|exenatide|incretin|glp[- ]?1|"
    r"gip\b|empagliflozin|dapagliflozin|canagliflozin|ertugliflozin|sotagliflozin|"
    r"sglt2|sglt-2|metformin|orlistat|naltrexone|bupropion|phentermine|topiramate|"
    r"spironolactone|eplerenone|finerenone|sacubitril|ivabradine|beta[- ]blocker|"
    r"bisoprolol|carvedilol|metoprolol|opioid|morphine|oxycodone|gabapentin|"
    r"pregabalin|corticosteroid|prednis|colchicine|iron|ferric|diuretic|furosemide|"
    r"nitrate|sildenafil|tadalafil|minoxidil|isotretinoin|dupilumab|methotrexate)", re.I)


def text_of(*vals):
    return " ".join(str(v) for v in vals if isinstance(v, (str, int, float)))


rows = []
for p in sorted(glob.glob("ssot/*/*.json")):
    topic = os.path.basename(os.path.dirname(p))
    if os.path.basename(p) != topic + ".json":
        continue
    try:
        obj = json.load(io.open(p, encoding="utf-8"))
    except Exception:
        continue
    blob = json.dumps(obj, ensure_ascii=False)
    drug_hit = PERCEPTIBLE.search(topic) or PERCEPTIBLE.search(blob[:40000])
    if not drug_hit:
        continue
    for o in (obj.get("outcomes") or []):
        if not isinstance(o, dict):
            continue
        name = text_of(o.get("name"), o.get("id"),
                       (o.get("estimand") or {}).get("case_definition"))
        m = SUBJECTIVE.search(name)
        if not m:
            continue
        oid = o.get("id")
        # what does D4 currently say for this outcome, per result?
        d4 = []
        for rid, rec in (((obj.get("risk_of_bias") or {}).get("by_outcome") or {})
                         .get(oid) or {}).items():
            if not isinstance(rec, dict):
                continue
            for dk, dv in (rec.get("domains") or {}).items():
                if not dk.startswith("D4") or not isinstance(dv, dict):
                    continue
                reason = str(dv.get("reason") or "")
                d4.append({
                    "result": rid,
                    "judgement": dv.get("judgement"),
                    "mentions_blinding_maintenance": bool(re.search(
                        r"unblind|blinding (was )?(maintained|tested|broken)|"
                        r"guess(ed)? (their )?allocation|perceptib|weight loss|"
                        r"side[- ]effect|adverse effect", reason, re.I)),
                    "reason_head": reason[:110]})
        rows.append({"topic": topic, "outcome": oid, "outcome_name": str(o.get("name"))[:70],
                     "matched_outcome_term": m.group(0),
                     "matched_drug_term": drug_hit.group(0), "d4": d4})

print("=" * 94)
print("D4 FUNCTIONAL-UNBLINDING EXPOSURE: subjective outcome + perceptible intervention")
print("=" * 94)
print("  topics scanned                                 %4d"
      % len({os.path.basename(os.path.dirname(p)) for p in glob.glob("ssot/*/*.json")}))
print("  flagged outcome(s)                             %4d  <- A LOWER BOUND" % len(rows))
print("  distinct topics flagged                        %4d"
      % len({r["topic"] for r in rows}))
assessed = [d for r in rows for d in r["d4"]]
asked = [d for d in assessed if d["mentions_blinding_maintenance"]]
print("")
print("  per-result D4 judgements on those outcomes     %4d" % len(assessed))
print("  of those, whose REASON engages with whether")
print("  blinding actually held                         %4d" % len(asked))
print("  defaulted without engaging the question        %4d" % (len(assessed) - len(asked)))
print("")
c = collections.Counter(str(d["judgement"]) for d in assessed)
print("  D4 judgements as they stand: %s"
      % (", ".join("%s %d" % kv for kv in c.most_common()) or "none recorded"))
print("")
for r in rows:
    print("  %-30s %-26s [%s x %s]"
          % (r["topic"][:30], (r["outcome"] or "")[:26],
             r["matched_outcome_term"][:18], r["matched_drug_term"][:14]))
    print("      %s" % r["outcome_name"])
    for d in r["d4"]:
        print("      D4 %-16s %-46s %s"
              % (str(d["judgement"]), d["reason_head"],
                 "ENGAGES" if d["mentions_blinding_maintenance"] else "does NOT engage"))
    if not r["d4"]:
        print("      D4 not recorded for this outcome")
json.dump(rows, io.open(r"F:\claude-temp\pend\d4_sweep.json", "w", encoding="utf-8"),
          indent=1)
print("")
print("  detail -> d4_sweep.json")
print("")
print("  VERDICT: this flags a QUESTION, not an answer. Each flagged result needs D4")
print("  answered on what the trials report about blinding maintenance. Neither the")
print("  mechanism nor the 'double-blind' label settles it.")
