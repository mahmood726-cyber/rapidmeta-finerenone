import sys, io, re
if __name__ == '__main__':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

LOWER = {0x102:'a',0x10F:'b',0x110:'c',0x11A:'d',0x11E:'e',0x128:'f',0x150:'g',0x15A:'h',
         0x15D:'i',0x169:'j',0x16C:'k',0x16F:'l',0x175:'m',0x176:'n',0x17D:'o',0x189:'p',
         0x18B:'q',0x18C:'r',0x190:'s',0x19A:'t',0x1B5:'u',0x1C0:'v',0x1C1:'w',0x1C6:'x',
         0x1C7:'y',0x1CC:'z'}
PUNCT = {0x355:',',0x356:';',0x357:':',0x358:'.',0x372:'-',0x36C:'/',0x37E:'(',0x37F:')',
         0x374:'-',0x439:'%',0x43D:'+',0x441:'=',0x444:'<',0x445:'>',0x448:'>=',0x452:'<=',
         0x35B:"'",0x35A:'"',0x35E:'"',0x35F:'_',0x373:'*',0x37A:'_',0x370:'!',0x34D:'?',
         0x37B:'[',0x37C:']',0x20B:'(',0x20C:')',0x2019:"'",0x2265:'>=',0x2264:'<=',
         0x33A:'.',0x34A:'?',0xF0B7:'*',0x296:'|',0x285:'u',0x1E4:'G',0x1E6:'G',0x1EB:'q',
         0x15F:'s',0x12E:'i',0x12B:'i',0x120:'g',0x179:'o',0x2013:'-',0x201C:'"',0x201D:'"',
         0xB1:'+/-',0xF1:'n'}
# Greek block = uppercase-ish glyphs seen in formulas; leave visible
def build():
    m = {}
    for k,v in LOWER.items(): m[chr(k)] = v
    for d in range(10): m[chr(0x3EC+d)] = str(d)
    for k,v in PUNCT.items(): m[chr(k)] = v
    return m
MAP = build()

def decode(s, upper=None):
    up = upper or {}
    out=[]
    for ch in s:
        if ch in MAP: out.append(MAP[ch])
        elif ch in up: out.append(up[ch])
        else: out.append(ch)
    return ''.join(out)

if __name__ == '__main__':
    raw = open(sys.argv[1], encoding='utf-8', errors='replace').read()
    pages = raw.split('\x0c')
    idx = int(sys.argv[2]) if len(sys.argv)>2 else 100
    print(decode(pages[idx]))
