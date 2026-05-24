"""D1+D2: SEO hygiene.

D1. Auto-generate a `<meta name="description" content="...">` per page from
    the PICO fields when present (pop / int / comp / out / drug / cond), else
    from the <h1> + opening prose. Cap at 160 chars (search-engine snippet
    limit). Skip pages that already have one.

D2. Emit sitemap.xml listing every *.html in the repo root with a
    GitHub-Pages-compatible URL prefix (https://mahmood726-cyber.github.io/
    rapidmeta-finerenone/<file>) and a lastmod from file mtime. Plus a
    robots.txt that allows everything and points crawlers at the sitemap.
"""
from __future__ import annotations
import re
import sys
import io
from datetime import date
from pathlib import Path

if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent.parent
PAGES_BASE = "https://mahmood726-cyber.github.io/rapidmeta-finerenone/"

H1_RE = re.compile(r"<h1[^>]*>(.*?)</h1>", re.DOTALL | re.IGNORECASE)
TITLE_RE = re.compile(r"<title>(.*?)</title>", re.DOTALL | re.IGNORECASE)
PICO_RE = re.compile(
    r"(pop|int|comp|out|drug|cond|population|intervention|comparator|outcome|drug_name|condition):\s*'([^']{6,500})'",
    re.IGNORECASE,
)
HERO_PROSE_RE = re.compile(r"<p[^>]*class=\"summary[^\"]*\"[^>]*>([\s\S]*?)</p>", re.IGNORECASE)
EXISTING_DESC_RE = re.compile(r'<meta\s+name="description"', re.IGNORECASE)
HEAD_END_RE = re.compile(r"</head>", re.IGNORECASE)


def strip_html(s: str) -> str:
    s = re.sub(r"<[^>]+>", " ", s)
    s = re.sub(r"&[a-z]+;", " ", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def derive_description(txt: str, stem: str) -> str | None:
    # Try PICO fields first.
    parts = []
    pico_seen = {}
    for m in PICO_RE.finditer(txt):
        k = m.group(1).lower()
        if k in pico_seen:
            continue
        pico_seen[k] = m.group(2).strip()
        if len(pico_seen) >= 4:
            break
    if pico_seen:
        order = ["drug", "drug_name", "int", "intervention", "cond", "condition", "pop", "population", "out", "outcome"]
        for k in order:
            if k in pico_seen:
                parts.append(pico_seen[k])
        snippet = "; ".join(parts)[:160]
        if len(snippet) >= 40:
            return snippet

    # Fall back to <h1> + first summary <p>.
    h1m = H1_RE.search(txt)
    if h1m:
        h1 = strip_html(h1m.group(1))
        prose_m = HERO_PROSE_RE.search(txt)
        prose = strip_html(prose_m.group(1)) if prose_m else ""
        combined = (h1 + " — " + prose).strip(" —")
        if len(combined) >= 40:
            return combined[:160]

    # Last-resort: <title> + stem.
    tm = TITLE_RE.search(txt)
    if tm:
        title = strip_html(tm.group(1))
        return f"{title} — RapidMeta living meta-analysis ({stem})."[:160]
    return None


def patch_meta_description(p: Path) -> bool:
    txt = p.read_text(encoding="utf-8", errors="replace")
    if EXISTING_DESC_RE.search(txt):
        return False
    stem = re.sub(r"\.html$", "", p.name)
    desc = derive_description(txt, stem)
    if not desc:
        return False
    # Escape quotes/ampersands for the attribute.
    safe = desc.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;").replace(">", "&gt;")
    tag = f'<meta name="description" content="{safe}">\n'
    # Lambda to avoid backref interpretation of \u etc. in the description text.
    if "</head>" not in txt:
        return False
    txt = txt.replace("</head>", tag + "</head>", 1)
    p.write_text(txt, encoding="utf-8")
    return True


def build_sitemap() -> str:
    pages = sorted(p for p in HERE.glob("*.html") if p.is_file())
    today = date.today().isoformat()
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for p in pages:
        mtime = date.fromtimestamp(p.stat().st_mtime).isoformat()
        # Index page gets priority 1.0, dashboard/audit 0.9, reviews 0.7.
        if p.name == "index.html":
            priority = "1.0"
        elif p.name in ("dashboard.html", "audit_table.html", "what_changed.html",
                        "cardiology_mortality_atlas.html"):
            priority = "0.9"
        elif p.name.endswith("_AUTO_REVIEW.html"):
            priority = "0.5"
        elif p.name.endswith("_AUTO_FULL_REVIEW.html"):
            priority = "0.6"
        else:
            priority = "0.7"
        # Index has the cleanest URL — use the root path.
        loc = PAGES_BASE if p.name == "index.html" else PAGES_BASE + p.name
        lines.append("  <url>")
        lines.append(f"    <loc>{loc}</loc>")
        lines.append(f"    <lastmod>{mtime}</lastmod>")
        lines.append(f"    <changefreq>monthly</changefreq>")
        lines.append(f"    <priority>{priority}</priority>")
        lines.append("  </url>")
    lines.append("</urlset>")
    return "\n".join(lines)


def build_robots() -> str:
    return (
        "User-agent: *\n"
        "Allow: /\n"
        f"Sitemap: {PAGES_BASE}sitemap.xml\n"
    )


def main():
    targets = sorted(p for p in HERE.glob("*.html") if p.is_file())
    print(f"D1: scanning {len(targets):,} pages for missing meta description...")
    n_added = 0
    for p in targets:
        if patch_meta_description(p):
            n_added += 1
    print(f"  added meta description to {n_added:,} pages")

    print("D2: writing sitemap.xml + robots.txt...")
    (HERE / "sitemap.xml").write_text(build_sitemap(), encoding="utf-8")
    (HERE / "robots.txt").write_text(build_robots(), encoding="utf-8")
    print(f"  sitemap.xml: {(HERE / 'sitemap.xml').stat().st_size:,} bytes")
    print(f"  robots.txt: {(HERE / 'robots.txt').stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
