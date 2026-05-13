"""R25 — Retraction Watch cross-check.

Download (or use cached) Retraction Watch CSV via Crossref/GitLab.
For each PMID in our corpus, check if it appears in OriginalPaperPubMedID.
If yes: the paper is RETRACTED — null the PMID and add a "retracted: <reason>"
note in a sidecar file.

Source: https://gitlab.com/crossref/retraction-watch-data (Crossref-hosted,
70K+ records, freely downloadable CSV).
"""
from __future__ import annotations
import json, csv, re, sys, io
from pathlib import Path

if hasattr(sys.stdout, "buffer") and getattr(sys.stdout, "encoding", "").lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent.parent
OUT = HERE / "outputs" / "extraction_audit"
DATA = OUT / "data"
RW_CSV = OUT / "retraction_watch" / "retraction_watch.csv"
DRY = "--dry-run" in sys.argv

if not RW_CSV.exists():
    print(f"Retraction Watch CSV missing at {RW_CSV}")
    sys.exit(1)

# Build PMID → record dict
print(f"Loading {RW_CSV.name}…")
rw_by_pmid = {}
n_rows = 0
with open(RW_CSV, "r", encoding="utf-8", errors="replace") as f:
    reader = csv.DictReader(f)
    for row in reader:
        n_rows += 1
        pmid = (row.get("OriginalPaperPubMedID") or "").strip()
        if pmid and pmid.isdigit() and 6 <= len(pmid) <= 9:
            rw_by_pmid[pmid] = {
                "reason": (row.get("Reason") or "").strip(),
                "title": (row.get("Title") or "")[:120],
                "retract_date": (row.get("RetractionDate") or "")[:10],
                "journal": (row.get("Journal") or ""),
                "nature": (row.get("RetractionNature") or "").strip(),
            }
print(f"Retraction Watch rows: {n_rows}  unique PMIDs in DB: {len(rw_by_pmid)}")

# Collect our PMIDs
hits = []
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
        pmid = (t.get("pmid") or "").strip()
        if not pmid.isdigit(): continue
        if pmid in rw_by_pmid:
            hits.append({"review": rv, "nct": nct, "pmid": pmid,
                          "name": t.get("name"),
                          **rw_by_pmid[pmid]})

print(f"\nOur PMIDs found in Retraction Watch: {len(hits)}")
for h in hits[:20]:
    print(f"  {h['review'][:35]:35s} {h['nct']} PMID={h['pmid']}")
    print(f"    nature: {h.get('nature')}  reason: {h['reason'][:80]}")
    print(f"    title: {h['title']}")
print()
if len(hits) > 20:
    print(f"  … and {len(hits)-20} more")


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


# For Retraction (not correction/erratum), null PMID + null HR (the trial's
# results are unreliable, not just the citation).
RETRACTION_NATURES = {"Retraction", "Withdrawal", "Expression of concern"}
applied = []
n_fix = 0
seen = set()
for h in hits:
    key = (h["review"], h["nct"])
    if key in seen: continue
    seen.add(key)
    html_path = HERE / f"{h['review']}.html"
    if not html_path.exists(): continue
    txt = html_path.read_text(encoding="utf-8")
    block = find_block(txt, h["nct"])
    if not block: continue
    _, _, bs, be = block
    nature = h.get("nature", "")
    new_txt, ok = null_field_in_block(txt, bs, be, "pmid")
    if ok:
        # For full retractions, also null HR+CI (results are retracted)
        if nature in RETRACTION_NATURES:
            for fld in ("publishedHR", "hrLCI", "hrUCI"):
                block2 = find_block(new_txt, h["nct"])
                if not block2: break
                _, _, bs2, be2 = block2
                nt2, ok2 = null_field_in_block(new_txt, bs2, be2, fld)
                if ok2: new_txt = nt2
        if not DRY: html_path.write_text(new_txt, encoding="utf-8")
        applied.append({**h, "status": "NULLED_PMID" +
                         (" + HR/CI" if nature in RETRACTION_NATURES else "")})
        n_fix += 1

(OUT / "r25_retraction_watch.json").write_text(
    json.dumps({"n_in_db": len(rw_by_pmid), "hits": hits, "applied": applied,
                 "summary": {"fixes": n_fix}},
                indent=2, ensure_ascii=False), encoding="utf-8")
print(f"\n{'DRY-RUN ' if DRY else ''}Fixes applied: {n_fix}")
