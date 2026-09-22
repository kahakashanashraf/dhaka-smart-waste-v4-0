# Technical Validation — auto-generated draft

The released Dhaka Smart Waste Synthetic IoT Dataset V4.0 was subjected to a reviewer-oriented, full-data technical validation. The validation scanned all `43,800,000` hourly observations and passed. Because the dataset is synthetic, these tests establish internal structural consistency, rule consistency, reproducibility of the release layout, and statistical behavior of the simulation; they should not be described as field validation of deployed municipal smart bins.

## Structural integrity

The release was checked for the canonical 5,000 persistent bins, 92 observation Parquet parts, and 43,800,000 hourly records. Each bin is expected to contribute 8,760 bin-hour records covering the 2025 calendar. Full key-coverage validation found `0` duplicate bin-hour keys and `0` missing keys. The minimum and maximum records per bin were `8,760` and `8,760`, respectively.

Persistent metadata were read from `/content/drive/MyDrive/Dhaka Smart Waste V4.0 2025/PARQUET_PARTS/bins.parquet`. `bins.parquet` present in the current Drive release tree: **True**.

## Logical and physical consistency

The validation checks mass balance (`gross waste − informal recovery = waste entering the bin`), mass-to-volume conversion, eight-component composition summing to 100%, fill-level bounds, collection-threshold logic, overflow constraints, battery bounds, and the relationship between collection-due and collection-need indicators. Counts for every hard invariant are saved in `validation_summary.csv` and `VALIDATION_REPORT.json`.

## Sensor behavior

The observed packet-loss rate was `0.4712%`. Among available packets, the sensor-anomaly rate was `0.1000%`. Excluding packet losses and deliberately injected anomalies, the fill-sensor residual had mean `0.0002` percentage points and standard deviation `1.5000` percentage points, consistent with the approximately 1.5-percentage-point Gaussian noise configured by the generator, subject to 0–100% clipping.

## Calendar and climate calibration

Calendar flags for weekends, Ramadan, Eid-ul-Fitr, and Eid-ul-Adha were independently reconstructed from dates and compared with the released fields. Monthly synthetic rainfall totals were compared with the configured Dhaka climate-normal targets; detailed month-level values are provided in `monthly_climate_validation.csv` and `figure_monthly_rainfall_validation.png`.

## Dynamic and scenario checks

A deterministic 64-bin temporal sample was used to evaluate sequential behavior and the operational four-hour fill forecast. For forecast instances with no collection during the four-hour horizon, the mean absolute error was `2.0403` percentage points (n=`514,552`). Scenario-level summaries quantify school open/closed behavior, recreation weekend/weekday behavior, Eid-ul-Adha effects, waste-composition shifts, Friday mosque-window behavior, density gradients, and collection delay by road accessibility. These directional checks validate implementation of the stated simulation assumptions; they are not independent empirical estimates of real-world effect sizes.

## Reproducibility note

The generator uses the fixed NumPy seed `20260902`. For a publication archive, the generator, this validator, the release-layout files, software requirements, and the generated `VALIDATION_REPORT.json` should be deposited together with the dataset.
