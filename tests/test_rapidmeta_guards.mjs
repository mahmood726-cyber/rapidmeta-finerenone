/**
 * Unit tests for assets/js/rapidmeta-guards.js
 *
 * Every BLOCK case below is seeded with the ACTUAL value that shipped in the corpus, cited to the
 * artifact that recorded it. A test that passes on invented data proves nothing; these fail if the
 * guard would have let the real defect through.
 *
 * Run:  node --test tests/test_rapidmeta_guards.mjs
 */
import { test, describe } from "node:test";
import assert from "node:assert/strict";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const G = require("../assets/js/rapidmeta-guards.js");

/** Assert fn throws a GuardBlock, optionally with a given code. */
function blocks(fn, code) {
  let thrown = null;
  try { fn(); } catch (e) { thrown = e; }
  assert.ok(thrown, "expected a GuardBlock, got none");
  assert.equal(thrown.name, "GuardBlock", `expected GuardBlock, got ${thrown.name}: ${thrown.message}`);
  if (code) assert.equal(thrown.code, code, `expected code ${code}, got ${thrown.code} (${thrown.message})`);
  return thrown;
}

/* ================================================================= core */

describe("core — fail-closed primitives", () => {
  test("isPresent treats 0 as a value and null/''/NaN as unknown", () => {
    assert.equal(G.isPresent(0), true);
    assert.equal(G.isPresent(null), false);
    assert.equal(G.isPresent(undefined), false);
    assert.equal(G.isPresent(""), false);
    assert.equal(G.isPresent(NaN), false);
  });

  test("resolveEstimand does NOT default to HR — the RM-A02 denylist bug", () => {
    blocks(() => G.resolveEstimand(undefined), "ESTIMAND_MISSING");
    blocks(() => G.resolveEstimand("something else"), "ESTIMAND_UNKNOWN");
    assert.equal(G.resolveEstimand("rate ratio"), "RATE_RATIO");
    assert.equal(G.resolveEstimand("HR"), "HR");
  });

  test("attempt() converts a block into a value instead of throwing", () => {
    const r = G.attempt(() => G.resolveEstimand(null));
    assert.equal(r.ok, false);
    assert.equal(r.block.code, "ESTIMAND_MISSING");
  });
});

/* ================================================= G01 continuous / ratio */

describe("G01 — a continuous or non-ratio estimate can never enter an HR/OR/RR model", () => {
  test("PASS: PARADIGM-HF hazard ratio into an HR model", () => {
    const r = G.G01_assertRatioModelInput(
      { estimandType: "HR", effect: 0.80, lci: 0.73, uci: 0.87 }, "HR");
    assert.equal(r.ok, true);
  });

  test("BLOCK: PARAGON-HF recurrent-event RATE RATIO 0.87 into a hazard-ratio model [ARNI c641f552f]", () => {
    blocks(() => G.G01_assertRatioModelInput(
      { estimandType: "RATE_RATIO", effect: 0.87, lci: 0.75, uci: 1.01 }, "HR"),
      "ESTIMAND_NOT_ADMISSIBLE");
  });

  test("BLOCK: PARAGLIDE-HF continuous ratio-of-change 0.85 into a ratio model [ARNI d906ba931]", () => {
    blocks(() => G.G01_assertRatioModelInput(
      { estimandType: "RATIO_CONTINUOUS", effect: 0.85, lci: 0.73, uci: 0.999 }, "HR"),
      "ESTIMAND_NOT_ADMISSIBLE");
  });

  test("BLOCK: HEART-FID win ratio paired with a ratio model [IRON §3]", () => {
    blocks(() => G.G01_assertRatioModelInput({ estimandType: "WIN_RATIO", effect: 1.10 }, "HR"),
      "ESTIMAND_NOT_ADMISSIBLE");
  });

  test("BLOCK: pubHR 73.83 — a percent change in a hazard-ratio field [CARDIO-MIS §1 F1]", () => {
    blocks(() => G.G01_assertRatioModelInput(
      { estimandType: "HR", publishedHR: 73.83, hrLCI: 65.15, hrUCI: 82.51,
        title: "Efficacy: Percent Change From Baseline in Anti-fXa Activity at the Nadir" }, "HR"),
      "RATIO_FIELD_IMPLAUSIBLE");
  });

  test("BLOCK: a NEGATIVE confidence bound (-0.5509) is structurally impossible for a ratio [CARDIO-MIS §1 F1]", () => {
    blocks(() => G.G01_assertRatioModelInput(
      { estimandType: "HR", publishedHR: 0.80, hrLCI: -0.5509, hrUCI: 2.1509 }, "HR"),
      "RATIO_FIELD_NON_POSITIVE");
  });

  test("BLOCK: a change-from-baseline title with a populated HR field", () => {
    blocks(() => G.G01_assertRatioModelInput(
      { estimandType: "HR", publishedHR: 1.02, title: "Percent Change From Baseline In Anti-fXa Activity" }, "HR"),
      "CHANGE_SCORE_IN_RATIO_FIELD");
  });

  test("BLOCK: the model itself is not a ratio model", () => {
    blocks(() => G.G01_assertRatioModelInput({ estimandType: "HR", effect: 0.8 }, "MD"), "MODEL_NOT_RATIO");
  });
});

/* ============================================================ G02 Peto */

describe("G02 — Peto output is labelled OR, never HR", () => {
  test("PASS: Peto forced to OR", () => {
    const r = G.G02_labelForEstimator("peto");
    assert.equal(r.measure, "OR");
    assert.equal(r.forced, true);
    assert.match(r.caveat, /biased at large effects/);
  });

  test("BLOCK: 'Peto HR' is a contradiction [BUG-CAT guard 2]", () => {
    blocks(() => G.G02_labelForEstimator("peto", "HR"), "ESTIMATOR_MEASURE_MISLABEL");
  });

  test("BLOCK: an unknown estimator fails closed", () => {
    blocks(() => G.G02_labelForEstimator("vibes"), "ESTIMATOR_UNKNOWN");
  });

  test("PASS: a scale-agnostic estimator keeps the caller's measure", () => {
    assert.equal(G.G02_labelForEstimator("reml", "HR").measure, "HR");
  });
});

/* ================================================== G03 / G07 scope lock */

describe("G03 / G07 — no silent endpoint fallback, no stale state", () => {
  const heartFid = {
    name: "HEART-FID",
    allOutcomes: [
      { shortLabel: "WIN", scopeClass: "hierarchical_composite", unit: "hierarchical",
        estimandType: "WIN_RATIO", effect: 1.10, lci: 0.99, uci: 1.23 },
      { shortLabel: "ACM", scopeClass: "all_cause_mortality", unit: "patients",
        estimandType: "RR", tE: 131, tN: 1532, cE: 158, cN: 1533 }
    ]
  };
  const ironman = {
    name: "IRONMAN",
    allOutcomes: [
      { shortLabel: "RECUR", scopeClass: "cvdeath_hfhosp_recurrent", unit: "events",
        estimandType: "RATE_RATIO", effect: 0.82, lci: 0.66, uci: 1.02 }
    ]
  };

  test("PASS: a matching scope binds its own row", () => {
    const r = G.G03_resolveOutcomeScope(heartFid, "all_cause_mortality");
    assert.equal(r.ok, true);
    assert.equal(r.row.tE, 131);
  });

  test("BLOCK-not-substitute: IRONMAN has no mortality row → excluded with a reason [IRON §3]", () => {
    const r = G.G03_resolveOutcomeScope(ironman, "all_cause_mortality");
    assert.equal(r.blocked, true);
    assert.equal(r.row, null);
    assert.equal(r.reason, "not available for this outcome");
  });

  test("BLOCK: there is no 'default' endpoint — the modal-title bug [IRON §1 Defect 1]", () => {
    blocks(() => G.G03_resolveOutcomeScope(heartFid, null), "SCOPE_MISSING");
  });

  test("applyOutcomeScope CLEARS every scoped field — no ?? fallback survives [IRON §1 Defect 2]", () => {
    const trial = Object.assign({}, ironman, {
      data: { tE: 336, tN: 569, cE: 411, cN: 568, effect: 0.82, keepMe: "trial-level" }
    });
    const out = G.G07_applyOutcomeScope(trial, "all_cause_mortality");
    assert.equal(out.included, false);
    assert.equal(out.data.tE, null, "the previous endpoint's 336 must not survive");
    assert.equal(out.data.tN, null, "the composite's denominator 569 must not survive");
    assert.equal(out.data.effect, null);
    assert.equal(out.data.keepMe, "trial-level", "non-scoped fields are preserved");
  });

  test("percentages are computed only for unit='patients' [RM-A01]", () => {
    const t = Object.assign({}, heartFid, { data: {} });
    assert.equal(G.G07_applyOutcomeScope(t, "all_cause_mortality").data.percentagesValid, true);
    assert.equal(G.G07_applyOutcomeScope(t, "hierarchical_composite").data.percentagesValid, false);
    const ir = Object.assign({}, ironman, { data: {} });
    assert.equal(G.G07_applyOutcomeScope(ir, "cvdeath_hfhosp_recurrent").data.percentagesValid, false,
      "336 vs 411 are TOTAL RECURRENT EVENTS; a percentage of the randomised n is not a risk");
  });

  test("BLOCK: an untyped outcome row", () => {
    blocks(() => G.G03_resolveOutcomeScope(
      { allOutcomes: [{ shortLabel: "acm" }] }, "acm"), "ROW_UNTYPED");
  });
});

/* ======================================== G04 component counts vs composite */

describe("G04 — component counts cannot pair with a composite effect", () => {
  test("PASS: counts and effect resolve to the same outcome key", () => {
    const r = G.G04_assertCountsMatchEffect({
      shortLabel: "MACE", tE: 386, tN: 2373, cE: 502, cN: 2371, effect: 0.74
    });
    assert.equal(r.checked, true);
  });

  test("BLOCK: SUMMIT-style worsening-HF counts beside a composite HR [BUG-CAT guard 4]", () => {
    blocks(() => G.G04_assertCountsMatchEffect({
      countOutcomeKey: "worsening_hf_alone", effectOutcomeKey: "cvdeath_or_worsening_hf",
      tE: 29, tN: 52, cE: 40, cN: 52, effect: 0.62
    }), "COUNT_EFFECT_KEY_MISMATCH");
  });

  test("BLOCK: APPRAISE-2 carries HR 0.95 beside counts giving RR 1.058 [APIXABAN §3 G8]", () => {
    blocks(() => G.G04_assertCountsMatchEffect({
      shortLabel: "ischaemic", tE: 515, tN: 3687, cE: 489, cN: 3705, effect: 0.95
    }), "DIRECTION_CONTRADICTION");
  });

  test("BLOCK: events exceed the denominator", () => {
    blocks(() => G.G04_assertCountsMatchEffect({
      shortLabel: "x", tE: 60, tN: 52, cE: 10, cN: 52, effect: 1.2
    }), "EVENTS_EXCEED_DENOMINATOR");
  });
});

/* ================================================ G05 missing is NA, not 0 */

describe("G05 — missing renders NA, never 0", () => {
  test("naOrNumber: null/''/NaN → NA; 0 stays 0", () => {
    assert.equal(G.G05_naOrNumber(null), G.NA);
    assert.equal(G.G05_naOrNumber(""), G.NA);
    assert.equal(G.G05_naOrNumber(NaN), G.NA);
    assert.equal(G.G05_naOrNumber(0), 0);
  });

  test("PARAGON-HF null numerator renders NA, not '0.0%' [ARNI ea1a8fea1]", () => {
    assert.equal(G.G05_renderPercent(null, 2407), "NA");
    assert.equal(G.G05_renderPercent(526, 2407), "21.9%");
  });

  test("the wrong first fix — Number.isFinite(Number(null)) — would have accepted null", () => {
    assert.equal(Number.isFinite(Number(null)), true, "documents why that idiom is unsafe");
    assert.equal(G.isPresent(null), false, "the guard rejects it");
  });

  test("an unrecorded PRISMA stage renders 'not recorded', never 0 [ARNI ea1a8fea1]", () => {
    assert.equal(G.G05_renderPrismaStage(null), "not recorded");
    assert.equal(G.G05_renderPrismaStage(0), "0");
  });

  test("BLOCK: 0 identified with trials included is an impossible PRISMA flow", () => {
    blocks(() => G.G05_assertPrismaCoherent({ identified: 0, screened: 0, eligible: 0, included: 4 }),
      "PRISMA_IMPOSSIBLE");
  });

  test("BLOCK: a downstream PRISMA stage exceeding an upstream one", () => {
    blocks(() => G.G05_assertPrismaCoherent({ identified: 100, screened: 120 }), "PRISMA_STAGE_INCREASES");
  });

  test("BLOCK: PARAGLIDE-HF 466 randomised vs 377 analysed with no stated reason [ARNI b0dbdd1ed]", () => {
    blocks(() => G.G05_assertDenominatorLabelled({ nRandomised: 466, nAnalysed: 377 }), "ATTRITION_UNEXPLAINED");
    const ok = G.G05_assertDenominatorLabelled({
      nRandomised: 466, nAnalysed: 377, attritionReason: "primary NT-proBNP analysis set (180 + 197)"
    });
    assert.equal(ok.ok, true);
  });

  test("BLOCK: an unlabelled denominator", () => {
    blocks(() => G.G05_assertDenominatorLabelled({ n: 466 }), "DENOMINATOR_UNLABELLED");
  });
});

/* ================================================= G06 same-estimand pooling */

describe("G06 — no analysis below 2 same-estimand estimates", () => {
  const arni = [
    { name: "PARADIGM-HF", estimandType: "HR" },
    { name: "PARADISE-MI", estimandType: "HR" },
    { name: "PARAGON-HF", estimandType: "RATE_RATIO" },
    { name: "PARAGLIDE-HF", estimandType: "RATIO_CONTINUOUS" }
  ];

  test("PASS: the HR stratum has k=2 and the rest are named as held out [ARNI c641f552f]", () => {
    const r = G.G06_assertPoolable(arni, { pooledEstimand: "HR" });
    assert.equal(r.k, 2);
    assert.deepEqual(r.heldOut.map(h => h.estimand).sort(), ["RATE_RATIO", "RATIO_CONTINUOUS"]);
  });

  test("BLOCK: asking for a stratum with k=1", () => {
    blocks(() => G.G06_assertPoolable(arni, { pooledEstimand: "RATE_RATIO" }), "REQUESTED_STRATUM_NOT_POOLABLE");
  });

  test("BLOCK: an untagged trial fails closed rather than defaulting to HR", () => {
    blocks(() => G.G06_assertPoolable([{ name: "A", estimandType: "HR" }, { name: "B" }]), "ESTIMAND_MISSING");
  });

  test("BLOCK: no stratum reaches k=2 — the ARNI Tier-1 state, pooled synthesis k=0 [ARNI 554b6f2a2]", () => {
    blocks(() => G.G06_assertPoolable([
      { name: "PARADIGM-HF", estimandType: "HR" },
      { name: "PARAGON-HF", estimandType: "RATE_RATIO" },
      { name: "PARAGLIDE-HF", estimandType: "RATIO_CONTINUOUS" }
    ]), "NO_POOLABLE_STRATUM");
  });
});

/* ========================================================== G08 safeRob */

describe("G08 — safeRob resolves unknowns to 'some', never 'low'", () => {
  test("BLOCK-equivalent: 'some-concerns' no longer becomes 'low' [IRON §4(1), BUG-CAT #2]", () => {
    const shipped = rob => rob.map(r => ["low", "some", "high"].includes(r) ? r : "low"); // the bug
    assert.deepEqual(shipped(["some-concerns", "some-concerns"]), ["low", "low"], "documents the shipped behaviour");
    assert.deepEqual(G.G08_safeRob(["some-concerns", "some-concerns"]), ["some", "some"]);
  });

  test("every alias maps to the right level", () => {
    assert.deepEqual(
      G.G08_safeRob(["low", "some concerns", "unclear", "moderate", "serious", "critical", "WAT", null]),
      ["low", "some", "some", "some", "high", "high", "some", "some"]);
  });

  test("a non-array resolves to all-'some', not all-'low'", () => {
    assert.deepEqual(G.G08_safeRob(undefined), ["some", "some", "some", "some", "some"]);
  });

  test("HEART-FID renders 'Some concerns', not 'Low risk' [IRON §4(1)]", () => {
    assert.equal(G.G08_overallRob(["some-concerns", "low", "low", "low", "low"]), "some");
  });

  test("RoB with no stored domain answers renders 'not assessed' [ARNI ea1a8fea1]", () => {
    const r = G.G08_assertRobAssessed({ design: "randomised, double-blind" });
    assert.equal(r.ok, false);
    assert.equal(r.render, "not assessed");
  });
});

/* ============================================== G09 registry concordance */

describe("G09 — registry concordance", () => {
  const topic = ["latent tuberculosis"];

  test("PASS: iAdhere concords with its LTBI record", () => {
    const r = G.G09_assertRegistryConcordance(
      { nct: "NCT01582711", name: "iAdhere", phase: "III" },
      { briefTitle: "iAdhere: Adherence to 3HP", phases: ["PHASE3"], conditions: ["Latent Tuberculosis Infection"] },
      topic);
    assert.equal(r.status, "CONCORDANT");
  });

  test("BLOCK: NCT00814671 is an ACTIVE-TB treatment trial in an LTBI review [RIFA §2.1]", () => {
    blocks(() => G.G09_assertRegistryConcordance(
      { nct: "NCT00814671", name: "Rifapentine LTBI", phase: "III" },
      { briefTitle: "Daily Rifapentine for Intensive Phase Treatment of Smear-positive Pulmonary Tuberculosis",
        phases: ["PHASE2"], conditions: ["Tuberculosis, Pulmonary"] },
      topic), "REGISTRY_DISCORDANT");
  });

  test("BLOCK: an unreachable registry is 'not checked', never 'concordant' [RECIPE-C §3.4]", () => {
    blocks(() => G.G09_assertRegistryConcordance({ nct: "NCT00831441", name: "APPRAISE-2" }, null, []),
      "REGISTRY_NOT_REACHED");
  });

  test("N/A, not passed, for an unregistered trial [RECIPE-C §3.1]", () => {
    const r = G.G09_assertRegistryConcordance({ name: "CIBIS-II" }, undefined, []);
    assert.equal(r.status, "N/A");
  });

  test("BLOCK: APPRAISE-1 fits 2 of 4 arms with no disclosure [APIXABAN §2.7]", () => {
    blocks(() => G.G09_assertRegistryConcordance(
      { nct: "NCT00313300", name: "APPRAISE", phase: "II", armsFitted: 2 },
      { briefTitle: "APPRAISE: Apixaban for Prevention of Acute Ischemic Events", phases: ["PHASE2"],
        conditions: ["Acute Coronary Syndrome"], armGroupCount: 5 },
      ["acute coronary syndrome"]), "REGISTRY_DISCORDANT");
  });
});

/* ============================================== G10 k-threshold machinery */

describe("G10 — k-threshold gate on machinery", () => {
  test("BLOCK: Copas 'Robust' at k=3 (needs k>=15) [ARNI 554b6f2a2]", () => {
    const r = G.G10_gateMachinery("copas", { k: 3 });
    assert.equal(r.render, false);
    assert.match(r.reason, /k >= 15/);
  });

  test("BLOCK: funnel / Egger / trim-fill at k=3", () => {
    for (const p of ["funnel", "egger", "trimfill"]) {
      assert.equal(G.G10_gateMachinery(p, { k: 3, estimand: "HR" }).render, false, p);
    }
  });

  test("BLOCK: meta-regression 'R2 = 100.0%' from 3 studies [ARNI 554b6f2a2]", () => {
    assert.equal(G.G10_gateMachinery("metaregression", { k: 3 }).render, false);
  });

  test("BLOCK: a subgroup interaction test with one trial per subgroup [ARNI 554b6f2a2]", () => {
    const r = G.G10_gateMachinery("subgroup", { k: 4, minSubgroupK: 1 });
    assert.equal(r.render, false);
    assert.match(r.reason, /is not a test/);
  });

  test("BLOCK: NMA league table / node-split in a pairwise review with no network [ARNI 554b6f2a2]", () => {
    assert.equal(G.G10_gateMachinery("leaguetable", { k: 4, hasNetwork: false }).render, false);
    assert.equal(G.G10_gateMachinery("nodesplit", { k: 4, hasNetwork: true, hasClosedLoop: false }).render, false);
  });

  test("BLOCK: NNT from an assumed baseline risk [ARNI 554b6f2a2 'NNT ~ 63']", () => {
    const r = G.G10_gateMachinery("nnt", { k: 3, estimand: "RR" });
    assert.equal(r.render, false);
    assert.match(r.reason, /assumed rate is not an estimate/);
  });

  test("N/A (not a pass): fragility index on an INDIRECT contrast [HFREF, 16 of 17]", () => {
    const r = G.G10_gateMachinery("fragility", { k: 1, estimand: "RR", hasCounts: true, isDirect: false, isSignificant: true });
    assert.equal(r.render, false);
    assert.match(r.reason, /UNDEFINED for an indirect estimate/);
  });

  test("N/A (not a pass): GRIM on binary counts, Benford on 16 digits [APIXABAN B5, §3]", () => {
    const grim = G.G10_gateMachinery("grim", { k: 4, hasBoundedMean: false });
    assert.equal(grim.na, true);
    const benford = G.G10_gateMachinery("benford", { k: 4, digits: 16 });
    assert.equal(benford.na, true);
    assert.match(benford.reason, /UNDERPOWERED/);
  });

  test("BLOCK: k unknown — a panel may not render before k is known", () => {
    blocks(() => G.G10_gateMachinery("funnel", {}), "K_UNKNOWN");
  });

  test("PASS: funnel at k=12 on an OR scale", () => {
    assert.equal(G.G10_gateMachinery("funnel", { k: 12, estimand: "OR" }).render, true);
  });

  test("BLOCK: DerSimonian-Laird at k=2 [RIFA S1]", () => {
    blocks(() => G.G10_assertEstimatorAdmissible("DL", 2), "ESTIMATOR_INADMISSIBLE");
    const r = G.G10_assertEstimatorAdmissible("REML", 2);
    assert.equal(r.reportHeterogeneity, false);
    assert.match(r.heterogeneityNote, /not interpretable at k=2/);
  });
});

/* ================================================ G11 unearned confidence */

describe("G11 — no verification claim over an unsourced field", () => {
  test("BLOCK: a '--' source under a verification claim [SOTA d5ec48c16]", () => {
    blocks(() => G.G11_assertVerificationClaim({ source: "--", verificationClaim: "100% confidence" }),
      "UNEARNED_VERIFICATION");
  });

  test("BLOCK: 'VERIFIED' with no quoted source text", () => {
    blocks(() => G.G11_assertVerificationClaim({ source: "NEJM 2019;381:1995", verificationClaim: "VERIFIED" }),
      "VERIFICATION_WITHOUT_QUOTE");
  });

  test("PASS: a claim backed by a quoted source field", () => {
    assert.equal(G.G11_assertVerificationClaim({
      source: "NEJM 2021;384:117-128", verificationClaim: "VERIFIED",
      quotedSourceText: "51.0 vs 76.3 per 100 person-years, HR 0.67 (0.52-0.85)",
      tier: "VERIFIED_FULL"
    }).ok, true);
  });

  test("BLOCK: an unknown evidence tier", () => {
    blocks(() => G.G11_assertTier("probably fine"), "TIER_MISSING_OR_UNKNOWN");
    assert.equal(G.G11_assertTier("VERIFIED_DENOM_ONLY"), "VERIFIED_DENOM_ONLY");
  });

  test("BLOCK: an all-cause-mortality analysis 'validated' against a composite benchmark [IRON §4(2)]", () => {
    blocks(() => G.G11_assertBenchmarkScope(
      { scope: "CV death + HHF", k: 3, trials: ["CONFIRM-HF", "AFFIRM-AHF", "IRONMAN", "HEART-FID"] },
      "all_cause_mortality"), "BENCHMARK_SCOPE_MISMATCH");
  });

  test("BLOCK: a benchmark whose k contradicts the trials named in its own scope string [IRON §4(2)]", () => {
    blocks(() => G.G11_assertBenchmarkScope(
      { scope: "all_cause_mortality", k: 3, trials: ["a", "b", "c", "d"] },
      "all_cause_mortality"), "BENCHMARK_SELF_INCONSISTENT");
  });
});

/* ======================================= G11 protocol provenance (RM-J01) */

describe("G11 — protocol provenance: drop the false attribution, KEEP the mechanism", () => {
  const good =
    "A publicly-pushed, version-controlled protocol commit is a tamper-evident protocol-provenance " +
    "record. Git history is a Merkle chain, so altering an earlier commit changes every later hash; " +
    "once public, third parties hold the original hashes. The evidence is the public push, not the " +
    "commit date, which is author-settable. This review is NOT prospectively registered.";

  test("BLOCK: the false ICMJE attribution [ARNI ce187425e]", () => {
    blocks(() => G.G11_assertProtocolProvenance(
      "Per ICMJE 2023, a GitHub commit hash + timestamp constitutes a verifiable pre-registration record."),
      "FALSE_ICMJE_ATTRIBUTION");
  });

  test("BLOCK: the PROSPERO-equivalence label", () => {
    blocks(() => G.G11_assertProtocolProvenance(
      "The commit record is equivalent to a PROSPERO registration. Tamper-evident public push."),
      "FALSE_PROSPERO_EQUIVALENCE");
  });

  test("BLOCK the OVER-CORRECTION: deleting the mechanism outright [ARNI 554b6f2a2 -> ce187425e]", () => {
    blocks(() => G.G11_assertProtocolProvenance("This review is NOT prospectively registered."),
      "MECHANISM_DELETED");
  });

  test("PASS: mechanism kept, attribution and equivalence gone", () => {
    assert.equal(G.G11_assertProtocolProvenance(good).ok, true);
  });

  test("BLOCK: a prospective claim smuggled into a retrospective review [ARNI ce187425e]", () => {
    blocks(() => G.G11_assertProtocolProvenance(
      "Tamper-evident public push. This review was prospectively registered by its protocol commit.",
      { retrospective: true }), "RETROSPECTIVE_FRAMED_AS_PROSPECTIVE");
    assert.equal(G.G11_assertProtocolProvenance(good, { retrospective: true }).ok, true);
  });
});

/* ============================================== G12 verdict-badge parity */

describe("G12 — both verdict surfaces or neither", () => {
  test("BLOCK: green 'INTERNAL CHECKS PASSED' over 2 AACT outcome-direction divergences [APIXABAN B1/B2]", () => {
    blocks(() => G.G12_assertVerdictParity(
      { verdict: "STABLE",
        counts: { p0_total: 0, P1_aact_concord: 2, P2_evidence_incomplete: 2, P2_aact_advisory: 2, n_trials_seen: 2 },
        reasons: ["2 AACT title/registry advisory", "2 AACT outcome-direction divergence(s)", "2 trial(s) missing evidence rows"] },
      { background: "#15803d", text: "INTERNAL CHECKS PASSED Fabrication-risk score: 0.275 Trials: 2" },
      { trialCount: 2 }), "FALSE_GREEN_FINDINGS");
  });

  test("BLOCK: HFrEF live on main — green badge 'Trials: 2' over an UNCERTAIN 28-trial verdict [HARNESS F-05]", () => {
    blocks(() => G.G12_assertVerdictParity(
      { verdict: "UNCERTAIN", counts: { n_trials_seen: 28 }, reasons: [] },
      { background: "#15803d", text: "INTERNAL CHECKS PASSED Trials: 2 Multi-source audit completed", trialCount: 2 },
      { trialCount: 28 }), "FALSE_GREEN_VERDICT");
  });

  test("BLOCK: a green badge over ZERO trials [276d749a3, EZETIMIBE_LIPID / LISINOPRIL_HTN]", () => {
    blocks(() => G.G12_assertVerdictParity(
      { verdict: "STABLE", counts: { n_trials_seen: 0 }, reasons: [] },
      { background: "#15803d", text: "CHECKS PASSED Trials: 2" },
      { trialCount: 0 }), "FALSE_GREEN_EMPTY");
  });

  test("BLOCK: badge says 2 trials, the ledger holds 4 [APIXABAN B3]", () => {
    blocks(() => G.G12_assertVerdictParity(
      { verdict: "UNCERTAIN", counts: { n_trials_seen: 2 }, reasons: ["x"] },
      { background: "#7c2d12", text: "VERDICT: UNCERTAIN", trialCount: 2 },
      { trialCount: 4 }), "TRIAL_COUNT_DISAGREEMENT");
  });

  test("BLOCK: 10 vs 14 internal-consistency rounds in one badge [APIXABAN B4 / ARNI 554b6f2a2]", () => {
    blocks(() => G.G12_assertBadgeSelfConsistent(
      "Multi-source audit completed (AACT 2026-04-12 + PubMed + 10 internal-consistency rounds). " +
      "Audited via AACT 2026-04-12 + PubMed + 14 internal-consistency rounds."),
      "BADGE_SELF_CONTRADICTION");
  });

  test("BLOCK: 'Trials: 28' beside '27 trials' [HFREF partial badge replacement]", () => {
    blocks(() => G.G12_assertBadgeSelfConsistent("Trials: <strong>28</strong> ... k = 27 ... Trials: 27"),
      "BADGE_SELF_CONTRADICTION");
  });

  test("BLOCK: an N/A gate printed without its reason [APIXABAN B5]", () => {
    blocks(() => G.G12_assertVerdictParity(
      { verdict: "UNCERTAIN", counts: { n_trials_seen: 4 }, reasons: ["x"] },
      { background: "#7c2d12", text: "VERDICT: UNCERTAIN", trialCount: 4, naGates: ["P0_grim"], naReasons: {} },
      { trialCount: 4 }), "NA_REPORTED_AS_PASS");
  });

  test("PASS: an honest amber badge agreeing with __verdict on every number", () => {
    const r = G.G12_assertVerdictParity(
      { verdict: "UNCERTAIN", counts: { n_trials_seen: 4, P1_aact_concord: 2 }, reasons: ["r1"] },
      { background: "#7c2d12",
        text: "VERDICT: UNCERTAIN - 23 FINDINGS. Trials: 4. GRIM N/A (binary counts, no means).",
        trialCount: 4, naGates: ["P0_grim"], naReasons: { P0_grim: "binary counts, no means to reconstruct" } },
      { trialCount: 4 });
    assert.equal(r.ok, true);
  });
});

/* ================================================== G13 app identity */

describe("G13 — the filename must describe the content", () => {
  test("BLOCK: TIRZEPATIDE_ARDS contains an andexanet alfa review [CARDIO-MIS §1]", () => {
    blocks(() => G.G13_assertAppIdentity(
      "TIRZEPATIDE_ARDS_AUTO_FULL_REVIEW",
      "RapidMeta | Andexanet alfa for FXa-inhibitor reversal (audit-first, full-functionality)",
      "Andexanet vs comparator in Bleeding (AACT-verified primary)"), "IDENTITY_MISMATCH");
  });

  test("BLOCK: ICAGEN contains an edoxaban review [CARDIO-MIS §2]", () => {
    blocks(() => G.G13_assertAppIdentity(
      "ICAGEN_AUTO_FULL_REVIEW", "RapidMeta | Edoxaban TIMI 48 cancer-VTE",
      "Edoxaban vs comparator in Cancer"), "IDENTITY_MISMATCH");
  });

  test("PASS: SGLT2_HF matches its own title", () => {
    assert.equal(G.G13_assertAppIdentity(
      "SGLT2_HF_REVIEW", "RapidMeta | SGLT2 inhibitors in heart failure", "Dapagliflozin").ok, true);
  });
});

/* ============================================ G14 template contamination */

describe("G14 — cross-topic template contamination", () => {
  test("BLOCK: the sacubitril/valsartan alias table in a tuberculosis app [RIFA §4 — 526 apps]", () => {
    blocks(() => G.G14_assertNoContamination(
      'KNOWN_TRIAL_ALIASES={NCT01035255:["paradigm-hf"],NCT01920711:["paragon-hf"],' +
      'NCT02924727:["paradise-mi"],NCT03988634:["paraglide-hf"]}',
      ["latent tuberculosis", "rifapentine"]), "TEMPLATE_CONTAMINATION");
  });

  test("PASS: the same table in the app that owns it", () => {
    assert.equal(G.G14_assertNoContamination(
      'KNOWN_TRIAL_ALIASES={NCT01035255:["paradigm-hf"],NCT01920711:["paragon-hf"]}',
      ["sacubitril valsartan", "heart failure"]).ok, true);
  });

  test("BLOCK: the SGLT2i adverse-event profile in an unrelated app [619512b4d, 148 clones]", () => {
    blocks(() => G.G14_assertNoContamination(
      "Adverse events of interest: Fournier gangrene, genital mycotic infection, diabetic ketoacidosis.",
      ["schistosomiasis", "praziquantel"]), "TEMPLATE_CONTAMINATION");
  });

  test("BLOCK: finerenone/FIDELIO donor strings in a non-MRA app", () => {
    blocks(() => G.G14_assertNoContamination(
      "Primary outcome mirrors FIDELIO-DKD; finerenone reduced eGFR slope.", ["tuberculosis"]),
      "TEMPLATE_CONTAMINATION");
  });

  test("PASS: the repo's own rapidmeta-finerenone asset URL is not contamination", () => {
    assert.equal(G.G14_assertNoContamination(
      '<link href="https://mahmood726-cyber.github.io/rapidmeta-finerenone/assets/css/paper-studio.css">',
      ["tuberculosis"]).ok, true);
  });
});

/* ======================================== G15 posted-value extraction */

describe("G15 — read unitOfMeasure before using a posted value", () => {
  test("BLOCK: APPRAISE-2 13.96 'percentage of participants/100-pt years' x 3687 = 515 [APIXABAN §2.1]", () => {
    blocks(() => G.G15_countFromPostedOutcome(13.96, "percentage of participants/100-pt years", 3687),
      "RATE_IS_NOT_A_PROPORTION");
  });

  test("BLOCK: AUGUSTUS 24.66 'Percentage per year' x 1153 = 284 [APIXABAN §2.1]", () => {
    blocks(() => G.G15_countFromPostedOutcome(24.66, "Percentage per year", 1153), "RATE_IS_NOT_A_PROPORTION");
  });

  test("PASS: a true proportion converts to a count", () => {
    const r = G.G15_countFromPostedOutcome(7.5, "Percentage of Participants", 3705);
    assert.equal(Math.round(r.count), 278);
  });

  test("BLOCK: a missing or unrecognised unit fails closed rather than guessing", () => {
    blocks(() => G.G15_countFromPostedOutcome(13.96, null, 3687), "UNIT_OF_MEASURE_MISSING");
    blocks(() => G.G15_countFromPostedOutcome(13.96, "some new unit", 3687), "UNIT_NOT_RECOGNISED");
  });

  test("arms bind by TITLE — ClinicalTrials.gov lists placebo first [APIXABAN §2.2]", () => {
    const groups = [{ id: "OG000", title: "Placebo" }, { id: "OG001", title: "Apixaban 2.5 mg BID" }];
    assert.equal(G.G15_bindArmByTitle(groups, "apixaban").id, "OG001");
    assert.equal(G.G15_bindArmByTitle(groups, "placebo").id, "OG000");
    blocks(() => G.G15_bindArmByTitle(groups, null), "ARM_TITLE_REQUIRED");
    blocks(() => G.G15_bindArmByTitle(groups, "ticagrelor"), "ARM_TITLE_NOT_FOUND");
  });
});

/* ============================================== G16 sensitivity interval */

describe("G16 — the interval that crosses 1 must be on the same surface", () => {
  test("BLOCK: an HKSJ interval crossing 1 hidden behind a significant headline [ACS-GATE acc656de0 R3]", () => {
    blocks(() => G.G16_assertIntervalCoRender(
      { lci: 1.0411, uci: 3.7458 },
      { label: "HKSJ", lci: 0.03, uci: 124.7 },
      "Pooled OR 1.97 (1.04-3.74), p=0.037, k=2."), "SENSITIVITY_INTERVAL_HIDDEN");
  });

  test("PASS: co-rendered", () => {
    assert.equal(G.G16_assertIntervalCoRender(
      { lci: 1.0411, uci: 3.7458 },
      { label: "HKSJ", lci: 0.03, uci: 124.7 },
      "Pooled OR 1.97 (1.04-3.74). HKSJ 0.03-124.7 crosses 1; fragility index 1.").required, true);
  });

  test("PASS: nothing required when the headline already crosses 1 [VIVAX F3]", () => {
    assert.equal(G.G16_assertIntervalCoRender(
      { lci: 0.629, uci: 1.825 }, { label: "Paule-Mandel", lci: 0.516, uci: 2.210 },
      "OR 1.072 (0.629, 1.825)").required, false);
  });
});

/* ==================================================== G17 direction */

describe("G17 — direction is derived from an explicit polarity", () => {
  test("BLOCK: no polarity on the row", () => {
    blocks(() => G.G17_assertPolarity({ title: "Culture conversion at week 8" }), "POLARITY_MISSING");
  });

  test("a GOOD outcome inverts the reading: OR<1 means WORSE [RIFA §2.1]", () => {
    assert.equal(G.G17_directionWord(0.389, "harm"), "favours the comparator");
    assert.equal(G.G17_directionWord(0.389, "benefit"), "favours the intervention");
  });

  test("APIXABAN: OR 1.975 on bleeding favours the comparator [cb876d805]", () => {
    assert.equal(G.G17_directionWord(1.975, "benefit"), "favours the comparator");
    assert.equal(G.G17_directionWord(0.850, "benefit"), "favours the intervention",
      "the pre-correction figure read as benefit — the arms, not the arithmetic, were wrong");
  });

  test("BLOCK: an NNH rendered for a result that favours the intervention", () => {
    blocks(() => G.G17_assertNntNnhLabel("nnh", 0.74, "benefit"), "NNH_ON_A_BENEFIT");
    blocks(() => G.G17_assertNntNnhLabel("nnt", 1.975, "benefit"), "NNT_ON_A_HARM");
    assert.equal(G.G17_assertNntNnhLabel("nnh", 1.975, "benefit").direction, "favours the comparator");
  });

  test("BLOCK: a good outcome and a bad outcome pooled on one scale [RIFA §2.3, P0]", () => {
    blocks(() => G.G17_assertPoolPolarityConsistent([
      { title: "Negative LJ culture at week 8", polarity: "harm" },
      { title: "Not advisable to continue study drugs", polarity: "benefit" }
    ]), "MIXED_POLARITY_POOL");
  });

  test("PASS: a consistent-polarity pool", () => {
    assert.equal(G.G17_assertPoolPolarityConsistent([
      { title: "ISTH major/CRNM bleeding", polarity: "benefit" },
      { title: "ISTH major/CRNM bleeding", polarity: "benefit" }
    ]).polarity, "benefit");
  });

  test("BLOCK: a non-positive effect has no direction", () => {
    blocks(() => G.G17_directionWord(-0.5509, "benefit"), "EFFECT_NOT_A_RATIO");
  });
});

/* ============================================ G18/G19/G20 — added 2026-07-30 calibration pass */

describe("G01 (strengthened) — the ratio range", () => {
  test("BLOCK: a NEGATIVE pooled 'hazard ratio' of -19.50 [bempedoic LDL-C selector]", () => {
    blocks(() => G.G01_assertRatioModelInput({ estimandType: "HR", publishedHR: -19.5 }, "HR"),
      "RATIO_FIELD_NON_POSITIVE");
  });
  test("BLOCK: outside the hard [0.01, 100] bound", () => {
    blocks(() => G.G01_assertRatioModelInput({ estimandType: "HR", publishedHR: 2050 }, "HR"),
      "RATIO_FIELD_IMPOSSIBLE");
    blocks(() => G.G01_assertRatioModelInput({ estimandType: "HR", publishedHR: 0.001 }, "HR"),
      "RATIO_FIELD_IMPOSSIBLE");
  });
  test("BLOCK: inside the hard bound but outside any reported range (pubHR 73.83)", () => {
    blocks(() => G.G01_assertRatioModelInput({ estimandType: "HR", publishedHR: 73.83 }, "HR"),
      "RATIO_FIELD_IMPLAUSIBLE");
  });
  test("PASS: an ordinary effect", () => {
    assert.equal(G.G01_assertRatioModelInput({ estimandType: "HR", publishedHR: 0.62 }, "HR").ok, true);
  });
});

describe("G18 — the fail-closed integrity gate", () => {
  test("BLOCK: a NULLED trial id [bempedoic NULLED:NCT02666664]", () => {
    blocks(() => G.G18_assertIntegrityGate({ trialIds: ["NCT02993406", "NULLED:NCT02666664"] }),
      "INTEGRITY_GATE_FAILED");
  });
  test("BLOCK: a null trial id", () => {
    blocks(() => G.G18_assertIntegrityGate({ trialIds: ["NCT02993406", null] }), "INTEGRITY_GATE_FAILED");
  });
  test("BLOCK: composite component sets differ across pooled rows [PCSK9 FOURIER vs ODYSSEY]", () => {
    const e = blocks(() => G.G18_assertIntegrityGate({
      trialIds: ["NCT01764633", "NCT01663402"],
      pooledRows: [
        { trial: "FOURIER", components: ["CV death", "MI", "stroke", "UA hosp", "revascularisation"] },
        { trial: "ODYSSEY OUTCOMES", components: ["CHD death", "nonfatal MI", "ischaemic stroke", "UA hosp"] }
      ]
    }), "INTEGRITY_GATE_FAILED");
    assert.match(e.message, /component sets differ/);
  });
  test("BLOCK: a NaN output and a leave-one-out NaN interval", () => {
    blocks(() => G.G18_assertIntegrityGate({
      trialIds: ["NCT1"], outputs: [{ name: "pooled", value: NaN }]
    }), "INTEGRITY_GATE_FAILED");
    blocks(() => G.G18_assertIntegrityGate({
      trialIds: ["NCT1"], outputs: [{ name: "leave-one-out", value: 0.9, interval: [null, null] }]
    }), "INTEGRITY_GATE_FAILED");
  });
  test("BLOCK: an impossible ratio output [-19.50]", () => {
    blocks(() => G.G18_assertIntegrityGate({
      trialIds: ["NCT1"], outputs: [{ name: "Pooled Hazard Ratio", value: -19.5, isRatio: true }]
    }), "INTEGRITY_GATE_FAILED");
  });
  test("BLOCK: trial counts disagreeing across surfaces [bempedoic 4 vs 5 vs 2]", () => {
    const e = blocks(() => G.G18_assertIntegrityGate({
      trialIds: ["NCT1"], trialCounts: [4, 5, 2]
    }), "INTEGRITY_GATE_FAILED");
    assert.match(e.message, /disagree across surfaces/);
  });
  test("BLOCK: a pass claimed without having run", () => {
    blocks(() => G.G18_assertIntegrityGate({
      trialIds: ["NCT1"], claimsPass: true, untested: "per-trial source verification"
    }), "UNEARNED_PASS");
  });
  test("PASS: a coherent state", () => {
    assert.equal(G.G18_assertIntegrityGate({
      trialIds: ["NCT01764633", "NCT01663402"],
      pooledRows: [
        { trial: "A", components: ["CV death", "MI", "stroke"] },
        { trial: "B", components: ["stroke", "CV death", "MI"] }
      ],
      outputs: [{ name: "pooled", value: 0.85, isRatio: true, interval: [0.78, 0.93] }],
      trialCounts: [2, 2, 2], participantCounts: [23246, 23246]
    }).ok, true);
  });
});

describe("G19 — composite component sets must match before pooling", () => {
  test("BLOCK: MACE-3 pooled with MACE-4 [bempedoic Wisdom vs CLEAR Outcomes]", () => {
    blocks(() => G.G19_assertCompositeComponentsMatch([
      { trial: "CLEAR Wisdom", components: ["CV death", "nonfatal MI", "nonfatal stroke"] },
      { trial: "CLEAR Outcomes", components: ["CV death", "nonfatal MI", "nonfatal stroke", "coronary revascularisation"] }
    ]), "COMPONENT_SET_MISMATCH");
  });
  test("BLOCK: an undeclared component set", () => {
    blocks(() => G.G19_assertCompositeComponentsMatch([
      { trial: "A", components: ["CV death", "MI"] }, { trial: "B" }
    ]), "COMPONENTS_UNDECLARED");
  });
  test("PASS: identical sets in any order", () => {
    assert.equal(G.G19_assertCompositeComponentsMatch([
      { trial: "A", components: ["CV death", "MI", "stroke"] },
      { trial: "B", components: ["stroke", "MI", "CV death"] }
    ]).checked, true);
  });
});

describe("G20 — the monitored watchlist must be the app's own topic", () => {
  const finerenoneWatchlist = [
    { label: "FIDELIO-DKD" }, { label: "FIGARO-DKD" }, { label: "FINEARTS-HF" },
    { label: "ARTS-DN" }, { label: "FINE-ONE" }, { label: "CONFIDENCE" }
  ];
  test("BLOCK: a PCSK9 app monitoring the finerenone programme [PCSK9_REVIEW.html]", () => {
    const e = blocks(() => G.G20_assertWatchlistOnTopic(finerenoneWatchlist,
      ["pcsk9", "evolocumab", "alirocumab", "lipid"]), "WATCHLIST_WRONG_TOPIC");
    assert.match(e.message, /FIDELIO-DKD/);
  });
  test("BLOCK: a bempedoic app monitoring the same list [BEMPEDOIC_ACID_REVIEW.html]", () => {
    blocks(() => G.G20_assertWatchlistOnTopic(finerenoneWatchlist, ["bempedoic", "acid"]),
      "WATCHLIST_WRONG_TOPIC");
  });
  test("PASS: the app that owns the watchlist", () => {
    assert.equal(G.G20_assertWatchlistOnTopic(finerenoneWatchlist,
      ["finerenone", "fidelio", "figaro", "fineartsef", "arts", "fine", "confidence"]).checked, true);
  });
  test("BLOCK: a partially foreign watchlist", () => {
    blocks(() => G.G20_assertWatchlistOnTopic(
      [{ label: "FOURIER" }, { label: "FIDELIO-DKD" }], ["fourier", "evolocumab"]),
      "WATCHLIST_PARTIALLY_FOREIGN");
  });
});
/* ============================================ G21 — the returning-visitor trap (RM-B09) */

describe("G21 — persisted state may never resurrect a withdrawn row", () => {
  // The andexanet app after its fix: realData emptied, three rows quarantined.
  const authoritative = {
    realDataIds: [],
    quarantinedIds: ["NCT02220725", "NCT02207725", "NCT02329327"],
    ledgerFingerprint: G.G21_ledgerFingerprint([], ["NCT02220725", "NCT02207725", "NCT02329327"], "v12.3")
  };
  // A profile saved BEFORE the fix, carrying the auto-seeded rows and a pooled result.
  const staleProfile = {
    ledgerFingerprint: G.G21_ledgerFingerprint(
      ["NCT02220725", "NCT02207725", "NCT02329327"], [], "v12.2"),
    trials: [
      { id: "NCT02220725", status: "include", data: { tE: 1, tN: 14, pubHR: 73.83 } },
      { id: "NCT02207725", status: "include", data: { tE: 0, tN: 9, pubHR: 73.15 } },
      { id: "NCT02329327", status: "include", data: { tE: 2, tN: 477, pubHR: 0.80, hrLCI: -0.5509 } }
    ],
    pooledResult: { rr: 0.03, lci: 0.00, uci: 0.52 }
  };

  test("a stale profile's quarantined rows are PURGED, not kept [reproduced live as RR 0.03 (0.00-0.52)]", () => {
    const r = G.G21_reconcilePersistedState(staleProfile, authoritative);
    assert.equal(r.trials.length, 0, "no pre-fix row survives into the analysis");
    assert.equal(r.purged.length, 3);
    assert.equal(r.staleLedger, true);
    assert.equal(r.mustRederive, true);
  });

  test("a persisted pooled estimate is NEVER carried forward", () => {
    const r = G.G21_reconcilePersistedState(staleProfile, authoritative);
    assert.equal(r.pooledResult, null, "the withdrawn RR 0.03 must not survive the hydrate");
  });

  test("a persisted row absent from the authoritative ledger is dropped", () => {
    const r = G.G21_reconcilePersistedState(
      { ledgerFingerprint: "lf1_x", trials: [{ id: "NCT99999999", status: "include", data: {} }] },
      { realDataIds: ["NCT01764633"], quarantinedIds: [], ledgerFingerprint: "lf1_y" });
    assert.equal(r.trials.length, 0);
    assert.equal(r.dropped[0].why, "absent from the authoritative ledger");
  });

  test("BLOCK: an authoritative ledger with no fingerprint cannot detect a stale profile", () => {
    blocks(() => G.G21_reconcilePersistedState(staleProfile,
      { realDataIds: [], quarantinedIds: [] }), "LEDGER_FINGERPRINT_MISSING");
  });

  test("PASS: a current profile against an unchanged ledger keeps its rows and re-derives", () => {
    const auth = {
      realDataIds: ["NCT01764633", "NCT01663402"], quarantinedIds: [],
      ledgerFingerprint: G.G21_ledgerFingerprint(["NCT01764633", "NCT01663402"], [], "v12.0")
    };
    const r = G.G21_reconcilePersistedState(
      { ledgerFingerprint: auth.ledgerFingerprint,
        trials: [{ id: "NCT01764633", data: {} }, { id: "NCT01663402", data: {} }] }, auth);
    assert.equal(r.trials.length, 2);
    assert.equal(r.staleLedger, false);
    assert.equal(r.purged.length, 0);
    assert.equal(r.mustRederive, false);
  });

  test("the fingerprint changes when the ledger changes, and is stable when it does not", () => {
    const a = G.G21_ledgerFingerprint(["A", "B"], [], "v1");
    const b = G.G21_ledgerFingerprint(["B", "A"], [], "v1");
    const c = G.G21_ledgerFingerprint(["A"], ["B"], "v1");
    assert.equal(a, b, "order-independent");
    assert.notEqual(a, c, "quarantining a row changes the fingerprint");
  });

  test("assertNoResurrection is the verifier form", () => {
    const r = G.G21_assertNoResurrection(staleProfile, authoritative);
    assert.equal(r.trials.length, 0);
  });
});
/* ============ G12 audit-trail strip — an honest badge quotes the claim it replaced */

describe("G12 — a quoted prior claim is not a live claim", () => {
  // LISINOPRIL_HTN_AUTO_FULL_REVIEW.html as it is live on main AFTER its fix (commit 0bcb8bd8a).
  const correctedBadge =
    "NO DATA — THIS IS NOT AN INTEGRITY PASS. Trials in ledger: 0 · Trials analysed: 0 · " +
    "Pooled estimate: none. What this badge used to say, and why it was wrong. " +
    "It read \u201cINTERNAL CHECKS PASSED · Fabrication-risk score 0.275 · Trials: 2\u201d on a " +
    "green background, and the page's own verdict said STABLE.";
  const verdict = { verdict: "NO_DATA", counts: { n_trials_seen: 0 }, reasons: [] };

  test("the corrected LISINOPRIL badge PASSES — the pass phrase is quoted, not asserted", () => {
    const r = G.G12_assertVerdictParity(verdict,
      { background: "#7c2d12", text: correctedBadge }, { trialCount: 0 });
    assert.equal(r.ok, true);
  });

  test("the quoted 'Trials: 2' is not read as the badge's own count", () => {
    assert.equal(/Trials?\s*:\s*(\d+)/.test(G.G12_stripAuditTrail(correctedBadge)), false);
  });

  test("self-consistency ignores numbers inside the retention text", () => {
    assert.equal(G.G12_assertBadgeSelfConsistent(correctedBadge).ok, true);
  });

  test("BLOCK still fires on a LIVE pass claim over a non-STABLE verdict", () => {
    blocks(() => G.G12_assertVerdictParity(verdict,
      { background: "#15803d", text: "INTERNAL CHECKS PASSED · Trials: 2" }, { trialCount: 0 }),
      "FALSE_GREEN_VERDICT");
  });

  test("BLOCK still fires when the contradiction is OUTSIDE the retention text", () => {
    blocks(() => G.G12_assertBadgeSelfConsistent(
      "Trials: 28 ... k = 27 ... Trials: 27 ... What this badge used to say: Trials: 99"),
      "BADGE_SELF_CONTRADICTION");
  });
});
/* ==================== G12 — gate P2: straight quotes, and a LIVE claim after the narrative */

describe("G12 audit-trail strip — gate P2 refinements", () => {
  test("a STRAIGHT-quoted prior claim is stripped, not treated as an assertion", () => {
    const badge = 'NO DATA. It read "INTERNAL CHECKS PASSED - Trials: 2" on a green background.';
    assert.equal(/CHECKS PASSED/.test(G.G12_stripAuditTrail(badge)), false);
    const r = G.G12_assertVerdictParity(
      { verdict: "NO_DATA", counts: { n_trials_seen: 0 }, reasons: [] },
      { background: "#7c2d12", text: badge }, { trialCount: 0 });
    assert.equal(r.ok, true, "an honest straight-quoted badge must not be blocked");
  });

  test("a LIVE pass claim placed AFTER a retention marker is still caught", () => {
    // Previously stripAuditTrail truncated everything from the marker onward, so anything the
    // badge asserted after its own narrative became invisible.
    const badge = "What this badge used to say, and why it was wrong. " +
                  "INTERNAL CHECKS PASSED · Trials: 2";
    assert.equal(/CHECKS PASSED/.test(G.G12_stripAuditTrail(badge)), true);
    blocks(() => G.G12_assertVerdictParity(
      { verdict: "UNCERTAIN", counts: { n_trials_seen: 2 }, reasons: ["x"] },
      { background: "#15803d", text: badge }, { trialCount: 2 }), "FALSE_GREEN_VERDICT");
  });

  test("only the retention SENTENCE is removed, not the rest of the badge", () => {
    const out = G.G12_stripAuditTrail("Verdict UNCERTAIN. It read wrongly. Trials: 4 in the fit.");
    assert.match(out, /Trials: 4 in the fit/);
  });
});

/* ============================================ G18 — gate P0-2: fail-closed on an empty ledger */

describe("G18 — an empty or absent ledger is N/A, never a pass (gate P0-2)", () => {
  test("BLOCK: assertIntegrityGate({}) must not return ok", () => {
    blocks(() => G.G18_assertIntegrityGate({}), "LEDGER_ABSENT");
  });

  test("BLOCK: zero trials with a NO_DATA verdict is still not a pass", () => {
    const e = blocks(() => G.G18_assertIntegrityGate({ trialIds: [], verdictWord: "NO_DATA" }),
      "LEDGER_ABSENT");
    assert.match(e.message, /NO_DATA/);
  });

  test("BLOCK: a STRING 'NaN' output is caught, not just a numeric NaN", () => {
    blocks(() => G.G18_assertIntegrityGate({
      trialIds: ["NCT1"], outputs: [{ name: "pooled", value: "NaN" }]
    }), "INTEGRITY_GATE_FAILED");
    blocks(() => G.G18_assertIntegrityGate({
      trialIds: ["NCT1"], outputs: [{ name: "loo", value: 0.9, interval: ["NaN", "NaN"] }]
    }), "INTEGRITY_GATE_FAILED");
  });

  test("PASS: a real ledger still passes", () => {
    assert.equal(G.G18_assertIntegrityGate({ trialIds: ["NCT1", "NCT2"], trialCounts: [2, 2] }).ok, true);
  });
});