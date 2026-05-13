"""R24b — Use cached PubMed abstracts to auto-fix R24 estimand mismatches.

For each R24 flag, fetch the cached PubMed abstract for the trial's PMID.
Then determine which estimandType the ABSTRACT supports:
  - Contains "hazard ratio" or "HR (" → TTE (use HR)
  - Contains "odds ratio" or "OR (" → BINARY (use OR)
  - Contains "relative risk" or "RR (" or "risk ratio" → BINARY (use RR)
  - Contains "mean difference", "MD", "change from baseline" → CONTINUOUS (use MD)

If the abstract supports a SINGLE estimandType that DIFFERS from what we
have AND matches what AACT said the outcome was → fix it.
"""
from __future__ import annotations
import json, re, sys, io
from pathlib import Path

if hasattr(sys.stdout, "buffer") and getattr(sys.stdout, "encoding", "").lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent.parent
OUT = HERE / "outputs" / "extraction_audit"
DATA = OUT / "data"
PMC = OUT / "pubmed_cache"
DRY = "--dry-run" in sys.argv

r24 = json.loads((OUT / "r24_design_outcomes.json").read_text(encoding="utf-8"))
findings = r24.get("findings", [])
print(f"R24 flagged trials: {len(findings)}")


def detect_in_abstract(abstract):
    """Return set of estimand types supported by the abstract."""
    a = (abstract or "").lower()
    types = set()
    if re.search(r"hazard ratio|\bHR\s*\(|\bHR\s*=", a, re.IGNORECASE): types.add("HR")
    if re.search(r"odds ratio|\bOR\s*\(|\bOR\s*=", a, re.IGNORECASE): types.add("OR")
    if re.search(r"relative risk|\brisk ratio|\bRR\s*\(|\bRR\s*=", a, re.IGNORECASE): types.add("RR")
    if re.search(r"mean difference|\bMD\b\s*\(|\bMD\s*=|change from baseline|least.squares mean|adjusted mean", a, re.IGNORECASE): types.add("MD")
    return types


def aact_type_to_estimand(t):
    return {"TTE": "HR", "CONTINUOUS": "MD", "BINARY": "OR"}.get(t)


# Load trial data
def load_trial(rv, nct):
    p = DATA / f"{rv}.json"
    if not p.exists(): return None
    try: d = json.loads(p.read_text(encoding="utf-8"))
    except: return None
    rd = d.get("realData") or {}
    return rd.get(nct) if isinstance(rd, dict) else None


fixes = []
for f in findings:
    rv = f["review"]; nct = f["nct"]
    aact_type = f["aact_outcome_type"]  # TTE / CONTINUOUS / BINARY
    expected = aact_type_to_estimand(aact_type)
    if not expected: continue
    t = load_trial(rv, nct)
    if not t: continue
    pmid = (t.get("pmid") or "").strip()
    if not pmid: continue
    cache_p = PMC / f"{pmid}.json"
    if not cache_p.exists(): continue
    try: cache = json.loads(cache_p.read_text(encoding="utf-8"))
    except: continue
    abstract = cache.get("abstract", "")
    if not abstract: continue
    detected = detect_in_abstract(abstract)
    # Auto-fix only when:
    #  - Abstract supports exactly ONE estimand type (unambiguous)
    #  - That type matches what AACT primary outcome implies
    if len(detected) == 1 and expected in detected:
        fixes.append({
            "review": rv, "nct": nct, "pmid": pmid,
            "old_estimand": f["estimandType"], "new_estimand": expected,
            "abstract_supports": list(detected),
            "aact_outcome_type": aact_type,
        })

print(f"Auto-fixable (abstract supports unambiguous + AACT-aligned): {len(fixes)}")


def find_block(txt, nct):
    key_pat = re.compile(r'(["\'])' + re.escape(nct) + r'\1\s*:\s*\{')
    m = key_pat.search(txt)
    if not m: return None
    start = m.end(); depth = 1; i = start; in_str = None
    while i < len(txt) and depth > 0:
        ch = txt[i]
        if in_str:
            if ch == "\\": i += 2; continue
            if ch == in_str: in_str = None
        else:
            if ch in ('"', "'"): in_str = ch
            elif ch == "{": depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0: return (m.start(), i+1, start, i)
        i += 1
    return None


def set_field_in_block(txt, body_start, body_end, field, value):
    body = txt[body_start:body_end]
    new_body, n = re.subn(
        r'((["\']?)' + re.escape(field) + r'\2\s*:\s*)(?:["\'][^"\']*["\']|[0-9.eE+-]+|true|false|null)(?=\s*[,}])',
        r'\1"' + value + '"', body, flags=re.IGNORECASE)
    if n == 0: return txt, False
    return txt[:body_start] + new_body + txt[body_end:], True


applied = []
n_fix = 0
seen = set()
for f in fixes:
    key = (f["review"], f["nct"])
    if key in seen: continue
    seen.add(key)
    html_path = HERE / f"{f['review']}.html"
    if not html_path.exists(): continue
    txt = html_path.read_text(encoding="utf-8")
    block = find_block(txt, f["nct"])
    if not block: continue
    _, _, bs, be = block
    new_txt, ok = set_field_in_block(txt, bs, be, "estimandType", f["new_estimand"])
    if ok:
        if not DRY: html_path.write_text(new_txt, encoding="utf-8")
        applied.append({**f, "status": "FIXED_ESTIMAND"})
        n_fix += 1

(OUT / "r24b_pubmed_estimand_fix.json").write_text(
    json.dumps({"candidates": fixes, "applied": applied,
                 "summary": {"estimand_fixed": n_fix}},
                indent=2, ensure_ascii=False), encoding="utf-8")
print(f"\n{'DRY-RUN ' if DRY else ''}Estimand fixes applied: {n_fix}")
