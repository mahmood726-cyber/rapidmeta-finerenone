"""GATE 7 -- count the blast radius before editing a file more than one topic builds through.

THE INSTANCE. A worker briefed for per-page work edited `ssot/build_tabbed.py`, verified the
result on the one object it was looking at, and the change reached fifteen. Nothing was
dishonest: the verification was real, it was simply of the wrong denominator. The worker never
had a number for how many topics the file it was editing could reach, because nothing produces
one.

SO THIS PRODUCES ONE, and refuses the edit until it has been acknowledged WITH THE COUNT. You
cannot acknowledge without having been told the number, which is the whole mechanism: the
acknowledgement is not a promise to be careful, it is evidence that the count was seen.

HOW RADIUS IS DERIVED -- and the inversion at the centre of it:

    ssot/<topic>/...              radius = that one topic
    module IN the corpus closure  radius = EVERY topic, whether or not it names any
                                  (closure = page builders AND object writers)
    module outside it, naming N   radius = those N topics
    module outside it, naming 0   radius = 0 (tooling; reaches no reader)

MEMBERSHIP OF THE BUILD CLOSURE DECIDES, AND NAMING A TOPIC NEVER NARROWS A BUILD MODULE.
The first derivation tested naming first and gave `build_tabbed.py` a radius of SIX, because
it mentions six topic ids in special-case branches. It builds all 155. A generator that
special-cases six topics is not a six-topic file, and reading those mentions as a narrowing is
the same reasoning that let a per-page brief edit a class-wide generator: the file looked
specific because it named specific things.

The closure is the import graph rooted at the page builders, so a module qualifies by being
REACHABLE FROM A BUILD, not by living in a directory. A self-check asserts each build root
comes out at the full corpus size, keyed to a fact established outside the derivation -- the
page builders build the corpus -- because an under-reported radius reads as reassurance.
"""
from __future__ import annotations

import ast
import collections
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _harness as H                                                        # noqa: E402

# TWO KINDS OF ROOT, AND THE SECOND WAS MISSING FOR A DAY.
#
# BUILD roots are the page builders. WRITE roots are the object-write choke points. The first
# version had only the build roots, and reported `ssot/atomic_write.py` at RADIUS 2 -- because
# no page builder imports it and it happens to name two topic ids in its docstrings. It is the
# atomic writer that 45 modules and every topic object pass through; its real radius is the
# corpus. A file can be class-wide by what WRITES through it as well as by what BUILDS through
# it, and a closure that models only one of those under-reports the other to almost nothing.
#
# Found by challenging a number that looked wrong -- radius 2 for the universal writer -- which
# is the same instrument that found the CRLF phantom diff. Not by a gate.
BUILD_ROOTS = ("ssot/build_app_v2.py", "ssot/build_tabbed.py", "ssot/paper_projector.py")
WRITE_ROOTS = ("ssot/atomic_write.py",)
ROOTS = BUILD_ROOTS + WRITE_ROOTS
ACK = "BLAST_RADIUS_ACK.json"

# KNOWN-NEGATIVE CONTROL for the topic-id matcher: source text that must NOT be read as naming
# the topic. Added because gate 2 caught this module matching text and reporting counts with no
# measured precision -- in the same run that it was checking everyone else.
TOPIC_NEGATIVES = [
    ("arni-hfrefx = 1", "arni-hfref", "an id is not a prefix of a longer identifier"),
    ("x_ablation_af_review = 2", "ablation-af-review", "underscores are not hyphens"),
    ("# see ablation-af-review-legacy", "ablation-af-review",
     "an id is not a prefix of a longer slug"),
    ("ARNI-HFREF", "arni-hfref", "the match is case-sensitive by design"),
]


def imports_of(path):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            tree = ast.parse(fh.read())
    except (OSError, SyntaxError):
        return set()
    out = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            for a in n.names:
                out.add(a.name.split(".")[0])
        elif isinstance(n, ast.ImportFrom) and n.module:
            out.add(n.module.split(".")[0])
    return out


def build_closure(repo, gate):
    """Modules reachable from the page builders OR the object writers, inside ssot/.

    Named `build_closure` for continuity; it is the CORPUS closure -- build paths and write
    paths both. See ROOTS above for why the write half had to be added.
    """
    avail = {}
    ssot = os.path.join(repo, "ssot")
    for fn in os.listdir(ssot):
        if fn.endswith(".py"):
            avail[fn[:-3]] = os.path.join("ssot", fn)
    closure, queue = set(), []
    for r in ROOTS:
        if os.path.exists(os.path.join(repo, r)):
            closure.add(r)
            queue.append(r)
        else:
            gate.broken("build root %s is absent; the closure is incomplete and this gate "
                        "would under-report every radius." % r)
    while queue:
        cur = queue.pop()
        for mod in imports_of(os.path.join(repo, cur)):
            rel = avail.get(mod)
            if rel and rel not in closure:
                closure.add(rel)
                queue.append(rel)
    return closure


def radius_map(repo, gate):
    topics = [H.topic_id(p) for p in H.topic_objects(repo)[0]]
    tset = set(topics)
    closure = build_closure(repo, gate)
    # longest ids first, so `ablation-af-review` is not consumed by `ablation-af`
    ordered = sorted(tset, key=len, reverse=True)
    out, kinds = {}, collections.Counter()

    for dirpath, dirnames, filenames in os.walk(os.path.join(repo, "ssot")):
        if "__pycache__" in dirpath:
            continue
        for fn in filenames:
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, repo).replace("\\", "/")
            parts = rel.split("/")
            if len(parts) >= 3:
                owner = parts[1]
                if owner in tset:
                    out[rel] = {"radius": 1, "why": "belongs to topic %s" % owner,
                                "topics": [owner]}
                    kinds["topic-owned file (radius 1)"] += 1
                    continue
            if not fn.endswith(".py"):
                out[rel] = {"radius": 0, "why": "shared data/asset, not a build module",
                            "topics": []}
                kinds["shared non-module file"] += 1
                continue
            try:
                with open(full, "r", encoding="utf-8", errors="replace") as fh:
                    src = fh.read()
            except OSError:
                continue
            named = [t for t in ordered if re.search(r"(?<![A-Za-z0-9-])" + re.escape(t)
                                                     + r"(?![A-Za-z0-9-])", src)]
            # THE CLOSURE DECIDES FIRST, AND NAMING A TOPIC DOES NOT NARROW A BUILD MODULE.
            #
            # The first version tested `named` first and gave build_tabbed.py a radius of 6,
            # because it mentions six topic ids in special-case branches. It BUILDS all of
            # them. A generator that special-cases six topics has not become a six-topic file;
            # it is a corpus-wide file with six special cases, and reading the mentions as a
            # narrowing is what let a per-page brief edit a class-wide generator in the first
            # place. Membership of the build closure is the property that matters; naming is
            # only informative for modules OUTSIDE it.
            if rel in closure:
                out[rel] = {"radius": len(topics),
                            "why": "in the build closure: every topic is built through it"
                                   + (" (it also special-cases %d topic ids, which does not "
                                      "narrow it)" % len(named) if named else ""),
                            "topics": sorted(tset)}
                kinds["CLASS-WIDE module (in the build closure)"] += 1
            elif named:
                out[rel] = {"radius": len(named),
                            "why": "outside the build closure, names %d topic id(s)"
                                   % len(named),
                            "topics": sorted(named)}
                kinds["one-off module naming specific topics"] += 1
            else:
                out[rel] = {"radius": 0,
                            "why": "names no topic and is not reachable from a page builder",
                            "topics": []}
                kinds["module outside the build closure"] += 1
    return out, kinds, closure


def changed_files(repo, argv):
    """What this run is judging. Explicit --files wins; otherwise the working tree."""
    if "--files" in argv:
        return argv[argv.index("--files") + 1:]
    try:
        r = subprocess.run(["git", "status", "--porcelain"], cwd=repo,
                           capture_output=True, check=True)
        out = []
        for line in r.stdout.decode("utf-8", "replace").splitlines():
            p = line[3:].strip().replace("\\", "/")
            if p.startswith("ssot/"):
                out.append(p)
        return out
    except Exception:
        return []


def main(argv):
    repo = H.repo_root()
    gate = H.Gate("7  BLAST RADIUS",
                  "an edit to a file more than one topic builds through must be acknowledged "
                  "with its radius, counted")

    fp = []
    for src, topic, why in TOPIC_NEGATIVES:
        if re.search(r"(?<![A-Za-z0-9-])" + re.escape(topic) + r"(?![A-Za-z0-9-])", src):
            fp.append(why)
    gate.requires_control()
    gate.control(len(TOPIC_NEGATIVES), len(fp), fp)

    rmap, kinds, closure = radius_map(repo, gate)

    # named positives: the file the incident happened in, and a file that must stay radius 1.
    gate.expect_case("ssot/build_tabbed.py", "the file edited under a per-page brief")
    gate.expect_case("topic-owned", "a topic-owned file, which must be radius 1")

    if "ssot/build_tabbed.py" in rmap:
        gate.saw("ssot/build_tabbed.py")
        r = rmap["ssot/build_tabbed.py"]
        gate.note("ssot/build_tabbed.py radius = %d topics (%s)" % (r["radius"], r["why"]))
        # DERIVATION SELF-CHECK, keyed to a fact established outside the derivation: the page
        # builders build the corpus, so their radius IS the corpus. Anything less means the
        # derivation is wrong, and a wrong radius here reads as reassurance.
        n_topics = len(H.topic_objects(repo)[0])
        for root in ROOTS:
            got = rmap.get(root, {}).get("radius")
            if got != n_topics:
                gate.broken("%s computed a radius of %r against %d topic objects. A page "
                            "builder that does not reach every topic means the derivation is "
                            "wrong, not the file -- and an under-reported radius is exactly "
                            "the reassurance this gate exists to withhold."
                            % (root, got, n_topics))
    else:
        gate.broken("ssot/build_tabbed.py is not in the radius map at all.")

    if any(v["radius"] == 1 and v["why"].startswith("belongs to topic") for v in rmap.values()):
        gate.saw("topic-owned")

    changed = [c for c in changed_files(repo, argv) if c in rmap]
    if "--plant" in argv:
        changed = ["ssot/build_tabbed.py"]
        gate.note("PLANTED: a change to ssot/build_tabbed.py, unacknowledged")

    ackpath = os.path.join(repo, "gates", ACK)
    ack = H.load(ackpath) if os.path.exists(ackpath) else {}

    kinds["files in this change under ssot/"] = len(changed)
    gate.kinds(dict(kinds))

    for f in sorted(changed):
        info = rmap[f]
        if info["radius"] <= 1:
            continue
        declared = ack.get(f)
        if declared == info["radius"]:
            gate.note("acknowledged: %s at radius %d" % (f, info["radius"]))
            continue
        gate.finding("CLASS-WIDE-EDIT-NOT-ACKNOWLEDGED",
                     "%s is built through by %d topics (%s). This change touches it and %s. "
                     "Verifying it on one object is a claim about 1/%d."
                     % (f, info["radius"], info["why"],
                        "no acknowledgement was recorded" if declared is None
                        else "the recorded acknowledgement says %r, not %d"
                             % (declared, info["radius"]),
                        info["radius"]),
                     numerator=info["radius"], denominator=len(rmap))

    top = sorted(((v["radius"], k) for k, v in rmap.items() if v["radius"] > 1), reverse=True)
    gate.note("the %d class-wide files under ssot/, widest first: %s"
              % (len(top), ", ".join("%s(%d)" % (k, r) for r, k in top[:8])))

    art = os.path.join(repo, "out", "gate7_blast_radius.json")
    os.makedirs(os.path.dirname(art), exist_ok=True)
    with open(art, "w", encoding="utf-8") as fh:
        json.dump({"gate": gate.as_json(), "radius": rmap,
                   "build_closure": sorted(closure), "changed": changed}, fh, indent=1)

    return gate.report(denominator="%d files under ssot/; %d in this change" % (len(rmap),
                                                                                len(changed)))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
