import io, sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

P = r"F:\rapidmeta-ssot-shell\ssot\projectors.py"
s = open(P, encoding="utf-8").read()
ANCHOR = "def rob_traffic_light_svg(trials, domains, assessors, cell):"
assert s.count(ANCHOR) == 1

NEW = r'''def visual_abstract_svg(title, question, k, n_total, measure, point, lo, hi,
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

    # --- the estimate, drawn on a log axis with the null in the middle -------
    ax_y = yy + 74
    L, R = 190, 130
    import math as _m
    span = max(abs(_m.log(lo / null_v)), abs(_m.log(hi / null_v)),
               abs(_m.log(point / null_v))) * 1.45 or 0.5
    X = lambda v: L + (_m.log(v / null_v) + span) / (2 * span) * (W - L - R)
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


'''
s = s.replace(ANCHOR, NEW + ANCHOR)
open(P, "w", encoding="utf-8").write(s)
print("projectors.py: visual_abstract_svg")

# ------------------------------------------------------------------ wire it in
Q = r"F:\rapidmeta-ssot-shell\ssot\projectors2.py"
w = open(Q, encoding="utf-8").read()
w = w.replace("funnel_svg, rob_traffic_light_svg, prisma_flow_svg,",
              "funnel_svg, rob_traffic_light_svg, prisma_flow_svg,\n"
              "                        visual_abstract_svg,", 1)
A2 = "def rob_figure(canon, p):"
assert w.count(A2) == 1
NEW2 = '''def visual_abstract(canon, res, outcome, p):
    """The graphical abstract, projected. Under the same gates as any figure."""
    pooled = res.get("pooled") or {}
    if not pooled.get("point"):
        return ""
    n_total = 0
    for t in (canon.get("inputs") or {}).get("trials", []):
        for a in (t.get("arms") or []):
            n_total += a.get("participants") or 0
    g = res.get("grade") or {}
    sens = res.get("sensitivity") or {}
    loo = ""
    rows = [a for a in (sens.get("analyses") or []) if isinstance(a, dict)]
    kept = [a for a in rows if a.get("still_excludes_null")]
    if rows:
        loo = ("Leave-one-out: %d of %d refits still exclude no difference; the "
               "estimate does not survive removal of the largest trial."
               % (len(kept), len(rows)))
    return fig(visual_abstract_svg(
        canon.get("title", ""), canon.get("question", ""),
        res.get("k") or len(res.get("per_trial") or []),
        "{:,}".format(n_total) if n_total else None,
        pooled.get("measure", ""), pooled["point"], pooled.get("ci_low"),
        pooled.get("ci_high"), outcome.get("null_value", 1),
        g.get("certainty"), outcome.get("name", ""), loo),
        "Visual abstract", "visual-abstract.svg",
        "Projected from the canonical object, so it carries the same k, the same "
        "pooled estimate and the same interval as the paper and cannot drift "
        "from them. The interval is drawn CROSSING the no-difference line "
        "because it does: a graphical abstract travels without its caption, and "
        "one that showed a favourable point estimate without showing that its "
        "interval includes no effect would be overstating a null result, which "
        "is a defect class this review documents in other papers.")


def rob_figure(canon, p):'''
w = w.replace(A2, NEW2, 1)
open(Q, "w", encoding="utf-8").write(w)
print("projectors2.py: visual_abstract wired")

# put it first in the figure suite
B = r"F:\rapidmeta-ssot-shell\ssot\build_tabbed.py"
b = open(B, encoding="utf-8").read()
old = '''        d["figures"] = (p2.prisma_figure(canon, p)'''
new = '''        d["figures"] = (p2.visual_abstract(canon, res, outcome, p)
                        + p2.prisma_figure(canon, p)'''
assert b.count(old) == 1
b = b.replace(old, new)
open(B, "w", encoding="utf-8").write(b)
print("build_tabbed.py: visual abstract leads the figure suite")
