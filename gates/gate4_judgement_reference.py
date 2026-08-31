"""GATE 4 -- a stored judgement must carry a reference to what it judged.

THE CLASS. A judgement recorded without a pointer to the version of its subject can only ever
be caught by a sweep somebody remembers to run. It does not fail; it does not warn; it agrees
with a subject that has since moved, and reads exactly like a judgement that is still true.
130 of the 242 checkable self-descriptions in this corpus are stale, and every one of them was
found by a sweep rather than by anything structural.

MEASURED HERE, 2026-08-28, over 2,789 stored judgement blocks in 155 topic objects:

    A  VERSIONED         40    a hash, a verbatim snapshot, or a commit -- exactly re-checkable
    B  TIMESTAMPED    1,397    a read time, but nothing saying WHAT was read
    C  IDENTIFIER       868    an NCT or PMID: names a MUTABLE subject, pins no version
    D  NOTHING          484    no reference of any kind

1.4% of the judgements in this corpus can be re-checked against their own subject. The other
98.6% are believed.

WHY AN IDENTIFIER IS NOT A REFERENCE. `nct` names the trial; it does not name the registry
record as it stood when the judgement was made. A registration is edited. This is the same
fact as "a page NAME is not an artefact identity" -- a name plus a version is.

WHY A TIMESTAMP IS NOT A REFERENCE EITHER. `checked_utc` says WHEN, not WHAT. It supports an
inference about staleness; it cannot detect a subject that changed and changed back, and it
cannot be verified at all without the original bytes.

THE DEMONSTRATION, NOT THE ASSERTION. `prove_undetectable()` below takes a real judgement of
each kind, mutates its subject, and shows what each kind can say afterwards. Kind A reports
STALE. Kinds B, C and D report NOT-CHECKABLE -- and NOT-CHECKABLE is never a pass.
"""
from __future__ import annotations

import ast
import collections
import copy
import hashlib
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _harness as H                                                        # noqa: E402

JUDGE_KEYS = ("verdict", "judgement", "rating", "certainty", "risk_of_bias_verdict",
              "grade", "assessment", "conformance")

VERSIONED = re.compile(r"sha256|sha1|checksum|digest|_at_derivation|verbatim|as_it_stood|"
                       r"\bcommit\b|\bblob\b|snapshot|version_checked|subject_ref", re.I)
STAMPED = re.compile(r"read_utc|checked_utc|assessed_utc|verified_utc|checked_on|verified_on|"
                     r"assessed_on|_utc$", re.I)
IDENT = re.compile(r"^(nct|pmid|doi|source_url|trial_id|registry_id|url)$", re.I)

KIND_A = "A VERSIONED   -- hash, verbatim snapshot or commit; exactly re-checkable"
KIND_B = "B TIMESTAMPED -- when it was read, not what was read"
KIND_C = "C IDENTIFIER  -- names a mutable subject, pins no version"
KIND_D = "D NOTHING     -- no reference to what was judged"

BACKLOG = "JUDGEMENT_REFERENCE_BACKLOG.json"
WRITER_BACKLOG = "JUDGEMENT_WRITER_BACKLOG.json"

# KNOWN-NEGATIVE CONTROL for the kind classifier -- key sets that must NOT be read as
# VERSIONED. Added because gate 2 caught this module reporting counts from a regex over field
# names with no measured precision. The gate found a real gap in its own author's work, which
# is the only kind of evidence that a gate is doing anything.
NOT_VERSIONED = [
    ({"verdict": "x", "nct": "NCT1"}, "an identifier is not a version"),
    ({"verdict": "x", "checked_utc": "t"}, "a timestamp says when, not what"),
    ({"verdict": "x", "reason": "y"}, "a reason is not a reference"),
    ({"verdict": "x", "authority": "Cochrane 10.10"}, "an authority is not a subject"),
    ({"verdict": "x", "source_url": "u"}, "a URL names a mutable document"),
    ({"verdict": "x", "assessor_1": "a", "assessor_2": "b"}, "who judged is not what"),
]


def subject_ref(fields):
    """THE FIX, offered as one line at the point a judgement is written.

        block['subject_ref'] = subject_ref({'d1': ..., 'd2': ...})

    A stable sha256 over the exact values judged. Storing it costs one field and converts a
    judgement from believed to checkable.
    """
    payload = json.dumps(fields, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


def classify(keys_self, keys_ancestors):
    keys = set(keys_self) | set(keys_ancestors)
    if any(VERSIONED.search(k) for k in keys):
        return KIND_A
    if any(STAMPED.search(k) for k in keys):
        return KIND_B
    if any(IDENT.match(k) for k in keys):
        return KIND_C
    return KIND_D


def judgement_blocks(obj):
    """(path, block, kind). Ancestors count: a snapshot held one level up still pins the
    subject, and scoring only the judgement's own dict returned a flat ZERO for kind A --
    an implausible proportion, which is a statement about the instrument."""
    out = []

    def rec(x, path, anc):
        if isinstance(x, dict):
            anc2 = anc | set(x)
            if any(isinstance(x.get(j), str) and x[j].strip() for j in JUDGE_KEYS):
                out.append((path, x, classify(x.keys(), anc2)))
            for k, v in x.items():
                rec(v, path + "." + str(k), anc2)
        elif isinstance(x, list):
            for i, v in enumerate(x):
                rec(v, path + "[" + str(i) + "]", anc)

    rec(obj, "", set())
    return out


# ---------------------------------------------------------------------------
# the demonstration: what can each kind SAY when its subject moves?
# ---------------------------------------------------------------------------
def recheck(block, subject_now):
    """STALE / CURRENT / NOT-CHECKABLE. NOT-CHECKABLE is never a pass."""
    stored = None
    for k, v in block.items():
        if isinstance(v, str) and v.startswith("sha256:"):
            stored = v
            break
    if stored is None:
        return "NOT-CHECKABLE"
    return "CURRENT" if stored == subject_ref(subject_now) else "STALE"


def prove_undetectable(gate):
    """A real RoB-shaped judgement of each kind, its subject mutated, and what each can say."""
    subject = {"D1": "low", "D2": "some concerns", "D3": "low"}
    moved = {"D1": "low", "D2": "high", "D3": "low"}

    versioned = {"verdict": "some concerns", "subject_ref": subject_ref(subject)}
    timestamped = {"verdict": "some concerns", "checked_utc": "2026-08-01T00:00:00Z"}
    identified = {"verdict": "some concerns", "nct": "NCT00643188"}
    bare = {"verdict": "some concerns", "reason": "as judged"}

    results = {
        KIND_A: recheck(versioned, moved),
        KIND_B: recheck(timestamped, moved),
        KIND_C: recheck(identified, moved),
        KIND_D: recheck(bare, moved),
    }
    if results[KIND_A] != "STALE":
        gate.broken("a VERSIONED judgement failed to notice its subject moved (%s). The fix "
                    "this gate recommends does not work, which is a worse finding than the "
                    "one it was checking." % results[KIND_A])
    if recheck(versioned, subject) != "CURRENT":
        gate.broken("a VERSIONED judgement reported STALE against an UNCHANGED subject -- the "
                    "reference is not stable, so it would cry wolf on every run.")
    for kind in (KIND_B, KIND_C, KIND_D):
        if results[kind] != "NOT-CHECKABLE":
            gate.broken("%s unexpectedly reported %r" % (kind, results[kind]))
    gate.note("demonstration -- same subject mutated D2 'some concerns' -> 'high':")
    for kind, verdict in results.items():
        gate.note("    %-62s -> %s" % (kind, verdict))
    return results


# ---------------------------------------------------------------------------
# ARM C -- a path that WRITES a judgement must write it through the stamped writer.
#
# Mahmood, 2026-08-28: "make the GENERATOR write subject_ref on every judgement it emits, and
# make the meta-gate FAIL if a judgement-writing path exists that does not." The stamp lives in
# ssot/atomic_write.py::write_json, which is the choke point 45 modules and every topic object
# pass through -- so the enforceable question is whether a judgement-writer goes through it.
#
# 56 modules persist a judgement into ssot/. 17 go through the stamped writer; 39 do not, and
# almost all of those are one-shot 2026-08-19 migrations already applied. They are FROZEN by
# name: the class cannot grow, which is the property that was missing.
# ---------------------------------------------------------------------------
JUDGE_WRITE_KEYS = set(JUDGE_KEYS)


def _writes_judgement(tree):
    for n in ast.walk(tree):
        if isinstance(n, ast.Assign):
            for t in n.targets:
                if isinstance(t, ast.Subscript) and isinstance(t.slice, ast.Constant)                         and t.slice.value in JUDGE_WRITE_KEYS:
                    return True
        if isinstance(n, ast.Dict):
            for k in n.keys:
                if isinstance(k, ast.Constant) and k.value in JUDGE_WRITE_KEYS:
                    return True
    return False


def arm_c(gate, repo):
    kinds = collections.Counter()
    bypass, stamped = [], []
    for d in ("scripts", "ssot"):
        base = os.path.join(repo, d)
        if not os.path.isdir(base):
            continue
        for fn in sorted(os.listdir(base)):
            if not fn.endswith(".py"):
                continue
            with open(os.path.join(base, fn), "r", encoding="utf-8", errors="replace") as fh:
                src = fh.read()
            try:
                tree = ast.parse(src)
            except SyntaxError:
                kinds["unparseable"] += 1
                continue
            if not _writes_judgement(tree):
                kinds["does not write a judgement"] += 1
                continue
            if not (("json.dump" in src or "write_json" in src) and "ssot" in src):
                kinds["writes a judgement but does not persist it to ssot/"] += 1
                continue
            rel = "%s/%s" % (d, fn)
            kinds["persists a judgement into ssot/"] += 1
            if "atomic_write" in src or "write_json" in src:
                kinds["  through the STAMPED writer"] += 1
                stamped.append(rel)
            else:
                kinds["  BYPASSES the stamped writer -- its judgements reference nothing"] += 1
                bypass.append(rel)
    return bypass, stamped, kinds


def ratchet(gate, repo, bare_sites):
    path = os.path.join(repo, "gates", BACKLOG)
    now = sorted(bare_sites)
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as fh:
            json.dump({"frozen_utc": "2026-08-28",
                       "what": "stored judgements carrying NO reference of any kind to what "
                               "they judged (kind D). May SHRINK, never GROW. A site here "
                               "that is not in the frozen list fails gate 4.",
                       "count": len(now), "sites": now}, fh, indent=1)
        gate.note("kind-D backlog frozen for the first time at %d sites." % len(now))
        return []
    frozen = set(H.load(path)["sites"])
    new = [s for s in now if s not in frozen]
    gate.note("kind-D backlog: %d frozen, %d now, %d retired, %d NEW"
              % (len(frozen), len(now), len(frozen - set(now)), len(new)))
    return new


def main(argv):
    repo = H.repo_root()
    gate = H.Gate("4  JUDGEMENT REFERENCE",
                  "a stored judgement must carry a reference to the version of what it judged")

    paths, kinds_pop = H.topic_objects(repo)
    objects = {}
    for p in paths:
        try:
            objects[H.topic_id(p)] = H.load(p)
        except Exception as exc:
            gate.broken("unparseable object %s: %s" % (p, exc))

    # NAMED POSITIVES ARE THE CLASSIFIER PROBES, NOT LIVE SITES.
    #
    # They were live sites first, and --repair showed why that is wrong: emptying kind D --
    # the SUCCESS this gate exists to produce -- made the case unreachable and the gate went
    # VACUOUS forever. A control that retires itself at the moment of success is not a control.
    # The probes are synthetic and immutable, so the gate keeps proving it can see all four
    # kinds however clean the corpus becomes. The live population is reported as KINDS.
    for kind in (KIND_A, KIND_B, KIND_C, KIND_D):
        gate.expect_case("probe:" + kind[0],
                         "the classifier still recognises %s" % kind.split("--")[0].strip())

    fp = [why for block, why in NOT_VERSIONED
          if classify(block.keys(), set(block)) == KIND_A]
    gate.requires_control()
    gate.control(len(NOT_VERSIONED), len(fp), fp)

    prove_undetectable(gate)
    for kind, block in ((KIND_A, {"verdict": "x", "subject_ref": "sha256:0"}),
                        (KIND_B, {"verdict": "x", "checked_utc": "2026-08-01T00:00:00Z"}),
                        (KIND_C, {"verdict": "x", "nct": "NCT00000000"}),
                        (KIND_D, {"verdict": "x", "reason": "as judged"})):
        if classify(block.keys(), set(block)) == kind:
            gate.saw("probe:" + kind[0])

    if "--plant" in argv:
        obj = copy.deepcopy(objects["ablation-af-review"])
        obj.setdefault("__planted", {})["a_new_unreferenced_judgement"] = {
            "verdict": "low risk", "reason": "planted for the gate"}
        objects["ablation-af-review"] = obj
        gate.note("PLANTED: a new judgement carrying no subject reference (in memory)")

    if "--repair" in argv:
        for t, obj in objects.items():
            for path, block, kind in judgement_blocks(obj):
                if kind == KIND_D:
                    block["subject_ref"] = subject_ref(
                        {k: v for k, v in block.items() if k != "subject_ref"})
        gate.note("REPAIRED in memory: every kind-D judgement given a subject_ref")

    counts = collections.Counter()
    bare_sites = []
    for topic, obj in objects.items():
        for path, block, kind in judgement_blocks(obj):
            counts[kind] += 1
            if kind == KIND_D:
                bare_sites.append(topic + path)

    new_bare = ratchet(gate, repo, bare_sites)

    bypass, stamped, kinds_c = arm_c(gate, repo)
    if "--plant-writer" in argv:
        bypass.append("scripts/__planted_judgement_writer.py")
        kinds_c["  BYPASSES the stamped writer -- its judgements reference nothing"] += 1
        gate.note("PLANTED: a new judgement-writer bypassing the stamped writer")
    new_writers = H.ratchet(gate, WRITER_BACKLOG, bypass,
                            "modules that persist a judgement into ssot/ without going "
                            "through the stamped writer, so the judgements they emit "
                            "reference nothing.")
    for mod in new_writers:
        gate.finding("JUDGEMENT-WRITER-BYPASSES-THE-STAMP",
                     "%s persists a judgement into ssot/ without ssot/atomic_write.write_json, "
                     "so the judgement it emits carries no reference to what it judged. It is "
                     "NEW since the backlog was frozen." % mod,
                     numerator=len(new_writers), denominator=len(bypass) + len(stamped))

    total = sum(counts.values())
    merged = dict(kinds_pop)
    for k in (KIND_A, KIND_B, KIND_C, KIND_D):
        merged[k] = counts.get(k, 0)
    merged.update({k: v for k, v in kinds_c.items()
                   if k != "does not write a judgement"})
    gate.kinds(merged)
    gate.note("the stamp is wired at ssot/atomic_write.py::write_json (blast radius 155, "
              "acknowledged) and fires on ssot/<topic>/<topic>.json only.")
    if total:
        gate.note("exactly re-checkable: %d/%d = %.1f%% of stored judgements. The remainder "
                  "are believed, not checked." % (counts[KIND_A], total,
                                                  100.0 * counts[KIND_A] / total))
    gate.note("the fix is one field at the point of writing: "
              "block['subject_ref'] = subject_ref({the values judged})")

    for site in new_bare:
        gate.finding("NEW-JUDGEMENT-WITHOUT-A-SUBJECT-REFERENCE",
                     "%s stores a judgement with no hash, snapshot or commit naming what it "
                     "judged. It is NEW since the backlog was frozen." % site,
                     numerator=len(new_bare), denominator=total)

    art = os.path.join(repo, "out", "gate4_judgement_reference.json")
    os.makedirs(os.path.dirname(art), exist_ok=True)
    with open(art, "w", encoding="utf-8") as fh:
        json.dump({"gate": gate.as_json(), "counts": dict(counts),
                   "new_bare": new_bare}, fh, indent=1)

    # COVERAGE. Only a VERSIONED reference can be re-checked; the other three kinds name a
    # mutable subject or nothing. This gate has been reporting that as a note for weeks.
    _all = sum(gate.kind(k) for k in (
        "A VERSIONED   -- hash, verbatim snapshot or commit; exactly re-checkable",
        "B TIMESTAMPED -- when it was read, not what was read",
        "C IDENTIFIER  -- names a mutable subject, pins no version",
        "D NOTHING     -- no reference to what was judged"))
    gate.coverage(gate.kind("A VERSIONED   -- hash, verbatim snapshot or commit; exactly re-checkable"), max(_all, 1),
                  "stored judgements whose reference pins no version, so staleness in "
                  "them is not detectable by anything -- they are believed, not checked")
    return gate.report(denominator="%d stored judgement blocks in %d topic objects"
                                   % (total, len(objects)))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
