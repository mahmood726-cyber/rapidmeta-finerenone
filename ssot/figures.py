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


def rasterise(svg, browser, workdir, stem):
    """SVG string -> PNG path at SCALE. Returns None if the browser is absent."""
    if not browser:
        return None
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
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=90)
    except Exception:                                    # noqa: BLE001
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
    except Exception:                                    # noqa: BLE001
        return None
    return pp


def convert(png_path, stem, outdir):
    """PNG -> TIFF (LZW) and JPG (q95), both with a real dpi header."""
    out = {}
    try:
        from PIL import Image
    except ImportError:
        return out
    try:
        im = Image.open(png_path)
        im.load()
        tp = os.path.join(outdir, stem + ".tiff")
        im.convert("RGB").save(tp, format="TIFF", compression="tiff_lzw",
                               dpi=(DPI, DPI))
        out["tiff"] = tp
        jp = os.path.join(outdir, stem + ".jpg")
        im.convert("RGB").save(jp, format="JPEG", quality=95, optimize=True,
                               dpi=(DPI, DPI))
        out["jpg"] = jp
    except Exception:                                    # noqa: BLE001
        pass
    return out


def _uri(path, mime):
    with open(path, "rb") as f:
        return "data:%s;base64,%s" % (mime, base64.b64encode(f.read()).decode())


def figure_downloads(svg, stem, browser, workdir, outdir):
    """Every offered format for one figure, as (label, filename, href, bytes).

    The SVG entry is built from the same string that is inlined, so it is the
    figure by identity. Each raster records the SHA-256 of the SVG it was
    generated from, which is what makes the cross-format equality claim checkable
    rather than assumed.
    """
    sha = hashlib.sha256(svg.encode("utf-8")).hexdigest()
    items = [("SVG (vector)", stem + ".svg",
              "data:image/svg+xml;charset=utf-8," + quote(svg, safe=""),
              len(svg.encode("utf-8")))]
    png = rasterise(svg, browser, workdir, stem)
    if png:
        w = h = None
        try:
            from PIL import Image
            with Image.open(png) as im:
                w, h = im.size
        except Exception:                                # noqa: BLE001
            pass
        items.append(("PNG %s" % (("%dx%d" % (w, h)) if w else ""),
                      stem + ".png", _uri(png, "image/png"),
                      os.path.getsize(png)))
        # TIFF and JPEG are no longer offered. JPEG is a lossy photographic
        # codec and these are line art: it puts ringing on every rule and every
        # glyph edge, so it was strictly worse than the PNG beside it. The TIFF
        # was a lossless duplicate of that PNG at four times the bytes. Dropping
        # both takes the page from 5.25 MB to about 1.4 MB and IMPROVES the
        # artwork. SVG remains the master and PNG the raster of record; any
        # journal wanting TIFF can convert either without loss.
    return items, sha, (png is not None)


def downloads_html(items, sha, rasterised, e, NL):
    """The download row plus the statement of what a reader is getting."""
    links = "".join(
        "    <a class='dl' download='%s' href=\"%s\">&#11015; %s</a> "
        "<small>%s KB</small>%s"
        % (e(fn), href, e(label), "{:,}".format(max(1, nb // 1024)), NL)
        for label, fn, href, nb in items)
    note = (("All raster formats were generated at build time from the same SVG "
             "as the graphic above (SHA-256 %s&hellip;), at %d dpi for a %.0f-inch "
             "print width, on a white ground. They are not screenshots of the page "
             "and do not change with the theme you are reading in."
             % (e(sha[:16]), DPI, PRINT_WIDTH_IN))
            if rasterised else
            ("Only the vector format is offered for this figure: no headless "
             "browser was available at build time, so the rasters were not "
             "generated. This is stated rather than silently omitted &mdash; the "
             "SVG is complete and will convert at any resolution."))
    return "  <p>%s%s  </p>%s  <p><small>%s</small></p>%s" % (NL, links, NL, note, NL)
