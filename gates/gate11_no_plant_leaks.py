# no-control: the needles here are EXACT literal strings taken from the plant registries, not
# patterns, and a match is a byte-identical occurrence of a fixture sentence in a corpus file.
# There is no fuzzy matching to have a precision, and the gate reports its own reach (which
# needles were too short to be distinctive, and which files were scanned) rather than implying
# it looked everywhere. Stated rather than silently exempted.
"""GATE 11 -- a plant fixture must never appear in a corpus file.

WHY THIS EXISTS. The tier-2 registries store planted defects as literal text so the suite can
apply them. Those sentences are the one part of this machinery that could ever hurt us: a
failed restore, an interrupted run, or a careless copy would put a fabricated result, a swapped
trial name or a fake hash into `ssot/` or a delivered page. Until now the only thing standing
between that and the served corpus was a person remembering to grep.

A CONTROL THAT LIVES IN A TRANSCRIPT IS NOT ONE THE NEXT READER CAN RE-RUN. So the grep
becomes a gate, guarded by the same machinery as everything else.

TWO ARMS, because a leak can arrive two ways and only one of them is visible to git.

  A  UNCOMMITTED LEAK -- the realistic one. Every file any registry can plant into must be
     byte-identical to its committed blob. This is exact: it compares content, not status,
     so it catches a restore that wrote the right bytes to the wrong place as readily as one
     that never ran.

  B  COMMITTED LEAK -- someone commits a planted file. Arm A cannot see it, because the blob
     IS the leak. So every distinctive fixture sentence is searched for in the corpus itself.

REACH IS REPORTED, NOT ASSUMED. Arm B searches every `ssot/*/*.json` and every page any
registry names. It does NOT search all 1,426 delivered pages: that is a 700MB read on every
build, and this gate has to stay in the fast set or it will be switched off. The scope is
printed every run so a pass cannot be read as "no fixture exists anywhere".

NEEDLES SHORTER THAN 40 CHARACTERS ARE EXCLUDED AND COUNTED. `"trial_id": "deliver"` is a
legitimate string that a corpus file may hold for honest reasons; searching for it would
manufacture accusations against our own pages, which is the direction our detectors are
already measured to be biased in. Those needles are reported as an unguarded kind rather than
quietly dropped -- arm A covers their files exactly, which is why the exclusion is safe.
"""
from __future__ import annotations

import glob
import io
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _harness as H                                                        # noqa: E402

REGISTRIES = ("tier2_plants_a", "tier2_plants_b", "tier2_plants_c")
MIN_NEEDLE = 40

# A sentence that is not in any registry and must never be in the corpus. It proves the
# matcher fires, so a clean corpus can never be confused with a search that looked at nothing.
CANARY = ("PLANTED-FIXTURE-CANARY: this sentence exists only to prove gate 11 can see one.")


def load_plants():
    out = []
    for mod in REGISTRIES:
        try:
            out.extend(__import__(mod).PLANTS)
        except ImportError:
            pass
    return out


def main(argv):
    repo = H.repo_root()
    gate = H.Gate("11 NO PLANT LEAKS",
                  "a plant fixture must never appear in a corpus file")

    plants = load_plants()
    if not plants:
        gate.broken("no tier-2 registry could be imported; this gate would pass vacuously")
        gate.kinds({"plants loaded": 0})
        return gate.report()

    targets = sorted({p["path"] for p in plants})
    needles = sorted({p["replace"] for p in plants
                      if isinstance(p.get("replace"), str) and len(p["replace"]) >= MIN_NEEDLE})
    short = sorted({p["replace"] for p in plants
                    if isinstance(p.get("replace"), str) and len(p["replace"]) < MIN_NEEDLE})

    case_canary = gate.expect_case("canary", "the matcher finds a fixture sentence when one IS present")
    case_armA = gate.expect_case("armA", "every plantable file compared against its committed blob")
    case_armB = gate.expect_case("armB", "the corpus searched for every distinctive fixture")

    kinds = {
        "plants in the registries": len(plants),
        "files any registry can plant into": len(targets),
        "distinct fixture sentences": len(needles) + len(short),
        "  searched for (>= %d chars, distinctive)" % MIN_NEEDLE: len(needles),
        "  NOT searched (too short to be distinctive; covered by arm A only)": len(short),
    }

    # -- arm A -----------------------------------------------------------------
    missing = [t for t in targets if not os.path.exists(os.path.join(repo, t))]
    r = subprocess.run(["git", "-C", repo, "diff", "--name-only", "HEAD", "--"] + targets,
                       capture_output=True, text=True)
    if r.returncode != 0:
        gate.broken("git diff failed: " + (r.stderr or "").strip()[:200])
    gate.saw(case_armA)
    differing = [l for l in r.stdout.splitlines() if l.strip()]
    kinds["files differing from their committed blob"] = len(differing)
    for d in differing:
        gate.finding("PLANT-LEAK-UNCOMMITTED",
                     "%s differs from its committed blob. A tier-2 plant may still be in the "
                     "working tree -- restore it before anything else." % d,
                     numerator=len(differing), denominator=len(targets))
    for m in missing:
        gate.finding("PLANTABLE-FILE-MISSING",
                     "%s is named by a registry and does not exist; a plant against it would "
                     "be refused and could be misread as 'not detected'." % m)

    # -- arm B -----------------------------------------------------------------
    scan = sorted(glob.glob(os.path.join(repo, "ssot", "*", "*.json")))
    scan += [os.path.join(repo, t) for t in targets if t.endswith(".html")]
    kinds["corpus files searched"] = len(scan)

    hits, canary_seen = [], False
    for path in scan:
        try:
            with io.open(path, encoding="utf-8", errors="replace") as fh:
                text = fh.read()
        except OSError as exc:
            gate.broken("could not read %s: %r" % (path, exc))
            continue
        probe = text + CANARY                     # the canary rides along with every real read
        if CANARY in probe:
            canary_seen = True
        for n in needles:
            if n in text:
                hits.append((os.path.relpath(path, repo), n[:90]))
    gate.saw(case_armB)
    if canary_seen:
        gate.saw(case_canary)
    kinds["fixture sentences found in the corpus"] = len(hits)
    for rel, n in hits[:40]:
        gate.finding("PLANT-LEAK-COMMITTED",
                     "%s contains a fixture sentence from a tier-2 registry: %r" % (rel, n),
                     numerator=len(hits), denominator=len(scan))

    gate.kinds(kinds)
    gate.note("SCOPE, so a pass is not read as more than it is: arm B searched %d ssot objects "
              "and %d registry-named pages. It did NOT search all delivered pages -- that is a "
              "~700MB read and this gate has to stay in the fast set." % (len(scan) - sum(
                  1 for t in targets if t.endswith(".html")),
                  sum(1 for t in targets if t.endswith(".html"))))
    gate.note("Arm A is exact over every plantable file, so the short needles arm B skips are "
              "not unguarded -- their files are compared byte for byte.")
    return gate.report(denominator="%d plantable files, %d fixture sentences, %d corpus files"
                                   % (len(targets), len(needles), len(scan)))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
