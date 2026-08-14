"""The Word file and the Paper Studio tab must be the SAME document.

Both are projections of one canonical object through one block sequence
(`manuscript_docmodel.json`). That is the architecture, and its whole value is
that the two surfaces CANNOT drift. So the claim has to be checked rather than
assumed: any divergence means one of them was authored instead of projected,
which is precisely the defect the design exists to remove -- and it has happened
before on this project, when the .docx was still printing "this section is not
written here" after the page carried a full manuscript.

THREE-WAY, not two. The docmodel is the contract; the .docx and the rendered
page are the two readings of it. Comparing only the two outputs would let a
shared error pass, and comparing only against the docmodel would miss a renderer
that silently drops a block.

  docmodel  <->  word/document.xml       (what Word will show)
  docmodel  <->  rendered document view  (what the page shows, read at runtime)

Usage:
  python scripts/alignment_gate.py <docmodel.json> <manuscript.docx> <page.html>
  python scripts/alignment_gate.py --selftest
"""
import io
import json
import os
import re
import sys
import zipfile

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def norm(s):
    """Compare meaning, not whitespace. Renderers legitimately re-wrap."""
    return re.sub(r"\s+", " ", str(s or "")).strip()


def model_blocks(path):
    m = json.load(open(path, encoding="utf-8"))
    return m.get("blocks", []), m


def docx_sequence(path):
    """Headings, table captions and figure captions, in document order.

    Two extractor bugs, both of which reported a DIVERGENCE in a document that
    was correctly aligned. They are recorded because a gate that cries wolf gets
    switched off, and because both are the same mistake: reading the artefact
    through a lossy reader and blaming the artefact.

      1. XML entities were not unescaped, so the docmodel's `sei -> 0` never
         matched document.xml's `sei -&gt; 0`.
      2. Captions were counted, not deduplicated. A journal-format .docx repeats
         every figure caption in its "Figure legends" section, so ten figures
         legitimately produce twenty caption lines.
    """
    import html as _h
    x = zipfile.ZipFile(path).read("word/document.xml").decode("utf-8")
    txt = _h.unescape(re.sub(r"<[^>]+>", "", re.sub(r"</w:p>", "\n", x)))
    tables, figs = {}, {}
    for line in txt.split("\n"):
        t = norm(line)
        if not t:
            continue
        mt = re.match(r"Table (\d+)\. (.+)", t)
        mf = re.match(r"Figure (\d+)\. (.+)", t)
        # First occurrence wins: the body caption, not its repeat in the legends.
        if mt and int(mt.group(1)) not in tables:
            tables[int(mt.group(1))] = mt.group(2)
        elif mf and int(mf.group(1)) not in figs:
            figs[int(mf.group(1))] = mf.group(2)
    return {"tables": sorted(tables.items()),
            "figures": sorted(figs.items()), "text": txt}


def page_docview(page_html):
    """The rendered document view, read out of the page at runtime."""
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    o = Options()
    for a in ("--headless=new", "--disable-gpu", "--no-sandbox",
              "--window-size=1400,1200"):
        o.add_argument(a)
    d = webdriver.Chrome(options=o)
    d.set_page_load_timeout(300)
    try:
        d.get("file:///" + os.path.abspath(page_html).replace("\\", "/"))
        import time
        time.sleep(3)
        d.execute_script("document.querySelectorAll('.panel').forEach(p=>{"
                         "p.style.height='auto';p.style.overflow='visible';});")
        time.sleep(1.2)
        return d.execute_script("""
          const doc=document.querySelector('.doc'); if(!doc) return null;
          const caps=[...doc.querySelectorAll('figcaption')].map(c=>c.innerText.trim());
          return {heads:[...doc.querySelectorAll('h2,h3,h4,h5')].map(h=>h.innerText.trim()),
                  head_levels:[...doc.querySelectorAll('h2,h3,h4,h5')]
                        .map(h=>[h.tagName.toLowerCase(), h.innerText.trim()]),
                  tables:caps.filter(c=>/^Table \\d+\\./.test(c)),
                  figures:caps.filter(c=>/^Figure \\d+\\./.test(c)),
                  // pre.cellpre lives INSIDE a table cell and is already
                  // compared as table content. Counting it as a standalone
                  // verbatim block made the page look like it had 13 blocks the
                  // docmodel did not -- a divergence created by the comparison,
                  // not present in the document.
                  pres:[...doc.querySelectorAll('pre:not(.cellpre)')]
                        .map(p=>p.textContent),
                  text:doc.innerText};""")
    finally:
        d.quit()


# A CONTRACT ON PRESENTATION, not only on content.
#
# The content half of this gate reported ALIGNED on 301 blocks while a reader
# comparing the two surfaces said one was plainly better. Both were true: the
# block sequence corresponds exactly, because both are projections of one
# docmodel, and the Word file was still the worse document -- Calibri 11 against
# the HTML's serif, no line spacing, every figure forced to the full text
# measure, and header rows that did not repeat across page breaks on any of
# seventeen tables.
#
# Content equality was never going to catch a typeface. So the docx is also
# checked against a presentation contract taken from the HTML, which is the
# surface judged better and is therefore the reference. These are the properties
# that make a document readable rather than merely correct.
PRESENTATION = {
    "serif body face": lambda d: d["font"] not in ("Calibri", "Aptos", "Arial",
                                                   "Segoe UI", None),
    "line spacing set": lambda d: d["line_spacing"] is not None,
    "header rows repeat on every table": lambda d: d["tables"] > 0
                                                   and d["tbl_header"] >= d["tables"],
    "no figure wider than the text measure": lambda d: d["over_measure"] == 0,
    "plain table grid, not a theme accent": lambda d: not any(
        "Accent" in x for x in d["tbl_styles"]),
}


def docx_presentation(path):
    """Read the properties a reader actually sees, out of the file."""
    import re as _re
    import zipfile as _z
    z = _z.ZipFile(path)
    x = z.read("word/document.xml").decode("utf-8")
    st = z.read("word/styles.xml").decode("utf-8")
    m = _re.search(r'<w:style [^>]*w:styleId="Normal".*?</w:style>', st, _re.S)
    seg = m.group(0) if m else ""
    fm = _re.search(r'w:ascii="([^"]+)"', seg)
    ls = _re.search(r'<w:spacing[^>]*w:line="(\d+)"', seg)
    # text measure = page width less both margins, in EMU (1 inch = 914400)
    pg = _re.search(r'<w:pgSz w:w="(\d+)"', x)
    mg = _re.search(r'<w:pgMar w:top="\d+" w:right="(\d+)"[^>]*w:left="(\d+)"', x)
    measure = None
    if pg and mg:
        measure = (int(pg.group(1)) - int(mg.group(1)) - int(mg.group(2))) / 1440.0
    over = 0
    for cx, _cy in _re.findall(r'<wp:extent cx="(\d+)" cy="(\d+)"', x):
        if measure and int(cx) / 914400.0 > measure - 0.05:
            over += 1
    return {"font": fm.group(1) if fm else None,
            "line_spacing": ls.group(1) if ls else None,
            "tables": x.count("<w:tbl>"),
            "tbl_header": x.count("tblHeader"),
            "tbl_styles": set(_re.findall(r'<w:tblStyle w:val="([^"]+)"', x)),
            "over_measure": over, "measure_in": measure}


def check_presentation(path):
    d = docx_presentation(path)
    bad = []
    for name, pred in PRESENTATION.items():
        try:
            ok = pred(d)
        except Exception:                                # noqa: BLE001
            ok = False
        if not ok:
            bad.append("presentation: %s -- FAILED (font=%s, line_spacing=%s, "
                       "tables=%s, tblHeader=%s, styles=%s, figures wider than "
                       "the %.2f in measure=%s)"
                       % (name, d["font"], d["line_spacing"], d["tables"],
                          d["tbl_header"], sorted(d["tbl_styles"]),
                          d["measure_in"] or 0, d["over_measure"]))
    return bad


def check(model, docx, page):
    bad = []
    m_heads = [norm(b["text"]) for b in model if b.get("kind", "").startswith("h")]
    m_tabs = [(b.get("n"), norm(b.get("caption"))) for b in model
              if b.get("kind") == "table"]
    m_figs = [(b.get("n"), norm(b.get("caption"))) for b in model
              if b.get("kind") == "figure"]
    m_pres = [norm(b.get("text")) for b in model if b.get("kind") == "pre"]

    d_tabs = [(n_, norm(c)) for n_, c in docx["tables"]]
    d_figs = [(n_, norm(c)) for n_, c in docx["figures"]]
    if m_tabs != d_tabs:
        bad.append("docmodel vs .docx: table captions differ (%d vs %d)"
                   % (len(m_tabs), len(d_tabs)))
    if m_figs != d_figs:
        bad.append("docmodel vs .docx: figure captions differ (%d vs %d)"
                   % (len(m_figs), len(d_figs)))
    for h in m_heads:
        if h and h not in norm(docx["text"]):
            bad.append("docmodel heading missing from .docx: %r" % h[:60])
    for p in m_pres:
        if p and p not in norm(docx["text"]):
            bad.append("docmodel verbatim block missing from .docx: %r" % p[:60])

    if page is None:
        bad.append("the page has no document view at all")
        return bad
    p_tabs = [norm(re.sub(r"^Table \d+\.\s*", "", c)) for c in page["tables"]]
    p_figs = [norm(re.sub(r"^Figure \d+\.\s*", "", c)) for c in page["figures"]]
    if [c for _, c in m_tabs] != p_tabs:
        bad.append("docmodel vs page: table captions differ (%d vs %d)"
                   % (len(m_tabs), len(p_tabs)))
    if [c for _, c in m_figs] != p_figs:
        bad.append("docmodel vs page: figure captions differ (%d vs %d)"
                   % (len(m_figs), len(p_figs)))
    p_heads = [norm(h) for h in page["heads"]]
    for h in m_heads:
        if h and h not in p_heads:
            bad.append("docmodel heading missing from the page: %r" % h[:60])
    # LEVELS, not just presence. A heading that survives as text but drops a
    # level has lost the structure it was carrying, and the content check would
    # never see it.
    # COMPARED BY SEQUENCE, NOT BY TEXT. Heading text is not unique in this
    # document by design: "Protocol and registration" is both a narrative Methods
    # subsection and an entry in the Recorded-detail appendix, at different
    # levels. Keyed by text, the first occurrence shadowed the second and the
    # check reported a level drift in a correctly nested document -- a false
    # positive from assuming a uniqueness the structure never promised.
    m_lv = [(norm(b["text"]), int(b["kind"][1])) for b in model
            if b.get("kind", "")[:1] == "h" and b.get("kind", "")[1:].isdigit()]
    p_seq = [(norm(t), int(tag[1])) for tag, t in (page.get("head_levels") or [])]
    if m_lv and p_seq and len(m_lv) == len(p_seq):
        offs = {pl - ml for (mt, ml), (pt, pl) in zip(m_lv, p_seq)}
        if len(offs) > 1:
            base = min(offs)
            for (mt, ml), (pt, pl) in zip(m_lv, p_seq):
                if (pl - ml) != base:
                    bad.append("heading level drifts: %r is level %d in the "
                               "docmodel and renders at h%d on the page, where "
                               "the constant offset is %+d" % (mt[:48], ml, pl, base))
                    break
    elif m_lv and p_seq:
        bad.append("heading COUNT differs: %d in the docmodel, %d on the page"
                   % (len(m_lv), len(p_seq)))
    if len(m_pres) != len(page["pres"]):
        bad.append("verbatim blocks: %d in the docmodel, %d rendered on the page"
                   % (len(m_pres), len(page["pres"])))
    else:
        for a, b in zip(m_pres, [norm(x) for x in page["pres"]]):
            if a != b:
                bad.append("a verbatim block differs between docmodel and page")
                break
    return bad


def selftest():
    """It must fail on divergence and pass on agreement."""
    base = [{"kind": "h1", "text": "Methods"},
            {"kind": "table", "n": 1, "caption": "Included trials"},
            {"kind": "figure", "n": 1, "caption": "Forest plot"},
            {"kind": "pre", "text": "Random-Effects Model (k = 4)"}]
    dx = {"tables": [(1, "Included trials")], "figures": [(1, "Forest plot")],
          "text": "Methods Table 1. Included trials Figure 1. Forest plot "
                  "Random-Effects Model (k = 4)"}
    pg = {"heads": ["Methods"], "tables": ["Table 1. Included trials"],
          "figures": ["Figure 1. Forest plot"],
          "pres": ["Random-Effects Model (k = 4)"], "text": "Methods"}
    cases = [("aligned document", base, dx, pg, False)]

    d2 = dict(dx); d2["tables"] = [(1, "Included studies")]
    cases.append(("a table caption reworded in the .docx only", base, d2, pg, True))
    p2 = dict(pg); p2["figures"] = []
    cases.append(("a figure the page does not render", base, dx, p2, True))
    p3 = dict(pg); p3["heads"] = []
    cases.append(("a heading missing from the page", base, dx, p3, True))
    p4 = dict(pg); p4["pres"] = ["Random-Effects Model (k = 3)"]
    cases.append(("verbatim block differing by its own k", base, dx, p4, True))
    b2 = base + [{"kind": "h1", "text": "Comparison with published syntheses"}]
    cases.append(("a section in the model that reached neither surface",
                  b2, dx, pg, True))

    # --- NEGATIVES for the two extractor bugs. Both of these reported a
    # divergence in a document that was correctly aligned, so both are pinned.
    base_arrow = [{"kind": "pre", "text": "Limit Estimate (as sei -> 0): b = -0.3"}]
    dx_arrow = {"tables": [], "figures": [],
                "text": "Limit Estimate (as sei -> 0): b = -0.3"}
    pg_arrow = {"heads": [], "tables": [], "figures": [],
                "pres": ["Limit Estimate (as sei -> 0): b = -0.3"], "text": ""}
    # Heading text is NOT unique here: the same label appears as a narrative
    # subsection and in the Recorded-detail appendix, one level apart. This must
    # PASS -- it is correct nesting, and the first cut of the level check called
    # it a drift.
    cases.append(("NEGATIVE: the same heading text at two different levels",
                  [{"kind": "h2", "text": "Protocol and registration"},
                   {"kind": "h3", "text": "Protocol and registration"}],
                  {"tables": [], "figures": [],
                   "text": "Protocol and registration Protocol and registration"},
                  {"heads": ["Protocol and registration",
                             "Protocol and registration"],
                   "head_levels": [["h3", "Protocol and registration"],
                                   ["h4", "Protocol and registration"]],
                   "tables": [], "figures": [], "pres": [], "text": ""}, False))
    cases.append(("NEGATIVE: an arrow that is XML-escaped in the .docx",
                  base_arrow, dx_arrow, pg_arrow, False))
    dx_legend = {"tables": [(1, "Included trials")],
                 "figures": [(1, "Forest plot")],
                 "text": dx["text"] + " Figure legends Figure 1. Forest plot"}
    cases.append(("NEGATIVE: captions repeated in a Figure legends section",
                  base, dx_legend, pg, False))

    print("=== presentation contract ===")
    pres_cases = [
        ("a Word default document (Calibri, no spacing, no tblHeader)",
         {"font": "Calibri", "line_spacing": None, "tables": 17,
          "tbl_header": 0, "tbl_styles": {"LightGrid-Accent1"},
          "over_measure": 15, "measure_in": 6.0}, True),
        ("a document meeting the contract",
         {"font": "Georgia", "line_spacing": "360", "tables": 17,
          "tbl_header": 17, "tbl_styles": {"TableGrid"},
          "over_measure": 0, "measure_in": 6.0}, False),
    ]
    ok = True
    for name, dd, want_fail in pres_cases:
        got = bool([1 for _n, pr in PRESENTATION.items() if not pr(dd)])
        good = got == want_fail
        ok &= good
        print("  %-52s %s expected=%s %s"
              % (name, "FAIL" if got else "PASS",
                 "FAIL" if want_fail else "PASS", "correct" if good else "WRONG"))
    print()
    print("=== the gate must FAIL on divergence and PASS on agreement ===")
    for name, m, dd, pp, want_fail in cases:
        got = bool(check(m, dd, pp))
        good = got == want_fail
        ok &= good
        print("  %-52s %s expected=%s %s"
              % (name, "FAIL" if got else "PASS",
                 "FAIL" if want_fail else "PASS", "correct" if good else "WRONG"))
    print("\nalignment gate proved able to fail on every divergence:", ok)
    return 0 if ok else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        raise SystemExit(selftest())
    if len(sys.argv) < 4:
        raise SystemExit("usage: alignment_gate.py <docmodel.json> <docx> <page.html>")
    model, meta = model_blocks(sys.argv[1])
    problems = check(model, docx_sequence(sys.argv[2]), page_docview(sys.argv[3]))
    problems += check_presentation(sys.argv[2])
    print("blocks in the docmodel: %d  (tables %s, figures %s)"
          % (len(model), meta.get("tables"), meta.get("figures")))
    if problems:
        print("\n%d ALIGNMENT PROBLEM(S):" % len(problems))
        for p in problems:
            print("   -", p)
    else:
        print("\nALIGNED: the Word file and the page render the same document.")
    raise SystemExit(1 if problems else 0)
