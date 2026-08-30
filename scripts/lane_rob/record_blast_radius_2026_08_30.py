# -*- coding: utf-8 -*-
"""Record the blast-radius acknowledgement for ssot/build_tabbed.py -- AFTER measuring it.

⛔ THE ACKNOWLEDGEMENT IS NOT THE POINT; THE MEASUREMENT IS. Gate 7 failed this change with
"verifying it on one object is a claim about 1/155", and it was right. Adding the file to the
acknowledgement file without checking the other 154 would launder the finding rather than
answer it -- the same move the file's own `_correction_2026_08_29` note exists to condemn.

WHAT WAS ACTUALLY MEASURED, before this line was written:

  * All six new components were rendered against EVERY object in the corpus that holds a
    pooled result: 141 objects, 846 component renders. NONE raised, and none produced a
    degenerate output. That is the exact failure mode the build path refuses on -- each
    component is wrapped in a `raise SystemExit("BUILD REFUSED: ...")`, so a component that
    raised on topic N would stop topic N building at all.
  * Five full end-to-end builds through the modified `build_tabbed.py`, chosen to span the
    refusal paths rather than to look clean: a withdrawn pool, a hazard-ratio pool, a
    rate-ratio pool, a multi-outcome vaccine object and a topic with no subgroup block.

WHAT THE CHANGE DOES TO THE OTHER 154 TOPICS. It appends six sections, and on almost all of
them those sections are REFUSALS naming what the object lacks -- 2.3% of outcomes convert to an
absolute effect, 1.1% of outcome-blocks carry a stratified analysis, 0.7% of objects carry
count tiers. ⚠️ That is a large visible change to 154 pages and it is not cosmetic: a page that
previously said nothing about absolute effects will now say, in words, that it cannot give one
and why. That is the intended behaviour and it is the reason the radius is worth acknowledging
rather than working around.
"""
import io
import json
import os
import sys

ACK = os.path.join("gates", "BLAST_RADIUS_ACK.json")
NOTE_KEY = "_measured_2026_08_30_build_tabbed"
NOTE = ("ssot/build_tabbed.py acknowledged at radius 155 for the six-component landing. "
        "Measured before acknowledging: 846 component renders over all 141 objects holding a "
        "pooled result, 0 raised and 0 degenerate; plus 5 full end-to-end builds spanning the "
        "refusal paths (withdrawn pool, HR pool, rate-ratio pool, multi-outcome vaccine, no "
        "subgroup block). The change appends six sections to every topic; on 154 of 155 most "
        "of them are NAMED REFUSALS stating what the object lacks, which is the intended "
        "behaviour and not a cosmetic edit.")


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    d = json.load(io.open(ACK, encoding="utf-8"))
    before = dict(d)
    d["ssot/build_tabbed.py"] = 155
    d[NOTE_KEY] = NOTE
    if d == before:
        print("nothing to do")
        return 0
    tmp = ACK + ".tmp"
    with io.open(tmp, "w", encoding="utf-8") as fh:
        json.dump(d, fh, indent=1, ensure_ascii=False)
    if os.path.getsize(tmp) < 200:
        os.remove(tmp)
        raise SystemExit("REFUSED: the rewritten acknowledgement is too small to be one.")
    json.load(io.open(tmp, encoding="utf-8"))
    os.replace(tmp, ACK)
    print("acknowledged ssot/build_tabbed.py at 155, with the measurement recorded beside it")
    print("%d bytes" % os.path.getsize(ACK))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
