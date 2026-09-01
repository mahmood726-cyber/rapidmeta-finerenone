# -*- coding: utf-8 -*-
"""Fire EVERY refusal these modules claim to make. Both directions, every one.

⛔ WHY THIS EXISTS, AND IT IS NOT HYPOTHETICAL. Tonight a module's docstring said it
"REFUSES TO EMIT" an expanded group. Line 113 still emitted one, and a page shipped five
expanded groups against an explicit ruling. THE COMMENT ASSERTED A GUARD THAT DID NOT
EXIST, and because the comment read as a guarantee, the missing guard was invisible --
worse, a real guard was later deleted on the strength of it.

⚠️ AND MY OWN MODULES WERE IN THE SAME STATE. `screening_ledger` and `rob_attribution` both
refuse things, and both refusals were real -- I watched them fire. But THAT IS A FACT ABOUT
TODAY. A refusal nobody re-fires is a comment with good intentions, and the next edit that
breaks it will do so silently, exactly as the ledger's did.

    A REFUSAL THAT CANNOT BE MADE TO FIRE AND A REFUSAL THAT FIRES ON EVERYTHING ARE THE
    SAME DEFECT: one reachable outcome measures nothing.

So every case below asserts BOTH -- the bad input is refused AND a clean input still passes.
A suite that only proved refusals would reward a module that refused everything, which is
how `audit_index_identity_drift` ran for days refusing its own negative control and printing
no count while looking like a tool being careful.
"""
from __future__ import annotations

import io
import json
import os
import sys
import tempfile

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, ".."))
sys.path.insert(0, os.path.join(_ROOT, "ssot"))

import claims as C                 # noqa: E402
import population as P             # noqa: E402
import screening_ledger as SL      # noqa: E402
import rob_attribution as RA       # noqa: E402
import growth_guard as GG          # noqa: E402
import grade_engine as GE          # noqa: E402
from rob_block import rob_block    # noqa: E402

FAIL = []


def check(name, cond, detail=""):
    print("  %s  %s%s" % ("PASS" if cond else "FAIL", name,
                          "" if cond else "   <- " + str(detail)[:110]))
    if not cond:
        FAIL.append(name)


def fires(name, fn, *, expect_in=None, exc=Exception):
    """Assert the call REFUSES, and that the refusal names the offending thing."""
    try:
        fn()
    except exc as e:
        ok = (expect_in is None) or (expect_in.lower() in str(e).lower())
        check(name, ok, "raised but did not name %r: %s" % (expect_in, e))
        return
    check(name, False, "did NOT refuse")


def passes(name, fn):
    try:
        fn()
        check(name, True)
    except Exception as e:                                   # noqa: BLE001
        check(name, False, "clean input was refused: %s" % e)


# --------------------------------------------------------------------------- fixtures
_LEDGER_N = [0]


def _ledger(rows=3, declared=None):
    """A fixture on a UNIQUE path every call.

    ⚠️ THE FIRST VERSION REUSED ONE FILENAME, so building the mismatched fixture OVERWROTE
    the good one, and three later cases then tripped the denominator guard instead of the
    guard they were testing -- reporting "REFUSES" failures whose message named a different
    refusal entirely. A shared mutable fixture makes a suite test the order its cases run in.
    """
    led = [{"pmid": "1000%d" % i, "title": "t%d" % i, "journal": "J", "year": 2020,
            "decision": "EXCLUDE", "rule": "R1", "reason": "why"} for i in range(rows)]
    doc = {"ledger": led, "denominator": {"records_screened": declared if declared
                                          is not None else rows}}
    _LEDGER_N[0] += 1
    p = os.path.join(tempfile.gettempdir(), "__control_ledger_%d.json" % _LEDGER_N[0])
    json.dump(doc, open(p, "w", encoding="utf-8"))
    return p


def _block(name="__control_ assessor A"):
    return {"assessors": [{"n": 1, "name": name, "model_family": "x"}],
            "trials": [{"trial": "T1", "id": "T1", "domains": [
                {"domain": "D1", "domain_name": "D1_randomisation_process",
                 "agreed": True,
                 "by_assessor": [{"n": 1, "assessor": name, "judgement": "LOW"}]}]}]}


# --------------------------------------------------------------------------- the cases
def t_screening_ledger():
    print("\n[1] screening_ledger.render")
    good = _ledger(3, 3)
    passes("a consistent ledger RENDERS", lambda: SL.render(good, "utc"))
    fires("parts do not sum -> REFUSES", lambda: SL.render(_ledger(2, 3), "utc"),
          expect_in="denominator declares", exc=ValueError)
    nold = os.path.join(tempfile.gettempdir(), "__control_noledger.json")
    json.dump({"denominator": {"records_screened": 3}}, open(nold, "w", encoding="utf-8"))
    fires("no `ledger` list -> REFUSES", lambda: SL.render(nold, "utc"),
          expect_in="refusing to render", exc=ValueError)

    # The guard that the OTHER module's comment claimed and did not have.
    orig = SL._row_html
    SL._row_html = lambda r: '<tr><td><details open><summary>x</summary></details></td></tr>'
    fires("an OPEN <details> -> REFUSES", lambda: SL.render(good, "utc"),
          expect_in="carries `open`", exc=ValueError)
    SL._row_html = lambda r: '<tr><td><script>x()</script></td></tr>'
    fires("a <script> -> REFUSES", lambda: SL.render(good, "utc"),
          expect_in="contains a script", exc=ValueError)
    SL._row_html = orig
    passes("and it RENDERS again once restored", lambda: SL.render(good, "utc"))


def t_rob_attribution():
    print("\n[2] rob_attribution.render")
    passes("a clean block RENDERS", lambda: RA.render(_block(), "utc"))
    fires("an assessor name the prose removers DELETE -> REFUSES",
          lambda: RA.render(_block("GPT-5 Codex, via `codex exec`"), "utc"),
          expect_in="codex exec", exc=ValueError)
    check("and the guard is still in step with the projector's own pattern",
          RA.removers_in_step() is True, RA.removers_in_step())
    check("no assessment -> empty string, not a placeholder", RA.render({}, "utc") == "")


def t_claims():
    print("\n[3] claims")
    passes("a shaped render_derivation VERIFIES", lambda: C.verify_render(
        {"a": 2.0, "b": 3.0},
        {"op": "product", "inputs": ["a", "b"], "produces": 6.0, "by": "x"}))
    fires("an unknown op -> REFUSES (never eval'd)", lambda: C.verify_render(
        {}, {"op": "__import__('os').system", "inputs": [], "produces": 1}),
        expect_in="unknown render op", exc=C.ClaimError)
    fires("an input that does not resolve -> REFUSES", lambda: C.verify_render(
        {"a": 1}, {"op": "product", "inputs": ["a", "nope.gone"], "produces": 1, "by": "x"}),
        expect_in="does not resolve", exc=C.ClaimError)
    fires("no `produces` -> REFUSES", lambda: C.verify_render(
        {"a": 2.0, "b": 3.0}, {"op": "product", "inputs": ["a", "b"], "by": "x"}),
        expect_in="no `produces`", exc=C.ClaimError)
    fires("authored=True WITH inputs -> REFUSES", lambda: C.set_derived(
        {}, "q", "v", ["title"], "x", authored=True), expect_in="laundered",
        exc=C.ClaimError)
    fires("reconstructed WITHOUT run_utc -> REFUSES", lambda: C.set_derived(
        {}, "q", "v", ["t"], "x", reconstructed=True), expect_in="reconstruction",
        exc=C.ClaimError)
    fires("validate_claim on an unresolvable path -> RAISES",
          lambda: C.validate_claim({"a": {}}, "a.b.c"), expect_in="unresolvable",
          exc=C.ClaimError)
    passes("validate_claim on a real container returns a list",
           lambda: C.validate_claim({"x": 1}, "x"))


def t_population():
    print("\n[4] population.assert_parts_sum")
    passes("parts that sum PASS",
           lambda: P.assert_parts_sum(10, "things", examined=7, corrupt=1, skipped=2))
    fires("parts that do not sum -> REFUSES",
          lambda: P.assert_parts_sum(10, "things", examined=7, corrupt=1, skipped=1),
          expect_in="do not account", exc=P.PartsDoNotSum)
    d = tempfile.gettempdir()
    trunc = os.path.join(d, "__control_trunc.json")
    open(trunc, "w").write('{"x":' + "a" * 32763)
    got = P.read_payload(trunc)
    check("a truncated payload is RETRIEVED_CORRUPT, not NO_PAYLOAD",
          got["state"] == P.RETRIEVED_CORRUPT, got["state"])
    check("and a power-of-two boundary is flagged", got.get("power_of_two_boundary") is True)
    check("an absent file is NO_PAYLOAD",
          P.read_payload(os.path.join(d, "__control_absent.json"))["state"] == P.NO_PAYLOAD)


def t_growth_guard():
    print("\n[5] growth_guard")
    d = tempfile.gettempdir()
    p = os.path.join(d, "__control_page.html")
    open(p, "w", encoding="utf-8").write("<p>" + ("word " * 500) + "</p>")
    small = "<p>" + ("word " * 520) + "</p>"
    big = "<p>" + ("word " * 2000) + "</p>"
    check("growth under the threshold is OK", GG.check(small, p)[0] == GG.OK)
    check("UNDECLARED growth past it REFUSES", GG.check(big, p)[0] == GG.REFUSED)
    check("the same growth DECLARED passes",
          GG.check(big, p, declaration="added the ledger")[0] == GG.OK)
    check("no baseline file -> NOT_ASSESSABLE, never a pass",
          GG.check(big, os.path.join(d, "__control_none.html"))[0] == GG.NOT_ASSESSABLE)


def t_grade_attachment():
    print("\n[6] grade_engine outcome attachment")
    obj = {"results": {"by_outcome": {"primary": {
        "outcome": "__control_ outcome", "k": 2,
        "pooled": {"point": 0.5, "ci_low": 0.4, "ci_high": 0.7, "ci_level": 95,
                   "measure": "RR"},
        "heterogeneity": {"i2": 0.0, "tau2": 0.0, "q": 1.0, "df": 1}}}}}
    named = GE.derive(obj, "primary")
    check("a NAMED outcome does not refuse for attachment",
          "NO NAME" not in (named.get("reason") or ""), named.get("reason", "")[:60])
    obj2 = json.loads(json.dumps(obj))
    obj2["results"]["by_outcome"]["primary"].pop("outcome")
    r2 = GE.derive(obj2, "primary")
    check("an UNNAMED outcome REFUSES", r2["state"] == GE.REFUSED, r2.get("state"))
    check("and issues NO certainty letter", r2.get("certainty") is None)
    check("and the refusal says a slug names a position",
          "names a position" in (r2.get("reason") or ""))


def main():
    print("REFUSAL CONTROLS -- every guard fired, both directions")
    print("a refusal nobody re-fires is a comment with good intentions\n")
    for t in (t_screening_ledger, t_rob_attribution, t_claims, t_population,
              t_growth_guard, t_grade_attachment):
        try:
            t()
        except Exception:                                    # noqa: BLE001
            FAIL.append(t.__name__)
            print("  ERROR in %s" % t.__name__)
            import traceback
            traceback.print_exc()
    print("\n" + "=" * 68)
    if FAIL:
        print("RESULT: FAIL -- %d check(s): %s" % (len(FAIL), ", ".join(FAIL[:6])))
        return 1
    print("RESULT: PASS -- every refusal fired, and every clean input still passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
