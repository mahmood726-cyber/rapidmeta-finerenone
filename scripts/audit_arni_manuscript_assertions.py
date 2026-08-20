"""What do ARNI's authored manuscript paragraphs ASSERT, and does a field back it?

BEFORE ANY TOKEN SUBSTITUTION IS BUILT. Resolving `[[k]]`, `[[pooled]]`, `[[i2]]` means
this renderer would emit SENTENCES A HUMAN WROTE WITH OUR NUMBERS DROPPED INTO THEM. That
is a template, and a template is what manufactured a Methods section in `paper-studio.js`
-- a FORMATTING control that produced an assertion no field supported.

THE DISTINCTION THAT MAKES IT SAFE IS NOT THE TEMPLATING, IT IS WHAT THE SENTENCE ASSERTS:

  "rests on [[k]] trials"                  the token IS the claim; substitute it from a
                                           named field path and the sentence asserts
                                           exactly what the object holds
  "Risk of bias was assessed using RoB 2"  a fact about how the review was conducted,
                                           NO token, NO field behind it. Inheriting this
                                           sentence means asserting a procedure nothing
                                           checks

So this counts three things per paragraph:
  * tokens, and whether each maps to a field path on THIS object
  * paragraphs with NO token at all -- candidates for un-tokened assertion
  * within those, sentences in the grammatical shape of a METHOD CLAIM

It decides nothing and adopts nothing. It is the survey that has to exist first.
"""
import io
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OBJ = os.path.join(REPO, "ssot", "arni-hfref", "arni-hfref.json")
TOKEN = re.compile(r"\[\[([a-z0-9_]+)\]\]", re.I)

# A token is SAFE only if its value comes from a named path on this object. No defaults.
# A path that does not resolve makes the whole paragraph refusable, by design.
TOKEN_PATHS = {
    "k": "results.by_outcome.cvdeath_or_hfh_first.k",
    "pooled": "results.by_outcome.cvdeath_or_hfh_first.pooled.point",
    "ci_low": "results.by_outcome.cvdeath_or_hfh_first.pooled.ci_low",
    "ci_high": "results.by_outcome.cvdeath_or_hfh_first.pooled.ci_high",
    "i2": "results.by_outcome.cvdeath_or_hfh_first.heterogeneity.i2",
    "tau2": "results.by_outcome.cvdeath_or_hfh_first.heterogeneity.tau2",
    "estimator": "results.by_outcome.cvdeath_or_hfh_first.estimator",
    "certainty": "grade.by_outcome.cvdeath_or_hfh_first.certainty",
    "n_total": "k_cascade.n_total",
    "n_records": "k_cascade.k0",
    "search_date": "search.databases[0].searched_on",
}

# Sentences that assert HOW THE REVIEW WAS CONDUCTED. These are the ones not to inherit
# without a field, because nothing in the object checks them.
METHOD_CLAIM = re.compile(
    r"\b(was|were)\s+(assessed|extracted|screened|rated|graded|appraised|performed|"
    r"conducted|registered|prespecified|pre-specified|double[- ]extracted|checked|"
    r"searched|applied|followed)\b|\b(we|two reviewers|both reviewers|independently)\b",
    re.I)


def get(obj, path):
    cur = obj
    for part in path.replace("[", ".[").split("."):
        if not part:
            continue
        if part.startswith("["):
            i = int(part[1:-1])
            if not isinstance(cur, list) or i >= len(cur):
                return None
            cur = cur[i]
        else:
            if not isinstance(cur, dict) or part not in cur:
                return None
            cur = cur[part]
    return cur


def paragraphs(m):
    for key, v in m.items():
        if key.startswith("_"):
            continue
        if isinstance(v, str):
            yield key, v
        elif isinstance(v, list):
            for x in v:
                if isinstance(x, str):
                    yield key, x
                elif isinstance(x, dict) and isinstance(x.get("text"), str):
                    yield key, x["text"]
        elif isinstance(v, dict):
            for k2, v2 in v.items():
                if isinstance(v2, str) and not k2.startswith("_"):
                    yield "%s.%s" % (key, k2), v2


def main():
    obj = json.load(io.open(OBJ, encoding="utf-8"))
    m = obj.get("manuscript")
    if not isinstance(m, dict):
        sys.exit("REFUSED: arni-hfref holds no manuscript block.")

    paras = list(paragraphs(m))
    if not paras:
        sys.exit("REFUSED: zero paragraphs read from the manuscript block.")

    tokened, untokened = [], []
    unresolvable = {}
    for key, text in paras:
        toks = TOKEN.findall(text)
        if toks:
            tokened.append((key, text, toks))
            for t in toks:
                path = TOKEN_PATHS.get(t.lower())
                if path is None or get(obj, path) is None:
                    unresolvable.setdefault(t.lower(), []).append(key)
        else:
            untokened.append((key, text))

    method_claims = [(k, t) for k, t in untokened if METHOD_CLAIM.search(t)]

    print("ARNI manuscript paragraphs read       %d" % len(paras))
    print("  carrying at least one token         %d" % len(tokened))
    print("  carrying NO token                   %d" % len(untokened))
    print("    ...of which assert a METHOD       %d   <- DO NOT INHERIT WITHOUT A FIELD"
          % len(method_claims))
    print()

    alltok = sorted({t.lower() for _, _, ts in tokened for t in ts})
    print("distinct tokens: %d" % len(alltok))
    print("%-16s %-56s %s" % ("token", "field path", "resolves on this object?"))
    print("-" * 110)
    for t in alltok:
        path = TOKEN_PATHS.get(t)
        val = get(obj, path) if path else None
        print("%-16s %-56s %s" % (t, path or "<<NO PATH DECLARED>>",
                                  ("yes -> %r" % (val,))[:44] if val is not None else "NO"))
    print()
    if unresolvable:
        print("TOKENS THAT CANNOT BE RESOLVED FROM A NAMED PATH -- every paragraph using one")
        print("must REFUSE, by name. Never a default:")
        for t, keys in sorted(unresolvable.items()):
            print("    %-16s used in: %s" % (t, ", ".join(sorted(set(keys)))))
        print()

    print("UN-TOKENED PARAGRAPHS ASSERTING A METHOD -- these are the sentences a human")
    print("wrote that state a fact about the review with no token and no field behind it.")
    print("Adopting one means asserting a procedure nothing checks:")
    print()
    for k, t in method_claims:
        s = re.sub(r"\s+", " ", t).strip()
        print("  [%s] %s" % (k, s[:220]))
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
