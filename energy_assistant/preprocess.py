"""Clean the original UCI household power file into the runtime CSV format."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from .data import METERS

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "data/raw/household_power_consumption.txt"
DEFAULT_OUTPUT = ROOT / "data/processed/household_power_consumption_cleaned.csv"


def clean_dataset(source: Path, output: Path) -> dict:
    if not source.exists():
        raise FileNotFoundError(f"Raw dataset not found: {source}")
    frame = pd.read_csv(source, sep=";", na_values=["?", ""], low_memory=False)
    required = {"Date", "Time", *METERS}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"Raw dataset is missing required columns: {', '.join(sorted(missing))}")

    rows_loaded = len(frame)
    frame["timestamp"] = pd.to_datetime(
        frame["Date"].astype(str) + " " + frame["Time"].astype(str),
        dayfirst=True, errors="coerce",
    )
    invalid_timestamps = int(frame["timestamp"].isna().sum())
    frame = frame.dropna(subset=["timestamp"]).sort_values("timestamp")
    duplicate_timestamps = int(frame["timestamp"].duplicated().sum())
    frame = frame.drop_duplicates("timestamp", keep="last").set_index("timestamp")

    for column in METERS:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    missing_before = frame[METERS].isna().sum().astype(int).to_dict()
    frame[METERS] = frame[METERS].interpolate(method="time", limit=5, limit_area="inside")
    for column in METERS:
        median = frame[column].median()
        if pd.isna(median):
            raise ValueError(f"Column {column} has no numeric readings to fill missing values.")
        frame[column] = frame[column].fillna(median)

    output.parent.mkdir(parents=True, exist_ok=True)
    cleaned = frame[METERS].reset_index()
    cleaned.to_csv(output, index=False)
    report = {
        "rows_loaded": rows_loaded,
        "rows_after_cleaning": len(cleaned),
        "invalid_timestamps_removed": invalid_timestamps,
        "duplicate_timestamps_removed": duplicate_timestamps,
        "missing_measurements_before_by_column": missing_before,
        "missing_measurements_after_by_column": frame[METERS].isna().sum().astype(int).to_dict(),
        "start_timestamp": cleaned["timestamp"].min().isoformat(),
        "end_timestamp": cleaned["timestamp"].max().isoformat(),
        "cleaning_rules": [
            "Read semicolon-delimited measurements; treat question marks and blanks as missing.",
            "Combine day-first Date and Time fields; remove invalid timestamps and keep the last duplicate.",
            "Interpolate internal gaps up to five consecutive minutes; median-fill remaining meter gaps.",
            "Write a separate cleaned CSV without changing the source file.",
        ],
    }
    (output.parent / "data_quality_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_SOURCE, help="Original semicolon-delimited UCI text file")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Cleaned CSV output path")
    args = parser.parse_args()
    report = clean_dataset(args.input, args.output)
    print(f"Cleaned dataset: {args.output}")
    print(f"Quality report: {args.output.parent / 'data_quality_report.json'}")
    print(f"Rows: {report['rows_after_cleaning']:,}; invalid timestamps removed: {report['invalid_timestamps_removed']:,}; duplicates removed: {report['duplicate_timestamps_removed']:,}")


if __name__ == "__main__":
    main()
