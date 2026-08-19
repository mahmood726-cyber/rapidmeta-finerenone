#!/usr/bin/env python3
"""ROUTE 7: A SCREENER THAT ASKS THE NEIGHBOURING TOPIC'S QUESTION UNDER THIS TOPIC'S NAME.

THE INSTANCE. The first version of `screen_rhythm_control_remainder_2026_08_19.py` was a
`sed`-rename of the sibling's `screen_ablation_medical_remainder_2026_08_19.py`. It parsed
cleanly, ran, and produced a complete set of 551 verdicts -- every one answering the SIBLING'S
question, because those rules ask whether ABLATION is the contrast.

    THE SIX EARLIER CONTAMINATION ROUTES CARRIED ONE TOPIC'S **DATA** INTO ANOTHER. THIS
    CARRIES ONE TOPIC'S **CRITERIA**, and the output is not corrupt, empty or malformed -- it
    is COMPLETE, PLAUSIBLE AND INVERTED.

    An arm declaring `Drug: Amiodarone` is the INTERVENTION for the rhythm-control review and
    the COMPARATOR for the ablation review. The same arm text means OPPOSITE things to the two
    reviews, which is precisely why they are two reviews -- and it is what a rename leaves
    untouched.

WHY NO EXISTING GUARD SEES IT. The file is new, the filename is right, the topic key is right,
the docstring is right after a rename, and every contamination check in this repository passes.
Nothing is malformed, so nothing looks wrong.

WHAT THIS CHECKS, AND WHY IT IS BEHAVIOURAL RATHER THAN STRUCTURAL.

A fingerprint over source text would be defeated by the very edit it is meant to catch -- a
rename changes names and leaves rules. So the fingerprint is over WHAT THE RULES DO: each
screener is handed a fixed set of REAL arm structures and must classify them the way its own
review's criteria require. The probe set is chosen to be DISCRIMINATING -- at least one arm
whose role differs between the two reviews -- because a probe both screeners answer the same
way cannot tell them apart.

    `Drug: Amiodarone`  ->  ablation review: a MEDICAL/comparator arm
                        ->  rhythm review:   a RHYTHM/intervention arm

That single probe is the whole detector. The rest are there so a partial rename is caught too.

THE PROBES ARE REAL ARM RECORDS FROM THIS CORPUS, not invented shapes -- detector 10's rule.
Each carries the registration it was read from.
"""
import importlib.util
import io
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(REPO, "scripts")

# --- REAL arm records, each with the registration it came from ---------------------------
PROBES = [
    ("amiodarone",       {"type": "ACTIVE_COMPARATOR", "label": "Amiodarone",
                          "interventionNames": ["Drug: Amiodarone"]},          "NCT00729911"),
    ("rate control",     {"type": "ACTIVE_COMPARATOR", "label": "Rate Control",
                          "interventionNames": ["Other: Rate Control"]},       "NCT01420393"),
    ("catheter ablation", {"type": "EXPERIMENTAL", "label": "Catheter Ablation",
                           "interventionNames": ["Procedure: Catheter ablation"]},
     "NCT06560047"),
    ("av nodal ablation", {"type": "EXPERIMENTAL", "label": "AV nodal ablation",
                           "interventionNames": ["Procedure: AV nodal ablation"]},
     "NCT01522898"),
    ("conventional",     {"type": "ACTIVE_COMPARATOR", "label": "2",
                          "interventionNames": ["Other: Conventional treatment"]},
     "NCT00643188"),
    ("no intervention",  {"type": "NO_INTERVENTION", "label": "Usual care",
                          "interventionNames": None},                          "NCT01288352"),
]

# --- WHAT EACH REVIEW'S CRITERIA REQUIRE. Written from the criteria blocks, not from the
# --- code, so a screener that drifts from its own review is caught as well as one that was
# --- copied from another.
EXPECTED = {
    "screen_ablation_medical_remainder_2026_08_19": {
        "topic": "ablation-af-medical-therapy",
        "kinds": {"amiodarone": "MEDICAL", "rate control": "MEDICAL",
                  "catheter ablation": "ABLATION", "av nodal ablation": "NODAL",
                  "conventional": "MEDICAL", "no intervention": "NONE"},
        "why": "the contrast is ABLATION against medical therapy, so every drug arm -- rate or "
               "rhythm -- is on the COMPARATOR side.",
    },
    "screen_rhythm_control_remainder_2026_08_19": {
        "topic": "early-rhythm-control-af",
        "kinds": {"amiodarone": "RHYTHM", "rate control": "RATE",
                  "catheter ablation": "RHYTHM", "av nodal ablation": "NODAL",
                  "conventional": "USUAL", "no intervention": "NONE"},
        "why": "the contrast is a RHYTHM-CONTROL STRATEGY against rate control or usual care, "
               "so an antiarrhythmic arm is the INTERVENTION and a rate-control arm is the "
               "comparator.",
    },
}

DISCRIMINATING = "amiodarone"


def load(mod_name):
    path = os.path.join(SCRIPTS, mod_name + ".py")
    if not os.path.exists(path):
        return None
    spec = importlib.util.spec_from_file_location(mod_name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod
    spec.loader.exec_module(mod)
    return mod


def fingerprint(mod):
    if not hasattr(mod, "arm_kind"):
        return None
    return {name: mod.arm_kind(arm) for name, arm, _nct in PROBES}


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    failures, checked = [], 0

    # THE DISCRIMINATING PROBE MUST ACTUALLY DISCRIMINATE, or this detector is decorative.
    want = {n: e["kinds"][DISCRIMINATING] for n, e in EXPECTED.items()}
    if len(set(want.values())) < 2:
        print("REFUSED: the probe %r is expected to give the SAME kind in every registered "
              "screener, so it cannot tell them apart. A fingerprint over a non-discriminating "
              "probe passes everything." % DISCRIMINATING)
        return 2
    print("discriminating probe %r expects: %s" % (DISCRIMINATING, want))
    print()

    for mod_name, exp in sorted(EXPECTED.items()):
        mod = load(mod_name)
        if mod is None:
            print("%-52s NOT_ASSESSABLE -- file absent" % mod_name)
            continue
        got = fingerprint(mod)
        if got is None:
            print("%-52s NOT_ASSESSABLE -- no arm_kind() to probe" % mod_name)
            continue
        checked += 1
        bad = {k: (got.get(k), v) for k, v in exp["kinds"].items() if got.get(k) != v}
        print("%-52s %s" % (mod_name, "OK" if not bad else "MISMATCH"))
        print("      declares topic %r -- %s" % (exp["topic"], exp["why"]))
        if bad:
            for probe, (g, w) in sorted(bad.items()):
                nct = next(n for nm, _a, n in PROBES if nm == probe)
                print("      probe %-20s from %s: got %-18s expected %s"
                      % (probe, nct, g, w))
            other = [n for n in EXPECTED
                     if n != mod_name and all(
                         got.get(k) == EXPECTED[n]["kinds"][k] for k in got)]
            if other:
                print("      AND IT MATCHES ANOTHER REVIEW'S FINGERPRINT EXACTLY: %s"
                      % ", ".join(other))
                print("      That is route 7: this screener asks %r's question under %r's name."
                      % (EXPECTED[other[0]]["topic"], exp["topic"]))
            failures.append(mod_name)
        print()

    print("screeners probed %d" % checked)
    if failures:
        print("\nREFUSED: %d screener(s) do not implement their own review's criteria."
              % len(failures))
        print("A screener that asks the neighbouring topic's question produces a COMPLETE,")
        print("PLAUSIBLE, INVERTED answer set, and nothing about its output looks wrong.")
        return 1
    print("\nevery screener classifies the discriminating probes the way its own review's")
    print("criteria require.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
