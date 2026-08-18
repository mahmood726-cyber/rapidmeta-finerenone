"""THE PROJECTOR: write a topic page's values from its canonical object, or refuse.

This is the straight path's missing final segment. Before this, nothing in the repository
turned an object into a page: `PAGE_MAP` is a registry of correspondence, and the
`tabbed_build` property is "checkbuild-equivalent" -- established for pages built through a
path, with no runnable checker for a page already on disk.

THREE INVARIANTS, EACH EARNED THIS WEEK.

  1. THE BLOCK LIST COMES FROM THE OBJECT, NOT FROM THIS CODE.
     The object carries `render: [{block, slot, path}, ...]`. This module maps a BLOCK
     TYPE to a formatter and knows nothing about which blocks a topic has. Adding a
     seventh block later is DATA. If this file hardcoded five, adding a sixth would be a
     rewrite -- and a projector whose property model cannot grow is the thing that would
     have to be rewritten when the methods work lands.

  2. A MISSING VALUE IS A REFUSAL, NEVER A PLACEHOLDER.
     If a declared block names a path the object does not carry, this raises. It does not
     substitute a default, an em-dash, or an empty string. AN OMITTED FIELD IS DATA; A
     DEFAULTED FIELD IS A LIE -- the same rule that governs the objects, arriving at the
     rendering layer. A renderer that can invent a value can diverge from its object, and
     the whole point of this file is that it structurally cannot.

  3. ALL OR NOTHING.
     Every block is formatted and every slot located BEFORE a single byte is written. A
     page half-filled from an object is worse than an empty one: a reader cannot tell
     which values came from the object and which are still placeholders, and the page
     would assert a provenance it only partly has.

AND THE PATTERN IS BORROWED DELIBERATELY from F:\\allmeta\\audit\\render.py -- one
canonical input, N renderers, no renderer holding data of its own. That signature is what
makes the multi-route defect structurally impossible rather than merely discouraged.

DONE IS NOT "A FILE WAS WRITTEN". Done is the LIVE page rendering the object's values,
cache-busted. This module writes; it does not confirm.
"""
from __future__ import annotations
import io
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STAMP_ID = "projector-build-stamp"


class Refused(Exception):
    """Raised instead of writing anything. Never caught inside this module."""


def dig(obj, path):
    """Fetch obj at a dotted path. RAISES if any segment is absent."""
    cur = obj
    for seg in path.split("."):
        if isinstance(cur, list):
            try:
                cur = cur[int(seg)]
                continue
            except (ValueError, IndexError):
                raise Refused("path %r: index %r not present" % (path, seg))
        if not isinstance(cur, dict) or seg not in cur:
            raise Refused("path %r: segment %r not present in the object" % (path, seg))
        cur = cur[seg]
    if cur is None:
        raise Refused("path %r resolves to null -- a null is an absence, not a value"
                      % path)
    return cur


# ---- BLOCK FORMATTERS. Each is a pure function of values dug from the object. ----
def _fmt_effect(o, spec):
    v = dig(o, spec["path"])
    return "%.2f" % v if isinstance(v, (int, float)) else str(v)


def _fmt_interval(o, spec):
    lo = dig(o, spec["path_low"])
    hi = dig(o, spec["path_high"])
    return "%.2f to %.2f" % (lo, hi)


def _fmt_percent(o, spec):
    return "%.1f%%" % dig(o, spec["path"])


def _fmt_text(o, spec):
    return str(dig(o, spec["path"]))


def _fmt_count(o, spec):
    return str(int(dig(o, spec["path"])))


FORMATTERS = {"effect": _fmt_effect, "interval": _fmt_interval,
              "percent": _fmt_percent, "text": _fmt_text, "count": _fmt_count}


def project(page_path: str, obj_path: str, *, commit: str, dry_run: bool = True):
    obj = json.load(io.open(obj_path, encoding="utf-8"))
    blocks = obj.get("render")
    if not blocks:
        raise Refused("the object declares no `render` list. THE BLOCK LIST IS THE "
                      "OBJECT'S TO DECLARE -- this projector will not invent one.")

    raw = open(page_path, "rb").read()
    html = raw.decode("utf-8", "replace")

    # PASS 1 -- format every block and locate every slot. Nothing is written yet.
    planned = []
    for spec in blocks:
        btype, slot = spec.get("block"), spec.get("slot")
        if btype not in FORMATTERS:
            raise Refused("unknown block type %r. Add a formatter deliberately; do not "
                          "let an unknown block render as empty." % btype)
        value = FORMATTERS[btype](obj, spec)          # raises on any missing path
        pat = re.compile(r'(<[^<>]*id="%s"[^<>]*>)\s*--\s*(</)' % re.escape(slot))
        if not pat.search(html):
            raise Refused("slot id=%r not found on the page carrying a `--` placeholder. "
                          "The page may already be filled, or the slot may not exist; "
                          "either way this projector will not guess." % slot)
        planned.append((pat, value, slot, btype))

    # PASS 2 -- apply. Only reached if every block formatted and every slot resolved.
    out = html
    for pat, value, slot, _ in planned:
        out, n = pat.subn(lambda m: m.group(1) + value + m.group(2), out, count=1)
        if n != 1:
            raise Refused("slot %r did not substitute exactly once" % slot)

    stamp = ('<div id="%s" data-object="%s" data-commit="%s" hidden>'
             'projected from %s at %s</div>'
             % (STAMP_ID, os.path.relpath(obj_path, REPO), commit,
                os.path.relpath(obj_path, REPO), commit))
    if STAMP_ID in out:
        out = re.sub(r'<div id="%s".*?</div>' % STAMP_ID, stamp, out, flags=re.S)
    else:
        # THE LAST </body>, NOT THE FIRST, AND ONLY IF IT IS OUTSIDE <script>.
        # This page holds FOUR "</body>" strings and the first sits inside a
        # JavaScript string literal. Inserting there produced
        # "Unexpected identifier 'projector'" and the page rendered zero studies.
        # The pre-push regression gate caught it. FIRST MATCH IS NOT THE RIGHT
        # MATCH -- the same family as substring-is-not-identity.
        idx = -1
        for m in re.finditer(r"</body>", out):
            i = m.start()
            if out.rfind("<script", 0, i) <= out.rfind("</script>", 0, i):
                idx = i          # outside any script block
        if idx < 0:
            raise Refused("no </body> outside a <script> block, and no existing stamp. "
                          "This page holds %d </body> strings, all inside script; there "
                          "is nowhere safe to record provenance, and an unstamped page "
                          "cannot be told from a hand-edited one."
                          % out.count("</body>"))
        out = out[:idx] + stamp + out[idx:]

    if out.count("\r\n") != raw.decode("utf-8", "replace").count("\r\n"):
        raise Refused("line-ending count changed")
    if out.count("</script>") != html.count("</script>"):
        raise Refused("script count changed")
    si = out.find(STAMP_ID)
    if si >= 0 and out.rfind("<script", 0, si) > out.rfind("</script>", 0, si):
        raise Refused("the build stamp landed INSIDE a <script> block -- this is the "
                      "defect the regression gate caught on 2026-08-18 and it is now "
                      "structurally refused rather than merely avoided.")

    # MEASURE IN BYTES ON BOTH SIDES. The first version compared len(str) to
    # len(bytes) and reported a 16,291-byte "shrink" on a page that grew by 45 --
    # non-ASCII characters are multi-byte. An alarming number from a unit mismatch,
    # which is the shape that has produced every instrument artefact this week.
    out_bytes = out.encode("utf-8")
    if not dry_run:
        open(page_path, "wb").write(out_bytes)
    return [(s, v, b) for _, v, s, b in planned], len(out_bytes) - len(raw)


def main() -> int:
    import subprocess
    args = sys.argv[1:]
    apply_it = "--apply" in args
    args = [a for a in args if a != "--apply"]
    if len(args) != 2:
        print("usage: project_topic_page.py <page.html> <object.json> [--apply]")
        return 2
    page, obj = args
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                            capture_output=True).stdout.decode("utf-8").strip() or "UNKNOWN"
    try:
        done, delta = project(os.path.join(REPO, page), os.path.join(REPO, obj),
                              commit=commit, dry_run=not apply_it)
    except Refused as e:
        print("REFUSED -- nothing written.")
        print("   %s" % e)
        return 1
    print("%s %d block(s), %+d bytes" % ("WROTE" if apply_it else "DRY RUN",
                                         len(done), delta))
    for slot, value, btype in done:
        print("   %-16s %-10s %s" % (slot, btype, value))
    if not apply_it:
        print("\n(dry run -- pass --apply to write)")
    else:
        print("\nWRITTEN IS NOT DELIVERED. Done is the LIVE page rendering these values, "
              "cache-busted.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
