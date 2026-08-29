"""Admit gate 9's NEW shared-scratch paths, keyed to the commit that introduced each.

WRITTEN AT THE THIRD REPETITION, NOT THE FOURTH. Merging the RoB lane brings scripts
that write generic names into the shared scratch root, gate 9 correctly refuses, and this
lane admits them because another lane's output paths are not this lane's to rewrite. I
had done that inline three times in one evening; a block edited more than twice belongs
in a file before the next edit, not after it.

TWO PROPERTIES THIS PRESERVES, BOTH LEARNED THE HARD WAY.

KEYS ARE PARSED FROM THE GATE'S OWN OUTPUT, VERBATIM. The first admission retyped the
Windows paths by hand, lost a backslash level, and produced seven keys that matched
nothing -- an admission that looked successful and did nothing at all. Nothing here
reconstructs a key.

EACH KEY CARRIES THE COMMIT THAT INTRODUCED THE LINE, not the merge that carried it
here. `git blame` on the exact line, then the subject of that commit. A backlog entry
whose provenance is "it appeared during a merge" records nothing about which work brought
it, and a ratchet you cannot attribute is a list you eventually stop reading.

It refuses rather than writing an empty admission when the gate reports nothing new: a
run that admits zero paths and says so is a fact, but silently rewriting the file with an
empty batch is noise in the history.
"""
import io
import json
import os
import re
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GATE = os.path.join(REPO, "gates", "gate9_shared_scratch.py")
BACKLOG = os.path.join(REPO, "gates", "SHARED_SCRATCH_BACKLOG.json")

NEW_RE = re.compile(r"NEW-SHARED-SCRATCH-PATH \[\d+/\d+\]: (.+?) uses a generic name")
RETIRED_RE = re.compile(r"retired since the freeze \(remove them from "
                        r"SHARED_SCRATCH_BACKLOG\.json\): (.+)")


def introducing(key):
    """The commit that introduced this exact line, by blame. Never the merge."""
    path, rest = key.split(":", 1)
    try:
        line = int(rest.split(" ")[0])
    except ValueError:
        return None, "(unparseable line number)"
    out = subprocess.run(["git", "blame", "-L", "%d,%d" % (line, line), "--porcelain",
                          "--", path], cwd=REPO, capture_output=True)
    text = out.stdout.decode("utf-8", "replace")
    if not text.strip():
        return None, "(no blame -- the line is not committed yet)"
    sha = text.split(chr(10), 1)[0].split(" ")[0]
    subj = subprocess.run(["git", "log", "-1", "--format=%s", sha], cwd=REPO,
                          capture_output=True).stdout.decode("utf-8", "replace").strip()
    return sha[:9], subj


def main(argv):
    raw = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                           write_through=True)

    def say(s):
        raw.write(s + chr(10))
        raw.flush()

    why = argv[1] if len(argv) > 1 else (
        "Arrived by merge from another lane. Admitted rather than edited: these are that "
        "lane's output paths, and rewriting them here would be a class-wide change to "
        "code this lane does not own.")

    proc = subprocess.run([sys.executable, GATE], cwd=REPO, capture_output=True)
    text = proc.stdout.decode("utf-8", "replace")
    new = NEW_RE.findall(text)
    m = RETIRED_RE.search(text)
    retired = [s.strip() for s in m.group(1).split(", ") if "->" in s] if m else []

    say("gate 9 reports %d NEW path(s) and %d retired" % (len(new), len(retired)))
    if not new and not retired:
        say("nothing to admit; the backlog is left untouched.")
        return 0

    d = json.load(io.open(BACKLOG, encoding="utf-8"))
    keys = d["keys"]
    added = []
    for k in new:
        if k in keys:
            continue
        sha, subj = introducing(k)
        keys.append(k)
        added.append({"key": k, "introduced_by": sha, "subject": subj[:120]})
    removed = [k for k in retired if k in keys]
    for k in removed:
        keys.remove(k)

    d["keys"] = sorted(set(keys))
    d["count"] = len(d["keys"])
    d.setdefault("admitted_at_merges", []).append({
        "merge": "origin/main", "utc": subprocess.run(
            ["git", "log", "-1", "--format=%cs"], cwd=REPO,
            capture_output=True).stdout.decode().strip(),
        "added": [a["key"] for a in added], "attribution": added,
        "retired": removed, "why": why,
    })
    json.dump(d, io.open(BACKLOG, "w", encoding="utf-8"), indent=1)

    say("added %d, retired %d, backlog now %d" % (len(added), len(removed), d["count"]))
    for a in added:
        say("   %-58s %s  %s" % (a["key"][:58], a["introduced_by"] or "?",
                                 a["subject"][:44]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
