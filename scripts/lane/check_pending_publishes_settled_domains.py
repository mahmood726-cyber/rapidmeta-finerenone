#!/usr/bin/env python3
"""A PENDING CERTAINTY MUST PUBLISH THE DOMAINS THAT ARE SETTLED, AND NO LEVEL.

Mahmood's ruling, 2026-08-28: no certainty rating is published while its risk-of-bias
domain is unadjudicated; publish the established downgrade reasons and say certainty is
unrated because bias is unresolved. Filling in a certainty over an unadjudicated
assessment is "the defect with better plumbing", so this check has to fail in BOTH
directions -- on a level that leaks, and on reasoning that is withheld.

TWO ASSERTIONS PER PENDING OUTCOME:
  1. no level reaches the reader   -- no "-> low", no derivation total, cell stays Pending
  2. every settled domain the object holds is named in the comment, with its reason

WHAT IT CANNOT SEE, named rather than implied: it reads the RESOLVER, not the page. A
consumer that drops `comment` would satisfy this check and serve nothing. That is why the
served-bytes probe is run separately and quoted beside it, and it is exactly how
`recorded_level` came to be computed by this module and read by no one.
"""
import io
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "ssot"))
sys.path.insert(0, os.path.join(ROOT, "gates"))
import grade_authority as ga            # noqa: E402
import _harness as H                    # noqa: E402

LEVEL_LEAKS = ("-> low", "-> moderate", "-> high", "-> very low", "total -1", "total -2")


def _controls():
    """POSITIVE: a block with a settled domain must produce a grounds sentence.
    NEGATIVE: a block holding ONLY risk_of_bias must produce nothing -- otherwise the
    check would pass by calling the unadjudicated domain settled, which is the ruling
    read backwards."""
    pos = {"domains": {"imprecision": {"rating": "serious",
                                       "triggers_computed": "the interval crosses the null"}}}
    neg = {"domains": {"risk_of_bias": {"rating": "serious",
                                        "basis_in_sources": "terminated early"}}}
    p = ga._established_grounds(pos, None)
    n = ga._established_grounds(neg, None)
    ok = ("imprecision is rated serious" in p) and (n == "")
    print("CONTROLS, both legs, every run")
    print("  POSITIVE  settled domain          -> published : %s" % bool(p))
    print("  NEGATIVE  risk_of_bias only       -> published : %s  (must be False)" % bool(n))
    print("  CONTROLS PASS: %s\n" % ok)
    return ok


def main():
    if not _controls():
        print("CONTROLS FAILED -- findings below are not reportable.")
        return 3
    objs, _ = H.topic_objects(ROOT)
    kinds = {"pending, holds settled domains": 0, "pending, holds none": 0,
             "not pending": 0}
    findings = []
    for path in objs:
        tid = H.topic_id(path)
        try:
            canon = json.load(io.open(path, encoding="utf-8"))
        except Exception:
            continue
        for oid in ((canon.get("results") or {}).get("by_outcome") or {}):
            try:
                r = ga.resolve(canon, oid)
            except Exception as e:
                findings.append((tid, oid, "resolver raised %s" % type(e).__name__))
                continue
            if r.get("state") != "PENDING":
                kinds["not pending"] += 1
                continue
            comment = r.get("comment") or ""
            if r.get("level") is not None:
                findings.append((tid, oid, "a level reached the reader: %r" % r["level"]))
            for leak in LEVEL_LEAKS:
                if leak in comment.lower():
                    findings.append((tid, oid, "the comment names a level via %r" % leak))
            grade = (((canon.get("results") or {}).get("by_outcome") or {})
                     .get(oid, {}).get("grade") or {})
            dom = grade.get("domains") if isinstance(grade.get("domains"), dict) else {}
            settled = [k for k, v in dom.items()
                       if k != "risk_of_bias" and isinstance(v, dict) and v.get("rating")]
            if not settled:
                kinds["pending, holds none"] += 1
                continue
            kinds["pending, holds settled domains"] += 1
            for name in settled:
                if ("%s is rated" % name.replace("_", " ")) not in comment:
                    findings.append((tid, oid,
                                     "holds a settled %s domain and does not publish it" % name))
    print("kinds in the population, before any count:")
    for k, v in kinds.items():
        print("   %-34s %d" % (k, v))
    print("\nfindings: %d" % len(findings))
    for t, o, w in findings[:25]:
        print("   %-34s %-22s %s" % (t[:34], o[:22], w))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
