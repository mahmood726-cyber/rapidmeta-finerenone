#!/usr/bin/env python3
"""SERVED-BYTES A/B ACROSS THE TRUE 155, for the two classes shipped on an understated radius.

gate7 filed `statement.py` at radius 6 and `projectors2.py` at 5 because its closure test
compared forward slashes against backslashes. Both are radius 155. The changes were approved
on the small numbers, so what has never been checked is the other 149.

METHOD, and it isolates the two files rather than the branch. A = HEAD with ONLY those two
files reverted to their pre-change versions; B = HEAD as-is. Everything else -- the forest
caption, the GRADE change, every object -- is held constant, so a difference is attributable
to these two files and nothing else.

Rendered text, not bytes: a build regenerates figs/, and byte-identity is the wrong
restoration test for a page carrying rasters. Each page gets its OWN output directory, so no
two parallel builds race on the same figs/ and both arms are symmetric.

ONE OUTPUT FILE PER PAGE, deleted first, existence asserted. A loop that reuses one output
path reported identical text for nine different pages earlier in this run.
"""
import concurrent.futures as cf
import hashlib
import html as _h
import io
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "gates"))
import _harness as H                                          # noqa: E402

ARM = sys.argv[1]                                             # "A" or "B"
OUT = os.path.join(ROOT, "scratch_ab", ARM)
WORKERS = 3


def rendered(path):
    s = io.open(path, encoding="utf-8", errors="replace").read()
    s = re.sub(r"(?is)<(script|style).*?</\1>", " ", s)
    return re.sub(r"\s+", " ", _h.unescape(re.sub(r"<[^>]+>", " ", s))).strip()


def one(obj):
    tid = H.topic_id(obj)
    d = os.path.join(OUT, tid)
    os.makedirs(d, exist_ok=True)
    page = os.path.join(d, "page.html")
    txt = os.path.join(OUT, tid + ".txt")
    for p in (page, txt):
        if os.path.exists(p):
            os.remove(p)
    # NO text=True. It decodes with the locale codec, which is cp1252 here, and the builder
    # prints tau-squared and a download glyph -- so the first non-ASCII byte in a REFUSAL
    # message would raise UnicodeDecodeError and lose the reason the build failed. Decode
    # explicitly. scripts/lint_subprocess_decode.py refused this commit for exactly this and
    # was right: 17 sites against a baseline of 16, and the new one was mine.
    r = subprocess.run([sys.executable, os.path.join(ROOT, "ssot", "build_tabbed.py"),
                        obj, page], capture_output=True, cwd=ROOT)
    if not os.path.exists(page):
        # A REFUSAL IS NOT A ZERO. do_not_rebuild refuses ARNI by design; it must appear in
        # the coverage number by name, never shrink the denominator silently.
        why = (r.stdout + r.stderr).decode("utf-8", "replace").strip().splitlines()
        return tid, None, (why[-1][:160] if why else "no page and no message")
    t = rendered(page)
    io.open(txt, "w", encoding="utf-8").write(t)
    assert os.path.exists(txt)
    return tid, hashlib.sha256(t.encode("utf-8")).hexdigest(), None


def main():
    objs, _ = H.topic_objects(ROOT)
    res, refused = {}, {}
    with cf.ThreadPoolExecutor(max_workers=WORKERS) as ex:
        for i, (tid, h, why) in enumerate(ex.map(one, objs), 1):
            if h is None:
                refused[tid] = why
            else:
                res[tid] = h
            if i % 20 == 0:
                print("  %s: %d/%d" % (ARM, i, len(objs)), flush=True)
    json.dump({"arm": ARM, "built": res, "refused": refused,
               "expected": len(objs)},
              io.open(os.path.join(ROOT, "out", "ab155_%s.json" % ARM), "w",
                      encoding="utf-8"), indent=1)
    print("ARM %s: expected %d | built %d | refused %d %s"
          % (ARM, len(objs), len(res), len(refused), list(refused)))


if __name__ == "__main__":
    sys.exit(main())
