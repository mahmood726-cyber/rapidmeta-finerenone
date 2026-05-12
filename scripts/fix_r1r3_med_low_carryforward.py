"""Apply normalized pattern-match fixes to R1+R2+R3 MED + LOW single-lens findings
that weren't auto-fixed earlier. Lower confidence than HIGH, so restrict to
the most-specific actionable categories: PMID + NCT.
"""
from __future__ import annotations
import json, re, sys, io
from pathlib import Path

if hasattr(sys.stdout, "buffer") and getattr(sys.stdout, "encoding", "").lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent.parent
OUT = HERE / "outputs" / "extraction_audit"


def categorize(category, reason="", issue="", evidence=""):
    blob = " ".join([str(category or ""), str(reason or ""), str(issue or ""), str(evidence or "")]).lower()
    if re.search(r'pmid|citation.?misatt|name.?collision', blob): return "PMID_NULL"
    if re.search(r'fabricat.?trial|nct.?(acronym|mismatch)|fake.?nct', blob): return "NCT_NULL_KEY"
    return "OTHER"


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


def null_key(txt, nct):
    nulled = f"NULLED:{nct}"
    if nulled in txt: return txt, 0
    pat = re.compile(r'(["\'])(' + re.escape(nct) + r')(\1)(\s*:)')
    new_txt, n = pat.subn(
        lambda m: f'{m.group(1)}NULLED:{m.group(2)}{m.group(3)}{m.group(4)}', txt)
    return new_txt, n


# Collect MED + LOW from R1+R2+R3 consensus files
candidates = []
for fname in ["multi_agent_consensus.json", "multi_agent_consensus_r2.json",
              "multi_agent_consensus_r3.json"]:
    p = OUT / fname
    if not p.exists(): continue
    cs = json.loads(p.read_text(encoding="utf-8"))
    for r in cs.get("records", []):
        if r.get("max_severity") not in ("MED", "LOW"): continue
        for ag, det in r.get("details", {}).items():
            ft = categorize(det.get("category"), det.get("reason"))
            if ft in ("PMID_NULL", "NCT_NULL_KEY"):
                candidates.append({
                    "review": r["review"], "nct": r["nct"],
                    "fix_type": ft, "severity": r.get("max_severity"),
                    "source_round": fname,
                    "category": det.get("category"),
                    "reason": (det.get("reason") or "")[:120],
                })
                break

# Dedupe by (review, nct, fix_type)
seen = set(); uniq = []
for c in candidates:
    key = (c["review"], c["nct"], c["fix_type"])
    if key in seen: continue
    seen.add(key); uniq.append(c)

print(f"Candidates (R1+R2+R3 MED+LOW with actionable categories): {len(uniq)}")

n_pmid = n_nct = n_skip = 0
log = []
for c in uniq:
    rv = c["review"]; nct = c["nct"]; ft = c["fix_type"]
    html_path = HERE / f"{rv}.html"
    if not html_path.exists():
        log.append({**c, "status": "FILE_MISSING"})
        continue
    txt = html_path.read_text(encoding="utf-8")
    if ft == "PMID_NULL":
        block = find_block(txt, nct)
        if not block:
            log.append({**c, "status": "BLOCK_NOT_FOUND_OR_NULLED"})
            n_skip += 1
            continue
        _, _, bs, be = block
        new_txt, ok = null_field_in_block(txt, bs, be, "pmid")
        if ok:
            html_path.write_text(new_txt, encoding="utf-8")
            log.append({**c, "status": "NULLED_PMID"})
            n_pmid += 1
        else:
            log.append({**c, "status": "PMID_ALREADY_NULL"})
            n_skip += 1
    elif ft == "NCT_NULL_KEY":
        new_txt, n = null_key(txt, nct)
        if n > 0:
            html_path.write_text(new_txt, encoding="utf-8")
            log.append({**c, "status": "NULLED_KEY"})
            n_nct += 1
        elif f"NULLED:{nct}" in txt:
            log.append({**c, "status": "ALREADY_NULLED"})
            n_skip += 1
        else:
            log.append({**c, "status": "NCT_NOT_FOUND"})
            n_skip += 1

(OUT / "r1r3_med_low_carryforward_fixes.json").write_text(
    json.dumps(log, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"  PMID nulls: {n_pmid}")
print(f"  NCT nulls:  {n_nct}")
print(f"  Skipped:    {n_skip}")
