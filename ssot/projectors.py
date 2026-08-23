"""Projectors for the tabbed SSOT page.

REBUILT 2026-08-12 after `git reset --hard HEAD~1` destroyed a day of uncommitted
generator work. The prose and HTML fragments here are recovered verbatim from
`evidence/2026-08-12/recovered-generator/build_app_v2.cpython-313.pyc` -- the only
surviving representation, which existed only because a probe had imported the
module. Control flow is written fresh; Python 3.13 has no working decompiler.

Kept as a separate module so the wiring into build_app_v2.py stays small, and so
this file can be committed the moment each projector works rather than at the end
of a round. That is the discipline whose absence caused the loss.

Acceptance test: the emitted page against
`evidence/2026-08-12/recovered-generator/ARNI_v6_mitral-base_2026-08-12.html`.
"""
import html as _html
import math
import re
from urllib.parse import quote

NL = chr(10)

# --- recovered verbatim from the compile ------------------------------------
TABS = (
    ("protocol", "1. Protocol",
     ("protocol", "registration", "amendments", "attestation", "completeness",
      "authority"), ("estimand",)),
    ("search", "2. Search", ("searchcard", "searchstrings"), ()),
    ("screen", "3. Screening", ("screening", "corpus"), ()),
    ("extract", "4. Extraction",
     ("carried", "considered", "components", "rob", "switching", "sources_card"),
     ("trials",)),
    ("analysis", "5. Analysis Suite", ("network",),
     ("headline", "forest", "figures", "countfigs", "hb", "sens", "dissent",
      "subgroups", "note")),
    ("report", "6. Scientific Output", ("output", "recon", "removal"), ("grade",)),
    ("paper", "7. Paper Studio", ("paper",), ()),
    ("statistics", "Statistics", (),
     ("stats", "counttabs", "crossengine", "panels")),
)
# TRACK D: a tab with no source renders an HONEST STATE, never empty and never
# silently merged into its neighbour. Silent merge is how a page becomes a flat
# scroll while still claiming to be a review: the reader sees no gap, so the
# absence makes no claim. These strings say what would be there, why it is not,
# and what that means for the reader.
ABSENT_STATE = {
 "protocol": ("No protocol record is held in this object. This review was assembled from named "
              "sources rather than from a pre-registered protocol, so no registration, amendment "
              "history or prospective estimand declaration can be shown here."),
 "search":   ("No search record is held in this object. The included set was reconciled against "
              "published syntheses rather than produced by a database search, so no query, date "
              "or yield can be shown. Treat the included set as a convenience sample, not a "
              "systematic one."),
 "screen":   ("No screening log is recorded for this review. The included set was reconciled "
              "against published syntheses rather than screened from a search, so no "
              "records-identified, excluded-with-reason or dual-screening counts exist."),
 "extract":  ("No per-trial extraction table is held in this object, so the numbers on this page "
              "cannot be traced to an arm-level source here."),
 "analysis": ("No pooled analysis is held in this object for the outcomes shown."),
 "report":   ("No GRADE assessment or reconciliation record is held in this object, so the "
              "certainty of this evidence has not been rated."),
 "paper":    ("No manuscript has been generated for this review."),
 "statistics": ("No statistical panel set is held in this object."),
}

# TRACK D, THIRD STATE -- PARTIALLY HELD. The two states above are NOT ENOUGH, and eleven
# delivered pages proved it. A thin tab is emitted as "Not held in this object" FOLLOWED BY THE
# THIN BODY IT DID CARRY, so a search panel holding an executed query but no yield table printed
# a sentence saying "no query, date or yield can be shown" DIRECTLY ABOVE ITS OWN QUERY.
#
#   THE DENIAL WAS DOING REAL WORK WITH THE WRONG WORDS. It correctly explained an empty panel
#   and incorrectly denied the part that was present. Deleting it -- which was the first
#   attempted repair -- removed a TRUE statement about the yield in order to remove a FALSE one
#   about the query, and left seven panels empty and unexplained. A composite claim needs a
#   composite check, and a composite absence needs a composite sentence.
#
# So when a tab carries SOMETHING but not enough, the page says which part is held and which is
# not, instead of denying the whole.
PARTIAL_STATE = {
 "search":   ("The executed query is held on this object and is shown below. Its YIELD is not: "
              "the record does not carry the identifiers this query returned, so the number of "
              "records and their disposition cannot be shown and the table below is empty for "
              "that reason."),
 "screen":   ("Part of the screening record is held and is shown below. The counts that would "
              "complete it -- records identified, excluded with reasons, dual-screening -- are "
              "not carried on this object."),
 "extract":  ("Part of the extraction record is held and is shown below. The per-arm source "
              "cells that would let every number be traced are not carried on this object."),
 "analysis": ("Part of the analysis is held and is shown below. No pooled estimate is carried "
              "for the outcomes shown."),
 "report":   ("Part of the reporting record is held and is shown below. No GRADE certainty "
              "rating is carried, so the certainty column is left as an em dash rather than "
              "guessed."),
 "protocol": ("Part of the protocol record is held and is shown below. The registration and "
              "amendment history that would complete it are not carried on this object."),
}


# CONVERTED objects need their OWN absence text. The strings above explain absences
# for AUTHORED reviews and give a REASON -- "reconciled against published syntheses
# rather than produced by a database search". That reason is TRUE of the authored
# objects and FALSE of a converted one, where the only true statement is that
# nothing was recoverable from the page the object was extracted from.
#
# Caught by looking at the rendered page rather than at the build log: a converted
# page was explaining its own gap with someone else's explanation. A panel that
# states the wrong reason for an absence is worse than a blank one -- the blank
# makes no claim, and this made a false one.
ABSENT_STATE_CONVERTED = {
 "protocol":  ("No protocol or registration record was recoverable from the published page "
               "this object was extracted from. That is a statement about what the page "
               "contained, not about whether the review had a protocol."),
 "search":    ("No search strategy was recoverable from the published page this object was "
               "extracted from, so no query, date or yield can be shown."),
 "screen":    ("No screening log was recoverable from the published page this object was "
               "extracted from, so no records-identified or excluded-with-reason counts exist "
               "here."),
 "extract":   ("No per-trial source sentences or resolvable links were recoverable. The values "
               "shown can be traced to the page they came from, but NOT to a paper."),
 "analysis":  ("No pooled analysis is held in this object for the outcomes shown."),
 "report":    ("No certainty rating or reconciliation record was recoverable from the "
               "published page this object was extracted from, so the certainty of this "
               "evidence has not been rated."),
 "paper":     ("No manuscript has been generated for this review."),
 "statistics": ("No statistical panel set was recoverable from the published page this object "
                "was extracted from."),
}

_CARD_SPLIT_RE = re.compile(r"<div class='card (?:rec|warn)'>")
_NON_DECISION_P_RE = re.compile(r"<p>(?!<strong>This review's decision)")
_TABLE_RE = re.compile(r"<table[ >]")


def screen_partial_note(body):
    """The screen tab's PARTIAL sentence, COMPUTED FROM THE PANEL, never recited.

    WHY THIS IS NOT A CONSTANT. `PARTIAL_STATE["screen"]` denies three things in one
    breath -- records identified, excluded with reasons, dual-screening -- and on the
    five pages that carry a screening log the middle limb splits:

        EARLY_RHYTHM_CONTROL_AF   551 records, 551 carry a stated reason
        APIXABAN_VTE_PROPHYLAXIS   72 records,  72 carry a stated reason
        APIXABAN_VTE_TREATMENT     72 records,  72 carry a stated reason
        AZILSARTAN_CLD_VS_OLM      57 records,   0 carry a stated reason
        BOCOCIZUMAB_LIPID          22 records,   0 carry a stated reason

    So one fixed sentence is FALSE on the first three and TRUE on the last two, and it
    reads identically either way -- which is class 29 exactly, one level down from the
    refusal that produced it. P17: a negative claim is COMPUTED and names what it was
    computed against. This one is computed against the panel's own rendered body.

    IT REFUSES TO GUESS. With no record card present it returns None, and the caller
    falls back to the constant rather than composing a sentence about a log it cannot
    see. A rule that cannot return nothing cannot tell you it does not know.
    """
    cards = [c.split("</div>")[0] for c in _CARD_SPLIT_RE.split(body)[1:]]
    n_rec = body.count("<div class='card rec'>")
    if not n_rec:
        return None
    n_adj = body.count("<div class='card warn'>")
    with_reason = sum(1 for c in cards if _NON_DECISION_P_RE.search(c))
    has_counts = bool(_TABLE_RE.search(body))

    if with_reason == n_rec:
        reasons = "every one carrying a stated reason"
    elif with_reason == 0:
        reasons = "none of which carries a stated reason"
    else:
        reasons = "%d of which carry a stated reason" % with_reason
    held = ("The per-record screening log IS held and is shown below: %d record%s, %s"
            % (n_rec, "" if n_rec == 1 else "s", reasons))
    if n_adj:
        held += ", and %d adjudication record%s" % (n_adj, "" if n_adj == 1 else "s")
    held += "."

    missing = []
    if not has_counts:
        missing.append("the records-identified and excluded-with-reason COUNTS that "
                       "would reconcile these records to a PRISMA total")
    if with_reason == 0:
        missing.append("a reason for any individual exclusion")
    elif with_reason < n_rec:
        missing.append("a reason for the remaining %d record%s"
                       % (n_rec - with_reason, "" if n_rec - with_reason == 1 else "s"))
    if not n_adj:
        missing.append("any dual-screening or adjudication record")
    if not missing:
        return None                        # nothing is missing; this is not a partial

    if len(missing) == 1:
        lack = missing[0]
    else:
        lack = ", ".join(missing[:-1]) + " and " + missing[-1]
    return ("%s Not carried on this object: %s. Carrying %s in the object's `screening` "
            "block would complete this tab."
            % (held, lack, "them" if len(missing) > 1 else "it"))


_SOF_ROW_RE = re.compile(r"<tr><td>.*?</tr>", re.S)
_LAST_CELL_RE = re.compile(r"<td>([^<]*)</td>\s*</tr>\s*$", re.S)


def report_certainty_unrated(body):
    """Is EVERY outcome in the summary-of-findings table left unrated?

    WHY THIS EXISTS, AND IT IS A DEFECT FOUND IN OUR OWN REBUILD. The report tab's
    honest sentence -- "no GRADE certainty rating is carried, so the certainty column
    is left as an em dash rather than guessed" -- was emitted only when the panel fell
    under FLOOR_CHARS. BOCOCIZUMAB_LIPID's report panel measures 610 characters.

        THE PAGE KEPT OR LOST ITS EXPLANATION OF A COLUMN OF EM DASHES ON A TEN
        CHARACTER MARGIN, and the direction is the wrong way round: the page with the
        LONGER summary table is the one that silently drops the explanation.

    A length threshold is a fine test for "is this panel empty". It is not a test for
    "does this review have a certainty rating", and it was being used as one. This
    reads the CELLS -- the same cells the reader sees -- and is indifferent to length.

    Returns True only when a Certainty column exists AND at least one outcome row is
    present AND every one of them is an em dash. No table, or no rows, returns False:
    absent is NOT_ASSESSABLE, and this function must not turn "I could not look" into
    "there is nothing there".
    """
    if "<th>Certainty</th>" not in body:
        return False
    rows = _SOF_ROW_RE.findall(body)
    cells = []
    for row in rows:
        m = _LAST_CELL_RE.search(row)
        if m:
            cells.append(m.group(1).strip())
    if not cells:
        return False
    return all(c in ("&mdash;", "—", "") for c in cells)


REQUIRED_TABS = ("protocol", "search", "screen", "extract", "analysis", "report",
                 "paper", "statistics")
GRADE_DOMAINS = ("risk_of_bias", "inconsistency", "indirectness", "imprecision",
                 "publication_bias")
FLOOR_CHARS = 600

TAB_CSS = """ .tabs input{position:absolute;clip-path:inset(50%);height:1px;width:1px;overflow:hidden}
 .absent-state{border-left:4px solid #B91C1C;background:#FEF2F2;padding:.7rem .9rem;margin:.6rem 0;font-size:.88rem;color:#7F1D1D}
 .tabnav{display:flex;flex-wrap:wrap;gap:.25rem;border-bottom:2px solid var(--line);margin:1.25rem 0 0}
 .tabnav label{padding:.5rem .9rem;cursor:pointer;font-size:.9rem;font-weight:600;color:var(--muted);border:1px solid transparent;border-bottom:none;border-radius:.375rem .375rem 0 0}
 .tabnav label:hover{color:var(--fg);background:var(--soft)}
 .panel{height:0;overflow:hidden}
 .toc{margin:.6rem 0 1rem;padding:.5rem .75rem;background:var(--soft);border-radius:.375rem;font-size:.85rem;color:var(--muted)}
 .card.rec{border-left:4px solid var(--line)}
 .mine{margin-top:.5rem;padding-top:.5rem;border-top:1px dashed var(--line);font-size:.85rem;color:var(--muted)}
 .mine button,.chip{margin-right:.35rem;padding:.25rem .6rem;border:1px solid var(--line);border-radius:.25rem;background:var(--soft);color:var(--fg);cursor:pointer;font:inherit;font-size:.85rem}
 svg{max-width:100%;height:auto}
 a.dl{display:inline-block;padding:.3rem .7rem;border:1px solid var(--line);border-radius:.25rem;background:var(--soft);color:var(--accent);text-decoration:none;font-size:.85rem}
 pre{background:var(--soft);border:1px solid var(--line);border-radius:.375rem;padding:.6rem;overflow-x:auto;font-size:.8rem;white-space:pre-wrap;color:var(--fg)}
 /* Ruled, not filled. Mint-green and pale-yellow row fills were the most
    dashboard-looking thing on the page and are a journalistic status device,
    not a scientific one. A left rule carries the same information and survives
    printing in black and white. */
 tr.inc td:first-child{border-left:3px solid var(--accent)}
 tr.und td:first-child{border-left:3px solid var(--warnb)}
"""


def fmt(x):
    """Display formatting for every projected value on the page.

    Floats are reported to 3 significant figures. INTEGERS ARE NEVER TOUCHED --
    sig() would render a count of 9544 as "9,540", and rounding a count is not a
    formatting choice, it is a wrong number. Counts are ints in this object and
    fall through to str() unchanged; only measured quantities are floats.

    The object keeps full precision, so nothing is lost: this is the report, not
    the record.
    """
    if x is None:
        return ""
    if isinstance(x, bool):
        return str(x)
    if isinstance(x, float):
        return sig(x, 3)
    return str(x)


def sig(x, n=3):
    """Round for DISPLAY to n significant figures. The object keeps its precision.

    "HR 0.8392 (0.7429 to 0.948)" reports four significant figures, then four,
    then three, on a pooled estimate from three trials whose narrowest input
    interval spans 0.14. That is machine output, not a considered report, and it
    reads as one -- a reader who sees four figures on a quantity that cannot
    support two stops trusting the ones that matter.

    Only the DISPLAY is rounded. The canonical object, the SVG and the data
    downloads keep every digit, so nothing is lost and re-analysis is unaffected.
    """
    if x is None:
        return ""
    if not isinstance(x, (int, float)) or isinstance(x, bool):
        return str(x)
    if x == 0:
        return "0"
    import math
    d = n - int(math.floor(math.log10(abs(x)))) - 1
    r = round(float(x), d)
    if d <= 0:
        return "{:,}".format(int(r))
    out = ("%.*f" % (d, r)).rstrip("0").rstrip(".")
    return out if out else "0"


e = _html.escape


# --------------------------------------------------------------- readiness
def _attested(a):
    """An attestation is present only if it names a person, a source and a date.

    A slot with the fields blank is an UNSIGNED FORM, and reading one as satisfied
    would make the whole mechanism a laundering channel: the page would report a
    human check that nobody performed."""
    return bool(a and a.get("by") and a.get("source_checked_against")
                and a.get("date_utc"))


def readiness(canon):
    """Compute the submission-readiness verdict. Three states, never a string.

    Replaces a banner that was a CONSTANT: both branches of the old ternary began
    "NOT SUBMISSION-READY", so no object in any state could render anything else.

    ATTESTABLE gaps are work a human discharges by doing it and recording that
    they did. STRUCTURAL gaps are facts no signature changes -- publication bias
    is not assessable at three studies whoever signs the form."""
    att = canon.get("attestations") or {}
    reg = canon.get("registration") or {}
    by_out = ((canon.get("results") or {}).get("by_outcome") or {})
    attestable = []
    for key, label in (("screening", "Screening decisions"),
                       ("extraction", "Data extraction against source"),
                       ("risk_of_bias", "Per-study risk of bias"),
                       ("grade", "GRADE domain ratings")):
        a = att.get(key)
        if a is None:
            continue
        attestable.append({"id": key, "label": label, "ok": _attested(a),
                           "what": a.get("what_must_be_checked", ""),
                           "att": a if _attested(a) else None})
    blocking, limits = [], []
    if reg:
        if not reg.get("commits"):
            blocking.append({"label": "No registration evidence",
                             "detail": "No timestamped commit is recorded for "
                                       "this object."})
        o = reg.get("ordering") or {}
        if o.get("verdict") != "established":
            limits.append({"label": "Registration is not prospective",
                           "detail": o.get("reason", "")})
    else:
        blocking.append({"label": "No registration evidence",
                         "detail": "This object records no protocol registration."})
    for oid, r in by_out.items():
        pb = (((r.get("grade") or {}).get("domains") or {})
              .get("publication_bias") or {})
        if pb.get("rating") in ("not assessable", "not_assessable"):
            limits.append({"label": "Publication bias not assessable",
                           "detail": "The GRADE publication-bias domain for this "
                                     "outcome is rated not assessable. No "
                                     "attestation changes that; it is a property "
                                     "of how many studies there are."})
            break
        ks = r.get("k_status") or {}
        if ks.get("is_lower_bound"):
            limits.append({"label": "k is a lower bound, not a settled count",
                           "detail": ks.get("why", "")})
    sc = canon.get("screening") or {}
    und = [x for x in (sc.get("records") or [])
           if x.get("disposition") and not x.get("criteria_failed")]
    if und:
        limits.append({"label": "%d record(s) with eligibility undetermined" % len(und),
                       "detail": "; ".join("%s: %s" % (x.get("trial", ""),
                                                       x.get("disposition", ""))
                                           for x in und)})
    unres = canon.get("screening_names_unresolved") or []
    if unres:
        limits.append({"label": "%d screened name(s) unresolved" % len(unres),
                       "detail": "; ".join("%s: %s" % (u.get("name_as_given", ""),
                                                       u.get("disposition", ""))
                                           for u in unres)})
    outstanding = [a for a in attestable if not a["ok"]]
    if blocking:
        state, why = "NOT READY", "a structural condition is unmet"
    elif outstanding:
        state, why = ("NOT YET DETERMINED",
                      "the author has not yet attested the surfaces below")
    elif attestable:
        state, why = "READY", "every attestable surface is signed"
    else:
        state, why = ("NOT YET DETERMINED",
                      "this object carries no attestation record at all")
    return {"state": state, "why": why, "attestable": attestable,
            "outstanding": outstanding, "blocking": blocking, "limitations": limits}


# Where the evidence for each outstanding attestation actually lives, DERIVED
# from the built page's own panels rather than assumed: RoB-2 is on the
# Extraction tab, not the Report tab, which is where a reasonable guess would
# have sent the reader. A link to the wrong tab is worse than no link, for the
# same reason a wrong measure label is worse than an absent one -- it is a
# confident statement that happens to be false. Anything not in this table gets
# NO link rather than a guessed one.
_EVIDENCE_TAB = (
    ("extraction", "extract", "the extraction table"),
    ("risk of bias", "extract", "the per-trial RoB-2 assessment"),
    ("screening", "screen", "the screening decisions"),
    ("grade", "report", "the GRADE domain ratings"),
)


def _evidence_link(label):
    """A link to the surface a reader can check while the attestation is open."""
    low = (label or "").lower()
    for key, tid, what in _EVIDENCE_TAB:
        if key in low:
            return (' <a href="#%s">Check it yourself: %s &rarr;</a>' % (tid, what))
    return ""


def verdict_card(canon, rd, p):
    """The verdict, and the qualifications that must not sit behind a tab.

    A JUDGEMENT CALL, made explicitly. Tabs let a reader never open a panel, and
    the honesty of this page has depended on its caveats being unavoidable. Three
    things stay above the tab strip: the computed verdict with its unmet items,
    the structural limitations no attestation can discharge, and each outcome's
    own leave-one-out finding."""
    tone = "" if rd["state"] == "READY" else " warn"
    items = ""
    for b in rd["blocking"]:
        items += ("    <li><strong>%s</strong> &mdash; %s</li>%s"
                  % (e(b["label"]), p(b["detail"]), NL))
    for a in rd["outstanding"]:
        # "AWAITING AUTHOR ATTESTATION: DATA EXTRACTION AGAINST SOURCE" is the
        # loudest extraction-related string on this page at load, and it sat
        # there with NO LINK to the table it is about. A reader met a notice
        # saying the data is not yet checked, and was given no way to check it.
        # That asymmetry -- not any difference in extraction content -- is the
        # most likely reason one page reads as having an audit surface and
        # another does not.
        #
        # The link points at the EVIDENCE, and the wording now says what the
        # reader can do while the attestation is outstanding. Not attested is
        # still not attested: this adds an address, it does not discharge
        # anything, and the item stays in the unmet list where it belongs.
        items += ("    <li><strong>Awaiting author attestation: %s</strong> "
                  "&mdash; %s%s</li>%s"
                  % (e(a["label"]), p(a["what"]), _evidence_link(a["label"]), NL))
    for l in rd["limitations"]:
        items += ("    <li><strong>%s</strong> <small>(no attestation can "
                  "discharge this)</small> &mdash; %s</li>%s"
                  % (e(l["label"]), p(l["detail"]), NL))
    quals = ""
    for oid, r in ((canon.get("results") or {}).get("by_outcome") or {}).items():
        f = (r.get("sensitivity") or {}).get("leave_one_out_finding")
        if f:
            quals += "    <li>%s</li>%s" % (p(f), NL)
    return ("<div class='card%s verdict'>%s  <h2>Submission readiness: %s</h2>%s"
            "  <p>Computed from this object's own state &mdash; %s. This is not a "
            "fixed disclaimer: the conditions below are each testable, and a build "
            "in which they are met renders READY.</p>%s"
            % (tone, NL, e(rd["state"]), NL, e(rd["why"]), NL)
            + ("  <ul>%s%s  </ul>%s" % (NL, items, NL) if items else "")
            + ("  <h3>Qualifications that travel with the headline</h3>%s  <ul>%s"
               "%s  </ul>%s" % (NL, NL, quals, NL) if quals else "")
            + "</div>" + NL)


# --------------------------------------------------------------- svg + figures
def svg_download(svg, filename, label):
    """Wrap an inline SVG so it can be saved, with no JavaScript.

    The href is a data URI built at BUILD time from the same bytes the page
    renders, so the downloaded file cannot carry a different number from the one
    on screen -- it IS the one on screen."""
    uri = "data:image/svg+xml;charset=utf-8," + quote(svg, safe="")
    return ("  <p><a class='dl' download='%s' href=\"%s\">&#11015; %s</a> "
            "<small>saves the figure exactly as rendered &mdash; the file is the "
            "same bytes as the graphic above</small></p>%s"
            % (filename, uri, label, NL))


# Set once by the build driver. Kept as module state rather than threaded through
# every projector because the alternative is a browser handle in the signature of
# a dozen pure functions that do not otherwise know what a browser is.
RASTER = {"browser": None, "workdir": None, "outdir": None}


def fig(svg, title, fname, note):
    """One figure card: inline SVG, downloads in every offered format, a note.

    The download set is generated from the SAME svg string that is inlined here,
    so every offered file descends from the graphic on screen rather than from a
    second render of the same data."""
    stem = fname.rsplit(".", 1)[0]
    dl = None
    if RASTER.get("workdir"):
        try:
            import figures as fg
            items, sha, ok, wr = fg.figure_downloads(
                svg, stem, RASTER.get("browser"), RASTER["workdir"],
                RASTER["outdir"])
            dl = fg.downloads_html(items, sha, ok, e, NL, wr)
        except Exception:                                # noqa: BLE001
            dl = None
    if dl is None:
        dl = svg_download(svg, fname, "Download (SVG)")
    return ("<div class='card'>%s  <h3>%s</h3>%s  %s%s%s  <p><small>%s</small>"
            "</p>%s</div>%s" % (NL, title, NL, svg, NL, dl, note, NL, NL))


def nice_log_ticks(lo, hi, null_v, limit=7):
    """Round tick values spanning [lo, hi] on a log axis, always including null.

    The ticks used to be exactly {null, min(data), max(data)}, which put labels
    like 0.000546, 0.0862 and 4.89 on the axis: three arbitrary numbers that told
    a reader nothing about the scale and changed whenever a trial entered. A
    reader uses an axis to locate a value, and cannot do that against extrema.

    These are 1-2-5-per-decade round numbers, which is scale furniture and not a
    claim -- it asserts nothing the data does not, it only says where the scale
    is. The null value is always kept because it is the line the whole plot is
    read against.

    Derived from the DATA range, never from a display window, so the invariance
    check that tick labels are identical across axis-range variants still holds:
    only the mapping moves.
    """
    if lo <= 0 or hi <= 0:
        return sorted({null_v})
    def _mk(mants):
        s, dec = set(), int(math.floor(math.log10(lo)))
        while dec <= int(math.floor(math.log10(hi))) + 1:
            for m in mants:
                v = m * (10.0 ** dec)
                if lo <= v <= hi:
                    # Snap: 0.7*10**0 is 0.7000000000000001 in binary floating
                    # point, and that renders on the axis exactly as written.
                    s.add(round(v, 10))
            dec += 1
        return s

    # Denser than 1-2-5: a hazard-ratio axis usually spans well under two
    # decades, where 1-2-5 leaves two labels on the whole scale. Ticks stay
    # inside the DATA range, so they are always on canvas whichever display
    # window is in force.
    out = _mk((1, 1.2, 1.5, 2, 2.5, 3, 4, 5, 7))
    if len(out) < 4:
        # A narrow span (e.g. a leave-one-out panel running 0.74 to 0.95) hits no
        # round number at all, which put us back at a single tick -- the very
        # defect this function exists to remove. Step down a decade for mantissas
        # before giving up.
        out |= _mk([m / 10.0 for m in (1, 1.5, 2, 3, 4, 5, 6, 7, 8, 9)])
    out.add(null_v)
    # Too many ticks is its own unreadability. Thin the non-null ones evenly and
    # keep the null, rather than truncating one end of the axis.
    if len(out) > limit:
        rest = sorted(v for v in out if v != null_v)
        step = max(1, round(len(rest) / float(limit - 1)))
        out = {null_v} | set(rest[::step])
    return sorted(out)


def nice_lin_ticks(lo, hi, limit=5):
    """Round tick values across a LINEAR range, on the 1-2-5 sequence.

    Same reasoning as nice_log_ticks, for the scatter panels: their axes were
    labelled with min(data) and max(data), which is where 0.000546, 0.0862 and
    4.89 came from. Those tell a reader nothing about the scale and move every
    time a trial enters.

    Ticks are clamped INSIDE the data range and never take the padded axis ends,
    which is the defect the original docstring here recorded: a padded extreme is
    a number no source contains. A round number inside the plotted range is scale
    furniture -- it asserts nothing about the data, it says where the scale is.
    """
    if hi <= lo or not all(map(math.isfinite, (lo, hi))):
        return [lo]
    raw = (hi - lo) / float(max(1, limit))
    mag = 10.0 ** math.floor(math.log10(raw)) if raw > 0 else 1.0
    for m in (1, 2, 2.5, 5, 10):
        if raw <= m * mag:
            step = m * mag
            break
    else:
        step = 10 * mag
    out, v = [], math.ceil(lo / step) * step
    while v <= hi + step * 1e-9 and len(out) < limit + 2:
        # -0.0 and float dust like 0.30000000000000004 both read as noise on an
        # axis; snap to the step's own precision.
        out.append(round(v, max(0, -int(math.floor(math.log10(step))) + 2)) + 0.0)
        v += step
    return out or [lo, hi]


def axis_title_svg(text, x, y):
    """One axis title. An axis of bare numerals does not say what it measures."""
    return ('  <text x="%.1f" y="%d" font-size="13" text-anchor="middle" '
            'fill="currentColor" opacity=".85">%s</text>%s' % (x, y, e(text), NL))


def forest_svg(res, outcome, window=None, bare=False):
    """A forest plot drawn from the stored per-trial and pooled estimates.

    `bare=True` RETURNS THE IMAGE AND NOTHING ELSE. Despite the name, the default return
    is not an SVG: it is `fig(...)` -- a card carrying its own <h3>, download links and
    explanatory note, built for the Analysis tab. The manuscript projector wraps its own
    <figure> with a numbered <figcaption>, so calling this without `bare` nests a complete
    Analysis-tab card inside a figure and the reader gets the heading "Forest plot" twice
    with two different captions. Caught on the first SGLT2 build, 2026-08-20: taking the
    template along with the logic, in the one session whose standing instruction is to take
    the logic and never the template.

    Added as a keyword defaulting to False so no existing caller changes behaviour.

    THE PLOT CARRIES NO TEXT NUMBERS except the row value labels, which are the
    same projected estimates the table beside it prints, and the axis ticks,
    which are round scale marks plus the null value. Placing a number on a scale
    is a rendering transform; it originates nothing."""
    # A NULLED ENTRY IS NOT PLOTTED. It is not counted in k, so plotting it drew a fourth
    # point on a forest whose caption says three -- the same contradiction CHK009_POOL_IDENTITY
    # found in the artefact, seen by a reader instead of by a gate.
    rows = [r for r in (res.get("per_trial") or [])
            if r.get("point") is not None and r.get("ci_low") is not None
                and r.get("ci_high") is not None
            and not (r.get("nulled") or str(r.get("trial_id") or r.get("nct")
                                            or "").startswith("NULLED:"))]
    if not rows:
        return ""
    pooled = res.get("pooled") or {}
    log = outcome.get("effect_scale") == "log"
    null_v = outcome.get("null_value", 1)
    tx = (lambda v: math.log(v)) if log else (lambda v: v)
    # The null is included in the range deliberately. On a review where every
    # interval excludes it, a null-only-in-the-tick-list axis puts the reference
    # line off the canvas -- the one line the whole plot is read against. Adding
    # it is deterministic and window-independent, so the cross-variant tick
    # invariance the display windows rely on is unaffected.
    lo = min([r["ci_low"] for r in rows] + [null_v]
             + ([pooled["ci_low"]] if pooled.get("ci_low") is not None else []))
    hi = max([r["ci_high"] for r in rows] + [null_v]
             + ([pooled["ci_high"]] if pooled.get("ci_high") is not None else []))
    if log and lo <= 0:
        return ""
    if window:
        # Only the MAPPING changes. lo and hi keep their data-derived values so
        # the tick labels below are identical in every variant.
        a, b = tx(window[0]), tx(window[1])
    else:
        a, b = tx(lo), tx(hi)
        pad = (b - a) * 0.08 or 1.0
        a, b = a - pad, b + pad
    W, L, R = 900, 250, 220
    X = lambda v: L + (tx(v) - a) / (b - a) * (W - L - R)
    ws = [1.0 / (r["log_se"] ** 2) if r.get("log_se") else 1.0 for r in rows]
    wmax = max(ws) or 1.0
    body, y, H, top = "", 26, 34, 26
    for r, w in zip(rows, ws):
        side = 5 + 9 * (w / wmax) ** 0.5
        # ROW VALUE LABELS. The last of the three things these figures were
        # missing. A forest plot whose numbers live only in a table beside it
        # makes the reader hold two objects at once; direct labelling is the
        # whole point of the form. The values are the SAME projected estimates
        # the table prints and are identical in every axis-range variant, so the
        # invariance check still holds -- only the mapping moves, never a label.
        body += ('  <line x1="%.1f" y1="%d" x2="%.1f" y2="%d" stroke="currentColor" '
                 'stroke-width="1.5"/>%s'
                 '  <rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" '
                 'fill="#1d4ed8"/>%s'
                 '  <text x="8" y="%d" font-size="15" fill="currentColor">%s</text>%s'
                 '  <text x="%d" y="%d" font-size="14" text-anchor="end" '
                 'fill="currentColor">%s (%s to %s)</text>%s'
                 % (X(r["ci_low"]), y, X(r["ci_high"]), y, NL,
                    X(r["point"]) - side / 2, y - side / 2, side, side, NL,
                    y + 4, e(str(r.get("trial_id", ""))), NL,
                    W - 4, y + 4, sig(r["point"], 3), sig(r["ci_low"], 3),
                    sig(r["ci_high"], 3), NL))
        y += H
    if pooled.get("point") is not None:
        cy, d = y + 4, 8
        body += ('  <polygon points="%.1f,%d %.1f,%d %.1f,%d %.1f,%d" '
                 'fill="#0f766e"/>%s'
                 '  <text x="8" y="%d" font-size="15" font-weight="700" '
                 'fill="currentColor">Pooled (%s)</text>%s'
                 % (X(pooled["ci_low"]), cy, X(pooled["point"]), cy - d,
                    X(pooled["ci_high"]), cy, X(pooled["point"]), cy + d, NL,
                    cy + 4, e(str(pooled.get("measure", ""))), NL))
        y += H
    height = y + 34
    ticks = ""
    for v in nice_log_ticks(lo, hi, null_v) if log else sorted({null_v, lo, hi}):
        ticks += ('  <line x1="%.1f" y1="%d" x2="%.1f" y2="%d" stroke="currentColor" stroke-opacity=".45" '
                  'stroke-dasharray="%s"/>%s'
                  '  <text x="%.1f" y="%d" font-size="14" text-anchor="middle" '
                  'fill="currentColor">%s</text>%s'
                  % (X(v), top - 18, X(v), y - 14,
                     "0" if v == null_v else "3 3", NL, X(v), y + 4, fmt(v), NL))
    # The measure comes from the object; no topic word is hardcoded here, because
    # this projector renders every review in the corpus and a drug name spliced
    # into it would be wrong on all but one of them.
    _meas = str((res.get("pooled") or {}).get("measure") or "Effect")
    ticks += axis_title_svg(
        "%s%s. %s = no difference." % (_meas, " (log scale)" if log else "",
                                       fmt(null_v)),
        L + (W - L - R) / 2.0, y + 26)
    height += 22
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" '
           'width="100%%" role="img" aria-label="Forest plot of the stored '
           'per-trial and pooled estimates">%s%s%s</svg>'
           % (W, height, NL, ticks + body, NL))
    if window is not None or bare:
        return svg
    return fig(svg, "Forest plot", "forest.svg",
               "Drawn from the same stored estimates the table above lists. The "
               "dashed guides mark the extremes of the plotted intervals; the "
               "solid guide is the null. Box area is proportional to "
               "inverse-variance weight.")


def scatter_svg(pts, xlab, ylab, invert_y=False, vline=None, diagonal=False):
    """Generic labelled scatter. Every plotted value is a STORED quantity.

    TICKS ARE LABELLED WITH STORED VALUES, NOT WITH THE PADDED AXIS ENDS. The
    first cut printed the padded extreme and the guard caught 13 numerals that
    were in neither the flat control nor the object."""
    if not pts:
        return ""
    W, H, L, R, T, B = 700, 300, 74, 24, 18, 46
    dxs = [q[0] for q in pts]
    xs = dxs + ([vline] if vline is not None else [])
    ys = [q[1] for q in pts]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    if x1 == x0:
        x0, x1 = x0 - 1, x1 + 1
    if y1 == y0:
        y0, y1 = y0 - 1, y1 + 1
    px, py = (x1 - x0) * .12, (y1 - y0) * .18
    ax0, ax1, ay0, ay1 = x0 - px, x1 + px, y0 - py, y1 + py
    X = lambda v: L + (v - ax0) / (ax1 - ax0) * (W - L - R)
    Y = ((lambda v: T + (v - ay0) / (ay1 - ay0) * (H - T - B)) if invert_y else
         (lambda v: H - B - (v - ay0) / (ay1 - ay0) * (H - T - B)))
    body = ""
    if vline is not None:
        body += ('<line x1="%.1f" y1="%d" x2="%.1f" y2="%d" stroke="currentColor" stroke-opacity=".4"/>%s'
                 % (X(vline), T, X(vline), H - B, NL))
    if diagonal:
        d0, d1 = max(ax0, ay0), min(ax1, ay1)
        if d1 > d0:
            body += ('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" '
                     'stroke="currentColor" stroke-opacity=".45" '
                     'stroke-dasharray="5 4"/>%s'
                     % (X(d0), Y(d0), X(d1), Y(d1), NL))
            body += ('<text x="%.1f" y="%.1f" font-size="12" '
                     'fill="currentColor" opacity=".7">no effect</text>%s'
                     % (X(d1) - 62, Y(d1) + 14, NL))
    for x, y, lab in pts:
        body += ('<circle cx="%.1f" cy="%.1f" r="5" fill="#1d4ed8" '
                 'fill-opacity=".8"/>%s' % (X(x), Y(y), NL))
        if lab:
            # Labels near the right edge are drawn to the LEFT of their point.
            # "parachute-h" -- clipped mid-word -- was the same lost-text defect
            # as the overflowing axis title, one element over.
            px = X(x)
            if px + 8 + 7.2 * len(str(lab)) > W - 4:
                body += ('<text x="%.1f" y="%.1f" font-size="14" '
                         'text-anchor="end" fill="currentColor">%s</text>%s'
                         % (px - 8, Y(y) + 4, e(str(lab)), NL))
            else:
                body += ('<text x="%.1f" y="%.1f" font-size="14" '
                         'fill="currentColor">%s</text>%s'
                         % (px + 8, Y(y) + 4, e(str(lab)), NL))
    # Ticks are rounded for display. Nobody labels an axis 139.209366, and the
    # six-decimal labels did more damage to these figures' credibility than any
    # other visual defect. The VALUE plotted is unchanged; only its label is
    # shortened, and the full number remains in the object and the SVG download.
    for v in nice_lin_ticks(min(dxs), max(dxs)):
        body += ('<line x1="%.1f" y1="%d" x2="%.1f" y2="%d" stroke="currentColor" '
                 'stroke-opacity=".25"/>%s'
                 '<text x="%.1f" y="%d" font-size="14" text-anchor="middle" '
                 'fill="currentColor">%s</text>%s'
                 % (X(v), H - B, X(v), H - B + 4, NL,
                    X(v), H - B + 16, fmt(v), NL))
    for v in nice_lin_ticks(min(ys), max(ys)):
        body += ('<line x1="%d" y1="%.1f" x2="%d" y2="%.1f" stroke="currentColor" '
                 'stroke-opacity=".25"/>%s'
                 '<text x="%d" y="%.1f" font-size="14" text-anchor="end" '
                 'fill="currentColor">%s</text>%s'
                 % (L - 4, Y(v), L, Y(v), NL, L - 6, Y(v) + 4, fmt(v), NL))
    # ARGUMENT SHIFT, found by reading the rendered aria-labels back off the page
    # rather than the code: the tuple fed aria-label's two slots with (NL, xlab)
    # and then handed ylab to the `>%s` immediately after the tag. So every
    # scatter announced itself to a screen reader as "\n against log effect" --
    # naming ONE axis, in the wrong slot -- and emitted its y-axis label as loose
    # character data inside <svg>, where SVG does not render it. Invisible on
    # screen, wrong to anything parsing the file. Named arguments now, so the
    # slots cannot silently reorder again.
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
            'width="100%" role="img" '
            'aria-label="{xl} (horizontal) against {yl} (vertical)">{nl}'
            '<line x1="{L}" y1="{T}" x2="{L}" y2="{yb}" stroke="currentColor"/>'
            '<line x1="{L}" y1="{yb}" x2="{xr}" y2="{yb}" '
            'stroke="currentColor"/>{nl}{body}'
            '<text x="{cx}" y="{ty}" font-size="14" text-anchor="middle" '
            'fill="currentColor">{xl}</text>{nl}'
            '<text x="13" y="{cy}" font-size="14" fill="currentColor" '
            'transform="rotate(-90 13 {cy})" text-anchor="middle">{yl}</text>'
            '{nl}</svg>').format(
                w=W, h=H, xl=e(xlab), yl=e(ylab), nl=NL, L=L, T=T, yb=H - B,
                xr=W - R, body=body, cx=(L + W - R) // 2, ty=H - 6,
                cy=(T + H - B) // 2)


def funnel_svg(points, pooled_log, null_log=0.0, measure="HR", k_note=""):
    """A funnel plot with an actual funnel.

    What shipped was a generic scatter: correct axes -- log effect against
    standard error, y inverted -- and NO pseudo-confidence contours, with its
    only reference line at the null rather than at the pooled estimate. The
    funnel in a funnel plot IS those contours; without them it is a scatter of
    four points and a reader has nothing to judge asymmetry against. Mahmood's
    words were "the funnel plot has no funnel", and he was right.

    Geometry follows the standard construction, cross-read against the
    implementation in F:\\allmeta\\funnel-plot:
      * pseudo-CI funnel: straight lines from (pooled, SE=0) to
        (pooled +/- z*SEmax, SEmax), at z = 1.96 and 2.576;
      * contour-enhanced significance regions (Peters 2008) radiating from the
        NULL at z = 1.645 / 1.96 / 2.576, so a reader can see whether a gap
        falls in a significant or a non-significant region;
      * a vertical line at the pooled estimate, which is what the funnel is
        centred on, in addition to the null.
    x is spaced linearly in log units and LABELLED on the ratio scale, which is
    how the measure is read everywhere else on the page.
    """
    if not points:
        return ""
    W, H, L, R, T, B = 700, 340, 74, 30, 20, 52
    pts = list(points_with_labels(points))
    se_max = max(max(1e-9, float(s)) for _, s, _ in pts)
    z95, z99, z90 = 1.959963985, 2.575829304, 1.644853627
    # Wide enough that the 99% funnel is inside the frame; otherwise the very
    # contours the plot exists for get clipped at the edge.
    half = max(z99 * se_max,
               max(abs(v - pooled_log) for v, _, _ in pts) * 1.15, 0.05)
    x0, x1 = pooled_log - half, pooled_log + half
    y1v = se_max * 1.10
    X = lambda v: L + (v - x0) / (x1 - x0) * (W - L - R)
    Y = lambda s: T + (s / y1v) * (H - T - B)          # SE increases DOWNWARD
    body = ""
    apex_x, apex_y, bot_y = X(null_log), Y(0.0), Y(y1v)

    def tri(zl, zr, fill):
        return ('<polygon points="%.1f,%.1f %.1f,%.1f %.1f,%.1f" fill="%s"/>%s'
                % (X(null_log - zl * y1v), bot_y, apex_x, apex_y,
                   X(null_log - zr * y1v), bot_y, fill, NL))

    body += ('<defs><clipPath id="funclip"><rect x="%d" y="%d" width="%d" '
             'height="%d"/></clipPath></defs><g clip-path="url(#funclip)">%s'
             % (L, T, W - L - R, H - T - B, NL))
    for zl, zr, fill in ((-z90, z90, "#e8eaee"), (z90, z95, "#f1f3f6"),
                         (-z95, -z90, "#f1f3f6"), (z95, z99, "#f8f9fb"),
                         (-z99, -z95, "#f8f9fb")):
        body += tri(zl, zr, fill)
    # Pseudo-CI funnel, centred on the POOLED estimate.
    for z, dash in ((z95, "4 3"), (z99, "2 3")):
        for sgn in (-1, 1):
            body += ('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" '
                     'stroke="currentColor" stroke-opacity=".55" '
                     'stroke-dasharray="%s"/>%s'
                     % (X(pooled_log), Y(0.0), X(pooled_log + sgn * z * y1v),
                        Y(y1v), dash, NL))
    body += ('<line x1="%.1f" y1="%d" x2="%.1f" y2="%.1f" stroke="currentColor" '
             'stroke-opacity=".8"/>%s'
             % (X(pooled_log), T, X(pooled_log), bot_y, NL))
    body += ('<line x1="%.1f" y1="%d" x2="%.1f" y2="%.1f" stroke="currentColor" '
             'stroke-opacity=".35" stroke-dasharray="5 4"/>%s'
             % (apex_x, T, apex_x, bot_y, NL))
    body += "</g>" + NL
    for (v, s, lab) in pts:
        body += ('<circle cx="%.1f" cy="%.1f" r="5" fill="#1d4ed8" '
                 'fill-opacity=".85"/>%s'
                 '<text x="%.1f" y="%.1f" font-size="13" '
                 'fill="currentColor">%s</text>%s'
                 % (X(v), Y(s), NL, X(v) + 8, Y(s) + 4, e(str(lab)), NL))
    # x ticks: round RATIO values, positioned by their logarithm.
    for rv in nice_log_ticks(math.exp(x0), math.exp(x1), math.exp(null_log)):
        lv = math.log(rv)
        if not (x0 <= lv <= x1):
            continue
        body += ('<text x="%.1f" y="%d" font-size="13" text-anchor="middle" '
                 'fill="currentColor">%s</text>%s' % (X(lv), H - B + 16,
                                                      fmt(rv), NL))
    for sv in nice_lin_ticks(0.0, y1v, 4):
        if sv < 0 or sv > y1v:
            continue
        body += ('<text x="%d" y="%.1f" font-size="13" text-anchor="end" '
                 'fill="currentColor">%s</text>%s'
                 % (L - 6, Y(sv) + 4, fmt(sv), NL))
    body += ('<line x1="%d" y1="%d" x2="%d" y2="%.1f" stroke="currentColor"/>'
             '<line x1="%d" y1="%.1f" x2="%d" y2="%.1f" stroke="currentColor"/>%s'
             % (L, T, L, bot_y, L, bot_y, W - R, bot_y, NL))
    # Short enough to fit the 700-unit viewBox. The first version ran off the
    # right edge and lost the end of its own sentence, which is the same
    # clipped-label defect this pass fixed on the manuscript figures. The k
    # caution lives in the caption, where there is room for it.
    body += axis_title_svg("%s -- dashed lines are the 95%% and 99%% funnel"
                           % measure, (L + W - R) / 2.0, H - 6)
    body += ('<text x="13" y="%d" font-size="13" fill="currentColor" '
             'transform="rotate(-90 13 %d)" text-anchor="middle">'
             'standard error (0 at top)</text>%s'
             % ((T + int(bot_y)) // 2, (T + int(bot_y)) // 2, NL))
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" '
            'width="100%%" role="img" aria-label="Funnel plot: %s (horizontal) '
            'against standard error (vertical, inverted), with pseudo-confidence '
            'contours">%s%s</svg>' % (W, H, e(measure), NL, body))


def points_with_labels(points):
    """Accepts [(x, se)] or [(x, se, label)] and always yields triples."""
    for p in points:
        if len(p) >= 3:
            yield p[0], p[1], p[2]
        else:
            yield p[0], p[1], ""


ROB_GLYPH = {"LOW": ("+", "#15803d", "#dcfce7"),
             "SOME CONCERNS": ("?", "#a16207", "#fef9c3"),
             "HIGH": ("\u2212", "#b91c1c", "#fee2e2"),
             "NOT ASSESSED": ("\u00b7", "#64748b", "#f1f5f9")}


def visual_abstract_svg(title, question, k, n_total, measure, point, lo, hi,
                        null_v, certainty, outcome_name, loo_note=""):
    """A graphical abstract PROJECTED from the object, never hand-drawn.

    IT MUST NOT IMPLY BENEFIT. The pooled estimate here is 0.872 with an
    interval of 0.746 to 1.018, which CONTAINS the null. A graphical abstract
    that shows a favourable point estimate without showing that its interval
    crosses no-difference is the conclusion-overstatement class this project
    documents in other people's papers, and it would be the most embarrassing
    thing we could ship -- a visual abstract is the one figure that travels
    without its caption.

    So the interval is drawn crossing the null line, the null is labelled in
    words as well as position, the verdict line states the finding in the
    direction the data supports, and no arrow, tick, colour or word implies a
    winner. Every quantity is passed in from the canonical object.
    """
    W, H = 900, 420
    crosses = (lo is not None and hi is not None and lo <= null_v <= hi)
    body = ""
    body += ('<rect x="1" y="1" width="%d" height="%d" fill="none" '
             'stroke="currentColor" stroke-opacity=".35" rx="8"/>%s'
             % (W - 2, H - 2, NL))

    def wrap(txt, width, x, y, size, lh, weight="400", op="1"):
        out, words, line = "", str(txt).split(), ""
        lines = []
        for wd in words:
            if len(line) + len(wd) + 1 > width:
                lines.append(line)
                line = wd
            else:
                line = (line + " " + wd).strip()
        if line:
            lines.append(line)
        for i, ln in enumerate(lines):
            out += ('<text x="%d" y="%d" font-size="%d" font-weight="%s" '
                    'fill="currentColor" opacity="%s">%s</text>%s'
                    % (x, y + i * lh, size, weight, op, e(ln), NL))
        return out, y + len(lines) * lh

    t, yy = wrap(title, 74, 28, 40, 17, 24, "700")
    body += t
    q, yy = wrap(question, 92, 28, yy + 10, 13, 18, "400", ".85")
    body += q

    # --- the estimate, drawn with the null in the middle --------------------
    # RATIO measures (null = 1) are drawn on a LOG axis: that is the scale they
    # are pooled on, and it puts 0.5 and 2.0 equidistant from the null, which is
    # what a reader needs.
    #
    # ADDITIVE measures -- mean difference, risk difference -- have a null of
    # ZERO and are pooled on the natural scale. log(lo / 0) is a ZeroDivisionError,
    # which is how this was found: alirocumab's object declares null_value 0 for
    # MD -54.66 (-60.75 to -48.56) and the build died outright (2026-08-16).
    # It is the same mistake as two others caught today -- the sig(x,3) rounding
    # and the exp(logEffect) back-transform that made four MD pages read 0.0000 --
    # all of them code that assumes a ratio because ratios are the common case.
    # Choose the axis from the null, never assume it.
    ax_y = yy + 74
    L, R = 190, 130
    import math as _m
    _log_axis = bool(null_v) and null_v > 0
    if _log_axis:
        span = max(abs(_m.log(lo / null_v)), abs(_m.log(hi / null_v)),
                   abs(_m.log(point / null_v))) * 1.45 or 0.5
        X = lambda v: L + (_m.log(v / null_v) + span) / (2 * span) * (W - L - R)
    else:
        span = max(abs(lo - null_v), abs(hi - null_v),
                   abs(point - null_v)) * 1.45 or 0.5
        X = lambda v: L + ((v - null_v) + span) / (2 * span) * (W - L - R)
    body += ('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="currentColor" '
             'stroke-opacity=".35"/>%s' % (L, ax_y, W - R, ax_y, NL))
    body += ('<line x1="%.1f" y1="%d" x2="%.1f" y2="%d" stroke="currentColor" '
             'stroke-width="1.5"/>%s'
             % (X(null_v), ax_y - 34, X(null_v), ax_y + 20, NL))
    body += ('<text x="%.1f" y="%d" font-size="12" text-anchor="middle" '
             'fill="currentColor" opacity=".85">no difference</text>%s'
             % (X(null_v), ax_y + 36, NL))
    body += ('<line x1="%.1f" y1="%d" x2="%.1f" y2="%d" stroke="#1d4ed8" '
             'stroke-width="3"/>%s'
             % (X(lo), ax_y - 14, X(hi), ax_y - 14, NL))
    for v in (lo, hi):
        body += ('<line x1="%.1f" y1="%d" x2="%.1f" y2="%d" stroke="#1d4ed8" '
                 'stroke-width="3"/>%s' % (X(v), ax_y - 21, X(v), ax_y - 7, NL))
    body += ('<rect x="%.1f" y="%.1f" width="12" height="12" fill="#1d4ed8"/>%s'
             % (X(point) - 6, ax_y - 20, NL))
    body += ('<text x="%d" y="%d" font-size="15" font-weight="700" '
             'fill="currentColor">%s %s</text>%s'
             % (24, ax_y - 10, e(str(measure)), fmt(point), NL))
    body += ('<text x="%d" y="%d" font-size="13" fill="currentColor" '
             'opacity=".85">%s%% CI %s to %s</text>%s'
             % (24, ax_y + 10, "95", fmt(lo), fmt(hi), NL))

    # --- the verdict, stated in the direction the data supports -------------
    vy = ax_y + 66
    verdict = ("The interval INCLUDES no difference: this pooled estimate is "
               "compatible with no effect." if crosses else
               "The interval excludes no difference.")
    v1, vy2 = wrap(verdict, 96, 28, vy, 15, 20, "700")
    body += v1
    facts = "%s trials, %s participants. Outcome: %s. GRADE certainty: %s." % (
        fmt(k), n_total or "n/a", outcome_name, certainty or "not rated")
    f1, vy3 = wrap(facts, 104, 28, vy2 + 8, 13, 18, "400", ".9")
    body += f1
    if loo_note:
        l1, _ = wrap(loo_note, 104, 28, vy3 + 6, 12, 17, "400", ".8")
        body += l1
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" '
            'width="100%%" role="img" aria-label="Visual abstract: %s '
            '(horizontal) against no difference (vertical reference line), '
            'showing the pooled estimate and its confidence interval">%s%s</svg>'
            % (W, H, e(str(measure)), NL, body))


def rob_traffic_light_svg(trials, domains, assessors, cell):
    """Cochrane-style risk-of-bias traffic light, BOTH assessors per cell.

    Colour AND glyph, deliberately: + / ? / minus survive greyscale printing and
    colour-blind reading, which a colour-only traffic light does not. Each cell is
    split because this review ran two independent cross-family assessors and never
    reconciled them -- showing one column would be a reconciliation presented as an
    observation, which is the thing the RoB card already refuses to do. Where an
    assessor has no judgement the cell says so rather than defaulting to low.
    """
    if not trials or not domains:
        return ""
    LW, CW, RH, TOP = 150, 92, 40, 54
    W = LW + CW * len(domains) + 16
    H = TOP + RH * len(trials) + 54
    body = ""
    for j, dm in enumerate(domains):
        x = LW + j * CW + CW / 2.0
        body += ('<text x="%.1f" y="%d" font-size="13" text-anchor="middle" '
                 'fill="currentColor" font-weight="600">%s</text>%s'
                 % (x, TOP - 14, e(str(dm)), NL))
    for i, tr in enumerate(trials):
        y = TOP + i * RH
        body += ('<text x="6" y="%.1f" font-size="14" fill="currentColor">%s</text>%s'
                 % (y + RH / 2.0 + 4, e(str(tr)), NL))
        for j, dm in enumerate(domains):
            cx = LW + j * CW + CW / 2.0
            for a, dx in ((0, -13), (1, 13)):
                v = (cell(tr, dm, a) or "NOT ASSESSED").upper()
                g, fg, bg = ROB_GLYPH.get(v, ROB_GLYPH["NOT ASSESSED"])
                body += ('<circle cx="%.1f" cy="%.1f" r="11" fill="%s" '
                         'stroke="%s"/>%s'
                         '<text x="%.1f" y="%.1f" font-size="14" '
                         'text-anchor="middle" fill="%s" font-weight="700">%s</text>%s'
                         % (cx + dx, y + RH / 2.0, bg, fg, NL,
                            cx + dx, y + RH / 2.0 + 5, fg, e(g), NL))
    ly = TOP + RH * len(trials) + 22
    body += ('<text x="6" y="%d" font-size="12" fill="currentColor">'
             'Left circle: %s. Right circle: %s. '
             '+ low, ? some concerns, \u2212 high, \u00b7 not assessed.</text>%s'
             % (ly, e(str(assessors[0])), e(str(assessors[1])), NL))
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" '
            'width="100%%" role="img" aria-label="Risk-of-bias traffic light: '
            'trials (rows) against domains (columns), two assessors per cell">'
            '%s%s</svg>' % (W, H, NL, body))


def prisma_flow_svg(boxes):
    """PRISMA-style flow. Boxes with no recorded count SAY SO.

    The identification counts for this corpus were never recorded by the pipeline
    that produced it and cannot be reconstructed without inventing numbers, so
    those boxes are drawn as NOT RECORDED rather than filled with a plausible
    figure or quietly omitted. A flow diagram missing its top box reads as an
    oversight; one that states the gap reads as a decision, and only the second is
    true here.
    """
    if not boxes:
        return ""
    W, BW, BH, GAP, L = 720, 430, 66, 26, 24
    H = len(boxes) * (BH + GAP) + 30
    body = ""
    for i, b in enumerate(boxes):
        y = 14 + i * (BH + GAP)
        known = b.get("n") is not None
        # No CSS variable here. These SVGs are also offered as standalone
        # vector downloads, where var(--soft) resolves to nothing and the
        # exporter warns "Can't handle color". The dashed border and the
        # words NOT RECORDED already carry the distinction, so the fill was
        # redundant as well as unportable.
        fill = "none"
        dash = "" if known else ' stroke-dasharray="5 4"'
        body += ('<rect x="%d" y="%d" width="%d" height="%d" fill="%s" '
                 'stroke="currentColor" stroke-opacity=".55"%s rx="4"/>%s'
                 % (L, y, BW, BH, fill, dash, NL))
        head = b.get("label", "")
        body += ('<text x="%d" y="%d" font-size="13" fill="currentColor" '
                 'font-weight="600">%s</text>%s' % (L + 12, y + 22, e(head), NL))
        val = ("n = %s" % fmt(b["n"])) if known else "NOT RECORDED"
        body += ('<text x="%d" y="%d" font-size="13" fill="currentColor">%s</text>%s'
                 % (L + 12, y + 42, e(val), NL))
        if b.get("note"):
            body += ('<text x="%d" y="%d" font-size="11" fill="currentColor" '
                     'opacity=".75">%s</text>%s'
                     % (L + 12, y + 58, e(str(b["note"])[:78]), NL))
        if b.get("side"):
            body += ('<text x="%d" y="%d" font-size="12" fill="currentColor" '
                     'opacity=".85">%s</text>%s'
                     % (L + BW + 16, y + 30, e(str(b["side"])[:40]), NL))
            body += ('<line x1="%d" y1="%.1f" x2="%d" y2="%.1f" '
                     'stroke="currentColor" stroke-opacity=".45"/>%s'
                     % (L + BW, y + BH / 2.0, L + BW + 12, y + BH / 2.0, NL))
        if i < len(boxes) - 1:
            body += ('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="currentColor" '
                     'stroke-opacity=".55"/>%s'
                     '<polygon points="%d,%d %d,%d %d,%d" fill="currentColor" '
                     'fill-opacity=".55"/>%s'
                     % (L + BW / 2, y + BH, L + BW / 2, y + BH + GAP - 8, NL,
                        L + BW / 2 - 5, y + BH + GAP - 8, L + BW / 2 + 5,
                        y + BH + GAP - 8, L + BW / 2, y + BH + GAP, NL))
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" '
            'width="100%%" role="img" aria-label="PRISMA flow of records through '
            'screening, with unrecorded stages stated as not recorded">%s%s</svg>'
            % (W, H, NL, body))


def not_computable_svg(title, reason, state="not computable"):
    """An explicit empty state. Never a drawn plot standing in for a real one.

    A figure that cannot be computed from the object is not drawn at all: a
    reader takes a rendered panel as a diagnostic that was RUN, and a plausible
    picture in place of an absent analysis is the exact failure this project
    exists to catch.

    `state` distinguishes the two honest reasons, because they are different
    facts about the review. NOT COMPUTABLE means the object lacks the inputs.
    NOT DRAWN means the inputs exist and the result would be uninformative at
    this k. The first version put "not computable" in the title of a panel whose
    own reason line began "Computable but uninformative", so the panel
    contradicted itself in two lines.
    """
    W, LH = 700, 22
    # Wrapped on WORD boundaries. Slicing the reason at a fixed character count
    # broke it mid-word -- "its shap" / "e is read" -- which is the same
    # lost-text defect as the clipped axis title and the clipped point label,
    # for the third time in this file.
    words, lines, cur = str(reason).split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > 86:
            lines.append(cur)
            cur = w
        else:
            cur = (cur + " " + w).strip()
    if cur:
        lines.append(cur)
    H = 64 + LH * max(1, len(lines))
    body = ('<text x="%d" y="42" font-size="15" text-anchor="middle" '
            'fill="currentColor" font-weight="600">%s &mdash; %s</text>%s'
            % (W // 2, e(title), e(state), NL))
    for i, ln in enumerate(lines):
        body += ('<text x="%d" y="%d" font-size="13" text-anchor="middle" '
                 'fill="currentColor" opacity=".85">%s</text>%s'
                 % (W // 2, 70 + i * LH, e(ln), NL))
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" '
            'width="100%%" role="img" aria-label="%s: %s">%s'
            '<rect x="1" y="1" width="%d" height="%d" fill="none" '
            'stroke="currentColor" stroke-opacity=".4" stroke-dasharray="6 5" '
            'rx="6"/>%s%s</svg>'
            % (W, H, e(title), e(state), NL, W - 2, H - 2, NL, body))


def rows_svg(rows, null_v, label_w=200, measure="", axis_note=""):
    """Point-and-interval rows on a log axis (leave-one-out, cumulative).

    These panels carried ONE tick -- the null -- no axis title, and no value on
    any row. That is a picture of a result rather than a report of one: a reader
    could see that an interval crossed the null but could not read what any
    estimate WAS without leaving the figure. Now they carry round ticks, a title
    naming the measure, and each row's own estimate, which are the same projected
    values the surrounding table prints.
    """
    if not rows:
        return ""
    # R widened from 30 to leave room for the row value labels; without this they
    # would be clipped at the right edge, which is the defect one panel over.
    W, R, T, H = 700, 172, 22, 32
    lo = min(min(r["ci_low"] for r in rows), null_v)
    hi = max(max(r["ci_high"] for r in rows), null_v)
    if lo <= 0:
        return ""
    a, b = math.log(lo), math.log(hi)
    pad = (b - a) * .1 or 1.0
    a, b = a - pad, b + pad
    X = lambda v: label_w + (math.log(v) - a) / (b - a) * (W - label_w - R)
    body, y = "", T
    for r in rows:
        body += ('<line x1="%.1f" y1="%d" x2="%.1f" y2="%d" stroke="currentColor"/>%s'
                 '<rect x="%.1f" y="%d" width="8" height="8" fill="#1d4ed8"/>%s'
                 '<text x="6" y="%d" font-size="14" fill="currentColor">%s</text>%s'
                 '<text x="%d" y="%d" font-size="13" text-anchor="end" '
                 'fill="currentColor">%s (%s to %s)</text>%s'
                 % (X(r["ci_low"]), y, X(r["ci_high"]), y, NL,
                    X(r["point"]) - 4, y - 4, NL, y + 4, e(str(r["label"])), NL,
                    W - 6, y + 4, sig(r["point"], 3), sig(r["ci_low"], 3),
                    sig(r["ci_high"], 3), NL))
        y += H
    for v in nice_log_ticks(lo, hi, null_v):
        body += ('<line x1="%.1f" y1="%d" x2="%.1f" y2="%d" stroke="currentColor" '
                 'stroke-opacity=".4" stroke-dasharray="%s"/>%s'
                 '<text x="%.1f" y="%d" font-size="14" text-anchor="middle" '
                 'fill="currentColor">%s</text>%s'
                 % (X(v), T - 14, X(v), y - 16, "0" if v == null_v else "3 3", NL,
                    X(v), y + 2, fmt(v), NL))
    _t = "%s (log scale). %s = no difference.%s" % (
        str(measure or "Effect"), fmt(null_v),
        (" " + str(axis_note)) if axis_note else "")
    body += axis_title_svg(_t, label_w + (W - label_w - R) / 2.0, y + 22)
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" '
            'width="100%%" role="img" aria-label="point and interval rows">%s%s'
            '</svg>' % (W, y + 34, NL, body))


# --------------------------------------------------------------- small helpers
def kv_card(title, pairs, note=""):
    """A label/value card. Emits nothing when every value is empty."""
    rows = "".join("    <tr><th scope='col'>%s</th><td>%s</td></tr>%s" % (k, v, NL)
                   for k, v in pairs if v)
    if not rows:
        return ""
    return ("<div class='card'>%s  <h3>%s</h3>%s  <table>%s%s  </table>%s"
            % (NL, title, NL, NL, rows, NL)
            + ("  <p><small>%s</small></p>%s" % (note, NL) if note else "")
            + "</div>" + NL)


def extraction_provenance_table(canon):
    """The Extraction tab's audit surface: one row per extracted value.

    WHY THIS EXISTS
        The tab already carried the numbers, the quoted sentences and the source
        URLs -- but scattered through ~36,000 characters of prose, with ZERO
        clickable links. A reader who wants to check us had to read the
        manuscript and retype a URL. That fails the tab's one job.

        This is the harness's own rule made visible to a reader: a referent must
        carry a per-key locator, and agreement without provenance is INVALID.
        Here the locator is a resolvable link, and the row states whether the
        value was READ from a source or DERIVED by us.

    FOUR COLUMNS, ALL FOUR ALWAYS PRESENT
        1. the value as extracted
        2. the verbatim sentence it was read from
        3. a resolvable link, plus PMID/NCT as text (the registration id is the
           identity key -- accepting a covering label instead is how PARACHUTE-HF
           was once read as ANSWER-HF)
        4. read vs derived, with the derivation named when we computed it

    A value with no traceable source SAYS SO in its own row. It is never dropped:
    an empty extraction table is honest, a partial one that looks complete is not.
    """
    trials = ((canon.get("inputs") or {}).get("trials")) or []
    if not trials:
        return ""
    outcomes = {o.get("id"): o for o in (canon.get("outcomes") or []) if isinstance(o, dict)}
    rows = []
    for t in trials:
        nct, pmid = t.get("nct"), t.get("pmid")
        ident = []
        if nct:
            ident.append("<a href='https://clinicaltrials.gov/study/%s' rel='noopener'>%s</a>"
                         % (quote(str(nct)), e(str(nct))))
        else:
            ident.append("<em>no registration id recorded</em>")
        if pmid:
            ident.append("PMID <a href='https://pubmed.ncbi.nlm.nih.gov/%s/' rel='noopener'>%s</a>"
                         % (quote(str(pmid)), e(str(pmid))))
        for oid, bo in (t.get("by_outcome") or {}).items():
            if not isinstance(bo, dict):
                continue
            eff = bo.get("effect") or {}
            pt, lo, hi = eff.get("point"), eff.get("ci_low"), eff.get("ci_high")
            oc = outcomes.get(oid) or {}
            meas = oc.get("measure") or eff.get("measure") or ""
            if pt is None:
                val = "<em>no effect value held for this outcome</em>"
            else:
                val = "<strong>%s %s</strong>" % (e(str(meas)), fmt(pt))
                if lo is not None and hi is not None:
                    val += " (%s%% CI %s to %s)" % (eff.get("ci_level", 95), fmt(lo), fmt(hi))

            prov = bo.get("provenance") or {}
            quotes = prov.get("source_quotes") or []
            if quotes:
                q = "".join("<blockquote><small>&ldquo;%s&rdquo;</small></blockquote>"
                            % e(str(s)) for s in quotes)
            else:
                q = ("<em>no source sentence recorded &mdash; this value cannot be "
                     "checked against a quoted line here</em>")

            links = list(ident)
            su = bo.get("source_url")
            if su:
                links.append("<a href='%s' rel='noopener'>source</a>" % e(str(su)))
            for cid, c in ((bo.get("cascade") or {}).get("checked") or {}).items():
                if isinstance(c, dict) and c.get("url") and c.get("status") == "found":
                    links.append("<a href='%s' rel='noopener'>%s</a>"
                                 % (e(str(c["url"])), e(str(cid))))
            if not su and not any("href" in x for x in links):
                links.append("<em>no resolvable source link</em>")

            df = eff.get("derived_from")
            tag = prov.get("tag")
            if df == "published_hazard_ratio" or (tag == "MEASURED" and df):
                rd = "<strong>READ</strong> from the source as printed"
            elif df:
                rd = "<strong>DERIVED</strong> by us from %s" % e(str(df))
            elif tag:
                rd = e(str(tag))
            else:
                rd = "<em>not stated whether read or derived</em>"
            note = eff.get("derivation_note") or prov.get("quote_note")
            if note:
                rd += "<br><small>%s</small>" % e(str(note))

            rows.append(
                "    <tr><td>%s<br><small>%s</small></td><td>%s</td><td>%s</td>"
                "<td>%s</td><td>%s</td></tr>%s"
                % (e(str(t.get("name") or t.get("id") or "?")), e(str(oid)),
                   val, q, " &middot; ".join(links), rd, NL))
    if not rows:
        return ""
    # A CONVERTED page must say what this tab CANNOT do, at the top, before the table.
    # This is the audit surface: a reader comes here to check us against sources. On a
    # converted page there are none to check against, and discovering that by clicking
    # an empty link column is finding out the hard way. Thin is not the problem;
    # silence about WHY it is thin is. The tab must not imply a provenance it lacks.
    # PROJECTED FROM WHAT THE OBJECT HOLDS, NOT FROM THE MODE LABEL.
    #
    # This used to fire on build_mode == "CONVERTED" alone and assert that "no
    # verbatim source sentence and no resolvable link to a paper was
    # recoverable". On ABLATION_AF that sentence became FALSE the moment the four
    # trial rows were re-read from their registry records and their publications
    # -- while the protocol, search, screening, risk-of-bias and certainty layers
    # stayed genuinely unrecoverable, so the mode label was still correct and
    # could not be flipped without making the ABSENCE reasons false instead.
    #
    # A note that describes the artefact must be derived from the artefact. So:
    # a converted object whose cells carry NO quotes says it cannot be checked; a
    # converted object whose cells DO carry quotes says which layer was rebuilt
    # and which was not. Neither sentence is available to be wrong about the
    # other, which is the property an expected-section manifest has and a
    # hand-written caption does not.
    cnote = ""
    if canon.get("build_mode") == "CONVERTED":
        _q = sum(1 for t in trials
                 for bo in (t.get("by_outcome") or {}).values()
                 if isinstance(bo, dict)
                 and ((bo.get("provenance") or {}).get("source_quotes")))
        _tot = sum(1 for t in trials
                   for bo in (t.get("by_outcome") or {}).values()
                   if isinstance(bo, dict))
        if not _q:
            cnote = ("  <div class='absent-state' role='note'><strong>These values cannot be "
                     "traced to a paper from this page.</strong> This object was RECOVERED from "
                     "the published page itself rather than assembled from source documents. "
                     "Each value below traces to the page it came from, but <strong>no verbatim "
                     "source sentence and no resolvable link to a paper was recoverable</strong>, "
                     "and the intervals are computed from a stored estimate and variance rather "
                     "than read from anything a source printed. Treat every row as unverified "
                     "against its source until it is checked against the trial report.</div>" + NL)
        else:
            cnote = ("  <div class='absent-state' role='note'><strong>The trial data on this "
                     "tab have been re-read from source; the rest of this review has not."
                     "</strong> This object was originally RECOVERED from a published page. "
                     "%d of %d value cells now carry a verbatim source sentence and a "
                     "resolvable link, read from the trial's own registry record or "
                     "publication. <strong>The protocol, search, screening log, risk-of-bias "
                     "assessment and certainty rating remain unrecoverable</strong> and are "
                     "recorded as absent on their own tabs. So the numbers below are "
                     "checkable and the REVIEW around them is still not a source-built "
                     "review.</div>" % (_q, _tot) + NL)

    # cnote is a FORMAT ARGUMENT, not a concatenation: `"a" + x + "b" % args` binds
    # the % to the last literal group only, which silently changes the argument count.
    return ("<div class='card'>%s  <h2>Extracted values, and where each came from</h2>%s%s"
            "  <p>One row per extracted value. Every row carries the value, the verbatim "
            "sentence it was read from, a resolvable link to the source, and whether the "
            "number was read or derived. Where any of those is absent the row says so "
            "rather than omitting the value.</p>%s"
            "  <table>%s    <tr><th>Trial / outcome</th><th>Value as extracted</th>"
            "<th>Verbatim source sentence</th><th>Source links</th>"
            "<th>Read or derived</th></tr>%s%s  </table>%s</div>%s"
            % (NL, NL, cnote, NL, NL, NL, "".join(rows), NL, NL))


def _slug(text, used):
    """A stable, unique, readable fragment id for a heading."""
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:48] or "section"
    base, n = s, 2
    while s in used:
        s, n = "%s-%d" % (base, n), n + 1
    used.add(s)
    return s


def _anchor_headings(body, tid):
    """Give every <h2>/<h3> in a panel an id, and return (body, [(id, text)]).

    Headings that ALREADY carry an id keep it -- rewriting one would break any
    link already pointing at it, and a fragment that used to resolve and now
    silently scrolls nowhere is worse than no fragment at all.

    The heading text is copied VERBATIM into the jump list. That rule was
    established when a digit-strip turned "RoB-2 assessment" into "RoB- assessment"
    in the first line of nearly every tab: the no-unprojected-numerals rule governs
    numbers the page ASSERTS, and an echo of an already-projected heading asserts
    nothing. An edited echo can differ from what it claims to point at; a verbatim
    one cannot.

    THE RETURNED TEXT IS PLAIN TEXT, NOT MARKUP, AND THAT DISTINCTION IS THE
    DEFECT THIS FIXES. `inner` is already-escaped HTML. Stripping its tags yields
    ESCAPED TEXT -- "(&#x27;as Adjudicated&#x27;)" -- and the caller escapes what
    it is handed, producing "&amp;#x27;" and putting the literal characters
    `&#x27;` in front of a reader.

    It went unnoticed because no heading in this corpus had previously contained
    a character needing escaping. SGLT2_CKD's outcome name quotes EMPA-KIDNEY's
    registry title, which contains apostrophes -- "('as Adjudicated')" -- and six
    jump-list entries on one page rendered them raw. The defect is latent
    everywhere and fires on any heading containing an apostrophe, an ampersand, a
    quote or an angle bracket.

    Same family as the raw-HTML-versus-rendered-text rule in the ledger: a
    boundary where the REPRESENTATION changes, crossed without anyone saying
    which side they were on. Unescaping here means the value is plain text from
    this point outward, and is escaped exactly once, at render.
    """
    used, heads = set(), []

    def repl(m):
        lvl, attrs, inner = m.group(1), m.group(2) or "", m.group(3)
        text = _html.unescape(
            re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", inner))).strip(" .·-")
        if not text:
            return m.group(0)
        have = re.search(r'\bid\s*=\s*["\']([^"\']+)["\']', attrs)
        if have:
            hid = have.group(1)
            used.add(hid)
            heads.append((hid, text))
            return m.group(0)
        hid = _slug("%s-%s" % (tid, text), used)
        heads.append((hid, text))
        return "<%s id=\"%s\"%s>%s</%s>" % (lvl, hid, attrs, inner, lvl)

    body = re.sub(r"<(h[23])((?:\s[^>]*)?)>(.*?)</\1>", repl, body, flags=re.S)
    return body, heads


# Deep-linking for the tab strip. The tabs are CSS radio-driven, which is why
# they work with no JavaScript at all -- but it also meant THE AUDIT SURFACE HAD
# NO ADDRESS. There was no way to send anyone a link to the extraction table,
# only instructions for finding it, and every reload dropped the reader back on
# "1. Protocol". For a project whose whole argument is that a reader without
# full-text access can check us, an unaddressable audit surface is the defect.
#
# This is PROGRESSIVE ENHANCEMENT, deliberately: with JS off the CSS tabs behave
# exactly as before and the first tab opens. Nothing here is load-bearing for
# reading the page; it only makes a URL mean something.
#
# It resolves three shapes, because a link is copied from wherever the reader
# happens to be standing:
#   #extract        the tab, by its short name
#   #rt-extract     the radio's own id, which is what a browser devtools copy gives
#   #pn-extract     the panel's id
#   #<heading-id>   any heading INSIDE a panel -- this one opens the containing
#                   tab first, which the naive version did not, so a jump-list
#                   link copied out of the page scrolled to a zero-height panel
#                   and appeared to do nothing.
_TAB_HASH_JS = """<script>
(function(){
  function tabFor(el){
    var p = el && el.closest ? el.closest("section.panel") : null;
    return p ? document.getElementById("rt-" + p.id.replace(/^pn-/, "")) : null;
  }
  function apply(hash){
    var raw = (hash || "").replace(/^#/, "");
    if (!raw) return false;
    var key = raw.replace(/^pn-/, "").replace(/^rt-/, "");
    var radio = document.getElementById("rt-" + key), target = null;
    if (!radio) {
      var el = document.getElementById(raw);
      if (!el) return false;
      radio = tabFor(el);
      target = el;
    }
    if (!radio) return false;
    radio.checked = true;
    var scrollTo = target || document.getElementById("pn-" + radio.id.replace(/^rt-/, ""));
    if (scrollTo && scrollTo.scrollIntoView) scrollTo.scrollIntoView({block: "start"});
    return true;
  }
  apply(location.hash);
  window.addEventListener("hashchange", function(){ apply(location.hash); });
  var radios = document.querySelectorAll('input[name="rmtab"]');
  for (var i = 0; i < radios.length; i++) {
    radios[i].addEventListener("change", function(){
      if (!this.checked || !history.replaceState) return;
      history.replaceState(null, "", "#" + this.id.replace(/^rt-/, ""));
    });
  }
})();
</script>"""


def tabbed_body(canon, parts, page):
    """Distribute the already-built parts across the tabs the spec declares.

    This function BUILDS NOTHING. It concatenates strings the projectors already
    produced and wraps them in a nav -- there is no slot here for a sentence about
    the review, so template contamination has nowhere to live.

    THE CONTENT FLOOR. The old test was `if page.get(k)` -- string-non-empty --
    which a heading plus an empty textarea passes. Below the floor is NOT a licence
    to delete: the body is carried into the previous populated panel."""
    panels = nav = inputs = css = ""
    first = None
    skipped, pending, carry_into = [], [], None
    for tid, label, page_keys, out_keys in TABS:
        chunks = [page[k] for k in page_keys if page.get(k)]
        for d in parts:
            got = [d[k] for k in out_keys if d.get(k)]
            if got:
                chunks.append("<h2>%s</h2>%s%s" % (d["name"], NL, "".join(got)))
        body = "".join(chunks)
        text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", body)).strip()
        data = len(re.findall(r"<(?:table|svg|li)[ >/]", body))
        # THE DATA LIMB IS A TEST FOR A DATA PANEL, AND THE PAPER TAB IS NOT ONE.
        # `data < 1` catches an analysis tab that talks about a forest plot without carrying
        # one, which is a real protection worth keeping. A MANUSCRIPT IS PROSE BY DEFINITION
        # and contains no table, figure or list -- so the limb classified 11,124 characters of
        # projected manuscript as "not held in this object" and printed a red banner saying no
        # manuscript had been generated, DIRECTLY ABOVE THE MANUSCRIPT. The thin-content limb
        # still applies to this tab: a page with no manuscript falls under FLOOR_CHARS and is
        # correctly reported absent.
        prose_tab = tid in ("paper",)
        if len(text) < FLOOR_CHARS or (data < 1 and not prose_tab):
            skipped.append((tid, len(text), data))
            # Emit the tab with an honest state instead of dropping it. Any thin
            # body it did carry is shown beneath the statement rather than being
            # merged invisibly into the previous panel.
            _tbl = (ABSENT_STATE_CONVERTED
                    if (canon.get("build_mode") == "CONVERTED") else ABSENT_STATE)
            # THREE STATES, NOT TWO. If the thin body carries something real, the page says
            # which part is held rather than denying the whole and then printing it.
            _carries_something = bool(re.search(r"<(?:pre|table|svg|li|dl)[ >/]", body))                 or len(re.sub(r"<[^>]+>", " ", body).strip()) > 80
            if _carries_something and tid in PARTIAL_STATE:
                _label = "Partially held."
                # COMPUTED WHERE IT CAN BE, RECITED ONLY WHERE IT CANNOT. The screen
                # tab's note names counts it can read off the panel; if it cannot read
                # them it returns None and the constant stands.
                note = (screen_partial_note(body) if tid == "screen" else None) \
                    or PARTIAL_STATE[tid]
            else:
                _label = "Not held in this object."
                note = _tbl.get(tid, "No content is held in this object for this section.")
            # THE MANUSCRIPT IS THE TAB A READER ARRIVES FOR, SO IT IS THE ONE THAT OPENS.
            #
            # The tabs work: `.panel{height:0;overflow:hidden}` and only the checked radio's
            # panel expands. What was wrong is WHICH ONE was checked. `rt-protocol` was
            # checked on load because it is first in the list, so a reader arriving to read
            # the review met the Protocol panel and had to find "7. Paper Studio" -- seventh
            # of eight, behind Search, Screening, Extraction, the Analysis Suite and
            # Scientific Output. Five rounds of "it reads like code" were answered by
            # rewriting a panel he had to click six tabs past to see.
            #
            # Nothing is moved and no id changes: `paper` simply takes the default. The
            # analysis suite is one click away, which is the right way round for a page whose
            # subject is a review.
            checked = ""
            if tid == "paper":
                checked = " checked"
                first = tid
            elif first is None and not any(t[0] == "paper" for t in TABS):
                first, checked = tid, " checked"
            inputs += '<input type="radio" name="rmtab" id="rt-%s"%s>%s' % (tid, checked, NL)
            nav += ' <label for="rt-%s">%s</label>%s' % (tid, label, NL)
            carry_into = " </section>" + NL + "<!--end-%s-->" % tid
            panels += (' <section class="panel" id="pn-%s">%s'
                       '<div class="absent-state" role="note">'
                       '<strong>%s</strong> %s</div>%s%s%s'
                       % (tid, NL, _label, note, NL, body, carry_into))
            css += (" #rt-%s:checked ~ .panels > #pn-%s{height:auto;overflow:visible}%s"
                    ' #rt-%s:checked ~ .tabnav label[for="rt-%s"]{color:#111;'
                    "background:#fff;border-color:#d4d4d8;box-shadow:0 2px 0 0 #fff}%s"
                    % (tid, tid, NL, tid, tid, NL))
            pending = []
            continue
        # The digit strip here produced "Open disagreements ()", "RoB- assessment"
        # and "ClinicalTrials.gov API v" in the first line of nearly every tab. It
        # was the no-unprojected-numerals rule applied at the wrong scope: that
        # rule governs numbers the page ASSERTS, and a table of contents asserts
        # nothing -- it echoes a heading that has already been projected and has
        # already passed the rule. Copying the heading verbatim is therefore
        # strictly safer than editing it, because an edited echo can differ from
        # what it claims to point at.
        # THE JUMP LIST NOW EMITS THE PANEL'S OWN SECTIONS, and links to them.
        #
        # It read <h3> ONLY, so on the Extraction tab it listed "What was
        # measured / What this pool holds constant / Contributing trials / The
        # methods rule governing this decision" -- and omitted the two headings
        # the reader actually came for, "Extracted values, and where each came
        # from" and "Sources", because those are <h2>. The one navigational aid
        # that should have pointed at the audit surface was the one thing that
        # did not mention it.
        #
        # THIRD INSTANCE of a hand-maintained surface drifting from what it
        # describes, after the authored cards and the section manifest. The
        # pattern each time: a list written once against the content as it then
        # was, never re-derived. So this derives it, every build, from the
        # headings actually present -- and makes the entries ANCHORS, since a
        # jump list you cannot jump from is a list of names.
        body, heads = _anchor_headings(body, tid)
        toc = ("  <p class='toc'><strong>In this section:</strong> "
               + " &middot; ".join('<a href="#%s">%s</a>' % (hid, e(htxt))
                                   for hid, htxt in heads) + "</p>" + NL) if heads else ""
        # THE MANUSCRIPT OPENS. Second of two tab-emitting sites, and the one the delivered
        # pages actually use -- patching the other alone changed nothing, which is how you
        # spend a build finding out there were two.
        checked = ""
        if tid == "paper":
            checked, first = " checked", tid
        elif first is None and not any(t[0] == "paper" for t in TABS):
            first, checked = tid, " checked"
        inputs += '<input type="radio" name="rmtab" id="rt-%s"%s>%s' % (tid, checked, NL)
        nav += '  <label for="rt-%s">%s</label>%s' % (tid, label, NL)
        carry_into = "  </section>" + NL + "<!--end-%s-->" % tid
        # A PANEL ABOVE THE FLOOR CAN STILL BE MISSING SOMETHING NAMEABLE. The state
        # banner used to be reachable ONLY through the thin branch, so a report tab
        # with an unrated certainty column kept its explanation or lost it depending
        # on whether its summary table happened to exceed 600 characters. The
        # condition is read from the cells instead, and the sentence is the same one
        # the thin branch would have emitted.
        state_note = ""
        if tid == "report" and report_certainty_unrated(body):
            state_note = ('  <div class="absent-state" role="note">'
                          '<strong>Partially held.</strong> %s</div>%s'
                          % (PARTIAL_STATE["report"], NL))
        # A BARE `#<tab>` ANCHOR, BECAUSE ONE WAS HANDED TO A READER AND DID NOT RESOLVE.
        #
        # Mahmood opened SGLT2_HF_REVIEW.html#paper on 2026-08-20. THERE WAS NO ELEMENT
        # WITH id="paper" ANYWHERE ON THE PAGE -- the panel is `pn-paper`, its radio is
        # `rt-paper`, and its sections are `paper-*`. The link landed him at the top of
        # the page, and the first thing he saw of the manuscript was nothing.
        #
        # `#paper` is the anchor a person constructs from the tab's own name, so it is the
        # one that has to work. Emitted as an empty span rather than by renaming the panel,
        # because `pn-` prefixes are wired into the tab CSS and the scroll script and
        # renaming them would trade a dead link for a dead tab.
        panels += ('  <section class="panel" id="pn-%s"><span id="%s"></span>%s%s%s%s%s'
                   % (tid, tid, NL, state_note, toc, "".join(pending) + body, carry_into))
        pending = []
        css += (" #rt-%s:checked ~ .panels > #pn-%s{height:auto;overflow:visible}%s"
                ' #rt-%s:checked ~ .tabnav label[for="rt-%s"]{color:#111;'
                "background:#fff;border-color:#d4d4d8;box-shadow:0 2px 0 0 #fff}%s"
                # THE FOCUS RING FOR THE TAB STRIP. The stylesheet already carried
                # `.tabs input:focus-visible + label`, which matches nothing: every
                # radio is emitted first and the labels live inside a later <nav>,
                # so a label is never the input's ADJACENT sibling. The rule was
                # present, so a reviewer counting focus rules found one, and it had
                # never once rendered -- the tab strip is reached by keyboard and
                # showed no focus at all. `~` with the same label[for] shape used
                # for :checked two lines up is what actually matches this markup.
                ' #rt-%s:focus-visible ~ .tabnav label[for="rt-%s"]{'
                "outline:3px solid var(--accent);outline-offset:2px}%s"
                % (tid, tid, NL, tid, tid, NL, tid, tid, NL))
    missing = ([t for t in REQUIRED_TABS if t in {x[0] for x in skipped}]
               if canon.get("requires_full_surface") else [])
    if missing:
        raise ValueError("REQUIRED TAB(S) BELOW THE CONTENT FLOOR: "
                         + "; ".join("%s (%d chars, %d data)" % s
                                     for s in skipped if s[0] in missing))
    if first is None:
        raise ValueError("tabbed build produced no populated tab")
    body = ('<div class="tabs">%s%s<nav class="tabnav" aria-label="Review '
            'sections">%s%s</nav>%s<div class="panels">%s%s</div>%s</div>%s%s%s'
            % (NL, inputs, NL, nav, NL, NL, panels, NL, NL, _TAB_HASH_JS, NL))
    css += (" @media print{.panel{height:auto;overflow:visible}"
            ".tabnav{display:none}}" + NL)
    return body, TAB_CSS + css


FOREST_WINDOWS = (
    ("fit", "Fit to data", None),
    ("w1", "0.5 to 2", (0.5, 2.0)),
    ("w2", "0.25 to 4", (0.25, 4.0)),
    ("w3", "0.7 to 1.3", (0.7, 1.3)),
)


def forest_ranged(res, outcome, e, browser=None, workdir=None, outdir=None):
    """The forest at several pre-rendered x-axis windows, switched by CSS only.

    Every window is present in the document, so the page stays fully readable
    without scripting and every variant is machine-readable at once. The
    invariant the reader-state detector checks is that the multiset of printed
    numerals is identical across variants: the ticks are labelled from the DATA
    (the null and the extremes of the plotted intervals), so widening the window
    moves the guides inward without renaming them.
    """
    base = forest_svg(res, outcome)
    if not base:
        return ""
    # A window NARROWER than the data pushes points and their tick labels outside
    # the viewport, where they are clipped. The numerals stay in the markup -- so
    # the invariance detector passes -- while the reader sees fewer of them. That
    # is a false claim of invariance, not a rendering nicety, so a window that
    # does not contain the data is DROPPED and said to be dropped, rather than
    # offered and quietly broken. Found by adversarial review.
    _rows = [r for r in (res.get("per_trial") or [])
             if r.get("ci_low") is not None and r.get("ci_high") is not None
             and not (r.get("nulled") or str(r.get("trial_id") or r.get("nct")
                                             or "").startswith("NULLED:"))]
    _pool = res.get("pooled") or {}
    # Includes the null for the same reason forest_svg's range does, and it must
    # be the SAME range or the two disagree: a window could satisfy this check by
    # containing all the data, while the null tick that forest_svg draws from a
    # null-inclusive range fell outside it and was clipped -- which is precisely
    # the silent-clipping this check exists to prevent.
    _null = outcome.get("null_value", 1)
    _lo = min([r["ci_low"] for r in _rows] + [_null]
              + ([_pool["ci_low"]] if _pool.get("ci_low") is not None else []))
    _hi = max([r["ci_high"] for r in _rows] + [_null]
              + ([_pool["ci_high"]] if _pool.get("ci_high") is not None else []))
    _dropped = []
    import figures as fg
    br = browser if browser is not None else fg.find_browser()
    variants, radios, panels = [], "", ""
    for key, label, win in FOREST_WINDOWS:
        if win and (win[0] > _lo or win[1] < _hi):
            _dropped.append(label)
            continue
        svg = forest_svg(res, outcome, window=win) if win else None
        if svg is None:
            m = re.search(r"<svg.*?</svg>", base, re.S)
            svg = m.group(0) if m else ""
        variants.append((key, label, svg))
    for i, (key, label, _svg) in enumerate(variants):
        radios += ('  <input type="radio" name="fw" id="fw-%s" class="fwr"%s>%s'
                   % (key, " checked" if i == 0 else "", NL))
    for key, label, _svg in variants:
        radios += ('  <label for="fw-%s" class="fwl">%s</label>%s'
                   % (key, e(label), NL))
    for key, label, svg in variants:
        dl = ""
        if workdir and outdir:
            items, sha, ok, wr = fg.figure_downloads(svg, "forest_%s" % key, br,
                                                 workdir, outdir)
            dl = fg.downloads_html(items, sha, ok, e, NL, wr)
        panels += ('  <div class="fwp" id="fwp-%s">%s%s%s%s  </div>%s'
                   % (key, NL, svg, NL, dl, NL))
    return ("<div class='card fwcard'>%s  <h3>Forest plot</h3>%s"
            "  <p><small>Drawn from the same stored estimates the table above "
            "lists. Box area is proportional to inverse-variance weight.</small>"
            "</p>%s  <p><small>x-axis range</small></p>%s%s%s  <p><small>Changing "
            "the range moves the axis window only. The guides stay labelled with "
            "the null and the extremes of the plotted intervals, so no plotted "
            "value and no printed number differs between these views &mdash; and "
            "that is checked at build time, not asserted.%s</small></p>%s</div>%s"
            % (NL, NL, NL, NL, radios, panels,
               (" Ranges not offered because they would crop the data: %s."
                % ", ".join(_dropped)) if _dropped else "", NL, NL))
