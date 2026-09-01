# -*- coding: utf-8 -*-
"""Three-way merge two versions of an SSOT object BY KEY, refusing to guess.

WHY THIS EXISTS, AND WHY A FILE-LEVEL DECISION IS THE WRONG SHAPE HERE.

Merging origin/main into a topic branch on 2026-08-31, the dapivirine object
conflicted as a single hunk of 20,462 lines. Measured:

    their side  +1,016 lines   (work inside existing keys)
    my side     +10 top-level keys

`--ours` would have deleted a lane's night of work. `--theirs` would have deleted
mine. BOTH RESOLVE CLEANLY AND BOTH LOSE WORK, and the log records neither.

Merged by key instead, of 36 top-level keys:

    18 identical on both sides
     2 changed by them only        -> theirs
    11 changed by me only          -> mine
     5 changed by both             -> recursed

and recursing those five reached SIX leaf conflicts, which turned out to be ONE
semantic difference repeated (a trial label carrying a sponsor protocol number).
A 20,462-line conflict was six decisions.

    THE RULE AT EVERY NODE: take the side that CHANGED; keep base where neither
    did; and REFUSE TO GUESS where both changed. Every unresolved leaf is
    printed with both values, and the caller decides.

USAGE

    python scripts/merge3_json_by_key.py BASE.json MINE.json THEIRS.json [-o OUT.json]

    git show $(git merge-base HEAD origin/main):ssot/X/X.json > base.json
    git show HEAD:ssot/X/X.json                               > mine.json
    git show origin/main:ssot/X/X.json                        > theirs.json

Exit 0 when every node resolved without guessing. Exit 1 when leaves remain --
the output is still written, using MINE at each unresolved leaf, and every one is
listed so nothing is silently chosen.

⚠️ SIZE IS NOT RICHNESS. In the case this was written for, one side was 6.6x
larger than the other and the difference was mostly provenance prose. Do not use
byte counts to decide which side is 'more complete'; that is the same error as
reading MB/s as throughput.
"""
import argparse
import io
import json
import os
import sys

MISSING = object()


def merge(base, mine, theirs, conflicts, path=()):
    """Return the merged value, appending (path, mine, theirs) for each guess refused."""
    if mine == theirs:
        return mine
    if mine == base:
        return theirs
    if theirs == base:
        return mine

    if isinstance(mine, dict) and isinstance(theirs, dict):
        b = base if isinstance(base, dict) else {}
        out = {}
        # THEIR key order first, then keys only I have -- so a merged object reads
        # like the destination branch with additions appended, which keeps the
        # diff against origin/main small and reviewable.
        for k in list(theirs) + [k for k in mine if k not in theirs]:
            bb = b.get(k, MISSING)
            mm = mine.get(k, MISSING)
            tt = theirs.get(k, MISSING)
            if mm is MISSING:
                out[k] = tt
            elif tt is MISSING:
                out[k] = mm
            else:
                out[k] = merge(bb, mm, tt, conflicts, path + (k,))
        return out

    if isinstance(mine, list) and isinstance(theirs, list) and len(mine) == len(theirs):
        b = base if isinstance(base, list) else []
        return [merge(b[i] if i < len(b) else MISSING, mine[i], theirs[i],
                      conflicts, path + (i,))
                for i in range(len(mine))]

    # ⛔ LISTS OF DIFFERENT LENGTH ARE NOT MERGED BY INDEX. Element 3 of one side
    # is not element 3 of the other once anything is inserted, and merging them
    # positionally silently pairs unrelated records. Refuse and let the caller
    # look.
    conflicts.append((path, mine, theirs))
    return mine


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("base")
    ap.add_argument("mine")
    ap.add_argument("theirs")
    ap.add_argument("-o", "--out", default=None,
                    help="write the merged object here (default: report only)")
    ap.add_argument("--indent", type=int, default=None,
                    help="output indent; default matches THEIRS, which is the "
                         "destination branch's convention")
    a = ap.parse_args()

    def load(p):
        with io.open(p, encoding="utf-8") as fh:
            return json.load(fh)

    base, mine, theirs = load(a.base), load(a.mine), load(a.theirs)
    conflicts = []
    out = merge(base, mine, theirs, conflicts)

    def size(o):
        return len(o) if isinstance(o, (dict, list)) else 1

    print("THREE-WAY MERGE BY KEY")
    print("  base   %-44s %d top-level" % (os.path.basename(a.base), size(base)))
    print("  mine   %-44s %d top-level" % (os.path.basename(a.mine), size(mine)))
    print("  theirs %-44s %d top-level" % (os.path.basename(a.theirs), size(theirs)))
    print("  merged %-44s %d top-level" % ("", size(out)))

    if isinstance(base, dict) and isinstance(mine, dict) and isinstance(theirs, dict):
        same = only_m = only_t = both = 0
        for k in set(base) | set(mine) | set(theirs):
            b, m, t = base.get(k, MISSING), mine.get(k, MISSING), theirs.get(k, MISSING)
            if m == t:
                same += 1
            elif m == b:
                only_t += 1
            elif t == b:
                only_m += 1
            else:
                both += 1
        print()
        print("  TOP-LEVEL KEYS BY KIND -- the denominator of every decision below")
        print("    identical on both sides        %3d" % same)
        print("    changed by THEM only -> theirs %3d" % only_t)
        print("    changed by ME only   -> mine   %3d" % only_m)
        print("    changed by BOTH -> recursed    %3d" % both)

    print()
    print("  LEAVES WHERE BOTH SIDES CHANGED AND NEITHER CAN BE PREFERRED: %d"
          % len(conflicts))
    for p, m, t in conflicts:
        print()
        print("    path   %s" % ".".join(str(x) for x in p))
        print("    mine   %s" % repr(m)[:300])
        print("    theirs %s" % repr(t)[:300])

    if a.out:
        indent = a.indent
        if indent is None:
            with io.open(a.theirs, encoding="utf-8") as fh:
                second = (fh.read().split("\n") + ["", ""])[1]
            indent = len(second) - len(second.lstrip(" ")) or 1
        crlf = b"\r\n" in open(a.theirs, "rb").read()
        txt = json.dumps(out, ensure_ascii=False, indent=indent) + "\n"
        data = txt.encode("utf-8")
        if crlf:
            data = data.replace(b"\n", b"\r\n")
        with open(a.out, "wb") as fh:
            fh.write(data)
        print()
        print("  written %s  (indent=%d, %s)"
              % (a.out, indent, "CRLF" if crlf else "LF"))
        if conflicts:
            print("  ⚠️ MINE was used at each unresolved leaf above. Every one is listed;")
            print("     none was chosen silently. Read them before committing the result.")

    return 1 if conflicts else 0


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                  errors="replace")
    sys.exit(main())
