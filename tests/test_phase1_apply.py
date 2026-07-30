#!/usr/bin/env python
"""
REAL --apply idempotence test on representative apps.

Gate requirement: "a REAL --apply idempotence + double-apply test must pass on a representative
sample (incl. an e156-submission pretty-printed app and a root minified app)".

The selftest exercises synthetic fixtures. This exercises the actual corpus files, through the
actual `--apply` write path, in a scratch tree OUTSIDE the repo. It asserts:

  * apply once  -> the guards are really in (T3 fired, low-fallback gone, sentinel present)
  * apply twice -> byte-identical (true idempotence through the write path, not just in memory)
  * CRLF and BOM survive the round trip
  * the PRETTY-PRINTED e156-submission shape gets REAL guards, not a sentinel over nothing
  * a file whose safeRob cannot be reached is REFUSED, not emitted

    python tests/test_phase1_apply.py
"""
from __future__ import annotations

import io
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

if not getattr(sys.stdout, "_rm_wrapped", False):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    try:
        sys.stdout._rm_wrapped = True
    except AttributeError:
        pass

ROOT = Path(__file__).resolve().parent.parent
PATCHER = ROOT / "scripts" / "phase1_engine_patch.py"


def pick_samples():
    """One minified root app, one pretty-printed e156-submission app, plus a NO_DATA app."""
    out = []
    root_pref = ["APIXABAN_ACS_AUTO_FULL_REVIEW.html", "PCSK9_REVIEW.html",
                 "LISINOPRIL_HTN_AUTO_FULL_REVIEW.html"]
    for n in root_pref:
        p = ROOT / n
        if p.exists():
            out.append(p)
    sub = sorted((ROOT / "e156-submission" / "assets").glob("*_REVIEW.html"))
    sub = [p for p in sub if p.stat().st_size >= 20000]
    out.extend(sub[:2])
    return out


def line_endings(b: bytes):
    crlf = b.count(b"\r\n")
    lf = b.count(b"\n") - crlf
    return crlf, lf


def run(args, cwd):
    p = subprocess.run([sys.executable, str(PATCHER)] + args, cwd=str(cwd),
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def main():
    samples = pick_samples()
    print("=" * 78)
    print("PHASE-1 REAL --apply IDEMPOTENCE TEST")
    print("=" * 78)
    if not samples:
        print("no sample apps found"); return 2
    for s in samples:
        print(f"  sample: {s.relative_to(ROOT)}  ({s.stat().st_size:,} B)")

    ok = True
    tmp = Path(tempfile.mkdtemp(prefix="rm_p1_apply_"))
    try:
        # scratch tree OUTSIDE the repo, preserving the sub-directory shape
        for s in samples:
            rel = s.relative_to(ROOT)
            dest = tmp / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(s, dest)

        before = {p: p.read_bytes() for p in sorted(tmp.rglob("*_REVIEW.html"))}

        rc1, out1 = run(["--apply", "--root", str(tmp), "--report", str(tmp / "r1.json")], ROOT)
        after1 = {p: p.read_bytes() for p in sorted(tmp.rglob("*_REVIEW.html"))}
        rc2, out2 = run(["--apply", "--root", str(tmp), "--report", str(tmp / "r2.json")], ROOT)
        after2 = {p: p.read_bytes() for p in sorted(tmp.rglob("*_REVIEW.html"))}

        checks = [("apply #1 exits 0", rc1 == 0), ("apply #2 exits 0", rc2 == 0)]
        refused = re.search(r"REFUSED \(fail-closed\) : (\d+)", out1)
        checks.append(("apply #1 refused nothing in the sample",
                       refused is None or refused.group(1) == "0"))

        for p in sorted(after1):
            rel = str(p.relative_to(tmp))
            b0, b1, b2 = before[p], after1[p], after2[p]
            t1 = b1.decode("utf-8-sig", errors="replace")
            crlf0, lf0 = line_endings(b0)
            crlf1, lf1 = line_endings(b1)
            checks += [
                (f"{rel}: modified by apply #1", b1 != b0),
                (f"{rel}: DOUBLE-APPLY is byte-identical", b2 == b1),
                (f"{rel}: exactly one sentinel", t1.count("RM-PHASE1-GUARDS v1 BEGIN") == 1),
                (f"{rel}: guard library really inlined", "root.RapidMetaGuards = api" in t1),
                (f"{rel}: safeRob low-fallback GONE (minified form)",
                 'valid.includes(r)?r:"low"' not in t1),
                (f"{rel}: safeRob low-fallback GONE (pretty form)",
                 "valid.includes(r) ? r : 'low'" not in t1),
                (f"{rel}: safeRob now falls back to 'some'", '??"some"' in t1),
                (f"{rel}: BOM preserved",
                 b0.startswith(b"\xef\xbb\xbf") == b1.startswith(b"\xef\xbb\xbf")),
                (f"{rel}: CRLF ratio preserved",
                 (crlf0 == 0) == (crlf1 == 0)),
            ]

        # fail-closed: a file that defines safeRob in an unreachable shape must be REFUSED
        bad = tmp / "UNREACHABLE_REVIEW.html"
        bad.write_text(
            "<html><body>" + ("x" * 20001)
            + '<div id="rapidmeta-integrity-badge">x</div>'
            + "<script>window.__verdict={};var safeRob = function (rob) { return rob; };</script>"
            + "</body></html>", encoding="utf-8", newline="")
        raw_before = bad.read_bytes()
        rc3, out3 = run(["--apply", "--root", str(tmp), "--report", str(tmp / "r3.json")], ROOT)
        checks += [
            ("unreachable-safeRob file is REFUSED", "REFUSED (fail-closed)" in out3),
            ("unreachable-safeRob file is left UNTOUCHED", bad.read_bytes() == raw_before),
            ("no sentinel leaked into the refused file",
             "RM-PHASE1-GUARDS" not in bad.read_text(encoding="utf-8")),
            ("the other files stayed idempotent on run #3",
             all(p.read_bytes() == after1[p] for p in after1)),
        ]

        for label, res in checks:
            print(f"  [{'OK  ' if res else 'FAIL'}] {label}")
            ok &= bool(res)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print("-" * 78)
    print("VERDICT:", "APPLY TEST PASS" if ok else "APPLY TEST FAIL")
    print("=" * 78)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
