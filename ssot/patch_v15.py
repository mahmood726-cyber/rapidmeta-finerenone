"""Design-review execution: the four defects, then size and craft.

Every change here is one the printed PDF would approve of, which is the arbiter
the review proposes and the one I have used to decide the borderline calls.
"""
import ast
import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
N = [0]


def sub(path, old, new, tag):
    s = open(path, encoding="utf-8").read()
    if old not in s:
        raise SystemExit("ANCHOR MISSING (%s) in %s" % (tag, path))
    open(path, "w", encoding="utf-8").write(s.replace(old, new, 1))
    N[0] += 1
    print("  %-46s %s" % (tag, path.split("/")[-1]))


PJ = "ssot/projectors.py"
BT = "ssot/build_tabbed.py"
FG = "ssot/figures.py"

print("DEFECT 1 -- delete the script (no-JS rule, and a localStorage draft keyed")
print("            on document.title survives across builds)")
sub(BT, "%s%s\n<p><small>Every number on this page is projected",
    "%s\n<p><small>Every number on this page is projected", "drop READER_JS slot")
sub(BT, "p(canon[\"title\"]), p(canon[\"question\"]), body, READER_JS)",
    "p(canon[\"title\"]), p(canon[\"question\"]), body)", "drop READER_JS arg")

print("DEFECT 2 -- theme: every hardcoded hex becomes a token, so dark is legible")
sub(PJ, ''' .tabnav{display:flex;flex-wrap:wrap;gap:.25rem;border-bottom:2px solid #d4d4d8;margin:1.25rem 0 0}
 .tabnav label{padding:.5rem .9rem;cursor:pointer;font-size:.9rem;font-weight:600;color:#52525b;border:1px solid transparent;border-bottom:none;border-radius:.375rem .375rem 0 0}
 .tabnav label:hover{color:#111;background:#f4f4f5}
 .panel{height:0;overflow:hidden}
 .toc{margin:.6rem 0 1rem;padding:.5rem .75rem;background:#f4f4f5;border-radius:.375rem;font-size:.85rem;color:#3f3f46}
 .card.rec{border-left:4px solid #d4d4d8}
 .mine{margin-top:.5rem;padding-top:.5rem;border-top:1px dashed #d4d4d8;font-size:.85rem;color:#52525b}
 .mine button,.chip{margin-right:.35rem;padding:.25rem .6rem;border:1px solid #d4d4d8;border-radius:.25rem;background:#fafafa;cursor:pointer;font:inherit;font-size:.85rem}
 #draft{width:100%;font:inherit;font-size:.9rem;padding:.6rem;border:1px solid #d4d4d8;border-radius:.375rem}
 svg{max-width:100%;height:auto}
 a.dl{display:inline-block;padding:.3rem .7rem;border:1px solid #d4d4d8;border-radius:.25rem;background:#fafafa;text-decoration:none;font-size:.85rem}
 pre{background:#fafafa;border:1px solid #e4e4e7;border-radius:.375rem;padding:.6rem;overflow-x:auto;font-size:.8rem;white-space:pre-wrap}
 tr.inc{background:#f0fdf4} tr.und{background:#fefce8}
''',
    ''' .tabnav{display:flex;flex-wrap:wrap;gap:.25rem;border-bottom:2px solid var(--line);margin:1.25rem 0 0}
 .tabnav label{padding:.5rem .9rem;cursor:pointer;font-size:.9rem;font-weight:600;color:var(--muted);border:1px solid transparent;border-bottom:none;border-radius:.375rem .375rem 0 0}
 .tabnav label:hover{color:var(--fg);background:var(--soft)}
 .panel{height:0;overflow:hidden}
 .toc{margin:.6rem 0 1rem;padding:.5rem .75rem;background:var(--soft);border-radius:.375rem;font-size:.85rem;color:var(--muted)}
 .card.rec{border-left:4px solid var(--line)}
 .mine{margin-top:.5rem;padding-top:.5rem;border-top:1px dashed var(--line);font-size:.85rem;color:var(--muted)}
 .mine button,.chip{margin-right:.35rem;padding:.25rem .6rem;border:1px solid var(--line);border-radius:.25rem;background:var(--soft);color:var(--fg);cursor:pointer;font:inherit;font-size:.85rem}
 svg{max-width:100%;height:auto}
 a.dl{display:inline-block;padding:.3rem .7rem;border:1px solid var(--line);border-radius:.25rem;background:var(--soft);color:var(--accent);text-decoration:none;font-size:.85rem}
 pre{background:var(--soft);border:1px solid var(--line);border-radius:.375rem;padding:.6rem;overflow-x:auto;font-size:.8rem;white-space:pre-wrap;color:var(--fg)}
 /* Ruled, not filled. Mint-green and pale-yellow row fills were the most
    dashboard-looking thing on the page and are a journalistic status device,
    not a scientific one. A left rule carries the same information and survives
    printing in black and white. */
 tr.inc td:first-child{border-left:3px solid var(--accent)}
 tr.und td:first-child{border-left:3px solid var(--warnb)}
''', "tab CSS -> tokens, row fills -> rules")

print("DEFECT 3 -- doctype, lang, viewport")
sub(BT, 'return """<meta charset="utf-8">',
    'return """<!doctype html>\n<html lang="en">\n<meta charset="utf-8">\n'
    '<meta name="viewport" content="width=device-width,initial-scale=1">',
    "doctype + lang + viewport")

print("DEFECT 4 -- the TOC generator stripped every digit")
sub(PJ, '''        heads = [re.sub(r"[0-9]", "", re.sub(r"<[^>]+>", "", h)).strip(" .·-")
                 for h in re.findall(r"<h3[^>]*>(.*?)</h3>", body, re.S)]''',
    '''        # The digit strip here produced "Open disagreements ()", "RoB- assessment"
        # and "ClinicalTrials.gov API v" in the first line of nearly every tab. It
        # was the no-unprojected-numerals rule applied at the wrong scope: that
        # rule governs numbers the page ASSERTS, and a table of contents asserts
        # nothing -- it echoes a heading that has already been projected and has
        # already passed the rule. Copying the heading verbatim is therefore
        # strictly safer than editing it, because an edited echo can differ from
        # what it claims to point at.
        heads = [re.sub(r"<[^>]+>", "", h).strip(" .·-")
                 for h in re.findall(r"<h3[^>]*>(.*?)</h3>", body, re.S)]''',
    "TOC keeps digits")

print("STEP 5 -- drop TIFF and JPEG")
sub(FG, '''        for k, p in convert(png, stem, outdir).items():
            items.append(("TIFF (LZW, %d dpi)" % DPI if k == "tiff"
                          else "JPG (quality 95, %d dpi)" % DPI,
                          os.path.basename(p),
                          _uri(p, "image/tiff" if k == "tiff" else "image/jpeg"),
                          os.path.getsize(p)))''',
    '''        # TIFF and JPEG are no longer offered. JPEG is a lossy photographic
        # codec and these are line art: it puts ringing on every rule and every
        # glyph edge, so it was strictly worse than the PNG beside it. The TIFF
        # was a lossless duplicate of that PNG at four times the bytes. Dropping
        # both takes the page from 5.25 MB to about 1.4 MB and IMPROVES the
        # artwork. SVG remains the master and PNG the raster of record; any
        # journal wanting TIFF can convert either without loss.''',
    "drop TIFF/JPG from downloads")

print("STEP 7 -- typography: measure, serif prose, sans evidence")
sub(BT, ''' body{font-family:system-ui,-apple-system,sans-serif;max-width:64rem;
       margin:0 auto;padding:1.5rem;line-height:1.6;
       color:var(--fg);background:var(--bg)}''',
    ''' /* Measure was ~125 characters at 64rem/16px -- about double a comfortable
    line. Serif for prose, sans for tables and numbers: a reader can tell at a
    glance which register they are in, and serif digits in dense tables are
    worse than a good sans. No webfont, deliberately -- this file is opened from
    disk by people on slow connections and 200 KB of woff2 buys nothing that a
    system serif does not already give. */
 body{font-family:Charter,"Bitstream Charter","Iowan Old Style",
       "Source Serif Pro",Georgia,"Times New Roman",serif;
       max-width:46rem;margin:0 auto;padding:1.5rem 1.25rem;
       font-size:1.02rem;line-height:1.65;color:var(--fg);background:var(--bg);
       text-rendering:optimizeLegibility}
 h1,h2,h3,h4,.tabnav label,th,td,.num,code,pre,small,.toc,figcaption,
 a.dl,.chip{font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
 th,td{font-variant-numeric:tabular-nums}
 h1{font-size:1.6rem;line-height:1.25;letter-spacing:-.01em}
 p{margin:.7rem 0}
 /* Wide evidence may exceed the prose measure without widening the page. */
 .card table{display:block;overflow-x:auto;max-width:100%}
 @media (max-width:560px){body{padding:1rem .75rem;font-size:1rem}
   .tabnav label{padding:.4rem .6rem;font-size:.82rem}}''',
    "typography: 46rem measure, serif prose, sans evidence")

print("STEP 7b -- soft token for both themes")
sub(BT, "       --paper:#fff;--paperfg:#111;--thbg:#f4f4f5}",
    "       --paper:#fff;--paperfg:#111;--thbg:#f4f4f5;--soft:#f4f4f5}", "light --soft")
sub(BT, "       --paper:#15181e;--paperfg:#e8e8ec;--thbg:#1c2029}",
    "       --paper:#15181e;--paperfg:#e8e8ec;--thbg:#1c2029;--soft:#1a1e26}",
    "dark --soft")

for f in (PJ, BT, FG):
    ast.parse(open(f, encoding="utf-8").read())
print("\n%d edits applied; all three modules parse" % N[0])
