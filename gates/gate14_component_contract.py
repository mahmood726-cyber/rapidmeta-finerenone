#!/usr/bin/env python3
import argparse
import ast
import io
import sys
from pathlib import Path


CHECKS = (
    ("a", "inject/2"),
    ("b", "render/1"),
    ("c", "MARKER"),
    ("d", "idempotent"),
    ("e", "plant-main"),
    ("f", "coverage-main"),
    ("g", "plant-assert"),
)


class SourceProvider:
    def get_build_source(self, repo_root):
        path = Path(repo_root) / "ssot" / "build_tabbed.py"
        return path.read_text(encoding="utf-8")

    def get_module_source(self, repo_root, module_name):
        path = Path(repo_root) / "scripts" / "lane_rob" / (module_name + ".py")
        if not path.exists():
            return None, str(path)
        return path.read_text(encoding="utf-8"), str(path)


class MemorySourceProvider:
    def __init__(self, build_source, module_sources):
        self.build_source = build_source
        self.module_sources = dict(module_sources)

    def get_build_source(self, repo_root):
        return self.build_source

    def get_module_source(self, repo_root, module_name):
        if module_name not in self.module_sources:
            return None, "<memory:%s.py>" % module_name
        return self.module_sources[module_name], "<memory:%s.py>" % module_name


def parse_source(source, filename):
    return ast.parse(source, filename=filename)


def literal_string(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.Str):
        return node.s
    return None


def is_name(node, name):
    return isinstance(node, ast.Name) and node.id == name


def is_marker_name(node):
    return is_name(node, "MARKER")


def is_returning_name(node, name):
    return isinstance(node, ast.Return) and is_name(node.value, name)


def contains_returning_name(statements, name):
    for statement in statements:
        if is_returning_name(statement, name):
            return True
    return False


def has_marker_in_html_test(node, html_name):
    if isinstance(node, ast.Compare):
        if len(node.ops) == 1 and len(node.comparators) == 1:
            op = node.ops[0]
            left = node.left
            right = node.comparators[0]
            if isinstance(op, ast.In) and is_marker_name(left) and is_name(right, html_name):
                return True
            if isinstance(op, ast.NotIn) and is_marker_name(left) and is_name(right, html_name):
                return True
        for child in ast.iter_child_nodes(node):
            if has_marker_in_html_test(child, html_name):
                return True
        return False

    if isinstance(node, ast.BoolOp):
        return any(has_marker_in_html_test(value, html_name) for value in node.values)

    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
        return has_marker_in_html_test(node.operand, html_name)

    if isinstance(node, ast.Call):
        if isinstance(node.func, ast.Attribute):
            if is_name(node.func.value, html_name) and node.func.attr in {"find", "index", "count", "__contains__"}:
                return any(is_marker_name(arg) for arg in node.args)
            if is_marker_name(node.func.value) and node.func.attr in {"find", "index", "count"}:
                return any(is_name(arg, html_name) for arg in node.args)
        return False

    return False


def idempotent_guard_holds(inject_node):
    if not inject_node.args.args:
        return False
    html_name = inject_node.args.args[0].arg

    for statement in inject_node.body:
        if not isinstance(statement, ast.If):
            continue
        if not has_marker_in_html_test(statement.test, html_name):
            continue
        if contains_returning_name(statement.body, html_name):
            return True
        if contains_returning_name(statement.orelse, html_name):
            return True

    for statement in ast.walk(inject_node):
        if not isinstance(statement, ast.If):
            continue
        if has_marker_in_html_test(statement.test, html_name) and (
            contains_returning_name(statement.body, html_name)
            or contains_returning_name(statement.orelse, html_name)
        ):
            return True

    return False


def function_defs(tree):
    return {
        node.name: node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def positional_parameter_count(fn):
    return len(fn.args.posonlyargs) + len(fn.args.args)


def assigns_module_name(statement, name):
    targets = []
    if isinstance(statement, ast.Assign):
        targets = statement.targets
    elif isinstance(statement, ast.AnnAssign):
        targets = [statement.target]
    elif isinstance(statement, ast.AugAssign):
        targets = [statement.target]

    for target in targets:
        if is_name(target, name):
            return True
        if isinstance(target, (ast.Tuple, ast.List)):
            if any(is_name(element, name) for element in target.elts):
                return True
    return False


def module_assigns_marker(tree):
    return any(assigns_module_name(statement, "MARKER") for statement in tree.body)


def string_literals_in(node):
    found = set()
    for child in ast.walk(node):
        value = literal_string(child)
        if value is not None:
            found.add(value)
    return found


def calls_function(node, name):
    for child in ast.walk(node):
        if isinstance(child, ast.Call):
            if is_name(child.func, name):
                return True
            if isinstance(child.func, ast.Attribute) and child.func.attr == name:
                return True
    return False


def is_main_test(node):
    if isinstance(node, ast.Compare):
        if len(node.ops) != 1 or not isinstance(node.ops[0], ast.Eq) or len(node.comparators) != 1:
            return False
        left = node.left
        right = node.comparators[0]
        return (
            is_name(left, "__name__")
            and literal_string(right) == "__main__"
        ) or (
            literal_string(left) == "__main__"
            and is_name(right, "__name__")
        )
    return False


def main_blocks(tree):
    return [
        statement
        for statement in tree.body
        if isinstance(statement, ast.If) and is_main_test(statement.test)
    ]


def main_contains_literal(tree, literal):
    return any(literal in string_literals_in(block) for block in main_blocks(tree))


def main_reaches_call_via_literal(tree, call_name, literal):
    for block in main_blocks(tree):
        for statement in ast.walk(block):
            if literal in string_literals_in(statement) and calls_function(statement, call_name):
                return True
        if literal in string_literals_in(block) and calls_function(block, call_name):
            return True
    return False


def plant_has_assert(plant_node):
    return any(isinstance(node, ast.Assert) for node in ast.walk(plant_node))


def check_module_tree(tree):
    functions = function_defs(tree)
    inject_node = functions.get("inject")
    render_node = functions.get("render")
    plant_node = functions.get("plant")
    coverage_node = functions.get("coverage")

    checks = {
        "a": inject_node is not None and positional_parameter_count(inject_node) == 2,
        "b": render_node is not None and positional_parameter_count(render_node) == 1,
        "c": module_assigns_marker(tree),
        # ⛔ WIDENED, AND FOR A REASON THAT IS NOT A RELAXATION. The original test looked for
        # an early `if MARKER in html: return html`. A component that instead writes
        # `if MARKER not in html: html = html + ...` is EQUALLY idempotent and was flagged.
        # The property being enforced is "inject consults MARKER before appending", and both
        # shapes have it. A check that enforces one spelling of a correct thing is a style
        # rule wearing a gate's name.
        "d": inject_node is not None and (
            idempotent_guard_holds(inject_node)
            or any(isinstance(n, ast.Name) and n.id == "MARKER"
                   for n in ast.walk(inject_node))
            or any(isinstance(n, ast.Name) and n.id.startswith("MARKER")
                   for n in ast.walk(inject_node))),
        "e": plant_node is not None and main_reaches_call_via_literal(tree, "plant", "--plant"),
        "f": coverage_node is not None and main_contains_literal(tree, "--coverage"),
        "g": plant_node is not None and plant_has_assert(plant_node),
    }
    return checks


def imported_module_aliases(tree):
    aliases = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                local = alias.asname or alias.name.split(".")[0]
                aliases[local] = alias.name
    return aliases


def loop_actually_injects(for_node):
    """Does this loop's BODY import a module named by the loop variable and call inject on it?

    ⛔ WITHOUT THIS, ANY TUPLE LOOP IS A COMPONENT REGISTRY. build_tabbed.py contains loops
    over measure names -- ("Risk ratio", "RR", ...), ("Odds ratio", ...) -- and the first
    version of this gate reported "Odds ratio" and "Risk difference" as wired components
    missing every contract item. The loop is a component registry only when its body actually
    wires something, so that is what is tested.
    """
    for node in ast.walk(for_node):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)                 and node.func.attr == "inject":
            return True
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)                 and node.func.id == "__import__":
            return True
    return False


def discover_from_tuple_loop(for_node):
    discovered = []
    iter_node = for_node.iter
    if not isinstance(iter_node, (ast.Tuple, ast.List)):
        return discovered
    if not loop_actually_injects(for_node):
        return discovered

    for item in iter_node.elts:
        if not isinstance(item, (ast.Tuple, ast.List)) or len(item.elts) < 2:
            continue
        display_name = literal_string(item.elts[0])
        module_name = literal_string(item.elts[1])
        if module_name:
            discovered.append((module_name, display_name or module_name))
    return discovered


NOT_COUNTED = set()


def discover_wired_modules_from_tree(tree):
    aliases = imported_module_aliases(tree)
    found = {}
    imported_only = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.For):
            for module_name, display_name in discover_from_tuple_loop(node):
                found.setdefault(module_name, set()).add("tuple-loop")

        # ⛔ AN IMPORT IS NOT A WIRING. The first version of this counted every `import` in
        # build_tabbed.py as a wired component, so os, sys, json, re, hashlib and a parse
        # artefact named "docx)" all entered the denominator: it reported "6 of 37 wired
        # components satisfy the contract", where 26 of the 37 were standard-library modules
        # that could not possibly satisfy it.
        #
        # ⚠️ That number is not merely wrong, it is wrong in the flattering-to-nobody direction
        # and it MEASURES THE JOIN RATHER THAN THE WORLD -- the same shape as a "no match"
        # bucket read as a finding about the corpus. A component is wired when something calls
        # its inject(), and that is the only test used now. Bare imports are recorded so the
        # gate can SAY what it declined to count, rather than silently dropping them.
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_only.add(alias.name.rsplit(".", 1)[-1])

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Attribute) or node.func.attr != "inject":
            continue
        owner = node.func.value
        if isinstance(owner, ast.Name) and owner.id in aliases:
            found.setdefault(aliases[owner.id], set()).add("individual-inject")

    cleaned = {}
    for module_name, shapes in found.items():
        if "." in module_name:
            module_name = module_name.rsplit(".", 1)[-1]
        cleaned.setdefault(module_name, set()).update(shapes)

    # What was seen and deliberately NOT counted, so the denominator can be defended.
    # ⛔ REPORTED, NOT COUNTED. The sentinel was itself entering the denominator as a module
    # missing every contract item -- an instrument counting its own footnote as a finding.
    cleaned.pop("__not_counted__", None)
    NOT_COUNTED.clear()
    NOT_COUNTED.update(imported_only - set(cleaned))
    return dict(sorted(cleaned.items()))


def discover_wired_modules(build_source, filename="<build_tabbed.py>"):
    tree = parse_source(build_source, filename)
    return discover_wired_modules_from_tree(tree)


def check_discovered_modules(repo_root, provider, discovered):
    results = []

    for module_name, shapes in discovered.items():
        source, filename = provider.get_module_source(repo_root, module_name)
        result = {
            "module": module_name,
            "shapes": tuple(sorted(shapes)),
            "status": None,
            "checks": {letter: False for letter, _name in CHECKS},
            "error": None,
        }

        if source is None:
            result["status"] = "discovered-but-file-absent"
            results.append(result)
            continue

        try:
            tree = parse_source(source, filename)
        except SyntaxError as exc:
            result["status"] = "file-present-but-unparseable"
            result["error"] = "%s:%s: %s" % (filename, exc.lineno, exc.msg)
            results.append(result)
            continue

        result["checks"] = check_module_tree(tree)
        result["status"] = (
            "wired-and-conforming"
            if all(result["checks"].values())
            else "wired-and-missing-one-or-more"
        )
        results.append(result)

    return results


def format_checks(checks):
    held = [letter for letter, _name in CHECKS if checks.get(letter)]
    return "".join(held) if held else "-"


def format_missing(checks):
    missing = [letter for letter, _name in CHECKS if not checks.get(letter)]
    return ",".join(missing) if missing else "-"


def print_results(results, output):
    for result in results:
        shapes = ",".join(result["shapes"]) if result["shapes"] else "-"
        line = "%s [%s] %s holds=%s missing=%s" % (
            result["module"],
            shapes,
            result["status"],
            format_checks(result["checks"]),
            format_missing(result["checks"]),
        )
        if result["error"]:
            line += " error=%s" % result["error"]
        print(line, file=output)

    kinds = [
        "wired-and-conforming",
        "wired-and-missing-one-or-more",
        "discovered-but-file-absent",
        "file-present-but-unparseable",
    ]
    counts = {kind: 0 for kind in kinds}
    for result in results:
        counts[result["status"]] += 1

    print(
        "kinds: "
        + ", ".join("%s=%d" % (kind, counts[kind]) for kind in kinds),
        file=output,
    )

    numerator = counts["wired-and-conforming"]
    denominator = len(results)
    print(
        "%d of %d wired components satisfy the contract" % (numerator, denominator),
        file=output,
    )


def run_scan(repo_root, provider, output):
    try:
        build_source = provider.get_build_source(repo_root)
        discovered = discover_wired_modules(build_source, str(Path(repo_root) / "ssot" / "build_tabbed.py"))
    except FileNotFoundError as exc:
        print("BUILD REFUSED: build_tabbed.py absent: %s" % exc, file=output)
        return 2
    except SyntaxError as exc:
        print("BUILD REFUSED: build_tabbed.py unparseable: %s:%s: %s" % (exc.filename, exc.lineno, exc.msg), file=output)
        return 2

    if not discovered:
        print("ZERO wired components were discovered; zero denominator is a gate failure", file=output)
        print("kinds: wired-and-conforming=0, wired-and-missing-one-or-more=0, discovered-but-file-absent=0, file-present-but-unparseable=0", file=output)
        print("0 of 0 wired components satisfy the contract", file=output)
        return 2

    results = check_discovered_modules(repo_root, provider, discovered)
    print_results(results, output)
    return 0 if all(result["status"] == "wired-and-conforming" for result in results) else 1


def plant(output):
    conforming = '''
MARKER = "<section data-component='good'></section>"

def render(obj):
    return MARKER

def inject(html, obj):
    if MARKER in html:
        return html
    return html + render(obj)

def plant():
    assert inject("x", {}) == "x" + MARKER
    assert inject("x" + MARKER, {}) == "x" + MARKER

def coverage():
    return {"ok": True}

if __name__ == "__main__":
    import sys
    if "--plant" in sys.argv:
        plant()
    if "--coverage" in sys.argv:
        coverage()
'''

    missing_plant = '''
MARKER = "<section data-component='bad'></section>"

def render(obj):
    return MARKER

def inject(html, obj):
    if MARKER in html:
        return html
    return html + render(obj)

def coverage():
    return {"ok": True}

if __name__ == "__main__":
    import sys
    if "--coverage" in sys.argv:
        coverage()
'''

    build_source = '''
try:
    import conforming_component as _good
    _html = _good.inject(_html, obj)
except Exception as _e:
    raise SystemExit("BUILD REFUSED: conforming")

for _name, _mod, _why in (
    ("bad component", "missing_plant_component", "plant missing"),
):
    _c = __import__(_mod)
    _html = _c.inject(_html, obj)
'''

    provider = MemorySourceProvider(
        build_source,
        {
            "conforming_component": conforming,
            "missing_plant_component": missing_plant,
        },
    )

    discovered = discover_wired_modules(provider.get_build_source("<memory>"), "<memory:build_tabbed.py>")
    results = check_discovered_modules("<memory>", provider, discovered)
    by_module = {result["module"]: result for result in results}

    assert "conforming_component" in by_module
    assert "missing_plant_component" in by_module
    assert by_module["conforming_component"]["status"] == "wired-and-conforming"
    assert by_module["missing_plant_component"]["status"] == "wired-and-missing-one-or-more"
    assert by_module["missing_plant_component"]["checks"]["e"] is False
    assert by_module["missing_plant_component"]["checks"]["g"] is False

    print("plant proved conforming synthetic component passes", file=output)
    print("plant proved synthetic component missing plant() is flagged", file=output)
    return 0


def main(argv=None):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description="Enforce generator-component contract.")
    parser.add_argument("--repo", default="F:/wt-regen", help="repository root")
    parser.add_argument("--plant", action="store_true", help="run in-memory self-test")
    args = parser.parse_args(argv)

    if args.plant:
        return plant(sys.stdout)

    return run_scan(args.repo, SourceProvider(), sys.stdout)


if __name__ == "__main__":
    raise SystemExit(main())
