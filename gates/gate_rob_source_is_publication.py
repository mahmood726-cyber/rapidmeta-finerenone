import sys,os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _harness as H


def main(argv):
    gate = H.Gate("ROB SOURCE IS PUBLICATION",
                  "RoB-2 per-trial domains must be judged from trial publications")
    gate.expect_case("synthetic-overall-only",
                     "a RoB entry with only an overall verdict and no domains must fire")
    gate.requires_control()

    pos_fires, neg_silent = controls()
    print("positive %s" % pos_fires)
    print("negative %s" % neg_silent)
    if pos_fires:
        gate.saw("synthetic-overall-only")
    gate.control(1, 0 if neg_silent else 1,
                 [] if neg_silent else ["complete five-domain PMID-sourced fixture"],
                 accuses=True)

    repo = H.repo_root()
    paths, kinds_pop = H.topic_objects(repo)
    objects = {}
    parse_failures = 0
    for p in paths:
        try:
            objects[H.topic_id(p)] = H.load(p)
        except Exception as exc:
            parse_failures += 1
            gate.broken("unparseable object %s: %s" % (p, exc))

    rows, counts = scan_objects(objects)
    for row in rows:
        gate.finding(row["key"], row["detail"],
                     numerator=len(rows),
                     denominator=counts["per-trial RoB entries reached"])

    merged = dict(kinds_pop)
    merged.update({
        "parseable topic objects": len(objects),
        "unparseable topic objects": parse_failures,
        "risk_of_bias.by_outcome maps reached": counts["risk_of_bias.by_outcome maps reached"],
        "outcome RoB maps reached": counts["outcome RoB maps reached"],
        "per-trial RoB entries reached": counts["per-trial RoB entries reached"],
        "  complete five-domain publication-sourced": counts["complete"],
        "  overall verdict with no domains": counts["overall-only"],
        "  no RoB-2 domain map": counts["no-domains"],
        "  missing one or more RoB-2 domains": counts["missing-domains"],
        "  one or more domain judgements missing": counts["missing-judgement"],
        "  one or more domains lack a publication source": counts["bad-source"],
    })
    gate.kinds(merged)
    gate.coverage(len(objects), len(paths),
                  "topic objects that were absent or unparseable; any RoB entries inside "
                  "them are not claimed clean by this run")
    print("corpus finding count %d" % len(rows))
    return gate.report(denominator="%d per-trial RoB entries in %d topic objects"
                                   % (counts["per-trial RoB entries reached"],
                                      len(objects)))


DOMAINS = (
    ("randomization", ("d1", "randomization", "randomisation")),
    ("deviations", ("d2", "deviation")),
    ("missing data", ("d3", "missing")),
    ("measurement", ("d4", "measurement")),
    ("selection of reported result", ("d5", "selection")),
)

JUDGEMENT_KEYS = ("judgement", "judgment", "rating", "verdict", "risk")
SOURCE_KEY_TOKENS = ("source", "basis", "pmid", "pmcid", "doi", "citation",
                     "reference", "publication", "primary report",
                     "published report", "trial report")
REGISTRY_TOKENS = ("clinicaltrials.gov", "ct.gov", "registry", "registration",
                   "registered", "design module", "resultssection", "api v2",
                   "eudract", "isrctn", "pactr", "drks", "chictr", "anzctr",
                   "trial registry")
JOURNAL_CUES = (" et al", "lancet", "jama", "nejm", "n engl j med", "bmj",
                "ann intern med", "new england journal", "journal", "trial report",
                "published report", "primary report")


def controls():
    positive = {"overall": "some concerns"}
    negative = {
        "overall": "LOW",
        "domains": {
            "D1_randomization": {
                "judgement": "LOW",
                "source": {"pmid": "12345678"},
            },
            "D2_deviations": {
                "judgement": "LOW",
                "source": {"pmid": "12345678"},
            },
            "D3_missing_data": {
                "judgement": "LOW",
                "source": {"pmid": "12345678"},
            },
            "D4_measurement": {
                "judgement": "LOW",
                "source": {"pmid": "12345678"},
            },
            "D5_selection_of_reported_result": {
                "judgement": "LOW",
                "source": {"pmid": "12345678"},
            },
        },
    }
    pos = analyse_entry("__control__", "primary", "NCT00000001", positive)
    neg = analyse_entry("__control__", "primary", "NCT00000002", negative)
    return (bool(pos), not bool(neg))


def scan_objects(objects):
    rows = []
    counts = {
        "risk_of_bias.by_outcome maps reached": 0,
        "outcome RoB maps reached": 0,
        "per-trial RoB entries reached": 0,
        "complete": 0,
        "overall-only": 0,
        "no-domains": 0,
        "missing-domains": 0,
        "missing-judgement": 0,
        "bad-source": 0,
    }
    for topic, obj in objects.items():
        if not isinstance(obj, dict):
            continue
        rob = obj.get("risk_of_bias")
        if not isinstance(rob, dict):
            continue
        by_outcome = rob.get("by_outcome")
        if not isinstance(by_outcome, dict):
            continue
        counts["risk_of_bias.by_outcome maps reached"] += 1
        for oid, trial_map in by_outcome.items():
            if not isinstance(trial_map, dict):
                continue
            counts["outcome RoB maps reached"] += 1
            for nct, entry in trial_map.items():
                if not _looks_like_trial_rob(nct, entry):
                    continue
                counts["per-trial RoB entries reached"] += 1
                findings = analyse_entry(topic, oid, nct, entry)
                for key in ("overall-only", "no-domains", "missing-domains",
                            "missing-judgement", "bad-source"):
                    if any(key in f["classes"] for f in findings):
                        counts[key] += 1
                if findings:
                    rows.extend(findings)
                else:
                    counts["complete"] += 1
    return rows, counts


def analyse_entry(topic, oid, nct, entry):
    path = "%s risk_of_bias.by_outcome.%s.%s" % (topic, oid, nct)
    if not isinstance(entry, dict):
        return [{
            "key": "ROB-ENTRY-NOT-STRUCTURED",
            "detail": "%s is not a dict, so no RoB-2 domain judgements or sources are shown"
                      % path,
            "classes": ("no-domains",),
        }]

    domains = domain_blocks(entry)
    if not domains:
        verdict = _overall_value(entry)
        if verdict:
            return [{
                "key": "ROB-OVERALL-WITHOUT-DOMAINS",
                "detail": "%s stores overall=%r with no per-domain RoB-2 judgements "
                          "sourced to a publication" % (path, verdict),
                "classes": ("overall-only", "no-domains"),
            }]
        return [{
            "key": "ROB-WITHOUT-DOMAINS",
            "detail": "%s has no per-domain RoB-2 judgements sourced to a publication"
                      % path,
            "classes": ("no-domains",),
        }]

    missing_domains = []
    missing_judgement = []
    bad_source = []
    for label, _aliases in DOMAINS:
        block = domains.get(label)
        if block is None:
            missing_domains.append(label)
            continue
        if not has_judgement(block):
            missing_judgement.append(label)
        ok, reason = has_publication_source(block)
        if not ok:
            bad_source.append("%s (%s)" % (label, reason))

    if not (missing_domains or missing_judgement or bad_source):
        return []

    bits = []
    classes = []
    if missing_domains:
        classes.append("missing-domains")
        bits.append("missing domains: " + ", ".join(missing_domains))
    if missing_judgement:
        classes.append("missing-judgement")
        bits.append("domains without a judgement: " + ", ".join(missing_judgement))
    if bad_source:
        classes.append("bad-source")
        bits.append("domains without a publication source: " + "; ".join(bad_source))
    return [{
        "key": "ROB-DOMAINS-NOT-PUBLICATION-SOURCED",
        "detail": "%s is unsupported: %s" % (path, "; ".join(bits)),
        "classes": tuple(classes),
    }]


def domain_blocks(entry):
    carrier = entry.get("domains") if isinstance(entry.get("domains"), (dict, list)) else entry
    out = {}
    if isinstance(carrier, dict):
        for key, value in carrier.items():
            slot = domain_slot(key)
            if slot is None and isinstance(value, dict):
                slot = domain_slot(value.get("domain") or value.get("name") or value.get("id"))
            if slot is not None:
                out[slot] = value
    elif isinstance(carrier, list):
        for item in carrier:
            if not isinstance(item, dict):
                continue
            slot = domain_slot(item.get("domain") or item.get("name") or item.get("id"))
            if slot is not None:
                out[slot] = item
    return out


def domain_slot(value):
    n = _norm(value)
    if not n:
        return None
    for label, aliases in DOMAINS:
        for alias in aliases:
            a = _norm(alias)
            if n == a or n.startswith(a + " ") or (" " + a + " ") in (" " + n + " "):
                return label
    return None


def has_judgement(block):
    if isinstance(block, str):
        return bool(block.strip())
    if not isinstance(block, dict):
        return False
    for key in JUDGEMENT_KEYS:
        value = block.get(key)
        if isinstance(value, str) and value.strip():
            return True
    return False


def has_publication_source(block):
    candidates = source_candidates(block)
    if not candidates:
        return False, "no source field"
    seen = []
    for key, value in candidates:
        text = _flatten_text(value)
        if publicationish(key, text):
            return True, "publication source present"
        if text:
            seen.append("%s=%s" % (key, _short(text)))
    if seen:
        return False, "source is not a publication: " + "; ".join(seen[:3])
    return False, "source field is empty"


def source_candidates(node):
    out = []

    def rec(x, path):
        if isinstance(x, dict):
            for key, value in x.items():
                here = path + "." + str(key) if path else str(key)
                if is_source_key(key):
                    out.append((here, value))
                if isinstance(value, (dict, list)):
                    rec(value, here)
        elif isinstance(x, list):
            for i, value in enumerate(x):
                if isinstance(value, (dict, list)):
                    rec(value, "%s[%d]" % (path, i))

    rec(node, "")
    return out


def is_source_key(key):
    n = _norm(key)
    if "subject ref" in n or "judgement ref" in n or "judgment ref" in n:
        return False
    return any(token in n for token in SOURCE_KEY_TOKENS)


def publicationish(key, text):
    nkey = _norm(key)
    lower = str(text).lower()
    if not lower.strip():
        return False
    if "not held" in lower or "not read" in lower or "no publication" in lower:
        return False
    if "pmid" in nkey and _has_digit(lower):
        return True
    if "pmid" in lower and _has_digit(lower):
        return True
    if ("pmcid" in nkey or "pmc" in nkey) and _has_digit(lower):
        return True
    if ("pmcid" in lower or "pmc" in lower) and _has_digit(lower):
        return True
    if "doi" in nkey and "/" in lower and _has_digit(lower):
        return True
    if "doi" in lower and _has_digit(lower):
        return True
    if "10." in lower and "/" in lower:
        return True
    if ("citation" in nkey or "reference" in nkey or "publication" in nkey
            or "report" in nkey):
        return has_citation_cue(lower) and not registry_only(lower)
    if has_citation_cue(lower) and not registry_only(lower):
        return True
    return False


def has_citation_cue(lower):
    if not has_year(lower):
        return False
    return any(cue in lower for cue in JOURNAL_CUES)


def registry_only(lower):
    if not any(token in lower for token in REGISTRY_TOKENS):
        return False
    return not (("pmid" in lower and _has_digit(lower))
                or ("doi" in lower and _has_digit(lower))
                or ("pmc" in lower and _has_digit(lower))
                or ("10." in lower and "/" in lower)
                or any(cue in lower for cue in (" et al", "lancet", "jama",
                                                "n engl j med", "nejm", "bmj")))


def _looks_like_trial_rob(nct, entry):
    if isinstance(nct, str) and nct.upper().startswith("NCT"):
        return True
    if isinstance(entry, dict) and isinstance(entry.get("nct"), str):
        return entry.get("nct").upper().startswith("NCT")
    return False


def _overall_value(entry):
    for key in ("overall", "overall_verdict", "overall_judgement", "overall_judgment"):
        value = entry.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _flatten_text(value):
    parts = []

    def rec(x):
        if isinstance(x, (str, int, float)):
            parts.append(str(x))
        elif isinstance(x, dict):
            for k, v in x.items():
                parts.append(str(k))
                rec(v)
        elif isinstance(x, list):
            for v in x:
                rec(v)

    rec(value)
    return " ".join(p for p in parts if p)


def has_year(lower):
    for year in range(1900, 2100):
        if str(year) in lower:
            return True
    return False


def _has_digit(text):
    return any(ch.isdigit() for ch in str(text))


def _norm(value):
    text = str(value or "")
    chars = []
    for ch in text:
        chars.append(ch.lower() if ch.isalnum() else " ")
    return " ".join("".join(chars).split())


def _short(text):
    text = " ".join(str(text).split())
    return text if len(text) <= 120 else text[:117] + "..."


if __name__=='__main__': sys.exit(main(sys.argv[1:]))
