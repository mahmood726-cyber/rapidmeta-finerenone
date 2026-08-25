"""Remove three defects from ARNI's AUTHORED manuscript, changing as little as possible.

MAHMOOD: "keep it but remove the thre defects. arni is also authored by you but really high
quality work so we should keep to learn from."

So this is not a regeneration. ARNI's manuscript lives in
`ssot/arni-hfref/manuscript_docmodel.json` and is rendered directly; the projector does not
reproduce it and the build guard exists to stop anything replacing it. Editing that file IS
the sanctioned way to amend authored content -- it is the stored document, versioned in git,
and the guard protects it from being OVERWRITTEN by generated prose, which is not what this
does.

THE PROSE IS THE THING BEING PRESERVED, so each edit is the smallest that removes the defect:
the identifier goes, the sentence around it stands. Where removal would leave a sentence
ungrammatical, the minimum words are added to close it, and nothing else is touched.

THREE SITES, and one of them carries real authored argument that must survive intact:

  blocks[90].caption  a Python dict interpolated into a figure caption. It holds the
                      agreement numbers AND a long paragraph of authored reasoning about why
                      RoB-2 agreement is lower than screening agreement. That paragraph is
                      the valuable part and is preserved VERBATIM; only the dict syntax and
                      the field names around it are replaced with the same facts in English.

  blocks[101].text    a dotted field path in a sentence -- "see
                      domains.risk_of_bias.rob2_effect_on_this_rating". The clause is
                      removed; the sentence before it already states the finding.

  blocks[68].rows     an outcome ID standing where an outcome name belongs, in the first
                      column of a four-row table. Replaced with the registered outcome text.

`search_capture.csv` is left alone: it is a filename in the extended data, which a reader can
download, not an identifier leaking into prose.
"""
import io
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOC = os.path.join(REPO, "ssot", "arni-hfref", "manuscript_docmodel.json")

_OUTCOME = ("cardiovascular death or hospitalisation for heart failure, "
            "whichever comes first")


def main():
    apply = "--apply" in sys.argv
    d = json.load(io.open(DOC, encoding="utf-8"))
    blocks = d["blocks"]
    changes = []

    # ---- 1. the dict, WHEREVER IT APPEARS ------------------------------------------
    #
    # A first version amended blocks[90].caption alone, because that is where the scan had
    # shown it. The same dict is also in blocks[235].text and blocks[252].text, so the page
    # still carried it after the "fix" -- the defect was corrected where it had been noticed
    # rather than everywhere the property has to hold, which is the error this repository
    # has now made in prose, in figures, and here in the same week.
    #
    # So: every block, every string field, swept.
    targets = []
    for _bi, _blk in enumerate(blocks):
        for _fld in ("caption", "text"):
            _v = _blk.get(_fld)
            if isinstance(_v, str) and "Agreement as measured: {" in _v:
                targets.append((_bi, _fld))

    for _bi, _fld in targets:
        cap = blocks[_bi].get(_fld) or ""
        i = cap.find("Agreement as measured: {")
        # THE AUTHORED PARAGRAPH, EXTRACTED BY ITS ACTUAL KEY FORM.
        #
        # A first version searched for a DOUBLE-quoted key. The caption is a Python dict
        # repr, so the key is SINGLE-quoted and only the value is double-quoted:
        # `'comparison_to_screening': "This is markedly lower...`. The search matched
        # nothing, `para` came back empty, and the amendment silently DELETED a paragraph of
        # authored reasoning -- the exact content this script exists to preserve. Caught by
        # verifying the written result rather than the diff, and reverted from a backup.
        #
        # The lesson in new clothing: a search that finds nothing returns the same empty
        # string as a field that holds nothing, and the caller cannot tell them apart unless
        # it asks. So this REFUSES rather than proceeding with an empty paragraph.
        _key = "'comparison_to_screening': \""
        j = cap.find(_key)
        if j < 0:
            print("REFUSED: the authored paragraph could not be located inside the caption. "
                  "Amending it would delete authored content, which is the one thing this "
                  "script must not do. Nothing was written.")
            return 2
        para = cap[j + len(_key):].rsplit('"}', 1)[0]
        if len(para.split()) < 40:
            print("REFUSED: the located paragraph is only %d words, which is too short to be "
                  "the authored passage. Nothing was written." % len(para.split()))
            return 2
        new_tail = (
            "Agreement as measured, not asserted: the two assessors agreed on 10 of 15 "
            "domain judgements (66.7 per cent) and on 1 of 3 overall judgements. " + para)
        new_cap = cap[:i] + new_tail
        changes.append(("blocks[%d].%s" % (_bi, _fld), cap[i:i + 90], new_tail[:90]))
        if apply:
            blocks[_bi][_fld] = new_cap

    # ---- 2. the dotted path in a sentence -------------------------------------------
    txt = blocks[101].get("text") or ""
    clause = "; see domains.risk_of_bias.rob2_effect_on_this_rating"
    if clause in txt:
        new_txt = txt.replace(clause, "")
        changes.append(("blocks[101].text", clause, "(clause removed)"))
        if apply:
            blocks[101]["text"] = new_txt

    # ---- 3. the outcome id in a table column ----------------------------------------
    for r, row in enumerate(blocks[68].get("rows") or []):
        if row and isinstance(row[0], str) and "cvdeath_or_hfh_first" in row[0]:
            trial = row[0].split("/")[0].strip()
            new_cell = "%s / %s" % (trial, _OUTCOME)
            changes.append(("blocks[68].rows[%d][0]" % r, row[0], new_cell))
            if apply:
                row[0] = new_cell

    for where, before, after in changes:
        print("  %-26s" % where)
        print("      was: %s" % before[:110])
        print("      now: %s" % after[:110])
    print()
    print("edits: %d" % len(changes))
    if apply:
        io.open(DOC, "w", encoding="utf-8").write(
            json.dumps(d, ensure_ascii=False, indent=1))
        print("written to %s" % os.path.relpath(DOC, REPO))
    else:
        print("DRY RUN. Re-run with --apply to write.")
    return 0


sys.exit(main())
