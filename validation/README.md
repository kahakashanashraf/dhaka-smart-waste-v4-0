# Full-release validation evidence

This directory contains publication-oriented technical validation artifacts for **Dhaka Smart Waste V4.0**.

The successful validation run was completed on **22 September 2026** against the distributed release. It scanned all **43,800,000** hourly observations across **92** logical Parquet parts.

## Final gate

- 49 hard checks: **PASS**
- 15 soft checks: **PASS**
- hard failures: **0**
- warnings: **0**
- duplicate bin-hour keys: **0**
- missing bin-hour keys: **0**
- records per bin: **8,760** for all 5,000 bins
- packet-loss rate: **0.4712%**
- sensor-anomaly rate among available packets: **0.1000%**
- fill-sensor residual mean: **0.0002 percentage points**
- fill-sensor residual SD: **1.5000 percentage points**
- 4-hour forecast MAE when no collection occurs in the horizon: **2.0403 percentage points** (n = **514,552**)

These checks establish release integrity, internal rule consistency, reproducibility evidence, and statistical behavior of the **synthetic** simulation. They do **not** constitute field validation of deployed municipal smart bins.

## Files

- `validation_summary.csv` — check-level validation table
- `VALIDATION_REPORT.json` — machine-readable full report
- `RELEASE_FILE_MANIFEST.csv` and `SHA256SUMS.txt` — release integrity manifest
- `parquet_zip_contents.csv` — 23 ZIP to 92 Parquet mapping
- `monthly_climate_validation.csv` — monthly climate calibration
- `scenario_summary.csv` — scenario-direction summaries
- `environment_summary.txt` and `environment_lock.txt` — executed validation environment
- `TECHNICAL_VALIDATION.md` — paper-ready technical-validation draft

Validator: `../scripts/validate_v4_0_paper.py`

Notebook: `../notebooks/Dhaka_Smart_Waste_V4_0_Paper_Validation.ipynb`

Archival dataset DOI: https://doi.org/10.17632/ctt5kwppwt.4
