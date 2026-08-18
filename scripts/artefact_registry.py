"""THE ARTEFACT REGISTRY: an index over git, not a second store.

WHAT PROBLEM THIS SOLVES, stated precisely because two different failures got conflated.

  VERSION LOSS -- one instance this week, and it predates us: a day of generator work
  destroyed by `git reset --hard HEAD~1`, surviving only as a .pyc because a probe had
  imported the module. GIT ALREADY PREVENTS THAT. The discipline failed, not the tool, and
  a new storage system would not have helped.

  DISCOVERY FAILURE -- five instances this week, all ours. The harness in a session outputs
  folder outside any repo. `projectors.py` in `ssot/` and not `scripts/`. The build path
  named in STATUS.md and not read. The generator commit named in ARNI's own build stamp.
  Two homes for executable code with nothing saying so. NONE of these is a versioning
  problem. Every one is "does this exist, and where".

THE LESSON TAKEN FROM GIT IS NOT VERSION HISTORY. It is that EVERY OBJECT IS ADDRESSABLE
AND EVERY REFERENCE IS EXPLICIT. This manifest gives artefacts an address by KIND rather
than by directory, so "where are the generators" has an answer that does not depend on
guessing which folder someone filed them in.

DELIBERATELY NOT BUILT: a numbering scheme, and any parallel store. GIT IS THE STORE. A
second storage system would be a second route, and every multi-route value in this corpus
has diverged. The manifest holds a content hash so drift is DETECTED, never so the content
is DUPLICATED.

THE DRIFT CHECK IS WHAT MAKES THIS A REGISTRY RATHER THAN A DOCUMENT. A document that
describes the tree slowly stops describing it -- that is this week's most reliable finding,
with the count-provenance detector, INDEX.md and PAGE_MAP all as instances. So:

  MISSING   a manifest entry whose file is not on disk        -> FAIL
  UNLISTED  a file of a known kind that is not in the manifest -> FAIL
  CHANGED   a listed file whose hash moved                     -> reported, and expected

`--update` refreshes hashes and adds unlisted files. It is a deliberate act, never
automatic, because a registry that silently absorbs whatever it finds cannot detect
anything.
"""
from __future__ import annotations
import hashlib
import io
import json
import os
import re
import sys

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST = os.path.join(REPO, "ARTEFACT-MANIFEST.json")

# KIND IS THE FIELD THAT WOULD HAVE SAVED THIS WEEK. "generator" is searchable regardless
# of which directory the file sits in -- which is the single fact four failed searches
# needed and none had.
KINDS = ("generator", "gate", "screen", "library", "object", "document", "evidence")

# How a file is classified when it is discovered. Directory is a HINT, never the answer:
# the generators live in ssot/ beside the data they project, which is exactly what broke
# four searches that assumed scripts/ meant tools.
GENERATOR_NAMES = {
    "ssot/build_tabbed.py": "the tabbed page builder: build_tabbed.py <object.json> <out.html>",
    "ssot/build_app_v2.py": "the FLAT control -- emits the pre-tab layout byte-identically; what every A/B is measured against",
    "ssot/projectors.py": "37 renderers (forest_svg, funnel_svg, rob_traffic_light_svg, prisma_flow_svg, verdict_card, readiness)",
    "ssot/projectors2.py": "further renderers",
    "ssot/paper.py": "manuscript surface from the same objects",
    "ssot/make_docx.py": "docx surface from the same objects",
    "scripts/project_topic_page.py": "RECONSTRUCTION of a working system, kept as a record of the error -- NOT a tool",
}
GATE_HINT = re.compile(r"_gate\.py$|^\.githooks/")
SCREEN_HINT = re.compile(r"_screen\.py$|_sweep\.py$|_audit\.py$|_triage\.py$|^scripts/lint_")


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def classify(rel):
    if rel in GENERATOR_NAMES:
        return "generator", GENERATOR_NAMES[rel]
    if GATE_HINT.search(rel):
        return "gate", ""
    if SCREEN_HINT.search(rel):
        return "screen", ""
    if rel.startswith("scripts/") and rel.endswith(".py"):
        return "library", ""
    if rel.endswith(".json") and rel.startswith("ssot/"):
        return "object", ""
    if rel.endswith(".md"):
        return "document", ""
    return None, ""


def discover():
    """Files of a KNOWN kind. Deliberately narrow -- a registry of everything is a
    registry of nothing."""
    out = {}
    for base in ("scripts", ".githooks", "ssot"):
        d = os.path.join(REPO, base)
        if not os.path.isdir(d):
            continue
        for root, _, files in os.walk(d):
            if os.sep + "sources" in root:
                continue
            for fn in files:
                rel = os.path.relpath(os.path.join(root, fn), REPO).replace("\\", "/")
                if base == "ssot" and rel not in GENERATOR_NAMES:
                    continue          # ssot objects are indexed by PAGE_MAP already
                kind, note = classify(rel)
                if kind:
                    out[rel] = (kind, note)
    for fn in sorted(os.listdir(REPO)):
        if fn.endswith(".md"):
            out[fn] = ("document", "")
    return out


def load():
    if os.path.exists(MANIFEST):
        return json.load(io.open(MANIFEST, encoding="utf-8"))
    return {"artefacts": {}}


def main() -> int:
    update = "--update" in sys.argv
    man = load()
    entries = man.get("artefacts", {})
    found = discover()

    missing = [p for p in entries if not os.path.exists(os.path.join(REPO, p))]
    unlisted = [p for p in found if p not in entries]
    changed = []
    for p, e in entries.items():
        fp = os.path.join(REPO, p)
        if os.path.exists(fp):
            h = sha(fp)
            if e.get("sha256_16") != h:
                changed.append((p, e.get("sha256_16"), h))

    if update:
        for p in unlisted:
            kind, note = found[p]
            entries[p] = {"kind": kind, "sha256_16": sha(os.path.join(REPO, p))}
            if note:
                entries[p]["note"] = note
        for p, _, h in changed:
            entries[p]["sha256_16"] = h
        man["artefacts"] = dict(sorted(entries.items()))
        man["what_this_is"] = (
            "AN INDEX OVER GIT, NOT A SECOND STORE. Git holds the content and its history; "
            "this holds the ADDRESS BY KIND, so 'where are the generators' has an answer "
            "that does not depend on guessing a directory. No numbering scheme and no "
            "parallel copy: a second store would be a second route.")
        man["kinds"] = list(KINDS)
        io.open(MANIFEST, "w", encoding="utf-8").write(
            json.dumps(man, ensure_ascii=False, indent=1))
        print("manifest updated: %d artefacts (+%d new, %d hashes refreshed)"
              % (len(entries), len(unlisted), len(changed)))
        return 0

    by_kind = {}
    for p, e in entries.items():
        by_kind.setdefault(e.get("kind", "?"), []).append(p)
    print("artefacts registered: %d" % len(entries))
    for k in KINDS:
        if by_kind.get(k):
            print("    %-11s %3d" % (k, len(by_kind[k])))
    print()
    if by_kind.get("generator"):
        print("GENERATORS -- the answer four failed searches needed:")
        for p in sorted(by_kind["generator"]):
            print("    %-34s %s" % (p, (entries[p].get("note") or "")[:64]))
        print()
    bad = False
    if missing:
        bad = True
        print("MISSING -- registered but not on disk: %d" % len(missing))
        for p in missing[:10]:
            print("    %s" % p)
    if unlisted:
        bad = True
        print("UNLISTED -- a file of a known kind, not registered: %d" % len(unlisted))
        for p in unlisted[:10]:
            print("    %-46s [%s]" % (p, found[p][0]))
    if changed:
        print("CHANGED -- content moved since registration: %d (expected; --update)"
              % len(changed))
    if bad:
        print()
        print("REGISTRY DRIFT. A document that describes the tree slowly stops describing "
              "it -- that is what makes this a registry and not a document.")
        return 1
    print("registry matches the tree.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
