"""A short structured statement for a topic that holds no poolable evidence.

WHY THIS EXISTS INSTEAD OF A MANUSCRIPT. Eight blind reviewers across two model families,
each shown only the rendered prose and told they were peer-reviewing for a clinical
journal, all called these pages a debug dump, a renderer log, or exposed database plumbing.
Collapsing the refusals into one table moved Gemini from "abysmal" to "badly" and no
further. Both families then prescribed the same thing independently:

    "Strip out all references to the software's internal data structures and missing
     variables, and state only the actual clinical methods and findings -- EVEN IF THAT
     REDUCES THE ENTIRE PAPER TO THREE SENTENCES."

A topic with nothing poolable has no results, no synthesis, no certainty rating and no
discussion, because there is nothing to have them about. Rendering a manuscript skeleton
and then declining every section of it produced a document that was 25 to 33 declines
wrapped around three sentences. The declines were honest; the SHAPE was the lie -- it
promised a paper and delivered an inventory of what a paper would have had.

FIVE THINGS A READER NEEDS, AND NOTHING ELSE:

    the question           what was actually asked
    what was checked       which registrations, which registry, on what date
    what was found         the trials, by registration id
    why nothing was pooled SPECIFICALLY -- "the two trials register different outcomes"
                           and not "insufficient data"
    what would change it   so a reader knows whether it is worth coming back

NO SECTION EXISTS SOLELY TO DECLINE. That is the rule separating this from the refusal
collapse: there, a section with only absences still printed its heading and moved its
refusals to a table. Here it does not render at all. An absence is stated once, in the
sentence where it belongs, or not at all.

NOTHING ABOUT THE SOFTWARE REACHES THE READER. No "this object", no "this page", no field
name, no `[Draft]`, no renderer explaining its own design. `_reader_safe` strips the ones
this corpus writes, and anything it cannot make safe is DROPPED rather than shown --
because a sentence about the generator is worse than a missing sentence.

AND IT STILL SAYS WHAT IS ABSENT. This is not a way to publish nothing quietly. It is the
opposite: the absence is the finding, and it is stated plainly in a paragraph a reader
will actually read instead of buried in thirty declines they will not.
"""
import re

# Phrases this corpus writes that are ABOUT THE SOFTWARE. A sentence carrying one of these
# is not shown to a reader; where the sentence is load-bearing the caller composes its own.
_SOFTWARE_TALK = re.compile(
    r"this object|this page|this renderer|composition path|projected from|"
    r"canonical object|build_stamp|\bfield\b|\[Draft\]|the record this page|"
    r"emitted only from|no field supports|machine-checked|the page standard",
    re.I)

# Absence markers that are values in the data rather than sentences to a reader.
_MARKER = re.compile(
    r"^\s*(not recorded|not available|not stated|no record|not established|"
    r"not captured|not applicable|not executed|none)\b", re.I)


def _reader_safe(text):
    """The sentences of `text` that a clinical reader can be shown, or None."""
    if not text:
        return None
    s = re.sub(r"\s+", " ", str(text)).strip()
    if _MARKER.match(s):
        return None
    kept = [p.strip() for p in re.split(r"(?<=[.?!])\s+", s)
            if p.strip() and not _SOFTWARE_TALK.search(p)]
    out = " ".join(kept).strip()
    return out or None


# Acronyms a clinical reader expects in capitals. Everything else that shouts is the
# corpus emphasising, not abbreviating, and comes down to ordinary case.
_KEEP_CAPS = {
    "NCT", "ROB", "GRADE", "PRISMA", "PROSPERO", "WHO", "HR", "OR", "RR", "MD", "SMD",
    "IRR", "RD", "CI", "SE", "HIV", "TB", "AF", "VTE", "HF", "CKD", "COVID", "AOM",
    "CDI", "MRSA", "PAH", "CTEPH", "LDL", "SGLT2", "PCSK9", "ARNI", "ATTR", "MDR",
    "ITT", "SD", "IQR", "NMA", "DTA", "TSA", "USA", "UK", "EU", "FDA", "EMA",
}


def _sentence_case(s):
    """Undo the corpus's shouting without touching real acronyms.

    A FIRST VERSION TITLE-CASED, and produced "ALL 2 of 2 Seeded Registrations Register NO
    Clinical Endpoint AT ANY RANK": it lowered long shouted words and left short ones alone,
    so the line shouted in a NEW pattern rather than stopping. A shouted run is emphasis,
    and emphasis becomes ordinary case; only a declared acronym stays up.
    """
    if not s:
        return s

    def fix(m):
        w = m.group(0)
        return w if w.upper().strip("-") in _KEEP_CAPS else w.lower()

    out = re.sub(r"\b[A-Z][A-Z0-9]+(?:-[A-Z0-9]+)?\b", fix, str(s))
    return re.sub(r"(^|(?<=[.?!]) )([a-z])",
                  lambda m: m.group(1) + m.group(2).upper(), out)


def _first_reason(text):
    """The reason itself, without the citation apparatus trailing it.

    The stored reasons open with the finding and then carry provenance a reader does not
    need in a four-sentence summary: "Registrations read: NCT00034645, NCT00044486.
    Authority: Cochrane Handbook 6.5 (2024) section 8.7, RoB 2 domain 5..." The
    registrations are already in the table directly above, and a Handbook citation belongs
    on a page that has methods for it to support.
    """
    keep = []
    for part in re.split(r"(?<=[.?!])\s+", text):
        if re.match(r"^(registrations read|authority|eligibility is|every registration)",
                    part.strip(), re.I):
            break
        keep.append(part.strip())
        if len(" ".join(keep).split()) >= 45:
            break
    return " ".join(keep).strip() or text


def holds_no_poolable_evidence(obj):
    """True when no outcome has two readable trials by registration sharing a measure.

    The same predicate `scripts/measure_poolability_2026_08_24.py` reports the split with,
    kept here so the page and the census cannot drift apart. A WITHDRAWN pool does NOT come
    here: those topics hold readable per-trial estimates and a recorded reason the pool was
    retracted, which is evidence and a finding, and publishing a four-sentence statement in
    its place would say "nothing was found" where the truth is "this was found and
    deliberately not combined".
    """
    for blk in ((obj.get("results") or {}).get("by_outcome") or {}).values():
        if not isinstance(blk, dict):
            continue
        rows = [r for r in (blk.get("per_trial") or [])
                if isinstance(r, dict)
                and all(r.get(k) is not None for k in ("point", "ci_low", "ci_high"))]
        ncts = {str(r.get("nct") or r.get("trial_id") or "").strip() for r in rows}
        ncts.discard("")
        measures = {str(r.get("measure")) for r in rows if r.get("measure")}
        if len(ncts) >= 2 and len(measures) == 1:
            return False
    return True


def _trials(obj):
    out = []
    for t in (obj.get("inputs") or {}).get("trials") or []:
        if not isinstance(t, dict):
            continue
        nct = str(t.get("nct") or t.get("registration") or "").strip()
        if nct:
            # `label` FIRST WAS THE WRONG FIELD. This corpus stores the trial's name under
            # `name` -- SOLOIST-WHF, SPRINT, CLEAR-Outcomes -- and `label` is mostly absent,
            # so 74 trials across 19 pages rendered the fallback "title not recorded in the
            # registry read". That fallback is not merely blank, it is a false claim ABOUT
            # THE REGISTRY: it tells a reader the registration carried no title when in fact
            # we read the wrong key. `registration_brief_title` is the registry's own words
            # and is taken before giving up.
            #
            # The identical mistake was made twice more in one evening -- a prototype report
            # reading `label`, and a field census guessing `n_randomised` for `enrolled` --
            # so the rule earned here is: when a value looks absent corpus-wide, print the
            # observed key list before believing it.
            name = (str(t.get("name") or "").strip()
                    or str(t.get("label") or "").strip()
                    or str(t.get("registration_brief_title") or "").strip())
            out.append((nct, name, str(t.get("registry") or "").strip()))
    return out


def _outcome_name(obj, oid):
    """The registered outcome text for `oid`, or the id if none is held."""
    for o in (obj.get("outcomes") or []):
        if isinstance(o, dict) and o.get("id") == oid:
            nm = " ".join(str(o.get("name") or "").split())
            if nm:
                return nm
    return str(oid)


def _rows_with_point(obj):
    """Every per-trial row carrying a point estimate, with its outcome id."""
    out = []
    for oid, blk in ((obj.get("results") or {}).get("by_outcome") or {}).items():
        if not isinstance(blk, dict):
            continue
        for r in blk.get("per_trial") or []:
            if isinstance(r, dict) and r.get("point") is not None:
                out.append((oid, r))
    return out


def _per_trial_estimates(obj):
    """(trial, outcome, result) for every estimate that carries an interval.

    ONLY WITH AN INTERVAL. A point estimate alone cannot be weighed by a reader and cannot
    be compared with one that has an interval sitting beside it in the same table.
    """
    out = []
    for oid, r in _rows_with_point(obj):
        lo, hi = r.get("ci_low"), r.get("ci_high")
        if lo is None or hi is None:
            continue
        who = str(r.get("nct") or r.get("trial_id") or "").strip() or "trial not named"
        measure = str(r.get("measure") or "").strip()
        try:
            est = "%s %.2f (%s%% CI %.2f to %.2f)" % (
                measure or "estimate", float(r["point"]),
                r.get("ci_level") or 95, float(lo), float(hi))
        except (TypeError, ValueError):
            continue
        out.append((who, _outcome_name(obj, oid), est.strip()))
    return out


def _bare_point_count(obj):
    """How many estimates are held with no interval, and so are not shown."""
    n = 0
    for _oid, r in _rows_with_point(obj):
        if r.get("ci_low") is None or r.get("ci_high") is None:
            n += 1
    return n


def _why_not_pooled(obj):
    """The SPECIFIC reason, in a reader's words. Never 'insufficient data'."""
    for blk in ((obj.get("results") or {}).get("by_outcome") or {}).values():
        if not isinstance(blk, dict):
            continue
        for key in ("poolable_reason", "withdrawn_reason"):
            src = blk.get(key) or (blk.get("pooled") or {}).get(key)
            safe = _reader_safe(_sentence_case(src or ""))
            if safe:
                return _first_reason(safe)
    return _reader_safe(_sentence_case(str(obj.get("which_limb_fails") or "")))


def _and_list(items):
    """'a', 'a and b', 'a, b and c'. Defined here because statement.py had no such helper
    and the first version of the pending-trials sentence called one that does not exist --
    a NameError that would have fired only on the pages this feature is FOR, which are the
    pages nobody looks at."""
    items = [str(x) for x in items if str(x).strip()]
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    return "%s and %s" % (", ".join(items[:-1]), items[-1])


def _awaiting_results(obj):
    """Eligible trials that exist and are registered but have not reported yet.

    THE THIRD HONEST ANSWER, and it was missing. A page that cannot pool had exactly two
    things it could say: we found the wrong trials, or no eligible trial exists. Neither
    describes AMOXICILLIN_AOM, where plain-amoxicillin trials in acute otitis media DO exist
    -- NCT06895135 and NCT07730814 -- and are NOT_YET_RECRUITING, the second not completing
    until 2031.

    Forcing that into either box misdescribes it, and in opposite directions: "no eligible
    trial exists" is false and closes a question that is open, while "we matched the wrong
    trial" implies a fixable error and invites a search that will find nothing usable.

    "A trial exists and will report in 2031" is the useful sentence. A reader can act on it:
    they know the question is live, they know nothing is being hidden, and they know when to
    come back. It is also the only one of the three that is true here.

    Read from `awaiting_results`, a list of {nct, status, expected} the object may record.
    Absent means not recorded -- never inferred, because inferring it would manufacture a
    trial.
    """
    rows = obj.get("awaiting_results")
    if not isinstance(rows, list):
        return None
    out = []
    for r in rows:
        if not isinstance(r, dict):
            continue
        nct = str(r.get("nct") or "").strip()
        if not nct:
            continue
        out.append((nct, str(r.get("status") or "").strip(),
                    str(r.get("expected") or "").strip()))
    return out or None


def _what_would_change_it(obj):
    """Derived from WHICH limb failed, so a reader knows whether to come back."""
    limb = str(obj.get("which_limb_fails") or "").lower()
    trials = _trials(obj)

    # NAMED, DATED, AND FIRST -- before any of the generic branches, because when a trial is
    # already registered and pending, that is the most specific true thing the page can say
    # and every sentence below it would be vaguer.
    pending = _awaiting_results(obj)
    if pending:
        bits = []
        for nct, status, expected in pending[:3]:
            piece = nct
            if status:
                piece += " (%s" % status.lower()
                piece += ", expected %s)" % expected if expected else ")"
            elif expected:
                piece += " (expected %s)" % expected
            bits.append(piece)
        return ("A pooled result becomes possible when the eligible trials that are already "
                "registered report their results: %s. They have not been matched to this "
                "question in error and they have not been overlooked -- they exist and have "
                "not reported yet." % _and_list(bits))
    if "outcome" in limb:
        return ("A pooled result becomes possible if these trials report a shared clinical "
                "outcome, or if a trial that registers one is added to this question.")
    if "comparator" in limb:
        return ("A pooled result becomes possible if trials sharing a common comparator "
                "are identified, so that like is compared with like.")
    if "participants" in limb or "population" in limb:
        return ("A pooled result becomes possible if trials in a common population are "
                "identified, or if the question is narrowed to one of the populations here.")
    if not trials:
        # "A SECOND eligible trial" is wrong when the first was never found. The sentence
        # has to match the state it describes, or it quietly asserts that one trial exists.
        return ("A pooled result becomes possible when eligible trials reporting a shared "
                "outcome are identified for this question.")
    if "k=1" in limb or (len(trials) < 2):
        return ("A pooled result becomes possible when a second eligible trial reporting "
                "the same outcome is published.")
    if "design" in limb:
        return ("A pooled result becomes possible if trials of a common design are "
                "identified, so that the estimates answer one question.")
    return ("A pooled result becomes possible when trials reporting a shared, comparably "
            "measured outcome are available.")



def _published_assessments(obj):
    """Which of (risk-of-bias, certainty) this object ACTUALLY publishes.

    Keyed on by_outcome entries that contain something, NOT on the presence of
    the parent block or of a verdict field. Two traps sit here and both were
    live:

      * amoxicillin-aom carries a truthy `risk_of_bias_verdict` whose value
        states the DOMAIN RULE ("RoB 2 domain 5 (Handbook 6.5 section 8.7)..."),
        not a judgement about any trial.
      * attr-cm-review carries a `certainty` block with six scaffolding keys
        and an EMPTY by_outcome, so the block is truthy and publishes nothing.

    Membership is not the property. Reading either field as a boolean would
    have produced the same sentence this function exists to stop.
    """
    rb = ((obj.get("risk_of_bias") or {}).get("by_outcome") or {})
    has_rob = any(isinstance(v, dict) and v for v in rb.values())
    ce = ((obj.get("certainty") or {}).get("by_outcome") or {})
    has_cert = any(isinstance(v, dict) and v for v in ce.values())
    return has_rob, has_cert


def _nothing_published_note(obj):
    """The closing note, stating only what the object actually withholds."""
    has_rob, has_cert = _published_assessments(obj)
    because = " because there is no combined result for them to describe."
    if not has_rob and not has_cert:
        return ("No pooled estimate, risk-of-bias assessment or certainty rating "
                "is published for this question," + because)
    also = ("A risk-of-bias assessment and a certainty rating are"
            if has_rob and has_cert else
            "A risk-of-bias assessment is" if has_rob else
            "A certainty rating is")
    withheld = ("No pooled estimate is published for this question,"
                if has_rob and has_cert else
                "No pooled estimate or certainty rating is published for this question,"
                if has_rob else
                "No pooled estimate or risk-of-bias assessment is published for this "
                "question,")
    return ("%s%s %s published below and describe%s the trials, not a combined result."
            % (withheld, because, also, "" if (has_rob and has_cert) else "s"))

def _searched(obj):
    """What was checked and when, in one sentence, or None if nothing is recorded.

    `verification_basis` HAS TWO SHAPES AND `str()` BETRAYED ONE OF THEM. On most objects it
    is a sentence. On six it is a DICT -- {'what_verifies_this_object': ...,
    'what_is_not_claimed': ..., 'families': [...]} -- and `str(a_dict)` is its REPR, so six
    delivered pages carried

        What was checked. {'what_verifies_this_object': 'ClinicalTrials.gov protocol records
        read 2026-08-19 at every registered rank.', 'what_is_not_claimed': 'That any event
        co...

    into the sentence a reader meets first. That is a container repr in prose AND two field
    names in prose, from one `str()` on a value whose type nobody checked.

    The dict holds the sentence; it just holds it under a key. Read the key.
    """
    _vb = obj.get("verification_basis")
    if isinstance(_vb, dict):
        _vb = (_vb.get("what_verifies_this_object")
               or _vb.get("basis") or _vb.get("what_was_checked") or "")
    basis = _reader_safe(_sentence_case(str(_vb or "")))
    # "READ IN FULL" IS A CLAIM ABOUT DEPTH, AND ONLY ONE FIELD WARRANTS IT.
    # `all_ranks_read_utc` records that every registered rank was read; `read_utc`
    # records only that a read happened. The sentence asserted the stronger claim
    # whenever EITHER was present -- and the `or` preferred the weaker field, so a
    # page could cite the shallower timestamp while claiming the deeper reading.
    # Across the corpus 82 objects have all_ranks on every trial, 40 have only
    # read_utc, and 1 has it on some: 41 objects were told they had been read in
    # full on the strength of a timestamp that does not say so.
    #
    # DERIVE OR REFUSE: say "read in full" where every registration warrants it,
    # say what was actually done where it does not, and name the split where the
    # object is mixed rather than rounding it to either end.
    _tr = [t for t in ((obj.get("inputs") or {}).get("trials") or []) if isinstance(t, dict)]
    _full = [t for t in _tr if t.get("all_ranks_read_utc")]
    dates = sorted({str(t.get("all_ranks_read_utc") or t.get("read_utc") or "")[:10]
                    for t in _tr} - {""})
    registries = sorted({r for _, _, r in _trials(obj) if r})
    if registries and dates:
        if _tr and len(_full) == len(_tr):
            what = "was read in full"
        elif _full:
            what = ("was read in full for %d of the %d registrations below, and retrieved "
                    "without a recorded rank-by-rank read for the rest"
                    % (len(_full), len(_tr)))
        else:
            what = ("was retrieved -- this object records no rank-by-rank read, so it does "
                    "not establish that every registered outcome was examined")
        return ("Every registration listed below %s on %s from %s."
                % (what, dates[-1], " and ".join(registries)))
    return basis


def _identity_check_sentence(obj):
    """What the trial-identity check could and could not decide, in the page's own words.

    MAHMOOD: "A page whose trials are undecidable should say so rather than implying they
    were checked and passed. Undecidable is a third state on the page as well as in the
    code."

    Silence here is the defect. A page that lists its trials and says nothing about whether
    they study its subject reads as though they were verified -- and on 113 of 420 records
    across the corpus, they were not. The check could not decide, because registered arm
    names are paraphrases: NCT00643188 registers "Procedure: Radiofrequency ablation" for a
    review that says "catheter ablation".

    Returns None where no check has been recorded, because a page must not claim a check that
    never ran either.
    """
    blk = obj.get("trial_identity_check")
    if not isinstance(blk, dict):
        return None
    ns, nn, nu = (blk.get("n_studied") or 0, blk.get("n_not_studied") or 0,
                  blk.get("n_undecidable") or 0)
    total = ns + nn + nu
    if not total:
        return None
    # The heading already asks the question, so the sentence answers it rather than
    # restating it -- "Whether these trials study this subject. Whether each trial studies
    # the subject..." was the first version, and read like a stutter.
    bits = ["Checked against each registration's arm structure on %s."
            % (blk.get("checked_utc") or "an unrecorded date")]
    if ns:
        bits.append("%d of %d %s confirmed: the drug is part of the randomised comparison."
                    % (ns, total, "trial was" if ns == 1 else "trials were"))
    if nn:
        bits.append("%d %s given in every arm, so %s background therapy rather than what the "
                    "trial randomised." % (nn, "trial was" if nn == 1 else "trials were",
                                           "it is" if nn == 1 else "they are"))
    if nu:
        bits.append("%d could NOT be decided this way, because the registered arm names do "
                    "not name the intervention the way this review does. That is not a pass: "
                    "%s unverified, and no other check has looked."
                    % (nu, "it remains" if nu == 1 else "they remain"))
    return " ".join(bits)


def statement_html(obj, e):
    """The whole statement. `e` escapes; every value here is object text."""
    title = (obj.get("title") or "").strip()
    question = _reader_safe(obj.get("question") or "")
    searched = _searched(obj)
    trials = _trials(obj)
    why = _why_not_pooled(obj)
    change = _what_would_change_it(obj)
    identity = _identity_check_sentence(obj)

    out = ["<div class='card'>", "<h2>Summary</h2>"]

    # A TOPIC WITH NO TRIALS AT ALL IS AN ABSENCE, AND MUST DECLARE ITSELF AS ONE.
    #
    # Four objects -- caspofungin-fungal, emtricitabine-hiv, etesevimab-covid, men-acwy --
    # record ZERO trials. The statement rendered honest prose for them, but the corpus
    # regression signal `ssot_empty_panel` refused it, and rightly: a panel that merely
    # reads thin is indistinguishable from one that failed to populate. The property this
    # project holds is that an absence DECLARES itself with a reason, in the markup a
    # reader's eye and a checker both recognise, rather than being inferred from a short
    # page. Same content; stated as what it is.
    # THREE STATES, BECAUSE "WE FOUND NOTHING" AND "WE DID NOT LOOK" ARE DIFFERENT CLAIMS.
    #
    # This branch told a reader the page should be read "as A SEARCH THAT FOUND NOTHING". Four
    # live objects reach it -- caspofungin-fungal, emtricitabine-hiv, etesevimab-covid,
    # men-acwy -- and NONE of them holds a search, a screening record, a PRISMA flow or a
    # k-cascade. There is nothing in any of them recording that a search was ever executed, and
    # one says so in its own words: WE NEVER LOOKED. Asserting a search found nothing, when no
    # search is recorded, is a claim about the world made from an absence in our own file.
    #
    # THE OBVIOUS FIX DOES NOT WORK, and testing it is why this helper exists. `searched` is
    # non-empty for all four -- it returns "Conditions, arm groups with types, and registered
    # outcome measures at every rank", which describes WHICH FIELDS OF A REGISTRATION WERE READ,
    # not that a search was run. Gating on it would have fired never and looked like a fix.
    _search_run = any(
        (obj.get(k) not in (None, "", [], {}))
        for k in ("search", "screening", "prisma_flow", "k_cascade"))
    if not trials:
        out.append(
            "<div class='absent-state' role='note'><strong>No trial was identified for "
            "this question.</strong> This review holds no contributing trial, so there is "
            "no evidence here to summarise, pool or assess. What was checked and when is "
            "given below, so that this is read as a search that found nothing rather than "
            "as a page that failed to load.</div>"
            if _search_run else
            "<div class='absent-state' role='note'><strong>No trial records are held on "
            "this object, and no search record is held either.</strong> This page holds no "
            "contributing trial, and it also holds no search, screening record, PRISMA flow "
            "or screening cascade &mdash; so it cannot tell you whether a registered trial "
            "for this question exists. Read this as a page that has not looked, NOT as a "
            "search that found nothing. The two are different claims and only the first is "
            "supported here.</div>")

    if question:
        out.append("<p><strong>Question.</strong> %s</p>" % e(question))
    if searched:
        out.append("<p><strong>What was checked.</strong> %s</p>" % e(searched))

    if trials:
        out.append("<p><strong>What was found.</strong> %d registered trial%s:</p>"
                   % (len(trials), "" if len(trials) == 1 else "s"))
        out.append("<table><tr><th>Registration</th><th>Trial</th></tr>")
        for nct, label, _reg in trials:
            out.append("<tr><td>%s</td><td>%s</td></tr>"
                       % (e(nct), e(label or "title not recorded in the registry read")))
        out.append("</table>")
    elif _search_run:
        out.append("<p><strong>What was found.</strong> No registered trial was "
                   "identified for this question.</p>")
    else:
        # The same distinction, in the sentence a reader is most likely to quote. "No
        # registered trial was identified" reads as a finding about the evidence base; without
        # a search record it is only a fact about this file.
        out.append("<p><strong>What was found.</strong> No trial records are held on this "
                   "object. Because no search or screening record is held either, this page "
                   "cannot conclude that no registered trial exists for this question.</p>")

    # WHAT THE TRIALS FOUND, WHERE THEY FOUND ANYTHING.
    #
    # A STATEMENT THAT NOTHING WAS POOLED IS NOT A LICENCE TO WITHHOLD WHAT WAS MEASURED.
    # Four topics reach this page holding a readable estimate -- bempedoic-acid-review
    # carries CLEAR-Outcomes at HR 0.87 (0.79 to 0.96) and intensive-bp-review carries
    # SPRINT at HR 0.75 (0.64 to 0.89) -- and every one of them published "no result is
    # pooled" with the number nowhere on the page. The manuscript layer had the identical
    # defect on unpooled outcomes and two blind reader families called it out in the same
    # words: you found the trial, you assessed it, and then you refused to report what it
    # said because you could not combine it.
    #
    # Not poolable and not findable are different states. This page exists to report the
    # first without ever implying the second.
    ests = _per_trial_estimates(obj)
    if ests:
        out.append("<p><strong>What the trials found.</strong> No estimate below is "
                   "combined with any other; each is the result of a single trial, "
                   "reported as that trial reported it.</p>")
        out.append("<table><tr><th>Trial</th><th>Outcome</th><th>Result</th></tr>")
        for who, what, est in ests:
            out.append("<tr><td>%s</td><td>%s</td><td>%s</td></tr>"
                       % (e(who), e(what), e(est)))
        out.append("</table>")
    n_bare = _bare_point_count(obj)
    if n_bare:
        # A POINT ESTIMATE WITH NO INTERVAL IS NOT A RESULT A READER CAN USE, and
        # antimalarial-act holds one recorded as RR 0.00 -- an arm with no events. Printing
        # "0.00" beside intervals that others carry invites it to be read as a real and
        # extraordinary effect. It is counted and named instead of shown.
        out.append("<p><small>%d further per-trial %s recorded without a confidence "
                   "interval and %s not shown here, because a point estimate with no "
                   "interval cannot be weighed.</small></p>"
                   % (n_bare, "estimate is" if n_bare == 1 else "estimates are",
                      "is" if n_bare == 1 else "are"))

    # THE FINDING, AND IT IS THE POINT OF THE PAGE.
    out.append("<p><strong>Why no result is pooled.</strong> %s</p>"
               % e(why or "The trials identified do not report a shared, comparably "
                          "measured outcome, so combining them would answer no single "
                          "question."))
    # BEFORE "what would change this", because a reader deciding whether to trust the trial
    # list needs to know what was verified about it before being told what would change.
    if identity:
        out.append("<p><strong>Whether these trials study this subject.</strong> %s</p>"
                   % e(identity))
    out.append("<p><strong>What would change this.</strong> %s</p>" % e(change))
    # This sentence was emitted unconditionally on 15 pages. On two of them --
    # attr-cm-review and early-rhythm-control-af -- the page displays an
    # assessor-column risk-of-bias table a few sections further down, so the
    # page denied publishing something it was publishing. Derived now.
    out.append("<p><small>%s</small></p>" % e(_nothing_published_note(obj)))
    out.append("</div>")
    return "\n".join(out)
