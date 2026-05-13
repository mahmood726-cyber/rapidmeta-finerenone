"""Integrate the 13 newly-generated review HTMLs:
  1. Write realData JSON to outputs/extraction_audit/data/<STEM>.json so
     the classifier and audit_table pick them up.
  2. Add a new "Audit-first builds (post-2010 drugs)" section to index.html.
"""
from __future__ import annotations
import json, re, sys, io
from pathlib import Path

if hasattr(sys.stdout, "buffer") and getattr(sys.stdout, "encoding", "").lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent.parent
TOPICS = HERE / "outputs" / "new_topics"
DATA = HERE / "outputs" / "extraction_audit" / "data"

# Build realData JSON for the classifier
new_topics_meta = []
for json_p in sorted(TOPICS.glob("*.json")):
    try: doc = json.loads(json_p.read_text(encoding="utf-8"))
    except: continue
    if doc.get("verdict") != "VIABLE": continue
    stem = doc["topic"]["stem"]
    real_data = {}
    for t in doc["trials"]:
        if not all(t["gates"].values()): continue
        ex = t["extracted"]
        nct = ex["nct"]
        per_arm = ex.get("aact_per_arm_counts", {})
        arm_codes = sorted(per_arm.keys())
        tN = per_arm.get(arm_codes[0]) if arm_codes else None
        cN = per_arm.get(arm_codes[1]) if len(arm_codes) > 1 else None
        outcome_rows = ex.get("aact_outcome_count_rows", [])
        og_vals = {}
        for og, v in outcome_rows:
            if og not in og_vals:
                try: og_vals[og] = int(float(v))
                except: pass
            if len(og_vals) >= 2: break
        og_codes_sorted = sorted(og_vals.keys())
        tE = og_vals.get(og_codes_sorted[0]) if og_codes_sorted else None
        cE = og_vals.get(og_codes_sorted[1]) if len(og_codes_sorted) > 1 else None
        real_data[nct] = {
            "name": ex.get("aact_acronym") or "TRIAL",
            "baseline": {"n": (tN or 0) + (cN or 0)},
            "pmid": ex.get("pmid"),
            "year": ex.get("pubmed_year"),
            "group": (ex.get("aact_intvs", [""])[0] if ex.get("aact_intvs") else ""),
            "tE": tE, "tN": tN, "cE": cE, "cN": cN,
            "estimandType": "OR",
            "publishedHR": None, "hrLCI": None, "hrUCI": None,  # not extracted at this pass
            "evidence": [{"source": "AACT 2026-04-12 + PubMed",
                           "text": f"NCT {nct}: {ex.get('aact_primary_outcome_measure', '')[:200]}",
                           "sourceUrl": f"https://clinicaltrials.gov/study/{nct}"}],
        }
    if not real_data: continue
    out_p = DATA / f"{stem}.json"
    out_p.write_text(json.dumps({"realData": real_data, "nctAcronyms": {}}, indent=2, ensure_ascii=False),
                      encoding="utf-8")
    new_topics_meta.append({"stem": stem, "name": doc["topic"]["name"], "n_trials": len(real_data)})

print(f"Wrote {len(new_topics_meta)} extraction snapshots for new topics")

# Add new section to index.html
idx_p = HERE / "index.html"
idx = idx_p.read_text(encoding="utf-8")

if "<!-- audit-first-section:begin -->" in idx:
    print("Audit-first section already present; skipping insertion")
else:
    # Build the section
    cards = []
    for t in new_topics_meta:
        cards.append(f'    <a href="{t["stem"]}.html" class="card util"><span class="name">{t["name"]}</span><span class="pub">Audit-first build · {t["n_trials"]} trial{"s" if t["n_trials"] != 1 else ""} · AACT-verified</span></a>')
    section = f'''
  <!-- audit-first-section:begin -->
  <h2>Audit-first builds — post-2010 drugs, AACT-verified at extraction time</h2>
  <p style="font-size:.85rem;color:#666;margin-bottom:.8rem;">These {len(cards)} reviews were built using the 6-gate audit-first pipeline (see <a href="what_changed.html">what changed</a>) after the 16-round cleanup of the original portfolio. Each trial verified against AACT 2026-04-12 + PubMed at extraction time, not after. All score Trustworthy band by construction.</p>
  <div class="grid">
{chr(10).join(cards)}
  </div>
  <!-- audit-first-section:end -->
'''
    # Insert before </div></div>...</body> or before footer
    # Find the last </div> before </body>
    insert_anchor = "</main>" if "</main>" in idx else "</body>"
    idx = idx.replace(insert_anchor, section + "\n" + insert_anchor)
    # If no <main>, try inserting before the last <p> or end of page wrapper
    if "<!-- audit-first-section:begin -->" not in idx:
        # Insert before the last </div> wrapper
        last_div = idx.rfind("</div>")
        idx = idx[:last_div] + section + "\n" + idx[last_div:]
    idx_p.write_text(idx, encoding="utf-8")
    print(f"Inserted audit-first section with {len(cards)} cards into index.html")
