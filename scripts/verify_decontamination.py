#!/usr/bin/env python
"""Verify Task-2 decontamination of the 29 SGLT2-HF clones.

Asserts the SCOPED deliverable (not blanket token-absence): the false benchmark
is gone, user-facing/SEO text + live search queries are off SGLT2, and inline JS
still parses. The deep Class-D residue (CV-scoring regexes, HFrEF/HFpEF phenotype
subgroup options, outcome-taxonomy label maps, Arabic translation values) is
intentionally left and is NOT asserted absent — it is a documented rebuild item.

Exit 0 = all pass; exit 1 = failures listed.
"""
import io, re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import jscheck
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parent.parent
MAP = ROOT / "outputs" / "_sglt2_clone_rebuild_list.md"

def app_files():
    out = []
    for line in MAP.read_text(encoding="utf-8").splitlines():
        m = re.match(r"\|\s*([A-Z0-9_]+_REVIEW\.html)\s*\|", line)
        if m: out.append(m.group(1))
    return out

# (label, predicate(s)->error_or_None)  predicate returns a problem string or None
def checks(s):
    probs = []
    # C: false benchmark removed
    if re.search(r"PUBLISHED_META_BENCHMARKS\s*=\s*\{\s*\}", s) is None:
        probs.append("PUBLISHED_META_BENCHMARKS not emptied")
    if "Vaduganathan" in s:
        probs.append("Vaduganathan benchmark still present")
    if "21947" in s:
        probs.append("n=21947 SGLT2 benchmark figure still present")
    if re.search(r"Jhund[^\"']*HFrEF-only pool", s):
        probs.append("Jhund SGLT2 benchmark still present")
    # A: user-facing / SEO
    md = re.search(r'<meta name="description" content="([^"]*)"', s)
    if md and re.search(r"Empagliflozin, Dapagliflozin", md.group(1)):
        probs.append("meta description still SGLT2")
    if re.search(r'"description":"[^"]*Empagliflozin, Dapagliflozin', s):
        probs.append("JSON-LD description still SGLT2")
    if "HFrEF Drug Comparison NMA" in s:
        probs.append("H2 section header still 'HFrEF Drug Comparison NMA'")
    if "hfref quadruple therapy" in s:
        probs.append("'hfref quadruple therapy' display slug still present")
    if "hfref_quadruple_therapy" in s:
        probs.append("'hfref_quadruple_therapy' filename slug still present")
    pp = re.search(r'id="p-pop"[^>]*value="([^"]*)"', s)
    if pp and "Adults with heart failure across EF spectrum" in pp.group(1):
        probs.append("PICO population still SGLT2-HF")
    # B: live search queries off SGLT2 drug terms
    if re.search(r"empagliflozin\+OR\+dapagliflozin\+OR\+sacubitril", s, re.I):
        probs.append("CT.gov intr query still SGLT2 drug terms")
    if re.search(r'\(dapagliflozin OR empagliflozin OR "?sotagliflozin"?\) AND heart failure', s, re.I):
        probs.append("CT.gov query still SGLT2 AND heart failure")
    if re.search(r'\(dapagliflozin OR empagliflozin OR "?sglt2"?\) AND "?heart failure"?', s, re.I):
        probs.append("encoded CT.gov fetch query still SGLT2")
    # indication dropdown bug (value/label mismatch from base)
    if re.search(r'<option value="[^"]*">Heart Failure</option>', s):
        probs.append("mf-indication still has a 'Heart Failure' option")
    return probs

def main():
    files = app_files()
    fail = 0
    for fn in files:
        s = (ROOT / fn).read_text(encoding="utf-8")
        probs = checks(s)
        js = jscheck.check(str(ROOT / fn))
        if js:
            probs.append(f"JS PARSE ERROR: {js[:2]}")
        if probs:
            fail += 1
            print(f"FAIL {fn}")
            for p in probs:
                print(f"      - {p}")
        else:
            print(f"ok   {fn}")
    print(f"\n{len(files)-fail}/{len(files)} apps clean")
    return 1 if fail else 0

if __name__ == "__main__":
    sys.exit(main())
