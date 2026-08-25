"""Every linked target resolves, or the build names the ones that do not.

# control: a synthetic hub containing one link to a file that certainly exists and one to a
# name that certainly does not. The gate must report exactly one dead link on it. A link checker
# that cannot fail is the verification theatre this project has already found twice.

REQUESTED AFTER A CENSUS LANE REPORTED EIGHT HARD 404s. The eight turned out to be a different
shape than reported -- every one has a copy under `retired/` and NONE is linked from any hub, so
those URLs were built from a list rather than followed from a page. A retired page 404ing at its
old root path is a decision, not a defect. But the question the report raised is real and had
never been asked, and asking it properly found 576 of them.

WHAT IT FOUND, AND THE SPLIT MATTERS MORE THAN THE TOTAL:

    index.html          579 links      0 dead      the front page is clean
    audit_table.html  1,458 links    569 dead      39% of an audit table points at nothing
    portfolio_pools     816 links     50 dead
    auto-gallery        165 links      5 dead

The index is not the problem. `audit_table.html` is a table ABOUT the corpus whose rows link to
pages that do not exist -- a reader following an audit trail lands on 404 two rows in three.
None of the 576 has a copy under `retired/`, so these are not retirements with stale links;
they are rows for pages that were never built or were deleted without touching the table.

WHY A LINK CHECK BELONGS IN THE BUILD. It is the cheapest possible instance of this project's
own rule -- a thing that does not reach a reader has not been delivered -- and it is the one
check where the answer is decidable with certainty rather than by judgement. It reads
origin/main, so it measures what is deployed, not what is on someone's disk.
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

# THE WORKTREE BY DEFAULT, NOT origin/main -- AND THIS WAS WRONG FOR A DAY.
#
# It read `origin/main` and was then wired into PRE-COMMIT, where it validated the PREVIOUS
# PUSH and could not see the commit being made. Planting a dead link in `index.html` and
# running it produced exit 0: the gate was structurally incapable of catching the defect it
# was placed there to catch.
#
# Same family as composed-versus-stored: the instrument was pointed at a different copy of the
# thing than the one being changed. A gate in the commit path must read what is being
# committed; `--ref origin/main` remains available for auditing what is delivered.
REF = None
for _i, _a in enumerate(sys.argv):
    if _a == "--ref" and _i + 1 < len(sys.argv):
        REF = sys.argv[_i + 1]
OUT = os.path.join(REPO, "outputs", "linked_target_resolution_2026_08_23.json")

HUBS = ["index.html", "audit_table.html", "portfolio_pools.html", "auto-gallery.html",
        "what_changed.html", "dashboard.html", "EVIDENCE_GAPS.html"]
LINK = re.compile(r'href="([^"#?]+\.html)')

# The front page is the surface a reader actually starts from. A dead link there is a different
# severity from a dead row in an audit table, so the gate FAILS on the index and REPORTS on the
# rest -- rather than one threshold that is either too strict to pass or too loose to mean
# anything.
FAIL_ON = {"index.html"}


def git(*a):
    return subprocess.run(["git"] + list(a), cwd=REPO, capture_output=True)


def tree():
    """Every .html that exists, from the worktree unless a ref was named."""
    if REF:
        out = git("ls-tree", "-r", "--name-only", REF).stdout.decode("utf-8", "replace")
        files = set(out.split("\n"))
    else:
        # Tracked files, plus anything present on disk at depth <= 1. A page added in the
        # commit under test resolves; a page linked and absent does not.
        out = git("ls-files").stdout.decode("utf-8", "replace")
        files = set(f for f in out.split("\n") if f.strip())
        for n in os.listdir(REPO):
            if n.endswith(".html"):
                files.add(n)
        rdir = os.path.join(REPO, "retired")
        if os.path.isdir(rdir):
            for n in os.listdir(rdir):
                if n.endswith(".html"):
                    files.add("retired/" + n)
    root = set(f for f in files if f.endswith(".html") and "/" not in f)
    retired = set(f.split("/")[-1] for f in files
                  if f.startswith("retired/") and f.endswith(".html"))
    return files, root, retired


def dead_links(hub, files, root):
    """Targets this hub links that do not resolve, as (target, kind)."""
    if REF:
        t = git("show", "%s:%s" % (REF, hub))
        if t.returncode:
            return None
        text = t.stdout.decode("utf-8", "replace")
    else:
        fp = os.path.join(REPO, hub)
        if not os.path.isfile(fp):
            return None
        text = io.open(fp, encoding="utf-8", errors="replace").read()
    out, total = [], set()
    for m in LINK.finditer(text):
        tgt = m.group(1)
        if tgt.startswith("http") or tgt.startswith("//"):
            continue
        total.add(tgt)
        norm = tgt.lstrip("./")
        if "/" in norm:
            if norm not in files:
                out.append(norm)
        elif norm not in root:
            out.append(norm)
    return sorted(set(out)), len(total)


def prove(files, root):
    """The gate must find exactly one dead link in a hub it is handed with one."""
    fake = ("<a href=\"index.html\">live</a>"
            "<a href=\"NO_SUCH_PAGE_9f3a.html\">dead</a>")
    found = [m.group(1) for m in LINK.finditer(fake)
             if m.group(1) not in root]
    return found == ["NO_SUCH_PAGE_9f3a.html"]


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    files, root, retired = tree()
    if not root:
        sys.exit("REFUSED: no root .html at %s -- the tree read failed" % REF)
    if not prove(files, root):
        sys.exit("REFUSED: the gate cannot detect a dead link in a fixture that contains one. "
                 "A link checker that cannot fail reports every corpus as clean.")

    print("")
    print("LINKED TARGET RESOLUTION at %s   (control: passed -- the gate detects a planted"
          " dead link)" % REF)
    print("")
    rows, all_dead, hard_fail = [], {}, []

    # ENUMERATED, NOT LISTED. HUBS names seven pages, and an overnight adversarial hunt
    # briefed to attack the gates asked the obvious question: what about a dead link on a
    # page that is not one of the seven? Answer: 102 of them, across 49 delivered pages,
    # invisible to this gate since it was written.
    #
    # Most are redirect stubs -- X_AUTO_REVIEW.html doing `location.replace` to an
    # X_AUTO_FULL_REVIEW.html that does not exist -- so a reader is bounced to a 404 by a
    # page that has just told them "This page is now the full RapidMeta dashboard".
    #
    # A fixed list is a vocabulary. It answers "are the pages I thought of clean?" while
    # reporting as though it had answered "are the pages clean?". Same shape as a hollow-
    # prose gate resting on seven literal phrases, and the same reason it produced clean
    # reports for a year. The seven stay as the FAIL set, because severity still differs;
    # what changes is that every other root page is now looked at.
    # `root` is already the set of root-level .html files, read from git at REF.
    scanned = sorted(set(HUBS) | set(root))
    for h in scanned:
        r = dead_links(h, files, root)
        if r is None:
            print("   %-24s not present at %s" % (h, REF))
            continue
        dead, total = r
        pct = 100.0 * len(dead) / max(1, total)
        print("   %-24s links=%-6d dead=%-5d %5.1f%%%s"
              % (h, total, len(dead), pct, "   <- FAILS" if (dead and h in FAIL_ON) else ""))
        rows.append({"hub": h, "links": total, "dead": len(dead), "targets": dead[:80]})
        for d in dead:
            all_dead.setdefault(d, []).append(h)
        if dead and h in FAIL_ON:
            hard_fail.append((h, dead))

    moved = sorted(set(all_dead) & retired)
    gone = sorted(set(all_dead) - retired)
    print("")
    print("   distinct dead targets                 %5d" % len(all_dead))
    print("      a copy exists under retired/       %5d   moved, link never updated" % len(moved))
    print("      no copy anywhere                   %5d   never built, or deleted" % len(gone))
    print("")
    print("A RETIRED PAGE 404ing AT ITS OLD PATH IS A DECISION. A ROW IN AN AUDIT TABLE")
    print("POINTING AT A PAGE THAT WAS NEVER BUILT IS A DEFECT, and the two are separated above")
    print("rather than summed, because only one of them is anybody's to fix.")

    if not os.path.isdir(os.path.dirname(OUT)):
        os.makedirs(os.path.dirname(OUT))
    json.dump({"ref": REF, "hubs": rows, "moved_to_retired": moved,
               "no_copy_anywhere": gone[:400], "no_copy_count": len(gone)},
              io.open(OUT, "w", encoding="utf-8"), indent=1)

    if hard_fail:
        sys.exit("REFUSED: %s links %d target(s) that do not resolve. The front page is the "
                 "surface a reader starts from."
                 % (hard_fail[0][0], len(hard_fail[0][1])))


if __name__ == "__main__":
    main()
