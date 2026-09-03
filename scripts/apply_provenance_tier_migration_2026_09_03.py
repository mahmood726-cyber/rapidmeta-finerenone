"""Migrate the seven legacy-provenance strings to tiers, using rows identified by reproduction.

WHAT THIS IS NOT. It is NOT a string-to-tier mapping. `ssot/provenance_tier.py::validate`
forbids exactly that, in code -- "a string containing the word 'registry' is not evidence
that the number came from a posted results table ... do NOT infer the tier from the words in
the string" -- and it is right: across `ssot/*/*.json` there are 40 distinct legacy strings,
and TWELVE of them say the OPPOSITE ("NOT SUPPLIED BY THE REGISTRY. NCTxxxxx posts NO RESULTS
SECTION"). A mapping written over the one string would have converted those twelve into
asserting a provenance they explicitly disclaim.

WHAT IT IS. Every field written here was obtained by IDENTIFICATION BY REPRODUCTION:
enumerate every posted outcome measure of the registration with no keyword filter at all,
recompute the stored estimate from each candidate row under a closed declared convention set,
and require TWO WITNESSES -- the point AND the 95% interval. See
`scripts/identify_source_row_by_reproduction_2026_09_03.py` and the full table in
`out/provenance_row_identification_2026_09_03.json`. THE ARITHMETIC NAMES THE ROW, NOT ME.

    THE POINT IDENTIFIES A CANDIDATE; THE INTERVAL DISCRIMINATES.
    A ONE-WITNESS METHOD IS NOT AN IDENTIFICATION.

On NCT00423319 six UNRELATED rows reproduce the stored point to within 0.2% -- Bloody
discharge, Hypoaesthesia, Monocytes (absolute) high, Neutrophils (absolute) low, Glucose
fasting serum high, and a non-fatal PE rate -- and not one reproduces the interval. A
point-only method would have written "Bloody discharge" into a major-bleeding provenance with
an exact arithmetic match as its evidence.

THE SEVENTH ROW, AND WHY `COULD_NOT_DETERMINE` IS TRUE NOW AND WAS FALSE BEFORE. That state
asserts SOMEONE LOOKED AND FAILED. Earlier today nobody had looked, so writing it would have
been a false statement about who did what, and it was refused on exactly that ground. Nine
outcome measures and seventy-two candidate computations later, with no keyword filter, the
looking has been done and has failed -- and it failed for a reason that is a PROPERTY OF THE
DATA, not a judgement about anybody's science: on NCT02829957 six posted rows are all `0/11`
against `0/8`, and every zero-versus-zero outcome yields the same continuity-corrected 8/11 =
0.7273. All six are named inside the block this script writes.

    IDENTIFICATION BY REPRODUCTION IS BLIND EXACTLY WHERE BOTH ARMS HAVE ZERO EVENTS.
    No enumeration resolves it and no larger corpus will.

BYTE DISCIPLINE. Both store objects round-trip byte-identically through
`json.dumps(indent=1, ensure_ascii=False)` with CRLF and a trailing newline -- verified before
any edit -- so the diff this produces is exactly the seven provenance values and nothing else.
The script proves it: it deep-compares the whole object before and after with the seven paths
excised, and refuses if anything else moved.

PLANTED BOTH WAYS. Each of the seven is asserted to hold the legacy STRING before, and to
hold a block that `provenance_tier.validate` accepts with zero problems after. A migration
that silently matched nothing would report success over an unchanged file.

Usage:  python scripts/apply_provenance_tier_migration_2026_09_03.py [--check]
"""
from __future__ import annotations

import copy
import io
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "ssot"))

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

IDENT = os.path.join(REPO, "out", "provenance_row_identification_2026_09_03.json")
LEGACY = "REGISTRY -- ClinicalTrials.gov posted results"
ACCESSED = "2026-09-03"

# (store object, outcome id) -> where the rows live. Rows are matched by trial_id, never by
# position: an index is not an identity and a reordering would silently retarget the edit.
TARGETS = [
    ("apixaban-vte-prophylaxis", "major_bleeding"),
    ("apixaban-vte-treatment", "major_bleeding"),
]


def store_path(app):
    return os.path.join(REPO, "ssot", app, app + ".json")


def load_bytes(p):
    return io.open(p, "rb").read()


def dump_bytes(obj):
    return (json.dumps(obj, indent=1, ensure_ascii=False) + "\n").replace(
        "\n", "\r\n").encode("utf-8")


def identifications():
    d = json.load(io.open(IDENT, encoding="utf-8"))
    return {r["nct"]: r for r in d["results"]}, d


def block_for(rec):
    """The provenance block for one registration, built ONLY from what reproduced."""
    nct = rec["nct"]
    common = {
        "registry": "ClinicalTrials.gov",
        "registry_id": nct,
        "accessed_utc": ACCESSED,
        "migrated_from_legacy_string": LEGACY,
        "identified_by": (
            "identification by reproduction: every posted outcome measure enumerated with no "
            "keyword filter (%d measures, %d candidate computations); the point AND the 95%% "
            "interval both required to reproduce"
            % (rec["outcome_measures_enumerated"], rec["candidate_computations"])),
        "method_script": "scripts/identify_source_row_by_reproduction_2026_09_03.py",
        "method_evidence": "out/provenance_row_identification_2026_09_03.json",
    }
    if rec["state"] == "IDENTIFIED":
        m = rec["matches"][0]
        row = "outcome measure index %d; %s versus %s" % (
            m["outcome_index"], m["numerator"], m["denominator"])
        if m["class"]:
            row += "; class %r" % m["class"]
        b = dict(common)
        b.update({
            "tier": "REGISTRY_POSTED_RESULT",
            "table": m["table"],
            "row_identifier": row,
            "reproduces": "%s -> %.4f (%.4f to %.4f) against the stored %.4f (%.4f to %.4f)"
                          % (m["convention"], m["reproduced"]["point"], m["reproduced"]["lo"],
                             m["reproduced"]["hi"], rec["stored"]["point"],
                             rec["stored"]["lo"], rec["stored"]["hi"]),
        })
        return b
    b = dict(common)
    b.update({
        "tier": "COULD_NOT_DETERMINE",
        "why": (
            "SOMEONE LOOKED AND FAILED, and the failure is a property of the data. Six posted "
            "rows reproduce the stored %.4f (%.4f to %.4f) EXACTLY, because all six are 0/11 "
            "against 0/8 and every zero-versus-zero outcome yields the same continuity-"
            "corrected 8/11. Identification by reproduction is blind exactly where both arms "
            "have zero events; no enumeration resolves it."
            % (rec["stored"]["point"], rec["stored"]["lo"], rec["stored"]["hi"])),
        "candidate_rows_none_of_which_can_be_distinguished": [
            "outcome measure index %d: %s" % (m["outcome_index"], m["table"])
            for m in rec["matches"]],
        "not_established": (
            "This does NOT say the value did not come from the registry. It says the registry "
            "cannot distinguish which of six posted rows it came from."),
    })
    return b


def rows_of(obj, outcome):
    return ((obj.get("results") or {}).get("by_outcome") or {}).get(outcome, {}).get(
        "per_trial") or []


def main(argv):
    import provenance_tier as pt

    ident, meta = identifications()
    check = "--check" in argv
    print("SOURCE OF EVERY FIELD: %s  (identified %d of %d)"
          % (os.path.relpath(IDENT, REPO), meta["identified"], meta["of"]))
    print("A legacy string is NEVER read for its meaning; only reproduced rows are written.\n")

    wrote, problems, touched = 0, [], []
    for app, outcome in TARGETS:
        p = store_path(app)
        raw = load_bytes(p)
        obj = json.loads(raw.decode("utf-8"))

        # BYTE FIDELITY PROVEN BEFORE ANY EDIT, not assumed.
        if dump_bytes(obj) != raw:
            problems.append("%s does not round-trip byte-identically; refusing to rewrite it"
                            % app)
            continue
        before = copy.deepcopy(obj)

        for r in rows_of(obj, outcome):
            nct = r.get("trial_id")
            if nct not in ident:
                continue
            rec = ident[nct]
            cur = r.get("provenance")
            if check:
                state = ("legacy string" if cur == LEGACY else
                         "tier %s" % cur.get("tier") if isinstance(cur, dict) else
                         "unexpected %s" % type(cur).__name__)
                print("   %-13s %-20s %s" % (nct, rec["state"], state))
                continue
            if isinstance(cur, dict) and cur.get("tier"):
                print("   %-13s already migrated (tier %s)" % (nct, cur["tier"]))
                continue
            if cur != LEGACY:
                problems.append("%s|%s does not hold the legacy string; found %r"
                                % (app, nct, str(cur)[:60]))
                continue
            r["provenance"] = block_for(rec)
            bad = pt.validate(r)
            if bad:
                problems.append("%s|%s the written block does not validate: %s" % (app, nct, bad))
                continue
            wrote += 1
            touched.append((app, outcome, nct))

        if check:
            continue

        # NOTHING ELSE MOVED. Excise the seven provenance values from both trees and
        # deep-compare the remainder; a migration that also changed something else is not a
        # migration.
        def excise(o):
            o = copy.deepcopy(o)
            for rr in rows_of(o, outcome):
                if rr.get("trial_id") in ident:
                    rr.pop("provenance", None)
            return o
        if excise(before) != excise(obj):
            problems.append("%s changed outside the provenance values" % app)
            continue

        new = dump_bytes(obj)
        io.open(p, "wb").write(new)
        back = load_bytes(p)
        if back != new:
            io.open(p, "wb").write(raw)
            problems.append("%s post-write byte check failed; REVERTED" % app)

    if check:
        return 0
    for pr in problems:
        print("   REFUSED: %s" % pr)
    if problems:
        return 1

    # PLANTED BOTH WAYS: re-read from disk and assert the end state.
    ok = 0
    for app, outcome in TARGETS:
        obj = json.loads(load_bytes(store_path(app)).decode("utf-8"))
        for r in rows_of(obj, outcome):
            nct = r.get("trial_id")
            if nct not in ident:
                continue
            pv = r.get("provenance")
            if not isinstance(pv, dict):
                print("   REFUSED: %s still holds a %s" % (nct, type(pv).__name__))
                return 1
            bad = pt.validate(r)
            if bad:
                print("   REFUSED: %s does not validate after the write: %s" % (nct, bad))
                return 1
            ok += 1
            print("   %-13s -> %-24s %s" % (nct, pv["tier"],
                                            (pv.get("table") or pv.get("why", ""))[:70]))
    print("\n-> migrated %d row(s); %d validate with zero problems" % (wrote, ok))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
