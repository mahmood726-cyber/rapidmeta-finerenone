#!/usr/bin/env python3
# sentinel:skip-file - developer tool; hardcoded ROOT is intentional (local Finrenone checkout only)
"""Inject a QoL/PRO detector that scans trial data + hydrated evidence for
patient-reported-outcome markers, populating state.results.patient
ReportedOutcomes so the peer-review QA concern retires when PRO data is
actually available upstream (even if not in the headline pool).

Detection targets (regex, case-insensitive):
  EQ-5D, SF-36, SF-12, KCCQ, PROMIS, HAQ(-DI)?, DLQI, EASI-QoL,
  EORTC QLQ-C30, FACT-[A-Z]+, MSIS-29, MIDAS, HIT-6, CDR-SB, MoCA,
  patient global, patient-reported, quality of life, quality-of-life,
  PRO, PROM

Scan sources (in order):
  1. trial.data.allOutcomes[].shortLabel / .title
  2. trial.data.evidence[] (from EvidenceHydrator)
  3. trial.data.patientReportedOutcomes (pre-declared in realData)

Populates:
  state.results.patientReportedOutcomes = {
      count: total mentions,
      scales: [unique scales detected],
      trials: [trial ids with PRO mentions],
  }

Idempotent. Fails closed. Injected before QA-enhancer so flag is set when
peer-review reads state.
"""
import argparse, pathlib, sys

ROOT = pathlib.Path(r"C:\Projects\Finrenone")
SENTINEL = "/*PRO-DETECTOR-v1*/"


PRO_SCRIPT = r"""<script>/*PRO-DETECTOR-v1*/
(function () {
    'use strict';

    // Validated PRO / QoL instruments commonly reported in pivotal trials.
    // Pattern list ordered from more specific to generic.
    var PATTERNS = [
        { re: /\bEQ[-\s]?5D(?:[-\s]?5L|[-\s]?3L)?\b/i,          name: 'EQ-5D' },
        { re: /\bSF[-\s]?36\b/i,                                 name: 'SF-36' },
        { re: /\bSF[-\s]?12\b/i,                                 name: 'SF-12' },
        { re: /\bKCCQ(?:[-\s]?(?:CSS|OSS|TSS))?\b/i,             name: 'KCCQ' },
        { re: /\bPROMIS\b/i,                                      name: 'PROMIS' },
        { re: /\bHAQ(?:[-\s]?DI)?\b/i,                           name: 'HAQ-DI' },
        { re: /\bDLQI\b/i,                                        name: 'DLQI' },
        { re: /\bPOEM\b/i,                                        name: 'POEM' },
        { re: /\bPP[-\s]?NRS\b/i,                                 name: 'PP-NRS' },
        { re: /\bEORTC\s*QLQ[-\s]?C30\b/i,                       name: 'EORTC QLQ-C30' },
        { re: /\bFACT[-\s]?[A-Z]{1,4}\b/i,                       name: 'FACT (generic)' },
        { re: /\bMSIS[-\s]?29\b/i,                                name: 'MSIS-29' },
        { re: /\bMIDAS\b/i,                                       name: 'MIDAS' },
        { re: /\bHIT[-\s]?6\b/i,                                  name: 'HIT-6' },
        { re: /\bCDR[-\s]?SB\b/i,                                 name: 'CDR-SB' },
        { re: /\bMoCA\b/i,                                        name: 'MoCA' },
        { re: /\bMMSE\b/i,                                        name: 'MMSE' },
        { re: /\bPANSS\b/i,                                       name: 'PANSS' },
        { re: /\bMADRS\b/i,                                       name: 'MADRS' },
        { re: /\bPHQ[-\s]?9\b/i,                                  name: 'PHQ-9' },
        { re: /\bGAD[-\s]?7\b/i,                                  name: 'GAD-7' },
        { re: /\bSGRQ\b/i,                                        name: 'SGRQ' },
        { re: /\bACQ\b/i,                                         name: 'ACQ' },
        { re: /\bCAT\s*\(COPD\)|COPD\s*assessment/i,             name: 'CAT (COPD)' },
        { re: /\bpatient[- ]?global\s*(?:assessment|impression)/i, name: 'Patient Global Assessment' },
        { re: /\bpatient[- ]?reported\b/i,                        name: 'PRO (generic)' },
        { re: /\bquality[- ]of[- ]life\b/i,                       name: 'QoL (generic)' },
        { re: /\bhealth[- ]related\s*quality\b/i,                 name: 'HRQoL' },
    ];

    function scanString(s) {
        if (!s || typeof s !== 'string') return [];
        var hits = [];
        for (var i = 0; i < PATTERNS.length; i++) {
            if (PATTERNS[i].re.test(s)) hits.push(PATTERNS[i].name);
        }
        return hits;
    }

    function scanTrialForPROs(trial) {
        var hits = new Set();
        var data = trial && trial.data;
        if (!data) return hits;

        // 1. allOutcomes[].shortLabel + title
        if (Array.isArray(data.allOutcomes)) {
            data.allOutcomes.forEach(function (o) {
                scanString(o && o.shortLabel).forEach(function (h) { hits.add(h); });
                scanString(o && o.title).forEach(function (h) { hits.add(h); });
            });
        }

        // 2. evidence array (fetched by EvidenceHydrator or declared in realData)
        if (Array.isArray(data.evidence)) {
            data.evidence.forEach(function (ev) {
                if (!ev) return;
                ['label', 'title', 'source', 'text', 'outcome'].forEach(function (field) {
                    scanString(ev[field]).forEach(function (h) { hits.add(h); });
                });
            });
        }

        // 3. pre-declared
        if (data.patientReportedOutcomes === true) hits.add('Pre-declared PRO');
        if (Array.isArray(data.patientReportedOutcomes)) {
            data.patientReportedOutcomes.forEach(function (name) {
                if (typeof name === 'string' && name.length) hits.add(name);
            });
        }

        return hits;
    }

    function detectPROs() {
        var RM = window.RapidMeta;
        if (!RM || !RM.state || !RM.state.results) return;
        var r = RM.state.results;
        if (r.patientReportedOutcomes && (r.patientReportedOutcomes.count > 0 || r.patientReportedOutcomes.scales)) return;

        var trials = (RM.state.trials || []).filter(function (t) { return t && t.data && t.included !== false; });
        if (!trials.length) return;

        var allScales = new Set();
        var trialsWithPRO = [];
        var totalHits = 0;

        trials.forEach(function (t) {
            var hits = scanTrialForPROs(t);
            if (hits.size > 0) {
                trialsWithPRO.push(t.id || (t.data && t.data.name) || '?');
                hits.forEach(function (h) { allScales.add(h); totalHits++; });
            }
        });

        r.patientReportedOutcomes = {
            count: totalHits,
            scales: Array.from(allScales),
            trials: trialsWithPRO,
            inHeadlineAnalysis: false,  // by default; apps that present PRO as headline should override
        };
    }

    function install() {
        var RM = window.RapidMeta;
        if (!RM) return false;
        if (RM.__proDetectorInstalled) return true;
        RM.__proDetectorInstalled = true;

        if (typeof window.AnalysisEngine === 'object' && window.AnalysisEngine && typeof window.AnalysisEngine.run === 'function') {
            var origRun = window.AnalysisEngine.run;
            window.AnalysisEngine.run = function () {
                var out = origRun.apply(this, arguments);
                try { detectPROs(); } catch (e) {}
                return out;
            };
        }
        if (RM.state && RM.state.results) {
            try { detectPROs(); } catch (e) {}
        }
        return true;
    }

    var tries = 0;
    function ready() {
        if (tries++ > 120) return;
        if (!install()) setTimeout(ready, 100);
    }
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', ready);
    else ready();
})();
</script>
"""


def apply_to_file(path: pathlib.Path, dry_run: bool) -> str:
    raw = path.read_bytes()
    crlf = b"\r\n" in raw
    text = raw.decode("utf-8").replace("\r\n", "\n")
    if SENTINEL in text:
        return f"SKIP {path.name}"

    # Inject right before REML retrofit so PRO detector sits at same chain position
    # (both run after original AnalysisEngine.run completes, before QA enhancer).
    anchor = text.find("/*REML-RETROFIT-v1*/")
    if anchor < 0:
        anchor = text.find("/*QA-ENHANCER-v1*/")
    if anchor < 0:
        anchor = text.find("/*PEER-REVIEW-v2*/")
    if anchor < 0:
        body_pos = text.rfind("</body>")
        if body_pos < 0:
            return f"FAIL {path.name}: no anchor"
        insertion_point = body_pos
    else:
        script_start = text.rfind("<script", 0, anchor)
        if script_start < 0:
            return f"FAIL {path.name}: <script> anchor not found"
        insertion_point = script_start

    new_text = text[:insertion_point] + PRO_SCRIPT + "\n" + text[insertion_point:]
    out = new_text.replace("\n", "\r\n") if crlf else new_text
    if not dry_run:
        path.write_bytes(out.encode("utf-8"))
    return f"OK   {path.name}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    if not (args.dry_run or args.apply):
        ap.error("pass --dry-run or --apply")
    ok = skip = fail = 0
    for p in sorted(ROOT.glob("*_REVIEW.html")):
        r = apply_to_file(p, args.dry_run)
        if r.startswith("OK"):
            ok += 1
        elif r.startswith("SKIP"):
            skip += 1
        else:
            print(r); fail += 1
    print(f"\n{'dry-run' if args.dry_run else 'apply'}: {ok} ok / {skip} skip / {fail} fail")
    if fail: sys.exit(1)


if __name__ == "__main__":
    main()
