import io, sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

P = r"F:\rapidmeta-ssot-shell\ssot\projectors.py"
s = open(P, encoding="utf-8").read()

ANCHOR = "def rows_svg(rows, null_v, label_w=200, measure=\"\", axis_note=\"\"):"
assert s.count(ANCHOR) == 1

NEW = r'''ROB_GLYPH = {"LOW": ("+", "#15803d", "#dcfce7"),
             "SOME CONCERNS": ("?", "#a16207", "#fef9c3"),
             "HIGH": ("\u2212", "#b91c1c", "#fee2e2"),
             "NOT ASSESSED": ("\u00b7", "#64748b", "#f1f5f9")}


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
        fill = "none" if known else "var(--soft)"
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


def not_computable_svg(title, reason):
    """An explicit empty state. Never a drawn plot standing in for a real one.

    A figure that cannot be computed from the object is not drawn at all: a
    reader takes a rendered panel as a diagnostic that was RUN, and a plausible
    picture in place of an absent analysis is the exact failure this project
    exists to catch.
    """
    W, H = 700, 150
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" '
            'width="100%%" role="img" aria-label="%s: not computable">%s'
            '<rect x="1" y="1" width="%d" height="%d" fill="none" '
            'stroke="currentColor" stroke-opacity=".4" stroke-dasharray="6 5" '
            'rx="6"/>%s'
            '<text x="%d" y="46" font-size="15" text-anchor="middle" '
            'fill="currentColor" font-weight="600">%s &mdash; not computable</text>%s'
            '<text x="%d" y="76" font-size="13" text-anchor="middle" '
            'fill="currentColor" opacity=".85">%s</text>%s'
            '<text x="%d" y="104" font-size="13" text-anchor="middle" '
            'fill="currentColor" opacity=".85">%s</text>%s</svg>'
            % (W, H, e(title), NL, W - 2, H - 2, NL,
               W // 2, e(title), NL,
               W // 2, e(reason[:88]), NL,
               W // 2, e(reason[88:176]), NL))


'''
s = s.replace(ANCHOR, NEW + ANCHOR)
open(P, "w", encoding="utf-8").write(s)
print("projectors.py: rob_traffic_light_svg, prisma_flow_svg, not_computable_svg")
