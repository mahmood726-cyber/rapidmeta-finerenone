"""Extract Lighthouse Perf/A11y/BP/SEO scores from outputs/lighthouse/*.json
and write a short Markdown summary."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
LH = HERE / "outputs" / "lighthouse"

cats = ["performance", "accessibility", "best-practices", "seo"]
labels = {"performance": "Perf", "accessibility": "A11y",
          "best-practices": "BP", "seo": "SEO"}

rows = []
for jf in sorted(LH.glob("*.json")):
    if jf.name == "summary.json":
        continue
    d = json.loads(jf.read_text(encoding="utf-8"))
    scores = {c: int(round((d.get("categories", {}).get(c, {}).get("score") or 0) * 100))
              for c in cats}
    rows.append((jf.stem, scores))

print(f"{'page':<40} | " + " | ".join(f"{labels[c]:>4}" for c in cats))
print("-" * 75)
for page, s in rows:
    print(f"{page:<40} | " + " | ".join(f"{s[c]:>4}" for c in cats))

# Per-page top failing audits
print("\nTop failing audits per page (score < 0.9):")
for jf in sorted(LH.glob("*.json")):
    if jf.name == "summary.json":
        continue
    d = json.loads(jf.read_text(encoding="utf-8"))
    fails = []
    for ai, audit in d.get("audits", {}).items():
        sc = audit.get("score")
        if sc is None or sc >= 0.9:
            continue
        # Skip 'metrics-passed' style soft audits
        if audit.get("scoreDisplayMode") in ("informative", "notApplicable", "manual"):
            continue
        fails.append((sc, audit.get("title", ai)))
    fails.sort()
    if fails:
        print(f"\n  {jf.stem}:")
        for sc, title in fails[:6]:
            print(f"    {sc:.2f}  {title[:80]}")
