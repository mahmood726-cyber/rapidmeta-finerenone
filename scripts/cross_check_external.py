"""
External cross-check: extracted pooled estimates vs. published meta-analysis claims.

Sample: 30 reviews with realData (>=3 trials with valid 2x2 counts) and no
P0 events-over-N defects (codes T04 in audit_data_integrity.py output).

For each review:
  1. Extract published-meta claim from the landing-page card (preferred) OR from
     the inline PUBLISHED_META_BENCHMARKS array embedded in the review HTML.
  2. Re-pool the per-trial 2x2 data parsed from the review HTML's `realData`
     block using random-effects (DerSimonian-Laird) on log-OR.
  3. Compare on the log scale; flag |Delta log| > 0.10.

This script is self-contained and does NOT depend on outputs/extraction_audit/
which is regenerated/cleaned by other workflows. We parse the per-trial 2x2
counts straight out of the HTML JS literal.

Output: tight markdown to stdout.
"""

from __future__ import annotations

import io
import math
import re
import sys
from pathlib import Path

# Script lives at <repo>/scripts/, so parents[1] is the repo root
# (Sentinel P0-hardcoded-local-path compliance).
ROOT = Path(__file__).resolve().parents[1]
LANDING = ROOT / "index.html"

try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
except Exception:
    pass

# Two SGLT2i HF benchmarks (Vaduganathan / Jhund 2022) appear bled into many
# unrelated review HTMLs. Treat both as placeholders.
_PLACEHOLDER_TUPLES = {
    ("HR", 0.77, 0.72, 0.82, 5),  # Vaduganathan
    ("HR", 0.78, 0.72, 0.84, 5),  # Jhund
}


def is_placeholder(claim) -> bool:
    if claim is None:
        return False
    key = (
        claim["measure"],
        round(claim["est"], 2),
        round(claim["lci"], 2),
        round(claim["uci"], 2),
        claim.get("k"),
    )
    return key in _PLACEHOLDER_TUPLES


# --------- Landing-card claim extraction ----------------------------------

LANDING_RE = re.compile(
    r'href="([A-Z0-9_]+_REVIEW)\.html".*?Published:\s*'
    r'(HR|OR|RR)\s*~?\s*(\d+\.\d+)\s*\(([\d.]+)[–\-]+([\d.]+)\),\s*k=(\d+)',
    re.IGNORECASE,
)


def load_landing_claims():
    text = LANDING.read_text(encoding="utf-8", errors="replace")
    claims = {}
    for m in LANDING_RE.finditer(text):
        stem = m.group(1)
        claims[stem] = {
            "source": "landing",
            "measure": m.group(2).upper(),
            "est": float(m.group(3)),
            "lci": float(m.group(4)),
            "uci": float(m.group(5)),
            "k": int(m.group(6)),
        }
    return claims


# --------- Inline PUBLISHED_META_BENCHMARKS extraction --------------------

INLINE_RE = re.compile(
    r"\{\s*label\s*:\s*['\"][^\n]*?['\"]\s*,"
    r"[^{}]*?measure\s*:\s*['\"](HR|OR|RR)['\"]\s*,"
    r"\s*estimate\s*:\s*([\d.]+)\s*,"
    r"\s*lci\s*:\s*([\d.]+)\s*,"
    r"\s*uci\s*:\s*([\d.]+)"
    r"(?:[^{}]*?k\s*:\s*(\d+))?",
    re.IGNORECASE,
)


def extract_inline_claim(text):
    anchor = text.find("PUBLISHED_META_BENCHMARKS")
    if anchor == -1:
        return None
    region = text[anchor : anchor + 12000]
    matches = list(INLINE_RE.finditer(region))
    if not matches:
        return None

    def to_claim(m):
        return {
            "source": "inline",
            "measure": m.group(1).upper(),
            "est": float(m.group(2)),
            "lci": float(m.group(3)),
            "uci": float(m.group(4)),
            "k": int(m.group(5)) if m.group(5) else None,
        }

    for m in matches:
        c = to_claim(m)
        if not is_placeholder(c):
            return c
    return to_claim(matches[0])


# --------- Per-trial 2x2 extraction direct from HTML ----------------------

# Match e.g.:
#   'NCT00643188': { ... tE: 51, tN: 179, cE: 82, cN: 184, ... },
# Tolerates other ordered fields and quoted values.
TRIAL_BLOCK_RE = re.compile(
    r"['\"]?(NCT\d{8})['\"]?\s*:\s*\{(?P<body>.*?)\},?\s*\n?\s*(?:['\"]?NCT\d{8}|\}\s*[,\];])",
    re.DOTALL,
)
COUNTS_RE = re.compile(
    r"tE\s*:\s*(\d+)\s*,\s*tN\s*:\s*(\d+)\s*,\s*cE\s*:\s*(\d+)\s*,\s*cN\s*:\s*(\d+)"
)


def parse_trials_from_html(text):
    """Return list of (nct, tE, tN, cE, cN) tuples extracted from the realData block.

    Uses a simpler approach: find the realData JS object body and grep for
    NCT-id followed by the canonical `tE:.., tN:.., cE:.., cN:..` pattern that
    sits on the same line in the review HTMLs (ABLATION_AF_REVIEW.html line 7124).
    """
    # Locate realData block
    m = re.search(r"realData\s*:\s*\{", text)
    if not m:
        return []
    start = m.end() - 1
    # We don't try to parse JS exactly -- the canonical pattern in this
    # codebase puts NCT and 4 counts on a single content line.
    block = text[start : start + 200_000]  # generous slice

    # Walk pattern: 'NCT....': {  ... tE: x, tN: y, cE: z, cN: w
    out = []
    nct_iter = re.finditer(
        r"['\"](NCT\d{8})['\"]\s*:\s*\{",
        block,
    )
    matches = list(nct_iter)
    for i, nm in enumerate(matches):
        nct = nm.group(1)
        seg_start = nm.end()
        seg_end = matches[i + 1].start() if i + 1 < len(matches) else seg_start + 8000
        seg = block[seg_start:seg_end]
        cm = COUNTS_RE.search(seg)
        if not cm:
            continue
        tE, tN, cE, cN = (int(cm.group(j)) for j in range(1, 5))
        if tN <= 0 or cN <= 0 or tE > tN or cE > cN or tE < 0 or cE < 0:
            continue
        out.append((nct, tE, tN, cE, cN))
    return out


# --------- P0 detection (events > N) -------------------------------------

def has_p0_events_over_n(trials):
    """Re-derive the T04 P0 finding from the per-trial counts."""
    for nct, tE, tN, cE, cN in trials:
        if tE > tN or cE > cN:
            return True
    return False


# --------- Pooling --------------------------------------------------------

def trial_logor(tE, tN, cE, cN):
    a, b, c, d = float(tE), float(tN - tE), float(cE), float(cN - cE)
    if min(a, b, c, d) == 0:
        a += 0.5
        b += 0.5
        c += 0.5
        d += 0.5
    if a <= 0 or b <= 0 or c <= 0 or d <= 0:
        return None, None
    log_or = math.log((a * d) / (b * c))
    var = 1 / a + 1 / b + 1 / c + 1 / d
    return log_or, var


def re_pool_dl(yi, vi):
    k = len(yi)
    if k == 0:
        return None
    wi_fe = [1 / v for v in vi]
    sw = sum(wi_fe)
    y_fe = sum(w * y for w, y in zip(wi_fe, yi)) / sw
    Q = sum(w * (y - y_fe) ** 2 for w, y in zip(wi_fe, yi))
    df = k - 1
    if df <= 0:
        tau2 = 0.0
    else:
        c = sw - sum(w * w for w in wi_fe) / sw
        tau2 = max(0.0, (Q - df) / c) if c > 0 else 0.0
    wi_re = [1 / (v + tau2) for v in vi]
    swr = sum(wi_re)
    y_re = sum(w * y for w, y in zip(wi_re, yi)) / swr
    se_re = math.sqrt(1 / swr)
    return {
        "k": k,
        "logOR": y_re,
        "se": se_re,
        "OR": math.exp(y_re),
        "lci": math.exp(y_re - 1.96 * se_re),
        "uci": math.exp(y_re + 1.96 * se_re),
        "tau2": tau2,
        "Q": Q,
    }


def repool_from_trials(trials):
    yi, vi = [], []
    for _, tE, tN, cE, cN in trials:
        y, v = trial_logor(tE, tN, cE, cN)
        if y is None:
            continue
        yi.append(y)
        vi.append(v)
    if len(yi) < 2:
        return None
    return re_pool_dl(yi, vi)


# --------- Classification -------------------------------------------------

def classify(claim, ours):
    if claim is None:
        return "no-claim", None
    delta_log = math.log(ours["OR"]) - math.log(claim["est"])
    if is_placeholder(claim) and claim.get("source") == "inline":
        return ("stale card text (Vaduganathan/Jhund SGLT2i placeholder bled into unrelated review)",
                delta_log)
    cm = claim["measure"]
    abs_d = abs(delta_log)
    if abs_d <= 0.10:
        return "converge", delta_log
    if cm == "HR":
        cause = "scale-mismatch (HR vs OR)"
    elif cm == "RR":
        cause = "scale-mismatch (RR vs OR)"
    else:
        cause = "OR-vs-OR -- investigate"
    if claim.get("k") and claim["k"] != ours["k"]:
        cause += f"; k differs ({claim['k']}->{ours['k']})"
    return cause, delta_log


# --------- Sample selection ----------------------------------------------

def all_zero_events(trials):
    return all(tE == 0 and cE == 0 for _, tE, _, cE, _ in trials)


def discover_reviews():
    """Return [(stem, html, trials, text)] for reviews with >=3 valid trials
    where at least one trial has events (>=1 event in either arm), so the
    binary 2x2 pool is meaningful. Excludes P0 events>N defects."""
    out = []
    for html in sorted(ROOT.glob("*_REVIEW.html")):
        # Skip backup files
        if ".pre_v16.bak" in html.name or ".bak" in html.name:
            continue
        try:
            text = html.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        trials = parse_trials_from_html(text)
        if len(trials) < 3:
            continue
        if has_p0_events_over_n(trials):
            continue
        # Skip continuous outcomes (MD): all-zero event counts means realData
        # encodes mean differences in effect-size fields, not 2x2 events.
        if all_zero_events(trials):
            continue
        stem = html.stem
        out.append((stem, html, trials, text))
    return out


# --------- Main -----------------------------------------------------------

def main():
    landing = load_landing_claims()
    discovered = discover_reviews()

    # Order reviews: those with landing-card claims first, then alphabetical.
    discovered.sort(key=lambda r: (0 if r[0] in landing else 1, r[0]))
    selected = discovered[:30]

    rows = []
    for stem, html, trials, text in selected:
        claim = landing.get(stem) or extract_inline_claim(text)
        ours = repool_from_trials(trials)
        if ours is None:
            rows.append({"stem": stem, "claim": claim, "ours": None,
                         "delta_log": None, "cause": "repool-failed"})
            continue
        cause, dlog = classify(claim, ours)
        rows.append({"stem": stem, "claim": claim, "ours": ours,
                     "delta_log": dlog, "cause": cause})

    # ----- Markdown output -----
    print("# External cross-check: extracted pooled estimates vs published claims")
    print()
    print(f"Sample: {len(rows)} reviews "
          f"(>= 3 valid trials in realData; tE<=tN & cE<=cN; landing-card claim "
          f"preferred over inline benchmark when both exist).")
    print()
    print("Pool method: random-effects DerSimonian-Laird on log-OR; "
          "Haldane 0.5 only when at least one cell is zero.")
    print()
    print("| Review | k | Claim (src/measure/est [lci-uci], k) | Our re-pool OR (95% CI), tau^2 | |dlog| | Suspected cause |")
    print("|---|---:|---|---|---:|---|")
    for r in rows:
        if r["ours"] is None:
            print(f"| {r['stem']} | - | - | repool failed | - | {r['cause']} |")
            continue
        o = r["ours"]
        c = r["claim"]
        if c:
            csrc = c["source"][0]
            ck = c.get("k") if c.get("k") is not None else "?"
            cstr = (f"[{csrc}] {c['measure']} {c['est']:.2f} "
                    f"({c['lci']:.2f}-{c['uci']:.2f}), k={ck}")
        else:
            cstr = "no claim text"
        ostr = f"OR {o['OR']:.2f} ({o['lci']:.2f}-{o['uci']:.2f}), tau2={o['tau2']:.3f}"
        d = f"{abs(r['delta_log']):.3f}" if r["delta_log"] is not None else "-"
        print(f"| {r['stem']} | {o['k']} | {cstr} | {ostr} | {d} | {r['cause']} |")

    converging = sum(1 for r in rows if r["cause"] == "converge")
    diverging_real = sum(
        1 for r in rows
        if r["delta_log"] is not None
        and r["cause"] not in ("converge", "no-claim", "repool-failed")
        and not r["cause"].startswith("stale card text")
    )
    placeholder = sum(1 for r in rows if r["cause"].startswith("stale card text"))
    no_claim = sum(1 for r in rows if r["cause"] == "no-claim")
    failed = sum(1 for r in rows if r["cause"] == "repool-failed")

    print()
    print("## Summary")
    print(f"- Converging (|dlog| <= 0.10): **{converging} / {len(rows)}**")
    print(f"- Diverging on real claim (|dlog| > 0.10, non-placeholder): **{diverging_real} / {len(rows)}**")
    print(f"- Inline-placeholder bleed (Vaduganathan/Jhund SGLT2i in unrelated review): **{placeholder} / {len(rows)}**")
    print(f"- Ambiguous (no-claim / repool-failed): **{no_claim + failed} / {len(rows)}**")
    print()

    real_div = [
        r for r in rows
        if r["delta_log"] is not None
        and r["cause"] not in ("converge",)
        and not r["cause"].startswith("stale card text")
    ]
    real_div.sort(key=lambda x: abs(x["delta_log"]), reverse=True)
    print("## Highlighted cases (top |dlog|, excluding placeholder bleed)")
    if not real_div:
        print("- (none above threshold once placeholder bleed excluded)")
    for r in real_div[:5]:
        o, c = r["ours"], r["claim"]
        if c is None:
            continue
        print(f"- **{r['stem']}** -- claim {c['measure']} {c['est']:.2f} "
              f"({c['lci']:.2f}-{c['uci']:.2f}, k={c.get('k')}); "
              f"our OR {o['OR']:.2f} ({o['lci']:.2f}-{o['uci']:.2f}, "
              f"k={o['k']}, tau2={o['tau2']:.3f}); "
              f"|dlog|={abs(r['delta_log']):.3f}; cause: {r['cause']}.")


if __name__ == "__main__":
    main()
