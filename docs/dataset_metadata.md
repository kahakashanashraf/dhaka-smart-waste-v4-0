# Dataset Metadata

| key | value |
| --- | --- |
| climate_calibration | Dhaka monthly mean temperature and precipitation normals from JMA/Tokyo Climate Center ClimatView. |
| dataset_title | Dhaka Smart Waste Synthetic IoT Dataset V4.0 — One-Year 2025 |
| eid_holiday_window | 2025-06-05..2025-06-12 |
| eid_ul_adha_2025_date | 2025-06-07 |
| eid_ul_fitr_2025_date | 2025-03-31 |
| eid_ul_fitr_holiday_window | 2025-03-29..2025-04-03 |
| end_local | 2025-12-31T23:00:00+06:00 |
| method_note | One-year scenario-based synthetic digital twin. Calendar/climate anchors and selected waste parameters are literature-calibrated; fine-grained behavioral multipliers are transparent simulation assumptions, not direct field measurements. |
| n_bins | 5000 |
| n_days | 365 |
| n_rows | 43800000 |
| packet_loss_probability | 0.005 |
| ramadan_2025_window | 2025-03-02..2025-03-30 |
| school_durga_break | 2025-09-28..2025-10-07 |
| school_ramadan_break | 2025-03-02..2025-04-07 |
| school_summer_eid_break | 2025-06-01..2025-06-19 |
| seed | 20260902 |
| sensor_anomaly_probability | 0.001 |
| sensor_noise_sigma_fill_percent | 1.5 |
| special_working_days | 2025-05-17;2025-05-24 |
| start_local | 2025-01-01T00:00:00+06:00 |
| synthetic_coordinates | True |
| timezone | Asia/Dhaka (UTC+06:00) |
| version | 4.0 |
| weekend_definition | Friday-Saturday |
| bins.base_composition_categories | ["organic_food", "fish_meat", "animal_residue", "plastic", "paper_cardboard", "textile", "metal_glass", "green_other"] |
| observations.composition_note | Eight percentage fields describe residual waste entering the bin after synthetic informal recovery and sum to exactly 100. |
| observations.dominant_waste_categories | ["organic_food", "fish_meat", "animal_residue", "plastic", "paper_cardboard", "textile", "metal_glass", "green_other"] |
| observations.event_categories | ["Normal", "Weekend", "Public Holiday", "Eid-ul-Fitr Holiday", "Eid-ul-Fitr", "Eid-ul-Adha Holiday", "Eid-ul-Adha", "Durga Puja Holiday"] |
| observations.fill_note | true_fill_level is latent volume-based ground truth; fill_level is noisy sensor observation and is NaN during packet loss. |
| observations.holiday_categories | ["None", "Shab-e-Barat", "Language Martyrs Day", "Independence Day", "Shab-e-Qadr/Jumuatul-Wida", "Eid-ul-Fitr", "Bangla New Year", "May Day", "Buddha Purnima", "Eid-ul-Adha", "Ashura", "Janmashtami", "Eid-e-Milad-un-Nabi", "Durga Puja", "Victory Day", "Christmas Day"] |
| observations.institution_status_categories | ["Not applicable", "Open", "Closed"] |
| observations.season_categories | ["Winter", "Pre-monsoon", "Monsoon", "Post-monsoon"] |
| observations.sensor_error_categories | ["none", "saturation_low", "saturation_high", "spike"] |
| observations.time_slot_categories | ["Night", "Morning", "Afternoon", "Evening"] |
| observations.weather_categories | ["Sunny", "Cloudy", "Rainy", "Storm"] |
| release_observation_format | Parquet only |
| generator_file | generate_v4_0.py |
| canonical_validation_file | validate_v4_0.py |
| release_validation_file | validate_export_parts.py |
| environment_capture_file | capture_environment.py |
| gpu_required | False |
| original_runtime_hardware_recorded | False |
| parquet_observation_parts | 92 |
| parquet_partition_rows | parts 000-090: 480000 each; part 091: 120000 |
| parquet_total_rows | 43800000 |
| transport_zip_archives | 23 |
| software_language | Python 3 |
| verified_software_environment | CPython 3.13.5; numpy 2.3.5; h5py 3.15.1; pandas 2.2.3; thrift 0.20.0 |
