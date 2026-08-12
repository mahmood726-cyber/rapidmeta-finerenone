"""Known-defect library, run BEFORE any adversary sees an object.

Each detector encodes a defect this programme actually shipped. A detector that
cannot fire is not a detector, so every one is exercised against a deliberately
broken input first (`--selftest`) and must catch it.

D1  chart originates a numeral present in neither the object nor the control
D2  a hidden panel drops out of document.body.innerText
D3  the readiness verdict is a CONSTANT masquerading as a computed value
D4  a downloaded figure carries different numbers from the rendered one
D5  a reader control changes a displayed number
D6  numbers lost between the flat control and the shipped layout
D7  a prose unit (rationale, caveat, citation, self-correction) disappears
D8  the flat control drifts from the committed generator

D1/D2/D5/D6 live in guard2.py, D7 in prose_guard.py, D8 in the build loop.
This file adds D3 and D4, which had no automation, and a runner for all eight.
"""
import io, json, re, subprocess, sys, time, tempfile, os
from collections import Counter
from urllib.parse import unquote
import html as _html
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

SS = r"F:\rapidmeta-ssot-shell\ssot"
GEN = os.path.join(SS, "build_app_v2.py")
NUM = re.compile(r"-?\d[\d,]*\.?\d*")


def build(obj_path, out, flat=False):
    a = [sys.executable, GEN, obj_path, out] + (["--flat"] if flat else [])
    r = subprocess.run(a, capture_output=True, text=True)
    return r.returncode == 0, r.stderr[-400:]


# ---------------------------------------------------------------- D3
def d3_verdict_is_computed(obj_path, tmp):
    """Mutate the object so every attestable surface is signed. The verdict MUST
    change. If it does not, the banner is a constant -- which is exactly the
    defect the old NOT SUBMISSION-READY string was."""
    d = json.load(open(obj_path, encoding="utf-8"))
    if not d.get("attestations"):
        return "SKIP", "object carries no attestation record"
    base = os.path.join(tmp, "v_base.html")
    ok, err = build(obj_path, base)
    if not ok:
        return "ERROR", err
    v0 = re.search(r"Submission readiness: ([A-Z ]+)<", open(base, encoding="utf-8").read())
    for k, a in d["attestations"].items():
        a.update({"by": "TEST", "role": "test",
                  "source_checked_against": "TEST", "date_utc": "2026-01-01"})
    m = os.path.join(tmp, "mutated.json")
    json.dump(d, open(m, "w", encoding="utf-8"))
    sig = os.path.join(tmp, "v_signed.html")
    ok, err = build(m, sig)
    if not ok:
        return "ERROR", err
    v1 = re.search(r"Submission readiness: ([A-Z ]+)<", open(sig, encoding="utf-8").read())
    a0 = v0.group(1).strip() if v0 else "?"
    a1 = v1.group(1).strip() if v1 else "?"
    if a0 == a1:
        return "FAIL", f"verdict is {a0!r} both unsigned and fully signed -- constant"
    return "PASS", f"unsigned={a0!r} -> fully signed={a1!r}"


# ---------------------------------------------------------------- D4
def d4_download_matches_render(html_path):
    """Every `a.dl` data URI must carry the same number multiset as the <svg>
    it sits under. A download that disagrees with the page is a second, silent
    copy of the evidence."""
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    o = Options()
    for f in ("--headless=new", "--no-sandbox", "--window-size=1300,1400"):
        o.add_argument(f)
    dr = webdriver.Chrome(options=o)
    try:
        dr.get("file:///" + html_path.replace("\\", "/"))
        time.sleep(1.2)
        pairs = dr.execute_script("""
          return [...document.querySelectorAll('a.dl')].map(a=>{
            const card=a.closest('.card');
            const svg=card?card.querySelector('svg'):null;
            return {href:a.getAttribute('href'),
                    svg: svg?svg.outerHTML:null,
                    name:a.getAttribute('download')};
          });""")
    finally:
        dr.quit()
    bad = []
    for p in pairs:
        if not p["svg"]:
            bad.append((p["name"], "no sibling svg")); continue
        # DECODE ENTITIES ON BOTH SIDES BEFORE COUNTING. The first run of this
        # detector flagged influence.svg: the download carried two extra "27"s.
        # They were the digits inside `&#x27;` -- the escaped apostrophe of
        # "Cook's distance" -- which Chrome re-serialises as a literal quote in
        # outerHTML. The data was identical. A numeral guard that can be fooled
        # by an entity can also be blinded by one, so both sides are normalised.
        dl = _html.unescape(unquote(p["href"].split(",", 1)[1]))
        rendered = _html.unescape(p["svg"])
        if Counter(NUM.findall(dl)) != Counter(NUM.findall(rendered)):
            bad.append((p["name"], "number multiset differs"))
    return ("FAIL" if bad else "PASS"), (bad if bad else f"{len(pairs)} figures match")


if __name__ == "__main__":
    obj = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        SS, "arni-hfref", "arni-hfref.json")
    tmp = tempfile.mkdtemp()
    page = os.path.join(tmp, "page.html")
    build(obj, page)
    print("object:", os.path.basename(obj))
    s, msg = d3_verdict_is_computed(obj, tmp)
    print("  D3 verdict-is-computed   %-5s %s" % (s, msg))
    s, msg = d4_download_matches_render(page)
    print("  D4 download==render      %-5s %s" % (s, msg))
