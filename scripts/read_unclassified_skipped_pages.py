"""The pages the reading-order rollout skipped that NEITHER marker set classifies.

READING LIST, NOT A DEFECT COUNT. `audit_skipped_but_current.py` separates the skipped set
by markers: this generator's own headings, or the old PRISMA/AMSTAR template's. A page
matching NEITHER is UNCLASSIFIED -- which is not evidence that it is old, and that
distinction is the whole point of the three-state reporting there.

THIS GOES ONE STEP FURTHER AND SAYS WHAT THEY DO CARRY, so the reading list is actionable
rather than a list of names. For each: does it carry a build stamp, does it resolve to an
object, does it carry a paper panel, and how large is it. None of those is a verdict; a page
can be perfectly good and simply predate the markers.

THE COUNTS MOVE WITH THE CORPUS AND THAT IS STATED. The classification reads CURRENT page
content against a skip list recorded at 11:20. Pages rebuilt since then can cross from
UNCLASSIFIED into CURRENT -- SGLT2_MACE_CVOT did exactly that tonight when it gained a
manuscript. So the count is a function of WHEN IT IS RUN, and a number quoted from it must
carry the run, not just the date.
"""
import io
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from instrument_controls import require_controls          # noqa: E402
import audit_skipped_but_current as A                     # noqa: E402

STAMP = re.compile(r"build[_ ]stamp|page_standard_version|built_by", re.I)


def main():
    require_controls(
        "read_unclassified_skipped_pages",
        positive=("a page carrying a current-generator marker is detected",
                  any(m in "Endpoint definitions, read from the registry" for m in A.CURRENT),
                  True),
        negative=("a page carrying only old-template text matches a CURRENT marker",
                  any(m in "RapidMeta Precision v9" for m in A.CURRENT), True))

    if not os.path.exists(A.LOG):
        print("NOT_ASSESSABLE: the rollout log that DEFINES the skipped set is absent (%s). "
              "Without it this entry has no artefact and should be struck rather than "
              "reconstructed." % A.LOG)
        return 2
    log = io.open(A.LOG, encoding="utf-8", errors="replace").read()
    skipped = sorted(set(re.findall(r"([A-Z0-9_]+\.html)\s+SKIPPED", log)))

    pagemap = {}
    pm = os.path.join(REPO, "ssot", "PAGE_MAP.json")
    if os.path.exists(pm):
        for p, o in json.load(io.open(pm, encoding="utf-8")).items():
            pagemap[os.path.basename(str(p))] = str(o)

    rows = []
    missing = []
    for name in skipped:
        path = os.path.join(REPO, name)
        if not os.path.exists(path):
            missing.append(name)
            continue
        text = io.open(path, encoding="utf-8", errors="replace").read()
        vis = A.visible(text)
        cur = sum(1 for m in A.CURRENT if m in vis)
        old = sum(1 for m in A.OLD if m in vis)
        if cur or old:
            continue                       # classified by the existing audit
        rows.append({
            "page": name,
            "bytes": os.path.getsize(path),
            "stamp": bool(STAMP.search(text)),
            "paper_panel": 'id="pn-paper"' in text,
            "object": pagemap.get(name, "-- not in PAGE_MAP --"),
        })

    print("")
    print("SKIPPED PAGES NAMED BY THE ROLLOUT LOG: %d" % len(skipped))
    if missing:
        print("   no longer on disk, NAMED not dropped: %d -- %s"
              % (len(missing), ", ".join(missing)))
    print("UNCLASSIFIED BY EITHER MARKER SET:        %d of %d" % (len(rows), len(skipped)))
    print("")
    print("   with a build stamp                     %d of %d"
          % (len([r for r in rows if r["stamp"]]), len(rows)))
    print("   with a paper panel                     %d of %d"
          % (len([r for r in rows if r["paper_panel"]]), len(rows)))
    print("   resolving to an object via PAGE_MAP    %d of %d"
          % (len([r for r in rows if not r["object"].startswith("--")]), len(rows)))
    print("")
    print("%-52s %9s %6s %6s %s" % ("page", "bytes", "stamp", "paper", "object"))
    for r in sorted(rows, key=lambda x: -x["bytes"]):
        print("%-52s %9d %6s %6s %s"
              % (r["page"][:52], r["bytes"], "yes" if r["stamp"] else "no",
                 "yes" if r["paper_panel"] else "no", r["object"]))
    print("")
    print("A READING LIST. None of these columns is a verdict -- a page can be current and")
    print("simply predate the marker headings. What it buys is that the next reader opens")
    print("the ones with a stamp and no paper panel FIRST, rather than opening 25 at random.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
