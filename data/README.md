# Data files in this repository

The complete hourly observation dataset contains 43,800,000 rows and is multi-gigabyte, so the full observation partitions are maintained in the archival/Drive release rather than duplicated in the normal Git history.

## Data committed directly to GitHub

- `bins.parquet` — complete persistent bin metadata table: 5,000 rows, 29 columns.
- `bins.csv.gz` — compressed CSV copy of the same complete persistent bin metadata table.
- `CSV_MANIFEST.csv` — complete 44-part CSV/GZIP observation manifest.
- `../sample/bins_sample_10.csv` — browser-viewable bin sample.
- `../sample/observations_sample_10.csv` — browser-viewable hourly observation sample.

## Full observation data

- CSV/GZIP (44 parts, 43,800,000 rows): https://drive.google.com/drive/folders/16JeuImcx-pDF01ydejQWKOOUEmcC0Y2m
- Parquet (92 parts grouped into 23 ZIP archives, 43,800,000 rows): https://drive.google.com/drive/folders/1TseLOtPXKv5t3wrujbpQFx9bRIXMYN8d
- Mendeley Data V4 DOI: https://doi.org/10.17632/ctt5kwppwt.4

All observation partitions form one logical hourly table. Join observations to the persistent bin table using `bin_index`.
