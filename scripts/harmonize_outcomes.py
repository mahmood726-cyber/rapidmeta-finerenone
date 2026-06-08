"""Harmonize outcome labels in poolable AUTO apps (PILOT).

The engine pools trials by realData outcome `shortLabel`. AUTO apps tag every
outcome "MACE", so all endpoints pool as one (invalid). This relabels each
outcome's shortLabel with a per-cluster key (fuzzy clustering from
analyze_poolability), so genuinely-matching endpoints pool and distinct ones
separate. Also:
  - state.selectedOutcome "MACE" -> "default" (valid resolved key)
  - neutralizes the visible cardiovascular MACE strings (label / narrative /
    NNT) that are wrong for a non-cardiac topic

Display labels come from the outcome `title` (via _derivedOutcomeMap), so the
new shortLabel keys are internal join keys and never shown.

Usage:
    python scripts/harmonize_outcomes.py FILE.html [FILE2 ...] [--dry-run]
"""
from __future__ import annotations
import argparse, io, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import analyze_poolability as ap  # noqa: E402

if hasattr(sys.stdout, "buffer") and getattr(sys.stdout, "encoding", "").lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

THRESH = 0.5

# Replace the shortLabel value only, keyed by the outcome's title.
_RELABEL_RE = re.compile(
    r"(\{shortLabel:(['\"]))MACE(\2,\s*title:(['\"])(?P<title>(?:\\.|(?!\4).)*)\4)")


def _slug(title):
    t = re.sub(r"\(primary\)\s*$", "", title)
    s = re.sub(r"[^A-Za-z0-9]", "", t.title())[:24]
    return s or "Outcome"


def assign_keys(outcomes, clusters):
    used = set()
    title_to_key = {}
    for cl in clusters:
        titles = [outcomes[i]["title"] for i in cl]
        # prefer a distinctive salient acronym shared in the cluster
        key = None
        sal = set()
        for i in cl:
            sal |= ap.salient_tokens(outcomes[i]["title"])
        for a in sorted(sal):
            cand = a.upper()
            if cand not in used:
                key = cand
                break
        if key is None:
            base = _slug(min(titles, key=len))
            key = base
            n = 2
            while key in used:
                key = f"{base}{n}"
                n += 1
        used.add(key)
        for t in titles:
            title_to_key[t] = key
    return title_to_key


def harmonize(html):
    pairs = ap.extract_trial_outcomes(html)
    outcomes = [o for _, o in pairs]
    if not outcomes:
        return html, {"changed": False, "reason": "no outcomes"}
    clusters = ap.cluster_outcomes(outcomes, THRESH)
    title_to_key = assign_keys(outcomes, clusters)

    def repl(m):
        key = title_to_key.get(m.group("title"))
        if not key:
            return m.group(0)
        return m.group(1) + key + m.group(3)

    new, n = _RELABEL_RE.subn(repl, html)

    # state default + visible cardiovascular strings
    new = new.replace('selectedOutcome:"MACE"', 'selectedOutcome:"default"')
    new = new.replace("Primary MACE Result", "Primary Result")
    new = new.replace(" (MACE)", "")
    new = new.replace("prevent 1 MACE event", "prevent 1 event")

    # build a small report: per-key trial count (simulated pooling)
    tids_by_key = {}
    for (tid, o) in pairs:
        k = title_to_key.get(o["title"], "?")
        tids_by_key.setdefault(k, set()).add(tid)
    pooled = {k: len(v) for k, v in tids_by_key.items()}
    return new, {"changed": n > 0, "relabeled": n, "n_outcomes": len(outcomes),
                 "n_trials": len({t for t, _ in pairs}), "pooled_k": pooled}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("files", nargs="+")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()
    for f in args.files:
        html = io.open(f, encoding="utf-8", errors="replace").read()
        new, rep = harmonize(html)
        name = os.path.basename(f)
        if not rep["changed"]:
            print(f"[skip] {name}: {rep.get('reason','no change')}")
            continue
        maxk = max(rep["pooled_k"].values()) if rep["pooled_k"] else 0
        print(f"[{'DRY' if args.dry_run else 'OK'}] {name}: relabeled {rep['relabeled']} "
              f"outcomes -> {len(rep['pooled_k'])} keys, max pooled k={maxk}")
        for k, n in sorted(rep["pooled_k"].items(), key=lambda x: -x[1]):
            print(f"       k={n}  {k}")
        if not args.dry_run:
            io.open(f, "w", encoding="utf-8", newline="").write(new)


if __name__ == "__main__":
    main()
