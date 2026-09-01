# -*- coding: utf-8 -*-
"""KNOWN-ANSWER CONTROL for ssot/claims.py. Every fixture is synthetic and __control_*.

Each case replays a REAL defect from 2026-08-30/31 and asserts the module rejects it. A
claim vocabulary that never refuses anything is documentation wearing a validator's clothes.
"""
from __future__ import annotations

import io
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "ssot"))

import claims as C  # noqa: E402

FAIL = []


def check(name, cond, detail=""):
    print("  %s  %s%s" % ("PASS" if cond else "FAIL", name, "" if cond else "   <- " + str(detail)))
    if not cond:
        FAIL.append(name)


def t_derived_agreement_is_not_corroboration():
    """The 59 introductions: one transform, two fields, perfect agreement, zero witnesses."""
    print("\n[1] DERIVED AGREEMENT -- two fields, one origin")
    o = {"title": "__control_ topic"}
    C.set_derived(o, "question", "In __control_ topic, what is the effect?",
                  ["title"], "__control_/repair.py")
    C.set_derived(o, "introduction", "This review asks: ...", ["question"],
                  "__control_/repair.py")
    check("question traces to title", C.origins(o, "question") == ["title"])
    check("introduction ALSO traces to title", C.origins(o, "introduction") == ["title"])
    check("so they do NOT corroborate", C.corroborate(o, "question", "introduction") is False)
    o2 = {"a": 1, "b": 2}
    C.set_derived(o2, "x", 1, [], "__control_", authored=True)
    C.set_derived(o2, "y", 2, [], "__control_", authored=True)
    check("two AUTHORED fields DO corroborate", C.corroborate(o2, "x", "y") is True)


def t_dotted_paths_resolve_across_containers():
    """The regression that shipped: a path the resolver cannot follow reads as independent.

    `manuscript.introduction` derives from `question`, which derives from `title`. Looking
    the path up as a FLAT key found nothing, treated it as its own origin, and returned
    corroborate()==True -- a false corroboration on the exact case this module exists for.
    """
    print("\n[1b] DOTTED PATHS -- a resolver that cannot resolve reports independence")
    o = {"title": "__control_ topic", "manuscript": {}}
    C.set_derived(o, "question", "In __control_ topic, ...", ["title"], "__control_/r.py")
    C.set_derived(o["manuscript"], "introduction", "This review asks: ...", ["question"],
                  "__control_/r.py")
    check("nested field traces THROUGH question TO title",
          C.origins(o, "manuscript.introduction") == ["title"],
          C.origins(o, "manuscript.introduction"))
    check("and therefore does NOT corroborate the question",
          C.corroborate(o, "question", "manuscript.introduction") is False)
    check("an unresolvable path is its own origin, not an error",
          C.origins(o, "nope.missing") == ["nope.missing"])


def t_validate_claim_takes_a_dotted_path_on_a_REAL_object():
    """⛔ PLANTED ON A REAL NESTED CORPUS OBJECT, NOT A FIXTURE.

    Every other control here is synthetic, and synthetic fixtures are FLAT -- a flat fixture
    cannot exercise a path resolver, which is why this class of defect has now survived two
    fixture suites tonight. This one loads a real object off disk and plants into its nested
    `results.by_outcome.<oid>` container, which is where the claims actually live.

    The defect: validate_claim used to take (container, plain_key) while its neighbours took
    (root, dotted_path). Handed a dotted path it did a flat lookup, missed, and returned []
    -- a clean pass on a value that should have been refused.
    """
    print("\n[1c] DOTTED PATH INTO A REAL OBJECT -- must refuse, not silently pass")
    import glob
    import json as _json
    # ⚠️ JSON FILES UNDER ssot/, NOT "the review corpus" -- the glob also matches
    # SEARCH-RECORD.json, ADJUDICATION-RECORD.json and SCREENING-RECORD.json. Harmless here
    # because this control takes the FIRST file carrying results.by_outcome and asserts a
    # property of it; it reports no count. The label is corrected so nobody reuses the line
    # believing it enumerates objects.
    hits = sorted(glob.glob(os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "ssot", "*", "*.json")))
    canon = None
    for p in hits:
        try:
            c = _json.load(open(p, encoding="utf-8"))
        except Exception:
            continue
        byo = ((c.get("results") or {}).get("by_outcome") or {}) if isinstance(c, dict) else {}
        if isinstance(byo, dict) and byo:
            canon, oid = c, sorted(byo)[0]
            break
    if canon is None:
        check("a real nested object was available to plant into", False, "none found")
        return

    res = canon["results"]["by_outcome"][oid]
    path = "results.by_outcome.%s.__control_slot" % oid
    # A value that CLAIMS to be a human judgement while recording that it was derived.
    res["__control_slot"] = "not recorded on the page this object was extracted from"
    res["__control_slot__claim"] = "authored_judgement"
    res["__control_slot__derived_from"] = {"inputs": ["title"], "by": "__control_/x.py",
                                           "run_utc": "2026-08-31", "authored": False}

    errs = C.validate_claim(canon, path)
    check("a DOTTED path into a nested container REFUSES", len(errs) >= 1, errs)
    check("and the refusal names the recorded inputs",
          any("records inputs" in e for e in errs), errs)

    res["__control_slot__derived_from"] = {"inputs": [], "by": "a person",
                                           "run_utc": "2026-08-31", "authored": True}
    check("a genuinely authored slot PASSES via the same dotted path",
          C.validate_claim(canon, path) == [])

    try:
        C.validate_claim(canon, "results.by_outcome.%s.nope.missing" % oid)
        check("an UNRESOLVABLE path raises rather than returning a clean pass", False,
              "it returned instead of raising")
    except C.ClaimError as e:
        check("an UNRESOLVABLE path raises rather than returning a clean pass",
              "unresolvable" in str(e))


def t_undeclared_quantity_from_the_RENDERED_page_must_fail():
    """⛔ THE DENOMINATOR COMES FROM THE BUILT BYTES, NOT FROM WHAT WAS DECLARED.

    A gate asking "did everything DECLARED verify?" is vacuous in exactly the way
    check_page_format's first --gate run was, reporting "OK: all 0 review pages conform"
    after measuring nothing. The non-vacuous question is "does every number A READER CAN SEE
    have a declaration that reproduces it", so this plant pulls a real rendered value off a
    real built page and asserts it is caught while undeclared.
    """
    print("\n[8] UNDECLARED QUANTITY, TAKEN FROM THE RENDERED PAGE")
    import glob
    import json as _json
    import re as _re
    root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
    pages = sorted(glob.glob(os.path.join(root, "*REVIEW*.html")))
    if not pages:
        check("a built page was available", False, "none found")
        return
    html = open(pages[0], encoding="utf-8", errors="replace").read()
    # Numbers a reader actually meets. Not a curated list -- whatever the page shows.
    rendered = _re.findall(r">\s*(\d+\.\d{2,4})\s*<", html)
    if not rendered:
        check("the page rendered a decimal quantity", False, "none matched")
        return
    value = rendered[0]
    container = {"q": float(value)}          # the page shows it; nothing declares it
    missing = C.undeclared(container, ["q"])
    check("an UNDECLARED rendered value is flagged", missing == ["q"],
          "%s from %s -> %r" % (value, os.path.basename(pages[0]), missing))

    # Declared but with the WRONG kind -- still undeclared for this purpose.
    container["q__claim"] = "derived_value"
    container["q__evidence"] = {}
    check("a value declared under the WRONG claim kind is still flagged",
          C.undeclared(container, ["q"]) == ["q"])

    # Properly declared AND recomputing -> not flagged.
    container["q__claim"] = "render_derivation"
    container["q__evidence"] = {"op": "product", "inputs": [{"literal": 2.0},
                                                            {"literal": 3.0}],
                                "produces": 6.0, "by": "__control_/p.py"}
    check("a properly declared value is NOT flagged",
          C.undeclared(container, ["q"]) == [])
    ok, got = C.verify_render(container, container["q__evidence"])
    check("and its declaration recomputes", ok and got == 6.0)


def t_authored_with_inputs_is_refused():
    print("\n[2] LAUNDERING -- authored=True with inputs must raise")
    try:
        C.set_derived({}, "q", "v", ["title"], "__control_", authored=True)
        check("refused", False, "it accepted authored=True with inputs")
    except C.ClaimError as e:
        check("refused, and says why", "laundered" in str(e))


def t_counterpart_needs_its_shape():
    """'122 objects mention Cochrane' -> 2 actually carry a counterpart."""
    print("\n[3] COUNTERPART -- string presence is not structural presence")
    bare = {"counterpart": {"note": "see the Cochrane review"},
            "counterpart__claim": "counterpart_review"}
    errs = C.validate_claim(bare, "counterpart")
    check("a bare mention is REFUSED", len(errs) >= 1, errs)
    check("and it names the missing pubN", any("pubN" in e for e in errs), errs)
    check("and names the missing identifier", any("cd/doi" in e for e in errs), errs)
    good = {"counterpart": {"cd": "CD007961", "pubN": "pub3", "checked_utc": "2026-08-30"},
            "counterpart__claim": "counterpart_review"}
    check("a shaped counterpart PASSES", C.validate_claim(good, "counterpart") == [])
    stale = dict(good)
    stale["counterpart"] = {"cd": "CD007961", "pubN": "pub3"}
    check("missing checked_utc is REFUSED -- a version-less counterpart is undated",
          any("checked_utc" in e for e in C.validate_claim(stale, "counterpart")))


def t_identifier_prefix_must_be_confirmed_in_the_record():
    """IPM 036 / MTN-036: digit equality is not identifier equality."""
    print("\n[4] IDENTIFIER -- the letter prefix is load-bearing")
    from_query = {"trial_id": "MTN-036", "trial_id__claim": "trial_identifier",
                  "trial_id__evidence": {"token_as_matched": "036",
                                         "prefix_confirmed_in_fetched_record": False}}
    errs = C.validate_claim(from_query, "trial_id")
    check("prefix unconfirmed is REFUSED", len(errs) >= 1, errs)
    check("and the refusal names query-vs-record",
          any("QUERY" in e for e in errs), errs)
    ok = {"trial_id": "MTN-036", "trial_id__claim": "trial_identifier",
          "trial_id__evidence": {"token_as_matched": "MTN-036",
                                 "prefix_confirmed_in_fetched_record": True}}
    check("confirmed in the fetched record PASSES", C.validate_claim(ok, "trial_id") == [])


def t_unverifiable_is_its_own_state():
    """A sponsor-declared publication no index can find is neither ghost nor confirmed."""
    print("\n[5] UNVERIFIABLE -- the third state")
    part = {"results_publication__claim": "unverifiable_claim",
            "results_publication__evidence": {"asserted_by": "sponsor"}}
    errs = C.validate_claim(part, "results_publication")
    check("a partial unverifiable claim is REFUSED", len(errs) >= 1, errs)
    for f in ("citation_as_given", "indexes_searched", "searched_utc", "located"):
        check("  requires %s" % f, any(f in e for e in errs))
    full = {"results_publication__claim": "unverifiable_claim",
            "results_publication__evidence": {
                "asserted_by": "sponsor", "citation_as_given": "X et al",
                "indexes_searched": ["PubMed"], "searched_utc": "2026-08-30",
                "located": False}}
    check("a fully shaped one PASSES", C.validate_claim(full, "results_publication") == [])


def t_unknown_origin_is_not_authored():
    print("\n[6] UNKNOWN ORIGIN -- reported, never silently promoted to authored")
    o = {"question": "a legacy value with no provenance"}
    errs, unknown = C.validate_object(o)
    check("no errors raised for a legacy field", errs == [], errs)
    check("but it IS reported as unknown-origin", "question" in unknown)
    check("and validate does not claim it was authored",
          o.get("question__derived_from") is None)


def t_unknown_claim_kind_is_refused():
    print("\n[7] VOCABULARY -- an unknown kind is refused, not tolerated")
    o = {"x": 1, "x__claim": "vibes"}
    errs = C.validate_claim(o, "x")
    check("unknown kind REFUSED", len(errs) == 1 and "unknown claim kind" in errs[0], errs)


def main():
    print("KNOWN-ANSWER CONTROL: ssot/claims.py  (synthetic __control_ fixtures only)")
    for t in (t_derived_agreement_is_not_corroboration, t_dotted_paths_resolve_across_containers,
              t_validate_claim_takes_a_dotted_path_on_a_REAL_object,
              t_authored_with_inputs_is_refused,
              t_counterpart_needs_its_shape, t_identifier_prefix_must_be_confirmed_in_the_record,
              t_unverifiable_is_its_own_state, t_unknown_origin_is_not_authored,
              t_unknown_claim_kind_is_refused,
              t_undeclared_quantity_from_the_RENDERED_page_must_fail):
        t()
    print("\n" + "=" * 66)
    if FAIL:
        print("RESULT: FAIL -- %d check(s): %s" % (len(FAIL), ", ".join(FAIL)))
        return 1
    print("RESULT: PASS -- every shape refused what it should refuse.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
