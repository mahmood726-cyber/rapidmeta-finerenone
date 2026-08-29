"""An irreversible action on an absence-defined set needs a positive restatement first.

THE CLASS. "Every page that does NOT have X" is a set defined by what a detector failed to
recognise. It contains, indistinguishably, the things that genuinely lack X and the things
whose X the detector could not see. Deleting it is safe only if you have separately named what
the members positively ARE.

THE INSTANCE, ON THIS REPOSITORY, 2026-08-28. A 763-page retirement selected pages by
"no interval matches this regex". Measured here, the same criterion selects 756 pages today; a
positive restatement -- pages that SAY they carry no pooled result -- selects 2. Every gate in
the chain passed, because each tested the removal against the selector and none tested the
selector.

AND THE RULE WAS ALREADY WRITTEN DOWN. `scripts/prune_legacy_corpus_2026_08_26.py` says, in
its own docstring, four days earlier:

    "Keep what you can name; never delete what you merely failed to recognise."

It was owned, correct, and in the same directory. A sibling script did the opposite two days
later. That is the whole argument for a gate over a rule.

WHAT THE SELECTOR MISSED, CONCRETELY. The shipped regex accepts `to`, `,` and `-` between the
bounds of an interval and not an en-dash. `PREDICTION_MODEL_KFRE_REVIEW.html` states
`0.88 (95% CI 0.86-0.90)` with an en-dash. It is invisible to the selector, and it was in the
removal set, described as a page with "no interval anywhere in its text".

HOW TO USE IT.

    tok = sanction("retire 756 pages",
                   population=all_pages,
                   negative=lambda p: not has_interval(p),      # what we cannot see
                   positive=lambda p: says_it_has_no_result(p), # what it positively IS
                   explain=...)
    remove(pages, tok)     # remove() refuses without the token

`sanction` never decides. It computes both counts, prints them, and refuses to issue a token
while the gap is unexplained. Naming the gap is the human step; skipping it is what this
prevents.
"""
from __future__ import annotations


class Unsanctioned(Exception):
    """An irreversible action was attempted on a set nobody restated positively."""


class Sanction:
    def __init__(self, action, n_negative, n_positive, gap, explanation):
        self.action = action
        self.n_negative = n_negative
        self.n_positive = n_positive
        self.gap = gap
        self.explanation = explanation

    def line(self):
        return ("%s: absence-defined selector chooses %d; positive restatement chooses %d; "
                "%d unexplained. %s" % (self.action, self.n_negative, self.n_positive,
                                        self.gap, self.explanation or "NO EXPLANATION GIVEN"))


def sanction(action, population, negative, positive, explain=None, allow_gap=0):
    """Refuses unless BOTH selectors are supplied and the gap is explained.

    `allow_gap` is the number of members the positive restatement is permitted not to reach,
    and it must be stated deliberately. A default of zero is the point: the caller has to
    write down how many members it cannot positively name, which is the number that was never
    written down before.
    """
    if positive is None:
        raise Unsanctioned(
            "%s selects a set by ABSENCE and supplied no positive restatement. A set defined "
            "by what a detector failed to recognise cannot be acted on irreversibly until "
            "somebody says what its members positively are." % action)
    pop = list(population)
    neg_set = [x for x in pop if negative(x)]
    pos_set = [x for x in pop if positive(x)]
    gap = len(neg_set) - len(set(map(id, pos_set)) & set(map(id, neg_set)))
    s = Sanction(action, len(neg_set), len(pos_set), gap, explain)
    if gap > allow_gap and not explain:
        raise Unsanctioned(s.line() + "  Refusing: the difference between the two counts is "
                                      "the set you would be deleting on a failure to "
                                      "recognise, and it is unexplained.")
    return s, neg_set, pos_set


def require_sanction(token, action):
    if not isinstance(token, Sanction):
        raise Unsanctioned("%s attempted with no sanction. Two counts and a positive "
                           "restatement are a precondition, not a report." % action)
    return True
