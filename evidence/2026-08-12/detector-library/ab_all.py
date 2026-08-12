"""Runtime A/B over every object: flat control vs tabbed, one browser."""
import io, os, re, sys, time, glob, json
from collections import Counter
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

NUM = re.compile(r"-?\d[\d,]*\.?\d*")
S = r"F:\claude-temp\claude\F--rapidmeta-finerenone\e7f51608-d242-495a-8fdb-f99c306556e9\scratchpad"

o = Options()
o.add_argument("--headless=new"); o.add_argument("--no-sandbox")
o.add_argument("--disable-gpu"); o.add_argument("--window-size=1400,2200")
o.set_capability("goog:loggingPrefs", {"browser": "ALL"})
d = webdriver.Chrome(options=o)


def grab(path):
    d.get("file:///" + path.replace("\\", "/"))
    time.sleep(0.9)
    t = d.execute_script("return document.body.innerText")
    errs = [l for l in d.get_log("browser") if l["level"] in ("SEVERE", "ERROR")]
    return t, errs


rows, bad = [], 0
try:
    for f in sorted(glob.glob(os.path.join(S, "ab_flat", "*.html"))):
        n = os.path.basename(f)
        g = os.path.join(S, "ab_tab", n)
        ft, fe = grab(f)
        tt, te = grab(g)
        fn, tn = Counter(NUM.findall(ft)), Counter(NUM.findall(tt))
        lost, gained = fn - tn, tn - fn
        ok = not lost
        if not ok or fe or te:
            bad += 1
        rows.append((n.replace(".html", ""), len(ft), len(tt),
                     sum(fn.values()), sum(tn.values()),
                     dict(lost), dict(gained), len(fe) + len(te)))
finally:
    d.quit()

print("%-26s %8s %8s %6s %6s %4s  %s" %
      ("object", "flatTxt", "tabTxt", "flatN", "tabN", "err", "LOST / GAINED"))
for r in rows:
    print("%-26s %8d %8d %6d %6d %4d  LOST=%s GAINED=%s"
          % (r[0], r[1], r[2], r[3], r[4], r[7], r[5] or "{}", r[6] or "{}"))
print("\nobjects with a LOST numeral or a console error:", bad, "of", len(rows))
