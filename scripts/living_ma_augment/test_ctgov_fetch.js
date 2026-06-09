/* eslint-disable */
/**
 * Unit tests for ctgov_fetch.js extractStructured (pure function).
 * Run: node test_ctgov_fetch.js.
 *
 * The fetch + cache helpers are not tested here -- they require a
 * browser env (fetch, localStorage, crypto.subtle). Those will be
 * exercised in the Playwright smoke test against a recorded fixture.
 */
const assert = require('assert');

// Stub the browser globals the fetch module references at load time.
global.localStorage = { getItem: () => null, setItem: () => {}, removeItem: () => {} };
global.fetch = () => { throw new Error('fetch not stubbed'); };
global.crypto = { subtle: { digest: async () => new ArrayBuffer(32) } };

const CTG = require('./ctgov_fetch.js');

let passed = 0, failed = 0;
function test(name, fn) {
    try { fn(); console.log(`  ok  ${name}`); passed++; }
    catch (e) { console.log(`  FAIL ${name}\n      ${e.message}`); failed++; }
}

// ============================================================================
// extractStructured: realistic CT.gov v2 fixture
// ============================================================================

const fixture = {
    protocolSection: {
        identificationModule: {
            nctId: 'NCT99999999',
            briefTitle: 'A Phase 3 Study of TestDrug vs Placebo in Test Disease',
        },
        statusModule: {
            overallStatus: 'COMPLETED',
            startDateStruct: { date: '2018-06' },
            completionDateStruct: { date: '2022-03' },
        },
        designModule: {
            phases: ['PHASE3'],
            allocation: 'RANDOMIZED',
        },
        descriptionModule: {
            briefSummary: 'A randomized double-blind trial of TestDrug 100 mg daily vs placebo in adults with Test Disease.',
        },
        sponsorCollaboratorsModule: { leadSponsor: { name: 'Test Pharma Inc' } },
        armsInterventionsModule: {
            armGroups: [
                { label: 'TestDrug 100mg', type: 'EXPERIMENTAL', description: '100mg PO daily' },
                { label: 'Placebo',         type: 'PLACEBO_COMPARATOR', description: 'matching placebo PO daily' },
            ],
        },
    },
    resultsSection: {
        participantFlowModule: {
            groups: [
                { id: 'FG000', title: 'Experimental TestDrug 100mg' },
                { id: 'FG001', title: 'Placebo' },
            ],
            periods: [{
                title: 'Overall Study',
                milestones: [{
                    type: 'STARTED',
                    achievements: [
                        { groupId: 'FG000', numSubjects: '203' },
                        { groupId: 'FG001', numSubjects: '198' },
                    ],
                }],
            }],
        },
        outcomeMeasuresModule: {
            outcomeMeasures: [{
                type: 'PRIMARY',
                title: 'Composite of MACE at 24 weeks',
                paramType: 'COUNT_OF_PARTICIPANTS',
                unitOfMeasure: 'Participants',
                groups: [
                    { id: 'OG000', title: 'Experimental TestDrug 100mg' },
                    { id: 'OG001', title: 'Placebo' },
                ],
                classes: [{
                    title: '',
                    categories: [{
                        title: '',
                        measurements: [
                            { groupId: 'OG000', value: '42' },
                            { groupId: 'OG001', value: '67' },
                        ],
                    }],
                }],
                analyses: [{
                    paramType: 'HAZARD_RATIO',
                    paramValue: '0.61',
                    ciLowerLimit: '0.42',
                    ciUpperLimit: '0.89',
                }],
            }],
        },
    },
};

test('extractStructured: NCT, name, phase, year, status, sponsor — HIGH confidence', () => {
    const r = CTG.extractStructured(fixture);
    assert.strictEqual(r.nct.value, 'NCT99999999');
    assert.strictEqual(r.nct.confidence, 'HIGH');
    assert.strictEqual(r.name.value, 'A Phase 3 Study of TestDrug vs Placebo in Test Disease');
    assert.strictEqual(r.phase.value, 'PHASE3');
    assert.strictEqual(r.year.value, 2018);
    assert.strictEqual(r.year.confidence, 'HIGH');
    assert.strictEqual(r.status.value, 'COMPLETED');
    assert.strictEqual(r.sponsor.value, 'Test Pharma Inc');
});

test('extractStructured: interventions and comparators by arm type', () => {
    const r = CTG.extractStructured(fixture);
    assert.strictEqual(r.interventions.length, 1);
    assert.strictEqual(r.interventions[0].label, 'TestDrug 100mg');
    assert.strictEqual(r.comparators.length, 1);
    assert.strictEqual(r.comparators[0].label, 'Placebo');
});

test('extractStructured: tN/cN from participantFlow STARTED milestone', () => {
    const r = CTG.extractStructured(fixture);
    assert.strictEqual(r.tN.value, 203);
    assert.strictEqual(r.tN.confidence, 'HIGH');
    assert.strictEqual(r.cN.value, 198);
    assert.strictEqual(r.cN.confidence, 'HIGH');
});

test('extractStructured: tE/cE from primary outcome measurement', () => {
    const r = CTG.extractStructured(fixture);
    assert.strictEqual(r.tE.value, 42);
    assert.strictEqual(r.tE.confidence, 'HIGH');
    assert.strictEqual(r.cE.value, 67);
});

test('extractStructured: HR + CI + estimandType from analysis', () => {
    const r = CTG.extractStructured(fixture);
    assert.strictEqual(r.publishedHR.value, 0.61);
    assert.strictEqual(r.hrLCI.value, 0.42);
    assert.strictEqual(r.hrUCI.value, 0.89);
    assert.strictEqual(r.estimandType.value, 'HR');
    assert.strictEqual(r.publishedHR.confidence, 'HIGH');
});

test('extractStructured: primary outcome label captured', () => {
    const r = CTG.extractStructured(fixture);
    assert.strictEqual(r.primaryOutcome.value, 'Composite of MACE at 24 weeks');
});

test('extractStructured: missing modules => NONE confidence (no crash)', () => {
    const sparse = { protocolSection: { identificationModule: { nctId: 'NCT00000001' } } };
    const r = CTG.extractStructured(sparse);
    assert.strictEqual(r.nct.value, 'NCT00000001');
    assert.strictEqual(r.tN.confidence, 'NONE');
    assert.strictEqual(r.tE.confidence, 'NONE');
    assert.strictEqual(r.publishedHR.confidence, 'NONE');
    assert.strictEqual(r.year.confidence, 'NONE');
});

test('extractStructured: empty study object does not throw', () => {
    const r = CTG.extractStructured({});
    assert.strictEqual(r.nct.value, null);
    assert.strictEqual(r.nct.confidence, 'NONE');
});

test('extractStructured: handles RR analysis', () => {
    const f = JSON.parse(JSON.stringify(fixture));
    f.resultsSection.outcomeMeasuresModule.outcomeMeasures[0].analyses[0].paramType = 'RISK_RATIO';
    f.resultsSection.outcomeMeasuresModule.outcomeMeasures[0].analyses[0].paramValue = '1.62';
    f.resultsSection.outcomeMeasuresModule.outcomeMeasures[0].analyses[0].ciLowerLimit = '1.38';
    f.resultsSection.outcomeMeasuresModule.outcomeMeasures[0].analyses[0].ciUpperLimit = '1.91';
    const r = CTG.extractStructured(f);
    assert.strictEqual(r.estimandType.value, 'RR');
    assert.strictEqual(r.publishedHR.value, 1.62);
    assert.strictEqual(r.hrLCI.value, 1.38);
    assert.strictEqual(r.hrUCI.value, 1.91);
});

test('extractStructured: skips unknown analysis paramType (no false fill)', () => {
    const f = JSON.parse(JSON.stringify(fixture));
    f.resultsSection.outcomeMeasuresModule.outcomeMeasures[0].analyses[0].paramType = 'NUMBER';
    const r = CTG.extractStructured(f);
    assert.strictEqual(r.publishedHR.confidence, 'NONE');
});

// ============================================================================
// HARDENING (2026-06-09): anti-fabrication guards on the structured extractor
// ============================================================================

test('extractStructured: MEAN outcome does NOT fabricate event counts (tE/cE stay NONE)', () => {
    // A mean change-from-baseline outcome value (e.g. -2.3) must never be
    // Math.round-ed into an event count. Contract: leave tE/cE NONE so the modal
    // asks the user, rather than store a fabricated count.
    const f = JSON.parse(JSON.stringify(fixture));
    const om = f.resultsSection.outcomeMeasuresModule.outcomeMeasures[0];
    om.title = 'Mean change in 6-minute walk distance';
    om.paramType = 'MEAN';
    om.unitOfMeasure = 'meters';
    om.classes[0].categories[0].measurements = [
        { groupId: 'OG000', value: '34.7' },
        { groupId: 'OG001', value: '12.1' },
    ];
    const r = CTG.extractStructured(f);
    assert.strictEqual(r.tE.confidence, 'NONE', 'mean outcome must not yield a tE count');
    assert.strictEqual(r.tE.value, null);
    assert.strictEqual(r.cE.confidence, 'NONE');
    // primary outcome label + N still extracted (those are legitimate)
    assert.strictEqual(r.tN.value, 203);
});

test('extractStructured: percentage-unit count outcome does NOT fabricate tE/cE', () => {
    const f = JSON.parse(JSON.stringify(fixture));
    const om = f.resultsSection.outcomeMeasuresModule.outcomeMeasures[0];
    om.paramType = 'NUMBER';
    om.unitOfMeasure = 'percentage of participants';
    om.classes[0].categories[0].measurements = [
        { groupId: 'OG000', value: '12.5' },
        { groupId: 'OG001', value: '20.0' },
    ];
    const r = CTG.extractStructured(f);
    assert.strictEqual(r.tE.confidence, 'NONE', 'a "%" unit must not be stored as an event count');
    assert.strictEqual(r.cE.confidence, 'NONE');
});

test('extractStructured: non-finite numSubjects does not store NaN as a count', () => {
    const f = JSON.parse(JSON.stringify(fixture));
    f.resultsSection.participantFlowModule.periods[0].milestones[0].achievements = [
        { groupId: 'FG000', numSubjects: 'NA' },
        { groupId: 'FG001', numSubjects: '198' },
    ];
    const r = CTG.extractStructured(f);
    assert.strictEqual(r.tN.confidence, 'NONE', 'NaN numSubjects must leave tN NONE, not NaN');
    assert.strictEqual(r.cN.value, 198);
});

// ---- normalizeDateLower (the dateFrom-format guard the pilot debrief flagged) ----

test('normalizeDateLower: pads partial precisions to YYYY-MM-DD', () => {
    assert.strictEqual(CTG.normalizeDateLower('2015'), '2015-01-01');
    assert.strictEqual(CTG.normalizeDateLower('2015-06'), '2015-06-01');
    assert.strictEqual(CTG.normalizeDateLower('2015-06-15'), '2015-06-15');
});

test('normalizeDateLower: boundary year-only date is NOT wrongly dropped', () => {
    // The debrief bug: bare "2015" < "2015-01-01" under raw string compare would
    // drop a valid 2015 study. After normalisation it is >= the bound.
    const sd = CTG.normalizeDateLower('2015');
    const bound = CTG.normalizeDateLower('2015-01-01');
    assert.ok(sd >= bound, '2015 study must pass a 2015-01-01 lower bound');
    assert.ok(CTG.normalizeDateLower('2014') < bound, '2014 study must still be dropped');
});

console.log(`\n${passed} passed, ${failed} failed`);
process.exit(failed === 0 ? 0 : 1);
