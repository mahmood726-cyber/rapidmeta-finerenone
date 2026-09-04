# -*- coding: utf-8 -*-
"""Publish the RETRIEVAL remainder per source, which no object has ever carried.

THE DIAGNOSIS THAT DECIDED THIS DESIGN, and it arrived late enough to change the build.

`k_unscreened_remainder` is NOT WRONG. It is a SCREENING remainder: how many candidates that
entered the cascade went unscreened. Both objects that publish one are correct.

    sglt2-hf                 k0_surfaced 56    k_unscreened_remainder 0
                             "Was 39, then 32 after the role correction; all 32 screened."
    early-rhythm-control-af  k0_surfaced 959   k_unscreened_remainder 88
                             88 were read by ONE seat, and one seat is not a screen.

The question NOBODY ANSWERS is different: **how many records did a search return that never
entered the cascade at all?** sglt2-hf's PubMed search returned 1,452 and retrieved 50. The
other 1,402 were never surfaced, never role-located, never screened — they are not in `k0` and
they are not in the screening remainder either. THERE IS NO FIELD FOR THEM.

    A TRUE STATEMENT ABOUT SCREENING, STANDING WHERE A READER MEETS A COMPLETENESS CLAIM.
    The page renders "unscreened remainder 0." and contains 1402 zero times.

SO THIS IS ADDITIVE AND OVERWRITES NOTHING. An earlier plan would have recomputed
`k_unscreened_remainder` as the sum of per-source remainders. That would have replaced
early-rhythm-control-af's honest 88 -- the only correct aggregate in the corpus -- with 0,
destroying the one number that got it right in the name of fixing the ones that did not.
**The most exposed of the four steps, removing a published number, is not performed at all.**

WHAT IS WRITTEN
    per source   `records_not_retrieved` and `records_not_retrieved_basis`
    per object   `search.retrieval_remainder`  {state, total, by_source, _scope, _not}

THE FOURTH STATE, AND THE RULE IT ENFORCES. Eight source rows record a search that RAN and
never say how many records came back. Their remainder cannot be derived and a 0 written there
would be an invention, so they are written `NOT_RECORDED` and the object's retrieval remainder
becomes `NOT_PROVABLE` rather than a number.

    AN ABSENCE MUST NOT BECOME A PROVEN ZERO. A SUM OVER A SILENT FIELD IS NOT A SMALLER
    SUM -- IT IS NOT A SUM.

WHAT THIS DOES NOT CLAIM. Not that a search was well aimed, not that the retrieved records
were the right ones, and NOTHING about completeness. `_not` on every block says so in the
object, because a new field that reads like a completeness claim would recreate the defect one
name over.
"""
from __future__ import annotations

import io
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from instrument_controls import require_controls  # noqa: E402

if hasattr(sys.stdout, "buffer") and getattr(sys.stdout, "encoding", "").lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
PAGE_MAP = ROOT / "ssot" / "PAGE_MAP.json"

TOTAL_KEYS = ("total_count", "total_reported", "totalCount", "total")
RETURNED_KEYS = ("records_returned", "returned", "records_returned_total", "count")
NOT_RECORDED = "NOT_RECORDED"
NOT_EXECUTED = "NOT_EXECUTED"
# Objects record these numbers under several names, and two of them carry the value as
# PROSE with the integer leading: "331 of 331 (idlist length 331 at retmax=1000)". Reading
# only int-typed fields called the best-documented record in the corpus silent.
TOTAL_KEYS = TOTAL_KEYS + ("hit_count",)
RETURNED_KEYS = RETURNED_KEYS + ("records_retrieved",)

SCOPE = ("Records a SEARCH returned and this object never retrieved. It is NOT the screening "
         "remainder: k_cascade.k_unscreened_remainder counts candidates that ENTERED the "
         "cascade and went unscreened, and both are published because they answer different "
         "questions.")
NOT_CLAIM = ("This is not a completeness claim. It says how many records were returned and "
             "not retrieved -- nothing about whether the query was well aimed, nor whether "
             "the retrieved records were the right ones.")


def _not_executed(db):
    """True when the object DECLARES this source and says it was never searched."""
    for k in ("query_as_executed", "tool", "state"):
        v = db.get(k)
        if isinstance(v, str) and "NOT EXECUTED" in v.upper():
            return True
    return False


def _num(d, keys):
    """(key, int) taking a leading integer out of an int or a prose string."""
    for k in keys:
        v = d.get(k)
        if isinstance(v, bool):
            continue
        if isinstance(v, int):
            return k, v
        if isinstance(v, str):
            m = re.match(r"\s*(\d+)", v)
            if m:
                return k, int(m.group(1))
    return None, None


def _first(d, keys):
    for k in keys:
        if k in d and d[k] is not None:
            return k, d[k]
    return None, None


def classify(db):
    """(state, remainder, basis) for one recorded source. Four states, not two.

    NOT_EXECUTED and NOT_RECORDED ARE DIFFERENT CLAIMS ABOUT THE WORLD, and the first version
    of this file collapsed them -- committing, one commit after the gate that catches it, the
    exact defect this lane exists to remove. Six of the eight rows it called "a search that
    RAN and did not say what it returned" say `query_as_executed: "NOT EXECUTED FOR THIS
    TOPIC"`. The search never ran. The basis sentence was false on six rows out of eight.

        NOT_EXECUTED   the source was declared and never searched. It has NO retrieval
                       remainder -- not zero. Nothing was returned, so nothing went
                       unretrieved, and reading that as 0 would let "we never searched PubMed"
                       stand as "PubMed contributed no unexamined records".
        NOT_RECORDED   the search RAN and the count is missing.

    AND THE NUMBER CAN BE PROSE. arni-hfref records `hit_count: "331 - read from
    esearchresult.count, not counted or computed"` and `records_retrieved: "331 of 331 (idlist
    length 331 at retmax=1000)"` -- both executed, both fully retrieved, remainder 0. Reading
    only int-typed fields under two key names reported the corpus's most carefully documented
    search record as silent. A LEADING INTEGER IS TAKEN, AND THE WHOLE STRING IS QUOTED IN THE
    BASIS so a reader can check what it was taken from.
    """
    if _not_executed(db):
        return ("NOT_EXECUTED", None,
                "NOT_EXECUTED. This source is declared and was never searched (%r). It has no "
                "retrieval remainder: nothing was returned, so nothing went unretrieved. That "
                "is NOT a remainder of zero -- the records this source would have surfaced "
                "were never surfaced at all."
                % str(db.get("query_as_executed") or db.get("tool"))[:60])
    tk, total = _num(db, TOTAL_KEYS)
    rk, returned = _num(db, RETURNED_KEYS)
    existing = db.get("records_not_retrieved")
    if isinstance(existing, int):
        return "RECORDED", existing, None
    if total is not None and returned is not None:
        return ("COMPUTABLE", total - returned,
                "Derived: %s (%d) minus %s (%d). Both are this object's own recorded numbers%s."
                % (tk, total, rk, returned,
                   "" if isinstance(db.get(tk), int) else
                   ", read as the leading integer of %r and %r"
                   % (str(db.get(tk))[:44], str(db.get(rk))[:44])))
    return ("NOT_ASSESSABLE", None,
            "NOT_RECORDED. This source records a search that RAN and does not state how many "
            "records it returned, so the remainder cannot be derived. A zero here would be an "
            "invention: an absence is not a proven zero.")


def apply_to(obj):
    """Return (changed, report). Mutates obj in place when changed."""
    dbs = ((obj.get("search") or {}).get("databases")) or []
    if not dbs:
        return False, None
    by_source, states, total = {}, [], 0
    silent, unexecuted = [], []
    for db in dbs:
        if not isinstance(db, dict):
            continue
        state, rem, basis = classify(db)
        states.append(state)
        name = str(db.get("database") or db.get("tool") or "<unnamed source>")
        if state == "NOT_EXECUTED":
            db["records_not_retrieved"] = NOT_EXECUTED
            db["records_not_retrieved_basis"] = basis
            by_source[name] = NOT_EXECUTED
            unexecuted.append(name)
        elif state == "NOT_ASSESSABLE":
            db["records_not_retrieved"] = NOT_RECORDED
            db["records_not_retrieved_basis"] = basis
            by_source[name] = NOT_RECORDED
            silent.append(name)
        else:
            if state == "COMPUTABLE":
                db["records_not_retrieved"] = rem
                db["records_not_retrieved_basis"] = basis
            by_source[name] = rem
            total += rem

    if silent:
        state, published = "NOT_PROVABLE", NOT_RECORDED
    elif unexecuted:
        state, published = "PROVED_FOR_EXECUTED_SOURCES", total
    else:
        state, published = "PROVED", total
    provable = not silent

    obj.setdefault("search", {})["retrieval_remainder"] = {
        "state": state,
        "total": published,
        "by_source": by_source,
        "sources_not_executed": unexecuted,
        "_scope": SCOPE,
        "_not": NOT_CLAIM,
        "_why_not_provable": (
            "At least one source states a search that RAN and does not say how many records "
            "it returned. A sum containing an unknown is unknown, so no total is published."
            if silent else None),
        "_executed_only": (
            "This total covers the sources that were SEARCHED. %d declared source(s) were "
            "never executed and are named in sources_not_executed. They have no remainder -- "
            "not a remainder of zero -- because nothing was returned to leave unretrieved, "
            "and the records they would have surfaced were never surfaced at all."
            % len(unexecuted) if unexecuted else None),
    }
    return True, {"state": state, "states": states, "total": total if provable else None,
                  "provable": provable, "n_sources": len(by_source)}


def controls():
    """A derivable remainder must be derived; a silent one must NOT become a zero."""
    good = {"search": {"databases": [
        {"database": "a", "records_returned": 50, "total_count": 1452}]}}
    apply_to(good)
    pos = good["search"]["databases"][0]["records_not_retrieved"]

    silent = {"search": {"databases": [{"database": "b", "records_returned": 50}]}}
    apply_to(silent)
    neg = silent["search"]["databases"][0]["records_not_retrieved"]
    return pos, neg


def main(argv):
    write = "--apply" in argv
    pos, neg = controls()
    require_controls(
        "apply_retrieval_remainder",
        ("source with total 1452 and returned 50, remainder written", pos, 1402),
        ("source with returned 50 and NO total, remainder written", neg, 0),
    )

    pm = json.loads(PAGE_MAP.read_text(encoding="utf-8"))
    by_obj = {}
    for page, rel in sorted(pm.items()):
        by_obj.setdefault(rel, []).append(page)

    print("")
    print("%-44s %5s %6s  %-27s %s" % ("OBJECT", "srcs", "total", "state", "per-source"))
    n_changed = 0
    by_state = {}
    for rel, pages in sorted(by_obj.items()):
        p = ROOT / rel
        if not p.exists():
            continue
        raw = io.open(p, encoding="utf-8", newline="").read()
        obj = json.loads(raw)
        changed, rep = apply_to(obj)
        if not changed:
            continue
        n_changed += 1
        by_state[rep["state"]] = by_state.get(rep["state"], 0) + 1
        counts = {}
        for s in rep["states"]:
            counts[s] = counts.get(s, 0) + 1
        print("%-44s %5d %6s  %-27s %s"
              % (p.stem[:44], rep["n_sources"],
                 rep["total"] if rep["provable"] else "n/a",
                 rep["state"],
                 " ".join("%s=%d" % (k, v) for k, v in sorted(counts.items()))))
        if write:
            # BYTE-EXACT APART FROM THE CHANGE. indent=1, ensure_ascii=False and NO trailing
            # newline reproduce these files exactly -- verified by round-tripping sglt2-hf.json
            # unchanged: 378,961 bytes in, 378,961 out, identical. An added trailing newline
            # rewrites the last line of every object, and unexplained churn in a served store
            # object is the thing this project objects to.
            # PRESERVE EACH FILE'S OWN LINE ENDINGS. Some of these objects are stored
            # LF and some CRLF, and imposing one convention rewrites every line of the
            # files that use the other -- 14,277 insertions against 13,999 deletions on
            # the first attempt, in which the actual change was unreviewable.
            eol = chr(13) + chr(10) if (chr(13) + chr(10)) in raw else chr(10)
            with io.open(p, "w", encoding="utf-8", newline=eol) as fh:
                fh.write(json.dumps(obj, indent=1, ensure_ascii=False))

    print("")
    print("objects carrying a search        %d" % n_changed)
    for k in sorted(by_state):
        print("  %-32s %d" % (k, by_state[k]))
    print("")
    if write:
        print("WRITTEN. k_unscreened_remainder was NOT touched on any object -- it is a "
              "SCREENING remainder and is correct where it exists.")
    else:
        print("DRY RUN. Nothing written. Re-run with --apply.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
