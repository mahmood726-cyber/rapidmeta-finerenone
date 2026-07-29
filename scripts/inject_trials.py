"""Injection-only trial-set corrector for RapidMeta AUTO apps.

Surgically inserts verified new trial entries into an app's EXISTING realData
block, preserving every other byte of the live HTML (SOUL baselines, PMID fixes,
i18n, poolability edits, etc.). Does NOT rebuild from a template and does NOT
touch existing trial entries.

Mechanism:
  1. Read the app HTML as UTF-8 with newline='' (CRLF preserved byte-for-byte).
  2. Locate the `realData: { ... }` object via regex + depth-balanced brace scan
     (same delimiter logic as scripts/clone_dashboard.py).
  3. Brace-scan the top-level `<key>: { ... }` entries; record keys + spans and
     the exact inter-entry separator string actually used in this file.
  4. For each addition whose KEY is NOT already present, render a minified JS
     entry matching the app's existing schema and insert it immediately after the
     last existing entry using the observed separator.
  5. Write back with newline='' so only the inserted bytes differ.

Truth-first: additions are provided as verified data (see additions JSON). This
script fabricates nothing; it only formats + splices what it is given.

Usage:
  python scripts/inject_trials.py <app.html> <additions.json> [--apply]
Without --apply it is a DRY-RUN (prints plan + writes nothing).
"""
from __future__ import annotations
import argparse, json, re, sys, io
from pathlib import Path

if hasattr(sys.stdout, "buffer") and getattr(sys.stdout, "encoding", "").lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


def _brace_span(s: str, open_idx: int) -> int:
    """Return index of the '}' matching the '{' at/after open_idx."""
    depth = 0
    started = False
    for j in range(open_idx, len(s)):
        c = s[j]
        if c == '{':
            depth += 1
            started = True
        elif c == '}':
            depth -= 1
            if started and depth == 0:
                return j
    raise ValueError("unbalanced braces")


def locate_realdata(src: str):
    m = re.search(r'realData\s*:\s*\{', src)
    if not m:
        raise SystemExit("realData block not found")
    brace = src.index('{', m.start())
    end = _brace_span(src, brace)   # index of the block-closing '}'
    return brace, end


# A realData key. Registry trials are keyed by NCT id; PRE-REGISTRY trials
# (CONSENSUS 1987, SOLVD, MERIT-HF, RALES, CIBIS, COPERNICUS, EMPHASIS, CARMEN)
# predate ClinicalTrials.gov and have no NCT. They are keyed by their published
# trial acronym instead. Keys may be bare or quoted (the AUTO template emits
# `"NCT01035255":{`, the older template emits `NCT01035255:{`).
ENTRY_KEY = re.compile(r'["\']?([A-Za-z][A-Za-z0-9_\-]{2,39})["\']?\s*:\s*\{')



_NCT_RE = re.compile(r"^NCT\d{8}$")
_NAME_KEY_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_\-]{2,39}$")


def entry_key(t: dict) -> str:
    """The realData key for one trial - IDENTIFIERS BY LOOKUP, NEVER RECALL.

    Registry-era trials keep their NCT id. Pre-registry trials (CONSENSUS 1987,
    SOLVD, MERIT-HF, RALES, CIBIS, COPERNICUS, EMPHASIS, CARMEN ...) have no NCT
    and are keyed by their published acronym, which MUST be backed by a PMID so
    the identity is checkable against the literature.

    Fails closed on the dangerous case: a key that merely LOOKS like a registry
    id but was not supplied as a real `nct` field is refused outright, so a
    fabricated NCT can never enter realData through this path.
    """
    nct = (t.get("nct") or "").strip()
    key = (t.get("key") or "").strip()
    if nct:
        if not _NCT_RE.match(nct):
            raise SystemExit(f"malformed NCT id {nct!r} for {t.get('name')!r} "
                             f"- expected NCT + 8 digits")
        if key and key != nct:
            raise SystemExit(f"conflicting key {key!r} vs nct {nct!r}")
        return nct
    if not key:
        raise SystemExit(f"trial {t.get('name')!r} has neither `nct` nor `key`")
    if key.upper().startswith("NCT"):
        raise SystemExit(f"key {key!r} imitates a registry id but no verified "
                         f"`nct` was supplied - refusing to invent an NCT")
    if not _NAME_KEY_RE.match(key):
        raise SystemExit(f"key {key!r} is not a usable trial acronym")
    pmid = str(t.get("pmid") or "").strip()
    if not pmid.isdigit():
        raise SystemExit(f"pre-registry trial {key!r} needs a numeric `pmid` so "
                         f"its identity is checkable (got {t.get('pmid')!r})")
    return key


def scan_entries(src: str, brace: int, end: int):
    """Return list of (key, start_idx, close_idx) for each top-level entry."""
    entries = []
    i = brace + 1
    for mk in ENTRY_KEY.finditer(src[brace:end + 1]):
        key = mk.group(1)
        abs_open = brace + mk.end() - 1          # index of that entry's '{'
        close = _brace_span(src, abs_open)
        entries.append((key, brace + mk.start(), close))
    return entries


def js_str(s: str) -> str:
    return '"' + s.replace('\\', '\\\\').replace('"', '\\"') + '"'


def num(x):
    return "null" if x is None else (str(x))


def render_outcome(o: dict) -> str:
    parts = [
        f'shortLabel:{js_str(o["shortLabel"])}',
        f'title:{js_str(o["title"])}',
        f'type:{js_str(o["type"])}',
        f'tE:{num(o["tE"])}', f'cE:{num(o["cE"])}',
        f'tN:{num(o["tN"])}', f'cN:{num(o["cN"])}',
        f'matchScore:{num(o.get("matchScore",100))}',
        f'estimandType:{js_str(o.get("estimandType","HR"))}',
    ]
    if o.get("pubHR") is not None:
        parts += [f'pubHR:{num(o["pubHR"])}',
                  f'pubHR_LCI:{num(o["pubHR_LCI"])}',
                  f'pubHR_UCI:{num(o["pubHR_UCI"])}']
    return '{' + ','.join(parts) + '}'


def render_evidence(e: dict) -> str:
    hl = ','.join(js_str(h) for h in e.get("highlights", []))
    return ('{' + f'label:{js_str(e["label"])},source:{js_str(e["source"])},'
            f'text:{js_str(e["text"])},highlights:[{hl}]' + '}')


def render_entry(t: dict) -> str:
    """Render one NCT-keyed realData entry, matching the app schema exactly."""
    outs = ','.join(render_outcome(o) for o in t["allOutcomes"])
    evs = ','.join(render_evidence(e) for e in t.get("evidence", []))
    rob = ','.join(js_str(r) for r in t.get("rob", ["low"] * 5))
    fields = [
        f'name:{js_str(t["name"])}',
        f'pmid:{js_str(t["pmid"])}',
        f'phase:{js_str(t.get("phase","III"))}',
        f'year:{num(t["year"])}',
        f'tE:{num(t["tE"])}', f'tN:{num(t["tN"])}',
        f'cE:{num(t["cE"])}', f'cN:{num(t["cN"])}',
        f'group:{js_str(t["group"])}',
        f'publishedHR:{num(t["publishedHR"])}',
        f'hrLCI:{num(t["hrLCI"])}', f'hrUCI:{num(t["hrUCI"])}',
        f'pubHR:{num(t["publishedHR"])}',
        f'pubHR_LCI:{num(t["hrLCI"])}', f'pubHR_UCI:{num(t["hrUCI"])}',
        f'allOutcomes:[{outs}]',
        f'rob:[{rob}]',
        f'robSource:{js_str(t.get("robSource",""))}',
        f'snippet:{js_str(t["snippet"])}',
        f'sourceUrl:{js_str(t["sourceUrl"])}',
        f'ctgovUrl:{js_str(t.get("ctgovUrl", t["sourceUrl"]))}',
        f'evidence:[{evs}]',
    ]
    return f'"{entry_key(t)}":{{' + ','.join(fields) + '}'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("app")
    ap.add_argument("additions")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    app = Path(args.app)
    src = app.read_text(encoding="utf-8", newline="")
    adds = json.loads(Path(args.additions).read_text(encoding="utf-8"))

    brace, end = locate_realdata(src)
    entries = scan_entries(src, brace, end)
    existing = [k for k, _, _ in entries]
    print(f"[{app.name}] existing realData trials ({len(existing)}): {existing}")

    if not entries:
        raise SystemExit("no existing entries to anchor insertion — aborting (would need template)")

    # Observed inter-entry separator (bytes between one entry's '}' and the next
    # entry's key). Falls back to ',\r\n' matching the file's CRLF convention.
    if len(entries) >= 2:
        sep = src[entries[-2][2] + 1: entries[-1][1]]
    else:
        sep = ',\r\n                '
    # Whitespace between last entry's '}' and the block-closing '}' (preserved).
    last_close = entries[-1][2]

    for t in adds:
        entry_key(t)                       # validate every key up-front
    to_add = [t for t in adds if entry_key(t) not in existing]
    skipped = [entry_key(t) for t in adds if entry_key(t) in existing]
    if skipped:
        print(f"  already present, skipping: {skipped}")
    if not to_add:
        print("  nothing to add.")
        return
    print(f"  adding: {[entry_key(t) for t in to_add]}")

    rendered = sep.join(render_entry(t) for t in to_add)
    insertion = sep + rendered
    # non-ASCII guard on our own additions
    non_ascii = [(i, repr(c)) for i, c in enumerate(insertion) if ord(c) > 127]
    if non_ascii:
        raise SystemExit(f"NON-ASCII in injected content (aborting): {non_ascii[:5]}")
    if any(c in insertion for c in "‘’“”"):
        raise SystemExit("curly quote in injected content (aborting)")

    new_src = src[:last_close + 1] + insertion + src[last_close + 1:]

    # sanity: only-additive — original must be a subsequence boundary preserved
    assert new_src[:last_close + 1] == src[:last_close + 1], "prefix changed!"
    assert new_src[last_close + 1 + len(insertion):] == src[last_close + 1:], "suffix changed!"
    print(f"  insertion length: {len(insertion)} chars; "
          f"file {len(src)} -> {len(new_src)} (+{len(new_src)-len(src)})")

    # --- Also add the new trial KEYS to AUTO_INCLUDE_TRIAL_IDS so they are actually
    #     pooled by default (a trial in realData but absent from this Set is
    #     catalogued but not auto-included). Purely additive: append before ']'.
    sm = re.search(r'AUTO_INCLUDE_TRIAL_IDS\s*=\s*new\s+Set\(\[([^\]]*)\]\)', new_src)
    if not sm:
        raise SystemExit("AUTO_INCLUDE_TRIAL_IDS Set not found — aborting")
    set_body = sm.group(1)
    present_ids = set(re.findall(r'["\']([A-Za-z][A-Za-z0-9_\-]{2,39})["\']', set_body))
    set_adds = [entry_key(t) for t in to_add if entry_key(t) not in present_ids]
    if set_adds:
        add_str = "".join(f',"{n}"' for n in set_adds)
        insert_at = sm.start(1) + len(set_body)          # just before the ']'
        before_set_len = len(new_src)
        new_src = new_src[:insert_at] + add_str + new_src[insert_at:]
        print(f"  AUTO_INCLUDE_TRIAL_IDS += {set_adds} (+{len(add_str)} chars)")
    else:
        print("  AUTO_INCLUDE_TRIAL_IDS already contains all added NCTs")

    if args.apply:
        app.write_text(new_src, encoding="utf-8", newline="")
        print("  APPLIED.")
    else:
        print("  DRY-RUN (no write). Re-run with --apply to write.")


if __name__ == "__main__":
    main()
