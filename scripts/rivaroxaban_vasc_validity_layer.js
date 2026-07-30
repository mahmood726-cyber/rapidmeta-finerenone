/* RIVAROXABAN VASCULAR REVIEW - app-local validity & honesty layer (2026-07-30)
 *
 * Appended to RIVAROXABAN_VASC_REVIEW.html only. Everything here is scoped to
 * this app; nothing in shared vendor/ or assets/js/ modules is modified, because
 * those are used by every RapidMeta app and changing them has portfolio-wide
 * blast radius.
 *
 * What this layer does, and why:
 *  A. Endpoint heterogeneity banner - the four trial primary endpoints are NOT
 *     the same endpoint, so the pooled estimate must not be presented as a
 *     harmonised 3-point MACE.
 *  B. Per-trial eligibility ledger - two included trials violate the written
 *     PICO. Rather than silently including them, the violation is stated.
 *  C. Small-k (k=4) validity gate - Egger / funnel / trim-and-fill /
 *     meta-regression / one-trial subgroups / TSA / fragility are marked
 *     EXPLORATORY with an on-panel reason instead of being read as results.
 *  D. PRISMA flow rebuilt to be arithmetically consistent (the shared
 *     vendor/prisma-flow.js diagram is overridden in this app's DOM only).
 *  E. Paper Studio worked-example quarantine - the shared teaching example is a
 *     finerenone/CKD manuscript; it is labelled so it cannot be mistaken for
 *     this study's content.
 */
(function () {
  "use strict";

  var TAG = "[rivaroxaban-validity]";
  var K = 4;

  // ---------------------------------------------------------------- helpers
  function el(tag, attrs, html) {
    var n = document.createElement(tag);
    if (attrs) Object.keys(attrs).forEach(function (k) { n.setAttribute(k, attrs[k]); });
    if (html != null) n.innerHTML = html;
    return n;
  }
  function once(id) {
    if (document.getElementById(id)) return false;
    return true;
  }

  var WARN_CSS =
    "border:1px solid #f59e0b;background:rgba(245,158,11,0.10);color:#fcd34d;" +
    "border-radius:6px;padding:10px 12px;margin:10px 0;font-size:11.5px;line-height:1.55;";
  var STOP_CSS =
    "border:1px solid #ef4444;background:rgba(239,68,68,0.10);color:#fca5a5;" +
    "border-radius:6px;padding:10px 12px;margin:10px 0;font-size:11.5px;line-height:1.55;";

  // ------------------------------------------------------- A. endpoint banner
  var ENDPOINTS = [
    ["COMPASS (n=18,278)", "CV death + stroke + MI", "3 components - exact 3-point MACE",
      "Rivaroxaban 2.5 mg BID + aspirin vs aspirin alone. Stable CAD/PAD."],
    ["VOYAGER-PAD (n=6,564)", "ALI + major amputation + MI + ischaemic stroke + CV death",
      "5 components - limb/CV composite, NOT 3-point MACE",
      "Rivaroxaban 2.5 mg BID + aspirin vs placebo + aspirin. PAD after revascularisation."],
    ["COMMANDER HF (n=5,022)", "ALL-CAUSE death + MI + stroke",
      "3 components but the death term is all-cause, NOT CV death",
      "Rivaroxaban 2.5 mg BID vs placebo (no aspirin comparator). Decompensated HFrEF + CAD."],
    ["ATLAS ACS 2 (2.5 mg arm)", "CV death + MI + stroke",
      "3 components - matches COMPASS on components only",
      "Rivaroxaban 2.5 mg BID vs placebo, on aspirin +/- a thienopyridine. ACUTE ACS. The " +
      "contemporaneous antiplatelet background differs from the stable-ASCVD setting, which is a " +
      "comparability issue in its own right - not a reason to exclude the trial for its age."]
  ];

  function endpointBanner() {
    if (!once("rv-endpoint-banner")) return;
    var rows = ENDPOINTS.map(function (e) {
      return '<tr>' +
        '<td style="padding:4px 8px;vertical-align:top;white-space:nowrap;"><strong>' + e[0] + '</strong></td>' +
        '<td style="padding:4px 8px;vertical-align:top;">' + e[1] + '</td>' +
        '<td style="padding:4px 8px;vertical-align:top;color:#fbbf24;">' + e[2] + '</td>' +
        '<td style="padding:4px 8px;vertical-align:top;color:#94a3b8;">' + e[3] + '</td>' +
        '</tr>';
    }).join("");

    return el("div", { id: "rv-endpoint-banner", style: STOP_CSS },
      '<div style="font-weight:700;margin-bottom:6px;">ENDPOINTS ARE NOT HARMONISED - the pooled estimate is not a 3-point MACE</div>' +
      '<div style="margin-bottom:8px;">The four trials contribute their own <em>trial-specific primary composite</em>. ' +
      'Only COMPASS has an endpoint that is exactly CV death + stroke + MI. Pooling these gives an estimate of ' +
      '"effect of low-dose rivaroxaban on each trial\'s own primary endpoint" - it is <strong>not</strong> a pooled ' +
      'cardiovascular-death/MI/stroke effect, and it should not be labelled or cited as one.</div>' +
      '<table style="width:100%;border-collapse:collapse;font-size:11px;">' +
      '<thead><tr style="color:#94a3b8;text-align:left;">' +
      '<th style="padding:4px 8px;">Trial</th><th style="padding:4px 8px;">Primary endpoint as registered</th>' +
      '<th style="padding:4px 8px;">Match to 3-point MACE</th><th style="padding:4px 8px;">Population / comparator</th>' +
      '</tr></thead><tbody>' + rows + '</tbody></table>' +
      '<div style="margin-top:8px;">The prediction interval for the pooled estimate crosses 1. A claim of a ' +
      '"robust 15% reduction across settings" is not supported: it overstates both the consistency and the ' +
      'transportability of the result.</div>');
  }

  // --------------------------------------------------- B. eligibility ledger
  // Eligibility is judged on SCOPE (PICO) plus verified data availability only.
  // Publication/enrolment date is not an eligibility axis: evidence is sourced
  // from regulatory dossiers (FDA/EMA), supplements of previous meta-analyses
  // and open-access full texts, not from ClinicalTrials.gov alone, so a trial's
  // age does not predict whether usable data can be obtained.
  var ELIGIBILITY = [
    ["COMPASS", "IN SCOPE", "#4ade80",
      "Stable ASCVD. Rivaroxaban 2.5 mg BID + aspirin vs aspirin alone - the dual-pathway " +
      "comparison. Full outcome data retrievable."],
    ["VOYAGER-PAD", "IN SCOPE", "#4ade80",
      "Symptomatic PAD after revascularisation. Rivaroxaban 2.5 mg BID + aspirin vs aspirin. " +
      "Full outcome data retrievable."],
    ["COMMANDER HF", "OUT OF SCOPE", "#f87171",
      "Population is decompensated HFrEF with CAD, not stable ASCVD/PAD. Comparator is placebo " +
      "with no aspirin requirement, so this is not a dual-pathway comparison. Data are " +
      "retrievable - the issue is scope and comparability, not availability."],
    ["ATLAS ACS 2", "OUT OF SCOPE", "#f87171",
      "Population is ACUTE ACS (within 7 days) on aspirin +/- a thienopyridine, not stable " +
      "ASCVD/PAD, and the comparator is placebo on that background. Judged on scope alone: its " +
      "2012 publication date is NOT a reason to exclude it, and its full 2.5 mg-arm mITT data " +
      "are verified and retrievable from the CT.gov results record."]
  ];

  function eligibilityLedger() {
    if (!once("rv-eligibility-ledger")) return;
    var rows = ELIGIBILITY.map(function (e) {
      return '<tr><td style="padding:4px 8px;"><strong>' + e[0] + '</strong></td>' +
        '<td style="padding:4px 8px;color:' + e[2] + ';font-weight:600;">' + e[1] + '</td>' +
        '<td style="padding:4px 8px;color:#cbd5e1;">' + e[3] + '</td></tr>';
    }).join("");
    return el("div", { id: "rv-eligibility-ledger", style: WARN_CSS },
      '<div style="font-weight:700;margin-bottom:6px;">ELIGIBILITY: 2 of 4 analysed trials fall outside the ' +
      'written scope</div>' +
      '<table style="width:100%;border-collapse:collapse;font-size:11px;"><tbody>' + rows + '</tbody></table>' +
      '<div style="margin-top:8px;"><strong>Eligibility is decided on scope (PICO) plus verified data ' +
      'availability. Publication or enrolment date is not an eligibility criterion</strong> - evidence is ' +
      'sourced from regulatory dossiers (FDA/EMA), supplements of previous meta-analyses and open-access full ' +
      'texts, not from ClinicalTrials.gov alone, so a trial\'s age does not determine whether its data can be ' +
      'used. An older trial with retrievable, non-firewalled data is eligible; a recent trial without usable ' +
      'outcome data is not.</div>' +
      '<div style="margin-top:8px;">What remains open is a genuine <em>scope</em> question, not a date one: the ' +
      'protocol as written asks a stable-ASCVD/PAD dual-pathway question, while COMMANDER HF (decompensated ' +
      'HFrEF, placebo comparator) and ATLAS ACS 2 (acute ACS, thienopyridine background) answer a broader one. ' +
      'Either widen the protocol to "very-low-dose rivaroxaban across ASCVD/ACS/PAD/HF" with setting-stratified ' +
      'analysis prespecified, or restrict the synthesis to COMPASS + VOYAGER-PAD. Both are defensible; the ' +
      'current mismatch between the stated scope and the analysed set is not.</div>');
  }

  // ------------------------------------------------- C. small-k validity gate
  var SUPPRESS = {
    "plot-egger": "Egger's regression on k=4 has almost no power; the intercept and its p-value are not interpretable.",
    "plot-funnel": "A funnel plot cannot be assessed for asymmetry at k=4. Any statement of 'visual symmetry' is unjustified.",
    "plot-metareg": "Meta-regression with k=4 has ~2 residual degrees of freedom; coefficients are uninterpretable.",
    "meta-regression-panel": "Meta-regression with k=4 is uninterpretable (covariates approach or exceed the number of studies).",
    "funnel-diagnostics-panel": "Publication-bias diagnostics (funnel, Egger, trim-and-fill) require k>=10. Trim-and-fill imputing studies at k=4 is unstable and must not be read as evidence for or against bias.",
    "plot-subgroup": "Each subgroup here contains a single trial, so subgroup contrasts are between-trial comparisons confounded by population, comparator and endpoint. These are not valid subgroup analyses.",
    "subgroup-interaction-panel": "Subgroups contain one trial each; interaction tests are confounded with trial identity and endpoint definition.",
    "plot-copas": "Copas selection modelling requires k>=15.",
    "plot-tsa": "Trial-sequential analysis assumes a common endpoint across trials. These four trials do not share an endpoint, so the required information size and the resulting 'evidence is sufficient' verdict are not meaningful here.",
    "plot-nnt": "An NNT cannot be derived from a pooled hazard ratio without a stated follow-up horizon and a stated baseline risk. Control event rates here are also incomplete. Any single NNT figure shown is not usable.",
    "plot-power": "Post-hoc power computed from the observed effect is not informative.",
    "plot-posterior": "The Bayesian prior is not specified (source, distribution and parameters are undocumented), so the posterior is not reproducible.",
    "bayesian-sensitivity-panel": "Prior specification is undocumented; treat as illustrative only.",
    "plot-baujat": "Influence diagnostics at k=4 are dominated by which single trial is dropped.",
    "plot-loo": "With k=4, leave-one-out is a sensitivity display, not an outlier test.",
    "plot-galbraith": "Radial/Galbraith plots need more studies to show a pattern.",
    "plot-labbe": "L'Abbe plots mix trials whose endpoints and follow-up differ."
  };

  function stampPanel(id, reason) {
    var node = document.getElementById(id);
    if (!node) return false;
    var host = node.closest ? (node.closest(".chart-container") || node.parentElement) : node.parentElement;
    if (!host) host = node;
    var mark = "rv-gate-" + id;
    if (document.getElementById(mark)) return true;
    var note = el("div", { id: mark, style: WARN_CSS + "margin:6px 0;" },
      '<strong>EXPLORATORY ONLY (k=' + K + ').</strong> ' + reason);
    host.parentElement ? host.parentElement.insertBefore(note, host) : host.appendChild(note);
    node.style.opacity = "0.45";
    node.setAttribute("data-rv-suppressed", "1");
    return true;
  }

  function applyGate() {
    Object.keys(SUPPRESS).forEach(function (id) { stampPanel(id, SUPPRESS[id]); });
  }

  // ------------------------------------------------------------- D. PRISMA
  function trialCounts() {
    var R = window.RapidMeta;
    var trials = (R && R.state && R.state.trials) || [];
    var total = trials.length;
    var excluded = trials.filter(function (t) { return t.status === "exclude"; }).length;
    var included = 4;
    var awaiting = Math.max(0, total - excluded - included);
    return { total: total, excluded: excluded, included: included, awaiting: awaiting };
  }

  function rebuildPrisma() {
    var host = document.getElementById("prismaFlowContainer");
    if (!host) return;
    if (host.getAttribute("data-rv-rebuilt") === "1") return;
    var c = trialCounts();
    if (!c.total) return;

    var box = function (x, y, w, h, label, n, fill) {
      return '<rect x="' + x + '" y="' + y + '" width="' + w + '" height="' + h + '" rx="6" fill="' +
        (fill || "#1e293b") + '" stroke="#475569"></rect>' +
        '<text x="' + (x + w / 2) + '" y="' + (y + h / 2 - 5) + '" text-anchor="middle" fill="#e2e8f0" font-size="11">' +
        label + '</text>' +
        '<text x="' + (x + w / 2) + '" y="' + (y + h / 2 + 11) + '" text-anchor="middle" fill="#94a3b8" font-size="10">n = ' +
        n + '</text>';
    };
    var arrow = function (x1, y1, x2, y2) {
      return '<line x1="' + x1 + '" y1="' + y1 + '" x2="' + x2 + '" y2="' + y2 +
        '" stroke="#64748b" stroke-width="1.5" marker-end="url(#rv-arrow)"></line>';
    };

    var svg = '<svg viewBox="0 0 720 420" width="100%" style="background:transparent;font-family:ui-sans-serif,system-ui,sans-serif;">' +
      '<defs><marker id="rv-arrow" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto">' +
      '<polygon points="0 0, 10 3, 0 6" fill="#64748b"></polygon></marker></defs>' +
      box(230, 20, 260, 46, "Records in screening queue", c.total) +
      arrow(360, 66, 360, 96) +
      box(230, 96, 260, 46, "Title/abstract screened", c.total) +
      box(520, 96, 180, 46, "Excluded at screening", c.excluded) +
      arrow(490, 119, 520, 119) +
      box(20, 96, 190, 46, "Awaiting adjudication", c.awaiting, "#422006") +
      arrow(360, 142, 360, 172) +
      box(230, 172, 260, 46, "Assessed for eligibility", c.included) +
      box(520, 172, 180, 46, "Excluded at eligibility", 0) +
      arrow(490, 195, 520, 195) +
      arrow(360, 218, 360, 248) +
      box(230, 248, 260, 46, "Included in synthesis", c.included, "#1e3a8a") +
      '<text x="360" y="322" text-anchor="middle" fill="#94a3b8" font-size="10">Balance: ' + c.total +
      ' = ' + c.excluded + ' excluded + ' + c.awaiting + ' awaiting + ' + c.included + ' assessed</text>' +
      '<text x="360" y="342" text-anchor="middle" fill="#fbbf24" font-size="9">' +
      'No full-text eligibility stage was performed - extraction is limited to registry records and abstracts.</text>' +
      '<text x="360" y="358" text-anchor="middle" fill="#fbbf24" font-size="9">' +
      'The 4 analysed trials entered as a preloaded landmark reference set, not reproducibly from the database searches.</text>' +
      '<text x="360" y="374" text-anchor="middle" fill="#fbbf24" font-size="9">' +
      'Screening decisions were signed by an autoscreener, not by two independent human reviewers.</text>' +
      '</svg>';

    host.innerHTML = svg;
    host.setAttribute("data-rv-rebuilt", "1");
    if (!document.getElementById("rv-prisma-note")) {
      host.parentElement.insertBefore(
        el("div", { id: "rv-prisma-note", style: WARN_CSS },
          "<strong>PRISMA rebuilt for internal consistency.</strong> The previous diagram reused the same " +
          "exclusion count at both the screening and the eligibility stage, which made the flow arithmetically " +
          "impossible, and it reported a full-text assessment stage that this review's declared data boundary " +
          "(registry records + abstracts only) rules out. Counts that were never recorded are shown as 0 or as " +
          "'awaiting adjudication' rather than being inferred."),
        host);
    }
  }

  // ------------------------------------------- E. Paper Studio quarantine
  function quarantinePaperStudio() {
    var tab = document.getElementById("tab-paper") || document.querySelector('[id*="paper"]');
    if (!tab) return;
    if (document.getElementById("rv-ps-note")) return;
    if (!/finerenone/i.test(tab.innerHTML || "")) return;
    tab.insertBefore(
      el("div", { id: "rv-ps-note", style: STOP_CSS },
        "<strong>Worked-example text below is NOT this study.</strong> The shared Paper Studio teaching module " +
        "ships a complete finerenone / chronic-kidney-disease worked example (title, abstract, methods, " +
        "discussion and conclusion) to illustrate manuscript structure. This review is about " +
        "<strong>rivaroxaban 2.5 mg BID</strong> in vascular disease across 4 trials. Do not paste the example " +
        "text into an export: doing so would produce a manuscript describing the wrong drug, the wrong " +
        "population and the wrong effect estimate."),
      tab.firstChild);
  }

  // -------------------------------------- F. published CI vs plotted CI note
  var PUBLISHED_CI = [
    ["COMPASS", "0.76 (0.66-0.86)", "CV death, stroke, or MI"],
    ["VOYAGER-PAD", "0.85 (0.76-0.96)", "ALI, amputation, MI, ischaemic stroke, or CV death"],
    ["COMMANDER HF", "0.94 (0.84-1.05)", "All-cause death, MI, or stroke"],
    ["ATLAS ACS 2", "0.84 (0.72-0.97)", "CV death, MI, or stroke (2.5 mg arm)"]
  ];

  function forestNote() {
    var host = document.getElementById("plot-forest");
    if (!host || document.getElementById("rv-forest-note")) return;
    var rows = PUBLISHED_CI.map(function (r) {
      return '<tr><td style="padding:3px 8px;"><strong>' + r[0] + '</strong></td>' +
        '<td style="padding:3px 8px;font-family:ui-monospace,monospace;">' + r[1] + '</td>' +
        '<td style="padding:3px 8px;color:#94a3b8;">' + r[2] + '</td></tr>';
    }).join("");
    var note = el("div", { id: "rv-forest-note", style: WARN_CSS },
      '<strong>Study intervals on the plot are not the published intervals.</strong> ' +
      'The forest reconstructs each study\'s interval from a standard error assumed symmetric on the log scale, ' +
      'so it can differ from the published interval in the second decimal place (COMPASS plots as about ' +
      '0.67-0.87 against a published 0.66-0.86). That is a reconstruction artefact, not a different result - but ' +
      'quote the published interval, not the plotted one. Published values:' +
      '<table style="width:100%;border-collapse:collapse;font-size:11px;margin-top:6px;"><tbody>' + rows +
      '</tbody></table>' +
      '<div style="margin-top:6px;">Each row is a <em>different endpoint</em>. The diamond is not a pooled ' +
      'CV-death/MI/stroke effect.</div>');
    host.parentElement.insertBefore(note, host.nextSibling);
  }

  // ------------------------------------- G. neutralise overclaiming summaries
  var CLAIM_FIXES = [
    [/TSA:\s*Evidence sufficient[^<]*/gi,
      "TSA: NOT INTERPRETABLE (trials do not share an endpoint; required information size assumes they do)"],
    [/Copas \(exploratory\):\s*Robust/gi, "Copas: NOT COMPUTABLE (needs k>=15)"],
    [/No significant interaction\./gi,
      "Subgroup test not interpretable: each subgroup holds a single trial, so differences are confounded with trial, population and endpoint."],
    [/The result is statistically significant, suggesting a 15% lower hazard/gi,
      "The pooled interval excludes 1, but the prediction interval (0.66-1.09) crosses 1 and the four inputs are different endpoints, so this is not a robust 15% reduction across settings"],
    [/asymmetry may reflect heterogeneity/gi,
      "trim-and-fill imputing studies at k=4 is unstable and must not be read as evidence about publication bias"],
    [/clinical cardiovascular or renal endpoint/gi, "clinical cardiovascular or limb endpoint"],
    [/Very Low[^.]{0,80}reflects confidence[^.]*\./gi,
      "Very Low certainty means the true effect is likely to be substantially different from this estimate."]
  ];

  function fixClaims() {
    var walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, null);
    var nodes = [], n;
    while ((n = walker.nextNode())) nodes.push(n);
    nodes.forEach(function (node) {
      if (node.parentElement && node.parentElement.closest("[id^=rv-]")) return;
      var v = node.nodeValue;
      if (!v || v.length < 6) return;
      var out = v;
      CLAIM_FIXES.forEach(function (f) { out = out.replace(f[0], f[1]); });
      if (out !== v) node.nodeValue = out;
    });
  }

  // ------------------------------- G2. retire date-based exclusions in state
  // The "exclude pre-2015" rule has been removed from the protocol, but users
  // who opened this app earlier carry its verdicts in localStorage. Removing
  // the filter from the code is not enough: any record already excluded on
  // date must be returned to the screening queue, or the retired rule keeps
  // silently deciding eligibility for anyone with saved state.
  var ERA_RE = /era restriction|pre-?2015/i;

  function retireDateExclusions() {
    var R = window.RapidMeta;
    if (!R || !R.state || !Array.isArray(R.state.trials)) return;
    if (R.state._rvDateAxisRetired) return;
    var restored = 0, cleared = 0;
    R.state.trials.forEach(function (t) {
      if (!t || !ERA_RE.test(String(t.reason || ""))) return;
      if (t.status === "exclude") {
        t.status = "search";
        restored += 1;
      }
      t.reason = "";
      cleared += 1;
    });
    R.state._rvDateAxisRetired = true;
    if (cleared && typeof R.save === "function") {
      try { R.save(); } catch (e) { /* non-fatal: state is corrected in memory */ }
    }
    if (cleared && window.console && console.info) {
      console.info(TAG, "retired date-based eligibility: " + cleared +
        " reason(s) cleared, " + restored + " record(s) returned to screening");
    }
    if (restored && !document.getElementById("rv-date-axis-note")) {
      var anchor = document.getElementById("rv-eligibility-ledger");
      if (anchor) {
        anchor.parentElement.insertBefore(
          el("div", { id: "rv-date-axis-note", style: WARN_CSS },
            "<strong>Saved screening state was updated.</strong> " + restored +
            " record(s) previously excluded under the retired \"pre-2015\" rule have been returned " +
            "to the screening queue and must be re-adjudicated on scope and data availability. " +
            "Publication date is no longer an eligibility criterion."),
          anchor.nextSibling);
      }
    }
  }

  // ------------------------------------------------------------- H. PICO
  // The protocol PICO cells shipped empty while the manuscript claimed a
  // defined question. Fill them with the scope the review actually operates,
  // and state where the analysed set departs from it.
  var PICO = {
    "Population": "Adults with atherosclerotic cardiovascular disease. Scope as written is STABLE " +
      "ASCVD or PAD; the analysed set also contains acute ACS (ATLAS ACS 2) and decompensated " +
      "HFrEF with CAD (COMMANDER HF), which fall outside it.",
    "Intervention": "Rivaroxaban 2.5 mg twice daily (very-low-dose, a direct oral factor Xa " +
      "inhibitor), given with aspirin in COMPASS and VOYAGER-PAD; given without an aspirin " +
      "requirement in COMMANDER HF; given on aspirin +/- a thienopyridine in ATLAS ACS 2.",
    "Comparator": "Aspirin alone (COMPASS, VOYAGER-PAD) or placebo on background therapy " +
      "(COMMANDER HF, ATLAS ACS 2). These are NOT the same comparator.",
    "Primary Outcome": "Each trial's own registered primary composite. These differ between " +
      "trials and are NOT pooled as a harmonised 3-point MACE.",
    "Subgroup Plan": "By clinical setting (stable CAD/PAD, post-revascularisation PAD, HF+CAD, " +
      "recent ACS). NOTE: each stratum contains exactly one trial, so these are between-trial " +
      "comparisons confounded with endpoint and comparator, not valid subgroup analyses."
  };

  function fillPico() {
    var host = document.getElementById("tab-protocol");
    if (!host) return;
    var cells = host.querySelectorAll("td,th");
    for (var i = 0; i < cells.length; i++) {
      var label = cells[i].textContent.trim();
      if (!PICO.hasOwnProperty(label)) continue;
      var row = cells[i].closest ? cells[i].closest("tr") : null;
      if (!row || row.children.length < 2) continue;
      var val = row.children[1];
      if (val.getAttribute("data-rv-filled") === "1") continue;
      if (val.textContent.trim().length > 0) continue;
      val.textContent = PICO[label];
      val.style.color = "#cbd5e1";
      val.setAttribute("data-rv-filled", "1");
    }
  }

  // ------------------------------------------------------ I. RoB2 / GRADE
  // Every trial carries an identical domain vector derived from registry design
  // fields (robSource: "AACT designs: alloc=RANDOMIZED, masking=QUADRUPLE...").
  // That is an auto-fill, not a Risk-of-Bias 2 assessment, and the certainty
  // rating disagrees between tabs. Say so rather than let "Low" read as done.
  function robGradeNote() {
    var host = document.getElementById("plot-rob-bar") ||
      document.getElementById("tab-analysis");
    if (!host || document.getElementById("rv-rob-note")) return;
    var note = el("div", { id: "rv-rob-note", style: STOP_CSS },
      '<div style="font-weight:700;margin-bottom:6px;">Risk of bias and GRADE are not completed assessments</div>' +
      '<div><strong>RoB 2.</strong> All four trials carry an identical domain vector auto-derived from ' +
      'ClinicalTrials.gov design fields (allocation, masking, assessor masking). No domain has a human ' +
      'judgement, no signalling questions were answered, and there is no second reviewer or adjudication. ' +
      'A displayed "Low" here means "the registry says it was randomised and quadruple-masked", not "this ' +
      'trial was assessed as low risk of bias". The auto-fill also could not detect the endpoint and ' +
      'denominator errors that were present in this app, which is the kind of problem RoB 2 domain 5 ' +
      '(selection of the reported result) exists to catch.</div>' +
      '<div style="margin-top:8px;"><strong>GRADE.</strong> The same body of evidence was rated Low in the ' +
      'Analysis Suite, Moderate in Scientific Output and Very Low in Paper Studio. Until these are derived ' +
      'from one set of corrected judgements, no certainty rating in this app should be quoted. On the ' +
      'corrected inputs the defensible rating for the pooled primary composite is <strong>LOW at best</strong>: ' +
      'downgrade for indirectness (four different endpoints, four different populations, two different ' +
      'comparators) and for imprecision (the prediction interval crosses 1). The single-trial COMPASS stroke ' +
      'result must not carry a High rating - one trial cannot be the stroke evidence base when three other ' +
      'trials also report stroke.</div>');
    host.parentElement ? host.parentElement.insertBefore(note, host) : host.appendChild(note);
  }

  // ------------------------------------------------------- mount + observe
  function mountBanners() {
    var analysis = document.getElementById("tab-analysis") ||
      document.querySelector('[id*="analysis"]');
    if (analysis && once("rv-endpoint-banner")) {
      var b = endpointBanner();
      if (b) analysis.insertBefore(b, analysis.firstChild);
    }
    if (analysis && once("rv-eligibility-ledger")) {
      var e = eligibilityLedger();
      if (e) {
        var anchor = document.getElementById("rv-endpoint-banner");
        anchor ? anchor.parentElement.insertBefore(e, anchor.nextSibling)
               : analysis.insertBefore(e, analysis.firstChild);
      }
    }
  }

  function tick() {
    try {
      retireDateExclusions();
      mountBanners();
      applyGate();
      rebuildPrisma();
      quarantinePaperStudio();
      forestNote();
      fillPico();
      robGradeNote();
      fixClaims();
    } catch (err) {
      if (window.console && console.warn) console.warn(TAG, err);
    }
  }

  function boot() {
    tick();
    [400, 1200, 2500, 5000, 9000].forEach(function (ms) { setTimeout(tick, ms); });
    document.addEventListener("click", function () { setTimeout(tick, 350); }, true);
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
})();
