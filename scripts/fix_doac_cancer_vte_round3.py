"""Round 3: make the headline verdict follow the interval the protocol says to quote.

Section 8 now pins the HKSJ interval as the one to quote at small k. The visual-abstract
verdict and the waiting-room significance flag were still reading the DerSimonian-Laird
interval alone. On the corrected data those disagree - DL 0.39-0.86 excludes 1, HKSJ
0.29-1.18 does not - so the page called a "robust 42% reduction" a result its own
recommended interval does not support.

Run after rounds 1 and 2:  python scripts/fix_doac_cancer_vte_round3.py
"""
import io
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HERE = os.path.dirname(os.path.abspath(__file__))
TARGET = os.path.normpath(os.path.join(HERE, '..', 'DOAC_CANCER_VTE_REVIEW.html'))

EDITS = []


def edit(tag, old, new, count=1):
    EDITS.append((tag, old, new, count))


def build_edits():
    # interpretRelativeEffect decides benefit / harm / neutral from a single interval.
    # Give it the HKSJ bounds as an optional second interval and require BOTH to
    # exclude the null before the page is allowed to call a result significant.
    edit('significance: require the HKSJ interval to agree before claiming an effect',
         'interpretRelativeEffect=(orVal,lciVal,uciVal)=>{const or=parseFloat(orVal),'
         'lci=parseFloat(lciVal),uci=parseFloat(uciVal);return[or,lci,uci].every(Number.isFinite)?'
         'uci<1?{direction:"benefit",significant:!0,pct:Math.abs(100*(1-or)).toFixed(0)}:'
         'lci>1?{direction:"harm",significant:!0,pct:Math.abs(100*(or-1)).toFixed(0)}:'
         '{direction:"neutral",significant:!1,pct:Math.abs(100*(or<=1?1-or:or-1)).toFixed(0)}:'
         '{direction:"neutral",significant:!1,pct:"--"}}',

         'interpretRelativeEffect=(orVal,lciVal,uciVal,hkLo,hkHi)=>{const or=parseFloat(orVal),'
         'lci=parseFloat(lciVal),uci=parseFloat(uciVal),hl=parseFloat(hkLo),hh=parseFloat(hkHi),'
         # At small k the protocol pins HKSJ as the interval to quote. When it is present
         # and straddles 1, the result is not significant however narrow the DL interval is.
         'hkOK=!(Number.isFinite(hl)&&Number.isFinite(hh))||(hh<1||hl>1);'
         'return[or,lci,uci].every(Number.isFinite)?'
         'uci<1&&hkOK?{direction:"benefit",significant:!0,pct:Math.abs(100*(1-or)).toFixed(0)}:'
         'lci>1&&hkOK?{direction:"harm",significant:!0,pct:Math.abs(100*(or-1)).toFixed(0)}:'
         '{direction:uci<1?"benefit":lci>1?"harm":"neutral",significant:!1,'
         'hksjDisagrees:!hkOK&&(uci<1||lci>1),pct:Math.abs(100*(or<=1?1-or:or-1)).toFixed(0)}:'
         '{direction:"neutral",significant:!1,pct:"--"}}')

    edit('verdict banner: pass the HKSJ bounds in and stop calling a straddling result robust',
         'effect=interpretRelativeEffect(r.or,r.lci,r.uci),neutralDirection=parseFloat(r.or)<=1?'
         '"reduction":"increase",verdictText="benefit"===effect.direction?`Evidence base '
         'consisting of ${phaseText} trials shows a robust ${effect.pct}% reduction in '
         '${verdictOutcome[outcomeKey]??"the selected endpoint"}.`:"harm"===effect.direction?'
         '`Evidence base consisting of ${phaseText} trials shows a clear ${effect.pct}% increase '
         'in ${verdictOutcome[outcomeKey]??"the selected endpoint"}.`:`Evidence base consisting '
         'of ${phaseText} trials suggests an estimated ${effect.pct}% ${neutralDirection} in '
         '${verdictOutcome[outcomeKey]??"the selected endpoint"}, but the confidence interval '
         'includes no effect.`',

         'effect=interpretRelativeEffect(r.or,r.lci,r.uci,r.hksjLCI,r.hksjUCI),'
         'neutralDirection=parseFloat(r.or)<=1?"reduction":"increase",'
         'verdictText=effect.hksjDisagrees?`Evidence base consisting of ${phaseText} trials '
         'estimates a ${effect.pct}% ${neutralDirection} in '
         '${verdictOutcome[outcomeKey]??"the selected endpoint"}, but this is NOT a significant '
         'finding: with only ${r.k} trials the HKSJ interval (${r.hksjLCI}-${r.hksjUCI}) is the '
         'one to quote and it includes no effect. The narrower DerSimonian-Laird interval '
         '(${r.lci}-${r.uci}) understates the uncertainty in between-study variance at this '
         'k.`:"benefit"===effect.direction&&effect.significant?`Evidence base consisting of '
         '${phaseText} trials shows a ${effect.pct}% reduction in '
         '${verdictOutcome[outcomeKey]??"the selected endpoint"}, with both the '
         'DerSimonian-Laird and HKSJ intervals excluding no effect.`:'
         '"harm"===effect.direction&&effect.significant?`Evidence base consisting of '
         '${phaseText} trials shows a ${effect.pct}% increase in '
         '${verdictOutcome[outcomeKey]??"the selected endpoint"}, with both the '
         'DerSimonian-Laird and HKSJ intervals excluding no effect.`:`Evidence base consisting '
         'of ${phaseText} trials suggests an estimated ${effect.pct}% ${neutralDirection} in '
         '${verdictOutcome[outcomeKey]??"the selected endpoint"}, but the confidence interval '
         'includes no effect.`')

    edit('narrative + waiting-room: same HKSJ gate on the prose and the pictogram',
         'interpretRelativeEffect(r.or,r.lci,r.uci),totalN=parseInt(r.n.replace(',
         'interpretRelativeEffect(r.or,r.lci,r.uci,r.hksjLCI,r.hksjUCI),totalN=parseInt(r.n.replace(')


def main():
    raw = open(TARGET, 'rb').read()
    had_bom = raw.startswith(b'\xef\xbb\xbf')
    src = raw.decode('utf-8-sig')
    build_edits()
    for tag, old, new, count in EDITS:
        found = src.count(old)
        if found != count:
            sys.exit('ANCHOR MISMATCH [%s]: expected %d, found %d\n  anchor: %.200s'
                     % (tag, count, found, old))
        src = src.replace(old, new)
    out = src.encode('utf-8')
    if had_bom:
        out = b'\xef\xbb\xbf' + out
    with open(TARGET, 'wb') as fh:
        fh.write(out)
    print('applied %d anchored edits (round 3)' % len(EDITS))
    for tag, _, _, _ in EDITS:
        print('  -', tag)


if __name__ == '__main__':
    main()
