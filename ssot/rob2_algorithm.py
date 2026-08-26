# -*- coding: utf-8 -*-
"""The published RoB 2 domain algorithms, transcribed from the tool and nothing else.

SOURCE, verified 2026-08-26 rather than recalled:
    Revised Cochrane risk-of-bias tool for randomized trials (RoB 2)
    Higgins, Savovic, Page, Sterne (eds), on behalf of the RoB2 Development Group
    **22 August 2019**, 72pp.
    Table 4  D1 randomization process
    Table 6  D2 deviations from intended interventions (EFFECT OF ASSIGNMENT)
    Table 10 D3 missing outcome data
    Table 12 D4 measurement of the outcome
    Table 14 D5 selection of the reported result
    Table 1  overall judgement for a result

A DIFFERENT DOCUMENT ALMOST GOT USED. The first copy retrieved was the 20 October 2016
"RoB 2.0" draft, whose tables differ (its D2 mapping has a different column set and its
D1 criteria are worded differently). It was discarded. Any future edit here must state
which version it is transcribing.

WHAT THIS MODULE WILL NOT DO. If the responses select no row, it returns UNDERIVABLE.
It never falls through to a default, and in particular never to LOW. A missing field
resolving to the flattering answer is the defect this project has spent its time chasing
(`rob: ['low'] * 5`); an algorithm that guesses when the table is silent is the same
mistake wearing better clothes.

D2 NOTE. Only the EFFECT OF ASSIGNMENT variant (Table 6) is implemented. The effect of
ADHERING variant (Table 8) asks a different question, and every assessment in this corpus
is an effect-of-assignment estimate. Passing adherence responses here would be a category
error, so the variant is named in the returned reasoning on every call.
"""

LOW, SOME, HIGH = 'LOW', 'SOME_CONCERNS', 'HIGH'
YPY, NPN, NI, NA = 'Y/PY', 'N/PN', 'NI', 'NA'

AUTHORITY = ('RoB 2, Revised Cochrane risk-of-bias tool for randomized trials, '
             'Higgins/Savovic/Page/Sterne (eds), RoB2 Development Group, '
             '22 August 2019')


def code(v):
    """Map a stored response onto the tool's coding. Returns None if unrecognised --
    an unrecognised response is refused, never coerced."""
    if v is None:
        return NI
    t = str(v).strip().upper().replace(' ', '_').replace('-', '_')
    if t in ('Y', 'YES', 'PY', 'PROBABLY_YES'):
        return YPY
    if t in ('N', 'NO', 'PN', 'PROBABLY_NO'):
        return NPN
    if t in ('NI', 'NO_INFORMATION', 'NOINFO', 'UNKNOWN', ''):
        return NI
    if t in ('NA', 'NOT_APPLICABLE'):
        return NA
    return None


def _i(v, *opts):
    return v in opts


def d1(q):
    """Table 4. 1.1 sequence random / 1.2 allocation concealed / 1.3 imbalance suggests problem."""
    a, b, c = q.get('1.1'), q.get('1.2'), q.get('1.3')
    if None in (a, b, c):
        return None, 'Table 4: an unrecognised response'
    if _i(b, NPN):
        return HIGH, 'Table 4 final row: 1.2 = N/PN -> High'
    if _i(b, NI) and _i(c, YPY):
        return HIGH, 'Table 4: 1.2 = NI AND 1.3 = Y/PY -> High'
    if _i(b, NI) and _i(c, NPN, NI):
        return SOME, ('Table 4: 1.2 = NI AND 1.3 = N/PN/NI -> Some concerns. '
                      'Table 3 states the same in words: "There is no information to '
                      'answer any of the signalling questions" -> Some concerns')
    if _i(a, YPY, NI) and _i(b, YPY) and _i(c, NI, NPN):
        return LOW, 'Table 4 row 1: 1.1 = Y/PY/NI, 1.2 = Y/PY, 1.3 = NI/N/PN -> Low'
    if _i(a, YPY) and _i(b, YPY) and _i(c, YPY):
        return SOME, 'Table 4 row 2: 1.1 = Y/PY, 1.2 = Y/PY, 1.3 = Y/PY -> Some concerns'
    if _i(a, NPN, NI) and _i(b, YPY) and _i(c, YPY):
        return SOME, 'Table 4 row 3: 1.1 = N/PN/NI, 1.2 = Y/PY, 1.3 = Y/PY -> Some concerns'
    return None, 'Table 4: responses select no row'


def d2(q):
    """Table 6, effect of ASSIGNMENT. Part 1 = 2.1-2.5, Part 2 = 2.6-2.7, domain = worse."""
    q1, q2, q3, q4, q5 = (q.get('2.%d' % i) for i in range(1, 6))
    q6, q7 = q.get('2.6'), q.get('2.7')
    if None in (q1, q2, q3, q6, q7):
        return None, 'Table 6: an unrecognised response'
    if _i(q1, NPN) and _i(q2, NPN):
        p1, r1 = LOW, 'Part 1 row 1: 2.1 & 2.2 = N/PN -> Low'
    elif _i(q3, NPN):
        p1, r1 = LOW, 'Part 1 row 2: 2.3 = N/PN -> Low'
    elif _i(q3, NI):
        p1, r1 = SOME, 'Part 1 row 3: 2.3 = NI -> Some concerns'
    elif _i(q3, YPY) and _i(q4, NPN):
        p1, r1 = SOME, 'Part 1 row 4: 2.3 = Y/PY, 2.4 = N/PN -> Some concerns'
    elif _i(q3, YPY) and _i(q5, YPY):
        p1, r1 = SOME, 'Part 1 row 5: 2.3 = Y/PY, 2.4 = Y/PY/NI, 2.5 = Y/PY -> Some concerns'
    elif _i(q3, YPY):
        p1, r1 = HIGH, 'Part 1 row 6: 2.3 = Y/PY, 2.5 = N/PN/NI -> High'
    else:
        return None, 'Table 6 Part 1: responses select no row'
    if _i(q6, YPY):
        p2, r2 = LOW, 'Part 2 row 1: 2.6 = Y/PY -> Low'
    elif _i(q7, NPN):
        p2, r2 = SOME, 'Part 2 row 2: 2.6 = N/PN/NI, 2.7 = N/PN -> Some concerns'
    elif _i(q7, YPY, NI):
        p2, r2 = HIGH, 'Part 2 row 3: 2.6 = N/PN/NI, 2.7 = Y/PY/NI -> High'
    else:
        return None, 'Table 6 Part 2: responses select no row'
    worst = HIGH if HIGH in (p1, p2) else (SOME if SOME in (p1, p2) else LOW)
    return worst, ('effect of ASSIGNMENT variant | %s | %s | domain criteria: the more '
                   'severe of the two parts -> %s' % (r1, r2, worst))


def d3(q):
    """Table 10. NOTE: every row requires 3.2 in {Y/PY, N/PN}. 3.2 = NI selects NO ROW,
    and Table 9's criteria cannot be met either, so an all-unknown D3 is UNDERIVABLE."""
    a, b, c, d = (q.get('3.%d' % i) for i in range(1, 5))
    if None in (a, b):
        return None, 'Table 10: an unrecognised response'
    if _i(a, YPY):
        return LOW, 'Table 10 row 1: 3.1 = Y/PY -> Low'
    if _i(a, NPN, NI) and _i(b, YPY):
        return LOW, 'Table 10 row 2: 3.1 = N/PN/NI, 3.2 = Y/PY -> Low'
    if _i(a, NPN, NI) and _i(b, NPN) and _i(c, NPN):
        return LOW, 'Table 10 row 3: 3.3 = N/PN -> Low'
    if _i(a, NPN, NI) and _i(b, NPN) and _i(c, YPY, NI) and _i(d, NPN):
        return SOME, 'Table 10 row 4: 3.4 = N/PN -> Some concerns'
    if _i(a, NPN, NI) and _i(b, NPN) and _i(c, YPY, NI) and _i(d, YPY, NI):
        return HIGH, 'Table 10 row 5: 3.4 = Y/PY/NI -> High'
    return None, ('Table 10 defines no row for 3.2 = NI: every row requires 3.2 in '
                  '{Y/PY, N/PN}. Table 9 cannot be met either. UNDERIVABLE.')


def d4(q):
    """Table 12."""
    a, b, c, d, e = (q.get('4.%d' % i) for i in range(1, 6))
    if None in (a, b, c):
        return None, 'Table 12: an unrecognised response'
    if _i(a, YPY):
        return HIGH, 'Table 12: 4.1 = Y/PY (method inappropriate) -> High'
    if _i(b, YPY):
        return HIGH, 'Table 12: 4.2 = Y/PY (differed between groups) -> High'
    if _i(b, NPN) and _i(c, NPN):
        return LOW, 'Table 12 row 1: 4.2 = N/PN, 4.3 = N/PN -> Low'
    if _i(b, NPN) and _i(c, YPY, NI) and _i(d, NPN):
        return LOW, 'Table 12 row 2: 4.4 = N/PN -> Low'
    if _i(b, NPN) and _i(c, YPY, NI) and _i(d, YPY, NI) and _i(e, NPN):
        return SOME, 'Table 12 row 3: 4.5 = N/PN -> Some concerns'
    if _i(b, NPN) and _i(c, YPY, NI) and _i(d, YPY, NI) and _i(e, YPY, NI):
        return HIGH, 'Table 12 row 4: 4.5 = Y/PY/NI -> High'
    if _i(b, NI) and _i(c, NPN):
        return SOME, 'Table 12 row 5: 4.2 = NI, 4.3 = N/PN -> Some concerns'
    if _i(b, NI) and _i(c, YPY, NI) and _i(d, NPN):
        return SOME, 'Table 12 row 6: 4.2 = NI, 4.4 = N/PN -> Some concerns'
    if _i(b, NI) and _i(c, YPY, NI) and _i(d, YPY, NI) and _i(e, NPN):
        return SOME, 'Table 12 row 7: 4.2 = NI, 4.5 = N/PN -> Some concerns'
    if _i(b, NI) and _i(c, YPY, NI) and _i(d, YPY, NI) and _i(e, YPY, NI):
        return HIGH, 'Table 12 row 8: 4.2 = NI, 4.5 = Y/PY/NI -> High'
    return None, 'Table 12: responses select no row'


def d5(q):
    """Table 14."""
    a, b, c = q.get('5.1'), q.get('5.2'), q.get('5.3')
    if None in (b, c):
        return None, 'Table 14: an unrecognised response'
    if _i(b, YPY) or _i(c, YPY):
        return HIGH, 'Table 14 final row: 5.2 or 5.3 = Y/PY -> High'
    if _i(a, YPY) and _i(b, NPN) and _i(c, NPN):
        return LOW, 'Table 14 row 1: 5.1 = Y/PY, 5.2 = N/PN, 5.3 = N/PN -> Low'
    if _i(a, NPN, NI) and _i(b, NPN) and _i(c, NPN):
        return SOME, 'Table 14 row 2: 5.1 = N/PN/NI, 5.2 & 5.3 = N/PN -> Some concerns'
    if _i(b, NPN) and _i(c, NI):
        return SOME, 'Table 14 row 3: 5.3 = NI -> Some concerns'
    if _i(b, NI) and _i(c, NPN):
        return SOME, 'Table 14 row 4: 5.2 = NI -> Some concerns'
    if _i(b, NI) and _i(c, NI):
        return SOME, 'Table 14 row 5: 5.2 = NI, 5.3 = NI -> Some concerns'
    return None, 'Table 14: responses select no row'


DOMAIN = {'D1': (d1, ('1.1', '1.2', '1.3')),
          'D2': (d2, ('2.1', '2.2', '2.3', '2.4', '2.5', '2.6', '2.7')),
          'D3': (d3, ('3.1', '3.2', '3.3', '3.4')),
          'D4': (d4, ('4.1', '4.2', '4.3', '4.4', '4.5')),
          'D5': (d5, ('5.1', '5.2', '5.3'))}


def overall(domains):
    """Table 1. `domains` maps D1..D5 -> judgement or None.

    Returns (None, reason) when ANY domain is underivable: an overall judgement is a
    statement about all five, and one cannot be reached over an incomplete set. The
    'some concerns in multiple domains' escalation in Table 1 is a REVIEW-AUTHOR
    decision, not an algorithm step, so it is never applied here -- it is surfaced for
    a person instead.
    """
    vals = list(domains.values())
    if not vals or any(v is None for v in vals):
        return None, ('Table 1: not reachable -- at least one domain is underivable, and '
                      'an overall judgement is a statement about all five')
    if any(v == HIGH for v in vals):
        return HIGH, 'Table 1: High risk of bias in at least one domain'
    if any(v == SOME for v in vals):
        n = sum(1 for v in vals if v == SOME)
        r = 'Table 1: Some concerns in %d domain(s), High in none' % n
        if n > 1:
            r += ('. Table 1 also permits a review author to escalate multiple '
                  '"some concerns" to High; that is a judgement, not an algorithm step, '
                  'and is left to a person')
        return SOME, r
    return LOW, 'Table 1: Low risk of bias in all five domains'
