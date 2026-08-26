#!/usr/bin/env python3
"""Re-derive every NO_INFORMATION *domain judgement* using the published RoB 2 algorithm.

WHY. Handbook v6.5 section 8.2.3 and the tool itself list three domain-level judgements --
Low, Some concerns, High -- and five SIGNALLING-QUESTION responses, of which "No
information" is one. This corpus uses NO_INFORMATION as a domain judgement 191 times,
more often than any valid one. That was a considered house convention, recorded in
`risk_of_bias.default_rule`, and Mahmood has ruled it be re-derived to the tool's values.

HOW, AND THE THREE THINGS THIS WILL NOT DO.

  NEVER IN PLACE. The stored `judgement` is not touched. The re-derivation is written to
  a sibling key, `rob2_algorithm_2026_08_26`, so if this is wrong the original is still
  on disk rather than in a history someone has to excavate.

  NEVER A DEFAULT. If the responses select no row of the published table, the state is
  UNDERIVABLE and no value is proposed. Reported as a data gap. An algorithm that answers
  when the table is silent is `rob: ['low'] * 5` with a citation attached.

  NEVER AN INVENTED RESPONSE. Two bases are accepted and both are recorded per domain:
    A  stored signalling answers on the domain
    B  the object's own declared ceiling -- `default_rule` / `ceiling` state that a domain
       unjudgeable from the sources read is NO_INFORMATION, so for such a domain every
       signalling response IS "No information" by the object's own declaration.
  A domain with neither is left alone entirely.

Default is a dry run. `--apply` writes. `--topic X` limits scope.
"""
import argparse
import io
import json
import os
import sys
import collections

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, 'ssot'))
from rob2_algorithm import DOMAIN, overall, code, AUTHORITY, NI, LOW, SOME, HIGH  # noqa: E402
import atomic_write  # noqa: E402
sys.path.insert(0, os.path.join(REPO, 'scripts'))
import instrument_controls  # noqa: E402

FIELD = 'rob2_algorithm_2026_08_26'

# stored signalling-question key names -> the tool's numbering. Derived from a census of
# every `signalling_questions` block in the corpus; an unmapped key is REPORTED, never
# silently dropped, because a dropped answer becomes an NI and NI changes the row.
KEYMAP = {
    'allocation_sequence_random': '1.1',
    'allocation_concealed': '1.2',
    'baseline_imbalance_suggesting_a_problem': '1.3',
    'participants_aware': '2.1',
    'carers_aware': '2.2',
    'appropriate_analysis_used': '2.6',
    'data_available_for_all_randomised': '3.1',
    'analysed_per_prespecified_plan': '5.1',
    'trial_selected_from_multiple_eligible_measurements': '5.2',
    'trial_selected_from_multiple_eligible_analyses': '5.3',
}

NOT_A_REPLACEMENT = (
    'This is the judgement the published algorithm proposes from the signalling '
    'responses named here. It does NOT replace the stored `judgement` beside it, and '
    'nothing reads it yet. The tool itself says its algorithms "provide proposed '
    'judgements, but users should verify these and change them if they feel this is '
    'appropriate" -- so this is an input to a person, not an output to a reader.')


def collect(dv, dn, declared_ceiling):
    """Return (responses, basis, unmapped_keys) or (None, None, ...) if no basis."""
    _, qs = DOMAIN[dn]
    stored = dv.get('signalling_questions')
    unmapped = []
    if isinstance(stored, dict) and stored:
        q = {}
        for k, v in stored.items():
            num = KEYMAP.get(k)
            if num is None:
                unmapped.append(k)
                continue
            q[num] = code(v)
        for n in qs:
            q.setdefault(n, NI)
        return q, 'A: stored signalling answers on this domain', unmapped
    if declared_ceiling:
        return ({n: NI for n in qs},
                'B: the object declares a domain unjudgeable from the sources read to be '
                'NO_INFORMATION, so every signalling response is "No information" by its '
                'own declaration', unmapped)
    return None, None, unmapped


def _controls():
    """Two known answers, established OUTSIDE this instrument, checked before any count.

    POSITIVE. D1 on a result where every signalling response is "No information". The
    answer is established by this repo's own reading of the tool, written into
    ssot/apply_d1_resolved_by_guidance.py on 2026-08-21 and quoting the guidance: "The
    tool maps 'No information' on 1.1 and 1.2 with no baseline concern to a DOMAIN
    judgement of SOME CONCERNS." That reading was made before this file existed, so
    reproducing it is not the code agreeing with itself.

    NEGATIVE. The over-flagging direction here is PROPOSING A JUDGEMENT WHERE THE TABLE
    DEFINES NONE -- the flattering-default failure this whole exercise is about. D3 with
    all responses "No information" selects no row of Table 10, so its state must NOT be
    DERIVED. Note the contract's polarity: require_controls raises when actual ==
    must_not_be, so the negative names the forbidden answer, not the wanted one.
    """
    qs = {n: NI for n in DOMAIN['D1'][1]}
    pos_val, _ = DOMAIN['D1'][0](qs)
    qs3 = {n: NI for n in DOMAIN['D3'][1]}
    neg_val, _ = DOMAIN['D3'][0](qs3)
    instrument_controls.require_controls(
        'rederive_no_information_domains',
        positive=('D1 with every signalling response NI (RoB 2 Table 4 / Table 3 clause '
                  'iii, as read in apply_d1_resolved_by_guidance.py)', pos_val, SOME),
        negative=('D3 with every signalling response NI -- Table 10 defines no row',
                  'DERIVED' if neg_val is not None else 'UNDERIVABLE', 'DERIVED'))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--topic', action='append', default=None)
    a = ap.parse_args()
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    _controls()

    root = os.path.join(REPO, 'ssot')
    topics = a.topic or sorted(d for d in os.listdir(root)
                               if os.path.isfile(os.path.join(root, d, d + '.json')))
    tier = collections.Counter()
    moves = collections.Counter()
    per_dom = collections.Counter()
    gaps = collections.Counter()
    unmapped_all = collections.Counter()
    ov_now = collections.Counter()
    ov_new = collections.Counter()
    touched = 0

    for t in topics:
        p = os.path.join(root, t, t + '.json')
        if not os.path.isfile(p):
            continue
        obj = json.load(io.open(p, encoding='utf-8'))
        if obj.get('state') == 'RETIRED':
            continue
        rb = obj.get('risk_of_bias')
        if not isinstance(rb, dict):
            continue
        declared_ceiling = bool(rb.get('default_rule') or rb.get('ceiling'))
        changed = False
        n_der = n_gap = 0
        for oc, per in (rb.get('by_outcome') or {}).items():
            if not isinstance(per, dict):
                continue
            for rid, rec in per.items():
                if not isinstance(rec, dict):
                    continue
                derived = {}
                for dk, dv in (rec.get('domains') or {}).items():
                    if not isinstance(dv, dict):
                        continue
                    dn = dk[:2]
                    if dn not in DOMAIN:
                        continue
                    stored_j = dv.get('judgement')
                    if not isinstance(stored_j, str):
                        derived[dn] = None
                        continue
                    if stored_j.strip().upper() != 'NO_INFORMATION':
                        derived[dn] = (stored_j.strip().upper()
                                       if stored_j.strip().upper() in (LOW, SOME, HIGH)
                                       else None)
                        continue
                    q, basis, unmapped = collect(dv, dn, declared_ceiling)
                    for u in unmapped:
                        unmapped_all[u] += 1
                    if q is None:
                        tier['no basis -- left untouched'] += 1
                        gaps['%s (no stored answers, no declared ceiling)' % dn] += 1
                        derived[dn] = None
                        continue
                    val, why = DOMAIN[dn][0](q)
                    block = {
                        'authority': AUTHORITY,
                        'basis': basis,
                        'signalling_responses_used': q,
                        'stored_judgement_at_derivation': stored_j,
                        'this_does_not_replace_the_stored_judgement': NOT_A_REPLACEMENT,
                    }
                    if val is None:
                        block['state'] = 'UNDERIVABLE'
                        block['reason'] = why
                        tier['UNDERIVABLE -- responses select no row'] += 1
                        gaps['%s (%s)' % (dn, why.split('.')[0][:60])] += 1
                        n_gap += 1
                    else:
                        block['state'] = 'DERIVED'
                        block['derived_judgement'] = val
                        block['algorithm'] = why
                        tier[basis[:1] + ' derived'] += 1
                        per_dom[(dn, val)] += 1
                        moves['%s -> %s' % (stored_j.strip().upper(), val)] += 1
                        n_der += 1
                    derived[dn] = val
                    if dv.get(FIELD) != block:
                        dv[FIELD] = block
                        changed = True
                ov = rec.get('overall')
                if isinstance(ov, str):
                    ov_now[ov.strip().upper()] += 1
                    no, owhy = overall(derived) if derived else (None, 'no domains')
                    ov_new['UNDERIVABLE' if no is None else no] += 1
                    blk = {'authority': AUTHORITY,
                           'stored_overall_at_derivation': ov.strip().upper(),
                           'this_does_not_replace_the_stored_judgement': NOT_A_REPLACEMENT}
                    if no is None:
                        blk['state'] = 'UNDERIVABLE'
                        blk['reason'] = owhy
                    else:
                        blk['state'] = 'DERIVED'
                        blk['derived_overall'] = no
                        blk['algorithm'] = owhy
                    if rec.get(FIELD) != blk:
                        rec[FIELD] = blk
                        changed = True
        if changed:
            touched += 1
            rb.setdefault('rob2_rederivation_2026_08_26', {}).update({
                'what': 'Domain judgements recorded as NO_INFORMATION re-derived with the '
                        'published algorithm and written alongside, never in place.',
                'authority': AUTHORITY,
                'handbook': 'Cochrane Handbook v6.5 section 8.2.3: the domain-level '
                            'judgements are Low / Some concerns / High; "No information" '
                            'is one of the five signalling-question responses.',
                'field': FIELD,
                'derived': n_der,
                'underivable_reported_as_a_data_gap': n_gap,
                'the_stored_judgements_are_unchanged': True,
                'control': 'scripts/plant_rob2_algorithm_tables.py -- one case per '
                           'published table row, plus four negative controls.',
            })
            if a.apply:
                atomic_write.write_text(p, json.dumps(obj, indent=1))

    print('=' * 84)
    print('RE-DERIVATION OF NO_INFORMATION DOMAIN JUDGEMENTS  (%s)'
          % ('APPLIED' if a.apply else 'DRY RUN -- nothing written'))
    print('=' * 84)
    print('  objects that would change : %d' % touched)
    for k, v in sorted(tier.items()):
        print('    %-58s %4d' % (k, v))
    print()
    print('  DATA GAPS -- nothing proposed, by reason:')
    for k, v in sorted(gaps.items()):
        print('    %-58s %4d' % (k, v))
    if unmapped_all:
        print()
        print('  UNMAPPED signalling-question key names (reported, never dropped):')
        for k, v in unmapped_all.most_common():
            print('    %-58s %4d' % (k, v))
    print()
    print('  DIRECTION -- every re-derivation:')
    for k, v in sorted(moves.items(), key=lambda x: -x[1]):
        print('    %-58s %4d' % (k, v))
    up = sum(v for k, v in moves.items() if k.endswith('-> ' + LOW))
    print('    %-58s %4d' % ('...of which move TOWARD Low (the flattering direction)', up))
    print()
    print('  BY DOMAIN:')
    for (dn, val), v in sorted(per_dom.items()):
        print('    %-6s -> %-16s %4d' % (dn, val, v))
    print()
    print('  OVERALL RATINGS (Table 1), stored vs re-derived:')
    for k in (LOW, SOME, HIGH, 'NO_INFORMATION', 'UNDERIVABLE'):
        print('    %-18s stored %4d   re-derived %4d' % (k, ov_now.get(k, 0),
                                                         ov_new.get(k, 0)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
