"""Validate rapidmeta-nma-engine-v2.js against R/netmeta outputs.

Runs the new JS engine in a headless browser on each NMA test dataset
and compares point estimates + tau² to the committed R JSON to 1e-3.
"""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

DATASETS = [
    ('btki_cll_nma',       'BR',              'HR',  False),  # HR; lower=better
    ('antiamyloid_ad_nma', 'Placebo',         'MD',  False),  # MD; lower=better (CDR-SB)
    ('antivegf_namd_nma',  'Aflibercept_2mg', 'MD',  True),   # BCVA MD; higher=better
    ('il_psoriasis_nma',   'Placebo',         'OR',  True),   # OR; higher=better (PASI 90)
]

ROOT = Path(__file__).resolve().parents[1]
VALIDATION_DIR = ROOT / 'nma' / 'validation'

def load_trials(slug):
    csv_path = ROOT / 'nma' / 'data' / f'{slug}_trials.csv'
    import csv as csvlib
    rows = []
    with open(csv_path) as f:
        for r in csvlib.DictReader(f):
            rows.append({
                'studlab': r['studlab'], 'treat1': r['treat1'], 'treat2': r['treat2'],
                'TE': float(r['te_for_netmeta']), 'seTE': float(r['seTE_for_netmeta'])
            })
    return rows

def run_js_engine(trials, reference, scale, page):
    """Run rapidmeta-nma-engine-v2.js in browser and return fit + sucra."""
    script = r'''
    () => {
      const trials = %s;
      const ref = %s;
      const f = RapidMetaNMA.fit({trials: trials, reference: ref, method_tau: 'REML', hksj: true, alpha: 0.05});
      // Only return JSON-safe subset
      return {
        treatments: f.treatments,
        effects: f.effects,
        tau2: f.tau2, I2: f.I2, Q: f.Q, p_Q: f.p_Q,
        Q_inconsistency: f.Q_inconsistency, p_Q_inconsistency: f.p_Q_inconsistency,
        HKSJ_multiplier: f.HKSJ_multiplier
      };
    }
    ''' % (json.dumps(trials), json.dumps(reference))
    return page.evaluate(script)

def main():
    html = '''<!DOCTYPE html><html><head><meta charset="utf-8"></head><body>
<script src="rapidmeta-nma-engine-v2.js"></script>
</body></html>'''
    (ROOT / 'nma_engine_test.html').write_text(html, encoding='utf-8')
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        pg = b.new_page()
        for slug, ref, scale, higher_better in DATASETS:
            trials = load_trials(slug)
            pg.goto(f'http://localhost:8788/nma_engine_test.html', wait_until='load', timeout=30000)
            pg.wait_for_timeout(500)
            js = run_js_engine(trials, ref, scale, pg)
            r_json = json.load(open(VALIDATION_DIR / f'{slug}_netmeta_results.json'))
            is_log = scale in ('HR','OR','RR')
            print(f'=== {slug} (k={len(trials)}, ref={ref}, scale={scale}) ===')
            print(f'  JS tau2={js["tau2"]:.5f} vs R tau2={r_json.get("tau2",[None])[0] if isinstance(r_json.get("tau2"), list) else r_json.get("tau2")}')
            print(f'  JS Q_inc={js["Q_inconsistency"]:.3f} vs R Q_inc={r_json.get("Q_inconsistency", [None])[0] if isinstance(r_json.get("Q_inconsistency"), list) else r_json.get("Q_inconsistency")}')
            print(f'  HR/OR/MD comparisons (treatment vs {ref}):')
            for trt, eff in js['effects'].items():
                if trt == ref: continue
                js_point = eff['est']
                # netmeta's te_random_vs_ref is log-scale for HR/OR/RR; native for MD
                # Our engine returns log-scale (beta_RE) for HR/OR/RR, native for MD — matches netmeta
                r_point_list = r_json.get('te_random_vs_ref', {})
                r_names = r_json.get('treatments', [])
                if isinstance(r_names, list) and trt in r_names:
                    r_idx = r_names.index(trt)
                    if isinstance(r_point_list, list) and r_idx < len(r_point_list):
                        r_val = r_point_list[r_idx]
                        import math
                        if is_log:
                            js_disp = math.exp(js_point)
                            r_disp = math.exp(r_val)
                        else:
                            js_disp = js_point
                            r_disp = r_val
                        diff = abs(js_disp - r_disp)
                        status = 'PASS' if diff < 1e-3 else ('CLOSE' if diff < 5e-2 else 'FAIL')
                        print(f'    {trt:<22} JS={js_disp:8.4f}  R={r_disp:8.4f}  diff={diff:.5f} {status}')
            print()
        b.close()

if __name__ == '__main__':
    main()
