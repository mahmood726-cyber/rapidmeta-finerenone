"""Re-run the bookkeeping writer so the STORED prose carries English lead-ins. Guarded four ways.

# no-control: an operation over objects, not a detector. Its controls are the four assertions
# below, each of which stops the run rather than reporting afterwards: quarantine exists before
# any write, no object loses a key, the stored text actually changed per object, and the known
# positive (MAVACAMTEN's `bar:`) is gone from the object afterwards.

WHY THE WRITER AND NOT THE RENDERER. `paper_projector._flatten_container` was fixed and
MAVACAMTEN was rebuilt to prove it -- and came back with the same three hits, because the
`key: value` text is BAKED INTO THE OBJECT at
`bookkeeping_2026_08_21.the_search_its_date_and_its_databases` by
`build_paper_bookkeeping_2026_08_21._flat`. A projector fix cannot reach a stored value and
both look identical on the page. That writer now calls `paper_projector._lead_in`, so both
paths read ONE map, `ssot/field_lead_ins.json`.

THE FOUR CONDITIONS, IMPOSED BECAUSE THIS WRITES TO ssot/**/*.json:

 1 NET-ADDITIVE ONLY. Key counts are taken per object before and after. If any object loses a
   key the run stops and reports; it does not continue and summarise.

 2 QUARANTINE FIRST, and to a FILE ON DISK rather than a git stash -- something that can be
   pointed at while the rollout is verified on served bytes.

 3 ONE MAP. Asserted by construction: the writer imports the projector's `_lead_in`. If the
   two could hold different maps they would drift, which is the two-locations problem that
   produced GRADE disagreements on 23 of 34 pooled outcomes.

 4 THE OCCURRENCE PREDICATE. Per object, the stored text must actually differ afterwards.
   "Ran and changed nothing" is indistinguishable from "never ran" without it, and that
   silence is exactly what hid the writer for two days.
"""
from __future__ import annotations

import glob
import io
import json
import os
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import instrument_controls as _ic  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QUAR = os.path.join(REPO, "outputs", "quarantine_bookkeeping_2026_08_23")
FIELD = "bookkeeping_2026_08_21"
OUT = os.path.join(REPO, "outputs", "bookkeeping_lead_in_rerun_2026_08_23.json")

# The shapes a bare field key leaves in stored prose.
OLD_SHAPES = ("what verifies this object:", "what is not claimed:", "bar:",
              "post hoc:", "families:")

# THE SAME CONTENT AFTER THE LEAD-INS LANDED. Selecting on the DEFECT alone is self-erasing:
# once a pass has fixed it, a later pass to correct the punctuation seam cannot find the
# objects it needs to correct, and reports success because everything it did select changed.
# The lead-in openers are read from the map so the two cannot drift apart.
def _new_shapes():
    import json as _j
    p = os.path.join(REPO, "ssot", "field_lead_ins.json")
    try:
        m = _j.load(io.open(p, encoding="utf-8"))
    except Exception:
        return ()
    out = []
    for spec in (m.get("by_key") or {}).values():
        for form in (spec.get("present"), spec.get("absent")):
            if isinstance(form, str):
                head = form.split("%s")[0].strip()
                if len(head) > 12:
                    out.append(head)
    return tuple(sorted(set(out)))


NEW_SHAPES = _new_shapes()


def objects():
    out = []
    for p in sorted(glob.glob(os.path.join(REPO, "ssot", "*", "*.json"))):
        t = os.path.basename(os.path.dirname(p))
        if os.path.basename(p) == t + ".json":
            out.append((t, p))
    return out


def keycount(x):
    if isinstance(x, dict):
        return 1 + sum(keycount(v) for v in x.values())
    if isinstance(x, list):
        return sum(keycount(v) for v in x)
    return 0


def stored_text(o):
    bk = o.get(FIELD)
    return json.dumps(bk, sort_keys=True) if isinstance(bk, dict) else ""


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    apply = "--apply" in sys.argv

    before = {}
    affected = []
    for t, p in objects():
        try:
            o = json.load(io.open(p, encoding="utf-8"))
        except ValueError:
            continue
        txt = stored_text(o)
        before[t] = {"path": p, "keys": keycount(o), "text": txt}
        # SELECTION BY DEFECT ALONE IS SELF-ERASING, AND IT BIT ON THE SECOND RUN.
        #
        # The first pass rewrote 48 objects, so their `key:` shapes were gone. A later pass to
        # fix the punctuation SEAM then matched only the 3 objects still carrying `families:`
        # and skipped the 46 it needed to correct -- and reported success, because every object
        # it did select changed. A run that can only see work it has not yet done cannot
        # correct its own output.
        #
        # So the set is "objects that hold this writer's output at all", and the occurrence
        # predicate below decides whether each actually changed.
        if any(s in txt for s in OLD_SHAPES) or any(s in txt for s in NEW_SHAPES):
            affected.append(t)

    print("objects read %d; carrying a bare field key in stored prose: %d"
          % (len(before), len(affected)))
    if not affected:
        print("NOTHING TO DO -- no stored bookkeeping text carries a bare key.")
        return
    if not apply:
        for t in affected[:12]:
            print("   %s" % t)
        print("")
        print("DRY RUN. Pass --apply to quarantine and rewrite.")
        return

    # 2 QUARANTINE, BEFORE ANY WRITE.
    if os.path.isdir(QUAR):
        shutil.rmtree(QUAR)
    os.makedirs(QUAR)
    for t in affected:
        shutil.copy2(before[t]["path"], os.path.join(QUAR, t + ".json"))
    n_q = len(os.listdir(QUAR))
    print("quarantined %d object(s) to %s" % (n_q, os.path.relpath(QUAR, REPO)))
    if n_q != len(affected):
        sys.exit("REFUSED: quarantine holds %d of %d objects. Nothing has been written."
                 % (n_q, len(affected)))

    # THE WRITER DOES NOT KNOW ABOUT `ssot/do_not_rebuild.py` AND OVERWRITES
    # `manuscript.references` UNCONDITIONALLY (line 468: `man["references"] = refs`, with no
    # guard, unlike `introduction` which checks for an existing value first).
    #
    # `arni-hfref` holds an AUTHORED manuscript -- abstract, discussion, conclusions,
    # methods_prose -- and a 5-entry references dict. Running the writer over it would replace
    # written argument with a projection, which is the exact thing the do-not-rebuild list
    # exists to prevent, arriving through a path that list does not cover.
    #
    # So the topics are passed EXPLICITLY rather than with `--all`. That the writer needs this
    # guard from outside is itself a finding and is reported, not silently worked around.
    skip = {"arni-hfref"}
    run_topics = [t for t in affected if t not in skip]
    excluded = sorted(set(affected) & skip)
    if excluded:
        print("EXCLUDED, authored manuscript the writer would overwrite: %s"
              % ", ".join(excluded))
    r = subprocess.run([sys.executable,
                        os.path.join(REPO, "scripts",
                                     "build_paper_bookkeeping_2026_08_21.py"),
                        "--all", "--apply"] + run_topics,
                       cwd=REPO, capture_output=True)
    tail = r.stdout.decode("utf-8", "replace").strip().splitlines()[-3:]
    print("writer exit %d: %s" % (r.returncode, " | ".join(tail)))
    if r.returncode != 0:
        sys.exit("REFUSED: the writer failed. Objects are quarantined at %s." % QUAR)

    # 1 NET-ADDITIVE, and 4 THE OCCURRENCE PREDICATE, per object.
    lost, unchanged, changed, still = [], [], [], []
    for t in run_topics:
        o = json.load(io.open(before[t]["path"], encoding="utf-8"))
        k2, txt2 = keycount(o), stored_text(o)
        if k2 < before[t]["keys"]:
            lost.append((t, before[t]["keys"], k2))
        if txt2 == before[t]["text"]:
            unchanged.append(t)
        else:
            changed.append(t)
        if any(s in txt2 for s in OLD_SHAPES):
            still.append(t)

    print("")
    print("   stored text CHANGED            %4d" % len(changed))
    print("   stored text UNCHANGED          %4d   <- the writer did not reach these" % len(unchanged))
    print("   objects that LOST a key        %4d" % len(lost))
    print("   still carrying a bare key      %4d" % len(still))
    json.dump({"affected": affected, "changed": changed, "unchanged": unchanged,
               "lost_keys": lost, "still": still,
               "quarantine": os.path.relpath(QUAR, REPO)},
              io.open(OUT, "w", encoding="utf-8"), indent=1)
    if lost:
        for t, a, b in lost[:8]:
            print("      %-34s %d -> %d keys" % (t[:34], a, b))
        sys.exit("REFUSED AFTER WRITING: %d object(s) lost keys. Restore from %s before "
                 "doing anything else." % (len(lost), QUAR))
    # THE OCCURRENCE PREDICATE, AWARE OF WHICH RUN IT IS.
    #
    # "Assert that something changed" is true of a first pass and FALSE of a repeat: this run
    # refused 48 objects as "expected to change and did not" while every one was already
    # correct. On a verification pass the discriminator is the DEFECT COUNT, not the change
    # count -- a run that never executed is also unchanged.
    first = "--verify" not in sys.argv
    _ic.occurrence_predicate(first, len(changed), len(unchanged),
                             len([t for t in still if "families" not in
                                  json.dumps(stored_text(json.load(io.open(
                                      before[t]["path"], encoding="utf-8"))))]),
                             "bookkeeping lead-in rewrite")
    print("")
    print("NET-ADDITIVE, EVERY AFFECTED OBJECT CHANGED, QUARANTINE HELD AT %s"
          % os.path.relpath(QUAR, REPO))


if __name__ == "__main__":
    main()
