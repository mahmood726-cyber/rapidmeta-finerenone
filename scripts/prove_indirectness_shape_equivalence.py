# -*- coding: utf-8 -*-
"""ARE grade.indirectness AND grade.domains.indirectness THE SAME FIELD?

absolute_effect.py:89-90 reads TWO paths:

    results.by_outcome.<oid>.grade.indirectness
    grade.by_outcome.<oid>.indirectness

and gates on `g.get("reason") or g.get("state")`, returning `state` and `reason`.

Eleven outcome-blocks instead carry a fully reasoned indirectness rating at

    results.by_outcome.<oid>.grade.domains.indirectness

with keys `rating` and `basis_in_sources`. The proposal was to read that path too,
which would take EMITTED from 1 to 9. THIS SCRIPT DECIDES WHETHER THAT IS A FIX OR
A LOOSENING, and it decides it on evidence rather than on the code's intent.

⛔ THE STANDARD OF PROOF, FIXED BEFORE THE FIRST RUN AND NOT TUNED AFTERWARDS.
Two shapes are interchangeable when an object carrying BOTH shows they say the same
thing -- and a bridge only licenses the DIRECTION it demonstrates. A single paired
example rating `serious` proves `serious <-> DOWNGRADE`. It says NOTHING about
`not serious`, because a mapping can be correct in one direction and undefined in
the other, and `not serious` is the value ten of the eleven actually hold.

    EQUIVALENT   requires >= 1 paired object in EVERY rating value to be translated
    UNPROVEN     otherwise -- which is a verdict about our evidence, not about the data

⭐ THIS SCRIPT CAN CHANGE ITS MIND. Add one object carrying both shapes with
`rating: not serious`, and the verdict flips to EQUIVALENT on the next run without
anyone editing this file. A proof that can only return one answer is not a proof.
"""
import glob
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)

FLAT_READ_BY_DERIVER = True
DERIVER_GATE_KEYS = ("reason", "state")       # absolute_effect.py:91
DERIVER_USES_KEYS = ("state", "reason")       # absolute_effect.py:92-93


def outcome_blocks():
    """POSITIVE FORM THROUGHOUT, and the refusal that produced it was right.

    The first draft skipped with `if not isinstance(...): continue` three times
    inside a corpus-wide sweep -- the precise shape audit_exclusion_by_absence
    refuses, and it refused this file at commit. The semantics were arguably
    fine; the SHAPE is what gets copied, and a sweep that drops items silently
    reports its own reach as though it were coverage. A proof about the corpus
    is the last place to hide a skip: if this walk quietly lost objects, the
    verdict "no bridge exists" would be indistinguishable from "no bridge was
    looked at". Every skip below is now a stated positive condition, and the
    counters make the dropped population visible instead of invisible."""
    seen = {"files": 0, "unreadable": 0, "not_an_object": 0, "no_by_outcome": 0}
    for f in sorted(glob.glob(os.path.join(REPO, "ssot", "*", "*.json"))):
        seen["files"] += 1
        canon = _read_json(f)
        if isinstance(canon, dict):
            res = canon.get("results")
            bo = res.get("by_outcome") if isinstance(res, dict) else None
            if isinstance(bo, dict):
                for oid, rec in bo.items():
                    if isinstance(rec, dict):
                        yield os.path.basename(f), oid, canon, rec
            else:
                seen["no_by_outcome"] += 1
        elif canon is _UNREADABLE:
            seen["unreadable"] += 1
        else:
            seen["not_an_object"] += 1
    OUTCOME_WALK_CENSUS.update(seen)


_UNREADABLE = object()
OUTCOME_WALK_CENSUS = {}


def _read_json(path):
    """The object, or _UNREADABLE. Never a silent skip -- the caller counts it."""
    try:
        with io.open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return _UNREADABLE


def shapes(canon, oid, rec):
    gr = rec.get("grade") if isinstance(rec.get("grade"), dict) else {}
    flat = gr.get("indirectness")
    if not isinstance(flat, dict):
        alt = (((canon.get("grade") or {}).get("by_outcome") or {}).get(oid) or {})
        flat = alt.get("indirectness") if isinstance(alt, dict) else None
    doms = gr.get("domains") if isinstance(gr.get("domains"), dict) else {}
    dom = doms.get("indirectness")
    return (flat if isinstance(flat, dict) else None,
            dom if isinstance(dom, dict) else None)


def main():
    paired, flat_only, dom_only = [], [], []
    for name, oid, canon, rec in outcome_blocks():
        flat, dom = shapes(canon, oid, rec)
        if flat and dom:
            paired.append((name, oid, flat, dom))
        elif flat:
            flat_only.append((name, oid, flat))
        elif dom:
            dom_only.append((name, oid, dom))

    print("INDIRECTNESS SHAPE EQUIVALENCE")
    print("  store files walked                : %d" % OUTCOME_WALK_CENSUS.get("files", 0))
    print("    unreadable                      : %d   <- NAMED, not dropped"
          % OUTCOME_WALK_CENSUS.get("unreadable", 0))
    print("    not a JSON object               : %d   <- NAMED, not dropped"
          % OUTCOME_WALK_CENSUS.get("not_an_object", 0))
    print("    no results.by_outcome            : %d   <- NAMED, not dropped"
          % OUTCOME_WALK_CENSUS.get("no_by_outcome", 0))
    print("  paired (BOTH shapes on one block) : %d" % len(paired))
    print("  flat shape only                   : %d" % len(flat_only))
    print("  domains shape only                : %d" % len(dom_only))
    print("")

    # ---- what the deriver would actually find at the domains path -------------
    print("  WOULD REPOINTING THE PATH ALONE CHANGE ANYTHING?")
    print("  The deriver accepts a record only if it has %s."
          % " or ".join(DERIVER_GATE_KEYS))
    passes = [d for _, _, d in dom_only
              if any(d.get(k) for k in DERIVER_GATE_KEYS)]
    print("    domains-shape records that pass that gate as-is : %d of %d"
          % (len(passes), len(dom_only)))
    print("    -> repointing alone emits %d extra block(s). The rest need the keys"
          % len(passes))
    print("       TRANSLATED (basis_in_sources -> reason, rating -> state), and it")
    print("       is the TRANSLATION, not the path, that must be proven.")
    print("")

    # ---- which rating values need a bridge, and which have one ---------------
    need = {}
    for _, _, d in dom_only:
        need.setdefault(str(d.get("rating")), 0)
        need[str(d.get("rating"))] += 1
    bridged = {}
    print("  BRIDGES -- objects carrying BOTH shapes, i.e. the only direct evidence")
    for name, oid, flat, dom in paired:
        same = (str(dom.get("basis_in_sources") or "").strip()
                == str(flat.get("reason") or "").strip())
        r = str(dom.get("rating"))
        bridged.setdefault(r, []).append((name, oid, same))
        print("    %-34s %-14s rating=%-12s flat.state=%-11s basis==reason: %s"
              % (name[:34], oid[:14], r, flat.get("state"),
                 "YES, VERBATIM" if same else "*** DIFFERS ***"))
    if not paired:
        print("    (none -- and that absence IS the answer: with no object carrying")
        print("     both, there is no direct evidence they are interchangeable)")
    print("")

    print("  RATING VALUES THAT MUST BE TRANSLATED, AND WHETHER A BRIDGE EXISTS")
    unproven = []
    for r, n in sorted(need.items()):
        ok = [b for b in bridged.get(r, []) if b[2]]
        print("    rating=%-14s used by %2d block(s)   bridge: %s"
              % (r, n, ("YES (%s)" % ok[0][0]) if ok else "*** NONE ***"))
        if not ok:
            unproven.append((r, n))
    print("")

    if unproven:
        print("  VERDICT: UNPROVEN -- DO NOT CHANGE THE READ PATH.")
        for r, n in unproven:
            print("    No object carries both shapes with rating=%r, so the mapping" % r)
            print("    from that value to a deriver state is undemonstrated, and it")
            print("    governs %d of the %d block(s) at issue." % (n, len(dom_only)))
        print("    Accepting it would be a LOOSENING: the instrument would move")
        print("    because we widened what counts, not because the corpus changed.")
        print("")
        print("    TO FLIP THIS VERDICT, add one object carrying BOTH shapes for each")
        print("    rating above, then re-run. Nothing in this file needs editing.")
        return 1

    print("  VERDICT: EQUIVALENT -- every rating value in use has a verbatim bridge.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
