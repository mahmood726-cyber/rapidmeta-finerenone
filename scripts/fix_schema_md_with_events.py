"""Deterministic fix: for trials with estimandType='MD' AND event counts
populated, null the event-count fields (they don't apply to continuous
outcomes). MD operates on means, not events — when both are present, the
event counts are extraction noise that confuse downstream pooling.

Why this is safe: the publishedHR field already holds the MD value (the
field name is legacy but value is correct per estimandType). Nulling
tE/tN/cE/cN preserves the MD pool while removing the schema violation
that the 12-method audit (M01) and Agent 2 flag.
"""
from __future__ import annotations
import json, re, sys, io
from pathlib import Path

if hasattr(sys.stdout, "buffer") and getattr(sys.stdout, "encoding", "").lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent.parent
DATA = HERE / "outputs" / "extraction_audit" / "data"
DRY = "--dry-run" in sys.argv


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


log = []
total_changed = 0
for json_p in sorted(DATA.glob("*.json")):
    if json_p.name.startswith("_"): continue
    rv = json_p.stem
    try: d = json.loads(json_p.read_text(encoding="utf-8"))
    except: continue
    rd = d.get("realData") or {}
    if not isinstance(rd, dict): continue
    targets = []
    for nct, t in rd.items():
        if not isinstance(t, dict): continue
        if nct.startswith("NULLED:"): continue
        et = str(t.get("estimandType") or "").upper()
        if et != "MD": continue
        has_events = any(t.get(k) not in (None, 0) for k in ("tE", "cE"))
        if has_events:
            targets.append(nct)
    if not targets: continue
    html_path = HERE / f"{rv}.html"
    if not html_path.exists(): continue
    txt = html_path.read_text(encoding="utf-8")
    changes = 0
    for nct in targets:
        block = find_block(txt, nct)
        if not block: continue
        _, _, bs, be = block
        # Null all four event-count fields
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
        log.append({"review": rv, "ncts_fixed": targets})
        total_changed += changes

out_p = HERE / "outputs" / "extraction_audit" / "schema_md_with_events_fixed.json"
out_p.write_text(json.dumps(log, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"{'DRY-RUN ' if DRY else ''}Schema-MD-with-events fix: {total_changed} trials across {len(log)} reviews")
print(f"Log → {out_p}")
