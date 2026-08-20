"""Grafts that actually REACH the check, for the three that had never fired.

A CHECK THAT HAS NEVER FIRED READS AS COVERAGE ON EVERY TABLE ANYONE MAKES. Three of the
classes opened 2026-08-20 named a command that COULD fail and had never been seen to. This
resolves each into a demonstrated state rather than an assumed one.

THE FIRST ATTEMPT AT THIS FILE FAILED IN THE MOST INSTRUCTIVE WAY. It copied each lint to a
temp directory and left the grafted input somewhere the lint never looked, so two of them
reported clean -- and "did not refuse the graft" is one keystroke from "cannot fire". A
graft that misses its target reporting a clean result is the accusing direction inverted,
and it would have put two working checks on the record as vacuous.

Each lint is copied INTO the temp tree and run from there, so its REPO resolves to the temp
tree and the graft is the only corpus it can see.
"""
import io
import os
import shutil
import subprocess
import sys
import tempfile

REPO = r"F:\rapidmeta-ssot-shell"


def run_in(tmp, script, args=()):
    """Run a COPY of the lint from inside `tmp`, so its REPO resolves to tmp.

    THE FIRST ATTEMPT COPIED THE SCRIPT AND LEFT THE GRAFT SOMEWHERE THE SCRIPT NEVER
    LOOKED, so both lints reported clean and I had to stop myself calling them vacuous. A
    graft that misses its target reporting "did not refuse" is the accusing direction
    inverted, and it is the fourth time tonight I have nearly made that error.
    """
    d = os.path.join(tmp, "scripts")
    os.makedirs(d, exist_ok=True)
    shutil.copy(os.path.join(REPO, "scripts", script), d)
    r = subprocess.run([sys.executable, os.path.join(d, script)] + list(args),
                       cwd=tmp, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return r.returncode, r.stdout.decode("utf-8", "replace")


def graft_44():
    """Class 44: a census field coerced to zero. The lint keys on CENSUS_FIELDS by NAME."""
    tmp = tempfile.mkdtemp(prefix="g44_")
    try:
        os.makedirs(os.path.join(tmp, "scripts"), exist_ok=True)
        bad = os.path.join(tmp, "scripts", "graft_census.py")
        io.open(bad, "w", encoding="utf-8", newline=chr(10)).write(chr(10).join([
            "def census(obj):",
            "    cascade = obj.get('k_cascade') or {}",
            "    return {",
            "        'surfaced': cascade.get('k0_surfaced', 0),",
            "        'unscreened': cascade.get('k_unscreened_remainder', 0),",
            "    }",
        ]))
        return run_in(tmp, "lint_no_false_allclear.py")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def graft_46():
    """Class 46: a method claim naming a field the object does not hold.

    The lint reads ssot/<topic>/<topic>.json for objects carrying manuscript prose, so the
    graft is a MINIMAL object in the temp tree rather than a copy of arni-hfref -- copying
    the real one made the lint read the real corpus and report on it.
    """
    import json
    tmp = tempfile.mkdtemp(prefix="g46_")
    try:
        d = os.path.join(tmp, "ssot", "graft-topic")
        os.makedirs(d)
        obj = {
            "topic": "graft-topic",
            "manuscript": {
                "methods": ("Records were screened in duplicate by two independent "
                            "reviewers, as recorded in "
                            "`screening.duplicate_screening.performed_by_two`. "
                            "Disagreements were resolved by discussion."),
            },
            "screening": {"records": []},
        }
        io.open(os.path.join(d, "graft-topic.json"), "w", encoding="utf-8",
                newline=chr(10)).write(json.dumps(obj, indent=1, ensure_ascii=False))
        return run_in(tmp, "lint_method_claim_has_a_field.py")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def graft_50():
    """Class 50: a self-describing safety claim not in the baseline.

    The baseline lives at evidence/self_describing_safety_baseline.json under REPO. In the
    temp tree it is written EMPTY, so any claim in the grafted object is new.
    """
    import json
    tmp = tempfile.mkdtemp(prefix="g50_")
    try:
        ev = os.path.join(tmp, "evidence")
        os.makedirs(ev)
        io.open(os.path.join(ev, "self_describing_safety_baseline.json"), "w",
                encoding="utf-8", newline=chr(10)).write(
                    json.dumps({"distinct_claims": 0}, indent=1))
        d = os.path.join(tmp, "ssot", "graft-topic")
        os.makedirs(d)
        obj = {"topic": "graft-topic",
               "inputs": {"trials": [{"nct": "NCT00000000",
                                      "note": ("arm order as the registry lists it; a "
                                               "swapped pair would show as a mismatch "
                                               "here")}]}}
        io.open(os.path.join(d, "graft-topic.json"), "w", encoding="utf-8",
                newline=chr(10)).write(json.dumps(obj, indent=1, ensure_ascii=False))
        return run_in(tmp, "lint_self_describing_safety_claim.py")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


_unfired = []
for label, fn in (("44 lint_no_false_allclear", graft_44),
                  ("46 lint_method_claim_has_a_field", graft_46),
                  ("50 lint_self_describing_safety_claim", graft_50)):
    code, out = fn()
    tail = " ".join(out.strip().split())[-260:]
    print("%-40s exit=%s" % (label, code))
    print("    %s" % tail)
    print("")
    if code == 0:
        _unfired.append(label)

# A GRAFT THAT DOES NOT FIRE IS THE FINDING, SO THIS FILE REFUSES RATHER THAN REPORTS.
# Its first version printed the exit codes and returned 0 whatever they were -- a file whose
# whole subject is checks that cannot fail, that could not fail.
if _unfired:
    print("REFUSED: %d check(s) did not refuse a constructed failing input:" % len(_unfired))
    for lab in _unfired:
        print("    %s" % lab)
    sys.exit(1)
print("All grafts fired. Each check refused an input built to make it refuse.")
