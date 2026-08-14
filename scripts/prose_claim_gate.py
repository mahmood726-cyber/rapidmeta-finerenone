"""Validate the SENTENCES against the object, the way the values already are.

The specification is a line from an independent review of this paper:

    "Your guard rails are checking the numbers; nothing is checking the
     sentences."

Every projected number reconciled against its quoted metafor output. No
arithmetic error was found. And in the same document the Discussion opened
"sacubitril/valsartan reduced the hazard" and the Conclusions ended "One trial
establishes this benefit" -- against a pooled interval containing the null; the
Methods said the search was not reproducible while the executed query strings sat
in the object; and three sections said no comparison with published syntheses was
attempted while that comparison was a major section with three tables.

Not one of those is a wrong number. Every one is a wrong sentence, and a numeric
gate cannot see any of them.

THREE CLASSES, because these are the three ways a sentence goes wrong here:

  DIRECTION   a claim of benefit, reduction or superiority made against an
              interval that includes the null.
  EXISTENCE   a claim that something was not done, or is not recorded, when the
              object contains it.
  COUNT       a claim about how many studies, checked by k_consistency_gate.

Usage:
  python prose_claim_gate.py <object.json>
  python prose_claim_gate.py --selftest
"""
import io
import json
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from verdict import Verdict, PASS, FAIL, INVALID, summarise  # noqa: E402

# Wording that asserts the intervention worked. Hedged forms are deliberately
# NOT here: "may reduce", "is compatible with a reduction" and "favours" state
# a direction without asserting it was established.
DIRECTION = [
    r"\breduced the (?:hazard|risk|rate)\b",
    r"\bestablishes? (?:this|the) benefit\b",
    r"\bwas (?:effective|superior)\b",
    r"\bdemonstrat\w+ (?:a )?(?:benefit|reduction|superiority)\b",
    r"\bconfers? a benefit\b",
    r"\bimproves? (?:survival|outcomes)\b",
    r"\bsignificantly (?:reduced|lowered|improved)\b",
]

# Claims that something is absent. Each carries a probe into the object; if the
# probe finds the thing, the sentence is false.
EXISTENCE = [
    (r"no executed query string is recorded",
     lambda d: any((db.get("query_as_executed") or "").strip()
                   for db in (d.get("search") or {}).get("databases") or []),
     "search.databases[].query_as_executed"),
    (r"not reproducible from this document",
     lambda d: any((db.get("query_as_executed") or "").strip()
                   for db in (d.get("search") or {}).get("databases") or []),
     "search.databases[].query_as_executed"),
    (r"does not attempt a formal comparison with previous syntheses",
     lambda d: bool((d.get("published_comparison") or {}).get("checks")),
     "published_comparison.checks"),
    (r"no per-domain RoB-2 assessment exists",
     lambda d: bool((d.get("rob2") or {}).get("trials")),
     "rob2.trials"),
    (r"no risk-of-bias assessment (?:was|has been) (?:performed|done)",
     lambda d: bool((d.get("rob2") or {}).get("trials")),
     "rob2.trials"),
    (r"identification counts .{0,40}(?:unrecoverable|not recorded)",
     lambda d: any(re.search(r"\d", str(db.get("records_retrieved") or ""))
                   for db in (d.get("search") or {}).get("databases") or []),
     "search.databases[].records_retrieved"),
]


def walk(o, p=""):
    if isinstance(o, dict):
        for k, v in o.items():
            yield from walk(v, p + "." + str(k))
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from walk(v, p + "[%d]" % i)
    elif isinstance(o, str):
        yield p, o


# Only this review's own voice. Quoted sources, screening records and the
# correction log all legitimately contain sentences we do not assert.
SKIP = (".screening", ".sources", ".rob2", ".citations", ".claims_corrected",
        ".published_comparison.checks", ".reconciliation", "_corrected",
        ".methodological_authority", "decision_corrected", "quote")


def check(d):
    out = []
    pooled = None
    for res in ((d.get("results") or {}).get("by_outcome") or {}).values():
        pooled = res.get("pooled") or {}
        break
    if not pooled or pooled.get("ci_low") is None:
        return [Verdict("pooled interval available", INVALID,
                        detail="no pooled interval, so a direction claim cannot "
                               "be judged either way")]
    lo, hi = pooled["ci_low"], pooled["ci_high"]
    crosses = lo <= 1.0 <= hi

    strings = [(p, t) for p, t in walk(d)
               if not any(s in p for s in SKIP)]
    # DIRECTION
    hits = []
    for p, t in strings:
        for pat in DIRECTION:
            m = re.search(pat, t, re.I)
            if m:
                hits.append((p, m.group(0)))
    if crosses:
        if hits:
            out.append(Verdict(
                "no unhedged benefit claim against a null-containing interval",
                FAIL,
                detail="pooled %.3f (%.3f to %.3f) INCLUDES 1, but %d claim(s) "
                       "assert benefit: %s"
                       % (pooled["point"], lo, hi, len(hits),
                          "; ".join("%s: %r" % (a.split(".")[-1], b)
                                    for a, b in hits[:4]))))
        else:
            out.append(Verdict(
                "no unhedged benefit claim against a null-containing interval",
                PASS,
                witness="pooled %.3f (%.3f to %.3f) includes 1; scanned %d "
                        "review-voice strings against %d benefit patterns, none "
                        "matched" % (pooled["point"], lo, hi, len(strings),
                                     len(DIRECTION)),
                failure_would_be="a sentence asserting the drug reduced the "
                                 "hazard while the interval contains no effect"))
    else:
        out.append(Verdict("direction claims (interval excludes the null)", PASS,
                           witness="pooled %.3f (%.3f to %.3f) excludes 1, so a "
                                   "benefit claim is supported; %d present"
                                   % (pooled["point"], lo, hi, len(hits)),
                           failure_would_be="n/a while the interval excludes "
                                            "the null"))
    # EXISTENCE
    for pat, probe, where in EXISTENCE:
        said = [(p, t) for p, t in strings if re.search(pat, t, re.I)]
        if not said:
            continue
        try:
            exists = bool(probe(d))
        except Exception:                                 # noqa: BLE001
            out.append(Verdict("existence claim %r" % pat[:38], INVALID,
                               detail="probe into %s raised" % where))
            continue
        if exists:
            out.append(Verdict("existence claim %r" % pat[:38], FAIL,
                               detail="the paper says this is absent, but %s is "
                                      "populated. Stated at %s"
                                      % (where, said[0][0])))
        else:
            out.append(Verdict("existence claim %r" % pat[:38], PASS,
                               witness="claim made at %s and %s is indeed empty"
                                       % (said[0][0], where),
                               failure_would_be="the object containing what the "
                                                "sentence says it does not"))
    return out


def selftest():
    base = {"results": {"by_outcome": {"o": {
        "pooled": {"point": 0.872, "ci_low": 0.746, "ci_high": 1.018}}}}}
    cases = []
    d1 = json.loads(json.dumps(base))
    d1["manuscript"] = {"d": "sacubitril/valsartan reduced the hazard of a first "
                             "cardiovascular death"}
    cases.append(("benefit claim against a null-containing interval", d1, FAIL))
    d2 = json.loads(json.dumps(base))
    d2["manuscript"] = {"d": "One trial establishes this benefit"}
    cases.append(("'establishes this benefit' against the same interval", d2,
                  FAIL))
    d3 = json.loads(json.dumps(base))
    d3["manuscript"] = {"d": "the pooled interval includes no difference and is "
                             "compatible with no effect"}
    cases.append(("NEGATIVE: an honest statement of a null result", d3, PASS))
    d4 = json.loads(json.dumps(base))
    d4["manuscript"] = {"d": "No executed query string is recorded for any "
                             "database."}
    d4["search"] = {"databases": [{"query_as_executed": "(sacubitril[tiab])"}]}
    cases.append(("says no query recorded while the object holds one", d4, FAIL))
    d5 = json.loads(json.dumps(base))
    d5["manuscript"] = {"d": "No executed query string is recorded for any "
                             "database."}
    d5["search"] = {"databases": [{"query_as_executed": ""}]}
    cases.append(("NEGATIVE: the same sentence when it is true", d5, PASS))
    d6 = {"results": {"by_outcome": {}}}
    cases.append(("no pooled interval -> INVALID, not PASS", d6, INVALID))
    # a benefit claim is legitimate when the interval supports it
    d7 = json.loads(json.dumps(base))
    d7["results"]["by_outcome"]["o"]["pooled"] = {"point": 0.839,
                                                  "ci_low": 0.743,
                                                  "ci_high": 0.948}
    d7["manuscript"] = {"d": "sacubitril/valsartan reduced the hazard"}
    cases.append(("NEGATIVE: benefit claim when the interval excludes the null",
                  d7, PASS))
    ok = True
    print("=== the prose-claim gate ===")
    for name, dd, want in cases:
        vs = check(dd)
        got = (FAIL if any(v.state == FAIL for v in vs)
               else INVALID if any(v.state == INVALID for v in vs) else PASS)
        good = got == want
        ok &= good
        print("  %-58s %-8s expected=%-8s %s"
              % (name[:58], got, want, "correct" if good else "WRONG"))
    print("\nprose-claim gate correct on every case:", ok)
    return 0 if ok else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        raise SystemExit(selftest())
    d = json.load(open(sys.argv[1], encoding="utf-8"))
    raise SystemExit(summarise(check(d), "prose:"))
