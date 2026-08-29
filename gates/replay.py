# no-control: the matching here is done inside the shipped detectors this module calls, each
# of which carries its own control. This module compares two sets of THEIR findings and emits
# no text-derived count of its own. Stated rather than silently exempted.
"""HISTORICAL REPLAY -- would the suite we have now have caught the defects we actually made?

WHY THIS BEATS A PLANT. A plant tests whether a detector can see a case constructed for it.
Replay tests whether it would have caught the thing that actually happened, in situ, with all
its surrounding noise, in the file where it really lived. Nothing synthetic reproduces that.

IT IS READ-ONLY. Every state is read with `git show`; no file is written, no plant is applied,
nothing needs restoring. The safety story here is not "we restored correctly", it is "there
was never anything to restore".

THE DIFFERENTIAL IS THE MEASUREMENT, AND IT IS THE WHOLE DESIGN. Running a detector over a
pre-fix file and counting its findings would score the corpus's ordinary background against
the defect. So every detector is run TWICE -- once on the parent of the fixing commit, once on
the commit itself -- and a CATCH requires a finding that is present BEFORE and absent AFTER.
A finding present in both is background and is counted as background, never as a catch.

WHAT A MISS MEANS HERE. The defect was real, a person found it, someone fixed it, and the
suite we have today, run over the exact bytes that carried it, says nothing. That is a recall
gap on a real defect and it is the deliverable.

Writes out/replay_report.json. Prints summary lines only.
"""
from __future__ import annotations

import io
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
REPO = os.path.dirname(HERE)

import _harness as H                                                        # noqa: E402
import gate1_trial_identity as G1                                           # noqa: E402
import gate3_one_reason_field as G3                                         # noqa: E402
import gate4_judgement_reference as G4                                      # noqa: E402
import gate6_nct_beside_name as G6                                          # noqa: E402
import textmatch as TM                                                      # noqa: E402

LEDGERS = ("out/blind-review/q1_ledger.json",)


def git(*args):
    return subprocess.run(["git", "-C", REPO] + list(args),
                          capture_output=True, text=True, errors="replace")


def show(rev, path):
    r = git("show", "%s:%s" % (rev, path))
    return r.stdout if r.returncode == 0 else None


def changed_files(commit):
    r = git("show", "--name-only", "--pretty=format:", commit)
    return [l.strip() for l in r.stdout.splitlines() if l.strip()]


# ---------------------------------------------------------------------------
# detectors, each returning a SET of finding keys so two states can be differenced
# ---------------------------------------------------------------------------
def detect_store(text, topic):
    """Every shipped store-side detector, over one object's bytes."""
    out = set()
    try:
        obj = json.loads(text)
    except Exception:
        return out, "unparseable"
    if not isinstance(obj, dict):
        return out, "not an object"
    try:
        rows, _ = G1.check_objects({topic: obj})
        for r in rows:
            out.add("gate1:SWAPPED-NAME:%s" % r.get("path"))
    except Exception as exc:
        out.add("gate1:ERROR:%r" % exc)
    try:
        rows, _ = G3.scan({topic: obj})
        for r in rows:
            out.add("gate3:REASON-DIVERGENCE:%s" % (r.get("outcome") or r.get("oid")))
    except Exception as exc:
        out.add("gate3:ERROR:%r" % exc)
    try:
        for path, _blk, kind in G4.judgement_blocks(obj):
            if kind == G4.KIND_D:
                out.add("gate4:JUDGEMENT-WITH-NO-REFERENCE:%s" % path)
    except Exception as exc:
        out.add("gate4:ERROR:%r" % exc)
    return out, "ok"


def detect_served(text):
    out = set()
    try:
        page = TM.page_text(text)
    except Exception as exc:
        return out, "page_text failed %r" % exc
    for nct in G6.PINNED:
        try:
            verdict, _ = G6.pair_by_nearest(page, nct)
        except Exception as exc:
            out.add("gate6:ERROR:%r" % exc)
            continue
        if verdict == "SWAPPED":
            out.add("gate6:SWAPPED-IN-PROSE:%s" % nct)
        elif verdict == "AMBIGUOUS":
            out.add("gate6:AMBIGUOUS(not a finding):%s" % nct)
    return out, "ok"


def is_corpus(path):
    return (path.startswith("ssot/") and path.endswith(".json")) or \
           (path.endswith(".html") and "/" not in path)


def main(argv):
    entries = []
    # A commit list may be supplied directly. The ledger holds mostly GENERATOR fixes, which
    # by design touch no corpus file and therefore cannot be replayed by diffing one; the
    # per-instance fixes that CAN be replayed are found in the history itself.
    if "--commits" in argv:
        for line in io.open(argv[argv.index("--commits") + 1], encoding="utf-8"):
            c = line.strip()
            if c:
                r = git("show", "-s", "--pretty=format:%s", c)
                entries.append({"claim": r.stdout.strip()[:110], "commit": c,
                                "state": "from-history", "reason": ""})
    for rel in ([] if entries else LEDGERS):
        p = os.path.join(REPO, rel)
        if not os.path.exists(p):
            continue
        led = json.load(io.open(p, encoding="utf-8"))
        for claim, rec in led.items():
            if isinstance(rec, dict) and rec.get("commit"):
                entries.append({"claim": claim[:110], "commit": rec["commit"],
                                "state": rec.get("state"), "reason": (rec.get("reason") or "")[:200]})

    print("register entries with a fixing commit: %d" % len(entries))

    report, kinds = [], {"defects replayed": 0, "  CAUGHT by a current detector": 0,
                         "  MISSED": 0, "  NOT REPLAYABLE (commit or parent unavailable)": 0,
                         "corpus files examined": 0}

    for e in entries:
        c = e["commit"]
        if git("cat-file", "-e", c + "^{commit}").returncode != 0:
            e["result"] = "NOT-REPLAYABLE"; e["why"] = "commit not in this history"
            kinds["  NOT REPLAYABLE (commit or parent unavailable)"] += 1
            report.append(e); continue
        if git("cat-file", "-e", c + "^^{commit}").returncode != 0:
            e["result"] = "NOT-REPLAYABLE"; e["why"] = "commit has no parent (root)"
            kinds["  NOT REPLAYABLE (commit or parent unavailable)"] += 1
            report.append(e); continue

        files = [f for f in changed_files(c) if is_corpus(f)]
        e["corpus_files_changed"] = len(files)
        gained, lost, seen = set(), set(), 0
        for f in files:
            before, after = show(c + "^", f), show(c, f)
            if before is None or after is None:
                continue
            seen += 1
            topic = os.path.basename(os.path.dirname(f)) if f.startswith("ssot/") else f
            if f.startswith("ssot/"):
                fb, _ = detect_store(before, topic)
                fa, _ = detect_store(after, topic)
            else:
                fb, _ = detect_served(before)
                fa, _ = detect_served(after)
            # a CATCH is a finding present BEFORE and absent AFTER. Present in both = background.
            real = {x for x in (fb - fa) if "AMBIGUOUS" not in x and ":ERROR:" not in x}
            gained |= real
            lost |= (fa - fb)
        kinds["corpus files examined"] += seen
        e["files_readable"] = seen
        e["caught_by"] = sorted(gained)
        e["new_findings_after_fix"] = sorted(lost)
        if not files or seen == 0:
            e["result"] = "NOT-REPLAYABLE"
            e["why"] = "the fix touched no corpus file readable at both states"
            kinds["  NOT REPLAYABLE (commit or parent unavailable)"] += 1
        elif gained:
            e["result"] = "CAUGHT"
            kinds["defects replayed"] += 1; kinds["  CAUGHT by a current detector"] += 1
        else:
            e["result"] = "MISSED"
            kinds["defects replayed"] += 1; kinds["  MISSED"] += 1
        report.append(e)

    outp = os.path.join(REPO, "out", "replay_report.json")
    with io.open(outp, "w", encoding="utf-8") as fh:
        json.dump({"kinds": kinds, "entries": report}, fh, indent=1)

    print("")
    for k, v in kinds.items():
        print("  %5s  %s" % (v, k))
    rep = kinds["defects replayed"]
    print("")
    print("  REPLAY RECALL: %d / %d" % (kinds["  CAUGHT by a current detector"], rep)
          + ("  (%.0f%%)" % (100.0 * kinds["  CAUGHT by a current detector"] / rep) if rep else ""))
    print("  wrote out/replay_report.json")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
