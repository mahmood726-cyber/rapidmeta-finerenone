"""Hard-remove + de-index a list of non-poolable apps.

Given a JSON list of app filenames (e.g. outputs/single_trial_remove.json),
this:
  1. deletes each *.html file
  2. removes its <a ... class="card"> entry from index.html
  3. removes its <url>..</url> block from sitemap.xml
  4. prunes its entry from outputs/extraction_audit/fabrication_risk_scores.json
     (so the index trust-tier counts recompute correctly)

--dry-run reports what would change and writes nothing. Idempotent: missing
files / already-absent references are counted as skips.
"""
from __future__ import annotations
import argparse, io, json, os, re, sys

if hasattr(sys.stdout, "buffer") and getattr(sys.stdout, "encoding", "").lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", required=True, help="JSON array of app filenames")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    names = json.load(io.open(os.path.join(HERE, args.list), encoding="utf-8"))
    nameset = set(names)
    stems = {n[:-5] if n.endswith(".html") else n for n in names}

    # 1. delete files
    deleted = missing = 0
    for n in names:
        p = os.path.join(HERE, n)
        if os.path.isfile(p):
            if not args.dry_run:
                os.remove(p)
            deleted += 1
        else:
            missing += 1

    # 2. index.html cards
    idx_path = os.path.join(HERE, "index.html")
    idx_removed = 0
    if os.path.isfile(idx_path):
        s = io.open(idx_path, encoding="utf-8", errors="replace").read()
        for n in names:
            pat = re.compile(r'<a\s+href="' + re.escape(n) + r'"[^>]*class="card[^"]*"[^>]*>.*?</a>\s*', re.DOTALL)
            s, k = pat.subn("", s)
            idx_removed += k
        if not args.dry_run:
            io.open(idx_path, "w", encoding="utf-8", newline="").write(s)

    # 3. sitemap.xml <url> blocks
    sm_path = os.path.join(HERE, "sitemap.xml")
    sm_removed = 0
    if os.path.isfile(sm_path):
        s = io.open(sm_path, encoding="utf-8", errors="replace").read()
        for n in names:
            pat = re.compile(r'\s*<url>\s*<loc>[^<]*' + re.escape(n) + r'</loc>.*?</url>', re.DOTALL)
            s, k = pat.subn("", s)
            sm_removed += k
        if not args.dry_run:
            io.open(sm_path, "w", encoding="utf-8", newline="").write(s)

    # 4. fabrication_risk_scores.json
    fr_path = os.path.join(HERE, "outputs", "extraction_audit", "fabrication_risk_scores.json")
    fr_removed = 0
    if os.path.isfile(fr_path):
        data = json.load(io.open(fr_path, encoding="utf-8"))
        before = len(data)
        data = [e for e in data if e.get("review") not in stems
                and (e.get("review", "") + ".html") not in nameset]
        fr_removed = before - len(data)
        if not args.dry_run:
            json.dump(data, io.open(fr_path, "w", encoding="utf-8"), indent=1, ensure_ascii=False)

    print(f"{'DRY-RUN' if args.dry_run else 'APPLIED'}  list={args.list}  ({len(names)} apps)")
    print(f"  files deleted        : {deleted}   (missing: {missing})")
    print(f"  index.html cards     : {idx_removed}")
    print(f"  sitemap.xml urls     : {sm_removed}")
    print(f"  fabrication entries  : {fr_removed}")


if __name__ == "__main__":
    main()
