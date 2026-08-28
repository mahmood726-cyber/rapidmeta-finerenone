"""GATE 1 -- a named trial must be the trial its registration says it is.

THE MOTIVATING CASE, AND IT IS LIVE. `agyw-hiv-prep-review` labels NCT01539226 "ASPIRE /
MTN-020" and NCT01617096 "The Ring Study". Both are wrong, and they are wrong by being each
other. A swapped name reads perfectly: two real trials, two real registrations, correct
spelling, plausible order. Nothing in the corpus contradicts it, because the name is the only
place the identity is asserted.

THE AUTHORITY IS OUTSIDE THIS CODEBASE. Every row of PINNED below was read from the
ClinicalTrials.gov API on 2026-08-28 by this lane, and the field that settles it is recorded
beside it. A control keyed to our own store would agree with the store by construction --
which is the failure this gate exists to catch.

WHY THE RULE IS CONTRADICTION, NOT EQUALITY. "FOCUS-style trial, IV ceftriaxone comparator"
is a DESCRIPTOR, not a claimed name, and demanding equality would accuse it. So the gate flags
a label only when it names a DIFFERENT pinned trial than its own registration -- which is
exactly the swap -- and reports descriptors as their own kind rather than folding them into
either pass or fail.

VACUOUS-PASS IS A FAILURE HERE. All four registrations are registered as named positives. If
the traversal never reaches one -- a filter, a renamed field, a moved file -- the gate exits
VACUOUS and never PASS. On 2026-08-28 three separate filters each hid the one case an
instrument was built to find, and nothing in the output said so.
"""
from __future__ import annotations

import copy
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _harness as H                                                        # noqa: E402

# ---------------------------------------------------------------------------
# THE AUTHORITY. Read from ClinicalTrials.gov, not from this repository.
# ---------------------------------------------------------------------------
PINNED = {
    "NCT01539226": {
        "name": "The Ring Study",
        # distinctive tokens that identify THIS trial and no other pinned one
        "aliases": ("the ring study", "ipm 027", "ipm027"),
        "authority": ("ClinicalTrials.gov NCT01539226, read 2026-08-28: sponsor "
                      "'International Partnership for Microbicides, Inc.', acronym null, "
                      "enrolment 1959, eligibility text names 'the IPM 027 trial'. "
                      "IPM 027 is The Ring Study."),
    },
    "NCT01617096": {
        "name": "ASPIRE",
        "aliases": ("aspire", "mtn-020", "mtn 020", "mtn020"),
        "authority": ("ClinicalTrials.gov NCT01617096, read 2026-08-28: acronym field is "
                      "literally 'ASPIRE'; detailed_description begins 'MTN-020 will enrol "
                      "approximately 3676...'; enrolment 2629."),
    },
    "NCT00509106": {
        "name": "FOCUS 1",
        "aliases": ("focus 1", "focus-1", "focus i "),
        "authority": ("ClinicalTrials.gov NCT00509106 -- ceftaroline registrational "
                      "programme, first of the two CAP trials (FOCUS 1)."),
    },
    "NCT00621504": {
        "name": "FOCUS 2",
        "aliases": ("focus 2", "focus-2", "focus ii"),
        "authority": ("ClinicalTrials.gov NCT00621504 -- ceftaroline registrational "
                      "programme, second of the two CAP trials (FOCUS 2)."),
    },
}

# BARE "FOCUS" IS DELIBERATELY NOT AN ALIAS. It cannot discriminate FOCUS 1 from FOCUS 2, and
# an alias that cannot discriminate turns "FOCUS-style trial" into an accusation. A token that
# matches both members of a pair carries no identity information at all.

# Keys whose value is a trial's NAME. Listed rather than pattern-matched, because a pattern
# over key names is how `registration_read_utc` became three false positives elsewhere.
NAME_KEYS = ("label", "trial", "trial_name", "name", "acronym", "short_name", "display_name")
NCT_KEYS = ("nct", "trial_id", "id", "registry_id")
NCT_RE = re.compile(r"\bNCT\d{8}\b")


def _norm(s):
    return re.sub(r"\s+", " ", str(s)).strip().lower()


def names_present(text):
    """Which pinned trials does this text NAME? Word-boundary, normalised."""
    t = " " + _norm(text) + " "
    hit = set()
    for nct, spec in PINNED.items():
        for a in spec["aliases"]:
            if re.search(r"(?<![a-z0-9])" + re.escape(a.strip()) + r"(?![a-z0-9])", t):
                hit.add(nct)
                break
    return hit


def check_objects(objects):
    """Pure. {topic: object} -> (rows, kinds). No file access, so it can be planted against."""
    rows = []
    kinds = {"label beside a pinned registration": 0,
             "  of those, CONFIRMED (names its own trial)": 0,
             "  of those, SWAPPED (names a different pinned trial)": 0,
             "  of those, DESCRIPTOR (names no pinned trial) -- not assessable": 0}
    for topic, obj in objects.items():
        for path, node in H.walk(obj):
            if not isinstance(node, dict):
                continue
            ncts = set()
            for k in NCT_KEYS:
                v = node.get(k)
                if isinstance(v, str):
                    ncts.update(NCT_RE.findall(v.upper()))
            # a risk_of_bias block is keyed BY the registration: .....primary.NCT01539226
            m = NCT_RE.search(path.upper())
            if m:
                ncts.add(m.group(0))
            pinned_here = ncts & set(PINNED)
            if len(pinned_here) != 1:
                continue
            nct = pinned_here.pop()
            for nk in NAME_KEYS:
                val = node.get(nk)
                if not isinstance(val, str) or not val.strip():
                    continue
                kinds["label beside a pinned registration"] += 1
                named = names_present(val)
                if not named:
                    kinds["  of those, DESCRIPTOR (names no pinned trial) -- not assessable"] += 1
                    verdict = "DESCRIPTOR"
                elif named == {nct}:
                    kinds["  of those, CONFIRMED (names its own trial)"] += 1
                    verdict = "CONFIRMED"
                else:
                    kinds["  of those, SWAPPED (names a different pinned trial)"] += 1
                    verdict = "SWAPPED"
                rows.append({"topic": topic, "path": path + "." + nk, "nct": nct,
                             "label": val, "verdict": verdict,
                             "names": sorted(named), "expected": PINNED[nct]["name"]})
    return rows, kinds


# ---------------------------------------------------------------------------
# the known-negative control: labels that MUST NOT be called swapped.
# Synthetic, built in memory, never written to a shared path.
# ---------------------------------------------------------------------------
KNOWN_NEGATIVES = [
    ("NCT01539226", "The Ring Study"),
    ("NCT01539226", "The Ring Study (IPM 027)"),
    ("NCT01617096", "ASPIRE"),
    ("NCT01617096", "ASPIRE / MTN-020"),
    ("NCT00509106", "FOCUS 1"),
    ("NCT00621504", "FOCUS 2"),
    # descriptors: no name claimed, so no identity to contradict
    ("NCT00509106", "FOCUS-style trial, IV ceftriaxone comparator"),
    ("NCT00621504", "second registrational trial, IV ceftriaxone comparator"),
    ("NCT01539226", "a ring-based prevention trial in southern Africa"),
    # near-miss strings that share letters with a pinned name but name nothing
    ("NCT01617096", "aspirational adherence sub-study"),
    ("NCT01617096", "the ring of sites contributing to this analysis"),
    ("NCT00509106", "refocusing the primary analysis on week 4"),
]


def run_control(gate):
    fp, examples = 0, []
    objs = {}
    for i, (nct, label) in enumerate(KNOWN_NEGATIVES):
        objs["__control_%02d" % i] = {"inputs": {"trials": [{"nct": nct, "label": label}]}}
    rows, _ = check_objects(objs)
    for r in rows:
        if r["verdict"] == "SWAPPED":
            fp += 1
            examples.append("%s labelled %r" % (r["nct"], r["label"]))
    if len(rows) != len(KNOWN_NEGATIVES):
        gate.broken("the control set did not round-trip: %d labels in, %d rows out. A control "
                    "the gate cannot see measures nothing." % (len(KNOWN_NEGATIVES), len(rows)))
    gate.control(len(KNOWN_NEGATIVES), fp, examples)


def main(argv):
    repo = H.repo_root()
    gate = H.Gate("1  TRIAL IDENTITY",
                  "a label beside a registration must not name a different pinned trial")
    gate.requires_control()
    for nct, spec in PINNED.items():
        gate.expect_case(nct, "%s -- %s" % (spec["name"], spec["authority"].split(":")[0]))

    paths, kinds_pop = H.topic_objects(repo)
    objects = {}
    for p in paths:
        try:
            objects[H.topic_id(p)] = H.load(p)
        except Exception as exc:
            gate.broken("unparseable object %s: %s" % (p, exc))

    # --hide drops the object carrying the motivating case, simulating exactly what happened
    # on 2026-08-28: a filter upstream removes the one case the instrument was built for. The
    # gate must NOT report PASS. This is the proof that the vacuous guard is load-bearing.
    if "--hide" in argv:
        objects.pop("agyw-hiv-prep-review", None)

    # --repair corrects the live swap IN MEMORY, to prove this gate can reach PASS at all.
    # A gate that has only ever said FAIL has not been shown to discriminate.
    if "--repair" in argv:
        obj = copy.deepcopy(objects.get("agyw-hiv-prep-review") or {})
        for path, node in H.walk(obj):
            if not isinstance(node, dict):
                continue
            for nk in NAME_KEYS:
                if not isinstance(node.get(nk), str):
                    continue
                ncts = {node.get(k) for k in NCT_KEYS if isinstance(node.get(k), str)}
                m = NCT_RE.search(path.upper())
                if m:
                    ncts.add(m.group(0))
                for want in ("NCT01539226", "NCT01617096"):
                    if want in ncts:
                        node[nk] = PINNED[want]["name"]
        objects["agyw-hiv-prep-review"] = obj

    # --plant swaps the two ceftaroline labels IN MEMORY, to prove the gate can fail on a
    # pair it currently passes. It never touches the store.
    planted = None
    if "--plant" in argv:
        planted = "ceftaroline FOCUS 1 <-> FOCUS 2, in memory only"
        obj = objects.get("ceftaroline-auto-full-review")
        if obj is None:
            gate.broken("--plant asked for ceftaroline-auto-full-review and it is absent")
        else:
            obj = copy.deepcopy(obj)
            for path, node in H.walk(obj):
                if isinstance(node, dict) and isinstance(node.get("label"), str):
                    if node.get("nct") == "NCT00509106" and node["label"] == "FOCUS 1":
                        node["label"] = "FOCUS 2"
                    elif node.get("nct") == "NCT00621504" and node["label"] == "FOCUS 2":
                        node["label"] = "FOCUS 1"
            objects["ceftaroline-auto-full-review"] = obj

    run_control(gate)
    rows, kinds = check_objects(objects)

    for r in rows:
        gate.saw(r["nct"])

    merged = dict(kinds_pop)
    merged.update(kinds)
    gate.kinds(merged)
    if planted:
        gate.note("PLANTED: " + planted)

    swapped = [r for r in rows if r["verdict"] == "SWAPPED"]
    keys = ["%s %s" % (r["topic"], r["path"]) for r in swapped]
    new = H.ratchet(gate, "GATE1_KNOWN_SWAPS.json", keys,
                    "trial labels naming a different pinned trial than their own "
                    "registration. Known at freeze: the agyw-hiv-prep-review pair, escalated.",
                    escalated="out/ESCALATIONS.jsonl 2026-08-28T15:05Z")
    swapped = [r for r in swapped if "%s %s" % (r["topic"], r["path"]) in set(new)]         if os.path.exists(os.path.join(repo, "gates", "GATE1_KNOWN_SWAPS.json")) else swapped
    for r in swapped:
        gate.finding("SWAPPED-NAME",
                     "%s %s carries %r, which names %s. The registration says %s. -- %s"
                     % (r["topic"], r["path"], r["label"],
                        " and ".join(PINNED[n]["name"] for n in r["names"]),
                        r["expected"], PINNED[r["nct"]]["authority"]),
                     numerator=1, denominator=len(rows))

    art = os.path.join(repo, "out", "gate1_trial_identity.json")
    os.makedirs(os.path.dirname(art), exist_ok=True)
    with open(art, "w", encoding="utf-8") as fh:
        json.dump({"gate": gate.as_json(), "rows": rows}, fh, indent=1)

    return gate.report(denominator="%d labels beside a pinned registration, in %d topic objects"
                                   % (len(rows), len(objects)))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
