# -*- coding: utf-8 -*-
"""One reader for risk of bias, whichever schema the object uses.

THE DRIFT WAS THREE LAYERS DEEP, so a rename fixes none of it:

  1 CONTAINER    every reader asked for canon["rob2"]; 30 of 31 stores write
                 canon["risk_of_bias"]. Result: 29 of the 30 rendered curated topics
                 printed "No per-domain RoB-2 assessment is stored in this object" over
                 a store that holds one. The single exception, arni-hfref, is the only
                 object that writes `rob2` -- which is what proved the diagnosis.

  2 GRANULARITY  canon["rob2"] holds trials[].domains[] with both assessors inline.
                 canon["risk_of_bias"] holds by_outcome{}{} with assessor 1 inline and
                 assessor 2 as a flat SECOND_ASSESSOR_*.verbatim_reply to be parsed.

  3 IDENTITY     readers hardcoded `assessor_1_openai` / `assessor_2_google`. The curated
                 pairs are assessor 1 = Claude Opus 5 (anthropic), 2 = GPT-5 Codex
                 (openai). A reader that finds the container but not the assessors
                 renders a PARTIAL panel, which is harder to spot than a blank one.

Ruling (Mahmood, 2026-08-26): `risk_of_bias` is canonical. So this reads the canonical
store and returns one normalised shape, with assessors held in an ORDERED LIST rather
than under lab-named keys -- the identity bug cannot recur if no lab name is a key.

WHAT IT WILL NOT DO. If there is only one assessor, `judgements` has one entry. It never
pads the second column with the first assessor's values: a panel that shows one reader's
verdicts twice is a false claim of independent agreement, which is worse than a blank.
"""
import re

_SQ = re.compile(r'\b(D[1-5]|OVERALL)=([A-Z_]+)')


def _second_assessor(rb):
    for k, v in (rb or {}).items():
        if k.upper().startswith('SECOND_ASSESSOR') and isinstance(v, dict):
            return v
    return None


def _parse_reply(txt, sole_outcome=None):
    """Two recorded line shapes, both real:
         'NCT0331__hfcv_first D1=X ...'   identifier and outcome
         'NCT0331 D1=X ...'               identifier only, single-outcome topics
    """
    out = {}
    for line in str(txt or '').splitlines():
        line = line.strip()
        if not line or '=' not in line:
            continue
        head = line.split()[0]
        if '__' in head:
            ident, oc = head.split('__', 1)
        else:
            ident, oc = head, sole_outcome
            if oc is None:
                continue
        vals = dict(_SQ.findall(line))
        if vals:
            out[(ident, oc)] = vals
    return out


def rob_block(canon):
    """Normalised risk-of-bias block, or None when the object holds no assessment.

    {'assessors': [{'n':1,'name':...,'model_family':...}, ...],
     'trials': [{'trial','id','outcome',
                 'domains':[{'domain','domain_name','judgements':[j1,j2],'agreed'}],
                 'overall':[o1,o2], 'overall_agreed'}],
     'agreement': {...} | absent,
     'source_key': 'risk_of_bias' | 'rob2'}
    """
    native = canon.get('rob2')
    if isinstance(native, dict) and native.get('trials'):
        return _from_native(native)

    rb = canon.get('risk_of_bias')
    if not isinstance(rb, dict):
        return None
    by = rb.get('by_outcome') or {}
    if not by:
        return None                      # a block with no by_outcome is a shell, not an
                                         # assessment. Calling it one is the ['low']*5
                                         # error a level up.

    sa = _second_assessor(rb)
    sole = list(by.keys())[0] if len(by) == 1 else None
    reply = _parse_reply((sa or {}).get('verbatim_reply'), sole)

    alias = {}
    for t in ((canon.get('inputs') or {}).get('trials') or []):
        if t.get('nct') and t.get('id'):
            alias[t['nct']] = t['id']
            alias[t['id']] = t['nct']
    for (ident, oc), v in list(reply.items()):
        if alias.get(ident):
            reply.setdefault((alias[ident], oc), v)

    trials, pairs, agreed = [], 0, 0
    for oc, per in by.items():
        if not isinstance(per, dict):
            continue
        for rid, rec in per.items():
            if not isinstance(rec, dict):
                continue
            r2 = reply.get((rid, oc)) or {}
            doms = []
            for dk, dv in sorted((rec.get('domains') or {}).items()):
                if not isinstance(dv, dict):
                    continue
                j1 = dv.get('judgement')
                if isinstance(j1, dict):          # arni-hfref's inline-dual shape
                    j1 = j1.get('assessor_1_openai')
                j2 = r2.get(dk[:2])
                ag = None if j2 is None else (j1 == j2)
                if j2 is not None:
                    pairs += 1
                    agreed += 1 if ag else 0
                doms.append({'domain': dk[:2], 'domain_name': dk,
                             'judgements': [j1] + ([j2] if j2 is not None else []),
                             'reason': dv.get('reason'), 'agreed': ag})
            ov = rec.get('overall')
            if isinstance(ov, dict):
                ov = ov.get('assessor_1_openai')
            o2 = r2.get('OVERALL')
            trials.append({'trial': rec.get('trial') or rid, 'id': rid, 'outcome': oc,
                           'domains': doms,
                           'overall': [ov] + ([o2] if o2 is not None else []),
                           'overall_agreed': None if o2 is None else (ov == o2)})
    if not trials:
        return None
    assessors = [{'n': 1, 'name': (sa or {}).get('assessor_1') or 'assessor 1',
                  'model_family': _family((sa or {}).get('assessor_1'))}]
    a2 = (sa or {}).get('assessor_2')
    if a2:
        assessors.append({'n': 2, 'name': a2, 'model_family': _family(a2)})
    out = {'assessors': assessors, 'trials': trials, 'source_key': 'risk_of_bias',
           'tool': rb.get('tool'), 'version': rb.get('version'),
           'unit_of_assessment': rb.get('unit_of_assessment'),
           'default_rule': rb.get('default_rule'), 'ceiling': rb.get('ceiling')}
    if pairs:
        out['agreement'] = {'per_domain_agreed': agreed, 'per_domain_total': pairs,
                            'per_domain_rate_pct': round(100.0 * agreed / pairs, 1),
                            'recomputed_from_the_stored_judgements': True,
                            'why_recomputed': (
                                'The stored disagreement tallies were frozen as text and '
                                '12 of 22 no longer match the judgements in the object -- '
                                'a later guidance pass moved 51 D1 judgements and the '
                                'tallies were never recomputed. This is derived from what '
                                'the object holds now.')}
    return out


def _family(name):
    n = (name or '').lower()
    for fam in ('anthropic', 'openai', 'google'):
        if fam in n:
            return fam
    return None


def _from_native(native):
    """arni-hfref's shape. Left structurally alone -- it is the control that proved the
    drift, and it is the only object using this schema."""
    out = {'assessors': [], 'trials': [], 'source_key': 'rob2',
           'agreement': native.get('agreement')}
    for i, a in enumerate(native.get('assessors') or [], 1):
        out['assessors'].append({'n': i, 'name': a.get('model') or a.get('model_family'),
                                 'model_family': a.get('model_family')})
    keys = ('assessor_1_openai', 'assessor_2_google')
    for t in native.get('trials') or []:
        doms = []
        for d in t.get('domains') or []:
            js = [(d.get(k) or {}).get('judgement') for k in keys]
            doms.append({'domain': d.get('domain'),
                         'domain_name': d.get('domain_name') or d.get('domain'),
                         'judgements': [x for x in js if x is not None],
                         'reason': (d.get(keys[0]) or {}).get('rationale'),
                         'agreed': d.get('agreed')})
        ovs = [t.get('overall_assessor_1_openai'), t.get('overall_assessor_2_google')]
        out['trials'].append({'trial': t.get('trial'), 'id': t.get('trial'),
                              'outcome': None, 'domains': doms,
                              'overall': [x for x in ovs if x is not None],
                              'overall_agreed': t.get('overall_agreed')})
    return out
