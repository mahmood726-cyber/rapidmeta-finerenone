"""BUILD STAMP -- can a reader tell which generator produced this page?

WHY THIS EXISTS
    ARNI served a build predating a feature every neighbouring page had, and
    nothing detected it. A page that does not name the code that made it cannot
    be told apart from a page made by different code, so "we fixed the generator"
    says nothing about any particular artefact.

    AND A STAMP FROM A DIRTY TREE IS NOT REPRODUCIBLE. If the generator had
    uncommitted changes, the commit named does not describe what ran, and the
    page must say so rather than print a hash that cannot be checked out.

WHAT A FULL PASS DOES NOT ESTABLISH
    - NOT that the named commit is the one that ACTUALLY produced the bytes; a
      stamp can be stale if the page was not rebuilt. It establishes the claim is
      present, well formed and honest about dirtiness.
    - NOT that the standard version stamped is the one the page meets.
"""
from __future__ import annotations
import io, os, re, sys

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

STAMP = re.compile(r"Generator build", re.I)
SHA = re.compile(r"<code>([0-9a-f]{7,40})</code>", re.I)
DIRTY = re.compile(r"uncommitted generator changes|NOT REPRODUCIBLE", re.I)
UNKNOWN = re.compile(r"\bUNKNOWN\b")


def check(html):
    if not STAMP.search(html):
        return "FAIL", "no build stamp: the page does not name the code that made it"
    seg = html[max(0, html.find("Generator build") - 200):][:800]
    if UNKNOWN.search(seg):
        return "FAIL", "build stamp present but reads UNKNOWN -- a stamp naming "
    m = SHA.search(seg)
    if not m:
        return "FAIL", "build stamp present with no commit id"
    if DIRTY.search(seg):
        return "PASS", ("commit %s, DECLARED NOT REPRODUCIBLE (built from a dirty "
                        "tree, and says so)" % m.group(1)[:12])
    return "PASS", "commit %s" % m.group(1)[:12]


def selftest():
    ok = True
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for page, want in (("ARNI_HF_REVIEW.html", "PASS"),
                       ("FINERENONE_CV_REVIEW.html", "PASS")):
        p = os.path.join(root, page)
        if not os.path.exists(p):
            print("  fixture absent: %s -- NOT PROVEN" % page); ok = False; continue
        v, why = check(open(p, encoding="utf-8", errors="replace").read())
        ok &= v == want
        print("  %-34s -> %-5s (want %s) %s" % (page[:34], v, want,
                                                "correct" if v == want else "WRONG"))
    # CONSTRUCTIBLE FAILURES, since no real stamped-then-unstamped page exists.
    for name, html, want in (
            ("a page with no stamp at all", "<html><body>nothing</body></html>", "FAIL"),
            ("a stamp reading UNKNOWN", "<p>Generator build <code>UNKNOWN</code></p>", "FAIL"),
            ("a stamp with no commit id", "<p>Generator build (none)</p>", "FAIL"),
            ("a dirty-tree stamp that declares itself",
             "<p>Generator build <code>abc1234def</code> (uncommitted generator "
             "changes -- NOT REPRODUCIBLE)</p>", "PASS")):
        v, why = check(html)
        ok &= v == want
        print("  %-34s -> %-5s (want %s) %s" % (name[:34], v, want,
                                                "correct" if v == want else "WRONG"))
    print("\nWHAT A FAILURE WOULD LOOK LIKE: an unstamped page passing, which is a "
          "page that cannot be told apart from one built by different code.")
    print("-> SELFTEST PASS" if ok else "-> SELFTEST FAILED")
    return 0 if ok else 1


def main():
    if len(sys.argv) < 2 or sys.argv[1] == "--selftest":
        return selftest()
    if not os.path.exists(sys.argv[1]):
        print("build_stamp: %s does not exist. NOT RUN -- not a pass." % sys.argv[1],
              file=sys.stderr)
        return 2
    v, why = check(open(sys.argv[1], encoding="utf-8", errors="replace").read())
    print("  %s\n  -> %s" % (why, v))
    return 0 if v == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
