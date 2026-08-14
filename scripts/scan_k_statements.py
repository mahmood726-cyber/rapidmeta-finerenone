"""Inventory every TEXTUAL statement of study count across both deliverables.

The numeric gate reconciled object fields and passed while the title said three
and the pool was four. k is written far more often as a word in a phrase than as
a field, so this scans prose: digits AND number-words, adjacent to a study noun.
"""
import io
import json
import os
import re
import sys
import zipfile

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
         "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11,
         "twelve": 12}
NUM = r"(?:\d{1,3}|" + "|".join(WORDS) + r")"
# A count only counts if a STUDY noun follows within a couple of words --
# "three trials" yes, "three domains" / "three scales" / "three tiers" no.
NOUN = (r"(?:randomised |randomized |included |eligible |contributing |"
        r"pooled |further |remaining |subsequent |smaller |later )*"
        r"(?:randomised |randomized )?"
        r"(?:trials?|studies|study|randomisations?|randomizations?|RCTs?|"
        r"comparisons?)")
PAT = re.compile(r"\b(" + NUM + r")\s+(" + NOUN + r")", re.I)
# reverse constructions: "trials (n = 3)", "k = 3", "of the 3 trials"
PAT2 = re.compile(r"\bk\s*=\s*(\d{1,3})\b", re.I)


def hits(text):
    out = []
    for m in PAT.finditer(text or ""):
        tok = m.group(1).lower()
        v = WORDS.get(tok, None)
        if v is None:
            try:
                v = int(tok)
            except ValueError:
                continue
        out.append((v, m.group(0).strip(), m.start()))
    for m in PAT2.finditer(text or ""):
        out.append((int(m.group(1)), m.group(0).strip(), m.start()))
    return out


def walk_json(o, path=""):
    if isinstance(o, dict):
        for k, v in o.items():
            yield from walk_json(v, path + "." + str(k))
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from walk_json(v, path + "[%d]" % i)
    elif isinstance(o, str):
        yield path, o


def report(label, pairs, k):
    """pairs: (location, text). Prints only count-bearing statements."""
    rows = []
    for loc, txt in pairs:
        for v, frag, pos in hits(txt):
            rows.append((v, loc, frag, txt))
    print("\n" + "=" * 78)
    print("%s  --  %d count statement(s)" % (label, len(rows)))
    print("=" * 78)
    bad = 0
    for v, loc, frag, txt in sorted(rows, key=lambda r: (r[0] != k, r[1])):
        flag = "OK " if v == k else "MISMATCH"
        if v != k:
            bad += 1
        ctx = re.sub(r"\s+", " ", txt)
        i = ctx.find(frag)
        ctx = ctx[max(0, i - 70):i + 110]
        print("  [%s] k=%-3s %-52s" % (flag, v, loc[:52]))
        print("           %r" % frag)
        print("           ...%s..." % ctx)
    print("  --> %d MISMATCH, %d OK" % (bad, len(rows) - bad))
    return bad


if __name__ == "__main__":
    OBJ = r"F:\rapidmeta-ssot-shell\ssot\arni-hfref\arni-hfref.json"
    D = (r"F:\claude-temp\claude\F--rapidmeta-finerenone"
         r"\e7f51608-d242-495a-8fdb-f99c306556e9\scratchpad")
    d = json.load(open(OBJ, encoding="utf-8"))
    oid = next(iter(d["results"]["by_outcome"]))
    K = d["results"]["by_outcome"][oid].get("k") or len(
        d["results"]["by_outcome"][oid].get("per_trial") or [])
    print("OBJECT k = %d  (per_trial rows = %d)"
          % (K, len(d["results"]["by_outcome"][oid].get("per_trial") or [])))

    total = 0
    total += report("SSOT OBJECT (all string fields)",
                    list(walk_json(d)), K)

    for name in ("ARNI_manuscript.docx", "ARNI_supplement.docx"):
        p = os.path.join(D, name)
        if not os.path.exists(p):
            continue
        z = zipfile.ZipFile(p)
        pairs = []
        for part in ("word/document.xml", "docProps/core.xml",
                     "docProps/app.xml"):
            if part in z.namelist():
                raw = z.read(part).decode("utf-8", errors="replace")
                pairs.append((name + "::" + part,
                              re.sub(r"<[^>]+>", " ", raw)))
        total += report("DOCX %s" % name, pairs, K)

    page = os.path.join(D, "ARNI_v23_nafis.html")
    if os.path.exists(page):
        h = open(page, encoding="utf-8").read()
        pairs = []
        m = re.search(r"<title>(.{0,600}?)</title>", h, re.S)
        if m:
            pairs.append(("page::<title>", m.group(1)))
        for tag in ("h1", "h2", "h3", "figcaption", "caption"):
            for i, mm in enumerate(re.finditer(
                    r"<%s\b[^>]{0,200}>(.{1,600}?)</%s>" % (tag, tag), h, re.S)):
                pairs.append(("page::%s[%d]" % (tag, i),
                              re.sub(r"<[^>]+>", " ", mm.group(1))))
        for i, mm in enumerate(re.finditer(r'alt="([^"]{1,400})"', h)):
            pairs.append(("page::alt[%d]" % i, mm.group(1)))
        total += report("HTML PAGE (title / headings / captions / alt)",
                        pairs, K)

    print("\n" + "#" * 78)
    print("TOTAL MISMATCHED COUNT STATEMENTS: %d" % total)
    sys.exit(1 if total else 0)
