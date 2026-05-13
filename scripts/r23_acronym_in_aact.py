"""R23 — verify extracted trial `name` (acronym) appears in AACT for the NCT.

For each (review, NCT, name): check that the name appears in AACT's
brief_title, official_title, acronym field, OR id_information.id_value
for that exact NCT.

If NOT found:
  - If the name is generic placeholder (NCT###, Study-#, C017, etc.):
    → null name (extraction fallback marker)
  - If the name is a real-looking acronym AND not generic:
    → null PMID (the trial-identity is broken; force re-extract)
"""
from __future__ import annotations
import json, csv, re, sys, io
from pathlib import Path
from collections import defaultdict, Counter

if hasattr(sys.stdout, "buffer") and getattr(sys.stdout, "encoding", "").lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent.parent
OUT = HERE / "outputs" / "extraction_audit"
DATA = OUT / "data"
AACT = Path("D:/AACT-storage/AACT/2026-04-12")
DRY = "--dry-run" in sys.argv

# Generic placeholder patterns
GENERIC_NAME_RE = re.compile(
    r"^(NCT\d{8}|Study[- ]?\d*|Trial[- ]?\d*|Phase[- ]?\d|"
    r"[A-Z]{1,3}\d{2,5}|C\d{3,4}|N0\d+|PER-\d+|JANSSEN-\d+|"
    r"YKP3089[-\w]*|[A-Z]+-001|MEZAGITAMAB-\w+|Vivitrol-\w+|"
    r"NCT\d+[a-z]?)$",
    re.IGNORECASE
)


def is_generic(name):
    if not name or len(name) < 3: return True
    return bool(GENERIC_NAME_RE.match(name))


# Collect target trials with meaningful name + NCT
target = []
for json_p in sorted(DATA.glob("*.json")):
    if json_p.name.startswith("_"): continue
    rv = json_p.stem
    try: d = json.loads(json_p.read_text(encoding="utf-8"))
    except: continue
    rd = d.get("realData") or {}
    if not isinstance(rd, dict): continue
    for nct, t in rd.items():
        if not isinstance(t, dict): continue
        if nct.startswith("NULLED:"): continue
        if not re.match(r"^NCT\d{8}$", nct): continue
        name = (t.get("name") or "").strip()
        if not name: continue
        target.append({"review": rv, "nct": nct, "name": name})

target_ncts = sorted({t["nct"] for t in target})
print(f"Target trials with name: {len(target)}  unique NCTs: {len(target_ncts)}")

target_set = set(target_ncts)

# Load AACT
def load_aact(filename, key_col, want_cols, filter_set):
    out = defaultdict(list)
    with open(AACT / filename, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f, delimiter="|")
        for row in reader:
            k = (row.get(key_col) or "").strip().upper()
            if k in filter_set:
                out[k].append({c: (row.get(c) or "").strip() for c in want_cols})
    return out


print("Loading AACT studies + id_information…")
studies = load_aact("studies.txt", "nct_id",
                     ["brief_title", "official_title", "acronym"], target_set)
id_info = load_aact("id_information.txt", "nct_id",
                     ["id_value", "id_type", "id_source"], target_set)
print(f"  studies: {len(studies)}  id_information: {len(id_info)}")


def normalize(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


# Verify
findings = []
for t in target:
    rv = t["review"]; nct = t["nct"]; name = t["name"]
    s = studies.get(nct, [])
    if not s: continue  # NCT not in AACT — already covered by R7-S1
    aact = s[0]
    name_norm = normalize(name)
    if not name_norm: continue
    # Check all AACT text fields for this NCT
    blob = " ".join([
        aact.get("brief_title", ""),
        aact.get("official_title", ""),
        aact.get("acronym", ""),
    ])
    blob_norm = normalize(blob)
    # Also check id_information
    for entry in id_info.get(nct, []):
        blob_norm += " " + normalize(entry.get("id_value", ""))
    found = name_norm in blob_norm
    if not found:
        findings.append({
            "review": rv, "nct": nct, "name": name,
            "is_generic": is_generic(name),
            "aact_title": (aact.get("brief_title") or "")[:80],
            "aact_acronym": aact.get("acronym") or "",
            "fix": ("NULL_NAME" if is_generic(name) else "NULL_PMID"),
        })

print(f"Names NOT found in AACT title/IDs: {len(findings)}")
print(f"  Generic-placeholder names: {sum(1 for f in findings if f['is_generic'])}")
print(f"  Real-looking-but-missing names: {sum(1 for f in findings if not f['is_generic'])}")


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


def null_field_in_block(txt, body_start, body_end, field):
    body = txt[body_start:body_end]
    new_body, n = re.subn(
        r'((["\']?)' + re.escape(field) + r'\2\s*:\s*)(?:["\'][^"\']*["\']|[0-9.eE+-]+|true|false)(?=\s*[,}])',
        r'\1null', body, flags=re.IGNORECASE)
    if n == 0: return txt, False
    return txt[:body_start] + new_body + txt[body_end:], True


applied = []
n_name = n_pmid = 0
seen = set()
for f in findings:
    key = (f["review"], f["nct"], f["fix"])
    if key in seen: continue
    seen.add(key)
    html_path = HERE / f"{f['review']}.html"
    if not html_path.exists(): continue
    txt = html_path.read_text(encoding="utf-8")
    block = find_block(txt, f["nct"])
    if not block: continue
    _, _, bs, be = block
    if f["fix"] == "NULL_NAME":
        new_txt, ok = null_field_in_block(txt, bs, be, "name")
        if ok:
            if not DRY: html_path.write_text(new_txt, encoding="utf-8")
            applied.append({**f, "status": "NULLED_NAME"})
            n_name += 1
        else:
            applied.append({**f, "status": "NAME_ALREADY_NULL"})
    elif f["fix"] == "NULL_PMID":
        new_txt, ok = null_field_in_block(txt, bs, be, "pmid")
        if ok:
            if not DRY: html_path.write_text(new_txt, encoding="utf-8")
            applied.append({**f, "status": "NULLED_PMID"})
            n_pmid += 1
        else:
            applied.append({**f, "status": "PMID_ALREADY_NULL"})

out_p = OUT / "r23_acronym_vs_aact.json"
out_p.write_text(json.dumps({"findings": findings[:200], "applied": applied,
                              "summary": {"name_nulls": n_name, "pmid_nulls": n_pmid}},
                             indent=2, ensure_ascii=False), encoding="utf-8")
print(f"\n{'DRY-RUN ' if DRY else ''}Fixes:")
print(f"  name nulls (generic placeholder):    {n_name}")
print(f"  PMID nulls (real-acronym not in AACT): {n_pmid}")
