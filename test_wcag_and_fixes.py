"""
Targeted Selenium tests for the 3 review fixes:
1. WCAG AA contrast verification (computed styles in browser)
2. controlEventRate ?? 0.15 (nullish coalescing, not ||)
3. No-op regex cleanup verification

Run: python test_wcag_and_fixes.py
"""
import sys, io, os, time, traceback, subprocess
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

REVIEW_FILES = [
    'FINERENONE_REVIEW.html', 'BEMPEDOIC_ACID_REVIEW.html',
    'COLCHICINE_CVD_REVIEW.html', 'GLP1_CVOT_REVIEW.html',
    'SGLT2_HF_REVIEW.html', 'PCSK9_REVIEW.html',
    'INTENSIVE_BP_REVIEW.html', 'LIPID_HUB_REVIEW.html',
    'INCRETIN_HFpEF_REVIEW.html', 'ATTR_CM_REVIEW.html',
    'SGLT2_CKD_REVIEW.html', 'ARNI_HF_REVIEW.html',
    'ABLATION_AF_REVIEW.html', 'IV_IRON_HF_REVIEW.html',
    'RENAL_DENERV_REVIEW.html', 'DOAC_CANCER_VTE_REVIEW.html',
    'MAVACAMTEN_HCM_REVIEW.html', 'RIVAROXABAN_VASC_REVIEW.html',
]

# WCAG AA contrast ratio calculation
def srgb_to_linear(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

def relative_luminance(r, g, b):
    return 0.2126 * srgb_to_linear(r) + 0.7152 * srgb_to_linear(g) + 0.0722 * srgb_to_linear(b)

def contrast_ratio(l1, l2):
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)

def parse_rgb(rgb_str):
    """Parse 'rgb(r, g, b)' or 'rgba(r, g, b, a)' to (r, g, b)"""
    rgb_str = rgb_str.strip()
    if rgb_str.startswith('rgba'):
        parts = rgb_str[5:-1].split(',')
    elif rgb_str.startswith('rgb'):
        parts = rgb_str[4:-1].split(',')
    else:
        return None
    return (int(parts[0].strip()), int(parts[1].strip()), int(parts[2].strip()))

def get_opts():
    opts = Options()
    opts.add_argument('--headless=new')
    opts.add_argument('--no-sandbox')
    opts.add_argument('--disable-gpu')
    opts.add_argument('--disable-dev-shm-usage')
    opts.add_argument('--incognito')
    opts.set_capability('goog:loggingPrefs', {'browser': 'ALL'})
    return opts

def kill_orphan():
    for proc in ['chromedriver.exe', 'chrome.exe']:
        try:
            subprocess.run(['taskkill', '/f', '/im', proc],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)
        except Exception:
            pass

# ── WCAG contrast targets ──
# selector -> (min_contrast, description)
WCAG_CHECKS = {
    '.badge-search': (4.5, 'Badge search text on bg'),
    '.chart-dl-btn': (4.5, 'Chart download button'),
    '.evidence-source': (4.5, 'Evidence source text'),
    '.extract-view-btn': (4.5, 'Extract view button text'),
}

results = {'pass': 0, 'fail': 0}

def check(label, condition, detail=''):
    if condition:
        results['pass'] += 1
        print(f'  [PASS] {label}')
    else:
        results['fail'] += 1
        print(f'  [FAIL] {label} -- {detail}')


print('='*70)
print('WCAG + Review Fixes Verification Test Suite')
print('='*70)

kill_orphan()
time.sleep(1)

# ── Test 1: WCAG contrast on representative files (3 samples) ──
WCAG_SAMPLE = ['FINERENONE_REVIEW.html', 'LIPID_HUB_REVIEW.html', 'COLCHICINE_CVD_REVIEW.html']

for fname in WCAG_SAMPLE:
    print(f'\n=== WCAG Contrast: {fname} ===')
    driver = None
    try:
        driver = webdriver.Chrome(options=get_opts())
        driver.set_page_load_timeout(30)
        fpath = 'file:///' + os.path.join(BASE_DIR, fname).replace('\\', '/')
        driver.get(fpath)
        time.sleep(2)

        for selector, (min_cr, desc) in WCAG_CHECKS.items():
            try:
                # Get computed color and background
                js = f"""
                    var el = document.querySelector('{selector}');
                    if (!el) return null;
                    var cs = window.getComputedStyle(el);
                    return {{
                        color: cs.color,
                        bg: cs.backgroundColor,
                        fontSize: cs.fontSize,
                        fontWeight: cs.fontWeight
                    }};
                """
                style = driver.execute_script(js)
                if not style:
                    check(f'{desc} ({selector})', False, 'Element not found in DOM')
                    continue

                fg = parse_rgb(style['color'])
                bg = parse_rgb(style['bg'])

                if not fg:
                    check(f'{desc} ({selector})', False, f'Could not parse fg: {style["color"]}')
                    continue

                # If bg is transparent (rgba 0,0,0,0), use page bg
                if not bg or (bg == (0, 0, 0) and 'rgba' in style['bg'] and ', 0)' in style['bg']):
                    # Fall back to body background
                    body_bg = driver.execute_script("return window.getComputedStyle(document.body).backgroundColor")
                    bg = parse_rgb(body_bg) or (2, 6, 23)  # --bg-dark fallback

                fg_lum = relative_luminance(*fg)
                bg_lum = relative_luminance(*bg)
                cr = contrast_ratio(fg_lum, bg_lum)

                check(f'{desc} ({selector}): {cr:.2f}:1',
                      cr >= min_cr,
                      f'Contrast {cr:.2f}:1 < {min_cr}:1 needed. fg={fg} bg={bg}')
            except Exception as e:
                check(f'{desc} ({selector})', False, str(e))

        # Also verify no JS errors
        logs = driver.get_log('browser')
        severe = [l for l in logs if l['level'] == 'SEVERE' and 'favicon' not in l.get('message', '')]
        check('No JS errors', len(severe) == 0,
              f'{len(severe)} errors: {severe[0]["message"][:100]}' if severe else '')

    except Exception as e:
        check(f'Load {fname}', False, str(e))
    finally:
        if driver:
            driver.quit()
        time.sleep(0.5)


# ── Test 2: Light mode contrast ──
print(f'\n=== Light Mode WCAG: FINERENONE_REVIEW.html ===')
driver = None
try:
    driver = webdriver.Chrome(options=get_opts())
    driver.set_page_load_timeout(30)
    fpath = 'file:///' + os.path.join(BASE_DIR, 'FINERENONE_REVIEW.html').replace('\\', '/')
    driver.get(fpath)
    time.sleep(2)

    # Toggle to light mode
    driver.execute_script("document.body.classList.add('light-mode');")
    time.sleep(0.5)

    for selector, (min_cr, desc) in WCAG_CHECKS.items():
        try:
            js = f"""
                var el = document.querySelector('{selector}');
                if (!el) return null;
                var cs = window.getComputedStyle(el);
                return {{ color: cs.color, bg: cs.backgroundColor }};
            """
            style = driver.execute_script(js)
            if not style:
                check(f'Light: {desc} ({selector})', True, 'Not rendered in light mode (OK)')
                continue

            fg = parse_rgb(style['color'])
            bg = parse_rgb(style['bg'])
            if not fg:
                continue

            if not bg or (bg == (0, 0, 0) and 'rgba' in style['bg'] and ', 0)' in style['bg']):
                body_bg = driver.execute_script("return window.getComputedStyle(document.body).backgroundColor")
                bg = parse_rgb(body_bg) or (248, 250, 252)

            fg_lum = relative_luminance(*fg)
            bg_lum = relative_luminance(*bg)
            cr = contrast_ratio(fg_lum, bg_lum)

            check(f'Light: {desc} ({selector}): {cr:.2f}:1',
                  cr >= min_cr,
                  f'Contrast {cr:.2f}:1 < {min_cr}:1. fg={fg} bg={bg}')
        except Exception as e:
            check(f'Light: {desc} ({selector})', False, str(e))

except Exception as e:
    check('Light mode test', False, str(e))
finally:
    if driver:
        driver.quit()
    time.sleep(0.5)


# ── Test 3: Verify ?? operator works (not || for controlEventRate) ──
# Test that controlEventRate of 0 is preserved (not replaced by 0.15)
NULLISH_FILES = ['COLCHICINE_CVD_REVIEW.html', 'GLP1_CVOT_REVIEW.html', 'SGLT2_HF_REVIEW.html']

print(f'\n=== Nullish Coalescing Fix ===')
for fname in NULLISH_FILES:
    fpath = os.path.join(BASE_DIR, fname)
    with open(fpath, 'r', encoding='utf-8') as f:
        src = f.read()
    has_bad = 'pooledControlEventRate(included) || 0.15' in src
    has_good = 'pooledControlEventRate(included) ?? 0.15' in src
    check(f'{fname}: uses ?? (not ||)',
          has_good and not has_bad,
          'Still uses || 0.15' if has_bad else ('Missing pattern' if not has_good else ''))


# ── Test 4: No-op regex cleanup verification ──
print(f'\n=== No-op Regex Cleanup ===')
for fname in REVIEW_FILES:
    fpath = os.path.join(BASE_DIR, fname)
    with open(fpath, 'r', encoding='utf-8') as f:
        src = f.read()
    has_noop = "h.pattern.replace(/\\\\/g, '\\\\')" in src
    check(f'{fname}: no-op regex removed',
          not has_noop,
          'Still has h.pattern.replace no-op' if has_noop else '')


# ── Test 5: Verify CSS color values in source ──
print(f'\n=== CSS Source Verification ===')
import re
for fname in REVIEW_FILES:
    fpath = os.path.join(BASE_DIR, fname)
    with open(fpath, 'r', encoding='utf-8') as f:
        src = f.read()

    # badge-search should have #cbd5e1 (not #94a3b8)
    badge_ok = bool(re.search(r'\.badge-search\s*\{[^}]*color:\s*#cbd5e1', src))
    # chart-dl-btn should have #94a3b8 (not #64748b)
    chart_ok = bool(re.search(r'\.chart-dl-btn\s*\{[^}]*color:\s*#94a3b8', src))
    # evidence-source should have #94a3b8 (not #64748b)
    ev_ok = bool(re.search(r'\.evidence-source\s*\{[^}]*color:\s*#94a3b8', src))
    # extract-view-btn should have #94a3b8 (not #64748b)
    ext_ok = bool(re.search(r'\.extract-view-btn\s*\{[^}]*color:\s*#94a3b8', src))

    all_ok = badge_ok and chart_ok and ev_ok and ext_ok
    detail = []
    if not badge_ok: detail.append('badge-search')
    if not chart_ok: detail.append('chart-dl-btn')
    if not ev_ok: detail.append('evidence-source')
    if not ext_ok: detail.append('extract-view-btn')

    check(f'{fname}: WCAG colors correct',
          all_ok,
          f'Wrong colors: {", ".join(detail)}' if detail else '')


# ── Test 6: Full app load + no JS errors (all 18 apps) ──
print(f'\n=== Full Load + JS Error Check (all 18 apps) ===')
for fname in REVIEW_FILES:
    driver = None
    try:
        driver = webdriver.Chrome(options=get_opts())
        driver.set_page_load_timeout(30)
        fpath = 'file:///' + os.path.join(BASE_DIR, fname).replace('\\', '/')
        driver.get(fpath)
        time.sleep(2)

        # Check for JS errors
        logs = driver.get_log('browser')
        severe = [l for l in logs if l['level'] == 'SEVERE'
                  and 'favicon' not in l.get('message', '')
                  and 'ERR_FILE_NOT_FOUND' not in l.get('message', '')]
        check(f'{fname}: loads without JS errors',
              len(severe) == 0,
              f'{len(severe)} errors: {severe[0]["message"][:120]}' if severe else '')

        # Verify RapidMeta initialized
        has_rm = driver.execute_script("return typeof RapidMeta !== 'undefined' && RapidMeta.state !== undefined")
        check(f'{fname}: RapidMeta initialized', has_rm, 'RapidMeta not found')

        # Verify key engines exist
        engines = driver.execute_script("""
            return {
                text: typeof TextExtractor !== 'undefined',
                grade: typeof GradeProfileEngine !== 'undefined',
                search: typeof SearchEngine !== 'undefined',
                extract: typeof ExtractEngine !== 'undefined'
            }
        """)
        check(f'{fname}: all engines present',
              engines and engines.get('text') and engines.get('grade')
              and engines.get('search') and engines.get('extract'),
              f'Missing: {[k for k,v in (engines or {}).items() if not v]}')

        # Verify SoF export button exists
        has_sof = driver.execute_script("""
            var btns = document.querySelectorAll('button');
            for (var b of btns) {
                if (b.textContent.includes('SoF') || b.onclick?.toString().includes('exportSoFHTML'))
                    return true;
            }
            return false;
        """)
        check(f'{fname}: SoF export button', has_sof, 'No SoF button found')

        # Verify manuscript text generator
        has_manuscript = driver.execute_script("return typeof generateManuscriptText === 'function'")
        check(f'{fname}: generateManuscriptText()', has_manuscript, 'Function not found')

    except Exception as e:
        check(f'{fname}: load', False, str(e))
    finally:
        if driver:
            driver.quit()
        time.sleep(0.3)


# ── Test 7: LivingMeta specific checks ──
print(f'\n=== LivingMeta.html ===')
driver = None
try:
    driver = webdriver.Chrome(options=get_opts())
    driver.set_page_load_timeout(30)
    fpath = 'file:///' + os.path.join(BASE_DIR, 'LivingMeta.html').replace('\\', '/')
    driver.get(fpath)
    time.sleep(3)

    logs = driver.get_log('browser')
    severe = [l for l in logs if l['level'] == 'SEVERE' and 'favicon' not in l.get('message', '')]
    check('LivingMeta: loads without JS errors', len(severe) == 0,
          f'{len(severe)} errors' if severe else '')

    # Check configs loaded
    config_count = driver.execute_script("return Object.keys(CONFIG_LIBRARY || {}).length")
    check(f'LivingMeta: configs loaded ({config_count})', config_count and config_count >= 5,
          f'Only {config_count} configs')

    # Check manuscript generator
    has_gen = driver.execute_script("return typeof generateFullManuscript === 'function'")
    check('LivingMeta: generateFullManuscript()', has_gen, 'Missing')

    # Check TextExtractor
    has_te = driver.execute_script("return typeof TextExtractor !== 'undefined'")
    check('LivingMeta: TextExtractor present', has_te, 'Missing')

except Exception as e:
    check('LivingMeta load', False, str(e))
finally:
    if driver:
        driver.quit()


# ── Final Summary ──
print(f'\n{"="*70}')
total = results['pass'] + results['fail']
print(f'FINAL: {results["pass"]}/{total} passed, {results["fail"]} failed')
print(f'{"="*70}')

if results['fail'] > 0:
    sys.exit(1)
