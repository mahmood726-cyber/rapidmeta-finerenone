#!/usr/bin/env python3
""""READ" MUST NOT MEAN "RETRIEVED". Every record where read > appraised must say so.

THE INSTANCE THAT MADE THIS MECHANICAL. lefamulin-cabp-auto-full-review records

    denominator = {matched: 19, retrieved: 19, read: 19, appraised: 1}

Nineteen records were retrieved and one was appraised, and the field that says "read"
carries the retrieved number. It is the THIRD instance -- 46 and 39 on other topics -- so
it is a corpus-wide property of how these objects were built, not three mistakes.

WHY IT MATTERS HERE SPECIFICALLY, and this is not hypothetical. An external reader found a
genuinely missing trial, LEAP China. Re-running this topic's search exactly as the pipeline
sent it RETURNED the 2025 pooled analysis whose abstract names LEAP China. The search found
the answer. The process recorded "19 read" and appraised one, and the answer was discarded
at the retrieval-to-appraisal boundary.

    THE SEARCH DID NOT FAIL. THE READING DID.

A count of 19 "read" is what makes that invisible: it reads as diligence and it means
retrieval.

WHAT THIS CHECKS. For every topic carrying a published-comparison denominator, compare the
read count against the appraised count. If read exceeds appraised, the object must carry an
explicit statement of the gap. Absent that statement, the object is claiming to have read
what it only listed.

EXIT CODES
    0  every topic with read > appraised declares the gap
    1  at least one does not
    2  the check could not run over the population it claims to cover
"""
import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from instrument_controls import require_controls, ControlFailed  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SSOT = os.path.join(REPO, "ssot")

# The sentence an object must carry when read exceeds appraised. Matched loosely on
# substance, not on exact wording, so a rephrase does not silently pass.
DECLARATIONS = ("read_is_retrieved", "READ_MEANS_RETRIEVED", "not_appraised",
                "read_not_appraised", "RETRIEVED_NOT_READ",
                "READ_IS_NOT_APPRAISED", "retrieved_but_never_appraised")


def has_declaration(text):
    """Does this text declare the gap? Substring search, and SAID SO in the name.

    This used to be a membership test inside classify(), whose parameter therefore
    accepted a bare string. A gate refused that, correctly: `x in blob` on a string is a
    SUBSTRING test, and if a collection were ever passed instead the same expression would
    silently mean something else and return complete, plausible, wrong output. Splitting it
    out makes classify() take a boolean, so there is nothing left to confuse.
    """
    if not isinstance(text, str):
        raise TypeError("has_declaration expects the raw text, not a collection")
    return any(marker in text for marker in DECLARATIONS)


def classify(read, appraised, declared):
    """The whole decision, as ONE PURE FUNCTION so it can be controlled.

    `declared` is a BOOLEAN, decided by has_declaration(). Returns "FLAG" when a topic
    reports reading more than it appraised without saying so, "DECLARED" when the gap
    exists and is stated, "CLEAN" when there is no gap.
    """
    if not isinstance(read, int) or not isinstance(appraised, int):
        return "CLEAN"
    if read <= appraised:
        return "CLEAN"
    return "DECLARED" if declared else "FLAG"


def controls():
    """Both controls are SYNTHETIC, and deliberately so.

    No item in this corpus has read <= appraised, so there is no natural negative control.
    A control anchored to a live corpus item also RETIRES ITSELF the moment that item is
    fixed -- it then passes for the wrong reason. Synthetic cases cannot rot, and they are
    namespaced __control_ so they can never be mistaken for data or enter a denominator.

    The positive's expected answer is established OUTSIDE this code: an external reviewer
    reported that lefamulin-cabp records "19 records retrieved/read" and appraised ONE.
    Those literals are pinned here, so the control tests the instrument against someone
    else's finding rather than against its own logic.
    """
    pos = classify(19, 1, declared=False)
    neg_equal = classify(5, 5, declared=False)
    neg_declared = classify(9, 1, declared=True)
    require_controls(
        "lint_read_is_not_appraised",
        ("__control_gap_undeclared (19 read / 1 appraised, externally established)",
         pos, "FLAG"),
        ("__control_no_gap (5 read / 5 appraised) must not be flagged",
         neg_equal, "FLAG"))
    # A second negative, because over-flagging has two shapes here: no gap at all, and a
    # gap that IS declared. An instrument that flagged the declared case would punish the
    # very fix it demands.
    if neg_declared == "FLAG":
        raise ControlFailed(
            "REFUSED: the instrument flags a gap that IS declared, which would punish the "
            "fix it asks for. NO COUNT IS PRINTED.")


def denominator(obj):
    pc = obj.get("published_comparison")
    if isinstance(pc, dict) and isinstance(pc.get("denominator"), dict):
        return pc["denominator"]
    return None


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    if not os.path.isdir(SSOT):
        print("REFUSED (exit 2): %s is not a directory; the population cannot be "
              "enumerated." % SSOT)
        return 2

    # CONTROLS BEFORE ANY COUNT. If the instrument cannot reproduce a known answer, or
    # flags a case it must not, nothing it says about the corpus is worth printing.
    try:
        controls()
    except ControlFailed as e:
        print(str(e))
        return 2
    print()

    # EVERY EXCLUSION IS COUNTED AND NAMED, NEVER A BARE `continue`.
    # A gate refused an earlier version of this loop for exactly that: "a NEW negative
    # guard sits inside a corpus-wide loop". A guard that skips an item silently shrinks
    # the denominator, and the remaining number then reads as coverage when it is only
    # reach. So the loop states the POSITIVE property -- what it examined -- and every
    # item it could not examine is reported by reason.
    # STATED AS POSITIVE PROPERTIES, not as absences.
    # A gate refused the first version twice: `if not den: continue` and
    # `if not os.path.isfile(p): continue` are negative guards inside a corpus-wide loop,
    # and its instruction is to say what an item IS rather than what it lacks. That is not
    # style. `not den` is true for a missing key, an empty dict, and a dict of zeroes
    # alike, so the skip silently merges three different situations into one; naming the
    # positive condition forces each to be handled and counted.
    topics, with_den, gaps, declared, undeclared = 0, 0, [], [], []
    excluded = {"directory carries no object file": 0, "object unreadable": 0,
                "object carries no published-comparison denominator": 0,
                "denominator present but read/appraised are not integers": 0}
    for t in sorted(os.listdir(SSOT)):
        p = os.path.join(SSOT, t, t + ".json")
        if os.path.isfile(p):
            topics += 1
            obj = None
            try:
                with io.open(p, encoding="utf-8") as fh:
                    obj = json.load(fh)
            except (ValueError, OSError):
                excluded["object unreadable"] += 1
            if isinstance(obj, dict):
                den = denominator(obj)
                if isinstance(den, dict) and den:
                    with_den += 1
                    read = den.get("read")
                    appraised = den.get("appraised")
                    if isinstance(read, int) and isinstance(appraised, int):
                        blob = json.dumps(den) + json.dumps(
                            obj.get("published_comparison", {}))
                        rec = os.path.join(SSOT, t, "SEARCH-RECORD.json")
                        if os.path.isfile(rec):
                            try:
                                with io.open(rec, encoding="utf-8") as fh:
                                    blob += fh.read()
                            except OSError:
                                pass
                        verdict = classify(read, appraised, has_declaration(blob))
                        if verdict in ("FLAG", "DECLARED"):
                            gaps.append((t, read, appraised))
                            (declared.append(t) if verdict == "DECLARED"
                             else undeclared.append((t, read, appraised)))
                    else:
                        excluded["denominator present but read/appraised are not "
                                 "integers"] += 1
                else:
                    excluded["object carries no published-comparison denominator"] += 1
        else:
            excluded["directory carries no object file"] += 1

    print("EXAMINED, and what could not be:")
    print("  directories under ssot/                              %d"
          % (topics + excluded["directory carries no object file"]))
    print("  topics with an object                                %d" % topics)
    for reason, n in excluded.items():
        if n:
            print("     not examined -- %-38s %d" % (reason, n))
    print("  => this check reports on %d of %d topics (%.0f%%). The rest were NOT clean;"
          % (with_den, topics, 100.0 * with_den / max(topics, 1)))
    print("     they were NOT LOOKED AT, and that is a different statement.")
    print()
    print("topics with an object                                  %d" % topics)
    print("topics carrying a published-comparison denominator      %d" % with_den)
    print("of those, read exceeds appraised                        %d" % len(gaps))
    print("   ... and the gap IS declared on the object            %d" % len(declared))
    print("   ... and the gap is NOT declared                      %d" % len(undeclared))
    print()
    if gaps:
        print("THE GAP, BY TOPIC (read / appraised):")
        for t, r, a in sorted(gaps, key=lambda x: x[2] - x[1]):
            mark = "  <-- undeclared" if any(t == u[0] for u in undeclared) else ""
            print("   %-46s %4d read / %3d appraised%s" % (t[:46], r, a, mark))
        print()
    if undeclared:
        print("REFUSED: %d topic(s) report reading more records than they appraised and do "
              "not say so." % len(undeclared))
        print("FIX: add an explicit statement to published_comparison recording how many")
        print("     records were retrieved but never appraised. 'read' that means")
        print("     'retrieved' is the third instance of this class in this corpus, and it")
        print("     is how a genuinely missing trial (LEAP China) survived a search that")
        print("     had already returned the paper naming it.")
        return 1
    print("Every topic whose read count exceeds its appraised count declares the gap.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
