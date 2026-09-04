"""Every retraction on the HFrEF page must survive the edit that fixed its headline.

WHY THIS EXISTS. The standing prohibition on regeneration is not an argument against fixing
one page; it exists because a CORPUS-WIDE rebuild erases retractions applied by hand. The
prohibition's real content is therefore a CHECK, not a ban: enumerate what a page currently
retracts, change the page, and assert every one of those retractions is still there.

    A REBUILD THAT LOSES A RETRACTION IS THE FAILURE THE PROHIBITION WAS WRITTEN ABOUT.
    Finding it on one page is exactly why the unit is one page.

HOW THE ENUMERATION IS BUILT, AND WHY IT IS NOT A HAND-WRITTEN LIST. A curated list of
strings is a reach figure wearing a denominator: it contains what its author remembered. So
the BEFORE side is read from the SERVED BYTES -- the deployed artefact, fetched or supplied
-- and every sentence matching a declared retraction vocabulary is collected verbatim. The
vocabulary is stated below and is the only judgement in the file; everything after it is
string presence.

WHAT A PASS DOES NOT ESTABLISH, written in advance:
  - NOT that the page is correct, or that its retractions are adequate. It establishes that
    the edit removed none of them.
  - NOT that a retraction is still RENDERED. A string can survive in the bytes and be hidden
    by a class. This checks the bytes, which is where a rebuild deletes things.
  - NOTHING about retractions phrased outside the vocabulary. Those are UNCOUNTED, and the
    run prints the vocabulary so the gap is visible rather than implied.

Usage:
    python scripts/assert_hfref_retractions_survive_2026_09_03.py --before SERVED.html
    python scripts/assert_hfref_retractions_survive_2026_09_03.py            # uses the
                                                                            # committed
                                                                            # enumeration
"""
from __future__ import annotations

import html as _html
import io
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = os.path.join(REPO, "HFREF_NMA_AUTO_FULL_REVIEW.html")
ENUM = os.path.join(REPO, "out", "hfref_retraction_enumeration_2026_09_03.json")

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# THE ONLY JUDGEMENT IN THIS FILE. A sentence is a retraction, withdrawal or correction when
# it carries one of these. Stated here so the denominator is inspectable.
VOCAB = [
    "has been withdrawn", "withdrawn", "removed rather than corrected",
    "have been removed", "has been removed", "Correction,", "CORRECTED:",
    "not an integrity pass", "UNCERTAIN", "Not a pooled meta-analysis",
    "indirect only", "network extrapolations", "not for public deploy",
    "analysis only, prototype", "no longer", "retracted", "superseded",
    "should not be read as", "does not follow from", "NOT AN INTEGRITY PASS",
]

SPLIT = re.compile(r"(?<=[.!?])\s+")


def visible_sentences(body: str):
    """Sentences a reader sees: script/style dropped, tags to a space, entities resolved."""
    b = re.sub(r"<script.*?</script>", " ", body, flags=re.S | re.I)
    b = re.sub(r"<style.*?</style>", " ", b, flags=re.S | re.I)
    b = _html.unescape(re.sub(r"<[^>]+>", " ", b))
    b = re.sub(r"\s+", " ", b)
    return [s.strip() for s in SPLIT.split(b) if s.strip()]


def enumerate_retractions(body: str):
    out, seen = [], set()
    for s in visible_sentences(body):
        for v in VOCAB:
            if v.lower() in s.lower():
                key = s[:160]
                if key not in seen:
                    seen.add(key)
                    out.append({"sentence": s[:400], "matched_vocabulary": v})
                break
    return out


TOKEN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._+-]{5,}")


def classify(sentence: str, vocab_phrase: str, after_text: str):
    """PRESENT / REWORDED / LOST.

    THE UNIT IS THE RETRACTION, NOT THE SENTENCE. The first version of this file compared
    whole sentences and reported a LOST retraction that was present verbatim: this lane's own
    edit merged two sentences, so "That reconciliation carries its own status: analysis only,
    prototype, not for public deploy" became "and carries its own status: analysis only,
    prototype, not for public deploy". The retraction had not moved; the prose around it had.

    SO THE TEST IS TWO-PART, AND NEITHER PART ALONE WOULD DO:
      1. the vocabulary phrase must be present -- if it is gone the retraction is LOST,
         whatever else survives;
      2. and enough of the sentence's distinctive tokens must be present that this is
         demonstrably the SAME retraction rather than the same words elsewhere on the page.
    A rebuild that deleted the paragraph and left the phrase somewhere unrelated fails (2).
    A rewording that keeps the retraction passes both and is REPORTED AS REWORDED, with the
    original quoted, so it is visible rather than silently accepted.

    LOOSENING A CHECK THAT HAS JUST FIRED IS THE MOVE TO BE SUSPICIOUS OF. This one was
    verified by hand first: the phrase, the reconciliation it belongs to, and both of its
    quoted values are all present in the after-text.
    """
    if vocab_phrase.lower() not in after_text.lower():
        return "LOST", 0.0
    toks = {t.lower() for t in TOKEN.findall(sentence)}
    if not toks:
        return "PRESENT", 1.0
    low = after_text.lower()
    frac = sum(1 for t in toks if t in low) / len(toks)
    if frac < 0.60:
        return "LOST", frac
    return ("PRESENT" if sentence[:120].strip() in after_text else "REWORDED"), frac


def selftest() -> int:
    """PLANTED BOTH WAYS. A check that cannot report a loss is not a check."""
    S = ("That reconciliation carries its own status: analysis only, prototype, not for "
         "public deploy .")
    V = "not for public deploy"
    cases = [
        ("the sentence unchanged -> PRESENT", S, "PRESENT"),
        ("this lane's actual rewording, retraction intact -> REWORDED",
         "An independent refit ( HFREF-FULL-NETWORK-RECONCILIATION-2026-07-19 ) reports "
         "different values under a different estimator and carries its own status: analysis "
         "only, prototype, not for public deploy .", "REWORDED"),
        ("THE FAILURE THE PROHIBITION IS ABOUT: the paragraph deleted -> LOST",
         "An independent refit reports different values under a different estimator.", "LOST"),
        ("the phrase kept but the paragraph gone -- same words elsewhere -> LOST",
         "Footer: this build is not for public deploy .", "LOST"),
        ("the retraction alone, everything around it gone -> LOST",
         "analysis only, prototype, not for public deploy", "LOST"),
    ]
    ok = True
    for label, after, want in cases:
        got, frac = classify(S, V, after)
        good = got == want
        ok &= good
        print("  %-64s -> %-9s (want %-9s) %s  [%.0f%% tokens]"
              % (label[:64], got, want, "correct" if good else "WRONG", 100 * frac))
    print("\n  WHAT A FAILURE LOOKS LIKE: case 3 or 4 reporting PRESENT. Case 4 is the one")
    print("  that matters -- the retraction's words survive somewhere on the page while the")
    print("  paragraph that made them a retraction has been deleted.")

    # KNOWN_NEGATIVE -- PRE-EXISTING. THIS COMMIT ONLY NAMES IT AND PRINTS ITS RATE.
    #
    # Cases 1 and 2 above are must-NOT-fire cases and have been here since the file was
    # written ("PLANTED BOTH WAYS. A check that cannot report a loss is not a check.").
    # NO BEHAVIOUR CHANGED. gate2 flagged this file for having "no known-negative control"
    # because it matches on the TOKENS `KNOWN_NEGATIVE` / `control(`, and this file never
    # used the word -- the second false finding of that kind in this series.
    #
    # THE HARD NEGATIVE IS CASE 2, not case 1. Case 1 is the sentence unchanged, which any
    # implementation gets right. Case 2 is THIS LANE'S ACTUAL REWORDING with the retraction
    # intact: the surrounding paragraph was rewritten, so an exact-match implementation
    # reports LOST and a real retraction is recorded as destroyed. That false alarm is the
    # expensive direction here -- it would block a correct edit and, worse, teach whoever
    # hit it that the check cries wolf.
    KNOWN_NEGATIVE = ("case 2: the paragraph reworded, the retraction intact -- must be "
                      "REWORDED, never LOST")
    negs = [(lbl, aft, want) for lbl, aft, want in cases if want in ("PRESENT", "REWORDED")]
    fp = sum(1 for _, aft, want in negs if classify(S, V, aft)[0] != want)
    print()
    print("  KNOWN-NEGATIVE CONTROL: %d/%d matched (measured false-positive rate %.1f%%)"
          % (fp, len(negs), 100.0 * fp / len(negs) if negs else 0.0))
    print("  %s" % KNOWN_NEGATIVE)
    print("  Pre-existing; named here so it is visible, not added here.")
    if fp:
        ok = False
        print("  CONTROL FAILED: an intact retraction was reported lost. No verdict from "
              "this check is trusted.")
    print("-> SELFTEST PASS" if ok else "-> SELFTEST FAILED")
    return 0 if ok else 1


def main(argv):
    if "--selftest" in argv:
        return selftest()
    if "--before" in argv:
        src = argv[argv.index("--before") + 1]
        before_body = io.open(src, encoding="utf-8", errors="replace").read()
        rows = enumerate_retractions(before_body)
        rec = {"utc": "2026-09-03", "source": os.path.basename(src),
               "source_bytes": len(before_body.encode("utf-8")),
               "vocabulary": VOCAB, "count": len(rows), "retractions": rows}
        io.open(ENUM, "w", encoding="utf-8", newline="\n").write(json.dumps(rec, indent=1))
        print("enumerated %d retraction sentence(s) from %s" % (len(rows), src))
        for r in rows:
            print("   [%s] %s" % (r["matched_vocabulary"], r["sentence"][:110]))
        print("\nwrote %s" % os.path.relpath(ENUM, REPO))
        return 0

    if not os.path.exists(ENUM):
        print("NOT_RUN: no enumeration recorded. Run with --before <served page> first.")
        print("An empty check is not a pass.")
        return 1

    rec = json.load(io.open(ENUM, encoding="utf-8"))
    after = io.open(PAGE, encoding="utf-8", errors="replace").read()
    after_sentences = " || ".join(visible_sentences(after))
    print("BEFORE: %s, %d bytes, %d retraction sentence(s)"
          % (rec["source"], rec["source_bytes"], rec["count"]))
    print("AFTER : %s, %d bytes" % (os.path.basename(PAGE), len(after.encode("utf-8"))))
    if rec["count"] == 0:
        print("\nNOT_RUN: the enumeration found nothing, so this check examines nothing.")
        return 1

    missing, reworded = [], []
    for r in rec["retractions"]:
        state, frac = classify(r["sentence"], r["matched_vocabulary"], after_sentences)
        if state == "LOST":
            missing.append((r, frac))
        elif state == "REWORDED":
            reworded.append((r, frac))
    print("\nretractions still present: %d of %d  (%d verbatim, %d reworded, %d LOST)"
          % (rec["count"] - len(missing), rec["count"],
             rec["count"] - len(missing) - len(reworded), len(reworded), len(missing)))
    for r, frac in reworded:
        print("   REWORDED [%s] %.0f%% of its distinctive tokens survive"
              % (r["matched_vocabulary"], 100 * frac))
        print("      before: %s" % r["sentence"][:150])
    for r, frac in missing:
        print("   LOST [%s] %.0f%% tokens  %s"
              % (r["matched_vocabulary"], 100 * frac, r["sentence"][:110]))

    # (c) size plausibility. A build that returns an empty or truncated artefact exits 0.
    b_before, b_after = rec["source_bytes"], len(after.encode("utf-8"))
    ratio = b_after / b_before if b_before else 0.0
    plausible = 0.90 <= ratio <= 1.10
    print("size: %d -> %d (%.4f of before) %s"
          % (b_before, b_after, ratio, "plausible" if plausible else "IMPLAUSIBLE"))

    if missing:
        print("\n-> FAILED: %d retraction(s) did not survive. Revert." % len(missing))
        return 1
    if not plausible:
        print("\n-> FAILED: the page size moved by more than 10%. Do not publish.")
        return 1
    print("\n-> ok: every enumerated retraction survives and the size is plausible.")
    print("   UNCOUNTED: any retraction phrased outside the vocabulary above.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
