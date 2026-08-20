"""Branches in our gates keyed on a marker the corpus does not produce.

THE FINDING THIS GENERALISES, and it is above the population it belongs to.

`scripts/regression_check.py` carried a three-state path for a withdrawn pooled estimate,
keyed on `name="rapidmeta:pooled-estimate" content="NONE"`. MEASURED 2026-08-20: **ZERO
pages in the corpus emit that tag.** The design was right, the implementation was present,
and it had executed ZERO TIMES -- while the two-state path beside it scored every honest
withdrawal as a breakage.

That is the unproven-guard class in its purest form. Not a guard that would have failed --
A GUARD THAT COULD NOT FIRE, inside the instrument whose verdicts we trusted, invisible
because the check's output looked identical either way.

THE PATTERN IS A CONTRACT AGREED ON ONE SIDE ONLY. The checker was told pages would declare
a withdrawal by meta tag. No builder was ever told to emit one. Both halves are internally
consistent and they were never introduced to each other.

WHAT THIS FLAGS. Distinctive string literals used as MARKERS in gates, lints and projectors
-- the argument of an `in` test, an equality, or a regex -- that appear NOWHERE in the
delivered pages or the objects. Each is a branch that has never been taken.

IT IS A READING LIST, NOT A DEFECT COUNT -- the same discipline as the 16 shape-flagged
resolvers. A marker may be absent because the condition is genuinely rare, because it
guards a future format, or because it is dead. Only reading each settles which, and this
file does not claim to have done that.
"""
import io
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Files whose job is to CHECK or RENDER -- where a never-taken branch matters.
def gate_files():
    out = []
    for d, pats in ((os.path.join(REPO, "scripts"),
                     ("gate", "lint_", "regression_check", "verify_", "audit_")),
                    (os.path.join(REPO, "ssot"),
                     ("projector", "guard", "build_", "assessment", "validate"))):
        if not os.path.isdir(d):
            continue
        for nm in sorted(os.listdir(d)):
            if nm.endswith(".py") and any(p in nm for p in pats):
                out.append(os.path.join(d, nm))
    return out


# A marker: a quoted literal long enough to be distinctive, used in a membership or
# equality test. Short or generic literals are excluded -- they match everything.
MARKER = re.compile(
    r"""(?:if|elif|and|or|not|assert)\s[^\n]*?["']([^"'\n]{14,90})["'][^\n]*?"""
    r"""(?:\sin\s|\s==\s|\.search|\.match|\.find)""")
MARKER2 = re.compile(r"""["']([^"'\n]{14,90})["']\s+in\s+""")
GENERIC = re.compile(r"^[\w\s]{0,8}$|^[/\\.\-_]+$|^\s*$")


def corpus_text():
    """Delivered pages and objects, concatenated once."""
    blobs = []
    n_pages = n_objs = 0
    for f in sorted(os.listdir(REPO)):
        if f.endswith("_REVIEW.html") and os.path.getsize(os.path.join(REPO, f)) > 40000:
            blobs.append(io.open(os.path.join(REPO, f), encoding="utf-8",
                                 errors="replace").read())
            n_pages += 1
    ssot = os.path.join(REPO, "ssot")
    for nm in sorted(os.listdir(ssot)):
        p = os.path.join(ssot, nm, nm + ".json")
        if os.path.exists(p):
            blobs.append(io.open(p, encoding="utf-8", errors="replace").read())
            n_objs += 1
    return "\n".join(blobs), n_pages, n_objs


def main():
    files = gate_files()
    if not files:
        print("NOT_ASSESSABLE: found no gate, lint or projector files.")
        return 2
    corpus, n_pages, n_objs = corpus_text()
    if not corpus:
        print("NOT_ASSESSABLE: read no pages and no objects; a marker cannot be shown "
              "absent from a corpus that was not loaded.")
        return 2

    found = {}
    for fp in files:
        try:
            src = io.open(fp, encoding="utf-8", errors="replace").read()
        except Exception:
            continue
        rel = os.path.relpath(fp, REPO).replace("\\", "/")
        for rx in (MARKER, MARKER2):
            for m in rx.finditer(src):
                lit = m.group(1)
                if GENERIC.match(lit) or lit.startswith(("http", "%", "{")):
                    continue
                if "/" in lit and "." in lit:          # a path, not a page marker
                    continue
                found.setdefault(lit, set()).add(rel)

    absent = {lit: fs for lit, fs in found.items() if lit not in corpus}
    print("gate / lint / projector files read      %d" % len(files))
    print("pages and objects loaded                %d pages, %d objects" % (n_pages, n_objs))
    print("distinct marker literals tested         %d" % len(found))
    print("MARKERS ABSENT FROM THE WHOLE CORPUS    %d   <- branches never taken" % len(absent))
    print()
    if absent:
        print("%-58s %s" % ("marker", "where it is tested"))
        print("-" * 128)
        for lit, fs in sorted(absent.items(), key=lambda kv: kv[0].lower())[:60]:
            print("%-58s %s" % (lit[:58], ", ".join(sorted(fs))[:64]))
        if len(absent) > 60:
            print("... +%d more" % (len(absent) - 60))
        print()
    print("A READING LIST, NOT A DEFECT COUNT. A marker may be absent because the condition")
    print("is genuinely rare, because it guards a format not yet emitted, or because the")
    print("branch is dead. THE ONE CONFIRMED INSTANCE is regression_check.py's")
    print("`rapidmeta:pooled-estimate` path: present, correct, and never once executed,")
    print("while the branch beside it mis-scored 99 candidate pages.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
