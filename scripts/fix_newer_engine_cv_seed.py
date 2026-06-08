"""Fix the hardcoded finerenone CV outcome taxonomy in newer-engine apps.

The newer NMA engine seeds its outcome dropdown with a hardcoded CV class set
["default","ACM","CVD","ACH","RENAL","RecurrentHF"] and labels the default
outcome "CV Death or Worsening HF". On a non-CV topic (pediatric AD, NSCLC,
ALS, ...) that shows phantom 0-count CV outcomes and a wrong default label,
even though the real outcomes (EASI75/PFS/OS/...) are correctly in realData.

Fix:
  - seed -> ["default"] for ALL such apps (safe: genuinely-CV apps re-add their
    classes from realData via the populateOutcomeSelector loop; non-CV apps
    lose only the phantom entries)
  - on NON-CV apps only (no CV-class shortLabel in realData), genericize the
    CV default label + narrative so the default isn't labeled "CV Death or
    Worsening HF"

Idempotent, --dry-run, jscheck-gated auto-revert.
"""
from __future__ import annotations
import argparse, glob, io, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SEED = '"default","ACM","CVD","ACH","RENAL","RecurrentHF"'
SEED_FIXED = '"default"'
# Precise CV-default strings to genericize on non-CV apps (dropdown label map,
# narrative composite text, bare narrative label map, and the static <option>).
NONCV_REPLACE = [
    ('default:"CV Death or Worsening HF (default)"', 'default:"Primary outcome (default)"'),
    ('default:"the primary composite endpoint (cardiovascular death or worsening heart failure)"',
     'default:"the trial-registered primary outcome"'),
    ('default:"CV Death or Worsening HF"', 'default:"Primary outcome"'),
    ('<option value="default">CV Death or Worsening HF (default)</option>',
     '<option value="default">Primary outcome (default)</option>'),
]

CV_CLASSES = {"ACM", "CVD", "ACH", "RENAL", "RecurrentHF"}


def is_cv_app(html):
    sls = set(re.findall(r'\{shortLabel:"([^"]+)",title:"', html))
    return bool(sls & CV_CLASSES)


def process(html):
    if "_outcomeAvailabilityCount(" not in html or SEED not in html:
        return html, "not-target"
    new = html.replace(SEED, SEED_FIXED)
    tag = "seed"
    if not is_cv_app(new):
        n = 0
        for old, repl in NONCV_REPLACE:
            if old in new:
                new = new.replace(old, repl)
                n += 1
        tag += f"+delabel{n}"
    else:
        tag += "(cv-keep-labels)"
    if new == html:
        return html, "no-change"
    return new, tag


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--glob", default="*_REVIEW.html")
    args = ap.parse_args()
    try:
        import jscheck
    except Exception:
        jscheck = None
    from collections import Counter
    tags = Counter()
    done = reverted = 0
    for f in sorted(glob.glob(os.path.join(HERE, args.glob))):
        if "_AUTO" in os.path.basename(f):
            continue
        html = io.open(f, encoding="utf-8", errors="replace").read()
        new, tag = process(html)
        if tag in ("not-target", "no-change"):
            continue
        tags[tag] += 1
        if args.dry_run:
            done += 1
            continue
        io.open(f, "w", encoding="utf-8", newline="").write(new)
        if jscheck is not None and jscheck.check(f):
            io.open(f, "w", encoding="utf-8", newline="").write(html)
            reverted += 1
            continue
        done += 1
    print(f"{'DRY-RUN' if args.dry_run else 'APPLIED'}  fixed={done} reverted={reverted}")
    print("tags:", dict(tags))


if __name__ == "__main__":
    main()
