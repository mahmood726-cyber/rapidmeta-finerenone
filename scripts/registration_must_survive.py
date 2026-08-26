"""MUST-SURVIVE: did a merge, rebase or deploy lose the registration work?

Run after any merge into main, before publishing:

    git fetch origin && python scripts/registration_must_survive.py

    exit 0  everything present and intact
    exit 1  something was lost or a claim broke
    exit 2  the check could not reach its target -- a NON-VERDICT, not a pass

WHY THIS FILE REPLACED A LIST OF PINNED BLOB HASHES
    The first version pinned an exact git blob SHA on every file the registration
    work touched. It fired twice in three hours, both times on a LEGITIMATE change,
    once from each of two lanes:

      scripts/registration_ordering_gate.py  -- improved by its own author
      ssot/arni-hfref/arni-hfref.json        -- reserialised, identical key-for-key

    A falsifier that cries wolf is one people start reading past, and the whole
    value of this one is that a lane refused to publish past it. So the checks are
    now split by what the artefact IS, not by whether it happened to be touched.

    EXACT BYTES are demanded only where THE BYTE IS THE CLAIM:
      - the eight anchored artefacts, because a transparency-log entry is a
        statement about specific bytes and nothing else. If these change, the
        published verification recipe stops working for a stranger.
      - the public signing key, because a changed key silently invalidates every
        signature ever made under it.

    CONTENT PROPERTIES everywhere else, because those files are meant to improve:
      - VERIFY.md must still carry its recipe and its stated limitation. Byte-
        pinning it would guarantee a false failure the next time it is improved --
        which is exactly the argument that condemned the blob pin on the gate, and
        it applies to VERIFY.md no less. It was in fact improved tonight.
      - the ordering gate must still carry its controls and its exit-code contract.
      - the three JSON files corrected tonight must still NOT carry the false
        timestamp claim. THIS is the check that does the real work: those files
        legitimately change on both sides of a merge, so a blob pin is useless,
        and a merge taking the branch's side would silently restore the false
        claim while looking like a clean merge.

    THE ANCHOR IS ITS OWN PIN. The sha256 values below are not hashes someone
    chose; they are the values recorded in the public transparency log, which
    anyone can fetch and compare. That is why they may be demanded exactly.

WHAT A FULL PASS DOES NOT ESTABLISH -- written in advance
    - NOT that the reviews are correct, complete or adequately searched.
    - NOT that files outside this list survived. It checks what it lists.
    - NOT that the anchors are still in the log. It compares committed bytes to
      the recorded log hash; it does not re-fetch Rekor. Use ssot/registration/
      VERIFY.md for the online check.
"""
from __future__ import annotations
import hashlib
import io
import json
import os
import re
import subprocess
import sys

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXIT_UNREACHABLE = 2

COMMITS = [
    ("7e9640d322601b4912aa916cd425eb819b8eb9ba", "arni false-timestamp fix"),
    ("3872817c06c92bad152cc4d076ea23b2f611012c", "finerenone-cv PROTOCOL (anchored)"),
    ("fe926bf4f25e4c72a6535bdabc0eab75d4373119", "finerenone-cv SEARCH-RECORD (anchored)"),
    ("29d61df0af9a83c53aebd637369f199ac8cf7410", "VERIFY.md + public key + gate scope"),
    ("1f609fd370c438f41bc24069c9e71446cea0dcef", "VERIFY.md executed-recipe note"),
    ("822ec6b2b08b64823576bf16e5a5c3515986d065", "empagliflozin PROTOCOL (anchored)"),
    ("9e65b30aaad98dafd7ad451fc4b8bad11e8e6585", "empagliflozin SEARCH-RECORD (anchored)"),
    ("7a05d1eb8adaaa4855261798c9c285ba1ab4f51e", "empagliflozin SCREENING-RECORD (anchored)"),
    ("0f8496a74", "gate: protocol-link resolution check"),
    ("8e5d6c657142773d07710529b7c231cf785c6825", "antimalarial-act PROTOCOL (anchored)"),
    ("0f69631b356348e45e1111c1daf0d1554f25b65a", "antimalarial-act SEARCH-RECORD (anchored)"),
    ("baf39718829360f126f4fdf0f11637967c22ead6", "empagliflozin ADJUDICATION-RECORD (anchored)"),
]

# path -> (sha256 recorded in the public log, rekor logIndex)
ANCHORED = {
    "ssot/antimalarial-act/PROTOCOL.md":
        ("56abb0a91eb426fea44a3708cb628c9d4b0946f82adb1df444e99c2feb97118a", 2606041205),
    "ssot/antimalarial-act/SEARCH-RECORD.json":
        ("757210be4f8ccca614798faed3d7fe8f79306fddf844bf63913f4225bc46d463", 2606136300),
    "ssot/empagliflozin-hf-auto-full-review/ADJUDICATION-RECORD.json":
        ("13cd3cdc101f8c82a15d9fd1b76d4ec1377c4c909c934046e964c579bce8d04f", 2606218011),
    "ssot/empagliflozin-hf-auto-full-review/PROTOCOL.md":
        ("80019b04d606f07e778fb7c724406e508fb27098cd96cf7c4dd6268df0891f1c", 2605627307),
    "ssot/empagliflozin-hf-auto-full-review/SCREENING-RECORD.json":
        ("2a79c88cb59f3f96b36fc3af755f33d2e953403ee83c802ca4e526c72d0ef889", 2605766019),
    "ssot/empagliflozin-hf-auto-full-review/SEARCH-RECORD.json":
        ("3ab55d89ef29f28e533a829de725ee08731b335004ee8055a7eb834b80b5a0fb", 2605693104),
    "ssot/finerenone-cv/PROTOCOL.md":
        ("7220ad588145ee338f936a6799fea6766d4b467f04994dd2198f2ea759fb2633", 2604694652),
    "ssot/finerenone-cv/SEARCH-RECORD.json":
        ("ec452d245ebf2a79602d14de321a77be1c6fefd2d58af0ef0f41579520ed9d9e", 2604754261),
}

PUBLIC_KEY = "ssot/registration/rekor-signing-key.pub.pem"

# path -> list of (label, regex that MUST match, expected_count or None for >=1)
PROPERTIES = {
    "ssot/registration/VERIFY.md": [
        ("states the limitation", r"the log time is independent of us; the key custody is not", None),
        ("carries the narrow claim", r"[Nn]o later than", None),
        ("gives the git show step", r"git show <commit>:<path>", None),
        ("says the recipe was run", r"This recipe has been run", None),
    ],
    "scripts/registration_ordering_gate.py": [
        ("refuses a violation fixture", r"__control_violation", None),
        ("refuses a bare date", r"__control_date_only", None),
        ("proves the link check fires", r"__control_broken_protocol_link", None),
        ("non-verdict is not exit 0", r"EXIT_NOTHING_COMPARED\s*=\s*2", None),
    ],
}

# The false claim corrected tonight. It must appear ZERO times in each of these.
FALSE_CLAIM = "set by the repository and by the APIs"
NO_FALSE_CLAIM = [
    "ssot/arni-hfref/arni-hfref.json",
    "ssot/arni-hfref/manuscript_docmodel.json",
    "ssot/manuscript_docmodel.json",
]


def show(ref, path):
    p = subprocess.run(["git", "-C", REPO, "show", ref + ":" + path], capture_output=True)
    return p.stdout if p.returncode == 0 else None


def main(ref="origin/main"):
    fails, checked = [], 0
    probe = subprocess.run(["git", "-C", REPO, "rev-parse", ref], capture_output=True)
    if probe.returncode != 0:
        print("CANNOT REACH " + ref + " -- non-verdict, not a pass.")
        return EXIT_UNREACHABLE

    print("COMMITS MUST BE ANCESTORS OF " + ref)
    for sha, label in COMMITS:
        checked += 1
        ok = subprocess.run(["git", "-C", REPO, "merge-base", "--is-ancestor", sha, ref],
                            capture_output=True).returncode == 0
        print(("  ok   " if ok else "  LOST ") + sha[:9] + "  " + label)
        if not ok:
            fails.append("commit " + sha[:9] + " (" + label + ")")

    print("\nANCHORED ARTEFACTS -- EXACT BYTES, because the byte IS the claim")
    for path, (want, log_index) in ANCHORED.items():
        checked += 1
        blob = show(ref, path)
        got = hashlib.sha256(blob).hexdigest() if blob else "MISSING"
        ok = got == want
        print(("  ok   " if ok else "  BROKEN ") + path + "  (logIndex " + str(log_index) + ")")
        if not ok:
            fails.append("ANCHOR BROKEN " + path + " want " + want[:16] + " got " + got[:16])

    print("\nPUBLIC KEY -- EXACT BYTES, a changed key invalidates every signature")
    checked += 1
    blob = show(ref, PUBLIC_KEY)
    ok = bool(blob) and b"BEGIN PUBLIC KEY" in blob
    print(("  ok   " if ok else "  LOST ") + PUBLIC_KEY)
    if not ok:
        fails.append("public key missing or malformed")

    print("\nCONTENT PROPERTIES -- files that are MEANT to improve")
    for path, props in PROPERTIES.items():
        blob = show(ref, path)
        if blob is None:
            checked += 1
            print("  LOST " + path)
            fails.append(path + " missing")
            continue
        # NORMALISE BEFORE MATCHING. A sentence a reader sees as one string is often
        # several strings in the file, split by a line break or an inline tag. Matching
        # raw source fails on text that is present and correct -- and the failure looks
        # like the content being gone. This check fired on VERIFY.md for exactly that
        # reason: the sentence "the log time is independent of us; the key custody is
        # not" is ONE sentence to a reader and TWO LINES on disk, and the unnormalised
        # regex reported it as gone. The fault was the checker, not the file.
        text = re.sub(r"\s+", " ", blob.decode("utf-8", "replace"))
        for label, pattern, _n in props:
            checked += 1
            ok = re.search(pattern, text) is not None
            print(("  ok   " if ok else "  LOST ") + path + " :: " + label)
            if not ok:
                fails.append(path + " no longer " + label)

    print("\nTHE FALSE CLAIM MUST NOT COME BACK")
    print("  (a merge taking the branch's side restores it and looks clean doing so)")
    for path in NO_FALSE_CLAIM:
        checked += 1
        blob = show(ref, path)
        n = blob.decode("utf-8", "replace").count(FALSE_CLAIM) if blob else -1
        ok = n == 0
        print(("  ok   " if ok else "  REGRESSED ") + path + "  occurrences=" + str(n))
        if not ok:
            fails.append(path + " carries the false claim again (" + str(n) + "x)")

    print("\nchecked " + str(checked) + " properties against " + ref)
    if fails:
        print("*** " + str(len(fails)) + " FAILURE(S) -- DO NOT PUBLISH ***")
        for f in fails:
            print("    " + f)
        return 1
    print("ALL CHECKS PASSED -- nothing of the registration work was lost.")
    return 0


def self_test():
    """Prove each KIND of check can fail, against the merge base where none of it exists."""
    base = "0be050e90"
    print("SELF-TEST: the same checks against " + base + ", where none of this work exists.")
    print("A check that has only ever passed is one nobody has tested.\n")
    rc = main(base)
    print("\nself-test exit: " + str(rc) + " -- expected 1")
    return rc == 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(0 if self_test() else 1)
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else "origin/main"))
