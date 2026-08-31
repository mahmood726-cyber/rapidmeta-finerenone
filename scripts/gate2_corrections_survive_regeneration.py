r"""GATE 2: prove a correction survives a regeneration, BEFORE regenerating.

THE STANDING WARNING THIS TESTS
    "Regeneration would erase every retraction." It has never been tested.
    A regeneration that silently eats the corrections is INDISTINGUISHABLE
    from one that had nothing to eat -- both leave a corrections directory
    that looks fine to whoever is running the build, and the difference only
    surfaces when a reader goes looking for a retraction that is gone.

    So this does not reason about the code. It plants a correction, runs a
    real forced regeneration over a real page, and looks.

WHAT IS PLANTED, AND WHY BOTH HALVES ARE NEEDED
    PLANT A -- the danger is REAL. A retraction note is written INSIDE a real
        sidecar JSON, which is the obvious and tempting place to put one.
        The regeneration is then run over that sidecar. The note must be
        GONE afterwards. If it survived, the warning would be theoretical
        and this whole gate would be ceremony. It does not survive:
        emit_sidecar() rebuilds the object from the page and writes the file
        whole, so anything added to the JSON is discarded.

    PLANT B -- our design SURVIVES. A correction file is written into
        corrections/ and the same regeneration is run. The file must still
        be present and byte-identical afterwards.

    Plant A is what makes plant B mean something. Without it, "the file was
    still there" is equally consistent with a regeneration that never
    touched anything at all.

    PLANT C -- the honest limit. A correction that survives on disk but that
        no reader ever sees is not a correction. This checks whether any
        build path renders corrections/ onto a served surface, and reports
        the answer either way rather than assuming it.

SAFETY
    Every file this touches is captured byte-for-byte first and restored in
    a finally path, with the restoration proven by sha256. ARNI and the three
    CONCLUSION_FLIPS artefacts are excluded from selection outright.
"""
from __future__ import annotations
import glob
import hashlib
import io
import json
import os
import re
import shutil
import sys
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

CORRECTIONS = os.path.join(ROOT, "corrections")
SIDECAR_DIR = os.path.join(ROOT, "outputs", "r_validation")

# Never selected as the guinea pig. ARNI and the HFrEF NMA are protected by
# standing instruction; the three flip artefacts are the retraction set and
# must not be perturbed while their corrections are being drafted.
PROTECTED = {"ARNI_HF", "ARNI_HFREF", "BIMEKIZUMAB_AS_AUTO_FULL",
             "BIMEKIZUMAB_AXIAL_AUTO_FULL", "VANDETANIB_LUNG_AUTO_FULL"}

results = []


def sha(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def record(name, expectation, ok):
    results.append((name, expectation, ok))
    print("    %s" % ("PLANT CAUGHT: " + expectation if ok else
                      "PLANT MISSED (this gate has only one reachable "
                      "outcome): " + expectation))


def classify_page(page, bbs):
    """Name what a page IS, for the purpose of choosing ONE guinea pig.

    Positive form: every page gets a name, and the names partition the
    population. This loop SELECTS a target rather than REPORTING a
    population, so nothing is being silently dropped from a count -- but it
    is written so that is visible rather than asserted, and the partition is
    printed and checked to sum.
    """
    stem = bbs.sidecar_stem(page.name)
    if stem in PROTECTED:
        return "protected", stem
    if os.path.exists(os.path.join(SIDECAR_DIR, stem + ".json")):
        try:
            trials = bbs.extract_binary_trials(page)
        except Exception:
            return "unextractable", stem
        if len(trials) >= 2:
            return "eligible", stem
        return "too_few_trials", stem
    return "no_served_sidecar", stem


def pick_target():
    """Partition every page, print the partition, return the first eligible.

    Returns (page, stem, sidecar_path, partition).
    """
    import build_binary_sidecar as bbs
    partition = {}
    chosen = None
    pages = sorted(Path(ROOT).glob("*_FULL_REVIEW.html"))
    for page in pages:
        kind, stem = classify_page(page, bbs)
        partition.setdefault(kind, []).append(stem)
        if kind == "eligible" and chosen is None:
            chosen = (page, stem, os.path.join(SIDECAR_DIR, stem + ".json"))
    total = sum(len(v) for v in partition.values())
    print("PAGE PARTITION (a selection, and it sums to the population)")
    for k in sorted(partition):
        print("  %-20s %d" % (k, len(partition[k])))
    print("  %d classified == %d pages : %s"
          % (total, len(pages), "HOLDS" if total == len(pages) else "FAILS"))
    print("")
    if chosen is None:
        return None, None, None, partition
    return chosen[0], chosen[1], chosen[2], partition


def main():
    print("GATE 2 -- DOES A CORRECTION SURVIVE A REGENERATION?")
    print("Nothing is reasoned about here. A correction is planted, a real")
    print("forced regeneration is run over a real page, and the result is")
    print("looked at.\n")

    import build_binary_sidecar as bbs
    page, stem, sc_path, _partition = pick_target()
    if page is None:
        print("NO TARGET FOUND -- this gate measured the harness, not the "
              "build. NO VERDICT.")
        return 2
    print("target page   : %s" % page.name)
    print("target sidecar: outputs/r_validation/%s.json\n" % stem)

    sc_before_bytes = open(sc_path, "rb").read()
    sc_before_sha = hashlib.sha256(sc_before_bytes).hexdigest()

    # ---------------------------------------------------------- PLANT A
    print("[A] A RETRACTION NOTE PLACED INSIDE THE SIDECAR JSON")
    try:
        obj = json.loads(sc_before_bytes.decode("utf-8"))
        obj["RETRACTION_NOTE_PLANTED"] = (
            "This pool is retracted. If you can still read this after a "
            "regeneration, in-file retractions survive.")
        with io.open(sc_path, "w", encoding="utf-8") as fh:
            json.dump(obj, fh, indent=2)
        planted_ok = "RETRACTION_NOTE_PLANTED" in open(
            sc_path, encoding="utf-8").read()
        print("    note written into the sidecar: %s" % planted_ok)
        r = bbs.emit_sidecar(page, force=True)
        print("    regeneration status: %s" % r.get("status"))
        after = open(sc_path, encoding="utf-8").read()
        gone = "RETRACTION_NOTE_PLANTED" not in after
        print("    note present after regeneration: %s" % (not gone))
        record("an in-file retraction is DESTROYED by regeneration",
               "the note is gone, so the standing warning describes a real "
               "mechanism and not a hypothetical one", gone and planted_ok)
    finally:
        with open(sc_path, "wb") as fh:
            fh.write(sc_before_bytes)
        ok = sha(sc_path) == sc_before_sha
        print("    restore: sha256 %s -> %s"
              % (sc_before_sha[:12], "BYTE-IDENTICAL" if ok else "*** DIFFERS ***"))

    # ---------------------------------------------------------- PLANT B
    print("\n[B] A CORRECTION FILE IN corrections/, THROUGH THE SAME "
          "REGENERATION")
    made_dir = not os.path.isdir(CORRECTIONS)
    os.makedirs(CORRECTIONS, exist_ok=True)
    probe = os.path.join(CORRECTIONS, "__gate2_probe__.md")
    body = ("# GATE 2 PROBE\n\nPlanted to test whether a regeneration erases "
            "corrections.\nIf this file is missing after a regeneration, "
            "every retraction is at risk.\n")
    existing = sorted(os.path.basename(p) for p in
                      glob.glob(os.path.join(CORRECTIONS, "*.md")))
    try:
        with io.open(probe, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(body)
        probe_sha = sha(probe)
        print("    probe written, sha256 %s" % probe_sha[:12])
        print("    real corrections present before: %d %s"
              % (len(existing), existing))
        sc2 = open(sc_path, "rb").read()
        r = bbs.emit_sidecar(page, force=True)
        print("    regeneration status: %s" % r.get("status"))
        survived = os.path.exists(probe)
        identical = survived and sha(probe) == probe_sha
        still = sorted(os.path.basename(p) for p in
                       glob.glob(os.path.join(CORRECTIONS, "*.md")))
        kept_real = all(e in still for e in existing)
        print("    probe survived: %s   byte-identical: %s" % (survived, identical))
        print("    real corrections still present: %s %s"
              % (kept_real, [e for e in existing if e not in still] or ""))
        record("a correction in corrections/ SURVIVES regeneration",
               "the probe and every real correction are still present and "
               "byte-identical", survived and identical and kept_real)
    finally:
        if os.path.exists(probe):
            os.remove(probe)
        with open(sc_path, "wb") as fh:
            fh.write(sc_before_bytes)
        ok = sha(sc_path) == sc_before_sha
        print("    restore: sidecar %s"
              % ("BYTE-IDENTICAL" if ok else "*** DIFFERS ***"))
        if made_dir and os.path.isdir(CORRECTIONS) and not os.listdir(CORRECTIONS):
            os.rmdir(CORRECTIONS)

    # ---------------------------------------------------------- PLANT C
    print("\n[C] DOES ANYTHING RENDER A CORRECTION TO A READER?")
    # THE PATTERN MUST MATCH A PATH, NOT THE WORD.
    # A first version of this check accepted ["']corrections["'] and matched
    # the PROSE on line 1 of scripts/revert_wrong_pmid_fixes.py -- a file
    # that reads outputs/pmid_corrections_applied.csv and has nothing to do
    # with corrections/. That single false hit turned a real gap into a
    # PASS: the check reported that a rendering path exists when none does.
    # An unanchored substring is the commonest defect in this repository and
    # it failed in the flattering direction here, which is the dangerous one.
    #
    # So: require a directory separator after the word, or a path-join with
    # it as a quoted segment. Both quote styles and both separators are
    # accepted, because assuming one of those is the OTHER commonest defect.
    pat = re.compile(
        r"""corrections[/\\]"""                       # corrections/ or corrections\
        r"""|["']corrections["']\s*[,)]"""            # join(..., "corrections")
        r"""|\bCORRECTIONS(_DIR)?\s*=""",             # a module-level constant
        re.I)
    hits = []
    for root, _d, names in os.walk(os.path.join(ROOT, "scripts")):
        for nm in sorted(names):
            if not nm.endswith((".py", ".R", ".js")):
                continue
            fp = os.path.join(root, nm)
            if os.path.abspath(fp) == os.path.abspath(__file__):
                continue
            try:
                src = io.open(fp, encoding="utf-8", errors="replace").read()
            except Exception:
                continue
            if pat.search(src):
                hits.append(os.path.relpath(fp, ROOT))
    print("    files referencing a corrections path: %d" % len(hits))
    for h in hits[:10]:
        print("      %s" % h)
    if hits:
        print("    -> a rendering path exists and must be checked separately")
    else:
        print("    -> NOTHING renders corrections/ to a reader. The "
              "corrections SURVIVE a regeneration, but no served surface "
              "shows them. That is a REAL GAP and is reported as one rather")
        print("       than being dressed up as a passing render check.")
    results.append(("a reader can actually see a correction",
                    "some build path renders corrections/", bool(hits)))

    print("\n" + "=" * 68)
    print("GATE 2 SUMMARY")
    bad = 0
    for name, expect, ok in results:
        print("  %-52s %s" % (name, "PASS" if ok else "FAIL"))
        if not ok:
            bad += 1
    print("  %d of %d" % (len(results) - bad, len(results)))
    if bad:
        print("\n  A FAIL here is a finding, not a formality. Read it before")
        print("  regenerating anything.")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
