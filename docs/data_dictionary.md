# Data Dictionary

| table | column | type | unit_or_encoding | description | status |
| --- | --- | --- | --- | --- | --- |
| bins | bin_index | int32 | index | Join key linking bins and hourly observations. | Synthetic/generated |
| bins | bin_id | string | - | Persistent synthetic smart-bin identifier. | Synthetic/generated |
| bins | city | string | - | City label; all records are Dhaka. | Synthetic/generated |
| bins | area_type | string | category | Main land-use/urban context class. | Synthetic/generated |
| bins | land_use_subtype | string | category | Detailed source context such as Fish Market, School, Restaurant/Food Zone, Garment Factory, or Park. | Synthetic/generated |
| bins | neighborhood | string | category | Synthetic neighborhood assignment among Mirpur, Gulshan/Banani, Dhanmondi, Old Dhaka, and Motijheel. | Synthetic/generated |
| bins | bin_volume_liter | float32 | L | Synthetic physical bin volume. | Synthetic/generated |
| bins | nominal_mass_capacity_kg | float32 | kg | Descriptive nominal mass capacity; true fill is volume-based. | Synthetic/generated |
| bins | latitude | float32 | degrees | Synthetic coordinate near a neighborhood center; not an observed municipal bin coordinate. | Synthetic/generated |
| bins | longitude | float32 | degrees | Synthetic coordinate near a neighborhood center; not an observed municipal bin coordinate. | Synthetic/generated |
| bins | placement | string | category | Synthetic placement context. | Synthetic/generated |
| bins | nearby_business_type | string | category | Nearby business/context type used for scenario diversity. | Synthetic/generated |
| bins | nearby_poi_type | string | category | Nearby point-of-interest class; Mosque enables Friday prayer-window effect. | Synthetic/generated |
| bins | population_density | string | category | Low/Medium/High synthetic catchment-density class. | Synthetic/generated |
| bins | catchment_population_equivalent | int32 | people-equivalent | Synthetic equivalent population/visitor load served by the bin. | Synthetic/generated |
| bins | income_band | string | category | Synthetic residential income band; NA for non-residential bins. | Synthetic/generated |
| bins | per_capita_waste_kg_day | float32 | kg/person/day | Residential literature-calibrated per-capita generation parameter with stochastic variation. | Synthetic/generated |
| bins | bin_capture_fraction | float32 | fraction | Fraction of catchment household waste assumed to enter the represented bin. | Synthetic/generated |
| bins | density_load_multiplier | float32 | multiplier | Scenario multiplier translating catchment density into bin pressure. | Synthetic/generated |
| bins | baseline_generation_kg_per_hour | float32 | kg/h | Per-bin baseline generation before hourly/context/event multipliers. | Synthetic/generated |
| bins | road_accessibility | string | category | Easy/Moderate/Difficult synthetic collection-access class. | Synthetic/generated |
| bins | collection_service_level | string | category | Good/Moderate/Limited service class. | Synthetic/generated |
| bins | collection_interval_hours | uint8 | h | Nominal collection interval. | Synthetic/generated |
| bins | informal_recovery_rate | float32 | fraction | Scenario rate controlling pre-bin recovery of recyclable fractions. | Synthetic/generated |
| bins | collection_threshold_percent | float32 | % | Fill threshold for needs_collection. | Synthetic/generated |
| bins | battery_drain_percent_per_hour | float32 | percentage points/h | Synthetic hourly battery drain parameter. | Synthetic/generated |
| bins | friday_prayer_multiplier | float32 | multiplier | Scenario multiplier applied to mosque-adjacent bins on Friday 12:00-14:00. | Synthetic/generated |
| bins | eid_day_multiplier | float32 | multiplier | Eid-ul-Adha day generation multiplier by source context. | Synthetic/generated |
| bins | base_composition_percent | float32[8] | % | Base 8-part waste-composition vector before hourly perturbation and recovery. | Synthetic/generated |
| observations | bin_index | int32 | index | Join key to bins table. | Synthetic/generated |
| observations | timestamp_unix | int64 | seconds since epoch | Hourly timestamp stored as Unix time; interpret in Asia/Dhaka UTC+06:00. | Synthetic/generated |
| observations | date_index | uint16 | days from 2025-01-01 | Zero-based day index. | Synthetic/generated |
| observations | day_of_week | uint8 | 0=Monday..6=Sunday | Calendar weekday. | Synthetic/generated |
| observations | hour | uint8 | 0-23 | Local hour of day. | Synthetic/generated |
| observations | time_slot_code | uint8 | lookup | Night/Morning/Afternoon/Evening code. | Synthetic/generated |
| observations | event_code | uint8 | lookup | Mutually exclusive high-level event state. | Synthetic/generated |
| observations | is_weekend | uint8 | 0/1 | Friday-Saturday weekend flag, excluding special government working Saturdays. | Synthetic/generated |
| observations | is_public_holiday | uint8 | 0/1 | Government/public holiday calendar flag used by the simulation. | Synthetic/generated |
| observations | holiday_code | uint8 | lookup | Holiday identity code. | Synthetic/generated |
| observations | season_code | uint8 | lookup | Winter/Pre-monsoon/Monsoon/Post-monsoon. | Synthetic/generated |
| observations | weather_code | uint8 | lookup | Sunny/Cloudy/Rainy/Storm synthetic weather state. | Synthetic/generated |
| observations | rainfall_mm_hour | float32 | mm/h | Citywide synthetic hourly rainfall; monthly sums are calibrated to Dhaka climate normals. | Synthetic/generated |
| observations | temperature_c | float32 | °C | Synthetic sensor-observed temperature with diurnal/monthly seasonality. | Synthetic/generated |
| observations | humidity_percent | float32 | % | Synthetic humidity observation. | Synthetic/generated |
| observations | institution_status_code | uint8 | lookup | Open/Closed/Not applicable for education and office contexts. | Synthetic/generated |
| observations | school_calendar_closed | uint8 | 0/1 | Closure flag based on 2025 secondary-school long breaks, weekends and public holidays. | Synthetic/generated |
| observations | college_calendar_closed | uint8 | 0/1 | Scenario college/university closure flag based on public holidays/weekends/Eid blocks. | Synthetic/generated |
| observations | office_calendar_closed | uint8 | 0/1 | Government-style office closure flag, including 2025 special working-day overrides. | Synthetic/generated |
| observations | is_special_working_day | uint8 | 0/1 | Flags 17 and 24 May 2025, declared working Saturdays. | Synthetic/generated |
| observations | activity_multiplier | float32 | multiplier | Land-use/hour/calendar/weather activity multiplier. | Synthetic/generated |
| observations | gross_waste_generation_kg | float32 | kg/h | Waste generated before informal recyclable recovery. | Synthetic/generated |
| observations | informal_recovery_kg | float32 | kg/h | Synthetic material recovered before residual waste enters the bin. | Synthetic/generated |
| observations | waste_entering_bin_kg | float32 | kg/h | Residual waste entering the bin after informal recovery. | Synthetic/generated |
| observations | waste_volume_liter | float32 | L/h | Residual waste volume derived from mass and composition-dependent bulk density. | Synthetic/generated |
| observations | waste_bulk_density_kg_m3 | float32 | kg/m³ | Synthetic mixture bulk density. | Synthetic/generated |
| observations | organic_food_pct | uint8 | % | Residual organic/food composition share. | Synthetic/generated |
| observations | fish_meat_pct | uint8 | % | Residual fish/meat composition share. | Synthetic/generated |
| observations | animal_residue_pct | uint8 | % | Residual animal-residue composition share, strongly elevated on Eid-ul-Adha. | Synthetic/generated |
| observations | plastic_pct | uint8 | % | Residual plastic share. | Synthetic/generated |
| observations | paper_cardboard_pct | uint8 | % | Residual paper/cardboard share. | Synthetic/generated |
| observations | textile_pct | uint8 | % | Residual textile share. | Synthetic/generated |
| observations | metal_glass_pct | uint8 | % | Residual metal/glass share. | Synthetic/generated |
| observations | green_other_pct | uint8 | % | Residual green/other share. | Synthetic/generated |
| observations | dominant_waste_code | uint8 | lookup | Dominant residual composition category. | Synthetic/generated |
| observations | true_fill_level_percent | float32 | % | Latent volume-based true fill level. | Synthetic/generated |
| observations | fill_level_percent | float32 | % | Noisy observed fill sensor; NaN during packet loss. | Synthetic/generated |
| observations | predicted_fill_level_percent | float32 | % | Four-hour operational fill forecast, clipped to 0-100. | Synthetic/generated |
| observations | collection_threshold_percent | float32 | % | Per-bin operational threshold repeated for modeling convenience. | Synthetic/generated |
| observations | needs_collection | uint8 | 0/1 | Rule-derived label: true_fill_level_percent >= collection_threshold_percent. | Synthetic/generated |
| observations | is_collection_due | uint8 | 0/1 | True when threshold and interval conditions make collection due. | Synthetic/generated |
| observations | collection_event | uint8 | 0/1 | Simulated successful/emergency collection event. | Synthetic/generated |
| observations | hours_since_last_collection | float32 | h | Hours since most recent collection before current decision. | Synthetic/generated |
| observations | collection_delay_minutes | float32 | min | Simulated due/arrival delay influenced by road access, service and weather. | Synthetic/generated |
| observations | overflow_kg | float32 | kg | True overflow mass for the current hour. | Synthetic/generated |
| observations | predicted_overflow_kg_4h | float32 | kg | Four-hour predicted overflow mass. | Synthetic/generated |
| observations | battery_level_percent | float32 | % | Observed battery level; NaN during packet loss. | Synthetic/generated |
| observations | battery_maintenance_event | uint8 | 0/1 | Battery replacement/maintenance event when low state is serviced. | Synthetic/generated |
| observations | is_packet_loss | uint8 | 0/1 | Injected telemetry packet-loss flag. | Synthetic/generated |
| observations | is_sensor_anomaly | uint8 | 0/1 | Injected sensor-anomaly flag. | Synthetic/generated |
| observations | sensor_error_code | uint8 | lookup | Anomaly type: none/saturation/spike. | Synthetic/generated |
| observations | is_friday_prayer_window | uint8 | 0/1 | Friday 12:00-14:00 calendar window. | Synthetic/generated |
| observations | friday_effect_active | uint8 | 0/1 | Friday prayer multiplier active for mosque-adjacent bin. | Synthetic/generated |
| observations | is_ramadan | uint8 | 0/1 | Ramadan 2025 flag (2-30 March in the simulator). | Synthetic/generated |
| observations | is_eid_fitr_period | uint8 | 0/1 | Eid-ul-Fitr holiday window flag (29 Mar-3 Apr). | Synthetic/generated |
| observations | is_eid_fitr_day | uint8 | 0/1 | Eid-ul-Fitr day flag (31 Mar). | Synthetic/generated |
| observations | is_eid_period | uint8 | 0/1 | Eid-ul-Adha extended holiday window flag (5-12 Jun). | Synthetic/generated |
| observations | is_eid_day | uint8 | 0/1 | Eid-ul-Adha day flag (7 Jun). | Synthetic/generated |
| observations | is_durga_puja_school_break | uint8 | 0/1 | School Durga Puja break window flag (28 Sep-7 Oct). | Synthetic/generated |
