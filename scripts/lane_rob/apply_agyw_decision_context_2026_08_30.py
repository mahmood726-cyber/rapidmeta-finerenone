# -*- coding: utf-8 -*-
"""The four facts a clinical reading needs that the object did not hold — each read at source.

⛔ THIS IS THE HONEST-GUARD PATH, NOT THE PARITY-PRESSURE PATH. The target is a generated
clinical reading EQUAL to the hand-written one. Three of the hand version's claims cannot be
derived from the object as it stood:

    "roughly 18 months"            -- no follow-up duration is stored in a comparable form
    "Condoms, STI screening and    -- no record that the trials delivered a background
     partner services remain          prevention package alongside the ring
     necessary"
    "limited by adherence inside   -- no record of the adherence measurement or the visit
     a trial with monthly contact"    schedule

⚠️ THE WRONG FIX IS TO WRITE THOSE SENTENCES INTO THE GENERATOR. That is prose asserting more
than the store holds, which is the failure this project keeps finding. The right fix is to READ
THEM AT SOURCE and store them as typed fields with the sentence they came from -- after which
the generator DERIVES the claim and a reader can check it.

Every value below is read from ASPIRE's primary report, PMC4993693, retrieved 2026-08-30 by
ncbi_efetch, 44,179 rendered characters,
sha256 a6c75ad7e331aff7ff37a7792efa39d3631550600aeebe8c1b219457c4a03752.

⭐ AND ONE OF THEM MAKES THE GENERATED CLAIM STRONGER THAN THE HAND-WRITTEN ONE. The hand page
says condoms and STI services "remain necessary", which is a care recommendation this review has
no standing to make. The report says every participant RECEIVED that package -- so the honest
and more useful claim is that the estimate is an effect measured ON TOP OF it, and does not
describe the ring used instead of those things. That is a property of the evidence rather than
advice, and it is checkable.
"""
import io
import json
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                              line_buffering=True)

OBJ = os.path.join("ssot", "agyw-hiv-prep-review", "agyw-hiv-prep-review.json")

SRC = {
    "document_id": "PMC4993693",
    "what": "ASPIRE / MTN-020 primary report",
    "route": "ncbi_efetch (Europe PMC returned 503)",
    "retrieved_utc": "2026-08-30",
    "tier": "trial report",
    "sha256": "a6c75ad7e331aff7ff37a7792efa39d3631550600aeebe8c1b219457c4a03752",
    "scope": "⚠️ ASPIRE ONLY. The Ring Study's report is not held (PMID 27959766, no PMC id, "
             "europepmc_by_pmid 404), so none of these values is claimed for both trials.",
}

FOLLOWUP = {
    "median": 1.6,
    "unit": "years",
    "iqr": "1.1 to 2.3",
    "maximum": 2.6,
    "person_years": 4280,
    "source": SRC,
    "source_quote": "The median follow-up was 1.6 years (interquartile range, 1.1 to 2.3), and "
                    "the maximum follow-up was 2.6 years; 1024 women contributed more than 2 "
                    "years of follow-up.",
    "basis": "⛔ THIS IS ASPIRE'S MEDIAN, NOT A POOLED FOLLOW-UP, and the number needed to "
             "treat derived beside it is over BOTH trials. It is reported as the horizon the "
             "larger trial observed rather than as the review's own, because the object holds "
             "no pooled follow-up and inventing one would attach a false precision to the "
             "figure a clinician remembers.",
}

BACKGROUND_CARE = {
    "delivered_to": "every participant in both arms",
    "what": "counselling on HIV-1 risk reduction, partner HIV-1 testing, treatment of sexually "
            "transmitted infections in participants and partners, and free condoms",
    "source": SRC,
    "source_quote": "All participants received a package of HIV-1 prevention services, "
                    "including counseling with respect to HIV-1 risk reduction, partner HIV-1 "
                    "testing, treatment of sexually transmitted infections in participants and "
                    "partners, and free condoms.",
    "what_it_means_for_the_estimate":
        "The effect is measured ON TOP OF this package, delivered to both arms. It therefore "
        "describes the ring ADDED to that care and says nothing about the ring used INSTEAD of "
        "it. ⭐ Stated as a property of the evidence rather than as advice: this review has no "
        "standing to recommend a package of care, and it does have standing to say what its own "
        "estimate is conditional on.",
}

ADHERENCE = {
    "measured": True,
    "how": "dapivirine detection in plasma, residual drug in returned rings, and the composite "
           "of those two measures",
    "rate_over_21": "more than 70% overall",
    "contact_schedule": "monthly follow-up visits including HIV-1 serologic testing, safety "
                        "monitoring and individualised adherence counselling",
    "source": SRC,
    "source_quote": "For women who were older than 21 years of age, the efficacy of HIV-1 "
                    "protection was 56% (95% CI, 31 to 71; P<0.001), and the rate of adherence "
                    "was more than 70% overall, as defined by dapivirine detection in plasma, "
                    "in returned rings, and in the composite of those two measures.",
    "schedule_quote": "Women returned for monthly follow-up visits, which included HIV-1 "
                      "serologic testing, safety monitoring, and individualized adherence "
                      "counseling.",
    "what_it_means_for_the_estimate":
        "Adherence was OBSERVED, not assumed, and it was observed under monthly contact. A "
        "service that does not reproduce monthly contact should expect lower adherence and "
        "therefore a smaller effect than this one: the estimate is an efficacy under trial "
        "conditions, not an effectiveness in use.",
}


def apply(path=OBJ, dry=False):
    c = json.load(io.open(path, encoding="utf-8"))
    prim = ((c.get("results") or {}).get("by_outcome") or {}).get("primary")
    if not isinstance(prim, dict):
        raise SystemExit("REFUSED: no primary outcome block in %s" % path)
    changed = []
    for key, val in (("followup", FOLLOWUP),
                     ("background_care", BACKGROUND_CARE),
                     ("adherence", ADHERENCE)):
        if key not in prim:
            prim[key] = val
            changed.append(key)
    print("")
    print("APPLY -- %s" % path)
    for ch in changed:
        print("   + %s" % ch)
    if not changed:
        print("   (nothing to do; this script is idempotent)")
        return 0
    if dry:
        print("   --dry: not written")
        return 0
    tmp = path + ".tmp"
    with io.open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(c, fh, indent=1, ensure_ascii=False)
    size = os.path.getsize(tmp)
    if size < 10000:
        os.remove(tmp)
        raise SystemExit("REFUSED: the rewritten object is %d bytes. Nothing was replaced."
                         % size)
    json.load(io.open(tmp, encoding="utf-8"))
    os.replace(tmp, path)
    print("   written, %d bytes, reparsed OK" % size)
    return 0


if __name__ == "__main__":
    raise SystemExit(apply(dry="--dry" in sys.argv))
