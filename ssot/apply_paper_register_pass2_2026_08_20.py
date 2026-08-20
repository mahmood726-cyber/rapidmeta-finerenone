"""Pass 2: the residue the first pass did not reach, found by reading the measurement.

PASS 1 MOVED 21% TO 16% ON THE SGLT2 PANEL, AGAINST A PREDICTION OF 8-12%. That prediction
was not met, and reading what survived says why: the remaining machine vocabulary is not in
the paragraphs at all. It is in the TABLE CELLS, and the worst of it is a Python dict
printed straight onto the page.

FOUR THINGS, all projector-level, all reaching every page that has them.

1. A RAW PYTHON DICT REPR IN THE GRADE TABLE. `"; ".join(str(x) for x in blk["steps"])`
   renders each rating step as `{'domain': 'risk_of_bias', 'levels': -1, 'from': 'HIGH',
   'to': 'MODERATE', 'reason': 'Rated down one level because unassessed is not low.'}`.
   THAT IS LITERALLY COMPUTER CODE ON A PAGE A READER OPENED. The step becomes a sentence:
   "risk of bias: HIGH to MODERATE, down 1 -- Rated down one level because unassessed is
   not low." Every value is the same value.

2. ESTIMAND KEYS AS TABLE ROW LABELS. The GRADE table's first column is `oid` and the
   risk-of-bias table's first column begins `cvdeath_or_whf_first -- DAPA-HF
   (NCT03036124)`. Both become the outcome's registered name, with the key still reachable
   in the section's source list.

3. DOMAIN KEYS AS TABLE TEXT. `risk_of_bias -1 inconsistency +0 indirectness +0 imprecision
   -1 publication_bias +0` becomes worded domains.

4. STORAGE PRECISION IN A GRADE REASON. "The interval (0.7062 to 0.8258)" and "(0.709 to
   0.8659)" carry four decimals where the estimate supports three significant figures. THIS
   ONE IS ON THE OBJECT, NOT IN THE PROJECTOR -- it is stored text -- so it is NOT rewritten
   here. Rewriting stored prose from a projector would be the projector inventing content,
   which is the rule every refusal on these pages rests on. It is reported and left.

AND ONE THING DELIBERATELY NOT DONE. Three sentences name a field in backticks --
"recorded in `prisma_flow`", "recorded element by element in
`screening.eligibility_provenance`". Those are hand-written sentences whose POINT is to tell
a reader where to look; the field name is the content, not the register. They stay.
"""
import io
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJ = os.path.join(REPO, "ssot", "paper_projector.py")


def sub_once(src, old, new, what):
    if old not in src:
        sys.exit("REFUSED: %s -- the text this pass was written against is not present." % what)
    if src.count(old) != 1:
        sys.exit("REFUSED: %s -- %d occurrences, expected one." % (what, src.count(old)))
    return src.replace(old, new, 1)


STEP_WORDS = '''
_GRADE_DOMAINS = {
    "risk_of_bias": "risk of bias",
    "publication_bias": "publication bias",
    "inconsistency": "inconsistency",
    "indirectness": "indirectness",
    "imprecision": "imprecision",
    "large_effect": "large effect",
    "dose_response": "dose-response",
    "confounding": "residual confounding",
}


def _grade_step_words(step):
    """One GRADE rating step as a sentence rather than as a dict repr.

    THIS WAS `str(x)` AND IT PUT `{'domain': 'risk_of_bias', 'levels': -1, 'from': 'HIGH',
    'to': 'MODERATE', 'reason': '...'}` ON A DELIVERED PAGE. Every value below is the same
    value; only the rendering changed. A step that is not a dict is returned as its own
    string rather than dropped -- an unrecognised shape must still reach the reader.
    """
    if not isinstance(step, dict):
        return str(step)
    dom = _GRADE_DOMAINS.get(step.get("domain"), str(step.get("domain") or "")
                             .replace("_", " "))
    lv = step.get("levels")
    frm, to = step.get("from"), step.get("to")
    bits = [dom] if dom else []
    if frm and to and frm != to:
        bits.append("%s to %s" % (frm, to))
    elif lv == 0 or lv == "0":
        bits.append("not rated down")
    if lv not in (None, 0, "0"):
        try:
            bits.append("down %d level(s)" % abs(int(lv)))
        except (TypeError, ValueError):
            bits.append("levels %s" % lv)
    txt = ": ".join([bits[0], ", ".join(bits[1:])]) if len(bits) > 1 else "".join(bits)
    reason = str(step.get("reason") or "").strip()
    return ("%s -- %s" % (txt, reason)) if reason else txt

'''

OLD_GRADE_ROWS = '''        rows.append([oid, str(blk.get("certainty") or "not rated"), str(blk.get("k", "?")),
                     str(blk.get("started_at") or ""),
                     "; ".join(str(x) for x in (blk.get("steps") or [])) or "no downgrade recorded"])'''
NEW_GRADE_ROWS = '''        # THE OUTCOME'S NAME AND WORDED STEPS. This row used to begin with the estimand
        # key and end with a Python dict repr. The key is still reachable -- it is in this
        # section's source list, as `grade.by_outcome.<oid>`.
        rows.append([_outcome_words(obj, oid), str(blk.get("certainty") or "not rated"),
                     str(blk.get("k", "?")), str(blk.get("started_at") or ""),
                     "; ".join(_grade_step_words(x) for x in (blk.get("steps") or []))
                     or "no downgrade recorded"])'''

OLD_ROB_ROW = '''                    rows.append(["%s -- %s (%s)" % (oid, label, rid),'''
NEW_ROB_ROW = '''                    # The outcome's NAME, not its key. Handbook 8.2 requires the
                    # result to be named; it does not require it to be named in the
                    # object's storage vocabulary.
                    rows.append(["%s -- %s (%s)"
                                 % (_outcome_words(obj, oid), label, rid),'''

OLD_ROB_WHY = '''                            why += ("  %s: %s -- %s"
                                    % (dn.replace("_", " "), dv.get("judgement"),'''
NEW_ROB_WHY = '''                            why += ("  %s: %s -- %s"
                                    % (_ROB_DOMAINS.get(dn, dn.replace("_", " ")),
                                       dv.get("judgement"),'''

ROB_DOMAINS = '''
_ROB_DOMAINS = {
    "D1": "randomisation process",
    "D2": "deviations from intended intervention",
    "D3": "missing outcome data",
    "D4": "measurement of the outcome",
    "D5": "selection of the reported result",
    "overall": "overall",
}

'''


def main():
    dry = "--apply" not in sys.argv
    p = io.open(PROJ, encoding="utf-8").read()
    if "_grade_step_words" not in p:
        anchor = "def _outcome_words(obj, oid):"
        if anchor not in p:
            sys.exit("REFUSED: pass 1 has not been applied; _outcome_words is absent.")
        p = p.replace(anchor, STEP_WORDS.lstrip("\\n") + ROB_DOMAINS.lstrip("\\n") + anchor, 1)
    p = sub_once(p, OLD_GRADE_ROWS, NEW_GRADE_ROWS, "the GRADE table rows")
    p = sub_once(p, OLD_ROB_ROW, NEW_ROB_ROW, "the risk-of-bias row label")
    p = sub_once(p, OLD_ROB_WHY, NEW_ROB_WHY, "the risk-of-bias domain label")
    print("paper_projector.py: GRADE steps worded, outcome names in both tables, RoB "
          "domains worded")
    if dry:
        print("DRY RUN -- pass --apply to write")
        return
    io.open(PROJ, "w", encoding="utf-8", newline="\n").write(p)
    print("wrote paper_projector.py")


if __name__ == "__main__":
    main()
