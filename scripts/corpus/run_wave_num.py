#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""Batched, resumable source rollout for the number-changing waves W4-W6.

DIFFERENT FROM run_rollout.py IN ONE WAY THAT MATTERS. W1-W3 could gate every page on
a render before committing it, because nothing a reader sees was allowed to move. W4-W6
DO move what a reader sees, so the render is no longer a per-page accept/reject gate --
it is the instrument that RECORDS the change. Rendering 863 pages three times over, once
per wave, would cost most of a day and would still not attribute a runtime change to a
wave any better than one pass over the union does.

So this driver commits on the SOURCE guards, which remain exactly as strict as they were
for W1-W3 -- rendered-number multiset identical, per-page data spans byte-identical,
whole-file number delta attributed to the anchors, divs balanced, JS parses -- and the
runtime evidence is gathered afterwards by one full render pass with
`--expect-change W4,W5,W6`, whose per-page log is the deliverable.

That split is sound because every W4-W6 anchor edits code inside <script>. None of them
touches visible text, so the zero-tolerance static guard is still a real constraint on
them and still fails closed. What it cannot see -- a page that stops running -- is what
the render pass is for, and no page ships to `main` before that pass is read.

Snapshots are written outside the repo and kept, so a batch can be restored byte-for-byte.

Usage:
    python run_wave_num.py --wave W4 --batch-size 150
    python run_wave_num.py --wave W4 --census
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import shutil
import subprocess
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import corpus_wave as W                                        # noqa: E402
import corpus_detectors as CD                                  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = HERE.parent.parent
SNAP_ROOT = pathlib.Path(r"F:\rapidmeta-snapshots")
LOG_ROOT = pathlib.Path(r"F:\E156\outputs\corpus_wave_logs")


def git(*args, check=True):
    p = subprocess.run(["git"] + list(args), cwd=str(ROOT), capture_output=True,
                       text=True, encoding="utf-8", errors="replace")
    if check and p.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed:\n{p.stdout}\n{p.stderr}")
    return p.stdout.strip()


def eligible(wave):
    """Template pages this wave may touch, stable order, unstamped first.

    Stable order is what lets a resumed run pick up where the last one stopped
    without trusting any progress file: the stamps in the pages are the state.
    """
    todo, done = [], []
    for p in sorted(ROOT.glob("*.html")):
        if W.is_excluded(p.name):
            continue
        try:
            s = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if not CD.is_template_page(s):
            continue
        (done if W.stamp_for(wave) in s else todo).append(p)
    return todo, done


def run_batch(wave, pages, snap_dir):
    """Apply the wave to one batch. Returns (written, results)."""
    written, results = [], []
    for p in pages:
        snap = snap_dir / p.name
        if not snap.exists():
            shutil.copy2(p, snap)
        r = W.process(p, waves=(wave,))
        results.append(r)
        if r.status == "OK":
            p.write_text(r.new_text, encoding="utf-8")
            written.append(p)
        elif r.status in ("DISCARDED", "ABORTED"):
            # restore from snapshot, defensively: process() never writes on failure,
            # but a half-written file is the one thing that cannot be recovered from
            # a report.
            shutil.copy2(snap, p)
    return written, results


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--wave", required=True, choices=["W4", "W5", "W6"])
    ap.add_argument("--batch-size", type=int, default=150)
    ap.add_argument("--max-batches", type=int, default=0, help="0 = run to completion")
    ap.add_argument("--census", action="store_true")
    a = ap.parse_args()

    todo, done = eligible(a.wave)
    excluded = [p.name for p in sorted(ROOT.glob("*.html")) if W.is_excluded(p.name)]
    print(f"wave {a.wave}: {len(todo)} to do, {len(done)} already stamped, "
          f"{len(excluded)} excluded by policy")
    if a.census:
        return 0

    snap_dir = SNAP_ROOT / a.wave
    snap_dir.mkdir(parents=True, exist_ok=True)
    LOG_ROOT.mkdir(parents=True, exist_ok=True)

    totals = collections.Counter()
    anchor_hits = collections.Counter()
    all_rows = []
    batch_no = 0
    t0 = time.time()

    while todo:
        batch_no += 1
        if a.max_batches and batch_no > a.max_batches:
            break
        batch, todo = todo[:a.batch_size], todo[a.batch_size:]
        bt = time.time()
        written, results = run_batch(a.wave, batch, snap_dir)
        for r in results:
            totals[r.status] += 1
            for x in r.applied:
                anchor_hits[x["anchor"]] += 1
            all_rows.append(r.as_dict())

        bad = [r for r in results if r.status in ("DISCARDED", "ABORTED")]
        for r in bad:
            print(f"   !! {r.status} {r.path.name}")
            g = r.guard
            if not g.get("rendered_numbers", {}).get("identical", True):
                print(f"      numbers moved: lost={g['rendered_numbers']['lost']} "
                      f"gained={g['rendered_numbers']['gained']}")
            if not g.get("js_syntax", {}).get("clean", True):
                print(f"      js: {g['js_syntax']['new']}")
            for x in r.aborted:
                print(f"      {x['anchor']}: {x['detail'][:100]}")

        if written:
            git("add", "--", *[str(p.relative_to(ROOT)) for p in written])
            git("commit", "-q", "-m",
                f"corpus({a.wave}): batch {batch_no} -- {len(written)} pages\n\n"
                f"Applied on the source guards (rendered-number multiset identical, "
                f"data spans byte-identical, whole-file number delta attributed to the "
                f"anchors, divs balanced, JS parses). Runtime evidence is gathered by "
                f"the full render pass with --expect-change, not per page here; see "
                f"corpus_wave_logs/{a.wave}.json for the per-page anchor log.\n\n"
                f"Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>")
        print(f"  batch {batch_no}: {len(written)} written, {len(bad)} rejected, "
              f"{len(todo)} left  ({time.time()-bt:.0f}s)")

    (LOG_ROOT / f"{a.wave}.json").write_text(
        json.dumps(all_rows, indent=1, ensure_ascii=False), encoding="utf-8")

    print(f"\n{'='*66}\n{a.wave} SOURCE ROLLOUT COMPLETE  ({time.time()-t0:.0f}s)")
    for k in sorted(totals):
        print(f"  {k:14s} {totals[k]}")
    print("\n  anchors applied:")
    for k in sorted(anchor_hits):
        print(f"    {k:26s} {anchor_hits[k]}")
    print(f"\n  snapshots: {snap_dir}")
    print(f"  per-page log: {LOG_ROOT / (a.wave + '.json')}")
    return 0 if not (totals["DISCARDED"] or totals["ABORTED"]) else 1


if __name__ == "__main__":
    sys.exit(main())
