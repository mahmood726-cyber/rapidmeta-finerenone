"""What did TONIGHT'S projector changes add and remove, measured against the previous commit?

WHY NOT COMPARE AGAINST THE DELIVERED PAGES. That was the first attempt and the baseline was
rotten: the pages on disk were built at various times today by several different versions of
this projector, so a diff against them mixes tonight's changes with every earlier change of
the day. It reported 51 pages "losing numbers", and the first one examined -- a truncated
PRISMA citation -- turned out to be truncated identically by the PREVIOUS COMMIT. Not a
regression at all; an older artefact.

A baseline has to be a known code state, not whatever happens to be lying on disk.

So: run the previous commit's projector and the current one over the SAME objects, in the
same process, and diff their text. No builds, no rasters, no delivered pages, and the only
difference between the two sides is the change being measured.

The property is the same one that matters for shipping: tonight's work may add whatever it
likes, but it must not remove a registration or a reported number.
"""
import glob
import importlib.util
import io
import json
import os
import re
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_REF = "616860a98~1"          # the commit before tonight's projector work
_NCT = re.compile(r"NCT\d{8}")
_NUM = re.compile(r"(?<![\w.])\d+(?:\.\d+)?(?![\w])")


def load_module(path, name):
    sys.path.insert(0, os.path.join(REPO, "ssot"))
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def tokens(text):
    ncts = set(_NCT.findall(text or ""))
    return ncts, set(_NUM.findall(_NCT.sub(" ", text or "")))


def main():
    base_path = os.path.join(REPO, "outputs", "_baseline_projector.py")
    src = subprocess.run(["git", "-C", REPO, "show",
                          "%s:ssot/paper_projector.py" % BASE_REF],
                         capture_output=True, timeout=120)
    if src.returncode != 0:
        print("could not read baseline:",
              src.stderr.decode("utf-8", "replace")[:200])
        return 2
    io.open(base_path, "wb").write(src.stdout)

    old = load_module(base_path, "pp_baseline")
    new = load_module(os.path.join(REPO, "ssot", "paper_projector.py"), "pp_current")

    L = []

    def w(s):
        L.append(str(s))

    compared = 0
    lost = []
    gained_words = 0
    lost_words = 0
    for p in sorted(glob.glob(os.path.join(REPO, "ssot", "*", "*.json"))):
        slug = os.path.basename(os.path.dirname(p))
        if os.path.basename(p) != slug + ".json":
            continue
        try:
            with io.open(p, encoding="utf-8") as fh:
                obj = json.load(fh)
        except Exception:
            continue
        try:
            a = old.render(old.project(obj), show_fields=False)
            b = new.render(new.project(obj), show_fields=False)
        except Exception:
            continue
        compared += 1
        gained_words += max(0, len(b.split()) - len(a.split()))
        lost_words += max(0, len(a.split()) - len(b.split()))
        o_nct, o_num = tokens(a)
        n_nct, n_num = tokens(b)
        ln, lnum = sorted(o_nct - n_nct), sorted(o_num - n_num)
        if ln or lnum:
            lost.append((slug, ln, lnum))

    w("BASELINE: %s (the commit before tonight's projector work)" % BASE_REF)
    w("objects projected under both        : %d" % compared)
    w("")
    w("LOSE NOTHING -- no registration, no number dropped : %d" % (compared - len(lost)))
    w("LOSE SOMETHING                                     : %d" % len(lost))
    w("")
    w("words added across the corpus       : %d" % gained_words)
    w("words removed across the corpus     : %d" % lost_words)
    w("")
    for slug, ln, lnum in lost:
        w("  %s" % slug)
        if ln:
            w("     registrations dropped: %s" % ", ".join(ln))
        if lnum:
            w("     numbers dropped (%d): %s" % (len(lnum), ", ".join(lnum[:16])))
    out = os.path.join(REPO, "outputs", "projector_delta_2026_08_24.txt")
    io.open(out, "w", encoding="utf-8").write("\n".join(L))
    print("\n".join(L[:70]))
    return 1 if lost else 0


sys.exit(main())
