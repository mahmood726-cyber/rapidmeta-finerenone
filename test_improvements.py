"""Test the 3 methodological improvements."""
import sys, io, os, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

opts = Options()
opts.add_argument('--headless=new')
opts.add_argument('--no-sandbox')
opts.add_argument('--disable-gpu')
opts.add_argument('--incognito')
opts.set_capability('goog:loggingPrefs', {'browser': 'ALL'})

DIR = os.path.dirname(os.path.abspath(__file__))
p = 0; f = 0

def check(label, cond, detail=''):
    global p, f
    if cond:
        p += 1; print(f'  [PASS] {label}')
    else:
        f += 1; print(f'  [FAIL] {label} -- {detail}')

def furl(fname):
    return 'file:///' + os.path.join(DIR, fname).replace(chr(92), '/')

APPS = [
    ('FINERENONE_REVIEW.html', 'Finerenone'),
    ('COLCHICINE_CVD_REVIEW.html', 'Colchicine'),
    ('ARNI_HF_REVIEW.html', 'ARNI'),
    ('LIPID_HUB_REVIEW.html', 'Omega-3'),
    ('SGLT2_CKD_REVIEW.html', 'SGLT2 CKD'),
    ('MAVACAMTEN_HCM_REVIEW.html', 'Mavacamten'),
]

for fname, label in APPS:
    print(f'\n=== {label} ({fname}) ===')
    d = None
    try:
        d = webdriver.Chrome(options=opts)
        d.set_page_load_timeout(45)
        d.get(furl(fname))
        time.sleep(3)
        d.execute_script("document.querySelector('[data-tab=\"analysis\"]').click()")
        time.sleep(2)

        # 1. I2 CI
        i2 = d.execute_script("return document.getElementById('res-i2').innerText")
        print(f'    I2: {i2}')
        # For I2 > 0, should show CI; for I2 = 0, just percentage
        i2_val = d.execute_script("""
            var inc = RapidMeta.state.trials.filter(t => t.status === 'include');
            var c = AnalysisEngine.computeCore(inc);
            return { I2: c.I2, I2_lo: c.I2_lo, I2_hi: c.I2_hi, k: c.k };
        """)
        if i2_val and i2_val.get('I2', 0) > 0 and i2_val.get('I2_hi', 0) > 0:
            check(f'{label}: I2 CI shown ({i2_val["I2"]:.0f}%, {i2_val["I2_lo"]:.0f}-{i2_val["I2_hi"]:.0f}%)',
                  '(' in str(i2), f'Got: {i2}')
        else:
            check(f'{label}: I2 point estimate shown', '%' in str(i2), f'Got: {i2}')

        # 2. HKSJ discordance
        hksj = d.execute_script("""
            var el = document.getElementById('res-hksj');
            if (!el) return null;
            var card = el.closest('.glass') || el.parentElement;
            var inc = RapidMeta.state.trials.filter(t => t.status === 'include');
            var c = AnalysisEngine.computeCore(inc);
            var waldSig = (c.lci > 1) || (c.uci < 1);
            var hksjSig = (c.hksjLCI > 1) || (c.hksjUCI < 1);
            return {
                text: el.innerText,
                waldSig: waldSig,
                hksjSig: hksjSig,
                borderColor: card.style.borderColor,
                hasTitle: card.title.length > 0
            };
        """)
        if hksj:
            if hksj['waldSig'] and not hksj['hksjSig']:
                check(f'{label}: HKSJ discordance flagged',
                      hksj['borderColor'] != '' or hksj['hasTitle'],
                      f'border={hksj["borderColor"]}')
            else:
                check(f'{label}: HKSJ concordance (no flag needed)', True)
            print(f'    HKSJ: {hksj["text"]}, Wald sig={hksj["waldSig"]}, HKSJ sig={hksj["hksjSig"]}')

        # 3. Sensitivity summary
        sens = d.execute_script("""
            var el = document.getElementById('sensitivity-concordance');
            return el ? el.innerText : null;
        """)
        check(f'{label}: sensitivity summary rendered',
              sens and 'Wald' in sens and 'HKSJ' in sens,
              f'Got: {sens}')
        if sens:
            print(f'    Sensitivity: {sens}')

        # No JS errors
        logs = d.get_log('browser')
        severe = [l for l in logs if l['level'] == 'SEVERE' and 'favicon' not in l.get('message', '')]
        check(f'{label}: no JS errors', len(severe) == 0,
              f'{severe[0]["message"][:80]}' if severe else '')

    except Exception as e:
        check(f'{label}: load', False, str(e)[:150])
    finally:
        if d:
            d.quit()
        time.sleep(0.3)

print(f'\n{"="*60}')
print(f'IMPROVEMENT TESTS: {p}/{p+f} passed, {f} failed')
print(f'{"="*60}')
if f > 0:
    sys.exit(1)
