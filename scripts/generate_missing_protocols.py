"""C1: Auto-generate the missing per-topic protocol .md files.

For every *_AUTO_FULL_REVIEW.html the protocol-badge href points at
  protocols/<stem>_auto_protocol_v1.1_2026-04-20.md
but most of those files were never written; commit 4d8476d5d rewrote the
hrefs to fall back to protocols/INDEX.md so users didn't 404. This script
generates the real per-topic files from each page's structured PICO + trial
data so the original hrefs work without the fallback.

The generated protocols are clearly labelled "auto-generated post-hoc from
AACT-verified extraction" — they are NOT a substitute for a pre-registered
PROSPERO/OSF protocol. The frontmatter sets `registration: post-hoc` and the
body has a prominent banner stating this.

After generation we restore the original specific-protocol hrefs in the
matching FULL_REVIEW headers (they currently all point at INDEX.md).
"""
from __future__ import annotations
import json
import re
import sys
import io
from datetime import date
from pathlib import Path

if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent.parent
PROTOCOLS = HERE / "protocols"
PROTOCOLS.mkdir(exist_ok=True)

NCT_ACRONYM_RE = re.compile(r"nctAcronyms:\s*\{([^}]*)\}")
NCT_PAIR_RE = re.compile(r"'(NCT\d{7,8})':\s*'([^']*)'")
TRIAL_BLOCK_RE = re.compile(
    r"'(NCT\d{7,8})':\s*\{(?P<body>(?:[^{}]|\{[^{}]*\}){0,4000})\}",
    re.DOTALL,
)
PICO_FIELD_RE = re.compile(
    r"\b(pop|int|comp|out|subgroup):\s*'((?:[^'\\]|\\.)*)'",
)
TITLE_RE = re.compile(r"<title>(.*?)</title>", re.DOTALL | re.IGNORECASE)
H1_RE = re.compile(r"<h1[^>]*>(.*?)</h1>", re.DOTALL | re.IGNORECASE)
HERO_RE = re.compile(r'hero_h2[^"\']*[\'"]([^\'"]+)[\'"]', re.IGNORECASE)
HEAD_PROTOCOL_HREF_RE = re.compile(
    r'href="protocols/INDEX\.md"(\s+target="_blank"\s+rel="noopener"\s+class="[^"]*"\s+title="[^"]*"\s+data-protocol-version="[^"]*"\s+data-protocol-date="[^"]*">📑 Protocol)'
)


def strip_html(s: str) -> str:
    s = re.sub(r"<[^>]+>", " ", s)
    s = re.sub(r"&[a-z]+;", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def extract_pico(txt: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for m in PICO_FIELD_RE.finditer(txt):
        k, v = m.group(1), m.group(2)
        if k not in out:
            out[k] = v.replace("\\'", "'")
    return out


def extract_acronyms(txt: str) -> dict[str, str]:
    m = NCT_ACRONYM_RE.search(txt)
    if not m:
        return {}
    return {p.group(1): p.group(2) for p in NCT_PAIR_RE.finditer(m.group(1))}


def extract_trials(txt: str) -> list[dict]:
    out = []
    for m in TRIAL_BLOCK_RE.finditer(txt):
        nct = m.group(1)
        body = m.group("body")
        name_m = re.search(r"name:\s*'([^']*)'", body)
        pmid_m = re.search(r"pmid:\s*'(\d*)'", body)
        year_m = re.search(r"year:\s*(\d+)", body)
        outcome_m = re.search(r"title:\s*'([^']{8,300})'", body)
        out.append({
            "nct": nct,
            "name": name_m.group(1) if name_m else nct,
            "pmid": pmid_m.group(1) if pmid_m else "",
            "year": year_m.group(1) if year_m else "",
            "outcome": outcome_m.group(1) if outcome_m else "",
        })
    return out


def render_protocol(stem: str, h1: str, pico: dict, trials: list[dict]) -> str:
    today = date.today().isoformat()
    canonical = f"https://mahmood726-cyber.github.io/rapidmeta-finerenone/protocols/{stem.lower()}_auto_protocol_v1.1_2026-04-20.md"
    app_url = f"https://mahmood726-cyber.github.io/rapidmeta-finerenone/{stem}_AUTO_FULL_REVIEW.html"

    lines = []
    lines.append("---")
    lines.append(f'title: "{h1}"')
    lines.append(f"slug: {stem.lower()}")
    lines.append("version: 1.1")
    lines.append("date: 2026-04-20")
    lines.append("registration: post-hoc")
    lines.append("registration_note: |")
    lines.append("  Auto-generated post-hoc from AACT-verified extraction; NOT a")
    lines.append("  pre-registered PROSPERO/OSF protocol. Use the per-topic curated")
    lines.append("  *_REVIEW.html when one exists for analyses requiring formal")
    lines.append("  pre-registration.")
    lines.append(f"canonical_url: {canonical}")
    lines.append(f"app_url: {app_url}")
    lines.append("license: MIT")
    lines.append("---")
    lines.append("")
    lines.append(f"# {h1}")
    lines.append("## Auto-generated Protocol (post-hoc, AACT-verified extraction)")
    lines.append("")
    lines.append("> **Notice — Auto-generated.** This protocol was rendered from the live")
    lines.append("> interactive review at the App URL above using the structured PICO and")
    lines.append("> trial data extracted from AACT 2026-04-12 + AACT-verified primary")
    lines.append("> publications. It is **not** a pre-registered PROSPERO/OSF protocol.")
    lines.append("> Authors targeting journals that require a PROSPERO number should")
    lines.append("> register the protocol before the first formal update cycle.")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 1. PICO")
    lines.append("")
    if pico.get("pop"):
        lines.append(f"**Population.** {pico['pop']}")
        lines.append("")
    if pico.get("int"):
        lines.append(f"**Intervention.** {pico['int']}")
        lines.append("")
    if pico.get("comp"):
        lines.append(f"**Comparator.** {pico['comp']}")
        lines.append("")
    if pico.get("out"):
        lines.append(f"**Outcome.** {pico['out']}")
        lines.append("")
    if pico.get("subgroup"):
        lines.append(f"**Subgroups.** {pico['subgroup']}")
        lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 2. Eligibility (6-gate audit, applied at extraction time)")
    lines.append("")
    lines.append("1. **GATE-A.** NCT exists in AACT 2026-04-12 snapshot.")
    lines.append("2. **GATE-B.** Drug pattern present in AACT `interventions` for the NCT.")
    lines.append("3. **GATE-C.** Condition pattern present in AACT `conditions`.")
    lines.append("4. **GATE-D.** Primary PMID's PubMed title or abstract mentions the drug")
    lines.append("   or condition.")
    lines.append("5. **GATE-E.** AACT `baseline_counts` reports ≥2 per-arm participant rows.")
    lines.append("6. **GATE-F.** AACT `design_outcomes` declares a primary outcome with")
    lines.append("   measure text.")
    lines.append("")
    lines.append("Trials below all passed all 6 gates.")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(f"## 3. Included trials (k = {len(trials)})")
    lines.append("")
    if trials:
        lines.append("| NCT | Name | Year | Primary outcome (AACT) | PMID |")
        lines.append("|-----|------|------|------------------------|------|")
        for t in trials:
            outcome = t["outcome"][:80].replace("|", "\\|") if t["outcome"] else "—"
            pmid_cell = f"[{t['pmid']}](https://pubmed.ncbi.nlm.nih.gov/{t['pmid']}/)" if t["pmid"] else "—"
            lines.append(f"| [{t['nct']}](https://clinicaltrials.gov/study/{t['nct']}) "
                         f"| {t['name']} | {t['year'] or '—'} | {outcome} | {pmid_cell} |")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 4. Statistical methods")
    lines.append("")
    lines.append("Pre-specified pooling = inverse-variance random-effects DerSimonian–Laird")
    lines.append("τ², with Hartung–Knapp–Sidik–Jonkman (HKSJ) variance correction and")
    lines.append("t<sub>k-1</sub> critical value (Cochrane Handbook v6.5). Effect scale is")
    lines.append("the trial-published metric (HR / OR / RR / MD) when available from AACT")
    lines.append("`outcome_analyses`, else an inverse-variance OR computed from AACT event")
    lines.append("counts via the Woolf estimator.")
    lines.append("")
    lines.append("Sensitivity analyses: leave-one-out, Baujat, cumulative MA, Bayesian")
    lines.append("posterior with weakly-informative prior μ ~ N(0, 1.0²) on the log scale,")
    lines.append("trim-and-fill, Egger/Peters publication-bias tests (k ≥ 3), prediction")
    lines.append("interval at α = 0.10 (Cochrane v6.5 t<sub>k-1</sub>), Trial Sequential")
    lines.append("Analysis with O'Brien–Fleming alpha-spending. See the live app for the")
    lines.append("full 28-panel statistics tab.")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 5. Risk of bias")
    lines.append("")
    lines.append("RoB-2 per trial is derived from AACT `designs` allocation + masking +")
    lines.append("outcomes_assessor_masked fields (D1 randomization, D2 deviations, D4")
    lines.append("measurement). D3 (missing data) and D5 (selective reporting) default to")
    lines.append("`some-concerns` because the registry cannot judge them. Each trial card")
    lines.append("ships a `robSource:` attribution string listing the exact AACT inputs.")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 6. Provenance & reproducibility")
    lines.append("")
    lines.append("- **AACT snapshot:** 2026-04-12 (Clinical Trials Transformation Initiative)")
    lines.append("- **PubMed bridge:** NCBI E-utilities + idconv API")
    lines.append("- **Repo:** https://github.com/mahmood726-cyber/rapidmeta-finerenone")
    lines.append("- **Scripts:** `scripts/bulk_clone_audit_first.py` (initial build),")
    lines.append("  `scripts/build_aact_pmid_and_design_maps.py` (PMID/RoB enrichment),")
    lines.append("  `scripts/build_aact_counts_with_param_type.py` (count extraction),")
    lines.append("  `scripts/build_aact_continuous.py` (continuous-outcome effects).")
    lines.append("")
    return "\n".join(lines)


def main():
    targets = sorted(p for p in HERE.glob("*_AUTO_FULL_REVIEW.html") if p.is_file())
    print(f"Generating protocols for {len(targets):,} AUTO_FULL_REVIEW pages...")

    n_generated = n_skipped_exists = 0
    n_href_restored = 0
    for i, p in enumerate(targets, 1):
        stem = p.name.replace("_AUTO_FULL_REVIEW.html", "")
        proto_name = f"{stem.lower()}_auto_protocol_v1.1_2026-04-20.md"
        proto_path = PROTOCOLS / proto_name
        if proto_path.exists():
            n_skipped_exists += 1
            continue
        txt = p.read_text(encoding="utf-8", errors="replace")
        # Title
        h1_m = H1_RE.search(txt)
        h1 = strip_html(h1_m.group(1)) if h1_m else stem.replace("_", " ").title()
        pico = extract_pico(txt)
        # Acronyms map for nicer trial names
        acronyms = extract_acronyms(txt)
        trials = extract_trials(txt)
        for t in trials:
            if t["nct"] in acronyms and acronyms[t["nct"]] != t["nct"]:
                t["name"] = acronyms[t["nct"]]
        md = render_protocol(stem, h1, pico, trials)
        proto_path.write_text(md, encoding="utf-8")
        n_generated += 1
        # Restore the original specific-protocol href in the FULL_REVIEW header.
        new_href = f'href="protocols/{proto_name}"'
        new_txt, n_sub = HEAD_PROTOCOL_HREF_RE.subn(
            new_href + r"\1", txt, count=1
        )
        if n_sub:
            p.write_text(new_txt, encoding="utf-8")
            n_href_restored += 1
        if i % 200 == 0:
            print(f"  [{i}/{len(targets)}] {p.name}")
    print(f"\nGenerated:     {n_generated:,} protocol files")
    print(f"Skipped (already existed): {n_skipped_exists:,}")
    print(f"FULL_REVIEW hrefs restored to specific file: {n_href_restored:,}")


if __name__ == "__main__":
    main()
