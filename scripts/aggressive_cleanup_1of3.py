"""Aggressive cleanup pass: for any trial flagged HIGH-severity by even one
agent across R1+R2+R3 (1-of-3 single-lens), null the PMID to remove the
broken provenance. Conservative on LOW/MED — those stay.

Rationale: HIGH from one specialized agent + a defensible category
(fabricated-trial, impossible-pmid, pmid-unrelated, famous-trial-wrong-nct,
nct-acronym-mismatch, magnitude-extreme, single-arm-fab-HR, CI-illogical,
wrong-direction) is strong enough evidence to remove the broken attribution.

Skipped categories (less actionable):
  - acronym-mismatch (cosmetic, doesn't impact pooled estimate)
  - generic-name (extraction marker, not necessarily wrong data)
  - literature-mismatch (could be subjective)
"""
from __future__ import annotations
import json, re, sys, io
from pathlib import Path

if hasattr(sys.stdout, "buffer") and getattr(sys.stdout, "encoding", "").lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent.parent
OUT_DIR = HERE / "outputs" / "extraction_audit"
DRY = "--dry-run" in sys.argv

ACTIONABLE_CATEGORIES = {
    # identity
    "fabricated-trial", "impossible-pmid", "pmid-unrelated",
    "famous-trial-wrong-nct", "nct-acronym-mismatch", "year-nct-era-mismatch",
    "name-drug-mismatch",
    # plausibility
    "magnitude-extreme", "single-arm-fab-HR", "CI-illogical", "wrong-direction",
    "events-exceed-N", "residual-single-arm", "residual-schema-MD",
    # coherence
    "wrong-drug-class", "wrong-drug-name", "year-implausible",
}

# Collect all HIGH 1-of-3 single-lens findings across rounds
candidates = []
for fname in ["multi_agent_consensus.json",
              "multi_agent_consensus_r2.json",
              "multi_agent_consensus_r3.json"]:
    p = OUT_DIR / fname
    if not p.exists(): continue
    cs = json.loads(p.read_text(encoding="utf-8"))
    for r in cs.get("records", []):
        if len(r.get("agents_flagged", [])) != 1: continue
        if r.get("max_severity") != "HIGH": continue
        # Find the single-agent detail
        for ag, det in r.get("details", {}).items():
            cat = det.get("category", "")
            if cat in ACTIONABLE_CATEGORIES:
                candidates.append({
                    "review": r["review"], "nct": r["nct"],
                    "agent": ag, "category": cat,
                    "reason": det.get("reason", "")[:200],
                    "source_round": fname.replace("multi_agent_consensus", "R").replace(".json", "").replace("_r", ""),
                })
                break

# Dedupe (same review,nct)
seen = set()
unique = []
for c in candidates:
    key = (c["review"], c["nct"])
    if key in seen: continue
    seen.add(key); unique.append(c)

print(f"Candidates (HIGH 1-of-3 with actionable category): {len(candidates)}")
print(f"Unique (review, nct): {len(unique)}")

# Apply null_pmid
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
n_applied = 0
for c in unique:
    rv, nct = c["review"], c["nct"]
    html_path = HERE / f"{rv}.html"
    if not html_path.exists():
        log.append({**c, "status": "FILE_MISSING"})
        continue
    txt = html_path.read_text(encoding="utf-8")
    block = find_block(txt, nct)
    if not block:
        # Maybe already NULLED
        if f"NULLED:{nct}" in txt:
            log.append({**c, "status": "ALREADY_NULLED"})
        else:
            log.append({**c, "status": "BLOCK_NOT_FOUND"})
        continue
    _, _, bs, be = block
    new_txt, ok = null_field_in_block(txt, bs, be, "pmid")
    if ok:
        if not DRY: html_path.write_text(new_txt, encoding="utf-8")
        log.append({**c, "status": "NULLED_PMID"})
        n_applied += 1
    else:
        log.append({**c, "status": "PMID_ALREADY_NULL"})

out_p = OUT_DIR / "aggressive_cleanup_1of3.json"
out_p.write_text(json.dumps(log, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"\n{'DRY-RUN ' if DRY else ''}Applied: {n_applied} PMID nulls")
print(f"Log → {out_p}")

# Print breakdown
from collections import Counter
status_counts = Counter(r["status"] for r in log)
print(f"\nStatus breakdown:")
for s, n in status_counts.most_common():
    print(f"  {s}: {n}")
