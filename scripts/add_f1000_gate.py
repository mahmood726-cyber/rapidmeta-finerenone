import io, sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
P = r"F:\rapidmeta-ssot-shell\ssot\make_docx.py"
s = open(P, encoding="utf-8").read()

ANCHOR = 'doc.save(OUT)\nprint("wrote", OUT, os.path.getsize(OUT), "bytes")'
assert s.count(ANCHOR) == 1

NEW = r'''# --- F1000Research submission checklist -------------------------------------
# Requirements taken from F1000Research's own author guidance for Systematic
# Reviews, looked up rather than remembered (their site 403s direct fetch, so
# these come from the indexed guideline pages):
#   * a Data Availability Statement is mandatory EVEN WHERE THERE IS NO DATA;
#   * PRISMA checklist AND flow diagram are required, and the completed
#     checklist and flow chart must be DEPOSITED in an approved repository,
#     with the guideline type, repository, DOI and licence in the statement;
#   * extended data needs title, repository, DOI/accession and licence, under
#     an "Extended data" subheading, cited in the main text;
#   * the repository must supply a persistent identifier and allow CC0 /
#     CC-BY 4.0 or equivalent;
#   * archived source code needs a DOI and citation in Zenodo under an open,
#     preferably OSI-approved, licence.
#
# These are MANDATORY FIELDS at this venue, not nice-to-haves, so an unmet one
# blocks rather than prints. The missing identifiers are recorded as null with a
# stated reason and are never filled with a plausible string: a wrong DOI in a
# Data Availability Statement points a reader at someone else's data, which is
# worse than no DOI at all. Minting them is an author action, not a build step.
_F1000 = []
_das = MS.get("data_availability_statement") or {}
_ed = _das.get("extended_data") or {}
_swx = MS.get("software_availability") or {}
for _label, _ok in (
    ("Data Availability Statement present", bool(_das)),
    ("Extended data: repository named", bool(_ed.get("repository"))),
    ("Extended data: persistent identifier (DOI) minted",
     bool(_ed.get("persistent_identifier"))),
    ("Extended data: open licence (CC0 or CC-BY 4.0)",
     str(_ed.get("licence", "")).upper().startswith(("CC0", "CC-BY", "CC BY"))),
    ("Software: source code location", bool(_swx.get("source_code_available_from"))),
    ("Software: archived Zenodo DOI at publication",
     bool(_swx.get("archived_source_code_at_time_of_publication"))),
    ("Software: OSI-approved licence", bool(_swx.get("licence"))),
    ("PRISMA flow diagram present", FIG > 0),
    ("PRISMA checklist deposited with a DOI",
     bool((MS.get("prisma") or {}).get("checklist_doi"))),
    ("Structured abstract", isinstance(MS.get("abstract"), dict)
     and len(MS.get("abstract") or {}) >= 4),
    ("Registration statement", bool(MS.get("registration_note_for_editor"))),
):
    if not _ok:
        _F1000.append(_label)
if _F1000:
    _probs.append("F1000 mandatory requirements unmet: " + "; ".join(_F1000))

doc.save(OUT)
print("wrote", OUT, os.path.getsize(OUT), "bytes")
if _F1000:
    print("")
    print("#" * 72)
    print("SUBMISSION BLOCKED -- %d mandatory F1000Research requirement(s) unmet:"
          % len(_F1000))
    for _x in _F1000:
        print("   - %s" % _x)
    print("These are author actions (Zenodo deposits), not build steps. No "
          "identifier will be invented to clear them.")
    print("#" * 72)'''

s = s.replace(ANCHOR, NEW, 1)
open(P, "w", encoding="utf-8").write(s)
print("make_docx: F1000 submission checklist wired into the conformance gate")
