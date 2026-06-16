#!/usr/bin/env python3
# sentinel:skip-file — local maintenance codemod (cache-bust token bump for shared Paper Studio assets)
"""Bump the ?v= cache-bust token on shared Paper Studio asset references to the CURRENT
content hash, across all root *_REVIEW.html. Idempotent: re-running with unchanged assets
is a no-op. Usage: python scripts/bump_paperstudio_cachebust.py [--apply]
"""
import hashlib, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
apply = "--apply" in sys.argv

def short(p):
    return hashlib.md5(ROOT.joinpath(p).read_bytes()).hexdigest()[:8]

css_v, js_v = short("assets/css/paper-studio.css"), short("assets/js/paper-studio.js")
print(f"target css ?v={css_v}  js ?v={js_v}\n")

pat_css = re.compile(r"(paper-studio\.css\?v=)[0-9a-fA-F]+")
pat_js  = re.compile(r"(paper-studio\.js\?v=)[0-9a-fA-F]+")

changed = already = skipped = 0
for f in sorted(ROOT.glob("*_REVIEW.html")):
    t = f.read_text(encoding="utf-8", newline="")
    if "paper-studio." not in t:
        skipped += 1; continue
    new = pat_css.sub(r"\g<1>"+css_v, t)
    new = pat_js.sub(r"\g<1>"+js_v, new)
    if new == t:
        already += 1; continue
    changed += 1
    if apply:
        f.write_text(new, encoding="utf-8", newline="")

print(f"{'APPLIED' if apply else 'DRY-RUN'}: {changed} to-update, {already} already-current, {skipped} no-ref")
