"""UNIT 2 -- a field whose NAME declares a full digest must hold a full digest.

THE REAL DEFECT THIS CAME FROM. Plant AS5 in `regression_plants.fx_fake_full_hash`, measured
2026-08-28 and recorded verbatim in the registry:

    "AS5: eight hex characters calling itself a full sha256, above a bare judgement.
     Measured 2026-08-28: adding this ONE key promoted 76 judgements from 'believed' to
     'exactly re-checkable' and the gate passed."

and the registry's own note on the class:

    "WORSE THAN A MISS. An 8-character fake sha256 promotes the judgements beneath it to
     VERSIONED and RAISES the corpus integrity metric."

That is why this class outranks its size. Every other undetected class leaves the integrity
number where it was. This one MOVES IT UP: the corpus scores better for holding a value that
cannot do the job its field name promises.

WHY THE BOUNDARY IS STRUCTURAL AND NOT NUMERIC. There is no threshold here and nothing to
tune. THE FIELD NAME IS A TYPE DECLARATION: a key called `source_sha256_full` states that its
value is a complete SHA-256, and a complete SHA-256 is exactly 64 hexadecimal characters. The
check is type conformance against a declaration the corpus made about itself. A shorter value
does not score lower -- it fails to be the thing it is named as.

THREE STATES, NEVER TWO (standing orders 9d). A two-state answer would convert honest absence
into a defect:

    ABSENT       no declaring field on the object            -> NOT ASSESSABLE, its own kind
    CONFORMING   declared full, and full                     -> clean
    TRUNCATED    declared full, and short / not hex / absent -> the finding

NOT ASSESSABLE is never folded into clean. `assessable()` returns the denominator so a caller
cannot quote a violation count without the population it came out of -- the standing rule that
a query on a typed field measures FIELD ADOPTION, not the condition it names.

THE MODEL ANSWER, asserted to pass. The behaviour this class enforces is *name the field for
what you actually hold*. A key named `source_sha256_prefix`, `..._short` or `sha256_first8`
holding eight hex characters is the EXEMPLARY CORRECT FORM and must not fire. If this detector
accused it, the only ways to satisfy the detector would be to stop recording short digests, or
to rename them into the full form -- and the second is the defect itself.

REACH, STATED. This reads a store object, not a page. A digest rendered only into HTML and
never held in a field is not examined, and is not counted as clean.
"""
from __future__ import annotations

import re

_FULL_LEN = {"sha1": 40, "sha224": 56, "sha256": 64, "sha384": 96, "sha512": 128, "md5": 32}

# A key DECLARES a full digest when it names an algorithm and does not qualify it as partial.
_ALGO = re.compile(r"(?:^|_)(sha1|sha224|sha256|sha384|sha512|md5)(?:_|$)")

# Qualifiers that WITHDRAW the "full" claim. A key carrying one is stating that it holds part
# of a digest, which is a different and entirely legitimate thing to hold.
_PARTIAL = re.compile(r"(?:^|_)(prefix|short|abbrev|abbreviated|trunc|truncated|head|"
                      r"first\d*|\d+)(?:_|$)")

_HEX = re.compile(r"\A[0-9a-f]+\Z")


def _norm(key):
    """camelCase and kebab-case collapse onto snake_case so one key is one key."""
    k = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", str(key))
    return re.sub(r"[^a-z0-9]+", "_", k.lower()).strip("_")


def declares_full_digest(key):
    """(algorithm, required_length) if this key NAMES a complete digest, else None.

    The qualifier check keeps the exemplary correct form -- a field honestly named as a
    prefix -- OUTSIDE the population entirely, rather than inside it and excused.
    """
    k = _norm(key)
    m = _ALGO.search("_" + k + "_")
    if not m:
        return None
    algo = m.group(1)
    padded = "_" + k + "_"
    rest = padded[:m.start(1)] + padded[m.end(1):]
    if _PARTIAL.search(rest):
        return None
    return algo, _FULL_LEN[algo]


def _walk(obj, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from _walk(v, "%s.%s" % (path, k) if path else str(k))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from _walk(v, "%s[%d]" % (path, i))
    else:
        yield path, obj


def _leaf_key(path):
    return path.rsplit(".", 1)[-1].split("[")[0]


def _conforms(value, need):
    if not isinstance(value, str):
        return False
    v = value.strip().lower()
    return len(v) == need and bool(_HEX.match(v))


def assessable(obj):
    """(n_declaring_fields, n_conforming, n_truncated) -- the denominator, always."""
    n = ok = bad = 0
    for path, value in _walk(obj):
        d = declares_full_digest(_leaf_key(path))
        if not d:
            continue
        n += 1
        if _conforms(value, d[1]):
            ok += 1
        else:
            bad += 1
    return n, ok, bad


def findings(obj, source="?"):
    """Every field that NAMES a complete digest and does not hold one."""
    out = []
    for path, value in _walk(obj):
        d = declares_full_digest(_leaf_key(path))
        if not d:
            continue
        algo, need = d
        if _conforms(value, need):
            continue
        if not isinstance(value, str):
            why = "not a string (%s)" % type(value).__name__
        elif not _HEX.match(value.strip().lower()):
            why = "not hexadecimal"
        else:
            why = "%d hex characters where %s declares %d" % (
                len(value.strip()), algo, need)
        out.append({
            "source": source, "field": path, "algorithm": algo,
            "declared_length": need, "reason": why,
            "quote": "%s = %r" % (path, value),
        })
    return out


# ---------------------------------------------------------------------------
# CONTROLS. Anchored to fixtures, never to the corpus's current belief: a control keyed to
# live content retires itself the moment the content changes, then passes for the wrong reason.
# ---------------------------------------------------------------------------
KNOWN_NEGATIVES = [
    # THE MODEL ANSWER: a real digest under a name that declares a real digest.
    {"source_sha256_full": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"},
    # THE MODEL ANSWER FOR THE SHORT CASE, and the reason this detector is safe to ship:
    # eight hex characters under a name that says eight hex characters is CORRECT BEHAVIOUR.
    {"source_sha256_prefix": "9c1b8e07"},
    {"source_sha256_short": "9c1b8e07"},
    {"sha256_first8": "9c1b8e07"},
    {"blob_sha1_full": "da39a3ee5e6b4b0d3255bfef95601890afd80709"},
    {"md5_full": "d41d8cd98f00b204e9800998ecf8427e"},
    # uppercase is the same digest; normalisation must not manufacture a finding
    {"source_sha256_full": "E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855"},
    # camelCase and kebab-case spellings of a conforming field
    {"sourceSha256Full": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"},
    {"source-sha256-full": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"},
    # a field naming no algorithm is not in this population at all
    {"revision": "9c1b8e07"},
    {"short_id": "abc123"},
    # nested, conforming
    {"trials": [{"review": {"source_sha256_full":
                            "5891b5b522d5df086d0ff0b110fbd9d21bb4fc7163af34d08286a2e846f6be03"}}]},
    # prose ABOUT sha256 holds no declaring field, so nothing is examined
    {"note": "each record carries a sha256 of its source document"},
]

KNOWN_POSITIVES = [
    # the motivating case, verbatim from regression_plants.fx_fake_full_hash
    {"source_sha256_full": "9c1b8e07", "review": {"verdict": "low risk of bias"}},
    # the same lie with the algorithm spelled differently
    {"sha256": "9c1b8e07"},
    # right length, not hexadecimal -- a placeholder a length-only check would pass
    {"source_sha256_full": "x" * 64},
    # a full sha1 in a field that declares sha256: 40 where 64 is promised
    {"source_sha256_full": "da39a3ee5e6b4b0d3255bfef95601890afd80709"},
    # not a string at all
    {"source_sha256_full": None},
    # nested where the corpus actually puts it
    {"trials": [{"review": {"source_sha256_full": "9c1b8e07"}}]},
]


def control():
    """(n_negatives, n_false_positives, examples), (n_positives, n_missed, examples)."""
    fp = [o for o in KNOWN_NEGATIVES if findings(o, "control")]
    missed = [o for o in KNOWN_POSITIVES if not findings(o, "control")]
    return (len(KNOWN_NEGATIVES), len(fp), fp), (len(KNOWN_POSITIVES), len(missed), missed)
