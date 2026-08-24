#!/usr/bin/env python3
"""MERGE the duplicate-screening, RoB 2 and GRADE records INTO each object. MERGE, NEVER WRITE.

A BUILDER THAT WRITES WHOLESALE REGRESSES EVERY ENRICHMENT SINCE THE LAST BUILD. This reads
each object, sets exactly four keys, and writes the whole structure back with every other key
untouched -- and it REFUSES to run if the reserialised object loses any top-level key it had
before, which is the cheapest possible test of that promise.

The four keys are the three claims the manuscript refused and could be made true, plus the one
that could not:

    screening.duplicate_screening   RECORDED where two independent families screened, OWED
                                    where they did not. Never described.
    risk_of_bias                    RoB 2, per RESULT, five domains, NO_INFORMATION where a
                                    domain cannot be reached from what we hold.
    grade                           per POOLED outcome only, with every rating-down step.
    protocol.prespecified           STAYS FALSE, PERMANENTLY, WITH ITS REASON.

WHY protocol.prespecified IS WRITTEN AS FALSE RATHER THAN LEFT ABSENT. Absent is ambiguous --
it reads as "nobody got round to it". FALSE with a reason is a statement:

    A PROTOCOL SPECIFIED BEFORE DATA COLLECTION IS A HISTORICAL FACT ABOUT THE PAST. Writing
    one now and calling it prespecified would be the single worst thing this project could
    ship -- it would make every other honest refusal in these pages worthless, because a reader
    who caught it would be right to disbelieve all of them. The criteria for these reviews were
    derived POST HOC, the derivation is traceable in `screening.eligibility_provenance`, and
    MECIR R107 permits post-hoc criteria PROVIDED THEY ARE DECLARED AS SUCH. They are declared.

The remedy is forward-looking and is recorded as such: a protocol registered BEFORE the search
for topics not yet built, so the claim becomes true GOING FORWARD rather than retroactively.
"""
import io
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EV = os.path.join(REPO, "evidence", "2026-08-19-batch1")

PRESPEC = {
    "prespecified": False,
    "permanently_refused": True,
    "why": ("A protocol specified before data collection is a HISTORICAL FACT ABOUT THE PAST "
            "and cannot be created retrospectively. Writing one now and calling it "
            "prespecified would invalidate every other refusal on these pages, because a "
            "reader who caught it would be right to disbelieve all of them."),
    "what_was_actually_done": ("Eligibility criteria were derived POST HOC from the trials and "
                               "the methodological authority, and the derivation is recorded "
                               "element by element in `screening.eligibility_provenance` with "
                               "the source of each."),
    "authority_permitting_it": ("MECIR R107 permits post-hoc eligibility criteria PROVIDED "
                                "THEY ARE DECLARED AS SUCH. They are declared, here and on the "
                                "page, and the page says 'derived, post hoc' in its heading."),
    "forward_remedy": ("For topics not yet built, a protocol is to be written and registered "
                       "BEFORE the search is executed, so that the claim becomes true GOING "
                       "FORWARD. It is never to be made true retroactively for a built topic."),
}


def key_paths(node, prefix=""):
    """EVERY key path in the object, not just the top level.

    THE GUARD THIS REPLACES COMPARED `set(obj.keys())` -- the TOP LEVEL ONLY -- while the
    merge below REPLACED `obj["risk_of_bias"]` wholesale. So the promise in this file's
    own docstring ("MERGE, NEVER WRITE ... it REFUSES to run if the reserialised object
    loses any key") was true of a level the merge never touched, and blind to the level it
    rewrote. Measured before the fix: running it would silently drop 18 nested keys across
    8 of its 9 targets -- `SECOND_ASSESSOR_2026_08_21` on seven, and eleven on `sglt2-hf`
    including `ONE_ASSESSOR_ONLY`, `sources_read` and `sources_NOT_read`. The projector
    renders several of them, so the loss would have reached readers as silence.

    A guard whose promise is wider than its comparison is worse than no guard: it is a
    licence. This walks the whole tree.

    Lists are indexed rather than descended by identity, because a list whose ORDER changes
    has not lost a key, and this guard is about loss, not about order.
    """
    out = set()
    if isinstance(node, dict):
        for k, v in node.items():
            kp = prefix + "." + str(k) if prefix else str(k)
            out.add(kp)
            out |= key_paths(v, kp)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            out |= key_paths(v, "%s[%d]" % (prefix, i))
    return out


def nest_merge(dst, src):
    """Recursively set src's keys into dst WITHOUT dropping dst's other keys.

    `dst.update(src)` at the top of a block is the whole defect: it keeps the block's name
    and discards everything the block held that the writer did not happen to re-supply.
    Where both sides hold a dict the merge descends; anywhere else src wins, because a
    re-derived scalar or list IS the update this script exists to apply.
    """
    for k, v in src.items():
        if isinstance(v, dict) and isinstance(dst.get(k), dict):
            nest_merge(dst[k], v)
        else:
            dst[k] = v
    return dst


def merge(topic, dup, rob, grade):
    p = os.path.join(REPO, "ssot", topic, topic + ".json")
    if not os.path.exists(p):
        return "absent"
    with io.open(p, encoding="utf-8") as fh:
        obj = json.load(fh)
    before = set(obj.keys())
    before_paths = key_paths(obj)
    n_before = len(json.dumps(obj))

    sc = obj.setdefault("screening", {})
    if isinstance(sc, dict) and topic in dup:
        sc["duplicate_screening"] = dup[topic]

    r = (rob.get("by_topic") or {}).get(topic)
    if r:
        # NEST-MERGE, NOT REPLACE. The seven keys below are the ones this script derives;
        # anything else the object holds under `risk_of_bias` was put there by other work
        # and is not this script's to discard. `by_outcome` is assigned rather than merged
        # because it IS the freshly computed assessment -- merging it would leave records
        # from a previous run beside the new ones with no way to tell them apart.
        nest_merge(obj.setdefault("risk_of_bias", {}),
                   {"tool": rob["authority"]["tool"],
                    "version": rob["authority"]["version"],
                    "handbook": rob["authority"]["handbook"],
                    "unit_of_assessment": rob["authority"]["unit_of_assessment"],
                    "default_rule": rob["default_rule"],
                    "ceiling": rob["ceiling"],
                    "d5_scope_rule": rob.get("d5_scope_rule"),
                    "by_outcome": r})
        if obj["risk_of_bias"].get("d5_scope_rule") is None:
            del obj["risk_of_bias"]["d5_scope_rule"]
    g = (grade.get("by_topic") or {}).get(topic)
    if g:
        nest_merge(obj.setdefault("grade", {}),
                   {"approach": grade["authority"]["approach"],
                    "reference": grade["authority"]["reference"],
                    "handbook_chapter": grade["authority"]["handbook_chapter"],
                    "starting_point": grade["authority"]["starting_point"],
                    "not_rated_up": grade["authority"]["not_rated_up"],
                    "by_outcome": g})
    obj.setdefault("protocol", {}).update(PRESPEC)

    after = set(obj.keys())
    lost = before - after
    if lost:
        # THE MERGE PROMISE, TESTED RATHER THAN ASSERTED.
        return "REFUSED: merge lost top-level key(s) %s" % ", ".join(sorted(lost))
    # THE SAME PROMISE, AT EVERY DEPTH. `by_outcome` is exempt by design and by name:
    # replacing a computed assessment is the update, and its record keys legitimately
    # change between runs. Everything else that existed must still exist.
    after_paths = key_paths(obj)
    deep_lost = sorted(q for q in (before_paths - after_paths)
                       if ".by_outcome" not in q and not q.endswith("by_outcome"))
    if deep_lost:
        return ("REFUSED: merge lost %d nested key path(s), e.g. %s"
                % (len(deep_lost), ", ".join(deep_lost[:6])))
    with io.open(p, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(obj, indent=1))
    return "merged (+%d bytes, %d -> %d top keys, %d -> %d key paths)" % (
        len(json.dumps(obj)) - n_before, len(before), len(after),
        len(before_paths), len(after_paths))


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    with io.open(os.path.join(EV, "duplicate_screening.json"), encoding="utf-8") as fh:
        dup = json.load(fh)
    with io.open(os.path.join(EV, "rob2.json"), encoding="utf-8") as fh:
        rob = json.load(fh)
    with io.open(os.path.join(EV, "grade.json"), encoding="utf-8") as fh:
        grade = json.load(fh)
    topics = sorted(set(list(dup.keys()) + list((rob.get("by_topic") or {}).keys())))
    rc = 0
    for t in topics:
        res = merge(t, dup, rob, grade)
        if res.startswith("REFUSED"):
            rc = 1
        print("%-30s %s" % (t, res))
    return rc


if __name__ == "__main__":
    sys.exit(main())
