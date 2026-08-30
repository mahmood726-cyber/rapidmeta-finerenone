# GIN cannot serve as the guideline-body denominator, and that corrects a ruled design

The standing orders name GIN as the way to avoid hand-listing guideline bodies:

> *"Guidelines International Network (GIN) — a membership registry OF guideline bodies.
> This is the closest thing to a denominator that exists."*

The reasoning is right and the rule it serves — **define the set by an enumerable registry,
never by our own list** — still stands. **The instrument does not.**

## What was checked, 2026-08-30

**GIN's robots.txt permits everything** (`User-agent: * / Disallow:` with an empty value)
and publishes a sitemap, so this is not a policy refusal. The site is open. The directory
is not in it.

| what | result |
|---|---|
| `g-i-n.net/robots.txt` | **allow all**, sitemap published |
| link labelled **"Members Directory"** | points at `/organisation` |
| `/organisation` page text | 48,564 characters, and **no member organisation names** — a search for NICE, SIGN, WHO, CADTH, IQWiG, AWMF, NHMRC, HAS, KCE returns nothing |
| where the directory actually lives | `connect.g-i-n.net` — **behind a member login** |
| `connect.g-i-n.net/` | 2,176 characters: a login shell |
| GIN "International Guidelines Library" | a **signpost page describing other free resources** — it recommends NICE Evidence and PubMed — not an enumerable library of guidelines |

⇒ **THE GIN MEMBER LIST IS NOT PUBLICLY ENUMERABLE.** It is a membership benefit, which is
entirely reasonable of GIN and fatal to the plan. A coverage fraction whose denominator
sits behind a login is a coverage fraction our readers cannot check — and the whole reason
for the free-source scope rule is that the reader must be able to check.

## Three alternative registries were probed, and the result is NOT a policy finding

| source | result |
|---|---|
| Epistemonikos | **HTTP 403** — even `/robots.txt` is 403 |
| WHO IRIS OAI-PMH (`verb=Identify`) | **HTTP 403** |
| ECRI Guidelines Trust | `/robots.txt` returns 200 with 125 kB of HTML — a soft 404, so no robots file was actually served |

⚠️ **A 403 TO MY CLIENT IS A FETCH STATE, NOT A REFUSAL BY THE PUBLISHER.** These look like
CDN bot-blocking on an unfamiliar user agent, and they may well answer a browser perfectly.
Recording them as "these sources refuse automated access" would be the same error as
recording a JavaScript-rendered registry page as EMPTY: **a statement about my reach,
written as a statement about the world.** They are logged as **UNRESOLVED — retry from a
browser**, and they are not counted as anything yet.

## What this means for the search-breadth axis

**The guideline-body coverage fraction cannot be reported today**, and no protocol should
claim guideline bodies were enumerated from GIN. That claim would have the same defect as
*"we searched ICTRP"* — ruled in, never run, and unsupportable if anyone checked.

**Three routes remain, none tested here:**

1. **A browser pass** at Epistemonikos, WHO IRIS and ECRI — the same *browser for
   discovery, API for the method* pattern already agreed for the six INDETERMINATE
   registries. A 403 to curl says nothing about what a browser gets.
2. **WHO IRIS via a different endpoint** — IRIS runs DSpace, which normally exposes both
   OAI-PMH and a REST API; only the OAI verb was tried and only once.
3. **Accept a NAMED, DATED hand-list and say so in terms** — *"these N bodies, chosen by us
   on this date, and here is what we did not enumerate"*. ⚠️ Worse than a registry, and the
   standing orders warn that a hand-list is a sample. But **a hand-list declared as a
   sample beats a registry claimed and not held**, and it is honest about which it is.

⭐ The number that stands today is the registry one, and it is unflattering: **of the 18
primary registries in the WHO ICTRP network, our free search returns a determinate answer
from 1.** The guideline-body figure is not "zero" — it is **not yet measurable**, which is a
different and more honest thing to print.
