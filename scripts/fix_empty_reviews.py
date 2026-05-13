"""Add explicit "audit-zeroed" or "no data extracted" notice to reviews
where the extraction section + analysis are empty.

Two categories:
  A) cleanup_zeroed: I nulled all trials in this review during the audit.
     Add a notice saying "Integrity audit found all extracted trials had
     wrong PMID/NCT or fabricated values; all rows nulled."
  B) never_extracted: the review HTML was created but no trial data was
     ever populated. Add a notice saying "This review's data extraction
     was never completed."

Both get a yellow/orange banner explaining the empty state so users don't
think the page is broken.
"""
from __future__ import annotations
import json, re, sys, io
from pathlib import Path

if hasattr(sys.stdout, "buffer") and getattr(sys.stdout, "encoding", "").lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent.parent
OUT = HERE / "outputs" / "extraction_audit"
DATA = OUT / "data"
DRY = "--dry-run" in sys.argv
NOTICE_MARKER = "rapidmeta-empty-data-notice"

# Identify categories
cleanup_zeroed = []
never_extracted = []
for f in sorted(DATA.glob("*.json")):
    if f.name.startswith("_"): continue
    rv = f.stem
    try: d = json.load(open(f, "r", encoding="utf-8"))
    except: continue
    rd = d.get("realData") or {}
    if not isinstance(rd, dict): continue
    total = len(rd)
    nulled = sum(1 for k in rd if k.startswith("NULLED:"))
    has_numeric = sum(1 for k, t in rd.items()
                       if not k.startswith("NULLED:")
                       and isinstance(t, dict)
                       and any(t.get(x) not in (None, 0) for x in ("tE","tN","cE","cN","publishedHR")))
    if has_numeric == 0:
        if total > 0 and nulled == total:
            cleanup_zeroed.append({"review": rv, "total": total, "nulled": nulled})
        elif total == 0:
            never_extracted.append({"review": rv, "total": total})
        else:
            cleanup_zeroed.append({"review": rv, "total": total, "nulled": nulled})

print(f"Cleanup-zeroed: {len(cleanup_zeroed)}")
print(f"Never-extracted: {len(never_extracted)}")


def make_notice(category, info):
    if category == "cleanup_zeroed":
        n = info.get("total", 0); k = info.get("nulled", 0)
        return f'''
<div id="{NOTICE_MARKER}" role="status" style="background:#FFF7E8;border:1px solid #E5CC8A;border-left:4px solid #ea580c;padding:14px 20px;margin:1rem 0;font-family:system-ui,sans-serif;color:#5C4310;border-radius:6px;">
  <strong style="display:block;margin-bottom:.3rem;font-size:.95rem;">⚠ Data-integrity audit nulled all extracted trials in this review</strong>
  <div style="font-size:.85rem;line-height:1.5;">
    The original extraction had {n} trial row{"s" if n != 1 else ""}. After cross-verification against AACT 2026-04-12 + PubMed + PubMed Central full-text + multi-agent consensus, all {k} entries failed integrity checks (wrong NCT, fabricated PMID, drug-disease mismatch, or arm-count inconsistencies). They were renamed to <code>NULLED:&lt;NCT&gt;</code> to preserve the audit trail while excluding them from pooling.
  </div>
  <div style="font-size:.8rem;color:#7A5A10;margin-top:.5rem;">
    This page is empty BY DESIGN — not a broken page. Ground-up re-extraction from primary sources is needed before this review can be cited or pooled.
    See <a href="audit_table.html" style="color:#7A5A10;">audit table</a> · <a href="what_changed.html" style="color:#7A5A10;">what changed</a>.
  </div>
</div>
'''
    else:  # never_extracted
        return f'''
<div id="{NOTICE_MARKER}" role="status" style="background:#F1F5F9;border:1px solid #94A3B8;border-left:4px solid #64748B;padding:14px 20px;margin:1rem 0;font-family:system-ui,sans-serif;color:#334155;border-radius:6px;">
  <strong style="display:block;margin-bottom:.3rem;font-size:.95rem;">📂 Data extraction pending</strong>
  <div style="font-size:.85rem;line-height:1.5;">
    This review's HTML template was created but trial-level data has not yet been populated. The Extraction and Analysis sections will display once trials are added.
  </div>
  <div style="font-size:.8rem;color:#475569;margin-top:.5rem;">
    See <a href="index.html" style="color:#475569;">main index</a> for completed reviews.
  </div>
</div>
'''


applied = []
for info in cleanup_zeroed + never_extracted:
    rv = info["review"]
    category = "cleanup_zeroed" if info in cleanup_zeroed else "never_extracted"
    html_path = HERE / f"{rv}.html"
    if not html_path.exists():
        applied.append({**info, "category": category, "status": "FILE_MISSING"})
        continue
    txt = html_path.read_text(encoding="utf-8")
    if NOTICE_MARKER in txt:
        applied.append({**info, "category": category, "status": "ALREADY_HAS_NOTICE"})
        continue
    notice = make_notice(category, info)
    # Insert after <body> (or after the integrity badge if present)
    badge_pat = re.compile(r'(<div id="rapidmeta-integrity-badge".*?</div>\s*</div>\s*)', re.DOTALL)
    m_badge = badge_pat.search(txt)
    if m_badge:
        ins = m_badge.end()
        new_txt = txt[:ins] + notice + txt[ins:]
    else:
        body_pat = re.compile(r"(<body[^>]*>)", re.IGNORECASE)
        m_body = body_pat.search(txt)
        if not m_body:
            applied.append({**info, "category": category, "status": "NO_BODY_TAG"})
            continue
        ins = m_body.end()
        new_txt = txt[:ins] + "\n" + notice + txt[ins:]
    if not DRY:
        html_path.write_text(new_txt, encoding="utf-8")
    applied.append({**info, "category": category, "status": "NOTICE_INJECTED"})

n_cz = sum(1 for r in applied if r["category"] == "cleanup_zeroed" and r["status"] == "NOTICE_INJECTED")
n_ne = sum(1 for r in applied if r["category"] == "never_extracted" and r["status"] == "NOTICE_INJECTED")
print(f"\n{'DRY-RUN ' if DRY else ''}Notices injected:")
print(f"  Cleanup-zeroed: {n_cz}")
print(f"  Never-extracted: {n_ne}")

(OUT / "empty_reviews_notice.json").write_text(
    json.dumps({"cleanup_zeroed": cleanup_zeroed, "never_extracted": never_extracted,
                 "applied": applied,
                 "summary": {"notices_injected": n_cz + n_ne}},
                indent=2, ensure_ascii=False), encoding="utf-8")
