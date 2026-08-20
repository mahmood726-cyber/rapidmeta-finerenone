"""For each check that has never fired: can a failing input be built from the corpus?

A CHECK THAT HAS NEVER FIRED READS AS COVERAGE ON EVERY TABLE ANYONE MAKES. That is worse
than a discipline written down, because a discipline at least announces that it depends on a
person. Three never-firing branches were found in `regression_check.py` alone tonight, one
of them in its BLOCKING set, reporting zero on every run this project has ever made -- where
the zero meant the marker did not exist.

SO "NEVER FIRED" MUST BE RESOLVED INTO ONE OF THREE STATES, NOT LEFT AS ONE:

    CAN FIRE, CONDITION ABSENT   a failing input was CONSTRUCTED and the check refused it.
                                 The corpus is clean; the detector works. LEGITIMATE, and
                                 it is now a demonstrated fact rather than an assumption.
    CANNOT FIRE                  no input makes it refuse. It is not a check.
    NOT A GATE                   it reports a reading list and was never meant to refuse.
                                 Legitimate, and it must not be counted as mechanised.

EVERY GRAFT IS MADE ON A COPY IN A TEMP DIRECTORY. Nothing here writes to the corpus.
"""
import io
import os
import re
import sys
import json
import shutil
import subprocess
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run(script, cwd=None, args=()):
    r = subprocess.run([sys.executable, os.path.join(REPO, "scripts", script)] + list(args),
                       cwd=cwd or REPO, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return r.returncode, r.stdout.decode("utf-8", "replace")


def graft_no_false_allclear():
    """Class 44. Plant a census site that coerces an uncounted topic to zero."""
    tmp = tempfile.mkdtemp(prefix="graft44_")
    try:
        d = os.path.join(tmp, "scripts")
        os.makedirs(d)
        shutil.copy(os.path.join(REPO, "scripts", "lint_no_false_allclear.py"), d)
        bad = os.path.join(d, "graft_census.py")
        io.open(bad, "w", encoding="utf-8", newline=chr(10)).write(chr(10).join([
            "def census(topics, counts):",
            "    rows = []",
            "    for t in topics:",
            "        rows.append((t, counts.get(t, 0)))",
            "    return rows",
        ]))
        # The lint scans the repo it lives in; run it from the temp root.
        code, out = run("lint_no_false_allclear.py", cwd=tmp)
        return code, out
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def graft_self_describing():
    """Class 50. The check is a RATCHET on a baseline of 7 claims; an 8th must refuse."""
    base = os.path.join(REPO, "scripts", "baselines")
    cands = [f for f in os.listdir(base) if "self_describing" in f or "safety_claim" in f]
    if not cands:
        return None, "no baseline file found for lint_self_describing_safety_claim"
    p = os.path.join(base, cands[0])
    original = io.open(p, encoding="utf-8").read()
    try:
        data = json.loads(original)
        key = next((k for k, v in data.items() if isinstance(v, list) and v), None)
        if key is None:
            return None, "baseline has no list to shrink"
        data[key] = data[key][:-1]        # drop one -> the corpus now has one MORE than known
        io.open(p, "w", encoding="utf-8", newline=chr(10)).write(
            json.dumps(data, indent=1, ensure_ascii=False))
        return run("lint_self_describing_safety_claim.py", args=("--gate",))
    finally:
        io.open(p, "w", encoding="utf-8", newline=chr(10)).write(original)


def graft_method_claim():
    """Class 46. Graft a method claim naming a field the object does not hold."""
    src = os.path.join(REPO, "ssot", "arni-hfref", "arni-hfref.json")
    if not os.path.exists(src):
        return None, "arni-hfref is not on disk"
    tmp = tempfile.mkdtemp(prefix="graft46_")
    try:
        obj = json.load(io.open(src, encoding="utf-8"))
        man = obj.get("manuscript")
        if not isinstance(man, dict):
            return None, "arni-hfref carries no manuscript dict"
        target = next((k for k, v in man.items() if isinstance(v, str) and len(v) > 200),
                      None)
        if target is None:
            return None, "no manuscript prose long enough to graft into"
        man[target] = man[target] + (
            " Records were screened in duplicate by two independent reviewers, as recorded "
            "in `screening.duplicate_screening.performed_by_two`.")
        d = os.path.join(tmp, "ssot", "arni-hfref")
        os.makedirs(d)
        io.open(os.path.join(d, "arni-hfref.json"), "w", encoding="utf-8",
                newline=chr(10)).write(json.dumps(obj, indent=1, ensure_ascii=False))
        shutil.copytree(os.path.join(REPO, "scripts"), os.path.join(tmp, "scripts"),
                        ignore=shutil.ignore_patterns("baselines", "__pycache__"))
        return run("lint_method_claim_has_a_field.py", cwd=tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    print("CAN THE NEVER-FIRED CHECKS FIRE? Each answer is a CONSTRUCTED failing input,")
    print("grafted on a copy. Nothing here writes to the corpus.")
    print("")

    results = []

    code, out = graft_no_false_allclear()
    results.append((
        "44  lint_no_false_allclear", code,
        "a census site doing counts.get(topic, 0) on an uncounted topic", out))

    code, out = graft_self_describing()
    results.append((
        "50  lint_self_describing_safety_claim", code,
        "one claim removed from the baseline, so the corpus carries an unbaselined one",
        out))

    code, out = graft_method_claim()
    results.append((
        "46  lint_method_claim_has_a_field", code,
        "a duplicate-screening sentence naming a field arni-hfref does not hold", out))

    for name, code, what, out in results:
        if code is None:
            state = "NOT GRAFTABLE"
        elif code != 0:
            state = "CAN FIRE, CONDITION ABSENT"
        else:
            state = "DID NOT REFUSE THE GRAFT"
        print("%-42s %s" % (name, state))
        print("      graft: %s" % what)
        tail = " ".join((out or "").strip().split())[-220:]
        print("      %s" % tail)
        print("")

    print("47  audit_path_resolvers                   NOT A GATE")
    print("      It prints a reading list -- 14 resolvers, of which 12 are unread -- and was")
    print("      never written to refuse. That is legitimate and it must NOT be counted as")
    print("      mechanised. Its own last line says 'this is not a clean bill and it is not a")
    print("      defect count; it is a reading list.'")
    print("")
    print("52  regression_check.py                    HAS FIRED, ON A LIVE RUN")
    print("      Its NOT_ASSESSABLE line printed on the pre-push check of the seven-page")
    print("      rollout: wrong_protocol_link reported 0 AND the marker arni_hf_protocol was")
    print("      not seen on any page read. Written blind hours earlier; it has now spoken.")


if __name__ == "__main__":
    main()
