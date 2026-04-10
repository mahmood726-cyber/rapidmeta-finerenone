#!/usr/bin/env python
"""Generate the portfolio index.html from app_inventory.json."""
import json, os, sys, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

inventory = json.load(open('C:/Projects/LivingMA_Portfolio/app_inventory.json'))

specialty_map = {
    'FINERENONE': 'Cardiology', 'ABLATION_AF': 'Cardiology', 'ARNI_HF': 'Cardiology',
    'BEMPEDOIC_ACID': 'Cardiology', 'COLCHICINE_CVD': 'Cardiology', 'DOAC_CANCER_VTE': 'Cardiology',
    'GLP1_CVOT': 'Cardiometabolic', 'INCRETIN_HFpEF': 'Cardiometabolic', 'INTENSIVE_BP': 'Cardiology',
    'IV_IRON_HF': 'Cardiology', 'LIPID_HUB': 'Cardiology', 'MAVACAMTEN_HCM': 'Cardiology',
    'PCSK9': 'Cardiology', 'RENAL_DENERV': 'Cardiology', 'RIVAROXABAN_VASC': 'Cardiology',
    'SGLT2_CKD': 'Nephrology', 'SGLT2_HF': 'Cardiology', 'ATTR_CM': 'Cardiology',
    'PFA_AF': 'Interventional', 'WATCHMAN_AMULET': 'Interventional', 'TRICUSPID_TEER': 'Interventional',
    'INCLISIRAN': 'Cardiology', 'TIRZEPATIDE_CV': 'Cardiometabolic', 'SEMAGLUTIDE_HFPEF': 'Cardiometabolic',
    'LEADLESS_PACING': 'Interventional', 'CSP': 'Interventional', 'CORONARY_IVL': 'Interventional',
    'OMECAMTIV': 'Cardiology', 'CTFFR': 'Interventional', 'VERICIGUAT': 'Cardiology',
    'SOTAGLIFLOZIN': 'Cardiology', 'TDXd_BREAST': 'Oncology', 'OSIMERTINIB_NSCLC': 'Oncology',
    'ANTI_AMYLOID_AD': 'Neurology', 'RESMETIROM_MASH': 'Hepatology', 'SEMAGLUTIDE_CKD': 'Nephrology',
    'TICAGRELOR_MONO': 'Cardiology', 'SOTATERCEPT_PAH': 'Pulm Vascular',
    'ICOSAPENT_ETHYL': 'Cardiology', 'K_BINDERS': 'Nephrology', 'EMPA_MI': 'Cardiology',
    'DCB_PAD': 'Peripheral Vascular', 'ORFORGLIPRON': 'Cardiometabolic', 'OBESITY_NMA': 'NMA',
    'ANTIPLATELET_NMA': 'NMA', 'BIMEKIZUMAB_PSO': 'Dermatology', 'DAPA_ACUTE_HF': 'Cardiology',
    'DUPILUMAB_COPD': 'Pulmonology', 'ENFORTUMAB_UC': 'Oncology', 'HFREF_NMA': 'NMA',
    'IPTACOPAN': 'Nephrology', 'KRAS_G12C_NSCLC': 'Oncology', 'PAH_NMA': 'NMA',
    'PEMBRO_ADJ_MEL': 'Oncology', 'SACITUZUMAB_TNBC': 'Oncology', 'SPARSENTAN_IGAN': 'Nephrology',
    'TEZEPELUMAB_ASTHMA': 'Pulmonology',
}

colors = {
    'Cardiology': '#3b82f6', 'Cardiometabolic': '#f97316', 'Oncology': '#f43f5e',
    'Pulmonology': '#06b6d4', 'Neurology': '#8b5cf6', 'Hepatology': '#f59e0b',
    'Nephrology': '#10b981', 'NMA': '#6366f1', 'Interventional': '#0ea5e9',
    'Peripheral Vascular': '#ec4899', 'Pulm Vascular': '#14b8a6', 'Dermatology': '#a855f7',
}

specialties_found = set()
cards = []
for app in sorted(inventory, key=lambda x: x['title']):
    spec = specialty_map.get(app['name'], 'Other')
    specialties_found.add(spec)
    color = colors.get(spec, '#64748b')
    badges = ''
    if app['dr']:
        badges += '<span class="badge badge-dr">DOSE-RESPONSE</span> '
    if app['nma']:
        badges += '<span class="badge badge-nma">NMA</span> '
    cards.append(f'''<a href="{app['gh_url']}" target="_blank" rel="noopener" class="card" data-specialty="{spec}" style="--card-accent:{color}">
      <div class="card-header"><span class="dot" style="background:{color}"></span><span class="spec-label" style="color:{color}">{spec}</span></div>
      <h3>{app['title']}</h3>
      <div class="card-meta">{app['trials']} trials &middot; {app['lines']:,} lines &middot; {app['effect']}</div>
      <div class="badges">{badges}</div>
    </a>''')

pills_html = f'<button class="pill active" style="--pill-color:#3b82f6" onclick="filterCards(this)" data-filter="all">All ({len(inventory)})</button>\n'
for spec in sorted(specialties_found):
    c = colors.get(spec, '#64748b')
    n = sum(1 for a in inventory if specialty_map.get(a['name'], 'Other') == spec)
    pills_html += f'    <button class="pill" style="--pill-color:{c}" onclick="filterCards(this)" data-filter="{spec}">{spec} ({n})</button>\n'

total_trials = sum(a['trials'] for a in inventory)
dr_count = sum(1 for a in inventory if a['dr'])
nma_count = sum(1 for a in inventory if a['nma'])

html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="description" content="Living Evidence Portfolio — {len(inventory)} transparent meta-analyses across {len(specialties_found)} specialties.">
<meta property="og:title" content="Living Evidence Portfolio — {len(inventory)} Transparent Meta-Analyses">
<meta property="og:description" content="{len(inventory)} living systematic reviews. Every number traces to its source.">
<meta property="og:type" content="website">
<title>Living Evidence Portfolio — {len(inventory)} Meta-Analyses</title>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css" crossorigin="anonymous">
<style>
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#020617;color:#f1f5f9;font-family:system-ui,-apple-system,sans-serif;min-height:100vh;padding:40px 20px}}
.container{{max-width:1200px;margin:0 auto}}
h1{{font-size:28px;font-weight:800;background:linear-gradient(135deg,#3b82f6,#8b5cf6);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:8px}}
.subtitle{{font-size:14px;color:#64748b;margin-bottom:32px}}
.stats{{display:flex;gap:24px;margin-bottom:24px;flex-wrap:wrap}}
.stat{{background:#0f172a;border:1px solid #1e293b;border-radius:12px;padding:16px 24px;text-align:center}}
.stat-num{{font-size:28px;font-weight:800;color:#3b82f6}}
.stat-label{{font-size:10px;color:#64748b;text-transform:uppercase;letter-spacing:0.1em;margin-top:4px}}
.pills{{display:flex;gap:8px;margin-bottom:24px;flex-wrap:wrap}}
.pill{{background:#0f172a;border:1px solid #1e293b;border-radius:20px;padding:6px 16px;font-size:11px;font-weight:600;color:#94a3b8;cursor:pointer;transition:all 0.2s}}
.pill:hover,.pill.active{{background:color-mix(in srgb,var(--pill-color) 15%,transparent);color:var(--pill-color);border-color:color-mix(in srgb,var(--pill-color) 30%,transparent)}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:16px}}
.card{{background:#0f172a;border:1px solid #1e293b;border-radius:16px;padding:20px;text-decoration:none;transition:all 0.2s;display:block}}
.card:hover{{border-color:var(--card-accent);box-shadow:0 0 20px color-mix(in srgb,var(--card-accent) 15%,transparent);transform:translateY(-2px)}}
.card-header{{display:flex;align-items:center;gap:8px;margin-bottom:8px}}
.dot{{width:8px;height:8px;border-radius:50%}}
.spec-label{{font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.1em}}
.card h3{{font-size:14px;font-weight:700;color:#f1f5f9;margin-bottom:6px}}
.card-meta{{font-size:11px;color:#64748b;margin-bottom:8px}}
.badges{{display:flex;gap:4px;flex-wrap:wrap}}
.badge{{padding:2px 8px;border-radius:8px;font-size:9px;font-weight:700}}
.badge-dr{{background:rgba(244,63,94,0.15);color:#fb7185;border:1px solid rgba(244,63,94,0.3)}}
.badge-nma{{background:rgba(99,102,241,0.15);color:#a5b4fc;border:1px solid rgba(99,102,241,0.3)}}
.hidden{{display:none!important}}
footer{{margin-top:48px;padding-top:24px;border-top:1px solid #1e293b;text-align:center;font-size:11px;color:#475569}}
</style>
</head>
<body>
<div class="container">
  <h1><i class="fa-solid fa-microscope" style="margin-right:8px"></i>Living Evidence Portfolio</h1>
  <p class="subtitle">Mahmood Ahmad &middot; Tahir Heart Institute &middot; {len(inventory)} living systematic reviews &middot; Every number traces to its source</p>
  <div class="stats">
    <div class="stat"><div class="stat-num">{len(inventory)}</div><div class="stat-label">Living MAs</div></div>
    <div class="stat"><div class="stat-num">{len(specialties_found)}</div><div class="stat-label">Specialties</div></div>
    <div class="stat"><div class="stat-num">{total_trials}</div><div class="stat-label">Trials</div></div>
    <div class="stat"><div class="stat-num">{dr_count}</div><div class="stat-label">Dose-Response</div></div>
    <div class="stat"><div class="stat-num">{nma_count}</div><div class="stat-label">NMA</div></div>
  </div>
  <div class="pills">
    {pills_html}
  </div>
  <div class="grid" id="grid">
    {"".join(cards)}
  </div>
  <footer>
    RapidMeta Living Evidence Portfolio &middot; v16.0 &middot; Updated 2026-04-10 &middot;
    <a href="https://github.com/mahmood726-cyber" style="color:#3b82f6">GitHub</a>
  </footer>
</div>
<script>
function filterCards(btn) {{
  document.querySelectorAll('.pill').forEach(p => p.classList.remove('active'));
  btn.classList.add('active');
  const filter = btn.dataset.filter;
  document.querySelectorAll('.card').forEach(c => {{
    if (filter === 'all' || c.dataset.specialty === filter) c.classList.remove('hidden');
    else c.classList.add('hidden');
  }});
}}
</script>
</body>
</html>'''

with open('C:/Projects/LivingMA_Portfolio/index.html', 'w', encoding='utf-8') as f:
    f.write(html)
print(f'Portfolio: {len(inventory)} apps, {len(specialties_found)} specialties, {total_trials} trials, {dr_count} DR, {nma_count} NMA')
