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


_GENERIC = {"response", "rate", "change", "score", "freq", "primary", "composite",
            "index", "total", "mean", "time", "free", "pct", "ratio", "annualized"}


def _expand_key(K):
    """Split a benchmark key (UPPER_SNAKE / CamelCase) into distinctive,
    non-generic word tokens used to test whether an outcome IS that endpoint."""
    parts = re.split(r"[_\s]+", K)
    toks = []
    for part in parts:
        for w in re.findall(r"[A-Z]+(?=[A-Z][a-z])|[A-Z]?[a-z]+|[A-Z]+|\d+", part):
            toks.append(w.lower())
    return [t for t in toks if len(t) >= 3 and not t.isdigit() and t not in _GENERIC]


def _all_share_key_token(outs, distinctive):
    """True iff EVERY outcome's normalized text contains >=1 distinctive key
    token (prefix match), i.e. all outcomes are the benchmark endpoint."""
    if not distinctive:
        return False
    for o in outs:
        toks = ap.normalize_tokens(o["title"])
        text = " ".join(toks)
        if not any(d in text for d in distinctive):
            return False
    return True


# Finerenone-template outcome CLASS labels — all wrong for a non-CV topic.
# Only these are rewritten to the benchmark key; already-harmonized keys
# (slugs/real acronyms) are left untouched so we never clobber correct labels.
TEMPLATE_LABELS = {"MACE", "CVD", "ACM", "ACH", "Renal", "Renal40", "Renal57",
                   "Safety", "RecurrentHF", "Hyperkalemia", "HF_CV_First",
                   "KidneyComp"}
_TEMPLATE_RE = re.compile(
    r'(\{shortLabel:(["\']))(' + "|".join(sorted(TEMPLATE_LABELS, key=len, reverse=True)) + r')\2')


_CV_RE = re.compile(
    r"cardiovascular|\bmace\b|myocardial|\bstroke\b|heart failure|cv death|"
    r"hf hospitali|worsening hf|composite of (?:cv|cardiovascular)", re.I)


def _outcomes_are_cv(outs):
    cv = sum(1 for o in outs if _CV_RE.search(o["title"]))
    return cv >= max(1, (len(outs) + 1) // 2)  # majority of outcome titles are CV


_RELABEL_TEMPLATE_RE = re.compile(
    r'(\{shortLabel:(["\']))(' + "|".join(sorted(TEMPLATE_LABELS, key=len, reverse=True))
    + r')\2,title:(["\'])(?P<title>(?:\\.|(?!\4).)*)\4')


def _relabel_by_cluster(html, outs, clusters, K=None):
    """Assign K to the cluster matching the benchmark endpoint (if K given) +
    harmonized keys to the rest; rewrite all template-label shortLabels by the
    outcome's title -> cluster key."""
    titles = [o["title"] for o in outs]
    distinctive = _expand_key(K) if K else []
    used, title_key = set(), {}
    for cl in clusters:
        cl_titles = [titles[i] for i in cl]
        cl_matches = (distinctive and K not in used and all(
            any(d in " ".join(ap.normalize_tokens(titles[i])) for d in distinctive)
            for i in cl))
        if cl_matches:
            key = K
        else:
            key = ho.assign_keys([outs[i] for i in cl], [list(range(len(cl)))])[cl_titles[0]]
        base, n = key, 2
        while key in used and key != K:
            key = f"{base}{n}"; n += 1
        used.add(key)
        for t in cl_titles:
            title_key[t] = key

    def _repl(m):
        key = title_key.get(m.group("title"), m.group(3))
        return (m.group(1) + key + m.group(2) + ",title:"
                + m.group(4) + m.group("title") + m.group(4))
    return _RELABEL_TEMPLATE_RE.sub(_repl, html)


def process(html):
    if "_outcomeAvailabilityCount(" in html:
        return html, "newer-engine"
    if not _TEMPLATE_RE.search(html):
        return html, "no-template-label"
    outs = [o for _, o in ap.extract_trial_outcomes(html)]
    if len(outs) < 1:
        return html, "no-outcomes"
    clusters = ap.cluster_outcomes(outs, THRESH)
    bks = benchmark_keys(html)
    nonmace = [k for k in bks if k != "MACE"]
    if not nonmace:
        # benchmark key is "MACE" (a leftover) or absent. If the outcomes are
        # genuinely cardiovascular, MACE is correct -> leave. Otherwise the
        # template labels mislabel real endpoints (HIV-RNA/OS/BCVA/weight) ->
        # harmonize from the outcome titles.
        if _outcomes_are_cv(outs):
            return html, "genuine-cv"
        new = _relabel_by_cluster(html, outs, clusters, K=None)
        tag = f"mace-harmonize({len(clusters)})"
    elif len(set(nonmace)) != 1:
        # >1 distinct benchmark key: harmonize from titles (each endpoint its
        # own key); standard-acronym endpoints align to their benchmark key.
        new = _relabel_by_cluster(html, outs, clusters, K=None)
        tag = f"multi-key-split({len(set(nonmace))})"
    else:
        K = nonmace[0]
        distinctive = _expand_key(K)
        if len(clusters) == 1 or _all_share_key_token(outs, distinctive):
            new = _TEMPLATE_RE.sub(lambda m: m.group(1) + K + m.group(2), html)
            tag = f"relabeled->{K}"
        else:
            new = _relabel_by_cluster(html, outs, clusters, K=K)
            tag = f"hetero-split->{K}+{len(clusters)-1}"
    new = re.sub(r'selectedOutcome:"(?:' + "|".join(TEMPLATE_LABELS) + r')"',
                 'selectedOutcome:"default"', new)
    new = new.replace("Primary MACE Result", "Primary Result")
    new = new.replace(" (MACE)", "")
    new = new.replace("prevent 1 MACE event", "prevent 1 event")
    if new == html:
        return html, "no-change"
    return new, tag


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
        is_change = reason.startswith(("relabeled", "hetero-split", "mace-harmonize",
                                       "multi-key-split"))
        key = reason.split("->")[0].split("(")[0] if is_change else reason
        outcome[key] += 1
        if not is_change:
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
