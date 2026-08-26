#!/usr/bin/env python3
"""PLANT the curated-overwrite defect and require merge_rob_grade_into_objects to REFUSE.

WHY THIS EXISTS. That script's key-loss guard exempts `by_outcome` "by design and by
name". The exemption is right for an assessment the script produced and wrong for one a
person made -- and 31 objects hold hand-made per-result judgements, 23 with a blind
second assessor. A re-run would have replaced them underneath preserved curated prose,
leaving an object that still looked hand-made. The guard added for that is exercised
here rather than asserted: it has passed every run it ever made while being unable to
see the one field that mattered, which is precisely the shape this project keeps finding.

FIXTURE ONLY. The real merge() is imported and driven against a temporary tree built by
this file. The live corpus is never opened, so no change to it can make this pass or
fail -- the control-keyed-to-corpus-state trap that has expired controls here before.

SIX CHECKS
  1 KNOWN POSITIVE    payload changes a stored judgement          -> REFUSES
  2 OLD GUARD MISSES  same payload through the OLD key-path guard -> reports NO loss
  3 NEGATIVE CONTROL  payload only ADDS a result                  -> writes
  4 DROP DETECTED     payload omits an existing result            -> REFUSES
  5 ESCAPE HATCH      --allow-overwrite names the topic           -> writes
  6 RESTORATION       fixture sha256 identical before and after
"""
import hashlib
import io
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import merge_rob_grade_into_objects_2026_08_19 as M

HERE = os.path.dirname(os.path.abspath(__file__))
# NOT tempfile.mkdtemp(): TMPDIR resolves to the SHARED claude-temp root, where another
# lane's run could collide with this one. A control that can be disturbed by a neighbour
# is not a control.
TMP = os.path.join(HERE, "_plant_curated_overwrite_tmp")

AUTHORITY = {"tool": "RoB 2", "version": "22 August 2019 version",
             "handbook": "Cochrane Handbook 6.5 ch.8",
             "unit_of_assessment": "A RESULT, not a study"}

CURATED = {
    "app_id": "fixture-topic",
    "risk_of_bias": {
        "tool": "RoB 2 (Cochrane risk-of-bias tool for randomized trials)",
        "version": "22 August 2019 version",
        "unit_of_assessment": "A RESULT, not a study",
        "default_rule": "A domain that cannot be judged from the sources read is "
                        "NO_INFORMATION, never SOME_CONCERNS.",
        "SECOND_ASSESSOR_2026_08_21": {
            "assessor_1": "Claude Opus 5 (anthropic family)",
            "assessor_2": "GPT-5 Codex (openai family), via `codex exec`",
            "DISAGREEMENT_RATE": "1 of 6 judgements",
        },
        "by_outcome": {
            "primary": {
                "NCT11111111": {
                    "trial": "FIXTURE-A",
                    "domains": {
                        "D1_randomisation": {"judgement": "SOME_CONCERNS",
                                             "reason": "hand-written by an assessor"},
                        "D5_selection_of_the_reported_result": {
                            "judgement": "HIGH", "reason": "hand-written by an assessor"},
                    },
                    "overall": "HIGH",
                },
                "NCT22222222": {
                    "trial": "FIXTURE-B",
                    "domains": {"D1_randomisation": {
                        "judgement": "LOW", "reason": "hand-written by an assessor"}},
                    "overall": "SOME_CONCERNS",
                },
            }
        },
    },
}

PAYLOAD_CHANGES = {"primary": {
    "NCT11111111": {"trial": "FIXTURE-A", "domains": {
        "D1_randomisation": {"judgement": "NO_INFORMATION"},
        "D5_selection_of_the_reported_result": {"judgement": "SOME_CONCERNS"}},
        "overall": "SOME_CONCERNS"},
    "NCT22222222": {"trial": "FIXTURE-B",
                    "domains": {"D1_randomisation": {"judgement": "LOW"}},
                    "overall": "SOME_CONCERNS"}}}

PAYLOAD_ADDS = json.loads(json.dumps(CURATED["risk_of_bias"]["by_outcome"]))
PAYLOAD_ADDS["primary"]["NCT33333333"] = {
    "trial": "FIXTURE-C", "domains": {"D1_randomisation": {"judgement": "LOW"}},
    "overall": "LOW"}

PAYLOAD_DROPS = {"primary": {"NCT11111111": json.loads(json.dumps(
    CURATED["risk_of_bias"]["by_outcome"]["primary"]["NCT11111111"]))}}


def rob_bundle(by_outcome):
    return {"authority": AUTHORITY, "default_rule": CURATED["risk_of_bias"]["default_rule"],
            "ceiling": {"no_result_can_reach_LOW": True},
            "by_topic": {"fixture-topic": by_outcome}}


def sha(p):
    return hashlib.sha256(io.open(p, "rb").read()).hexdigest()


def build():
    if os.path.isdir(TMP):
        shutil.rmtree(TMP)
    os.makedirs(os.path.join(TMP, "fixture-topic"))
    p = os.path.join(TMP, "fixture-topic", "fixture-topic.json")
    io.open(p, "w", encoding="utf-8").write(json.dumps(CURATED, indent=1))
    return p


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    results = []

    p = build()
    baseline = sha(p)
    print("FIXTURE   %s" % p)
    print("BASELINE  sha256 %s" % baseline)
    print("MODULE    %s" % M.__file__)
    print()

    # 1 KNOWN POSITIVE -- the real merge(), against the fixture tree
    print("--- CHECK 1: merge must REFUSE a payload that changes stored judgements")
    res = M.merge("fixture-topic", {}, rob_bundle(PAYLOAD_CHANGES), {}, root=TMP)
    print(res)
    ok1 = res.startswith("REFUSED")
    same1 = sha(p) == baseline
    print("    fixture unchanged by the refused run: %s" % same1)
    results.append(("1 KNOWN POSITIVE   changed judgement -> REFUSES", ok1 and same1))
    print()

    # 2 THE OLD GUARD, RECONSTRUCTED, MUST MISS IT
    print("--- CHECK 2: the OLD key-path guard on the same payload")
    obj = json.load(io.open(p, encoding="utf-8"))
    after = json.loads(json.dumps(obj))
    after["risk_of_bias"]["by_outcome"] = PAYLOAD_CHANGES
    lost = sorted(q for q in (M.key_paths(obj) - M.key_paths(after))
                  if ".by_outcome" not in q and not q.endswith("by_outcome"))
    print("    nested key paths it reports lost: %d  %s"
          % (len(lost), lost[:4] if lost else "(none)"))
    print("    -> the old guard PASSES this write. Two judgements change silently.")
    results.append(("2 OLD GUARD MISSES it (reports no loss)", len(lost) == 0))
    print()

    # 3 NEGATIVE CONTROL -- pure addition must go through
    print("--- CHECK 3: a payload that only ADDS a result must be written")
    build()
    res3 = M.merge("fixture-topic", {}, rob_bundle(PAYLOAD_ADDS), {}, root=TMP)
    print("    %s" % res3)
    obj3 = json.load(io.open(p, encoding="utf-8"))
    kept = obj3["risk_of_bias"]["by_outcome"]["primary"]
    ok3 = (not res3.startswith("REFUSED")
           and kept["NCT11111111"]["domains"]["D1_randomisation"]["judgement"] == "SOME_CONCERNS"
           and "NCT33333333" in kept)
    print("    stored judgement preserved and new result present: %s" % ok3)
    results.append(("3 NEGATIVE CONTROL pure addition -> writes", ok3))
    print()

    # 4 DROPPED RESULT
    print("--- CHECK 4: a payload that omits an existing result must be refused")
    build()
    res4 = M.merge("fixture-topic", {}, rob_bundle(PAYLOAD_DROPS), {}, root=TMP)
    print(res4)
    results.append(("4 DROPPED RESULT detected -> REFUSES",
                    res4.startswith("REFUSED") and "DROPPED" in res4))
    print()

    # 5 ESCAPE HATCH
    print("--- CHECK 5: --allow-overwrite naming the topic must let it through")
    build()
    res5 = M.merge("fixture-topic", {}, rob_bundle(PAYLOAD_CHANGES), {}, root=TMP,
                   allow_overwrite=("fixture-topic",))
    print("    %s" % res5)
    obj5 = json.load(io.open(p, encoding="utf-8"))
    moved = (obj5["risk_of_bias"]["by_outcome"]["primary"]["NCT11111111"]
             ["domains"]["D1_randomisation"]["judgement"])
    ok5 = (not res5.startswith("REFUSED")) and moved == "NO_INFORMATION"
    print("    judgement actually replaced under authorisation: %s (%s)" % (ok5, moved))
    results.append(("5 ESCAPE HATCH named topic -> writes", ok5))
    print()

    # 6 RESTORATION
    print("--- CHECK 6: rebuild the fixture and assert it is byte-identical")
    build()
    final = sha(p)
    print("    baseline %s" % baseline)
    print("    final    %s" % final)
    results.append(("6 RESTORATION fixture byte-identical", final == baseline))
    shutil.rmtree(TMP, ignore_errors=True)
    print()

    print("=" * 74)
    passed = sum(1 for _, o in results if o)
    for label, o in results:
        print("  %-52s %s" % (label, "PASS" if o else "FAIL"))
    print("=" * 74)
    print("  %d of %d" % (passed, len(results)))
    if passed != len(results):
        sys.exit("PLANT FAILED -- the guard is not proven")
    return 0


if __name__ == "__main__":
    sys.exit(main())
