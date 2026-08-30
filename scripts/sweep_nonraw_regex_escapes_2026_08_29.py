"""A word boundary written in a non-raw string is a backspace, and the check goes quiet.

FOUR TIMES IN ONE EVENING, IN THREE FILES, AND THREE OF THE FOUR HAD MADE A LIVE CHECK
INERT. `r"\\bPRISMA\\b"` written through a shell heredoc arrives as `"<BS>PRISMA<BS>"`.
The pattern compiles. It prints, in most terminals, as `PRISMA`. It matches nothing, the
check exits 0, and it reports good news.

THAT IS THE FAMILY, NOT THE BUG. Every silent instrument failure this project has found
returns good news: ripgrep honouring .gitignore and reporting no matches; `$?` read
through a pipe and reporting the exit code of `tail`; a truncated page reported as
reviewed; a filter that drops candidates before counting them. A check that dies loudly
is a nuisance. A check that dies quietly is worse than not having one, because it also
removes the doubt that would have made someone look.

WHAT THIS READS. The parsed value, not the text. `ast` gives what Python actually built,
and `ast.get_source_segment` gives what was written, so the two can be compared:

  ALREADY BROKEN   the compiled value contains a control character. `\\b` became 0x08.
                   This is a live defect: that alternative can match nothing.
  LATENT           the source is a non-raw literal containing a regex escape. It behaves
                   correctly today -- Python leaves `\\d` and `\\s` alone -- but it is one
                   heredoc away from the first case, and `\\b` in that position is silent.

The two are reported separately because they are not the same claim. Conflating them
would inflate a real count with a stylistic one, and this lane has already had to correct
one count downward tonight.

SCOPE IS STATED, NOT ASSUMED. It reads every .py file it can reach and prints the number
it parsed against the number it found, because a sweep that cannot say what it failed to
parse is reporting its reach as coverage.
"""
import ast
import io
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "outputs", "nonraw_regex_escapes_2026_08_29.json")

# Escapes Python INTERPRETS inside a non-raw literal. Each of these silently becomes a
# control character, and \b is the one that looks like a regex word boundary.
INTERPRETED = {"\x07": r"\a", "\x08": r"\b", "\x0c": r"\f", "\x0b": r"\v"}

# Escapes Python LEAVES ALONE in a non-raw literal. Harmless today, and one transport
# away from the case above.
LATENT = ("\\d", "\\s", "\\w", "\\b", "\\S", "\\W", "\\D", "\\A", "\\Z")

RE_CALLS = {"compile", "search", "match", "fullmatch", "findall", "finditer", "sub",
            "subn", "split"}


def looks_like_regex(s):
    return any(ch in s for ch in "\\[](){}|^$*+?") and len(s) > 2


# --------------------------------------------------------------------------
# KNOWN-NEGATIVE CONTROLS. A COUNT WITHOUT A MEASURED PRECISION IS NOT A FINDING.
# (source, expect_already_broken, expect_latent, why)
KNOWN_NEGATIVE_CONTROLS = [
    ('p = re.compile(r"\\bPRISMA\\b")', 0, 0,
     "a correctly written raw literal must not be flagged at all"),
    ('p = re.compile("\\bPRISMA\\b")', 1, 0,
     "a NON-raw literal: Python turns both boundaries into 0x08, already broken"),
    ('p = re.compile("\\\\bPRISMA\\\\b")', 0, 1,
     "a non-raw literal with the backslash escaped: behaves correctly, still latent"),
    ('s = "a plain sentence with no escapes"', 0, 0,
     "ordinary prose must never be flagged"),
    ('s = "C:\\\\Users\\\\mahmo"', 0, 0,
     "a Windows path is not a regex and its backslashes are deliberate"),
    ('print("done\\n")', 0, 0,
     "\\n is an intended newline, not a mangled regex escape"),
]


def scan_source(src, path="<control>"):
    """(already_broken, latent) for one file's source."""
    broken, latent = [], []
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return None, None
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Constant) and isinstance(node.value, str)):
            continue
        val = node.value
        seg = ast.get_source_segment(src, node) or ""
        hits = sorted(set(c for c in val if c in INTERPRETED))
        # A DETECTOR'S OWN VOCABULARY IS NOT AN INSTANCE OF WHAT IT DETECTS.
        # The first run flagged 8 sites and every one was a lookup-table key inside this
        # file or lint_escape_hazards.py -- the single control characters that DEFINE the
        # class. A control is not data; counting it as data is how a calibration page ends
        # up inside a statistic.
        #
        # The discriminator is length, not filename, so it cannot be gamed by moving code:
        # a vocabulary entry is the bare character, while a mangled regex always carries the
        # pattern it was written around it. a bare 0x08 alone is a definition; "<BS>PRISMA<BS>"
        # is a defect.
        if hits and len(val) <= 2:
            continue
        if hits:
            broken.append({"path": path, "line": node.lineno,
                           "became": [INTERPRETED[c] for c in hits],
                           "source": seg[:110]})
            continue
        # latent: a NON-raw literal carrying a regex escape
        prefix = seg[:2].lower()
        is_raw = seg.startswith(("r", "R")) or prefix in ("rb", "br", "fr", "rf")
        if is_raw or not seg:
            continue
        if looks_like_regex(val) and any(e in val for e in LATENT):
            latent.append({"path": path, "line": node.lineno, "source": seg[:110]})
    return broken, latent


def measure_precision(say):
    bad = 0
    for src, want_b, want_l, why in KNOWN_NEGATIVE_CONTROLS:
        b, l = scan_source(src)
        if b is None:
            bad += 1
            say("   CONTROL UNPARSEABLE: %s" % src[:60])
            continue
        if len(b) != want_b or len(l) != want_l:
            bad += 1
            say("   CONTROL FAILED  %-46s broken %d/%d latent %d/%d -- %s"
                % (src[:46], len(b), want_b, len(l), want_l, why))
    rate = 100.0 * bad / len(KNOWN_NEGATIVE_CONTROLS)
    say("   controls: %d/%d wrong (measured error rate %.1f%%)"
        % (bad, len(KNOWN_NEGATIVE_CONTROLS), rate))
    return bad


def main():
    raw = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                           write_through=True)

    def say(s):
        raw.write(s + chr(10))
        raw.flush()

    say("NON-RAW REGEX ESCAPE SWEEP")
    say("")
    say("PRECISION, measured before any count is reported:")
    if measure_precision(say):
        say("")
        say("REFUSED: the detector failed its own controls. Any count would be a statement "
            "about the matcher, not about the tree.")
        return 2
    if "--plant" in sys.argv:
        say("")
        say("PLANT -- constructed cases with known answers")
        ok = 0
        for src, wb, wl, why in KNOWN_NEGATIVE_CONTROLS:
            b, l = scan_source(src)
            good = b is not None and len(b) == wb and len(l) == wl
            ok += 1 if good else 0
            say("   [%s] %s" % ("PASS" if good else "FAIL", why))
        say("   plant: %d/%d" % (ok, len(KNOWN_NEGATIVE_CONTROLS)))
        return 0 if ok == len(KNOWN_NEGATIVE_CONTROLS) else 2
    say("")

    broken, latent, parsed, unparsed = [], [], 0, []
    for root, dirs, files in os.walk(REPO):
        dirs[:] = [d for d in dirs if d not in (".git", "node_modules", "__pycache__")]
        # POSITIVE SELECTION, AND A POSITIVE OUTCOME BRANCH.
        # This loop first read `if not fn.endswith(".py"): continue` and `if b is None:
        # continue`, and the repository's own ratchet refused the commit for both. It was
        # right to. A file skipped by a negative guard leaves no trace in the count, and
        # this whole sweep exists because silence reads as good news. Selecting the Python
        # files, and branching on a SUCCESSFUL parse, says the same thing without a path
        # through which an item can vanish.
        for fn in [f for f in files if f.endswith(".py")]:
            full = os.path.join(root, fn)
            rel = os.path.relpath(full, REPO).replace(os.sep, "/")
            try:
                src = io.open(full, encoding="utf-8", errors="replace").read()
                b, l = scan_source(src, rel)
            except OSError:
                b, l = None, None
            if b is not None:
                parsed += 1
                broken.extend(b)
                latent.extend(l)
            else:
                unparsed.append(rel)

    say("SCOPE, before the counts")
    say("   Python files parsed:          %d" % parsed)
    say("   Python files that would NOT parse (not scanned, not clean): %d" % len(unparsed))
    for u in unparsed[:8]:
        say("      %s" % u)
    say("")
    say("ALREADY BROKEN -- the compiled value holds a control character: %d" % len(broken))
    for h in broken[:40]:
        say("   %-56s:%-5d %s   %s"
            % (h["path"][:56], h["line"], ",".join(h["became"]), h["source"][:60]))
    say("")
    say("LATENT -- a non-raw literal carrying a regex escape, correct today: %d" % len(latent))
    byfile = {}
    for h in latent:
        byfile.setdefault(h["path"], []).append(h["line"])
    for f in sorted(byfile, key=lambda x: -len(byfile[x]))[:20]:
        say("   %-64s %d" % (f[:64], len(byfile[f])))

    json.dump({"n_parsed": parsed, "unparsed": unparsed,
               "already_broken": broken, "latent": latent},
              io.open(OUT, "w", encoding="utf-8"), indent=1)
    say("")
    say("wrote %s" % os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    sys.exit(main())
