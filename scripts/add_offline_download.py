"""Inject the offline-download button (scripts/offline_bundle_snippet.html) before
</body> and extend connect-src so the bundler's fetches to cdn.plot.ly / cdnjs are
not CSP-blocked. Idempotent (skips files already carrying the marker), jscheck-gated.

Usage:
  python scripts/add_offline_download.py --files FINERENONE_REVIEW.html   # one app
  python scripts/add_offline_download.py --keep                            # validated tier
  python scripts/add_offline_download.py --all                             # every app
  add --dry-run to preview.
"""
import re, glob, io, sys, os, json, subprocess, argparse
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SNIPPET = open(os.path.join(REPO, "scripts", "offline_bundle_snippet.html"), encoding="utf-8").read().strip()
MARKER = "rm-offline-download:begin"
CDN_HOSTS = "https://cdn.plot.ly https://cdnjs.cloudflare.com"


def jscheck(fn):
    r = subprocess.run([sys.executable, os.path.join(REPO, "scripts", "jscheck.py"), fn],
                       capture_output=True, text=True)
    return "[JS-OK]" in (r.stdout + r.stderr)


def extend_connect_src(html):
    """Add the CDN hosts to connect-src if a CSP exists and they're absent."""
    m = re.search(r'(connect-src\s+)([^;"]*)', html)
    if not m:
        return html
    existing = m.group(2)
    add = " ".join(h for h in CDN_HOSTS.split() if h not in existing)
    if not add:
        return html
    return html[:m.start(2)] + existing.rstrip() + " " + add + html[m.end(2):]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--files", nargs="*")
    ap.add_argument("--keep", action="store_true")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if args.files:
        targets = args.files
    elif args.keep:
        part = json.load(open(os.path.join(REPO, "outputs", "corpus_partition.json"), encoding="utf-8"))
        targets = [n + "_REVIEW.html" for n in part["tiers"]["BENCHMARK"] + part["tiers"]["PROVENANCE"]]
    elif args.all:
        targets = [os.path.basename(p) for p in glob.glob(os.path.join(REPO, "*_REVIEW.html"))]
    else:
        ap.error("choose --files / --keep / --all")

    done = skip = reverts = 0
    for fn in sorted(set(targets)):
        p = os.path.join(REPO, fn)
        if not os.path.exists(p):
            continue
        html = open(p, encoding="utf-8", errors="replace").read()
        if MARKER in html:
            skip += 1; continue
        # Extend connect-src FIRST (it inserts text earlier in the doc, shifting
        # later offsets), THEN locate the LAST </body> in the resulting string.
        # Computing the offset before the edit lands the splice ~48 chars early,
        # mid-content. Inject before the LAST </body> (the real document close):
        # apps embed printable HTML templates (new Blob(['<html>...</body>...']))
        # whose in-string </body> would otherwise be matched first.
        new = extend_connect_src(html)
        matches = list(re.finditer(r"</body\s*>", new, re.IGNORECASE))
        if not matches:
            skip += 1; continue
        pos = matches[-1].start()
        new = new[:pos] + "\n" + SNIPPET + "\n" + new[pos:]
        if args.dry_run:
            done += 1; continue
        open(p, "w", encoding="utf-8").write(new)
        if not jscheck(p):
            open(p, "w", encoding="utf-8").write(html); reverts += 1
            print(f"  REVERTED {fn}"); continue
        done += 1
    print(f"{'DRY-RUN ' if args.dry_run else ''}injected: {done}, already-present: {skip}, reverts: {reverts}")


if __name__ == "__main__":
    main()
