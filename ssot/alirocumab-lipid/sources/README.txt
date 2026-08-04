SOURCE PAYLOADS

Every file here was fetched from the named public source and written verbatim.
Nothing in this directory was edited by hand.

  <NCT>.ctgov.json    - the ClinicalTrials.gov API v2 record for that trial,
                        including its posted results section where one exists.
                        This is the record the canonical object's registry-
                        sourced cells were read from.
  PMID<id>.pubmed.xml - the PubMed record for that publication, including the
                        abstract. Cells attributed to a publication abstract
                        were read from these.
  INDEX.json          - what each file is, per app.

To verify a cell: take its `source_id` and `source` text in the canonical
object, open the corresponding file here, and read the value yourself. If a
value cannot be found in these files, the object is asserting something the
workspace does not support, and that is a defect worth reporting.

FORMATTING WARNING, so a real match is not mistaken for a missing one:
PubMed XML writes thin/hair spaces INSIDE numerals. A denominator of 14964
appears in the abstract as "14&#x2008;964" and renders as "14 964". Normalise
whitespace and entities inside digit runs before concluding a value is absent.
Every per-arm count and denominator in both canonical objects was checked
against these files after such normalisation and every one was found.
