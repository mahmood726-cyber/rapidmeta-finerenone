"""pooled-value gate -- does the page's headline number match the object's?

WHY THIS EXISTS
    A mutation test on 2026-08-16 changed the object's pooled point estimate from
    0.872 to 0.640 -- a 27% shift, from null-inclusive to strongly protective --
    and EVERY existing gate returned PASS, exit 0.
    The k gate caught a k 4->7 mutant, so coverage was non-zero; but the single most
    consequential number on the page was compared against nothing.
    The alignment gates check STRUCTURE (tables, figures, fonts). identity_gate checks
    TRIAL IDENTITY. Nothing compared the pooled VALUE between page and object.

THE TWO RULES IT ENFORCES
    1. Per-key provenance: every value is compared against a referent key with a
       locator (object path). A value checked against "some number somewhere" is
       not checked.
    2. A field nobody checked must NOT read as a field that passed. A missing
       referent key yields INVALID, never PASS, and INVALID keeps a page out of
       "verified live".

Exit: 0 = PASS, 1 = FAIL, 2 = INVALID (not assessed -- never treat as a pass).
"""
from __future__ import annotations
import argparse, json, re, sys
from pathlib import Path

TOL = 0.005          # absolute tolerance on a ratio measure
CI_TOL = 0.005


def load_object(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8", errors="replace"))


def referent_keys(obj: dict):
    """Yield (locator, dict-with-point/ci) for every pooled result in the object.

    The locator IS the provenance: it names exactly where in the object the
    expected value came from. No locator -> no check.
    """
    res = (obj.get("results") or {}).get("by_outcome") or {}
    for outcome, block in res.items():
        pooled = (block or {}).get("pooled")
        if isinstance(pooled, dict) and "point" in pooled:
            yield f"results.by_outcome.{outcome}.pooled", pooled, block.get("k")


def page_text(p: Path) -> str:
    t = p.read_text(encoding="utf-8", errors="replace")
    t = re.sub(r"<script[^>]*>.*?</script>", " ", t, flags=re.S)
    t = re.sub(r"<style[^>]*>.*?</style>", " ", t, flags=re.S)
    return re.sub(r"<[^>]+>", " ", t)


NUMPAT = r"(\d+\.\d{2,4})"
TRIPLE = re.compile(
    r"(?:HR|RR|OR|RATE_RATIO|MD|SMD)\s*,?\s*" + NUMPAT +
    r"\s*[\(\[]?\s*(?:95%\s*CI[,: ]*)?" + NUMPAT + r"\s*(?:to|-|–|—|,)\s*" + NUMPAT,
    re.I)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--object", required=True)
    ap.add_argument("--page", required=True)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()

    if a.selftest:
        return selftest()

    obj = load_object(Path(a.object))
    txt = page_text(Path(a.page))
    found = TRIPLE.findall(txt)
    triples = {(round(float(p), 4), round(float(lo), 4), round(float(hi), 4)) for p, lo, hi in found}

    keys = list(referent_keys(obj))
    if not keys:
        print("pooled-value gate: object carries NO pooled referent key")
        print("-> INVALID (exit 2)  -- not assessed; must not be read as a pass")
        return 2

    n_pass = n_fail = 0
    for locator, pooled, k in keys:
        pt = pooled.get("point"); lo = pooled.get("ci_low"); hi = pooled.get("ci_high")
        if pt is None or lo is None or hi is None:
            print(f"  {locator}: referent incomplete (point/ci_low/ci_high) -> INVALID")
            return 2
        hit = any(abs(P - pt) <= TOL and abs(L - lo) <= CI_TOL and abs(H - hi) <= CI_TOL
                  for P, L, H in triples)
        if hit:
            print(f"  {locator}: PASS  page shows {pt} ({lo} to {hi})")
            n_pass += 1
        else:
            near = sorted(triples, key=lambda t: abs(t[0] - pt))[:3]
            print(f"  {locator}: FAIL  object says {pt} ({lo} to {hi}); "
                  f"page's nearest displayed triples: {near}")
            n_fail += 1

    print(f"\npooled-value gate: {len(keys)} referent key(s): {n_pass} PASS, {n_fail} FAIL")
    if n_fail:
        print("-> FAIL (exit 1)")
        return 1
    print("-> PASS (exit 0)")
    return 0


def selftest() -> int:
    """Positive AND negative. A gate that cannot fail is not a gate."""
    import tempfile, os
    ok = True
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        obj = {"results": {"by_outcome": {"primary": {"k": 4,
               "pooled": {"measure": "HR", "point": 0.872, "ci_low": 0.746, "ci_high": 1.02}}}}}
        (d / "o.json").write_text(json.dumps(obj), encoding="utf-8")
        (d / "match.html").write_text("<p>pooled HR 0.872 (0.746 to 1.02)</p>", encoding="utf-8")
        (d / "mismatch.html").write_text("<p>pooled HR 0.640 (0.746 to 1.02)</p>", encoding="utf-8")
        (d / "empty.json").write_text(json.dumps({"results": {"by_outcome": {}}}), encoding="utf-8")

        cases = [("page matches object", "o.json", "match.html", 0),
                 ("THE M1 REGRESSION: page and object disagree on the point", "o.json", "mismatch.html", 1),
                 ("object has no pooled key -> INVALID not PASS", "empty.json", "match.html", 2)]
        for name, o, p, want in cases:
            r = os.system(f'"{sys.executable}" "{__file__}" --object "{d/o}" --page "{d/p}" >nul 2>&1')
            got = r >> 8 if r > 255 else r
            mark = "correct" if got == want else "WRONG"
            if got != want:
                ok = False
            print(f"  {name:58s} exit={got} expected={want}  {mark}")
    print(f"\npooled-value gate correct on every case: {ok}")
    print("-> PASS (exit 0)" if ok else "-> SELFTEST FAILED (exit 1)")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
