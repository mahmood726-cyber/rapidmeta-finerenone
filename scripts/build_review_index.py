"""Path i — Build a single-page public review index.

Reads outputs/extraction_audit/fabrication_risk_scores.json + per-review
metadata and renders ALL 411 reviews into a filterable HTML index at
index.html (overwrites any existing).

Features:
  - Sort/filter by classification band + score
  - Search box (filter by review name)
  - Color-coded badges matching the in-review classification
  - Direct link to each review HTML

Self-contained, no external CDN. Works on GitHub Pages.
"""
from __future__ import annotations
import json, sys, io
from pathlib import Path

if hasattr(sys.stdout, "buffer") and getattr(sys.stdout, "encoding", "").lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent.parent
OUT = HERE / "outputs" / "extraction_audit"
scores = json.loads((OUT / "fabrication_risk_scores.json").read_text(encoding="utf-8"))
scores.sort(key=lambda r: (r["score"], r["review"]))

BAND_COLORS = {
    "OK":           {"bg": "#16a34a", "border": "#15803d"},
    "LOW_CONCERN":  {"bg": "#ca8a04", "border": "#a16207"},
    "MANUAL_REVIEW":{"bg": "#ea580c", "border": "#c2410c"},
    "QUARANTINE":   {"bg": "#7f1d1d", "border": "#fbbf24"},
}
BAND_LABELS = {
    "OK": "TRUSTWORTHY",
    "LOW_CONCERN": "LOW CONCERN",
    "MANUAL_REVIEW": "MANUAL REVIEW",
    "QUARANTINE": "QUARANTINED",
}

from collections import Counter
band_counts = Counter(r["classification"] for r in scores)

# Track which full-dashboard files get an inline link, so any full dashboard
# with no matching audit-score row can still be surfaced (additively) in a
# footer block by its own authoritative filename (zero mislink risk).
import glob as _glob
_linked_full = set()

# Build review rows
rows = []
for r in scores:
    cls = r["classification"]
    colors = BAND_COLORS[cls]
    label = BAND_LABELS[cls]
    score = r["score"]
    rv = r["review"]
    n = r["n_trials"]
    flag_q = "★ banner" if r["already_quarantined"] else ""
    # Additive: link the full-functionality interactive dashboard when one
    # exists for this review. The audit `review` name maps to the dashboard
    # file by a DETERMINISTIC transform (no fuzzy matching → no mislink):
    #   audit "X_AUTO_REVIEW"  -> dashboard "X_AUTO_FULL_REVIEW.html"
    #   audit "X" (==stem)     -> dashboard "X_FULL_REVIEW.html"
    # Only an exact-filename file-exists check is used; nothing is removed and
    # the lightweight <rv>.html link is untouched.
    full_link = ""
    _cands = [f"{rv}_FULL_REVIEW.html"]
    if rv.endswith("_REVIEW"):
        _cands.append(f"{rv[:-len('_REVIEW')]}_FULL_REVIEW.html")
    for _fc in _cands:
        if (HERE / _fc).exists():
            _linked_full.add(_fc)
            full_link = (f'<a href="{_fc}" title="Full interactive '
                         f'RapidMeta dashboard (editable extraction, screening, RoB, '
                         f'live re-pool, WebR)" style="color:#34d399;text-decoration:none;'
                         f'font-size:11px;margin-left:10px;">⧉ full dashboard</a>')
            break
    rows.append(f'''<tr data-band="{cls}" data-name="{rv.lower()}" data-score="{score:.3f}">
    <td style="padding:6px 10px;border-bottom:1px solid #1f2a44;">
      <span style="display:inline-block;background:{colors["bg"]};color:#fff;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:600;letter-spacing:0.04em;border:1px solid {colors["border"]};">{label}</span>
    </td>
    <td style="padding:6px 10px;border-bottom:1px solid #1f2a44;color:#cbd5e1;font-family:JetBrains Mono,monospace;font-size:11px;">{score:.3f}</td>
    <td style="padding:6px 10px;border-bottom:1px solid #1f2a44;color:#94a3b8;text-align:right;">{n}</td>
    <td style="padding:6px 10px;border-bottom:1px solid #1f2a44;">
      <a href="{rv}.html" style="color:#7dd3fc;text-decoration:none;font-family:JetBrains Mono,monospace;font-size:12px;">{rv}</a>
      {f'<span style="color:#fbbf24;font-size:10px;margin-left:8px;">★ banner</span>' if r["already_quarantined"] else ''}{full_link}
    </td>
  </tr>''')

# Additive: any full dashboard with no matching audit-score row is still
# surfaced here, linked by its own authoritative filename (zero mislink).
_all_full = sorted(p.name for p in HERE.glob("*_FULL_REVIEW.html"))
_unindexed = [f for f in _all_full if f not in _linked_full]
if _unindexed:
    _items = "\n".join(
        f'<li style="margin:2px 0;"><a href="{f}" style="color:#34d399;'
        f'font-family:JetBrains Mono,monospace;font-size:12px;text-decoration:none;">'
        f'⧉ {f[:-len("_FULL_REVIEW.html")]}</a></li>' for f in _unindexed)
    _extra_block = (
        f'<section style="padding:16px 24px;background:#0a0f1f;border-top:1px solid #1f2a44;">'
        f'<div style="color:#94a3b8;font-size:12px;margin-bottom:8px;">'
        f'<strong>{len(_unindexed)} additional full interactive dashboards</strong> '
        f'(no audit-score row yet — reachable directly):</div>'
        f'<ul style="columns:3;-webkit-columns:3;list-style:none;padding:0;margin:0;">{_items}</ul></section>')
else:
    _extra_block = ""

html = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>rapidmeta-finerenone — Data-integrity index</title>
<meta name="description" content="Audit-classified index of {len(scores)} meta-analysis reviews, with per-review fabrication-risk badges.">
<style>
  body {{ margin:0; padding:0; background:#0f172a; color:#e2e8f0; font-family:system-ui,-apple-system,sans-serif; line-height:1.5; }}
  header {{ padding:24px; background:#0a0f1f; border-bottom:1px solid #1f2a44; }}
  h1 {{ margin:0 0 8px 0; font-size:22px; }}
  .summary-row {{ display:flex; gap:14px; flex-wrap:wrap; margin:14px 0 0; }}
  .summary-card {{ padding:10px 14px; background:#1e293b; border-radius:6px; min-width:140px; }}
  .summary-card .num {{ font-size:24px; font-weight:600; }}
  .summary-card .label {{ font-size:11px; color:#94a3b8; text-transform:uppercase; letter-spacing:0.05em; }}
  .controls {{ padding:16px 24px; background:#0a0f1f; border-bottom:1px solid #1f2a44; display:flex; gap:12px; align-items:center; flex-wrap:wrap; }}
  .controls input, .controls select {{ background:#0f172a; border:1px solid #334155; color:#e2e8f0; padding:6px 10px; border-radius:4px; font-size:13px; }}
  .controls input {{ flex:1; min-width:200px; max-width:400px; }}
  table {{ width:100%; border-collapse:collapse; background:#0f172a; }}
  thead th {{ position:sticky; top:0; background:#0a0f1f; padding:10px; text-align:left; font-size:11px; color:#94a3b8; text-transform:uppercase; letter-spacing:0.05em; border-bottom:1px solid #1f2a44; }}
  footer {{ padding:16px 24px; background:#0a0f1f; border-top:1px solid #1f2a44; color:#94a3b8; font-size:11px; }}
  a {{ color:#7dd3fc; }}
</style>
</head>
<body>
<header>
<h1>rapidmeta-finerenone — Data-integrity index</h1>
<div style="color:#94a3b8;font-size:13px;">
  {len(scores)} meta-analysis reviews · audit-classified across 15 rounds (deterministic + multi-agent + AACT + PubMed + PMC)
  · <a href="what_changed.html">what changed →</a>
  · <a href="outputs/extraction_audit/FINAL_INTEGRITY_REPORT_V2.md">methodology (FINAL_INTEGRITY_REPORT_V2.md)</a>
</div>
<div style="color:#34d399;font-size:12px;margin-top:6px;">
  <strong>⧉ full dashboard</strong> = full-functionality interactive RapidMeta (editable extraction, screening, RoB, live re-pool, WebR) — shown next to reviews that have one.
</div>
<div class="summary-row">
  <div class="summary-card" style="border-left:3px solid {BAND_COLORS["OK"]["bg"]};">
    <div class="num">{band_counts.get("OK",0)}</div>
    <div class="label">Trustworthy</div>
  </div>
  <div class="summary-card" style="border-left:3px solid {BAND_COLORS["LOW_CONCERN"]["bg"]};">
    <div class="num">{band_counts.get("LOW_CONCERN",0)}</div>
    <div class="label">Low concern</div>
  </div>
  <div class="summary-card" style="border-left:3px solid {BAND_COLORS["MANUAL_REVIEW"]["bg"]};">
    <div class="num">{band_counts.get("MANUAL_REVIEW",0)}</div>
    <div class="label">Manual review</div>
  </div>
  <div class="summary-card" style="border-left:3px solid {BAND_COLORS["QUARANTINE"]["bg"]};">
    <div class="num">{band_counts.get("QUARANTINE",0)}</div>
    <div class="label">Quarantined</div>
  </div>
</div>
</header>

<div class="controls">
  <input id="search" type="text" placeholder="Filter by review name…" oninput="filterRows()">
  <select id="band-filter" onchange="filterRows()">
    <option value="">All bands</option>
    <option value="OK">Trustworthy only</option>
    <option value="LOW_CONCERN">Low concern only</option>
    <option value="MANUAL_REVIEW">Manual review only</option>
    <option value="QUARANTINE">Quarantined only</option>
  </select>
  <select id="sort-key" onchange="sortRows()">
    <option value="score-asc">Sort: score ascending</option>
    <option value="score-desc">Sort: score descending</option>
    <option value="name-asc">Sort: name A-Z</option>
  </select>
  <span id="count" style="color:#94a3b8;font-size:11px;margin-left:auto;"></span>
</div>

<table>
<thead>
<tr>
  <th>Band</th>
  <th>Risk score</th>
  <th style="text-align:right;">Trials</th>
  <th>Review</th>
</tr>
</thead>
<tbody id="rows">
{chr(10).join(rows)}
</tbody>
</table>

{_extra_block}

<footer>
Generated by <code>scripts/build_review_index.py</code> from
<code>outputs/extraction_audit/fabrication_risk_scores.json</code>.
For methodology and per-round logs, see
<a href="outputs/extraction_audit/FINAL_INTEGRITY_REPORT_V2.md">FINAL_INTEGRITY_REPORT_V2.md</a>.
Per AACT attribution: AACT 2026-04-12 (CTTI). Per PubMed attribution: NCBI E-utilities + PMC OAI.
</footer>

<script>
function filterRows() {{
  const q = document.getElementById('search').value.toLowerCase();
  const b = document.getElementById('band-filter').value;
  const rows = document.querySelectorAll('#rows tr');
  let n = 0;
  rows.forEach(r => {{
    const okName = !q || r.dataset.name.includes(q);
    const okBand = !b || r.dataset.band === b;
    const v = okName && okBand;
    r.style.display = v ? '' : 'none';
    if (v) n++;
  }});
  document.getElementById('count').textContent = n + ' visible';
}}
function sortRows() {{
  const k = document.getElementById('sort-key').value;
  const tbody = document.getElementById('rows');
  const rows = Array.from(tbody.querySelectorAll('tr'));
  rows.sort((a, b) => {{
    if (k === 'score-asc') return parseFloat(a.dataset.score) - parseFloat(b.dataset.score);
    if (k === 'score-desc') return parseFloat(b.dataset.score) - parseFloat(a.dataset.score);
    if (k === 'name-asc') return a.dataset.name.localeCompare(b.dataset.name);
  }});
  rows.forEach(r => tbody.appendChild(r));
}}
filterRows();
</script>
</body>
</html>
'''

(HERE / "audit_table.html").write_text(html, encoding="utf-8")
print(f"Wrote audit_table.html with {len(scores)} reviews")
print(f"Bands: {dict(band_counts)}")
