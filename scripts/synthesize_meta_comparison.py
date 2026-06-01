"""Synthesize the published-meta-comparison workflow result into the registry +
a report. Reads the workflow task-output JSON (path as arg) and writes
outputs/published_meta_comparisons.json (merged) + prints a verdict summary
and the actionable FLAG_* / FLAG_VALUE apps.
"""
import sys, io, json
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent.parent
REG = HERE / "outputs" / "published_meta_comparisons.json"


def reldiff(a, b):
    try:
        return round(abs(a - b) / abs(b) * 100, 1)
    except (TypeError, ZeroDivisionError):
        return None


def main(out_path):
    o = json.loads(Path(out_path).read_text(encoding="utf-8"))
    res = o.get("result", {})
    rows = res.get("results", [])
    # keep existing manual entries
    reg = {"_doc": "App pool vs source-verified published meta. Workflow-generated + manual.", "verified": []}
    if REG.exists():
        try:
            old = json.loads(REG.read_text(encoding="utf-8"))
            reg["verified"] = [e for e in old.get("verified", []) if e.get("_manual")]
        except ValueError:
            pass
    from collections import Counter
    vc = Counter()
    flags = []
    for r in rows:
        vc[r.get("verdict", "?")] += 1
        if not r.get("confirmed"):
            continue
        diff = reldiff(r.get("app_est"), r.get("published_est"))
        entry = {"app": r["app"], "app_est": r.get("app_est"), "app_k": r.get("app_k"),
                 "published_est": r.get("published_est"), "published_k": r.get("k"),
                 "rel_diff_pct": diff, "verdict": r.get("verdict"),
                 "citation": r.get("citation"), "doi": r.get("doi"), "note": r.get("note", "")[:240]}
        reg["verified"].append(entry)
        if r.get("verdict") in ("FLAG_INCLUSION", "FLAG_VALUE"):
            flags.append(entry)
    REG.write_text(json.dumps(reg, indent=1), encoding="utf-8")
    print("verdict summary:", dict(vc))
    print(f"confirmed comparisons written: {sum(1 for e in reg['verified'] if not e.get('_manual'))}")
    print(f"\n=== ACTIONABLE FLAGS ({len(flags)}) — app pool diverges from / mismatches the published meta ===")
    for e in sorted(flags, key=lambda x: -(x.get("rel_diff_pct") or 0))[:60]:
        print(f"  [{e['verdict']}] {e['app'][:40]:40s} app={e['app_est']} pub={e['published_est']} "
              f"diff={e['rel_diff_pct']}%  {e['citation']}")


if __name__ == "__main__":
    main(sys.argv[1])
