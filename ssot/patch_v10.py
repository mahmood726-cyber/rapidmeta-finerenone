"""Apply the three remaining surface changes to the projectors.

1. Multi-format publication-resolution downloads on every figure.
2. Theme-inheriting figure colours, so one SVG is legible light and dark.
3. A pre-rendered, CSS-only forest x-axis range control.

On (3): the ticks are LABELLED FROM THE DATA in every variant -- the null and the
extremes of the plotted intervals -- so switching range moves the mapping and
nothing else. No printed numeral differs between variants, which is what makes
the reader-state-invariance test pass rather than needing an exemption. The
naive implementation, which relabels ticks at round numbers for each window,
would have changed printed numerals and been a real defect.
"""
import io
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

PJ = "ssot/projectors.py"
s = open(PJ, encoding="utf-8").read()
n = 0


def sub(old, new, why):
    global s, n
    if old not in s:
        raise SystemExit("ANCHOR MISSING (%s): %r" % (why, old[:70]))
    s = s.replace(old, new)
    n += 1


# ---------------------------------------------------------------- 2. colours
# currentColor, not a hardcoded hex. On the page it inherits the theme's text
# colour, so the same bytes are legible in light and dark. In a downloaded
# standalone file currentColor resolves to the viewer's default, which is black,
# so the saved figure is black on white -- correct for print without a second
# render. The two accent fills stay explicit because both are legible on either
# ground and they carry meaning (trial marker, pooled diamond).
sub('stroke="#3f3f46" \'\n                 \'stroke-width="1.5"/>%s\'',
    'stroke="currentColor" \'\n                 \'stroke-width="1.5"/>%s\'',
    "forest CI line")
sub("'  <text x=\"8\" y=\"%d\" font-size=\"12\" fill=\"#111\">%s</text>%s'",
    "'  <text x=\"8\" y=\"%d\" font-size=\"12\" fill=\"currentColor\">%s</text>%s'",
    "forest trial label")
sub("'  <text x=\"8\" y=\"%d\" font-size=\"12\" font-weight=\"700\" '\n"
    "                 'fill=\"#111\">Pooled (%s)</text>%s'",
    "'  <text x=\"8\" y=\"%d\" font-size=\"12\" font-weight=\"700\" '\n"
    "                 'fill=\"currentColor\">Pooled (%s)</text>%s'",
    "forest pooled label")
sub("stroke=\"#a1a1aa\" '", "stroke=\"currentColor\" stroke-opacity=\".45\" '",
    "forest tick guide")
sub("'fill=\"#52525b\">%s</text>%s'", "'fill=\"currentColor\">%s</text>%s'",
    "forest tick label")

# ---------------------------------------------------------------- 3. range
sub("def forest_svg(res, outcome):", "def forest_svg(res, outcome, window=None):",
    "forest signature")
sub("""    a, b = tx(lo), tx(hi)
    pad = (b - a) * 0.08 or 1.0
    a, b = a - pad, b + pad""",
    """    if window:
        # Only the MAPPING changes. lo and hi keep their data-derived values so
        # the tick labels below are identical in every variant.
        a, b = tx(window[0]), tx(window[1])
    else:
        a, b = tx(lo), tx(hi)
        pad = (b - a) * 0.08 or 1.0
        a, b = a - pad, b + pad""",
    "forest window")
sub("""    return fig(svg, "Forest plot", "forest.svg",""",
    """    if window is not None:
        return svg
    return fig(svg, "Forest plot", "forest.svg",""",
    "forest raw-return for variants")

open(PJ, "w", encoding="utf-8").write(s)
print("projectors.py: %d edits" % n)

# ---------------------------------------------------------------- ranged card
RANGED = '''

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
    import figures as fg
    br = browser if browser is not None else fg.find_browser()
    variants, radios, panels = [], "", ""
    for key, label, win in FOREST_WINDOWS:
        svg = forest_svg(res, outcome, window=win) if win else None
        if svg is None:
            m = re.search(r"<svg.*?</svg>", base, re.S)
            svg = m.group(0) if m else ""
        variants.append((key, label, svg))
    for i, (key, label, _svg) in enumerate(variants):
        radios += ('  <input type="radio" name="fw" id="fw-%s" class="fwr"%s>%s'
                   '  <label for="fw-%s" class="fwl">%s</label>%s'
                   % (key, " checked" if i == 0 else "", NL, key, e(label), NL))
    for key, label, svg in variants:
        dl = ""
        if workdir and outdir:
            items, sha, ok = fg.figure_downloads(svg, "forest_%s" % key, br,
                                                 workdir, outdir)
            dl = fg.downloads_html(items, sha, ok, e, NL)
        panels += ('  <div class="fwp" id="fwp-%s">%s%s%s%s  </div>%s'
                   % (key, NL, svg, NL, dl, NL))
    return ("<div class='card'>%s  <h3>Forest plot</h3>%s"
            "  <p><small>Drawn from the same stored estimates the table above "
            "lists. Box area is proportional to inverse-variance weight.</small>"
            "</p>%s  <fieldset class='fwset'>%s"
            "    <legend><small>x-axis range</small></legend>%s%s  </fieldset>%s"
            "%s  <p><small>Changing the range moves the axis window only. The "
            "guides stay labelled with the null and the extremes of the plotted "
            "intervals, so no plotted value and no printed number differs between "
            "these views &mdash; and that is checked at build time, not "
            "asserted.</small></p>%s</div>%s"
            % (NL, NL, NL, NL, NL, radios, NL, panels, NL, NL))
'''
open(PJ, "a", encoding="utf-8").write(RANGED)
print("projectors.py: forest_ranged appended")
