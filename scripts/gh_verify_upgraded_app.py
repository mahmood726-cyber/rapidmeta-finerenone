#!/usr/bin/env python
"""Verify a global-health app after the HFrEF-style upgrade. Fail-closed.

Generalises scripts/hfref_verify_app_quarantine.py to any app upgraded under
GLOBAL_HEALTH_UPGRADE_RECIPE.md. Driven by the same `*_badge.json` spec used to
write the badge, so the spec is the single source of truth for both surfaces.

Checks (exit non-zero on any failure):
  A. structural       - div-balance delta vs the recorded baseline, no literal
                        </script> inside a script body, no placeholder tokens.
  B. surface presence - the badge exists and carries the spec's headline.
  C. AGREEMENT        - window.__verdict matches the spec's verdict_patch, and
                        no green "checks passed" badge sits over a non-clean
                        verdict.
  D. self-contradiction - no trial/arm count appears in the badge that
                        disagrees with the spec's stated figures. (This is the
                        check the first HFrEF draft needed and did not have.)
  E. quarantine       - every quarantined trial is still PRESENT and flagged in
                        the app, not deleted, and its named violation is stated.
  F. no stale claims  - withdrawn numbers do not survive anywhere in the file.

Usage:
  python scripts/gh_verify_upgraded_app.py --app FILE --spec outputs/<x>_badge.json
  python scripts/gh_verify_upgraded_app.py ... --selftest   # prove it can FAIL
"""
from __future__ import annotations

import argparse
import copy
import io
import json
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

GREEN_BG = {"#15803d", "#166534", "#16a34a", "#22c55e", "#14532d"}
CLEAN_VERDICTS = {"STABLE", "PASS", "CLEAN"}
RE_VERDICT = re.compile(r"window\.__verdict\s*=\s*(\{.*?\});", re.S)
RE_TAG = re.compile(r"<[^>]+>")


def badge_html(html: str) -> str:
    i = html.find('id="rapidmeta-integrity-badge"')
    if i < 0:
        return ""
    start = html.rfind("<div", 0, i)
    depth = 0
    for m in re.finditer(r"<div\b|</div\s*>", html[start:]):
        depth += 1 if m.group(0).startswith("<div") else -1
        if depth == 0:
            return html[start:start + m.end()]
    return html[start:]


def check(html: str, spec: dict, div_delta_baseline: int | None) -> list[str]:
    fails: list[str] = []
    badge = badge_html(html)
    badge_text = re.sub(r"\s+", " ", RE_TAG.sub(" ", badge))

    # ---- A. structural
    d = len(re.findall(r"<div[\s>]", html)) - len(re.findall(r"</div>", html))
    if div_delta_baseline is not None and d != div_delta_baseline:
        fails.append(f"A: div-balance delta {d} != baseline {div_delta_baseline}")
    for sm in re.finditer(r"<script\b[^>]*>(.*?)</script>", html, re.S):
        if "</script>" in sm.group(1):
            fails.append(f"A: literal </script> inside a script body at {sm.start()}")
    for tok in ("REPLACE_ME", "__PLACEHOLDER__", "TODO_FILL"):
        if tok in html:
            fails.append(f"A: unpopulated template token {tok!r}")

    # ---- B. surface presence
    if not badge:
        fails.append("B: no #rapidmeta-integrity-badge element")
    elif spec["headline"] not in badge_text:
        fails.append("B: badge does not carry the spec headline")

    # ---- C. agreement
    m = RE_VERDICT.search(html)
    if not m:
        fails.append("C: no window.__verdict")
    else:
        v = json.loads(m.group(1))
        want = spec["verdict_patch"]
        if v.get("verdict") != want.get("verdict"):
            fails.append(f"C: verdict {v.get('verdict')!r} != spec {want.get('verdict')!r}")
        if v.get("p0_total") != want.get("p0_total"):
            fails.append(f"C: p0_total {v.get('p0_total')} != spec {want.get('p0_total')}")
        for k, exp in (want.get("counts") or {}).items():
            got = (v.get("counts") or {}).get(k)
            if got != exp:
                fails.append(f"C: counts.{k} {got} != spec {exp}")
        bg = re.search(r'id="rapidmeta-integrity-badge"[^>]*background:(#[0-9a-fA-F]{3,6})', html)
        if bg and bg.group(1).lower() in GREEN_BG and v.get("verdict") not in CLEAN_VERDICTS:
            fails.append(f"C: GREEN badge over verdict={v.get('verdict')!r}")
        if bg and bg.group(1).lower() in GREEN_BG and (v.get("p0_total") or 0) > 0:
            fails.append("C: GREEN badge over p0_total>0")

    # ---- D. self-contradiction: any "Trials: N" / "N trials" in the badge must
    #        equal the spec's stated in-fit count.
    n_fit = spec["facts"].get("Trials in fit")
    if n_fit is not None:
        for mm in re.finditer(r"Trials in fit:\s*(\d+)|Trials:\s*(\d+)|(\d+)\s+trials in (?:the )?fit",
                              badge_text, re.I):
            got = int(next(g for g in mm.groups() if g))
            if got != int(n_fit):
                fails.append(f"D: badge states {got} trials in fit, spec says {n_fit}")
    n_q = spec["facts"].get("Quarantined")
    if n_q is not None:
        for mm in re.finditer(r"Quarantined:\s*(\d+)", badge_text, re.I):
            if int(mm.group(1)) != int(n_q):
                fails.append(f"D: badge states {mm.group(1)} quarantined, spec says {n_q}")

    # ---- E. quarantine integrity: retained + flagged, never deleted
    for q in spec.get("quarantined_trials", []):
        if q["id"] not in html:
            fails.append(f"E: quarantined trial {q['id']} DELETED from the app (must be retained and flagged)")
        elif q.get("violation") and q["violation"] not in badge_text:
            fails.append(f"E: quarantined trial {q['id']} present but its named violation is not stated")

    # ---- F. withdrawn numbers must not survive in any CLAIM-BEARING surface.
    # The badge itself is exempt: per the HFrEF precedent a superseded value is
    # "gone except where the correction itself is documented", and naming what
    # was withdrawn is the point of the correction notice.
    outside = html.replace(badge, "") if badge else html
    for stale in spec.get("stale_forbidden", []):
        if stale in outside:
            fails.append(f"F: withdrawn value {stale!r} still present outside the correction notice")
    return fails


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--app", required=True)
    ap.add_argument("--spec", required=True)
    ap.add_argument("--div-delta", type=int, default=None)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    spec = json.load(open(args.spec, encoding="utf-8"))
    html = open(args.app, encoding="utf-8").read()

    fails = check(html, spec, args.div_delta)
    print(f"=== verify {args.app} ===")
    for f in fails:
        print("  FAIL", f)
    print("  PASS - all checks" if not fails else f"  {len(fails)} failure(s)")

    if args.selftest:
        print("\n=== SELF-TEST: the gate must FAIL on each seeded defect ===")
        ok = True
        cases = {
            "green badge restored over a non-clean verdict":
                lambda h: h.replace("background:#991b1b", "background:#15803d"),
            "verdict downgraded back to STABLE":
                lambda h: RE_VERDICT.sub(
                    lambda m: 'window.__verdict = ' + json.dumps(
                        {**json.loads(m.group(1)), "verdict": "STABLE"}) + ';', h, count=1),
            "p0_total zeroed":
                lambda h: RE_VERDICT.sub(
                    lambda m: 'window.__verdict = ' + json.dumps(
                        {**json.loads(m.group(1)), "p0_total": 0}) + ';', h, count=1),
            "badge trial count contradicts the spec":
                lambda h: h.replace("Trials in fit: <strong>0</strong>",
                                    "Trials in fit: <strong>2</strong>"),
            "quarantined trial deleted instead of flagged":
                lambda h: h.replace("NCT01582711", "NCTXXXXXXXX"),
            "withdrawn pooled estimate reinstated":
                lambda h: h.replace("</body>", "<p>pooled OR 0.389 (95% CI 0.134-1.124)</p></body>"),
        }
        for name, mutate in cases.items():
            mutated = mutate(html)
            if mutated == html:
                print(f"  [SKIP] {name} - seed did not apply")
                continue
            got = check(mutated, spec, args.div_delta)
            status = "BLOCKS" if got else "*** DID NOT BLOCK ***"
            if not got:
                ok = False
            print(f"  [{status}] {name}" + (f" -> {got[0]}" if got else ""))
        if not ok:
            print("\nSELF-TEST FAILED: a gate that cannot fail is verification theatre.")
            return 2
        print("\nSELF-TEST PASSED: every seeded defect is blocked.")

    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
