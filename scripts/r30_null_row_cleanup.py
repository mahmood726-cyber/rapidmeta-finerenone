"""R30 — Rename fully-null trial keys to NULLED: prefix.

A trial that has all of (pmid, year, tE, tN, cE, cN, publishedHR) null and
either no `group` or a null/empty group field contributes nothing to pooling
but appears as a row in dashboards. Rename its key to NULLED:<NCT> so it's
excluded from pooling but the audit trail is preserved.

Conservative — require ALL of:
  - pmid is null
  - year is null
  - tE, tN, cE, cN ALL null
  - publishedHR null
"""
from __future__ import annotations
import json, re, sys, io
from pathlib import Path

if hasattr(sys.stdout, "buffer") and getattr(sys.stdout, "encoding", "").lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent.parent
OUT = HERE / "outputs" / "extraction_audit"
DATA = OUT / "data"
DRY = "--dry-run" in sys.argv


def is_null_like(v):
    """Treat None, 0, '0', '' as null-like for numerics."""
    if v is None: return True
    if isinstance(v, str) and v.strip() in ("", "null", "None"): return True
    return False


targets = []
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
        pmid_null = is_null_like(t.get("pmid"))
        year_null = is_null_like(t.get("year"))
        numerics_all_null = all(is_null_like(t.get(k)) for k in ("tE", "tN", "cE", "cN"))
        hr_null = is_null_like(t.get("publishedHR"))
        if pmid_null and year_null and numerics_all_null and hr_null:
            targets.append({"review": rv, "nct": nct,
                             "name": t.get("name"), "group": t.get("group")})

print(f"Fully-null rows (pmid+year+tE+tN+cE+cN+HR all null): {len(targets)}")


def null_key(txt, nct):
    nulled = f"NULLED:{nct}"
    if nulled in txt: return txt, 0
    pat = re.compile(r'(["\'])(' + re.escape(nct) + r')(\1)(\s*:)')
    new_txt, n = pat.subn(
        lambda m: f'{m.group(1)}NULLED:{m.group(2)}{m.group(3)}{m.group(4)}', txt)
    return new_txt, n


applied = []
n_fix = 0
seen = set()
for t in targets:
    if (t["review"], t["nct"]) in seen: continue
    seen.add((t["review"], t["nct"]))
    html_path = HERE / f"{t['review']}.html"
    if not html_path.exists(): continue
    txt = html_path.read_text(encoding="utf-8")
    new_txt, n = null_key(txt, t["nct"])
    if n > 0:
        if not DRY: html_path.write_text(new_txt, encoding="utf-8")
        applied.append({**t, "status": "NULLED_KEY"})
        n_fix += 1
    elif f"NULLED:{t['nct']}" in txt:
        applied.append({**t, "status": "ALREADY_NULLED"})

(OUT / "r30_null_row_cleanup.json").write_text(
    json.dumps({"targets": targets, "applied": applied,
                 "summary": {"nct_keys_nulled": n_fix}},
                indent=2, ensure_ascii=False), encoding="utf-8")
print(f"\n{'DRY-RUN ' if DRY else ''}NCT keys nulled: {n_fix}")
