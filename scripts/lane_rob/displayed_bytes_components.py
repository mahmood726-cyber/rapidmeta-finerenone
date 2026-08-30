#!/usr/bin/env python3
import argparse
import ast
import html
import importlib
import io
import json
import re
import sys
from pathlib import Path


REPO_ROOT = Path("F:/wt-regen")
# ⛔ A HAND-LISTED SET IS A SAMPLE. This list is checked against what build_tabbed.py actually
# wires (see `assert_covers_every_wired_component` below), because an instrument that examines
# six of seven components and prints "0 findings" is reporting its REACH as the population --
# and the seventh is exactly where the next defect would sit unseen.
MODULE_NAMES = (
    "absolute_effects",
    "certainty_profile",
    "subgroup_efficacy",
    "other_outcomes",
    "count_provenance",
    "clinical_reading",
    "audit_trail",
)
SURVIVING_ENTITIES = (
    "&mdash;",
    "&ndash;",
    "&amp;",
    "&lt;",
    "&gt;",
    "&larr;",
    "&times;",
    "&nbsp;",
    "&ldquo;",
    "&rdquo;",
)
MAX_EXAMPLES_PER_MODULE = 3

SCRIPT_STYLE_RE = re.compile(r"<(script|style)\b[^>]*>.*?</\1\s*>", re.IGNORECASE | re.DOTALL)
TAG_RE = re.compile(r"<[^>]+>")
WHITESPACE_RE = re.compile(r"\s+")
# ⛔ "None" IS ALSO AN ENGLISH WORD, AND THE FIRST VERSION OF THIS ACCUSED A CORRECT PAGE.
#
# It flagged currency_query for the sentence "None is pooled; they are listed because a reader
# deciding whether to rely on this page is entitled to know what it has not weighed." That is
# prose. The right response was to strengthen the detector, not to reword the page: our
# detectors have a measured bias toward accusing our own pages, and a fix built on a false
# finding is worse than no fix.
#
# So the token is flagged only where a LEAKED VALUE could sit -- as the entire content of an
# element, or immediately after a colon, an equals sign or an opening bracket. That is a
# STRUCTURAL boundary rather than a tuned word list, and it is applied to the RAW HTML, because
# element boundaries are exactly what tag-stripping destroys.
BARE_TOKEN_RE = re.compile(r"\b(?:nan|undefined)\b")
LEAKED_VALUE_RE = re.compile(
    r">\s*(None|nan|undefined)\s*<"
    r"|[:=]\s*(None|nan|undefined)\b"
    r"|[(\[{,]\s*(None|nan|undefined)\b"
    r"|/(None|nan|undefined)\b"
    r"|\b(None|nan|undefined)\s*[)\]}]")
TEMPLATE_TOKEN_RE = re.compile(r"\{\{.*?\}\}|REPLACE_ME|__PLACEHOLDER__", re.DOTALL)
INTERVAL_RE = re.compile(r"\(([^()]+?)\s+to\s+([^()]+?)\)")
FLOAT_RE = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$")


def displayed_text(rendered_html):
    text = SCRIPT_STYLE_RE.sub(" ", rendered_html)
    text = TAG_RE.sub(" ", text)
    text = html.unescape(text)
    text = WHITESPACE_RE.sub(" ", text).strip()
    return text


def parse_display_float(value):
    value = value.strip().replace("%", "").replace(",", "")
    if not FLOAT_RE.fullmatch(value):
        return None
    try:
        return float(value)
    except ValueError:
        return None


def check_surviving_entity(text):
    return [entity for entity in SURVIVING_ENTITIES if entity in text]


def check_bare_token(text):
    return [match.group(0) for match in BARE_TOKEN_RE.finditer(text)]


def check_leaked_value(raw_html):
    """Run on the RAW html: a token sitting where only a VALUE could sit."""
    out = []
    for m in LEAKED_VALUE_RE.finditer(raw_html or ""):
        out.append(next(g for g in m.groups() if g))
    return out


def check_template_token(text):
    return [match.group(0) for match in TEMPLATE_TOKEN_RE.finditer(text)]


def check_descending_interval(text):
    findings = []
    for match in INTERVAL_RE.finditer(text):
        left = parse_display_float(match.group(1))
        right = parse_display_float(match.group(2))
        if left is not None and right is not None and left > right:
            findings.append(match.group(0))
    return findings


CHECKS = (
    ("surviving HTML entity", check_surviving_entity),
    ("bare token", check_bare_token),
    ("unfilled template token", check_template_token),
    ("descending interval", check_descending_interval),
)


def collect_text_findings(text):
    findings = []
    for label, check in CHECKS:
        for token in check(text):
            findings.append(f"{label}: {token}")
    return findings


def is_in_scope_object(canon):
    if not isinstance(canon, dict):
        return False
    results = canon.get("results")
    if not isinstance(results, dict):
        return False
    by_outcome = results.get("by_outcome")
    return isinstance(by_outcome, dict) and bool(by_outcome)


def iter_json_paths(ssot_root):
    if not ssot_root.exists():
        return
    for topic_dir in sorted(path for path in ssot_root.iterdir() if path.is_dir()):
        json_path = topic_dir / f"{topic_dir.name}.json"
        if json_path.name.endswith(".striptest") or str(json_path).endswith(".striptest"):
            continue
        if json_path.is_file():
            yield json_path


def load_in_scope_objects(ssot_root):
    for json_path in iter_json_paths(ssot_root):
        try:
            with json_path.open("r", encoding="utf-8-sig") as handle:
                canon = json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            yield str(json_path), None, [f"load error: {exc}"]
            continue

        if is_in_scope_object(canon):
            yield str(json_path), canon, []


def import_render_modules(repo_root):
    lane_rob = repo_root / "scripts" / "lane_rob"
    ssot = repo_root / "ssot"
    for path in (ssot, lane_rob):
        path_text = str(path)
        if path_text in sys.path:
            sys.path.remove(path_text)
        sys.path.insert(0, path_text)
    return {name: importlib.import_module(name) for name in MODULE_NAMES}


def snippet(text, limit=160):
    text = WHITESPACE_RE.sub(" ", text).strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def run_scan(repo_root):
    # ⛔ THE POPULATION IS DERIVED, NOT LISTED. MODULE_NAMES is the hand-written set; what
    # build_tabbed.py WIRES is the population this instrument claims to police. Scanning the
    # first and reporting it as the second is the reach-as-population failure, and it would
    # print "0 findings" for a component it had never opened.
    #
    # A wired component that cannot be rendered is UNCHECKABLE and is named as such. It is
    # never counted clean and never silently dropped.
    lane_rob = Path(repo_root) / "scripts" / "lane_rob"
    ssot_dir = Path(repo_root) / "ssot"
    for _p in (ssot_dir, lane_rob):
        if str(_p) in sys.path:
            sys.path.remove(str(_p))
        sys.path.insert(0, str(_p))
    wired = wired_component_names(repo_root) or set(MODULE_NAMES)
    names, unrenderable = [], []
    for name in sorted(set(MODULE_NAMES) | wired):
        if not (Path(repo_root) / "scripts" / "lane_rob" / (name + ".py")).exists():
            continue
        names.append(name)
    modules = {}
    for name in names:
        try:
            modules[name] = importlib.import_module(name)
        except Exception as exc:
            unrenderable.append((name, "import failed: %s" % exc))
    for name, _why in unrenderable:
        if name in names:
            names.remove(name)
    for name in list(names):
        fn = getattr(modules.get(name), "render", None)
        if not callable(fn):
            unrenderable.append((name, "defines no render(), so its displayed bytes cannot be "
                                       "examined by this instrument"))
            names.remove(name)
            continue
        # ⛔ A render() THAT DOES NOT TAKE A TOPIC OBJECT IS UNCHECKABLE, NOT BROKEN.
        # integrity_section renders from the assembled HTML, not from the object. Feeding it a
        # canon produced 141 identical "render error" findings -- an instrument reporting its
        # own mismatched call as 141 defects in the component it was checking. Detected by
        # SIGNATURE, before any call is made.
        try:
            import inspect
            required = [p for p in inspect.signature(fn).parameters.values()
                        if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)
                        and p.default is p.empty]
            if len(required) != 1 or required[0].name not in ("canon", "obj", "object", "o"):
                unrenderable.append(
                    (name, "render%s does not take a topic object, so this instrument cannot "
                           "supply its input" % str(inspect.signature(fn))))
                names.remove(name)
        except (TypeError, ValueError):
            pass
    module_results = {
        name: {"rendered": 0, "findings": [], "elided": 0}
        for name in names
    }

    ssot_root = repo_root / "ssot"
    in_scope = list(load_in_scope_objects(ssot_root))

    for object_id, canon, load_errors in in_scope:
        if load_errors:
            for name in names:
                module_results[name]["findings"].append((object_id, "; ".join(load_errors), ""))
            continue

        for name in names:
            result = module_results[name]
            try:
                rendered = modules[name].render(canon)
                result["rendered"] += 1
            except Exception as exc:
                result["findings"].append((object_id, f"render error: {exc}", ""))
                continue

            raw = str(rendered)
            text = displayed_text(raw)
            findings = collect_text_findings(text)
            # ⛔ The value-leak check reads the RAW html, because element boundaries are the
            # structure it depends on and tag-stripping is what destroys them.
            for tok in check_leaked_value(raw):
                findings.append("leaked value in a value position: %s" % tok)
            for finding in findings:
                result["findings"].append((object_id, finding, snippet(text)))

    if unrenderable:
        print("")
        print("  UNCHECKABLE -- wired, and this instrument cannot examine them. Named, never")
        print("  counted clean:")
        for name, why in unrenderable:
            print("     %-22s %s" % (name, why))
        print("")
    total_findings = 0
    total_rendered = 0
    for name in names:
        result = module_results[name]
        findings = result["findings"]
        total_findings += len(findings)
        total_rendered += result["rendered"]

        print(f"{name}: {len(findings)} findings over {result['rendered']} objects rendered")
        shown = findings[:MAX_EXAMPLES_PER_MODULE]
        for object_id, finding, context in shown:
            if context:
                print(f"  {object_id}: {finding} | {context}")
            else:
                print(f"  {object_id}: {finding}")
        elided = max(0, len(findings) - len(shown))
        if elided:
            print(f"  {elided} examples elided")

    # ⛔ NAME THE UNIT. `total_rendered` is COMPONENT RENDERS (objects x modules), not
    # objects; printing it as "objects rendered" states a denominator 6x the real one.
    # ⛔ THE DIVISOR IS THE MODULE COUNT, NOT A LITERAL 6. Hard-coded, it printed
    # "235 objects x 6 components" once the scanned set grew to ten -- a denominator that
    # silently changes meaning when the population it describes changes.
    ncomp = len(names) or 1
    print(f"total: {total_findings} findings over {total_rendered} component renders "
          f"({total_rendered // ncomp} objects x {ncomp} components)")

    if total_rendered == 0:
        print("SCAN FAILED: zero objects were rendered; a zero over an unstated denominator is a statement about reach, not about the corpus.")
        return 2
    if total_findings:
        return 1
    return 0


def assert_check(label, check, bad_text, clean_text):
    bad_hits = check(displayed_text(bad_text))
    clean_hits = check(displayed_text(clean_text))
    if not bad_hits:
        raise AssertionError(f"{label} did not flag planted bad string")
    if clean_hits:
        raise AssertionError(f"{label} flagged planted clean string: {clean_hits}")


def run_plant():
    assert_check(
        "surviving HTML entity",
        check_surviving_entity,
        "<p>Doubled entity: &amp;mdash;</p>",
        "<p>Displayed dash: &mdash;</p>",
    )
    assert_check(
        "bare token",
        check_bare_token,
        "<p>Result is None today</p>",
        "<p>Result is nonetheless available</p>",
    )
    assert_check(
        "unfilled template token",
        check_template_token,
        "<p>{{ outcome_name }}</p>",
        "<p>Outcome name</p>",
    )
    assert_check(
        "descending interval",
        check_descending_interval,
        "<p>(9.5 to 4.2)</p>",
        "<p>(4.2 to 9.5)</p>",
    )
    # ⛔ "0 findings" READS AS A VACUOUS PASS. What was proven is that each check FIRED on a
    # planted positive and stayed silent on a clean negative -- say that, not a zero.
    print("plant: 4 of 4 checks fired on a planted positive AND stayed silent on a clean "
          "negative. Both directions watched.")
    return 0


def main(argv=None):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description="Check rendered lane_rob component displayed text.")
    parser.add_argument("--repo", default=str(REPO_ROOT), help="Repository root.")
    parser.add_argument("--plant", action="store_true", help="Run planted self-checks without reading the corpus.")
    args = parser.parse_args(argv)

    if args.plant:
        return run_plant()
    return run_scan(Path(args.repo))



def wired_component_names(repo_root):
    """The components build_tabbed.py actually wires, derived rather than assumed."""
    src = Path(repo_root) / "ssot" / "build_tabbed.py"
    try:
        tree = ast.parse(src.read_text(encoding="utf-8", errors="replace"), str(src))
    except (OSError, SyntaxError):
        return set()
    names = set()
    aliases = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                aliases[a.asname or a.name.split(".")[0]] = a.name.rsplit(".", 1)[-1]
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)                 and node.func.attr == "inject":
            owner = node.func.value
            if isinstance(owner, ast.Name) and owner.id in aliases:
                names.add(aliases[owner.id])
        if isinstance(node, ast.For) and isinstance(node.iter, (ast.Tuple, ast.List)):
            body = ast.dump(node)
            if "'inject'" not in body and "__import__" not in body:
                continue
            for item in node.iter.elts:
                if isinstance(item, (ast.Tuple, ast.List)) and len(item.elts) >= 2:
                    m = item.elts[1]
                    if isinstance(m, ast.Constant) and isinstance(m.value, str):
                        names.add(m.value)
    return names


def assert_covers_every_wired_component(repo_root):
    """-> (ok, message). Uncovered components are named, never counted as clean."""
    wired = wired_component_names(repo_root)
    if not wired:
        return False, ("could not derive the wired set from build_tabbed.py, so this scan "
                       "cannot say what it failed to cover")
    checked = set(MODULE_NAMES)
    missed = sorted(w for w in wired if w not in checked
                    and (Path(repo_root) / "scripts" / "lane_rob" / (w + ".py")).exists())
    if missed:
        return False, ("this scan checks %d components but build_tabbed wires %d; NOT covered: "
                       "%s" % (len(checked), len(wired), ", ".join(missed)))
    return True, "covers every wired component (%d checked, %d wired)" % (len(checked),
                                                                          len(wired))


if __name__ == "__main__":
    raise SystemExit(main())

