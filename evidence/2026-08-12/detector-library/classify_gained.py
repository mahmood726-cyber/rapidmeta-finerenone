"""Every gained numeral must be either (a) a count increase of a numeral ALREADY
on the flat page -- i.e. a repeated heading, no new value -- or (b) a substring
of the object's own GRADE block. Anything else is a fabricated number."""
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
d = webdriver.Chrome(options=o)


def txt(p):
    d.get("file:///" + p.replace("\\", "/")); time.sleep(0.9)
    return d.execute_script("return document.body.innerText")


verdicts = []
try:
    for f in sorted(glob.glob(os.path.join(S, "ab_flat", "*.html"))):
        n = os.path.basename(f).replace(".html", "")
        ft = txt(f)
        tt = txt(os.path.join(S, "ab_tab", n + ".html"))
        fn, tn = Counter(NUM.findall(ft)), Counter(NUM.findall(tt))
        gained = tn - fn
        # the object's grade text, concatenated
        j = json.load(open(os.path.join(SS, n, n + ".json"), encoding="utf-8"))
        gtext = ""
        for blk in j["results"]["by_outcome"].values():
            g = blk.get("grade")
            if g:
                gtext += json.dumps(g)
        unexplained = {}
        for num, c in gained.items():
            if num in fn:                      # (a) count increase only
                continue
            if num in gtext:                   # (b) verbatim from GRADE
                continue
            unexplained[num] = c
        verdicts.append((n, dict(gained), unexplained))
finally:
    d.quit()

print("%-26s %-42s %s" % ("object", "gained", "UNEXPLAINED"))
tot = 0
for n, g, u in verdicts:
    tot += len(u)
    print("%-26s %-42s %s" % (n, str(g)[:42], u or "-- none --"))
print("\nTOTAL unexplained (= fabricated) numerals across all 12 objects:", tot)
