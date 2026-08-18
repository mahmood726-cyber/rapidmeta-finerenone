"""CLASS 3 RULE MADE MECHANICAL: never `text=True` on subprocess when content may be non-ASCII.

Prose did not hold it. The rule is in rules/lessons.md under Data Handling, it is mine, and
I wrote a verifier with `text=True` on 2026-08-18 that decoded git output as cp1252 and
accused six intact objects of changed values. Fifth instrument artefact, first in a
verifier.

WHY THIS ONE IS LINTABLE AND substring-is-not-identity IS NOT: `text=True` is a literal
token. It needs no semantic judgement, so a grep IS the enforcement.

The fix at each site: `capture_output=True` then `.stdout.decode("utf-8", "replace")`.
"""
import io
import os
import re
import sys

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAT = re.compile(r"text\s*=\s*True|universal_newlines\s*=\s*True")
SKIP = re.compile(r"#\s*lint:allow-text-true")
# text=True WITH AN EXPLICIT ENCODING IS SAFE -- the hazard is the DEFAULT codepage, not
# text mode itself. Flagging `text=True, encoding="utf-8"` is a false positive, and a lint
# that cries wolf on correct code is how gates stop being read. Found when the ratchet
# refused a commit over two pre-existing sites that were already doing the right thing.
SAFE = re.compile(r"encoding\s*=\s*[\"']")


def main() -> int:
    hits = []
    for root, _, files in os.walk(os.path.join(REPO, "scripts")):
        for fn in files:
            if not fn.endswith(".py") or fn == os.path.basename(__file__):
                continue
            p = os.path.join(root, fn)
            for i, line in enumerate(io.open(p, encoding="utf-8", errors="replace"), 1):
                if PAT.search(line) and not SKIP.search(line) and not SAFE.search(line):
                    hits.append((os.path.relpath(p, REPO), i, line.strip()[:74]))
    for f, i, t in hits:
        print("%s:%d  %s" % (f, i, t))
    print()
    print("subprocess decode-hazard sites: %d" % len(hits))

    # A RATCHET, NOT A ZERO-GATE, and the reason is stated rather than assumed.
    # Gating at zero would have blocked the next commit behind a 28-site refactor,
    # and a guard that stops the work is a guard that gets bypassed -- which is
    # exactly how guard_write failed. The ratchet is mechanical TODAY: the count
    # can fall and can never rise. Each new site is refused at the moment it is
    # written, which is when it is cheapest to fix.
    base_file = os.path.join(REPO, ".lint-decode-baseline")
    base = 10 ** 9
    if os.path.exists(base_file):
        try:
            base = int(io.open(base_file, encoding="utf-8").read().strip())
        except Exception:
            pass
    if len(hits) > base:
        print("REFUSED: %d sites against a baseline of %d. A NEW decode hazard was "
              "introduced." % (len(hits), base))
        print("FIX: capture_output=True, then .stdout.decode('utf-8', 'replace').")
        print("Deliberate exception: append  # lint:allow-text-true  on the line.")
        return 1
    if len(hits) < base:
        io.open(base_file, "w", encoding="utf-8").write(str(len(hits)))
        print("baseline lowered to %d -- the ratchet only turns one way." % len(hits))
    return 0


if __name__ == "__main__":
    sys.exit(main())
