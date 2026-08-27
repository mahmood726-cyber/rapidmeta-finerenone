"""How many build vintages is the served corpus? Read the stamp, do not assume.

WHY. Stage 2 pre-registered "stamp only" as the expected difference for five pages and was
wrong on four, because I assumed the served corpus was uniformly current. It is not. The
vintage is IN THE SERVED BYTES and could have been read before the expectation was named --
pre-registering an expectation is only worth something if the expectation is derived rather
than assumed.

This turns "is this diff a regression or a catch-up?" from a judgement into a lookup, which
is the same move as data-store for identity and data-artefact for kind, applied to time.

WHAT IS READ. `Generator build <code>SHA</code>` from the reproducibility block, which
build_tabbed writes on every page from `_generator_stamp()`. The suffix matters and is kept:
DIRTY means the page was built from uncommitted generator code and cannot be reproduced from
the sha alone, which is a different state from a clean stamp and must not be pooled with it.

EACH SHA IS RESOLVED, NOT JUST COUNTED. A stamp naming a commit this repository does not
contain is a page whose provenance cannot be checked at all, and that is a third state --
never folded into "old".

CONTROL. SGLT2_HF_REVIEW's served bytes are known to carry 36ae41332: it was rebuilt from
that generator last night and the stage-2 diff showed exactly that one rendered word. The
extractor must reproduce it, and must NOT extract a sha from a page that carries none.
"""
import collections
import io
import json
import os
import re
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "scripts"))
OUT = os.path.join(REPO, "outputs", "stamp_census_2026_08_27.json")

# The real markup is `Generator build</th><td><code>SHA</code>` -- table cells between the
# label and the value. The first version required <code> to follow immediately and matched
# 0 of 163 pages, which is the implausible number that sent me to read the bytes.
STAMP = re.compile(r"Generator build\s*(?:</?[a-z][^>]*>\s*){0,4}<code>"
                   r"([0-9a-fA-F]{6,40})</code>([^<]{0,60})", re.I)


def stamp_of(html):
    """(sha, suffix) or (None, None). Never a guess."""
    m = STAMP.search(html or "")
    if not m:
        return None, None
    return m.group(1), (m.group(2) or "").strip()


def run_controls():
    """Keyed to a REAL served page, not to a string I wrote.

    The first version of this control built its own input from the same assumption as the
    regex -- "Generator build <code>SHA</code>" -- so it passed while the extractor found 0
    of 163 real pages. A control constructed from the code's own premise cannot test that
    premise; it is a tautology wearing a control's name.

    SGLT2_HF_REVIEW's served bytes carry 36ae41332, established outside this script: the RoB
    lane committed that rebuild (784b969a6) and the stage-2 diff showed that exact sha as the
    single differing rendered word.
    """
    from instrument_controls import require_controls
    real = os.path.join(REPO, "SGLT2_HF_REVIEW.html")
    got = stamp_of(io.open(real, encoding="utf-8", errors="replace").read())[0]         if os.path.exists(real) else None
    none_ = "<p>a page with no reproducibility block at all</p>"
    require_controls(
        "stamp_census (extractor)",
        ("the sha in a REAL served page is read back", got, "36ae41332"),
        ("a page carrying no stamp yields one anyway", stamp_of(none_)[0] is not None, True))


def main():
    run_controls()
    raw = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                           write_through=True)

    def log(s):
        raw.write(s + chr(10))
        raw.flush()

    pm = json.load(io.open(os.path.join(REPO, "ssot", "PAGE_MAP.json"), encoding="utf-8"))
    rows, bysha = [], collections.Counter()
    unstamped, dirty = [], []
    for page in sorted(pm):
        fp = os.path.join(REPO, page)
        if not os.path.exists(fp):
            rows.append({"page": page, "state": "NO SERVED FILE"})
            continue
        sha, suf = stamp_of(io.open(fp, encoding="utf-8", errors="replace").read())
        if not sha:
            unstamped.append(page)
            rows.append({"page": page, "state": "UNSTAMPED"})
            continue
        d = bool(suf and ("DIRTY" in suf.upper() or "uncommitted" in suf.lower()))
        if d:
            dirty.append(page)
        bysha[sha] += 1
        rows.append({"page": page, "state": "stamped", "sha": sha, "suffix": suf, "dirty": d})

    # RESOLVE each sha. A stamp naming a commit we do not have is its own state.
    info = {}
    for sha in bysha:
        r = subprocess.run(["git", "log", "-1", "--format=%h|%ad|%s", "--date=format:%m-%d %H:%M",
                            sha], capture_output=True, cwd=REPO)
        if r.returncode != 0:
            info[sha] = ("UNRESOLVABLE", "", "not present in this repository")
            continue
        parts = r.stdout.decode("utf-8", "replace").strip().split("|", 2)
        anc = subprocess.run(["git", "merge-base", "--is-ancestor", sha, "HEAD"],
                             capture_output=True, cwd=REPO).returncode == 0
        info[sha] = (parts[0], parts[1] if len(parts) > 1 else "",
                     ("ancestor" if anc else "NOT an ancestor of HEAD") + " -- " +
                     (parts[2] if len(parts) > 2 else "")[:52])

    n = len([r for r in rows if r.get("state") == "stamped"])
    log("pages in PAGE_MAP        : %d" % len(pm))
    log("stamped                  : %d" % n)
    log("UNSTAMPED                : %d" % len(unstamped))
    log("built from a DIRTY tree  : %d" % len(dirty))
    log("distinct generator shas  : %d" % len(bysha))
    log("")
    log("%-11s %6s  %-13s %s" % ("sha", "pages", "committed", "state"))
    for sha, cnt in bysha.most_common():
        h, d, st = info[sha]
        log("%-11s %6d  %-13s %s" % (sha, cnt, d, st[:64]))
    if unstamped:
        log("")
        log("UNSTAMPED pages (%d): %s" % (len(unstamped), ", ".join(unstamped[:6])))
    if dirty:
        log("")
        log("DIRTY-tree pages (%d): %s" % (len(dirty), ", ".join(dirty[:6])))
    log("")
    log("A page's vintage is now a lookup. A rebuild diff against a page N generations")
    log("behind should show the deltas of those N generations -- not 'the stamp only'.")

    json.dump({"question": "how many build vintages is the served corpus",
               "n_pages": len(pm), "stamped": n, "unstamped": unstamped, "dirty": dirty,
               "by_sha": {k: {"pages": v, "resolved": info[k]} for k, v in bysha.items()},
               "rows": rows},
              io.open(OUT, "w", encoding="utf-8"), indent=1)
    log("wrote %s" % os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    sys.exit(main())
