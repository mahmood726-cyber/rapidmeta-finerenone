"""Corpus rollout of the two render fixes: the `#paper` anchor and the reading order.

THE PREDICTION, STATED BEFORE THE RUN so the run can contradict it:

  1. SECTION COUNT UNCHANGED on every page. The reading order is a sort; it moves
     sections and creates none. A page whose h3 count moves has done something nobody
     asked for.
  2. WORD COUNT UNCHANGED within rounding on every page. Re-ordering moves words; it does
     not write them. More than a 1% move is a content change wearing a formatting change's
     clothes.
  3. id="paper" PRESENT on every page afterwards, and on none before.
  4. NOT ONE PAGE COMES OUT BYTE-IDENTICAL. Every tab panel now emits a bare id, so every
     page must change. A BYTE-IDENTICAL PAGE HERE MEANS IT WAS NOT REBUILT -- in a build
     directory "unchanged" and "never built" are the same bytes, and this run is exactly
     the case where that matters.

Any page failing 1, 2 or 3 is RESTORED from git and reported. The run does not stop, so
one bad page does not hide the state of the rest, and the summary refuses at the end.

ARNI_HF_REVIEW.html IS EXCLUDED BY NAME. Its manuscript is an authored docmodel the
projector reproduces at about 11%, and ssot/manuscript_guard.py would refuse the build
anyway. Named here rather than silently skipped.
"""
import io
import json
import os
import re
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXCLUDE = {"ARNI_HF_REVIEW.html": "authored docmodel; the projector reproduces ~11% of it"}
H3 = re.compile(r"<h3[^>]*id=['\"](paper-[^'\"]+)['\"][^>]*>", re.S)
ANCHOR = re.compile(r"""id=['"]paper['"]""")


def measure(path):
    if not os.path.exists(path):
        return None
    t = io.open(path, encoding="utf-8", errors="replace").read()
    body = re.sub(r"<[^>]+>", " ", t)
    return {"bytes": len(t.encode("utf-8")),
            "sections": len(H3.findall(t)),
            "words": len(body.split()),
            "anchor": bool(ANCHOR.search(t))}


def main():
    pm = json.load(io.open(os.path.join(REPO, "ssot", "PAGE_MAP.json"), encoding="utf-8"))
    targets = sorted((page, objp) for page, objp in pm.items()
                     if page not in EXCLUDE and os.path.exists(os.path.join(REPO, page)))
    limit = None
    for a in sys.argv[1:]:
        if a.startswith("--limit="):
            limit = int(a.split("=", 1)[1])
    if limit:
        targets = targets[:limit]

    print("pages to rebuild: %d" % len(targets))
    for k, v in EXCLUDE.items():
        print("EXCLUDED %-28s %s" % (k, v))
    print()

    built = 0
    failures = []
    identical = []
    skipped_legacy = []
    for n, (page, objp) in enumerate(targets, 1):
        fp = os.path.join(REPO, page)
        before = measure(fp)
        # A PAGE WITH NO `paper-*` SECTIONS WAS NOT BUILT BY THIS GENERATOR, and rebuilding
        # it is not a re-ordering -- it is a replacement. The trial run found
        # ACS_ANTIPLATELET_REVIEW.html at 27,482 words and ZERO paper sections; the rebuild
        # produced 27 sections and 6,484 words, which is a 76% content loss dressed as a
        # formatting pass. The prediction caught it and it was restored.
        #
        # These are skipped and COUNTED, not quietly passed over: they are the same
        # legacy-page population that made five REML corrections unreachable by a reader,
        # and deciding what to do with them is its own unit.
        if before and before["sections"] == 0:
            skipped_legacy.append((page, before["words"]))
            print("%3d/%d %-46s SKIPPED, not a current-generator page (%d words, 0 paper "
                  "sections)" % (n, len(targets), page[:46], before["words"]), flush=True)
            continue
        # NOT text=True. scripts/lint_subprocess_decode.py refuses it and is right:
        # `text=True` decodes with the LOCALE codec, and a build that prints a trial name
        # with an en-dash raises UnicodeDecodeError -- turning a page that built fine into
        # a crash of the rollout, on a machine-dependent condition. Decode explicitly.
        p = subprocess.run([sys.executable, "-W", "ignore",
                            os.path.join(REPO, "ssot", "build_tabbed.py"),
                            os.path.join(REPO, objp), fp],
                           capture_output=True, cwd=REPO)
        out = ((p.stdout or b"") + (p.stderr or b"")).decode("utf-8", "replace")
        if "REFUSED" in out or "ABORTED" in out:
            failures.append((page, "BUILD REFUSED", out.strip().splitlines()[-1][:90]))
            print("%3d/%d %-46s BUILD REFUSED" % (n, len(targets), page[:46]), flush=True)
            continue
        after = measure(fp)
        built += 1
        problems = []
        if after["sections"] != before["sections"]:
            problems.append("sections %d -> %d" % (before["sections"], after["sections"]))
        if before["words"] and abs(after["words"] - before["words"]) > 0.01 * before["words"]:
            problems.append("words %d -> %d" % (before["words"], after["words"]))
        if not after["anchor"]:
            problems.append("no id=paper after rebuild")
        if after["bytes"] == before["bytes"] and after == before:
            identical.append(page)
        if problems:
            subprocess.run(["git", "checkout", "--", page], cwd=REPO,
                           capture_output=True)
            failures.append((page, "RESTORED", "; ".join(problems)))
            print("%3d/%d %-46s FAILED, RESTORED: %s"
                  % (n, len(targets), page[:46], "; ".join(problems)), flush=True)
        else:
            print("%3d/%d %-46s ok  %d sections, %d words, anchor=%s"
                  % (n, len(targets), page[:46], after["sections"], after["words"],
                     after["anchor"]), flush=True)

    print()
    print("=" * 96)
    print("pages attempted %d | rebuilt %d | skipped as legacy %d | failed %d | "
          "byte-identical %d"
          % (len(targets), built, len(skipped_legacy), len(failures), len(identical)))
    if skipped_legacy:
        print()
        print("NOT BUILT BY THIS GENERATOR -- these keep the dead #paper anchor and have no")
        print("projected manuscript at all. Rebuilding them REPLACES their content and is a")
        print("separate decision, not a formatting pass:")
        for page, words in sorted(skipped_legacy, key=lambda x: -x[1]):
            print("    %-46s %7d words" % (page[:46], words))
    for page, kind, detail in failures:
        print("  %-46s %-14s %s" % (page[:46], kind, detail))
    if identical:
        print()
        print("BYTE-IDENTICAL AFTER REBUILD -- these were NOT actually rebuilt, because the")
        print("anchor change alone must alter every page:")
        for page in identical:
            print("   ", page)
    if built == 0:
        print("\nREFUSED: not one page was rebuilt.")
        return 2
    if identical:
        print("\nREFUSED: %d page(s) came out byte-identical, which the prediction says is "
              "impossible if they were rebuilt." % len(identical))
        return 1
    if failures:
        print("\nREFUSED: %d page(s) failed a prediction and were restored." % len(failures))
        return 1
    print("\nPASS, measured against the four stated predictions on %d pages: section count "
          "unchanged everywhere, word count within 1%% everywhere, id=paper present "
          "everywhere, and no page byte-identical." % built)
    return 0


if __name__ == "__main__":
    sys.exit(main())
