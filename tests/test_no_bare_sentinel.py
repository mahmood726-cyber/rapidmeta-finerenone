#!/usr/bin/env python
"""No delivered page may render the absence sentinel as a value-shaped string.

The converter (ssot/sentinel_render.py) turns "not recorded on the page this object was
extracted/built from", where it is the value of a cell/paragraph/note, into a machine-readable
<em data-absent='NOT_ON_SOURCE_PAGE'>. build_tabbed applies it on every build. This test reads
the SERVED BYTES of every indexed page that has a source object and fails if a bare
value-position sentinel survives on any of them -- so the placeholder cannot come back through a
rebuild, a hand-edit, or a new render path. A sentinel SPLICED into a sentence is a different
defect and is intentionally not covered here.

Run: python tests/test_no_bare_sentinel.py   (or via pytest)
"""
import io
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "ssot"))
import sentinel_render as sr


def _served_pages_with_object():
    idx = io.open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
    pages = sorted(set(re.findall(r'["\'](?:\./)?([A-Za-z0-9_]+_REVIEW\.html)["\']', idx)))
    pmap = json.load(io.open(os.path.join(ROOT, "ssot", "PAGE_MAP.json"), encoding="utf-8"))
    out = []
    for p in pages:
        obj = pmap.get(p)
        pp = os.path.join(ROOT, p)
        if obj and os.path.exists(os.path.join(ROOT, obj)) and os.path.exists(pp):
            out.append((p, pp))
    return out


def main():
    offenders = []
    pages = _served_pages_with_object()
    for name, path in pages:
        html = io.open(path, "rb").read().decode("utf-8")
        n = sr.count_bare(html)
        if n:
            offenders.append((name, n))
    print("test_no_bare_sentinel: %d served page(s) with an object scanned" % len(pages))
    if offenders:
        print("  FAIL -- value-shaped sentinel survives on:")
        for name, n in offenders:
            print("    %-46s %d cell(s)" % (name, n))
        return 1
    print("  OK -- no page renders a bare value-position sentinel")
    return 0


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    raise SystemExit(main())
