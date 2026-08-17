"""STALENESS -- was this page built before a generator feature that would change it?

WHY THIS EXISTS
    ARNI_HF_REVIEW, the flagship, served a build that PREDATED the extraction
    provenance table. Its object carried more source quotes than any neighbouring
    page (9 against SGLT2's 8) and the page showed none of them, because it was
    built at 4b0b0abab and the feature landed at ee17a912e. Mahmood found it by
    looking; nothing we owned detected it.

    "FIXED IN THE GENERATOR" AND "FIXED ON THE SITE" ARE DIFFERENT CLAIMS.
    We were caught by that gap twice in one day: this, and the pre-push hook whose
    repair existed in one clone while six others still carried the broken version.
    The repair existing is not the repair arriving.

HOW IT WORKS
    Pages embed no build stamp, so staleness is read from git ancestry: the last
    commit that touched the page, against each generator commit that changes what a
    build emits. A feature commit that is NOT an ancestor of the page's build
    commit is a feature the page cannot contain.

WHAT A FULL PASS DOES NOT ESTABLISH -- written in advance
    - NOT that the page is CORRECT, only that it was built after every known
      output-changing generator commit.
    - NOT that a listed generator commit actually changes THIS page. A feature
      touching mean-difference rendering does not affect a ratio page, so the
      result is an UPPER BOUND on staleness, and stated as such.
    - NOT staleness relative to the OBJECT. A page rebuilt after a feature but
      before its object changed is stale in a way this does not see.
    - NOT anything about pages never committed, or served from outside the repo.
"""
from __future__ import annotations
import os, re, subprocess, sys, io, json, glob

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = r"F:\rapidmeta-ssot-shell"
GEN = ["ssot/projectors.py", "ssot/projectors2.py", "ssot/build_tabbed.py",
       "ssot/build_app_v2.py", "ssot/wysiwyg.py"]


def git(*a):
    return subprocess.run(["git", "-C", REPO, *a], capture_output=True, text=True).stdout.strip()


def feature_commits(limit=40):
    """Generator commits, newest first. Each is a candidate output change."""
    out = git("log", "--format=%H\t%s", "-n", str(limit), "--", *GEN)
    rows = []
    for ln in out.splitlines():
        if "\t" in ln:
            h, s = ln.split("\t", 1)
            rows.append((h, s))
    return rows


def main() -> int:
    feats = feature_commits()
    if not feats:
        print("no generator commits found -- UNMEASURABLE, not clean")
        return 2
    print("generator feature commits considered: %d (newest first)" % len(feats))
    for h, s in feats[:5]:
        print("   %s %s" % (h[:9], s[:66]))
    pages = sorted(os.path.basename(p) for p in glob.glob(os.path.join(REPO, "*_REVIEW*.html")))
    # only pages the index actually links -- a page nobody can reach is a different problem
    idx = open(os.path.join(REPO, "index.html"), encoding="utf-8", errors="replace").read()
    linked = [p for p in pages if 'href="%s"' % p in idx]
    print("\npages in repo: %d   linked from the index: %d" % (len(pages), len(linked)))
    stale, fresh, unknown = [], 0, 0
    for pg in linked:
        bc = git("log", "-1", "--format=%H", "--", pg)
        if not bc:
            unknown += 1
            continue
        missing = []
        for h, s in feats:
            r = subprocess.run(["git", "-C", REPO, "merge-base", "--is-ancestor", h, bc],
                               capture_output=True)
            if r.returncode != 0:
                missing.append((h[:9], s[:56]))
        if missing:
            stale.append((pg, bc[:9], missing))
        else:
            fresh += 1
    print("\n  FRESH (built after every generator commit) : %d" % fresh)
    print("  STALE (missing >=1 generator feature)      : %d" % len(stale))
    print("  UNKNOWN (never committed)                  : %d" % unknown)
    print("\n  NOTE: this is an UPPER BOUND. A generator commit that cannot affect a given "
          "page still counts against it here.")
    for pg, bc, miss in sorted(stale, key=lambda x: -len(x[2]))[:20]:
        print("    %-46s built %s  missing %d feature(s), newest: %s"
              % (pg[:46], bc, len(miss), miss[0][1]))
    json.dump([{"page": p, "built": b, "missing": m} for p, b, m in stale],
              open(r"F:\E156\outputs\codex-corpus-scan\STALENESS.json", "w",
                   encoding="utf-8"), indent=1)
    return 1 if stale else 0


if __name__ == "__main__":
    sys.exit(main())
