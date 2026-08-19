#!/usr/bin/env python3
"""RESTATE THE SEARCH PANELS THAT ARE PARTIALLY HELD -- the third state, encoded.

WHAT THE REMOVAL GOT RIGHT AND WHAT IT GOT WRONG. Eleven pages opened their search tab denying
that any query could be shown, and then showed one. The denial was FALSE and removing it was
right. But on SEVEN of the eleven the panel is still a stub: the query is printed and its
RESULTS TABLE IS EMPTY --

    <table><caption>Table 2. ClinicalTrials.gov API v2 ...</caption></table>

-- with no rows. The pre-push regression check caught this immediately as `ssot_empty_panel`
with `absent-state reason 0c`: I had removed the element that explained an empty panel and left
the panel empty and unexplained.

    THE DENIAL WAS DOING REAL WORK WITH THE WRONG WORDS. Deleting it fixed the false sentence
    and created a silent gap, which is the same trade this project keeps refusing. The remedy is
    REPLACEMENT, not removal.

SO THE THIRD STATE IS WRITTEN OUT EXPLICITLY, per panel:

    HELD              the query, its date and its yield are all on the page.
    PARTIALLY HELD    the query is held and its yield table is not. <- these seven
    NOT HELD          nothing is held, and why.

The four pages whose panels carry a populated table keep the removal and get nothing added.

USAGE
    python scripts/restate_partial_search_panels_2026_08_19.py [--apply]
"""
import io
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REC = os.path.join(REPO, "evidence", "2026-08-19-batch1", "contradicted_refusals.json")
OUT = os.path.join(REPO, "evidence", "2026-08-19-batch1", "partial_search_panels.json")

NOTE = (
    '<div class="absent-state" role="note"><strong>Partially held.</strong> The executed query '
    'is held on this object and is printed below. <strong>Its yield table is not held</strong> '
    '&mdash; the record does not carry the identifiers this query returned, so the number of '
    'records and their disposition cannot be shown here and the table below is empty for that '
    'reason. This panel previously opened by denying that any query could be shown, which was '
    'false: the query was directly beneath it. Corrected 2026-08-19.</div>\n')


def sec(html, sid="pn-search"):
    return re.search(r'<section[^>]*id="%s".*?</section>' % sid, html, re.S)


def table_is_empty(block):
    """A table whose only content is its caption has no yield to show."""
    for m in re.finditer(r"<table>(.*?)</table>", block, re.S):
        body = re.sub(r"<caption>.*?</caption>", "", m.group(1), flags=re.S)
        if re.search(r"<t[rdh][\s>]", body):
            return False
    return True


def run(apply_it):
    rec = json.load(io.open(REC, encoding="utf-8"))
    pages = [f["page"] for f in rec["fixed"]]
    done, left = [], []
    for pg in pages:
        p = os.path.join(REPO, pg)
        with io.open(p, "rb") as fh:
            raw = fh.read()
        html = raw.decode("utf-8", "replace")
        m = sec(html)
        if not m:
            continue
        block = m.group(0)
        if "absent-state" in block:
            left.append({"page": pg, "why": "already carries an absent-state note"})
            continue
        if not table_is_empty(block):
            left.append({"page": pg, "state": "HELD",
                         "why": "the yield table is populated; nothing to restate"})
            continue
        anchor = b'<section class="panel" id="pn-search">\n'
        if raw.count(anchor) != 1:
            left.append({"page": pg, "why": "section opener not found exactly once"})
            continue
        new = raw.replace(anchor, anchor + NOTE.encode("utf-8"))
        grew = len(new) - len(raw)
        if grew != len(NOTE.encode("utf-8")):
            left.append({"page": pg, "why": "unexpected size change"})
            continue
        done.append({"page": pg, "state": "PARTIALLY_HELD", "bytes_added": grew})
        if apply_it:
            with io.open(p, "wb") as fh:
                fh.write(new)
            with io.open(p, "rb") as fh:
                if fh.read() != new:
                    with io.open(p, "wb") as fh2:
                        fh2.write(raw)
                    done.pop()
                    left.append({"page": pg, "why": "post-write check failed; REVERTED"})

    print("panels restated as PARTIALLY HELD: %d" % len(done))
    for d in done:
        print("   %-44s +%d bytes" % (d["page"][:44], d["bytes_added"]))
    print("\nleft alone: %d" % len(left))
    for x in left:
        print("   %-44s %s" % (x["page"][:44], x.get("state") or x["why"]))
    if apply_it:
        with io.open(OUT, "w", encoding="utf-8", newline="") as fh:
            fh.write(json.dumps({"run_utc": "2026-08-19", "restated": done, "left": left,
                                 "the_three_states": {
                                     "HELD": "query, date and yield all on the page",
                                     "PARTIALLY_HELD": "query held, yield table not",
                                     "NOT_HELD": "nothing held, and why"}},
                                indent=1, ensure_ascii=False))
        print("\nwrote %s" % os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.exit(run("--apply" in sys.argv))
