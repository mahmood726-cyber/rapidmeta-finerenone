"""Audit which reviews remain unvalidated by R metafor and why.
Produces outputs/unvalidated_audit.csv + a brief stdout summary.
"""
from __future__ import annotations
import sys, io, csv, json, re
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path(__file__).resolve().parent.parent

NCT_HEAD_RE = re.compile(r"'(NCT\d{8}[A-Za-z0-9_]*)'\s*:\s*\{")
TRIAL_BINARY_RE = re.compile(
    r"tE:\s*([\d.eE+\-]+|null|None|NaN)\s*,[^{}]*?"
    r"tN:\s*([\d.eE+\-]+|null|None|NaN)\s*,[^{}]*?"
    r"cE:\s*([\d.eE+\-]+|null|None|NaN)\s*,[^{}]*?"
    r"cN:\s*([\d.eE+\-]+|null|None|NaN)",
    re.DOTALL,
)
CONT_RE = re.compile(r"type\s*:\s*['\"]?CONTINUOUS['\"]?")


def to_int(s):
    s = (s or "").strip()
    if s.lower() in ("null", "none", "nan", ""): return None
    try: return int(float(s))
    except (ValueError, TypeError): return None


def find_balanced(text, start):
    depth, i, n = 1, start + 1, len(text)
    while i < n and depth > 0:
        c = text[i]
        if c == "'":
            i += 1
            while i < n and text[i] != "'":
                i += 2 if text[i] == "\\" else 1
            i += 1
        elif c == '{': depth += 1; i += 1
        elif c == '}': depth -= 1; i += 1
        else: i += 1
    return (start, i) if depth == 0 else None


def categorise(hp: Path):
    text = hp.read_text(encoding="utf-8", errors="replace")
    n_ncts = len(set(re.findall(r"'(NCT\d{8})'\s*:", text)))
    binary_valid = 0
    continuous_valid = 0
    for m in NCT_HEAD_RE.finditer(text):
        bounds = find_balanced(text, m.end() - 1)
        if not bounds: continue
        block = text[bounds[0]:bounds[1]]
        # Binary: tE/tN/cE/cN all valid?
        bm = TRIAL_BINARY_RE.search(block)
        if bm:
            tE, tN, cE, cN = (to_int(bm.group(i)) for i in range(1, 5))
            if all(v is not None and v >= 0 for v in (tE, cE)) \
                    and all(v is not None and v > 0 for v in (tN, cN)) \
                    and tE <= tN and cE <= cN:
                binary_valid += 1
        # Continuous: any CONTINUOUS outcome?
        if CONT_RE.search(block):
            continuous_valid += 1
    return {"n_ncts": n_ncts, "binary_pool_eligible": binary_valid, "continuous_pool_eligible": continuous_valid}


def main():
    manifest = json.loads((REPO / "outputs/r_validation/index.json").read_text())
    validated = {t["topic"] for t in manifest["topics"]}
    files = sorted(REPO.glob("*_REVIEW.html"))

    rows = []
    for hp in files:
        topic = hp.stem.replace("_REVIEW", "")
        if topic in validated: continue
        c = categorise(hp)
        # Decide reason
        if c["binary_pool_eligible"] >= 2 or c["continuous_pool_eligible"] >= 2:
            reason = "EXTRACTION_REGEX_GAP"  # data is there but our regex missed it
        elif c["n_ncts"] >= 2 and c["binary_pool_eligible"] < 2 and c["continuous_pool_eligible"] < 2:
            reason = "MIXED_OR_ATYPICAL_FORMAT"  # has multiple NCTs but neither path enough
        elif c["n_ncts"] <= 1:
            reason = "K_LE_1_LEGITIMATELY_UNPOOLABLE"
        else:
            reason = "UNKNOWN"
        rows.append({
            "topic": topic, "file": hp.name,
            "n_ncts": c["n_ncts"],
            "binary_eligible": c["binary_pool_eligible"],
            "continuous_eligible": c["continuous_pool_eligible"],
            "reason": reason,
        })

    out = REPO / "outputs/unvalidated_audit.csv"
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["topic","file","n_ncts","binary_eligible","continuous_eligible","reason"])
        w.writeheader()
        for r in rows: w.writerow(r)

    by_reason = {}
    for r in rows:
        by_reason.setdefault(r["reason"], []).append(r)
    print(f"Unvalidated: {len(rows)} of {len(files)} reviews\n")
    for k in sorted(by_reason):
        items = by_reason[k]
        print(f"  {k}: {len(items)}")
        for r in items[:5]:
            print(f"    - {r['topic']} (NCTs={r['n_ncts']}, bin={r['binary_eligible']}, cont={r['continuous_eligible']})")
        if len(items) > 5: print(f"    ... and {len(items)-5} more")
    print(f"\nReport: {out}")


if __name__ == "__main__":
    main()
