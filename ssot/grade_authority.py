"""ONE place that answers "what certainty does this pooled outcome carry", for every surface.

WHY THIS FILE EXISTS. A rating could live in two places and no surface read both:

    grade.by_outcome.<oid>.certainty          the structured record, with domains and steps
    results.by_outcome.<oid>.grade.certainty  what the Summary of findings table renders

Four consumers -- the Summary of findings column, the Paper Studio draft, the manuscript
token set and the .docx -- all read the SECOND one only. Across 34 pooled outcomes the
first holds 26 ratings and the second holds 7, so a reader met whichever location the
surface they were looking at happened to read. Every surface now calls `resolve()`.

THIS MERGE MANUFACTURES NOTHING. All 23 disagreements are "one location only" -- there is
not a single case where the two hold different LEVELS -- so resolving them is a lookup, not
a judgement. Where NEITHER location holds an assessment the answer is that no assessment
was made, said in the project's own words, and a level is never inferred from a
neighbouring outcome, from the domains, or from the size of the interval.

AND IF THE TWO LOCATIONS EVER DO DISAGREE ON A LEVEL, THIS REFUSES. `DISAGREEMENT` is a
state, not a tie-break. There are zero today; the arrangement that produced the split is
still in the objects, so the state is implemented rather than assumed away.

THE SUPERVISED READ ON THE FIVE POOLS RATED IN BOTH PLACES, and what it found. Four of the
five are `iv-iron-hf`, which holds LOW in both locations ON CONTRADICTING GROUNDS:

    hfh_cvd_recurrent   structured  rated down for what is NOT RECORDED -- "D5 cannot,
                                    because no trial's statistical analysis plan is held,
                                    and D1 cannot, because allocation concealment is in
                                    neither the registration nor this object", and it says
                                    in terms: "a limit on what we can reach, not a finding
                                    against the trials"
                        table       rated down for a PROPERTY OF A TRIAL -- "it is OPEN
                                    LABEL, with no placebo infusion"

Those are not the same claim and one is not a restatement of the other. They are also not
in conflict about any fact: the four estimands draw on DIFFERENT trial pairs -- recurrent
is AFFIRM-AHF + IRONMAN (open label), first-event and hfh-recurrent are AFFIRM-AHF +
FAIR-HF2, all-cause mortality is AFFIRM-AHF + CONFIRM-HF (both double-blind) -- which was
checked against `per_trial` before anything was called a contradiction.

    So the LEVEL is safe to resolve and the GROUNDS are not interchangeable.

`resolve()` therefore returns BOTH justifications whenever both exist and flags
`both_locations_rated`. A merge that kept the letter and dropped one of two substantively
different reasons for it would lose the more informative half, and the half it would lose
is the one that distinguishes "we could not find out" from "we found out and it was
serious" -- a distinction this project exists to make.

THE FOUR STATES OF THE CERTAINTY CELL.

    RATED, HIGH             the level, no footnote
    RATED, BELOW HIGH       the level AND a footnote, because a downgrade that does not say
                            what was downgraded is a grade with its reason removed
    NOT ASSESSED            "See comment" + the absent-state string + the departure
                            declaration. NEVER a level and never an em dash.
    WITHDRAWN POOL          "See comment". Never a level, EVEN WHEN A LOCATION HOLDS ONE --
                            `sglt2-hf` rates its withdrawn outcome "high" in the table, and
                            that rating described an estimate that has since been taken
                            down. Rendering it beside "not pooled" is the arrangement the
                            per-pool audit calls indefensible under either answer.

NO EM DASH. An em dash means nothing in Cochrane's certainty scheme, and zero of nine
published reviews checked use one. The cell said "not rated" by saying nothing, which a
reader can read as "nothing to report" rather than "not assessed".
"""
from __future__ import annotations

# The project's own absence string, imported rather than restated so the two cannot drift.
try:
    from projectors import ABSENT_STATE as _ABSENT
except ImportError:  # imported as a package from outside ssot/
    from .projectors import ABSENT_STATE as _ABSENT

# THE SAME PREDICATE THE RISK-OF-BIAS SECTION USES, imported rather than restated. If this
# module decided for itself what "adjudicated" means, the two sections could disagree about
# whether this review holds a final judgement -- which is the exact failure being fixed.
try:
    from rob_block import rob_adjudication_state as _rob_state
except ImportError:
    from .rob_block import rob_adjudication_state as _rob_state

STRUCTURED = "grade.by_outcome"
TABLE = "results.by_outcome.<oid>.grade"
# The third source of a level, added 2026-08-30: not a stored record but a DERIVATION
# from the object, performed by the generator on every build. Named separately so a
# reader and an auditor can always tell which of the three answered.
DERIVED = "ssot/grade_engine.py (derived at build time)"

# The four cell values a reader can meet, and nothing else.
CELL_SEE_COMMENT = "See comment"
# A FIFTH CELL, AND IT IS NOT "See comment". The three non-rated states above all mean
# NOTHING WAS ASSESSED, and "See comment" says that honestly. This one means the opposite:
# the work was done, it is on the object, and it is NOT FINAL. Folding it into "See
# comment" would tell a reader an assessment is missing when what is missing is the
# adjudication between two that exist -- and it is the difference between "we have not
# looked" and "two readers looked and disagreed", which is the distinction this review
# spent the day learning to make.
CELL_PENDING = "Pending"
LEVELS = {"HIGH": "High", "MODERATE": "Moderate", "LOW": "Low", "VERY_LOW": "Very low"}

# Cited as instructed. The section's PRINTED TITLE is not held in this object and is not
# invented here -- `methodological_authority.sections_relied_on` is where a verified title
# would go, and this section is not in it. Three states: the reference is present, the
# title is not established, and neither is guessed.
DEPARTURE_SECTION = "Cochrane Handbook §III.3.4.1"
DEPARTURE_DECLARATION = (
    "This is recorded as a DECLARED DEPARTURE under %s: the review reports a pooled "
    "estimate for which no certainty assessment was made. Rating it here would require two "
    "assessors and an adjudicator, and a rating produced by neither is not a GRADE "
    "assessment whatever letter it carries." % DEPARTURE_SECTION)

NOT_ASSESSED_TEXT = _ABSENT["report"] + " " + DEPARTURE_DECLARATION

WITHDRAWN_TEXT = (
    "The pooled estimate for this outcome has been WITHDRAWN, so there is no estimate for a "
    "certainty rating to be about. Any rating this object still carries for this outcome "
    "was made about the withdrawn estimate and is not shown beside it.")


PENDING_TEXT = (
    "This certainty rating is PENDING, not rated. It rests on a risk-of-bias judgement "
    "that this review has not finalised: %s Cochrane rates certainty per outcome by "
    "aggregating the risk-of-bias judgements of the results contributing to it, so a "
    "certainty rating cannot be more final than the risk-of-bias assessment it reads. "
    "%s The rating this object currently records, and the steps behind it, are shown "
    "below as the work so far rather than as this review's answer. No level is published "
    "for this outcome -- not the recorded one, not a more cautious one, and not a "
    "midpoint -- because choosing one would be the judgement that has not been made.")


def _rob_claim(s_blk, t_blk):
    """Does this outcome's GRADE make a risk-of-bias claim, and is it a downgrade?

    READ BOTH LOCATIONS AND BOTH SHAPES. The claim can live as a structured `steps` entry,
    as `domains.risk_of_bias.rating`, or as a FLAT `grade.risk_of_bias` block -- and on
    sotagliflozin-hf it is the flat one that carries the citation of the assessment
    ("2 of 2 results are HIGH overall, all of them on domain 5"), while the prose in
    `domains.risk_of_bias.basis_in_sources` argues from trial-level facts and never
    mentions an assessor. A check that read only the prose location concluded GRADE was
    independent of the assessment. It was reading the field where the dependency is not
    recorded, next to the field where it is.
    """
    down, claim, cites = False, False, []
    for blk in (s_blk or {}), (t_blk or {}):
        for st in (blk.get("steps") if isinstance(blk.get("steps"), list) else []):
            if isinstance(st, dict) and str(st.get("domain")) == "risk_of_bias":
                claim = True
                if (st.get("levels") or 0) < 0:
                    down = True
        d = (blk.get("domains") or {}).get("risk_of_bias")
        if isinstance(d, dict) and d.get("rating"):
            claim = True
            if str(d["rating"]).strip().lower() not in ("not serious", "not assessable"):
                down = True
        flat = blk.get("risk_of_bias")
        if isinstance(flat, dict):
            claim = True
            if (flat.get("rated_down") or 0) > 0 or flat.get("severity"):
                down = True
            if flat.get("now_supported_by"):
                cites.append(str(flat["now_supported_by"]).strip())
    return claim, down, cites


def _norm(v):
    if v is None:
        return None
    t = str(v).strip().upper().replace(" ", "_").replace("-", "_")
    return t or None


def _at(container, oid):
    blk = (container or {}).get(oid)
    return blk if isinstance(blk, dict) else {}


def _grounds(blk):
    """EVERY reason this location recorded, without paraphrase and without a pick.

    THIS RETURNED THE FIRST MATCH AND DROPPED THE REST, which quietly contradicted the one
    claim this module makes about grounds. A block holding both `certainty_derivation` and
    `steps` came back as the derivation alone -- and on iv-iron-hf the derivation is the
    one-line summary while `steps` carries the per-domain reasoning that the whole
    both-locations argument rests on. So the function that exists to prove nothing is
    dropped was itself dropping the more informative half.

    Found by an outside model reading this file cold, with the file supplied in full so it
    had no reason to guess.
    """
    if not blk:
        return None
    out = {}
    for k in ("certainty_derivation", "steps", "domains", "reason", "basis_in_sources"):
        if blk.get(k):
            out[k] = blk[k]
    return out or None


def resolve(canon, oid):
    """The one answer. Never raises for a missing rating -- absence is a state, not a fault.

    Returns a dict with, always: state, level, cell, needs_footnote, comment, source,
    grounds_structured, grounds_table, both_locations_rated.
    """
    res = ((canon.get("results") or {}).get("by_outcome") or {})
    gbo = ((canon.get("grade") or {}).get("by_outcome") or {})
    blk = _at(res, oid)
    # `or {}` IS NOT A TYPE GUARD. A non-dict `pooled` -- an int, a string -- survives
    # it and raises on the next `.get`. Latent today: no object holds one. "Latent, not
    # firing" is the exact phrase the zero-drop defect wore the day before it fired.
    pooled = blk.get("pooled")
    pooled = pooled if isinstance(pooled, dict) else {}

    s_blk = _at(gbo, oid)
    t_blk = blk.get("grade") if isinstance(blk.get("grade"), dict) else {}
    s_lvl, t_lvl = _norm(s_blk.get("certainty")), _norm(t_blk.get("certainty"))
    g_s, g_t = _grounds(s_blk), _grounds(t_blk)
    both = bool(s_lvl and t_lvl)

    out = {"oid": oid, "level": None, "source": None,
           "grounds_structured": g_s, "grounds_table": g_t,
           "both_locations_rated": both, "needs_footnote": False, "comment": ""}

    # WITHDRAWN FIRST, and it OUTRANKS a held rating. This ordering is the whole point:
    # sglt2-hf holds "high" in the table for its withdrawn outcome, and reading the rating
    # before the withdrawal is exactly how that reached a reader.
    if pooled.get("withdrawn"):
        out.update(state="WITHDRAWN_POOL", cell=CELL_SEE_COMMENT,
                   comment=WITHDRAWN_TEXT)
        # BOTH CARRIED RATINGS, NOT ONE. `s_lvl or t_lvl` named the structured value and
        # attributed it correctly -- but where the two locations carried DIFFERENT levels
        # for the withdrawn estimate, the other one vanished. The withdrawn branch returns
        # before the disagreement check by design, so a divergence here is never reported
        # anywhere else: this was the only place it could have been said, and it was not.
        if s_lvl and t_lvl and s_lvl != t_lvl:
            out["comment"] += (
                " The two locations carried DIFFERENT ratings for this withdrawn estimate: "
                "%s in %s and %s in %s. Both are recorded here rather than one being chosen, "
                "and neither is shown in the certainty column."
                % (LEVELS.get(s_lvl, s_lvl), STRUCTURED, LEVELS.get(t_lvl, t_lvl), TABLE))
        elif s_lvl or t_lvl:
            out["comment"] += (
                " The rating it carried was %s, held in %s; it is recorded here rather than "
                "shown in the certainty column." %
                (LEVELS.get(s_lvl or t_lvl, s_lvl or t_lvl),
                 STRUCTURED if s_lvl else TABLE))
        return out

    if both and s_lvl != t_lvl:
        # NOT A TIE-BREAK. Zero cases today; implemented so that the first one is loud.
        out.update(state="DISAGREEMENT", cell=CELL_SEE_COMMENT,
                   comment=("The two locations that can hold a certainty rating for this "
                            "outcome hold DIFFERENT levels -- %s in %s and %s in %s. "
                            "Neither is shown as the answer, because choosing between them "
                            "is a judgement about the evidence and has not been made."
                            % (LEVELS.get(s_lvl, s_lvl), STRUCTURED,
                               LEVELS.get(t_lvl, t_lvl), TABLE)))
        return out

    lvl = s_lvl or t_lvl
    # A LEVEL MUST BE ONE OF THE FOUR. A stored `certainty: 3` normalised to "3" and
    # rendered as the cell value -- a fifth state, arriving through the one path the
    # four-state gate cannot see, because the gate reads what this returns. An
    # unrecognised level is NOT a rating and is not silently shown as one.
    if lvl and lvl not in LEVELS:
        out.update(state="DISAGREEMENT", cell=CELL_SEE_COMMENT,
                   comment=("A certainty value is stored for this outcome that is not "
                            "one of the four GRADE levels: %r. It is not shown as a "
                            "rating, because a value this scheme does not define is "
                            "not a rating whatever it is stored as." % (lvl,)))
        return out
    if not lvl:
        # ⭐ NEITHER STORED LOCATION HOLDS A RATING. Before calling this NOT ASSESSED, ask
        # the ENGINE whether the object supports one.
        #
        # WHY THE ORDER IS THIS WAY ROUND. A stored rating is a human judgement recorded
        # against this outcome; a derived one is what the object's own fields entail. The
        # stored one therefore WINS wherever it exists, and the engine only ever fills a
        # hole. It cannot overwrite, contradict or silently "improve" a recorded rating,
        # which is the failure mode that would make every hand-written assessment in this
        # corpus unauditable.
        #
        # AND WHERE THE ENGINE REFUSES, THE REFUSAL IS RICHER THAN THE OLD SILENCE. The
        # previous behaviour said only "no assessment was made". The engine says which of
        # the five domains it COULD assess, what each one found, and exactly which inputs
        # are missing for the rest -- so a reader meets a partial, sourced assessment and a
        # named gap rather than a blank. That is strictly more than the cell said before
        # and strictly less than a rating, which is what is true.
        try:
            import grade_engine as _ge
        except ImportError:
            from . import grade_engine as _ge
        drv = _ge.derive(canon, oid)
        out["derived"] = drv
        if drv.get("rated") and drv.get("certainty") in LEVELS:
            dl = drv["certainty"]
            out.update(state="RATED", level=dl, derived=drv, derived_rating=True,
                       cell=LEVELS.get(dl, dl.replace("_", " ").capitalize()),
                       source=DERIVED, needs_footnote=(dl != "HIGH"),
                       comment=_derived_footnote(drv))
            return out
        out.update(state="NOT_ASSESSED", cell=CELL_SEE_COMMENT,
                   derived_rating=False,
                   comment=NOT_ASSESSED_TEXT + " " + _derived_partial(drv))
        return out

    # PENDING OUTRANKS RATED, AND ONLY RATED. It sits below WITHDRAWN (no estimate to be
    # about), below DISAGREEMENT (a louder fault), and below NOT_ASSESSED (nothing was
    # rated at all) -- it is precisely the case where a level EXISTS and may not yet be
    # published.
    claim, down, cites = _rob_claim(s_blk, t_blk)
    if claim:
        st = _rob_state(canon)
        why = None
        # THE NARROWER CASE FIRST. Both can be true of one outcome -- the topic's
        # assessment is unadjudicated AND this outcome is not in it -- and "we did not
        # assess this outcome" is the more specific thing to say. Ordered the other way,
        # sotagliflozin's mace3_first reported an adjudication problem for an assessment
        # that never covered it.
        if st.get("assessed") and oid not in (st.get("outcomes_assessed") or set()):
            why = ("this review's RoB 2 assessment does not cover this outcome at all -- "
                   "it assesses %d result(s) across %d other outcome(s) -- so the "
                   "risk-of-bias domain here rests on no assessment recorded on this "
                   "object." % (st.get("results_assessed") or 0,
                                len(st.get("outcomes_assessed") or ())))
        elif st.get("assessed") and st.get("dual") and not st.get("adjudicated"):
            why = ("two assessors read every contributing result independently, they "
                   "disagree, and no adjudication has been performed, so this review "
                   "holds no final risk-of-bias judgement for these results.")
        if why:
            cited = ""
            if cites:
                # QUOTE ONLY AS FAR AS THE CLAIM. The stored string continues into a
                # per-trial list, and the projector that renders this sentence-cases its
                # input -- which turned SCORED into "Scored" and SOLOIST-WHF into
                # "soloist-whf" INSIDE QUOTATION MARKS. A quotation that silently
                # rewrites a trial's name is worse than no quotation; the trial acronyms
                # add nothing here, and the sentence they were in is on the page already.
                _q = cites[0].split("Per-result")[0].strip().rstrip(".")
                cited = ("The dependency is not inferred: this object records the "
                         "risk-of-bias domain as supported by “%s”, which is one "
                         "assessor's count of results at HIGH risk of bias -- a count the "
                         "second assessor's judgements do not contain, on any result. "
                         % _q)
            out.update(state="PENDING", cell=CELL_PENDING, level=None,
                       pending_because=why, recorded_level=lvl,
                       needs_footnote=True,
                       comment=PENDING_TEXT % (why, cited))
            return out

    out.update(state="RATED", level=lvl,
               cell=LEVELS.get(lvl, lvl.replace("_", " ").capitalize()),
               source=(STRUCTURED if (s_lvl and t_lvl) else
                       (STRUCTURED if s_lvl else TABLE)),
               needs_footnote=(lvl != "HIGH"))
    if both:
        out["source"] = "both (%s and %s)" % (STRUCTURED, TABLE)
    if out["needs_footnote"]:
        out["comment"] = _footnote(lvl, s_blk, t_blk, both)
    return out


def _derived_footnote(drv):
    """The footnote for a DERIVED rating. It says it was derived, and from what.

    A derived rating that did not announce itself would be the worst outcome available
    here: a reader would take it for an assessor's judgement. Every sentence below is
    generated from the engine's own record, so the footnote cannot drift from the rating.
    """
    moved = [d for d in drv.get("domains", []) if d["state"] == "DOWNGRADE"]
    na = [d for d in drv.get("domains", []) if d["state"] == "NOT_ASSESSABLE"]
    parts = ["DERIVED BY THE GENERATOR from the fields this object holds, not recorded by "
             "an assessor. Started HIGH because the contributing studies are randomized "
             "trials."]
    for d in moved:
        parts.append("%s: %s %s" % (d["domain"].replace("_", " ").upper(), d["move"],
                                    "-- " + d["reason"]))
    for d in na:
        parts.append("%s: %s -- %s" % (d["domain"].replace("_", " ").upper(), d["move"],
                                       d["reason"]))
    if not moved:
        parts.append("No domain was rated down.")

    # ⭐⭐ THE THRESHOLD AND THE SENSITIVITY REACH THE READER, NOT JUST THE RECORD.
    # A certainty rating whose decision threshold is only in a JSON field is, to a reader,
    # still a letter with a footnote. These two sentences are the difference between an
    # audit trail we hold and an audit trail they can score.
    imp = next((d for d in drv.get("domains", []) if d["domain"] == "imprecision"), None)
    th = (imp or {}).get("thresholds") or {}
    if th.get("chosen"):
        parts.append("IMPRECISION WAS JUDGED AGAINST A NAMED THRESHOLD: %s (%s). %s"
                     % (th["chosen"], th.get("chosen_kind", "").lower().replace("_", " "),
                        th.get("chosen_source", "")))
        if th.get("topic_specific_threshold_absent"):
            parts.append(th["topic_specific_threshold_absent"])
    sens = drv.get("sensitivity") or {}
    if sens.get("statement"):
        parts.append("SENSITIVITY: " + sens["statement"] + " " +
                     sens.get("what_this_is_not", ""))

    rob = next((d for d in drv.get("domains", []) if d["domain"] == "risk_of_bias"), None)
    pri = (rob or {}).get("per_result_inputs") or {}
    if pri.get("n_results"):
        parts.append("RISK OF BIAS WAS ASSESSED PER RESULT, not per outcome: %d "
                     "contributing result(s) judged by %d assessor(s) across the five "
                     "RoB 2 domains, each domain's response and each assessor's answer "
                     "recorded beside the rating rather than summarised into it."
                     % (pri["n_results"], pri.get("n_assessors", 0)))

    # The reference is taken from the RECORD, not from a constant in this module. The
    # first version named `HANDBOOK_REF`, which lives in `grade_engine` and is not
    # imported here -- so every derived rating raised NameError, and it would have taken
    # the generator down on the first result it managed to rate rather than refuse. Read
    # from the record and the citation cannot drift from the rating it describes either.
    parts.append("Method: %s, %s." % (drv.get("derived_by"),
                                      drv.get("handbook_reference") or ""))
    return " ".join(p for p in parts if p)


def _derived_partial(drv):
    """What the engine COULD say when it could not issue a rating.

    ⚠️ This is the sentence that turns a blank cell into a measurement. It names the
    domains that were assessed AND the inputs whose absence blocked the rest, so the gap
    is countable by a reader rather than merely felt.
    """
    doms = drv.get("domains") or []
    if not doms:
        return ""
    done = [d for d in doms if d["state"] != "REFUSED"]
    ref = [d for d in doms if d["state"] == "REFUSED"]
    bits = []
    if done:
        bits.append("Of the five GRADE domains, %d WERE assessed from this object: %s."
                    % (len(done), "; ".join("%s -- %s" % (d["domain"].replace("_", " "),
                                                          d["move"]) for d in done)))
    if ref:
        missing = sorted({m for d in ref for m in (d.get("inputs_missing") or [])})
        bits.append("%d could not be: %s. The specific inputs that would lift the refusal "
                    "are %s. No overall certainty is issued from the remainder, because a "
                    "GRADE level means all five domains were considered."
                    % (len(ref), ", ".join(d["domain"].replace("_", " ") for d in ref),
                       "; ".join(missing) or "not enumerable here"))

    # ⭐⭐⭐ THE BOUND REACHES THE READER. Withholding a letter is right; withholding
    # everything is not. The domains that WERE assessed already constrain the answer, and
    # saying so is the difference between a refusal that informs and a blank cell that
    # reads as "nothing to report" -- the exact misreading this module was built to stop.
    b = drv.get("certainty_bounds") or {}
    if b.get("statement"):
        bits.append("CERTAINTY BOUND: " + b["statement"] + " " +
                    b.get("what_this_is_not", ""))
    return " ".join(bits)


def _footnote(lvl, s_blk, t_blk, both):
    """What was downgraded, from the record that holds it. Never a paraphrase of the level."""
    # `elif` HERE MADE THE SENTENCE BELOW FALSE IN THE SENTENCE THAT SAYS IT.
    #
    # This read: if the structured record has downgrades, use them, OTHERWISE fall back to
    # the table's derivation. So whenever both locations rated -- the exact case this
    # footnote exists to describe -- the table's recorded reason was dropped, while the
    # footnote went on to assert "neither is dropped: both are carried on this object and
    # shown in the certainty record". On iv-iron-hf the reader met that claim with the
    # table's grounds absent.
    #
    # Two cold reviewers from different vendors found the same class independently in one
    # night: GPT-5 in `_grounds`, which returned the first matching key and dropped the
    # rest, and Gemini here, quoting the docstring against the `elif`. The convergence is
    # the finding: a module whose whole argument is "nothing is dropped" had dropped
    # something at both levels it operates on.
    bits = []
    steps = s_blk.get("steps") if isinstance(s_blk.get("steps"), list) else []
    down = [st for st in steps
            if isinstance(st, dict) and (st.get("levels") or 0) < 0]
    if down:
        # NOT `("started_at", "HIGH")`. A DEFAULT STARTING LEVEL IS A CERTAINTY CLAIM.
        #
        # 28 of 48 GRADE blocks across 17 topics record no starting level, and this line
        # asserted "Rated down from HIGH" on every one of them -- telling a reader the
        # evidence began at high certainty when nobody recorded that. GRADE's convention is
        # that randomised evidence starts high, but a convention WE applied is not a value
        # THIS REVIEW recorded, and the sentence gave a reader no way to tell them apart.
        #
        # Found by sweeping deliberately for flatter-by-default fallbacks after the
        # screening defect, rather than waiting to trip over a third one. Same species as
        # `else "included"`: a missing field becomes the answer that flatters.
        bits.append("Rated down from %s for %s."
                    % (s_blk.get("started_at")
                       or "a starting level this review does not record",
                       ", ".join(str(st.get("domain", "?")).replace("_", " ")
                                 for st in down)))
    if t_blk.get("certainty_derivation"):
        bits.append("The summary-of-findings record derives it as: %s."
                    % str(t_blk["certainty_derivation"]).strip().rstrip("."))
    if both:
        bits.append("Both stored locations rate this outcome %s, and their recorded GROUNDS "
                    "are not the same text. Both are stated above rather than one being "
                    "chosen, because the two can differ in KIND -- one recording what the "
                    "trials were found to be, the other recording what could not be "
                    "established about them." % LEVELS.get(lvl, lvl))
    if not bits:
        bits.append("Rated %s. The record does not carry which domains were downgraded, "
                    "and none is inferred here." % LEVELS.get(lvl, lvl))
    return " ".join(bits)


def cell(canon, oid):
    """The certainty column's text. One of four states, never an em dash."""
    return resolve(canon, oid)["cell"]


def rated_level(canon, oid):
    """The level, or None. For consumers that need the value rather than the cell."""
    return resolve(canon, oid)["level"]
