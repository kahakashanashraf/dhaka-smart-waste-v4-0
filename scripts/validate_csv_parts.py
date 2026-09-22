#!/usr/bin/env python3
from pathlib import Path
import csv
import gzip
import sys

ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
EXPECTED_PARTS = 44
EXPECTED_TOTAL = 43_800_000
EXPECTED_OBS_COLUMNS = 59
EXPECTED_BINS = 5_000
EXPECTED_BIN_COLUMNS = 29

def count_gzip_csv(path):
    with gzip.open(path, "rt", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        header = next(reader)
        rows = sum(1 for _ in reader)
    return header, rows

errors = []
total = 0

parts = sorted(ROOT.glob("observations_part_*.csv.gz"))
if len(parts) != EXPECTED_PARTS:
    errors.append(f"Expected {EXPECTED_PARTS} observation parts, found {len(parts)}")

for i in range(EXPECTED_PARTS):
    p = ROOT / f"observations_part_{i:03d}.csv.gz"
    if not p.exists():
        errors.append(f"Missing {p.name}")
        continue
    try:
        header, rows = count_gzip_csv(p)
    except Exception as e:
        errors.append(f"{p.name}: unreadable gzip/CSV: {e}")
        continue
    expected_rows = 800_000 if i == 43 else 1_000_000
    if len(header) != EXPECTED_OBS_COLUMNS:
        errors.append(f"{p.name}: {len(header)} columns, expected {EXPECTED_OBS_COLUMNS}")
    if rows != expected_rows:
        errors.append(f"{p.name}: {rows:,} rows, expected {expected_rows:,}")
    total += rows

bins = ROOT / "bins.csv.gz"
if not bins.exists():
    errors.append("Missing bins.csv.gz")
else:
    try:
        header, rows = count_gzip_csv(bins)
        if len(header) != EXPECTED_BIN_COLUMNS:
            errors.append(f"bins.csv.gz: {len(header)} columns, expected {EXPECTED_BIN_COLUMNS}")
        if rows != EXPECTED_BINS:
            errors.append(f"bins.csv.gz: {rows:,} rows, expected {EXPECTED_BINS:,}")
    except Exception as e:
        errors.append(f"bins.csv.gz: unreadable gzip/CSV: {e}")

if total != EXPECTED_TOTAL:
    errors.append(f"Total observation rows {total:,}, expected {EXPECTED_TOTAL:,}")

print(f"CSV observation parts: {len(parts)}")
print(f"CSV rows: {total:,}")
print(f"bins rows: {EXPECTED_BINS:,}" if bins.exists() else "bins rows: missing")

if errors:
    print("\nFAIL")
    for e in errors:
        print(" -", e)
    raise SystemExit(1)

print("PASS")
