"""What a reader sees when the shell is degraded three ways."""
import io, os, re, sys, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

SRC = r"F:\claude-temp\claude\F--rapidmeta-finerenone\e7f51608-d242-495a-8fdb-f99c306556e9\scratchpad\ARNI_HF_REVIEW_FULL.html"
OUT = os.path.dirname(SRC)
s = open(SRC, encoding="utf-8").read()

variants = {
    "0_asbuilt": s,
    "1_style_stripped": re.sub(r"<style>.*?</style>", "", s, flags=re.S),
    "2_datauri_stripped": re.sub(r'href="data:[^"]*"', 'href="#"', s),
    "3_inputs_removed": re.sub(r"<input[^>]*>", "", s),
    "4_inputs_and_labels_removed":
        re.sub(r"<label[^>]*>.*?</label>", "",
               re.sub(r"<input[^>]*>", "", s), flags=re.S),
    "5_script_stripped": re.sub(r"<script>.*?</script>", "", s, flags=re.S),
}
for k, v in variants.items():
    open(os.path.join(OUT, "deg_%s.html" % k), "w", encoding="utf-8").write(v)

o = Options()
for f in ("--headless=new", "--no-sandbox", "--window-size=1300,1600"):
    o.add_argument(f)
d = webdriver.Chrome(options=o)
print("%-30s %9s %9s %7s %7s  %s"
      % ("variant", "innerText", "visible*", "svgVis", "tabs", "verdict"))
try:
    for k in variants:
        p = os.path.join(OUT, "deg_%s.html" % k).replace("\\", "/")
        d.get("file:///" + p)
        time.sleep(1.0)
        it = d.execute_script("return document.body.innerText") or ""
        vis = d.execute_script("""
          return [...document.querySelectorAll('.panel')]
            .filter(p=>p.getBoundingClientRect().height>2).length;""")
        npanel = d.execute_script("return document.querySelectorAll('.panel').length")
        svgvis = d.execute_script("""
          return [...document.querySelectorAll('svg')]
            .filter(x=>x.getBoundingClientRect().height>2).length;""")
        tabs = d.execute_script("return document.querySelectorAll('.tabnav label').length")
        # is any content unreachable? a panel with zero height and no way to open it
        verdict = ("ALL CONTENT VISIBLE" if vis == npanel else
                   ("%d/%d panels shown, rest reachable by tab" % (vis, npanel)
                    if tabs else
                    "*** %d/%d PANELS HIDDEN WITH NO CONTROL TO OPEN THEM ***"
                    % (npanel - vis, npanel)))
        print("%-30s %9d %9s %7d %7d  %s"
              % (k, len(it), "%d/%d" % (vis, npanel), svgvis, tabs, verdict))
finally:
    d.quit()
print("\n* visible = panel bounding-box height > 2px")
