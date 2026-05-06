"""Run UAT audit against a stratified sample of *_REVIEW.html files.

Drives headless Chromium via Playwright Python.
For each file:
  1. Navigate (file:// URL)
  2. Wait for hydration
  3. Run window.__UAT_AUDIT__() (loaded from scripts/uat_audit.js)
  4. Collect JSON result + console errors

Output:
  outputs/uat_results.json      — full per-file results
  outputs/uat_report.md         — human-readable summary

Usage: python scripts/uat_run.py [FILE1 FILE2 ...]
       (no args = stratified sample defined inline)
"""
from __future__ import annotations
import sys, io, json, time
from pathlib import Path
from datetime import datetime
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path(__file__).resolve().parent.parent
AUDIT_JS = (REPO / "scripts/uat_audit.js").read_text(encoding="utf-8")

NMA_FILES = [
    "ADC_HER2_NMA_REVIEW.html", "ANTIAMYLOID_AD_NMA_REVIEW.html",
    "ANTIVEGF_NAMD_NMA_REVIEW.html", "ATOPIC_DERM_NMA_REVIEW.html",
    "BTKI_CLL_NMA_REVIEW.html", "CARDIORENAL_DKD_NMA_REVIEW.html",
    "CD_BIOLOGICS_NMA_REVIEW.html", "CFTR_MODULATORS_NMA_REVIEW.html",
    "CGRP_MIGRAINE_NMA_REVIEW.html", "DOAC_AF_NMA_REVIEW.html",
    "DOAC_VTE_NMA_REVIEW.html", "FINERENONE_REVIEW.html",
    "GLP1_CVOT_NMA_REVIEW.html", "HF_QUADRUPLE_NMA_REVIEW.html",
    "IL_PSORIASIS_NMA_REVIEW.html", "INCRETINS_T2D_NMA_REVIEW.html",
    "JAKI_RA_NMA_REVIEW.html", "PCSK9_LIPID_NMA_REVIEW.html",
    "SEVERE_ASTHMA_NMA_REVIEW.html", "SGLT2I_HF_NMA_REVIEW.html",
    "UC_BIOLOGICS_NMA_REVIEW.html",
]
PAIRWISE_FILES = [
    "AGYW_HIV_PREP_REVIEW.html", "ALOPECIA_JAKI_REVIEW.html",
    "ANTI_CD20_MS_REVIEW.html", "ARPI_mHSPC_REVIEW.html",
    "AVACINCAPTAD_GA_REVIEW.html", "BELIMUMAB_SLE_REVIEW.html",
    "CGRP_MIGRAINE_REVIEW.html", "DUPILUMAB_AD_REVIEW.html",
    "HIV_LA_PREP_REVIEW.html", "INCLISIRAN_REVIEW.html",
    "JAK_UC_REVIEW.html", "PAH_THERAPY_REVIEW.html",
    "PHYSICAL_REHAB_OLDER_REVIEW.html", "RENAL_DENERV_REVIEW.html",
    "SOTAGLIFLOZIN_HF_REVIEW.html",
]


def main(argv):
    from playwright.sync_api import sync_playwright

    files = argv if argv else (NMA_FILES + PAIRWISE_FILES)
    print(f"Auditing {len(files)} files headless ...")
    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context()
        page = ctx.new_page()

        # Capture console errors per page
        for fname in files:
            entry = {
                "file": fname,
                "console_errors": [],
                "console_warnings": [],
                "audit": None,
                "error": None,
            }
            console_msgs = []
            failed_requests = []

            def on_console(msg, _store=console_msgs):
                _store.append((msg.type, msg.text))
            def on_request_failed(req, _store=failed_requests):
                _store.append(req.url)
            def on_response(resp, _store=failed_requests):
                if resp.status >= 400:
                    _store.append(f"{resp.status} {resp.url}")
            page.on("console", on_console)
            page.on("requestfailed", on_request_failed)
            page.on("response", on_response)

            try:
                url = f"http://127.0.0.1:8767/{fname}"
                page.goto(url, wait_until="domcontentloaded", timeout=15000)
                # Wait for either RapidMeta hydration or 4s timeout
                try:
                    page.wait_for_function(
                        "() => typeof window.RapidMeta === 'object' || performance.now() > 5000",
                        timeout=5000,
                    )
                except Exception:
                    pass
                time.sleep(0.6)  # let auto-render settle

                # Inject + run audit
                page.evaluate(AUDIT_JS)
                audit = page.evaluate("async () => { return await window.__UAT_AUDIT__({exerciseButtons: true}); }")
                entry["audit"] = audit
            except Exception as e:
                entry["error"] = f"{type(e).__name__}: {str(e)[:300]}"

            # Capture console — filter out expected environmental noise
            ENV_NOISE = (
                "PubMed primary query failed",
                "Failed to fetch",
                "ERR_INTERNET_DISCONNECTED",
                "EuropePMC",
                "CORS",
                "net::ERR",
                "epmc.fts",
            )
            for typ, txt in console_msgs:
                if any(n in txt for n in ENV_NOISE):
                    continue
                if typ == "error":
                    entry["console_errors"].append(txt[:300])
                elif typ == "warning":
                    entry["console_warnings"].append(txt[:300])
            entry["failed_requests"] = failed_requests
            page.remove_listener("console", on_console)
            page.remove_listener("requestfailed", on_request_failed)
            page.remove_listener("response", on_response)

            verdict = (entry["audit"] or {}).get("overall", "FAIL") if not entry["error"] else "ERROR"
            n_iss = len((entry["audit"] or {}).get("issues", [])) if not entry["error"] else 999
            n_err = len(entry["console_errors"])
            print(f"  {verdict:5s} {fname[:60]:60s} issues={n_iss} errors={n_err}")
            results.append(entry)

        browser.close()

    # Persist raw JSON
    raw = REPO / "outputs/uat_results.json"
    raw.write_text(json.dumps({
        "ts": datetime.now().isoformat(timespec="seconds"),
        "n": len(results),
        "results": results,
    }, indent=2))
    print(f"\nWrote {raw}")

    # Build markdown summary
    md = ["# UAT Audit Report", "",
          f"_Generated {datetime.now().isoformat(timespec='seconds')}_", "",
          f"**Scope:** {len(files)} files audited via headless Chromium", "",
          "## Verdicts"]

    n_pass = sum(1 for r in results if (r.get("audit") or {}).get("overall") == "PASS")
    n_warn = sum(1 for r in results if (r.get("audit") or {}).get("overall") == "WARN")
    n_fail = sum(1 for r in results if (r.get("audit") or {}).get("overall") == "FAIL")
    n_err = sum(1 for r in results if r.get("error"))
    md.append("")
    md.append(f"| PASS | WARN | FAIL | ERROR |")
    md.append(f"|------|------|------|-------|")
    md.append(f"| {n_pass} | {n_warn} | {n_fail} | {n_err} |")
    md.append("")

    md.append("## Per-file table")
    md.append("")
    md.append("| File | Verdict | RapidMeta | Trials | Console errors | Issues |")
    md.append("|------|---------|-----------|--------|----------------|--------|")
    for r in results:
        a = r.get("audit") or {}
        v = a.get("overall", "ERR")
        rm = "✓" if a.get("state", {}).get("has_RapidMeta") else "✗"
        nt = a.get("state", {}).get("realData_count", 0)
        ce = len(r.get("console_errors", []))
        iss = ", ".join(a.get("issues", []) or [])[:80] if a else (r.get("error") or "")[:80]
        md.append(f"| {r['file']} | {v} | {rm} | {nt} | {ce} | {iss} |")

    # Failed/warn details
    md.append("")
    md.append("## Issues detail (FAIL + WARN)")
    md.append("")
    for r in results:
        a = r.get("audit") or {}
        if a.get("overall") in ("PASS",) and not r.get("console_errors"):
            continue
        md.append(f"### {r['file']}")
        if r.get("error"):
            md.append(f"  - **Error:** `{r['error']}`")
        if r.get("console_errors"):
            md.append(f"  - **Console errors ({len(r['console_errors'])}):**")
            for e in r["console_errors"][:5]:
                md.append(f"    - `{e}`")
        if a.get("issues"):
            md.append(f"  - **Issues:** {', '.join(a['issues'])}")
        # Buttons that failed
        bad_btns = [(k, v) for k, v in a.get("buttons", {}).items()
                    if isinstance(v, dict) and v.get("found") and v.get("clicked") is False]
        if bad_btns:
            md.append(f"  - **Failed buttons:**")
            for k, v in bad_btns:
                md.append(f"    - `{k}`: {v.get('error', 'no error msg')}")
        # Text issues
        tc = a.get("text_checks", {})
        if tc.get("has_unfilled_placeholder"):
            md.append(f"  - **Placeholder residue in DOM**")
        if tc.get("has_NaN"):
            md.append(f"  - **NaN in DOM**")
        md.append("")

    out = REPO / "outputs/uat_report.md"
    out.write_text("\n".join(md), encoding="utf-8")
    print(f"Wrote {out}")
    print(f"\nResult: PASS={n_pass} WARN={n_warn} FAIL={n_fail} ERROR={n_err}")


if __name__ == "__main__":
    main(sys.argv[1:])
