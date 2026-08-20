"""Render the mapped pages and compare occupancy against the static census.

WHY, IN THE USER'S TERMS. The tab-occupancy matrix was produced by an instrument that had
already been corrected twice in the same run -- once for markup generation, once for
click-lazy rendering. TWO KNOWN BLIND SPOTS IN ONE CENSUS IS NOT A CENSUS. The number
"101 of 116 hold three of eight" was reported as measured fact and is unverified until the
probe is re-run generation-aware and click-aware.

WHAT THE RE-EXAMINATION ESTABLISHED BEFORE RENDERING ANYTHING:

  * The mapped set is 115 G3 pages plus ONE G1 page, not 116 of one family.
  * G3 tabs are PURE CSS -- `<input type="radio" name="rmtab">` plus `<label for="rt-X">`.
    One <script> in the file, no *Engine.render(), no click listeners. So the click blind
    spot that invalidated the G1 numbers DOES NOT APPLY to G3.
  * The `absent-state` div that marks a refused tab sits at offset ~44, IMMEDIATELY after
    the section tag. Panels holding content carry none. So the static classification is
    reading the right marker.

That is three reasons to expect the static matrix to hold, and NOT ONE OF THEM IS A
MEASUREMENT. This renders the pages and compares, because the entire lesson of the run is
that reasoning about what an instrument should see is not a substitute for looking.
"""
from __future__ import annotations
import io
import json
import os
import re
import subprocess
import sys
import tempfile

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
TABS = ["protocol", "search", "screen", "extract", "analysis", "report", "paper",
        "statistics"]
PANEL = re.compile(r'<section class="panel" id="pn-([a-z]+)"', re.I)


def classify(html: str) -> dict:
    marks = [(m.group(1), m.start()) for m in PANEL.finditer(html)]
    out = {}
    for i, (tid, start) in enumerate(marks):
        end = marks[i + 1][1] if i + 1 < len(marks) else len(html)
        seg = html[start:end]
        m = re.search(r'class="absent-state"', seg)
        # TAB-LEVEL REFUSAL ONLY. `absent-state` is ALSO used inside a populated
        # panel for a withdrawn-estimate note, so "contains absent-state anywhere"
        # would score a full panel as empty. The tab-level note is emitted
        # immediately after the section tag; anything deeper is content.
        out[tid] = "-" if (m and m.start() < 200) else "H"
    return out


def render(path: str):
    with tempfile.TemporaryDirectory() as prof:
        cmd = [CHROME, "--headless=new", "--disable-gpu", "--no-sandbox",
               "--user-data-dir=" + prof, "--virtual-time-budget=8000",
               "--dump-dom", "file:///" + path.replace("\\", "/")]
        try:
            r = subprocess.run(cmd, capture_output=True, timeout=120)
        except subprocess.TimeoutExpired:
            return None
        return r.stdout.decode("utf-8", "replace") if r.returncode == 0 else None


def main() -> int:
    pm = sorted(json.load(io.open(os.path.join(REPO, "ssot", "PAGE_MAP.json"),
                                  encoding="utf-8")))
    g3 = []
    for p in pm:
        fp = os.path.join(REPO, p)
        if not os.path.exists(fp):
            continue
        t = io.open(fp, encoding="utf-8", errors="replace").read()
        if '<section class="panel" id="pn-' in t:
            g3.append(p)

    step = max(1, len(g3) // 10)
    sample = [g3[i] for i in range(0, len(g3), step)][:10]

    print("RENDER-VERIFY: static census against rendered DOM")
    print("G3 pages in the mapped set: %d   sample: %d" % (len(g3), len(sample)))
    print()
    print("%-44s %-9s %s" % ("PAGE", "SOURCE", " ".join(t[:4] for t in TABS)))
    agree = differ = failed = 0
    for name in sample:
        fp = os.path.join(REPO, name)
        stat = classify(io.open(fp, encoding="utf-8", errors="replace").read())
        dom = render(fp)
        if dom is None:
            failed += 1
            print("%-44s RENDER FAILED -- not measurable, not zero" % name[:43])
            continue
        rend = classify(dom)
        srow = [stat.get(t, " ") for t in TABS]
        rrow = [rend.get(t, " ") for t in TABS]
        print("%-44s %-9s %s" % (name[:43], "static", "  ".join(srow)))
        print("%-44s %-9s %s   %s" % ("", "rendered", "  ".join(rrow),
                                      "AGREE" if srow == rrow else "*** DIFFERS ***"))
        if srow == rrow:
            agree += 1
        else:
            differ += 1

    print()
    print("agree %d   differ %d   render-failed %d" % (agree, differ, failed))
    if differ == 0 and agree:
        print()
        print("THE STATIC MATRIX HOLDS ON G3. No delta. The click blind spot that")
        print("invalidated the G1 sample does not reach this generation, because these")
        print("tabs are CSS and their panels are emitted by the builder, not by a script.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
