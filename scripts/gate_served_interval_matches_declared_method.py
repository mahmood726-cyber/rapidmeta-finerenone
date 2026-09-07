# -*- coding: utf-8 -*-
"""GATE: the served interval must be the one the OBJECT declares -- the generator must never IMPOSE a method.

The defect this closes (caught 2026-09-07 by reading a served subtitle, not by any check): the page
generator imposed modified HKSJ on every ratio page, recomputing t_{k-1}. At k=2 that is t(1)=12.706,
which blew EMPAGLIFLOZIN's interval to 0.413-1.44 -- a SECOND interval, computed by a method the object
did not declare, sitting beside the object's own fixed-effect CI [0.700, 0.849]. "Declared method vs
served number" is the same family as gate 38's dead-value-served-live: the page shows a number that its
own source does not back.

The check is self-contained because the generated page now EMBEDS its current object
(<script id="ssot-current">): the headline interval the reader sees must equal the pooled CI the
embedded object stores, to tolerance. If it does not, the page computed the interval by some other
method -- a FAIL -- regardless of which method or why. The generator's job is to RENDER what the object
declares, never to re-derive an interval of its own.

  PASS   every generated page's shown interval equals its embedded object's pooled CI
  FAIL   a page serves an interval its embedded object does not back (an imposed method)
  NO_OBJECT / NO_HEADLINE   not a pass -- the gate's reach ran out; counted, never silent
"""
from __future__ import annotations
import io, os, re, json, sys, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# The generator writes the CI separator as an EN-dash (or em-dash); negative bounds use a hyphen-minus.
# Matching the separator as en/em-dash ONLY lets "-52.73–-48.38" parse as lo=-52.73, hi=-48.38 rather
# than the minus being read as the separator. Point and both bounds may be negative (difference measures).
_SEP = r"[–—]"                          # en-dash / em-dash separator (NOT the hyphen-minus of a negative)
_HEADLINE = re.compile(r'class="headline"[^>]*>\s*[A-Za-z]+\s+(-?[0-9.]+)\s*\(\s*(-?[0-9.]+)\s*' + _SEP +
                       r'\s*(-?[0-9.]+)\s*\)', re.I)
_EMBED = re.compile(r'<script[^>]*id="ssot-current"[^>]*>(.*?)</script>', re.S | re.I)


def _embedded_pool(page_html):
    m = _EMBED.search(page_html)
    if not m:
        return None
    try:
        obj = json.loads(m.group(1).replace("<\\/", "</"))
    except Exception:
        return None
    for o in ((obj.get("results") or {}).get("by_outcome") or {}).values():
        pooled = (o or {}).get("pooled") or {}
        if pooled.get("ci_low") is not None and pooled.get("ci_high") is not None:
            return pooled
    return None


def check_page(page_html, tol=5e-3):
    """Return ('OK'|'FAIL'|'NO_OBJECT'|'NO_HEADLINE', detail)."""
    pooled = _embedded_pool(page_html)
    if pooled is None:
        return "NO_OBJECT", {}
    m = _HEADLINE.search(page_html)
    if not m:
        return "NO_HEADLINE", {}
    shown_lo, shown_hi = float(m.group(2)), float(m.group(3))
    obj_lo, obj_hi = float(pooled["ci_low"]), float(pooled["ci_high"])
    # relative tolerance so a 4-dp headline vs a stored value differs only by rounding
    ok = (abs(shown_lo - obj_lo) < max(tol, 1e-2 * abs(obj_lo)) and
          abs(shown_hi - obj_hi) < max(tol, 1e-2 * abs(obj_hi)))
    return ("OK" if ok else "FAIL"), {"shown": [shown_lo, shown_hi], "object": [obj_lo, obj_hi],
                                       "model": pooled.get("model")}


# SYNTHETIC positive control -- pinned in code so it cannot self-retire when a page is fixed.
# The exact defect: headline shows the imposed modified-HKSJ interval; the embedded object declares
# the fixed-effect CI. The two disagree -> the gate must FIRE.
_SYNTH_BAD = ('<p class="headline">HR 0.7708 (0.413–1.44)</p>'
              '<script type="application/json" id="ssot-current">'
              '{"results":{"by_outcome":{"primary":{"pooled":{"point":0.7708,"ci_low":0.700,'
              '"ci_high":0.8488,"model":"fixed-effect inverse variance"}}}}}</script>')
# SYNTHETIC negative control: headline equals the embedded object's CI -> must stay SILENT.
_SYNTH_OK = ('<p class="headline">HR 0.7708 (0.7000–0.8488)</p>'
             '<script type="application/json" id="ssot-current">'
             '{"results":{"by_outcome":{"primary":{"pooled":{"point":0.7708,"ci_low":0.700,'
             '"ci_high":0.8488,"model":"fixed-effect inverse variance"}}}}}</script>')


def controls():
    pos = check_page(_SYNTH_BAD)[0] == "FAIL"      # imposed method: must fire
    neg = check_page(_SYNTH_OK)[0] == "OK"         # faithful render: must not fire
    return pos, neg


def scan(paths):
    hits, checked, reach = [], 0, {"NO_OBJECT": 0, "NO_HEADLINE": 0}
    for p in paths:
        try:
            html = io.open(p, encoding="utf-8", errors="replace").read()
        except Exception:
            continue
        verdict, detail = check_page(html)
        if verdict == "OK":
            checked += 1
        elif verdict == "FAIL":
            hits.append((os.path.basename(p), detail))
        else:
            reach[verdict] = reach.get(verdict, 0) + 1
    return hits, checked, reach


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    paths = args or glob.glob(os.path.join(ROOT, "out", "generated", "*.html"))
    pos, neg = controls()
    print("gate: served interval matches the method the OBJECT declares (no imposed method)")
    print("  CONTROL positive (imposed 0.413-1.44 over fixed-effect CI) fires: %s (must be True)" % pos)
    print("  CONTROL negative (faithful render) silent:                  %s (must be True)" % neg)
    hits, checked, reach = scan(paths)
    print("  CHECKED (shown interval == embedded object CI): %d page(s)" % checked)
    print("  reach ran out (not passes): NO_OBJECT=%d NO_HEADLINE=%d" % (reach.get("NO_OBJECT", 0), reach.get("NO_HEADLINE", 0)))
    if hits:
        print("  FAIL -- served interval NOT backed by the object (imposed method): %d" % len(hits))
        for name, d in hits:
            print("     %-52s shown %s  object %s" % (name, d["shown"], d["object"]))
    ok = pos and neg and not hits
    print("\n%s" % ("PASS" if ok else "FAIL ABOVE"))
    raise SystemExit(0 if ok else 1)
