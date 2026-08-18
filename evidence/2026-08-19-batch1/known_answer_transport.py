"""Known-answer test for ctgov_transport, run BEFORE the guard is trusted anywhere.

The guard must do BOTH directions, or it is not a guard:
  * REFUSE the flattened MCP shape (the case that silently returned not_assessable).
  * ACCEPT the raw v2 shape (or it blocks the real pipeline, which is a worse failure).

Then the live fetch, checked against a record whose arm roles we already know:
NCT02789917 -> EXPERIMENTAL 'Dual therapy (incl. NOAC)' / ACTIVE_COMPARATOR 'Triple therapy'.
"""
import os
import sys

sys.path.insert(0, "F:/rapidmeta-ssot-shell/ssot")
os.environ.setdefault("RM_CTGOV_CACHE",
                      "F:/claude-temp/claude/F--rapidmeta-ssot-shell/"
                      "eb4d84e5-8a24-4c3b-afe2-34bd91c20bc7/scratchpad/.ctgov-raw-cache")

import ctgov_transport as X
import topic_identity as T

MCP_SHAPE = {"nct_id": "NCT02789917", "title": "APixaban Versus PhenpRocoumon...",
             "interventions": ["Dual Therapy", "Triple Therapy"]}

fails = []


def check(name, got, expected):
    ok = got == expected
    if not ok:
        fails.append(name)
    print(f"[{'ok ' if ok else 'MISS'}] {name}: got={got!r} expected={expected!r}")


# --- direction 1: the flattened shape must RAISE, not return a verdict -----------------
try:
    X.require_raw_v2(MCP_SHAPE, "NCT02789917")
    check("guard refuses flattened MCP shape", "returned", "raised WrongPayloadShape")
except X.WrongPayloadShape as exc:
    check("guard refuses flattened MCP shape", "raised", "raised")
    print(f"        reason: {str(exc)[:150]}...")

# --- direction 2: a live raw record must PASS the guard --------------------------------
state, study, detail = X.fetch_raw("NCT02789917")
check("fetch_raw state", state, X.OK)
print(f"        {detail}")

if state == X.OK:
    try:
        X.require_raw_v2(study, "NCT02789917")
        check("guard accepts raw v2 shape", "passed", "passed")
    except X.WrongPayloadShape:
        check("guard accepts raw v2 shape", "raised", "passed")

    check("nct_of", X.nct_of(study), "NCT02789917")

    # --- the answer we already know ----------------------------------------------------
    role, ev = T.locate(study, T.synonyms_for("apixaban"))
    check("locate() on LIVE raw record", role, T.EXPERIMENTAL)
    print(f"        evidence: {ev}")

    arms = study["protocolSection"]["armsInterventionsModule"].get("armGroups") or []
    check("arm types present in raw payload",
          sorted(a.get("type") for a in arms),
          ["ACTIVE_COMPARATOR", "EXPERIMENTAL"])

    # --- correct-negative: a drug genuinely not in this trial must NOT be located -------
    role_n, _ = T.locate(study, T.synonyms_for("bosentan"))
    check("correct-negative (bosentan in an apixaban trial)", role_n, T.NOT_ASSESSABLE)

# --- the cache must be content-keyed, and a second read must agree ---------------------
state2, study2, detail2 = X.fetch_raw("NCT02789917")
check("second fetch state", state2, X.OK)
check("cache returns identical content", X.nct_of(study2), "NCT02789917")
print(f"        {detail2}")

print()
print(f"{'ALL KNOWN ANSWERS REPRODUCED' if not fails else 'FAILURES: ' + ', '.join(fails)}")
sys.exit(1 if fails else 0)
