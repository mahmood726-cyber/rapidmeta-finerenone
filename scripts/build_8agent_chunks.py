"""Build 8 blinded review-audit chunks + TruthCert input manifest.

Sample = 168 reviews from 3 unvalidated bands:
  - LOW_CONCERN (95): score 0.30 ≤ s < 0.50
  - MANUAL_REVIEW (62): score 0.50 ≤ s < 0.70
  - Quarantined (11): score-irrelevant, banner-injected

Each of 8 agents gets ~21 reviews, randomly assigned (stratified by band so
each agent sees a mix of all 3 levels — avoids one agent getting only-easy
or only-hard chunks).

TruthCert methodology:
  Each chunk has an input manifest signed with HMAC-SHA256 keyed by
  TRUTHCERT_HMAC_KEY env var. The agent's output is paired with the input's
  sig in its own output manifest, also HMAC-signed. Aggregator verifies
  both sigs before accepting findings.

Output:
  outputs/extraction_audit/8agent_chunks/<chunk_id>.json
"""
from __future__ import annotations
import json, os, sys, io, hashlib, hmac, random
from pathlib import Path

if hasattr(sys.stdout, "buffer") and getattr(sys.stdout, "encoding", "").lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent.parent
OUT = HERE / "outputs" / "extraction_audit"
CHUNK_DIR = OUT / "8agent_chunks"
CHUNK_DIR.mkdir(parents=True, exist_ok=True)
DATA = OUT / "data"

random.seed(8642)

# TruthCert key — never from the bundle (per lessons.md)
HMAC_KEY = os.environ.get("TRUTHCERT_HMAC_KEY")
if not HMAC_KEY:
    # Generate a session key (recorded local-only, NOT committed)
    keyfile = HERE / ".truthcert_8agent.key"
    if keyfile.exists():
        HMAC_KEY = keyfile.read_text(encoding="utf-8").strip()
    else:
        HMAC_KEY = hashlib.sha256(os.urandom(32)).hexdigest()
        keyfile.write_text(HMAC_KEY, encoding="utf-8")
    print(f"Session HMAC key cached at {keyfile} (gitignored)")
# Add to gitignore
gi = HERE / ".gitignore"
if gi.exists():
    if ".truthcert_8agent.key" not in gi.read_text(encoding="utf-8"):
        with open(gi, "a", encoding="utf-8") as f:
            f.write("\n.truthcert_8agent.key\n")

# Load classifier scores
scores = json.loads((OUT / "fabrication_risk_scores.json").read_text(encoding="utf-8"))

# Identify already-quarantined reviews (set from R3 + R4 logs)
quarantined = set()
for fname in ["multi_agent_fixes_applied_r3.json", "multi_agent_fixes_applied_r4.json"]:
    p = OUT / fname
    if not p.exists(): continue
    log = json.loads(p.read_text(encoding="utf-8"))
    for entry in log.get("batch2", []) + log.get("batch1", []):
        if entry.get("status") == "QUARANTINED":
            quarantined.add(entry["review"])
# Plus the 2 post-R4 escalations
quarantined.update(["MM_BISPECIFIC_BROAD_NMA_REVIEW", "BLADDER_NMIBC_NEW_NMA_REVIEW"])

# Partition into 3 bands
band_low = [r["review"] for r in scores
            if 0.30 <= r["score"] < 0.50 and r["review"] not in quarantined]
band_manual = [r["review"] for r in scores
               if 0.50 <= r["score"] < 0.70 and r["review"] not in quarantined]
band_quar = sorted(quarantined)

print(f"Bands:")
print(f"  LOW_CONCERN:   {len(band_low)} reviews")
print(f"  MANUAL_REVIEW: {len(band_manual)} reviews")
print(f"  Quarantined:   {len(band_quar)} reviews")
print(f"  Total:         {len(band_low) + len(band_manual) + len(band_quar)}")

# Stratified round-robin into 8 chunks
chunks = [[] for _ in range(8)]
def assign_round_robin(reviews: list[str], band_label: str):
    random.shuffle(reviews)
    for i, rv in enumerate(reviews):
        chunks[i % 8].append({"review": rv, "band": band_label})

assign_round_robin(band_low, "LOW_CONCERN")
assign_round_robin(band_manual, "MANUAL_REVIEW")
assign_round_robin(band_quar, "QUARANTINED")

# Build per-chunk trial data
def build_trial_data(rv: str) -> list[dict]:
    p = DATA / f"{rv}.json"
    if not p.exists(): return []
    try: d = json.loads(p.read_text(encoding="utf-8"))
    except: return []
    rd = d.get("realData") or {}
    if not isinstance(rd, dict): return []
    out = []
    for nct, t in rd.items():
        if not isinstance(t, dict): continue
        if nct.startswith("NULLED:"): continue
        out.append({
            "nct": nct, "name": t.get("name"),
            "year": t.get("year"), "pmid": t.get("pmid"),
            "group": t.get("group"),
            "tE": t.get("tE"), "tN": t.get("tN"),
            "cE": t.get("cE"), "cN": t.get("cN"),
            "publishedHR": t.get("publishedHR"),
            "hrLCI": t.get("hrLCI"), "hrUCI": t.get("hrUCI"),
            "estimandType": t.get("estimandType"),
        })
    return out


def hmac_sign(payload: bytes) -> str:
    return hmac.new(HMAC_KEY.encode("utf-8"), payload, hashlib.sha256).hexdigest()


for ci, chunk in enumerate(chunks):
    chunk_id = f"chunk_{ci+1}_of_8"
    reviews_with_data = []
    for entry in chunk:
        trials = build_trial_data(entry["review"])
        reviews_with_data.append({
            "review": entry["review"],
            "band": entry["band"],
            "n_trials": len(trials),
            "trials": trials,
        })
    n_trials_total = sum(r["n_trials"] for r in reviews_with_data)
    canonical = json.dumps(reviews_with_data, sort_keys=True, separators=(",", ":")).encode("utf-8")
    sig = hmac_sign(canonical)
    manifest = {
        "chunk_id": chunk_id,
        "n_reviews": len(reviews_with_data),
        "n_trials": n_trials_total,
        "bands_in_chunk": sorted({r["band"] for r in reviews_with_data}),
        "input_sha256": hashlib.sha256(canonical).hexdigest(),
        "input_hmac_sig": sig,
        "instructions": "See agent prompt. Emit findings JSON paired with output_hmac_sig.",
        "reviews": reviews_with_data,
    }
    chunk_path = CHUNK_DIR / f"{chunk_id}.json"
    chunk_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  {chunk_id}: {len(reviews_with_data)} reviews / {n_trials_total} trials → {chunk_path.name}")

print(f"\nAll 8 chunks written to {CHUNK_DIR}")
print(f"HMAC sig algorithm: SHA-256, key length: {len(HMAC_KEY)} hex chars")
