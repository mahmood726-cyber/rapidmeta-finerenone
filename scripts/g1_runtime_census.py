"""Actual tab occupancy on G1 pages, measured by RENDERING them.

STRUCTURAL PRESENCE IS NOT OCCUPANCY, and on this generation the difference is total. A G1
page carries `<div id="tab-screen" class="tab-content">` in its served bytes and fills it
at load from `ScreenEngine.render()`. So a static reader sees seven tabs on 434 pages and
learns NOTHING about whether any of them holds content -- the same reason content_gate
cannot check a V2 page.

Reporting "7 tabs present" for these would be the exact error the mapped-corpus census
made when it scored SOTATERCEPT_PAH_AUTO_2 at zero: mistaking what the instrument can see
for what is there. In that case the instrument under-read; here it would over-read. BOTH
DIRECTIONS ARE THE SAME DEFECT.

So: render a sample in Chrome, wait for the engines, and measure the text each panel
actually holds. A SAMPLE IS NOT THE POPULATION and the number is reported as a sample.
"""
import io
import json
import os
import subprocess
import sys
import tempfile

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
REPO = r"F:\rapidmeta-ssot-shell"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
TABS = ["protocol", "search", "screen", "extract", "analysis", "report", "paper",
        "statistics"]
FLOOR = 400          # same spirit as the builder's content floor

SAMPLE = [
          "ABALOPARATIDE_OSTEO_AUTO_FULL_REVIEW.html",
          "AVATROMBOPAG_CIT_AUTO_FULL_REVIEW.html",
          "BUDESONIDE_IBD_AUTO_FULL_REVIEW.html",
          "DELANDISTROGENE_DMD_AUTO_FULL_REVIEW.html",
          "ERDAFITINIB_BLADDER_AUTO_FULL_REVIEW.html",
          "GOSERELIN_PROSTATE_AUTO_FULL_REVIEW.html",
          "IXEKIZUMAB_PSORIASIS_AUTO_FULL_REVIEW.html",
          "MOMELOTINIB_MF_AUTO_2.html",
          "OZANIMOD_CROHN_DISEASE_AUTO_FULL_REVIEW.html",
          "PPSV23_VACCINE_AUTO_FULL_REVIEW.html",
          "RUCAPARIB_PROSTATE_AUTO_FULL_REVIEW.html",
          "TIRZEPATIDE_ARDS_AUTO_FULL_REVIEW.html"
]

JS = """
(() => {
  const out = {};
  for (const t of %s) {
    const el = document.getElementById('tab-' + t);
    if (!el) { out[t] = null; continue; }
    const txt = (el.innerText || el.textContent || '').replace(/\\s+/g,' ').trim();
    const data = el.querySelectorAll('table, svg, li').length;
    out[t] = {n: txt.length, d: data};
  }
  return JSON.stringify(out);
})()
""" % json.dumps(TABS)


def render(path):
    """Load the page in headless Chrome and evaluate the probe after the engines run."""
    with tempfile.TemporaryDirectory() as prof:
        # --virtual-time-budget lets the page's own scripts finish before the dump.
        cmd = [CHROME, "--headless=new", "--disable-gpu", "--no-sandbox",
               "--user-data-dir=" + prof, "--virtual-time-budget=9000",
               "--run-all-compositor-stages-before-draw",
               "--dump-dom", "file:///" + path.replace("\\", "/")]
        try:
            r = subprocess.run(cmd, capture_output=True, timeout=120)
        except subprocess.TimeoutExpired:
            return None
        if r.returncode != 0:
            return None
        return r.stdout.decode("utf-8", "replace")


def main():
    import re
    print("G1 RUNTIME TAB CENSUS -- rendered, not read from served bytes")
    print("sample of %d pages; a sample is not the population" % len(SAMPLE))
    print()
    rows = []
    for name in SAMPLE:
        p = os.path.join(REPO, name)
        if not os.path.exists(p):
            print("  %-46s FILE ABSENT" % name[:45])
            continue
        dom = render(p)
        if dom is None:
            print("  %-46s RENDER FAILED -- not measurable, not zero" % name[:45])
            continue
        st = []
        for t in TABS:
            m = re.search(r'id="tab-%s"' % t, dom)
            if not m:
                st.append(" ")
                continue
            seg = dom[m.start():m.start() + 400000]
            nxt = re.search(r'id="tab-(?!%s)' % t, seg[10:])
            if nxt:
                seg = seg[:nxt.start() + 10]
            text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", seg)).strip()
            data = len(re.findall(r"<(?:table|svg|li)[ >/]", seg))
            st.append("H" if (len(text) >= FLOOR and data >= 1) else "-")
        rows.append((name, st))
        print("  %-46s %s" % (name[:45], "  ".join(st)))

    if rows:
        print()
        print("  %-46s %s" % ("TAB", " ".join(t[:4] for t in TABS)))
        held = [sum(1 for _, st in rows if st[i] == "H") for i in range(len(TABS))]
        print("  %-46s %s" % ("HELD in sample",
                              " ".join("%-4d" % h for h in held)))
        print()
        print("  pages in sample with all 7 present tabs held: %d of %d"
              % (sum(1 for _, st in rows if all(s != "-" for s in st[:7])), len(rows)))
    print()
    print("A RENDER FAILURE IS 'NOT MEASURABLE', NEVER 'ZERO TABS HELD'.")


if __name__ == "__main__":
    main()
