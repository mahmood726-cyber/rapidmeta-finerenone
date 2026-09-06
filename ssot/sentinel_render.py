"""Convert the value-shaped absence sentinel into a machine-readable null+state.

THE DEFECT. Objects store an absence as a literal sentence -- "not recorded on the page this
object was extracted from" (and "...built from") -- and the template rendered it verbatim into
a table cell. 197 such cells across 29 delivered pages (measured 2026-09-06). A reader can tell
it is an absence, but a CHECK cannot: it is a non-empty string, so any test asking "is this
field populated?" waves it through. That is how a placeholder survives -- it is value-shaped.

THE CONVERSION. Wrap the sentinel, WHERE IT IS THE ENTIRE VALUE OF A CELL, in
`<em data-absent='NOT_ON_SOURCE_PAGE'>...</em>`. The reader sees the same words; a check now has
`data-absent` to key on, so the null carries a state and is no longer a bare value. One pass
over the assembled HTML converts every rendering of every field at once -- so a field cannot
clear in one table and survive in another, which is the failure this is written against.

SCOPE, DELIBERATELY NARROW. Only a sentinel that is the WHOLE text of a `<td>`/`<th>` cell is
converted. A sentinel spliced into a sentence ("Methodological decisions follow <sentinel>,
version...") is a DIFFERENT defect -- a sentence built around a marker -- and paper_projector
already refuses those; wrapping mid-prose would nest an <em> inside a clause. Matching the cell
boundary also makes this idempotent: after conversion the cell is `<td><em ...>...</em></td>`,
which the pattern no longer matches.
"""
from __future__ import annotations

import re

_SENTINEL = r'not recorded on the page this object was (?:extracted|built) from'
_STATE = "NOT_ON_SOURCE_PAGE"
# A sentinel that BEGINS an element's text node -- immediately preceded by a tag's '>'. That is
# what makes it the value of a cell (`<td>S</td>`), a Methods paragraph (`<p>S<sup>1</sup></p>`),
# or a note (`<small>S</small>`), rather than a word spliced into a sentence ("follow S,
# version") which is preceded by text, not '>', and is a DIFFERENT defect left untouched here.
# The second lookbehind makes it idempotent: once wrapped, the sentinel is preceded by the
# marker, so a re-run skips it.
_BARE = re.compile(r"(?<=>)(?<!NOT_ON_SOURCE_PAGE'>)(" + _SENTINEL + r")")


def _wrap(m):
    return "<em data-absent='%s'>%s</em>" % (_STATE, m.group(1))


def count_bare(html):
    """Value-position sentinels not yet converted -- the number a gate must drive to zero."""
    return len(_BARE.findall(html))


def convert_sentinels(html):
    """Wrap every value-position absence sentinel as a null+state <em data-absent>. A sentinel
    spliced mid-sentence (preceded by a word, not '>') is left alone. Idempotent."""
    return _BARE.sub(_wrap, html)


def _selftest():
    out, ok = [], True

    def check(name, cond):
        nonlocal ok
        ok &= bool(cond)
        out.append((name, "OK" if cond else "*** FAIL ***"))

    cell = "<td>not recorded on the page this object was extracted from</td>"
    conv = convert_sentinels(cell)
    check("a full-cell sentinel is wrapped with data-absent",
          "data-absent='NOT_ON_SOURCE_PAGE'" in conv and count_bare(conv) == 0)
    check("the reader-visible words are preserved",
          "not recorded on the page this object was extracted from" in conv)

    th = "<th scope='col'>Comparator</th><td>not recorded on the page this object was built from</td>"
    check("the 'built from' variant and <th> cells convert too",
          count_bare(convert_sentinels(th)) == 0)

    # THE METHODS-SECTION CASE the whole change is aimed at: a field that clears in the PROSPERO
    # <td> must ALSO clear where it renders in a Methods <p> (often with a trailing citation ref)
    # and in a <small> note. If these survive, a field cleared in one table and not another.
    para = "<p>not recorded on the page this object was extracted from<sup class='prov-ref'>1</sup></p>"
    check("a Methods <p> with a trailing citation ref converts",
          count_bare(convert_sentinels(para)) == 0 and "<sup class='prov-ref'>1</sup>" in convert_sentinels(para))
    small = "<small>not recorded on the page this object was extracted from</small>"
    check("a <small> note converts", count_bare(convert_sentinels(small)) == 0)
    plain = "<p>not recorded on the page this object was extracted from</p>"
    check("a full-value <p> converts", count_bare(convert_sentinels(plain)) == 0)

    check("idempotent -- a second pass changes nothing",
          convert_sentinels(conv) == conv and convert_sentinels(convert_sentinels(para)) == convert_sentinels(para))

    prose = ("<p>Methodological decisions follow not recorded on the page this object was "
             "built from, version 2</p>")
    check("a sentinel SPLICED into prose (preceded by a word) is left alone (different defect)",
          convert_sentinels(prose) == prose)

    real = "<td>Placebo or standard of care</td>"
    check("a real value is untouched", convert_sentinels(real) == real)

    embedded_json = '"comparator": "not recorded on the page this object was extracted from"'
    check("a sentinel inside the embedded object JSON (preceded by a quote) is not touched",
          convert_sentinels(embedded_json) == embedded_json)

    return ok, out


if __name__ == "__main__":
    import io, sys
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    good, rows = _selftest()
    print("sentinel_render selftest")
    for name, verdict in rows:
        print("  %-58s %s" % (name, verdict))
    print("\n%s" % ("ALL PASS" if good else "FAILURES ABOVE"))
    raise SystemExit(0 if good else 1)
