"""Show failing nodes for specific a11y audits from each Lighthouse report."""
import json
import sys
from pathlib import Path

LH = Path(__file__).resolve().parent.parent / "outputs" / "lighthouse"
audits_of_interest = sys.argv[1:] or [
    "label", "heading-order", "target-size",
]

for jf in sorted(LH.glob("*.json")):
    if jf.name == "summary.json":
        continue
    try:
        d = json.loads(jf.read_text(encoding="utf-8"))
    except Exception:
        continue
    page_label = jf.stem
    for ai in audits_of_interest:
        audit = d.get("audits", {}).get(ai, {})
        if audit.get("score") is None or audit.get("score") >= 0.9:
            continue
        items = audit.get("details", {}).get("items", [])
        if not items:
            continue
        print(f"\n=== {page_label} / {ai} ({len(items)} failing) ===")
        for it in items[:6]:
            node = it.get("node", {})
            print(f"  selector: {node.get('selector', '?')[:120]}")
            print(f"  snippet:  {node.get('snippet', '?')[:140]}")
            expl = node.get("explanation", "")
            if expl:
                print(f"  reason:   {expl[:200]}")
            print()
