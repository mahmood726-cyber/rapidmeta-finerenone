"""Two confirmed trial-name swaps: the NCTs are right, the NAMES are on the wrong trials.

WHICH SIDE IS WRONG IS ESTABLISHED, NOT ASSUMED. The agyw object states its own enrolments --
"ASPIRE / MTN-020 1959 v 1952; The Ring Study 2629 v 2626" -- and the registry says
NCT01539226 enrolled 1959 while NCT01617096 (acronym ASPIRE, read from the registry) enrolled
2629. So the object groups NCT01539226 with n=1959 correctly and calls it ASPIRE, which is the
other trial. The registration and the count travel together; only the NAME is misplaced.

    NCT01539226   is  The Ring Study      (n=1959)   -- object called it ASPIRE / MTN-020
    NCT01617096   is  ASPIRE / MTN-020    (n=2629)   -- object called it The Ring Study
    NCT00621504   is  FOCUS 1             (n=606)    -- object called it FOCUS 2
    NCT00509106   is  FOCUS 2             (n=622)    -- object called it FOCUS 1

THE CEFTAROLINE PAIR IS WEAKER EVIDENCE AND IS RECORDED AS SUCH. Both registrations carry
acronym "CAP" and the same brief title, so the REGISTRY CANNOT SEPARATE FOCUS 1 FROM FOCUS 2.
That mapping rests on the published trial reports and on the enrolment ordering (606 against
622), not on anything this repository can re-derive. It is applied because it was confirmed
upstream, and this note exists so nobody later mistakes it for a registry-verified fact.

NOTHING NUMERIC MOVES. Every per-trial row, effect and pooled estimate is keyed by NCT and is
untouched; a fingerprint is compared before and after. This repairs display names only.

WHY THIS MATTERS MORE THAN A COSMETIC LABEL. Both pages are in the READY index. A reader
following the reference list lands on the wrong registration for the trial they just read
about -- and the two trials have different populations, different countries and different
sizes.
"""
import io
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "outputs", "trial_name_swaps_2026_08_28.json")

TRUE_NAME = {
    "NCT01539226": ("The Ring Study", "registry n=1959 matches the object's own stated "
                                      "enrolment for this registration"),
    "NCT01617096": ("ASPIRE / MTN-020", "registry acronym is literally ASPIRE, n=2629"),
    "NCT00621504": ("FOCUS 1", "NOT registry-separable -- both ceftaroline registrations "
                               "carry acronym CAP; from the published reports and the "
                               "enrolment ordering (606)"),
    "NCT00509106": ("FOCUS 2", "NOT registry-separable -- see NCT00621504; enrolment 622"),
}

PROSE_FIXES = [
    ("ssot/agyw-hiv-prep-review/agyw-hiv-prep-review.json",
     "ASPIRE / MTN-020 1959 v 1952; The Ring Study 2629 v 2626",
     "The Ring Study 1959 v 1952; ASPIRE / MTN-020 2629 v 2626"),
    ("ssot/agyw-hiv-prep-review/agyw-hiv-prep-review.json",
     "ASPIRE ran in South Africa and Uganda; The Ring Study ran in Malawi, South Africa, "
     "Uganda and Zimbabwe.",
     "The Ring Study ran in South Africa and Uganda; ASPIRE ran in Malawi, South Africa, "
     "Uganda and Zimbabwe."),
]

OBJECTS = ["ssot/agyw-hiv-prep-review/agyw-hiv-prep-review.json",
           "ssot/ceftaroline-auto-full-review/ceftaroline-auto-full-review.json"]

OLD_NAMES = set(["ASPIRE / MTN-020", "The Ring Study", "FOCUS 1", "FOCUS 2"])


def fingerprint(obj):
    """Every number a reader could quote, so the repair can prove it moved none."""
    out = []
    for oid, blk in sorted(((obj.get("results") or {}).get("by_outcome") or {}).items()):
        if not isinstance(blk, dict):
            continue
        out.append((oid, (blk.get("pooled") or {}).get("point"),
                    [(r.get("nct"), r.get("point"), r.get("ci_low"), r.get("ci_high"))
                     for r in (blk.get("per_trial") or [])]))
    return json.dumps(out, sort_keys=True)


def relabel(node, nct_in_scope, changes, apply_):
    """Rewrite a `label`/`trial` field that sits beside a known NCT."""
    if not isinstance(node, dict):
        return
    nct = node.get("nct") or node.get("registration") or nct_in_scope
    for key in ("label", "trial", "name"):
        val = node.get(key)
        if not isinstance(val, str) or val not in OLD_NAMES:
            continue
        if nct not in TRUE_NAME:
            continue
        correct = TRUE_NAME[nct][0]
        if val == correct:
            continue
        changes.append({"nct": nct, "field": key, "from": val, "to": correct})
        if apply_:
            node[key] = correct


def walk(node, changes, apply_, nct_in_scope=None):
    if isinstance(node, dict):
        here = node.get("nct") or node.get("registration") or nct_in_scope
        relabel(node, here, changes, apply_)
        for k, v in node.items():
            # a dict keyed BY the nct (risk_of_bias.by_outcome.primary.NCT01539226)
            walk(v, changes, apply_, k if k in TRUE_NAME else here)
    elif isinstance(node, list):
        for v in node:
            walk(v, changes, apply_, nct_in_scope)


def main():
    apply_ = "--apply" in sys.argv
    raw = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                           write_through=True)

    def say(s):
        raw.write(s + chr(10))
        raw.flush()

    all_changes, prose_done, refusals = [], [], []

    for rel in OBJECTS:
        path = os.path.join(REPO, rel)
        obj = json.load(io.open(path, encoding="utf-8"))
        before = fingerprint(obj)
        changes = []
        walk(obj, changes, apply_)

        text = json.dumps(obj, ensure_ascii=False)
        for prel, old, new in PROSE_FIXES:
            if prel != rel:
                continue
            if old in text:
                text = text.replace(old, new)
                prose_done.append({"object": rel, "from": old[:70], "to": new[:70]})
            else:
                refusals.append((rel, "prose target not found: %r" % old[:60]))
        obj = json.loads(text)

        after = fingerprint(obj)
        if after != before:
            refusals.append((rel, "A NUMBER MOVED -- refusing"))
            continue
        all_changes.extend([dict(c, object=rel) for c in changes])
        if apply_:
            io.open(path, "w", encoding="utf-8").write(
                json.dumps(obj, indent=1, ensure_ascii=False))

    say("LABEL FIELDS REPAIRED: %d" % len(all_changes))
    for c in all_changes:
        say("   %-12s %-6s %-20r -> %r" % (c["nct"], c["field"], c["from"], c["to"]))
    say("")
    say("PROSE SENTENCES REPAIRED: %d" % len(prose_done))
    for p in prose_done:
        say("   %s" % p["from"])
        say("      -> %s" % p["to"])
    say("")
    say("estimates moved: 0 (asserted by fingerprint)")
    say("refusals: %d" % len(refusals))
    for r, why in refusals:
        say("   %-40s %s" % (r[:40], why))
    say("")
    for nct, (name, why) in sorted(TRUE_NAME.items()):
        say("   %-12s -> %-18s  %s" % (nct, name, why))

    if refusals:
        return 2
    if not apply_:
        say("")
        say("(dry run -- nothing written; pass --apply)")
        return 0
    json.dump({"true_names": {k: {"name": v[0], "basis": v[1]}
                              for k, v in TRUE_NAME.items()},
               "label_changes": all_changes, "prose_changes": prose_done,
               "numbers_changed": 0,
               "caveat": "the ceftaroline FOCUS 1/2 mapping is NOT registry-separable -- both "
                         "registrations carry acronym CAP -- and rests on the published "
                         "reports and enrolment ordering"},
              io.open(OUT, "w", encoding="utf-8"), indent=1)
    say("wrote %s" % os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    sys.exit(main())
