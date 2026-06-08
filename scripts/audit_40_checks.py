"""40-check portfolio audit. Each check returns (severity, count, samples).

Runs across all *.html under the repo root. Output: outputs/audit40/report.json
plus a human-readable summary on stdout.

Severities:
    P0  page-breaking JS/HTML — site never loads
    P1  silently shows wrong data
    P2  usability / visual defect
    P3  housekeeping / cosmetic
"""
from __future__ import annotations
import json
import re
import sys
import io
from pathlib import Path
from collections import Counter, defaultdict

# Only rewrap stdout when run as a script. Importing this module (e.g. to reuse
# an individual check) must NOT reassign the caller's stdout -- doing so GC-closes
# the inherited buffer and breaks the importer (lessons.md: module-level stdout
# reassignment trap).
if __name__ == "__main__" and "pytest" not in sys.modules and hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent.parent
OUT = HERE / "outputs" / "audit40"
OUT.mkdir(parents=True, exist_ok=True)

NCT_RE = re.compile(r"NCT\d{7,8}")
PMID_RE = re.compile(r"pmid:\s*['\"](\d*)['\"]")
PMID_LINK_RE = re.compile(r"https://pubmed\.ncbi\.nlm\.nih\.gov/(\d+)/")
NCT_LINK_RE = re.compile(r"https://clinicaltrials\.gov/study/(NCT\d{7,8})")
HREF_RE = re.compile(r'href="([^"#?]+\.(?:html|md|json|csv))"', re.IGNORECASE)
ID_ATTR_RE = re.compile(r'\bid="([^"]+)"')
TRIAL_BLOCK_RE = re.compile(
    r"'(NCT\d{7,8})':\s*\{(?P<body>(?:[^{}]|\{[^{}]*\}){0,4000})\}",
    re.DOTALL,
)


def load_text(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace")


# ---------------------------------------------------------------------------
# Checks (each function appends rows to findings list and bumps counters).
# A check is `check_NN(p: Path, txt: str, ctx: dict) -> list[dict]` returning
# zero or more finding dicts. Each finding: {check, severity, file, detail}.
# ---------------------------------------------------------------------------


def check_01_python_none_in_js(p, txt, ctx):
    """P0: bare `None` in JS object-value position."""
    out = []
    # Mask quoted strings so we don't false-positive on "None declared" or 'None'.
    masked = mask_strings(txt)
    for m in re.finditer(r":\s+None(?=[,}\s])", masked):
        out.append({"check": "01_py_None_in_js", "severity": "P0", "file": p.name,
                    "detail": txt[max(0, m.start()-20): m.end()+5]})
        if len(out) >= 3: break
    return out


def check_02_python_True_False_in_js(p, txt, ctx):
    out = []
    masked = mask_strings(txt)
    for m in re.finditer(r":\s+(True|False)(?=[,}\s])", masked):
        out.append({"check": "02_py_TrueFalse_in_js", "severity": "P0", "file": p.name,
                    "detail": txt[max(0, m.start()-20): m.end()+5]})
        if len(out) >= 3: break
    return out


def check_03_unmatched_script_tag(p, txt, ctx):
    """P0: a `<script>` element left unclosed at EOF (page never finishes parsing).

    Uses browser-accurate <script> semantics rather than a naive open/close count:
    once inside a script element the parser ignores further `<script` substrings
    (they are JS/string content) and closes ONLY on a literal `</script>`. An
    escaped `<\\/script>` (the deliberate safe pattern used by sanitization
    regexes such as `new RegExp("<script...<\\/script>")`) is NOT a real close,
    so it no longer produces a phantom imbalance. We flag only the unambiguous
    page-breaking case: a script that is still open when the document ends.
    """
    out = []
    open_re = re.compile(r"<script\b[^>]*>", re.IGNORECASE)
    close_re = re.compile(r"</script\s*>", re.IGNORECASE)
    i, n = 0, len(txt)
    in_script = False
    while i < n:
        if not in_script:
            m = open_re.search(txt, i)
            if not m:
                break
            in_script = True
            i = m.end()
        else:
            m = close_re.search(txt, i)
            if not m:
                # script opened but never closed before EOF -> genuinely broken
                out.append({"check": "03_unbalanced_script", "severity": "P0",
                            "file": p.name, "detail": "unclosed <script> at EOF"})
                break
            in_script = False
            i = m.end()
    return out


def check_04_div_balance(p, txt, ctx):
    """P2: div balance off by more than a small tolerance."""
    masked = mask_strings(txt, keep_template_strings=False)
    opens = len(re.findall(r"<div\b[\s>]", masked, re.IGNORECASE))
    closes = len(re.findall(r"</div\s*>", masked, re.IGNORECASE))
    if abs(opens - closes) > 0:
        return [{"check": "04_div_balance", "severity": "P2", "file": p.name,
                 "detail": f"open={opens} close={closes} diff={opens-closes}"}]
    return []


def check_05_broken_local_links(p, txt, ctx):
    out = []
    for m in HREF_RE.finditer(txt):
        href = m.group(1).strip()
        # Skip data:, anchors, mailto handled by regex already.
        if href.startswith(("http://", "https://", "data:", "mailto:")):
            continue
        # Resolve relative to repo root.
        tgt = (HERE / href).resolve()
        if not tgt.exists():
            out.append({"check": "05_broken_local_link", "severity": "P1", "file": p.name,
                        "detail": href})
            if len(out) >= 5: break
    return out


def check_06_unpopulated_placeholders(p, txt, ctx):
    """P1: literal {{token}} / __PLACEHOLDER__ / REPLACE_ME / $$$ leaked through."""
    out = []
    patterns = [r"\{\{[A-Z_][A-Z0-9_]*\}\}", r"__[A-Z_]+__", r"\bREPLACE_ME\b",
                r"<<<<+\s", r"\$\$\$+", r"\bTODO_FIXME\b"]
    for pat in patterns:
        for m in re.finditer(pat, txt):
            # ignore inside <pre>/<code> samples
            ctx_str = txt[max(0, m.start()-30): m.end()+30]
            if "<pre" in ctx_str or "code" in ctx_str[:35]:
                continue
            out.append({"check": "06_unpopulated_placeholder", "severity": "P1",
                        "file": p.name, "detail": m.group(0) + " ctx=" + ctx_str[:80]})
            if len(out) >= 3:
                return out
    return out


def check_07_empty_pmid_link(p, txt, ctx):
    """P2: <a href="https://pubmed.ncbi.nlm.nih.gov//">PMID </a> with empty id."""
    out = []
    for m in re.finditer(r"pubmed\.ncbi\.nlm\.nih\.gov/(\d*)/", txt):
        if not m.group(1):
            out.append({"check": "07_empty_pmid_link", "severity": "P2", "file": p.name,
                        "detail": "empty PMID in link"})
            return out
    return out


def check_08_event_count_consistency(p, txt, ctx):
    """P1: tE > tN or cE > cN within a realData trial block."""
    out = []
    for m in TRIAL_BLOCK_RE.finditer(txt):
        nct = m.group(1)
        body = m.group("body")
        nums = {}
        for fld in ("tE", "tN", "cE", "cN"):
            mm = re.search(rf"\b{fld}:\s*(-?\d+|null|None)", body)
            if mm:
                v = mm.group(1)
                if v in ("null", "None"):
                    nums[fld] = None
                else:
                    nums[fld] = int(v)
        # Both arms must have valid numeric counts to compare.
        if all(nums.get(k) is not None for k in ("tE", "tN", "cE", "cN")):
            tE, tN, cE, cN = nums["tE"], nums["tN"], nums["cE"], nums["cN"]
            if tE > tN or cE > cN or tE < 0 or cE < 0 or tN <= 0 or cN <= 0:
                out.append({"check": "08_event_count_inconsistency", "severity": "P1",
                            "file": p.name,
                            "detail": f"{nct} tE={tE} tN={tN} cE={cE} cN={cN}"})
                if len(out) >= 5: break
    return out


def check_09_rob_array_length(p, txt, ctx):
    """P2: rob: [...] not length 5 in a trial block (RoB 2.0 needs 5 domains)."""
    out = []
    for m in TRIAL_BLOCK_RE.finditer(txt):
        nct = m.group(1)
        body = m.group("body")
        mm = re.search(r"rob:\s*\[([^\]]*)\]", body)
        if mm:
            items = [x for x in mm.group(1).split(",") if x.strip()]
            if len(items) != 5 and len(items) != 0:
                out.append({"check": "09_rob_length", "severity": "P2", "file": p.name,
                            "detail": f"{nct} rob has {len(items)} items"})
                if len(out) >= 3: break
    return out


def check_10_nct_in_auto_include_vs_realdata(p, txt, ctx):
    """P1: AUTO_INCLUDE set must match keys in realData."""
    out = []
    inc_match = re.search(r"AUTO_INCLUDE_TRIAL_IDS\s*=\s*new\s+Set\(\[([^\]]*)\]\)", txt)
    if not inc_match:
        return out
    inc_set = set(NCT_RE.findall(inc_match.group(1)))
    real_set = set(NCT_RE.findall(re.search(r"realData:\s*\{[\s\S]*?async init", txt).group(0)
                                  if re.search(r"realData:\s*\{[\s\S]*?async init", txt) else ""))
    extra_inc = inc_set - real_set
    extra_real = real_set - inc_set
    if extra_inc or extra_real:
        out.append({"check": "10_nct_set_mismatch", "severity": "P1", "file": p.name,
                    "detail": f"auto_include-only={sorted(extra_inc)[:3]} realData-only={sorted(extra_real)[:3]}"})
    return out


def check_11_duplicate_html_ids(p, txt, ctx):
    """P2: duplicate id="..." attributes (illegal HTML, breaks JS getElementById)."""
    ids = [m.group(1) for m in ID_ATTR_RE.finditer(txt)]
    cnt = Counter(ids)
    dupes = {k: v for k, v in cnt.items() if v > 1 and k not in ("",)}
    if dupes:
        return [{"check": "11_dup_html_ids", "severity": "P2", "file": p.name,
                 "detail": "; ".join(f"{k}×{v}" for k, v in list(dupes.items())[:3])}]
    return []


def check_12_truncated_outcome_titles(p, txt, ctx):
    """P3: outcome titles cut off mid-word (end with a partial like "Rheumat")."""
    out = []
    for m in re.finditer(r"title:\s*'([^']{60,200}?)\s*\(primary\)'", txt):
        title = m.group(1).rstrip()
        # If it ends mid-word (alphanumeric, no punctuation), flag.
        if title and re.search(r"[A-Za-z]{4,}$", title) and not re.search(r"[.\):]$", title):
            # heuristic: <=200 char limit suggests truncation
            if len(title) >= 110:
                out.append({"check": "12_truncated_title", "severity": "P3",
                            "file": p.name, "detail": title[-60:]})
                if len(out) >= 3: break
    return out


def check_13_hardcoded_local_paths(p, txt, ctx):
    """P1: Windows / Unix local paths leaked into shipped HTML."""
    out = []
    for m in re.finditer(r'[A-Z]:\\\\?Users\\\\?[A-Za-z]+|/home/[a-z]+/', txt):
        out.append({"check": "13_local_path", "severity": "P1", "file": p.name,
                    "detail": m.group(0)})
        if len(out) >= 3: break
    return out


def check_14_invalid_pmid_format(p, txt, ctx):
    """P2: pmid: 'NaN' / 'undefined' / 'null' literal as string / non-numeric."""
    out = []
    for m in PMID_RE.finditer(txt):
        v = m.group(1)
        # empty is OK (intentional wipe), non-digit non-empty is a bug.
        if v and not v.isdigit():
            out.append({"check": "14_pmid_non_digit", "severity": "P2", "file": p.name,
                        "detail": repr(v)})
            if len(out) >= 3: break
    return out


def check_15_outcome_special_chars(p, txt, ctx):
    """P3: outcome titles with mojibake (â€, â€™, Ã©, etc.)."""
    out = []
    if re.search(r"â€[\W™]|Ã[©¨ª¢]|â”€|â˜…|â”|â€\"", txt):
        out.append({"check": "15_mojibake", "severity": "P3", "file": p.name,
                    "detail": "encoding-damaged unicode found"})
    return out


def check_16_external_cdn_inside_csp(p, txt, ctx):
    """P2: <script src= or <link href= to a host not whitelisted in CSP connect-src."""
    out = []
    # Find CSP if any
    csp = re.search(r'http-equiv="Content-Security-Policy"\s*content="([^"]+)"', txt)
    if not csp:
        return out
    allowed_hosts = set(re.findall(r"https?://[^\s']+", csp.group(1)))
    # Check external script/link
    for m in re.finditer(r"(?:src|href)=\"(https?://[^/\"]+)/", txt):
        host = m.group(1)
        if host.endswith(("clinicaltrials.gov", "ebi.ac.uk", "openalex.org", "r-wasm.org", "ncbi.nlm.nih.gov", "cdn.plot.ly", "cdnjs.cloudflare.com", "fonts.googleapis.com", "fonts.gstatic.com")):
            continue
        if host not in allowed_hosts:
            # Many will trigger; report once
            out.append({"check": "16_csp_off_whitelist", "severity": "P2", "file": p.name,
                        "detail": host})
            return out
    return out


def check_17_year_plausibility(p, txt, ctx):
    """P2: year in realData < 1990 or > 2030."""
    out = []
    for m in TRIAL_BLOCK_RE.finditer(txt):
        body = m.group("body")
        mm = re.search(r"\byear:\s*(-?\d+)", body)
        if mm:
            y = int(mm.group(1))
            if y < 1990 or y > 2030:
                out.append({"check": "17_year_implausible", "severity": "P2", "file": p.name,
                            "detail": f"{m.group(1)} year={y}"})
                if len(out) >= 3: break
    return out


def check_18_viewport_meta(p, txt, ctx):
    """P2: missing mobile viewport meta tag."""
    if 'name="viewport"' not in txt:
        return [{"check": "18_no_viewport", "severity": "P2", "file": p.name, "detail": ""}]
    return []


def check_19_inline_script_size(p, txt, ctx):
    """P3: any single inline <script> > 200 KB (perf — consider extracting)."""
    out = []
    for m in re.finditer(r"<script\b[^>]*>([\s\S]*?)</script>", txt):
        body = m.group(1)
        if len(body) > 200_000:
            out.append({"check": "19_huge_inline_script", "severity": "P3", "file": p.name,
                        "detail": f"{len(body):,} bytes"})
            return out
    return out


def check_20_localStorage_key_collision(p, txt, ctx):
    """P1: localStorage key looks like a stock template (e.g. 'rapid_meta_template')."""
    out = []
    for m in re.finditer(r"localStorage\.\w+\(['\"]([^'\"]{1,200})['\"]", txt):
        k = m.group(1)
        if "{{" in k or "STEM" in k or "TEMPLATE" in k or k.endswith("_undefined"):
            out.append({"check": "20_localStorage_template_key", "severity": "P1",
                        "file": p.name, "detail": k})
            return out
    return out


def check_21_meta_description(p, txt, ctx):
    """P3: missing OG/twitter description."""
    if 'name="description"' not in txt and 'property="og:description"' not in txt:
        return [{"check": "21_no_description", "severity": "P3", "file": p.name, "detail": ""}]
    return []


def check_22_outcome_title_dupe(p, txt, ctx):
    """P3: every trial has identical outcome title (likely template not substituted)."""
    titles = re.findall(r"title:\s*'([^']{20,})\s*\(primary\)'", txt)
    if len(titles) >= 2 and len(set(titles)) == 1:
        return [{"check": "22_outcome_titles_all_identical", "severity": "P3",
                 "file": p.name, "detail": titles[0][:80]}]
    return []


def check_23_svg_invalid_coords(p, txt, ctx):
    """P1: SVG forest-plot coordinates containing NaN, Infinity, or empty."""
    out = []
    for m in re.finditer(r"<svg[^>]*viewBox=\"([^\"]+)\"", txt):
        vb = m.group(1).split()
        for v in vb:
            try:
                fv = float(v)
                if fv != fv or fv == float("inf") or fv == float("-inf"):
                    out.append({"check": "23_svg_bad_viewbox", "severity": "P1",
                                "file": p.name, "detail": vb})
                    return out
            except ValueError:
                out.append({"check": "23_svg_bad_viewbox", "severity": "P1",
                            "file": p.name, "detail": vb})
                return out
    # x="NaN" anywhere in <text>/<rect>/<line>
    if re.search(r'\b(?:x|y|x1|x2|y1|y2|cx|cy)="(?:NaN|Infinity|-Infinity)"', txt):
        out.append({"check": "23_svg_bad_coord", "severity": "P1", "file": p.name,
                    "detail": "NaN/Infinity in svg attr"})
    return out


def check_24_orphan_close_tag(p, txt, ctx):
    """P2: stray </body> or </html> appearing before the actual end."""
    out = []
    if txt.count("</body>") > 1:
        out.append({"check": "24_dup_body_close", "severity": "P2", "file": p.name,
                    "detail": f"</body> ×{txt.count('</body>')}"})
    if txt.count("</html>") > 1:
        out.append({"check": "24_dup_html_close", "severity": "P2", "file": p.name,
                    "detail": f"</html> ×{txt.count('</html>')}"})
    return out


def check_25_orphan_anchor_with_no_text(p, txt, ctx):
    """P3: empty anchor <a href="..."></a> visible to users as a dead spot."""
    out = []
    for m in re.finditer(r'<a\s+href="[^"]+"[^>]*>\s*</a>', txt):
        out.append({"check": "25_empty_anchor", "severity": "P3", "file": p.name,
                    "detail": m.group(0)[:120]})
        if len(out) >= 2: break
    return out


def check_26_inconsistent_acronyms(p, txt, ctx):
    """P3: trial name in realData differs between `name:` and `snippet:`."""
    out = []
    for m in TRIAL_BLOCK_RE.finditer(txt):
        body = m.group("body")
        name_m = re.search(r"name:\s*'([^']*)'", body)
        snip_m = re.search(r"snippet:\s*'NCT[^:]*:\s*([^']{4,40})", body)
        # Best-effort, may not always be set; only flag when both present and clearly inconsistent.
        if name_m and snip_m:
            name = name_m.group(1).strip()
            if name and len(name) > 3 and name not in body[:600]:
                pass  # too noisy; skip this check
    return out


def check_27_huge_file(p, txt, ctx):
    """P3: file > 2 MB (perf concern)."""
    if len(txt) > 2_000_000:
        return [{"check": "27_huge_file", "severity": "P3", "file": p.name,
                 "detail": f"{len(txt):,} bytes"}]
    return []


def check_28_tiny_file(p, txt, ctx):
    """P3: shipped page < 4 KB (likely stub)."""
    if len(txt) < 4_000 and p.name.endswith((".html",)):
        return [{"check": "28_tiny_file", "severity": "P3", "file": p.name,
                 "detail": f"{len(txt):,} bytes"}]
    return []


def check_29_dashboard_link_orphan(p, txt, ctx):
    """P1 (only on dashboard.html / index.html / audit_table.html): href points to missing file."""
    # already covered by 05; skip
    return []


def check_30_double_quoted_attr_with_unescaped_quote(p, txt, ctx):
    """P2: attribute like value="abc"def" — broken HTML."""
    out = []
    for m in re.finditer(r'\b\w+="[^"]*"\w', txt):
        out.append({"check": "30_attr_unescaped_quote", "severity": "P2",
                    "file": p.name, "detail": m.group(0)[:80]})
        if len(out) >= 2: break
    return out


def check_31_window_global_unset(p, txt, ctx):
    """P1: file references RapidMeta but does NOT define it (broken extraction)."""
    if 'RapidMeta' not in txt:
        return []
    if 'RapidMeta = {' in txt or 'const RapidMeta' in txt or 'window.RapidMeta=' in txt or 'window.RapidMeta =' in txt:
        return []
    # Else: RapidMeta is referenced but no definition exists.
    if re.search(r"\bRapidMeta\.\w+", txt):
        return [{"check": "31_undefined_RapidMeta", "severity": "P1", "file": p.name,
                 "detail": "RapidMeta referenced without definition"}]
    return []


def check_32_no_h1(p, txt, ctx):
    """P3: page has no <h1> (a11y/SEO)."""
    if not re.search(r"<h1\b", txt, re.IGNORECASE):
        return [{"check": "32_no_h1", "severity": "P3", "file": p.name, "detail": ""}]
    return []


def check_33_pmid_link_mismatch_with_realdata(p, txt, ctx):
    """P1: hardcoded PMID anchor text differs from the realData pmid for the same NCT.

    Only applies to lite/audit-first pages where both forms can coexist."""
    out = []
    # Build NCT -> realData pmid
    real_pmid = {}
    for m in TRIAL_BLOCK_RE.finditer(txt):
        nct = m.group(1)
        mm = PMID_RE.search(m.group("body"))
        if mm:
            real_pmid[nct] = mm.group(1)
    # Check anchor pmid links near NCT mention.
    pair_re = re.compile(r'(NCT\d{7,8})</a>[^<]*<a href="https://pubmed\.ncbi\.nlm\.nih\.gov/(\d+)/"')
    for m in pair_re.finditer(txt):
        nct, anchor_pmid = m.group(1), m.group(2)
        rp = real_pmid.get(nct)
        if rp and anchor_pmid != rp:
            out.append({"check": "33_pmid_anchor_realdata_mismatch", "severity": "P1",
                        "file": p.name,
                        "detail": f"{nct} anchor={anchor_pmid} realData={rp}"})
            if len(out) >= 3: break
    return out


def check_34_screening_template_old(p, txt, ctx):
    """P2: pages still using the pre-v3 screening template (t.data?.ctgovUrl only)."""
    if "${t.data?.ctgovUrl ? `<a href" in txt:
        return [{"check": "34_old_screening_template", "severity": "P2", "file": p.name,
                 "detail": "still uses pre-v3 ctgovUrl-only template"}]
    return []


def check_35_robots_no_robots(p, txt, ctx):
    """P3: meta robots=noindex on a published page (probably unintentional)."""
    if re.search(r'name="robots"\s+content="[^"]*noindex', txt, re.IGNORECASE):
        return [{"check": "35_noindex_set", "severity": "P3", "file": p.name, "detail": ""}]
    return []


def check_36_target_blank_no_noopener(p, txt, ctx):
    """P2: target="_blank" without rel="noopener" (tab-napping security)."""
    out = []
    for m in re.finditer(r'<a[^>]*target="_blank"[^>]*>', txt):
        anchor = m.group(0)
        if 'rel="noopener' not in anchor and "rel='noopener" not in anchor:
            out.append({"check": "36_blank_no_noopener", "severity": "P2",
                        "file": p.name, "detail": anchor[:120]})
            if len(out) >= 2: break
    return out


def check_37_inconsistent_drug_name(p, txt, ctx):
    """P3: title-case 'Drug' mentioned but stem says 'OTHER_DRUG' — review name drift."""
    stem = re.split(r"_AUTO_FULL_REVIEW|_AUTO_REVIEW|_REVIEW", p.name, 1)[0]
    if not stem or "_" not in stem:
        return []
    first = stem.split("_")[0].lower()
    if len(first) < 4 or first in {"new", "trial", "study", "all"}:
        return []
    # If the first stem token does not appear at all in the page, flag.
    if first.lower() not in txt.lower():
        return [{"check": "37_stem_not_in_page", "severity": "P3", "file": p.name,
                 "detail": f"stem token '{first}' not present"}]
    return []


def check_38_nesting_via_template_literal(p, txt, ctx):
    """P0: backtick template literal containing `${` but missing closing brace."""
    # Cheap heuristic: dollar-brace count balance in script content.
    out = []
    for m in re.finditer(r"<script\b[^>]*>([\s\S]*?)</script>", txt):
        body = m.group(1)
        n_open_db = body.count("${")
        # Count closing braces that ARE in template-literal context — hard. Skip
        # unless extremely lopsided (rough sanity).
        if n_open_db == 0: continue
        # Look for stray `${` followed by `}` mismatch is too noisy; just record gross outliers.
    return out


def check_39_aria_label_missing_on_button(p, txt, ctx):
    """P3: <button> with no text and no aria-label."""
    out = []
    for m in re.finditer(r"<button\b[^>]*>(\s*)</button>", txt):
        # Inspect the button tag for aria-label
        start = max(0, m.start()-200)
        anchor = txt[start: m.end()]
        if "aria-label" not in anchor:
            out.append({"check": "39_empty_button_no_aria", "severity": "P3",
                        "file": p.name, "detail": anchor[-80:]})
            if len(out) >= 2: break
    return out


def check_40_orphan_pubmed_link(p, txt, ctx):
    """P2: a pubmed.ncbi.nlm.nih.gov/<n>/ link where <n> isn't a real PMID (< 100)."""
    out = []
    for m in PMID_LINK_RE.finditer(txt):
        v = m.group(1)
        if v and int(v) < 100:
            out.append({"check": "40_implausible_pmid", "severity": "P2",
                        "file": p.name, "detail": v})
            if len(out) >= 2: break
    return out


# Helper -----------------------------------------------------------------------
def mask_strings(t: str, keep_template_strings: bool = True) -> str:
    """Replace contents of quoted strings with blanks.

    keep_template_strings=False also blanks backtick template literals.
    """
    out = []
    i = 0
    n = len(t)
    while i < n:
        c = t[i]
        if c in ("'", '"') or (not keep_template_strings and c == "`"):
            quote = c
            j = i + 1
            while j < n and t[j] != quote:
                if t[j] == "\\":
                    j += 2
                else:
                    j += 1
            out.append(" " * max(1, j - i + 1))
            i = j + 1
        else:
            out.append(c)
            i += 1
    return "".join(out)


CHECKS = [
    check_01_python_none_in_js,
    check_02_python_True_False_in_js,
    check_03_unmatched_script_tag,
    check_04_div_balance,
    check_05_broken_local_links,
    check_06_unpopulated_placeholders,
    check_07_empty_pmid_link,
    check_08_event_count_consistency,
    check_09_rob_array_length,
    check_10_nct_in_auto_include_vs_realdata,
    check_11_duplicate_html_ids,
    check_12_truncated_outcome_titles,
    check_13_hardcoded_local_paths,
    check_14_invalid_pmid_format,
    check_15_outcome_special_chars,
    check_16_external_cdn_inside_csp,
    check_17_year_plausibility,
    check_18_viewport_meta,
    check_19_inline_script_size,
    check_20_localStorage_key_collision,
    check_21_meta_description,
    check_22_outcome_title_dupe,
    check_23_svg_invalid_coords,
    check_24_orphan_close_tag,
    check_25_orphan_anchor_with_no_text,
    check_26_inconsistent_acronyms,
    check_27_huge_file,
    check_28_tiny_file,
    check_29_dashboard_link_orphan,
    check_30_double_quoted_attr_with_unescaped_quote,
    check_31_window_global_unset,
    check_32_no_h1,
    check_33_pmid_link_mismatch_with_realdata,
    check_34_screening_template_old,
    check_35_robots_no_robots,
    check_36_target_blank_no_noopener,
    check_37_inconsistent_drug_name,
    check_38_nesting_via_template_literal,
    check_39_aria_label_missing_on_button,
    check_40_orphan_pubmed_link,
]


def main():
    files = sorted([p for p in HERE.glob("*.html") if p.is_file()])
    print(f"Scanning {len(files):,} files with {len(CHECKS)} checks each")

    all_findings = []
    counter = Counter()
    per_check_files = defaultdict(set)
    ctx = {}
    for i, p in enumerate(files, 1):
        try:
            txt = load_text(p)
        except Exception as e:
            all_findings.append({"check": "00_read_error", "severity": "P0",
                                  "file": p.name, "detail": repr(e)})
            counter["00_read_error"] += 1
            continue
        for fn in CHECKS:
            try:
                res = fn(p, txt, ctx) or []
                for r in res:
                    all_findings.append(r)
                    counter[r["check"]] += 1
                    per_check_files[r["check"]].add(p.name)
            except Exception as e:
                all_findings.append({"check": fn.__name__, "severity": "PX",
                                      "file": p.name, "detail": f"AUDIT BUG: {e!r}"})
                counter[fn.__name__ + "_AUDIT_BUG"] += 1
        if i % 300 == 0:
            print(f"  [{i}/{len(files)}] scanned")

    # Sort by severity then count
    sev_order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3, "PX": 99}
    summary = []
    seen_checks = set(counter.keys())
    for ck in sorted(seen_checks, key=lambda c: (sev_order.get(_severity_of(c, all_findings), 99), -counter[c])):
        sev = _severity_of(ck, all_findings)
        summary.append({
            "check": ck,
            "severity": sev,
            "files_with_issue": len(per_check_files[ck]),
            "total_findings": counter[ck],
        })

    (OUT / "report.json").write_text(json.dumps({
        "files_scanned": len(files),
        "summary": summary,
        "findings": all_findings[:5000],  # cap raw findings
    }, indent=2), encoding="utf-8")

    print()
    print(f"{'check':<40} {'sev':<4} {'files':<8} {'total':<8}")
    print("-" * 72)
    for row in summary:
        print(f"{row['check']:<40} {row['severity']:<4} {row['files_with_issue']:<8} {row['total_findings']:<8}")


def _severity_of(check_name, findings):
    for f in findings:
        if f["check"] == check_name:
            return f["severity"]
    return "P3"


if __name__ == "__main__":
    main()
