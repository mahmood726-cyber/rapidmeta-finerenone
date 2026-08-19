"""THE THREE-PART PROOF for the two guards written on 2026-08-19 (PAGE-STANDARD P16).

    A guard MUST BE ABLE TO FIRE; it MUST NOT FIRE ON THE CORRECT CASE; and NEITHER OF THOSE
    CAN BE ESTABLISHED BY THE BUILD REPORTING SUCCESS.

The third clause is the one that gets skipped, and it is the one that caught the
foreign-registration-id guard: it compiled, imported, ran, and the build printed
`HELD 7 / REFUSING 1` and success while the guard was unable to match anything, because the
heredoc transport had turned its `\\b` into a literal backspace byte.

GUARDS UNDER TEST
    scripts/lint_ours_matches_pool.py       a field named `ours` holding a superseded estimate
    scripts/lint_cascade_arithmetic.py      k2_role_located counting the records it could not
                                            locate

THE PLANTED DEFECTS ARE REAL AND ARE READ OUT OF GIT, not invented here. Both are taken from
`21e9cfcf3`, the commit at which they were shipped on a gated page. A synthetic fixture would
test each guard against its author's idea of the defect; these are the defect.

Part 3 PLANTS ON DISK, runs the real builder, and shows the builder reporting success over the
planted object -- then restores from git and verifies the restore by hash. If the restore
cannot be verified this script FAILS rather than leaving the tree modified.
"""
import hashlib
import io
import json
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(REPO, "scripts")
sys.path.insert(0, SCRIPTS)

import lint_cascade_arithmetic as CASC     # noqa: E402
import lint_ours_matches_pool as OURS      # noqa: E402

SHIPPED_REV = "21e9cfcf3"
TOPIC = "alirocumab-lipid"
OBJ_REL = "ssot/%s/%s.json" % (TOPIC, TOPIC)
OBJ_ABS = os.path.join(REPO, OBJ_REL)


def git_show(rev, rel):
    # Decoded explicitly rather than by text=True, which uses the console codepage.
    return subprocess.run(["git", "-C", REPO, "show", "%s:%s" % (rev, rel)],
                          capture_output=True, check=True).stdout.decode("utf-8", "replace")


def run(argv):
    """(returncode, stdout) with stdout decoded as UTF-8, never as cp1252."""
    p = subprocess.run(argv, capture_output=True, cwd=REPO,
                       env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    return p.returncode, p.stdout.decode("utf-8", "replace")


def md5(path):
    with open(path, "rb") as fh:
        return hashlib.md5(fh.read()).hexdigest()


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    failures = []

    shipped = json.loads(git_show(SHIPPED_REV, OBJ_REL))
    real_ours = shipped["published_comparison"]["divergence_decomposed"]["ours"]
    real_k2 = shipped["k_cascade"]["k2_role_located"]
    print("THE PLANTED DEFECTS, read from git %s -- not written for this test" % SHIPPED_REV)
    print("   published_comparison.divergence_decomposed.ours")
    print("      %s" % " ".join(real_ours.split())[:150])
    print("   k_cascade.k2_role_located = %s  (with kNA = %s, so 'located' includes the "
          "unlocatable)" % (real_k2, shipped["k_cascade"]["kNA_not_assessable"]))
    print()

    with io.open(OBJ_ABS, encoding="utf-8") as fh:
        current = json.load(fh)

    # ---------------------------------------------------------------- PART 1: it can fire
    print("PART 1 -- CAN IT FIRE? Plant each real defect into the CURRENT object and check.")
    planted = json.loads(json.dumps(current))
    planted["published_comparison"]["divergence_decomposed"]["ours"] = real_ours
    rows, _adv = OURS.check(planted)
    fired = [r for r in rows if r[1] == OURS.FAIL]
    print("   lint_ours_matches_pool          %d failing limb(s)  %s"
          % (len(fired), "FIRES" if fired else "SILENT -- THE GUARD IS DEAD"))
    for r in fired:
        print("        %s -- %s" % (r[0], r[2]))
    if not fired:
        failures.append("lint_ours_matches_pool did not fire on the real planted defect")

    planted2 = json.loads(json.dumps(current))
    planted2["k_cascade"]["k2_role_located"] = real_k2
    _state, crows = CASC.check(planted2)
    cfired = [r for r in crows if r[1] == CASC.FAIL]
    print("   lint_cascade_arithmetic         %d failing limb(s)  %s"
          % (len(cfired), "FIRES" if cfired else "SILENT -- THE GUARD IS DEAD"))
    for cid, _v, detail in cfired:
        print("        %s -- %s" % (cid, detail))
    if not cfired:
        failures.append("lint_cascade_arithmetic did not fire on the real planted defect")

    # ------------------------------------------------- PART 2: it is silent when correct
    print()
    print("PART 2 -- DOES IT STAY SILENT ON THE CORRECT CASE? Same object, defects removed.")
    rows, _adv = OURS.check(current)
    ofalse = [r for r in rows if r[1] == OURS.FAIL]
    _state, crows = CASC.check(current)
    cfalse = [r for r in crows if r[1] == CASC.FAIL]
    print("   lint_ours_matches_pool          %d alarm(s)  %s"
          % (len(ofalse), "SILENT" if not ofalse else "FALSE ALARM"))
    print("   lint_cascade_arithmetic         %d alarm(s)  %s"
          % (len(cfalse), "SILENT" if not cfalse else "FALSE ALARM"))
    for r in ofalse:
        print("        %s -- %s" % (r[0], r[2]))
    for cid, _v, detail in cfalse:
        print("        %s -- %s" % (cid, detail))
    if ofalse:
        failures.append("lint_ours_matches_pool raised a false alarm on the corrected object")
    if cfalse:
        failures.append("lint_cascade_arithmetic raised a false alarm on the corrected object")

    # -------------------------------- PART 3: the build's success proves NEITHER of those
    print()
    print("PART 3 -- THE BUILD CANNOT ESTABLISH EITHER. Plant ON DISK, run the real builder,")
    print("          and read what it says about an object carrying a shipped defect.")
    # THE SNAPSHOT IS RAW BYTES, NOT A PARSED COPY, AND THE FIRST VERSION GOT THIS WRONG.
    # Restoring by re-serialising `current` produced a file that differed from the original
    # and then took one builder run to converge back -- so the restore "succeeded" while
    # leaving the tree in a state neither the builder nor git had produced.
    #
    #     A ROUND TRIP THROUGH A PARSER IS NOT A COPY. If the original bytes are available,
    #     restore THOSE. The same rule that made the k=8 reproduction gate pass.
    with open(OBJ_ABS, "rb") as fh:
        snapshot = fh.read()
    before = hashlib.md5(snapshot).hexdigest()
    restored = False
    try:
        with io.open(OBJ_ABS, "w", encoding="utf-8") as fh:
            fh.write(json.dumps(planted, indent=1, ensure_ascii=True))
        brc, bout = run([sys.executable, "-W", "error::SyntaxWarning",
                         os.path.join(REPO, "ssot", "build_to_standard.py"), TOPIC])
        verdict = [ln for ln in bout.splitlines() if ln.startswith("HELD ")]
        print("   builder exit code            %d" % brc)
        print("   builder final verdict        %s"
              % (verdict[-1] if verdict else "(no HELD line)"))
        lrc, _lout = run([sys.executable,
                          os.path.join(SCRIPTS, "lint_ours_matches_pool.py")])
        print("   lint exit code               %d" % lrc)
        print("   lint verdict                 %s" % ("REFUSED" if lrc else "clean"))
        proved = brc == 0 and lrc != 0
        print("   %s" % ("PROVED: the builder reported SUCCESS over an object the guard "
                         "refuses.\n           A green build is not evidence about a guard "
                         "inside it."
                         if proved else
                         "NOT PROVED: the builder did not report success, so this run says "
                         "nothing\n           about whether a green build could hide the "
                         "defect."))
        if not proved:
            failures.append("part 3 did not demonstrate builder-success alongside guard-fire")
    finally:
        # NOT `git checkout`: the object has been legitimately restated since HEAD and
        # restoring from HEAD would discard that work. The exact bytes read at the start of
        # part 3 are the only correct target.
        with open(OBJ_ABS, "wb") as fh:
            fh.write(snapshot)
        restored = md5(OBJ_ABS) == before

    print()
    print("   restore verified by md5      %s  (%s)"
          % ("YES" if restored else "NO", before))
    if not restored:
        failures.append("THE PLANTED OBJECT WAS NOT RESTORED -- the working tree is modified")

    print()
    if failures:
        for f in failures:
            print("FAILED: %s" % f)
        return 1
    print("ALL THREE PARTS PASS for both guards.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
