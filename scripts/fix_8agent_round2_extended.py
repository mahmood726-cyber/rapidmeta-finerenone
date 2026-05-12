"""Extended 8-agent fix pass — pattern-match all variant category names
and free-form reasons to apply the right fix.

Why needed: the 8 blinded agents used inconsistent category labels:
  "pmid-unrelated" vs "PMID_MISATTRIBUTION" vs "pmid_misattribution" vs
  "citation_misattribution" vs "WRONG_DRUG_PMID_MISATTRIBUTION"
  ... all mean "PMID is wrong, null it."

This pass normalizes via case-insensitive keyword matching on
(category, reason) and applies the appropriate fix.

Fix taxonomy:
  PMID_NULL     — anything matching pmid|citation|misattribut
  NCT_NULL_KEY  — anything matching fabricat-trial|nct-mismatch|fake_nct|name_is_nct
  EFFECT_NULL   — anything matching effect[_]direction|effect[_]size_implaus|fabricated_control|fabricat[_]count|zero_control_event
  SCHEMA_NULL   — anything matching rate_in_count|fractional_events|estimand_mismatch|schema_
  ESTIMAND_FIX  — set estimandType to "OR" for magnitude-extreme; "MD" not auto-fixable
  REVIEW_FLAG   — review_band_concern; recorded but no field-level fix
"""
from __future__ import annotations
import json, re, sys, io
from pathlib import Path

if hasattr(sys.stdout, "buffer") and getattr(sys.stdout, "encoding", "").lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent.parent
OUT = HERE / "outputs" / "extraction_audit"
DRY = "--dry-run" in sys.argv


def categorize(category: str, reason: str, issue: str = "", evidence: str = "") -> str:
    """Map (category, reason, issue, evidence) to one of the fix taxonomies."""
    c = (category or "").lower()
    r = (reason or "").lower()
    i = (issue or "").lower()
    e = (evidence or "").lower()
    blob = " ".join([c, r, i, e])
    # Order matters — more specific patterns first
    if re.search(r'pmid|citation.?misatt|name.?collision', blob): return "PMID_NULL"
    if re.search(r'fabricat.?trial|nct.?acronym|nct.?mismatch|fake.?nct|name.?is.?nct|consecutive.?nct|trial.?identity', blob):
        return "NCT_NULL_KEY"
    if re.search(r'effect.?direction|effect.?size|fabricated.?control|fabricated.?count|zero.?control.?event|single.?arm', blob):
        return "EFFECT_NULL"
    if re.search(r'rate.?in.?count|fractional.?event|estimand.?mismatch|schema|negative.?hr', blob):
        return "SCHEMA_NULL"
    if re.search(r'magnitude.?extreme', blob): return "ESTIMAND_FIX_OR"
    if re.search(r'wrong.?direction', blob): return "EFFECT_NULL"
    if re.search(r'review.?band|review.?level', blob): return "REVIEW_FLAG"
    if re.search(r'estimandtype|estimand_type|estimand.?label|estimand.?mismatch', blob):
        return "SCHEMA_NULL"  # null event fields if estimand misaligned
    return "UNHANDLED"


# Helpers (copy from prior scripts)
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


def set_field_in_block(txt, body_start, body_end, field, value):
    body = txt[body_start:body_end]
    new_body, n = re.subn(
        r'((["\']?)' + re.escape(field) + r'\2\s*:\s*)(?:["\'][^"\']*["\']|[0-9.eE+-]+|true|false|null)(?=\s*[,}])',
        r'\1"' + value + '"', body, flags=re.IGNORECASE)
    if n == 0: return txt, False
    return txt[:body_start] + new_body + txt[body_end:], True


def null_key(txt, nct):
    nulled = f"NULLED:{nct}"
    if nulled in txt: return txt, 0
    pat = re.compile(r'(["\'])(' + re.escape(nct) + r')(\1)(\s*:)')
    new_txt, n = pat.subn(
        lambda m: f'{m.group(1)}NULLED:{m.group(2)}{m.group(3)}{m.group(4)}', txt)
    return new_txt, n


# Process unfixed HIGH findings
agg = json.loads((OUT / "8agent_aggregate.json").read_text(encoding="utf-8"))

# Skip already-fixed (from prior aggregate run)
already_done = set()
for r in agg["fixes_applied"]["details"]["pmid"]:
    if "NULLED" in r["status"]:
        already_done.add(("pmid", r["review"], r["nct"]))
for r in agg["fixes_applied"]["details"]["nct"]:
    if "NULLED" in r["status"]:
        already_done.add(("nct", r["review"], r["nct"]))

log = []
n_pmid = n_nct = n_effect = n_schema = n_estimand = 0
unhandled = []

for f in agg["findings"]:
    if f.get("severity") != "HIGH": continue
    rv = f.get("review", "")
    nct = f.get("nct", "")
    if not rv or not nct: continue
    fix_type = categorize(f.get("category"), f.get("reason"),
                            f.get("issue", ""), f.get("evidence", ""))

    html_path = HERE / f"{rv}.html"
    if not html_path.exists():
        log.append({**f, "fix_type": fix_type, "status": "FILE_MISSING"})
        continue
    txt = html_path.read_text(encoding="utf-8")

    if fix_type == "PMID_NULL":
        if ("pmid", rv, nct) in already_done:
            log.append({**f, "fix_type": fix_type, "status": "PRIOR_DONE"})
            continue
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
        if ("nct", rv, nct) in already_done:
            log.append({**f, "fix_type": fix_type, "status": "PRIOR_DONE"})
            continue
        new_txt, n = null_key(txt, nct)
        if n > 0:
            if not DRY: html_path.write_text(new_txt, encoding="utf-8")
            log.append({**f, "fix_type": fix_type, "status": "NULLED_KEY"})
            n_nct += 1
        elif f"NULLED:{nct}" in txt:
            log.append({**f, "fix_type": fix_type, "status": "ALREADY_NULLED"})
        else:
            log.append({**f, "fix_type": fix_type, "status": "NCT_NOT_FOUND"})

    elif fix_type == "EFFECT_NULL":
        block = find_block(txt, nct)
        if not block:
            log.append({**f, "fix_type": fix_type, "status": "BLOCK_NOT_FOUND"})
            continue
        _, _, bs, be = block
        changes = 0
        for fld in ("publishedHR", "hrLCI", "hrUCI"):
            new_txt, ok = null_field_in_block(txt, bs, be, fld)
            if ok:
                txt = new_txt
                block = find_block(txt, nct)
                if not block: break
                _, _, bs, be = block
                changes += 1
        if changes:
            if not DRY: html_path.write_text(txt, encoding="utf-8")
            log.append({**f, "fix_type": fix_type, "status": "NULLED_HR_CI",
                         "fields": changes})
            n_effect += 1
        else:
            log.append({**f, "fix_type": fix_type, "status": "HR_ALREADY_NULL"})

    elif fix_type == "SCHEMA_NULL":
        block = find_block(txt, nct)
        if not block:
            log.append({**f, "fix_type": fix_type, "status": "BLOCK_NOT_FOUND"})
            continue
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
            log.append({**f, "fix_type": fix_type, "status": "NULLED_EVENTS",
                         "fields": changes})
            n_schema += 1
        else:
            log.append({**f, "fix_type": fix_type, "status": "EVENTS_ALREADY_NULL"})

    elif fix_type == "ESTIMAND_FIX_OR":
        block = find_block(txt, nct)
        if not block:
            log.append({**f, "fix_type": fix_type, "status": "BLOCK_NOT_FOUND"})
            continue
        _, _, bs, be = block
        new_txt, ok = set_field_in_block(txt, bs, be, "estimandType", "OR")
        if ok:
            if not DRY: html_path.write_text(new_txt, encoding="utf-8")
            log.append({**f, "fix_type": fix_type, "status": "SET_ESTIMAND_OR"})
            n_estimand += 1
        else:
            log.append({**f, "fix_type": fix_type, "status": "ESTIMAND_NOT_FOUND"})

    elif fix_type == "REVIEW_FLAG":
        log.append({**f, "fix_type": fix_type, "status": "REVIEW_LEVEL_NO_FIELD_FIX"})

    else:
        unhandled.append({**f, "fix_type": fix_type})

out_p = OUT / "8agent_extended_fixes.json"
out_p.write_text(json.dumps({"log": log, "unhandled": unhandled}, indent=2, ensure_ascii=False), encoding="utf-8")

print(f"{'DRY-RUN ' if DRY else ''}Extended 8-agent fixes:")
print(f"  PMID nulls:     {n_pmid}")
print(f"  NCT key nulls:  {n_nct}")
print(f"  HR/CI nulls:    {n_effect}")
print(f"  Event nulls:    {n_schema}")
print(f"  Estimand→OR:    {n_estimand}")
print(f"  Unhandled:      {len(unhandled)}")
print(f"\nLog → {out_p}")

if unhandled:
    print(f"\nUnhandled findings (first 10):")
    for u in unhandled[:10]:
        print(f"  category={u.get('category','?')!r}  reason={u.get('reason','')[:80]!r}")
