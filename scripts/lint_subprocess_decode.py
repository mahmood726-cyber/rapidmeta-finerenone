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
            # THE UNIT IS THE CALL, NOT THE LINE, AND THAT IS THE WHOLE FIX.
            #
            # The SAFE exemption for an explicit encoding= was evaluated PER LINE. A call
            # written across several physical lines --
            #     subprocess.run(args,
            #                    text=True,
            #                    encoding="utf-8", errors="replace")
            # -- carries text=True on one line and encoding= on the next, so the exemption
            # never saw it and the site was flagged. Correct code, refused by its own guard.
            #
            # This is the unit-of-analysis error that assessor_registry's detector 5 exists to
            # catch -- the check ran correctly on the WRONG UNIT -- and it appeared here, in
            # the lint that makes a lesson mechanical. Found when it blocked a commit of two
            # sites that were already doing exactly what it asks for.
            #
            # The window below widens each hit to its enclosing call before applying the
            # exemption, so SAFE is tested against the same call that carries the hazard.
            with io.open(p, encoding="utf-8", errors="replace") as fh:
                lines = fh.read().splitlines()
            for i, line in enumerate(lines, 1):
                if not PAT.search(line) or SKIP.search(line):
                    continue
                start = i - 1
                while start > 0 and "(" not in lines[start]:
                    start -= 1
                depth, end = 0, start
                for j in range(start, min(len(lines), start + 40)):   # bounded: cannot hang
                    depth += lines[j].count("(") - lines[j].count(")")
                    end = j
                    if depth <= 0 and j > start:
                        break
                call = chr(10).join(lines[start:end + 1])
                if SAFE.search(call) or SKIP.search(call):
                    continue
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
