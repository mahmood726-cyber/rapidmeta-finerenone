"""Writes the contrast/estimand gap onto the objects, in one pass. Corrects nothing.

TWO THINGS GO ON.

1. EVERY BLOCK CARRYING `estimand_established` GAINS A SENTENCE SAYING WHAT IT DOES NOT
   COVER. The flag certifies that the contributing trials measure the SAME QUANTITY. It
   says nothing about what that quantity was measured AGAINST. On `attr-pn-review` the flag
   is TRUE and CORRECT while the pool combines patisiran-against-saline,
   vutrisiran-against-PATISIRAN and eplontersen-against-a-different-trial's-placebo. The
   flag is NOT renamed: it is true, and a rename moves a reader between meanings without
   telling them.

2. EVERY TRIAL ROW WHOSE ARM ROLES THE OBJECT'S OWN OTHER FIELDS CONTRADICT GAINS A NOTE
   SAYING SO, AND NOTHING IS SWAPPED. Found by
   `scripts/lint_arm_roles_contradict_the_object.py`, which asks only what an object can
   answer about itself -- no registration required, because reading one per trial does not
   scale to a corpus:

     A  a TREATMENT arm labelled as a placebo (4 rows)
     B  a trial NAME naming a comparator its control arm does not carry (3 rows)
     C  both arms naming the same drug with no placebo anywhere (3 rows)

   WHY NOTHING IS SWAPPED. A role swap changes what the object says a trial DID. Where the
   arms carry event counts -- FOURIER does, 429/13780 against 378/13784 -- swapping them
   inverts any effect recomputed from them. That is a published-number decision. And
   `attr-pn` is the standing warning against inferring it: there the roles looked obvious
   from the drug names, and the registration turned out to say something sharper still,
   that the stored value was not the randomised contrast at all.

   ONE OF THE FLAGGED TOPICS IS CLOSED. `icosapent-lipid-auto-full-review` reached 4/4 on
   P46 tonight and BOTH of its trials record "Placebo" as the treatment arm and AMR101 as
   the control. THE STORED ESTIMATE IS UNAFFECTED -- those arms carry no counts, and the
   per-trial values are the published mean differences (-33.1 and -21.5), stored with the
   sign the publications report. The defect is in what the ARMS TABLE TELLS A READER, and
   it is recorded rather than quietly repaired.
"""
import io
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TODAY = "2026-08-20"
STAMP = TODAY.replace("-", "_")

GAP = ("READ THIS BESIDE `estimand_established`. That flag records that every contributing "
       "trial measures the SAME QUANTITY. It records NOTHING about what that quantity was "
       "measured AGAINST -- whether the comparators are of one kind, whether each "
       "comparison was randomised, whether it was concurrent. On attr-pn-review the flag "
       "is TRUE and correct while the pool combines patisiran against its own saline "
       "placebo, vutrisiran against PATISIRAN, and eplontersen against the placebo cohort "
       "of a DIFFERENT TRIAL. The two questions were never separated. Named as P48 in "
       "PAGE-STANDARD.md v1.21.0 and swept by scripts/audit_mixed_contrast_pools.py.")

# (topic, nct, class, what the object's own fields say)
ROWS = [
    ("evolocumab-dyslipidemia-review", "NCT01764633", "A",
     "FOURIER's TREATMENT arm is labelled 'Placebo' and its CONTROL arm 'Evolocumab'. A "
     "placebo is not an intervention, so the roles are inverted. THESE ARMS CARRY EVENT "
     "COUNTS -- 429/13780 on the row called treatment and 378/13784 on the row called "
     "control -- so anything recomputed from them inverts with the roles. Not swapped "
     "here: that is a published-number decision."),
    ("evolocumab-mixed-dyslipidemia-auto-full-review", "NCT03433755", "A",
     "HUA TUO's TREATMENT arm is labelled 'Placebo Q2W' and its CONTROL arm 'Evolocumab "
     "420 mg QM'. The roles are inverted. Its sibling row, BERSON, records atorvastatin as "
     "the treatment and 'Evolocumab QM + Atorvastatin' as the control, which puts this "
     "topic's own index drug in the comparator on BOTH rows. Not swapped here."),
    ("icosapent-lipid-auto-full-review", "NCT01047683", "A",
     "MARINE's TREATMENT arm is labelled 'Placebo' and its CONTROL arm 'AMR101 (ethyl "
     "icosapentate) - 4 g/day'. The roles are inverted in the ARMS TABLE. THE ESTIMATE IS "
     "NOT AFFECTED: these arms carry no counts, and the per-trial value is the published "
     "mean difference -33.1 (-45.65 to -20.55), stored with the sign the publication "
     "reports. THIS TOPIC IS AT 4/4 ON P46 AND THE DEFECT IS REPORTED RATHER THAN QUIETLY "
     "REPAIRED, because a reader opening the arms table is told the treatment was placebo."),
    ("icosapent-lipid-auto-full-review", "NCT01047501", "A",
     "ANCHOR's TREATMENT arm is labelled 'Placebo' and its CONTROL arm 'AMR101 (ethyl "
     "icosapentate) - 4 g/day'. Same defect as MARINE, same absence of counts, same "
     "unaffected published mean difference -21.5 (-26.75 to -16.25)."),
    ("hepatitis-b-taf-tdf-review", "NCT01940341", "B and C",
     "The row's own NAME is 'GS-US-320-0108 (TAF vs TDF, HBeAg-negative)' and its arms are "
     "'TAF 25 mg' against 'Open-label TAF'. TDF APPEARS NOWHERE. A comparison the object "
     "describes as TAF against TDF is recorded as TAF against TAF. The pool is already "
     "withdrawn; this is why it must stay withdrawn."),
    ("hepatitis-b-taf-tdf-review", "NCT01940471", "B and C",
     "The row's own NAME is 'GS-US-320-0110 (TAF vs TDF, HBeAg-positive)' and its arms are "
     "'TAF 25 mg' against 'Open-label TAF'. Same defect as its sibling."),
    ("netarsudil-ocular-hypertension-auto-full-review", "NCT02207621", "C",
     "ROCKET-2's arms are 'AR-13324 Ophthalmic Solution 0.02% & pla' against 'AR-13324 "
     "Ophthalmic Solution 0.02% BID'. BOTH ARMS ARE NETARSUDIL, so this row is a dose or "
     "schedule contrast sitting beside two netarsudil-against-timolol rows. The treatment "
     "label is also TRUNCATED MID-WORD at '& pla', which is a second defect on the same "
     "field. The pool is already withdrawn."),
    ("rosuvastatin-auto-full-review", "NCT00468923", "B",
     "The row's own NAME is 'HOPE-3 (rosuvastatin 10 mg vs placebo)' and its control arm "
     "is 'Candesartan/HCT'. HOPE-3 was 2x2 factorial and the arm recorded here is the "
     "ANTIHYPERTENSIVE factor, not the lipid one. This topic was already REFERRED on a "
     "separate finding -- it pools an estimand HOPE-3 does not hold -- and this is a "
     "second, independent defect on the same row."),
]


def load(topic):
    path = os.path.join(REPO, "ssot", topic, topic + ".json")
    if not os.path.exists(path):
        return None, None
    return path, json.load(io.open(path, encoding="utf-8"))


def save(path, obj):
    with io.open(path, "rb") as fh:
        head = fh.read(4096)
    nl = "\r\n" if b"\r\n" in head else "\n"
    with io.open(path, "w", encoding="utf-8", newline=nl) as fh:
        json.dump(obj, fh, indent=1, ensure_ascii=False)
        fh.write("\n")


def main():
    dry = "--apply" not in sys.argv
    touched = {}
    blocks = 0
    rows_written = 0

    # 1 -- the gap sentence, everywhere estimand_established appears.
    for topic in sorted(os.listdir(os.path.join(REPO, "ssot"))):
        path, obj = load(topic)
        if obj is None:
            continue
        hit = False
        for _name, blk in ((obj.get("results") or {}).get("by_outcome") or {}).items():
            if isinstance(blk, dict) and "estimand_established" in blk:
                key = "estimand_established_does_not_cover_the_contrast_%s" % STAMP
                if key not in blk:
                    blk[key] = GAP
                    blocks += 1
                    hit = True
        if hit:
            touched[topic] = (path, obj)

    # 2 -- the arm-role contradictions, on the rows they belong to.
    for topic, nct, cls, text in ROWS:
        if topic in touched:
            path, obj = touched[topic]
        else:
            path, obj = load(topic)
            if obj is None:
                sys.exit("REFUSED: %s is not on disk." % topic)
        found = False
        for t in (obj.get("inputs") or {}).get("trials") or []:
            if t.get("nct") != nct:
                continue
            found = True
            t["arm_roles_contradicted_by_this_object_%s" % STAMP] = {
                "class": cls,
                "detector": "scripts/lint_arm_roles_contradict_the_object.py",
                "finding": text,
                "NOT_CORRECTED": (
                    "The roles are NOT swapped. A swap changes what this object says the "
                    "trial did, and where arms carry counts it inverts anything recomputed "
                    "from them. Establishing a contrast is done from the registration, not "
                    "from what the drug names make obvious -- which is exactly what "
                    "attr-pn-review's NEURO-TTRansform row turned out to disprove."),
            }
            rows_written += 1
        if not found:
            sys.exit("REFUSED: %s is not on %s. Re-read before writing." % (nct, topic))
        touched[topic] = (path, obj)

    print("estimand/contrast gap written to %d outcome blocks" % blocks)
    print("arm-role contradictions written to %d trial rows across %d objects"
          % (rows_written, len(set(r[0] for r in ROWS))))
    print("objects touched: %d" % len(touched))
    if blocks == 0 or rows_written != len(ROWS):
        sys.exit("REFUSED: the pass did not reach what it was written to reach "
                 "(%d blocks, %d of %d rows)." % (blocks, rows_written, len(ROWS)))
    if dry:
        print("DRY RUN -- pass --apply to write")
        return
    for topic, (path, obj) in sorted(touched.items()):
        save(path, obj)
    print("wrote %d objects" % len(touched))


if __name__ == "__main__":
    main()
