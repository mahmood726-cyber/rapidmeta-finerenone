"""The registry payload, and a SHAPE GUARD that refuses the wrong one.

WHY THIS EXISTS. `topic_identity.locate()` reads the ClinicalTrials.gov v2 shape --
`protocolSection.armsInterventionsModule.armGroups`, each arm carrying a `type`
(EXPERIMENTAL / ACTIVE_COMPARATOR / ...). That is where arm ROLE lives, and role is the
whole question the arm-role cascade asks.

The MCP search tool (`mcp__plugin_bio-research_c-trials__*`) returns a FLATTENED record:

    {"nct_id": ..., "title": ..., "interventions": ["Dual Therapy", "Triple Therapy"], ...}

No `protocolSection`. No `armGroups`. **No arm types at all.** Role is not merely harder to
read in that shape -- it is absent from it.

Fed the flattened shape, `locate()` returns NOT_ASSESSABLE for every trial, with the reason
"topic drug not located in interventions, arms, or registration title". Verified on
NCT02789917, whose answer we know: raw shape -> `experimental`; MCP shape -> `not_assessable`.

**That is a cascade of silent refusals that reads as caution and is actually breakage**, and
it runs in the same withholding direction as every defect in the 2026-08-18 record: it makes
the corpus look more careful than it is, and nothing is built to notice silence.

So the fix is not a converter. There is nothing to convert FROM -- the roles were never in
the flattened payload. The fix is:

  1. FETCH THE RAW v2 RECORD for anything that needs a role, and
  2. REFUSE, LOUDLY, if a record of the wrong shape reaches a role reader.

`require_raw_v2()` is the mechanical rejection. An assessor cannot accidentally consume the
flattened shape, because the guard raises rather than returning a verdict -- same discipline
as `AssessorRejected`: an instrument that cannot read its input must not emit a number.

DIVISION OF LABOUR, and both halves are Claude-side by necessity.
  * The MCP tools run the SEARCH and produce the executed-search record (query verbatim,
    date, records returned). That is what they are good for and it is what is archived.
  * This module fetches the ROLE PAYLOAD for each surfaced registration.
Codex has no network in its sandbox, so neither half can move to that seat.
"""

import json
import os
import urllib.error
import urllib.parse
import urllib.request

from invariants import cache_is_valid, content_cache_key

API = "https://clinicaltrials.gov/api/v2/studies"
CACHE_DIR = os.environ.get("RM_CTGOV_CACHE", ".ctgov-raw-cache")

# Three states, same law as assessment.py: an instrument that could not read must not
# report a negative reading.
OK = "OK"
UNREACHABLE = "UNREACHABLE"          # transport failed -- NOT "no such trial"
MALFORMED = "MALFORMED"              # 200 but not the shape we require


class WrongPayloadShape(TypeError):
    """Raised when a role reader is handed a record that cannot carry roles.

    Deliberately an exception and not a verdict. A flattened record reaching `locate()`
    produced `not_assessable` for a trial whose answer was known -- a wrong ANSWER dressed
    as an honest refusal. The guard makes that stop the run instead.
    """


def is_raw_v2(study):
    """Does this record carry the fields role reading requires? No inference."""
    if not isinstance(study, dict):
        return False
    ps = study.get("protocolSection")
    if not isinstance(ps, dict):
        return False
    return isinstance(ps.get("armsInterventionsModule"), dict)


def require_raw_v2(study, nct_id=None):
    """Fail closed before any role is read. Returns the study when it is readable."""
    if is_raw_v2(study):
        return study
    keys = sorted(study)[:8] if isinstance(study, dict) else type(study).__name__
    raise WrongPayloadShape(
        f"{nct_id or '<unknown>'}: record carries no protocolSection.armsInterventionsModule "
        f"(top-level keys: {keys}). This is the FLATTENED MCP shape, which contains no arm "
        f"types at all. Reading roles from it returns not_assessable for every trial -- a "
        f"silent all-refusal cascade. Fetch the raw v2 record via fetch_raw() instead.")


def _cache_path(nct_id, fields):
    key = content_cache_key("ctgov-v2", nct_id, fields)
    return os.path.join(CACHE_DIR, f"{nct_id}_{key}.json")


def fetch_raw(nct_id, fields="protocolSection", timeout=45, use_cache=True):
    """Fetch ONE raw v2 record. Returns (state, study_or_None, detail).

    The cache key is derived from CONTENT (nct_id + requested fields), never from batch
    position -- `invariants.content_cache_key` exists because a position-keyed cache made
    three articles with 26/53/86 references return byte-identical results. Zero bytes is a
    MISS, not a hit, because a cached 0-byte file once turned a transport failure into a
    permanent "unparseable data" finding.
    """
    path = _cache_path(nct_id, fields)
    if use_cache and cache_is_valid(path):
        try:
            with open(path, "r", encoding="utf-8") as fh:
                study = json.load(fh)
        except (ValueError, OSError) as exc:
            return MALFORMED, None, f"cached record unreadable: {type(exc).__name__}: {exc}"
        if not is_raw_v2(study):
            return MALFORMED, None, "cached record is not the raw v2 shape"
        return OK, study, f"cache hit {path}"

    url = f"{API}/{urllib.parse.quote(nct_id)}?{urllib.parse.urlencode({'fields': fields})}"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            if resp.status != 200:
                return UNREACHABLE, None, f"HTTP {resp.status}"
            body = resp.read()
    except (urllib.error.URLError, OSError, TimeoutError) as exc:
        # A transport failure is UNREACHABLE. It is NOT "this trial does not exist" and it
        # is NOT a data defect -- conflating those is the night's whole subject.
        return UNREACHABLE, None, f"{type(exc).__name__}: {exc}"

    if not body:
        return UNREACHABLE, None, "empty body"
    try:
        study = json.loads(body.decode("utf-8"))
    except ValueError as exc:
        return MALFORMED, None, f"not JSON: {exc}"
    if not is_raw_v2(study):
        return MALFORMED, None, f"200 but wrong shape (keys: {sorted(study)[:8]})"

    if use_cache:
        os.makedirs(CACHE_DIR, exist_ok=True)
        tmp = path + ".part"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(study, fh)
        os.replace(tmp, path)          # never leave a half-written file where a hit looks valid
    return OK, study, f"fetched {len(body)} bytes"


def nct_of(study):
    """The registration id, from the raw record. Reconciliation is keyed on this, never
    on a title -- two topics seeding one trial is a real corpus pattern."""
    ps = (study or {}).get("protocolSection") or {}
    return ((ps.get("identificationModule") or {}).get("nctId")) or None
