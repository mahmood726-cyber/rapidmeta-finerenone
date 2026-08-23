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


def scan_covers_what_it_emits(function_name, own_literals_matched, callee_renders, what):
    """A LITERAL CAN LIVE ONE CALL AWAY, AND A SCAN OF A FUNCTION'S OWN BODY IS NOT A SCAN OF
    WHAT IT EMITS. Same family as `composed_or_stored`, one level up.

    THE INCIDENT, 2026-08-23. An audit was written to find procedural sentences asserted from
    literals rather than projected from fields. It filtered to "functions that emit markup" by
    looking for HTML tags among each function's OWN string constants -- and missed
    `protocol_card`, THE FUNCTION IT WAS WRITTEN FOR. That function holds only the sentences;
    it returns `kv_card(...)`, and the tags live in the callee.

    The hand-classified control caught it, which is the only reason it was caught: a scan that
    cannot see the known instance cannot be trusted to report an absence.

    THE FAMILY THIS BELONGS TO, now six deep in one day: the fix, the probe, or the scan lands
    where the author was looking rather than where the text is produced.

        composed at render time, or stored          -- the value was baked into the object
        one render point of two                     -- seven panels used a different callable
        two surfaces of three de-indexed            -- audit_table.html was never touched
        a probe keyed to what the fix removed       -- braces, not field names
        a selector keyed to the defect              -- shrank as the work succeeded
        a scan of a body, not of what it emits      -- THIS ONE

    THE CHECK: when classifying functions by what they render, ask whether rendering happens
    HERE or in something this calls. If a function's content is handed to a builder, the scan
    must follow the call or key on the handoff, not on tags.
    """
    if own_literals_matched or callee_renders:
        return
    raise ControlFailed(
        "REFUSED: %s classified `%s` as non-emitting on the strength of its own literals, but "
        "it hands its content to a renderer. A scan of a function's body is not a scan of what "
        "it emits." % (what, function_name))


def control_is_keyed_to_something_stable(control_reads, work_changes, what):
    """A CONTROL MUST BE KEYED TO SOMETHING THE WORK DOES NOT CHANGE -- a fixture, a frozen
    copy, or a property of the instrument -- NEVER to the corpus state the work is altering.

    THE STRONGEST OF THESE LESSONS, because it is the one that makes SUCCESS INDISTINGUISHABLE
    FROM FAILURE. Every other class here produces a wrong answer; this one produces a refusal
    that arrives precisely when the work has gone right, and the natural response to a control
    failing is to assume the work broke.

    FIVE INSTANCES IN ONE DAY, all the same shape:

      1 `lint_field_name_in_reader_prose` -- positive control was MAVACAMTEN's `bar:` at
        origin/main. That IS the defect the lint exists to remove: a successful rollout would
        have made the control fail and the lint refuse every run thereafter. Pinned to
        a2091846a.
      2 the grammar-seam gate -- patterns proven against live corpus text that the repair was
        about to clean. Moved to planted fixtures.
      3 the procedural-constants scan -- required `protocol_card` to be FOUND carrying
        procedural constants. Fixing the seven rows made its own control fail.
      4 the Table 1 classifier -- required `Study selection process` to classify CONSTANT.
        Same fix, same death.
      5 the field-name lint again, at the ratchet: a zero-target would have blocked every
        commit until the rollout landed. Made a ratchet on the baseline instead.

    THE TEST, AND IT TAKES ONE QUESTION: if this work succeeds completely, does the control
    still hold? If the answer is no, the control is keyed to the thing being removed. Key it to
    a fixture that will never be cleaned, a pinned revision that will never be rewritten, or a
    property of the instrument itself -- "the pattern fires on its own planted defect" is true
    forever regardless of what the corpus does.
    """
    shared = set(control_reads) & set(work_changes)
    if not shared:
        return
    raise ControlFailed(
        "REFUSED: %s keys its control on %s, which is exactly what this work changes. If the "
        "work succeeds the control fails, and a control that dies on success makes success "
        "indistinguishable from failure. Key it to a fixture, a pinned revision, or a property "
        "of the instrument." % (what, ", ".join(sorted(shared))))


def match_on_the_meaning_bearing_part(matcher, known_differing_pair, what):
    """WHEN MATCHING NAMES, MATCH ON THE PART THAT CARRIES THE MEANING -- and prove it against
    a pair you already know differs.

    THE INCIDENT, 2026-08-23. A sweep for "one concept stored under two key names" tested
    lexical closeness by SHARED PREFIX. `dual_screening` and `duplicate_screening` share
    exactly two leading characters, "du". The concept is in the SUFFIX: a synonym pair is
    usually two different qualifiers on the same noun, and the noun comes last.

    The sweep therefore missed the one pair that had already been established by hand, and the
    control refused before any count was printed. Without that control it would have reported
    a clean-looking list that omitted its own founding case.

    SAME FAMILY AS `selection_is_population_not_defect`: a rule keyed to the convenient end of
    the data rather than to the part that decides the answer. A prefix is where string
    comparison starts, which is why it gets used; it is not where the meaning lives.

    THE CHECK: any name-matching rule must be run against a pair whose answer is already known
    -- ideally one that is SIMILAR in the dimension being tested and DIFFERENT in the one that
    matters -- before it is allowed to report.
    """
    a, b = known_differing_pair
    if matcher(a, b):
        return
    raise ControlFailed(
        "REFUSED: %s does not match %r and %r, which are known to name one concept. The rule "
        "is keyed to a part of the name that does not carry the meaning." % (what, a, b))


def selection_is_population_not_defect(selected, population, defect_matched, what):
    """A SELECTOR KEYED TO THE DEFECT IS A SELECTOR THAT SHRINKS AS THE WORK SUCCEEDS, AND ITS
    SUCCESS SIGNAL IS COMPUTED OVER THE SURVIVORS.

    THE INCIDENT, 2026-08-23. A repair pass selected objects by the defect -- stored prose
    containing `what verifies this object:` and its siblings -- and rewrote 48 of them. A second
    pass was then needed to correct a punctuation seam the first pass had introduced. It used
    the SAME selector. By then the defect was gone from 46 of the 49, so the selector matched
    only the 3 objects still carrying a refused key.

    IT REPORTED SUCCESS. Every object it selected did change, so the occurrence predicate
    passed, the counts closed, and 46 objects kept the seam. The success signal was computed
    over the survivors of the very filter that was wrong.

    THIS IS NOT ONLY ABOUT REPAIR SCRIPTS. Any run that finds its work by looking for the
    problem has this shape: a linter fixing what it can still detect, a migration selecting
    un-migrated rows, a retry queue holding only failures. The moment the operation partially
    succeeds, the population and the selector diverge, and the run cannot see what it already
    touched.

    THE REMEDY: define the POPULATION independently of the defect -- "objects that hold this
    writer's output", not "objects that hold its broken output" -- and read that definition
    from THE SAME SOURCE the fix reads, so the two cannot drift. Then let the occurrence
    predicate decide per item whether anything changed.
    """
    missed = len(population) - len(selected)
    if missed <= 0:
        return
    raise ControlFailed(
        "REFUSED: %s selected %d item(s) but the population is %d. %d were skipped, and %d of "
        "the selected matched the defect -- which means the selector is keyed to the defect "
        "and has shrunk as the work succeeded. Its success signal would be computed over the "
        "survivors." % (what, len(selected), len(population), missed, defect_matched))


def occurrence_predicate(first_application, changed, unchanged, defects_remaining, what):
    """THE OCCURRENCE PREDICATE, AWARE OF WHICH RUN IT IS. Mahmood's correction, 2026-08-23.

    The rule as originally imposed -- "assert per item that the operation actually changed
    something, so 'ran and changed nothing' is distinguishable from 'never ran'" -- is TRUE OF A
    FIRST PASS AND FALSE OF A REPEAT. On a verification re-run the correct outcome is that
    nothing changes, and a predicate that demands change refuses a corpus that is already
    right. That happened: the re-run reported 48 objects "expected to change and did not" while
    every one of them was correct, and the only way through was to verify against the defect
    directly.

    SO THE DISCRIMINATOR DEPENDS ON THE RUN:

        FIRST APPLICATION   assert CHANGED. An item that did not change was not reached, and
                            "not reached" is indistinguishable from "nothing to do" without it.
        VERIFICATION PASS   assert UNCHANGED **and** DEFECT-FREE. Unchanged alone proves
                            nothing -- a run that never executed is also unchanged. The
                            discriminator is the DEFECT COUNT, not the change count.

    Both runs are still separating the same two states. Only the evidence differs.
    """
    if first_application:
        if unchanged:
            raise ControlFailed(
                "REFUSED: %s is a FIRST APPLICATION and %d item(s) did not change. That is "
                "'ran and changed nothing', which is indistinguishable from 'never ran'."
                % (what, unchanged))
        return
    if defects_remaining:
        raise ControlFailed(
            "REFUSED: %s is a VERIFICATION PASS and %d defect(s) remain. Unchanged is only "
            "reassuring when the defect count is zero -- a run that never executed is also "
            "unchanged." % (what, defects_remaining))
    if changed:
        raise ControlFailed(
            "REFUSED: %s is a VERIFICATION PASS and %d item(s) CHANGED. Either the previous "
            "application was incomplete or this run is not idempotent; both need saying before "
            "the result is trusted." % (what, changed))


def composed_or_stored(rendered_string, render_time_sources, stored_sources, what):
    """BEFORE FIXING A RENDERED STRING, ESTABLISH WHETHER IT IS COMPOSED AT RENDER TIME OR
    STORED. A projector fix cannot reach a baked value, and both look identical on the page.

    THE INCIDENT, AND IT IS THE FOURTH OF ITS FAMILY IN ONE NIGHT. The container-repr leak was
    fixed in `paper_projector._flatten_container`, the fix was unit-tested and correct, and
    MAVACAMTEN was rebuilt to prove it. The page came back with the SAME THREE HITS:

        "... what verifies this object: ClinicalTrials.gov protocol records, read 2026-08-18.
         what is not claimed: that any per-trial count was checked against a results record.
         bar: not recorded on the page this object was built from."

    The projector renders a STORED STRING. The `key: value` text is written into the object at
    `bookkeeping_2026_08_21.the_search_its_date_and_its_databases` by a DIFFERENT function --
    `scripts/build_paper_bookkeeping_2026_08_21.py::_flat` -- and had been sitting in the JSON
    since 2026-08-21. I FIXED THE RENDERER AND THE DEFECT WAS IN THE WRITER.

    THE FAMILY, ALL FOUR FOUND ON 2026-08-22/23, AND THE COMMON SHAPE IS THAT THE FIX LANDS
    WHERE THE AUTHOR WAS LOOKING RATHER THAN WHERE THE TEXT IS PRODUCED:

        * a probe searched for BRACES, which is what the fix removed, so it could only agree
          with whoever wrote the fix
        * the transform was placed on the PAPER panel's loop while seven other panels rendered
          through a different callable
        * a de-indexing updated `index.html` and `sitemap.xml` and not `audit_table.html`
        * a renderer was fixed while the string was baked into the object by a writer

    THE CHECK: for a rendered string you intend to change, enumerate BOTH the paths that
    compose it at render time and the fields that may already hold it, and say which one you
    are fixing. A rebuild that changes nothing is the signature of getting this wrong -- and it
    is silent, because a page that was never going to change looks exactly like a page that had
    nothing to fix.
    """
    if render_time_sources or stored_sources:
        return
    raise ControlFailed(
        "REFUSED: %r is to be changed but neither a render-time path nor a stored field has "
        "been identified for it (%s). A fix aimed at the wrong one produces a rebuild that "
        "changes nothing, silently." % (rendered_string[:60], what))


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

    THE AUTHOR OF THIS LESSON BROKE IT AGAIN WITHIN THE HOUR, in a disposable one-line waiter,
    where nobody would have looked: `ps -W | grep rollout_corpus` never matches because that
    shell's `ps` does not print command lines, so the negation was true on the first pass and
    the waiter announced "ROLLOUT FINISHED" while the rollout was still building pages. It
    would have reported a rebuild complete at 90 of 157. WRITING A RULE DOWN DOES NOT
    IMMUNISE YOU AGAINST IT -- which is the strongest available evidence that this class is
    structural and not carelessness.

    IT WAS CAUGHT BY A DIFFERENT RULE, NOT BY THIS ONE: a lock file is an artefact, a running
    process is a fact -- so the process list was checked and the process was alive. THE RULES
    COVER EACH OTHER AND NO SINGLE ONE IS SUFFICIENT. Do not expect to be saved by the rule
    that names the mistake you are making; expect to be saved by a different one.
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
