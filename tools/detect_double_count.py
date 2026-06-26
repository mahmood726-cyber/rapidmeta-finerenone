"""detect_double_count.py — portfolio detector for shared-control double-counting
in RapidMeta *_REVIEW.html dashboards.

The bug: a multi-arm trial (e.g. a dose-finding RCT with two intervention doses
vs ONE shared placebo) is entered as >=2 separate realData entries, each carrying
the FULL control cE/cN. Naive pairwise pooling then counts the control group twice,
inflating precision. Correct fix: combine the intervention arms into a single
comparison vs the single control (Cochrane Handbook 23.3.4), or split the control
evenly, or run NMA.

This script is DETECTION ONLY (read-only). It never writes to a dashboard.

Signals (ranked), computed over NON-excluded realData entries within each app:
  HIGH dup_nct    : same 8-digit NCT in >=2 entry keys
  HIGH dup_name   : identical trial name in >=2 entries
  MED  arm_base   : same name-base (dose/arm suffix stripped) in >=2 entries
                    AND those entries share an identical (cE,cN) control cell
  LOW  shared_ctrl: identical (cE,cN), cN>0, in >=2 entries with DIFFERENT names

Usage:
  python detect_double_count.py --root C:/Projects --out audit.json
"""
from __future__ import annotations
import argparse, io, json, os, re, sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REALDATA_RE = re.compile(r"realData\s*[:=]\s*\{")
# entry key: quoted "FOO:NCT..." or bare NCT12345678, followed by :{
KEY_RE = re.compile(r'(?:"([^"]+)"|\b(NCT\d{8})\b)\s*:\s*\{')
NUM = r'(-?\d+(?:\.\d+)?)'
NAME_RE = re.compile(r'name\s*:\s*"([^"]*)"')
F_RE = {k: re.compile(rf'\b{k}\s*:\s*{NUM}') for k in ("tE", "tN", "cE", "cN")}
GROUP_RE = re.compile(r'group\s*:\s*"([^"]*)"')
NCT8 = re.compile(r'NCT\d{8}')
# strip a trailing dose/arm token to get a name "base"
ARM_SUFFIX = re.compile(
    r'[\s\(\-_/]*('
    r'\d+(?:\.\d+)?\s?mg(?:/day|/d)?|'
    r'(?:low|high|mid|medium)[\s-]?dose|'
    r'\d+\s?(?:mcg|µg|ug|units?|mL)|'
    r'arm\s?[a-z0-9]|q\dw|once[\s-]?(?:daily|weekly)|bid|tid|od'
    r')\s*\)?\s*$', re.I)
EXCL_HINT = re.compile(r'NULL|EXCL|DROP|DUP|REMOV', re.I)


def find_block(text, open_idx):
    depth = 0
    for j in range(open_idx, min(len(text), open_idx + 4_000_000)):
        c = text[j]
        if c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0:
                return j
    return -1


def parse_entries(text):
    m = REALDATA_RE.search(text)
    if not m:
        return []
    brace = m.end() - 1
    end = find_block(text, brace)
    if end < 0:
        return []
    block = text[brace:end + 1]
    out = []
    for km in KEY_RE.finditer(block):
        key = km.group(1) or km.group(2)
        eb = block.find('{', km.end() - 1)
        ee = find_block(block, eb)
        if ee < 0:
            continue
        body = block[eb:ee + 1]
        # only treat as a trial entry if it has the arm fields
        vals = {}
        ok = True
        for k, rx in F_RE.items():
            mm = rx.search(body)
            if not mm:
                ok = False
                break
            vals[k] = float(mm.group(1))
        if not ok:
            continue
        nm = NAME_RE.search(body)
        gm = GROUP_RE.search(body)
        excluded = bool(EXCL_HINT.search(key))
        out.append({
            "key": key,
            "name": nm.group(1) if nm else "",
            "group": gm.group(1) if gm else "",
            "nct": (NCT8.search(key).group(0) if NCT8.search(key)
                    else (NCT8.search(body).group(0) if NCT8.search(body) else "")),
            "excluded": excluded,
            **{k: vals[k] for k in ("tE", "tN", "cE", "cN")},
        })
    return out


def base_name(n):
    prev = None
    s = n.strip()
    while s != prev:
        prev = s
        s = ARM_SUFFIX.sub('', s).strip()
    return s.lower()


def analyse(entries):
    inc = [e for e in entries if not e["excluded"]]
    findings = []
    # dup_nct
    by_nct = {}
    for e in inc:
        if e["nct"]:
            by_nct.setdefault(e["nct"], []).append(e)
    for nct, es in by_nct.items():
        if len(es) >= 2:
            findings.append(("dup_nct", nct, [e["key"] for e in es]))
    # dup_name
    by_name = {}
    for e in inc:
        if e["name"]:
            by_name.setdefault(e["name"], []).append(e)
    for nm, es in by_name.items():
        if len(es) >= 2:
            findings.append(("dup_name", nm, [e["key"] for e in es]))
    # shared control cell among >=2 entries
    by_ctrl = {}
    for e in inc:
        if e["cN"] > 0:
            by_ctrl.setdefault((e["cE"], e["cN"]), []).append(e)
    for (ce, cn), es in by_ctrl.items():
        if len(es) < 2:
            continue
        names = {e["name"] for e in es}
        bases = {base_name(e["name"]) for e in es if e["name"]}
        # different treatment cells (else it's a true full duplicate, caught above)
        tcells = {(e["tE"], e["tN"]) for e in es}
        if len(tcells) < 2:
            continue
        if len(bases) == 1 and bases != {""}:
            sev = "arm_base"
        else:
            sev = "shared_ctrl"
        findings.append((sev, f"cE={ce:g},cN={cn:g}",
                         [f'{e["name"]}|t={e["tE"]:g}/{e["tN"]:g}' for e in es]))
    # name-base collision INDEPENDENT of control match: catches dose-arm splits
    # (e.g. "DRUG 10 mg" / "DRUG 20 mg") even when the control cell was entered
    # with slightly different numbers per arm.
    GENERIC = {"", "cap", "study", "trial", "phase iii", "rct", "main"}
    by_base = {}
    for e in inc:
        b = base_name(e["name"])
        if b and b not in GENERIC and len(b) >= 4:
            by_base.setdefault(b, []).append(e)
    seen_keys = {tuple(sorted(f[2])) for f in findings}
    for b, es in by_base.items():
        if len(es) >= 2 and len({e["name"] for e in es}) >= 2:
            arms = sorted(f'{e["name"]}|t={e["tE"]:g}/{e["tN"]:g}|c={e["cE"]:g}/{e["cN"]:g}'
                          for e in es)
            if tuple(sorted(e["name"] for e in es)) not in seen_keys:
                findings.append(("arm_namebase", b, arms))
    return findings, len(inc), len(entries) - len(inc)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="C:/Projects")
    ap.add_argument("--out", default="double_count_audit.json")
    a = ap.parse_args()
    files = []
    for dp, dn, fn in os.walk(a.root):
        if any(x in dp for x in (os.sep + ".git", "node_modules", "__pycache__")):
            continue
        for f in fn:
            if f.endswith("_REVIEW.html"):
                files.append(os.path.join(dp, f))
    files.sort()
    results = []
    rank = {"dup_nct": 3, "dup_name": 3, "arm_base": 2, "arm_namebase": 2,
            "shared_ctrl": 1}
    for i, p in enumerate(files):
        try:
            if os.path.getsize(p) > 30_000_000:
                print(f"  SKIP (huge): {p}", flush=True)
                continue
            s = open(p, encoding="utf-8", errors="replace").read()
        except (OSError, MemoryError):
            print(f"  SKIP (read err): {p}", flush=True)
            continue
        ents = parse_entries(s)
        if not ents:
            continue
        finds, ninc, nexc = analyse(ents)
        if finds:
            top = max(rank[f[0]] for f in finds)
            results.append({
                "file": p, "n_included": ninc, "n_excluded": nexc,
                "max_rank": top,
                "findings": [{"type": t, "ctrl_or_id": k, "arms": arms}
                             for (t, k, arms) in finds],
            })
        if (i + 1) % 200 == 0:
            print(f"  scanned {i+1}/{len(files)} ... {len(results)} flagged", flush=True)
    results.sort(key=lambda r: (-r["max_rank"], r["file"]))
    json.dump({"scanned": len(files), "flagged": len(results),
               "results": results}, open(a.out, "w", encoding="utf-8"), indent=1)
    from collections import Counter
    c = Counter()
    for r in results:
        for f in r["findings"]:
            c[f["type"]] += 1
    print(f"\nscanned {len(files)} | flagged apps {len(results)}")
    print("findings by type:", dict(c))
    print("HIGH-severity apps (dup_nct/dup_name):",
          sum(1 for r in results if r["max_rank"] == 3))
    print("MED (arm_base):", sum(1 for r in results if r["max_rank"] == 2))
    print("LOW (shared_ctrl only):", sum(1 for r in results if r["max_rank"] == 1))
    print("out ->", a.out)


if __name__ == "__main__":
    main()
