"""Check remaining Sentinel methodology rule violations across curated REVIEW pages."""
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent

n_files = 0
no_reml_iteration = []
no_reml_primary = []
no_mh_pool = []
rob_me_chip_no_engine = []

for p in HERE.glob("*_REVIEW.html"):
    if not p.is_file() or "AUTO" in p.name or "FULL_REVIEW" in p.name:
        continue
    txt = p.read_text(encoding="utf-8", errors="replace")
    if "tau2" not in txt and "REML" not in txt:
        continue  # not a substantive pooling page
    n_files += 1

    # REML iteration block: has tau2_reml + iteration math
    if "tau2_reml" in txt:
        if not re.search(r"tau2_reml\s*\+\s*_delta|_delta\s*=.*?tau2_reml", txt):
            no_reml_iteration.append(p.name)
    else:
        # No tau2_reml at all
        no_reml_iteration.append(p.name)
        no_reml_primary.append(p.name)

    # REML primary selection
    if "tau2_reml" in txt and not re.search(
        r"const\s+tau2\s*=.*?tau2_reml|tau2\s*=\s*tau2_reml", txt
    ):
        if p.name not in no_reml_primary:
            no_reml_primary.append(p.name)

    # M-H pool
    has_binary = bool(re.search(r"\btE:\s*\d+,\s*tN:", txt))
    has_mh = bool(re.search(r"mantel|m_h\b|mantelHaenszel|\bMH_OR\b|mhPool|peto",
                            txt, re.IGNORECASE))
    if has_binary and not has_mh:
        no_mh_pool.append(p.name)

    # ROB-ME chip without backing engine
    has_chip = "chip-robme" in txt or "ROB-ME:" in txt
    has_engine = bool(re.search(
        r"\bRobMe\b|robMe[A-Z]|computeRobMe|robme_|RobMeEngine|domains_robme",
        txt,
    ))
    if has_chip and not has_engine:
        rob_me_chip_no_engine.append(p.name)

print(f"Substantive pooling REVIEW files: {n_files}")
print()
print(f"Missing REML iteration block (only DL): {len(no_reml_iteration)}")
print(f"Has tau2_reml but doesn't select it as primary: {len(no_reml_primary) - sum(1 for f in no_reml_primary if f in no_reml_iteration)}")
print(f"Has binary trials but no M-H pool: {len(no_mh_pool)}")
print(f"Has RoB-ME chip but no engine: {len(rob_me_chip_no_engine)}")
print()
print("Sample no-REML-iteration:")
for f in no_reml_iteration[:5]: print(f"  {f}")
print("Sample no-M-H:")
for f in no_mh_pool[:5]: print(f"  {f}")
print("Sample chip-no-engine:")
for f in rob_me_chip_no_engine[:5]: print(f"  {f}")
