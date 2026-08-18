"""WITHDRAWAL REASON -- is the reason given for a withdrawal true?

WHY THIS EXISTS
    APIXABAN_ACS's card said "Estimate withdrawn -- bleeding and efficacy endpoints
    pooled". BOTH of its trials register bleeding. Verbatim:

      APPRAISE-1  "Event Rate of Composite of Adjudicated Major Bleeding and
                  Clinically Relevant Non-Major Bleeding ..."
      APPRAISE-J  "Percentage of Participants Who Had Composite of ISTH-Defined
                  Major and Clinically-relevant Non-major (CRNM) Bleeding Events"

    There was no efficacy endpoint in that pool to mix with a safety one. The
    withdrawal was RIGHT; its published explanation was FALSE.

    A WITHDRAWAL IS A PUBLISHED CLAIM. Nothing here was checking whether the reason
    given for one was true, and under the old rule a topic with a false reason
    still counted as done. A reader who accepts a false explanation is misled as
    surely as by a bad estimate.

THE FOUNDING FIXTURE PAIR, AND WHY IT IS UNUSUALLY GOOD
    RIVAROXABAN_ACS carries the IDENTICAL card wording -- "bleeding and efficacy
    endpoints pooled" -- and there it is TRUE: ATLAS ACS TIMI 46 really does
    register both a primary SAFETY outcome and a primary EFFICACY outcome.

    THE SAME SENTENCE IS FALSE ON ONE PAGE AND TRUE ON ANOTHER, and only the
    registrations separate them. A detector with a true positive and a true
    negative drawn from one sentence is about as discriminating as a fixture gets:
    it cannot pass by pattern-matching the words.

WHAT IT CHECKS
    A withdrawal reason claiming an efficacy/safety MIXTURE requires that at least
    one included trial register an efficacy endpoint AND at least one register a
    safety endpoint. That is decidable offline from the `outcome_definition` each
    trial now carries, read from the registry.

WHAT THIS DOES NOT ESTABLISH -- written in advance
    - NOT that a reason it cannot parse is false. It reads ONE family of claim --
      the efficacy/safety mixture -- because that is the one with a fixture. Every
      other reason returns NOT_APPLICABLE, which is not a pass.
    - NOT that a reason it clears is true. Confirming that both endpoint types are
      present does not confirm the rest of the sentence.
    - NOT that a false reason means the withdrawal is wrong. On APIXABAN_ACS the
      withdrawal stood on three other grounds. The verdict is about the REASON.
    - NOTHING without recorded endpoint definitions. UNCHECKABLE, never a pass,
      per the rule in scripts/gate_integrity.py.

USAGE
    python scripts/withdrawal_reason_gate.py <object.json> [...]
    python scripts/withdrawal_reason_gate.py --selftest
"""
from __future__ import annotations
import glob
import io
import json
import os
import re
import sys

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# A reason ASSERTING that a safety endpoint was pooled with an efficacy one.
MIXTURE = re.compile(
    r"(bleeding|safety|adverse[- ]event|harm)s?\b[^.]{0,80}?\band\b[^.]{0,80}?"
    r"(efficacy|effectiveness)|"
    r"(efficacy|effectiveness)\b[^.]{0,80}?\band\b[^.]{0,80}?"
    r"(bleeding|safety|adverse[- ]event|harm)s?", re.I)

SAFETY = re.compile(r"bleed|haemorrhag|hemorrhag|adverse event|toxicit|"
                    r"tolerabilit|safety", re.I)
EFFICACY = re.compile(r"stroke|embolism|embolic|infarction|mortality|death|"
                      r"thromboembolism|recurren|revascularis|revasculariz|"
                      r"hospitali|composite of (?:cardiovascular|major)", re.I)


def endpoint_kinds(obj):
    """(has_safety, has_efficacy, per-trial detail) from recorded definitions."""
    trials = ((obj.get("inputs") or {}).get("trials")) or []
    results = ((obj.get("results") or {}).get("by_outcome")) or {}
    if not results:
        return None, None, []
    oid = sorted(results)[0]
    detail, safe, eff = [], False, False
    for t in trials:
        bo = (t.get("by_outcome") or {}).get(oid) or {}
        d = bo.get("outcome_definition") or ""
        src = bo.get("outcome_definition_source") or {}
        text = "%s %s" % (d, src.get("components_as_the_registry_states_them") or "")
        if not d:
            detail.append((t.get("name") or "?", None, None))
            continue
        s_hit = bool(SAFETY.search(text))
        # a bleeding composite that also names an efficacy event is BOTH
        e_hit = bool(EFFICACY.search(text))
        safe |= s_hit
        eff |= e_hit
        detail.append((t.get("name") or "?", s_hit, e_hit))
    return safe, eff, detail


def assess(obj):
    results = ((obj.get("results") or {}).get("by_outcome")) or {}
    if not results:
        return "UNCHECKABLE", "object carries no outcome", []
    oid = sorted(results)[0]
    pooled = (results[oid].get("pooled") or {})
    if not pooled.get("withdrawn"):
        return "NOT_APPLICABLE", "this outcome is not withdrawn", []
    reason = " ".join(str(pooled.get(k) or "") for k in
                      ("withdrawn_reason", "card_note"))
    if not MIXTURE.search(reason):
        return ("NOT_APPLICABLE",
                "the stated reason does not claim an efficacy/safety mixture; this "
                "gate reads only that family of claim and has no fixture for others",
                [])
    safe, eff, detail = endpoint_kinds(obj)
    if not detail or all(d[1] is None for d in detail):
        return ("UNCHECKABLE",
                "no endpoint definitions are recorded, so the reason cannot be "
                "tested against them. Not a pass", detail)
    if safe and eff:
        return ("PASS",
                "the reason claims an efficacy/safety mixture and the recorded "
                "definitions contain both", detail)
    missing = "efficacy" if safe else "safety"
    return ("FAIL",
            "THE STATED REASON IS FALSE. It claims an efficacy/safety mixture, and "
            "NO included trial registers a %s endpoint. The withdrawal may still be "
            "right -- this gate judges the REASON, not the verdict -- but the "
            "explanation a reader is given is contradicted by the trials' own "
            "registrations." % missing, detail)


def selftest() -> int:
    ok = True

    def obj(reason, defs):
        return {"inputs": {"trials": [
                    {"name": "T%d" % i,
                     "by_outcome": {"o": {"outcome_definition": d}}}
                    for i, d in enumerate(defs)]},
                "results": {"by_outcome": {"o": {
                    "pooled": {"withdrawn": True, "withdrawn_reason": reason}}}}}

    APIX_ACS = ["Event Rate of Composite of Adjudicated Major Bleeding and Clinically "
                "Relevant Non-Major Bleeding During the Treatment Period",
                "Percentage of Participants Who Had Composite of ISTH-Defined Major and "
                "Clinically-relevant Non-major (CRNM) Bleeding Events"]
    RIVA_ACS = ["Thrombolysis in Myocardial Infarction (TIMI) Clinically Significant "
                "Bleeding Events (Primary Safety)",
                "The Percentage of Patients With the Composite Endpoint of Cardiovascular "
                "Death, Myocardial Infarction, or Stroke"]
    MIX = "bleeding and efficacy endpoints pooled"
    cases = [
        ("FOUNDING APIXABAN_ACS: the reason is FALSE, both trials register bleeding",
         obj(MIX, APIX_ACS), "FAIL"),
        ("FOUNDING RIVAROXABAN_ACS: the IDENTICAL sentence, and here it is TRUE",
         obj(MIX, RIVA_ACS), "PASS"),
        ("a withdrawal whose reason claims no mixture is NOT_APPLICABLE, not a pass",
         obj("the trials count different composites", RIVA_ACS), "NOT_APPLICABLE"),
        ("no recorded definitions is UNCHECKABLE, never a pass",
         obj(MIX, ["", ""]), "UNCHECKABLE"),
        ("a live pool is NOT_APPLICABLE",
         {"inputs": {"trials": []},
          "results": {"by_outcome": {"o": {"pooled": {"point": 0.8}}}}}, "NOT_APPLICABLE"),
    ]
    for label, o, want in cases:
        v, why, _ = assess(o)
        good = v == want
        ok &= good
        print("  %-64s -> %-15s (want %-15s) %s"
              % (label[:64], v, want, "correct" if good else "WRONG"))
        if not good:
            print("        " + why[:170])
    print("\nWHAT A FAILURE WOULD LOOK LIKE: the two founding cases returning the same "
          "verdict. They carry the IDENTICAL reason sentence and differ only in what the "
          "registrations say, so a gate that pattern-matches the words cannot tell them "
          "apart -- and telling them apart is the entire job.")
    print("-> SELFTEST PASS" if ok else "-> SELFTEST FAILED")
    return 0 if ok else 1


def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] == "--selftest":
        return selftest()
    paths = sys.argv[1:]
    if paths[0] == "--corpus":
        repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        paths = [p for p in sorted(glob.glob(os.path.join(repo, "ssot", "*", "*.json")))
                 if os.path.basename(p)[:-5] == os.path.basename(os.path.dirname(p))]
    tally, worst = {}, 0
    for p in paths:
        try:
            obj = json.load(open(p, encoding="utf-8"))
        except Exception:
            continue
        v, why, detail = assess(obj)
        tally[v] = tally.get(v, 0) + 1
        if v in ("FAIL", "UNCHECKABLE") or len(paths) == 1:
            print("%s\n  -> %s  %s" % (os.path.basename(p), v, why[:180]))
            for n, s, e in detail:
                if s is not None:
                    print("     %-24s safety=%-5s efficacy=%s" % (n[:24], s, e))
        if v == "FAIL":
            worst = 1
    if len(paths) > 1:
        print("\nobjects: %d" % len(paths))
        for k in sorted(tally):
            print("  %-16s %d" % (k, tally[k]))
        print("  NOT_APPLICABLE and UNCHECKABLE are not passes.")
    return worst


if __name__ == "__main__":
    sys.exit(main())
