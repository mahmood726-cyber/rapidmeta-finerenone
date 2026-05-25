"""Show total-byte-weight detail (which resources are heaviest)."""
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
    a = d.get("audits", {}).get("total-byte-weight", {})
    items = a.get("details", {}).get("items", [])
    if not items:
        continue
    print(f"\n=== {jf.stem} ===  total transfer: {a.get('numericValue', 0)/1024:.0f} KB")
    for it in items[:8]:
        url = it.get("url", "?")
        size = it.get("totalBytes", 0)
        print(f"  {size/1024:>7.1f} KB  {url[-100:]}")
