# -*- coding: utf-8 -*-
"""Field ORIGIN and field CLAIM KIND, enforced rather than documented.

⭐ THE ONE-LINE JUSTIFICATION. Three lanes hit the same defect today in three different
fields, and one rule catches all three:

    A CLAIM WHOSE REQUIRED SHAPE IS ABSENT IS A DEFECT, NOT A CLAIM.

The three:
  1. `question` and `manuscript.introduction` agreed on 59 objects and looked like two
     witnesses. One transform wrote both. ⇒ DERIVED AGREEMENT IS NOT WEAK EVIDENCE, IT IS
     PERFECT AGREEMENT -- cleaner than two independent sources would ever produce, and the
     cleanest agreement is the most suspicious.
  2. "122 of 152 objects mention Cochrane" read as counterpart availability. Testing for the
     STRUCTURAL signature -- a CD###### with a pubN -- returned 2. The 122 were the Cochrane
     HANDBOOK cited as method authority. ⇒ STRING PRESENCE IS NOT STRUCTURAL PRESENCE.
  3. A paper matched for `IPM 036` is the report of `MTN-036`. ⇒ DIGIT EQUALITY IS NOT
     IDENTIFIER EQUALITY; the letter prefix is load-bearing.

`__derived_from` answers WHERE A VALUE CAME FROM. `__claim` answers WHAT IT IS ASSERTING.
Neither substitutes for the other: (2) and (3) are shape failures that provenance alone
would not have caught.

⚠️ UNKNOWN ORIGIN IS ITS OWN STATE. A field with no `__derived_from` is UNKNOWN, never
AUTHORED. Defaulting unknown to authored reopens the hole for every legacy field; defaulting
it to refused blacks out the corpus on day one. `validate_object` reports unknowns and does
not fail on them.

⛔ AND NOTHING HERE SYNTHESISES PROVENANCE. For most existing fields the origin is
unrecoverable -- the transforms ran and left no trace -- and reconstructing it from git
history would be a guess dressed as a record. A FABRICATED ORIGIN IS WORSE THAN AN ABSENT
ONE: absent is honest, fabricated is a false witness, which is the failure this module
exists to prevent.
"""
from __future__ import annotations

import datetime

SUFFIX_FROM = "__derived_from"
SUFFIX_CLAIM = "__claim"
SUFFIX_EVIDENCE = "__evidence"

# claim kind -> fields its evidence block MUST carry. Enforced by validate_claim; a claim
# whose shape is absent is rejected rather than believed.
CLAIM_SHAPES = {
    "method_citation": ("section",),
    "counterpart_review": ("pubN", "checked_utc"),
    "evidence_source": ("read_utc",),
    "derived_value": (),
    "authored_judgement": (),
    "trial_identifier": ("token_as_matched", "prefix_confirmed_in_fetched_record"),
    "unverifiable_claim": ("asserted_by", "citation_as_given", "indexes_searched",
                           "searched_utc", "located"),
}

# counterpart_review needs ONE OF these as well -- a review with neither is unidentified.
ANY_OF = {"counterpart_review": ("cd", "doi")}


class ClaimError(ValueError):
    pass


def set_derived(obj, field, value, inputs, by, authored=False,
                run_utc=None, reconstructed=False):
    """Write a field AND its origin together, so the two cannot drift apart.

    A separate 'remember to record provenance' step is a convention, and conventions fail
    silently. This is the only supported way to write a derived field.

    ⚠️ `run_utc` AND `reconstructed` EXIST FOR BACKFILL, AND THEY ARE NOT COSMETIC. Stamping
    a backfilled record with `now` would assert that a transform ran tonight when it ran on
    2026-08-24 -- a false origin, which is the exact failure this module prevents. Pass the
    real run date, and set `reconstructed=True` so the record says it was reassembled after
    the fact rather than written by the transform itself. A reconstructed origin is weaker
    evidence than a contemporaneous one and must never be indistinguishable from it.
    """
    if authored and inputs:
        raise ClaimError(
            "authored=True with inputs=%r: a value computed from another field is not "
            "authored. This pairing is exactly how a transform is laundered into a witness."
            % (inputs,))
    if reconstructed and not run_utc:
        raise ClaimError(
            "reconstructed=True without run_utc: a reconstruction that cannot name WHEN the "
            "transform ran is a guess, and a fabricated origin is worse than an absent one.")
    obj[field] = value
    rec = {
        "inputs": list(inputs),
        "by": by,
        "run_utc": run_utc or datetime.datetime.now(datetime.timezone.utc)
                              .isoformat(timespec="seconds"),
        "authored": bool(authored),
    }
    if reconstructed:
        rec["reconstructed"] = True
        rec["reconstructed_utc"] = (datetime.datetime.now(datetime.timezone.utc)
                                    .isoformat(timespec="seconds"))
        rec["reconstruction_basis"] = None      # caller must state it; validated below
    obj[field + SUFFIX_FROM] = rec
    return obj


def resolve(root, path):
    """(container_dict, leaf_key) for a DOTTED path, or (None, leaf) if it does not resolve.

    ⛔ DOTTED PATHS RESOLVE FROM THE ROOT, AND `origins` MUST USE THIS. An earlier version
    looked `path + "__derived_from"` up as a FLAT KEY, so `manuscript.introduction` found
    nothing, was treated as its own origin, and `corroborate("question",
    "manuscript.introduction")` returned TRUE -- a FALSE CORROBORATION on the single case
    this module was built to catch. The provenance was recorded correctly; the reader of it
    could not follow a path across containers. A resolver that silently fails to resolve
    reports independence, which is the flattering direction.
    """
    parts = path.split(".")
    cur = root
    for p in parts[:-1]:
        p = p.replace("[]", "")
        if isinstance(cur, dict) and p in cur:
            cur = cur[p]
        elif isinstance(cur, list) and cur and isinstance(cur[0], dict):
            cur = cur[0]
        else:
            return None, parts[-1]
    return (cur if isinstance(cur, dict) else None), parts[-1].replace("[]", "")


def origins(root, path, _seen=None):
    """Transitive ORIGIN fields behind a value, following dotted paths from `root`.

    A field with no record returns itself -- UNKNOWN origin is its own state and must not be
    silently promoted to authored.
    """
    _seen = _seen or set()
    if path in _seen:                       # a cycle is a defect, not an origin
        return []
    _seen = _seen | {path}
    container, leaf = resolve(root, path)
    meta = container.get(leaf + SUFFIX_FROM) if isinstance(container, dict) else None
    if not isinstance(meta, dict) or meta.get("authored") or not meta.get("inputs"):
        return [path]
    out = []
    for src in meta["inputs"]:
        out.extend(origins(root, src, _seen))
    return out


def corroborate(obj, a, b):
    """Do two fields INDEPENDENTLY support each other?

    False when they share any origin -- which is the 59-introduction case: `question` and
    `manuscript.introduction` both trace to `title`, so their agreement is one fact counted
    twice.
    """
    oa, ob = set(origins(obj, a)), set(origins(obj, b))
    return bool(oa) and bool(ob) and oa.isdisjoint(ob)


def validate_claim(obj, field):
    """Errors for one field's claim. Empty list means the claim carries its required shape."""
    kind = obj.get(field + SUFFIX_CLAIM)
    if kind is None:
        return []
    errs = []
    if kind not in CLAIM_SHAPES:
        return ["%s: unknown claim kind %r (known: %s)"
                % (field, kind, ", ".join(sorted(CLAIM_SHAPES)))]
    ev = obj.get(field + SUFFIX_EVIDENCE)
    if not isinstance(ev, dict):
        ev = obj.get(field) if isinstance(obj.get(field), dict) else {}
    for req in CLAIM_SHAPES[kind]:
        if ev.get(req) in (None, "", []):
            errs.append("%s claims %s but carries no %r -- a claim whose required shape is "
                        "absent is a defect, not a claim" % (field, kind, req))
    anyof = ANY_OF.get(kind)
    if anyof and not any(ev.get(k) for k in anyof):
        errs.append("%s claims %s but carries none of %s -- unidentified"
                    % (field, kind, "/".join(anyof)))
    if kind == "trial_identifier" and ev.get("prefix_confirmed_in_fetched_record") is not True:
        errs.append("%s: identifier prefix was NOT confirmed in the fetched record. A match "
                    "confirmed only from the QUERY is not confirmed -- the query is what you "
                    "believed, the record is what arrived (IPM 036 / MTN-036)." % field)
    if kind == "derived_value":
        meta = obj.get(field + SUFFIX_FROM)
        if not isinstance(meta, dict) or meta.get("authored"):
            errs.append("%s claims derived_value but has no %s with authored=false"
                        % (field, SUFFIX_FROM))
    if kind == "authored_judgement":
        meta = obj.get(field + SUFFIX_FROM)
        if isinstance(meta, dict) and meta.get("inputs"):
            errs.append("%s claims authored_judgement but records inputs %r"
                        % (field, meta["inputs"]))
    return errs


def walk_fields(node, path="", _depth=0):
    """Every field at EVERY depth, as (dotted_path, container). Suffix keys excluded.

    ⚠️ THE SHALLOW COUNT WAS FLATTERING US BY 27.8x. Counting only top-level keys gave
    "4,188 fields, 100% unknown origin". The recursive count is 116,617, of which 11,833 sit
    under `results.by_outcome.*` -- which is where the estimates, the counts and the
    certainty ratings live. ⇒ A COUNT OF THE SHALLOW LAYER IS NOT A COUNT OF THE PROBLEM,
    and the direction of the error was the comfortable one.

    Lists contribute their dict/list members under a `[]` path segment; list POSITION is not
    an identity and must never be treated as one.
    """
    if isinstance(node, dict):
        for k, v in node.items():
            if k.endswith((SUFFIX_FROM, SUFFIX_CLAIM, SUFFIX_EVIDENCE)):
                continue
            p = "%s.%s" % (path, k) if path else k
            yield p, node
            for item in walk_fields(v, p, _depth + 1):
                yield item
    elif isinstance(node, list):
        for v in node:
            if isinstance(v, (dict, list)):
                for item in walk_fields(v, path + "[]", _depth):
                    yield item


def validate_object(canon, recursive=True):
    """(errors, unknown_origin_fields) for a whole object.

    Unknowns are REPORTED, never failed: a field with no provenance record is of unknown
    origin, which is a different state from authored and from derived.
    """
    errs, unknown = [], []
    if not recursive:
        for k in list(canon):
            if k.endswith((SUFFIX_FROM, SUFFIX_CLAIM, SUFFIX_EVIDENCE)):
                continue
            errs.extend(validate_claim(canon, k))
            if (k + SUFFIX_FROM) not in canon:
                unknown.append(k)
        return errs, unknown
    for path, container in walk_fields(canon):
        leaf = path.rsplit(".", 1)[-1].replace("[]", "")
        if isinstance(container, dict) and (leaf + SUFFIX_CLAIM) in container:
            errs.extend("%s: %s" % (path, e) for e in validate_claim(container, leaf))
        if not (isinstance(container, dict) and (leaf + SUFFIX_FROM) in container):
            unknown.append(path)
    return errs, unknown
