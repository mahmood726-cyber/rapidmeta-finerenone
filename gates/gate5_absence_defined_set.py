"""GATE 5 -- no irreversible action on an absence-defined set without a positive restatement.

Runs the REAL retirement selector from `scripts/retire_2026_08_28.py` -- imported, not
re-implemented, so the gate exercises the shipped function rather than a copy of it that could
drift into agreeing with itself -- and puts a positive restatement beside it.

    absence-defined  ("no interval matched this regex")     756
    positive         ("the page SAYS it carries no result")   2
    unexplained gap                                          754

754 pages sit in an irreversible-action set on the strength of a detector's silence. This gate
does NOT claim those 754 have results. It claims nobody established that they do not, which is
a different and larger problem, and it is the one that was one command from being served.

THE NAMED POSITIVE IS A PAGE THE SELECTOR GETS WRONG, and it was found by widening the
selector's own regex by one character. `PREDICTION_MODEL_KFRE_REVIEW.html` states
`0.88 (95% CI 0.86-0.90)` with an en-dash; the shipped regex accepts `to`, `,` and `-` and not
an en-dash, so the page reads as having no interval anywhere in its text. If a future edit
makes the gate stop seeing this page, the gate exits VACUOUS rather than PASS.
"""
from __future__ import annotations

import collections
import glob
import importlib.util
import io
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _harness as H                                                        # noqa: E402
import absence as A                                                         # noqa: E402

# The positive restatement. A page positively IS resultless when it SAYS so.
SAYS_NO_RESULT = re.compile(
    r"no pooled (estimate|result)|nothing is pooled|not pooled|no combined (figure|estimate)|"
    r"no meta-analys|no synthesis was|declines to pool|refuses to pool|"
    r"no quantitative synthesis|not been pooled", re.I)

# The selector's own regex, widened by exactly the characters it omits. Used only to DEMONSTRATE
# that the shipped one is incomplete -- never as a replacement criterion, because a wider
# negative selector is still a negative selector.
WIDER_INTERVAL = re.compile(
    r"\d+\.\d+\s*[\(\[]\s*(?:95\s*%?\s*(?:CI|CrI)\s*[:,]?\s*)?"
    r"-?\d+\.\d+\s*(?:to|,|-|–|—|−|and)\s*-?\d+\.\d+\s*[\)\]]", re.I)

NAMED = "PREDICTION_MODEL_KFRE_REVIEW.html"


def load_real_selector(repo, gate):
    """Import the SHIPPED module. A gate that re-implements what it checks is a tautology."""
    path = os.path.join(repo, "scripts", "retire_2026_08_28.py")
    if not os.path.exists(path):
        gate.broken("scripts/retire_2026_08_28.py is absent; the gate cannot exercise the "
                    "real selector and will not substitute a copy of it.")
        return None
    spec = importlib.util.spec_from_file_location("_retire_shipped", path)
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except Exception as exc:
        gate.broken("importing the shipped retirement module failed: %s" % exc)
        return None
    for needed in ("INTERVAL", "rendered"):
        if not hasattr(mod, needed):
            gate.broken("the shipped module has no %r; its shape changed and this gate is "
                        "checking something else." % needed)
            return None
    return mod


# The known-negative control: text that MUST NOT read as "this page says it has no result".
KNOWN_NEGATIVES = [
    "the pooled hazard ratio is 0.85 (95% CI 0.72 to 0.99)",
    "trials were pooled using a random-effects model",
    "a pooled estimate is displayed above",
    "we pooled the two trials and report the interval",
    "the risk of bias assessment is not pooled across domains",   # 'not pooled' about RoB
    "GRADE certainty was rated down for imprecision",
]


def main(argv):
    repo = H.repo_root()
    gate = H.Gate("5  ABSENCE-DEFINED SET",
                  "an irreversible action needs a positive restatement and a two-count "
                  "comparison as a precondition")
    gate.requires_control()
    case = gate.expect_case(NAMED,
                            "a page stating 0.88 (95%% CI 0.86-0.90) with an en-dash, which "
                            "the shipped selector reads as having no interval at all")

    shipped = load_real_selector(repo, gate)
    if shipped is None:
        gate.kinds({"could not load the shipped selector": 1})
        return gate.report()

    page_map = set(H.load(os.path.join(repo, "ssot", "PAGE_MAP.json")))
    pages = sorted(os.path.basename(p) for p in glob.glob(os.path.join(repo, "*_REVIEW.html")))

    kinds = collections.Counter()
    rendered_cache = {}
    candidates = []
    for p in pages:
        if p in page_map:
            kinds["in PAGE_MAP (has a store) -- outside the removal set"] += 1
            continue
        with io.open(os.path.join(repo, p), encoding="utf-8", errors="replace") as fh:
            t = shipped.rendered(fh.read())
        rendered_cache[p] = t
        if not re.search(r"PRISMA|GRADE|AMSTAR|risk of bias", t, re.I):
            kinds["no review apparatus -- outside the removal set"] += 1
            continue
        if shipped.INTERVAL.search(t):
            kinds["shipped selector sees an interval -- kept"] += 1
            continue
        candidates.append(p)
    kinds["ABSENCE-DEFINED removal set"] = len(candidates)

    # the two-count comparison, through the sanction API
    def negative(p):
        return True                      # membership already decided by the shipped selector

    def positive(p):
        return bool(SAYS_NO_RESULT.search(rendered_cache[p]))

    # control first: the positive restatement is a text matcher and needs its precision measured
    fp = [s for s in KNOWN_NEGATIVES if SAYS_NO_RESULT.search(s)]
    gate.control(len(KNOWN_NEGATIVES), len(fp), fp)

    if "--sanction" in argv:
        explain = ("a human named the 754 and accepted them" if "--explain" in argv else None)
    else:
        explain = None

    # SCOPE. As a STANDING gate this reports the two counts every run and refuses nothing:
    # the selector selects 756 pages whether or not anybody intends to remove them, and a gate
    # that refuses a hypothetical action fails on every push and gets bypassed within a day.
    # It REFUSES under --action, which is what an actual removal passes. The counts print
    # either way, which is the part that was missing when 763 pages were one command from
    # being served.
    action = "--action" in argv
    try:
        tok, neg_set, pos_set = A.sanction(
            "retire %d pages" % len(candidates), candidates, negative, positive,
            explain=explain)
        gate.note("SANCTIONED: " + tok.line())
    except A.Unsanctioned as exc:
        pos_set = [p for p in candidates if positive(p)]
        if action:
            gate.finding("UNSANCTIONED-IRREVERSIBLE-ACTION", str(exc),
                         numerator=len(candidates), denominator=len(pages))
        else:
            gate.note("WOULD REFUSE under --action: " + str(exc))

    kinds["POSITIVE restatement (the page SAYS it has no result)"] = len(pos_set)
    kinds["unexplained gap between the two"] = len(candidates) - len(pos_set)

    # the selector's own blind spot, demonstrated on real pages
    only_wider = [p for p in candidates if WIDER_INTERVAL.search(rendered_cache[p])]
    kinds["in the removal set BUT an interval is present under a one-character widening"] = \
        len(only_wider)
    new_wider = set(H.ratchet(gate, "GATE5_KNOWN_SELECTOR_MISSES.json", only_wider,
                              "pages inside an absence-defined removal set that DO carry an "
                              "interval under a one-character widening of the selector."))
    frozen_exists = os.path.exists(os.path.join(repo, "gates",
                                                "GATE5_KNOWN_SELECTOR_MISSES.json"))
    for p in only_wider:
        if p == NAMED:
            gate.saw(case)
        if frozen_exists and p not in new_wider:
            continue
        m = WIDER_INTERVAL.search(rendered_cache[p])
        gate.finding("SELECTOR-MISSES-A-RESULT-IT-CLAIMS-IS-ABSENT",
                     "%s is in the removal set as having no interval anywhere in its text, "
                     "and its text contains %r. The shipped regex accepts `to`, `,` and `-` "
                     "between the bounds and not an en-dash."
                     % (p, m.group(0)[:60]),
                     numerator=len(only_wider), denominator=len(candidates))

    if NAMED not in candidates and NAMED in pages:
        gate.note("%s is no longer in the absence-defined set -- either the selector or the "
                  "page changed. That is worth reading, not assuming." % NAMED)

    gate.kinds(dict(kinds))
    gate.note("the measured 16.7%% false-positive rate on the POSITIVE restatement makes the "
              "754 a LOWER bound, not an upper one: a false positive inflates the positive "
              "count and therefore SHRINKS the gap. The direction of the error is stated "
              "because a rate without a direction is not a measurement.")
    gate.note("the rule this enforces was already written, four days earlier, in "
              "scripts/prune_legacy_corpus_2026_08_26.py: \"Keep what you can name; never "
              "delete what you merely failed to recognise.\" A sibling script did the "
              "opposite two days later. That is the argument for a gate over a rule.")

    art = os.path.join(repo, "out", "gate5_absence_defined_set.json")
    os.makedirs(os.path.dirname(art), exist_ok=True)
    with open(art, "w", encoding="utf-8") as fh:
        json.dump({"gate": gate.as_json(), "absence_defined": candidates,
                   "positive_restatement": pos_set, "missed_by_selector": only_wider},
                  fh, indent=1)

    return gate.report(denominator="%d *_REVIEW.html pages scanned" % len(pages))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
