# Release Checklist

## Status
- [x] README present
- [x] LICENSE present
- [x] Runtime manifest present (`requirements.txt`)
- [x] Public remote configured
- [x] Validation scripts present (`validate_finerenone.R`, `FINERENONE_R_validation.R`)
- [ ] Working tree cleaned for release
- [ ] DOI minted from tagged release

## Before Publishing
1. Run the R validation scripts and regenerate the validation outputs if needed.
2. Re-run the browser validation checks for `FINERENONE_REVIEW.html`.
3. Clean or separate generated artifacts before tagging a release.
4. Create the release tag on GitHub.
5. Mint the Zenodo DOI and update `CITATION.cff` if you want the DOI cited.
