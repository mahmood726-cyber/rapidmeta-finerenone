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

signals = {
    "page_errors": [],
    "no_trials": [],
    "zero_included": [],
    "no_rob_banner": [],
    "wrong_protocol_link": [],
    "no_webr_tag": [],
    "pool_broken": [],
    "fully_ok": [],
}

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
        pg_errors = []
        pg.on('pageerror', lambda e: pg_errors.append(str(e)[:100]))
        try:
            pg.goto(f'http://localhost:8787/{a}.html', wait_until='load', timeout=60000)
            pg.wait_for_timeout(1500)
            pg.evaluate('localStorage.clear()')
            pg.goto(f'http://localhost:8787/{a}.html', wait_until='load', timeout=60000)
            pg.wait_for_timeout(2200)
        except Exception as e:
            signals["page_errors"].append((a, f"load: {e}"))
            continue

        if pg_errors:
            signals["page_errors"].append((a, pg_errors[:2]))

        try:
            trials = pg.evaluate('RapidMeta?.state?.trials?.length ?? -1')
            incl = pg.evaluate('(RapidMeta?.state?.trials||[]).filter(t => (t.screenReview?.status || t.status) === "include").length')
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
        if incl < 1:
            signals["zero_included"].append((a, incl))
        if "Provisional RoB-2 and GRADE" not in banner_txt:
            signals["no_rob_banner"].append((a, banner_txt[:60]))
        if a != "ARNI_HF_REVIEW" and "arni_hf_protocol" in proto_href:
            signals["wrong_protocol_link"].append((a, proto_href))
        if not webr_tag:
            signals["no_webr_tag"].append((a,))
        pool_clean = pool.strip()
        try:
            pool_f = float(pool_clean)
            if pool_f in (0.0,):
                signals["pool_broken"].append((a, pool_clean))
        except (TypeError, ValueError):
            # "--" or blank means pool failed
            if pool_clean in ("", "--", "NaN"):
                signals["pool_broken"].append((a, pool_clean or "empty"))

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
        _blocking_keys = ("page_errors", "no_trials", "zero_included", "no_rob_banner",
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

# Save raw
Path("/tmp/regression_results.json").write_text(json.dumps({k: v for k, v in signals.items()}, default=str), encoding='utf-8')
print()
print("Raw JSON saved to /tmp/regression_results.json")

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
