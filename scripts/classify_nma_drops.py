"""Classify the 32 TRIALS_DROPPED files into:

  DEMOTE      — intersection(realData, NMA_CONFIG NCTs) < 3
                The NMA engine has too few usable trials, demote to pairwise.

  PRUNE       — intersection >= 3 but NMA_CONFIG has phantom NCTs not in
                realData (declared trials never extracted). Drop the phantoms
                from NMA_CONFIG but keep the network structure.

  EXTEND      — intersection covers all of NMA_CONFIG NCTs but realData has
                additional trials not in any comparison. Extend NMA_CONFIG
                to add them as new edges.

  COMPLEX     — both phantoms AND extras (e.g., dropped > 0 AND missing-from-rd > 0).
                Manual review needed.

Reads outputs/nma_config_audit.csv (must run scripts/audit_nma_config.py first
if stale). Writes outputs/nma_classification.csv with the recommendation
column for each file.
"""
from __future__ import annotations
import sys, io, csv, re, json
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path("C:/Projects/Finrenone")
OUT_CSV = REPO / "outputs" / "nma_classification.csv"

NMA_CONFIG_RE = re.compile(r'const\s+NMA_CONFIG\s*=\s*(\{[\s\S]*?\});', re.MULTILINE)
REALDATA_NCT_RE = re.compile(r"'(NCT\d+)'\s*:\s*\{")


def parse_config(text):
    m = NMA_CONFIG_RE.search(text)
    if not m:
        return None
    raw = m.group(1)
    try:
        cfg = json.loads(raw)
    except json.JSONDecodeError:
        return None
    cfg_ncts = set()
    for c in cfg.get("comparisons", []) or []:
        for t in c.get("trials", []) or []:
            if isinstance(t, str) and t.startswith("NCT"):
                cfg_ncts.add(t)
    return {
        "treatments": cfg.get("treatments", []),
        "cfg_ncts": cfg_ncts,
    }


def realdata_ncts(text):
    return set(REALDATA_NCT_RE.findall(text))


def classify(rd, cfg):
    if not cfg:
        return "NO_CONFIG"
    intersect = rd & cfg["cfg_ncts"]
    in_cfg_only = cfg["cfg_ncts"] - rd  # phantoms (declared but not extracted)
    in_rd_only = rd - cfg["cfg_ncts"]   # extras (extracted but not in any cmp)
    n_treat = len(cfg["treatments"])

    if n_treat < 3:
        return "DEMOTE_DEGENERATE"
    if len(intersect) < 3:
        return "DEMOTE_NO_OVERLAP"
    if in_cfg_only and not in_rd_only:
        return "PRUNE_PHANTOMS"
    if in_rd_only and not in_cfg_only:
        return "EXTEND_EXTRAS"
    if in_cfg_only and in_rd_only:
        return "COMPLEX"
    return "OK"


def main():
    files = sorted(REPO.glob("*_NMA_REVIEW.html"))
    rows = []
    for hp in files:
        text = hp.read_text(encoding="utf-8", errors="replace")
        rd = realdata_ncts(text)
        cfg = parse_config(text)
        action = classify(rd, cfg)
        if not cfg:
            rows.append({
                "file": hp.name, "n_treat": 0, "n_rd": len(rd),
                "n_cfg": 0, "intersection": 0, "phantoms": 0, "extras": 0,
                "action": action,
            })
            continue
        intersect = rd & cfg["cfg_ncts"]
        rows.append({
            "file": hp.name,
            "n_treat": len(cfg["treatments"]),
            "n_rd": len(rd),
            "n_cfg": len(cfg["cfg_ncts"]),
            "intersection": len(intersect),
            "phantoms": len(cfg["cfg_ncts"] - rd),
            "extras": len(rd - cfg["cfg_ncts"]),
            "action": action,
        })

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    by_a = {}
    for r in rows:
        by_a[r["action"]] = by_a.get(r["action"], 0) + 1
    print(f"=== Classification of {len(rows)} *_NMA_REVIEW.html files ===")
    for k, n in sorted(by_a.items(), key=lambda x: -x[1]):
        print(f"  {k:25s} {n}")

    for action in ["DEMOTE_NO_OVERLAP", "DEMOTE_DEGENERATE",
                   "PRUNE_PHANTOMS", "EXTEND_EXTRAS", "COMPLEX"]:
        sample = [r for r in rows if r["action"] == action]
        if not sample:
            continue
        print(f"\n=== {action} ({len(sample)} files) ===")
        for r in sample[:30]:
            print(f"  {r['file'][:48]:48s} treat={r['n_treat']} rd={r['n_rd']} cfg={r['n_cfg']} ∩={r['intersection']} phantoms={r['phantoms']} extras={r['extras']}")

    print(f"\nWritten: {OUT_CSV}")


if __name__ == "__main__":
    main()
