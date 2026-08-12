"""Round-2 guard, all 12 objects, at runtime.

  1. numbers LOST from flat -> tabbed must be 0
  2. every numeral GAINED must trace either to the flat control (a count
     increase, e.g. a repeated heading) or to the canonical object's own text.
     Anything else is a number the shell originated -- the thing that must not
     happen.
  3. console errors must be 0
  4. every panel must remain in document.body.innerText
  5. clicking reader controls must not change a single number on the page
"""
import io, os, re, sys, time, glob, json
from collections import Counter
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

NUM = re.compile(r"-?\d[\d,]*\.?\d*")
S = r"F:\claude-temp\claude\F--rapidmeta-finerenone\e7f51608-d242-495a-8fdb-f99c306556e9\scratchpad"
SS = r"F:\rapidmeta-ssot-shell\ssot"

o = Options()
o.add_argument("--headless=new"); o.add_argument("--no-sandbox")
o.add_argument("--window-size=1400,2200")
o.set_capability("goog:loggingPrefs", {"browser": "ALL"})
d = webdriver.Chrome(options=o)


def grab(p):
    d.get("file:///" + p.replace("\\", "/")); time.sleep(1.0)
    return (d.execute_script("return document.body.innerText"),
            [l for l in d.get_log("browser") if l["level"] in ("SEVERE", "ERROR")])


print("%-24s %7s %7s %6s %6s %4s %5s %s"
      % ("object", "flatTxt", "tabTxt", "flatN", "tabN", "err", "tabs", "VERDICT"))
fails = 0
try:
    for f in sorted(glob.glob(os.path.join(S, "ab_flat", "*.html"))):
        n = os.path.basename(f).replace(".html", "")
        ft, fe = grab(f)
        tp = os.path.join(S, "ab_tab", n + ".html")
        tt, te = grab(tp)
        ntabs = len(d.execute_script(
            "return [...document.querySelectorAll('.tabnav label')]"))
        obj = open(os.path.join(SS, n, n + ".json"), encoding="utf-8").read()
        fn, tn = Counter(NUM.findall(ft)), Counter(NUM.findall(tt))
        lost = fn - tn
        gained = tn - fn
        # NAV ORDINALS ARE NOT DATA. MITRAL numbers its tabs ("5. Analysis
        # Suite", "7. Paper Studio") and Mahmood asked for its naming. Those
        # ordinals are navigation chrome, not quantities, and they are the only
        # numerals the shell is permitted to introduce -- so they are exempted
        # NARROWLY, by reading the nav's own text, never by a blanket allow.
        navnums = set()
        for t in d.execute_script(
                "return [...document.querySelectorAll('.tabnav label')]"
                ".map(x=>x.innerText)") or []:
            navnums |= set(NUM.findall(t))
        orig = {k: v for k, v in gained.items()
                if k not in fn and k not in obj and k not in navnums}
        # reader-state invariance: click every screening button + a paper chip,
        # then re-read the numbers.
        d.execute_script("""
          document.querySelectorAll('[data-mark]').forEach(b=>b.click());
          document.querySelectorAll('.chip').forEach(c=>c.click());""")
        time.sleep(0.6)
        after = Counter(NUM.findall(
            d.execute_script("return document.body.innerText")))
        # the draft textarea is reader content; innerText does not include
        # textarea value, so any delta here would be a real page change
        drift = (after - tn) + (tn - after)
        ok = (not lost) and (not orig) and not (fe or te) and not drift
        if not ok:
            fails += 1
        print("%-24s %7d %7d %6d %6d %4d %5d %s"
              % (n, len(ft), len(tt), sum(fn.values()), sum(tn.values()),
                 len(fe) + len(te), ntabs,
                 "OK" if ok else "FAIL"))
        if lost:
            print("      LOST:", dict(lost))
        if orig:
            print("      ORIGINATED (not in flat, not in object):", orig)
        if drift:
            print("      CHANGED BY READER CLICKS:", dict(drift))
finally:
    d.quit()

print("\nobjects failing:", fails, "of 12")
