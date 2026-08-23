#!/usr/bin/env python3
"""PROJECT A MANUSCRIPT FROM AN SSOT OBJECT. Every sentence names the field behind it.

WHY THIS IS PROJECTION AND NOT THE INVENTION I REFUSED HOURS AGO. Earlier tonight the objects
held nothing a manuscript could be made of, and writing one would have been fabrication. They
now hold an executed search with its queries and PRISMA counts, a criteria block with sourced
elements, a screening disposition for every surfaced trial, pooled estimates with verbatim
model output, and the estimand reasoning. A manuscript rendered from those is a VIEW of the
object, and every sentence in it can be traced back to the field it came from.

    THE RULE IS THE CRITERIA-DERIVATION RULE, UNCHANGED: A SECTION WITH NO FIELD BEHIND IT DOES
    NOT GET WRITTEN. The tab keeps refusing for that section rather than filling it.

--------------------------------------------------------------------------------------------
THREE PROPERTIES KEPT FROM `F:\\allmeta\\paper\\assets\\js\\paper-studio.js`, AND ONE INVERTED.

KEPT 1 -- IDENTITY JOIN, NEVER POSITIONAL. Its own comment records why: "Effects are joined to
records by identity in the bridge, not by position." That is the same defect class as reading
`outcomeMeasures[0]` -- and this repository has now met that class twice in one night, so the
join here is on registration id and a record whose id does not resolve is REPORTED, not
silently dropped and not silently paired with its neighbour.

KEPT 2 -- OMIT-IF-MISSING. `buildResultsNarrative` states it: "Omits any sentence whose key
values are missing so nothing is fabricated." Every sentence below is emitted only if its
field is present, and the absent ones are listed by name.

KEPT 3 -- HOUSE STYLE AS A PARAMETER, NOT A FORK. One projector, a `journal` and a `length`
parameter, no per-journal copies to drift apart.

INVERTED -- AND THIS IS THE ONE THAT MATTERS. In paper-studio, THE LENGTH DROPDOWN GENERATES
PROCEDURAL CLAIMS. Selecting a longer Methods emits, from no field whatsoever:

    len != "concise"   "Two review authors independently screened records and extracted data,
                        resolving disagreements by discussion."
    len != "concise"   "...study selection and data extraction performed in duplicate."
    len == "detailed"  "Reporting followed the PRISMA 2020 guidance, and the review methods
                        were specified before data collection."
    always             "Risk of bias was assessed using RoB 2, and certainty of evidence using
                        GRADE."                       (`c.rob` defaults to "RoB 2" via `|| `)
    len != "concise"   "Between-study variance (tau^2) was estimated using a random-effects
                        (DerSimonian-Laird) model"    (regardless of the estimator actually used)

    A FORMATTING CONTROL THAT ASSERTS TWO INDEPENDENT REVIEWERS, DUPLICATE EXTRACTION, A
    PRESPECIFIED PROTOCOL AND A NAMED RISK-OF-BIAS TOOL IS MANUFACTURING THE METHODS SECTION.
    It carries an author-facing "please confirm" note, which is a hedge and not a gate: the
    sentence is in the document, in the author's voice, whether or not anyone confirms it.

Methods is the easiest place in a manuscript to write fluent sentences asserting procedures
nobody performed, so here LENGTH CHANGES ONLY HOW MUCH OF WHAT IS RECORDED IS SAID -- never
what is asserted. If the object does not record that something was done, this does not say it
was done. There is no `|| "RoB 2"` anywhere in this file.
"""
import io
import json
import math
import re
import os
import sys

WRITTEN, REFUSED = "WRITTEN", "REFUSED"


def get(obj, path):
    """Dotted lookup returning None rather than raising. `None` and "" are both absent."""
    cur = obj
    for part in path.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return None
    return None if (cur is None or cur == "" or cur == [] or cur == {}) else cur


def _bookkeeping(obj, field):
    """One of the five fetchable PRISMA claims, with the path it came from.

    Returns (text, [source_path]) or (None, None). The key is dated, so the path is built
    from the key that was FOUND rather than retyped -- retyping it is how the same section
    rendered its own correction as a refusal earlier today.
    """
    k = next((x for x in sorted(obj) if str(x).startswith("bookkeeping_")
              and isinstance(obj[x], dict)), None)
    if not k:
        return None, None
    v = obj[k].get(field)
    if not isinstance(v, str) or not v.strip():
        return None, None
    return v.strip(), ["%s.%s" % (k, field)]


def _add_bookkeeping(s, obj, field):
    t, src = _bookkeeping(obj, field)
    return bool(t) and s.add(obj, t, src)


def _drafted(obj, section):
    """The drafted interpretive claims for one section, newest dated key wins.

    A DRAFT IS NEVER RETURNED AS THOUGH IT WERE READ. The caller renders these in a marked
    block, separately from projected facts, because the author replaces them by dictation and
    must be able to see at a glance which sentences are his to replace.
    """
    k = next((x for x in sorted(obj) if str(x).startswith("manuscript_draft_")
              and isinstance(obj[x], dict)), None)
    if not k:
        return []
    # READING ORDER, NOT KEY ORDER. Sorted alphabetically, the Discussion opened with
    # "whether the effect size is clinically meaningful" and reached "why this result differs
    # from the published ones" last -- a paper does not argue in alphabetical order.
    order = ["why_the_question_is_open", "why_a_new_synthesis",
             "what_the_evidence_shows", "is_the_effect_size_clinically_meaningful",
             "is_the_heterogeneity_clinically_important",
             "why_this_differs_from_published", "is_the_evidence_base_adequate",
             "was_the_search_broad_enough", "what_further_evidence_would_change_it",
             "implication_for_practice", "implication_for_policy",
             "implication_for_research"]
    out = []
    for ck, cv in (obj[k].get("claims") or {}).items():
        if isinstance(cv, dict) and cv.get("section") == section and cv.get("is_a_draft"):
            out.append((order.index(ck) if ck in order else 99, ck, cv,
                        "%s.claims.%s.draft" % (k, ck)))
    return [(ck, cv, path) for _n, ck, cv, path in sorted(out)]


def _add_drafts(s, obj, section):
    n = 0
    for ck, cv, path in _drafted(obj, section):
        # ONE SHORT MARKER, SENTENCE CASE, ONCE PER PASSAGE. The marker was longer than
        # some of the sentences it marked, shouted, and repeated for every claim.
        if s.add(obj, "[Draft] %s" % cv.get("draft", ""), [path]):
            n += 1
    return n


def _manuscript_prose(obj, key):
    """Authored manuscript prose, from `manuscript.<key>`, flattened to one string.

    THE PROJECTOR WAS LOOKING IN THE WRONG PLACE ON THE ONE OBJECT THAT HAS THE CONTENT.
    It read top-level `discussion`, `conclusions` and `protocol.rationale`. arni-hfref --
    the flagship, the object every other topic is measured against -- holds all of them
    under `manuscript.{abstract,introduction,discussion,limitations,conclusions}`, and all
    three top-level fields are None on it. Measured 2026-08-20: 29,272 chars sat under
    that block, unread.

    THIS IS WHY IT MATTERS BEYOND ONE OBJECT. "The projector reproduces ~11% of ARNI" was
    quoted as evidence that OBJECTS lack substance. Part of it was evidence that the
    PROJECTOR was reading the wrong key, and the two have very different consequences.

    AND ARNI'S FIELD NAMES ARE NOW THE SCHEMA THE OTHER 140 WRITE INTO -- deliberately,
    rather than inventing one here. A shape invented by the renderer makes every future
    object's content a function of what the renderer happened to ask for, which is the
    `paper-studio.js` failure where a FORMATTING control manufactured a Methods section
    that no field supported. THE OBJECT DECLARES WHAT IT HOLDS AND THE PROJECTOR READS IT,
    never the reverse. ARNI is the only object in 141 with authored manuscript prose, so
    it is the only available declaration of that shape, and it was written by a person
    rather than derived from this file.

    Shapes seen on ARNI: a plain string (`conclusions`), a list of paragraphs
    (`introduction`, `discussion`, `limitations`), and a dict of labelled parts
    (`abstract`). All three are flattened; anything else returns None rather than a
    stringified container, because "{'a': 1}" rendered into a manuscript is worse than a
    refusal.
    """
    m = (obj or {}).get("manuscript")
    if not isinstance(m, dict):
        return None
    v = m.get(key)
    parts = []
    if isinstance(v, str):
        parts = [v.strip()]
    elif isinstance(v, list):
        # Paragraphs are strings on `limitations` and DICTS with `text` and an optional
        # `heading` on `introduction` and `discussion`. Both shapes are real on ARNI.
        for x in v:
            if isinstance(x, str) and x.strip():
                parts.append(x.strip())
            elif isinstance(x, dict) and isinstance(x.get("text"), str) and x["text"].strip():
                h = x.get("heading")
                parts.append(("%s. %s" % (h, x["text"].strip())) if h else x["text"].strip())
    elif isinstance(v, dict):
        for k2, v2 in v.items():
            if isinstance(v2, str) and v2.strip() and not k2.startswith("_"):
                parts.append("%s. %s" % (k2.replace("_", " ").capitalize(), v2.strip()))
    out = "\n\n".join(p for p in parts if p)
    if not out:
        return None
    # THE MANUSCRIPT BLOCK IS A DOCMODEL, NOT PROSE, AND THIS IS THE REAL BOUNDARY.
    #
    # Its paragraphs carry substitution tokens -- [[k]], [[pooled]], [[i2]], [[certainty]]
    # -- that ARNI's own docmodel renderer fills and this projector cannot. The first
    # version of this function returned them raw and put SEVENTEEN unresolved [[token]]
    # strings into the projection, which is a shipped-placeholder defect: the page would
    # have read "rests on [[k]] trials". Caught by grepping the projection before anything
    # was delivered, which is the only reason it is a paragraph here and not an incident.
    #
    # So a paragraph carrying an unresolved token is NOT returned. The section refuses,
    # and it refuses for the true reason -- the text exists and cannot be rendered here --
    # rather than for the false one it gave before, that no text exists.
    # RESOLVE THE TOKENS RATHER THAN REFUSE OVER THEM, because every one of them is a
    # quantity THIS OBJECT ALREADY HOLDS. `paper.build_tokens` resolves 50 of them from
    # the object only -- k, pooled, ci_low, ci_high, i2, tau2, n_total, certainty,
    # estimator -- and it is the same function `make_docx.py` uses, so the docx, the
    # docmodel render and this projection cannot disagree about a number.
    #
    # THE LOGIC, NOT THE TEMPLATE. What is reused is the token table; the rendering stays
    # here. Copying the docmodel renderer would have brought its headings and its layout
    # with it, which is class 71 all over again.
    #
    # THE REFUSAL IS NOT REMOVED, IT IS NARROWED. A token that does NOT resolve still
    # blocks the section, so `rests on [[k]] trials` can never reach a reader. Before
    # this, ARNI's Discussion and Conclusions refused as CONTENT gaps while the object
    # held 7 authored paragraphs and a 534-character conclusion -- the refusal was true
    # about the projector and false about the object, and it was reported to Mahmood as
    # evidence that objects lack substance.
    if TOKEN_RE.search(out):
        out = _resolve_tokens(obj, out)
    if TOKEN_RE.search(out):
        return None
    return out


def _and_list(items):
    """`a`, `a and b`, `a, b and c`. Never a Python list repr in a sentence."""
    xs = [str(i).strip() for i in items if str(i).strip()]
    if not xs:
        return ""
    if len(xs) == 1:
        return xs[0]
    return "%s and %s" % (", ".join(xs[:-1]), xs[-1])


def _sentence_join(parts):
    """Join composed clauses into one readable sentence, without a trailing double stop."""
    xs = [p.strip().rstrip(".") for p in parts if p and p.strip()]
    if not xs:
        return ""
    if len(xs) == 1:
        return xs[0]
    return "%s; and %s" % ("; ".join(xs[:-1]), xs[-1])


def _first_by_outcome(obj, leaf_path):
    """The first non-None value at `results.by_outcome.<any>.<leaf_path>`.

    THE ABSTRACT SUMMARISES; IT DOES NOT SELECT SILENTLY. Where a review has several
    outcomes this reports the first in key order, which is the same one the Findings clause
    already leads with. It is a summary sentence, and the per-outcome detail is in Results
    and in the certainty table -- both of which enumerate every outcome.
    """
    for _oid, blk in sorted((get(obj, "results.by_outcome") or {}).items()):
        cur = blk
        for part in leaf_path:
            cur = cur.get(part) if isinstance(cur, dict) else None
        if cur is not None:
            return cur
    return None


def _authored(obj, field):
    """Authored text from `field`, tokens RESOLVED, or None if any token survives.

    THE TOKEN GUARD MUST COVER EVERY PATH THAT REACHES A READER, NOT JUST ONE. The abstract
    read `manuscript.abstract.Conclusions` directly and bypassed `_manuscript_prose`, so
    ARNI's conclusion reached the projection as "Across [[k]] randomised trials" -- the
    exact shipped-placeholder defect the guard in `_manuscript_prose` exists to stop, out
    through a second door. Caught by reading the output, not by a check.
    """
    v = get(obj, field)
    if v is None:
        return None
    text = _v_str(v)
    if not text:
        return None
    if TOKEN_RE.search(text):
        text = _resolve_tokens(obj, text)
    if TOKEN_RE.search(text):
        return None
    return text


def _num(v, places=1):
    """A stored number, rounded for prose. `I-squared 32.8939087126%` is a machine talking."""
    try:
        f = float(v)
    except (TypeError, ValueError):
        return _v_str(v)
    return ("%.*f" % (places, f)).rstrip("0").rstrip(".") or "0"


def _source_names(dbs):
    """Human names of the searched sources. NEVER a dict repr.

    `search.databases` is a LIST OF DICTS on this corpus and the key is `database`, not
    `name`. The first cut fell through to `str(d)` and put a whole Python dict -- query
    string, tool name and all -- into the Methods sentence of the abstract. A container repr
    in the one paragraph an editor reads first.
    """
    out = []
    items = dbs.values() if isinstance(dbs, dict) else (dbs or [])
    for d in items:
        if isinstance(d, str):
            nm = d
        elif isinstance(d, dict):
            nm = d.get("database") or d.get("name") or d.get("source") or ""
        else:
            nm = ""
        nm = str(nm).split("--")[0].strip()
        if nm and nm not in out:
            out.append(nm)
    return out


def _pc_cell(r, *names):
    """First non-empty of `names` on a published-synthesis record.

    TWO VOCABULARIES WROTE THESE RECORDS AND ONLY ONE WAS EVER READ. The projector asked
    for `scope` and `how_it_differs_from_ours`; the appliers written during the 2026-08-20
    run stored `outcome_pooled` and `agreement`. Sixteen rows across thirteen topics
    therefore reached readers as a PMID beside four empty cells -- limb 3 of the page
    standard written into the object and delivered to nobody. Registry class 83.

    Reading the alternates here is the DELIVERY half of the fix; the objects are repaired
    to carry both names as well, so neither end depends on the other being right.
    """
    for n in names:
        t = str(r.get(n) or "").strip()
        if t:
            return t
    return ""


def _pc_citation(r):
    """A citation, from `citation` if stored and composed from its parts if not."""
    t = str(r.get("citation") or "").strip()
    if t:
        return t
    bits = [str(r.get(k) or "").strip() for k in ("title", "journal", "year")]
    bits = [b for b in bits if b]
    return ". ".join(bits) if bits else ""


def _pc_their_k(r):
    """How many trials THEY carried -- never guessed, and blank rather than wrong.

    Taken from a stored `their_k`, or from the LENGTH of a named trial set. A trial set
    whose first entry is a sentinel ("NOT READ -- ten studies") has length 1 and does NOT
    mean k = 1, so those return blank here and the count is written into the object by
    hand, where it can be audited, rather than parsed out of prose at render time.
    """
    k = r.get("their_k")
    if isinstance(k, int) or (isinstance(k, str) and k.strip()):
        return str(k).strip()
    ts = r.get("trial_set")
    if isinstance(ts, list) and ts and all(
            isinstance(x, str) and not x.strip().upper().startswith("NOT ") for x in ts):
        return str(len(ts))
    return ""


def _v_str(v):
    """Word a stored declaration. NEVER `str()` a container into a manuscript.

    A dict rendered as "{'funder': 'None'}" in a Grant information section is the raw-repr
    defect (class 62's neighbour) landing in the one part of the paper an editor reads for
    compliance. Strings pass through; lists become paragraphs; dicts become `Key. value`
    lines with underscore keys worded and `_`-prefixed bookkeeping keys skipped.
    """
    if isinstance(v, str):
        return v.strip()
    if isinstance(v, (int, float)):
        return str(v)
    if isinstance(v, list):
        parts = [_v_str(x) for x in v]
        return "\n\n".join(p for p in parts if p)
    if isinstance(v, dict):
        parts = []
        for k, val in v.items():
            if str(k).startswith("_"):
                continue
            t = _v_str(val)
            if t:
                parts.append("%s. %s" % (str(k).replace("_", " ").capitalize(), t))
        return "\n\n".join(parts)
    return ""


def _resolve_tokens(obj, text):
    """Substitute `[[name]]` from the object's own quantities. Never invents one."""
    try:
        import paper as _paper
        byo = ((obj.get("results") or {}).get("by_outcome") or {})
        oid = next(iter(byo), None)
        if oid is None:
            return text
        tok = _paper.build_tokens(obj, byo[oid], oid)
    except Exception:                       # noqa: BLE001 - an unresolved token still blocks
        return text
    return TOKEN_RE.sub(lambda m: str(tok.get(m.group(0)[2:-2], m.group(0))), text)


# `[[name]]` substitution tokens, as ARNI's authored docmodel uses them.
TOKEN_RE = re.compile(r"\[\[[a-z0-9_]+\]\]", re.I)



# ---------------------------------------------------------------------------------------
# PROSE HYGIENE, AT THE ONE PLACE EVERY PARAGRAPH PASSES THROUGH.
#
# Four defects made the manuscript read as machine output rather than as a paper, and every
# one of them was fixable in `Section.add` rather than at the hundred sites that call it.
# Fixing at the call site is exactly what was tried for the container-repr class and it did
# not hold: the class recurred in a path the sweep did not cover.
# ---------------------------------------------------------------------------------------

_DICT_REPR = re.compile(r"\{'[^']+':\s*(?:'|\[|\{)")
_LIST_REPR = re.compile(r"\['[^']*'(?:,\s*'[^']*')*\]")


_LEAD_INS = None


def _lead_ins():
    """The key -> English lead-in map, loaded from data rather than written in code.

    Mahmood's decision, 2026-08-23: field names get a proper English lead-in, not a refusal.
    The map lives in `ssot/field_lead_ins.json` so a key can be given a sentence without a
    code change, and so the reasoning for each one is readable next to it.
    """
    global _LEAD_INS
    if _LEAD_INS is None:
        import json as _json
        import os as _os
        p = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "field_lead_ins.json")
        try:
            _LEAD_INS = _json.load(io.open(p, encoding="utf-8"))
        except Exception:
            _LEAD_INS = {"by_key": {}, "cascade_steps": {}, "_refused": {}}
    return _LEAD_INS


def _outcome_label(obj, oid):
    """The outcome's NAME, read from where the object stores it. `None` if it stores none.

    THE OUTCOME-IDENTIFIER LEAK, Mahmood's decision of 2026-08-23: an identifier standing
    where a label belongs becomes the outcome's actual name. `outcomes[]` holds `id` and
    `name`, so the lookup is a lookup and not a guess.

    RETURNS None RATHER THAN THE ID WHEN NO NAME IS STORED, and callers say so. A missing
    label is a MISSING FIELD, not a rendering choice, and printing the identifier while
    calling it a label would be the same substitution this change exists to remove.
    """
    for o in (obj.get("outcomes") or []):
        if isinstance(o, dict) and o.get("id") == oid:
            nm = o.get("name")
            return nm if isinstance(nm, str) and nm.strip() else None
    return None


_NOT_RECORDED = ("not recorded", "not available", "not stated", "no record",
                 "not established", "not captured")


def _lead_in_has_value(v):
    """Absence test for the LEAD-IN ONLY -- deliberately not `_is_value`.

    `_is_value` tests exact membership of `_NULL_MARKERS` and gates POOLING decisions. The
    corpus's absence markers here are long sentences -- "not recorded on the page this object
    was extracted from", 35 of 39 `bar` values -- so an exact-set test calls them present and
    the lead-in produces a sentence about nothing: "The bar this object had to clear was: not
    recorded on the page this object was built from."

    Widening `_is_value` to catch them would change what counts as a backed claim for pooling,
    which is not a presentation decision and is not this change's to make. So the wider test is
    scoped to this one use.
    """
    if not _is_value(v):
        return False
    s = str(v).strip().lower()
    return not any(s.startswith(p) for p in _NOT_RECORDED)


def _lead_in(key, value):
    """One flattened pair as an English sentence, or the bare key if we cannot say what it is.

    A KEY WITH NO ENTRY IS LEFT VISIBLE ON PURPOSE. A fluent wrong sentence is worse than a
    field name: the field name is obviously unfinished and the sentence is not. `families` is
    refused this way -- it appears under two containers with two meanings and the flattened
    text does not say which, so a lead-in would be a confident false statement about how the
    review was screened.
    """
    spec = (_lead_ins().get("by_key") or {}).get(key)
    if not spec:
        return "%s: %s%s" % (key.replace("_", " "), value,
                            "" if value.endswith((".", "?", "!")) else ".")
    form = spec.get("present") if _lead_in_has_value(value) else spec.get("absent")
    if not form:
        return "%s: %s." % (key.replace("_", " "), value)
    out = form % _embed(value) if "%s" in form else form
    return out if out.endswith((".", "?", "!")) else out + "."


# SENTENCE OPENERS THAT MUST LOSE THEIR CAPITAL WHEN EMBEDDED MID-SENTENCE, BY NAME.
#
# The stored values were written as standalone sentences, so many begin with a capital. Dropped
# into a lead-in they produced "This review does not claim That any event count was checked".
# A BLANKET LOWERCASE IS WRONG: the same field holds "ClinicalTrials.gov protocol records", and
# lowercasing by rule turns a proper noun into "clinicalTrials.gov". The general shape of that
# mistake is a rule inferred from one example and applied to a population -- so this is a list.
_EMBED_LC = {"that", "the", "a", "an", "no", "any", "every", "it", "this", "these", "those",
             "whether", "all", "none", "some", "both", "neither", "each", "there", "we",
             "nothing", "not"}


def _embed(value):
    """A stored value prepared to sit INSIDE a sentence rather than to be one.

    Two defects this removes, both measured in the delivered corpus after the lead-ins landed:
    16 double full stops ("... at every registered rank.. This review does not claim ...") from
    a value that already ended in a period meeting a template that supplies one; and a
    capitalised opener mid-clause ("does not claim That any event count ...").
    """
    v = str(value).strip().rstrip(".").strip()
    if not v:
        return v
    first = re.split(r"[^A-Za-z]", v, 1)[0]
    if first.lower() in _EMBED_LC and first[:1].isupper():
        v = v[:1].lower() + v[1:]
    return v


def _flatten_container(text):
    """A Python container reaching rendered prose is the container-repr class.

    `{'what_verifies_this_object': 'Two things...', 'families': ['openai', 'google']}` was
    printed in a Methods body. The value is real and belongs on the page; its REPR does not.
    Dicts become `key: value.` sentences and lists become `a, b and c`, so the content
    survives and the punctuation of a data structure does not.

    THIS FIX IS NOT COMPLETE AND THE PROBE THAT SAID IT WAS WAS MEASURING THE WRONG THING.
    ------------------------------------------------------------------------------------
    The container-repr class was reported CLOSED on the strength of a probe that searched
    delivered pages for BRACES AND QUOTES and found zero. It found zero because this function
    removes the braces. IT DOES NOT REMOVE THE FIELD NAMES -- it promotes them to prose
    labels. Delivered MAVACAMTEN_HCM_REVIEW, Methods-search, verbatim:

        ... on the dates recorded on each entry; what verifies this object:
        ClinicalTrials.gov protocol records, read 2026-08-18. what is not claimed: that any
        per-trial count was checked against a results record. bar: not recorded on the page
        this object was built from.

    `bar:` is a schema identifier sitting in a sentence. A reader meets a data structure with
    its punctuation filed off, which is most of the way to where it started.

    THE GENERAL LESSON, WHICH COST THREE INSTANCES IN ONE NIGHT TO LEARN: A CHECK BUILT TO
    FIND THE THING THE FIX REMOVED CAN ONLY EVER AGREE WITH THE PERSON WHO WROTE THE FIX.
    Key the probe to what a READER MEETS, never to the artefact the remedy happens to delete.
    The correct predicate here is "does a schema identifier appear where a sentence should
    be", and braces are irrelevant to it. That probe is
    `scripts/lint_field_name_in_reader_prose_2026_08_23.py`; its positive control is this
    page's `bar:`, found by a census lane reading the page, NOT a fixture written by whoever
    wrote this function.

    IT MEASURES 220 OCCURRENCES ACROSS THE DELIVERED CORPUS -- `what verifies this object`
    66, `what is not claimed` 61, `bar` 57, plus outcome IDs (`post_hoc`, `primary_oa`,
    `cvdeath_or_whf_first`) which are a SECOND leak: an outcome identifier standing where an
    outcome label belongs.

    AND THE STRUCTURAL FORM OF THE SAME LESSON, WHICH IS THE ONE WORTH KEEPING:
    A PROBE SEES ONLY THE SHAPE IT WAS WRITTEN FOR, AND A SHAPE DISTINCTION READS AS A
    DISAGREEMENT BETWEEN PEOPLE.
    ---------------------------------------------------------------------------------------
    Two review lanes reported ARNI_HF_REVIEW as carrying the dict leak and as not carrying it,
    and an hour went into treating that as a contradiction to arbitrate. It was not one. This
    class has TWO shapes and each lane's probe saw exactly one:

        container-key shape    `bar:`, `what verifies this object:`   ABSENT from ARNI
        outcome-identifier     `primary_oa` x4, `prior_meta` x1       PRESENT on ARNI

    Both lanes read the page correctly. Neither was careless. The failure was structural --
    each probe was complete with respect to the shape its author had in mind and silent about
    the other, and silence is indistinguishable from absence at the reporting layer.

    So when two readings of one page conflict, the first question is NOT which reader was
    wrong. It is whether the two probes are looking for the same shape. A disagreement that
    dissolves under that question was never a disagreement, and resolving it by picking a
    winner would have recorded one correct reading as an error.

    WHY IT IS NOT FIXED HERE. Closing it properly means deciding WHERE the pairs go, and the
    standing constraint is that nothing is removed from the page, only moved out of the
    reading flow. Dropping the keys alone breaks the values -- "that any per-trial count was
    checked against a results record" asserts nothing without the label that governs it. The
    honest shapes are (a) refuse the sentence and name the obstacle, keeping the structure in
    "Sources for this section", or (b) map each key to an English lead-in. Both are design
    decisions about what a reader is owed, not presentation tweaks, and they are Mahmood's.
    Left standing, measured, and named rather than half-fixed again.
    """
    def _list(m):
        items = re.findall(r"'([^']*)'", m.group(0))
        if len(items) <= 1:
            return items[0] if items else ""
        return ", ".join(items[:-1]) + " and " + items[-1]

    text = _LIST_REPR.sub(_list, text)
    if not _DICT_REPR.search(text):
        return text
    out, i = [], 0
    while True:
        m = _DICT_REPR.search(text, i)
        if not m:
            out.append(text[i:])
            break
        start = m.start()
        depth, j = 0, start
        while j < len(text):
            if text[j] == "{":
                depth += 1
            elif text[j] == "}":
                depth -= 1
                if depth == 0:
                    j += 1
                    break
            j += 1
        out.append(text[i:start])
        body = text[start:j]
        # STRING **AND** LIST VALUES. Matching only strings dropped
        # `families: [openai, google]` silently, and the instruction on every one of
        # these repairs is that the facts survive and only the presentation changes.
        # ANCHORED TO A PAIR BOUNDARY. `'([^']+)':` could start matching inside a
        # previous list's items, so the pair that followed a list was swallowed and
        # `families: [openai, google]` vanished from the flattened text. A presentation fix
        # that drops a fact is the thing this project refuses all week; it cannot be the fix
        # that ships.
        pairs = re.findall(
            r"(?:[{,]\s*)'([^']+?)':\s*(\[[^\]]*\]|'(?:[^'\\]|\\.)*')", body)
        bits = []
        for _k, _raw in pairs:
            if _raw.startswith('['):  # a list value is a fact and must survive
                _it = re.findall(r"'([^']*)'", _raw)
                _v = (', '.join(_it[:-1]) + ' and ' + _it[-1]) if len(_it) > 1 else (
                    _it[0] if _it else '')
            else:
                _v = _raw[1:-1]
            _v = _v.strip()
            if _v:
                bits.append(_lead_in(_k, _v))
        out.append(' '.join(bits))
        i = j
    return "".join(out)


# WORDS THAT ARE CAPITALS BECAUSE THAT IS THEIR NAME, not because we were shouting.
_KEEP_CAPS = {
    "GRADE", "PRISMA", "REML", "REM", "DL", "PM", "HR", "RR", "IRR", "MD", "SMD", "RD",
    "CI", "NCT", "PMID", "DOI", "FDA", "EMA", "NICE", "WHO", "RCT", "RCTS", "ITT", "PP", "AE",
    "SAE", "LDL", "HFPEF", "HFREF", "CKD", "T2D", "HIV", "PCI", "MI", "TOC", "APOLLO",
    "HELIOS", "JUPITER", "EMPEROR", "STEP", "FLOW", "SELECT", "ROSE", "TIGER", "HORUS",
    "DELIVER", "FIDELIO", "FIGARO", "FIDELITY", "ORION", "CHAMPION", "US", "UK", "EU",
    # RATING WORDS ARE VALUES, NOT EMPHASIS. Lowercasing GRADE LOW to "GRADE low" turns a
    # recorded certainty rating into an adjective, which is a loss of meaning and not a
    # change of presentation.
    "LOW", "HIGH", "MODERATE",

    "CERTAINTY", "PROSPERO", "REFUSED", "WITHDRAWN", "PENDING",
    # NOT function words. `IS`, `THE`, `AND`, `A` were in this set at first and the
    # result was "A Disagreement rate IS meaningless without THE facts" -- half-shouted,
    # which reads worse than the shouting did. Inside a run being de-emphasised, a
    # conjunction is a conjunction.
}
# TWO WORDS, NOT THREE, AND PUNCTUATION INSIDE THE RUN.
#
# The first version required three consecutive all-caps words and 51 runs survived it on one
# page -- shorter ones, and ones broken by a comma, a dash or a full stop. Emphasis does not
# come in a minimum length.
_CAPS_RUN = re.compile(
    # A ONE-LETTER WORD DOES NOT END A RUN OF SHOUTING.
    # "BOTH CONTRIBUTING TRIALS SET A MINIMUM AGE OF 18 YEARS" was two runs
    # separated by "A", so both halves lowered and the "A" stood alone in the
    # middle of the sentence: "...trials set A minimum age of 18 years".
    r"\b(?:[A-Z][A-Z'\-]*[,;:\-]?\s+){1,}[A-Z][A-Z'\-]{1,}\b")


# A SINGLE SHOUTED WORD IS STILL SHOUTING. The run rule needs two adjacent capitalised words,
# so `ELIGIBILITY turns on...`, `adults with CHRONIC heart failure`, `Background is ARGUMENT`
# and `it does NOT turn on` all survived it -- and those are the ones left on the live page.
#
# WHAT IS NOT TOUCHED, and the exclusions matter more than the rule:
#   anything in _KEEP_CAPS                     GRADE, PRISMA, REML, trial acronyms
#   anything with an underscore                NO_INFORMATION, SOME_CONCERNS -- stored values
#   anything adjacent to a hyphen              DAPA-HF, EMPEROR-Reduced
#   anything containing a digit                COVID19, PHASE3
#   anything with no vowel                     RCT, NCT, HR, CI -- initialisms
#   anything of three letters or fewer         too likely to be an initialism
_SINGLE_CAPS = re.compile(r"(?<![A-Z0-9_\-])\b([A-Z]{3,})\b(?![A-Z0-9_\-])")
_VOWELS = set("AEIOUY")
# VERDICT TOKENS ARE VALUES IN A TABLE CELL AND ORDINARY WORDS IN A SENTENCE.
# Protecting them globally produced "No PROSPERO registration OR protocol record is
# HELD on this object" -- a stored verdict word leaking into prose because a cell
# elsewhere needed it. The protection is passed in by the caller that needs it.
_CELL_TOKENS = {"HELD", "FAIL", "PASS", "SKIP", "ABSENT", "PRESENT", "REFUSING",
                "STANDS", "WITHDRAWN", "REFERRED", "PENDING", "UNSTAMPED", "PROOF",
                "OR", "RR", "HR"}
# SHOUTED SHORT WORDS, BY NAME. The four-letter floor leaves "it does NOT turn on" and
# its neighbours standing. A general three-letter rule would eat RCT, NCT, ITT, AE and
# every initialism in the corpus, so these are listed rather than inferred.
_SHOUTED_SHORT = {"NOT", "AND", "BUT", "ALL", "ANY", "ONE", "TWO", "NOR", "YET", "OWN",
                  "WHY", "HOW", "WHO", "NEW", "OLD", "FEW", "PER", "VIA", "THE", "ITS"}


def _lower_single_caps(text):
    def _fix(m):
        w = m.group(1)
        if w in _KEEP_CAPS:
            return w
        if len(w) == 3 and w not in _SHOUTED_SHORT:
            return w
        if not (_VOWELS & set(w)):
            return w
        # a word that starts a sentence keeps its initial capital
        pre = m.string[:m.start()].rstrip()
        if (not pre) or pre.endswith((".", "?", "!", ":", ";")):
            return w.capitalize()
        return w.lower()

    return _SINGLE_CAPS.sub(_fix, text)


def _sentence_case(text):
    """Capitals used as emphasis become sentence case. Papers do not shout.

    Only runs of THREE OR MORE consecutive all-caps words are touched, so `GRADE`, `REML`,
    `RoB 2`, an NCT id and a trial acronym are all left exactly as they are -- the emphasis
    was doing work that sentence structure should do, and a single capitalised name is not
    emphasis. ALLCAPS_SNAKE constants are values, not shouting, and are left alone.
    """
    def _fix(m):
        run = m.group(0)
        words = run.split()
        if all(w.strip(",;:") in _KEEP_CAPS or "_" in w for w in words):
            return run
        # ONLY CAPITALISE IF THE RUN STARTS A SENTENCE. Capitalising the first word of the
        # run unconditionally produced "A Disagreement rate is meaningless" -- the run began
        # mid-sentence after "A ", so the capital landed on a word that is not a sentence
        # start. Caught by a blind read from the other model family.
        _pre = m.string[:m.start()].rstrip()
        _starts_sentence = (not _pre) or _pre.endswith((".", "?", "!", ":", ";"))
        out = []
        for n, w in enumerate(words):
            bare = w.strip(",;:")
            if bare in _KEEP_CAPS or "_" in bare or re.match(r"^[A-Z]+\d", bare):
                out.append(w)
            else:
                out.append(w.capitalize() if (n == 0 and _starts_sentence) else w.lower())
        return " ".join(out)

    return _CAPS_RUN.sub(_fix, text)


# SENTENCES THAT NARRATE THE SENTENCE THE READER IS READING.
#
# "Everything in this paragraph is derived from stored fields and none of it is authored."
# A reader does not need to be told how the prose in front of them was made; that belongs
# once, in a note about the record, not inside the Introduction.
_SELF_NARRATION = re.compile(
    r"(?is)\s*(?:Everything (?:in this paragraph|above) is derived from stored fields[^.]*\.|"
    r"Nothing in it is authored\.|"
    r"Everything above is derived from stored fields and nothing in it is authored\.|"
    r"The interpretive sentences that follow are marked as drafts and are the author's to "
    r"replace\.)")


def _tidy(text, protect=()):
    if not isinstance(text, str):
        text = str(text)
    text = _SELF_NARRATION.sub(" ", text)
    if protect:
        _KEEP_CAPS.update(protect)
    try:
        return _lower_single_caps(_sentence_case(_flatten_container(text))).strip()
    finally:
        if protect:
            _KEEP_CAPS.difference_update(protect)


class Section(object):
    """A manuscript section, its text, and THE FIELDS IT WAS PROJECTED FROM.

    `fields` is not documentation. It is the section's licence to exist: a section is WRITTEN
    only if it lists at least one field that resolved, and every field it lists is checked to
    resolve before the section is emitted.
    """

    def __init__(self, key, heading):
        self.key = key
        self.heading = heading
        self.paras = []          # [(text, [field paths])]
        self.tables = []         # [(caption, [headers], [[cells]], [field paths])]
        self.figures = []        # [(n, caption, svg, refusal_reason, [field paths])]
        self.refusals = []       # [(what was not written, which field was absent)]

    def add(self, obj, text, fields):
        """Emit `text` only if EVERY field it cites resolves. Otherwise record the refusal."""
        missing = [f for f in fields if get(obj, f) is None]
        if missing:
            self.refusals.append((_tidy(text)[:70] + ("..." if len(text) > 70 else ""),
                                  missing))
            return False
        # EVERY PARAGRAPH IS TIDIED HERE, which is the whole point of doing it here.
        self.paras.append((_tidy(text), list(fields)))
        return True

    def add_table(self, obj, caption, headers, rows, fields):
        """A TABLE IS A PROJECTION TOO, and it obeys the same licence as a paragraph.

        Added 2026-08-20. Until now a projected manuscript could only emit prose, so
        per-trial characteristics, GRADE domain steps and risk-of-bias judgements -- all
        of which the objects hold, and all of which ARNI presents as tables -- had no way
        to reach the page at all. That is not a formatting limitation, it is 18 tables of
        substance the projector could not express.

        Refuses on the same terms as `add`: every field cited must resolve, and a table
        with no rows is a refusal rather than an empty frame with a caption on it.
        """
        missing = [f for f in fields if get(obj, f) is None]
        if missing:
            self.refusals.append((_tidy(caption), missing))
            return False
        if not rows:
            self.refusals.append((_tidy(caption) + " (no rows resolved)", list(fields)))
            return False

        # A TABLE CELL CAN HOLD A PARAGRAPH, AND FOUR OF THEM WERE STILL SHOUTING.
        #
        # `add` tidied every paragraph; `add_table` tidied nothing, so a cell carrying
        # "THREE TRIALS. NCT00761267's registered primary is ADVERSE EVENTS" reached the page
        # untouched -- and a reader does not know or care which method emitted the sentence
        # they are reading. Only cells long enough to be prose are tidied: a short cell is a
        # value, and verdict tokens are protected by name in _KEEP_CAPS above.
        caption = _tidy(caption)
        rows = [[(_tidy(c, _CELL_TOKENS) if isinstance(c, str) and len(c.split()) >= 6
                  else c) for c in row] for row in rows]

        # A ROW OF BLANKS IS WORSE THAN NO TABLE. Added 2026-08-21 as registry class 83.
        #
        # Sixteen rows across thirteen topics were reaching readers as a PMID and FOUR
        # EMPTY CELLS under the headers "Citation / Their k / Scope / How it differs from
        # ours". Every published comparison written during this run rendered that way,
        # because the appliers stored `title`/`journal`/`outcome_pooled`/`agreement` and
        # this projector read `citation`/`their_k`/`scope`/`how_it_differs_from_ours`. Two
        # vocabularies, never reconciled, because nobody opened the rendered table.
        #
        # An empty cell under a filled header ASSERTS that the comparison was made and has
        # nothing behind it -- strictly worse than the refusal the same section emits when
        # no comparison exists at all. So a row carrying content in at most one column is
        # dropped, and a table left with no surviving row refuses and names the reason.
        kept = [list(r) for r in rows
                if sum(1 for c in r if str(c if c is not None else "").strip()) > 1]
        if not kept:
            self.refusals.append(
                (caption + " -- EVERY ROW WAS BLANK EXCEPT FOR AN IDENTIFIER, so the table "
                          "is refused rather than drawn. An empty cell under a filled "
                          "header asserts a comparison that has nothing behind it",
                 list(fields)))
            return False
        if len(kept) < len(rows):
            self.paras.append(
                ("%d of %d rows of the table below carried content in one column only and "
                 "were dropped; a row of blanks under filled headers asserts more than the "
                 "object holds." % (len(rows) - len(kept), len(rows)), list(fields)))
        self.tables.append((caption, list(headers), kept, list(fields)))
        return True

    def add_figure(self, obj, caption, svg, fields, refusal=None):
        """A FIGURE IS A PROJECTION TOO, and a figure that cannot be drawn REFUSES IN PLACE.

        Added 2026-08-20, after Mahmood read SGLT2_HF's paper panel and said there was no
        forest plot. There was not, in the paper -- but there were THREE, on the Analysis
        tab of the same page, drawn by `projectors.forest_svg` from the same object. The
        manuscript projector could emit prose, tables and refusals and had no way to carry
        an image at all, so 1 delivered page out of 118 with a paper panel carried a figure
        and that one is ARNI, served by the docmodel renderer rather than by this one.

        TWO RULES, AND THE SECOND IS THE ONE THAT GETS DROPPED FOR EXPEDIENCE:

        1. A FIGURE CARRIES A NUMBER, A CAPTION AND ITS SOURCE FIELDS. The same licence a
           paragraph obeys: every field cited must resolve. A figure with no stated source
           is a picture, not evidence, and it is read with more trust than a sentence.

        2. A FIGURE THAT CANNOT BE DRAWN OCCUPIES ITS SLOT AND SAYS WHY. It does not
           vanish. A gap where a funnel plot should be reads to reviewers as an oversight;
           `k = 3, and a funnel has almost no power below about ten trials` reads as a
           decision. This is P47's principle -- a refusal is content -- applied to figures,
           and it is the reason `refusal` is a required argument in practice rather than a
           convenience: passing an empty `svg` with no reason stores a sentence saying so.

        THE DEGENERATE CASE IS EXCLUDED AT THE CALLER, NOT HERE. An outcome that exists but
        cannot be plotted gets a refusal figure; an object with no outcomes at all must gain
        NO figure, because a refusal figure for an outcome that does not exist would be
        manufacturing content -- the exact shape of the constructed-fixture defect (class
        58) read from the other direction.
        """
        missing = [f for f in fields if get(obj, f) is None]
        if missing:
            self.refusals.append((caption, missing))
            return False
        n = len(self.figures) + 1
        if svg:
            self.figures.append((n, caption, svg, None, list(fields)))
            return True
        self.figures.append((
            n, caption, "",
            refusal or ("not drawn, and NO REASON WAS RECORDED. That is the defect this "
                        "slot exists to prevent, reported rather than hidden as a gap."),
            list(fields)))
        return False

    @property
    def state(self):
        return WRITTEN if (self.paras or self.tables or self.figures) else REFUSED


def _fmt_ci(p):
    lo, hi = p.get("ci_low"), p.get("ci_high")
    return "%.4g (%.4g to %.4g)" % (p["point"], lo, hi) if lo is not None else "%.4g" % p["point"]


# ===========================================================================================
# THE PROSE LAYER. Three rules, each from a defect read off our own output beside ARNI's.
# ===========================================================================================

def outcome_text(obj, oid):
    """The REGISTERED outcome text, or None. NEVER the database key.

    RULE 1. Our Results section opened "For hfh_cvd_recurrent (k = 2), the pooled estimate
    was ..." -- the subject of the sentence was a dict key. ARNI's reads "The pooled hazard
    ratio was 0.872 ... favouring sacubitril/valsartan over enalapril."

    The registered text is held, on every one of these objects, at `outcomes[].name`:

        hfh_cvd_recurrent -> "Recurrent hospitalisations for heart failure together with
                              cardiovascular death, as a rate ratio"

    So this was never a content gap. It was a lookup nobody did, and the fallback
    `blk.get("outcome") or oid` made the omission invisible by always producing something.

    Returns None when the object holds no registered text, so the CALLER REFUSES the
    sentence and names the field. A subject that reads as an internal identifier is worse
    than an absent sentence: the reader cannot tell it is not the outcome's name.
    """
    for o in (obj.get("outcomes") or []):
        if isinstance(o, dict) and o.get("id") == oid:
            for key in ("name", "registered_text", "definition"):
                if o.get(key):
                    return str(o[key])
    return None



# WORDED ROW LABELS FOR THE SCREENING CASCADE. `k3_experimental` is a key; "Named the
# intervention rather than a comparator or background therapy" is what it means. A key
# absent from this map renders with underscores replaced -- degraded, not dropped, because
# a stage silently missing from the table would understate the screening.
_CASCADE_LABELS = {
    "k0_surfaced": "Records surfaced by the executed searches",
    "k1_deduplicated": "After removing duplicate registrations",
    "k2_role_located": "Records where the topic drug's role in the trial could be located",
    "k3_experimental": "Records where the topic drug is the randomised intervention",
    "k4_comparator": "Records where the topic drug is the comparator instead",
    "k5_background": "Records where the topic drug is background therapy in both arms",
    "kNA_not_assessable": "Records where the role could not be decided either way",
    "k_included_in_object": "Trials included in this review",
    "k_unscreened_remainder": "Surfaced records not yet screened",
    "k3_corrected_from": "Earlier value of the intervention count, before correction",
}



_GRADE_DOMAINS = {
    "risk_of_bias": "risk of bias",
    "publication_bias": "publication bias",
    "inconsistency": "inconsistency",
    "indirectness": "indirectness",
    "imprecision": "imprecision",
    "large_effect": "large effect",
    "dose_response": "dose-response",
    "confounding": "residual confounding",
}


def _grade_step_words(step):
    """One GRADE rating step as a sentence rather than as a dict repr.

    THIS WAS `str(x)` AND IT PUT `{'domain': 'risk_of_bias', 'levels': -1, 'from': 'HIGH',
    'to': 'MODERATE', 'reason': '...'}` ON A DELIVERED PAGE. Every value below is the same
    value; only the rendering changed. A step that is not a dict is returned as its own
    string rather than dropped -- an unrecognised shape must still reach the reader.
    """
    if not isinstance(step, dict):
        return str(step)
    dom = _GRADE_DOMAINS.get(step.get("domain"), str(step.get("domain") or "")
                             .replace("_", " "))
    lv = step.get("levels")
    frm, to = step.get("from"), step.get("to")
    bits = [dom] if dom else []
    if frm and to and frm != to:
        bits.append("%s to %s" % (frm, to))
    elif lv == 0 or lv == "0":
        bits.append("not rated down")
    if lv not in (None, 0, "0"):
        try:
            bits.append("down %d level(s)" % abs(int(lv)))
        except (TypeError, ValueError):
            bits.append("levels %s" % lv)
    txt = ": ".join([bits[0], ", ".join(bits[1:])]) if len(bits) > 1 else "".join(bits)
    reason = str(step.get("reason") or "").strip()
    if reason:
        txt = "%s -- %s" % (txt, reason)
    # EVERY OTHER KEY IS PRINTED TOO, AND THIS IS THE HALF THE FIRST VERSION GOT WRONG.
    # It handled domain, levels, from, to and reason, and SILENTLY DROPPED everything else.
    # On alirocumab-lipid one step carries `reason_superseded_2026_08_20`: "k = 8 and the
    # interval (-60.23 to -49.42) excludes the null." -- a sentence holding the pooled
    # interval, which vanished from the delivered page. A FORMATTER THAT KNOWS FIVE KEYS AND
    # DISCARDS THE REST IS NOT A FORMATTER, IT IS A FILTER, and the difference is invisible
    # until the sixth key exists.
    #
    # Caught by prove_register_change_moved_no_content, on the one page in the corpus where
    # such a key is present. The estimate invariant that looked pedantic is what found it.
    KNOWN = ("domain", "levels", "from", "to", "reason")
    extra = []
    for k, v in step.items():
        if k in KNOWN or v in (None, ""):
            continue
        extra.append("%s: %s" % (str(k).replace("_", " "), v))
    if extra:
        txt = "%s (%s)" % (txt, "; ".join(extra))
    return txt


_ROB_DOMAINS = {
    "D1": "randomisation process",
    "D2": "deviations from intended intervention",
    "D3": "missing outcome data",
    "D4": "measurement of the outcome",
    "D5": "selection of the reported result",
    "overall": "overall",
}

REFERRED_PREFIX = "THE_POOL_IS_REFERRED_"
# A SECOND PREFIX FOR FINDINGS THAT ARE NOT A REFERRAL AND NOT A BIAS DOMAIN.
# icosapent's registered primary is a MEDIAN percent change while the pool is a MEAN
# difference, and both its trials registered THREE arms where the object records two.
# Neither is a risk-of-bias domain and neither withdraws the pool -- but a reader who meets
# -25.84 should meet them, and the standing test for anything found tonight is: does it
# reach a reader, or does it exist for us.
FINDING_PREFIX = "POOL_FINDINGS_"


def pool_referral(blk):
    """The referral recorded on a pooled outcome, as a paragraph for the reader.

    TWO POOLS WERE REFERRED ON 2026-08-20 -- sglt2-mace-cvot-review, whose two trials count
    different stroke components and one of which registered a second co-primary this review
    silently dropped; and attr-pn-review, whose three rows put patisiran on both sides of
    one number. Both referrals were written onto the objects with their reasons. NO
    RENDERER NAMED THE KEY, so a reader met the estimate and none of it.

    THE REFERRAL EXISTED FOR US AND NOT FOR THEM -- registry class 65, on the very fields
    written in response to naming class 65. It renders BESIDE THE NUMBER for the same
    reason the estimand disclosure does: a disclosure a reader has to go looking for is the
    same defect one layer out.

    Returns (text, field paths) or (None, []). The key carries a date stamp, so this MATCHES
    ON THE PREFIX rather than on one day's spelling -- a renderer keyed to
    `THE_POOL_IS_REFERRED_2026_08_20` would go silent the next time a pool is referred.
    """
    # EVERY REFERRAL ON THIS POOL, NOT THE FIRST ONE ALPHABETICALLY.
    #
    # `attr-pn-review` was referred on 2026-08-20 for putting patisiran on both sides of one
    # number, and again on 2026-08-21 for two of its three contrasts sharing one external
    # placebo arm. Returning on the first match meant the SECOND referral -- written the same
    # night, onto the same pool, for a different defect -- reached no reader at all. A pool
    # can be wrong in more than one way, and the renderer that reports only the earliest one
    # is the same "exists for us and not for them" failure this function was written to fix.
    out, paths = [], []
    for key in sorted(blk):
        if not key.startswith(REFERRED_PREFIX):
            continue
        r = blk.get(key)
        if not isinstance(r, dict):
            continue
        bits = []
        state = str(r.get("state") or "REFERRED").strip()
        defect = str(r.get("primary_defect") or "").strip()
        what = str(r.get("what_is_wrong") or r.get("second_defect") or "").strip()
        obstacle = str(r.get("obstacle") or "").strip()
        bits.append("THIS POOL IS %s." % state)
        if defect:
            bits.append(defect if defect.endswith(".") else defect + ".")
        if what:
            bits.append(what)
        if obstacle:
            bits.append("The obstacle is %s." % obstacle.lower())
        not_withdrawn = str(r.get("not_withdrawn_because") or "").strip()
        if not_withdrawn:
            bits.append(not_withdrawn)
        out.append(" ".join(bits))
        paths.append("results.by_outcome.<this outcome>.%s" % key)
    if not out:
        return None, []
    return " ".join(out), paths


def pool_findings(blk):
    """Findings recorded on a pooled outcome that are neither a referral nor a bias domain.

    Same prefix-matching discipline as pool_referral, and the same reason for existing: a
    finding that lives only on the object is a finding that exists for us and not for the
    reader. Returns (text, field paths) or (None, []).
    """
    # EVERY DATED FINDINGS BLOCK, NOT THE FIRST. Same defect as pool_referral had: cangrelor
    # carries POOL_FINDINGS_2026_08_20 and a second block written 2026-08-21, and returning on
    # the first meant the newer one -- the missing measure, and the MI-definition cause --
    # reached no reader. Findings accumulate on a pool; a renderer that shows only the oldest
    # goes quieter the more is found.
    out, paths = [], []
    for key in sorted(blk):
        if not key.startswith(FINDING_PREFIX):
            continue
        f = blk.get(key)
        if not isinstance(f, dict):
            continue
        bits = []
        for k in sorted(f):
            v = str(f[k] or "").strip()
            if v:
                bits.append(v)
        if not bits:
            continue
        out.append(" ".join(bits))
        paths.append("results.by_outcome.<this outcome>.%s" % key)
    if not out:
        return None, []
    return "NOTED ON THIS POOL. " + " ".join(out), paths


def _outcome_words(obj, oid):
    """The outcome's registered name, falling back to the key made readable.

    NEVER SILENTLY EMPTY. A missing name degrades to the key with underscores replaced,
    which is worse prose and is still true; returning "" would delete the subject of the
    sentence.
    """
    for o in (obj.get("outcomes") or []):
        if isinstance(o, dict) and o.get("id") == oid:
            nm = (o.get("name") or "").strip()
            if nm:
                return _lc_first(nm)
    return oid.replace("_", " ")



def _phrase(value, max_words=14):
    """A value fit to drop into `X was {slot}`, or None if it is prose.

    THE CLASS THIS FIXES. A template reading `eligibility was {field}` was handed a paragraph
    that itself begins "ELIGIBILITY turns on population, intervention and comparator: ..." and
    produced, live on the page:

        "eligibility was ELIGIBILITY turns on population, intervention and comparator: a trial
         is in scope if it randomised adults with CHRONIC heart failure ... because section
         3.2.4 cautions that making e;"

    -- the slot's own name repeated, a whole paragraph inside a clause, and a cut mid-word at
    300 characters. Three defects in one sentence, and none of them is specific to eligibility.

    THE RULE: A SLOT TAKES A PHRASE; PROSE GETS ITS OWN SENTENCE. This returns the value only
    when it is genuinely phrase-like -- short, one sentence, not opening with a shouted field
    name. Otherwise the caller drops the template and lets the field's own sentence stand.
    """
    if value is None:
        return None
    t = _v_str(value).strip()
    if not t:
        return None
    # a paragraph, or several sentences, is not a phrase
    if "\n" in t or t.count(". ") >= 1:
        return None
    if len(t.split()) > max_words:
        return None
    # a value opening with its own field name in capitals is a field, not a phrase
    if re.match(r"^[A-Z]{4,}[A-Z_ ]*\b", t):
        return None
    return t.rstrip(". ")


def _own_sentence(value, limit=600):
    """The field's own prose, cut at a SENTENCE boundary and never mid-word."""
    t = _v_str(value).strip()
    if not t:
        return None
    t = re.sub(r"\s+", " ", t)
    if len(t) <= limit:
        return t if t.endswith((".", "?", "!")) else t + "."
    cut = t[:limit]
    # back off to the last sentence end; if there is none, to the last whole word
    m = list(re.finditer(r"[.!?]\s", cut))
    if m:
        return cut[:m[-1].end()].strip()
    return cut.rsplit(" ", 1)[0].rstrip(",;:") + " ..."


def _model_words(model):
    """`random` and `fixed` are half a name. The page read "pooled under random"."""
    t = (_v_str(model) or "").strip()
    low = t.lower()
    if low in ("random", "random effects", "randomeffects"):
        return "a random-effects model"
    if low in ("fixed", "fixed effect", "fixed effects", "common", "common effect"):
        return "a fixed-effect model"
    if low.startswith("random-effects") or low.startswith("fixed-effect"):
        return "a " + t if not t.lower().startswith("a ") else t
    return t


def _live_certainty(obj):
    """The GRADE rating, from the GRADE record, over outcomes the review actually publishes.

    THE ABSTRACT PUBLISHED "certainty of the evidence was high" WHILE GRADE HELD LOW. It read
    `results.by_outcome.<first key>.grade.certainty`, which on sglt2-hf is a stale block on the
    WITHDRAWN outcome reading "start high; no downgrades". Two defects at once: the wrong field,
    and selecting the first outcome in KEY ORDER without asking whether it is one the review
    publishes. Either alone was enough to put a wrong rating in front of a reader.
    """
    res = (obj.get("results") or {}).get("by_outcome") or {}
    grade = ((obj.get("grade") or {}).get("by_outcome") or {})
    vals = []
    for oid, g in sorted(grade.items()):
        if not isinstance(g, dict) or not g.get("certainty"):
            continue
        pooled = (res.get(oid) or {}).get("pooled")
        if not isinstance(pooled, dict) or pooled.get("point") is None or pooled.get("withdrawn"):
            continue
        vals.append(str(g["certainty"]).replace("_", " ").lower())
    if not vals:
        return None
    uniq = sorted(set(vals))
    if len(uniq) == 1:
        return uniq[0]
    return "%s across the pooled outcomes" % _and_list(uniq)



def _lc_first(nm):
    """Lower-case an initial capital ONLY where it is an ordinary capitalised word.

    `nm[0].lower() + nm[1:]` turned the outcome "HIV-1 seroconversion" into "hIV-1
    seroconversion" on a delivered page. An acronym's first letter is not a sentence capital,
    and the test for the difference is the SECOND character: `Cardiovascular` lowers, `HIV`
    and `LDL` do not.
    """
    nm = str(nm or "")
    if len(nm) < 2 or not nm[0].isupper():
        return nm
    if nm[1].isupper():
        return nm
    return nm[0].lower() + nm[1:]



# ---------------------------------------------------------------------------------------
# DID A POOL ACTUALLY HAPPEN? One predicate, consulted by every surface that speaks about it.
# ---------------------------------------------------------------------------------------

_NULL_MARKERS = {"", "none", "not applicable", "n/a", "na", "not recorded", "unknown",
                 "not stated", "null", "nan", "-", "--"}


def _is_value(v):
    """A field that resolves is not the same as a field that holds a value.

    `estimator_used` holds the STRING "not applicable" on the not-poolable pages, so every
    path-resolves check passed and the manuscript announced "the not applicable estimator".
    A PATH THAT RESOLVES TO A NULL-MARKER IS NOT A BACKED CLAIM.
    """
    if v is None:
        return False
    if isinstance(v, str):
        return v.strip().lower() not in _NULL_MARKERS
    return True


def _pool_occurred(blk):
    """True only where this outcome carries a pooled estimate a reader can see.

    Not "is there a model field". Not "does the estimator path resolve". The question every
    sentence about pooling depends on is whether a pool was performed and published, and that
    is answered by the pooled point itself.
    """
    if not isinstance(blk, dict):
        return False
    p = blk.get("pooled")
    if not isinstance(p, dict):
        return False
    return p.get("point") is not None and not p.get("withdrawn")


def _any_pool_occurred(obj):
    return any(_pool_occurred(b)
               for b in ((obj.get("results") or {}).get("by_outcome") or {}).values())


def _i2_words(i2):
    """A plain-English band for I-squared. Handbook 10.10.2 gives overlapping ranges and
    warns against a mechanical reading, so the words are DELIBERATELY loose and the number
    is always printed beside them. This describes; it does not grade."""
    try:
        v = float(i2)
    except (TypeError, ValueError):
        return "of unstated"
    if v < 30:
        return "closely"
    if v < 60:
        return "moderately"
    if v < 75:
        return "loosely"
    return "poorly"

def disp(x, sig=3):
    """A number at DISPLAY precision, for prose only.

    RULE 2. Our prose printed 0.8066 where ARNI's prints 0.872. That is not a different
    convention, it is storage precision reaching the page: ARNI's OBJECT holds
    0.87153524291 and its manuscript rounds it, which is what a paper does.

    THIS DOES NOT CONFLICT WITH THE FOUR-SIGNIFICANT-FIGURE RULE in build_tabbed, and the
    distinction matters because that rule exists for a real defect. That rule governs the
    POOLED RESULT CARD, where the displayed number must equal the verified number or the
    three-surface check fails. This governs PROSE, where the exact value is carried
    verbatim two sections away under "Statistical output, quoted verbatim". ARNI's
    delivered page already carries both precisions, on the same page, today.
    """
    if x is None:
        return None
    try:
        f = float(x)
    except (TypeError, ValueError):
        return str(x)
    if f == int(f) and abs(f) < 1e6:
        return str(int(f))
    return "%.*g" % (sig, f)


def strip_measure_suffix(name, measure):
    """Drop a trailing ", as a <measure>" from a registered outcome name.

    THE OBJECTS NAME THEIR OUTCOMES WITH THE MEASURE INSIDE THE NAME:

        "Recurrent hospitalisations for heart failure together with cardiovascular death,
         as a rate ratio"

    so a sentence that leads with the measure -- which is what a paper does -- says it
    twice: "The pooled rate ratio for recurrent hospitalisations ..., as a rate ratio was
    0.807". This removes the duplicate ONLY when the trailing clause names the SAME measure
    already being stated. It removes nothing otherwise, and it never removes anything that
    is not a trailing measure clause.

    This is a de-duplication, not an edit of the field: the full registered text is still
    what is matched against, and where the two disagree the name is left untouched, because
    a name that says "as a hazard ratio" beside a rate-ratio estimate is a FINDING, not a
    formatting problem.
    """
    if not name or not measure:
        return name
    words = measure_words(measure)
    for tail in (", as an %s" % words, ", as a %s" % words):
        if name.lower().endswith(tail.lower()):
            return name[: -len(tail)]
    return name


def ci_prose(p, sig=3):
    """`0.872 (0.746 to 1.02)` -- the form a reader expects, at display precision."""
    pt = disp(p.get("point"), sig)
    lo, hi = disp(p.get("ci_low"), sig), disp(p.get("ci_high"), sig)
    return "%s (%s to %s)" % (pt, lo, hi) if lo is not None else str(pt)


MEASURE_WORDS = {"HR": "hazard ratio", "RR": "risk ratio", "OR": "odds ratio",
                 "RATE_RATIO": "rate ratio", "IRR": "incidence rate ratio",
                 "MD": "mean difference", "SMD": "standardised mean difference",
                 "LSMD": "least-squares mean difference", "RD": "risk difference"}


def measure_words(measure):
    """`HR` -> `hazard ratio`. A manuscript does not print an enum.

    The first prose pass rendered "the pooled hr was 0.796" -- lower-casing an abbreviation
    is not the same as expanding it, and it reads as a typing error rather than a measure.
    An unmapped code is returned unchanged rather than mangled: a code we do not know is
    better shown as it is stored than guessed at.
    """
    if not measure:
        return "estimate"
    key = str(measure).strip().upper()
    if key in MEASURE_WORDS:
        return MEASURE_WORDS[key]
    return str(measure).replace("_", " ").lower() if "_" in str(measure) else str(measure)


def _arms_text(value):
    """The Arms cell, formatted -- because `str()` of a list of dicts is a Python repr.

    This cell was `str(t.get("comparison") or t.get("arms") or "")`, so a reader received

        [{&#x27;label&#x27;: &#x27;colchicine 0.5 mg once daily&#x27;, &#x27;role&#x27;: ...

    on 189 trial rows across 62 topics -- 22 of the pages clean of it before the sixteen
    new sections were projected into them. It is the same family as the `None` the push
    gate caught, and the gate cannot see it, because a repr contains no bare None.

    WRITTEN AGAINST EVERY SHAPE IN THE CORPUS, NOT THE ONE I FIRST LOOKED AT. Enumerated:
    218 rows null, 117 `label/role/events/participants`, 23 empty lists, and eleven further
    key sets carrying extras (`registry_label`, `label_corrected`, `regimen`,
    `pcr_corrected_cure_percent`, ...). All of them share `label` and `role`; the rest are
    per-topic. A formatter built from one instance encodes that instance's shape.

    NOTHING IS SILENTLY DROPPED. Keys beyond the three rendered are COUNTED and the count
    is stated in the cell, because some of them carry corrections that contradict the label
    beside them -- `label_corrected: "LABELS SWAPPED, ARITHMETIC CORRECT"` is one. A reader
    who cannot see that a field exists cannot ask for it.
    """
    if value is None:
        return "not recorded on this object"
    if isinstance(value, str):
        return value
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, dict):
        value = [value]
    if not isinstance(value, list):
        # Never a repr. An unformattable shape is named, so it can be fixed.
        return "NOT_ASSESSABLE -- arms recorded in an unrecognised shape (%s)" \
            % type(value).__name__
    if not value:
        # An empty list is an ABSENCE and is reported as one. `[]` on a page is a Python
        # object standing where a statement belongs.
        return "not recorded on this object"
    IDENT = ("label", "name", "role", "participants", "randomised")
    rendered, counted, notes = [], 0, []
    for arm in value:
        if not isinstance(arm, dict):
            rendered.append(str(arm))
            continue
        label = str(arm.get("label") or arm.get("name") or "").strip()
        role = str(arm.get("role") or "").strip()
        n = arm.get("participants")
        if n is None:
            n = arm.get("randomised")
        bits = []
        if role:
            bits.append(role)
        if n is not None:
            bits.append("n=%s" % (int(n) if isinstance(n, float) and n.is_integer() else n))
        piece = label or "unlabelled arm"
        if bits:
            piece += " (%s)" % ", ".join(bits)
        rendered.append(piece)
        # A NOTE IS NOT AN EXTRA FIELD. The first version of this counted everything
        # outside IDENT, which on doac-af-review reduced 8470 characters to the phrase
        # "[+8 further fields recorded on the object]" -- and among those eight was
        # `label_corrected_because: "registry arm size 6076 is the dabigatran 150 mg
        # group"`. A correction note is a FINDING in this corpus, not metadata, and
        # replacing a finding with a count of findings is the shape this project audits
        # for. It was unreadable inside a repr before; counted is not better enough.
        #
        # THE TEST IS STRUCTURAL, NOT A KEYWORD LIST. Prose is prose whatever the field
        # is called, and a keyword list would only ever catch the names already seen --
        # `label_corrected_because`, `registry_role_contradiction_note`,
        # `head_to_head_role_note` were all invented one at a time. A string value over
        # 40 characters in a data cell is a sentence somebody wrote to be read.
        for k in sorted(arm):
            if k in IDENT:
                continue
            v = arm.get(k)
            if isinstance(v, str) and len(v.strip()) > 40:
                notes.append("%s (%s): %s" % (label or "arm", k, v.strip()))
            else:
                counted += 1
    out = " vs ".join(rendered)
    if counted:
        out += "  [+%d further field%s recorded on the object]" % (
            counted, "" if counted == 1 else "s")
    for note in notes:
        out += "  " + note
    return out


def _trials_by_identity(obj):
    """{registration id -> trial record}. IDENTITY, NEVER POSITION.

    A record with no resolvable id is returned in a separate list rather than dropped or
    positionally paired -- an unjoinable record is a reportable state, not a silent one.
    """
    by_id, unjoinable = {}, []
    for t in ((obj.get("inputs") or {}).get("trials") or []):
        ident = t.get("nct") or t.get("id")
        if not ident:
            unjoinable.append(t.get("name") or "(unnamed record)")
            continue
        by_id[ident] = t
    return by_id, unjoinable


def project(obj, journal="generic", length="standard"):
    """Return [Section]. `journal` and `length` are parameters; neither licenses a claim."""
    we = journal in ("cochrane", "plos")
    verb = "We searched" if we else "Searches were executed in"
    secs = []

    # ---- TITLE / QUESTION -------------------------------------------------------------
    s = Section("title", "Title and review question")
    _title, _question = get(obj, "title") or "", get(obj, "question") or ""
    s.add(obj, _title, ["title"])
    # A POINTER TO ANOTHER REVIEW, AT THE TOP, WHERE A READER ARRIVES.
    #
    # `malaria-vaccine` is NOT POOLABLE and `malaria-vaccines` pools the same two vaccines, and
    # read side by side without this the two pages contradict each other. They do not -- they
    # ask different questions -- but a reader cannot know that from either page alone, and a
    # pointer buried in the back matter is one nobody meets. Nothing is withdrawn by it.
    for _pk in sorted(k for k in obj if str(k).startswith("pointer_to_another_review")):
        if isinstance(obj[_pk], str) and obj[_pk].strip():
            s.add(obj, obj[_pk].strip(), [_pk])
    # CORRECTIONS AND WITHDRAWALS, AT THE TOP, WHERE A READER ARRIVES.
    #
    # A claim found false is withdrawn IN PLACE with what it said and what is true. That is
    # worth nothing if the withdrawal renders somewhere a reader never reaches -- the same
    # defect as a referral that exists for us and not for them. Matched on prefixes so the
    # next correction is not keyed to one day's spelling.
    for _ck in sorted(k for k in obj
                      if str(k).startswith(("CLAIM_WITHDRAWN", "ACRONYMS_CORRECTED",
                                            "POPULATION_LABEL_WITHDRAWN", "SCOPE_CORRECTED",
                                            "REGISTRATION_DISCREPANCY"))):
        if isinstance(obj[_ck], str) and obj[_ck].strip():
            s.add(obj, obj[_ck].strip(), [_ck])
    if _question and _question == _title:
        # THE OBJECT RECORDS THE SAME STRING TWICE, on 10 topics. Printing it twice is not
        # a manuscript, and silently printing it once hides that the review's QUESTION is
        # a copy of its TITLE -- which is the defect `lint_question_is_a_question.py`
        # exists for. Say which it is.
        s.add(obj, "This object records its review question and its title as the SAME "
                   "string, so no question distinct from the title is stated here. A "
                   "question copied from a title has not been asked.", ["question"])
    else:
        s.add(obj, _question, ["question"])
    secs.append(s)

    # ---- METHODS: SEARCH --------------------------------------------------------------
    s = Section("methods_search", "Methods — search")
    dbs = get(obj, "search.databases") or []
    for i, d in enumerate(dbs):
        q = d.get("query_as_executed")
        if not q:
            s.refusals.append(("a search entry with no executed query",
                               ["search.databases[%d].query_as_executed" % i]))
            continue
        # A DEFAULT A PRESENT-BUT-NULL KEY CAN NEVER REACH (registry class 39). These three
        # defaults are careful, deliberate fallbacks -- "an unrecorded number of" reads
        # correctly in the sentence around it -- and `dict.get`'s default applies only to a
        # MISSING key, never to one present with a null value. Six topics hold
        # `records_returned: null` and SEVEN DELIVERED PAGES read "It returned None
        # record(s)." The care was real; the construct defeated it, and no gate sees it,
        # because the leak detector matches None in a value slot or at the end of a URL and
        # this one is mid-sentence.
        #
        # `or` WOULD BE WRONG HERE. A search returning 0 records is a real and important
        # result -- it is how a query that missed is recorded -- and `0 or default` would
        # replace it with the absence phrase. The test is `is None`, not falsiness.
        def _dflt(key, fallback):
            v = d.get(key)
            return fallback if v is None else v
        txt = ("%s %s on %s with the query, verbatim: %s. It returned %s record(s)."
               % (verb, _dflt("database", "an unnamed source"),
                  _dflt("date_executed", "(no date recorded)"),
                  q, _dflt("records_returned", "an unrecorded number of")))
        # A QUERY THAT MISSED AN INCLUDED TRIAL IS PART OF THE METHODS, NOT AN EMBARRASSMENT
        # TO OMIT. The object records it; the manuscript states it.
        if d.get("DEFECT_FOUND"):
            txt += " " + d["DEFECT_FOUND"]
        s.paras.append((txt, ["search.databases[%d]" % i]))
    if not dbs:
        s.refusals.append(("the entire search description", ["search.databases"]))
    # AFTER the refusal decision, never before it. Placed at the top of the
    # section this line made `s.paras` non-empty, the `if not (s.paras or
    # s.tables)` refusal stopped firing, and six topics lost a refusal that was
    # true -- delivery 26 -> 20. A bookkeeping claim belongs in the section; it
    # must not be the thing that decides the section has content.
    _add_bookkeeping(s, obj, "the_search_its_date_and_its_databases")
    secs.append(s)

    # ---- METHODS: ELIGIBILITY ---------------------------------------------------------
    s = Section("methods_eligibility", "Methods — eligibility criteria")
    # THE CRITERIA BLOCK IS A STRING ON SOME OBJECTS AND A MAPPING ON OTHERS. The first version
    # of this projector handled only the mapping and refused sglt2-hf's criteria as ABSENT --
    # a refusal that would have been read as a gap in the OBJECT when it was a gap in the
    # PROJECTOR. Caught by reading the output against the object rather than trusting the
    # refusal, which is the only reason a refusing instrument is safe to build.
    elig = get(obj, "screening.eligibility")
    if isinstance(elig, str):
        s.paras.append((elig, ["screening.eligibility"]))
    elif isinstance(elig, dict):
        for k, v in elig.items():
            if isinstance(v, str) and v.strip():
                s.paras.append(("%s: %s" % (k.replace("_", " ").capitalize(), v),
                                ["screening.eligibility.%s" % k]))
    if not s.paras:
        s.refusals.append(("the eligibility criteria", ["screening.eligibility"]))
    prov = get(obj, "screening.eligibility_provenance")
    if prov:
        s.paras.append(("Each criterion above is recorded with the source it was derived from "
                        "in `screening.eligibility_provenance`; none is asserted here without "
                        "one.", ["screening.eligibility_provenance"]))
    secs.append(s)

    # ---- METHODS: FLOW ----------------------------------------------------------------
    # PLAIN ENGLISH, NO BARE `k`. The heading read "Methods -- study flow and k at every
    # stage": a single-letter symbol in an article heading reads as code whatever the section
    # beneath it says, and it is the only heading in the sequence that carried one.
    s = Section("methods_flow", "Methods — how many studies at each stage")
    kc = get(obj, "k_cascade") or {}
    if kc:
        # A TABLE, NOT A SENTENCE. This was `key.replace("_", " ")` joined with semicolons,
        # which produced "k0 surfaced 56; k2 role located 56; k3 experimental 49; k4
        # comparator 1; k5 background 6; kNA not assessable 0" -- a table flattened into
        # prose, and the single worst section of the SGLT2 page a reader called computer
        # code. EVERY COUNT BELOW IS THE SAME NUMBER; only the rendering changed. A key
        # with no worded label keeps its raw form rather than being silently dropped.
        rows = [[_CASCADE_LABELS.get(k, k.replace("_", " ")), str(v)]
                for k, v in kc.items() if isinstance(v, int)]
        s.tables.append((
            "Records at every stage of screening. k is reported at each stage rather than "
            "as a single number, because each stage is what the instrument at that stage "
            "could actually decide.",
            ["Stage", "Records"], rows, ["k_cascade"]))
    else:
        s.refusals.append(("the k cascade", ["k_cascade"]))
    if get(obj, "prisma_flow"):
        s.paras.append(("The PRISMA 2020 flow counts are recorded in `prisma_flow` and "
                        "reconcile with the executed searches above.", ["prisma_flow"]))
    rem = kc.get("k_unscreened_remainder")
    if rem is not None:
        s.paras.append(("The unscreened remainder is %d." % rem,
                        ["k_cascade.k_unscreened_remainder"]))
    secs.append(s)

    # ---- METHODS: THE WITHHOLDING QUESTION --------------------------------------------
    s = Section("methods_withholding", "Methods — outcomes sought at every registered rank")
    wq = get(obj, "withholding_question")
    if isinstance(wq, dict) and wq.get("question"):
        txt = ("Before deciding which outcomes could be combined, every trial was read at "
               "every registered rank -- primary, secondary and other -- asking: %s"
               % wq["question"])
        for extra in ("why_before_deciding", "answer",
                      "why_the_answer_is_decisive_rather_than_unexamined",
                      "why_this_check_is_a_check_and_not_a_bias"):
            if wq.get(extra):
                txt += " " + str(wq[extra])
        s.paras.append((txt, ["withholding_question.question",
                              "withholding_question.why_before_deciding"]))
    else:
        # THE SAME LESSON AS `screening.eligibility` BEING A STRING HERE AND A MAPPING THERE.
        # Only sglt2-hf carries a prose `withholding_question` block; the ablation reviews and
        # iv-iron record the same fact PER TRIAL as `all_ranks_read_utc` plus the secondary and
        # other ranks they read. Refusing on the absence of one field name would have printed
        # "no evidence ranks below the primary were read" about objects that read every rank
        # and stamped the time they did it -- a refusal that reads as a finding about the
        # REVIEW when it is a finding about the PROJECTOR.
        by_id_r, _ = _trials_by_identity(obj)
        stamped = [i for i, t in by_id_r.items() if t.get("all_ranks_read_utc")]
        if stamped:
            s.paras.append(("Every registered rank -- primary, secondary and other -- was read "
                            "for %d of %d contributing trials before any decision about which "
                            "outcomes could be combined; each records the time it was read."
                            % (len(stamped), len(by_id_r)),
                            ["inputs.trials[].all_ranks_read_utc"]))
        else:
            s.refusals.append(("the statement that outcomes were sought below the primary",
                               ["withholding_question", "inputs.trials[].all_ranks_read_utc"]))
    secs.append(s)

    # ---- METHODS: SYNTHESIS -----------------------------------------------------------
    # EVERY CLAIM HERE IS READ FROM THE OUTCOME BLOCK THAT USED IT. No default estimator, no
    # default risk-of-bias tool, no assertion of duplicate screening, no assertion of
    # prespecification. If the object does not record it, this section does not say it.
    s = Section("methods_synthesis", "Methods — synthesis")
    for oid, blk in (get(obj, "results.by_outcome") or {}).items():
        model, est = blk.get("model"), blk.get("estimator_used") or blk.get("estimator")
        # THE SAME PREDICATE THE ABSTRACT NOW USES. This section already refused where the
        # fields were absent; it still asserted where they held a NULL-MARKER, which is how
        # "a random-effects model was fitted with the not applicable estimator" reached a page
        # whose own title says NOT POOLABLE.
        if _pool_occurred(blk) and _is_value(model) and _is_value(est):
            # THE OUTCOME'S NAME, NOT ITS KEY. This read "For cvdeath_or_whf_first, a random
            # model was fitted" -- a database key as the subject of an English sentence. The
            # key is still reachable: it is in this paragraph's source list.
            s.paras.append(("For %s, a %s model was fitted with the %s estimator."
                            % (_outcome_words(obj, oid), model, est),
                            ["results.by_outcome.%s.model" % oid,
                             "results.by_outcome.%s.estimator_used" % oid]))
        else:
            _why = ("no pooled estimate was produced for this outcome, so no model was "
                    "fitted and none is described"
                    if not _pool_occurred(blk) else
                    "the model or estimator is recorded as a null marker rather than a value")
            s.refusals.append(("the model/estimator sentence for %s -- %s"
                               % (_outcome_words(obj, oid), _why),
                               [p for p, v in (("results.by_outcome.%s.model" % oid, model),
                                               ("results.by_outcome.%s.estimator_used" % oid,
                                                est))
                                if not _is_value(v)]
                               or ["results.by_outcome.%s.pooled.point" % oid]))
    cl = get(obj, "config.confidence_level")
    if cl:
        s.paras.append(("Intervals are %s%% confidence intervals." % cl,
                        ["config.confidence_level"]))
    ma = get(obj, "methodological_authority")
    if isinstance(ma, dict) and ma.get("reference"):
        s.paras.append(("Methodological decisions follow %s%s, and the sections relied on are "
                        "listed in the object rather than cited generically."
                        % (ma["reference"],
                           (", version %s" % ma["version"]) if ma.get("version") else ""),
                        ["methodological_authority.reference"]))
    # DUPLICATE SCREENING -- stated only in the form that is true.
    ds = get(obj, "screening.duplicate_screening")
    if isinstance(ds, dict) and ds.get("performed"):
        fams = ", ".join("%s (%s)" % kv for kv in sorted((ds.get("families") or {}).items()))
        txt = ("Records were screened in duplicate by TWO INDEPENDENT MODEL FAMILIES -- %s -- "
               "each blind to the other's answers. %s records were read by both."
               % (fams, ds.get("records_read_by_both")))
        if ds.get("code_agreement_pct") is not None:
            txt += (" Agreement was %.4g%% on the code and %.4g%% on the disposition, over the "
                    "vocabulary recorded with the rate."
                    % (float(ds["code_agreement_pct"]), float(ds["disposition_agreement_pct"])))
        if ds.get("records_read_by_one_only_NOT_adjudicated"):
            txt += (" %s records were read by ONE seat only and are reported as single-read, "
                    "not as agreement." % ds["records_read_by_one_only_NOT_adjudicated"])
        txt += " " + ds["reviewers_are_not_people"]
        txt += " Disagreements: " + ds["disagreement_resolution"]
        s.paras.append((txt, ["screening.duplicate_screening"]))
    elif isinstance(ds, dict):
        s.refusals.append(("the claim that records were screened in duplicate -- and this "
                           "topic OWES one rather than merely lacking one: " + ds.get("why", ""),
                           ["screening.duplicate_screening.performed"]))
    else:
        s.refusals.append(("the claim that records were screened in duplicate by two "
                           "independent reviewers", ["screening.duplicate_screening"]))

    # RISK OF BIAS -- the tool, the unit, and the default rule that keeps it honest.
    rb = get(obj, "risk_of_bias")
    if isinstance(rb, dict) and rb.get("tool"):
        n = sum(len(v) for v in (rb.get("by_outcome") or {}).values())
        s.paras.append(("Risk of bias was assessed with %s (%s), following %s. %s %d "
                        "result-level assessments were made. %s"
                        % (rb["tool"], rb.get("version", ""), rb.get("handbook", ""),
                           rb.get("unit_of_assessment", ""), n, rb.get("default_rule", "")),
                        ["risk_of_bias.tool", "risk_of_bias.by_outcome"]))
        # THE CEILING IS STATED ONCE, IN THE RISK-OF-BIAS SECTION.
        #
        # It used to be emitted here as well, and once a dedicated `risk_of_bias` section
        # existed the SAME 300-CHARACTER PARAGRAPH APPEARED TWICE in the manuscript, on
        # every object that records a ceiling. Neither site was wrong on its own; the
        # duplication only came into being when the second section was added, which is why
        # it was invisible to whoever wrote either one.
        #
        # Caught by a test asserting that no long paragraph is emitted more than once --
        # not by reading, and not by any check that looks at one section at a time.
        # Methods points at the assessment; the assessment states the bound.
        ceil = rb.get("ceiling") or {}
        if ceil.get("statement"):
            s.paras.append(("A ceiling applies to every risk-of-bias judgement in this "
                            "review; it is stated with the assessment itself rather than "
                            "summarised here.", ["risk_of_bias.ceiling"]))
    else:
        s.refusals.append(("the claim that risk of bias was assessed with a named tool",
                           ["risk_of_bias.tool"]))

    # GRADE -- rated only where a pool exists.
    gr = get(obj, "grade")
    if isinstance(gr, dict) and gr.get("approach"):
        rated = [o for o, v in (gr.get("by_outcome") or {}).items() if v.get("rated")]
        notr = [o for o, v in (gr.get("by_outcome") or {}).items() if not v.get("rated")]
        txt = ("Certainty of evidence was rated with %s, following %s. %s %d pooled outcome(s) "
               "were rated. %s" % (gr["approach"], gr.get("handbook_chapter", ""),
                                   gr.get("starting_point", ""), len(rated),
                                   gr.get("not_rated_up", "")))
        if notr:
            txt += (" %d outcome(s) were NOT rated because their pool is declined or "
                    "withdrawn: there is no effect estimate to rate the certainty of, and "
                    "rating one would be certainty about a number this review refused to "
                    "publish." % len(notr))
        s.paras.append((txt, ["grade.approach", "grade.by_outcome"]))
    else:
        # A GRADE RATING CAN LIVE PER POOLED OUTCOME AND NOT AT THE OBJECT ROOT, and this
        # branch used to REFUSE in that case -- publishing "Refused: the claim that
        # certainty of evidence was graded" on a page whose object holds three ratings.
        #
        # THAT IS A FALSE REFUSAL, WHICH IS WORSE THAN A MISSING ONE. A blank slot is
        # visibly empty; a refusal is a positive statement, and this one said something
        # untrue about its own object. Found on sotagliflozin-hf on 2026-08-20; measured
        # across 155 objects it is the only topic that holds GRADE in that shape alone,
        # so the fix reaches one page -- and the class reaches every projector branch that
        # looks in ONE place and then reports an absence.
        per = []
        for oid, blk in (get(obj, "results.by_outcome") or {}).items():
            g2 = blk.get("grade") if isinstance(blk, dict) else None
            if isinstance(g2, dict) and g2.get("certainty"):
                per.append((oid, g2))
        if per:
            s.paras.append((
                "Certainty of evidence was rated per pooled outcome rather than in a single "
                "review-level block, and %d outcome(s) carry a rating: %s. Each rating is "
                "about its own estimand and about nothing else. %s"
                # THE OUTCOME'S NAME, NOT ITS IDENTIFIER. This read "3 outcome(s) carry a
                # rating: hfcv_total LOW; hfcv_first LOW" -- schema keys in a sentence about
                # certainty. Where the object stores no name the identifier is shown AND
                # named as unlabelled, because a missing label is a missing field.
                % (len(per), "; ".join(
                    "%s %s" % (_outcome_label(obj, o)
                               or ("the outcome recorded as %s, for which this object stores "
                                   "no name" % o),
                               str(g2.get("certainty")).upper())
                    for o, g2 in per),
                   next((str(g2.get("what_this_certainty_is_about")) for _, g2 in per
                         if g2.get("what_this_certainty_is_about")), "")),
                ["results.by_outcome.%s.grade" % o for o, _ in per]))
        else:
            s.refusals.append(("the claim that certainty of evidence was graded",
                               ["grade.approach"]))

    # PRESPECIFICATION -- REFUSED PERMANENTLY, AND THE REFUSAL IS THE STATEMENT.
    pp = get(obj, "protocol")
    if isinstance(pp, dict) and pp.get("permanently_refused"):
        s.refusals.append(("the claim that the review methods were prespecified before data "
                           "collection. THIS REFUSAL IS PERMANENT AND IS NOT A GAP TO BE "
                           "FILLED. " + pp["why"] + " " + pp["what_was_actually_done"] + " "
                           + pp["authority_permitting_it"],
                           ["protocol.prespecified = false (declared, not missing)"]))
    else:
        s.refusals.append(("the claim that the review methods were prespecified before data "
                           "collection", ["protocol.prespecified"]))
    secs.append(s)

    # ---- RESULTS ----------------------------------------------------------------------
    # THE ESTIMAND REASONING TRAVELS WITH THE NUMBERS. This topic publishes two pools over
    # DIFFERENT composites and declines a third; reporting the estimates without the reason
    # they are separate would misrepresent the object they were projected from.
    s = Section("results", "Results")
    by_id, unjoinable = _trials_by_identity(obj)
    if unjoinable:
        s.paras.append(("%d contributing record(s) could not be joined by registration "
                        "identity and are reported rather than positionally matched: %s."
                        % (len(unjoinable), "; ".join(unjoinable)), ["inputs.trials"]))
    reported, declined = [], []
    for oid, blk in (get(obj, "results.by_outcome") or {}).items():
        p = blk.get("pooled") or {}
        (declined if (p.get("withdrawn") or p.get("point") is None) else reported).append((oid, blk))

    if not reported and not declined:
        s.refusals.append(("the entire results section", ["results.by_outcome"]))
    _het_caveats_said = {}                 # caveat text -> the outcome that first stated it
    _grounds_said = {}                     # poolable_reason text -> already stated
    # PROSE, NOT A RECORD. What changed here, and why each change is a projection and not
    # an invention:
    #
    #   the SUBJECT is the registered outcome text (`outcomes[].name`), never the dict key
    #   NUMBERS are at display precision; the exact values are quoted two sections away
    #   NO SENTENCE ADDRESSES A MAINTAINER -- "stored verbatim on the object rather than
    #     re-typed here" is a note to us, and it was in the manuscript
    #   THE REASONING FIELDS ARE THE ARGUMENT, not a list appended after the numbers.
    #     `heterogeneity_status` on these objects already says what ARNI's manuscript says
    #     in prose -- that Q on one degree of freedom carries almost no information -- so
    #     the because-clause is PROJECTED, exactly like the estimate is.
    for oid, blk in reported:
        p, het = blk["pooled"], (blk.get("heterogeneity") or {})
        name = outcome_text(obj, oid)
        if not name:
            s.refusals.append(("the result sentence for the outcome recorded as `%s` -- its "
                               "REGISTERED TEXT is not held, and an internal identifier is "
                               "not an outcome name" % oid,
                               ["outcomes[id=%s].name" % oid]))
            continue
        f = ["outcomes[id=%s].name" % oid, "results.by_outcome.%s.pooled" % oid]
        # LEAD WITH THE FINDING, as a paper does, with the registered text INSIDE the
        # sentence rather than standing in front of it as a fragment. The first pass
        # emitted "<outcome name>. Across 2 trials the pooled ... was ..." -- a heading
        # and a sentence, which is the shape of a record.
        _lvl = get(obj, "config.confidence_level")
        _subject = strip_measure_suffix(name, p.get("measure"))
        _ci = ci_prose(p)
        if _lvl:
            _ci = _ci[:-1] + ", %s%% interval)" % _lvl if _ci.endswith(")") else _ci
            f.append("config.confidence_level")
        txt = "The pooled %s for %s was %s across %s trials" % (
            measure_words(p.get("measure")), _lc_first(_subject), _ci,
            blk.get("k", "an unstated number of"))
        comparator = (next((o.get("comparator") for o in (obj.get("outcomes") or [])
                            if isinstance(o, dict) and o.get("id") == oid), None))
        if comparator:
            txt += ", against %s" % comparator
            f.append("outcomes[id=%s].comparator" % oid)
        txt += "."
        s.paras.append((txt, f))

        # THE REFERRAL, BESIDE THE NUMBER IT QUALIFIES.
        # A pool referred with its reason, and no renderer naming the key, is a referral
        # that exists for us and not for the reader -- registry class 65 on the fields
        # written in response to class 65. It goes here, immediately after the estimate
        # sentence, not into a methods tab.
        _ref_txt, _ref_f = pool_referral(blk)
        if _ref_txt:
            s.paras.append((_tidy(_ref_txt),
                            [p.replace("<this outcome>", oid) for p in _ref_f]))
        _fnd_txt, _fnd_f = pool_findings(blk)
        if _fnd_txt:
            s.paras.append((_tidy(_fnd_txt),
                            [p.replace("<this outcome>", oid) for p in _fnd_f]))

        # HETEROGENEITY, WITH THE CAVEAT THE OBJECT ALREADY RECORDS.
        if het.get("i2") is not None:
            hf = ["results.by_outcome.%s.heterogeneity.i2" % oid]
            # GLOSSED, NOT DROPPED. Every number here is the number that was there.
            # "I-squared 0%, tau-squared 0, Q 0.384, degrees of freedom 2" is four
            # statistics and no sentence; a reader who does not already know what they are
            # cannot use them, and a reader who does loses nothing by being told.
            _i2 = disp(het["i2"])
            ht = ("The trials' results were %s consistent with one another: I-squared, the "
                  "share of the variation between them that is more than chance alone "
                  "would produce, was %s%%" % (_i2_words(het["i2"]), _i2))
            _tail = []
            for extra, label in (
                    ("tau2", "the estimated variance of the true effects between trials "
                             "(tau-squared) was"),
                    ("q", "the heterogeneity test statistic Q was"),
                    ("df", "on degrees of freedom")):
                if het.get(extra) is not None:
                    _tail.append("%s %s" % (label, disp(het[extra])))
                    hf.append("results.by_outcome.%s.heterogeneity.%s" % (oid, extra))
            if _tail:
                ht += "; " + ", ".join(_tail)
            ht += "."
            # SAY THE CAVEAT ONCE. Every outcome on iv-iron-hf carries the SAME
            # `heterogeneity_status` text, so the first prose pass printed an identical
            # 60-word paragraph four times. ARNI states such a caveat once. Repetition is
            # a property of iterating a dict, not of an argument -- and a reader who meets
            # the same paragraph four times stops reading it the first time.
            status = blk.get("heterogeneity_status")
            if status:
                if status in _het_caveats_said:
                    ht += (" The caveat recorded above for %s applies here too."
                           % _het_caveats_said[status])
                else:
                    _het_caveats_said[status] = _lc_first(_subject)
                    ht += " %s" % status
                hf.append("results.by_outcome.%s.heterogeneity_status" % oid)
            s.paras.append((ht, hf))

        # WHY THIS POOL IS A POOL. The estimand reasoning is the argument of the section.
        if blk.get("poolable_reason"):
            # THE FIELD IS A NOUN PHRASE, not a clause. "This pool is a pool because a
            # single effect measure, a single outcome concept and a single unit of
            # analysis" is not a sentence, and lower-casing its first letter to force it
            # into one made it worse. The lead-in names it as recorded grounds instead.
            _pr = str(blk["poolable_reason"])
            if _pr in _grounds_said:
                pass          # said once, for the first outcome that recorded it
            else:
                _grounds_said[_pr] = True
                s.paras.append(("The grounds for pooling are recorded as: %s Where a later "
                                "pool on this page rests on the same grounds, they are not "
                                "restated." % _pr,
                                ["results.by_outcome.%s.poolable_reason" % oid]))
        for reason_field, lead_in in (
                ("why_k_equals_3_and_not_4", ""),
                ("relationship_to_the_other_pools", ""),
                ("WHY_THIS_REPLACES_A_WITHDRAWAL", ""),
                ("what_this_does_not_establish", "What this does not establish: ")):
            if blk.get(reason_field):
                s.paras.append(("%s%s" % (lead_in, blk[reason_field]),
                                ["results.by_outcome.%s.%s" % (oid, reason_field)]))

    for oid, blk in declined:
        name = outcome_text(obj, oid) or None
        reason = blk.get("poolable_reason")
        if not name:
            s.refusals.append(("the declined-pool sentence for `%s` -- no registered outcome "
                               "text is held" % oid, ["outcomes[id=%s].name" % oid]))
            continue
        if reason:
            s.paras.append(("%s. These %s trials are NOT pooled, and the reason is stated "
                            "rather than the outcome being quietly omitted: %s"
                            % (name[0].upper() + name[1:], blk.get("k", "?"), reason),
                            ["outcomes[id=%s].name" % oid,
                             "results.by_outcome.%s.poolable_reason" % oid]))
        else:
            s.refusals.append(("the reason the pool over %s is declined" % name,
                               ["results.by_outcome.%s.poolable_reason" % oid]))

        # A DECLINED POOL CAN STILL CARRY A REFERRAL AND A FINDING, AND UNTIL NOW NEITHER
        # RENDERED HERE.
        #
        # The reported branch above calls pool_referral() and pool_findings() immediately
        # after the estimate; this branch called neither. So a finding recorded on an
        # outcome WITHOUT a pooled point existed for us and not for the reader -- registry
        # class 65, on the exact mechanism built to fix class 65, surviving on the one path
        # nobody re-read. Found on cangrelor-pci-review, where BOTH of the object's pooled
        # outcomes are unreachable: `primary` is declared but has no point, so it lands
        # here; `corrected_composite_3component` has a point but no registered name, so the
        # reported branch refuses it. THE OBJECT COULD NOT RENDER A FINDING AT ALL.
        #
        # A pool that was declined is exactly where a reader most needs to be told what the
        # literature found instead.
        _ref_txt, _ref_f = pool_referral(blk)
        if _ref_txt:
            s.paras.append((_tidy(_ref_txt),
                            [p.replace("<this outcome>", oid) for p in _ref_f]))
        _fnd_txt, _fnd_f = pool_findings(blk)
        if _fnd_txt:
            s.paras.append((_tidy(_fnd_txt),
                            [p.replace("<this outcome>", oid) for p in _fnd_f]))
    # AND A POINTER TO THE TRANSCRIPT, so the guarantee is reachable from the body.
    # The verbatim model output is no longer a numbered section of the article; it sits at the
    # end as Extended data, where this venue puts material that supports the claims and is not
    # prose. A reader of Results should not have to discover that by scrolling.
    if any(((b or {}).get("r_output") or {}).get("verbatim")
           for b in (get(obj, "results.by_outcome") or {}).values()):
        s.add(obj, "The full model output for every pooled outcome -- the call, the "
                   "estimator, the heterogeneity statistics and the back-transformed "
                   "interval -- is reproduced verbatim as Extended data at the end of this "
                   "article, so every number above can be checked against the software that "
                   "produced it.",
              ["results.by_outcome"])
    secs.append(s)

    # ---- LIMITATIONS ------------------------------------------------------------------
    s = Section("limitations", "Limitations")
    _auth_lim = _manuscript_prose(obj, "limitations")
    if _auth_lim:
        s.add(obj, _auth_lim, ["manuscript.limitations"])
    # THE SECOND SOURCE OF FIELD NAMES IN PROSE, and it is deliberate label construction
    # rather than a container repr -- which is why a probe aimed at `_flatten_container`
    # alone would have left `What is not claimed:` standing on 65 pages. Where the map has a
    # sentence for the key, the sentence is used; otherwise the label form remains, visibly
    # unfinished.
    for field, lead in (("screening.known_limitation", "Known limitation of the screen"),
                        ("eligible_but_not_contributing.note",
                         "Eligible trials that do not contribute"),
                        ("verification_basis.what_is_not_claimed", "What is not claimed")):
        v = get(obj, field)
        if isinstance(v, str):
            key = field.rsplit(".", 1)[-1]
            txt = (_lead_in(key, v.strip())
                   if (_lead_ins().get("by_key") or {}).get(key)
                   else "%s: %s" % (lead, v))
            s.paras.append((txt, [field]))
    cc = get(obj, "claims_corrected")
    if isinstance(cc, list) and cc:
        s.paras.append(("%d claim(s) previously made about this review were corrected and the "
                        "corrections are retained on the object rather than overwritten."
                        % len(cc), ["claims_corrected"]))
    if not s.paras:
        s.refusals.append(("the limitations section", ["screening.known_limitation"]))
    secs.append(s)

    # =====================================================================================
    # THE SIXTEEN SECTIONS THE PROJECTOR COULD NOT REACH
    #
    # Measured 2026-08-20 against ARNI's authored manuscript, section by section: of the
    # 25 major sections ARNI carries, 16 were projectable from fields the other objects
    # ALREADY HOLD -- 32,254 characters of RoB rows, GRADE reasoning, published
    # comparisons, per-trial tables, quoted model output, references, data and software
    # availability -- and only 5 were genuinely absent from the objects. The projector had
    # a hard ceiling of eight sections and no slot for any of the sixteen.
    #
    # EVERY SECTION BELOW IS A SLOT THAT ALWAYS EXISTS. A topic with no published
    # comparison SAYS SO, by name, naming the field it would have come from. Omitting the
    # section silently is the failure this whole design exists to prevent: an absent
    # section and an unmentioned one look identical to a reader.
    # =====================================================================================

    # ---- ABSTRACT ----------------------------------------------------------------------
    s = Section("abstract", "Abstract")
    # WHAT THE REVIEW DOES NOT PUBLISH, IN THE ABSTRACT ITSELF.
    #
    # A withdrawn outcome was recorded beside the outcome it concerned, and a reader of the
    # abstract never reached it. Found by a blind cross-family read: given the object and the
    # abstract and none of our conclusions, GPT-5 said a reader "would reasonably conclude the
    # review publishes a pooled estimate across all relevant trials", and the object does not
    # support that. Rendered at the END of the abstract so it qualifies the numbers a reader
    # has just met rather than preceding them.
    _nd = next((k for k in sorted(obj) if str(k).startswith("what_this_review_does_not_publish")
                and isinstance(obj[k], str) and obj[k].strip()), None)
    # An AUTHORED abstract, where the object holds one, in preference to the composed
    # sentences below -- and the composed ones still follow, because they name the fields
    # they came from and an authored paragraph does not.
    _auth_abs = _manuscript_prose(obj, "abstract")
    if _auth_abs:
        s.add(obj, _auth_abs, ["manuscript.abstract"])
    s.add(obj, "Question. %s" % (get(obj, "question") or ""), ["question"])
    casc = get(obj, "k_cascade") or {}
    if casc.get("k_included") is not None:
        s.add(obj, "Included studies. %s trial(s) contribute to at least one synthesis."
              % casc.get("k_included"), ["k_cascade.k_included"])
    _pooled = []
    for oid, blk in sorted((get(obj, "results.by_outcome") or {}).items()):
        p = (blk or {}).get("pooled") or {}
        _nm = outcome_text(obj, oid)
        if p.get("point") is not None and _nm:
            # THE SUBJECT IS THE REGISTERED OUTCOME TEXT. An abstract that reads
            # "0.81 for hfh_cvd_recurrent" is a record of a dict, not a finding.
            # THE MEASURE IS NOT NAMED TWICE. Some outcome names already end "... as a
            # hazard ratio", and appending the measure word produced, live, "as a hazard
            # ratio: hazard ratio 0.783". Caught by a blind copy-edit read from a second
            # family; a doubled word is the kind of thing only reading finds.
            _mw = measure_words(p.get("measure"))
            _nm_l = str(_nm).lower()
            _dup = _mw and _mw.lower().rstrip("s") in _nm_l
            _pooled.append("%s: %s%s across %s trials"
                           % (_nm, "" if _dup else _mw + " ", ci_prose(p),
                              blk.get("k", "an unstated number of")))
    # A QUALIFIED ESTIMATE MUST NOT APPEAR UNQUALIFIED IN THE ABSTRACT.
    #
    # The Results section renders a pool's referral and its findings immediately after the
    # estimate. THE ABSTRACT REPEATED THE SAME NUMBERS AND CARRIED NEITHER -- and an
    # abstract is frequently the only part read, so a referred pool quoted here bare is the
    # withholding failure at the point of maximum exposure.
    #
    # A FLAG, NOT THE TEXT. Reproducing a full referral would swamp a 300-word abstract and
    # the venue counts those words. This says a qualification exists and where to read it,
    # which is what a reader needs to decide whether to go and look.
    _qual = [oid for oid, blk in sorted((get(obj, "results.by_outcome") or {}).items())
             if isinstance(blk, dict)
             and (pool_referral(blk)[0] or pool_findings(blk)[0])]
    if _pooled and _qual:
        _pooled.append("%d of these pooled outcome(s) carr%s a stated qualification -- a "
                       "referral or a recorded finding -- given in full in Results and not "
                       "reproduced here"
                       % (len(_qual), "ies" if len(_qual) == 1 else "y"))
    # ---- THE STRUCTURED ABSTRACT F1000RESEARCH REQUIRES --------------------------------
    #
    # Background / Methods / Results / Conclusions. TWO OF THE FOUR ARE FACTS AND TWO ARE
    # ARGUMENT, and the split is the whole design:
    #
    #   METHODS and RESULTS are composed from stored quantities -- what was searched, what
    #   was eligible, how it was pooled, what came out, how heterogeneous, how certain.
    #   Composing a sentence from facts the object holds is a rendering transform.
    #
    #   BACKGROUND and CONCLUSIONS ARE ARGUMENT. They say why the question matters and what
    #   the reader should now believe, and NO ARRANGEMENT OF STORED QUANTITIES YIELDS
    #   EITHER. They are emitted ONLY from an authored field and refused otherwise. There is
    #   deliberately no composition branch for them -- not a disabled one, none -- because a
    #   renderer that can compose an argument will eventually be asked to.
    #
    # Measured before this was written: 131 of 155 objects can produce a Methods paragraph,
    # 43 of 155 a Results paragraph, and 1 of 155 a Background -- ARNI, whose object carries
    # a person's authored abstract. That 1 is authored, never generated.

    # -- BACKGROUND: authored only -------------------------------------------------------
    _bg, _bgtxt = None, None
    for _f in ("manuscript.abstract.Background", "protocol.rationale"):
        _bgtxt = _authored(obj, _f)
        if _bgtxt:
            _bg = _f
            break
    # NOT TWICE. When the object carries a whole authored abstract, that paragraph already
    # opens with its own Background and adding this one repeats it verbatim -- which is what
    # the first cut did on ARNI.
    if _bg and not _auth_abs:
        s.add(obj, "Background. %s" % _bgtxt, [_bg])
    elif _bg and _auth_abs:
        pass
    else:
        s.refusals.append((
            "the Background sentence of the abstract. Background is ARGUMENT -- why this "
            "question matters -- and no arrangement of the quantities this object holds "
            "yields it. It is emitted only from an authored field and there is no "
            "composition path for it here",
            ["manuscript.abstract.Background"]))

    # -- METHODS: composed from facts ----------------------------------------------------
    _mparts, _mfields = [], []
    _elig_own = None
    _dbs = get(obj, "search.databases")
    if isinstance(_dbs, (list, dict)) and _dbs:
        _names = _source_names(_dbs)
        if _names:
            _mparts.append("%s were searched" % _and_list(_names))
            _mfields.append("search.databases")
    _elig = get(obj, "screening.eligibility")
    if _elig is not None:
        _ep = _phrase(_elig, 18)
        if _ep:
            _mparts.append("eligibility was %s" % _ep)
        else:
            # PROSE GETS ITS OWN SENTENCE. Dropped into `eligibility was {slot}` this produced
            # "eligibility was ELIGIBILITY turns on population, intervention and comparator..."
            # and was then cut mid-word at 300 characters.
            _elig_own = _own_sentence(_elig)
        _mfields.append("screening.eligibility")
    # THE ABSTRACT GOES THROUGH THE SAME PREDICATE, NOT A SECOND GUARD. On MALARIA_ACT the
    # synthesis section refused this sentence and the abstract asserted it, four sections
    # apart, from the same field.
    _model = _first_by_outcome(obj, ("model",)) if _any_pool_occurred(obj) else None
    _est = _first_by_outcome(obj, ("estimator_used",)) if _any_pool_occurred(obj) else None
    _model = _model if _is_value(_model) else None
    _est = _est if _is_value(_est) else None
    if _model or _est:
        _mparts.append("estimates were pooled under %s%s"
                       % (_model_words(_model) if _model else "the recorded model",
                          " with the %s estimator" % _v_str(_est) if _est else ""))
        _mfields.append("results.by_outcome")
    _tool = get(obj, "risk_of_bias.tool")
    if _tool is not None:
        _mparts.append("risk of bias was assessed with %s" % _v_str(_tool))
        _mfields.append("risk_of_bias.tool")
    _gr = get(obj, "grade.approach")
    if _gr is not None:
        _mparts.append("certainty was rated with %s" % _v_str(_gr))
        _mfields.append("grade.approach")
    if _mparts:
        s.add(obj, "Methods. %s." % _sentence_join(_mparts), _mfields)
        # THE ELIGIBILITY PARAGRAPH DOES NOT BELONG IN THE ABSTRACT. An abstract must stand
        # alone, and this paragraph cites "section 3.2.4" of a document it never names --
        # flagged by the second reviewer as reading like a cross-reference to nothing. It is
        # carried in Methods -- eligibility criteria, where the reader has the context.
        pass
    else:
        # CITE ONLY WHAT IS ACTUALLY ABSENT. The first cut cited `results.by_outcome` as a
        # stand-in for "the pooling model", but that container is PRESENT on these objects
        # and the figure legends use it -- so one manuscript said a field was missing in the
        # abstract and used it two sections later, on 10 topics. The pooling model lives at
        # `results.by_outcome.<oid>.model`, and that is the path to name.
        _absent = [f for f in ("search.databases", "screening.eligibility",
                               "risk_of_bias.tool", "grade.approach")
                   if get(obj, f) is None]
        _absent += ["results.by_outcome.%s.model" % oid
                    for oid in sorted((get(obj, "results.by_outcome") or {}))
                    if _first_by_outcome(obj, ("model",)) is None]
        s.refusals.append((
            "the Methods sentence of the abstract. None of the method facts this would be "
            "composed from -- databases searched, eligibility, pooling model, "
            "risk-of-bias tool, certainty approach -- is recorded on this object",
            _absent or ["search.databases"]))

    # -- RESULTS: composed from facts ----------------------------------------------------
    _rparts, _rfields = [], []
    if casc.get("k_included") is not None:
        _rparts.append("%s trial(s) contributed to at least one synthesis"
                       % casc.get("k_included"))
        _rfields.append("k_cascade.k_included")
    if _pooled:
        _rparts.append("; ".join(_pooled))
        _rfields.append("results.by_outcome")
    _i2 = _first_by_outcome(obj, ("heterogeneity", "i2"))
    if _i2 is not None:
        # `_i2_words` RETURNS AN ADVERB -- "closely", "loosely" -- because it was written to
        # complete "the trials agreed closely". Dropped into "heterogeneity was {word}" it
        # produced "heterogeneity was closely (I-squared 0%)", which is not a sentence.
        _rparts.append("the trials agreed %s (I-squared %s%%)"
                       % (_i2_words(_i2), _num(_i2)))
        _rfields.append("results.by_outcome")
    _cert = _live_certainty(obj)
    if _cert is not None:
        _rparts.append("certainty of the evidence was %s" % _cert)
        _rfields.append("grade.by_outcome")
    if _rparts:
        # A SENTENCE STARTS WITH A CAPITAL. "Results. cardiovascular death or..." was flagged
        # by both reviewers; the first clause is an outcome name and arrived lower-cased.
        _rtext = _sentence_join(_rparts)
        _rtext = _rtext[:1].upper() + _rtext[1:] if _rtext else _rtext
        s.add(obj, "Results. %s." % _rtext, sorted(set(_rfields)))
    else:
        # CITE THE LEAVES THAT ARE ACTUALLY ABSENT, NOT A WILDCARD OVER A PARENT THAT IS
        # PRESENT. `results.by_outcome.*.pooled.point` reads to the whole-document check as
        # `results.by_outcome`, which the figure legends USE -- so the manuscript said the
        # same field was absent in one section and used it in another, on 10 topics.
        #
        # THE CHECK WAS RIGHT AND I MADE IT FIRE. The refusal predates this change, but the
        # abstract was REFUSED as a whole on those topics, so its citations were never
        # compared against the rest of the document. Composing a Methods paragraph turned
        # the section WRITTEN and exposed it. A defect that becomes visible when a section
        # starts working was always there.
        _missing = ["results.by_outcome.%s.pooled.point" % oid
                    for oid in sorted((get(obj, "results.by_outcome") or {}))]
        s.refusals.append((
            "the Results sentence of the abstract -- no outcome on this object carries a "
            "pooled point estimate, so there is nothing to report and none is manufactured "
            "here. The reason each pool is declined is given in Results",
            _missing or ["results.by_outcome"]))

    # -- CONCLUSIONS: authored only ------------------------------------------------------
    _cc, _cctxt = None, None
    for _f in ("manuscript.abstract.Conclusions", "conclusions", "manuscript.conclusions"):
        _cctxt = _authored(obj, _f)
        if _cctxt:
            _cc = _f
            break
    if _cc and _auth_abs:
        pass
    elif _cc and _cctxt and s.add(obj, "Conclusions. %s" % _cctxt, [_cc]):
        pass
    else:
        s.refusals.append((
            "the Conclusions sentence of the abstract. A conclusion is ARGUMENT -- what a "
            "reader should now believe -- and it is emitted only from an authored field. "
            "Composing one from the estimate would be this renderer telling the reader "
            "what to conclude, which no field supports",
            ["manuscript.abstract.Conclusions"]))
    secs.append(s)

    # ---- INTRODUCTION (content gap, refused by name) -----------------------------------
    s = Section("introduction", "Introduction")
    # CITE THE FIELD THE TEXT ACTUALLY CAME FROM, not both candidates. `Section.add`
    # requires EVERY cited field to resolve, which is right -- a paragraph naming a field
    # that holds nothing is the provenance equivalent of a dead link -- so the source is
    # chosen first and cited alone.
    _intro_src = ("protocol.rationale" if get(obj, "protocol.rationale")
                  else ("manuscript.introduction" if _manuscript_prose(obj, "introduction")
                        else None))
    _intro = (get(obj, "protocol.rationale") if _intro_src == "protocol.rationale"
              else _manuscript_prose(obj, "introduction"))
    _intro_ok = bool(_intro_src and s.add(obj, "Background. %s" % _intro, [_intro_src]))
    _add_drafts(s, obj, "Introduction")
    if not _intro_ok and not _drafted(obj, "Introduction"):
        s.refusals.append(("the Introduction -- no background or rationale is recorded on "
                           "this object. This is a CONTENT gap, not a rendering one: no "
                           "change to this projector produces it, and it is written by "
                           "adding `protocol.rationale` to the object",
                           ["protocol.rationale"]))
    secs.append(s)

    # ---- CERTAINTY OF THE EVIDENCE (GRADE) ---------------------------------------------
    s = Section("certainty", "Certainty of the evidence")
    g = get(obj, "grade") or {}
    if g.get("approach"):
        s.add(obj, "Certainty was rated with %s. %s"
              % (g.get("approach"), g.get("starting_point") or ""), ["grade.approach"])
    if g.get("not_rated_up"):
        s.add(obj, str(g["not_rated_up"]), ["grade.not_rated_up"])
    rows, fields = [], []
    for oid, blk in sorted((g.get("by_outcome") or {}).items()):
        if not isinstance(blk, dict):
            continue
        # THE OUTCOME'S NAME AND WORDED STEPS. This row used to begin with the estimand
        # key and end with a Python dict repr. The key is still reachable -- it is in this
        # section's source list, as `grade.by_outcome.<oid>`.
        rows.append([_outcome_words(obj, oid), str(blk.get("certainty") or "not rated"),
                     str(blk.get("k", "?")), str(blk.get("started_at") or ""),
                     "; ".join(_grade_step_words(x) for x in (blk.get("steps") or []))
                     or "no downgrade recorded"])
        fields.append("grade.by_outcome.%s" % oid)
    s.add_table(obj, "Certainty of the evidence, by outcome, with every rating step",
                ["Outcome", "Certainty", "k", "Started at", "Rating steps"], rows,
                fields or ["grade.by_outcome"])
    for oid, blk in sorted((g.get("by_outcome") or {}).items()):
        if isinstance(blk, dict) and blk.get("summary"):
            s.add(obj, str(blk["summary"]), ["grade.by_outcome.%s.summary" % oid])
    if not (s.paras or s.tables):
        s.refusals.append(("the certainty assessment -- no GRADE record is held, so the "
                           "certainty column elsewhere on this page is an em dash rather "
                           "than a guess", ["grade"]))
    # AFTER the refusal decision, never before it. Placed at the top of the
    # section this line made `s.paras` non-empty, the `if not (s.paras or
    # s.tables)` refusal stopped firing, and six topics lost a refusal that was
    # true -- delivery 26 -> 20. A bookkeeping claim belongs in the section; it
    # must not be the thing that decides the section has content.
    _add_bookkeeping(s, obj, "which_risk_of_bias_domains_drove_the_rating")
    secs.append(s)

    # ---- RISK OF BIAS ------------------------------------------------------------------
    s = Section("risk_of_bias", "Risk of bias in the included results")
    rob = get(obj, "risk_of_bias") or {}
    if rob.get("tool"):
        s.add(obj, "Risk of bias was assessed with %s. The unit of assessment is %s"
              % (rob.get("tool"), rob.get("unit_of_assessment") or "a result"),
              ["risk_of_bias.tool"])
    ceiling = rob.get("ceiling") or {}
    if ceiling.get("statement"):
        s.add(obj, "%s %s" % (ceiling["statement"],
                              ceiling.get("what_would_change_it") or ""),
              ["risk_of_bias.ceiling.statement"])
    if rob.get("default_rule"):
        s.add(obj, str(rob["default_rule"]), ["risk_of_bias.default_rule"])

    # THE SECOND ASSESSOR, AND THE DISAGREEMENT RATE. Added 2026-08-21.
    #
    # Mahmood's standing specification is that RoB 2 must be done by TWO AIs. Three topics now
    # carry a blind cross-family second assessment with its verbatim reply and its disagreement
    # rate -- AND NONE OF IT RENDERED. The projector read `tool`, `ceiling`, `default_rule` and
    # `by_outcome`, so a reader met an assessment with no indication that a second assessor had
    # ever seen it, or that it disagreed. CLASS 83, ON THE ONE THING THE SPECIFICATION NAMES,
    # recorded on the same night the delivery audit was built for exactly this failure.
    #
    # The one-assessor disclosure is rendered too. A page whose assessment is incomplete
    # against the specification should say so where the assessment is.
    for _k in sorted(k for k in rob if k.startswith("SECOND_ASSESSOR")):
        _sa = rob.get(_k)
        if not isinstance(_sa, dict):
            continue
        for _f, _lead in (("assessor_2", "A SECOND, INDEPENDENT ASSESSMENT WAS OBTAINED FROM"),
                          ("assessor_1", "The assessment above was made by"),
                          ("how_it_was_asked", "How the second assessor was asked"),
                          ("DISAGREEMENT_RATE", "THE DISAGREEMENT RATE, reported as "
                                                "disagreement because agreement between two "
                                                "assessors given the same facts authenticates "
                                                "nothing"),
                          ("the_disagreement", "Where they disagree"),
                          # `verbatim_reply` AND THE PROTOCOL DESCRIPTION LEAVE THE BODY.
                          #
                          # Nine lines of `NCT03036124__cvdeath_or_whf_first
                          # D1=NO_INFORMATION D2=NO_INFORMATION ...` were printed in the
                          # middle of the article. That is machine output in a paper. It is
                          # not dropped -- it is rendered in Extended data beside the R
                          # transcript, which is where this venue puts material that
                          # supports the claims and is not prose. The body keeps the rate,
                          # the per-domain breakdown and the named disagreements, which are
                          # the finding.
                          ("not_changed_here", "What has NOT been changed on the strength of "
                                               "it")):
            _v = _sa.get(_f)
            if isinstance(_v, str) and _v.strip():
                s.add(obj, "%s: %s" % (_lead, _v.strip()),
                      ["risk_of_bias.%s.%s" % (_k, _f)])
        # THE PER-DOMAIN BREAKDOWN, WHICH IS THE FINDING AND NOT THE RATE.
        #
        # Written onto 19 topics and rendered on none: the projector read DISAGREEMENT_RATE and
        # not PER_DOMAIN. A bare rate reads as noise; "they disagree on D1 every time and on D2
        # and D3 never" is a measurement, and it was the half that never reached a reader.
        _pd = _sa.get("PER_DOMAIN")
        if isinstance(_pd, dict) and _pd:
            s.add(obj, "Where they disagree, by domain: %s."
                  % _and_list(["%s %s" % (k, v) for k, v in sorted(_pd.items())]),
                  ["risk_of_bias.%s.PER_DOMAIN" % _k])
        # THE RECOUNT, IMMEDIATELY AFTER THE NUMBER IT QUALIFIES.
        #
        # Applying the RoB 2 D1 guidance moved this review onto the position assessor 2 had
        # taken, which left `PER_DOMAIN` printing `D1: 2 of 2 disagree` inches from a table
        # saying NO_INFORMATION on both. A page asserting a live disagreement its own object no
        # longer holds is class 44, and the stored rate is a PUBLISHED NUMBER that is not this
        # project's to correct silently -- so both are rendered, in order, labelled. Anywhere
        # else on the page and the reader meets the stale number without the correction.
        # THE SOURCE PATH IS BUILT FROM THE KEY THAT WAS FOUND, NEVER RETYPED.
        # Written first as `...RECOUNTED_AFTER_THE_D1_RESOLUTION` while the field is
        # `..._2026_08_21`, so every sentence here rendered as a REFUSAL on the page -- the
        # projector could not resolve the path and said so, correctly. Class 83 for the sixth
        # time in this run, in the projector, in an edit whose whole purpose was to make a
        # correction visible. Retyping a key beside code that already holds it is the defect.
        _rk = next((_x for _x in sorted(_sa) if _x.startswith("RECOUNTED_AFTER")
                    and isinstance(_sa[_x], dict)), None)
        _rc = _sa.get(_rk) if _rk else None
        if _rc:
            _src = ["risk_of_bias.%s.%s" % (_k, _rk)]
            s.add(obj, "That rate was measured before this review's D1 judgements moved. "
                       "It is left as measured: %s" % _rc.get("why_this_field_exists", ""),
                  _src)
            s.add(obj, "Re-run on the object as it now stands: %s. By domain: %s."
                  % (_rc.get("recounted_now", ""),
                     _and_list(["%s %s" % (a, b) for a, b in
                                sorted((_rc.get("PER_DOMAIN_recounted_now") or {}).items())])),
                  _src)
            for _f in ("what_moved_and_what_did_not", "why_D1_still_disagrees_here",
                       "and_it_bounds_a_finding_of_ours"):
                if isinstance(_rc.get(_f), str) and _rc[_f].strip():
                    s.add(obj, _rc[_f].strip(), _src)
        _ea = _sa.get("each_disagreement")
        if isinstance(_ea, list) and _ea:
            # OUTCOME IDENTIFIERS INSIDE A COMPOSITE KEY. These entries are stored as
            # `NCT03036124__cvdeath_or_whf_first D1: assessor 1 SOME_CONCERNS ...`, and the
            # schema identifier reached the page inside a trial-plus-outcome key. Where the
            # object stores a name for that outcome the name is substituted; where it does not,
            # the identifier stands and is NOT dressed up as a label, because a missing label
            # is a missing field.
            def _name_ids(txt):
                out = str(txt)
                for _o in (obj.get("outcomes") or []):
                    if not isinstance(_o, dict):
                        continue
                    _oid, _nm = _o.get("id"), _o.get("name")
                    if _oid and isinstance(_nm, str) and _nm.strip() and _oid in out:
                        out = out.replace("__" + _oid, " on %s" % _nm.strip())
                        out = re.sub(r"(?<![\w-])%s(?![\w-])" % re.escape(_oid),
                                     _nm.strip(), out)
                return out
            s.add(obj, "Every disagreement, named: %s."
                  % "; ".join(_name_ids(x) for x in _ea),
                  ["risk_of_bias.%s.each_disagreement" % _k])
        _td = _sa.get("the_three_disagreements")
        if isinstance(_td, dict):
            for _dk in sorted(_td):
                if isinstance(_td[_dk], str) and _td[_dk].strip():
                    s.add(obj, "Disagreement -- %s: %s"
                          % (str(_dk).replace("_", " "), _td[_dk].strip()),
                          ["risk_of_bias.%s.the_three_disagreements" % _k])
    _one = rob.get("ONE_ASSESSOR_ONLY")
    if isinstance(_one, str) and _one.strip() and not any(
            k.startswith("SECOND_ASSESSOR") for k in rob):
        s.add(obj, _one.strip(), ["risk_of_bias.ONE_ASSESSOR_ONLY"])
    # `by_outcome` IS THE SHAPE THIS CORPUS ACTUALLY USES, and it was not in this list.
    #
    # Measured 2026-08-20 across 155 objects: ONE object holds risk of bias under
    # `by_result`, and TEN hold it under `by_outcome` -- 36 result-level assessments, on
    # alirocumab-lipid, arni-hfref, iv-iron-hf, bempedoic-acid-review, sglt2-hf and five
    # others. Every one of those 36 reached NO READER. The section rendered its tool, its
    # unit of assessment and its ceiling, and then no judgements, so a page could say
    # "4 result-level assessments were made" and show none of them.
    #
    # P46 counts an object as holding risk of bias per result. IT DOES. The count was
    # right and the delivery was empty, which is the class this project keeps meeting:
    # counted is not delivered, and a summary with no detail beneath it cannot disagree
    # with anything.
    #
    # `by_outcome` nests one level deeper -- outcome, then result -- so it is flattened
    # with the outcome named in the row rather than folded away. THE SAME TRIAL APPEARS
    # TWICE UNDER TWO OUTCOMES AND CAN LAND DIFFERENTLY, which is the entire point of
    # assessing a result rather than a study, and a table keyed on the trial alone would
    # destroy exactly that.
    rows, fields = [], []
    for key in ("by_outcome", "by_result", "results", "assessments", "by_trial"):
        blk = rob.get(key)
        if not isinstance(blk, dict) or not blk:
            continue
        if key == "by_outcome":
            for oid, per in sorted(blk.items()):
                if not isinstance(per, dict):
                    continue
                for rid, judgement in sorted(per.items()):
                    if not isinstance(judgement, dict):
                        rows.append(["%s -- %s" % (oid, rid), str(judgement), ""])
                        continue
                    label = judgement.get("trial") or rid
                    # The reason a reader needs is the reason for the OVERALL judgement,
                    # and then the domain that drove it. A domain judged HIGH with its
                    # reason omitted is the same defect one level down.
                    why = str(judgement.get("overall_reason")
                              or judgement.get("reason") or "")
                    doms = judgement.get("domains")
                    if isinstance(doms, dict):
                        # EVERY JUDGED DOMAIN, not only the adverse ones. Filtering to
                        # HIGH and SOME_CONCERNS dropped the single most informative
                        # sentence in this assessment -- the reason SOLOIST-WHF's
                        # total-event result is LOW on domain 5, which is that the pooled
                        # estimand IS its registered primary word for word. A table that
                        # shows only what went wrong tells a reader nothing about what
                        # went right, and the contrast between the two is the finding.
                        # NO_INFORMATION is excluded because its reason is a fixed
                        # sentence about what this review did not retrieve, repeated
                        # identically on every result, and it is stated once above.
                        driving = [(dn, dv) for dn, dv in sorted(doms.items())
                                   if isinstance(dv, dict)
                                   and dv.get("judgement") in ("HIGH", "SOME_CONCERNS", "LOW")]
                        for dn, dv in driving:
                            # EITHER VOCABULARY FOR THE JUSTIFICATION. Some objects store a
                            # domain's justification as `reason`, others as an `evidence`
                            # LIST -- bempedoic-acid-review is the second shape, and reading
                            # only `reason` rendered its whole per-result table as judgements
                            # with EMPTY reasons. The delivery audit reported the limb as
                            # reaching no reader, and it was right for the wrong field.
                            _why = dv.get("reason") or dv.get("why")
                            if not _why:
                                _ev = dv.get("evidence")
                                if isinstance(_ev, list):
                                    _why = " ".join(str(x) for x in _ev if x)
                                elif isinstance(_ev, str):
                                    _why = _ev
                            why += ("  %s: %s -- %s"
                                    % (_ROB_DOMAINS.get(dn, dn.replace("_", " ")),
                                       dv.get("judgement"), _why or ""))
                    # The outcome's NAME, not its key. Handbook 8.2 requires the
                    # result to be named; it does not require it to be named in the
                    # object's storage vocabulary.
                    rows.append(["%s -- %s (%s)"
                                 % (_outcome_words(obj, oid), label, rid),
                                 str(judgement.get("overall") or judgement.get("rating")
                                     or "not judged"),
                                 why or str(judgement.get("overall_note") or "")])
        else:
            for rid, judgement in sorted(blk.items()):
                if isinstance(judgement, dict):
                    rows.append([rid, str(judgement.get("overall") or judgement.get("rating")
                                          or "not judged"),
                                 str(judgement.get("reason") or judgement.get("why") or "")])
                else:
                    rows.append([rid, str(judgement), ""])
        fields.append("risk_of_bias.%s" % key)
        break
    if rows:
        s.add_table(obj, "Risk-of-bias judgement for every included result",
                    ["Result", "Judgement", "Reason"], rows, fields)

    # A REFUSED ASSESSMENT MUST SAY SO WHERE THE ASSESSMENT WOULD HAVE BEEN.
    #
    # An object that refuses this limb stores `state`, `why`, `what_would_close_it` and
    # `consequence_carried_into_grade`, and NONE of them was read here. So on
    # apixaban-vte-prophylaxis a reader met exactly one sentence -- "Risk of bias was
    # assessed with RoB 2 … the unit of assessment is a result" -- and nothing else. THAT
    # ASSERTS AN ASSESSMENT THAT WAS REFUSED, which is worse than the refusal it replaced.
    # P46 counts a refusal as a completed outcome; a completed outcome nobody can read is
    # not completed.
    if not rows:
        for _k, _lead in (("state", "This limb is REFUSED, and the state recorded is"),
                          ("why", "Why it is refused"),
                          ("what_would_close_it", "What would close it"),
                          ("consequence_carried_into_grade",
                           "What this refusal carries into the certainty rating"),
                          ("refusal_discharges_P46_because",
                           "Why the refusal discharges the standard")):
            _v = rob.get(_k)
            if isinstance(_v, str) and _v.strip():
                s.add(obj, "%s: %s" % (_lead, _v.strip()), ["risk_of_bias.%s" % _k])

    if not (s.paras or s.tables):
        s.refusals.append(("the risk-of-bias assessment", ["risk_of_bias"]))
    # AFTER the refusal decision, never before it. Placed at the top of the
    # section this line made `s.paras` non-empty, the `if not (s.paras or
    # s.tables)` refusal stopped firing, and six topics lost a refusal that was
    # true -- delivery 26 -> 20. A bookkeeping claim belongs in the section; it
    # must not be the thing that decides the section has content.
    _add_bookkeeping(s, obj, "that_two_assessors_disagreed_and_where")
    secs.append(s)

    # ---- DISAGREEMENTS BETWEEN SOURCES -------------------------------------------------
    s = Section("disagreements", "Disagreements between sources")
    rec = get(obj, "reconciliation") or {}
    if rec.get("why_this_step_exists"):
        s.add(obj, str(rec["why_this_step_exists"]), ["reconciliation.why_this_step_exists"])
    if rec.get("clean_because"):
        s.add(obj, str(rec["clean_because"]), ["reconciliation.clean_because"])
    if rec.get("what_the_benchmarks_show"):
        s.add(obj, str(rec["what_the_benchmarks_show"]),
              ["reconciliation.what_the_benchmarks_show"])
    bm = rec.get("published_benchmarks")
    if isinstance(bm, list) and bm:
        s.add_table(obj, "Published benchmarks this review was reconciled against",
                    ["Review", "Endpoint", "Measure", "Estimate", "Trials"],
                    [[str(b.get("review_id", "")), str(b.get("endpoint", "")),
                      str(b.get("measure", "")),
                      ("%s (%s to %s)" % (b.get("point"), b.get("ci_low"), b.get("ci_high"))
                       if b.get("point") is not None else "not stated"),
                      str(b.get("trial_count", ""))] for b in bm if isinstance(b, dict)],
                    ["reconciliation.published_benchmarks"])
    if not (s.paras or s.tables):
        s.refusals.append(("the reconciliation against other sources",
                           ["reconciliation"]))
    secs.append(s)

    # ---- COMPARISON WITH PUBLISHED SYNTHESES -------------------------------------------
    s = Section("published_comparison", "Comparison with published syntheses")
    pc = get(obj, "published_comparison") or {}
    if pc.get("_how_identified"):
        s.add(obj, "Published syntheses were identified as follows. %s"
              % pc["_how_identified"], ["published_comparison._how_identified"])
    revs = pc.get("reviews")
    if isinstance(revs, list) and revs:
        s.add_table(obj, "Published syntheses compared with this review, with a denominator",
                    ["Citation", "PMID", "Their k", "Scope", "How it differs from ours"],
                    [[_pc_citation(r)[:160], str(r.get("pmid", "")),
                      _pc_their_k(r), _pc_cell(r, "scope", "outcome_pooled")[:110],
                      _pc_cell(r, "how_it_differs_from_ours", "agreement",
                               "why_not_comparable")[:220]]
                     for r in revs if isinstance(r, dict)],
                    ["published_comparison.reviews"])
        s.add(obj, "This review was compared against %d published synthesis(es); the "
                   "denominator is stated because a comparison against an unstated number "
                   "of reviews is not a comparison." % len(revs),
              ["published_comparison.reviews"])
    # THE FINDING OF THE COMPARISON, WHICH IS THE POINT OF MAKING ONE.
    #
    # Every applier this run wrote its conclusion to `THE_FINDING_OF_THIS_COMPARISON_<stamp>`
    # and NOTHING READ THAT KEY. The text reached readers only on the topics where the same
    # sentences were also copied into the outcome block's findings -- so on the rest, the
    # manuscript showed that a comparison existed and never said what it found. Class 83.
    for _k in sorted(k for k in pc if k.startswith("THE_FINDING_OF_THIS_COMPARISON")):
        _t = _v_str(pc.get(_k))
        if _t:
            s.add(obj, "What this comparison found. %s" % _t,
                  ["published_comparison.%s" % _k])
    _ib = str(pc.get("identity_basis") or "").strip()
    if _ib:
        s.add(obj, "On what basis their trial set is known: %s" % _ib,
              ["published_comparison.identity_basis"])
    dd = pc.get("divergence_decomposed")
    if isinstance(dd, dict) and dd.get("why_they_differ"):
        s.add(obj, "Where our result differs from theirs: %s" % dd["why_they_differ"],
              ["published_comparison.divergence_decomposed.why_they_differ"])
    if not (s.paras or s.tables):
        s.refusals.append(("the comparison with published syntheses -- no published "
                           "synthesis is recorded for this topic, so no denominator can be "
                           "given", ["published_comparison"]))
    secs.append(s)

    # ---- EXTENDED DATA: STATISTICAL OUTPUT, QUOTED VERBATIM ----------------------------
    #
    # THE SECTION THAT WAS NEARLY MISCLASSIFIED. A first probe looked at
    # `results.cross_engine` and reported this as a CONTENT gap. It lives one level lower,
    # per outcome, at `results.by_outcome.<oid>.r_output.verbatim` -- present for every
    # outcome, with the R call and the package versions. An absence my own search reported.
    # F1000Research's own name for it. The venue defines "Extended data" as "Additional
    # materials that support the key claims in the paper but are not a part of the main body",
    # and lists Supplementary Material after the declarations. That is exactly what a metafor
    # transcript is: it supports the estimate and it is not prose.
    s = Section("statistical_output",
                "Extended data: statistical output, quoted verbatim")
    any_out = False
    for oid, blk in sorted((get(obj, "results.by_outcome") or {}).items()):
        ro = (blk or {}).get("r_output") or {}
        v = ro.get("verbatim")
        if v:
            any_out = True
            # EITHER SPELLING. 17 blocks store `environment` and 7 store `_environment`;
            # only the second was read, so the engine and package versions were dropped from
            # the manuscript on 17 of 24. Class 83's mechanism at smaller stakes.
            env = ro.get("_environment") or ro.get("environment") or ""
            call = ro.get("call") or ""
            s.add(obj, "%s%s%s" % (("[%s] " % env) if env else "",
                                   ("call: %s -- " % call) if call else "", str(v)),
                  ["results.by_outcome.%s.r_output.verbatim" % oid])
        ce = (blk or {}).get("cross_engine") or {}
        if ce.get("engine"):
            s.add(obj, "Cross-engine verification for %s: %s %s"
                  % (oid, ce.get("engine"), ce.get("agreement") or ""),
                  ["results.by_outcome.%s.cross_engine" % oid])
    # AND THE SAME OUTPUT STORED AT THE TOP LEVEL. Added 2026-08-21, class 83.
    #
    # The loop above reads `results.by_outcome.<oid>.r_output.verbatim`. Limb 4 of the page
    # standard was being written to a TOP-LEVEL `model_output.verbatim` by this run's
    # appliers, which nothing read -- so a refit whose R output had been captured, stored
    # and checked against the delivered point still produced the refusal "no analysis
    # output is stored on this object". Both locations are read now.
    mo = get(obj, "model_output") or {}
    if isinstance(mo, dict) and str(mo.get("verbatim") or "").strip():
        any_out = True
        s.add(obj, "%s%s\n\n%s"
              % (("[%s] " % mo["engine"]) if mo.get("engine") else "",
                 ("call: %s --" % mo["invocation"]) if mo.get("invocation") else "",
                 str(mo["verbatim"])),
              ["model_output.verbatim"])
        if mo.get("reproduces_the_stored_point_to_4dp") is True:
            s.add(obj, "This refit REPRODUCES THE POINT ESTIMATE THIS PAGE DELIVERS TO FOUR "
                       "DECIMAL PLACES. The output above is quoted as the software printed "
                       "it and is not paraphrased.",
                  ["model_output.reproduces_the_stored_point_to_4dp"])
    if not any_out and not s.paras:
        s.refusals.append(("the verbatim model output -- no analysis output is stored on "
                           "this object, so nothing can be quoted and nothing is "
                           "paraphrased in its place",
                           ["results.by_outcome.*.r_output.verbatim"]))
    secs.append(s)

    # ---- DISCUSSION / CONCLUSIONS (content gaps, refused by name) ----------------------
    for key, heading, field in (("discussion", "Discussion", "discussion"),
                                ("conclusions", "Conclusions", "conclusions")):
        s = Section(key, heading)
        _src = (field if get(obj, field)
                else ("manuscript.%s" % field if _manuscript_prose(obj, field) else None))
        _txt = (get(obj, field) if _src == field else _manuscript_prose(obj, field))
        _has = bool(_src and s.add(obj, str(_txt), [_src]))
        # THE DRAFTS, AFTER ANY AUTHORED TEXT AND AFTER THE REFUSAL DECISION.
        #
        # A topic the author has written reads as a finished paper: his prose first, and the
        # drafts still beneath it so he can see what they said. A topic he has not touched
        # reads as a full draft he can dictate over rather than an empty refusal.
        if not _has and not _drafted(obj, heading):
            s.refusals.append(("the %s -- this is a CONTENT gap. The object records no "
                               "interpretive text, and none is generated here: a %s "
                               "written by the renderer would be an argument no field "
                               "supports" % (heading, heading.lower()), [field]))
        _add_drafts(s, obj, heading)
        secs.append(s)

    # ---- SECTIONS NOT WRITTEN, AND WHY -------------------------------------------------
    # APPARATUS, NAMED AS APPARATUS. This was a heading in the article's own sequence,
    # between Trial characteristics and Submission conformance, so a reader working down the
    # paper met a section about the paper's own construction as though it were part of it.
    s = Section("not_written", "Notes on this record — sections not written, and why")
    ref = get(obj, "build_stamp.refusing")
    if isinstance(ref, list) and ref:
        s.add(obj, "This review refuses %d of the page standard's properties, by name: %s. "
                   "A refused property is a completed outcome with a stated reason, not an "
                   "omission." % (len(ref), ", ".join(str(x) for x in ref)),
              ["build_stamp.refusing"])
    else:
        s.refusals.append(("the list of refused properties", ["build_stamp.refusing"]))
    # AFTER the refusal decision, never before it. Placed at the top of the
    # section this line made `s.paras` non-empty, the `if not (s.paras or
    # s.tables)` refusal stopped firing, and six topics lost a refusal that was
    # true -- delivery 26 -> 20. A bookkeeping claim belongs in the section; it
    # must not be the thing that decides the section has content.
    _add_bookkeeping(s, obj, "which_limbs_this_review_refuses")
    secs.append(s)

    # ---- FUNDING AND CONFLICTS (content gap) -------------------------------------------
    s = Section("funding", "Funding and conflicts of interest")
    if not s.add(obj, str(get(obj, "funding") or ""), ["funding"]):
        s.refusals.append(("the funding and conflict-of-interest statement -- a CONTENT "
                           "gap. A submission requires it and this object does not carry "
                           "it; it is not inferable from anything held here", ["funding"]))
    secs.append(s)

    # ---- F1000RESEARCH MANDATORY DECLARATIONS ------------------------------------------
    #
    # Four statements the venue REQUIRES of every article. Three of them are declarations
    # ABOUT THE AUTHOR, not about the evidence: no object can hold them and no renderer may
    # invent them. "No competing interests were disclosed" is the journal's own wording for
    # the nil case, but writing it on Mahmood's behalf would be declaring something about
    # him that he has not said. They refuse by name until he answers.
    #
    # The fourth is different in kind and is DERIVED -- see below.
    for key, heading, field, what in (
            ("competing_interests", "Competing interests",
             "manuscript.competing_interests",
             "the competing-interests declaration. F1000Research requires this section on "
             "every article, and requires explicit text where there is nothing to declare. "
             "IT IS A STATEMENT ABOUT THE AUTHOR AND NOT ABOUT THE EVIDENCE: no field of "
             "this object implies it and none is invented here"),
            ("grant_information", "Grant information", "manuscript.funding_statement",
             "the grant information. The venue requires each funder's name, the grant "
             "number where applicable, and the person the grant was assigned to. None of "
             "that is derivable from a synthesis"),
            ("author_contributions", "Author contributions",
             "manuscript.author_contributions",
             "the author-contributions statement. Who did what is a fact about people, and "
             "this object records none")):
        s = Section(key, heading)
        v = get(obj, field)
        if not (v is not None and s.add(obj, _v_str(v), [field])):
            s.refusals.append((what, [field]))
        secs.append(s)

    # ---- REPORTING GUIDELINE COMPLIANCE ------------------------------------------------
    #
    # DERIVED, BECAUSE IT IS A FACT ABOUT THE REVIEW -- and derived ONLY where the review
    # can support it. F1000Research requires compliance with a consensus reporting
    # guideline; for a completed systematic review that is PRISMA 2020.
    #
    # ASSERTING PRISMA 2020 COMPLIANCE ON A TOPIC WITH NO SCREENING RECORD WOULD BE A FALSE
    # CLAIM IN A COMPLIANCE STATEMENT, which is worse than no statement: it is the exact
    # shape of the `verified: true beside a null id` defect. 93 of 155 objects carry no
    # screening block, and on those this refuses and says which item is missing.
    #
    # PRISMA-P IS NOT SUBSTITUTED. It governs PROTOCOLS, and these are completed reviews.
    s = Section("reporting_guidelines", "Reporting guidelines")
    _scr = get(obj, "screening")
    _stated = get(obj, "manuscript.reporting_guidelines")
    if _stated is not None:
        s.add(obj, _v_str(_stated), ["manuscript.reporting_guidelines"])
    elif isinstance(_scr, dict) and _scr:
        s.add(obj, "This review reports against PRISMA 2020. A screening record is held on "
                   "this object and the flow it supports is shown in the Methods. THE "
                   "COMPLETED PRISMA CHECKLIST AND FLOW DIAGRAM ARE NOT HELD HERE: the "
                   "venue requires them deposited in an approved repository with a DOI "
                   "cited in the Data Availability Statement, and minting that DOI is an "
                   "author action rather than a build step.", ["screening"])
    else:
        s.refusals.append((
            "the reporting-guideline compliance statement. PRISMA 2020 is the guideline "
            "for a completed systematic review, and THIS OBJECT CARRIES NO SCREENING "
            "RECORD, so a claim of compliance would be asserted rather than shown. It is "
            "refused rather than written, because a false statement in a compliance "
            "section is worse than an absent one", ["screening"]))
    secs.append(s)

    # ---- REGISTRATION (PROSPERO) -------------------------------------------------------
    #
    # REGISTRATION IS AN ACT WITH A DATE. A review that was not registered prospectively
    # cannot claim it, and the ABSENCE of a field is not knowledge that no registration
    # exists -- so this states the distinction rather than resolving it either way.
    s = Section("prospero", "Registration")
    _pro = get(obj, "protocol.prospero")
    if _pro is not None:
        s.add(obj, "Registered prospectively: %s." % _v_str(_pro), ["protocol.prospero"])
    else:
        s.refusals.append((
            "the registration statement. No PROSPERO registration is recorded on this "
            "object. THAT IS NOT THE SAME AS KNOWING THE REVIEW WAS NOT REGISTERED, and "
            "neither claim is made here. Prospective registration cannot be added after "
            "the fact, so if none exists the honest statement is that the review was not "
            "prospectively registered -- which is a statement only the author can make",
            ["protocol.prospero"]))
    secs.append(s)

    # ---- REFERENCES --------------------------------------------------------------------
    s = Section("references", "References")
    src = get(obj, "sources")
    # `sources` HAS TWO SHAPES IN THIS CORPUS and only one was handled:
    #   {id: {layer, name, url, ...}}   a described source
    #   {id: "evidence/....json"}       a bare path to an evidence file
    # Filtering to dict values produced ZERO rows on the second shape, so References
    # refused for want of `sources` while Data availability counted the same dict and
    # wrote -- one manuscript saying both. Found by the whole-document check, not by
    # either section. Both shapes are rendered now, and each row says which it is.
    _rows = []
    if isinstance(src, dict) and src:
        for sid, v in sorted(src.items()):
            if isinstance(v, dict):
                _rows.append([sid, str(v.get("layer", "")), str(v.get("name", ""))[:150],
                              str(v.get("url") or v.get("staged_as") or "")])
            elif isinstance(v, str) and v.strip():
                _rows.append([sid, "evidence file", "", v])
    # THE BIBLIOGRAPHY, WHICH IS NOT THE SAME OBJECT AS `sources`.
    #
    # This section refused entirely on every topic whose `sources` is empty, and `sources` is
    # a record of the provenance LAYER each fact was read at -- what an auditor re-reads, not
    # what a reader looks up. A paper with no reference list is incomplete in a way nobody
    # would defend, and it was never argument: the trials are on the object with their
    # registrations, the appraised syntheses with their PMIDs, the software with its version.
    _bib = get(obj, "manuscript.references")
    _bib_rendered = False
    if isinstance(_bib, dict):
        _inc = _bib.get("included_studies") or []
        if _inc:
            s.add_table(obj, "Included studies, by registration",
                        ["Trial", "Registration", "Registry", "Read"],
                        [[r.get("label", ""), r.get("registration", ""),
                          r.get("registry", ""), r.get("read_utc", "")] for r in _inc],
                        ["manuscript.references"])
            _bib_rendered = True
        _pub = _bib.get("published_syntheses_compared_against") or []
        if _pub:
            s.add_table(obj, "Published syntheses this review was compared against",
                        ["Citation", "Identifier"],
                        [[r.get("citation", ""), r.get("identifier", "")] for r in _pub],
                        ["manuscript.references"])
            _bib_rendered = True
        _mg = _bib.get("methods_guidance_and_software") or []
        if _mg:
            s.add_table(obj, "Methods guidance and software, with what each is cited for",
                        ["Cited for", "Reference"],
                        [[r.get("cited_for", ""), r.get("citation", "")] for r in _mg],
                        ["manuscript.references"])
            _bib_rendered = True
    if _rows:
        s.add_table(obj, "Sources this review reads, with the layer each was read at",
                    ["Id", "Layer", "Source", "Location"], _rows, ["sources"])
    elif not _bib_rendered:
        s.refusals.append(("the reference list", ["sources"]))
    if _nd:
        s.add(obj, obj[_nd].strip(), [_nd])
    secs.append(s)

    # ---- KEYWORDS (content gap) --------------------------------------------------------
    s = Section("keywords", "Keywords")
    if not s.add(obj, ", ".join(get(obj, "keywords") or []) or "", ["keywords"]):
        s.refusals.append(("the keyword list -- a CONTENT gap; no keywords are recorded "
                           "and inventing them would be indexing this review under terms "
                           "nobody chose", ["keywords"]))
    secs.append(s)

    # ---- DATA AVAILABILITY -------------------------------------------------------------
    s = Section("data_availability", "Data availability")
    ri = get(obj, "registration_identity") or {}
    trials = ri.get("trials")
    _rows = [t for t in (trials or []) if isinstance(t, dict)]
    # HOW MANY ARE KEYED IS COUNTED, NOT ASSERTED. This sentence read "Every trial in
    # this review is keyed to a registration identifier, verified by <method>" for every
    # object that had a method, including one whose own table beneath it showed a trial
    # with no identifier at all. An assertion contradicted by the content under it reads
    # as diligence, and `.get("nct", "")` returned the literal string "None" into that
    # table because a key PRESENT with a null value never reaches the default.
    _keyed = sum(1 for t in _rows if str(t.get("nct") or "").strip())
    if ri.get("method"):
        _on = (" on %s" % ri["verified_utc"]) if ri.get("verified_utc") else ""
        if _rows and _keyed < len(_rows):
            s.add(obj, "%d of the %d trials in this review are keyed to a registration "
                       "identifier and verified by %s%s. The remaining %d %s no identifier "
                       "on this object; %s recorded below as NOT_ASSESSABLE, which is not "
                       "the same as unregistered."
                  % (_keyed, len(_rows), ri["method"], _on, len(_rows) - _keyed,
                     "carries" if len(_rows) - _keyed == 1 else "carry",
                     "it is" if len(_rows) - _keyed == 1 else "they are"),
                  ["registration_identity.method", "registration_identity.trials"])
        else:
            s.add(obj, "Every trial in this review is keyed to a registration identifier, "
                       "verified by %s%s." % (ri["method"], _on),
                  ["registration_identity.method"])
    if _rows:
        def _cell(v):
            # An absent value is NOT_ASSESSABLE. Never "None", and never blank -- a blank
            # is not a complete outcome, and "None" is a Python object reaching a reader.
            t = str(v).strip() if v is not None else ""
            return t if t and t != "None" else "NOT_ASSESSABLE"

        def _reg(t):
            # A REFUSAL MUST NOT DISCARD WHAT THE OBJECT KNOWS. Rendering NOT_ASSESSABLE
            # here when the row holds `registration_id` and `registry` would tell a reader
            # the trial has no identifier, which is the opposite of what the object says:
            # LoDoCo2 is registered, on ANZCTR, and it is the ClinicalTrials.gov-shaped
            # field that cannot carry it. Unassessable VERIFICATION is not an absent id.
            if t.get("nct"):
                return _cell(t.get("nct"))
            ident, reg = t.get("registration_id"), t.get("registry")
            if ident:
                return "%s (%s)" % (ident, reg) if reg else str(ident)
            return "NOT_ASSESSABLE"
        s.add_table(obj, "Registration identifiers, and whether each was verified",
                    ["Registration", "Verified", "Link"],
                    [[_reg(t), _cell(t.get("verified")), _cell(t.get("link"))]
                     for t in _rows],
                    ["registration_identity.trials"])
    if isinstance(src, dict) and src:
        s.add(obj, "The underlying records are the %d source(s) listed under References; "
                   "each names the layer it was read at, so a reader can tell a registry "
                   "record from a published report." % len(src), ["sources"])
    if not (s.paras or s.tables):
        s.refusals.append(("the data availability statement",
                           ["registration_identity", "sources"]))
    secs.append(s)

    # ---- SOFTWARE AVAILABILITY ---------------------------------------------------------
    s = Section("software_availability", "Software availability")
    envs = sorted({(((blk or {}).get("r_output") or {}).get("_environment")
                    or ((blk or {}).get("r_output") or {}).get("environment") or "")
                   for blk in (get(obj, "results.by_outcome") or {}).values()} - {""})
    if envs:
        s.add(obj, "Analyses were computed under %s." % "; ".join(envs),
              ["results.by_outcome"])
    cl = get(obj, "config.confidence_level")
    if cl is not None:
        s.add(obj, "Intervals are reported at the %s%% level." % cl,
              ["config.confidence_level"])
    if not s.paras:
        s.refusals.append(("the software and environment statement",
                           ["results.by_outcome.*.r_output._environment",
                            "config.confidence_level"]))
    secs.append(s)

    # ---- NOTE ON REGISTRATION ----------------------------------------------------------
    s = Section("note_on_registration", "Note on registration")
    pr = get(obj, "protocol") or {}
    if pr.get("permanently_refused") or pr.get("prespecified") is not None:
        s.add(obj, "Protocol status. Prespecified: %s. %s"
              % (pr.get("prespecified"), pr.get("why") or ""), ["protocol"])
        if pr.get("what_was_actually_done"):
            s.add(obj, str(pr["what_was_actually_done"]),
                  ["protocol.what_was_actually_done"])
        if pr.get("authority_permitting_it"):
            s.add(obj, "Authority: %s" % pr["authority_permitting_it"],
                  ["protocol.authority_permitting_it"])
    else:
        s.refusals.append(("the registration note", ["protocol"]))
    # AFTER the refusal decision, never before it. Placed at the top of the
    # section this line made `s.paras` non-empty, the `if not (s.paras or
    # s.tables)` refusal stopped firing, and six topics lost a refusal that was
    # true -- delivery 26 -> 20. A bookkeeping claim belongs in the section; it
    # must not be the thing that decides the section has content.
    _add_bookkeeping(s, obj, "whether_this_review_was_prospectively_registered")
    secs.append(s)

    # ---- TABLES: TRIAL CHARACTERISTICS -------------------------------------------------
    s = Section("trial_characteristics", "Trial characteristics")
    by_id, unjoinable = _trials_by_identity(obj)
    if by_id:
        s.add_table(obj, "Characteristics of every trial contributing to this review",
                    ["Registration", "Trial", "Arms", "Participants"],
                    [[nct, str(t.get("name") or ""),
                      _arms_text(t.get("comparison") or t.get("arms")),
                      str(t.get("n") or t.get("n_total") or "not extracted")]
                     for nct, t in sorted(by_id.items())],
                    ["inputs.trials"])
    else:
        s.refusals.append(("the trial characteristics table", ["inputs.trials"]))
    if unjoinable:
        s.add(obj, "%d record(s) carry no resolvable registration identifier and are "
                   "reported here rather than dropped or matched by position: %s."
              % (len(unjoinable), "; ".join(unjoinable)), ["inputs.trials"])
    secs.append(s)

    # ---- FIGURE LEGENDS ----------------------------------------------------------------
    s = Section("figure_legends", "Figure legends")
    rows = []
    for oid, blk in sorted((get(obj, "results.by_outcome") or {}).items()):
        p = (blk or {}).get("pooled") or {}
        rows.append([outcome_text(obj, oid) or ("(no registered text held for `%s`)" % oid),
                     "Forest plot",
                     ("%s %s across %s trials"
                      % (measure_words(p.get("measure")), ci_prose(p),
                         (blk or {}).get("k", "?"))
                      if p.get("point") is not None
                      else "not pooled; the reason is given in Results")])
    if rows:
        s.add_table(obj, "Figures, and what each one shows",
                    ["Outcome", "Figure", "What it shows"], rows, ["results.by_outcome"])
    else:
        s.refusals.append(("the figure legends", ["results.by_outcome"]))
    secs.append(s)

    # ---- FIGURES -----------------------------------------------------------------------
    # The plots themselves, drawn by the SAME generator that already renders them on the
    # Analysis tab of every one of these pages. Nothing is drawn here that the object does
    # not already back, and nothing is taken from another review's document.
    s = Section("figures", "Figures")
    byo = get(obj, "results.by_outcome") or {}
    if not byo:
        # THE DEGENERATE CASE, EXCLUDED DELIBERATELY. No outcome means nothing to plot, and
        # a refusal figure here would be a figure about a result that does not exist.
        s.refusals.append(("the figures -- this object records no pooled outcome, so there "
                           "is nothing to plot and no figure is manufactured to say so",
                           ["results.by_outcome"]))
    else:
        try:
            import projectors as _pj
        except Exception:                              # noqa: BLE001 - reported, not silent
            _pj = None
        decl = dict((d["id"], d) for d in (obj.get("outcomes") or [])
                    if isinstance(d, dict) and d.get("id"))
        for oid, res in sorted(byo.items()):
            if not isinstance(res, dict):
                continue
            oc = decl.get(oid) or {}
            name = _outcome_words(obj, oid)
            base = "results.by_outcome.%s" % oid
            k = res.get("k")
            kw = k if isinstance(k, int) else "not recorded"
            # CITE WHAT ACTUALLY BACKS THE FIGURE. `base` always resolves -- we are
            # iterating it -- so a figure is never lost to a missing sub-field; the
            # sub-fields are named when they are there, and named in the reason when
            # they are not.
            src = [f for f in (base + ".per_trial", base + ".pooled")
                   if get(obj, f) is not None] or [base]

            # -- FOREST ------------------------------------------------------------------
            svg = ""
            if _pj is not None:
                try:
                    # bare=True -- the image only. The default return is an Analysis-tab
                    # CARD with its own heading and downloads, and nesting that inside a
                    # numbered <figure> gives the reader two headings and two captions for
                    # one plot. Take the logic, never the template.
                    svg = _pj.forest_svg(res, oc, bare=True)
                except Exception:                      # noqa: BLE001 - becomes the reason
                    svg = ""
            pt = [r for r in (res.get("per_trial") or []) if isinstance(r, dict)]
            usable = [r for r in pt
                      if r.get("point") and r.get("ci_low") and r.get("ci_high")]
            if not pt:
                why = ("no per-trial estimates are stored for this outcome, so there are no "
                       "rows to plot. The pooled value alone is a point, not a forest.")
            elif not usable:
                why = ("%d per-trial row(s) are stored and NONE carries a point estimate "
                       "with both interval bounds. A forest drawn from points without "
                       "intervals would show a precision the object does not hold."
                       % len(pt))
            else:
                why = ("%d per-trial row(s) carry a plottable estimate and the generator "
                       "still declined: on a log scale an interval bound at or below zero "
                       "cannot be placed on the axis." % len(usable))
            s.add_figure(
                obj,
                "Forest plot -- %s. Each contributing trial's stored estimate and interval, "
                "with the pooled result. k = %s." % (name, kw),
                svg, src, refusal=why)

            # -- FUNNEL ------------------------------------------------------------------
            # DECLINED BELOW k = 10, AND THE DECLINE IS THE POINT. The Analysis tab draws
            # this at any k with a note that it cannot be read; a manuscript figure is read
            # by reviewers as an assertion, so here it is refused with the threshold named.
            # Cochrane Handbook 13.3.5.4.
            fpan = (res.get("panels") or {}).get("funnel")
            fsvg, fwhy = "", ""
            if not isinstance(k, int) or k < 10:
                fwhy = ("k = %s. A funnel plot and its asymmetry tests have almost no power "
                        "below about ten trials (Cochrane Handbook 13.3.5.4), so a funnel "
                        "drawn here would invite a reading of asymmetry this evidence "
                        "cannot support. IT IS DECLINED RATHER THAN DRAWN, and this slot "
                        "says so where the plot would have been." % kw)
            elif not fpan:
                fwhy = ("k = %s meets the threshold, but no funnel panel is stored on this "
                        "outcome -- `%s.panels.funnel` is absent -- so the per-trial log "
                        "effects and standard errors the plot needs are not held."
                        % (kw, base))
            elif _pj is not None:
                try:
                    pooled_pt = (res.get("pooled") or {}).get("point")
                    pl = (res.get("panels") or {}).get("fit", {}).get("log_point")
                    if pl is None:
                        pl = math.log(pooled_pt) if pooled_pt and pooled_pt > 0 else 0.0
                    fsvg = _pj.funnel_svg(
                        [(x["log_effect"], x["se"], x["trial"]) for x in fpan], pl,
                        null_log=0.0,
                        measure=str((res.get("pooled") or {}).get("measure") or "Effect"),
                        k_note="k = %s." % kw)
                except Exception as _exc:              # noqa: BLE001 - becomes the reason
                    fsvg, fwhy = "", ("the stored funnel panel could not be plotted (%s). A "
                                      "broken instrument is reported, never shown as an "
                                      "absent figure." % type(_exc).__name__)
            s.add_figure(
                obj,
                "Funnel plot -- %s. Standard error against effect, with the pseudo-"
                "confidence funnel drawn from the pooled estimate. k = %s." % (name, kw),
                fsvg, src, refusal=fwhy)
    secs.append(s)

    # ---- SUBMISSION CONFORMANCE --------------------------------------------------------
    s = Section("submission_conformance", "Submission conformance")
    bs = get(obj, "build_stamp") or {}
    if bs.get("page_standard_version"):
        s.add(obj, "This review was built to page standard %s (%s), by %s on %s. A page "
                   "built below the current standard is knowably below it rather than "
                   "silently stale."
              % (bs.get("page_standard_version"), bs.get("standard_document", ""),
                 bs.get("built_by", ""), bs.get("built_utc", "")),
              ["build_stamp.page_standard_version"])
    held = bs.get("held")
    if isinstance(held, list) and held:
        s.add(obj, "Properties held: %d, by name -- %s."
              % (len(held), ", ".join(str(x) for x in held)), ["build_stamp.held"])
    if not s.paras:
        s.refusals.append(("the submission conformance statement", ["build_stamp"]))
    secs.append(s)

    if length == "concise":
        for sec in secs:
            sec.paras = sec.paras[:2]
    return _in_reading_order(secs)


# THE SECTIONS WERE EMITTED IN THE ORDER THEY WERE CODED, AND THAT IS NOT THE ORDER OF A
# PAPER. On the delivered SGLT2_HF_REVIEW.html the reader met, in this sequence:
#
#     ... Methods (5 sections), Results, Limitations, ABSTRACT, INTRODUCTION, Certainty ...
#
# Abstract ninth and Introduction tenth, AFTER the results and the limitations. Nothing was
# missing and nothing was malformed; the manuscript simply could not be read as one, and
# "reads as badly written" is the correct description of it. Every page in the corpus had
# this order, because it is the order the builders appear in this file.
#
# The fix is a declared reading order applied at the end rather than a reshuffle of the
# builders, so no section builder changes and a section that is added later and not listed
# here keeps its position relative to the rest instead of vanishing.
# THE ORDER IS THE VENUE'S, READ FROM THE VENUE. F1000Research, "Preparing a Systematic
# Review article", retrieved 2026-08-21. Its canonical element order is:
#
#     Authors / Title / Abstract / Keywords / Main Body / Data and Software Availability /
#     Reporting Guidelines / Author Contributions / Competing Interests / Grant Information /
#     Acknowledgments / Supplementary Material / References and footnotes / Figures and Tables
#
# and, verbatim, "For most Systematic Reviews, the following standard format will be the most
# appropriate: Introduction / Methods / Results / Conclusions/Discussion".
#
# THREE THINGS THE PREVIOUS ORDER GOT WRONG, and each one on its own reads as machine output:
#
#   KEYWORDS SAT AT POSITION 21, AFTER REFERENCES. The venue puts it directly after the
#   Abstract, and References AFTER the declarations rather than before them.
#
#   FIVE NON-ARTICLE SECTIONS SAT BETWEEN RESULTS AND DISCUSSION -- statistical output, risk
#   of bias, certainty, comparison with published syntheses, disagreements between sources.
#   Those are parts OF Results and OF the Discussion, not peers of them, and interleaving
#   them breaks the one structure a reader of this venue expects.
#
#   METHODS WAS FIVE SIBLING TOP-LEVEL SECTIONS rather than one. They keep their own headings
#   and their own content; they are simply consecutive now, so "Methods" reads as one thing.
#
# AND THE R CONSOLE TRANSCRIPT IS NO LONGER A NUMBERED SECTION OF THE ARTICLE. P46 limb 4
# requires it verbatim and it is not deleted or shortened -- it moves to the end, after the
# declarations, where this venue puts Supplementary Material and Extended data. Results
# references it. A `rma(yi = log(hr), sei = ...)` call with `Signif. codes: 0 '***' 0.001` in
# the body of a paper does not read LIKE computer code; in that section it IS computer code.
READING_ORDER = [
    # ---- front matter -------------------------------------------------------------------
    "title", "abstract", "keywords", "introduction",
    # ---- Main Body: Methods, as one section in five parts -------------------------------
    "methods_search", "methods_eligibility", "methods_flow", "methods_withholding",
    "methods_synthesis",
    # ---- Main Body: Results, with what belongs to it ------------------------------------
    "results", "risk_of_bias", "certainty",
    # ---- Main Body: Discussion, with what belongs to it ---------------------------------
    "discussion", "published_comparison", "disagreements", "limitations", "conclusions",
    # ---- declarations, in the venue's order ---------------------------------------------
    "data_availability", "software_availability", "reporting_guidelines",
    "author_contributions", "competing_interests", "grant_information", "funding",
    "note_on_registration", "prospero",
    # ---- references and display items ---------------------------------------------------
    "references", "figure_legends", "figures", "trial_characteristics",
    # ---- supplementary and apparatus, after everything a reader reads as the paper -------
    "statistical_output", "submission_conformance", "not_written",
]


def _in_reading_order(secs):
    """Order the emitted sections the way a paper is read.

    A key not in READING_ORDER keeps its original position by sorting on the index of the
    last listed key before it -- so an unlisted section stays where its author put it
    rather than being silently moved to the end, which would be a quiet content change
    dressed as a formatting one.
    """
    pos = {k: i for i, k in enumerate(READING_ORDER)}
    order, last = [], -1
    for n, s in enumerate(secs):
        key = getattr(s, "key", None)
        if key in pos:
            last = pos[key]
            order.append((last, 0, n))
        else:
            order.append((last, 1, n))
    ranked = [secs[n] for _, _, n in sorted(order)]
    if len(ranked) != len(secs):
        raise AssertionError("reading-order pass changed the section count from %d to %d"
                             % (len(secs), len(ranked)))
    return ranked


def render(secs, show_fields=True):
    out = []
    for s in secs:
        out.append("## %s  [%s]" % (s.heading, s.state))
        for text, fields in s.paras:
            out.append("")
            out.append(text)
            if show_fields:
                out.append("      <- %s" % ", ".join(fields))
        for caption, headers, rows, fields in getattr(s, "tables", []):
            out.append("")
            out.append("TABLE. %s  (%d row(s))" % (caption, len(rows)))
            out.append("      " + " | ".join(headers))
            for row in rows[:8]:
                out.append("      " + " | ".join(str(c)[:40] for c in row))
            if len(rows) > 8:
                out.append("      ... %d more row(s)" % (len(rows) - 8))
            if show_fields:
                out.append("      <- %s" % ", ".join(fields))
        for what, missing in s.refusals:
            out.append("")
            out.append("REFUSED: %s" % what)
            out.append("      no field: %s" % ", ".join(missing))
        out.append("")
    return "\n".join(out)


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    topic = sys.argv[1] if len(sys.argv) > 1 else "sglt2-hf"
    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with io.open(os.path.join(repo, "ssot", topic, topic + ".json"), encoding="utf-8") as fh:
        obj = json.load(fh)
    secs = project(obj)
    print(render(secs))
    w = [s.key for s in secs if s.state == WRITTEN]
    r = [s.key for s in secs if s.state == REFUSED]
    nref = sum(len(s.refusals) for s in secs)
    print("SECTIONS WRITTEN %d: %s" % (len(w), ", ".join(w)))
    print("SECTIONS REFUSED %d: %s" % (len(r), ", ".join(r) or "-"))
    print("INDIVIDUAL REFUSALS WITHIN WRITTEN SECTIONS: %d" % nref)
    return 0


if __name__ == "__main__":
    sys.exit(main())
