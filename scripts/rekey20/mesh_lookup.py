# -*- coding: utf-8 -*-
"""MeSH lookup that VERIFIES WHICH RECORD IT GOT before using anything from it.

⛔⛔ THE DEFECT THIS EXISTS TO CLOSE, AND IT IS NOT THE ONE I FIRST REPORTED.
`REPORT-CONDITION-MESH.md` §3.1 blamed the UNIT -- "a condition is a phrase and I expanded
its words". That is true and it is not the root cause. Measured:

    query (free-text esearch)                  descriptor actually returned
    hypercholesterolemia                    -> Hyperlipoproteinemia Type III
    pulmonary arterial hypertension         -> Familial Primary Pulmonary Hypertension
    paroxysmal supraventricular tachycardia -> Tachycardia, Ventricular

⇒ THE PHRASE QUERIES FAIL TOO. `esearch db=mesh` with a bare term is RELEVANCE-RANKED over
every field, so it returns whatever ranks first -- routinely a narrow child or a familial
variant. Taking `idlist[0]` and reading its entry terms is asking a confident authority a
question and never checking which question it answered.

That is why `supraventricular` expanded to `ventricular tachycardia`: not because a word is
not a phrase, but because THE RECORD WAS NEVER VERIFIED. Binding the query to the descriptor
field fixes the first case outright -- `hypercholesterolemia[MeSH Terms]` returns
`Hypercholesterolemia` -- but binding alone is not enough, because a bound query can still
return a near-miss. So the record's own NAME is checked against the query, and a mismatch
REFUSES rather than expands.

⭐ THIS IS THE SAME SHAPE AS THE SEED DEFECT, THIRD OCCURRENCE. `SGLT2` -> the protein,
`Intravenous` -> the route, `supraventricular` -> a ventricular arrhythmia. Every time: a
wrong seed, confidently expanded by an authority, returning a plausible list. The fix each
time is to check the identity of what came back, not the size of it.

⚠️ E-utilities without a key allows ~3 requests/second and answers 429 when pushed. Every
call is paced and retried; a 429 that is swallowed becomes an empty expansion that looks
like "MeSH has nothing", which is a wrong belief about an authority.
"""
import io
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request

ESEARCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
EFETCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
PACE = 0.40                      # seconds between EVERY call, not between every query
_last = [0.0]

# Words that carry no concept identity, dropped before comparing a query with a descriptor.
_STOP = set("""the a an of in for with and or to disease diseases disorder disorders
syndrome syndromes type types primary secondary idiopathic familial heritable acute
chronic""".split())


def _pace():
    dt = time.time() - _last[0]
    if dt < PACE:
        time.sleep(PACE - dt)
    _last[0] = time.time()


def _get(url, tries=5):
    """-> (text, status). A 429 is RETRIED, never swallowed: an empty expansion that is
    really a rate limit reads as 'the authority holds nothing', which is a wrong belief
    about the authority rather than a fact about the term."""
    for a in range(tries):
        _pace()
        try:
            with urllib.request.urlopen(url, timeout=60) as fh:
                return fh.read().decode("utf-8", "replace"), "OK"
        except urllib.error.HTTPError as e:
            if e.code == 429 and a < tries - 1:
                time.sleep(1.5 + 2.0 * a)
                continue
            return None, "HTTP_%d" % e.code
        except Exception as e:                                    # noqa: BLE001
            if a == tries - 1:
                return None, "ERROR_%s" % type(e).__name__
            time.sleep(1.0 + 2.0 * a)
    return None, "ERROR"


def _tokens(s):
    """Content tokens, singularised.

    ⚠️ THE STEM IS NOT COSMETIC. Without it `dyslipidemia` and MeSH's `Dyslipidemias` are
    different tokens, the record verifier calls a CORRECT record a mismatch, and a working
    expansion is refused. That is over-flagging -- the failure mode that matters here --
    committed inside the check written to prevent the opposite error.
    """
    out = []
    for w in re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).split():
        if len(w) > 4 and w.endswith("s") and not w.endswith("ss"):
            w = w[:-1]
        if w and w not in _STOP:
            out.append(w)
    return out


def record_matches(query, descriptor):
    """Does the returned record answer the question asked?

    MeSH inverts phrases -- `Hypertension, Pulmonary` for `pulmonary hypertension` -- so the
    test is on the TOKEN SET, not the string. One side must contain the other: a descriptor
    may be broader-worded than the query or vice versa, but it may not be a DIFFERENT
    concept. `paroxysmal supraventricular tachycardia` vs `Tachycardia, Ventricular` shares
    only `tachycardia` and fails, which is the whole point.

    ⛔ SUBSET ALONE IS TOO WEAK FOR A ONE-TOKEN QUERY, and a clean sibling in
    `plant_mesh_lookup.py` found it before any corpus did: `stroke` is a subset of
    `{stroke, genius}`, so `Strokes of Genius Syndrome` verified as the record for `stroke`.
    A single token is a subset of almost any descriptor containing that token -- `Heat
    Stroke`, `Stroke Volume`.

    ⇒ SO CONTAINMENT COUNTS ONLY WHEN BOTH SIDES CARRY AT LEAST TWO TOKENS; otherwise the
    sets must be EQUAL. This is strictly stricter, which is the safe direction for a check
    whose job is to refuse, and it loses nothing measured: every record that verified on the
    twenty did so by set EQUALITY.

    ⚠️ This was changed after seeing a failure, and the distinction matters. The failing case
    was SYNTHETIC -- written to test discrimination, not drawn from the corpus -- so fixing
    it does not tune the gate to the data it is about to judge. The British-spelling
    over-refusal in M3 IS a corpus case and is deliberately left unpatched for that reason.
    """
    q, d = set(_tokens(query)), set(_tokens(descriptor))
    if not q or not d:
        return False
    if q == d:
        return True
    if len(q) >= 2 and len(d) >= 2:
        return q <= d or d <= q
    return False


def _parse(body):
    """MeSH full text report -> (descriptor, entry_terms, tree_numbers)."""
    lines = body.strip().splitlines()
    descriptor = lines[0].split(":", 1)[-1].strip() if lines else ""
    entries = []
    for block in re.split(r"\n\s*\n", body):
        if re.search(r"entry terms?\s*:", block, re.I):
            for line in block.splitlines()[1:]:
                v = line.strip(" \t-")
                if 2 < len(v) < 60 and not re.match(r"(?i)entry terms?\s*:", v):
                    entries.append(v)
    trees = []
    for m in re.finditer(r"Tree Number\(s\):\s*(.+)", body):
        trees.extend(t.strip() for t in m.group(1).split(",") if t.strip())
    return descriptor, sorted(set(entries)), trees


def lookup(term, cache=None, field="[MeSH Terms]"):
    """-> dict with descriptor, entry_terms, tree_numbers, verified, status.

    ⛔ `verified` is False whenever the record's name does not answer the query. A caller
    must REFUSE to expand on an unverified record; using it is how `supraventricular`
    became `ventricular tachycardia`.
    """
    # ⛔ THE CACHE HOLDS THE RAW FETCH AND `verified` IS DERIVED ON EVERY READ.
    # The first version stored the computed flag, so fixing `_tokens` to singularise did NOT
    # reach cached rows: `dyslipidemia` kept coming back RECORD_MISMATCH from a verdict
    # computed under the OLD rule, and the broken `[MeSH Tree Number]` field left cached
    # `descriptor: None` entries that made `broader()` return nothing even after the field
    # was fixed. A cache of derived values is a frozen copy of a rule's output -- the same
    # shape as an instrument certified in one configuration and run in another.
    # CACHE_VERSION is in the key so a change to the FETCH shape also invalidates.
    key = "v2||" + term.lower() + "||" + field
    if cache is not None and key in cache:
        hit = dict(cache[key])
        hit["verified"] = record_matches(term, hit.get("descriptor"))
        if hit.get("status") in ("OK", "RECORD_MISMATCH"):
            hit["status"] = "OK" if hit["verified"] else "RECORD_MISMATCH"
        return hit
    q = term + field
    body, st = _get("%s?db=mesh&retmode=json&retmax=1&term=%s"
                    % (ESEARCH, urllib.parse.quote(q)))
    out = {"query": term, "field": field, "descriptor": None, "entry_terms": [],
           "tree_numbers": [], "verified": False, "status": st}
    if body is None:
        if cache is not None:
            cache[key] = out
        return out
    try:
        ids = (json.loads(body).get("esearchresult") or {}).get("idlist") or []
    except ValueError:
        ids = []
    if not ids:
        out["status"] = "NO_RECORD"
        if cache is not None:
            cache[key] = out
        return out
    txt, st2 = _get("%s?db=mesh&rettype=full&retmode=text&id=%s" % (EFETCH, ids[0]))
    if txt is None:
        out["status"] = st2
        if cache is not None:
            cache[key] = out
        return out
    desc, entries, trees = _parse(txt)
    out.update({"descriptor": desc, "entry_terms": entries, "tree_numbers": trees,
                "verified": record_matches(term, desc), "status": "OK"})
    if not out["verified"]:
        out["status"] = "RECORD_MISMATCH"
    if cache is not None:
        cache[key] = out
    return out


def broader(tree_numbers, cache=None):
    """Parent descriptors, from the tree. -> [(parent_tree, descriptor)].

    ⭐ ENTRY TERMS ARE SYNONYMS AND CANNOT RESCUE A DEAD TERM. `Hypercholesterolemia` has 96
    entry terms and every one is a familial variant; `Hyperlipidemias` is its TREE PARENT,
    not a synonym, so no amount of synonym expansion reaches it. A dead concept needs a
    BROADER term and a promiscuous one needs a narrower: direction is chosen by the measured
    failure, not by taste.
    """
    out = []
    for tn in tree_numbers:
        if "." not in tn:
            continue
        parent = tn.rsplit(".", 1)[0]
        key = "TREEv2::" + parent
        if cache is not None and key in cache:
            rec = cache[key]
        else:
            # ⛔ THE FIELD IS `[TN]`. `[MeSH Tree Number]` -- the spelled-out name, which
            # reads as the obvious one -- returns count=0 SILENTLY for every tree number.
            # A dead branch here would have made broader() return nothing forever and read
            # as "MeSH holds no parents", a wrong belief about the authority rather than a
            # fact about the term. Found only by giving each candidate field its own count;
            # `TREE_FIELD_PROBE` below keeps it from recurring.
            body, st = _get("%s?db=mesh&retmode=json&retmax=1&term=%s"
                            % (ESEARCH, urllib.parse.quote(parent + "[TN]")))
            rec = {"descriptor": None, "status": st}
            if body is not None:
                try:
                    ids = (json.loads(body).get("esearchresult") or {}).get("idlist") or []
                except ValueError:
                    ids = []
                if ids:
                    txt, st2 = _get("%s?db=mesh&rettype=full&retmode=text&id=%s"
                                    % (EFETCH, ids[0]))
                    if txt:
                        rec = {"descriptor": _parse(txt)[0], "status": "OK"}
                    else:
                        rec["status"] = st2
                else:
                    rec["status"] = "NO_RECORD"
            if cache is not None:
                cache[key] = rec
        if rec.get("descriptor"):
            out.append((parent, rec["descriptor"]))
    seen, uniq = set(), []
    for tn, d in out:
        if d.lower() not in seen:
            seen.add(d.lower())
            uniq.append((tn, d))
    return uniq


# A tree number whose parent is known independently: C18.452.584.500.500.396 is
# Hypercholesterolemia and its parent C18.452.584.500.500 is Hyperlipidemias. If the field
# ever stops resolving, this returns None and the caller refuses instead of silently
# expanding nothing.
TREE_FIELD_PROBE = ("C18.452.584.500.500", "Hyperlipidemias")


def tree_field_works(cache=None):
    """-> (ok, descriptor). Proves the tree field can return a POSITIVE at all."""
    got = broader(["C18.452.584.500.500.396"], cache=cache)
    desc = got[0][1] if got else None
    return (desc == TREE_FIELD_PROBE[1]), desc


def load_cache(path):
    if os.path.exists(path):
        try:
            return json.load(io.open(path, encoding="utf-8"))
        except ValueError:
            return {}
    return {}


def save_cache(cache, path):
    json.dump(cache, io.open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
