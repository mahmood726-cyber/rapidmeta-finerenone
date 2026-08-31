# -*- coding: utf-8 -*-
"""PLANT: prove the published-correction guard fires, and that it is CALLED.

⛔ WHY BOTH HALVES ARE NEEDED. A guard that works and is never invoked is the
"available, not operative" defect this repo has shipped repeatedly -- most
recently nine repo gates written, tested and called by nothing. Proving the
function refuses is half the job; proving the builder runs it before the write
is the other half, and the second half is the one that gets skipped.

FOUR ASSERTIONS, EACH ON REAL BYTES

  1 the guard PASSES on a real correction page as it stands today
  2 the guard REFUSES the same page with the correction removed
  3 the guard REFUSES when the pinned list is absent -- an absent list is not an
    empty list, and a silent skip would merge two opposite facts
  4 the guard is WIRED: build_tabbed.py calls it immediately before the write

⭐ NOTHING ON DISK IS TOUCHED. The planted defect is made in memory, so there is
no restore to get wrong -- and a restore verified by anything short of a byte
comparison is how a test leaves damage behind.

    python scripts/plant_correction_survives_rebuild.py
"""
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "ssot"))

PROTECTED = {"BEMPEDOIC_ACID_REVIEW.html", "CANGRELOR_PCI_REVIEW.html",
             "INCRETIN_HFpEF_REVIEW.html", "ARNI_HF_REVIEW.html"}


def pick():
    """A real page with a pinned correction, avoiding every protected page."""
    p = os.path.join(ROOT, "scripts", "baselines", "published_corrections.json")
    with io.open(p, encoding="utf-8") as fh:
        pages = json.load(fh).get("pages", {})
    for name, rec in sorted(pages.items()):
        if rec.get("class") != "PUBLISHED_CORRECTION" or not rec.get("must_render"):
            continue
        if name in PROTECTED or "HFREF" in name or "ARNI" in name:
            continue
        if os.path.exists(os.path.join(ROOT, name)):
            return name, rec["must_render"]
    return None, None


def main():
    import do_not_rebuild as dnr

    page, must = pick()
    if page is None:
        print("REFUSED: no page carries a PINNED published correction, so this plant "
              "has nothing real to test. That is a finding, not a pass.")
        return 2
    path = os.path.join(ROOT, page)
    with io.open(path, encoding="utf-8", errors="replace") as fh:
        html = fh.read()
    before = len(html)
    print("PLANT: published-correction guard")
    print("  page   %s  (%d bytes)" % (page, before))
    print("  pinned %s" % must[:120])
    print("")

    ok = True

    # 1 -- passes as it stands
    try:
        dnr.check_correction_survives(path, html)
        print("  1 PASS  the guard accepts the page as it stands today")
    except SystemExit as exc:
        print("  1 *** FAIL *** the guard refuses an UNMODIFIED page: %s" % str(exc)[:160])
        ok = False

    # 2 -- refuses with the correction removed
    norm = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html))
    frag = re.sub(r"\s+", " ", must).strip()
    # Remove the sentence from the RENDERED text by removing the words that carry
    # it; the crudest reliable planting is to delete the longest run of the pinned
    # sentence wherever it appears in the source.
    longest = max(re.split(r"<[^>]+>", must), key=len) if "<" in must else must
    planted = html.replace(longest.strip(), "", 1) if longest.strip() in html else None
    if planted is None:
        words = [w for w in frag.split(" ") if len(w) > 6][:8]
        planted = html
        for w in words:
            planted = planted.replace(w, "", 1)
    try:
        dnr.check_correction_survives(path, planted)
        print("  2 *** FAIL *** the guard ACCEPTED a page with the correction removed. "
              "It cannot report the thing it exists for.")
        ok = False
    except SystemExit as exc:
        msg = str(exc)
        named = page in msg and "DROPPED IT" in msg
        print("  2 PASS  the guard refuses the page with the correction removed")
        print("          and %s the page and quotes the correction"
              % ("names" if named else "*** DOES NOT name ***"))
        if not named:
            ok = False

    # 3 -- an absent list refuses rather than passing
    real = dnr.CORRECTIONS
    try:
        dnr.CORRECTIONS = os.path.join(ROOT, "scripts", "baselines",
                                       "__absent_for_the_plant.json")
        try:
            dnr.check_correction_survives(path, html)
            print("  3 *** FAIL *** an ABSENT list was treated as an empty one")
            ok = False
        except SystemExit as exc:
            print("  3 PASS  an absent list refuses: %s" % str(exc)[:90])
    finally:
        dnr.CORRECTIONS = real

    # 4 -- the guard is actually CALLED, immediately before the write
    with io.open(os.path.join(ROOT, "ssot", "build_tabbed.py"), encoding="utf-8") as fh:
        src = fh.read().split("\n")
    call = [i for i, l in enumerate(src) if "check_correction_survives(" in l]
    write = [i for i, l in enumerate(src)
             if l.strip().startswith('open(out, "w"') and ".write(_html)" in l]
    if call and write and 0 < (write[0] - call[0]) <= 3:
        print("  4 PASS  build_tabbed.py calls it %d line(s) before the write"
              % (write[0] - call[0]))
    else:
        print("  4 *** FAIL *** the guard is not called immediately before the write "
              "(call=%s write=%s). A guard nothing invokes is not operative."
              % (call, write))
        ok = False

    # nothing was written; prove it
    with io.open(path, encoding="utf-8", errors="replace") as fh:
        after = len(fh.read())
    print("")
    print("  page unchanged on disk: %s (%d -> %d bytes)"
          % ("yes" if before == after else "*** NO ***", before, after))
    if before != after:
        ok = False

    print("")
    print("  %s" % ("PLANT PROVEN: the guard refuses a dropped correction, refuses an "
                    "absent list, and is invoked before the write."
                    if ok else
                    "PLANT NOT PROVEN -- read the failures above. Until this passes, no "
                    "page may be rebuilt."))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.exit(main())
