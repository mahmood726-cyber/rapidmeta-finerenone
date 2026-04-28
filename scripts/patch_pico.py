"""
Patch the state.protocol literal in 8 pairwise reviews where the PICO was
copy-pasted from a sibling template and never replaced.

Surgical fix: replaces only the `protocol: { pop:..., int:..., comp:..., out:..., subgroup:... }`
literal in the state object. Trial data, narrative, and other parts of each
dashboard are already correct (verified by trial-name audit).

Usage:
    python scripts/patch_pico.py --dry-run    # report only
    python scripts/patch_pico.py              # apply
"""
import argparse, os, re, sys

ROOT = r'C:\Projects\Finrenone'

# Per-file correct PICO. Each tuple is (pop, int, comp, out, subgroup).
# Sourced from each dashboard's actual trial(s) — primary endpoints per protocol/SAP.
PICO = {
    'AFICAMTEN_HCM_REVIEW.html': (
        'Adults with symptomatic obstructive HCM (NYHA II-III) on standard-of-care therapy',
        'Aficamten (next-generation cardiac myosin inhibitor)',
        'Placebo',
        'Change in pVO2 from baseline to week 24 (SEQUOIA-HCM primary)',
        'NYHA class, beta-blocker use, baseline LVOT gradient',
    ),
    'ETRASIMOD_UC_REVIEW.html': (
        'Adults with moderate-to-severe ulcerative colitis',
        'Etrasimod (oral S1P receptor modulator)',
        'Placebo',
        'Clinical remission at week 12 (induction) and week 52 (maintenance)',
        'Biologic-naive vs experienced, disease activity, prior JAK exposure',
    ),
    'RESMETIROM_MASH_REVIEW.html': (
        'Adults with biopsy-confirmed MASH (formerly NASH) and F2-F3 fibrosis (non-cirrhotic)',
        'Resmetirom (oral thyroid hormone receptor-beta agonist)',
        'Placebo',
        'NASH resolution and/or >=1-stage fibrosis improvement at 52 weeks (MAESTRO-NASH)',
        'Fibrosis stage (F2 vs F3), T2DM status, baseline liver stiffness',
    ),
    'SOTATERCEPT_PAH_REVIEW.html': (
        'Adults with pulmonary arterial hypertension (WHO Group 1, FC II-III) on background therapy',
        'Sotatercept (activin-signaling inhibitor)',
        'Placebo',
        'Change in 6-minute walk distance at week 24 (STELLAR primary)',
        'PAH etiology, background therapy, REVEAL 2.0 risk score',
    ),
    'VOCLOSPORIN_LN_REVIEW.html': (
        'Adults with biopsy-proven active lupus nephritis (Class III/IV +/- V)',
        'Voclosporin + MMF + low-dose steroids',
        'MMF + low-dose steroids + placebo',
        'Complete renal response at 52 weeks (AURORA-1 primary)',
        'Race/ethnicity, baseline UPCR, MMF dose',
    ),
    'VORASIDENIB_GLIOMA_REVIEW.html': (
        'Adults with residual or recurrent IDH1/2-mutant grade 2 glioma after surgery',
        'Vorasidenib (oral dual IDH1/2 inhibitor)',
        'Placebo',
        'Imaging-based progression-free survival by BIRC (INDIGO primary)',
        'IDH mutation type (IDH1 vs IDH2), 1p/19q codeletion, baseline tumor volume',
    ),
    'BEMPEDOIC_ACID_REVIEW.html': (
        'Adults with statin-intolerance and ASCVD or high CV risk + elevated LDL-C',
        'Bempedoic acid 180 mg daily',
        'Placebo',
        '4-point MACE (CV death, nonfatal MI, nonfatal stroke, coronary revascularization)',
        'Primary vs secondary prevention, baseline LDL-C, sex',
    ),
    'INTENSIVE_BP_REVIEW.html': (
        'Adults at high CV risk without diabetes (SPRINT-eligible, SBP 130-180 mmHg)',
        'Intensive BP control (SBP target <120 mmHg)',
        'Standard BP control (SBP target <140 mmHg)',
        'Composite of MI, ACS, stroke, HF, or CV death (SPRINT primary)',
        'Age (>=75 vs <75), prior CKD, baseline SBP',
    ),
}


# Match the existing protocol literal regardless of values: anchor by the keys.
# Capture the protocol object opening through closing brace and replace.
PROTO_LINE_RE = re.compile(
    r"protocol:\s*\{\s*pop:\s*'(?:\\'|[^'])*',\s*int:\s*'(?:\\'|[^'])*',\s*comp:\s*'(?:\\'|[^'])*',\s*out:\s*'(?:\\'|[^'])*',\s*subgroup:\s*'(?:\\'|[^'])*',(\s*query:\s*'[^']*',\s*rctOnly:\s*\w+,\s*post2015:\s*\w+\s*)\}"
)


def js_escape(s):
    """Escape apostrophes for JS single-quoted string."""
    return s.replace("\\", "\\\\").replace("'", "\\'")


def build_protocol_literal(pop, intv, comp, out, sub, tail):
    return (f"protocol: {{ pop: '{js_escape(pop)}', int: '{js_escape(intv)}', "
            f"comp: '{js_escape(comp)}', out: '{js_escape(out)}', subgroup: '{js_escape(sub)}',"
            f"{tail}}}")


def patch_file(path, pop, intv, comp, out, sub, dry=False):
    src = open(path, 'r', encoding='utf-8').read()
    matches = list(PROTO_LINE_RE.finditer(src))
    if len(matches) == 0:
        return False, 'NO_MATCH (regex did not find protocol literal)'
    if len(matches) > 1:
        return False, f'AMBIGUOUS ({len(matches)} matches)'
    m = matches[0]
    tail = m.group(1)
    new_literal = build_protocol_literal(pop, intv, comp, out, sub, tail)
    new_src = src[:m.start()] + new_literal + src[m.end():]
    if new_src == src:
        return False, 'NO_CHANGE'
    if not dry:
        open(path, 'w', encoding='utf-8').write(new_src)
    # Snippet of new literal for verification
    return True, new_literal[:140] + '...'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()
    print(f'Mode: {"DRY-RUN" if args.dry_run else "APPLY"}')
    summary = {'changed': 0, 'unchanged': 0, 'errors': 0}
    for fname, (pop, intv, comp, out, sub) in PICO.items():
        path = os.path.join(ROOT, fname)
        if not os.path.exists(path):
            print(f'\n[ERROR] {fname}: not found')
            summary['errors'] += 1
            continue
        try:
            changed, info = patch_file(path, pop, intv, comp, out, sub, dry=args.dry_run)
            tag = 'CHANGED' if changed else 'no-op'
            print(f'\n[{tag}] {fname}')
            print(f'  -> {info}')
            summary['changed' if changed else 'unchanged'] += 1
        except Exception as e:
            print(f'\n[ERROR] {fname}: {e}')
            summary['errors'] += 1
    print(f'\nSummary: {summary}')
    return 0 if summary['errors'] == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
