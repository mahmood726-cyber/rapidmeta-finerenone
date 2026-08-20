"""A Python dict rendered as text on a delivered page. 13 pages, 1,414 occurrences.

`{'POPULATION': 'HOLDS', 'COMPARATOR': 'FAILS', 'INTERVENTION': 'HOLDS'}` on a page a
reader opened is the most literal possible form of "it reads like computer code", and
`EARLY_RHYTHM_CONTROL_AF_REVIEW.html` carries 738 of them. THAT IS NOT A LESSER INSTANCE OF
THE GRADE CELL. IT IS THE SAME DEFECT AT THIRTY TIMES THE SCALE.

THE THREE SOURCES ARE NOT THE SAME KIND OF PROBLEM, AND THE FIX DIFFERS ACCORDINGLY.

  RENDER-TIME.  `_v()` in `build_tabbed.py` is the generic value renderer. Its docstring
                already records that `str()` IS THE BUG rather than the escaping -- it was
                written after `str(None)` put the word "None" in six criteria tables. The
                same `str()` puts a dict repr in a cell. The lesson was learnt for one type
                and not for the type next to it. FIXED HERE, and it reaches every dict or
                list value on every page at the next build.

  WRITE-TIME.   `scripts/screen_*_2026_08_19.py` built exclusion reasons as
                `"fails %s. ALL limbs: %s" % (failing, limbs)` where `limbs` is a dict. The
                repr was baked into the STORED STRING at the moment it was written, so no
                renderer can be blamed and no render-time fix reaches it. The stored strings
                are REPAIRED on the objects, and the three writers are fixed so the next run
                does not re-create them.

                THIS IS NOT THE PROJECTOR REWRITING STORED PROSE. That rule -- which stands,
                and is why the four-decimal GRADE interval was left alone -- protects prose
                an author wrote. This is a VALUE THAT WAS MIS-SERIALISED AT THE POINT OF
                WRITING: nobody chose to say `{'POPULATION': 'HOLDS'}`, a `%s` on a dict
                did. The repair prints the same keys and the same values, in the same order.

  JSON-IN-A-FIELD. `IV_IRON_HF_REVIEW.html` carries raw registry JSON --
                `"title": "All-cause Mortality", "description": "Number of participants..."`
                -- inside a stored string. IV IRON IS ONE OF THE FOUR CLEAN TOPICS AND ONE
                MAHMOOD HAS ALREADY OPENED THIS WEEK. Reported here and NOT rewritten: that
                one is a quoted registry payload, and shortening a quotation is a content
                decision. It is queued, named, and its page is flagged so the rollout does
                not report it as repaired.

WHAT IS NOT CLAIMED. Fixing `_v()` does not make a page clean; it makes the RENDERER stop
producing the defect. A stored string that already contains a repr renders identically
afterwards, which is exactly why the write-time repair is a separate limb of this pass.
"""
import io
import json
import os
import re
import sys
import glob

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TODAY = "2026-08-20"

DICT_IN_TEXT = re.compile(r"\{'[^{}]{0,400}?'\}")


def words_from_repr(text):
    """Turn an embedded dict repr into worded text, printing the same keys and values.

    NOT A PARAPHRASE AND NOT A SUMMARY. Every key and every value survives, in order, with
    underscores replaced and the braces and quotes removed:

        {'POPULATION': 'HOLDS', 'COMPARATOR': 'FAILS'}
        -> population HOLDS, comparator FAILS

    A repr this cannot parse is LEFT EXACTLY AS IT IS. A half-converted dict would be worse
    than an honest one, and a silent partial conversion is how a reader ends up unable to
    tell which half they are reading.
    """
    def one(m):
        blob = m.group(0)
        try:
            import ast
            d = ast.literal_eval(blob)
        except Exception:
            return blob
        if not isinstance(d, dict):
            return blob
        parts = []
        for k, v in d.items():
            key = str(k).replace("_", " ")
            parts.append("%s %s" % (key, v))
        return ", ".join(parts)
    return DICT_IN_TEXT.sub(one, text)


# A FIELD WHOSE JOB IS TO QUOTE MUST NOT BE REWRITTEN, EVEN INTO BETTER WORDS.
# This pass repaired `bempedoic-acid-review.extraction.cells[1].verbatim`, which held
# "{'count': 13970, 'type': 'ACTUAL'}" -- the registry's OWN payload for that cell, stored
# under a key that promises it is quoted. Wording it made the page read better and made the
# field a lie. Reverted, and the rule is now enforced rather than remembered: this is the
# same rule that left the four-decimal GRADE interval alone.
QUOTED_KEYS = ("verbatim", "r_output", "quote", "quoted", "raw", "as_posted",
               "registry_text", "source_text")


def repair_strings(node, counter, key_path=()):
    if isinstance(node, dict):
        out = {}
        for k, v in node.items():
            if str(k).lower() in QUOTED_KEYS:
                out[k] = v          # a quoted field is left exactly as stored
            else:
                out[k] = repair_strings(v, counter, key_path + (str(k),))
        return out
    if isinstance(node, list):
        return [repair_strings(v, counter, key_path) for v in node]
    if isinstance(node, str) and DICT_IN_TEXT.search(node):
        new = words_from_repr(node)
        if new != node:
            counter[0] += 1
            return new
    return node


V_OLD = '''    if x is None:
        return absent
    t = str(x)'''

V_NEW = '''    if x is None:
        return absent
    # A CONTAINER IS NOT A VALUE A READER CAN READ, and `str()` on one produces Python
    # source. This function's own docstring above records `str()` IS THE BUG for the None
    # case; the same str() put
    #
    #     {'domain': 'risk_of_bias', 'levels': -1, 'from': 'HIGH', 'to': 'MODERATE'}
    #
    # into a GRADE table cell and 738 screening-limb dicts onto
    # EARLY_RHYTHM_CONTROL_AF_REVIEW.html. The lesson was learnt for one type and not for
    # the type beside it. Keys and values are all printed -- nothing is summarised away.
    if isinstance(x, dict):
        t = ", ".join("%s %s" % (str(k).replace("_", " "), _v(v, absent=absent))
                      for k, v in x.items()) or absent
        return t if t == absent else t
    if isinstance(x, (list, tuple, set)):
        items = [_v(i, absent=absent) for i in x]
        return "; ".join(i for i in items if i) or absent
    t = str(x)'''


def main():
    dry = "--apply" not in sys.argv

    # ---- 1. the renderer -------------------------------------------------------------
    bt_path = os.path.join(REPO, "ssot", "build_tabbed.py")
    bt = io.open(bt_path, encoding="utf-8").read()
    if "A CONTAINER IS NOT A VALUE A READER CAN READ" in bt:
        print("_v() already handles containers")
    else:
        if bt.count(V_OLD) != 1:
            sys.exit("REFUSED: _v()'s body is not what this pass was written against.")
        bt = bt.replace(V_OLD, V_NEW, 1)

    # ---- 2. the stored strings -------------------------------------------------------
    touched = {}
    total = 0
    for path in sorted(glob.glob(os.path.join(REPO, "ssot", "*", "*.json"))):
        topic = os.path.basename(os.path.dirname(path))
        if os.path.basename(path) != topic + ".json":
            continue
        raw = io.open(path, encoding="utf-8").read()
        if not DICT_IN_TEXT.search(raw):
            continue
        obj = json.loads(raw)
        counter = [0]
        new = repair_strings(obj, counter)
        if counter[0]:
            touched[path] = (new, counter[0], raw)
            total += counter[0]

    print("renderer  : ssot/build_tabbed.py::_v now words dicts, lists, tuples and sets")
    print("objects   : %d string(s) carrying an embedded dict repr, across %d object(s)"
          % (total, len(touched)))
    for p, (_n, c, _r) in sorted(touched.items()):
        print("    %-46s %d" % (os.path.basename(os.path.dirname(p)), c))
    print("")
    print("NOT REPAIRED, AND NAMED: IV_IRON_HF_REVIEW carries raw registry JSON -- the "
          "keys title and description -- inside a stored string. That is a QUOTED PAYLOAD "
          "and shortening a quotation is a content decision, not a serialisation repair.")

    if total == 0 and "A CONTAINER IS NOT A VALUE" in bt:
        sys.exit("REFUSED: nothing to do and the renderer was already patched -- this pass "
                 "would report success having done nothing.")
    if dry:
        print("DRY RUN -- pass --apply to write")
        return

    io.open(bt_path, "w", encoding="utf-8", newline=chr(10)).write(bt)
    for p, (new, c, raw) in sorted(touched.items()):
        nl = chr(13) + chr(10) if (chr(13) + chr(10)) in raw[:4096] else chr(10)
        with io.open(p, "w", encoding="utf-8", newline=nl) as fh:
            json.dump(new, fh, indent=1, ensure_ascii=False)
            fh.write(chr(10))
    print("wrote build_tabbed.py and %d object(s)" % len(touched))


if __name__ == "__main__":
    main()
