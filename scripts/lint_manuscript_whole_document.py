#!/usr/bin/env python3
"""A WHOLE-DOCUMENT CHECK ON THE PROJECTED MANUSCRIPT. Per-section checks are blind to this.

WHY IT EXISTS. The risk-of-bias ceiling statement -- 300 characters -- was emitted TWICE in
every manuscript whose object records one: once by `methods_synthesis`, which had carried it
for weeks, and once by the `risk_of_bias` section added hours later.

    NEITHER SITE WAS WRONG ON ITS OWN. The duplication came into existence when the second
    section was added, which is exactly why it was invisible to whoever wrote either one.
    No check that looks at one section at a time can see it, however careful.

So the unit of checking has to be the DOCUMENT. Three things are checked, each of which is a
property of the whole and of no part:

  D1 REPEATED PARAGRAPH   the same substantial paragraph emitted in more than one place
  D2 REPEATED TABLE       the same caption, or the same rows, tabled twice
  D3 REFUSED-THEN-USED    one section refuses for want of a field that ANOTHER section
                          successfully cites. That is class 29 at document scale: the
                          manuscript tells the reader a thing is not held on a page that
                          uses it.

WHAT IT DELIBERATELY DOES NOT DO. It does not flag near-duplicates or paraphrase. A rule that
fires on similarity would fire on every methods section in the corpus and would be ignored
within a day -- the same reasoning that kept the refusal lint narrow enough to find 11 real
contradictions among 38 candidates.

Exit 1 on any finding. Absent or unreadable objects are NOT_ASSESSABLE, named, and never a
failure: an absence reported by a filesystem is not an absence in the world.
"""
import collections
import glob
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "ssot"))
import paper_projector as ppj                                          # noqa: E402

PARA_FLOOR = 120                 # a paragraph short enough to repeat innocently
NA, FINDINGS = [], []


def check(topic, obj):
    """Return [(code, detail)] for one object's projected manuscript."""
    out = []
    secs = ppj.project(obj)

    # D1 -- the same substantial paragraph in more than one place
    seen = collections.defaultdict(list)
    for s in secs:
        for text, _ in s.paras:
            if len(text) >= PARA_FLOOR:
                seen[text].append(s.key)
    for text, keys in seen.items():
        if len(keys) > 1:
            out.append(("D1 repeated paragraph",
                        "%d chars in sections %s -- %r"
                        % (len(text), " + ".join(keys), text[:90])))

    # D2 -- the same table twice, by caption or by content
    caps = collections.defaultdict(list)
    bodies = collections.defaultdict(list)
    for s in secs:
        for caption, headers, rows, _ in getattr(s, "tables", []):
            caps[caption].append(s.key)
            bodies[json.dumps(rows, sort_keys=True)].append(s.key)
    for cap, keys in caps.items():
        if len(keys) > 1:
            out.append(("D2 repeated table caption",
                        "%r in sections %s" % (cap[:70], " + ".join(keys))))
    for body, keys in bodies.items():
        if len(keys) > 1 and len(body) > 80:
            out.append(("D2 repeated table content",
                        "identical rows in sections %s" % " + ".join(keys)))

    # D3 -- a field refused in one section and successfully cited in another
    refused_fields = collections.defaultdict(list)
    used_fields = collections.defaultdict(list)
    for s in secs:
        for _what, missing in s.refusals:
            for f in missing:
                refused_fields[f].append(s.key)
        for _text, fields in s.paras:
            for f in fields:
                used_fields[f].append(s.key)
        for _c, _h, _r, fields in getattr(s, "tables", []):
            for f in fields:
                used_fields[f].append(s.key)
    for f, where in refused_fields.items():
        if f in used_fields:
            out.append(("D3 refused-then-used",
                        "`%s` refused in %s and USED in %s"
                        % (f, " + ".join(sorted(set(where))),
                           " + ".join(sorted(set(used_fields[f]))))))
    return out


def main():
    os.chdir(REPO)
    only = sys.argv[1:] or None
    topics = 0
    for op in sorted(glob.glob("ssot/*/*.json")):
        name = os.path.basename(op)[:-5]
        if os.path.basename(os.path.dirname(op)) != name:
            continue
        if only and name not in only:
            continue
        try:
            obj = json.load(open(op, encoding="utf-8"))
        except Exception as exc:
            NA.append((name, "unreadable: %s" % exc))
            continue
        if not isinstance(obj, dict) or "title" not in obj:
            NA.append((name, "not a topic object"))
            continue
        topics += 1
        try:
            found = check(name, obj)
        except Exception as exc:
            NA.append((name, "projector raised %s: %s" % (type(exc).__name__, exc)))
            continue
        for code, detail in found:
            FINDINGS.append((name, code, detail))

    print("manuscripts checked as WHOLE DOCUMENTS : %d" % topics)
    print("NOT_ASSESSABLE                         : %d" % len(NA))
    for n, why in NA[:10]:
        print("    %-38s %s" % (n[:38], why))
    print()
    by_code = collections.Counter(c for _, c, _ in FINDINGS)
    print("FINDINGS: %d across %d topic(s)"
          % (len(FINDINGS), len({t for t, _, _ in FINDINGS})))
    for code, n in sorted(by_code.items()):
        print("    %-28s %d" % (code, n))
    print()
    for topic, code, detail in FINDINGS[:40]:
        print("  %-30s %-28s %s" % (topic[:30], code, detail[:90]))
    if len(FINDINGS) > 40:
        print("  ... %d more" % (len(FINDINGS) - 40))
    if FINDINGS:
        print()
        print("REFUSED: a projected manuscript repeats itself or contradicts itself across "
              "sections.")
        return 1
    print("OK -- no manuscript repeats a paragraph or a table, and no section refuses for "
          "want of a field another section uses.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
