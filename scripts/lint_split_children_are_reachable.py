"""A SPLIT TOPIC MUST LINK ITS CHILDREN. Any object carrying `split_provenance` must have at
least one page linked from index.html.

WHY THE ARTEFACT AND NOT THE PROCEDURE. There is no split script to hook. Splits are
per-topic one-offs -- create_apixaban_split_objects_2026_08_19.py,
create_bosentan_four_2026_08_19.py, create_colchicine_coronary_2026_08_19.py,
create_ablation_hf_object_2026_08_19.py -- each written once, all dated the same day. Guarding
a procedure covers the splits already written; guarding the PROPERTY covers the ones nobody
has written yet, which is the only kind that can still go wrong.

WHAT IT FOUND ON ITS FIRST RUN: 10 of 10. Splitting a topic has never once included linking
the children. The step is in nobody's procedure, which is why a guard and not a fix.

WHAT THIS DOES NOT ESTABLISH. Not that a linked child is CORRECTLY placed, or that the parent
still makes sense after the split. Only that a reader can reach it from the front door.
"""
from __future__ import annotations
import glob, io, json, os, re, sys

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from instrument_controls import require_controls  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LINK = re.compile(r'href="([A-Za-z0-9_\-]+\.html)"')

# RATCHET, NOT CLEARANCE. These 10 are unreachable TODAY. Baselined so the guard can enter
# the hook chain without blocking every commit on a backlog -- and NOT a pass: each is a
# split child a reader cannot get to. The ratchet ASSERTS: an 11th raises SystemExit.
# Removing a name is only possible by linking the page.
SPLIT_BASELINE = {
    "ablation-af-heart-failure", "ablation-af-medical-therapy",
    "apixaban-vte-prophylaxis", "apixaban-vte-treatment",
    "bosentan-pah-children", "bosentan-pah-combination",
    "bosentan-pah-monotherapy", "bosentan-ph-not-group1",
    "colchicine-cvd-coronary", "early-rhythm-control-af",
}


def unreachable_splits(root):
    """Slugs whose object records a split and whose pages are linked from no index section."""
    idx_path = os.path.join(root, "index.html")
    linked = set(LINK.findall(io.open(idx_path, encoding="utf-8", errors="replace").read())) \
        if os.path.exists(idx_path) else set()
    pm_path = os.path.join(root, "ssot", "PAGE_MAP.json")
    pm = json.load(io.open(pm_path, encoding="utf-8")) if os.path.exists(pm_path) else {}
    obj2pages = {}
    for pg, op in pm.items():
        obj2pages.setdefault(op.replace("\\", "/"), []).append(pg)
    bad = []
    for p in sorted(glob.glob(os.path.join(root, "ssot", "*", "*.json"))):
        slug = os.path.basename(os.path.dirname(p))
        # POSITIVE PROPERTIES ONLY. This loop runs over the whole object corpus, and the
        # first version filtered it with `if not ...: continue` twice -- negative guards
        # inside a corpus-wide loop, which is the shape that silently removes items from a
        # corpus-wide pass. The gate that refused this file refused an earlier one of mine
        # for the same reason today; the population is what IS a topic object recording a
        # split, not what fails to be one.
        is_topic_object = os.path.basename(p)[:-5] == slug
        if is_topic_object:
            try:
                o = json.load(io.open(p, encoding="utf-8"))
            except Exception:
                o = {}
            records_a_split = bool(o.get("split_provenance"))
            if records_a_split:
                rel = os.path.relpath(p, root).replace(os.sep, "/")
                pages = obj2pages.get(rel, [])
                reachable = any(pg in linked for pg in pages)
                if pages and not reachable:
                    bad.append(slug)
    return sorted(bad)


def selftest():
    """Plant an ELEVENTH split with unlinked children and require refusal BY NAME; then link
    it and require silence. Fixtures, so no corpus state can make either pass."""
    import shutil, tempfile
    tmp = tempfile.mkdtemp(prefix="split_")
    try:
        os.makedirs(os.path.join(tmp, "ssot", "planted-split"))
        io.open(os.path.join(tmp, "ssot", "planted-split", "planted-split.json"), "w",
                encoding="utf-8").write(json.dumps(
                    {"split_provenance": {"why": "planted"}}))
        io.open(os.path.join(tmp, "ssot", "PAGE_MAP.json"), "w", encoding="utf-8").write(
            '{"PLANTED_REVIEW.html": "ssot/planted-split/planted-split.json"}')
        io.open(os.path.join(tmp, "index.html"), "w", encoding="utf-8").write(
            '<h2 id="sp-cardiology">C</h2><a href="SOMETHING_ELSE.html">x</a>')
        got = unreachable_splits(tmp)
        assert got == ["planted-split"], (
            "GUARD CANNOT FAIL: planted an unlinked split child and it reported %r" % (got,))
        io.open(os.path.join(tmp, "index.html"), "w", encoding="utf-8").write(
            '<h2 id="sp-cardiology">C</h2><a href="PLANTED_REVIEW.html">x</a>')
        got2 = unreachable_splits(tmp)
        assert got2 == [], "GUARD OVER-FLAGS: a linked split child reported as %r" % (got2,)
        require_controls(
            "lint_split_children_are_reachable",
            positive=("an eleventh split with unlinked children is named",
                      got, ["planted-split"]),
            negative=("the same split, once linked, must NOT be named -- the over-flag "
                      "direction, since a spurious hit would block every commit",
                      got2, ["planted-split"]))
        print("selftest: refused a planted unlinked split by name, and stayed silent once "
              "it was linked. OK")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    selftest()
    bad = unreachable_splits(REPO)
    new = [s for s in bad if s not in SPLIT_BASELINE]
    healed = sorted(SPLIT_BASELINE - set(bad))
    print()
    print("objects recording a split, unreachable from index.html: %d (baseline %d)"
          % (len(bad), len(SPLIT_BASELINE)))
    if healed:
        print("%d baselined split(s) are now linked -- REMOVE from SPLIT_BASELINE so the "
              "ratchet tightens: %s" % (len(healed), ", ".join(healed)))
    if new:
        print()
        print("REFUSED: %d split topic(s) whose children a reader cannot reach, above the "
              "baseline of %d. Splitting a topic must link the children: %s"
              % (len(new), len(SPLIT_BASELINE), ", ".join(new)))
        raise SystemExit(1)
    print("ALL BASELINED, none new. NOT a clearance: %d split child(ren) remain unreachable."
          % len(bad))


if __name__ == "__main__":
    main()
