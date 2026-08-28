"""Protocols and SAPs from the registration's own document set. Keyed on NCT only.

WHY NCT AND NOTHING ELSE. Reading identifiers out of stored records, this lane took the first
doi/pmcid in each and some of those were RELATED ARTICLES -- 19 of 74 trials ended up carrying
an identifier shared with another trial, two of them provably Cochrane reviews rather than
trial reports. Five documents were quarantined. An NCT cannot collide: it is the key the
registration is filed under, so this route is immune to the defect that spoiled the last one.

WHAT THIS RECOVERS AND WHY IT IS THE RIGHT REMAINING ROUTE. ClinicalTrials.gov publishes the
PROTOCOL and the STATISTICAL ANALYSIS PLAN as documents on many registrations. Those are the
documents domains D1 to D3 actually need -- prespecification, randomisation, deviations -- and
no index gatekeeps them. A trial whose paper is paywalled may still publish its whole protocol
here.

*** A 000 IS NOT A PAYWALL, AND A 200 IS NOT A DOCUMENT. ***

Two failure modes that both produce a clean-looking negative:
  status 000  the request never left the machine. Codex has NO network -- curl returns 000 --
              so a fetch delegated there records every route as failed and looks like a
              thorough negative. This refuses to write ANY verdict when it sees 000.
  status 200  a publisher landing page. All 29 trials still at abstract level return
              doi_resolver=200 and hold no full text.

So a route is recorded as genuinely unavailable only on a real refusal -- a 403, a 404, or an
explicit absence in the registration -- and never on a transport failure.

REFUSALS ARE RECORDED WITH THEIR REASON, not as bare failures. A withdrawn application is a
different fact from a paywall, and both are different from "we could not reach the network".
"""
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STORE = os.path.join(REPO, "evidence", "acquisition")
OUT = os.path.join(REPO, "out", "registry_documents_2026_08_28.json")
TRIALS = os.path.join(REPO, "outputs", "_acq_trials.txt")
TODAY = "2026-08-28"
API = ("https://clinicaltrials.gov/api/v2/studies/%s"
       "?fields=NCTId,LargeDocumentModule,OverallStatus")


def fetch(url):
    r = subprocess.run(["curl", "-sSL", "-g", "--max-time", "60",
                        "-w", "\n<<<HTTP:%{http_code}>>>", url], capture_output=True)
    b = (r.stdout or b"").decode("utf-8", "surrogateescape")
    m = re.search(r"<<<HTTP:(\d+)>>>\s*$", b)
    return (b[:m.start()] if m else b), (int(m.group(1)) if m else 0)


class NoNetwork(Exception):
    """Raised on status 000 so a transport failure can never become a verdict."""


def main():
    raw = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                           write_through=True)

    def say(s):
        raw.write(s + chr(10))
        raw.flush()

    start = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    count = int(sys.argv[2]) if len(sys.argv) > 2 else 12
    ncts = [l.split("\t")[0] for l in io.open(TRIALS, encoding="utf-8") if l.strip()]
    batch = ncts[start:start + count]
    say("trials %d   batch %d..%d" % (len(ncts), start, start + len(batch)))

    rows, n000 = [], 0
    for nct in batch:
        body, code = fetch(API % nct)
        if code == 0:
            n000 += 1
            rows.append({"nct": nct, "verdict": "NOT ASSESSED -- transport failure (000)",
                         "note": "the request never left the machine; this is NOT evidence "
                                 "that the registration lacks documents"})
            say("  %-13s 000 NO NETWORK -- no verdict written" % nct)
            continue
        docs = []
        try:
            # documentSection, NOT protocolSection. The first version read
            # protocolSection.largeDocumentModule, which does not exist, so every trial
            # reported "0 documents declared" -- a clean-looking negative that was really a
            # wrong field path. Caught by validating against a KNOWN POSITIVE (NCT04994509
            # publishes two protocol amendments and an SAP) before trusting any zero.
            doc = json.loads(body)
            ld = ((doc.get("documentSection") or {}).get("largeDocumentModule") or {})                 .get("largeDocs") or []
            for x in ld:
                docs.append({"label": x.get("label"), "filename": x.get("filename"),
                             "has_protocol": bool(x.get("hasProtocol")),
                             "has_sap": bool(x.get("hasSap")),
                             "date": x.get("date")})
        except ValueError:
            rows.append({"nct": nct, "verdict": "registration did not parse",
                         "http": code})
            say("  %-13s %s unparseable" % (nct, code))
            continue

        got = []
        for x in docs:
            fn = x.get("filename")
            if not fn:
                continue
            url = "https://cdn.clinicaltrials.gov/large-docs/%s/%s/%s" % (nct[-2:], nct, fn)
            b2, c2 = fetch(url)
            if c2 == 0:
                n000 += 1
                got.append({"filename": fn, "verdict": "NOT ASSESSED -- 000", "http": 0})
                continue
            if c2 == 200 and len(b2) > 5000:
                d = os.path.join(STORE, nct)
                os.makedirs(d, exist_ok=True)
                fp = os.path.join(d, "regdoc_" + fn)
                # PDFs. Written as BYTES: encoding a PDF as utf-8 text corrupts it silently
                # and the corruption is invisible until someone tries to read the document.
                raw_bytes = b2.encode("utf-8", "surrogateescape")
                io.open(fp, "wb").write(raw_bytes)
                got.append({"filename": fn, "http": c2, "bytes": len(raw_bytes),
                            "sha256": hashlib.sha256(raw_bytes).hexdigest(),
                            "path": os.path.relpath(fp, REPO).replace("\\", "/"),
                            "has_protocol": x["has_protocol"], "has_sap": x["has_sap"],
                            "retrieved_utc": TODAY})
            else:
                got.append({"filename": fn, "http": c2,
                            "verdict": "refused or not a document",
                            "bytes": len(b2)})
            time.sleep(0.3)

        rows.append({"nct": nct, "http": code, "declared_documents": len(docs),
                     "documents_retrieved": len([g for g in got if g.get("sha256")]),
                     "documents": got,
                     "verdict": ("no documents declared on the registration" if not docs
                                 else "declared %d" % len(docs))})
        say("  %-13s declared=%-2d retrieved=%d"
            % (nct, len(docs), len([g for g in got if g.get("sha256")])))
        time.sleep(0.25)

    old = {"rows": []}
    if os.path.exists(OUT):
        try:
            old = json.load(io.open(OUT, encoding="utf-8"))
        except ValueError:
            pass
    done = set(r["nct"] for r in rows)
    old["rows"] = [r for r in old.get("rows", []) if r["nct"] not in done] + rows
    old["keyed_on"] = "NCT only -- an NCT cannot collide, unlike the doi/pmcid extraction " \
                      "that produced 19 shared identifiers and 5 quarantined documents"
    old["guards"] = ["a 000 is not a paywall -- no verdict is written on a transport failure",
                     "a 200 is not a document -- a body under 5000 bytes is not stored"]
    json.dump(old, io.open(OUT, "w", encoding="utf-8"), indent=1)

    ret = sum(r.get("documents_retrieved", 0) for r in rows)
    say("")
    say("SUMMARY batch=%d..%d trials=%d docs_retrieved=%d transport_failures=%d"
        % (start, start + len(batch), len(batch), ret, n000))
    if n000:
        say("WARNING %d transport failure(s) -- those trials have NO verdict and must be "
            "re-run from a networked host" % n000)
    return 0


if __name__ == "__main__":
    sys.exit(main())
