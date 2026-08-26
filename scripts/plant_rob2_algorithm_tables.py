#!/usr/bin/env python3
"""KNOWN-ANSWER control for ssot/rob2_algorithm.py -- one case per published table row.

WHY THIS IS THE CONTROL THAT MATTERS. The re-derivation of 191 stored judgements rests
entirely on five tables transcribed by hand out of a PDF. Nothing downstream can catch a
mis-transcribed row: a wrong row yields a plausible judgement with a plausible citation,
and it would be published. So every row of Tables 4, 6, 10, 12 and 14 is exercised here
against the answer the tool itself prints, plus Table 1.

THE VERSION IS PART OF THE CONTROL. The first guidance PDF retrieved on 2026-08-26 was
the 20 October 2016 "RoB 2.0" draft, whose tables differ. These expectations are the
22 August 2019 tool. If someone re-transcribes from a different version, these fail --
which is the point.

FOUR NEGATIVE CONTROLS, because a table-reader that always answers is worse than useless:
  * D3 with 3.2 = NI must be UNDERIVABLE (no row requires it; Table 9 cannot be met)
  * an unrecognised response must be UNDERIVABLE, never coerced to NI
  * overall over an incomplete domain set must be UNDERIVABLE
  * no all-unknown domain may return LOW -- the flattering-default direction
"""
import io
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), 'ssot'))
from rob2_algorithm import (DOMAIN, overall, code, LOW, SOME, HIGH,
                            YPY, NPN, NI, NA)

Y, N, U = YPY, NPN, NI

# (domain, {responses}, expected, note naming the published row)
CASES = [
    # ---- Table 4, D1 -- all six rows
    ('D1', {'1.1': Y, '1.2': Y, '1.3': N}, LOW,  'T4 r1 Y/PY,Y/PY,N/PN'),
    ('D1', {'1.1': U, '1.2': Y, '1.3': U}, LOW,  'T4 r1 NI,Y/PY,NI'),
    ('D1', {'1.1': Y, '1.2': Y, '1.3': Y}, SOME, 'T4 r2 all Y/PY'),
    ('D1', {'1.1': N, '1.2': Y, '1.3': Y}, SOME, 'T4 r3 N/PN,Y/PY,Y/PY'),
    ('D1', {'1.1': Y, '1.2': U, '1.3': N}, SOME, 'T4 r4 any,NI,N/PN'),
    ('D1', {'1.1': U, '1.2': U, '1.3': U}, SOME, 'T4 r4 ALL UNKNOWN -> Some concerns'),
    ('D1', {'1.1': Y, '1.2': U, '1.3': Y}, HIGH, 'T4 r5 any,NI,Y/PY'),
    ('D1', {'1.1': Y, '1.2': N, '1.3': N}, HIGH, 'T4 r6 any,N/PN,any'),

    # ---- Table 6, D2 (effect of assignment)
    ('D2', {'2.1': N, '2.2': N, '2.3': N, '2.4': NA, '2.5': NA,
            '2.6': Y, '2.7': NA}, LOW, 'T6 P1r1 unaware + P2r1 appropriate'),
    ('D2', {'2.1': Y, '2.2': U, '2.3': N, '2.4': NA, '2.5': NA,
            '2.6': Y, '2.7': NA}, LOW, 'T6 P1r2 2.3 = N/PN'),
    ('D2', {'2.1': Y, '2.2': U, '2.3': U, '2.4': NA, '2.5': NA,
            '2.6': Y, '2.7': NA}, SOME, 'T6 P1r3 2.3 = NI'),
    ('D2', {'2.1': Y, '2.2': U, '2.3': Y, '2.4': N, '2.5': NA,
            '2.6': Y, '2.7': NA}, SOME, 'T6 P1r4 2.4 = N/PN'),
    ('D2', {'2.1': Y, '2.2': U, '2.3': Y, '2.4': Y, '2.5': Y,
            '2.6': Y, '2.7': NA}, SOME, 'T6 P1r5 2.5 balanced'),
    ('D2', {'2.1': Y, '2.2': U, '2.3': Y, '2.4': Y, '2.5': N,
            '2.6': Y, '2.7': NA}, HIGH, 'T6 P1r6 2.5 = N/PN -> High'),
    ('D2', {'2.1': N, '2.2': N, '2.3': N, '2.4': NA, '2.5': NA,
            '2.6': N, '2.7': N}, SOME, 'T6 P2r2 2.6 = N/PN, 2.7 = N/PN'),
    ('D2', {'2.1': N, '2.2': N, '2.3': N, '2.4': NA, '2.5': NA,
            '2.6': N, '2.7': Y}, HIGH, 'T6 P2r3 2.7 = Y/PY -> High'),
    ('D2', {'2.1': U, '2.2': U, '2.3': U, '2.4': U, '2.5': U,
            '2.6': U, '2.7': U}, HIGH,
     'T6 ALL UNKNOWN: P1 Some concerns, P2 High (2.6 NI -> 2.7 NI) -> High'),

    # ---- Table 10, D3 -- all five rows
    ('D3', {'3.1': Y, '3.2': NA, '3.3': NA, '3.4': NA}, LOW,  'T10 r1 3.1 = Y/PY'),
    ('D3', {'3.1': N, '3.2': Y, '3.3': NA, '3.4': NA}, LOW,  'T10 r2 3.2 = Y/PY'),
    ('D3', {'3.1': N, '3.2': N, '3.3': N, '3.4': NA}, LOW,  'T10 r3 3.3 = N/PN'),
    ('D3', {'3.1': N, '3.2': N, '3.3': Y, '3.4': N}, SOME, 'T10 r4 3.4 = N/PN'),
    ('D3', {'3.1': N, '3.2': N, '3.3': Y, '3.4': Y}, HIGH, 'T10 r5 3.4 = Y/PY'),
    ('D3', {'3.1': U, '3.2': U, '3.3': U, '3.4': U}, None,
     'T10 NEGATIVE CONTROL: 3.2 = NI selects no row -> UNDERIVABLE'),

    # ---- Table 12, D4
    ('D4', {'4.1': N, '4.2': N, '4.3': N, '4.4': NA, '4.5': NA}, LOW,  'T12 r1'),
    ('D4', {'4.1': N, '4.2': N, '4.3': Y, '4.4': N, '4.5': NA},  LOW,  'T12 r2'),
    ('D4', {'4.1': N, '4.2': N, '4.3': Y, '4.4': Y, '4.5': N},   SOME, 'T12 r3'),
    ('D4', {'4.1': N, '4.2': N, '4.3': Y, '4.4': Y, '4.5': Y},   HIGH, 'T12 r4'),
    ('D4', {'4.1': N, '4.2': U, '4.3': N, '4.4': NA, '4.5': NA}, SOME, 'T12 r5'),
    ('D4', {'4.1': N, '4.2': U, '4.3': Y, '4.4': N, '4.5': NA},  SOME, 'T12 r6'),
    ('D4', {'4.1': N, '4.2': U, '4.3': Y, '4.4': Y, '4.5': N},   SOME, 'T12 r7'),
    ('D4', {'4.1': N, '4.2': U, '4.3': Y, '4.4': Y, '4.5': Y},   HIGH, 'T12 r8'),
    ('D4', {'4.1': Y, '4.2': N, '4.3': N, '4.4': NA, '4.5': NA}, HIGH, 'T12 r9 4.1 = Y/PY'),
    ('D4', {'4.1': N, '4.2': Y, '4.3': N, '4.4': NA, '4.5': NA}, HIGH, 'T12 r10 4.2 = Y/PY'),
    ('D4', {'4.1': U, '4.2': U, '4.3': U, '4.4': U, '4.5': U},   HIGH,
     'T12 r8 ALL UNKNOWN -> High'),

    # ---- Table 14, D5
    ('D5', {'5.1': Y, '5.2': N, '5.3': N}, LOW,  'T14 r1'),
    ('D5', {'5.1': N, '5.2': N, '5.3': N}, SOME, 'T14 r2 5.1 = N/PN'),
    ('D5', {'5.1': U, '5.2': N, '5.3': N}, SOME, 'T14 r2 5.1 = NI'),
    ('D5', {'5.1': Y, '5.2': N, '5.3': U}, SOME, 'T14 r3 5.3 = NI'),
    ('D5', {'5.1': Y, '5.2': U, '5.3': N}, SOME, 'T14 r4 5.2 = NI'),
    ('D5', {'5.1': U, '5.2': U, '5.3': U}, SOME, 'T14 r5 ALL UNKNOWN -> Some concerns'),
    ('D5', {'5.1': Y, '5.2': N, '5.3': Y}, HIGH, 'T14 r6 5.3 = Y/PY'),
    ('D5', {'5.1': Y, '5.2': Y, '5.3': N}, HIGH, 'T14 r6 5.2 = Y/PY'),
]

OVERALL_CASES = [
    ({'D1': LOW, 'D2': LOW, 'D3': LOW, 'D4': LOW, 'D5': LOW}, LOW,  'T1 all Low'),
    ({'D1': SOME, 'D2': LOW, 'D3': LOW, 'D4': LOW, 'D5': LOW}, SOME, 'T1 one Some'),
    ({'D1': SOME, 'D2': SOME, 'D3': LOW, 'D4': LOW, 'D5': LOW}, SOME,
     'T1 multiple Some -> Some (escalation is an author decision, not an algorithm step)'),
    ({'D1': LOW, 'D2': HIGH, 'D3': LOW, 'D4': LOW, 'D5': LOW}, HIGH, 'T1 one High'),
    ({'D1': LOW, 'D2': LOW, 'D3': None, 'D4': LOW, 'D5': LOW}, None,
     'T1 NEGATIVE CONTROL: an underivable domain blocks the overall'),
]


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    fails = []
    print('KNOWN-ANSWER CONTROL -- RoB 2, 22 August 2019, Tables 1/4/6/10/12/14')
    print('=' * 78)
    for dn, q, want, note in CASES:
        fn, _ = DOMAIN[dn]
        got, why = fn(q)
        ok = (got == want)
        if not ok:
            fails.append((dn, note, want, got, why))
        print('  %-4s %-58s %s' % (dn, note, 'ok' if ok else
                                   'FAIL want=%s got=%s' % (want, got)))
    print()
    for doms, want, note in OVERALL_CASES:
        got, why = overall(doms)
        ok = (got == want)
        if not ok:
            fails.append(('T1', note, want, got, why))
        print('  %-4s %-58s %s' % ('T1', note, 'ok' if ok else
                                   'FAIL want=%s got=%s' % (want, got)))
    print()

    # NEGATIVE CONTROL: an unrecognised response must not be coerced.
    print('  NEGATIVE CONTROLS')
    bad = code('probably-ish')
    ok_bad = bad is None
    print('    unrecognised response is refused, not coerced to NI : %s (%r)'
          % ('ok' if ok_bad else 'FAIL', bad))
    if not ok_bad:
        fails.append(('code', 'unrecognised coerced', None, bad, ''))
    got, _ = DOMAIN['D1'][0]({'1.1': None, '1.2': YPY, '1.3': NPN})
    ok_none = got is None
    print('    a None response yields UNDERIVABLE, not a judgement    : %s (%r)'
          % ('ok' if ok_none else 'FAIL', got))
    if not ok_none:
        fails.append(('D1', 'None response judged', None, got, ''))

    # NEGATIVE CONTROL: no all-unknown domain may land on LOW.
    flattered = []
    for dn, (fn, qs) in sorted(DOMAIN.items()):
        got, _ = fn({k: NI for k in qs})
        if got == LOW:
            flattered.append(dn)
    print('    no all-unknown domain returns LOW                     : %s %s'
          % ('ok' if not flattered else 'FAIL', flattered or ''))
    if flattered:
        fails.append(('all-NI', 'flattering default', 'not LOW', flattered, ''))

    print()
    print('=' * 78)
    total = len(CASES) + len(OVERALL_CASES) + 3
    print('  %d of %d' % (total - len(fails), total))
    if fails:
        for f in fails:
            print('  FAILED %s %s want=%s got=%s :: %s' % f)
        sys.exit('TABLE TRANSCRIPTION IS WRONG -- do not re-derive anything')
    return 0


if __name__ == '__main__':
    sys.exit(main())
