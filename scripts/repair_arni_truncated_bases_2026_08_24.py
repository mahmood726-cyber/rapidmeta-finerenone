"""Two more copies of the ARNI truncation, and a correction to my own claim.

# no-control: an edit. Its control is asserted inline and the run REFUSES rather than
# writes: each truncated value must be a LITERAL PREFIX of the longer value replacing it,
# both must live in the same object, and no key may be lost.

WHAT I GOT WRONG. Repairing `grade.by_outcome.<oid>.steps[risk_of_bias].reason` on
arni-hfref, I reported "corpus-wide there is exactly one such value". That was a statement
about THE ONE PATH I SEARCHED, not about the corpus, and it was written as though it were
about the corpus.

There are three copies on this object, not one:

    grade.by_outcome.cvdeath_or_hfh_first.steps[risk_of_bias].reason      repaired earlier
    grade.by_outcome.cvdeath_or_hfh_first.grade_table_rows[0].basis       400 chars, here
    grade.by_outcome.cvdeath_or_hfh_first.grade_table_rows[2].basis       400 chars, here

Row 0 is a literal prefix of `results...grade.domains.risk_of_bias.basis_in_sources`
(1,249 chars) -- the same full text as before. Row 2 is a prefix of
`...domains.indirectness.basis_in_sources` (608 chars), a SECOND DOMAIN I did not know was
affected. Both repairs are lookups: the full text is in the same object and the truncated
value is a literal prefix of it, so nothing is decided here.

AND THE 400-CHARACTER BOUNDARY HYPOTHESIS IS REFUTED, which is why this file exists rather
than a corpus-wide truncation fixer. Measured over 12,100 strings of 150+ characters: 17
are exactly 400 long, against a local average of 11.8 per length in the 380-420 band --
1.4x, and there are MORE strings at 401 (25) than at 400. FOUR HUNDRED IS NOT A CUT POINT.
The other fifteen 400-character values are prose that happens to be that long; only these
two are prefixes of a longer sibling, which is the property that makes a truncation
detectable rather than merely suspected.

STORED, NOT RENDERED. `grade_table_rows` is read by no projector in this repository, and
the delivered ARNI page carries the FULL 1,249-character text, not the truncated one. So
this is latent, exactly as the first copy was -- real and not reaching a reader, which are
different statements. ARNI is on do_not_rebuild and the page is not touched.
"""
from __future__ import annotations

import io
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OBJ = os.path.join(REPO, "ssot", "arni-hfref", "arni-hfref.json")
OID = "cvdeath_or_hfh_first"
TARGETS = ((0, "risk_of_bias"), (2, "indirectness"))


def count_keys(x):
    if isinstance(x, dict):
        return len(x) + sum(count_keys(v) for v in x.values())
    if isinstance(x, list):
        return sum(count_keys(v) for v in x)
    return 0


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    apply = "--apply" in sys.argv
    raw = io.open(OBJ, encoding="utf-8", newline="").read()
    obj = json.loads(raw)
    before = count_keys(obj)

    rows = (((obj.get("grade") or {}).get("by_outcome") or {})
            .get(OID) or {}).get("grade_table_rows") or []
    doms = (((obj.get("results") or {}).get("by_outcome") or {})
            .get(OID) or {}).get("grade") or {}
    doms = doms.get("domains") or {}

    plan = []
    for idx, dom in TARGETS:
        if idx >= len(rows):
            sys.exit("REFUSED: grade_table_rows[%d] does not exist." % idx)
        cur = str(rows[idx].get("basis") or "")
        full = str((doms.get(dom) or {}).get("basis_in_sources") or "")
        if not full:
            sys.exit("REFUSED: no basis_in_sources held for domain %r." % dom)
        if len(cur) != 400:
            sys.exit("REFUSED: grade_table_rows[%d].basis is %d characters, not the 400 "
                     "this repair is about; it has already changed." % (idx, len(cur)))
        if not full.startswith(cur):
            sys.exit("REFUSED: the short value at grade_table_rows[%d] is NOT a literal "
                     "prefix of the %s basis. That makes this a rewrite, not a lookup, and "
                     "it is not done here." % (idx, dom))
        plan.append((idx, dom, cur, full))

    print("")
    print("ARNI grade_table_rows -- truncated bases")
    for idx, dom, cur, full in plan:
        print("   row[%d] %-14s %4d -> %4d chars, literal prefix confirmed"
              % (idx, dom, len(cur), len(full)))
        print("        was ending: ...%r" % cur[-46:])
    print("")
    if not apply:
        print("   dry run -- pass --apply to write")
        return
    for idx, dom, cur, full in plan:
        rows[idx]["basis"] = full
        rows[idx]["basis_restored_2026_08_24"] = (
            "Stored TRUNCATED at exactly 400 characters, ending mid-sentence, and restored "
            "from `results.by_outcome.%s.grade.domains.%s.basis_in_sources`, of which the "
            "truncated value was a literal prefix -- a lookup with nothing decided. This is "
            "the second and third copy of a truncation whose first copy was repaired earlier "
            "the same day under the claim that it was the only one corpus-wide. That claim "
            "described the one JSON path searched, not the corpus. `grade_table_rows` is "
            "read by no projector here and the delivered page carries the full text, so "
            "this was latent rather than reaching a reader." % (OID, dom))
    after = count_keys(obj)
    if after < before:
        sys.exit("REFUSED: the object lost keys (%d -> %d)." % (before, after))
    nl = "\r\n" if "\r\n" in raw else "\n"
    body = json.dumps(obj, indent=1, ensure_ascii=False) + "\n"
    io.open(OBJ, "w", encoding="utf-8", newline="").write(
        body.replace("\n", nl) if nl != "\n" else body)
    print("   keys %d -> %d (net-additive); ARNI page NOT rebuilt (do_not_rebuild)"
          % (before, after))


if __name__ == "__main__":
    main()
