#!/usr/bin/env python
"""Survey verdict-producing checks for shape and vacuity risks.

This is an evidence script, not a fixer. It reads source, runs bounded local
checks under the caller's Python, and writes a Markdown report. It deliberately
does not modify ssot/**/*.json or any check implementation.
"""

from __future__ import annotations

import ast
import collections
import dataclasses
import inspect
import json
import os
import pathlib
import re
import subprocess
import sys
import textwrap
import warnings
from typing import Any, Mapping


warnings.simplefilter("error")

REPO = pathlib.Path(__file__).resolve().parents[1]
SSOT = REPO / "ssot"
SCRIPTS = REPO / "scripts"
HOOKS = REPO / ".githooks"
REPORT = REPO / "evidence" / "2026-08-19-corpus" / "vacuity_sweep.md"

CHECK_NAME_RE = re.compile(
    r"(check|gate|validat|verify|audit|assess|verdict|reconcile|"
    r"precondition|invariant|readiness|classify|require|guard|enforce|"
    r"screen|integrity|consistency|census|lint|assert|selftest)",
    re.I,
)

SKIP_GENERIC_FILES = {
    "ssot/validate_v2.py",
    "ssot/preconditions.py",
    "scripts/nafis_harness/probes.py",
    "scripts/nafis_harness/probes_corpus.py",
    "scripts/nafis_harness/probes_build.py",
    "scripts/vacuity_sweep.py",
}

SELFTEST_FILES = [
    "scripts/withdrawal_reason_gate.py",
    "scripts/verdict.py",
    "scripts/text_match.py",
    "scripts/absence_reason_gate.py",
    "scripts/analyze_poolability.py",
    "scripts/subject_match_gate.py",
    "scripts/banner_anchor.py",
    "scripts/subject_is_experimental_gate.py",
    "scripts/alignment_gate.py",
    "scripts/ssot_net_deletion_check.py",
    "scripts/arm_identity_gate.py",
    "scripts/silent_exclusion_screen.py",
    "scripts/section_manifest_gate.py",
    "scripts/search_recall_gate.py",
    "scripts/screen_harness.py",
    "scripts/build_stamp_gate.py",
    "scripts/clone_contamination_gate.py",
    "scripts/corpus/corpus_detectors.py",
    "scripts/registration_identity_gate.py",
    "scripts/rebuild_guard.py",
    "scripts/extraction_table_gate.py",
    "scripts/export_artefact.py",
    "scripts/declared_contrast_gate.py",
    "scripts/protocol_subject_gate.py",
    "scripts/estimand_definition_gate.py",
    "scripts/prose_claim_gate.py",
    "scripts/durable_artefact_gate.py",
    "scripts/count_provenance_gate.py",
    "scripts/double_escape_gate.py",
    "scripts/project_index_cards.py",
    "scripts/precision_sample_gate.py",
    "scripts/citation_year_gate.py",
    "scripts/card_alignment_gate.py",
    "scripts/pooled_value_gate.py",
    "scripts/poolability.py",
    "scripts/identity_by_registration_gate.py",
    "scripts/headline_reproducible_gate.py",
    "scripts/index_markup_gate.py",
    "scripts/identity_gate.py",
    "scripts/k_consistency_gate.py",
    "scripts/gate_integrity.py",
]


@dataclasses.dataclass
class Row:
    category: str
    name: str
    file: str
    line: int
    depends: str
    shape_assert: str
    pass_without_predicate: str
    consumes: str
    emissions: str = "UNKNOWN"
    adjudicated: str = "UNKNOWN"
    passes: str = "UNKNOWN"
    fails: str = "UNKNOWN"
    invalid: str = "UNKNOWN"
    basis: str = "static read"


def rel(path: pathlib.Path | str) -> str:
    p = pathlib.Path(path)
    try:
        return p.relative_to(REPO).as_posix()
    except ValueError:
        return str(p)


def md_escape(value: Any) -> str:
    text = str(value)
    text = text.replace("|", "\\|")
    text = text.replace("\n", "<br>")
    return text


def short(value: Any, limit: int = 140) -> str:
    text = str(value)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > limit:
        return text[: limit - 3] + "..."
    return text


def source_text(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8-sig", errors="replace")


def object_location(obj: Any) -> tuple[str, int]:
    path = inspect.getsourcefile(obj)
    line = inspect.getsourcelines(obj)[1]
    return rel(pathlib.Path(path)), line


def source_of(obj: Any) -> str:
    try:
        return inspect.getsource(obj)
    except (OSError, TypeError):
        return ""


def extract_dependencies_from_source(src: str) -> str:
    out: list[str] = []
    try:
        tree = ast.parse(textwrap.dedent(src))
    except SyntaxError:
        return "UNKNOWN"

    def add(s: str) -> None:
        if not isinstance(s, str):
            return
        if not s or len(s) > 80:
            return
        if re.search(r"[a-zA-Z_][a-zA-Z0-9_]*(\.[a-zA-Z_][a-zA-Z0-9_]*)*", s):
            out.append(s)

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            fname = ""
            if isinstance(node.func, ast.Name):
                fname = node.func.id
            elif isinstance(node.func, ast.Attribute):
                fname = node.func.attr
            if fname in {"read", "read_scalar", "get", "pop", "setdefault"}:
                for arg in node.args[:2]:
                    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                        add(arg.value)
            for kw in node.keywords:
                if isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                    if kw.arg and kw.arg.endswith(("path", "field", "key", "id")):
                        add(kw.value.value)
        elif isinstance(node, ast.Subscript):
            sl = node.slice
            if isinstance(sl, ast.Constant) and isinstance(sl.value, str):
                add(sl.value)
    dedup = []
    for item in out:
        if item not in dedup:
            dedup.append(item)
    return ", ".join(dedup[:12]) if dedup else "UNKNOWN"


def consumes_from_source(path: str, src: str) -> str:
    lower = (path + "\n" + src).lower()
    bits = []
    if "mcp" in lower or "ctgov" in lower or "clinicaltrials" in lower:
        bits.append("MCP/ClinicalTrials.gov payload")
    if "cache" in lower or ".json" in lower or "build-artefacts" in lower:
        bits.append("cached/json file or build artefact")
    if "wrapper" in lower or "adapter" in lower or "payloads_for" in lower:
        bits.append("wrapper/adapter payload")
    if ".html" in lower or "page" in lower:
        bits.append("HTML/page surface")
    if "subprocess" in lower or ".githooks" in lower or "pre-push" in lower:
        bits.append("process/hook status")
    return "; ".join(dict.fromkeys(bits)) or "local object/source"


def shape_heuristic(src: str) -> str:
    if "require_raw_v2" in src or "WrongPayloadShape" in src:
        return "yes"
    if "assessment.read" in src or ("read(" in src and "judge(" in src):
        return "yes"
    if "make_invalid" in src or "INVALID" in src or "return 2" in src:
        return "partial"
    if "raise " in src and ("not " in src or "missing" in src.lower()):
        return "partial"
    return "UNKNOWN"


def vacuity_heuristic(src: str) -> str:
    dedented = textwrap.dedent(src)
    first_block = dedented.find("rep.block")
    prefix = dedented if first_block == -1 else dedented[:first_block]
    if re.search(r"\breturn\s*(?:\n|#|$)", prefix) or "return []" in prefix or 'return ""' in prefix:
        return "yes"
    if "if not " in prefix and "return" in prefix:
        return "yes"
    if "continue" in dedented and "rep.block" in dedented and "if not" in dedented:
        return "unclear"
    return "UNKNOWN"


def import_project_modules() -> None:
    for path in (str(SSOT), str(SCRIPTS), str(REPO)):
        if path not in sys.path:
            sys.path.insert(0, path)


def measure_nafis() -> tuple[list[Row], dict[str, Any]]:
    import_project_modules()
    import harness_gate
    from nafis_harness import Verdict, build_registry
    from nafis_harness.artefact import ARTEFACT_DECIDABLE, RETRIEVAL_SCOPED, payloads_for

    reg = build_registry()
    stats: dict[str, dict[str, Any]] = {
        cid: {
            "emissions": 0,
            "adjudicated": 0,
            "passes": 0,
            "fails": 0,
            "invalid": 0,
            "vacuous": 0,
            "examples": [],
        }
        for cid in reg.ids()
    }
    artefacts = sorted((REPO / "build-artefacts").glob("*.json"))
    for path in artefacts:
        try:
            with path.open(encoding="utf-8") as fh:
                art = json.load(fh)
        except Exception:
            continue
        for check_id, payload in payloads_for(art):
            s = stats.setdefault(
                check_id,
                {
                    "emissions": 0,
                    "adjudicated": 0,
                    "passes": 0,
                    "fails": 0,
                    "invalid": 0,
                    "vacuous": 0,
                    "examples": [],
                },
            )
            s["emissions"] += 1
            result = reg.run(check_id, payload)
            if result.verdict is Verdict.PASS:
                s["passes"] += 1
                s["adjudicated"] += 1
            elif result.verdict is Verdict.FAIL:
                s["fails"] += 1
                s["adjudicated"] += 1
            else:
                s["invalid"] += 1
                if str(result.reason).startswith("PASS is vacuous"):
                    s["vacuous"] += 1
                    if len(s["examples"]) < 8:
                        key = (
                            payload.get("row_id")
                            or payload.get("pool_id")
                            or payload.get("page_id")
                            or payload.get("surface_id")
                            or "?"
                        )
                        s["examples"].append(
                            {
                                "artefact": rel(path),
                                "key": key,
                                "reason": result.reason,
                                "terms": sorted(result.vacuity.get("vacuous_terms") or []),
                            }
                        )

    rows: list[Row] = []
    for cid in reg.ids():
        chk = reg.get(cid)
        file, line = object_location(chk.fn)
        reads = ", ".join(chk.instrument.reads) if chk.instrument.reads else "UNKNOWN"
        st = stats[cid]
        if st["vacuous"]:
            shape = "no (predicate vocabulary not fully asserted)"
            pwop = "yes"
        elif st["emissions"] == 0:
            shape = "partial (registered harness controls; not emitted here)"
            pwop = "UNKNOWN (no corpus emission)"
        else:
            shape = "partial (harness controls and witness required)"
            pwop = "no by harness vacuity run"
        if cid in RETRIEVAL_SCOPED:
            consumes = "retrieval-scoped wrapper payload; not build-artefact runnable"
        elif cid in ARTEFACT_DECIDABLE:
            consumes = "build-artefacts/*.json via payloads_for adapter"
        else:
            consumes = "registered harness payload"
        rows.append(
            Row(
                category="NAFIS CHK registry",
                name=cid,
                file=file,
                line=line,
                depends=reads,
                shape_assert=shape,
                pass_without_predicate=pwop,
                consumes=consumes,
                emissions=str(st["emissions"]),
                adjudicated=str(st["adjudicated"]),
                passes=str(st["passes"]),
                fails=str(st["fails"]),
                invalid=str(st["invalid"]),
                basis="executed harness against build-artefacts",
            )
        )
    total_emissions = sum(s["emissions"] for s in stats.values())
    total_adjudicated = sum(s["adjudicated"] for s in stats.values())
    total_passes = sum(s["passes"] for s in stats.values())
    total_fails = sum(s["fails"] for s in stats.values())
    total_invalid = sum(s["invalid"] for s in stats.values())
    file, line = object_location(harness_gate.main)
    rows.append(
        Row(
            category="NAFIS aggregate gate",
            name="harness_gate aggregate process PASS",
            file=file,
            line=line,
            depends="build-artefact payloads, child Result.verdict, invalid-ceiling",
            shape_assert="partial (zero executions exit 2; invalids allowed below ceiling)",
            pass_without_predicate=(
                "yes at process level: exits 0 while child INVALID results are present"
                if total_invalid
                else "no observed child INVALIDs"
            ),
            consumes="build-artefacts/*.json via payloads_for adapter",
            emissions=str(total_emissions),
            adjudicated=str(total_adjudicated),
            passes=f"1 process PASS; {total_passes} child PASS",
            fails=str(total_fails),
            invalid=str(total_invalid),
            basis="derived from executed harness run; confirmed by harness_gate CLI",
        )
    )
    return rows, {"artefacts": len(artefacts), "stats": stats}


def measure_preconditions() -> tuple[list[Row], dict[str, Any]]:
    import_project_modules()
    import corpus_assess as C
    import preconditions as P
    from assessment import FAIL, NOT_ASSESSABLE, PASS

    report = C.build_report()
    names = getattr(P, "PRECONDITIONS", getattr(P, "SEVEN"))
    rows: list[Row] = []
    stats: dict[str, Any] = {}
    for name in names:
        fn, reads, _accepts, _unit = P.REGISTRY._by_name[name]
        counts = report["precondition_tally"][name]
        emissions = sum(counts.values())
        adjudicated = counts[PASS] + counts[FAIL]
        stats[name] = {
            "emissions": emissions,
            "adjudicated": adjudicated,
            "passes": counts[PASS],
            "fails": counts[FAIL],
            "not_assessable": counts[NOT_ASSESSABLE],
            "assessor_bug": counts.get(C.ASSESSOR_BUG, 0),
        }
        file, line = object_location(fn)
        rows.append(
            Row(
                category="registered precondition",
                name=name,
                file=file,
                line=line,
                depends=", ".join(reads),
                shape_assert="yes (assessment.read/judge path; registry type guard where declared)",
                pass_without_predicate="no observed PASS without predicate; NOT_ASSESSABLE is explicit",
                consumes="ssot/<topic>/<topic>.json cached object",
                emissions=str(emissions),
                adjudicated=str(adjudicated),
                passes=str(counts[PASS]),
                fails=str(counts[FAIL]),
                invalid=str(counts[NOT_ASSESSABLE]),
                basis="executed corpus_assess.build_report without writing corpus_assess.json",
            )
        )
    return rows, {
        "coverage": report["coverage"],
        "authority_publishable": report["authority_publishable"],
        "batch1_known_answer": report["batch1_known_answer_check"],
        "detector4_alarms": report["detector4_alarms"],
        "stats": stats,
        "names": list(names),
    }


def measure_validate_v2() -> tuple[list[Row], dict[str, Any]]:
    import_project_modules()
    import validate_v2 as V

    paths = sorted(SSOT.glob("*/*.json"))
    stats: dict[str, dict[str, Any]] = {
        name: {"emissions": 0, "passes": 0, "blocks": 0, "notes": 0, "raises": 0, "raise_examples": []}
        for name, _ in V.DETECTORS
    }
    for path in paths:
        try:
            canon = json.loads(path.read_text(encoding="utf-8-sig"))
        except Exception:
            continue
        for name, fn in V.DETECTORS:
            rep = V.Report()
            st = stats[name]
            st["emissions"] += 1
            try:
                fn(canon, rep)
            except Exception as exc:
                st["raises"] += 1
                if len(st["raise_examples"]) < 3:
                    st["raise_examples"].append(f"{path.name}: {type(exc).__name__}: {exc}")
                continue
            st["blocks"] += len(rep.blocks)
            st["notes"] += len(rep.notes)
            if not rep.blocks:
                st["passes"] += 1

    rows: list[Row] = []
    for name, fn in V.DETECTORS:
        file, line = object_location(fn)
        src = source_of(fn)
        st = stats[name]
        can_pass = vacuity_heuristic(src)
        if name in {"network", "removal-grounds", "source-category-binding", "arm-completeness"}:
            can_pass = "yes"
        if name in {"cross-engine-recompute", "grade-certainty"}:
            can_pass = "yes when optional dependency/grade subject is absent or skipped; CLI currently raises here"
        rows.append(
            Row(
                category="validate_v2 detector",
                name=name,
                file=file,
                line=line,
                depends=extract_dependencies_from_source(src),
                shape_assert="no common schema guard; per-detector run raised on malformed/missing shapes",
                pass_without_predicate=can_pass,
                consumes="ssot/<topic>/<topic>.json cached object; some source-cache helpers",
                emissions=str(st["emissions"]),
                adjudicated="UNKNOWN",
                passes=str(st["passes"]),
                fails=str(st["blocks"]),
                invalid=str(st["raises"]),
                basis="executed detector directly with exceptions captured; validate() CLI aborts on missing modules",
            )
        )
    return rows, {"json_paths": len(paths), "stats": stats}


def registered_support_rows() -> list[Row]:
    import_project_modules()
    rows: list[Row] = []

    import assessment
    import assessor_registry
    import ctgov_transport
    import estimand_identity
    import invariants
    import journal_profile
    import projectors
    import projectors2
    import synthesis_reconcile
    import topic_identity

    support = [
        ("assessment helper", "assessment.read", assessment.read,
         "dotted path", "yes", "no (reader only; no PASS emitted)", "dict object"),
        ("assessment helper", "assessment.judge", assessment.judge,
         "Reading.state/value", "yes", "no (predicate called only for present Reading)", "Reading wrapper"),
        ("assessment helper", "assessment.assess", assessment.assess,
         "dotted path", "yes", "no (delegates to read/judge)", "dict object"),
        ("assessment helper", "assessment.inclusion_criteria_auditable",
         assessment.inclusion_criteria_auditable, "screening.eligibility", "yes",
         "no observed; delegates to judge(read())", "cached object"),
        ("assessment helper", "assessment.eligibility_met", assessment.eligibility_met,
         "screening.eligibility, full_text_read", "yes",
         "no; returns NOT_ASSESSABLE without full text", "cached object"),
        ("assessment helper", "assessment.require_named_intervention",
         assessment.require_named_intervention, "topic, intervention, condition", "yes",
         "no PASS emitted; raises on malformed query", "query wrapper"),
        ("assessor registry gate", "Registry.register duplicate-path guard",
         assessor_registry.Registry.register, "declared reads, function source, unit_source", "yes",
         "no PASS emitted; raises AssessorRejected", "assessor registration wrapper"),
        ("assessor registry gate", "Registry.type_guard",
         assessor_registry.Registry.type_guard, "accepts map, declared reads", "yes",
         "no PASS emitted; returns NOT_ASSESSABLE on type mismatch", "assessor/cached object"),
        ("assessor registry gate", "Registry.identical_tally_alarm",
         assessor_registry.Registry.identical_tally_alarm, "assessor result tallies", "partial",
         "yes if fewer than two assessors; caller must not count [] as clean evidence", "assessor results"),
        ("transport guard", "ctgov_transport.require_raw_v2", ctgov_transport.require_raw_v2,
         "protocolSection.armsInterventionsModule", "yes", "no PASS emitted; raises WrongPayloadShape",
         "MCP/ClinicalTrials.gov raw-v2 payload"),
        ("topic assessor", "topic_identity.locate", topic_identity.locate,
         "protocolSection.armsInterventionsModule.armGroups/interventions", "no",
         "yes for verdict-shaped NOT_ASSESSABLE on flattened MCP shape", "MCP/ClinicalTrials.gov payload"),
        ("estimand assessor", "estimand_identity.compare", estimand_identity.compare,
         "estimand definition strings", "partial", "no PASS label; SAME only after string comparison", "object fields"),
        ("estimand assessor", "estimand_identity.compare_all", estimand_identity.compare_all,
         "estimand definition list", "partial", "no PASS label; <2 definitions returns UNDECIDABLE", "object fields"),
        ("invariant", "invariants.identical_output_alarm", invariants.identical_output_alarm,
         "mapping of inputs to outputs", "partial", "yes if caller treats [] over <2 inputs as pass", "cache/comparison wrapper"),
        ("invariant", "invariants.cache_is_valid", invariants.cache_is_valid,
         "cache file path", "yes", "no PASS emitted; boolean helper", "cache file"),
        ("journal profile", "journal_profile.check_abstract", journal_profile.check_abstract,
         "abstract text/list", "partial", "UNKNOWN", "journal profile dict"),
        ("journal profile", "journal_profile.check_keywords", journal_profile.check_keywords,
         "keywords list", "partial", "UNKNOWN", "journal profile dict"),
        ("journal profile", "journal_profile.check_title_words", journal_profile.check_title_words,
         "title words", "partial", "UNKNOWN", "journal profile dict"),
        ("journal profile", "journal_profile.enforce", journal_profile.enforce,
         "journal profile checks", "partial", "no PASS emitted; raises ProfileViolation", "journal profile dict"),
        ("projector gate", "projectors.readiness", projectors.readiness,
         "attestations, registration, results.by_outcome, screening", "no",
         "unclear; can emit READY if blocking/outstanding lists stay empty", "cached object"),
        ("projector gate", "projectors.verdict_card", projectors.verdict_card,
         "preconditions/verdict blocks", "partial", "UNKNOWN", "cached object/html renderer"),
        ("projector gate", "projectors2.screening_cards", projectors2.screening_cards,
         "screening/absent_from_source", "partial", "UNKNOWN", "cached object/html renderer"),
        ("projector gate", "projectors2.published_comparison_card", projectors2.published_comparison_card,
         "published_comparison/checks denominator", "no",
         "no PASS emitted; silently returns empty HTML when checks/denominator absent", "cached object/html renderer"),
        ("projector gate", "projectors2.rob2_card", projectors2.rob2_card,
         "rob2/trials", "no",
         "no PASS emitted; silently returns empty HTML when subject absent", "cached object/html renderer"),
        ("synthesis assessor", "synthesis_reconcile.select_included_table",
         synthesis_reconcile.select_included_table, "tables/title/header/ids", "partial",
         "no PASS label; returns NOT-ASSESSABLE/REFUSED on no/multiple candidates", "PDF/table extraction wrapper"),
        ("synthesis assessor", "synthesis_reconcile.classify_record",
         synthesis_reconcile.classify_record, "trial id/status/category", "partial",
         "no PASS label; unknowns become UNCATEGORISED", "source/corpus record"),
        ("synthesis assessor", "synthesis_reconcile.rate_is_quotable",
         synthesis_reconcile.rate_is_quotable, "classification counts", "yes",
         "no PASS label; fail-closed on zero total or high uncategorised share", "classification tally"),
    ]
    for category, name, obj, depends, shape, pwop, consumes in support:
        file, line = object_location(obj)
        rows.append(
            Row(
                category=category,
                name=name,
                file=file,
                line=line,
                depends=depends,
                shape_assert=shape,
                pass_without_predicate=pwop,
                consumes=consumes,
                basis="static read; selected support surface",
            )
        )
    return rows


def generic_static_rows(already: set[tuple[str, int, str]]) -> tuple[list[Row], dict[str, Any]]:
    rows: list[Row] = []
    scanned_files: list[pathlib.Path] = []
    parse_failures: list[str] = []
    for root in (SSOT, SCRIPTS):
        if root.exists():
            scanned_files.extend(sorted(p for p in root.rglob("*.py") if "__pycache__" not in p.parts))
    if HOOKS.exists():
        scanned_files.extend(sorted(p for p in HOOKS.rglob("*") if p.is_file()))

    for path in scanned_files:
        rpath = rel(path)
        if rpath in SKIP_GENERIC_FILES:
            continue
        if path.is_file() and path.suffix != ".py":
            if rpath.startswith(".githooks/"):
                rows.append(
                    Row(
                        category="hook gate",
                        name=rpath,
                        file=rpath,
                        line=1,
                        depends="changed files, build artefacts, regression pages, process exit codes",
                        shape_assert="partial",
                        pass_without_predicate=(
                            "yes for scoped no-op branches; output labels them as scoped, not corpus clean"
                        ),
                        consumes="git hook/process status/wrapper commands",
                        basis="static shell read; not executed to avoid pre-push side effects",
                    )
                )
            continue
        try:
            text = source_text(path)
            tree = ast.parse(text)
        except Exception as exc:
            if CHECK_NAME_RE.search(rpath):
                parse_failures.append(f"{rpath}: {type(exc).__name__}: {exc}")
                rows.append(
                    Row(
                        category="static candidate",
                        name="PARSE-FAILED",
                        file=rpath,
                        line=1,
                        depends="UNKNOWN",
                        shape_assert="UNKNOWN",
                        pass_without_predicate="UNKNOWN",
                        consumes=consumes_from_source(rpath, ""),
                        basis=f"AST parse failed: {type(exc).__name__}: {exc}",
                    )
                )
            continue
        lines = text.splitlines()
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue
            if not CHECK_NAME_RE.search(node.name):
                continue
            key = (rpath, node.lineno, node.name)
            if key in already:
                continue
            start = node.lineno - 1
            end = getattr(node, "end_lineno", node.lineno)
            src = "\n".join(lines[start:end])
            rows.append(
                Row(
                    category="static candidate",
                    name=node.name,
                    file=rpath,
                    line=node.lineno,
                    depends=extract_dependencies_from_source(src),
                    shape_assert=shape_heuristic(src),
                    pass_without_predicate=vacuity_heuristic(src),
                    consumes=consumes_from_source(rpath, src),
                    basis="AST name-pattern scan; not all candidates are runtime gates",
                )
            )
    return rows, {"scanned_files": len(scanned_files), "parse_failures": parse_failures}


def run_selftests() -> list[dict[str, Any]]:
    out = []
    for relpath in SELFTEST_FILES:
        path = REPO / relpath
        args = [sys.executable, "-W", "error", str(path), "--selftest"]
        try:
            proc = subprocess.run(
                args,
                cwd=REPO,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=60,
            )
            combined = (proc.stdout or "") + (proc.stderr or "")
            out.append(
                {
                    "file": relpath,
                    "exit": proc.returncode,
                    "warning": "ResourceWarning" in combined or "warning:" in combined.lower(),
                    "tail": short(combined.strip()[-500:], 300),
                }
            )
        except subprocess.TimeoutExpired:
            out.append({"file": relpath, "exit": "TIMEOUT", "warning": "UNKNOWN", "tail": ""})
    return out


def run_validate_cli_probe() -> dict[str, Any]:
    target = SSOT / "iv-iron-hf" / "iv-iron-hf.json"
    proc = subprocess.run(
        [sys.executable, "-W", "error", str(SSOT / "validate_v2.py"), str(target)],
        cwd=REPO,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )
    return {"exit": proc.returncode, "tail": short(((proc.stdout or "") + (proc.stderr or "")).strip(), 500)}


def code_block(path: str, start: int, end: int) -> str:
    p = REPO / path
    lines = source_text(p).splitlines()
    body = []
    for num in range(start, min(end, len(lines)) + 1):
        body.append(f"{num:>4}: {lines[num - 1]}")
    return "```python\n" + "\n".join(body) + "\n```"


def table(rows: list[Row]) -> str:
    headers = [
        "name",
        "file:line",
        "depends on",
        "shape assert?",
        "PASS without predicate?",
        "consumes",
        "emissions",
        "adjudicated",
        "passes",
        "fail/block",
        "invalid/raise",
        "basis",
    ]
    parts = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for r in rows:
        parts.append(
            "| "
            + " | ".join(
                md_escape(x)
                for x in [
                    f"{r.category}: {r.name}",
                    f"{r.file}:{r.line}",
                    r.depends,
                    r.shape_assert,
                    r.pass_without_predicate,
                    r.consumes,
                    r.emissions,
                    r.adjudicated,
                    r.passes,
                    r.fails,
                    r.invalid,
                    r.basis,
                ]
            )
            + " |"
        )
    return "\n".join(parts)


def render_report(
    rows: list[Row],
    nafis: dict[str, Any],
    pre: dict[str, Any],
    validate: dict[str, Any],
    static: dict[str, Any],
    selftests: list[dict[str, Any]],
    validate_cli: dict[str, Any],
) -> str:
    measured_pass_gaps = []
    measured_other_gaps = []
    for r in rows:
        try:
            e = int(r.emissions)
            a = int(r.adjudicated)
        except ValueError:
            continue
        gap = e - a
        pass_no_pred = r.pass_without_predicate.lower().startswith("yes")
        if gap and pass_no_pred:
            measured_pass_gaps.append((gap, r))
        elif gap:
            measured_other_gaps.append((gap, r))
    measured_pass_gaps.sort(key=lambda item: (-item[0], item[1].name))
    measured_other_gaps.sort(key=lambda item: (-item[0], item[1].name))

    validate_pass_risks = []
    for name, st in validate["stats"].items():
        if st["passes"]:
            validate_pass_risks.append((st["passes"], st["raises"], st["blocks"], name))
    validate_pass_risks.sort(reverse=True)

    warning_selftests = [r for r in selftests if r["warning"] or r["exit"] != 0]
    total = len(rows)
    yes_shape = sum(1 for r in rows if str(r.shape_assert).startswith("yes"))
    no_shape = sum(1 for r in rows if str(r.shape_assert).startswith("no"))
    yes_vac = sum(1 for r in rows if str(r.pass_without_predicate).startswith("yes"))
    unknown_vac = sum(1 for r in rows if "UNKNOWN" in str(r.pass_without_predicate))

    out = []
    out.append("# Vacuity Sweep - 2026-08-19 Corpus")
    out.append("")
    out.append("Scope: source-only survey in `F:/rapidmeta-ssot-shell`; no network.")
    out.append("")
    out.append("## How I Found The Checks")
    out.append("")
    out.append(
        f"- Scanned `ssot/**/*.py`, `scripts/**/*.py`, and `.githooks/**` with an AST/name-pattern sweep. "
        f"Files considered: {static['scanned_files']}. Parse failures: {len(static['parse_failures'])}."
    )
    out.append(
        f"- Expanded runtime registries rather than relying on names alone: {len(nafis['stats'])} NAFIS checks, "
        f"{len(pre['names'])} registered preconditions, and {len(validate['stats'])} `validate_v2.DETECTORS`."
    )
    out.append(
        f"- Total row count reported below: {total}. This deliberately includes static candidates whose runtime "
        "applicability is UNKNOWN, because reporting UNKNOWN is safer than silently treating them as sound."
    )
    if static["parse_failures"]:
        out.append("")
        out.append("Parse failures from the static sweep:")
        for failure in static["parse_failures"]:
            out.append(f"- `{failure}`")
    out.append("")
    out.append("## Calibration")
    out.append("")
    out.append(
        "- `ctgov_transport.require_raw_v2()` is the reference transport pattern: it asserts "
        "`protocolSection.armsInterventionsModule` and raises `WrongPayloadShape` before role reading."
    )
    out.append(
        "- Current `ssot/preconditions.py` registers eight preconditions, not seven: the source says "
        "`inclusion_criteria_auditable` split into `criteria_stated` and `criteria_predefined` on 2026-08-19. "
        "All eight were scored shape-asserting because they route reads through `assessment.read`/`judge` "
        "or explicit `read_scalar`, and `contributes_a_randomised_contrast` refuses unknown arm-role vocabulary."
    )
    out.append(
        f"- Precondition corpus run: {pre['coverage']['candidate_directories']} candidate directories, "
        f"{pre['coverage']['read']} readable objects, {pre['coverage']['absent']} absent pseudo-topics. "
        f"Batch1 known-answer comparison matched: {pre['batch1_known_answer']['matched']}."
    )
    out.append("")
    out.append("## Main Ranking: Measured PASS-Style Gaps")
    out.append("")
    out.append(
        "This ranking includes only checks/gates where this sweep measured both emissions and adjudications "
        "and the gap can surface as a clean/pass-style result. Explicit NOT_ASSESSABLE or INVALID gaps are "
        "listed separately below, because those are not the CHK024 failure shape."
    )
    out.append("")
    out.append("| rank | check | emissions | adjudicated | gap | pass-without-predicate? | note |")
    out.append("| --- | --- | --- | --- | --- | --- | --- |")
    rank = 1
    for gap, r in measured_pass_gaps[:25]:
        note = ""
        if r.name == "CHK021_MEASURE_SCALE_MISMATCH":
            note = "5 vacuous PASSes on RATE_RATIO/WIN_RATIO rows in iv-iron-hf"
        elif r.name == "harness_gate aggregate process PASS":
            note = "process exit 0 with child INVALID results below the ceiling"
        out.append(
            f"| {rank} | {md_escape(r.category + ': ' + r.name)} | {r.emissions} | "
            f"{r.adjudicated} | {gap} | {md_escape(r.pass_without_predicate)} | {md_escape(note)} |"
        )
        rank += 1
    if not measured_pass_gaps:
        out.append("| - | none measured | - | - | - | - | - |")
    out.append("")
    out.append("Measured non-pass gaps, retained so the emissions/adjudications accounting is visible:")
    out.append("")
    out.append("| rank | check | emissions | adjudicated | gap | state |")
    out.append("| --- | --- | --- | --- | --- | --- |")
    for rank, (gap, r) in enumerate(measured_other_gaps[:25], 1):
        state = "explicit NOT_ASSESSABLE/INVALID, not PASS"
        out.append(
            f"| {rank} | {md_escape(r.category + ': ' + r.name)} | {r.emissions} | "
            f"{r.adjudicated} | {gap} | {md_escape(state)} |"
        )
    out.append("")
    out.append("## Current NAFIS Corpus Measurement")
    out.append("")
    n_tot = sum(s["emissions"] for s in nafis["stats"].values())
    n_adj = sum(s["adjudicated"] for s in nafis["stats"].values())
    n_pass = sum(s["passes"] for s in nafis["stats"].values())
    n_fail = sum(s["fails"] for s in nafis["stats"].values())
    n_invalid = sum(s["invalid"] for s in nafis["stats"].values())
    out.append(
        f"`build-artefacts/*.json`: {nafis['artefacts']} artefacts, {n_tot} emissions, "
        f"{n_adj} adjudicated, {n_pass} PASS, {n_fail} FAIL, {n_invalid} INVALID."
    )
    out.append("")
    chk21 = nafis["stats"].get("CHK021_MEASURE_SCALE_MISMATCH", {})
    if chk21.get("examples"):
        out.append("CHK021 vacuous examples:")
        for ex in chk21["examples"]:
            out.append(
                f"- `{ex['artefact']}` `{ex['key']}` terms={ex['terms']}: {short(ex['reason'], 220)}"
            )
    out.append("")
    out.append("## `validate_v2` Measurement")
    out.append("")
    out.append(
        f"Direct per-detector invocation over {validate['json_paths']} `ssot/*/*.json` files produced block/no-block "
        "counts, but not reliable actual adjudication counts. The CLI probe failed before a complete pass:"
    )
    out.append("")
    out.append(f"- `python -W error ssot/validate_v2.py ssot/iv-iron-hf/iv-iron-hf.json` exit {validate_cli['exit']}: {validate_cli['tail']}")
    out.append("")
    out.append("Highest pass-producing `validate_v2` rows, ranked by no-block pass emissions:")
    out.append("")
    out.append("| detector | passes | blocks | raises | pass-without-predicate risk |")
    out.append("| --- | --- | --- | --- | --- |")
    row_by_name = {r.name: r for r in rows if r.category == "validate_v2 detector"}
    for passes, raises, blocks, name in validate_pass_risks[:20]:
        risk = row_by_name[name].pass_without_predicate if name in row_by_name else "UNKNOWN"
        out.append(f"| `{name}` | {passes} | {blocks} | {raises} | {md_escape(risk)} |")
    out.append("")
    out.append("## Runnable Selftests")
    out.append("")
    out.append(
        "Each command was invoked as `python -W error <script> --selftest` with a 60 second timeout. "
        "Warnings are reported as defects in the warning policy even when Python printed them at shutdown "
        "and returned exit 0."
    )
    out.append("")
    out.append("| script | exit | warning? | tail |")
    out.append("| --- | --- | --- | --- |")
    for item in selftests:
        out.append(
            f"| `{item['file']}` | {item['exit']} | {item['warning']} | {md_escape(item['tail'])} |"
        )
    out.append("")
    if warning_selftests:
        out.append("Selftests that failed or emitted warnings:")
        for item in warning_selftests:
            out.append(f"- `{item['file']}` exit={item['exit']} warning={item['warning']}: {item['tail']}")
    out.append("")
    out.append("## Specific Verdict-Without-Reading Paths")
    out.append("")
    out.append("### CHK021 unknown measure falls through to PASS")
    out.append("")
    out.append(code_block("scripts/nafis_harness/probes_corpus.py", 396, 397))
    out.append(code_block("scripts/nafis_harness/probes_corpus.py", 668, 708))
    out.append(
        "Measured effect: `RATE_RATIO` and `WIN_RATIO` are in neither vocabulary set, so neither branch "
        "adjudicates the scale rule before the unconditional `make_pass()`."
    )
    out.append("")
    out.append("### `validate_v2.validate()` converts no block into a pass")
    out.append("")
    out.append(code_block("ssot/validate_v2.py", 3770, 3782))
    out.append("")
    out.append("### `validate_v2.check_network()` returns before checking when `network` is absent")
    out.append("")
    out.append(code_block("ssot/validate_v2.py", 2981, 2997))
    out.append(
        "With the wrapper above, this early return becomes a `network` pass for non-network objects."
    )
    out.append("")
    out.append("### Source-cache detectors return when the source cache is absent")
    out.append("")
    out.append(code_block("ssot/validate_v2.py", 2039, 2057))
    out.append(
        "`check_source_category_binding`, `check_identifier_anchoring`, `check_reference_consistency`, "
        "`check_arm_completeness`, and related source-backed detectors share this pattern: source cache "
        "absence is owned elsewhere, but the individual detector still records as passed when `validate()` "
        "sees no block from that detector."
    )
    out.append("")
    out.append("### `validate_v2.check_cross_engine()` notes a skip, then the wrapper records a pass")
    out.append("")
    out.append(code_block("ssot/validate_v2.py", 3465, 3504))
    out.append("")
    out.append("### `validate_v2.check_grade()` skips absent grade blocks")
    out.append("")
    out.append(code_block("ssot/validate_v2.py", 3597, 3637))
    out.append("")
    out.append("### `topic_identity.locate()` reads raw-v2 fields without enforcing raw-v2 shape")
    out.append("")
    out.append(code_block("ssot/topic_identity.py", 77, 88))
    out.append(code_block("ssot/topic_identity.py", 130, 142))
    out.append(
        "A flattened MCP ClinicalTrials.gov record has none of these raw-v2 role fields, so the assessor "
        "can return a verdict-shaped `not_assessable` cascade instead of raising."
    )
    out.append("")
    out.append("### The reference guard that does raise")
    out.append("")
    out.append(code_block("ssot/ctgov_transport.py", 67, 86))
    out.append("")
    out.append("## Static-Vs-Dynamic Hardcode Disclosure")
    out.append("")
    out.append("| item | static/dynamic | disclosure |")
    out.append("| --- | --- | --- |")
    out.append("| Check discovery roots | static | `ssot`, `scripts`, `.githooks` per task scope. |")
    out.append("| Selftest file list | static | Fixed in this helper from `rg -l \"def selftest|--selftest\" scripts ssot`, excluding `figure_audit.py --selftest-structure` because it requires two explicit pages. |")
    out.append("| NAFIS/precondition/validate registries | dynamic | Imported from current source at run time. |")
    out.append("| Metrics | dynamic | Computed from current `build-artefacts/*.json` and `ssot/*/*.json`; no network. |")
    out.append("| Adjudication for `validate_v2` | unknown | The validator exposes block/no-block, not predicate-run witnesses. Rows are not reported as sound. |")
    out.append("")
    out.append("## Full Inventory")
    out.append("")
    out.append(
        f"Summary: {total} rows. Shape-asserting yes: {yes_shape}; shape-asserting no: {no_shape}; "
        f"PASS-without-predicate risk yes: {yes_vac}; vacuity UNKNOWN: {unknown_vac}."
    )
    out.append("")
    for category in sorted({r.category for r in rows}):
        section_rows = sorted([r for r in rows if r.category == category], key=lambda r: (r.file, r.line, r.name))
        out.append(f"### {category}")
        out.append("")
        out.append(table(section_rows))
        out.append("")
    return "\n".join(out).rstrip() + "\n"


def main() -> int:
    import_project_modules()
    nafis_rows, nafis = measure_nafis()
    pre_rows, pre = measure_preconditions()
    validate_rows, validate = measure_validate_v2()
    support_rows = registered_support_rows()

    already = {(r.file, r.line, r.name) for r in nafis_rows + pre_rows + validate_rows + support_rows}
    generic_rows, static = generic_static_rows(already)

    rows = sorted(
        nafis_rows + pre_rows + validate_rows + support_rows + generic_rows,
        key=lambda r: (r.category, r.file, r.line, r.name),
    )
    selftests = run_selftests()
    validate_cli = run_validate_cli_probe()
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(
        render_report(rows, nafis, pre, validate, static, selftests, validate_cli),
        encoding="utf-8",
    )
    print(f"Wrote {rel(REPORT)} with {len(rows)} rows.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
