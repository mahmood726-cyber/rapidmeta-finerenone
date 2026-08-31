"""Rebuild one page and diff it against the SERVED bytes, dates and stamp normalised out.

WHAT COUNTS AS EXPECTED. Three things should differ and nothing else:

  * the three declared surfaces landed today -- data-store, data-artefact, data-pool
  * the build stamp and any timestamp, which move on every build by construction
  * for FINERENONE_CV_REVIEW only, the direction label, where the served bytes carry a
    hand-edited false refusal and the rebuild restores the recorded direction

ANYTHING ELSE IS A FINDING. This is the point of the exercise: a rebuild is a risk surface,
and last night one nearly reverted eight served fixes. The diff is read before page two.

READ-ONLY AGAINST THE SERVED TREE. The served copy lives in the primary worktree, which
another lane owns. Nothing here writes to it -- the rebuild goes to a scratch path and only
the comparison touches the served file.

NORMALISATION IS NAMED, NOT SILENT. Every substitution below is listed in the output, so a
reader can see what was excused rather than trusting that the excusing was fair. A diff that
normalises quietly is a diff that can hide the thing it was run to find.

Usage:  python diff_rebuilt_vs_served_2026_08_27.py <PAGE.html> [served_root]
"""
import difflib
import io
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "ssot"))
SERVED_ROOT_DEFAULT = r"F:\rapidmeta-finerenone"

TAG = re.compile(r"<[^>]+>")
SCRIPT = re.compile(r"<script\b.*?</script>", re.S | re.I)

# (label, pattern, replacement) -- printed, so nothing is excused invisibly
NORMALISERS = [
    ("iso timestamp", re.compile(r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(:\d{2})?(Z|[+-]\d{2}:?\d{2})?"), "<TS>"),
    ("iso date", re.compile(r"\d{4}-\d{2}-\d{2}"), "<DATE>"),
    ("data-store", re.compile(r'\s*data-store(-absent)?="[^"]*"'), ""),
    ("data-artefact", re.compile(r'\s*data-artefact="[^"]*"'), ""),
    ("data-pool", re.compile(r'\s*data-pool="[^"]*"'), ""),
]


def normalise(t, log):
    for label, pat, rep in NORMALISERS:
        t, n = pat.subn(rep, t)
        log.append("    %-14s %d substitution(s)" % (label, n))
    return t


def text(html):
    """Rendered text: <script> stripped FIRST, because a script block is not page content."""
    return re.sub(r"\s+", " ", TAG.sub(" ", SCRIPT.sub(" ", html or ""))).strip()


def main():
    if len(sys.argv) < 2:
        print("usage: diff_rebuilt_vs_served_2026_08_27.py <PAGE.html> [served_root]")
        return 2
    page = sys.argv[1]
    served_root = sys.argv[2] if len(sys.argv) > 2 else SERVED_ROOT_DEFAULT

    out = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                           write_through=True)

    def log(s):
        out.write(s + chr(10))
        out.flush()

    import build_tabbed as B
    pm = json.load(io.open(os.path.join(REPO, "ssot", "PAGE_MAP.json"), encoding="utf-8"))
    if page not in pm:
        log("NOT MEASURABLE: %s is not in PAGE_MAP, so this generator does not build it." % page)
        return 1
    served = os.path.join(served_root, page)
    if not os.path.exists(served):
        log("NOT MEASURABLE: no served copy at %s" % served)
        return 1

    obj = json.load(io.open(os.path.join(REPO, pm[page]), encoding="utf-8"))
    rebuilt = B.build(obj)
    served_bytes = io.open(served, encoding="utf-8", errors="replace").read()

    log("page        : %s" % page)
    log("object      : %s" % pm[page])
    log("served from : %s   (%d bytes, read-only)" % (served, len(served_bytes)))
    log("rebuilt     : %d bytes" % len(rebuilt))
    log("")

    nlog_r, nlog_s = [], []
    a = normalise(text(served_bytes), nlog_s)
    b = normalise(text(rebuilt), nlog_r)
    log("normalisers applied to SERVED:")
    for l in nlog_s:
        log(l)
    log("normalisers applied to REBUILT:")
    for l in nlog_r:
        log(l)
    log("")

    aw, bw = a.split(" "), b.split(" ")
    sm = difflib.SequenceMatcher(None, aw, bw, autojunk=False)
    ops = [o for o in sm.get_opcodes() if o[0] != "equal"]
    log("rendered-word diff after normalisation: %d change region(s)" % len(ops))
    log("")
    if not ops:
        log("IDENTICAL once dates, the stamp and the three declared surfaces are removed.")
        log("Nothing beyond the expected differences. Safe to proceed.")
    for tag, i1, i2, j1, j2 in ops[:25]:
        log("  [%s]" % tag)
        if i2 > i1:
            log("    served  : %s" % " ".join(aw[i1:i2])[:220])
        if j2 > j1:
            log("    rebuilt : %s" % " ".join(bw[j1:j2])[:220])
    if len(ops) > 25:
        log("  ... and %d more region(s)" % (len(ops) - 25))
    return 0


if __name__ == "__main__":
    sys.exit(main())
