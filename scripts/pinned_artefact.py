"""Read an artefact AS IT WAS, and carry its identity with every observation.

THE CLASS THIS CLOSES. On 2026-08-25 an adjudicator refuted a claim by quoting the FIX that
had been applied between the claim being raised and the claim being judged. Both were right
about the bytes they saw; the verdict was worthless. A corpus rebuild had touched 152 pages in
that window, so all 38 verdicts were affected and none could be partitioned into "refuted
because wrong" and "refuted because fixed".

    A PAGE NAME IS NOT AN ARTEFACT IDENTITY. A PAGE NAME PLUS A SHA IS.

And the general form, which is five faces of one problem: nearly every correction this week
was a number that was accurate about a DIFFERENT THING than it appeared to describe --

    a different population   five pages that were fifteen
    a different denominator  records retrieved vs full text
    a different factor       judge spread that was a raiser effect
    a different design cell  balanced in aggregate, confounded per unit
    a different POINT IN TIME  this one

So an observation must carry the identity of what it observed. Not the name -- the identity.

USE:

    from pinned_artefact import pin, read_pinned
    sha = pin()                       # the commit the run is reading, recorded once
    text = read_pinned(path, sha)     # bytes as of that commit, not as of now
    record = {..., "artefact_sha": sha, "artefact_path": path}

`read_pinned` REFUSES rather than falling back to the working tree. A silent fallback would
reintroduce exactly the defect: the caller would believe it read a pinned artefact and would
have read whatever is on disk now.
"""
import os
import subprocess

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class NotPinned(Exception):
    pass


def pin(repo=REPO):
    """The commit this run reads. Record it beside every observation the run produces."""
    r = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, cwd=repo, timeout=30)
    if r.returncode != 0:
        raise NotPinned("git rev-parse failed; a run that cannot name its commit must not "
                        "record observations as if it could")
    sha = r.stdout.decode("utf-8", "replace").strip()
    dirty = subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"],
                           capture_output=True, cwd=repo, timeout=60)
    if (dirty.stdout or b"").strip():
        # NOT an error -- a dirty tree is normal mid-session -- but the caller must know the
        # sha does not fully describe what is on disk.
        return sha + "+dirty"
    return sha


def read_pinned(path, sha, repo=REPO):
    """The artefact's bytes AS OF `sha`. Raises rather than falling back to the worktree."""
    if not sha:
        raise NotPinned("no sha supplied; refusing to read the working tree and call it pinned")
    base = sha.replace("+dirty", "")
    rel = os.path.relpath(os.path.abspath(path), repo).replace(os.sep, "/")
    r = subprocess.run(["git", "show", "%s:%s" % (base, rel)],
                       capture_output=True, cwd=repo, timeout=60)
    if r.returncode != 0:
        raise NotPinned("%s does not exist at %s. The artefact this observation is about "
                        "cannot be read as it was, so no observation is recorded." % (rel, base[:9]))
    return r.stdout.decode("utf-8", "replace")


def same_artefact(rec_a, rec_b):
    """True only if two observations are about the same bytes.

    A comparison across two records with different `artefact_sha` is a comparison across a
    rebuild, and must either be pinned or reported as not separable.
    """
    a, b = rec_a.get("artefact_sha"), rec_b.get("artefact_sha")
    if not a or not b:
        return None          # unknown is not no
    return a == b
