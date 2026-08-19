"""RE-DERIVE ANY TOPIC'S CASCADE ACROSS EVERY REVISION OF THE CLASSIFIER.

    python scripts/regate_across_revisions.py <topic-dir>

WHY THIS IS PARAMETERISED AND ITS PREDECESSOR WAS NOT.
`scripts/regate_sglt2_three_revisions.py` answered one question about one topic: why sglt2-hf's
stored cascade did not reproduce. It worked, and the moment a second topic needed the same
answer the choice was to copy it or to parameterise it. The standing rule is to parameterise at
the SECOND use, not the fourth -- a hardcoded target list edited twice is guaranteed drift.

WHAT IT IS FOR. PAGE-STANDARD P18: a restated quantity must be reproducible by a COMMAND. Two
topics carry a `restated_2026_08_19_placebo_discriminator` block narrating a delta that no
script could re-derive, so the number lived only in prose and would have aged exactly the way
sglt2-hf's did. This is that command.

The revision list is derived from git -- every commit that touched the classifier, oldest
first -- so it does not need editing when the classifier changes again.
"""
import importlib.util
import io
import json
import os
import subprocess
import sys

REPO = "F:/rapidmeta-ssot-shell"
sys.path.insert(0, REPO + "/ssot")
sys.path.insert(0, REPO + "/scripts")
os.environ.setdefault(
    "RM_CTGOV_CACHE",
    "F:/claude-temp/claude/F--rapidmeta-ssot-shell/"
    "eb4d84e5-8a24-4c3b-afe2-34bd91c20bc7/scratchpad/.ctgov-raw-cache")

import ctgov_transport as X                      # noqa: E402
import regate_cascade_2026_08_19 as R            # noqa: E402

SCRATCH = ("F:/claude-temp/claude/F--rapidmeta-ssot-shell/"
           "6b629e1e-cc8c-4565-af03-e40341ee43f3/scratchpad")
CLASSIFIER = "ssot/topic_identity.py"


def revisions():
    """Every commit that touched the classifier, OLDEST FIRST, from git rather than a list."""
    out = subprocess.run(["git", "-C", REPO, "log", "--reverse", "--format=%h\t%s",
                          "--", CLASSIFIER],
                         capture_output=True, check=True).stdout.decode("utf-8", "replace")
    rows = []
    for line in out.splitlines():
        if "\t" in line:
            sha, subject = line.split("\t", 1)
            rows.append((sha.strip(), subject.strip()))
    return rows


def load_rev(rev):
    src = subprocess.run(["git", "-C", REPO, "show", "%s:%s" % (rev, CLASSIFIER)],
                         capture_output=True, check=True).stdout.decode("utf-8", "replace")
    os.makedirs(SCRATCH, exist_ok=True)
    path = os.path.join(SCRATCH, "ti_%s.py" % rev)
    with io.open(path, "w", encoding="utf-8") as fh:
        fh.write(src)
    spec = importlib.util.spec_from_file_location("ti_%s" % rev, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    if len(sys.argv) < 2 or sys.argv[1] not in R.TOPICS:
        print("usage: regate_across_revisions.py <topic-dir>")
        print("topics on file: %s" % sorted(R.TOPICS))
        return 2
    topic = sys.argv[1]
    spec = R.TOPICS[topic]
    key = spec["topic_key"]

    state, ids, detail = R.raw_search(spec["raw_expr"])
    ids = sorted(set(ids))
    print("%s [%s]" % (topic, key))
    print("   surfaced set re-executed: %s -- %s" % (state, detail))
    if state != X.OK:
        print("   REFUSING: the surfaced set is incomplete, so every k below would be a "
              "floor rather than a count.")
        return 1

    payloads = {}
    for nct in ids:
        st, study, det = X.fetch_raw(nct)
        if st != X.OK:
            print("   UNREACHABLE %s: %s %s -- never read, not a verdict" % (nct, st, det))
            continue
        payloads[nct] = X.require_raw_v2(study, nct)

    obj = json.load(io.open("%s/ssot/%s/%s.json" % (REPO, topic, topic), encoding="utf-8"))
    kc = obj.get("k_cascade") or {}
    stored = {s: kc.get(s) for s in ("k3_experimental", "k4_comparator",
                                     "k5_background", "kNA_not_assessable")}

    revs = revisions()
    print("\n   %-11s %4s %4s %4s %4s   reproduces the stored %s/%s/%s/%s?"
          % ("revision", "k3", "k4", "k5", "kNA",
             stored["k3_experimental"], stored["k4_comparator"],
             stored["k5_background"], stored["kNA_not_assessable"]))
    per_rev, matches = {}, []
    for rev, subject in revs:
        mod = load_rev(rev)
        try:
            syns = mod.synonyms_for(key)
        except KeyError:
            print("   %-11s topic not declared at this revision -- NOT_ASSESSABLE, not a "
                  "zero" % rev)
            continue
        roles = {n: mod.locate(p, syns)[0] for n, p in payloads.items()}
        per_rev[rev] = roles
        t = {"k3_experimental": sum(1 for r in roles.values() if r == mod.EXPERIMENTAL),
             "k4_comparator": sum(1 for r in roles.values() if r == mod.COMPARATOR),
             "k5_background": sum(1 for r in roles.values() if r == mod.BACKGROUND),
             "kNA_not_assessable": sum(1 for r in roles.values() if r == mod.NOT_ASSESSABLE)}
        same = all(t[s] == stored[s] for s in stored)
        if same:
            matches.append(rev)
        print("   %-11s %4d %4d %4d %4d   %s"
              % (rev, t["k3_experimental"], t["k4_comparator"], t["k5_background"],
                 t["kNA_not_assessable"], "YES" if same else "no"))
        print("               %s" % subject[:88])

    print("\n   PER-TRIAL MOVEMENT between consecutive revisions:")
    seq = [r for r, _s in revs if r in per_rev]
    for a, b in zip(seq, seq[1:]):
        moved = {n: (per_rev[a][n], per_rev[b][n]) for n in per_rev[a]
                 if per_rev[a][n] != per_rev[b][n]}
        print("     %s -> %s: %d moved" % (a, b, len(moved)))
        for n, (x, y) in sorted(moved.items()):
            print("         %s  %s -> %s" % (n, x, y))

    print()
    if not matches:
        print("   THE STORED CASCADE REPRODUCES AT NO REVISION. That is not staleness -- it "
              "is a\n   number no version of this instrument produces, and it needs its own "
              "investigation.")
        return 1
    if matches[-1] != seq[-1]:
        print("   STALE: the stored numbers reproduce at %s and the classifier has moved on "
              "%d\n   revision(s) since. This is a MISSED RE-RUN, not changed data -- the "
              "surfaced set\n   was re-executed above and returned the same size."
              % (", ".join(matches), len(seq) - 1 - seq.index(matches[-1])))
        return 1
    print("   CURRENT: the stored numbers reproduce at the newest revision of the classifier.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
