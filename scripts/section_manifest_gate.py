"""EXPECTED-SECTION MANIFEST -- does every surface carry every section the object earns?

WHY THIS EXISTS
    The Word-vs-HTML alignment gate compared only the sections BOTH surfaces
    emit. A section present in one and absent from the other was therefore
    silently OUT OF SCOPE rather than a divergence, and the extraction provenance
    table was missing from every Word manuscript this project ever produced.
    Nothing could have reported it.

    A GATE THAT COMPARES ONLY WHAT BOTH SURFACES HAVE CAN NEVER DETECT ABSENCE.
    The intersection is not the expected set. Using it as one converts every
    missing section into a pass.

    Porting that one section by hand fixed one instance. This is what stops
    instance two: the only thing preventing the next silently-missing section was
    that someone happened to look.

THE MANIFEST IS PROJECTED, NOT WRITTEN
    Each rule below asks the OBJECT what it holds and derives which sections the
    object has therefore earned. A hand-written list would be one more surface
    that drifts out of step with the thing it describes -- which is the defect
    this file exists to catch, one level up.

WHAT A FULL PASS DOES NOT ESTABLISH -- written in advance
    - NOT that section CONTENT agrees between surfaces. This checks presence.
      Two surfaces can both carry an extraction table and disagree in every row;
      that is the alignment gate's job and this does not replace it.
    - NOT that a section is CORRECT, complete, or well-formed.
    - NOT that sections the object does NOT earn are absent. A surface carrying an
      extra section passes here.
    - NOT anything about surfaces it is not given. A renderer nobody passes in is
      unchecked, not clean.
"""
from __future__ import annotations
import json
import os, os, re, sys, io

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


def manifest(canon):
    """Sections this object EARNS, derived from what it actually holds."""
    req = {}
    trials = (canon.get("inputs") or {}).get("trials") or []

    quoted = any((bo.get("provenance") or {}).get("source_quotes")
                 for t in trials for bo in (t.get("by_outcome") or {}).values())
    if quoted:
        req["extraction_provenance"] = (
            "Extracted values, and where each came from",
            "the object holds verbatim source quotes on at least one trial, so both "
            "surfaces must show a reader where each value came from")

    outs = (canon.get("results") or {}).get("by_outcome") or {}
    if any((o.get("pooled") or {}).get("point") is not None for o in outs.values()):
        req["pooled_result"] = (
            "0.",  # any rendered decimal for the pooled value; matched on content
            "the object holds a pooled point estimate, so both surfaces must display it")
    if any(o.get("grade") for o in outs.values()):
        req["certainty"] = ("Certainty of the evidence",
                            "the object holds a GRADE rating")
    if canon.get("published_comparison"):
        req["published_comparison"] = ("Comparison with published synthes",
                                       "the object holds a published-synthesis comparison")
    if canon.get("rob2") or canon.get("risk_of_bias_verdict"):
        req["risk_of_bias"] = ("Risk of bias", "the object holds a risk-of-bias assessment")
    if canon.get("screening"):
        req["screening"] = ("creening", "the object holds a screening record")
    return req


def html_sections(text):
    v = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", text, flags=re.S)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", v))


def word_sections(docmodel):
    return json.dumps(docmodel, ensure_ascii=False)


def check(canon, html_text, docmodel):
    req = manifest(canon)
    h, w = html_sections(html_text), word_sections(docmodel)
    rows = []
    for key, (needle, why) in sorted(req.items()):
        in_h, in_w = needle in h, needle in w
        v = "PASS" if (in_h and in_w) else "FAIL"
        rows.append((key, v, in_h, in_w, why))
    return rows


def selftest() -> int:
    """A constructed failure, per the standard in gate_integrity: delete a section
    from one renderer and require the gate to FAIL. A gate with no constructible
    failing input is not a gate, and that applies to remedies too."""
    ok = True
    R = r"F:\rapidmeta-ssot-shell"
    canon = json.loads(open(os.path.join(R, "ssot", "arni-hfref", "arni-hfref.json"),
                            encoding="utf-8", errors="replace").read())
    html = open(os.path.join(R, "ARNI_HF_REVIEW.html"), encoding="utf-8",
                errors="replace").read()
    dm = json.loads(open(os.path.join(R, "ssot", "arni-hfref", "manuscript_docmodel.json"),
                         encoding="utf-8", errors="replace").read())

    print("  manifest earned by the ARNI object: %s" % sorted(manifest(canon)))
    rows = check(canon, html, dm)
    base_ok = all(v == "PASS" for _, v, _, _, _ in rows)
    print("  NEGATIVE both surfaces as built: %s"
          % ("all sections present" if base_ok else
             "FAILS on %s" % [k for k, v, _, _, _ in rows if v == "FAIL"]))
    ok &= base_ok

    # CONSTRUCTED FAILURE: remove the extraction section from the Word side only.
    broken = json.loads(json.dumps(dm))
    broken["blocks"] = [b for b in broken["blocks"]
                        if "Extracted values, and where each came from"
                        not in json.dumps(b, ensure_ascii=False)]
    removed = len(dm["blocks"]) - len(broken["blocks"])
    rows2 = check(canon, html, broken)
    fired = any(k == "extraction_provenance" and v == "FAIL" for k, v, _, _, _ in rows2)
    print("  POSITIVE extraction section deleted from Word (%d blocks removed): %s"
          % (removed, "FIRES" if fired else "SILENT -- WRONG"))
    ok &= fired and removed > 0
    if removed == 0:
        print("        the fixture removed nothing, so the test proved nothing")
        ok = False

    # CONSTRUCTED FAILURE 2: remove it from the HTML side only.
    html_broken = html.replace("Extracted values, and where each came from", "REMOVED")
    rows3 = check(canon, html_broken, dm)
    fired2 = any(k == "extraction_provenance" and v == "FAIL" for k, v, _, _, _ in rows3)
    print("  POSITIVE extraction section deleted from HTML: %s"
          % ("FIRES" if fired2 else "SILENT -- WRONG"))
    ok &= fired2 and html_broken != html

    print("\nWHAT A FAILURE WOULD LOOK LIKE: a section deleted from one surface and the "
          "gate still passing -- which is the state that hid the extraction table from "
          "every Word manuscript we ever produced.")
    print("-> SELFTEST PASS" if ok else "-> SELFTEST FAILED")
    return 0 if ok else 1


def main() -> int:
    if "--selftest" in sys.argv:
        return selftest()
    # AN EXCEPTION IS NOT A VERDICT (2026-08-17).
    #
    # Called with one argument instead of three, this raised IndexError and the
    # caller scored the traceback as FAIL -- a defect asserted on a page the gate
    # never opened. A crash is neither a pass nor a fail: it is the gate not
    # running, and it takes its own exit code so nobody can read it as either.
    # The audit that mis-called it was mine; both sides are fixed, because a gate
    # that tracebacks on bad input teaches its callers to guess.
    need = ["<object>.json", "<page>.html", "<docmodel>.json"]
    if len(sys.argv) - 1 < len(need):
        print("section_manifest_gate: needs %d arguments, got %d."
              % (len(need), len(sys.argv) - 1), file=sys.stderr)
        print("  usage: section_manifest_gate.py %s" % " ".join(need), file=sys.stderr)
        print("  NOT RUN. This is neither a pass nor a failure of the subject.",
              file=sys.stderr)
        return 2
    for _a in sys.argv[1:4]:
        if not os.path.exists(_a):
            print("section_manifest_gate: %s does not exist. NOT RUN -- not a pass."
                  % _a, file=sys.stderr)
            return 2
    canon = json.loads(open(sys.argv[1], encoding="utf-8", errors="replace").read())
    html = open(sys.argv[2], encoding="utf-8", errors="replace").read()
    dm = json.loads(open(sys.argv[3], encoding="utf-8", errors="replace").read())
    rows = check(canon, html, dm)
    print("%-24s %-6s %-6s %-6s %s" % ("SECTION", "VERDICT", "HTML", "WORD", "WHY EARNED"))
    for k, v, ih, iw, why in rows:
        print("%-24s %-6s %-6s %-6s %s" % (k, v, "yes" if ih else "NO",
                                           "yes" if iw else "NO", why[:60]))
    bad = [k for k, v, _, _, _ in rows if v == "FAIL"]
    print("\n%d section(s) earned; %d missing from a surface" % (len(rows), len(bad)))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
