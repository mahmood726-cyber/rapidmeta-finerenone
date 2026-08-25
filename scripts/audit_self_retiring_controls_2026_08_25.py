"""Which checks have a control that is the defect they hunt?

THE RULE, EARNED BY AN AUDIT DOING IT TO ITSELF:

    A CONTROL MUST BE A CASE THAT STILL FAILS, OR THE INSTRUMENT RETIRES ITSELF THE MOMENT
    IT SUCCEEDS.

`audit_tidy_blanks_a_value` used `watched("excluded")` as its positive control -- a bare
status word being blanked, which was exactly the defect it existed to find. The moment that
was fixed the control stopped holding, and the audit refused to print any count. It failed
closed, which is the good outcome. A check whose control degrades the other way is the
dangerous one: it certifies silence.

TWO SHAPES OF CONTROL, and only one survives its own success:

  SYNTHETIC   the control constructs its input inline -- a planted string, a hand-built
              dict, a fixture. Fixing the corpus cannot touch it. Durable.

  LIVE        the control points at a real page, object or slug that currently carries the
              defect. Fix that instance and the control is testing a case that no longer
              exists.

A LIVE control is not wrong, and this does not propose replacing them wholesale: pointing at
a real instance is the strongest possible evidence that a check works ON THIS CORPUS. It is
FRAGILE, which is a different thing, and the fragility is invisible until the day the
instance is fixed and somebody reads a clean report.

WHAT THIS PRODUCES is a shortlist for human review, not a verdict. Each LIVE control needs a
person to ask: when this instance is fixed, does the check fail closed like the tidy audit
did, or does it quietly start passing?

CONTROL FOR THIS AUDIT, and it is deliberately synthetic so this file does not commit the
error it hunts: a constructed LIVE-shaped snippet must be classified LIVE, and a constructed
SYNTHETIC-shaped one must not.
"""
import io
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "scripts"))

from instrument_controls import require_controls          # noqa: E402

# A control that reaches for the corpus. Page names, object paths, globs, file reads --
# anything whose truth depends on what is currently on disk.
_LIVE = re.compile(
    r"[A-Z][A-Z0-9_]{6,}\.html|ssot/|ssot\\\\|glob\.|io\.open|open\(|\.json['\"]|"
    r"delivered|read_text|listdir|PAGE_MAP", re.I)


def controls_in(src):
    """(name, positive_expression) for every require_controls call in a source file."""
    out = []
    for m in re.finditer(r"require_controls\(", src):
        depth, i = 0, m.end() - 1
        while i < len(src):
            if src[i] == "(":
                depth += 1
            elif src[i] == ")":
                depth -= 1
                if depth == 0:
                    break
            i += 1
        call = src[m.end():i]
        # the positive is either the kwarg or the second positional argument
        pm = re.search(r"positive\s*=\s*\((.*?)\)\s*,\s*(?:negative|$)", call, re.S)
        pos = pm.group(1) if pm else call
        name = re.match(r'\s*["\']([^"\']+)["\']', call)
        out.append((name.group(1) if name else "?", " ".join(pos.split())))
    return out


def main():
    require_controls(
        "audit_self_retiring_controls",
        positive=("a control that names a delivered page is classified LIVE",
                  bool(_LIVE.search('("dead link found", scan("SGLT2_HF_REVIEW.html"), True)')),
                  True),
        negative=("a control that builds its input inline must NOT be classified LIVE",
                  bool(_LIVE.search('("a planted repr is caught", flags("[\'a\', \'b\']"), True)')),
                  True))
    print()

    live, synth = [], 0
    for root, dirs, files in os.walk(os.path.join(REPO, "scripts")):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for fn in [f for f in files if f.endswith(".py")]:
            p = os.path.join(root, fn)
            if os.path.basename(p) == os.path.basename(__file__):
                continue
            try:
                src = io.open(p, encoding="utf-8", errors="replace").read()
            except OSError:
                continue
            for name, pos in controls_in(src):
                if _LIVE.search(pos):
                    live.append((os.path.relpath(p, REPO), name, pos[:150]))
                else:
                    synth += 1

    L = ["CHECKS DECLARING A CONTROL VIA require_controls: %d" % (len(live) + synth), "",
         "  control built from a SYNTHETIC input (durable)   : %d" % synth,
         "  control pointing at a LIVE corpus instance       : %d" % len(live), "",
         "A LIVE control is the strongest evidence a check works on THIS corpus, and the",
         "most fragile: fix the instance and the control tests a case that no longer exists.",
         "Each needs a person to ask whether the check then FAILS CLOSED, as the tidy audit",
         "did, or quietly starts passing.", ""]
    for path, name, pos in sorted(live):
        L.append("  %s" % path)
        L.append("      control %-34s %s" % (name, pos[:110]))
    io.open(os.path.join(REPO, "outputs", "self_retiring_controls_2026_08_25.txt"),
            "w", encoding="utf-8").write("\n".join(L))
    print("\n".join(L[:60]))
    return 0


sys.exit(main())
