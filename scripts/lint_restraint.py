#!/usr/bin/env python3
"""E4 -- THE DETECTOR FOR RESTRAINT. Every other guard in this repo catches overreach.

    EVERY GUARD WE HAVE CATCHES OVERREACH; NOTHING CATCHES RESTRAINT.

That sentence was written on 2026-08-19 as a limitation. This is the attempt to stop it being
one. It is the class with the only DEMONSTRATED corpus-wide cost: the arm-role classifier read
registry arm types literally and silently SHRANK evidence bases -- ten trials on `sglt2-hf`
alone, two on `iv-iron-hf`, and it would have shrunk every topic built with that instrument.

WHY RESTRAINT IS STRUCTURALLY HARD TO CATCH, stated plainly rather than glossed: a guard fires
on something present and wrong. Withheld evidence is ABSENT. It leaves no trace in the object,
so there is nothing for a single-instrument check to read. This is why the class survived every
guard we had.

THE WAY IN IS THE ONE THAT ACTUALLY WORKED. The arm-type defect was not found by a person
noticing. It was found because TWO INDEPENDENT INSTRUMENTS DISAGREED: the executed search
surfaced an object's OWN INCLUDED TRIALS, and the arm-role classifier then refused to recognise
two of them as the intervention. Neither found it alone. That pattern generalises:

    A REFUSAL BY ONE INSTRUMENT WHERE AN INDEPENDENT ONE RETURNS A DEFINITE ANSWER IS A
    CANDIDATE FOR REVIEW, NOT A SAFE DEFAULT.

NOT_ASSESSABLE is the correct third state and this file does not argue otherwise. What it
argues is that a refusal is only safe when nothing else can decide. Where something else HAS
decided, the refusal is a disagreement, and a disagreement that nobody looks at is
indistinguishable from a silent loss.

TWO LANES, both comparing instruments that do not share an input path:

  LANE 1  INCLUSION vs ARM-ROLE. The object asserts a trial contributes a randomised contrast
          (a definite answer, reached by a human screening decision recorded on the object).
          ssot/topic_identity.locate() independently classifies the same registration from the
          raw registry payload. locate() returning anything but `experimental` for a trial the
          object INCLUDES is the AFFIRM-AHF/HEART-FID signature exactly.

  LANE 2  PRECONDITION REFUSAL vs OBJECT CONTENT. A precondition returning NOT_ASSESSABLE for
          "field absent" where the field is in fact present and non-empty. That is not the
          third state, it is a read failure wearing the third state's clothes -- which is how
          P7 came to be hardcoded to REFUSING while the object held 11 resolved checks.

WHAT LANE 1 DOES NOT COVER, AND IT IS HALF THE ORIGINAL DEFECT. Lane 1 iterates a topic's
INCLUDED trials. It reproduces the `iv-iron-hf` shape exactly -- verified, see below -- but it
would NOT have caught the `sglt2-hf` ten. Those trials were withheld at the SURFACED stage:
the classifier called them comparators, so they never reached the included set, and a check
that reads the included set cannot see a trial that was kept out of it.

    THE LARGER HALF OF A WITHHOLDING DEFECT IS INVISIBLE TO A CHECK THAT READS THE OBJECT,
    BECAUSE WITHHOLDING IS PRECISELY WHAT KEEPS THINGS OUT OF THE OBJECT.

Closing it needs the executed search payload per topic as instrument A -- surfaced set versus
classifier verdict -- and that payload is currently stored for one topic. Named here rather
than implied by a passing run: this detector covers the shape it was tested on and one lane of
a two-lane problem.

A RATCHET, NOT A ZERO-GATE, AND THE REASON IS STATED RATHER THAN ASSUMED. Restraint findings
are CANDIDATES FOR REVIEW by construction -- some disagreements will be the classifier being
right and the inclusion being wrong, which is a finding in the other direction and equally worth
having. Blocking on a nonzero count would force every one of them to be adjudicated before any
unrelated commit. So the baseline is recorded and the gate blocks on an INCREASE. A new
disagreement is always worth a look; the standing set is worth a session, not a commit.
"""
import io
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SSOT = os.path.join(REPO, "ssot")
sys.path.insert(0, SSOT)

BASELINE_PATH = os.path.join(REPO, "scripts", ".restraint-baseline.json")
CACHE = os.environ.get(
    "RM_CTGOV_CACHE",
    "F:/claude-temp/claude/F--rapidmeta-ssot-shell/"
    "eb4d84e5-8a24-4c3b-afe2-34bd91c20bc7/scratchpad/.ctgov-raw-cache")

# Topic key -> the synonym-set key ssot/topic_identity uses. Declared, never guessed: an
# unmapped topic is REPORTED AS UNCHECKED rather than silently skipped, because a topic that
# falls out of the loop is exactly the silent loss this file exists to detect.
TOPIC_SYNONYM_KEY = {
    "iv-iron-hf": "intravenous iron",
    "sglt2-hf": "sglt2 inhibitors",
}


def raw_record(nct):
    """The raw v2 payload for one registration, from the local cache. None if not cached."""
    if not os.path.isdir(CACHE):
        return None
    for fn in os.listdir(CACHE):
        if fn.startswith(nct + "_") and fn.endswith(".json"):
            try:
                with io.open(os.path.join(CACHE, fn), encoding="utf-8") as fh:
                    return json.load(fh)
            except (ValueError, OSError):
                return None
    return None


def lane1_inclusion_vs_armrole():
    """The object INCLUDES a trial; the classifier declines to call it the intervention."""
    from topic_identity import locate, synonyms_for
    findings, unchecked = [], []
    for topic in sorted(os.listdir(SSOT)):
        p = os.path.join(SSOT, topic, topic + ".json")
        if not os.path.exists(p):
            continue
        key = TOPIC_SYNONYM_KEY.get(topic)
        if not key:
            unchecked.append((topic, "no declared synonym key"))
            continue
        try:
            with io.open(p, encoding="utf-8") as fh:
                obj = json.load(fh)
            syns = synonyms_for(key)
        except (ValueError, OSError, KeyError) as e:
            unchecked.append((topic, "unreadable: %s" % e))
            continue
        for t in ((obj.get("inputs") or {}).get("trials") or []):
            nct = t.get("nct")
            if not nct:
                continue
            rec = raw_record(nct)
            if rec is None:
                unchecked.append((topic, "%s not cached" % nct))
                continue
            role, ev = locate(rec, syns)
            if role != "experimental":
                findings.append({
                    "lane": 1, "topic": topic, "nct": nct, "verdict_b": role,
                    "why": ("the object INCLUDES this trial as a contributing randomised "
                            "contrast; locate() independently returns %r" % role),
                    "evidence_b": (ev or "")[:120]})
    return findings, unchecked


# Lane 2: precondition refusals that cite absence, paired with the object path that would
# settle them. DECLARED, because a refusal reason is prose and guessing which field it means is
# the substring-is-not-identity defect all over again.
REFUSAL_CITES_ABSENCE = {
    "criteria_stated": ["screening.eligibility"],
    "criteria_predefined": ["screening.eligibility_provenance"],
    "population_stated": ["question"],
    "estimand_named": ["outcomes"],
}


def _dig(obj, path):
    node = obj
    for part in path.split("."):
        node = node.get(part) if isinstance(node, dict) else None
        if node is None:
            return None
    return node


def lane2_refusal_vs_content():
    """A precondition says 'cannot assess: absent' while the field is present and non-empty."""
    findings = []
    for topic in sorted(os.listdir(SSOT)):
        p = os.path.join(SSOT, topic, topic + ".json")
        if not os.path.exists(p):
            continue
        try:
            with io.open(p, encoding="utf-8") as fh:
                obj = json.load(fh)
        except (ValueError, OSError):
            continue
        pv = obj.get("precondition_verdict") or {}
        for name, paths in REFUSAL_CITES_ABSENCE.items():
            entry = pv.get(name)
            if not isinstance(entry, dict):
                continue
            verdict = str(entry.get("verdict") or "")
            reason = str(entry.get("reason") or "")
            if "NOT_ASSESSABLE" not in verdict.upper().replace("-", "_"):
                continue
            if not any(w in reason.lower() for w in
                       ("absent", "neither", "no ", "not present", "cannot assess")):
                continue
            for path in paths:
                val = _dig(obj, path)
                if val:
                    findings.append({
                        "lane": 2, "topic": topic, "precondition": name,
                        "verdict_b": "NOT_ASSESSABLE",
                        "why": ("refusal cites absence, but %s is PRESENT and non-empty "
                                "(%s)" % (path, type(val).__name__)),
                        "evidence_b": reason[:120]})
    return findings


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    f1, unchecked = lane1_inclusion_vs_armrole()
    f2 = lane2_refusal_vs_content()
    findings = f1 + f2

    for f in findings:
        who = f.get("nct") or f.get("precondition")
        print("LANE %d  %s  %s" % (f["lane"], f["topic"], who))
        print("        %s" % f["why"])
        if f.get("evidence_b"):
            print("        instrument B: %s" % f["evidence_b"])
    if unchecked:
        print()
        print("UNCHECKED (reported, never silently skipped -- a topic that falls out of the")
        print("loop is the silent loss this file exists to detect):")
        for topic, why in unchecked[:12]:
            print("   %-24s %s" % (topic, why))
        if len(unchecked) > 12:
            print("   ... and %d more" % (len(unchecked) - 12))

    base = 0
    if os.path.exists(BASELINE_PATH):
        try:
            with io.open(BASELINE_PATH, encoding="utf-8") as fh:
                base = json.load(fh).get("count", 0)
        except (ValueError, OSError):
            base = 0
    print()
    print("lane 1 (inclusion vs arm-role)     %d" % len(f1))
    print("lane 2 (refusal vs content)        %d" % len(f2))
    print("restraint candidates               %d   (baseline %d)" % (len(findings), base))
    print("unchecked                          %d" % len(unchecked))
    if len(findings) > base:
        print()
        print("REFUSED: %d restraint candidate(s), above the baseline of %d."
              % (len(findings), base))
        print("Each is a DISAGREEMENT between two independent instruments, not a proven defect.")
        print("Adjudicate it: either the classifier is withholding, or the inclusion is wrong.")
        print("Both are findings. Neither is a safe default.")
        return 1
    print()
    print("no NEW restraint candidates: no instrument refuses where an independent one decides.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
