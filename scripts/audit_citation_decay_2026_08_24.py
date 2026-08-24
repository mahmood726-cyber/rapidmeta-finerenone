"""Count-plus-source sentences whose source no longer produces the count.

THE CLASS. A citation is a claim about a RELATIONSHIP between two things -- a number and
where it came from -- and it can fail because EITHER ONE MOVED. That makes it different from
the false-provenance defects found earlier in this project, which were simply wrong when
written (a PMID that never matched the paper). This kind is DECAYED: every component was
true, the combination is false, and nothing in the sentence says which half aged.

    propagate_pi_k1.py: "flagged this across 213 curated dashboards
                         (per scripts/scan_stat_engine_violations.py)"

213 was the count that scanner produced when the line was written. The script then did its
job, and the scanner now reports 0. The number did not become wrong; the ATTRIBUTION did.
A reader who followed the citation got 0 and had every reason to conclude the sentence was
a lie.

WHY A SWEEP AND NOT A ONE-OFF FIX. Nothing in this corpus checks any count-plus-source
sentence. Every one of them decays the moment the work it describes is done, and the ones
most likely to decay are exactly the ones attached to a script whose PURPOSE is to drive the
count to zero. So the highest-risk sentence in the repository is a docstring on a repair
script citing the scanner that motivated the repair.

WHAT THIS DOES AND DOES NOT DO. It finds the sentences and reports THREE STATES. It does not
re-derive the numbers: running every cited script to compare is neither cheap nor safe, and
a mismatch would still need a human to say whether the number aged or the source moved.
Naming them is the deliverable.

    LIVE_SOURCE        the cited path exists and is executable today
    SOURCE_GONE        the cited path does not exist -- the citation cannot be checked at all
    NO_PATH_CITED      a bare number with no source; not decayable, but not checkable either
"""
from __future__ import annotations

import io
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from instrument_controls import require_controls  # noqa: E402

# A number of 2+ digits within 200 characters of a repo-relative path. Both orders, because
# the corpus writes "flagged 213 ... (per scripts/x.py)" and "scripts/x.py found 213".
NUM = r"(?<![\w.])(\d{2,3}(?:,\d{3})*|\d{2,})(?![\w.%])"
PATH = r"((?:scripts|ssot|outputs)/[\w./-]+\.(?:py|json|md))"
NEAR = re.compile(NUM + r"[^\n]{0,160}?" + PATH + r"|" + PATH + r"[^\n]{0,160}?" + NUM)

# Words that make a number a CLAIM ABOUT A POPULATION rather than a parameter or a version.
CLAIMY = re.compile(r"\b(flagged|found|reports?|across|of\s+\d|out of|affected|carrying|"
                    r"holds?|rendered|objects?|pages?|files?|dashboards?|reviews?|"
                    r"guards?|lanes?|rows?|trials?|records?)\b", re.I)

# Places a decayed citation actually costs a reader something.
ROOTS = ("scripts", "ssot")
DOCS = ("PACKET-COMPLETENESS-2026-08-23.md", "PAGE-STANDARD.md", "README.md")


def sentences_with_citations():
    out = []
    seen = set()
    files = []
    for r in ROOTS:
        for dp, _d, names in os.walk(os.path.join(REPO, r)):
            for nm in sorted(names):
                if nm.endswith((".py", ".md")):
                    files.append(os.path.join(dp, nm))
    for d in DOCS:
        p = os.path.join(REPO, d)
        if os.path.isfile(p):
            files.append(p)
    for fp in files:
        rel = os.path.relpath(fp, REPO).replace("\\", "/")
        # SKIP SELF. This file's docstring quotes the founding sentence and an
        # illustrative `scripts/x.py`, and the first run reported that example as a
        # real SOURCE_GONE finding. An instrument that reads itself reports its own
        # examples as data -- the same shape as the `files == 0` check that could
        # never fire because the sweep walks the directory the sweeper lives in.
        if rel == "scripts/audit_citation_decay_2026_08_24.py":
            continue
        try:
            text = io.open(fp, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        # Only prose: docstrings and comments. Code carries numbers next to paths for
        # reasons that are not citations.
        for m in re.finditer(r'"""(.*?)"""|^\s*#(.*)$', text, re.S | re.M):
            blob = m.group(1) or m.group(2) or ""
            for line_no, chunk in enumerate(re.split(r"(?<=[.:])\s+", blob)):
                if not CLAIMY.search(chunk):
                    continue
                hit = NEAR.search(chunk)
                if not hit:
                    continue
                num = hit.group(1) or hit.group(4)
                # A YEAR IS NOT A COUNT. Six of the first 21 hits were the bare
                # string 2026 sitting beside a path in a dated filename or a "written
                # 2026-08-19" note. Left in, they would have made the population look
                # 40% larger than it is -- a false positive rate hidden inside a
                # number I was about to report as a finding.
                if num and num.isdigit() and 2015 <= int(num) <= 2035:
                    continue
                path = hit.group(2) or hit.group(3)
                key = (rel, num, path)
                if key in seen:
                    continue
                seen.add(key)
                out.append({"file": rel, "number": num, "cited": path,
                            "sentence": re.sub(r"\s+", " ", chunk).strip()[:150]})
    return out


def state_of(row):
    if not row["cited"]:
        return "NO_PATH_CITED"
    return ("LIVE_SOURCE" if os.path.isfile(os.path.join(REPO, row["cited"]))
            else "SOURCE_GONE")


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

    # CONTROLS, ON FIXTURE STRINGS. The positive is the sentence that founded this class,
    # in its ORIGINAL decayed wording -- it must be recognised as a citation. The negative
    # is a number beside a path with no population word between them, which is a parameter
    # and not a claim; recognising it would flood the report with version numbers.
    pos_s = ("Sentinel rule flagged this across 213 curated dashboards "
             "(per scripts/scan_stat_engine_violations.py).")
    neg_s = "Retry after 30 seconds using scripts/lane_daemon.py as the entry point."
    pos_ok = bool(CLAIMY.search(pos_s) and NEAR.search(pos_s))
    neg_ok = bool(CLAIMY.search(neg_s) and NEAR.search(neg_s))
    require_controls(
        "citation_decay",
        ("the founding sentence, in its original decayed wording, reads as a citation: %s"
         % pos_ok, pos_ok, True),
        ("a bare number beside a path with no population word must NOT read as a citation; "
         "it does: %s" % neg_ok, neg_ok, True))

    rows = sentences_with_citations()
    tally = {}
    for r in rows:
        r["state"] = state_of(r)
        tally[r["state"]] = tally.get(r["state"], 0) + 1

    print("")
    print("COUNT-PLUS-SOURCE SENTENCES")
    print("")
    print("   a citation is a claim about a RELATIONSHIP. It fails if EITHER side moves,")
    print("   and the sentence never says which. Nothing in this corpus checks any of them.")
    print("")
    for k in ("LIVE_SOURCE", "SOURCE_GONE", "NO_PATH_CITED"):
        print("   %-16s %4d" % (k, tally.get(k, 0)))
    print("   %-16s %4d" % ("total", len(rows)))
    print("")
    gone = [r for r in rows if r["state"] == "SOURCE_GONE"]
    if gone:
        print("   SOURCE_GONE -- the citation cannot be checked at all:")
        for r in gone[:20]:
            print("     %-46s %s -> %s" % (r["file"][:46], r["number"], r["cited"]))
    print("")
    print("   HIGHEST DECAY RISK: a repair script citing the scanner that motivated it.")
    print("   The repair drives the count to zero; the docstring keeps quoting the number")
    print("   from before. Sentences in a file whose name says repair, fix or propagate:")
    risky = [r for r in rows
             if re.search(r"/(repair|fix|propagate|apply|withdraw|rollout)", r["file"])]
    for r in risky[:20]:
        print("     %-52s %-6s %s" % (r["file"][:52], r["number"], r["state"]))
    print("     %d such sentence(s)." % len(risky))
    import json
    json.dump(rows, io.open(os.path.join(REPO, "outputs",
                                         "citation_decay_2026_08_24.json"),
                            "w", encoding="utf-8"), indent=1)


if __name__ == "__main__":
    main()
