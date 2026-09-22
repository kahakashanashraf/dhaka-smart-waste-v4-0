# Data Generation Methodology
## Dhaka Smart Waste Synthetic IoT Dataset V4.0 — One-Year 2025

### Scope

The Dhaka Smart Waste Synthetic IoT Dataset V4.0 is a deterministic, scenario-based urban digital-twin simulation for smart-waste, IoT, spatiotemporal, collection-planning, sensor-quality, and urban-analytics research.

The released data are **synthetic**. They are not observations from deployed municipal smart bins. The synthetic coordinates do not identify real municipal bin locations. Calendar/climate anchors and selected waste-management parameters are informed by documented external sources; fine-grained behavioral coefficients are transparent simulation assumptions implemented directly in `generate_v4_0.py`.

### Canonical dimensions

- Persistent synthetic bins: **5,000**
- Period: **1 January 2025 00:00 through 31 December 2025 23:00**
- Timezone: **Asia/Dhaka (UTC+06:00)**
- Days: **365**
- Hours per bin: **8,760**
- Hourly observations: **43,800,000**
- Fixed NumPy random seed: **20260902**
- Canonical generator: `generate_v4_0.py`
- Canonical validation: `validate_v4_0.py`
- Release-layout validation: `validate_export_parts.py`

### Generation pipeline

The simulator follows this causal sequence:

`land-use subtype → catchment/density → calendar/activity → gross waste generation → dynamic composition → informal recovery → residual mass → composition-weighted bulk density → waste volume → bin fill → collection/accessibility → overflow → forecast → IoT sensor observation/faults`

The fill level is therefore not sampled independently. Waste generation and composition first determine mass and bulk density; those determine waste volume, which determines the latent bin fill level.

### Persistent smart-bin population

The 5,000 bins are assigned exact main-area counts:

| Area type | Bins |
|---|---:|
| Residential | 1,300 |
| Commercial | 700 |
| Slum / informal settlement | 800 |
| Market | 700 |
| Office | 600 |
| Education | 350 |
| Garments | 200 |
| Recreation | 350 |
| **Total** | **5,000** |

Land-use subtypes include Apartment Residential, Dense Residential, Shopping, Restaurant/Food Zone, Mixed Commercial, Informal Settlement, Fish Market, Vegetable Market, General Market, Government Office, Private Office, School, College/University, Garment Factory, Park, Playground, and Entertainment Center.

Synthetic neighborhood counts are:

| Neighborhood | Bins |
|---|---:|
| Mirpur | 1,046 |
| Gulshan/Banani | 1,023 |
| Dhanmondi | 997 |
| Old Dhaka | 972 |
| Motijheel | 962 |

Latitude and longitude are generated around fixed neighborhood centers with Gaussian perturbations. They are synthetic locations, not real bin coordinates.

### Density, catchment, income and baseline generation

Each bin receives a Low, Medium, or High population-density category. The density probabilities depend on land use. Density multipliers are 0.85, 1.00 and 1.15 respectively.

A synthetic `catchment_population_equivalent` is generated from the density class. Market, Commercial and Recreation bins can receive a larger upper range because their catchments represent visitors/users in addition to residents.

Residential and informal-settlement bins use income-associated per-capita waste anchors:

| Income band | kg/person/day |
|---|---:|
| Low | 0.270 |
| Lower-middle | 0.305 |
| Middle | 0.371 |
| Upper-middle | 0.389 |
| High | 0.504 |

Residential baseline generation combines catchment population, per-capita waste, bin-capture fraction, density multiplier, and small bin-level lognormal heterogeneity.

Non-residential subtypes use subtype-specific baseline kg/h values scaled by equivalent catchment load, density and bin-level heterogeneity. Examples include Fish Market 1.40 kg/h, Vegetable Market 1.20 kg/h, Restaurant/Food Zone 1.12 kg/h, Garment Factory 1.00 kg/h, School 0.50 kg/h and Park 0.44 kg/h at the reference load.

### Static infrastructure and service characteristics

Each persistent bin also receives synthetic values for:

- bin volume
- placement
- nearby business type
- nearby point of interest
- road accessibility
- collection service level
- collection interval
- informal recovery rate
- collection threshold
- battery-drain rate
- Friday-prayer multiplier
- Eid-ul-Adha multiplier

Container volumes are selected from 240 L, 360 L, 660 L and 1,100 L according to land-use-specific probabilities.

Road accessibility is Easy, Moderate or Difficult. Collection service level is generated conditionally as Good, Moderate or Limited. Collection thresholds are primarily 75%, 80% or 85% according to density, with additional adjustments for market and informal-settlement contexts.

### 2025 calendar and event context

The complete 2025 calendar is represented at hourly resolution.

- Weekend: **Friday–Saturday**
- Special working Saturdays: **17 May 2025** and **24 May 2025**
- Ramadan simulation window: **2–30 March 2025**
- Eid-ul-Fitr day: **31 March 2025**
- Eid-ul-Fitr simulation holiday window: **29 March–3 April 2025**
- Eid-ul-Adha day: **7 June 2025**
- Eid-ul-Adha simulation holiday window: **5–12 June 2025**
- School Ramadan break: **2 March–7 April**
- School summer/Eid break: **1–19 June**
- School Durga break: **28 September–7 October**

Other public-holiday labels are also encoded in the generator. School, college/university and office open/closed states are represented separately.

### Synthetic weather

Weather is synthetic but calibrated to Dhaka monthly climate normals documented in `RESEARCH_CALIBRATION.md`.

Monthly rainfall targets in mm are:

| Month | mm |
|---|---:|
| Jan | 7.5 |
| Feb | 23.7 |
| Mar | 48.2 |
| Apr | 148.5 |
| May | 299.5 |
| Jun | 311.8 |
| Jul | 362.5 |
| Aug | 296.0 |
| Sep | 235.4 |
| Oct | 165.4 |
| Nov | 14.2 |
| Dec | 16.0 |

Hourly weather state is Sunny, Cloudy, Rainy or Storm. Rainfall is sampled for rainy/storm hours and rescaled month-by-month so the synthetic monthly total matches the configured normal. Temperature combines a monthly normal, diurnal cycle, slowly varying daily anomaly, weather-state adjustment and small random noise. Humidity is generated from monthly, diurnal and weather-state components.

The weather series is **not actual hourly 2025 Dhaka weather**.

### Hourly activity

Each land-use subtype receives its own hourly activity pattern. Examples include residential morning/evening peaks, fish-market early-morning peaks, vegetable-market morning peaks, daytime office/school activity, garment-factory operating hours, and stronger evening/weekend recreation activity.

Ramadan, institutional closure, weekend, holiday, rain/storm and other context flags modify relevant activity patterns.

### Special contextual effects

A Friday-prayer scenario applies to mosque-adjacent bins during the Friday 12:00–14:00 window. The bin-specific multiplier is sampled within the range implemented by the generator.

Eid-ul-Adha produces the strongest exceptional pulse, especially for Residential and Informal Settlement contexts, and also changes residual waste composition toward animal residue. Eid-ul-Fitr applies a weaker event effect to selected household, commercial and recreation contexts.

These multiplier magnitudes are simulation assumptions rather than field-measured effect sizes.

### Gross waste generation

For bin `i` at time `t`, the model can be summarized as:

`gross_generation(i,t) = baseline(i) × activity(i,t) × contextual_effects(i,t) × hourly_stochastic_factor(i,t)`

The hourly stochastic term is lognormal and centered so its expected multiplier remains approximately one.

### Dynamic eight-component composition

Residual waste is represented by eight components:

1. organic food
2. fish/meat
3. animal residue
4. plastic
5. paper/cardboard
6. textile
7. metal/glass
8. green/other

Each land-use subtype has a fixed base vector. Small hourly perturbations are added, followed by clipping and renormalization. Calendar events can alter selected shares; notably Eid-ul-Adha strongly increases animal residue for affected contexts.

### Informal recovery before bin entry

Recyclable recovery is modeled before residual waste enters the bin. Plastic, paper/cardboard, textile and metal/glass are treated as recyclable components. The recovery fraction depends on the bin-specific recovery parameter, the current recyclable share and a bounded stochastic factor.

The recovered recyclable mass is removed from gross waste, and the residual composition is renormalized.

### Mass-to-volume conversion

The model separates mass and volume. Residual bulk density is computed from the composition-weighted component densities:

| Component | Synthetic bulk density (kg/m³) |
|---|---:|
| Organic food | 260 |
| Fish/meat | 520 |
| Animal residue | 560 |
| Plastic | 70 |
| Paper/cardboard | 90 |
| Textile | 110 |
| Metal/glass | 900 |
| Green/other | 180 |

Residual volume is calculated as:

`volume_liter = waste_entering_bin_kg / bulk_density_kg_m3 × 1000`

### Fill and overflow

Each bin starts with a small initial volume. Incoming residual waste volume is added hour-by-hour.

`true_fill_level_percent` is the latent physical fill value derived from waste volume and bin capacity.

`needs_collection` is rule-derived:

`needs_collection = true_fill_level_percent >= collection_threshold_percent`

Any volume above physical capacity is recorded as overflow and converted back to mass using current mixture density.

### Collection process

A collection becomes due when fill exceeds the threshold and enough time has elapsed since the previous collection. Collection success depends on service level, road accessibility, weather and selected event conditions. Emergency collection can occur for a fully filled bin.

Collection delay includes time accumulated after a collection becomes due plus an access/weather-dependent arrival component. After collection, a small residual quantity remains rather than resetting every bin to exactly zero.

### Four-hour operational forecast

The dataset includes `predicted_fill_level_percent` and `predicted_overflow_kg_4h`.

These are generated operational forecast features derived from current state and expected short-horizon waste input, with a small forecast-error term. They are **not predictions from a separately trained machine-learning model**.

### IoT sensor simulation

The simulator distinguishes latent physical state from observed sensor state.

- `true_fill_level_percent`: latent volume-derived state.
- `fill_level_percent`: noisy sensor observation.
- Sensor noise for fill: Gaussian, sigma approximately 1.5 percentage points.
- Packet loss baseline probability: approximately 0.005, with additional context effects.
- Sensor anomaly probability: approximately 0.001 when a packet is available.
- Anomalies include saturation-low, saturation-high and spike behavior.
- During packet loss, selected sensor readings are missing while latent physical state continues to evolve.
- Battery level drains over time and can receive maintenance/replacement.

### Composition storage

The residual composition is stored as integer percentages. After rounding, the rounding difference is assigned to the dominant component so that the eight percentages sum to exactly 100 for every observation.

### Canonical state and public release

The generator writes the canonical state to:

`dhaka_smart_waste_v4_0_2025.h5`

with separate persistent `bins` and hourly `observations` groups.

The public observation release contains **92 Parquet files**:

- `observations_part_000.parquet` through `observations_part_090.parquet`: **480,000 rows each**
- `observations_part_091.parquet`: **120,000 rows**

Total:

`91 × 480,000 + 120,000 = 43,800,000`

For transport, the 92 observation files are grouped into **23 ZIP archives**. The ZIP split has no analytical meaning; all Parquet parts form one logical observation table.

Persistent bin metadata are distributed separately as `bins.parquet` and join to hourly observations via `bin_index`.

### Canonical validation

`validate_v4_0.py` performs full-data structural and scenario checks. The recorded validation includes:

- exactly 43,800,000 observations
- exactly 5,000 bins
- 8,760 hourly records per bin by design
- all eight residual-composition percentages sum to 100
- `needs_collection` agrees with the threshold rule
- packet-loss and sensor-anomaly rates
- informal recovery and organic-family residual share
- subtype-specific composition checks
- school open/closed comparison
- recreation weekend/weekday comparison
- density-generation gradient
- Eid-ul-Fitr and Eid-ul-Adha scenario comparisons
- Friday mosque-window effect
- collection-delay pattern by accessibility
- monthly climate checks

`VALIDATION_REPORT.json` stores the recorded canonical-state results.

These are **internal simulation-validation checks**, not field validation.

### Reproduction

See `REPRODUCIBILITY.md` for exact commands, environment-recording limitations, software requirements, expected outputs, validation steps and release verification.
