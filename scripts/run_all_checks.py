"""One entry point for every validated check, so another lane can run them at scale.

  python scripts/run_all_checks.py --object <obj.json> [--page <page.html>]
                                   [--docx <f.docx> --docmodel <m.json>]
  python scripts/run_all_checks.py --selftest        # every gate's own self-test

Exit code is the number of checks that FAILED, so a batch runner can sum it.
Each check prints its own verdict; nothing is summarised away.

APPLICABILITY IS ENFORCED, not assumed. A check that cannot run against a given
artefact reports SKIPPED with the reason. It never reports a pass it did not
earn -- the failure mode this whole suite exists to prevent is a green result
produced by measuring the wrong thing, or nothing.

See DEFECT_CLASSES.md for what each check is looking for and why.
"""
import io
import os
import subprocess
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
HERE = os.path.dirname(os.path.abspath(__file__))


def run(label, argv, ok_codes=(0,), skip_codes=()):
    print("\n" + "=" * 74)
    print(label)
    print("=" * 74)
    try:
        r = subprocess.run([sys.executable] + argv, capture_output=True,
                           text=True, encoding="utf-8", errors="replace",
                           timeout=1800)
    except subprocess.TimeoutExpired:
        print("TIMEOUT")
        return 1
    out = (r.stdout or "") + (r.stderr or "")
    print(out.strip()[-3000:])
    if r.returncode in skip_codes:
        print("-> SKIPPED (not applicable to this artefact)")
        return 0
    verdict = "PASS" if r.returncode in ok_codes else "FAIL"
    print("-> %s (exit %d)" % (verdict, r.returncode))
    return 0 if verdict == "PASS" else 1


def main(argv):
    a = dict()
    k = None
    for tok in argv:
        if tok.startswith("--"):
            k = tok[2:]
            a[k] = True
        elif k:
            a[k] = tok
            k = None
    fails = 0

    if a.get("selftest"):
        fails += run("k-consistency gate -- self-test",
                     [os.path.join(HERE, "k_consistency_gate.py"), "--selftest"])
        fails += run("alignment gate -- self-test",
                     [os.path.join(HERE, "alignment_gate.py"), "--selftest"])
        fails += run("verdict type -- self-test",
                     [os.path.join(HERE, "verdict.py")])
        fails += run("identity gate -- self-test",
                     [os.path.join(HERE, "identity_gate.py"), "--selftest"])
        fails += run("prose-claim gate -- self-test",
                     [os.path.join(HERE, "prose_claim_gate.py"), "--selftest"])
        fails += run("citation-year gate -- self-test",
                     [os.path.join(HERE, "citation_year_gate.py"), "--selftest"])
        print("\n%d self-test(s) FAILED" % fails)
        return fails

    if a.get("selftest") is None and a.get("object"):
        pass
    obj = a.get("object")
    if obj and obj is not True:
        fails += run("k-consistency gate (numeric + textual k)",
                     [os.path.join(HERE, "k_consistency_gate.py"), obj])
        # exit 2 = INVALID present, which is NOT a pass: see verdict.py.
        fails += run("identity gate (registration verified in the source doc)",
                     [os.path.join(HERE, "identity_gate.py"), obj,
                      "--sources", os.path.join(os.path.dirname(obj), "sources")])
        fails += run("prose-claim gate (direction / existence claims)",
                     [os.path.join(HERE, "prose_claim_gate.py"), obj])
        fails += run("citation-year gate (issue year, not the epub date)",
                     [os.path.join(HERE, "citation_year_gate.py"), obj])

    page = a.get("page")
    if page and page is not True:
        # exit 2 = unrecognised/unauditable structure, which is a legitimate
        # SKIP rather than a failure: see the Plotly note in DEFECT_CLASSES.md.
        fails += run("figure audit (series / axes / caption promises)",
                     [os.path.join(HERE, "figure_audit.py"), page],
                     skip_codes=(2,))

    dm, dx = a.get("docmodel"), a.get("docx")
    if dm and dx and page and dm is not True and dx is not True:
        fails += run("alignment gate (docmodel <-> .docx <-> page)",
                     [os.path.join(HERE, "alignment_gate.py"), dm, dx, page])

    print("\n" + "#" * 74)
    print("TOTAL CHECKS FAILED: %d" % fails)
    return fails


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
