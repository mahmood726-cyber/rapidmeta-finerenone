#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""Stage the full-corpus before/after render workspace for the W4-W6 gate.

BEFORE = the page as `origin/main` has it, i.e. pre-W4. AFTER = the page as it stands on
the branch, post-W6. One pass over the union of the three waves rather than three passes,
for the reason in run_wave_num.py's docstring: the render is the instrument that RECORDS
the runtime change, not a per-page accept/reject gate, and one pass attributes a change
to the union exactly as well as three passes attribute it to each wave.

BOTH SIDES GET THE FULL SIBLING ENVIRONMENT. A dir holding only the page plus vendor/
and assets/ is not the page's environment: the corpus also loads root-level siblings
(the Tailwind CSS, effect-measure-toggle.js, stats-ext.js, grade-indirectness-ext.js,
webr-validator.js, rapidmeta-auth.js). Rendering without them changes load timing and,
for effect-measure-toggle.js, can change the resolved effect measure -- which shows up
later as "nondeterminism" and costs a Stage-0 cycle to track down.

    python stage_render_full.py --out DIR [--limit N] [--seed 7]
"""
from __future__ import annotations

import argparse
import pathlib
import random
import shutil
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import corpus_wave as W                                        # noqa: E402
import corpus_detectors as CD                                  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = HERE.parent.parent


def env(d: pathlib.Path):
    d.mkdir(parents=True, exist_ok=True)
    for sub in ("vendor", "assets"):
        if (ROOT / sub).exists() and not (d / sub).exists():
            shutil.copytree(ROOT / sub, d / sub)
    for pat in ("*.js", "*.css"):
        for f in ROOT.glob(pat):
            t = d / f.name
            if not t.exists():
                shutil.copy2(f, t)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--ref", default="origin/main")
    ap.add_argument("--limit", type=int, default=0, help="0 = every eligible page")
    ap.add_argument("--seed", type=int, default=7)
    a = ap.parse_args()

    out = pathlib.Path(a.out)
    before, after = out / "before", out / "after"
    env(before)
    env(after)

    names = []
    for p in sorted(ROOT.glob("*.html")):
        if W.is_excluded(p.name):
            continue
        s = p.read_text(encoding="utf-8", errors="replace")
        if CD.is_template_page(s):
            names.append(p.name)

    if a.limit and a.limit < len(names):
        # Stratified by lineage, so a sample cannot accidentally be all one generation:
        # the two differ in which anchors they received on every one of the three waves.
        gen1 = [n for n in names
                if "isHRMode" in (ROOT / n).read_text(encoding="utf-8", errors="replace")]
        gen2 = [n for n in names if n not in set(gen1)]
        rnd = random.Random(a.seed)
        k1 = max(1, round(a.limit * len(gen1) / len(names)))
        names = sorted(rnd.sample(gen1, min(k1, len(gen1)))
                       + rnd.sample(gen2, min(a.limit - k1, len(gen2))))
        print(f"stratified sample: {len(names)} pages "
              f"({k1} from the isHRMode lineage)")

    missing = 0
    for i, n in enumerate(names, 1):
        r = subprocess.run(["git", "show", f"{a.ref}:{n}"], cwd=str(ROOT),
                           capture_output=True)
        if r.returncode != 0:
            # A page that does not exist on the ref has no pre-wave baseline. Skipping
            # it is correct -- there is nothing to compare -- but it must be counted,
            # not silently dropped, or the render pass reports a coverage it lacks.
            missing += 1
            continue
        (before / n).write_bytes(r.stdout)
        shutil.copy2(ROOT / n, after / n)
        if i % 200 == 0:
            print(f"  staged {i}/{len(names)}")

    staged = len(list(after.glob("*.html")))
    print(f"\nstaged {staged} page pairs")
    print(f"  no baseline on {a.ref}: {missing}")
    print(f"  before: {before}")
    print(f"  after : {after}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
