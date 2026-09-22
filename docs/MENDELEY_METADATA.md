# Mendeley Release Metadata

## Title

A One-Year Context-Aware Synthetic IoT Dataset for Smart Waste Management in Dhaka, Bangladesh: 43.8 Million Hourly Observations

## License

CC BY 4.0 (Creative Commons Attribution 4.0 International)

## Description

This dataset provides a one-year, context-aware synthetic IoT benchmark for smart waste-management research in Dhaka, Bangladesh. It represents 5,000 persistent synthetic smart-bin digital twins simulated hourly throughout 2025, producing exactly 43,800,000 observations.

The simulation includes land-use-specific activity, population density and catchment effects, institutional and market schedules, waste composition, informal recovery, weather seasonality, Ramadan and Eid scenarios, collection accessibility, overflow dynamics, and IoT sensor behaviour. The dataset contains 59 hourly observation variables and 29 persistent bin-level variables.

Geographic coordinates are synthetic points generated around representative Dhaka neighborhood centers and do not correspond to real municipal smart-bin locations.

The public release is distributed as 92 Parquet observation files grouped into 23 ZIP archives, together forming one logical dataset. Persistent bin metadata are provided separately in `bins.parquet`.

## Steps to reproduce

1. Install Python 3 and the required packages:

   `pip install -r requirements.txt`

2. Generate the complete synthetic dataset:

   `python generate_v4_0.py`

3. Validate the generated dataset:

   `python validate_v4_0.py`

4. Validate the Parquet release:

   `python validate_export_parts.py`

The generator uses the fixed NumPy random seed `20260902`. The expected output contains 5,000 persistent synthetic bins, 8,760 hourly observations per bin, and exactly 43,800,000 hourly observations for 2025.

## Public release layout

- 23 ZIP transport archives
- 92 Parquet observation files
- parts 000–090: 480,000 rows each
- part 091: 120,000 rows
- total observation rows: 43,800,000
- persistent bin table: `bins.parquet`
