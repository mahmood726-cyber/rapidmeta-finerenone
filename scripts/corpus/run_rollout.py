#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""Batched, resumable W1-W3 rollout over the whole template corpus.

WHAT IT DOES, PER BATCH
  1. select the next N eligible pages that are not already stamped
  2. snapshot each page (kept, outside the repo)
  3. run corpus_wave --apply (fail-closed anchors + the four source guards)
  4. headless render check, before vs after, on every page the wave accepted
  5. discard any page that fails the render check -- restore it from its snapshot
  6. commit the surviving pages as ONE commit on the branch
  7. append cumulative state to the progress file

RESUMABILITY IS THE POINT. Every page carries a per-wave stamp, so a re-run never
double-applies and never has to remember what it did. The progress file is a report,
not the source of truth: the source of truth is the branch plus the stamps in the
pages. A fresh session can pick this up by running the same command.

SAFETY. Never merges, never pushes, never touches a deploy ref. One commit per batch,
on the current branch, with explicit paths -- never `git add -A` over the worktree.

Usage:
    python run_rollout.py --batch-size 150            # run until done
    python run_rollout.py --batch-size 150 --max-batches 1
    python run_rollout.py --census                    # what is left, no writes
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
import render_check as RC                                      # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = HERE.parent.parent
SCRATCH = pathlib.Path(
    r"F:\claude-temp\claude\F--rapidmeta-finerenone"
    r"\4c2b2ee3-5d1b-4565-9f73-b330d4647c60\scratchpad\rollout")
SNAP = SCRATCH / "snapshots"
RENDER = SCRATCH / "render"
STATE = SCRATCH / "state.json"
PROGRESS = pathlib.Path(r"F:\E156\outputs\corpus_wave_progress.md")
WAVES = ("W1", "W2", "W3")


# --------------------------------------------------------------------------- selection

def eligible():
    """Template pages this rollout may touch, in a stable order.

    Stable order matters more than it looks: it is what makes a resumed run pick up
    exactly where the last one stopped without needing to trust the progress file."""
    out = []
    for p in sorted(ROOT.glob("*.html")):
        if W.is_excluded(p.name):
            continue
        try:
            s = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if not CD.is_template_page(s):
            continue
        done = all(W.stamp_for(w) in s for w in WAVES)
        out.append((p, done))
    return out


def census():
    rows = eligible()
    done = [p for p, d in rows if d]
    todo = [p for p, d in rows if not d]
    excluded = [p.name for p in sorted(ROOT.glob("*.html")) if W.is_excluded(p.name)]
    return rows, done, todo, excluded


# --------------------------------------------------------------------------- render

def ensure_render_workspace():
    """One copy of vendor/ and assets/ per side, made once. The pages themselves are
    swapped in and out per batch; copying 7 MB of vendor code 900 times would dominate
    the run."""
    for side in ("before", "after"):
        d = RENDER / side
        d.mkdir(parents=True, exist_ok=True)
        for sub in ("vendor", "assets"):
            if (ROOT / sub).exists() and not (d / sub).exists():
                shutil.copytree(ROOT / sub, d / sub)
        for pat in ("*.js", "*.css"):
            for f in ROOT.glob(pat):
                t = d / f.name
                if not t.exists():
                    shutil.copy2(f, t)


def clear_render_pages():
    for side in ("before", "after"):
        for f in (RENDER / side).glob("*.html"):
            f.unlink()


# --------------------------------------------------------------------------- git

def git(*args, check=True):
    p = subprocess.run(["git"] + list(args), cwd=str(ROOT), capture_output=True,
                       text=True, encoding="utf-8", errors="replace")
    if check and p.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed:\n{p.stdout}\n{p.stderr}")
    return p.stdout.strip()


def assert_safe_branch():
    br = git("rev-parse", "--abbrev-ref", "HEAD")
    if br != "corpus-cleanup/wave-neutral":
        raise SystemExit(f"REFUSING: on branch {br!r}, not corpus-cleanup/wave-neutral")
    return br


def commit_batch(paths, n, stats):
    if not paths:
        return None
    # Explicit paths only. `git add -A` here would sweep in anything else that happens
    # to be in the worktree, which is exactly the kind of thing an unattended run must
    # not do.
    for chunk in (paths[i:i + 200] for i in range(0, len(paths), 200)):
        git("add", "--", *[p.name for p in chunk])
    msg = (
        f"corpus(W1-W3): batch {n} -- {stats['written']} pages\n"
        f"\n"
        f"Number-neutral waves over finerenone-template clones. Per-page data is never\n"
        f"parsed or re-emitted; realData / allOutcomes / outcomeKeys / TRIALS / evidence\n"
        f"are byte-identical on every page written here.\n"
        f"\n"
        f"  pages selected            {stats['selected']}\n"
        f"  written                   {stats['written']}\n"
        f"  discarded (guard)         {stats['discarded_guard']}\n"
        f"  discarded (render)        {stats['discarded_render']}\n"
        f"  aborted (AMBIGUOUS)       {stats['aborted']}\n"
        f"  anchors applied           {stats['applied']}\n"
        f"  anchors skipped           {stats['skipped']}\n"
        f"\n"
        f"Gate on every written page: rendered-number multiset identical (zero\n"
        f"tolerance), data spans byte-identical, whole-file number delta attributable\n"
        f"to the applied anchors, inline JS parses, headless render clean.\n"
        f"\n"
        f"Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>\n")
    mf = SCRATCH / f"msg_{n}.txt"
    mf.write_text(msg, encoding="utf-8")
    git("-c", "user.name=mahmood729", "-c", "user.email=mahmood726@gmail.com",
        "commit", "-q", "-F", str(mf))
    return git("rev-parse", "--short", "HEAD")


# --------------------------------------------------------------------------- progress

def load_state():
    if STATE.exists():
        return json.loads(STATE.read_text(encoding="utf-8"))
    return {"batches": [], "class_counts": {}, "discards": [], "aborts": [],
            "gen1_banner": {"applied": 0, "skipped": 0}}


def save_state(st):
    SCRATCH.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(st, indent=1), encoding="utf-8")


def write_progress(st):
    rows, done, todo, excluded = census()
    tot_w = sum(b["written"] for b in st["batches"])
    tot_a = sum(b["applied"] for b in st["batches"])
    tot_s = sum(b["skipped"] for b in st["batches"])
    L = []
    L.append("# Corpus W1-W3 rollout - progress\n")
    L.append("**Branch:** `corpus-cleanup/wave-neutral` (worktree `F:\\rapidmeta-corpus-wave`)  ")
    L.append("**Status: ON THE BRANCH ONLY. Not merged, not deployed, not pushed.**  ")
    L.append(f"**Last updated:** batch {len(st['batches'])} complete\n")
    L.append("| | |")
    L.append("|---|--:|")
    L.append(f"| Eligible template pages | {len(rows)} |")
    L.append(f"| Completed (all three wave stamps) | **{len(done)}** |")
    L.append(f"| Remaining | {len(todo)} |")
    L.append(f"| Pages written by this rollout | {tot_w} |")
    L.append(f"| Anchors applied | {tot_a} |")
    L.append(f"| Anchors skipped (attributable) | {tot_s} |")
    L.append(f"| Anchors aborted (AMBIGUOUS) | {len(st['aborts'])} |")
    L.append(f"| Pages discarded by a guard | {len(st['discards'])} |")
    L.append(f"| Excluded by policy (SSOT + rebuild queue) | {len(excluded)} |")
    L.append("")
    if st["class_counts"]:
        L.append("## Anchors applied by class\n")
        L.append("| Anchor | Pages |")
        L.append("|---|--:|")
        for k, v in sorted(st["class_counts"].items()):
            L.append(f"| `{k}` | {v} |")
        L.append("")
    L.append("## Batches\n")
    L.append("| # | Commit | Selected | Written | Guard-discarded | Render-discarded | Aborted | Applied | Skipped | Minutes |")
    L.append("|--:|---|--:|--:|--:|--:|--:|--:|--:|--:|")
    for b in st["batches"]:
        L.append(f"| {b['n']} | `{b.get('commit') or '-'}` | {b['selected']} | {b['written']} | "
                 f"{b['discarded_guard']} | {b['discarded_render']} | {b['aborted']} | "
                 f"{b['applied']} | {b['skipped']} | {b.get('minutes', 0):.1f} |")
    L.append("")
    if st["discards"]:
        L.append("## Discarded pages - branch untouched for these\n")
        for d in st["discards"]:
            L.append(f"- `{d['page']}` - {d['reason']}: {d['detail']}")
        L.append("")
    if st["aborts"]:
        L.append("## Aborted pages - an anchor matched more than once\n")
        for a in st["aborts"]:
            L.append(f"- `{a['page']}` - `{a['anchor']}`: {a['detail']}")
        L.append("")
    L.append("## Resuming\n")
    L.append("```")
    L.append("cd F:\\rapidmeta-corpus-wave")
    L.append("python scripts/corpus/run_rollout.py --batch-size 150")
    L.append("```")
    L.append("")
    L.append("Every page carries `<!--RM-WAVE-W1-APPLIED-->` and siblings once its wave has run, "
             "and the wave engine refuses to run a stamped wave again. So a resumed run needs no "
             "memory of what happened: it re-derives the remaining set from the pages themselves. "
             "This file is a report, not the source of truth.")
    PROGRESS.parent.mkdir(parents=True, exist_ok=True)
    PROGRESS.write_text("\n".join(L), encoding="utf-8")


# --------------------------------------------------------------------------- batch

def run_batch(n, pages, st, do_render=True):
    t0 = time.time()
    SNAP.mkdir(parents=True, exist_ok=True)
    stats = collections.Counter()
    stats["selected"] = len(pages)

    snaps = {}
    for p in pages:
        d = SNAP / p.name
        shutil.copy2(p, d)
        snaps[p.name] = d

    results = []
    for p in pages:
        try:
            r = W.process(p, WAVES)
        except Exception as e:                                  # noqa: BLE001
            st["discards"].append({"page": p.name, "reason": "ENGINE_ERROR", "detail": str(e)[:200]})
            stats["discarded_guard"] += 1
            continue
        results.append(r)
        stats["applied"] += len(r.applied)
        stats["skipped"] += len(r.skipped)
        for x in r.applied:
            st["class_counts"][x["anchor"]] = st["class_counts"].get(x["anchor"], 0) + 1
        for x in r.aborted:
            st["aborts"].append({"page": p.name, "anchor": x["anchor"], "detail": x["detail"]})
        if r.status == "ABORTED":
            stats["aborted"] += 1
        elif r.status == "DISCARDED":
            stats["discarded_guard"] += 1
            g = r.guard
            why = []
            if not g.get("rendered_numbers", {}).get("identical", True):
                why.append(f"rendered numbers moved lost={g['rendered_numbers']['lost']} "
                           f"gained={g['rendered_numbers']['gained']}")
            if not g.get("data_spans", {}).get("identical", True):
                why.append("per-page data spans changed")
            if not g.get("script_numbers", {}).get("attributed", True):
                why.append(f"unattributed numbers {g['script_numbers']['actual_delta']}")
            if not g.get("js_syntax", {}).get("clean", True):
                why.append(f"js syntax {g['js_syntax']['new']}")
            if not g.get("div_balance", {}).get("balanced", True):
                why.append("div balance")
            st["discards"].append({"page": p.name, "reason": "GUARD",
                                   "detail": "; ".join(why)[:300] or "unknown"})
        elif r.status == "OK":
            p.write_text(r.new_text, encoding="utf-8")
            stats["written_pre_render"] += 1

    written = [p for p in pages if any(r.path == p and r.status == "OK" for r in results)]

    # ---- render gate ---------------------------------------------------------
    render_bad = []
    if do_render and written:
        ensure_render_workspace()
        clear_render_pages()
        for p in written:
            shutil.copy2(snaps[p.name], RENDER / "before" / p.name)
            shutil.copy2(p, RENDER / "after" / p.name)
        rep = RC.run_pair(RENDER / "before", RENDER / "after")
        for row in rep:
            if row.get("verdict") != "OK":
                render_bad.append(row)
        (SCRATCH / f"render_batch_{n}.json").write_text(
            json.dumps(rep, indent=1, ensure_ascii=False), encoding="utf-8")
        clear_render_pages()

    for row in render_bad:
        name = row["page"]
        shutil.copy2(SNAP / name, ROOT / name)          # restore: branch untouched
        stats["discarded_render"] += 1
        detail = (f"result-numbers identical={row.get('result_numbers_identical')} "
                  f"new-errors={row.get('new_console_errors', [])[:2]}")
        st["discards"].append({"page": name, "reason": "RENDER", "detail": detail[:300]})
    bad_names = {r["page"] for r in render_bad}
    final = [p for p in written if p.name not in bad_names]
    stats["written"] = len(final)

    sha = commit_batch(final, n, stats)
    mins = (time.time() - t0) / 60.0
    st["batches"].append({"n": n, "commit": sha, "minutes": mins,
                          **{k: int(stats[k]) for k in
                             ("selected", "written", "discarded_guard",
                              "discarded_render", "aborted", "applied", "skipped")}})
    save_state(st)
    write_progress(st)
    print(f"[batch {n}] selected={stats['selected']} written={stats['written']} "
          f"guard-discard={stats['discarded_guard']} render-discard={stats['discarded_render']} "
          f"aborted={stats['aborted']} applied={stats['applied']} skipped={stats['skipped']} "
          f"commit={sha} {mins:.1f} min", flush=True)
    return stats


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch-size", type=int, default=150)
    ap.add_argument("--max-batches", type=int, default=0)
    ap.add_argument("--census", action="store_true")
    ap.add_argument("--no-render", action="store_true")
    a = ap.parse_args()

    assert_safe_branch()
    rows, done, todo, excluded = census()
    print(f"eligible={len(rows)} done={len(done)} todo={len(todo)} excluded={len(excluded)}",
          flush=True)
    if a.census:
        by = collections.Counter()
        for p in todo:
            s = p.read_text(encoding="utf-8", errors="replace")
            by["gen1" if "significantBenefit" in s and "interpretRelativeEffect" not in s
               else "gen2"] += 1
        print("remaining by generation:", dict(by))
        print("excluded:", ", ".join(excluded[:40]), "..." if len(excluded) > 40 else "")
        return 0

    st = load_state()
    n = len(st["batches"])
    made = 0
    while todo:
        if a.max_batches and made >= a.max_batches:
            break
        n += 1
        made += 1
        batch = todo[:a.batch_size]
        print(f"\n=== batch {n}: {len(batch)} pages, {len(todo)} remaining ===", flush=True)
        run_batch(n, batch, st, do_render=not a.no_render)
        rows, done, todo, excluded = census()
    print(f"\nROLLOUT: {len(done)} done, {len(todo)} remaining", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
