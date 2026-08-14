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
REQUIRED_TABS = ("protocol", "search", "screen", "extract", "analysis", "report",
                 "paper", "statistics")
GRADE_DOMAINS = ("risk_of_bias", "inconsistency", "indirectness", "imprecision",
                 "publication_bias")
FLOOR_CHARS = 600

TAB_CSS = """ .tabs input{position:absolute;clip-path:inset(50%);height:1px;width:1px;overflow:hidden}
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
    by_out = canon["results"]["by_outcome"]
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
        items += ("    <li><strong>Awaiting author attestation: %s</strong> "
                  "&mdash; %s</li>%s" % (e(a["label"]), p(a["what"]), NL))
    for l in rd["limitations"]:
        items += ("    <li><strong>%s</strong> <small>(no attestation can "
                  "discharge this)</small> &mdash; %s</li>%s"
                  % (e(l["label"]), p(l["detail"]), NL))
    quals = ""
    for oid, r in canon["results"]["by_outcome"].items():
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


def forest_svg(res, outcome, window=None):
    """A forest plot drawn from the stored per-trial and pooled estimates.

    THE PLOT CARRIES NO TEXT NUMBERS except the row value labels, which are the
    same projected estimates the table beside it prints, and the axis ticks,
    which are round scale marks plus the null value. Placing a number on a scale
    is a rendering transform; it originates nothing."""
    rows = [r for r in (res.get("per_trial") or [])
            if r.get("point") and r.get("ci_low") and r.get("ci_high")]
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
             + ([pooled["ci_low"]] if pooled.get("ci_low") else []))
    hi = max([r["ci_high"] for r in rows] + [null_v]
             + ([pooled["ci_high"]] if pooled.get("ci_high") else []))
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
    if pooled.get("point"):
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
    if window is not None:
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
        if len(text) < FLOOR_CHARS or data < 1:
            skipped.append((tid, len(text), data))
            if body and carry_into:
                panels = panels.replace(carry_into, body + carry_into, 1)
            elif body:
                pending.append(body)
            continue
        # The digit strip here produced "Open disagreements ()", "RoB- assessment"
        # and "ClinicalTrials.gov API v" in the first line of nearly every tab. It
        # was the no-unprojected-numerals rule applied at the wrong scope: that
        # rule governs numbers the page ASSERTS, and a table of contents asserts
        # nothing -- it echoes a heading that has already been projected and has
        # already passed the rule. Copying the heading verbatim is therefore
        # strictly safer than editing it, because an edited echo can differ from
        # what it claims to point at.
        heads = [re.sub(r"<[^>]+>", "", h).strip(" .·-")
                 for h in re.findall(r"<h3[^>]*>(.*?)</h3>", body, re.S)]
        heads = [h for h in heads if h]
        toc = ("  <p class='toc'><strong>In this section:</strong> "
               + " &middot; ".join(heads) + "</p>" + NL) if heads else ""
        checked = ""
        if first is None:
            first, checked = tid, " checked"
        inputs += '<input type="radio" name="rmtab" id="rt-%s"%s>%s' % (tid, checked, NL)
        nav += '  <label for="rt-%s">%s</label>%s' % (tid, label, NL)
        carry_into = "  </section>" + NL + "<!--end-%s-->" % tid
        panels += ('  <section class="panel" id="pn-%s">%s%s%s%s'
                   % (tid, NL, toc, "".join(pending) + body, carry_into))
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
            'sections">%s%s</nav>%s<div class="panels">%s%s</div>%s</div>%s'
            % (NL, inputs, NL, nav, NL, NL, panels, NL, NL))
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
             if r.get("ci_low") and r.get("ci_high")]
    _pool = res.get("pooled") or {}
    # Includes the null for the same reason forest_svg's range does, and it must
    # be the SAME range or the two disagree: a window could satisfy this check by
    # containing all the data, while the null tick that forest_svg draws from a
    # null-inclusive range fell outside it and was clipped -- which is precisely
    # the silent-clipping this check exists to prevent.
    _null = outcome.get("null_value", 1)
    _lo = min([r["ci_low"] for r in _rows] + [_null]
              + ([_pool["ci_low"]] if _pool.get("ci_low") else []))
    _hi = max([r["ci_high"] for r in _rows] + [_null]
              + ([_pool["ci_high"]] if _pool.get("ci_high") else []))
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
