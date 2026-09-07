# -*- coding: utf-8 -*-
"""GATE: the served interval is the one the OBJECT declares -- the generator must never IMPOSE a method.

Defect (caught 2026-09-07 by reading a served subtitle, not by any check): the page generator imposed
modified HKSJ on every ratio page, recomputing t_{k-1}. At k=2 that is t(1)=12.706, which blew
EMPAGLIFLOZIN's interval to 0.413-1.44 -- a SECOND interval beside the object's own fixed-effect CI
[0.700, 0.849]. Same family as gate 38's dead-value-served-live: the page shows a number its own source
does not back.

Self-contained because the generated page EMBEDS its current object (<script id="ssot-current">): the
headline interval a reader sees must equal the pooled CI the embedded object stores, to tolerance. If
not, the page computed the interval by some other method -- a FAIL. Registered in run_all.py so it is
operative (gate 8: a gate nothing runs is VACUOUS).
"""
from __future__ import annotations
import io, os, re, json, glob, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _harness as H  # noqa: E402

_SEP = r"[–—]"                          # en/em-dash separator (NOT the hyphen-minus of a negative bound)
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
    pooled = _embedded_pool(page_html)
    if pooled is None:
        return "NO_OBJECT", {}
    m = _HEADLINE.search(page_html)
    if not m:
        return "NO_HEADLINE", {}
    shown_lo, shown_hi = float(m.group(2)), float(m.group(3))
    obj_lo, obj_hi = float(pooled["ci_low"]), float(pooled["ci_high"])
    ok = (abs(shown_lo - obj_lo) < max(tol, 1e-2 * abs(obj_lo)) and
          abs(shown_hi - obj_hi) < max(tol, 1e-2 * abs(obj_hi)))
    return ("OK" if ok else "FAIL"), {"shown": [shown_lo, shown_hi], "object": [obj_lo, obj_hi]}


# Synthetic controls, pinned in code so they cannot self-retire when a page is fixed.
_SYNTH_BAD = ('<p class="headline">HR 0.7708 (0.413–1.44)</p>'
              '<script type="application/json" id="ssot-current">'
              '{"results":{"by_outcome":{"primary":{"pooled":{"point":0.7708,"ci_low":0.700,'
              '"ci_high":0.8488}}}}}</script>')
_SYNTH_OK = ('<p class="headline">HR 0.7708 (0.7000–0.8488)</p>'
             '<script type="application/json" id="ssot-current">'
             '{"results":{"by_outcome":{"primary":{"pooled":{"point":0.7708,"ci_low":0.700,'
             '"ci_high":0.8488}}}}}</script>')


def main(argv):
    gate = H.Gate("SERVED INTERVAL MATCHES DECLARED METHOD",
                  "a page's shown interval equals its embedded object's pooled CI; no imposed method")
    named = gate.expect_case("__synthetic_imposed_interval__",
                             "a page showing an interval its embedded object does not back must be flagged")
    gate.requires_control()

    pos = check_page(_SYNTH_BAD)[0] == "FAIL"      # imposed method: must fire
    neg = check_page(_SYNTH_OK)[0] == "OK"         # faithful render: must not fire
    if pos:
        gate.saw(named)
    gate.control(1, 0 if neg else 1, [] if neg else ["faithful-render negative control was flagged"], accuses=True)
    if not pos:
        gate.broken("the positive control (imposed 0.413-1.44 over a fixed-effect CI) did NOT fire; "
                    "the detector cannot see the defect it exists for")

    repo = H.repo_root()
    pages = sorted(glob.glob(os.path.join(repo, "out", "generated", "*.html")))
    checked = 0
    reach = {"NO_OBJECT": 0, "NO_HEADLINE": 0}
    for p in pages:
        try:
            html = io.open(p, encoding="utf-8", errors="replace").read()
        except Exception:
            continue
        v, d = check_page(html)
        if v == "OK":
            checked += 1
        elif v == "FAIL":
            gate.finding(os.path.basename(p), "shown interval %s does not match embedded object CI %s "
                         "(imposed method)" % (d["shown"], d["object"]))
        else:
            reach[v] = reach.get(v, 0) + 1
    gate.kinds({"page CHECKED (shown == embedded CI)": checked,
                "page FAIL (imposed method)": gate.n_findings(),
                "no embedded object": reach["NO_OBJECT"],
                "no parseable headline": reach["NO_HEADLINE"]})
    gate.coverage(checked + gate.n_findings(), len(pages),
                  "%d generated page(s) carry no embedded object or no parseable headline to check"
                  % (reach["NO_OBJECT"] + reach["NO_HEADLINE"]))
    return gate.report(denominator="%d generated page(s) under out/generated/" % len(pages))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
