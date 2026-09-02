"""Build the comparator-seed firewall exclusion set.

PHASE 0 of the comparator-seeded retrieval path. Enumerates every topic that is
currently SCORED against a published comparator, and every comparator work used
to score one. Those two sets are the exclusion list: a topic in the first set may
never be seeded, and a comparator in the second set may never be used as a seed.

Reads only committed repo artefacts. Writes outputs/comparator_seed_firewall.json.
"""
import json
import io
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = os.environ.get("REPO_ROOT", os.getcwd())
OUT_ROOT = os.environ.get("OUT_ROOT", ROOT)


def norm(name):
    """Normalise a topic label to a comparable key.

    'Acs Antiplatelet' / 'ACS_ANTIPLATELET_REVIEW.html' / 'acs-antiplatelet-review'
    all collapse to ACS_ANTIPLATELET.
    """
    s = re.sub(r"\.html?$", "", str(name), flags=re.I)
    s = re.sub(r"[^A-Za-z0-9]+", "_", s).strip("_").upper()
    for suf in ("_AUTO_FULL_REVIEW", "_AUTO_REVIEW", "_FULL_REVIEW", "_REVIEW", "_NEW"):
        if s.endswith(suf):
            s = s[: -len(suf)]
    return s


def load(rel):
    p = os.path.join(ROOT, rel)
    if not os.path.exists(p):
        return None
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


def main():
    sources = {}
    scored = {}      # norm key -> list of {source, label}
    comparators = {} # doi -> {citation, topics:[]}

    big = load("outputs/published_meta_comparisons.json")
    if big is None:
        raise SystemExit("FATAL: outputs/published_meta_comparisons.json absent - cannot enumerate the scored set")
    n = 0
    for bucket in ("genuine", "wrong_outcome_agent_mismatch", "continuous_mismatch"):
        for r in big.get(bucket, []):
            n += 1
            k = norm(r["app"])
            scored.setdefault(k, []).append(
                {"source": "published_meta_comparisons.json:" + bucket, "label": r["app"]}
            )
            doi = (r.get("doi") or "").strip().lower()
            if doi:
                e = comparators.setdefault(doi, {"citation": r.get("citation"), "topics": []})
                e["topics"].append(k)
    sources["outputs/published_meta_comparisons.json"] = n

    small = load("outputs/published_meta_comparison.json")
    if small:
        for row in small:
            k = norm(row[0])
            scored.setdefault(k, []).append(
                {"source": "published_meta_comparison.json", "label": row[0]}
            )
        sources["outputs/published_meta_comparison.json"] = len(small)

    bench = load("outputs/benchmark_set.json")
    if bench:
        for name in bench:
            k = norm(name)
            scored.setdefault(k, []).append(
                {"source": "benchmark_set.json", "label": name}
            )
        sources["outputs/benchmark_set.json"] = len(bench)

    inv = load("_inventory.json")
    all_topics = sorted({norm(r["file"]) for r in inv}) if inv else []

    out = {
        "_doc": (
            "PHASE-0 FIREWALL. A topic seeded from a published comparator can never be "
            "scored against that comparator. Topics listed in scored_topics are EXCLUDED "
            "from comparator seeding. Comparator works listed in scored_comparator_dois "
            "are EXCLUDED from use as seeds. Both sets are declared before any reference "
            "list is fetched."
        ),
        "rule": {
            "id": "COMPARATOR_SEED_FIREWALL_V1",
            "seedable": "a topic is seedable iff norm(topic) not in scored_topics",
            "usable_as_seed": "a published MA is usable as a seed iff its DOI not in scored_comparator_dois",
            "provenance": "every trial entering the corpus via this route carries found_via='FOUND_VIA_COMPARATOR' and seed_source_pmcid/seed_source_doi, and is never counted as our own search yield",
        },
        "counts": {
            "source_records": sources,
            "scored_topics": len(scored),
            "scored_comparator_dois": len(comparators),
            "all_corpus_topics": len(all_topics),
            "seedable_topics": len([t for t in all_topics if t not in scored]),
        },
        "scored_topics": {k: v for k, v in sorted(scored.items())},
        "scored_comparator_dois": {k: v for k, v in sorted(comparators.items())},
    }
    dest = os.path.join(OUT_ROOT, "outputs", "comparator_seed_firewall.json")
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1, ensure_ascii=False)
    print(json.dumps(out["counts"], indent=1))
    print("wrote", dest)


if __name__ == "__main__":
    main()
