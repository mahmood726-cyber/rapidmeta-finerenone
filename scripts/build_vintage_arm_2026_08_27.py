"""Population C, vintage arm: the OLD generator against the CURRENT object.

WHY TWO BUILDS. Population C is 99 pages where BOTH the generator and the object moved since
the page was served. A single diff against served bytes therefore has two causes and cannot
attribute either. Building each page twice separates them by construction:

    vintage generator (2c0cf3bf0) + CURRENT object   -> isolates what the STORE changed
    HEAD generator                + CURRENT object   -> the page we would serve

    served vs vintage-arm   = the object's contribution
    vintage-arm vs HEAD-arm = the generator's contribution

That is a two-cause difference made single-cause by construction rather than by argument,
which is the only version worth acting on.

THE OBJECT PATH IS PASSED, NOT COPIED. build_tabbed takes the object as an argument, so the
old generator reads today's object directly out of the working worktree. Nothing is copied
into the vintage tree, so the vintage tree stays exactly what git says it is.

NO PIN AT THIS VINTAGE. REQUIRED_GENERATOR_COMMITS did not exist at 2c0cf3bf0, so the
ancestor gate cannot run there -- which is itself worth knowing: the 123 pages served from
that generator were built with no generator-pin protection at all. Nothing from this arm is
ever served; it exists only as a comparison baseline.
"""
import io
import os
import subprocess
import sys
import time

GEN = r"F:\claude-temp\wt\genstore"
VINTAGE = r"F:\claude-temp\wt\vintage-2c0"
OUT = (r"F:\claude-temp\claude\F--rapidmeta-finerenone"
       r"\e2e2a1d5-c19e-44de-90ab-690dbc5235a1\scratchpad\vintage_arm")


def main():
    listfile = sys.argv[1]
    out = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                           write_through=True)

    def say(s):
        out.write(s + chr(10))
        out.flush()

    os.makedirs(OUT, exist_ok=True)
    items = []
    for line in io.open(listfile, encoding="utf-8"):
        p = line.rstrip(chr(10)).split(chr(9))
        if len(p) >= 2 and p[0].strip():
            items.append((p[0].strip(), p[1].strip()))

    say("vintage arm: %d page(s)  generator=2c0cf3bf0  objects=CURRENT" % len(items))
    ok = fail = 0
    for i, (page, obj) in enumerate(items, 1):
        dst = os.path.join(OUT, page)
        if os.path.exists(dst) and os.path.getsize(dst) > 10000:
            ok += 1
            continue
        t0 = time.time()
        r = subprocess.run([sys.executable, "build_tabbed.py",
                            os.path.join(GEN, obj), dst],
                           cwd=os.path.join(VINTAGE, "ssot"),
                           capture_output=True, timeout=1800)
        if r.returncode == 0 and os.path.exists(dst):
            ok += 1
            say("[%3d/%d] %-46s ok %.0fs" % (i, len(items), page[:46], time.time() - t0))
        else:
            fail += 1
            say("[%3d/%d] %-46s FAILED %s" % (i, len(items), page[:46],
                (r.stderr or b"").decode("utf-8", "replace")[-90:]))
    say("")
    say("vintage arm built %d   failed %d" % (ok, fail))
    return 0


if __name__ == "__main__":
    sys.exit(main())
