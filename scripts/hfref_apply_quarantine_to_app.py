#!/usr/bin/env python
"""Apply the CARMEN quarantine + the four re-sourced findings to the HFrEF app.

Reads outputs/hfref_quarantine_primary.json (the R re-fit, anchor-gated) and
rewrites, in HFREF_NMA_AUTO_FULL_REVIEW.html:

  1. script#hfref-fit-data  -- the four embedded cells get their AFTER league
     tables, node rows, tau2, HKSJ and structure; the trial ledger gets the
     corrected identifiers and the quarantine record; nma_config loses the
     edge CARMEN alone supplied.
  2. window.__verdict       -- the machine-readable badge payload.
  3. #rapidmeta-integrity-badge -- the human-readable badge prose.

Both verdict surfaces are written from the SAME derived facts here, so they
cannot drift apart. scripts/hfref_verify_app_coprimary.py re-checks that.
(scripts/hfref_verify_app_quarantine.py was superseded by the co-primary
verifier and removed 2026-07-30 -- it crashed with KeyError 'contrasts_checked'
against the co-primary-era payload.)

Never edits F:/E156/hfref_eightcell_fit.R.
"""
import io
import json
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

APP = "HFREF_NMA_AUTO_FULL_REVIEW.html"
FIT = "outputs/hfref_quarantine_primary.json"
DATE = "2026-07-30"

CARMEN_ID = "HF-021"
CARMEN_VIOLATION = ("no death data in source; 14/14/14 unsourced; "
                    "primary is LVESVI")

fit = json.load(open(FIT, encoding="utf-8"))
if not fit["anchor_before"]["reproduced"]:
    sys.exit("FAIL: re-fit anchor did not reproduce; refusing to touch the app")

after_by_cell = {c["cell_id"]: c["after"] for c in fit["app_cells"]}
before_by_cell = {c["cell_id"]: c["before"] for c in fit["app_cells"]}

html = open(APP, encoding="utf-8").read()
orig_len = len(html)

# ---------------------------------------------------------------- payload ---
m = re.search(r'(<script id="hfref-fit-data" type="application/json">)(.*?)(</script>)',
              html, re.S)
if not m:
    sys.exit("FAIL: script#hfref-fit-data not found")
P = json.loads(m.group(2))

for cell in P["cells"]:
    cid = cell["cell_id"]
    if cid not in after_by_cell:
        continue
    a = after_by_cell[cid]
    b = before_by_cell[cid]
    cell["trials"] = a["trials"]
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
    cell["quarantine_applied"] = [CARMEN_ID]
    cell["before_quarantine"] = {
        "trials": b["trials"], "tau2": b["tau2"],
        "structure": b["structure"],
        "node_vs_placebo": b["node_vs_placebo"],
        "note": ("The pre-quarantine fit, retained so the effect of removing "
                 "CARMEN is inspectable rather than asserted.")}

# ---- anchor: record the move rather than silently restating the old value ---
ps = after_by_cell["OURS-STRICT"]
pb = before_by_cell["OURS-STRICT"]


def node(pack, name):
    return next(n for n in pack["node_vs_placebo"] if n["node"] == name)


P["anchor"] = {
    "passed": True,
    "gate": ("The pre-quarantine re-fit reproduces the settled primary to <1e-8 "
             "on both anchor nodes and on tau^2; only then is the quarantined "
             "fit emitted. See scripts/hfref_quarantine_primary.R."),
    "before_quarantine": {
        "ACEI+BB": [node(pb, "ACEI+BB")["rr"], node(pb, "ACEI+BB")["lo"],
                    node(pb, "ACEI+BB")["hi"]],
        "ACEI+BB+MRA": [node(pb, "ACEI+BB+MRA")["rr"], node(pb, "ACEI+BB+MRA")["lo"],
                        node(pb, "ACEI+BB+MRA")["hi"]],
        "tau2": pb["tau2"]},
    "after_quarantine": {
        "ACEI+BB": [node(ps, "ACEI+BB")["rr"], node(ps, "ACEI+BB")["lo"],
                    node(ps, "ACEI+BB")["hi"]],
        "ACEI+BB+MRA": [node(ps, "ACEI+BB+MRA")["rr"], node(ps, "ACEI+BB+MRA")["lo"],
                        node(ps, "ACEI+BB+MRA")["hi"]],
        "tau2": ps["tau2"]}}

# ---- top-level quarantine record -------------------------------------------
P["quarantine"] = {
    "date": DATE,
    "principle": ("Quarantine, never silent deletion. Every withheld "
                  "contribution carries a NAMED violation and its arm rows stay "
                  "on record in outputs/hfref_quarantine_ledger.json."),
    "withheld": [{
        "id": CARMEN_ID, "trial": "CARMEN", "violation": CARMEN_VIOLATION,
        "source": "PMID 15115904 (Cardiovasc Drugs Ther 2004;18:57-66)",
        "detail": ("The publication confirms the three arms exactly "
                   "(191/190/191) but its primary endpoint is left-ventricular "
                   "end-systolic volume index and it reports NO per-arm death "
                   "counts. The ledger carried an identical 14 deaths in all "
                   "three arms, for which no source could be located. The "
                   "settled fit script's own line 377 already annotated CARMEN "
                   "inadmissible."),
        "withheld_rows": [
            {"treat": "ACEI", "events": 14, "n": 190},
            {"treat": "ACEI+BB", "events": 14, "n": 191},
            {"treat": "BB", "events": 14, "n": 191}],
        "reinstatement_condition": (
            "Locate a primary or CARMEN-authored secondary report stating "
            "per-arm all-cause deaths.")}],
    "considered_and_NOT_withheld": [
        {"id": "HF-008", "trial": "SPICE",
         "why": ("The audit proposed quarantine for 'no primary source'. That "
                 "claim is withdrawn: the primary is PMID 10740141 (Granger, "
                 "Am Heart J 2000;139:609-17). SPICE = Study of Patients "
                 "Intolerant of Converting Enzyme inhibitors; the acronym is "
                 "absent from the PubMed record, which is why an acronym-keyed "
                 "search missed it. n=179 candesartan / n=91 placebo = 270 "
                 "exact, and 'death 3.4% and 3.3%' recovers 6/179 and 3/91 "
                 "exactly."),
         "consequence_of_retaining_it": (
             "SPICE alone supplies the Placebo-ARB edge, which is the only "
             "between-trial loop in the network. Branches 7b/7c, which drop "
             "SPICE, both have ICDF 0. Retaining SPICE is what keeps ICDF at 1.")},
        {"id": "HF-020", "trial": "He 2015",
         "why": ("The audit recorded the per-arm denominators as unverified. "
                 "PMC5746969 Table 1 gives the five arm sizes and Table 2 the "
                 "per-arm all-cause deaths: the ledger's 19/198 is exactly "
                 "11/97 + 8/101, and 14/96 matches. Verified, not withheld.")},
        {"id": "HF-038", "trial": "QUEST",
         "why": ("Counts verified verbatim in PMC11333273 (221 and 262). The "
                 "finding is a presentation constraint, not a data error.")}],
    "ledger": "outputs/hfref_quarantine_ledger.json",
    "refit": "outputs/hfref_quarantine_primary.json",
    "report": "outputs/HFREF_INTEGRITY_GATES_2026-07-30.md"}

# ---- trial ledger: corrected identifiers + quarantine flag ------------------
FIXES = {
    "HF-008": dict(
        pmid="10740141", doi="10.1016/s0002-8703(00)90037-1",
        pmid_note=("RESOLVED 2026-07-30: the audit recorded SPICE as having no "
                   "primary source. It has one. Granger CB et al, Am Heart J "
                   "2000;139(4):609-17 = SPICE (Study of Patients Intolerant of "
                   "Converting Enzyme inhibitors). Abstract: 'randomization in "
                   "a 2:1 ratio to receive candesartan (n = 179) or a placebo "
                   "(n = 91)' and 'death 3.4% and 3.3%'. 6/179 = 3.35% and "
                   "3/91 = 3.30% recover the ledger exactly.")),
    "HF-019": dict(
        pmid="10653828", doi="10.1161/01.cir.101.4.378",
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

n_quar = 0
for t in P["trials"]:
    tid = t.get("id")
    if tid in FIXES:
        t.update(FIXES[tid])
    if tid == CARMEN_ID:
        t["quarantined"] = True
        t["quarantine_violation"] = CARMEN_VIOLATION
        t["in_network"] = False
        t["pmid_note"] = (
            "QUARANTINED 2026-07-30. PMID 15115904 confirms the arms "
            "(carvedilol N=191, enalapril N=190, combination N=191) but the "
            "trial's primary endpoint is LVESVI and it reports NO deaths. The "
            "14/14/14 the ledger carried has no located source, and the "
            "settled fit script's line 377 already called CARMEN inadmissible. "
            "Its mortality contribution is withheld from every cell except the "
            "calibration cell, which must keep its inputs to remain a "
            "reproducibility check. Rows retained, not deleted: see "
            "outputs/hfref_quarantine_ledger.json.")
        n_quar += 1
    else:
        t.setdefault("quarantined", False)
        t.setdefault("in_network", True)
if n_quar != 1:
    sys.exit("FAIL: expected exactly one quarantined trial, found %d" % n_quar)

# ---- nma_config: drop the edge CARMEN alone supplied -----------------------
newcmp = []
for c in P["nma_config"]["comparisons"]:
    trials = [x for x in c["trials"] if x != "CARMEN"]
    if not trials:
        continue                      # ACEI+BB vs BB -- CARMEN was its only trial
    c["trials"] = trials
    newcmp.append(c)
P["nma_config"]["comparisons"] = newcmp

st = ps["structure"]
P["nma_config"]["note"] = (
    "%d RCTs, %d GDMT nodes, %d direct edges, cyclomatic number %d and ICDF %d. "
    "CARMEN's mortality contribution is QUARANTINED (%s), which removes the "
    "ACEI+BB vs BB edge and the network's only multi-arm trial. ICDF is "
    "UNCHANGED at %d: the loop CARMEN closed lay entirely inside a single "
    "study, and the ICDF definition already excluded such loops because they "
    "carry no between-trial inconsistency information. The one between-trial "
    "loop that remains is Placebo-ACEI-ARB, and it survives only because SPICE "
    "was re-sourced rather than quarantined. Random-effects GLS network fit, "
    "log-RR scale, REML tau^2, HKSJ variance inflation with the mandatory "
    "max(1,.) floor and a t_df critical value."
) % (ps["trials"], st["V"], st["E"], st["cyclomatic"], st["icdf"],
     CARMEN_VIOLATION, st["icdf"])

P["coverage"] = {
    "network_trials": ps["trials"],
    "trials_on_record": len(P["trials"]),
    "quarantined": 1,
    "extraction_substantiated": ps["trials"],
    "arm_rows": 54,
    "study_contrasts": ps["contrasts"],
    "pmid_verified": ps["trials"],
    "pmid_missing": 0,
    "note": ("57 arm rows and 30 contrasts before the quarantine; CARMEN's 3 "
             "arms and 3 contrasts are withheld. Every trial remaining in the "
             "network now carries a PMID: SPICE's was located this pass.")}

P["fit_source"] = (
    "F:/E156/hfref_eightcell_fit.R (lines 1-587 only, never its RUN or EMIT "
    "sections), re-executed with the CARMEN quarantine applied and expanded to "
    "all 105 pairwise contrasts by scripts/hfref_quarantine_primary.R. "
    "Anchor-gated: the pre-quarantine fit must reproduce the settled primary "
    "to <1e-8 before the quarantined fit is emitted.")

html = html[:m.start(2)] + json.dumps(P, ensure_ascii=False) + html[m.end(2):]

# ---------------------------------------------------------------- verdict ---
n_excl = ps["counts"]["ci_excludes_null"]
n_excl_before = pb["counts"]["ci_excludes_null"]
indirect_excl = sum(1 for p in ps["league"]
                    if (p["lo"] > 1 or p["hi"] < 1) and p["direct_k"] == 0)

verdict = {
    "verdict": "UNCERTAIN",
    "counts": {
        "P0_internal": 0, "P0_aact_nct_missing": 0, "P0_grim": 0,
        "P1_aact_concord": 0, "P1_fi_critical": 0, "P1_fi_warn": 0,
        "P1_pi_gap": 0, "P2_evidence_incomplete": 0, "P2_aact_advisory": 0,
        "n_trials_seen": ps["trials"],
        "trials_on_record": len(P["trials"]),
        "gates_executed_date": DATE,
        "findings_raised": 5, "findings_resolved": 5, "findings_open": 0,
        "trials_quarantined": 1,
        "audit_claims_withdrawn": 3,
        "count_values_changed": 0,
        "arm_rows_checked": 54, "contrasts_checked": ps["contrasts"],
        "source_verified_full": 19,
        "source_verified_denominator_only": 8,
        "registry_concordance_applicable": 9,
        "registry_concordance_not_applicable": 18,
        "grim_applicable": False,
        "nma_ci_excludes_1": n_excl,
        "nma_ci_excludes_1_before_quarantine": n_excl_before,
        "nma_ci_excludes_1_purely_indirect": indirect_excl,
        "icdf_before": pb["structure"]["icdf"], "icdf_after": st["icdf"]},
    "reasons": [
        ("All five provenance findings raised on %s are now DISPOSITIONED. "
         "Four resolved to 'the extraction was right, the provenance record was "
         "wrong'; one (CARMEN) resolved to 'the extraction has no source' and "
         "was quarantined. No extracted count was altered." % DATE),
        ("QUARANTINED: CARMEN. Named violation - %s. Its arm rows are retained "
         "in outputs/hfref_quarantine_ledger.json with a stated reinstatement "
         "condition; they are withheld from the fit, not deleted." % CARMEN_VIOLATION),
        ("THREE AUDIT CLAIMS ARE WITHDRAWN AS WRONG. SPICE was reported to have "
         "no primary source: it has one, PMID 10740141, and its counts recover "
         "exactly. He 2015's per-arm denominators were reported unverified: "
         "PMC5746969 Tables 1 and 2 verify them exactly (19/198 = 11/97 + "
         "8/101). QUEST's counts were reported unverified: PMC11333273 states "
         "221 and 262 verbatim."),
        ("RESOLVD's citation is corrected to PMID 10653828. The 3.4%-vs-3.7% "
         "residual resolves as an inconsistency INTERNAL TO THE SOURCE - the "
         "body text reports n=8 (3.7%) against the abstract's 3.4% - and the "
         "extracted counts match the body. The publisher blocks automated "
         "retrieval and that was not circumvented, so the body figures are "
         "labelled SECONDARY_CORROBORATED rather than claimed as a direct read."),
        ("QUEST remains a live PRESENTATION constraint. The trial's own "
         "all-cause-mortality analysis is HR 0.84 (95% CI 0.70-1.01), P=0.058 - "
         "NOT significant. Fisher's exact on the crude 2x2 gives p=0.0426 with "
         "a fragility index of 1. The trial's reported analysis is "
         "authoritative; no QLQX contrast is presented as significant on the "
         "crude 2x2."),
        ("STRUCTURE: removing CARMEN drops the ACEI+BB vs BB edge and the "
         "cyclomatic number from %d to %d, but ICDF is UNCHANGED at %d. "
         "CARMEN's loop lay entirely inside one study and the ICDF definition "
         "already excluded it. The surviving between-trial loop is "
         "Placebo-ACEI-ARB, which exists only because SPICE was re-sourced "
         "instead of quarantined - branches 7b/7c, which drop SPICE, have ICDF "
         "0." % (pb["structure"]["cyclomatic"], st["cyclomatic"], st["icdf"])),
        ("THE QUARANTINE MOVED THE HEADLINE NUMBERS AWAY FROM THE NULL, AND "
         "THAT IS NOT A RESULT THAT GOT BETTER. CARMEN's identical 14/14/14 "
         "was RR=1.00 on every edge it touched, so withdrawing it removes a "
         "null-pulling weight: ACEI+BB %.3f to %.3f and ACEI+BB+MRA %.3f to "
         "%.3f, and the count of contrasts whose CI excludes 1 rises from %d to "
         "%d. The change is a provenance correction, not evidence of benefit."
         % (node(pb, "ACEI+BB")["rr"], node(ps, "ACEI+BB")["rr"],
            node(pb, "ACEI+BB+MRA")["rr"], node(ps, "ACEI+BB+MRA")["rr"],
            n_excl_before, n_excl)),
        ("%d of the %d contrasts whose CI excludes 1 are PURELY INDIRECT. The "
         "Walsh fragility index is defined on an observed 2x2 table; an "
         "indirect estimate has none. No fragility index is quoted for them, "
         "and their fragility is not merely unfavourable - it is unmeasurable "
         "by that method." % (indirect_excl, n_excl)),
        ("Arithmetic remains clean and this is a tested zero: all 54 remaining "
         "arm rows pass count plausibility and all %d contrasts recompute "
         "logRR and seLogRR from the raw counts to under 1e-8. GRIM/GRIMMER is "
         "NOT APPLICABLE (binary outcome, no means), not passed." % ps["contrasts"]),
        ("Registry concordance still covers only 9 of the %d trials in the "
         "network; the rest predate ClinicalTrials.gov or are registered "
         "elsewhere, so concordance is N/A - there is no record to concord "
         "with. No concordance is claimed for them." % ps["trials"]),
        ("VERDICT STAYS UNCERTAIN. Dispositioning the findings did not earn a "
         "PASS. Full-text verification is still absent for 8 denominator-only "
         "trials, no inconsistency test is fitted, and AMSTAR-2 confidence "
         "remains CRITICALLY LOW."),
    ],
}

mv = re.search(r'(<script>window\.__verdict = )(\{.*?\})(;?\s*</script>)', html, re.S)
if not mv:
    sys.exit("FAIL: window.__verdict block not found")
html = html[:mv.start(2)] + json.dumps(verdict, ensure_ascii=False) + html[mv.end(2):]

# ------------------------------------------------------------ badge prose ---
def f3(x):
    return ("%.3f" % x)


badge_headline = "VERDICT: UNCERTAIN &mdash; 5 FINDINGS DISPOSITIONED, 1 TRIAL QUARANTINED"
badge_body = (
    '<div style="margin-top:8px;font-size:12.5px;line-height:1.6;">'
    '<b>Network:</b> %d trials (CARMEN quarantined) &middot; '
    '<b>Arithmetic gates:</b> 0 findings on 54 arm rows / %d contrasts &middot; '
    '<b>Provenance findings:</b> 5 raised, 5 dispositioned, 0 open &middot; '
    '<b>Counts changed:</b> 0'
    '<br><b>Quarantined:</b> CARMEN &mdash; <i>%s</i>. '
    'Arm rows retained in <code>outputs/hfref_quarantine_ledger.json</code>, not deleted.'
    '<br><b>Withdrawn as wrong:</b> the audit&rsquo;s claims that SPICE has no primary source '
    '(it is PMID 10740141), that He 2015&rsquo;s per-arm denominators are unverified '
    '(PMC5746969 verifies 19/198 = 11/97 + 8/101 exactly), and that QUEST&rsquo;s counts are '
    'unverified (PMC11333273 states 221 and 262 verbatim).'
    '<br><b>Anchor moved:</b> ACEI+BB %s &rarr; %s &middot; ACEI+BB+MRA %s &rarr; %s. '
    'CARMEN&rsquo;s identical 14/14/14 was RR=1.00 on every edge, so removing it moves '
    'estimates AWAY from the null and CI-excludes-1 rises %d &rarr; %d. '
    'That is a provenance correction, <b>not</b> a result that got better.'
    '<br><b>Structure:</b> cyclomatic %d &rarr; %d, but <b>ICDF unchanged at %d</b> &mdash; '
    'CARMEN&rsquo;s loop was internal to one study and was never counted. The surviving '
    'between-trial loop is Placebo&ndash;ACEI&ndash;ARB and it exists only because SPICE was '
    're-sourced rather than quarantined.'
    '<br><b>QUEST:</b> the trial&rsquo;s own all-cause-mortality analysis is HR 0.84 '
    '(0.70&ndash;1.01), P=0.058 &mdash; <b>not significant</b>. No QLQX contrast is presented as '
    'significant on the crude 2&times;2 (p=0.0426, fragility index 1).'
    '<br><b>%d of %d</b> CI-excludes-1 contrasts are purely indirect; fragility index is '
    '<b>undefined</b> for them, not favourable.'
    '<br><b>What was tested:</b> all 54 remaining arm rows pass count plausibility and all '
    '%d contrasts recompute logRR/seLogRR from the raw counts to under 1e-8 &mdash; a tested '
    'zero, not an untested one. GRIM/GRIMMER is <b>not applicable</b> (binary outcome, no '
    'means), not passed. Registry concordance covers <b>9 of %d</b> trials; the rest predate '
    'ClinicalTrials.gov or are registered elsewhere, so concordance is <b>N/A</b> &mdash; '
    'there is no record to concord with, and none is claimed. Full text is still absent for '
    '8 denominator-only trials and no inconsistency test is fitted. '
    'AMSTAR-2 confidence: <b>CRITICALLY LOW</b>.'
    '</div>'
) % (ps["trials"], ps["contrasts"], CARMEN_VIOLATION,
     f3(node(pb, "ACEI+BB")["rr"]), f3(node(ps, "ACEI+BB")["rr"]),
     f3(node(pb, "ACEI+BB+MRA")["rr"]), f3(node(ps, "ACEI+BB+MRA")["rr"]),
     n_excl_before, n_excl,
     pb["structure"]["cyclomatic"], st["cyclomatic"], st["icdf"],
     indirect_excl, n_excl, ps["contrasts"], ps["trials"])

# Replace the badge's ENTIRE inner content, found by balanced <div> matching.
# An earlier draft only swapped the headline and appended the new body, which
# left the previous stats row ("Trials: 28") and a trailing paragraph ("all 57
# arm rows") in place -- so the badge asserted both 28 and 27 trials at once.
# Rendering the page is what exposed it. Partial replacement of a surface that
# states numbers is not safe; the whole surface gets rewritten.
mstart = re.search(r'<div id="rapidmeta-integrity-badge"[^>]*>', html)
if not mstart:
    sys.exit("FAIL: integrity badge not found")
i = mstart.end()
depth = 1
tag = re.compile(r"<(/?)div\b[^>]*>")
while depth:
    t = tag.search(html, i)
    if not t:
        sys.exit("FAIL: unbalanced <div> inside the integrity badge")
    depth += -1 if t.group(1) else 1
    i = t.end()
inner_end = i - len(t.group(0))     # offset of the badge's closing </div>

html = html[:mstart.end()] + (
    '<div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap;">'
    '<strong style="font-size:14px;letter-spacing:0.04em;">%s</strong>'
    '<span style="font-size:11.5px;">Network: <strong>%d trials</strong> &middot; '
    'Quarantined: <strong>1</strong> &middot; Arithmetic gates: <strong>0 findings</strong> '
    '&middot; Provenance findings: <strong>5 raised, 5 dispositioned, 0 open</strong>'
    '</span></div>%s'
    % (badge_headline, ps["trials"], badge_body)) + html[inner_end:]

open(APP, "w", encoding="utf-8").write(html)
print("app updated: %s (%d -> %d bytes)" % (APP, orig_len, len(html)))
print("  cells rewritten     : %d" % len(after_by_cell))
print("  primary trials      : %d -> %d" % (pb["trials"], ps["trials"]))
print("  ACEI+BB             : %s -> %s" % (f3(node(pb, "ACEI+BB")["rr"]),
                                            f3(node(ps, "ACEI+BB")["rr"])))
print("  ACEI+BB+MRA         : %s -> %s" % (f3(node(pb, "ACEI+BB+MRA")["rr"]),
                                            f3(node(ps, "ACEI+BB+MRA")["rr"])))
print("  CI excludes 1       : %d -> %d (%d purely indirect)" % (n_excl_before, n_excl, indirect_excl))
print("  ICDF                : %d -> %d" % (pb["structure"]["icdf"], st["icdf"]))
