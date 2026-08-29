#!/usr/bin/env python3
"""A THIRD DIRECTION: pages that OVERSTATE THEIR OWN WEAKNESS. LAYER: served bytes, checked against the store.

WE SWEEP FOR PAGES CLAIMING TOO MUCH. We now sweep for pages DENYING WHAT THEY HOLD. This is
neither: it is a page accusing itself of a defect it does not have.

    gepotidacin states "This pool collapses that split, so its single ratio is an average over
    two populations the published analysis keeps apart" -- while the SAME OBJECT records that
    "this object's registered outcome text names no analysis population" and that it pools
    "over an UNSTATED population". You cannot know you collapsed a split you cannot locate.
    The confident self-accusation is not supported by the object it describes.

WHY NOTHING WE OWN CATCHES IT: self-criticism is never challenged. A reviewer reading "this
pool collapses the split" takes it as candour and moves on, so the sentence survives every
pass -- while making our own evidence look worse than it is, in front of a reader.

CHECK THE ASSERTION AGAINST THE OBJECT, NOT AGAINST ANOTHER STORED JUDGEMENT. A stored reason
is itself a claim; 130 of 242 checkable self-descriptions in this corpus are stale. So where a
claim is mechanically checkable it is checked against structure -- does the field exist, does
the object hold the thing it says it lacks -- and where it is not, it is NOT_ASSESSABLE and
said to be.

THREE STATES, NEVER TWO: TRUE_SELF_CRITICISM, FALSE_SELF_CRITICISM, NOT_ASSESSABLE.

CONTROLS ARE MANDATORY AND BOTH LEGS RUN ON EVERY INVOCATION, because three filters hid a
known case from its own output tonight and nothing in the output said so:
  POSITIVE, and NON-VACUOUS -- the instrument must SEE the gepotidacin sentence and classify it
    FALSE_SELF_CRITICISM. Merely "finding a row for gepotidacin" does not pass.
  NEGATIVE -- a self-criticism whose assertion the object SUPPORTS must come back TRUE, so the
    instrument cannot be one that calls everything false.
"""
import io
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
TAG = re.compile(r"<[^>]+>")
WS = re.compile(r"\s+")
SCRIPT = re.compile(r"(?is)<(script|style)\b.*?</\1>")

# Self-critical claims that assert something CHECKABLE. Vague self-deprecation is excluded on
# purpose: "this review is limited" asserts nothing a structure can contradict.
CLAIMS = [
    ("collapses_a_split", re.compile(r"(?i)\b(collapses?|collapsed|conflates?|mixes|merges)\b"
                                     r"[^.]{0,120}\b(split|strata|stratum|populations?|groups?)\b")),
    ("cannot_distinguish", re.compile(r"(?i)\b(cannot be distinguished|is not separated|"
                                      r"are not separable|indistinguishable)\b")),
    ("holds_nothing", re.compile(r"(?i)\b(no [a-z ]{3,30} (?:exists|is held|is recorded)|"
                                 r"records no [a-z ]{3,30}|holds no [a-z ]{3,30})\b")),
    ("was_not_applied", re.compile(r"(?i)\b(was not (?:applied|executed|run|performed)|"
                                   r"not executed|never executed)\b")),
]


def say(s=""):
    OUT.write(s + "\n")
    OUT.flush()


def rendered(html):
    return WS.sub(" ", TAG.sub(" ", SCRIPT.sub(" ", html))).strip()


def walk(o, p=""):
    if isinstance(o, dict):
        for k, v in o.items():
            yield from walk(v, p + "/" + str(k))
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from walk(v, p + "/%d" % i)
    else:
        yield p, o


UNSTATED = re.compile(r"(?i)\b(unstated|names no analysis population|no analysis population|"
                      r"not recorded|does not record|unknown population)\b")


def adjudicate(kind, sentence, obj):
    """Check the assertion against the OBJECT's structure. Returns (state, why)."""
    leaves = list(walk(obj))
    text_leaves = [(k, v) for k, v in leaves if isinstance(v, str)]

    if kind == "collapses_a_split":
        # To COLLAPSE two populations, the object must know which population its own inputs
        # belong to. If it records that population as unstated, the confident accusation
        # asserts more than the object can support.
        unstated = [k for k, v in text_leaves
                    if UNSTATED.search(v) and re.search(r"(?i)population", v)]
        if unstated:
            return ("FALSE_SELF_CRITICISM",
                    "the object records its own analysis population as UNSTATED at %s, so it "
                    "cannot establish that its pool merges two populations it cannot locate"
                    % unstated[0])
        # if the object holds per-stratum rows, a pool over them really would collapse them
        strata = [k for k, v in text_leaves
                  if re.search(r"(?i)stratum|susceptib|subgroup", str(v)) and "/per_trial/" in k]
        if strata:
            return ("TRUE_SELF_CRITICISM",
                    "the object holds per-stratum rows at %s, so a single pool over them does "
                    "merge them" % strata[0])
        return ("NOT_ASSESSABLE",
                "the object records neither an analysis population nor per-stratum rows, so "
                "the claim cannot be checked against structure")

    if kind == "holds_nothing":
        # WITHDRAWN AS A VERDICT, KEPT AS AN ENUMERATION. Hand-read 2026-08-28: of 13
        # FALSE_SELF_CRITICISM verdicts this sweep produced, 12 were this check and ONE was
        # real. Precision 1/13. Word-in-path matching cannot decide whether an object holds
        # "the thing the sentence names":
        #   'background'  matched /citation_policy/ratio/background, topic_is_background and
        #                 background_incidence -- none is the review's Background section
        #   'poolable'    matched a field holding the value FALSE, which is structurally
        #                 present and semantically the opposite of what was claimed
        #   'adjudication' matched NEEDS_ADJUDICATION and bearing_on_the_pending_adjudication,
        #                 which AGREE with "no adjudication is recorded" -- the check counted
        #                 its own confirming evidence as a contradiction
        # A presence test cannot answer a question about MEANING, and reporting its output as
        # a defect count would have published 12 false accusations of false accusation.
        # The claims are still enumerated so the population is known; only the verdict is
        # withheld, and the reason travels with it.
        return ("NOT_ASSESSABLE",
                "this claim kind needs a semantic read: a presence test on field names cannot "
                "decide whether the object holds the thing the sentence names")

    return ("NOT_ASSESSABLE",
            "no structural check is defined for this claim kind; it needs a human read")


def collect():
    pm = json.load(io.open(os.path.join(ROOT, "ssot", "PAGE_MAP.json"), encoding="utf-8"))
    rows = []
    pages_read = 0
    pages_missing = 0
    for page, obj_rel in sorted(pm.items()):
        fp = os.path.join(ROOT, page)
        op = os.path.join(ROOT, obj_rel)
        if os.path.exists(fp) and os.path.exists(op):
            pages_read += 1
        else:
            pages_missing += 1
            continue
        text = rendered(io.open(fp, encoding="utf-8", errors="replace").read())
        try:
            obj = json.load(io.open(op, encoding="utf-8"))
        except Exception:
            continue
        for kind, pat in CLAIMS:
            for m in pat.finditer(text):
                # A18 -- "a page DENIES a protocol that exists in the repository" -- is another
                # lane's class and already has a three-state generator fix landed for it.
                # Re-finding it here badly would double-count it and contradict better work.
                _ctx = text[max(0, m.start() - 80):m.end() + 80].lower()
                if "protocol registration" in _ctx or "prospero" in _ctx:
                    continue
                lo = text.rfind(".", 0, m.start()) + 1
                hi = text.find(".", m.end())
                sentence = text[lo:hi if hi > 0 else m.end() + 200].strip()
                state, why = adjudicate(kind, sentence, obj)
                rows.append(dict(page=page, topic=os.path.basename(os.path.dirname(obj_rel)),
                                 kind=kind, sentence=sentence[:400], state=state, why=why))
                break   # one instance per kind per page
    return rows, pages_read, pages_missing


def controls(rows):
    """Both legs, every run. A control that only checks the positive can still be an instrument
    that calls everything false, and one that only checks the negative can be one that calls
    everything true."""
    ok = True
    gep = [r for r in rows if r["topic"].startswith("gepotidacin")
           and r["kind"] == "collapses_a_split"]
    seen = bool(gep)
    classified = bool(gep) and gep[0]["state"] == "FALSE_SELF_CRITICISM"
    say("CONTROL -- POSITIVE, and non-vacuous")
    say("  gepotidacin 'collapses that split' SEEN by the sweep      : %s" % seen)
    say("  ...and classified FALSE_SELF_CRITICISM                     : %s" % classified)
    if seen:
        say("     sentence: %s" % gep[0]["sentence"][:150])
        say("     because : %s" % gep[0]["why"][:150])
    ok &= seen and classified

    # THE NEGATIVE CONTROL MUST BE SYNTHETIC HERE, and saying why is part of the control.
    # The corpus contains exactly ONE `collapses_a_split` claim and it is false, so no real row
    # can prove the instrument is capable of returning TRUE. A control drawn from data that
    # contains no negative is not a control. This one is CONSTRUCTED: an object that genuinely
    # holds per-stratum rows, where the same sentence SHOULD be upheld. It is synthetic on
    # purpose -- a control anchored to a live object stops being a control the moment that
    # object is fixed.
    fixture = {"results": {"by_outcome": {"primary": {"per_trial": [
        {"trial": "SYNTH-1", "note": "nitrofurantoin-susceptible stratum"},
        {"trial": "SYNTH-2", "note": "not-susceptible stratum"}]}}}}
    st, why = adjudicate("collapses_a_split",
                         "This pool collapses that split across two populations", fixture)
    say("CONTROL -- NEGATIVE (synthetic, because the corpus holds no true case)")
    say("  a constructed object that DOES hold per-stratum rows returns : %s" % st)
    say("     %s" % why[:150])
    neg_ok = (st == "TRUE_SELF_CRITICISM")
    say("  instrument can return TRUE, so it is not one that calls everything false: %s"
        % neg_ok)
    real_trues = [r for r in rows if r["state"] == "TRUE_SELF_CRITICISM"]
    say("  real corpus rows returning TRUE: %d  (0 is expected and is not a failure here --"
        % len(real_trues))
    say("     there is one such claim in the corpus and it is the false one)")
    ok &= neg_ok
    return ok


def main():
    rows, read, missing = collect()
    say("LAYER: served bytes for the claim, STORE STRUCTURE for the check.")
    say("pages read: %d   | pages skipped (page or object absent): %d" % (read, missing))
    say("")
    ok = controls(rows)
    say("")
    say("CONTROLS PASS: %s" % ok)
    if not ok:
        say("  -> the counts below are NOT reportable until both legs pass.")
    say("")
    counts = {}
    for r in rows:
        counts[r["state"]] = counts.get(r["state"], 0) + 1
    say("%-26s %s" % ("STATE", "n"))
    for k in ("FALSE_SELF_CRITICISM", "TRUE_SELF_CRITICISM", "NOT_ASSESSABLE"):
        say("%-26s %d   /%d" % (k, counts.get(k, 0), len(rows)))
    say("")
    for r in rows:
        if r["state"] == "FALSE_SELF_CRITICISM":
            say("  FALSE  %-34s %s" % (r["topic"][:34], r["sentence"][:110]))
            say("         %s" % r["why"][:140])
    with io.open(os.path.join(ROOT, "out", "false_self_accusation.json"), "w",
                 encoding="utf-8", newline="\n") as fh:
        json.dump({"layer": "served bytes + store structure", "pages_read": read,
                   "pages_skipped": missing, "controls_pass": ok,
                   "counts": counts, "rows": rows}, fh, indent=1, ensure_ascii=False)
    say("")
    say("wrote out/false_self_accusation.json")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
