"""D3 + C6: Schema.org JSON-LD + lightweight accessibility patches.

D3. For every *.html page, inject a Schema.org `MedicalScholarlyArticle`
    JSON-LD block in <head>:
      - headline      = page <title>
      - description   = existing meta description (D1) or PICO digest
      - datePublished = file mtime (best-available signal)
      - dateModified  = same
      - author        = Mahmood Ahmad
      - publisher     = RapidMeta (Organization)
      - url           = canonical https://...github.io/.../<file>
      - about         = first PICO `cond` or `condition`
      - keywords      = drug + condition + 'meta-analysis, living review'
    Skip if a JSON-LD block already exists.

C6. Three low-risk a11y improvements:
      - Ensure <html lang="en"> is set (some pages don't have it).
      - Inject a "skip to main content" link as the first <body> child for
        keyboard users (visually hidden, focus-visible).
      - Add aria-label to icon-only <button>/<a> elements that have no
        text content but do have an onclick/href. Uses the `title=` attr
        when present, else falls back to the icon class name or a sensible
        default ("Action button").

Both passes are idempotent — they each leave a marker comment so re-runs
detect previous injections and no-op.
"""
from __future__ import annotations
import json
import re
import sys
import io
from datetime import date
from pathlib import Path

if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent.parent
PAGES_BASE = "https://mahmood726-cyber.github.io/rapidmeta-finerenone/"

TITLE_RE = re.compile(r"<title>(.*?)</title>", re.DOTALL | re.IGNORECASE)
DESC_RE = re.compile(r'<meta\s+name="description"\s+content="([^"]*)"', re.IGNORECASE)
HEAD_END_RE = re.compile(r"</head>", re.IGNORECASE)
PICO_FIELD_RE = re.compile(r"\b(pop|int|comp|out|drug|cond|condition):\s*'((?:[^'\\]|\\.)*)'")
HTML_OPEN_RE = re.compile(r"<html(\s[^>]*)?>", re.IGNORECASE)
BODY_OPEN_RE = re.compile(r"<body(\s[^>]*)?>", re.IGNORECASE)

JSONLD_MARK = "<!-- jsonld:begin -->"
JSONLD_END = "<!-- jsonld:end -->"
SKIPLINK_MARK = "<!-- a11y-skiplink:begin -->"
SKIPLINK_END = "<!-- a11y-skiplink:end -->"

SKIPLINK_BLOCK = (
    f"{SKIPLINK_MARK}\n"
    '<a href="#main" class="rm-a11y-skiplink" '
    'style="position:absolute;left:-999px;top:auto;width:1px;height:1px;'
    'overflow:hidden;z-index:9999;background:#0b1220;color:#fff;'
    'padding:8px 12px;border-radius:0 0 6px 0;text-decoration:none;'
    'font-family:system-ui,-apple-system,sans-serif;font-size:14px;" '
    'onfocus="this.style.left=\'0\';this.style.top=\'0\';this.style.width=\'auto\';'
    'this.style.height=\'auto\';" '
    'onblur="this.style.left=\'-999px\';">Skip to main content</a>\n'
    f"{SKIPLINK_END}"
)


def extract_first_pico(txt: str, key: str) -> str | None:
    for m in PICO_FIELD_RE.finditer(txt):
        if m.group(1) == key:
            return m.group(2).replace("\\'", "'")
    return None


def jsonld_for(p: Path, txt: str) -> str | None:
    if JSONLD_MARK in txt:
        return None  # already injected
    title_m = TITLE_RE.search(txt)
    headline = title_m.group(1).strip() if title_m else p.stem.replace("_", " ").title()
    desc_m = DESC_RE.search(txt)
    description = desc_m.group(1).strip() if desc_m else None

    drug = extract_first_pico(txt, "drug") or extract_first_pico(txt, "int")
    cond = extract_first_pico(txt, "cond") or extract_first_pico(txt, "condition")
    if drug:
        drug = drug.split("(")[0].strip()
    if cond:
        cond = cond.split("(")[0].strip()
    keywords = ["meta-analysis", "living review", "RapidMeta"]
    if drug:
        keywords.append(drug)
    if cond:
        keywords.append(cond)

    mtime = date.fromtimestamp(p.stat().st_mtime).isoformat()
    url = PAGES_BASE if p.name == "index.html" else PAGES_BASE + p.name

    payload = {
        "@context": "https://schema.org",
        "@type": "MedicalScholarlyArticle",
        "headline": _clean(headline),
        "name": _clean(headline),
        "url": url,
        "datePublished": mtime,
        "dateModified": mtime,
        "inLanguage": "en",
        "author": {
            "@type": "Person",
            "name": "Mahmood Ahmad",
            "identifier": "https://orcid.org/",
        },
        "publisher": {
            "@type": "Organization",
            "name": "RapidMeta",
            "url": PAGES_BASE,
        },
        "isAccessibleForFree": True,
        "keywords": ", ".join(keywords),
    }
    if description:
        payload["description"] = description[:5000]
    if cond:
        payload["about"] = {"@type": "MedicalCondition", "name": cond}
    if drug:
        payload["mentions"] = {"@type": "Drug", "name": drug}

    json_str = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
    return (
        f"{JSONLD_MARK}\n"
        f'<script type="application/ld+json">{json_str}</script>\n'
        f"{JSONLD_END}"
    )


def _clean(s: str) -> str:
    s = re.sub(r"\s+", " ", s).strip()
    return s[:300]


def patch_html(p: Path) -> dict:
    txt = p.read_text(encoding="utf-8", errors="replace")
    orig = txt
    stats = {"jsonld": False, "lang": False, "skiplink": False, "aria": 0}

    # D3 JSON-LD
    block = jsonld_for(p, txt)
    if block and "</head>" in txt:
        txt = txt.replace("</head>", block + "\n</head>", 1)
        stats["jsonld"] = True

    # C6.1 <html lang="en">
    html_m = HTML_OPEN_RE.search(txt)
    if html_m and "lang=" not in html_m.group(0):
        new_open = html_m.group(0).replace("<html", '<html lang="en"', 1)
        txt = txt[: html_m.start()] + new_open + txt[html_m.end():]
        stats["lang"] = True

    # C6.2 skip-link
    if SKIPLINK_MARK not in txt and "<body" in txt:
        # Insert right after the opening <body ...>
        body_m = BODY_OPEN_RE.search(txt)
        if body_m:
            insert_at = body_m.end()
            txt = txt[:insert_at] + "\n" + SKIPLINK_BLOCK + txt[insert_at:]
            stats["skiplink"] = True
            # Add id="main" to the first content container if it doesn't already have one.
            main_m = re.search(r'<main(\s[^>]*)?>', txt[insert_at + len(SKIPLINK_BLOCK):], re.IGNORECASE)
            if main_m:
                seg_start = insert_at + len(SKIPLINK_BLOCK)
                mm = re.search(r'<main(\s[^>]*)?>', txt[seg_start:], re.IGNORECASE)
                attrs = mm.group(1) or ""
                if 'id=' not in attrs:
                    repl = f'<main id="main"{attrs}>'
                    txt = txt[: seg_start + mm.start()] + repl + txt[seg_start + mm.end():]

    # C6.3 aria-label on empty button/anchor with onclick/href but no text
    # Only target buttons/anchors that contain a single <i class="..."> icon and no text node.
    def add_aria(match):
        tag = match.group(0)
        if "aria-label" in tag:
            return tag
        title_m = re.search(r'\btitle="([^"]+)"', tag)
        label = title_m.group(1) if title_m else None
        if not label:
            # Try data-tooltip / data-action.
            for attr in ("data-tooltip", "data-action", "aria-labelledby"):
                m2 = re.search(rf'\b{attr}="([^"]+)"', tag)
                if m2:
                    label = m2.group(1); break
        if not label:
            label = "Toolbar action"
        stats["aria"] += 1
        # Insert aria-label right after the tag name.
        return re.sub(r"^<(\w+)", rf'<\1 aria-label="{label}"', tag, count=1)

    txt = re.sub(
        r'<button(?![^>]*aria-label)[^>]*>\s*<i\s+class="[^"]*"\s*></i>\s*</button>',
        add_aria, txt,
    )

    if txt != orig:
        p.write_text(txt, encoding="utf-8")
    return stats


def main():
    targets = sorted(p for p in HERE.glob("*.html") if p.is_file())
    print(f"Scanning {len(targets):,} pages...")
    n_jsonld = n_lang = n_skip = n_aria = 0
    files_touched = 0
    for i, p in enumerate(targets, 1):
        s = patch_html(p)
        if any([s["jsonld"], s["lang"], s["skiplink"], s["aria"]]):
            files_touched += 1
        n_jsonld += int(s["jsonld"])
        n_lang += int(s["lang"])
        n_skip += int(s["skiplink"])
        n_aria += s["aria"]
        if i % 300 == 0:
            print(f"  [{i}/{len(targets)}] {p.name}")
    print(f"\nFiles touched          : {files_touched:,}")
    print(f"  JSON-LD injected     : {n_jsonld:,}")
    print(f"  <html lang> added    : {n_lang:,}")
    print(f"  skip-link added      : {n_skip:,}")
    print(f"  aria-label added     : {n_aria:,} buttons")


if __name__ == "__main__":
    main()
