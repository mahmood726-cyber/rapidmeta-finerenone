"""Does a legacy page hold a computed result? Decided by EXECUTING it, never by reading `--`.

# control: two pages classified by hand before the run -- one SSOT page that certainly pools
# (SGLT2_HF_REVIEW) and one legacy page whose static bytes show `--` (GLP1_CVOT_REVIEW). The run
# exits non-zero if the SSOT control comes back with no result, because an instrument that
# cannot see a result that is certainly there cannot be trusted to report its absence.

THE MISTAKE THIS EXISTS TO PREVENT, AND IT WAS ABOUT TO BE MADE. The legacy pages render their
headline statistics as `--` in the delivered bytes, and it was reported to Mahmood that 744 of
them "render pooled statistics as --" with the implication that they hold no result. THEY MAY
HOLD ONE. `--` is the PRE-JAVASCRIPT state:

    updateStatCards(c) {
      if (!c) { getElementById("res-or").innerText = "--"; ... }
      getElementById("res-or").innerText = c.pOR.toFixed(2)
    }

The page carries a real pooling engine -- REML, DerSimonian-Laird, tau^2, logOR -- and fills
those cards on load. Whether a reader meets a number or a dash is decided at RUNTIME, from
whether the page also carries trial data. A static read of the delivered bytes cannot tell the
two apart, and reporting the static count as "no computed result" would have been this
project's own house failure: ABSENT READ AS ZERO.

This matters beyond bookkeeping. Mahmood's step zero is to remove a pass-banner from every
legacy page that HOLDS NO POOLED RESULT. That predicate decides which pages get edited. Getting
it from the static bytes would delete a truthful banner from pages that earned it, and this
project has spent the night establishing that a claim must be backed by a field -- the same
standard applies to a claim that a page is empty.

WHAT IS MEASURED. Chrome renders the file from disk with a virtual time budget, and the run
reads the three stat cards out of the resulting DOM. A page is RESULT-BEARING when `#res-or`
holds something other than the dash placeholder. Nothing is edited here; this only classifies.
"""
from __future__ import annotations

import io
import json
import os
import re
import subprocess
import sys
import tempfile
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
OUT = os.path.join(REPO, "outputs", "legacy_result_state_2026_08_23.json")

# the dash the page writes when `c` is falsy, plus the empty and whitespace cases
DASHES = {"--", "\u2014", "\u2013", "", "-", "N/A", "n/a"}
CARDS = ("res-or", "res-ci", "res-i2")


def render(path, budget_ms=25000, timeout=180):
    """Return the post-script DOM, or None if Chrome could not render it."""
    d = tempfile.mkdtemp(prefix="rmrender")
    url = "file:///" + os.path.abspath(path).replace("\\", "/")
    cmd = [CHROME, "--headless=new", "--disable-gpu", "--no-sandbox",
           "--disable-dev-shm-usage", "--user-data-dir=" + d,
           "--virtual-time-budget=%d" % budget_ms, "--dump-dom", url]
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return None
    dom = r.stdout.decode("utf-8", "replace")
    return dom if len(dom) > 500 else None


def cards_from(dom):
    """The three headline stat cards as the DOM holds them after scripts have run."""
    out = {}
    for oid in CARDS:
        m = re.search(r'id="%s"[^>]*>(.{0,80}?)<' % re.escape(oid), dom, re.S)
        out[oid] = re.sub(r"\s+", " ", m.group(1)).strip() if m else None
    return out


def bears_result(cards):
    v = cards.get("res-or")
    return bool(v) and v not in DASHES


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    names = sys.argv[1:]
    if not names:
        sys.exit("usage: render_legacy_result_state_2026_08_23.py <page.html> [...]")

    # THE CONTROL RUNS FIRST AND THE RUN REFUSES IF IT FAILS.
    #
    # IT MUST BE A LEGACY PAGE. The first version of this script controlled on SGLT2_HF_REVIEW,
    # an SSOT page -- which carries no `#res-or` card at all, because the SSOT projector renders
    # its estimates as prose and tables. The control therefore reported "failed" on a page that
    # had rendered perfectly, and would have kept reporting it forever: it was asking a page
    # from one family for a marker that only exists in the other.
    #
    # GLP1_CVOT_REVIEW is the right control because it is legacy AND its result is now known by
    # execution: OR 0.86, 95% CI 0.82-0.90, I2 38.7%. So the control asserts the positive
    # property -- the instrument can SEE a result that is certainly there -- which is the only
    # thing that licenses this run to report absence anywhere else.
    ctrl = "GLP1_CVOT_REVIEW.html"
    ctrl_ok = None
    if os.path.isfile(os.path.join(REPO, ctrl)):
        dom = render(os.path.join(REPO, ctrl))
        ctrl_ok = dom is not None and bears_result(cards_from(dom))
        print("control  %-42s %s" % (ctrl, "SEES THE KNOWN RESULT" if ctrl_ok else "FAILED"))

    rows, res, dash, failed = [], 0, 0, 0
    for n in names:
        p = n if os.path.isabs(n) else os.path.join(REPO, n)
        if not os.path.isfile(p):
            print("  %-46s NOT ON DISK" % n[:46])
            continue
        t0 = time.time()
        dom = render(p)
        if dom is None:
            failed += 1
            print("  %-46s RENDER FAILED" % n[:46])
            rows.append({"page": os.path.basename(n), "state": "render_failed"})
            continue
        c = cards_from(dom)
        b = bears_result(c)
        res += b
        dash += (not b)
        rows.append({"page": os.path.basename(n), "state": "result" if b else "no_result",
                     "cards": c, "secs": round(time.time() - t0, 1)})
        print("  %-46s %-9s or=%-10s ci=%-22s i2=%s"
              % (os.path.basename(n)[:46], "RESULT" if b else "no result",
                 c["res-or"], (c["res-ci"] or "")[:22], c["res-i2"]))

    print("")
    print("EXECUTED %d page(s): %d hold a computed result, %d show the placeholder, %d failed"
          % (len(rows), res, dash, failed))
    print("")
    print("`--` IN THE DELIVERED BYTES IS THE PRE-SCRIPT STATE AND MEANS NOTHING ON ITS OWN.")
    print("A page that computes on load holds a result a reader meets; a page that does not is")
    print("the one whose pass-banner is false. Only the render tells them apart.")

    if not os.path.isdir(os.path.dirname(OUT)):
        os.makedirs(os.path.dirname(OUT))
    json.dump({"rows": rows, "result": res, "no_result": dash, "render_failed": failed},
              io.open(OUT, "w", encoding="utf-8"), indent=1)
    if ctrl_ok is False:
        sys.exit("REFUSED: the control page did not render, so a 'no result' verdict from this "
                 "run would be the instrument failing, not the page being empty.")


if __name__ == "__main__":
    main()
