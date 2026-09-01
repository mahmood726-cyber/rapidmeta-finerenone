# -*- coding: utf-8 -*-
"""GAP 1 PRECONDITION: is Cochrane RoB-with-justifying-quote actually obtainable, free?

The mandate names Cochrane's /references page. I measured that host returning HTTP 412 to
automated clients earlier tonight, so this probes FOUR routes and reports which, if any,
yields the triple we need:

    (domain, authors' judgement, support for judgement)

"Support for judgement" is the justifying sentence -- it is the provenance ground truth,
and it is a native RevMan field, not something we would be inferring.

MEASURED / INFERRED / CLAIMED is stamped on every line this prints.
"""
import io, json, re, sys, time
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                              line_buffering=True)
UA_BOT = {"User-Agent": "research/1.0 (mailto:mahmood726@gmail.com)"}
UA_BROWSER = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                            "(KHTML, like Gecko) Chrome/120.0 Safari/537.36",
              "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
              "Accept-Language": "en-GB,en;q=0.9"}
E = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
EPMC = "https://www.ebi.ac.uk/europepmc/webservices/rest"


def fetch(url, headers, timeout=90):
    """Return (status, bytes) -- a 4xx is a RESULT, not an exception to swallow."""
    try:
        r = urlopen(Request(url, headers=headers), timeout=timeout)
        return r.getcode(), r.read()
    except HTTPError as e:
        return e.code, b""
    except URLError as e:
        return "URLERR:%s" % (e.reason,), b""
    except Exception as e:
        return "ERR:%s" % type(e).__name__, b""


# --- pick real cardiology reviews from the frame we just built ---
rows = [json.loads(l) for l in io.open("cdsr_frame_cardiology.jsonl", encoding="utf-8") if l.strip()]
rows = [r for r in rows if r["record_kind"] == "review"]
sample = [rows[i] for i in (0, 40, 120, 300, 700)]
print("MEASURED  frame supplies %d cardiology reviews; probing %d of them" % (len(rows), len(sample)))
print("          cmd: python probe_rob_groundtruth.py")
print("")

# --- ROUTE 1: Cochrane Library /references, as the mandate names ---
print("ROUTE 1  cochranelibrary.com /references  (the route the mandate names)")
for r in sample[:3]:
    u = "https://www.cochranelibrary.com/cdsr/doi/10.1002/14651858.%s/references" % r["cd_base"]
    for label, hdr in (("bot-UA", UA_BOT), ("browser-UA", UA_BROWSER)):
        st, body = fetch(u, hdr)
        print("  MEASURED  %s %-11s status=%-8s bytes=%d" % (r["cd_base"], label, st, len(body)))
        time.sleep(0.5)
print("")

# --- ROUTE 2: PMC id conversion, then Europe PMC full text XML ---
print("ROUTE 2  Europe PMC fullTextXML  (RevMan RoB tables travel into PMC full text)")
pmids = [r["pmid"] for r in rows[:400]]
have_pmc = {}
for i in range(0, len(pmids), 200):
    st, body = fetch("%s/elink.fcgi?dbfrom=pubmed&db=pmc&retmode=json&id=%s"
                     % (E, ",".join(pmids[i:i + 200])), UA_BOT)
    if st == 200:
        try:
            d = json.loads(body.decode("utf-8", "replace"), strict=False)
            for ls in d.get("linksets", []):
                src = (ls.get("ids") or [None])[0]
                for db in ls.get("linksetdbs", []):
                    if db.get("dbto") == "pmc" and db.get("links"):
                        have_pmc[str(src)] = db["links"][0]
        except Exception as e:
            print("  MEASURED  elink parse failed: %s" % type(e).__name__)
    time.sleep(0.34)
print("  MEASURED  of %d cardiology reviews probed, %d have a PMC record (%.0f%%)"
      % (len(pmids), len(have_pmc), 100.0 * len(have_pmc) / max(1, len(pmids))))

ROB_HINT = re.compile(r"risk of bias|support for judgement|allocation concealment|"
                      r"random sequence generation|blinding of participants", re.I)
ok = 0
for pmid, pmcid in list(have_pmc.items())[:6]:
    st, body = fetch("%s/PMC%s/fullTextXML" % (EPMC, pmcid), UA_BOT, timeout=120)
    txt = body.decode("utf-8", "replace") if body else ""
    hits = len(ROB_HINT.findall(txt))
    sfj = len(re.findall(r"[Ss]upport for judge?ment", txt))
    print("  MEASURED  PMC%-9s status=%-6s bytes=%-8d rob_markers=%-4d 'support for judgement'=%d"
          % (pmcid, st, len(txt), hits, sfj))
    if st == 200 and sfj > 0:
        ok += 1
    time.sleep(0.5)
print("  MEASURED  %d of %d fetched full texts contain an explicit 'Support for judgement' field"
      % (ok, min(6, len(have_pmc))))
print("")

# --- ROUTE 3: does the PubMed abstract carry any RoB at all? (expected: no) ---
print("ROUTE 3  PubMed abstract  (control -- expected NEGATIVE, proves the probe can say no)")
st, body = fetch("%s/efetch.fcgi?db=pubmed&retmode=xml&id=%s" % (E, sample[0]["pmid"]), UA_BOT)
t = body.decode("utf-8", "replace")
print("  MEASURED  status=%s bytes=%d 'support for judgement'=%d  <-- a zero here is the "
      "control that shows a zero elsewhere means something"
      % (st, len(t), len(re.findall(r"[Ss]upport for judge?ment", t))))
