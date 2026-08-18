"""The three-state verdict, in ONE place, because implementing it per-site failed three times.

WHY THIS EXISTS. In a single night this project scored an absent thing as a negative
finding in THREE different layers:

  1. A classification scheme with no name for the healthy case routed three working
     tabs into NOT-MEASURABLE.
  2. A build-queue script assigned a state from a tab NAME without reading the object,
     so 111 cells migrated between tabs and a grand-total check certified it.
  3. A precondition assessor scored `arms: []` as FAIL -- "no data" reported as
     "the data is wrong" -- and scored a correctly-roled trial as FAIL because the
     drug name was not in the arm's display LABEL.

Each was fixed at its own site. That is why it happened three times. This module is the
fix that is not a fourth reminder: every assessor and every sweep routes through
`judge()`, so the distinction is made once and cannot be re-derived incorrectly.

THE RULE, and it is the whole module:

    absent field          -> NOT_ASSESSABLE
    empty collection      -> NOT_ASSESSABLE
    unreadable input      -> NOT_ASSESSABLE
    declared absence      -> FAIL for an existence predicate, and the reason says the
                             object DECLARED it, which is different from being silent
    present + readable + predicate false -> FAIL
    present + readable + predicate true  -> PASS

An instrument that cannot read a case must not record a negative result for that case.
NOT_ASSESSABLE is a distinct state from zero and from FAIL, and it is never a pass.

THE SECOND RULE. An assessor NAMES THE FIELD IT READS AND READS ONLY THAT FIELD.
`read()` requires the path, and `judge()` prints it in every reason. An assessor that
wants to look at a display label must say so, and then it is obvious in the output that
the verdict rests on a label rather than on the semantic field beside it.
"""

PASS = "PASS"
FAIL = "FAIL"
NOT_ASSESSABLE = "NOT-ASSESSABLE"

_MISSING = object()

# Values that are PRESENT and READABLE but assert their own absence. These are not
# silence -- an object that says "not recorded" has told you something, and an
# existence predicate over it is a real FAIL rather than an unreadable case.
DECLARED_ABSENT_PREFIXES = (
    "not recorded",
    "not stated",
    "not reported",
    "not available",
    "none recorded",
    "unknown",
)


class Reading:
    """What an assessor actually observed at one named path. Nothing is inferred here."""

    __slots__ = ("path", "value", "state", "detail")

    def __init__(self, path, value, state, detail):
        self.path = path
        self.value = value
        self.state = state          # "present" | "absent" | "empty" | "declared_absent" | "unreadable"
        self.detail = detail

    @property
    def readable(self):
        return self.state == "present"

    def __repr__(self):
        return f"Reading({self.path!r}, {self.state}, {self.detail!r})"


def read(obj, path, treat_declared_absent=True):
    """Read ONE dotted path. The path is recorded so every verdict names its own source.

    Returns a Reading. Does not judge -- judging is `judge()`'s job, so that the
    three-state rule lives in exactly one function.
    """
    cur = obj
    walked = []
    for part in path.split("."):
        walked.append(part)
        if isinstance(cur, dict):
            if part not in cur:
                return Reading(path, None, "absent",
                               f"no key {'.'.join(walked)}")
            cur = cur[part]
        else:
            return Reading(path, None, "unreadable",
                           f"{'.'.join(walked[:-1])} is {type(cur).__name__}, not a mapping")

    if cur is None:
        return Reading(path, None, "absent", f"{path} is null")
    if isinstance(cur, str):
        s = cur.strip()
        if not s:
            return Reading(path, cur, "empty", f"{path} is an empty string")
        if treat_declared_absent and s.lower().startswith(DECLARED_ABSENT_PREFIXES):
            return Reading(path, cur, "declared_absent",
                           f"{path} states its own absence: {s[:60]!r}")
        return Reading(path, cur, "present", f"{path} carries {len(s)} characters")
    if isinstance(cur, (list, tuple, set, dict)):
        if len(cur) == 0:
            return Reading(path, cur, "empty", f"{path} is an empty {type(cur).__name__}")
        return Reading(path, cur, "present", f"{path} carries {len(cur)} entries")
    return Reading(path, cur, "present", f"{path} = {cur!r}")


def judge(reading, predicate=None, pass_reason=None, fail_reason=None,
          declared_absence_is_failure=True, on_predicate_error="raise"):
    """Turn a Reading into (state, reason). THE ONLY place the three-state rule is applied.

    `predicate` is called ONLY when the reading is present and readable. It must not be
    asked to interpret absence -- that is exactly the confusion this module removes.
    """
    if reading.state in ("absent", "empty", "unreadable"):
        return NOT_ASSESSABLE, f"cannot assess: {reading.detail}"

    if reading.state == "declared_absent":
        if declared_absence_is_failure:
            return FAIL, f"declared absent: {reading.detail}"
        return NOT_ASSESSABLE, f"cannot assess: {reading.detail}"

    if predicate is None:
        return PASS, pass_reason or f"present: {reading.detail}"

    # A RAISING PREDICATE IS A BUG IN THE ASSESSOR, NOT AN UNREADABLE CASE.
    #
    # This function previously caught every exception and returned NOT_ASSESSABLE. A
    # cross-family review (Gemini 3.1 Pro, 2026-08-18) pointed out what that hides: a typo
    # like `a.roole.lower()` raises AttributeError, and `age > 18` against the string
    # "adult" raises TypeError -- and BOTH were silently converted into "cannot assess".
    #
    # That is this module's own defect, in the module written to stop exactly it: a broken
    # instrument reporting "no reading" instead of "I am broken". An assessor bug must be
    # LOUD. Unreadable DATA is already handled above, by inspecting the Reading -- it never
    # needed an exception handler to detect it.
    #
    # Callers sweeping many objects, where one malformed payload should not kill the run,
    # may pass on_predicate_error="not_assessable" -- but they must then REPORT the raised
    # type, so a systematic assessor bug cannot masquerade as a corpus full of gaps.
    try:
        ok = predicate(reading.value)
    except Exception as exc:
        if on_predicate_error == "raise":
            raise
        return NOT_ASSESSABLE, (f"ASSESSOR BUG (not a data gap): predicate over "
                                f"{reading.path} raised {type(exc).__name__}: {exc}")

    if ok:
        return PASS, pass_reason or f"holds at {reading.path}"
    return FAIL, fail_reason or f"contradicted at {reading.path}"


def assess(obj, path, predicate=None, **kw):
    """read() + judge() in one call, for the common case."""
    return judge(read(obj, path), predicate=predicate, **kw)


# ---------------------------------------------------------------------------
# THE RANDOMISED COMPARISON, not the arm count.
# ---------------------------------------------------------------------------
#
# WHY THIS IS HERE AND NOT IN EACH ASSESSOR. The first arm-role test asked "does this
# trial have exactly one treatment arm and exactly one control arm". That is a test of
# TRIAL SHAPE, and it fails correctly-designed trials:
#
#   AUGUSTUS (NCT02415400) is an open-label 2x2 FACTORIAL -- apixaban vs vitamin K
#   antagonist AND aspirin vs aspirin-placebo. Four cells, two randomised comparisons,
#   one of which is exactly the comparison an apixaban review asks about. An arm-count
#   test rejects it. It should not be rejected.
#
#   APPRAISE (NCT00313300) is a multi-arm dose-ranging trial -- several apixaban doses
#   against one placebo. Same rejection, same error.
#
# The Handbook does not treat these as ineligible. Its guidance on variants of the
# randomised trial covers studies with more than two intervention groups and factorial
# designs, and the standard handling is to take ONE randomised comparison at a time --
# the one the review asks about -- and to record what the other factor or the unused
# arms were. So the correct predicate is not about arm count at all:
#
#   "is there EXACTLY ONE randomised comparison of the topic intervention against a
#    non-topic control that this review is asking about"
#
# CITATION IS NOT YET VERIFIED AND MUST BE BEFORE THIS SHIPS. The project's own rule is
# that a Handbook section is cited only after being read in the current version, so the
# section number is deliberately absent rather than guessed. `HANDBOOK_AUTHORITY` below
# mirrors the objects' own `handbook_authority` shape and carries `verified_on: None`.
# Any caller that publishes a verdict resting on this MUST fail closed while that is None.

HANDBOOK_AUTHORITY = {
    "handbook": "Cochrane Handbook for Systematic Reviews of Interventions",
    "version": None,          # fill from the edition actually read
    "sections": None,         # variants on randomised trials: >2 intervention groups; factorial
    "verified_on": None,      # MUST be set from a real read before this authority is cited
    "claim": ("A factorial or multi-arm trial is included for ONE randomised comparison at a "
              "time -- the comparison the review asks about -- with the other factor or the "
              "unused arms recorded rather than the trial excluded."),
}


def handbook_authority_is_verified():
    """Fail closed. An unverified citation is not authority, and must not be printed as one."""
    return all(HANDBOOK_AUTHORITY[k] is not None
               for k in ("version", "sections", "verified_on"))


def randomised_comparisons(trial, is_topic_arm, arms_path="arms"):
    """Every randomised comparison in `trial` that pits a topic arm against a non-topic arm.

    Reads the SEMANTIC role/label pair the caller identifies -- it never guesses from
    display text on its own; `is_topic_arm` is supplied by the caller and is the single
    place topic identity is decided.

    Returns (Reading, comparisons). `comparisons` is a list of (topic_arm, control_arm)
    and is meaningful only when the Reading is readable.
    """
    r = read(trial, arms_path)
    if not r.readable:
        return r, []
    topic = [a for a in r.value if is_topic_arm(a)]
    other = [a for a in r.value if not is_topic_arm(a)]
    return r, [(t, c) for t in topic for c in other]


def judge_one_comparison(trial, is_topic_arm, label_of, arms_path="arms"):
    """PASS when the trial offers exactly one topic-vs-non-topic randomised comparison.

    A factorial or dose-ranging trial yields MORE than one; that is not a failure of the
    trial, it is a decision the review owes its reader -- so the state is FAIL with the
    candidate comparisons named, and the caller records which one the review asks about.
    No arms at all remains NOT_ASSESSABLE, via judge()'s single rule.
    """
    r, comps = randomised_comparisons(trial, is_topic_arm, arms_path)
    if not r.readable:
        return judge(r)
    if len(comps) == 1:
        return PASS, f"{r.path}: one topic-vs-control randomised comparison"
    if not comps:
        return FAIL, f"{r.path}: no randomised comparison of the topic against a non-topic arm"
    named = "; ".join(f"{label_of(t)} vs {label_of(c)}" for t, c in comps[:4])
    return FAIL, (f"{r.path}: {len(comps)} candidate randomised comparisons, review must name "
                  f"which one it asks about ({named})")


# ---------------------------------------------------------------------------
# TWO PRECONDITIONS, TWO NAMES. They were one word, and the word hid the difference.
# ---------------------------------------------------------------------------
#
# A cross-family review (Gemini 3.1 Pro, 2026-08-18) argued that a `screening.eligibility`
# reading "not recorded on the page this object was built from" must be NOT_ASSESSABLE,
# because it describes the DOCUMENT'S EXTRACTION STATE and not the trial's clinical
# reality. That is correct -- for the question it was answering. We had committed to FAIL,
# which is also correct -- for the question WE were answering. Both verdicts were right
# and they disagreed, which is the signature of one name carrying two questions.
#
#   INCLUSION_CRITERIA_AUDITABLE -- "can this OBJECT state the criteria by which its
#       included set was chosen, so a reader can audit that set?"
#       A declared "not recorded" is a definite, readable NO. FAIL is correct.
#       An object with no `screening` key at all is silent. NOT_ASSESSABLE is correct.
#
#   ELIGIBILITY_MET -- "did THIS TRIAL meet the stated criteria?"
#       Unanswerable while the criteria are unstated, and unanswerable from JSON alone
#       even when they are, because inclusion logic is conditional clinical prose
#       ("exclude if X unless Y within 30 days") that a flattened record drops.
#       NOT_ASSESSABLE until a full-text read, and it is never inferred from the other.
#
# THE TWO ARE NOT ORDERED AND NEITHER IMPLIES THE OTHER. Passing auditability says
# nothing about whether any trial met the criteria; passing eligibility for one trial says
# nothing about whether the set can be audited. Run them independently and report both.

INCLUSION_CRITERIA_AUDITABLE = "inclusion_criteria_auditable"
ELIGIBILITY_MET = "eligibility_met"


def inclusion_criteria_auditable(canon, path="screening.eligibility"):
    """Can the OBJECT state the criteria its included set was chosen by? Declared no = FAIL."""
    return judge(read(canon, path), declared_absence_is_failure=True)


def eligibility_met(canon, full_text_read=False, path="screening.eligibility"):
    """Did each trial MEET the criteria? Not answerable from JSON, and never inferred."""
    r = read(canon, path)
    if not r.readable:
        return NOT_ASSESSABLE, (f"cannot assess: criteria are not stated ({r.detail}), so "
                                f"whether any trial met them cannot be decided")
    if not full_text_read:
        return NOT_ASSESSABLE, (f"cannot assess: {r.path} is stated, but inclusion logic is "
                                f"conditional prose and no full text was read this pass")
    raise NotImplementedError(
        "eligibility_met over full texts is not implemented; it must not silently degrade "
        "to an auditability check -- that conflation is what the rename removed")


def read_scalar(element, key):
    """Read a required scalar off ONE collection element, three-state aware.

    agy's D1 case: `{"role": ""}`. A blank string is NOT the value "no role" -- it is an
    unreadable field, and counting it as a non-match turned missing data into a FAIL. Any
    caller iterating arms/trials/rows must route each field through this rather than
    reaching in with .get() and a default, because .get(k, "") is precisely how an absent
    field becomes an empty string becomes a negative finding.
    """
    return read(element, key, treat_declared_absent=False)


def tally(verdicts):
    """Count states without collapsing any of them. Every sweep reports all three."""
    out = {PASS: 0, FAIL: 0, NOT_ASSESSABLE: 0}
    for state, _reason in verdicts:
        out[state] = out.get(state, 0) + 1
    return out
