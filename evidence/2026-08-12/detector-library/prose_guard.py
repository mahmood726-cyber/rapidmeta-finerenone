"""CONTENT NON-REGRESSION.

Numerals cannot detect prose loss. This takes every sentence-length text unit
from two baselines -- the flat control (all the original ARNI depth) and the
round-2 tabbed exemplar -- and asserts each still appears in the merged page.

Reported as a count with losses named, the same way numerals are.
"""
import io, re, sys, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

MIN = 45          # ignore fragments too short to be a claim
S = r"F:\claude-temp\claude\F--rapidmeta-finerenone\e7f51608-d242-495a-8fdb-f99c306556e9\scratchpad"


def norm(t):
    return re.sub(r"\s+", " ", t).strip()


def units(txt):
    out = set()
    for line in txt.split("\n"):
        line = norm(line)
        if not line:
            continue
        # split into sentences but keep them whole enough to be meaningful
        for s in re.split(r"(?<=[.;:])\s+(?=[A-Z(])", line):
            s = norm(s)
            if len(s) >= MIN:
                out.add(s)
        if len(line) >= MIN:
            out.add(line)
    return out


o = Options()
o.add_argument("--headless=new"); o.add_argument("--no-sandbox")
o.add_argument("--window-size=1400,2400")
d = webdriver.Chrome(options=o)


def txt(p):
    d.get("file:///" + p.replace("\\", "/")); time.sleep(1.1)
    return d.execute_script("return document.body.innerText")


try:
    flat = txt(S + r"\ab_flat\arni-hfref.html")
    r2 = txt(S + r"\ARNI_R2_BASELINE.html")
    new = txt(S + r"\ab_tab\arni-hfref.html")
finally:
    d.quit()

new_n = norm(new)
report = []
for label, base in (("flat control (original ARNI depth)", flat),
                    ("round-2 tabbed exemplar", r2)):
    u = units(base)
    missing = sorted(x for x in u if norm(x) not in new_n)
    report.append((label, len(u), missing))

print("=== CONTENT NON-REGRESSION (text units >= %d chars) ===" % MIN)
for label, n, missing in report:
    print("  %-38s checked=%4d  LOST=%d" % (label, n, len(missing)))
print()
for label, n, missing in report:
    if missing:
        print("--- LOST from %s ---" % label)
        for m in missing[:25]:
            print("   *", m[:200])
print("\nchars: flat=%d  round2=%d  merged=%d" % (len(flat), len(r2), len(new)))

KEY = [
    "PIONEER-HF", "Pathadka 2020", "Zhao 2022", "ANSWER-HF", "Li 2019",
    "10.10.4.4", "10.10.4.5", "HKSJ", "leave-one-out", "win ratio",
    "every instance of HR is heart rate", "An earlier version",
    "eligibility could not be established", "rate ratio",
]
print("\n=== named must-survive strings ===")
for k in KEY:
    print("  %-40s flat=%d  round2=%d  merged=%d"
          % (k, flat.count(k), r2.count(k), new.count(k)))
