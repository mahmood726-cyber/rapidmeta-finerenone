"""Extract every rendered figure's ACTUAL plotted series and compare them.

Reading the plotting code tells you what it meant to draw. This renders the page
and reads the geometry back out, which is the only thing that answers "do these
two panels show the same series". Point patterns are normalised to their own
bounding box, so two panels drawing the same data are identical here even when
their axes differ.
"""
import io
import json
import os
import sys
import time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

PAGE = sys.argv[1]
o = Options()
for a in ("--headless=new", "--disable-gpu", "--no-sandbox",
          "--window-size=1500,1200"):
    o.add_argument(a)
d = webdriver.Chrome(options=o)
d.set_page_load_timeout(300)
try:
    d.get("file:///" + PAGE.replace("\\", "/"))
    time.sleep(3)
    d.execute_script("document.querySelectorAll('.panel').forEach(p=>{"
                     "p.style.height='auto';p.style.overflow='visible';});")
    time.sleep(1.5)
    figs = d.execute_script("""
      const out=[];
      document.querySelectorAll('svg').forEach((s,i)=>{
        const card=s.closest('.card');
        const h=card?card.querySelector('h3'):null;
        const cap=card?card.querySelector('p,small,figcaption'):null;
        // marks: circles (scatter), rects (forest/rows squares), polygons
        const circles=[...s.querySelectorAll('circle')].map(c=>[
            +c.getAttribute('cx'), +c.getAttribute('cy')]);
        const rects=[...s.querySelectorAll('rect')].map(c=>[
            +c.getAttribute('x'), +c.getAttribute('y')]);
        const texts=[...s.querySelectorAll('text')].map(t=>t.textContent.trim());
        out.push({i:i,
                  title:h?h.innerText.trim():('svg'+i),
                  aria:s.getAttribute('aria-label')||'',
                  caption:cap?cap.innerText.trim().slice(0,200):'',
                  circles:circles, rects:rects, texts:texts,
                  viewBox:s.getAttribute('viewBox')});
      });
      return out;""")
finally:
    d.quit()


def norm(pts):
    """Normalise a point set to its own bounding box, rounded."""
    if len(pts) < 2:
        return tuple(tuple(round(v, 3) for v in p) for p in pts)
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    dx = (max(xs) - min(xs)) or 1.0
    dy = (max(ys) - min(ys)) or 1.0
    return tuple(sorted((round((p[0] - min(xs)) / dx, 3),
                         round((p[1] - min(ys)) / dy, 3)) for p in pts))


print("FIGURES RENDERED ON THE PAGE: %d\n" % len(figs))
series = {}
for f in figs:
    marks = f["circles"] or f["rects"]
    f["_n"] = len(marks)
    f["_sig"] = norm(marks)
    print("[%d] %-38s marks=%-3d aria=%r" % (f["i"], f["title"][:38],
                                             len(marks), f["aria"][:60]))
    print("     viewBox=%s" % f["viewBox"])
    print("     tick/label texts: %s" % (f["texts"][:12]))
    print("     caption: %s" % f["caption"][:130])
    print()

print("=" * 78)
print("SERIES COLLISION CHECK -- normalised point patterns")
print("=" * 78)
coll = 0
for i in range(len(figs)):
    for j in range(i + 1, len(figs)):
        a, b = figs[i], figs[j]
        if a["_n"] < 2 or b["_n"] < 2:
            continue
        if a["_sig"] == b["_sig"]:
            coll += 1
            print("  COLLISION: [%d] %s  ==  [%d] %s   (%d identical marks)"
                  % (a["i"], a["title"][:30], b["i"], b["title"][:30], a["_n"]))
if not coll:
    print("  none -- every figure's normalised point pattern is distinct")
print("\ncollisions: %d" % coll)

# A figure whose accessible label does not name two axes is either a scatter
# built through the shifted-argument path or a plot type that never declared its
# axes. Both were live here: every scatter announced "\n against <xlab>".
unlabelled = [f for f in figs
              if "(horizontal)" not in f["aria"] and "rows" not in f["aria"]
              and "Forest" not in f["aria"]]
print("figures whose aria-label does not name both axes: %d%s"
      % (len(unlabelled),
         ("  " + ", ".join(f["title"] for f in unlabelled)) if unlabelled else ""))
sys.exit(1 if (coll or unlabelled) else 0)
json.dump([{k: v for k, v in f.items() if k != "_sig"} for f in figs],
          open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "figure_audit.json"), "w", encoding="utf-8"),
          indent=1)
