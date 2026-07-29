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
import argparse, os, json, os, re, sys, shutil

ROOT = os.environ.get('RAPIDMETA_REPO_ROOT', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


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
    for k in ('tE', 'cE', 'matchScore', 'effect', 'lci', 'uci', 'md', 'se',
              'pubHR', 'pubHR_LCI', 'pubHR_UCI'):
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


def trial_key(t):
    """realData key for one trial. Registry trials use their NCT id; PRE-REGISTRY
    trials (CONSENSUS 1987, SOLVD, MERIT-HF, RALES, CIBIS, COPERNICUS, EMPHASIS,
    CARMEN ...) have no NCT and are keyed by published acronym + a PMID so the
    identity stays checkable. A key that imitates an NCT without a verified
    `nct` field is refused - never invent a registry id."""
    nct = (t.get('nct') or '').strip()
    key = (t.get('key') or '').strip()
    if nct:
        if not re.match(r'^NCT\d{8}$', nct):
            raise SystemExit(f"malformed NCT id {nct!r} for {t.get('name')!r}")
        return nct
    if not key:
        raise SystemExit(f"trial {t.get('name')!r} has neither `nct` nor `key`")
    if key.upper().startswith('NCT'):
        raise SystemExit(f"key {key!r} imitates a registry id but no verified "
                         f"`nct` was supplied - refusing to invent an NCT")
    if not re.match(r'^[A-Za-z][A-Za-z0-9_\-]{2,39}$', key):
        raise SystemExit(f"key {key!r} is not a usable trial acronym")
    if not str(t.get('pmid') or '').strip().isdigit():
        raise SystemExit(f"pre-registry trial {key!r} needs a numeric `pmid`")
    return key


def render_trial_entry(t):
    """Render one realData entry (NCT- or acronym-keyed)."""
    head = (
        f"name: '{js_escape(t['name'])}', pmid: '{t.get('pmid','')}', "
        f"phase: '{t.get('phase','III')}', year: {t.get('year',2024)}, "
        f"tE: {t.get('tE','null')}, tN: {t['tN']}, cE: {t.get('cE','null')}, cN: {t['cN']}, "
        f"group: '{js_escape(t.get('group',''))}', "
        f"publishedHR: {t.get('publishedHR','null')}, "
        f"hrLCI: {t.get('hrLCI','null')}, hrUCI: {t.get('hrUCI','null')}, "
        f"pubHR: {t.get('pubHR', t.get('publishedHR','null'))}, "
        f"pubHR_LCI: {t.get('pubHR_LCI', t.get('hrLCI','null'))}, "
        f"pubHR_UCI: {t.get('pubHR_UCI', t.get('hrUCI','null'))}"
    )
    outcomes_str = ',\n                        '.join(render_outcome(o) for o in t.get('allOutcomes', []))
    rob = t.get('rob', ['low', 'low', 'low', 'low', 'low'])
    rob_str = '[' + ', '.join(f"'{r}'" for r in rob) + ']'
    evidence = t.get('evidence', [])
    if evidence:
        ev_str = '[\n                        ' + ',\n                        '.join(render_evidence(e) for e in evidence) + '\n                    ]'
    else:
        ev_str = '[]'
    return f"""'{trial_key(t)}': {{


                    {head},


                    allOutcomes: [
                        {outcomes_str}
                    ],


                    rob: {rob_str},


                    snippet: '{js_escape(t.get('snippet',''))}',


                    sourceUrl: '{js_escape(t.get('sourceUrl',''))}',


                    ctgovUrl: '{("https://clinicaltrials.gov/study/" + t['nct']) if t.get('nct') else js_escape(t.get('sourceUrl',''))}',


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

    # PICO state.protocol. Tolerant of single- OR double-quoted values: the
    # original base used single quotes (pop:'...'), the minified base uses
    # double quotes (pop:"..."). Each field's quote char is captured and the
    # replacement value is escaped for that exact delimiter.
    if 'pico' in config:
        p = config['pico']
        # field-value: opening quote (group), then any escaped char or
        # non-delimiter char, then the matching closing quote (backref).
        def fld(key, qgrp):
            return rf"(\s*,?\s*{key}:\s*)(['\"])(?:\\.|(?!\{qgrp}).)*\{qgrp}"
        proto_re = re.compile(
            r"(protocol:\s*\{\s*pop:\s*)(['\"])(?:\\.|(?!\2).)*\2"
            + fld("int", 4) + fld("comp", 6) + fld("out", 8) + fld("subgroup", 10),
            re.DOTALL,
        )

        def _esc(val, q):
            return val.replace('\\', '\\\\').replace(q, '\\' + q)

        def repl(m):
            pre = [m.group(1), m.group(3), m.group(5), m.group(7), m.group(9)]
            q = [m.group(2), m.group(4), m.group(6), m.group(8), m.group(10)]
            vals = [p['pop'], p['int'], p['comp'], p['out'], p['subgroup']]
            return ''.join(
                pre[i] + q[i] + _esc(vals[i], q[i]) + q[i] for i in range(5)
            )
        src, n = proto_re.subn(repl, src, count=1)
        log.append(f'  [APPLIED:{n}]        protocol.pico')

    # realData entries — replace the entire `realData: { ... }` block.
    # Tolerant of a minified base (`realData:{`) as well as the original
    # pretty-printed form (`realData: {`).
    if 'real_data_entries' in config:
        m = re.search(r'realData\s*:\s*\{', src)
        if not m:
            raise SystemExit('realData block not found in base')
        brace = src.index('{', m.start())
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

    # Blank hardcoded external benchmarks (e.g. PUBLISHED_META_BENCHMARKS with
    # 'BOREAS dupilumab vs placebo' estimate 0.7) — a false reference for any
    # other topic. Per-topic benchmarks are not available for audit-first
    # builds, so the honest value is an empty object.
    if config.get('blank_benchmarks'):
        # Tolerant of both the original (`const PUBLISHED_META_BENCHMARKS = {
        # ...\n};`) and the minified (`,PUBLISHED_META_BENCHMARKS={...}`) forms:
        # locate the identifier, then brace-scan its object literal and blank it.
        bm = re.search(r"PUBLISHED_META_BENCHMARKS\s*[:=]\s*\{", src)
        if bm:
            obrace = src.index('{', bm.start())
            depth, end = 0, -1
            for j in range(obrace, len(src)):
                if src[j] == '{':
                    depth += 1
                elif src[j] == '}':
                    depth -= 1
                    if depth == 0:
                        end = j
                        break
            if end > 0:
                src = src[:obrace] + '{}' + src[end + 1:]
                log.append('  [APPLIED]          blank_benchmarks (PUBLISHED_META_BENCHMARKS={})')
            else:
                log.append('  [SKIP_NOT_FOUND]   blank_benchmarks (unbalanced braces)')
        else:
            log.append('  [SKIP_NOT_FOUND]   blank_benchmarks')

    # Free-form replaces (precise, single-occurrence claim neutralizers).
    # These run BEFORE global_replaces so claim-bearing strings (mechanism,
    # phenotype) are neutralized to data-driven text rather than token-swapped
    # into a false claim (e.g. "tezepelumab (IL-4Ralpha ...)").
    for old, new in config.get('extra_replaces', []):
        src = replace_one(src, old, new, f'extra_replace [{old[:40]}...]', log)

    # Global replaces — unconditional replace-ALL. This is the fix for the
    # n>1 SKIP_AMBIGUOUS bug: residual base tokens (dupilumab, COPD, base
    # localStorage key, export filenames, base trial acronyms) appear many
    # times in JS string literals and MUST all be swapped. Order matters:
    # longest/compound tokens first so 'dupilumab' inside 'dupilumab_copd'
    # or 'rapid_meta_dupilumab_copd' is not partially clobbered.
    for old, new in config.get('global_replaces', []):
        n = src.count(old)
        if n == 0:
            log.append(f'  [SKIP_NOT_FOUND]   global [{old[:40]}]')
            continue
        src = src.replace(old, new)
        log.append(f'  [APPLIED:{n}]        global [{old[:40]} -> {new[:30]}]')

    if not dry:
        open(out, 'w', encoding='utf-8').write(src)
        # Auto-minify the inline engine block. Without this, freshly cloned
        # pages ship the ~1 MB unminified engine and accumulate Lighthouse
        # debt until a follow-up minify pass runs. Soft-fail if Node/terser
        # isn't available so the clone itself still succeeds.
        _minify_engine_in_place(out, log)
    return log


def _minify_engine_in_place(path, log):
    """Best-effort terser pass on the inline engine block of a cloned page.
    Mirrors what scripts/minify_all_engines.mjs does for the bulk-portfolio
    case. Logs success or skip; does not raise.
    """
    import subprocess
    script = os.path.join(ROOT, 'scripts', 'minify_engine_block.mjs')
    if not os.path.exists(script):
        log.append('  [SKIP_MINIFY]      minify_engine_block.mjs not present')
        return
    node = 'node.exe' if os.name == 'nt' else 'node'
    try:
        proc = subprocess.run(
            [node, script, path, path],  # read and write same file
            capture_output=True, text=True, timeout=120,
            encoding='utf-8', errors='replace',
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as e:
        log.append(f'  [SKIP_MINIFY]      {type(e).__name__}')
        return
    if proc.returncode == 0:
        # terser writes its stats to stderr (see minify_engine_block.mjs)
        last = (proc.stderr or '').strip().splitlines()
        savings = last[-2] if len(last) >= 2 else (last[0] if last else 'minified')
        log.append(f'  [APPLIED]          terser: {savings[:80]}')
    else:
        log.append(f'  [SKIP_MINIFY]      terser rc={proc.returncode}: {(proc.stderr or "")[:100]}')


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
