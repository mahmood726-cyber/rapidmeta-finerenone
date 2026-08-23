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

def same_bytes(a_bytes, b_bytes):
    """Compare DELIVERED bytes to LOCAL bytes. Both arguments must already be `bytes`.

    READ BYTES, COMPARE BYTES -- CLASS: THE INSTRUMENT NORMALISED WHAT IT WAS MEASURING.
    ---------------------------------------------------------------------------------
    A page was reported to Mahmood as a deploy gap, and the report had to be withdrawn. The
    evidence was that local content differed from `origin/main` by 752 bytes on a file git
    reported unmodified. The mechanism was the reader, not the repo:

        io.open(name, encoding="utf-8").read()   -> TEXT mode, converts CRLF to LF
        git show origin/main:name                -> raw bytes, CRLF preserved

    752 was the line count. The two were identical. Worse, the same artefact was used to
    argue the local tree was a MIXTURE OF BUILDS -- which is a frightening claim, because one
    passing spot-check would then license trusting a corpus that could not be trusted -- and
    it was false. Read in binary, local equalled origin on 156 of 157 pages.

    THE CORPUS *WAS* A MIXTURE, JUST NOT IN THE WAY THE BROKEN READ SUGGESTED: 133 pages
    carried generator `a3c7bb8b2` and 7 carried the current one. A real finding was nearly
    buried under a fake one produced by the instrument.

    So: open in "rb", or `git show` into bytes, and compare bytes. If a comparison must be
    newline-insensitive, normalise BOTH sides explicitly and say so -- never let one side be
    normalised by the mode the file happened to be opened in.
    """
    if not isinstance(a_bytes, bytes) or not isinstance(b_bytes, bytes):
        raise ControlFailed(
            "REFUSED: same_bytes was handed %s and %s, not bytes. A str argument means the "
            "caller already read in text mode, which is the defect this function exists to "
            "prevent -- the newline conversion has happened before the comparison."
            % (type(a_bytes).__name__, type(b_bytes).__name__))
    return a_bytes == b_bytes


def plant_and_require(instrument, detector, clean_case, planted_case):
    """THE HOUSE REQUIREMENT FOR GATES: plant the defect, require the gate to find it.

    Three gates earned their result this way -- the bypass mutant that strips the render-point
    transform, the dead link planted in a synthetic hub, the known-bad input handed to the
    pass/fail audit. Each of the three was written after a gate had already shipped that could
    only say yes. A pre-push hook once printed "Regression check PASS" at 0 of 1522 fully-ok,
    because nothing in it could return non-zero.

    A GATE THAT HAS NEVER BEEN SEEN TO FAIL IS NOT A GATE. It is a log line. `detector` is
    called on both cases; it must be quiet on `clean_case` and must fire on `planted_case`,
    and this refuses before the gate is allowed to report anything about real data.
    """
    if detector(planted_case) and not detector(clean_case):
        return
    raise ControlFailed(
        "REFUSED: %s did not survive its planted control -- it %s on the planted defect and "
        "%s on the clean case. A gate that cannot be seen to fail cannot be trusted when it "
        "passes." % (instrument,
                     "fired" if detector(planted_case) else "STAYED QUIET",
                     "fired" if detector(clean_case) else "stayed quiet"))


def every_referring_surface(target, surfaces_checked, surfaces_that_reference, what):
    """A CHANGE IS APPLIED TO THE SURFACES ITS AUTHOR WAS THINKING ABOUT, AND NOT TO THE ONE
    THEY WERE NOT. Enumerate the referring surfaces and ASSERT them; never remember them.

    THREE INSTANCES OF ONE CLASS, ALL FOUND ON 2026-08-23:

      1. A DELETION VALIDATED ON TWO SURFACES OUT OF THREE. Commit 2a011cdfe removed 519
         single-trial AUTO apps on a correct and documented principle -- k=1 is not a
         meta-analysis -- and its own message records updating `index.html` cards (47) and
         `sitemap.xml` entries (520). It did not touch `audit_table.html`. Eleven weeks later
         the index has ZERO dead links and the audit table has 569: two rows in five of the
         surface a sceptical reader opens first point at nothing.

      2. THE POOLING CLAIM fixed in Methods-synthesis and left standing in the Abstract.

      3. GRADE LIVING IN TWO PLACES -- `results.*.grade` and `grade.by_outcome` -- with each
         rendered surface reading a different one, so a reader met whichever location the
         panel they were looking at happened to consult.

    THE COMMON SHAPE: the author had a mental list of surfaces, acted on all of it, and the
    list was incomplete. Nothing failed. Every check passed. The work was CORRECT and the
    coverage was not, which is why review does not catch this class -- there is no error to
    see, only an absence, and the absence is somewhere nobody was looking.

    THE GENERAL FORM, AND IT IS A CHECK RATHER THAN A HABIT: when a record is removed or
    changed, ENUMERATE every surface that references it -- by searching for references, not by
    recalling them -- and assert that each was handled. A remembered list is the failure mode
    itself.
    """
    missed = sorted(set(surfaces_that_reference) - set(surfaces_checked))
    if not missed:
        return
    raise ControlFailed(
        "REFUSED: %s was changed on %d surface(s) but %d surface(s) still reference it and "
        "were not handled: %s. This is the class where the work is correct and the coverage "
        "is not -- %s." % (target, len(surfaces_checked), len(missed), ", ".join(missed), what))


NOT_ASSESSABLE = "NOT_ASSESSABLE"


def abstain_or_answer(can_decide, verdict, what):
    """A CHECK THAT REQUIRES JUDGEMENT SHOULD BE BUILT TO ABSTAIN, NOT TO GUESS.

    THE ASYMMETRY THAT UNDERLIES EVERY WITHDRAWAL OF 2026-08-23, and it is the general rule:

        THE ABSENCE LIMB NEEDS NO JUDGEMENT. "Does NCT01084557 exist" is answered by the
        registry's own 404, re-queried live. There is nothing to interpret, so the number is
        publishable: 57 pages cite identifiers that do not exist.

        THE DONOR LIMB NEEDS A CONCEPT MATCH. "Is this the RIGHT trial for this page" requires
        knowing that ALS is Amyotrophic Lateral Sclerosis, that NSCLC is Non-Small Cell Lung
        Cancer, that MCI-186 is edaravone and VEGF Trap-Eye is aflibercept. That needs a real
        ontology or a person. It was implemented as SUBSTRING OVERLAP and produced 727 of 745,
        then 149 of 602. Both withdrawn.

    THE PATTERN, NAMED SO IT IS RECOGNISABLE NEXT TIME: A HEURISTIC KEYED TO SOMETHING
    CONVENIENT RATHER THAN TO THE THING BEING ASKED. Substring overlap against registry text
    was never a test of "is this the right trial". It was a test of "do these strings happen to
    share characters", which is a different question that happens to be easy to compute. The
    convenience is what makes it seductive and the mismatch is invisible in the output, because
    a wrong verdict looks exactly like a right one.

    So when a check cannot decide, it returns NOT_ASSESSABLE and SAYS SO. That is not a
    failure to deliver -- an abstention is information, and a guess dressed as a measurement
    costs more than silence. Roughly a third of this run's value was in refusing to answer.
    """
    if can_decide:
        return verdict
    return NOT_ASSESSABLE


def page_states_its_own_condition(page_says, instrument_says, what, page):
    """WHEN A PAGE STATES ITS OWN CONDITION AND THE INSTRUMENT DISAGREES, THE PAGE IS THE
    EVIDENCE AND THE INSTRUMENT IS THE HYPOTHESIS.

    THE INCIDENT, AND IT REFUTED A CORRECT PIECE OF REASONING. Legacy pages carry a banner
    reading, in plain English:

        "47 number(s) on this page marked UNVERIFIED -- no resolvable trial id"

    An extraction was run to test whether such pages ALSO name identifiers a reader could look
    up. It found NCTs on 128 of 129 of them and reported that the bare-count distinction was
    "weaker than claimed". The reasoning it refuted was correct. The NCTs it found were real
    but belonged to other, verified content -- ZERO were among the numbers flagged unverified,
    which is precisely what the banner had already said. Corrected overlap: 1 of 129.

    THE CORPUS WAS TELLING THE INSTRUMENT THE ANSWER AND THE INSTRUMENT OVERRODE IT.

    This is not the same as trusting page text blindly. A page's SELF-DESCRIPTION of its own
    state -- "no resolvable trial id", "no pooled estimate was produced", "this review has been
    retired" -- is a first-class observation, usually written by the code that knows. When a
    probe contradicts one, the probability that the probe is asking a subtly different question
    is far higher than the probability that the page is lying about itself. Check the probe
    first. Every time this has come up tonight, the probe was wrong.

    Call with the page's own claim and the instrument's, and it refuses when they diverge, so
    the disagreement has to be resolved before a number is published rather than after.
    """
    if bool(page_says) == bool(instrument_says):
        return
    raise ControlFailed(
        "REFUSED: %s says %r about %s and this instrument says %r. The page's statement about "
        "its own condition is the evidence; this check is the hypothesis. Establish which "
        "question the probe is actually asking before reporting a number."
        % (page, page_says, what, instrument_says))


def authored_not_constructed(path, text):
    """A CHANNEL NOTHING VALIDATES IS WHERE SILENT CORRUPTION SURVIVES.

    THE INCIDENT. A commit message was passed to `git commit -m "..."` with backticks in the
    body. The shell COMMAND-SUBSTITUTED them: `` `_REVIEW` `` was executed, produced nothing,
    and the sentence "whose filenames omit `_REVIEW`" was recorded as "whose filenames omit".
    The commit succeeded. Every gate passed. The push would have gone out clean.

    WHY THIS ONE IS WORTH A FUNCTION AND NOT JUST A NOTE. It is the same shape as a gate that
    cannot fail, arriving from the opposite direction. A commit message is a channel NOTHING
    DOWNSTREAM READS: no test parses it, no linter checks it, no reader diffs it against what
    was meant. So a corruption there is not caught late -- IT IS NEVER CAUGHT. The record is
    silently wrong forever, and the only reason this instance was found is that a person
    happened to read the log within the minute.

    The transport does not have to be malicious or exotic to do this. Backticks command-
    substitute, `$` expands, `\\b` becomes a literal 0x08 byte, CRLF is rewritten. Every one is
    a documented failure in this repo's history and every one produced output that looked fine.

    THE RULE, GENERALISED: never construct content through a shell string. Write the bytes to a
    file with a file tool and hand the FILE to the command -- `git commit -F <file>`. A file is
    a channel you can read back and diff; a shell argument is not.

    This helper is the assertion form: hand it the path you wrote and the text you meant, and
    it refuses if what landed is not what was intended.
    """
    import io as _io
    try:
        got = _io.open(path, encoding="utf-8").read()
    except OSError as e:
        raise ControlFailed("REFUSED: cannot read back %s (%s). Content that cannot be read "
                            "back has not been verified, only sent." % (path, e))
    if got.strip() == text.strip():
        return
    raise ControlFailed(
        "REFUSED: what landed in %s is not what was authored (%d chars written, %d read "
        "back). Something in the transport rewrote it, and a commit message is a channel "
        "nothing downstream validates -- so this would have been wrong permanently and "
        "silently." % (path, len(text), len(got)))
