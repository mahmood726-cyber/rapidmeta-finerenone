"""SUBJECT IS EXPERIMENTAL -- is the drug this topic is NAMED for the thing being TESTED?

WHY THIS EXISTS
    OLMESARTAN_HTN carried three trials and olmesartan was the ACTIVE_COMPARATOR in all
    three: two tested azilsartan, one tested LCZ696. The topic contained no trial in
    which its own titled drug was the intervention. It was retired 2026-08-18 and there
    was no honest version of it -- an artefact of a drug-name search that matches a name
    ANYWHERE in a trial record instead of resolving it to an arm.

    Nothing that blocks could see it. subject_match_gate blocks on foreign registration
    ids and there were none. protocol_subject_gate reads prose and the prose was this
    page's own. And all three trials genuinely register a blood-pressure primary, so the
    poolability triage's outcome limb passed them.

A PREVIOUS ATTEMPT AT THIS CHECK PASSED ITS OWN FOUNDING CASE AND WAS REVERTED
    It asked "is the subject drug in the trial's interventions list". ClinicalTrials.gov
    lists EVERY drug there, comparators included, so the answer was yes for a comparator
    too. Matching the brief title made it worse: "... Compared to Olmesartan ..." matches.
    A check that returns PASS on the defect it was built for is not a weak check, it is
    an INVERTED one, and shipping it would have certified the defect.

    The level that decides is the ARM. `armGroups[].type` is EXPERIMENTAL or
    ACTIVE_COMPARATOR or PLACEBO_COMPARATOR, and `armGroups[].interventionNames` says
    which drug is in it. Resolve the subject to its arm and read that arm's type.

WHAT THIS CHECKS
    For each trial: does the topic's subject token appear in the interventionNames of an
    arm whose type is EXPERIMENTAL? A topic needs at least two such trials to support a
    pool about its own subject.

WHAT A FULL PASS DOES NOT ESTABLISH -- written in advance
    - NOT that a pool is warranted. Comparator, population and outcome are other limbs
      and this gate says nothing about them. RIOCIGUAT_PAH passes this gate and is still
      not poolable, because its two trials are in different diseases.
    - NOT that the subject token is the right one. It is derived from the page name, and
      a page named for a class rather than a drug ("SGLT2", "DOAC") will not resolve.
      Those return UNRESOLVED, which is not a pass.
    - NOT anything about a trial with no armGroups. Registrations vary; absence is
      reported as unreadable, never as a failure of the topic.

USAGE
    python scripts/subject_is_experimental_gate.py --selftest
    python scripts/subject_is_experimental_gate.py <subject> <NCT> [NCT ...]
"""
from __future__ import annotations
import io
import json
import sys
import urllib.error
import urllib.request

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

API = "https://clinicaltrials.gov/api/v2/studies/{}?format=json"
EXPERIMENTAL = "EXPERIMENTAL"


def arms_of(study):
    """[(arm_type, interventionNames_joined)] from a study record."""
    ai = (study.get("protocolSection") or {}).get("armsInterventionsModule") or {}
    out = []
    for a in ai.get("armGroups") or []:
        out.append((a.get("type") or "",
                    " ".join(a.get("interventionNames") or []) + " " + (a.get("label") or "")))
    return out


def role_of_subject(study, subject):
    """EXPERIMENTAL / COMPARATOR / ABSENT / NO_ARMS for the subject drug in one trial."""
    arms = arms_of(study)
    if not arms:
        return "NO_ARMS"
    s = subject.lower()
    exp = [t for t, names in arms if s in names.lower() and t == EXPERIMENTAL]
    any_hit = [t for t, names in arms if s in names.lower()]
    if exp:
        return "EXPERIMENTAL"
    if any_hit:
        return "COMPARATOR"
    return "ABSENT"


def assess(subject, studies):
    """studies: {nct: study record}."""
    roles = {n: role_of_subject(s, subject) for n, s in studies.items()}
    exp = [n for n, r in roles.items() if r == "EXPERIMENTAL"]
    comp = [n for n, r in roles.items() if r == "COMPARATOR"]
    noarms = [n for n, r in roles.items() if r == "NO_ARMS"]
    absent = [n for n, r in roles.items() if r == "ABSENT"]

    if noarms and len(noarms) == len(roles):
        return ("UNRESOLVED", "no registration on this topic declares arm groups, so the "
                "subject's role cannot be read. Not a pass", roles)
    if not exp and comp:
        return ("FAIL",
                "THE TOPIC'S OWN SUBJECT IS THE COMPARATOR AND NEVER THE INTERVENTION. "
                "It appears in %d trial(s), in a comparator arm every time. There is no "
                "trial here in which the drug this topic is named for is the thing being "
                "tested." % len(comp), roles)
    if len(exp) < 2:
        return ("REVIEW",
                "the subject is the intervention in only %d trial(s); %d carry it as a "
                "comparator and %d not at all. Not enough for a pool about this subject"
                % (len(exp), len(comp), len(absent)), roles)
    return ("PASS",
            "the subject is in an EXPERIMENTAL arm in %d trial(s)" % len(exp), roles)


def fetch(nct):
    req = urllib.request.Request(API.format(nct), headers={"User-Agent": "rapidmeta-gate"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


# --------------------------------------------------------------------- fixtures
def _study(*arms):
    return {"protocolSection": {"armsInterventionsModule": {"armGroups": [
        {"type": t, "interventionNames": ["Drug: " + d], "label": d} for t, d in arms]}}}


def selftest() -> int:
    ok = True

    # THE FOUNDING PAIR. Same shape, same outcome, differing ONLY in which arm the
    # subject drug sits in. The reverted version returned the SAME verdict for both.
    OLM = {
        "NCT00846365": _study(("EXPERIMENTAL", "Azilsartan medoxomil and chlorthalidone"),
                              ("ACTIVE_COMPARATOR", "Olmesartan medoxomil-hydrochlorothiazide")),
        "NCT01033071": _study(("EXPERIMENTAL", "Azilsartan medoxomil and chlorthalidone"),
                              ("ACTIVE_COMPARATOR", "Olmesartan medoxomil and hydrochlorothiazide")),
        "NCT01599104": _study(("EXPERIMENTAL", "LCZ696"),
                              ("ACTIVE_COMPARATOR", "Olmesartan")),
    }
    AZI = {
        "NCT00846365": _study(("EXPERIMENTAL", "Azilsartan medoxomil and chlorthalidone"),
                              ("ACTIVE_COMPARATOR", "Olmesartan medoxomil-hydrochlorothiazide")),
        "NCT01033071": _study(("EXPERIMENTAL", "Azilsartan medoxomil and chlorthalidone"),
                              ("ACTIVE_COMPARATOR", "Olmesartan medoxomil and hydrochlorothiazide")),
    }
    RIO = {
        "NCT00810693": _study(("EXPERIMENTAL", "Riociguat (Adempas, BAY63-2521)"),
                              ("PLACEBO_COMPARATOR", "Placebo")),
        "NCT00855465": _study(("EXPERIMENTAL", "Riociguat (Adempas, BAY63-2521)"),
                              ("PLACEBO_COMPARATOR", "Placebo")),
    }

    cases = [
        ("FOUNDING/false: OLMESARTAN -- subject is the COMPARATOR in all three",
         "olmesartan", OLM, "FAIL"),
        ("FOUNDING/true: AZILSARTAN -- THE SAME TWO TRIALS, subject is EXPERIMENTAL",
         "azilsartan", AZI, "PASS"),
        ("a subject experimental in only one trial is REVIEW, not a pass",
         "lcz696", OLM, "REVIEW"),
        ("RIOCIGUAT passes THIS limb and is still not poolable -- other limbs are "
         "not this gate's business",
         "riociguat", RIO, "PASS"),
        ("a topic whose registrations declare no arms is UNRESOLVED, never a pass",
         "anything", {"NCT00000000": {"protocolSection": {}}}, "UNRESOLVED"),
    ]
    for label, subject, studies, want in cases:
        v, why, roles = assess(subject, studies)
        good = v == want
        ok &= good
        print("  %-72s -> %-11s (want %-11s) %s"
              % (label[:72], v, want, "correct" if good else "WRONG"))
        if not good:
            print("        %s   roles=%s" % (why[:120], roles))

    print()
    print("WHAT A FAILURE WOULD LOOK LIKE: the two founding cases returning the SAME")
    print("verdict. They are THE SAME TWO TRIALS under two different subject names, so a")
    print("check that reads anything other than the ARM cannot tell them apart -- and the")
    print("previous version of this gate could not. It passed OLMESARTAN, the page it was")
    print("written to catch.")
    print("-> SELFTEST PASS" if ok else "-> SELFTEST FAILED")
    return 0 if ok else 1


def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] == "--selftest":
        return selftest()
    subject, ncts = sys.argv[1], sys.argv[2:]
    studies = {}
    for n in ncts:
        try:
            studies[n] = fetch(n)
        except urllib.error.HTTPError as e:
            print("  %s  FETCH FAILED HTTP %d" % (n, e.code))
    v, why, roles = assess(subject, studies)
    for n, r in sorted(roles.items()):
        print("  %-14s %s" % (n, r))
    print("  -> %s  %s" % (v, why))
    return 1 if v == "FAIL" else 0


if __name__ == "__main__":
    sys.exit(main())
