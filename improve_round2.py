"""
Round 2 improvements for RapidMeta apps:

1. HKSJ sanity cap — cap extreme HKSJ CIs at [0.001, 999] with visual indicator
2. ARIA labels — add to stat cards, tabs, modals for screen reader accessibility
3. Print stylesheet enhancement — hide non-essential UI, improve page breaks
4. Stat card tooltips — add explanatory title attributes

Run: python improve_round2.py
"""
import os, sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

DIR = os.path.dirname(os.path.abspath(__file__))
FILES = sorted([f for f in os.listdir(DIR)
                if f.endswith('.html') and '_REVIEW' in f
                and '.bak.' not in f and 'backup' not in f.lower()])

print(f'Processing {len(FILES)} files...\n')
count = {1: 0, 2: 0, 3: 0, 4: 0}

for fname in FILES:
    path = os.path.join(DIR, fname)
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    original = content

    # ── IMPROVEMENT 1: HKSJ sanity cap ──
    # Cap extreme HKSJ CIs and add note
    OLD_HKSJ_DISPLAY = r"""hksjEl.innerText = `${c.hksjLCI.toFixed(2)} \u2014 ${c.hksjUCI.toFixed(2)}`;"""
    NEW_HKSJ_DISPLAY = r"""const _hkLo = Math.max(0.001, c.hksjLCI);
                    const _hkHi = Math.min(999, c.hksjUCI);
                    const _hkCapped = c.hksjLCI < 0.001 || c.hksjUCI > 999;
                    hksjEl.innerText = `${_hkLo.toFixed(2)} \u2014 ${_hkHi > 100 ? '>100' : _hkHi.toFixed(2)}${_hkCapped ? ' *' : ''}`;"""
    if OLD_HKSJ_DISPLAY in content:
        content = content.replace(OLD_HKSJ_DISPLAY, NEW_HKSJ_DISPLAY)
        count[1] += 1

    # ── IMPROVEMENT 2: ARIA labels on tabs ──
    # Add role="tablist" to tab container and role="tab" to tab buttons
    if 'role="tablist"' not in content:
        # Tab buttons pattern: data-tab="protocol"
        content = re.sub(
            r'(<[^>]*class="[^"]*tab-btn[^"]*"[^>]*data-tab="(\w+)")',
            r'\1 role="tab" aria-selected="false" aria-controls="tab-\2"',
            content,
            count=10  # max 10 tabs
        )
        count[2] += 1

    # Add aria-label to stat cards
    STAT_LABELS = {
        'res-or': 'Pooled effect estimate',
        'res-ci': 'Confidence interval',
        'res-i2': 'Heterogeneity I-squared',
        'res-hksj': 'HKSJ-adjusted confidence interval',
        'res-pi': 'Prediction interval',
        'res-qtest': 'Cochran Q test for heterogeneity',
    }
    for el_id, label in STAT_LABELS.items():
        old_id = f'id="{el_id}"'
        new_id = f'id="{el_id}" aria-label="{label}"'
        if old_id in content and f'aria-label="{label}"' not in content:
            content = content.replace(old_id, new_id, 1)

    # Add aria-live to sensitivity summary (updates dynamically)
    if 'sensitivity-concordance' in content and 'aria-live' not in content.split('sensitivity-concordance')[1][:100]:
        content = content.replace(
            'id="sensitivity-concordance"',
            'id="sensitivity-concordance" aria-live="polite" aria-label="Sensitivity analysis concordance summary"'
        )

    # ── IMPROVEMENT 3: Enhanced print stylesheet ──
    PRINT_ENHANCEMENT = """
        @media print {
            body { background: white !important; color: black !important; font-size: 11pt !important; }
            .glass, .stat-chip { background: white !important; border: 1px solid #ddd !important; color: black !important; }
            .stat-chip { display: inline-block !important; margin: 2px !important; padding: 4px 8px !important; }
            #sensitivity-concordance span { border: 1px solid #999 !important; }
            header, .tab-btn, .export-dropdown, button[onclick], .chart-dl-btn { display: none !important; }
            .js-plotly-plot { break-inside: avoid; max-height: 400px !important; }
            [data-tab] { display: none !important; }
            #tab-analysis, #tab-report { display: block !important; }
        }"""

    # Add after existing @media print if not already enhanced
    if 'font-size: 11pt' not in content and '@media print' in content:
        # Find last @media print block end
        last_print = content.rfind('@media print')
        if last_print > 0:
            # Find closing brace of this block
            brace_count = 0
            i = content.find('{', last_print)
            while i < len(content):
                if content[i] == '{':
                    brace_count += 1
                elif content[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        content = content[:i+1] + PRINT_ENHANCEMENT + content[i+1:]
                        count[3] += 1
                        break
                i += 1

    # ── IMPROVEMENT 4: Stat card tooltips ──
    TOOLTIPS = {
        'Heterogeneity (I': {
            'after': 'Heterogeneity (I',
            'title': 'I-squared measures the proportion of total variability due to heterogeneity rather than chance. CI shown uses Higgins-Thompson test-based method.',
        },
        'HKSJ-Adjusted CI': {
            'after': 'HKSJ-Adjusted CI',
            'title': 'Hartung-Knapp-Sidik-Jonkman adjustment uses t-distribution with k-1 df, accounting for uncertainty in tau-squared estimation. More reliable than Wald for small k.',
        },
        'Prediction Interval': {
            'after': 'Prediction Interval',
            'title': 'Predicts the range of true effects in a new similar study. Uses t-distribution with k-2 df. Wider than CI because it includes between-study variance.',
        },
    }

    for label_text, info in TOOLTIPS.items():
        # Add title attribute to the card container
        if f'>{label_text}<' in content and f'title="{info["title"]}"' not in content:
            # Find the div containing this label and add title
            idx = content.find(f'>{label_text}<')
            if idx > 0:
                # Find the enclosing div with class="glass"
                search_start = max(0, idx - 300)
                glass_idx = content.rfind('class="glass', search_start, idx)
                if glass_idx > 0:
                    div_start = content.rfind('<div', search_start, glass_idx + 1)
                    if div_start > 0:
                        insert_pt = content.find('>', div_start)
                        if insert_pt > 0 and insert_pt < idx:
                            content = content[:insert_pt] + f' title="{info["title"]}"' + content[insert_pt:]
                            count[4] += 1

    if content != original:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'  IMPROVED: {fname}')
    else:
        print(f'  SKIP: {fname}')

print(f'\n{"="*60}')
print(f'SUMMARY:')
print(f'  HKSJ sanity cap:     {count[1]} files')
print(f'  ARIA labels:         {count[2]} files')
print(f'  Print stylesheet:    {count[3]} files')
print(f'  Stat card tooltips:  {count[4]} files')
print(f'{"="*60}')
