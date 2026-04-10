#!/usr/bin/env python
"""
CT.gov Mining → Atlas Integration Report.

Diffs ctgov_mining_results.json against cardiology_mortality_atlas.json:
  1. Discrepancies — atlas HR vs CT.gov HR (>20% deviation OR non-overlapping CIs)
  2. Atlas gaps — trials in atlas with no HR but CT.gov has one
  3. Mining surplus — CT.gov-only trials (UNMAPPED) that should join an existing class
  4. Source provenance — analyses vs Peto-derived HR mix

Discrepancy threshold (DOMAIN DECISION):
  Currently set to 20% absolute deviation in HR OR non-overlapping CIs.
  TODO Mahmood: refine if too loose/tight. Options:
    - 5% (atlas default — very tight, will flag rounding)
    - 10% (moderate — flag clinically meaningful disagreements)
    - 20% (loose — only flag major divergence)
    - CI-overlap-only (purely statistical, ignores effect size)
"""
import sys, io, os, json, math
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

DISCREPANCY_PCT = 0.05  # 5% relative deviation in HR — strict audit threshold


def cis_overlap(lo1, hi1, lo2, hi2):
    return not (hi1 < lo2 or hi2 < lo1)


def main():
    with open('ctgov_mining_results.json', 'r', encoding='utf-8') as f:
        mined = json.load(f)
    with open('cardiology_mortality_atlas.json', 'r', encoding='utf-8') as f:
        atlas = json.load(f)

    nct_to_class = {}
    nct_to_atlas_trial = {}
    for cls in atlas['classes']:
        for t in cls.get('trials', []):
            nct = t.get('nct') or t.get('id')
            if nct:
                nct_to_class[nct] = cls['drug_class']
                nct_to_atlas_trial[nct] = t

    # Collect by category
    discrepancies = []
    confirmations = []
    atlas_gaps_filled = []  # atlas trial had no HR; mining provided one
    source_mix = {'analyses': 0, 'peto_logrank': 0}
    unmapped_trials = []

    for nct, info in mined.items():
        outcomes = info.get('outcomes', {})
        acm = outcomes.get('ACM')
        cls = nct_to_class.get(nct)

        # Track source mix
        for tag in ('ACM', 'CV_death', 'HF_hosp'):
            o = outcomes.get(tag)
            if o:
                src = o.get('source', 'analyses')
                source_mix[src] = source_mix.get(src, 0) + 1

        if not cls:
            # Unmapped — find what classes/conditions it might fit
            unmapped_trials.append({
                'nct': nct,
                'title': info.get('title', '')[:80],
                'app': info.get('app', ''),
                'has_acm': acm is not None,
                'acm_hr': acm['est'] if acm else None,
                'acm_source': acm.get('source') if acm else None,
            })
            continue

        atlas_t = nct_to_atlas_trial[nct]
        atlas_hr = atlas_t.get('hr')
        atlas_lci = atlas_t.get('lo') or atlas_t.get('lci') or atlas_t.get('ci_low')
        atlas_uci = atlas_t.get('hi') or atlas_t.get('uci') or atlas_t.get('ci_high')

        if not acm:
            continue

        if atlas_hr is None:
            atlas_gaps_filled.append({
                'nct': nct, 'class': cls,
                'trial': atlas_t.get('name', nct),
                'mined_hr': acm['est'],
                'mined_ci': f'{acm["lci"]:.2f}-{acm["uci"]:.2f}',
                'source': acm.get('source', 'analyses'),
            })
            continue

        # Both present — compare
        rel_diff = abs(acm['est'] - atlas_hr) / atlas_hr
        ci_overlap = (atlas_lci is not None and atlas_uci is not None
                      and cis_overlap(atlas_lci, atlas_uci, acm['lci'], acm['uci']))
        is_discrepancy = rel_diff > DISCREPANCY_PCT or not ci_overlap

        record = {
            'nct': nct, 'class': cls,
            'trial': atlas_t.get('name', nct),
            'atlas_hr': atlas_hr,
            'atlas_ci': f'{atlas_lci}-{atlas_uci}' if atlas_lci else 'n/a',
            'mined_hr': acm['est'],
            'mined_ci': f'{acm["lci"]:.2f}-{acm["uci"]:.2f}',
            'rel_diff_pct': round(rel_diff * 100, 1),
            'ci_overlap': ci_overlap,
            'source': acm.get('source', 'analyses'),
        }
        if is_discrepancy:
            discrepancies.append(record)
        else:
            confirmations.append(record)

    # Build report
    lines = []
    lines.append('# CT.gov Mining → Atlas Integration Report\n\n')
    lines.append(f'**Discrepancy threshold:** {DISCREPANCY_PCT*100:.0f}% relative HR deviation OR non-overlapping CIs\n\n')
    lines.append(f'## Summary\n\n')
    lines.append(f'- Trials mined: **{len(mined)}**\n')
    lines.append(f'- HR sources: **{source_mix.get("analyses",0)}** from CT.gov analyses, **{source_mix.get("peto_logrank",0)}** Peto-derived from event counts\n')
    lines.append(f'- Atlas confirmations (within tolerance): **{len(confirmations)}**\n')
    lines.append(f'- **Discrepancies flagged:** **{len(discrepancies)}**\n')
    lines.append(f'- **Atlas gaps filled by mining:** **{len(atlas_gaps_filled)}**\n')
    lines.append(f'- **CT.gov trials unmapped to atlas classes:** **{len(unmapped_trials)}**\n')

    if discrepancies:
        lines.append('\n## Discrepancies (require review)\n\n')
        lines.append('| NCT | Class | Trial | Atlas HR | Mined HR | Δ% | CIs overlap | Source |\n')
        lines.append('|---|---|---|---|---|---|---|---|\n')
        for d in sorted(discrepancies, key=lambda x: -x['rel_diff_pct']):
            ovlap = '✓' if d['ci_overlap'] else '✗'
            lines.append(
                f'| {d["nct"]} | {d["class"][:20]} | {d["trial"][:25]} | '
                f'{d["atlas_hr"]:.3f} ({d["atlas_ci"]}) | '
                f'{d["mined_hr"]:.3f} ({d["mined_ci"]}) | '
                f'{d["rel_diff_pct"]:.1f}% | {ovlap} | {d["source"]} |\n'
            )

    if atlas_gaps_filled:
        lines.append('\n## Atlas gaps filled by CT.gov mining\n\n')
        lines.append('| NCT | Class | Trial | Mined HR | Source |\n')
        lines.append('|---|---|---|---|---|\n')
        for g in atlas_gaps_filled:
            lines.append(
                f'| {g["nct"]} | {g["class"][:20]} | {g["trial"][:25]} | '
                f'{g["mined_hr"]:.3f} ({g["mined_ci"]}) | {g["source"]} |\n'
            )

    if unmapped_trials:
        lines.append(f'\n## Unmapped trials ({len(unmapped_trials)})\n\n')
        lines.append('CT.gov trials returned by search but not currently in any atlas pool. '
                     'Review for possible inclusion as new pool members or new drug classes.\n\n')
        with_acm = [u for u in unmapped_trials if u['has_acm']]
        without_acm = [u for u in unmapped_trials if not u['has_acm']]
        lines.append(f'- With ACM data: **{len(with_acm)}**\n')
        lines.append(f'- Without ACM data: **{len(without_acm)}**\n\n')
        if with_acm:
            lines.append('### Unmapped trials with ACM data\n\n')
            lines.append('| NCT | Title | ACM HR | Source |\n|---|---|---|---|\n')
            for u in with_acm:
                lines.append(f'| {u["nct"]} | {u["title"][:60]} | {u["acm_hr"]:.3f} | {u["acm_source"]} |\n')

    if confirmations:
        lines.append(f'\n## Confirmations ({len(confirmations)})\n\n')
        lines.append('Atlas HR within tolerance of CT.gov-mined HR.\n\n')
        lines.append('| NCT | Class | Trial | Atlas HR | Mined HR | Δ% | Source |\n')
        lines.append('|---|---|---|---|---|---|---|\n')
        for c in sorted(confirmations, key=lambda x: x['class']):
            lines.append(
                f'| {c["nct"]} | {c["class"][:20]} | {c["trial"][:25]} | '
                f'{c["atlas_hr"]:.3f} | {c["mined_hr"]:.3f} | '
                f'{c["rel_diff_pct"]:.1f}% | {c["source"]} |\n'
            )

    with open('ctgov_integration_report.md', 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print(f'Wrote ctgov_integration_report.md')
    print(f'  discrepancies: {len(discrepancies)}')
    print(f'  confirmations: {len(confirmations)}')
    print(f'  atlas gaps filled: {len(atlas_gaps_filled)}')
    print(f'  unmapped: {len(unmapped_trials)}')
    print(f'  source mix: {source_mix}')


if __name__ == '__main__':
    main()
