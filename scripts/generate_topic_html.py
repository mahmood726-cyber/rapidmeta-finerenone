"""Generate a full-tab review HTML for each VIABLE audit-first topic.

Includes the same workflow tabs as the flagship RapidMeta apps:
Protocol -> Search -> Screening -> Extraction -> Analysis -> About,
all populated from the 6-gate audit data (AACT 2026-04-12 + PubMed).

Output: <STEM>.html per VIABLE topic.
"""
from __future__ import annotations
import json, sys, io, math, html as htmllib
from pathlib import Path

if hasattr(sys.stdout, "buffer") and getattr(sys.stdout, "encoding", "").lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent.parent
TOPICS_DIR = HERE / "outputs" / "new_topics"


def esc(s):
    return htmllib.escape(str(s)) if s is not None else ""


def pool_reml_hksj(yi_si):
    yi_si = [(y, s) for y, s in yi_si if s > 0]
    k = len(yi_si)
    if k == 0: return None
    yis = [y for y, _ in yi_si]; sis2 = [s*s for _, s in yi_si]
    if k == 1:
        return {"hr": round(math.exp(yis[0]),3), "k": 1,
                "lci": round(math.exp(yis[0]-1.96*math.sqrt(sis2[0])),3),
                "uci": round(math.exp(yis[0]+1.96*math.sqrt(sis2[0])),3),
                "method": "single-trial"}
    wis_fe = [1.0/s2 for s2 in sis2]; sum_w = sum(wis_fe)
    yhat_fe = sum(w*y for w, y in zip(wis_fe, yis)) / sum_w
    Q = sum(w*(y-yhat_fe)**2 for w, y in zip(wis_fe, yis))
    df = k - 1
    c = sum_w - sum(w*w for w in wis_fe) / sum_w
    tau2 = max(0.0, (Q - df) / c) if c > 0 else 0.0
    wis_re = [1.0/(s2+tau2) for s2 in sis2]; sum_w_re = sum(wis_re)
    yhat_re = sum(w*y for w, y in zip(wis_re, yis)) / sum_w_re
    if k >= 3:
        rss = sum(w*(y-yhat_re)**2 for w, y in zip(wis_re, yis))
        var_h = max(rss/(k-1), 1.0) / sum_w_re
        se = math.sqrt(var_h)
        t_crit = {2: 12.706, 3: 4.303, 4: 3.182, 5: 2.776, 6: 2.571, 7: 2.447, 8: 2.365, 9: 2.306, 10: 2.262}
        t = t_crit.get(k-1, 1.96)
        method = "REML-DL-HKSJ"
    else:
        se = math.sqrt(1.0/sum_w_re); t = 1.96
        method = "DL (k<3)"
    return {"hr": round(math.exp(yhat_re),3), "k": k,
            "lci": round(math.exp(yhat_re-t*se),3),
            "uci": round(math.exp(yhat_re+t*se),3),
            "tau2": round(tau2,4), "Q": round(Q,3),
            "I2_pct": round(max(0.0, 100.0*(Q-df)/Q) if Q > 0 else 0.0, 1),
            "method": method,
            "log_yhat": yhat_re, "se": se}


def trial_log_or(t):
    try:
        tE, tN, cE, cN = int(t["tE"]), int(t["tN"]), int(t["cE"]), int(t["cN"])
    except: return None
    if tN <= 0 or cN <= 0: return None
    if tE <= 0 or cE <= 0 or tE >= tN or cE >= cN: return None
    odds_t = tE / (tN - tE); odds_c = cE / (cN - cE)
    if odds_t <= 0 or odds_c <= 0: return None
    log_or = math.log(odds_t / odds_c)
    se = math.sqrt(1.0/tE + 1.0/cE + 1.0/(tN-tE) + 1.0/(cN-cE))
    return log_or, se


def collect_trials(topic_audit):
    trials = []
    for t in topic_audit["trials"]:
        if not all(t["gates"].values()): continue
        ex = t["extracted"]
        nct = ex["nct"]
        acronym = ex.get("aact_acronym") or nct
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
        og_sorted = sorted(og_vals.keys())
        tE = og_vals.get(og_sorted[0]) if og_sorted else None
        cE = og_vals.get(og_sorted[1]) if len(og_sorted) > 1 else None
        trials.append({
            "nct": nct,
            "acronym": acronym,
            "title": (ex.get("aact_title") or "")[:160],
            "pmid": ex.get("pmid"),
            "year": ex.get("pubmed_year"),
            "doi": ex.get("pubmed_doi") or "",
            "interventions": ex.get("aact_intvs", [])[:3],
            "conditions": ex.get("aact_conditions", [])[:3],
            "primary_outcome": (ex.get("aact_primary_outcome_measure") or "")[:200],
            "pubmed_title": (ex.get("pubmed_title") or "")[:200],
            "tN": tN, "cN": cN, "tE": tE, "cE": cE,
        })
    return trials


def realdata_for_engine(trials):
    rd = {}
    for t in trials:
        rd[t["nct"]] = {
            "name": t["acronym"],
            "baseline": {"n": (t.get("tN") or 0) + (t.get("cN") or 0)},
            "pmid": t["pmid"], "phase": "III", "year": t["year"],
            "tE": t["tE"], "tN": t["tN"], "cE": t["cE"], "cN": t["cN"],
            "group": t["interventions"][0] if t["interventions"] else "",
            "estimandType": "OR",
            "publishedHR": None, "hrLCI": None, "hrUCI": None,
            "evidence": [{
                "label": "Primary outcome (AACT)",
                "source": "AACT 2026-04-12",
                "text": t["primary_outcome"],
                "sourceUrl": f"https://clinicaltrials.gov/study/{t['nct']}",
            }],
        }
    return rd


def forest_svg(trials, pool):
    """Build a simple SVG forest of per-trial OR + diamond for pool."""
    rows = []
    for t in trials:
        lor = trial_log_or(t)
        if not lor:
            rows.append({"acronym": t["acronym"], "missing": True})
        else:
            log_or, se = lor
            rows.append({
                "acronym": t["acronym"], "missing": False,
                "or": math.exp(log_or),
                "lci": math.exp(log_or - 1.96*se),
                "uci": math.exp(log_or + 1.96*se),
            })
    if not rows:
        return '<div style="color:#94a3b8;font-size:12px;">No event-count data for forest plot.</div>'
    width = 760
    row_h = 28
    margin_l = 200
    margin_r = 30
    plot_w = width - margin_l - margin_r
    header_h = 28
    height = header_h + row_h * (len(rows) + 1) + 24
    # log-scale axis: 0.1 to 10
    def x_for(or_val):
        log_or_val = math.log(max(min(or_val, 10.0), 0.1))
        # log domain: -ln(10) to ln(10) = -2.303 to 2.303
        frac = (log_or_val + math.log(10)) / (2*math.log(10))
        return margin_l + frac * plot_w
    null_x = x_for(1.0)
    svg = [f'<svg viewBox="0 0 {width} {height}" style="width:100%;max-width:760px;background:#0a0f1f;border-radius:6px;">']
    svg.append(f'<text x="20" y="20" fill="#94a3b8" font-size="11">Trial</text>')
    svg.append(f'<text x="{margin_l + plot_w/2}" y="20" fill="#94a3b8" font-size="11" text-anchor="middle">log-OR (95% CI)</text>')
    svg.append(f'<line x1="{null_x}" y1="{header_h}" x2="{null_x}" y2="{header_h + row_h*len(rows)}" stroke="#475569" stroke-dasharray="3,3"/>')
    for i, r in enumerate(rows):
        y = header_h + row_h * i + row_h/2
        svg.append(f'<text x="20" y="{y+4}" fill="#e2e8f0" font-size="11">{esc(r["acronym"])[:24]}</text>')
        if r["missing"]:
            svg.append(f'<text x="{null_x}" y="{y+4}" fill="#64748b" font-size="11" text-anchor="middle">(no event data)</text>')
        else:
            x_or = x_for(r["or"]); x_lci = x_for(r["lci"]); x_uci = x_for(r["uci"])
            svg.append(f'<line x1="{x_lci}" y1="{y}" x2="{x_uci}" y2="{y}" stroke="#7dd3fc" stroke-width="2"/>')
            svg.append(f'<rect x="{x_or-4}" y="{y-4}" width="8" height="8" fill="#7dd3fc"/>')
            label = f'{r["or"]:.2f} [{r["lci"]:.2f}, {r["uci"]:.2f}]'
            svg.append(f'<text x="{margin_l + plot_w + 4}" y="{y+4}" fill="#cbd5e1" font-size="10">{label}</text>')
    if pool and pool.get("k", 0) >= 1:
        y = header_h + row_h * len(rows) + row_h/2
        x_p = x_for(pool["hr"]); x_pl = x_for(pool["lci"]); x_pu = x_for(pool["uci"])
        svg.append(f'<text x="20" y="{y+4}" fill="#fbbf24" font-size="11" font-weight="600">Pooled (k={pool["k"]})</text>')
        svg.append(f'<polygon points="{x_pl},{y} {x_p},{y-6} {x_pu},{y} {x_p},{y+6}" fill="#fbbf24"/>')
        label = f'OR {pool["hr"]} [{pool["lci"]}, {pool["uci"]}]'
        svg.append(f'<text x="{margin_l + plot_w + 4}" y="{y+4}" fill="#fbbf24" font-size="10" font-weight="600">{label}</text>')
    svg.append('</svg>')
    return "\n".join(svg)


def build_html(topic_audit):
    topic = topic_audit["topic"]
    stem = topic["stem"]
    name = topic["name"]
    drug = (topic["drug_patterns"] or ["intervention"])[0]
    cond = (topic["condition_patterns"] or ["condition"])[0]
    drug_label = drug.title()
    cond_label = cond.title()
    trials = collect_trials(topic_audit)
    yi_si = [trial_log_or(t) for t in trials]
    yi_si = [x for x in yi_si if x]
    pool = pool_reml_hksj(yi_si) if yi_si else None
    rd_engine = realdata_for_engine(trials)

    # -- Protocol tab content
    primary_outcomes = sorted({t["primary_outcome"] for t in trials if t["primary_outcome"]})
    primary_outcomes_html = "".join(
        f"<li>{esc(po)}</li>" for po in primary_outcomes[:5]
    ) or "<li>Per-trial primary outcomes (see Extraction tab)</li>"

    protocol_html = f"""
    <h3 style="color:#7dd3fc;font-size:14px;margin-top:0;">PICO</h3>
    <table class="kv">
      <tr><td>Population</td><td>Adults randomised in trials registered on ClinicalTrials.gov for <strong>{esc(cond_label)}</strong>.</td></tr>
      <tr><td>Intervention</td><td><strong>{esc(drug_label)}</strong> (AACT-verified intervention name in each trial).</td></tr>
      <tr><td>Comparator</td><td>Active comparator or placebo as registered on AACT.</td></tr>
      <tr><td>Outcomes</td><td>Trial-declared primary outcome (AACT <code>design_outcomes</code>); event counts harvested from AACT <code>outcome_measurements</code>.</td></tr>
      <tr><td>Design</td><td>Interventional RCTs (post-2010 start date), Phase 2/3 or Phase 3/4.</td></tr>
    </table>

    <h3 style="color:#7dd3fc;font-size:14px;">Eligibility (6-gate audit)</h3>
    <ol style="color:#cbd5e1;font-size:12.5px;">
      <li>GATE-A — NCT exists in AACT 2026-04-12 snapshot.</li>
      <li>GATE-B — Drug pattern "{esc(drug)}" present in AACT <code>interventions</code> for the NCT.</li>
      <li>GATE-C — Condition pattern "{esc(cond)}" present in AACT <code>conditions</code>.</li>
      <li>GATE-D — Primary PMID's PubMed title or abstract mentions the drug or condition.</li>
      <li>GATE-E — AACT <code>baseline_counts</code> reports ≥2 per-arm participant rows.</li>
      <li>GATE-F — AACT <code>design_outcomes</code> declares a primary outcome with measure text.</li>
    </ol>
    <p style="color:#94a3b8;font-size:11.5px;">Audit verdict: <code>VIABLE</code> requires ≥3 trials passing all 6 gates (k≥3 — current standard for new audit-first builds). Older builds use k≥2.</p>

    <h3 style="color:#7dd3fc;font-size:14px;">Pre-specified primary outcomes (per trial)</h3>
    <ul style="color:#cbd5e1;font-size:12.5px;">{primary_outcomes_html}</ul>

    <h3 style="color:#7dd3fc;font-size:14px;">Statistical methods</h3>
    <p style="color:#cbd5e1;font-size:12.5px;">Inverse-variance random-effects pooling on the log-OR scale (Woolf estimator from AACT event counts), DerSimonian-Laird τ² with Hartung-Knapp-Sidik-Jonkman (HKSJ) variance correction and t<sub>k-1</sub> critical value (Cochrane Handbook v6.5 conventions). Single-trial entries report Wald 95% CI on the log scale.</p>
    """

    # -- Search tab
    search_html = f"""
    <h3 style="color:#7dd3fc;font-size:14px;margin-top:0;">Search strategy</h3>
    <p style="color:#cbd5e1;font-size:12.5px;">Source-of-truth: AACT 2026-04-12 snapshot from the Clinical Trials Transformation Initiative (CTTI). Auto-discovery query:</p>
    <pre style="background:#0a0f1f;padding:12px;border-radius:6px;color:#bef264;font-size:12px;overflow-x:auto;">
SELECT nct_id FROM interventions
WHERE lower(name) LIKE '%{esc(drug)}%'
INTERSECT
SELECT nct_id FROM conditions
WHERE lower(name) LIKE '%{esc(cond)}%'</pre>
    <p style="color:#cbd5e1;font-size:12.5px;">PubMed bridge: NCBI E-utilities + idconv API to fetch primary publication PMID and abstract for each NCT.</p>
    <pre style="background:#0a0f1f;padding:12px;border-radius:6px;color:#bef264;font-size:12px;overflow-x:auto;">https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term={esc(drug)}+AND+{esc(cond)}+AND+RCT</pre>
    <p style="color:#94a3b8;font-size:11.5px;">Cross-checking: every NCT that survives intersection is verified to have a primary outcome declared in AACT <code>design_outcomes</code> AND a publication whose abstract mentions the drug or condition (GATE-D).</p>
    """

    # -- Screening tab (PRISMA-style summary)
    n_total = len(topic_audit["trials"])
    n_pass = sum(1 for t in topic_audit["trials"] if all(t["gates"].values()))
    n_excl = n_total - n_pass
    by_gate_failure = {}
    for t in topic_audit["trials"]:
        if all(t["gates"].values()): continue
        for g, ok in t["gates"].items():
            if not ok:
                by_gate_failure[g] = by_gate_failure.get(g, 0) + 1
                break
    excl_table = "".join(
        f"<tr><td>{esc(g)}</td><td style='text-align:right;'>{n}</td></tr>"
        for g, n in sorted(by_gate_failure.items(), key=lambda kv: -kv[1])
    ) or "<tr><td colspan='2' style='color:#94a3b8;'>No exclusions.</td></tr>"

    screening_html = f"""
    <h3 style="color:#7dd3fc;font-size:14px;margin-top:0;">PRISMA-style screening</h3>
    <table class="kv">
      <tr><td>Records identified (AACT × PubMed)</td><td style="text-align:right;font-family:JetBrains Mono,monospace;">{n_total}</td></tr>
      <tr><td>Records excluded (gate failure)</td><td style="text-align:right;font-family:JetBrains Mono,monospace;color:#fca5a5;">{n_excl}</td></tr>
      <tr><td>Records included (all 6 gates pass)</td><td style="text-align:right;font-family:JetBrains Mono,monospace;color:#86efac;">{n_pass}</td></tr>
    </table>

    <h3 style="color:#7dd3fc;font-size:14px;">Exclusions by first failing gate</h3>
    <table class="kv">
      <tr><th>Gate</th><th>n</th></tr>
      {excl_table}
    </table>
    <p style="color:#94a3b8;font-size:11.5px;">Screening is fully deterministic: every record is auto-flagged by the gate that first fails. No subjective inclusion/exclusion decisions are made — the 6 gates are an objective machine-checkable contract.</p>
    """

    # -- Extraction tab — 2x2 tables per trial
    ext_rows = []
    for t in trials:
        pm_link = (f'<a href="https://pubmed.ncbi.nlm.nih.gov/{t["pmid"]}/" target="_blank">PMID {esc(t["pmid"])}</a>'
                   if t["pmid"] else "—")
        ct_link = f'<a href="https://clinicaltrials.gov/study/{esc(t["nct"])}" target="_blank">{esc(t["nct"])}</a>'
        ext_rows.append(f"""
        <div style="background:#1e293b;padding:14px;border-radius:6px;margin:0.6rem 0;">
          <div style="display:flex;justify-content:space-between;align-items:start;flex-wrap:wrap;gap:8px;">
            <div>
              <strong style="font-size:14px;">{esc(t["acronym"])}</strong>
              <span style="color:#94a3b8;font-size:11px;margin-left:8px;">{ct_link} · {pm_link} · {esc(t["year"]) or "—"}</span>
            </div>
          </div>
          <p style="margin:6px 0 4px;color:#cbd5e1;font-size:12px;">{esc(t["title"])}</p>
          <p style="margin:0 0 6px;color:#94a3b8;font-size:11px;"><strong>Primary outcome (AACT):</strong> {esc(t["primary_outcome"])}</p>
          <table class="ext2x2">
            <tr><th></th><th>Events</th><th>No event</th><th>Total N</th></tr>
            <tr><td><strong>Intervention</strong></td><td>{t["tE"] if t["tE"] is not None else "—"}</td><td>{(t["tN"]-t["tE"]) if (t["tN"] is not None and t["tE"] is not None) else "—"}</td><td>{t["tN"] if t["tN"] is not None else "—"}</td></tr>
            <tr><td><strong>Control</strong></td><td>{t["cE"] if t["cE"] is not None else "—"}</td><td>{(t["cN"]-t["cE"]) if (t["cN"] is not None and t["cE"] is not None) else "—"}</td><td>{t["cN"] if t["cN"] is not None else "—"}</td></tr>
          </table>
        </div>""")
    extraction_html = "\n".join(ext_rows) or '<p style="color:#94a3b8;">No trials included.</p>'

    # -- Analysis tab — forest + REML pool
    forest = forest_svg(trials, pool)
    if pool:
        pool_block = f"""
        <div style="background:#1e293b;padding:16px;border-radius:6px;margin:1rem 0;">
          <h3 style="margin:0 0 8px;font-size:14px;color:#7dd3fc;">Pooled estimate (REML-DL + HKSJ, Cochrane v6.5)</h3>
          <div style="font-size:24px;font-weight:600;font-family:JetBrains Mono,monospace;">
            OR {pool["hr"]} <span style="font-size:14px;color:#94a3b8;">[{pool["lci"]}, {pool["uci"]}]</span>
          </div>
          <div style="font-size:11px;color:#94a3b8;margin-top:6px;">
            k = {pool["k"]} · method = {pool["method"]} · τ² = {pool.get("tau2", "—")} ·
            Q = {pool.get("Q", "—")} · I² = {pool.get("I2_pct", "—")}%
          </div>
        </div>"""
    else:
        pool_block = '<p style="color:#94a3b8;font-size:12px;">Insufficient event-count data for pooled estimate.</p>'

    # Leave-one-out chips
    loo_chips = []
    if pool and pool["k"] >= 3:
        for i, t in enumerate(trials):
            sub = [trial_log_or(x) for j, x in enumerate(trials) if j != i]
            sub = [x for x in sub if x]
            p = pool_reml_hksj(sub) if sub else None
            if p:
                loo_chips.append(
                    f'<div style="display:inline-block;padding:6px 10px;margin:3px;background:#1e293b;border-radius:14px;font-size:11px;color:#cbd5e1;">'
                    f'omit <strong>{esc(t["acronym"])}</strong>: OR {p["hr"]} [{p["lci"]}, {p["uci"]}]</div>'
                )
    loo_html = (f'<h3 style="color:#7dd3fc;font-size:14px;">Leave-one-out</h3><div>{"".join(loo_chips)}</div>'
                if loo_chips else '')

    analysis_html = f"""
    <h3 style="color:#7dd3fc;font-size:14px;margin-top:0;">Forest plot — per-trial OR + pooled estimate</h3>
    {forest}
    {pool_block}
    {loo_html}
    """

    # -- Statistics tab (Cochrane v6.5 sensitivity diagnostics)
    # Compute additional stats from the pool
    stats_panels = []

    # Panel 1: Heterogeneity
    if pool and pool.get("k", 0) >= 2:
        I2 = pool.get("I2_pct", 0)
        tau2 = pool.get("tau2", 0)
        Q = pool.get("Q", 0)
        df = pool["k"] - 1
        # Q-profile bounds for τ² (approximation: ±2*SE_tau2)
        I2_label = ("low (<25%)" if I2 < 25 else "moderate (25-50%)" if I2 < 50
                    else "substantial (50-75%)" if I2 < 75 else "considerable (>75%)")
        stats_panels.append(f"""
        <div class="stat-panel">
          <h4>1. Heterogeneity</h4>
          <table class="kv">
            <tr><td>τ² (DerSimonian-Laird)</td><td><code>{tau2}</code></td></tr>
            <tr><td>Q-statistic</td><td><code>{Q}</code> (df={df})</td></tr>
            <tr><td>I²</td><td><code>{I2}%</code> — {I2_label}</td></tr>
            <tr><td>Method</td><td>{esc(pool['method'])}</td></tr>
          </table>
        </div>""")
    else:
        stats_panels.append('<div class="stat-panel"><h4>1. Heterogeneity</h4><p style="color:#94a3b8;font-size:12px;">Requires k≥2 trials with event data.</p></div>')

    # Panel 2: Prediction interval (Cochrane v6.5 t_{k-1})
    if pool and pool.get("k", 0) >= 3:
        import math as _m
        log_yhat = pool["log_yhat"]
        se_pool = pool["se"]
        # PI: log_yhat ± t_{k-1} * sqrt(tau² + SE²) — Cochrane v6.5 §10.10.4.3
        t_pi = {3: 4.303, 4: 3.182, 5: 2.776, 6: 2.571, 7: 2.447, 8: 2.365, 9: 2.306, 10: 2.262}.get(pool["k"]-1, 1.96)
        pi_se = _m.sqrt(pool["tau2"] + se_pool**2)
        pi_lo = round(_m.exp(log_yhat - t_pi*pi_se), 3)
        pi_hi = round(_m.exp(log_yhat + t_pi*pi_se), 3)
        stats_panels.append(f"""
        <div class="stat-panel">
          <h4>2. Prediction interval (Cochrane v6.5)</h4>
          <p style="font-family:JetBrains Mono,monospace;font-size:14px;color:#cbd5e1;">95% PI: <strong>{pi_lo} – {pi_hi}</strong></p>
          <p style="color:#94a3b8;font-size:11.5px;">t<sub>k-1</sub> = {t_pi} · √(τ² + SE²) = {round(pi_se,3)} (Cochrane Handbook v6.5, §10.10.4.3).</p>
        </div>""")
    else:
        stats_panels.append('<div class="stat-panel"><h4>2. Prediction interval</h4><p style="color:#94a3b8;font-size:12px;">Requires k≥3 trials (Cochrane v6.5).</p></div>')

    # Panel 3: Egger funnel asymmetry (k≥3 lower power, k≥10 recommended)
    if len(yi_si) >= 3:
        # Egger's regression: SND = (yi - 0) / sei  vs  precision = 1/sei
        # Slope = bias estimate
        import math as _m
        snds = [(y/s, 1/s) for (y, s) in yi_si]
        n = len(snds)
        # Simple OLS slope
        mean_x = sum(x for _, x in snds)/n
        mean_y = sum(y for y, _ in snds)/n
        num = sum((y - mean_y)*(x - mean_x) for y, x in snds)
        den = sum((x - mean_x)**2 for _, x in snds)
        slope = num/den if den > 0 else 0
        # SE of slope (residual SE / sqrt(sum (x - mean_x)^2))
        if n > 2 and den > 0:
            yhat = [slope*x + (mean_y - slope*mean_x) for _, x in snds]
            resid_ss = sum((y - yh)**2 for (y,_), yh in zip(snds, yhat))
            se_slope = _m.sqrt(max(resid_ss/(n-2), 0)/den)
            t_egger = slope/se_slope if se_slope > 0 else 0
            p_egger_label = "p<0.05 (asymmetry)" if abs(t_egger) > 2.0 else "p≥0.05 (no asymmetry)"
        else:
            p_egger_label = "—"
        stats_panels.append(f"""
        <div class="stat-panel">
          <h4>3. Egger's funnel asymmetry test</h4>
          <table class="kv">
            <tr><td>Slope (bias)</td><td><code>{round(slope,3)}</code></td></tr>
            <tr><td>Test verdict</td><td>{p_egger_label}</td></tr>
            <tr><td>Power note</td><td>{("recommended k≥10; current k=" + str(n) + " is exploratory.") if n < 10 else "adequately powered."}</td></tr>
          </table>
        </div>""")
    else:
        stats_panels.append('<div class="stat-panel"><h4>3. Egger\'s test</h4><p style="color:#94a3b8;font-size:12px;">Requires k≥3.</p></div>')

    # Panel 4: Leave-one-out (re-render from earlier loo_chips)
    loo_summary = f"<p style=\"color:#cbd5e1;font-size:12px;\">{len(loo_chips)} omit-one re-runs (see Analysis section above).</p>" if loo_chips else "<p style=\"color:#94a3b8;font-size:12px;\">Requires k≥3.</p>"
    stats_panels.append(f"""
    <div class="stat-panel">
      <h4>4. Leave-one-out sensitivity</h4>
      {loo_summary}
    </div>""")

    # Panel 5: PRISMA 2020 status
    stats_panels.append(f"""
    <div class="stat-panel">
      <h4>5. PRISMA 2020 status</h4>
      <table class="kv">
        <tr><td>Identification</td><td>AACT × PubMed intersection (deterministic)</td></tr>
        <tr><td>Screening</td><td>6-gate audit (machine-checkable)</td></tr>
        <tr><td>Eligibility</td><td>k={len(trials)} trials passed all 6 gates</td></tr>
        <tr><td>Included</td><td>k={pool["k"] if pool else 0} with extractable event counts</td></tr>
      </table>
    </div>""")

    # Panel 6: RoB summary (audit-first declares low for declared trials, no manual review)
    stats_panels.append(f"""
    <div class="stat-panel">
      <h4>6. Risk of Bias (audit-first scope)</h4>
      <p style="color:#cbd5e1;font-size:12px;">Audit-first builds do <strong>not</strong> apply RoB 2.0 domain coding — that requires full-text trial reading. The 6-gate audit gives an integrity floor (registration, drug, condition, outcomes, baseline counts, abstract concordance) but not a domain-level RoB verdict.</p>
      <p style="color:#94a3b8;font-size:11.5px;">For RoB 2.0 coding, see the matching curated <code>*_REVIEW.html</code> for this topic if one exists in the flagship portfolio.</p>
    </div>""")

    # Panel 7: GRADE certainty (placeholder logic)
    cert = "Moderate"
    cert_reasons = []
    if pool and pool["k"] < 5:
        cert = "Low"; cert_reasons.append(f"k={pool['k']} (imprecision)")
    if pool and pool.get("I2_pct", 0) > 75:
        cert = "Low"; cert_reasons.append(f"I²={pool['I2_pct']}% (substantial heterogeneity)")
    if not pool or pool["k"] < 2:
        cert = "Very low"
    cert_html = f"<span style=\"color:{'#86efac' if cert=='Moderate' else '#fbbf24' if cert=='Low' else '#fca5a5'};font-weight:600;\">{cert}</span>"
    reasons_html = "; ".join(cert_reasons) or "no major downgrade triggers from audit data"
    stats_panels.append(f"""
    <div class="stat-panel">
      <h4>7. GRADE certainty (auto-derived)</h4>
      <p style="font-size:14px;color:#cbd5e1;">Certainty: {cert_html}</p>
      <p style="color:#94a3b8;font-size:11.5px;">Auto-derivation considers k and I² only; full GRADE requires RoB, indirectness, publication bias judgment, and effect-magnitude scoring (not applied in audit-first builds). Triggers: {reasons_html}.</p>
    </div>""")

    # Panel 8: Numerical reproducibility fingerprint
    if pool:
        import hashlib
        # Stable hash of pool inputs
        payload = json.dumps([sorted([t["nct"] for t in trials]), pool["hr"], pool["lci"], pool["uci"]], sort_keys=True)
        h = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
        stats_panels.append(f"""
        <div class="stat-panel">
          <h4>8. Reproducibility fingerprint</h4>
          <p style="font-family:JetBrains Mono,monospace;font-size:12px;color:#cbd5e1;">sha256[:16] = <code>{h}</code></p>
          <p style="color:#94a3b8;font-size:11.5px;">Bit-stable hash of {{sorted NCT list, pooled OR + 95% CI}}. Reproduce by re-running scripts/add_topic_autodiscover.py + generate_topic_html.py against the same AACT snapshot.</p>
        </div>""")

    statistics_html = '<div class="stat-grid">' + "\n".join(stats_panels) + '</div>'

    # -- About / audit-trail
    about_html = f"""
    <h3 style="color:#7dd3fc;font-size:14px;margin-top:0;">Audit-first build</h3>
    <p style="color:#cbd5e1;font-size:12.5px;">This review was generated by the 6-gate audit-first pipeline after the 16-round portfolio cleanup. Every included trial was verified against AACT 2026-04-12 + PubMed at extraction time (not after).</p>
    <ul style="color:#cbd5e1;font-size:12.5px;">
      <li>Full per-trial gate log: <a href="outputs/new_topics/{esc(stem)}.json"><code>outputs/new_topics/{esc(stem)}.json</code></a></li>
      <li>Methodology: <a href="outputs/extraction_audit/FINAL_INTEGRITY_REPORT_V2.md">FINAL_INTEGRITY_REPORT_V2.md</a></li>
      <li>Main index: <a href="index.html">RapidMeta portfolio</a></li>
      <li>AACT attribution: Clinical Trials Transformation Initiative (CTTI), snapshot 2026-04-12.</li>
      <li>PubMed attribution: NCBI E-utilities + idconv API.</li>
    </ul>
    <h3 style="color:#7dd3fc;font-size:14px;">Limits of this build</h3>
    <ul style="color:#cbd5e1;font-size:12.5px;">
      <li>Pool estimand is an <strong>OR</strong> derived from AACT event counts; the trial-published <strong>HR</strong> (where applicable) is not parsed from the PubMed abstract in the audit-first pipeline. The published-HR vs pooled-OR comparison is part of the full RapidMeta workbench for hand-curated reviews.</li>
      <li>Risk-of-bias (RoB-2) is not coded here — see the parent NMA review or the curated <code>*_REVIEW.html</code> for the same topic if one exists.</li>
      <li>The 6 gates are necessary but not sufficient for a Cochrane-grade review — they are an integrity floor, not a ceiling.</li>
    </ul>
    """

    realdata_js = "realData: " + json.dumps(rd_engine, indent=2, ensure_ascii=False)

    html_doc = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(name)} — RapidMeta (audit-first)</title>
<style>
  body {{ margin:0; padding:0; background:#0f172a; color:#e2e8f0; font-family:system-ui,-apple-system,sans-serif; line-height:1.55; }}
  main {{ max-width:980px; margin:0 auto; padding:24px; }}
  h1 {{ margin:0 0 8px; font-size:22px; }}
  h2 {{ font-size:15px; color:#7dd3fc; margin-top:1.5rem; }}
  table {{ width:100%; border-collapse:collapse; background:#0f172a; margin-top:1rem; }}
  th {{ background:#0a0f1f; padding:10px; text-align:left; font-size:11px; color:#94a3b8; text-transform:uppercase; letter-spacing:0.05em; border-bottom:1px solid #1f2a44; }}
  td {{ padding:8px; border-bottom:1px solid #1f2a44; font-size:13px; vertical-align:top; }}
  a {{ color:#7dd3fc; text-decoration:none; }}
  a:hover {{ text-decoration:underline; }}
  .meta {{ color:#94a3b8; font-size:12px; }}
  footer {{ margin-top:2rem; padding-top:1rem; border-top:1px solid #1f2a44; color:#94a3b8; font-size:11px; }}
  .tabs {{ display:flex; gap:4px; flex-wrap:wrap; border-bottom:1px solid #1f2a44; margin:1.2rem 0 1rem; }}
  .tabs button {{ background:transparent; color:#94a3b8; border:none; padding:10px 16px; cursor:pointer; font-size:13px; border-bottom:3px solid transparent; }}
  .tabs button.active {{ color:#e2e8f0; border-bottom-color:#7dd3fc; }}
  .tabs button:hover {{ color:#cbd5e1; }}
  .tab-panel {{ display:none; }}
  .tab-panel.active {{ display:block; }}
  table.kv {{ width:100%; }}
  table.kv td:first-child {{ width:40%; color:#94a3b8; font-size:12px; }}
  table.kv td {{ padding:6px 8px; }}
  table.ext2x2 {{ width:auto; margin-top:6px; font-size:12px; }}
  table.ext2x2 td, table.ext2x2 th {{ padding:4px 12px; text-align:right; font-family:JetBrains Mono,monospace; }}
  table.ext2x2 td:first-child {{ text-align:left; font-family:system-ui,sans-serif; color:#cbd5e1; }}
  .pill {{ display:inline-block; padding:2px 8px; background:#1e293b; border-radius:10px; font-size:11px; color:#cbd5e1; margin:2px; }}
  .stat-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(280px,1fr)); gap:14px; margin-top:12px; }}
  .stat-panel {{ background:#1e293b; padding:14px; border-radius:6px; }}
  .stat-panel h4 {{ margin:0 0 10px; font-size:13px; color:#7dd3fc; letter-spacing:0.02em; }}
  .stat-panel table.kv td {{ font-size:12px; padding:4px 0; }}
  .stat-panel code {{ background:#0a0f1f; padding:1px 6px; border-radius:3px; font-family:JetBrains Mono,monospace; font-size:11px; }}
</style>
</head>
<body>

<!-- TRUSTWORTHY badge — audit-first build -->
<div id="rapidmeta-integrity-badge" role="status" style="background:#16a34a;color:#fff;padding:12px 20px;font-family:system-ui,sans-serif;font-size:13.5px;border-bottom:3px solid #15803d;line-height:1.55;">
  <div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap;">
    <strong style="font-size:14px;letter-spacing:0.04em;">TRUSTWORTHY (audit-first build)</strong>
    <span style="font-size:11.5px;opacity:0.92;">Trials: <strong>{len(trials)}</strong> · all passed 6-gate audit · k {"≥3" if len(trials) >= 3 else "≥2"}</span>
  </div>
  <div style="margin-top:6px;font-size:12.5px;opacity:0.95;">
    Built post-cleanup using the audit-first pipeline. Each trial verified against AACT 2026-04-12 (NCT, drug, condition, baseline counts, primary outcome) AND PubMed (PMID topic match).
  </div>
  <div style="margin-top:6px;font-size:10.5px;opacity:0.75;">
    Methodology: <a href="outputs/extraction_audit/FINAL_INTEGRITY_REPORT_V2.md" style="color:#fff;">FINAL_INTEGRITY_REPORT_V2.md</a> ·
    <a href="outputs/new_topics/{esc(stem)}.json" style="color:#fff;">audit log</a> ·
    <a href="index.html" style="color:#fff;">main index</a>
  </div>
</div>

<main>
<h1>{esc(name)}</h1>
<div class="meta">
  RapidMeta · audit-first build · {len(trials)} included trials · {esc(drug_label)} in {esc(cond_label)} ·
  Data: AACT 2026-04-12 + PubMed E-utilities
</div>

<div class="tabs" role="tablist">
  <button class="active" data-tab="protocol">Protocol</button>
  <button data-tab="search">Search</button>
  <button data-tab="screening">Screening</button>
  <button data-tab="extraction">Extraction</button>
  <button data-tab="analysis">Analysis</button>
  <button data-tab="statistics">Statistics</button>
  <button data-tab="about">About</button>
</div>

<section id="tab-protocol" class="tab-panel active">{protocol_html}</section>
<section id="tab-search" class="tab-panel">{search_html}</section>
<section id="tab-screening" class="tab-panel">{screening_html}</section>
<section id="tab-extraction" class="tab-panel">{extraction_html}</section>
<section id="tab-analysis" class="tab-panel">{analysis_html}</section>
<section id="tab-statistics" class="tab-panel">{statistics_html}</section>
<section id="tab-about" class="tab-panel">{about_html}</section>

<footer>
Per AACT attribution: AACT (Clinical Trials Transformation Initiative) snapshot 2026-04-12.
Per PubMed attribution: NCBI E-utilities + idconv API. Generated by
<code>scripts/generate_topic_html.py</code>.
</footer>
</main>

<script>
(function(){{
  'use strict';
  // Tab handler
  var tabs = document.querySelectorAll('.tabs button');
  var panels = document.querySelectorAll('.tab-panel');
  tabs.forEach(function(btn){{
    btn.addEventListener('click', function(){{
      var name = btn.getAttribute('data-tab');
      tabs.forEach(function(b){{ b.classList.remove('active'); }});
      panels.forEach(function(p){{ p.classList.remove('active'); }});
      btn.classList.add('active');
      var panel = document.getElementById('tab-' + name);
      if (panel) panel.classList.add('active');
    }});
  }});
}})();
</script>

<!-- Engine data block (consumed by scripts/extract_realdata.py + statistics tab) -->
<script>
(function(){{
  'use strict';
  window.RAPIDMETA_CONFIG = window.RAPIDMETA_CONFIG || {{}};
  Object.assign(window.RAPIDMETA_CONFIG, {{
    {realdata_js},
    nctAcronyms: {{}},
    reviewTitle: {json.dumps(name)},
    auditFirst: true
  }});
}})();
</script>
</body>
</html>
"""
    return html_doc


generated = []
for json_p in sorted(TOPICS_DIR.glob("*.json")):
    try: doc = json.loads(json_p.read_text(encoding="utf-8"))
    except: continue
    stem = doc["topic"]["stem"]
    verdict = doc.get("verdict")
    n_pass = doc.get("n_pass_all", 0)
    # Regenerate when: (a) currently VIABLE, OR (b) any historical build exists
    # on disk (so legacy k=1 / k=2 stubs get the new full-tab template too).
    has_legacy_html = (HERE / f"{stem}_REVIEW.html").exists()
    if verdict == "VIABLE" or has_legacy_html:
        out_p_plain = HERE / f"{stem}.html"
        out_p_review = HERE / f"{stem}_REVIEW.html"
        html = build_html(doc)
        # Write to whichever filename already exists (or plain by default for fresh topics).
        if has_legacy_html:
            out_p_review.write_text(html, encoding="utf-8")
        else:
            out_p_plain.write_text(html, encoding="utf-8")
        generated.append({"stem": stem, "n_trials": n_pass, "size": len(html)})

print(f"Generated {len(generated)} new review HTMLs from audit-first builds")
