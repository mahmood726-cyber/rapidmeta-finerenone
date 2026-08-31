# -*- coding: utf-8 -*-
"""BACKFILL `ids` ONTO EVERY SEARCH RECORD -- with a set where one survives, null where none does.

WHAT A SEARCH RECORD IS, IN THIS CORPUS. `ssot/<topic>/<topic>.json -> search.databases[]`.
40 entries across 18 objects on 2026-08-31, and NOT ONE of them carried an identifier list.
Each states a count -- `records_returned: 137` -- that nothing can recompute.

WHAT THIS WRITES. The field defined in scripts/search_ids.py, on ALL 40, never on some:

    ids: [...]   recovered from a file that recorded what that search RETURNED
    ids: null    plus ids_absent_because, naming WHICH of two very different things it is

A null with a reason is the honest state and it is the point of writing it. Leaving the key
off entirely is the fourth state -- a writer who never considered the field -- and it is
indistinguishable, to `dict.get`, from a writer who looked and found nothing. Writing null
everywhere else is what makes a later FIELD_ABSENT a detectable regression rather than the
default condition of the corpus.

WHAT MAY BE USED AS A RECOVERY SOURCE, AND WHAT MAY NOT.

ONLY a file that records what a SEARCH RETURNED. `evidence/2026-08-19-batch1/` also holds
cascade.json, *_screening.json, reconcile.json and a dozen other files full of NCTs -- and
every one of those is a DOWNSTREAM set: what survived a screen, what an adjudication moved,
what a cascade classified. Backfilling `ids` from one of those would write a smaller,
tidier, wrong list into the field and call it recovered. The whole value of the field is
that `records_returned == len(ids)` becomes checkable, and a screened set breaks that
identity while looking entirely plausible.

TWO CONDITIONS FOR A MATCH, NEVER ONE.

    1  the recovered set's LENGTH equals the record's own count, and
    2  the recovered set's QUERY agrees with the record's `query_as_executed`

Count equality alone is a coincidence detector. Three ClinicalTrials.gov queries in this
corpus return 57 records for three different drugs, and a length-only match would have
attributed one topic's identifiers to another and reconciled perfectly afterwards.

AND RE-RUNNING THE QUERY IS NOT A BACKFILL. Registry contents change; a set retrieved today
is not the set a 2026-08-19 count describes. Nothing here goes to the network.

USAGE:  python scripts/backfill_search_ids.py            # report only, writes nothing
        python scripts/backfill_search_ids.py --apply    # writes the objects
"""
import collections
import glob
import io
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import search_ids  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NOT_EXECUTED = re.compile(r"NOT EXECUTED", re.I)

# The count, in every spelling this corpus actually uses. Measured, not assumed: an earlier
# pass keyed on `records_returned` alone and filed arni-hfref's two EXECUTED searches -- which
# spell it `hit_count` / `records_retrieved` -- as never executed, turning two unrecoverable
# records into two that needed no recovery. A field-name assumption is a denominator error.
COUNT_KEYS = ("records_returned", "records_retrieved", "hit_count",
              "total_count", "total_reported")


def count_of(entry):
    for k in COUNT_KEYS:
        v = entry.get(k)
        if isinstance(v, int):
            return v, k
        if isinstance(v, str):
            m = re.match(r"\s*(\d+)", v)
            if m:
                return int(m.group(1)), k
    return None, None


def _tok(s):
    return set(re.findall(r"[a-z0-9]{3,}", str(s).lower()))


def recovery_sources(root):
    """Every id set on disk that records WHAT A SEARCH RETURNED. Nothing downstream."""
    out = []

    p = os.path.join(root, "evidence/2026-08-19-batch1/ablation_split_search.json")
    if os.path.exists(p):
        d = json.load(io.open(p, encoding="utf-8"))
        for topic, v in d.items():
            for q in (v.get("queries") or []):
                if q.get("ids"):
                    out.append({"topic": topic, "ids": list(q["ids"]),
                                "query": json.dumps(q.get("expr"), sort_keys=True),
                                "namespace": "nct", "file": p,
                                "at": "%s/queries[label=%s]/ids"
                                      % (topic, (q.get("label") or "")[:24])})

    p = os.path.join(root, "evidence/2026-08-19-batch1/colchicine_surfaced_137.json")
    if os.path.exists(p):
        d = json.load(io.open(p, encoding="utf-8"))
        # page_1 + page_2 IN THAT ORDER. The pages are the record of the pagination and the
        # order is not decorative: page 2 held CLEAR SYNERGY, the review's largest included
        # trial, and a screen stopped at page 1 would have been 27 per cent short.
        out.append({"topic": d.get("topic"), "ids": list(d["page_1"]) + list(d["page_2"]),
                    "query": d.get("query_as_executed"), "namespace": "nct",
                    "file": p, "at": "page_1 + page_2"})

    p = os.path.join(root, "evidence/2026-08-19-batch1/colchicine_pubmed_523.json")
    if os.path.exists(p):
        d = json.load(io.open(p, encoding="utf-8"))
        out.append({"topic": d.get("topic"), "ids": list(d["pmids"]),
                    "query": d.get("query_as_executed"), "namespace": "pmid",
                    "file": p, "at": "pmids"})
    return out


def match(entry, topic, sources):
    """The one recovery source for this record, or None. BOTH conditions must hold."""
    n, _ = count_of(entry)
    if n is None:
        return None
    ent_q = _tok(entry.get("query_as_executed"))
    for s in sources:
        if len(s["ids"]) != n:
            continue                                   # condition 1: the count
        if not (_tok(topic) & _tok(s["topic"])):
            continue                                   # the record must be about this topic
        src_q = _tok(s["query"])
        if not src_q:
            continue
        # condition 2: the QUERY. A count match alone attributes one topic's identifiers to
        # another and then reconciles perfectly, which is the worst available failure mode.
        if len(src_q & ent_q) / float(len(src_q)) < 0.80:
            continue
        return s
    return None


def plan(root):
    rows, malformed = [], []
    for path in sorted(glob.glob(os.path.join(root, "ssot", "*", "*.json"))):
        try:
            obj = json.load(io.open(path, encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if not isinstance(obj, dict) or not isinstance(obj.get("search"), dict):
            continue
        topic = os.path.basename(path)[:-5]
        for i, e in enumerate(obj["search"].get("databases") or []):
            # THE POSITIVE PROPERTY: a search record IS a mapping. Written this way round
            # deliberately -- `if not isinstance(...): continue` states the absence, and the
            # `continue` then drops the entry out of the population without anything
            # counting it. Anything that is not a record is named in `malformed` and stays
            # visible, because a skip that never reaches the denominator is how a clean
            # number gets manufactured.
            if isinstance(e, dict):
                rows.append({"path": path, "topic": topic, "i": i,
                             "database": e.get("database"), "entry": e})
            else:
                malformed.append({"path": path, "i": i, "type": type(e).__name__})
    if malformed:
        print("  %d databases[] entr%s that is not a mapping and is therefore not a search "
              "record: %s" % (len(malformed), "y" if len(malformed) == 1 else "ies",
                              malformed[:4]))
    srcs = recovery_sources(root)
    for r in rows:
        e = r["entry"]
        n, key = count_of(e)
        r["count"], r["count_key"] = n, key
        if NOT_EXECUTED.search(str(e.get("tool") or "")) or \
           NOT_EXECUTED.search(str(e.get("query_as_executed") or "")):
            r["class"] = "NEVER_EXECUTED"
            r["field"] = search_ids.make(
                None, absent_because="THE SOURCE WAS NOT RUN for this topic. There is no "
                                     "identifier set to recover, and this is not the same "
                                     "fact as a search that ran and returned nothing.")
            continue
        s = match(e, r["topic"], srcs)
        if s:
            r["class"] = "BACKFILLED"
            r["from"] = "%s :: %s" % (os.path.relpath(s["file"], root).replace("\\", "/"),
                                      s["at"])
            r["field"] = search_ids.make(s["namespace"], ids=s["ids"])
            r["field"]["ids_recovered_from"] = r["from"]
        else:
            r["class"] = "EXECUTED_NOT_CAPTURED"
            r["field"] = search_ids.make(
                None, absent_because="THE SEARCH RAN AND ITS IDENTIFIER SET WAS NOT "
                                     "RECORDED. %s %s is what the record states and "
                                     "nothing on disk can recompute it. Re-running the "
                                     "query today would produce a DIFFERENT set -- registry "
                                     "contents change -- so this cannot be recovered, only "
                                     "re-executed as a new record."
                                     % (key, n))
    return rows


def main(apply_it=False):
    rows = plan(REPO)
    tally = collections.Counter(r["class"] for r in rows)
    print("SEARCH RECORDS -- ssot/<topic>/<topic>.json :: search.databases[]")
    print()
    for r in rows:
        st = search_ids.state(r["field"])
        print("  %-46s [%d] %-11s %-24s %s"
              % (r["topic"][:46], r["i"],
                 ("%s=%s" % (r["count_key"] or "-", r["count"])), r["class"], st))
        if r["class"] == "BACKFILLED":
            ok, detail = search_ids.reconcile(r["field"], r["count"])
            print("        <- %s   reconcile=%s  %s" % (r["from"], ok, detail))
            if not ok:
                print("        REFUSED: the recovered set does not reconcile with the "
                      "record's own count. NOT WRITTEN.")
    print()
    print("  candidates             %d" % len(rows))
    for k in ("BACKFILLED", "EXECUTED_NOT_CAPTURED", "NEVER_EXECUTED"):
        print("    %-22s %d" % (k, tally[k]))
    print("    %-22s %d" % ("--- sum", sum(tally.values())))
    assert sum(tally.values()) == len(rows), "examined + skipped + absent != candidates"

    if not apply_it:
        print("\n  REPORT ONLY. Nothing written. Pass --apply to write.")
        return 0

    # REFUSE TO WRITE A SET THAT DOES NOT RECONCILE. A recovered list whose length disagrees
    # with the record's own count is either the wrong list or a wrong count, and writing it
    # would manufacture exactly the false agreement the field exists to make impossible.
    bad = [r for r in rows if r["class"] == "BACKFILLED"
           and not search_ids.reconcile(r["field"], r["count"])[0]]
    if bad:
        print("\n  REFUSED: %d recovered set(s) do not reconcile. Nothing written." % len(bad))
        return 1

    # OTHER LANES ARE LIVE IN THIS REPO AND THEIR WORK IS ALREADY IN THE INDEX. Writing to a
    # path another lane has staged would put an unstaged edit of mine on top of their staged
    # content, where their next `git add` would sweep it in. So a staged path is REFUSED,
    # NAMED, and STAYS IN THE DENOMINATOR -- a skip that never reaches the count is how a
    # clean number gets manufactured.
    staged = set()
    try:
        import subprocess
        # capture_output + an explicit decode, never text=True: a path this repo cannot
        # spell in the console encoding would raise inside the guard, and a guard that
        # crashes is a guard that does not run.
        out = subprocess.run(["git", "diff", "--cached", "--name-only"],
                             cwd=REPO, capture_output=True).stdout
        staged = set(out.decode("utf-8", "replace").split())
    except OSError:
        print("\n  git unavailable -- cannot prove no path is staged by another lane.")
        return 1

    by_file = collections.defaultdict(list)
    for r in rows:
        by_file[r["path"]].append(r)
    held = {p: rs for p, rs in by_file.items()
            if os.path.relpath(p, REPO).replace("\\", "/") in staged}
    if held:
        print()
        for p, rs in sorted(held.items()):
            print("  REFUSED, ANOTHER LANE HOLDS IT IN THE INDEX: %s (%d entr%s not written)"
                  % (os.path.relpath(p, REPO).replace("\\", "/"), len(rs),
                     "y" if len(rs) == 1 else "ies"))
        by_file = {p: rs for p, rs in by_file.items() if p not in held}
    written = sum(len(rs) for rs in by_file.values())
    print("\n  entries written %d + refused-because-staged %d == candidates %d"
          % (written, sum(len(rs) for rs in held.values()), len(rows)))
    assert written + sum(len(rs) for rs in held.values()) == len(rows)

    for path, rs in sorted(by_file.items()):
        with io.open(path, "rb") as fh:
            raw = fh.read()
        obj = json.loads(raw.decode("utf-8"))
        for r in rs:
            obj["search"]["databases"][r["i"]].update(r["field"])
        obj["search"]["ids_field_is"] = (
            "Each databases[] entry carries `ids`: the identifiers THAT SOURCE RETURNED, "
            "verbatim in the source's own namespace, with `ids_normalised` beside it. "
            "`ids: []` means the source ran and returned nothing; `ids: null` means no set "
            "was captured and `ids_absent_because` says which. Defined in "
            "scripts/search_ids.py; checked by scripts/check_search_ids.py.")
        # ⛔ THE FILE'S OWN LINE ENDINGS ARE PRESERVED, AND NEITHER "always LF" NOR THE
        # DEFAULT IS CORRECT.
        #
        # The default translates on Windows, so every LF file came back CRLF -- the
        # whole-file-rewrite class `.gitattributes` was added to remove on 2026-08-31, where
        # five of seven merge conflicts became total and "take ours" would have silently
        # deleted another lane's work. But forcing LF is the SAME defect mirrored: five of
        # the seventeen objects here are already CRLF in HEAD, and rewriting them to LF
        # produces exactly the total diff being avoided.
        #
        # `* text=auto eol=lf` governs what git stores from here on; it does NOT strip CRLF
        # out of blobs that already carry it. So the only rule that adds nothing to any diff
        # is: write back what this file already uses.
        #
        # ⭐ FOUND BY THE BYTE-IDENTITY LIMB OF check_search_ids.py --plant, which failed on
        # the RESTORE. No other check in this chain would have seen it.
        nl = "\r\n" if b"\r\n" in raw else "\n"
        with io.open(path, "w", encoding="utf-8", newline=nl) as fh:
            json.dump(obj, fh, indent=1, ensure_ascii=False)
            fh.write("\n")
        print("  wrote %s (%d entries)" % (os.path.relpath(path, REPO), len(rs)))
    return 0


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.exit(main("--apply" in sys.argv))
