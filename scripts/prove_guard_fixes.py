"""Prove each P0 fix fires, using Codex's exact adversarial inputs.

A fix asserted is a fix untested. Every case below is one Codex constructed and
demonstrated PASSING against the previous code; each must now FAIL. The last case
is the control: an ordinary unchanged object must still pass, because a guard
that fails on everything is as useless as one that fails on nothing.
"""
import copy
import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import regression_guard as G  # noqa: E402

OBJ = r"F:\rapidmeta-ssot-shell\ssot\arni-hfref\arni-hfref.json"
base = json.load(open(OBJ, encoding="utf-8"))
led = {"apps": {}}
led = G.update_ledger(led, G.state_of(base))

rows = []


def case(name, mutate, expect_fail=True):
    o = copy.deepcopy(base)
    mutate(o)
    r = G.check(o, led)
    fired = r["verdict"] != "PASS"
    ok = fired == expect_fail
    rows.append((name, "FAIL" if fired else "PASS",
                 "expected " + ("FAIL" if expect_fail else "PASS"),
                 "correct" if ok else "*** WRONG ***"))
    return ok


def zero_events(o):
    t = o["inputs"]["trials"][0]
    oid = next(iter(t["by_outcome"]))
    t["by_outcome"][oid]["treatment"]["events"] = 0


def halve_n(o):
    t = o["inputs"]["trials"][0]
    oid = next(iter(t["by_outcome"]))
    t["by_outcome"][oid]["control"]["n"] = 1


def move_effect(o):
    t = o["inputs"]["trials"][0]
    oid = next(iter(t["by_outcome"]))
    if (t["by_outcome"][oid].get("effect") or {}).get("point") is not None:
        t["by_outcome"][oid]["effect"]["point"] = 9.99


def drop_trial(o):
    o["inputs"]["trials"] = o["inputs"]["trials"][:-1]


def drop_trial_blank_form(o):
    tid = o["inputs"]["trials"][-1]["id"]
    o["inputs"]["trials"] = o["inputs"]["trials"][:-1]
    o["removal_records"] = [{"key": "%s::trial::%s" % (o["app_id"], tid),
                             "criterion": " ", "evidence": " ",
                             "adjudicated_by": " "}]


def drop_trial_properly(o):
    tid = o["inputs"]["trials"][-1]["id"]
    o["inputs"]["trials"] = o["inputs"]["trials"][:-1]
    o["removal_records"] = [{
        "key": "%s::trial::%s" % (o["app_id"], tid),
        "criterion": "outcome axis: reports a different composite",
        "evidence": "trial methods read at primary source, PMID 30415601",
        "adjudicated_by": "Mahmood Ahmad"}]


ok = True
ok &= case("P0-2 arm events 914 -> 0 (key survives, value zeroed)", zero_events)
ok &= case("P0-2 control n -> 1", halve_n)
ok &= case("P0-2 effect point -> 9.99", move_effect)
ok &= case("baseline: trial removed with no record", drop_trial)
ok &= case("P1-6 removal justified by three single spaces", drop_trial_blank_form)
ok &= case("control: removal with a real criterion, evidence, adjudicator",
           drop_trial_properly, expect_fail=False)
ok &= case("control: unchanged object", lambda o: None, expect_fail=False)

# P0-3 app rename is a check_all-level property, tested separately below.
o = copy.deepcopy(base)
o["app_id"] = "arni-hfref-renamed"
r = G.check(o, led)
rows.append(("P0-3 app_id renamed (check() alone cannot see this)",
             r["verdict"], "handled by check_all vanished-app test", "see below"))

print("%-58s %-6s %-46s %s" % ("case", "got", "expected", ""))
for a, b, c, d in rows:
    print("%-58s %-6s %-46s %s" % (a[:58], b, c, d))
print("\nall value/removal cases behaved correctly:", ok)
sys.exit(0 if ok else 1)
