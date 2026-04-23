#!/usr/bin/env python3
"""Fix the pre-existing structural bug where `<div id="manuscript-text">` was
inserted INSIDE the `<style>` block in 76 of 99 apps. The element exists in
source but is treated as CSS text by the browser, so getElementById() returns
null and generateManuscriptText() silently no-ops.

Two-step fix per affected app:
  1. REMOVE the 9-line panel HTML wrongly placed inside <style>
  2. INSERT a fresh panel inside the tab-analysis <section>, right before
     its closing </section> tag
"""
import argparse, pathlib, re, sys

ROOT = pathlib.Path(r"C:\Projects\Finrenone")

# The exact 9-line HTML block as currently found inside <style>
# (CRLF tolerated via LF-normalization pre-match).
BROKEN_PANEL = (
    '                    <!-- Auto-Generated Methods & Results Text -->\n'
    '                    <div class="glass p-8 rounded-[30px] border border-indigo-500/20 bg-indigo-500/5">\n'
    '                        <div class="flex items-center justify-between mb-4">\n'
    '                            <h3 class="text-xs font-bold opacity-60 uppercase tracking-[0.3em]"><i class="fa-solid fa-pen-nib mr-1"></i> Auto-Generated Manuscript Text</h3>\n'
    '                            <button onclick="copyManuscriptText()" class="text-[11px] font-bold text-indigo-400 uppercase bg-indigo-400/10 px-4 py-1.5 rounded-full border border-indigo-400/20 hover:bg-indigo-400/20 transition-all"><i class="fa-solid fa-copy mr-1"></i> Copy All</button>\n'
    '                        </div>\n'
    '                        <div id="manuscript-text" class="space-y-6 text-sm text-slate-300 leading-relaxed" style="font-family: Georgia, serif;" aria-live="polite">\n'
    '                            <p class="text-slate-500 italic">Click "Generate Output" to create manuscript text.</p>\n'
    '                        </div>\n'
    '                    </div>\n'
)

# The panel we WANT to insert at the correct location (inside tab-analysis).
# Uses same content + indentation as CFTR's working placement.
CORRECT_PANEL = (
    '\n                    <!-- Auto-Generated Methods & Results Text -->\n'
    '                    <div class="glass p-8 rounded-[30px] border border-indigo-500/20 bg-indigo-500/5">\n'
    '                        <div class="flex items-center justify-between mb-4">\n'
    '                            <h3 class="text-xs font-bold opacity-60 uppercase tracking-[0.3em]"><i class="fa-solid fa-pen-nib mr-1"></i> Auto-Generated Manuscript Text</h3>\n'
    '                            <button onclick="copyManuscriptText()" class="text-[11px] font-bold text-indigo-400 uppercase bg-indigo-400/10 px-4 py-1.5 rounded-full border border-indigo-400/20 hover:bg-indigo-400/20 transition-all"><i class="fa-solid fa-copy mr-1"></i> Copy All</button>\n'
    '                        </div>\n'
    '                        <div id="manuscript-text" class="space-y-6 text-sm text-slate-300 leading-relaxed" style="font-family: Georgia, serif;" aria-live="polite">\n'
    '                            <p class="text-slate-500 italic">Click "Generate Output" to create manuscript text.</p>\n'
    '                        </div>\n'
    '                    </div>\n'
)


def apply_to_file(path: pathlib.Path, dry_run: bool) -> str:
    text = path.read_text(encoding="utf-8", newline="")

    # Detect "already properly placed": first <div id="manuscript-text"
    # occurrence is AFTER the closing </style>.
    style_close = text.find("\n    </style>")
    mt_first = text.find('<div id="manuscript-text"')
    if style_close < 0:
        return f"SKIP {path.name}: no </style> found"
    if mt_first < 0:
        return f"SKIP {path.name}: no manuscript-text element present at all"
    if mt_first > style_close:
        return f"SKIP {path.name}: already properly placed (after </style>)"

    crlf = "\r\n" in text
    work = text.replace("\r\n", "\n") if crlf else text

    # Step 1: remove the broken panel block (only the first one)
    if work.count(BROKEN_PANEL) != 1:
        return f"FAIL {path.name}: BROKEN_PANEL matched {work.count(BROKEN_PANEL)} times (expected 1)"
    work = work.replace(BROKEN_PANEL, "", 1)

    # Step 2: insert correct panel before </section> that closes tab-analysis.
    # The first `\n        </section>` AFTER `<section id="tab-analysis"` is the
    # closing tag; we insert the panel right before it.
    analysis_pos = work.find('<section id="tab-analysis"')
    if analysis_pos < 0:
        return f"FAIL {path.name}: no tab-analysis section"
    close_match = re.search(r"\n        </section>", work[analysis_pos:])
    if not close_match:
        return f"FAIL {path.name}: no </section> closing tab-analysis"
    insert_at = analysis_pos + close_match.start()
    # Insert CORRECT_PANEL then a matching blank line (the closing \n of
    # the panel already provides separation from </section>).
    work = work[:insert_at] + CORRECT_PANEL + work[insert_at:]

    if not dry_run:
        out = work.replace("\n", "\r\n") if crlf else work
        path.write_text(out, encoding="utf-8", newline="")
    return f"OK   {path.name}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    if not (args.dry_run or args.apply): ap.error("pass --dry-run or --apply")
    targets = sorted(ROOT.glob("*_REVIEW.html"))
    ok = skip = fail = 0
    for p in targets:
        r = apply_to_file(p, dry_run=args.dry_run)
        if r.startswith("OK"): ok += 1
        elif r.startswith("SKIP"): skip += 1
        else: fail += 1
        if not r.startswith("SKIP"): print(r)
    print(f"\nSummary: {len(targets)} | {ok} fix | {skip} skip | {fail} fail | mode={'dry-run' if args.dry_run else 'apply'}")
    if fail: sys.exit(1)


if __name__ == "__main__":
    main()
