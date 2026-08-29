# -*- coding: utf-8 -*-
"""PAGE WEIGHT AS A CLINICAL PROPERTY, with a budget.

THE READER THIS EXISTS FOR. A doctor in Laos or Bangladesh on a metered phone connection. For
that reader a 7 MB page is not evidence, it is a bill -- and no AI judge will ever mark us down
for it. This is the clearest case measured so far where the audience test and the judge test
point in opposite directions, and where they do, the doctor wins.

⭐ WHAT THE MEASUREMENT FOUND, and it is larger than the weight problem it was looking for:

  indexed pages                            26      total 48.0 MB
  <img> tags across all of them            16
  inline <svg> figures                    297
  PNG bytes inside <a download> links    38.9 MB   81% of ALL page weight
  PNG bytes anywhere else                 1.1 MB

⇒ EVERY READER DOWNLOADS 38.9 MB OF RASTER THAT IS NEVER DISPLAYED. The figures on screen are
inline SVGs -- the pages label them "1 KB" beside a 400 KB PNG of the same plot. The rasters
exist only as `<a download>` convenience links, and a data: URI in an href is part of the
document: it is paid for on load, by everyone, whether or not anyone clicks it.

Removing them takes the indexed corpus from 48.0 MB to 9.1 MB, an 81% reduction, WITH NO
VISIBLE CHANGE.

⛔ NOT DONE UNILATERALLY. It removes a feature from 163 pages and the blast radius is counted
rather than assumed. The recommended fix keeps the feature at zero cost: render the PNG in the
browser from the SVG already on the page, on click. That needs a ruling and a generator change,
so this module MEASURES and REPORTS and the removal waits.

THE BUDGET. Proposed, and deliberately generous, because a budget nobody can meet is ignored:
  green   under 500 KB   opens on a slow connection without thinking about it
  amber   under 2 MB     opens, but a metered reader notices
  red     over 2 MB      the reader we built this for will close it
"""
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(os.path.dirname(os.path.dirname(HERE)))

GREEN, AMBER = 500_000, 2_000_000


def measure(path):
    h = io.open(path, encoding="utf-8", errors="replace").read()
    total = len(h.encode("utf-8"))
    png_dl = 0
    for m in re.finditer(r'data:image/png;base64,([A-Za-z0-9+/=]+)', h):
        if re.search(r"<a[^>]*download=", h[max(0, m.start() - 160):m.start()], re.I):
            png_dl += len(m.group(1))
    text = len(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ",
                      re.sub(r"(?is)<(script|style).*?</\1>", " ", h))))
    return {"page": os.path.basename(path), "bytes": total,
            "undisplayed_raster": png_dl, "rendered_text": text,
            "without_raster": total - png_dl,
            "band": "green" if total < GREEN else ("amber" if total < AMBER else "red"),
            "band_without_raster": "green" if (total - png_dl) < GREEN
            else ("amber" if (total - png_dl) < AMBER else "red")}


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                                  line_buffering=True)
    ready = json.load(io.open(r"F:\claude-temp\pend\ready.json", encoding="utf-8"))
    pages = sorted({t["page"] for t in (ready.get("keep") or [])} |
                   {a["page"] for a in (ready.get("admitted_by_ruling") or [])})
    rows = [measure(p) for p in pages if os.path.exists(p)]
    rows.sort(key=lambda r: -r["bytes"])
    tot = sum(r["bytes"] for r in rows)
    ras = sum(r["undisplayed_raster"] for r in rows)
    print("")
    print("PAGE WEIGHT -- measured for a reader on a metered connection")
    print("")
    print("  %-42s %8s %10s %9s" % ("page", "MB", "band", "MB if the"))
    print("  %-42s %8s %10s %9s" % ("", "", "", "raster goes"))
    for r in rows[:10]:
        print("  %-42s %8.2f %10s %9.2f"
              % (r["page"][:42], r["bytes"] / 1e6, r["band"], r["without_raster"] / 1e6))
    print("")
    for band in ("red", "amber", "green"):
        now = sum(1 for r in rows if r["band"] == band)
        after = sum(1 for r in rows if r["band_without_raster"] == band)
        print("  %-6s now %2d   after removing undisplayed raster %2d" % (band, now, after))
    print("")
    print("  corpus %.1f MB  ->  %.1f MB   (%.0f%% is raster nobody sees)"
          % (tot / 1e6, (tot - ras) / 1e6, 100.0 * ras / tot))
    out = r"F:\claude-temp\pend\out\page_weight.json"
    json.dump(rows, io.open(out, "w", encoding="utf-8"), indent=1)
    print("  detail -> page_weight.json")
    print("")
    print("  ⚠️ MEASURED, NOT FIXED. Removing the download links touches 163 pages and drops a")
    print("     feature; the fix that keeps it is client-side rendering from the SVG already")
    print("     present. Both need a ruling.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
