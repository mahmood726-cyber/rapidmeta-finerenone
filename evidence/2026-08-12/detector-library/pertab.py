"""What is actually INSIDE each tab panel, at runtime. Per tab, not totals."""
import io, os, sys, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

JS = """
const out = [];
document.querySelectorAll('.panel').forEach(p => {
  const txt = (p.textContent || '').replace(/\\s+/g,' ').trim();
  out.push({
    id: p.id,
    cards:  p.querySelectorAll('.card').length,
    tables: p.querySelectorAll('table').length,
    rows:   p.querySelectorAll('tr').length,
    svg:    p.querySelectorAll('svg').length,
    dl:     p.querySelectorAll('a.dl').length,
    h:      p.querySelectorAll('h2,h3,h4').length,
    chars:  txt.length,
    head:   txt.slice(0, 90)
  });
});
return out;
"""

o = Options()
for f in ("--headless=new", "--no-sandbox", "--window-size=1400,2000"):
    o.add_argument(f)
d = webdriver.Chrome(options=o)
try:
    for path in sys.argv[1:]:
        d.get("file:///" + os.path.abspath(path).replace("\\", "/"))
        time.sleep(1.2)
        rows = d.execute_script(JS)
        print("=" * 100)
        print("%s  (%d bytes)" % (os.path.basename(path), os.path.getsize(path)))
        print("%-14s %6s %7s %5s %5s %4s %4s %8s  %s"
              % ("panel", "cards", "tables", "rows", "svg", "dl", "h", "chars", "state"))
        for r in rows:
            state = ("EMPTY" if r["chars"] < 40 else
                     "STUB" if r["chars"] < 200 and r["cards"] == 0 else
                     "populated")
            print("%-14s %6d %7d %5d %5d %4d %4d %8d  %s"
                  % (r["id"], r["cards"], r["tables"], r["rows"], r["svg"],
                     r["dl"], r["h"], r["chars"], state))
        for r in rows:
            if r["chars"] < 200:
                print("   -> %-14s text=%r" % (r["id"], r["head"]))
finally:
    d.quit()
