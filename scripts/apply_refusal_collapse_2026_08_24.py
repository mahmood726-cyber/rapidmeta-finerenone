"""Apply the refusal-collapse redesign to ssot/build_tabbed.py.

THE SPEC CAME FROM THE READERS, NOT FROM ME. Eight blind reviewers, each shown only the
rendered Paper panel and told they were peer-reviewing for a clinical journal, all eight
said the manuscript reads BADLY and described it as a debug dump, a renderer log, or
exposed database plumbing. One classified the document line by line: 27 of 118 lines pure
MACHINE, 39 more machine-worded, 56% of the document. Four independently prescribed the
same fix: collapse the scattered refusals into ONE consolidated section and write the rest
in ordinary clinical language.

WHAT DOES NOT CHANGE. Every absence is still named. That is the generator's contract and
the reason it is trustworthy; a redesign that quietly dropped refusals would trade a
readability defect for an honesty one. The refusals move, they do not disappear, and the
table names the article area each one belongs to so nothing loses its address.

FOUR CHANGES:
  1. No `Refused:` block appears in the body of the paper at all.
  2. A section whose ONLY content is refusals does not render a heading. On the posaconazole
     page that removes Discussion and Conclusions from the body; both appear in the table.
  3. One final section, "Not reported in this record", after everything else -- it is an
     audit trail, not part of the scientific argument -- carrying a table of
     Article area | Item not reported | Reason.
  4. The refusal text is split into item and reason on its first " -- " or ". ", because
     the stored strings already carry both and a table wants them in separate columns.

Run with --apply. Idempotent: refuses if already applied.
"""
import io
import os
import sys

TARGET = os.path.join("ssot", "build_tabbed.py")

OLD_REFUSAL_RENDER = '''        for what, missing in s.refusals:
            out.append("<div class='absent-state' role='note'><strong>Refused:</strong> "
                       "%s%s</div>" % (e(_pp._tidy(what)), _mark(missing)))'''

NEW_REFUSAL_RENDER = '''        # REFUSALS NO LONGER INTERRUPT THE PAPER. They are collected and rendered once,
        # at the end, in "Not reported in this record". Readers counted 30, 22 and 14
        # "Refused:" blocks on single pages and every one of them described the result as
        # an audit log rather than a manuscript. Nothing is dropped: each refusal keeps its
        # article area, its item, its reason and its source fields.
        for what, missing in s.refusals:
            _deferred.append((s.heading, _pp._tidy(what), list(missing)))'''

OLD_HEAD = '''    for s in secs:
        out.append("<h3>%s</h3>" % e(s.heading))'''

NEW_HEAD = '''    # A SECTION THAT IS NOTHING BUT A REFUSAL DOES NOT GET A HEADING. A heading promises
    # content; "Discussion" followed only by "Refused: the Discussion" promises and then
    # withdraws in two lines. Its absence is named once, in the table at the end.
    _deferred = []

    def _has_body(sec):
        return bool(sec.paras or getattr(sec, "tables", []) or getattr(sec, "figures", []))

    for s in secs:
        if not _has_body(s):
            for what, missing in s.refusals:
                _deferred.append((s.heading, _pp._tidy(what), list(missing)))
            continue
        out.append("<h3>%s</h3>" % e(s.heading))'''

OLD_CLOSE = '''    out.append("</div>")
    return NL.join(out)


def _paper_panel(canon):'''

NEW_CLOSE = '''    # ---- NOT REPORTED IN THIS RECORD --------------------------------------------------
    #
    # LAST, AND DELIBERATELY. This is an audit trail, not part of the scientific argument,
    # and a reader should be able to read the paper once without being interrupted by it.
    # It is not optional and not collapsed: a reader who wants to know what is missing must
    # be able to see that the list exists without opening anything.
    if _deferred:
        out.append("<h3 id='paper-not-reported'>Not reported in this record</h3>")
        out.append("<p>The items below were not written because the record does not hold "
                   "what they would be composed from. They are named here so that an "
                   "absence is not mistaken for an omission.</p>")
        out.append("<table><caption>Items not reported, and why</caption>")
        out.append("<tr><th>Article area</th><th>Item not reported</th><th>Reason</th></tr>")
        for area, what, missing in _deferred:
            item, reason = _split_refusal(what)
            out.append("<tr><td>%s</td><td>%s</td><td>%s</td></tr>"
                       % (e(area), e(item), e(reason)))
        out.append("</table>")
    out.append("</div>")
    return NL.join(out)


def _split_refusal(what):
    """Split a stored refusal into (item, reason).

    The corpus writes these as one string carrying both -- "the keyword list -- a content
    gap; no keywords are recorded and inventing them would be indexing this review under
    terms nobody chose". A table wants them apart, and the separator the corpus actually
    uses is " -- " first and ". " second. Where there is no separator the whole string is
    the item and the reason column says so rather than being left blank, because an empty
    cell under a filled header asserts a comparison with nothing behind it.
    """
    s = (what or "").strip()
    for sep in (" -- ", " — ", ". "):
        if sep in s:
            item, reason = s.split(sep, 1)
            item = item.strip().rstrip(".,;:")
            reason = reason.strip()
            if item and reason:
                return item[0].upper() + item[1:], reason[0].upper() + reason[1:]
    if not s:
        return "An unnamed item", "No reason was recorded with this refusal."
    return s[0].upper() + s[1:], "No further reason is recorded."


def _paper_panel(canon):'''


def main():
    if "--apply" not in sys.argv:
        print("dry run; pass --apply")
    src = open(TARGET, encoding="utf-8").read()
    if "_split_refusal" in src:
        sys.exit("REFUSED: already applied (found _split_refusal in %s)." % TARGET)
    for old in (OLD_REFUSAL_RENDER, OLD_HEAD, OLD_CLOSE):
        if src.count(old) != 1:
            sys.exit("REFUSED: anchor matched %d times, expected 1:\n%s"
                     % (src.count(old), old[:120]))
    out = (src.replace(OLD_HEAD, NEW_HEAD)
              .replace(OLD_REFUSAL_RENDER, NEW_REFUSAL_RENDER)
              .replace(OLD_CLOSE, NEW_CLOSE))
    if "--apply" in sys.argv:
        with io.open(TARGET, "w", encoding="utf-8") as fh:
            fh.write(out)
        print("applied to %s" % TARGET)
    else:
        print("would change %d bytes -> %d bytes" % (len(src), len(out)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
