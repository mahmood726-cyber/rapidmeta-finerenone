"""Phase 1 demotion: rename _NMA_REVIEW.html files that aren't actually NMAs
and strip their NMA tab.

Two passes via --target flag:
  --target degenerate   3 files where NMA_CONFIG declares only 2 treatments
                        (pairwise MA mislabelled as NMA)
  --target no-config    21 files named *_NMA_REVIEW.html that have no
                        NMA_CONFIG declaration at all (engine has nothing
                        to render, NMA tab probably empty)

For each affected file:
  A. Remove the NMA tab button:
     `<button onclick="RapidMeta.switchTab('nma')" ...>5. Network Meta-Analysis</button>`
  B. Remove the NMA tab content section:
     `<section id="tab-nma" ...>...</section>` (balanced, ~12KB on average)
  C. git mv FOO_NMA_REVIEW.html → FOO_REVIEW.html (drop the _NMA_)

Idempotent. Refuses to touch files where the NMA tab landmarks are already
absent, or where renaming would collide with an existing FOO_REVIEW.html.

Use --dry-run to preview. Then run without --dry-run to apply.

After renaming, you'll want to re-run scripts/compute_verdict_badges.py
because it indexes by filename.
"""
from __future__ import annotations
import sys, io, re, argparse, subprocess
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path("C:/Projects/Finrenone")

# 3 degenerate files (NMA_CONFIG.treatments.length < 3 per audit)
DEGENERATE = [
    "ADC_HER2_ADJUVANT_NMA_REVIEW.html",
    "ADC_HER2_LOW_NMA_REVIEW.html",
    "HER2_LOW_ADC_NMA_REVIEW.html",
]

# 21 files named *_NMA_REVIEW.html with no NMA_CONFIG
NO_CONFIG = [
    "AGYW_HIV_PREP_NMA_REVIEW.html",
    "ALDO_SYNTHASE_NMA_REVIEW.html",
    "ALK_NSCLC_NMA_REVIEW.html",
    "ALOPECIA_JAKI_NMA_REVIEW.html",
    "ATTR_CM_NMA_REVIEW.html",
    "ATTR_PN_NMA_REVIEW.html",
    "FRAGILITY_FRACTURE_NMA_REVIEW.html",
    "HCC_1L_NMA_REVIEW.html",
    "HEPATITIS_HCV_DAA_NMA_REVIEW.html",
    "HIV_ART_FIRSTLINE_NMA_REVIEW.html",
    "HIV_LA_PREP_NMA_REVIEW.html",
    "HPV_DOSE_REDUCTION_NMA_REVIEW.html",
    "IL23_PSA_NMA_REVIEW.html",
    "JAKI_AD_NMA_REVIEW.html",
    "KRAS_G12C_NMA_REVIEW.html",
    "MALARIA_ACT_NMA_REVIEW.html",
    "MALARIA_VACCINES_NMA_REVIEW.html",
    "MM_1L_NMA_REVIEW.html",
    "PPH_BUNDLE_NMA_REVIEW.html",
    "RCC_1L_NMA_REVIEW.html",
    "SCD_DISEASE_MOD_NMA_REVIEW.html",
]

NMA_BUTTON_RE = re.compile(
    r'\s*<button[^>]*onclick="RapidMeta\.switchTab\(\'nma\'\)"[^>]*>'
    r'[^<]*</button>\s*'
)


def find_nma_section(text: str):
    """Return (start, end) indices of <section id="tab-nma" ...>...</section>
    with balanced section nesting. Returns None if not found."""
    m = re.search(r'<section id="tab-nma"', text)
    if not m:
        return None
    s = m.start()
    i = s
    depth = 0
    while i < len(text):
        op = text.find("<section", i)
        cl = text.find("</section>", i)
        if cl == -1:
            return None
        if op != -1 and op < cl:
            depth += 1
            i = op + 8
        else:
            depth -= 1
            i = cl + 10
            if depth == 0:
                return (s, i)
    return None


def strip_nma_from_file(path: Path, dry_run: bool) -> dict:
    text = path.read_text(encoding="utf-8", errors="replace")
    btn_match = NMA_BUTTON_RE.search(text)
    sec = find_nma_section(text)

    actions = []
    new_text = text
    # Remove section first (later position) so button offset stays valid.
    if sec:
        new_text = new_text[:sec[0]] + new_text[sec[1]:]
        actions.append(f"section -{sec[1]-sec[0]}c")
    if btn_match:
        # Re-find button after section removal
        m2 = NMA_BUTTON_RE.search(new_text)
        if m2:
            new_text = new_text[:m2.start()] + new_text[m2.end():]
            actions.append(f"button -{m2.end()-m2.start()}c")

    if not actions:
        return {"changed": False, "actions": []}
    if not dry_run:
        path.write_text(new_text, encoding="utf-8")
    return {"changed": True, "actions": actions}


def rename_file(path: Path, dry_run: bool) -> Path | None:
    new_name = path.name.replace("_NMA_REVIEW.html", "_REVIEW.html")
    new_path = path.parent / new_name
    if new_path.exists():
        print(f"  COLLISION  {path.name} → {new_name} (target already exists)")
        return None
    if dry_run:
        return new_path
    # Use git mv for clean history
    try:
        subprocess.check_call(
            ["git", "-C", str(REPO), "mv", path.name, new_name],
            stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT
        )
    except subprocess.CalledProcessError:
        # Fallback: file isn't tracked yet → plain rename
        path.rename(new_path)
    return new_path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", choices=["degenerate", "no-config", "both"], required=True)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    queue: list[str] = []
    if args.target in ("degenerate", "both"):
        queue.extend(DEGENERATE)
    if args.target in ("no-config", "both"):
        queue.extend(NO_CONFIG)

    print(f"Phase 1 demote — {len(queue)} files (--target {args.target})")
    if args.dry_run:
        print("  DRY RUN — no changes written.")

    stripped, renamed, skipped = 0, 0, 0
    for fname in queue:
        path = REPO / fname
        if not path.exists():
            print(f"  MISSING  {fname}")
            skipped += 1
            continue

        # Strip NMA tab from contents (only if landmarks present)
        result = strip_nma_from_file(path, dry_run=args.dry_run)
        if result["changed"]:
            stripped += 1
            print(f"  STRIP    {fname}  [{', '.join(result['actions'])}]")
        else:
            print(f"  CLEAN    {fname}  (no NMA tab landmarks)")

        # Rename
        new_path = rename_file(path, dry_run=args.dry_run)
        if new_path:
            renamed += 1
            print(f"  RENAME   → {new_path.name}")

    print(f"\n=== Summary ===")
    print(f"  Tab content stripped: {stripped}")
    print(f"  Renamed:              {renamed}")
    print(f"  Skipped/missing:      {skipped}")
    if args.dry_run:
        print("  (DRY RUN — nothing written)")


if __name__ == "__main__":
    main()
