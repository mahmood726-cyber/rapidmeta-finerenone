"""Upgrade `*_AUTO_REVIEW.html` (audit-first lite, ~22 KB) so it stops being thin.

The lite pages are produced by `scripts/generate_topic_html.py` and ship with:
  * Static PRISMA, gates table, AACT outcome label, per-trial 2x2 table, forest plot.
  * No PubMed abstract.
  * No link to the richer `*_AUTO_FULL_REVIEW.html` twin even when one exists.
  * No risk-of-bias evidence (intentional — audit-first scope).

What this script adds:
  1. A prominent banner at the top of each lite page:
       — if a `_AUTO_FULL_REVIEW.html` twin exists -> "Open the full interactive
         dashboard (editable extraction, forest, RoB, GRADE) →"
       — otherwise -> the existing TRUSTWORTHY banner stays as-is.
  2. Per-trial abstract preview block under the Extraction tab cards, hydrated
     at runtime via PubMed E-utilities `efetch?db=pubmed&id=<pmid>&rettype=abstract`.
     PMIDs come from the same AACT `study_references` map used for FULL_REVIEW
     hydration (`outputs/pmid_resolver/nct_to_pmid.json`). If a NCT has no
     verified PMID, the abstract block silently no-ops — no broken UI.
  3. The PMID map is embedded as a small JSON island in the page (only the
     NCTs that the page references), so no second HTTP request just to learn
     pmids.

Idempotent. Only edits `*_AUTO_REVIEW.html` (not FULL_REVIEW, not curated REVIEW).
"""
from __future__ import annotations
import json
import re
import sys
import io
from pathlib import Path

if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent.parent
NCT_PMID = json.loads((HERE / "outputs" / "pmid_resolver" / "nct_to_pmid.json").read_text(encoding="utf-8"))
NCT_RE = re.compile(r"NCT\d{7,8}")

# Banner block — inserted just after the existing #rapidmeta-integrity-badge div.
BANNER_MARK = "<!-- rapidmeta-upgrade-banner:begin -->"
BANNER_END = "<!-- rapidmeta-upgrade-banner:end -->"

# Abstract-hydration script — inserted just before </body>.
ABSTRACT_MARK = "<!-- rapidmeta-abstract-hydrator:begin -->"
ABSTRACT_END = "<!-- rapidmeta-abstract-hydrator:end -->"

BANNER_TEMPLATE = """{begin}
<div style="background:#1e293b;border-left:4px solid #34d399;padding:12px 16px;margin:0;font-family:system-ui,sans-serif;font-size:13px;color:#cbd5e1;line-height:1.55;">
  <strong style="color:#34d399;">⧉ Full interactive dashboard available</strong> for this topic.
  <a href="{full_href}" style="color:#7dd3fc;text-decoration:underline;margin-left:8px;">Open editable extraction + forest + RoB + GRADE →</a>
  <span style="display:block;color:#94a3b8;font-size:11.5px;margin-top:4px;">
    This audit-first lite page documents the 6-gate integrity floor; the full dashboard runs the same trials through the interactive RapidMeta workbench with PubMed-hydrated abstracts.
  </span>
</div>
{end}
"""

ABSTRACT_SCRIPT_TEMPLATE = """{begin}
<script>
(function(){{
  'use strict';
  var NCT_PMID = {nct_pmid_json};
  function $(sel, root){{ return (root||document).querySelector(sel); }}
  function fetchAbstract(pmid){{
    var key = 'rm_abstract_v1_' + pmid;
    try {{
      var c = localStorage.getItem(key);
      if (c) {{
        var o = JSON.parse(c);
        if (o && o.text && (Date.now() - o.fetchedAt) < 1000*60*60*24*90) return Promise.resolve(o.text);
      }}
    }} catch(e){{}}
    var url = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id=' + encodeURIComponent(pmid) + '&rettype=abstract&retmode=text';
    return fetch(url).then(function(r){{ return r.ok ? r.text() : ''; }}).then(function(t){{
      t = (t||'').trim();
      if (t) {{ try {{ localStorage.setItem(key, JSON.stringify({{text:t, fetchedAt:Date.now()}})); }} catch(e){{}} }}
      return t;
    }}).catch(function(){{ return ''; }});
  }}
  function render(){{
    var pane = document.getElementById('tab-extraction');
    if (!pane) return;
    var cards = pane.querySelectorAll('div[style*="background:#1e293b"]');
    cards.forEach(function(card){{
      var ncts = (card.innerHTML.match(/NCT\\d{{7,8}}/g) || []);
      if (!ncts.length) return;
      var nct = ncts[0];
      var rec = NCT_PMID[nct];
      if (!rec || !rec.pmid) return;
      if (card.querySelector('.rm-abstract-block')) return;
      var block = document.createElement('div');
      block.className = 'rm-abstract-block';
      block.style.cssText = 'margin-top:10px;padding:10px 12px;background:#0a0f1f;border-radius:4px;border-left:3px solid #7dd3fc;font-size:12px;color:#cbd5e1;line-height:1.55;max-height:340px;overflow:auto;';
      block.innerHTML = '<div style="color:#94a3b8;font-size:11px;margin-bottom:6px;text-transform:uppercase;letter-spacing:0.05em;">PubMed abstract · <a href="https://pubmed.ncbi.nlm.nih.gov/' + rec.pmid + '/" target="_blank" style="color:#7dd3fc;">PMID ' + rec.pmid + '</a> · <span style="color:#64748b;">'+ (rec.type||'') +'</span></div><div class="rm-abstract-text" style="white-space:pre-wrap;">Loading abstract…</div>';
      card.appendChild(block);
      fetchAbstract(rec.pmid).then(function(text){{
        var t = block.querySelector('.rm-abstract-text');
        if (!t) return;
        if (text) {{ t.textContent = text; }}
        else {{ t.textContent = 'Abstract unavailable from PubMed E-utilities (network or rate-limit). Open the PMID link above for the canonical record.'; t.style.color = '#94a3b8'; }}
      }});
    }});
  }}
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', render);
  else render();
  // Re-render when the Extraction tab becomes active (tab handler defers DOM work otherwise).
  document.addEventListener('click', function(e){{
    if (e.target && e.target.dataset && e.target.dataset.tab === 'extraction') setTimeout(render, 50);
  }});
}})();
</script>
{end}
"""


def patch_file(p: Path) -> tuple[bool, dict]:
    txt = p.read_text(encoding="utf-8", errors="replace")
    orig = txt
    stats = {"banner_added": False, "abstract_added": False, "pmids_for": 0}

    stem = p.name.replace("_AUTO_REVIEW.html", "")
    full_twin = HERE / f"{stem}_AUTO_FULL_REVIEW.html"
    curated_twin = HERE / f"{stem}_REVIEW.html"

    # Prefer the cloned full dashboard if it exists; otherwise fall back to the
    # curated flagship (some non-viable audit stubs have a hand-authored
    # `<STEM>_REVIEW.html` that is the real richest view for the topic).
    twin = full_twin if full_twin.exists() else (curated_twin if curated_twin.exists() else None)

    # --- 1. Banner ---
    if twin is not None:
        if BANNER_MARK not in txt:
            block = BANNER_TEMPLATE.format(
                begin=BANNER_MARK, end=BANNER_END, full_href=twin.name
            )
            # Insert right after the closing </div> of #rapidmeta-integrity-badge.
            anchor_re = re.compile(
                r'(id="rapidmeta-integrity-badge"[\s\S]*?</div>\s*</div>)',
                re.IGNORECASE,
            )
            new_txt, n = anchor_re.subn(lambda m: m.group(1) + "\n" + block, txt, count=1)
            if n == 1:
                txt = new_txt
                stats["banner_added"] = True
        # If the banner already exists but the href changed, refresh it.
        else:
            existing_banner_re = re.compile(
                r'<!-- rapidmeta-upgrade-banner:begin -->[\s\S]*?<!-- rapidmeta-upgrade-banner:end -->'
            )
            refreshed = BANNER_TEMPLATE.format(
                begin=BANNER_MARK, end=BANNER_END, full_href=twin.name
            ).rstrip()
            txt = existing_banner_re.sub(lambda _m: refreshed, txt, count=1)

    # --- 2. Abstract hydrator (always — works whether or not twin exists) ---
    # Build mini map of just the NCTs referenced by this page.
    ncts = sorted(set(NCT_RE.findall(txt)))
    local_map = {n: NCT_PMID[n] for n in ncts if n in NCT_PMID}
    stats["pmids_for"] = len(local_map)
    if local_map:
        snippet = ABSTRACT_SCRIPT_TEMPLATE.format(
            begin=ABSTRACT_MARK,
            end=ABSTRACT_END,
            nct_pmid_json=json.dumps(local_map, separators=(",", ":")),
        )
        if ABSTRACT_MARK in txt:
            # Replace existing snippet so the embedded map stays current.
            existing_re = re.compile(
                r'<!-- rapidmeta-abstract-hydrator:begin -->[\s\S]*?<!-- rapidmeta-abstract-hydrator:end -->'
            )
            # Use a lambda so backslashes in `snippet` are not treated as regex back-refs.
            txt = existing_re.sub(lambda _m: snippet.rstrip(), txt, count=1)
            stats["abstract_added"] = True
        else:
            # Insert just before </body>. Use str.replace, not re.sub, so the JS
            # body (which contains `NCT\d{7,8}`) is not interpreted as a regex
            # template escape.
            if "</body>" in txt:
                txt = txt.replace("</body>", snippet + "\n</body>", 1)
                stats["abstract_added"] = True

    changed = txt != orig
    if changed:
        p.write_text(txt, encoding="utf-8")
    return changed, stats


def main():
    targets = sorted(HERE.glob("*_AUTO_REVIEW.html"))
    print(f"Targets: {len(targets):,} AUTO_REVIEW (lite) files")
    n_banner = n_abs = n_changed = 0
    pmid_total = 0
    for i, p in enumerate(targets, 1):
        changed, s = patch_file(p)
        if changed:
            n_changed += 1
        if s["banner_added"]:
            n_banner += 1
        if s["abstract_added"]:
            n_abs += 1
        pmid_total += s["pmids_for"]
        if i <= 5 or i % 200 == 0:
            print(f"  [{i}/{len(targets)}] {p.name}: banner={s['banner_added']} abstract={s['abstract_added']} pmids={s['pmids_for']}")
    print()
    print(f"Files touched              : {n_changed:,}")
    print(f"Banners added              : {n_banner:,}")
    print(f"Abstract hydrators added   : {n_abs:,}")
    print(f"Total embedded PMID map sz : {pmid_total:,} NCT entries (across all pages)")


if __name__ == "__main__":
    main()
