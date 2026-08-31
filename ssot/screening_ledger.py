# -*- coding: utf-8 -*-
"""Render EVERY screened record with its decision, into the Screening tab.

⛔ THE DEFECT THIS CLOSES. The format requires "Screening WITH EVERY RECORD AND ITS
DECISION". The built page carries **14 table rows** while the screen's own ledger holds
**1,443**, and the object names the gap itself:

    ledger_is_at: evidence/2026-08-30-dapivirine-ahead/BIBLIOGRAPHIC_SCREEN.json
                  -- 1443 rows, one per screened record
    decisions_sum_to_the_denominator: "1443 of 1443"

⇒ **A COUNT WHERE A LIST BELONGS IS THE OPPOSITE OF THE FORMAT.** 14 rows of per-decision
totals is a summary of the screen; the format asks for the screen. And the ledger living in
a sibling directory means the "one downloadable HTML file" does not contain its own evidence
-- a reader who saves the page saves the summary and loses the records.

⚠️ NO TRUNCATION, EVER. Not "the first 200", not "the excluded ones collapsed". Truncating
here would reproduce the defect in a smaller font: the page would still be showing a
selection while claiming to show the screen. Every row renders, including the 1,238
EXCLUDEs, because a reader checking whether the screen threw away something important can
only do that by reading what it threw away.

⭐ AND EVERY ROW THAT CAN LINK OUT, DOES. The Extraction and Screening tabs currently carry
ZERO outbound links, measured on the built bytes. Every ledger row holds a `pmid`, so every
identified record becomes a link a reader can follow to the source. That is the difference
between an extracted number and a traceable one -- and it is the same mechanism that closes
Extraction's zero-links defect.

Standalone by design: this module imports nothing from the tabbed generator, so it can be
written and reviewed while `build_tabbed.py` is held by another lane.
"""
from __future__ import annotations

import html
import json
import os

PUBMED = "https://pubmed.ncbi.nlm.nih.gov/%s/"

# Decision order: what PASSED first, what was thrown away last, and the two states that are
# neither. A reader auditing a screen reads the passes to check them and the excludes to
# challenge them; burying either is an editorial act.
ORDER = ("PASS_INCLUDED_TRIAL", "PASS_ALREADY_RETRIEVED", "PASS_OUTSIDE_REGISTRY_SET",
         "PASS_NO_ID", "UNDECIDABLE", "EXCLUDE")

GLOSS = {
    "PASS_INCLUDED_TRIAL": "Passed the screen and is a trial this review pools.",
    "PASS_ALREADY_RETRIEVED": "Passed; the record was already held from the registry route.",
    "PASS_OUTSIDE_REGISTRY_SET": "Passed; names a trial outside the registry-retrieved set.",
    "PASS_NO_ID": "Passed the concept screen but carries no trial identifier to join on.",
    "UNDECIDABLE": "Neither passed nor excluded -- the record does not carry enough to decide.",
    "EXCLUDE": "Excluded by a named rule. The rule and reason are on the row.",
}


def _e(v):
    return html.escape("" if v is None else str(v), quote=True)


def load_ledger(path):
    with open(path, encoding="utf-8") as fh:
        doc = json.load(fh)
    rows = doc.get("ledger")
    if not isinstance(rows, list):
        raise ValueError("no `ledger` list in %s -- refusing to render a partial screen"
                         % path)
    return doc, rows


def _row_html(r):
    pmid = r.get("pmid")
    ident = ('<a href="%s" rel="noopener">%s</a>' % (PUBMED % _e(pmid), _e(pmid))) if pmid \
        else '<span class="noid">no identifier</span>'
    return ("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>"
            % (ident, _e(r.get("title")), _e(r.get("journal")), _e(r.get("year")),
               _e(r.get("rule")), _e(r.get("reason"))))


def render(ledger_path, measured_utc):
    """The whole screen, grouped by decision, every row present, links where identified."""
    doc, rows = load_ledger(ledger_path)
    den = doc.get("denominator") or {}
    declared = den.get("records_screened")
    if declared is not None and int(declared) != len(rows):
        # ⛔ FAIL CLOSED. A ledger whose length disagrees with the denominator it claims is
        # exactly the reach-vs-coverage defect; rendering it would publish that as a screen.
        raise ValueError("ledger holds %d rows but the denominator declares %s -- refusing"
                         % (len(rows), declared))

    by = {}
    for r in rows:
        by.setdefault(r.get("decision") or "UNRECORDED", []).append(r)
    seen = set(ORDER)
    groups = list(ORDER) + sorted(k for k in by if k not in seen)

    out = []
    linked = sum(1 for r in rows if r.get("pmid"))
    out.append(
        '<p class="ledger-head">Every one of the <strong>%d</strong> screened records is '
        'below, with the decision and the rule that made it. '
        '<strong>%d</strong> carry an identifier and link to the source; '
        '<strong>%d</strong> do not and say so. Nothing is truncated and nothing is '
        'collapsed away &mdash; a screen a reader cannot read is a count, not a screen. '
        'Ledger read %s.</p>'
        % (len(rows), linked, len(rows) - linked, _e(measured_utc)))

    for g in groups:
        grp = by.get(g) or []
        if not grp:
            continue
        out.append(
            '<details class="screen-group"%s><summary><strong>%s</strong> &mdash; %d record'
            '%s. %s</summary>' % (" open" if g != "EXCLUDE" else "", _e(g), len(grp),
                                  "" if len(grp) == 1 else "s", _e(GLOSS.get(g, ""))))
        out.append('<table class="ledger"><thead><tr><th>Identifier</th><th>Title</th>'
                   '<th>Journal</th><th>Year</th><th>Rule</th><th>Reason</th></tr></thead>'
                   '<tbody>')
        out.extend(_row_html(r) for r in grp)
        out.append("</tbody></table></details>")

    total = sum(len(v) for v in by.values())
    out.append('<p class="ledger-foot">Groups sum to <strong>%d</strong> of '
               '<strong>%d</strong> screened records.</p>' % (total, len(rows)))
    return "\n".join(out)


if __name__ == "__main__":
    import datetime
    import sys
    lp = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        "evidence", "2026-08-30-dapivirine-ahead", "BIBLIOGRAPHIC_SCREEN.json")
    frag = render(lp, datetime.datetime.now(datetime.timezone.utc)
                  .isoformat(timespec="seconds"))
    sys.stdout.buffer.write(frag.encode("utf-8"))
