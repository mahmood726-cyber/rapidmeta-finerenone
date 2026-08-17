#!/usr/bin/env python
"""HARNESS GATE -- runs the artefact-decidable detectors and blocks the push.

Install as `scripts/harness_gate.py` in the corpus repo and add the block in
HANDOFF_CORPUS_LANE.md Sec 3a to `.githooks/pre-push`. This file does not edit
the hook; the corpus lane holds it.

  exit 0   every artefact-decidable check PASSed or was NOT APPLICABLE
  exit 1   at least one FAIL -- a real defect, push blocked
  exit 2   the registry is unfit, or the INVALID share is above the ceiling.
           NOT a pass. A gate that cannot see must not wave things through.

WHY THIS EXITS 2 RATHER THAN 0 ON AN UNFIT REGISTRY
    Because `regression_check.py` "contained no sys.exit at all... it exited 0
    whatever it found", and the hook it lived under read `$?` from a pipe. Both
    layers had to be repaired. This file is the second layer for the harness, and
    the first thing it does is prove it can return non-zero.

WHAT A FULL PASS DOES NOT ESTABLISH -- written in advance, per gate_integrity.py
    - NOT that the page is correct. Twenty of thirty detectors run here; ten are
      RETRIEVAL_SCOPED and cannot run against a static artefact. They are listed
      by name in the output every run, so silence is never mistaken for coverage.
    - NOT that the artefact adapter extracted everything. A field absent from the
      artefact yields NOT APPLICABLE, which is not a clean result.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from nafis_harness import Verdict, build_registry            # noqa: E402
from nafis_harness.artefact import (ARTEFACT_DECIDABLE,      # noqa: E402
                                    RETRIEVAL_SCOPED, payloads_for)


def run_artefact(reg, artefact: dict) -> list:
    results = []
    for check_id, payload in payloads_for(artefact):
        if check_id not in ARTEFACT_DECIDABLE:
            continue
        results.append((check_id, payload, reg.run(check_id, payload)))
    return results


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="harness_gate")
    ap.add_argument("artefacts", nargs="*",
                    help="JSON files, each one build artefact")
    ap.add_argument("--invalid-ceiling", type=float, default=0.5)
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)

    reg = build_registry()
    fitness = reg.self_test()
    if not fitness["ok"]:
        print("[harness-gate] REGISTRY UNFIT: " + ", ".join(fitness["unfit"]),
              file=sys.stderr)
        print("[harness-gate] Refusing to report a result from a registry whose "
              "own controls misbehave.", file=sys.stderr)
        return 2

    if not args.artefacts:
        print("[harness-gate] No artefacts given; nothing to check. This is a "
              "scoped pass, not a clean bill.")
        return 0

    fails, invalids, passes, n_files = [], [], 0, 0
    for path in args.artefacts:
        if not os.path.exists(path):
            print(f"[harness-gate] artefact not found: {path}", file=sys.stderr)
            return 2
        with open(path, encoding="utf-8") as fh:
            art = json.load(fh)
        n_files += 1
        for check_id, payload, r in run_artefact(reg, art):
            if r.verdict is Verdict.FAIL:
                fails.append((path, check_id, r))
            elif r.verdict is Verdict.INVALID:
                invalids.append((path, check_id, r))
            else:
                passes += 1

    total = passes + len(fails) + len(invalids)

    # ZERO EXECUTIONS IS NOT A PASS (corpus lane, 2026-08-17).
    #
    # Before the exporter existed this gate was handed real SSOT objects, matched
    # NOTHING in them, and printed PASS on 0 check executions. Installed, green,
    # seeing nothing -- and `wiring.detect()` would have flipped the ledger
    # headline to ~50% while no detector ran on anything we build.
    #
    # A silently non-recognising exporter is otherwise INDISTINGUISHABLE FROM A
    # CLEAN CORPUS, which is the most dangerous state available here. The harness
    # already argues this for INVALID; "the adapter recognised nothing" is the
    # same statement one layer earlier, so it takes the same exit code.
    if n_files and total == 0:
        print("[harness-gate] %d artefact(s) yielded ZERO check executions. The "
              "adapter recognised nothing in them." % n_files, file=sys.stderr)
        print("[harness-gate] That is not a pass. Nothing was checked.",
              file=sys.stderr)
        return 2
    if not args.quiet:
        print(f"[harness-gate] {n_files} artefact(s), {total} check execution(s): "
              f"{passes} PASS, {len(fails)} FAIL, {len(invalids)} INVALID")
        print(f"[harness-gate] artefact-decidable detectors: "
              f"{len(ARTEFACT_DECIDABLE)}")
        print(f"[harness-gate] NOT RUN HERE (retrieval-scoped, {len(RETRIEVAL_SCOPED)}): "
              + ", ".join(c.split('_')[0] for c in RETRIEVAL_SCOPED))
        print("[harness-gate] Those are not covered by this gate. Silence from "
              "them is not evidence.")

    for path, check_id, r in fails:
        print(f"\n[harness-gate] FAIL {check_id}\n  artefact: {path}\n"
              f"  {r.reason}")
        if r.witness:
            print(f"  observed : {r.witness.observed}")
            print(f"  at       : {r.witness.locator}")

    # AN INVALID IS A CHECK THAT RAN AND COULD NOT SEE, AND IT WAS NAMED ONLY
    # WHEN THE CEILING WAS BREACHED. Below the ceiling the count went into the
    # summary line and nothing said WHICH detector went blind or why -- this
    # repository's own rule broken inside its own gate, since silence from a
    # detector is not evidence and a bare "2 INVALID" is silence with a number
    # on it.
    if invalids and not args.quiet:
        print("\n[harness-gate] INVALID -- ran but could not see. Not a pass:")
        for path, check_id, r in invalids:
            print(f"  {check_id} on {os.path.basename(path)}: {r.reason[:130]}")

    if total and len(invalids) / total > args.invalid_ceiling:
        print(f"\n[harness-gate] INSTRUMENT DEGRADED: {len(invalids)}/{total} "
              f"checks returned INVALID, above the "
              f"{args.invalid_ceiling:.0%} ceiling.", file=sys.stderr)
        for path, check_id, r in invalids[:5]:
            print(f"  INVALID {check_id} on {path}: {r.reason[:140]}",
                  file=sys.stderr)
        return 2

    if fails:
        print(f"\n[harness-gate] {len(fails)} defect(s). This gate has no override.")
        return 1

    print("[harness-gate] PASS.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
