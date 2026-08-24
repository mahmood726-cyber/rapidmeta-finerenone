"""Pin three verified claims about `scripts/add_dta_tau2_ci_display.py`, and REFUSE if any moves.

# control: the POSITIVE is the artefact itself -- the three properties were read out of the
# file and the corpus by hand before this was written, and are re-derived here every run. The
# NEGATIVE is the latent/live distinction: this must NOT report a live defect while no page is
# half-patched, which is the state today.

WHERE THIS CAME FROM. A cold Codex lane, handed the module inline, returned three specific
claims. All three were checked against the artefact rather than believed. This file is that
check, kept so the verification is repeatable rather than a sentence in a commit message.

    1  A CHECK THAT CANNOT FAIL. `main()` holds exactly one return, `return 0`, and the only
       exit is `sys.exit(main())`. No input makes it exit non-zero -- an empty file list, or
       every file landing in `no_anchor`, still exits 0. A release check calling it passes on
       a run that changed nothing.

    2  AN IDEMPOTENCY GUARD SATISFIED BY ITS OWN OUTPUT. `FIXED_MARKER` is "Q-profile 95% CI"
       and that string appears INSIDE both `SENS_NEW` and `SPEC_NEW`. Writing either card
       plants the marker whose presence makes the file skip forever. It asks "has this text
       been seen" when the question is "have both cards been written".

    3  LATENT, NOT LIVE. All six `_DTA_REVIEW.html` pages carry both cards; nothing is
       half-patched, so the guard is not skipping real work today. The defect is real and not
       firing, and those are different statements.

AND THIS FILE ITSELF COULD NOT FAIL WHEN IT WAS FIRST WRITTEN. It printed verdicts and
returned nothing -- a verifier for a check-that-cannot-fail which could not fail, refused by
`lint_gate_can_fail` on the commit. It now refuses in two directions: if a pinned property
stops being true, and if the latent defect ever becomes LIVE.

AND MY FIRST VERSION OF CLAIM 1'S CHECK WAS WRONG. It matched `sys\\.exit\\(([^)]*)\\)`, which
stops at the first close-paren, so `sys.exit(main())` captured "main(" and it reported a TRUE
claim as "not as claimed". A pattern that cannot represent its subject, refuting correct work.
"""
from __future__ import annotations

import io
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SUBJECT = os.path.join(REPO, "scripts", "add_dta_tau2_ci_display.py")


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    if not os.path.isfile(SUBJECT):
        sys.exit("REFUSED: %s is gone. The pinned claims are about a file that no longer "
                 "exists, so this check has nothing to say and must not pass silently."
                 % os.path.relpath(SUBJECT, REPO))
    src = io.open(SUBJECT, encoding="utf-8").read()
    broken = []

    print("")
    print("CLAIM 1 -- no reachable non-zero exit")
    returns = re.findall(r"^\s{4}return\s+(.+)$", src, re.M)
    # THE WHOLE LINE, not a paren-balancing regex. `[^)]*` stopped at the first close-paren.
    exits = [l.strip() for l in src.splitlines() if "sys.exit" in l]
    raises = bool(re.search(r"\braise\b|exit\(1\)|exit\(2\)", src))
    print("   returns in main   %s" % returns)
    print("   exit line         %s" % exits)
    print("   any raise/nonzero %s" % raises)
    still = returns == ["0"] and exits == ["sys.exit(main())"] and not raises
    print("   %s" % ("CONFIRMED, unchanged" if still else
                     "MOVED -- the subject now has a way to fail; re-verify the finding"))
    if not still:
        broken.append("claim 1: the subject's exit behaviour changed")

    print("")
    print("CLAIM 2 -- the idempotency marker sits inside its own replacement text")
    m = re.search(r'FIXED_MARKER\s*=\s*"([^"]+)"', src)
    marker = m.group(1) if m else None
    in_sens = bool(marker) and marker in src.split("SENS_NEW", 1)[-1][:1400]
    in_spec = bool(marker) and marker in src.split("SPEC_NEW", 1)[-1][:1400]
    print("   FIXED_MARKER      %r" % marker)
    print("   inside SENS_NEW   %s" % in_sens)
    print("   inside SPEC_NEW   %s" % in_spec)
    if not marker:
        broken.append("claim 2: FIXED_MARKER is gone; the guard has been rewritten")
        print("   MOVED -- FIXED_MARKER no longer present")
    elif in_sens or in_spec:
        print("   CONFIRMED, unchanged -- the guard is still satisfied by its own output")
    else:
        print("   RESOLVED -- the marker no longer appears in the replacement text")

    print("")
    print("CLAIM 3 -- latent or live?")
    pages = sorted(f for f in os.listdir(REPO) if f.endswith("_DTA_REVIEW.html"))
    live = []
    for f in pages:
        t = io.open(os.path.join(REPO, f), encoding="utf-8", errors="replace").read()
        has = bool(marker) and marker in t
        sens_done = "tau&sup2; (Sens, logit)" in t
        spec_done = "tau&sup2; (Spec, logit)" in t
        if has and not (sens_done and spec_done):
            live.append(f)
        print("      %-42s marker=%-5s sens=%-5s spec=%-5s" % (f[:42], has, sens_done,
                                                               spec_done))
    print("")
    print("   pages the guard would skip while still incomplete: %d" % len(live))
    if live:
        print("   LIVE -- %s" % ", ".join(live))
        broken.append("claim 3: the defect is now FIRING on %d page(s): %s"
                      % (len(live), ", ".join(live)))
    else:
        print("   LATENT -- nothing is half-patched, so the guard skips no real work today.")

    print("")
    if broken:
        for b in broken:
            print("   %s" % b)
        sys.exit("REFUSED: %d pinned claim(s) no longer hold. A verified finding that has "
                 "moved is either fixed or worse, and either way it must be re-read rather "
                 "than left asserted." % len(broken))
    print("All three pinned claims still hold, and the defect is still latent.")


if __name__ == "__main__":
    main()
