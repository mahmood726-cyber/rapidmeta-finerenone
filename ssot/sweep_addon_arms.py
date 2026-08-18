"""Sweep SSOT arm labels for suspected add-on/background designs.

This is object-side only. It reads each ssot/<topic>/<topic>.json object,
inspects inputs.trials[].arms[], and writes a reproducible markdown report.
It deliberately does not modify any SSOT object.
"""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any


GUARD_WORDS = frozenset({"placebo", "matching", "matched", "dummy", "sham"})

# These words describe study structure, route, dose, formulation, population, or
# ordinary care. They are not treated as shared drug-like components.
STOP_WORDS = frozenset(
    """
    a active acute add add-on addon adjunct adult adults after alone an and arm arms
    as background baseline before best between bid blind blinded by cancer capsule capsules
    care change chronic cohort combination combinations comparator composite control
    controlled controls conventional daily day days deferred disease dose doses double
    drug early endpoint every experimental failure five for four from g group groups
    heart high higher hospitalisation hospitalization inactive in infection infusion
    injection investigational intravenous iu iv kg l late low lower matched matching
    mcg medical mg ml monotherapy month monthly months m2 od of on once ophthalmic
    optimal optimized oral orally participant participants partner partners patient
    patients per percent phase pla placebo placebo-controlled plus prevention product
    prophylaxis qd qday qid randomized randomization randomisation randomised ratio
    rate recommended regimen regimens sc second seasonal seven sham six solution
    solutions soc sq standard standard-of-care started stent stents study subcutaneous
    supportive synergy tablet tablets target targets ten the therapy therapy-treated
    third three tid to treated treatment treatments trial trials twice two ug unit
    units usual vaccine vaccines versus visit visits vs week weekly weeks with within
    year years
    """.split()
)

GENERIC_PHRASES = frozenset(
    {
        "background therapy",
        "best supportive care",
        "conventional treatment",
        "heart failure",
        "medical therapy",
        "ophthalmic solution",
        "seasonal chemoprevention",
        "standard care",
        "standard of care",
        "synergy stent",
        "target",
        "trial",
        "usual care",
    }
)

UNITS = (
    "mg|mcg|ug|g|kg|ml|l|iu|units|unit|mmol|mol|percent|%|m2|"
    "mcg/kg|mg/kg|mg/m2|iu/kg"
)
SEPARATOR_RE = re.compile(
    r"\s*(?:/|\+|,|;|&|\bplus\b|\band\b|\bwith\b)\s*", re.IGNORECASE
)
PAREN_RE = re.compile(r"\(([^()]*)\)")
DOSE_RE = re.compile(
    rf"(?<![a-z0-9-])\d+(?:\.\d+)?\s*(?:{UNITS})\b", re.IGNORECASE
)
NUM_RE = re.compile(r"(?<![a-z0-9-])\d+(?:\.\d+)?(?![a-z0-9-])")
FREQ_RE = re.compile(
    r"\b(?:once|twice|three times|daily|weekly|monthly|bid|tid|qid|qd|od|"
    r"q\d+h|q\d+w|every\s+\d+\s+(?:day|days|week|weeks|month|months))\b",
    re.IGNORECASE,
)

KNOWN_SGLT2_HF_INCLUDED_NCTS = frozenset(
    {"NCT03036124", "NCT03057977", "NCT03057951", "NCT03619213"}
)


@dataclass(frozen=True)
class ArmEvidence:
    role: str
    label: str
    tokens: tuple[str, ...]
    guarded_tokens: tuple[str, ...]
    unguarded_tokens: tuple[str, ...]


@dataclass(frozen=True)
class TrialResult:
    topic: str
    path: Path
    trial_id: str
    nct: str
    name: str
    status: str
    reason: str
    shared_tokens: tuple[str, ...]
    unguarded_shared_tokens: tuple[str, ...]
    guard_removed_tokens: tuple[str, ...]
    arms: tuple[ArmEvidence, ...]


def ascii_lower(value: Any) -> str:
    text = str(value or "")
    return (
        unicodedata.normalize("NFKD", text)
        .encode("ascii", "ignore")
        .decode("ascii")
        .lower()
    )


def parenthetical_replacement(match: re.Match[str]) -> str:
    content = match.group(1).strip()
    if not content:
        return " "
    letters = [ch for ch in content if ch.isalpha()]
    mostly_upper = bool(letters) and (
        sum(1 for ch in letters if ch.isupper()) / len(letters) > 0.8
    )
    has_separator = bool(SEPARATOR_RE.search(content))
    if mostly_upper and not has_separator:
        return " "
    return f" , {content} , "


def label_pieces(label: str) -> list[str]:
    expanded = PAREN_RE.sub(parenthetical_replacement, str(label or ""))
    return [piece for piece in SEPARATOR_RE.split(expanded) if piece.strip()]


def raw_has_guard(piece: str) -> bool:
    raw = ascii_lower(piece)
    return any(re.search(rf"\b{re.escape(word)}\b", raw) for word in GUARD_WORDS)


def clean_words(piece: str) -> list[str]:
    text = ascii_lower(piece)
    text = DOSE_RE.sub(" ", text)
    text = FREQ_RE.sub(" ", text)
    text = NUM_RE.sub(" ", text)
    text = re.sub(r"\b(?:mg|mcg|ug|g|kg|ml|iu|units?|percent|per)\b", " ", text)
    text = re.sub(r"[^a-z0-9-]+", " ", text)

    words: list[str] = []
    for word in text.split():
        word = word.strip("-")
        if not word or len(word) <= 1 or word in STOP_WORDS:
            continue
        words.append(word)
    return words


def component_tokens(piece: str) -> set[str]:
    words = clean_words(piece)
    if not words:
        return set()

    tokens: set[str] = set()
    phrase = " ".join(words)
    if phrase not in GENERIC_PHRASES and len(words) <= 4:
        tokens.add(phrase)

    for word in words:
        if len(word) >= 4 and word not in GENERIC_PHRASES:
            tokens.add(word)
    return tokens


def label_tokens(label: str, *, apply_guard: bool) -> tuple[set[str], set[str]]:
    present: set[str] = set()
    guarded: set[str] = set()
    for piece in label_pieces(label):
        tokens = component_tokens(piece)
        if not tokens:
            continue
        if apply_guard and raw_has_guard(piece):
            guarded.update(tokens)
        else:
            present.update(tokens)
    return present, guarded


def object_paths(ssot_root: Path) -> list[Path]:
    paths: list[Path] = []
    for child in sorted(ssot_root.iterdir(), key=lambda p: p.name.lower()):
        if not child.is_dir():
            continue
        path = child / f"{child.name}.json"
        if path.exists():
            paths.append(path)
    return paths


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8-sig") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} did not contain a JSON object")
    return data


def trial_identifier(trial: dict[str, Any]) -> str:
    for key in ("nct", "id", "name"):
        value = str(trial.get(key) or "").strip()
        if value:
            return value
    return "UNKNOWN_TRIAL"


def assess_trial(topic: str, path: Path, trial: dict[str, Any]) -> TrialResult:
    trial_id = trial_identifier(trial)
    nct = str(trial.get("nct") or "").strip()
    name = str(trial.get("name") or "").strip()
    arms_raw = trial.get("arms")

    if not isinstance(arms_raw, list) or not arms_raw:
        return TrialResult(
            topic=topic,
            path=path,
            trial_id=trial_id,
            nct=nct,
            name=name,
            status="NOT_ASSESSABLE",
            reason="no inputs.trials[].arms array with arm labels",
            shared_tokens=(),
            unguarded_shared_tokens=(),
            guard_removed_tokens=(),
            arms=(),
        )

    arm_views: list[ArmEvidence] = []
    treatment_tokens: set[str] = set()
    control_tokens: set[str] = set()
    treatment_unguarded: set[str] = set()
    control_unguarded: set[str] = set()
    treatment_labels = 0
    control_labels = 0
    missing_role_or_label = False

    for arm in arms_raw:
        if not isinstance(arm, dict):
            missing_role_or_label = True
            continue
        role = str(arm.get("role") or "").strip().lower()
        label = str(arm.get("label") or "").strip()
        if role not in {"treatment", "control"}:
            missing_role_or_label = True
            continue
        if not label:
            missing_role_or_label = True
            continue

        guarded_tokens, phrase_guarded = label_tokens(label, apply_guard=True)
        unguarded_tokens, _ = label_tokens(label, apply_guard=False)
        arm_views.append(
            ArmEvidence(
                role=role,
                label=label,
                tokens=tuple(sorted(guarded_tokens)),
                guarded_tokens=tuple(sorted(phrase_guarded)),
                unguarded_tokens=tuple(sorted(unguarded_tokens)),
            )
        )
        if role == "treatment":
            treatment_labels += 1
            treatment_tokens.update(guarded_tokens)
            treatment_unguarded.update(unguarded_tokens)
        else:
            control_labels += 1
            control_tokens.update(guarded_tokens)
            control_unguarded.update(unguarded_tokens)

    if missing_role_or_label:
        return TrialResult(
            topic=topic,
            path=path,
            trial_id=trial_id,
            nct=nct,
            name=name,
            status="NOT_ASSESSABLE",
            reason="at least one arm lacks a treatment/control role or label",
            shared_tokens=(),
            unguarded_shared_tokens=(),
            guard_removed_tokens=(),
            arms=tuple(arm_views),
        )
    if treatment_labels == 0 or control_labels == 0:
        return TrialResult(
            topic=topic,
            path=path,
            trial_id=trial_id,
            nct=nct,
            name=name,
            status="NOT_ASSESSABLE",
            reason="missing at least one labelled treatment-role or control-role arm",
            shared_tokens=(),
            unguarded_shared_tokens=(),
            guard_removed_tokens=(),
            arms=tuple(arm_views),
        )

    shared = treatment_tokens & control_tokens
    unguarded_shared = treatment_unguarded & control_unguarded
    guard_removed = unguarded_shared - shared
    status = "SUSPECTED_ADDON" if shared else "NO_ADDON_FOUND"
    reason = (
        "drug-like token appears in both treatment-role and control-role labels"
        if shared
        else "no shared drug-like treatment/control arm-label token after guard"
    )

    return TrialResult(
        topic=topic,
        path=path,
        trial_id=trial_id,
        nct=nct,
        name=name,
        status=status,
        reason=reason,
        shared_tokens=tuple(sorted(shared)),
        unguarded_shared_tokens=tuple(sorted(unguarded_shared)),
        guard_removed_tokens=tuple(sorted(guard_removed)),
        arms=tuple(arm_views),
    )


def sweep(ssot_root: Path) -> tuple[list[TrialResult], list[str]]:
    results: list[TrialResult] = []
    objects_without_trials: list[str] = []

    for path in object_paths(ssot_root):
        topic = path.parent.name
        data = load_json(path)
        trials = (data.get("inputs") or {}).get("trials")
        if not isinstance(trials, list) or not trials:
            objects_without_trials.append(topic)
            continue
        for trial in trials:
            if not isinstance(trial, dict):
                results.append(
                    TrialResult(
                        topic=topic,
                        path=path,
                        trial_id="UNKNOWN_TRIAL",
                        nct="",
                        name="",
                        status="NOT_ASSESSABLE",
                        reason="trial entry is not a JSON object",
                        shared_tokens=(),
                        unguarded_shared_tokens=(),
                        guard_removed_tokens=(),
                        arms=(),
                    )
                )
                continue
            results.append(assess_trial(topic, path, trial))

    return results, objects_without_trials


def sglt2_known_answer(results: list[TrialResult]) -> tuple[list[TrialResult], set[str]]:
    found = [
        result
        for result in results
        if result.topic == "sglt2-hf" and result.nct in KNOWN_SGLT2_HF_INCLUDED_NCTS
    ]
    found_ncts = {result.nct for result in found}
    missing = set(KNOWN_SGLT2_HF_INCLUDED_NCTS - found_ncts)
    bad = [result for result in found if result.shared_tokens]
    return bad, missing


def md_cell(value: Any) -> str:
    text = str(value)
    text = text.replace("\r", " ").replace("\n", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text.replace("|", "\\|")


def trial_label(result: TrialResult) -> str:
    parts = []
    if result.nct:
        parts.append(result.nct)
    if result.name:
        parts.append(result.name)
    if not parts:
        parts.append(result.trial_id)
    return " ".join(parts)


def quoted_arms(result: TrialResult) -> str:
    return "<br>".join(
        f'{md_cell(arm.role)} "{md_cell(arm.label)}"' for arm in result.arms
    )


def compact_suspect_cell(results: list[TrialResult]) -> str:
    entries = []
    for result in results:
        token_text = ", ".join(result.shared_tokens)
        entries.append(f"{trial_label(result)}: {token_text}; {quoted_arms(result)}")
    return "<br>".join(entries)


def topic_summaries(
    results: list[TrialResult], objects_without_trials: list[str]
) -> dict[str, dict[str, Any]]:
    summaries: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "n_trials": 0,
            "n_assessable": 0,
            "n_not_assessable": 0,
            "n_suspected": 0,
            "shared_tokens": Counter(),
            "statuses": Counter(),
        }
    )

    for result in results:
        summary = summaries[result.topic]
        summary["n_trials"] += 1
        summary["statuses"][result.status] += 1
        if result.status == "NOT_ASSESSABLE":
            summary["n_not_assessable"] += 1
        else:
            summary["n_assessable"] += 1
        if result.status == "SUSPECTED_ADDON":
            summary["n_suspected"] += 1
            summary["shared_tokens"].update(result.shared_tokens)

    for topic in objects_without_trials:
        _ = summaries[topic]

    return summaries


def render_report(
    *,
    results: list[TrialResult],
    objects_without_trials: list[str],
    ssot_root: Path,
    output_path: Path,
) -> str:
    summaries = topic_summaries(results, objects_without_trials)
    suspects = [r for r in results if r.status == "SUSPECTED_ADDON"]
    not_assessable = [r for r in results if r.status == "NOT_ASSESSABLE"]
    guard_removed_trials = [r for r in results if r.guard_removed_tokens]
    guard_prevented_trials = [
        r for r in guard_removed_trials if not r.shared_tokens and r.unguarded_shared_tokens
    ]
    guard_removed_token_total = sum(len(r.guard_removed_tokens) for r in guard_removed_trials)
    bad_known, missing_known = sglt2_known_answer(results)
    try:
        output_display = output_path.relative_to(ssot_root.parent).as_posix()
    except ValueError:
        output_display = output_path.name

    ranked_topics = sorted(
        (
            (topic, summary)
            for topic, summary in summaries.items()
            if summary["n_suspected"] > 0
        ),
        key=lambda item: (-item[1]["n_suspected"], item[0]),
    )
    suspect_by_topic: dict[str, list[TrialResult]] = defaultdict(list)
    for result in suspects:
        suspect_by_topic[result.topic].append(result)

    lines: list[str] = []
    lines.append("# Add-on Arm Sweep")
    lines.append("")
    lines.append("Date: 2026-08-19")
    lines.append("")
    lines.append(
        "Scope: object-side only; no network; read `inputs.trials[].arms[].label` "
        "and `inputs.trials[].arms[].role` from `ssot/<topic>/<topic>.json`."
    )
    lines.append("")
    lines.append("## Method")
    lines.append("")
    lines.append(
        "- A trial is `SUSPECTED_ADDON` when at least one retained intervention "
        "component appears in both a treatment-role arm label and a control-role "
        "arm label."
    )
    lines.append(
        "- Labels are split on `/`, `+`, `,`, `plus`, `and`, and `with`; doses, "
        "units, route/frequency words, and generic study/formulation words are "
        "removed."
    )
    lines.append(
        "- Matching-placebo guard: components containing `placebo`, `matching`, "
        "`matched`, `dummy`, or `sham` do not count as containing the named active "
        "drug. This prevents `Placebo matching X` from becoming evidence that X "
        "is in the control arm."
    )
    lines.append(
        "- A trial with no usable labelled treatment and control arms is "
        "`NOT_ASSESSABLE`, not a clean negative."
    )
    lines.append("")
    lines.append("## Known-answer check")
    lines.append("")
    if missing_known:
        lines.append(
            "FAIL: `sglt2-hf` is missing expected included NCTs from the check: "
            + ", ".join(sorted(missing_known))
            + "."
        )
    elif bad_known:
        lines.append(
            "FAIL: the `sglt2-hf` included-trial check flagged: "
            + ", ".join(trial_label(result) for result in bad_known)
            + "."
        )
    else:
        lines.append(
            "PASS: the `sglt2-hf` included trials NCT03036124 DAPA-HF, "
            "NCT03057977 EMPEROR-Reduced, NCT03057951 EMPEROR-Preserved, and "
            "NCT03619213 DELIVER returned zero suspected add-on hits."
        )
    lines.append("")
    for result in sorted(
        [r for r in results if r.topic == "sglt2-hf"], key=lambda r: r.nct or r.trial_id
    ):
        if result.nct in KNOWN_SGLT2_HF_INCLUDED_NCTS:
            lines.append(
                f"- {trial_label(result)}: {result.status}; {quoted_arms(result)}"
            )
    lines.append("")
    lines.append("## Corpus totals")
    lines.append("")
    lines.append(f"- Objects read: {len(object_paths(ssot_root))}")
    lines.append(f"- Objects without included trials: {len(objects_without_trials)}")
    lines.append(f"- Included trial records read: {len(results)}")
    lines.append(f"- Assessable trial records: {len(results) - len(not_assessable)}")
    lines.append(f"- `NOT_ASSESSABLE` trial records: {len(not_assessable)}")
    lines.append(f"- Suspected add-on/shared-token trial records: {len(suspects)}")
    lines.append(f"- Topics with at least one suspected trial: {len(ranked_topics)}")
    lines.append(
        "- Matching-placebo guard prevented trial-level candidates: "
        f"{len(guard_prevented_trials)}"
    )
    lines.append(
        "- Matching-placebo guard removed shared-token matches: "
        f"{guard_removed_token_total}"
    )
    lines.append("")
    lines.append("## Ranked suspected topics")
    lines.append("")
    if ranked_topics:
        lines.append(
            "| topic | n trials | n not assessable | n suspected add-on | "
            "shared token(s) | arm labels |"
        )
        lines.append("|---|---:|---:|---:|---|---|")
        for topic, summary in ranked_topics:
            topic_results = sorted(
                suspect_by_topic[topic], key=lambda r: (r.nct or r.trial_id, r.name)
            )
            shared = ", ".join(sorted(summary["shared_tokens"]))
            lines.append(
                "| "
                + " | ".join(
                    [
                        md_cell(topic),
                        str(summary["n_trials"]),
                        str(summary["n_not_assessable"]),
                        str(summary["n_suspected"]),
                        md_cell(shared),
                        md_cell(compact_suspect_cell(topic_results)),
                    ]
                )
                + " |"
            )
    else:
        lines.append("No assessable included trial had a shared treatment/control token.")
    lines.append("")
    lines.append("## Suspected-trial details")
    lines.append("")
    if suspects:
        for topic, _summary in ranked_topics:
            lines.append(f"### {topic}")
            lines.append("")
            for result in sorted(
                suspect_by_topic[topic], key=lambda r: (r.nct or r.trial_id, r.name)
            ):
                lines.append(f"- {trial_label(result)}")
                lines.append(f"  - shared token(s): {', '.join(result.shared_tokens)}")
                lines.append(f"  - arm labels: {quoted_arms(result)}")
            lines.append("")
    else:
        lines.append("None.")
        lines.append("")
    lines.append("## arni-hfref callout")
    lines.append("")
    arni_results = [r for r in results if r.topic == "arni-hfref"]
    arni_suspects = [r for r in arni_results if r.status == "SUSPECTED_ADDON"]
    lines.append(
        "`arni-hfref` is the flagship active-comparator programme "
        "(sacubitril/valsartan against enalapril, on background therapy)."
    )
    if arni_suspects:
        lines.append(
            f"It trips this label-only shared-token test in {len(arni_suspects)} "
            "included trial(s): "
            + ", ".join(trial_label(result) for result in arni_suspects)
            + "."
        )
    else:
        lines.append(
            "It does not trip this label-only shared-token test in any included "
            "trial. The explicit arm labels name sacubitril/valsartan in the "
            "treatment arms and enalapril in the control arms; background therapy "
            "is not named as a shared arm-label component."
        )
    lines.append("")
    for result in sorted(arni_results, key=lambda r: (r.nct or r.trial_id, r.name)):
        lines.append(f"- {trial_label(result)}: {result.status}; {quoted_arms(result)}")
    lines.append("")
    lines.append("## Matching-placebo guard removals")
    lines.append("")
    lines.append(
        "The guard removal count is a finding: without it, matching-placebo labels "
        "would create false shared-token candidates."
    )
    lines.append("")
    if guard_removed_trials:
        lines.append(
            "| topic | trial | removed token(s) | remaining suspected token(s) | arm labels |"
        )
        lines.append("|---|---|---|---|---|")
        for result in sorted(
            guard_removed_trials, key=lambda r: (r.topic, r.nct or r.trial_id, r.name)
        ):
            remaining = ", ".join(result.shared_tokens) if result.shared_tokens else "none"
            lines.append(
                "| "
                + " | ".join(
                    [
                        md_cell(result.topic),
                        md_cell(trial_label(result)),
                        md_cell(", ".join(result.guard_removed_tokens)),
                        md_cell(remaining),
                        md_cell(quoted_arms(result)),
                    ]
                )
                + " |"
            )
    else:
        lines.append("No shared-token candidates were removed by the guard.")
    lines.append("")
    lines.append("## NOT_ASSESSABLE topics")
    lines.append("")
    lines.append(
        "`NOT_ASSESSABLE` means the included trial record lacks enough arm-label "
        "structure for this test. These rows are not clean negatives."
    )
    lines.append("")
    na_topics = sorted(
        (
            (topic, summary)
            for topic, summary in summaries.items()
            if summary["n_not_assessable"] > 0
        ),
        key=lambda item: (-item[1]["n_not_assessable"], item[0]),
    )
    if na_topics:
        lines.append("| topic | n trials | n not assessable | reason counts |")
        lines.append("|---|---:|---:|---|")
        reason_counts: dict[str, Counter[str]] = defaultdict(Counter)
        for result in not_assessable:
            reason_counts[result.topic][result.reason] += 1
        for topic, summary in na_topics:
            reasons = "; ".join(
                f"{reason}: {count}"
                for reason, count in sorted(reason_counts[topic].items())
            )
            lines.append(
                "| "
                + " | ".join(
                    [
                        md_cell(topic),
                        str(summary["n_trials"]),
                        str(summary["n_not_assessable"]),
                        md_cell(reasons),
                    ]
                )
                + " |"
            )
    else:
        lines.append("None.")
    lines.append("")
    lines.append("## Full per-topic summary")
    lines.append("")
    lines.append(
        "| topic | n trials | n assessable | n not assessable | n suspected add-on | status counts |"
    )
    lines.append("|---|---:|---:|---:|---:|---|")
    for topic in sorted(summaries):
        summary = summaries[topic]
        statuses = "; ".join(
            f"{status}: {count}" for status, count in sorted(summary["statuses"].items())
        )
        if not statuses:
            statuses = "NO_INCLUDED_TRIALS: 1 object"
        lines.append(
            "| "
            + " | ".join(
                [
                    md_cell(topic),
                    str(summary["n_trials"]),
                    str(summary["n_assessable"]),
                    str(summary["n_not_assessable"]),
                    str(summary["n_suspected"]),
                    md_cell(statuses),
                ]
            )
            + " |"
        )
    lines.append("")
    lines.append("## Could not determine")
    lines.append("")
    lines.append(
        f"{len(not_assessable)} included trial record(s) were not assessable because "
        "they lacked usable arm labels or roles. They are not counted as no add-on "
        "found."
    )
    lines.append(
        "This sweep can identify shared treatment/control label components, but it "
        "does not prove clinical add-on status, topic-drug identity, or whether a "
        "shared molecule is part of a dose, timing, formulation, or background "
        "contrast. The arm labels quoted above are the evidence for each suspect."
    )
    lines.append("")
    lines.append("## Hardcode disclosure")
    lines.append("")
    lines.append("| Item | Static or dynamic | Disclosure |")
    lines.append("|---|---|---|")
    lines.append(
        "| SSOT object data | dynamic | Read live from `ssot/<topic>/<topic>.json`; "
        "no trial counts are hardcoded. |"
    )
    lines.append(
        "| Matching-placebo guard and stop words | static | Encoded in "
        "`ssot/sweep_addon_arms.py` to make the detector deterministic and "
        "reviewable. |"
    )
    lines.append(
        "| SGLT2 known-answer check | static | The four expected `sglt2-hf` included "
        "NCT IDs are fixed as a fail-closed regression test. |"
    )
    lines.append("")
    lines.append(
        f"Generated by `python -W error ssot/sweep_addon_arms.py --output "
        f"{output_display}`."
    )
    lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    default_repo = Path(__file__).resolve().parents[1]
    parser.add_argument(
        "--ssot-root",
        type=Path,
        default=default_repo / "ssot",
        help="Path to the ssot directory.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=default_repo / "evidence" / "2026-08-19-corpus" / "addon_arms.md",
        help="Markdown report path.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    ssot_root = args.ssot_root.resolve()
    output_path = args.output.resolve()
    if not ssot_root.exists():
        raise FileNotFoundError(f"SSOT root does not exist: {ssot_root}")

    results, objects_without_trials = sweep(ssot_root)
    bad_known, missing_known = sglt2_known_answer(results)
    if missing_known or bad_known:
        problems = []
        if missing_known:
            problems.append("missing " + ", ".join(sorted(missing_known)))
        if bad_known:
            problems.append(
                "flagged "
                + ", ".join(f"{r.nct} ({', '.join(r.shared_tokens)})" for r in bad_known)
            )
        raise SystemExit("sglt2-hf known-answer check failed: " + "; ".join(problems))

    report = render_report(
        results=results,
        objects_without_trials=objects_without_trials,
        ssot_root=ssot_root,
        output_path=output_path,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8", newline="\n")

    suspects = sum(1 for result in results if result.status == "SUSPECTED_ADDON")
    not_assessable = sum(1 for result in results if result.status == "NOT_ASSESSABLE")
    guard_removed = sum(len(result.guard_removed_tokens) for result in results)
    print(f"objects_read={len(object_paths(ssot_root))}")
    print(f"trials_read={len(results)}")
    print(f"suspected_addon_trials={suspects}")
    print(f"not_assessable_trials={not_assessable}")
    print(f"guard_removed_token_matches={guard_removed}")
    print(f"wrote={output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
