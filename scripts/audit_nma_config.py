"""Audit NMA_CONFIG vs realData across all *_NMA_REVIEW.html files.

Detects two methodological anomalies:

  1. **NMA_DEGENERATE**: NMA_CONFIG declares fewer than 3 treatments
     (i.e., the network has only 2 nodes — that's a pairwise MA labelled as NMA).

  2. **TRIALS_DROPPED**: NMA_CONFIG references fewer trial NCTs than
     realData contains (silently excluded trials that the title/scope
     suggests should be in the network).

Output: outputs/nma_config_audit.csv + console summary.

Use this audit to decide which reviews to (a) demote to pairwise MA file
naming or (b) extend the NMA_CONFIG to capture all realData trials.
"""
from __future__ import annotations
import sys, io, csv, re, json
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path("C:/Projects/Finrenone")
OUT_CSV = REPO / "outputs" / "nma_config_audit.csv"


# Match `const NMA_CONFIG = { ... }` — non-greedy, balanced-brace tolerant
# enough for our HTMLs (no nested template literals inside the literal).
NMA_CONFIG_RE = re.compile(r'const\s+NMA_CONFIG\s*=\s*(\{[\s\S]*?\});', re.MULTILINE)

# Match every `'NCT...': {` real-data block opener
REALDATA_NCT_RE = re.compile(r"'(NCT\d+)'\s*:\s*\{")


def parse_nma_config(text: str):
    """Extract treatments + comparison NCTs from NMA_CONFIG. Returns
    {treatments: [...], comparison_trials: set[str], raw_str: str} or None."""
    m = NMA_CONFIG_RE.search(text)
    if not m:
        return None
    raw = m.group(1)
    # Try strict JSON parse (NMA_CONFIG is JSON-shaped in our corpus).
    try:
        cfg = json.loads(raw)
    except json.JSONDecodeError:
        # Fallback: regex out treatments + trial NCTs by hand
        treats = re.findall(r'"treatments"\s*:\s*\[([^\]]*)\]', raw)
        trials = REALDATA_NCT_RE.findall(raw)
        if not treats:
            return None
        treat_list = re.findall(r'"([^"]+)"', treats[0])
        return {
            "treatments": treat_list,
            "comparison_trials": set(re.findall(r"NCT\d+", raw)),
            "raw_chars": len(raw),
            "parse_method": "regex",
        }
    trial_set: set[str] = set()
    for c in cfg.get("comparisons", []) or []:
        for t in c.get("trials", []) or []:
            if isinstance(t, str) and t.startswith("NCT"):
                trial_set.add(t)
    return {
        "treatments": list(cfg.get("treatments", [])),
        "comparison_trials": trial_set,
        "raw_chars": len(raw),
        "parse_method": "json",
    }


def realdata_ncts(text: str) -> set[str]:
    """Return the set of NCTs appearing as keys in the realData object."""
    # realData blocks are at the indentation level of `'NCTxxxxxxxx': {`
    # We need to ignore mentions inside NMA_CONFIG.comparisons[].trials[].
    # Approach: count distinct NCT keys throughout the file, then SUBTRACT
    # the NCTs found in NMA_CONFIG.
    return set(REALDATA_NCT_RE.findall(text))


def main():
    files = sorted(REPO.glob("*_NMA_REVIEW.html"))
    print(f"Scanning {len(files)} *_NMA_REVIEW.html files ...")

    rows = []
    for hp in files:
        text = hp.read_text(encoding="utf-8", errors="replace")
        cfg = parse_nma_config(text)
        all_ncts = realdata_ncts(text)

        if cfg is None:
            rows.append({
                "file": hp.name,
                "verdict": "NO_NMA_CONFIG",
                "n_treatments": 0,
                "treatments": "",
                "n_realdata_ncts": len(all_ncts),
                "n_config_ncts": 0,
                "dropped_trials": "",
                "notes": "no NMA_CONFIG declaration found",
            })
            continue

        n_t = len(cfg["treatments"])
        cfg_ncts = cfg["comparison_trials"]
        # realData NCTs not referenced in NMA_CONFIG.comparisons[].trials
        dropped = all_ncts - cfg_ncts

        verdicts = []
        if n_t < 3:
            verdicts.append("NMA_DEGENERATE_2T")
        if dropped:
            verdicts.append(f"TRIALS_DROPPED({len(dropped)})")
        if not verdicts:
            verdicts = ["OK"]

        rows.append({
            "file": hp.name,
            "verdict": ";".join(verdicts),
            "n_treatments": n_t,
            "treatments": ", ".join(cfg["treatments"][:6]) + ("..." if n_t > 6 else ""),
            "n_realdata_ncts": len(all_ncts),
            "n_config_ncts": len(cfg_ncts),
            "dropped_trials": ", ".join(sorted(dropped)[:6]) + ("..." if len(dropped) > 6 else ""),
            "notes": cfg["parse_method"],
        })

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    by_v = {}
    for r in rows:
        for tag in r["verdict"].split(";"):
            tag = tag.split("(")[0]
            by_v[tag] = by_v.get(tag, 0) + 1

    print(f"\n=== Verdict tally ===")
    for tag, n in sorted(by_v.items(), key=lambda x: -x[1]):
        print(f"  {tag:25s} {n}")

    degen = [r for r in rows if "NMA_DEGENERATE" in r["verdict"]]
    print(f"\n=== {len(degen)} 2-treatment 'NMA' files (pairwise MA mislabelled) ===")
    for r in degen:
        print(f"  {r['file'][:48]:48s}  treats=[{r['treatments']}]  realdata_NCTs={r['n_realdata_ncts']}, config_NCTs={r['n_config_ncts']}")

    drop = [r for r in rows if "TRIALS_DROPPED" in r["verdict"] and "NMA_DEGENERATE" not in r["verdict"]]
    print(f"\n=== {len(drop)} files with trials silently excluded from NMA_CONFIG ===")
    for r in drop[:30]:
        print(f"  {r['file'][:48]:48s}  treats={r['n_treatments']}  rd={r['n_realdata_ncts']} cfg={r['n_config_ncts']}  dropped={r['dropped_trials']}")

    nocfg = [r for r in rows if r["verdict"] == "NO_NMA_CONFIG"]
    print(f"\n=== {len(nocfg)} *_NMA_REVIEW.html files with NO NMA_CONFIG declaration ===")
    for r in nocfg[:20]:
        print(f"  {r['file'][:48]:48s}  realdata_NCTs={r['n_realdata_ncts']}")

    print(f"\nWritten: {OUT_CSV}")


if __name__ == "__main__":
    main()
