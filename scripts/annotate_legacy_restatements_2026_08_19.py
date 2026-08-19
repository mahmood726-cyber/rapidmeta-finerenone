"""GIVE THE TWO LEGACY RESTATEMENT BLOCKS A COMMAND THAT RE-DERIVES THEM (P18).

`restated_2026_08_19_placebo_discriminator` lives on the OBJECT rather than in the builder's
per-topic spec, so it is annotated here. Both blocks narrate a delta that, until
`scripts/regate_across_revisions.py` existed, no command could reproduce -- which is precisely
the condition that let sglt2-hf's cascade go stale while looking corrected.

AND ONE OF THE TWO NARRATES ITS DELTA WRONG. Re-derived across every commit that touched the
classifier, bempedoic-acid-review went:

    e6c08d3be  17 / 4 / 0
    92d84da72  15 / 4 / 2    <- the BOTH-ARMS rule moved NCT06450366 and NCT07614958
                                experimental -> background
    f2bf16022  16 / 3 / 2    <- the PLACEBO-DISCRIMINATOR moved NCT05263778
                                comparator -> EXPERIMENTAL
    e20f94068  16 / 5 / 0    <- the same two records moved background -> comparator

The stored sentence says the placebo-discriminator "moved one to comparator and two to
background". It caused NEITHER of those: the two-to-background move belongs to an earlier
commit, and its own single move ran in the OPPOSITE direction.

    THE NUMBER 16 WAS RIGHT AND THE STORY OF HOW IT GOT THERE WAS WRONG -- the same class as
    P15, one stage later. A reader checks a verdict against its reason, and nothing downstream
    ever recomputes a reason.

The original text is kept beside the correction, not replaced.
"""
import io
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KEY = "restated_2026_08_19_placebo_discriminator"

REPRODUCER = (
    "scripts/regate_across_revisions.py <topic> -- re-executes this topic's own recorded "
    "query, loads EVERY revision of ssot/topic_identity.py from git, and reports at which of "
    "them the stored cascade reproduces. Added 2026-08-19 under PAGE-STANDARD P18, after "
    "sglt2-hf's cascade was found to reproduce at exactly one revision and no other while "
    "carrying a restatement note that made it look current.")

PATCH = {
    "sglt2-hf": {
        "reproduced_by": REPRODUCER,
        "verified_2026_08_19": (
            "36 -> 46 CONFIRMED at f2bf16022: ten records moved comparator -> experimental "
            "there, and the attribution in this block is correct. What was NOT correct is that "
            "the block was left standing as the current state after two further revisions "
            "moved three more records. Those are at "
            "k_cascade.restated_2026_08_19_two_missed_revisions."),
    },
    "bempedoic-acid-review": {
        "reproduced_by": REPRODUCER,
        "attribution_corrected_2026_08_19": (
            "THIS BLOCK'S NUMBER IS RIGHT AND ITS ATTRIBUTION IS WRONG, and only a walk across "
            "revisions could show it. 17 -> 16 is not one move by the placebo-discriminator. "
            "It is 17 -> 15 at 92d84da72, where the BOTH-ARMS rule moved NCT06450366 and "
            "NCT07614958 experimental -> background, then 15 -> 16 at f2bf16022, where the "
            "placebo-discriminator moved NCT05263778 comparator -> EXPERIMENTAL. The stored "
            "sentence credits the placebo-discriminator with the entire delta and describes "
            "its single move in the opposite direction to the one it made. A CORRECT NUMBER "
            "REACHED BY A WRONG ACCOUNT passes every check that reads quantities."),
    },
}


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    rc = 0
    for topic, extra in sorted(PATCH.items()):
        path = os.path.join(REPO, "ssot", topic, topic + ".json")
        with io.open(path, encoding="utf-8") as fh:
            obj = json.load(fh)
        blk = (obj.get("k_cascade") or {}).get(KEY)
        if not isinstance(blk, dict):
            print("%-24s NOT_ASSESSABLE: no %s block to annotate" % (topic, KEY))
            rc = 1
            continue
        blk.update(extra)
        with io.open(path, "w", encoding="utf-8") as fh:
            fh.write(json.dumps(obj, indent=1, ensure_ascii=True))
        print("%-24s annotated: %s" % (topic, ", ".join(sorted(extra))))
    return rc


if __name__ == "__main__":
    sys.exit(main())
