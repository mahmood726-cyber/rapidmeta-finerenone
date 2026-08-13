"""Journal submission profiles, as machine-checkable requirements.

WHY A PROFILE AND NOT AN ARNI FIX. Every requirement below recurs on every paper
Mahmood submits to this journal. Encoding them as a profile with validators means
the next Nafis review inherits them instead of rediscovering them, and a build
that violates one FAILS rather than producing a manuscript that will bounce.

WHAT A PROFILE IS NOT. It is not a style preference. Each entry here is a stated
requirement of the journal, and where the journal states an ORDER of preference
-- EPS first, the original graph file second, uncompressed TIFF only "if none of
the above options is possible" -- the profile records the order, because
satisfying the fallback while the first choice was available is a worse
submission, not an equal one.

THE VALIDATORS FAIL THE BUILD. A word limit that only warns is a word limit that
gets exceeded. These raise.
"""
import re


class ProfileViolation(Exception):
    """A submission requirement was not met. Never ship past this."""


F1000RESEARCH = {
    "name": "F1000Research",
    "submission_formats": ("doc", "docx", "rtf"),

    # ---------------------------------------------------------------- figures
    "figure_formats_in_preference_order": (
        ("eps", "Line art should be EPS. This is the journal's FIRST preference "
                "and all ten of our plots are line art."),
        ("original", "Failing EPS, the original file the graph was made in."),
        ("tiff", "Uncompressed TIFF at 600 dpi or better, accepted only 'if none "
                 "of the above options is possible'."),
    ),
    "figure_formats_rejected": {
        "jpeg": ("Not on the accepted list, and it is a lossy photographic codec "
                 "applied to line art: it puts ringing on every rule and glyph "
                 "edge. Dropping it costs nothing."),
        "svg": ("NOT on the accepted list. Kept for the web page only, where it "
                "is the master the other formats are generated from."),
    },
    "figure_min_dpi": 600,
    "figure_tiff_compression": None,      # uncompressed, explicitly
    "figure_colour_modes": ("RGB", "greyscale"),
    "figure_background": "white",
    "figure_min_text_pt": 8,
    "figure_display_width_mm": (75, 150),
    "figure_title_max_words": 15,
    "figure_legend_required": True,
    "figures_and_tables_position": "end",   # not inline

    # ---------------------------------------------------------------- abstract
    "abstract_structured": True,
    "abstract_sections": ("Background", "Methods", "Results", "Conclusions"),
    "abstract_max_words": 300,
    "abstract_allows_citations": False,
    "abstract_abbreviations": "spelled out on first use",

    "keywords_max": 8,

    # ------------------------------------------------------------ no supplement
    "accepts_supplementary_material": False,
    "extended_data_route": (
        "Deposit in an approved repository under CC0 or CC-BY, cite in the Data "
        "Availability Statement with its DOI. There is no attachment channel."),
    "data_availability_statement_required": True,   # even when there is no data
    "prisma_required": True,
    "prisma_route": "deposited with a DOI and cited in the Data Availability Statement",
    "prospero_encouraged": True,

    "software_requirements": (
        "Source code on GitHub, an archived copy in Zenodo with a DOI, and an "
        "OSI-approved licence."),

    "table_construction": "Word Insert Table, or supplied as Excel. Not images.",
    "table_title_max_words": 15,
}


# ---------------------------------------------------------------- validators

def _words(s):
    return len((s or "").split())


def check_abstract(sections, profile=F1000RESEARCH, tokens=None):
    """Structured, within the word limit, right headings, no citations.

    The count is of the FILLED text when tokens are supplied. A [[token]] is one
    word in the source and can be five once substituted -- [[loo_paradigm]]
    expands to "0.935 (0.765 to 1.14)" -- so counting the template undercounts
    exactly the abstract that is closest to the limit. The editor counts the
    filled text; so does this.
    """
    problems = []
    if tokens:
        def _fill(v):
            return re.sub(r"\[\[([a-z0-9_]+)\]\]",
                          lambda mm: str(tokens.get(mm.group(1), mm.group(0))), v or "")
        sections = {k: _fill(v) for k, v in sections.items()}
    want = list(profile["abstract_sections"])
    got = [k for k in sections if not k.startswith("_")]
    if [g.lower() for g in got] != [w.lower() for w in want]:
        problems.append("abstract sections are %s; the journal requires exactly "
                        "%s in that order" % (got, want))
    total = sum(_words(v) for k, v in sections.items() if not k.startswith("_"))
    if total > profile["abstract_max_words"]:
        problems.append("abstract is %d words; the limit is %d"
                        % (total, profile["abstract_max_words"]))
    if not profile["abstract_allows_citations"]:
        # No local `import re` here: binding the name inside the function makes it
        # local to the WHOLE function, so the earlier re.sub in _fill() becomes a
        # free-variable error. Module-level import is used throughout.
        for k, v in sections.items():
            if k.startswith("_"):
                continue
            if re.search(r"\[\d+\]|\(\s*[A-Z][a-z]+ (?:et al\.?,? )?\d{4}\s*\)", v or ""):
                problems.append("abstract section %r appears to carry a citation; "
                                "the journal does not allow them" % k)
    return total, problems


def check_keywords(kw, profile=F1000RESEARCH):
    if kw is None:
        return ["no keywords supplied; the journal asks for up to %d"
                % profile["keywords_max"]]
    if len(kw) > profile["keywords_max"]:
        return ["%d keywords supplied; the maximum is %d"
                % (len(kw), profile["keywords_max"])]
    return []


def check_title_words(title, kind, profile=F1000RESEARCH):
    lim = profile["%s_title_max_words" % kind]
    n = _words(title)
    return ([] if n <= lim else
            ["%s title is %d words; the limit is %d: %r" % (kind, n, lim, title[:70])])


def enforce(problems, where):
    if problems:
        raise ProfileViolation(
            "%s does not meet %s requirements:\n  - %s"
            % (where, F1000RESEARCH["name"], "\n  - ".join(problems)))


def statement_of_conformance(profile=F1000RESEARCH):
    """What the build did about each requirement, for the record."""
    return {
        "profile": profile["name"],
        "figures": ("EPS generated as the journal's first preference for line "
                    "art; uncompressed TIFF at %d dpi carried as the stated "
                    "fallback; JPEG dropped (not accepted, and lossy on line "
                    "art); SVG retained for the web page only, where it is the "
                    "master the others derive from."
                    % profile["figure_min_dpi"]),
        "supplementary": ("The journal accepts none. Extended data is built as a "
                          "deposit package for an approved repository under CC0 "
                          "or CC-BY and cited in the Data Availability "
                          "Statement by DOI."),
        "abstract": "Structured, %d words maximum, %s, no citations." % (
            profile["abstract_max_words"], " / ".join(profile["abstract_sections"])),
        "tables_and_figures": "Legends and tables placed at the end, not inline.",
        "prisma": "Checklist and flow diagram deposited and cited by DOI.",
        "registration": ("Protocol registered as a timestamped, SHA-pinned public "
                         "commit. PROSPERO is the token the journal names; ours "
                         "is arguably stronger evidence of ordering but is NOT "
                         "the same token, and that difference is flagged rather "
                         "than presented as equivalent."),
    }
