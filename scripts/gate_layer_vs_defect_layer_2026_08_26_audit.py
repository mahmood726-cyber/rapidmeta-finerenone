"""WHICH LAYER DOES EACH GATE READ, AND WHICH LAYER DOES ITS DEFECT LIVE ON?

WHY THIS EXISTS. `lint_method_claim_has_a_field.py` reports "asserts 0 claim(s), 0 unbacked"
over 141 objects and prints PASS, while the claim it exists to catch is printed on the
delivered page. It reads the OBJECT. The Methods sentence is composed by the PROJECTOR at
render time and exists nowhere in the object. A gate that inspects the source cannot see a
defect created downstream of it, and its green is not evidence of anything.

THE CLASS: gate reads layer L1; the defect it names lives on layer L2; L1 != L2.
Such a gate is STRUCTURALLY VACUOUS for that class -- not weak, not flaky: incapable.

WHAT THIS DOES NOT ESTABLISH, stated before the counts.
  - NOT that an OBJECT-reading gate is wrong. Many defects genuinely live on the object.
    The finding is only a MISMATCH between what is read and what is claimed.
  - NOT that a PAGE-reading gate is safe. It can still be keyed to the wrong string.
  - The claim-layer is inferred from the module's own docstring and its exit messages,
    which is a WEAK instrument. Every mismatch it reports is a CANDIDATE for reading,
    not a verdict. The count is a floor and is labelled as one.
"""
from __future__ import annotations
import ast, io, os, re, sys, json, collections

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(REPO, "scripts")

OBJ_HINT  = re.compile(r"ssot[/\][^\"']*\.json|PAGE_MAP|\.json[\"']|canon|obj\.get|load_object")
PAGE_HINT = re.compile(r"\.html|delivered|served|pn-paper|<[a-z]+ |innerHTML|BeautifulSoup")
SRC_HINT  = re.compile(r"\.py[\"']|ast\.parse|inspect\.getsource")

def exits(tree):
    """A gate can fail iff it can leave non-zero. AST, not grep: raise SystemExit and
    sys.exit(main()) are both real and neither matches `grep sys.exit(1)`."""
    found = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) \
           and n.func.attr == "exit":
            found.append("sys.exit")
        if isinstance(n, ast.Raise) and isinstance(n.exc, ast.Call) \
           and getattr(n.exc.func, "id", "") == "SystemExit":
            found.append("raise SystemExit")
        if isinstance(n, ast.Raise) and getattr(n.exc, "id", "") == "SystemExit":
            found.append("raise SystemExit")
    return found

def layers_read(src):
    L = set()
    if OBJ_HINT.search(src):  L.add("OBJECT")
    if PAGE_HINT.search(src): L.add("PAGE")
    if SRC_HINT.search(src):  L.add("SOURCE")
    return L

# What layer does the module SAY its defect lives on? Read from its own prose.
SAYS_PAGE = re.compile(r"delivered|served bytes|on the page|a reader|rendered|reaches a reader"
                       r"|reader-facing|the page says|printed", re.I)
SAYS_OBJ  = re.compile(r"on the object|in the object|the object holds|field path|stored", re.I)

def main():
    rows = []
    for fn in sorted(os.listdir(SCRIPTS)):
        if not fn.endswith(".py"): continue
        p = os.path.join(SCRIPTS, fn)
        src = io.open(p, encoding="utf-8", errors="replace").read()
        try:
            tree = ast.parse(src)
        except SyntaxError:
            rows.append((fn, "UNPARSEABLE", set(), set(), [])); continue
        ex = exits(tree)
        # STATED AS THE POSITIVE PROPERTY: "this module CAN leave non-zero, therefore it
        # can gate". The previous form was `if not ex: continue` -- a negative guard inside
        # a loop over the whole scripts/ corpus, which is the shape that has silently
        # removed live pages from corpus-wide passes in this repository before. The
        # population is what CAN fail, not what fails to lack an exit.
        if ex:
            doc = ast.get_docstring(tree) or ""
            head = doc + "\n" + "\n".join(src.splitlines()[:60])
            claim = set()
            if SAYS_PAGE.search(head): claim.add("PAGE")
            if SAYS_OBJ.search(head):  claim.add("OBJECT")
            rows.append((fn, "gate", layers_read(src), claim, ex))

    gates = [r for r in rows if r[1] == "gate"]
    print("modules in scripts/ that can exit non-zero (i.e. can gate): %d" % len(gates))
    print()
    mism = [r for r in gates
            if "PAGE" in r[3] and "PAGE" not in r[2] and "OBJECT" in r[2]]
    only_obj = [r for r in gates if r[2] == {"OBJECT"}]
    both = [r for r in gates if {"OBJECT", "PAGE"} <= r[2]]
    print("reads OBJECT only                        : %d" % len(only_obj))
    print("reads OBJECT and PAGE                    : %d" % len(both))
    print("reads PAGE only                          : %d"
          % len([r for r in gates if r[2] == {"PAGE"}]))
    print()
    print("CANDIDATES -- claims a PAGE/reader defect but reads only the OBJECT: %d" % len(mism))
    print("(a floor, and each is a candidate for reading, not a verdict)")
    for fn, _, rd, cl, ex in sorted(mism):
        print("   %-58s reads=%s" % (fn[:58], ",".join(sorted(rd))))
    json.dump([[r[0], sorted(r[2]), sorted(r[3])] for r in gates],
              io.open(os.path.join(REPO, "outputs",
                      "gate_layer_audit_2026_08_26.json"), "w", encoding="utf-8"), indent=1)

main()
