# -*- coding: utf-8 -*-
"""Render WHO DECIDED EACH RISK-OF-BIAS DOMAIN, per trial, per assessor.

⛔ THE DEFECT THIS CLOSES, MEASURED ON THE BUILT BYTES of AGYW_HIV_PREP_REVIEW.html:

    the OBJECT knows            assessors: Claude Opus 5 (anthropic),
                                           GPT-5 Codex (openai), via `codex exec`
                                per-domain judgements from each, and their agreement
    the PAGE renders            "anthropic" x5, "openai" x5, "Assessor" x6,
                                "inter-assessor" x2
    the PAGE does NOT render    "Claude Opus 5"  0
                                "GPT-5 Codex"    0
                                per-domain attribution  0

⇒ A reader can see THAT two assessors were involved and cannot see WHO JUDGED WHICH DOMAIN.
That is material held in the object and withheld by the page -- the same defect as the
unprinted registrations, and formal GRADE is one of only two axes lost across six blinded
judges. A certainty rating is auditable only when each domain call traces to whoever made it.

⚠️ AND THE MATERIAL ONLY BECAME RENDERABLE TONIGHT. `rob_block` carried `judgements: [j1,
j2]` -- attributable ONLY by list position against the `assessors` array, and in the native
path compacted with `[x for x in js if x is not None]`, so a missing first assessor silently
shifted the second one's call into index 0. A LIST POSITION IS NOT AN IDENTITY. `by_assessor`
now carries the name on every entry; this renders it.

⛔ COLLAPSED, CSS-ONLY, NO RUNTIME -- the same contract as the screening ledger. The tab
shell is radio inputs and sibling selectors; this must not be the one thing needing a script.
"""
from __future__ import annotations

import html
import re

_OPEN_RE = re.compile(r"<details[^>]*\sopen[\s>]", re.I)

# Kept in step with paper_projector._VALIDATION_PROSE. If that pattern changes and this does
# not, this guard goes quiet -- so it is asserted against the projector's own pattern below
# rather than trusted as a copy.
_REMOVER_STRINGS = re.compile(
    r"model famil|independent file access|second, independent assessment|"
    r"this repository|codex exec|badge this|verification rests|"
    r"each asked to find a defect|pure projection", re.I)


def removers_in_step():
    """True when this module's copy still matches the projector's own pattern.

    A guard built from a COPY of someone else's regex is a guard that stops firing the day
    they edit theirs, silently. This lets a caller assert the two are the same object.
    """
    try:
        from paper_projector import _VALIDATION_PROSE as theirs
    except Exception:
        return None
    return theirs.pattern == _REMOVER_STRINGS.pattern

# A judgement a reader should not have to look up. Ordered worst-first so a scan finds the
# problems before the reassurance.
_RANK = {"HIGH": 0, "SOME_CONCERNS": 1, "NO_INFORMATION": 2, "LOW": 3}


def _e(v):
    return html.escape("" if v is None else str(v), quote=True)


def _cells(dom, assessors):
    """One cell per DECLARED assessor, by NAME -- never by list position.

    An assessor who did not judge this domain gets an explicit "not judged" cell rather than
    a shorter row. A shorter row is what made position unreliable in the first place.
    """
    got = {a.get("n"): a for a in (dom.get("by_assessor") or []) if isinstance(a, dict)}
    out = []
    for a in assessors:
        n = a.get("n")
        rec = got.get(n)
        # ⛔ THE ASSESSOR IS NAMED IN EVERY CELL, NOT ONCE IN THE HEADER.
        #
        # A single attribution line at the head of a table is what lets a reader assume ONE
        # judge decided everything -- and the entire point of this section is that two
        # assessors agreed on some domains and differed on others. A header-only name reads
        # as a property of the TABLE; a per-cell name reads as a property of the CALL. It
        # also survives what a header cannot: a reader copying one row, a screen reader
        # announcing cells away from their column, or a later renderer that reflows the
        # table and drops the head.
        who = _e(a.get("name") or ("assessor %s" % n))
        if rec is None:
            out.append('<td class="nj"><span class="noid">not judged</span>'
                       '<span class="who"> &mdash; %s</span></td>' % who)
        else:
            out.append('<td>%s<span class="who"> &mdash; %s</span></td>'
                       % (_e(rec.get("judgement")), who))
    return "".join(out)


def render(block, measured_utc):
    """The attribution table. Returns "" when the object holds no assessment to attribute.

    Returning "" rather than a placeholder is deliberate: an object with no risk-of-bias
    assessment must not grow a section implying one exists.
    """
    if not isinstance(block, dict):
        return ""
    assessors = [a for a in (block.get("assessors") or []) if isinstance(a, dict)]
    trials = [t for t in (block.get("trials") or []) if isinstance(t, dict)]
    if not assessors or not trials:
        return ""

    # ⛔ EVERY DOMAIN LANDS IN EXACTLY ONE BUCKET AND THE BUCKETS MUST SUM. A negative guard
    # with `continue` here would drop a domain out of the denominator silently, which is the
    # defect this repo has 253 instances of.
    attributed = unattributed = 0
    for t in trials:
        for d in (t.get("domains") or []):
            if isinstance(d, dict) and (d.get("by_assessor") or []):
                attributed += 1
            else:
                unattributed += 1
    total = attributed + unattributed
    if total == 0:
        return ""

    head = "".join("<th>%s</th>" % _e(a.get("name") or ("assessor %s" % a.get("n")))
                   for a in assessors)
    rows = []
    for t in trials:
        rows.append('<tr class="trial"><th colspan="%d">%s</th></tr>'
                    % (len(assessors) + 2, _e(t.get("trial") or t.get("id"))))
        doms = sorted((d for d in (t.get("domains") or []) if isinstance(d, dict)),
                      key=lambda d: str(d.get("domain")))
        for d in doms:
            ag = d.get("agreed")
            agtxt = "&mdash;" if ag is None else ("agree" if ag else "<strong>differ</strong>")
            rows.append("<tr><td>%s</td>%s<td>%s</td></tr>"
                        % (_e(d.get("domain_name") or d.get("domain")),
                           _cells(d, assessors), agtxt))

    frag = (
        '<details class="rob-attribution"><summary><strong>Who judged each domain</strong>'
        ' &mdash; %d domain call%s across %d trial%s, %d assessor%s named. Expand to see '
        'every call and who made it.</summary>'
        '<p class="attr-head">Each row is one risk-of-bias domain for one trial, with the '
        'judgement each named assessor recorded. %s Read %s.</p>'
        '<table class="rob-attr"><thead><tr><th>Domain</th>%s<th>Agreement</th></tr></thead>'
        '<tbody>%s</tbody></table></details>'
        % (total, "" if total == 1 else "s", len(trials), "" if len(trials) == 1 else "s",
           len(assessors), "" if len(assessors) == 1 else "s",
           ("<strong>%d of %d domain calls carry no attribution</strong> and say so rather "
            "than being omitted." % (unattributed, total)) if unattributed else
           "Every domain call carries the assessor who made it.",
           _e(measured_utc), head, "".join(rows)))

    # ⛔ WOULD THE PROJECTOR'S OWN REMOVERS DELETE THIS?
    #
    # `ssot/paper_projector.py` runs three text removers over prose before it reaches a page,
    # and one of them, `_VALIDATION_PROSE`, exists to strip the vocabulary of independent
    # verification: `model famil`, `independent file access`, `second, independent
    # assessment`, `verification rests`, `codex exec`, `pure projection`.
    #
    # ⚠️ AND THIS RENDERER EMITS ONE OF THOSE STRINGS BY NECESSITY. Assessor 2 is literally
    # named "GPT-5 Codex (openai family), via `codex exec`". Naming the assessor in every
    # cell -- which is the whole point, so a reader cannot assume one judge decided
    # everything -- took the exposure from 1 occurrence to 11.
    #
    # ⇒ A renderer whose output a downstream remover deletes is BUILT AND INVISIBLE, and the
    # fragment cannot tell you: only the page can. So this refuses at build time and names
    # the strings, rather than emitting attribution that may silently not arrive. The fix is
    # to route this fragment around the prose removers -- it is a table, not prose -- and
    # NOT to rename the assessor, because the name is the provenance.
    stripped = _REMOVER_STRINGS.findall(frag)
    if stripped:
        raise ValueError(
            "refusing to emit: this fragment contains %d occurrence(s) of text that "
            "paper_projector's _VALIDATION_PROSE remover deletes (%s). Route it around the "
            "prose removers -- it is a table. Renaming the assessor would falsify the "
            "provenance this section exists to show."
            % (len(stripped), ", ".join(sorted(set(stripped)))))

    if _OPEN_RE.search(frag):
        raise ValueError("refusing to emit: a <details> carries `open`. Collapse is a "
                         "property of this module, not a habit of its callers.")
    if "<script" in frag.lower():
        raise ValueError("refusing to emit: this fragment contains a script. The shell is "
                         "CSS-only and works offline; this must not be what breaks that.")
    return frag


SHOWN_WHOLE = "SHOWN_WHOLE"
SHOWN_TRUNCATED = "SHOWN_TRUNCATED"
NOT_SHOWN = "NOT_SHOWN"
CRITERION_DEGENERATE = "CRITERION_DEGENERATE"


def _witness(s, page_html):
    """The longest prefix of `s` present in `page_html`, and whether it LOCATES s uniquely.

    Returns (prefix, unique) where prefix is "" if nothing matches.

    ⛔ TWO WRONG CRITERIA WERE TRIED HERE, IN OPPOSITE DIRECTIONS, AND BOTH ARE INSTRUCTIVE.

    (1) `min_prefix=12` -- a TUNED LENGTH. Not a criterion, a threshold chosen against the
        values in front of you, and choosing it after seeing which values it rescues fits it
        to its own test set.

    (2) "the shortest prefix unique AMONG THE CANDIDATES" -- which for two assessors returned
        the single character 'C'. That is unique among two names and matches trivially
        anywhere on a 1.3 MB page, so two values GENUINELY ABSENT from the page scored
        SHOWN_TRUNCATED. I reproduced the other lane's degeneracy exactly, inverted:
        theirs read absent as truncated via a 3-character sentence boundary, mine via a
        1-character uniqueness boundary.

    ⇒ UNIQUE AMONG THE CANDIDATES IS NOT INFORMATIVE AGAINST THE PAGE. The witness has to
    LOCATE the value in the artefact, so the test is uniqueness IN THE PAGE: a prefix that
    matches in many places attributes nothing and is reported degenerate rather than scored.
    That is a property, not a length -- it needs no threshold and cannot be tuned.
    """
    best = ""
    for n in range(1, len(s) + 1):
        pre = s[:n]
        if pre in page_html or html.escape(pre, quote=True) in page_html:
            best = pre
        else:
            break
    if not best:
        return "", False
    hits = page_html.count(best) or page_html.count(html.escape(best, quote=True))
    return best, hits == 1


def _witness_among(s, others):
    """Kept for the candidate-uniqueness question, which is a DIFFERENT question.

    ⛔ A STRUCTURAL BOUNDARY IS NOT AUTOMATICALLY A GOOD ONE. Another lane built this same
    three-state check using "the opening sentence" as the truncation witness, and its
    sentence split stopped at the first ". " -- so a value beginning "A. " or "RR. " got a
    three-character witness that matches trivially anywhere on the page, and a field that was
    ENTIRELY ABSENT scored as TRUNCATED. "Use the artefact's own structure" was right about
    where to look and did not by itself make the unit sound.

    ⚠️ AND MY FIRST VERSION HAD THE SAME HOLE WITH A DIFFERENT SHAPE: a fixed
    `min_prefix=12`. A tuned length is not a criterion, it is a threshold chosen against the
    values in front of you -- and choosing it AFTER seeing which values it rescues is how a
    criterion gets fitted to its own test set.

    ⇒ So the witness is chosen by DISTINCTIVENESS, not by length: the shortest prefix that
    is unique among the candidates. If no prefix distinguishes this value from another
    candidate, there IS no witness and the criterion is DEGENERATE for it -- which is a
    state to report, not a length to raise.
    """
    for n in range(1, len(s) + 1):
        pre = s[:n]
        if not any(o != s and o.startswith(pre) for o in others):
            return pre
    return None


def verify_survives(block, page_html, scope=None):
    """Did every emitted string reach the page WHOLE? Three states, never two.

    ⛔ `SHOWN_TRUNCATED` IS A REAL THIRD STATE AND IT IS NOT `NOT_SHOWN`. Another lane found
    a page rendering 389 characters of a 568-character stored paragraph -- and the dropped
    sentence was the one saying the paragraph was DERIVED rather than authored. A check that
    asks "does the text START there" passes that; a check that asks "is the text ABSENT"
    also passes it. Only asking whether it survives WHOLE catches it.

    ⚠️ AND THE TRUNCATION DROPPED THE QUALIFIER, which is the direction that should be
    expected rather than assumed: qualifiers live at the END of sentences, so a length cut
    removes the hedge and keeps the claim. A truncation is not neutral about which half of a
    statement it deletes.

    Returns {state: [strings]} so a caller reports per class rather than a pooled rate.
    """
    out = {SHOWN_WHOLE: [], SHOWN_TRUNCATED: [], NOT_SHOWN: [], CRITERION_DEGENERATE: []}
    if not isinstance(block, dict) or not page_html:
        return out
    wanted = []
    for a in (block.get("assessors") or []):
        if isinstance(a, dict) and a.get("name"):
            wanted.append(str(a["name"]))
    for t in (block.get("trials") or []):
        for d in (t.get("domains") or []):
            if isinstance(d, dict) and d.get("domain_name"):
                wanted.append(str(d["domain_name"]))
    cands = list(dict.fromkeys(wanted))
    for s in cands:
        # The haystack is the SCOPE when one is given, and the whole page otherwise. Mixing
        # the two is what made the first scoped version report everything whole: it tested
        # membership against the page, then consulted the scope only for the middle case, so
        # the scope never changed a verdict.
        hay = (scope(s) if callable(scope) else scope) if scope is not None else page_html
        if hay and (s in hay or html.escape(s, quote=True) in hay):
            out[SHOWN_WHOLE].append(s)
            continue
        # ⛔ TRUNCATION IS NOT DECIDABLE BY SCANNING A WHOLE PAGE FOR PREFIXES, AND I TRIED
        # THREE CRITERIA BEFORE ACCEPTING THAT.
        #
        #   min_prefix=12                a tuned length, fitted to the values in front of me
        #   unique among candidates      returned 'C' for two assessor names
        #   longest prefix, unique in page   still calls a coincidental "Claude " a truncation
        #
        # Every one of them scored a value that is GENUINELY ABSENT as truncated, which is
        # the other lane's degeneracy reproduced three times in three shapes. The reason is
        # structural, not a bug to fix: on a 1.3 MB page SOME prefix of almost any string
        # matches by chance, and "how improbable is this match" cannot be answered without a
        # threshold -- and a threshold chosen here is chosen against these values.
        #
        # ⇒ SO THE INSTRUMENT IS SCOPED INSTEAD. Truncation is decidable when you compare a
        # value against THE REGION THAT SHOULD CONTAIN IT -- which is what made the other
        # lane's finding sound: a specific stored paragraph against its specific rendered
        # counterpart, 389 of 568 characters. Without a scope, this refuses to guess and
        # reports the honest state.
        if scope is None:
            out[CRITERION_DEGENERATE].append(s)
            continue
        region = hay
        if not region:
            out[NOT_SHOWN].append(s)
        elif s in region or html.escape(s, quote=True) in region:
            out[SHOWN_WHOLE].append(s)
        elif any(region.rstrip().endswith(s[:n]) for n in range(len(s) // 2, len(s))):
            # A PROPER PREFIX ending the region: the region stops mid-value. That is
            # truncation with a located boundary, not a coincidental match somewhere.
            out[SHOWN_TRUNCATED].append(s)
        else:
            out[NOT_SHOWN].append(s)
    return out


def tally(block):
    """(attributed, unattributed, total) -- for a caller that wants the numbers per class."""
    a = u = 0
    for t in (block or {}).get("trials") or []:
        for d in (t.get("domains") or []):
            if isinstance(d, dict) and (d.get("by_assessor") or []):
                a += 1
            else:
                u += 1
    return a, u, a + u
