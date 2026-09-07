import sys,os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _harness as H
import re


EVENT_PATTERNS = (
    ("death", r"\b(?:death|deaths|mortality)\b"),
    ("hospitalisation", r"\b(?:hospitali[sz]ation|hospitali[sz]ations|hospital admission|hospital admissions|readmission|readmissions)\b"),
    ("stroke", r"\bstrokes?\b"),
    ("mi", r"\b(?:mi|mis|myocardial infarction|myocardial infarctions)\b"),
    ("embolism", r"\b(?:embolism|embolisms|thromboembolism|thromboembolisms|pulmonary embolism|pe|vte|dvt)\b"),
    ("revascularisation", r"\b(?:revasculari[sz]ation|revasculari[sz]ations|pci|cabg)\b"),
    ("bleeding", r"\b(?:bleeding|bleed|bleeds|haemorrhage|haemorrhages|hemorrhage|hemorrhages)\b"),
    ("progression", r"\b(?:progression|relapse|recurrence|exacerbation)\b"),
    ("amputation", r"\bamputations?\b"),
    ("transplant", r"\btransplants?\b"),
)
EVENT_RE = [(name, re.compile(pattern, re.I)) for name, pattern in EVENT_PATTERNS]
COMPOSITE_RE = re.compile(r"\bcomposite\b", re.I)
CONNECTOR_RE = re.compile(r"\b(?:and|or)\b", re.I)
TEXT_FIELDS = ("title", "name", "measure", "estimand")
ESTIMAND_TEXT_FIELDS = ("title", "name", "measure", "label", "description", "definition", "endpoint", "outcome")
COMPONENT_KEYS = ("components", "component_list", "component_outcomes", "component_results",
                  "component_analyses", "decomposition", "decomposed", "by_component")
NAME_KEYS = ("name", "title", "label", "component", "outcome", "endpoint", "event", "id")
META_KEYS = {
    "measure", "method", "model", "pooled", "summary", "overall", "effect", "estimate",
    "point", "ci", "ci_low", "ci_high", "p", "p_value", "q", "df", "i2", "tau2", "k",
    "n", "notes", "note", "source", "sources", "citation", "reference", "references",
}


def _control_contract_available():
    try:
        H._require_controls(
            "gate composite control probe",
            positive=("probe positive", True, True),
            negative=("probe negative", False, True),
            out=lambda _line: None,
        )
        return True
    except ImportError:
        return False
    except SystemExit:
        return True


def _install_local_control_contract_if_needed():
    if _control_contract_available():
        return

    def require_controls(name, positive, negative, out):
        p_desc, p_got, p_want = positive
        n_desc, n_got, n_want = negative
        out("control positive: %s got=%s want=%s" % (p_desc, p_got, p_want))
        out("control negative: %s got=%s want=%s" % (n_desc, n_got, n_want))
        if p_got != p_want or n_got != n_want:
            raise SystemExit("%s controls did not hold" % name)

    H._require_controls = require_controls


def _norm_text(value):
    text = str(value or "").replace("_", " ")
    text = re.sub(r"[\u2010-\u2015]", "-", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _norm_key(value):
    return re.sub(r"[^a-z0-9]+", "_", str(value or "").lower()).strip("_")


def _text_leaves(value, keys=ESTIMAND_TEXT_FIELDS):
    found = []
    if isinstance(value, str):
        text = _norm_text(value)
        if text:
            found.append(text)
    elif isinstance(value, dict):
        for key in keys:
            if key in value:
                found.extend(_text_leaves(value.get(key), keys))
    elif isinstance(value, list):
        for item in value:
            found.extend(_text_leaves(item, keys))
    return found


def _all_text_leaves(value):
    found = []
    if isinstance(value, str):
        text = _norm_text(value)
        if text:
            found.append(text)
    elif isinstance(value, dict):
        for child in value.values():
            found.extend(_all_text_leaves(child))
    elif isinstance(value, list):
        for item in value:
            found.extend(_all_text_leaves(item))
    return found


def _texts_for_key(value, wanted_key):
    found = []
    if isinstance(value, dict):
        for key, child in value.items():
            if key == wanted_key:
                found.extend(_all_text_leaves(child))
            if isinstance(child, (dict, list)):
                found.extend(_texts_for_key(child, wanted_key))
    elif isinstance(value, list):
        for item in value:
            found.extend(_texts_for_key(item, wanted_key))
    return found


def _append_texts(texts, field, value, seen):
    for text in _text_leaves(value):
        if text not in seen:
            seen.add(text)
            texts.append((field, text))


def _append_all_texts(texts, field, value, seen):
    for text in _all_text_leaves(value):
        if text not in seen:
            seen.add(text)
            texts.append((field, text))


def _per_trial_source_texts(outcome):
    texts = []
    per_trial = outcome.get("per_trial") if isinstance(outcome, dict) else None
    if not isinstance(per_trial, list):
        return texts
    for item in per_trial:
        if isinstance(item, dict) and "source" in item:
            texts.extend(_all_text_leaves(item.get("source")))
    return texts


def _rob_block_for_outcome(obj, outcome_id):
    if not isinstance(obj, dict):
        return None
    rob = obj.get("risk_of_bias")
    if not isinstance(rob, dict):
        return None
    by_outcome = rob.get("by_outcome")
    if isinstance(by_outcome, dict):
        return by_outcome.get(outcome_id)
    if isinstance(by_outcome, list):
        match = re.match(r"outcome_(\d+)$", str(outcome_id))
        if match:
            index = int(match.group(1))
            if 0 <= index < len(by_outcome):
                return by_outcome[index]
    return rob.get(outcome_id)


def _risk_of_bias_result_texts(outcome, obj=None, outcome_id=None):
    texts = []
    if isinstance(outcome, dict):
        texts.extend(_texts_for_key(outcome.get("risk_of_bias"), "result_assessed"))
    if outcome_id is not None:
        texts.extend(_texts_for_key(_rob_block_for_outcome(obj, outcome_id), "result_assessed"))
    return texts


def _by_outcome_count(obj):
    if not isinstance(obj, dict):
        return 0
    by_outcome = (obj.get("results") or {}).get("by_outcome")
    if isinstance(by_outcome, dict):
        return len(by_outcome)
    if isinstance(by_outcome, list):
        return len(by_outcome)
    return 0


def _object_question_applies(obj, outcome_id):
    count = _by_outcome_count(obj)
    norm = _norm_key(outcome_id)
    return count == 1 or norm == "primary" or norm.startswith("primary_") or norm.endswith("_primary")


def outcome_texts(outcome, obj=None, outcome_id=None):
    texts = []
    if not isinstance(outcome, dict):
        return texts
    seen = set()
    for field in TEXT_FIELDS:
        if field in outcome:
            _append_texts(texts, field, outcome.get(field), seen)
    for text in _per_trial_source_texts(outcome):
        if text not in seen:
            seen.add(text)
            texts.append(("per_trial.source", text))
    for text in _risk_of_bias_result_texts(outcome, obj, outcome_id):
        if text not in seen:
            seen.add(text)
            texts.append(("risk_of_bias.result_assessed", text))
    if isinstance(obj, dict) and "question" in obj and _object_question_applies(obj, outcome_id):
        _append_all_texts(texts, "object.question", obj.get("question"), seen)
    return texts


def _event_mentions(text):
    mentions = []
    for name, regex in EVENT_RE:
        for match in regex.finditer(text):
            mentions.append((name, match.start(), match.end(), match.group(0)))
    mentions.sort(key=lambda row: (row[1], row[2]))
    return mentions


def _joined_event_signal(text, mentions):
    if len({m[0] for m in mentions}) < 2:
        return None
    for left in mentions:
        for right in mentions:
            if left[0] == right[0] or left[2] > right[1]:
                continue
            if CONNECTOR_RE.search(text, left[2], right[1]):
                terms = sorted({left[0], right[0]})
                return "and/or connector joins recognised event terms: %s" % ", ".join(terms)
    return None


def composite_signal(outcome, obj=None, outcome_id=None):
    for field, text in outcome_texts(outcome, obj, outcome_id):
        mentions = _event_mentions(text)
        if COMPOSITE_RE.search(text):
            terms = sorted({m[0] for m in mentions})
            if terms:
                return True, "%s says composite and names event term(s): %s" % (field, ", ".join(terms))
            return True, "%s contains the explicit word composite" % field
        joined = _joined_event_signal(text, mentions)
        if joined:
            return True, "%s has %s" % (field, joined)
    return False, "no explicit composite word or and/or-joined pair of recognised event terms"


def _component_item_has_name(item):
    if isinstance(item, str):
        return bool(_norm_text(item))
    if not isinstance(item, dict):
        return False
    for key in NAME_KEYS:
        value = item.get(key)
        if isinstance(value, str) and _norm_text(value):
            return True
    return False


def _component_count(value):
    if isinstance(value, list):
        return sum(1 for item in value if _component_item_has_name(item))
    if not isinstance(value, dict):
        return 0

    for key in COMPONENT_KEYS:
        if key in value:
            count = _component_count(value.get(key))
            if count >= 2:
                return count

    child_counts = [_component_count(v) for v in value.values() if isinstance(v, (dict, list))]
    best_child = max(child_counts or [0])
    if best_child >= 2:
        return best_child

    candidate_keys = []
    for key, child in value.items():
        norm = _norm_key(key)
        if norm in META_KEYS:
            continue
        if isinstance(child, (dict, list)) and norm:
            candidate_keys.append(key)
    if len(candidate_keys) >= 2:
        return len(candidate_keys)
    return best_child


def _candidate_component_blocks(node):
    if isinstance(node, dict):
        for key, value in node.items():
            norm = _norm_key(key)
            if norm in COMPONENT_KEYS:
                yield value
            if isinstance(value, (dict, list)):
                for block in _candidate_component_blocks(value):
                    yield block
    elif isinstance(node, list):
        for item in node:
            for block in _candidate_component_blocks(item):
                yield block


def has_components(outcome):
    if not isinstance(outcome, dict):
        return False
    if _component_count(outcome.get("components")) >= 2:
        return True
    estimand = outcome.get("estimand")
    if isinstance(estimand, dict) and _component_count(estimand.get("components")) >= 2:
        return True
    for block in _candidate_component_blocks(outcome):
        if _component_count(block) >= 2:
            return True
    return False


def _by_outcome_entries(obj):
    by_outcome = (obj.get("results") or {}).get("by_outcome")
    if isinstance(by_outcome, dict):
        for outcome_id, outcome in by_outcome.items():
            yield str(outcome_id), outcome
    elif isinstance(by_outcome, list):
        for index, outcome in enumerate(by_outcome):
            outcome_id = "outcome_%d" % index
            if isinstance(outcome, dict):
                outcome_id = str(outcome.get("id") or outcome.get("name") or outcome_id)
            yield outcome_id, outcome


def scan_objects(objects):
    findings = []
    kinds = {
        "object with no results.by_outcome mapping": 0,
        "outcome examined": 0,
        "outcome with no composite signal": 0,
        "composite outcome with components listed": 0,
        "composite outcome missing components": 0,
        "non-dict outcome skipped": 0,
    }
    for topic, obj in sorted(objects.items()):
        by_outcome = (obj.get("results") or {}).get("by_outcome") if isinstance(obj, dict) else None
        if not isinstance(by_outcome, (dict, list)):
            kinds["object with no results.by_outcome mapping"] += 1
            continue
        for outcome_id, outcome in _by_outcome_entries(obj):
            if not isinstance(outcome, dict):
                kinds["non-dict outcome skipped"] += 1
                continue
            kinds["outcome examined"] += 1
            is_composite, why = composite_signal(outcome, obj, outcome_id)
            if not is_composite:
                kinds["outcome with no composite signal"] += 1
                continue
            if has_components(outcome):
                kinds["composite outcome with components listed"] += 1
                continue
            kinds["composite outcome missing components"] += 1
            findings.append((topic, outcome_id, why,
                             " | ".join(t for _field, t in outcome_texts(outcome, obj, outcome_id))[:220]))
    return findings, kinds


def controls():
    positive = {
        "title": "cardiovascular death or hospitalisation for heart failure",
    }
    negative_with_components = {
        "title": "cardiovascular death or hospitalisation for heart failure",
        "components": ["cardiovascular death", "hospitalisation for heart failure"],
    }
    negative_single_event = {
        "title": "all-cause mortality",
    }
    pos_findings, _pos_kinds = scan_objects({"__positive__": {"results": {"by_outcome": {"primary": positive}}}})
    neg_findings, _neg_kinds = scan_objects({
        "__negative_components__": {"results": {"by_outcome": {"primary": negative_with_components}}},
        "__negative_single_event__": {"results": {"by_outcome": {"primary": negative_single_event}}},
    })
    return bool(pos_findings), not bool(neg_findings)


def main(argv):
    _install_local_control_contract_if_needed()
    gate = H.Gate("COMPOSITE LISTS COMPONENTS",
                  "a composite primary endpoint must list the component outcomes it combines")
    named = gate.expect_case("__synthetic_composite_without_components__",
                             "cardiovascular death or hospitalisation for heart failure with no components list")
    gate.requires_control()

    pos_fires, neg_silent = controls()
    if pos_fires:
        gate.saw(named)
    if not pos_fires:
        gate.broken("positive control did not fire: composite endpoint without components was missed")
    gate.control(2, 0 if neg_silent else 1,
                 [] if neg_silent else ["component-listed composite or single-event mortality was flagged"],
                 accuses=True)

    repo = H.repo_root()
    paths, path_kinds = H.topic_objects(repo)
    objects = {}
    unparseable = 0
    for path in paths:
        try:
            objects[H.topic_id(path)] = H.load(path)
        except Exception as exc:
            unparseable += 1
            gate.broken("unparseable topic object %s: %s" % (path, exc))

    findings, scan_kinds = scan_objects(objects)
    merged_kinds = dict(path_kinds)
    merged_kinds.update(scan_kinds)
    merged_kinds["unparseable topic object"] = unparseable
    gate.kinds(merged_kinds)
    gate.note("controls: positive %s, negative %s" % (pos_fires, neg_silent))
    gate.note("corpus finding count: %d" % len(findings))
    gate.note("detection rule: explicit word composite, or an and/or connector spanning at least two recognised clinical event categories in outcome title/name/measure/estimand text, per-trial source text, matching risk-of-bias result_assessed text, or the object question when the object has one outcome or the outcome id is primary-like")

    for topic, outcome_id, why, text in findings:
        gate.finding("%s/%s" % (topic, outcome_id),
                     "composite signal without a usable components/decomposition list (%s): %s"
                     % (why, text))

    visible_objects = len(objects)
    population_objects = len(paths)
    gate.coverage(
        visible_objects,
        population_objects,
        "unparseable topic objects or topic objects absent from ssot; detection is conservative: explicit 'composite' or and/or-joined recognised event terms in outcome title/name/measure/estimand text, per-trial source text, matching risk-of-bias result_assessed text, or the object question when the object has one outcome or the outcome id is primary-like, requiring outcome.components, estimand.components, or a decomposition block with at least two component names",
    )
    return gate.report(denominator="%d results.by_outcome outcome(s) in %d topic object(s)"
                       % (scan_kinds["outcome examined"], len(objects)))


if __name__=='__main__': sys.exit(main(sys.argv[1:]))
