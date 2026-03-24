"""
LivingMeta Cross-Validation: Independent double-data-extraction
Fetches trial data from CT.gov API v2 and compares against our stored values.
This serves as the "second extractor" for publication-quality verification.

Usage: python cross_validate.py
"""
import sys, io, os, time, json, urllib.request, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

CTG_API = "https://clinicaltrials.gov/api/v2/studies"

# Curated trial data from LivingMeta (manually extracted from the HTML)
CURATED_TRIALS = {
    # Colchicine
    "NCT02551094": {"id": "COLCOT", "config": "colchicine_cvd", "mace_tE": 131, "mace_tN": 2366, "mace_cE": 170, "mace_cN": 2379, "mace_hr": 0.77},
    "NCT03048825": {"id": "CLEAR-SYNERGY", "config": "colchicine_cvd", "mace_tE": 322, "mace_tN": 3528, "mace_cE": 327, "mace_cN": 3534, "mace_hr": 0.99},
    # Finerenone
    "NCT02540993": {"id": "FIDELIO-DKD", "config": "finerenone", "mace_hr": 0.86, "mace_tE": 367, "mace_tN": 2833, "mace_cE": 420, "mace_cN": 2841},
    "NCT02545049": {"id": "FIGARO-DKD", "config": "finerenone", "mace_hr": 0.87, "mace_tE": 458, "mace_tN": 3686, "mace_cE": 519, "mace_cN": 3666},
    # SGLT2 HF
    "NCT03036124": {"id": "DAPA-HF", "config": "sglt2_hf", "mace_hr": 0.74, "mace_tE": 386, "mace_tN": 2373, "mace_cE": 502, "mace_cN": 2371},
    "NCT03057977": {"id": "EMPEROR-Reduced", "config": "sglt2_hf", "mace_hr": 0.75, "mace_tE": 361, "mace_tN": 1863, "mace_cE": 462, "mace_cN": 1867},
    # GLP-1
    "NCT01179048": {"id": "LEADER", "config": "glp1_cvot", "mace_hr": 0.87, "mace_tE": 608, "mace_tN": 4668, "mace_cE": 694, "mace_cN": 4672},
    "NCT03574597": {"id": "SELECT", "config": "glp1_cvot", "mace_hr": 0.80, "mace_tE": 569, "mace_tN": 8803, "mace_cE": 701, "mace_cN": 8801},
    # PCSK9
    "NCT01764633": {"id": "FOURIER", "config": "pcsk9", "mace_hr": 0.85, "mace_tE": 1344, "mace_tN": 13784, "mace_cE": 1563, "mace_cN": 13780},
    "NCT01663402": {"id": "ODYSSEY", "config": "pcsk9", "mace_hr": 0.85, "mace_tE": 903, "mace_tN": 9462, "mace_cE": 1052, "mace_cN": 9462},
}

def fetch_study(nct_id):
    """Fetch a single study from CT.gov API v2."""
    url = f"{CTG_API}/{nct_id}?format=json"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "LivingMeta-CrossValidation/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        print(f"  WARN: Failed to fetch {nct_id}: {e}")
        return None

def extract_primary_hr(data):
    """Extract primary outcome HR from CT.gov results section."""
    rs = data.get("resultsSection")
    if not rs:
        return None, None, None, "No results section"

    om = rs.get("outcomeMeasuresModule", {}).get("outcomeMeasures", [])
    for measure in om:
        for analysis in measure.get("analyses", []):
            method = (analysis.get("statisticalMethod", "") or "").lower()
            param_type = (analysis.get("paramType", "") or "").lower()
            combined = method + " " + param_type

            if "hazard" in combined or "cox" in combined:
                try:
                    val = float(analysis.get("paramValue", 0))
                    ci_lo = float(analysis.get("ciLowerLimit", 0)) if analysis.get("ciLowerLimit") else None
                    ci_hi = float(analysis.get("ciUpperLimit", 0)) if analysis.get("ciUpperLimit") else None
                    if val > 0 and val < 50:
                        return val, ci_lo, ci_hi, measure.get("title", "")[:60]
                except (ValueError, TypeError):
                    continue
    return None, None, None, "No HR found in analyses"

def extract_enrollment(data):
    """Extract enrollment from protocol section."""
    ps = data.get("protocolSection", {})
    design = ps.get("designModule", {})
    return design.get("enrollmentInfo", {}).get("count", 0)

def main():
    print("=" * 80)
    print("LivingMeta Cross-Validation Report")
    print("Independent double-data-extraction via CT.gov API v2")
    print("=" * 80)
    print()

    results = []

    for nct_id, curated in CURATED_TRIALS.items():
        print(f"Fetching {nct_id} ({curated['id']})...")
        data = fetch_study(nct_id)
        time.sleep(0.3)

        if not data:
            results.append({"nct": nct_id, "id": curated["id"], "status": "FETCH_FAILED"})
            continue

        ctg_hr, ctg_ci_lo, ctg_ci_hi, ctg_outcome = extract_primary_hr(data)
        ctg_n = extract_enrollment(data)
        our_hr = curated.get("mace_hr")
        our_n = curated.get("mace_tN", 0) + curated.get("mace_cN", 0)

        # Compare
        hr_match = "N/A"
        if ctg_hr and our_hr:
            diff = abs(ctg_hr - our_hr)
            hr_match = "EXACT" if diff < 0.005 else "CLOSE" if diff < 0.05 else "DIFFERS"
        elif ctg_hr is None:
            hr_match = "NO_CTG_HR"

        n_match = "MATCH" if abs(ctg_n - our_n) < 100 else "CLOSE" if abs(ctg_n - our_n) < 500 else "DIFFERS"

        result = {
            "nct": nct_id, "id": curated["id"], "config": curated["config"],
            "our_hr": our_hr, "ctg_hr": ctg_hr, "hr_match": hr_match,
            "our_n": our_n, "ctg_n": ctg_n, "n_match": n_match,
            "ctg_outcome": ctg_outcome
        }
        results.append(result)

        status = "OK" if hr_match in ("EXACT", "CLOSE") else "CHECK"
        print(f"  {curated['id']:20} HR: ours={our_hr}, CTG={ctg_hr}, {hr_match} | N: ours={our_n}, CTG={ctg_n}, {n_match}")

    print()
    print("=" * 80)
    print("CONCORDANCE SUMMARY")
    print("=" * 80)

    exact = sum(1 for r in results if r.get("hr_match") == "EXACT")
    close = sum(1 for r in results if r.get("hr_match") == "CLOSE")
    differs = sum(1 for r in results if r.get("hr_match") == "DIFFERS")
    no_hr = sum(1 for r in results if r.get("hr_match") == "NO_CTG_HR")
    failed = sum(1 for r in results if r.get("status") == "FETCH_FAILED")

    print(f"  EXACT match (diff < 0.005): {exact}")
    print(f"  CLOSE match (diff < 0.05):  {close}")
    print(f"  DIFFERS (diff >= 0.05):     {differs}")
    print(f"  No CT.gov HR available:     {no_hr}")
    print(f"  Fetch failed:               {failed}")
    print(f"  Total: {len(results)}")
    print(f"  Concordance rate: {(exact + close)}/{exact + close + differs} = {((exact + close) / max(1, exact + close + differs) * 100):.0f}%")

    # Save report
    with open("cross_validation_report.json", "w") as f:
        json.dump({"generated": time.strftime("%Y-%m-%d %H:%M"), "results": results}, f, indent=2)
    print(f"\nReport saved to cross_validation_report.json")

if __name__ == "__main__":
    main()
