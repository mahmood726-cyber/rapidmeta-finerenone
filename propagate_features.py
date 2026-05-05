"""
Propagate 3 features from FINERENONE_REVIEW.html to all sibling apps:
1. TextExtractor (51 patterns, ~400 lines)
2. GradeProfileEngine upgrade (exportSoFHTML + helper functions)
3. Manuscript text generator (HTML + JS + wiring)

Run: python propagate_features.py
"""
import sys as _sys
if __name__ != "__main__":
    _sys.exit(0)

import re, os, sys

DIR = os.path.dirname(os.path.abspath(__file__))
SOURCE = os.path.join(DIR, 'FINERENONE_REVIEW.html')

# Files that need TextExtractor (all except FINERENONE and LivingMeta which already have it)
NEED_TEXT_EXTRACTOR = [
    'GLP1_CVOT_REVIEW.html', 'BEMPEDOIC_ACID_REVIEW.html', 'COLCHICINE_CVD_REVIEW.html',
    'INTENSIVE_BP_REVIEW.html', 'LIPID_HUB_REVIEW.html', 'PCSK9_REVIEW.html', 'SGLT2_HF_REVIEW.html'
]

# Files that have OLD GradeProfileEngine (need replacement + helpers)
HAS_OLD_GRADE = [
    'PCSK9_REVIEW.html', 'BEMPEDOIC_ACID_REVIEW.html', 'LIPID_HUB_REVIEW.html', 'INTENSIVE_BP_REVIEW.html'
]

# Files that need FULL GradeProfileEngine + helpers
NEED_FULL_GRADE = [
    'GLP1_CVOT_REVIEW.html', 'COLCHICINE_CVD_REVIEW.html', 'SGLT2_HF_REVIEW.html'
]

# All siblings that need manuscript text
NEED_MANUSCRIPT = [
    'GLP1_CVOT_REVIEW.html', 'BEMPEDOIC_ACID_REVIEW.html', 'COLCHICINE_CVD_REVIEW.html',
    'INTENSIVE_BP_REVIEW.html', 'LIPID_HUB_REVIEW.html', 'PCSK9_REVIEW.html',
    'SGLT2_HF_REVIEW.html', 'LivingMeta.html'
]

def read_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def write_file(path, content):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

def extract_block(source_lines, start_marker, end_marker):
    """Extract lines between start_marker and end_marker (inclusive of start, exclusive of end)."""
    start_idx = None
    for i, line in enumerate(source_lines):
        if start_marker in line and start_idx is None:
            start_idx = i
        if end_marker in line and start_idx is not None and i > start_idx:
            return source_lines[start_idx:i]
    return None

def extract_block_inclusive(source_lines, start_marker, end_marker):
    """Extract lines between start_marker and end_marker (inclusive of both)."""
    start_idx = None
    for i, line in enumerate(source_lines):
        if start_marker in line and start_idx is None:
            start_idx = i
        if end_marker in line and start_idx is not None and i > start_idx:
            return source_lines[start_idx:i+1]
    return None

def find_grade_engine_end(lines, start_idx):
    """Find the end of GradeProfileEngine object (matching braces)."""
    depth = 0
    for i in range(start_idx, len(lines)):
        depth += lines[i].count('{') - lines[i].count('}')
        if depth == 0 and i > start_idx:
            return i
    return None


# ========== LOAD SOURCE ==========
print("Reading source file (FINERENONE_REVIEW.html)...")
source = read_file(SOURCE)
source_lines = source.split('\n')

# ========== EXTRACT CODE BLOCKS ==========

# 1. TextExtractor block (from `const TextExtractor = (() => {` to end of IIFE before AutoExtractEngine)
te_start = None
te_end = None
for i, line in enumerate(source_lines):
    if 'const TextExtractor = (() => {' in line:
        te_start = i
    if te_start and 'const AutoExtractEngine = {' in line:
        te_end = i
        break

if te_start is None or te_end is None:
    print("ERROR: Could not find TextExtractor block in source")
    sys.exit(1)

text_extractor_block = '\n'.join(source_lines[te_start:te_end])
print(f"  TextExtractor: lines {te_start+1}-{te_end} ({te_end-te_start} lines)")

# 2. Helper functions: normalizedEffectMeasure + computeInterventionEventRate
helpers_start = None
helpers_end = None
for i, line in enumerate(source_lines):
    if 'const normalizedEffectMeasure' in line:
        helpers_start = i
    if helpers_start and 'const summarizeAbsoluteEffect' in line:
        helpers_end = i
        break

if helpers_start is None or helpers_end is None:
    print("ERROR: Could not find helper functions in source")
    sys.exit(1)

helpers_block = '\n'.join(source_lines[helpers_start:helpers_end])
print(f"  Helpers (normalizedEffectMeasure + computeIER): lines {helpers_start+1}-{helpers_end} ({helpers_end-helpers_start} lines)")

# 3. computeGradeAssessment
cga_start = None
cga_end = None
for i, line in enumerate(source_lines):
    if 'const computeGradeAssessment = (c, included' in line:
        cga_start = i
    if cga_start and line.strip() == '};' and i > cga_start + 10:
        cga_end = i + 1
        break

if cga_start is None or cga_end is None:
    print("ERROR: Could not find computeGradeAssessment in source")
    sys.exit(1)

grade_assessment_block = '\n'.join(source_lines[cga_start:cga_end])
print(f"  computeGradeAssessment: lines {cga_start+1}-{cga_end} ({cga_end-cga_start} lines)")

# 4. Full GradeProfileEngine (with exportSoFHTML)
gpe_start = None
for i, line in enumerate(source_lines):
    if 'const GradeProfileEngine = {' in line and i > 8000:  # Skip any earlier refs
        gpe_start = i
        break

if gpe_start is None:
    print("ERROR: Could not find GradeProfileEngine in source")
    sys.exit(1)

gpe_end = find_grade_engine_end(source_lines, gpe_start)
if gpe_end is None:
    print("ERROR: Could not find end of GradeProfileEngine")
    sys.exit(1)

grade_engine_block = '\n'.join(source_lines[gpe_start:gpe_end+1])
# Make _plainLanguage dynamic (replace hardcoded "Finerenone")
grade_engine_block = grade_engine_block.replace(
    "return `Finerenone probably reduces",
    "const _drug = RapidMeta.state.protocol?.int ?? 'The intervention'; return `${_drug} probably reduces"
).replace(
    "return `Finerenone may increase",
    "const _drug2 = RapidMeta.state.protocol?.int ?? 'The intervention'; return `${_drug2} may increase"
).replace(
    "return `Finerenone may result",
    "const _drug3 = RapidMeta.state.protocol?.int ?? 'The intervention'; return `${_drug3} may result"
)
print(f"  GradeProfileEngine: lines {gpe_start+1}-{gpe_end+1} ({gpe_end-gpe_start+1} lines)")

# 5. Manuscript text functions
ms_start = None
ms_end = None
for i, line in enumerate(source_lines):
    if '/* ═══ Auto-Generated Manuscript Text ═══ */' in line:
        ms_start = i
    if ms_start and 'function copyManuscriptText()' in line:
        # Find end of copyManuscriptText
        for j in range(i, min(i+10, len(source_lines))):
            if source_lines[j].strip() == '}':
                ms_end = j + 1
                break
        break

if ms_start is None or ms_end is None:
    print("ERROR: Could not find manuscript text functions in source")
    sys.exit(1)

manuscript_js_block = '\n'.join(source_lines[ms_start:ms_end])
print(f"  Manuscript JS: lines {ms_start+1}-{ms_end} ({ms_end-ms_start} lines)")

# 6. Manuscript HTML container
manuscript_html = """
                    <!-- Auto-Generated Methods & Results Text -->
                    <div class="glass p-8 rounded-[30px] border border-indigo-500/20 bg-indigo-500/5">
                        <div class="flex items-center justify-between mb-4">
                            <h3 class="text-xs font-bold opacity-40 uppercase tracking-[0.3em]"><i class="fa-solid fa-pen-nib mr-1"></i> Auto-Generated Manuscript Text</h3>
                            <button onclick="copyManuscriptText()" class="text-[10px] font-bold text-indigo-400 uppercase bg-indigo-400/10 px-4 py-1.5 rounded-full border border-indigo-400/20 hover:bg-indigo-400/20 transition-all"><i class="fa-solid fa-copy mr-1"></i> Copy All</button>
                        </div>
                        <div id="manuscript-text" class="space-y-6 text-sm text-slate-300 leading-relaxed" style="font-family: Georgia, serif;">
                            <p class="text-slate-500 italic">Click "Generate Output" to create manuscript text.</p>
                        </div>
                    </div>
"""

# 7. SoF export button HTML
sof_button_html = """                            <button onclick="GradeProfileEngine.exportSoFHTML()" class="text-[10px] font-bold text-emerald-400 uppercase bg-emerald-400/10 px-6 py-2 rounded-full border border-emerald-400/20 transition-all hover:bg-emerald-400/20">
                                <i class="fa-solid fa-file-word mr-1"></i> Download SoF Table (Word-compatible)
                            </button>"""

# ========== PROPAGATION ==========
results = {}

for fname in set(NEED_TEXT_EXTRACTOR + HAS_OLD_GRADE + NEED_FULL_GRADE + NEED_MANUSCRIPT):
    fpath = os.path.join(DIR, fname)
    if not os.path.exists(fpath):
        print(f"  SKIP: {fname} not found")
        continue

    print(f"\n--- Processing {fname} ---")
    content = read_file(fpath)
    lines = content.split('\n')
    changes = []

    # 1. TextExtractor insertion
    if fname in NEED_TEXT_EXTRACTOR:
        anchor = None
        for i, line in enumerate(lines):
            if 'const AutoExtractEngine = {' in line:
                anchor = i
                break

        if anchor is None:
            print(f"  WARNING: No AutoExtractEngine anchor in {fname}")
        elif 'const TextExtractor' in content:
            print(f"  SKIP TextExtractor: already present")
        else:
            lines.insert(anchor, text_extractor_block + '\n')
            changes.append('TextExtractor')
            print(f"  INSERTED TextExtractor before line {anchor+1}")

    # Rebuild content after potential insertion
    content = '\n'.join(lines)
    lines = content.split('\n')

    # 2. GradeProfileEngine upgrade
    if fname in HAS_OLD_GRADE:
        # Find and replace the old engine
        old_start = None
        for i, line in enumerate(lines):
            if 'const GradeProfileEngine = {' in line:
                old_start = i
                break

        if old_start is not None:
            old_end = find_grade_engine_end(lines, old_start)
            if old_end is not None:
                # Check if helpers already exist
                has_helpers = 'normalizedEffectMeasure' in content
                has_cga = 'computeGradeAssessment' in content

                # Build replacement block
                replacement = ''
                if not has_helpers:
                    replacement += helpers_block + '\n\n'
                if not has_cga:
                    replacement += grade_assessment_block + '\n\n'
                replacement += grade_engine_block

                # Replace old engine with new
                lines[old_start:old_end+1] = [replacement]
                changes.append('GradeProfileEngine replaced')
                print(f"  REPLACED GradeProfileEngine (lines {old_start+1}-{old_end+1})")
            else:
                print(f"  WARNING: Could not find end of old GradeProfileEngine")
        else:
            print(f"  WARNING: No GradeProfileEngine found to replace")

    elif fname in NEED_FULL_GRADE:
        if 'const GradeProfileEngine' in content:
            print(f"  SKIP GradeProfileEngine: already present")
        else:
            # Find insertion point - before ZipBuilder or ReportEngine
            anchor = None
            for i, line in enumerate(lines):
                if '// ===== v12.0: INLINE ZIP BUILDER' in line or 'const ZipBuilder' in line:
                    anchor = i
                    break

            if anchor is None:
                # Try before ReportEngine
                for i, line in enumerate(lines):
                    if 'const ReportEngine' in line or 'ReportEngine' in line:
                        if 'const' in line:
                            anchor = i
                            break

            if anchor:
                # Build full block with helpers
                full_block = helpers_block + '\n\n' + grade_assessment_block + '\n\n' + grade_engine_block + '\n\n'
                lines.insert(anchor, full_block)
                changes.append('GradeProfileEngine + helpers added')
                print(f"  INSERTED full GradeProfileEngine before line {anchor+1}")
            else:
                print(f"  WARNING: No insertion point found for GradeProfileEngine in {fname}")

    elif fname == 'LivingMeta.html':
        if 'GradeProfileEngine' not in content:
            # Find anchor for LivingMeta
            anchor = None
            for i, line in enumerate(lines):
                if '// ===== v12.0: INLINE ZIP BUILDER' in line or 'const ZipBuilder' in line:
                    anchor = i
                    break
            if anchor:
                full_block = helpers_block + '\n\n' + grade_assessment_block + '\n\n' + grade_engine_block + '\n\n'
                lines.insert(anchor, full_block)
                changes.append('GradeProfileEngine + helpers added')
                print(f"  INSERTED full GradeProfileEngine before line {anchor+1}")

    # Rebuild content
    content = '\n'.join(lines)
    lines = content.split('\n')

    # 3. SoF button in UI
    if fname != 'LivingMeta.html' and 'exportSoFHTML' not in content:
        # Find the exportCSV button for GradeProfileEngine
        for i, line in enumerate(lines):
            if 'GradeProfileEngine.exportCSV()' in line and '<button' in line:
                lines.insert(i + 1, sof_button_html)
                changes.append('SoF button')
                print(f"  INSERTED SoF button after line {i+1}")
                break

    # Rebuild content
    content = '\n'.join(lines)
    lines = content.split('\n')

    # 4. Manuscript text
    if fname in NEED_MANUSCRIPT:
        if 'manuscript-text' in content:
            print(f"  SKIP manuscript: already present")
        else:
            # Insert HTML container - find visual abstract or waiting room section
            html_inserted = False
            for i, line in enumerate(lines):
                if 'Waiting Room' in line or 'wr-section' in line or 'waiting-room' in line.lower():
                    # Insert before this section
                    lines.insert(i, manuscript_html)
                    html_inserted = True
                    changes.append('manuscript HTML')
                    print(f"  INSERTED manuscript HTML before line {i+1}")
                    break

            if not html_inserted:
                # Try after report-content div
                for i, line in enumerate(lines):
                    if 'id="report-content"' in line:
                        # Find a good place after the visual abstract
                        for j in range(i, min(i + 100, len(lines))):
                            if 'visual-abstract' in lines[j] or 'Visual Abstract' in lines[j]:
                                # Find closing div of visual abstract section
                                for k in range(j, min(j + 30, len(lines))):
                                    if '</div>' in lines[k] and k > j + 2:
                                        lines.insert(k + 1, manuscript_html)
                                        html_inserted = True
                                        changes.append('manuscript HTML')
                                        print(f"  INSERTED manuscript HTML after line {k+1}")
                                        break
                                break
                        break

            if not html_inserted:
                print(f"  WARNING: Could not find place for manuscript HTML in {fname}")

            # Rebuild content
            content = '\n'.join(lines)
            lines = content.split('\n')

            # Insert JS functions - before downloadPDFReport
            js_inserted = False
            for i, line in enumerate(lines):
                if 'function downloadPDFReport()' in line:
                    lines.insert(i, manuscript_js_block + '\n')
                    js_inserted = True
                    changes.append('manuscript JS')
                    print(f"  INSERTED manuscript JS before line {i+1}")
                    break

            if not js_inserted:
                print(f"  WARNING: Could not find downloadPDFReport anchor for manuscript JS in {fname}")

            # Rebuild content
            content = '\n'.join(lines)
            lines = content.split('\n')

            # Wire into report generate
            wired = False
            for i, line in enumerate(lines):
                if "GradeProfileEngine.renderTable('grade-profile-container')" in line:
                    lines.insert(i + 1, "                // Auto-generate manuscript Methods & Results text")
                    lines.insert(i + 2, "                if (typeof generateManuscriptText === 'function') generateManuscriptText();")
                    wired = True
                    changes.append('manuscript wired')
                    print(f"  WIRED generateManuscriptText after line {i+1}")
                    break

            if not wired:
                # Try alternate anchor
                for i, line in enumerate(lines):
                    if 'reportEl.classList.remove' in line or 'report-content' in line:
                        if 'classList.remove' in line:
                            lines.insert(i, "                if (typeof generateManuscriptText === 'function') generateManuscriptText();")
                            wired = True
                            changes.append('manuscript wired (alt)')
                            print(f"  WIRED generateManuscriptText before line {i+1}")
                            break

            if not wired:
                print(f"  WARNING: Could not wire generateManuscriptText in {fname}")

    # Write file
    if changes:
        content = '\n'.join(lines)
        write_file(fpath, content)
        results[fname] = changes
        print(f"  SAVED: {', '.join(changes)}")
    else:
        results[fname] = ['no changes needed']
        print(f"  No changes needed")

# ========== VALIDATION ==========
print("\n\n========== VALIDATION ==========")
for fname in set(NEED_TEXT_EXTRACTOR + HAS_OLD_GRADE + NEED_FULL_GRADE + NEED_MANUSCRIPT):
    fpath = os.path.join(DIR, fname)
    if not os.path.exists(fpath):
        continue
    content = read_file(fpath)

    has_te = 'const TextExtractor' in content
    has_gpe = 'GradeProfileEngine' in content
    has_sof = 'exportSoFHTML' in content
    has_ms = 'generateManuscriptText' in content

    # Div balance
    div_opens = len(re.findall(r'<div[\s>]', content))
    div_closes = content.count('</div>')
    div_ok = abs(div_opens - div_closes) <= 2  # Allow small tolerance for regex in JS

    status = f"TE:{'Y' if has_te else 'N'} GPE:{'Y' if has_gpe else 'N'} SoF:{'Y' if has_sof else 'N'} MS:{'Y' if has_ms else 'N'} DIV:{'OK' if div_ok else f'WARN({div_opens}/{div_closes})'}"
    print(f"  {fname}: {status}")

print("\n========== SUMMARY ==========")
for fname, chg in sorted(results.items()):
    print(f"  {fname}: {', '.join(chg)}")
print("\nDone. Run test_livingmeta.py to verify.")
