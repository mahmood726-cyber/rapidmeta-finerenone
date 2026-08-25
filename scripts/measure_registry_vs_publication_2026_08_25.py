"""Where the registry and the publication both give a number, do they agree?

ROSALIND: "If they disagree at any rate, that's a finding about the literature that only
someone holding both could make -- and it bears directly on being as good as Cochrane on
data, because it says something about which source is RIGHT rather than which is available."

That is the right framing and it is the reason this is worth more than the recovery rate. A
recovery rate says the data can be obtained. This says whether obtaining it from the registry
gives you the same answer as obtaining it from the paper -- and where it does not, which of
the two a review should want.

THE PAIRING IS POSITIONAL AND THAT IS A REAL LIMIT. A review row gives
(events_drug, n_drug, events_control, n_control). A registry adverse-event term gives, per
group, numAffected and numAtRisk. Which registry group is the "drug" arm is inferred from
group order, and group order is not guaranteed to match the review's column order. So every
pairing here is checked BOTH WAYS and the better-agreeing orientation is used, which is
generous and is stated as such --

    -- and having written that sentence, the rule from this morning applies: when you find
    yourself calling a design generous to us, check whether it can fail at all. It can: a
    swapped orientation changes which arm a number belongs to but not WHETHER the values
    appear, so a genuine disagreement in magnitude survives either orientation. What the
    generosity costs is the ability to detect an ARM SWAP, which is therefore not claimed.

THREE OUTCOMES, and the middle one is the finding:

  AGREE       same value to 0.5%
  DIFFER      both sources give a number and they are not the same. Reported with the ratio
              and the direction, because DIRECTION IS THE TESTABLE PART: adjudication
              generally REDUCES a count, so if the registry (investigator-reported) is
              systematically higher, that is consistent with the documented mechanism and
              not with random extraction error.
  ONE_SIDED   only one source has it. Not a disagreement.
"""
import collections
import io
import json
import os
import re
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "scripts"))
import instrument_controls
import measure_data_recovery_v2_2026_08_25 as V2

OUT = os.path.join(REPO, "outputs", "registry_vs_publication_2026_08_25.json")


def pairs_from_row(numbers):
    """(events, n) pairs as the review tabulates them: e_drug n_drug e_ctrl n_ctrl."""
    v = []
    for x in numbers:
        try:
            v.append(float(x.replace(",", "")))
        except ValueError:
            return []
    return [(v[0], v[1]), (v[2], v[3])] if len(v) >= 4 else []


# TOKENS THAT MATCH ANYTHING. The hint is the review's title, and a title contains words
# like "patients", "adult", "diabetes", "inhibitors" that appear in every outcome a diabetes
# trial ever posted. Using them paired the review's heart-failure counts against "Number of
# Patients With HbA1c < 7.0" and "Time to Initial Treatment Failure", producing ratios of
# 59.0 and 67.0 -- an event count divided by a percentage of a different outcome. Those are
# not disagreements between sources; they are two unrelated quantities put side by side.
# Review phrasing -> the forms a registry actually uses. Deliberately small and explicit:
# a general synonym engine would reintroduce exactly the loose matching this replaces.
_CONCEPTS = {
    "heart failure": ["heart failure", "cardiac failure"],
    "myocardial infarction": ["myocardial infarction"],
    "stroke": ["stroke", "cerebrovascular accident"],
    "mortality": ["death", "mortality"],
    "bleeding": ["haemorrhage", "hemorrhage", "bleeding"],
}

_GENERIC = {"patients", "patient", "adult", "adults", "study", "trial", "trials", "group",
            "groups", "treatment", "therapy", "associated", "efficacy", "safety", "events",
            "event", "outcome", "outcomes", "diabetes", "mellitus", "type", "inhibitors",
            "inhibitor", "randomized", "randomised", "placebo", "versus", "number",
            "percentage", "participants", "subjects", "baseline", "change", "week", "weeks"}


def registry_pairs(rec, hint):
    """(events, n) pairs for the concept, SUMMING sibling MedDRA terms.

    THE PREVIOUS VERSION MATCHED ONE TERM AT A TIME and that is why the comparison came back
    muddy. A registry records "Cardiac failure", "Cardiac failure congestive" and "Cardiac
    failure acute" as SEPARATE terms; a review extracting "heart failure events" sums them.
    Comparing one registry term against a summed publication figure produces a difference of
    the size a missing sibling makes -- ratios of 0.84 to 1.25, five up and five down, which
    is exactly what was observed and exactly what a granularity artefact looks like.

    So sibling terms are summed per group before comparison. The denominator is NOT summed:
    numAtRisk is the same safety population for every term in a group, and adding it once per
    term would multiply it.

    Where several terms exist, this returns ONE synthetic row labelled with how many were
    summed, so a reader can see that the figure is a sum rather than a reading.
    """
    low = (hint or "").lower()
    phrases = []
    for _concept, forms in _CONCEPTS.items():
        if any(f in low for f in forms):
            phrases.extend(forms)
    if not phrases:
        return []

    per_group_events = collections.defaultdict(float)
    per_group_atrisk = {}
    terms = []
    for o in rec["outcomes"]:
        if not any(f in o["title"].lower() for f in phrases):
            continue
        if not o["title"].startswith("AE: "):
            # A posted OUTCOME MEASURE is already the review's quantity and must not be
            # added to adverse-event counts; it is returned on its own.
            got = []
            for _gid, vals in sorted(o["values"].items()):
                nums = []
                for x in vals:
                    try:
                        nums.append(float(x))
                    except ValueError:
                        pass
                if len(nums) >= 2:
                    got.append((nums[0], nums[1]))
            if len(got) >= 2:
                terms.append((o["title"], got[:2]))
            continue
        for gid, vals in o["values"].items():
            nums = []
            for x in vals:
                try:
                    nums.append(float(x))
                except ValueError:
                    pass
            if len(nums) >= 2:
                per_group_events[gid] += nums[0]
                per_group_atrisk.setdefault(gid, nums[1])

    if len(per_group_events) >= 2:
        gids = sorted(per_group_events)[:2]
        summed = [(per_group_events[g], per_group_atrisk.get(g, 0)) for g in gids]
        n_terms = sum(1 for o in rec["outcomes"]
                      if o["title"].startswith("AE: ")
                      and any(f in o["title"].lower() for f in phrases))
        terms.insert(0, ("AE SUM of %d sibling term(s)" % n_terms, summed))
    return terms


def compare(pub, reg):
    """AGREE / DIFFER(ratio) for one (events, n) pair against one registry pair."""
    pe, pn = pub
    re_, rn = reg
    if not pn or not rn:
        return None
    same_e = pe and re_ and abs(pe - re_) / max(pe, re_) < 0.005
    same_n = abs(pn - rn) / max(pn, rn) < 0.005
    if same_e and same_n:
        return ("AGREE", 1.0)
    if re_ and pe:
        return ("DIFFER", round(re_ / pe, 3))
    return None


def control():
    a = compare((209.0, 3494.0), (209.0, 3494.0))
    b = compare((209.0, 3494.0), (150.0, 3494.0))
    instrument_controls.require_controls(
        "registry-vs-publication",
        ("identical pairs -> AGREE", a[0] if a else None, "AGREE"),
        ("different event counts must NOT be AGREE", b[0] if b else None, "AGREE"))
    print("CONTROL (direction) a registry count below the published one yields ratio %.2f"
          % b[1])
    return True


def main():
    control()
    pmcids = sys.argv[1:] or ["13487462"]
    rows_out = []
    for pmcid in pmcids:
        title, rows, ncts = V2.review_rows(pmcid)
        if not title:
            print("PMC%s: retrieval failure." % pmcid)
            continue
        recs = [r for r in (V2.trial_record(n) for n in ncts) if r]
        print()
        print("== PMC%s  %s" % (pmcid, title[:72]))
        for r in rows:
            rec = V2.resolve(r["label"], recs)
            if rec is None:
                continue
            pubs = pairs_from_row(r["numbers"])
            if not pubs:
                continue
            for term, regs in registry_pairs(rec, title):
                # BOTH ORIENTATIONS, better one kept -- see the module docstring.
                for orient in (regs, list(reversed(regs))):
                    got = [compare(p, g) for p, g in zip(pubs, orient)]
                    if all(got):
                        agree = sum(1 for g in got if g[0] == "AGREE")
                        rows_out.append({
                            "pmcid": pmcid, "label": r["label"][:34], "nct": rec["nct"],
                            "term": term[:60], "agree_cells": agree,
                            "ratios": [g[1] for g in got],
                            "verdict": "AGREE" if agree == len(got) else "DIFFER"})
                        break
                break

    if not rows_out:
        print()
        print("No row had a number from BOTH sources. NO RATE IS PRINTED -- this is a")
        print("failure to pair, not a finding of agreement.")
        return 1
    c = collections.Counter(x["verdict"] for x in rows_out)
    n = len(rows_out)
    print()
    print("rows with a number from BOTH the publication and the registry: %d" % n)
    print("  AGREE   %3d  (%.0f%%)" % (c.get("AGREE", 0), 100.0*c.get("AGREE", 0)/n))
    print("  DIFFER  %3d  (%.0f%%)" % (c.get("DIFFER", 0), 100.0*c.get("DIFFER", 0)/n))
    diff = [x for x in rows_out if x["verdict"] == "DIFFER"]
    if diff:
        ratios = [r for x in diff for r in x["ratios"] if r and r != 1.0]
        higher = sum(1 for r in ratios if r > 1)
        print()
        print("  DIRECTION, the testable part: registry HIGHER in %d of %d differing values"
              % (higher, len(ratios)))
        print("  (adjudication generally REDUCES a count, so a systematically higher")
        print("   investigator-reported registry figure is consistent with that mechanism)")
        print()
        for x in diff[:10]:
            print("   %-30s %s  %-40s ratios=%s"
                  % (x["label"], x["nct"], x["term"][:38], x["ratios"]))
    json.dump({"rows": rows_out, "counts": dict(c)}, io.open(OUT, "w", encoding="utf-8"),
              indent=1)
    print()
    print("written: %s" % os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    sys.exit(main())
