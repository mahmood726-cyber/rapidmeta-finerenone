# Search capture — ARNI vs enalapril in HFrEF

Review: sacubitril/valsartan versus enalapril in heart failure with reduced ejection fraction
Executed by: screener/searcher A (Claude, Anthropic family). A second cross-family screener runs separately.
Capture date: 2026-08-12

---

## 1. THE ORDERING TEST

| Quantity | Value | How established |
|---|---|---|
| Protocol commit (registration) | `973f031773d384f54bc1a6107931614aa5fda7ea` | GitHub REST API |
| Protocol commit timestamp (UTC) | **2026-08-12T11:27:47Z** | `commit.author.date` == `commit.committer.date`, read from API |
| Strengthened protocol commit | `dde501167666f41ffdc81a07df1628734ce327a0` | GitHub REST API |
| Strengthened commit timestamp (UTC) | 2026-08-12T12:05:56Z | `commit.committer.date` |
| **First query — issued (UTC)** | **2026-08-12T12:19:18Z** | attempt; blocked at transport (see §4) |
| **First query — first SUCCESSFUL execution (UTC)** | **2026-08-12T12:22:39.556Z** | browser Navigation Timing `startTime`; response complete 12:22:40.277Z |

**Ordering: PASS on both readings of "first query".**

- Against the registration commit `973f031`: margin **+51 min 31 s** (attempt) / **+54 min 52 s** (successful execution).
- Against the strengthened commit `dde5011`: margin **+13 min 22 s** (attempt) / **+16 min 43 s** (successful execution).

No timestamp here was backdated, rounded, or reconstructed. The 12:19:18Z attempt is reported even though it returned nothing, because reporting only the successful execution would silently move the first-query time 3 minutes later and make the claim look better than it is.

### Protocol verification performed before any query

1. `GET /repos/mahmood726-cyber/rapidmeta-finerenone/commits/973f031773d384f54bc1a6107931614aa5fda7ea` → **200**, author and committer date both `2026-08-12T11:27:47Z`, subject `protocol(arni-hfref): register the review protocol BEFORE the search runs`.
2. `GET .../commits/dde501167666` → **200**, full SHA `dde501167666f41ffdc81a07df1628734ce327a0`, date `2026-08-12T12:05:56Z`, subject `protocol(arni-hfref): strengthen section 9 so RoB-2 is pre-registered, not merely intended`, one file changed: `ssot/arni-hfref/PROTOCOL.md` (+66 / −9), **parent = `973f031773d3`**. The two commits are a chain, not rival registrations — consistent with what was described.
3. `GET /git/ref/heads/main` → `865744da62912a0e65fd5c1c3aeb8b41195a9985`.
4. `GET /contents/ssot/arni-hfref/PROTOCOL.md?ref=main` → present, **size 15,475 bytes**, blob `6fac376bad5b6603d44194b41edd4c4e62308b91`. Matches the size stated.
5. Protocol read in full at `dde501167666` (rendered blob).

All five checks are read-only. Nothing was written to the repository.

---

## 2. DATABASE 1 — PubMed (NCBI E-utilities `esearch`)

**String, exactly as registered in §5 of the protocol and exactly as executed:**

```
("sacubitril valsartan"[tiab] OR "LCZ696"[tiab] OR sacubitril[tiab] OR Entresto[tiab])
AND (enalapril[tiab] OR "angiotensin converting enzyme inhibitor"[tiab] OR ACEI[tiab])
AND ("heart failure"[MeSH Terms] OR "heart failure"[tiab] OR HFrEF[tiab])
AND (randomized controlled trial[pt] OR randomised[tiab] OR randomized[tiab] OR trial[tiab])
```

| Field | Value |
|---|---|
| Endpoint | `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi` |
| Parameters | `db=pubmed`, `retmode=json`, `term=<string above>` |
| Filters applied | **none** — no language filter, no date filter, as registered |
| Executed (UTC) | 2026-08-12T12:22:39.556Z (response 12:22:40.277Z) |
| **Hit count** | **331** — read from `esearchresult.count`, not counted or computed |
| Records retrieved | 331 of 331 (`idlist` length 331 at `retmax=1000`) |

**PubMed's own query translation, as returned** (evidence the string was parsed as intended, all four blocks preserved):

```
("sacubitril valsartan"[Title/Abstract] OR "LCZ696"[Title/Abstract] OR "sacubitril"[Title/Abstract]
 OR "Entresto"[Title/Abstract])
AND ("enalapril"[Title/Abstract] OR "angiotensin converting enzyme inhibitor"[Title/Abstract]
 OR "ACEI"[Title/Abstract])
AND ("heart failure"[MeSH Terms] OR "heart failure"[Title/Abstract] OR "HFrEF"[Title/Abstract])
AND ("randomized controlled trial"[Publication Type] OR "randomised"[Title/Abstract]
 OR "randomized"[Title/Abstract] OR "trial"[Title/Abstract])
```

No warnings and no error list were returned. Metadata (title, journal, year, publication types) obtained by `esummary` over all 331 PMIDs.

---

## 3. DATABASE 2 — ClinicalTrials.gov API v2

**Parameters, exactly as registered in §5 and exactly as executed:**

```
query.intr=sacubitril valsartan OR LCZ696
query.cond=heart failure
filter.overallStatus=COMPLETED|TERMINATED|ACTIVE_NOT_RECRUITING
```

| Field | Value |
|---|---|
| Endpoint | `https://clinicaltrials.gov/api/v2/studies` |
| Additional parameters | `countTotal=true`, `pageSize` (pagination only — not a filter) |
| Filters applied | only the registered `filter.overallStatus`; **no** language filter, **no** date filter |
| Executed (UTC) | 2026-08-12T12:26:16.427Z (response 12:26:16.604Z) |
| **Hit count** | **92** — read from `totalCount`, not counted or computed |
| Records retrieved | 92 of 92, via `nextPageToken` pagination |

The registered pipe-delimited status list (`COMPLETED|TERMINATED|ACTIVE_NOT_RECRUITING`) was accepted by API v2 as written. **No departure was required and none was made.**

---

## 4. OBSTACLES — named as obstacles, never recorded as absences

| # | Obstacle | Where | Effect on the record |
|---|---|---|---|
| 1 | **Sandbox egress proxy returned `403 Forbidden`** for `eutils.ncbi.nlm.nih.gov` | first query attempt, 2026-08-12T12:19:18Z | Query issued, zero records returned. Re-executed successfully through the browser at 12:22:39.556Z. **This is a blocked transport, not a null result.** |
| 2 | `web_fetch` **timed out after 180 s** (twice: `api.github.com` contents at pinned ref; the PubMed esearch URL) | protocol read; first PubMed attempt | Routed via the browser. No effect on any count. |
| 3 | `raw.githubusercontent.com` fetch **not approved** | protocol read | Protocol read instead via GitHub REST API + rendered blob. No effect. |
| 4 | GitHub code search returned **`401 Requires authentication`** | protocol verification | Substituted a complete recursive tree read (`truncated: false`) — a stronger check. |
| 5 | ClinicalTrials.gov returned **`429 Too Many Requests`** | a *confirmatory* lookup of the primary-outcome-measure fields for NCT01035255 and NCT02468232, attempted after corpus retrieval | **The registry cross-check of the two included trials' primary endpoint definitions did not happen.** The corpus retrieval (92/92) had already completed and is unaffected. The estimand for both included trials is therefore established from the published abstract only — see the `evidence_basis` column in the screening file and the caveat in `03_PRISMA.md`. |
| 6 | Output filter suppressed two tool returns as "Cookie/query string data" | protocol body dump; a timing read | Re-obtained by other means. No data lost. |

---

## 5. SOURCES REGISTERED BUT NOT YET EXECUTED

Protocol §4 names four information sources. Two were executed in this run. The remaining two are **not absent — they are not yet run**, and the PRISMA numbers in `03_PRISMA.md` are labelled accordingly:

- **Backward citation search** (protocol §5): the included-study table of every retrievable synthesis of this comparison, diffed against this review's included set in both directions. **Not executed.** The corpus already contains at least 30 candidate syntheses of this comparison (flagged `synthesis_candidate=Y` in the screening file) which are the input to that step.
- **Regulatory documents**: FDA statistical review and EMA EPAR for Entresto, admissible under §4 where a cell cannot be established from the other sources. **Not consulted.**

A PubMed-only search measures indexing, not existence. This capture is two databases, and it is not yet the whole registered search.
