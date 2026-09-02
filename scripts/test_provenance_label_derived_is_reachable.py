"""The Extraction tab's read-vs-derived label must not call a derived value READ.

`extraction_provenance_table` decides column four from two fields:

    if df == "published_hazard_ratio" or (tag == "MEASURED" and df):
        "READ from the source as printed"
    elif df:
        "DERIVED by us from %s"

`df` is `effect.derived_from` and `tag` is `provenance.tag`. The second disjunct
conflates two different things. `MEASURED` is defined by the validator
(`check_against_sources`) as A CELL THAT CAN BE VERIFIED AGAINST A STAGED SOURCE
PAYLOAD -- it says the value is source-backed and checkable, NOT that the source
printed it in that form. SCHEMA_v2 item 28 is the clearest case: the source prints a
vaccine efficacy percentage, the object stores a ratio, the derivation must reproduce
including the interval inversion -- source-backed AND derived, both at once.

So on APIXABAN_VTE_PROPHYLAXIS the four rows print "READ from the source as printed"
directly above their own note, which reads: "Events are the posted event RATE
multiplied by the analysed denominator and rounded -- DERIVED, and labelled DERIVED".
The page states the opposite of itself in adjacent cells.

These tests call the REAL projector -- `extraction_provenance_table` from
ssot/projectors.py -- against the REAL stores. Nothing here reimplements the label.

Run:  python scripts/test_provenance_label_derived_is_reachable.py   (standalone)
  or: pytest scripts/test_provenance_label_derived_is_reachable.py
"""
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)

_SSOT = os.path.join(REPO, "ssot")
if _SSOT not in sys.path:
    sys.path.insert(0, _SSOT)
import projectors as pj  # noqa: E402  (path must be set first)

READ = "<strong>READ</strong> from the source as printed"
DERIVED = "<strong>DERIVED</strong> by us from"


def _store(topic):
    path = os.path.join(REPO, "ssot", topic, topic + ".json")
    assert os.path.exists(path), "fixture store missing: %s" % path
    with io.open(path, encoding="utf-8") as fh:
        return json.load(fh)


def rows_for(topic):
    """Every <tr> of the real Extraction provenance table, as rendered."""
    html = pj.extraction_provenance_table(_store(topic))
    assert html, "no provenance table rendered for %s" % topic
    rows = re.findall(r"<tr>.*?</tr>", html, re.S)
    assert rows, "provenance table for %s rendered no rows" % topic
    return rows


def rows_where_object_says_derived(topic):
    """Rows whose OWN note asserts the value was derived, matched back to the render.

    The object is the authority on its own provenance; this reads the note rather
    than restating the rule the code under test applies.
    """
    obj = _store(topic)
    wanted = []
    for trial in ((obj.get("inputs") or {}).get("trials") or []):
        for oid, bo in (trial.get("by_outcome") or {}).items():
            if not isinstance(bo, dict):
                continue
            eff = bo.get("effect") or {}
            prov = bo.get("provenance") or {}
            note = str(eff.get("derivation_note") or prov.get("quote_note") or "")
            if eff.get("derived_from") and "DERIVED" in note:
                wanted.append((str(trial.get("id") or ""), oid, note))
    return wanted


# ---------------------------------------------------------------------------
# THE DEFECT. The object says DERIVED in its own note; the label says READ.
# ---------------------------------------------------------------------------

def test_apixaban_prophylaxis_rows_are_not_labelled_read():
    """Four rows: "DERIVED, and labelled DERIVED" -- and labelled READ."""
    declared = rows_where_object_says_derived("apixaban-vte-prophylaxis")
    assert len(declared) == 4, (
        "expected 4 self-declared-derived rows, found %d -- the fixture must be "
        "repointed, not deleted" % len(declared))
    offenders = [r for r in rows_for("apixaban-vte-prophylaxis")
                 if READ in r and "DERIVED, and labelled DERIVED" in r]
    assert not offenders, (
        "%d row(s) print 'READ from the source as printed' in the same cell as a note "
        "saying 'DERIVED, and labelled DERIVED'" % len(offenders))


def test_apixaban_treatment_rows_are_not_labelled_read():
    """"The risk ratio and its interval are DERIVED from the arm-level counts."""
    offenders = [r for r in rows_for("apixaban-vte-treatment")
                 if READ in r and "are DERIVED from the arm-level counts" in r]
    assert not offenders, (
        "%d row(s) print READ above a note saying the ratio is DERIVED"
        % len(offenders))


# ---------------------------------------------------------------------------
# THE CONTROLS. These rows also carry `derived_from` with tag MEASURED, so a
# blanket "drop the MEASURED disjunct" change relabels them too -- but their own
# notes say, in terms, that the value WAS read as printed. Turning these into
# DERIVED would replace one false label with another. They must stay READ.
# ---------------------------------------------------------------------------

def test_alirocumab_rows_that_say_read_as_printed_stay_read():
    """"It is read as printed. It is NOT computed from the two arm means..."""
    rows = [r for r in rows_for("alirocumab-lipid") if "It is read as printed" in r]
    assert len(rows) == 6, "expected 6 such rows, found %d" % len(rows)
    mislabelled = [r for r in rows if DERIVED in r]
    assert not mislabelled, (
        "%d row(s) print DERIVED above a note saying 'It is read as printed'"
        % len(mislabelled))


def test_bococizumab_row_that_says_read_not_derived_stays_read():
    """"READ, not derived." -- the note could not be more explicit."""
    rows = [r for r in rows_for("bococizumab-lipid-review")
            if "READ, not derived" in r]
    assert len(rows) == 6, "expected 6 such rows, found %d" % len(rows)
    mislabelled = [r for r in rows if DERIVED in r]
    assert not mislabelled, (
        "%d row(s) print DERIVED above their own note saying 'READ, not derived'"
        % len(mislabelled))


def test_finerenone_cv_rows_read_from_the_registry_stay_read():
    """"Point estimate and interval are READ from the ClinicalTrials.gov results."""
    rows = [r for r in rows_for("finerenone-cv")
            if "are READ from the ClinicalTrials.gov results section" in r]
    assert len(rows) == 2, "expected 2 such rows, found %d" % len(rows)
    mislabelled = [r for r in rows if DERIVED in r]
    assert not mislabelled, (
        "%d row(s) print DERIVED above a note saying the estimate is READ"
        % len(mislabelled))


def test_iv_iron_rows_stored_as_the_source_prints_them_stay_read():
    """"The point estimate and interval are stored as the source prints them."""
    rows = [r for r in rows_for("iv-iron-hf")
            if "stored as the source prints them" in r]
    assert rows, "expected rows stored as the source prints them, found none"
    mislabelled = [r for r in rows if DERIVED in r]
    assert not mislabelled, (
        "%d of %d row(s) print DERIVED above a note saying the estimate is stored as "
        "the source prints it" % (len(mislabelled), len(rows)))


def test_published_hazard_ratio_rows_stay_read():
    """The case the brief explicitly preserves: 23 rows across the corpus."""
    rows = [r for r in rows_for("arni-hfref") if READ in r]
    assert rows, "ARNI's published-hazard-ratio rows no longer render READ"


# ---------------------------------------------------------------------------
# THE CLASSIFICATION ITSELF. A value nobody has read the note for is missing
# evidence; a default would turn that into a printed claim about provenance.
# ---------------------------------------------------------------------------

def _all_topics():
    root = os.path.join(REPO, "ssot")
    topics = sorted(n for n in os.listdir(root)
                    if os.path.exists(os.path.join(root, n, n + ".json")))
    assert len(topics) >= 100, (
        "only %d stores visible -- an enumeration reports where it LOOKED, and a "
        "truncated corpus would pass this for the wrong reason" % len(topics))
    return topics


def _distinct_derived_from():
    """Every distinct `derived_from` value in the corpus, with its row count."""
    counts = {}
    for topic in _all_topics():
        obj = _store(topic)
        for trial in ((obj.get("inputs") or {}).get("trials") or []):
            for oid, bo in (trial.get("by_outcome") or {}).items():
                if not isinstance(bo, dict):
                    continue
                df = (bo.get("effect") or {}).get("derived_from")
                if df is not None:
                    counts[str(df)] = counts.get(str(df), 0) + 1
    return counts


def test_every_derived_from_value_in_the_corpus_is_classified():
    """Enumerated, not sampled. A value you have not seen still exists."""
    kind = getattr(pj, "provenance_kind", None)
    assert kind is not None, "ssot/projectors.py exposes no provenance_kind()"
    counts = _distinct_derived_from()
    assert len(counts) >= 18, (
        "expected at least the 18 known values, enumerated %d" % len(counts))
    unclassified = []
    for value in sorted(counts):
        try:
            kind(value)
        except ValueError:
            unclassified.append((value, counts[value]))
    assert not unclassified, (
        "%d of %d distinct derived_from values are unclassified, covering %d rows:\n%s"
        % (len(unclassified), len(counts), sum(c for _, c in unclassified),
           "\n".join("    [%3d] %s" % (c, v) for v, c in unclassified)))


def test_an_unclassified_value_fails_loudly():
    """The negative control on the gate itself: it must be able to refuse."""
    kind = getattr(pj, "provenance_kind", None)
    assert kind is not None, "ssot/projectors.py exposes no provenance_kind()"
    try:
        kind("a provenance nobody has ever written down")
    except ValueError:
        return
    raise AssertionError(
        "an unknown derived_from value was accepted -- it must raise, not default, "
        "or missing evidence becomes a printed verdict")


# ---------------------------------------------------------------------------
# THE CORPUS SWEEP, judged against the OBJECT'S OWN NOTE rather than against the
# classification table -- checking the table against itself would prove nothing.
# ---------------------------------------------------------------------------

# Phrases a row's own note uses to state its provenance. Chosen without
# apostrophes: the note is HTML-escaped into the row, so "page's" is "page&#x27;s".
SAYS_READ = (
    "READ, not derived",
    "It is read as printed",
    "READ from the source as printed, never recomputed",
    "embedded publishedHR",
    "are READ from the ClinicalTrials.gov results section",
    "stored as the source prints them",
)
SAYS_DERIVED = (
    "DERIVED, and labelled DERIVED",
    "are DERIVED from the arm-level counts",
    "DERIVED, not read",
)


def test_no_row_label_contradicts_its_own_note():
    examined, wrong = 0, []
    for topic in _all_topics():
        try:
            rows = rows_for(topic)
        except AssertionError:
            continue  # no provenance table on this topic
        for row in rows:
            says_read = any(p in row for p in SAYS_READ)
            says_derived = any(p in row for p in SAYS_DERIVED)
            if not (says_read or says_derived):
                continue
            examined += 1
            if says_read and says_derived:
                continue  # note describes both halves; not a contradiction
            if says_read and DERIVED in row:
                wrong.append((topic, "labelled DERIVED, note says READ"))
            if says_derived and READ in row:
                wrong.append((topic, "labelled READ, note says DERIVED"))
    assert examined >= 40, (
        "only %d rows carried a note stating their provenance; expected ~70" % examined)
    assert not wrong, (
        "%d of %d rows carry a label contradicting their own note:\n%s"
        % (len(wrong), examined,
           "\n".join("    %-44s %s" % (t, w) for t, w in sorted(wrong))))


def test_the_largest_already_derived_group_is_left_alone():
    """`extractor recovery from the published page` -- 49 rows, note says
    "DERIVED, not read". It renders DERIVED today and must keep doing so."""
    rows = [r for r in rows_for("acs-antiplatelet-review") if "DERIVED, not read" in r]
    assert rows, "no extractor-recovery rows found on acs-antiplatelet-review"
    mislabelled = [r for r in rows if READ in r]
    assert not mislabelled, (
        "%d of %d extractor-recovery rows flipped to READ" % (len(mislabelled), len(rows)))


if __name__ == "__main__":
    failed = 0
    for _name, _fn in sorted(globals().items()):
        if _name.startswith("test_") and callable(_fn):
            try:
                _fn()
                print("PASS  %s" % _name)
            except AssertionError as exc:
                failed += 1
                print("FAIL  %s\n      %s" % (_name, exc))
    print("\n%d failed" % failed)
    raise SystemExit(1 if failed else 0)
