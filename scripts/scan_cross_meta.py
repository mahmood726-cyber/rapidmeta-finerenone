"""Cross-meta contamination gate.

scan_narrative_leftover.py catches dupilumab/COPD BASE-template leftover.
This catches a different failure: one audit-first topic's trial data (NCTs)
bleeding into ANOTHER topic's dashboard ("data from across metas by mistake").

For each VIABLE topic:
  expected_ncts = NCTs of trials that pass all gates (the exact set
                  bulk_clone_audit_first.build_config injects).
For its <STEM>_FULL_REVIEW.html:
  found_ncts    = every NCT\\d{8} literal in the file.
Violation = a found NCT not in this topic's expected set. Such an NCT is
either base leftover (NCT03930732/NCT04456673 — also caught by the
leftover scanner) or, worse, an NCT whose rightful owner is a DIFFERENT
topic (true cross-meta bleed) — reported with the owning topic.

Exit 0 = clean, 1 = contamination, 2 = usage error.
"""
from __future__ import annotations
import glob, io, json, os, re, sys

if hasattr(sys.stdout, "buffer") and getattr(sys.stdout, "encoding", "").lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOPICS = os.path.join(HERE, "outputs", "new_topics")
NCT_RE = re.compile(r"NCT\d{8}")
# Base-template trial NCTs (BOREAS / NOTUS) — never legitimate in any clone.
BASE_NCTS = {"NCT03930732", "NCT04456673"}

# Cross-meta bleed only matters in the ACTIVE per-topic analysis data that
# clone_dashboard.py rewrites — NOT in shared engine scaffold (alias maps,
# code comments, UI placeholders, special-case logic) that is identical in
# every RapidMeta dashboard incl. the ~900 flagships by design. Extract NCTs
# only from: AUTO_INCLUDE_TRIAL_IDS set, nctAcronyms map, realData block.


def _analysis_ncts(src: str) -> set:
    found = set()
    m = re.search(r"AUTO_INCLUDE_TRIAL_IDS\s*=\s*new\s+Set\(\[(.*?)\]\)", src, re.DOTALL)
    if m:
        found |= set(NCT_RE.findall(m.group(1)))
    m = re.search(r"nctAcronyms:\s*\{(.*?)\}", src, re.DOTALL)
    if m:
        found |= set(NCT_RE.findall(m.group(1)))
    i = src.find("realData: {")
    if i >= 0:
        brace = src.find("{", i)
        depth = 0
        for j in range(brace, len(src)):
            c = src[j]
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    found |= set(NCT_RE.findall(src[brace:j + 1]))
                    break
    return found


def _expected(doc):
    """NCTs build_config injects: trials where every gate passes."""
    out = set()
    for t in doc.get("trials", []):
        if not all((t.get("gates") or {}).values()):
            continue
        nct = (t.get("extracted") or {}).get("nct")
        if nct:
            out.add(nct)
    return out


def main():
    topic_files = sorted(glob.glob(os.path.join(TOPICS, "*.json")))
    expected_by_stem = {}
    owner_of_nct = {}        # nct -> set(stems that legitimately own it)
    for p in topic_files:
        try:
            doc = json.loads(io.open(p, encoding="utf-8", errors="replace").read())
        except Exception:
            continue
        # Reference set for EVERY topic with >=1 gate-passing trial (bulk now
        # builds NON_VIABLE-with-data too). _expected() is verdict-agnostic.
        stem = doc.get("topic", {}).get("stem")
        if not stem:
            continue
        exp = _expected(doc)
        expected_by_stem[stem] = exp
        for n in exp:
            owner_of_nct.setdefault(n, set()).add(stem)

    htmls = sorted(glob.glob(os.path.join(HERE, "*_FULL_REVIEW.html")))
    clean = bad = 0
    violations = []
    for h in htmls:
        stem = os.path.basename(h)[:-len("_FULL_REVIEW.html")]
        exp = expected_by_stem.get(stem)
        if exp is None:
            # No matching topic JSON at all -> genuine orphan.
            violations.append((stem, "ORPHAN", "no matching topic JSON"))
            bad += 1
            continue
        src = io.open(h, encoding="utf-8", errors="replace").read()
        found = _analysis_ncts(src)   # active per-topic data only, not engine scaffold
        foreign = found - exp
        if not foreign:
            clean += 1
            continue
        bad += 1
        detail = []
        for n in sorted(foreign):
            if n in BASE_NCTS:
                detail.append(f"{n}(BASE-leftover)")
            elif n in owner_of_nct:
                detail.append(f"{n}(owned by {','.join(sorted(owner_of_nct[n]))})")
            else:
                detail.append(f"{n}(unknown-origin)")
        violations.append((stem, "FOREIGN_NCT", "; ".join(detail)))

    print(f"=== Cross-meta scan: {clean} CLEAN, {bad} CONTAMINATED (of {len(htmls)}) ===")
    for stem, kind, det in violations[:40]:
        print(f"  [{kind}] {stem}: {det[:160]}")
    if bad:
        log = os.path.join(HERE, "outputs", "_cross_meta_violations.log")
        io.open(log, "w", encoding="utf-8").write(
            "\n".join(f"{s}\t{k}\t{d}" for s, k, d in violations))
        print(f"  full list -> {log}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
