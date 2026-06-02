/* NMA engine <-> netmeta parity harness (VAL-6).
 *
 * Runs rapidmeta-nma-engine-v2.js in node (no browser, no R) on every NMA
 * dataset that has BOTH input trials (nma/data/<slug>_trials.csv) and a stored
 * netmeta reference (nma/validation/<slug>_netmeta_results.json), and asserts
 * the engine reproduces netmeta's numbers.
 *
 * IMPORTANT — network correspondence. Parity is only meaningful when the engine
 * is run on the SAME network netmeta used. The reference is auto-detected from
 * the results (the treatment with te_random_vs_ref == 0), and the engine
 * network is validated against the reference treatment set. When the committed
 * CSV is a SUBSET of (or otherwise differs from) the reference network, the
 * dataset is reported as DATA-MISMATCH and NOT gated — a subset network yields
 * different indirect-evidence contrasts, so a mismatch there is a data problem,
 * not an engine bug. (As of writing, 5 of 6 committed CSVs are subsets of their
 * stored references; reconcile nma/data vs nma/validation, or regenerate the
 * references from the committed CSVs with R/netmeta, to widen coverage.)
 *
 * Gated for corresponding datasets (deterministic, direction-independent):
 *   - contrasts  te_random_vs_ref[trt]  (log scale for HR/OR/RR, native for MD)
 *   - tau2
 * Reported with a loose tolerance (SUCRA is a 100k-sample MC, no seed):
 *   - SUCRA per treatment, under the better-matching rank direction.
 *
 * Exit non-zero on any gated mismatch among corresponding datasets. This
 * validates the JS engine against an independent netmeta computation — unlike
 * parity_test_all_sidecars.R (metafor-vs-metafor) and webr-validator.js
 * (advisory, in-browser).
 */
import { readFileSync } from 'fs';
import { createRequire } from 'module';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, '..');
const require = createRequire(import.meta.url);
require(join(ROOT, 'rapidmeta-nma-engine-v2.js')); // attaches globalThis.RapidMetaNMA
const NMA = globalThis.RapidMetaNMA;

// slug -> SUCRA rank direction (higher_better). Reference is auto-detected.
const DATASETS = [
  { slug: 'btki_cll_nma',       higher: false },
  { slug: 'antiamyloid_ad_nma', higher: false },
  { slug: 'antivegf_namd_nma',  higher: true  },
  { slug: 'il_psoriasis_nma',   higher: true  },
  { slug: 'incretins_t2d_nma',  higher: false },
  { slug: 'jaki_ra_nma',        higher: true  },
];

const TOL_CONTRAST = 5e-3; // log/native scale; engine documents |dHR|<1e-3
const TOL_TAU2     = 5e-3; // absolute
const TOL_SUCRA    = 0.04; // 4 points; MC noise at N=1e5 is ~0.002

function parseCsv(path) {
  const lines = readFileSync(path, 'utf8').trim().split(/\r?\n/);
  const head = lines[0].split(',');
  return lines.slice(1).map(line => {
    const cells = line.split(',');
    const o = {};
    head.forEach((h, i) => (o[h] = cells[i]));
    return {
      studlab: o.studlab, treat1: o.treat1, treat2: o.treat2,
      TE: parseFloat(o.te_for_netmeta), seTE: parseFloat(o.seTE_for_netmeta),
    };
  });
}

function detectReference(R) {
  // netmeta's reference is the treatment with te_random_vs_ref == 0.
  for (let i = 0; i < R.treatments.length; i++) {
    if (Math.abs(Number(R.te_random_vs_ref[i])) < 1e-12) return R.treatments[i];
  }
  return null;
}

function approx(a, b, tol) { return Number.isFinite(a) && Number.isFinite(b) && Math.abs(a - b) <= tol; }

const failures = [];      // real parity failures (gate)
const dataMismatch = [];  // network does not correspond (not gated)
let gated = 0;

for (const { slug, higher } of DATASETS) {
  let trials, R;
  try {
    trials = parseCsv(join(ROOT, 'nma', 'data', `${slug.replace('_nma', '')}_nma_trials.csv`));
    R = JSON.parse(readFileSync(join(ROOT, 'nma', 'validation', `${slug}_netmeta_results.json`), 'utf8'));
  } catch (e) {
    failures.push(`${slug}: could not load inputs (${e.message})`);
    continue;
  }

  const ref = detectReference(R);
  if (!ref) { failures.push(`${slug}: could not detect netmeta reference (no te==0)`); continue; }

  // Network correspondence: engine treatment set must equal the reference set.
  const csvTrts = new Set();
  trials.forEach(t => { csvTrts.add(t.treat1); csvTrts.add(t.treat2); });
  const refTrts = new Set(R.treatments);
  const missing = [...refTrts].filter(t => !csvTrts.has(t));
  const extra = [...csvTrts].filter(t => !refTrts.has(t));
  if (missing.length || extra.length) {
    dataMismatch.push(`${slug}: CSV network (${csvTrts.size}) != reference network (${refTrts.size}); ` +
      `ref=${ref}; missing_from_csv=[${missing.join(',')}] extra_in_csv=[${extra.join(',')}]`);
    continue;
  }

  let fit;
  try {
    fit = NMA.fit({ trials, reference: ref, method_tau: 'REML', hksj: true, alpha: 0.05 });
  } catch (e) {
    failures.push(`${slug}: engine fit() threw: ${e.message}`);
    continue;
  }
  gated++;

  // contrasts (gated)
  for (let i = 0; i < R.treatments.length; i++) {
    const trt = R.treatments[i];
    if (trt === ref) continue;
    const eff = fit.effects[trt];
    if (!eff) { failures.push(`${slug}: engine missing contrast for ${trt}`); continue; }
    if (!approx(eff.est, Number(R.te_random_vs_ref[i]), TOL_CONTRAST)) {
      failures.push(`${slug}: contrast ${trt} vs ${ref}: engine ${eff.est.toFixed(5)} vs netmeta ` +
        `${Number(R.te_random_vs_ref[i]).toFixed(5)} (d=${Math.abs(eff.est - Number(R.te_random_vs_ref[i])).toExponential(2)})`);
    }
  }

  // tau2 (gated)
  if (!approx(fit.tau2, Number(R.tau2), TOL_TAU2)) {
    failures.push(`${slug}: tau2 engine ${fit.tau2.toExponential(3)} vs netmeta ${Number(R.tau2).toExponential(3)}`);
  }

  // SUCRA (gated, best-matching direction)
  if (R.sucra) {
    let best = null;
    for (const dir of [higher, !higher]) {
      const s = NMA.sucra(fit, { higher_better: dir, N: 100000 });
      let maxd = 0;
      for (const trt of Object.keys(R.sucra)) {
        if (s.sucra[trt] == null) continue;
        maxd = Math.max(maxd, Math.abs(s.sucra[trt] - R.sucra[trt]));
      }
      if (best === null || maxd < best.maxd) best = { dir, maxd };
    }
    if (best && best.maxd > TOL_SUCRA) {
      failures.push(`${slug}: SUCRA max diff ${best.maxd.toFixed(3)} (best dir higher_better=${best.dir}) exceeds ${TOL_SUCRA}`);
    }
  }
}

console.log(`NMA parity: ${gated} dataset(s) gated, ${dataMismatch.length} skipped for network mismatch.`);
if (dataMismatch.length) {
  console.log('\nDATA-MISMATCH (CSV network does not correspond to stored netmeta reference; NOT an engine bug):');
  for (const d of dataMismatch) console.log('  - ' + d);
}
if (failures.length) {
  console.log(`\nFAIL: ${failures.length} parity mismatch(es) among corresponding datasets:`);
  for (const f of failures) console.log('  - ' + f);
  process.exit(1);
}
if (gated === 0) {
  console.log('\nWARNING: 0 datasets had a CSV network matching their netmeta reference, so no ' +
    'engine-vs-netmeta parity was actually asserted. Reconcile nma/data vs nma/validation ' +
    '(or regenerate references from the committed CSVs with R/netmeta) to widen coverage.');
} else {
  console.log(`\nPASS: engine matches netmeta on contrasts + tau2 (+ SUCRA within tol) for ${gated} corresponding dataset(s).`);
}
process.exit(0);
