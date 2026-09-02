# -*- coding: utf-8 -*-
"""What already EXISTS on a revision, indexed by WHAT IT DOES rather than what it is called.

THE NIGHT THIS WAS BUILT, THREE LANES INDEPENDENTLY REBUILT SOMETHING main ALREADY SHIPPED:
a guideline coverage map, an HTA / Summary-of-Findings projector, and a metafor oracle --
and two lanes wrote the same stdout lint within minutes of each other. Every one was
diagnosed as "the thing is missing" from a stale or partial view, and two of the three were
BETTER on main than in the rebuild.

    THAT IS NOT FOUR MISTAKES. IT IS ONE MISSING CAPABILITY: NO INVENTORY OF WHAT EXISTS.

A NAME-KEYED INDEX WOULD HAVE MISSED ALL OF THEM, AND THAT IS THE WHOLE DESIGN CONSTRAINT.
The symbol sof_card does not contain the string "HTA". The symbol etd_coverage_card does not
contain "guideline". Searching for what you are about to build, BY ITS NAME, returns nothing
and returns it CONFIDENTLY. So this indexes the PROSE a symbol carries -- module docstring,
function docstring, and the comment block directly above it -- because that is where a thing
says what it does. Verified on the case that motivated it: projectors_sof.py opens with "The
HTA tab as a SUMMARY OF FINDINGS table, and the Guideline tab as an EVIDENCE-TO-DECISION
COVERAGE MAP", so both capabilities are findable from their descriptions and neither by name.

WHAT THIS CANNOT DO, STATED ON THE OBJECT RATHER THAN DISCOVERED LATER:
  - It indexes ONE revision. A capability living only on another branch is not here.
    git log --all -S is the tool for that, and on this repo it TIMED OUT at ten minutes,
    which makes any absence it reports a REACH figure and not a coverage figure.
  - It indexes prose. A capability whose code is excellent and whose docstring is empty is
    invisible to it, and will be reported as absent when it is merely undescribed.
  - Absence here means ABSENT FROM WHAT WAS SEARCHED. Every run prints its own reach.

Usage:
  python scripts/capability_index.py --rev origin/main --json CAPABILITY-INDEX.json
  python scripts/capability_index.py --rev origin/main --find "hta summary of findings"
"""
from __future__ import annotations

import argparse
import ast
import io
import json
import os
import re
import subprocess
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, ".."))

INDEXED_EXT = (".py",)
STOP = set("""the a an and or of to in for with by is are be that this it its as on at from
not no any all we our you your they their he she can may will would should must if then than
was were been has have had do does did but so such other into over under only same each
per via using use used which what when where who whom how why one two three first second
new old more most less least very much many few both either neither
def class self return none true false import print str int float list dict set""".split())
TABCH = chr(9)
NLB = chr(10).encode()
TERM = re.compile(r"[a-z][a-z0-9_]{2,}")


def terms(text):
    return {t for t in TERM.findall((text or "").lower()) if t not in STOP}


def rev_blobs(rev):
    """[(path, sha)] for every indexed file at REV, from ls-tree.

    BY SHA, NOT BY `rev:path`, AND THE REASON IS A BUG THIS HAD. The first version wrote
    `rev:path` request lines and walked the reply by offset arithmetic. One desync and every
    subsequent blob is attributed to the WRONG PATH -- which is what happened: the index held
    a projectors_sof.py whose module docstring was empty and whose functions were not the
    ones on main. It reported those contents with total confidence, and nothing in the output
    could show it. Requesting by SHA lets the reply be CHECKED: git echoes the sha it is
    returning, and a mismatch raises instead of being indexed.
    """
    out = subprocess.run(["git", "ls-tree", "-r", rev], cwd=_ROOT,
                         capture_output=True, encoding="utf-8", errors="replace")
    if out.returncode != 0:
        raise SystemExit("REFUSED: cannot list %s -- %s" % (rev, out.stderr.strip()[:140]))
    got = []
    for line in out.stdout.splitlines():
        if "	" not in line:
            continue
        meta, path = line.split("	", 1)
        bits = meta.split()
        if len(bits) < 3 or bits[1] != "blob":
            continue
        if path.strip().endswith(INDEXED_EXT):
            got.append((path.strip(), bits[2]))
    return got


def batch_read(pairs):
    """All blobs in ONE git cat-file --batch. 1388 separate git show calls took 8 minutes.

    Every reply header carries the sha it is answering; it is COMPARED to the sha requested,
    so a desync raises here rather than silently mis-attributing content to a path.
    """
    if not pairs:
        return {}
    proc = subprocess.Popen(["git", "cat-file", "--batch"], cwd=_ROOT,
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    raw, _ = proc.communicate("".join(sha + chr(10) for _p, sha in pairs).encode("ascii"))
    blobs, pos = {}, 0
    for path, sha in pairs:
        nl = raw.find(NLB, pos)
        if nl < 0:
            raise SystemExit("REFUSED: cat-file reply ended early at %s. A truncated reply "
                             "would attribute the remaining blobs to the wrong paths." % path)
        header = raw[pos:nl].decode("utf-8", "replace").strip()
        bits = header.split()
        if len(bits) != 3 or bits[0] != sha or bits[1] != "blob":
            raise SystemExit(
                "REFUSED: cat-file returned %r for %s (%s). The reply is out of step with "
                "the request, and every blob after this point would be indexed under the "
                "wrong path." % (header[:60], path, sha[:12]))
        size = int(bits[2])
        blobs[path] = raw[nl + 1:nl + 1 + size]
        pos = nl + 1 + size + 1
    return blobs


def lead_comment(lines, lineno):
    """The comment block directly above a def -- often where the WHY actually lives."""
    out, i = [], lineno - 2
    while i >= 0 and lines[i].lstrip().startswith("#"):
        out.append(lines[i].lstrip("# ").rstrip())
        i -= 1
    return " ".join(reversed(out))


def _module_prose(tree):
    """Every top-level string literal, not only the one Python calls a docstring.

    ⛔ THE CASE THAT FORCED THIS IS THE WHOLE POINT OF THE FILE. On origin/main,
    ssot/projectors_sof.py begins:

        import re, then the coding comment, then a triple-quoted paragraph beginning
        "The HTA tab as a SUMMARY OF FINDINGS table, and the Guideline tab as an
        EVIDENCE-TO-DECISION COVERAGE MAP".

    One import above the docstring, and it is no longer a docstring -- it is a discarded
    string expression. ast.get_docstring() returns None, CORRECTLY, and every doc-driven
    tool goes blind to the sentence that says what the module does. That is precisely how a
    shipped capability becomes invisible to a search for it, and then gets rebuilt by
    someone who looked and honestly found nothing.

    So prose is taken as prose wherever it sits at top level. The searcher does not care
    which statement position the sentence occupies.
    """
    out = []
    for node in tree.body:
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant)                 and isinstance(node.value.value, str):
            out.append(node.value.value)
    return " ".join(out)


def index_rev(rev):
    pairs = rev_blobs(rev)
    paths = [p for p, _s in pairs]
    blobs = batch_read(pairs)
    rows, unread = [], []
    for p in paths:
        raw = blobs.get(p)
        if raw is None:
            unread.append(p)
            continue
        text = raw.decode("utf-8", "replace")
        try:
            tree = ast.parse(text, filename=p)
        except SyntaxError as exc:
            unread.append("%s (UNPARSABLE: %s)" % (p, str(exc)[:50]))
            continue
        lines = text.splitlines()
        mod_doc = _module_prose(tree)
        rows.append({"path": p, "symbol": "<module>", "kind": "module",
                     "own": mod_doc[:900], "inherited": ""})
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                doc = ast.get_docstring(node) or ""
                # THE MODULE DOC IS CARRIED ONTO EVERY SYMBOL DELIBERATELY. The docstring on
                # sof_card does not say "HTA"; the docstring on its MODULE does, and that is
                # the sentence a searcher will actually type.
                # ORDER AND PER-PART CAPS, AND THE CONTROL IS WHAT FOUND THIS.
                # The first version concatenated own-docstring, lead comment and module
                # docstring IN THAT ORDER and then cut the result at 1200 characters. On
                # sof_card the first two filled the budget, so the MODULE docstring -- the
                # only place the word HTA appears, and the entire reason this field exists --
                # was truncated off the end. The index then reported 6 terms for a symbol
                # whose module says exactly what a searcher would type. A silent truncation
                # that removes precisely the signal the field was designed to carry.
                # Each part is capped SEPARATELY now, and the module doc goes FIRST.
                # OWN PROSE AND INHERITED PROSE ARE KEPT APART, AND THE CONTROL FORCED IT.
                # Carrying the module docstring onto every symbol made every symbol in a
                # file score identically, so _e and _blocks tied with sof_card and won on
                # ordering. Inherited prose says which FILE is relevant; only own prose says
                # which SYMBOL. Scored separately, and inherited counts for less.
                rows.append({"path": p, "symbol": node.name,
                             "kind": "class" if isinstance(node, ast.ClassDef) else "def",
                             "own": (doc[:600] + " || "
                                     + lead_comment(lines, node.lineno)[:400]),
                             "inherited": mod_doc[:600]})
    return rows, unread, len(paths)


def _idf(rows):
    """How rare each term is across the corpus. Built once, from the corpus, not tuned.

    WHY PLAIN OVERLAP FAILED, AND THE CONTROL CAUGHT IT. Querying "HTA tab summary of
    findings table" with every term weighted equally, the right answer TIED with modules that
    merely contain the words table, summary and findings -- which is most of a meta-analysis
    repo -- and lost the tie. The word carrying nearly all the meaning was "hta", which
    appears in a handful of files. Rarity is the signal; equal weighting discards it.
    """
    import math
    df = {}
    for r in rows:
        for t in terms(r["own"] + " " + r["inherited"]):
            df[t] = df.get(t, 0) + 1
    n = max(1, len(rows))
    return {t: math.log(n / float(c)) for t, c in df.items()}, n


def find(rows, query, top=8, idf=None):
    q = terms(query)
    if idf is None:
        idf, _n = _idf(rows)
    # An unseen term is maximally rare, not free: default to the highest weight present.
    default = max(idf.values()) if idf else 1.0
    denom = sum(idf.get(t, default) for t in q) or 1.0
    scored = []
    INHERITED_WEIGHT = 0.55     # enough to rank the right FILE, never the right SYMBOL
    for r in rows:
        own = terms(r["own"])
        inh = terms(r["inherited"]) - own
        hit_own, hit_inh = q & own, q & inh
        if not hit_own and not hit_inh:
            continue
        # Scored on DESCRIPTION overlap only, weighted by rarity, with a symbol judged
        # mainly on what IT says. Name overlap is not scored at all -- name-first ranking
        # is the exact failure this index exists to avoid.
        score = (sum(idf.get(x, default) for x in hit_own)
                 + INHERITED_WEIGHT * sum(idf.get(x, default) for x in hit_inh)) / denom
        scored.append((score, len(hit_own) + len(hit_inh), sorted(hit_own | hit_inh), r))
    scored.sort(key=lambda x: (-x[0], -x[1]))
    return scored[:top]


# THE CONTROL SET. Cases 1-2 were used WHILE building the scorer, so they are development
# data and cannot measure it -- fitting a scorer to the two examples you tuned on proves
# nothing. Case 3 was added AFTER the scorer was finished and has never been tuned against:
# it is the only one of the three whose result is evidence.
CONTROLS = [("guideline coverage map evidence to decision",
             "ssot/projectors_sof.py", "etd_coverage_card", "development"),
            ("HTA tab summary of findings table",
             "ssot/projectors_sof.py", "sof_card", "development"),
            ("refuse a commit that net-deletes content from an SSOT object",
             "scripts/ssot_net_deletion_check.py", None, "HELD OUT")]


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--rev", default="origin/main")
    ap.add_argument("--json", dest="out")
    ap.add_argument("--find")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)

    rows, unread, nfiles = index_rev(a.rev)
    print("INDEXED %s : %d files, %d symbols" % (a.rev, nfiles, len(rows)))
    if unread:
        print("NOT INDEXED (named, never dropped): %d" % len(unread))
        for u in unread[:6]:
            print("   %s" % u[:80])

    if a.selftest:
        # THE CONTROL SET IS REAL WORK REBUILT TONIGHT, WITH ANSWERS KNOWN IN ADVANCE.
        # An index that cannot find the work whose duplication caused it to be written has
        # not been shown to do anything at all.
        bad = 0
        print()
        print("SELFTEST -- capabilities rebuilt tonight, queried BY DESCRIPTION")
        idf, _n = _idf(rows)
        for q, want_path, want_sym, provenance in CONTROLS:
            got = find(rows, q, top=6, idf=idf)
            names = ["%s::%s" % (r["path"], r["symbol"]) for _s, _n2, _h, r in got]
            ok = any(want_path in n and (want_sym is None or want_sym in n) for n in names)
            print("  %s [%s] %-40s -> %s"
                  % ("FOUND " if ok else "MISSED", provenance, q[:40],
                     names[0] if names else "NOTHING"))
            if not ok:
                bad += 1
                for n in names[:4]:
                    print("         also: %s" % n)
        if bad:
            print()
            print("REFUSED: %d control case(s) not found." % bad)
            return 1
        print()
        print("Every control located BY DESCRIPTION. Neither is findable by its name.")
        return 0

    if a.find:
        got = find(rows, a.find)
        print()
        print("ALREADY EXISTS ON %s, MATCHED ON WHAT IT DOES:" % a.rev)
        if not got:
            print("   nothing matched -- and this searched ONE revision, prose only.")
        for score, n, hit, r in got:
            print("   %5.2f  %s::%s" % (score, r["path"], r["symbol"]))
            print("          on: %s" % ", ".join(hit[:8]))
    if a.out:
        with io.open(os.path.join(_ROOT, a.out), "w", encoding="utf-8") as fh:
            json.dump({"_rev": a.rev, "_reach": "%d files indexed" % nfiles,
                       "_not_indexed": unread, "rows": rows}, fh, indent=1)
        print()
        print("written: %s" % a.out)
    return 0


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.exit(main(sys.argv[1:]))
