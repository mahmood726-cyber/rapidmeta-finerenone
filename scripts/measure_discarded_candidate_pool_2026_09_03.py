# -*- coding: utf-8 -*-
"""Measure the candidate pool `find_ncts` computes and then throws away.

THE DEFECT, IN ONE LINE OF ANOTHER FILE.

    scripts/add_topic_autodiscover.py:5500      return matches[:max_per_topic]

(Line 5500 at THIS commit. The same statement is at :5400 in the pre-8b41493b file and was
cited to this lane as :5420, which is neither -- so the line number is printed by the run
rather than trusted from a note, and the slice is located by its text.)

`matches` is the complete, ranked, already-screened candidate list for a topic. The slice
keeps the head and discards the tail, and NOTHING ANYWHERE RECORDS HOW LONG THE TAIL WAS.
The number is computed -- it exists, in memory, one expression before the slice -- and is
then destroyed. Downstream, `outputs/new_topics/<STEM>.json` stores `n_total`, which reads
like a denominator and is not one: it is `len(topic["ncts"])`, the count AFTER the cut.

    A REACH FIGURE RENDERED AS COVERAGE IS WORSE THAN A BLANK. A blank prompts the
    question. `n_total: 8` answers it, wrongly, and nobody asks again.

WHY THIS FILE ONLY MEASURES AND CHANGES NOTHING. The question "how much was discarded" has
never been answered for this corpus, so the size of the problem is itself unknown. Raising
a cap before measuring what the cap costs would be a guess with a number attached.

HOW THE MATCHER IS OBTAINED. Not reimplemented -- EXTRACTED. The block from `DRUG_SYNS = {`
through `return matches[:max_per_topic]` is read out of add_topic_autodiscover.py as text
and exec'd unmodified, and its sha256 is printed on every run. A reimplementation would
measure this file's idea of the matcher; the extract measures THE MATCHER. If the source
block changes, the digest changes and the reading is no longer comparable to a prior one.

THE CONTROLS ARE SYNTHETIC, AND THAT IS DELIBERATE.

    A control anchored to the live corpus RETIRES ITSELF the moment the corpus moves --
    it then either fails and looks like a regression, or passes for the wrong reason.

The positive control is a fabricated index in which the discard is known non-zero BY
CONSTRUCTION (12 eligible, cap 5, therefore exactly 7 discarded). It exists because a
discard counter reporting 0 and a discard counter that is broken are indistinguishable
from the outside, and this counter exists in order to be believed when it reports a number.
The negative control is a fabricated index whose eligible pool is SHORTER than the cap, so
a correct counter must report 0 discarded -- the direction in which this instrument would
otherwise manufacture a loss that never happened, which a positive-only control cannot see.

The real AACT reading is reported alongside, with the snapshot identified by directory and
by the size and mtime of every table read, because a count taken against an unnamed snapshot
is not reproducible and this file exists to be reproduced.

WHAT THE FIRST RUN OF THIS FILE FOUND, AND IT WAS NOT THE CAP.

    `find_ncts` DID NOT RUN AT 852b0478. It raised NameError on the first candidate it
    examined, because `_experimental_interventions` reads a global `exp_intv_by_nct` that
    was referenced once in this repository and constructed nowhere.

Measured by execution, not by reading. The identity gate arrived in 8b41493b (2026-08-25)
with the sweep that motivated it; the index it depends on did not arrive with it, and for
nine days the autodiscovery path could not return a candidate for any topic. Nothing said
so, because nothing ran it.

    A CAP CANNOT BE THE REASON A TOPIC INGESTS FIVE TRIALS IF THE FUNCTION HOLDING THE CAP
    CANNOT REACH THE CAP. The discard measured below is what the cap costs ONCE THE MATCHER
    RUNS, and that is a different claim from what it cost while the matcher was dead.

The index is now built, so `find_ncts` runs. The two questions stay separate, because they
fail separately and one of them hides the other:

    BEHAVIOURAL  `probe_matcher_operable` hands the matcher a one-row index in which every
                 gate is satisfied by construction and requires that row back. It CANNOT
                 see an index the SOURCE forgot to build, because the probe supplies it.
    STATIC       `unconstructed_globals` compares the names the matcher READS against the
                 names the source file ASSIGNS. This is the check that catches the class.
                 Against 852b0478 it returns ['exp_intv_by_nct']; against this tree, none.
                 A check that could only ever return none would not be a check.

The funnel below is still measured through the drug-pattern gate that PREDATES 8b41493b, so
its counts remain comparable to the pre-repair reading and are an UPPER BOUND on what the
trial-identity gate now passes. That gate narrows the pool further, by an amount this file
does not yet report; until it does the number is labelled UNMEASURED rather than guessed.
"""
from __future__ import annotations

import ast
import builtins
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
SLICE_START = "DRUG_SYNS = {"
# The matcher now applies its cap above the return and hands back `kept`, so the slice
# ends at that statement. The marker is a TEXT anchor, not a line number, and it moved
# once already: when the enumeration ledger landed, both instruments raised ValueError
# rather than silently measuring a shorter slice, which is the behaviour to keep.
SLICE_END = "    return kept"

# Filled by load_matcher so the static check reads the SAME bytes that were exec'd.
EXTRACT_CACHE = {}

# The tables `find_ncts` closes over. Named here so a missing one is reported as a missing
# table rather than surfacing later as an empty index and a confident zero.
TABLES = ("interventions.txt", "conditions.txt", "studies.txt")

# The class the delivered SGLT2_HF_REVIEW page pools. Five molecules, not six: bexagliflozin
# is absent from that page, and adding it moves the drug-match count without moving the
# eligible pool -- the kind of silent denominator change this file exists to expose.
SGLT2_FIVE = ["dapagliflozin", "empagliflozin", "canagliflozin",
              "sotagliflozin", "ertugliflozin"]
HEART_FAILURE = ["heart failure"]

# The five registrations that page carries, read off the page, not inferred here.
SGLT2_HF_INGESTED = ("NCT03036124", "NCT03057977", "NCT03057951",
                     "NCT03619213", "NCT03521934")


def load_matcher(source):
    """Return (namespace, digest, first_line, last_line) for the extracted matcher block."""
    src = source.read_text(encoding="utf-8")
    i = src.index(SLICE_START)
    j = src.index(SLICE_END) + len(SLICE_END)
    block = src[i:j]
    EXTRACT_CACHE["block"] = block
    EXTRACT_CACHE["source"] = src
    # `re` is a module-level import in the source file and therefore outside the extracted
    # slice. Supplying it here keeps the slice itself unmodified; rewriting the block to add
    # its own import would mean measuring an edited matcher and calling it the matcher.
    # `re` and `os` are module-level imports in the source and therefore outside the
    # extracted slice; the slice now reads os.environ for the cap. Supplying them keeps
    # the slice itself unmodified -- editing the block to add its own imports would mean
    # measuring an edited matcher and calling it the matcher.
    ns = {"re": re, "os": os}
    exec(compile(block, str(source), "exec"), ns)
    return (ns,
            hashlib.sha256(block.encode("utf-8")).hexdigest(),
            src[:i].count("\n") + 1,
            src[:j].count("\n") + 1)


def probe_matcher_operable(ns):
    """Call the extracted `find_ncts` on an index where a working matcher MUST return a row.

    Returns (operable, detail). The index has exactly one candidate and every gate is
    satisfied by construction: the drug pattern is the whole intervention name, the
    condition matches, the study type is interventional. A matcher that returns that one
    NCT is operable. A matcher that returns nothing is broken in a way a corpus run would
    report as "no candidates found" -- indistinguishable from a genuinely empty topic. A
    matcher that raises is broken in a way that never reaches a count at all.

    THIS EXISTS BECAUSE READING THE FUNCTION IS NOT RUNNING IT. The missing global here is
    visible to grep, and was not noticed by grep for nine days.

    `ns` MUST BE THE NAMESPACE THE EXTRACTED FUNCTION WAS EXEC'D INTO, not a copy of it. An
    exec'd function resolves globals through that exact dict, so injecting into a copy leaves
    the function looking at the empty original -- and the probe then reports the FIRST name
    it cannot find (`intv_by_nct`) instead of the one that is genuinely absent from the
    source (`exp_intv_by_nct`). That failure names a real-looking global that is not the
    defect, which is worse than reporting nothing. The caller passes a fresh namespace so
    the injection does not leak into the control readings.
    """
    probe = "NCT03036124"
    inject = {
        "intv_by_nct": {probe: ["dapagliflozin 10 mg"]},
        "cond_by_nct": {probe: ["heart failure"]},
        "study_type_by_nct": {probe: "interventional"},
        "enroll_by_nct": {probe: 4744},
        "phase_by_nct": {probe: "phase3"},
        "results_posted_by_nct": {probe: True},
        # The EXPERIMENTAL-arm index. Supplied here because this probe asks a BEHAVIOURAL
        # question -- given a complete index, does the matcher return the row? -- and a
        # missing index would answer a different question. Whether the SOURCE builds this
        # index is asked separately, by unconstructed_globals, which is the check that
        # catches the class rather than this one instance of it.
        "exp_intv_by_nct": {probe: ["dapagliflozin 10 mg"]},
    }
    ns.update(inject)
    try:
        got = ns["find_ncts"](["dapagliflozin"], ["heart failure"], 20)
    except NameError as exc:
        return False, "raises NameError: %s" % exc
    except Exception as exc:  # noqa: BLE001 -- the class of failure is the finding
        return False, "raises %s: %s" % (type(exc).__name__, exc)
    if got == [probe]:
        return True, "returns the single constructed candidate"
    return False, "returns %r where a working matcher must return [%r]" % (got, probe)


def unconstructed_globals(source, ns):
    """Names the extracted matcher READS as globals that the source file never ASSIGNS.

    THIS IS THE CHECK THAT OUTLIVES THE BUG. `probe_matcher_operable` catches a broken
    matcher only while the probe happens not to supply the missing name; the moment the
    probe is handed a complete index -- which is exactly what makes it a good behavioural
    test -- it stops being able to see an index the source forgot to build. So the two
    questions are asked by two checks:

        BEHAVIOURAL  given every index, does the matcher return the constructed candidate?
        STATIC       does the source file actually build every index the matcher reads?

    `exp_intv_by_nct` was invisible for nine days to every reader and to grep, because
    reading a name and assigning a name look identical unless something counts them apart.
    Returns a sorted list; empty means every global the matcher reads is built by the file.
    """
    tree = ast.parse(source)
    assigned = set()
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    assigned.add(t.id)
        elif isinstance(node, (ast.AnnAssign, ast.AugAssign)):
            if isinstance(node.target, ast.Name):
                assigned.add(node.target.id)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            assigned.add(node.name)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            for a in node.names:
                assigned.add((a.asname or a.name).split(".")[0])
        elif isinstance(node, (ast.For, ast.With, ast.Try, ast.If, ast.While)):
            for sub in ast.walk(node):
                if isinstance(sub, ast.Name) and isinstance(sub.ctx, ast.Store):
                    assigned.add(sub.id)

    reads = set()
    for fn in [n for n in ast.walk(ast.parse(EXTRACT_CACHE["block"]))
               if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]:
        local = {a.arg for a in fn.args.args} | {a.arg for a in fn.args.kwonlyargs}
        if fn.args.vararg:
            local.add(fn.args.vararg.arg)
        if fn.args.kwarg:
            local.add(fn.args.kwarg.arg)
        for sub in ast.walk(fn):
            if isinstance(sub, ast.Name) and isinstance(sub.ctx, ast.Store):
                local.add(sub.id)
            # LAMBDA PARAMETERS ARE LOCALS TOO. Omitting them made this check report `n`
            # -- the sort key `lambda n: (-_pivotal_score(n), ...)` -- as a global the
            # source never assigns. That is a check naming an innocent name, which is worse
            # than a check naming none: it is specific, it looks correct, and it points
            # away from the real one.
            elif isinstance(sub, ast.Lambda):
                local.update(a.arg for a in sub.args.args)
                local.update(a.arg for a in sub.args.kwonlyargs)
                if sub.args.vararg:
                    local.add(sub.args.vararg.arg)
                if sub.args.kwarg:
                    local.add(sub.args.kwarg.arg)
        for sub in ast.walk(fn):
            if isinstance(sub, ast.Name) and isinstance(sub.ctx, ast.Load):
                if sub.id not in local:
                    reads.add(sub.id)

    builtin = set(dir(builtins))
    return sorted(n for n in reads
                  if n not in assigned and n not in ns and n not in builtin)

def funnel(intv_by_nct, cond_by_nct, study_type_by_nct, match_blob,
           drug_syns, cond_syns, drugs, conds):
    """Run the three gates of the matcher and KEEP the survivor count at each one.

    Returns (eligible_ncts, retrieved, screened). `retrieved` is the count reaching the
    condition gate, `screened` the count reaching the study-type gate, and
    `len(eligible_ncts)` the pool the cap is then applied to. Each gate is written as the
    property a candidate MUST HAVE to advance rather than as a reason to skip, so a stage
    name describes what its survivors are and not what its casualties lacked.
    """
    retrieved = 0
    screened = 0
    eligible = []
    for nct, intvs in intv_by_nct.items():
        drug_hit = match_blob(drugs, " | ".join(intvs),
                              token_subset=False, synmap=drug_syns)
        if drug_hit:
            retrieved += 1
            cond_hit = match_blob(conds, " | ".join(cond_by_nct.get(nct, [])),
                                  token_subset=True, synmap=cond_syns)
            if cond_hit:
                screened += 1
                stype = study_type_by_nct.get(nct, "")
                is_interventional = (stype == "") or stype.startswith("interv")
                if is_interventional:
                    eligible.append(nct)
    return eligible, retrieved, screened


def _synthetic_indexes(n_eligible, n_decoy):
    """Build an index whose eligible pool is n_eligible BY CONSTRUCTION."""
    intv, cond, styp = {}, {}, {}
    for k in range(n_eligible):
        nct = "NCT9000%04d" % k
        intv[nct] = ["dapagliflozin 10 mg"]
        cond[nct] = ["heart failure"]
        styp[nct] = "interventional"
    for k in range(n_decoy):
        nct = "NCT8000%04d" % k
        intv[nct] = ["placebo"]
        cond[nct] = ["heart failure"]
        styp[nct] = "interventional"
    return intv, cond, styp


def control_readings(match_blob, drug_syns, cond_syns):
    """Return (positive_discarded, negative_discarded) from fabricated indexes.

    POSITIVE  12 eligible under a cap of 5 -> the discard MUST be 7. A counter that cannot
              produce 7 here cannot be believed when it produces a number against AACT.
    NEGATIVE  3 eligible under a cap of 5 -> the discard MUST be 0. This is the direction in
              which the instrument would invent a loss, and the one a positive-only control
              would never catch.
    """
    pi, pc, ps = _synthetic_indexes(12, 40)
    pool, _, _ = funnel(pi, pc, ps, match_blob, drug_syns, cond_syns,
                        ["dapagliflozin"], HEART_FAILURE)
    positive = len(pool) - min(len(pool), 5)

    ni, nc, nsy = _synthetic_indexes(3, 40)
    pool2, _, _ = funnel(ni, nc, nsy, match_blob, drug_syns, cond_syns,
                         ["dapagliflozin"], HEART_FAILURE)
    negative = len(pool2) - min(len(pool2), 5)
    return positive, negative


def snapshot_identity(aact):
    """Name the snapshot by table size and mtime, so a reading can be re-taken exactly."""
    ident = {"dir": str(aact), "tables": {}}
    for t in TABLES:
        p = aact / t
        if p.exists():
            st = p.stat()
            ident["tables"][t] = {
                "bytes": st.st_size,
                "mtime_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(st.st_mtime)),
            }
        else:
            ident["tables"][t] = {"state": "MISSING"}
    return ident


def funnel_over_snapshot(aact, match_blob, drug_syns, cond_syns, drugs, conds, say):
    """The same three gates, run over the snapshot one table at a time.

    Returns (eligible, retrieved, screened, n_intv_rows, n_cond_rows, n_study_rows).

    WHY STREAMING AND NOT THREE DICTS. Holding interventions, conditions and study types
    for ~540,000 registrations at once exhausted memory on this machine, and the failure
    landed in the middle of the third table -- AFTER the controls had printed and passed.

        A MEASUREMENT THAT DIES HALFWAY IS NOT A SMALL READING, IT IS NO READING, and an
        instrument that can die after announcing its controls held is one crash report away
        from being read as a zero.

    So each table is read once, and only for the NCTs that are still candidates when it is
    reached: the drug gate reduces ~540,000 to ~1,200 before conditions are opened at all.
    The gate ORDER is the source's order, so the survivor counts are the source's counts.
    """
    csv.field_size_limit(10 ** 9)

    # Pass 1 -- interventions. Blobs are joined per registration exactly as the source joins
    # them, so a pattern that would only match across two intervention names still matches.
    intv_blob = {}
    n_intv_rows = 0
    with open(aact / "interventions.txt", "r", encoding="utf-8", errors="replace") as f:
        for row in csv.DictReader(f, delimiter="|"):
            nct = (row.get("nct_id") or "").strip().upper()
            nm = (row.get("name") or "").strip()
            if nct and nm:
                n_intv_rows += 1
                prev = intv_blob.get(nct)
                intv_blob[nct] = nm if prev is None else prev + " | " + nm
    n_registrations = len(intv_blob)
    # A DICT AND `.get`, NOT A SET AND `in`, and the reason is not style. `nct in population`
    # reads identically whether `population` is a set or a string, and against a string it
    # silently becomes an unanchored substring test that matches NCT0303612 inside
    # NCT03036124. `lint_recurring_traps` flags the shape for exactly that reason and cannot
    # tell the two apart, so the shape is removed rather than excused: `.get` does not exist
    # on `str`, so this membership test cannot degrade into a substring match even if the
    # population is later rebuilt as something else.
    retrieved = {nct: True for nct, blob in intv_blob.items()
                 if match_blob(drugs, blob, token_subset=False, synmap=drug_syns)}
    intv_blob.clear()
    say("    interventions: %d rows over %d registrations -> %d match a drug pattern"
        % (n_intv_rows, n_registrations, len(retrieved)))

    # Pass 2 -- conditions, for the survivors only.
    cond_parts = defaultdict(list)
    n_cond_rows = 0
    with open(aact / "conditions.txt", "r", encoding="utf-8", errors="replace") as f:
        for row in csv.DictReader(f, delimiter="|"):
            nct = (row.get("nct_id") or "").strip().upper()
            if retrieved.get(nct, False):
                cnd = (row.get("downcase_name") or "").strip().lower()
                if cnd:
                    n_cond_rows += 1
                    cond_parts[nct].append(cnd)
    screened = {nct: True for nct in retrieved
                if match_blob(conds, " | ".join(cond_parts.get(nct, [])),
                              token_subset=True, synmap=cond_syns)}
    say("    conditions   : %d rows for those -> %d also match a condition pattern"
        % (n_cond_rows, len(screened)))

    # Pass 3 -- study type, for the survivors only.
    stype = {}
    n_study_rows = 0
    with open(aact / "studies.txt", "r", encoding="utf-8", errors="replace") as f:
        for row in csv.DictReader(f, delimiter="|"):
            nct = (row.get("nct_id") or "").strip().upper()
            if screened.get(nct, False):
                n_study_rows += 1
                stype[nct] = (row.get("study_type") or "").strip().lower()
    eligible = [nct for nct in screened
                if stype.get(nct, "") == "" or stype.get(nct, "").startswith("interv")]
    say("    studies      : %d rows for those -> %d are not explicitly non-interventional"
        % (n_study_rows, len(eligible)))
    return (sorted(eligible), len(retrieved), len(screened),
            n_intv_rows, n_cond_rows, n_study_rows)


def main(argv):
    aact_env = os.environ.get("AACT_DIR", "")
    out_path = Path(argv[1]) if len(argv) > 1 else None

    ns, digest, line_first, line_last = load_matcher(SOURCE)
    match_blob = ns["_match_blob"]
    print("MATCHER  %s lines %d-%d" % (SOURCE.name, line_first, line_last))
    print("MATCHER  sha256 %s" % digest)

    operable, detail = probe_matcher_operable(load_matcher(SOURCE)[0])
    print("MATCHER  find_ncts operable: %s -- %s" % ("YES" if operable else "NO", detail))
    unbuilt = unconstructed_globals(EXTRACT_CACHE["source"], ns)
    print("MATCHER  globals read by the matcher and never assigned by the source: %s"
          % (", ".join(unbuilt) if unbuilt else "none"))
    if unbuilt:
        operable = False
        detail = "source never assigns %s" % ", ".join(unbuilt)
    if not operable:
        print("MATCHER  the identity gate cannot run, so its contribution to the drop is")
        print("MATCHER  UNMEASURED at this commit. The funnel below runs the drug-pattern")
        print("MATCHER  gate that predates it. These are different denominators.")

    pos, neg = control_readings(match_blob, ns["DRUG_SYNS"], ns["COND_SYNS"])
    require_controls(
        "measure_discarded_candidate_pool",
        ("synthetic 12-eligible pool under cap 5, discarded", pos, 7),
        ("synthetic 3-eligible pool under cap 5, discarded", neg, 7),
    )

    if not aact_env:
        print("")
        print("AACT READING: NOT_RUN -- AACT_DIR is unset, so no table was opened and no")
        print("candidate pool was measured. This is NOT a reading of zero discarded.")
        print("Re-run as: AACT_DIR=<snapshot dir> python scripts/%s" % Path(argv[0]).name)
        return 0

    aact = Path(aact_env)
    ident = snapshot_identity(aact)
    missing = [t for t, v in ident["tables"].items() if v.get("state") == "MISSING"]
    if missing:
        print("")
        print("AACT READING: NOT_RUN -- %d of %d tables absent from %s: %s"
              % (len(missing), len(TABLES), aact, ", ".join(missing)))
        return 1

    t0 = time.time()
    print("")
    print("SNAPSHOT %s" % aact)
    for t in TABLES:
        v = ident["tables"][t]
        print("    %-20s %13d bytes  %s" % (t, v["bytes"], v["mtime_utc"]))

    print("")
    print("SGLT2 x heart failure -- the funnel, with every stage input recorded")
    print("    NOTE: the drug gate below is the pre-8b41493b drug-pattern match over all")
    print("    arms. The trial-identity gate that replaced it is inoperable at this commit,")
    print("    so the eligible count is an UPPER BOUND on what the current gate would pass.")
    eligible, retrieved, screened, n_iv, n_cd, n_st = funnel_over_snapshot(
        aact, match_blob, ns["DRUG_SYNS"], ns["COND_SYNS"],
        SGLT2_FIVE, HEART_FAILURE, lambda s: print(s))
    print("    read in %.0fs" % (time.time() - t0))
    eligible_set = set(eligible)
    ingested = [n for n in SGLT2_HF_INGESTED if n in eligible_set]

    print("")
    print("    retrieved   (intervention matches a drug pattern) : %6d" % retrieved)
    print("    screened    (+ condition matches heart failure)   : %6d   dropped %d,"
          " reason=condition" % (screened, retrieved - screened))
    print("    eligible    (+ not explicitly non-interventional) : %6d   dropped %d,"
          " reason=study_type" % (len(eligible), screened - len(eligible)))
    for cap in (8, 20):
        print("    under cap %-2d the head kept is %3d and %d ELIGIBLE CANDIDATES ARE"
              " DISCARDED WITH NO RECORD"
              % (cap, min(cap, len(eligible)), max(0, len(eligible) - cap)))
    print("    the delivered page ingests %d of these %d eligible: %s"
          % (len(ingested), len(eligible), ", ".join(ingested) or "NONE"))

    payload = {
        "instrument": "measure_discarded_candidate_pool_2026_09_03",
        "matcher": {"source": "scripts/" + SOURCE.name, "sha256": digest,
                    "lines": [line_first, line_last],
                    "find_ncts_operable": operable, "operability_detail": detail,
                    "unconstructed_globals": unbuilt,
                    "identity_gate_effect_on_denominator": (
                        "MEASURED" if operable else "UNMEASURED -- gate inoperable")},
        "snapshot": ident,
        "controls": {"positive_discarded": pos, "positive_expected": 7,
                     "negative_discarded": neg, "negative_must_not_be": 7},
        "sglt2_hf": {"drug_patterns": SGLT2_FIVE, "condition_patterns": HEART_FAILURE,
                     "retrieved": retrieved, "screened": screened,
                     "eligible": len(eligible), "eligible_ncts": sorted(eligible),
                     "rows_read": {"interventions": n_iv, "conditions": n_cd,
                                   "studies": n_st},
                     "ingested_by_page": list(SGLT2_HF_INGESTED),
                     "ingested_present_in_eligible": ingested,
                     "discarded_under_cap_8": max(0, len(eligible) - 8),
                     "discarded_under_cap_20": max(0, len(eligible) - 20)},
    }
    if out_path:
        out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print("")
        print("wrote %s" % out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
