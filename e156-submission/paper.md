Mahmood Ahmad
Tahir Heart Institute
mahmood.ahmad2@nhs.net

Browser-Based Finerenone Meta-Analysis Validated Against R metafor

Can a standalone browser application reproduce R metafor results for finerenone cardiovascular and renal trials across multiple effect measures? We implemented RapidMeta as a single 7,800-line HTML file executing DerSimonian-Laird and REML random-effects meta-analysis entirely client-side, covering odds ratios, risk ratios, and hazard ratios with HKSJ adjustment, Bayesian analysis, and Trial Sequential Analysis. All data were extracted from open-access sources including ClinicalTrials.gov, PubMed abstracts, and FDA documents for three Phase III trials enrolling 19,112 patients across FIDELIO-DKD, FIGARO-DKD, and FINEARTS-HF. Across 14 analyses spanning five outcomes, the application matched metafor to six decimal places for all estimates including MACE HR 0.87 (95% CI 0.79-0.95) and all-cause mortality HR 0.91 (95% CI 0.84-0.99). Concordance testing against 17 published meta-analyses showed 88 percent within 0.03 absolute difference. Browser-native JavaScript achieves reference-grade numerical accuracy for clinical meta-analysis without server infrastructure. The limitation of three-trial pooling means heterogeneity assessment has low power and results may shift as additional trials report.

Outside Notes

Type: pairwise
Primary estimand: HR
App: RapidMeta Cardiology v1.0
Data: FIDELIO-DKD, FIGARO-DKD, FINEARTS-HF (N=19,112), OA sources only
Code: https://github.com/mahmood726-cyber/rapidmeta-finerenone
Version: 1.0
Validation: DRAFT

References

1. Roever C. Bayesian random-effects meta-analysis using the bayesmeta R package. J Stat Softw. 2020;93(6):1-51.
2. Higgins JPT, Thompson SG, Spiegelhalter DJ. A re-evaluation of random-effects meta-analysis. J R Stat Soc Ser A. 2009;172(1):137-159.
3. Borenstein M, Hedges LV, Higgins JPT, Rothstein HR. Introduction to Meta-Analysis. 2nd ed. Wiley; 2021.
