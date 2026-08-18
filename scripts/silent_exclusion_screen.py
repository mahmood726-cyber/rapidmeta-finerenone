"""SILENT EXCLUSION -- a trial the page includes and the pool never sees.

WHY THIS EXISTS
    On COLCHICINE_CVD the page's own include list named five trials, its embedded
    data carried three, and the card published k=2. The trial that vanished was
    CLEAR SYNERGY: 7,264 randomised, the largest of them, and the only one whose
    result was null. Nothing on the page said it had been left out.

    On DOAC_AF the vanishing trial was ROCKET AF, and on DOAC_CANCER_VTE it was
    ADAM VTE. In both cases the mechanism was mechanical rather than chosen: those
    trials carry no event COUNTS on the page, and a pool derived from 2x2 counts
    silently drops whatever has none.

    NOBODY INTENDED ANY OF THIS. That is exactly why it is worth measuring: a
    pipeline that drops trials for a reason CORRELATED WITH THEIR RESULT produces
    publication bias without anyone choosing it, and the only way to know whether
    that is happening is to look at the direction of what got dropped.

WHAT IT MEASURES
    For each page: the trials named in its include list, minus the trials that
    carry an effect the pool could use. For each dropped trial, its size and the
    direction of its published result where the page records one.

WHAT THIS DOES NOT ESTABLISH -- written in advance, and this matters here
    - NOT that a dropped trial SHOULD have been included. Some exclusions are
      correct and some are required: a trial measuring a different endpoint
      belongs out of the pool, and this screen cannot tell that from an accident.
    - NOT bias, from any single instance. One dropped null trial is an anecdote.
      The question this answers is DISTRIBUTIONAL: across the corpus, do dropped
      trials skew toward the null?
    - NOTHING about pages whose include list it cannot read. Those are reported as
      unread, with their count, and never folded into the denominator.
    - AND THE NULL RESULT IS A REAL RESULT HERE. If dropped trials are directionally
      balanced, that is worth knowing and worth saying plainly, because the
      alarming reading is the one everyone will expect.

USAGE
    python scripts/silent_exclusion_screen.py            # every *_REVIEW.html
    python scripts/silent_exclusion_screen.py <page.html> [...]
    python scripts/silent_exclusion_screen.py --selftest
"""
from __future__ import annotations
import glob
import io
import json
import math
import os
import re
import sys

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

INCLUDE = re.compile(r"AUTO_INCLUDE_TRIAL_IDS\s*=\s*new Set\(\[(.*?)\]\)", re.S)
ID_IN_LIST = re.compile(r'"([^"]+)"')
# ONE EMBEDDED TRIAL RECORD, FOUND BY BRACE MATCHING RATHER THAN BY REGEX.
# The first cut used a regex with a lookahead for the next key, and it failed to
# match records at the end of an object -- so it reported trials as HAVING NO
# RECORD when the record was right there. That is the alarm direction, and for
# this screen specifically that is not the safe one: the whole output is a
# DISTRIBUTIONAL claim about which trials get dropped, and a parser that invents
# drops would manufacture exactly the bias it was built to detect. Caught by the
# third selftest case, which is a page where nothing is dropped at all.
KEY = re.compile(r'"?([A-Z][A-Z0-9_\-]{3,})"?\s*:\s*\{')
TE = re.compile(r"tE\s*:\s*([^,}]+)")
CE = re.compile(r"cE\s*:\s*([^,}]+)")
TN = re.compile(r"tN\s*:\s*([^,}]+)")
CN = re.compile(r"cN\s*:\s*([^,}]+)")
NAME = re.compile(r'name\s*:\s*"([^"]*)"')
HR = re.compile(r"publishedHR\s*:\s*([-\d.]+)")


def _records(seg):
    """{trial id: fields} by scanning balanced braces from each `ID:{`."""
    out = {}
    for m in KEY.finditer(seg):
        tid = m.group(1)
        if tid in out:
            continue
        i = seg.index("{", m.end() - 1)
        depth, j = 0, i
        while j < len(seg):
            if seg[j] == "{":
                depth += 1
            elif seg[j] == "}":
                depth -= 1
                if depth == 0:
                    break
            j += 1
        body = seg[i:j + 1]
        nm = NAME.search(body)
        # a record with no name and no counts is not a trial record
        if not nm and not TN.search(body):
            continue
        out[tid] = {"name": nm.group(1) if nm else None,
                    "tE": _num(TE.search(body)), "cE": _num(CE.search(body)),
                    "tN": _num(TN.search(body)), "cN": _num(CN.search(body)),
                    "hr": _num(HR.search(body))}
    return out


def _num(m):
    if not m:
        return None
    v = m.group(1).strip()
    if v in ("null", "undefined", ""):
        return None
    try:
        return float(v)
    except ValueError:
        return None


def read_page(html):
    """(included ids, {id: record}) or (None, None) if the include list is absent."""
    m = INCLUDE.search(html or "")
    if not m:
        return None, None
    ids = ID_IN_LIST.findall(m.group(1))
    i = html.find("realData:{")
    recs = _records(html[i:i + 120000]) if i >= 0 else {}
    return ids, recs


def assess(html):
    ids, recs = read_page(html)
    if ids is None:
        return "UNREAD", "no include list on this page", []
    dropped = []
    for tid in ids:
        r = recs.get(tid)
        # A trial is usable by a count-derived pool only if BOTH event counts are
        # present. That is the actual mechanism observed on three topics.
        if r is None:
            dropped.append({"id": tid, "name": None, "why": "named in the include list and carries no embedded record",
                            "n": None, "hr": None})
        elif r["tE"] is None or r["cE"] is None:
            dropped.append({"id": tid, "name": r["name"], "why": "no event counts",
                            "n": (r["tN"] or 0) + (r["cN"] or 0) or None, "hr": r["hr"]})
    return ("DROPPED" if dropped else "COMPLETE",
            "%d of %d included trial(s) contribute no usable effect" % (len(dropped), len(ids)),
            dropped)


def selftest() -> int:
    ok = True
    COLCH = ('AUTO_INCLUDE_TRIAL_IDS=new Set(["NCT02551094","ACTRN-LODOCO2",'
             '"NCT03048825"]),x realData:{NCT02551094:{name:"COLCOT",tE:131,tN:2366,'
             'cE:170,cN:2379,publishedHR:.77},NCT03048825:{name:"CLEAR",tE:322,'
             'tN:3528,cE:327,cN:3534,publishedHR:.99}}')
    NULLCOUNT = ('AUTO_INCLUDE_TRIAL_IDS=new Set(["NCT1","NCT2"]),x realData:{'
                 'NCT1:{name:"A",tE:10,tN:100,cE:20,cN:100,publishedHR:.5},'
                 'NCT2:{name:"B",tE:null,tN:145,cE:null,cN:142,publishedHR:.99}}')
    cases = [
        ("COLCHICINE shape: an included id with no record at all", COLCH, "DROPPED", 1),
        ("ADAM VTE shape: a record present with null event counts", NULLCOUNT, "DROPPED", 1),
        ("a page whose included trials all carry counts",
         'AUTO_INCLUDE_TRIAL_IDS=new Set(["NCT1"]),x realData:{NCT1:{name:"A",tE:1,'
         'tN:10,cE:2,cN:10,publishedHR:.5}}', "COMPLETE", 0),
        ("a page with no include list is UNREAD, never COMPLETE",
         "<html>nothing here</html>", "UNREAD", 0),
    ]
    for label, html, want, n in cases:
        v, why, dropped = assess(html)
        good = v == want and len(dropped) == n
        ok &= good
        print("  %-58s -> %-9s (want %-9s, %d dropped) %s"
              % (label[:58], v, want, len(dropped), "correct" if good else "WRONG"))
        if not good:
            print("        %s | %s" % (why, dropped))
    print("\nWHAT A FAILURE WOULD LOOK LIKE: the last case reporting COMPLETE. A page whose "
          "include list cannot be read has not been shown to be clean, and folding it into "
          "the clean count is how a screen reports a corpus it never examined.")
    print("-> SELFTEST PASS" if ok else "-> SELFTEST FAILED")
    return 0 if ok else 1


def main() -> int:
    if len(sys.argv) > 1 and sys.argv[1] == "--selftest":
        return selftest()
    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    paths = (sys.argv[1:] if len(sys.argv) > 1
             else sorted(glob.glob(os.path.join(repo, "*_REVIEW*.html"))))
    unread = complete = 0
    rows = []
    for p in paths:
        try:
            html = open(p, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        v, why, dropped = assess(html)
        if v == "UNREAD":
            unread += 1
            continue
        if v == "COMPLETE":
            complete += 1
            continue
        for d in dropped:
            rows.append((os.path.basename(p), d))

    print("PAGES: %d scanned | %d had no readable include list (UNREAD, not clean) | "
          "%d complete | %d with at least one dropped trial"
          % (len(paths), unread, complete, len({r[0] for r in rows})))
    if not rows:
        print("no dropped trials found in the pages that could be read")
        return 0

    # A RATIO MEASURE MUST BE POSITIVE. Some pages store a MEAN DIFFERENCE in
    # the publishedHR slot, so the column holds negative values -- a real finding
    # about that field's naming, and a math domain error if fed to a geometric
    # mean. Counted and reported SEPARATELY rather than dropped in silence,
    # which is the very defect this script exists to measure.
    all_hr = [d for _, d in rows if isinstance(d.get("hr"), float)]
    non_ratio = [d for d in all_hr if d["hr"] <= 0]
    with_hr = [d for d in all_hr if d["hr"] > 0]
    print("\nDROPPED TRIALS: %d total | %d carry a usable published ratio | "
          "%d carry a NON-RATIO value in the publishedHR field"
          % (len(rows), len(with_hr), len(non_ratio)))
    if with_hr:
        favour = sum(1 for d in with_hr if d["hr"] < 0.95)
        null_ish = sum(1 for d in with_hr if 0.95 <= d["hr"] <= 1.05)
        against = sum(1 for d in with_hr if d["hr"] > 1.05)
        gm = math.exp(sum(math.log(d["hr"]) for d in with_hr) / len(with_hr))
        print("  direction of the dropped, by published point estimate:")
        print("    favours the intervention (<0.95) : %d" % favour)
        print("    null-ish (0.95 to 1.05)          : %d" % null_ish)
        print("    favours the control (>1.05)      : %d" % against)
        print("    geometric mean of dropped effects: %.3f" % gm)
        print("  A geometric mean near 1.00 with a balanced spread is the REASSURING "
              "reading and is what it looks like when trials drop for reasons unrelated "
              "to their result. A mean pulled toward 1 with the favourable ones retained "
              "is the alarming one.")
    print("\n  %-46s %-22s %-9s %s" % ("page", "dropped trial", "n", "published effect"))
    for name, d in sorted(rows, key=lambda r: -(r[1].get("n") or 0))[:40]:
        print("  %-46s %-22s %-9s %s"
              % (name[:46], (d.get("name") or d["id"])[:22],
                 ("%d" % d["n"]) if d.get("n") else "-",
                 ("%.2f" % d["hr"]) if d.get("hr") else "not on the page"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
