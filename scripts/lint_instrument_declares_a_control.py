"""A NEW instrument that reports a corpus-wide finding must declare a control.

THIS IS THE MECHANICAL FORM OF THE NIGHT'S MOST EXPENSIVE HABIT. Four wrong accusations in
one session: 0.06 and 1.79 read out of a WITHDRAWAL NOTICE and relayed to a reader as what
the page serves; `pool_broken` reported against a pool that had been withdrawn on purpose;
two unbacked-claim findings raised against the flagship manuscript that were not unbacked;
a count of 49 never-taken branches produced by an extraction that captured code spans
between quotes rather than string literals. Every one was caught by a person reading the
instance. NOT ONE was caught by the instrument that produced it.

So the reading becomes part of the instrument. An instrument reporting a corpus-wide finding
routes through `instrument_controls.require_controls`, declaring:

    POSITIVE  a real corpus item whose answer is established INDEPENDENTLY -- from a
              registration, a delivered page, a recorded prior finding. Not from the same
              logic under test, which would only prove the code agrees with itself.
    NEGATIVE  a real corpus item the instrument must NOT flag. This side is not optional
              where over-flagging is the failure mode, and over-flagging was the failure
              mode in all four instances above. The mixed-contrast sweep's first draft
              accused `malaria-vaccines` and `cryptococcal-meningitis`, both of which
              CONTAIN mixed contrasts and NEITHER of which pools across them; only a
              negative control catches that.

WHAT COUNTS AS AN INSTRUMENT HERE. A file under `scripts/` named `audit_*`, `lint_*` or
`*_gate.py` that walks the corpus -- `ssot/*/*.json`, `figs/*.html`, or a comparable glob --
AND prints a count. A one-topic applier is not one; a corpus sweep is.

RATCHET, NOT RETROFIT. Fifty-odd existing instruments predate this and are listed in
`scripts/baselines/instrument_control_baseline.json`. They are NOT excused on the merits --
most of them can only say yes -- they are excused because rewriting fifty tonight would
itself be an unreviewed corpus-wide change, which is the shape of half this registry. THE
BASELINE COUNT MUST NEVER RISE. Any instrument not on it must comply, and an instrument
that legitimately cannot have a control says so in one line:

    # no-control: <why a known-answer case cannot exist for this check>

PROVEN, NOT ASSERTED. `--prove` writes a throwaway instrument with no control into a temp
directory, runs the check over it, and requires a refusal. A gate that has never been shown
to fail is a gate nobody has tested, and this file's whole subject is instruments that
could only ever report clean.
"""
import io
import json
import os
import re
import sys
import glob

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(REPO, "scripts")
BASELINE = os.path.join(SCRIPTS, "baselines", "instrument_control_baseline.json")

# WIDENED AFTER MEASURING ITS OWN REACH. The first version matched a glob literal only and
# saw 12 of the 116 files named audit_/lint_/*_gate. A baseline built from a detector that
# cannot see most of its subject is the same defect one level up, so the walk is recognised
# by any of the ways this repository actually iterates the corpus.
CORPUS_WALK = re.compile(
    r"glob\.glob\([^)]*(?:ssot|figs|evidence|REVIEW)[^)]*\)"
    r"|os\.listdir\([^)]*(?:ssot|figs|SSOT|FIGS|REPO)[^)]*\)"
    r"|os\.walk\("
    r"|for\s+\w+\s+in\s+sorted\(\s*(?:glob|os\.listdir)"
    r"|PAGE_MAP|objects_for_pages|iter_objects|all_objects\(",
    re.S)
PRINTS_A_COUNT = re.compile(r"print\([^)]*%d|print\([^)]*len\(|print\([^)]*\{[^}]*\}", re.S)
HAS_CONTROL = re.compile(r"instrument_controls|require_controls")
EXEMPT = re.compile(r"^\s*#\s*no-control:\s*\S", re.M)


def is_instrument(name):
    return (name.startswith("audit_") or name.startswith("lint_")
            or name.endswith("_gate.py")) and name.endswith(".py")


def scan(scripts_dir):
    """-> (compliant, exempted, offending) lists of basenames."""
    compliant, exempted, offending = [], [], []
    for path in sorted(glob.glob(os.path.join(scripts_dir, "*.py"))):
        name = os.path.basename(path)
        if not is_instrument(name):
            continue
        src = io.open(path, encoding="utf-8", errors="replace").read()
        if not (CORPUS_WALK.search(src) and PRINTS_A_COUNT.search(src)):
            continue
        if HAS_CONTROL.search(src):
            compliant.append(name)
        elif EXEMPT.search(src):
            exempted.append(name)
        else:
            offending.append(name)
    return compliant, exempted, offending


def load_baseline():
    if not os.path.exists(BASELINE):
        return None
    return json.load(io.open(BASELINE, encoding="utf-8"))


def prove():
    """Write an instrument with no control and require this check to refuse it."""
    import tempfile
    import shutil
    tmp = tempfile.mkdtemp(prefix="control_proof_")
    try:
        bad = os.path.join(tmp, "audit_proof_no_control.py")
        io.open(bad, "w", encoding="utf-8", newline="\n").write(
            'import glob\n'
            'rows = glob.glob("ssot/*/*.json")\n'
            'print("found %d things" % len(rows))\n')
        _c, _e, offending = scan(tmp)
        if "audit_proof_no_control.py" not in offending:
            sys.exit("PROOF FAILED: an instrument that walks the corpus, prints a count and "
                     "declares no control was NOT flagged. This check cannot fail and is "
                     "therefore not a check.")
        # And the exemption line must lift it, or the escape hatch does not work either.
        io.open(bad, "w", encoding="utf-8", newline="\n").write(
            '# no-control: proof fixture\n'
            'import glob\n'
            'rows = glob.glob("ssot/*/*.json")\n'
            'print("found %d things" % len(rows))\n')
        _c, exempted, offending = scan(tmp)
        if "audit_proof_no_control.py" in offending or not exempted:
            sys.exit("PROOF FAILED: the `# no-control:` declaration does not lift the "
                     "finding, so the only way past this check is to delete it.")
        print("PROOF PASSED: an uncontrolled corpus instrument is refused, and a declared")
        print("exemption lifts it. Both directions demonstrated on a real file.")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    if "--prove" in sys.argv:
        prove()
        return

    compliant, exempted, offending = scan(SCRIPTS)
    base = load_baseline()

    named = len([n for n in os.listdir(SCRIPTS) if is_instrument(n)])
    seen = len(compliant) + len(exempted) + len(offending)
    print("CORPUS INSTRUMENTS AND THEIR CONTROLS")
    print("    %d files are named audit_/lint_/*_gate; THIS CHECK SEES %d of them -- the"
          % (named, seen))
    print("    rest take a path argument or iterate through a helper and are NOT ASSESSED.")
    print("    That residual is stated rather than counted as clean.")
    print("    route through instrument_controls   %3d" % len(compliant))
    print("    declare `# no-control:` with a why  %3d" % len(exempted))
    print("    NEITHER                             %3d" % len(offending))
    for n in compliant:
        print("        + %s" % n)

    if base is None:
        print("")
        print("NO BASELINE ON DISK. Writing one from the current %d uncontrolled "
              "instruments." % len(offending))
        os.makedirs(os.path.dirname(BASELINE), exist_ok=True)
        json.dump({
            "written": "2026-08-20",
            "why": ("These instruments predate lint_instrument_declares_a_control.py. They "
                    "are NOT excused on the merits -- most of them can only say yes. They "
                    "are excused because rewriting all of them in one unreviewed pass is "
                    "the shape of half the defects in DEFECT-REGISTRY.md. THIS COUNT MUST "
                    "NEVER RISE."),
            "uncontrolled": sorted(offending),
        }, io.open(BASELINE, "w", encoding="utf-8", newline="\n"), indent=1,
            ensure_ascii=False)
        print("wrote %s" % BASELINE)
        return

    known = set(base.get("uncontrolled") or [])
    new = sorted(set(offending) - known)
    healed = sorted(known - set(offending))

    print("")
    print("BASELINE: %d uncontrolled instruments recorded %s"
          % (len(known), base.get("written")))
    if healed:
        print("%d have since gained a control or an exemption: %s"
              % (len(healed), ", ".join(healed)))
    if not new:
        print("NO NEW UNCONTROLLED INSTRUMENT. The baseline has not risen.")
        return

    print("")
    print("REFUSED: %d instrument(s) walk the corpus, print a count, and declare no case "
          "whose" % len(new))
    print("answer is already known:")
    for n in new:
        print("    %s" % n)
    print("")
    print("Route it through instrument_controls.require_controls with a positive control")
    print("and, where it can over-flag, a negative one. If a known-answer case genuinely")
    print("cannot exist for this check, say why in one line: `# no-control: <reason>`.")
    sys.exit(1)


if __name__ == "__main__":
    main()
