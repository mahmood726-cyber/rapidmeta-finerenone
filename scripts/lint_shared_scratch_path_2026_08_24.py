"""No script may read or write a GENERIC name in the shared scratch root.

WHAT HAPPENED. `git commit -F /f/claude-temp/msg.txt` committed 220 files of this session's
work under the message "Interactive education pilot: two style variants + noscript coverage".
The content was correct; the message belonged to ANOTHER LANE, which had written that exact
path seven hours earlier. Three agent lanes were active on this machine tonight and `msg.txt`
is the filename every one of them would independently choose.

AND `/tmp` IS THAT SAME ROOT. On this machine `/tmp` resolves to `F:/claude-temp` -- 31,531
loose files, shared by every lane. So `/tmp/anything` is not a private temp file, and a
session that believes otherwise is one collision away from reading somebody else's work as
its own.

THE NEAR-MISS THAT MATTERS MORE THAN THE COMMIT MESSAGE. A plant-the-defect test copied the
live manuscript projector to `/tmp/pp_backup.py`, deliberately corrupted the original,
observed the failure, and then RESTORED THE LIVE PROJECTOR FROM THAT PATH. Had another lane
written `/tmp/pp_backup.py` in the intervening minutes, the restore would have written their
file over a 4,600-line generator that renders 148 published pages. It did not happen -- the
file's contents place it correctly in this session's timeline -- but nothing prevented it.

THIS IS THE SAME FAILURE AS EVERY OTHER ONE TONIGHT. A read that returns SOMETHING, and the
something comes from an adjacent source: a debug render instead of a page, `render()` instead
of built HTML, Git Bash paths against Windows Python, a delivered artefact instead of a code
state, our own records instead of an independent answer key. It simply arrived through the
filesystem rather than through an instrument.

THE RULE: scratch files go in the SESSION directory, which is unique per lane. If a script
must use the shared root, the filename carries a unique suffix. A bare generic name there is
refused.
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from instrument_controls import require_controls  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Paths in the shared scratch root. `/tmp` is included because it RESOLVES there on this
# machine, which is the part that makes it dangerous -- it looks private and is not.
_SHARED = re.compile(
    r"""(?:['"]|\s)(?:/tmp/|/f/claude-temp/|F:[\\/]{1,2}claude-temp[\\/]{1,2})"""
    r"""(?P<rest>[^'"\s)]*)""", re.I)

# A name is SAFE in the shared root if it carries something unique to this lane: a session
# id, a pid, a timestamp, or the per-session `claude/<project>/<uuid>/` prefix the harness
# provides. Anything else is a name another lane would plausibly choose too.
_UNIQUE = re.compile(
    # `claude[\\/]` BOTH WAYS. Checking only the forward slash flagged four session-scoped
    # Windows paths as shared -- the lint reporting a defect that was not there, which is
    # the same class of error as the one it exists to catch. Fix the instrument before
    # believing its output.
    r"claude[\\/]|[0-9a-f]{8}-[0-9a-f]{4}|\$\$|\$RANDOM|getpid|uuid|%s|\{.*\}|"
    r"20\d\d[-_]?\d\d[-_]?\d\d", re.I)


def main():
    hits = []
    for root, dirs, files in os.walk(os.path.join(REPO, "scripts")):
        dirs[:] = [d for d in dirs if d not in (".git", "__pycache__")]
        # POSITIVE FORM: the files that ARE python, excluding this one, whose docstring
        # necessarily quotes the paths it forbids. `audit_exclusion_by_absence --gate`
        # refuses a corpus-wide loop defined by what it skips, and it is right even here --
        # a scan that cannot say how many files it examined cannot support "8 hits".
        python_files = [f for f in files
                        if f.endswith(".py") and f != os.path.basename(__file__)]
        for fn in python_files:
            p = os.path.join(root, fn)
            try:
                src = io.open(p, encoding="utf-8", errors="replace").read()
            except OSError:
                continue
            for m in _SHARED.finditer(src):
                rest = m.group("rest")
                if _UNIQUE.search(rest):
                    continue
                line = src[:m.start()].count("\n") + 1
                hits.append((os.path.relpath(p, REPO), line, rest[:60]))

    # ROUTED THROUGH THE SHARED HELPER, which `lint_instrument_declares_a_control` requires
    # and which is right to: a hand-rolled control is one more thing that can quietly stop
    # firing. The positive case is the REAL LINE that caused the incident, quoted verbatim
    # from the command that committed 220 files under another lane's message.
    def flags(src):
        return any(not _UNIQUE.search(m.group("rest")) for m in _SHARED.finditer(src))

    require_controls(
        "lint_shared_scratch_path",
        positive=("the line that caused the incident -- "
                  'git commit -F "/tmp/msg.txt"',
                  flags('git commit -F "/tmp/msg.txt"'), True),
        negative=("a session-scoped path, which is the SAFE form and must not be flagged",
                  flags('open(r"F:\\claude-temp\\claude\\proj\\e2e2a1d5-c19e\\s\\msg.txt")'),
                  True))
    print()

    print("SHARED-ROOT SCRATCH PATHS WITH A NAME ANOTHER LANE COULD CHOOSE: %d" % len(hits))
    for path, line, rest in hits:
        print("   %s:%d  -> %s" % (path, line, rest))
    if hits:
        print()
        print("REFUSED: write to the SESSION scratch directory, or add a unique suffix.")
        print("A shared path that looks private is how 220 files were committed under")
        print("another lane's message, and how a live generator was nearly restored from")
        print("a file this session did not write.")
        return 1
    print("   none.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
