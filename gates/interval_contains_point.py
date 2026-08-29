"""UNIT 1 -- an effect estimate must lie inside its own confidence interval.

WHY THIS ONE FIRST. It is the rare check that is both GENERAL and near-exact. It needs no
schema, no registry and no model, so it runs on our pages and on somebody else's published
review alike; and its only legitimate-exception mode is a parse error, not a disagreement of
opinion. That makes it the right unit to point at external content, where a false accusation
costs far more than it does at home.

WHAT IT REFUSES. `RR 1.20 (95% CI 0.60 to 1.10)` -- the point sits outside the interval it is
printed with. One of the two numbers is wrong and the text cannot tell you which. There is no
reading of a confidence interval on which this is acceptable.

THE PARSING IS WHERE THIS GOES WRONG, SO IT IS CONSERVATIVE ON PURPOSE:

  * separators: `to`, `-`, en-dash, em-dash, comma, semicolon -- gate 5 read a page as having
    NO interval because its shipped regex accepted three of those and not the en-dash;
  * negatives are kept (a mean difference of -2.5 with a CI of -4.0 to -1.0 is ordinary);
  * a hyphen between two numbers is ONLY a range separator when neither side is signed, since
    `-4.0 - -1.0` is unparseable and `0.60-1.10` is not;
  * `I2`, `tau2`, `p`, percentages and counts are excluded: they are not effect estimates with
    an interval and treating them as such is how a general detector becomes a noise generator;
  * bounds are compared with a tolerance, because a printed interval is rounded and a point
    equal to a bound to the last printed digit is not a contradiction.

REACH, STATED: it reads rendered text. An estimate held only in a table cell that this text
extraction flattens away is not examined, and is not counted as clean.
"""
from __future__ import annotations

import re
from re import error

# A measure name, a point, then an interval. The measure list is explicit rather than a
# pattern: an open-ended one swept in "Figure 2 (95% CI ...)" and similar.
MEASURES = (r"RR|OR|HR|IRR|RD|MD|SMD|WMD|aOR|aHR|risk ratio|odds ratio|hazard ratio|"
            r"rate ratio|risk difference|mean difference|standardised mean difference|"
            r"standardized mean difference")

NUM = r"[-−]?\d+(?:[.,]\d+)?"

# point, then an interval opened by a CI marker. The CI marker is REQUIRED -- without it,
# "0.79 (0.71 to 0.88)" also matches ordinary prose like a date range in parentheses.
PAT = re.compile(
    r"(?P<measure>" + MEASURES + r")\s*"
    r"(?:of|was|=|:|\s)\s*"
    r"(?P<point>" + NUM + r")\s*"
    r"[\(\[]\s*"
    r"(?:9[05](?:\.\d)?\s*%\s*(?:CI|confidence interval)|CI|confidence interval)\s*[:=]?\s*"
    r"(?P<lo>" + NUM + r")\s*(?P<sep>to|–|—|--|,|;|-)\s*(?P<hi>" + NUM + r")\s*"
    r"[\)\]]",
    re.I)

TOL = 1e-9


def _f(s):
    s = s.replace("−", "-").strip()
    # a comma is a thousands separator only with 3 trailing digits; otherwise a decimal comma
    if "," in s and re.search(r",\d{3}$", s):
        s = s.replace(",", "")
    else:
        s = s.replace(",", ".")
    return float(s)


def _scan(pat, text, source):
    out = []
    for m in pat.finditer(text):
        sep = m.group("sep")
        lo_raw, hi_raw = m.group("lo"), m.group("hi")
        # a bare hyphen cannot separate signed numbers: "-4.0 - -1.0" is not a range we parse
        if sep == "-" and (lo_raw.startswith(("-", "−")) or hi_raw.startswith(("-", "−"))):
            continue
        try:
            point, lo, hi = _f(m.group("point")), _f(lo_raw), _f(hi_raw)
        except ValueError:
            continue
        if lo > hi:
            lo, hi = hi, lo                       # printed high-to-low is a style, not a defect
        # tolerance keyed to the PRINTED precision: an interval rounded to 2dp cannot exclude
        # a point by less than half of the last place.
        dp = max(len((lo_raw.split(".") + [""])[1]), len((hi_raw.split(".") + [""])[1]))
        tol = 0.5 * (10 ** -dp) if dp else 0.5
        if point < lo - tol - TOL or point > hi + tol + TOL:
            s = max(0, m.start() - 60)
            try:
                meas = m.group("measure")
            except (IndexError, error):
                meas = "(unnamed)"
            out.append({
                "source": source,
                "measure": meas,
                "point": point, "lo": lo, "hi": hi,
                "quote": re.sub(r"\s+", " ", text[s:m.end() + 40]).strip(),
            })
    return out


# ---------------------------------------------------------------------------
# LEG 3 -- the known-negative control. Anchored to FIXTURES, never to the corpus's
# current belief: a control keyed to live content retires itself the moment the content
# changes, and then passes for the wrong reason.
# ---------------------------------------------------------------------------
KNOWN_NEGATIVES = [
    "The pooled risk ratio was RR 0.79 (95% CI 0.71 to 0.88).",
    "MD -2.50 (95% CI -4.00 to -1.00) points on the scale.",
    "HR 1.00 (95% CI 1.00 to 1.00) -- a point equal to both bounds.",
    "OR 0.50 (95% CI 0.50 to 0.90) -- a point equal to the lower bound.",
    "OR 0.90 (95% CI 0.50 to 0.90) -- a point equal to the upper bound.",
    "RR 0.79 (95% CI 0.71–0.88) with an en-dash separator.",
    "SMD 0,35 (95% CI 0,10 to 0,60) written with decimal commas.",
    "RR 1.05 (95% CI 0.99 to 1.12) crossing no difference.",
    "The risk ratio of 2.00 (95% CI 1.20 to 3.30) favoured control.",
    "HR 0.67 (95% CI 0.45 to 0.99); I2 = 45%; tau2 = 0.02.",
    "Rounding: RR 0.70 (95% CI 0.70 to 0.90) where the point equals the bound to 2dp.",
    "RR 1.20 (95% CI 1.20 to 1.60) at the boundary exactly.",
    "MD 0.00 (95% CI -1.00 to 1.00) spanning zero.",
    "Between 2010 and 2015 the OR fell (95% CI not reported).",
    "aHR 0.88 (95% CI 0.79 to 0.98) adjusted for baseline risk.",
]

KNOWN_POSITIVES = [
    "RR 1.20 (95% CI 0.60 to 1.10) -- the point is above the interval.",
    "OR 0.30 (95% CI 0.55 to 0.90) -- the point is below the interval.",
    "MD -5.00 (95% CI -2.00 to 1.00) -- a negative point outside a negative-to-positive CI.",
    "hazard ratio 2.50 (95% CI 1.10 to 1.90) -- above.",
]


def control():
    """(n_negatives, n_false_positives, examples) and (n_positives, n_missed)."""
    fp = [t for t in KNOWN_NEGATIVES if findings(t, "control")]
    missed = [t for t in KNOWN_POSITIVES if not findings(t, "control")]
    return (len(KNOWN_NEGATIVES), len(fp), fp), (len(KNOWN_POSITIVES), len(missed), missed)


def findings(text, source="?"):
    """Every estimate whose printed interval does not contain its printed point."""
    return _scan(PAT, text, source)


# ---------------------------------------------------------------------------
# WIDE PATTERN. The strict pattern requires a measure NAME beside the point, and on real
# published text that is the minority case: 158 of 531 CI-marked intervals across 15 Cochrane
# reviews, with 14 of the 15 contributing none. A detector that examines 30% of its own
# population and reports a count is reporting REACH as though it were coverage.
#
# So: a bare point immediately followed by its CI, with no measure name required. The
# arithmetic is unchanged -- only the anchoring is looser -- and the FP rate is re-measured on
# an ENLARGED negative set that includes the prose shapes this looseness can swallow.
PAT_WIDE = re.compile(
    r"(?<![\w.])(?P<point>" + NUM + r")\s*"
    r"[\(\[]\s*"
    r"(?:9[05](?:\.\d)?\s*%\s*(?:CI|confidence interval)|CI|confidence interval)\s*[:=]?\s*"
    r"(?P<lo>" + NUM + r")\s*(?P<sep>to|–|—|--|,|;|-)\s*(?P<hi>" + NUM + r")\s*"
    r"[\)\]]",
    re.I)

WIDE_NEGATIVES = KNOWN_NEGATIVES + [
    "In 2019 (95% CI 0.71 to 0.88) was first reported.",
    "Participants numbered 1,204 (95% CI 0.71 to 0.88) in the pooled set.",
    "Version 6.5 (95% CI 1.10 to 1.90) of the Handbook.",
    "The 12 (95% CI 8 to 15) week follow-up window.",
    "Absolute risk 5% (95% CI 3 to 8) per year.",
    "Scale 0-100 (95% CI 40 to 60) points.",
]


def findings_wide(text, source="?"):
    return _scan(PAT_WIDE, text, source)
