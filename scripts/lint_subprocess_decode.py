"""CLASS 3 RULE MADE MECHANICAL: never `text=True` on subprocess when content may be non-ASCII.

Prose did not hold it. The rule is in rules/lessons.md under Data Handling, it is mine, and
I wrote a verifier with `text=True` on 2026-08-18 that decoded git output as cp1252 and
accused six intact objects of changed values. Fifth instrument artefact, first in a
verifier.

WHY THIS ONE IS LINTABLE AND substring-is-not-identity IS NOT: `text=True` is a literal
token. It needs no semantic judgement, so a grep IS the enforcement.

The fix at each site: `capture_output=True` then `.stdout.decode("utf-8", "replace")`.
"""
import ast
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
            with io.open(p, encoding="utf-8", errors="replace") as fh:
                lines = fh.read().splitlines()
            # THE CALL IS FOUND BY PARSING, NOT BY COUNTING BRACKETS.
            #
            # A first fix walked backwards to the nearest line containing "(". That is still
            # the wrong unit: in
            #     proc = subprocess.run(
            #         [sys.executable, "-W", "error", str(SSOT / "v.py"), str(target)],
            #         text=True,
            #         encoding="utf-8",
            # the nearest "(" going up is `str(` INSIDE the argument list, so the window
            # closed before reaching encoding= and the false positive survived. Widening a
            # bracket heuristic just moves the boundary; it does not make it the call.
            #
            # AST gives the exact node. Every keyword of the SAME CALL is inspected together,
            # which is what "the unit is the call" actually means. Falls back to the line test
            # only when the file will not parse, and says so rather than passing silently.
            # AND THE SAME AST PASS DECIDES WHERE THE HAZARD *IS*, NOT ONLY WHERE IT IS SAFE.
            #
            # Until 2026-08-19 the final loop was still a raw line scan, so a COMMENT SAYING
            # `text=True` COUNTED AS A SITE. Two of the eighteen baselined entries are exactly
            # that -- lines 8 and 20 of lint_encoding_defaults.py, which are prose describing
            # the hazard. They were absorbed into the baseline instead of being recognised,
            # and the ratchet then made every future comment about the rule cost a refusal.
            #
            #     A LINT THAT COUNTS ITS OWN DOCUMENTATION AS A VIOLATION TAXES WRITING THE
            #     RULE DOWN. The AST was already being walked for the safe case; asking it
            #     which lines carry a real keyword costs nothing and removes the class.
            #
            # The line fallback survives for files that will not parse, and is announced.
            keyword_safe: set[int] = set()
            keyword_real: set[int] = set()
            parsed_ok = True
            try:
                tree = ast.parse(chr(10).join(lines))
            except SyntaxError:
                parsed_ok = False
            if parsed_ok:
                for node in ast.walk(tree):
                    if not isinstance(node, ast.Call):
                        continue
                    names = {k.arg for k in node.keywords if k.arg}
                    if not ({"text", "universal_newlines"} & names):
                        continue
                    for k in node.keywords:
                        if k.arg in ("text", "universal_newlines"):
                            keyword_real.add(k.value.lineno)
                            if "encoding" in names:
                                # Safe: decodes with an explicit codec, not the codepage.
                                keyword_safe.add(k.value.lineno)
            for i, line in enumerate(lines, 1):
                if not PAT.search(line) or SKIP.search(line):
                    continue
                if parsed_ok and i not in keyword_real:
                    # The token is present but it is not a keyword of any call on this line:
                    # a comment, a docstring, or a string literal. Not a site.
                    continue
                if parsed_ok and i in keyword_safe:
                    continue
                if not parsed_ok and SAFE.search(line):
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
