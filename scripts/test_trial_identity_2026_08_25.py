"""Validate the trial-identity rule against the REAL mismatches, not three exemplars.

MAHMOOD: "Validate against all 33 known mismatches, not just the three: a matcher that passes
its three exemplars and fails the other 30 would be the vocabulary-versus-property error
again."

The sweep finished at 139 pages, 29 MISMATCH, 42 mismatched trial records. This runs the new
rule over every one of them AND over a sample of the CLEAN pages, because a matcher change
can break what was right as easily as fix what was wrong.

WHAT EACH CASE IS BUILT FROM. The sweep recorded, per trial, the NCT id, whether it studies
the subject, and the ROLE the adjudicator assigned -- EXPERIMENTAL, COMPARATOR, BACKGROUND or
ABSENT. That role is the ground truth the new rule has to reproduce from the intervention
names alone. Where the object stores no intervention names for a trial the case is reported
UNTESTABLE rather than passed: a rule that cannot see the data cannot be credited with
getting it right.

THE THREE NAMED CONTROLS ARE INCLUDED AS EXPLICIT CASES so a regression on any of them fails
loudly by name rather than as one line of a summary count.
"""
import io
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "ssot"))
sys.path.insert(0, os.path.join(REPO, "scripts"))
import trial_identity as T
import instrument_controls

SWEEP = os.path.join(REPO, "outputs", "trial_identity_sweep_2026_08_25.jsonl")

# The three failure modes, written as the cases a naive matcher gets wrong.
NAMED = [
    ("combination -- taniborbactam is not tazobactam",
     ["cefepime tazobactam"], ["cefepime/VNRX-5133", "meropenem"], None, False),
    ("combination -- the bare component must not match the combination",
     ["cefepime"], ["cefepime/VNRX-5133"], None, False),
    ("combination -- amoxicillin is not amoxicillin-clavulanate",
     ["amoxicillin"], ["amoxicillin-clavulanate", "placebo"], None, False),
    ("comparator -- RAMBLE randomises rivaroxaban against apixaban",
     ["apixaban"], ["rivaroxaban", "apixaban"], ["rivaroxaban"], False),
    ("background -- TWILIGHT gives ticagrelor to everyone and randomises aspirin",
     ["ticagrelor"], ["ticagrelor", "aspirin", "placebo"], ["aspirin", "placebo"], False),
    ("plain match must still pass",
     ["apixaban"], ["apixaban", "warfarin"], ["apixaban"], True),
    ("the combination topic must match its own combination",
     ["cefepime tazobactam"], ["WCK 4282 (FEP-TAZ)", "meropenem"], None, False),
    ("a code name for the combination matches when named as a synonym",
     ["wck 4282"], ["WCK 4282 (FEP-TAZ) 4 g", "meropenem"], ["WCK 4282 (FEP-TAZ) 4 g"], True),
    ("unknown roles must not be read as NO",
     ["dabigatran"], ["dabigatran etexilate", "warfarin"], None, True),
]


def drug_patterns_for(page):
    """Topic drug tokens from the page name. Deliberately crude -- it is what the matcher
    itself has, and testing the rule with better inputs than production gets would flatter
    it."""
    base = re.sub(r"\.html$", "", page)
    parts = [p.lower() for p in re.split(r"[_\-]", base)]
    stop = {"auto", "full", "review", "ssot", "html", "2"}
    return [p for p in parts if len(p) >= 5 and p not in stop][:1]


def main():
    print("== NAMED CONTROLS (the three failure modes, by name)")
    failed = []
    for label, pats, allnames, exp, want in NAMED:
        got, why = T.studies_subject(pats, allnames, exp)
        ok = (got == want)
        print("  %-4s %-62s %s" % ("PASS" if ok else "FAIL", label, why[:60]))
        if not ok:
            failed.append(label)
    if failed:
        print()
        print("REFUSED: %d named control(s) failed: %s. The rule is not validated and no "
              "corpus count is printed." % (len(failed), "; ".join(failed)))
        return 2

    instrument_controls.require_controls(
        "trial-identity-rule",
        ("the nine named cases covering combination, comparator, background and plain match",
         len(failed), 0),
        ("a plain single-agent match, which must NOT be rejected",
         T.studies_subject(["apixaban"], ["apixaban", "warfarin"], ["apixaban"])[0], False))

    if not os.path.exists(SWEEP):
        print("\nThe sweep ledger is absent, so the corpus cases could not be run. "
              "Named controls passed; corpus validation NOT performed.")
        return 0

    print()
    print("== CORPUS CASES -- READ THE CAVEAT BEFORE THE NUMBER")
    print("   This is NOT a validation of the rule. Two things prevent that, and both were")
    print("   found by running it:")
    print()
    print("   (1) THE INPUT IS WRONG. The objects store a trial's official TITLE, not its")
    print("       per-arm intervention names. The rule is built to read interventions and")
    print("       arm roles. Feeding it titles measures the harness. 77 records store no")
    print("       intervention text at all.")
    print()
    print("   (2) THE GROUND TRUTH IS A CLAIM. The ROLE labels come from the sweep, which is")
    print("       unverified model output -- the same 'claims are not findings' problem one")
    print("       level down. RAMBLE is the proof: its registered interventions are")
    print("       ['Apixaban', 'Rivaroxaban'] and apixaban is the HYPOTHESISED BETTER arm,")
    print("       so the sweep's role=COMPARATOR is wrong. It reached the right verdict --")
    print("       the trial does not belong on an apixaban VTE page -- for the wrong reason:")
    print("       it measures MENSTRUAL BLOOD LOSS, not VTE. Validating an arm-role rule")
    print("       against labels like that would encode the error into a gate.")
    print()
    print("   So the disagreement count below is a measurement of the HARNESS and of the")
    print("   sweep's labels. It is printed because hiding it would be worse, and it is")
    print("   explicitly NOT evidence about the rule.")
    print()
    pmap = json.load(io.open(os.path.join(REPO, "ssot", "PAGE_MAP.json"), encoding="utf-8"))
    agree = disagree = untestable = 0
    misses = []
    for line in io.open(SWEEP, encoding="utf-8"):
        try:
            d = json.loads(line)
        except ValueError:
            continue
        if d.get("status") != "ok" or d["page"] not in pmap:
            continue
        path = os.path.join(REPO, pmap[d["page"]])
        if not os.path.exists(path):
            continue
        obj = json.load(io.open(path, encoding="utf-8"))
        by_nct = {}
        for t in ((obj.get("inputs") or {}).get("trials") or []):
            if isinstance(t, dict) and (t.get("nct") or t.get("trial_id")):
                by_nct[t.get("nct") or t.get("trial_id")] = t
        pats = drug_patterns_for(d["page"])
        for t in d.get("trials", []):
            rec = by_nct.get(t["nct"])
            names = []
            if rec:
                for k in ("arms", "interventions"):
                    v = rec.get(k)
                    if isinstance(v, (list, tuple)):
                        names.extend(str(x) for x in v)
                if rec.get("label"):
                    names.append(str(rec["label"]))
            if not names or not pats:
                untestable += 1
                continue
            want = (t["studies_subject"] == "YES")
            got, why = T.studies_subject(pats, names, None)
            if got == want:
                agree += 1
            else:
                disagree += 1
                if len(misses) < 12:
                    misses.append((d["page"], t["nct"], t["role"],
                                   "wanted %s" % want, why[:70]))
    total = agree + disagree
    print("  cases with intervention text to test : %d" % total)
    print("  rule agrees with the sweep's label   : %d  (%.0f%%)  -- see caveat above"
          % (agree, 100.0 * agree / max(total, 1)))
    print("  rule disagrees                       : %d" % disagree)
    print("  no intervention text stored          : %d   <- UNTESTABLE, not passed"
          % untestable)
    if misses:
        print()
        print("  disagreements (first %d):" % len(misses))
        for m in misses:
            print("    %-40s %-12s role=%-12s %s | %s" % (m[0][:38], m[1], m[2], m[3], m[4]))
    print()
    print("WHAT WOULD ACTUALLY VALIDATE THIS RULE, and none of it is available here:")
    print("  * an AACT snapshot with design_groups.txt and design_group_interventions.txt,")
    print("    which is what the matcher consumes. AACT_DIR is unset and ~/AACT is absent, so")
    print("    the matcher itself cannot be re-run on this machine.")
    print("  * per-trial arm-group types from the registry. The c-trials tool returns an")
    print("    intervention LIST without arm roles, so it cannot supply them either.")
    print("  * verified role labels rather than swept ones.")
    print()
    print("Until one of those exists the rule ships validated on its NINE NAMED CASES only,")
    print("each built from a fact checked by hand -- taniborbactam is not tazobactam, WCK")
    print("4282 is cefepime-tazobactam, TWILIGHT randomises aspirin on universal ticagrelor.")
    print("That is a real but narrow warrant and it is stated as such.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
