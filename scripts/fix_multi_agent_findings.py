"""Apply the high-confidence multi-agent consensus findings.

For each ≥2-of-3 HIGH-severity finding where ground truth was provided by
Agent 3 (identity triangulation), apply the appropriate corrective:

  WAYFINDER (id=20)         : likely fabricated — null pmid + null hr fields
  CheckMate-238-ADJ (id=26) : trial legitimate; HRs diverge across reviews (Op C tier 2)
  QuANTUM-R (id=27)         : NCT belongs to QuANTUM-First — rename key to NULLED:NCT02668653 in this review only
  PSILO-MDD (id=33)         : wrong PMID — null pmid
  QUILT-3032 (id=47)        : NCT04165116 wrong; correct is NCT03022825 — rename key
  Vivitrol-OUD (id=49)      : estimandType mismatch (MD labelled HR) — null estimandType to force re-extract
  ILLUMENATE-EU (id=52)     : NCT01858363 wrong; correct is NCT01927068 — rename key
  PEDAP (id=58)             : NCT04420572 wrong; correct is NCT04796779 — rename key
  HELIOS-B (id=67)          : NCT05534659 wrong; correct is NCT04153149 — rename key
  MEZAGITAMAB-ITP (id=71)   : impossible PMID — null pmid
  REGAIN/AMBER (id=50)      : NCT03533790 is AMBER not REGAIN — null pmid + flag for relabel

Each operation is idempotent and writes a log to
outputs/extraction_audit/multi_agent_fixes_applied.json.
"""
from __future__ import annotations
import json, re, sys, io
from pathlib import Path

if hasattr(sys.stdout, "buffer") and getattr(sys.stdout, "encoding", "").lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent.parent

DRY = "--dry-run" in sys.argv

# Each op: (review_stem, nct_or_pattern, op, params)
# Op codes:
#   NULL_KEY  — rename realData["NCT..."] to "NULLED:..." (also acronyms dict)
#   NULL_PMID — set pmid: null in the realData entry
#   NULL_HR   — set publishedHR/hrLCI/hrUCI/tE/tN/cE/cN to null (full data void)
OPS = [
    # WAYFINDER — likely fabricated (identical effect to SIROCCO, NCT doesn't match)
    {"review":"SEVERE_ASTHMA_BIOLOGICS_REVIEW","nct":"NCT04039113","op":"NULL_PMID",
     "reason":"WAYFINDER agent-consensus 3-of-3 HIGH: name+NCT don't match any real tezepelumab program; effect identical to SIROCCO (copy-paste fingerprint)"},
    # QuANTUM-R (id=27) — NCT02668653 belongs to QuANTUM-First
    {"review":"AML_TARGETED_NEW_REVIEW","nct":"NCT02668653","op":"NULL_KEY",
     "reason":"QuANTUM-R label on NCT02668653 wrong; NCT belongs to QuANTUM-First (newly diagnosed FLT3+AML, Erba Lancet 2023). QuANTUM-R is a different trial."},
    # PSILO-MDD (id=33) — wrong PMID
    {"review":"DEPRESSION_NEW_RAPID_REVIEW","nct":"NCT03775200","op":"NULL_PMID",
     "reason":"PSILO-MDD label uses PMID 33999283 which is not the COMP-001 Goodwin NEJM 2022 paper for NCT03775200"},
    # QUILT-3032 (id=47) — NCT04165116 wrong, correct is NCT03022825
    {"review":"BLADDER_NMIBC_NEW_NMA_REVIEW","nct":"NCT04165116","op":"NULL_KEY",
     "reason":"QUILT-3032 N-803+BCG (Chamie 2023) correct NCT is NCT03022825 (originally QUILT-3.0xx); NCT04165116 is a different study"},
    # Vivitrol-OUD (id=49) — estimandType=MD but data is HR
    {"review":"OUD_NEW_AGENTS_NMA_REVIEW","nct":"NCT00604682","op":"NULL_ESTIMAND",
     "reason":"estimandType=MD inconsistent with HR=7.0 (CI 3.0-11.0); X:BOT relapse outcome — needs re-extraction"},
    # ILLUMENATE-EU (id=52) — wrong NCT, correct is NCT01927068
    {"review":"PERIPHERAL_DCB_PAD_NMA_REVIEW","nct":"NCT01858363","op":"NULL_KEY",
     "reason":"ILLUMENATE EU (Stellarex DCB, Krishnan Circulation 2017) correct NCT is NCT01927068; NCT01858363 is a different DCB study"},
    # PEDAP (id=58) — wrong NCT, correct is NCT04796779
    {"review":"T1D_CLOSED_LOOP_NMA_REVIEW","nct":"NCT04420572","op":"NULL_KEY",
     "reason":"PEDAP (Wadwa NEJM 2023) correct NCT is NCT04796779; NCT04420572 doesn't match"},
    # HELIOS-B (id=67) — wrong NCT, correct is NCT04153149
    {"review":"ATTR_CM_REVIEW","nct":"NCT05534659","op":"NULL_KEY",
     "reason":"HELIOS-B vutrisiran ATTR-CM (Fontana NEJM 2024) correct NCT is NCT04153149; NCT05534659 does not match"},
    # MEZAGITAMAB-ITP (id=71) — impossible PMID
    {"review":"ITP_NEW_AGENTS_REVIEW","nct":"NCT04278924","op":"NULL_PMID",
     "reason":"PMID 41950473 is >4×10^7, impossible for current PubMed range — fabricated"},
    # REGAIN/AMBER (id=50) — NCT03533790 is AMBER not REGAIN; values 145/145 implausible
    {"review":"HYPERKALEMIA_K_BINDER_NMA_REVIEW","nct":"NCT03533790","op":"NULL_KEY",
     "reason":"NCT03533790 is AMBER trial (patiromer+spironolactone Agarwal Lancet 2019), labelled 'REGAIN' (galcanezumab CH = different trial); extracted tE=tN=145 (100% response) is biologically implausible — provenance broken"},
    # ATTRibute-CM duplicate (id=24) — fabricated PMID 41205147
    {"review":"ACORAMIDIS_ATTR_CM_REVIEW","nct":"NCT03860935","op":"NULL_PMID_IF_IMPOSSIBLE",
     "reason":"PMID 41205147 is >4×10^7, impossible — fabricated"},
]


def find_block(txt: str, nct: str):
    """Return (start_idx, end_idx) of `realData[NCT]: { ... }` block or None."""
    key_pat = re.compile(r'(["\'])' + re.escape(nct) + r'\1\s*:\s*\{')
    m = key_pat.search(txt)
    if not m: return None
    start = m.end()
    depth = 1; i = start; in_str = None
    while i < len(txt) and depth > 0:
        ch = txt[i]
        if in_str:
            if ch == "\\": i += 2; continue
            if ch == in_str: in_str = None
        else:
            if ch in ('"',"'"): in_str = ch
            elif ch == "{": depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0: return (m.start(), i+1, start, i)
        i += 1
    return None


def null_field_in_block(txt: str, body_start: int, body_end: int, field: str) -> tuple[str, bool]:
    body = txt[body_start:body_end]
    new_body, n = re.subn(
        r'((["\']?)' + re.escape(field) + r'\2\s*:\s*)(?:["\'][^"\']*["\']|[0-9.eE+-]+|true|false)(?=\s*[,}])',
        r'\1null', body, flags=re.IGNORECASE
    )
    if n == 0: return txt, False
    return txt[:body_start] + new_body + txt[body_end:], True


log = []
for op in OPS:
    rv, nct, kind, reason = op["review"], op["nct"], op["op"], op["reason"]
    html_path = HERE / f"{rv}.html"
    if not html_path.exists():
        log.append({**op, "status": "MISSING_FILE"})
        continue
    txt = html_path.read_text(encoding="utf-8")
    if kind == "NULL_KEY":
        # Rename quoted key to NULLED:<nct> (both realData and nctAcronyms)
        nulled = f"NULLED:{nct}"
        if nulled in txt:
            log.append({**op, "status": "ALREADY_NULLED"})
            continue
        pat = re.compile(r'(["\'])(' + re.escape(nct) + r')(\1)(\s*:)')
        new_txt, n = pat.subn(lambda m: f'{m.group(1)}NULLED:{m.group(2)}{m.group(3)}{m.group(4)}', txt)
        if n == 0:
            log.append({**op, "status": "NCT_NOT_FOUND"})
            continue
        if not DRY: html_path.write_text(new_txt, encoding="utf-8")
        log.append({**op, "status": "NULLED_KEY", "occurrences": n})
        continue

    block = find_block(txt, nct)
    if not block:
        log.append({**op, "status": "BLOCK_NOT_FOUND"})
        continue
    _, _, body_start, body_end = block

    if kind == "NULL_PMID":
        new_txt, ok = null_field_in_block(txt, body_start, body_end, "pmid")
        if ok:
            if not DRY: html_path.write_text(new_txt, encoding="utf-8")
            log.append({**op, "status": "NULLED_PMID"})
        else:
            log.append({**op, "status": "PMID_NOT_FOUND"})
    elif kind == "NULL_ESTIMAND":
        new_txt, ok = null_field_in_block(txt, body_start, body_end, "estimandType")
        if ok:
            if not DRY: html_path.write_text(new_txt, encoding="utf-8")
            log.append({**op, "status": "NULLED_ESTIMAND"})
        else:
            log.append({**op, "status": "ESTIMAND_NOT_FOUND"})
    elif kind == "NULL_PMID_IF_IMPOSSIBLE":
        # Same as NULL_PMID but caller asserts the PMID is in the >4e7 impossible band
        new_txt, ok = null_field_in_block(txt, body_start, body_end, "pmid")
        if ok:
            if not DRY: html_path.write_text(new_txt, encoding="utf-8")
            log.append({**op, "status": "NULLED_IMPOSSIBLE_PMID"})
        else:
            log.append({**op, "status": "PMID_NOT_FOUND"})

out_p = HERE / "outputs" / "extraction_audit" / "multi_agent_fixes_applied.json"
out_p.write_text(json.dumps(log, indent=2, ensure_ascii=False), encoding="utf-8")

print(f"{'DRY-RUN: ' if DRY else ''}Applied {sum(1 for r in log if 'NULLED' in r['status'])}/{len(OPS)}")
for r in log:
    print(f"  {r['status']:25s}  {r['review']:50s}  {r['nct']}")
print(f"\nLog → {out_p}")
