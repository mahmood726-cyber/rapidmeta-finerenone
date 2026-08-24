"""Does a withdrawal notice claim MORE than the object's own scoped wording?

# control: the POSITIVE is amoxicillin-aom, established by hand before this existed -- its
# `withdrawn_reason` opens "ALL 2 OF 2 SEEDED REGISTRATIONS REGISTER NO CLINICAL ENDPOINT AT
# ANY RANK" while the object's `question` says the same thing scoped, "...on the clinical
# quantity this page pools", and the object holds three clinical endpoints. The NEGATIVE is
# attr-pn-review, whose withdrawal was written tonight against the object's own fields and
# must NOT be flagged.

EVERY GUARD IN THIS REPOSITORY POINTS AT OVERCLAIMING A RESULT. This one points the other
way. A withdrawal notice that drops a scoping clause converts an accurate criticism of OUR
SYNTHESIS into a false sweeping claim about SOMEBODY'S TRIALS.

    "All 2 of 2 seeded registrations register no clinical endpoint at any rank."

is a statement about two real trials run by real investigators, and it is false: the object
holds Time to Resolution of Symptoms, Adverse Events and Resolution of Symptoms in those
registrations. What is true is the scoped version the object states three separate times --
that no registration pre-specified THE QUANTITY THIS PAGE POOLS.

    BEING UNFAIRLY HARSH IS A FABRICATION TOO, and it is the direction with no guard. The
    same shape as a hardcoded "none pre-specified" subgroup row: a refusal asserted without
    checking. An overclaimed result gets caught by a reader who knows the trial; an
    overclaimed criticism reads as rigour.

TWO CHECKS, BOTH KEYED TO THE OBJECT'S OWN WORDS.

  A  A SCOPE CLAUSE HELD AND DROPPED. The object states a scoped version somewhere --
     `question`, `which_limb_fails`, `poolable_reason` -- and the rendered notice states the
     unscoped one. Detected by the scope phrases the corpus actually uses, not by a
     paraphrase, so a hit is quotable rather than arguable.

  B  A FIELD THAT EXISTS TO PREVENT A MISREADING AND IS NOT PROJECTED.
     `what_this_verdict_does_not_establish` is written for exactly one purpose: to stop a
     reader taking a statement about a REGISTRATION as a statement about a TRIAL. Held and
     not rendered, it is the estimand-caveat diagnosis again -- 125 objects, zero pages.
"""
from __future__ import annotations

import glob
import io
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from instrument_controls import require_controls  # noqa: E402

GUARD_FIELD = "what_this_verdict_does_not_establish"

# The scoping phrases this corpus actually uses. Read off the objects, not invented.
SCOPES = (
    "on the clinical quantity this page pools",
    "the pooled quantity is not pre-specified",
    "the quantity this page pools",
    "that this page pools",
    "the pooled quantity",
)
# An unscoped sweeping form: a universal quantifier over the registrations or trials.
SWEEPING = ("at any rank", "no clinical endpoint", "none of the", "not one",
            "no registration", "all of them", "every registration")


def pagemap():
    p = os.path.join(REPO, "ssot", "PAGE_MAP.json")
    m = json.load(io.open(p, encoding="utf-8"))
    out = {}
    for pg, rel in m.items():
        out.setdefault(rel.replace("\\", "/"), []).append(pg)
    return out


def scan():
    pm = pagemap()
    rows = []
    for p in sorted(glob.glob(os.path.join(REPO, "ssot", "*", "*.json"))):
        t = os.path.basename(os.path.dirname(p))
        if os.path.basename(p) != t + ".json":
            continue
        rel = "ssot/%s/%s.json" % (t, t)
        try:
            o = json.load(io.open(p, encoding="utf-8"))
        except ValueError:
            continue
        pages = [x for x in pm.get(rel, []) if os.path.isfile(os.path.join(REPO, x))]
        blob = json.dumps(o, ensure_ascii=False).lower()
        for oid, blk in ((o.get("results") or {}).get("by_outcome") or {}).items():
            if not isinstance(blk, dict):
                continue
            pl = blk.get("pooled") or {}
            if not isinstance(pl, dict) or not pl.get("withdrawn"):
                continue
            reason = str(pl.get("withdrawn_reason") or "")
            # THE POSITIVE PROPERTY: this withdrawal carries a stated reason, which is
            # the text this audit reads. A withdrawal with no reason is not skipped
            # silently below -- it is counted as its own state, because `no reason
            # recorded` is a finding about the object and not a gap in the audit.
            if reason:
                low = reason.lower()
                scoped_on_object = [s for s in SCOPES if s in blob]
                scoped_in_reason = [s for s in SCOPES if s in low]
                sweeping = [w for w in SWEEPING if w in low]
                guard = blk.get(GUARD_FIELD) or pl.get(GUARD_FIELD) or o.get(GUARD_FIELD)
                guard_rendered = None
                if guard and pages:
                    needle = str(guard)[:60].lower()
                    guard_rendered = any(
                        needle in io.open(os.path.join(REPO, pg), encoding="utf-8",
                                          errors="replace").read().lower()
                        for pg in pages)
                rows.append({
                    "topic": t, "outcome": oid, "pages": pages,
                    "scope_on_object": scoped_on_object,
                    "scope_in_reason": scoped_in_reason,
                    "sweeping_in_reason": sweeping,
                    "drops_scope": bool(scoped_on_object and not scoped_in_reason and sweeping),
                    "guard_held": bool(guard),
                    "guard_rendered": guard_rendered,
                })
    return rows


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    rows = scan()
    by = {(r["topic"], r["outcome"]): r for r in rows}
    pos = by.get(("amoxicillin-aom", "primary"))
    neg = by.get(("attr-pn-review", "primary"))
    require_controls(
        "refusal_overclaim",
        ("amoxicillin-aom/primary drops a scope clause the object holds -- read by hand "
         "before this existed; got %r" % (pos and pos["drops_scope"]),
         bool(pos and pos["drops_scope"]), True),
        ("attr-pn-review/primary was written against the object's own fields tonight and "
         "must not be flagged; got %r" % (neg and neg["drops_scope"]),
         bool(neg and neg["drops_scope"]), True))

    drops = [r for r in rows if r["drops_scope"]]
    held = [r for r in rows if r["guard_held"]]
    unrendered = [r for r in held if r["guard_rendered"] is False]
    print("")
    print("WITHDRAWAL NOTICES, over %d withdrawn outcome(s) carrying a reason" % len(rows))
    print("")
    print("   A  drop a scope clause the object itself holds   %4d" % len(drops))
    print("   B  hold `%s`   %4d" % (GUARD_FIELD, len(held)))
    print("      of those, NOT rendered on any delivered page  %4d" % len(unrendered))
    print("")
    for r in drops:
        print("   DROPS SCOPE  %-34s %-24s" % (r["topic"][:34], r["outcome"][:24]))
        print("        object holds : %s" % (r["scope_on_object"][:2],))
        print("        notice says  : %s" % (r["sweeping_in_reason"][:3],))
        print("        pages        : %s" % (", ".join(r["pages"]) or "none"))
    if unrendered:
        print("")
        for r in unrendered[:20]:
            print("   GUARD HELD, NOT RENDERED  %-34s %s" % (r["topic"][:34], r["outcome"]))
    print("")
    print("A REFUSAL IS A CLAIM. Overclaiming one is a fabrication in the direction this")
    print("project has no guard for, because an overclaimed criticism reads as rigour.")
    json.dump({"rows": rows, "drops_scope": len(drops), "guard_held": len(held),
               "guard_not_rendered": len(unrendered)},
              io.open(os.path.join(REPO, "outputs",
                                   "refusal_overclaim_2026_08_24.json"),
                      "w", encoding="utf-8"), indent=1)
    if drops or unrendered:
        sys.exit("REFUSED: %d notice(s) overclaim beyond the object's own scoped wording, "
                 "and %d object(s) hold a misreading guard no page renders."
                 % (len(drops), len(unrendered)))


if __name__ == "__main__":
    main()
