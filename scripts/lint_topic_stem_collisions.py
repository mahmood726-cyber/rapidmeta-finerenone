# -*- coding: utf-8 -*-
"""A repeated TOPICS stem silently replaces a topic, and the survivor may ask a different question.

THE MECHANISM. `add_topic_autodiscover.py` builds `topic_specs` by iterating TOPICS in order,
and every entry writes `outputs/new_topics/<STEM>.json`. Two entries with the same stem write
the same filename, so the LAST one wins -- including when the two carry DIFFERENT condition
patterns, which means they are not duplicates at all but different questions wearing one name.

THE INSTANCE, TRACED TO ITS TWO LINES RATHER THAN ASSUMED.

    OBICETRAPIB_LIPID_AUTO, line 53:    conditions ["hypercholesterol", "atherosclerot"]
    OBICETRAPIB_LIPID_AUTO, line 3902:  conditions ["hyperlipidemia"]

The delivered record holds 8 trials, which the FIRST finds. The SECOND finds ZERO: not one of
those 8 registrations carries the string "hyperlipidemia" -- they carry hypercholesterolemia,
dyslipidemias, high cholesterol. The surviving definition is the one that finds nothing, and
the record it overwrites still reads n_total 8.

    A COLLISION DOES NOT LOOK LIKE AN ERROR FROM EITHER END. The first entry looks like a
    topic that works. The second looks like a topic that found nothing, which is an ordinary
    outcome. Only the pair, seen together, shows that one silently replaced the other.

RATCHET, NOT RETROFIT, which is this repository's own convention for a rule arriving after
the violations. 335 stems are already repeated. They are listed in
scripts/baselines/topic_stem_collision_baseline.json and they are NOT absolved by being
listed -- the run prints them as OWED. What this refuses is a stem gaining a NEW collision,
so the count cannot grow while nobody is looking.

WHY THIS IS A LINT AND NOT A GATE. Fixing 335 collisions means deciding, for each, which
question was meant -- a judgement about the evidence base, not a mechanical rename. A gate
refusing today would block every commit in the repository until someone made 335 such
judgements under time pressure, which is how bad renames happen.

USAGE:  python scripts/lint_topic_stem_collisions.py            (report + refuse new)
        python scripts/lint_topic_stem_collisions.py --write-baseline
        python scripts/lint_topic_stem_collisions.py --selftest  (prove it can refuse)
"""
from __future__ import annotations

import ast
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SOURCE = os.path.join(HERE, "add_topic_autodiscover.py")
BASELINE = os.path.join(HERE, "baselines", "topic_stem_collision_baseline.json")

if hasattr(sys.stdout, "buffer") and getattr(sys.stdout, "encoding", "").lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


def stems_with_patterns(src):
    """(stem, conditions) for every TOPICS entry, in source order, by AST.

    Read by AST rather than by regex because a stem is a string literal in a tuple and a
    regex over 5,900 lines of nested lists would be counting parentheses.
    """
    out = []
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.Assign):
            if not any(isinstance(t, ast.Name) and t.id == "TOPICS" for t in node.targets):
                continue
            if not isinstance(node.value, ast.List):
                continue
            for elt in node.value.elts:
                if isinstance(elt, ast.Tuple) and len(elt.elts) >= 4:
                    try:
                        out.append((ast.literal_eval(elt.elts[0]),
                                    ast.literal_eval(elt.elts[3]),
                                    getattr(elt, "lineno", 0)))
                    except (ValueError, TypeError):
                        continue
    return out


def collisions(entries):
    """{stem: [(lineno, conditions), ...]} for every stem appearing more than once."""
    seen = {}
    for stem, conds, lineno in entries:
        seen.setdefault(stem, []).append((lineno, conds))
    return {s: v for s, v in seen.items() if len(v) > 1}


def load_baseline():
    if not os.path.exists(BASELINE):
        return None
    with io.open(BASELINE, encoding="utf-8") as fh:
        return set(json.load(fh).get("stems", []))


def report(src, baseline):
    """(exit_code, lines). Refuses only stems colliding that are not already baselined."""
    entries = stems_with_patterns(src)
    coll = collisions(entries)
    lines = []
    lines.append("TOPICS entries          %d" % len(entries))
    lines.append("distinct stems          %d" % len({e[0] for e in entries}))
    lines.append("stems appearing twice+  %d" % len(coll))

    # A COLLISION WHERE THE QUESTIONS DIFFER IS THE DANGEROUS KIND, and it is counted
    # separately: two identical entries waste a line, two different ones lose a topic.
    differing = {s: v for s, v in coll.items()
                 if len({tuple(c) for _ln, c in v}) > 1}
    lines.append("of those, with DIFFERENT condition patterns %d  <- one question replaced "
                 "another" % len(differing))

    if baseline is None:
        lines.append("")
        lines.append("NO BASELINE FILE. Nothing can be called NEW without one, so this run "
                     "reports and does not refuse. Write one with --write-baseline.")
        return 0, lines

    new = sorted(set(coll) - baseline)
    fixed = sorted(baseline - set(coll))
    lines.append("baselined stems still colliding %d -- OWED, not cleared by being listed"
                 % len(set(coll) & baseline))
    if fixed:
        lines.append("baselined stems no longer colliding %d (%s)"
                     % (len(fixed), ", ".join(fixed[:5])))
    if not new:
        lines.append("")
        lines.append("NO STEM GAINED A NEW COLLISION.")
        return 0, lines

    lines.append("")
    lines.append("REFUSED: %d stem(s) gained a NEW collision." % len(new))
    for s in new[:25]:
        where = ", ".join("line %d conditions=%r" % (ln, c) for ln, c in coll[s])
        lines.append("   scripts/add_topic_autodiscover.py :: %s -- %s" % (s, where))
    lines.append("")
    lines.append("Each entry writes outputs/new_topics/%s.json, so the LAST wins and the "
                 "earlier definition is lost without a message." % "<STEM>")
    return 1, lines


def selftest():
    """Prove the refusal fires, by planting a collision the baseline cannot excuse.

    A LINT THAT HAS NEVER BEEN SEEN TO REFUSE IS NOT KNOWN TO WORK. It is exactly as quiet
    as one whose parser silently returns nothing, and this parser walks an AST over 5,900
    lines of nested tuples -- a shape where returning nothing is entirely plausible.
    """
    ok = True
    src = io.open(SOURCE, encoding="utf-8").read()
    entries = stems_with_patterns(src)
    if len(entries) < 100:
        print("SELFTEST FAIL: parsed only %d TOPICS entries; the parser is not reading the "
              "list." % len(entries))
        return 1
    print("SELFTEST parser reads %d entries" % len(entries))

    planted = src.replace(
        '    ("VAXNEUVANCE_CHICKENPOX_AUTO", "Vaxneuvance in Chickenpox",',
        '    ("__SELFTEST_PLANTED_STEM__", "planted A", ["x"], ["cond one"]),\n'
        '    ("__SELFTEST_PLANTED_STEM__", "planted B", ["x"], ["cond two"]),\n'
        '    ("VAXNEUVANCE_CHICKENPOX_AUTO", "Vaxneuvance in Chickenpox",', 1)
    if planted == src:
        print("SELFTEST FAIL: could not plant -- the anchor entry has moved.")
        return 1
    code, lines = report(planted, load_baseline() or set())
    if code != 1 or not any("__SELFTEST_PLANTED_STEM__" in ln for ln in lines):
        print("SELFTEST FAIL: a planted colliding stem did NOT cause a refusal.")
        for ln in lines:
            print("   " + ln)
        ok = False
    else:
        print("SELFTEST planted collision -> REFUSED, and the offender is named")

    # The other direction: the unplanted source must NOT refuse against its own baseline.
    code2, _ = report(src, load_baseline())
    if code2 != 0:
        print("SELFTEST FAIL: the unmodified source refuses against its own baseline, so "
              "the lint would block every commit and could not be trusted to mean anything.")
        ok = False
    else:
        print("SELFTEST unmodified source -> no refusal")
    return 0 if ok else 1


def main(argv):
    src = io.open(SOURCE, encoding="utf-8").read()
    if "--selftest" in argv:
        return selftest()
    if "--write-baseline" in argv:
        coll = collisions(stems_with_patterns(src))
        os.makedirs(os.path.dirname(BASELINE), exist_ok=True)
        with io.open(BASELINE, "w", encoding="utf-8") as fh:
            json.dump({
                "_what": "TOPICS stems already colliding in scripts/add_topic_autodiscover.py",
                "_owed": ("These are NOT absolved by being listed. Each is a topic definition "
                          "silently replaced by a later one sharing its stem; fixing one means "
                          "deciding which question was meant, which is a judgement about the "
                          "evidence base and not a rename."),
                "_generated_by": "scripts/lint_topic_stem_collisions.py --write-baseline",
                "count": len(coll),
                "stems": sorted(coll),
            }, fh, indent=2)
            fh.write("\n")
        print("wrote %s with %d stems" % (BASELINE, len(coll)))
        return 0
    code, lines = report(src, load_baseline())
    for ln in lines:
        print(ln)
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv))
