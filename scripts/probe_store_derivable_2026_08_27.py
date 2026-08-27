"""Is a page's store path derivable from its app_id, or must it be passed in?

The store-path emission has two possible designs and this decides between them before
either is written:

  DERIVE   build_tabbed reconstructs "ssot/<app_id>/<app_id>.json" from the object it
           already holds. One line, no caller changes -- and silently wrong for any object
           whose file does not follow the convention.
  PASS IN  the driver hands the real path down. Correct by construction, touches callers.

An arithmetic expectation, carried in before looking: PAGE_MAP is the authority, so if the
convention held universally the mapping would be redundant and would probably not exist.
Some mismatch is therefore expected, and the question is how much.
"""
import io
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def norm(p):
    return (p or "").replace(chr(92), "/").strip().lower()


def main():
    pm = json.load(io.open(os.path.join(REPO, "ssot", "PAGE_MAP.json"), encoding="utf-8"))
    tot = len(pm)
    ok = mismatch = noid = unreadable = 0
    ex = []
    for page, path in pm.items():
        full = os.path.join(REPO, path)
        if not os.path.exists(full):
            unreadable += 1
            continue
        try:
            o = json.load(io.open(full, encoding="utf-8"))
        except (ValueError, OSError):
            unreadable += 1
            continue
        a = o.get("app_id")
        if not a:
            noid += 1
            continue
        derived = "ssot/%s/%s.json" % (a, a)
        if norm(derived) == norm(path):
            ok += 1
        else:
            mismatch += 1
            if len(ex) < 5:
                ex.append((page, path, derived))

    out = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                           write_through=True)

    def log(s):
        out.write(s + chr(10))

    log("PAGE_MAP entries            : %d" % tot)
    log("derivation from app_id HOLDS: %d / %d  (%.1f%%)" % (ok, tot, 100.0 * ok / tot))
    log("app_id present but MISMATCH : %d / %d" % (mismatch, tot))
    log("object carries no app_id    : %d / %d" % (noid, tot))
    log("object unreadable / absent  : %d / %d" % (unreadable, tot))
    log("")
    for p, stored, derived in ex:
        log("  mismatch %s" % p)
        log("     stored  %s" % stored)
        log("     derived %s" % derived)
    if mismatch or noid:
        log("")
        log("DERIVATION IS NOT SAFE for %d of %d pages. The path must be passed in, or the"
            % (mismatch + noid, tot))
        log("emission must refuse for those pages rather than assert a path that is wrong.")
    else:
        log("")
        log("Derivation holds for every entry -- but PAGE_MAP existing at all is evidence it")
        log("was not always so, and a convention is not a contract.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
