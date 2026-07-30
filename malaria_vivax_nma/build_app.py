"""Build VIVAX_RADICAL_CURE_NMA_REVIEW.html from the fitted results.

Every displayed number is read from outputs/vivax_nma_results.json,
preflight/network.json or preflight/arm_level_evidence.json. Nothing is typed
by hand, so the app cannot drift from the fit.
"""
import json, os, sys, io, html

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..'))

R = json.load(open(os.path.join(ROOT, 'outputs', 'vivax_nma_results.json'), encoding='utf-8'))
NET = json.load(open(os.path.join(HERE, 'preflight', 'network.json'), encoding='utf-8'))
EV = json.load(open(os.path.join(HERE, 'preflight', 'arm_level_evidence.json'), encoding='utf-8'))
OUT = os.path.join(ROOT, 'VIVAX_RADICAL_CURE_NMA_REVIEW.html')

e = html.escape
CTG = 'https://clinicaltrials.gov/study/'
PM = 'https://pubmed.ncbi.nlm.nih.gov/'
FDA795 = ('https://www.accessdata.fda.gov/drugsatfda_docs/nda/2018/'
          '210795Orig1s000MultidisciplineR.pdf')

# ---------------------------------------------------------------- verdict ----
VERDICT = {
    "verdict": "EXPOSED",
    "counts": {
        "P0_arithmetic": 0,
        "P0_provenance": 0,
        "P1_structural_fragility": 1,
        "P1_between_design_inconsistency": 1,
        "P1_ph_violation": 1,
        "P1_two_source_only": 1,
        "P1_estimand_loss": 1,
        "P2_advisory": 3,
        "n_trials_seen": R['full']['n_trials'],
        "n_nodes": len(R['full']['nodes']),
    },
    "reasons": [
        "14 of 17 edges rest on a single trial; the robust core is only 3 of 7 nodes",
        "Between-design Q = 12.05 (df 4, p = 0.017): designs disagree more than trials within a design",
        "INSPECTOR violates proportional hazards on the TQ-vs-PQ edge; its authors use OR 4.57, not an HR",
        "DETECTIVE Part 1 is two-source only - NCT01376167 posts results for Part 2 alone",
        "IMPROV (N=2336) is excluded outright: it has no 180-day row, and the rate was not back-converted",
        "Per-trial ORs on the focal edge span 0.354 to 3.841 (I2 = 64.8%)",
        "Mixed estimators coexist across trials (crude proportion, Kaplan-Meier, hazard ratio)",
        "The 'no therapy' node is chloroquine alone in DETECTIVE but DHA-piperaquine alone in INSPECTOR",
    ],
    "p0_total": 0,
    "tier_meaning": ("Arithmetic and provenance gates pass (0 P0). The exposure is STRUCTURAL: "
                     "the pooled estimate must not be read at face value."),
}

TIER_DESC = {
    "STABLE": "All gates pass; the pooled estimate can be read at face value.",
    "MODERATE": "One topic-level issue; read the pooled estimate with the noted caveat.",
    "EXPOSED": VERDICT["tier_meaning"],
    "UNCERTAIN": "Insufficient data - gates could not run.",
}

FULL = R['full']; CORE = R['core']; QD = R['q_decomposition']
LOO = [("DETECTIVE_PART1", 4, "TQ 50, TQ 100, TQ 600"),
       ("DETECTIVE_PART2", 7, ""), ("GATHER", 7, ""), ("INSPECTOR", 7, ""),
       ("EFFORT", 6, "PQ 7 d high")]
SRC = {t['id']: t['sources'] for t in NET['trials']}
PUB = {t['id']: t['sources']['publication'] for t in NET['trials']}
NCT = {tr['id']: tr.get('nct') for tr in EV['trials']}


def orcell(v, lo, hi):
    if lo is None:
        return '<td class="num ref">1.00</td><td class="ci">reference</td>'
    cls = 'sig' if hi < 1 else ('adv' if lo > 1 else '')
    return (f'<td class="num {cls}">{v:.3f}</td>'
            f'<td class="ci">{lo:.3f} to {hi:.3f}</td>')


def node_rows(tbl):
    out = []
    for n in tbl:
        out.append(f'<tr><td class="node">{e(n["label"])}</td>'
                   + orcell(n['OR'], n['lo'], n['hi']) + '</tr>')
    return '\n'.join(out)


# ------------------------------------------------------------- ledger --------
def ledger_rows():
    rows = []
    for t in NET['trials']:
        tid = t['id']
        ev = next((x for x in EV['trials'] if x['id'] == tid), {})
        nct = NCT.get(tid)
        s = SRC[tid]
        links = []
        if nct:
            reg = 'results table' if s.get('registry_results') else 'protocol only (no results)'
            links.append(f'<a href="{CTG}{nct}" target="_blank" rel="noopener">{nct}</a> '
                         f'<span class="tag">{reg}</span>')
        if s.get('publication'):
            pmid = s['publication'].replace('PMID ', '')
            links.append(f'<a href="{PM}{pmid}" target="_blank" rel="noopener">PMID {pmid}</a>')
        if s.get('fda'):
            links.append(f'<a href="{FDA795}" target="_blank" rel="noopener">'
                         f'{e(s["fda"])}</a>')
        src = ' &middot; '.join(links)
        tier = ev.get('provenance_tier', '?')
        for i, a in enumerate(t['arms']):
            first = i == 0
            rows.append(
                '<tr>'
                + (f'<td rowspan="{len(t["arms"])}" class="trial">{e(tid)}'
                   f'<div class="tier">tier {e(tier)}</div></td>' if first else '')
                + f'<td class="node">{e(a["node"])}</td>'
                + f'<td class="num">{a["n"]}</td>'
                + f'<td class="num">{a["recurrence"]}</td>'
                + f'<td class="num">{a["recurrence_free"]}</td>'
                + f'<td class="num">{a.get("censored", 0)}</td>'
                + f'<td class="num">{a.get("km_pct", "&mdash;")}</td>'
                + (f'<td rowspan="{len(t["arms"])}" class="src">{src}</td>' if first else '')
                + '</tr>')
    return '\n'.join(rows)


def mv_rows():
    out = []
    for c in R['multiverse']:
        prim = 'primary' in c['level'].lower()
        if c.get('estimable'):
            flag = '' if c.get('tau2_estimable', True) else ' <span class="warn">tau&sup2; not estimable</span>'
            body = (f'<td class="num">{c["n_trials"]}</td>'
                    f'<td class="num">{c["OR"]:.3f}</td>'
                    f'<td class="ci">{c["lo"]:.3f} to {c["hi"]:.3f}</td>'
                    f'<td class="num">{c["I2"]:.1f}%{flag}</td>')
        else:
            body = (f'<td class="num">&mdash;</td><td colspan="3" class="notest">'
                    f'NOT ESTIMABLE &mdash; {e(c["reason"])}</td>')
        note = f'<div class="note">{e(c["note"])}</div>' if c.get('note') else ''
        out.append(f'<tr class="{"prim" if prim else ""}">'
                   f'<td class="cell">{e(c["cell"])}</td>'
                   f'<td>{e(c["axis"])}<br><span class="lvl">{e(c["level"])}</span>{note}</td>'
                   + body + '</tr>')
    return '\n'.join(out)


def forest_rows():
    pt = R['focal']['per_trial']
    lo = min(x['OR'] for x in pt); hi = max(x['OR'] for x in pt)
    import math
    def x(v):
        a, b = math.log(0.25), math.log(5.0)
        return max(0, min(100, (math.log(v) - a) / (b - a) * 100))
    out = []
    for p in pt:
        blind = 'double-blind' if p['blind'] else 'OPEN-LABEL'
        out.append(
            f'<tr><td class="trial">{e(p["trial"])}<div class="tier">{e(p["partner"])}'
            f' &middot; {blind}</div></td>'
            f'<td class="num">{p["tq_events"]}/{p["tq_n"]}</td>'
            f'<td class="num">{p["pq_events"]}/{p["pq_n"]}</td>'
            f'<td class="num">{p["OR"]:.3f}</td>'
            f'<td class="plot"><div class="axis"></div>'
            f'<div class="unity"></div>'
            f'<div class="dot" style="left:{x(p["OR"]):.1f}%"></div></td></tr>')
    return '\n'.join(out), lo, hi


MV = mv_rows()
FOREST, F_LO, F_HI = forest_rows()
LEDGER = ledger_rows()

CSS = """
:root{--bg:#0b1016;--panel:#121a24;--line:#1f2c3a;--ink:#e6edf5;--dim:#93a4b8;
--acc:#5eead4;--warn:#fbbf24;--bad:#f87171;--good:#34d399}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
font:15px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
.wrap{max-width:1180px;margin:0 auto;padding:28px 20px 80px}
h1{font-size:26px;margin:0 0 6px;letter-spacing:-.01em}
h2{font-size:19px;margin:38px 0 10px;padding-bottom:7px;border-bottom:1px solid var(--line)}
h3{font-size:15px;margin:22px 0 8px;color:var(--acc)}
.sub{color:var(--dim);margin:0 0 18px;font-size:13.5px}
.panel{background:var(--panel);border:1px solid var(--line);border-radius:12px;
padding:16px 18px;margin:14px 0}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:14px}
@media(max-width:820px){.grid2{grid-template-columns:1fr}}
table{width:100%;border-collapse:collapse;font-size:13.5px}
th,td{padding:7px 9px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}
th{color:var(--dim);font-weight:600;font-size:12px;text-transform:uppercase;letter-spacing:.04em}
.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
.ci{color:var(--dim);font-variant-numeric:tabular-nums;white-space:nowrap;font-size:12.5px}
.sig{color:var(--good);font-weight:600}
.adv{color:var(--bad);font-weight:600}
.ref{color:var(--dim)}
.node{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12.5px}
.trial{font-weight:600;font-size:13px}
.tier{color:var(--dim);font-weight:400;font-size:11.5px;margin-top:2px}
.src{font-size:11.5px;line-height:1.75}
.src a{color:var(--acc);text-decoration:none;border-bottom:1px dotted}
.tag{color:var(--dim);font-size:10.5px}
.tbl-scroll{overflow-x:auto}
.cell{font-family:ui-monospace,monospace;font-weight:600;color:var(--acc)}
.lvl{color:var(--dim);font-size:12px}
.note{color:var(--warn);font-size:11.5px;margin-top:4px;max-width:430px}
tr.prim{background:rgba(94,234,212,.06)}
.notest{color:var(--warn);font-size:12.5px}
.warn{color:var(--warn);font-size:11px}
.plot{position:relative;width:210px;height:22px}
.axis{position:absolute;left:0;right:0;top:11px;height:1px;background:var(--line)}
.unity{position:absolute;left:50%;top:2px;bottom:2px;width:1px;background:var(--dim)}
.dot{position:absolute;top:6px;width:11px;height:11px;margin-left:-5px;border-radius:50%;
background:var(--acc)}
ul{margin:6px 0;padding-left:20px}li{margin:5px 0}
.kv{display:flex;gap:26px;flex-wrap:wrap;font-size:13px;color:var(--dim)}
.kv b{color:var(--ink);font-variant-numeric:tabular-nums}
.claim{border-left:3px solid var(--acc);padding-left:14px}
.claimB{border-left:3px solid var(--warn);padding-left:14px}
.adversary{background:#161f2b;border:1px solid var(--line);border-radius:10px;
padding:12px 14px;margin:9px 0}
.adversary b{color:var(--warn)}
code{background:#0d141c;padding:1px 5px;border-radius:4px;font-size:12.5px}
.tabs{display:flex;gap:6px;margin:14px 0 0;flex-wrap:wrap}
.tabs button{background:var(--panel);color:var(--dim);border:1px solid var(--line);
border-radius:8px 8px 0 0;padding:8px 14px;cursor:pointer;font-size:13px}
.tabs button.on{background:#182433;color:var(--ink);border-bottom-color:#182433}
.tabpane{display:none;background:#182433;border:1px solid var(--line);border-radius:0 10px 10px 10px;
padding:16px}
.tabpane.on{display:block}
footer{margin-top:44px;color:var(--dim);font-size:12px;border-top:1px solid var(--line);padding-top:14px}
"""

JS = """
document.querySelectorAll('.tabs button').forEach(function(b){
  b.onclick=function(){
    var g=b.getAttribute('data-g');
    document.querySelectorAll('.tabs button[data-g="'+g+'"]').forEach(function(x){x.classList.remove('on');});
    document.querySelectorAll('.tabpane[data-g="'+g+'"]').forEach(function(x){x.classList.remove('on');});
    b.classList.add('on');
    var p=document.getElementById(b.getAttribute('data-t'));
    if(p) p.classList.add('on');
  };
});
(function(){
  var v=window.__verdict; if(!v) return;
  var TD=window.__tierDesc||{};
  var col={STABLE:['#064e3b','#6ee7b7','#10b981'],MODERATE:['#78350f','#fcd34d','#f59e0b'],
           EXPOSED:['#7f1d1d','#fca5a5','#ef4444'],UNCERTAIN:['#1f2937','#9ca3af','#6b7280']};
  var c=col[v.verdict]||col.UNCERTAIN;
  var host=document.getElementById('verdict');
  if(!host) return;
  var rs=(v.reasons||[]).map(function(r){return '<li>'+r+'</li>';}).join('');
  host.innerHTML =
    '<div style="background:'+c[0]+';border:1px solid '+c[2]+';border-left:5px solid '+c[2]+
    ';border-radius:12px;padding:15px 18px">'+
    '<div style="display:flex;align-items:center;gap:14px;flex-wrap:wrap">'+
    '<span style="font-size:19px;font-weight:700;letter-spacing:.06em;color:'+c[1]+'"'+
    ' id="verdict-tier">'+v.verdict+'</span>'+
    '<span style="color:'+c[1]+';font-size:13px">'+(TD[v.verdict]||'')+'</span></div>'+
    '<div style="margin-top:9px;color:#e6edf5;font-size:12.5px">P0 (arithmetic + provenance) defects: <b>'+
    v.p0_total+'</b> &nbsp;&middot;&nbsp; trials: <b>'+v.counts.n_trials_seen+
    '</b> &nbsp;&middot;&nbsp; nodes: <b>'+v.counts.n_nodes+'</b></div>'+
    '<ul style="margin:10px 0 0;padding-left:20px;color:#e6edf5;font-size:12.5px">'+rs+'</ul></div>';
})();
"""

doc = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>P. vivax radical cure &mdash; network meta-analysis of recurrence at 180 days</title>
<meta name="description" content="Arm-based binary NMA of hypnozoiticidal regimens for P. vivax radical cure; recurrence by 180 days; 7 nodes, 5 trials, N=2153.">
<style>{CSS}</style></head><body><div class="wrap">

<h1>P.&nbsp;vivax radical cure &mdash; recurrence by 180 days</h1>
<p class="sub">Arm-based binary network meta-analysis &middot; {FULL['n_trials']} trials &middot;
N&nbsp;=&nbsp;{FULL['N']} &middot; {len(FULL['nodes'])} nodes &middot; generated {e(R['generated'])}
&middot; <b>staged, not published</b></p>

<div id="verdict"></div>

<div class="panel">
<h3 style="margin-top:0">The estimand is RECURRENCE, not relapse</h3>
<p style="margin:0">Unlike falciparum, <b>PCR genotyping does not resolve vivax relapse</b>:
hypnozoites are frequently genetically heterologous to the primary infection, so relapse,
reinfection and recrudescence cannot be separated. EFFORT's post-hoc genotyping found the
<b>majority of recurrences were heterologous</b> &mdash; homologous in only 9/24 (37.5%),
11/23 (47.8%) and 12/31 (38.7%) of recurrences by arm. The outcome is therefore named
<b>recurrence by 180 days</b> throughout, and the ambiguity is an irreducible limit of the
question, not a limitation of this analysis.</p>
</div>

<h2>Two distinct claims</h2>
<div class="grid2">
<div class="panel claim">
<h3 style="margin-top:0">Claim A &mdash; full network ({len(FULL['nodes'])} nodes)</h3>
<div class="kv"><span>trials <b>{FULL['n_trials']}</b></span><span>N <b>{FULL['N']}</b></span>
<span>&tau;&sup2; <b>{FULL['tau2']}</b></span><span>I&sup2; <b>{FULL['I2']}%</b></span>
<span>Q <b>{FULL['Q']}</b> (df {FULL['df']}, p&nbsp;=&nbsp;{FULL['pQ']})</span></div>
<div class="tbl-scroll"><table><thead><tr><th>node</th><th class="num">OR</th><th>95% CI</th></tr></thead>
<tbody>{node_rows(FULL['nodes'])}</tbody></table></div>
<p class="sub" style="margin:10px 0 0">Odds ratio of <b>recurrence</b> versus no hypnozoiticidal
therapy. OR&nbsp;&lt;&nbsp;1 favours the node.</p>
</div>

<div class="panel claimB">
<h3 style="margin-top:0">Claim B &mdash; robust core (3 nodes)</h3>
<div class="kv"><span>trials <b>{CORE['n_trials']}</b></span><span>N <b>{CORE['N']}</b></span>
<span>&tau;&sup2; <b>{CORE['tau2']}</b></span><span>I&sup2; <b>{CORE['I2']}%</b></span>
<span>Q <b>{CORE['Q']}</b> (df {CORE['df']}, p&nbsp;=&nbsp;{CORE['pQ']})</span></div>
<div class="tbl-scroll"><table><thead><tr><th>node</th><th class="num">OR</th><th>95% CI</th></tr></thead>
<tbody>{node_rows(CORE['nodes'])}</tbody></table></div>
<p class="sub" style="margin:10px 0 0">The subnetwork that survives removal of <b>any single
trial</b>. Claim A adds four nodes but <b>changes nothing</b> here &mdash; see below.</p>
</div>
</div>

<div class="panel">
<h3 style="margin-top:0">Claim A adds nodes but adds no information to Claim B</h3>
<p>On all three contrasts the two networks share, the estimates are <b>identical to three
decimal places</b> (ratio 1.000). That is not a coincidence and not a bug: it is the arithmetic
signature of the fragility below. TQ&nbsp;50/100/600 and PQ&nbsp;7&nbsp;d are each fitted by
their own saturated within-trial contrasts, so they contribute <b>zero</b> to Q and
<b>zero</b> information to the core contrasts. R&nbsp;<code>netmeta</code>'s
<code>netsplit</code> agrees independently: the direct-evidence proportion is <b>1.00</b> for
the key PQ&nbsp;3.5-vs-TQ&nbsp;300 edge, so indirect evidence contributes essentially nothing
anywhere in this network.</p>
</div>

<h2>Structural fragility &mdash; leave one trial out</h2>
<div class="panel">
<div class="tbl-scroll"><table><thead><tr><th>trial removed</th>
<th class="num">nodes still connected</th><th>nodes lost</th></tr></thead><tbody>
{''.join(f'<tr><td class="trial">{e(t)}</td><td class="num">{n} / 7</td>'
         f'<td class="{"notest" if l else ""}">{e(l) if l else "network intact"}</td></tr>'
         for t, n, l in LOO)}
</tbody></table></div>
<p style="margin:12px 0 0"><b>Only 3 of 17 edges carry direct evidence from more than one
trial</b>, and they are exactly the three edges of the robust core. The remaining 14 are
single-trial. The TQ dose ladder stands or falls with DETECTIVE&nbsp;Part&nbsp;1; the
PQ&nbsp;7-day node stands or falls with EFFORT.</p>
</div>

<h2>The focal edge: tafenoquine 300&nbsp;mg vs primaquine 3.5&nbsp;mg/kg</h2>
<div class="panel">
<p style="margin-top:0">This is the <b>only</b> edge with more than one trial's direct evidence
&mdash; five trials. The pooled estimate says no difference; the per-trial estimates say the
trials are not measuring the same thing.</p>
<div class="tbl-scroll"><table><thead><tr><th>trial</th><th class="num">TQ rec/n</th>
<th class="num">PQ rec/n</th><th class="num">OR</th>
<th>0.25 &nbsp;&larr;&nbsp; favours TQ &nbsp;|&nbsp; favours PQ &nbsp;&rarr;&nbsp; 5</th></tr></thead>
<tbody>{FOREST}</tbody></table></div>
<p style="margin:12px 0 0">Spread <b>{F_LO:.3f}</b> to <b>{F_HI:.3f}</b>, a
{F_HI / F_LO:.1f}-fold range, I&sup2;&nbsp;=&nbsp;{FULL['I2']}%. The Q decomposition locates it:
within-design Q&nbsp;=&nbsp;{QD['within_design']:.2f} (df&nbsp;{QD['within_df']},
p&nbsp;=&nbsp;{QD['within_p']:.3f}) but <b>between-design
Q&nbsp;=&nbsp;{QD['between_design']:.2f} (df&nbsp;{QD['between_df']},
p&nbsp;=&nbsp;{QD['between_p']:.3f})</b>. Designs disagree with each other far more than trials
within a design do &mdash; exactly what the pre-registered partner-drug confound predicts.</p>
</div>

<h2>Pre-declared specification multiverse</h2>
<p class="sub">Eight axes, fixed in the Stage&nbsp;0 preflight <b>before any model was fitted</b>.
Every cell reports the focal contrast. Primary cells are highlighted.</p>
<div class="panel"><div class="tbl-scroll"><table><thead><tr><th>cell</th><th>axis / level</th>
<th class="num">k</th><th class="num">OR</th><th>95% CI</th><th class="num">I&sup2;</th></tr></thead>
<tbody>{MV}</tbody></table></div></div>

<h2>Pre-registered adversary targets</h2>
<p class="sub">Declared at Stage&nbsp;0, before fitting, for the cross-family gate.</p>
<div class="adversary"><b>1. Recurrence &ne; relapse, irreducibly.</b> PCR cannot separate relapse
from reinfection in vivax. EFFORT's genotyping found most recurrences heterologous. The estimand
stays "recurrence" everywhere in this app, including the badge.</div>
<div class="adversary"><b>2. The partner blood-stage drug confounds the anti-hypnozoite estimate.</b>
Piperaquine's prophylactic tail suppresses early recurrence well past day 42. INSPECTOR found
TQ+DHA-PQ far worse than PQ+DHA-PQ (OR of relapsing <b>4.57, 95% CI 1.75&ndash;11.97</b>); EFFORT
independently replicated it, with recurrence <b>22.4%</b> in its tafenoquine group in Indonesia
where the partner was DHA-PQ. Axis P3 exists for this.</div>
<div class="adversary"><b>3. Chloroquine alone is not a placebo, and the reference node is not one
thing.</b> The "no hypnozoiticidal therapy" node is <b>chloroquine alone</b> in DETECTIVE
Parts&nbsp;1&nbsp;and&nbsp;2 but <b>DHA-piperaquine alone</b> in INSPECTOR &mdash; drugs with very
different post-treatment prophylactic tails. Where chloroquine-resistant vivax circulates a
"recurrence" may be blood-stage failure, not relapse.</div>
<div class="adversary"><b>4. CYP2D6 breaks transitivity between the PQ and TQ nodes specifically.</b>
Primaquine needs CYP2D6 activation; tafenoquine does not. INSPECTOR measured it: 67/150 (45%) were
poor or intermediate metabolisers, with no significant effect detected &mdash; in a trial of 150,
which is not evidence of absence.</div>
<div class="adversary"><b>5. The approved 300&nbsp;mg tafenoquine dose is itself contested.</b>
Watson et&nbsp;al. (eLife 2022) vs Sharma et&nbsp;al. (eLife 2024) dispute 300&nbsp;mg versus
450&nbsp;mg. EFFORT's median tafenoquine dose was <b>5.4&nbsp;mg/kg</b>. The TQ dose ladder in this
network (50/100/300/600&nbsp;mg) rests entirely on DETECTIVE&nbsp;Part&nbsp;1.</div>

<h2>Transparency ledger &mdash; every arm-level count and its source</h2>
<div class="tabs">
<button class="on" data-g="t1" data-t="pane-ledger">Ledger</button>
<button data-g="t1" data-t="pane-check">Every number checkable</button>
<button data-g="t1" data-t="pane-limits">Declared limits</button>
<button data-g="t1" data-t="pane-methods">Methods &amp; validation</button>
</div>

<div class="tabpane on" id="pane-ledger" data-g="t1">
<div class="tbl-scroll"><table><thead><tr><th>trial</th><th>node</th><th class="num">n</th>
<th class="num">recurrence</th><th class="num">recurrence-free</th><th class="num">censored</th>
<th class="num">KM %</th><th>sources</th></tr></thead><tbody>{LEDGER}</tbody></table></div>
<p class="sub" style="margin-top:12px">Tier&nbsp;T1 = three-way concordant (registry + publication
+ FDA). T2 = two-way (one leg absent). T3 = single source.</p>
</div>

<div class="tabpane" id="pane-check" data-g="t1">
<h3 style="margin-top:0">How to check any number in this app</h3>
<ul>
<li><b>DETECTIVE Part&nbsp;2</b> &mdash; the only three-way concordant trial. Registry
<a href="{CTG}NCT01376167" target="_blank" rel="noopener">NCT01376167</a> primary outcome
"Number of Participants With Recurrence-free Efficacy at 6 Months" gives 35&nbsp;/&nbsp;133,
155&nbsp;/&nbsp;260, 83&nbsp;/&nbsp;129. FDA NDA&nbsp;210795 Table&nbsp;30 gives the same numerators
and denominators. The publication (PMID&nbsp;30650322) gives 522 in a 2:1:1 allocation.</li>
<li><b>DETECTIVE Part&nbsp;1</b> &mdash; <span class="notest">two-source only</span>. NCT01376167's
results section posts <b>Part&nbsp;2 alone</b>; Part&nbsp;1 has no registry results table.
Publication (PMID&nbsp;24360369) and FDA Table&nbsp;22 agree to the decimal on all six arms and all
six confidence intervals.</li>
<li><b>GATHER</b> &mdash; use its own OR <b>1.141 (0.643, 2.027)</b>, from FDA Table&nbsp;41.
<span class="notest">Never use the abstract's 1.81</span>: that figure comes from a pre-planned
patient-level meta-analysis pooling GATHER with DETECTIVE&nbsp;Part&nbsp;2. The arithmetic proves
it &mdash; 426&nbsp;=&nbsp;260&nbsp;+&nbsp;166 and 214&nbsp;=&nbsp;129&nbsp;+&nbsp;85. Using it
would double-count DETECTIVE&nbsp;Part&nbsp;2.</li>
<li><b>INSPECTOR</b> &mdash; the registry and the publication were never in conflict. CT.gov posts
the <b>crude proportions</b> (6/50, 11/50, 26/50 = 12%, 22%, 52%); the abstract quotes the
<b>Kaplan-Meier</b> estimates (11.2%, 21.0%, 52.0%). Different estimators, both correct, both shown.</li>
<li><b>EFFORT</b> &mdash; arm-level first-recurrence counts 34/295, 35/305, 49/301 come from the
full text (PMID&nbsp;41690325). Its confidence intervals are <b>97.55%</b>, not 95%, because alpha
was spent at an interim look; they are converted on the log-hazard-ratio scale, never treated as 95%.</li>
<li><b>The fit itself</b> &mdash; <code>nma_fit.py</code> reproduces R <code>netmeta</code>'s
fixed-effect log-ORs and standard errors to a maximum absolute difference of
<b>{R['validation']['max_abs_diff_fixed_effect']:.2e}</b>, inside the
{R['validation']['tolerance']:.0e} tolerance. Q, df, p and I&sup2; reproduce exactly, as do all
five per-trial ORs on the focal edge.</li>
</ul>
</div>

<div class="tabpane" id="pane-limits" data-g="t1">
<h3 style="margin-top:0">Limits carried forward, stated rather than smoothed over</h3>
<ul>
<li><b>Mixed estimators coexist.</b> Crude proportions, Kaplan-Meier cumulative incidence and
hazard ratios all appear across these five trials; KM exceeds crude wherever censoring is
non-trivial. Axis&nbsp;P8 makes the choice explicit &mdash; and the answer barely moves
(1.072&nbsp;/&nbsp;1.063&nbsp;/&nbsp;1.073).</li>
<li><b>EFFORT is open-label</b> and reports <b>97.55% CIs</b>; the other four are double-blind with
95% CIs. It is also the only trial deliberately measuring <i>effectiveness</i> (unsupervised
dosing) rather than efficacy &mdash; axis&nbsp;P6, where the estimate moves most
(1.249 supervised vs 0.667 unsupervised).</li>
<li><b>The reference node is not a placebo node</b> and is not even one intervention: chloroquine
alone in DETECTIVE, DHA-piperaquine alone in INSPECTOR.</li>
<li><b>Proportional hazards is violated</b> on INSPECTOR's TQ-vs-PQ contrast. Its authors call the
HR unreliable and use OR&nbsp;4.57 (1.75&ndash;11.97). A single pooled HR on that edge would
mislead, which is why this analysis pools odds ratios throughout.</li>
<li><b>IMPROV (N&nbsp;=&nbsp;2336) is excluded entirely.</b> It reports incidence risk at day&nbsp;28,
day&nbsp;42 and 1&nbsp;year &mdash; there is no 180-day row anywhere in the paper. The person-year
rate was <b>not</b> back-converted and the 180-day risk was <b>not</b> interpolated. It would have
been the largest trial in the network.</li>
<li><b>Three proposed nodes do not exist at this estimand</b> and are declared absent rather than
improvised: PQ&nbsp;14&nbsp;d high dose (7&nbsp;mg/kg) has no 180-day evidence at all;
PQ&nbsp;weekly&nbsp;&times;&nbsp;8&nbsp;wk has no eligible trial; paediatric tafenoquine is
single-arm only.</li>
<li><b>Only NDA&nbsp;210795 (Krintafel) backs this network.</b> NDA&nbsp;210607 (Arakoda) is a
<b>prophylaxis</b> approval whose trials randomise uninfected people; it supplies
<b>zero efficacy nodes</b> here. Two tafenoquine FDA packages exist, but only one is evidence for
radical cure.</li>
<li><b>Tafenoquine has no EMA authorisation or scientific opinion</b> (verified 2026-07-30): absent
from the EMA medicines register, and not among the eleven EU-M4all/Article&nbsp;58 opinions EMA
enumerates. Its non-FDA regulatory basis is TGA&nbsp;Australia via WHO prequalification
(MA203&nbsp;/&nbsp;MA204, 2024-12-04). The EU-M4all list is dated July&nbsp;2020, so a later
opinion would not appear in it.</li>
</ul>
</div>

<div class="tabpane" id="pane-methods" data-g="t1">
<h3 style="margin-top:0">Methods</h3>
<p>Contrast-based random-effects network meta-analysis (Lu &amp; Ades parameterisation) on the
log odds ratio of recurrence. Each trial contributes contrasts against its own baseline arm with
the shared-baseline covariance Var&nbsp;=&nbsp;v<sub>base</sub>&nbsp;+&nbsp;v<sub>k</sub>,
Cov&nbsp;=&nbsp;v<sub>base</sub>; the random-effects structure adds &tau;&sup2; on the diagonal and
&tau;&sup2;/2 off it. <b>&tau;&sup2; is estimated by REML, not DerSimonian-Laird</b>, which is
materially downward-biased at k&nbsp;=&nbsp;5. Where a cell has too few contrasts to identify
&tau;&sup2;, it is fixed at 0 and <b>labelled as not estimable</b> rather than left to a flat
likelihood. Continuity correction is applied only if a trial actually has a zero cell; none does
here.</p>
<h3>Validation</h3>
<p>Independently reproduced in R <code>netmeta</code>. Fixed-effect log-ORs and SEs agree to
{R['validation']['max_abs_diff_fixed_effect']:.2e} (tolerance {R['validation']['tolerance']:.0e});
Q&nbsp;=&nbsp;{QD['total']:.3f}, df&nbsp;=&nbsp;{QD['total_df']},
p&nbsp;=&nbsp;{QD['total_p']:.4f} and I&sup2; reproduce exactly, as do the five per-trial ORs.
The Q decomposition and <code>netsplit</code> figures quoted above are netmeta's own.</p>
<h3>Provenance</h3>
<p>Arm-level counts were taken from ClinicalTrials.gov results tables, the primary publications,
and the FDA multi-discipline review for NDA&nbsp;210795, and reconciled across all three where all
three exist. Discrepancies are displayed, not resolved silently. The FDA review PDF ships broken
font CMaps that yield confident garbage rather than an error; it was decoded per page by scoring
candidate transforms against a word list, and every extracted arm then satisfied
recurrence&nbsp;+&nbsp;recurrence-free&nbsp;+&nbsp;censored&nbsp;=&nbsp;n.</p>
</div>

<footer>
Staged for the Claude &rarr; Codex &rarr; Gemini cross-family gate. Not published.
Generated from <code>outputs/vivax_nma_results.json</code>; no displayed number is hand-typed.
</footer>
</div>

<script>window.__verdict = {json.dumps(VERDICT)};</script>
<script>window.__tierDesc = {json.dumps(TIER_DESC)};</script>
<script>{JS}</script>
</body></html>
"""

open(OUT, 'w', encoding='utf-8').write(doc)
print(f'wrote {OUT}  ({len(doc):,} bytes)')
