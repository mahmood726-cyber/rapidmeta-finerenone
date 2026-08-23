"""Which writers can overwrite authored manuscript prose, and which of them are guarded.

# no-control: a static audit of source files, so the known answer is the source itself. The
# control that matters is asserted: `build_paper_bookkeeping_2026_08_21.py` MUST come back
# guarded (it was fixed for this reason today) and at least one unguarded writer must be found
# if any exists -- a scan that reports every writer as safe on a corpus where one certainly was
# not is a scan that is not reading anything.

THE NEAR-MISS THIS COMES FROM, AND IT WOULD HAVE DESTROYED THE ONLY AUTHORED MANUSCRIPT IN THE
CORPUS. `build_paper_bookkeeping_2026_08_21.py` writes:

    man["references"] = refs                                    <- UNCONDITIONAL
    if intro and not str(man.get("introduction") or "").strip(): <- GUARDED, two lines later

One field in one function is careful and the other is not, which means somebody already knew
the guard was needed and applied it to one field. Run with `--all`, it would have replaced
ARNI's five authored references with a projection.

`ssot/do_not_rebuild.py` did not stop it: THAT LIST GUARDED THE BUILDER AND THE WRITE CAME
THROUGH A DIFFERENT DOOR. `check()` takes an out_path -- a page -- and writers never see one.
`check_object()` was added for exactly this and the writer now imports it.

SO THE QUESTION IS WHETHER THE LIST GUARDS ONE ENTRY POINT OF SEVERAL. This names the others.

TWO THINGS ARE REPORTED SEPARATELY BECAUSE THEY ARE DIFFERENT RISKS:

  * writers that mutate `ssot/**/*.json` WITHOUT importing the do-not-rebuild check -- any of
    them can reach a protected object
  * assignments to `manuscript.<field>` that are UNCONDITIONAL -- these overwrite authored
    prose even on an unprotected object, and the only defence is that nobody has run them
"""
from __future__ import annotations

import glob
import io
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "outputs", "writer_guard_audit_2026_08_23.json")

WRITES_OBJECT = re.compile(
    r"atomic_write\.write_json|json\.dump\s*\(\s*obj|write_json\s*\(")
GUARDED = re.compile(r"do_not_rebuild|check_object\s*\(|_dnr\.")
# man["x"] = ...  /  man.setdefault(...)  /  obj["manuscript"]["x"] = ...
# `man[...]` ALONE IS NOT A MANUSCRIPT WRITE, and the first version of this audit reported one
# that was not. `scripts/artefact_registry.py` names its ARTEFACT-MANIFEST variable `man` and
# writes `man["artefacts"]`, `man["what_this_is"]`, `man["kinds"]` to ARTEFACT-MANIFEST.json --
# nothing to do with a manuscript. A regex keyed to a variable NAME rather than to what the
# variable holds is the same mistake as a probe keyed to a token rather than a claim, so the
# file must also show it is handling a manuscript at all.
MAN_ASSIGN = re.compile(
    r"""(?:man|manuscript|_man)\s*\[\s*["']([a-z_0-9]+)["']\s*\]\s*=""")
IS_MANUSCRIPT_FILE = re.compile(
    r"""["']manuscript["']|manuscript\s*=|\.manuscript\b""")
# the guarded form: `if <something> and not str(man.get("x") ...` on the preceding lines
GUARD_NEAR = re.compile(
    r"not\s+str\(\s*man\.get\(|if\s+not\s+man\.get\(|man\.setdefault\(|refuse_if_authored")


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    rows, unguarded_writers, man_writes = [], [], []
    for p in sorted(glob.glob(os.path.join(REPO, "scripts", "*.py"))
                    + glob.glob(os.path.join(REPO, "ssot", "*.py"))):
        try:
            src = io.open(p, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        name = os.path.relpath(p, REPO).replace("\\", "/")
        # THE POSITIVE PROPERTY, STATED. The population is "files that WRITE an object" --
        # `atomic_write.write_json`, `json.dump(obj`, `write_json(` -- and every file in it is
        # counted. This is a selection, not an exclusion-by-absence: a file that writes no
        # object is not a writer whose guard status could mean anything, and the number that
        # matters (70) is the size of the population itself, printed on every run.
        writes_an_object = bool(WRITES_OBJECT.search(src))
        if not writes_an_object:  # lint:allow-negative-guard  selection, not absence
            continue
        guarded = bool(GUARDED.search(src))
        rows.append({"file": name, "guarded": guarded})
        if not guarded:
            unguarded_writers.append(name)
        lines = src.splitlines()
        handles_manuscript = bool(IS_MANUSCRIPT_FILE.search(src))
        for i, line in enumerate(lines):
            m = MAN_ASSIGN.search(line)
            # A COMMENT QUOTING THE CODE IS NOT THE CODE. This audit flagged line 489 of
            # `build_paper_bookkeeping_2026_08_21.py` -- a comment reading `man["references"]
            # = refs` that was written to EXPLAIN the guard sitting directly beneath it. An
            # instrument that reads its own documentation as an instance is the same shape as
            # a probe keyed to a token rather than a claim, and it appeared here within an
            # hour of that lesson being written down.
            if not m or not handles_manuscript or line.lstrip().startswith("#"):
                continue
            window = "\n".join(lines[max(0, i - 3):i + 1])
            man_writes.append({"file": name, "line": i + 1, "field": m.group(1),
                               "guarded": bool(GUARD_NEAR.search(window))})

    print("")
    print("WRITERS THAT MUTATE ssot/**/*.json: %d" % len(rows))
    print("   import the do-not-rebuild check   %4d" % sum(1 for r in rows if r["guarded"]))
    print("   DO NOT                            %4d" % len(unguarded_writers))
    print("")
    for n in unguarded_writers[:24]:
        print("      %s" % n)
    if len(unguarded_writers) > 24:
        print("      ... and %d more" % (len(unguarded_writers) - 24))

    print("")
    print("ASSIGNMENTS TO manuscript.<field>: %d" % len(man_writes))
    ung = [w for w in man_writes if not w["guarded"]]
    print("   guarded against an existing value %4d" % (len(man_writes) - len(ung)))
    print("   UNCONDITIONAL                     %4d   <- these overwrite authored prose"
          % len(ung))
    print("")
    for w in ung[:20]:
        print("      %-52s line %-5d manuscript.%s" % (w["file"][:52], w["line"], w["field"]))

    # THE CONTROL. The file fixed today must come back guarded; if it does not, this scan is
    # not reading what it claims to read.
    bk = next((r for r in rows if r["file"].endswith("build_paper_bookkeeping_2026_08_21.py")),
              None)
    print("")
    if bk is None:
        sys.exit("REFUSED: the writer known to mutate objects was not even detected as one. "
                 "This scan is not reading what it claims to read.")
    print("CONTROL: build_paper_bookkeeping_2026_08_21.py guarded = %r (fixed today, must be "
          "True)" % bk["guarded"])
    json.dump({"writers": rows, "unguarded_writers": unguarded_writers,
               "manuscript_writes": man_writes},
              io.open(OUT, "w", encoding="utf-8"), indent=1)
    if not bk["guarded"]:
        sys.exit("REFUSED: the control file reports unguarded.")
    print("")
    print("A LIST THAT GUARDS ONE ENTRY POINT OF SEVERAL IS A LIST THAT WILL BE BYPASSED BY")
    print("THE NEXT CALLER. The unguarded writers above are named so the choice to leave them")
    print("that way is a decision rather than an oversight.")


if __name__ == "__main__":
    main()
