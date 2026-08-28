"""ROUND 3 -- the seven classes added to the brief, planted where they naturally occur.

Same contract as round 1: exact unique substitution or EOF append, refused if the anchor is
not present exactly once, so no plant can become a silent zero.
"""

A = "append"

PLANTS = [
    # ------------------------------------------------ A3
    dict(id="T01", cls="A3-result-under-trials-that-did-not-produce-it", layer="store",
         path="ssot/sglt2-hf/sglt2-hf.json",
         find='"trial_id": "NCT03036124",\n      "nct": "NCT03036124",\n      "measure": "HR",\n'
              '      "point": 0.74,\n      "ci_low": 0.65,\n      "ci_high": 0.85,\n'
              '      "ci_level": 95,\n      "rank_used": "PRIMARY"',
         replace='"trial_id": "NCT02397096",\n      "nct": "NCT02397096",\n      "measure": "HR",\n'
                 '      "point": 0.74,\n      "ci_low": 0.65,\n      "ci_high": 0.85,\n'
                 '      "ci_level": 95,\n      "rank_used": "PRIMARY"',
         what="a pooled row attributed to a trial that is not among this topic's sources and "
              "never reported this outcome"),
    dict(id="T02", cls="A3-result-under-trials-that-did-not-produce-it", layer="served",
         path="SOTAGLIFLOZIN_HF_AUTO_FULL_REVIEW.html", mode=A,
         replace='<p>Contributing trials for this pooled estimate: SOLOIST-WHF, SCORED and '
                 'DAPA-HF (NCT03036124).</p>',
         what="the served page names a contributing trial that produced no row in this pool"),

    # ------------------------------------------------ Q4
    dict(id="T03", cls="Q4-pooled-k-disagrees-with-title", layer="store",
         path="ssot/sglt2-hf/sglt2-hf.json",
         find='"k": 2,\n    "estimand_id": "threecomp_cvdeath_hhf_urgent",',
         replace='"k": 5,\n    "estimand_id": "threecomp_cvdeath_hhf_urgent",',
         what="a second k on the pool disagreeing with the two rows behind it"),
    dict(id="T04", cls="Q4-pooled-k-disagrees-with-title", layer="served",
         path="SGLT2_HF_REVIEW.html", mode=A,
         replace='<p>Pooled across three randomised trials (k = 4).</p>',
         what="the served prose states a trial count that disagrees with the k beside it"),

    # ------------------------------------------------ AS3
    dict(id="T05", cls="AS3-page-accuses-itself-falsely", layer="served",
         path="MALARIA_ACT_REVIEW.html", mode=A,
         replace='<p>Note: this page reports a withdrawn pooled estimate as though it were '
                 'live, and its certainty rating was never adjudicated.</p>',
         what="the page accuses itself of two defects it does not have"),
    dict(id="T06", cls="AS3-page-accuses-itself-falsely", layer="store",
         path="ssot/tigecycline-ciai/tigecycline-ciai.json",
         find='"app_id": "tigecycline-ciai"',
         replace='"app_id": "tigecycline-ciai",\n "self_report": "This object stores a pooled '
                 'estimate that was withdrawn and never removed."',
         what="the object records a defect about itself that is not true of it"),

    # ------------------------------------------------ S1
    dict(id="T07", cls="S1-outcome-with-no-rows-behind-it", layer="store",
         path="ssot/sotagliflozin-hf/sotagliflozin-hf.json",
         find='\n    "estimand_id": "mace3_first-estimand",',
         replace='\n    "estimand_id": "mace3_first-estimand",\n    "per_trial": [],',
         what="an outcome published with k and a pooled estimate and no rows behind it"),

    # ------------------------------------------------ S2
    dict(id="T08", cls="S2-certainty-over-unadjudicated-assessment", layer="store",
         path="ssot/sglt2-hf/sglt2-hf.json",
         find='"certainty": "high",\n     "certainty_derivation": "start high; no downgrades; '
              'total -0 -> high"',
         replace='"certainty": "high",\n     "certainty_derivation": "no risk-of-bias '
                 'assessment has been adjudicated for this outcome"',
         what="a certainty rating asserted over an assessment that was never adjudicated"),

    # ------------------------------------------------ S3
    dict(id="T09", cls="S3-noninferiority-pooled-as-superiority", layer="store",
         path="ssot/sglt2-hf/sglt2-hf.json",
         find='"trial_id": "emperor-preserved"',
         replace='"trial_id": "NCT00509106"',
         what="a registered NON-INFERIORITY trial (per out/blind-review/noninferiority_trials"
              ".json) placed in a superiority pool"),
    dict(id="T10", cls="S3-noninferiority-pooled-as-superiority", layer="served",
         path="TIGECYCLINE_CIAI_SSOT.html", mode=A,
         replace='<p>All contributing trials were designed to test superiority, and the pooled '
                 'estimate is interpreted as a superiority result.</p>',
         what="a superiority reading asserted over a corpus whose trials are non-inferiority"),

    # ------------------------------------------------ S4
    dict(id="T11", cls="S4-partial-repair-one-copy-fixed", layer="store",
         path="ssot/sglt2-hf/sglt2-hf.json",
         find='\n       "point": 0.7835,', replace='\n       "point": 0.6120,',
         what="the pooled point repaired in the store while every other copy of it stays"),
    dict(id="T12", cls="S4-partial-repair-one-copy-fixed", layer="served",
         path="IV_IRON_HF_REVIEW.html", mode=A,
         replace='<p>Corrected pooled risk ratio: 0.83 (95% CI 0.72 to 0.96). The summary '
                 'table above and the abstract still carry the superseded 0.79.</p>',
         what="one copy of a number repaired on the page and the other copies left"),
]
