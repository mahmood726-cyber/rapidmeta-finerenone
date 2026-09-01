r"""Build portfolio_pools.html — a sortable/filterable dashboard of every
R-validation pool in the portfolio (binary + continuous, ~1,317 sidecars).

For each sidecar, the row carries: topic name, scale, k, pooled estimate,
95% CI, I-squared, Q p-value, prediction interval, and a link to the
source review page. Sortable client-side; filterable by scale, k tier,
and free-text topic search.

Strictly additive: writes one new file at the repo root.
"""
from __future__ import annotations
import sys, io, json, html
from pathlib import Path

if "pytest" not in sys.modules and hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent.parent
import importlib.util as _ilu


def _load(mod, rel):
    """Import a sibling script WITHOUT copying its logic. A second reader of the
    same fact is how two surfaces begin disagreeing about one artefact."""
    _sp = _ilu.spec_from_file_location(mod, str(HERE / "scripts" / rel))
    _m = _ilu.module_from_spec(_sp)
    _src = open(_sp.origin, encoding="utf-8").read().split(chr(10) + "if __name__")[0]
    exec(compile(_src, _sp.origin, "exec"), _m.__dict__)
    return _m


STORE_REFUSAL = _load("store_refusal", "store_refusal.py")
MEMBERSHIP = _load("sidecar_membership", "sidecar_membership.py")

BIN_DIR = HERE / "outputs" / "r_validation"
CONT_DIR = HERE / "outputs" / "r_validation" / "continuous"


def _round(v, n=3):
    if v is None: return ""
    try:
        return f"{float(v):.{n}f}"
    except (TypeError, ValueError):
        return ""


def _find_source_page(stem: str) -> str:
    """Best-effort: locate the review HTML for this sidecar stem.

    Sidecars under outputs/r_validation/<STEM>.json are named after the
    page name minus _REVIEW.html (e.g. ABALOPARATIDE_OSTEO_AUTO_FULL ->
    ABALOPARATIDE_OSTEO_AUTO_FULL_REVIEW.html). For legacy sidecars
    (FINERENONE) the page is <STEM>_REVIEW.html.

    Continuous sidecars under outputs/r_validation/continuous/<STEM>.json
    use the FULL page name (with _REVIEW suffix) e.g.
    SEMAGLUTIDE_OBESITY_REVIEW.json -> SEMAGLUTIDE_OBESITY_REVIEW.html.
    """
    candidates = [
        HERE / f"{stem}_REVIEW.html",
        HERE / f"{stem}.html",
    ]
    for c in candidates:
        if c.exists():
            return c.name
    return f"{stem}_REVIEW.html"


def read_binary_sidecars():
    rows = []
    for p in sorted(BIN_DIR.glob("*.json")):
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        stem = p.stem
        k = d.get("k", 0)
        if not k: continue
        rows.append({
            "stem": stem,
            "kind": "binary",
            "scale": d.get("method", "").startswith("REML") and "OR" or d.get("scale", "OR"),
            "k": k,
            "pool": d.get("pooled_OR"),
            "lci": d.get("ci_low_OR"),
            "uci": d.get("ci_high_OR"),
            "i2": d.get("I2"),
            "qp": d.get("Qp"),
            "pi_lci": d.get("PI_low_OR"),
            "pi_uci": d.get("PI_high_OR"),
            "tau2": d.get("tau2"),
            "hksj_floor": bool(d.get("hksj_floor_applied", False)),
            "page": _find_source_page(stem),
            "_sidecar": d,
        })
    return rows


def read_continuous_sidecars():
    rows = []
    if not CONT_DIR.exists():
        return rows
    for p in sorted(CONT_DIR.glob("*.json")):
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        stem = p.stem
        k = d.get("k", 0)
        if not k: continue
        scale = d.get("scale", "MD")
        # Continuous sidecars keep their _REVIEW suffix in the stem
        page = f"{stem}.html"
        if not (HERE / page).exists():
            page = stem + ".html"
        rows.append({
            "stem": stem,
            "kind": "continuous",
            "scale": scale,
            "k": k,
            "pool": d.get("pool"),
            "lci": d.get("lci"),
            "uci": d.get("uci"),
            "i2": d.get("I2"),
            "qp": d.get("Qp") or d.get("Qp"),
            "pi_lci": d.get("PI_lci"),
            "pi_uci": d.get("PI_uci"),
            "tau2": d.get("tau2"),
            "hksj_floor": bool(d.get("hksj_floor_applied", False)),
            "page": page,
            "_sidecar": d,
        })
    return rows


# --- WITHHOLDING, DECIDED HERE AND RENDERED BELOW -------------------------------
# RULED: withhold AT THE GENERATOR, never by post-editing a served page. Eleven rows
# were hand-written into portfolio_pools.html on 2026-08-31 and this generator knew
# nothing about them -- one run would have erased every disclosure silently.
#
# A WITHHELD CELL WHOSE REASON NAMES NO TRIALS IS THE SAME DEFECT ONE LEVEL DOWN, so
# every reason below names the trials it is about.
#
# AND A WRONG REASON IS WORSE THAN NO REASON. The AGYW row previously read "the
# endpoint this number measures is not recorded" -- which invites a reader to conclude
# the NUMBER is right and only the LABEL is missing. It is the other way round: that
# pool is built from HPTN 082 and FACTS-001, and the review is a dapivirine-ring review
# of ASPIRE and the Ring Study. Understating a defect directs the reader's inference
# wrongly.
POLARITY_WITHHOLDING_ENABLED = False   # RULING B, held pending the tau-squared lane.
# Enabling this is one line and a decision, not a rewrite. It would withhold 9 of 99
# rows; the store-level figure is 97 of 163 PAGE_MAP pages and DOES NOT transfer,
# because 74 pool stems map to no PAGE_MAP page at all.


def _page_html(page):
    fp = HERE / page
    if not fp.exists():
        return None
    return fp.read_text(encoding="utf-8", errors="replace")


def withholding_for(row, sidecar, page_map):
    """[{kind, reason, trials, source}] for one pool row. Callers render; they do
    not re-decide. Empty means nothing is withheld."""
    out = []
    page = row.get("page") or ""

    for w in STORE_REFUSAL.for_page(page, page_map):
        if w["kind"] == "polarity-unknown" and not POLARITY_WITHHOLDING_ENABLED:
            continue
        out.append({"kind": w["kind"], "reason": w["reason"],
                    "trials": [], "source": w["source"]})

    html_text = _page_html(page)
    if sidecar is not None and html_text is not None:
        state, ev = MEMBERSHIP.classify(sidecar, html_text)
        if state in ("EXCLUDED_BY_REVIEW", "DISJOINT"):
            excluded = ev.get("present_only_as_an_excluded_record") or []
            absent = ev.get("absent_from_the_page") or []
            bits = []
            if excluded:
                bits.append("%s appears on the review page ONLY inside its "
                            "excluded-records list -- the review considered it and "
                            "said no, and this pool took it anyway"
                            % ", ".join(excluded))
            if absent:
                bits.append("%s does not appear on the review page at all"
                            % ", ".join(absent))
            out.append({
                "kind": "SIDECAR_TRIAL_SET_DISJOINT_FROM_REVIEW",
                "reason": ("This estimate is not this review's. It pools %s, and %s. "
                           "A pool built from trials the review does not include "
                           "answers a different question, so the number is withheld "
                           "rather than shown beside the review's name."
                           % (", ".join(ev.get("pooled") or []), "; ".join(bits))),
                "trials": ev.get("pooled") or [],
                "source": "outputs/r_validation/%s.json" % row.get("stem", "")})

    if sidecar is not None and row.get("k") == 1:
        out.append({
            "kind": "SINGLE_TRIAL_NOT_A_POOL",
            "reason": ("Nothing is pooled here: k=1. The value is one trial's own "
                       "result and is not a synthesis."),
            "trials": [t for t, _ in MEMBERSHIP.trial_labels(sidecar)],
            "source": "outputs/r_validation/%s.json" % row.get("stem", "")})
    return out


def _withheld_cells(kinds):
    return ('<td class="pool"><span class="withheld-pool" data-withheld="%s">withheld</span></td>'
            '<td class="ci"><span class="withheld-pool">withheld</span></td>'
            '<td class="pi"><span class="withheld-pool">withheld</span></td>'
            % html.escape(",".join(kinds)))


def _detail_row(row, whs):
    blocks = []
    for w in whs:
        # LABELS ARE RENDERED VERBATIM. Several sidecars store a truncated label --
        # AGYW_HIV_PREP holds "HPTN 082 (oral PrEP" with the bracket unclosed. Tidying
        # it here would hide a defect in the stored record and make the surface look
        # tidier than the data is; leaving it bare invites the reader to blame the
        # page. So it is shown as stored and MARKED as stored.
        trials = ""
        if w.get("trials"):
            ragged = any(t.count("(") != t.count(")") for t in w["trials"])
            trials = ('<span class="withheld-trials">Trials in this pool: %s%s</span>'
                      % (html.escape("; ".join(w["trials"])),
                         (" [labels shown exactly as the sidecar stores them; one or "
                          "more is truncated in the record itself]") if ragged else ""))
        blocks.append('<div class="withheld-reason" data-fact="%s">%s %s'
                      '<span class="withheld-src">-- %s</span></div>'
                      % (html.escape(w["kind"]), html.escape(w["reason"]), trials,
                         html.escape(w.get("source") or "")))
    return ('<tr class="withheld-detail" data-stem="%s" data-withheld="%s">'
            '<td colspan="10">%s</td></tr>'
            % (html.escape(str(row.get("stem", "")).lower()),
               html.escape(",".join(w["kind"] for w in whs)), "".join(blocks)))


def _row_html(r: dict, idx: int, whs=None) -> str:
    """Render one <tr>. When `whs` is non-empty the pooled cells are
    replaced by a withheld marker and a detail row carrying the reason
    and the trials by name."""
    sig_class = ""
    pool = r["pool"]
    lci, uci = r["lci"], r["uci"]
    # Significance heuristic (binary OR vs 1, continuous MD vs 0)
    if r["kind"] == "binary" and lci is not None and uci is not None:
        if uci < 1.0:
            sig_class = "sig-benefit"   # CI fully below null
        elif lci > 1.0:
            sig_class = "sig-harm"
    elif r["kind"] == "continuous" and lci is not None and uci is not None:
        if uci < 0:
            sig_class = "sig-benefit"
        elif lci > 0:
            sig_class = "sig-harm"

    pool_fmt = _round(pool, 3) if pool is not None else "—"
    ci_fmt = (
        f"{_round(lci, 3)} to {_round(uci, 3)}"
        if lci is not None and uci is not None
        else "—"
    )
    pi_fmt = (
        f"{_round(r['pi_lci'], 3)} to {_round(r['pi_uci'], 3)}"
        if r["pi_lci"] is not None and r["pi_uci"] is not None
        else "—"
    )
    qp = r["qp"]
    qp_fmt = "—"
    if qp is not None:
        try:
            v = float(qp)
            qp_fmt = f"{v:.3f}" if v >= 0.001 else f"{v:.2e}"
        except (TypeError, ValueError):
            pass
    i2_fmt = _round(r["i2"], 1)
    tau2_fmt = _round(r["tau2"], 4)
    floor_badge = (
        '<span class="floor-yes" title="HKSJ floor applied (Wiksten 2016)">Yes</span>'
        if r["hksj_floor"] else '<span class="floor-no">—</span>'
    )

    page_link = html.escape(r["page"])
    stem_disp = html.escape(r["stem"])

    whs = whs or []
    if whs:
        # A withheld row carries NO significance class: it has not been shown to
        # have a direction, and colouring it would assert one.
        sig_class = ""
    body = (
        f'<td class="pool">{pool_fmt}</td>'
        f'<td class="ci">{ci_fmt}</td>'
        f'<td class="pi">{pi_fmt}</td>'
    ) if not whs else _withheld_cells([w["kind"] for w in whs])

    return (
        f'<tr data-stem="{html.escape(r["stem"].lower())}" data-scale="{r["scale"]}" '
        f'data-k="{r["k"]}"'
        + (f' data-withheld="{html.escape(",".join(w["kind"] for w in whs))}"' if whs else "")
        + f' class="{sig_class}">'
        f'<td><a href="{page_link}">{stem_disp}</a></td>'
        f'<td class="scale">{r["scale"]}</td>'
        f'<td class="k">{r["k"]}</td>'
        + body
        + f'<td class="i2">{i2_fmt}{"%" if i2_fmt else ""}</td>'
        + f'<td class="qp">{qp_fmt}</td>'
        + f'<td class="tau2">{tau2_fmt}</td>'
        + f'<td class="floor">{floor_badge}</td>'
        + '</tr>'
        + (_detail_row(r, whs) if whs else "")
    )


def main():
    binary = read_binary_sidecars()
    cont = read_continuous_sidecars()
    rows = binary + cont
    rows.sort(key=lambda r: (r["stem"], r["kind"]))
    print(f"Binary rows: {len(binary)}")
    print(f"Continuous rows: {len(cont)}")
    print(f"Total: {len(rows)}")

    # Summary stats
    from collections import Counter
    scale_dist = Counter(r["scale"] for r in rows)
    k_dist = Counter()
    for r in rows:
        k = r["k"]
        if k == 1: k_dist["k=1"] += 1
        elif k <= 3: k_dist["k=2-3"] += 1
        elif k <= 10: k_dist["k=4-10"] += 1
        else: k_dist["k>10"] += 1
    floor_count = sum(1 for r in rows if r["hksj_floor"])
    sig_benefit = sum(1 for r in rows if r["kind"] == "binary" and r["uci"] is not None and r["uci"] < 1.0)
    sig_harm = sum(1 for r in rows if r["kind"] == "binary" and r["lci"] is not None and r["lci"] > 1.0)

    # DECIDE WITHHOLDING BEFORE RENDERING, and PRINT what was withheld so the run
    # states it rather than leaving it to be found in the output.
    try:
        with open(str(HERE / "ssot" / "PAGE_MAP.json"), encoding="utf-8") as _fh:
            page_map = json.load(_fh)
    except Exception:
        page_map = {}
    withheld_by_row, wh_kinds = {}, Counter()
    for _i, _r in enumerate(rows):
        _whs = withholding_for(_r, _r.get("_sidecar"), page_map)
        if _whs:
            withheld_by_row[_i] = _whs
            for _w in _whs:
                wh_kinds[_w["kind"]] += 1
    print("withheld rows: %d of %d" % (len(withheld_by_row), len(rows)))
    for _k, _n in sorted(wh_kinds.items()):
        print("   %-44s %d" % (_k, _n))
    if not POLARITY_WITHHOLDING_ENABLED:
        print("   polarity-unknown SUPPRESSED -- ruling B is held; enabling it is",
              "one line and a decision, not a rewrite")

    body = chr(10).join(_row_html(r, i, withheld_by_row.get(i))
                        for i, r in enumerate(rows))
    summary_row = f"""
    <div class="summary-row">
      <div class="summary-card"><div class="num">{len(rows):,}</div><div class="lab">Total pools</div></div>
      <div class="summary-card"><div class="num">{len(binary):,}</div><div class="lab">Binary (OR)</div></div>
      <div class="summary-card"><div class="num">{len(cont):,}</div><div class="lab">Continuous (MD/HR/RR/RD)</div></div>
      <div class="summary-card"><div class="num">{floor_count:,}</div><div class="lab">HKSJ-floor applied</div></div>
      <div class="summary-card sig-benefit-card"><div class="num">{sig_benefit:,}</div><div class="lab">Binary pools with 95% CI &lt; 1 (benefit)</div></div>
      <div class="summary-card sig-harm-card"><div class="num">{sig_harm:,}</div><div class="lab">Binary pools with 95% CI &gt; 1 (harm)</div></div>
    </div>
    """

    out = HERE / "portfolio_pools.html"
    out.write_text(f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Portfolio pools — rapidmeta-finerenone</title>
<meta name="description" content="Sortable dashboard of every R-validation meta-analysis pool in the rapidmeta-finerenone portfolio">
<style>
  body {{ margin:0; background:#0f172a; color:#e2e8f0; font-family:system-ui,-apple-system,sans-serif; font-size:13px; line-height:1.5; }}
  header {{ padding:24px; background:#0a0f1f; border-bottom:1px solid #1f2a44; }}
  h1 {{ margin:0 0 8px 0; font-size:20px; }}
  .desc {{ color:#94a3b8; font-size:13px; max-width:1100px; margin-top:8px; }}
  .summary-row {{ display:flex; gap:10px; flex-wrap:wrap; margin:14px 0; max-width:1200px; }}
  .summary-card {{ background:#1e293b; padding:10px 14px; border-radius:6px; min-width:130px; }}
  .summary-card .num {{ font-size:22px; font-weight:600; color:#7dd3fc; }}
  .summary-card .lab {{ font-size:11px; color:#94a3b8; text-transform:uppercase; letter-spacing:0.04em; }}
  .summary-card.sig-benefit-card .num {{ color:#86efac; }}
  .summary-card.sig-harm-card .num {{ color:#fca5a5; }}
  main {{ padding:24px; max-width:1400px; margin:0 auto; }}
  .controls {{ display:flex; gap:10px; flex-wrap:wrap; margin-bottom:14px; align-items:center; }}
  .controls input, .controls select {{ background:#1e293b; color:#e2e8f0; border:1px solid #334155; padding:6px 10px; border-radius:4px; font-size:13px; }}
  .controls input {{ min-width:240px; }}
  .controls .count {{ color:#94a3b8; font-size:12px; }}
  table {{ width:100%; border-collapse:collapse; background:#0a0f1f; font-size:12px; }}
  th, td {{ text-align:left; padding:6px 10px; border-bottom:1px solid #1f2a44; }}
  th {{ background:#1e293b; cursor:pointer; user-select:none; position:sticky; top:0; }}
  th:hover {{ background:#334155; }}
  th .arrow {{ color:#7dd3fc; margin-left:4px; font-size:10px; }}
  td.k, td.pool, td.i2, td.qp, td.tau2 {{ font-family:JetBrains Mono,monospace; }}
  td.scale {{ font-family:JetBrains Mono,monospace; color:#7dd3fc; font-size:11px; }}
  td a {{ color:#e2e8f0; text-decoration:none; font-family:JetBrains Mono,monospace; font-size:11px; }}
  td a:hover {{ color:#7dd3fc; text-decoration:underline; }}
  tr.sig-benefit td.pool {{ color:#86efac; font-weight:600; }}
  tr.sig-harm td.pool {{ color:#fca5a5; font-weight:600; }}
  .floor-yes {{ background:#15803d; color:#fff; padding:1px 6px; border-radius:3px; font-size:10px; }}
  .floor-no {{ color:#64748b; }}
  footer {{ padding:14px 24px; background:#0a0f1f; border-top:1px solid #1f2a44; color:#94a3b8; font-size:11px; max-width:1400px; margin:0 auto; }}
  footer code {{ background:#1e293b; padding:1px 4px; border-radius:3px; }}
</style>
</head>
<body>
<header>
  <h1>Portfolio pools — every R-validated meta-analysis in this corpus</h1>
  <div class="desc">
    Each row is one topic's pooled estimate from <code>outputs/r_validation/*.json</code> (binary OR)
    or <code>outputs/r_validation/continuous/*.json</code> (MD/HR/OR/RR/RD). Methodology:
    REML &tau;<sup>2</sup>, HKSJ variance scaling with floor at 1 (Wiksten 2016),
    prediction interval via t<sub>(k-1)</sub> per Cochrane Handbook v6.5. Significance
    coding: 95% CI fully below null = benefit (green); fully above = harm (red).
  </div>
  {summary_row}
</header>
<main>
<div class="controls">
  <input id="search" type="text" placeholder="Filter by topic name…" aria-label="Filter by topic name">
  <select id="scale-filter" aria-label="Filter by scale">
    <option value="">All scales</option>
    <option value="OR">OR (binary)</option>
    <option value="MD">MD</option>
    <option value="HR">HR</option>
    <option value="RR">RR</option>
    <option value="RD">RD</option>
  </select>
  <select id="k-filter" aria-label="Filter by k tier">
    <option value="">All k</option>
    <option value="2-3">k = 2-3</option>
    <option value="4-10">k = 4-10</option>
    <option value="10+">k &gt; 10</option>
  </select>
  <span class="count" id="visible-count"></span>
</div>
<table>
  <thead>
    <tr>
      <th onclick="sortBy('stem')">Topic <span class="arrow"></span></th>
      <th onclick="sortBy('scale')">Scale <span class="arrow"></span></th>
      <th onclick="sortBy('k')">k <span class="arrow"></span></th>
      <th onclick="sortBy('pool')">Pooled <span class="arrow"></span></th>
      <th>95% CI</th>
      <th>95% PI</th>
      <th onclick="sortBy('i2')">I&sup2; <span class="arrow"></span></th>
      <th onclick="sortBy('qp')">Q p-val <span class="arrow"></span></th>
      <th onclick="sortBy('tau2')">&tau;&sup2; <span class="arrow"></span></th>
      <th>HKSJ floor</th>
    </tr>
  </thead>
  <tbody id="rows">
  {body}
  </tbody>
</table>
</main>
<footer>
  Generated by <code>scripts/build_portfolio_pools_dashboard.py</code> · Total rows: {len(rows):,} ·
  <a href="index.html" style="color:#7dd3fc;">back to portfolio index</a>
</footer>
<script>
  const tbody = document.getElementById('rows');
  const search = document.getElementById('search');
  const scaleF = document.getElementById('scale-filter');
  const kF = document.getElementById('k-filter');
  const visCount = document.getElementById('visible-count');
  let sortKey = null;
  let sortAsc = true;

  function applyFilters() {{
    const q = search.value.toLowerCase();
    const s = scaleF.value;
    const k = kF.value;
    let visible = 0;
    for (const tr of tbody.children) {{
      const stem = tr.dataset.stem;
      const scale = tr.dataset.scale;
      const kVal = +tr.dataset.k;
      let show = (!q || stem.includes(q));
      if (show && s) show = scale === s;
      if (show && k) {{
        if (k === '2-3') show = kVal >= 2 && kVal <= 3;
        else if (k === '4-10') show = kVal >= 4 && kVal <= 10;
        else if (k === '10+') show = kVal > 10;
      }}
      tr.style.display = show ? '' : 'none';
      if (show) visible++;
    }}
    visCount.textContent = visible + ' visible';
  }}

  function sortBy(key) {{
    const rows = Array.from(tbody.children);
    sortAsc = (sortKey === key) ? !sortAsc : true;
    sortKey = key;
    rows.sort((a, b) => {{
      let av, bv;
      if (key === 'stem' || key === 'scale') {{
        av = a.dataset[key] || ''; bv = b.dataset[key] || '';
        return sortAsc ? av.localeCompare(bv) : bv.localeCompare(av);
      }}
      const cellMap = {{ k: 2, pool: 3, i2: 6, qp: 7, tau2: 8 }};
      const idx = cellMap[key];
      const ap = parseFloat(a.cells[idx].textContent.replace('%','').replace(/[^\\d.\\-eE]/g, '')) || -Infinity;
      const bp = parseFloat(b.cells[idx].textContent.replace('%','').replace(/[^\\d.\\-eE]/g, '')) || -Infinity;
      return sortAsc ? ap - bp : bp - ap;
    }});
    tbody.replaceChildren(...rows);
    // Update arrow
    document.querySelectorAll('th .arrow').forEach(a => a.textContent = '');
    const th = Array.from(document.querySelectorAll('th'))
      .find(t => t.getAttribute('onclick') && t.getAttribute('onclick').includes(`'${{key}}'`));
    if (th) th.querySelector('.arrow').textContent = sortAsc ? '▲' : '▼';
  }}

  search.addEventListener('input', applyFilters);
  scaleF.addEventListener('change', applyFilters);
  kF.addEventListener('change', applyFilters);
  applyFilters();
</script>
</body>
</html>
""", encoding="utf-8")
    print(f"\nWrote {out.relative_to(HERE)} ({out.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
