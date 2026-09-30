from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_DATA = PROJECT_ROOT / "data" / "processed" / "household_power_consumption_cleaned.csv"
OUTPUT_DATA = Path(__file__).resolve().parent / "prepared_energy_data.csv"
QUALITY_REPORT = Path(__file__).resolve().parent / "data_quality_summary.json"

REQUIRED_COLUMNS = [
    "timestamp",
    "Global_active_power",
    "Global_reactive_power",
    "Voltage",
    "Global_intensity",
    "Sub_metering_1",
    "Sub_metering_2",
    "Sub_metering_3",
]


def load_dataset(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")

    df = pd.read_csv(path)
    missing = [column for column in REQUIRED_COLUMNS if column not in df.columns]
    if missing:
        raise ValueError(f"Dataset is missing required columns: {missing}")

    return df


def prepare_dataset(df: pd.DataFrame) -> pd.DataFrame:
    prepared = df.copy()

    prepared["timestamp"] = pd.to_datetime(prepared["timestamp"], errors="coerce")
    prepared = prepared.dropna(subset=["timestamp"]).sort_values("timestamp").reset_index(drop=True)

    for column in REQUIRED_COLUMNS[1:]:
        prepared[column] = pd.to_numeric(prepared[column], errors="coerce")

    prepared["hour"] = prepared["timestamp"].dt.hour
    prepared["day_of_week"] = prepared["timestamp"].dt.dayofweek
    prepared["month"] = prepared["timestamp"].dt.month
    prepared["day_of_month"] = prepared["timestamp"].dt.day
    prepared["is_weekend"] = prepared["timestamp"].dt.dayofweek.isin([5, 6]).astype(int)

    return prepared


def generate_quality_report(df: pd.DataFrame) -> dict:
    missing_by_column = df.isna().sum().to_dict()
    summary = {
        "rows_loaded": int(len(df)),
        "columns": list(df.columns),
        "timestamp_start": df["timestamp"].min().isoformat() if not df.empty else None,
        "timestamp_end": df["timestamp"].max().isoformat() if not df.empty else None,
        "duplicate_timestamps": int(df["timestamp"].duplicated().sum()),
        "missing_by_column": {str(key): int(value) for key, value in missing_by_column.items()},
        "time_features_added": ["hour", "day_of_week", "month", "day_of_month", "is_weekend"],
        "preprocessing_rules": [
            "Load the existing project dataset without modifying the source file.",
            "Convert timestamp strings to pandas datetime values and remove invalid entries.",
            "Sort the dataset chronologically for reliable time-series analysis.",
            "Validate required energy-measurement columns and force numeric conversion.",
            "Create time-of-day and calendar features for analytics, anomaly detection, and forecasting.",
        ],
    }
    return summary


def main() -> None:
    raw_df = load_dataset(SOURCE_DATA)
    prepared_df = prepare_dataset(raw_df)
    quality_report = generate_quality_report(prepared_df)

    prepared_df.to_csv(OUTPUT_DATA, index=False)
    QUALITY_REPORT.write_text(json.dumps(quality_report, indent=2), encoding="utf-8")

    print(f"Prepared dataset written to: {OUTPUT_DATA}")
    print(f"Quality summary written to: {QUALITY_REPORT}")
    print(f"Rows prepared: {len(prepared_df)}")
    print(f"Date range: {prepared_df['timestamp'].min()} to {prepared_df['timestamp'].max()}")


if __name__ == "__main__":
    main()
