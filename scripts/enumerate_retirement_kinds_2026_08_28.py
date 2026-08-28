"""Enumerate the KINDS before any count, and state every overlap.

WHY THIS RUNS BEFORE ANYTHING IS REMOVED. Four denominators on this project have been wrong
because a count was taken before the kinds in the population were enumerated. A removal is
worse than a count: it is not reversible from the reader's side.

THE SETS ARE DEFINED BY DIFFERENT INSTRUMENTS AT DIFFERENT TIMES and there is no reason to
assume they are disjoint. Each is recomputed here from the corpus rather than quoted, and
every pairwise overlap is printed -- including the empty ones, because an overlap of zero is a
finding and an unstated overlap is a guess.

WHAT THIS CAN AND CANNOT SEE, stated rather than glossed:

  MEASURABLE HERE   refused-to-build, result-less shells, withdrawn/superseded pools,
                    redirect notices, pages absent from PAGE_MAP
  NOT LOCATABLE     the 67 verdict-only, the 287 orphans, the 515 protocol-points-nowhere.
                    Those were produced by other lanes and their artefacts are not in this
                    worktree. They are NAMED as gaps rather than estimated, because a
                    reconciled table with an invented row is worse than an incomplete one.

VERDICT-ONLY IS DELIBERATELY NOT COMPUTED as a retirement candidate. A verdict-only page is a
legitimate output: it records that trials were assessed and found not poolable, and "none is
coming" answers a real question. It is counted here only so its overlap with the other sets is
visible.
"""
import collections
import io
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "scripts"))
OUT = os.path.join(REPO, "outputs", "retirement_kinds_2026_08_28.json")

SCRIPT = re.compile(r"<script\b.*?</script>", re.S | re.I)
STYLE = re.compile(r"<style\b.*?</style>", re.S | re.I)
TAG = re.compile(r"<[^>]+>")
INTERVAL = re.compile(r"\d+\.\d+\s*[\(\[]\s*(?:95\s*%?\s*(?:CI|CrI)\s*[:,]?\s*)?"
                      r"-?\d+\.\d+\s*(?:to|,|-)\s*-?\d+\.\d+\s*[\)\]]")
REDIRECT = re.compile(r"Moved, not removed|has moved|canonical page|superseded by", re.I)


def carries_estimate(t):
    """Does the page carry an estimate of ANY recognised shape? A POSITIVE test.

    Three shapes, because the corpus writes estimates three ways and requiring one of them
    is how 758 pages were nearly removed as result-less:
      a bracketed interval    0.85 (0.72 to 0.99)
      a measure and a value   HR = 0.85 / OR: 1.２ / MD -5.69
      a stated interval type  95% CI / 95% CrI
    """
    return bool(INTERVAL.search(t)
                or re.search(r"\b(?:HR|OR|RR|MD|SMD|IRR)\s*[=:]?\s*-?\d+\.\d+", t)
                or re.search(r"95\s*%\s*(?:CI|CrI)", t, re.I))


def text(h):
    return re.sub(r"\s+", " ", TAG.sub(" ", STYLE.sub(" ", SCRIPT.sub(" ", h or "")))).strip()


def main():
    raw = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                           write_through=True)

    def say(s):
        raw.write(s + chr(10))
        raw.flush()

    pm = json.load(io.open(os.path.join(REPO, "ssot", "PAGE_MAP.json"), encoding="utf-8"))
    pages = sorted(f for f in os.listdir(REPO)
                   if f.lower().endswith(".html") and os.path.isfile(os.path.join(REPO, f)))

    sets = collections.OrderedDict()
    sets["all served root pages"] = set(pages)
    sets["in PAGE_MAP (has a store)"] = set(pm)
    sets["NOT in PAGE_MAP (no store)"] = set(pages) - set(pm)

    refused, withdrawn, redirects, apparatus = set(), set(), set(), set()
    with_estimate = set()
    for p in pages:
        h = io.open(os.path.join(REPO, p), encoding="utf-8", errors="replace").read()
        t = text(h)
        has_interval = bool(INTERVAL.search(t))
        has_apparatus = bool(re.search(r"PRISMA|GRADE|AMSTAR|risk of bias", t, re.I))
        if REDIRECT.search(t) and len(t) < 6000:
            redirects.add(p)
        if has_apparatus:
            apparatus.add(p)
            if carries_estimate(t):
                with_estimate.add(p)
    for p, path in pm.items():
        fp = os.path.join(REPO, path)
        if not os.path.exists(fp):
            continue
        o = json.load(io.open(fp, encoding="utf-8"))
        by = (o.get("results") or {}).get("by_outcome") or {}
        if not o.get("title") and not by:
            refused.add(p)
        for blk in by.values():
            if isinstance(blk, dict) and any(
                    "withdraw" in k.lower() or "supersed" in k.lower() for k in blk):
                withdrawn.add(p)
                break

    # THE SHELLS ARE A SET DIFFERENCE, NOT A NEGATED TEST IN A LOOP.
    #
    # The loop collects only POSITIVE facts: this page carries apparatus, this page carries
    # an estimate. The shells fall out as apparatus-minus-estimate afterwards. That is the
    # same set the negated form would produce and it is arrived at without ever asking "is
    # this thing absent" while iterating -- which is the shape that let 758 pages be
    # selected as result-less because their estimates were written in a form the detector
    # did not recognise. Both sides of the partition are reported, so the absence half is
    # never the only thing measured.
    shells = apparatus - with_estimate
    sets["carries apparatus AND an estimate"] = with_estimate
    sets["refused to build (no title, no results)"] = refused
    sets["apparatus but NO interval (result-less shell)"] = shells
    sets["carries a withdrawn/superseded pool"] = withdrawn
    sets["redirect / moved notice"] = redirects

    say("KINDS, each recomputed from the corpus rather than quoted")
    say("")
    for k, v in sets.items():
        say("  %-46s %5d" % (k, len(v)))
    say("")
    say("NOT LOCATABLE IN THIS WORKTREE, named rather than estimated:")
    say("  the 67 verdict-only    -- other lane's artefact, definition not available here")
    say("  the 287 orphans        -- other lane's artefact")
    say("  the 515 protocol-points-nowhere -- other lane's artefact")
    say("  A reconciled table with an invented row is worse than an incomplete one.")
    say("")
    say("PAIRWISE OVERLAPS (zero is a finding, unstated is a guess)")
    keys = [k for k in sets if k not in ("all served root pages",)]
    say("")
    for i, a in enumerate(keys):
        for b in keys[i + 1:]:
            n = len(sets[a] & sets[b])
            say("  %-44s x %-44s %5d" % (a[:44], b[:44], n))

    json.dump({"note": "kinds enumerated before any removal; sets recomputed, not quoted",
               "not_locatable": ["67 verdict-only", "287 orphans",
                                 "515 protocol-points-nowhere"],
               "counts": {k: len(v) for k, v in sets.items()},
               "overlaps": {"%s|%s" % (a, b): len(sets[a] & sets[b])
                            for i, a in enumerate(keys) for b in keys[i + 1:]},
               "members": {k: sorted(v)[:400] for k, v in sets.items()}},
              io.open(OUT, "w", encoding="utf-8"), indent=1)
    say("")
    say("wrote %s" % os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    sys.exit(main())
