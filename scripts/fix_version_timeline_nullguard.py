#!/usr/bin/env python3
# sentinel:skip-file
"""Fix TypeError in ReportEngine.generate() -> renderVersionTimeline when a
legacy version-snapshot in localStorage has no 'or' field. Adds Number.isFinite
guards inline so ${s.or.toFixed(2)} becomes ${Number.isFinite(s.or) ? s.or.toFixed(2) : '--'}.

Pattern to fix (at FINERENONE_REVIEW.html:41179 and equivalent line in every
_REVIEW.html). Note: the source file contains literal backslash-u-2013 (the
6-char escape sequence) and literal backslash-u-00B2, not the Unicode characters.
"""
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]

# Literal 6-char escape strings as they appear in source
DASH = "\\u2013"          # literal: –
SUP2 = "\\u00B2"          # literal: ²

OLD = (
    "${s.or.toFixed(2)} "
    "[${s.lci.toFixed(2)}" + DASH + "${s.uci.toFixed(2)}] "
    "&middot; I" + SUP2 + "=${s.i2.toFixed(1)}%"
)

NEW = (
    "${Number.isFinite(s.or) ? s.or.toFixed(2) : '--'} "
    "[${Number.isFinite(s.lci) ? s.lci.toFixed(2) : '--'}" + DASH + "${Number.isFinite(s.uci) ? s.uci.toFixed(2) : '--'}] "
    "&middot; I" + SUP2 + "=${Number.isFinite(s.i2) ? s.i2.toFixed(1) : '--'}%"
)


def main():
    ok = miss = skip = 0
    for p in sorted(ROOT.glob("*_REVIEW.html")):
        raw = p.read_bytes()
        crlf = b"\r\n" in raw
        text = raw.decode("utf-8")
        norm = text.replace("\r\n", "\n")
        if NEW in norm:
            skip += 1
            continue
        if OLD not in norm:
            miss += 1
            continue
        new_norm = norm.replace(OLD, NEW, 1)
        out = new_norm.replace("\n", "\r\n") if crlf else new_norm
        p.write_bytes(out.encode("utf-8"))
        ok += 1
    print(f"patched: {ok}, already-fixed: {skip}, no-match: {miss}")
    return 0 if miss == 0 else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
