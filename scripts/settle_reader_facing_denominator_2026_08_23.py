"""THE DENOMINATOR, SETTLED BY TRANSITIVE CLOSURE OVER THE DELIVERED STATE.

# control: the closure must contain the index itself and the two hub pages it links, and every
# page in it must exist at origin/main. The run refuses if the reachable set is smaller than the
# index's own out-degree, which is the shape a truncated read produces.

FOUR NUMBERS WERE IN CIRCULATION FOR THE SAME QUANTITY and at least three were taken with
instruments now known to mislead:

    ~417   a truncated index fetch                                   withdrawn by its author
     579   `href="..."` occurrences in index.html                    MINE, AND WRONG
     947   a census lane reading the index                           very close to right
   1,509   root .html files in the worktree                          right, but not the question

MINE WAS WRONG BECAUSE I ASKED ONE PAGE. `index.html` links 579 pages directly, but it is not
the only hub. `audit_table.html` carries 889 links and `portfolio_pools.html` 766, and BOTH ARE
LINKED FROM THE INDEX. A reader two clicks in reaches 351 pages that the index never names. So
every rate this project has published against 579 was against a denominator that stopped at the
first hop, and the census lane's 947 was nearer the truth than my 579 by a wide margin.

WHY THE CLOSURE IS THE RIGHT QUESTION. "Reader-facing" is not "linked from the front page"; it
is "reachable by following links". The 1,509 root files are the wrong answer in the other
direction -- 579 of them are reachable from nothing and a reader never meets them. Reachability
is the property, so reachability is what is computed.

MEASURED OVER origin/main, NOT THE WORKTREE. The delivered state is the one a reader meets, and
this project has already spent a night on the difference. Every byte read here comes from
`git show origin/main:<path>`, never from disk.
"""
from __future__ import annotations

import collections
import io
import json
import os
import re
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REF = "origin/main"
OUT = os.path.join(REPO, "outputs", "reader_facing_denominator_2026_08_23.json")

# hubs and instruments, not reviews -- excluded from the review count and named here so the
# exclusion is auditable rather than a silent filter
NOT_REVIEWS = {"index.html", "audit_table.html", "dashboard.html", "portfolio_pools.html",
               "what_changed.html", "EVIDENCE_GAPS.html", "auto-gallery.html"}

LINK = re.compile(r'href="([^"#?]+\.html)')


def git(*a):
    return subprocess.run(["git"] + list(a), cwd=REPO, capture_output=True)


def tree():
    out = git("ls-tree", "-r", "--name-only", REF).stdout.decode("utf-8", "replace")
    return set(out.split("\n"))


def text(path, cache={}):
    if path not in cache:
        r = git("show", "%s:%s" % (REF, path))
        cache[path] = "" if r.returncode else r.stdout.decode("utf-8", "replace")
    return cache[path]


def closure(root):
    """Every root page reachable from index.html, with the hop at which it is first met."""
    seen, depth, hubs = {"index.html"}, {"index.html": 0}, collections.Counter()
    q = ["index.html"]
    while q:
        cur = q.pop(0)
        t = text(cur)
        if not t:
            continue
        outs = set()
        for m in LINK.finditer(t):
            n = m.group(1).split("/")[-1]
            if n in root:
                outs.add(n)
        hubs[cur] = len(outs)
        for n in outs:
            if n not in seen:
                seen.add(n)
                depth[n] = depth[cur] + 1
                q.append(n)
    return seen, depth, hubs


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    ls = tree()
    root = set(f for f in ls if f.endswith(".html") and "/" not in f)
    if not root:
        sys.exit("REFUSED: no root .html at %s -- the ref is wrong or the tree read failed"
                 % REF)
    seen, depth, hubs = closure(root)
    reviews = sorted(seen - NOT_REVIEWS)
    unreachable = sorted(root - seen)

    print("")
    print("READER-FACING DENOMINATOR, transitive closure from index.html over %s" % REF)
    print("")
    print("   root .html files present in the tree        %5d" % len(root))
    print("   REACHABLE by following links               %5d" % len(seen))
    print("   of those, review pages (hubs excluded)     %5d" % len(reviews))
    print("   present but reachable from NOTHING         %5d" % len(unreachable))
    print("")
    print("   by hop from the index:")
    for d in sorted(set(depth.values())):
        print("      depth %d   %5d" % (d, sum(1 for v in depth.values() if v == d)))
    print("")
    print("   hub pages by out-degree:")
    for p, c in hubs.most_common(6):
        if c:
            print("      %-32s %5d" % (p, c))

    # THE CONTROL. A read that stops early produces a closure no larger than the index's own
    # out-degree, which is exactly the failure that put 579 into circulation. Refuse it.
    idx_out = hubs.get("index.html", 0)
    if len(seen) <= idx_out + 1:
        sys.exit("REFUSED: the closure (%d) is no larger than index.html's own out-degree (%d). "
                 "That is the shape a first-hop-only read produces, and it is the error this "
                 "script exists to correct." % (len(seen), idx_out))

    print("")
    print("EVERY PUBLISHED RATE MUST NAME WHICH OF THESE IT IS AGAINST.")
    print("Reachable-from-the-index is the reader-facing population. The %d unreachable files"
          % len(unreachable))
    print("are work that reached nobody, and they are NOT a denominator for anything.")

    if not os.path.isdir(os.path.dirname(OUT)):
        os.makedirs(os.path.dirname(OUT))
    json.dump({"ref": REF, "root_html": len(root), "reachable": sorted(seen),
               "reviews": reviews, "unreachable": unreachable,
               "hubs": dict(hubs.most_common(12)),
               "by_depth": {str(d): sum(1 for v in depth.values() if v == d)
                            for d in sorted(set(depth.values()))}},
              io.open(OUT, "w", encoding="utf-8"), indent=1)
    print("")
    print("written: %s" % os.path.relpath(OUT, REPO))


if __name__ == "__main__":
    main()
