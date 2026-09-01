# -*- coding: utf-8 -*-
"""The parts must sum, and a corrupt payload is its own state. Both as GATES, not habits.

⛔ TWO RULES, ONE MODULE, BECAUSE THEY ARE THE SAME DEFECT SEEN FROM TWO SIDES.

    A COMPONENT THAT RENDERS OR COUNTS A SUBSET OF A DECLARED WHOLE MUST REFUSE WHEN THE
    PARTS DO NOT SUM.

    A PAYLOAD THAT WAS FETCHED AND IS UNREADABLE IS NOT A PAYLOAD THAT WAS NEVER FETCHED.

⭐ WHY A HELPER AND NOT A CONVENTION. 253 `except` blocks in this repo return a default
immediately after a file read, and 186 of them are `continue` inside a loop whose entire
output is a COUNT. Every one of those counts is a count of items THAT HAPPENED TO PARSE, and
nothing in the output can show the difference. A convention asking each author to remember
this has already failed 253 times; `screening_ledger.py` enforces it and is the only place
that does. This lifts that enforcement so it can be called.

⚠️ THE INSTANCE THAT PROMPTED IT, and it is the dangerous shape:

    evidence/acquisition/NCT03045406/registry.txt   (CARAVAGGIO)
       HEAD  123,891 b  parses
       WORK   32,768 b  fails at char 32,729   <- 2^15 EXACTLY, a buffer-boundary truncation

NOT a zero-byte file -- a PLAUSIBLE-SIZED one. Every "is it non-zero" check passes it. And
the reader returned None, the same value it returns for a file never fetched, so the sweep
filed a corruption under "no registry payload". A claim derived from a truncated source is
not a claim with a missing source; it is a claim whose source LIED ABOUT ITS COMPLETENESS.
"""
from __future__ import annotations

import json
import os

NO_PAYLOAD = "NO_PAYLOAD"                 # never fetched, or unreadable at the filesystem
RETRIEVED = "RETRIEVED"                   # fetched and parsed
RETRIEVED_CORRUPT = "RETRIEVED_CORRUPT"   # fetched, and it does not parse
RETRIEVED_NO_VALUE = "RETRIEVED_NO_VALUE" # fetched, parsed, and holds nothing


class PartsDoNotSum(ValueError):
    pass


def read_payload(path, parse=json.loads):
    """A payload read that distinguishes the three ways it can fail to give you a value.

    Returns a dict that ALWAYS carries `state`. Never returns a bare None, because a bare
    None is the value that conflated "corrupt" with "absent" in the first place.
    """
    try:
        with open(path, encoding="utf-8") as fh:
            raw = fh.read()
    except OSError as exc:
        return {"state": NO_PAYLOAD, "path": path, "why": str(exc)}
    try:
        value = parse(raw)
    except Exception as exc:                     # noqa: BLE001 -- any parser, any failure
        return {"state": RETRIEVED_CORRUPT, "path": path, "bytes": len(raw),
                "failed_at": getattr(exc, "pos", None), "why": str(exc)[:200],
                # ⭐ THE TELL, RECORDED SO IT IS NOTICED. A truncation at a power of two is
                # a buffer boundary, not a damaged source -- it means something stopped
                # writing, and the bytes that arrived are internally plausible.
                "power_of_two_boundary": (len(raw) & (len(raw) - 1)) == 0 and len(raw) > 0}
    if value in (None, {}, [], ""):
        return {"state": RETRIEVED_NO_VALUE, "path": path, "bytes": len(raw)}
    return {"state": RETRIEVED, "path": path, "bytes": len(raw), "value": value}


def assert_parts_sum(candidates, what="items", **parts):
    """Refuse unless the parts account for every candidate. Raises PartsDoNotSum.

    ⛔ THE POINT IS THE REFUSAL. Reporting "examined 1,443" beside a list of 1,442 is worse
    than reporting nothing: the count REASSURES the reader precisely where the evidence is
    missing. A summary that agrees with itself and not with its rows is not a summary.

        assert_parts_sum(1443, "screened records", examined=1400, corrupt=1, skipped=42)
    """
    total = sum(int(v or 0) for v in parts.values())
    if total != int(candidates):
        raise PartsDoNotSum(
            "%s: the parts do not account for the population -- %s = %d, but %d %s were "
            "offered. A count of what happened to parse is not a count of what exists; the "
            "difference is exactly what this refusal exists to make visible."
            % (what, " + ".join("%s %d" % (k, v) for k, v in sorted(parts.items())),
               total, int(candidates), what))
    return True


def sweep(paths, on_value, what="objects", parse=json.loads):
    """Walk paths with a full accounting. Returns (results, tally) and the tally SUMS.

    Use this instead of `for p in paths: try: ... except: continue`. The corrupt files leave
    the loop but they do NOT leave the denominator.
    """
    results, tally = [], {"examined": 0, "corrupt": 0, "absent": 0, "empty": 0}
    corrupt_paths = []
    for p in paths:
        got = read_payload(p, parse=parse)
        st = got["state"]
        if st == RETRIEVED:
            tally["examined"] += 1
            results.append(on_value(got["value"], p))
        elif st == RETRIEVED_CORRUPT:
            tally["corrupt"] += 1
            corrupt_paths.append(p)
        elif st == NO_PAYLOAD:
            tally["absent"] += 1
        else:
            tally["empty"] += 1
    assert_parts_sum(len(list(paths)) if not hasattr(paths, "__len__") else len(paths),
                     what, **tally)
    tally["corrupt_paths"] = corrupt_paths
    return results, tally


def render_tally(tally, what="objects"):
    """One line a reader can check, naming every kind rather than only the survivors."""
    line = ("%s: %d examined, %d corrupt, %d absent, %d empty"
            % (what, tally["examined"], tally["corrupt"], tally["absent"], tally["empty"]))
    if tally.get("corrupt_paths"):
        line += " | corrupt: " + ", ".join(os.path.basename(p)
                                           for p in tally["corrupt_paths"][:5])
    return line
