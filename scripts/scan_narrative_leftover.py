"""Fail-closed scanner: detect dupilumab/COPD base-template narrative leftover
in a cloned *_FULL_REVIEW.html.

The bulk-clone pipeline templates DUPILUMAB_COPD_REVIEW.html for arbitrary
audit-first topics. clone_dashboard.py swaps structured data blocks, but
hand-written narrative prose, hardcoded benchmarks, export filenames and the
localStorage key can leak the base drug/condition. This scanner is the ship
gate: a clone that still contains a base-specific token is QUARANTINED, never
shipped.

Token policy
------------
HARD (always forbidden — no audit-first topic is ever about these):
    dupilumab, Dupilumab, DUPILUMAB, BOREAS, NOTUS,
    NCT03930732, NCT04456673,
    dupilumab_copd, dupi_copd, rapid_meta_dupilumab_copd

SOFT (forbidden UNLESS the topic legitimately uses it):
    COPD  -> allowed only if the topic condition contains "copd"

Usage
-----
    python scripts/scan_narrative_leftover.py FILE.html [--topic STEM_or_json]
    python scripts/scan_narrative_leftover.py --dir . --batch     # scan all *_FULL_REVIEW.html

Exit 0 = clean, 1 = leftover found (fail-closed), 2 = usage error.
"""
from __future__ import annotations
import argparse, glob, io, json, os, re, sys

if hasattr(sys.stdout, "buffer") and getattr(sys.stdout, "encoding", "").lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOPICS_DIR = os.path.join(HERE, "outputs", "new_topics")

# HARD: base-template-specific tokens NEVER legitimate for any topic
# (compound localStorage/export keys + the base trial acronyms/NCTs).
HARD_TOKENS = [
    "BOREAS", "NOTUS",
    "NCT03930732", "NCT04456673",
    "dupilumab_copd", "dupi_copd", "rapid_meta_dupilumab_copd",
]
# SOFT: forbidden UNLESS the topic legitimately uses the token. "dupilumab"
# is a base leftover for a tezepelumab topic but the CORRECT drug for a
# DUPILUMAB_AD topic — same logic as COPD for a COPD topic.
SOFT_TOKENS = {
    "COPD": "copd",
    "dupilumab": "dupilumab",
    "Dupilumab": "dupilumab",
    "DUPILUMAB": "dupilumab",
}


def _read(path: str) -> str:
    return io.open(path, "r", encoding="utf-8", errors="replace").read()


def _topic_condition(topic_ref: str | None) -> str:
    """Return lowercased condition text for the topic, or '' if unknown."""
    if not topic_ref:
        return ""
    p = topic_ref
    if not os.path.isfile(p):
        cand = os.path.join(TOPICS_DIR, topic_ref)
        if os.path.isfile(cand):
            p = cand
        elif os.path.isfile(cand + ".json"):
            p = cand + ".json"
        else:
            stem = os.path.basename(topic_ref).replace(".json", "")
            cand = os.path.join(TOPICS_DIR, f"{stem}.json")
            p = cand if os.path.isfile(cand) else ""
    if not p or not os.path.isfile(p):
        return ""
    try:
        doc = json.loads(io.open(p, encoding="utf-8", errors="replace").read())
    except Exception:
        return ""
    topic = doc.get("topic", {})
    parts = list(topic.get("condition_patterns") or [])
    parts += list(topic.get("drug_patterns") or [])  # SOFT dupilumab allow-check
    parts.append(topic.get("name", ""))
    parts.append(topic.get("stem", ""))
    return " ".join(parts).lower()


def scan(html_path: str, topic_ref: str | None = None):
    """Return list of (token, char_offset, context) violations. Empty == clean."""
    src = _read(html_path)
    cond = _topic_condition(topic_ref)
    violations = []

    for tok in HARD_TOKENS:
        for m in re.finditer(re.escape(tok), src):
            s = max(0, m.start() - 70)
            ctx = src[s:m.start() + len(tok) + 50].replace("\n", " ")
            violations.append((tok, m.start(), ctx))

    for tok, allow_if in SOFT_TOKENS.items():
        if allow_if in cond:
            continue  # topic legitimately uses this token
        for m in re.finditer(re.escape(tok), src):
            s = max(0, m.start() - 70)
            ctx = src[s:m.start() + len(tok) + 50].replace("\n", " ")
            violations.append((tok, m.start(), ctx))

    return violations


def _scan_one(html_path: str, topic_ref: str | None) -> bool:
    v = scan(html_path, topic_ref)
    name = os.path.basename(html_path)
    if not v:
        print(f"  [CLEAN] {name}")
        return True
    print(f"  [LEFTOVER] {name}  ({len(v)} hits)")
    seen = {}
    for tok, off, ctx in v:
        seen.setdefault(tok, 0)
        if seen[tok] < 3:  # cap context spam per token
            print(f"      {tok} @ {off}: ...{ctx[:110]}...")
        seen[tok] += 1
    summary = ", ".join(f"{t}x{c}" for t, c in sorted(seen.items()))
    print(f"      => {summary}")
    return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("html", nargs="?", help="path to a *_FULL_REVIEW.html")
    ap.add_argument("--topic", help="topic stem or json (resolves allowed SOFT tokens)")
    ap.add_argument("--dir", help="scan all *_FULL_REVIEW.html in this dir")
    ap.add_argument("--batch", action="store_true",
                    help="with --dir: pair each html with outputs/new_topics/<STEM>.json")
    args = ap.parse_args()

    if args.dir:
        files = sorted(glob.glob(os.path.join(args.dir, "*_FULL_REVIEW.html")))
        if not files:
            print(f"No *_FULL_REVIEW.html in {args.dir}", file=sys.stderr)
            return 2
        clean = bad = 0
        bad_files = []
        for f in files:
            stem = os.path.basename(f).replace("_FULL_REVIEW.html", "")
            ref = stem if args.batch else None
            if _scan_one(f, ref):
                clean += 1
            else:
                bad += 1
                bad_files.append(os.path.basename(f))
        print(f"\n=== Scanner: {clean} CLEAN, {bad} LEFTOVER (of {len(files)}) ===")
        if bad_files:
            print("Quarantine candidates: " + ", ".join(bad_files[:30])
                  + (" ..." if len(bad_files) > 30 else ""))
        return 1 if bad else 0

    if not args.html:
        print("usage: scan_narrative_leftover.py FILE.html [--topic STEM] "
              "| --dir DIR [--batch]", file=sys.stderr)
        return 2
    if not os.path.isfile(args.html):
        print(f"not a file: {args.html}", file=sys.stderr)
        return 2
    return 0 if _scan_one(args.html, args.topic) else 1


if __name__ == "__main__":
    sys.exit(main())
