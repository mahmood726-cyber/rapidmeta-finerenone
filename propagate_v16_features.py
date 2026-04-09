"""
Propagate v16 features from FINERENONE_REVIEW.html to all sibling apps.
Phases 4-8 (extends propagate_features.py phases 1-3):
  4. CumulativeEngine
  5. ProvenanceChainEngine + DataSealEngine (update)
  6. QAEngine
  7. CrossValidationEngine (+ CSS)
  8. BenchmarkEngine

Safety:
  - .pre_v16.bak.html backup before any changes
  - Duplicate detection (skip if engine already present)
  - Div balance validation after all phases
  - No trial data modifications
  - Dynamic drug name substitution (no hardcoded "finerenone")

Run: python propagate_v16_features.py [--dry-run]
"""
import re, os, sys, shutil

DRY_RUN = '--dry-run' in sys.argv

DIR = os.path.dirname(os.path.abspath(__file__))
SOURCE = os.path.join(DIR, 'FINERENONE_REVIEW.html')

# All sibling apps (excludes FINERENONE itself)
ALL_TARGETS = [
    'ABLATION_AF_REVIEW.html', 'ARNI_HF_REVIEW.html', 'ATTR_CM_REVIEW.html',
    'BEMPEDOIC_ACID_REVIEW.html', 'COLCHICINE_CVD_REVIEW.html', 'DOAC_CANCER_VTE_REVIEW.html',
    'GLP1_CVOT_REVIEW.html', 'INCRETIN_HFpEF_REVIEW.html', 'INTENSIVE_BP_REVIEW.html',
    'IV_IRON_HF_REVIEW.html', 'LIPID_HUB_REVIEW.html', 'MAVACAMTEN_HCM_REVIEW.html',
    'PCSK9_REVIEW.html', 'RENAL_DENERV_REVIEW.html', 'RIVAROXABAN_VASC_REVIEW.html',
    'SGLT2_CKD_REVIEW.html', 'SGLT2_HF_REVIEW.html', 'LivingMeta.html'
]

def read_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def write_file(path, content):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

def find_engine_block(source_lines, start_marker):
    """Extract an engine block using brace-depth matching from start_marker."""
    start_idx = None
    for i, line in enumerate(source_lines):
        if start_marker in line and start_idx is None:
            start_idx = i
            break
    if start_idx is None:
        return None, None, None
    depth = 0
    for i in range(start_idx, len(source_lines)):
        depth += source_lines[i].count('{') - source_lines[i].count('}')
        if depth == 0 and i > start_idx:
            return start_idx, i, '\n'.join(source_lines[start_idx:i+1])
    return start_idx, None, None

def find_line(lines, marker):
    """Find line index containing marker."""
    for i, line in enumerate(lines):
        if marker in line:
            return i
    return None

def div_balance(content):
    """Check div open/close balance."""
    opens = len(re.findall(r'<div[\s>]', content))
    closes = content.count('</div>')
    return opens, closes, abs(opens - closes) <= 2


# ========== LOAD SOURCE ==========
print("=" * 60)
print("v16 Feature Propagation")
print("=" * 60)
if DRY_RUN:
    print("*** DRY RUN — no files will be modified ***\n")

print("Reading source: FINERENONE_REVIEW.html")
source = read_file(SOURCE)
source_lines = source.split('\n')


# ========== EXTRACT ENGINE BLOCKS ==========
print("\nExtracting engine blocks from source...")

# Phase 4: CumulativeEngine
cum_start, cum_end, cumulative_block = find_engine_block(source_lines, 'const CumulativeEngine = {')
if cumulative_block:
    print(f"  CumulativeEngine: lines {cum_start+1}-{cum_end+1} ({cum_end-cum_start+1} lines)")
else:
    print("  ERROR: CumulativeEngine not found"); sys.exit(1)

# Phase 5a: ProvenanceChainEngine
prov_start, prov_end, provenance_block = find_engine_block(source_lines, 'const ProvenanceChainEngine = {')
if provenance_block:
    print(f"  ProvenanceChainEngine: lines {prov_start+1}-{prov_end+1} ({prov_end-prov_start+1} lines)")
else:
    print("  ERROR: ProvenanceChainEngine not found"); sys.exit(1)

# Phase 5b: DataSealEngine (v16 version)
ds_start, ds_end, dataseal_block = find_engine_block(source_lines, 'const DataSealEngine = {')
if dataseal_block:
    print(f"  DataSealEngine: lines {ds_start+1}-{ds_end+1} ({ds_end-ds_start+1} lines)")
else:
    print("  ERROR: DataSealEngine not found"); sys.exit(1)

# Phase 6: QAEngine
qa_start, qa_end, qa_block = find_engine_block(source_lines, 'const QAEngine = {')
if qa_block:
    print(f"  QAEngine: lines {qa_start+1}-{qa_end+1} ({qa_end-qa_start+1} lines)")
else:
    print("  ERROR: QAEngine not found"); sys.exit(1)

# Phase 7: CrossValidationEngine
xv_start, xv_end, xval_block = find_engine_block(source_lines, 'const CrossValidationEngine = {')
if xval_block:
    print(f"  CrossValidationEngine: lines {xv_start+1}-{xv_end+1} ({xv_end-xv_start+1} lines)")
else:
    print("  ERROR: CrossValidationEngine not found"); sys.exit(1)

# Phase 7b: CrossValidation CSS
xval_css_lines = []
for i, line in enumerate(source_lines):
    if '/* v13.0: Cross-Validation Panel */' in line:
        xval_css_lines.append(line)
        for j in range(i+1, len(source_lines)):
            if source_lines[j].strip().startswith('.xval-') or source_lines[j].strip().startswith('.light-mode .xval-'):
                xval_css_lines.append(source_lines[j])
            else:
                break
        break
xval_css_block = '\n'.join(xval_css_lines) if xval_css_lines else None
if xval_css_block:
    print(f"  CrossValidation CSS: {len(xval_css_lines)} lines")
else:
    print("  WARNING: CrossValidation CSS not found")

# Phase 8: BenchmarkEngine
bm_start, bm_end, benchmark_block = find_engine_block(source_lines, 'const BenchmarkEngine = {')
if benchmark_block:
    # Replace hardcoded "finerenone corridor" with dynamic drug name
    benchmark_block = benchmark_block.replace(
        'the published finerenone corridor',
        "the published ${RapidMeta.state.protocol?.int ?? 'benchmark'} corridor"
    )
    print(f"  BenchmarkEngine: lines {bm_start+1}-{bm_end+1} ({bm_end-bm_start+1} lines)")
else:
    print("  ERROR: BenchmarkEngine not found"); sys.exit(1)


# ========== HTML CONTAINERS ==========

CUMULATIVE_HTML = """
                    <!-- v15.0: Cumulative Meta-Analysis -->
                    <div class="glass p-10 rounded-[40px] border border-slate-800">
                        <div class="flex items-center justify-between mb-6">
                            <h3 class="text-sm font-bold opacity-60 uppercase tracking-[0.3em]">Cumulative Meta-Analysis</h3>
                            <button type="button" onclick="CumulativeEngine.render()" class="text-[11px] font-bold text-teal-400 uppercase bg-teal-400/10 px-6 py-2 rounded-full border border-teal-400/20 transition-all hover:bg-teal-400/20"><i class="fa-solid fa-layer-group mr-1"></i>Run Cumulative</button>
                        </div>
                        <div id="cumulative-container">
                            <div class="text-xs text-slate-500 italic">Click "Run Cumulative" to generate a cumulative meta-analysis ordered by publication year.</div>
                        </div>
                    </div>
"""

QA_HTML = """
                    <!-- v15.0: QA Checks -->
                    <div class="glass p-10 rounded-[40px] border border-slate-800">
                        <div class="flex items-center justify-between mb-6">
                            <h3 class="text-sm font-bold opacity-60 uppercase tracking-[0.3em]">Quality Assurance (18 Checks)</h3>
                            <button type="button" onclick="QAEngine.render()" class="text-[11px] font-bold text-amber-400 uppercase bg-amber-400/10 px-6 py-2 rounded-full border border-amber-400/20 transition-all hover:bg-amber-400/20"><i class="fa-solid fa-clipboard-check mr-1"></i>Run QA</button>
                        </div>
                        <div id="qa-container">
                            <div class="text-xs text-slate-500 italic">Click "Run QA" to execute 18 automated quality checks on the current analysis.</div>
                        </div>
                    </div>
"""

# Phase 4-8 section comments for the JS engines
CUMULATIVE_COMMENT = """
        // ═══════════════════════════════════════════════════════════
        // v15.0: Cumulative Meta-Analysis Engine
        // DL pooling ordered by year, conditional 0.5 correction, t-distribution CIs
        // ═══════════════════════════════════════════════════════════
"""

PROVENANCE_COMMENT = """
        // ═══════════════════════════════════════════════════════════
        // v15.0: Provenance Chain Engine
        // SHA-256 hash chain with djb2 fallback for file:// protocol
        // ═══════════════════════════════════════════════════════════
"""

QA_COMMENT = """
        // ═══════════════════════════════════════════════════════════
        // v15.0: QA Engine — 18 automated checks
        // ═══════════════════════════════════════════════════════════
"""

XVAL_COMMENT = """
        // ═══════════════════════════════════════════════════════════
        // v13.0: Cross-Validation Engine
        // Three-source concordance checking: CT.gov API vs PubMed abstract vs extracted value
        // ═══════════════════════════════════════════════════════════
"""


# ========== PROPAGATION ==========
results = {}

for fname in ALL_TARGETS:
    fpath = os.path.join(DIR, fname)
    if not os.path.exists(fpath):
        print(f"\n  SKIP: {fname} not found")
        continue

    print(f"\n{'='*50}")
    print(f"Processing {fname}")
    print(f"{'='*50}")

    content = read_file(fpath)
    original_content = content  # keep for backup comparison
    lines = content.split('\n')
    changes = []

    # ---- Phase 4: CumulativeEngine ----
    if 'const CumulativeEngine' in content:
        print("  Phase 4: SKIP CumulativeEngine (already present)")
    else:
        # JS insertion: after DataSealEngine or after PowerEngine or before downloadPDFReport
        anchor = find_line(lines, 'const SensitivityEngine = {')
        if anchor is None:
            anchor = find_line(lines, 'const DataSealEngine = {')
        if anchor is None:
            anchor = find_line(lines, 'const PowerEngine = {')
        if anchor is None:
            anchor = find_line(lines, 'function downloadPDFReport()')

        if anchor is not None:
            insert_block = CUMULATIVE_COMMENT + cumulative_block + '\n'
            lines.insert(anchor, insert_block)
            changes.append('CumulativeEngine JS')
            print(f"  Phase 4: INSERTED CumulativeEngine JS before line {anchor+1}")

            # Rebuild
            content = '\n'.join(lines)
            lines = content.split('\n')

            # HTML insertion: after GRADE section or after SoF button
            html_anchor = None
            # Look for GRADE profile section end
            for i, line in enumerate(lines):
                if 'GradeProfileEngine.exportCSV()' in line or 'Download SoF Table' in line:
                    # Find the closing </div> of this glass panel (2-3 levels up)
                    depth = 0
                    for j in range(i, min(i + 20, len(lines))):
                        depth += lines[j].count('</div>') - len(re.findall(r'<div[\s>]', lines[j]))
                        if depth >= 2:  # closed the panel
                            html_anchor = j + 1
                            break
                    break

            if html_anchor is None:
                # Fallback: before Waiting Room
                for i, line in enumerate(lines):
                    if 'Waiting Room' in line and ('h3' in line or 'heading' in line.lower()):
                        # Go back to find the glass panel start
                        for j in range(i, max(0, i - 10), -1):
                            if 'glass' in lines[j] and '<div' in lines[j]:
                                html_anchor = j
                                break
                        break

            if html_anchor is not None:
                lines.insert(html_anchor, CUMULATIVE_HTML)
                changes.append('CumulativeEngine HTML')
                print(f"  Phase 4: INSERTED CumulativeEngine HTML at line {html_anchor+1}")
            else:
                print("  Phase 4: WARNING — could not find HTML insertion point for Cumulative")
        else:
            print("  Phase 4: WARNING — no JS anchor found for CumulativeEngine")

        content = '\n'.join(lines)
        lines = content.split('\n')

    # ---- Phase 5a: ProvenanceChainEngine ----
    if 'const ProvenanceChainEngine' in content:
        print("  Phase 5a: SKIP ProvenanceChainEngine (already present)")
    else:
        # Insert after CumulativeEngine or before QAEngine or before downloadPDFReport
        anchor = None
        for marker in ['const CumulativeEngine', 'const SensitivityEngine', 'const DataSealEngine', 'const PowerEngine', 'function downloadPDFReport()']:
            idx = find_line(lines, marker)
            if idx is not None:
                # Find end of this engine block using brace matching
                depth = 0
                found_end = False
                for i in range(idx, min(idx + 500, len(lines))):
                    depth += lines[i].count('{') - lines[i].count('}')
                    if depth == 0 and i > idx:
                        anchor = i + 1
                        found_end = True
                        break
                if found_end:
                    break
                # If we couldn't find end via braces, just insert before this marker
                anchor = idx
                break

        if anchor is not None:
            insert_block = PROVENANCE_COMMENT + provenance_block + '\n'
            lines.insert(anchor, insert_block)
            changes.append('ProvenanceChainEngine')
            print(f"  Phase 5a: INSERTED ProvenanceChainEngine at line {anchor+1}")
        else:
            print("  Phase 5a: WARNING — no anchor found for ProvenanceChainEngine")

        content = '\n'.join(lines)
        lines = content.split('\n')

    # ---- Phase 5b: DataSealEngine (update to v16 if needed) ----
    if 'const DataSealEngine' in content:
        # Check if it's the old version (missing djb2 fallback)
        ds_idx = find_line(lines, 'const DataSealEngine = {')
        if ds_idx is not None:
            # Find existing block end
            depth = 0
            ds_end_idx = None
            for i in range(ds_idx, min(ds_idx + 100, len(lines))):
                depth += lines[i].count('{') - lines[i].count('}')
                if depth == 0 and i > ds_idx:
                    ds_end_idx = i
                    break
            if ds_end_idx is not None:
                old_block = '\n'.join(lines[ds_idx:ds_end_idx+1])
                if 'djb2' not in old_block:
                    # Replace with v16 version
                    lines[ds_idx:ds_end_idx+1] = [dataseal_block]
                    changes.append('DataSealEngine updated to v16')
                    print(f"  Phase 5b: UPDATED DataSealEngine to v16 (added djb2 fallback)")
                else:
                    print("  Phase 5b: SKIP DataSealEngine (already v16)")
            else:
                print("  Phase 5b: WARNING — could not find end of DataSealEngine")
        else:
            print("  Phase 5b: SKIP DataSealEngine (marker found but line lookup failed)")
    else:
        # Insert DataSealEngine — after PowerEngine or CopasEngine
        anchor = None
        for marker in ['const PowerEngine', 'const CopasEngine']:
            idx = find_line(lines, marker)
            if idx is not None:
                depth = 0
                for i in range(idx, min(idx + 200, len(lines))):
                    depth += lines[i].count('{') - lines[i].count('}')
                    if depth == 0 and i > idx:
                        anchor = i + 1
                        break
                if anchor:
                    break

        if anchor is None:
            anchor = find_line(lines, 'function downloadPDFReport()')

        if anchor is not None:
            insert_block = '\n        // ===== v11.0: DATA SEAL (SHA-256) =====\n' + dataseal_block + '\n'
            lines.insert(anchor, insert_block)
            changes.append('DataSealEngine added')
            print(f"  Phase 5b: INSERTED DataSealEngine at line {anchor+1}")
        else:
            print("  Phase 5b: WARNING — no anchor found for DataSealEngine")

        content = '\n'.join(lines)
        lines = content.split('\n')

    content = '\n'.join(lines)
    lines = content.split('\n')

    # ---- Phase 6: QAEngine ----
    if 'const QAEngine' in content:
        print("  Phase 6: SKIP QAEngine (already present)")
    else:
        # JS insertion: after ProvenanceChainEngine or after DataSealEngine
        anchor = None
        for marker in ['const ProvenanceChainEngine', 'const DataSealEngine', 'const PowerEngine']:
            idx = find_line(lines, marker)
            if idx is not None:
                depth = 0
                for i in range(idx, min(idx + 200, len(lines))):
                    depth += lines[i].count('{') - lines[i].count('}')
                    if depth == 0 and i > idx:
                        anchor = i + 1
                        break
                if anchor:
                    break

        if anchor is not None:
            insert_block = QA_COMMENT + qa_block + '\n'
            lines.insert(anchor, insert_block)
            changes.append('QAEngine JS')
            print(f"  Phase 6: INSERTED QAEngine JS at line {anchor+1}")

            content = '\n'.join(lines)
            lines = content.split('\n')

            # HTML: insert QA container after Cumulative section or after GRADE
            html_anchor = None
            # Find the "Run Cumulative" button text — the panel ends 4 lines after cumulative-container
            for i, line in enumerate(lines):
                if 'id="cumulative-container"' in line:
                    # The cumulative panel structure is:
                    #   <div id="cumulative-container">...</div>
                    #   </div>  (closes glass panel)
                    # Scan forward for the next closing sequence
                    for j in range(i + 1, min(i + 8, len(lines))):
                        if lines[j].strip() == '</div>' or (lines[j].strip().startswith('</div>') and 'glass' not in lines[j]):
                            # Keep looking for the outermost panel close
                            pass
                        if j > i + 1 and '</div>' in lines[j] and '</div>' in lines[j-1]:
                            html_anchor = j + 1
                            break
                    if html_anchor is None and i + 4 < len(lines):
                        html_anchor = i + 4  # fallback: insert a few lines after container
                    break

            if html_anchor is None:
                # After manuscript-text or Waiting Room
                for i, line in enumerate(lines):
                    if 'manuscript-text' in line and 'id=' in line:
                        for j in range(i + 1, min(i + 10, len(lines))):
                            if '</div>' in lines[j] and '</div>' in lines[j-1] if j > 0 else False:
                                html_anchor = j + 1
                                break
                        if html_anchor is None:
                            html_anchor = i + 5
                        break

            if html_anchor is None:
                # Last fallback: before Waiting Room
                for i, line in enumerate(lines):
                    if 'Waiting Room' in line:
                        html_anchor = i
                        break

            if html_anchor is not None:
                lines.insert(html_anchor, QA_HTML)
                changes.append('QAEngine HTML')
                print(f"  Phase 6: INSERTED QAEngine HTML at line {html_anchor+1}")
            else:
                print("  Phase 6: WARNING — could not find HTML insertion point for QA")
        else:
            print("  Phase 6: WARNING — no JS anchor found for QAEngine")

        content = '\n'.join(lines)
        lines = content.split('\n')

    # ---- Phase 7: CrossValidationEngine ----
    if 'const CrossValidationEngine' in content:
        print("  Phase 7: SKIP CrossValidationEngine (already present)")
    else:
        # JS insertion: before CumulativeEngine or before ManuscriptEngine or before downloadPDFReport
        anchor = None
        for marker in ['const CumulativeEngine', 'const ManuscriptEngine',
                        '/* ═══ Auto-Generated Manuscript Text ═══ */',
                        'function downloadPDFReport()']:
            idx = find_line(lines, marker)
            if idx is not None:
                anchor = idx
                break

        if anchor is not None:
            insert_block = XVAL_COMMENT + xval_block + '\n'
            lines.insert(anchor, insert_block)
            changes.append('CrossValidationEngine JS')
            print(f"  Phase 7: INSERTED CrossValidationEngine JS before line {anchor+1}")
        else:
            print("  Phase 7: WARNING — no JS anchor found for CrossValidationEngine")

        content = '\n'.join(lines)
        lines = content.split('\n')

        # CSS insertion: before </style>
        if xval_css_block and '.xval-panel' not in content:
            style_end = find_line(lines, '</style>')
            if style_end is not None:
                lines.insert(style_end, xval_css_block)
                changes.append('CrossValidation CSS')
                print(f"  Phase 7: INSERTED CrossValidation CSS before </style>")

        content = '\n'.join(lines)
        lines = content.split('\n')

    # ---- Phase 8: BenchmarkEngine ----
    if 'const BenchmarkEngine' in content:
        print("  Phase 8: SKIP BenchmarkEngine (already present)")
    else:
        # Only add if app has getSelectedBenchmarkEntries
        if 'getSelectedBenchmarkEntries' in content:
            # Insert after CrossValidationEngine or CumulativeEngine or before ArtifactEngine or CapsuleEngine
            anchor = None
            for marker in ['const ArtifactEngine', 'const CapsuleEngine', 'function downloadPDFReport()']:
                idx = find_line(lines, marker)
                if idx is not None:
                    anchor = idx
                    break

            if anchor is not None:
                insert_block = '\n' + benchmark_block + '\n'
                lines.insert(anchor, insert_block)
                changes.append('BenchmarkEngine')
                print(f"  Phase 8: INSERTED BenchmarkEngine before line {anchor+1}")
            else:
                print("  Phase 8: WARNING — no anchor found for BenchmarkEngine")
        else:
            print("  Phase 8: SKIP BenchmarkEngine (no getSelectedBenchmarkEntries in app)")

        content = '\n'.join(lines)
        lines = content.split('\n')

    # ========== WRITE & VALIDATE ==========
    content = '\n'.join(lines)

    if changes:
        if not DRY_RUN:
            # Backup
            bak_path = fpath.replace('.html', '.pre_v16.bak.html')
            if not os.path.exists(bak_path):
                shutil.copy2(fpath, bak_path)
                print(f"  BACKUP: {os.path.basename(bak_path)}")

            write_file(fpath, content)

        # Validate
        opens, closes, ok = div_balance(content)
        div_status = f"OK ({opens}/{closes})" if ok else f"WARN ({opens}/{closes})"

        # Script tag check
        script_ok = '${"<"}/script>' not in content or True  # Template literal escaping is fine
        raw_close_scripts = len(re.findall(r'</script>', content))
        open_scripts = len(re.findall(r'<script', content))
        script_status = "OK" if raw_close_scripts == open_scripts else f"WARN ({open_scripts} open / {raw_close_scripts} close)"

        results[fname] = {
            'changes': changes,
            'div': div_status,
            'script': script_status
        }
        action = "WOULD SAVE" if DRY_RUN else "SAVED"
        print(f"  {action}: {', '.join(changes)}")
        print(f"  DIV: {div_status} | SCRIPT: {script_status}")
    else:
        results[fname] = {'changes': ['no changes needed'], 'div': 'N/A', 'script': 'N/A'}
        print("  No changes needed")


# ========== SUMMARY ==========
print(f"\n{'='*60}")
print("PROPAGATION SUMMARY")
print(f"{'='*60}")

total_changes = 0
for fname, info in sorted(results.items()):
    chg = info['changes']
    n_changes = len([c for c in chg if c != 'no changes needed'])
    total_changes += n_changes
    status_icon = "+" if n_changes > 0 else "-"
    print(f"  [{status_icon}] {fname}: {', '.join(chg)}")
    if n_changes > 0:
        print(f"       DIV: {info['div']} | SCRIPT: {info['script']}")

print(f"\nTotal: {total_changes} changes across {len(results)} files")
if DRY_RUN:
    print("\n*** DRY RUN — no files were modified. Remove --dry-run to apply. ***")
else:
    print("\nRun: python cross_validate.py  (verify benchmarks)")
    print("Run: python test_all_apps_comprehensive.py  (verify no regressions)")
