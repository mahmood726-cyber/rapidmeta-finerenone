# -*- coding: utf-8 -*-
"""Drug lexicon AND class authority, from ONE external source: ChEMBL.

The lexicon is not a list I wrote. A token is a DRUG iff ChEMBL resolves it to a
molecule with max_phase >= 1. The CLASS is that molecule's `usan_stem_definition`
-- the WHO/USAN nomenclature stem, which is the published drug-class vocabulary
that review titles are written in ("-entan" -> "endothelin receptor antagonists").

Using one authority for both jobs means the rule has no place for my judgement to
enter. Where the authority gives a class that is a MODALITY rather than a
therapeutic class (an antibody stem, "-mab" -> "monoclonal antibodies: fully
human"), that is recorded as a FAILURE STATE of the rule, not repaired by hand.

Cached to chembl_cache.json so the run is repeatable and the API is hit once.
"""
import io, json, os, sys, time, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "chembl_cache.json")
API = "https://www.ebi.ac.uk/chembl/api/data/molecule/search"
UA = {"User-Agent": "research/1.0"}

# A USAN stem that names a MOLECULAR MODALITY rather than a therapeutic class.
# Declared here, before the scan, from the stem vocabulary -- not from the twenty.
MODALITY_STEMS = ("monoclonal antibod", "antibod", "fusion protein", "receptor molecules",
                  "peptide", "oligonucleotide", "antisense", "small interfering",
                  "recombinant")
# "enzyme" was here and was REMOVED -- see RULE-AMENDMENT.md. An enzyme inhibitor is a
# mechanism class (statins are "HMG-CoA inhibitors"); an antibody is a modality.


def _cache():
    if os.path.exists(CACHE):
        return json.load(io.open(CACHE, encoding="utf-8"))
    return {}


def _save(c):
    json.dump(c, io.open(CACHE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def resolve(token, cache=None, save=True):
    """token -> dict or None. None means ChEMBL holds no clinical molecule of that name."""
    key = token.lower().strip()
    c = cache if cache is not None else _cache()
    if key in c:
        return c[key]
    url = API + "?" + urllib.parse.urlencode({"q": key, "format": "json", "limit": 20})
    out = None
    for attempt in range(4):
        try:
            raw = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=90).read()
            data = json.loads(raw.decode("utf-8"))
            break
        except Exception:
            if attempt == 3:
                c[key] = {"error": "unreachable"}
                if save:
                    _save(c)
                return c[key]
            time.sleep(2 * (attempt + 1))
    best = None
    for m in data.get("molecules", []):
        pref = (m.get("pref_name") or "").lower()
        syn = [s.get("molecule_synonym", "").lower() for s in (m.get("molecule_synonyms") or [])]
        if pref != key and key not in syn:
            continue                        # exact name/synonym only -- no partial matches
        mp = m.get("max_phase")
        try:
            mp = float(mp) if mp is not None else -9
        except (TypeError, ValueError):
            mp = -9
        if mp < 1:
            continue                        # clinical molecules only
        if best is None or mp > best[0]:
            best = (mp, m)
    if best:
        m = best[1]
        stem_def = m.get("usan_stem_definition")
        out = {
            "chembl_id": m.get("molecule_chembl_id"),
            "pref_name": m.get("pref_name"),
            "max_phase": best[0],
            "usan_stem": m.get("usan_stem"),
            "usan_stem_definition": stem_def,
            # NOTE: the REST API returns atc_classifications as a list of CODE STRINGS;
            # the MCP wrapper returns a list of dicts. Same field, two shapes,
            # two access paths. Handle both rather than assume one.
            "atc": [a if isinstance(a, str) else a.get("level5")
                    for a in (m.get("atc_classifications") or [])],
        }
        out["class_is_modality"] = bool(stem_def) and any(
            s in stem_def.lower() for s in MODALITY_STEMS)
    c[key] = out
    if save:
        _save(c)
    return out


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                                  line_buffering=True)
    for t in sys.argv[1:]:
        print(t, "->", json.dumps(resolve(t), ensure_ascii=False))
