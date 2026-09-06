# -*- coding: utf-8 -*-
"""Of the 13 judgement fields, how many can be got WITHOUT a model at all?

THE CONSTRAINT THIS TESTS. A Path-B trial entry carries 29 fields. 16 are machine-derivable
from the registry and were never in question. The other 13 were called "requiring a document
or a judgement", and that phrase has been carrying a lot of weight -- it is the reason
"this cannot be a scraper" is true, and it is the stated reason to reach for a model.

    THE PHRASE WAS NEVER MEASURED. It was a reading of one trial entry, by one person, in one
    afternoon. Twice tonight a job proposed for a local model collapsed into ordinary code on
    inspection, so the prior is that this will too.

WHAT THIS MEASURES, against the ACTUAL Path-B trial set rather than an example:

    (a) PRESENT IN A STRUCTURED SOURCE NOBODY IS READING -- an AACT column that already holds
        it. No model, no parsing, a lookup.
    (b) PRESENT IN PROSE BUT DETERMINISTICALLY LOCATABLE -- a labelled cell, a named column,
        a verbatim quote with a stated provenance rule. Code, not judgement.
    (c) GENUINELY A JUDGEMENT -- a decision about whether two things are the same construct.
        Irreducible.

For each field the class is asserted with the AACT columns that would supply it, and the
COVERAGE is measured: of the trials Path B actually pools, how many have those rows? A field
is only class (a) if the column exists AND is populated for the trials we hold.

    A COLUMN THAT EXISTS AND IS EMPTY IS NOT A SOURCE. Coverage is reported per field so a
    class-(a) claim cannot rest on the column's existence alone.

WHAT THIS DOES NOT CLAIM. Not that a class-(a) field can be copied across unexamined -- the
registry's number and the paper's number disagree often enough that this project has a whole
defect class about it. Only that obtaining a CANDIDATE value needs no model. The acceptance
rule that decides whether a candidate enters the corpus is a separate mechanism and is not
built here.
"""
from __future__ import annotations

import csv
import io
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from instrument_controls import require_controls  # noqa: E402

if hasattr(sys.stdout, "buffer") and getattr(sys.stdout, "encoding", "").lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
PAGE_MAP = ROOT / "ssot" / "PAGE_MAP.json"

# The 13, each with the AACT table.column that would supply it and the class asserted BEFORE
# coverage is measured, so the measurement can contradict the assertion.
FIELDS = [
    ("id", "b", None, None,
     "a slug of `name`. Deterministic string transform, no source needed."),
    ("name", "a", "studies", ["acronym"],
     "the trial acronym, which the registry stores in its own column."),
    ("pmid", "a", "study_references", ["pmid"],
     "the registry links its own publications."),
    ("year", "a", "study_references", ["citation"],
     "the citation string carries the year; PubMed confirms it but is not required to obtain "
     "a candidate."),
    ("design", "b", "designs", ["allocation", "intervention_model", "masking"],
     "allocation + intervention_model + masking + phase compose the sentence. The PROSE is "
     "written; the FACTS are columns."),
    # CORRECTED AFTER MEASURING. This first named ["criteria", "population"] and coverage came
    # back 0.6%. `eligibilities.population` is an OBSERVATIONAL-study column, empty for
    # interventional trials, and the all-columns-filled test let one empty column zero out a
    # source that is 99.7% populated. THE FOURTH TIME IN THIS LANE AN ABSENCE WAS THE
    # INSTRUMENT. The AND is kept -- by_outcome genuinely needs a point AND both bounds -- but
    # a column list is now a claim that must itself be checked.
    ("population", "b", "eligibilities", ["criteria"],
     "the registry stores the eligibility criteria verbatim. Summarising them into one "
     "sentence is composition, not judgement."),
    ("comparator_type", "a", "design_groups", ["group_type"],
     "PLACEBO_COMPARATOR / ACTIVE_COMPARATOR / NO_INTERVENTION is a registry enum."),
    ("comparator_type_basis", "c", "design_groups", ["title", "description"],
     "THE LOAD-BEARING ONE. The arm title and description supply the raw material -- "
     "'Placebo + standard of care' -- but deciding that this makes the contrast COMMENSURABLE "
     "with another trial's is a judgement about constructs."),
    ("arms", "a", "outcome_counts", ["ctgov_group_code", "count"],
     "per-arm event counts, where results are posted."),
    ("arms_not_used", "c", None, None,
     "which arms to exclude from the pool. A decision about scope, not a fact to look up."),
    ("enrolment_note", "b", "studies", ["enrollment", "enrollment_type"],
     "randomised-versus-analysed is two numbers and a rule; the note is generated from them."),
    ("by_outcome", "a", "outcome_analyses",
     ["param_type", "param_value", "ci_lower_limit", "ci_upper_limit"],
     "the registry posts the effect estimate AND its interval for analysed outcomes."),
    ("registered_primary_timeframe_basis", "b", "design_outcomes", ["time_frame"],
     "the timeframe is a column; the 'basis' sentence states that it was quoted verbatim, "
     "which is a template, not a reading."),
]

CLASS_NAME = {"a": "(a) STRUCTURED SOURCE NOBODY READS",
              "b": "(b) PROSE, DETERMINISTICALLY LOCATABLE",
              "c": "(c) GENUINELY A JUDGEMENT"}


def path_b_trials():
    """Every NCT the Path-B objects actually pool. The real population, not an example."""
    pm = json.loads(PAGE_MAP.read_text(encoding="utf-8"))
    seen, ncts = set(), set()
    for _page, rel in sorted(pm.items()):
        if rel in seen:
            continue
        seen.add(rel)
        p = ROOT / rel
        if not p.exists():
            continue
        obj = json.loads(p.read_text(encoding="utf-8"))
        for t in (obj.get("inputs") or {}).get("trials") or []:
            n = t.get("nct")
            if isinstance(n, str) and n.upper().startswith("NCT"):
                ncts.add(n.upper())
    return ncts


def coverage(aact, table, cols, ncts, say):
    """Fraction of `ncts` with at least one row in `table` where every named column is filled."""
    p = aact / (table + ".txt")
    if not p.exists():
        say("    %-20s TABLE ABSENT" % table)
        return None, 0
    csv.field_size_limit(10 ** 9)
    wanted = {n: True for n in ncts}
    hit = set()
    rows = 0
    with open(p, "r", encoding="utf-8", errors="replace") as f:
        for row in csv.DictReader(f, delimiter="|"):
            nct = (row.get("nct_id") or "").strip().upper()
            # A DICT AND `.get`, NOT A SET AND `in`. `nct in population` reads identically
            # whether population is a set or a string, and against a string it silently
            # becomes an unanchored substring match. `.get` does not exist on str, so this
            # cannot degrade even if the population is later rebuilt as something else.
            if wanted.get(nct):
                rows += 1
                if all((row.get(c) or "").strip() for c in cols):
                    hit.add(nct)
    return len(hit), rows


def controls(ncts):
    """The population must be non-empty and must contain a trial we know Path B pools.

    POSITIVE  NCT03036124 (DAPA-HF) is in sglt2-hf's inputs.trials, read off the object.
              If the collector cannot find it, every coverage figure below is measured over
              the wrong set and none of them means anything.
    NEGATIVE  a fabricated registration must NOT be in the population -- the direction in
              which a collector that returned "everything" would look like a triumph.
    """
    return ("NCT03036124" in ncts), ("NCT99999999" in ncts)


def main(argv):
    out_path = Path(argv[1]) if len(argv) > 1 else None
    aact_env = os.environ.get("AACT_DIR", "")
    ncts = path_b_trials()
    pos, neg = controls(ncts)
    require_controls(
        "measure_extraction_depth_ceiling",
        ("DAPA-HF NCT03036124 is in the Path-B trial population", pos, True),
        ("a fabricated NCT99999999 is in the population", neg, True),
    )
    print("PATH-B TRIALS (the population every figure below is measured over): %d" % len(ncts))

    tally = defaultdict(list)
    for name, cls, _t, _c, _why in FIELDS:
        tally[cls].append(name)
    print("")
    print("CLASS ASSERTED BEFORE MEASURING, so the measurement can contradict it:")
    for c in ("a", "b", "c"):
        print("  %-38s %d of 13   %s"
              % (CLASS_NAME[c], len(tally[c]), ", ".join(tally[c])))

    if not aact_env:
        print("")
        print("COVERAGE: NOT_RUN -- AACT_DIR is unset. The classes above are ASSERTIONS until "
              "the columns are shown to be populated for these trials. This is NOT a reading "
              "of full coverage.")
        return 0

    aact = Path(aact_env)
    print("")
    print("COVERAGE against %s -- a column that exists and is EMPTY is not a source"
          % aact.name)
    print("%-36s %-4s %-22s %8s %8s" % ("FIELD", "cls", "table", "trials", "pct"))
    results = []
    for name, cls, table, cols, why in FIELDS:
        if table is None:
            print("%-36s %-4s %-22s %8s %8s" % (name[:36], cls, "-- no source needed --",
                                                "n/a", "n/a"))
            results.append({"field": name, "class": cls, "table": None,
                            "covered": None, "pct": None, "why": why})
            continue
        hit, rows = coverage(aact, table, cols, ncts, lambda s: print(s))
        pct = (100.0 * hit / max(len(ncts), 1)) if hit is not None else None
        print("%-36s %-4s %-22s %8s %7s%%"
              % (name[:36], cls, table, hit if hit is not None else "ABSENT",
                 ("%.1f" % pct) if pct is not None else "--"))
        results.append({"field": name, "class": cls, "table": table, "columns": cols,
                        "covered": hit, "of": len(ncts), "pct": round(pct, 1) if pct else 0.0,
                        "why": why})

    print("")
    print("THE ANSWER TO n OF 13:")
    for c in ("a", "b", "c"):
        names = [r["field"] for r in results if r["class"] == c]
        print("  %-38s %d of 13" % (CLASS_NAME[c], len(names)))
        for r in [x for x in results if x["class"] == c]:
            cov = ("%s%% of %d trials" % (r["pct"], r["of"])) if r.get("pct") is not None and r["table"] else "no source needed"
            print("      %-34s %s" % (r["field"], cov))
    print("")
    print("A class-(a) or class-(b) claim is only as good as its coverage column. Any field "
          "below reading 0.0%% is asserted and NOT demonstrated.")

    if out_path:
        out_path.write_text(json.dumps(
            {"instrument": "measure_extraction_depth_ceiling_2026_09_04",
             "snapshot": aact.name, "path_b_trials": len(ncts),
             "fields": results}, indent=2), encoding="utf-8")
        print("")
        print("wrote %s" % out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
