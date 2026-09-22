#!/usr/bin/env python3
"""Reviewer-oriented technical validation for Dhaka Smart Waste V4.0.

This script validates the *released Parquet package*, not only the generator.
It scans all 43.8M hourly observations out-of-core with PyArrow, checks
structural and logical invariants, summarizes scenario behavior, and writes
paper-ready tables/figures plus a machine-readable JSON report.

The data are synthetic; these checks establish internal consistency,
reproducibility, and plausibility of the encoded simulation rules. They do
not constitute field validation of deployed Dhaka smart bins.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
import zipfile
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd

try:
    import pyarrow.parquet as pq
except ImportError as exc:
    raise SystemExit("pyarrow is required. Install with: pip install pyarrow") from exc

# ----------------------------- Canonical constants -----------------------------
N_BINS = 5_000
N_DAYS = 365
HOURS_PER_DAY = 24
N_HOURS = N_DAYS * HOURS_PER_DAY
N_ROWS = N_BINS * N_HOURS
N_OBS_FILES = 92
START_LOCAL = datetime(2025, 1, 1, tzinfo=timezone(timedelta(hours=6)))
START_TS = int(START_LOCAL.timestamp())
SEED = 20260902

EXPECTED_AREA_COUNTS = {
    "Residential": 1300, "Commercial": 700, "Slum": 800, "Market": 700,
    "Office": 600, "Education": 350, "Garments": 200, "Recreation": 350,
}
EXPECTED_NEIGHBORHOOD_COUNTS = {
    "Mirpur": 1046, "Gulshan/Banani": 1023, "Dhanmondi": 997,
    "Old Dhaka": 972, "Motijheel": 962,
}
MONTHLY_PRECIP_MM = {
    1: 7.5, 2: 23.7, 3: 48.2, 4: 148.5, 5: 299.5, 6: 311.8,
    7: 362.5, 8: 296.0, 9: 235.4, 10: 165.4, 11: 14.2, 12: 16.0,
}
MONTHLY_MEAN_TEMP_C = {
    1: 18.2, 2: 21.7, 3: 26.2, 4: 28.4, 5: 28.5, 6: 29.2,
    7: 28.9, 8: 29.0, 9: 28.9, 10: 27.6, 11: 23.7, 12: 19.6,
}
COMPOSITION_COLS = [
    "organic_food_pct", "fish_meat_pct", "animal_residue_pct", "plastic_pct",
    "paper_cardboard_pct", "textile_pct", "metal_glass_pct", "green_other_pct",
]
REQUIRED_OBS_COLS = [
    "bin_index", "timestamp_unix", "date_index", "day_of_week", "hour",
    "event_code", "is_weekend", "is_public_holiday", "weather_code",
    "rainfall_mm_hour", "temperature_c", "humidity_percent",
    "school_calendar_closed", "college_calendar_closed", "office_calendar_closed",
    "gross_waste_generation_kg", "informal_recovery_kg", "waste_entering_bin_kg",
    "waste_volume_liter", "waste_bulk_density_kg_m3", *COMPOSITION_COLS,
    "true_fill_level_percent", "fill_level_percent", "predicted_fill_level_percent",
    "collection_threshold_percent", "needs_collection", "is_collection_due",
    "collection_event", "collection_delay_minutes", "overflow_kg",
    "predicted_overflow_kg_4h", "battery_level_percent", "battery_maintenance_event",
    "is_packet_loss", "is_sensor_anomaly", "sensor_error_code",
    "is_friday_prayer_window", "friday_effect_active", "is_ramadan",
    "is_eid_fitr_period", "is_eid_fitr_day", "is_eid_period", "is_eid_day",
]


def _safe_float(x):
    try:
        return float(x)
    except Exception:
        return None


def _status(ok: bool) -> str:
    return "PASS" if bool(ok) else "FAIL"


def _mean(sum_, count_):
    return float(sum_ / count_) if count_ else float("nan")


def _decode_scalar(x):
    """Normalize byte-like scalar metadata to plain UTF-8 text."""
    if isinstance(x, (bytes, bytearray, np.bytes_)):
        return bytes(x).decode("utf-8", errors="replace")
    return x


def _decode_bytes_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Decode byte-valued object/string columns emitted by some Parquet writers."""
    out = df.copy()
    for col in out.columns:
        if out[col].dtype == object:
            out[col] = out[col].map(_decode_scalar)
    return out


def _json_safe(obj):
    """Recursively convert bytes, NumPy objects and Paths to strict JSON types."""
    if isinstance(obj, dict):
        return {str(_decode_scalar(k)): _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [_json_safe(v) for v in obj]
    if isinstance(obj, (bytes, bytearray, np.bytes_)):
        return bytes(obj).decode("utf-8", errors="replace")
    if isinstance(obj, np.ndarray):
        return [_json_safe(v) for v in obj.tolist()]
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.floating):
        v = float(obj)
        return v if math.isfinite(v) else None
    if isinstance(obj, np.bool_):
        return bool(obj)
    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, float) and not math.isfinite(obj):
        return None
    return obj


def extract_release(project_root: Path, extract_dir: Path) -> tuple[list[Path], dict]:
    """Verify all transport ZIPs and extract/refresh the 92 logical Parquet parts."""
    zip_dir = project_root / "PARQUET_PARTS"
    zips = sorted(zip_dir.glob("dhaka_smart_waste_v4_0_PARQUET_PART_*_of_23.zip"))
    zip_info = {"zip_count": len(zips), "corrupt_zips": [], "members": []}
    extract_dir.mkdir(parents=True, exist_ok=True)

    # Always test archive integrity. A previous extracted cache must never cause a
    # false PASS for transport integrity. Also record the ZIP-to-Parquet mapping.
    expected_sizes = {}
    valid_archives = []
    for zp in zips:
        try:
            with zipfile.ZipFile(zp, "r") as zf:
                bad = zf.testzip()
                if bad is not None:
                    zip_info["corrupt_zips"].append(f"{zp.name}:{bad}")
                    continue
                valid_archives.append(zp)
                for info in zf.infolist():
                    if info.is_dir():
                        continue
                    name = Path(info.filename).name
                    zip_info["members"].append({
                        "archive": zp.name,
                        "member": name,
                        "uncompressed_bytes": int(info.file_size),
                        "compressed_bytes": int(info.compress_size),
                        "crc32": f"{info.CRC:08x}",
                    })
                    if re.fullmatch(r"observations_part_\d{3}\.parquet", name):
                        expected_sizes[name] = int(info.file_size)
        except zipfile.BadZipFile as exc:
            zip_info["corrupt_zips"].append(f"{zp.name}:BadZipFile:{exc}")

    existing = {p.name: p for p in extract_dir.glob("observations_part_*.parquet")}
    cache_ok = (
        len(existing) == N_OBS_FILES
        and len(expected_sizes) == N_OBS_FILES
        and all(name in existing and existing[name].stat().st_size == size
                for name, size in expected_sizes.items())
    )

    if not cache_ok:
        # Remove only our generated observation cache, then reconstruct it from
        # the verified transport archives. This avoids stale-part contamination.
        for p in extract_dir.glob("observations_part_*.parquet"):
            p.unlink(missing_ok=True)
        for zp in valid_archives:
            with zipfile.ZipFile(zp, "r") as zf:
                for info in zf.infolist():
                    name = Path(info.filename).name
                    if re.fullmatch(r"observations_part_\d{3}\.parquet", name):
                        target = extract_dir / name
                        with zf.open(info, "r") as src, target.open("wb") as dst:
                            import shutil
                            shutil.copyfileobj(src, dst, length=1024 * 1024)

    parquet_files = sorted(
        extract_dir.glob("observations_part_*.parquet"),
        key=lambda p: int(re.search(r"_(\d+)\.parquet$", p.name).group(1)),
    )
    zip_info["extracted_cache_reused"] = bool(cache_ok)
    return parquet_files, zip_info


def load_bins(project_root: Path) -> tuple[pd.DataFrame, str, bool]:
    """Prefer bins.parquet; fall back to bins.csv.gz; normalize text encoding."""
    candidates = [
        project_root / "PARQUET_PARTS" / "bins.parquet",
        project_root / "bins.parquet",
    ]
    for p in candidates:
        if p.exists():
            return _decode_bytes_dataframe(pd.read_parquet(p)), str(p), True
    csv_path = project_root / "CSV_PARTS" / "bins.csv.gz"
    if csv_path.exists():
        return _decode_bytes_dataframe(pd.read_csv(csv_path)), str(csv_path), False
    raise FileNotFoundError("Could not find bins.parquet or CSV_PARTS/bins.csv.gz")


def validate_bins(bins: pd.DataFrame) -> tuple[list[dict], dict]:
    checks = []
    metrics = {}

    def add(name, expected, observed, ok, severity="hard"):
        checks.append({"check": name, "expected": str(expected), "observed": str(observed),
                       "status": _status(ok), "severity": severity})

    add("Persistent bin count", N_BINS, len(bins), len(bins) == N_BINS)
    add("Unique bin_index", N_BINS, bins["bin_index"].nunique(), bins["bin_index"].nunique() == N_BINS)
    add("Unique bin_id", N_BINS, bins["bin_id"].nunique(), bins["bin_id"].nunique() == N_BINS)
    add("bin_index range", "0..4999", f"{bins.bin_index.min()}..{bins.bin_index.max()}",
        bins.bin_index.min() == 0 and bins.bin_index.max() == N_BINS - 1)

    area_counts = bins["area_type"].value_counts().to_dict()
    nb_counts = bins["neighborhood"].value_counts().to_dict()
    add("Exact area-type counts", EXPECTED_AREA_COUNTS, area_counts, area_counts == EXPECTED_AREA_COUNTS)
    add("Exact neighborhood counts", EXPECTED_NEIGHBORHOOD_COUNTS, nb_counts,
        nb_counts == EXPECTED_NEIGHBORHOOD_COUNTS)

    allowed_vol = {240.0, 360.0, 660.0, 1100.0}
    obs_vol = set(np.round(bins["bin_volume_liter"].dropna().astype(float), 6).unique())
    add("Allowed container volumes", sorted(allowed_vol), sorted(obs_vol), obs_vol <= allowed_vol)
    add("Collection threshold bounds", "0..100%",
        f"{bins.collection_threshold_percent.min():.3f}..{bins.collection_threshold_percent.max():.3f}",
        bins.collection_threshold_percent.between(0, 100).all())
    add("Informal recovery-rate bounds", "0..1",
        f"{bins.informal_recovery_rate.min():.6f}..{bins.informal_recovery_rate.max():.6f}",
        bins.informal_recovery_rate.between(0, 1).all())
    add("Synthetic latitude bounds", "plausible Dhaka envelope 23.60..23.90",
        f"{bins.latitude.min():.6f}..{bins.latitude.max():.6f}",
        bins.latitude.between(23.60, 23.90).all(), "soft")
    add("Synthetic longitude bounds", "plausible Dhaka envelope 90.25..90.55",
        f"{bins.longitude.min():.6f}..{bins.longitude.max():.6f}",
        bins.longitude.between(90.25, 90.55).all(), "soft")

    # Base composition is serialized as 8 semicolon-separated percentages in CSV.
    if "base_composition_percent" in bins.columns:
        comp = bins["base_composition_percent"].astype(str).str.split(";", expand=True).apply(pd.to_numeric, errors="coerce")
        comp_sum = comp.sum(axis=1)
        add("Static base composition has 8 components", 8, comp.shape[1], comp.shape[1] == 8)
        add("Static base composition sums to ~100%", "100% ± 0.01",
            f"min={comp_sum.min():.6f}, max={comp_sum.max():.6f}",
            np.allclose(comp_sum.to_numpy(), 100.0, atol=0.01))

    metrics["area_counts"] = area_counts
    metrics["neighborhood_counts"] = nb_counts
    metrics["latitude_range"] = [float(bins.latitude.min()), float(bins.latitude.max())]
    metrics["longitude_range"] = [float(bins.longitude.min()), float(bins.longitude.max())]
    return checks, metrics


def validate_parquet_metadata(parquet_files: list[Path]) -> tuple[list[dict], dict, list[str]]:
    checks = []
    metrics = {}
    schemas = []
    rows = []
    file_indices = []

    for p in parquet_files:
        m = re.search(r"observations_part_(\d+)\.parquet$", p.name)
        if m:
            file_indices.append(int(m.group(1)))
        pf = pq.ParquetFile(p)
        rows.append(int(pf.metadata.num_rows))
        schemas.append(pf.schema_arrow)

    indices_ok = file_indices == list(range(N_OBS_FILES))
    total_rows = int(sum(rows))
    rows_ok = len(rows) == N_OBS_FILES and all(
        r == (120_000 if i == 91 else 480_000) for i, r in enumerate(rows)
    )
    schema_ok = bool(schemas) and all(s == schemas[0] for s in schemas[1:])
    colnames = schemas[0].names if schemas else []
    required_ok = set(REQUIRED_OBS_COLS).issubset(colnames)

    checks.extend([
        {"check":"Observation Parquet file count", "expected":str(N_OBS_FILES), "observed":str(len(parquet_files)), "status":_status(len(parquet_files)==N_OBS_FILES), "severity":"hard"},
        {"check":"Observation part indices", "expected":"000..091 exactly once", "observed":str(file_indices[:4])+"..."+str(file_indices[-4:]), "status":_status(indices_ok), "severity":"hard"},
        {"check":"Per-file row counts", "expected":"000..090: 480,000; 091: 120,000", "observed":f"min={min(rows) if rows else 0:,}, max={max(rows) if rows else 0:,}", "status":_status(rows_ok), "severity":"hard"},
        {"check":"Total hourly observations", "expected":f"{N_ROWS:,}", "observed":f"{total_rows:,}", "status":_status(total_rows==N_ROWS), "severity":"hard"},
        {"check":"Parquet schemas identical", "expected":"identical across all 92 parts", "observed":str(schema_ok), "status":_status(schema_ok), "severity":"hard"},
        {"check":"Required observation columns present", "expected":f"{len(REQUIRED_OBS_COLS)} required fields", "observed":f"{len(colnames)} total fields", "status":_status(required_ok), "severity":"hard"},
    ])
    metrics["parquet_rows_per_file"] = rows
    metrics["observation_columns"] = colnames
    metrics["observation_column_count"] = len(colnames)
    return checks, metrics, colnames


def stream_validate(parquet_files: list[Path], bins: pd.DataFrame, batch_size: int = 200_000):
    """Full-data out-of-core validation over every observation row."""
    bins = bins.sort_values("bin_index").reset_index(drop=True)
    if not np.array_equal(bins.bin_index.to_numpy(), np.arange(N_BINS)):
        raise ValueError("bins metadata must contain bin_index 0..4999 in sorted order")

    # Encode static metadata for fast vectorized joins by bin_index.
    area_categories = sorted(bins.area_type.astype(str).unique())
    area_map = {x:i for i,x in enumerate(area_categories)}
    area_code = bins.area_type.astype(str).map(area_map).to_numpy(np.int16)
    subtype = bins.land_use_subtype.astype(str).to_numpy()
    density_categories = ["Low", "Medium", "High"]
    density_map = {x:i for i,x in enumerate(density_categories)}
    density_code = bins.population_density.astype(str).map(density_map).fillna(-1).to_numpy(np.int8)
    access_categories = ["Easy", "Moderate", "Difficult"]
    access_map = {x:i for i,x in enumerate(access_categories)}
    access_code = bins.road_accessibility.astype(str).map(access_map).fillna(-1).to_numpy(np.int8)
    is_school_bin = (subtype == "School")
    is_recreation_bin = (bins.area_type.astype(str).to_numpy() == "Recreation")
    is_res_slum_bin = np.isin(bins.area_type.astype(str).to_numpy(), ["Residential", "Slum"])
    is_mosque_bin = (bins.nearby_poi_type.astype(str).to_numpy() == "Mosque")

    checks = []
    metrics = {}
    failure_counts = defaultdict(int)

    # Full key coverage uses only ~44 MB and catches missing + duplicate bin-hour keys.
    seen = np.zeros(N_ROWS, dtype=np.uint8)
    per_bin_count = np.zeros(N_BINS, dtype=np.int32)
    duplicate_keys = 0
    invalid_keys = 0

    # Numeric accumulators.
    n_rows_scanned = 0
    packet_n = anomaly_n = available_n = 0
    noise_n = 0
    noise_sum = 0.0
    noise_sumsq = 0.0
    noise_sample = []
    rng = np.random.default_rng(SEED)

    # Group aggregates.
    gross_by_area_sum = np.zeros(len(area_categories), dtype=np.float64)
    gross_by_area_n = np.zeros(len(area_categories), dtype=np.int64)
    gross_by_density_sum = np.zeros(3, dtype=np.float64)
    gross_by_density_n = np.zeros(3, dtype=np.int64)
    delay_by_access_sum = np.zeros(3, dtype=np.float64)
    delay_by_access_n = np.zeros(3, dtype=np.int64)
    scen = defaultdict(lambda: [0.0, 0])
    animal = defaultdict(lambda: [0.0, 0])

    # One complete hourly context series from bin 0.
    context_rows = []

    # Deterministic sample for sequential/forecast checks.
    sample_bins = np.sort(rng.choice(np.arange(N_BINS), size=64, replace=False))
    sample_set = set(sample_bins.tolist())
    sample_frames = []

    cols = list(dict.fromkeys(REQUIRED_OBS_COLS))

    for file_no, p in enumerate(parquet_files):
        pf = pq.ParquetFile(p)
        for batch in pf.iter_batches(batch_size=batch_size, columns=cols):
            names = batch.schema.names
            def c(name):
                return batch.column(names.index(name)).to_numpy(zero_copy_only=False)

            b = c("bin_index").astype(np.int64, copy=False)
            ts = c("timestamp_unix").astype(np.int64, copy=False)
            di = c("date_index").astype(np.int64, copy=False)
            hour = c("hour").astype(np.int64, copy=False)
            dow = c("day_of_week").astype(np.int64, copy=False)
            n = len(b)
            n_rows_scanned += n

            valid = (b >= 0) & (b < N_BINS) & (di >= 0) & (di < N_DAYS) & (hour >= 0) & (hour < 24)
            invalid_keys += int((~valid).sum())
            if valid.any():
                bv, div, hv = b[valid], di[valid], hour[valid]
                keys = bv * N_HOURS + div * 24 + hv
                u, cnt = np.unique(keys, return_counts=True)
                duplicate_keys += int((cnt - 1).clip(min=0).sum())
                duplicate_keys += int(seen[u].sum())
                seen[u] = 1
                per_bin_count += np.bincount(bv, minlength=N_BINS).astype(np.int32)

            exp_ts = START_TS + di * 86400 + hour * 3600
            failure_counts["timestamp_rule_mismatch"] += int(np.count_nonzero(ts != exp_ts))
            exp_dow = (2 + di) % 7  # 2025-01-01 was Wednesday; Monday=0.
            failure_counts["day_of_week_mismatch"] += int(np.count_nonzero(dow != exp_dow))

            gross = c("gross_waste_generation_kg").astype(np.float64)
            rec = c("informal_recovery_kg").astype(np.float64)
            entering = c("waste_entering_bin_kg").astype(np.float64)
            density = c("waste_bulk_density_kg_m3").astype(np.float64)
            volume = c("waste_volume_liter").astype(np.float64)

            failure_counts["negative_mass"] += int(np.count_nonzero((gross < 0) | (rec < 0) | (entering < 0)))
            failure_counts["recovery_exceeds_gross"] += int(np.count_nonzero(rec > gross + 1e-5))
            mass_ok = np.isclose(gross - rec, entering, rtol=2e-5, atol=2e-4)
            failure_counts["mass_balance_mismatch"] += int((~mass_ok).sum())
            vol_expected = entering / np.maximum(density, 1e-12) * 1000.0
            volume_ok = np.isclose(volume, vol_expected, rtol=3e-5, atol=2e-3)
            failure_counts["mass_to_volume_mismatch"] += int((~volume_ok).sum())
            failure_counts["nonpositive_bulk_density"] += int(np.count_nonzero(density <= 0))

            comp = np.column_stack([c(x).astype(np.int16, copy=False) for x in COMPOSITION_COLS])
            failure_counts["composition_sum_not_100"] += int(np.count_nonzero(comp.sum(axis=1) != 100))
            failure_counts["composition_out_of_range"] += int(np.count_nonzero((comp < 0) | (comp > 100)))

            true_fill = c("true_fill_level_percent").astype(np.float64)
            obs_fill = c("fill_level_percent").astype(np.float64)
            pred_fill = c("predicted_fill_level_percent").astype(np.float64)
            threshold = c("collection_threshold_percent").astype(np.float64)
            needs = c("needs_collection").astype(np.uint8)
            due = c("is_collection_due").astype(np.uint8)
            collect = c("collection_event").astype(np.uint8)
            overflow = c("overflow_kg").astype(np.float64)
            pred_overflow = c("predicted_overflow_kg_4h").astype(np.float64)

            failure_counts["true_fill_out_of_range"] += int(np.count_nonzero((true_fill < 0) | (true_fill > 100)))
            finite_obs = np.isfinite(obs_fill)
            failure_counts["observed_fill_out_of_range"] += int(np.count_nonzero(finite_obs & ((obs_fill < 0) | (obs_fill > 100))))
            failure_counts["predicted_fill_out_of_range"] += int(np.count_nonzero((pred_fill < 0) | (pred_fill > 100)))
            needs_expected = (true_fill >= threshold).astype(np.uint8)
            failure_counts["needs_collection_rule_mismatch"] += int(np.count_nonzero(needs != needs_expected))
            failure_counts["due_without_need"] += int(np.count_nonzero((due == 1) & (needs == 0)))
            failure_counts["collection_without_need"] += int(np.count_nonzero((collect == 1) & (needs == 0)))
            failure_counts["negative_overflow"] += int(np.count_nonzero((overflow < 0) | (pred_overflow < 0)))
            failure_counts["overflow_below_full"] += int(np.count_nonzero((overflow > 1e-6) & (true_fill < 99.999)))

            packet = c("is_packet_loss").astype(bool)
            anomaly = c("is_sensor_anomaly").astype(bool)
            err = c("sensor_error_code").astype(np.int16)

            # Calendar/climate arrays reused later for the one-row-per-hour
            # context series. Define them once per batch before any use.
            rainfall_all = c("rainfall_mm_hour").astype(np.float64)
            ramadan_all = c("is_ramadan").astype(bool)
            fitr_period_all = c("is_eid_fitr_period").astype(bool)
            eid_period_all = c("is_eid_period").astype(bool)

            temp = c("temperature_c").astype(np.float64)
            humid = c("humidity_percent").astype(np.float64)
            battery = c("battery_level_percent").astype(np.float64)
            maint = c("battery_maintenance_event").astype(bool)

            packet_n += int(packet.sum())
            anomaly_n += int(anomaly.sum())
            available_n += int((~packet).sum())
            failure_counts["packet_sensor_not_nan"] += int(np.count_nonzero(packet & (np.isfinite(obs_fill) | np.isfinite(temp) | np.isfinite(humid) | np.isfinite(battery))))
            failure_counts["available_sensor_nan"] += int(np.count_nonzero((~packet) & (~np.isfinite(obs_fill) | ~np.isfinite(temp) | ~np.isfinite(humid) | ~np.isfinite(battery))))
            failure_counts["packet_anomaly_conflict"] += int(np.count_nonzero(packet & anomaly))
            failure_counts["sensor_error_code_mismatch"] += int(np.count_nonzero((anomaly & ((err < 1) | (err > 3))) | ((~anomaly) & (err != 0))))
            failure_counts["humidity_out_of_range"] += int(np.count_nonzero((~packet) & ((humid < 40) | (humid > 100))))
            failure_counts["battery_out_of_range"] += int(np.count_nonzero((~packet) & ((battery < 0) | (battery > 100))))
            failure_counts["temperature_implausible"] += int(np.count_nonzero((~packet) & ((temp < 8) | (temp > 45))))
            failure_counts["maintenance_low_battery"] += int(np.count_nonzero(maint & (~packet) & (battery < 95)))

            noise_mask = (~packet) & (~anomaly) & np.isfinite(obs_fill)
            residual = obs_fill[noise_mask] - true_fill[noise_mask]
            noise_n += len(residual)
            noise_sum += float(residual.sum())
            noise_sumsq += float(np.square(residual).sum())
            if len(noise_sample) < 500_000 and residual.size:
                take = residual[::max(1, residual.size // 3000)]
                room = 500_000 - len(noise_sample)
                noise_sample.extend(take[:room].tolist())

            # Group aggregates from static metadata joined by bin_index.
            ac = area_code[b]
            dc = density_code[b]
            xc = access_code[b]
            for k in range(len(area_categories)):
                m = ac == k
                if m.any():
                    gross_by_area_sum[k] += float(gross[m].sum())
                    gross_by_area_n[k] += int(m.sum())
            for k in range(3):
                m = dc == k
                if m.any():
                    gross_by_density_sum[k] += float(gross[m].sum())
                    gross_by_density_n[k] += int(m.sum())
                m2 = (xc == k) & (collect == 1)
                if m2.any():
                    dly = c("collection_delay_minutes").astype(np.float64)[m2]
                    delay_by_access_sum[k] += float(dly.sum())
                    delay_by_access_n[k] += int(m2.sum())

            weekend = c("is_weekend").astype(bool)
            school_closed = c("school_calendar_closed").astype(bool)
            eid_day = c("is_eid_day").astype(bool)
            fitr_day = c("is_eid_fitr_day").astype(bool)
            friday_active = c("friday_effect_active").astype(bool)
            friday_window = c("is_friday_prayer_window").astype(bool)
            event_code = c("event_code").astype(np.int16)
            animal_pct = c("animal_residue_pct").astype(np.float64)

            masks = {
                "school_open": is_school_bin[b] & (~school_closed),
                "school_closed": is_school_bin[b] & school_closed,
                "recreation_weekend": is_recreation_bin[b] & weekend,
                "recreation_weekday": is_recreation_bin[b] & (~weekend),
                "eid_adha_res_slum": is_res_slum_bin[b] & eid_day,
                "normal_res_slum": is_res_slum_bin[b] & (event_code == 0),
                "eid_fitr_res_slum": is_res_slum_bin[b] & fitr_day,
                "friday_mosque_active": is_mosque_bin[b] & friday_active,
                "friday_window_nonmosque": (~is_mosque_bin[b]) & friday_window,
            }
            for key, m in masks.items():
                if m.any():
                    scen[key][0] += float(gross[m].sum())
                    scen[key][1] += int(m.sum())

            m = is_res_slum_bin[b] & eid_day
            if m.any():
                animal["eid_adha_res_slum"][0] += float(animal_pct[m].sum()); animal["eid_adha_res_slum"][1] += int(m.sum())
            m = is_res_slum_bin[b] & (event_code == 0)
            if m.any():
                animal["normal_res_slum"][0] += float(animal_pct[m].sum()); animal["normal_res_slum"][1] += int(m.sum())

            # One row per hour for calendar/climate checks.
            m0 = b == 0
            if m0.any():
                for idx in np.flatnonzero(m0):
                    context_rows.append({
                        "timestamp_unix": int(ts[idx]), "date_index": int(di[idx]), "hour": int(hour[idx]),
                        "rainfall_mm_hour": float(rainfall_all[idx]),
                        "temperature_c": float(temp[idx]) if np.isfinite(temp[idx]) else np.nan,
                        "is_weekend": int(weekend[idx]), "is_ramadan": int(ramadan_all[idx]),
                        "is_eid_fitr_period": int(fitr_period_all[idx]), "is_eid_fitr_day": int(fitr_day[idx]),
                        "is_eid_period": int(eid_period_all[idx]), "is_eid_day": int(eid_day[idx]),
                    })

            # Deterministic 64-bin time series for sequential and 4h forecast diagnostics.
            ms = np.isin(b, sample_bins)
            if ms.any():
                sample_frames.append(pd.DataFrame({
                    "bin_index": b[ms].astype(np.int32), "date_index": di[ms].astype(np.int16),
                    "hour": hour[ms].astype(np.int8), "true_fill": true_fill[ms].astype(np.float32),
                    "pred_fill": pred_fill[ms].astype(np.float32), "collection": collect[ms].astype(np.uint8),
                }))

        print(f"Scanned {file_no+1:02d}/{len(parquet_files)}: {p.name}", flush=True)

    # Full-key coverage metrics.
    missing_keys = int(N_ROWS - int(seen.sum()))
    metrics["rows_scanned"] = int(n_rows_scanned)
    metrics["duplicate_bin_hour_keys"] = int(duplicate_keys)
    metrics["missing_bin_hour_keys"] = missing_keys
    metrics["invalid_bin_hour_keys"] = int(invalid_keys)
    metrics["hours_per_bin_min"] = int(per_bin_count.min())
    metrics["hours_per_bin_max"] = int(per_bin_count.max())
    metrics["failure_counts"] = {k:int(v) for k,v in failure_counts.items()}

    packet_rate = packet_n / n_rows_scanned
    anomaly_rate_available = anomaly_n / max(available_n, 1)
    noise_mean = noise_sum / max(noise_n, 1)
    noise_var = max(noise_sumsq / max(noise_n, 1) - noise_mean**2, 0.0)
    noise_std = math.sqrt(noise_var)
    metrics.update({
        "packet_loss_rate": packet_rate,
        "sensor_anomaly_rate_available": anomaly_rate_available,
        "fill_sensor_noise_mean_pp": noise_mean,
        "fill_sensor_noise_std_pp": noise_std,
        "fill_sensor_noise_n": int(noise_n),
    })

    # Context/calendar/climate checks from bin 0 (one record per simulated hour).
    ctx = pd.DataFrame(context_rows).sort_values(["date_index", "hour"]).reset_index(drop=True)
    ctx["local_time"] = pd.to_datetime(ctx.timestamp_unix, unit="s", utc=True).dt.tz_convert("Asia/Dhaka")
    ctx["month"] = ctx.local_time.dt.month
    rainfall_monthly = ctx.groupby("month")["rainfall_mm_hour"].sum()
    temp_monthly = ctx.groupby("month")["temperature_c"].mean()
    rainfall_table = pd.DataFrame({
        "month": range(1,13),
        "target_mm": [MONTHLY_PRECIP_MM[m] for m in range(1,13)],
        "observed_mm": [float(rainfall_monthly.get(m, np.nan)) for m in range(1,13)],
        "target_mean_temp_c": [MONTHLY_MEAN_TEMP_C[m] for m in range(1,13)],
        "observed_mean_temp_c": [float(temp_monthly.get(m, np.nan)) for m in range(1,13)],
    })
    rainfall_table["rain_abs_error_mm"] = (rainfall_table.observed_mm - rainfall_table.target_mm).abs()
    rainfall_table["temp_abs_error_c"] = (rainfall_table.observed_mean_temp_c - rainfall_table.target_mean_temp_c).abs()

    # Exact calendar flag checks.
    dts = ctx.local_time.dt.date
    special_working = {datetime(2025,5,17).date(), datetime(2025,5,24).date()}
    expected_weekend = np.array([(d.weekday() in (4,5)) and d not in special_working for d in dts], dtype=np.uint8)
    expected_ramadan = np.array([datetime(2025,3,2).date() <= d <= datetime(2025,3,30).date() for d in dts], dtype=np.uint8)
    expected_fitr_period = np.array([datetime(2025,3,29).date() <= d <= datetime(2025,4,3).date() for d in dts], dtype=np.uint8)
    expected_fitr_day = np.array([d == datetime(2025,3,31).date() for d in dts], dtype=np.uint8)
    expected_eid_period = np.array([datetime(2025,6,5).date() <= d <= datetime(2025,6,12).date() for d in dts], dtype=np.uint8)
    expected_eid_day = np.array([d == datetime(2025,6,7).date() for d in dts], dtype=np.uint8)
    failure_counts["weekend_flag_mismatch"] = int(np.count_nonzero(ctx.is_weekend.to_numpy(np.uint8) != expected_weekend))
    failure_counts["ramadan_flag_mismatch"] = int(np.count_nonzero(ctx.is_ramadan.to_numpy(np.uint8) != expected_ramadan))
    failure_counts["eid_fitr_period_flag_mismatch"] = int(np.count_nonzero(ctx.is_eid_fitr_period.to_numpy(np.uint8) != expected_fitr_period))
    failure_counts["eid_fitr_day_flag_mismatch"] = int(np.count_nonzero(ctx.is_eid_fitr_day.to_numpy(np.uint8) != expected_fitr_day))
    failure_counts["eid_adha_period_flag_mismatch"] = int(np.count_nonzero(ctx.is_eid_period.to_numpy(np.uint8) != expected_eid_period))
    failure_counts["eid_adha_day_flag_mismatch"] = int(np.count_nonzero(ctx.is_eid_day.to_numpy(np.uint8) != expected_eid_day))
    metrics["failure_counts"] = {k:int(v) for k,v in failure_counts.items()}

    # Sequential diagnostics on 64 deterministic bins.
    sdf = pd.concat(sample_frames, ignore_index=True).sort_values(["bin_index", "date_index", "hour"])
    sdf["hour_index"] = sdf.date_index.astype(np.int32)*24 + sdf.hour.astype(np.int32)
    g = sdf.groupby("bin_index", sort=False)
    sdf["next_true"] = g.true_fill.shift(-1)
    sdf["next_hour_index"] = g.hour_index.shift(-1)
    sdf["next_collection"] = g.collection.shift(-1)
    contiguous = sdf.next_hour_index.eq(sdf.hour_index + 1)
    no_current_collect = sdf.collection.eq(0)
    monotonic_mask = contiguous & no_current_collect & sdf.next_true.notna()
    monotonic_viol = int((sdf.loc[monotonic_mask, "next_true"] + 1e-5 < sdf.loc[monotonic_mask, "true_fill"]).sum())
    post_collect_mask = contiguous & sdf.collection.eq(1) & sdf.next_true.notna()
    post_collect_vals = sdf.loc[post_collect_mask, "next_true"].to_numpy()

    # 4h operational forecast against future latent fill when no collection intervenes.
    sdf["true_t4"] = g.true_fill.shift(-4)
    sdf["h4"] = g.hour_index.shift(-4)
    future_collect = np.zeros(len(sdf), dtype=np.float64)
    for k in range(1,5):
        future_collect += g.collection.shift(-k).fillna(0).to_numpy()
    fmask = sdf.h4.eq(sdf.hour_index + 4) & sdf.true_t4.notna() & sdf.collection.eq(0) & (future_collect == 0)
    ferr = (sdf.loc[fmask, "pred_fill"] - sdf.loc[fmask, "true_t4"]).to_numpy(np.float64)
    forecast_mae = float(np.mean(np.abs(ferr))) if len(ferr) else float("nan")
    forecast_bias = float(np.mean(ferr)) if len(ferr) else float("nan")
    forecast_rmse = float(np.sqrt(np.mean(ferr**2))) if len(ferr) else float("nan")
    metrics.update({
        "sequential_sample_bins": sample_bins.tolist(),
        "sample_monotonic_violations_without_collection": monotonic_viol,
        "sample_post_collection_next_fill_median": float(np.median(post_collect_vals)) if len(post_collect_vals) else None,
        "sample_post_collection_next_fill_p95": float(np.quantile(post_collect_vals,0.95)) if len(post_collect_vals) else None,
        "forecast_4h_no_collection_n": int(len(ferr)),
        "forecast_4h_no_collection_mae_pp": forecast_mae,
        "forecast_4h_no_collection_rmse_pp": forecast_rmse,
        "forecast_4h_no_collection_bias_pp": forecast_bias,
    })

    # Scenario summaries.
    scenario_rows = []
    for key, (s, n) in sorted(scen.items()):
        scenario_rows.append({"scenario":key, "mean_gross_waste_kg":_mean(s,n), "n":int(n)})
    for key, (s, n) in sorted(animal.items()):
        scenario_rows.append({"scenario":"animal_pct__"+key, "mean_gross_waste_kg":_mean(s,n), "n":int(n)})
    scenario_df = pd.DataFrame(scenario_rows)

    metrics["gross_generation_by_area"] = {a:_mean(gross_by_area_sum[i], gross_by_area_n[i]) for i,a in enumerate(area_categories)}
    metrics["gross_generation_by_density"] = {d:_mean(gross_by_density_sum[i], gross_by_density_n[i]) for i,d in enumerate(density_categories)}
    metrics["collection_delay_minutes_by_accessibility"] = {a:_mean(delay_by_access_sum[i], delay_by_access_n[i]) for i,a in enumerate(access_categories)}
    metrics["scenario_means"] = {r["scenario"]:r["mean_gross_waste_kg"] for r in scenario_rows}

    # Convert accumulated invariants to checks.
    hard_zero = [
        "timestamp_rule_mismatch", "day_of_week_mismatch", "negative_mass", "recovery_exceeds_gross",
        "mass_balance_mismatch", "mass_to_volume_mismatch", "nonpositive_bulk_density",
        "composition_sum_not_100", "composition_out_of_range", "true_fill_out_of_range",
        "observed_fill_out_of_range", "predicted_fill_out_of_range", "needs_collection_rule_mismatch",
        "due_without_need", "collection_without_need", "negative_overflow", "overflow_below_full",
        "packet_sensor_not_nan", "available_sensor_nan", "packet_anomaly_conflict",
        "sensor_error_code_mismatch", "humidity_out_of_range", "battery_out_of_range",
        "weekend_flag_mismatch", "ramadan_flag_mismatch", "eid_fitr_period_flag_mismatch",
        "eid_fitr_day_flag_mismatch", "eid_adha_period_flag_mismatch", "eid_adha_day_flag_mismatch",
    ]
    checks.extend([
        {"check":"Full scan row count", "expected":f"{N_ROWS:,}", "observed":f"{n_rows_scanned:,}", "status":_status(n_rows_scanned==N_ROWS), "severity":"hard"},
        {"check":"Unique bin-hour coverage", "expected":"0 duplicates and 0 missing keys", "observed":f"duplicates={duplicate_keys:,}; missing={missing_keys:,}; invalid={invalid_keys:,}", "status":_status(duplicate_keys==0 and missing_keys==0 and invalid_keys==0), "severity":"hard"},
        {"check":"Hours per bin", "expected":"8,760 for every bin", "observed":f"min={per_bin_count.min():,}; max={per_bin_count.max():,}", "status":_status(per_bin_count.min()==N_HOURS and per_bin_count.max()==N_HOURS), "severity":"hard"},
    ])
    for name in hard_zero:
        v = int(failure_counts.get(name, 0))
        checks.append({"check":name.replace("_"," ").title(), "expected":"0", "observed":str(v), "status":_status(v==0), "severity":"hard"})

    # Soft/statistical expectations: failures are warnings rather than falsifying data integrity.
    checks.extend([
        {"check":"Packet-loss rate", "expected":"approximately 0.5% with context effects", "observed":f"{packet_rate*100:.4f}%", "status":"PASS" if 0.0035 <= packet_rate <= 0.0080 else "WARN", "severity":"soft"},
        {"check":"Sensor-anomaly rate among available packets", "expected":"approximately 0.1%", "observed":f"{anomaly_rate_available*100:.4f}%", "status":"PASS" if 0.0007 <= anomaly_rate_available <= 0.0013 else "WARN", "severity":"soft"},
        {"check":"Fill-sensor residual mean", "expected":"near 0 percentage points", "observed":f"{noise_mean:.4f}", "status":"PASS" if abs(noise_mean) <= 0.08 else "WARN", "severity":"soft"},
        {"check":"Fill-sensor residual SD", "expected":"near configured sigma=1.5 pp (clipping lowers it slightly)", "observed":f"{noise_std:.4f}", "status":"PASS" if 1.2 <= noise_std <= 1.8 else "WARN", "severity":"soft"},
        {"check":"Monthly rainfall calibration", "expected":"each monthly total within 0.05 mm of configured normal", "observed":f"max abs error={rainfall_table.rain_abs_error_mm.max():.6f} mm", "status":"PASS" if rainfall_table.rain_abs_error_mm.max() <= 0.05 else "WARN", "severity":"soft"},
        {"check":"Sample temporal monotonicity between collections", "expected":"0 decreases when no collection occurs", "observed":str(monotonic_viol), "status":"PASS" if monotonic_viol==0 else "WARN", "severity":"soft"},
        {"check":"Temperature plausibility", "expected":"sensor values broadly within 8..45 C", "observed":str(int(failure_counts.get("temperature_implausible",0))), "status":"PASS" if int(failure_counts.get("temperature_implausible",0))==0 else "WARN", "severity":"soft"},
        {"check":"Maintenance restores battery", "expected":"maintenance observations generally >=95% when packet available", "observed":str(int(failure_counts.get("maintenance_low_battery",0))), "status":"PASS" if int(failure_counts.get("maintenance_low_battery",0))==0 else "WARN", "severity":"soft"},
    ])

    # Scenario directional checks, reported as soft because they are modeled assumptions.
    def scen_mean(k):
        s,n = scen[k]
        return _mean(s,n)
    directional = [
        ("School open > school closed generation", scen_mean("school_open"), scen_mean("school_closed"), lambda a,b: a>b),
        ("Recreation weekend > weekday generation", scen_mean("recreation_weekend"), scen_mean("recreation_weekday"), lambda a,b: a>b),
        ("Eid-ul-Adha residential/slum > normal generation", scen_mean("eid_adha_res_slum"), scen_mean("normal_res_slum"), lambda a,b: a>b),
    ]
    animal_eid = _mean(*animal["eid_adha_res_slum"])
    animal_norm = _mean(*animal["normal_res_slum"])
    directional.append(("Eid-ul-Adha animal-residue share > normal", animal_eid, animal_norm, lambda a,b:a>b))
    for label,a,b,fn in directional:
        ok = np.isfinite(a) and np.isfinite(b) and fn(a,b)
        checks.append({"check":label, "expected":"direction encoded by scenario", "observed":f"scenario={a:.5f}; reference={b:.5f}", "status":"PASS" if ok else "WARN", "severity":"soft"})

    return checks, metrics, rainfall_table, scenario_df, np.asarray(noise_sample, dtype=np.float32), sdf


def make_figures(output_dir: Path, rainfall_table: pd.DataFrame, noise_sample: np.ndarray, metrics: dict, scenario_df: pd.DataFrame):
    import matplotlib.pyplot as plt
    output_dir.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(9,4.8))
    ax.plot(rainfall_table.month, rainfall_table.target_mm, marker="o", label="Configured monthly normal")
    ax.plot(rainfall_table.month, rainfall_table.observed_mm, marker="x", label="Observed synthetic monthly total")
    ax.set_xlabel("Month"); ax.set_ylabel("Rainfall (mm)")
    ax.set_title("Monthly rainfall calibration")
    ax.legend(); fig.tight_layout()
    fig.savefig(output_dir / "figure_monthly_rainfall_validation.png", dpi=220)
    plt.close(fig)

    if noise_sample.size:
        fig, ax = plt.subplots(figsize=(8,4.8))
        ax.hist(noise_sample, bins=80)
        ax.set_xlabel("Observed fill − latent true fill (percentage points)")
        ax.set_ylabel("Count")
        ax.set_title("Fill-sensor residual distribution (deterministic sample)")
        fig.tight_layout(); fig.savefig(output_dir / "figure_sensor_fill_noise.png", dpi=220)
        plt.close(fig)

    delay = metrics.get("collection_delay_minutes_by_accessibility", {})
    if delay:
        fig, ax = plt.subplots(figsize=(7,4.8))
        labels = list(delay.keys()); vals = [delay[x] for x in labels]
        ax.bar(labels, vals)
        ax.set_ylabel("Mean collection delay (minutes)")
        ax.set_title("Collection delay by road accessibility")
        fig.tight_layout(); fig.savefig(output_dir / "figure_collection_delay_accessibility.png", dpi=220)
        plt.close(fig)

    # Selected scenario ratios for an interpretable manuscript figure.
    sm = metrics.get("scenario_means", {})
    ratios = {}
    pairs = [
        ("School open/closed", "school_open", "school_closed"),
        ("Recreation weekend/weekday", "recreation_weekend", "recreation_weekday"),
        ("Eid-Adha res/slum vs normal", "eid_adha_res_slum", "normal_res_slum"),
    ]
    for label,a,b in pairs:
        if a in sm and b in sm and sm[b] and np.isfinite(sm[a]) and np.isfinite(sm[b]):
            ratios[label] = sm[a]/sm[b]
    if ratios:
        fig, ax = plt.subplots(figsize=(9,4.8))
        ax.bar(list(ratios.keys()), list(ratios.values()))
        ax.axhline(1.0, linewidth=1)
        ax.set_ylabel("Mean-generation ratio")
        ax.set_title("Directional scenario checks")
        ax.tick_params(axis="x", rotation=15)
        fig.tight_layout(); fig.savefig(output_dir / "figure_scenario_effects.png", dpi=220)
        plt.close(fig)


def write_technical_validation_md(output_dir: Path, checks_df: pd.DataFrame, metrics: dict, bins_source: str, bins_parquet_present: bool):
    hard = checks_df[checks_df.severity == "hard"]
    n_fail = int((hard.status == "FAIL").sum())
    overall = "passed" if n_fail == 0 else f"identified {n_fail} hard validation failure(s)"
    m = metrics
    text = f"""# Technical Validation — auto-generated draft

The released Dhaka Smart Waste Synthetic IoT Dataset V4.0 was subjected to a reviewer-oriented, full-data technical validation. The validation scanned all `{m.get('rows_scanned', 0):,}` hourly observations and {overall}. Because the dataset is synthetic, these tests establish internal structural consistency, rule consistency, reproducibility of the release layout, and statistical behavior of the simulation; they should not be described as field validation of deployed municipal smart bins.

## Structural integrity

The release was checked for the canonical 5,000 persistent bins, 92 observation Parquet parts, and 43,800,000 hourly records. Each bin is expected to contribute 8,760 bin-hour records covering the 2025 calendar. Full key-coverage validation found `{m.get('duplicate_bin_hour_keys', 0):,}` duplicate bin-hour keys and `{m.get('missing_bin_hour_keys', 0):,}` missing keys. The minimum and maximum records per bin were `{m.get('hours_per_bin_min', 0):,}` and `{m.get('hours_per_bin_max', 0):,}`, respectively.

Persistent metadata were read from `{bins_source}`. `bins.parquet` present in the current Drive release tree: **{bins_parquet_present}**.

## Logical and physical consistency

The validation checks mass balance (`gross waste − informal recovery = waste entering the bin`), mass-to-volume conversion, eight-component composition summing to 100%, fill-level bounds, collection-threshold logic, overflow constraints, battery bounds, and the relationship between collection-due and collection-need indicators. Counts for every hard invariant are saved in `validation_summary.csv` and `VALIDATION_REPORT.json`.

## Sensor behavior

The observed packet-loss rate was `{m.get('packet_loss_rate', float('nan'))*100:.4f}%`. Among available packets, the sensor-anomaly rate was `{m.get('sensor_anomaly_rate_available', float('nan'))*100:.4f}%`. Excluding packet losses and deliberately injected anomalies, the fill-sensor residual had mean `{m.get('fill_sensor_noise_mean_pp', float('nan')):.4f}` percentage points and standard deviation `{m.get('fill_sensor_noise_std_pp', float('nan')):.4f}` percentage points, consistent with the approximately 1.5-percentage-point Gaussian noise configured by the generator, subject to 0–100% clipping.

## Calendar and climate calibration

Calendar flags for weekends, Ramadan, Eid-ul-Fitr, and Eid-ul-Adha were independently reconstructed from dates and compared with the released fields. Monthly synthetic rainfall totals were compared with the configured Dhaka climate-normal targets; detailed month-level values are provided in `monthly_climate_validation.csv` and `figure_monthly_rainfall_validation.png`.

## Dynamic and scenario checks

A deterministic 64-bin temporal sample was used to evaluate sequential behavior and the operational four-hour fill forecast. For forecast instances with no collection during the four-hour horizon, the mean absolute error was `{m.get('forecast_4h_no_collection_mae_pp', float('nan')):.4f}` percentage points (n=`{m.get('forecast_4h_no_collection_n', 0):,}`). Scenario-level summaries quantify school open/closed behavior, recreation weekend/weekday behavior, Eid-ul-Adha effects, waste-composition shifts, Friday mosque-window behavior, density gradients, and collection delay by road accessibility. These directional checks validate implementation of the stated simulation assumptions; they are not independent empirical estimates of real-world effect sizes.

## Reproducibility note

The generator uses the fixed NumPy seed `20260902`. For a publication archive, the generator, this validator, the release-layout files, software requirements, and the generated `VALIDATION_REPORT.json` should be deposited together with the dataset.
"""
    (output_dir / "TECHNICAL_VALIDATION_AUTO.md").write_text(text, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default="/content/drive/MyDrive/Dhaka Smart Waste V4.0 2025")
    parser.add_argument("--extract-dir", default="/content/dhaka_smart_waste_v4_parquet_validation")
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--batch-size", type=int, default=200_000)
    args = parser.parse_args()

    project_root = Path(args.project_root)
    extract_dir = Path(args.extract_dir)
    output_dir = Path(args.output_dir) if args.output_dir else project_root / "VALIDATION_OUTPUTS"
    output_dir.mkdir(parents=True, exist_ok=True)

    all_checks = []
    report = {"dataset":"Dhaka Smart Waste Synthetic IoT Dataset V4.0 — One-Year 2025", "validator":"validate_v4_0_paper.py"}

    parquet_files, zip_info = extract_release(project_root, extract_dir)
    all_checks.append({"check":"Transport ZIP count", "expected":"23", "observed":str(zip_info["zip_count"]), "status":_status(zip_info["zip_count"]==23), "severity":"hard"})
    all_checks.append({"check":"Transport ZIP integrity", "expected":"0 corrupt ZIPs", "observed":str(zip_info["corrupt_zips"]), "status":_status(len(zip_info["corrupt_zips"])==0), "severity":"hard"})

    bins, bins_source, bins_parquet_present = load_bins(project_root)
    bin_checks, bin_metrics = validate_bins(bins)
    all_checks.extend(bin_checks)
    # Release packaging expectation: documentation names bins.parquet. Keep as soft warning so current CSV fallback can still be validated.
    all_checks.append({"check":"Documented bins.parquet release file", "expected":"bins.parquet available with public Parquet release", "observed":bins_source, "status":"PASS" if bins_parquet_present else "WARN", "severity":"soft"})

    meta_checks, meta_metrics, colnames = validate_parquet_metadata(parquet_files)
    all_checks.extend(meta_checks)

    stream_checks, stream_metrics, climate_df, scenario_df, noise_sample, sample_df = stream_validate(
        parquet_files, bins, batch_size=args.batch_size
    )
    all_checks.extend(stream_checks)

    checks_df = pd.DataFrame(all_checks)
    checks_df.to_csv(output_dir / "validation_summary.csv", index=False)
    climate_df.to_csv(output_dir / "monthly_climate_validation.csv", index=False)
    scenario_df.to_csv(output_dir / "scenario_summary.csv", index=False)
    pd.DataFrame(zip_info.get("members", [])).to_csv(output_dir / "parquet_zip_contents.csv", index=False)

    report["run_metadata"] = {
        "python": sys.version.split()[0],
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "pyarrow": __import__("pyarrow").__version__,
        "batch_size": int(args.batch_size),
        "project_root": str(project_root),
        "extract_dir": str(extract_dir),
        "output_dir": str(output_dir),
    }

    report.update({
        "zip_info": zip_info,
        "bins_source": bins_source,
        "bins_parquet_present": bins_parquet_present,
        "bin_metrics": bin_metrics,
        "parquet_metrics": meta_metrics,
        "validation_metrics": stream_metrics,
        "checks": all_checks,
    })
    hard_failures = [x for x in all_checks if x["severity"] == "hard" and x["status"] == "FAIL"]
    report["hard_failure_count"] = len(hard_failures)
    report["overall_hard_status"] = "PASS" if not hard_failures else "FAIL"
    report = _json_safe(report)
    report_tmp = output_dir / "VALIDATION_REPORT.json.tmp"
    report_tmp.write_text(
        json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False),
        encoding="utf-8",
    )
    report_tmp.replace(output_dir / "VALIDATION_REPORT.json")

    make_figures(output_dir, climate_df, noise_sample, stream_metrics, scenario_df)
    write_technical_validation_md(output_dir, checks_df, stream_metrics, bins_source, bins_parquet_present)

    print("\n=== VALIDATION COMPLETE ===")
    print(checks_df[["check","status","severity"]].to_string(index=False))
    print(f"\nHard failures: {len(hard_failures)}")
    print(f"Outputs: {output_dir}")
    if hard_failures:
        print("\nHard failures:")
        for x in hard_failures:
            print(" -", x["check"], "=>", x["observed"])
        sys.exit(1)


if __name__ == "__main__":
    main()
