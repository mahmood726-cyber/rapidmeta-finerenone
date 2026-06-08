"""Relabel MACE->benchmark-key for HOMOGENEOUS benchmarked curated apps.

These OLD-engine curated apps carry the all-MACE outcome mislabel but have a
REAL topic benchmark keyed by the true endpoint. Clustering is the wrong tool
here (it can split valid pools); the benchmark key IS the authoritative
endpoint. Safe rule:

  - app must have exactly ONE non-"MACE" top-level benchmark key K
  - the app's outcomes must form a SINGLE cluster (homogeneous = all the same
    endpoint), so relabeling every outcome to K neither over- nor under-pools
  -> replace shortLabel "MACE" -> K, selectedOutcome -> "default", neutralize
     visible MACE. Pool is preserved (all share K); benchmark now key-matches.

Heterogeneous apps (multiple clusters) and MACE-keyed (genuinely CV) apps are
skipped and reported. Idempotent, --dry-run, jscheck-gated.
"""
from __future__ import annotations
import argparse, glob, io, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import analyze_poolability as ap
import harmonize_outcomes as ho

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
THRESH = 0.5


def benchmark_keys(html):
    m = re.search(r"PUBLISHED_META_BENCHMARKS\s*[:=]\s*\{", html)
    if not m:
        return []
    i = html.index("{", m.start())
    depth, end = 0, -1
    for j in range(i, len(html)):
        if html[j] == "{":
            depth += 1
        elif html[j] == "}":
            depth -= 1
            if depth == 0:
                end = j
                break
    seg = html[i:end + 1] if end > 0 else html[i:i + 4000]
    return re.findall(r"([A-Za-z_][A-Za-z0-9_]*)\s*:\s*\[", seg)


def process(html):
    if 'shortLabel:"MACE"' not in html and "shortLabel:'MACE'" not in html:
        return html, "no-mace"
    if "_outcomeAvailabilityCount(" in html:
        return html, "newer-engine"
    bks = benchmark_keys(html)
    nonmace = [k for k in bks if k != "MACE"]
    if not nonmace:
        return html, "mace-or-no-benchmark"
    if len(set(nonmace)) != 1:
        return html, f"multi-key({len(set(nonmace))})"
    K = nonmace[0]
    outs = [o for _, o in ap.extract_trial_outcomes(html)]
    if len(outs) < 1:
        return html, "no-outcomes"
    clusters = ap.cluster_outcomes(outs, THRESH)
    if len(clusters) != 1:
        return html, f"heterogeneous({len(clusters)} clusters)"
    # homogeneous + single benchmark key -> relabel all MACE shortLabels to K
    new = re.sub(r'(\{shortLabel:(["\']))MACE\2', lambda m: m.group(1) + K + m.group(2), html)
    new = new.replace('selectedOutcome:"MACE"', 'selectedOutcome:"default"')
    new = new.replace("Primary MACE Result", "Primary Result")
    new = new.replace(" (MACE)", "")
    new = new.replace("prevent 1 MACE event", "prevent 1 event")
    return new, f"relabeled->{K}"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--glob", default="*_REVIEW.html")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("files", nargs="*")
    args = p.parse_args()
    try:
        import jscheck
    except Exception:
        jscheck = None

    files = list(args.files) or sorted(glob.glob(os.path.join(HERE, args.glob)))
    from collections import Counter
    outcome = Counter()
    done = reverted = 0
    relabeled_apps = []
    for f in files:
        if "_AUTO" in os.path.basename(f):
            continue
        html = io.open(f, encoding="utf-8", errors="replace").read()
        new, reason = process(html)
        key = reason.split("->")[0] if reason.startswith("relabeled") else reason
        outcome[key] += 1
        if not reason.startswith("relabeled"):
            continue
        if args.dry_run:
            done += 1
            relabeled_apps.append((os.path.basename(f), reason))
            continue
        io.open(f, "w", encoding="utf-8", newline="").write(new)
        if jscheck is not None and jscheck.check(f):
            io.open(f, "w", encoding="utf-8", newline="").write(html)
            reverted += 1
            continue
        done += 1
        relabeled_apps.append((os.path.basename(f), reason))

    print(f"{'DRY-RUN' if args.dry_run else 'APPLIED'}  relabeled={done} reverted={reverted}")
    print("outcome breakdown:", dict(outcome))
    for n, r in relabeled_apps[:25]:
        print(f"   {n}: {r}")


if __name__ == "__main__":
    main()
