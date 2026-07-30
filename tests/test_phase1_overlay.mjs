/**
 * BEHAVIOURAL tests for the Phase-1 bootstrap that actually SHIPS into the apps.
 *
 * Why this file exists: the 131 tests in test_rapidmeta_guards.mjs test the LIBRARY. Gate finding
 * P1-3 was library-correct / wiring-wrong — `G21_reconcilePersistedState` computed `mustRederive`
 * and returned `pooledResult:null`, and the bootstrap never read either, so a returning visitor's
 * persisted pooled estimate survived. A library-only suite cannot see that class of defect.
 *
 * These tests extract the real bootstrap out of `overlay_js()` (the exact text injected into every
 * app), run it against a minimal DOM/window double, and assert on OBSERVED BEHAVIOUR.
 *
 * Run:  node --test tests/test_phase1_overlay.mjs
 */
import { test, describe, before } from "node:test";
import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { createRequire } from "node:module";
import vm from "node:vm";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, "..");
const require = createRequire(import.meta.url);

/** Ask the patcher for the exact block it injects, so these tests can never drift from it. */
function shippedOverlay() {
  // NOTE: do NOT wrap sys.stdout here. The module wraps it once, guarded by a sentinel; a second
  // wrap closes the first one's buffer and every print raises "I/O operation on closed file" -
  // the same double-import trap recorded in rules/lessons.md. Set the encoding via the env.
  const py =
    "import sys;sys.path.insert(0,'scripts');" +
    "import phase1_engine_patch as p;" +
    "sys.stdout.write(p.overlay_js(open('assets/js/rapidmeta-guards.js',encoding='utf-8').read()))";
  return execFileSync("python", ["-c", py], {
    cwd: ROOT, encoding: "utf-8", maxBuffer: 64 * 1024 * 1024,
    env: Object.assign({}, process.env, { PYTHONIOENCODING: "utf-8" })
  });
}

let BOOTSTRAP = null;
before(() => {
  const block = shippedOverlay();
  const m = block.match(/<script>\/\* RapidMeta Phase-1 bootstrap[\s\S]*?<\/script>/);
  assert.ok(m, "could not locate the bootstrap script in the shipped overlay");
  BOOTSTRAP = m[0].slice("<script>".length, -"</script>".length);
});

/** Minimal DOM/window double. Only what the bootstrap touches. */
function makeEnv(opts = {}) {
  const store = Object.assign({}, opts.localStorage || {});
  const elements = Object.assign({}, opts.elements || {});
  const listeners = {};
  const badge = opts.badge === null ? null : Object.assign({
    textContent: "", innerText: "", style: { background: "" },
    _children: [],
    appendChild(n) { this._children.push(n); },
    querySelector(sel) {
      return this._children.find((c) => sel.includes(c._attr)) || null;
    }
  }, opts.badge || {});
  if (badge) elements["rapidmeta-integrity-badge"] = badge;

  const win = {
    RapidMetaGuards: require(path.join(ROOT, "assets/js/rapidmeta-guards.js")),
    __verdict: opts.verdict,
    __quarantinedTrials: opts.quarantined,
    CTGOV_EVIDENCE_REGISTRY: opts.watchlist,
    RapidMeta: opts.rapidMeta,
    console: { warn() {}, log() {} },
    addEventListener(ev, fn) { (listeners[ev] = listeners[ev] || []).push(fn); },
    setTimeout: (fn) => { (listeners.__timers = listeners.__timers || []).push(fn); return 0; },
    localStorage: {
      getItem: (k) => (k in store ? store[k] : null),
      setItem: (k, v) => { store[k] = String(v); },
      _store: store
    }
  };
  win.window = win;
  const doc = {
    readyState: "complete",
    title: opts.title || "RapidMeta | Test",
    documentElement: { innerHTML: opts.html || "" },
    body: { innerText: "" },
    getElementById: (id) => elements[id] || null,
    querySelectorAll: () => [],
    createElement: () => ({ _attr: null, style: { cssText: "" }, textContent: "",
                            setAttribute(k, v) { if (k === "data-rm-guard") this._attr = v; } }),
    addEventListener(ev, fn) { (listeners[ev] = listeners[ev] || []).push(fn); }
  };
  win.document = doc;
  const ctx = vm.createContext(win);
  vm.runInContext(BOOTSTRAP, ctx);
  return { win, doc, badge, store, listeners, fireTimers() { (listeners.__timers || []).forEach((f) => f()); } };
}

/* ============================================================ P1-3 · mustRederive is consumed */

describe("bootstrap G21 — the persisted pooled estimate must not survive (gate P1-3)", () => {
  const KEY = "rapid_meta_x_v12_0";

  test("a persisted __pooledResult is purged even when NOTHING is quarantined or dropped", () => {
    let saved = null;
    const state = {
      trials: [{ id: "NCT01764633", status: "include", data: {} }],
      __pooledResult: { rr: 0.03, lci: 0.0, uci: 0.52 }
    };
    const env = makeEnv({
      rapidMeta: {
        realData: { NCT01764633: {} },
        state,
        save() { saved = JSON.parse(JSON.stringify(this.state)); }
      },
      quarantined: {},
      verdict: { verdict: "STABLE", counts: { n_trials_seen: 1 }, reasons: [] },
      localStorage: { [KEY]: "{}" }
    });
    const applied = env.win.__rmGuardsApplied;
    assert.equal(applied.G21_persisted_state.rederived, true,
      "mustRederive must be consumed — this is the exact wiring the gate found missing");
    assert.equal(state.__pooledResult, null, "the withdrawn RR 0.03 must be gone from live state");
    assert.ok(saved, "save() must be called so the purge reaches localStorage");
    assert.equal(saved.__pooledResult, null);
    assert.ok(saved.__rmLedgerFp, "a ledger fingerprint must be persisted");
  });

  test("a quarantined row is purged from the persisted profile", () => {
    const state = {
      trials: [
        { id: "NCT02220725", status: "include", data: { pubHR: 73.83 } },
        { id: "NCT01764633", status: "include", data: {} }
      ]
    };
    const env = makeEnv({
      rapidMeta: { realData: { NCT01764633: {} }, state, save() {} },
      quarantined: { NCT02220725: {} },
      verdict: { verdict: "UNCERTAIN", counts: { n_trials_seen: 1 }, reasons: ["x"] }
    });
    const r = env.win.__rmGuardsApplied.G21_persisted_state;
    assert.equal(r.purged, 1);
    assert.deepEqual(state.trials.map((t) => t.id), ["NCT01764633"]);
  });

  test("a clean, current profile is left alone and does not re-derive", () => {
    const G = require(path.join(ROOT, "assets/js/rapidmeta-guards.js"));
    const fp = G.G21_ledgerFingerprint(["NCT01764633"], [], "RapidMeta | Test");
    const state = { trials: [{ id: "NCT01764633", status: "include" }], __rmLedgerFp: fp };
    const env = makeEnv({
      rapidMeta: { realData: { NCT01764633: {} }, state, save() {}, version: "RapidMeta | Test" },
      quarantined: {},
      verdict: { verdict: "STABLE", counts: { n_trials_seen: 1 }, reasons: [] }
    });
    const r = env.win.__rmGuardsApplied.G21_persisted_state;
    assert.equal(r.rederived, false);
    assert.equal(r.purged, 0);
    assert.equal(r.dropped, 0);
  });
});

/* ==================================================== P0-2 · G18 fail-closed and never frozen */

describe("bootstrap G18 — fail-closed, and a PASS never freezes (gate P0-2)", () => {
  test("an app with NO ledger reports NOT-APPLICABLE, never PASS", () => {
    const env = makeEnv({
      rapidMeta: { realData: {}, state: { trials: [] }, save() {} },
      verdict: { verdict: "NO_DATA", counts: { n_trials_seen: 0 }, reasons: [] },
      badge: { innerText: "NO DATA — THIS IS NOT AN INTEGRITY PASS", textContent: "NO DATA" }
    });
    const v = env.win.__rmGuardsApplied.G18_G12_gate;
    assert.equal(v, "NOT-APPLICABLE");
    assert.notEqual(v, "PASS");
  });

  test("NOT-APPLICABLE is NOT settled, so a late hydrate re-runs the gate", () => {
    const rm = { realData: {}, state: { trials: [] }, save() {} };
    const env = makeEnv({
      rapidMeta: rm,
      verdict: { verdict: "NO_DATA", counts: { n_trials_seen: 0 }, reasons: [] }
    });
    assert.equal(env.win.__rmGuardsApplied.G18_G12_gate, "NOT-APPLICABLE");
    // the ledger arrives late, exactly as it does in a real app
    rm.realData = { NCT01: {}, NCT02: {} };
    env.win.__verdict = { verdict: "STABLE", counts: { n_trials_seen: 2 }, reasons: [] };
    env.fireTimers();
    assert.equal(env.win.__rmGuardsApplied.G18_G12_gate, "PASS",
      "the retry must actually re-run — a frozen NOT-APPLICABLE would never become a real verdict");
  });

  test("a PASS is re-checked on the late hydrate and can BECOME a block", () => {
    const rm = { realData: { NCT01: {}, NCT02: {} }, state: { trials: [] }, save() {} };
    const env = makeEnv({
      rapidMeta: rm,
      verdict: { verdict: "STABLE", counts: { n_trials_seen: 2 }, reasons: [] },
      badge: { innerText: "ok", textContent: "ok", style: { background: "#7c2d12" } }
    });
    assert.equal(env.win.__rmGuardsApplied.G18_G12_gate, "PASS");
    // hydrate reveals a NULLED row — the state the early pass could not see
    rm.realData = { NCT01: {}, "NULLED:NCT02": {} };
    env.fireTimers();
    assert.equal(env.win.__rmGuardsApplied.G18_G12_gate, "BLOCKED",
      "a frozen PASS is exactly the false assurance the gate blocked on");
  });

  test("a real integrity failure suppresses the pooled surfaces and recolours the badge", () => {
    const resOr = { textContent: "0.85" };
    const env = makeEnv({
      rapidMeta: { realData: { NCT01: {}, "NULLED:NCT02": {} }, state: { trials: [] }, save() {} },
      verdict: { verdict: "STABLE", counts: { n_trials_seen: 2 }, reasons: [] },
      elements: { "res-or": resOr },
      badge: { innerText: "x", textContent: "x", style: { background: "#15803d" } }
    });
    assert.equal(env.win.__rmGuardsApplied.G18_G12_gate, "BLOCKED");
    assert.equal(resOr.textContent, "--", "the pooled estimate must be suppressed");
    assert.equal(env.badge.style.background, "#7c2d12");
    assert.ok(env.win.__rmGuardBlocked);
  });
});

/* ================================================================== T2 allowlist fails closed */

describe("bootstrap __rmGuardEstimandOK — the allowlist T2 substitutes in", () => {
  test("an untagged estimand is NOT admitted (fails closed)", () => {
    const env = makeEnv({ rapidMeta: { realData: {}, state: { trials: [] }, save() {} } });
    assert.equal(env.win.__rmGuardEstimandOK({}), false);
    assert.equal(env.win.__rmGuardEstimandOK({ estimandType: "RATE_RATIO" }), false);
    assert.equal(env.win.__rmGuardEstimandOK({ estimandType: "HR" }), true);
  });
});

/* ============================================================ G07 must not be dead code again */

describe("bootstrap G07 — reports the TEXTUAL neutralisation, not a flag nothing reads", () => {
  test("reports NEUTRALISED-BY-T4 when the T4 marker is in the document", () => {
    const env = makeEnv({
      html: "<script>/* RM-PHASE1 G07: disabled - ... */</script>",
      rapidMeta: { realData: {}, state: { trials: [] }, save() {} }
    });
    assert.equal(env.win.__rmGuardsApplied.G07_pooling_repair, "NEUTRALISED-BY-T4");
  });

  test("the dead __rmPoolingRepairDisabled flag is gone from the shipped bootstrap", () => {
    assert.equal(/__rmPoolingRepairDisabled/.test(BOOTSTRAP), false);
  });
});
