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
    cases.append(("NEGATIVE: an arrow that is XML-escaped in the .docx",
                  base_arrow, dx_arrow, pg_arrow, False))
    dx_legend = {"tables": [(1, "Included trials")],
                 "figures": [(1, "Forest plot")],
                 "text": dx["text"] + " Figure legends Figure 1. Forest plot"}
    cases.append(("NEGATIVE: captions repeated in a Figure legends section",
                  base, dx_legend, pg, False))

    ok = True
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
    print("blocks in the docmodel: %d  (tables %s, figures %s)"
          % (len(model), meta.get("tables"), meta.get("figures")))
    if problems:
        print("\n%d ALIGNMENT PROBLEM(S):" % len(problems))
        for p in problems:
            print("   -", p)
    else:
        print("\nALIGNED: the Word file and the page render the same document.")
    raise SystemExit(1 if problems else 0)
