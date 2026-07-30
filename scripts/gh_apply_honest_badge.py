#!/usr/bin/env python
"""Replace a RapidMeta integrity badge WHOLESALE with an honest one.

Why wholesale: the first HFrEF draft patched only the headline and appended a
new body, leaving a stale "Trials: 28" row behind - the badge then asserted 28
and 27 simultaneously. Partial badge edits are how self-contradiction ships.
This module finds the `<div id="rapidmeta-integrity-badge" ...>` element, walks
its children by BALANCED <div> matching, and swaps the entire element.

It also rewrites `window.__verdict` so the two surfaces state the same thing.

Usage:
  python scripts/gh_apply_honest_badge.py --app FILE --spec outputs/<x>_badge.json
  python scripts/gh_apply_honest_badge.py --app FILE --spec ... --check
"""
from __future__ import annotations

import argparse
import io
import json
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

BADGE_ID = 'id="rapidmeta-integrity-badge"'
RE_VERDICT = re.compile(r"(window\.__verdict\s*=\s*)(\{.*?\})(;)", re.S)


def find_badge_span(html: str) -> tuple[int, int]:
    """Return (start, end) of the whole badge element by balanced <div> walk."""
    i = html.find(BADGE_ID)
    if i < 0:
        raise SystemExit("no #rapidmeta-integrity-badge element in this app")
    start = html.rfind("<div", 0, i)
    if start < 0:
        raise SystemExit("badge id found but no opening <div>")
    depth = 0
    for m in re.finditer(r"<div\b|</div\s*>", html[start:]):
        depth += 1 if m.group(0).startswith("<div") else -1
        if depth == 0:
            return start, start + m.end()
    raise SystemExit("unbalanced <div> - refusing to edit")


def esc(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def render(spec: dict) -> str:
    bg, border = spec["bg"], spec["border"]
    rows = "".join(
        f'<div style="margin-top:6px;font-size:12.5px;">{esc(r)}</div>'
        for r in spec["body"]
    )
    facts = " &middot; ".join(
        f"{esc(k)}: <strong>{esc(str(v))}</strong>" for k, v in spec["facts"].items()
    )
    return (
        f'<div id="rapidmeta-integrity-badge" role="status" '
        f'style="background:{bg};color:#fff;padding:12px 20px;'
        f'font-family:system-ui,sans-serif;font-size:13.5px;'
        f'border-bottom:3px solid {border};line-height:1.55;">'
        f'<div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap;">'
        f'<strong style="font-size:14px;letter-spacing:0.04em;">{esc(spec["headline"])}</strong>'
        f'<span style="font-size:11.5px;">{facts}</span></div>'
        f'{rows}'
        f'<div style="margin-top:6px;font-size:10.5px;">{esc(spec["footer"])}</div>'
        f'</div>'
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--app", required=True)
    ap.add_argument("--spec", required=True)
    ap.add_argument("--check", action="store_true", help="report, do not write")
    args = ap.parse_args()

    spec = json.load(open(args.spec, encoding="utf-8"))
    # newline="" on BOTH read and write: the corpus is CRLF, and universal-newline
    # translation on read + newline="" on write silently rewrites every line
    # (6341/6341 diff on the first pilot attempt). Preserve endings verbatim.
    html = open(args.app, encoding="utf-8", newline="").read()

    o_open = len(re.findall(r"<div[\s>]", html))
    o_close = len(re.findall(r"</div>", html))

    s, e = find_badge_span(html)
    old = html[s:e]
    new = render(spec)
    print(f"badge span [{s}:{e}] len {len(old)} -> {len(new)}")
    print("OLD headline:", (re.search(r"<strong[^>]*>(.*?)</strong>", old, re.S) or [None, "?"])[1])
    print("NEW headline:", spec["headline"])

    html2 = html[:s] + new + html[e:]

    # Reconcile the machine surface with the visible one.
    m = RE_VERDICT.search(html2)
    if not m:
        raise SystemExit("no window.__verdict to reconcile")
    v = json.loads(m.group(2))
    v.update(spec["verdict_patch"])
    html2 = html2[:m.start()] + m.group(1) + json.dumps(v) + m.group(3) + html2[m.end():]
    print("verdict:", v.get("verdict"), "| reasons:", len(v.get("reasons", [])))

    n_open = len(re.findall(r"<div[\s>]", html2))
    n_close = len(re.findall(r"</div>", html2))
    if n_open - n_close != o_open - o_close:
        raise SystemExit(
            f"div balance changed ({o_open-o_close} -> {n_open-n_close}); refusing to write"
        )
    print(f"div balance preserved: {n_open} open / {n_close} close")

    if args.check:
        print("[CHECK ONLY] not written")
        return 0
    open(args.app, "w", encoding="utf-8", newline="").write(html2)
    print("written:", args.app)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
