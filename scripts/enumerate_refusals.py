"""Enumerate the REFUSALS a delivered page makes, with line numbers.

WHY THIS EXISTS. This corpus's dominant output is documented refusal -- pools
withdrawn with a reason, figures not drawn and the slot saying so, a protocol
that will not be written retrospectively. When an external reviewer reads a
page and reports defects, those refusals are the part most easily tidied away
by a fix, because nothing points at them. They were enumerated once, by hand,
into a report. A FINDING THAT LIVES ONLY IN A REPORT IS ONE DETACHED DRIVE AWAY
FROM NEVER HAVING HAPPENED -- which is very nearly what occurred: the working
clone holding that enumeration was on an external volume that is now gone, and
only the pushed commit survived.

WHAT IT IS NOT. It does not judge whether a refusal is correct. It records that
the page makes one, and where, so a later edit that removes one is visible as a
diff rather than as silence.

IDENTITY. A page name is not an artefact identity; a name plus a blob sha is.
The output records the sha of the bytes actually read, so a count can be
re-derived against the same bytes rather than against whatever the name points
at later.

CONTROLS ARE SYNTHETIC ON PURPOSE. A control anchored to a live page retires
itself the moment that page is edited: it either fails and looks like a
regression, or passes for the wrong reason. Both controls here are fabricated
strings run through the same detector, so they cannot drift.
"""
import argparse
import html
import io
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from instrument_controls import require_controls, zero_has_a_reading

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# The vocabulary of refusal as this corpus writes it. Each alternative was read
# off a delivered page, not invented.
REFUSAL = re.compile(
    r"(DO NOT POOL|withdraw|DECLINE[SD]?|declined|refus|not pooled|cannot vouch"
    r"|NOT INSERTED|is not pooled|no absolute effect|withheld|does not publish"
    r"|MUST NOT|is withdrawn|not drawn|NOT ASSESSABLE|no interval is computed)",
    re.I)

# A line must carry this much prose before it is worth recording; below it the
# match is usually a stylesheet or an attribute rather than a statement.
MIN_FRAGMENT = 40


def _plain(line):
    """Rendered text of one source line. Markup splits sentences; matching the
    source would miss any refusal that spans a tag."""
    t = re.sub(r"<[^>]+>", " ", line)
    t = html.unescape(t)
    return re.sub(r"\s+", " ", t).strip()


def refusals_in(text):
    """-> [(line_number, fragment)] for every distinct refusal statement.

    Positive property: a line is RECORDED when it carries a refusal token inside
    enough prose to read. Lines are examined in full; none is skipped silently.
    """
    found, seen = [], set()
    for n, line in enumerate(text.split("\n"), 1):
        flat = _plain(line)
        # ONE statement per line, but SCAN PAST duplicates to find it. Taking
        # only the first match drops the whole line whenever that fragment
        # duplicates one already recorded -- silently, with the count merely
        # coming back lower (it cost L668 exactly). Taking every match instead
        # over-counts, because the fragments overlap. Both were measured.
        for m in REFUSAL.finditer(flat):
            start = max(0, m.start() - 110)
            frag = flat[start:m.start() + 150].strip()
            key = re.sub(r"[^a-z]", "", frag.lower())[:70]
            if len(frag) < MIN_FRAGMENT or key in seen:
                continue
            seen.add(key)
            found.append((n, frag))
            break
    return found


def _blob(ref, path):
    """(sha, text) for a path at a git ref. Bytes then decode explicitly."""
    r = subprocess.run(["git", "-C", REPO, "rev-parse", "%s:%s" % (ref, path)],
                       capture_output=True)
    if r.returncode:
        raise SystemExit("no blob for %s at %s" % (path, ref))
    sha = r.stdout.decode("utf-8", "replace").strip()
    b = subprocess.run(["git", "-C", REPO, "cat-file", "blob", sha],
                       capture_output=True).stdout
    return sha, b.decode("utf-8", "replace")


def main():
    # MODULE SCOPE WOULD CLOSE THE CALLER'S BUFFER. A module that rewraps
    # sys.stdout on import kills any wrapper its importer already installed --
    # it happened to this file's own reconciliation script minutes after it was
    # written. Rewrap only when run as a program.
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                  errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("--page", default="SGLT2_HF_REVIEW.html")
    ap.add_argument("--ref", default="origin/main")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    # --- controls, before any count is printed -----------------------------
    pos_line = ("<p>Figure 1 not drawn. this pool was withdrawn, and the reason "
                "is given in Results.</p>")
    neg_line = ("<p>The pooled estimate is 0.7636 (0.7062 to 0.8258) over three "
                "contributing trials, and the interval excludes no difference.</p>")
    require_controls(
        "enumerate_refusals",
        positive=("a fabricated line stating a figure was not drawn",
                  len(refusals_in(pos_line)), 1),
        negative=("a fabricated line reporting a pooled estimate plainly",
                  len(refusals_in(neg_line)), 1))

    sha, text = _blob(a.ref, a.page)
    rows = refusals_in(text)
    marker_lives = bool(REFUSAL.search(_plain(pos_line)))
    print(zero_has_a_reading(len(rows), marker_lives, "refusal statement(s)",
                             "%s @ %s" % (a.page, sha[:12])))

    payload = {
        "page": a.page,
        "ref_when_read": a.ref,
        "blob_sha": sha,
        "bytes": len(text.encode("utf-8")),
        "n_refusals": len(rows),
        "refusals": [{"line": n, "text": f} for n, f in rows],
        "what_this_records": (
            "That the page makes a refusal at this line, not that the refusal is "
            "correct. Its purpose is to make a later edit that REMOVES one visible "
            "as a diff rather than as silence."),
    }
    out = a.out or os.path.join(
        REPO, "outputs",
        "refusals_%s.json" % os.path.splitext(os.path.basename(a.page))[0])
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with io.open(out, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=1, ensure_ascii=False)
        fh.write("\n")
    print("wrote %s" % out)
    for n, f in rows:
        print("  L%-6d %s" % (n, f[:150]))


if __name__ == "__main__":
    main()
