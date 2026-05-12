"""Push the 8-agent fixes to MED severity (was HIGH-only).

MED findings indicate "likely defect, lower confidence" — applying the same
normalized pattern-match fixer. Lower-confidence fixes ARE riskier (FP rate
goes up), so this is a balanced choice: only auto-fix MED for the highest-
specificity categories (PMID, NCT-mismatch, schema). Don't auto-fix MED for
broader categories (effect-magnitude, copy-paste) — those benefit from
human review.
"""
from __future__ import annotations
import json, re, sys, io
from pathlib import Path
from collections import Counter

if hasattr(sys.stdout, "buffer") and getattr(sys.stdout, "encoding", "").lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent.parent
OUT = HERE / "outputs" / "extraction_audit"
DRY = "--dry-run" in sys.argv


# Categorizer (same as round-2 extended)
def categorize(category, reason, issue="", evidence=""):
    c = (category or "").lower(); r = (reason or "").lower()
    i = (issue or "").lower(); e = (evidence or "").lower()
    blob = " ".join([c, r, i, e])
    if re.search(r'pmid|citation.?misatt|name.?collision', blob): return "PMID_NULL"
    if re.search(r'fabricat.?trial|nct.?(acronym|mismatch)|fake.?nct|name.?is.?nct|consecutive.?nct|trial.?identity', blob):
        return "NCT_NULL_KEY"
    if re.search(r'rate.?in.?count|fractional.?event|estimand.?mismatch|schema|negative.?hr|estimandtype|estimand_type', blob):
        return "SCHEMA_NULL"
    return "SKIP_FOR_MED"  # don't auto-fix other MED categories


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
            if ch in ('"',"'"): in_str = ch
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


agg = json.loads((OUT / "8agent_aggregate.json").read_text(encoding="utf-8"))
n_pmid = n_nct = n_schema = n_skip = 0
log = []

for f in agg["findings"]:
    if f.get("severity") != "MED": continue
    rv = f.get("review", "")
    nct = f.get("nct", "")
    if not rv or not nct: continue
    fix_type = categorize(f.get("category"), f.get("reason"),
                          f.get("issue", ""), f.get("evidence", ""))
    if fix_type == "SKIP_FOR_MED":
        n_skip += 1
        log.append({**f, "fix_type": fix_type, "status": "SKIPPED_MED_BROAD_CAT"})
        continue
    html_path = HERE / f"{rv}.html"
    if not html_path.exists():
        log.append({**f, "fix_type": fix_type, "status": "FILE_MISSING"})
        continue
    txt = html_path.read_text(encoding="utf-8")
    if fix_type == "PMID_NULL":
        block = find_block(txt, nct)
        if not block:
            log.append({**f, "fix_type": fix_type, "status": "BLOCK_NOT_FOUND"})
            continue
        _, _, bs, be = block
        new_txt, ok = null_field_in_block(txt, bs, be, "pmid")
        if ok:
            if not DRY: html_path.write_text(new_txt, encoding="utf-8")
            log.append({**f, "fix_type": fix_type, "status": "NULLED_PMID"})
            n_pmid += 1
        else:
            log.append({**f, "fix_type": fix_type, "status": "PMID_ALREADY_NULL"})
    elif fix_type == "NCT_NULL_KEY":
        new_txt, n = null_key(txt, nct)
        if n > 0:
            if not DRY: html_path.write_text(new_txt, encoding="utf-8")
            log.append({**f, "fix_type": fix_type, "status": "NULLED_KEY"})
            n_nct += 1
        elif f"NULLED:{nct}" in txt:
            log.append({**f, "fix_type": fix_type, "status": "ALREADY_NULLED"})
        else:
            log.append({**f, "fix_type": fix_type, "status": "NCT_NOT_FOUND"})
    elif fix_type == "SCHEMA_NULL":
        block = find_block(txt, nct)
        if not block: continue
        _, _, bs, be = block
        changes = 0
        for fld in ("tE", "tN", "cE", "cN"):
            new_txt, ok = null_field_in_block(txt, bs, be, fld)
            if ok:
                txt = new_txt
                block = find_block(txt, nct)
                if not block: break
                _, _, bs, be = block
                changes += 1
        if changes:
            if not DRY: html_path.write_text(txt, encoding="utf-8")
            log.append({**f, "fix_type": fix_type, "status": "NULLED_EVENTS"})
            n_schema += 1

out_p = OUT / "med_severity_fixes.json"
out_p.write_text(json.dumps(log, indent=2, ensure_ascii=False), encoding="utf-8")

print(f"{'DRY-RUN ' if DRY else ''}MED-severity fixes:")
print(f"  PMID nulls:    {n_pmid}")
print(f"  NCT nulls:     {n_nct}")
print(f"  Schema nulls:  {n_schema}")
print(f"  Skipped (broad MED category, human review preferred): {n_skip}")
print(f"\nLog → {out_p}")
