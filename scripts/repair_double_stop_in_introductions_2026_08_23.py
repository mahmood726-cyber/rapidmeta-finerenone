"""Remove the double full stop from stored introductions. Non-authored manuscripts only.

# no-control: a targeted text repair, not a detector. Its controls are asserted inline: the
# authored guard is consulted per object before any write, the change must be exactly the
# removal of a duplicated terminator (byte length falls by exactly the number of seams fixed),
# and the grammar-seam gate must report zero afterwards.

WHY A REPAIR AND NOT JUST A GENERATOR FIX. `build_paper_bookkeeping.introduction()` appended a
full stop unless the text ended in "?", so a question already ending in "." received a second
one -- "... not what the withdrawal on this page said.. It examines 2 randomised trials ...".
The generator is fixed. But the writer GUARDS `manuscript.introduction` against overwriting an
existing value, correctly, so the fix cannot reach the ~20 objects that already hold one. The
guard is right and the stored text is wrong, so the stored text is repaired in place.

FOUND BY THE GRAMMAR-SEAM GATE ON ITS FIRST REAL RUN, and it predates today's lead-in work
entirely. Nothing had ever looked at the joins between assembled sentences.
"""
from __future__ import annotations

import glob
import io
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "ssot"))
import atomic_write                                            # noqa: E402
import authored_guard as _ag                                   # noqa: E402
import do_not_rebuild as _dnr                                  # noqa: E402

DOUBLE = re.compile(r"\.\s*\.")


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    apply = "--apply" in sys.argv
    fixed, skipped_authored, seams = [], [], 0
    for p in sorted(glob.glob(os.path.join(REPO, "ssot", "*", "*.json"))):
        t = os.path.basename(os.path.dirname(p))
        if os.path.basename(p) != t + ".json":
            continue
        try:
            o = json.load(io.open(p, encoding="utf-8"))
        except ValueError:
            continue
        man = o.get("manuscript")
        if not isinstance(man, dict):
            continue
        intro = man.get("introduction")
        if not isinstance(intro, str) or not DOUBLE.search(intro):
            continue
        if _ag.is_authored(man):
            skipped_authored.append(t)
            continue
        _dnr.check_object(p)
        n = len(DOUBLE.findall(intro))
        new = DOUBLE.sub(".", intro)
        # THE CHANGE MUST BE EXACTLY THE REMOVAL OF DUPLICATED TERMINATORS. Any other delta
        # means the substitution reached something it should not have.
        if len(intro) - len(new) != n:
            sys.exit("REFUSED on %s: the edit changed %d characters where %d duplicated "
                     "terminators were found. Nothing written."
                     % (t, len(intro) - len(new), n))
        seams += n
        fixed.append(t)
        if apply:
            man["introduction"] = new
            atomic_write.write_json(p, o, indent=1)

    print("objects with a double full stop in manuscript.introduction: %d (%d seam(s))"
          % (len(fixed), seams))
    if skipped_authored:
        print("skipped, AUTHORED manuscript: %s" % ", ".join(skipped_authored))
    for t in fixed[:12]:
        print("   %s" % t)
    if not apply:
        print("")
        print("DRY RUN. Pass --apply to write.")


if __name__ == "__main__":
    main()
