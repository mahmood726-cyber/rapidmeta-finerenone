Mahmood Ahmad
Tahir Heart Institute
author@example.com

Protocol: Browser-Based Finerenone Meta-Analysis Validated Against R metafor

This protocol describes the planned evidence synthesis for Browser-Based Finerenone Meta-Analysis Validated Against R metafor, targeting transparent, reproducible estimation of HR in a versioned analytical workflow. Eligible studies include randomised controlled trials reporting the primary endpoint in the target clinical population, with no restrictions on publication year, language, geography, or sample size. Searches will cover PubMed and the ClinicalTrials.gov registry (AACT), using structured database strategies, registry-results screening, and duplicate review of linked publication abstracts before extraction. The primary analysis will estimate HR using frequentist random-effects meta-analysis (REML with the Hartung-Knapp-Sidik-Jonkman small-sample adjustment, and DerSimonian-Laird as a sensitivity estimator), reporting 95 percent confidence intervals validated for numerical agreement against R metafor. Heterogeneity will be summarised using I-squared and tau-squared, with prespecified sensitivity analyses across variance estimators, exclusion scenarios, and leave-one-out patterns. Analysis code will be versioned and archived at https://github.com/mahmood726-cyber/rapidmeta-finerenone, and reporting will follow PRISMA 2020 guidance to support independent verification and reuse. Anticipated limitations include publication bias, clinical heterogeneity, sparse data in some settings, and the constraints of aggregate-level evidence synthesis.

Outside Notes

Type: protocol
Primary estimand: HR
App: RapidMeta Cardiology v1.0
Code: https://github.com/mahmood726-cyber/rapidmeta-finerenone
Date: 2026-03-26
Validation: DRAFT

References

1. Viechtbauer W. Conducting meta-analyses in R with the metafor package. J Stat Softw. 2010;36(3):1-48.
2. Higgins JPT, Thompson SG, Spiegelhalter DJ. A re-evaluation of random-effects meta-analysis. J R Stat Soc Ser A. 2009;172(1):137-159.
3. Borenstein M, Hedges LV, Higgins JPT, Rothstein HR. Introduction to Meta-Analysis. 2nd ed. Wiley; 2021.

AI Disclosure

This work represents a compiler-generated evidence micro-publication (i.e., a structured, pipeline-based synthesis output). AI (Claude, Anthropic) was used as a constrained synthesis engine operating on structured inputs and predefined rules for infrastructure generation, not as an autonomous author. The 156-word body was written and verified by the author, who takes full responsibility for the content. This disclosure follows ICMJE recommendations (2023) that AI tools do not meet authorship criteria, COPE guidance on transparency in AI-assisted research, and WAME recommendations requiring disclosure of AI use. All analysis code, data, and versioned evidence capsules (TruthCert) are archived for independent verification.

