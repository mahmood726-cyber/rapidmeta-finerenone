import io, sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
P = r"F:\rapidmeta-ssot-shell\ssot\make_docx.py"
s = open(P, encoding="utf-8").read()

# 1. the REAL renderer learns monospace cells
old = '''def table(doc, caption, headers, rows):
    global TBL
    TBL += 1
    c = doc.add_paragraph("Table %d. %s" % (TBL, caption))
    c.runs[0].bold = True
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Light Grid Accent 1"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, h in enumerate(headers):
        cell = t.rows[0].cells[i]
        cell.text = ""
        run = cell.paragraphs[0].add_run(h)
        run.bold = True
    for r in rows:
        cells = t.add_row().cells
        for i, v in enumerate(r):
            cells[i].text = n(v)
    doc.add_paragraph()
    return t'''
new = '''def table(doc, caption, headers, rows, mono_cols=()):
    """Render a table. `mono_cols` are column indices holding VERBATIM text.

    Quoted evidence belongs in a table with its context -- what result it belongs
    to, the call, the estimate -- not as a free-standing block a reader has to
    match up by eye. But a metafor table whose columns stop lining up is a
    misquotation, so the monospace and the line breaks are preserved INSIDE the
    cell: one paragraph per line, Consolas, zero space-after.
    """
    global TBL
    TBL += 1
    c = doc.add_paragraph("Table %d. %s" % (TBL, caption))
    c.runs[0].bold = True
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Light Grid Accent 1"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, h in enumerate(headers):
        cell = t.rows[0].cells[i]
        cell.text = ""
        run = cell.paragraphs[0].add_run(h)
        run.bold = True
    for r in rows:
        cells = t.add_row().cells
        for i, v in enumerate(r):
            if i in mono_cols:
                cell = cells[i]
                cell.text = ""
                lines = str(v if v is not None else "").split("\\n")
                for j, line in enumerate(lines):
                    para = cell.paragraphs[0] if j == 0 else cell.add_paragraph()
                    para.paragraph_format.space_after = Pt(0)
                    run = para.add_run(line)
                    run.font.name = "Consolas"
                    run.font.size = Pt(7.5)
            else:
                cells[i].text = n(v)
    doc.add_paragraph()
    return t'''
assert s.count(old) == 1
s = s.replace(old, new)

# 2. the RECORDER carries mono_cols into the docmodel so the page matches
old2 = '''def table(doc, caption, headers, rows):
    global TBL
    TBL += 1
    DOCMODEL.append({"kind": "table", "n": TBL, "caption": caption,
                     "headers": [str(h) for h in headers],
                     "rows": [[n(v) for v in r] for r in rows]})
    if _DEFER_ON:
        _DEFERRED_T.append((TBL, caption, headers, rows))
        return None
    return _real_table(doc, caption, headers, rows)'''
new2 = '''def table(doc, caption, headers, rows, mono_cols=()):
    global TBL
    TBL += 1
    # mono_cols travels in the block so the page renders the same cells verbatim.
    # A quotation that is monospaced in one surface and reflowed in the other is
    # two different quotations, which the alignment gate would then have to call
    # a divergence.
    DOCMODEL.append({"kind": "table", "n": TBL, "caption": caption,
                     "headers": [str(h) for h in headers],
                     "mono_cols": list(mono_cols),
                     "rows": [[(v if i in mono_cols else n(v))
                               for i, v in enumerate(r)] for r in rows]})
    if _DEFER_ON:
        _DEFERRED_T.append((TBL, caption, headers, rows, tuple(mono_cols)))
        return None
    return _real_table(doc, caption, headers, rows, mono_cols)'''
assert s.count(old2) == 1
s = s.replace(old2, new2)

# 3. deferred emission passes it through
old3 = '''    for _n, _cap, _hd, _rw in _DEFERRED_T:
        TBL = _n - 1
        _real_table(doc, _cap, _hd, _rw)'''
new3 = '''    for _n, _cap, _hd, _rw, _mc in _DEFERRED_T:
        TBL = _n - 1
        _real_table(doc, _cap, _hd, _rw, _mc)'''
assert s.count(old3) == 1
s = s.replace(old3, new3)

# 4. R output section becomes ONE table instead of loose pre blocks
old4 = '''    for _bid, _b in _RO["blocks"].items():
        doc.add_heading(_b.get("label", _bid), 2)
        doc.add_paragraph("Call: %s" % _b.get("call", ""))
        verbatim(doc, _b.get("output", ""))'''
new4 = '''    table(doc, "Statistical output quoted verbatim, with the call that produced it",
          ["Result", "Call", "Verbatim output"],
          [[_b.get("label", _bid), _b.get("call", ""), _b.get("output", "")]
           for _bid, _b in _RO["blocks"].items()],
          mono_cols=(2,))'''
assert s.count(old4) == 1
s = s.replace(old4, new4)

# 5. the comparison section's quoted evidence becomes a table too
old5 = '''        doc.add_heading("Quoted evidence for each check", 2)
        for c in _ck:
            _q = c.get("quote")
            doc.add_paragraph("%s -- %s. %s"
                              % (c.get("verdict", ""), c.get("what", ""),
                                 ("Quoted from %s: \\u201c%s\\u201d"
                                  % (c.get("location", ""), _q)) if _q else
                                 ("Checked at %s; nothing to quote because the "
                                  "item is absent from the paper."
                                  % c.get("location", ""))))'''
new5 = '''        # Claim, verbatim quotation, location, adjudication -- in that order,
        # because that is the order a reader checks us in.
        table(doc, "Quoted evidence for each check, with its location and our "
                   "adjudication",
              ["Claim checked", "Verbatim quotation", "Location", "Adjudication"],
              [[c.get("what", ""),
                (c.get("quote") or
                 "[nothing to quote: the item is absent from the paper]"),
                c.get("location", ""),
                "%s%s" % (c.get("verdict", ""),
                          (" (%s)" % c["severity"]) if c.get("severity") else "")]
               for c in _ck],
              mono_cols=())'''
assert s.count(old5) == 1
s = s.replace(old5, new5)

open(P, "w", encoding="utf-8").write(s)
print("make_docx: mono_cols tables; R output and quoted evidence now tabular")

# ---------------------------------------------------------------- wysiwyg
W = r"F:\rapidmeta-ssot-shell\ssot\wysiwyg.py"
w = open(W, encoding="utf-8").read()
oldw = '''def _table(b):
    head = "".join("<th>%s</th>" % e(str(h)) for h in b.get("headers", []))
    body = ""
    for r in b.get("rows", []):
        body += ("      <tr>%s</tr>%s"
                 % ("".join("<td>%s</td>" % e(str(v)) for v in r), NL))'''
neww = '''def _table(b):
    head = "".join("<th>%s</th>" % e(str(h)) for h in b.get("headers", []))
    body = ""
    mono = set(b.get("mono_cols") or [])
    for r in b.get("rows", []):
        # A verbatim cell keeps its own line breaks and column alignment. Without
        # this the page reflows a metafor table that the Word file preserves, and
        # the two surfaces would be showing different quotations.
        body += ("      <tr>%s</tr>%s"
                 % ("".join(("<td><pre class='cellpre'>%s</pre></td>"
                             if i in mono else "<td>%s</td>")
                            % e(str(v)) for i, v in enumerate(r)), NL))'''
assert w.count(oldw) == 1
w = w.replace(oldw, neww)
oldc = " .doc pre{font-family:Consolas,'SF Mono',Menlo,monospace;font-size:.76rem;"
newc = (" .doc pre.cellpre{margin:0;padding:.2rem .25rem;border:0;background:none;\n"
        "      font-size:.66rem;line-height:1.25;white-space:pre;overflow-x:auto}\n"
        " .doc pre{font-family:Consolas,'SF Mono',Menlo,monospace;font-size:.76rem;")
assert w.count(oldc) == 1
w = w.replace(oldc, newc)
open(W, "w", encoding="utf-8").write(w)
print("wysiwyg: verbatim table cells render as <pre>")
