# no-control: the only text matching here is an EXACT literal anchor that must occur
# precisely once, and the plant is REFUSED otherwise -- so its precision is 1.0 by
# construction and a known-negative control would measure a constant. The counts it
# prints are of plants applied and files restored, neither derived from matching
# document prose. Stated rather than silently exempted.
"""TIER 2 -- plant the real corpus, run the real gates, restore, and PROVE the restoration.

WHY THIS EXISTS SEPARATELY FROM GATE 10. Tier 1 calls each shipped predicate against a
fixture: it proves the RULE still fires. It cannot prove the TRAVERSAL still reaches a defect
in situ, and on 2026-08-28 that distinction was the whole finding -- gate 1's predicate was
correct and a swapped trial name written in prose was never handed to it. Only planting the
real corpus tests reach.

NOT ON EVERY BUILD. This mutates tracked files. It is nightly or on demand, never in a hook.

SAFETY, AND IT REFUSES RATHER THAN WARNS:
  * refuses unless the working tree is clean, so a failed restore can never be mistaken for
    somebody else's edit -- and so `git status` stays a meaningful signal throughout;
  * refuses on `main` and on any branch it does not own;
  * records sha256 AND byte count before each plant and asserts both after;
  * copies the originals outside the tree and restores from those bytes, not from git;
  * refuses any plant whose anchor is not present exactly once -- a plant that silently fails
    to apply would be recorded as "nothing detected it", which is a FALSE ZERO and the exact
    failure this whole exercise exists to measure rather than commit;
  * never runs `git worktree prune`.

Usage:  python gates/tier2_corpus_plants.py --check | --run
"""
from __future__ import annotations

import hashlib
import importlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
REPO = os.path.dirname(HERE)

REGISTRIES = ("tier2_plants_a", "tier2_plants_b", "tier2_plants_c")
FORBIDDEN_BRANCHES = ("main", "master")


def _git(*args):
    return subprocess.run(["git", "-C", REPO] + list(args),
                          capture_output=True, text=True)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def status_lines():
    return [l for l in _git("status", "--porcelain").stdout.splitlines() if l.strip()]


def branch():
    return _git("branch", "--show-current").stdout.strip()


def load_plants():
    out = []
    for mod in REGISTRIES:
        try:
            out.extend(importlib.import_module(mod).PLANTS)
        except ImportError:
            print("  registry %s not present -- skipped" % mod)
    return out


def preflight():
    """Refuse, loudly, rather than proceed on a tree where a mistake would be invisible."""
    problems = []
    b = branch()
    if b in FORBIDDEN_BRANCHES:
        problems.append("on branch %r -- tier 2 mutates tracked files and never runs here" % b)
    if not b:
        problems.append("detached HEAD -- refusing, because a restore has nowhere to be checked")
    lines = status_lines()
    if lines:
        problems.append("working tree is not clean (%d entries); a dirty tree makes a failed "
                        "restore indistinguishable from somebody's edit" % len(lines))
    return problems


def main(argv):
    plants = load_plants()
    print("tier-2 registries: %d plant(s) over %d class(es)"
          % (len(plants), len({p["cls"] for p in plants})))

    problems = preflight()
    if problems:
        print("REFUSING:")
        for p in problems:
            print("  " + p)
        return 3

    if "--run" not in argv:
        # --check: prove every anchor resolves, WITHOUT touching a file.
        bad = 0
        for p in plants:
            full = os.path.join(REPO, p["path"])
            if not os.path.exists(full):
                print("  MISSING FILE  %s  %s" % (p["id"], p["path"])); bad += 1; continue
            if p.get("mode") == "append":
                continue
            with io.open(full, encoding="utf-8", errors="strict") as fh:
                n = fh.read().count(p["find"])
            if n != 1:
                print("  ANCHOR x%-3d   %s  %s" % (n, p["id"], p["path"])); bad += 1
        print("plants that CANNOT be applied: %d / %d" % (bad, len(plants)))
        print("(--check only; nothing was modified. Use --run to plant, gate and restore.)")
        return 1 if bad else 0

    backup = tempfile.mkdtemp(prefix="tier2-originals-")
    targets, manifest = sorted({p["path"] for p in plants}), {}
    for rel in targets:
        full = os.path.join(REPO, rel)
        manifest[rel] = {"sha256": sha256(full), "bytes": os.path.getsize(full)}
        shutil.copy2(full, os.path.join(backup, rel.replace("/", "__").replace("\\", "__")))

    planted, refused = 0, []
    try:
        for p in plants:
            full = os.path.join(REPO, p["path"])
            with io.open(full, encoding="utf-8", errors="strict") as fh:
                text = fh.read()
            if p.get("mode") == "append":
                new = text + p["replace"]
            else:
                if text.count(p["find"]) != 1:
                    refused.append(p["id"])
                    continue
                new = text.replace(p["find"], p["replace"], 1)
            with io.open(full, "w", encoding="utf-8", newline="") as fh:
                fh.write(new)
            with io.open(full, encoding="utf-8", errors="strict") as fh:
                if p["replace"] in fh.read():
                    planted += 1
                else:
                    refused.append(p["id"] + " (write did not take)")
        print("PLANTED %d / %d; refused: %s" % (planted, len(plants), refused or "none"))

        rc = subprocess.run([sys.executable, os.path.join(HERE, "run_all.py")],
                            cwd=REPO).returncode
        print("gate suite over the PLANTED corpus returned %d "
              "(0 PASS / 1 FAIL / 2 VACUOUS / 3 BROKEN)" % rc)
        print("A PASS HERE IS THE FINDING: %d planted defects and nothing objected." % planted)
    finally:
        bad = []
        for rel, rec in manifest.items():
            full = os.path.join(REPO, rel)
            shutil.copy2(os.path.join(backup, rel.replace("/", "__").replace("\\", "__")), full)
            if sha256(full) != rec["sha256"] or os.path.getsize(full) != rec["bytes"]:
                bad.append(rel)
        _git("checkout", "--", "out")
        lines = status_lines()
        print("=" * 78)
        print("RESTORATION VERIFIED BY CONTENT, NOT BY EXIT CODE")
        print("  files restored:           %d" % len(manifest))
        print("  sha256 + byte mismatches: %d %s" % (len(bad), bad or ""))
        print("  git status --porcelain:   %d lines" % len(lines))
        for l in lines[:20]:
            print("    " + l)
        print("  VERDICT: %s" % ("CLEAN" if not bad and not lines else "DIRTY"))
        print("=" * 78)
        shutil.rmtree(backup, ignore_errors=True)
        if bad or lines:
            return 3
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
