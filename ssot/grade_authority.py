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

STRUCTURED = "grade.by_outcome"
TABLE = "results.by_outcome.<oid>.grade"

# The four cell values a reader can meet, and nothing else.
CELL_SEE_COMMENT = "See comment"
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
        out.update(state="NOT_ASSESSED", cell=CELL_SEE_COMMENT,
                   comment=NOT_ASSESSED_TEXT)
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
        bits.append("Rated down from %s for %s."
                    % (s_blk.get("started_at", "HIGH"),
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
