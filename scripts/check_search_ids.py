# -*- coding: utf-8 -*-
"""GATE THE `ids` FIELD ACROSS THE CORPUS -- and prove every limb of it can FAIL.

WHAT IT REFUSES ON, per search record at `ssot/<topic>/<topic>.json :: search.databases[]`:

  FIELD_ABSENT           no `ids` key at all. `rec.get("ids")` cannot tell this from an
                         explicit null, which is the silent default wearing the shape of
                         the bug it hides. This limb tests key MEMBERSHIP.
  NULL_WITHOUT_REASON    `ids: null` and no `ids_absent_because`. An unexplained null is
                         indistinguishable from a writer who never looked.
  EMPTY_WITH_A_REASON    `ids: []` beside an `ids_absent_because`. Those are contradictory
                         claims: one says the source ran and found nothing, the other says
                         we captured nothing. Exactly the conflation this field exists for.
  COUNT_MISMATCH         the record's own count is not len(ids). The count we publish,
                         finally checkable against the set behind it.
  DUPLICATE              the same identifier twice. It keeps the count right and the total
                         right and is invisible to every check but a set comparison.
  NORMALISED_DESYNC      ids_normalised is not the position-by-position normalisation of
                         ids. Verbatim and normalised are stored BOTH; if they drift, the
                         verbatim copy has stopped being evidence.

⛔ A CHECK NOT WATCHED TO FAIL IS NOT A CHECK. `--plant` takes each limb, plants its
violation IN A REAL FILE IN THIS REPO, runs the gate, asserts it REFUSES, restores the file
and asserts the restoration is byte-identical and the gate passes again. Three instruments
in this project have shipped with only one reachable outcome; a fixture pair proves the
logic and says nothing about whether the limb is wired to anything.

⚠️ AND THE DISTRIBUTION IS PRINTED OVER THE WHOLE POPULATION BEFORE ANY GATE IS WIRED,
because a fixture tells you the logic works and nothing at all about the corpus verdict.

USAGE:  python scripts/check_search_ids.py           # scan + distribution
        python scripts/check_search_ids.py --plant   # plant/restore proof for every limb
"""
import collections
import glob
import hashlib
import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import search_ids  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COUNT_KEYS = ("records_returned", "records_retrieved", "hit_count",
              "total_count", "total_reported")


def count_of(entry):
    import re
    for k in COUNT_KEYS:
        v = entry.get(k)
        if isinstance(v, int):
            return v
        if isinstance(v, str):
            m = re.match(r"\s*(\d+)", v)
            if m:
                return int(m.group(1))
    return None


def check_entry(e):
    """[] of refusal codes for one search record. Empty means it passes."""
    st = search_ids.state(e)
    bad = []
    if st == search_ids.FIELD_ABSENT:
        return ["FIELD_ABSENT"]
    if st == search_ids.MALFORMED:
        return ["MALFORMED"]
    has_reason = bool(e.get(search_ids.IDS_ABSENT_BECAUSE))
    if st == search_ids.NOT_CAPTURED and not has_reason:
        bad.append("NULL_WITHOUT_REASON")
    if st == search_ids.RAN_AND_RETURNED_NOTHING and has_reason:
        bad.append("EMPTY_WITH_A_REASON")
    if st in (search_ids.CAPTURED, search_ids.RAN_AND_RETURNED_NOTHING):
        ok, detail = search_ids.reconcile(e, count_of(e))
        if ok is False:
            bad.append("DUPLICATE" if "DUPLICATE" in detail else
                       "NORMALISED_DESYNC" if "normalis" in detail else "COUNT_MISMATCH")
    return bad


def scan(root):
    rows = []
    for path in sorted(glob.glob(os.path.join(root, "ssot", "*", "*.json"))):
        try:
            obj = json.load(io.open(path, encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if not isinstance(obj, dict) or not isinstance(obj.get("search"), dict):
            continue
        for i, e in enumerate(obj["search"].get("databases") or []):
            if isinstance(e, dict):
                rows.append({"path": path, "i": i, "topic": os.path.basename(path)[:-5],
                             "database": e.get("database"),
                             "state": search_ids.state(e), "bad": check_entry(e)})
    return rows


def report(root, quiet=False):
    rows = scan(root)
    states = collections.Counter(r["state"] for r in rows)
    fails = [r for r in rows if r["bad"]]
    if not quiet:
        print("SEARCH RECORDS SCANNED: %d" % len(rows))
        print()
        print("  STATE DISTRIBUTION OVER THE POPULATION (not a fixture):")
        for k in (search_ids.CAPTURED, search_ids.RAN_AND_RETURNED_NOTHING,
                  search_ids.NOT_CAPTURED, search_ids.FIELD_ABSENT, search_ids.MALFORMED):
            print("    %-26s %d" % (k, states[k]))
        print("    %-26s %d" % ("--- sum", sum(states.values())))
        assert sum(states.values()) == len(rows), "states do not sum to the population"
        print()
        if fails:
            print("  REFUSED: %d" % len(fails))
            for r in fails:
                print("    %-40s [%d] %-34s %s"
                      % (r["topic"][:40], r["i"], str(r["database"])[:34],
                         ",".join(r["bad"])))
        else:
            print("  REFUSED: 0")
    return len(fails), rows


# ------------------------------------------------------------------- plant the defect

def _sha(path):
    with io.open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def _find(rows, state):
    for r in rows:
        if r["state"] == state and not r["bad"]:
            return r
    return None


def plant():
    """Every limb: plant the violation in a REAL file, watch it FAIL, restore, assert."""
    fails = []

    def ck(name, got, want):
        ok = got == want
        print("    %-62s %s  %r" % (name, "ok" if ok else "FAIL", got))
        if not ok:
            fails.append(name)

    n0, rows = report(REPO, quiet=True)
    base = sorted("%s[%d]:%s" % (r["topic"], r["i"], ",".join(r["bad"]))
                  for r in rows if r["bad"])
    print("BASELINE: %d search records, %d refused." % (len(rows), n0))
    # ⚠️ THE BASELINE IS NOT ZERO AND IS NOT ASSERTED TO BE. Two records live in a file
    # another lane holds in the index, so the backfill REFUSED to write them and they are
    # honestly FIELD_ABSENT. Asserting a clean baseline would have meant either weakening
    # the gate or writing into another lane's staged file. Instead the baseline is PINNED by
    # name, so a plant is proven by the gate getting STRICTLY WORSE than a known set -- and
    # any NEW refusal appearing here fails this selftest just as loudly.
    for b in base:
        print("    baseline refusal (pinned): %s" % b)
    ck("baseline refusals are exactly the known set", base, sorted([
        "azilsartan-chlorthalidone-vs-olmesartan-hctz[0]:FIELD_ABSENT",
        "azilsartan-chlorthalidone-vs-olmesartan-hctz[1]:FIELD_ABSENT"]))

    cap = _find(rows, search_ids.CAPTURED)
    nul = _find(rows, search_ids.NOT_CAPTURED)
    if not cap or not nul:
        print("  NO REAL RECORD IN A REQUIRED STATE -- the plants cannot run, and a plant "
              "that cannot run is not a pass.")
        return 1
    print("  planting into REAL files:")
    print("    CAPTURED     %s [%d]" % (os.path.relpath(cap["path"], REPO), cap["i"]))
    print("    NOT_CAPTURED %s [%d]" % (os.path.relpath(nul["path"], REPO), nul["i"]))
    print()

    def run_plant(label, target, mutate, expect):
        path = target["path"]
        before_sha = _sha(path)
        # THE ORIGINAL IS HELD AS BYTES AND RESTORED AS BYTES. Reading text and writing it
        # back translates line endings on Windows, so a "restore" would silently rewrite the
        # file and the byte-identity assertion below would be measuring the harness rather
        # than the plant. Not hypothetical: this limb is what caught the backfill writing
        # CRLF into LF files.
        with io.open(path, "rb") as fh:
            original = fh.read()
        obj = json.loads(original.decode("utf-8"))
        mutate(obj["search"]["databases"][target["i"]])
        # The file's own endings, same rule as the backfill writer: neither the default nor
        # a forced LF is correct, because five of these objects are CRLF in HEAD already.
        nl = "\r\n" if b"\r\n" in original else "\n"
        with io.open(path, "w", encoding="utf-8", newline=nl) as fh:
            json.dump(obj, fh, indent=1, ensure_ascii=False)
            fh.write("\n")
        try:
            got = [r for r in scan(REPO)
                   if r["path"] == path and r["i"] == target["i"]][0]["bad"]
            ck("PLANT %-20s -> the gate refuses with %s" % (label, expect),
               expect in got, True)
            n, _ = report(REPO, quiet=True)
            ck("PLANT %-20s -> the corpus is strictly worse than baseline" % label,
               n, n0 + 1)
        finally:
            with io.open(path, "wb") as fh:
                fh.write(original)
        ck("RESTORED %-17s -> the file is byte-identical" % label, _sha(path), before_sha)
        n, _ = report(REPO, quiet=True)
        ck("RESTORED %-17s -> the corpus returns to baseline" % label, n, n0)

    def _del_ids(e):
        e.pop(search_ids.IDS, None)
    run_plant("FIELD_ABSENT", nul, _del_ids, "FIELD_ABSENT")

    def _del_reason(e):
        e.pop(search_ids.IDS_ABSENT_BECAUSE, None)
    run_plant("NULL_WITHOUT_REASON", nul, _del_reason, "NULL_WITHOUT_REASON")

    # ⭐ THE ONE THIS FIELD EXISTS FOR: null and [] made interchangeable.
    def _null_to_empty(e):
        e[search_ids.IDS] = []
        e[search_ids.IDS_NORMALISED] = []
    run_plant("EMPTY_WITH_A_REASON", nul, _null_to_empty, "EMPTY_WITH_A_REASON")

    def _drop_one(e):
        e[search_ids.IDS] = e[search_ids.IDS][:-1]
        e[search_ids.IDS_NORMALISED] = e[search_ids.IDS_NORMALISED][:-1]
    run_plant("COUNT_MISMATCH", cap, _drop_one, "COUNT_MISMATCH")

    # ⭐ THE LIMB NO OTHER CHECK REACHES. A duplicate keeps the LENGTH right, so the record's
    # own count still reconciles and every arithmetic check still passes. Only a set
    # comparison sees it, and it silently inflates any denominator built from the list.
    def _dup(e):
        e[search_ids.IDS][1] = e[search_ids.IDS][0]
        e[search_ids.IDS_NORMALISED][1] = e[search_ids.IDS_NORMALISED][0]
    run_plant("DUPLICATE", cap, _dup, "DUPLICATE")

    def _desync(e):
        e[search_ids.IDS_NORMALISED][0] = "not-the-normalisation-of-anything"
    run_plant("NORMALISED_DESYNC", cap, _desync, "NORMALISED_DESYNC")

    # ------------------------------------------------------------------ the derivation
    #
    # ⛔ THE CONFLATION IS NOT COSMETIC AND THIS PROVES IT ON REAL DATA. A source we did not
    # capture, entered as an EMPTY SET, is reported as "returned 0, unique 0" -- a statement
    # about the literature. Entered as NULL it is reported as SKIPPED -- a statement about
    # us. The two produce different output from the same underlying ignorance.
    print()
    print("  THE CONFLATION, MEASURED ON A REAL OBJECT:")
    obj = json.load(io.open(nul["path"], encoding="utf-8"))
    dbs = obj["search"]["databases"]
    recs = [(str(e.get("database")), e) for e in dbs]
    honest = search_ids.unique_yield(recs)
    ck("as written, the uncaptured source is SKIPPED, not counted",
       len(honest["sources_skipped"]) >= 1, True)
    ck("and skipped + counted == candidates",
       honest["sources_counted"] + len(honest["sources_skipped"]), honest["candidates"])
    lying = json.loads(json.dumps(dbs))
    lying[nul["i"]][search_ids.IDS] = []
    lying[nul["i"]][search_ids.IDS_NORMALISED] = []
    fake = search_ids.unique_yield([(str(e.get("database")), e) for e in lying])
    ck("conflated to [], it enters per_source as a claim about the world",
       str(dbs[nul["i"]].get("database")) in fake["per_source"], True)
    ck("and the two disagree about how many sources were counted",
       fake["sources_counted"] != honest["sources_counted"], True)

    print()
    print("SELFTEST %s" % ("FAILED: %s" % fails if fails else "PASSED"))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    if "--plant" in sys.argv:
        sys.exit(plant())
    n, _ = report(REPO)
    sys.exit(1 if n else 0)
