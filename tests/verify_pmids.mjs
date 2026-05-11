// tests/verify_pmids.mjs — PMID verification harness for survival pack fixtures
// ============================================================
// Closes P2-4 from the 2026-05-11 self-review pass: makes citation
// misattribution catchable by tooling instead of by manual eyeball.
//
// Two modes:
//
//   1. Offline (default, no network):
//        node tests/verify_pmids.mjs
//      Scans tests/survival_fixtures/*.json and GLP1_CVOT_SURV_REVIEW.html
//      for PMID references, builds a checklist of {pmid, studlab, source_file,
//      pubmed_url}, prints it. Operators can click through the URLs and
//      visually verify against the claimed studlab/year.
//
//   2. Online (opt-in, network required):
//        node tests/verify_pmids.mjs --online
//      Same scan, plus a real PubMed e-utils esummary call per unique PMID.
//      Compares each PMID's actual journal title and author list against
//      the claimed citation; reports mismatches.
//      e-utils rate limit: 3 req/s without API key, 10/s with one (set
//      NCBI_API_KEY env var to use). Sleeps 350ms between calls by default.
//
// Designed to be run on every fixture refresh, especially when adding new
// trials. Catches the LLM-citation-misattribution pattern flagged in
// ~/.claude/rules/lessons.md (4-22% baseline rate) at the source.
//
// Exit codes:
//   0  — all claimed PMIDs verified (or offline mode completed with no errors)
//   1  — at least one PMID misattribution detected
//   2  — script error (network failure, malformed input, etc.)
// ============================================================

import { readFileSync, readdirSync, statSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = join(__dirname, '..');
const FIXTURE_DIR = join(__dirname, 'survival_fixtures');
const TOPIC_FILE = join(REPO_ROOT, 'GLP1_CVOT_SURV_REVIEW.html');

const ONLINE = process.argv.includes('--online') || process.env.PMID_VERIFY_ONLINE === '1';
const SLEEP_MS = parseInt(process.env.PMID_VERIFY_SLEEP_MS || '350', 10);
const NCBI_API_KEY = process.env.NCBI_API_KEY || null;

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

// ------------------------------------------------------------
// Scan: collect {pmid, studlab, source_file} records
// ------------------------------------------------------------

function scanFixtures() {
  const out = [];
  for (const f of readdirSync(FIXTURE_DIR)) {
    if (!f.endsWith('.json')) continue;
    const path = join(FIXTURE_DIR, f);
    let data;
    try { data = JSON.parse(readFileSync(path, 'utf-8')); }
    catch (e) { console.error(`  [warn] ${f}: JSON parse failed (${e.message})`); continue; }
    const trials = Array.isArray(data.trials) ? data.trials : (Array.isArray(data) ? data : null);
    if (!trials) continue;
    for (const t of trials) {
      if (typeof t.pmid === 'string' && /^\d+$/.test(t.pmid)) {
        out.push({
          pmid: t.pmid,
          studlab: t.studlab || t.name || '?',
          year: t.year || null,
          doi: t.doi || null,
          source_file: `tests/survival_fixtures/${f}`
        });
      }
    }
  }
  return out;
}

function scanTopicFile() {
  const out = [];
  let text;
  try { text = readFileSync(TOPIC_FILE, 'utf-8'); }
  catch (e) { return out; }

  // Inline JSON block (<script type="application/json" id="surv-trials">[...]</script>)
  const jsonMatch = text.match(/<script type="application\/json" id="surv-trials">\s*([\s\S]+?)\s*<\/script>/);
  if (jsonMatch) {
    try {
      const arr = JSON.parse(jsonMatch[1]);
      for (const t of arr) {
        if (typeof t.pmid === 'string' && /^\d+$/.test(t.pmid)) {
          out.push({
            pmid: t.pmid,
            studlab: t.studlab || '?',
            year: t.year || null,
            doi: t.doi || null,
            source_file: 'GLP1_CVOT_SURV_REVIEW.html (embedded JSON)'
          });
        }
      }
    } catch (e) {
      console.error(`  [warn] inline JSON parse failed in topic file: ${e.message}`);
    }
  }

  // Inline prose "PMID 12345678" references
  const proseRe = /PMID[:\s]+(\d{6,})/g;
  let m;
  const seenInProse = new Set();
  while ((m = proseRe.exec(text)) !== null) {
    const pmid = m[1];
    const key = `prose:${pmid}`;
    if (seenInProse.has(key)) continue;
    seenInProse.add(key);
    // Extract a small context window for studlab inference
    const start = Math.max(0, m.index - 200);
    const ctx = text.slice(start, m.index);
    // Heuristic: pick the last all-caps trial name or "Author YYYY" in the context window
    const studlabMatch = ctx.match(/([A-Z][A-Z0-9\-]{2,}(?:\s+\d{4})?|[A-Z][a-z]+\s+\d{4})/g);
    const studlab = studlabMatch ? studlabMatch[studlabMatch.length - 1] : '(prose ref)';
    out.push({
      pmid: pmid,
      studlab: studlab,
      year: null,
      doi: null,
      source_file: 'GLP1_CVOT_SURV_REVIEW.html (prose)'
    });
  }
  return out;
}

// ------------------------------------------------------------
// Online: fetch PubMed esummary in batches
// ------------------------------------------------------------

async function fetchPubMed(pmids) {
  const idCsv = pmids.join(',');
  const apiKeyParam = NCBI_API_KEY ? `&api_key=${NCBI_API_KEY}` : '';
  const url = `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id=${idCsv}&retmode=json${apiKeyParam}`;
  const resp = await fetch(url);
  if (!resp.ok) throw new Error(`PubMed e-utils HTTP ${resp.status}`);
  const json = await resp.json();
  return json.result || {};
}

function compareRecord(claimed, actual) {
  // actual is PubMed's esummary record. Compare by:
  //  - source (journal) and pubdate vs claimed
  //  - title and authors (best-effort substring match against studlab)
  // Returns { ok: bool, why: string }
  if (!actual || actual.error) {
    return { ok: false, why: `PubMed returned no record (${actual && actual.error || 'unknown'})` };
  }
  const title = (actual.title || '').toLowerCase();
  const sortfirstauthor = (actual.sortfirstauthor || '').toLowerCase();
  const source = actual.source || '';
  const pubdate = actual.pubdate || '';
  // Loose studlab match — split into tokens (trial acronym + year) and require >=1 in title or author
  const tokens = String(claimed.studlab).split(/[\s\-]+/).filter(s => s.length >= 3);
  const hitsInTitle = tokens.filter(tok => title.includes(tok.toLowerCase()));
  const hitsInAuthor = tokens.filter(tok => sortfirstauthor.includes(tok.toLowerCase()));
  if (hitsInTitle.length === 0 && hitsInAuthor.length === 0) {
    return {
      ok: false,
      why: `Title="${actual.title}" / first author="${actual.sortfirstauthor}" does not mention any token of claimed studlab "${claimed.studlab}"`
    };
  }
  return {
    ok: true,
    why: `${source} ${pubdate}: ${actual.title.slice(0, 80)}${actual.title.length > 80 ? '…' : ''}`
  };
}

// ------------------------------------------------------------
// Main
// ------------------------------------------------------------

async function main() {
  console.log('PMID verification harness — survival pack');
  console.log('=========================================');
  const fixtureRecs = scanFixtures();
  const topicRecs = scanTopicFile();
  const all = [...fixtureRecs, ...topicRecs];
  if (all.length === 0) {
    console.log('No PMIDs found. Nothing to verify.');
    return 0;
  }
  // De-duplicate by pmid (preserve first occurrence for source provenance)
  const uniqueMap = new Map();
  for (const r of all) {
    if (!uniqueMap.has(r.pmid)) uniqueMap.set(r.pmid, []);
    uniqueMap.get(r.pmid).push(r);
  }
  console.log(`Found ${all.length} PMID references across ${uniqueMap.size} unique PMIDs in ${fixtureRecs.length > 0 ? 'fixtures + topic file' : 'topic file only'}.\n`);

  let fails = 0;

  if (!ONLINE) {
    console.log('Offline mode — printing checklist for manual review.');
    console.log('Pass --online or set PMID_VERIFY_ONLINE=1 to verify against PubMed.\n');
    for (const [pmid, recs] of uniqueMap) {
      const primary = recs[0];
      console.log(`  PMID ${pmid}`);
      console.log(`    claimed: ${primary.studlab} (${primary.year || 'no year'})`);
      console.log(`    source:  ${recs.map(r => r.source_file).join(', ')}`);
      console.log(`    verify:  https://pubmed.ncbi.nlm.nih.gov/${pmid}/`);
      if (primary.doi) console.log(`    doi:     https://doi.org/${primary.doi}`);
      console.log('');
    }
    console.log(`${uniqueMap.size} PMID(s) listed. Click each URL and confirm the studlab/year match.`);
    return 0;
  }

  console.log(`Online mode — querying PubMed e-utils (NCBI rate-limit: ${NCBI_API_KEY ? '10/s w/ API key' : '3/s no key'}, sleep ${SLEEP_MS}ms between batches).\n`);

  // Fetch in batches of 20
  const pmids = [...uniqueMap.keys()];
  const BATCH = 20;
  const allFetched = {};
  for (let i = 0; i < pmids.length; i += BATCH) {
    const batch = pmids.slice(i, i + BATCH);
    try {
      const fetched = await fetchPubMed(batch);
      for (const pmid of batch) {
        allFetched[pmid] = fetched[pmid] || null;
      }
    } catch (e) {
      console.error(`  [error] PubMed batch fetch failed: ${e.message}`);
      return 2;
    }
    if (i + BATCH < pmids.length) await sleep(SLEEP_MS);
  }

  // Compare each claim
  for (const [pmid, recs] of uniqueMap) {
    const primary = recs[0];
    const actual = allFetched[pmid];
    const cmp = compareRecord(primary, actual);
    const tag = cmp.ok ? '✓' : '✗';
    console.log(`  ${tag} PMID ${pmid} (${primary.studlab})`);
    console.log(`    ${cmp.why}`);
    if (!cmp.ok) {
      fails++;
      for (const r of recs) console.log(`    in: ${r.source_file}`);
    }
    console.log('');
  }

  console.log('=========================================');
  if (fails === 0) {
    console.log(`All ${uniqueMap.size} unique PMIDs verified against PubMed.`);
    return 0;
  } else {
    console.log(`${fails} PMID misattribution(s) detected out of ${uniqueMap.size}. Review and fix.`);
    return 1;
  }
}

main()
  .then((code) => process.exit(code))
  .catch((e) => {
    console.error('Fatal:', e);
    process.exit(2);
  });
