"""Extract all unique fg/bg color combinations failing WCAG AA across the
Lighthouse reports, ranked by frequency."""
import json
import re
from pathlib import Path
from collections import Counter

LH = Path(__file__).resolve().parent.parent / "outputs" / "lighthouse"
COLOR_RE = re.compile(
    r"foreground color:\s*(#[0-9a-fA-F]+)[^,]*,\s*background color:\s*(#[0-9a-fA-F]+)"
)

combos: Counter = Counter()
for jf in sorted(LH.glob("*.json")):
    if jf.name == "summary.json":
        continue
    try:
        d = json.loads(jf.read_text(encoding="utf-8"))
    except Exception:
        continue
    audit = d.get("audits", {}).get("color-contrast", {})
    for it in audit.get("details", {}).get("items", []):
        explanation = it.get("node", {}).get("explanation", "")
        m = COLOR_RE.search(explanation)
        if m:
            combos[(m.group(1).lower(), m.group(2).lower())] += 1

print(f"{'fg':<10} {'bg':<10} {'n':>4}")
print("-" * 28)
for (fg, bg), n in combos.most_common(15):
    print(f"{fg:<10} {bg:<10} {n:>4}")
