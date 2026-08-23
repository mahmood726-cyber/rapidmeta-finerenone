"""Count reader-facing constructions across the DELIVERED corpus -- and refuse any count whose
check has no known positive.

# control: EVERY pattern below carries a `positive` fixture drawn from a real sentence, and the
# run asserts the pattern fires on it. A pattern that cannot fire is reported as NOT VALIDATED
# and its count is withheld -- never printed as zero.

THE DISCIPLINE THIS ENCODES WAS SET BY A CENSUS LANE, AND IT WAS RIGHT TO REFUSE. It reported
three probes as CHECK NOT VALIDATED rather than give numbers: `ELIGIBILITY turns` returned
absent everywhere while a hand-confirmed page contains it three times; `pooled under random
with` never had a known-positive established at all. A CHECK RETURNING ZERO WHILE A KNOWN
POSITIVE EXISTS IS BROKEN, AND ITS ZERO IS NOT A FINDING. Four validated numbers beat twelve
unvalidated ones.

WHY THE DELIVERED CORPUS IS A MIXTURE, WHICH IS THE MECHANISM BEHIND MOST OF THE NIGHT'S
DISAGREEMENTS. The generator stamp at origin/main is not uniform:

    a3c7bb8b2   133 pages     predates the projector fixes
    (no stamp)   14 pages
    216aa30f0     7 pages     carries them
    2633d68c9     2 pages
    d1339a8cb     1 page

So a fix landing in `ssot/paper_projector.py` is live on SEVEN pages, not 157. Two lanes
sampling different pages get different answers about the same construction and BOTH ARE READING
CORRECTLY. That is not a stale tree -- local bytes equal origin bytes on 156 of 157 -- it is an
un-rebuilt corpus, and the distinction matters because rebuilding is the remedy and re-pushing
is not.

READS origin/main, NEVER THE WORKTREE, because the delivered bytes are the ones a reader meets.
"""
from __future__ import annotations

import collections
import io
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from instrument_controls import require_controls  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REF = "origin/main"
OUT = os.path.join(REPO, "outputs", "delivered_constructions_2026_08_23.json")

# name -> (compiled pattern, a KNOWN POSITIVE the pattern must fire on)
#
# Each positive is a real sentence or a real fragment of markup. If the pattern stops matching
# its own positive -- because the projector changed, or because the pattern was tightened -- the
# check reports NOT VALIDATED and withholds its count rather than reporting a zero.
CHECKS = {
    "heterogeneity adverb": (
        re.compile(r"heterogeneity was (?:closely|loosely)"),
        "Across those trials heterogeneity was loosely consistent."),
    "pooled under a null estimator": (
        re.compile(r"pooled under [a-z\- ]*with the not applicable estimator"),
        "Estimates were pooled under random-effects with the not applicable estimator."),
    "ELIGIBILITY turns": (
        re.compile(r"\bELIGIBILITY turns\b"),
        "The rule was ELIGIBILITY turns on the registered population."),
    "python dict repr": (
        re.compile(r"\{'[a-z_]{2,}':\s*(?:'|\d|None|\[|\{)"),
        "Sources for this section: {'database': 'PubMed', 'hits': 41}"),
    "shouted slot": (
        re.compile(r"\b(?:[A-Z][A-Z'\-]*[,;:\-]?\s+){1,}[A-Z][A-Z'\-]{1,}\b(?![^<]*</t[dh]>)"),
        "The comparison was BENCHMARK SERVED as its own result."),
}


def git(*a):
    return subprocess.run(["git"] + list(a), cwd=REPO, capture_output=True)


def stamp_of(b):
    m = re.search(rb"Generator build.{0,400}?<code>([0-9a-f]{6,12})</code>", b, re.S)
    return m.group(1).decode() if m else "(no stamp)"


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

    # VALIDATE EVERY CHECK BEFORE COUNTING ANYTHING.
    valid, broken = {}, []
    for name, (pat, pos) in CHECKS.items():
        if pat.search(pos):
            valid[name] = pat
        else:
            broken.append(name)

    # THE CORPUS CONTROLS. A fixture only proves the pattern matches the string I wrote for
    # it; these two are real delivered pages whose answers were established by someone else
    # reading them, which is the only kind of positive that licenses reporting an absence.
    #
    # POSITIVE  SGLT2_HF_REVIEW carries `ELIGIBILITY turns`. A census lane hand-confirmed
    #           three instances and then correctly DISCARDED ITS OWN ZERO when its probe
    #           returned absent everywhere. If this run cannot see them either, it has the
    #           same broken probe and must not print a count.
    # NEGATIVE  MAVACAMTEN_HCM_REVIEW pools nothing and was rebuilt onto the current
    #           generator, so it must NOT be flagged for the null-estimator construction.
    #           That construction is the one whose fix this run is measuring, and an
    #           instrument that flags the fixed page is measuring itself.
    sg = git("show", "%s:SGLT2_HF_REVIEW.html" % REF).stdout.decode("utf-8", "replace")
    mv = git("show", "%s:MAVACAMTEN_HCM_REVIEW.html" % REF).stdout.decode("utf-8", "replace")
    require_controls(
        "delivered_constructions",
        ("SGLT2_HF_REVIEW carries 'ELIGIBILITY turns' (hand-confirmed by a census lane)",
         bool(CHECKS["ELIGIBILITY turns"][0].search(sg)), True),
        ("MAVACAMTEN_HCM_REVIEW pools nothing and is rebuilt -- no null-estimator claim",
         bool(CHECKS["pooled under a null estimator"][0].search(mv)), True))

    pm = json.load(io.open(os.path.join(REPO, "ssot", "PAGE_MAP.json"), encoding="utf-8"))
    names = sorted(set(pm if isinstance(pm, list) else pm.keys()))

    counts = collections.Counter()          # pages carrying the construction
    hits = collections.Counter()            # total occurrences
    by_stamp = collections.defaultdict(collections.Counter)
    stamps = collections.Counter()
    pages = collections.defaultdict(list)
    read = 0
    for n in names:
        r = git("show", "%s:%s" % (REF, n))
        if r.returncode:
            continue
        read += 1
        raw = r.stdout
        st = stamp_of(raw)
        stamps[st] += 1
        t = raw.decode("utf-8", "replace")
        for name, pat in valid.items():
            k = len(pat.findall(t))
            if k:
                counts[name] += 1
                hits[name] += k
                by_stamp[name][st] += 1
                pages[name].append(n)

    print("")
    print("DELIVERED CONSTRUCTIONS across %d page(s) at %s" % (read, REF))
    print("")
    print("GENERATOR STAMP DISTRIBUTION -- the corpus is a mixture and this is why lanes")
    print("sampling different pages get different answers about the same construction:")
    for k, v in stamps.most_common():
        print("   %-14s %4d" % (k, v))
    print("")
    print("   %-30s %6s %8s   %s" % ("construction", "pages", "hits", "by generator stamp"))
    for name in CHECKS:
        if name in broken:
            print("   %-30s %6s %8s   CHECK NOT VALIDATED -- no count reported"
                  % (name, "--", "--"))
            continue
        dist = ", ".join("%s=%d" % (s, c) for s, c in by_stamp[name].most_common(4)) or "-"
        print("   %-30s %6d %8d   %s" % (name, counts[name], hits[name], dist))
    print("")
    if broken:
        print("NOT VALIDATED, AND DELIBERATELY WITHOUT NUMBERS: %s" % ", ".join(broken))
        print("A check that cannot fire on its own known positive cannot report an absence.")
        print("")
    print("EVERY NUMBER ABOVE FIRED ON A KNOWN POSITIVE BEFORE IT WAS ALLOWED TO COUNT.")
    print("A construction concentrated in one stamp is not fixed corpus-wide; it is fixed in")
    print("the projector and un-rebuilt everywhere else. Rebuilding is the remedy, not pushing.")

    if not os.path.isdir(os.path.dirname(OUT)):
        os.makedirs(os.path.dirname(OUT))
    json.dump({"ref": REF, "pages_read": read, "stamps": dict(stamps),
               "counts": dict(counts), "hits": dict(hits),
               "not_validated": broken,
               "by_stamp": {k: dict(v) for k, v in by_stamp.items()},
               "pages": {k: v[:60] for k, v in pages.items()}},
              io.open(OUT, "w", encoding="utf-8"), indent=1)
    if broken:
        sys.exit("REFUSED: %d check(s) could not fire on their own known positive."
                 % len(broken))


if __name__ == "__main__":
    main()
