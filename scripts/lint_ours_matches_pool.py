#!/usr/bin/env python3
"""A FIELD THAT SAYS "OURS" MUST HOLD OUR NUMBER.

THE INSTANCE, AND WHY THE EXISTING DETECTOR COULD NOT SEE IT.

`alirocumab-lipid` was restated from k=6 to k=8 when two eligible, poolable trials were
recovered by screening. The headline moved to MD -54.82 (-60.23 to -49.42). Its
published-comparison block did not:

    published_comparison.divergence_decomposed.ours
        "Mean difference -54.66 percent (-60.75 to -48.56) ... at week 24, k=6, random
         effects, DerSimonian-Laird. PREDICTION INTERVAL -74.1 to -35.2, which is the number
         to quote."

So a gated page states two different estimates for its own review, and the superseded one is
the one sitting in the table a reader consults to compare us against the literature -- P7,
which must agree between the page and the Word manuscript.

`scripts/lint_block_contradicts_object.py` is silent on it BY CONSTRUCTION. It scopes
`published_comparison` out entirely as a FOREIGN_SUBJECT, because that block describes OTHER
people's reviews and reading "reports no pooled estimate of its own" as a claim about this
object was one of its two false-alarm families. That exclusion was right about the block and
wrong about one field inside it:

    A BLOCK EXCLUDED BECAUSE IT DESCRIBES OTHER WORK IS EXACTLY WHERE A FIELD NAMED `ours`
    HIDES. The scope-out is at block level; the first person is at field level.

This is not the removed prose check returning. That one asked what an arbitrary sentence
meant, could not tell a THRESHOLD ("below k=10") from a CLAIM, and accused 43 correct objects.
Here the subject is given by the KEY -- `ours`, `our_estimate`, `this_review` -- so no sentence
is interpreted to decide who it is about. Only the numbers are read.

WHAT IS CHECKED, and every failing limb is reported rather than the first:

  1  POINT   a first-person field quotes no number that round-matches this object's own pooled
             point AT THE PRECISION THE FIELD ITSELF QUOTES. `-54.8` matches a stored -54.82;
             `-54.66` does not. Precision comes from the text, so rounding is never an excuse
             and never a false alarm.
  2  K       a first-person field says `k=N` where N is not the k of any pooled outcome.
  3  OUR-N   `our <decimal>` in running prose must round-match a pooled point the same way.

TWO FALSE ALARMS WERE FIXED RATHER THAN BASELINED, AND THEY NAME THE LIMIT OF LIMB 1.
`incretin-hfpef-review` carries
`...published_synthesis_comparison.trial_set_overlap.ours = ["NCT04847557 SUMMIT
(tirzepatide)", ...]` -- a first-person field whose content is an ID LIST, not an estimate.
The first version read `04847557` as a quoted number and accused a correct object.

    A FIELD CAN BE FIRST-PERSON AND NOT BE A NUMERIC CLAIM.

So limb 1 is assessable only where the field quotes at least one DECIMAL number, and registry
identifiers are stripped before any number is read. The conservative direction is stated
rather than hidden: an `ours` field whose estimate is a whole number is NOT_ASSESSABLE here
and this check will not catch it.

LIMB 3 WAS PROMOTED FROM ADVISORY AFTER EVERY HIT WAS READ. It raised 3 occurrences, all on
`alirocumab-lipid`, and all 3 are the SAME stale k=6 estimate reached by a different route
(`our -54.66` twice, `our -54.7` once -- the latter being -54.66 rounded, so it was correct
when written and is stale now). 3 inspected, 3 true, 0 baselined. Had any been correct text
the limb would have stayed advisory: an uninspected alarm may not be assumed false.

ABSENT IS NOT FAIL. An object with no pooled point is NOT_ASSESSABLE here: there is nothing
for a first-person field to disagree with, and refusing on that would be inventing a defect
out of an absence.
"""
import io
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SSOT = os.path.join(REPO, "ssot")

FAIL, NA, OK = "FAIL", "NOT_ASSESSABLE", "OK"

# The subject is decided by the KEY, never by parsing the sentence.
FIRST_PERSON_KEY = re.compile(r"^(ours|our|our_[a-z0-9_]+|this_review|ours_[a-z0-9_]+)$", re.I)

NUM = re.compile(r"-?\d+\.\d+|-?\d+")
K_CLAIM = re.compile(r"\bk\s*=\s*(\d+)")
OUR_NUM = re.compile(r"\bour\s+(-?\d+\.\d+)")
DECIMAL = re.compile(r"-?\d+\.\d+")
# Registry identifiers are not quantities. NCT04847557 read as a number is how limb 1
# accused a correct object; stripped here rather than filtered by magnitude, because a
# magnitude threshold is a guess and a prefix is a fact about the identifier scheme.
IDENTIFIER = re.compile(r"\b(?:NCT|PMID|PMC|DOI|ISRCTN|EudraCT|NTR|ChiCTR)[:\s]*[\w./-]+",
                        re.I)


def walk(node, path=""):
    if isinstance(node, dict):
        for k, v in node.items():
            for r in walk(v, path + "." + k):
                yield r
    elif isinstance(node, list):
        for i, v in enumerate(node):
            for r in walk(v, "%s[%d]" % (path, i)):
                yield r
    elif isinstance(node, str):
        yield path, node


def quoted_numbers(text):
    """(value, decimals) for every number in the text, decimals as WRITTEN.

    Identifiers are removed FIRST. `NCT04847557` is not the number 4,847,557.
    """
    text = IDENTIFIER.sub(" ", text)
    out = []
    for tok in NUM.findall(text):
        try:
            v = float(tok)
        except ValueError:
            continue
        d = len(tok.split(".")[1]) if "." in tok else 0
        out.append((v, d))
    return out


def pooled_points(obj):
    """[(outcome, point, k)] for outcomes that really pooled a value."""
    out = []
    for name, blk in (((obj.get("results") or {}).get("by_outcome")) or {}).items():
        if not isinstance(blk, dict):
            continue
        pooled = blk.get("pooled") or {}
        pt = pooled.get("point")
        if pt is None or pooled.get("withdrawn"):
            continue
        out.append((name, float(pt), blk.get("k")))
    return out


def check(obj):
    pts = pooled_points(obj)
    rows, advisory = [], []

    for path, text in walk(obj):
        key = path.rsplit(".", 1)[-1]
        key = re.sub(r"\[\d+\]$", "", key)

        # LIMB 3 -- `our <decimal>` in running prose, anywhere in the object.
        for m in OUR_NUM.finditer(text):
            v = float(m.group(1))
            d = len(m.group(1).split(".")[1])
            if not pts:
                advisory.append((path, m.group(0), NA))
            elif any(round(pt, d) == v for _n, pt, _k in pts):
                advisory.append((path, m.group(0), OK))
            else:
                rows.append((path, FAIL,
                             "prose says '%s'; this object's pooled point(s) are %s"
                             % (m.group(0),
                                ", ".join("%g" % p for _n, p, _ in pts)),
                             " ".join(text.split())[:170]))

        if not FIRST_PERSON_KEY.match(key):
            continue
        if not pts:
            rows.append((path, NA, "no pooled point exists in this object to compare against",
                         text[:120]))
            continue
        # A FIELD CAN BE FIRST-PERSON AND NOT BE A NUMERIC CLAIM -- an id list, a trial name,
        # a scope sentence. Limb 1 is assessable only where a DECIMAL is quoted.
        if not DECIMAL.search(IDENTIFIER.sub(" ", text)):
            rows.append((path, NA,
                         "first-person field quotes no decimal number, so there is no "
                         "estimate here to disagree with the pool",
                         " ".join(text.split())[:120]))
            continue

        # 1 -- POINT, at the precision the field itself quotes.
        quoted = quoted_numbers(text)
        matched = None
        for name, pt, _k in pts:
            for v, d in quoted:
                if round(pt, d) == v:
                    matched = (name, pt, v, d)
                    break
            if matched:
                break
        if matched is None:
            rows.append((path, FAIL,
                         "quotes no number matching this object's own pooled point(s) %s at "
                         "the precision it writes them"
                         % ", ".join("%s=%g" % (n, p) for n, p, _ in pts),
                         " ".join(text.split())[:170]))

        # 2 -- K. Reported even when limb 1 already failed: a check that returns on the first
        #      failing limb makes the reason a fact about the order the limbs were written in.
        ks = {k for _n, _p, k in pts if isinstance(k, int)}
        for m in K_CLAIM.finditer(text):
            claimed = int(m.group(1))
            if ks and claimed not in ks:
                rows.append((path, FAIL,
                             "says k=%d; this object's pooled outcome(s) declare k in %s"
                             % (claimed, sorted(ks)),
                             " ".join(text.split())[:170]))
    return rows, advisory


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    only = sys.argv[1] if len(sys.argv) > 1 else None
    scanned = 0
    failing = {}
    advisories = []
    na = 0
    for d in sorted(os.listdir(SSOT)):
        if only and d != only:
            continue
        p = os.path.join(SSOT, d, d + ".json")
        if not os.path.exists(p):
            continue
        try:
            with io.open(p, encoding="utf-8") as fh:
                obj = json.load(fh)
        except (ValueError, OSError) as exc:
            print("%s  UNREADABLE: %s -- NOT_ASSESSABLE, not a failure" % (d, exc))
            continue
        scanned += 1
        rows, adv = check(obj)
        advisories += [(d, a, b, c) for a, b, c in adv]
        bad = [r for r in rows if r[1] == FAIL]
        na += sum(1 for r in rows if r[1] == NA)
        if bad:
            failing[d] = bad
            print(d)
            for path, verdict, why, excerpt in bad:
                print("   %s" % path)
                print("      %s" % why)
                print("      ...%s..." % excerpt)
            print()

    print("topic objects scanned                         %d" % scanned)
    print("first-person fields with nothing to check     %d   <- NOT_ASSESSABLE" % na)
    print("objects whose first-person field disagrees    %d" % len(failing))
    print()
    print("`our <number>` in prose that AGREES with the pool: %d occurrence(s)"
          % sum(1 for _d, _p, _f, v in advisories if v == OK))
    for d, path, frag, verdict in advisories:
        print("   %-24s %-52s %-14s %s" % (d, path[:52], frag, verdict))
    if failing:
        print()
        print("REFUSED: a field named for this review states a number this review does not hold.")
        return 1
    print()
    print("every first-person field agrees with this object's own pool.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
