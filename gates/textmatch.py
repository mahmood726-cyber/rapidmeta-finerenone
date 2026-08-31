"""Text matching that cannot report a count without reporting its precision.

THE FAILURE THIS CLOSES. A matcher reported 62 confirmations and roughly one in five of them
was PAGE SIZE rather than content: a long page accumulates incidental occurrences of any short
token, so "the page confirms X" degenerates into "the page is big". Adding a contiguity
requirement -- the token must occur near the structure that would make it a confirmation, not
merely somewhere on the page -- cut the false positives by about four fifths.

WHY A LIBRARY AND NOT A RULE. "Always measure precision" has been written down here for weeks.
It fires only when the author already suspects the count is fragile, which is the case where it
was never needed. So this module makes it STRUCTURAL: `ControlledCount.value` RAISES until a
known-negative control has been run against the same matcher. You cannot obtain the number
without measuring how often the matcher is wrong.

WHAT A KNOWN-NEGATIVE CONTROL IS. A set of cases that MUST NOT match, established from
something other than the matcher itself. Not "cases I believe are clean" -- cases whose answer
is fixed outside this code. Anything drawn from the matcher's own output is a tautology.

MEASURED ON THIS CORPUS, 2026-08-28, on the task "does this delivered page confirm that trial
<ACRONYM> contributes to this topic", ground truth taken from the SSOT store:

    naive (token anywhere on page)        false positives  6/378 = 1.6%
    contiguous (token within 300 chars of a registration)  1/378 = 0.3%

and the naive false positives sit on pages with a median of 70,455 characters against a corpus
median of 46,185 -- the confounder is visible in the measurement, which is the point.
"""
from __future__ import annotations

import re

NCT_RE = re.compile(r"NCT\d{8}")
_TAG = re.compile(r"<script.*?</script>|<style.*?</style>", re.S | re.I)


class PrecisionNotMeasured(Exception):
    """Raised when a count is read before its false-positive rate is known."""


def page_text(html):
    """Rendered text. <script> is NOT page content -- two headline findings came from
    counting it, so it is stripped before anything else happens."""
    s = _TAG.sub(" ", html)
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", s)


def occurrences(haystack, needle):
    """Word-boundary occurrences. Not `in`: `in` matches ASPIRE inside ASPIRENZA."""
    if not needle:
        return []
    return list(re.finditer(r"(?<![A-Za-z0-9])" + re.escape(needle) + r"(?![A-Za-z0-9])",
                            haystack, re.I))


def matches_naive(haystack, needle):
    return bool(occurrences(haystack, needle))


def matches_contiguous(haystack, needle, anchor=NCT_RE, window=300):
    """The token must occur NEAR the structure that would make it a confirmation.

    `window` is characters either side. A page that merely mentions a name in discussion has
    no registration beside it; a contributing row does.
    """
    for m in occurrences(haystack, needle):
        lo = max(0, m.start() - window)
        hi = min(len(haystack), m.end() + window)
        if anchor.search(haystack[lo:hi]):
            return True
    return False


class ControlledCount:
    """A count you cannot read until you have measured how often the matcher is wrong.

    Usage:
        c = ControlledCount("pages confirming X", denominator=141)
        for case in population:  c.observe(match_fn(case), case)
        c.run_control(known_negatives, match_fn)     # mandatory
        print(c.line())                              # count AND fp rate, one line
    """

    def __init__(self, what, denominator=None):
        self.what = what
        self.denominator = denominator
        self._hits = []
        self._seen = 0
        self._control = None

    def observe(self, hit, case=None):
        self._seen += 1
        if hit:
            self._hits.append(case)
        return hit

    def run_control(self, known_negatives, match_fn):
        """`known_negatives` must MUST-NOT-MATCH by an answer fixed outside this matcher."""
        neg = list(known_negatives)
        if not neg:
            raise ValueError("a control with no negatives measures nothing")
        fp = [c for c in neg if match_fn(c)]
        self._control = (len(neg), len(fp), fp[:5])
        return self._control

    @property
    def controlled(self):
        return self._control is not None

    @property
    def value(self):
        if self._control is None:
            raise PrecisionNotMeasured(
                "%r was read before its false-positive rate was measured. Supply a "
                "known-negative control via run_control(). A count without a measured "
                "precision is not a finding." % self.what)
        return len(self._hits)

    @property
    def fp_rate(self):
        if self._control is None:
            return None
        n, fp, _ = self._control
        return fp / n

    def hits(self):
        _ = self.value          # same gate: no reading the members without the precision
        return list(self._hits)

    def line(self):
        n, fp, ex = self._control if self._control else (0, 0, [])
        den = self.denominator if self.denominator is not None else self._seen
        return ("%s: %d/%s  (known-negative control %d/%d matched, measured "
                "false-positive rate %.1f%%)" % (self.what, self.value, den, fp, n,
                                                 100.0 * fp / n))
