# -*- coding: utf-8 -*-
"""Plant the defect in the blinding guard, and prove what the prompt does and does not carry.

WHAT WAS ASKED, AND WHAT IS ACTUALLY THE CASE. The brief was to repair
`second_assessor_prompt.py` because the blinding supposedly withholds the decision rule. It
does not: the guard scans the assembled FACT BLOCKS (`JUDGEMENT_WORDS.search(body)`) and
never the header, and the header carries the rule in full. So there is no repair to make --
but "there is nothing to fix" is a claim, and a claim of that kind is exactly what this
project has learned to distrust unless it can be made to fail on demand.

FOUR CONTROLS, KEYED TO A REAL STORED ASSESSMENT rather than a synthetic object:

  P1  the decision rule REACHES the second assessor           -- must be in the prompt
  P2  the first assessor's judgements do NOT reach it         -- blinding actually blinds
  N1  a verdict word PLANTED in a fact field is REFUSED       -- the guard can fail
  N2  the same topic unplanted is NOT refused                 -- it does not refuse always

N1 is the one that matters. A blinding check that cannot fail is not a blinding check, and
P1+P2 alone would pass a guard that had been commented out.
"""
import copy
import io
import json
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                              line_buffering=True)
REPO = r"F:\rapidmeta-ssot-shell"
sys.path.insert(0, os.path.join(REPO, "scripts"))
os.chdir(REPO)
import second_assessor_prompt as SAP  # noqa: E402


def pick_topic():
    """A real topic that carries a dual assessment and builds a prompt."""
    import glob
    for p in sorted(glob.glob("ssot/*/*.json")):
        t = os.path.basename(os.path.dirname(p))
        if os.path.basename(p) != t + ".json":
            continue
        try:
            obj = json.load(io.open(p, encoding="utf-8"))
        except Exception:
            continue
        rb = obj.get("risk_of_bias") or {}
        if not any(str(k).startswith("SECOND_ASSESSOR") for k in rb):
            continue
        try:
            pr, ids = SAP.build(t)
        except SystemExit:
            continue
        if pr and ids:
            return t, obj, pr, ids
    return None, None, None, None


def build_or_refusal(topic):
    """Returns ('built', prompt) or ('refused', message)."""
    try:
        pr, ids = SAP.build(topic)
        return ("built", pr)
    except SystemExit as ex:
        return ("refused", str(ex))


fails = 0


def check(label, got, want):
    global fails
    ok = got == want
    if not ok:
        fails += 1
    print("   %-6s %-62s %s" % ("PASS" if ok else "FAIL", label, got))
    if not ok:
        print("          expected %r" % (want,))


real_facts_for_check = SAP.facts_for
topic, obj, prompt, ids = pick_topic()
if not topic:
    sys.exit("REFUSED: no real dual-assessed topic builds a prompt; nothing to key to.")
print("CONTROL TOPIC (real, stored): %s  -- %d result block(s)\n" % (topic, len(ids)))

# --- P1: the decision rule reaches the second assessor --------------------------------
rule_bits = ["NO_INFORMATION, never LOW", "HOUSE RULE YOU MUST APPLY",
             "Do not score LOW by default"]
print("P1  does the DECISION RULE reach the assessor?")
for b in rule_bits:
    check("prompt contains %r" % b[:40], b in prompt, True)
stored = str(((obj.get("risk_of_bias") or {}).get("default_rule") or ""))
print("      stored default_rule: %s" % (stored[:96] or "(none stored)"))
print("      the header states the same rule in its own words, and it is the header that is")
print("      sent -- the guard below never inspects it.\n")

# --- P2: the first assessor's judgements do not reach it ------------------------------
print("P2  do the FIRST assessor's judgements leak into the prompt?")
j1 = []
for oid, per in ((obj.get("risk_of_bias") or {}).get("by_outcome") or {}).items():
    if not isinstance(per, dict):
        continue
    for rid, rec in per.items():
        if not isinstance(rec, dict):
            continue
        for dk, dv in (rec.get("domains") or {}).items():
            v = dv.get("judgement") if isinstance(dv, dict) else None
            if isinstance(v, str):
                j1.append(v)
check("first assessor recorded judgements (sanity)", len(j1) > 0, True)
# SCOPED TO THE FACT BLOCKS, NOT THE WHOLE PROMPT. The first version of this control
# searched the entire prompt for judgement words and failed -- because the HEADER
# legitimately contains "NO_INFORMATION, never LOW" as the RULE. That is precisely the
# conflation the original diagnosis made: treating the presence of a verdict word as
# evidence of a leaked verdict, when the rule itself is written in those words. What must
# not leak is the first assessor's judgements into the FACTS, which is what the guard checks.
_o, _blocks, _i = real_facts_for_check(topic)
_body = "\n\n".join(_blocks)
check("no judgement word appears in the FACT BLOCKS",
      not any(re.search(r"\b%s\b" % re.escape(v), _body) for v in set(j1)), True)
check("the rule's words are in the header and that is NOT a leak",
      ("NO_INFORMATION, never LOW" in prompt) and ("NO_INFORMATION" not in _body), True)
print()

# --- N1: PLANT THE DEFECT -------------------------------------------------------------
print("N1  PLANTED DEFECT -- a verdict word injected into a FACT field must be refused")
real_facts = SAP.facts_for


def planted_facts(t):
    o, blocks, i = real_facts(t)
    if blocks:
        blocks = list(blocks)
        blocks[0] = blocks[0] + "\n  registered comparator: placebo (assessor 1 said HIGH)"
    return o, blocks, i


SAP.facts_for = planted_facts
state, msg = build_or_refusal(topic)
SAP.facts_for = real_facts
check("planted prompt is REFUSED", state, "refused")
check("the refusal names the leaked word",
      bool(re.search(r"verdict word 'HIGH'|verdict word \"HIGH\"", msg)), True)
print("      refusal: %s" % re.sub(r"\s+", " ", msg)[:150])
print()

# --- N2: unplanted, same topic, must build --------------------------------------------
print("N2  the SAME topic, unplanted, must NOT be refused")
state2, _ = build_or_refusal(topic)
check("unplanted prompt builds", state2, "built")

print()
print("ALL CONTROLS HELD" if not fails else "%d CONTROL(S) FAILED" % fails)
print("")
print("CONCLUSION: the blinding guard CAN fail and does fail on a planted verdict, and the")
print("decision rule is carried to the second assessor. The premise that the rule was")
print("withheld does not hold, so there is no repair to make and the re-run would not")
print("change what assessor 2 was told.")
raise SystemExit(1 if fails else 0)
