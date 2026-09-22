# Mendeley Description

This dataset provides a one-year, context-aware synthetic IoT benchmark for smart waste-management research in Dhaka, Bangladesh. It represents 5,000 persistent synthetic smart-bin digital twins simulated hourly throughout 2025, producing exactly 43,800,000 observations.

The simulation includes land-use-specific activity, population density and catchment effects, institutional and market schedules, waste composition, informal recovery, weather seasonality, Ramadan and Eid scenarios, collection accessibility, overflow dynamics, and IoT sensor behaviour. The dataset contains 59 hourly observation variables and 29 persistent bin-level variables.

Geographic coordinates are synthetic points generated around representative Dhaka neighborhood centers and do not correspond to real municipal smart-bin locations.

The public release is distributed as 92 Parquet observation files grouped into 23 ZIP archives, together forming one logical dataset. Persistent bin metadata are provided separately in `bins.parquet`.
