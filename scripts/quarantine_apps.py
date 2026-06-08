"""Step 1: quarantine the clear non-meta-analyses (single-trial + genuinely empty),
EXCLUDING DTA / NMA / dose-response apps (which pool via non-pairwise methods the
partition's pairwise check under-counts -- those need manual review, not removal).

Quarantine = (a) de-index from sitemap.xml, (b) remove the card from index.html,
(c) inject an honest "NOT a validated meta-analysis" banner right after <body>,
(d) list them in a fenced auto-gallery.html. Nothing is deleted or moved; URLs
stay valid (so old links don't 404) but are de-indexed + clearly labelled.

--dry-run : print the list + counts, change nothing.
"""
import re, glob, io, sys, os, json, subprocess, argparse
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SPECIAL = re.compile(r"DTA|_NMA$|NMA|DOSE_RESP")  # non-pairwise: never auto-quarantine

BANNER = (
    '<div style="background:#7f1d1d;color:#fff;padding:10px 16px;font:600 13px/1.4 '
    'system-ui,sans-serif;text-align:center" data-quarantine-banner>'
    'AUTOMATED OUTPUT — NOT a validated meta-analysis. This page pools fewer than two '
    'trials with poolable data and has not been externally benchmarked or provenance-'
    'verified. See the validated portfolio at '
    '<a href="index.html" style="color:#fecaca;text-decoration:underline">the index</a>.'
    '</div>')


def safe_set():
    d = json.load(open(os.path.join(REPO, "outputs", "corpus_partition.json"), encoding="utf-8"))
    q = d["quarantine_reasons"]
    cand = [x for x in q["k<2"]] + [x for x in q["no_contributing_trials"] if not x.endswith("_AUTO")]
    return sorted(x for x in set(cand) if not SPECIAL.search(x))


def jscheck(fn):
    r = subprocess.run([sys.executable, os.path.join(REPO, "scripts", "jscheck.py"), fn],
                       capture_output=True, text=True)
    return "[JS-OK]" in (r.stdout + r.stderr)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    names = safe_set()
    files = [n + "_REVIEW.html" for n in names]
    files = [f for f in files if os.path.exists(os.path.join(REPO, f))]
    print(f"safe-to-quarantine: {len(files)} apps")
    if args.dry_run:
        print("sample:", files[:12]); return

    # (c) banner injection (jscheck-gated)
    banned = reverts = 0
    for f in files:
        p = os.path.join(REPO, f)
        html = open(p, encoding="utf-8", errors="replace").read()
        if "data-quarantine-banner" in html:
            continue
        m = re.search(r"<body[^>]*>", html, re.IGNORECASE)
        if not m:
            continue
        new = html[:m.end()] + BANNER + html[m.end():]
        open(p, "w", encoding="utf-8").write(new)
        if not jscheck(p):
            open(p, "w", encoding="utf-8").write(html); reverts += 1; continue
        banned += 1
    print(f"banners injected: {banned}, reverts: {reverts}")

    # (a) de-index from sitemap
    sm_path = os.path.join(REPO, "sitemap.xml")
    sm = open(sm_path, encoding="utf-8").read()
    drop = set(files)
    blocks = re.split(r"(?=<url>)", sm)
    kept = [b for b in blocks
            if not (re.search(r"/([^/<]+\.html)</loc>", b)
                    and re.search(r"/([^/<]+\.html)</loc>", b).group(1) in drop)]
    open(sm_path, "w", encoding="utf-8").write("".join(kept))
    print(f"de-indexed from sitemap: {len(blocks) - len(kept)}")

    # (b) remove cards from index.html
    idx_path = os.path.join(REPO, "index.html")
    idx = open(idx_path, encoding="utf-8").read()
    removed = 0
    for f in files:
        pat = re.compile(r'\s*<a href="' + re.escape(f) + r'"[^>]*>.*?</a>', re.DOTALL)
        idx, n = pat.subn("", idx)
        removed += n
    open(idx_path, "w", encoding="utf-8").write(idx)
    print(f"index cards removed: {removed}")

    # (d) build the fenced gallery
    items = "\n".join(
        f'  <li><a href="{f}">{f[:-len("_REVIEW.html")].replace("_"," ")}</a></li>'
        for f in sorted(files))
    gallery = (
        '<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">'
        '<meta name="robots" content="noindex">'
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">'
        '<title>Automated (unvalidated) gallery — RapidMeta</title></head><body>'
        '<h1>Automated, unvalidated outputs</h1>'
        '<p>These pages were produced by the automated pipeline and pool fewer than '
        'two trials with poolable data. They are <b>NOT validated meta-analyses</b>, '
        'are excluded from the portfolio index and sitemap, and are listed here only '
        'for transparency. For the validated portfolio see '
        '<a href="index.html">the index</a>.</p>\n<ul>\n' + items + '\n</ul></body></html>')
    open(os.path.join(REPO, "auto-gallery.html"), "w", encoding="utf-8").write(gallery)
    print(f"wrote auto-gallery.html ({len(files)} entries)")


if __name__ == "__main__":
    main()
