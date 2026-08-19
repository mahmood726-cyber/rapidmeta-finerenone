"""P10 -- CONFIRM THE PAGES IN BYTES SERVED OVER HTTP, NOT IN A SOURCE FILE OR AN EXIT CODE.

TWO CHECKS PER PAGE, AND EITHER ALONE IS INSUFFICIENT:

  1  md5(served) == md5(disk)
        Catches a server, a cache or a rewrite putting different bytes on the wire from the
        ones the build wrote.

  2  A CONTENT CHECK, derived from the OBJECT rather than typed here
        Catches the case md5 cannot: A STALE FILE MATCHES ITS OWN DISK COPY PERFECTLY. If the
        page was never rebuilt after the object changed, both hashes agree and everything
        looks correct. The only thing that separates a served-and-current page from a
        served-and-stale one is whether the CURRENT facts are in the bytes.

The expected strings are PROJECTED FROM EACH OBJECT at run time -- its own build_stamp P2
sentence and its own pooled point estimate. Typing them here would test the page against this
script's author, and would keep passing after the next restatement.

Absent object, absent page, unreadable file -> NOT_ASSESSABLE, reported as its own state.
An unverifiable page is never a pass.
"""
import functools
import hashlib
import http.server
import io
import json
import os
import socket
import sys
import threading
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PAGES = {
    "alirocumab-lipid": "ALIROCUMAB_LIPID_SSOT.html",
    "attr-cm-review": "ATTR_CM_REVIEW.html",
    "bempedoic-acid-review": "BEMPEDOIC_ACID_REVIEW.html",
    "iv-iron-hf": "IV_IRON_HF_REVIEW.html",
    "sglt2-hf": "SGLT2_HF_REVIEW.html",
    "ablation-af-heart-failure": "ABLATION_AF_HEART_FAILURE_REVIEW.html",
}

FAIL, NA, OK = "FAIL", "NOT_ASSESSABLE", "OK"


def expected_from_object(obj):
    """[(label, string that MUST appear in the served bytes)] -- projected, never typed."""
    out = []
    p2 = (((obj.get("build_stamp") or {}).get("properties") or {})
          .get("P2_k_cascade") or {}).get("reason")
    if isinstance(p2, str) and p2.strip():
        out.append(("build_stamp P2 cascade sentence", p2.strip()))
    for name, blk in (((obj.get("results") or {}).get("by_outcome")) or {}).items():
        if not isinstance(blk, dict):
            continue
        pooled = blk.get("pooled") or {}
        pt = pooled.get("point")
        if pt is None or pooled.get("withdrawn"):
            continue
        out.append(("pooled point of %s" % name, ("%g" % float(pt))))
    return out


def serve(directory):
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=directory)
    # Port 0 -> the OS picks a free one. A hardcoded port makes this fail on a busy box and
    # a failure to bind must not read as a failure of the pages.
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    srv.daemon_threads = True
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, srv.socket.getsockname()[1]


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    socket.setdefaulttimeout(120)
    srv, port = serve(REPO)
    print("serving %s on http://127.0.0.1:%d\n" % (REPO, port))
    verdicts = []
    try:
        for topic, page in sorted(PAGES.items()):
            disk = os.path.join(REPO, page)
            objp = os.path.join(REPO, "ssot", topic, topic + ".json")
            print("--- %s  ->  %s" % (topic, page))
            if not os.path.exists(disk) or not os.path.exists(objp):
                print("    %s: page or object absent -- an unverifiable page is not a pass"
                      % NA)
                verdicts.append((topic, NA))
                continue
            with open(disk, "rb") as fh:
                disk_bytes = fh.read()
            with io.open(objp, encoding="utf-8") as fh:
                obj = json.load(fh)

            url = "http://127.0.0.1:%d/%s" % (port, page)
            try:
                with urllib.request.urlopen(url, timeout=120) as resp:
                    status = resp.status
                    served = resp.read()
            except Exception as exc:                    # noqa: BLE001 - transport, reported
                print("    %s: fetch failed (%s: %s) -- NOT a page failure"
                      % (NA, type(exc).__name__, exc))
                verdicts.append((topic, NA))
                continue

            limbs = []
            d5, s5 = hashlib.md5(disk_bytes).hexdigest(), hashlib.md5(served).hexdigest()
            limbs.append(("md5 served == disk", OK if d5 == s5 else FAIL,
                          "disk %s / served %s, %d bytes, HTTP %d"
                          % (d5[:12], s5[:12], len(served), status)))

            text = served.decode("utf-8", "replace")
            exp = expected_from_object(obj)
            if not exp:
                limbs.append(("content check", NA,
                              "the object projects nothing checkable: no build_stamp P2 "
                              "sentence and no pooled point"))
            for label, needle in exp:
                limbs.append(("content: %s" % label,
                              OK if needle in text else FAIL,
                              ("found" if needle in text else "ABSENT FROM THE SERVED BYTES")
                              + " -- " + " ".join(needle.split())[:96]))

            # EVERY LIMB IS PRINTED, not the first failing one. A verdict that names one
            # reason drawn from an ordered sequence is a fact about the sequence.
            for name, verdict, detail in limbs:
                print("    %-46s %-15s %s" % (name, verdict, detail))
            if any(v == FAIL for _n, v, _d in limbs):
                verdicts.append((topic, FAIL))
            elif any(v == NA for _n, v, _d in limbs):
                verdicts.append((topic, NA))
            else:
                verdicts.append((topic, OK))
            print()
    finally:
        srv.shutdown()

    print("SUMMARY")
    for topic, v in verdicts:
        print("   %-26s %s" % (topic, v))
    bad = [t for t, v in verdicts if v == FAIL]
    na = [t for t, v in verdicts if v == NA]
    if bad:
        print("\nREFUSED: %s verified in served bytes as WRONG or STALE." % ", ".join(bad))
        return 1
    if na:
        print("\nNOT VERIFIED: %s. Not a pass -- an unverifiable page is unverified."
              % ", ".join(na))
        return 1
    print("\nAll %d pages confirmed in served bytes: hash matches disk AND the object's own "
          "current\nfacts are present in what the server sent." % len(verdicts))
    return 0


if __name__ == "__main__":
    sys.exit(main())
