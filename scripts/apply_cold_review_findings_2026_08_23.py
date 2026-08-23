"""Three findings from a cold, blinded outside read, each verified against the object first.

# no-control: an edit, not a detector. Its controls are asserted inline and the run REFUSES
# rather than writes if any fails: each target field must currently hold the value being
# corrected, the truncated text must be a literal PREFIX of the full text replacing it, and
# no key may be lost.

WHERE THESE CAME FROM. Two independent models were run over this lane's output, cold: a
GPT-5 lane on the enumerations and a Gemini 3.1 Pro lane on the judgement-shaped questions.
The Gemini lane was given evidence INLINE, with no file access. That produced both of the
things a blinded read produces.

FIRST, WHAT DID NOT SURVIVE, BECAUSE IT COST NOTHING AND IS THE MORE USEFUL HALF. The cold
read returned six charges of fabrication against the attr-pn withdrawal text -- that the
"77 patients" control count, `estimand_established`, the
`estimand_established_does_not_cover_the_contrast_2026_08_20` field, NEURO-TTR as the origin
of the borrowed group, and the Duarte network were all invented. Every one of those six is
ON THE OBJECT and was checked there before being accepted or rejected. They were absent from
the PACKET I built, not from the record.

    AN INCOMPLETE EVIDENCE PACKET MANUFACTURES FALSE DEFECT CLASSES, and it manufactures
    them in the most convincing possible form: a specific, quotable accusation of
    fabrication. The blinding is what makes the read valuable and it is also what makes
    this failure mode certain. The fix is not to stop blinding; it is to check every
    finding against the artefact before acting on it, which is what this file records.

NOW THE THREE THAT DID SURVIVE.

1. THE WITHDRAWAL GIVES ONE GROUND WHERE THE OBJECT RECORDS TWO. The attr-pn withdrawal
   rests entirely on borrowed controls. The object separately records, and has since
   2026-08-20, that the pool combines three different drugs and that PATISIRAN IS THE
   INTERVENTION IN ONE ROW AND THE COMPARATOR IN ANOTHER inside a single pooled number.
   That is an independent ground, it does not depend on the comparator argument, and it is
   arguably the more fundamental of the two. Omitting it understates the case in the
   corpus's own favour, which is a failure in the same family as overstating it. Added --
   and, as with the first ground, this is quoting a field rather than making a new finding.

2. NEURO-TTRansform'S ARMS AND ITS DECLARED CONTRAST DESCRIBE DIFFERENT COMPARISONS, and
   nothing said so. The object holds

       arms                            [["Inotersen", "treatment"], ["Eplontersen", "control"]]
       registration_declared_contrasts [["Eplontersen", "External Placebo"], ...]

   Read cold that looks like corrupt data, and it was reported as such. It is not: the
   trial randomises eplontersen against inotersen AND declares its primary comparison
   against an external placebo group, so both records are true of it and they are true of
   different things. That is exactly why the arm-role correction refused to touch this
   trial. The two records are now stated side by side, so the next cold reader meets the
   explanation rather than the apparent contradiction.

3. A STORED JUSTIFICATION TRUNCATED AT EXACTLY 400 CHARACTERS, ON THE FLAGSHIP.
   `arni-hfref`'s structured `grade.by_outcome.cvdeath_or_hfh_first.steps[risk_of_bias]
   .reason` is 400 characters and ends mid-sentence: "...which is one of the two components.
   In the same trial". The table's `basis_in_sources` for the same domain is 1,249
   characters and the truncated value is a LITERAL PREFIX of it, so the repair is a lookup
   with nothing to decide. Corpus-wide there is exactly one such value; the delivered ARNI
   page renders the TABLE text and so never showed the broken sentence, which is why
   nothing caught it.

   ARNI IS ON `ssot/do_not_rebuild.py` AND IS NOT REBUILT HERE. The object is repaired; the
   page is not touched. A reader sees no change today, and the next legitimate rebuild
   carries a sentence that finishes.

AND ONE DEFECT IN THIS SCRIPT, FOUND BY PLANTING AGAINST ITS OWN CONTROL. The prefix
check was planted -- the full text altered so the truncated value was no longer its
prefix -- and it refused correctly. But it refused AFTER attr-pn had already been
written, because the writes were interleaved with the checks. A refusal that leaves
half the work applied is worse than no refusal: the operator reads REFUSED and believes
nothing happened. Every check for every object now runs first, and nothing is written
until all of them have passed.
"""
from __future__ import annotations

import io
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TODAY = "2026-08-23"

SECOND_GROUND = (
    "AND A SECOND, INDEPENDENT GROUND THAT THIS OBJECT ALREADY RECORDED AND THIS "
    "WITHDRAWAL DID NOT ORIGINALLY NAME. The pool also combines THREE DIFFERENT DRUGS -- "
    "patisiran, vutrisiran and eplontersen -- and, in this object's own words from "
    "2026-08-20, \"PATISIRAN IS THE INTERVENTION IN ONE ROW AND THE COMPARATOR IN ANOTHER "
    "inside a single pooled number\". That does not depend on the comparator argument above "
    "and would stand even if every contrast were randomised and concurrent. It is stated "
    "here because a withdrawal that gives one ground where the record holds two understates "
    "the case in the corpus's own favour, which is a failure of the same kind as "
    "overstating it. Whether to pool ACROSS drugs is a method argument on which reasonable "
    "people differ; whether one number may contain a drug as both intervention and "
    "comparator is not.")

NEURO_NOTE = (
    "THESE TWO RECORDS DESCRIBE DIFFERENT COMPARISONS AND BOTH ARE TRUE OF THIS TRIAL. "
    "`arms` records the randomised allocation -- inotersen against eplontersen. "
    "`registration_declared_contrasts` records the comparison the registration declares for "
    "its primary outcome -- eplontersen against an EXTERNAL placebo group, which is "
    "NEURO-TTR's. A reader meeting only the two fields side by side reads them as a "
    "contradiction or as corrupt data, and an outside model reading this object cold did "
    "exactly that. Neither is corrupt. This is also precisely why the 2026-08-23 arm-role "
    "correction, which corrected twelve arms in six other trials from their registrations, "
    "REFUSED to touch this one: a correction driven by drug-name plausibility would have "
    "inverted it, and a correction driven by the declared contrast would have overwritten a "
    "true record of what was randomised.")


def count_keys(x):
    if isinstance(x, dict):
        return len(x) + sum(count_keys(v) for v in x.values())
    if isinstance(x, list):
        return sum(count_keys(v) for v in x)
    return 0


def load(path):
    raw = io.open(path, encoding="utf-8", newline="").read()
    return raw, json.loads(raw)


def save(path, raw, obj, before):
    after = count_keys(obj)
    if after < before:
        sys.exit("REFUSED: %s lost keys (%d -> %d)." % (path, before, after))
    nl = "\r\n" if "\r\n" in raw else "\n"
    body = json.dumps(obj, indent=1, ensure_ascii=False) + "\n"
    io.open(path, "w", encoding="utf-8", newline="").write(
        body.replace("\n", nl) if nl != "\n" else body)
    return after


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    apply = "--apply" in sys.argv

    # ---- 1 and 2: attr-pn-review
    p = os.path.join(REPO, "ssot", "attr-pn-review", "attr-pn-review.json")
    raw, obj = load(p)
    before = count_keys(obj)
    pooled = ((obj["results"]["by_outcome"]).get("primary") or {}).get("pooled") or {}
    if not pooled.get("withdrawn"):
        sys.exit("REFUSED: attr-pn-review/primary is not withdrawn; the second ground "
                 "would be attached to a live estimate.")
    if "PATISIRAN IS THE INTERVENTION IN ONE ROW" not in json.dumps(obj, ensure_ascii=False):
        sys.exit("REFUSED: the object does not record the mixed-drug finding this quotes. "
                 "Adding it would be a NEW claim, not a quotation.")
    if "three different drugs" in (pooled.get("withdrawn_reason") or "").lower():
        sys.exit("REFUSED: the second ground is already recorded; re-running would stack it.")

    neuro = None
    for t in obj["inputs"]["trials"]:
        if (t.get("nct") or t.get("id")) == "NCT04136184":
            neuro = t
    if neuro is None:
        sys.exit("REFUSED: NEURO-TTRansform is not on this object.")
    arms = [(a.get("label"), a.get("role")) for a in neuro.get("arms") or []]
    if arms != [("Inotersen", "treatment"), ("Eplontersen", "control")]:
        sys.exit("REFUSED: NEURO-TTRansform's arms are %r, not the pair this note explains."
                 % (arms,))

    print("")
    print("1  attr-pn-review/primary -- second independent ground added to the withdrawal")
    print("     the object records it at THE_POOL_IS_REFERRED_2026_08_20; this quotes it")
    print("2  NEURO-TTRansform -- arms and declared contrast stated side by side")
    print("     arms %r" % (arms,))
    print("     declared %r" % (neuro.get("registration_declared_contrasts"),))
    # NOTHING IS WRITTEN HERE. See the note above `main`: this run touches two objects
    # and a refusal on the second used to leave the first already changed.
    plan = [(p, raw, obj, before,
             lambda: (pooled.__setitem__("and_a_second_independent_ground",
                                         SECOND_GROUND),
                      neuro.__setitem__("why_arms_and_declared_contrast_differ",
                                        NEURO_NOTE)))]

    # ---- 3: the arni truncation
    p2 = os.path.join(REPO, "ssot", "arni-hfref", "arni-hfref.json")
    raw2, obj2 = load(p2)
    before2 = count_keys(obj2)
    oid = "cvdeath_or_hfh_first"
    steps = (((obj2.get("grade") or {}).get("by_outcome") or {}).get(oid) or {}).get("steps") or []
    step = next((s for s in steps if s.get("domain") == "risk_of_bias"), None)
    full = ((((obj2["results"]["by_outcome"][oid].get("grade") or {}).get("domains") or {})
             .get("risk_of_bias") or {}).get("basis_in_sources") or "")
    if step is None or not full:
        sys.exit("REFUSED: arni-hfref does not hold both halves of this repair.")
    cur = step.get("reason") or ""
    if len(cur) != 400:
        sys.exit("REFUSED: the structured reason is %d characters, not the 400 this repair "
                 "is about. It has already been changed." % len(cur))
    if not full.startswith(cur):
        sys.exit("REFUSED: the truncated text is NOT a literal prefix of the full text, so "
                 "this is not a truncation and restoring would be a rewrite, not a lookup.")

    print("")
    print("3  arni-hfref -- a structured justification truncated at exactly 400 characters")
    print("     was  %d chars, ending %r" % (len(cur), cur[-42:]))
    print("     full %d chars, and the truncated value is a literal prefix of it" % len(full))
    print("     ARNI is on do_not_rebuild; the OBJECT is repaired and the PAGE is not touched")
    def _write_arni():
        step["reason"] = full
        step["reason_restored_2026_08_23"] = (
            "This reason was stored TRUNCATED AT EXACTLY 400 CHARACTERS and ended "
            "mid-sentence, on the flagship. It is restored from "
            "`results.by_outcome.%s.grade.domains.risk_of_bias.basis_in_sources`, of which "
            "the truncated value was a literal prefix -- so the repair is a lookup and "
            "nothing was decided. Found by an outside model reading the two GRADE locations "
            "cold; no gate in this repository looks for a stored value that stops "
            "mid-sentence. The delivered page renders the TABLE text and so never showed "
            "the broken sentence, which is why it survived." % oid)
    plan.append((p2, raw2, obj2, before2, _write_arni))

    print("")
    if not apply:
        print("   dry run -- pass --apply to write")
        return

    # EVERY CHECK ABOVE HAS PASSED FOR EVERY OBJECT. Only now does anything change.
    for path, r0, o0, b0, mutate in plan:
        mutate()
        n = save(path, r0, o0, b0)
        print("   wrote %-46s keys %d -> %d"
              % (os.path.relpath(path, REPO), b0, n))


if __name__ == "__main__":
    main()
