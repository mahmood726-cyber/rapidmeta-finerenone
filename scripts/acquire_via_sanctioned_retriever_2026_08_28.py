"""Full text for the indexed trials, through the RoB lane's retriever rather than a new one.

WHY NOT A SECOND RETRIEVER. scripts/lane_rob/multiroute_retrieve.py declares itself the only
sanctioned way to record document access, and it is right to: two retrievers over one corpus
produce two access records and no way to tell which a page used. That is the ambiguity the
search lane was split off to prevent, and it would be self-inflicted here.

So this file contributes the part that module does not have -- the identifiers -- and lets it
do the fetching. All 74 DOIs and 36 PMCIDs were extracted from documents THIS LANE ALREADY
HOLDS. As with the 55 PMIDs recovered from registrations, the identifier was never missing;
nobody had read it out.

WHAT IT ADDS OVER THE FIRST PASS. That pass reached 24 of 74 trials with full text. The
remaining 50 sit at abstract level, and the routes most likely to close that gap are the ones
keyed on a PMCID or a DOI, which the first pass did not have.

THE ACCESS RECORD IS THE MODULE'S, NOT MINE. retrieve() returns every route it tried with each
status; that whole record is stored, not just the winner. A document is unreachable only when
every route has been tried and named -- never on one index's say-so.
"""
import hashlib
import io
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "scripts", "lane_rob"))
import multiroute_retrieve as MR                      # noqa: E402  the sanctioned retriever

IDS = os.path.join(REPO, "outputs", "_acq_ids.json")
STORE = os.path.join(REPO, "evidence", "acquisition")
OUT = os.path.join(REPO, "out", "acquisition_fulltext_2026_08_28.json")
TODAY = "2026-08-28"


def main():
    raw = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                           write_through=True)

    def say(s):
        raw.write(s + chr(10))
        raw.flush()

    start = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    count = int(sys.argv[2]) if len(sys.argv) > 2 else 10

    ids = json.load(io.open(IDS, encoding="utf-8"))
    keys = sorted(ids)
    batch = keys[start:start + count]
    say("trials: %d   batch %d..%d (%d)" % (len(keys), start, start + len(batch), len(batch)))

    rows = []
    for nct in batch:
        v = ids[nct]
        d = os.path.join(STORE, nct)
        os.makedirs(d, exist_ok=True)
        # already have full text from the first pass? then do not refetch.
        if os.path.exists(os.path.join(d, "pmc.xml")):
            rows.append({"nct": nct, "skipped": "full text already held from the first pass"})
            say("  %-13s already holds full text" % nct)
            continue
        rec = MR.retrieve(pmcid=v.get("pmcid"), pmid=v.get("pmid"), doi=v.get("doi"),
                          out_dir=d, save_as="fulltext")
        got = rec.get("route")
        chars = rec.get("rendered_chars") or 0
        sha = None
        saved = rec.get("saved_to")
        if saved and os.path.exists(saved):
            b = io.open(saved, "rb").read()
            sha = hashlib.sha256(b).hexdigest()
        rows.append({"nct": nct, "route": got, "rendered_chars": chars,
                     "saved_to": (os.path.relpath(saved, REPO).replace("\\", "/")
                                  if saved else None),
                     "sha256": sha, "retrieved_utc": TODAY,
                     "attempts": rec.get("attempts", [])})
        say("  %-13s %s" % (nct, MR.summarise(rec)[:96]))

    old = {"rows": []}
    if os.path.exists(OUT):
        try:
            old = json.load(io.open(OUT, encoding="utf-8"))
        except ValueError:
            pass
    done = set(r["nct"] for r in rows)
    old["rows"] = [r for r in old.get("rows", []) if r["nct"] not in done] + rows
    old["retriever"] = "scripts/lane_rob/multiroute_retrieve.py -- the sanctioned module; " \
                       "this lane supplied identifiers and storage only"
    old["identifiers"] = "74 DOIs and 36 PMCIDs extracted from documents this lane already " \
                         "held; none required a new search"
    json.dump(old, io.open(OUT, "w", encoding="utf-8"), indent=1)

    hit = len([r for r in rows if r.get("route")])
    skip = len([r for r in rows if r.get("skipped")])
    say("")
    say("SUMMARY batch=%d..%d trials=%d fulltext=%d already_held=%d none=%d"
        % (start, start + len(batch), len(batch), hit, skip,
           len(batch) - hit - skip))
    return 0


if __name__ == "__main__":
    sys.exit(main())
