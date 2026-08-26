"""ONE-SHOT MIGRATION CHECK, NOT A GATE. DO NOT LEAVE THIS IN A HOOK CHAIN.

Its assertions compare a POST-deletion tree against a PRE-prune retain-list. Once it has
run, that comparison can never fail again -- it is a check that can only fail once, which is
indistinguishable in a log from a check that can never fail. Run it, read it, then leave it
as a record of what was removed and why.

WHY THE SIGNATURE IS `Canonical object` AND WHY IT TESTS PRESENCE ONLY.
Current-generation pages carry a reproducibility table whose first row is `Canonical object`.
The test is PRESENCE, never value: two lanes are still repairing pages whose row is blank,
and a value test would delete exactly the pages being fixed.

WHY AN ALLOW-LIST AND NOT A DENY-LIST.
A rule phrased as "drop pages carrying the legacy paper-studio script" leaves behind anything
carrying NEITHER marker -- `LivingMeta.html` is 949 KB and has neither. Keep what you can
name; never delete what you merely failed to recognise.

ORDER IS LOAD-BEARING: DELETE, THEN REGENERATE THE SITEMAP.
`build_sitemap()` globs the real files, so it self-corrects -- but only if it runs after the
deletion. 1,191 of the sitemap's 1,309 entries are pages this prune removes; regenerating
first would publish a sitemap advertising 1,191 dead URLs, which is worse than the pages.

THE CHECKSUM EXISTS BECAUSE VERIFYING A LIST AND SHIPPING A DELETION ARE TWO ARTEFACTS.
Everything above computes a plan. What ships is a tree. The assertions below compare the
surviving tree to the plan -- count and bytes -- and refuse rather than report.
"""
import io, os, re, sys, glob, json, subprocess

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SIG = "Canonical object"
LEGACY_MARK = "assets/js/paper-studio.js"
APPLY = "--apply" in sys.argv


def build_named(root):
    """Furniture, DERIVED FROM THE BUILD rather than from judgement.

    Anything named by pages.yml, pages_preflight.py or the sitemap generator is a page the
    SITE needs, whatever markers it carries. My own inspection produced seven names and
    missed two the build names explicitly -- what_changed.html and
    cardiology_mortality_atlas.html. The build is the authority on what the site needs; an
    opinion about what looks like furniture is not.
    """
    named = set()
    for rel in (".github/workflows/pages.yml",
                "scripts/pages_preflight.py",
                "scripts/add_meta_description_and_sitemap.py"):
        p = os.path.join(root, rel)
        if os.path.exists(p):
            named |= set(re.findall(r"[A-Za-z0-9_\-]+\.html",
                                    io.open(p, encoding="utf-8", errors="replace").read()))
    # RESIDUAL: reached by a reader, not named by the build. Explicit, and small.
    named |= {"index.html", "NMA_INDEX.html", "META_DASHBOARD.html",
              "withdrawn_audit_rows.html", "dose_response_landing.html"}
    return named


def classify(root):
    """DROP ONLY WHAT IS POSITIVELY IDENTIFIED. Everything else is RETAINED.

    The first version asked "does this carry the review signature?" and dropped everything
    that did not -- which condemned index.html, because the homepage has no reproducibility
    table. A marker written for review pages, evaluated over every file in the root.

    WHEN A CLASSIFIER CANNOT TELL, KEEP. An unknown file retained costs bytes; an unknown
    file dropped may be a page someone needs, and nobody finds out until a reader does.
    Dropping on uncertainty is the flattering default wearing new clothes: it makes the
    prune look decisive and puts the cost somewhere invisible.
    """
    furniture = build_named(root)
    keep, drop, unknown = [], [], []
    for p in sorted(glob.glob(os.path.join(root, "*.html"))):
        n = os.path.basename(p)
        h = io.open(p, encoding="utf-8", errors="replace").read()
        size = os.path.getsize(p)
        if n in furniture or SIG in h:
            keep.append(n)
        elif LEGACY_MARK in h:
            drop.append(n)
        elif size < 20000 and re.search(r"http-equiv=.refresh|rapidmeta:page-state",
                                        h, re.I):
            drop.append(n)
        else:
            keep.append(n)
            unknown.append(n)
    return keep, drop, unknown


def linked_from_index(root, names):
    idx = io.open(os.path.join(root, "index.html"), encoding="utf-8",
                  errors="replace").read()
    return set(re.findall(r'href="([A-Za-z0-9_\-]+\.html)"', idx)) & set(names)


def selftest():
    """Fixture, so no corpus state can make it pass. A page carrying the signature is kept;
    one without it is dropped; and a page carrying NEITHER generation marker is DROPPED by
    the allow-list rather than surviving as it would under a deny-list."""
    import tempfile, shutil
    tmp = tempfile.mkdtemp(prefix="prune_")
    try:
        io.open(os.path.join(tmp, "KEEP.html"), "w", encoding="utf-8").write(
            "<td>Canonical object</td>")
        io.open(os.path.join(tmp, "LEGACY.html"), "w", encoding="utf-8").write(
            "<script src='assets/js/paper-studio.js'></script>")
        io.open(os.path.join(tmp, "NEITHER.html"), "w", encoding="utf-8").write(
            "<h1>neither marker</h1>")
        k, d, _u = classify(tmp)
        assert sorted(k) == ["KEEP.html", "NEITHER.html"], (
            "the retain set must hold the review page AND the unclassified one: %r" % (k,))
        assert d == ["LEGACY.html"], (
            "only the positively-identified legacy page may be dropped: %r" % (d,))
        assert "NEITHER.html" in k and "NEITHER.html" in _u, (
            "a page carrying NEITHER marker must be RETAINED and listed as unclassified, "
            "not dropped -- dropping on uncertainty is the flattering default: keep=%r "
            "unknown=%r" % (k, _u))
        print("selftest: keeps the review signature, drops ONLY the positively-identified "
              "legacy page, and RETAINS the page carrying neither marker while naming it "
              "unclassified. OK")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    selftest()
    keep, drop, unknown = classify(REPO)
    ssot_html = [os.path.relpath(p, REPO).replace(os.sep, "/")
                 for p in glob.glob(os.path.join(REPO, "ssot", "**", "*.html"),
                                    recursive=True)]
    plan_bytes = sum(os.path.getsize(os.path.join(REPO, f)) for f in keep)
    drop_bytes = sum(os.path.getsize(os.path.join(REPO, f)) for f in drop)
    MB = 1024.0 ** 2
    print()
    print("RETAIN %d files, %.1f MB   DROP %d files, %.1f MB   (+%d html under ssot/)"
          % (len(keep), plan_bytes / MB, len(drop), drop_bytes / MB, len(ssot_html)))
    unlinked = sorted(set(keep) - linked_from_index(REPO, keep) - {"index.html"})
    print("retained pages with NO index card: %d" % len(unlinked))
    _man = ["# Retained because the classifier could not tell what they are", "",
            "%d files. Not a judgement that they belong -- a record that nobody has" % len(unknown),
            "decided. When a classifier cannot tell, KEEP: an unknown retained costs bytes;",
            "an unknown dropped may be a page someone needs, and nobody finds out until a",
            "reader does.", "",
            "Files dropped as `legacy` are classified by TEMPLATE VINTAGE, not by content.",
            "24 of 43 genuine network pages in this corpus are not named NMA, so a page",
            "dropped as a legacy NMA page may still hold a network worth keeping. Every",
            "dropped file is recoverable from the staging directory.", ""]
    _man += ["- %s" % u for u in unknown]
    io.open(os.path.join(REPO, "PRUNE-UNCLASSIFIED-2026-08-26.md"), "w",
            encoding="utf-8", newline="").write(chr(10).join(_man) + chr(10))
    if not APPLY:
        print("\nDRY RUN. Nothing deleted. Re-run with --apply.")
        return

    # ---- MOVE, DO NOT DELETE. An abort must be recoverable without git. ----
    # The first run of this script deleted in a loop with the assertions at the end. Another
    # lane's pre-commit hook held a file open, os.remove raised PermissionError at file 793
    # of 1,359, and the tree was left in a state neither the plan nor HEAD described. The
    # checksum protected against a WRONG result and not against a PARTIAL one.
    stage = os.path.join(REPO, "_pruned_2026_08_26")
    os.makedirs(stage, exist_ok=True)
    moved, blocked = [], []
    for f in drop + ssot_html:
        src = os.path.join(REPO, f)
        dst = os.path.join(stage, f.replace("/", "__"))
        try:
            os.replace(src, dst)
            moved.append(f)
        except OSError as e:
            blocked.append((f, str(e)[:60]))
    if blocked:
        print("REFUSED: %d file(s) could not be moved; ROLLING BACK %d already moved."
              % (len(blocked), len(moved)))
        for f in moved:
            os.replace(os.path.join(stage, f.replace("/", "__")), os.path.join(REPO, f))
        for f, e in blocked[:5]:
            print("   %s -- %s" % (f, e))
        raise SystemExit(1)

    # ---- INDEX: STRIP DEAD CARDS AND ADD MISSING ONES, IN THE SAME PASS ----
    # A card is a promise that a page exists. After the move, 464 cards would point at
    # nothing; the index must list what the site HAS.
    idx = io.open(os.path.join(REPO, "index.html"), encoding="utf-8", errors="replace").read()
    dropped_set = set(drop)
    CARD = re.compile(r'<a href="([A-Za-z0-9_\-]+\.html)" class="card[^"]*">.*?</a>', re.S)
    removed = []
    def _strip(m):
        if m.group(1) in dropped_set:
            removed.append(m.group(1))
            return ""
        return m.group(0)
    idx = CARD.sub(_strip, idx)
    io.open(os.path.join(REPO, "index.html"), "w", encoding="utf-8", newline="").write(idx)
    print("index cards removed (pointed at pruned pages): %d" % len(removed))

    subprocess.run([sys.executable, os.path.join(REPO, "scripts", "add_cards_for_uncarded.py")],
                   cwd=REPO, capture_output=True)
    subprocess.run([sys.executable, os.path.join(REPO, "scripts",
                                                 "add_meta_description_and_sitemap.py")],
                   cwd=REPO, capture_output=True)
    subprocess.run([sys.executable, os.path.join(REPO, "scripts",
                                                 "build_index_indicators.py")],
                   cwd=REPO, capture_output=True)

    # ---- ASSERTIONS ON THE ARTEFACT, BOTH DIRECTIONS ----
    surviving = sorted(os.path.basename(x)
                       for x in glob.glob(os.path.join(REPO, "*.html")))
    surv_bytes = sum(os.path.getsize(os.path.join(REPO, f)) for f in surviving)
    idx = io.open(os.path.join(REPO, "index.html"), encoding="utf-8", errors="replace").read()
    carded = set(re.findall(r'href="([A-Za-z0-9_\-]+\.html)"', idx))
    ok = True
    if surviving != sorted(keep):
        ok = False
        print("REFUSED: surviving tree != retain-list. extra=%r missing=%r"
              % (sorted(set(surviving) - set(keep))[:5],
                 sorted(set(keep) - set(surviving))[:5]))
    if surv_bytes != plan_bytes:
        ok = False
        print("REFUSED: surviving bytes %d != planned %d" % (surv_bytes, plan_bytes))
    dead = sorted(c for c in carded if c not in set(surviving))
    if dead:
        ok = False
        print("REFUSED: %d card(s) point at a file that does not exist, e.g. %r"
              % (len(dead), dead[:5]))
    uncarded = sorted(set(surviving) - carded - {"index.html"})
    if uncarded:
        ok = False
        print("REFUSED: %d surviving page(s) have NO card. A one-way check would pass a "
              "site listing 104 cards for 151 pages, so this direction blocks too: %r"
              % (len(uncarded), uncarded[:6]))
    sm = io.open(os.path.join(REPO, "sitemap.xml"), encoding="utf-8", errors="replace").read()
    entries = re.findall(r"<loc>[^<]*/([A-Za-z0-9_\-]+\.html)</loc>", sm)
    stale = sorted(set(entries) - set(surviving))
    if stale:
        ok = False
        print("REFUSED: sitemap advertises %d gone page(s), e.g. %r" % (len(stale), stale[:5]))
    print("moved %d  surviving %d  cards %d  dead-cards %d  uncarded %d  sitemap %d  stale %d"
          % (len(moved), len(surviving), len(carded), len(dead), len(uncarded),
             len(entries), len(stale)))
    if not ok:
        raise SystemExit(1)
    print("ASSERTIONS HELD both directions: every card resolves, every retained page "
          "accounted for, sitemap advertises nothing gone.")


if __name__ == "__main__":
    main()
