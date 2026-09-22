# CSV Release — Dhaka Smart Waste V4.0

This folder contains the CSV/GZIP representation of the one-year synthetic smart-waste dataset.

## Files

- `bins.csv.gz` — 5,000 persistent synthetic bin/context records; 29 columns.
- `observations_part_000.csv.gz` through `observations_part_042.csv.gz` — 1,000,000 hourly observation rows each.
- `observations_part_043.csv.gz` — 800,000 hourly observation rows.
- Total hourly observations: **43,800,000**.
- Hourly observation variables: **59**.

The observation CSV files and the Parquet release represent the same logical synthetic dataset. Join persistent bin metadata to observations using `bin_index`.

## Geographic note

Latitude/longitude values are synthetic points generated around representative Dhaka neighborhood centers. They are not coordinates of real municipal smart bins.

## Validation

Run:

```bash
python validate_csv_parts.py
```

from a directory containing `bins.csv.gz` and all 44 `observations_part_*.csv.gz` files.

Expected result:

```text
CSV observation parts: 44
CSV rows: 43800000
bins rows: 5000
PASS
```

## Partition layout

The 44-part CSV layout is independent of the 92-part Parquet layout. CSV uses 1,000,000 rows per observation part except the final 800,000-row part.
