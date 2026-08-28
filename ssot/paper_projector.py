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

# THE ONE PLACE CERTAINTY IS RESOLVED. This module read the stored certainty directly and
# was therefore a fifth consumer outside the module built to be the single answer.
try:
    import grade_authority as _ga
except ImportError:  # pragma: no cover -- package import path
    from . import grade_authority as _ga
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


# INTERNAL PROPERTY NAMES, TRANSLATED ONCE, WHERE THEY REACH A READER.
#
# Two blind reviewers from DIFFERENT model families independently quoted the same sentence
# as one of the page's three worst passages:
#
#   "Of the four properties this project requires of a completed topic, 0 are held (none)
#    and 4 are refused with the obstacle named in the evidence (comparison denominator,
#    grade per pool, model output verbatim, rob per result)."
#
#   "Pure software debugging jargon that a clinical reader cannot parse. Terms like
#    'rob per result' expose internal data validation states rather than describing
#    clinical research methods."
#
# `rob per result` is a key. It is not English, and a clinical reader has no route to it.
# The four appear on 148 pages each. Translating them is not inventing content: each phrase
# below says exactly what the identifier already means, in words a reviewer can read.
#
# DECLARED AND ENUMERATED, like every other vocabulary in this file: an identifier not on
# this list is left exactly as it is rather than guessed at.
_PROPERTY_ENGLISH = {
    "rob per result":
        "a risk-of-bias judgement for each reported result",
    "grade per pool":
        "a GRADE certainty rating for each pooled outcome",
    "model output verbatim":
        "the statistical model's output, quoted as it was produced",
    "comparison denominator":
        "the number of published syntheses this review was compared against",
    "k cascade":
        "the count of records at each stage of screening",
}


# FIELD NAMES THAT REACH READER PROSE FROM STORED TEXT, and what they mean.
#
# These are not emitted by this projector -- they are written into the objects' own prose,
# 29 objects saying "metafor 5.0.1 run_utc 2026-08-21", 7 saying "see poolable_reason". So
# they cannot be fixed at a composition site, and rewriting the stored sentences would mutate
# records to solve a rendering problem. Translated on the way out instead, which is the same
# choice `_english_properties` and `_enums_to_english` already make.
#
# A CURATED PHRASE WHERE ONE IS NEEDED, AND UNDERSCORE-TO-SPACE AS THE SHAPE RULE FOR THE
# REST -- vocabulary for the cases we know, a property for the ones we do not, which is the
# ordering that stopped `_english_properties` going blind to `P18_restatement_is_reproducible`.
_FIELD_ENGLISH = {
    "poolable_reason": "the recorded reason this pool was declined",
    "run_utc": "run at",
    "derivation_note": "its recorded note on how the value was derived",
    "label_correction_note": "the recorded note on the label correction",
    "label_corrected_because": "the recorded reason the label was corrected",
    "label_corrected": "the recorded label correction",
    "estimand_established": "whether the estimand was established",
    "what_is_not_claimed": "what this review does not claim",
    "what_verifies_this_object": "what this review was verified against",
}

# A bare field token in prose. NOT one followed by `=`, because that is the executed search
# query quoted verbatim -- `study_type=interventional; page_size=100` is evidence a reader can
# check against the registry, and rewriting a quotation to read more smoothly would falsify it.
_FIELD_TOKEN = re.compile(r"(?<![\w./-])([a-z][a-z0-9]*(?:_[a-z0-9]+)+)(?![\w/-])(?!\s*=)")

_FIELD_KEEP = {"risk_of_bias", "p_value", "follow_up"}


def _field_names_to_english(text):
    """Bare field names in prose, as a reader would say them. Quoted queries untouched."""
    if not text:
        return text

    def sub(m):
        tok = m.group(1)
        if tok in _FIELD_KEEP:
            return tok
        if tok in _FIELD_ENGLISH:
            return _FIELD_ENGLISH[tok]
        # SPLITTING ON UNDERSCORES MAKES WORDS, AND SOME OF THOSE WORDS ARE ACRONYMS.
        #
        # `kccq_css_change` became "kccq css change", putting a lowercased KCCQ into reader
        # prose -- a NEW instance of the very class this function exists to reduce. The
        # corpus-wide count of lowercased clinical acronyms went 1 -> 2 on the rebuild that
        # shipped it, which is how it was caught: a count going UP after a fix is the fix's
        # problem until proved otherwise.
        #
        # Two rules, each correct alone, meeting at a boundary. The words coming out of the
        # split are checked against the acronym set before a reader sees them.
        return " ".join(w.upper() if w.upper() in _KEEP_CAPS else w
                        for w in tok.split("_"))

    return _FIELD_TOKEN.sub(sub, str(text))


def _english_properties(text):
    """Replace internal property identifiers with what they mean, longest first."""
    if not text:
        return text
    out = str(text)
    for key in sorted(_PROPERTY_ENGLISH, key=len, reverse=True):
        # The boundary is a LOOKAROUND, not a word-boundary escape: sent through a
        # shell heredoc that escape arrived here as a literal BACKSPACE byte (0x08),
        # the pattern matched nothing, and this function returned its input unchanged
        # while inspect.getsource printed code that looked correct. That is the class
        # .githooks/pre-push runs lint_control_chars.py for, and whose own comment
        # records it recurring eight times in one night against an author who had read
        # the rule. This was the ninth.
        out = re.sub(r"(?<![\w-])%s(?![\w-])" % re.escape(key),
                     _PROPERTY_ENGLISH[key], out, flags=re.I)

    # AND THEN BY SHAPE, because the map is a vocabulary and the corpus writes identifiers.
    #
    # Every key above is a SPACE-SEPARATED PHRASE -- "rob per result", "k cascade" -- while
    # the objects store `P18_restatement_is_reproducible`, `P6_analysis_output`,
    # `P7_published_comparison`. The map therefore matched none of them, `_english_properties`
    # returned its input untouched, and five pages published a list of our own build-property
    # identifiers as manuscript prose. A blind editor desk-rejected one of them for
    # unreadability and quoted an identifier back.
    #
    # The map handles the names we knew about; this handles the ones we did not, which is the
    # only way a translator survives a corpus that adds properties. `P18_` prefix off,
    # underscores to spaces -- a shape, not a list.
    def _shape(m):
        words = m.group("name").replace("_", " ").strip()
        return _PROPERTY_ENGLISH.get(words.lower(), words)

    return re.sub(r"(?<![\w-])P\d+_(?P<name>[A-Za-z][A-Za-z0-9_]*)(?![\w-])", _shape, out)


def _add_bookkeeping(s, obj, field):
    t, src = _bookkeeping(obj, field)
    return bool(t) and s.add(obj, _english_properties(t), src)


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


def _withdrawn_points(obj):
    """Every pooled point this object has WITHDRAWN, as the strings prose would print.

    `previous_values` is a LIST on some objects and a DICT on others, and reading it as
    one shape raises on the other. Both are accepted rather than one being declared
    correct, because nothing here is authorised to migrate a schema.
    """
    out = []
    for _oid, blk in ((obj.get("results") or {}).get("by_outcome") or {}).items():
        if not isinstance(blk, dict):
            continue
        pl = blk.get("pooled") or {}
        if not pl.get("withdrawn"):
            continue
        prev = pl.get("previous_values") or []
        if isinstance(prev, dict):
            prev = [prev]
        for pv in prev:
            if isinstance(pv, dict) and pv.get("point") is not None:
                out.append("%g" % pv["point"])
    return out


def _add_drafts(s, obj, section):
    # A STORED DRAFT CANNOT BE REACHED BY A PROJECTOR FIX, AND BOTH LOOK THE SAME ON THE
    # PAGE. These passages are prose held on the object, with the estimate BAKED INTO the
    # sentence rather than substituted at render time. So withdrawing a pooled estimate
    # nulls the point, prints the withdrawal notice, and leaves the Discussion still
    # saying "That is the estimate" about the number that was just taken down.
    #
    # MEASURED, NOT ASSUMED. Only three withdrawn pools in the corpus record a previous
    # point at all; the other hundred record none, so there is no number to leak. Two of
    # those three still asserted it in prose -- attr-pn-review, and SGLT2_HF_REVIEW,
    # whose OWN `withdrawn_note` documents this exact lesson and was written believing it
    # closed. The object was corrected. The stored prose was not.
    #
    # NOTHING HERE REWRITES THE PROSE. Deciding what a draft should say once its estimate
    # is gone is the author's, and these passages are explicitly his to replace. What is
    # not his to supply is the fact that the sentence predates the withdrawal, so the
    # marker carries it and the number stops being asserted as current.
    n = 0
    gone = _withdrawn_points(obj)
    for ck, cv, path in _drafted(obj, section):
        body = cv.get("draft", "") or ""
        stale = sorted({g for g in gone if g in body})
        # ONE SHORT MARKER, SENTENCE CASE, ONCE PER PASSAGE. The marker was longer than
        # some of the sentences it marked, shouted, and repeated for every claim.
        mark = "[Draft] "
        if stale:
            mark = ("[Draft, SUPERSEDED] This passage was written before the pooled "
                    "estimate it quotes (%s) was withdrawn, and it is shown unaltered "
                    "rather than quietly edited or dropped. The withdrawal and its "
                    "reason are in Results. The number below is NOT this review's "
                    "current estimate. " % ", ".join(stale))
        if s.add(obj, "%s%s" % (mark, body), [path]):
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


def _search_was_executed(d):
    """Was a search actually RUN against this source, or is the entry an honest absence?

    The objects in this corpus record a source that was NOT searched as a full entry with the
    name present and the execution fields marked. AZILSARTAN carries, verbatim:

        'database': 'PubMed (NCBI E-utilities esearch)',
        'query_as_executed': 'NOT EXECUTED FOR THIS TOPIC',
        'what_is_unexamined': 'NO PUBMED SEARCH WAS RUN FOR THIS TOPIC. Recorded as an
                               absence rather than omitted.'

    That is the object being scrupulous. `_source_names` then listed the name like any other
    and the abstract said "ClinicalTrials.gov API v2 and PubMed were searched" -- on a page
    whose own Methods section says, two paragraphs later, "No search was executed against
    PubMed for this topic". The object recorded the absence correctly and the projector threw
    it away one layer up, turning a disclosure into a false claim.

    Confirmed on 3 of 149 pages by a second family reading the delivered page against the
    object: AZILSARTAN_HTN, AZILSARTAN_CLD_VS_OLM_HCTZ (PubMed), COLCHICINE_CVD_CORONARY
    (anzctr). Two further pages named both sources and had genuinely run both.
    """
    if not isinstance(d, dict):
        return True
    q = str(d.get("query_as_executed") or "")
    if "NOT EXECUTED" in q.upper():
        return False
    for k in ("what_is_unexamined", "note", "status"):
        if "NO " in str(d.get(k) or "").upper() and "SEARCH WAS RUN" in str(d.get(k) or "").upper():
            return False
    return True


def _sources_run_and_not_run(dbs):
    """(names searched, names NOT searched). Both are reported; neither is dropped."""
    items = dbs.values() if isinstance(dbs, dict) else (dbs or [])
    ran, notrun = [], []
    for d in items:
        nm = d if isinstance(d, str) else (
            (d.get("database") or d.get("name") or d.get("source") or "")
            if isinstance(d, dict) else "")
        nm = str(nm).split("--")[0].strip()
        if not nm:
            continue
        bucket = ran if _search_was_executed(d) else notrun
        if nm not in bucket:
            bucket.append(nm)
    return ran, notrun


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

    SCOPING IT WAS RIGHT ABOUT `_is_value` AND WRONG ABOUT ITSELF. Keeping the wider test away
    from POOLING was correct. Keeping it away from every other PROSE site was not: the
    identical defect was live at four more composition sites and reached a reader 138 times
    across 38 delivered pages -- 76 of them Methods sentences reading "Methodological
    decisions follow not recorded on the page this object was built from, version not
    recorded on the page this object was built from", which is a claim to have followed
    guidance whose name and version are both absence markers.

    EVERY ONE OF THOSE GUARDS WAS A TRUTHINESS TEST -- `if ma.get("reference")` -- and a
    sentinel STRING is truthy, so the guard passed and the sentence was composed around the
    marker. That is fixing the instance and leaving the class. The predicate below is
    unchanged; it is now reachable by a name that says what it is for, from every prose site.
    """
    if not _is_value(v):
        return False
    s = str(v).strip().lower()
    return not any(s.startswith(p) for p in _NOT_RECORDED)


# The same predicate under the name that says what it is for. `_lead_in_has_value` stays
# because its callers use it; a new prose site should say what it means.
_prose_has_value = _lead_in_has_value


# A MARKER STANDING ALONE IS FINE; A SENTENCE BUILT AROUND ONE IS NOT.
#
# "Comparator | not recorded on the page this object was extracted from" in its own table
# cell is honest and a reader understands it -- 366 such uses on this corpus, all correct.
# The defect is a marker with prose in front of it on the same line, where a value belongs:
#
#     "Known limitation of the screen: not recorded on the page this object was extracted from"
#     "It examines 4 randomised trials and does not pool them, against not recorded on ..."
#     "Methodological decisions follow not recorded on the page this object was built from"
#
# THE SEPARATOR SET IS THE WHOLE CHECK AND IT IS WHY THIS EXISTS. A first version anchored
# on `[a-z,]` plus a literal space and therefore missed every COLON-prefixed lead-in --
# 72 instances on 38 pages, found only when an adversarial pass went looking for the sites
# the first pass had not enumerated. `\x20` and not `\s`: `\s` matches a newline, and a
# table header adjacent to its value cell then reads as one spliced sentence.
_SENTINEL_TAIL = ("not recorded", "not available", "not stated", "no record",
                  "not established", "not captured")
_SPLICED_SENTINEL = re.compile(
    r"[a-z0-9,;:.)\]–—-][\x20\u00a0]*(?:not recorded|not available|not stated|no record|"
    r"not established|not captured)[\x20\u00a0]+on the page this object was "
    r"(?:extracted|built) from", re.I)


def _splices_a_sentinel(text):
    """True when `text` composes a sentence around an absence marker."""
    return bool(text) and bool(_SPLICED_SENTINEL.search(str(text)))


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

    # CLINICAL ACRONYMS A READER OF THIS CORPUS ALREADY KNOWS.
    #
    # Measured, not guessed: 45 occurrences across ~14 pages were reaching readers in lower
    # case -- "mace", "vte", "nyha", "sglt2", and on one cardiology page "barc Type 2, 3,
    # or 5", which a blind reviewer quoted back while rejecting the paper. The case pass is
    # right to lowercase a shouted English word and wrong to touch these, and it cannot
    # tell them apart without being told which is which.
    #
    # `OR`, `PE`, `PRO` and `AS` are deliberately NOT here. Each is also an ordinary word,
    # and keeping them in capitals would shout an English word on every page that used it
    # -- the opposite defect, and a commoner one.
    "MACE", "VTE", "DVT", "NYHA", "LVEF", "EGFR", "TIMI", "GUSTO", "STEMI", "NSTEMI",
    "CABG", "ACS", "DAPT", "BARC", "KCCQ", "SGLT2", "PCSK9", "ARNI", "MRA", "ARB", "ACEI",
    "ESRD", "AKI", "DKA", "BNP", "CRP", "ICU", "ARDS", "COPD", "RSV", "HPV", "BCG",
    "SBP", "DBP", "INR", "BMI", "ALT", "AST", "TEAE", "QALY", "ICER", "SUCRA",
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


# AN ENUM IS A STORED VALUE, NOT A WORD A READER CAN READ.
#
# `_lower_single_caps` lists "anything with an underscore -- NO_INFORMATION, SOME_CONCERNS
# -- stored values" among the things it does NOT touch. Right about case-fixing, wrong about
# rendering: nothing stopped them reaching prose at all, and the live SOTAGLIFLOZIN page
# carries 48 identifier-shaped tokens -- SOME_CONCERNS x11, D5 x10, NO_INFORMATION x9, plus
# SEARCH_RECORD, REG_CTGOV, PM_VADUGANATHAN2022.
#
# Two blind reviewers from DIFFERENT model families quoted the same sentence:
#   "Domains 1 to 3 were NO_INFORMATION on all four results. D5 carried the worse-than-LOW
#    judgement in 3 results."
#   Gemini: "unparsed software constant, complete with an underscore, used as an adjective"
#   Codex:  "D5 is a label pointing at nothing for most clinical readers"
#
# TRANSLATED BY MEANING, THEN CAUGHT BY SHAPE, and that ordering is the point. The map
# handles the vocabulary we know; the SHAPE test catches what the map does not. A check that
# greps for today's four constants is the string-match-standing-in-for-a-rule failure this
# repo has hit three times today. "No identifier-shaped token in reader-facing prose" is a
# PROPERTY, testable without knowing which identifiers exist.
_ENUM_ENGLISH = {
    "NO_INFORMATION": "no information",
    "SOME_CONCERNS": "some concerns",
    "HIGH_RISK": "high risk of bias",
    "LOW_RISK": "low risk of bias",
    "NOT_ASSESSABLE": "not assessable",
    "NOT_ESTABLISHED": "not established",
    "SEARCH_RECORD": "the search record",
    "REG_CTGOV": "the ClinicalTrials.gov registration",
    "PUBLISHED_SYNTHESIS_SCREEN": "the screen of published syntheses",
}

# The four RoB 2 verdicts as a reader meets them. Note that `HIGH` and `LOW` are stored bare,
# WITHOUT the `_RISK` suffix that `_ENUM_ENGLISH` above expects -- which is precisely how a
# HIGH judgement stayed invisible to a summariser looking for the phrase "high risk of bias".
_ROB_WORDS = {
    "HIGH": "high risk of bias",
    "SOME_CONCERNS": "some concerns",
    "NO_INFORMATION": "no information",
    "LOW": "low risk of bias",
}


def _grade_derivation_words(text):
    """A stored GRADE derivation, in English. Never invents a reason not in the string.

    The stored form is the arithmetic of the rating, in field names, with an ASCII arrow:
    "start high; risk_of_bias serious (-1), imprecision serious (-1); total -2 -> low".
    That is a codebook note, and both blind reader families said so of an earlier draft
    that printed it verbatim. The reasons are what a reader needs; the arrow is not.

    ONLY THE REASONS THE STRING NAMES. An earlier version of this mapping in a prototype
    glossed "imprecision" as "imprecision -- the intervals remain wide", and three reviewers
    disputed it against HR 0.72 (0.62 to 0.82) because it was a characterisation nobody had
    recorded. For an audience that cannot tell our additions from the trials' own findings,
    an unsourced gloss is worse than terse.
    """
    t = str(text or "").lower()
    if not t.strip():
        return ""
    named = []
    for key, english in (("risk_of_bias", "risk of bias"), ("risk of bias", "risk of bias"),
                         ("imprecision", "imprecision"),
                         ("inconsistency", "inconsistency"),
                         ("indirectness", "indirectness"),
                         ("publication_bias", "publication bias"),
                         ("publication bias", "publication bias")):
        if key in t and english not in named:
            named.append(english)
    if not named:
        return ""
    return "rated down for " + _and_list(named)


def _title_reference(obj):
    """A short way to refer back to a title too long to repeat, or None.

    THREE TOPICS CARRY A TITLE THAT IS A PIPE-JOINED LIST OF REGISTRY OUTCOME NAMES --
    "Multiple trial-declared outcomes: Participants With Any Event From the Composite of
    Death From Vascular Causes, Myocardial Infarction (MI), and Stroke | Number of Subjects
    Reaching the Composite Endpoint of ... | Number of Participants With barc Type 2, 3, or
    5". The title itself is honest: those trials really did declare different outcomes, and
    naming them all is the finding. What is not honest is repeating fifty words of it SEVEN
    TIMES down one page, which is what a blind reviewer counted before rejecting it: "A
    human would define the endpoints once and subsequently refer to them as the composite
    outcomes."

    So the title is stated in full, once, where a title belongs. Everywhere else refers to
    it. The reference COUNTS the parts rather than characterising them, because counting is
    something the string supports and summarising is not -- calling three different
    composites "the composite outcome" would assert the very sameness this review exists to
    deny.
    """
    t = " ".join(str(get(obj, "title") or "").split())
    if not t:
        return None
    parts = [p.strip() for p in t.split("|") if p.strip()]
    if len(parts) > 1:
        return ("the %s trial-declared outcomes named in the title"
                % _NUMBER_WORDS.get(len(parts), str(len(parts))))
    if len(t.split()) > 25:
        return "the review question stated in the title"
    return None


_NUMBER_WORDS = {2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven",
                 8: "eight", 9: "nine", 10: "ten"}


def _state_a_long_title_once(secs, obj):
    """Replace every repeat of an over-long title with a short reference to it.

    Runs after composition, so it catches the title wherever it reached -- the abstract's
    question, the introduction, a results lead, a figure legend -- without each of those
    sites having to know it was doing it. Several of them interpolate the title through the
    `question` field rather than directly, so a fix applied at the composition sites would
    have missed exactly the ones a reader complained about.
    """
    ref = _title_reference(obj)
    if not ref:
        return secs
    full = " ".join(str(get(obj, "title") or "").split())

    # MATCHED CASE-INSENSITIVELY, BECAUSE THE TIDY HAS ALREADY BEEN OVER IT. The stored
    # title for acs-antiplatelet-review says "BARC Type 2, 3, or 5"; by the time it reaches
    # a paragraph the case pass has written "barc". An exact match therefore found the
    # title NOWHERE on the page it was repeated across seven times -- a substitution keyed
    # to the raw field cannot see text that a later pass has legitimately altered.
    pat = re.compile(re.escape(full), re.I)
    seen = [False]                       # the first occurrence is the title itself

    def fix(text):
        if not pat.search(text):
            return text
        if not seen[0]:
            seen[0] = True
            m = pat.search(text)
            head, kept, tail = text[:m.start()], text[m.start():m.end()], text[m.end():]
            return head + kept + pat.sub(ref, tail)
        return pat.sub(ref, text)

    for s in secs:
        s.paras = [(fix(t), f) for t, f in s.paras]
        s.tables = [(fix(cap), hdrs, [[fix(str(c)) for c in row] for row in rows], f)
                    for cap, hdrs, rows, f in s.tables]
    return secs


def _clinical_gaps(obj):
    """The things a clinician needs that this object does not hold. Measured per topic.

    MEASURED, NOT LISTED. A fixed sentence saying "no harms, no absolute effects, no
    follow-up" would be true of most of this corpus and false of the rest, and a claimed
    absence that is not real is the same defect as a real absence that goes unclaimed -- a
    prototype of this report told readers "No certainty rating is held for these outcomes"
    on a topic that rated every outcome, because it probed the wrong key. So each clause is
    checked against the object and appears only if the field is genuinely empty.

    The four here are the four that five blind reviewers, across two model families,
    independently said stopped them acting on the review.
    """
    trials = [t for t in ((obj.get("inputs") or {}).get("trials") or [])
              if isinstance(t, dict)]
    blks = [b for b in ((obj.get("results") or {}).get("by_outcome") or {}).values()
            if isinstance(b, dict)]
    rows = [r for b in blks for r in (b.get("per_trial") or []) if isinstance(r, dict)]

    def any_key(dicts, keys):
        return any(d.get(k) not in (None, "", [], {}) for d in dicts for k in keys)

    # WHICH QUANTITIES THIS OUTCOME TYPE CAN EVEN HAVE. A mean difference in mmHg
    # has no events in each arm and no number needed to treat -- a mean difference
    # IS an absolute effect. Asking for them named an absence that cannot be
    # filled, which is the same defect as a claimed absence that is not real, in
    # the other direction: it tells a clinician the review is missing something
    # the outcome type never had. Measured from the pooled measures, so a page
    # carrying both a hazard ratio and a mean difference still asks for events.
    _measures = {str((b.get("pooled") or {}).get("measure") or "").upper()
                 for b in blks if isinstance(b.get("pooled"), dict)}
    _measures |= {str(r.get("measure") or "").upper() for r in rows}
    _measures.discard("")
    _COUNTABLE = {"HR", "RR", "OR", "IRR", "RD", "PETO OR", "RATE RATIO", "RATIO"}
    _has_countable = bool(_measures & _COUNTABLE) or not _measures

    # THE ARMS ARE THE OTHER PLACE EVENT COUNTS LIVE, and probing only `per_trial` walked this
    # function into the exact failure its own docstring warns about: it probed the wrong key.
    #
    # Measured 2026-08-28 at origin/main e3a9c964b: of 141 objects carrying a results block,
    # 38 hold arm-level event counts at inputs.trials[*].arms[*].events while holding none of
    # the per_trial keys below -- so each was telling a clinician "this review does not give
    # you the number of events in each arm" on a page that gives exactly that. On
    # ablation-af-medical-therapy all 3 of 3 trials carry them: CASTLE-AF 51/179 vs 82/184,
    # CABANA 89/1108 vs 101/1096, RAFT-AF 50/214 vs 64/197.
    #
    # A FALSE DENIAL IS THE HARDER HALF TO SEE. Every detector here looks for a page claiming
    # too much; a page claiming too LITTLE reads as modesty and passes. This clause was
    # generating that defect rather than catching it.
    _arm_events = any(a.get("events") is not None
                      for t in trials for a in (t.get("arms") or [])
                      if isinstance(a, dict))
    gaps = []
    if _has_countable and not _arm_events and not any_key(
            rows, ("events_int", "events_ctrl", "e_int", "e_ctrl",
                   "events", "n_events", "treatment_evaluable",
                   "control_evaluable")):
        gaps.append("the number of events in each arm")
    if _has_countable and not any_key(blks, ("absolute", "risk_difference", "nnt",
                                             "absolute_effect", "control_risk",
                                             "baseline_risk", "cer")):
        # A LIST ITEM CANNOT CARRY ITS OWN "and so" -- inside `_and_list` it rendered as
        # "any absolute effect, and so no number needed to treat, how long participants
        # were followed and any measure of harm", which reads as four items or five
        # depending on where the eye lands.
        gaps.append("any absolute effect or number needed to treat")
    if not any_key(trials, ("follow_up", "median_follow_up", "duration",
                            "follow_up_months", "registered_primary_timeframe")):
        gaps.append("how long participants were followed")
    if not (obj.get("harms") or obj.get("adverse_events")
            or any("adverse" in str(o.get("name", "")).lower()
                   or "harm" in str(o.get("name", "")).lower()
                   or "safety" in str(o.get("name", "")).lower()
                   for o in (obj.get("outcomes") or []) if isinstance(o, dict))):
        gaps.append("any measure of harm")
    return gaps


def _trial_population(obj, nct, trial):
    """Who this trial studied, in its own words. Never invented, never inferred.

    The population is held in two places and neither is reliably populated: per trial
    (`inputs.trials[].population`, 5 of 50 topics) and per RESULT
    (`results.by_outcome[].per_trial[].population`, 24 of 50). The per-result text is the
    richer of the two -- "adults with type 2 diabetes, chronic kidney disease with an
    estimated glomerular filtration rate of 25 to 60, and cardiovascular risk; heart failure
    was NOT an entry requirement" -- so where a trial record holds nothing, the result rows
    for that same registration are read instead.

    Rows are matched by NCT and nothing else. Matching by position is how a population
    description ends up under the wrong trial, and a wrong population is worse than none.
    """
    own = " ".join(str(trial.get("population") or "").split())
    if own:
        return own
    seen = []
    for blk in ((obj.get("results") or {}).get("by_outcome") or {}).values():
        if not isinstance(blk, dict):
            continue
        for r in blk.get("per_trial") or []:
            if not isinstance(r, dict):
                continue
            if str(r.get("nct") or r.get("trial_id") or "").strip() != str(nct).strip():
                continue
            t = " ".join(str(r.get("population") or "").split())
            if t and t not in seen:
                seen.append(t)
    # THE REGISTRY'S OWN CONDITION LIST, where no summary exists. 18 pooled results were
    # delivered with NO population on any contributing row, which is what made it impossible
    # for anyone -- including the student checking us -- to judge whether the pool combined
    # patients who belong together. Registry wording is worse prose and better evidence: a
    # reader can open the registration and find the same words, which they cannot do with a
    # summary written here.
    if not seen:
        for blk in ((obj.get("results") or {}).get("by_outcome") or {}).values():
            if not isinstance(blk, dict):
                continue
            for r in blk.get("per_trial") or []:
                if not isinstance(r, dict):
                    continue
                if str(r.get("nct") or r.get("trial_id") or "").strip() != str(nct).strip():
                    continue
                c = " ".join(str(r.get("registered_conditions") or "").split())
                if c and c not in seen:
                    seen.append("registered condition: " + c)
    if not seen:
        return "not recorded"
    # ONE TRIAL, ONE POPULATION. Where results disagree about who was studied that is
    # itself worth a reader's attention, so both are shown rather than the first taken.
    return seen[0] if len(seen) == 1 else " / ".join(seen)


def _second_assessor_tally(obj):
    """(a2_counts, n_disagree, has_adjudication) or (None, 0, False) if single-assessor.

    ASSESSOR 1'S TALLY IS NOT THE REVIEW'S FINDING when a second assessor exists and no
    adjudication has been performed. On sotagliflozin-hf the stored overalls are
    {HIGH: 3, SOME_CONCERNS: 1} and assessor 2's are {SOME_CONCERNS: 2, NO_INFORMATION: 2}
    -- the two agree on ZERO of four -- and the page reported the first tally as what the
    review assessed while stating on the same page that there is no adjudication.
    """
    import collections as _c
    rb = obj.get("risk_of_bias") or {}
    sa = None
    for k, v in rb.items():
        if k.upper().startswith("SECOND_ASSESSOR") and isinstance(v, dict):
            sa = v
            break
    if not sa:
        return None, 0, False
    by = rb.get("by_outcome") or {}
    sole = list(by.keys())[0] if len(by) == 1 else None
    a2 = {}
    for line in str(sa.get("verbatim_reply") or "").splitlines():
        head = line.split()[0] if line.split() else ""
        if "__" in head:
            ident, oc = head.split("__", 1)
        elif head and sole:
            ident, oc = head, sole
        else:
            continue
        m = re.search(r"OVERALL=([A-Z_]+)", line)
        if m:
            a2[(oc, ident)] = m.group(1)
    if not a2:
        return None, 0, False
    counts = _c.Counter(a2.values())
    dis = 0
    for oc, per in by.items():
        if not isinstance(per, dict):
            continue
        for nct, rec in per.items():
            if isinstance(rec, dict) and a2.get((oc, nct)):
                if (rec.get("overall") or "") != a2[(oc, nct)]:
                    dis += 1
    return counts, dis, bool(rb.get("adjudication"))


def _rob_distribution(obj):
    """The stored risk-of-bias verdicts, counted. Returns (counts, n, unit-word).

    READS THE JUDGEMENTS. Does not read prose, and cannot be fooled by a sentence that
    discusses a verdict without being one.

    Per-RESULT overall verdicts are preferred, because "assessed at the level of each
    reported result" is the claim the summary makes and the overall verdict is what that
    level holds. Only where no overall verdict exists does this fall back to per-domain
    judgements, and it says which it counted so the two can never be confused: four results
    and twenty domains are different denominators for the same assessment, and reporting one
    under the other's name is how "3 of 4 results at HIGH" became invisible.
    """
    rob = obj.get("risk_of_bias")
    if not isinstance(rob, dict):
        return {}, 0, ""

    def norm(v):
        t = str(v or "").strip().upper().replace(" ", "_")
        if t in ("HIGH_RISK", "HIGH_RISK_OF_BIAS"):
            t = "HIGH"
        if t in ("LOW_RISK", "LOW_RISK_OF_BIAS"):
            t = "LOW"
        return t if t in _ROB_WORDS else ""

    overalls, domains = [], []
    for _oid, per in (rob.get("by_outcome") or {}).items():
        if not isinstance(per, dict):
            continue
        for _rid, rec in per.items():
            if not isinstance(rec, dict):
                continue
            v = norm(rec.get("overall") or rec.get("rating"))
            if v:
                overalls.append(v)
            for _dn, d in (rec.get("domains") or {}).items():
                if isinstance(d, dict):
                    dv = norm(d.get("judgement"))
                    if dv:
                        domains.append(dv)

    chosen, unit = (overalls, "results") if overalls else (domains, "domain judgements")
    if not chosen:
        return {}, 0, ""
    counts = {}
    for v in chosen:
        counts[v] = counts.get(v, 0) + 1
    return counts, len(chosen), (unit if len(chosen) != 1 else unit.rstrip("s"))


_ROB_DOMAIN_ENGLISH = {
    "D1": "the randomisation process",
    "D2": "deviations from the intended intervention",
    "D3": "missing outcome data",
    "D4": "measurement of the outcome",
    "D5": "selection of the reported result",
}
_IDENTIFIER_SHAPED = re.compile(
    r"(?<![\w-])(?:[A-Za-z][A-Za-z0-9]*_[A-Za-z0-9_]+|D[1-5])(?![\w-])")


def _enums_to_english(text):
    """Translate stored enum values into clinical language, longest name first."""
    out = str(text)
    for table in (_ENUM_ENGLISH, _ROB_DOMAIN_ENGLISH):
        for key in sorted(table, key=len, reverse=True):
            out = re.sub(r"(?<![\w-])%s(?![\w-])" % re.escape(key), table[key], out)
    return out


# CITATION KEYS ARE IDENTIFIERS TOO, AND THEY COME THROUGH A DIFFERENT PIPE.
# PM_VADUGANATHAN2022, OA_SOLOIST2021, FDA_LABEL_INPEFA, EMA_ZYNQUISTA -- nine of them
# survived the enum fix because the source list does not pass through `_tidy`. Same rule,
# different path, which is the shape of nearly every recurrence in this codebase. A source
# key names a reference a reader can already see in References; in prose it is noise.
_CITATION_KEY = re.compile(
    r"(?<![\w-])(?:PM|OA|FDA|EMA|REG|DOI|PMC)_[A-Z0-9_]+(?![\w-])")


def strip_citation_keys(text):
    """Remove source keys from prose, and repair what removing them leaves behind.

    A NAIVE STRIP MAKES A NEW DEFECT. "Compared with PM_VADUGANATHAN2022 and OA_SOLOIST2021"
    became "Compared with and," -- the keys went and their connectives stayed, which is
    worse than the identifiers were. Deleting a noun leaves a hole where the sentence
    expected one.

    So: strip, repair the joins, and DROP any sentence that had nothing in it but source
    keys. A sentence whose whole content was a list of reference labels has nothing to say
    to a reader once the labels are gone, and the references themselves are in References.
    """
    out = re.sub(r"\s*\(?%s\)?" % _CITATION_KEY.pattern, "", str(text or ""))
    # Repair the joins the removal left. Order matters: collapse the doubled connective
    # first, then drop a preposition that now governs nothing. "Compared with PM_X and
    # OA_Y, ..." went to "Compared with and, ..." and then to "Compared with, ..." -- the
    # second is better than the first and still visibly broken, so the dangling
    # preposition goes too and the clause that opened it goes with it.
    out = re.sub(r"\b(with|to|against|and|versus|from|by)\s+(and|,)\s*", r"\1 ", out)
    out = re.sub(r"\b\w+\s+(?:with|to|against|from|by|versus)\s*,\s*", "", out)
    out = re.sub(r"\b(with|to|against|from|by|versus)\s*([.,;])", r"\2", out)
    out = re.sub(r"\s+,", ",", out)
    out = re.sub(r",\s*,+", ",", out)
    out = re.sub(r"\(\s*\)", "", out)
    out = re.sub(r"\s{2,}", " ", out)
    # Drop sentences left with no substance -- BUT ONLY WHERE THIS FUNCTION EMPTIED THEM.
    #
    # THE RULE WAS RIGHT AND ITS SCOPE WAS NOT. "A sentence whose whole content was a list
    # of reference labels has nothing to say once the labels are gone" is true, and an
    # under-four-words test is a fair proxy FOR THAT CASE. Applied to every string reaching
    # `_tidy`, it deletes any short value that never contained a citation key at all:
    #
    #     _tidy("Meropenem")               -> ''   a review title
    #     _tidy("HIV-1 seroconversion")    -> ''   an outcome name
    #     _tidy("early clinical response") -> ''   an outcome name
    #     _tidy("excluded")                -> ''   a screening decision
    #
    # Measured by wrapping `_tidy` and projecting the whole corpus: 20 distinct values, 33
    # occurrences, every one a real value that reached a reader as nothing.
    # meropenem-auto-full-review renders an EMPTY Title section with no refusal beside it --
    # and a blank reads as "nothing to report" rather than as an error, so nobody
    # investigates it. That is what makes this worse than a wrong value.
    #
    # It already shipped once at scale: routing a screening verdict through the escaper,
    # which applies `_tidy`, turned 501 wrong decisions into 501 blank ones.
    #
    # So the drop applies only when the input actually carried a citation key. A fragment
    # this function did not touch is returned as it arrived; it is not this function's to
    # judge.
    _had_keys = bool(_CITATION_KEY.search(str(text or "")))
    kept = []
    for part in re.split(r"(?<=[.?!])\s+", out):
        p = part.strip()
        if not p:
            continue
        words = [w for w in re.findall(r"[A-Za-z]{2,}", p)]
        if len(words) < 4 and _had_keys:
            continue
        kept.append(re.sub(r"\b(with|and|to|against)\s*\.", ".", p))
    return " ".join(kept).strip()


def identifier_tokens(text):
    """Every identifier-shaped token still present; empty means the prose is clean.

    Exported so a gate can assert the PROPERTY rather than re-listing the vocabulary.
    """
    return [m.group(0) for m in _IDENTIFIER_SHAPED.finditer(str(text or ""))]


def _tidy(text, protect=()):
    if not isinstance(text, str):
        text = str(text)
    text = _SELF_NARRATION.sub(" ", text)
    text = _enums_to_english(text)
    text = _field_names_to_english(text)
    text = strip_citation_keys(text)
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
        """Emit `text` only if EVERY field it cites resolves. Otherwise record the refusal.

        AND NEVER EMIT A SENTENCE BUILT AROUND AN ABSENCE MARKER. See `_splices_a_sentinel`
        below: this is the LAST line, not the first. The per-site guards are still the
        right fix and are still there; this exists because I fixed four sites Codex found
        and declared the class closed, and an adversarial pass found 72 more instances live
        on 38 pages in a form none of those four guards covered. A defect population is
        bounded by where you looked, and the way to stop paying that repeatedly is a check
        that does not depend on having enumerated the sites.
        """
        if _splices_a_sentinel(text):
            self.refusals.append(
                ("a sentence that would have been composed around an absence marker -- the "
                 "field it needed records only that it was never recorded", list(fields)))
            return False
        missing = [f for f in fields if get(obj, f) is None]
        if missing:
            # A REFUSAL WITH NO SUBJECT IS THE DEFECT THIS BRANCH USED TO SHIP.
            # `text` is composed by the caller from the very fields being checked, so when
            # the field is absent the caller often hands us the empty string -- and the
            # page then rendered a bare "Refused:" with nothing after it, 2 times on each
            # of 145 pages. That is worse than silence: this project's whole contract with
            # a reader is that an absent section is named, so the reader can tell an absent
            # procedure from an unmentioned one. A refusal that names nothing breaks
            # exactly that promise while looking like it is keeping it.
            #
            # NAMING THE SECTION IS NOT INVENTING CONTENT. The heading is already on the
            # page directly above; repeating it in the refusal asserts nothing the object
            # does not already say, and the missing field is still listed as the evidence.
            what = _tidy(text)
            what = what[:70] + ("..." if len(what) > 70 else "")
            if not what.strip():
                what = "the %s section -- nothing on this object composes it" % (
                    (self.heading or self.key or "unnamed").strip().lower())
            self.refusals.append((what, missing))
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
        # A TABLE IS PROSE TOO, AND `add` GOT THIS GUARD WHILE `add_table` DID NOT.
        # I put the structural sentinel check in `Section.add` and called the class closed;
        # an adversarial sweep pointed out this method sits beside it, refuses on the same
        # terms, and has no such check. A caption composed around an absence marker is the
        # same defect as a paragraph composed around one, and a table asserts MORE than a
        # sentence because it is read with more trust.
        if _splices_a_sentinel(caption):
            self.refusals.append(
                ("a table whose caption would have been composed around an absence marker",
                 list(fields)))
            return False
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
    """`random` and `fixed` are half a name. The page read "pooled under random".

    AND THE FIX FOR THAT LEFT A SECOND HALF-NAME BEHIND, on more pages than the first.
    The branch below for an ALREADY-HYPHENATED value added the article and not the noun, so
    the corpus's commonest stored value -- `random-effects`, held on 104 outcomes against 13
    for `random` -- rendered as "pooled under a random-effects", a modifier with nothing to
    modify. It reached 80 built pages and 0 objects, because it is composed here.

    IT SURVIVED THE GATE WRITTEN FOR EXACTLY THIS DEFECT. `gate_paper_reads_as_prose`'s
    LOST_TAIL is `\\bpooled under (random|fixed)\\b(?!-|\\s*effects?)`, which cannot match
    once an article sits between "under" and "random". The gate exits 0 on every one of the
    80. A vocabulary-bound check does not see the same defect in different words, and the
    first repair here is what put it into different words.

    So the noun is now REQUIRED on every branch rather than spelled out on some of them.
    """
    t = (_v_str(model) or "").strip()
    low = t.lower()
    if low in ("random", "random effects", "randomeffects"):
        return "a random-effects model"
    if low in ("fixed", "fixed effect", "fixed effects", "common", "common effect"):
        return "a fixed-effect model"
    if low.startswith("random-effects") or low.startswith("fixed-effect"):
        out = t if low.startswith("a ") else "a " + t
        # The noun, on the branch that forgot it. Checked rather than appended blindly, so
        # a value that already carries one ("a random-effects model") is not doubled.
        if not re.search(r"\b(model|analysis|meta-analysis|synthesis)\b", out, re.I):
            out += " model"
        return out
    return t


def _live_certainty(obj):
    """The GRADE rating, from the GRADE record, over outcomes the review actually publishes.

    THE ABSTRACT PUBLISHED "certainty of the evidence was high" WHILE GRADE HELD LOW. It read
    `results.by_outcome.<first key>.grade.certainty`, which on sglt2-hf is a stale block on the
    WITHDRAWN outcome reading "start high; no downgrades". Two defects at once: the wrong field,
    and selecting the first outcome in KEY ORDER without asking whether it is one the review
    publishes. Either alone was enough to put a wrong rating in front of a reader.
    """
    # AND IT WAS STILL A RAW READ, WHICH IS THE NINTH CONSUMER. The fix above corrected WHICH
    # outcomes it reads and WHICH field, but it still took the level straight off the object
    # instead of asking the module built to be the single answer. Measured across every
    # rendering surface on 2026-08-27: this line put a certainty level on 20 pages whose
    # other surfaces withhold one, and it is the whole of that 20.
    #
    # It also retires an earlier claim of mine. I reported ZERO conflicting levels; that
    # comparison read the Summary of Findings against the certainty column and no other
    # surface. Reading all of them finds one page showing two different levels outright --
    # sglt2-hf, "high" on the GRADE card against "low" here -- and 20 showing a level where
    # another surface withholds it.
    res = (obj.get("results") or {}).get("by_outcome") or {}
    grade = ((obj.get("grade") or {}).get("by_outcome") or {})
    vals = []
    for oid in sorted(set(grade) | set(res)):
        g = grade.get(oid)
        pooled = (res.get(oid) or {}).get("pooled")
        if not isinstance(pooled, dict) or pooled.get("point") is None or pooled.get("withdrawn"):
            continue
        r = _ga.resolve(obj, oid)
        if r["state"] != "RATED" or not r.get("level"):
            # PENDING, NOT_ASSESSED, WITHDRAWN and DISAGREEMENT all mean the same thing to
            # this sentence: there is no level to state. Skipping them silently would let a
            # partial set speak for the whole, so a single withheld outcome suppresses the
            # summary entirely rather than averaging over what is left.
            return None
        vals.append(str(r["level"]).replace("_", " ").lower())
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


def _short_names(obj):
    """A short label per outcome, established once and reused. {oid: (full, short)}.

    ABBREVIATION IS A CAPABILITY, NOT A FIND-AND-REPLACE. Zelniker names "major adverse
    cardiovascular events (myocardial infarction, stroke, or cardiovascular death)" ONCE and
    says "major adverse cardiovascular events" for the rest of the paper. Stern defines
    "community-acquired pneumonia (CAP)" once and uses CAP thereafter. Both introduce the
    term with its definition attached, then rely on it.

    We projected the stored label every single time, so the SOTAGLIFLOZIN page repeated
    "total occurrences of cardiovascular death, hospitalization for heart failure and urgent
    heart failure visit" at every mention. A blind reviewer: "unbearably repetitive and
    structurally torturous... states the exact same rating three times while spelling out
    massive outcome strings in full."

    THE SHORT FORM IS DERIVED FROM THE STORED NAME, never invented: the leading noun phrase
    up to the first comma or "and", which is what the trial itself called the thing. A name
    short enough already keeps its own wording and no abbreviation is introduced -- an
    abbreviation for a four-word outcome costs a reader more than it saves.
    """
    out = {}
    for o in (obj.get("outcomes") or []):
        if not isinstance(o, dict) or not o.get("id"):
            continue
        full = _tidy(str(o.get("name") or "")).strip()
        if not full:
            continue
        if len(full.split()) <= 7:
            out[o["id"]] = (full, full)
            continue
        # A SHORT FORM IS A TERM, NOT A TRUNCATION. A first attempt cut the leading noun
        # phrase and produced "Total occurrences", "that same composite", "Time to the first
        # occurrence" -- fragments, which read worse than the repetition they replace.
        #
        # We cannot mechanically derive "major adverse cardiovascular events" from a stored
        # string; that term exists in the literature and inventing one would be authorship.
        # What IS derivable is the thing that distinguishes these estimands from each other,
        # and on this corpus that is nearly always HOW THE EVENTS ARE COUNTED -- the same
        # composite appears as total events and as time to first event, and telling them
        # apart is the entire point of pages like SOTAGLIFLOZIN_HF.
        low = full.lower()
        if low.startswith("total occurrences"):
            short = "the composite counted as total events"
        elif re.match(r"time to (the )?first", low):
            short = "the composite counted as time to first event"
        elif low.startswith("percent change") or low.startswith("change from baseline"):
            short = "the change from baseline"
        else:
            head = re.split(r",| and ", full)[0].strip()
            # Only abbreviate to something that reads as a noun phrase on its own.
            short = head if 2 <= len(head.split()) <= 7 and not head.lower().startswith(
                ("time", "total", "number", "proportion", "percent")) else full
        out[o["id"]] = (full, short.rstrip(" ,."))

    # A SHORT NAME THAT IS NOT UNIQUE IS WORSE THAN NO SHORT NAME.
    #
    # On SOTAGLIFLOZIN_HF the derivation gave "the composite counted as time to first event"
    # to BOTH hfcv_first and mace3_first -- a heart-failure composite and a three-component
    # atherothrombotic endpoint, two different questions wearing one label. That is the
    # hollow-noun defect again: a name that does not identify the thing it names.
    #
    # Any short form claimed by more than one outcome is withdrawn from ALL of them, and
    # those outcomes keep their full names. Repetition is a readability cost; ambiguity is a
    # correctness one, and they are not traded against each other.
    claimed = {}
    for oid, (full, short) in out.items():
        claimed.setdefault(short, []).append(oid)
    for short, oids in claimed.items():
        if len(oids) > 1:
            for oid in oids:
                out[oid] = (out[oid][0], out[oid][0])
    return out


# =======================================================================================
# LENGTH BUDGET -- DERIVED FROM THE ANCHORS, NOT GUESSED
# =======================================================================================
# Measured on the two published reviews the blind panel rates "Well":
#
#     Zelniker, Lancet 2018     393 words     3 trials    3 outcomes
#     Stern, Cochrane 2017      550 words    17 trials    6 outcomes
#     SOTAGLIFLOZIN_HF (ours) 7,241 words     2 trials    3 outcomes
#
# Two things fall out. First, LENGTH IS ALMOST INDEPENDENT OF TRIAL COUNT: 5.7x the trials
# buys 1.40x the words, because a review is long in proportion to what it has to SAY, not
# to what it read. Second, ours is 18.4x Zelniker WITH FEWER TRIALS.
#
# Every round tonight corrected vocabulary inside a document an order of magnitude too long,
# while both model families kept saying "unbearably repetitive" and "devolves into a
# checklist of excuses" -- complaints about proportion that terminology cannot answer.
#
# The fit below reproduces both anchors within ~12%: 300 + 30/outcome + 8/trial gives
# Zelniker 414 (actual 393) and Stern 616 (actual 550). The anchors are ABSTRACTS, so the
# multiplier gives a full panel room to be fuller than an abstract while staying in the
# right order of magnitude -- roughly 600-1,200 words for a typical topic here, against
# 7,241 today.
# THE BUDGET WAS CALIBRATED FOR A DIFFERENT READER, AND THE READER HAS CHANGED.
#
# 2.0 was derived from published anchors -- Zelniker (Lancet 2018), Stern (Cochrane 2017) --
# to make these pages the length of a published review, because the acceptance test then was
# "does this read like one". That test is retired. Mahmood: "the idea is that you write the
# manuscript and then we check and rewrite it ... a lot of people doing are med students so
# unfamiliar." The output is a WORKING DRAFT a novice will check and rewrite.
#
# A journal imposes a word count. A working draft has no such constraint, and brevity in one
# actively harms the thing it is for: a student who cannot check a claim because the section
# supporting it was cut to hit a length target is a student being asked to trust us.
#
# THE OLD VALUE WAS EVICTING REAL SECTIONS. Measured page-to-page against the delivered
# corpus: 51 of 59 rebuilt pages lost numbers, and the losses were not the false placeholders
# I had assumed -- they were whole sections that step 4 dropped for length. ABLATION_AF lost
# Disagreements between sources, Reporting guidelines, Figure legends and Notes on this
# record; ACS_ANTIPLATELET the same four. Those are exactly the sections that tell an
# unfamiliar editor where the record disagrees with itself and what was not written.
#
# So the multiplier now buys room for the content the projection debt restored -- the
# participants table, the per-trial estimates on unpooled outcomes, the clinician-gaps
# paragraph -- rather than forcing them to displace it. Step 2 still drops draft scaffolding
# and validation narrative, which is OUR workings and not article content at any length.
_BUDGET_MULTIPLIER = 5.0


def _length_budget(obj):
    """Words this topic's manuscript is worth, from what it actually has to report."""
    n_out = len([o for o in (obj.get("outcomes") or []) if isinstance(o, dict)])
    n_tri = len([t for t in ((obj.get("inputs") or {}).get("trials") or [])
                 if isinstance(t, dict)])
    return int((300 + 30 * n_out + 8 * n_tri) * _BUDGET_MULTIPLIER)


# What a review is FOR. These sections are never dropped to make room; if the budget is
# tight they are what the budget is spent on.
_ESSENTIAL = {"title", "abstract", "intro", "methods_search", "methods_synthesis",
              "results", "limitations", "conclusions", "references",
              # WHO WAS STUDIED IS WHAT A REVIEW IS FOR. Five blind reviewers read a
              # sotagliflozin paper that never once said "type 2 diabetes", and named the
              # omission before anything else: "You defined the endpoints down to the
              # statistical estimand but completely forgot the patients." The population
              # was in the object the whole time and this section carries it. A budget
              # that can delete the patients is spending on the wrong things.
              "trial_characteristics"}

# Dropped FIRST and in this order when over budget. Evidenced rather than chosen: every
# item here was named by a blind reviewer as something that should not be in a journal
# article. Draft scaffolding and validation narrative go before anything else because they
# are not article content at all -- they are our workings.
_DROP_ORDER = ["drafts", "validation", "bookkeeping", "conformance", "not_written",
               "figure_legends", "extended", "keywords", "software", "reporting_guideline",
               "statistical_output", "disagreements", "reporting_guidelines"]

# SECTIONS THAT ENUMERATE WHERE A REVIEW SUMMARISES.
#
# Measured on SOTAGLIFLOZIN_HF: risk_of_bias is 1,527 words -- FORTY PER CENT of the whole
# document, and nearly four times Zelniker's entire abstract -- for a two-trial review. Stern
# covers risk of bias across SEVENTEEN trials in about forty words: "We assessed the risk of
# selection bias and attrition bias as low or unclear overall."
#
# The difference is not length discipline, it is a different operation. We print every domain
# of every result; a review states the distribution and moves on. The detail is not lost --
# it stays on the Extraction tab, where a reader who wants per-domain judgements can have
# them -- but the ARTICLE reports the shape.
#
# Summarised rather than dropped, because risk of bias is not decoration: it is the answer to
# "should a reader believe this evidence", and a review that omits it has not arrived.
_SUMMARISE = {"risk_of_bias", "published_comparison"}

# Prose that is about OUR PROCESS rather than about the evidence.
_VALIDATION_PROSE = re.compile(
    r"model famil|independent file access|second, independent assessment|"
    r"this repository|codex exec|badge this|verification rests|"
    r"each asked to find a defect|pure projection", re.I)


def _words(secs):
    n = 0
    for s in secs:
        n += len(str(s.heading).split())
        for text, _f in s.paras:
            n += len(str(text).split())
        for what, _m in s.refusals:
            n += len(str(what).split())
    return n


def _fit_to_budget(secs, obj):
    """Choose what to report. NEVER truncate -- omit whole items, keep every number.

    TRUNCATION IS THE DEFECT WE FIXED THIS MORNING: a title cut at a fixed width read
    "...Serious Bleeding, or Cardiac Arrest in Patie". Cutting mid-thought produces
    nonsense and hides that anything was cut. Selection removes a WHOLE item and leaves the
    rest intact and readable, which is the discipline a journal imposes and this projector
    has never had.

    NOTHING NUMERIC IS ELIGIBLE. Only our workings, our scaffolding and repetition are.
    """
    budget = _length_budget(obj)
    removed = []

    # 1. DRAFT SCAFFOLDING -- never article content, dropped regardless of budget. Both
    #    families named it unprompted: "it mixes manuscript prose with draft placeholders",
    #    "repeatedly exposes scaffolding". A draft is a note to the author, not to a reader.
    for s in secs:
        keep = [(t, f) for (t, f) in s.paras if not str(t).lstrip().startswith("[Draft")]
        if len(keep) != len(s.paras):
            removed.append("%d draft passage(s) in %s" % (len(s.paras) - len(keep), s.key))
            s.paras = keep

    # 2. VALIDATION NARRATIVE -- our QA process, printed inside Methods. "This object's
    #    verification rests on Two things, and neither is a badge this repository can emit
    #    about itself" was quoted back as one of the page's three worst passages.
    for s in secs:
        keep = [(t, f) for (t, f) in s.paras if not _VALIDATION_PROSE.search(str(t))]
        if len(keep) != len(s.paras):
            removed.append("%d validation passage(s) in %s"
                           % (len(s.paras) - len(keep), s.key))
            s.paras = keep

    # 3. SUMMARISE the enumerative sections. Not dropped: risk of bias answers "should a
    #    reader believe this evidence", and a review that omits it has not arrived. What
    #    goes is the per-domain, per-result enumeration; what stays is the distribution,
    #    which is what a published review reports.
    for s in secs:
        if s.key not in _SUMMARISE:
            continue
        if s.key == "risk_of_bias":
            # THIS COUNTED THE PROSE, AND THE PROSE IS NOT THE JUDGEMENTS.
            #
            # The previous version regex-matched the rendered paragraphs of this section for
            # "high risk of bias|some concerns|low risk of bias|no information" and reported
            # the tally as the review's finding. It was wrong in both directions at once, and
            # the error had a fixed sign:
            #
            #   IT COUNTED SENTENCES ABOUT JUDGING. This corpus states its own rule as "A
            #   domain that cannot be judged ... is NO_INFORMATION, never SOME_CONCERNS. A
            #   rating of SOME CONCERNS with no explanation reads as a judgement against the
            #   trial" -- method text, counted as verdicts.
            #
            #   IT COULD NOT SEE A HIGH JUDGEMENT AT ALL. Judgements are stored as the token
            #   `HIGH`; the regex wanted the phrase "high risk of bias". Nothing writes that
            #   phrase in passing, while "some concerns" and "no information" appear freely
            #   in any discussion of method -- so the count inflated the reassuring
            #   categories and silently dropped the alarming one.
            #
            # Measured live before the fix: sotagliflozin-hf stores HIGH for 3 of its 4
            # results and published "8 at some concerns, 7 at no information, 1 at low risk
            # of bias"; tigecycline-ciai stores HIGH for 3 of 3 and published "11 at no
            # information, 8 at some concerns". Both told a reader that NO result was at high
            # risk of bias. Understating risk of bias is the one direction a summary must
            # never fail in, and a phrase count fails in exactly that direction every time.
            #
            # So the distribution is READ FROM THE STORED JUDGEMENTS. If none can be read the
            # section refuses, rather than reporting a tally nothing supports.
            counts, n_results, unit = _rob_distribution(obj)
            if counts:
                order = ("HIGH", "SOME_CONCERNS", "NO_INFORMATION", "LOW")
                parts = ", ".join("%d at %s" % (counts[k], _ROB_WORDS[k])
                                  for k in order if counts.get(k))
                keep_fields = sorted({f for _t, fs in s.paras for f in fs})
                # A SINGLE ASSESSOR'S TALLY IS NOT THE REVIEW'S FINDING. Where a second
                # assessor exists and no adjudication has been performed, this sentence
                # reported assessor 1's stored overalls as what "the review assessed" --
                # on a page that simultaneously said no adjudication exists. On
                # sotagliflozin-hf the two readers agreed on ZERO of four results.
                #
                # THE INTERIM WORDING MUST NOT PICK A WINNER. Not assessor 2, not an
                # average, and not an implicit adjudication by choosing. It states that
                # two assessors read independently, that they differ, that no adjudication
                # has been performed, and that the review therefore holds NO FINAL
                # risk-of-bias judgement for these results. Both readers' judgements are
                # shown; neither is reported as the review's.
                _a2, _dis, _adj = _second_assessor_tally(obj)
                if _a2 and not _adj:
                    _a2parts = ", ".join(
                        "%d at %s" % (_a2[k], _ROB_WORDS.get(k, k.lower().replace("_", " ")))
                        for k in ("HIGH", "SOME_CONCERNS", "NO_INFORMATION", "LOW")
                        if _a2.get(k))
                    lead = ("Risk of bias was assessed with RoB 2 at the level of each "
                            "reported result, by TWO assessors reading independently. "
                            "Their judgements differ on %d of the %d %s and NO ADJUDICATION "
                            "HAS BEEN PERFORMED, so this review holds no final "
                            "risk-of-bias judgement for these results. Assessor 1 recorded: "
                            "%s. Assessor 2 recorded: %s. Both are shown in the "
                            "risk-of-bias table; neither is the review's finding."
                            % (_dis, n_results, unit, parts, _a2parts))
                else:
                    lead = ("Risk of bias was assessed with RoB 2 at the level of each "
                            "reported result. Across the %d %s assessed: %s."
                            % (n_results, unit, parts))
                # THE WORST JUDGEMENT LEADS THE LIST, which is why there is no second
                # sentence restating it. A first draft added "3 of those 4 are at HIGH risk
                # of bias" after a list already opening "3 at high risk of bias", and on
                # tigecycline that read "3 at high risk of bias. 3 of those 3 are at HIGH
                # risk of bias." Emphasis by repetition is the defect five reviewers named in
                # these papers; ordering carries it without saying anything twice.
                if (not (_a2 and not _adj)) and counts.get("HIGH") == n_results                         and n_results > 1:
                    lead += (" No result escaped that judgement.")
                lead += (" The per-domain judgements behind them are recorded with the "
                         "extracted data.")
                s.paras = [(lead, keep_fields or ["risk_of_bias"])]
                s.tables = []
                removed.append("risk_of_bias enumeration (%d judgements summarised)"
                               % sum(counts.values()))
            else:
                s.paras = []
                s.tables = []
                s.refusals.append(("the risk-of-bias distribution", ["risk_of_bias"]))
        elif s.key == "published_comparison" and len(s.paras) > 1:
            s.paras = s.paras[:1]
            s.tables = []
            removed.append("published_comparison detail")

    # 4. Whole non-essential sections, lowest value first, until inside the budget.
    for key in _DROP_ORDER:
        if _words(secs) <= budget:
            break
        for s in list(secs):
            if s.key == key and s.key not in _ESSENTIAL:
                secs.remove(s)
                removed.append("section %s" % s.key)

    # 5. Still over? Drop remaining non-essential sections in reverse document order --
    #    the back matter a reader reaches last.
    #
    # "EMPTY" ONCE MEANT `not s.paras`, AND A TABLE IS NOT A PARAGRAPH. `Section.state`
    # already defines the property correctly -- WRITTEN when paras OR tables OR figures --
    # and this loop contradicted it, so every table-only section was deletable AND the
    # removal log recorded the deletion as "empty section X" while the section held its
    # table. On sotagliflozin-hf that silently deleted `trial_characteristics`, the table
    # carrying who was studied and how many were randomised, then wrote a false reason for
    # it into our own build log. Who was studied was the single most-cited omission when
    # five blind reviewers read these papers: it had been built correctly and thrown away,
    # and the log said it was never there.
    #
    # Using the class's own predicate means the two cannot disagree again.
    for s in reversed(list(secs)):
        if _words(secs) <= budget:
            break
        if s.key not in _ESSENTIAL and s.state == REFUSED:
            secs.remove(s)
            removed.append("empty section %s" % s.key)
    return secs, budget, removed


def project(obj, journal="generic", length="standard"):
    """Return [Section]. `journal` and `length` are parameters; neither licenses a claim."""
    we = journal in ("cochrane", "plos")
    verb = "We searched" if we else "Searches were executed in"
    secs = []
    _SHORT = _short_names(obj)
    _introduced = set()

    def oname(oid, force_full=False):
        """Full name with its short form attached on first use; the short form after."""
        full, short = _SHORT.get(oid, (None, None))
        if not full:
            return None
        if full == short:
            return full
        if force_full or oid not in _introduced:
            _introduced.add(oid)
            return "%s (referred to below as %s)" % (full, short)
        return short

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
        # THE QUESTION IS STATED ONCE, IN THE ABSTRACT. It used to appear here AND as the
        # Abstract's opening "Question." line, verbatim, on 79 topics --
        # `lint_manuscript_whole_document.py` refuses that, and it is right: a paper that
        # states its question twice in its first two sections is the repetition both model
        # families kept naming. Nothing is lost by saying it once; a reader meets it in the
        # Abstract, where a reader of any journal expects it.
        s.heading = "Title"
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
        # A NON-EXECUTED SEARCH REPORTED AS AN EXECUTED ONE IS A FALSE METHODS CLAIM.
        # The stored query on seven pages is literally "Not executed for this topic", and
        # this sentence wrapped it as: "Searches were executed in PubMed on 2026-08-19 with
        # the query, verbatim: Not executed for this topic. It returned an unrecorded number
        # of record(s)." The page claims a search it also says did not happen, and
        # overstates its own bibliographic coverage to any reader who skims the Methods.
        if not _prose_has_value(q) or str(q).strip().lower().startswith("not executed"):
            txt = ("No search was executed against %s for this topic."
                   % _dflt("database", "this source"))
        else:
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
        # WORDING, NOT LOGIC. "Refused: the entire search description" sat on 129 pages
        # directly beneath a bookkeeping paragraph that had just described how the trials
        # were found -- "No bibliographic search was run. The 2 included trials were
        # identified by reading named registrations on 2026-08-18." A reader meets a
        # description of the search followed by a refusal to describe it.
        #
        # THE REFUSAL IS NOT SUPPRESSED, DELIBERATELY. The comment below records that
        # letting a bookkeeping line decide the section has content cost six topics a
        # refusal that was TRUE. So the logic is untouched and only the claim is narrowed
        # to what is actually absent: the database-search record, not the description.
        # RECONCILED BEFORE IT IS STATED, WHICH IS THE RULE THE EARLIER SPEC LACKED.
        #
        # Two absence statements were both true and could not both be said:
        #     "No bibliographic search for primary trials was run."
        #     "The executed database query, date and yield are not reported."
        # A blind reviewer quoted them back as a contradiction -- "if no search was run,
        # there is no query to report; 'not reported' implies they exist but were omitted."
        # Moving an absence to the section a reader expects does not make it coherent with
        # the OTHER absences already there. They need one account per topic, settled before
        # rendering.
        #
        # So the refusal still fires -- it is TRUE, and suppressing it is the mistake the
        # comment above records -- but it says the one thing that is the case. Where the
        # bookkeeping line already states that no search was run, this must not also imply
        # a search whose paperwork is missing.
        _bk, _ = _bookkeeping(obj, "the_search_its_date_and_its_databases")
        _no_search_stated = bool(_bk) and re.search(
            r"no bibliographic search|no search (?:was )?(?:run|executed)", str(_bk), re.I)
        if _no_search_stated:
            s.refusals.append(
                ("a database search for primary trials, which was not carried out for this "
                 "review; the included trials were identified from named registrations",
                 ["search.databases"]))
        else:
            s.refusals.append(
                ("the database-search record: no executed query is held, so no query, date "
                 "or yield can be shown", ["search.databases"]))
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
        # NOT "recorded in `prisma_flow`". A READER DOES NOT KNOW WHAT prisma_flow IS.
        #
        # 12 delivered pages -- the largest single instance of the class a blind editor
        # desk-rejected this corpus for -- told a clinical reader that counts are "recorded
        # in `prisma_flow`", which names a key in our schema and says nothing a reader can
        # act on. What they need is that the counts exist, that they reconcile, and where to
        # look, which is this page.
        #
        # The provenance is NOT removed: the field is still cited in this section's sources
        # list, which is where a reader who wants the key can find it. The rule is that a
        # field path may be REACHABLE and must not appear inside a sentence.
        s.paras.append(("The PRISMA 2020 flow counts are held for this review and reconcile "
                        "with the executed searches above; they are set out in the flow "
                        "figure and its accompanying counts.", ["prisma_flow"]))
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
    # `_prose_has_value`, NOT truthiness. `ma.get("reference")` is true for the string
    # "not recorded on the page this object was built from", which is how 76 pages came to
    # claim they followed guidance that was never recorded.
    if isinstance(ma, dict) and _prose_has_value(ma.get("reference")):
        s.paras.append(("Methodological decisions follow %s%s, and the sections relied on are "
                        "listed in the object rather than cited generically."
                        % (ma["reference"],
                           (", version %s" % ma["version"])
                           if _prose_has_value(ma.get("version")) else ""),
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
        # AN OUTCOME THAT CARRIES A GRADE CERTAINTY HAS BEEN RATED.
        #
        # This counted only blocks with a truthy `rated` FLAG. Across the 30 objects holding
        # grade.by_outcome, 13 blocks carry a `certainty` value and NO `rated` key at all --
        # so 13 pages published "0 pooled outcome(s) were rated" beside an abstract correctly
        # reporting "certainty of the evidence was low", drawn from that same certainty.
        #
        # THE ABSTRACT WAS RIGHT AND THE BODY WAS WRONG, which is the opposite of the shape
        # we have been finding all week, and I nearly fixed the abstract. What settled it was
        # reading the object: AGYW_HIV_PREP holds pooled {point 0.703, CI 0.566 to 0.873, RR}
        # with k=2 and certainty LOW. A real pool, really rated.
        _by = gr.get("by_outcome") or {}
        rated = [o for o, v in _by.items()
                 if isinstance(v, dict) and (v.get("rated") or v.get("certainty"))]
        notr = [o for o in _by if o not in rated]
        txt = ("Certainty of evidence was rated with %s, following %s. %s %d pooled outcome(s) "
               "were rated. %s" % (gr["approach"], gr.get("handbook_chapter", ""),
                                   gr.get("starting_point", ""), len(rated),
                                   gr.get("not_rated_up", "")))
        if notr:
            # AND THE REASON IS CHECKED, NOT ASSERTED. This attributed "their pool is
            # declined or withdrawn" to every unrated outcome without ever looking at the
            # result block. On the 13 pages above the pool was neither -- so the sentence
            # stated a count that was wrong AND a reason that was invented, and the invented
            # reason is what made the wrong count sound considered.
            _res = get(obj, "results.by_outcome") or {}
            _confirmed = []
            for _o in notr:
                _b = _res.get(_o) or {}
                _pool = _b.get("pooled") if isinstance(_b, dict) else None
                _declined = (not isinstance(_pool, dict)
                             or _pool.get("point") is None
                             or bool(_pool.get("withdrawn"))
                             or _b.get("poolable") is False)
                if _declined:
                    _confirmed.append(_o)
            if _confirmed:
                txt += (" %d outcome(s) were NOT rated because their pool is declined or "
                        "withdrawn: there is no effect estimate to rate the certainty of, "
                        "and rating one would be certainty about a number this review "
                        "refused to publish." % len(_confirmed))
            _other = len(notr) - len(_confirmed)
            if _other:
                txt += (" %d further outcome(s) carry no certainty rating, and this review "
                        "does not record why." % _other)
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
        # THE FIFTH CONSUMER, AND IT NEVER CALLED `resolve`. `grade_authority` says in its
        # own docstring that every surface calls it; this one reads
        # `results.by_outcome.<oid>.grade.certainty` straight off the object, so it printed
        # LOW for outcomes the certainty column had already stopped publishing. A module
        # built to be the single answer is only the single answer for the consumers that
        # ask it, and "every surface" was a claim about the four that were known.
        #
        # AND "PER POOLED OUTCOME" WAS FALSE OF ITS OWN LIST. sotagliflozin-hf's mace3_first
        # has one trial, is not pooled, and says so in three other places on the same page --
        # and it was counted here among the "pooled outcome(s)" carrying a rating. Whether an
        # outcome pooled is read per outcome now, not asserted over the list.
        per, pend = [], []
        for oid, blk in (get(obj, "results.by_outcome") or {}).items():
            if not isinstance(blk, dict):
                continue
            r = _ga.resolve(obj, oid)
            if r["state"] == "RATED":
                per.append((oid, r))
            elif r["state"] == "PENDING":
                pend.append((oid, r))
        _po = get(obj, "results.by_outcome") or {}

        def _pooled(oid):
            b = (_po.get(oid) or {}).get("pooled")
            b = b if isinstance(b, dict) else {}
            return b.get("point") is not None and not b.get("withdrawn")
        if pend:
            s.paras.append((
                "Certainty of evidence is rated per outcome rather than in a single "
                "review-level block. %d outcome(s) are PENDING and carry no published "
                "rating: %s. %s"
                % (len(pend),
                   "; ".join("%s%s" % (_outcome_label(obj, o)
                                       or ("the outcome recorded as %s, for which this "
                                           "object stores no name" % o),
                                       "" if _pooled(o) else " (not pooled)")
                             for o, _ in pend),
                   pend[0][1]["comment"]),
                ["results.by_outcome.%s.grade" % o for o, _ in pend]
                + ["risk_of_bias.by_outcome"]))
        if per:
            s.paras.append((
                "Certainty of evidence was rated per outcome rather than in a single "
                "review-level block, and %d outcome(s) carry a rating: %s. Each rating is "
                "about its own estimand and about nothing else. %s"
                # THE OUTCOME'S NAME, NOT ITS IDENTIFIER. This read "3 outcome(s) carry a
                # rating: hfcv_total LOW; hfcv_first LOW" -- schema keys in a sentence about
                # certainty. Where the object stores no name the identifier is shown AND
                # named as unlabelled, because a missing label is a missing field.
                % (len(per), "; ".join(
                    "%s%s %s" % (_outcome_label(obj, o)
                                 or ("the outcome recorded as %s, for which this object "
                                     "stores no name" % o),
                                 "" if _pooled(o) else " (not pooled)",
                                 str(r["level"]).replace("_", " ").upper())
                    for o, r in per),
                   next((str(((_po.get(o) or {}).get("grade") or {})
                             .get("what_this_certainty_is_about"))
                         for o, _ in per
                         if ((_po.get(o) or {}).get("grade") or {})
                         .get("what_this_certainty_is_about")), "")),
                ["results.by_outcome.%s.grade" % o for o, _ in per]))
        elif not pend:
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
        if _prose_has_value(comparator):
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
            if _prose_has_value(status):
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
        # A DECLINED POOL HAS ITS REASON IN ONE OF TWO FIELDS, AND THIS READ ONE.
        #
        # `poolable_reason` says why a pool was not built. `pooled.withdrawn_reason`
        # says why one that WAS built has been taken down. On 91 of 103 withdrawn
        # pooled outcomes the two hold identical text and nothing was wrong. On the
        # rest they diverge, and reading only the first is a page that does not say
        # what it knows:
        #
        #   fcm-hf-review / harmonised_cvdeath_or_hfh holds a substantive
        #   `withdrawn_reason` -- an arm inversion in the IRONMAN row moved the pool
        #   from RR 0.7987 (I2=0%) to RR 0.976 (I2=97.9%) with the two trials pointing
        #   in OPPOSITE directions -- and NO `poolable_reason`. The sentence was
        #   refused, so FCM_HF_REVIEW.html printed no reason at all while the object
        #   held one. That is the withheld-withdrawal-reason class.
        #
        # NEITHER FIELD WINS, BECAUSE NEITHER IS RELIABLY THE LATER ONE. On
        # incretin-hfpef-review the `poolable_reason` CORRECTS the `withdrawn_reason`:
        # the withdrawal text still says the page had no index card at all, and the
        # correction records that the card existed and published HR 0.41 (0.22 to 0.79)
        # but was invisible because a scan matched card links with [A-Z0-9_]+\.html,
        # which cannot match the lowercase p in HFpEF. Preferring `withdrawn_reason`
        # there would have re-published a sentence the object had already retracted.
        # On colchicine-cvd-coronary the withdrawal text is a POINTER -- "no shared
        # estimand -- see poolable_reason" -- and the substance is in the other field.
        #
        # So both are printed when both exist and they differ, attributed to the field
        # each came from. A reader meeting two accounts of the same withdrawal is
        # better served than one meeting whichever account the code happened to read.
        _pool = blk.get("pooled") or {}
        _pr = (blk.get("poolable_reason") or "").strip()
        _wr = (_pool.get("withdrawn_reason") or "").strip() if _pool.get("withdrawn") else ""
        _fields = []
        if _pr and _wr and _pr != _wr:
            reason = ("%s  AND, RECORDED SEPARATELY ON THE WITHDRAWAL ITSELF: %s"
                      % (_pr, _wr))
            _fields = ["results.by_outcome.%s.poolable_reason" % oid,
                       "results.by_outcome.%s.pooled.withdrawn_reason" % oid]
        elif _wr:
            reason = _wr
            _fields = ["results.by_outcome.%s.pooled.withdrawn_reason" % oid]
        else:
            reason = _pr or None
            _fields = ["results.by_outcome.%s.poolable_reason" % oid]
        if not name:
            s.refusals.append(("the declined-pool sentence for `%s` -- no registered outcome "
                               "text is held" % oid, ["outcomes[id=%s].name" % oid]))
            continue
        if reason:
            # "THESE 0 TRIALS ARE NOT POOLED" IS NOT A SENTENCE ANYONE CAN READ, and on a
            # page that has already said "The 2 included trials were identified by reading
            # named registrations" it reads as a flat self-contradiction. A blind reviewer
            # quoted both halves back as the document contradicting itself.
            #
            # BOTH NUMBERS ARE CORRECT AND THEY COUNT DIFFERENT THINGS: `k` is how many
            # trials contribute an ESTIMATE for THIS OUTCOME, and the 2 is how many trials
            # the review includes. The defect is the wording collapsing that distinction,
            # not the arithmetic -- so the k = 0 case says what it means instead.
            _k = blk.get("k")
            if _k in (0, "0"):
                lead = ("%s. No trial on this review contributes an estimate for this "
                        "outcome, so nothing is pooled" % (name[0].upper() + name[1:]))
            elif _k in (1, "1"):
                # "THESE 1 TRIALS" was ungrammatical on every single-trial outcome, and a
                # single-trial outcome is the commonest reason a pool is declined.
                lead = ("%s. Only one trial reports this outcome, so nothing is pooled"
                        % (name[0].upper() + name[1:]))
            else:
                lead = ("%s. These %s trials are not pooled"
                        % (name[0].upper() + name[1:], _k if _k is not None else "?"))
            s.paras.append(("%s, and the reason is stated rather than the outcome being "
                            "quietly omitted: %s" % (lead, reason),
                            ["outcomes[id=%s].name" % oid] + _fields))
            # AND THEN THE NUMBER, WHICH THIS USED TO WITHHOLD.
            #
            # Declining to pool is not a reason to withhold what the trials found. The
            # estimates are held -- 28 of the 50 topics with any readable estimate have at
            # least one on an outcome that was never pooled -- and a reader met the reason
            # for the silence and never the result behind it. Both blind families called
            # this out, one of them exactly: "You asked the question, you found the trial,
            # you assessed its bias, and then you refused to report the numbers because you
            # couldn't pool them. That is absurd."
            #
            # Reported per trial, never combined, because not combining them is the whole
            # point of the paragraph above.
            #
            # BUT NEVER FOR A POOL THAT WAS RETRACTED, and the distinction is the reason
            # this branch is not simply "print the numbers":
            #
            #   NEVER POOLED  -- one trial reports the outcome, or the trials measure
            #                    different things. Each estimate is valid FOR ITS OWN TRIAL,
            #                    and withholding it is the absurdity quoted above.
            #
            #   WITHDRAWN     -- a pool WAS computed, someone examined it, and it was
            #                    retracted. On 22 outcomes across this corpus that retraction
            #                    still leaves per-trial rows behind, and on some of them the
            #                    retraction is that THE MEASURE ITSELF IS INVALID:
            #                    netarsudil records "A HAZARD RATIO OVER A CONTINUOUS
            #                    PRESSURE"; pitavastatin "THE ENDPOINTS AGREE AND THE MEASURE
            #                    IS WRONG"; bococizumab an odds ratio derived from an
            #                    undocumented dichotomisation of a percent change. Where the
            #                    measure is the defect, the per-trial estimates carry the
            #                    SAME defective measure -- so re-publishing them beside the
            #                    retraction hands a reader the retracted quantity in
            #                    component form.
            #
            # A FIRST ATTEMPT TRIED TO TELL THE TWO APART BY READING THE REASON for phrases
            # like "MEASURE IS THE DEFECT". It caught 1 of the 3 cases and missed netarsudil
            # and pitavastatin outright -- the vocabulary-standing-in-for-a-rule failure this
            # repository has now hit four times. `withdrawn` is a PROPERTY the object states
            # about itself; the phrasing of a reason is not.
            #
            # So: a retraction is reported as a retraction, with its reason in full, and the
            # components stay on the Extraction tab where the whole record lives.
            _pooled = blk.get("pooled") or {}
            _retracted = bool(_pooled.get("withdrawn") or _pooled.get("withdrawn_reason"))
            _rows = [] if _retracted else [
                r for r in (blk.get("per_trial") or [])
                if isinstance(r, dict) and r.get("point") is not None]
            if _rows:
                _bits = []
                for r in _rows:
                    _who = str(r.get("nct") or r.get("trial_id") or "").strip()
                    _est = ci_prose(r)
                    _bits.append("%s %s%s" % (measure_words(r.get("measure")), _est,
                                              (" in %s" % _who) if _who else ""))
                # ONE TRIAL IS NOT "EACH ON ITS OWN, NOT COMBINED WITH THE OTHERS". A first
                # draft said exactly that on a single-trial outcome, which is the commonest
                # case this branch handles -- the plural apparatus has to go when there is
                # nothing to be plural about.
                if len(_rows) == 1:
                    s.paras.append(
                        ("The trial that did report it found %s." % _bits[0],
                         ["results.by_outcome.%s.per_trial" % oid]))
                else:
                    s.paras.append(
                        ("What each trial reporting it found, separately and not combined: "
                         "%s." % _sentence_join(_bits),
                         ["results.by_outcome.%s.per_trial" % oid]))
        else:
            s.refusals.append(("the reason the pool over %s is declined -- NEITHER "
                               "`poolable_reason` NOR `pooled.withdrawn_reason` is held"
                               % name,
                               ["results.by_outcome.%s.poolable_reason" % oid,
                                "results.by_outcome.%s.pooled.withdrawn_reason" % oid]))

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
        # THE ARTICLE PROMISED AN "Extended data" SECTION THAT IS NOT ON THE PAGE. The
        # string appeared exactly once in the delivered build -- in this promise. A
        # pointer to material a reader cannot reach is worse than no pointer: it reads as
        # a reproducibility affordance and spends the credit without delivering it. The
        # sentence now says where the output actually is, which is on the object.
        s.add(obj, "The full model output for every pooled outcome -- the call, the "
                   "estimator, the heterogeneity statistics and the back-transformed "
                   "interval -- is stored verbatim on this review object at "
                   "`results.by_outcome.<outcome>.r_output.verbatim`. It is NOT reproduced "
                   "as an Extended data section in this article; an earlier version of "
                   "this sentence said it was, and no such section exists.",
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
        if isinstance(v, str) and _prose_has_value(v):
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
    # WHAT A CLINICIAN WOULD NEED AND WILL NOT FIND HERE, NAMED.
    #
    # Five blind reviewers, both model families, independently reached the same place: they
    # could read the review, they believed it, and they could not act on it. "I cannot
    # prescribe a drug without absolute risk reductions"; "You gave me benefits without
    # harms, and relative metrics without absolute context." Every one of them worked that
    # out for themselves from what was missing.
    #
    # A document that states its own insufficiency is more useful than one that leaves a
    # reader to discover it, and this costs a paragraph. It is the same principle that makes
    # a withdrawn pool worth publishing: the absence is a finding, and it is stated where it
    # will be read rather than inferred from a gap.
    #
    # Measured, not assumed -- each clause appears only when the field really is absent
    # across this object, so a topic that later gains harms or follow-up stops claiming to
    # lack them.
    # ONLY WHERE THERE IS A RESULT FOR THE GAPS TO BE GAPS IN.
    #
    # A first version emitted this on every topic, including four that hold NO TRIAL AT
    # ALL, and `lint_manuscript_whole_document` refused it correctly: `trial_characteristics`
    # refuses for want of `inputs.trials` on those pages while this paragraph cited
    # `inputs.trials` as a field it had used. Two sections of one document disagreeing about
    # whether a field exists.
    #
    # The deeper error was citing a field as a SOURCE when the paragraph is about that
    # field being EMPTY. A review with nothing to report does not need a paragraph on what
    # its reporting fails to give a clinician -- it gives nothing, and says so where that
    # belongs. So this speaks only where an estimate exists, and cites only the outcome
    # block it actually read.
    _has_estimate = any(
        r.get("point") is not None
        for b in (get(obj, "results.by_outcome") or {}).values() if isinstance(b, dict)
        for r in (b.get("per_trial") or []) if isinstance(r, dict))
    _gaps = _clinical_gaps(obj) if _has_estimate else []
    if _gaps:
        s.paras.append(
            ("What this review does not give a clinician: %s. A relative effect cannot be "
             "turned into the benefit or the risk facing one patient without them, so this "
             "review can support a judgement about what these trials found and not a "
             "judgement about what to do." % _and_list(_gaps),
             ["results.by_outcome"]))
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
        # NAME WHAT RAN AND WHAT DID NOT. Listing every entry regardless of whether its
        # search executed is what turned an honest object into a false abstract; silently
        # DROPPING the unexecuted ones would be the other failure -- deleting an absence to
        # buy a cleaner sentence. Both are said.
        _ran, _notrun = _sources_run_and_not_run(_dbs)
        if _ran:
            _mparts.append("%s %s searched"
                           % (_and_list(_ran), "were" if len(_ran) > 1 else "was"))
            _mfields.append("search.databases")
        if _notrun:
            _mparts.append("no search was executed against %s" % _and_list(_notrun))
            _mfields.append("search.databases")
    _elig = get(obj, "screening.eligibility")
    if _prose_has_value(_elig):
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
    # A TOOL NAME IS NOT AN ASSESSMENT, AND AN APPROACH NAME IS NOT A RATING.
    #
    # `risk_of_bias.tool` holding the string "RoB 2" says which instrument WOULD be used.
    # It does not establish that anyone applied it. Nine pages carried the abstract sentence
    # "risk of bias was assessed with RoB 2; and certainty was rated with GRADE" while the
    # SAME PAGE said "No per-domain RoB-2 assessment is stored" and "Risk-of-bias traffic
    # light -- not computable". That is the defect this whole project exists to prevent,
    # committed in its own abstract: a methods claim with nothing behind it.
    #
    # The claim now requires the ASSESSMENT to exist, not merely its label.
    _tool = get(obj, "risk_of_bias.tool")
    if _tool is not None and get(obj, "risk_of_bias.by_outcome") is not None:
        _mparts.append("risk of bias was assessed with %s" % _v_str(_tool))
        _mfields.append("risk_of_bias.by_outcome")
    _gr = get(obj, "grade.approach")
    if _gr is not None and get(obj, "grade.by_outcome") is not None:
        _mparts.append("certainty was rated with %s" % _v_str(_gr))
        _mfields.append("grade.by_outcome")
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
    # AN AGREEMENT STATISTIC ABOUT A POOL THE ABSTRACT DOES NOT PRESENT.
    #
    # This was appended whenever the object stored an i2, with no reference to whether any
    # pooled estimate was being reported. On 25 of 149 pages that produced an abstract whose
    # only quantitative sentence was "The trials agreed closely (I-squared 0%)" -- above a
    # body stating those trials are not pooled at all. On FINERENONE the pool had been
    # WITHDRAWN (2026-08-18); the withdrawal cleared the rows and refused the figures, and
    # left this sentence standing, so the abstract still reported the agreement of an
    # analysis the page had retracted.
    #
    # Found by the STUDENT persona in the corpus panel, not by any gate we wrote -- and it
    # is precisely what that persona was briefed to find: a confident sentence a novice
    # would not question, sitting on top of an analysis that does not exist. Our own checks
    # read each claim against the object, where the i2 genuinely IS stored, and so could not
    # see it. The contradiction lives between two sentences, not between a sentence and a
    # field.
    #
    # An i2 is meaningful only beside the estimate it describes. If no pooled estimate is
    # reported here, neither is its heterogeneity.
    #
    # AND NO REFUSAL IS RECORDED FOR IT, which took a second attempt to get right. The first
    # version appended a refusal citing `results.by_outcome` as the missing field -- but that
    # container is PRESENT and other sections use it, so `lint_manuscript_whole_document`
    # refused 16 topics for "refused in abstract and USED in figure_legends + limitations".
    # The lint was right. Nothing is absent here: the i2 is stored, and withholding it is a
    # judgement about what it describes, not a gap in the object. Claiming a present field
    # was missing would have replaced one false sentence with another.
    #
    # This is not an absence being quietly deleted to buy words either. The page states, in
    # the section where the reader has the context, that these trials are not pooled and why.
    # What is withheld is a statistic with nothing to attach to.
    if _i2 is not None and not _pooled:
        _i2 = None
    if _i2 is not None:
        # `_i2_words` RETURNS AN ADVERB -- "closely", "loosely" -- because it was written to
        # complete "the trials agreed closely". Dropped into "heterogeneity was {word}" it
        # produced "heterogeneity was closely (I-squared 0%)", which is not a sentence.
        # "THE TRIALS AGREED CLOSELY" IS A CLAIM THE STATISTIC CANNOT MAKE AT k=2.
        # I-squared near zero means no heterogeneity was DETECTED, and with two studies
        # the test has almost no power to detect any -- so the sentence reported the
        # absence of evidence as evidence of agreement, in the results lead, where the
        # impression forms. Wording taken from the external review, which put it better
        # than we did.
        _k_here = None
        for _b in (get(obj, "results.by_outcome") or {}).values():
            if isinstance(_b, dict) and isinstance(_b.get("k"), int):
                _k_here = max(_k_here or 0, _b["k"])
        if (_k_here or 0) <= 2:
            _rparts.append("no statistical heterogeneity was detected (I-squared %s%%), "
                           "though heterogeneity cannot be reliably assessed with two "
                           "trials" % _num(_i2))
        else:
            _rparts.append("no statistical heterogeneity was detected (I-squared %s%%)"
                           % _num(_i2))
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
    # GRADE LIVES IN TWO PLACES AND THIS SECTION KNEW ABOUT ONE OF THEM.
    #
    # Most topics record it at object level as `grade.by_outcome`. sotagliflozin-hf records
    # it on each OUTCOME BLOCK as `results.by_outcome.<oid>.grade`. The Methods section
    # reads the block form, so the same document said "3 outcome(s) carry a rating ... LOW,
    # LOW, LOW" in one section and "no GRADE record is held" in another. A blind reader
    # given the med-student brief found it immediately and named exactly what a novice
    # would do with it: "A novice will report LOW because it is a concrete answer that fits
    # their template" -- resolving a contradiction by picking the half that is easier to
    # write up, with no way of knowing which half is true.
    #
    # This is the SAME key-location error that made a prototype of this work announce "No
    # certainty rating is held for these outcomes" on a topic that rated every outcome. A
    # projection that looks in one of two places does not find nothing; it asserts nothing
    # is there.
    _blk_grade = {}
    for _oid, _b in (get(obj, "results.by_outcome") or {}).items():
        if isinstance(_b, dict) and isinstance(_b.get("grade"), dict) \
                and _b["grade"].get("certainty"):
            _blk_grade[_oid] = _b["grade"]
    # AND THE CITATION HAS TO NAME WHERE IT CAME FROM, NOT WHERE IT USUALLY LIVES.
    # `add_table` refuses any table citing a field that does not resolve, which is right
    # and which caught the first version of this merge: it pulled the ratings from the
    # outcome blocks and then cited `grade.by_outcome.<oid>`, a path absent on exactly the
    # object the merge existed to serve. A student told to check a claim against a field
    # that is not there learns nothing except that the document cannot be trusted.
    _grade_field = {}
    if _blk_grade:
        merged = dict(g.get("by_outcome") or {})
        for _oid, _gr in _blk_grade.items():
            if _oid not in merged:            # object level wins where both exist
                merged[_oid] = _gr
                _grade_field[_oid] = "results.by_outcome.%s.grade" % _oid
        g = dict(g)
        g["by_outcome"] = merged
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
        # "NO DOWNGRADE RECORDED" WAS FALSE ON EVERY BLOCK-LEVEL RATING.
        #
        # The object-level form records `steps`. The block-level form records the working as
        # one string in `certainty_derivation`: "start high; risk_of_bias serious (-1),
        # imprecision serious (-1); total -2 -> low". Reading only `steps` produced a table
        # asserting NO DOWNGRADE beside a rating of LOW -- not merely incomplete, but telling
        # a reader the rating came from nowhere. A student correcting this draft would have
        # had to invent a justification for a LOW rating whose two reasons were recorded all
        # along, one field away. Same shape as every other defect found tonight: the value
        # was held, and the projection looked in one place.
        _steps = "; ".join(_grade_step_words(x) for x in (blk.get("steps") or []))
        if not _steps:
            _steps = _grade_derivation_words(blk.get("certainty_derivation"))
        _k = blk.get("k")
        if _k in (None, ""):
            _k = ((get(obj, "results.by_outcome") or {}).get(oid) or {}).get("k")
        _start = blk.get("started_at") or ("high" if blk.get("randomised") else "")
        # THE SIXTH CONSUMER READING THE STORED LEVEL DIRECTLY. `grade_authority` exists to
        # be the single answer to "what certainty does this outcome carry", and this table
        # -- the most prominent certainty surface on the page -- never asked it. So the
        # Summary of findings column and the abstract stopped publishing a level while
        # this table went on printing "low" three rows deep, in the same section as the
        # sentence saying the rating is pending. Every surface that shows a certainty
        # value has to resolve it, or the withheld ones are simply the ones somebody
        # remembered.
        _r = _ga.resolve(obj, oid)
        _cell = _r["cell"] if _r["state"] != "RATED" else str(blk.get("certainty"))
        if _r["state"] == "PENDING" and _steps:
            # THE STEPS STAY, AND THEY ARE LABELLED. Deleting the working would hide that
            # the assessment was done; printing it unlabelled beside "Pending" reads as a
            # rating with a caveat. It is the work so far, and it says so.
            _steps = "the steps taken so far, not a final rating: " + _steps
        rows.append([_outcome_words(obj, oid), _cell,
                     str(_k if _k not in (None, "") else "?"), str(_start),
                     _steps or "no downgrade recorded"])
        fields.append(_grade_field.get(oid, "grade.by_outcome.%s" % oid))
    # SAY IT ONCE, ABOVE THE TABLE. A column reading "Pending" with no explanation is a
    # word, not a statement; the reader has to be told what it is waiting on.
    _pending = [oid for oid in sorted(g.get("by_outcome") or {})
                if _ga.resolve(obj, oid)["state"] == "PENDING"]
    if _pending:
        s.add(obj, _ga.resolve(obj, _pending[0])["comment"],
              ["risk_of_bias.by_outcome"])
    s.add_table(obj, "Certainty of the evidence, by outcome, with every rating step",
                ["Outcome", "Certainty", "k", "Started at", "Rating steps"], rows,
                fields or ["grade.by_outcome"])
    for oid, blk in sorted((g.get("by_outcome") or {}).items()):
        if isinstance(blk, dict) and blk.get("summary"):
            s.add(obj, str(blk["summary"]),
                  [_grade_field.get(oid, "grade.by_outcome.%s" % oid) + ".summary"
                   if oid in _grade_field else "grade.by_outcome.%s.summary" % oid])
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
    # ONLY WHERE THERE IS AN ASSESSMENT TO SAY THAT ABOUT.
    #
    # This line reads "No second, independent risk-of-bias assessment is recorded for this
    # topic. The judgements were made once." On a topic that HAS a single assessment that is
    # exactly right and worth saying. On a topic with NO assessment at all it asserts that
    # judgements exist, and the same page then lists "the risk-of-bias assessment" among the
    # items not reported. A blind reviewer quoted both halves back as the document
    # contradicting itself, and it was right: `risk_of_bias` is absent on posaconazole-fungal
    # and the sentence still claimed judgements had been made.
    #
    # The consolidation is what made it visible -- the two statements used to sit twenty
    # refusal blocks apart. Collapsing them into one view did not create the contradiction,
    # it stopped hiding it.
    if get(obj, "risk_of_bias") is not None:
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
            # "a conclusions written by the renderer" -- the heading is spliced after an
            # article, and "Conclusions" is plural, so 118 pages carried the disagreement.
            # The heading is already named at the start of this sentence, so the second
            # mention was redundant as well as ungrammatical.
            s.refusals.append(("the %s -- this is a CONTENT gap. The object records no "
                               "interpretive text, and none is generated here: text "
                               "written by the renderer would be an argument no field "
                               "supports" % (heading,), [field]))
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
                   "omission." % (len(ref),
                                  ", ".join(_english_properties(str(x)) for x in ref)),
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
        # THE DISCLAIMER GOES; THE PRINCIPLE STAYS, ONCE, IN PLAIN WORDS.
        #
        # This read "...THAT IS NOT THE SAME AS KNOWING THE REVIEW WAS NOT REGISTERED, and
        # neither claim is made here." Both model families called it circular; Gemini:
        # "bizarre, defensive, and circular -- a convoluted double-negative that adds
        # absolutely nothing to the reader's understanding."
        #
        # The underlying principle is right -- absence of a registration record is not proof
        # of non-registration -- and it is still honoured: the sentence below states what is
        # and is not known WITHOUT the double negative, and without appending a disclaimer
        # to every absence on the page. A caveat repeated at each absence stops being read;
        # said once, plainly, it is information.
        s.refusals.append((
            "a registration statement: no prospective registration is recorded for this "
            "review, and whether one exists elsewhere has not been established",
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
        # "Participants" READ `n` AND `n_total`, AND THIS CORPUS STORES `enrolled`.
        #
        # So the column printed "not extracted" for 28 of the 50 topics that hold the
        # number -- 1,222 and 10,584 sat in `enrolled` on sotagliflozin-hf while the table
        # declared both unknown. A field census written for this same repair made the
        # identical mistake in its first pass, guessing `n_randomised` and reporting 0/50
        # for a field the majority of topics carry. Guessing a key name and reporting the
        # miss as an absence is one error, not two, and it is the one to watch for here.
        #
        # WHO and HOW MANY are now separate columns, because they are separate questions
        # and a reader asked both. `population` is the per-trial text; where a trial holds
        # none, the per-result rows often do, and that is read rather than left blank.
        s.add_table(obj, "Characteristics of every trial contributing to this review",
                    ["Registration", "Trial", "Participants", "Randomised",
                     "Primary outcome measured over", "Design"],
                    [[nct, str(t.get("name") or ""),
                      _trial_population(obj, nct, t),
                      str(t.get("enrolled") or t.get("registration_enrolment")
                          or t.get("n") or t.get("n_total") or "not extracted"),
                      # THE REGISTRY'S OWN WORDS FOR THE TIME FRAME, not a parsed duration.
                      # "up to 5 years" is not 5 years and "Mean follow up of 4 years" is not
                      # a median; normalising them would hand a student a tidy number they
                      # cannot check against the source it came from.
                      str(t.get("registered_primary_timeframe") or "not recorded"),
                      _own_sentence(t.get("design")) or _arms_text(
                          t.get("comparison") or t.get("arms"))]
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
                      if r.get("point") is not None and r.get("ci_low") is not None
              and r.get("ci_high") is not None]

            # A WITHDRAWN POOL IS NOT DRAWN. Found by a blind editor in round 2 of the
            # multi-persona review, and it is the sharpest kind of defect: the page said one
            # thing in prose and the opposite in a picture.
            #
            #   text:   the four-trial pool "mixed the two definitions" and "remains withdrawn"
            #   figure: "Figure 1. Forest plot -- cardiovascular death or a worsening heart
            #            failure event, whichever comes first, as a hazard ratio. k = 4."
            #
            # The editor's words: "That is not review-ready." A forest plot IS the pooled
            # claim -- a diamond under four rows asserts exactly the combination the text
            # retracted -- so drawing it re-published a retraction in the one form a reader
            # trusts most and reads first.
            #
            # Prose already refused to re-publish the components of a retracted pool. Figures
            # were never taught the same rule, which is what happens when a fix is applied
            # where the defect was noticed rather than everywhere the property must hold.
            _wd = res.get("pooled") or {}
            if _wd.get("withdrawn") or _wd.get("withdrawn_reason"):
                pt, usable = [], []
                svg = ""

            if _wd.get("withdrawn") or _wd.get("withdrawn_reason"):
                why = ("this pool was withdrawn, and the reason is given in Results. A forest "
                       "plot is the pooled claim in picture form, so drawing one here would "
                       "restate the very combination this review retracted.")
            elif not pt:
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
            # A CAPTION MUST NOT DESCRIBE A PICTURE THAT IS NOT THERE. Refusing in place
            # is right and is P47's principle; describing the refused figure as though it
            # were drawn is not. "Each contributing trial's stored estimate and interval,
            # with the pooled result" sat under a slot reading "Figure 1 not drawn" on 126
            # pages, several of them at k = 0 with the estimate withdrawn. When the figure
            # is refused the caption names it and the reason carries the rest.
            # THE CAPTION MUST COUNT WHAT THE FIGURE DRAWS, NOT WHAT THE OBJECT HOLDS.
            #
            # COVID19_VACCINES stores three trial rows and the plot draws two: NCT04510207 has
            # no computed risk ratio, so it cannot be placed on the axis. The caption said
            # "k = 3" over a figure showing two effects and two labels -- an overstatement of
            # the evidence in the one place a reader counts it, and the store was right both
            # times. `usable` is the set actually drawn, a few lines above.
            #
            # THREE STATES, because "k" answers a two-state question that has three answers:
            #   stored k equals the rows drawn      -> "k = n" is true, keep it
            #   stored k exceeds the rows drawn     -> say BOTH numbers; one k cannot carry it
            #   nothing drawable, or pool withdrawn -> the refusal caption already handles it,
            #                                          and must not describe a figure as drawn
            _stored_k = k if isinstance(k, int) else None
            _drawn = len(usable)
            if _drawn and _stored_k is not None and _drawn != _stored_k:
                # NO HTML ENTITY HERE. This string is escaped downstream, so "&mdash;"
                # arrives at the reader as the literal text "&mdash;" -- caught by reading the
                # served bytes rather than trusting the marker to mean the caption was right.
                _kcap = ("%d plotted rows against %d stored trial rows, the difference being "
                         "trials this object holds without an estimate that can be placed "
                         "on the axis" % (_drawn, _stored_k))
            else:
                _kcap = "k = %s" % kw
            s.add_figure(
                obj,
                ("Forest plot -- %s. %s." % (name, _kcap)) if why else
                ("Forest plot -- %s. Each contributing trial's stored estimate and interval, "
                 "with the pooled result. %s." % (name, _kcap)),
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
                        "cannot support. It is declined rather than drawn, and this slot "
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
            # Same as the forest caption above: "with the pseudo-confidence funnel drawn
            # from the pooled estimate" described a funnel on 147 pages where the slot
            # immediately above said the funnel was declined and not drawn.
            # THE FUNNEL IS THE SAME CLAIM, and it draws its pseudo-confidence bounds FROM
            # the pooled estimate -- so on a withdrawn pool it is not merely a picture of
            # retracted data, it is a picture built out of the retracted number itself.
            if _wd.get("withdrawn") or _wd.get("withdrawn_reason"):
                fsvg, fwhy = "", ("this pool was withdrawn. The funnel's bounds are drawn "
                                  "from the pooled estimate, so there is no pooled value "
                                  "left for it to be drawn around.")
            s.add_figure(
                obj,
                ("Funnel plot -- %s. k = %s." % (name, kw)) if fwhy else
                ("Funnel plot -- %s. Standard error against effect, with the pseudo-"
                 "confidence funnel drawn from the pooled estimate. k = %s." % (name, kw)),
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
        # THE COUNT REACHES THE READER; THE INTERNAL NAMES DO NOT.
        #
        # This line used to print every property identifier verbatim --
        # "P19_promotion_reaches_derived_blocks, P1_executed_search, P2_k_cascade,
        # P20_cascade_reconciles..." -- into the manuscript. A blind editor desk-rejected the
        # page for unreadability and quoted `k_cascade` back as an example of "bizarre text".
        # They were right about this one: it is a list of OUR OWN build-property names, it
        # means nothing to a clinical reader, and it is the software talking about itself in
        # a document about trials.
        #
        # The count is a real claim and stays. The identifiers are build metadata and belong
        # with the build, not in the paper. Verified count, no vocabulary.
        s.add(obj, "%d machine-checked properties were verified for this page before it was "
                   "published; the checks and their names are recorded with the build rather "
                   "than here." % len(held), ["build_stamp.held"])
    if not s.paras:
        s.refusals.append(("the submission conformance statement", ["build_stamp"]))
    secs.append(s)

    if length == "concise":
        for sec in secs:
            sec.paras = sec.paras[:2]

    # TWO REFUSALS FOR ONE ABSENCE IS ONE REFUSAL TOO MANY, AND I CAUSED THIS ONE.
    #
    # Naming the section when the caller hands `add` an empty string was the right fix for
    # the bare "Refused:" that shipped on 145 pages. But where the caller ALSO appends its
    # own, more specific refusal for the same field, the reader now meets both:
    #
    #     Refused: the keywords section -- nothing on this object composes it
    #     Refused: the keyword list -- a content gap; no keywords are recorded and
    #              inventing them would be indexing this review under terms nobody chose
    #
    # The second says everything the first does and says why. Same absence, same field,
    # twice, and the density of refusals on these pages is already what makes them hard to
    # read. Keyed on the field set, keeping the longest text, because the specific one is
    # always the longer.
    for sec in secs:
        best = {}
        for what, missing in sec.refusals:
            key = tuple(sorted(missing))
            if key not in best or len(what) > len(best[key][0]):
                best[key] = (what, missing)
        if len(best) < len(sec.refusals):
            seen, kept = set(), []
            for what, missing in sec.refusals:
                key = tuple(sorted(missing))
                if key in seen:
                    continue
                seen.add(key)
                kept.append(best[key])
            sec.refusals = kept
    # WRITTEN TO A BUDGET, LAST, ONCE EVERYTHING HAS BEEN PROJECTED. Choosing what to keep
    # requires seeing the whole document, so this cannot be a decision each section makes
    # about itself -- that is exactly how 7,241 words accumulated, every one of them
    # locally justified.
    # BEFORE the budget, so the words this frees are words the budget can spend elsewhere.
    secs = _state_a_long_title_once(secs, obj)
    secs, _budget, _removed = _fit_to_budget(secs, obj)
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
