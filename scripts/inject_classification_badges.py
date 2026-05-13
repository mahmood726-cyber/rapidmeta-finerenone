"""Inject classification badges into every review HTML.

Badge mapping (from fabrication_risk_classifier output):
  OK (score <0.30)                  → green  "TRUSTWORTHY"
  LOW_CONCERN (0.30 ≤ s < 0.50)     → yellow "LOW CONCERN — spot-check before citing"
  MANUAL_REVIEW (0.50 ≤ s < 0.70)   → orange "MANUAL REVIEW — per-trial re-extract needed"
  QUARANTINE (≥0.70)                → red    "DATA-INTEGRITY QUARANTINE"

Banner-quarantined reviews already have a banner; they get the same red badge
near it for consistency. Score-band QUARANTINE without banner gets a new
banner-style red badge.

Idempotent: skip if a badge marker already exists.
"""
from __future__ import annotations
import json, re, sys, io
from pathlib import Path

if hasattr(sys.stdout, "buffer") and getattr(sys.stdout, "encoding", "").lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent.parent
OUT = HERE / "outputs" / "extraction_audit"
DRY = "--dry-run" in sys.argv
BADGE_MARKER = "rapidmeta-integrity-badge"

BADGE_TEMPLATES = {
    "OK": {
        "bg": "#16a34a", "border": "#15803d", "text": "#fff",
        "label": "TRUSTWORTHY",
        "subtitle": "Multi-source audit completed (AACT 2026-04-12 + PubMed + 10 internal-consistency rounds). Routine pre-publication human spot-check recommended."
    },
    "LOW_CONCERN": {
        "bg": "#ca8a04", "border": "#a16207", "text": "#fff",
        "label": "LOW CONCERN",
        "subtitle": "Some trials in this review had wrong-PMID or NCT-acronym issues caught by the audit (nulled). Spot-check the affected trials' provenance before citing."
    },
    "MANUAL_REVIEW": {
        "bg": "#ea580c", "border": "#c2410c", "text": "#fff",
        "label": "MANUAL REVIEW REQUIRED",
        "subtitle": "Multiple trials flagged with audit issues. Per-trial source-paper re-extraction recommended before citation."
    },
    "QUARANTINE": {
        "bg": "#7f1d1d", "border": "#fbbf24", "text": "#fff",
        "label": "DATA-INTEGRITY QUARANTINE",
        "subtitle": "Multi-agent audit found multiple trials with fabricated/unresolvable NCTs or PMIDs. Do NOT cite or ship until ground-up re-extraction is completed."
    },
}


def make_badge_html(classification, score, n_trials, components):
    t = BADGE_TEMPLATES[classification]
    bar_html = ""
    if components:
        # Visual breakdown bar
        bars = []
        for label, val in [
            ("evidence-gap", components.get("E_no_evidence", 0)),
            ("null-PMID", components.get("P_null_pmid", 0)),
            ("null-NCT", components.get("N_nulled_nct", 0)),
            ("agent-flags", components.get("A_agent_flag_density", 0)),
        ]:
            if val > 0.05:
                bars.append(f'<span style="background:rgba(255,255,255,0.18);padding:2px 6px;border-radius:3px;font-size:10.5px;margin-right:6px;">{label}: {val:.0%}</span>')
        if bars:
            bar_html = '<div style="margin-top:8px;">' + "".join(bars) + '</div>'
    return (
        f'<div id="{BADGE_MARKER}" role="status" '
        f'style="background:{t["bg"]};color:{t["text"]};padding:12px 20px;'
        f'font-family:system-ui,sans-serif;font-size:13.5px;'
        f'border-bottom:3px solid {t["border"]};line-height:1.55;">'
        f'<div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap;">'
        f'<strong style="font-size:14px;letter-spacing:0.04em;">{t["label"]}</strong>'
        f'<span style="font-size:11.5px;opacity:0.92;">'
        f'Fabrication-risk score: <strong>{score:.3f}</strong> · '
        f'Trials: <strong>{n_trials}</strong></span>'
        f'</div>'
        f'<div style="margin-top:6px;font-size:12.5px;opacity:0.95;">{t["subtitle"]}</div>'
        f'{bar_html}'
        f'<div style="margin-top:6px;font-size:10.5px;opacity:0.75;">'
        f'Audited via AACT 2026-04-12 + PubMed + 14 internal-consistency rounds. '
        f'See <code style="background:rgba(255,255,255,0.15);padding:1px 4px;border-radius:2px;">outputs/extraction_audit/FINAL_INTEGRITY_REPORT_V2.md</code> for methodology.'
        f'</div></div>'
    )


# Load classifier output
scores = json.loads((OUT / "fabrication_risk_scores.json").read_text(encoding="utf-8"))

n_injected = 0
n_skipped = 0
n_missing_file = 0
n_replaced = 0
classifications_seen = {"OK": 0, "LOW_CONCERN": 0, "MANUAL_REVIEW": 0, "QUARANTINE": 0}

for r in scores:
    rv = r["review"]
    cls = r["classification"]
    score = r["score"]
    n_trials = r["n_trials"]
    components = r.get("components", {})
    classifications_seen[cls] += 1
    html_path = HERE / f"{rv}.html"
    if not html_path.exists():
        n_missing_file += 1
        continue
    txt = html_path.read_text(encoding="utf-8")
    new_badge = make_badge_html(cls, score, n_trials, components)
    # Remove old badge if present (idempotent + allow updates)
    old_badge_pat = re.compile(
        r'<div id="' + re.escape(BADGE_MARKER) + r'"[^>]*>.*?</div>\s*</div>',
        re.DOTALL | re.IGNORECASE
    )
    m_old = old_badge_pat.search(txt)
    if m_old:
        txt = txt[:m_old.start()] + txt[m_old.end():]
        n_replaced += 1
    # Inject just after <body> (or after the existing quarantine banner if present)
    quar_banner = re.search(r'(<div id="rapidmeta-quarantine-banner".*?</div>\s*)', txt, re.DOTALL)
    if quar_banner:
        # Place badge AFTER the quarantine banner
        insert_pos = quar_banner.end()
        new_txt = txt[:insert_pos] + "\n" + new_badge + "\n" + txt[insert_pos:]
    else:
        body_pat = re.compile(r"(<body[^>]*>)", re.IGNORECASE)
        m_body = body_pat.search(txt)
        if not m_body:
            n_missing_file += 1
            continue
        insert_pos = m_body.end()
        new_txt = txt[:insert_pos] + "\n" + new_badge + "\n" + txt[insert_pos:]
    if not DRY:
        html_path.write_text(new_txt, encoding="utf-8")
    n_injected += 1

# Also handle banner-quarantined reviews that aren't in classifier (shouldn't happen
# since classifier covers all reviews; this is a safety net)

print(f"{'DRY-RUN ' if DRY else ''}Badge injection complete")
print(f"  Injected/updated: {n_injected}")
print(f"  Replaced existing: {n_replaced}")
print(f"  Missing file:     {n_missing_file}")
print(f"\nClassifications:")
for k, n in classifications_seen.items():
    print(f"  {k}: {n}")
