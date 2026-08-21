"""The stored disagreement rate stands as measured. Re-run the same count on the object as it now is.

APPLYING THE D1 GUIDANCE MADE FOURTEEN PAGES CONTRADICT THEMSELVES. Each carries a second
assessor block whose `PER_DOMAIN` reads `D1: 2 of 2 disagree` -- a comparison made when this
assessment said LOW -- printed inches from a table that now says NO_INFORMATION, which is what
assessor 2 said. The page asserts a live disagreement its own object no longer holds.

TWO WRONG WAYS TO FIX IT, AND WHY EACH IS WRONG.

    OVERWRITE THE RATE. It is a published number on live pages, and correcting one silently is
    not this project's to do. It would also delete the finding: that a blind second assessor
    disagreed on D1 across the corpus is the reason the guidance was re-read at all. A record
    that is edited whenever it is acted on stops being a record.

    RECOMPUTE AND REPLACE. Same objection, plus it destroys the only evidence that the change
    was warranted. The disagreement is WHY the object moved; erasing it leaves the move
    unexplained.

SO BOTH NUMBERS ARE WRITTEN AND BOTH ARE LABELLED. The stored rate keeps its wording and its
date. Beside it goes the same computation re-run against the object as it now stands, saying
which axis moved and why.

AND THE RECOUNT IS COMPUTED, NEVER ASSERTED. It parses assessor 2's `verbatim_reply` -- stored
on the object -- and compares it against the object's current judgements, through
`second_assessor_reconcile`'s own `align`, `norm` and `first_assessment`. IMPORTED, NOT COPIED:
a second implementation of the domain-prefix matching would drift from the first, and that
matching is where six separate under-counts have already been found in this run.

WHY THIS IS NOT "D1 IS NOW RESOLVED EVERYWHERE". `sglt2-hf` records `D1: 9 of 9 disagree` and
only 5 of its D1 judgements were LOW; the other 4 were SOME_CONCERNS, which assessor 2 also
disagreed with, and which this change does not touch. A note claiming the D1 disagreement had
been resolved would be false on that topic. The recount is computed per topic for exactly that
reason -- the number is different on different topics, and only measuring tells you which.
"""
import glob
import importlib.util
import io
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "ssot"))
import atomic_write                                            # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "sar", os.path.join(REPO, "scripts", "second_assessor_reconcile.py"))
sar = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sar)

TODAY = "2026-08-21"
FIELD = "RECOUNTED_AFTER_THE_D1_RESOLUTION_%s" % TODAY.replace("-", "_")


def parse_reply(text):
    out = {}
    for line in str(text or "").splitlines():
        m = sar.LINE.match(line.strip())
        if m:
            out[m.group(1)] = dict(zip(sar.DOMS, [sar.norm(x) for x in m.groups()[1:]]))
    return out


def count(mine, theirs):
    dis = cmp = 0
    bydom = {d: [0, 0] for d in sar.DOMS}
    for rid, row in sorted(theirs.items()):
        if rid not in mine:
            continue
        for d in sar.DOMS:
            a, b = mine[rid].get(d), row.get(d)
            if not a or not b:
                continue
            cmp += 1
            bydom[d][1] += 1
            if a != b:
                dis += 1
                bydom[d][0] += 1
    return dis, cmp, bydom


HOUSE_RULE = (
    "BOTH ASSESSORS READ THE SAME ABSENCE OF A CONCEALMENT METHOD, so this is a house-rule "
    "divergence and not an evidential one. RoB 2's algorithm answers SOME CONCERNS when 1.2 is "
    "`No information` and there is no baseline concern; this project writes NO_INFORMATION on "
    "the domain instead, so a reader can tell a domain nobody could evaluate from a domain "
    "evaluated and found wanting. Both cap OVERALL at the same place. The disagreement is real "
    "and it is about vocabulary.")


def d1_left_note(mine, theirs):
    """Describe the D1 disagreements that REMAIN, from the pairs themselves."""
    pairs = {}
    for rid, row in theirs.items():
        if rid not in mine:
            continue
        a, b = mine[rid].get("D1"), row.get("D1")
        if a and b and a != b:
            pairs["%s / %s" % (a, b)] = pairs.get("%s / %s" % (a, b), 0) + 1
    if not pairs:
        return "D1 now agrees with assessor 2 on every compared result."
    shape = "; ".join("%d where this assessment says %s and assessor 2 says %s"
                      % (n, k.split(" / ")[0], k.split(" / ")[1])
                      for k, n in sorted(pairs.items(), key=lambda kv: -kv[1]))
    return "%d D1 disagreement(s) remain -- %s. %s" % (sum(pairs.values()), shape, HOUSE_RULE)


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    dry = "--apply" not in sys.argv
    touched = refused = 0
    # THE TWO SKIPS BELOW ARE EXCLUSIONS BY ABSENCE, AND EITHER COULD SILENTLY DO NOTHING.
    #
    # `if not keys` skips a topic with no second-assessor block; `if not moved` skips one where
    # no D1 moved. Both are correct as written -- and both read the same way when the LOOKUP is
    # broken as when the property is genuinely absent. If `resolved_2026_08_21` were spelled
    # wrong, every topic would report `moved = 0`, the script would touch nothing, print
    # `0 topic(s) recounted`, and exit 0. That is the exact shape of the six class-83
    # under-counts already found in this run, all of which pointed at the data.
    #
    # So the two absences are counted and the run FAILS CLOSED if either is universal. A skip
    # that can only ever skip is not a skip, it is a broken lookup with a tidy exit code.
    seen_blocks = seen_moved = 0
    for path in sorted(glob.glob(os.path.join(REPO, "ssot", "*", "*.json"))):
        topic = os.path.basename(os.path.dirname(path))
        if os.path.basename(path) != topic + ".json":
            continue
        obj = json.load(io.open(path, encoding="utf-8"))
        rob = obj.get("risk_of_bias") or {}
        keys = [k for k in rob if str(k).startswith("SECOND_ASSESSOR")]
        if not keys:
            continue
        seen_blocks += 1
        blk = rob[keys[0]]
        if not isinstance(blk, dict):
            continue
        already = FIELD in blk

        # DID ANY D1 ON THIS TOPIC ACTUALLY MOVE? If none did, the stored rate still describes
        # the object and adding a note saying it was re-checked would be apparatus, not a
        # finding. Nothing is written on those topics.
        moved = 0
        for per in (rob.get("by_outcome") or {}).values():
            if not isinstance(per, dict):
                continue
            for j in per.values():
                if not isinstance(j, dict):
                    continue
                for k, v in (j.get("domains") or {}).items():
                    if (str(k).upper().startswith("D1") and isinstance(v, dict)
                            and v.get("resolved_%s" % TODAY.replace("-", "_"))):
                        moved += 1
        if not moved:
            continue
        # COUNTED BEFORE THE ALREADY-WRITTEN SKIP, NOT AFTER.
        # Placed after it, the floor fires on the second run of an idempotent script -- every
        # topic already carries the field, nothing is recounted, and a correct no-op is
        # reported as a broken lookup. A floor that fails on success is worse than no floor:
        # it teaches you to ignore it.
        seen_moved += 1
        if already:
            continue

        theirs = parse_reply(blk.get("verbatim_reply"))
        if not theirs:
            print("   REFUSED %-42s the stored reply does not parse -- the recount would be "
                  "of nothing" % topic[:42])
            refused += 1
            continue
        mine = sar.first_assessment(topic)
        theirs = sar.align(mine, theirs)
        matched = [r for r in theirs if r in mine]
        if not matched:
            print("   REFUSED %-42s no reply row aligns to a stored result -- reported rather "
                  "than counted as zero disagreement" % topic[:42])
            refused += 1
            continue

        dis, cmp, bydom = count(mine, theirs)
        per_domain = {d: "%d of %d disagree" % (bydom[d][0], bydom[d][1])
                      for d in sar.DOMS if bydom[d][1]}
        stored_rate = str(blk.get("DISAGREEMENT_RATE") or "").strip()
        stored_d1 = str((blk.get("PER_DOMAIN") or {}).get("D1") or "").strip()

        blk[FIELD] = {
            "why_this_field_exists": (
                "On %s this review's D1 judgements moved from LOW to NO_INFORMATION on the "
                "RoB 2 guidance -- the position assessor 2 had taken. The rate above was "
                "measured BEFORE that and is left exactly as measured: it is a published "
                "number, it is the record of what a blind second assessor said, and it is the "
                "reason the guidance was re-read. Editing it would delete the evidence that "
                "the change was warranted. This is the same computation re-run on the object "
                "as it now stands, so both are visible and neither is silently corrected."
                % TODAY),
            "as_measured_before": stored_rate or "(not recorded)",
            "recounted_now": "%d of %d judgements -- %.1f%%" % (dis, cmp,
                                                                100.0 * dis / cmp) if cmp else
                             "(nothing comparable)",
            "PER_DOMAIN_recounted_now": per_domain,
            "D1_before": stored_d1 or "(not recorded)",
            "D1_now": per_domain.get("D1", "(not compared)"),
            "what_moved_and_what_did_not": (
                "%d D1 judgement(s) on this topic moved. Any D1 disagreement that REMAINS is "
                "one where this assessment said SOME_CONCERNS rather than LOW -- assessor 2 "
                "said NO_INFORMATION there too, and the guidance applied here speaks to LOW, "
                "not to SOME_CONCERNS. So a claim that 'the D1 disagreement is resolved' would "
                "be false wherever those two numbers differ, which is why the count is re-run "
                "per topic instead of asserted once." % moved),
            # THE DIRECTION IS READ OFF THE PAIRS, NEVER ASSUMED.
            #
            # A first version wrote one sentence for every topic with a D1 disagreement left --
            # "assessor 2 said SOME_CONCERNS" -- because that is what the first two topics
            # examined showed. On `sglt2-hf` the remaining four run the OTHER WAY: THIS
            # assessment says SOME_CONCERNS and assessor 2 says NO_INFORMATION. The sentence
            # would have described the wrong assessor on the one topic with the most of them.
            # Class 73 again: an entry misdescribing its own item, from generalising two cases.
            "why_D1_still_disagrees_here": d1_left_note(mine, theirs),
            "and_it_bounds_a_finding_of_ours": (
                "Class 94 records assessor 2 saying NO_INFORMATION on D1/D2/D3 `100 of 100`. "
                "Measured across all 23 topics now stored that is 239 of 243, and ALL FOUR "
                "exceptions are D1=SOME_CONCERNS on `agyw-hiv-prep-review` and "
                "`cab-prep-hiv-review` -- two of the three topics asked under the EARLIER "
                "prompt build, the one whose reply ids are bare NCTs. Under that build it is "
                "4 of 6; under the later build 0 of 75. The 100% was measured on the later "
                "build's topics. The two-defaults mechanism stands; its universality does not, "
                "and what varies with it is the PROMPT."),
            "the_rate_is_still_conditional_on_the_same_allow_list": (
                "Both numbers are conditional on the fact list in "
                "THE_ALLOW_LIST_THE_RATE_IS_CONDITIONAL_ON above. Neither is a rate of "
                "agreement between assessors in general."),
        }
        obj.setdefault("display_change_announced", []).append({
            "date": TODAY,
            "change": "second-assessor disagreement rate recounted beside the stored one",
            "values_moved": ("NONE -- the stored rate and PER_DOMAIN are untouched. The "
                             "recount is written as a separate, labelled field."),
            "what_changed": "D1 %s -> %s; overall %s -> %s" % (
                stored_d1 or "(not recorded)", per_domain.get("D1", "(not compared)"),
                stored_rate.split("--")[0].strip() or "(not recorded)",
                "%d of %d" % (dis, cmp) if cmp else "(nothing comparable)"),
            "why": ("Applying the D1 guidance moved this review's judgements to the position "
                    "assessor 2 had taken, which left the stored rate describing a "
                    "disagreement the object no longer holds. Both numbers now appear."),
        })
        print("%-44s D1 %-16s -> %-16s   overall %s -> %d of %d"
              % (topic[:44], stored_d1 or "(none)", per_domain.get("D1", "(not compared)"),
                 stored_rate.split("--")[0].strip() or "(none)", dis, cmp))
        touched += 1
        if not dry:
            atomic_write.write_json(path, obj, indent=1)

    if not seen_blocks:
        sys.exit("PROOF FAILED: no topic in the corpus carries a SECOND_ASSESSOR block. 23 do. "
                 "The block lookup is broken, not the corpus.")
    if not seen_moved:
        sys.exit("PROOF FAILED: %d topic(s) carry a second-assessor block and NOT ONE reports a "
                 "moved D1. 51 judgements moved on 15 topics. The `resolved_%s` marker lookup "
                 "is broken, not the corpus." % (seen_blocks, TODAY.replace("-", "_")))
    print("\nfloor: %d topic(s) carry a second-assessor block, %d of them a moved D1 -- "
          "neither skip was universal" % (seen_blocks, seen_moved))
    print("%d topic(s) recounted, %d refused" % (touched, refused))
    if dry:
        print("DRY RUN -- pass --apply to write")


if __name__ == "__main__":
    main()
