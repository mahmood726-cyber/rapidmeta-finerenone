"""IDENTITY BY REGISTRATION -- is every trial keyed to a registration id, and is
that id the one the covering label actually belongs to?

WHY THIS EXISTS -- THE WORST ERROR THIS PROJECT HAS MADE
    PARACHUTE-HF was read as ANSWER-HF. A covering LABEL was accepted as document
    identity while the registry id said otherwise, and a trial that was never in
    the review was reported as though it were. Nothing downstream could recover
    from it: every count, every pool, every sentence about that trial described a
    different study.

    A NAME IS NOT AN IDENTITY. Acronyms collide, are reused across programmes,
    and are printed inconsistently. The registration id is the only key that
    cannot collide with English, and it is the only thing this gate will accept.

WHAT A FULL PASS DOES NOT ESTABLISH -- written in advance
    - NOT that the registration id is the RIGHT trial for the question. It
      establishes that a key exists, is well formed, is unique within the object,
      and that the name attached to it does not contradict it.
    - NOT that the registry entry says what the object says it says. That is the
      extraction gate's job, and it needs the registry, not this artefact.
    - NOT anything about trials the object never mentions.
"""
from __future__ import annotations
import io, json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import object_shapes as _os                                   # noqa: E402

NCT = re.compile(r"^NCT\d{8}$")
# Acronyms that appear in a trial NAME. Compared whole, never as a fragment:
# "AF_" once matched inside "TAF_TDF" and cost a corpus sweep.
ACRO = re.compile(r"\b([A-Z][A-Z0-9]{2,}(?:-[A-Z0-9]+)*)\b")


def check(obj, known=None):
    """-> (verdict, rows). known: {nct: canonical_acronym} to catch conflation."""
    known = known or {}
    trials = _os.trials_of(obj)
    if not trials:
        return "UNCHECKABLE", [("<no trials>", "UNCHECKABLE",
                                "the object carries no trials in either schema")]
    rows, seen = [], {}
    for t in trials:
        nct, name = (t.get("nct") or "").strip(), (t.get("name") or "").strip()
        if not nct:
            rows.append((name or "<unnamed>", "FAIL",
                         "no registration id: keyed by name alone, which is the "
                         "PARACHUTE-HF/ANSWER-HF shape"))
            continue
        if not NCT.match(nct):
            rows.append((nct, "FAIL", "malformed registration id %r" % nct))
            continue
        if nct in seen and seen[nct] != name:
            rows.append((nct, "FAIL", "one id carries two names: %r and %r"
                         % (seen[nct], name)))
            continue
        seen[nct] = name
        # CONFLATION: the id is real and the NAME belongs to a different id.
        canon = known.get(nct)
        if canon:
            acros = set(ACRO.findall(name.upper()))
            if acros and canon.upper() not in acros:
                rows.append((nct, "FAIL",
                             "id %s is %s, but this object names it %r -- a "
                             "covering label accepted as identity"
                             % (nct, canon, name)))
                continue
        rows.append((nct, "PASS", "%s = %r" % (nct, name or "(unnamed)")))
    verdict = ("FAIL" if any(v == "FAIL" for _, v, _ in rows)
               else "PASS" if any(v == "PASS" for _, v, _ in rows)
               else "UNCHECKABLE")
    return verdict, rows


def selftest():
    """REPLAYED AGAINST THE REAL CONFLATION, not a synthetic one."""
    ok = True
    # PARACHUTE-HF is NCT04023266; ANSWER-HF is a different trial entirely.
    KNOWN = {"NCT04023266": "PARACHUTE-HF"}
    defect = {"inputs": {"trials": [
        {"nct": "NCT04023266", "name": "ANSWER-HF", "arms": []}]}}
    v, rows = check(defect, KNOWN)
    good = v == "FAIL"
    ok &= good
    print("  POSITIVE PARACHUTE-HF's id carrying ANSWER-HF's name -> %-4s %s"
          % (v, "correct" if good else "WRONG"))
    print("        %s" % rows[0][2])

    clean = {"inputs": {"trials": [
        {"nct": "NCT04023266", "name": "PARACHUTE-HF", "arms": []}]}}
    v2, _ = check(clean, KNOWN)
    ok &= v2 == "PASS"
    print("  NEGATIVE the same id with its own name           -> %-4s %s"
          % (v2, "correct" if v2 == "PASS" else "WRONG"))

    noid = {"inputs": {"trials": [{"name": "ANSWER-HF", "arms": []}]}}
    v3, _ = check(noid)
    ok &= v3 == "FAIL"
    print("  POSITIVE a trial keyed by NAME ALONE             -> %-4s %s"
          % (v3, "correct" if v3 == "FAIL" else "WRONG"))

    dup = {"inputs": {"trials": [
        {"nct": "NCT04023266", "name": "PARACHUTE-HF", "arms": []},
        {"nct": "NCT04023266", "name": "ANSWER-HF", "arms": []}]}}
    v4, _ = check(dup)
    ok &= v4 == "FAIL"
    print("  POSITIVE one id carrying two different names     -> %-4s %s"
          % (v4, "correct" if v4 == "FAIL" else "WRONG"))

    empty = {}
    v5, _ = check(empty)
    ok &= v5 == "UNCHECKABLE"
    print("  NEGATIVE an object with no trials                -> %-4s %s (not a pass)"
          % (v5, "correct" if v5 == "UNCHECKABLE" else "WRONG"))

    print("\nWHAT A FAILURE WOULD LOOK LIKE: the conflation passing, which is how a "
          "trial that was never in the review came to be reported as though it were.")
    print("-> SELFTEST PASS" if ok else "-> SELFTEST FAILED")
    return 0 if ok else 1


def main():
    if len(sys.argv) < 2 or sys.argv[1] == "--selftest":
        return selftest()
    if not os.path.exists(sys.argv[1]):
        print("identity_by_registration: %s does not exist. NOT RUN -- not a pass."
              % sys.argv[1], file=sys.stderr)
        return 2
    obj = json.loads(open(sys.argv[1], encoding="utf-8", errors="replace").read())
    known = {}
    kp = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      "ssot", "KNOWN_REGISTRATIONS.json")
    if os.path.exists(kp):
        known = json.loads(open(kp, encoding="utf-8").read())
    v, rows = check(obj, known)
    for key, verdict, why in rows:
        print("  %-14s %-12s %s" % (key, verdict, why))
    print("  -> %s" % v)
    return 0 if v == "PASS" else (2 if v == "UNCHECKABLE" else 1)


if __name__ == "__main__":
    sys.exit(main())
