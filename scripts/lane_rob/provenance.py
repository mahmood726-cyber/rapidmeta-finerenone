# -*- coding: utf-8 -*-
"""Stamp every artefact this lane hands to another lane.

THE FAILURE THIS CLOSES. My artefacts were regenerated at 02:17 while another lane was
computing on the 02:07 versions -- SUPERSEDED 55 -> 5, HAS_STORE 94 -> 166, legacy 860 -> 797
-- and nothing warned anyone, because the JSON carried no version of its own. The consuming
side has since begun stamping its inputs with size, sha256 and mtime, which detects the
problem one step too late: it can tell that a file changed, not what produced it or whether
the producer was the current one.

Same class as the build stamp, one layer up. A build stamp names the generator a page must be
rebuilt with; this names the script, commit and inputs an artefact was derived from. An
artefact that cannot say what it is can only be trusted by the process that made it.

WRITTEN AS A SIDECAR, DELIBERATELY. Embedding a provenance record inside the array would
change the shape every consumer already parses, and silently turning a data row into a header
is precisely the kind of break this is meant to prevent. The sidecar is additive: consumers
that ignore it are unaffected, and consumers that read it get size, sha256, mtime, the
producing script, the git commit, whether the tree was dirty, and the same three facts for
every input the artefact was derived from.
"""
import hashlib
import io
import json
import os
import subprocess
import sys


def _facts(path):
    try:
        st = os.stat(path)
    except OSError:
        return {"path": path, "present": False}
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return {"path": path, "present": True, "bytes": st.st_size,
            "sha256": h.hexdigest(), "mtime": int(st.st_mtime)}


def _git(args, cwd):
    try:
        r = subprocess.run(["git"] + args, cwd=cwd, capture_output=True, timeout=60)
        return r.stdout.decode("utf-8", "replace").strip() if r.returncode == 0 else None
    except Exception:
        return None


def stamp(out_path, inputs=(), repo=None, note=None):
    """Write <out_path>.prov.json describing out_path and everything it was derived from."""
    root = repo or os.getcwd()
    rec = {
        "artefact": _facts(out_path),
        "produced_by": os.path.basename(sys.argv[0]) or "<interactive>",
        # THE ARGUMENTS ARE PART OF THE PRODUCTION AND WERE NOT RECORDED. A scoped run of
        # adjudication_triage.py (one topic) overwrote the corpus-wide artefact, and this
        # sidecar reported it UNCHANGED and VALID -- correctly, by its own definition, since
        # the file matched its own hash and its inputs had not moved. A cost model built on
        # it understated disagreements by 22x before the regeneration caught it. Same defect
        # as a page naming its generator and not its object: the record described how the
        # artefact was made and not what it was made ABOUT.
        "argv": list(sys.argv[1:]),
        "produced_by_path": os.path.abspath(sys.argv[0]) if sys.argv and sys.argv[0] else None,
        "git_commit": _git(["rev-parse", "HEAD"], root),
        # A CLEANLINESS CHECK THAT COUNTS UNTRACKED BUILD OUTPUT CAN NEVER RETURN CLEAN IN
        # A REPO THAT BUILDS. This read `git status --porcelain` with no
        # --untracked-files=no, so 27 unignored, regenerable figure exports made git_dirty
        # true on EVERY record this lane wrote, permanently -- and a stamp that is always
        # dirty carries no information at all. Ignoring those particular files fixed the
        # instance; this fixes the class, so the next unignored artefact does not reproduce
        # it.
        #
        # Both facts are reported rather than one verdict: modified TRACKED files are a
        # statement about the source the artefact was built from, which is what provenance
        # is for. Untracked files are a statement about the working directory, which is
        # usually build output. They are different claims and are no longer summed.
        "git_dirty": bool(_git(["status", "--porcelain", "--untracked-files=no"], root)),
        "git_untracked": len([ln for ln in
                              (_git(["status", "--porcelain", "--untracked-files=all"], root)
                               or "").splitlines() if ln.startswith("??")]),
        "inputs": [_facts(p) for p in inputs],
        "note": note,
    }
    side = out_path + ".prov.json"
    io.open(side, "w", encoding="utf-8").write(json.dumps(rec, indent=1))
    return side


def check(path, expect_commit=None):
    """Read a sidecar and say, in words, whether the artefact still matches it."""
    side = path + ".prov.json"
    if not os.path.exists(side):
        return False, "no provenance sidecar: this artefact cannot say what produced it"
    rec = json.load(io.open(side, encoding="utf-8"))
    now = _facts(path)
    was = rec.get("artefact") or {}
    if now.get("sha256") != was.get("sha256"):
        return False, ("the artefact has been rewritten since it was stamped -- sha256 %s "
                       "now, %s when stamped by %s"
                       % (str(now.get("sha256"))[:12], str(was.get("sha256"))[:12],
                          rec.get("produced_by")))
    for i in rec.get("inputs") or []:
        cur = _facts(i["path"])
        if cur.get("sha256") != i.get("sha256"):
            return False, ("an INPUT changed since this artefact was produced: %s"
                           % i["path"])
    if expect_commit and rec.get("git_commit") != expect_commit:
        return False, "produced at commit %s, not %s" % (rec.get("git_commit"), expect_commit)
    return True, "artefact and all %d input(s) unchanged since production by %s at %s" % (
        len(rec.get("inputs") or []), rec.get("produced_by"), str(rec.get("git_commit"))[:9])
