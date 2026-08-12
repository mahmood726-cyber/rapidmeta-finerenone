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
 .tabnav{display:flex;flex-wrap:wrap;gap:.25rem;border-bottom:2px solid #d4d4d8;margin:1.25rem 0 0}
 .tabnav label{padding:.5rem .9rem;cursor:pointer;font-size:.9rem;font-weight:600;color:#52525b;border:1px solid transparent;border-bottom:none;border-radius:.375rem .375rem 0 0}
 .tabnav label:hover{color:#111;background:#f4f4f5}
 .panel{height:0;overflow:hidden}
 .toc{margin:.6rem 0 1rem;padding:.5rem .75rem;background:#f4f4f5;border-radius:.375rem;font-size:.85rem;color:#3f3f46}
 .card.rec{border-left:4px solid #d4d4d8}
 .mine{margin-top:.5rem;padding-top:.5rem;border-top:1px dashed #d4d4d8;font-size:.85rem;color:#52525b}
 .mine button,.chip{margin-right:.35rem;padding:.25rem .6rem;border:1px solid #d4d4d8;border-radius:.25rem;background:#fafafa;cursor:pointer;font:inherit;font-size:.85rem}
 #draft{width:100%;font:inherit;font-size:.9rem;padding:.6rem;border:1px solid #d4d4d8;border-radius:.375rem}
 svg{max-width:100%;height:auto}
 a.dl{display:inline-block;padding:.3rem .7rem;border:1px solid #d4d4d8;border-radius:.25rem;background:#fafafa;text-decoration:none;font-size:.85rem}
 pre{background:#fafafa;border:1px solid #e4e4e7;border-radius:.375rem;padding:.6rem;overflow-x:auto;font-size:.8rem;white-space:pre-wrap}
 tr.inc{background:#f0fdf4} tr.und{background:#fefce8}
"""


def fmt(x):
    if x is None:
        return ""
    if isinstance(x, float):
        return ("%.6f" % x).rstrip("0").rstrip(".")
    return str(x)


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


def fig(svg, title, fname, note):
    """One figure card: inline SVG, a no-JS download of the same bytes, a note."""
    return ("<div class='card'>%s  <h3>%s</h3>%s  %s%s%s  <p><small>%s</small>"
            "</p>%s</div>%s" % (NL, title, NL, svg, NL,
                                svg_download(svg, fname, "Download (SVG)"),
                                note, NL, NL))


def forest_svg(res, outcome):
    """A forest plot drawn from the stored per-trial and pooled estimates.

    THE PLOT CARRIES NO TEXT NUMBERS except the axis ticks, and the ticks are the
    null value and the extremes of the data already rendered in the table beside
    it. Placing a number on a scale is a rendering transform; it originates
    nothing."""
    rows = [r for r in (res.get("per_trial") or [])
            if r.get("point") and r.get("ci_low") and r.get("ci_high")]
    if not rows:
        return ""
    pooled = res.get("pooled") or {}
    log = outcome.get("effect_scale") == "log"
    null_v = outcome.get("null_value", 1)
    tx = (lambda v: math.log(v)) if log else (lambda v: v)
    lo = min([r["ci_low"] for r in rows]
             + ([pooled["ci_low"]] if pooled.get("ci_low") else []))
    hi = max([r["ci_high"] for r in rows]
             + ([pooled["ci_high"]] if pooled.get("ci_high") else []))
    if log and lo <= 0:
        return ""
    a, b = tx(lo), tx(hi)
    pad = (b - a) * 0.08 or 1.0
    a, b = a - pad, b + pad
    W, L, R = 720, 250, 40
    X = lambda v: L + (tx(v) - a) / (b - a) * (W - L - R)
    ws = [1.0 / (r["log_se"] ** 2) if r.get("log_se") else 1.0 for r in rows]
    wmax = max(ws) or 1.0
    body, y, H, top = "", 26, 34, 26
    for r, w in zip(rows, ws):
        side = 5 + 9 * (w / wmax) ** 0.5
        body += ('  <line x1="%.1f" y1="%d" x2="%.1f" y2="%d" stroke="#3f3f46" '
                 'stroke-width="1.5"/>%s'
                 '  <rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" '
                 'fill="#1d4ed8"/>%s'
                 '  <text x="8" y="%d" font-size="12" fill="#111">%s</text>%s'
                 % (X(r["ci_low"]), y, X(r["ci_high"]), y, NL,
                    X(r["point"]) - side / 2, y - side / 2, side, side, NL,
                    y + 4, e(str(r.get("trial_id", ""))), NL))
        y += H
    if pooled.get("point"):
        cy, d = y + 4, 8
        body += ('  <polygon points="%.1f,%d %.1f,%d %.1f,%d %.1f,%d" '
                 'fill="#b45309"/>%s'
                 '  <text x="8" y="%d" font-size="12" font-weight="700" '
                 'fill="#111">Pooled (%s)</text>%s'
                 % (X(pooled["ci_low"]), cy, X(pooled["point"]), cy - d,
                    X(pooled["ci_high"]), cy, X(pooled["point"]), cy + d, NL,
                    cy + 4, e(str(pooled.get("measure", ""))), NL))
        y += H
    height = y + 34
    ticks = ""
    for v in sorted({null_v, lo, hi}):
        ticks += ('  <line x1="%.1f" y1="%d" x2="%.1f" y2="%d" stroke="#a1a1aa" '
                  'stroke-dasharray="%s"/>%s'
                  '  <text x="%.1f" y="%d" font-size="11" text-anchor="middle" '
                  'fill="#52525b">%s</text>%s'
                  % (X(v), top - 18, X(v), y - 14,
                     "0" if v == null_v else "3 3", NL, X(v), y + 4, fmt(v), NL))
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" '
           'width="100%%" role="img" aria-label="Forest plot of the stored '
           'per-trial and pooled estimates">%s%s%s</svg>'
           % (W, height, NL, ticks + body, NL))
    return fig(svg, "Forest plot", "forest.svg",
               "Drawn from the same stored estimates the table above lists. The "
               "dashed guides mark the extremes of the plotted intervals; the "
               "solid guide is the null. Box area is proportional to "
               "inverse-variance weight.")


def scatter_svg(pts, xlab, ylab, invert_y=False, vline=None):
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
        body += ('<line x1="%.1f" y1="%d" x2="%.1f" y2="%d" stroke="#a1a1aa"/>%s'
                 % (X(vline), T, X(vline), H - B, NL))
    for x, y, lab in pts:
        body += ('<circle cx="%.1f" cy="%.1f" r="5" fill="#1d4ed8" '
                 'fill-opacity=".8"/>%s' % (X(x), Y(y), NL))
        if lab:
            body += ('<text x="%.1f" y="%.1f" font-size="11" fill="#3f3f46">%s'
                     '</text>%s' % (X(x) + 8, Y(y) + 4, e(str(lab)), NL))
    for v in (min(dxs), max(dxs)):
        body += ('<text x="%.1f" y="%d" font-size="10" text-anchor="middle" '
                 'fill="#52525b">%s</text>%s' % (X(v), H - B + 16, fmt(v), NL))
    for v in (min(ys), max(ys)):
        body += ('<text x="%d" y="%.1f" font-size="10" text-anchor="end" '
                 'fill="#52525b">%s</text>%s' % (L - 6, Y(v) + 4, fmt(v), NL))
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" '
            'width="100%%" role="img" aria-label="%s against %s">%s'
            '<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="#71717a"/>'
            '<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="#71717a"/>%s%s'
            '<text x="%d" y="%d" font-size="11" text-anchor="middle" '
            'fill="#3f3f46">%s</text>%s'
            '<text x="13" y="%d" font-size="11" fill="#3f3f46" '
            'transform="rotate(-90 13 %d)" text-anchor="middle">%s</text>%s</svg>'
            % (W, H, NL, e(xlab), e(ylab), L, T, L, H - B, L, H - B, W - R, H - B,
               NL, body, (L + W - R) // 2, H - 6, e(xlab), NL,
               (T + H - B) // 2, (T + H - B) // 2, e(ylab), NL))


def rows_svg(rows, null_v, label_w=200):
    """Point-and-interval rows on a log axis (leave-one-out, cumulative)."""
    if not rows:
        return ""
    W, R, T, H = 700, 30, 22, 32
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
        body += ('<line x1="%.1f" y1="%d" x2="%.1f" y2="%d" stroke="#3f3f46"/>%s'
                 '<rect x="%.1f" y="%d" width="8" height="8" fill="#1d4ed8"/>%s'
                 '<text x="6" y="%d" font-size="11" fill="#111">%s</text>%s'
                 % (X(r["ci_low"]), y, X(r["ci_high"]), y, NL,
                    X(r["point"]) - 4, y - 4, NL, y + 4, e(str(r["label"])), NL))
        y += H
    body += ('<line x1="%.1f" y1="%d" x2="%.1f" y2="%d" stroke="#a1a1aa"/>%s'
             '<text x="%.1f" y="%d" font-size="10" text-anchor="middle" '
             'fill="#52525b">%s</text>%s'
             % (X(null_v), T - 14, X(null_v), y - 16, NL, X(null_v), y + 2,
                fmt(null_v), NL))
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" '
            'width="100%%" role="img" aria-label="point and interval rows">%s%s'
            '</svg>' % (W, y + 14, NL, body))


# --------------------------------------------------------------- small helpers
def kv_card(title, pairs, note=""):
    """A label/value card. Emits nothing when every value is empty."""
    rows = "".join("    <tr><th>%s</th><td>%s</td></tr>%s" % (k, v, NL)
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
        heads = [re.sub(r"[0-9]", "", re.sub(r"<[^>]+>", "", h)).strip(" .·-")
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
                % (tid, tid, NL, tid, tid, NL))
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
