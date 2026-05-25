"""Show failing color-contrast nodes from each Lighthouse report."""
import json
from pathlib import Path

LH = Path(__file__).resolve().parent.parent / "outputs" / "lighthouse"

for jf in sorted(LH.glob("*.json")):
    if jf.name == "summary.json":
        continue
    try:
        d = json.loads(jf.read_text(encoding="utf-8"))
    except Exception:
        continue
    audit = d.get("audits", {}).get("color-contrast", {})
    items = audit.get("details", {}).get("items", [])
    if not items:
        continue
    print(f"\n=== {jf.stem} ({len(items)} failing nodes) ===")
    for it in items[:8]:
        node = it.get("node", {})
        snippet = node.get("snippet", "?")[:140]
        sel = node.get("selector", "?")[:140]
        explanation = node.get("explanation", "")[:200]
        print(f"  selector: {sel}")
        print(f"  snippet:  {snippet}")
        if explanation:
            print(f"  reason:   {explanation}")
        print()
