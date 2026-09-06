# -*- coding: utf-8 -*-
"""How much of the corpus k is a hand-typed identifier, and how much was discovered.

THE CLAIM THIS TESTS. This lane was handed the premise that "141 hand-typed NCT ids ARE the
corpus k -- ingestion is a hand-typed dict in scripts/add_topic_autodiscover.py". The second
half is measurably false in that file: it contains ZERO literal NCT ids and discovers its
candidates by scanning an AACT snapshot. The first half is a question about the whole corpus
and is worth an actual number rather than a correction, so this counts it.

WHAT IS HAND-TYPED HERE IS THE QUESTION, NOT THE ANSWER. The hand-maintained object in the
autodiscovery path is TOPICS: 2,229 entries under 1,893 distinct stems, of which 335 collide
and 158 of those collisions carry DIFFERENT condition patterns -- one question silently
replacing another, both writing the same output file. That is the hand-typed thing which
does determine the corpus, and scripts/lint_topic_stem_collisions.py is the ratchet on it.

METHOD, AND ITS LIMIT STATED UP FRONT. Two populations are counted and intersected:
identifiers written as literals anywhere under scripts/, and identifiers appearing in the
delivered *_REVIEW*.html pages. The intersection is an UPPER BOUND on the hand-typed share:
a registration can appear in a script because it was typed in to seed a topic, and equally
because a later audit or screening script listed something discovery had already found.
This instrument cannot tell those apart, so it reports the bound and says so rather than
reporting a share it cannot support.

    AN UPPER BOUND THAT REFUTES A CLAIM IS STILL A REFUTATION. If at most 20% of the corpus
    is hand-typed, "the hand-typed ids ARE the corpus k" is false whichever way the
    remaining ambiguity resolves.
"""
from __future__ import annotations

import glob
import io
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from instrument_controls import require_controls  # noqa: E402

if hasattr(sys.stdout, "buffer") and getattr(sys.stdout, "encoding", "").lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
NCT = re.compile(r"NCT\d{8}")


def ids_in(paths):
    found = {}
    for p in paths:
        try:
            with io.open(p, encoding="utf-8", errors="replace") as fh:
                hits = set(NCT.findall(fh.read()))
        except OSError:
            continue
        if hits:
            found[p] = hits
    return found


def controls():
    """The extractor must find a planted id and must not invent one.

    POSITIVE  a string containing NCT01234567 must yield exactly that id. A scan returning
              nothing and a corpus containing nothing are the same output otherwise.
    NEGATIVE  a string containing NCT123 (too short) and NCT012345678901 must not yield a
              spurious id -- the over-matching direction, which would inflate BOTH
              populations at once and drag the intersection toward a false agreement.
    """
    pos = sorted(NCT.findall("see NCT01234567 for detail"))
    neg = sorted(NCT.findall("NCT123 and NCTABCDEFGH and nct01234567"))
    return pos, neg


def main(argv):
    out_path = Path(argv[1]) if len(argv) > 1 else None
    pos, neg = controls()
    require_controls(
        "measure_handtyped_share_of_k",
        ("planted NCT01234567 in a sentence", pos, ["NCT01234567"]),
        ("too-short / lowercase / non-numeric forms", neg, ["NCT01234567"]),
    )

    scripts = ids_in(sorted(glob.glob(str(ROOT / "scripts" / "**" / "*.py"), recursive=True)))
    pages_paths = [p for p in sorted(glob.glob(str(ROOT / "*_REVIEW*.html")))
                   if "backup" not in os.path.basename(p)]
    pages = ids_in(pages_paths)

    hand = set().union(*scripts.values()) if scripts else set()
    corpus = set().union(*pages.values()) if pages else set()

    print("")
    print("scripts/ files carrying a literal NCT id   %d" % len(scripts))
    print("distinct hand-typed NCT ids in scripts/    %d" % len(hand))
    print("delivered *_REVIEW*.html pages scanned     %d  (of %d matched, %d excluded as backups)"
          % (len(pages_paths), len(glob.glob(str(ROOT / "*_REVIEW*.html"))),
             len(glob.glob(str(ROOT / "*_REVIEW*.html"))) - len(pages_paths)))
    print("distinct NCT ids across the corpus         %d   <- the corpus k" % len(corpus))
    if not corpus:
        print("NOT_RUN -- no delivered page yielded an identifier, so no share was computed. "
              "This is not a reading of zero hand-typed.")
        return 1

    overlap = corpus & hand
    print("")
    print("corpus ids ALSO written literally in scripts/  %d   %.1f%%  <- UPPER BOUND on the "
          "hand-typed share" % (len(overlap), 100.0 * len(overlap) / len(corpus)))
    print("corpus ids not typed literally anywhere       %d   %.1f%%"
          % (len(corpus - hand), 100.0 * len(corpus - hand) / len(corpus)))
    print("hand-typed ids that are NOT in any page        %d   (typed for audits, screens and "
          "benchmarks rather than for ingestion)" % len(hand - corpus))
    print("")
    print("The share is an UPPER BOUND: an id can appear in a script because it was typed in "
          "to seed a topic, or because a later audit listed one discovery had already found. "
          "This cannot separate them and does not pretend to.")

    top = sorted(scripts.items(), key=lambda kv: -len(kv[1]))[:8]
    print("")
    print("scripts holding the most literal ids:")
    for p, v in top:
        print("   %4d  %s" % (len(v), os.path.relpath(p, ROOT).replace(os.sep, "/")))

    if out_path:
        out_path.write_text(json.dumps({
            "instrument": "measure_handtyped_share_of_k_2026_09_03",
            "scripts_with_literal_ncts": len(scripts),
            "distinct_handtyped_ncts": len(hand),
            "pages_scanned": len(pages_paths),
            "corpus_distinct_ncts": len(corpus),
            "overlap": len(overlap),
            "handtyped_share_upper_bound_pct": round(100.0 * len(overlap) / len(corpus), 1),
            "corpus_not_handtyped": len(corpus - hand),
            "handtyped_not_in_any_page": len(hand - corpus),
            "note": ("overlap is an UPPER BOUND on the hand-typed share; an id can appear in "
                     "a script because it seeded a topic or because an audit listed one that "
                     "discovery found."),
        }, indent=2), encoding="utf-8")
        print("")
        print("wrote %s" % out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
