"""Replace Python container reprs inside `build_stamp.properties.*.reason` with English.

APPROVED SCOPE, and the narrower of the two options deliberately. 16 objects, 37 string
values, every one under a field named `reason`. The alternative -- re-running
`build_to_standard.py` -- would regenerate the stamps correctly from the fixed writer but
rewrites a whole stamp block to fix a formatting defect, which is a larger change than the
problem justifies and would bury the diff.

WHAT THIS DOES NOT TOUCH. `build_stamp.properties.*.reason` records which of OUR OWN build
properties held. It is not extracted evidence, not a trial fact, not a screening decision,
and not provenance about the science. Only that one field name is written.

REVERSIBLE AND VERIFIABLE. Every change is a text substitution inside one string; the lint
that found the defect re-run afterwards is the check. `--apply` writes; without it, nothing.
"""
import io
import json
import glob
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# A Python list-of-strings repr: ['a', 'b'] or ['a']. Dict reprs are matched separately
# because their repair is different -- a dict has keys, and flattening one to prose would
# invent a relationship the text does not state, so those are REPORTED and not rewritten.
_LIST = re.compile(r"\[\s*'((?:[^']|'')*)'(?:\s*,\s*'((?:[^']|'')*)')*\s*\]")
_DICT = re.compile(r"\{\s*'[^']*'\s*:")


def english(m):
    items = re.findall(r"'([^']*)'", m.group(0))
    if not items:
        return m.group(0)
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + " and " + items[-1]


def main():
    apply = "--apply" in sys.argv
    changed_objs = 0
    changed_vals = 0
    out_of_scope = 0
    dicts = []

    for p in sorted(glob.glob(os.path.join(REPO, "ssot", "*", "*.json"))):
        slug = os.path.basename(os.path.dirname(p))
        if os.path.basename(p) != slug + ".json":
            continue
        try:
            with io.open(p, encoding="utf-8") as fh:
                obj = json.load(fh)
        except Exception:
            continue
        # POSITIVE FORM, and the gate is right to insist even here. An object with no
        # property block is OUT OF SCOPE rather than skipped, and it is counted, because
        # this script WRITES to objects and must be able to say how many it considered.
        bs = obj.get("build_stamp")
        props = bs.get("properties") if isinstance(bs, dict) else {}
        in_scope = isinstance(props, dict) and bool(props)
        out_of_scope += 0 if in_scope else 1
        props = props if in_scope else {}

        touched = False
        # POSITIVE FORM, per `audit_exclusion_by_absence --gate`: iterate the entries that
        # ARE property blocks carrying a string reason. A loop defined by what it skips
        # cannot report how many it declined to touch, and this one writes to objects.
        reasons = [(k, v) for k, v in props.items()
                   if isinstance(v, dict) and isinstance(v.get("reason"), str)]
        for pname, pblk in reasons:
            val = pblk["reason"]
            if _DICT.search(val):
                dicts.append((slug, pname))
                continue                 # reported, never rewritten
            new = _LIST.sub(english, val)
            if new != val:
                pblk["reason"] = new
                touched = True
                changed_vals += 1
        if touched:
            changed_objs += 1
            if apply:
                # indent=1, matching the corpus. Re-serialising at another indent once
                # buried a semantic change under 119,000 lines of diff.
                io.open(p, "w", encoding="utf-8").write(
                    json.dumps(obj, ensure_ascii=False, indent=1))

    print("objects with no property block (out of scope): %d" % out_of_scope)
    print("objects with a rewritten reason : %d" % changed_objs)
    print("reason strings rewritten        : %d" % changed_vals)
    print("dict reprs found and NOT touched: %d" % len(dicts))
    for slug, pname in dicts[:6]:
        print("   %-30s %s" % (slug, pname))
    if dicts:
        print("   (a dict has keys; flattening one to prose would invent a relationship the")
        print("    text does not state, so these are reported for a person to decide)")
    if not apply:
        print("\nDRY RUN. Re-run with --apply to write.")
    return 0


sys.exit(main())
