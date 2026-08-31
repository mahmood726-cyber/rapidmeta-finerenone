#!/usr/bin/env python3
"""WHAT THE CORPUS COULD SAY AND DOES NOT, COUNTED ON THE ONLY KEY THAT IS WELL-DEFINED.

    THE UNIT IS (TOPIC, TRIAL). NOT TRIAL.

ARISTOTLE (NCT00412984) is used by `doac-af-review` at point=0.7917 and used by NOTHING in
`apixaban-af-review`, which holds it too. A trial-keyed denominator has to put it in one bucket
or the other, and either choice is false: "contributes" hides the apixaban gap, "contributes
nothing" hides the doac use. Every trial-keyed count quoted about this corpus -- including both
of mine earlier today -- silently drops exactly the cases where a trial is simultaneously used
and unused, which are the interesting ones.

    A trial is not used or unused. A trial is used BY A TOPIC, and the same trial may be
    unused by the topic sitting next to it.

THE AACT ROOT IS RESOLVED BY CALLING THE RESOLVER, NEVER BY RETYPING ITS CANDIDATES.

    ⭐ TO TEST WHAT A FUNCTION RESOLVES, CALL THE FUNCTION.

Earlier today I reported this corpus's AACT snapshot as MISSING and used that to overturn a
brief. The snapshot was present at `F:/AACT-storage/AACT/2026-04-12`, exactly where
`_resolve_aact_root()` looks. I had typed a candidate list into a shell loop -- `F:/AACT`,
`D:/AACT-storage`, `C:/AACT` -- and never tested `F:/AACT-storage`. A hand-typed vocabulary
narrower than the thing it claims to test, committed inside the check I used to contradict the
orchestrator. It fails silently toward ABSENT, absent reads as a clean negative result, and a
clean negative is the finding nobody re-checks. Sibling of "grepping for a remembered wording
is not a check".

THREE STATES ON EVERY AXIS. A (topic, trial) pair is CONTRIBUTING, RETRIEVABLE, or
NOTHING_IN_AACT -- and the third is a claim about AACT that has to survive being re-checked
with a looser predicate, because the first version of this scan produced an 87 that may have
been an artefact of its own strictness rather than a fact about the registry.
"""
import csv
import io
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "scripts"))
csv.field_size_limit(10 ** 8)

# POSITIVE PROPERTY, from the shared module. This file previously carried
# `if not NCT.match(n): continue` -- an ABSENCE where `is a registered trial` was meant,
# which would drop every ISRCTN, EudraCT, ACTRN, ChiCTR, CTRI, JPRN, IRCT and PACTR
# registrant from every denominator below, silently. Measured 2026-08-27: 403 of 403
# identifiers are NCT, so the exclusion was empirically empty -- and unsafe in general.
#
# AND THE REWIRING ITSELF BROKE TWICE, which is why it is recorded here. A blanket text
# replace fixed one call site and left a second bare `NCT.match(n)` with no `NCT` in scope --
# NameError on the next run. The same replace also rewrote THIS COMMENT, so the file briefly
# described its own fix as the defect it fixed. Both caught by running it, neither by reading
# it.
sys.path.insert(0, os.path.join(REPO, "ssot"))
from registration_identifiers import is_registration_id  # noqa: E402


def aact_root():
    """CALL the repo's resolver. Do not reimplement its candidate list here -- copying the
    list is the defect this module's docstring is about, and a copy drifts silently.

    IT CANNOT BE IMPORTED, AND THAT IS THE CAUSE OF THE WHOLE ERROR CLASS.
    `scripts/aact_baselines.py` does work at MODULE level: it calls the resolver on import
    and then reads `outputs/corpus_ncts.txt`, which does not exist. So `from aact_baselines
    import _resolve_aact_root` raises FileNotFoundError before the function is bound. A
    resolver nobody can import is a resolver everybody retypes -- which is precisely how I
    came to test `F:/AACT` and never `F:/AACT-storage`.

    So the function is lifted out of the source by name and executed alone. That is still
    the repo's own candidate list, read from the repo's own file at run time; it is not a
    copy, and it goes stale only if the source does.
    """
    import ast
    src_path = os.path.join(REPO, "scripts", "aact_baselines.py")
    with io.open(src_path, encoding="utf-8") as fh:
        src = fh.read()
    tree = ast.parse(src)
    fn = next((n for n in tree.body
               if isinstance(n, ast.FunctionDef) and n.name == "_resolve_aact_root"), None)
    if fn is None:
        raise SystemExit("REFUSED: _resolve_aact_root is no longer defined in %s. It has "
                         "been renamed or removed; find it rather than retyping its paths."
                         % src_path)
    ns = {}
    exec(compile(ast.Module(body=[fn], type_ignores=[]), src_path, "exec"),
         {"os": os, "Path": __import__("pathlib").Path, "SystemExit": SystemExit}, ns)
    return str(ns["_resolve_aact_root"]())


def population():
    """Every (topic, trial) pair the corpus holds, with whether THAT TOPIC uses it."""
    ssot = os.path.join(REPO, "ssot")
    pairs = {}
    unidentified = []
    for t in sorted(os.listdir(ssot)):
        p = os.path.join(ssot, t, t + ".json")
        if not os.path.isdir(os.path.join(ssot, t)) or not os.path.exists(p):
            continue
        with io.open(p, encoding="utf-8") as fh:
            obj = json.load(fh)
        trials = ((obj.get("inputs") or {}).get("trials") or [])
        if not trials:
            continue
        held, used = set(), set()
        for tr in trials:
            n = (tr.get("nct") or "").strip()
            # POSITIVE CONTROL FLOW, not `if not ...: continue`. The predicate names the
            # property -- IS a registration identifier -- and the trials that fail it are
            # COUNTED rather than skipped in silence, because a trial dropped without a
            # message is exactly what `audit_exclusion_by_absence` exists to prevent and
            # exactly what this file did an hour ago. Measured: 4 trials corpus-wide carry
            # no identifier field at all, and they are now reported instead of vanishing.
            if is_registration_id(n):
                held.add(n)
                for _oid, b in (tr.get("by_outcome") or {}).items():
                    if ((b or {}).get("effect") or {}).get("point") is not None:
                        used.add(n)
            else:
                unidentified.append((t, repr(tr.get("nct"))[:40]))
        for _oid, b in ((obj.get("results") or {}).get("by_outcome") or {}).items():
            for r in ((b or {}).get("per_trial") or []):
                if isinstance(r, dict) and r.get("point") is not None:
                    n = (r.get("nct") or "").strip()
                    if is_registration_id(n):
                        used.add(n)
        for n in held:
            pairs[(t, n)] = (n in used)
    return pairs, unidentified


def aact_capability(ncts, root):
    """For each NCT: does AACT hold an ANALYSIS (read) and/or ARM COUNTS (derive).

    STRICT AND LOOSE, BOTH REPORTED. The strict read-predicate requires a value and both
    interval bounds. The loose one requires only a value -- an analysis with a point and no
    interval is still a posted analysis, and calling it "nothing in AACT" would be the same
    over-strictness that produced a number I could not defend.
    """
    read_strict, read_loose, analysis_rows = set(), set(), {}
    with io.open(os.path.join(root, "outcome_analyses.txt"),
                 encoding="utf-8", errors="replace", newline="") as fh:
        for row in csv.DictReader(fh, delimiter="|"):
            n = (row.get("nct_id") or "").strip()
            if n not in ncts:
                continue
            analysis_rows[n] = analysis_rows.get(n, 0) + 1
            val = (row.get("param_value") or "").strip()
            lo = (row.get("ci_lower_limit") or "").strip()
            hi = (row.get("ci_upper_limit") or "").strip()
            if val not in ("", "NA"):
                read_loose.add(n)
                if lo not in ("", "NA") and hi not in ("", "NA"):
                    read_strict.add(n)
    groups = {}
    with io.open(os.path.join(root, "outcome_counts.txt"),
                 encoding="utf-8", errors="replace", newline="") as fh:
        for row in csv.DictReader(fh, delimiter="|"):
            n = (row.get("nct_id") or "").strip()
            if n not in ncts:
                continue
            c = (row.get("count") or "").strip()
            if c in ("", "NA"):
                continue
            groups.setdefault(n, {}).setdefault(row.get("outcome_id"), set()).add(
                row.get("result_group_id"))
    derive = {n for n, o in groups.items() if any(len(g) >= 2 for g in o.values())}
    return read_strict, read_loose, derive, analysis_rows


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    root = aact_root()
    print("AACT root, RESOLVED BY CALLING THE RESOLVER: %s" % root)
    pairs, unidentified = population()
    topics = sorted({t for t, _ in pairs})
    ncts = {n for _, n in pairs}
    unused_pairs = {k for k, used in pairs.items() if not used}
    used_pairs = {k for k, used in pairs.items() if used}

    # THE CASE THAT PROVES THE KEY. Counted, not asserted.
    both = sorted({n for _, n in used_pairs} & {n for _, n in unused_pairs})

    print()
    print("POPULATION ON THE (TOPIC, TRIAL) KEY")
    print("   trials carrying NO registration identifier %2d  <- counted, not dropped"
          % len(unidentified))
    print("   topics with >=1 trial            %4d" % len(topics))
    print("   distinct trials (NCT)            %4d" % len(ncts))
    print("   (topic, trial) PAIRS             %4d" % len(pairs))
    print("     pairs where the topic USES it  %4d" % len(used_pairs))
    print("     pairs where it CONTRIBUTES NOTHING %4d" % len(unused_pairs))
    print("   topics with >=1 unused pair      %4d"
          % len({t for t, _ in unused_pairs}))
    print()
    print("TRIALS THAT ARE SIMULTANEOUSLY USED AND UNUSED: %d" % len(both))
    print("   every trial-keyed denominator quoted today mis-assigns these.")
    for n in both[:10]:
        u = sorted(t for t, x in unused_pairs if x == n)
        v = sorted(t for t, x in used_pairs if x == n)
        print("     %s  unused by %s | used by %s" % (n, ",".join(u), ",".join(v)))

    want = {n for _, n in unused_pairs}
    rs, rl, dv, arows = aact_capability(want, root)
    print()
    print("AACT CAPABILITY, denominator = %d DISTINCT trials appearing in >=1 unused pair"
          % len(want))
    print("   analysis rows present at all     %4d" % len(arows))
    print("   READ  strict (value + both CI)   %4d" % len(rs))
    print("   READ  loose  (value only)        %4d" % len(rl))
    print("   DERIVE (>=2 arm groups w/ counts)%4d" % len(dv))
    print("   EITHER (strict read or derive)   %4d" % len(rs | dv))
    print("   NOTHING IN AACT                  %4d" % len(want - (rl | dv)))
    print()
    print("AND ON THE UNIT THAT MATTERS -- (topic, trial) PAIRS:")
    pr = {k for k in unused_pairs if k[1] in (rs | dv)}
    pn = {k for k in unused_pairs if k[1] not in (rl | dv)}
    print("   RETRIEVABLE pairs                %4d  across %d topics"
          % (len(pr), len({t for t, _ in pr})))
    print("   NOTHING-IN-AACT pairs            %4d  across %d topics"
          % (len(pn), len({t for t, _ in pn})))
    print("   loose-only (value, no interval)  %4d"
          % len({k for k in unused_pairs if k[1] in (rl - rs) and k[1] not in dv}))

    dest = os.path.join(REPO, "outputs", "topic_trial_retrievability_2026_08_26.json")
    if not os.path.isdir(os.path.dirname(dest)):
        os.makedirs(os.path.dirname(dest))
    with io.open(dest, "w", encoding="utf-8") as fh:
        fh.write(json.dumps({
            "aact_root": root, "topics": len(topics), "distinct_trials": len(ncts),
            "pairs": len(pairs), "used_pairs": len(used_pairs),
            "unused_pairs": len(unused_pairs),
            "trials_both_used_and_unused": both,
            "read_strict": sorted(rs), "read_loose_only": sorted(rl - rs),
            "derive": sorted(dv), "nothing_in_aact": sorted(want - (rl | dv)),
            "retrievable_pairs": sorted("%s|%s" % k for k in pr),
            "nothing_pairs": sorted("%s|%s" % k for k in pn),
            "DONE": True}, indent=1))
    print()
    print("wrote %s" % dest)
    return 0


if __name__ == "__main__":
    sys.exit(main())
