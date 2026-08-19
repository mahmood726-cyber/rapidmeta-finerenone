#!/usr/bin/env python3
"""ONE PLACE THAT KNOWS WHAT RETIREMENT LOOKS LIKE.

WHY THIS MODULE EXISTS. A topic can be retired by MERGE, which records `absorbed_by` naming one
survivor, or by SPLIT, which records `split_into` naming several. Eight instruments in this
repository tested retirement themselves, and every one of them was written before the second
form existed. Six of them still read only `absorbed_by`, and four carried the same shape:

    if state == "RETIRED" **and** o.get("absorbed_by"):

**THAT `and` MAKES THE SUCCESSOR FIELD A PRECONDITION FOR RECOGNISING RETIREMENT.** A tombstone
that names its successors under the other key is not merely mislabelled -- it is not seen as
retired at all, and falls through to whatever the code does with a live topic. It cost a
published number: `audit_templated_questions.py` reported "LIVE TOPICS: 139 (retired tombstones
excluded: 10)" when there were ELEVEN tombstones, counting a retired topic among the live ones.

  THE CONCEPT ACQUIRED A SECOND REPRESENTATION AND ONLY ONE WAS KNOWN TO THE CODE. Fixing the
  first instrument to fail did not fix the others; their failure was already latent and merely
  had not been triggered yet. When a domain concept gains a second name, grep for the first one
  EVERYWHERE before assuming the fix is local -- and then, as here, give it one definition
  instead of seven.

THE RULE THIS ENCODES. Retirement is decided by `state` ALONE. The successor is a separate
question with a separate answer, and "retired but the successor is unrecorded" is a real state
that must be reportable -- never silently downgraded to "not retired".
"""
RETIRED = "RETIRED"

# Every key that has ever named a successor. Adding a third retirement route means adding one
# line HERE, and nowhere else.
SUCCESSOR_KEYS = ("absorbed_by", "split_into")
NO_SUCCESSOR = "RETIRED, and no successor is recorded on the tombstone"


def is_retired(o):
    """True if this object is a tombstone. Reads `state` and NOTHING ELSE.

    Deliberately does not consult the successor fields: a tombstone with no successor recorded
    is still a tombstone, and treating it as live is the defect this module exists for.
    """
    return isinstance(o, dict) and str(o.get(RETIRED.lower()) or o.get("state") or
                                       "").upper() == RETIRED


def successors(o):
    """The successor topics as a LIST, however the tombstone spells them. [] if none recorded."""
    if not isinstance(o, dict):
        return []
    for k in SUCCESSOR_KEYS:
        v = o.get(k)
        if not v:
            continue
        return list(v) if isinstance(v, (list, tuple)) else [v]
    return []


def successor_label(o):
    """A human-readable successor string, or an explicit statement that none is recorded.

    NEVER returns None or "" for a retired object -- an empty successor read as falsy is exactly
    how the `and o.get("absorbed_by")` guards lost their tombstones.
    """
    s = successors(o)
    return ", ".join(s) if s else NO_SUCCESSOR


def selftest():
    fails = []

    def ck(n, got, want):
        ok = got == want
        print("  %-64s %s  %r" % (n, "ok" if ok else "FAIL", got))
        if not ok:
            fails.append(n)

    merged = {"state": "RETIRED", "absorbed_by": "omecamtiv-heartfail"}
    split = {"state": "RETIRED", "split_into": ["a-treatment", "a-surgical"]}
    bare = {"state": "RETIRED"}
    live = {"state": None, "inputs": {}}

    print("1. BOTH RETIREMENT ROUTES ARE RECOGNISED:")
    ck("merged", is_retired(merged), True)
    ck("split", is_retired(split), True)

    print("\n2. AND THE ONE THAT COST A PUBLISHED NUMBER -- retirement is decided by `state`")
    print("   ALONE, so a tombstone with NO successor recorded is still retired:")
    ck("bare tombstone is retired", is_retired(bare), True)
    ck("...and says so rather than returning an empty string",
       successor_label(bare), NO_SUCCESSOR)
    ck("...and the old guard `state==RETIRED and absorbed_by` would have said",
       bool(bare.get("state") == "RETIRED" and bare.get("absorbed_by")), False)

    print("\n3. SUCCESSORS COME BACK AS A LIST WHICHEVER KEY HOLDS THEM:")
    ck("merge -> one", successors(merged), ["omecamtiv-heartfail"])
    ck("split -> several", successors(split), ["a-treatment", "a-surgical"])
    ck("label joins them", successor_label(split), "a-treatment, a-surgical")

    print("\n4. A LIVE TOPIC IS NOT RETIRED, and non-objects do not crash:")
    ck("live", is_retired(live), False)
    ck("None", is_retired(None), False)
    ck("successors of a live topic", successors(live), [])

    print("\n%s" % ("SELFTEST FAILED: %s" % fails if fails else "SELFTEST PASSED"))
    return 1 if fails else 0


if __name__ == "__main__":
    import io
    import sys
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.exit(selftest())
