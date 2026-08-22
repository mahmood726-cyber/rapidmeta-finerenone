"""Disclose, IN THE ABSTRACT, the outcomes an object holds and does not publish.

WHY THE ABSTRACT AND NOT BESIDE THE ESTIMATE. The withdrawal was already recorded -- on the
outcome that was withdrawn. A reader who never scrolls to that outcome never meets it, and the
abstract is where the impression forms. A disclosure a reader reaches only by looking for it is
a disclosure for us and not for them.

FOUND BY A BLIND CROSS-FAMILY READ. GPT-5, given the object and the abstract and none of our
conclusions, said a reader "would reasonably conclude the review publishes a pooled estimate
across all relevant trials", and that the object does not support that. The sweep
`sweep_abstract_omits_withdrawn_2026_08_22.py` generalised it to 7 topics.

WHAT IS WRITTEN, AND WHAT IS NOT. One sentence naming the outcomes not published and, where the
object records one, the reason in its own words. NO ESTIMATE MOVES. Nothing is withdrawn or
un-withdrawn here; the abstract stops being silent about what the object already says.
"""
import io
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "ssot"))
import atomic_write                                            # noqa: E402

TODAY = "2026-08-22"
FIELD = "what_this_review_does_not_publish_%s" % TODAY.replace("-", "_")
HITS = os.path.join(REPO, "outputs", "abstract_omits_withdrawn_2026_08_22.json")


def phrase(oid, k, why):
    name = oid.replace("_", " ")
    why = (why or "").strip()
    if why.lower().startswith("not pooled"):
        return "%s (k=%s), which is not pooled" % (name, k)
    first = why.split(".")[0].strip()
    if len(first) > 190:
        first = first[:190].rsplit(" ", 1)[0] + "..."
    return "%s (k=%s) -- %s" % (name, k, first)


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    dry = "--apply" not in sys.argv
    if not os.path.isfile(HITS):
        sys.exit("REFUSED: run sweep_abstract_omits_withdrawn_2026_08_22.py first -- this "
                 "applies what that measured and does not re-derive it.")
    hits = json.load(io.open(HITS, encoding="utf-8"))
    if not hits:
        sys.exit("REFUSED: the sweep found nothing. Applying a disclosure to no topic is not "
                 "a no-op worth recording; check the sweep.")
    n = 0
    for h in hits:
        t = h["topic"]
        p = os.path.join(REPO, "ssot", t, t + ".json")
        obj = json.load(io.open(p, encoding="utf-8"))
        others = [phrase(oid, k, why) for oid, k, why in h["unmentioned"]]
        claims = ", ".join("%s at k=%s" % (pt, k) for _oid, pt, k in h["abstract_claims"])
        # PROSE, NOT A FIELD DUMP. The first version read "This object also holds 1
        # outcome(s) for which no pooled estimate is published" -- it named the DATA OBJECT to
        # a reader of a paper and used programmatic pluralisation. Caught by a blind read from
        # a third model family (Gemini 3.1 Pro), whose rewrite is adopted almost verbatim. It
        # is the same "reads like code" class raised five times, reintroduced by the fix for a
        # different one.
        _n = len(others)
        _count = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five",
                  6: "six", 7: "seven", 8: "eight"}.get(_n, str(_n))
        obj[FIELD] = (
            "WHAT THIS REVIEW DOES NOT PUBLISH. This review also examined %s outcome%s for "
            "which no pooled estimate is published: %s. "
            % (_count, "" if _n == 1 else "s", "; ".join(others)) + (
            "Each is recorded with its reason, and none of them is part of the estimate "
            "reported above (%s). A reader meeting the pooled result should not take it as "
            "covering every outcome, or every trial, this review examined. "
            "This sentence exists because a second, independent reading -- by a different "
            "model family, given the object and the abstract and none of our conclusions -- "
            "found that a reader would reasonably conclude the review pools all relevant "
            "trials, and that the object does not support that. The withdrawals were already "
            "recorded beside the outcomes they concern; they were invisible from the abstract, "
            "which is where the impression forms." % (claims or "above")))
        obj.setdefault("display_change_announced", []).append({
            "date": TODAY,
            "change": "the abstract now names the outcomes this review does not publish",
            "values_moved": "NONE -- no estimate, interval, rating or withdrawal changes",
            "what_changed": "one disclosure sentence, rendered with the abstract",
            "why": ("The withdrawals were recorded only beside the outcomes they concern, "
                    "which a reader of the abstract never reaches."),
        })
        n += 1
        print("%-44s %d unpublished outcome(s) named" % (t[:44], len(others)))
        if not dry:
            atomic_write.write_json(p, obj, indent=1)
    print("\n%d topic(s)" % n)
    if dry:
        print("DRY RUN -- pass --apply to write")


if __name__ == "__main__":
    main()
