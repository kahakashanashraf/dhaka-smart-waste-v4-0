# Data in Brief submission readiness — Dhaka Smart Waste V4.0

Status date: 2026-09-22

## Technical/data package

- [x] Public archival dataset DOI recorded: `10.17632/ctt5kwppwt.4`
- [x] 5,000 persistent synthetic bins
- [x] 43,800,000 hourly observations
- [x] 29 persistent bin-level variables
- [x] 59 hourly observation variables
- [x] Full data dictionary and categorical code lookup
- [x] Deterministic generator with fixed NumPy seed `20260902`
- [x] Research calibration/evidence map separating external anchors from scenario assumptions
- [x] CSV/GZIP and Parquet release layouts documented
- [x] `bins.parquet` and `bins.csv.gz` available
- [x] 92 Parquet observation parts represented by 23 transport ZIPs
- [x] Full-release validator and source-only Colab notebook available
- [x] Reviewer-oriented full scan completed: 43,800,000/43,800,000 rows
- [x] 49 hard checks PASS
- [x] 15 soft checks PASS
- [x] 0 hard failures / 0 warnings
- [x] 0 duplicate bin-hour keys / 0 missing bin-hour keys
- [x] SHA-256 release manifest generated
- [x] ZIP-to-Parquet mapping generated
- [x] Executed validation environment captured
- [x] Root CC BY 4.0 license present
- [x] CITATION.cff present
- [x] Clean-clone path mismatches in canonical validation tools corrected on `main`
- [x] Publication-oriented validation artifacts mirrored under `validation/`

## Manuscript package still to prepare

- [ ] Descriptive abstract focused on the dataset
- [ ] Specifications Table
- [ ] 3–5 short Value of the Data bullets
- [ ] Concise Background
- [ ] Data Description
- [ ] Experimental Design, Materials and Methods
- [ ] Limitations
- [ ] Ethics Statement for a fully synthetic dataset
- [ ] CRediT author contribution statement based on actual contributions
- [ ] Funding/Acknowledgements based on actual funding status
- [ ] Declaration of Competing Interest
- [ ] Final Data Availability statement
- [ ] Final Code Availability statement
- [ ] References directly supporting the data-generation/calibration choices
- [ ] Generative-AI writing disclosure if required by the journal at submission time

## Final external checks before submission

1. Open the Mendeley Data V4 DOI in a normal browser and verify that the public landing page shows the intended V4 title, authors, license, and files.
2. Confirm that the Mendeley V4 deposited files match the release intended for the paper. Use `validation/SHA256SUMS.txt` for byte-level comparison where possible.
3. Use an immutable GitHub commit SHA from `main` in the Code Availability statement. The historical `v4.0` tag remains an archival snapshot and is intentionally not rewritten.
4. Do not describe the validation as field validation. The dataset is a scenario-based synthetic digital twin; validation establishes structural integrity, implementation consistency, and reproducibility of the released simulation.
5. Do not regenerate the dataset merely to prepare the paper unless the dataset itself is intentionally being revised. Current V4.0 release-level validation passed.

## Journal-format note

Current Data in Brief guidance emphasizes a descriptive data article rather than a mini research paper. Avoid a conventional Discussion/Conclusion section unless the current journal template explicitly requests it. The article should make the data accessible, understandable, and reusable, and should clearly distinguish empirical/literature anchors from synthetic scenario coefficients.
