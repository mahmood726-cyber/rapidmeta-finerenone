"""Finish the de-indexing that commit 2a011cdfe did on two surfaces out of three.

# no-control: an edit, not a detector. Its controls are asserted inline and the run refuses
# rather than writes if any fails: every removed target must be absent from the tree, every
# surviving target must still be linked, the scored rows must be untouched, and the advertised
# count must equal the list it describes.

WHAT HAPPENED, AND IT IS NOT A MISTAKE ABOUT THE PAGES. Commit 2a011cdfe (2026-06-07) removed
519 single-trial AUTO apps on a correct and documented principle:

    "A meta-analysis requires >=2 trials measuring a shared outcome ... found 519
     AUTO_FULL_REVIEW apps with exactly one trial -- k=1, not meta-analyses. Hard-deleted +
     de-indexed: removed their index.html cards (47) and sitemap.xml entries (520)."

The deletion was right and the de-indexing was thorough on the two surfaces its author was
thinking about. `audit_table.html` was the third. Eleven weeks later `index.html` has ZERO dead
links and this table has 569 -- two rows in five of the surface a sceptical reader opens first
pointing at nothing.

WHERE THEY ARE, WHICH DECIDES THAT THIS IS SAFE. Not in the audit rows. Every dead link sits in
one appended section -- "N additional full interactive dashboards (no audit-score row yet --
reachable directly)" -- as `<li><a href=...>` items. The scored `<tr>` rows carry findings and
are not touched by this script at all.

SO THIS PUBLISHES NOTHING AND ASSERTS NOTHING NEW. It removes links to pages that were
deliberately deleted, and corrects a count that describes the list it sits above. Every removal
is verified against the tree: a target that still exists is KEPT, whatever this script thinks.
"""
from __future__ import annotations

import io
import os
import re
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = os.path.join(REPO, "audit_table.html")
REF = "origin/main"

LI = re.compile(r'<li style="margin:2px 0;"><a href="([^"]+\.html)".*?</li>\s*', re.S)
COUNT = re.compile(r"<strong>(\d+) additional full interactive dashboards</strong>")


def tree_root():
    out = subprocess.run(["git", "ls-tree", "-r", "--name-only", REF],
                         cwd=REPO, capture_output=True).stdout.decode("utf-8", "replace")
    return set(f for f in out.split("\n") if f.endswith(".html") and "/" not in f)


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    root = tree_root()
    if not root:
        sys.exit("REFUSED: could not read the tree at %s." % REF)
    src = io.open(PAGE, encoding="utf-8", newline="").read()

    items = LI.findall(src)
    if not items:
        sys.exit("REFUSED: no delisting items matched. The section's markup has changed and "
                 "this script would edit nothing while reporting success.")
    dead = [n for n in items if n.split("/")[-1] not in root]
    live = [n for n in items if n.split("/")[-1] in root]
    rows_before = src.count("<tr")
    print("delisting section: %d item(s) -- %d live, %d pointing at deleted pages"
          % (len(items), len(live), len(dead)))
    if not dead:
        print("nothing to do.")
        return

    def drop(m):
        return "" if m.group(1).split("/")[-1] not in root else m.group(0)

    out = LI.sub(drop, src)

    # THE COUNT DESCRIBES THE LIST IT SITS ABOVE. Leaving it at 499 over a shorter list would
    # replace a broken link with a false number, which is a worse defect than the one fixed.
    m = COUNT.search(out)
    if m:
        out = COUNT.sub("<strong>%d additional full interactive dashboards</strong>"
                        % len(live), out, count=1)
        print("advertised count %s -> %d" % (m.group(1), len(live)))

    # CONTROLS. Refuse rather than write.
    after = LI.findall(out)
    errs = []
    if sorted(after) != sorted(live):
        errs.append("the surviving list is not exactly the live targets (%d vs %d)"
                    % (len(after), len(live)))
    if any(n.split("/")[-1] not in root for n in after):
        errs.append("a surviving link still points at a missing page")
    if out.count("<tr") != rows_before:
        errs.append("the scored rows changed (%d -> %d) -- this script must not touch them"
                    % (rows_before, out.count("<tr")))
    if len(out) >= len(src):
        errs.append("the file did not shrink, so nothing was delisted")
    if errs:
        sys.exit("REFUSED, nothing written:\n   " + "\n   ".join(errs))

    io.open(PAGE, "w", encoding="utf-8", newline="").write(out)
    print("")
    print("audit_table.html %d -> %d bytes; %d dead link(s) removed, %d kept, %d scored rows "
          "untouched" % (len(src), len(out), len(dead), len(live), rows_before))
    print("")
    print("The deletion these links pointed at was correct and documented. Only its coverage")
    print("was incomplete: two surfaces of three. This is the third.")


if __name__ == "__main__":
    main()
