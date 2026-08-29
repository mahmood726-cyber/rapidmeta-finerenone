# Guideline layer: worked the 131, and the fraction moved from 1 to 16

**All figures against the GIN denominator of 136, which travels with every claim below.**

## Registry version, because a claim about a registry is a claim about a version

```
Guidelines International Network (GIN)
endpoint    https://g-i-n.net/wp-json/wp/v2/organisation
X-WP-Total  136
re-verified 2026-08-29
```

⚠️ **The endpoint returned HTTP 403 to the default python-requests user-agent and 200 to a
browser one.** The denominator is unchanged, but the incident matters more than the number:
**a 403 is a fact about a request until it has been retried properly.** Every "blocked"
recorded without a considered user-agent had to be re-tested, and some of them moved.

## The headline fraction

| | of 136 |
|---|---|
| **queryable** — a machine-readable search surface responded | **15** |
| reached — responds, but nothing machine-readable | 13 |
| blocked — a named obstacle | 4 |
| **unresolved — no address could be established at all** | **104** |

Plus **openFDA**, already in the harness and not a GIN member ⇒ **16 queryable guideline
sources, up from 1.**

⚠️ **"All guideline bodies" is still not a claim any search here supports.** 104 of 136
bodies have no address at all. The fraction improved; it did not close.

## GIN is a denominator, not an address book — established twice

1. Not one of the 136 API records carries an external URL (`acf` is empty; `content` holds
   only a PDF on GIN's own domain).
2. The rendered member profile pages carry no link to the member's own site either — only
   GIN's fonts, GIN's charity registration and GIN's social account.

**An index is not a source.** Addresses had to come from elsewhere.

## How addresses were obtained, and its measured error rate

**Wikidata P856 "official website"**, queried per member name. A derivation from a public
knowledge base, not a hand-written list — 136 names in, whatever Wikidata holds out.

**⚠️ The first two runs of this returned 0 and then 6, and both were artefacts of my own
requests, not facts about Wikidata:**

- **0** — Wikimedia refuses a generic browser user-agent; every call was 403. **There is no
  universal user-agent.** The browser string that fixed GIN is precisely what breaks
  Wikidata.
- **6** — 113 of 136 came back **HTTP 429**. Reporting "6 of 136 are resolvable" would have
  been a claim about the world assembled from my own rate limiting.

Only after polite pacing and retries does the number settle. **A zero from an invalid
comparison is not a clean result**, and this one produced two different wrong answers before
the right one.

### Measured precision — a count without one is not a finding

All 35 initially-resolved sites were read by hand. **Three were the wrong organisation** and
were removed rather than kept:

| body | resolved to | why it is wrong |
|---|---|---|
| ECRI | `coe.int` | the Council of Europe. "ECRI" is also the European Commission against Racism and Intolerance, and Wikidata matched that. |
| Covidence | `who.int` | Covidence is a Cochrane screening tool; the matched entity is not it. |
| Alzheimer's Association | `fightdementia.org.au` | Dementia Australia, not the US Alzheimer's Association. |

```
resolved and hand-checked   35
wrong entity, removed        3
correct                     32     precision 91%
```

⚠️ **The labeller was the author of the resolver.** That is a real weakness and is recorded
rather than dropped. It also failed once already in the automated form: my first precision
checker flagged `who.int` for the World Health Organisation and `apa.org` for the American
Psychological Association as suspicious, because it stripped stop-words before computing
initials. **The heuristic was worse than reading 35 rows.**

## Why the 104 are unresolved, by named reason

```
no Wikidata entity at all                       80
Wikidata hits, none describing an organisation  10
entity exists but carries no P856 website       10
wrong entity, rejected by hand                   3
still rate-limited at stop time                  1
```

**The dominant reason is a genuine limit of the route, not of the bodies.** Wikidata covers
international societies well and small national agencies, ministries and hospitals poorly —
*State Expert Center of the Ministry of Health of Ukraine*, *Children's Hospital of Nanjing
Medical University*, *Heart Foundation Australia*. Resolving those needs a different route,
and that is the next lever.

## The four named obstacles, re-tested with a considered user-agent

| body | recorded before | re-tested |
|---|---|---|
| **WHO IRIS** | HTTP 403, unreachable | ⭐ **QUERYABLE.** Its DSpace-7 API answers: `iris.who.int/server/api/discover/search/objects` returned JSON with `totalElements=50` for *empagliflozin*. OAI-PMH also responds. **This was never unreachable; it was asked wrongly.** |
| NICE | HTTP 401, syndication needs a key | site returns 200 and 141 KB of server-rendered HTML. Reachable, not machine-queryable without a key. |
| TRIP | "Cloudflare challenge behind a 200" | **my characterisation was wrong** — it is a React single-page app returning a 4 KB shell. Still not server-queryable, but the obstacle is a JS shell, not a challenge page. **A 200 is not a document**, for a different reason than I gave. |
| Epistemonikos | HTTP 405 on the documented API | site search returns 200 and 219 KB of HTML. Reachable, HTML only. |

⭐ **WHO IRIS is the single most valuable recovery here** — the body whose guidance matters
most across this corpus, wrongly recorded as blocked because of how it was asked.

## The 15 with a machine-readable surface

`who.int` · `jbi.global` · `g-i-n.net` · `cap.org` · `entnet.org` · `aasmnet.org` ·
`esaic.org` · `eaaci.org` · `sirweb.org` · `aslms.org` · `erwcpt.eu` ·
`lungfoundation.com.au` · `aerztekammer.at` · `mcmaster.ca` · `unesp.br`

Surfaces are WordPress REST or an HTML search form, detected from the page rather than
guessed. **A surface is not a search**: none of these has been queried for any topic yet,
and until they are, this is a map of what *can* be asked, not a claim about what was.

## What is deliberately not claimed

- Not that guideline evidence is covered. **16 of 136 is a fraction, and it is the headline.**
- Not that the 15 were searched. They were **resolved and probed**, which is a different act.
- Not that the 104 lack websites. They lack websites *reachable by this route*.
- Not that the 4 blocked bodies are unreachable — **WHO IRIS was in that list yesterday.**
