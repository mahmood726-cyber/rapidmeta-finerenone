"""ROUND 2 -- positive controls placed at each gate's OWN reading surface.

Round 1 planted defects where they naturally occur and measured what the suite catches. That
mixes two very different reasons for a miss: the class is not covered, or the instrument never
reached the case. Round 2 separates them. Each plant below is placed at the exact structural
site the named gate is documented to read, in a topic/outcome NOT in that gate's frozen
known-case list, so a gate that still passes is blind at its own chosen surface.

A gate that fails here and passed in round 1 is WORKING BUT NARROW. A gate that passes both is
not detecting the class at all.
"""

A = "append"

PLANTS = [
    dict(id="R01", cls="C1-swapped-trial-name", layer="store", gate="gate1",
         path="ssot/ceftaroline-auto-full-review/ceftaroline-auto-full-review.json",
         find='"trial_id": "NCT00509106",\n    "nct": "NCT00509106",\n    "label": "FOCUS 1"',
         replace='"trial_id": "NCT00509106",\n    "nct": "NCT00509106",\n    "label": "FOCUS 2"',
         what="a NEW label/registration swap between two PINNED trials, at gate 1's own site"),

    dict(id="R02", cls="C5-stale-judgement", layer="store", gate="gate4",
         path="ssot/ceftaroline-auto-full-review/ceftaroline-auto-full-review.json",
         find='"nct": "NCT00621504",\n    "label": "FOCUS 2",\n    "registry"',
         replace='"nct": "NCT00621504",\n    "label": "FOCUS 2",\n'
                 '    "planted_review": {"verdict": "low risk of bias", '
                 '"reason": "the allocation sequence was concealed"},\n    "registry"',
         what="a NEW judgement block carrying a verdict and no reference of any kind (kind D)"),

    dict(id="R03", cls="C8-page-denies-what-it-holds", layer="store", gate="gate3",
         path="ssot/sglt2-hf/sglt2-hf.json",
         find='"poolable_reason": "Both trials register this same three-component composite '
              'as their PRIMARY endpoint. One endpoint definition, one question."',
         replace='"poolable_reason": "Both trials register this same three-component composite '
                 'as their PRIMARY endpoint. One endpoint definition, one question.",\n'
                 '    "not_poolable_reason": "The two trials measure different quantities and '
                 'were never combined; nothing was pooled for this outcome."',
         what="two spellings of the reason holding two DIFFERENT substantive answers, at gate 3's site"),

    dict(id="R04", cls="C1-swapped-trial-name", layer="served", gate="gate6-C",
         path="SGLT2_CKD_REVIEW.html", mode=A,
         replace='<p>ASPIRE &mdash; https://clinicaltrials.gov/study/NCT01539226</p>',
         what="a PINNED registration labelled with the OTHER pinned trial, ONE occurrence on "
              "a page that holds no other, so the pairing cannot be ambiguous"),

    dict(id="R05", cls="C1-swapped-trial-name", layer="served", gate="gate6-C",
         path="ABATACEPT_RA_AUTO_FULL_REVIEW.html", mode=A,
         replace='<p>FOCUS 2 &mdash; https://clinicaltrials.gov/study/NCT00509106</p>',
         what="a second unambiguous served swap, different page, different pinned pair"),
]
