#!/usr/bin/env python
"""Clone HFREF_NMA_REVIEW.html template into a new NMA topic app.

Config structure (JSON file path):
{
  "slug": "btki_cll_nma",
  "filename": "BTKI_CLL_NMA_REVIEW",
  "title": "RapidMeta Haematology | BTKi Class NMA in CLL v1.1",
  "banner": "RapidMeta BTKi CLL NMA v1.1",
  "protocol_title": "Network Meta-Analysis of BTKi in CLL: ...",
  "outcome_label": "PFS",
  "outcome_slug": "pfs",
  "outcome_note": "Progression-free survival; log-HR scale; random-effects",
  "auto_include": ["NCT02475681", "NCT02477696", "NCT03734016", "NCT01722487"],
  "acronyms": {"NCT02475681": "ELEVATE-TN", ...},
  "treatments": ["Acalabrutinib", "Ibrutinib", "Zanubrutinib", "Chemoimmunotherapy"],
  "comparisons": [
    {"t1": "Acalabrutinib", "t2": "Ibrutinib", "trials": ["NCT02477696"]},
    {"t1": "Acalabrutinib", "t2": "Chemoimmunotherapy", "trials": ["NCT02475681"]},
    {"t1": "Ibrutinib", "t2": "Chemoimmunotherapy", "trials": ["NCT01722487"]},
    {"t1": "Zanubrutinib", "t2": "Ibrutinib", "trials": ["NCT03734016"]}
  ],
  "nma_note": "Closed-loop NMA with consistency assumption. ...",
  "ctgov_intr": "(acalabrutinib OR ibrutinib OR zanubrutinib) AND chronic lymphocytic leukemia",
  "realData_block": "...JS literal of realData object body..."
}
"""
import json
import re
import sys
import io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import os
ROOT = Path(os.environ.get("RAPIDMETA_ROOT") or Path(__file__).resolve().parents[1])
# Sibling project; lives under the same parent dir as Finrenone in dev layout.
TEMPLATE = Path(
    os.environ.get("RAPIDMETA_NMA_TEMPLATE")
    or (ROOT.parent / "HFrEF_NMA_LivingMeta" / "HFREF_NMA_REVIEW.html")
)


def clone(config):
    t = TEMPLATE.read_text(encoding="utf-8")
    slug = config["slug"]
    filename = config["filename"]
    out = ROOT / f"{filename}.html"

    # A. <title>
    t = re.sub(r"<title>[^<]*</title>",
               f'<title>{config["title"]}</title>', t, count=1)

    # Replace template-title string elsewhere (fallbacks)
    t = t.replace(
        "RapidMeta Cardiology | HFrEF Quadruple Therapy NMA v15.0",
        config["title"],
    )

    # B. Banner
    for old in [
        "RapidMeta Cardiology NMA v15.0",
        "RapidMeta NMA v15.0",
        "HFrEF Quadruple NMA v15.0",
        "HFrEF Quadruple Therapy NMA v15.0",
    ]:
        t = t.replace(old, config["banner"])

    # C. AUTO_INCLUDE_TRIAL_IDS
    ai = ", ".join(f"'{x}'" for x in config["auto_include"])
    t = re.sub(
        r"const AUTO_INCLUDE_TRIAL_IDS = new Set\(\[[^\]]*\]\);",
        f"const AUTO_INCLUDE_TRIAL_IDS = new Set([{ai}]);",
        t, count=1,
    )

    # D. nctAcronyms mapping
    acro = ", ".join(f"'{k}': '{v}'" for k, v in config["acronyms"].items())
    t = re.sub(
        r"nctAcronyms:\s*\{[^\}]*\},",
        f"nctAcronyms: {{ {acro} }},",
        t, count=1,
    )

    # E. NMA_CONFIG block
    nma_json = {
        "treatments": config["treatments"],
        "comparisons": config["comparisons"],
        "outcome": config.get("outcome_slug", "primary"),
        "outcome_label": config.get("outcome_label", "Primary outcome"),
        "note": config.get("nma_note", ""),
    }
    nma_literal = json.dumps(nma_json, indent=8, ensure_ascii=False)
    t = re.sub(
        r"const NMA_CONFIG = \{[\s\S]*?\}; // Populated by generator for NMA-enabled apps",
        "const NMA_CONFIG = " + nma_literal + "; // Populated by generator for NMA-enabled apps",
        t, count=1,
    )

    # F. realData block (HFrEF NMA template: realData closes at col-12)
    pat = r"            realData:\s*\{\n[\s\S]*?\n            \},\n\n(            async init\(\))"
    new_block = config["realData_block"]
    if new_block.strip().startswith("'NCT") or new_block.strip().startswith("            '"):
        wrapped = "            realData: {\n" + new_block.rstrip().rstrip(",") + "\n            },\n\n"
    else:
        wrapped = new_block.rstrip() + "\n\n"
        if not wrapped.endswith(",\n\n"):
            wrapped = wrapped.rstrip("\n") + ",\n\n"

    def _repl(m):
        return wrapped + m.group(1)

    new_t, n = re.subn(pat, _repl, t, count=1)
    if n == 0:
        raise RuntimeError("realData block anchor not found")
    t = new_t

    # G. localStorage keys (HFREF template uses 'rapid_meta_hfref_nma_v15_0' etc.)
    t = re.sub(
        r"rapid_meta_hfref_nma_v\d+_\d+",
        f"rapid_meta_{slug}_v1_0",
        t,
    )
    t = t.replace("rapid_meta_hfref_nma_theme", f"rapid_meta_{slug}_theme")

    # H. Drug-class propagation (same as pairwise cloner)
    intr_val = config.get("ctgov_intr")
    if intr_val:
        parts = re.split(r"\s+AND\s+", intr_val, maxsplit=1)
        drug_terms = parts[0].strip()
        drug_list = [x.strip() for x in re.split(r"\s+OR\s+", drug_terms) if x.strip()]
        drug_regex = "|".join(x.lower() for x in drug_list)
        drug_space = " ".join(drug_list)

        # OpenAlex
        t = re.sub(
            r"const oaUrl = 'https://api\.openalex\.org/works\?search=[^&']+(&per_page=50[^']*)';",
            "const oaUrl = 'https://api.openalex.org/works?search=" + drug_space + r"\1';",
            t, count=1,
        )
        # Europe PMC main
        t = re.sub(
            r"const epmcQuery = encodeURIComponent\('[^']*? AND \(TITLE:randomized",
            "const epmcQuery = encodeURIComponent('" + drug_terms + " AND (TITLE:randomized",
            t, count=1,
        )
        # Europe PMC fallback
        t = re.sub(
            r"const fbQ = encodeURIComponent\('[^']*? AND SRC:MED'\);",
            "const fbQ = encodeURIComponent('" + drug_terms + " AND SRC:MED');",
            t, count=1,
        )
        # CT.gov fetch
        t = re.sub(
            r"const r = await fetch\('https://clinicaltrials\.gov/api/v2/studies\?query\.intr=[^']+'\);",
            "const r = await fetch('https://clinicaltrials.gov/api/v2/studies?query.intr=" + intr_val + "&pageSize=50&filter.overallStatus=COMPLETED');",
            t, count=1,
        )

    # I. Protocol title cell (optional)
    if "protocol_title" in config:
        t = re.sub(
            r"(Review Title</td>\s*<td[^>]*>)[^<]*(</td>)",
            f"\\g<1>{config['protocol_title']}\\g<2>",
            t, count=1,
        )

    # J. Hardening for peer-review (CSP + COOP SW + bridge exports + PR panel)
    #    Idempotent — only applied if not already present.
    # (a) CSP: ensure 'unsafe-eval' and 'wasm-unsafe-eval' for WebR WASM
    t = t.replace(
        "script-src 'self' 'unsafe-inline' https://webr.r-wasm.org;",
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' 'wasm-unsafe-eval' https://webr.r-wasm.org;",
    )

    # (b) Inject coi-serviceworker.js at top of <head>
    coi_tag = '<script src="coi-serviceworker.js"></script>'
    if coi_tag not in t:
        # Insert right after <meta charset="UTF-8"> or first <meta>
        m = re.search(r"(<meta\s+[^>]*charset[^>]*>)", t)
        if m:
            t = t[:m.end(1)] + "\n    " + coi_tag + t[m.end(1):]
        else:
            t = t.replace("<head>", "<head>\n    " + coi_tag, 1)

    # (c) Bridge exports at end of main script (window.RapidMeta/NMAEngine/NMA_CONFIG)
    bridge = (
        "        // NMA Peer-Review bridge (auto-injected by clone_nma_review.py)\n"
        "        try { window.RapidMeta = RapidMeta; } catch(e){}\n"
        "        try { window.NMAEngine = NMAEngine; } catch(e){}\n"
        "        try { window.NMA_CONFIG = NMA_CONFIG; } catch(e){}\n"
    )
    if "window.RapidMeta = RapidMeta" not in t:
        # Insert before the final </script> of the main app block (the one just after `RapidMeta.init()`)
        marker = "window.onload = () => RapidMeta.init();"
        idx = t.find(marker)
        if idx >= 0:
            idx2 = t.find("</script>", idx)
            if idx2 >= 0:
                t = t[:idx2] + bridge + t[idx2:]

    # (d) PR tools script tag before </body>
    pr_tag = '<script src="nma-peer-review-tools.js" defer></script>'
    if pr_tag not in t and "</body>" in t:
        idx = t.rfind("</body>")
        t = t[:idx] + pr_tag + "\n" + t[idx:]

    out.write_text(t, encoding="utf-8")
    print(f"  wrote {out.name} ({len(t)} bytes)")
    return out


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: python clone_nma_review.py <config.json>", file=sys.stderr)
        sys.exit(1)
    cfg = json.load(open(sys.argv[1], "r", encoding="utf-8"))
    clone(cfg)
