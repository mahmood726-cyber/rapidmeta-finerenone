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
            out.append((nct, (t.get("label") or "").strip(),
                        str(t.get("registry") or "").strip()))
    return out


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


def _what_would_change_it(obj):
    """Derived from WHICH limb failed, so a reader knows whether to come back."""
    limb = str(obj.get("which_limb_fails") or "").lower()
    trials = _trials(obj)
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


def _searched(obj):
    """What was checked and when, in one sentence, or None if nothing is recorded."""
    basis = _reader_safe(_sentence_case(str(obj.get("verification_basis") or "")))
    dates = sorted({str(t.get("read_utc") or t.get("all_ranks_read_utc") or "")[:10]
                    for t in ((obj.get("inputs") or {}).get("trials") or [])
                    if isinstance(t, dict)} - {""})
    registries = sorted({r for _, _, r in _trials(obj) if r})
    if registries and dates:
        return ("Every registration listed below was read in full on %s from %s."
                % (dates[-1], " and ".join(registries)))
    return basis


def statement_html(obj, e):
    """The whole statement. `e` escapes; every value here is object text."""
    title = (obj.get("title") or "").strip()
    question = _reader_safe(obj.get("question") or "")
    searched = _searched(obj)
    trials = _trials(obj)
    why = _why_not_pooled(obj)
    change = _what_would_change_it(obj)

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
    if not trials:
        out.append(
            "<div class='absent-state' role='note'><strong>No trial was identified for "
            "this question.</strong> This review holds no contributing trial, so there is "
            "no evidence here to summarise, pool or assess. What was checked and when is "
            "given below, so that this is read as a search that found nothing rather than "
            "as a page that failed to load.</div>")

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
    else:
        out.append("<p><strong>What was found.</strong> No registered trial was "
                   "identified for this question.</p>")

    # THE FINDING, AND IT IS THE POINT OF THE PAGE.
    out.append("<p><strong>Why no result is pooled.</strong> %s</p>"
               % e(why or "The trials identified do not report a shared, comparably "
                          "measured outcome, so combining them would answer no single "
                          "question."))
    out.append("<p><strong>What would change this.</strong> %s</p>" % e(change))
    out.append("<p><small>No pooled estimate, risk-of-bias assessment or certainty rating "
               "is published for this question, because there is no combined result for "
               "them to describe.</small></p>")
    out.append("</div>")
    return "\n".join(out)
