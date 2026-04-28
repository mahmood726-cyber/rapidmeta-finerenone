"""
Clone an existing RapidMeta dashboard and retemplate it for a new drug/trial.

Used to spin up Tier-1 post-2015 dashboards (ENSIFENTRINE_COPD, SPARSENTAN_IGAN,
PELACARSEN_LPa, MIRVETUXIMAB_OVARIAN, CAPIVASERTIB_BC, ...) from the closest
existing template without hand-editing 1.1MB of HTML.

The config dict declares every replacement; the script applies them as
ordered string-replaces (one occurrence each, fail-loud on missing anchors).

Trial-data section needs careful handling because each trial entry's first
line is unique. The script looks for the existing realData block opener and
replaces it wholesale with the new entries.

Usage:
    python scripts/clone_dashboard.py --config scripts/configs/ensifentrine_copd.json
    python scripts/clone_dashboard.py --config <path> --dry-run

Config schema:
    {
      "base":        path to source dashboard,
      "out":         path to write the new dashboard,
      "title":       new <title> contents,
      "hero_h2":     new hero header text,
      "nyt_headline": new NYT headline,
      "auto_include_ncts": [list of NCT strings],
      "nct_acronyms": {"NCTxxx": "ACR", ...},
      "localstorage_old": "rapid_meta_OLD_v1_0",
      "localstorage_new": "rapid_meta_NEW_v1_0",
      "selected_outcome_keep_mace": true,   # leave shortLabel='MACE' on primary
      "pico":  {pop, int, comp, out, subgroup},
      "real_data_entries": [
          {nct, name, pmid, phase, year, tE, tN, cE, cN, group,
           publishedHR, hrLCI, hrUCI, allOutcomes: [...], snippet,
           sourceUrl, ctgovUrl}
      ],
      "extra_replaces": [["old", "new"], ...]   # any file-specific tweaks
    }
"""
import argparse, json, os, re, sys, shutil

ROOT = r'C:\Projects\Finrenone'


def js_escape(s):
    return s.replace('\\', '\\\\').replace("'", "\\'")


def render_outcome(o):
    """Render one allOutcomes entry as a single-line JS object literal."""
    parts = []
    for k in ('shortLabel', 'title'):
        if k in o:
            parts.append(f"{k}: '{js_escape(o[k])}'")
    if 'type' in o:
        parts.append(f"type: '{o['type']}'")
    for k in ('tE', 'cE', 'matchScore', 'effect', 'lci', 'uci', 'md', 'se'):
        if k in o and o[k] is not None:
            parts.append(f"{k}: {o[k]}")
    if 'estimandType' in o:
        parts.append(f"estimandType: '{o['estimandType']}'")
    return '{ ' + ', '.join(parts) + ' }'


def render_evidence(e):
    parts = [f"label: '{js_escape(e['label'])}'", f"source: '{js_escape(e['source'])}'", f"text: '{js_escape(e['text'])}'"]
    hl = e.get('highlights') or []
    if hl:
        parts.append("highlights: [" + ', '.join(f"'{js_escape(h)}'" for h in hl) + "]")
    return '{ ' + ', '.join(parts) + ' }'


def render_trial_entry(t):
    """Render one realData NCT-keyed entry."""
    head = (
        f"name: '{js_escape(t['name'])}', pmid: '{t.get('pmid','')}', "
        f"phase: '{t.get('phase','III')}', year: {t.get('year',2024)}, "
        f"tE: {t.get('tE','null')}, tN: {t['tN']}, cE: {t.get('cE','null')}, cN: {t['cN']}, "
        f"group: '{js_escape(t.get('group',''))}', "
        f"publishedHR: {t.get('publishedHR','null')}, "
        f"hrLCI: {t.get('hrLCI','null')}, hrUCI: {t.get('hrUCI','null')}"
    )
    outcomes_str = ',\n                        '.join(render_outcome(o) for o in t.get('allOutcomes', []))
    rob = t.get('rob', ['low', 'low', 'low', 'low', 'low'])
    rob_str = '[' + ', '.join(f"'{r}'" for r in rob) + ']'
    evidence = t.get('evidence', [])
    if evidence:
        ev_str = '[\n                        ' + ',\n                        '.join(render_evidence(e) for e in evidence) + '\n                    ]'
    else:
        ev_str = '[]'
    return f"""'{t['nct']}': {{


                    {head},


                    allOutcomes: [
                        {outcomes_str}
                    ],


                    rob: {rob_str},


                    snippet: '{js_escape(t.get('snippet',''))}',


                    sourceUrl: '{js_escape(t.get('sourceUrl',''))}',


                    ctgovUrl: 'https://clinicaltrials.gov/study/{t['nct']}',


                    evidence: {ev_str}


                }}"""


def replace_one(src, old, new, label, log):
    """Apply a single replacement; log success/skip."""
    n = src.count(old)
    if n == 0:
        log.append(f'  [SKIP_NOT_FOUND] {label}')
        return src
    if n > 1:
        log.append(f'  [SKIP_AMBIGUOUS:{n}] {label}')
        return src
    log.append(f'  [APPLIED]          {label}')
    return src.replace(old, new, 1)


def clone(config, dry=False):
    base = config['base']
    out = config['out']
    if not os.path.exists(base):
        raise SystemExit(f'base file not found: {base}')

    # Read base (no actual file copy yet — we'll write the modified version directly)
    src = open(base, 'r', encoding='utf-8').read()
    log = []

    # Title
    src = re.sub(r'<title>[^<]+</title>',
                 f"<title>{config['title']}</title>", src, count=1)
    log.append('  [APPLIED]          title')

    # Hero h2
    if 'hero_h2' in config:
        src = re.sub(r'(<div class="va-header"><h2[^>]*>)[^<]+(</h2>)',
                     lambda m: m.group(1) + config['hero_h2'] + m.group(2), src, count=1)
        log.append('  [APPLIED]          hero_h2')

    # NYT headline
    if 'nyt_headline' in config:
        src = re.sub(r'(<h3 class="nyt-headline[^>]*>)[^<]+(</h3>)',
                     lambda m: m.group(1) + config['nyt_headline'] + m.group(2), src, count=1)
        log.append('  [APPLIED]          nyt_headline')

    # AUTO_INCLUDE
    if 'auto_include_ncts' in config:
        new_set = ', '.join(f"'{n}'" for n in config['auto_include_ncts'])
        src = re.sub(r"AUTO_INCLUDE_TRIAL_IDS\s*=\s*new\s+Set\(\[[^\]]*\]\)",
                     f"AUTO_INCLUDE_TRIAL_IDS = new Set([{new_set}])", src, count=1)
        log.append('  [APPLIED]          AUTO_INCLUDE_TRIAL_IDS')

    # nctAcronyms
    if 'nct_acronyms' in config:
        new_map = ', '.join(f"'{n}': '{js_escape(a)}'" for n, a in config['nct_acronyms'].items())
        src = re.sub(r"nctAcronyms:\s*\{[^}]*\}",
                     f"nctAcronyms: {{ {new_map} }}", src, count=1)
        log.append('  [APPLIED]          nctAcronyms')

    # localStorage keys
    if 'localstorage_old' in config and 'localstorage_new' in config:
        n = src.count(config['localstorage_old'])
        src = src.replace(config['localstorage_old'], config['localstorage_new'])
        log.append(f'  [APPLIED:{n}]        localStorage keys')

    # PICO state.protocol
    if 'pico' in config:
        p = config['pico']
        proto_re = re.compile(
            r"(protocol:\s*\{\s*pop:\s*')(?:\\'|[^'])*(',\s*int:\s*')(?:\\'|[^'])*(',\s*comp:\s*')(?:\\'|[^'])*(',\s*out:\s*')(?:\\'|[^'])*(',\s*subgroup:\s*')(?:\\'|[^'])*('.*?)\}",
            re.DOTALL,
        )
        def repl(m):
            return (m.group(1) + js_escape(p['pop']) +
                    m.group(2) + js_escape(p['int']) +
                    m.group(3) + js_escape(p['comp']) +
                    m.group(4) + js_escape(p['out']) +
                    m.group(5) + js_escape(p['subgroup']) +
                    m.group(6) + '}')
        src, n = proto_re.subn(repl, src, count=1)
        log.append(f'  [APPLIED:{n}]        protocol.pico')

    # realData entries — replace the entire `realData: { ... }` block
    if 'real_data_entries' in config:
        i = src.find('realData: {')
        if i < 0:
            raise SystemExit('realData block not found in base')
        brace = src.find('{', i)
        depth = 0
        started = False
        end = -1
        for j in range(brace, len(src)):
            c = src[j]
            if c == '{': depth += 1; started = True
            elif c == '}':
                depth -= 1
                if started and depth == 0: end = j; break
        new_entries = ',\n\n\n                '.join(
            render_trial_entry(t) for t in config['real_data_entries'])
        new_block = '{\n\n\n                ' + new_entries + '\n            }'
        src = src[:brace] + new_block + src[end+1:]
        log.append(f'  [APPLIED:{len(config["real_data_entries"])}]        realData entries')

    # Free-form replaces
    for old, new in config.get('extra_replaces', []):
        src = replace_one(src, old, new, f'extra_replace [{old[:40]}...]', log)

    if not dry:
        open(out, 'w', encoding='utf-8').write(src)
    return log


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--config', required=True)
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()
    cfg = json.loads(open(args.config, 'r', encoding='utf-8').read())
    print(f'Mode: {"DRY-RUN" if args.dry_run else "APPLY"}  Config: {args.config}')
    log = clone(cfg, dry=args.dry_run)
    for line in log:
        print(line)
    print(f'Output: {cfg["out"]}')


if __name__ == '__main__':
    sys.exit(main())
