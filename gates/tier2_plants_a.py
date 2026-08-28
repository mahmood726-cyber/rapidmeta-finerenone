"""The plant registry: known errors, one per entry, drawn from classes this corpus actually has.

EVERY PLANT IS AN EXACT SUBSTITUTION OR AN APPEND. Not a regex, not a fuzzy anchor. The
harness refuses to apply a plant whose `find` does not occur EXACTLY ONCE in the target, and
refuses to report a miss for a plant it could not apply. A plant that silently fails to apply
would be recorded as "nothing detected it" -- a FALSE ZERO, which is the single failure mode
this whole exercise exists to avoid.

MODES
    find/replace   exact unique substitution
    append         `replace` is appended at end of file (served pages here end mid-markup,
                   with no </body> to anchor against -- itself a fact about these bytes)

LAYER is recorded per plant because a defect planted in one layer is invisible to an
instrument reading another, and that is itself a finding rather than a miss.
    store   ssot/<topic>/<topic>.json      -- the object a page is built from
    served  <PAGE>.html at the repo root   -- the bytes a reader receives
"""

A = "append"

PLANTS = [

    # ---------------------------------------------------------------- C1
    # A swapped trial name where the registration stays correct.
    dict(id="P01", cls="C1-swapped-trial-name", layer="store",
         path="ssot/agyw-hiv-prep-review/agyw-hiv-prep-review.json",
         find='ASPIRE / MTN-020 1959 v 1952; The Ring Study 2629 v 2626',
         replace='The Ring Study 1959 v 1952; ASPIRE / MTN-020 2629 v 2626',
         what="the two PINNED trials' names exchanged; both registrations untouched"),
    dict(id="P02", cls="C1-swapped-trial-name", layer="served",
         path="CEFTAROLINE_AUTO_FULL_REVIEW.html", mode=A,
         replace='<p>FOCUS 2 (NCT00509106) enrolled 613 participants with '
                 'community-acquired pneumonia.</p>',
         what="PINNED NCT00509106 (FOCUS 1) labelled FOCUS 2 in served prose"),
    dict(id="P03", cls="C1-swapped-trial-name", layer="store",
         path="ssot/sglt2-hf/sglt2-hf.json",
         find='"trial_id": "dapa-hf"', replace='"trial_id": "deliver"',
         what="DAPA-HF row relabelled DELIVER, its NCT03036124 left correct (NOT a pinned trial)"),
    dict(id="P04", cls="C1-swapped-trial-name", layer="served",
         path="SGLT2_HF_REVIEW.html", mode=A,
         replace='<p>EMPEROR-Preserved (NCT03057977) randomised patients with an ejection '
                 'fraction of 40% or less.</p>',
         what="NCT03057977 (EMPEROR-Reduced) labelled EMPEROR-Preserved (NOT a pinned trial)"),

    # ---------------------------------------------------------------- C2
    # A numerator and a denominator drawn from different analysis populations.
    dict(id="P05", cls="C2-mixed-analysis-population", layer="store",
         path="ssot/sglt2-hf/sglt2-hf.json",
         find="each trial's own full analysis set, which on all four equals its randomised total",
         replace="events counted on the full analysis set over a per-protocol denominator",
         what="estimand declares numerator and denominator from two different populations"),
    dict(id="P06", cls="C2-mixed-analysis-population", layer="store",
         path="ssot/iv-iron-hf/iv-iron-hf.json",
         find='\n    "population": "adults hospitalised for acute heart failure with '
              'concomitant iron deficiency and a left ventricular ejection fraction below '
              '50%, randomised before hospital discharge"',
         replace='\n    "population": "events from the intention-to-treat set expressed over '
                 'the per-protocol randomised denominator"',
         what="a per-trial row states a numerator population and a different denominator population"),
    dict(id="P07", cls="C2-mixed-analysis-population", layer="served",
         path="MALARIA_VACCINES_REVIEW.html", mode=A,
         replace='<p>Cases were counted in the modified intention-to-treat population and '
                 'divided by the per-protocol denominator.</p>',
         what="served prose states a numerator and denominator from different populations"),

    # ---------------------------------------------------------------- C3
    # An interim result row substituted for a complete one.
    dict(id="P08", cls="C3-interim-substituted-for-complete", layer="store",
         path="ssot/sglt2-hf/sglt2-hf.json",
         find='"composite_as_this_trial_defines_it": "cardiovascular death, hospitalization '
              'for heart failure, or an urgent heart failure visit resulting in intravenous '
              'therapy",\n      "derivation": "the published hazard ratio',
         replace='"composite_as_this_trial_defines_it": "cardiovascular death, hospitalization '
                 'for heart failure, or an urgent heart failure visit resulting in intravenous '
                 'therapy",\n      "derivation": "the SECOND PRE-SPECIFIED INTERIM ANALYSIS '
                 'hazard ratio, database not locked, read as the published hazard ratio',
         what="an interim-analysis estimate stored in the row that claims the complete result"),
    dict(id="P09", cls="C3-interim-substituted-for-complete", layer="served",
         path="SOTAGLIFLOZIN_HF_AUTO_FULL_REVIEW.html", mode=A,
         replace='<p>The hazard ratio below is taken from the second interim analysis; the '
                 'final database lock is not yet reported.</p>',
         what="served page presents an interim cut under a complete-result heading"),

    # ---------------------------------------------------------------- C4
    # A narrative interval that differs from the page's declared method.
    dict(id="P10", cls="C4-narrative-interval-vs-method", layer="served",
         path="IV_IRON_HF_REVIEW.html", mode=A,
         replace='<p>Pooling is declared as random-effects with the Hartung-Knapp adjustment. '
                 'The summary risk ratio was 0.79 (95% CI 0.71 to 0.88), computed on '
                 'fixed-effect inverse-variance weights.</p>',
         what="the narrative interval is computed by a method the page does not declare"),
    dict(id="P11", cls="C4-narrative-interval-vs-method", layer="served",
         path="MALARIA_VACCINE_REVIEW.html", mode=A,
         replace='<p>The prediction interval (0.41 to 0.95) uses the normal quantile, although '
                 'the declared analysis is Hartung-Knapp with a t distribution on k-1 degrees '
                 'of freedom.</p>',
         what="declared method is HKSJ/t but the quoted interval is z-based"),

    # ---------------------------------------------------------------- C5
    # A stale judgement whose subject has moved.
    dict(id="P12", cls="C5-stale-judgement", layer="store",
         path="ssot/tigecycline-ciai/tigecycline-ciai.json",
         find='"i2": 58.7606\n       },\n       "verdict": "the interval now includes the null"',
         replace='"i2": 58.7606\n       },\n       "verdict": "the interval excludes the null"',
         what="a stored verdict now contradicts the numbers in its own block; timestamp untouched"),
    dict(id="P13", cls="C5-stale-judgement", layer="store",
         path="ssot/ablation-af-heart-failure/ablation-af-heart-failure.json",
         find='"state": "undecidable",\n    "why": "no arm name matches the pattern, and arm '
              'names are paraphrases -- this method cannot decide identity for this trial"\n'
              '   },\n   "NCT01420393"',
         replace='"state": "studied",\n    "why": "the registered experimental arm names this '
                 'intervention"\n   },\n   "NCT01420393"',
         what="an identity judgement flipped to a positive verdict its own method cannot reach"),
    dict(id="P14", cls="C5-stale-judgement", layer="store",
         path="ssot/sglt2-hf/sglt2-hf.json",
         find='"checked_utc"', replace='"checked_utc_UNSET"',
         what="a judgement loses the only field stating when it was made"),

    # ---------------------------------------------------------------- C6
    # A role inversion on a trial's arms.
    dict(id="P15", cls="C6-arm-role-inversion", layer="store",
         path="ssot/sglt2-hf/sglt2-hf.json",
         find='"comparator": "placebo added to background heart failure therapy"',
         replace='"comparator": "dapagliflozin added to background heart failure therapy"',
         what="the comparator arm is named as the intervention; every effect direction inverts"),
    dict(id="P16", cls="C6-arm-role-inversion", layer="store",
         path="ssot/sglt2-hf/sglt2-hf.json",
         find='"direction_of_benefit": "lower"', replace='"direction_of_benefit": "higher"',
         what="benefit direction inverted while the stored point estimate stays below 1"),
    dict(id="P17", cls="C6-arm-role-inversion", layer="served",
         path="TIGECYCLINE_CIAI_SSOT.html", mode=A,
         replace='<p>Participants randomised to the comparator arm received tigecycline; the '
                 'tigecycline arm served as the control.</p>',
         what="served prose states the intervention arm was the control"),

    # ---------------------------------------------------------------- C7
    # A truncated hash presented as a full one.
    dict(id="P18", cls="C7-truncated-hash-as-full", layer="served",
         path="LENACAPAVIR_PREP_REVIEW.html", mode=A,
         replace='<p>Built from store object with full SHA-256 digest 4f2a9c1b8e07.</p>',
         what="a 12-hex-character value labelled a full SHA-256 digest"),
    dict(id="P19", cls="C7-truncated-hash-as-full", layer="store",
         path="ssot/malaria-vaccines/malaria-vaccines.json",
         find='"app_id": "malaria-vaccines"',
         replace='"app_id": "malaria-vaccines",\n "source_sha256_full": "9c1b8e07"',
         what="a field naming itself a full sha256 carries eight hex characters"),

    # ---------------------------------------------------------------- C8
    # A page denying something it holds.
    dict(id="P20", cls="C8-page-denies-what-it-holds", layer="served",
         path="ANTIMALARIAL_ACT_SSOT.html", mode=A,
         replace='<p>No confidence interval is reported anywhere on this page. The pooled '
                 'risk ratio was 0.62 (95% CI 0.48 to 0.80).</p>',
         what="the page denies holding an interval one clause before printing one"),
    dict(id="P21", cls="C8-page-denies-what-it-holds", layer="served",
         path="MALARIA_ACT_REVIEW.html", mode=A,
         replace='<p>This review contains no GRADE certainty assessment. Certainty of '
                 'evidence: MODERATE, downgraded once for inconsistency.</p>',
         what="the page denies a GRADE assessment it then prints"),

    # ---------------------------------------------------------------- C9
    # A page asserting something it lacks.
    dict(id="P22", cls="C9-page-asserts-what-it-lacks", layer="served",
         path="LENACAPAVIR_HIV_AUTO_FULL_REVIEW.html", mode=A,
         replace='<p>A full risk-of-bias assessment for every contributing trial is presented '
                 'in the table below.</p>',
         what="asserts a RoB table that is not on the page"),
    dict(id="P23", cls="C9-page-asserts-what-it-lacks", layer="served",
         path="SGLT2_CKD_REVIEW.html", mode=A,
         replace='<p>Individual participant data were obtained for all contributing trials and '
                 'are reconstructed in the survival figure below.</p>',
         what="asserts IPD reconstruction the page does not contain"),

    # ---------------------------------------------------------------- C10
    # A falsy value reaching the reader.
    dict(id="P24", cls="C10-falsy-value-served", layer="served",
         path="MALARIA_VACCINES_SSOT.html", mode=A,
         replace='<p>Pooled efficacy: None (95% CI None to None) across None trials.</p>',
         what="Python None rendered into reader-facing prose"),
    dict(id="P25", cls="C10-falsy-value-served", layer="served",
         path="SGLT2I_HF_NMA_REVIEW.html", mode=A,
         replace='<p>Participants analysed: undefined. Heterogeneity: NaN%.</p>',
         what="JavaScript undefined and NaN rendered into reader-facing prose"),
    dict(id="P26", cls="C10-falsy-value-served", layer="store",
         path="ssot/antimalarial-act/antimalarial-act.json",
         find='"title": "Artemisinin-based combination therapies against '
              'artemether-lumefantrine',
         replace='"title": "None -- Artemisinin-based combination therapies against '
                 'artemether-lumefantrine',
         what="a falsy token welded into the title a projector renders as a heading"),

    # ---------------------------------------------------------------- C11
    # A citation attached to a trial it does not report.
    dict(id="P27", cls="C11-citation-wrong-trial", layer="store",
         path="ssot/sglt2-hf/sglt2-hf.json",
         find='"pmid": "31535829"', replace='"pmid": "33200892"',
         what="the DAPA-HF source row cites the EMPEROR-Reduced paper instead"),
    dict(id="P28", cls="C11-citation-wrong-trial", layer="served",
         path="CEFTAROLINE_AUTO_REVIEW.html", mode=A,
         replace='<p>FOCUS 1 (NCT00509106) is reported in File et al., Clin Infect Dis '
                 '2010;51:1395, which is the FOCUS 2 report.</p>',
         what="a citation attached in prose to a trial the cited paper does not report"),
]
