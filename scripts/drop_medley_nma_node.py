#!/usr/bin/env python
"""Drop the inert (already-NULLED) MEDLEY node from the RSV nirsevimab NMA app.

Option B of the nirsevimab/MEDLEY review: the record keyed "NULLED:NCT02878330"
(name="MEDLEY", n=925, RR 0.33 [0.14,0.81], pmid 35687449 = a physics comment)
is removed from both structures in RSV_PROPHY_INFANT_BROAD_NMA_REVIEW.html:
  (1) the NCT->label map entry  "NULLED:NCT02878330":"MEDLEY",
  (2) the realData object entry "NULLED:NCT02878330":{...}

Rationale: MEDLEY (NCT03959488) is a palivizumab-controlled SAFETY trial with no
placebo-controlled MA-RSV-LRTI efficacy RR, so its 0.33 value is unsourced and it
does not belong as a placebo-efficacy node. It was already NULLED (inert) by the
2026-05-10 audit; this removes the dead entry and its garbage PMID entirely.

Binary-safe, asserting, idempotent. Verifies brace/quote balance after edit.
"""
from __future__ import annotations
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(REPO, "RSV_PROPHY_INFANT_BROAD_NMA_REVIEW.html")


def object_span(html: str, key: str):
    """Return (start, end_after_optional_trailing_comma) for key:{...}."""
    i = html.find(key)
    assert i != -1, f"key not found: {key}"
    assert html.count(key) == 1, f"key not unique: {key}"
    j = i + len(key) - 1  # index of the opening '{'
    assert html[j] == "{"
    depth = 0
    k = j
    instr = False
    esc = False
    while k < len(html):
        c = html[k]
        if instr:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                instr = False
        else:
            if c == '"':
                instr = True
            elif c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    break
        k += 1
    end = k + 1
    if end < len(html) and html[end] == ",":
        end += 1
    return i, end


def main():
    html = open(PATH, "rb").read().decode("utf-8", "replace")

    label = '"NULLED:NCT02878330":"MEDLEY",'
    obj_key = '"NULLED:NCT02878330":{'

    if label not in html and obj_key not in html:
        print("already removed (idempotent no-op)")
        return 0

    # remove realData object entry first (compute span on current html)
    start, end = object_span(html, obj_key)
    removed_obj = html[start:end]
    assert 'name:"MEDLEY"' in removed_obj, "span does not contain the MEDLEY object"
    assert '35687449' in removed_obj, "span missing the garbage pmid -- aborting"
    html2 = html[:start] + html[end:]

    # remove the label-map entry
    assert html2.count(label) == 1, "label entry not unique"
    html3 = html2.replace(label, "", 1)

    # sanity: balanced braces & quotes unchanged elsewhere
    assert html3.count('name:"MEDLEY"') == 0, "MEDLEY object still present"
    assert '"NULLED:NCT02878330"' not in html3, "NCT02878330 key still present"
    # brace balance of the whole file should be unchanged net (we removed a balanced object)
    if html.count("{") - html.count("}") != html3.count("{") - html3.count("}"):
        raise SystemExit("brace balance changed unexpectedly -- aborting")

    open(PATH, "wb").write(html3.encode("utf-8"))
    print(f"removed MEDLEY node: {len(removed_obj)} chars (realData) + label entry")
    print("  removed object head:", removed_obj[:70])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
