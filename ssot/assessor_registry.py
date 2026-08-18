"""Four mechanical detectors, because writing the rule down failed five times in one night.

WHY THIS EXISTS, and it is not the same reason as assessment.py's.

`assessment.py` put the three-state rule in one function so it could not be re-derived
incorrectly. It was imported, it was used -- and the SAME author then reproduced the same
defect class FOUR MORE TIMES in a single script within hours of committing it:

  1. `subject_role` was written as `assess(o, "screening.eligibility")` -- byte-identical
     to `inclusion_criteria_auditable`. One check, two names, producing a fake independent
     signal. This was committed hours after a commit whose entire subject was one NAME
     carrying two CHECKS.
  2. `estimand` compared free-text outcome definitions with string equality.
  3. `comparator` compared control-arm LABELS with string equality, so `Placebo Q2W` and
     `Placebo` read as different comparators.
  4. `contract` asserted `isinstance(schema_version, int)` when the field is int on four
     objects and str ("2-authored-from-source") on six. A schema FACT judged as a failure.

The conclusion is not "try harder". Documentation has now failed as a control in the most
favourable conditions it will ever get: freshly written, one page long, by the person who
wrote it, minutes earlier. THESE ARE THE SAME FOUR MISTAKES AS DETECTORS. An assessor that
commits one does not register, so it cannot run, so it cannot produce a number.
"""

import ast
import collections
import inspect
import re

from assessment import PASS, FAIL, NOT_ASSESSABLE, read, judge


# ---------------------------------------------------------------------------
# DETECTOR 2's dependency: one text comparison, with cases that pin both directions.
# ---------------------------------------------------------------------------

# Suffixes that qualify HOW a thing was given, not WHAT it is. `Placebo Q2W` and `Placebo`
# are the same comparator; the schedule is not part of the comparator's identity.
_DOSE_SUFFIX = re.compile(
    r"\b(q\.?\s?\d*\s?[dwmh]|q\.?[dwmh]|bid|tid|qid|od|sc|iv|po|"
    r"once daily|twice daily|every \d+ weeks?|weekly|monthly|matching)\b", re.I)
_PAREN = re.compile(r"\([^)]*\)")
_PUNCT = re.compile(r"[^\w\s]")
_WS = re.compile(r"\s+")


def normalise_text(s):
    s = str(s or "").lower()
    s = _PAREN.sub(" ", s)
    s = _DOSE_SUFFIX.sub(" ", s)
    s = _PUNCT.sub(" ", s)
    return _WS.sub(" ", s).strip()


def text_match(a, b):
    """The ONLY sanctioned text comparison. Exact after normalisation -- never fuzzy.

    Fuzziness is what would let `risk ratio` and `rate ratio` collapse, and those must
    stay different. Normalisation removes only schedule/format noise.
    """
    return normalise_text(a) == normalise_text(b)


# Both directions are pinned. A change that makes a MUST_MATCH pass by making a
# MUST_DIFFER also pass is not an improvement, and this is what catches that.
MUST_MATCH = [
    ("Placebo Q2W", "Placebo"),                       # the comparator artifact, live case
    ("Placebo Q2W", "placebo  q2w"),
    ("Warfarin (adjusted dose)", "warfarin"),
    ("Acetylsalicylic acid", "acetylsalicylic acid"),
    ("Bempedoic Acid + Ezetimibe", "bempedoic acid + ezetimibe"),
]
MUST_DIFFER = [
    ("risk ratio", "rate ratio"),                     # one character, different quantity
    ("hazard ratio", "odds ratio"),
    ("stroke or systemic embolism", "ISTH major bleeding"),   # apixaban-af, real finding
    ("percent change in LDL-C at week 12", "percent change in LDL-C at week 52"),
    ("warfarin", "aspirin"),
    ("placebo", "warfarin"),
]


def _selftest():
    for a, b in MUST_MATCH:
        if not text_match(a, b):
            raise AssertionError(f"text_match MUST_MATCH failed: {a!r} vs {b!r}")
    for a, b in MUST_DIFFER:
        if text_match(a, b):
            raise AssertionError(f"text_match MUST_STAY_DIFFERENT collapsed: {a!r} vs {b!r}")


_selftest()          # import-time. A broken text_match must not be importable.


# ---------------------------------------------------------------------------
# DETECTOR 2: raw text equality does not register.
# ---------------------------------------------------------------------------

class AssessorRejected(Exception):
    """Raised at REGISTRATION. A rejected assessor cannot run, so it cannot emit a number."""


_TEXT_SIGNATURES = (".lower()", ".strip()", ".casefold()")


def _uses_raw_text_equality(fn):
    """AST-scan for string equality that did not go through text_match."""
    try:
        src = inspect.getsource(fn)
    except (OSError, TypeError):
        return None                               # cannot read source -> not a clean pass
    if "text_match" in src:
        return False
    tree = ast.parse(_dedent(src))

    # SCOPE MATTERS, AND THE FIRST VERSION OF THIS GOT IT WRONG. It tested each AST node's
    # own segment, so `[str(x).lower() for x in ...]` (which normalises) and
    # `len(set(labs)) == 1` (which compares) never appeared in the SAME node, and the
    # detector passed the exact `comparator` defect it was written to catch. Looking in
    # too narrow a scope is the same error as checking a grand total instead of a per-tab
    # count -- the failure is real, and it sits between the units you inspected.
    #
    # So: normalisation ANYWHERE in the function plus comparison ANYWHERE in the function,
    # without text_match, is a rejection. Fail closed; the author routes through
    # text_match() or restructures.
    normalises = any(sig in src for sig in _TEXT_SIGNATURES) or "str(" in src
    if not normalises:
        return False

    for node in ast.walk(tree):
        if isinstance(node, ast.Compare) and any(
                isinstance(o, (ast.Eq, ast.NotEq)) for o in node.ops):
            return f"normalises text and compares with {ast.unparse(node)!r}"
        if isinstance(node, ast.Call) and getattr(node.func, "id", "") == "set":
            return f"normalises text and de-duplicates with {ast.unparse(node)!r}"
    return False


def _dedent(src):
    lines = src.splitlines()
    pad = min((len(l) - len(l.lstrip()) for l in lines if l.strip()), default=0)
    return "\n".join(l[pad:] for l in lines)


# ---------------------------------------------------------------------------
# DETECTORS 1, 3, 4 live in the registry itself.
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# DETECTOR 5: the unit of analysis. The one that is not about absence at all.
# ---------------------------------------------------------------------------
#
# Detector 2 failed its own test in the exact shape of the bug it targets: it inspected
# each AST NODE's local segment while claiming to check the FUNCTION, so normalisation in
# one node and comparison in another never met. That is the same error as certifying a
# per-tab migration with a grand-total check, and as a per-topic sweep that sums across
# topics.
#
# None of these is an absence problem. THE CHECK RAN CORRECTLY ON THE WRONG UNIT. That is
# a distinct failure class and it is mechanically detectable: make every assessor DECLARE
# the unit it analyses, then verify the declared unit is the unit it actually iterates.

class UnitMismatch(AssessorRejected):
    pass


def _iterated_expressions(fn):
    """Every expression this function iterates over, as source text."""
    try:
        tree = ast.parse(_dedent(inspect.getsource(fn)))
    except (OSError, TypeError, SyntaxError):
        return None
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.For):
            out.append(ast.unparse(node.iter))
        elif isinstance(node, (ast.ListComp, ast.SetComp, ast.GeneratorExp, ast.DictComp)):
            out.extend(ast.unparse(g.iter) for g in node.generators)
    return out


def check_unit(name, fn, unit, unit_source):
    """`unit_source` is a token that MUST appear in what the function iterates.

    unit="object" means the assessor judges the object as a whole and iterates no
    sub-collection to reach its verdict.
    """
    iterated = _iterated_expressions(fn)
    if iterated is None:
        raise UnitMismatch(f"{name}: source unreadable, cannot verify unit of analysis.")
    if unit == "object":
        return
    if not any(unit_source in expr for expr in iterated):
        raise UnitMismatch(
            f"{name}: declares unit={unit!r} but iterates {iterated or 'nothing'} -- none "
            f"mentions {unit_source!r}. A check that runs on a unit other than the one it "
            f"declares is the grand-total-versus-per-tab error, and it produces a correct "
            f"answer to the wrong question.")


class Registry:
    def __init__(self):
        self._by_name = {}
        self._paths = {}

    def register(self, name, fn, reads, accepts=None, unit="object", unit_source=""):
        """DETECTOR 1 (duplicate path) + DETECTOR 2 (text equality) + DETECTOR 3 (types).

        `reads`   - every dotted path this assessor reads. Required, non-empty.
        `accepts` - {path: tuple_of_types}. A value of another type is NOT_ASSESSABLE,
                    never FAIL: a field that is int on some objects and str on others is a
                    SCHEMA FACT, and a predicate that assumed one type must refuse, not judge.
        """
        if not reads:
            raise AssessorRejected(f"{name}: declares no paths. An assessor names what it reads.")

        key = frozenset(reads)
        if key in self._paths:
            raise AssessorRejected(
                f"{name}: reads exactly the same path set as {self._paths[key]!r} "
                f"({sorted(reads)}). Two assessors over one path is one check with two "
                f"names, which is how `subject_role` produced a fake independent signal.")

        seg = _uses_raw_text_equality(fn)
        if seg:
            raise AssessorRejected(
                f"{name}: compares display text directly ({seg!r}). Route through "
                f"text_match(), which keeps 'Placebo Q2W'=='Placebo' while keeping "
                f"'risk ratio'!='rate ratio'.")
        if seg is None:
            raise AssessorRejected(f"{name}: source unreadable, cannot verify text handling.")

        check_unit(name, fn, unit, unit_source)          # DETECTOR 5

        self._paths[key] = name
        self._by_name[name] = (fn, tuple(reads), dict(accepts or {}), unit)
        return fn

    def assessor(self, name, reads, accepts=None, unit="object", unit_source=""):
        def deco(fn):
            self.register(name, fn, reads, accepts, unit, unit_source)
            return fn
        return deco

    def type_guard(self, name, obj):
        """DETECTOR 3, applied before the assessor runs."""
        _fn, _reads, accepts, _unit = self._by_name[name]
        for path, types in accepts.items():
            r = read(obj, path)
            if r.state in ("absent", "empty", "unreadable"):
                continue                                     # judge() handles these
            if not isinstance(r.value, tuple(types)):
                return (NOT_ASSESSABLE,
                        f"cannot assess: {path} is {type(r.value).__name__}, and this "
                        f"assessor declares {[t.__name__ for t in types]}. A polymorphic "
                        f"field is a schema fact, not a failure.")
        return None

    def run(self, objects):
        """Run every assessor over every object, then DETECTOR 4."""
        results = collections.defaultdict(dict)
        for key, obj in objects.items():
            for name, (fn, _reads, _acc, _u) in self._by_name.items():
                guarded = self.type_guard(name, obj)
                results[name][key] = guarded if guarded else fn(obj)
        return dict(results), self.identical_tally_alarm(results)

    @staticmethod
    def identical_tally_alarm(results):
        """DETECTOR 4: two assessors byte-identical across every object.

        Cheap, always on. This is what gave `subject_role` away, after inspection rather
        than before -- so it runs by default now.
        """
        alarms = []
        names = sorted(results)
        for i, a in enumerate(names):
            for b in names[i + 1:]:
                if results[a] == results[b]:
                    alarms.append(
                        f"{a} and {b} returned byte-identical results across all "
                        f"{len(results[a])} objects -- duplicate check, or a coincidence "
                        f"worth one look.")
        return alarms
