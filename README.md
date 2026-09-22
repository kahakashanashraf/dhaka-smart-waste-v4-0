# Dhaka Smart Waste V4.0

**A One-Year Context-Aware Synthetic IoT Dataset for Smart Waste Management in Dhaka, Bangladesh: 43.8 Million Hourly Observations**

Dhaka Smart Waste V4.0 is a deterministic, scenario-based synthetic IoT dataset containing **5,000 persistent smart-bin digital twins** simulated hourly throughout **2025**, producing exactly **43,800,000 hourly observations**.

## Dataset at a glance

- 5,000 persistent synthetic bins
- 365 days / 8,760 hours per bin
- 43,800,000 hourly observations
- 59 hourly observation variables
- 29 persistent bin-level variables
- fixed NumPy seed: `20260902`
- timezone: `Asia/Dhaka (UTC+06:00)`
- synthetic coordinates around representative Dhaka neighborhood centers; not real municipal bin locations

The simulator is context-aware: waste generation and bin behavior depend on land-use subtype, synthetic catchment population, population density, hour/day/weekend, institutional status, market/recreation activity, Ramadan and Eid scenarios, weather seasonality, waste composition, informal recovery, road accessibility, collection dynamics, overflow, battery state, packet loss, and sensor anomalies.

## Full data download

The complete multi-gigabyte data are kept outside GitHub so that users can download the full release without GitHub file-size limitations.

- **CSV/GZIP full release (44 observation parts + `bins.csv.gz`)**: https://drive.google.com/drive/folders/16JeuImcx-pDF01ydejQWKOOUEmcC0Y2m
- **Parquet full release (23 ZIP archives containing 92 observation parts)**: https://drive.google.com/drive/folders/1TseLOtPXKv5t3wrujbpQFx9bRIXMYN8d
- **Documentation package**: https://drive.google.com/drive/folders/1LpIMF1x3pF-aivdPPxvF2YHqNeds22eo
- **Code and Colab notebooks**: https://drive.google.com/drive/folders/1N3naS2gc9BCBupLz7TVOGsXHm86CGg7C

The archival dataset release is available through **Mendeley Data V4**: https://doi.org/10.17632/ctt5kwppwt.4

## Data layouts

### CSV/GZIP

- `observations_part_000.csv.gz` through `observations_part_042.csv.gz`: 1,000,000 rows each
- `observations_part_043.csv.gz`: 800,000 rows
- total: 43,800,000 rows
- static table: `bins.csv.gz`

### Parquet

- `observations_part_000.parquet` through `observations_part_090.parquet`: 480,000 rows each
- `observations_part_091.parquet`: 120,000 rows
- total: 43,800,000 rows
- static table: `bins.parquet`

All observation partitions form one logical hourly table. Join the persistent bin metadata using `bin_index`.

## Reproduce

```bash
python -m pip install -r requirements.txt
python src/generate_v4_0.py
python scripts/validate_v4_0.py
```

Validate a reconstructed Parquet release under `final_parts/PARQUET/`:

```bash
python scripts/validate_export_parts.py final_parts
```

For the distributed Drive release (23 transport ZIPs + `bins.parquet`), run the publication-oriented validator:

```bash
python -m pip install -r requirements-validation.txt
python scripts/validate_v4_0_paper.py --project-root "/path/to/Dhaka Smart Waste V4.0 2025"
```

For the exact package versions used in the successful 22 September 2026 full-release validation, see `requirements-validation.txt` and `validation/environment_summary.txt`.

Validate the CSV/GZIP release:

```bash
python scripts/validate_csv_parts.py /path/to/CSV_PARTS
```

### Post-release reproducibility note

The **V4.0 dataset bytes are unchanged**. The repository `main` branch contains post-release reproducibility-path fixes, the reviewer-oriented validator, and validation evidence generated from the distributed V4.0 release. The historical GitHub `v4.0` tag remains an archival snapshot and is not rewritten.

## Full-release technical validation

A reviewer-oriented validation run on the distributed V4.0 release scanned all **43,800,000** hourly observations across **92** Parquet parts. The final automated gate reported:

- **49/49 hard checks PASS**
- **15/15 soft checks PASS**
- **0 duplicate bin-hour keys**
- **0 missing bin-hour keys**
- **8,760 records for every one of the 5,000 bins**
- packet-loss rate: **0.4712%**
- sensor-anomaly rate among available packets: **0.1000%**
- fill-sensor residual SD: **1.5000 percentage points**
- four-hour no-collection forecast MAE: **2.0403 percentage points** (n = **514,552**)

See `validation/` for the machine-readable/check-level evidence and `scripts/validate_v4_0_paper.py` for the publication-oriented validator. These are internal/release-consistency checks for a synthetic dataset, not field validation of deployed Dhaka smart bins.

## Repository contents

```text
src/         canonical data generator
scripts/     validation and environment tools
docs/        methodology, dictionary, calibration and reproducibility notes
data/        full CSV manifest
sample/      small CSV examples
notebooks/   Colab notebooks
validation/  publication-oriented full-release validation artifacts
```

The full observation data are intentionally hosted in Drive/Mendeley rather than committed directly to GitHub.

## License

CC BY 4.0 — Creative Commons Attribution 4.0 International.

## Citation

Ashraf, Kahakashan; Arefin, Mohammad Shamsul (2026), “A One-Year Context-Aware Synthetic IoT Dataset for Smart Waste Management in Dhaka, Bangladesh: 43.8 Million Hourly Observations”, Mendeley Data, V4, doi: 10.17632/ctt5kwppwt.4
