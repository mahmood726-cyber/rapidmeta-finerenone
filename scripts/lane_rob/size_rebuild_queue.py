# -*- coding: utf-8 -*-
"""Split the stale-certainty pages into REBUILDABLE and BLOCKED, and give the 137 a face.

WHY THE SPLIT EXISTS. A build stamp is not provenance, it is an INSTRUCTION: it names the
generator the next build must use. So a page with no stamp, or with a stamp naming a commit
that does not resolve, cannot be correctly rebuilt at all -- rebuilding it at HEAD is a guess,
and guessing is what nearly reverted eight served direction labels tonight.

That turns "137 of 149 pages carry no stamp" from a documentation backlog into a hard
blocker, and this counts how much of the current repair queue it actually blocks.

FOUR STATES, and the last two are the ones that matter:

  REBUILDABLE          stamp present, names a commit that resolves in this repository
  BLOCKED_NO_STAMP     no stamp -> nothing says which generator; the build must refuse
  BLOCKED_UNRESOLVED   stamp names a commit git cannot find -> same, with a false trail
  BLOCKED_UNKNOWN      stamp says UNKNOWN (git unavailable at build) -- honest, still blocked

READ-ONLY.
"""
import collections
import io
import json
import os
import re
import subprocess
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                              line_buffering=True)
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
os.chdir(REPO)

STAMP_RE = re.compile(r"Generator build.{0,80}?<code>([^<]{1,60})</code>", re.S)
SHA_RE = re.compile(r"\b([0-9a-f]{7,40})\b")


def stamp_state(page):
    try:
        raw = open(page, "rb").read().decode("utf-8", "replace")
    except OSError:
        return "BLOCKED_NO_STAMP", None
    m = STAMP_RE.search(raw)
    if not m:
        return "BLOCKED_NO_STAMP", None
    txt = m.group(1).strip()
    if "unknown" in txt.lower():
        return "BLOCKED_UNKNOWN", txt
    s = SHA_RE.search(txt)
    if not s:
        return "BLOCKED_UNRESOLVED", txt
    sha = s.group(1)
    r = subprocess.run(["git", "cat-file", "-e", sha + "^{commit}"],
                       cwd=REPO, capture_output=True)
    if r.returncode != 0:
        return "BLOCKED_UNRESOLVED", txt
    return "REBUILDABLE", sha


def main():
    src = json.load(io.open(r"F:\claude-temp\pend\conflict_levels.json", encoding="utf-8"))
    stale = [r["page"] for r in src if r.get("conflict_level_vs_withheld")
             or r.get("conflict_distinct_levels")]
    rows = []
    for p in sorted(set(stale)):
        st, detail = stamp_state(p)
        rows.append({"page": p, "state": st, "stamp": detail,
                     "exists": os.path.isfile(p)})

    c = collections.Counter(r["state"] for r in rows)
    print("=" * 88)
    print("REBUILD QUEUE FOR THE STALE-CERTAINTY PAGES")
    print("=" * 88)
    print("  pages needing a rebuild                     %4d  == the denominator" % len(rows))
    for k in ("REBUILDABLE", "BLOCKED_NO_STAMP", "BLOCKED_UNRESOLVED", "BLOCKED_UNKNOWN"):
        if c[k]:
            print("     %-34s %4d" % (k, c[k]))
    print("")
    for r in sorted(rows, key=lambda x: (x["state"], x["page"])):
        print("   %-20s %-44s %s" % (r["state"], r["page"][:43], r["stamp"] or ""))

    print("")
    print("=" * 88)
    print("AND THE SAME QUESTION ACROSS EVERY DELIVERED PAGE -- giving the 137 a face")
    print("=" * 88)
    import glob
    allrows = collections.Counter()
    for p in sorted(glob.glob("*.html")):
        allrows[stamp_state(p)[0]] += 1
    tot = sum(allrows.values())
    print("  delivered pages                             %4d  == the denominator" % tot)
    for k, v in allrows.most_common():
        print("     %-34s %4d   %5.1f%%" % (k, v, 100.0 * v / tot if tot else 0))
    blocked = tot - allrows["REBUILDABLE"]
    print("")
    print("  CANNOT BE CORRECTLY REBUILT AT ALL          %4d   %5.1f%%"
          % (blocked, 100.0 * blocked / tot if tot else 0))
    json.dump(rows, io.open(r"F:\claude-temp\pend\rebuild_queue.json", "w",
                            encoding="utf-8"), indent=1)
    print("")
    print("  detail -> rebuild_queue.json")


if __name__ == "__main__":
    main()
