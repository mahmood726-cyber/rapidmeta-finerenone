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
        self.refusals = []       # [(what was not written, which field was absent)]

    def add(self, obj, text, fields):
        """Emit `text` only if EVERY field it cites resolves. Otherwise record the refusal."""
        missing = [f for f in fields if get(obj, f) is None]
        if missing:
            self.refusals.append((text[:70] + ("..." if len(text) > 70 else ""), missing))
            return False
        self.paras.append((text, list(fields)))
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
            self.refusals.append((caption, missing))
            return False
        if not rows:
            self.refusals.append((caption + " (no rows resolved)", list(fields)))
            return False
        self.tables.append((caption, list(headers), [list(r) for r in rows], list(fields)))
        return True

    @property
    def state(self):
        return WRITTEN if (self.paras or self.tables) else REFUSED


def _fmt_ci(p):
    lo, hi = p.get("ci_low"), p.get("ci_high")
    return "%.4g (%.4g to %.4g)" % (p["point"], lo, hi) if lo is not None else "%.4g" % p["point"]


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
    s.add(obj, get(obj, "title") or "", ["title"])
    s.add(obj, get(obj, "question") or "", ["question"])
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
        txt = ("%s %s on %s with the query, verbatim: %s. It returned %s record(s)."
               % (verb, d.get("database", "an unnamed source"), d.get("date_executed", "(no date recorded)"),
                  q, d.get("records_returned", "an unrecorded number of")))
        # A QUERY THAT MISSED AN INCLUDED TRIAL IS PART OF THE METHODS, NOT AN EMBARRASSMENT
        # TO OMIT. The object records it; the manuscript states it.
        if d.get("DEFECT_FOUND"):
            txt += " " + d["DEFECT_FOUND"]
        s.paras.append((txt, ["search.databases[%d]" % i]))
    if not dbs:
        s.refusals.append(("the entire search description", ["search.databases"]))
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
    s = Section("methods_flow", "Methods — study flow and k at every stage")
    kc = get(obj, "k_cascade") or {}
    if kc:
        parts = [("%s %s" % (k.replace("_", " "), v)) for k, v in kc.items()
                 if isinstance(v, int)]
        s.paras.append(("k is reported at every stage rather than as a single number: %s."
                        % "; ".join(parts), ["k_cascade"]))
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
        if model and est:
            s.paras.append(("For %s, a %s model was fitted with the %s estimator."
                            % (oid, model, est),
                            ["results.by_outcome.%s.model" % oid,
                             "results.by_outcome.%s.estimator_used" % oid]))
        else:
            s.refusals.append(("the model/estimator sentence for %s" % oid,
                               [p for p, v in (("results.by_outcome.%s.model" % oid, model),
                                               ("results.by_outcome.%s.estimator_used" % oid, est))
                                if not v]))
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
        # THE CEILING, ON THE PAGE. Without it a reader takes SOME CONCERNS as a verdict on the
        # trials, when it is a bound set by what this review could read.
        ceil = rb.get("ceiling") or {}
        if ceil.get("statement"):
            s.paras.append((ceil["statement"] + " " + ceil.get("what_would_change_it", ""),
                            ["risk_of_bias.ceiling"]))
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
        s.refusals.append(("the claim that certainty of evidence was graded", ["grade.approach"]))

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
    for oid, blk in reported:
        p, het = blk["pooled"], (blk.get("heterogeneity") or {})
        outcome_txt = blk.get("outcome") or oid
        txt = ("For %s (k = %s), the pooled estimate was %s"
               % (outcome_txt, blk.get("k", "?"), _fmt_ci(p)))
        f = ["results.by_outcome.%s.pooled" % oid]
        if het.get("i2") is not None:
            txt += ", with I-squared %.4g%%" % float(het["i2"])
            f.append("results.by_outcome.%s.heterogeneity.i2" % oid)
        txt += "."
        if blk.get("r_output"):
            txt += (" The model output is stored verbatim on the object rather than "
                    "re-typed here.")
            f.append("results.by_outcome.%s.r_output" % oid)
        s.paras.append((txt, f))
        # the estimand reason, which is what makes two pools two pools
        for reason_field in ("why_k_equals_3_and_not_4", "relationship_to_the_other_pools",
                             "WHY_THIS_REPLACES_A_WITHDRAWAL", "what_this_does_not_establish"):
            if blk.get(reason_field):
                s.paras.append((str(blk[reason_field]),
                                ["results.by_outcome.%s.%s" % (oid, reason_field)]))
    for oid, blk in declined:
        reason = blk.get("poolable_reason")
        if reason:
            s.paras.append(("The pool over %s (k = %s) is DECLINED and its reason is stated "
                            "rather than the pool being quietly omitted: %s"
                            % (oid, blk.get("k", "?"), reason),
                            ["results.by_outcome.%s.poolable_reason" % oid]))
        else:
            s.refusals.append(("the reason the %s pool is declined" % oid,
                               ["results.by_outcome.%s.poolable_reason" % oid]))
    secs.append(s)

    # ---- LIMITATIONS ------------------------------------------------------------------
    s = Section("limitations", "Limitations")
    for field, lead in (("screening.known_limitation", "Known limitation of the screen"),
                        ("eligible_but_not_contributing.note",
                         "Eligible trials that do not contribute"),
                        ("verification_basis.what_is_not_claimed", "What is not claimed")):
        v = get(obj, field)
        if isinstance(v, str):
            s.paras.append(("%s: %s" % (lead, v), [field]))
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
    s.add(obj, "Question. %s" % (get(obj, "question") or ""), ["question"])
    casc = get(obj, "k_cascade") or {}
    if casc.get("k_included") is not None:
        s.add(obj, "Included studies. %s trial(s) contribute to at least one synthesis."
              % casc.get("k_included"), ["k_cascade.k_included"])
    _pooled = []
    for oid, blk in sorted((get(obj, "results.by_outcome") or {}).items()):
        p = (blk or {}).get("pooled") or {}
        if p.get("point") is not None:
            _pooled.append("%s %s for %s (k = %s)"
                           % (p.get("measure", "estimate"), _fmt_ci(p),
                              (blk.get("label") or oid), blk.get("k", "?")))
    if _pooled:
        s.add(obj, "Findings. %s." % "; ".join(_pooled),
              ["results.by_outcome"])
    else:
        s.refusals.append(("the findings sentence of the abstract -- this review pools "
                           "nothing, and the reason is given in Results rather than an "
                           "estimate being manufactured here",
                           ["results.by_outcome.*.pooled.point"]))
    secs.append(s)

    # ---- INTRODUCTION (content gap, refused by name) -----------------------------------
    s = Section("introduction", "Introduction")
    if not s.add(obj, "Background. %s" % (get(obj, "protocol.rationale") or ""),
                 ["protocol.rationale"]):
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
        rows.append([oid, str(blk.get("certainty") or "not rated"), str(blk.get("k", "?")),
                     str(blk.get("started_at") or ""),
                     "; ".join(str(x) for x in (blk.get("steps") or [])) or "no downgrade recorded"])
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
    rows, fields = [], []
    for key in ("by_result", "results", "assessments", "by_trial"):
        blk = rob.get(key)
        if isinstance(blk, dict):
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
    if not (s.paras or s.tables):
        s.refusals.append(("the risk-of-bias assessment", ["risk_of_bias"]))
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
                    [[str(r.get("citation", ""))[:120], str(r.get("pmid", "")),
                      str(r.get("their_k", "")), str(r.get("scope", ""))[:80],
                      str(r.get("how_it_differs_from_ours", ""))[:160]]
                     for r in revs if isinstance(r, dict)],
                    ["published_comparison.reviews"])
        s.add(obj, "This review was compared against %d published synthesis(es); the "
                   "denominator is stated because a comparison against an unstated number "
                   "of reviews is not a comparison." % len(revs),
              ["published_comparison.reviews"])
    dd = pc.get("divergence_decomposed")
    if isinstance(dd, dict) and dd.get("why_they_differ"):
        s.add(obj, "Where our result differs from theirs: %s" % dd["why_they_differ"],
              ["published_comparison.divergence_decomposed.why_they_differ"])
    if not (s.paras or s.tables):
        s.refusals.append(("the comparison with published syntheses -- no published "
                           "synthesis is recorded for this topic, so no denominator can be "
                           "given", ["published_comparison"]))
    secs.append(s)

    # ---- STATISTICAL OUTPUT, QUOTED VERBATIM -------------------------------------------
    #
    # THE SECTION THAT WAS NEARLY MISCLASSIFIED. A first probe looked at
    # `results.cross_engine` and reported this as a CONTENT gap. It lives one level lower,
    # per outcome, at `results.by_outcome.<oid>.r_output.verbatim` -- present for every
    # outcome, with the R call and the package versions. An absence my own search reported.
    s = Section("statistical_output", "Statistical output, quoted verbatim")
    any_out = False
    for oid, blk in sorted((get(obj, "results.by_outcome") or {}).items()):
        ro = (blk or {}).get("r_output") or {}
        v = ro.get("verbatim")
        if v:
            any_out = True
            env = ro.get("_environment") or ""
            call = ro.get("call") or ""
            s.add(obj, "%s%s%s" % (("[%s] " % env) if env else "",
                                   ("call: %s -- " % call) if call else "", str(v)),
                  ["results.by_outcome.%s.r_output.verbatim" % oid])
        ce = (blk or {}).get("cross_engine") or {}
        if ce.get("engine"):
            s.add(obj, "Cross-engine verification for %s: %s %s"
                  % (oid, ce.get("engine"), ce.get("agreement") or ""),
                  ["results.by_outcome.%s.cross_engine" % oid])
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
        if not s.add(obj, str(get(obj, field) or ""), [field]):
            s.refusals.append(("the %s -- this is a CONTENT gap. The object records no "
                               "interpretive text, and none is generated here: a %s "
                               "written by the renderer would be an argument no field "
                               "supports" % (heading, heading.lower()), [field]))
        secs.append(s)

    # ---- SECTIONS NOT WRITTEN, AND WHY -------------------------------------------------
    s = Section("not_written", "Sections not written, and why")
    ref = get(obj, "build_stamp.refusing")
    if isinstance(ref, list) and ref:
        s.add(obj, "This review refuses %d of the page standard's properties, by name: %s. "
                   "A refused property is a completed outcome with a stated reason, not an "
                   "omission." % (len(ref), ", ".join(str(x) for x in ref)),
              ["build_stamp.refusing"])
    else:
        s.refusals.append(("the list of refused properties", ["build_stamp.refusing"]))
    secs.append(s)

    # ---- FUNDING AND CONFLICTS (content gap) -------------------------------------------
    s = Section("funding", "Funding and conflicts of interest")
    if not s.add(obj, str(get(obj, "funding") or ""), ["funding"]):
        s.refusals.append(("the funding and conflict-of-interest statement -- a CONTENT "
                           "gap. A submission requires it and this object does not carry "
                           "it; it is not inferable from anything held here", ["funding"]))
    secs.append(s)

    # ---- REFERENCES --------------------------------------------------------------------
    s = Section("references", "References")
    src = get(obj, "sources")
    if isinstance(src, dict) and src:
        s.add_table(obj, "Sources this review reads, with the layer each was read at",
                    ["Id", "Layer", "Source", "Location"],
                    [[sid, str((v or {}).get("layer", "")), str((v or {}).get("name", ""))[:150],
                      str((v or {}).get("url") or (v or {}).get("staged_as") or "")]
                     for sid, v in sorted(src.items()) if isinstance(v, dict)],
                    ["sources"])
    else:
        s.refusals.append(("the reference list", ["sources"]))
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
    if ri.get("method"):
        s.add(obj, "Every trial in this review is keyed to a registration identifier, "
                   "verified by %s%s." % (ri["method"],
                                          (" on %s" % ri["verified_utc"])
                                          if ri.get("verified_utc") else ""),
              ["registration_identity.method"])
    trials = ri.get("trials")
    if isinstance(trials, list) and trials:
        s.add_table(obj, "Registration identifiers, and whether each was verified",
                    ["Registration", "Verified", "Link"],
                    [[str(t.get("nct", "")), str(t.get("verified", "")),
                      str(t.get("link", ""))] for t in trials if isinstance(t, dict)],
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
    envs = sorted({(((blk or {}).get("r_output") or {}).get("_environment") or "")
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
    secs.append(s)

    # ---- TABLES: TRIAL CHARACTERISTICS -------------------------------------------------
    s = Section("trial_characteristics", "Trial characteristics")
    by_id, unjoinable = _trials_by_identity(obj)
    if by_id:
        s.add_table(obj, "Characteristics of every trial contributing to this review",
                    ["Registration", "Trial", "Arms", "Participants"],
                    [[nct, str(t.get("name") or ""),
                      str(t.get("comparison") or t.get("arms") or ""),
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
        rows.append([oid, "Forest plot",
                     ("%s %s, k = %s" % (p.get("measure", "estimate"), _fmt_ci(p),
                                         (blk or {}).get("k", "?"))
                      if p.get("point") is not None
                      else "not pooled; the reason is given in Results")])
    if rows:
        s.add_table(obj, "Figures, and what each one shows",
                    ["Outcome", "Figure", "What it shows"], rows, ["results.by_outcome"])
    else:
        s.refusals.append(("the figure legends", ["results.by_outcome"]))
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
    return secs


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
