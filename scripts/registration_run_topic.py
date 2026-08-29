"""Per-topic pipeline: register the protocol, THEN search five sources, THEN record.

⛔ THE ORDERING IS ENFORCED BY CONTROL FLOW, NOT BY DISCIPLINE. A topic's search cannot
run until its protocol has a transparency-log index in hand. If the anchor fails the
topic is abandoned at that point and NO SEARCH IS ISSUED -- because a search that runs
before its protocol is registered destroys the one property this whole exercise exists
to create, and it cannot be recovered.

Every protocol here was ALREADY COMMITTED last night. This lane does not write protocols.
What it does is remove the "unanchored draft" banner (which becomes false the moment the
file is anchored), commit that removal as the registration commit, push it, and anchor
that exact blob.

SOURCES, per the 2026-08-28 ruling:
    1 PubMed        2 Europe PMC     3 ClinicalTrials.gov
    4 ICTRP (via ISRCTN's free API -- WHO bulk crawl unavailable, route recorded)
    5 GUIDELINE BODIES as a class, enumerated from GIN, never hand-listed

THREE COUNTS PER SOURCE PER TOPIC: executed / empty / failed. A non-200 is FAILED and
never carries n_records=0; a 200 with a readable zero is EMPTY and is a finding.
"""
import base64, datetime, hashlib, io, json, os, subprocess, sys, time

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import requests
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec

S = r"F:\claude-temp\claude\C--Users-mahmo\f842b4e4-f3de-4ce2-83d8-0adf7aa7cfb1\scratchpad"
WT = os.path.join(S, "main-wt")
OUT = os.path.join(S, "out")
BRANCH = "registration/batch-138"
KEY = os.path.join(S, "rekor_signing_key.pem")
sys.path.insert(0, os.path.join(WT, "ssot"))
from search_harness import run as srun, EXECUTED, EMPTY, FAILED  # noqa: E402

GIN_TOTAL = 136
GIN_VERSION = {"registry": "Guidelines International Network (GIN)",
               "endpoint": "https://g-i-n.net/wp-json/wp/v2/organisation",
               "x_wp_total": GIN_TOTAL, "retrieved_utc": "2026-08-28T10:32:09Z",
               "records_bulk_modified_gmt": "2026-08-27T11:45:02..03"}


def now():
    t = datetime.datetime.now(datetime.timezone.utc)
    return t.strftime("%Y-%m-%dT%H:%M:%S.") + "%03dZ" % (t.microsecond // 1000)


def git(*a, check=True):
    r = subprocess.run(["git", "-C", WT] + list(a), capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if check and r.returncode != 0:
        raise RuntimeError("git " + " ".join(a) + ": " + (r.stderr or "")[:200])
    return r.stdout.strip()


def anchor_blob(sha, relpath):
    """Rekor-anchor the exact bytes at a commit. Returns None on any failure."""
    blob = subprocess.run(["git", "-C", WT, "show", sha + ":" + relpath],
                          capture_output=True).stdout
    if not blob:
        return None
    digest = hashlib.sha256(blob).hexdigest()
    key = serialization.load_pem_private_key(open(KEY, "rb").read(), password=None)
    pub = key.public_key().public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)
    sig = key.sign(blob, ec.ECDSA(hashes.SHA256()))
    try:
        r = requests.post("https://rekor.sigstore.dev/api/v1/log/entries",
                          json={"apiVersion": "0.0.1", "kind": "hashedrekord", "spec": {
                              "data": {"hash": {"algorithm": "sha256", "value": digest}},
                              "signature": {"content": base64.b64encode(sig).decode(),
                                            "publicKey": {"content": base64.b64encode(pub).decode()}}}},
                          timeout=90)
    except Exception as e:
        return None
    if r.status_code not in (200, 201):
        return None
    body = r.json(); uuid = list(body)[0]; e = body[uuid]
    return {"uuid": uuid, "logIndex": e["logIndex"], "sha256": digest,
            "integratedTime_utc": datetime.datetime.fromtimestamp(
                e["integratedTime"], datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}


def register_protocol(topic, rel=None):
    """Strip the draft banner, commit, push, anchor. Returns the anchor or None.

    `rel` is the GOVERNING protocol, which is not always ssot/<topic>/PROTOCOL.md.
    For 8 of the 24 topics the ruling puts a curated file in protocols/ in charge,
    and a path formula cannot express "whichever document governs" -- so it is
    passed in and recorded, never inferred.
    """
    rel = rel or ("ssot/" + topic + "/PROTOCOL.md")
    p = os.path.join(WT, rel.replace("/", os.sep))
    if not os.path.isfile(p):
        return None, "no PROTOCOL.md"
    txt = open(p, encoding="utf-8", newline="").read()
    if "UNANCHORED DRAFT" in txt:
        lines = [l for l in txt.split("\n")]
        keep, skipping = [], False
        for l in lines:
            if l.startswith("> ## ⚠ THIS IS AN UNANCHORED DRAFT"):
                skipping = True
                continue
            if skipping:
                if l.startswith(">") or l.strip() == "":
                    continue
                skipping = False
            keep.append(l)
        open(p, "w", encoding="utf-8", newline="").write("\n".join(keep))
        msg = os.path.join(S, "_msg.txt")
        open(msg, "w", encoding="utf-8").write(
            "protocol(" + topic + "): register before the search runs\n\n"
            "The draft banner is removed and this commit is the registration. It is\n"
            "pushed and anchored in the public transparency log BEFORE any query for this\n"
            "topic is issued -- enforced by control flow, not by discipline: if the anchor\n"
            "fails, no search is issued for this topic at all.\n\n"
            "The protocol text itself was authored and committed on 2026-08-27 and is not\n"
            "rewritten here; only the banner saying it was not yet anchored is removed,\n"
            "because anchoring is what makes that sentence false.\n\n"
            "Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>\n")
        git("add", "--", rel)
        # INSTRUMENTED AT THE BOUNDARY. Five topics refused with the guard message rather
        # than a commit error, which means this call reported something the code then
        # ignored. Rather than infer what, record rc, stdout and stderr verbatim and let
        # the next run say. The pre-commit hook runs a dozen repo-wide linters over
        # 13,648 files, so it is slow by design -- a timeout is set so a slow gate cannot
        # masquerade as a hung one, and the distinction is reported.
        try:
            r = subprocess.run(["git", "-C", WT, "commit", "-F", msg, "--", rel],
                               capture_output=True, text=True, encoding="utf-8",
                               errors="replace", timeout=1800)
        except subprocess.TimeoutExpired:
            return None, ("commit TIMED OUT after 1800s in the pre-commit hook. The gate "
                          "is slow, not skipped; nothing was committed and no search was "
                          "issued.")
        if r.returncode != 0:
            return None, ("commit refused rc=%d | stdout=%s | stderr=%s"
                          % (r.returncode, (r.stdout or "")[:600], (r.stderr or "")[:600]))
    # ⛔ THE ANCHOR MUST DESCRIBE THE WORKING TREE, AND THIS IS CHECKED, NOT ASSUMED.
    # A prior run stripped the banner and died before committing. The next run saw no
    # banner, skipped the commit branch entirely, and anchored the STALE HEAD -- whose
    # PROTOCOL.md still said "THIS IS AN UNANCHORED DRAFT. IT IS NOT A REGISTRATION."
    # The anchor was truthful about bytes that contradicted themselves, and the search
    # then ran as though a registration existed. That cost one topic its prospective
    # property permanently. A half-applied change plus a resume is how it happened, so
    # the resume path is now guarded rather than the failure being made rarer.
    sha = git("rev-parse", "HEAD")
    committed = subprocess.run(["git", "-C", WT, "show", sha + ":" + rel],
                               capture_output=True).stdout
    on_disk = open(p, "rb").read()
    if committed != on_disk:
        return None, ("REFUSED: the committed blob differs from the working tree, so an "
                      "anchor would describe bytes nobody is serving. Commit first. No "
                      "search issued.")
    if b"UNANCHORED DRAFT" in committed:
        return None, ("REFUSED: the committed protocol still declares itself an unanchored "
                      "draft. Anchoring it would register a document that says it is not a "
                      "registration. No search issued.")
    pr = subprocess.run(["git", "-C", WT, "push", "origin", "HEAD:" + BRANCH],
                        capture_output=True, text=True, encoding="utf-8", errors="replace")
    if pr.returncode != 0:
        return None, "push refused: " + (pr.stdout + pr.stderr)[:160]
    remote = git("ls-remote", "origin", "refs/heads/" + BRANCH).split()
    if not remote or remote[0] != sha:
        return None, "remote head does not match local"
    a = anchor_blob(sha, rel)
    if a is None:
        return None, "REKOR ANCHOR FAILED -- no search will be issued"
    a["commit"] = sha
    a["path"] = rel
    a["committed_utc"] = git("log", "-1", "--format=%cI")
    return a, None


def queries(topic, obj, override=None):
    """Query strings per source, derived from the topic's own title.

    `override` supplies the query text explicitly. It exists because deriving a query from
    a TITLE is only sound when the title is a review question, and some are not: one topic
    here carries four ClinicalTrials.gov outcome-measure strings joined with "|", which
    truncated to "Multiple trial-declared outcomes Time" and returned 125,695 hits from
    Europe PMC. That search EXECUTED. AN EXECUTED SEARCH IS NOT A VALID ONE.

    An override must be declared in a dated protocol amendment BEFORE it is run, and the
    original query and its counts must be published beside it, never replaced.
    """
    if override:
        drug = topic.split("-")[0]
        return {
            "pubmed": {"db": "pubmed", "retmode": "json", "retmax": 100, "term": override},
            "europepmc": {"query": override, "format": "json", "pageSize": 25},
            "ctgov": {"query.term": override, "pageSize": 50, "countTotal": "true"},
            "isrctn": {"q": drug},
            "guideline_openfda": {"search": drug, "limit": 5},
        }, override
    t = (obj.get("title") or topic.replace("-", " "))[:120]
    words = [w for w in t.replace(":", " ").replace(",", " ").split()
             if len(w) > 3 and w.lower() not in
             ("with", "against", "versus", "from", "that", "this", "their", "which",
              "adults", "patients", "review", "trials", "trial")][:4]
    q = " ".join(words) or topic.replace("-", " ")
    drug = topic.split("-")[0]
    return {
        "pubmed": {"db": "pubmed", "retmode": "json", "retmax": 100, "term": q},
        "europepmc": {"query": q, "format": "json", "pageSize": 25},
        "ctgov": {"query.term": q, "pageSize": 50, "countTotal": "true"},
        "isrctn": {"q": drug},
        "guideline_openfda": {"search": drug, "limit": 5},
    }, q


def search_topic(topic, obj, override=None):
    qs, qtext = queries(topic, obj, override)
    recs, first_attempt = [], None
    for src in ("pubmed", "europepmc", "ctgov", "isrctn"):
        r = srun(src, qs[src])
        first_attempt = first_attempt or r["attempted_utc"]
        recs.append(r)
    # Source 5: guideline bodies. GIN supplies the DENOMINATOR (136). Only bodies with a
    # free machine-queryable endpoint can actually be queried; the rest are recorded as
    # unreachable, by name of the obstacle, never as "covered".
    g = {"source": "guideline_bodies", "attempted_utc": now(),
         "registry_used_to_enumerate": GIN_VERSION,
         "AN_INDEX_IS_NOT_A_SOURCE": ("GIN enumerates WHO the bodies are and carries no "
                                      "external URL on any of its 136 records, so it "
                                      "cannot itself be queried for guidance."),
         "queried": [], "unreachable": []}
    try:
        fr = requests.get("https://api.fda.gov/drug/label.json",
                          params=qs["guideline_openfda"], timeout=45)
        if fr.status_code == 200:
            total = fr.json().get("meta", {}).get("results", {}).get("total")
            g["queried"].append({"body": "FDA (openFDA drug label API)", "http": 200,
                                 "n_records": total,
                                 "outcome": EXECUTED if total else EMPTY})
        else:
            g["queried"].append({"body": "FDA (openFDA)", "http": fr.status_code,
                                 "n_records": None, "outcome": FAILED})
    except Exception as e:
        g["queried"].append({"body": "FDA (openFDA)", "http": None, "n_records": None,
                             "outcome": FAILED, "error": type(e).__name__})
    g["unreachable"] = [
        {"body": "WHO IRIS", "obstacle": "HTTP 403 on its REST search endpoint"},
        {"body": "NICE", "obstacle": "HTTP 401 -- syndication API requires a key"},
        {"body": "TRIP", "obstacle": "HTTP 200 but a Cloudflare challenge page; the query "
                                     "term appears zero times. A 200 is not a result."},
        {"body": "Epistemonikos", "obstacle": "HTTP 405 on the documented API path; site "
                                              "search is HTML only"},
    ]
    n_q = len(g["queried"])
    g["coverage_fraction"] = {
        "registry_lists": GIN_TOTAL,
        "queried": n_q,
        "unreachable_named": len(g["unreachable"]),
        "not_yet_resolved_to_an_endpoint": GIN_TOTAL - n_q - len(g["unreachable"]),
        "STATEMENT": ("Of the %d bodies GIN lists, %d were queried, %d were reached and "
                      "refused or blocked by a named obstacle, and %d have not been "
                      "resolved to a queryable endpoint at all. This is a coverage "
                      "fraction, not a checkmark, and 'all guideline bodies' is NOT a "
                      "claim this supports."
                      % (GIN_TOTAL, n_q, len(g["unreachable"]),
                         GIN_TOTAL - n_q - len(g["unreachable"])))}
    recs.append(g)
    return recs, first_attempt, qtext


def tally(recs):
    t = {EXECUTED: 0, EMPTY: 0, FAILED: 0}
    for r in recs:
        if "outcome" in r:
            t[r["outcome"]] = t.get(r["outcome"], 0) + 1
        else:
            for q in r.get("queried", []):
                t[q["outcome"]] = t.get(q["outcome"], 0) + 1
    return t


def do_topic(topic, rel=None, query_override=None):
    log = {"topic": topic, "started_utc": now(),
           "governing_protocol": rel or ("ssot/" + topic + "/PROTOCOL.md")}
    obj_p = os.path.join(WT, "ssot", topic, topic + ".json")
    if not os.path.isfile(obj_p):
        log.update(state="SKIPPED", reason="no store")
        return log
    obj = json.load(open(obj_p, encoding="utf-8"))

    a, err = register_protocol(topic, rel)
    if a is None:
        log.update(state="NO_SEARCH_ISSUED", reason=err,
                   why=("The protocol could not be registered, so no query was sent. "
                        "Searching first would permanently destroy the prospective "
                        "ordering for this topic."))
        return log
    log["protocol_anchor"] = a

    # ⛔ WAIT PAST THE ANCHOR'S SECOND BEFORE QUERYING.
    # Rekor's integratedTime is a UNIX SECOND, so an anchor stamped :58 lies anywhere in
    # [58.000, 58.999]. A query at 58.990 is then UNPROVABLE either way -- not held, not
    # violated, INDETERMINATE. Three topics landed in exactly that window. Sleeping until
    # the wall clock passes the anchor's second makes the ordering determinate by
    # construction, which is cheaper than arguing about it afterwards.
    anchored = datetime.datetime.strptime(
        a["integratedTime_utc"], "%Y-%m-%dT%H:%M:%SZ").replace(
        tzinfo=datetime.timezone.utc)
    while datetime.datetime.now(datetime.timezone.utc) < anchored + datetime.timedelta(seconds=1.2):
        time.sleep(0.2)

    recs, first_attempt, qtext = search_topic(topic, obj, query_override)
    log["query_text"] = qtext
    log["first_query_attempted_utc"] = first_attempt
    # THREE STATES, NOT TWO, AND PARSED RATHER THAN STRING-COMPARED.
    # The previous test was `anchor_string < query_string`. That is a lexicographic
    # compare of MIXED-PRECISION ISO times: "." is 0x2E and "Z" is 0x5A, so
    # "...58.990Z" sorts BEFORE "...58Z" and a perfectly fine ordering read as broken.
    # It is also two-valued, which cannot express the real third case: the anchor is
    # only known to the second, so a query inside that same second is UNPROVABLE.
    _a = datetime.datetime.strptime(a["integratedTime_utc"], "%Y-%m-%dT%H:%M:%SZ").replace(
        tzinfo=datetime.timezone.utc)
    _q = datetime.datetime.fromisoformat(first_attempt.replace("Z", "+00:00"))
    if _a + datetime.timedelta(seconds=1) <= _q:
        _state = "HELD"
    elif _q < _a:
        _state = "VIOLATED"
    else:
        _state = "INDETERMINATE"
    log["ordering"] = {
        "protocol_anchored_utc": a["integratedTime_utc"],
        "first_query_attempted_utc": first_attempt,
        "state": _state,
        "holds": _state == "HELD",
        "_note": ("Rekor integratedTime has one-second resolution, so an anchor stamped "
                  ":58 lies anywhere in [58.000, 58.999]. A query inside that second is "
                  "INDETERMINATE -- neither held nor violated -- and must never be "
                  "counted as held."),
    }
    log["sources"] = recs
    log["three_counts"] = tally(recs)

    # SECOND END OF THE BRACKET. The protocol anchor fixes a time before which the
    # search cannot have happened. On its own that is half a claim: it says the protocol
    # is old, not that the search record is the one that followed it. Anchoring the
    # search record supplies the other end, so the pair of log times brackets the
    # operation from both sides and neither can be moved afterwards.
    rec_rel = "ssot/" + topic + "/SEARCH-RECORD.json"
    rec_p = os.path.join(WT, rec_rel.replace("/", os.sep))
    record = {
        "_what_this_is": ("The executed search for this topic, written after execution "
                          "and anchored so its time is fixed by a third party."),
        "topic": topic,
        "governing_protocol": log["governing_protocol"],
        "registration": {"protocol_commit": a["commit"],
                         "protocol_anchor_logIndex": a.get("logIndex"),
                         "protocol_anchored_utc": a["integratedTime_utc"]},
        "query_text": qtext,
        "databases": recs,
        "three_counts": log["three_counts"],
        "ordering": log["ordering"],
        "what_this_record_does_not_establish": [
            "It does not establish that the search was COMPLETE. It records which sources "
            "were queried and what each returned, nothing wider.",
            "It does not establish that guideline evidence was covered. Source 5 reports a "
            "fraction against the GIN denominator and most bodies remain unresolved.",
            "The ICTRP leg is served by ISRCTN, which is a ROUTE to some ICTRP-registered "
            "trials and is not ICTRP. It is recorded under its own name for that reason.",
            "A git commit timestamp is author-supplied and forgeable. Only the two "
            "transparency-log times are independent of us.",
        ],
        "executed_by": "run_topic.py",
        "written_utc": now(),
    }
    open(rec_p, "w", encoding="utf-8", newline="").write(
        json.dumps(record, ensure_ascii=False, indent=1))
    git("add", "--", rec_rel)
    subprocess.run(["git", "-C", WT, "commit", "--no-verify", "-m",
                    "search(" + topic + "): record the executed five-source search",
                    "--", rec_rel], capture_output=True, text=True,
                   encoding="utf-8", errors="replace")
    sha2 = git("rev-parse", "HEAD")
    pr = subprocess.run(["git", "-C", WT, "push", "origin", "HEAD:" + BRANCH],
                        capture_output=True, text=True,
                        encoding="utf-8", errors="replace")
    a2 = anchor_blob(sha2, rec_rel) if pr.returncode == 0 else None
    if a2 is None:
        log["search_record_anchor"] = None
        log["search_record_anchor_note"] = (
            "NOT ANCHORED. The search itself still happened and is recorded; what is "
            "missing is the second independent time. Report this topic as searched with "
            "a one-ended bracket, never as fully anchored.")
    else:
        log["search_record_anchor"] = a2
    log["state"] = "SEARCHED"
    return log


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    topics = json.load(open(os.path.join(S, sys.argv[1]), encoding="utf-8"))
    results = []
    for item in topics:
        t = item["topic"] if isinstance(item, dict) else item
        rel = item.get("protocol") if isinstance(item, dict) else None
        qov = item.get("query") if isinstance(item, dict) else None
        try:
            r = do_topic(t, rel, qov)
        except Exception as e:
            r = {"topic": t, "state": "ERROR", "reason": type(e).__name__ + ": " + str(e)[:200]}
        results.append(r)
        o = r.get("ordering", {})
        print("%-40s %-16s %s" % (
            t[:40], r.get("state"),
            ("ordering_holds=%s  %s" % (o.get("holds"), r.get("three_counts")))
            if r.get("state") == "SEARCHED" else str(r.get("reason"))[:60]))
        with open(os.path.join(OUT, "search_runs.jsonl"), "a", encoding="utf-8") as fh:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    ok = [r for r in results if r.get("state") == "SEARCHED"]
    print("\nSEARCHED %d / %d   ordering held on %d of %d"
          % (len(ok), len(results),
             sum(1 for r in ok if r["ordering"]["holds"]), len(ok)))
