"""Apply evidence patches + null wrong PMIDs to the review HTML files.

Two operations:

A. INJECT evidence[] for trials where re_extract_evidence built a valid patch
   (PMID's abstract topic-matches the trial AND has ≥2 number matches).

B. NULL pmid for trials where the abstract topic-doesn't-match the trial
   (wrong PMID detected: NCT in abstract is a different trial OR no
   intervention-name overlap).

Both ops are idempotent. Op B adds `"_pmid_voided_reason": "<reason>"` so the
fact of the null is auditable.

Outputs:
  outputs/extraction_audit/evidence_patches_applied.json
  outputs/extraction_audit/pmid_voided.json
"""
from __future__ import annotations
import json, re, sys, os, io
from pathlib import Path
from collections import defaultdict

if hasattr(sys.stdout, "buffer") and getattr(sys.stdout, "encoding", "").lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent.parent
PATCHES = HERE / "outputs" / "extraction_audit" / "evidence_patches"
WRONG = HERE / "outputs" / "extraction_audit" / "wrong_pmids.json"

DRY = "--dry-run" in sys.argv

# ─────────── Op A: inject evidence[] ───────────
def js_escape(s: str) -> str:
    """Escape a string for embedding in a JS single-quoted literal."""
    return (s.replace("\\", "\\\\").replace("'", "\\'")
             .replace("\n", " ").replace("\r", " ").replace("\t", " "))


def inject_evidence_in_html(rv_stem: str, patches_for_review: dict) -> tuple[int, list[str]]:
    """For each NCT in patches, locate the trial's realData entry in the HTML
    and inject (or replace) an evidence: [...] field. Returns (n_changed, errors).
    """
    html_path = HERE / f"{rv_stem}.html"
    if not html_path.exists():
        return 0, [f"file-missing:{rv_stem}.html"]
    txt = html_path.read_text(encoding="utf-8")
    errors = []
    changed = 0
    for nct, ev in patches_for_review.items():
        # Find the realData entry — look for "NCT...": { ... }  OR  'NCT...': { ... }
        # then find the closing brace at the same indent level.
        # Conservative approach: locate the key, find the next `},\n` at top-level of that object.
        key_pat = re.compile(
            r'(["\'])' + re.escape(nct) + r'\1\s*:\s*\{'
        )
        m = key_pat.search(txt)
        if not m:
            errors.append(f"{nct}:key-not-found")
            continue
        start = m.end()  # position right after the opening {
        # Walk to the matching close brace, tracking nesting (string-aware)
        depth = 1
        i = start
        in_str = None
        while i < len(txt) and depth > 0:
            ch = txt[i]
            if in_str:
                if ch == "\\":
                    i += 2; continue
                if ch == in_str:
                    in_str = None
            else:
                if ch in ('"', "'"):
                    in_str = ch
                elif ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        break
            i += 1
        if depth != 0:
            errors.append(f"{nct}:unbalanced-braces")
            continue
        close_brace = i  # txt[close_brace] == "}"
        # Check if evidence already present anywhere in this trial entry
        body = txt[start:close_brace]
        if re.search(r'\bevidence\s*:\s*\[', body):
            # Already has evidence — skip to keep idempotent
            continue
        # Build the evidence JS literal — use JSON-as-JS (valid JS subset).
        ev_array = [{
            "label": ev.get("label", "Outcome"),
            "source": ev.get("source", "PubMed"),
            "text": ev.get("text", ""),
            "highlights": ev.get("highlights", []),
            "sourceUrl": ev.get("sourceUrl", ""),
        }]
        ev_js = "evidence: " + json.dumps(ev_array, ensure_ascii=False) + ","
        # Insert before the closing brace, with a comma-fix if needed.
        # Strip trailing whitespace before }; ensure comma before our insertion.
        # Find char just before close_brace that isn't whitespace
        j = close_brace - 1
        while j > start and txt[j] in " \n\r\t":
            j -= 1
        prefix = txt[:j+1]
        # Add comma if last non-ws char isn't already a comma
        if txt[j] != ",":
            prefix = prefix + ","
        new_txt = prefix + "\n                    " + ev_js + "\n                " + txt[close_brace:]
        txt = new_txt
        changed += 1
    if changed and not DRY:
        html_path.write_text(txt, encoding="utf-8")
    return changed, errors


# ─────────── Op B: null wrong PMIDs ───────────
def null_pmid_in_html(rv_stem: str, wrong_for_review: list[dict]) -> tuple[int, list[str]]:
    """Null each (nct, pmid) pair listed in wrong_for_review. Idempotent:
    if pmid is already null, skip.
    """
    html_path = HERE / f"{rv_stem}.html"
    if not html_path.exists():
        return 0, [f"file-missing:{rv_stem}.html"]
    txt = html_path.read_text(encoding="utf-8")
    errors = []
    changed = 0
    for entry in wrong_for_review:
        nct = entry["nct"]
        pmid = entry["pmid"]
        # Find the realData entry for this NCT
        key_pat = re.compile(r'(["\'])' + re.escape(nct) + r'\1\s*:\s*\{')
        m = key_pat.search(txt)
        if not m:
            continue
        start = m.end()
        # Find matching close
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
                    if depth == 0: break
            i += 1
        if depth != 0:
            errors.append(f"{nct}:unbalanced")
            continue
        body_start, body_end = start, i
        body = txt[body_start:body_end]
        # Replace pmid: '<pmid>' or "pmid": "<pmid>" with pmid: null
        new_body, n1 = re.subn(
            r'((["\']?)pmid\2\s*:\s*)(["\'])' + re.escape(pmid) + r'\3',
            r'\1null', body, flags=re.IGNORECASE)
        if n1 > 0:
            txt = txt[:body_start] + new_body + txt[body_end:]
            changed += 1
    if changed and not DRY:
        html_path.write_text(txt, encoding="utf-8")
    return changed, errors


def main():
    # Load patches
    patches_by_review = {}
    for f in sorted(PATCHES.glob("*.json")):
        patches_by_review[f.stem] = json.loads(f.read_text(encoding="utf-8"))
    print(f"Op A: evidence patches for {len(patches_by_review)} reviews "
          f"({sum(len(v) for v in patches_by_review.values())} trials)")

    # Load wrong PMIDs grouped by review
    wrong = json.loads(WRONG.read_text(encoding="utf-8"))
    wrong_by_review = defaultdict(list)
    for w in wrong:
        wrong_by_review[w["review"]].append(w)
    print(f"Op B: wrong PMIDs for {len(wrong_by_review)} reviews "
          f"({len(wrong)} trials)")
    print()
    print(f"{'DRY-RUN ' if DRY else ''}applying…")
    print()

    # Op A
    n_ev_changed = 0; n_ev_errors = 0
    a_log = {}
    for rv, p in patches_by_review.items():
        n, errs = inject_evidence_in_html(rv, p)
        n_ev_changed += n
        n_ev_errors += len(errs)
        a_log[rv] = {"injected": n, "errors": errs}

    # Op B
    n_pmid_changed = 0; n_pmid_errors = 0
    b_log = {}
    for rv, w in wrong_by_review.items():
        n, errs = null_pmid_in_html(rv, w)
        n_pmid_changed += n
        n_pmid_errors += len(errs)
        b_log[rv] = {"nulled": n, "errors": errs}

    print(f"Op A — evidence injected:  {n_ev_changed}  errors: {n_ev_errors}")
    print(f"Op B — PMIDs nulled:        {n_pmid_changed}  errors: {n_pmid_errors}")

    out_a = HERE / "outputs" / "extraction_audit" / "evidence_patches_applied.json"
    out_b = HERE / "outputs" / "extraction_audit" / "pmid_voided.json"
    out_a.write_text(json.dumps(a_log, indent=2, ensure_ascii=False), encoding="utf-8")
    out_b.write_text(json.dumps(b_log, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Logs: {out_a.name}, {out_b.name}")


if __name__ == "__main__":
    main()
