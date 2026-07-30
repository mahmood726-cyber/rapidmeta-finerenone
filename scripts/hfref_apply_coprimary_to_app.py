#!/usr/bin/env python
"""Apply the SYMMETRIC quarantine and the CO-PRIMARY presentation to the app.

Supersedes scripts/hfref_apply_quarantine_to_app.py, which wrote a single
CARMEN-removed fit as though it were the primary. Two corrections:

  1. The quarantine rule -- unverified per-arm all-cause deaths AND identical
     across-arm counts -- is applied to every trial that meets it, not one.
     It is also RELEASED from every trial that stops meeting it: the rule is a
     conjunction, so verifying the counts clears a trial even when they stay
     identical. Currently quarantined: CARMEN, Vizzardi 2014. Reinstated:
     GALACTIC-HF, on per-arm all-cause deaths read from the ClinicalTrials.gov
     NCT02929329 posted results (see scripts/hfref_recover_galactic_allcause.py)
     -- which also RESTORES the +Omecamtiv node that its quarantine had deleted.

  2. BOTH fits are carried and BOTH are displayed. The FULL network is the
     conservative co-primary; the quarantined network is a provenance
     sensitivity. The reader sees both or the app is lying by omission.

Reads outputs/hfref_coprimary_fit.json (the anchor-gated R re-fit) and rewrites:

  1. script#hfref-fit-data       -- cells carry FULL as the primary league plus
     a parallel `coprimary_quarantined` pack; nma_config carries both edge sets.
  2. window.__verdict            -- machine-readable badge payload.
  3. #rapidmeta-integrity-badge  -- human-readable badge prose.
  4. the headline renderer       -- side-by-side co-primary hero cards, the
     honest direction flag AT THE POINT OF DISPLAY, and a both-columns table.

Both verdict surfaces are written from the SAME derived facts here so they
cannot drift. scripts/hfref_verify_app_coprimary.py re-checks that.

Never edits F:/E156/hfref_eightcell_fit.R.
"""
import io
import json
import re
import subprocess
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

APP = "HFREF_NMA_AUTO_FULL_REVIEW.html"
FIT = "outputs/hfref_coprimary_fit.json"
DATE = "2026-07-30"
# the last commit whose payload still carried the FULL 16-edge nma_config
PRE_QUARANTINE_REV = "2e9347f95"

PAYLOAD_RE = (r'(<script id="hfref-fit-data" type="application/json">)'
              r'(.*?)(</script>)')

QUAR = {
    "HF-021": dict(
        trial="CARMEN",
        violation=("unverified per-arm all-cause deaths (14/14/14) identical "
                   "across all three arms; primary endpoint is LVESVI and the "
                   "source reports no deaths"),
        source="PMID 15115904 (Cardiovasc Drugs Ther 2004;18:57-66)",
        rows=[{"treat": "ACEI", "events": 14, "n": 190},
              {"treat": "ACEI+BB", "events": 14, "n": 191},
              {"treat": "BB", "events": 14, "n": 191}],
        reinstatement=("Locate a primary or CARMEN-authored secondary report "
                       "stating per-arm all-cause deaths."),
        cost="Removes the ACEI+BB vs BB edge and the network's only multi-arm trial."),
    "HF-025": dict(
        trial="Vizzardi 2014",
        violation=("unverified per-arm all-cause deaths (8/8) identical across "
                   "both arms; the source reports only composite event-free "
                   "survival"),
        source="PMID 24196866 (Am J Med Sci 2014;347:271-6)",
        rows=[{"treat": "ACEI+BB", "events": 8, "n": 65},
              {"treat": "ACEI+BB+MRA", "events": 8, "n": 65}],
        reinstatement=("Read the Am J Med Sci full text for per-arm all-cause "
                       "deaths. The trial was never registered, so there is no "
                       "registry route."),
        cost=("No node lost; the direct ACEI+BB vs ACEI+BB+MRA leg loses a "
              "contributing trial.")),
}
QNAMES = {v["trial"] for v in QUAR.values()}

# Quarantined 2026-07-30 and REINSTATED the same day, on the registry route the
# quarantine pass had recorded as unexhausted. Kept as an explicit structure --
# not simply deleted from QUAR -- so the app can show the round trip rather than
# quietly presenting the trial as though it had never been withheld.
REINST = {
    "HF-034": dict(
        trial="GALACTIC-HF",
        cleared=("The quarantine rule requires per-arm all-cause deaths to be "
                 "UNVERIFIED **and** identical across arms. The counts are still "
                 "identical (1078/1078); they are no longer unverified."),
        count_source=("ClinicalTrials.gov NCT02929329 posted results, "
                      "adverse-events module (the FDAAA 'All-Cause Mortality' "
                      "table), retrieved 2026-07-30 via CT.gov API v2"),
        rows=[{"treat": "ACEI+BB+MRA", "events": 1078, "n": 4112},
              {"treat": "+Omecamtiv", "events": 1078, "n": 4120}],
        restores="+Omecamtiv (GALACTIC-HF is that node's only trial)"),
}
RNAMES = {v["trial"] for v in REINST.values()}

fit = json.load(open(FIT, encoding="utf-8"))
if not fit["anchor"]["full"]["reproduced"]:
    sys.exit("FAIL: full-network anchor did not reproduce; refusing to touch the app")

full_by_cell = {c["cell_id"]: c["full"] for c in fit["app_cells"]}
quar_by_cell = {c["cell_id"]: c["quarantined"] for c in fit["app_cells"]}
FU, QU = fit["full"], fit["quarantined"]
DD = fit["presentation"]["direction_detail"]

html = open(APP, encoding="utf-8").read()
orig_len = len(html)

m = re.search(PAYLOAD_RE, html, re.S)
if not m:
    sys.exit("FAIL: script#hfref-fit-data not found")
P = json.loads(m.group(2))


def node(pack, name):
    for n in pack["node_vs_placebo"]:
        if n["node"] == name:
            return n
    return None


def f3(x):
    return "%.3f" % x


# ---------------------------------------------------------------- cells -----
for cell in P["cells"]:
    cid = cell["cell_id"]
    if cid not in full_by_cell:
        continue
    a, b = full_by_cell[cid], quar_by_cell[cid]
    # the FULL network is the conservative co-primary and the app's default
    cell["trials"] = a["trials"]
    cell["arm_rows"] = a["arm_rows"]
    cell["contrasts_in_data"] = a["contrasts"]
    cell["nodes_in_network"] = a["structure"]["V"]
    cell["estimable_pairs"] = a["counts"]["estimable"]
    cell["tau2"] = a["tau2"]
    cell["hksj"] = {"applied": True, "q": a["hksj"]["q"], "df": a["hksj"]["df"],
                    "crit": a["hksj"]["crit"]}
    cell["structure"] = a["structure"]
    cell["node_vs_placebo"] = a["node_vs_placebo"]
    cell["league"] = a["league"]
    cell["pscore"] = a["pscore"]
    cell["direct_edges"] = a["structure"]["E"]
    cell["coprimary_role"] = "CONSERVATIVE CO-PRIMARY (full network)"
    cell["quarantine_applied"] = []
    cell.pop("before_quarantine", None)
    # the parallel co-primary
    cell["coprimary_quarantined"] = {
        "role": "PROVENANCE SENSITIVITY (integrity-quarantined network)",
        "quarantine_applied": sorted(QUAR),
        "trials": b["trials"], "arm_rows": b["arm_rows"],
        "contrasts_in_data": b["contrasts"],
        "nodes_in_network": b["structure"]["V"],
        "estimable_pairs": b["counts"]["estimable"],
        "tau2": b["tau2"], "i2": b["i2"],
        "hksj": {"applied": True, "q": b["hksj"]["q"], "df": b["hksj"]["df"],
                 "crit": b["hksj"]["crit"]},
        "structure": b["structure"],
        "node_vs_placebo": b["node_vs_placebo"],
        "league": b["league"], "pscore": b["pscore"],
        "direct_edges": b["structure"]["E"],
        "counts": b["counts"]}

ps, pb = quar_by_cell["OURS-STRICT"], full_by_cell["OURS-STRICT"]

# ------------------------------------------------------------- anchor -------
P["anchor"] = {
    "mode": "CO-PRIMARY",
    "passed": True,
    "gate": ("The FULL-network re-fit reproduces the settled primary to <1e-8 "
             "on both anchor nodes and on tau^2; only then is the quarantined "
             "co-primary emitted. See scripts/hfref_coprimary_fit.R."),
    "full": {
        "role": "CONSERVATIVE CO-PRIMARY",
        "trials": FU["trials"], "arm_rows": FU["arm_rows"],
        "ACEI+BB": [node(FU, "ACEI+BB")["rr"], node(FU, "ACEI+BB")["lo"],
                    node(FU, "ACEI+BB")["hi"]],
        "ACEI+BB+MRA": [node(FU, "ACEI+BB+MRA")["rr"],
                        node(FU, "ACEI+BB+MRA")["lo"],
                        node(FU, "ACEI+BB+MRA")["hi"]],
        "tau2": FU["tau2"], "i2": FU["i2"]},
    "quarantined": {
        "role": "PROVENANCE SENSITIVITY",
        "trials": QU["trials"], "arm_rows": QU["arm_rows"],
        "ACEI+BB": [node(QU, "ACEI+BB")["rr"], node(QU, "ACEI+BB")["lo"],
                    node(QU, "ACEI+BB")["hi"]],
        "ACEI+BB+MRA": [node(QU, "ACEI+BB+MRA")["rr"],
                        node(QU, "ACEI+BB+MRA")["lo"],
                        node(QU, "ACEI+BB+MRA")["hi"]],
        "tau2": QU["tau2"], "i2": QU["i2"]},
    "direction_flag": fit["presentation"]["direction_flag"],
    "direction_detail": DD,
    # kept for the anchor-provenance trail: these are the settled originals
    "settled_original": {"ACEI+BB": 0.64459765, "ACEI+BB+MRA": 0.59333495,
                         "tau2": 0.02323609,
                         "reproduced_by_full_network": True}}

# ------------------------------------------------------- quarantine record --
P["quarantine"] = {
    "date": DATE,
    "rule": ("A trial is withheld when BOTH hold: its per-arm all-cause death "
             "counts are UNVERIFIED against the accessible primary record, AND "
             "those counts are IDENTICAL across the trial's arms. Either alone "
             "is common and benign; the conjunction is the signature of a "
             "placeholder."),
    "symmetry": ("The rule is a property of the data, not of the trial, so it "
                 "is applied to every trial that meets it. All 87 arm rows / "
                 "43 trials were scanned. Four matched; %d are withheld here. "
                 "Cohn 1997 (2/35, 2/70) is dupe-excluded from every cell and "
                 "enters no fit, so there is nothing to withhold. GALACTIC-HF "
                 "(1078/1078) was withheld and is now REINSTATED: its counts "
                 "are verified against the ClinicalTrials.gov NCT02929329 "
                 "posted results, so it fails the rule's first limb."
                 % len(QUAR)),
    "reversibility": ("Symmetry cuts both ways. Limb (a) -- 'unverified' -- is "
                      "a statement about what has been looked for, not about "
                      "the data, so locating the source clears it without "
                      "changing any count. Every withheld trial therefore "
                      "carries a reinstatement condition, and meeting it "
                      "returns the trial to the fit. A rule that could only "
                      "ever remove trials would be a ratchet, not a check."),
    "reinstated": [
        {"id": k, "trial": v["trial"], "cleared_because": v["cleared"],
         "count_source": v["count_source"], "restored_rows": v["rows"],
         "restores_node": v["restores"],
         "evidence": "outputs/hfref_galactic_allcause_recovery.json"}
        for k, v in sorted(REINST.items())],
    "principle": ("Quarantine, never silent deletion, and never replacement. "
                  "Every withheld contribution carries a NAMED violation, its "
                  "arm rows stay on record in "
                  "outputs/hfref_quarantine_ledger.json, and the FULL network "
                  "is still fitted and still displayed beside the quarantined "
                  "one as the conservative co-primary."),
    "withheld": [
        {"id": k, "trial": v["trial"], "violation": v["violation"],
         "source": v["source"], "withheld_rows": v["rows"],
         "reinstatement_condition": v["reinstatement"],
         "structural_cost": v["cost"]}
        for k, v in sorted(QUAR.items())],
    "considered_and_NOT_withheld": [
        {"id": "HF-055", "trial": "Cohn 1997",
         "why": ("Identical across-arm counts (2/35, 2/70), but dupe-excluded "
                 "by select_trials() from all four cells. It enters no fit, so "
                 "there is nothing to withhold. Recorded so the scan is "
                 "auditable rather than asserted.")},
        {"id": "HF-008", "trial": "SPICE",
         "why": ("Counts are not identical (6/179 vs 3/91) and the primary was "
                 "located: PMID 10740141 (Granger, Am Heart J 2000;139:609-17). "
                 "RE-TIERED this pass from VERIFIED_FULL to "
                 "RECOVERED_FROM_PERCENTAGE_UNIQUE -- see count_provenance."),
         "consequence_of_retaining_it": (
             "SPICE alone supplies the Placebo-ARB edge, the network's only "
             "between-trial loop. Branches 7b/7c, which drop SPICE, have "
             "ICDF 0.")},
        {"id": "HF-020", "trial": "He 2015",
         "why": ("PMC5746969 Table 1 gives the arm sizes and Table 2 the "
                 "per-arm all-cause deaths; 19/198 = 11/97 + 8/101 and 14/96 "
                 "match exactly. Verified, and counts differ across arms.")},
        {"id": "HF-038", "trial": "QUEST",
         "why": ("Counts verified verbatim in PMC11333273 (221 and 262) and "
                 "they differ across arms. The finding is a presentation "
                 "constraint, not a data error.")}],
    "ledger": "outputs/hfref_quarantine_ledger.json",
    "refit": FIT,
    "report": "outputs/HFREF_INTEGRITY_GATES_2026-07-30.md"}

# --------------------------------------------------- count-provenance tier --
P["count_provenance"] = {
    "date": DATE,
    "why": ("Verification status alone conflated a count the source PRINTS "
            "with a count we BACK-COMPUTED from a rounded percentage. These "
            "are separate axes and are now separately labelled."),
    "tiers": {
        "VERBATIM_COUNT": "The per-arm death count is printed as an integer in the source.",
        "RECOVERED_FROM_PERCENTAGE_UNIQUE": (
            "The source prints only a rounded percentage; exactly one integer "
            "rounds to it against the stated denominator, so the recovery "
            "carries no discretion. Sound, but not a verbatim-reported count, "
            "and it inherits any error in the published percentage."),
        "RECOVERED_FROM_PERCENTAGE_NON_UNIQUE": (
            "More than one integer rounds to the published percentage; the "
            "ledger value is one of several admissible integers."),
        "NOT_RECOVERABLE_FROM_PERCENTAGE": (
            "No integer over the stated denominator reproduces the published "
            "percentage; the ledger value's origin is unexplained."),
        "UNVERIFIED": "Neither the count nor a percentage from which to derive it is stated."},
    "assignments": {
        "HF-008 SPICE": {
            "tier": "RECOVERED_FROM_PERCENTAGE_UNIQUE",
            "was": "VERIFIED_FULL",
            "detail": ("The source states no integer deaths, only 'death 3.4% "
                       "and 3.3%'. Candesartan 3.4% over n=179 admits exactly "
                       "one integer, 6; placebo 3.3% over n=91 admits exactly "
                       "one, 3. Uniqueness re-checked by exhaustive search. "
                       "SPICE stays in the network, fully sourced -- this is a "
                       "labelling correction, not a downgrade, and no count "
                       "or fit changed."),
            "doi": "10.1016/s0002-8703(00)90037-1", "pmid": "10740141"},
        "HF-018 US-Carvedilol": {
            "tier": "RECOVERED_FROM_PERCENTAGE_UNIQUE", "was": "VERIFIED_FULL",
            "detail": "7.8% over n=398 -> {31} unique; 3.2% over n=696 -> {22} unique."},
        "HF-023 EMPHASIS-HF": {
            "tier": "RECOVERED_FROM_PERCENTAGE_NON_UNIQUE", "was": "VERIFIED_FULL",
            "detail": ("Placebo 15.5% over n=1373 -> {213} unique, but "
                       "eplerenone 12.5% over n=1364 admits TWO integers, 170 "
                       "and 171. The ledger's 171 is admissible but not "
                       "uniquely determined.")},
        "HF-010 ELITE": {
            "tier": "SPLIT -- losartan RECOVERED_FROM_PERCENTAGE_UNIQUE, "
                    "captopril NOT_RECOVERABLE_FROM_PERCENTAGE",
            "was": "VERIFIED_FULL",
            "detail": ("NEW FINDING. Losartan 4.8% over n=352 -> {17} unique, "
                       "matching the ledger. But captopril 8.7% over n=370 "
                       "admits NO integer: 32/370 = 8.649% (prints 8.6%), "
                       "33/370 = 8.919% (prints 8.9%). The ledger's 32 is not "
                       "derivable from the published percentage -- most likely "
                       "the published figures are Kaplan-Meier estimates at 48 "
                       "weeks, not crude proportions. NOT a quarantine trigger "
                       "(counts differ across arms) and no count was changed. "
                       "Raised for the next gate.")}},
    "verbatim_count_trials": [
        "SOLVD-Treatment", "CIBIS-I", "CIBIS-II", "MERIT-HF", "COPERNICUS",
        "BEST", "RALES", "J-EMPHASIS-HF", "PARADIGM-HF", "DAPA-HF", "VICTOR",
        "DIGIT-HF", "He 2015", "QUEST"],
    "counts_changed": 0,
    "method": ("Exhaustive integer search: for published percentage p at d "
               "decimals and denominator n, the admissible set is "
               "{x in 0..n : p - 0.5*10^-d <= 100*x/n < p + 0.5*10^-d}.")}

# ----------------------------------------------- trial ledger annotations ---
FIXES = {
    "HF-008": dict(
        pmid="10740141", doi="10.1016/s0002-8703(00)90037-1",
        count_provenance_tier="RECOVERED_FROM_PERCENTAGE_UNIQUE",
        pmid_note=(
            "SOURCED 2026-07-30, RE-TIERED 2026-07-30. The primary is Granger "
            "CB et al, Am Heart J 2000;139(4):609-17, DOI "
            "10.1016/s0002-8703(00)90037-1 = SPICE (Study of Patients "
            "Intolerant of Converting Enzyme inhibitors); the acronym is absent "
            "from the PubMed record, which is why an acronym-keyed search "
            "missed it. Abstract: 'randomization in a 2:1 ratio to receive "
            "candesartan (n = 179) or a placebo (n = 91)' and 'death 3.4% and "
            "3.3%'. TIER: RECOVERED_FROM_PERCENTAGE_UNIQUE, not VERIFIED_FULL. "
            "The source prints NO integer death counts. 6 and 3 are each the "
            "unique integer rounding to the published percentages against the "
            "stated denominators (6/179 = 3.352%, 3/91 = 3.297%). That is a "
            "sound derivation but it is not a verbatim-reported count, unlike "
            "CIBIS-II or MERIT-HF which print their integers. SPICE stays in "
            "the network: this is a labelling correction, no count changed.")),
    "HF-018": dict(count_provenance_tier="RECOVERED_FROM_PERCENTAGE_UNIQUE",
                   pmid_note=("RE-TIERED 2026-07-30. Counts derived from "
                              "'7.8 percent' and '3.2 percent'; 31/398 and "
                              "22/696 are each uniquely determined. Retained.")),
    "HF-023": dict(count_provenance_tier="RECOVERED_FROM_PERCENTAGE_NON_UNIQUE",
                   pmid_note=("RE-TIERED 2026-07-30. Counts derived from "
                              "'12.5%' and '15.5%'. Placebo 213/1373 is "
                              "unique; eplerenone 12.5% over n=1364 admits "
                              "BOTH 170 and 171. The ledger's 171 is "
                              "admissible but not uniquely determined. "
                              "Retained; the 1-death ambiguity is far below "
                              "the resolution of any network estimate.")),
    "HF-010": dict(count_provenance_tier="NOT_RECOVERABLE_FROM_PERCENTAGE",
                   pmid_note=("RE-TIERED 2026-07-30 and a NEW FINDING. "
                              "Losartan 17/352 is uniquely recovered from the "
                              "published 4.8%. Captopril is NOT: 8.7% over "
                              "n=370 admits no integer (32 prints 8.6%, 33 "
                              "prints 8.9%), so the ledger's 32 cannot be "
                              "derived from the accessible record. Most likely "
                              "the published 4.8%/8.7% are Kaplan-Meier "
                              "estimates at 48 weeks rather than crude "
                              "proportions. NOT a quarantine trigger -- the "
                              "counts are not identical across arms -- and no "
                              "count was changed. Raised for the next gate.")),
    "HF-019": dict(
        pmid="10653828", doi="10.1161/01.cir.101.4.378",
        count_provenance_tier="VERBATIM_COUNT (body text, SECONDARY_CORROBORATED)",
        pmid_note=("CORRECTED 2026-07-30: was PMID 10477530 (McKelvie, "
                   "Circulation 1999;100:1056-64), the candesartan/enalapril "
                   "comparison in 768 patients, which contains no metoprolol "
                   "randomisation and cannot substantiate this contrast. The "
                   "data are the RESOLVD metoprolol sub-study, Circulation "
                   "2000;101(4):378-84: '426 patients ... randomized to receive "
                   "metoprolol CR or placebo' (212+214=426). The abstract's "
                   "'3.4% versus 8.1%' conflicts with the paper's own body "
                   "text, which reports the metoprolol deaths as n=8 (3.7%) vs "
                   "placebo n=17 (8.1%); the extracted 8 and 17 match the body. "
                   "The residual is an inconsistency INTERNAL TO THE SOURCE, "
                   "not an extraction error. Evidence tier for the body "
                   "figures: SECONDARY_CORROBORATED (publisher blocks "
                   "automated retrieval; that was not circumvented).")),
    "HF-020": dict(
        count_provenance_tier="VERBATIM_COUNT",
        pmid_note=("VERIFIED FULL 2026-07-30 from PMC5746969. Table 1 arm "
                   "sizes: metoprolol 96, low-dose benazepril 97, low-dose "
                   "valsartan 100, high-dose benazepril 101, high-dose "
                   "valsartan 97. Table 2 all-cause deaths: 14, 11, 13, 8, 8. "
                   "Ledger ACEI 19/198 = 11/97 + 8/101 exactly; BB 14/96 "
                   "exactly. DISCLOSURES: (a) the two benazepril DOSE arms are "
                   "pooled onto one ACEI node; the trial found them "
                   "significantly different (P=0.042) but that P is for the "
                   "PRIMARY COMPOSITE, not all-cause death - on all-cause "
                   "death the arms are 11/97 vs 8/101, Fisher p=0.49, so the "
                   "pooling is defensible for THIS outcome. (b) the two "
                   "valsartan arms (13/100 and 8/97) are dropped entirely "
                   "rather than mapped to the ARB node. (c) the source is "
                   "internally inconsistent on enrolment: abstract and "
                   "registry say 480, the Results text and Table 1 sum to 491.")),
    "HF-038": dict(
        count_provenance_tier="VERBATIM_COUNT",
        pmid_note=("VERIFIED FULL 2026-07-30 from PMC11333273: 'A total of 221 "
                   "patients (14.21%) in the QLQX group and 262 patients "
                   "(16.85%) in the placebo group died from any cause (HR, "
                   "0.84; 95% CI, 0.70-1.01; P = 0.058).' Counts and "
                   "denominators exact. BINDING PRESENTATION CONSTRAINT: the "
                   "trial's own all-cause-mortality analysis is NOT "
                   "significant. Fisher's exact on the crude 2x2 gives "
                   "p=0.0426 with fragility index 1, but that test ignores "
                   "censoring and differential follow-up. No QLQX contrast may "
                   "be presented as significant on the crude 2x2.")),
}

QNOTE = {
    "HF-021": ("QUARANTINED 2026-07-30 (symmetric pass). PMID 15115904 "
               "confirms the arms (carvedilol N=191, enalapril N=190, "
               "combination N=191) but the trial's primary endpoint is LVESVI "
               "and it reports NO per-arm deaths anywhere -- its only safety "
               "statement is 'All three arms showed similar safety profiles "
               "and withdrawal rates.' The 14/14/14 has no located source, and "
               "the settled fit script's line 377 already called CARMEN "
               "inadmissible. Withheld from the QUARANTINED co-primary; STILL "
               "PRESENT in the FULL co-primary, which is displayed beside it."),
    "HF-034": ("QUARANTINED then REINSTATED 2026-07-30. The quarantine was "
               "correct on the evidence then in hand: PMID 33185990 confirms "
               "the denominators exactly (omecamtiv 4120, placebo 4112) but "
               "states only CARDIOVASCULAR death -- '808 patients (19.6%) and "
               "798 patients (19.4%) ... died from cardiovascular causes' -- so "
               "the identical 1078/1078 all-cause figure was unverified AND "
               "identical, which is the rule exactly. The pass flagged the "
               "registry as the one route it had not exhausted. That route "
               "closes it: the ClinicalTrials.gov NCT02929329 posted results "
               "state per-arm ALL-CAUSE deaths as verbatim integers in the "
               "FDAAA All-Cause Mortality table -- 1078 of 4112 (placebo) and "
               "1078 of 4120 (omecamtiv) -- matching the extraction exactly in "
               "both arms, over a window running to end of study. The identical "
               "count is a genuine coincidence (26.216% vs 26.165%). Only the "
               "identical limb of the rule still holds, so the trial is "
               "RETAINED IN BOTH co-primary fits and the +Omecamtiv node "
               "survives. No count was changed."),
    "HF-025": ("QUARANTINED 2026-07-30 (symmetric pass). PMID 24196866 "
               "confirms n=65/65 exactly, but the trial reports only the "
               "composite of death from any cause or cardiovascular "
               "hospitalization and event-free survival; no per-arm all-cause "
               "death count is stated. The ledger's identical 8/8 is unverified "
               "AND identical across arms. Withheld from the QUARANTINED "
               "co-primary; STILL PRESENT in the FULL one."),
}

n_quar = 0
n_reinst = 0
for t in P["trials"]:
    tid = t.get("id")
    if tid in FIXES:
        t.update(FIXES[tid])
    if tid in QUAR:
        t["quarantined"] = True
        t["quarantine_violation"] = QUAR[tid]["violation"]
        t["in_network"] = True          # in the FULL co-primary
        t["in_quarantined_network"] = False
        t["count_provenance_tier"] = "UNVERIFIED"
        t["pmid_note"] = QNOTE[tid]
        n_quar += 1
    elif tid in REINST:
        # In BOTH fits, but carrying its quarantine history rather than passing
        # silently as a trial that was never questioned.
        #
        # A previous run of this script wrote quarantine_violation onto this
        # trial. The payload is rewritten in place, so leaving that key would
        # ship a trial marked quarantined=false while still carrying live prose
        # asserting a violation against it -- a self-contradicting surface.
        # Demote it to a history field instead of deleting it: the finding was
        # real when it was made, and the record of it is worth keeping.
        stale = t.pop("quarantine_violation", None)
        if stale:
            t["violation_when_quarantined"] = stale
            t["violation_resolved_by"] = REINST[tid]["count_source"]
        t["quarantined"] = False
        t["was_quarantined"] = True
        t["reinstated"] = True
        t["reinstated_because"] = REINST[tid]["cleared"]
        t["count_source"] = REINST[tid]["count_source"]
        t["in_network"] = True
        t["in_quarantined_network"] = True
        t["count_provenance_tier"] = "VERBATIM_COUNT"
        t["pmid_note"] = QNOTE[tid]
        n_reinst += 1
    else:
        t.setdefault("quarantined", False)
        t.setdefault("in_network", True)
        t["in_quarantined_network"] = True
        t.setdefault("count_provenance_tier", "VERBATIM_COUNT")
if n_quar != len(QUAR):
    sys.exit("FAIL: expected exactly %d quarantined trials, found %d"
             % (len(QUAR), n_quar))
if n_reinst != len(REINST):
    sys.exit("FAIL: expected exactly %d reinstated trials, found %d"
             % (len(REINST), n_reinst))

# ------------------------------------------------------------- nma_config ---
# The prior pass DELETED the edge CARMEN alone supplied. The full co-primary
# needs it back, so the full edge set is recovered from the last commit whose
# payload still carried it, and the quarantined set is derived from that.
pre = subprocess.run(["git", "show", "%s:%s" % (PRE_QUARANTINE_REV, APP)],
                     capture_output=True, text=True, encoding="utf-8")
if pre.returncode != 0:
    sys.exit("FAIL: cannot read %s:%s" % (PRE_QUARANTINE_REV, APP))
pre_payload = json.loads(re.search(PAYLOAD_RE, pre.stdout, re.S).group(2))
full_cmp = pre_payload["nma_config"]["comparisons"]
if len(full_cmp) != FU["structure"]["E"]:
    sys.exit("FAIL: recovered %d edges, R says the full network has %d"
             % (len(full_cmp), FU["structure"]["E"]))

quar_cmp, dropped_edges = [], []
for c in full_cmp:
    keep = [x for x in c["trials"] if x not in QNAMES]
    if keep:
        quar_cmp.append({"t1": c["t1"], "t2": c["t2"], "trials": keep})
    else:
        dropped_edges.append("%s vs %s" % (c["t1"], c["t2"]))
if len(quar_cmp) != QU["structure"]["E"]:
    sys.exit("FAIL: derived %d quarantined edges, R says %d"
             % (len(quar_cmp), QU["structure"]["E"]))

P["nma_config"]["comparisons"] = full_cmp
P["nma_config"]["comparisons_quarantined"] = quar_cmp
P["nma_config"]["edges_dropped_by_quarantine"] = dropped_edges
fst, qst = FU["structure"], QU["structure"]
P["nma_config"]["note"] = (
    "CO-PRIMARY. (a) FULL NETWORK -- %d RCTs, %d nodes, %d direct edges, "
    "cyclomatic %d, ICDF %d. This is the conservative co-primary and the "
    "default shown here. (b) INTEGRITY-QUARANTINED NETWORK -- %d RCTs, %d "
    "nodes, %d direct edges, cyclomatic %d, ICDF %d, after withholding CARMEN "
    "and Vizzardi 2014 under the rule 'unverified per-arm all-cause deaths AND "
    "identical across-arm counts'. Edges lost: %s. NO NODE is lost: both "
    "networks carry all %d treatments, so every league pair is estimable in "
    "both. GALACTIC-HF was withheld by an earlier pass -- which did delete the "
    "+Omecamtiv node -- and has since been reinstated on verified "
    "ClinicalTrials.gov all-cause counts, restoring it. "
    "ICDF is UNCHANGED at %d: the loop CARMEN closed lay entirely inside a "
    "single study and the ICDF definition already excluded such loops. The one "
    "between-trial loop that remains is Placebo-ACEI-ARB, and it survives only "
    "because SPICE was re-sourced rather than quarantined. Random-effects GLS "
    "network fit, log-RR scale, REML tau^2, HKSJ variance inflation with the "
    "mandatory max(1,.) floor and a t_df critical value."
) % (FU["trials"], fst["V"], fst["E"], fst["cyclomatic"], fst["icdf"],
     QU["trials"], qst["V"], qst["E"], qst["cyclomatic"], qst["icdf"],
     "; ".join(dropped_edges), qst["V"], qst["icdf"])
# The "NO NODE is lost" sentence above is a claim about this fit, so gate it
# rather than trusting the prose to stay true if the quarantine set changes.
if qst["V"] != fst["V"]:
    sys.exit("FAIL: nma_config note claims no node is lost, but the quarantined "
             "network has %d nodes vs the full network's %d"
             % (qst["V"], fst["V"]))

# --------------------------------------------------------------- coverage ---
P["coverage"] = {
    "mode": "CO-PRIMARY",
    "full_network_trials": FU["trials"],
    "quarantined_network_trials": QU["trials"],
    "trials_on_record": len(P["trials"]),
    "quarantined": len(QUAR),
    "reinstated": len(REINST),
    "arm_rows_full": FU["arm_rows"],
    "arm_rows_quarantined": QU["arm_rows"],
    "arm_rows_withheld": FU["arm_rows"] - QU["arm_rows"],
    "study_contrasts_full": FU["contrasts"],
    "study_contrasts_quarantined": QU["contrasts"],
    "pmid_verified": FU["trials"],
    "pmid_missing": 0,
    "note": ("Arm rows %d -> %d: CARMEN's 3 and Vizzardi 2014's 2 are withheld "
             "from the quarantined co-primary, %d in total. Contrasts %d -> %d. "
             "GALACTIC-HF's 2 rows were withheld by an earlier pass and are "
             "RESTORED, on per-arm all-cause deaths verified against the "
             "ClinicalTrials.gov NCT02929329 posted results. All %d rows remain "
             "on record in outputs/hfref_quarantine_ledger.json and all %d "
             "trials remain in the FULL co-primary. Every trial carries a PMID: "
             "SPICE's was located this pass.")
    % (FU["arm_rows"], QU["arm_rows"], FU["arm_rows"] - QU["arm_rows"],
       FU["contrasts"], QU["contrasts"], FU["arm_rows"], FU["trials"])}

P["fit_source"] = (
    "F:/E156/hfref_eightcell_fit.R (lines 1-587 only, never its RUN or EMIT "
    "sections), re-executed twice by scripts/hfref_coprimary_fit.R -- once "
    "with every trial retained (the conservative co-primary) and once with the "
    "%d integrity-quarantined trials withheld (the provenance sensitivity) "
    "-- and expanded to all pairwise contrasts. Anchor-gated: the FULL fit "
    "must reproduce the settled primary to <1e-8 before the quarantined fit is "
    "emitted." % len(QUAR))

html = html[:m.start(2)] + json.dumps(P, ensure_ascii=False) + html[m.end(2):]

# ---------------------------------------------------------------- verdict ---
n_excl_full = FU["counts"]["ci_excludes_null"]
n_excl_quar = QU["counts"]["ci_excludes_null"]
indirect_excl = sum(1 for p in FU["league"]
                    if (p["lo"] > 1 or p["hi"] < 1) and p["direct_k"] == 0)
common = DD["common_pairs"]
f_ex, q_ex = (DD["ci_excludes_null_common"]["full"],
              DD["ci_excludes_null_common"]["quarantined"])
n_gain, n_lose = len(DD["gained_significance"]), len(DD["lost_significance"])
NPC = DD["node_point_estimate_pct_change"]
node_med = NPC["median"]
node_total = NPC["retained_nodes"]
node_away = NPC["moved_away_from_null"]
node_toward = NPC["moved_toward_null"]
node_worst = NPC["largest_move_toward_null"]
wid_med = DD["pair_ci_width_pct_change"]["median"]

verdict = {
    "verdict": "UNCERTAIN",
    "presentation_mode": "CO-PRIMARY",
    "counts": {
        "P0_internal": 0, "P0_aact_nct_missing": 0, "P0_grim": 0,
        "P1_aact_concord": 0, "P1_fi_critical": 0, "P1_fi_warn": 0,
        "P1_pi_gap": 0, "P2_evidence_incomplete": 0, "P2_aact_advisory": 0,
        "n_trials_seen": FU["trials"],
        "n_trials_full_coprimary": FU["trials"],
        "n_trials_quarantined_coprimary": QU["trials"],
        "trials_on_record": len(P["trials"]),
        "gates_executed_date": DATE,
        "findings_raised": 5, "findings_resolved": 5, "findings_open": 0,
        "gate_findings_raised": 4, "gate_findings_resolved": 4,
        "trials_quarantined": len(QUAR),
        "trials_reinstated": len(REINST),
        "audit_claims_withdrawn": 3,
        "count_values_changed": 0,
        "arm_rows_full": FU["arm_rows"],
        "arm_rows_quarantined": QU["arm_rows"],
        "arm_rows_checked": FU["arm_rows"],
        "contrasts_full": FU["contrasts"],
        "contrasts_quarantined": QU["contrasts"],
        "registry_concordance_applicable": 9,
        "registry_concordance_not_applicable": 18,
        "grim_applicable": False,
        "nma_ci_excludes_1_full": n_excl_full,
        "nma_ci_excludes_1_quarantined": n_excl_quar,
        "nma_ci_excludes_1_like_for_like": {"common_pairs": common,
                                            "full": f_ex, "quarantined": q_ex,
                                            "gained": n_gain, "lost": n_lose},
        "nma_ci_excludes_1_purely_indirect": indirect_excl,
        "icdf_full": fst["icdf"], "icdf_quarantined": qst["icdf"],
        "nodes_full": fst["V"], "nodes_quarantined": qst["V"]},
    "reasons": [
        ("PRESENTED AS CO-PRIMARY. (a) the FULL network, %d trials, %d arm "
         "rows, ACEI+BB %s and ACEI+BB+MRA %s -- the CONSERVATIVE co-primary. "
         "(b) the INTEGRITY-QUARANTINED network, %d trials, %d arm rows, "
         "ACEI+BB %s and ACEI+BB+MRA %s -- a PROVENANCE SENSITIVITY. Both are "
         "displayed. Neither replaces the other."
         % (FU["trials"], FU["arm_rows"], f3(node(FU, "ACEI+BB")["rr"]),
            f3(node(FU, "ACEI+BB+MRA")["rr"]), QU["trials"], QU["arm_rows"],
            f3(node(QU, "ACEI+BB")["rr"]), f3(node(QU, "ACEI+BB+MRA")["rr"]))),
        ("THE QUARANTINE RULE IS A CONJUNCTION, APPLIED SYMMETRICALLY AND "
         "RELEASED SYMMETRICALLY. The rule is 'unverified per-arm all-cause "
         "deaths AND identical across-arm counts'. TWO trials currently meet "
         "it: CARMEN (14/14/14, 572 pts) and Vizzardi 2014 (8/8, 130 pts). "
         "Identical counts alone are NOT a violation -- they are the trigger "
         "for checking provenance, never the finding itself."),
        ("GALACTIC-HF WAS QUARANTINED AND IS NOW REINSTATED. It was withheld "
         "because its identical 1078/1078 all-cause figure could not be "
         "confirmed: PMID 33185990 states CARDIOVASCULAR death (808/798) only. "
         "The ClinicalTrials.gov NCT02929329 posted results DO state per-arm "
         "ALL-CAUSE deaths, as verbatim integers in the FDAAA All-Cause "
         "Mortality table -- 1078 of 4112 placebo and 1078 of 4120 omecamtiv, "
         "matching the extraction exactly in both arms on the publication's own "
         "denominators. The identical count is a genuine coincidence (26.216% "
         "vs 26.165%). Only the 'identical' limb still holds, so the trial is "
         "retained in BOTH fits. No count was changed. A rule that could only "
         "ever remove trials would be a ratchet, not an integrity check."),
        ("THE SCAN IS RECORDED, NOT ASSERTED. All 87 arm rows / 43 trials were "
         "checked for identical across-arm counts. Four matched; two are "
         "quarantined. Cohn 1997 (2/35, 2/70) is dupe-excluded from every "
         "fitted cell, so it enters no fit and there is nothing to withhold, "
         "and GALACTIC-HF's identical counts are verified. Both are logged with "
         "explicit entries rather than dropped from the record."),
        ("ANCHOR. The FULL co-primary reproduces the settled primary exactly -- "
         "ACEI+BB 0.64459765, ACEI+BB+MRA 0.59333495, tau^2 0.02323609, all to "
         "<1e-8 -- and the quarantined fit is emitted only after that gate "
         "passes. Quarantined anchors: ACEI+BB %.8f, ACEI+BB+MRA %.8f."
         % (node(QU, "ACEI+BB")["rr"], node(QU, "ACEI+BB+MRA")["rr"])),
        ("HONEST DIRECTION FLAG, PART 1 -- POINT ESTIMATES MOSTLY MOVE AWAY "
         "FROM THE NULL. %d of %d retained treatment nodes fall (median "
         "%+.2f%%) when the unverified identical-count trials are withheld, "
         "because identical counts are RR=1.00 on every edge they touch and act "
         "as a null-pulling weight. %d move the other way (largest %s %+.2f%%). "
         "The majority direction is real and it must NOT be read as evidence of "
         "benefit; it is why the quarantined fit is labelled a provenance "
         "sensitivity. The split is COUNTED, not asserted: earlier passes of "
         "this app claimed EVERY retained node fell, which was never true."
         % (node_away, node_total, node_med, node_toward,
            node_worst["node"], node_worst["pct"])),
        ("HONEST DIRECTION FLAG, PART 2 -- INTERVAL SIGNIFICANCE FALLS, IT "
         "DOES NOT RISE. On the %d pairs BOTH fits estimate, the number whose "
         "CI excludes 1 goes %d -> %d: %d gain significance, %d lose it. tau^2 "
         "rises %.1f%%, I^2 goes %.1f%% -> %.1f%%, HKSJ df falls %d -> %d, and "
         "CI widths grow by a median %+.2f%%. The single-trial (CARMEN-only) "
         "re-fit reported this count RISING 12 -> 17; that rise was an "
         "artefact of an asymmetric quarantine, and once the added "
         "heterogeneity and lost degrees of freedom are counted it falls "
         "instead. Neither reading makes the quarantined fit stronger evidence."
         % (common, f_ex, q_ex, n_gain, n_lose,
            100 * (QU["tau2"] / FU["tau2"] - 1), 100 * FU["i2"], 100 * QU["i2"],
            FU["hksj"]["df"], QU["hksj"]["df"], wid_med)),
        ("STRUCTURAL COST OF THE QUARANTINE, STATED PLAINLY. NO NODE IS LOST: "
         "nodes %d -> %d, so every one of the %d league pairs is estimable in "
         "both fits. Edges %d -> %d and cyclomatic %d -> %d. ICDF is UNCHANGED "
         "at %d, because CARMEN's loop lay entirely inside one study and the "
         "ICDF definition already excluded such loops. This is a CHANGE from "
         "the previous pass, which withheld GALACTIC-HF and so DELETED the "
         "+Omecamtiv node (nodes 15 -> 14) and 14 league pairs with it. "
         "Reinstating GALACTIC-HF on verified registry counts restores that "
         "node. Note what did and did not move: GALACTIC-HF sits on a PENDANT "
         "edge to a leaf node, so it carries no information about any other "
         "contrast -- restoring it recovers a whole treatment comparison while "
         "shifting the other anchors by <1e-7. The structural gain is large; "
         "the numerical perturbation is not. Both are true."
         % (fst["V"], qst["V"], len(QU["league"]), fst["E"], qst["E"],
            fst["cyclomatic"], qst["cyclomatic"], qst["icdf"])),
        ("SPICE IS RE-TIERED, NOT QUARANTINED. Its counts were labelled "
         "VERIFIED_FULL, which put them in the same tier as CIBIS-II and "
         "MERIT-HF, whose integers the source PRINTS. SPICE's are not printed: "
         "the source gives only 'death 3.4% and 3.3%', and 6/179 and 3/91 are "
         "the unique integers rounding to those figures. New tier: "
         "RECOVERED_FROM_PERCENTAGE_UNIQUE. It stays in the network, fully "
         "sourced (PMID 10740141, DOI 10.1016/s0002-8703(00)90037-1). "
         "Labelling only -- no count and no fit changed. This matters because "
         "SPICE alone supplies the Placebo-ARB leg and therefore the network's "
         "only between-trial loop."),
        ("THE TIER IS APPLIED SYMMETRICALLY TOO. Exhaustive integer search over "
         "all 28 trials found three more counts derived rather than printed: "
         "US-Carvedilol (unique), EMPHASIS-HF (NON-unique -- eplerenone 12.5% "
         "admits both 170 and 171), and ELITE, which raises a NEW FINDING: "
         "captopril 8.7% over n=370 admits NO integer at all (32 prints 8.6%, "
         "33 prints 8.9%), so the ledger's 32 is not derivable from the "
         "published percentage. Likely a Kaplan-Meier estimate rather than a "
         "crude proportion. Not a quarantine trigger, no count changed, raised "
         "for the next gate."),
        ("THREE AUDIT CLAIMS REMAIN WITHDRAWN AS WRONG. SPICE was reported to "
         "have no primary source: it has one, PMID 10740141. He 2015's per-arm "
         "denominators were reported unverified: PMC5746969 Tables 1 and 2 "
         "verify them exactly (19/198 = 11/97 + 8/101). QUEST's counts were "
         "reported unverified: PMC11333273 states 221 and 262 verbatim."),
        ("QUEST remains a live PRESENTATION constraint. The trial's own "
         "all-cause-mortality analysis is HR 0.84 (95% CI 0.70-1.01), P=0.058 - "
         "NOT significant. Fisher's exact on the crude 2x2 gives p=0.0426 with "
         "a fragility index of 1. The trial's reported analysis is "
         "authoritative; no QLQX contrast is presented as significant on the "
         "crude 2x2."),
        ("%d of the %d contrasts whose CI excludes 1 in the FULL co-primary are "
         "PURELY INDIRECT. The Walsh fragility index is defined on an observed "
         "2x2 table; an indirect estimate has none. No fragility index is "
         "quoted for them, and their fragility is not merely unfavourable - it "
         "is unmeasurable by that method." % (indirect_excl, n_excl_full)),
        ("Arithmetic remains clean and this is a tested zero: all %d arm rows "
         "pass count plausibility and all %d contrasts recompute logRR and "
         "seLogRR from the raw counts to under 1e-8. GRIM/GRIMMER is NOT "
         "APPLICABLE (binary outcome, no means), not passed."
         % (FU["arm_rows"], FU["contrasts"])),
        ("Registry concordance still covers only 9 of the %d trials; the rest "
         "predate ClinicalTrials.gov or are registered elsewhere, so "
         "concordance is N/A - there is no record to concord with. No "
         "concordance is claimed for them." % FU["trials"]),
        ("VERDICT STAYS UNCERTAIN. Applying the rule symmetrically and showing "
         "both fits did not earn a PASS - it made the uncertainty visible "
         "rather than resolving it. Full-text verification is still absent for "
         "8 denominator-only trials, %d trials have no sourced mortality at "
         "all, no inconsistency test is fitted, and AMSTAR-2 confidence "
         "remains CRITICALLY LOW." % len(QUAR)),
    ],
}

mv = re.search(r'(<script>window\.__verdict = )(\{.*?\})(;?\s*</script>)', html, re.S)
if not mv:
    sys.exit("FAIL: window.__verdict block not found")
html = html[:mv.start(2)] + json.dumps(verdict, ensure_ascii=False) + html[mv.end(2):]

# ------------------------------------------------------------ badge prose ---
badge_headline = ("VERDICT: UNCERTAIN &mdash; CO-PRIMARY (FULL + QUARANTINED) "
                  "&middot; %d TRIALS QUARANTINED, %d REINSTATED"
                  % (len(QUAR), len(REINST)))
badge_body = (
    '<div style="margin-top:8px;font-size:12.5px;line-height:1.6;">'
    '<b>Presented as co-primary.</b> <b>(a) FULL network</b> &mdash; %d trials, %d arm rows, '
    'ACEI+BB <b>%s</b>, ACEI+BB+MRA <b>%s</b>: the <b>conservative</b> co-primary. '
    '<b>(b) INTEGRITY-QUARANTINED network</b> &mdash; %d trials, %d arm rows, '
    'ACEI+BB <b>%s</b>, ACEI+BB+MRA <b>%s</b>: a <b>provenance sensitivity</b>. '
    'Both are shown; neither replaces the other.'
    '<br><b>Quarantined (%d, rule applied symmetrically):</b> '
    'CARMEN &mdash; <i>14/14/14, 572 pts; primary is LVESVI and the source reports no deaths</i>; '
    'Vizzardi 2014 &mdash; <i>8/8, 130 pts; the source reports only composite event-free '
    'survival</i>. The rule is <i>unverified per-arm all-cause deaths <b>AND</b> identical '
    'across-arm counts</i> &mdash; a conjunction, so identical counts alone are never the '
    'finding, only the trigger to check provenance. All 87 arm rows were scanned; four matched. '
    'Cohn 1997 is dupe-excluded from every cell and enters no fit. Arm rows retained in '
    '<code>outputs/hfref_quarantine_ledger.json</code>, not deleted.'
    '<br><b style="color:#86efac">Reinstated (1): GALACTIC-HF.</b> It was quarantined because '
    'PMID 33185990 states <i>cardiovascular</i> death only (808/798), leaving its identical '
    '1078/1078 all-cause figure unverified. The <b>ClinicalTrials.gov NCT02929329 posted '
    'results do state per-arm all-cause deaths</b>, as verbatim integers in the FDAAA '
    'All-Cause Mortality table: <b>1078 of 4112</b> (placebo) and <b>1078 of 4120</b> '
    '(omecamtiv), matching the extraction exactly in both arms, on the publication&rsquo;s own '
    'denominators. The identical count is a genuine coincidence (26.216%% vs 26.165%%). Only the '
    '&ldquo;identical&rdquo; limb of the rule still holds, so the trial is <b>retained in both '
    'fits</b> and <b>no count was changed</b>. A rule that could only ever remove trials would '
    'be a ratchet, not an integrity check.'
    '<br><b>Anchor:</b> the FULL co-primary reproduces the settled primary exactly &mdash; '
    'ACEI+BB <b>0.645</b>, ACEI+BB+MRA <b>0.593</b>, &tau;&sup2; 0.02323609, all to &lt;1e-8. '
    'Quarantined: ACEI+BB <b>%s</b>, ACEI+BB+MRA <b>%s</b>.'
    '<br><b style="color:#fdba74">Honest direction flag &mdash; two parts, neither favourable.</b> '
    '<b>(1)</b> Withholding these null-pulling unverified trials moves <b>%d of %d</b> retained '
    'nodes&rsquo; <b>point estimates away from the null</b> (median %+.2f%%); %d move the other way '
    '(largest %s %+.2f%%). Identical counts are RR=1.00 on every edge they touch. The majority '
    'direction must <b>not</b> be read as evidence of benefit. This split is <b>counted, not '
    'asserted</b> &mdash; earlier passes claimed <i>every</i> retained node fell, which was never true. '
    '<b>(2)</b> But <b>interval significance falls, it does not rise</b>: on the %d pairs both '
    'fits estimate, CI-excludes-1 goes <b>%d &rarr; %d</b> (%d gain, %d lose), because &tau;&sup2; '
    'rises %.1f%%, I&sup2; goes %.1f%% &rarr; %.1f%%, HKSJ df falls %d &rarr; %d and CIs widen by '
    'a median %+.2f%%. The earlier CARMEN-only fit reported this count <i>rising</i> 12 &rarr; 17; '
    'that was an artefact of an asymmetric quarantine. <b>Neither reading makes the quarantined '
    'fit stronger evidence.</b>'
    '<br><b>Structural cost: no node is lost.</b> Nodes <b>%d &rarr; %d</b>, so all <b>%d</b> '
    'league pairs are estimable in both fits. Edges %d &rarr; %d, cyclomatic %d &rarr; %d. '
    '<b>ICDF unchanged at %d</b>: CARMEN&rsquo;s loop was internal to one study and was never '
    'counted. The surviving between-trial loop is Placebo&ndash;ACEI&ndash;ARB and it exists only '
    'because SPICE was re-sourced rather than quarantined. <b>This is a change from the previous '
    'pass</b>, which withheld GALACTIC-HF and so deleted the +Omecamtiv node (15 &rarr; 14) and '
    '14 league pairs with it; reinstating GALACTIC-HF restores them. Note what did and did not '
    'move: GALACTIC-HF sits on a <b>pendant</b> edge to a leaf node, so it carries no information '
    'about any other contrast &mdash; restoring it recovers a whole treatment comparison while '
    'shifting the other anchors by &lt;1e-7. The structural gain is large; the numerical '
    'perturbation is not. Both are true.'
    '<br><b>SPICE re-tiered, not quarantined:</b> VERIFIED_FULL &rarr; '
    '<b>RECOVERED_FROM_PERCENTAGE_UNIQUE</b>. The source prints no integers, only '
    '&ldquo;death 3.4%% and 3.3%%&rdquo;; 6/179 and 3/91 are the unique integers rounding to those '
    'figures. That is a sound derivation but <b>not a verbatim-reported count</b>, unlike '
    'CIBIS-II or MERIT-HF which print theirs. It stays in the network, fully sourced '
    '(PMID 10740141, DOI 10.1016/s0002-8703(00)90037-1). Labelling only &mdash; no count or fit '
    'changed. Applied symmetrically, the tier also moves US-Carvedilol (unique), EMPHASIS-HF '
    '(non-unique: eplerenone 12.5%% admits both 170 and 171) and ELITE, which raises a '
    '<b>new finding</b> &mdash; captopril 8.7%% over n=370 admits <i>no</i> integer, so its 32 is '
    'not derivable from the published percentage. Not a quarantine trigger; raised for the next gate.'
    '<br><b>Withdrawn as wrong:</b> the audit&rsquo;s claims that SPICE has no primary source '
    '(it is PMID 10740141), that He 2015&rsquo;s per-arm denominators are unverified '
    '(PMC5746969 verifies 19/198 = 11/97 + 8/101 exactly), and that QUEST&rsquo;s counts are '
    'unverified (PMC11333273 states 221 and 262 verbatim).'
    '<br><b>QUEST:</b> the trial&rsquo;s own all-cause-mortality analysis is HR 0.84 '
    '(0.70&ndash;1.01), P=0.058 &mdash; <b>not significant</b>. No QLQX contrast is presented as '
    'significant on the crude 2&times;2 (p=0.0426, fragility index 1).'
    '<br><b>%d of %d</b> CI-excludes-1 contrasts in the full co-primary are purely indirect; '
    'fragility index is <b>undefined</b> for them, not favourable.'
    '<br><b>What was tested:</b> all %d arm rows pass count plausibility and all %d contrasts '
    'recompute logRR/seLogRR from the raw counts to under 1e-8 &mdash; a tested zero, not an '
    'untested one. GRIM/GRIMMER is <b>not applicable</b> (binary outcome, no means), not passed. '
    'Registry concordance covers <b>9 of %d</b> trials; the rest predate ClinicalTrials.gov or are '
    'registered elsewhere, so concordance is <b>N/A</b> &mdash; there is no record to concord '
    'with, and none is claimed. Full text is still absent for 8 denominator-only trials, %d '
    'trials have no sourced mortality at all, and no inconsistency test is fitted. '
    'AMSTAR-2 confidence: <b>CRITICALLY LOW</b>.'
    '</div>'
) % (FU["trials"], FU["arm_rows"], f3(node(FU, "ACEI+BB")["rr"]),
     f3(node(FU, "ACEI+BB+MRA")["rr"]),
     QU["trials"], QU["arm_rows"], f3(node(QU, "ACEI+BB")["rr"]),
     f3(node(QU, "ACEI+BB+MRA")["rr"]),
     len(QUAR),
     f3(node(QU, "ACEI+BB")["rr"]), f3(node(QU, "ACEI+BB+MRA")["rr"]),
     node_away, node_total, node_med, node_toward,
     node_worst["node"], node_worst["pct"],
     common, f_ex, q_ex, n_gain, n_lose,
     100 * (QU["tau2"] / FU["tau2"] - 1), 100 * FU["i2"], 100 * QU["i2"],
     FU["hksj"]["df"], QU["hksj"]["df"], wid_med,
     fst["V"], qst["V"], len(QU["league"]), fst["E"], qst["E"],
     fst["cyclomatic"], qst["cyclomatic"], qst["icdf"],
     indirect_excl, n_excl_full,
     FU["arm_rows"], FU["contrasts"], FU["trials"], len(QUAR))

# Replace the badge's ENTIRE inner content by balanced <div> matching. Partial
# replacement of a surface that states numbers is not safe -- an earlier draft
# left a stale "Trials: 28" row beside a new 27 and the badge contradicted
# itself. The whole surface gets rewritten.
mstart = re.search(r'<div id="rapidmeta-integrity-badge"[^>]*>', html)
if not mstart:
    sys.exit("FAIL: integrity badge not found")
i, depth = mstart.end(), 1
tag = re.compile(r"<(/?)div\b[^>]*>")
while depth:
    t = tag.search(html, i)
    if not t:
        sys.exit("FAIL: unbalanced <div> inside the integrity badge")
    depth += -1 if t.group(1) else 1
    i = t.end()
inner_end = i - len(t.group(0))

html = html[:mstart.end()] + (
    '<div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap;">'
    '<strong style="font-size:14px;letter-spacing:0.04em;">%s</strong>'
    '<span style="font-size:11.5px;">Co-primary: <strong>%d trials (full)</strong> / '
    '<strong>%d trials (quarantined)</strong> &middot; Quarantined: <strong>%d</strong> '
    '&middot; Arithmetic gates: <strong>0 findings</strong> &middot; '
    'Provenance findings: <strong>5 raised, 5 dispositioned, 0 open</strong>'
    '</span></div>%s'
    % (badge_headline, FU["trials"], QU["trials"], len(QUAR), badge_body)
) + html[inner_end:]

open(APP, "w", encoding="utf-8").write(html)
print("app updated: %s (%d -> %d bytes)" % (APP, orig_len, len(html)))
print("  cells rewritten        : %d (full + quarantined each)" % len(full_by_cell))
print("  co-primary (a) FULL    : %d trials, %d arm rows, ACEI+BB %s, ACEI+BB+MRA %s"
      % (FU["trials"], FU["arm_rows"], f3(node(FU, "ACEI+BB")["rr"]),
         f3(node(FU, "ACEI+BB+MRA")["rr"])))
print("  co-primary (b) QUARANT : %d trials, %d arm rows, ACEI+BB %s, ACEI+BB+MRA %s"
      % (QU["trials"], QU["arm_rows"], f3(node(QU, "ACEI+BB")["rr"]),
         f3(node(QU, "ACEI+BB+MRA")["rr"])))
print("  quarantined trials     : %d (%s)"
      % (len(QUAR), ", ".join(sorted(v["trial"] for v in QUAR.values()))))
print("  reinstated trials      : %d (%s)"
      % (len(REINST), ", ".join(sorted(v["trial"] for v in REINST.values()))))
print("  edges                  : %d -> %d (dropped: %s)"
      % (fst["E"], qst["E"], "; ".join(dropped_edges)))
print("  nodes                  : %d -> %d" % (fst["V"], qst["V"]))
print("  CI excludes 1 (common) : %d -> %d (%d gain, %d lose) over %d pairs"
      % (f_ex, q_ex, n_gain, n_lose, common))
print("  ICDF                   : %d -> %d" % (fst["icdf"], qst["icdf"]))
