"""Stored text silently shortened on the way to a page. Two instances, so: is it a class?

# control: the POSITIVE is bosentan-pah, still live and unfixed -- its withdrawal notice
# quotes a registered outcome title in short form while the object holds the full one. The
# NEGATIVE is a synthetic pair built in this file, where a short string is NOT a prefix of a
# longer one and must not be flagged. ARNI is deliberately NOT the positive: its 400-character
# justification was repaired hours ago, and a control keyed to a defect you have removed
# expires the moment you succeed.

TWO INSTANCES FOUND SEPARATELY, BY DIFFERENT MEANS, IN ONE NIGHT.

    arni-hfref   a stored risk-of-bias justification cut at EXACTLY 400 characters, ending
                 mid-sentence -- "...which is one of the two components. In the same trial"
                 -- and a literal PREFIX of the 1,249-character text it was copied from.
                 Found by a blinded outside model reading the two GRADE locations cold.

    bosentan-pah a withdrawal notice quoting a registered outcome title as "Time to First
                 Confirmed Morbidity/Mortality Event" where the object holds "...up to the
                 End of Study". Found by a blinded reviewer on a complete packet.

AN UNMARKED TRUNCATION IS A QUOTATION THAT IS NOT A QUOTATION. Quotation marks are a
promise about exactness, and a shortened quote with no ellipsis breaks that promise
silently -- the reader cannot tell, and neither can any check that compares the quoted text
to itself.

THREE DETECTORS, because the two known instances arrived by different routes:

  A  A ROUND-NUMBER CUT. A stored value whose length is exactly 200/300/400/500/1000 and
     which does not end at a sentence boundary. Length alone is weak evidence; length AND a
     mid-sentence ending together are not.

  B  A PREFIX PAIR. One stored value is a proper prefix of another stored value in the same
     object, and the shorter one is where the longer one belongs. This is what caught ARNI.

  C  AN UNMARKED SHORT QUOTE. A quoted span inside prose that is a proper prefix of a
     longer string held elsewhere in the same object, with no ellipsis. This is bosentan.
"""
from __future__ import annotations

import glob
import io
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from instrument_controls import require_controls  # noqa: E402

ROUND = (200, 300, 400, 500, 750, 1000, 1200, 1500, 2000)
ENDS_OK = re.compile(r"[.!?)\]\"']\s*$")
QUOTED = re.compile(r"'([^']{25,160})'|\"([^\"]{25,160})\"")
MIN_LEN = 40


def strings_of(obj):
    """(path, value) for every string worth checking."""
    out = []

    def walk(x, p=""):
        if isinstance(x, dict):
            for k, v in x.items():
                walk(v, p + "/" + str(k))
        elif isinstance(x, list):
            for i, v in enumerate(x):
                walk(v, "%s[%d]" % (p, i))
        elif isinstance(x, str) and len(x) >= MIN_LEN:
            out.append((p, x))

    walk(obj)
    return out


def round_cuts(items):
    hits = []
    for p, v in items:
        if len(v) in ROUND and not ENDS_OK.search(v):
            hits.append((p, len(v), v[-46:]))
    return hits


def prefix_pairs(items):
    hits = []
    byval = sorted(items, key=lambda x: len(x[1]))
    for i, (p, v) in enumerate(byval):
        if ENDS_OK.search(v):
            continue
        for q, w in byval[i + 1:]:
            if len(w) > len(v) and w.startswith(v):
                hits.append((p, len(v), q, len(w)))
                break
    return hits


def short_quotes(items):
    """A quoted span that is a proper prefix of a longer stored string, no ellipsis."""
    longs = [v for _p, v in items if len(v) >= 60]
    hits = []
    for p, v in items:
        for m in QUOTED.finditer(v):
            q = (m.group(1) or m.group(2) or "").strip()
            if len(q) < 25 or q.endswith(("...", "…")):
                continue
            for w in longs:
                if w != q and w.startswith(q) and len(w) > len(q) + 8:
                    hits.append((p, q[:60], w[len(q):len(q) + 40]))
                    break
    return hits


# The synthetic negative: a short string that is NOT a prefix of the long one.
FIXTURE = {"a": "A complete sentence that ends properly and is long enough to count.",
           "b": "An entirely different sentence, also complete, sharing no prefix at all."}


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    per = {}
    for p in sorted(glob.glob(os.path.join(REPO, "ssot", "*", "*.json"))):
        t = os.path.basename(os.path.dirname(p))
        if os.path.basename(p) != t + ".json":
            continue
        try:
            o = json.load(io.open(p, encoding="utf-8"))
        except ValueError:
            continue
        items = strings_of(o)
        per[t] = {"round": round_cuts(items), "prefix": prefix_pairs(items),
                  "quote": short_quotes(items)}

    bos = per.get("bosentan-pah", {})
    fx = strings_of(FIXTURE)
    require_controls(
        "silent_truncation",
        ("bosentan-pah quotes a registered outcome title in short form while the object "
         "holds the full one -- read by hand and still live; unmarked short quotes found: %d"
         % len(bos.get("quote", [])), len(bos.get("quote", [])) >= 1, True),
        # `must_not_be` is the BAD outcome, not the good one. Written as (0, 0) this refused
        # whenever the fixture was correctly clean -- the second time tonight I have handed
        # this argument the state I want rather than the state I forbid.
        ("a synthetic pair with no shared prefix must not be flagged; did it flag? %s"
         % bool(prefix_pairs(fx)), bool(prefix_pairs(fx)), True))

    tot = {k: sum(len(v[k]) for v in per.values()) for k in ("round", "prefix", "quote")}
    objs = {k: sum(1 for v in per.values() if v[k]) for k in ("round", "prefix", "quote")}
    print("")
    print("SILENTLY SHORTENED STORED TEXT, over %d objects" % len(per))
    print("")
    print("   A  round-number cut, ending mid-sentence   %4d in %3d object(s)"
          % (tot["round"], objs["round"]))
    print("   B  a value that is a PREFIX of another     %4d in %3d object(s)"
          % (tot["prefix"], objs["prefix"]))
    print("   C  an unmarked short quote                 %4d in %3d object(s)"
          % (tot["quote"], objs["quote"]))
    print("")
    for kind, label in (("round", "ROUND CUT"), ("prefix", "PREFIX PAIR"),
                        ("quote", "SHORT QUOTE")):
        shown = 0
        for t, v in sorted(per.items()):
            for h in v[kind]:
                if shown >= 8:
                    break
                print("   %-11s %-30s %s" % (label, t[:30], str(h)[:110]))
                shown += 1
            if shown >= 8:
                break
        if shown:
            print("")
    json.dump({"totals": tot, "objects": objs,
               "per_topic": {k: {kk: vv for kk, vv in v.items() if vv}
                             for k, v in per.items() if any(v.values())}},
              io.open(os.path.join(REPO, "outputs",
                                   "silent_truncation_2026_08_24.json"),
                      "w", encoding="utf-8"), indent=1)
    print("A quotation is a promise about exactness. An unmarked short quote breaks it in a")
    print("way neither the reader nor a self-comparison can detect.")


if __name__ == "__main__":
    main()
