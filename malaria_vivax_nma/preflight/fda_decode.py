"""Decode FDA multi-discipline-review PDFs whose embedded subset fonts carry a
broken ToUnicode CMap.  Three distinct corruptions occur, page by page:
  * clean  - ordinary ASCII, no transform needed
  * cmap   - lowercase mapped into Latin-Extended-A/B, uppercase into ASCII punct
  * shift  - every codepoint offset by a constant (glyph-index fallback)
Per page we try every candidate and keep whichever scores best against an
English word list, so the choice is evidence-driven rather than assumed.
"""
import sys, io, re, collections

LOWER = {0x102:'a',0x10F:'b',0x110:'c',0x11A:'d',0x11E:'e',0x128:'f',0x150:'g',0x15A:'h',
         0x15D:'i',0x169:'j',0x16C:'k',0x16F:'l',0x175:'m',0x176:'n',0x17D:'o',0x189:'p',
         0x18B:'q',0x18C:'r',0x190:'s',0x19A:'t',0x1B5:'u',0x1C0:'v',0x1C1:'w',0x1C6:'x',
         0x1C7:'y',0x1CC:'z'}
UPPER = {0x04:'A',0x11:'B',0x12:'C',0x18:'D',0x1C:'E',0x26:'F',0x27:'G',0x2C:'H',0x2F:'I',
         0x36:'J',0x3C:'K',0x3E:'L',0x44:'M',0x45:'N',0x4B:'O',0x57:'P',0x59:'Q',0x5A:'R',
         0x5E:'S',0x64:'T',0x68:'U',0x73:'V',0x74:'W',0x76:'X',0x7A:'Y',0x7C:'Z'}
PUNCT = {0x355:',',0x356:';',0x357:':',0x358:'.',0x372:'-',0x36C:'/',0x37E:'(',0x37F:')',
         0x374:'-',0x439:'%',0x43D:'+',0x441:'=',0x444:'<',0x445:'>',0x448:'>=',0x452:'<=',
         0x35B:"'",0x35A:'"',0x35E:'"',0x35F:'_',0x373:'*',0x37A:'_',0x34D:'?',0x37B:'[',
         0x37C:']',0x20B:'(',0x20C:')',0x2019:"'",0x2265:'>=',0x2264:'<=',0x2013:'-',
         0x201C:'"',0x201D:'"',0xB1:'+/-',0x296:'|',0x398:'&',0x33A:'.',0x34A:'?',0xF0B7:'*'}

CMAP = {}
for _k, _v in LOWER.items(): CMAP[chr(_k)] = _v
for _k, _v in UPPER.items(): CMAP[chr(_k)] = _v
for _k, _v in PUNCT.items(): CMAP[chr(_k)] = _v
for _d in range(10): CMAP[chr(0x3EC + _d)] = str(_d)

WORDS = set("""the and for with that this from were was are not but all any had has have been
subject subjects patient patients treatment treatments study studies trial trials arm arms
recurrence recurrent relapse malaria vivax plasmodium primaquine tafenoquine chloroquine
efficacy safety analysis analyses population dose doses day days month months table figure
review reviewer clinical statistical percent proportion difference confidence interval
odds ratio hazard risk placebo control group groups total number median range mean baseline
haemolysis hemolysis hemoglobin glucose dehydrogenase deficiency endpoint primary secondary
free rate time event events follow followed randomized randomised double blind""".split())

def _score(s):
    toks = re.findall(r'[a-z]{3,}', s.lower())
    if not toks: return 0.0
    return sum(1 for t in toks if t in WORDS) / len(toks) ** 0.5

def _shift(s, k):
    return ''.join(chr(ord(c) + k) if 0 < ord(c) + k < 0x2FFFF else c for c in s)

def _cmap(s):
    return ''.join(CMAP.get(c, c) for c in s)

def decode_page(p):
    cands = [('clean', p), ('cmap', _cmap(p))]
    for k in list(range(0x10, 0x40)) + [-0x1D, -0x22]:
        cands.append((f'shift{k:+d}', _shift(p, k)))
    best = max(cands, key=lambda kv: _score(kv[1]))
    return best[0], best[1]

def decode_doc(path):
    pages = open(path, encoding='utf-8', errors='replace').read().split('\x0c')
    out, modes = [], collections.Counter()
    for p in pages:
        m, t = decode_page(p)
        modes[m] += 1
        out.append(t)
    return out, modes

if __name__ == '__main__':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    pages, modes = decode_doc(sys.argv[1])
    print('MODES:', modes.most_common(), file=sys.stderr)
    open(sys.argv[2], 'w', encoding='utf-8').write('\n\x0c'.join(pages))
    print('wrote', sys.argv[2], sum(len(p) for p in pages), 'chars', file=sys.stderr)
