"""A regex escape in a non-raw literal, and the silent-good-news family it belongs to.

FOUR TIMES IN ONE EVENING, IN THREE FILES UNDER scripts/lane_rob, AND THREE OF THE FOUR
HAD MADE A LIVE CHECK INERT. A word boundary written through a shell heredoc arrives as a
literal 0x08: `r"\\bPRISMA\\b"` becomes `"<BS>PRISMA<BS>"`. It compiles. It prints, in most
terminals, as `PRISMA`. It matches nothing, the check exits 0, and it reports good news.

THAT IS THE FAMILY, AND IT IS THE ONE THAT KEEPS COSTING US. Every silent instrument
failure this project has found returns GOOD NEWS: ripgrep honouring .gitignore and
reporting no matches; `$?` read through a pipe returning the exit code of `tail`; a
truncated page reported as reviewed; a filter dropping candidates before they were
counted; a gate whose plant no longer trips it. A check that dies loudly is a nuisance. A
check that dies quietly is worse than no check, because it also removes the doubt that
would have made someone look.

TWO CLASSES, REPORTED SEPARATELY BECAUSE THEY ARE NOT THE SAME CLAIM.

  ALREADY BROKEN   the compiled value holds a control character. That alternative can
                   match nothing. This is a live defect and the gate refuses ANY of them --
                   there is no baseline, because zero is the only defensible number and
                   the tree is at zero.
  LATENT           a non-raw literal carrying a regex escape. Correct today: Python leaves
                   `\\d` and `\\s` alone. One transport away from the first class, and `\\b`
                   in that position fails silently. Ratcheted at the measured 122, which
                   may fall and must not rise.

Conflating the two would inflate a real count with a stylistic one. This lane has already
had to correct one count downward tonight and does not intend to earn a second.
"""
from __future__ import annotations

import io
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _harness as H                                                        # noqa: E402

DETECTOR = os.path.join("scripts", "sweep_nonraw_regex_escapes_2026_08_29.py")
RESULT = os.path.join("outputs", "nonraw_regex_escapes_2026_08_29.json")
BACKLOG = "NONRAW_REGEX_ESCAPE_BACKLOG.json"


def main(argv):
    gate = H.Gate("13 NON-RAW REGEX ESCAPE",
                  "a word boundary written as a control character makes a check inert")
    # THE NAMED CASE IS THE DETECTOR'S ABILITY TO TELL THE TWO CLASSES APART. Naming a
    # specific broken file would make this gate go vacuous the moment that file is fixed --
    # and all four known instances were fixed hours before this gate existed.
    gate.expect_case("discriminates",
                     "a non-raw \\b is caught as ALREADY BROKEN while an escaped one is "
                     "only LATENT and a raw literal is neither")
    gate.requires_control()

    repo = H.repo_root()
    path = os.path.join(repo, DETECTOR)
    if not os.path.exists(path):
        gate.broken("%s is absent; this gate RUNS the detector rather than reimplementing "
                    "it." % DETECTOR)
        gate.kinds({"detector present": 0, "detector absent": 1})
        return gate.report(denominator="0 files -- the detector could not run")

    plant = subprocess.run([sys.executable, path, "--plant"], cwd=repo, capture_output=True)
    pout = plant.stdout.decode("utf-8", "replace")
    held = plant.returncode == 0 and pout.count("[PASS]") == 6
    if held:
        gate.control(6, 0, [], accuses=True)
        gate.saw("discriminates")
    else:
        gate.control(6, 6, ["the detector's own plant did not hold"], accuses=True)
        gate.broken("the detector's plant did not pass 6/6, so its counts are not usable. "
                    "stdout: %s" % pout[-300:].replace(chr(10), " "))

    proc = subprocess.run([sys.executable, path], cwd=repo, capture_output=True)
    if proc.returncode == 2:
        gate.broken("the detector REFUSED its own controls: %s"
                    % proc.stdout.decode("utf-8", "replace")[-300:].replace(chr(10), " "))
        gate.kinds({"files reached": 0})
        return gate.report(denominator="the detector refused rather than reporting a pass")

    try:
        doc = json.load(io.open(os.path.join(repo, RESULT), encoding="utf-8"))
    except Exception as e:
        gate.broken("the detector ran but its result could not be read: %s" % e)
        gate.kinds({"result file readable": 0})
        return gate.report(denominator="no result to ratchet")

    broken = doc.get("already_broken") or []
    latent = doc.get("latent") or []
    parsed = doc.get("n_parsed", 0)
    unparsed = doc.get("unparsed") or []

    found = ["%s:%d" % (h["path"], h["line"]) for h in latent]
    if "--plant" in argv:
        found.append("__control_planted_file.py:1")
        gate.note("PLANTED: a new non-raw literal carrying a regex escape")

    new = H.ratchet(gate, BACKLOG, found,
                    "non-raw string literals carrying a regex escape, which behave "
                    "correctly today and fail silently if ever re-transported.")

    gate.kinds({
        "Python files parsed": parsed,
        "Python files that would not parse": len(unparsed),
        "ALREADY BROKEN -- the value holds a control character": len(broken),
        "LATENT -- non-raw literal with a regex escape": len(latent),
        "of those, NEW since the freeze": len(new),
    })
    gate.coverage(parsed, parsed + len(unparsed),
                  "Python files that would not parse, which were not scanned and are "
                  "therefore neither clean nor dirty")
    gate.note("the four instances that motivated this gate were repaired hours before it "
              "existed, so ALREADY BROKEN standing at %d is the repaired state, not an "
              "untouched one. There is no baseline for that class: zero is the only "
              "defensible number." % len(broken))
    gate.note("LATENT is ratcheted, not blocked. Rewriting 122 literals across the tree "
              "would be a class-wide edit nobody asked for; stopping the 123rd is the "
              "property that was missing.")

    # ALREADY BROKEN IS REFUSED OUTRIGHT, WITH NO BASELINE. A live defect that makes a
    # check inert does not get a grandfather clause.
    for h in broken:
        gate.finding("REGEX-ESCAPE-IS-A-CONTROL-CHARACTER",
                     "%s:%d compiled a literal containing %s. That alternative can match "
                     "nothing, so whatever this check reports, it reports it without "
                     "looking. Source: %s"
                     % (h["path"], h["line"], ",".join(h["became"]), h["source"][:70]),
                     numerator=len(broken), denominator=parsed)

    for f in new:
        gate.finding("NEW-NONRAW-REGEX-LITERAL",
                     "%s is a new non-raw string literal carrying a regex escape. It is "
                     "correct today and silent if it is ever moved through a shell. Write "
                     "it as a raw literal." % f,
                     numerator=len(new), denominator=len(latent))

    return gate.report(denominator="%d Python files parsed; %d latent, %d frozen"
                       % (parsed, len(latent), len(found) - len(new)))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
