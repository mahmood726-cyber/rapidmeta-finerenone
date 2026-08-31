# -*- coding: utf-8 -*-
"""Notice when a page GROWS, and require the growth to be declared.

⚠️ THE ASYMMETRY THIS CLOSES. `ssot/manuscript_guard.py` refuses when manuscript text falls
more than 5% or a section disappears. Nothing in this repo notices growth AT ALL. So a page
can double and no gate says a word, while losing a paragraph is blocked -- and the direction
that is unguarded is the one actually costing us.

⛔ AND THE HARM IS MEASURED, NOT HYPOTHETICAL. Two blinded judges called
AGYW_HIV_PREP_REVIEW.html "cluttered" and "hard for a normal clinical reader to use" at
about 87,000 rendered characters -- BEFORE the 687 KB screening ledger was embedded. Clarity
is an axis this corpus loses 0-2 on in head-to-head judging. ⇒ A FORMAT THAT IS COMPLETE AND
UNREADABLE FAILS A DIFFERENT CLAUSE OF THE SAME REQUIREMENT, and completeness is the clause
we are currently optimising.

⭐ THIS IS A DECLARATION, NOT A LIMIT, AND THE DISTINCTION IS THE WHOLE DESIGN.

A size cap would be wrong here and would be gamed within a day: the ledger embed is CORRECT
-- Mahmood ruled it, every one of 1,443 records belongs in the file, and truncating to fit a
threshold would reintroduce the 14-row defect that the embed exists to fix. A cap punishes
the right change and rewards hiding evidence.

What is missing is not restraint. It is a RECORD. So growth past the threshold does not
block; it requires the build to say WHAT was added and WHY, in a field a reader can read.
Undeclared growth refuses; declared growth of any size passes.

    small growth              -> OK, silent
    large growth, declared    -> OK, and the declaration ships on the page
    large growth, undeclared  -> REFUSED, naming the delta and what to declare
    shrink                    -> NOT this module's business; manuscript_guard owns it

Same verdict vocabulary and the same NOT_ASSESSABLE discipline as manuscript_guard: an
absence reported by the filesystem is not an absence in the world, and a first build has
nothing to compare against.
"""
from __future__ import annotations

import os
import re

OK = "OK"
REFUSED = "REFUSED"
NOT_ASSESSABLE = "NOT_ASSESSABLE"

# Fractional growth in RENDERED CHARACTERS above which a declaration is required. Rendered,
# not bytes: a reader's burden is the text they meet, and markup weight is not that.
THRESHOLD = 0.10

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")
_SCRIPT_RE = re.compile(r"<(script|style)\b.*?</\1>", re.S | re.I)

# Growth that a reader does NOT pay for on arrival, because it lands collapsed. Counted and
# reported separately rather than exempted silently -- a collapsed section is still in the
# file, still in the download, and still findable; it simply is not between the reader and
# the result.
_COLLAPSED_RE = re.compile(r"<details(?![^>]*\sopen)[^>]*>(.*?)</details>", re.S | re.I)


def rendered_chars(html):
    """Characters a reader meets, and how many of those arrive collapsed.

    Returns (total, collapsed) or None when there is nothing to measure. None means NOT
    MEASURED and must never be collapsed into zero by a caller.
    """
    if not html:
        return None
    body = _SCRIPT_RE.sub(" ", html)
    total = len(_WS_RE.sub(" ", _TAG_RE.sub(" ", body)).strip())
    collapsed = 0
    for m in _COLLAPSED_RE.finditer(body):
        collapsed += len(_WS_RE.sub(" ", _TAG_RE.sub(" ", m.group(1))).strip())
    return total, collapsed


def check(new_html, out_path, declaration=None, threshold=THRESHOLD):
    """Would writing `new_html` to `out_path` grow the page past the threshold undeclared?

    `declaration` -- what was added and why, in a reader's words. Required only when growth
    exceeds the threshold. A declaration that does not say WHAT was added is not one; this
    module cannot judge that, and the page shipping it is the check.
    """
    new = rendered_chars(new_html)
    if new is None:
        return NOT_ASSESSABLE, "No new HTML to measure."
    if not os.path.exists(out_path):
        return NOT_ASSESSABLE, ("Nothing delivered at %s yet -- a first build has no "
                                "baseline, and an absent file is not a small page."
                                % out_path)
    try:
        with open(out_path, encoding="utf-8", errors="replace") as fh:
            old = rendered_chars(fh.read())
    except OSError as exc:
        return NOT_ASSESSABLE, "Could not read the delivered page (%s)." % exc
    if not old or not old[0]:
        return NOT_ASSESSABLE, "The delivered page has no measurable text."

    old_total, old_collapsed = old
    new_total, new_collapsed = new
    delta = (new_total - old_total) / float(old_total)
    # ⚠️ OPEN TEXT IS COMPARED AGAINST OPEN TEXT. An earlier version of this line divided
    # the new OPEN count by the old TOTAL, which reported -67% for a change that leaves the
    # reader's arrival text within 51 characters of where it was -- a number that reads as a
    # huge improvement and means nothing. Comparing a subset against a whole is the same
    # unit error this repo keeps finding, committed inside the guard written to measure
    # reader burden.
    old_open = max(1, old_total - old_collapsed)
    new_open = new_total - new_collapsed
    open_delta = (new_open - old_open) / float(old_open)

    if delta <= threshold:
        return OK, ("%+.1f%% rendered text (%d -> %d chars); under the %.0f%% declaration "
                    "threshold." % (delta * 100, old_total, new_total, threshold * 100))

    shape = ("%+.1f%% rendered text (%d -> %d chars), of which %d chars arrive COLLAPSED, "
             "so the text a reader meets ON ARRIVAL changes %+.1f%% (%d -> %d open chars)."
             % (delta * 100, old_total, new_total, new_collapsed, open_delta * 100, old_open, new_open))

    if declaration and str(declaration).strip():
        return OK, ("GROWTH DECLARED. %s\n  Declared: %s" % (shape, declaration))

    return REFUSED, (
        "UNDECLARED GROWTH. %s\n"
        "⇒ This is not a size limit and the page is not too big. What is missing is the "
        "RECORD: pass `declaration` saying WHAT was added and WHY, and it ships on the page "
        "so a reader meets the reason for the length rather than only the length. Two "
        "blinded judges have already called this corpus's pages cluttered; growth nobody "
        "wrote down is how a complete page becomes an unreadable one." % shape)


def enforce(new_html, out_path, declaration=None, printer=print):
    verdict, message = check(new_html, out_path, declaration)
    printer("  growth guard: %s -- %s" % (verdict, message))
    if verdict == REFUSED:
        raise SystemExit(1)
    return verdict
