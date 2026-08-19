"""WHY sglt2-hf's STORED CASCADE DOES NOT REPRODUCE -- measured across three revisions.

The re-gate run found four of five gated topics moving under the repaired classifier. Four of
them also REPRODUCED their stored numbers exactly under the classifier as it stood immediately
before the repair. `sglt2-hf` did not:

    stored on the object   k3 46   k4 2   k5 8   kNA 0
    recomputed at 7a08bcbe1 (pre-repair)   k3 48   k4 2   k5 6   kNA 0

Two trials' worth of disagreement that the repair cannot explain, because the repair had not
happened yet at that revision. So either the stored numbers were produced by an EARLIER
classifier and never re-run, or the registry records changed under a constant k0.

THIS FILE DECIDES BETWEEN THOSE TWO, and it decides by loading each revision from git rather
than by argument. `ssot/topic_identity.py` was touched by exactly these commits, newest last:

    e6c08d3be  bcce1602a  92d84da72  b65d892de  f2bf16022  c5b98b329  e20f94068

`sglt2-hf`'s own k_cascade records `restated_2026_08_19_placebo_discriminator: k3 36 -> 46`,
which is the f2bf16022 rule. If the stored 46 reproduces at f2bf16022 and not after, the
answer is "restated once and never re-run", and the missing re-run is c5b98b329 -- the
LEADING-anchor placebo fix, which shipped on the same night and was never carried back to a
page that had already been gated.
"""
import importlib.util
import json
import os
import subprocess
import sys

REPO = "F:/rapidmeta-ssot-shell"
sys.path.insert(0, REPO + "/ssot")
os.environ.setdefault(
    "RM_CTGOV_CACHE",
    "F:/claude-temp/claude/F--rapidmeta-ssot-shell/"
    "eb4d84e5-8a24-4c3b-afe2-34bd91c20bc7/scratchpad/.ctgov-raw-cache")

import ctgov_transport as X          # noqa: E402

SCRATCH = ("F:/claude-temp/claude/F--rapidmeta-ssot-shell/"
           "6b629e1e-cc8c-4565-af03-e40341ee43f3/scratchpad")

REVISIONS = [
    ("b65d892de", "reframe(locate): what was randomised"),
    ("f2bf16022", "placebo-discriminator -- the rule sglt2-hf's own restatement cites"),
    ("c5b98b329", "E1 LEADING anchor: 'Placebo (for alirocumab)'"),
    ("e20f94068", "E1 TRAILING anchor: 'Apixaban-matching placebo'  == HEAD for this file"),
]

STORED = {"k3_experimental": 46, "k4_comparator": 2, "k5_background": 8,
          "kNA_not_assessable": 0}


def load_rev(rev):
    src = subprocess.run(["git", "-C", REPO, "show", f"{rev}:ssot/topic_identity.py"],
                         capture_output=True, check=True).stdout.decode("utf-8", "replace")
    os.makedirs(SCRATCH, exist_ok=True)
    path = os.path.join(SCRATCH, f"ti_{rev}.py")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(src)
    spec = importlib.util.spec_from_file_location(f"ti_{rev}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    ids = sorted(set(json.load(open(
        os.path.join(SCRATCH, "regate_cascade_2026_08_19.json"),
        encoding="utf-8"))["sglt2-hf"]["included_in_object"]))
    # The surfaced set, not just the included set -- reread from the same run.
    run = json.load(open(os.path.join(SCRATCH, "regate_cascade_2026_08_19.json"),
                         encoding="utf-8"))["sglt2-hf"]
    surfaced = sorted(set(list(run["changed"]) + run["included_in_object"]))
    # `changed` only holds movers; re-execute the recorded query for the full set instead.
    sys.path.insert(0, REPO + "/scripts")
    import regate_cascade_2026_08_19 as R          # noqa: E402
    state, all_ids, detail = R.raw_search(R.TOPICS["sglt2-hf"]["raw_expr"])
    all_ids = sorted(set(all_ids))
    print(f"surfaced set re-executed: {state} -- {detail}")
    if state != X.OK:
        print("REFUSING: the surfaced set is incomplete, so every k below would be a floor.")
        return 1

    payloads = {}
    for nct in all_ids:
        st, study, det = X.fetch_raw(nct)
        if st != X.OK:
            print(f"  UNREACHABLE {nct}: {st} {det} -- never read, not a verdict")
            continue
        payloads[nct] = X.require_raw_v2(study, nct)

    print(f"\n{'revision':<12}{'k3':>5}{'k4':>5}{'k5':>5}{'kNA':>5}   "
          f"reproduces the stored 46/2/8/0?")
    per_rev = {}
    for rev, why in REVISIONS:
        mod = load_rev(rev)
        syns = mod.synonyms_for("sglt2 inhibitors")
        roles = {n: mod.locate(p, syns)[0] for n, p in payloads.items()}
        per_rev[rev] = roles
        t = {"k3_experimental": sum(1 for r in roles.values() if r == mod.EXPERIMENTAL),
             "k4_comparator": sum(1 for r in roles.values() if r == mod.COMPARATOR),
             "k5_background": sum(1 for r in roles.values() if r == mod.BACKGROUND),
             "kNA_not_assessable": sum(1 for r in roles.values() if r == mod.NOT_ASSESSABLE)}
        same = all(t[k] == STORED[k] for k in STORED)
        print(f"{rev:<12}{t['k3_experimental']:>5}{t['k4_comparator']:>5}"
              f"{t['k5_background']:>5}{t['kNA_not_assessable']:>5}   "
              f"{'YES -- this is the revision the page was built to' if same else 'no'}")
        print(f"            {why}")

    print("\nPER-TRIAL MOVEMENT between consecutive revisions:")
    for (a, _), (b, _) in zip(REVISIONS, REVISIONS[1:]):
        moved = {n: (per_rev[a][n], per_rev[b][n]) for n in per_rev[a]
                 if per_rev[a][n] != per_rev[b][n]}
        print(f"  {a} -> {b}: {len(moved)} moved")
        for n, (x, y) in sorted(moved.items()):
            flag = "  *** INCLUDED IN THE OBJECT ***" if n in ids else ""
            print(f"      {n}  {x} -> {y}{flag}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
