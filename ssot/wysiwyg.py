"""Render the manuscript on the page as the document it is, not as cards about it.

WHY THIS EXISTS. Paper Studio projected the manuscript as a set of cards -- an
abstract card, a methods card, a references card. That describes a paper. The
.docx CONTAINED one: eleven laid-out tables, ten embedded figures, numbered
captions, a reference list. Two renderings of the same work that a reader could
not check against each other, and which had already drifted once (the .docx was
still printing "this section is not written here" after the page had a full
manuscript).

The fix is not to re-implement the document twice. `make_docx.py` now records
every block it emits -- heading, paragraph, table, figure, in order -- and writes
that record to `manuscript_docmodel.json`. This module renders THAT record. So
the page does not resemble the Word file; it is the same block sequence in a
different renderer, and a table that appears in one appears in the other because
there is only one list.

Figures are embedded as base64 PNGs -- the SAME png files the .docx embeds, not a
re-render of the SVG -- so the download-equals-render check spans both surfaces.
"""
import base64
import html
import json
import os

NL = "\n"
e = html.escape


def _img(path):
    try:
        with open(path, "rb") as f:
            return "data:image/png;base64," + base64.b64encode(f.read()).decode()
    except Exception:                                   # noqa: BLE001
        return None


def _table(b):
    head = "".join("<th>%s</th>" % e(str(h)) for h in b.get("headers", []))
    body = ""
    for r in b.get("rows", []):
        body += ("      <tr>%s</tr>%s"
                 % ("".join("<td>%s</td>" % e(str(v)) for v in r), NL))
    return ("  <figure class='doc-t'>%s"
            "    <figcaption><strong>Table %s.</strong> %s</figcaption>%s"
            "    <table>%s      <tr>%s</tr>%s%s    </table>%s  </figure>%s"
            % (NL, b.get("n", ""), e(str(b.get("caption", ""))), NL,
               NL, head, NL, body, NL, NL))


def _figure(b):
    uri = _img(b.get("png", ""))
    if not uri:
        return ("  <figure class='doc-f'><figcaption><strong>Figure %s.</strong> "
                "%s &mdash; image not available at build time, stated rather than "
                "shown as a blank</figcaption></figure>%s"
                % (b.get("n", ""), e(str(b.get("caption", ""))), NL))
    return ("  <figure class='doc-f'>%s    <img alt=\"%s\" src=\"%s\">%s"
            "    <figcaption><strong>Figure %s.</strong> %s</figcaption>%s"
            "  </figure>%s"
            % (NL, e(str(b.get("caption", ""))), uri, NL,
               b.get("n", ""), e(str(b.get("caption", ""))), NL, NL))


def render(path, dl_html=""):
    """The manuscript as a document. Returns "" if the model is not on disk."""
    if not os.path.exists(path):
        return ""
    m = json.load(open(path, encoding="utf-8"))
    out = []
    li_open = False
    for b in m.get("blocks", []):
        k = b.get("kind")
        if k != "li" and li_open:
            out.append("  </ul>" + NL)
            li_open = False
        if k == "table":
            out.append(_table(b))
        elif k == "figure":
            out.append(_figure(b))
        elif k == "li":
            if not li_open:
                out.append("  <ul>" + NL)
                li_open = True
            out.append("    <li>%s</li>%s" % (e(b.get("text", "")), NL))
        elif k in ("h1", "h2", "h3", "h4"):
            lvl = {"h1": "h2", "h2": "h3", "h3": "h4", "h4": "h5"}[k]
            out.append("  <%s>%s</%s>%s" % (lvl, e(b.get("text", "")), lvl, NL))
        elif k == "p":
            out.append("  <p>%s</p>%s" % (e(b.get("text", "")), NL))
    if li_open:
        out.append("  </ul>" + NL)
    stat = ("<p><small>Rendered from the same block sequence the Word file is "
            "built from: <span class='num'>%s</span> tables and "
            "<span class='num'>%s</span> figures, in the same order, with the "
            "same numbering. The figures are the identical PNG files the .docx "
            "embeds, not a second render. Built %s.</small></p>%s"
            % (m.get("tables", "?"), m.get("figures", "?"),
               e(str(m.get("built_utc", ""))), NL))
    return ("<div class='card doc-wrap'>%s"
            "  <h2>Manuscript &mdash; document view</h2>%s%s%s"
            "  <div class='doc'>%s%s  </div>%s</div>%s"
            % (NL, NL, stat, dl_html, NL, "".join(out), NL, NL))


DOC_CSS = """
 .doc-wrap{padding:1rem}
 .doc{background:var(--paper);color:var(--paperfg);border:1px solid var(--line);
      border-radius:.35rem;padding:2.2rem 2.6rem;max-width:52rem;margin:0 auto;
      font-family:Georgia,'Times New Roman',serif;line-height:1.55}
 .doc h2{font-size:1.35rem;margin:1.6rem 0 .5rem;border-bottom:1px solid var(--line);
      padding-bottom:.25rem}
 .doc h3{font-size:1.08rem;margin:1.2rem 0 .35rem}
 .doc h4{font-size:.98rem;margin:1rem 0 .3rem;font-style:italic}
 .doc p{margin:.55rem 0;text-align:justify}
 .doc ul{margin:.4rem 0 .4rem 1.1rem}
 .doc figure{margin:1.2rem 0}
 .doc figcaption{font-size:.86rem;margin:.4rem 0;font-family:system-ui,sans-serif}
 .doc .doc-f img{width:100%;height:auto;display:block;border:1px solid var(--line)}
 .doc table{border-collapse:collapse;width:100%;font-size:.82rem;
      font-family:system-ui,sans-serif}
 .doc th,.doc td{border:1px solid var(--line);padding:.32rem .45rem;
      text-align:left;vertical-align:top}
 .doc th{background:var(--thbg);font-weight:600}
 .doc-t{overflow-x:auto}
"""
