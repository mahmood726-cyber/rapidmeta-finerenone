"""How many published reviews print the per-trial numbers they extracted?

THE SECOND HALF OF THE AUDITABILITY PAIR. The first half is that 95% of full-text reviews
name no trial registration, so a reader cannot tell WHICH trials were included. This is the
other, independent reason the same review cannot be checked: it never prints WHAT it
extracted from them.

Either alone stops an audit. Together they are much harder to argue with, because a review
could in principle fix one and still be uncheckable.

A pilot on five reviews found one in five printing per-trial numbers. This runs the same test
on the 300 already sampled, with the same denominator discipline: full text only, records
with a real reference list, never counting a thin PMC stub as a review that prints nothing.

WHAT COUNTS AS A PER-TRIAL OUTCOME TABLE, and the distinction cost an instrument failure to
learn:

  * a table with rows carrying a TRIAL IDENTITY -- an NCT id, a year, or a name longer than
    an endpoint acronym
  * at least four numeric cells in such a row, which is the shape of events/denominators for
    two arms

  NOT a characteristics table (rows are trials, but the numbers are ages and counts of
  countries, not outcomes)
  NOT a pooled-by-outcome table. PMC13491898's rows are labelled OS, PFS, ORR, DCR, TRAE:
  one row per OUTCOME with pooled numbers. Reading those as trials produced "0 of 11
  resolved", which looks like a registry failure and is nothing of the kind.

A ZERO FROM A MEASUREMENT WHOSE PRECONDITION IS ABSENT IS THE MOST DANGEROUS NUMBER WE
PRODUCE. It reads as evidence of absence and is absence of evidence, and it always lands
against whichever side the measurement was built to doubt. Hence the guard, and hence the
separate reporting of "no table at all" from "table present, nothing recovered".
"""
import collections
import io
import json
import os
import re
import subprocess
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "scripts"))
import instrument_controls

if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                                  write_through=True)

EFETCH = ("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pmc"
          "&id=%s&retmode=xml")
CACHE = os.path.join(REPO, "outputs", "per_trial_tables_2026_08_25.jsonl")
SRC = {"general": os.path.join(REPO, "outputs",
                               "review_registration_naming_2026_08_25.jsonl"),
       "cochrane": os.path.join(REPO, "outputs",
                                "cochrane_registration_naming_2026_08_25.jsonl")}

NUM = re.compile(r"^-?[\d,]+(?:\.\d+)?$")
NCT = re.compile(r"NCT\d{8}")
YEAR = re.compile(r"(19|20)\d{2}")


def looks_like_trial(label):
    if NCT.search(label or ""):
        return True
    if YEAR.search(label or ""):
        return True
    return len(re.sub(r"[^A-Za-z]", "", label or "")) > 8


def analyse(xml):
    """(has_per_trial_table, n_such_rows, n_tables). None if not full text."""
    if len(re.findall(r"<ref\b", xml)) <= 5:
        return None, 0, 0
    tables = re.findall(r"<table-wrap.*?</table-wrap>", xml, re.S)
    best = 0
    for blk in tables:
        rows = re.findall(r"<tr>(.*?)</tr>", blk, re.S)
        good = 0
        for r in rows:
            cells = [" ".join(re.sub(r"<[^>]+>", " ", c).split())
                     for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", r, re.S)]
            if not cells:
                continue
            nums = [c for c in cells[1:] if NUM.match(c)]
            if len(nums) >= 4 and looks_like_trial(cells[0]):
                good += 1
        best = max(best, good)
    return (best >= 2), best, len(tables)


def control():
    per_trial = ('<article><ref/><ref/><ref/><ref/><ref/><ref/><table-wrap><tr>'
                 '<td>CARMELINA 2019</td><td>209</td><td>3494</td><td>226</td><td>3485</td>'
                 '</tr><tr><td>SAVOR-TIMI 2013</td><td>289</td><td>8280</td><td>228</td>'
                 '<td>8212</td></tr></table-wrap></article>')
    pooled = ('<article><ref/><ref/><ref/><ref/><ref/><ref/><table-wrap><tr>'
              '<td>OS</td><td>0.8</td><td>0.7</td><td>0.9</td><td>0.01</td></tr><tr>'
              '<td>PFS</td><td>0.7</td><td>0.6</td><td>0.8</td><td>0.02</td></tr>'
              '</table-wrap></article>')
    stub = '<article><table-wrap><tr><td>x</td></tr></table-wrap></article>'
    instrument_controls.require_controls(
        "per-trial-table",
        ("a real per-trial outcome table is detected", analyse(per_trial)[0], True),
        ("a POOLED-BY-OUTCOME table must NOT count as per-trial",
         analyse(pooled)[0], True))
    if analyse(stub)[0] is not None:
        raise instrument_controls.ControlFailed(
            "REFUSED: a thin stub was judged instead of being excluded. A stub that prints "
            "no table is not a review that prints no table. NO COUNT IS PRINTED.")
    print("CONTROL (third state) a thin PMC stub is EXCLUDED, not counted as 'no table'")
    return True


def main():
    control()
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 10**9
    done = {}
    if os.path.exists(CACHE):
        for line in io.open(CACHE, encoding="utf-8"):
            try:
                d = json.loads(line)
            except ValueError:
                continue
            done[d["pmcid"]] = d

    todo = []
    for frame, path in SRC.items():
        if not os.path.exists(path):
            continue
        seen = set()
        for line in io.open(path, encoding="utf-8"):
            try:
                d = json.loads(line)
            except ValueError:
                continue
            if d.get("status") == "ok" and d["pmcid"] not in seen:
                seen.add(d["pmcid"])
                todo.append((frame, d["pmcid"]))
    todo = todo[:limit]
    print("reviews to examine: %d  (%d cached)" % (len(todo), len(done)))

    rows = []
    for i, (frame, pid) in enumerate(todo, 1):
        if pid in done:
            rows.append(done[pid])
            continue
        try:
            p = subprocess.run(["curl", "-sL", "-m", "90", EFETCH % pid],
                               capture_output=True, timeout=120)
            xml = (p.stdout or b"").decode("utf-8", "replace")
        except Exception:
            xml = ""
        if len(xml) < 2000:
            rec = {"pmcid": pid, "frame": frame, "status": "fetch failed"}
        else:
            has, nrows, ntab = analyse(xml)
            rec = {"pmcid": pid, "frame": frame,
                   "status": "thin" if has is None else "ok",
                   "per_trial": bool(has), "rows": nrows, "tables": ntab}
        with io.open(CACHE, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        rows.append(rec)
        if i % 25 == 0:
            print("  %d/%d" % (i, len(todo)))
        time.sleep(0.34)

    full = [r for r in rows if r.get("status") == "ok"]
    thin = [r for r in rows if r.get("status") == "thin"]
    fail = [r for r in rows if r.get("status") == "fetch failed"]
    print()
    print("examined                : %d" % len(rows))
    print("  full text             : %d" % len(full))
    print("  thin PMC stubs        : %d   (EXCLUDED, not counted as 'no table')" % len(thin))
    print("  fetch failures        : %d   (recorded as failures)" % len(fail))
    if not full:
        print("NO RATE IS PRINTED.")
        return 1
    yes = [r for r in full if r["per_trial"]]
    print()
    print("FULL-TEXT REVIEWS PRINTING A PER-TRIAL OUTCOME TABLE: %d of %d  (%.0f%%)"
          % (len(yes), len(full), 100.0*len(yes)/len(full)))
    print("printing NONE                                        : %d of %d  (%.0f%%)"
          % (len(full)-len(yes), len(full), 100.0*(len(full)-len(yes))/len(full)))
    for frame in sorted({r["frame"] for r in full}):
        sub = [r for r in full if r["frame"] == frame]
        sy = [r for r in sub if r["per_trial"]]
        print("   %-10s %3d of %3d (%.0f%%)" % (frame, len(sy), len(sub),
                                                100.0*len(sy)/max(len(sub), 1)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
