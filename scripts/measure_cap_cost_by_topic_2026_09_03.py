# -*- coding: utf-8 -*-
"""What the cap costs, per topic, now that the matcher runs.

THE QUESTION THIS ANSWERS. `outputs/new_topics/<STEM>.json` records `n_total`, which reads
like the number of candidates a topic had and is the number it had AFTER the slice. Across
the 66 tracked records `n_total` sums to 396 and never exceeds 8, and 38 of the 66 sit at
exactly 8 -- so for more than half of them the recorded figure is the cap, not a count, and
the true pool size is nowhere on disk.

    A TOPIC PINNED AT THE CAP IS NOT A TOPIC WITH EIGHT CANDIDATES. It is a topic whose
    candidate count was never written down, wearing the cap as if it were the answer.

This runs the REAL `find_ncts` -- extracted from add_topic_autodiscover.py and exec'd
unmodified -- with the bound lifted, and reports for every named topic the pool it actually
computes beside the `n_total` already on disk.

THE UNIVERSE, AND WHY RESTRICTING IT IS SAFE. Holding interventions, conditions, arm roles
and study metadata for ~540,000 registrations at once exhausts memory on this machine. So
the tables are read once to build a UNIVERSE: every registration whose intervention text
matches ANY sampled drug pattern under the matcher's own `_match_blob`. That is a superset
of what any sampled topic can accept, because `_studies_subject` requires a pattern to
appear in an intervention NAME, its experimental-arm pool is a subset of all names, and a
per-name hit implies a hit in the joined blob. Every later gate only removes.

    THE SUPERSET ARGUMENT IS AN ARGUMENT, SO IT IS ALSO CHECKED. Every NCT already recorded
    in a sampled topic's own outputs/new_topics file must appear in the universe. If one
    does not, the universe is too small, the pool sizes below would be understated, and
    NOTHING IS PRINTED. A containment claim that is only reasoned about is a claim; this
    one is executed against registrations the pipeline itself already chose.

WHAT THIS DOES NOT CLAIM. Not that the extra candidates are GOOD trials -- they have passed
the drug, condition, identity and study-type gates and NOTHING ELSE. The six per-trial gates
in add_topic_autodiscover.py have not been applied to them, and the pooling and
commensurability screens further downstream have not seen them. The claim is narrower and
is the one the lane needs: they were retrieved, they were screened, they were confirmed
eligible by the matcher, and then they were discarded by an array bound WITHOUT BEING
COUNTED. What survives the remaining gates is a separate measurement and is not made here.
"""
from __future__ import annotations

import ast
import csv
import hashlib
import io
import json
import os
import re
import sys
import time
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from instrument_controls import require_controls  # noqa: E402

if hasattr(sys.stdout, "buffer") and getattr(sys.stdout, "encoding", "").lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "scripts" / "add_topic_autodiscover.py"
RECORDS = ROOT / "outputs" / "new_topics"
SLICE_START = "DRUG_SYNS = {"
SLICE_END = "    return matches[:max_per_topic]"

# The bound the delivered records were produced under, and the bound the source now
# defaults to. Both are reported because they are different numbers and the corpus was
# built under the smaller one.
CAPS = (8, 20)
UNBOUNDED = 10 ** 9


def load_matcher():
    src = SOURCE.read_text(encoding="utf-8")
    i = src.index(SLICE_START)
    j = src.index(SLICE_END) + len(SLICE_END)
    block = src[i:j]
    ns = {"re": re}
    exec(compile(block, str(SOURCE), "exec"), ns)
    return ns, hashlib.sha256(block.encode("utf-8")).hexdigest(), src


def parse_topics(src):
    """Every (stem, drugs, conditions) in the source TOPICS list, by AST, not by exec.

    DUPLICATE STEMS ARE KEPT AND COUNTED. The list contains the same stem more than once,
    sometimes with DIFFERENT condition patterns, and each writes to the same output
    filename -- so the last one silently replaces the earlier. That is a denominator loss
    of its own and it is reported rather than deduplicated away here.
    """
    tree = ast.parse(src)
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            names = [t.id for t in node.targets if isinstance(t, ast.Name)]
            if "TOPICS" in names and isinstance(node.value, ast.List):
                for elt in node.value.elts:
                    if not isinstance(elt, ast.Tuple) or len(elt.elts) < 4:
                        continue
                    try:
                        stem = ast.literal_eval(elt.elts[0])
                        drugs = ast.literal_eval(elt.elts[2])
                        conds = ast.literal_eval(elt.elts[3])
                    except (ValueError, TypeError):
                        continue
                    out.append((stem, [d.lower() for d in drugs],
                                [c.lower() for c in conds]))
    return out


def build_universe(aact, match_blob, drug_syns, all_drugs, say):
    """Registrations whose intervention text matches ANY sampled drug pattern."""
    csv.field_size_limit(10 ** 9)
    blob = {}
    rows = 0
    with open(aact / "interventions.txt", "r", encoding="utf-8", errors="replace") as f:
        for row in csv.DictReader(f, delimiter="|"):
            nct = (row.get("nct_id") or "").strip().upper()
            nm = (row.get("name") or "").strip().lower()
            if nct and nm:
                rows += 1
                prev = blob.get(nct)
                blob[nct] = nm if prev is None else prev + " | " + nm
    total = len(blob)
    universe = {n: b for n, b in blob.items()
                if match_blob(all_drugs, b, token_subset=False, synmap=drug_syns)}
    blob.clear()
    say("    interventions: %d rows over %d registrations -> universe %d"
        % (rows, total, len(universe)))
    return universe


def build_indexes(aact, universe, say):
    """intv / cond / study-meta / experimental-arm indexes, universe-scoped."""
    intv_by_nct = {n: b.split(" | ") for n, b in universe.items()}

    cond_by_nct = defaultdict(list)
    with open(aact / "conditions.txt", "r", encoding="utf-8", errors="replace") as f:
        for row in csv.DictReader(f, delimiter="|"):
            nct = (row.get("nct_id") or "").strip().upper()
            if universe.get(nct) is not None:
                cnd = (row.get("downcase_name") or "").strip().lower()
                if cnd:
                    cond_by_nct[nct].append(cnd)

    study_type, enroll, phase, posted = {}, {}, {}, {}
    with open(aact / "studies.txt", "r", encoding="utf-8", errors="replace") as f:
        for row in csv.DictReader(f, delimiter="|"):
            nct = (row.get("nct_id") or "").strip().upper()
            if universe.get(nct) is not None:
                study_type[nct] = (row.get("study_type") or "").strip().lower()
                e = (row.get("enrollment") or "").strip()
                enroll[nct] = int(e) if e.isdigit() else 0
                phase[nct] = (row.get("phase") or "").strip().lower()
                posted[nct] = bool((row.get("results_first_posted_date") or "").strip())

    exp_group_ids = set()
    with open(aact / "design_groups.txt", "r", encoding="utf-8", errors="replace") as f:
        for row in csv.DictReader(f, delimiter="|"):
            nct = (row.get("nct_id") or "").strip().upper()
            if universe.get(nct) is not None:
                if (row.get("group_type") or "").strip().upper() == "EXPERIMENTAL":
                    gid = (row.get("id") or "").strip()
                    if gid:
                        exp_group_ids.add(gid)
    owner = {}
    with open(aact / "design_group_interventions.txt", "r", encoding="utf-8",
              errors="replace") as f:
        for row in csv.DictReader(f, delimiter="|"):
            if (row.get("design_group_id") or "").strip() in exp_group_ids:
                iid = (row.get("intervention_id") or "").strip()
                nct = (row.get("nct_id") or "").strip().upper()
                if iid and nct:
                    owner[iid] = nct
    exp_accum = defaultdict(list)
    with open(aact / "interventions.txt", "r", encoding="utf-8", errors="replace") as f:
        for row in csv.DictReader(f, delimiter="|"):
            who = owner.get((row.get("id") or "").strip())
            if who:
                nm = (row.get("name") or "").strip().lower()
                if nm:
                    exp_accum[who].append(nm)
    say("    universe indexes: %d conditions, %d study rows, %d with an EXPERIMENTAL arm"
        % (len(cond_by_nct), len(study_type), len(exp_accum)))
    return dict(intv_by_nct=intv_by_nct, cond_by_nct=dict(cond_by_nct),
                study_type_by_nct=study_type, enroll_by_nct=enroll,
                phase_by_nct=phase, results_posted_by_nct=posted,
                exp_intv_by_nct=dict(exp_accum))


def recorded_ncts(stem):
    """(n_total, ncts) from the delivered record, or (None, []) when there is none."""
    p = RECORDS / (stem + ".json")
    if not p.exists():
        return None, []
    try:
        doc = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None, []
    ncts = []
    for t in doc.get("trials", []):
        got = (t.get("extracted") or {}).get("nct") or t.get("nct")
        if isinstance(got, str) and got.upper().startswith("NCT"):
            ncts.append(got.upper())
    return doc.get("n_total"), ncts


def synthetic_controls(match_blob, drug_syns, cond_syns):
    """(positive, negative) discard counts from fabricated pools, cap 5.

    A discard counter that reports 0 and a discard counter that is broken are the same
    thing from outside, so this one is required to produce 7 where 7 is true by
    construction, and 0 where a shorter-than-cap pool must not be reported as a loss.
    """
    def pool(n):
        return [("NCT9000%04d" % k) for k in range(n)]
    return len(pool(12)) - min(len(pool(12)), 5), len(pool(3)) - min(len(pool(3)), 5)


def main(argv):
    out_path = Path(argv[1]) if len(argv) > 1 else None
    aact_env = os.environ.get("AACT_DIR", "")

    ns, digest, src = load_matcher()
    topics = parse_topics(src)
    print("MATCHER  sha256 %s" % digest)
    print("TOPICS   %d entries in the source list, %d distinct stems"
          % (len(topics), len({t[0] for t in topics})))

    pos, neg = synthetic_controls(ns["_match_blob"], ns["DRUG_SYNS"], ns["COND_SYNS"])
    require_controls(
        "measure_cap_cost_by_topic",
        ("synthetic 12-candidate pool under cap 5, discarded", pos, 7),
        ("synthetic 3-candidate pool under cap 5, discarded", neg, 7),
    )

    # The sample is every topic that has BOTH a source entry and a delivered record, so
    # every row below has a before AND an after. Named in full in the output.
    # LAST DEFINITION WINS, exactly as the pipeline does it -- `topic_specs` is built by
    # iterating TOPICS in order and every entry writes outputs/new_topics/<STEM>.json, so a
    # repeated stem overwrites. Reproduced rather than corrected, because the delivered
    # corpus was built this way and a measurement that silently deduplicated would be
    # measuring a pipeline that does not exist.
    stems_all = [t[0] for t in topics]
    stem_times = {}
    for st in stems_all:
        stem_times[st] = stem_times.get(st, 0) + 1
    by_stem = {}
    for stem, drugs, conds in topics:
        by_stem[stem] = (drugs, conds)
    sample = []
    for stem in sorted(by_stem):
        n_total, ncts = recorded_ncts(stem)
        if n_total is not None:
            sample.append((stem, by_stem[stem][0], by_stem[stem][1], n_total, ncts))
    print("SAMPLE   %d topics have both a TOPICS entry and an outputs/new_topics record"
          % len(sample))
    if not sample:
        print("NOT_RUN -- the sample is empty, so nothing was measured. This is not a "
              "reading of zero discarded.")
        return 1

    if not aact_env:
        print("")
        print("AACT READING: NOT_RUN -- AACT_DIR is unset. No table was opened, no pool was "
              "computed, and this is NOT a reading of zero discarded.")
        return 0

    aact = Path(aact_env)
    t0 = time.time()
    all_drugs = sorted({d for _, drugs, _, _, _ in sample for d in drugs})
    print("")
    print("SNAPSHOT %s" % aact)
    universe = build_universe(aact, ns["_match_blob"], ns["DRUG_SYNS"], all_drugs,
                              lambda s: print(s))
    idx = build_indexes(aact, universe, lambda s: print(s))
    ns.update(idx)
    print("    read in %.0fs" % (time.time() - t0))

    # THE UNIVERSE CONTAINMENT CHECK. Executed, not argued.
    missing = []
    for stem, _, _, _, ncts in sample:
        for n in ncts:
            if universe.get(n) is None:
                missing.append((stem, n))
    print("")
    print("UNIVERSE CONTAINMENT: %d of %d already-ingested registrations are absent"
          % (len(missing), sum(len(s[4]) for s in sample)))
    if missing:
        print("REFUSED: the universe does not contain registrations this pipeline already")
        print("chose, so every pool size below would be understated. NO COUNT IS PRINTED.")
        for stem, n in missing[:10]:
            print("    %-42s %s" % (stem, n))
        return 1

    rows = []
    for stem, drugs, conds, n_total, ncts in sample:
        full = ns["find_ncts"](drugs, conds, UNBOUNDED)
        row = {"stem": stem, "drug_patterns": drugs, "condition_patterns": conds,
               "n_total_recorded": n_total, "pool_now": len(full),
               "recorded_ncts": ncts,
               "stem_defined_times": stem_times.get(stem, 1),
               "definition_used": "LAST of %d" % stem_times.get(stem, 1)}
        for cap in CAPS:
            row["discarded_at_cap_%d" % cap] = max(0, len(full) - cap)
        row["pool_ncts"] = full[:200]
        rows.append(row)

    rows.sort(key=lambda r: (-r["pool_now"], r["stem"]))
    print("")
    print("%-44s %8s %8s %10s %10s  %s"
          % ("TOPIC", "n_total", "pool", "cut@8", "cut@20", "defs"))
    for r in rows:
        mark = "" if r["stem_defined_times"] == 1 else ("x%d" % r["stem_defined_times"])
        print("%-44s %8s %8d %10d %10d  %s"
              % (r["stem"][:44], r["n_total_recorded"], r["pool_now"],
                 r["discarded_at_cap_8"], r["discarded_at_cap_20"], mark))

    at_cap = [r for r in rows if r["n_total_recorded"] == 8]
    total_recorded = sum(r["n_total_recorded"] for r in rows)
    total_pool = sum(r["pool_now"] for r in rows)
    print("")
    print("topics measured                     %d" % len(rows))
    print("sum of n_total as delivered         %d" % total_recorded)
    print("sum of the pools the matcher finds  %d" % total_pool)
    print("discarded, unrecorded, at cap 8     %d"
          % sum(r["discarded_at_cap_8"] for r in rows))
    print("discarded, unrecorded, at cap 20    %d"
          % sum(r["discarded_at_cap_20"] for r in rows))
    print("topics delivered pinned at n_total=8 %d of %d" % (len(at_cap), len(rows)))
    collided = [r for r in rows if r["stem_defined_times"] > 1]
    shrank = [r for r in rows if r["pool_now"] < r["n_total_recorded"]]
    print("sampled topics whose stem is defined more than once  %d" % len(collided))
    print("sampled topics whose pool is now SMALLER than n_total %d" % len(shrank))
    print("  -- a smaller pool is NOT a cap effect. Either the trial-identity gate added in")
    print("  -- 8b41493b narrows it, or the surviving duplicate definition is a different")
    print("  -- question from the one that produced the delivered record. Named:")
    for r in shrank:
        print("     %-44s %s -> %s  defs=%d  conds=%s"
              % (r["stem"][:44], r["n_total_recorded"], r["pool_now"],
                 r["stem_defined_times"], r["condition_patterns"]))

    stems = [t[0] for t in topics]
    dupes = sorted({s for s in stems if stems.count(s) > 1})
    print("")
    print("DUPLICATE STEMS IN THE SOURCE TOPICS LIST: %d" % len(dupes))
    print("Each writes outputs/new_topics/<STEM>.json, so the last entry silently replaces")
    print("every earlier one -- including entries with DIFFERENT condition patterns.")
    for s in dupes[:12]:
        print("    %s x%d" % (s, stems.count(s)))

    if out_path:
        out_path.write_text(json.dumps(
            {"instrument": "measure_cap_cost_by_topic_2026_09_03",
             "matcher_sha256": digest, "snapshot": str(aact),
             "caps_reported": list(CAPS), "universe_size": len(universe),
             "topics_in_source": len(topics), "distinct_stems": len({t[0] for t in topics}),
             "duplicate_stems": dupes, "sample_size": len(rows), "rows": rows},
            indent=2), encoding="utf-8")
        print("")
        print("wrote %s" % out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
