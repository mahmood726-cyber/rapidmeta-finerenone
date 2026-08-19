#!/usr/bin/env python3
"""P10, CORRECTED: VERIFY THE BYTES A READER RECEIVES, AND NAME THE HOST THAT SERVED THEM.

THE FAILURE THIS REPLACES IS OURS, AND IT IS THE LARGEST DELIVERY-IS-NOT-AUDIT INSTANCE IN THIS
PROJECT'S HISTORY.

`verify_served_bytes_2026_08_19.py` started a `SimpleHTTPRequestHandler` over the repository,
fetched each page from `127.0.0.1`, compared md5 to disk, and reported

    "All N pages confirmed in served bytes."

Every word of that was true and none of it was about delivery. It served the build directory to
itself. md5(served) == md5(disk) is a TAUTOLOGY when the server IS the disk: the check could not
fail for the reason anyone cared about. Meanwhile:

    live SGLT2_HF_REVIEW.html      md5 ca872295...  ==  origin/main's copy, byte for byte
    local build of the same page   md5 d9164e1c...
    origin/fix/ssot-tabbed-shell   UNKNOWN REVISION -- the branch was never pushed
    GitHub Pages source            {"branch": "main", "path": "/"}
    divergence                     96 commits ahead of origin/main, 0 behind

    THE DEPLOYMENT IS PERFECTLY CURRENT WITH RESPECT TO MAIN. WHAT IS STALE IS MAIN, RELATIVE
    TO A BRANCH THAT WAS NEVER PUSHED AT ALL.

And the general form, which is the part worth keeping:

    A VERIFICATION IS ONLY EVER ABOUT THE ARTEFACT IT FETCHED. A check that does not name its
    host is not a delivery check. Ninety-six commits of green "served bytes" verifications were
    true of a build and silent about the artefact a reader opens.

WHAT THIS DOES DIFFERENTLY, ALL FOUR DELIBERATE:

  1. IT FETCHES THE PUBLIC URL. Not localhost, not a temporary server, not the working tree.
  2. IT NAMES THE HOST on every line it prints and in its summary, so a local verification can
     never again be read as a delivery claim by whoever quotes the output.
  3. IT FAILS CLOSED. If the public URL cannot be reached the verdict is NOT_ASSESSABLE and the
     exit status is non-zero. IT NEVER FALLS BACK TO LOCAL AND PASSES -- a fallback that
     downgrades the artefact while keeping the verdict is exactly how this defect survived.
  4. IT REPORTS THE DEPLOY REF against the ref being verified, because a push to a branch the
     pipeline does not track produces a remote branch and no deployment.

`--build-only` still exists, because checking a build before deciding to deploy is a real need.
It prints BUILD CHECK on every line, refuses to print the word delivered, and CANNOT RETURN A
DELIVERY PASS. The mode is in the output, not only in the invocation.
"""
import argparse
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PAGES = {
    "alirocumab-lipid": "ALIROCUMAB_LIPID_SSOT.html",
    "attr-cm-review": "ATTR_CM_REVIEW.html",
    "bempedoic-acid-review": "BEMPEDOIC_ACID_REVIEW.html",
    "iv-iron-hf": "IV_IRON_HF_REVIEW.html",
    "sglt2-hf": "SGLT2_HF_REVIEW.html",
    "ablation-af-heart-failure": "ABLATION_AF_HEART_FAILURE_REVIEW.html",
    "ablation-af-medical-therapy": "ABLATION_AF_MEDICAL_THERAPY_REVIEW.html",
    "early-rhythm-control-af": "EARLY_RHYTHM_CONTROL_AF_REVIEW.html",
    "apixaban-vte-treatment": "APIXABAN_VTE_TREATMENT_REVIEW.html",
    "apixaban-vte-prophylaxis": "APIXABAN_VTE_PROPHYLAXIS_REVIEW.html",
    "bococizumab-lipid-review": "BOCOCIZUMAB_LIPID_REVIEW.html",
    "azilsartan-chlorthalidone-vs-olmesartan-hctz": "AZILSARTAN_CLD_VS_OLM_HCTZ_REVIEW.html",
}

FAIL, NA, OK, STALE = "FAIL", "NOT_ASSESSABLE", "OK", "STALE"


def git(*args):
    try:
        r = subprocess.run(("git",) + args, cwd=REPO, stdout=subprocess.PIPE,
                           stderr=subprocess.DEVNULL, timeout=60)
        return r.stdout.decode("utf-8", "replace").strip() if r.returncode == 0 else None
    except Exception:
        return None


def public_base():
    """The URL A READER OPENS, derived from the remote so it cannot drift from the repository.

    Override with RM_PUBLIC_BASE for a custom domain. Derivation is deterministic and needs no
    credentials; guessing is not involved, and if the remote is not a GitHub URL this returns
    None and the run is NOT_ASSESSABLE rather than quietly local.
    """
    env = os.environ.get("RM_PUBLIC_BASE")
    if env:
        return env.rstrip("/") + "/", "RM_PUBLIC_BASE"
    url = git("remote", "get-url", "origin") or ""
    m = re.search(r"github\.com[:/]([^/]+)/([^/.]+)", url)
    if not m:
        return None, "origin=%r does not look like a GitHub remote" % url
    return "https://%s.github.io/%s/" % (m.group(1), m.group(2)), "derived from origin"


def deploy_ref():
    """Which ref the Pages pipeline builds, and whether HEAD is on it."""
    info = {"pages_branch": None, "how": None}
    try:
        r = subprocess.run(("gh", "api",
                            "repos/{owner}/{repo}/pages".format(owner="{owner}", repo="{repo}")),
                           cwd=REPO, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                           timeout=90)
        if r.returncode == 0:
            d = json.loads(r.stdout.decode("utf-8", "replace"))
            info["pages_branch"] = (d.get("source") or {}).get("branch")
            info["how"] = "GitHub Pages API"
    except Exception:
        pass
    if not info["pages_branch"]:
        head = git("symbolic-ref", "refs/remotes/origin/HEAD")
        if head:
            info["pages_branch"] = head.rsplit("/", 1)[-1]
            info["how"] = "origin/HEAD (Pages API unavailable -- INFERRED, not read)"
    info["head_branch"] = git("rev-parse", "--abbrev-ref", "HEAD")
    info["head_sha"] = git("rev-parse", "--short", "HEAD")
    if info["pages_branch"]:
        info["ahead"] = git("rev-list", "--count",
                            "origin/%s..HEAD" % info["pages_branch"])
        info["pushed"] = git("rev-parse", "--verify", "--quiet",
                             "refs/remotes/origin/%s" % info["head_branch"]) is not None
    return info


def expected_from_object(obj):
    """[(label, string that MUST appear in the delivered bytes)] -- projected, never typed."""
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


def fetch(url):
    req = urllib.request.Request(url, headers={"Cache-Control": "no-cache",
                                               "User-Agent": "rapidmeta-delivery-check"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        return resp.status, resp.read()


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("--build-only", action="store_true",
                    help="check the local build. CANNOT return a delivery pass.")
    args = ap.parse_args()

    base, how = public_base()
    ref = deploy_ref()

    if args.build_only:
        host = "LOCAL BUILD DIRECTORY (%s)" % REPO
        print("MODE: BUILD CHECK -- THIS IS NOT A DELIVERY VERIFICATION.")
    else:
        host = base
        print("MODE: DELIVERY VERIFICATION")
    print("HOST VERIFIED: %s   [%s]" % (host, how if not args.build_only else "not a host"))
    print("Pages builds:  %s   [%s]" % (ref.get("pages_branch") or "UNKNOWN", ref.get("how")))
    print("HEAD:          %s @ %s   pushed to origin: %s   ahead of the deploy ref by: %s"
          % (ref.get("head_branch"), ref.get("head_sha"),
             ref.get("pushed"), ref.get("ahead")))
    if ref.get("pushed") is False:
        print("\n    WARNING: THE CURRENT BRANCH DOES NOT EXIST ON THE REMOTE. Nothing on it")
        print("    can be deployed, and no verification of it can be a delivery claim.")
    print()

    if not args.build_only and not base:
        print("%s: no public base URL could be derived (%s)." % (NA, how))
        print("FAILING CLOSED. A delivery check that cannot reach the public artefact does not")
        print("fall back to the local one -- that is how a build check became a delivery claim.")
        return 1

    verdicts = []
    for topic, page in sorted(PAGES.items()):
        disk = os.path.join(REPO, page)
        objp = os.path.join(REPO, "ssot", topic, topic + ".json")
        print("--- %s  ->  %s   @ %s" % (topic, page, host))
        if not os.path.exists(disk) or not os.path.exists(objp):
            print("    %s: local page or object absent -- unverifiable is not a pass" % NA)
            verdicts.append((topic, NA))
            continue
        with open(disk, "rb") as fh:
            disk_bytes = fh.read()
        with io.open(objp, encoding="utf-8") as fh:
            obj = json.load(fh)

        if args.build_only:
            status, got = 200, disk_bytes
        else:
            try:
                status, got = fetch(base + page)
            except urllib.error.HTTPError as exc:
                print("    %s: HTTP %s from %s -- the reader gets this, and it is not a pass"
                      % (FAIL if exc.code == 404 else NA, exc.code, host))
                verdicts.append((topic, FAIL if exc.code == 404 else NA))
                continue
            except Exception as exc:                    # noqa: BLE001 - transport, reported
                print("    %s: fetch failed (%s: %s). NOT falling back to local."
                      % (NA, type(exc).__name__, exc))
                verdicts.append((topic, NA))
                continue

        limbs = []
        d5, s5 = hashlib.md5(disk_bytes).hexdigest(), hashlib.md5(got).hexdigest()
        if args.build_only:
            limbs.append(("md5 of the build", NA,
                          "%s -- comparing the build to itself proves nothing about delivery"
                          % d5[:12]))
        else:
            # THE LIMB THAT NOW MEANS SOMETHING. Delivered != built is the deployment question,
            # and against a real host it is answerable and can genuinely fail.
            limbs.append(("delivered bytes == local build", OK if d5 == s5 else STALE,
                          "build %s / delivered %s, %d bytes, HTTP %d"
                          % (d5[:12], s5[:12], len(got), status)))

        text = got.decode("utf-8", "replace")
        exp = expected_from_object(obj)
        if not exp:
            limbs.append(("content check", NA,
                          "the object projects nothing checkable: no build_stamp P2 sentence "
                          "and no pooled point"))
        for label, needle in exp:
            present = needle in text
            limbs.append(("content: %s" % label, OK if present else FAIL,
                          ("found" if present else "ABSENT FROM THE BYTES %s SERVED" % host)
                          + " -- " + " ".join(needle.split())[:88]))

        for name, verdict, detail in limbs:
            print("    %-46s %-15s %s" % (name, verdict, detail))
        vs = [v for _n, v, _d in limbs]
        verdicts.append((topic, FAIL if FAIL in vs else
                         STALE if STALE in vs else
                         NA if NA in vs else OK))
        print()

    print("SUMMARY -- host: %s" % host)
    for topic, v in verdicts:
        print("   %-30s %s" % (topic, v))

    bad = [t for t, v in verdicts if v == FAIL]
    stale = [t for t, v in verdicts if v == STALE]
    na = [t for t, v in verdicts if v == NA]
    if args.build_only:
        print("\nBUILD CHECK COMPLETE. THIS IS NOT A DELIVERY RESULT and must not be reported")
        print("as one. Run without --build-only to verify what a reader receives.")
        return 1 if bad else 0
    if bad:
        print("\nREFUSED: %s -- the bytes %s serves are WRONG." % (", ".join(bad), host))
        return 1
    if stale:
        print("\nNOT DELIVERED: %s -- %s serves DIFFERENT bytes from the local build."
              % (", ".join(stale), host))
        print("The build is not the artefact. Deploying is what changes this, not rebuilding.")
        return 1
    if na:
        print("\nNOT VERIFIED at %s: %s. An unverifiable page is unverified, never a pass."
              % (host, ", ".join(na)))
        return 1
    print("\nAll %d pages confirmed IN THE BYTES %s DELIVERED: identical to the local build,"
          % (len(verdicts), host))
    print("and carrying each object's own current facts.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
