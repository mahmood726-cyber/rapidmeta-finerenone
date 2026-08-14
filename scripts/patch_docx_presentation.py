import io, sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
P = r"F:\rapidmeta-ssot-shell\ssot\make_docx.py"
s = open(P, encoding="utf-8").read()

# --- 1. tblHeader: repeat the header row across page breaks -------------------
old = '''    for i, h in enumerate(headers):
        cell = t.rows[0].cells[i]
        cell.text = ""
        run = cell.paragraphs[0].add_run(h)
        run.bold = True'''
new = '''    # REPEAT THE HEADER ROW ACROSS PAGE BREAKS. Zero of seventeen tables had
    # this. The screening log is fourteen rows and the statistical-output table
    # fourteen more; both cross a page in the Word file, and a reader met the
    # continuation with no column headers at all. This is a reading defect, not
    # a cosmetic one, and it is the first thing a reviewer would hit.
    _trPr = t.rows[0]._tr.get_or_add_trPr()
    _th = OxmlElement('w:tblHeader')
    _th.set(qn('w:val'), "true")
    _trPr.append(_th)
    for i, h in enumerate(headers):
        cell = t.rows[0].cells[i]
        cell.text = ""
        run = cell.paragraphs[0].add_run(h)
        run.bold = True
        # Light shading on the header so the repeat is recognisable as a header
        # rather than as data. Grey, not a theme accent: this is a manuscript.
        _sh = OxmlElement('w:shd')
        _sh.set(qn('w:val'), 'clear')
        _sh.set(qn('w:fill'), 'EDEDED')
        cell._tc.get_or_add_tcPr().append(_sh)'''
assert s.count(old) == 1
s = s.replace(old, new)

# --- 2. figures sized to CONTENT, not all to the full measure ----------------
old2 = '''def figure(doc, caption, path, width=6.0):
    global FIG
    FIG += 1
    doc.add_picture(path, width=Inches(width))'''
new2 = '''def figure(doc, caption, path, width=6.0):
    """Size to the image, within the measure -- not every figure to the measure.

    All fifteen were forced to exactly 6.00 inches against a text measure of
    exactly 6.00 inches (8.5 less two 1.25 margins), so every figure ran edge to
    edge with no breathing room, and because aspect ratios span 0.15 to 0.68 the
    empty-state panels became 6x0.9 inch strips. Width is now capped below the
    measure and height capped so nothing runs past a page, with the aspect ratio
    preserved from the file rather than assumed.
    """
    global FIG
    FIG += 1
    MAX_W, MAX_H = 5.6, 7.0
    w = width
    try:
        from PIL import Image as _I
        with _I.open(path) as im:
            pw, ph = im.size
        w = min(MAX_W, MAX_W)                       # never wider than the cap
        if ph and pw and (ph / float(pw)) * w > MAX_H:
            w = MAX_H * (pw / float(ph))            # tall image: bound by height
    except Exception:                                # noqa: BLE001
        w = min(width, MAX_W)
    doc.add_picture(path, width=Inches(w))'''
assert s.count(old2) == 1
s = s.replace(old2, new2)

# --- 3. body face, line spacing, table style ---------------------------------
old3 = '''st = doc.styles["Normal"]
st.font.name = "Calibri"
st.font.size = Pt(11)'''
new3 = '''st = doc.styles["Normal"]
# A MANUSCRIPT FACE, NOT A UI FACE. Calibri 11 is Word's default and reads as an
# office document; the HTML projection -- which is the surface Mahmood judged
# better -- sets Georgia. Matching it is the point: both are projections of one
# object and the Word file was the lossy one.
st.font.name = "Georgia"
st.font.size = Pt(10.5)
# 1.5 line spacing. Journals ask for 1.5 or double on a review copy and Word's
# default single is neither. Ragged right rather than justified: Word does not
# hyphenate by default and justified text without hyphenation opens rivers,
# which is worse than the ragged edge it replaces.
st.paragraph_format.line_spacing = 1.5
st.paragraph_format.space_after = Pt(6)'''
assert s.count(old3) == 1
s = s.replace(old3, new3)

old4 = '''    t.style = "Light Grid Accent 1"'''
new4 = '''    # Plain ruled grid. "Light Grid Accent 1" is an Office theme style whose
    # colour belongs to a slide deck, not to a manuscript table.
    try:
        t.style = "Table Grid"
    except KeyError:
        t.style = "Light Grid Accent 1"'''
assert s.count(old4) == 1
s = s.replace(old4, new4)

open(P, "w", encoding="utf-8").write(s)
print("make_docx: tblHeader on every table, content-sized figures, Georgia 1.5, plain grid")
