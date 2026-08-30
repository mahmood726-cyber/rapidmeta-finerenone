
# -*- coding: utf-8 -*-
"""TRIAGE, NOT A GATE: which component controls would notice if the thing they guard broke?

⛔ IT IS NAMED TRIAGE ON PURPOSE. This repository has already renamed four files that were
called `*_gate.py` and were in fact correctly-built triage tools; the name is a promise that a
non-zero exit means a DEFECT. Here it does not. A surviving mutant is a CANDIDATE finding that
has to be adjudicated one at a time, and the three adjudicated so far were all correct
behaviour.

WHAT IT DOES. For each component it runs `--plant`, then re-runs it against mutated copies:

  M1  invert the first assert in plant()                 -- killed 7 of 7
  M2  delete the first assert line in plant()            -- survived 5 of 7
  M3  replace the first string literal in a control dict -- survived 6 of 7
  M4  perturb the first NUMBER inside MODEL_ANSWER       -- survived 5 of 7

⚠️ AND THE HEADLINE NUMBER IS A STATEMENT ABOUT THE OPERATORS, NOT ABOUT THE CONTROLS.
11 of 28 mutants killed reads like half the controls are dead. Adjudicating three survivors:

  * `absolute_effects` M3 replaces the first string literal inside MODEL_ANSWER, which is the
    KEY "app_id". Nothing reads it. The mutant SHOULD survive.
  * `absolute_effects` M2 deletes `assert got, why` -- a guard against a case the model answer
    does not exercise, so removing it changes nothing for a valid fixture. Correct.
  * `absolute_effects` M4 perturbs the TREATMENT arm's event count. The component derives the
    absolute effect from the CONTROL arm and the pooled ratio and never reads the treatment
    arm, so the fixture field is decorative and the mutant survives correctly.

⇒ At this granularity mutation testing largely measures WHICH FIXTURE FIELDS A COMPONENT READS.
To test a control it must perturb a value the assertions actually depend on, and knowing which
that is per component is a judgement. Use this to FIND candidates; do not quote its ratio as a
quality figure, and never let a survivor drive a change until it has been adjudicated -- a fix
built on a false finding is worse than no fix.
"""
import argparse
import io
import os
import re
import shutil
import subprocess
import sys
import tempfile

MODULES = [
    "absolute_effects",
    "subgroup_efficacy",
    "other_outcomes",
    "count_provenance",
    "clinical_reading",
    "audit_trail",
    "certainty_profile",
]

# ⛔ M3 IS RETAINED BUT ITS SURVIVORS ARE NOT FINDINGS -- see mutate_m4. M4 is the
# operator that can actually reach an expectation.
MUTATIONS = ["M1", "M2", "M3", "M4"]
TIMEOUT_SECONDS = 180


def normalize_repo(path):
    return os.path.abspath(os.path.expanduser(path))


def module_source_path(repo, module):
    return os.path.join(repo, "scripts", "lane_rob", module + ".py")


def subprocess_env(repo, temp_dir=None):
    lane_rob = os.path.join(repo, "scripts", "lane_rob")
    ssot = os.path.join(repo, "ssot")
    existing = os.environ.get("PYTHONPATH", "")
    parts = []
    if temp_dir:
        parts.append(temp_dir)
    parts.extend([lane_rob, ssot])
    if existing:
        parts.append(existing)

    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(parts)
    return env


def run_plant(path, cwd, repo, temp_dir=None):
    try:
        result = subprocess.run(
            [sys.executable, path, "--plant"],
            cwd=cwd,
            env=subprocess_env(repo, temp_dir=temp_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding="utf-8",
            errors="replace",
            timeout=TIMEOUT_SECONDS,
        )
        return {
            "kind": "exit",
            "code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "kind": "timeout",
            "code": None,
            "stdout": exc.stdout or "",
            "stderr": exc.stderr or "",
        }


def read_text(path):
    with open(path, "r", encoding="utf-8", errors="replace") as handle:
        return handle.read()


def write_text(path, text):
    with open(path, "w", encoding="utf-8", errors="replace", newline="") as handle:
        handle.write(text)


def line_start_offsets(text):
    starts = [0]
    for match in re.finditer(r"\n", text):
        starts.append(match.end())
    return starts


def offset_to_line_index(starts, offset):
    index = 0
    for i, start in enumerate(starts):
        if start > offset:
            break
        index = i
    return index


def leading_indent(line):
    match = re.match(r"[ \t]*", line)
    return match.group(0) if match else ""


def indentation_width(indent):
    width = 0
    for char in indent:
        if char == "\t":
            width += 4
        else:
            width += 1
    return width


def find_plant_body_lines(text):
    starts = line_start_offsets(text)
    match = re.search(r"(?m)^([ \t]*)def[ \t]+plant[ \t]*\([^)]*\)[ \t]*:", text)
    if not match:
        return None

    lines = text.splitlines(True)
    def_line = offset_to_line_index(starts, match.start())
    def_indent_width = indentation_width(match.group(1))

    body_start = None
    body_end = len(lines)

    for i in range(def_line + 1, len(lines)):
        stripped = lines[i].strip()
        if not stripped:
            continue
        current_width = indentation_width(leading_indent(lines[i]))
        if current_width <= def_indent_width:
            return None
        body_start = i
        break

    if body_start is None:
        return None

    for i in range(body_start + 1, len(lines)):
        stripped = lines[i].strip()
        if not stripped:
            continue
        current_width = indentation_width(leading_indent(lines[i]))
        if current_width <= def_indent_width:
            body_end = i
            break

    return lines, body_start, body_end


def split_assert_expression(line):
    newline = ""
    body = line
    if body.endswith("\r\n"):
        newline = "\r\n"
        body = body[:-2]
    elif body.endswith("\n"):
        newline = "\n"
        body = body[:-1]

    match = re.match(r"^([ \t]*)assert[ \t]+(.+)$", body)
    if not match:
        return None

    indent = match.group(1)
    rest = match.group(2)
    in_string = None
    escaped = False
    paren_depth = 0
    bracket_depth = 0
    brace_depth = 0

    for i, char in enumerate(rest):
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == in_string:
                in_string = None
            continue

        if char in ("'", '"'):
            in_string = char
        elif char == "(":
            paren_depth += 1
        elif char == ")":
            paren_depth = max(0, paren_depth - 1)
        elif char == "[":
            bracket_depth += 1
        elif char == "]":
            bracket_depth = max(0, bracket_depth - 1)
        elif char == "{":
            brace_depth += 1
        elif char == "}":
            brace_depth = max(0, brace_depth - 1)
        elif (
            char == ","
            and paren_depth == 0
            and bracket_depth == 0
            and brace_depth == 0
        ):
            expression = rest[:i].strip()
            message = rest[i:]
            return indent, expression, message, newline

    return indent, rest.strip(), "", newline


def mutate_m1(text):
    found = find_plant_body_lines(text)
    if not found:
        return None, "plant() not found"

    lines, body_start, body_end = found
    for i in range(body_start, body_end):
        parsed = split_assert_expression(lines[i])
        if not parsed:
            continue
        indent, expression, message, newline = parsed
        if not expression:
            continue
        lines[i] = indent + "assert not (" + expression + ")" + message + newline
        return "".join(lines), None

    return None, "no assert found inside plant()"


def mutate_m2(text):
    found = find_plant_body_lines(text)
    if not found:
        return None, "plant() not found"

    lines, body_start, body_end = found
    for i in range(body_start, body_end):
        if re.match(r"^[ \t]*assert[ \t]+", lines[i]):
            del lines[i]
            return "".join(lines), None

    return None, "no assert line found inside plant()"


def find_matching_brace(text, open_index):
    in_string = None
    escaped = False
    comment = False
    depth = 0

    for i in range(open_index, len(text)):
        char = text[i]

        if comment:
            if char == "\n":
                comment = False
            continue

        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == in_string:
                if i + 2 < len(text) and text[i:i + 3] == in_string * 3:
                    in_string = None
                    i += 2
                elif len(in_string) == 1:
                    in_string = None
            continue

        if char == "#":
            comment = True
        elif text[i:i + 3] in ("'''", '"""'):
            in_string = text[i:i + 3]
        elif char in ("'", '"'):
            in_string = char
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return i

    return None


def find_control_dict_spans(text):
    pattern = re.compile(
        r"(?m)^([A-Za-z_][A-Za-z0-9_]*?(?:_CONTROL)|MODEL_ANSWER)[ \t]*=[ \t]*\{"
    )
    spans = []

    for match in pattern.finditer(text):
        open_index = text.find("{", match.start(), match.end())
        if open_index < 0:
            continue
        close_index = find_matching_brace(text, open_index)
        if close_index is None:
            continue
        spans.append((open_index, close_index + 1))

    return spans


def replace_first_string_literal(text, start, end):
    i = start
    in_comment = False

    while i < end:
        char = text[i]

        if in_comment:
            if char == "\n":
                in_comment = False
            i += 1
            continue

        if char == "#":
            in_comment = True
            i += 1
            continue

        prefix_start = i
        while i < end and text[i] in "rRuUbBfF":
            i += 1

        quote = None
        quote_len = 0
        if text[i:i + 3] in ("'''", '"""'):
            quote = text[i:i + 3]
            quote_len = 3
        elif i < end and text[i] in ("'", '"'):
            quote = text[i]
            quote_len = 1
        else:
            i = prefix_start + 1
            continue

        literal_start = prefix_start
        content_start = i + quote_len
        j = content_start
        escaped = False

        while j < end:
            if escaped:
                escaped = False
                j += 1
                continue
            if text[j] == "\\":
                escaped = True
                j += 1
                continue
            if text[j:j + quote_len] == quote:
                literal_end = j + quote_len
                return text[:literal_start] + '"MUTATED"' + text[literal_end:]
            j += 1

        return None

    return None


def mutate_m3(text):
    for start, end in find_control_dict_spans(text):
        mutated = replace_first_string_literal(text, start, end)
        if mutated is not None:
            return mutated, None
    return None, "no string literal found inside _CONTROL or MODEL_ANSWER dict"


def mutate_m4(text):
    """Perturb the first NUMBER inside MODEL_ANSWER. The arithmetic must notice.

    ⛔ M3 WAS TOO SHALLOW AND ITS SURVIVORS WERE NOT FINDINGS. It replaces the first string
    literal inside a control dict, which in every component here is the KEY "app_id". Changing
    a key nothing reads cannot change an outcome, so the mutant SHOULD survive -- and counting
    that as "the controls did not notice" would have reported 11 survivors as weak controls
    when most were the operator being cosmetic.

    ⚠️ A mutation operator that cannot reach an expectation measures itself. This one changes a
    NUMBER the model answer's assertions are computed from, so a plant that checks arithmetic
    must fail and a plant that only checks shapes will not -- which is the real question.
    """
    m = re.search(r"MODEL_ANSWER\s*=\s*\{", text)
    if not m:
        return None, "no MODEL_ANSWER block found"
    tail = text[m.end():]
    # A bare integer or float that is a VALUE (preceded by ": " or ", "), not a key or an index.
    num = re.search(r"(?<=[:,]\s)(\d+(?:\.\d+)?)(?=\s*[,}\]])", tail)
    if not num:
        return None, "no numeric value found inside MODEL_ANSWER"
    try:
        original = float(num.group(1))
    except ValueError:
        return None, "numeric literal did not parse"
    replacement = repr(original * 3.0 + 7.0) if "." in num.group(1) else str(int(original) * 3 + 7)
    start = m.end() + num.start()
    end = m.end() + num.end()
    return text[:start] + replacement + text[end:], None


def build_mutant_text(text, mutation):
    if mutation == "M1":
        return mutate_m1(text)
    if mutation == "M2":
        return mutate_m2(text)
    if mutation == "M3":
        return mutate_m3(text)
    if mutation == "M4":
        return mutate_m4(text)
    return None, "unknown mutation"


def status_for_mutant(run_result):
    if run_result["kind"] == "timeout":
        return "timeout"
    if run_result["code"] == 0:
        return "survived"
    return "killed"


def print_output_line(text):
    print(text)


def select_modules(only):
    if not only:
        return MODULES
    selected = []
    requested = [item.strip() for item in only.split(",") if item.strip()]
    for item in requested:
        if item not in MODULES:
            print_output_line("Unknown module for --only: " + item)
        else:
            selected.append(item)
    return selected


def main():
    sys.stdout = io.TextIOWrapper(
        sys.stdout.buffer,
        encoding="utf-8",
        errors="replace",
        line_buffering=True,
    )

    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default="F:/wt-regen")
    parser.add_argument("--only", default="")
    args = parser.parse_args()

    repo = normalize_repo(args.repo)
    modules = select_modules(args.only)

    totals = {
        "killed": 0,
        "survived": 0,
        "mutant-could-not-be-built": 0,
        "baseline-plant-already-failing": 0,
        "timeout": 0,
        "built": 0,
        "possible": 0,
    }

    survivors = []
    baseline_failures = []

    print_output_line(
        "Kinds: killed, survived, mutant-could-not-be-built, "
        "baseline-plant-already-failing, timeout"
    )

    for module in modules:
        source_path = module_source_path(repo, module)
        print_output_line("")
        print_output_line(module)

        if not os.path.exists(source_path):
            print_output_line("  baseline: baseline-plant-already-failing source missing")
            totals["baseline-plant-already-failing"] += len(MUTATIONS)
            totals["possible"] += len(MUTATIONS)
            baseline_failures.append((module, "source missing"))
            print_output_line("  0 of " + str(len(MUTATIONS)) + " mutants were killed")
            continue

        baseline = run_plant(source_path, repo, repo)
        baseline_ok = baseline["kind"] == "exit" and baseline["code"] == 0

        if baseline_ok:
            print_output_line("  baseline: exit 0")
        elif baseline["kind"] == "timeout":
            print_output_line("  baseline: baseline-plant-already-failing timeout")
            baseline_failures.append((module, "timeout"))
        else:
            print_output_line(
                "  baseline: baseline-plant-already-failing exit "
                + str(baseline["code"])
            )
            baseline_failures.append((module, "exit " + str(baseline["code"])))

        try:
            source = read_text(source_path)
        except OSError as exc:
            source = None
            print_output_line("  source-read: " + str(exc))

        module_killed = 0
        module_built = 0
        module_possible = len(MUTATIONS)
        totals["possible"] += module_possible

        for mutation in MUTATIONS:
            if not baseline_ok:
                totals["baseline-plant-already-failing"] += 1
                print_output_line(
                    "  " + mutation + ": baseline-plant-already-failing"
                )
                continue

            if source is None:
                totals["mutant-could-not-be-built"] += 1
                print_output_line(
                    "  " + mutation + ": mutant-could-not-be-built source unreadable"
                )
                continue

            mutant_text, error = build_mutant_text(source, mutation)
            if mutant_text is None:
                totals["mutant-could-not-be-built"] += 1
                print_output_line(
                    "  " + mutation + ": mutant-could-not-be-built " + error
                )
                continue

            temp_dir = tempfile.mkdtemp(prefix="plant_mutation_check_")
            try:
                mutant_path = os.path.join(temp_dir, module + ".py")
                write_text(mutant_path, mutant_text)
                module_built += 1
                totals["built"] += 1

                result = run_plant(mutant_path, repo, repo, temp_dir=temp_dir)
                status = status_for_mutant(result)

                if status == "killed":
                    module_killed += 1
                    totals["killed"] += 1
                    print_output_line(
                        "  "
                        + mutation
                        + ": killed exit "
                        + str(result["code"])
                    )
                elif status == "survived":
                    totals["survived"] += 1
                    survivors.append((module, mutation))
                    print_output_line("  " + mutation + ": survived exit 0")
                else:
                    totals["timeout"] += 1
                    print_output_line("  " + mutation + ": timeout")
            finally:
                shutil.rmtree(temp_dir, ignore_errors=True)

        print_output_line(
            "  "
            + str(module_killed)
            + " of "
            + str(module_possible)
            + " mutants were killed"
        )

    print_output_line("")
    print_output_line("Survivors:")
    if survivors:
        for module, mutation in survivors:
            print_output_line("  " + module + " " + mutation)
    else:
        print_output_line("  none")

    print_output_line("")
    print_output_line("Baseline failures:")
    if baseline_failures:
        for module, reason in baseline_failures:
            print_output_line("  " + module + " " + reason)
    else:
        print_output_line("  none")

    print_output_line("")
    print_output_line("Counts:")
    print_output_line("  killed: " + str(totals["killed"]))
    print_output_line("  survived: " + str(totals["survived"]))
    print_output_line(
        "  mutant-could-not-be-built: "
        + str(totals["mutant-could-not-be-built"])
    )
    print_output_line(
        "  baseline-plant-already-failing: "
        + str(totals["baseline-plant-already-failing"])
    )
    print_output_line("  timeout: " + str(totals["timeout"]))
    print_output_line(
        "Overall: "
        + str(totals["killed"])
        + " of "
        + str(totals["possible"])
        + " mutants were killed"
    )

    if totals["built"] == 0:
        print_output_line(
            "ZERO mutants could be built; this is a failure of the instrument."
        )
        return 2
    if totals["survived"] > 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
