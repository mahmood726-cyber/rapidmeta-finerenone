#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Preflight for the GitHub Actions Pages build.

WHY THIS EXISTS. The site is 1,478 root HTML pages and ~1.1 GB. Two failure modes
are silent if nobody looks:

  1. A checkout that is missing `.nojekyll` -- the Pages runtime then treats the
     tree as a Jekyll source and drops every path beginning with `_`. The site
     still deploys; it is just missing files. Nothing fails.
  2. A payload that has crossed a GitHub limit. Pages documents a 1 GB published
     site limit and a 10 GB artifact ceiling. At 1.1 GB this repo is already past
     the first one, so the number has to be printed on every build rather than
     discovered when a deploy starts failing.

So this script asserts the shape of the site and prints the payload. It is run by
`.github/workflows/pages.yml` and can be run locally against a checkout:

    python scripts/pages_preflight.py --root .

It fails (exit 1) on a structurally broken site -- missing `.nojekyll`, missing
`index.html`, or a root page count below the floor -- and on a payload above the
artifact ceiling. It WARNS but does not fail above the 1 GB site limit, because the
legacy builder is serving this repo at that size today: failing here would block a
build for a limit that is not currently being enforced against us. The warning is a
GitHub annotation, so it is visible on the run without being a gate.

The exclusions mirror `actions/upload-pages-artifact`, which tars the path with
`--exclude=.git --exclude=.github`. Measuring anything else would report a number
that is not the artifact.
"""
from __future__ import annotations

import argparse
import os
import pathlib
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Mirrors actions/upload-pages-artifact's tar excludes. Anything added here also has
# to be added to the workflow, or the measured number stops being the artifact.
ARTIFACT_EXCLUDES = {".git", ".github"}

SITE_LIMIT_BYTES = 1_000_000_000       # GitHub Pages published-site limit (warn)
ARTIFACT_LIMIT_BYTES = 10_000_000_000  # Pages artifact ceiling (fail)

# A floor, not a target. The corpus is 1,478 root pages; anything under this means
# the checkout is partial (shallow clone gone wrong, LFS pointers, sparse checkout)
# and deploying it would silently 404 most of the site.
ROOT_PAGE_FLOOR = 800


def walk_artifact(root: pathlib.Path):
    """Yield every file that would land in the Pages artifact."""
    for dirpath, dirnames, filenames in os.walk(root):
        rel = pathlib.Path(dirpath).relative_to(root)
        # prune excluded top-level dirs in place so os.walk does not descend
        if rel == pathlib.Path("."):
            dirnames[:] = [d for d in dirnames if d not in ARTIFACT_EXCLUDES]
        for fn in filenames:
            yield pathlib.Path(dirpath) / fn


def annotate(level: str, msg: str) -> None:
    """Emit a GitHub Actions annotation, and a plain line when run locally."""
    if os.environ.get("GITHUB_ACTIONS") == "true":
        print(f"::{level}::{msg}")
    else:
        print(f"[{level.upper()}] {msg}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".", help="checkout root to publish")
    ap.add_argument("--page-floor", type=int, default=ROOT_PAGE_FLOOR)
    ap.add_argument("--summary", default=os.environ.get("GITHUB_STEP_SUMMARY"))
    args = ap.parse_args()

    root = pathlib.Path(args.root).resolve()
    failures: list[str] = []

    # --- shape -----------------------------------------------------------------
    nojekyll = (root / ".nojekyll").exists()
    if not nojekyll:
        failures.append(
            ".nojekyll is missing. Pages would run the Jekyll processor and drop "
            "every path starting with '_'."
        )

    index = (root / "index.html").exists()
    if not index:
        failures.append("index.html is missing from the publish root.")

    root_pages = sorted(p.name for p in root.glob("*.html"))
    if len(root_pages) < args.page_floor:
        failures.append(
            f"root page count {len(root_pages)} is below the floor {args.page_floor}. "
            "The checkout looks partial; publishing it would 404 most of the site."
        )

    # --- payload ---------------------------------------------------------------
    total = 0
    nfiles = 0
    for f in walk_artifact(root):
        try:
            total += f.stat().st_size
        except OSError:
            # a broken symlink or a file that vanished mid-walk; tar would fail on
            # it too, so surface rather than swallow
            failures.append(f"unreadable file in publish root: {f}")
            continue
        nfiles += 1

    if total > ARTIFACT_LIMIT_BYTES:
        failures.append(
            f"payload {total/1e9:.2f} GB exceeds the {ARTIFACT_LIMIT_BYTES/1e9:.0f} GB "
            "Pages artifact ceiling."
        )
    elif total > SITE_LIMIT_BYTES:
        annotate(
            "warning",
            f"publish payload is {total/1e9:.3f} GB, above the documented 1 GB "
            "GitHub Pages site limit. The legacy builder is serving this size today, "
            "so this is reported, not enforced.",
        )

    # --- report ----------------------------------------------------------------
    lines = [
        "## Pages preflight",
        "",
        "| check | value |",
        "|---|--:|",
        f"| root HTML pages | {len(root_pages)} |",
        f"| files in artifact | {nfiles} |",
        f"| payload | {total/1e6:.1f} MB ({total/1e9:.3f} GB) |",
        f"| `.nojekyll` | {'present' if nojekyll else 'MISSING'} |",
        f"| `index.html` | {'present' if index else 'MISSING'} |",
        f"| excluded from artifact | {', '.join(sorted(ARTIFACT_EXCLUDES))} |",
    ]
    report = "\n".join(lines)
    print(report)

    if args.summary:
        try:
            with open(args.summary, "a", encoding="utf-8") as fh:
                fh.write(report + "\n")
        except OSError as exc:
            print(f"(could not write step summary: {exc})")

    if failures:
        print("\nPREFLIGHT FAILED:")
        for f in failures:
            print(f"  - {f}")
            annotate("error", f)
        return 1

    print("\nPreflight OK.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
