#!/usr/bin/env python
"""Regression check across all 53 apps after the recent changes:
  - living-MA fix (b929e52)
  - 4+4+4 new-topic clones (4f59c67, 306b52c, 35a72ab)
  - WebR validator injection (138b90e)
  - P1/P2 batch v1.1 protocols (f305b52)
  - P0 editor-review banner + taxonomy (8befc5f)

For each app, verifies 7 signals:
  1. Page loads without pageerror events
  2. RapidMeta.state.trials present, count >= 1
  3. Auto-include trials are in 'include' status
  4. Provisional RoB+GRADE banner present + correct wording
  5. Protocol link no longer points to arni_hf_protocol (except ARNI_HF itself)
  6. webr-validator.js script tag present
  7. Analysis tab pool computes (res-or is a finite number, not '--')
Outputs: 53/53 PASS or list of failures per signal.
"""
import io
import json
import os
import subprocess
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
SKIP = {"LivingMeta.html", "META_DASHBOARD.html", "AutoGRADE.html", "AutoManuscript.html"}

# SCOPE. The header claimed 53 apps; the glob returns every *_REVIEW.html in the
# repo, which is 1449, so the "~60 second" hook was in fact an hours-long walk and
# that is why it hung. `--only` restricts the walk to named pages, which lets the
# pre-push hook check exactly the pages a push touches instead of the whole corpus.
# `--only` present at all means the caller is naming the scope. An EMPTY list then
# means "no pages in scope", not "every page" -- the first cut fell through to the
# full 1449-page walk on `--only` with no arguments, which is the same failure the
# hook had: a flag that cannot restrict is not a scope.
_scoped = "--only" in sys.argv
_only = []
if _scoped:
    _i = sys.argv.index("--only")
    _only = [a.replace(".html", "") for a in sys.argv[_i + 1:] if a.endswith(".html")
             or a.endswith("_REVIEW")]

apps = sorted([p.name.replace('.html', '') for p in ROOT.glob("*_REVIEW.html")])
if _scoped:
    apps = [a for a in apps if a in set(_only)]
print(f"Regression checking {len(apps)} apps"
      + (" (scoped by --only)" if _scoped else ""))
if not apps:
    print("No app pages in scope for this run.")
    sys.exit(0)

sys.path.insert(0, str(Path(__file__).resolve().parent))
import re as _re2                       # noqa: E402
import ssot_signals as _ssot            # noqa: E402
import hashlib as _hl                   # noqa: E402
import pathlib as _pl                   # noqa: E402

_ARCHIVE = _pl.Path(r"F:\E156\outputs\corpus-archive\pages")

# THE PORT IS AN ARGUMENT, AND THE SERVER'S IDENTITY IS CHECKED (2026-08-17).
#
# This gate hardcoded port 8787. On that date the port was served by the SIBLING
# WORKING TREE of this same repository, on a different branch, so every
# regression verdict of the day was measured against files that were not the
# ones being pushed: ARNI was 912,140 bytes over the wire against 6,147,695 on
# disk.
#
# The hook's probe was `curl -sf .../index.html`, which establishes that
# SOMETHING answers. It never established that the something was THIS repo --
# liveness versus identity -- and it produced false LIFE rather than false
# death: a green gate that had never seen the files being pushed.
_PORT = int(os.environ.get("RM_PORT", "8787"))
if "--port" in sys.argv:
    _PORT = int(sys.argv[sys.argv.index("--port") + 1])


def _assert_server_identity():
    """Refuse to run unless the server is serving THIS working tree.

    A NONCE written here and fetched over HTTP is the only probe a different
    directory cannot satisfy: it did not exist anywhere a moment ago. Comparing
    the size or hash of an existing page would pass the instant two trees
    happened to agree on that one file.
    """
    import urllib.request as _u, uuid as _uu
    nonce = "._rm_identity_%s" % _uu.uuid4().hex[:12]
    f = ROOT / nonce
    f.write_text("identity-probe", encoding="utf-8")
    try:
        with _u.urlopen("http://127.0.0.1:%d/%s" % (_PORT, nonce), timeout=5) as r:
            served = r.read().decode("utf-8", "replace").strip()
        if served != "identity-probe":
            raise RuntimeError("served %r" % served[:40])
    except Exception as ex:                                  # noqa: BLE001
        print("REFUSING TO RUN: the server on port %d is NOT serving %s (%s)."
              % (_PORT, ROOT, ex))
        print("A gate that reads another directory's bytes is worse than no gate: "
              "it reports PASS having never seen the files being pushed.")
        sys.exit(2)
    finally:
        try:
            f.unlink()
        except OSError:
            pass


# THE SETTLE WINDOW. 12s was where a cold load finished rendering its included
# studies on 2026-08-17 (0 at 2.5s, 0 at 6s, 7 at 12s). Overridable, because a
# constant tuned on one machine on one day is a guess everywhere else.
_SETTLE_MS = int(os.environ.get("RM_SETTLE_MS", "10000"))
# WHAT THIS COUNTS, AND WHY IT CHANGED (2026-08-17).
#
# It counted trials whose SCREENING STATUS is "include". Measured against the
# correct tree that fired on 28 of 51 pages -- and it was wrong. Those pages
# carry 4, 5 and 3 ANALYSED trials with data and compute pooled estimates from
# them (0.96, 7.36); the AUTO generation simply does not mark its analysed set
# with that status field. I renamed this signal so it would describe what it
# observes and then left it reading the wrong field, which made it honest about
# the sampling WINDOW and still dishonest about the SUBJECT. Third instance in
# one day of a check reporting something other than what it measures, and the
# only one of the three that was mine.
#
# It now counts the ANALYSED SET -- trials carrying the arm data the pool is
# computed from -- because that is what "this review has studies behind its
# estimate" actually means to a reader. Screening status is accepted as well,
# so a page that does mark inclusion that way still counts.
_INCL_JS = ("""(()=>{const tr=(window.RapidMeta&&RapidMeta.state&&RapidMeta.state.trials)||[];
  const analysed = tr.filter(t => {
    const d = t.data || {};
    const hasCounts = (d.tN != null) || (d.cN != null) || (d.tE != null) || (d.cE != null);
    const hasEffect = (d.est != null) || (d.point != null) || (t.effect && t.effect.point != null);
    return hasCounts || hasEffect;
  }).length;
  const included = tr.filter(t => (t.screenReview && t.screenReview.status || t.status) === "include").length;
  return Math.max(analysed, included);})()""")
# Kept as DATA, per page, not collapsed into a verdict. "12 seconds to render a
# review's included studies" is a reader-facing fact and its own defect, separate
# from the sampling question, and we cannot know how many pages are that slow
# without recording it.
settle_profile = {}
# Pages on which the full window was actually spent. Printed every run: the day
# this silently drops to zero we need to see it, not infer it.
settle_used = []


_EXCEPTION_REGISTER = None


def _exception_registered(app):
    """Is this page listed in the standard-exception register?

    Registration is the half of the exemption that cannot be forged by editing
    the page. A banner is page content and anyone can paste one; the register is
    a reviewed file, so the exemption costs you a line in a backlog someone reads.
    """
    global _EXCEPTION_REGISTER
    if _EXCEPTION_REGISTER is None:
        import json as _j
        try:
            _d = _j.loads((ROOT / "STANDARD_EXCEPTIONS.json")
                          .read_text(encoding="utf-8"))
            _EXCEPTION_REGISTER = {p for e in _d.get("entries", []) for p in e.get("pages", [])}
        except Exception:                                        # noqa: BLE001
            # NO REGISTER MEANS NO EXEMPTION. Failing open here would hand every
            # page a pass the moment the file is renamed or malformed -- the
            # comfortable direction, and the one this gate must never take.
            _EXCEPTION_REGISTER = set()
    return (app + ".html") in _EXCEPTION_REGISTER


def _has_exception_banner(src):
    """Does the page itself tell the reader what is outstanding?"""
    return bool(src) and 'id="standard-exception-banner"' in src


def _is_restoration(app, src):
    """Archive id whose snapshot this content byte-for-byte matches, else None.

    The archive is the record of what we have previously published. Content
    identical to a snapshot in it is therefore not a new claim -- it is a state
    that was already live. Hashing the bytes is what makes this safe: a page that
    merely LOOKS like an old one does not qualify, so this cannot be used to slip
    an edited page past the gate.
    """
    d = _ARCHIVE / app
    if not d.is_dir():
        return None
    try:
        h = _hl.sha256(src.encode("utf-8", "replace")).hexdigest()
    except Exception:                                        # noqa: BLE001
        return None
    for f in sorted(d.glob("*.html")):
        try:
            if _hl.sha256(f.read_text(encoding="utf-8", errors="replace")
                          .encode("utf-8", "replace")).hexdigest() == h:
                return f.name
        except Exception:                                    # noqa: BLE001
            continue
    return None

ssot_seen = []

# Which searched-for markers were observed ANYWHERE this run. A count of zero for a
# marker that occurs nowhere means the search cannot match; it does not mean the defect
# is absent. See instrument_controls.zero_has_a_reading.
marker_seen = {}

signals = {
    "page_errors": [],
    "no_trials": [],
    "no_studies_rendered": [],
    "nondeterministic_render": [],
    "no_rob_banner": [],
    "wrong_protocol_link": [],
    "no_webr_tag": [],
    "pool_broken": [],
    # THE THIRD STATE. Reported, and NOT in _blocking_keys: a page that withdraws its
    # estimate with a reason is behaving correctly and must not be blocked for it.
    "pool_withdrawn_with_reason": [],
    "fully_ok": [],
}

_assert_server_identity()

with sync_playwright() as p:
    b = p.chromium.launch(headless=True, args=['--disable-gpu'])
    ctx = b.new_context(viewport={'width': 1400, 'height': 900})
    pg = ctx.new_page()
    for i, a in enumerate(apps, 1):
        # SSOT DISPATCH. The seven signals below are AUTO-shaped: they look for
        # seeded trials in JS state, a RoB banner element, a WebR tag and a pool
        # computed in the browser. An SSOT page has none of those BY DESIGN --
        # every number is projected at build time and it carries no engine. Now
        # that this gate can actually fail, running the AUTO set against an SSOT
        # page would block every push touching one, for the sole reason that the
        # page is the architecture we are moving towards. Classify first.
        try:
            _src = (ROOT / (a + ".html")).read_text(encoding="utf-8", errors="replace")
        except Exception:                                    # noqa: BLE001
            _src = ""
        # A STUB has no engine and no analysis, so BOTH signal sets are inapplicable.
        # Without this it fell through to the AUTO browser walk and failed on
        # "ReferenceError: RapidMeta is not defined" -- a page error report about a
        # page that correctly contains no RapidMeta. Classifying it right was only
        # half the fix; the caller has to act on the classification.
        if _src and _ssot.classify(_src) == "STUB":
            print("  [stub] %s is a redirect/stub: no engine and no analysis, so "
                  "neither the AUTO nor the SSOT signals apply." % a)
            signals["fully_ok"].append(a)
            continue
        if _src and _ssot.classify(_src) == "SSOT":
            _txt = _re2.sub(r"\s+", " ", _re2.sub(r"<[^>]+>", " ", _src))
            _fired = _ssot.run(_src, _txt)
            ssot_seen.append(a)
            # RESTORE EXEMPTION (2026-08-16).
            #
            # On 2026-08-16 four pages went live carrying ANOTHER DRUG'S trials --
            # sotagliflozin's page named sacubitril 24 times -- and the revert was
            # BLOCKED by this gate, because the archived flat pages do not carry
            # "Submission readiness:". That string is emitted by the tabbed build,
            # so those pages never had it and were never claimed to. The gate was
            # correct in its own terms and still blocked the right action: it
            # cannot tell a forward BUILD from a RESTORATION, which is the one
            # case it was not designed to classify. The revert needed an
            # authorised --no-verify, and a lane overriding a gate it hardened
            # hours earlier is exactly how gates rot.
            #
            # So a restore is now a first-class concept rather than an afterthought.
            # Content byte-identical to a preservation-archive snapshot is a state
            # we PREVIOUSLY PUBLISHED, so it passes. Anything else -- including a
            # forward build missing the readiness verdict -- still fails.
            #
            # The signals are still REPORTED for a restore, never silently dropped:
            # an exemption that hides what it exempted is how the next blind spot
            # gets built.
            if _fired and _is_restoration(a, _src):
                _arc = _is_restoration(a, _src)
                print("  [restore-exempt] %s matches archive %s byte for byte; "
                      "signals reported, not blocking: %s"
                      % (a, _arc, ", ".join(sorted(_fired))))
                signals["fully_ok"].append(a)
                continue
            if _fired:
                for _k, _why in _fired.items():
                    signals.setdefault("ssot_" + _k, []).append((a, _why))
            else:
                signals["fully_ok"].append(a)
            continue
        # A RETIRED PAGE IS NOT A BROKEN REVIEW. It carries no RapidMeta app because there is
        # no review left on it, so every app-level probe below would report a page error for a
        # page that is behaving exactly as intended. It is checked for what it IS instead: it
        # must declare its state, name its absorber, and link to a page that exists.
        _src = (ROOT / f"{a}.html").read_text(encoding="utf-8", errors="replace")
        if 'name="rapidmeta:page-state" content="RETIRED"' in _src:
            import re as _re
            # A TOPIC CAN BE RETIRED BY MERGE **OR** BY SPLIT, and this test read only the merge
            # spelling. `absorbed-by` names one survivor; `split-into` names several. The first
            # topic retired by split failed here as "declares RETIRED and names no absorber" --
            # a correct tombstone reported as a broken page, because the checker knew one word
            # for successor. IDENTICAL to the `absorbed_by` / `split_into` miss in
            # project_dashboard_index.py the same hour, which makes it class 25 twice over in
            # two instruments. Read EITHER, and check EVERY link rather than the first.
            _m = (_re.search(r'name="rapidmeta:absorbed-by" content="([^"]+)"', _src)
                  or _re.search(r'name="rapidmeta:split-into" content="([^"]+)"', _src))
            _links = _re.findall(r'class="go" href="([^"]+)"', _src)
            _bad = []
            if not _m:
                _bad.append("declares RETIRED and names neither an absorber nor a split target")
            if not _links:
                _bad.append("declares RETIRED and offers no link to a surviving review")
            for _href in _links:
                if not (ROOT / _href).exists():
                    _bad.append("links to %s, which does not exist -- a reader would 404"
                                % _href)
            if _bad:
                signals["page_errors"].append((a, "; ".join(_bad)))
            else:
                signals["fully_ok"].append(a)
            continue

        # A REVIEW THAT PUBLISHES NO POOLED ESTIMATE IS NOT A BROKEN DASHBOARD EITHER. It
        # carries no RapidMeta app because there is no pool to render, so every app-level probe
        # below would report a page error for a page behaving exactly as intended -- the same
        # missing concept that made the checker reject the tombstone, one state along.
        #
        # ENCODE THE DISTINCTION RATHER THAN EXEMPT THE FILE. It is checked for what it IS: it
        # must DECLARE that it publishes nothing, SAY so where a reader sees it rather than only
        # in a meta tag, name at least one trial, and every link it offers must resolve. A page
        # that quietly rendered nothing would still fail all four.
        if 'name="rapidmeta:pooled-estimate" content="NONE"' in _src:
            import re as _re
            _links = _re.findall(r'class="go" href="([^"]+)"', _src)
            _bad = []
            if "No pooled estimate" not in _src:
                _bad.append("declares no pooled estimate in a meta tag but nowhere a reader "
                            "would see it")
            if not _re.search(r"NCT\d{8}", _src):
                _bad.append("publishes no estimate AND names no trial -- there is nothing on "
                            "this page")
            for _href in _links:
                if not (ROOT / _href).exists():
                    _bad.append("links to %s, which does not exist -- a reader would 404"
                                % _href)
            if _bad:
                signals["page_errors"].append((a, "; ".join(_bad)))
            else:
                signals["fully_ok"].append(a)
            continue
        pg_errors = []
        pg.on('pageerror', lambda e: pg_errors.append(str(e)[:100]))
        try:
            pg.goto(f'http://localhost:{_PORT}/{a}.html', wait_until='load', timeout=60000)
            pg.wait_for_timeout(1500)
            pg.evaluate('localStorage.clear()')
            pg.goto(f'http://localhost:{_PORT}/{a}.html', wait_until='load', timeout=60000)
            pg.wait_for_timeout(2200)
        except Exception as e:
            signals["page_errors"].append((a, f"load: {e}"))
            continue

        if pg_errors:
            signals["page_errors"].append((a, pg_errors[:2]))

        try:
            trials = pg.evaluate('RapidMeta?.state?.trials?.length ?? -1')
            # TWO READS ACROSS THE SETTLE WINDOW. One read cannot tell "this review
            # includes no studies" from "this review has not finished rendering
            # them yet", and the old single read at ~2.2s reported the second as
            # the first. Measured 2026-08-17: 0 at 2.5s, 0 at 6s, 7 at 12s on a
            # cold load, and 7 offline (faster -- the fetches fail fast instead of
            # hanging), so this is LOCAL settling, not third-party success.
            incl = pg.evaluate(_INCL_JS)
            # CONDITIONAL SETTLE WINDOW. The defect is "a reader sees a review
            # with no studies in it". If the first read is NON-ZERO that reader
            # never occurs, so the window buys nothing on this page. If it is
            # ZERO we cannot tell "still settling" from "genuinely empty", and
            # that is exactly where the window must be spent. The property is
            # preserved; only the cost is dropped.
            #
            # WHAT THIS NO LONGER MEASURES, stated because it is a real gap:
            # a page rendering N studies at 2.2s and a DIFFERENT non-zero N at
            # 12.2s now passes unexamined. Churn among a non-empty set is
            # invisible here. It is narrower than the gap it replaces -- an
            # empty render is the reader-facing defect -- but it is not nothing.
            #
            # Why the conditional and not a shorter window: shortening it would
            # have removed the detection while looking like optimisation, which
            # is the shape of every mechanism in gate_integrity.py.
            if incl < 1:
                settle_used.append(a)
                pg.wait_for_timeout(_SETTLE_MS)
                incl_settled = pg.evaluate(_INCL_JS)
            else:
                incl_settled = incl
            settle_profile[a] = {"at_sample_ms": 2200, "at_sample": incl,
                                 "at_settle_ms": 2200 + _SETTLE_MS,
                                 "at_settle": incl_settled}
            banner_txt = pg.evaluate('document.getElementById("rob-status-banner")?.innerText || ""') or ""
            proto_href = pg.evaluate('document.querySelector(\'a[href*="protocols/"][href*="_protocol_v1"]\')?.getAttribute("href") || ""') or ""
            webr_tag = pg.evaluate('!!document.querySelector("script[src=\\"webr-validator.js\\"]")')
            # Switch to analysis tab and read pool
            pg.evaluate('try { RapidMeta.switchTab("analysis") } catch(e){}')
            pg.wait_for_timeout(800)
            pool = pg.evaluate('document.getElementById("res-or")?.innerText || ""') or ""
        except Exception as e:
            signals["page_errors"].append((a, f"eval: {e}"))
            continue

        if trials < 1:
            signals["no_trials"].append((a, trials))
        # FLAKY, AND THE CAUSE IS THE CORPUS-WIDE ONE (measured 2026-08-17).
        # `incl` counts trials whose status arrives from data the page FETCHES AT
        # LOAD. On 2026-08-17 ANTI_CD20_MS fired this signal 1 of 2 runs on the
        # UNEDITED page and 0 of 3 on the edited one, and blocked a good push.
        # 19 of 21 sampled pages issue third-party requests on load and every one
        # of them was getting HTTP 429 from api.openalex.org in the same window.
        # SO THIS GATE'S VERDICT DEPENDS ON A THIRD PARTY'S RATE LIMITER. A gate
        # that is non-deterministic teaches people to re-run it until it is green,
        # which is a bypass that leaves no trace in any log. Recorded here rather
        # than softened: the fix is self-containment (v1 property), not a retry.
        # THREE-STATE VERDICT. PASS / FAIL / NONDETERMINISTIC.
        #
        # RENAMED, because the old name asserted what it did not measure. It was
        # zero_included -- "this review includes no studies" -- and what it
        # observed was "no studies were rendered within the sampling window".
        # Third time today that a check reported something other than what it
        # measured (no_rob_banner tests a disclosure element and reads as an
        # assessment; the raw-HTML rule counted script source as page content).
        #
        # NONDETERMINISTIC BLOCKS, exactly as FAIL does. It is not a softer
        # verdict: not knowing what a page shows a reader is not a passing state,
        # and the same reasoning already makes INVALID distinct from PASS. What
        # it must NOT become is a longer wait until the number goes green -- that
        # would hide a genuine reader-facing defect rather than report it, and a
        # reader who looks in the first few seconds really does see zero studies.
        if incl < 1 and incl_settled < 1:
            signals["no_studies_rendered"].append((a, "0 at both %dms and %dms"
                                                   % (2200, 2200 + _SETTLE_MS)))
        elif incl != incl_settled:
            signals["nondeterministic_render"].append(
                (a, "%d at %dms -> %d at %dms" % (incl, 2200, incl_settled,
                                                  2200 + _SETTLE_MS)))
        if "Provisional RoB-2 and GRADE" not in banner_txt:
            signals["no_rob_banner"].append((a, banner_txt[:60]))
        # CLASS 52 ACCOUNTING, AT THE SITE OF TWO OF ITS THREE INSTANCES. This signal
        # keys on the marker `arni_hf_protocol` and has reported 0 on every run this
        # project has ever made -- because the marker appears on NO page in the corpus,
        # not because no page has the defect. A zero from a search whose term does not
        # exist is NOT_ASSESSABLE, and until now it was read as clean AND it sat in the
        # BLOCKING set. Every page is now asked whether the marker occurs at all, so the
        # zero can state which of its two readings it is.
        if "arni_hf_protocol" in proto_href:
            marker_seen["arni_hf_protocol"] = marker_seen.get("arni_hf_protocol", 0) + 1
        if a != "ARNI_HF_REVIEW" and "arni_hf_protocol" in proto_href:
            signals["wrong_protocol_link"].append((a, proto_href))
        if not webr_tag:
            signals["no_webr_tag"].append((a,))
        # A POOL CAN BE ABSENT FOR TWO REASONS AND THIS SIGNAL KNEW ONLY ONE.
        #
        # THREE STATES, NOT TWO: rendered, WITHDRAWN-WITH-REASON, failed.
        #
        # Until 2026-08-20 an empty or "--" pooled display was `pool_broken`, full stop.
        # But a page that WITHDRAWS its estimate deliberately renders exactly that, and
        # withdrawing is a behaviour this project has spent the week increasing. So the
        # check was scoring our most careful pages as our most broken ones, and every plan
        # built on its output inherited the inversion.
        #
        # TIRZEPATIDE_ARDS_AUTO_FULL_REVIEW opens with "IDENTITY CORRECTED -- THIS IS A
        # REVIEW OF ANDEXANET ALFA. Pooled: 0 trials, Quarantined: 3, Pooled estimate:
        # withdrawn", explains that the figure it used to show was computed from arm sizes
        # mistaken for event counts, and records a result it declines to pool. It was
        # scored identically to a page whose renderer fell over.
        #
        # THE SAME BIAS, ONE LAYER UP, PRODUCED A FALSE REPORT THE SAME NIGHT: a regex
        # matched the numerals inside that withdrawal notice and reported them as what the
        # page serves. A CHECKER THAT READS A DISCLOSURE AS THE DEFECT IT DISCLOSES
        # PENALISES A PAGE IN PROPORTION TO HOW HONESTLY IT DOCUMENTS ITSELF.
        #
        # There was already a declared-absent path here, keyed on
        # `rapidmeta:pooled-estimate content="NONE"`. MEASURED 2026-08-20: ZERO pages in
        # the corpus carry that meta tag, so that branch had never executed once -- a
        # three-state mechanism that had never reached its third state. The declaration is
        # therefore read from what the page SHOWS A READER, which is where 99 pages
        # currently put it, and the meta tag remains as a stronger form.
        #
        # AND READING WHAT THE PAGE SHOWS IS RIGHT FOR A SECOND REASON, INDEPENDENT OF
        # WHETHER ANY PAGE EMITS THE TAG. A withdrawal declared ONLY in metadata would
        # satisfy a meta-tag check while telling the reader nothing -- the check would pass
        # on a page whose reader still sees an unexplained "--". That is the same principle
        # as verifying SERVED BYTES rather than a hash: the artefact a reader receives is
        # the thing under test, and a marker they cannot see is not a disclosure.
        pool_clean = pool.strip()
        _absent = False
        try:
            pool_f = float(pool_clean)
            if pool_f in (0.0,):
                _absent = True
        except (TypeError, ValueError):
            if pool_clean in ("", "--", "NaN"):
                _absent = True
        if _absent:
            # Withdrawn-with-reason must be DECLARED where a reader sees it, and must
            # carry a REASON -- a bare "no pooled estimate" is not a withdrawal, it is a
            # blank with a label. The same four-part rigour as the meta-tag path.
            _decl = ("No pooled estimate" in _src or "no pooled estimate" in _src
                     or "estimate is withdrawn" in _src
                     or "Pooled estimate: withdrawn" in _src)
            _reason = any(k in _src for k in
                          ("withdrawn, not merely caveated", "Quarantined:",
                           "why this review publishes no pooled estimate",
                           "Why this review publishes no pooled estimate",
                           "was withdrawn because", "is withdrawn because",
                           "estimand", "not poolable", "declines to pool"))
            _names_trial = bool(__import__("re").search(r"NCT\d{8}", _src))
            if _decl and _reason and _names_trial:
                signals.setdefault("pool_withdrawn_with_reason", []).append(
                    (a, pool_clean or "empty"))
            else:
                _why = []
                if not _decl:
                    _why.append("no withdrawal declared where a reader sees it")
                if not _reason:
                    _why.append("no reason given for the absence")
                if not _names_trial:
                    _why.append("names no trial")
                signals["pool_broken"].append(
                    (a, (pool_clean or "empty") + " -- " + "; ".join(_why)))

        # DECLARED-ABSENT IS NOT MISSING, AND NEITHER IS A PASS (2026-08-17).
        #
        # 51 pages needed a JavaScript crash fixed -- a present harm to a reader on
        # their second visit -- and fail two PRE-EXISTING signals that nothing had
        # ever checked, because this gate only inspects pages a push touches and
        # nobody had touched them.
        #
        # The obvious way through was to add the "Provisional RoB-2 and GRADE"
        # banner. THAT WOULD HAVE BEEN A LIE: measured at runtime, those pages carry
        # ZERO risk-of-bias assessments. So does FINERENONE_REVIEW, WHICH PASSES THIS
        # SIGNAL while printing the banner over 0 of 145 trials assessed. The signal
        # is named no_rob_banner and it tests for a DISCLOSURE ELEMENT, not for an
        # assessment -- and reads to everyone as though it tested the assessment.
        # One more check that fails toward comfort.
        #
        # So: three states, not two. MISSING blocks. DECLARED-ABSENT does not block,
        # and is REPORTED every run, never silently dropped -- the restore exemption
        # above set that precedent and the reasoning is the same.
        #
        # A BANNER ALONE CANNOT BUY THE EXEMPTION. The page must ALSO be listed in
        # STANDARD_EXCEPTIONS.json, so the only way past this gate is to add
        # yourself to a countable backlog someone reads. Otherwise the comfortable
        # move -- paste the banner, ship anything -- would be available immediately,
        # and this gate would join the list it was written to escape.
        _declared = _exception_registered(a) and _has_exception_banner(_src)
        if _declared:
            _waived = [k for k in ("no_rob_banner", "no_webr_tag")
                       if any(x[0] == a for x in signals[k])]
            if _waived:
                print("  [standard-exception] %s declares its outstanding properties and "
                      "is registered; NOT blocking, still reported: %s"
                      % (a, ", ".join(_waived)))

        # If the app hit NO signal-failure so far, mark fully ok
        _blocking_keys = ("page_errors", "no_trials", "no_studies_rendered",
                          "nondeterministic_render", "no_rob_banner",
                          "wrong_protocol_link", "no_webr_tag", "pool_broken")
        if _declared:
            _blocking_keys = tuple(k for k in _blocking_keys
                                   if k not in ("no_rob_banner", "no_webr_tag"))
        broken_here = any(
            any(x[0] == a for x in signals[k])
            for k in _blocking_keys
        )
        if not broken_here:
            signals["fully_ok"].append(a)

        if i % 10 == 0:
            print(f"  [{i}/{len(apps)}]")
    b.close()

print()
print("=" * 60)
for k, v in signals.items():
    if k == "fully_ok":
        print(f"{k}:    {len(v)}/{len(apps)}")
        continue
    print(f"{k}:    {len(v)}/{len(apps)}")
    for item in v[:6]:
        print(f"   {item}")
    if len(v) > 6:
        print(f"   ... +{len(v)-6} more")

# THE ZERO WITH TWO READINGS, STATED RATHER THAN IMPLIED (registry class 52).
for _marker, _sig in (("arni_hf_protocol", "wrong_protocol_link"),):
    _n = len(signals.get(_sig) or [])
    if _n == 0 and not marker_seen.get(_marker):
        print("")
        print("NOT_ASSESSABLE: %s reported 0, AND the marker %r was not seen on ANY of the "
              "%d pages" % (_sig, _marker, len(apps)))
        print("    read this run. THE SEARCH CANNOT MATCH. This zero is not evidence that no")
        print("    page has the defect, and this signal is in the BLOCKING set, so it has")
        print("    been contributing a clean verdict it could never have contributed")
        print("    otherwise. Either the marker is stale or the check is.")

# Save raw
Path("/tmp/regression_results.json").write_text(json.dumps({k: v for k, v in signals.items()}, default=str), encoding='utf-8')
print()
print("Raw JSON saved to /tmp/regression_results.json")

# THE SETTLE PROFILE, KEPT AS DATA. Not collapsed into the verdict, because
# "how long before a reader sees this review's included studies" is a
# reader-facing fact and a defect in its own right, separate from the sampling
# question the verdict answers. Twelve seconds is a long time to show someone an
# empty review, and we cannot know how many pages are that slow without a record.
if settle_profile:
    _slow = {k: v for k, v in settle_profile.items()
             if v["at_sample"] < 1 <= v["at_settle"]}
    (ROOT / "outputs").mkdir(exist_ok=True)
    with open(ROOT / "outputs" / "settle_profile.json", "w", encoding="utf-8") as _fh:
        json.dump(settle_profile, _fh, indent=1)
    print("settle profile: %d page(s) measured; full window spent on %d "
          "(first read was zero); %d rendered NOTHING at %dms and recovered by %dms"
          % (len(settle_profile), len(settle_used), len(_slow), 2200,
             2200 + _SETTLE_MS))
    for _k in sorted(_slow)[:8]:
        print("   %-44s %d -> %d" % (_k, _slow[_k]["at_sample"], _slow[_k]["at_settle"]))

# THE FAILURE PATH. This script previously had no sys.exit ANYWHERE, so it exited 0
# whatever it found -- and the pre-push hook then read `$?` after a pipe, which is
# `tail`'s status and also always 0. Two independent reasons the gate could never
# block a push. A guard that cannot fail is not a guard, so the exit code is now
# derived from the findings.
# fully_ok is the SUCCESS list, not a signal. Including it here inverted the
# gate: a page that passed all seven checks was added to fully_ok, which made
# this dict non-empty, which blocked the push. The first push after the gate was
# repaired to be able to fail was rejected with
#
#     REGRESSION CHECK FAILED. Signals firing:
#       fully_ok: 1
#
# on a page whose seven defect signals were all zero. The gate went from never
# failing to failing on success, which is the same defect wearing the opposite
# sign, and it is why a success counter must never be read as a finding.
_OK_KEYS = {"fully_ok"}
# A DECLARED EXCEPTION IS REPORTED, NOT COUNTED AS A BLOCKING FINDING.
# The per-page loop already decides this; the exit logic has to agree, or the
# gate reports "not blocking" and then blocks -- which is exactly what the first
# cut of this change did. Two places deciding the same thing independently is
# how the fully_ok inversion above happened too, so the waiver is applied here
# by REMOVING the waived (page, signal) pairs, leaving any OTHER page's failure
# of the same signal fully intact.
_WAIVABLE = ("no_rob_banner", "no_webr_tag")
_waived_pairs = 0
for _k in _WAIVABLE:
    _kept = []
    for _row in signals[_k]:
        _app = _row[0] if isinstance(_row, tuple) else _row
        if _exception_registered(_app) and _has_exception_banner(
                (ROOT / (_app + ".html")).read_text(encoding="utf-8", errors="replace")
                if (ROOT / (_app + ".html")).exists() else ""):
            _waived_pairs += 1
            continue
        _kept.append(_row)
    signals[_k] = _kept
if _waived_pairs:
    print("\n%d signal(s) waived under STANDARD_EXCEPTIONS.json -- these pages "
          "are BELOW STANDARD and say so on their face. Waived is not fixed and the "
          "register is the backlog." % _waived_pairs)
_fail = {k: v for k, v in signals.items() if v and k not in _OK_KEYS}
if _fail:
    print()
    print("REGRESSION CHECK FAILED. Signals firing:")
    for k, v in _fail.items():
        print(f"  {k}: {len(v)}")
    sys.exit(1)
print()
print("Regression check clean across the pages in scope.")
sys.exit(0)
