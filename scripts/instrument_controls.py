"""The shared assertions. An instrument routes through these instead of remembering to.

WHY THIS FILE AND NOT ANOTHER REGISTRY ENTRY. The heredoc class was breached NINE TIMES by
an author who had just read the rule, and the tenth attempt was stopped by a hook that does
not care whether anyone understands it. Fifty-five documented classes is more than anyone
holds. What refuses is what controls.

TWO ASSERTIONS, BOTH DRAWN FROM DEFECTS THAT ACTUALLY RECURRED TONIGHT.

`require_controls` -- THE ACCUSING DIRECTION.
    Four wrong accusations in one night: 0.06 and 1.79 read out of a WITHDRAWAL NOTICE and
    relayed to a reader; `pool_broken` reported against a pool that was withdrawn on
    purpose; two unbacked-claim findings against the flagship that were not unbacked; a
    count of 49 never-taken branches from an extraction that captured code spans. Every one
    was caught by a person reading the instance. NONE was caught by the instrument.

    So the reading becomes part of the instrument. An instrument that reports a corpus-wide
    finding declares a POSITIVE control -- a real corpus item whose answer is already
    established -- and, where the failure mode is over-flagging, a NEGATIVE control it must
    NOT flag. If either disagrees, NOTHING IS PRINTED. A detector that can only say yes is
    not a detector, and the malaria false positive is why the negative side is not optional.

`zero_has_a_reading` -- CLASS 52.
    A check reporting zero has two readings and only one is reassuring: "looked, found
    none" and "the marker does not exist so nothing could ever match". Three instances in
    one night, TWO OF THEM INSIDE `regression_check.py`, one of those in its BLOCKING set,
    reporting 0 on every run this project has ever made -- where the zero meant the marker
    was absent from the corpus entirely and was read as "no page has this defect".

    A zero is only reportable if the thing being searched FOR is known to exist somewhere.
    When it is not, the answer is NOT_ASSESSABLE, which is a different word on purpose.

NEITHER FUNCTION PRINTS A REASSURANCE IT CANNOT SUPPORT. Both raise SystemExit, because a
warning an operator can ignore is the control that has already failed.
"""
import sys


class ControlFailed(SystemExit):
    pass


def require_controls(instrument, positive, negative=None, out=None):
    """Refuse to proceed unless the known answers come back known.

    positive -- (label, actual, expected). A real corpus item whose answer is established
                independently of this instrument. Established means read from a
                registration, a delivered page, or a prior recorded finding -- NOT inferred
                by the same logic under test, which would only prove the code agrees with
                itself.
    negative -- (label, actual, must_not_be). The case the instrument must NOT flag. Supply
                it whenever the instrument can over-flag, which is nearly always.

    Returns None on success. Raises ControlFailed otherwise, before any count is printed.
    """
    say = out or (lambda s: sys.stdout.write(s + "\n"))
    plab, pact, pexp = positive
    say("CONTROL (positive) %s: %s -> %r, expected %r" % (instrument, plab, pact, pexp))
    if pact != pexp:
        raise ControlFailed(
            "REFUSED: %s does not reproduce the one answer that is already established "
            "(%s gave %r, not %r). It is not trusted for anything else and NO COUNT IS "
            "PRINTED." % (instrument, plab, pact, pexp))
    if negative is None:
        say("CONTROL (negative) %s: NONE DECLARED -- this instrument can only say yes."
            % instrument)
        return
    nlab, nact, nforbid = negative
    say("CONTROL (negative) %s: %s -> %r, must not be %r" % (instrument, nlab, nact, nforbid))
    if nact == nforbid:
        raise ControlFailed(
            "REFUSED: %s FLAGS THE CASE IT MUST NOT (%s came back %r). Accusing in the "
            "wrong direction is the failure this control exists to catch. NO COUNT IS "
            "PRINTED." % (instrument, nlab, nact))
    say("    both controls held.")


def zero_has_a_reading(count, marker_exists_somewhere, what, where):
    """Return a reportable string for a count, or NOT_ASSESSABLE when a zero is ambiguous.

    marker_exists_somewhere -- True only if the thing searched FOR has been observed at
    least once, anywhere, in this run. Not "the vocabulary is non-empty"; the vocabulary
    being non-empty is what `arni_hf_protocol` had.
    """
    if count > 0:
        return "%d %s in %s" % (count, what, where)
    if marker_exists_somewhere:
        return "0 %s in %s -- LOOKED AND FOUND NONE (the marker occurs elsewhere, so the " \
               "search is live)" % (what, where)
    return "NOT_ASSESSABLE: 0 %s in %s, AND THE MARKER OCCURS NOWHERE AT ALL. This zero " \
           "means the search cannot match, not that the defect is absent." % (what, where)


def refuse_unless_marker_lives(marker, corpus_hits, fixture_hit, instrument):
    """A marker-keyed check must be able to fire. Raise if it provably cannot.

    `arni_hf_protocol` was in `regression_check.py`'s BLOCKING set and appears on 0 of 888
    pages. It has reported clean on every run this project has ever made and could not have
    reported anything else.
    """
    if corpus_hits or fixture_hit:
        return
    raise ControlFailed(
        "REFUSED: %s keys on %r, which occurs on NO page in the corpus and in NO fixture. "
        "The check cannot fire. A clean result from it is not evidence." % (instrument, marker))
