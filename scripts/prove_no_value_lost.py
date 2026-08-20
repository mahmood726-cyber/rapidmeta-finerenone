"""Did any leaf VALUE disappear from an SSOT object, as opposed to moving?

THE COMPANION TO THE PATH-KEYED CHECK, AND THE REASON IT EXISTS IS REGISTRY CLASS 68: a
path-keyed comparison cannot distinguish a relocation from a deletion. Preserving a prior
state under `superseded_state_<stamp>` is exactly a relocation, so the path-keyed check
reports it as loss every time the right thing is done.

This asks the other half: is the VALUE still somewhere in the object? Together the two say
what happened --

    path lost, value present   -> RELOCATED. The right thing, reported as loss by the other
                                  check, which is why both are needed.
    path lost, value absent    -> DELETED. The standing rule breached.
    path present, value changed-> REWRITTEN in place, which neither check flags and which is
                                  a gap both of them share. Stated rather than implied.

THE GAP IS NOT HYPOTHETICAL AND THIS INSTRUMENT ONLY CAUGHT IT BY LUCK. Converting
empagliflozin's `risk_of_bias.ceiling` from a bare string to a dict, I RETYPED the sentence
and wrote `the sources read` where the authored text said `the sources READ`. This check saw
it -- but only because the SHAPE changed too, so the old scalar path vanished. Had the value
stayed a string, a retyped word would have passed both checks in silence. A sentence carried
from one artefact to another should be MOVED, never retyped.


NEITHER CHECK ALONE IS A VERDICT. The one that reports zero is not the reassuring one; the
pair is.
"""
import io
import json
import os
import sys
import glob
import subprocess

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from instrument_controls import require_controls

BS = chr(92)


def leaves(node):
    out = []
    if isinstance(node, dict):
        for v in node.values():
            out += leaves(v)
    elif isinstance(node, list):
        for v in node:
            out += leaves(v)
    else:
        out.append(node)
    return out


def main():
    gate = "--gate" in sys.argv
    old_fix = {"a": {"b": "kept"}, "c": "gone"}
    new_reloc = {"a": {"b": "kept"}, "superseded": {"c": "gone"}}
    new_del = {"a": {"b": "kept"}}
    lost = lambda o, n: [v for v in leaves(o) if v not in set(leaves(n))]
    require_controls(
        "prove_no_value_lost",
        positive=("a value deleted outright", bool(lost(old_fix, new_del)), True),
        negative=("the same value RELOCATED under a superseded key",
                  bool(lost(old_fix, new_reloc)), True))

    total, files, rows = 0, 0, []
    new_at_head, unparsable_at_head = [], []
    for path in sorted(glob.glob(os.path.join(REPO, "ssot", "*", "*.json"))):
        topic = os.path.basename(os.path.dirname(path))
        if os.path.basename(path) != topic + ".json":
            continue
        rel = os.path.relpath(path, REPO).replace(BS, "/")
        raw = subprocess.run(["git", "show", "HEAD:" + rel],
                             capture_output=True).stdout
        # THE POSITIVE PROPERTY IS `HAS A COMMITTED PRIOR STATE`, and the two ways of not
        # having one are NAMED rather than skipped. An object absent from HEAD is new, so it
        # has lost nothing -- but a silent `continue` also drops it out of the denominator,
        # and a reader seeing `155 objects compared` cannot tell 155-of-155 from 155-of-160.
        #
        # THAT IS OPEN ITEM O2 OF THE REGISTRY -- `a scoped pass that does not state its
        # scope` -- which was written in this project about the pre-push regression check,
        # and which I then reproduced in a NEW instrument the same night and quoted a number
        # from. Measured here it was LATENT rather than realised: 155 on disk, 155 compared,
        # 0 excluded. The count I reported was over the whole population. It was true, and it
        # was not KNOWN to be true, and those are different things.
        if not raw:
            new_at_head.append(topic)
            continue
        try:
            old = json.loads(raw.decode("utf-8"))
        except ValueError:
            unparsable_at_head.append(topic)
            continue
        new = json.load(io.open(path, encoding="utf-8"))
        files += 1
        gone = lost(old, new)
        if gone:
            total += len(gone)
            rows.append((topic, gone))

    print("")
    print("OBJECTS ON DISK: %d" % (files + len(new_at_head) + len(unparsable_at_head)))
    print("OBJECTS COMPARED AGAINST HEAD BY VALUE: %d" % files)
    print("NOT COMPARED -- NO COMMITTED PRIOR STATE, SO NOTHING TO LOSE: %d" % len(new_at_head))
    for topic in new_at_head:
        print("    %s -- new since HEAD" % topic)
    if unparsable_at_head:
        print("NOT COMPARED -- THE HEAD COPY DOES NOT PARSE: %d" % len(unparsable_at_head))
        for topic in unparsable_at_head:
            print("    %s -- READ THIS AS A FINDING, not as an exclusion" % topic)
    print("LEAF VALUES GENUINELY ABSENT AFTER THE CHANGE: %d" % total)
    for topic, gone in rows:
        print("    %s -- %d" % (topic, len(gone)))
        for v in gone[:3]:
            print("        %s" % repr(v)[:110])
    if not rows:
        print("    none. Every value present at HEAD is still somewhere in its object.")
    print("")
    print("READ THIS BESIDE THE PATH-KEYED COUNT, NEVER INSTEAD OF IT. A value that moved is")
    print("reported as lost by that one and as present by this one, and the disagreement is")
    print("the information. A value that BOTH report as gone is a deletion.")
    if gate and rows:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
