import re, html as H
TAB, NL = chr(9), chr(10)
def prose(path, limit=None):
    h = open(path, encoding='utf-8', errors='replace').read()
    i = h.find('id=' + chr(34) + 'pn-paper' + chr(34))
    if i < 0:
        return ''
    i2 = h.find('>', i)
    i = i2 + 1 if i2 >= 0 else 0
    j = h.find('end-paper', i)
    if j >= 0:
        k = h.rfind('<!--', i, j)
        j = k if k >= 0 else j
    else:
        j = len(h)
    seg = h[i:j]
    seg = re.sub('(?i)</(p|div|h[1-6]|tr|section|td|th|li)>', NL, seg)
    t = H.unescape(re.sub('(?s)<[^>]+>', ' ', seg))
    t = t.replace(TAB, ' ')
    while '  ' in t:
        t = t.replace('  ', ' ')
    out = NL.join(x.strip() for x in t.split(NL) if len(x.strip()) > 2)
    if limit and len(out) > limit:
        out = out[:limit] + NL + '[TRUNCATED BY THE EXTRACTOR AT %d CHARACTERS]' % limit
    return out
