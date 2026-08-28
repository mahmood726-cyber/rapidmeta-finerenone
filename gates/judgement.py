"""Stamp a stored judgement with a reference to what it judged — at the moment of writing.

MAHMOOD'S RULING, 2026-08-28: *"Nothing writes `subject_ref`. That is `absence.py` again: the
gate exists, the field exists, and NOTHING POPULATES IT."* Caught that shape in the morning,
fixed it, and reproduced it in my own delivery within hours.

THE SEMANTICS ARE THE WHOLE DESIGN, AND THE OBVIOUS IMPLEMENTATION IS WRONG.

Stamping every judgement on every write — "keep the ref up to date" — makes the reference
track its subject, so a judgement is permanently CURRENT and the check can never fire. That is
a field that looks like provenance and carries none. **The staleness we want to detect is
exactly the case where the subject moved and the judgement did not.**

So:

    no ref yet                          -> STAMP.  A first judgement, about today's subject.
    ref present, judgement UNCHANGED    -> LEAVE.  If the subject drifts, the ref no longer
                                                   matches it, and that is the finding.
    ref present, judgement CHANGED      -> RESTAMP. Somebody judged again; the new judgement
                                                    is about the current subject.

`judgement_digest` is what distinguishes the second case from the third: a hash of the
judgement VALUES only, so a change to the evidence never looks like a re-judgement.

WHAT COUNTS AS THE SUBJECT. Every sibling field of the judgement that is not itself a
judgement, a reference, or bookkeeping. For a RoB domain block that is the signalling answers,
the quotes and the reasoning — the things the verdict is *about*. Defined by exclusion because
the corpus stores subjects under many names and an inclusion list would silently miss one,
which is the defect class this whole batch exists for.

THE INVARIANT. `stamp_object` adds keys and never removes or alters one. `assert_only_added`
proves that on every call, because this runs inside the atomic writer that 45 modules and
every topic object pass through, and a bug here corrupts the corpus rather than reporting it.
"""
from __future__ import annotations

import hashlib
import json

JUDGE_KEYS = ("verdict", "judgement", "rating", "certainty", "risk_of_bias_verdict",
              "grade", "assessment", "conformance")

# not part of the subject: the judgement itself, our own refs, and bookkeeping that changes
# for reasons unrelated to what was judged
NOT_SUBJECT = set(JUDGE_KEYS) | {
    "subject_ref", "judgement_ref", "stamped_utc",
    "checked_utc", "assessed_utc", "verified_utc", "read_utc", "recorded_utc",
    "checked_on", "verified_on", "assessed_on",
}


def _canon(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def subject_ref(fields):
    """A stable sha256 over the exact values judged."""
    return "sha256:" + hashlib.sha256(_canon(fields).encode("utf-8")).hexdigest()


def judgement_digest(block):
    """A hash of the JUDGEMENT VALUES only — so evidence drift is not read as a re-judgement."""
    vals = {k: block[k] for k in JUDGE_KEYS if k in block}
    return "sha256:" + hashlib.sha256(_canon(vals).encode("utf-8")).hexdigest()


def is_judgement(block):
    return isinstance(block, dict) and any(
        isinstance(block.get(k), str) and block[k].strip() for k in JUDGE_KEYS)


def subject_of(block):
    """The fields the judgement is ABOUT. Scalars and containers alike, minus bookkeeping."""
    return {k: v for k, v in block.items() if k not in NOT_SUBJECT}


def stamp(block):
    """Stamp one judgement block in place. Returns 'stamped' | 'restamped' | 'left'."""
    if not is_judgement(block):
        return "left"
    digest = judgement_digest(block)
    if "subject_ref" not in block:
        block["subject_ref"] = subject_ref(subject_of(block))
        block["judgement_ref"] = digest
        return "stamped"
    if block.get("judgement_ref") != digest:
        # a NEW judgement was made; it is about the subject as it stands now
        block["subject_ref"] = subject_ref(subject_of(block))
        block["judgement_ref"] = digest
        return "restamped"
    # unchanged judgement: leave the ref pointing at what it was made against, so that a
    # subject that has since moved reads as STALE. This branch is the point of the module.
    return "left"


def stamp_object(obj):
    """Walk and stamp. Returns a count per outcome. Mutates in place."""
    counts = {"stamped": 0, "restamped": 0, "left": 0}

    def rec(x):
        if isinstance(x, dict):
            counts[stamp(x)] += 1 if is_judgement(x) else 0
            for v in x.values():
                rec(v)
        elif isinstance(x, list):
            for v in x:
                rec(v)

    rec(obj)
    return counts


def recheck(block):
    """CURRENT | STALE | NOT-CHECKABLE for one stored judgement."""
    if not is_judgement(block):
        return "NOT-A-JUDGEMENT"
    stored = block.get("subject_ref")
    if not stored:
        return "NOT-CHECKABLE"
    return "CURRENT" if stored == subject_ref(subject_of(block)) else "STALE"


REF_KEYS = ("subject_ref", "judgement_ref")


def assert_only_added(before, after, path="$"):
    """Prove the stamp added keys and touched nothing but its own two ref fields.

    Runs inside the atomic writer, on every object write, because a bug here corrupts the
    corpus rather than reporting on it. Raises with the exact path on any alteration.

    THE FIRST VERSION FORBADE ALL VALUE CHANGES AND WAS WRONG -- it refused a legitimate
    RE-STAMP, which is precisely the branch that runs when somebody makes a new judgement.
    Caught by exercising step 4 of the probe rather than by reading the code. The invariant
    is not "nothing changes"; it is "nothing but OUR OWN two fields changes", and stating it
    loosely would have let the stamp rewrite evidence unnoticed.
    """
    if isinstance(before, dict):
        if not isinstance(after, dict):
            raise ValueError("stamping changed the TYPE at %s" % path)
        for k, v in before.items():
            if k not in after:
                raise ValueError("stamping REMOVED %s.%s" % (path, k))
            if k in REF_KEYS:
                continue                      # ours to update; see the docstring above
            assert_only_added(v, after[k], path + "." + str(k))
        extra = set(after) - set(before)
        if extra - set(REF_KEYS):
            raise ValueError("stamping added unexpected keys at %s: %s"
                             % (path, sorted(extra - set(REF_KEYS))))
    elif isinstance(before, list):
        if not isinstance(after, list) or len(before) != len(after):
            raise ValueError("stamping changed a list at %s" % path)
        for i, (b, a) in enumerate(zip(before, after)):
            assert_only_added(b, a, "%s[%d]" % (path, i))
    elif before != after:
        raise ValueError("stamping ALTERED a value at %s" % path)
