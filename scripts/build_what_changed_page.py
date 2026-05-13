"""Build a 'what changed' summary page showing per-round fix counts and methodology.

Output: what_changed.html (single page, no external CDN)
"""
from __future__ import annotations
import json, sys, io
from pathlib import Path
from collections import Counter

if hasattr(sys.stdout, "buffer") and getattr(sys.stdout, "encoding", "").lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent.parent
OUT = HERE / "outputs" / "extraction_audit"

# Hand-curated round summary (matches commit history)
ROUNDS = [
    {"id": "R1-init", "label": "Initial 12-method audit + 8-agent scan + deterministic fixes",
     "fixes": 768, "sources": ["deterministic", "agent"]},
    {"id": "R1-multi", "label": "R1 multi-agent (3 lenses, 77 trials)",
     "fixes": 11, "sources": ["multi-agent"]},
    {"id": "R2", "label": "Multi-agent R2 (249 trials, 3 lenses)",
     "fixes": 204, "sources": ["multi-agent"]},
    {"id": "R3", "label": "Multi-agent R3 (184 trials, fab-review deep audit)",
     "fixes": 230, "sources": ["multi-agent", "quarantines"]},
    {"id": "R4", "label": "R4 + risk classifier + aggressive cleanup",
     "fixes": 38, "sources": ["multi-agent", "classifier"]},
    {"id": "R5", "label": "R5 fidelity vs published landmark trials (16 NCTs)",
     "fixes": 1, "sources": ["landmark trials", "calibration"]},
    {"id": "R5b", "label": "R5b pool reproduction vs 20 published reference MAs",
     "fixes": 0, "sources": ["published MAs", "calibration"]},
    {"id": "8-agent", "label": "8-agent blinded TruthCert audit (157 reviews, 1,100 trials)",
     "fixes": 57, "sources": ["8 blinded agents", "TruthCert HMAC"]},
    {"id": "8-agent-ext", "label": "8-agent extended fixer + MED + carryforward",
     "fixes": 53, "sources": ["multi-agent"]},
    {"id": "R6abc", "label": "Internal-consistency suite (9 checks: direction, copy-paste, baseline-N…)",
     "fixes": 264, "sources": ["internal"]},
    {"id": "R7", "label": "AACT cross-verify (LOW+MANUAL band, 1,063 trials)",
     "fixes": 100, "sources": ["AACT 2026-04-12"]},
    {"id": "R7c", "label": "AACT verify on OK band (248 trustworthy reviews)",
     "fixes": 139, "sources": ["AACT"]},
    {"id": "R8", "label": "PMID-year era heuristic (PubMed indexing rate)",
     "fixes": 31, "sources": ["PubMed indexing"]},
    {"id": "R9", "label": "AACT baseline_counts per-arm enrollment check",
     "fixes": 110, "sources": ["AACT baseline_counts"]},
    {"id": "R10", "label": "AACT outcome_measurements event-count cross-check",
     "fixes": 554, "sources": ["AACT outcome_measurements"]},
    {"id": "R19", "label": "AACT primary_completion_date vs extracted year",
     "fixes": 197, "sources": ["AACT completion dates"]},
    {"id": "R20", "label": "Stress-test (re-run R5+R5b on cleaned corpus)",
     "fixes": 0, "sources": ["regression test"]},
    {"id": "R22", "label": "MeSH-anchored review-topic vs AACT-conditions",
     "fixes": 422, "sources": ["AACT", "curated MeSH dict"]},
    {"id": "R23", "label": "Trial acronym vs AACT brief_title + id_information",
     "fixes": 249, "sources": ["AACT id_information"]},
    {"id": "Path-A", "label": "PMC OAI full-text evidence injection (29.8% PMC OA hit rate)",
     "fixes": 12, "sources": ["PMC OAI", "NCBI E-utilities"]},
    {"id": "R24", "label": "AACT design_outcomes type classification (flag-only)",
     "fixes_flagged": 225, "fixes": 0, "sources": ["AACT design_outcomes"]},
    {"id": "R24b", "label": "PubMed-directed R24 estimand auto-fix (conservative gate)",
     "fixes": 10, "sources": ["PubMed abstracts"]},
    {"id": "R30", "label": "Fully-null trial-row cleanup",
     "fixes": 0, "sources": ["internal"]},
    {"id": "R31-33", "label": "Polish suite (Benford after cleanup + decimal precision + confidence score)",
     "fixes": 0, "sources": ["audit metrics"]},
    {"id": "R25-RW", "label": "Retraction Watch DB cross-check (Crossref/GitLab, 70,147 retractions)",
     "fixes": 0, "sources": ["Retraction Watch"]},
]


# Load classifier for current band counts
scores = json.loads((OUT / "fabrication_risk_scores.json").read_text(encoding="utf-8"))
bc = Counter(r["classification"] for r in scores)
total_fixes = sum(r.get("fixes", 0) for r in ROUNDS)
total_flagged = sum(r.get("fixes_flagged", 0) for r in ROUNDS)

# Identity-score buckets
id_scores = json.loads((OUT / "r33_trial_identity_score.json").read_text(encoding="utf-8"))
id_buckets = id_scores.get("buckets", {})


def round_card(r):
    fixes = r.get("fixes", 0)
    flagged = r.get("fixes_flagged", 0)
    label = r["label"]
    rid = r["id"]
    sources = ", ".join(r.get("sources", []))
    badge_color = "#16a34a" if fixes > 0 else "#475569"
    return f'''<div style="background:#1e293b;border-left:3px solid {badge_color};padding:12px 16px;margin-bottom:10px;border-radius:0 6px 6px 0;">
  <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:8px;">
    <div>
      <strong style="color:#7dd3fc;font-family:JetBrains Mono,monospace;font-size:13px;">{rid}</strong>
      <span style="color:#e2e8f0;margin-left:8px;">{label}</span>
    </div>
    <div style="text-align:right;">
      {f'<span style="background:#16a34a;color:#fff;padding:2px 10px;border-radius:4px;font-size:11px;font-weight:600;">{fixes} fixes</span>' if fixes else ''}
      {f'<span style="background:#ca8a04;color:#fff;padding:2px 10px;border-radius:4px;font-size:11px;font-weight:600;margin-left:6px;">{flagged} flagged</span>' if flagged else ''}
    </div>
  </div>
  <div style="margin-top:6px;color:#94a3b8;font-size:11px;">Sources: {sources}</div>
</div>'''


html = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>What changed — rapidmeta-finerenone integrity audit</title>
<style>
  body {{ margin:0; padding:0; background:#0f172a; color:#e2e8f0; font-family:system-ui,-apple-system,sans-serif; line-height:1.55; }}
  header {{ padding:24px; background:#0a0f1f; border-bottom:1px solid #1f2a44; }}
  h1 {{ margin:0 0 8px 0; font-size:22px; }}
  h2 {{ font-size:16px; color:#7dd3fc; margin-top:0; }}
  main {{ padding:24px; max-width:1100px; margin:0 auto; }}
  section {{ margin-bottom:32px; }}
  .top-stats {{ display:flex; gap:14px; flex-wrap:wrap; margin:14px 0 0; }}
  .stat {{ background:#1e293b; padding:12px 16px; border-radius:6px; min-width:140px; }}
  .stat .num {{ font-size:24px; font-weight:600; color:#7dd3fc; }}
  .stat .lab {{ font-size:11px; color:#94a3b8; text-transform:uppercase; letter-spacing:0.05em; }}
  a {{ color:#7dd3fc; }}
  footer {{ padding:16px 24px; background:#0a0f1f; border-top:1px solid #1f2a44; color:#94a3b8; font-size:11px; }}
</style>
</head>
<body>
<header>
<h1>What changed — rapidmeta-finerenone data-integrity audit</h1>
<div style="color:#94a3b8;font-size:13px;">
  Per-round summary of the automated integrity sweep · 15+ rounds · 0 human-reviewer hours ·
  <a href="index.html">← back to review index</a>
</div>
<div class="top-stats">
  <div class="stat"><div class="num">{total_fixes:,}</div><div class="lab">Total fixes</div></div>
  <div class="stat"><div class="num">{len(ROUNDS)}</div><div class="lab">Audit rounds</div></div>
  <div class="stat"><div class="num">{total_flagged}</div><div class="lab">Flagged (no auto-fix)</div></div>
  <div class="stat"><div class="num">{len(scores)}</div><div class="lab">Reviews audited</div></div>
</div>
</header>

<main>
<section>
<h2>Current state by classification band</h2>
<div class="top-stats">
  <div class="stat" style="border-left:3px solid #16a34a;">
    <div class="num">{bc.get("OK",0)}</div><div class="lab">Trustworthy (&lt;0.30)</div>
  </div>
  <div class="stat" style="border-left:3px solid #ca8a04;">
    <div class="num">{bc.get("LOW_CONCERN",0)}</div><div class="lab">Low concern (0.30-0.50)</div>
  </div>
  <div class="stat" style="border-left:3px solid #ea580c;">
    <div class="num">{bc.get("MANUAL_REVIEW",0)}</div><div class="lab">Manual review (0.50-0.70)</div>
  </div>
  <div class="stat" style="border-left:3px solid #7f1d1d;">
    <div class="num">{bc.get("QUARANTINE",0)}</div><div class="lab">Quarantined (≥0.70)</div>
  </div>
</div>
</section>

<section>
<h2>Per-trial identity-confidence score (R33 — 1,655 trials)</h2>
<p style="color:#94a3b8;font-size:12px;">Composite of 25%·NCT-in-AACT + 20%·drug-in-AACT-intvs + 15%·PMID-present + 10%·year + 10%·name + 20%·evidence[]-non-empty.</p>
<div class="top-stats">
  <div class="stat" style="border-left:3px solid #16a34a;">
    <div class="num">{id_buckets.get("80-100 (excellent)",0)}</div><div class="lab">Excellent (80-100)</div>
  </div>
  <div class="stat" style="border-left:3px solid #65a30d;">
    <div class="num">{id_buckets.get("60-79 (good)",0)}</div><div class="lab">Good (60-79)</div>
  </div>
  <div class="stat" style="border-left:3px solid #ca8a04;">
    <div class="num">{id_buckets.get("40-59 (caution)",0)}</div><div class="lab">Caution (40-59)</div>
  </div>
  <div class="stat" style="border-left:3px solid #ea580c;">
    <div class="num">{id_buckets.get("20-39 (poor)",0)}</div><div class="lab">Poor (20-39)</div>
  </div>
  <div class="stat" style="border-left:3px solid #7f1d1d;">
    <div class="num">{id_buckets.get("0-19 (bad)",0)}</div><div class="lab">Bad (0-19)</div>
  </div>
</div>
</section>

<section>
<h2>Audit rounds (chronological)</h2>
{chr(10).join(round_card(r) for r in ROUNDS)}
</section>

<section>
<h2>Ground-truth sources</h2>
<ul style="color:#cbd5e1;font-size:13px;line-height:1.8;">
  <li><strong>AACT 2026-04-12</strong> — Clinical Trials Transformation Initiative pipe-delimited snapshot (studies, conditions, interventions, baseline_counts, outcome_measurements, design_outcomes, id_information, primary_completion_date)</li>
  <li><strong>PubMed E-utilities</strong> — NCBI metadata (1,190 cached abstracts) + idconv API (PMID↔PMC mapping)</li>
  <li><strong>PMC OAI full-text</strong> — NCBI PubMed Central full-text XML (60 papers retrieved, 12 evidence entries injected at ≥3 number matches)</li>
  <li><strong>Retraction Watch (Crossref/GitLab)</strong> — 70,147 retractions cross-checked; 0 retracted papers in corpus</li>
  <li><strong>Published landmark trials</strong> — NEJM/Lancet primary publications (16 trials, 34 occurrences, 97% byte-exact)</li>
  <li><strong>Published reference MAs</strong> — 20 published meta-analyses, REML+HKSJ pool reproduction (93% within Cochrane floor)</li>
  <li><strong>Multi-agent consensus</strong> — 3-lens ≥2-of-3 consensus (R1-R4) + 8-agent blinded TruthCert HMAC (157 reviews)</li>
  <li><strong>Internal cross-consistency</strong> — direction-inconsistent, copy-paste arms, NCT-era, PMID-cross-NCT, baseline-N mismatch, CI-outside-HR, year-inconsistent-across-reviews, MeSH-anchored topic matching</li>
</ul>
</section>

<section>
<h2>Files</h2>
<ul style="color:#cbd5e1;font-size:13px;">
  <li><a href="outputs/extraction_audit/FINAL_INTEGRITY_REPORT_V2.md">FINAL_INTEGRITY_REPORT_V2.md</a> — 232-line consolidated methodology</li>
  <li><a href="outputs/extraction_audit/fabrication_risk_table.csv">fabrication_risk_table.csv</a> — per-review classifier scores</li>
  <li><a href="outputs/extraction_audit/truthcert/">truthcert/</a> — 409 HMAC-SHA256 signed per-review manifests</li>
  <li><code>scripts/</code> — every round's auto-fix script (replayable)</li>
</ul>
</section>
</main>

<footer>
Generated by <code>scripts/build_what_changed_page.py</code>. Per AACT attribution: AACT 2026-04-12 (CTTI).
Per PubMed attribution: NCBI E-utilities + PMC OAI. Per Retraction Watch attribution: Crossref-hosted at gitlab.com/crossref/retraction-watch-data.
</footer>
</body>
</html>
'''

(HERE / "what_changed.html").write_text(html, encoding="utf-8")
print(f"Wrote what_changed.html (total fixes: {total_fixes})")
print(f"Total flagged (no fix): {total_flagged}")
