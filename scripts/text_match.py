"""ONE normaliser for every text comparison in this repository.

FOUR INSTANCES OF ONE SHAPE THIS WEEK, all inside checks written to catch exactly that
shape in other people's work:

  1. CASE. A batch harness grepped `not on the page` against a gate message reading
     `IS NOT ON THE PAGE`. Five rebuilt pages were reported as content failures.
  2. HTML ENTITIES. The verdict gate matched an object's prose against a served page where
     the apostrophe was `&#x27;`. Five more pages reported as failures with the text
     present.
  3. SUBSTRING BOUNDARIES. A subject check matched a drug name inside a longer token --
     broken INSIDE the tool built to enforce that very rule.
  4. UNNORMALISED EXACT MATCH ON FREE TEXT. The metric gate compared paramType
     `Relative Risk Reduction` against `Relative Risk Reduction (RRR)` and found no
     intersection. A sound pool flagged as a live defect.

THE FIX FOR THE FIRST THREE WAS BUILT AND NOT APPLIED TO THE FOURTH. The rule existed, was
understood, was implemented, and was bypassed by its own author within hours. That is the
class-3 pattern exactly: every mechanical guard built this week has held, every prose rule
has failed.

SO: route every text comparison through here. The fifth instance becomes impossible rather
than caught.

WHAT norm() DOES, and each step is one of the four defects:
  - html.unescape, twice, because a page can carry `&amp;#x27;`      (defect 2)
  - strip HTML tags                                                  (defect 2)
  - casefold, not lower -- correct for non-ASCII                     (defect 1)
  - collapse all whitespace runs to a single space                   (defect 1)
  - drop bracketed abbreviations and trailing punctuation            (defect 4)

WHAT IT DELIBERATELY DOES NOT DO. It does not stem, synonym-map, or fuzzy-match. Those
would make DIFFERENT things compare equal, which is the opposite failure and the more
expensive one: `equivalent()` must never say two incommensurable quantities are the same.
Use contains() for "is this text present", equivalent() for "are these the same label".
"""
from __future__ import annotations
import html
import re

_TAG = re.compile(r"<[^>]+>")
_WS = re.compile(r"\s+")
_PAREN_ABBREV = re.compile(r"\s*\([A-Za-z0-9/\-\. ]{1,12}\)")
_TRAIL = re.compile(r"[\s.;:,]+$")


def norm(s) -> str:
    """Normalise text for comparison. Never for display, never stored."""
    if s is None:
        return ""
    s = str(s)
    s = html.unescape(html.unescape(s))     # twice: a page can carry &amp;#x27;
    s = _TAG.sub("", s)
    s = _WS.sub(" ", s)
    s = s.casefold().strip()
    return _TRAIL.sub("", s)


def label(s) -> str:
    """norm() plus dropping a trailing bracketed abbreviation.

    'Relative Risk Reduction (RRR)' and 'Relative Risk Reduction' are ONE label. This is
    the ONLY place that equivalence is granted, and it is granted for abbreviations only --
    never for synonyms, because 'incidence rate' and 'percentage of participants' must
    stay different.
    """
    return _TRAIL.sub("", _PAREN_ABBREV.sub("", norm(s))).strip()


def contains(haystack, needle) -> bool:
    """Is `needle` present in `haystack`? Both normalised first."""
    return norm(needle) in norm(haystack)


def equivalent(a, b) -> bool:
    """Are these the same label? Abbreviation-insensitive, synonym-blind."""
    return label(a) == label(b)


def selftest() -> int:
    cases = [
        (contains("<b>IS NOT ON THE PAGE</b>", "is not on the page"), True, "case+tags"),
        (contains("the trials&#x27; own words", "the trials' own words"), True, "entity"),
        (contains("carried &amp;#x27;out", "carried 'out"), True, "double entity"),
        (equivalent("Relative Risk Reduction", "Relative Risk Reduction (RRR)"), True,
         "bracketed abbreviation"),
        (equivalent("Hazard Ratio (HR)", "hazard  ratio"), True, "whitespace + abbrev"),
        (equivalent("incidence rate", "percentage of participants"), False,
         "MUST STAY DIFFERENT -- rate is not a proportion"),
        (equivalent("Risk Ratio", "Rate Ratio"), False,
         "MUST STAY DIFFERENT -- one letter, two quantities"),
        (contains("dabigatran etexilate", "gatran"), True,
         "substring: contains() is deliberately permissive -- use equivalent() for identity"),
        (equivalent("dabigatran", "dabigatran etexilate"), False,
         "identity is not substring"),
    ]
    bad = 0
    for got, want, why in cases:
        ok = got is want
        bad += 0 if ok else 1
        print("   %-4s %s" % ("ok" if ok else "FAIL", why))
    print()
    print("selftest: %d/%d" % (len(cases) - bad, len(cases)))
    return 1 if bad else 0


if __name__ == "__main__":
    import sys
    sys.exit(selftest())
