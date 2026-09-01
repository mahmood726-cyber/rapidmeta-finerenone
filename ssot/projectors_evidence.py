# -*- coding: utf-8 -*-
"""Three tabs that were showing summaries where the format requires the working.

All three are GENERATOR COMPONENTS: they read any canon, key on declared field
paths, and render "" when the object holds nothing. Adding a topic adds no code.

WHY THESE THREE, AND IN THIS ORDER OF VALUE.

  SEARCH. `search_executed_2026_08_30` holds a fully executed six-source search
  -- concept block, reported against retrieved per source, screen, coverage
  fraction, four named limits -- and the Search tab rendered 343 BYTES AND ZERO
  ROWS, because no projector had ever been written for it. The search axis is
  the one this project loses 0-5 to Cochrane on. ⇒ WE ARE BEING MARKED DOWN FOR
  SOMETHING ALREADY IN THE STORE AND MERELY UNRENDERED. Sixteen other objects
  hold a differently-shaped `search` + `prisma_flow` pair; both shapes render
  here or the card names the one it could not read.

  EXTRACTION. 57 rows, ZERO outbound links. Every extracted datum names its
  source in prose and none of it is clickable. Measured corpus-wide: 171 of 179
  per-trial rows (96%) across 49 objects carry an NCT, a PMID or a source URL,
  so this is a rendering gap and not a data gap -- the same shape as 403
  identifiers stored with 76.4% of pages rendering none.

  SCREENING. A decision-COUNT table where a per-record LIST belongs: 14 rows
  against 1,443 decided records, with the ledger sitting in a JSON file beside
  the page. ⛔ A CITATION TO A FILE THE READER CANNOT OPEN IS NOT TRANSPARENCY,
  IT IS A RECEIPT FOR TRANSPARENCY. The ledger renders INTO the page here.

NO NETWORK. NO TOPIC NAMES.
"""
import html
import re

_MAX_LEDGER_ROWS = 4000          # a bound, declared, not a silent truncation


def _e(x):
    return html.escape("—" if x is None else str(x))


def _card(title, inner, cls="card"):
    return "<div class='%s'>\n  <h2>%s</h2>\n%s</div>\n" % (cls, _e(title), inner)


def _para(s):
    return "  <p>%s</p>\n" % _e(s)


def _small(s):
    return "  <p><small>%s</small></p>\n" % _e(s)


def _h3(s):
    return "  <h3>%s</h3>\n" % _e(s)


def _warn(s):
    return "  <div class='absent-state'>%s</div>\n" % _e(s)


def _tbl(headers, rows, caption=None):
    if not rows:
        return ""
    out = "  <div class='tscroll'><table>\n"
    if caption:
        out += "    <caption>%s</caption>\n" % _e(caption)
    out += "    <tr>" + "".join("<th scope='col'>%s</th>" % _e(h)
                                for h in headers) + "</tr>\n"
    out += "".join(rows)
    return out + "  </table></div>\n"


# --------------------------------------------------------------- LINKING ----
def source_link(row):
    """A clickable source for one extracted row, or None.

    ⭐ THE ORDER IS A DECLARATION, NOT A PREFERENCE. A registration is the
    stronger link because it is the record the counts were read from; a PMID
    points at a paper that may report different counts, which is the count-tier
    judgement and not the same object. Where a row carries both, the registry
    wins and the paper is offered beside it.
    """
    if not isinstance(row, dict):
        return None
    u = row.get("source_url") or row.get("url")
    if u and str(u).startswith("http"):
        return (str(u), "source_url")
    nct = row.get("nct") or row.get("trial_id") or row.get("nct_id")
    if nct and str(nct).upper().startswith("NCT"):
        return ("https://clinicaltrials.gov/study/%s" % str(nct).strip(), "nct")
    pmid = row.get("pmid")
    if pmid and str(pmid).strip().isdigit():
        return ("https://pubmed.ncbi.nlm.nih.gov/%s/" % str(pmid).strip(), "pmid")
    isrctn = row.get("isrctn")
    if isrctn:
        return ("https://www.isrctn.com/%s" % str(isrctn).strip(), "isrctn")
    return None


def _a(url, text):
    return "<a href='%s' rel='noopener'>%s</a>" % (_e(url), _e(text))


# ---------------------------------------------------------------- SEARCH ----
def _search_blocks(canon):
    """Every search-shaped block, newest-declared first, with its field path."""
    found = []
    for k in canon:
        kl = str(k).lower()
        if kl.startswith("search_executed"):
            v = canon.get(k)
            if isinstance(v, dict):
                found.append((k, v))
    found.sort(key=lambda x: x[0], reverse=True)
    v = canon.get("search")
    if isinstance(v, dict):
        found.append(("search", v))
    return found


def search_card(canon, p=None):
    blocks = _search_blocks(canon)
    prisma = canon.get("prisma_flow") if isinstance(canon.get("prisma_flow"), dict) else None
    if not blocks and not prisma:
        return ""

    inner = ""
    for path, b in blocks:
        inner += _h3("Search record: %s" % path)
        for key in ("search_date", "executed_utc", "executed_by", "scope_rule",
                    "_scope"):
            if b.get(key):
                inner += _small("%s — %s" % (key, b[key]))

        cb = b.get("concept_block")
        if isinstance(cb, list) and cb:
            inner += _para("Concept block, as executed: %s"
                           % "; ".join(str(x) for x in cb))
        if b.get("no_and_block_because"):
            inner += _small(b["no_and_block_because"])
        if b.get("development_codes_included_because"):
            inner += _small(b["development_codes_included_because"])

        # SOURCES: reported against retrieved. The whole point of the table.
        srcs = b.get("sources")
        rows = ""
        if isinstance(srcs, list):
            for s in srcs:
                if not isinstance(s, dict):
                    continue
                st = str(s.get("status") or "")
                cls = "warn" if st and st not in ("OK", "EMPTY") else ""
                rows += ("    <tr class='%s'><td>%s</td><td><strong>%s</strong></td>"
                         "<td>%s</td><td>%s</td><td><small>%s</small></td></tr>\n"
                         % (cls, _e(s.get("source")), _e(st),
                            _e(s.get("reported")), _e(s.get("retrieved")),
                            _e(s.get("note") or s.get("note_2026_08_30_LATER") or "")))
        elif isinstance(srcs, dict):
            for name, s in srcs.items():
                d = s if isinstance(s, dict) else {}
                rows += ("    <tr><td>%s</td><td><strong>%s</strong></td>"
                         "<td>%s</td><td>%s</td><td></td></tr>\n"
                         % (_e(name), _e(d.get("status")), _e(d.get("reported")),
                            _e(d.get("retrieved"))))
        if rows:
            inner += _tbl(["Source", "Status", "Reported", "Retrieved", "Note"],
                          [rows],
                          "Sources searched — reported against retrieved. A "
                          "source whose reported count exceeds what was "
                          "retrieved is TRUNCATED and says so.")
        # ⛔ TWO SHAPES, AND JOINING BLINDLY CRASHED THE BUILD. This read
        # `", ".join(dbs)` under a comment saying "databases in the older shape"
        # -- and the newer shape is a list of DICTS:
        #
        #     {"database": "ClinicalTrials.gov API v2 -- CHOSEN QUERY",
        #      "tool": "https://clinicaltrials.gov/api/v2/studies?..."}
        #
        # so the build died with "TypeError: sequence item 0: expected str
        # instance, dict found" on 2 of the first 5 pages of a rebuild that was
        # about to run over 148. A comment naming the shape it handles is not a
        # guard against the shape it does not.
        #
        # ⭐ AND THE DICT SHAPE IS RICHER, so it is RENDERED rather than
        # flattened: the database name, and its query as a link where the tool
        # field is one. An entry of neither shape is NAMED, not skipped and not
        # crashed on -- a source dropped silently from "Databases:" is a search
        # that looks narrower than it was.
        dbs = b.get("databases")
        if dbs and not rows:
            if isinstance(dbs, str):
                inner += _para("Databases: %s" % _e(dbs))
            elif isinstance(dbs, list):
                parts, odd = [], 0
                for d in dbs:
                    if isinstance(d, str):
                        parts.append(_e(d))
                    elif isinstance(d, dict):
                        nm = str(d.get("database") or d.get("name")
                                 or d.get("source") or "").strip()
                        tool = str(d.get("tool") or d.get("url") or "").strip()
                        if nm and tool.startswith("http"):
                            parts.append("%s (%s)" % (_e(nm), _a(tool, "query")))
                        elif nm:
                            parts.append(_e(nm))
                        else:
                            odd += 1
                    else:
                        odd += 1
                if parts:
                    inner += _para("Databases: %s" % ", ".join(parts))
                if odd:
                    inner += _para("<em>%d source entr%s carried neither a name nor "
                                   "a recognised shape and are NOT listed above. "
                                   "They are counted here rather than dropped: a "
                                   "source missing from this line makes the search "
                                   "look narrower than it was.</em>"
                                   % (odd, "y" if odd == 1 else "ies"))
            else:
                inner += _para("<em>the databases field is a %s, which this "
                               "renderer cannot list; the search is not described "
                               "here rather than being described wrongly.</em>"
                               % type(dbs).__name__)

        cov = b.get("coverage_fraction")
        if isinstance(cov, dict):
            inner += (_h3("Coverage")
                      + _para("Recall %s — %s search miss(es)."
                              % (cov.get("recall"), cov.get("search_misses"))))
            for kk in ("denominator_is_now", "means",
                       "what_changed_and_what_did_not", "still_NOT_claimed"):
                if cov.get(kk):
                    inner += _small(cov[kk])

        lims = b.get("limits")
        if isinstance(lims, list) and lims:
            inner += _h3("What this search cannot reach")
            for l in lims:
                inner += _warn(l)
        if b.get("makes_no_claim_about"):
            inner += _warn(b["makes_no_claim_about"])

        rep = b.get("reproduce_with")
        if rep:
            inner += _small("Reproduce with: %s"
                            % (", ".join(rep) if isinstance(rep, list) else rep))

        # older shape: identification / included / reconciliation
        for kk in ("identification", "included", "eligibility_ctgov",
                   "reconciliation", "pagination_verified"):
            if b.get(kk):
                inner += _small("%s — %s" % (kk, str(b[kk])[:600]))

    if isinstance(prisma, dict) and prisma:
        rows = "".join("    <tr><td>%s</td><td><strong>%s</strong></td></tr>\n"
                       % (_e(k.replace("_", " ")), _e(v))
                       for k, v in prisma.items() if not str(k).startswith("_"))
        inner += _h3("PRISMA flow") + _tbl(["Stage", "Records"], [rows])

    return _card("Search — executed, source by source", inner)


# ------------------------------------------------------------ EXTRACTION ----
# Built with chr(92) so no shell transport can turn the word-boundary
# escapes into 0x08 -- that exact defect sat inside a green gate in this
# repo, matching nothing, because grep renders 0x08 as blank.
_BARE_NCT = re.compile(chr(92) + 'ANCT' + chr(92) + 'd{8}' + chr(92) + 'Z')


def extraction_rows_card(canon, p=None):
    """Every extracted per-trial value, EACH LINKED TO WHERE IT CAME FROM."""
    res_by = ((canon.get("results") or {}) if isinstance(canon.get("results"), dict)
              else {}).get("by_outcome") or {}
    if not isinstance(res_by, dict):
        return ""
    inner = ""
    linked = unlinked = 0
    for oid, res in res_by.items():
        if not isinstance(res, dict):
            continue
        per = res.get("per_trial") or []
        if not per:
            continue
        rows = ""
        for t in per:
            if not isinstance(t, dict):
                continue
            link = source_link(t)
            label = t.get("label") or t.get("trial_id") or t.get("nct") or "?"
            # ⛔ A BARE NCT IN THE TRIAL COLUMN IS AN ABSENCE WEARING A VALUE.
            # Where ClinicalTrials.gov records no acronym, the ingest stored the
            # registration id AS the label, so the Trial column reads
            # "NCT02913326" and a reader is left to conclude either that the id
            # IS the trial's name or that we failed to look it up. NEITHER IS
            # TRUE, and saying which costs one clause.
            #
            # Verified against the registry API before writing this sentence,
            # rather than asserting it: NCT02913326, NCT00152971 and NCT06551402
            # all return acronym=None. Each DOES carry a briefTitle, so the name
            # exists and is one click away -- what is missing is the short form.
            #
            # Measured in this tree: 10 rows across 2 pages
            # (DABIGATRAN_VTE_CEREBRAL 4, DABIGATRAN_VTE_SURGICAL 6).
            if _BARE_NCT.match(str(label).strip()):
                label_html = ('%s <small class="muted">&mdash; the registry '
                              'records no acronym for this trial</small>'
                              % _e(str(label).strip()))
            else:
                label_html = _e(label)
            if link:
                linked += 1
                ident = _a(link[0], t.get("nct") or t.get("trial_id") or "source")
                via = link[1]
            else:
                unlinked += 1
                ident = "<em>no identifier on this row</em>"
                via = "—"
            ap = t.get("as_posted") if isinstance(t.get("as_posted"), dict) else {}
            counts = ("%s" % ", ".join("%s %s" % (k, v) for k, v in ap.items())
                      ) if ap else "—"
            rows += ("    <tr><td>%s</td><td>%s</td><td>%s</td>"
                     "<td>%s %s (%s to %s)</td><td><small>%s</small></td>"
                     "<td><small>%s</small></td></tr>\n"
                     % (label_html, ident, _e(via),
                        _e(t.get("measure") or ""), _e(t.get("point")),
                        _e(t.get("ci_low")), _e(t.get("ci_high")),
                        _e(counts), _e(t.get("provenance") or t.get("derivation") or "")))
        if rows:
            inner += (_h3("Outcome %s" % oid)
                      + _tbl(["Trial", "Source", "Linked via", "Effect",
                              "Counts as posted", "Provenance"], [rows],
                             "Every extracted value with a link to the record "
                             "it was read from."))
    if not inner:
        return ""
    tot = linked + unlinked
    head = (_para("Every per-trial value this review pools, with a link to the "
                  "record it came from. Derived by "
                  "ssot/projectors_evidence.py for any topic whose rows carry "
                  "an NCT, a PMID, an ISRCTN or a source URL.")
            + _para("%d of %d rows are linked to a source; %d carry no "
                    "identifier and are shown as unlinked rather than omitted."
                    % (linked, tot, unlinked)))
    if unlinked:
        head += _warn("%d row(s) carry no identifier at all. An extracted "
                      "number with no link to its source does not belong in an "
                      "extraction table, and hiding those rows would make the "
                      "table look complete." % unlinked)
    return _card("Extraction — every datum linked to its source", head + inner)


# ------------------------------------------------------------- SCREENING ----
def _ledger_blocks(canon):
    out = []
    for k in canon:
        v = canon.get(k)
        if isinstance(v, dict) and isinstance(v.get("ledger"), list) and v["ledger"]:
            out.append((k, v))
    sc = canon.get("screening")
    if isinstance(sc, dict) and isinstance(sc.get("records"), list) and sc["records"]:
        out.append(("screening", {"ledger": sc["records"]}))
    return out


def screening_ledger_card(canon, p=None):
    """THE PER-RECORD LIST, IN THE FILE.

    ⛔ A decision-count table where a list belongs is the opposite of this
    format. The ledger is rendered here, in the downloadable page, so a reader
    can pull any record and check the exclusion without a file they do not
    have."""
    blocks = _ledger_blocks(canon)
    if not blocks:
        return ""
    inner = ""
    for path, b in blocks:
        led = b["ledger"]
        shown = led[:_MAX_LEDGER_ROWS]
        rows = ""
        for r in shown:
            if not isinstance(r, dict):
                continue
            dec = str(r.get("decision") or "")
            cls = ("warn" if dec.startswith(("UNDECID", "PASS_OUTSIDE"))
                   else ("ok" if dec.startswith("PASS") else ""))
            ident = r.get("pmid") or r.get("id") or r.get("key") or ""
            link = source_link({"pmid": r.get("pmid"), "nct": r.get("nct")})
            idcell = _a(link[0], ident) if link and ident else _e(ident)
            rows += ("    <tr class='%s'><td>%s</td><td>%s</td>"
                     "<td><strong>%s</strong></td><td><code>%s</code></td>"
                     "<td><small>%s</small></td><td><small>%s</small></td></tr>\n"
                     % (cls, idcell, _e(str(r.get("title") or "")[:150]),
                        _e(dec), _e(r.get("rule")),
                        _e(r.get("field_read")), _e(str(r.get("reason") or "")[:180])))
        inner += (_h3("Every screened record — %d of %d shown"
                      % (len(shown), len(led)))
                  + _tbl(["Record", "Title", "Decision", "Rule", "Field read",
                          "Reason"], [rows],
                         "One row per screened record. The rule id and the "
                         "field it read are shown so an exclusion can be "
                         "checked without trusting the summary."))
        if len(led) > len(shown):
            inner += _warn("⚠️ %d of %d rows are rendered. The remaining %d are "
                           "NOT shown, and this bound is declared rather than "
                           "applied silently -- a truncated list that does not "
                           "say it is truncated is the same defect as a count "
                           "where a list belongs."
                           % (len(shown), len(led), len(led) - len(shown)))
        inner += _small("Rendered from %s.ledger" % path)
    return _card("Screening ledger — every record, in this file", inner)


# ----------------------------------------------- registry screen, per record --
def registry_screen_card(canon, p=None):
    """The REGISTRY screen, one row per candidate.

    ⚠️ 61 of 63 registry exclusions were counts-by-reason with only the two
    withdrawn trials named. That is the same defect as the bibliographic
    count-table at a smaller scale, and it is rendered here whenever the object
    carries per-record dispositions rather than totals."""
    for k in canon:
        v = canon.get(k)
        if not isinstance(v, dict):
            continue
        disp = v.get("screen_per_record") or v.get("registry_dispositions")
        if not isinstance(disp, list) or not disp:
            continue
        rows = ""
        for r in disp:
            if not isinstance(r, dict):
                continue
            nct = r.get("nct") or ""
            link = source_link({"nct": nct})
            dec = str(r.get("decision") or "")
            cls = "ok" if dec.startswith(("INCLUDE", "PASS")) else "warn"
            rows += ("    <tr class='%s'><td>%s</td><td>%s</td>"
                     "<td><strong>%s</strong></td><td><small>%s</small></td></tr>\n"
                     % (cls, _a(link[0], nct) if link else _e(nct),
                        _e(str(r.get("title") or "")[:130]), _e(dec),
                        _e(str(r.get("reason") or "")[:190])))
        return _card("Registry screen — every candidate, with its decision",
                     _para("One row per registration the registry search "
                           "returned. A count by reason cannot be checked; a "
                           "named decision can.")
                     + _tbl(["Registration", "Title", "Decision", "Reason"],
                            [rows]) + _small("Rendered from %s" % k))
    return ""
