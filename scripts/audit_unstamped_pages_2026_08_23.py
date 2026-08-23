"""How many delivered pages declare their standard UNSTAMPED -- excluding the sentence about
another topic being unstamped.

# control: routed through require_controls with the two shapes read by hand. POSITIVE is
# MAVACAMTEN_HCM_REVIEW, whose footer reads "Page standard UNSTAMPED -- unknown-version. This
# page carries no build_stamp". NEGATIVE is SGLT2_HF_REVIEW, which is STAMPED and merely
# mentions that a DIFFERENT topic is unstamped -- and which a naive substring match on
# "unstamped" flags. If the negative control is flagged, no count is printed.

THE EXCLUSION RULE, STATED RATHER THAN IMPLIED. Two footers contain the word "unstamped" and
they say opposite things:

  TRUE   MAVACAMTEN: "Page standard UNSTAMPED -- unknown-version. This page carries no
         build_stamp, so the standard it was built to cannot be established. That is a
         statement about the record, not a claim that the page is below standard."

  FALSE  SGLT2:      "This page is stamped to the standard version above. If the standard
         rises, this page is below it and knowably so. No page is grandfathered; ARNI-HFREF
         IS PRESENTLY UNSTAMPED and is therefore unknown-version, not compliant."

The second page is stamped. It is describing ANOTHER TOPIC's state, in a sentence whose whole
purpose is to refuse grandfathering. A substring match on "unstamped" reports it as unstamped,
which inverts the meaning of the sentence it matched.

SO THE PREDICATE IS THE PAGE'S CLAIM ABOUT ITSELF: "Page standard UNSTAMPED" or "this page
carries no build_stamp". The `<topic> is presently unstamped` clause is removed from the text
BEFORE matching, and the negative control asserts that removal works.

This is the same class as the container probe that searched for braces: a check keyed to a
token rather than to the claim a reader meets. Here the token appears on both sides of the
distinction.
"""
from __future__ import annotations

import io
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from instrument_controls import require_controls          # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REF = "origin/main"
OUT = os.path.join(REPO, "outputs", "unstamped_pages_2026_08_23.json")

# THE EXCLUSION: a clause about some OTHER topic's stamp state, stripped before matching.
OTHER_TOPIC = re.compile(
    r"(?i)\b[a-z0-9][a-z0-9\-_]{2,}\s+is\s+presently\s+unstamped[^.]*\.")
# THE PAGE'S CLAIM ABOUT ITSELF.
SELF_UNSTAMPED = re.compile(
    r"(?i)(page standard\s+unstamped|this page carries no\s*<?[^>]*>?\s*build_stamp)")


def git(*a):
    return subprocess.run(["git"] + list(a), cwd=REPO, capture_output=True)


def declares_unstamped(html):
    t = re.sub(r"<[^>]+>", " ", html)
    t = OTHER_TOPIC.sub(" ", t)          # <- the exclusion, applied before the match
    return bool(SELF_UNSTAMPED.search(re.sub(r"\s+", " ", t)))


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    mv = git("show", "%s:MAVACAMTEN_HCM_REVIEW.html" % REF).stdout.decode("utf-8", "replace")
    sg = git("show", "%s:SGLT2_HF_REVIEW.html" % REF).stdout.decode("utf-8", "replace")
    require_controls(
        "unstamped_pages",
        ("MAVACAMTEN declares itself UNSTAMPED (read by hand)", declares_unstamped(mv), True),
        ("SGLT2 is STAMPED and only mentions arni-hfref being unstamped -- must not be flagged",
         declares_unstamped(sg), True))

    pm = json.load(io.open(os.path.join(REPO, "ssot", "PAGE_MAP.json"), encoding="utf-8"))
    names = sorted(set(pm if isinstance(pm, list) else pm.keys()))
    flagged, naive, read = [], [], 0
    for n in names:
        r = git("show", "%s:%s" % (REF, n))
        if r.returncode:
            continue
        read += 1
        t = r.stdout.decode("utf-8", "replace")
        if declares_unstamped(t):
            flagged.append(n)
        if re.search(r"(?i)unstamped", t):
            naive.append(n)

    print("")
    print("PAGES DECLARING THEIR OWN STANDARD UNSTAMPED, %d delivered page(s) at %s"
          % (read, REF))
    print("")
    print("   declare THEMSELVES unstamped               %4d   %5.1f%%"
          % (len(flagged), 100.0 * len(flagged) / max(1, read)))
    print("   contain the word 'unstamped' anywhere      %4d   %5.1f%%"
          % (len(naive), 100.0 * len(naive) / max(1, read)))
    print("   FALSE POSITIVES a naive match would report %4d"
          % (len(naive) - len(flagged)))
    print("")
    print("   The gap is the `<topic> is presently unstamped` clause -- a sentence whose")
    print("   purpose is to refuse grandfathering, on pages that ARE stamped. Matching the")
    print("   token instead of the claim inverts the meaning of the sentence it matched.")
    json.dump({"ref": REF, "read": read, "unstamped": flagged,
               "naive_match": naive}, io.open(OUT, "w", encoding="utf-8"), indent=1)
    print("")
    print("written: %s" % os.path.relpath(OUT, REPO))


if __name__ == "__main__":
    main()
