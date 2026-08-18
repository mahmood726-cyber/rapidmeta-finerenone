"""What does the generator actually read, and in what shape? Derived from the consumer.

THE PROBLEM THIS ENDS. Building AZILSARTAN took four cycles: build, fail on one field, fix
it, rebuild, fail on the next. Three shape defects on one object, discovered one per build,
at ninety seconds a build because the generator rasterises through a browser.

AND AN EARLIER CHECK ONLY GOT HALFWAY. `buildability_check.py` reads BRACKET ACCESSES on
the canonical root -- `canon["outcomes"]` -- and predicted 4 of 8 blockers on the first
real build. It could not see requirements nested inside per-trial structures, which is
where the other four were. THIS IS THAT MOVE ONE LEVEL DEEPER.

THE SOURCE OF TRUTH IS THE CONSUMER, NOT THE OBJECTS. A field name appearing in two
plausible places on an object does not say which one is read; only the code that reads it
does. `provenance` sits on the object root, on `inputs.trials[]`, and on
`inputs.trials[].by_outcome[oid]` -- and the generator reads the third. Two guesses were
wrong before one read settled it.

WHAT IT EXTRACTS, per accessing expression:
  REQUIRED   `x["field"]`            -- raises when absent
  OPTIONAL   `x.get("field")`        -- tolerated
  SHAPE      `x["field"].get(...)`   -- must be a MAPPING
             `x["field"]` iterated / `or []`  -- must be a SEQUENCE
             A SHAPE THE CONSUMER CANNOT READ IS THE SAME DEFECT AS A FIELD IT CANNOT FIND,
             and AZILSARTAN carried both: provenance in the wrong place, and
             eligible_but_not_contributing as a list where a mapping is read.

IT REPORTS, IT DOES NOT PATCH. A field's correct VALUE is never derivable from the code
that consumes it -- only its presence and shape are. Writing a value to satisfy a consumer
is the defaulted-field lie this project has refused all week.
"""
from __future__ import annotations
import io
import os
import re
import sys

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEN = ["ssot/build_app_v2.py", "ssot/build_tabbed.py", "ssot/projectors.py"]

# A FIELD NAME IS NOT AN ADDRESS. `provenance` exists on the object root, on
# inputs.trials[], and on inputs.trials[].by_outcome[oid] -- and the generator reads
# exactly one of them. Two careful guesses both failed before one read settled it. THE
# STRUCTURE IS THE IDENTITY; THE NAME IS A LABEL ON IT. So every reported field names the
# structure it hangs off, and the ambiguity disappears.
BINDING = {
    "canon": "the CANONICAL OBJECT ROOT",
    "o":     "an entry of canon['outcomes']",
    "t":     "an entry of canon['inputs']['trials']",
    "d":     "t['by_outcome'][outcome_id] -- PER-TRIAL, PER-OUTCOME",
    "blk":   "an analysis block under results.by_outcome",
    "res":   "an analysis block under results.by_outcome",
    "pooled": "blk['pooled']",
    "het":   "blk['heterogeneity']",
    "outcome": "an entry of canon['outcomes']",
    "prov":  "d['provenance']",
    "eff":   "a per-trial effect record",
}

# x["field"] -- raises if absent
HARD = re.compile(r"\b([a-z_][a-z_0-9]*)\[[\"']([a-z_0-9]+)[\"']\]")
# x["field"].get(  -- must be a mapping
MAPPING = re.compile(r"\b([a-z_][a-z_0-9]*)\[[\"']([a-z_0-9]+)[\"']\]\s*\.\s*get\s*\(")
# x.get("field") or []  /  for y in x.get("field")  -- must be a sequence
SEQUENCE = re.compile(
    r"\b([a-z_][a-z_0-9]*)\s*\.\s*get\s*\(\s*[\"']([a-z_0-9]+)[\"']\s*\)\s*or\s*\[\]")
SOFT = re.compile(r"\b([a-z_][a-z_0-9]*)\s*\.\s*get\s*\(\s*[\"']([a-z_0-9]+)[\"']")


def main() -> int:
    hard, mapping, seq, soft = {}, {}, {}, {}
    for rel in GEN:
        p = os.path.join(REPO, rel)
        if not os.path.exists(p):
            continue
        t = io.open(p, encoding="utf-8", errors="replace").read()
        for rx, bucket in ((HARD, hard), (MAPPING, mapping),
                           (SEQUENCE, seq), (SOFT, soft)):
            for m in rx.finditer(t):
                bucket.setdefault((m.group(1), m.group(2)), set()).add(rel)

    print("CONSUMER-DERIVED SCHEMA -- what the generator reads, from the code that reads it")
    print()
    print("=== REQUIRED (bracket access -- ABSENT MEANS KeyError): %d" % len(hard))
    byvar = {}
    for (var, fld), where in hard.items():
        byvar.setdefault(var, []).append(fld)
    for var in sorted(byvar):
        where = BINDING.get(var)
        print("    %-10s %s" % (var, ", ".join(sorted(set(byvar[var])))[:88]))
        if where:
            print("               ^ %s" % where)
    print()
    print("=== MUST BE A MAPPING (x['f'].get(...) -- a LIST here raises): %d" % len(mapping))
    for (var, fld) in sorted(mapping):
        print("    %s[%r]   on %s" % (var, fld, BINDING.get(var, "(binding not recorded)")))
    print()
    print("=== MUST BE A SEQUENCE (x.get('f') or [] then iterated): %d" % len(seq))
    bys = {}
    for (var, fld) in seq:
        bys.setdefault(var, []).append(fld)
    for var in sorted(bys):
        print("    %-12s %s" % (var, ", ".join(sorted(set(bys[var])))[:96]))
    print()
    print("=== OPTIONAL (.get, tolerated absent): %d distinct" % len(soft))
    print()
    print("THE VARIABLE NAME IS THE STRUCTURE. `canon` is the object root; `t` is an entry")
    print("of inputs.trials[]; `d` is t['by_outcome'][oid]; `blk` is an analysis block.")
    print("A FIELD NAME ALONE DOES NOT SAY WHERE IT IS READ -- provenance appears on three")
    print("structures in this corpus and the generator reads exactly one of them.")
    print()
    print("REPORTS ONLY. A field's correct VALUE is never derivable from the code that")
    print("consumes it -- only its presence and shape. Writing a value to satisfy a")
    print("consumer is the defaulted-field lie.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
