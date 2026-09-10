#!/usr/bin/env python3
"""A STORED COUNT MUST EQUAL THE ARRAY IT COUNTS, AND THE CHECK IS EXECUTABLE.

WHY A CHECK AND NOT A RENDER-TIME DERIVATION.

On 2026-09-04 `screening_of_remainder.iv_iron_2026_08_19.tally` on `iv-iron-hf` read
{EXCLUDED: 13, ELIGIBLE_NO_RESULTS_YET: 10, ELIGIBLE_NOT_POOLABLE: 6} while the 29-row
`trials` array beside it recounted to {14, 10, 5}. The obvious repair is to delete the stored
field and derive it where it renders. THAT REPAIR WOULD HAVE HIDDEN THE DEFECT INSTEAD OF
FINDING IT, and here is the evidence:

    THE WRONG TALLY WAS NEVER RENDERED. IV_IRON_HF_REVIEW.html prints the remainder split
    from a DIFFERENT stored count -- `k_cascade.remainder_dispositions` -- which happened to
    hold 14/5/10 and was right. The reader saw the correct numbers the whole time. The wrong
    proxy sat on the object for two weeks and misled nobody, WHICH IS EXACTLY WHY NOBODY
    FOUND IT.

A render-time derivation fixes the number a reader sees. It does nothing for a number no
reader sees, and it is the unread ones that rot -- they are inherited by the next script, the
next audit, the next sweep, silently. Derivation makes proxies invisible. A check makes them
noisy. This corpus is full of stored counts of arrays, at least two of them counting the SAME
array, so what is needed is something that recounts them all and complains, not one call site
made honest.

Two further reasons, both specific to this repo:

  1. THE OBJECTS ARE HAND-AUTHORED AND HAND-EDITED. `ssot/do_not_rebuild.py` records commits
     that "changed nine served .html files and zero .py and zero .json between them". The
     served text is not reliably a function of the code, so a fix that lives only in a
     renderer is a fix that a direct edit walks straight past. A check reads the artefact.

  2. DELETING A KEY IS A CHANGE TO WHAT THE OBJECT ASSERTS. Other code reads these blocks.
     Removing a stored field to make it underivable is a bigger, less reversible act than
     making it verifiable, and it destroys the evidence of the drift.

WHAT THIS REFUSES TO DO. It never reports PASS for a tally it could not bind to an array. A
stored count with no locatable array is reported UNBOUND and counted separately. An unchecked
proxy is not a passing proxy; it is an unwatched one, and saying "PASS" over it would be the
same class of defect this file exists to catch.

HOW A BINDING IS ESTABLISHED. Conservatively, and never by name. A dict is a candidate tally
if it has two or more integer values. An array is bound to it only if some string field of
that array takes EXACTLY the tally's integer-keyed key set as its distinct values -- not a
subset, not a superset. Set equality is what makes the binding non-accidental. Cross-subtree
bindings that locality cannot reach are declared explicitly in EXPLICIT_BINDINGS below, so
that a proxy sitting far from its array is watched rather than excused.

    Run:   python3 scripts/lint_stored_counts_match_arrays.py [topic ...]
    Exit:  0 all bound tallies agree · 1 at least one disagrees · 2 could not run
"""
import collections
import glob
import io
import json
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from instrument_controls import require_controls

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SSOT = os.path.join(REPO, "ssot")

# Cross-subtree bindings locality cannot find, declared so they are CHECKED and not merely
# reported UNBOUND. Each entry: (topic, dotted path to the tally, dotted path to the array,
# field on the array rows). Add to this list rather than letting a proxy go unwatched.
EXPLICIT_BINDINGS = [
    ("iv-iron-hf",
     "k_cascade.remainder_dispositions",
     "screening_of_remainder.iv_iron_2026_08_19.trials",
     "verdict",
     "The remainder split the served page actually renders. It counts the SAME 29 rows as "
     "screening_of_remainder.iv_iron_2026_08_19.tally, from a different place in the object, "
     "and on 2026-09-04 the two disagreed. Two stored counts of one array is one count too "
     "many; until one of them goes, both are checked."),
]


def _walk_dicts(node, path=""):
    """Yield (path, dict) for every dict in the tree."""
    if isinstance(node, dict):
        yield path, node
        for k, v in node.items():
            for r in _walk_dicts(v, "%s.%s" % (path, k) if path else k):
                yield r
    elif isinstance(node, list):
        for i, v in enumerate(node):
            for r in _walk_dicts(v, "%s[%d]" % (path, i)):
                yield r


def _int_keys(d):
    return {k: v for k, v in d.items()
            if isinstance(v, int) and not isinstance(v, bool)}


def _row_arrays(parent):
    """(key, list-of-dicts) arrays reachable from `parent` at depth 1 or 2."""
    out = []
    for k, v in parent.items():
        if isinstance(v, list) and v and all(isinstance(x, dict) for x in v):
            out.append((k, v))
        elif isinstance(v, dict):
            for k2, v2 in v.items():
                if isinstance(v2, list) and v2 and all(isinstance(x, dict) for x in v2):
                    out.append(("%s.%s" % (k, k2), v2))
    return out


def _bind(tally_ints, rows):
    """Return (field, Counter) if some string field's DISTINCT VALUES equal the tally's keys."""
    fields = set()
    for r in rows:
        fields |= {k for k, v in r.items() if isinstance(v, str)}
    for f in sorted(fields):
        vals = [r[f] for r in rows if isinstance(r.get(f), str)]
        if len(vals) == len(rows) and set(vals) == set(tally_ints):
            return f, collections.Counter(vals)
    return None, None


def _get(obj, dotted):
    cur = obj
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


def check_object(path):
    """Return (passes, failures, unbound) for one object file."""
    with io.open(path, encoding="utf-8") as fh:
        obj = json.load(fh)
    topic = os.path.basename(path)[:-5]
    passes, failures, unbound = [], [], []

    seen = set()

    # 1. explicit bindings first, so they are never reported as unbound
    for t, tpath, apath, field, why in EXPLICIT_BINDINGS:
        if t != topic:
            continue
        tally = _get(obj, tpath)
        rows = _get(obj, apath)
        if not isinstance(tally, dict) or not isinstance(rows, list):
            unbound.append((topic, tpath, "DECLARED BINDING DOES NOT RESOLVE -- %s" % apath))
            continue
        ints = _int_keys(tally)
        got = collections.Counter(r.get(field) for r in rows if isinstance(r, dict))
        got = {k: v for k, v in got.items() if k in ints or k is not None}
        seen.add(tpath)
        if {k: got.get(k, 0) for k in ints} == ints:
            passes.append((topic, tpath, apath + "[]." + field, len(rows), "declared"))
        else:
            failures.append((topic, tpath, apath + "[]." + field, ints,
                             {k: got.get(k, 0) for k in set(ints) | set(got)}, why))

    # 2. locality bindings
    for ppath, parent in _walk_dicts(obj):
        arrays = _row_arrays(parent)
        if not arrays:
            continue
        for k, v in parent.items():
            if not isinstance(v, dict):
                continue
            ints = _int_keys(v)
            if len(ints) < 2:
                continue
            tpath = ("%s.%s" % (ppath, k)) if ppath else k
            if tpath in seen:
                continue
            bound = False
            for akey, rows in arrays:
                field, got = _bind(ints, rows)
                if field is None:
                    continue
                bound = True
                seen.add(tpath)
                apath = ("%s.%s[].%s" % (ppath, akey, field)) if ppath else "%s[].%s" % (akey, field)
                if dict(got) == ints:
                    passes.append((topic, tpath, apath, len(rows), "locality"))
                else:
                    failures.append((topic, tpath, apath, ints, dict(got), "locality binding"))
                break
            if not bound:
                unbound.append((topic, tpath,
                                "no array in scope whose distinct values equal %s"
                                % sorted(ints)))
    return passes, failures, unbound


def _control_failures(planted):
    """Run check_object over a synthetic object and return how many tallies it flags.

    SYNTHETIC ON PURPOSE. The defect that motivated this instrument -- iv-iron-hf's
    tally reading 13/10/6 against a 29-row array that recounts to 14/10/5 -- is LIVE
    corpus data. A control anchored to it would retire itself the moment that object is
    corrected, and would then pass for the wrong reason while looking like it still
    tested something. These two fixtures cannot be fixed out from under the check.

    planted=True  the stored tally says EXCLUDED 3 where the array holds 2 -> MUST flag.
    planted=False the stored tally agrees with the array exactly       -> MUST NOT flag.
    Identical in every respect but the one integer, so what the control proves is that
    the instrument turns on the disagreement and not on the shape.
    """
    obj = {"block": {"tally": {"EXCLUDED": 3 if planted else 2, "ELIGIBLE": 1},
                     "rows": [{"verdict": "EXCLUDED"},
                              {"verdict": "EXCLUDED"},
                              {"verdict": "ELIGIBLE"}]}}
    d = tempfile.mkdtemp(prefix="lscma_control_")
    try:
        fp = os.path.join(d, "control.json")
        with io.open(fp, "w", encoding="utf-8") as fh:
            fh.write(json.dumps(obj))
        return len(check_object(fp)[1])
    finally:
        shutil.rmtree(d, ignore_errors=True)


def main(argv):
    require_controls(
        "lint_stored_counts_match_arrays",
        positive=("a tally planted one out of step with its array is FLAGGED",
                  _control_failures(planted=True), 1),
        negative=("a tally that agrees with its array is NOT flagged",
                  _control_failures(planted=False), 1))
    pattern = os.path.join(SSOT, "*", "*.json")
    files = [p for p in sorted(glob.glob(pattern))
             if os.path.basename(p)[:-5] == os.path.basename(os.path.dirname(p))]
    if argv:
        want = set(argv)
        files = [p for p in files if os.path.basename(p)[:-5] in want]
        if not files:
            print("NOT_RUN: no topic object matched %s" % sorted(want))
            return 2
    if not files:
        print("NOT_RUN: no topic objects found under %s" % SSOT)
        return 2

    P, F, U, unreadable = [], [], [], []
    for p in files:
        try:
            a, b, c = check_object(p)
        except Exception as exc:                                   # noqa: BLE001
            unreadable.append((p, repr(exc)))
            continue
        P += a
        F += b
        U += c

    print("STORED COUNT vs THE ARRAY IT COUNTS -- %d topic objects read" % len(files))
    print()
    if F:
        print("FAIL -- %d stored count(s) disagree with their array:" % len(F))
        for topic, tpath, apath, stored, got, why in F:
            print("  %s" % topic)
            print("    stored   %s = %s" % (tpath, dict(sorted(stored.items()))))
            print("    counted  %s = %s" % (apath, dict(sorted(got.items()))))
            print("    THE ARRAY IS RIGHT AND THE STORED COUNT IS WRONG.")
            print("    binding: %s" % why)
        print()
    for topic, tpath, apath, n, how in P:
        print("  PASS      {:<24} {:<50} == recount of {} (n={}, {} binding)"
              .format(topic, tpath, apath, n, how))
    if U:
        print()
        print("UNBOUND -- %d stored count(s) could NOT be bound to an array and are therefore"
              % len(U))
        print("NOT CHECKED. Reported, never counted as PASS. Most are cascade counts whose")
        print("denominator is not an array on the object at all; a few are proxies that ought")
        print("to be bound and should be added to EXPLICIT_BINDINGS.")
        by_topic = collections.Counter(t for t, _, _ in U)
        if "--verbose" in sys.argv or "-v" in sys.argv:
            for topic, tpath, why in U:
                print("  UNBOUND   %-24s %-50s %s" % (topic, tpath, why))
        else:
            for topic, n in by_topic.most_common(12):
                print("  UNBOUND   %-24s %d" % (topic, n))
            if len(by_topic) > 12:
                print("  ... and %d more topics (re-run with --verbose for every path)"
                      % (len(by_topic) - 12))
    if unreadable:
        print()
        print("NOT_RUN -- %d object(s) could not be read:" % len(unreadable))
        for p, err in unreadable:
            print("  NOT_RUN   %s  %s" % (p, err))

    print()
    print("PASS %d · FAIL %d · UNBOUND (not checked) %d · NOT_RUN %d"
          % (len(P), len(F), len(U), len(unreadable)))
    return 1 if F else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
