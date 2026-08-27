"""Publication-resolution figure downloads, rasterised at BUILD time.

WHY NOT IN THE BROWSER. Rasterising from live DOM state means the file a reader
saves is produced from whatever the page happens to be showing, which is a second
source of truth for the same figure. Everything here is generated from the same
SVG STRING that is inlined into the page, so the raster and the rendered graphic
have a single common ancestor and the download-equals-render test is a statement
about bytes rather than about intent.

FORMATS. SVG (vector, the master), TIFF (LZW, what journals ask for on line art),
JPG (quality 95, for submission systems that reject TIFF). PNG is kept as the
intermediate and offered too, since it is lossless and universally accepted.

RESOLUTION. The SVG is authored at 720 user units wide and is treated as a
6-inch print width, so a device scale factor of 5 yields 3600 px across, which is
600 dpi. That is the line-art figure requirement at most cardiology journals.
The dpi is written into the TIFF and JPG headers, not merely implied by pixel
count, because a submission system reads the header.

COLOUR. The rasters are generated from a LIGHT-THEME render regardless of the
reader's theme. A dark-mode raster would be white strokes on a transparent or
black ground, which prints as a black rectangle or as nothing; a reader who
switched to dark mode and then downloaded a figure for a manuscript would get an
unusable file and would not find out until a reviewer told them.
"""
import base64
import hashlib
import os
import re
import shutil
import subprocess
import tempfile
from urllib.parse import quote

SCALE = 5           # 720 units @ 6 in -> 3600 px -> 600 dpi
DPI = 600
PRINT_WIDTH_IN = 6.0

_CHROME_CANDIDATES = (
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
)


def find_browser():
    for c in _CHROME_CANDIDATES:
        if os.path.exists(c):
            return c
    for n in ("chrome", "msedge", "chromium"):
        w = shutil.which(n)
        if w:
            return w
    return None


def _svg_px(svg):
    """Intrinsic pixel size from viewBox, so the wrapper does not letterbox."""
    m = re.search(r'viewBox="([-\d.]+)\s+([-\d.]+)\s+([\d.]+)\s+([\d.]+)"', svg)
    if m:
        return float(m.group(3)), float(m.group(4))
    w = re.search(r'width="([\d.]+)"', svg)
    h = re.search(r'height="([\d.]+)"', svg)
    return (float(w.group(1)) if w else 720.0,
            float(h.group(1)) if h else 400.0)


def _cache_path(svg, workdir):
    """Where a raster of THIS EXACT SVG lives, and whether it is already there.

    CONTENT-ADDRESSED, AND THAT MATTERS TWICE.

    SPEED. Every figure launches a cold headless Chrome: 21 seconds on this machine at
    best, up to the 90-second timeout at worst. A page carries several figures, so a full
    rebuild of 162 pages runs to roughly nine hours with the Python process idle
    throughout -- all of it waiting for a browser to redraw pictures that have not
    changed. An edit to the manuscript layer does not alter a forest plot, so in such a
    rebuild nearly every raster is byte-identical to the one already on disk.

    CORRECTNESS. `rasterise` names its output by STEM -- the figure's position on the
    page -- and therefore must delete any existing PNG first, because a Chrome run that
    fails silently leaves the PREVIOUS figure's raster at that path to be returned as this
    one's. The comment below records that this was found by adversarial review, and the
    delete is a sound guard. Naming the file by the SHA-256 of the SVG that produced it
    REMOVES the hazard instead of guarding against it: a raster keyed to its own source
    cannot be another figure's, whatever fails.

    So this is not a shortcut bolted onto a fragile path. It is the safer naming, which
    happens also to be fast.
    """
    # ONE CACHE FOR THE WHOLE REPOSITORY, NOT ONE PER OUTPUT DIRECTORY.
    #
    # Keyed on `workdir` first, which is `<dirname of the page>/figs`, this cached nothing
    # useful the moment a page was built anywhere else: a verification pass building the
    # same 74 pages into `outputs/_shrink_check/` got a cold cache for every figure and ran
    # at 2.5 minutes a page -- three hours to check work that took minutes to do.
    #
    # A content-addressed entry is safe to share across every output directory BY
    # CONSTRUCTION: the filename is the SHA-256 of the SVG that produced it, so two builds
    # collide only when they are drawing byte-identical pictures. Scoping it per directory
    # bought nothing and cost the entire benefit.
    sha = hashlib.sha256(svg.encode("utf-8")).hexdigest()[:32]
    cdir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "..", "figs", "_raster_cache")
    cdir = os.path.normpath(cdir)
    try:
        os.makedirs(cdir, exist_ok=True)
    except OSError:
        return None, None
    p = os.path.join(cdir, sha + ".png")
    return p, (p if os.path.exists(p) and os.path.getsize(p) > 0 else None)


def rasterise(svg, browser, workdir, stem):
    """SVG string -> PNG path at SCALE. Returns None if the browser is absent."""
    if not browser:
        return None

    # A RASTER OF THIS EXACT SVG, IF ONE HAS ALREADY BEEN DRAWN.
    #
    # A hit requires the SVG bytes to match, so this cannot serve a stale or a wrong
    # figure: any change to the plot changes the SVG, changes the hash, and misses.
    # Nothing is cached until it has passed the non-empty and blankness checks below, so
    # a cached file is one that already satisfied them.
    _cpath, _hit = _cache_path(svg, workdir)
    if _hit:
        return _hit

    w, h = _svg_px(svg)
    # White ground, not transparent: a transparent PNG flattened by a journal's
    # converter can come out black, and line art on black is invisible.
    html = ("<!doctype html><meta charset='utf-8'>"
            "<style>html,body{margin:0;padding:0;background:#fff}"
            "svg{display:block}</style>" + svg)
    hp = os.path.join(workdir, stem + ".html")
    pp = os.path.join(workdir, stem + ".png")
    with open(hp, "w", encoding="utf-8") as f:
        f.write(html)
    # DELETE ANY STALE RASTER FIRST. Without this, a Chrome run that fails writes
    # nothing, the previous figure's PNG is still on disk, and the function
    # returns it as a success -- so the page offers the OLD figure's raster while
    # printing the NEW figure's SHA-256 beside it. That is precisely the
    # download-does-not-equal-render defect the detectors exist to catch, arriving
    # through the one path they do not inspect. Found by adversarial review.
    if os.path.exists(pp):
        try:
            os.remove(pp)
        except OSError:
            return None
    cmd = [browser, "--headless=new", "--disable-gpu", "--hide-scrollbars",
           "--force-device-scale-factor=%d" % SCALE,
           "--default-background-color=FFFFFFFF",
           "--window-size=%d,%d" % (int(w), int(h)),
           "--screenshot=" + pp, "file:///" + hp.replace("\\", "/")]
    # NARROWED FROM `except Exception`. The expected failures here are environmental --
    # the browser is not installed, or it hung. A TypeError or AttributeError in this
    # function is OUR bug, and swallowing it published "this topic has no figure", which
    # is a claim the page makes to a reader. A broken renderer must not be able to
    # impersonate a topic that legitimately has nothing to draw.
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=90)
    except (FileNotFoundError, PermissionError, OSError,
            subprocess.TimeoutExpired):
        return None
    if r.returncode != 0:                 # was ignored entirely
        return None
    if not (os.path.exists(pp) and os.path.getsize(pp) > 0):
        return None
    # A non-empty screenshot can still be a blank page. A blank raster offered as
    # a figure is worse than no raster, because it looks like a file.
    try:
        from PIL import Image
        with Image.open(pp) as im:
            ex = im.convert("L").getextrema()
        if ex[0] == ex[1]:
            return None
    except ImportError:
        pass
    except (OSError, ValueError):
        # Pillow could not decode the raster we just wrote. That is a real failure of
        # THIS png, so returning None is honest.
        return None
    # NOTE: no bare `except` here on purpose. This block decides whether a SUCCESSFULLY
    # RENDERED figure is blank. A bug in the blankness test previously discarded a good
    # figure and the page then told the reader the topic had none. Any other exception
    # is ours and must be loud.

    # ONLY NOW IS IT CACHED -- after non-empty and after not-blank. Caching before these
    # checks would make a bad raster permanent and serve it to every later build, which is
    # a worse failure than the slow path it replaces.
    if _cpath:
        try:
            shutil.copyfile(pp, _cpath)
        except OSError:
            pass          # a cache that cannot be written is a slow build, not a wrong one
    return pp


def to_eps(svg, stem, outdir):
    """SVG -> genuine VECTOR EPS. The journal's first preference for line art.

    Vector, not a raster wrapped in an EPS header: the marks stay resolution-
    independent, which is the whole reason the journal asks for EPS on line art.
    Returns None if the toolchain is absent, and the caller says so rather than
    silently offering one format fewer.
    """
    try:
        from svglib.svglib import svg2rlg
        from reportlab.graphics import renderPS
    except ImportError:
        return None
    sp = os.path.join(outdir, stem + "_src.svg")
    ep = os.path.join(outdir, stem + ".eps")
    try:
        with open(sp, "w", encoding="utf-8") as f:
            f.write(svg)
        drawing = svg2rlg(sp)
        if drawing is None:
            return None
        renderPS.drawToFile(drawing, ep)
    except (OSError, ValueError):                        # unwritable path / unconvertible SVG
        return None
    return ep if os.path.exists(ep) and os.path.getsize(ep) > 0 else None


def convert(png_path, stem, outdir):
    """PNG -> UNCOMPRESSED TIFF at 600 dpi.

    Uncompressed is explicit, not an oversight: the journal's fallback wording is
    "uncompressed TIFF", and an LZW file is smaller but is not what was asked
    for. JPEG is gone -- it is not on the accepted list and it is a lossy
    photographic codec applied to line art.
    """
    out = {}
    try:
        from PIL import Image
    except ImportError:
        return out
    try:
        im = Image.open(png_path)
        im.load()
        tp = os.path.join(outdir, stem + ".tiff")
        im.convert("RGB").save(tp, format="TIFF", compression=None,
                               dpi=(DPI, DPI))
        out["tiff"] = tp
    except (OSError, ValueError):                        # unreadable png / unwritable tiff
        pass
    return out


def _uri(path, mime):
    with open(path, "rb") as f:
        return "data:%s;base64,%s" % (mime, base64.b64encode(f.read()).decode())


VECTOR_BY_CHOICE = "VECTOR_BY_CHOICE"

LINE_ART = {"rob-traffic-light"}


def is_line_art(stem):
    """Figures whose graphic is discrete marks, glyphs and text on a grid.

    THIS EXEMPTION IS A JUDGEMENT, AND IT IS MINE RATHER THAN THE CODEBASE'S. It rests on
    one property: the risk-of-bias traffic light is sparse vector marks -- circles, four
    glyphs, row and column labels. A 600 dpi raster of that cost 568 KB to reproduce,
    losslessly and at any zoom, what the inline SVG beside it already shows. Measured on
    SGLT2_HF_REVIEW: that one PNG was 8.22x its served size and was the ENTIRE 1.44x
    growth of the rebuilt page -- every other figure was byte-identical.

    IT MUST NOT BE EXTENDED TO A DATA-DENSE FIGURE WITHOUT SOMEONE MAKING THAT CALL
    AGAIN. A forest plot, a funnel, a GOSH cloud, a bubble plot or the visual abstract
    may be worth 600 dpi to a reader building a slide, and nothing argued here bears on
    them. Adding a stem to LINE_ART is a decision about what a reader loses, not a size
    optimisation.

    The multiplier that makes it matter: the page renders its content in three views, so
    any figure that grows, grows threefold.
    """
    return stem in LINE_ART


def figure_downloads(svg, stem, browser, workdir, outdir):
    """Every offered format for one figure, as (label, filename, href, bytes).

    The SVG entry is built from the same string that is inlined, so it is the
    figure by identity. Each raster records the SHA-256 of the SVG it was
    generated from, which is what makes the cross-format equality claim checkable
    rather than assumed.
    """
    sha = hashlib.sha256(svg.encode("utf-8")).hexdigest()
    written = []
    items = [("SVG (vector)", stem + ".svg",
              "data:image/svg+xml;charset=utf-8," + quote(svg, safe=""),
              len(svg.encode("utf-8")))]
    if is_line_art(stem):
        # VECTOR ONLY, BY DECISION. Returns the third element as VECTOR_BY_CHOICE rather
        # than False so downloads_html can say WHY -- claiming a browser was unavailable
        # when the omission was chosen would be a page lying about its own provenance.
        return items, sha, VECTOR_BY_CHOICE, written
    png = rasterise(svg, browser, workdir, stem)
    if png:
        w = h = None
        try:
            from PIL import Image
            with Image.open(png) as im:
                w, h = im.size
        except (OSError, ValueError):                    # size is cosmetic; a bug is not
            pass
        items.append(("PNG %s" % (("%dx%d" % (w, h)) if w else ""),
                      stem + ".png", _uri(png, "image/png"),
                      os.path.getsize(png)))
        # SUBMISSION FORMATS GO TO DISK, NOT INTO THE PAGE. Embedding them as
        # data URIs took the page to 210 MB: an uncompressed 600 dpi TIFF is
        # tens of megabytes by design, and base64 adds a third again. They are
        # for the journal, not for a reader on a slow connection, and putting
        # them in the page served neither. They are written to the figures
        # directory and the page says where they are and how big they got.
        eps = to_eps(svg, stem, outdir)
        if eps:
            written.append(("EPS (vector, journal's first choice for line art)",
                            eps, os.path.getsize(eps)))
        for _k, _p in convert(png, stem, outdir).items():
            written.append(("TIFF (uncompressed, %d dpi -- journal fallback)" % DPI,
                            _p, os.path.getsize(_p)))
    return items, sha, (png is not None), written


def downloads_html(items, sha, rasterised, e, NL, written=()):
    """The download row plus the statement of what a reader is getting."""
    links = "".join(
        "    <a class='dl' download='%s' href=\"%s\">&#11015; %s</a> "
        "<small>%s KB</small>%s"
        % (e(fn), href, e(label), "{:,}".format(max(1, nb // 1024)), NL)
        for label, fn, href, nb in items)
    # THREE STATES, NOT TWO. A figure offered as vector only because the build could not
    # rasterise, and one offered as vector only because a raster was judged to add weight
    # without fidelity, are different facts about the page. Collapsing them would have a
    # page claim a browser was missing when the omission was a decision -- the same class
    # of self-description defect this project has spent its time removing.
    if rasterised is VECTOR_BY_CHOICE or rasterised == VECTOR_BY_CHOICE:
        note = ("Only the vector format is offered for this figure, by choice: it is "
                "line art &mdash; discrete marks, glyphs and labels &mdash; which SVG "
                "reproduces exactly at any size, so a raster would add weight without "
                "adding fidelity. The build was able to rasterise; it was asked not to.")
    elif rasterised:
        note = ("All raster formats were generated at build time from the same SVG "
                "as the graphic above (SHA-256, first 16 hex characters: %s), at %d dpi "
                "for a %.0f-inch "
                "print width, on a white ground. They are not screenshots of the page "
                "and do not change with the theme you are reading in."
                % (e(sha[:16]), DPI, PRINT_WIDTH_IN))
    else:
        note = ("Only the vector format is offered for this figure: no headless "
                "browser was available at build time, so the rasters were not "
                "generated. This is stated rather than silently omitted &mdash; the "
                "SVG is complete and will convert at any resolution.")
    # The journal formats are on disk, not in the page. Saying so -- with the
    # sizes -- is the difference between a reader thinking they are missing and
    # a reader knowing where they are.
    sub = ""
    if written:
        sub = ("  <p><small>Submission formats written to the figures directory, "
               "not embedded here because an uncompressed 600 dpi TIFF is tens of "
               "megabytes: %s.</small></p>%s"
               % ("; ".join("%s &mdash; <code>%s</code>, %s KB"
                            % (e(lbl), e(os.path.basename(pth)),
                               "{:,}".format(max(1, nb // 1024)))
                            for lbl, pth, nb in written), NL))
    return ("  <p>%s%s  </p>%s  <p><small>%s</small></p>%s%s"
            % (NL, links, NL, note, NL, sub))
