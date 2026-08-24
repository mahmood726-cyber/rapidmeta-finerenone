"""Give the withdrawal notice the bound the object already states about itself.

THE DEFECT. Ten objects say, in their withdrawal notice:

    ALL 2 OF 2 SEEDED REGISTRATIONS REGISTER NO CLINICAL ENDPOINT AT ANY RANK.

and say, in their own `question` field, the same thing bounded:

    no registration declares a clinical endpoint at any rank
    ON THE CLINICAL QUANTITY THIS PAGE POOLS

The first is a claim about the trials. The second is a claim about this page. They are not
the same claim, and only the second is one the object can support: the trial records show
NCT00377260 registering 21 secondary outcome measures, several of them plainly clinical in
ordinary usage. What the object established is that none of them is the quantity this page
pools. The notice dropped that bound and became a statement about the trials.

THE REPAIR IS A PROJECTION, NOT AN EDIT. The bound is not written here. It is read from the
object's own `question` field and appended to the object's own sentence, in the case of the
sentence it joins. Nothing is rephrased and nothing is softened -- the finding is unchanged
and the claim only stops reaching past its evidence.

TEN, NOT SEVEN. Seven of these were confirmed by cold reviewer lanes. Three --
menacwy-booster, thiamine-sepsis, tigecycline-infection -- carry the identical defect and
were never reviewed, because no lane happened to reach them. SEVEN WAS A COUNT OF REVIEWER
REACH AND I READ IT AS A COUNT OF THE CORPUS. That is the same error as reading an audit's
silence as an absence, and the fix is the same: once a reviewer names a SHAPE, stop counting
the instances the reviewer found and go count the shape.

WHAT THIS DOES NOT TOUCH, AND WHY. Each trial record carries a flag
`clinical_endpoint_at_any_rank`, and on NCT00377260 it is False while the registered
secondaries include "The Distribution of Clinical Failures by the On-therapy Visit". Whether
a clinical failure count is a clinical endpoint is a DEFINITIONAL judgement that flag has
already made. Re-deciding it is a judgement about the evidence, not a projection, so it is
reported and not touched here.
"""
from __future__ import annotations

import glob
import io
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from instrument_controls import require_controls  # noqa: E402

BOUND_RE = re.compile(r"at any rank (on the clinical quantity this page pools)", re.I)
UNBOUNDED = re.compile(r"(REGISTER NO CLINICAL ENDPOINT AT ANY RANK)"
                       r"(?! ON THE CLINICAL QUANTITY)")
FIELDS = ("poolable_reason", "withdrawn_reason")


def object_paths():
    for p in sorted(glob.glob(os.path.join(REPO, "ssot", "*", "*.json"))):
        t = os.path.basename(os.path.dirname(p))
        if os.path.basename(p) == t + ".json":
            yield t, p


def bound_of(obj):
    """The object's OWN bound, read from its own question. Never written here."""
    m = BOUND_RE.search(str(obj.get("question") or ""))
    return m.group(1) if m else None


def repair_text(txt, bound):
    return UNBOUNDED.sub(lambda m: m.group(1) + " " + bound.upper(), txt, count=1)


def scan(apply_it):
    changed, skipped, occurrences = [], [], 0
    for t, p in object_paths():
        raw = io.open(p, encoding="utf-8", newline="").read()
        nl = "\r\n" if "\r\n" in raw else "\n"
        try:
            o = json.loads(raw)
        except ValueError:
            continue
        bysec = (o.get("results") or {}).get("by_outcome") or {}
        if not isinstance(bysec, dict):
            continue
        touched = 0
        bound = bound_of(o)
        for _oid, blk in bysec.items():
            if not isinstance(blk, dict):
                continue
            targets = [blk]
            pl = blk.get("pooled")
            if isinstance(pl, dict):
                targets.append(pl)
            for holder in targets:
                for f in FIELDS:
                    v = holder.get(f)
                    if not isinstance(v, str) or not UNBOUNDED.search(v):
                        continue
                    occurrences += 1
                    if not bound:
                        # THREE STATES. The object states the unbounded claim and does not
                        # state the bound anywhere, so there is nothing to project. That is
                        # COULD NOT DETERMINE, not a licence to write the bound myself.
                        skipped.append((t, f, "object states no bound of its own"))
                        continue
                    holder[f] = repair_text(v, bound)
                    touched += 1
        if touched:
            changed.append((t, touched))
            if apply_it:
                # KEY COUNT BEFORE AND AFTER, AND THE FILE'S OWN LINE ENDING. A five-value
                # change once became a 2,452-line diff because the writer chose the newline.
                before = raw.count('":')
                out = json.dumps(o, indent=1, ensure_ascii=False)
                if nl != "\n":
                    out = out.replace("\n", nl)
                assert out.count('":') == before, (t, before, out.count('":'))
                io.open(p, "w", encoding="utf-8", newline="").write(out + nl)
    return changed, skipped, occurrences


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    apply_it = "--apply" in sys.argv

    # CONTROLS, KEYED TO FIXTURE STRINGS AND NOT TO THE CORPUS THIS RUN MOVES.
    #
    # A control keyed to "how many objects still carry the unbounded form" would read PASS
    # before the run and FAIL after it, measuring the repair rather than the repairer. That
    # mistake has now been made seven times in this session, so both controls below are
    # literal strings that no run can touch.
    pos_in = ("ALL 2 OF 2 SEEDED REGISTRATIONS REGISTER NO CLINICAL ENDPOINT AT ANY RANK. "
              "Every registration was read.")
    pos_out = repair_text(pos_in, "on the clinical quantity this page pools")
    neg_in = ("ALL 2 OF 2 SEEDED REGISTRATIONS REGISTER NO CLINICAL ENDPOINT AT ANY RANK ON "
              "THE CLINICAL QUANTITY THIS PAGE POOLS. Every registration was read.")
    neg_out = repair_text(neg_in, "on the clinical quantity this page pools")
    require_controls(
        "repair_unbounded_registration_claim",
        ("an unbounded fixture sentence gains the bound once: %r" % pos_out[:96],
         pos_out.count("ON THE CLINICAL QUANTITY THIS PAGE POOLS") == 1
         and pos_out != pos_in, True),
        ("an ALREADY-BOUNDED fixture sentence must come back byte-identical, or a second "
         "run would bound it twice; changed=%s" % (neg_out != neg_in),
         neg_out != neg_in, True))

    changed, skipped, occ = scan(apply_it)
    print("")
    print("UNBOUNDED REGISTRATION CLAIM%s" % ("  [APPLIED]" if apply_it else "  [dry run]"))
    print("")
    print("   objects carrying it                    %4d" % (len(changed) + len(
        {t for t, _f, _w in skipped})))
    print("   field occurrences                      %4d" % occ)
    print("   objects repaired from their own bound  %4d" % len(changed))
    print("   objects with no bound of their own     %4d   <- could not determine"
          % len({t for t, _f, _w in skipped}))
    print("")
    reviewed = {"amoxicillin-aom", "doravirine-hiv", "influenza-recombinant",
                "lenacapavir-hiv", "linezolid-mrsa", "posaconazole-fungal",
                "rifapentine-tb"}
    for t, n in changed:
        print("   %-30s fields=%d   %s"
              % (t, n, "confirmed by a reviewer lane" if t in reviewed
                 else "NEVER REVIEWED -- found by counting the shape"))
    for t, f, why in skipped:
        print("   %-30s %-18s %s" % (t, f, why))


if __name__ == "__main__":
    main()
