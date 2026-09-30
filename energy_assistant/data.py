from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = Path(os.getenv("ENERGY_DATA_PATH", ROOT / "data/processed/household_power_consumption_cleaned.csv"))
POWER = "Global_active_power"
METERS = [POWER, "Global_reactive_power", "Voltage", "Global_intensity", "Sub_metering_1", "Sub_metering_2", "Sub_metering_3"]


class DataSourceError(RuntimeError):
    """Raised when the cleaned dataset is missing, malformed, or unsafe to analyze."""


@lru_cache(maxsize=1)
def minute_data() -> pd.DataFrame:
    # GUARDRAIL SHOWCASE 1: fail closed when data is absent or does not match the expected schema.
    if not DATA_PATH.exists():
        raise DataSourceError("Cleaned dataset is missing. Run `python prepare_data.py` or set ENERGY_DATA_PATH.")
    try:
        columns = set(pd.read_csv(DATA_PATH, nrows=0).columns)
    except (OSError, pd.errors.ParserError, UnicodeError) as exc:
        raise DataSourceError("Cleaned dataset could not be read. Rebuild it with `python prepare_data.py`.") from exc
    required = {"timestamp", *METERS}
    missing_columns = required.difference(columns)
    if missing_columns:
        raise DataSourceError(f"Cleaned dataset is missing required columns: {', '.join(sorted(missing_columns))}.")
    try:
        df = pd.read_csv(DATA_PATH, usecols=["timestamp", *METERS])
    except (OSError, pd.errors.ParserError, UnicodeError) as exc:
        raise DataSourceError("Cleaned dataset could not be read. Rebuild it with `python prepare_data.py`.") from exc
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    invalid_times = int(df["timestamp"].isna().sum())
    if invalid_times:
        raise DataSourceError(f"Cleaned dataset contains {invalid_times:,} invalid timestamps. Rebuild the dataset.")
    if df.empty:
        raise DataSourceError("Cleaned dataset has no rows. Rebuild it with `python prepare_data.py`.")
    for col in METERS:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    missing_values = int(df[METERS].isna().sum().sum())
    if missing_values:
        raise DataSourceError(f"Cleaned dataset contains {missing_values:,} missing meter values. Rebuild the dataset.")
    if df["timestamp"].duplicated().any():
        raise DataSourceError("Cleaned dataset contains duplicate timestamps. Rebuild the dataset.")
    df = df.set_index("timestamp").sort_index()
    return df


@lru_cache(maxsize=1)
def hourly_data() -> pd.DataFrame:
    minute = minute_data()
    hourly = minute.resample("h").mean()
    hourly["minute_count"] = minute[POWER].resample("h").count()
    # Dataset sub-meter fields are Wh per minute. Convert each hour's summed values to kWh.
    for col in ["Sub_metering_1", "Sub_metering_2", "Sub_metering_3"]:
        hourly[col + "_kwh"] = minute[col].resample("h").sum() / 1000.0
    hourly["total_energy_kwh"] = minute[POWER].resample("h").sum() / 60.0
    sub_sum = sum(hourly[f"Sub_metering_{i}_kwh"] for i in (1, 2, 3))
    hourly["other_energy_kwh"] = (hourly["total_energy_kwh"] - sub_sum).clip(lower=0)
    return hourly


def select_hours(start: str | None = None, end: str | None = None) -> pd.DataFrame:
    df = hourly_data()
    # GUARDRAIL SHOWCASE 2: validate date syntax, ordering, and source-data coverage.
    try:
        lower = pd.Timestamp(start) if start else df.index.min().normalize()
        upper = pd.Timestamp(end) if end else df.index.max().normalize()
    except (TypeError, ValueError) as exc:
        raise ValueError("Dates must use YYYY-MM-DD or ISO timestamp format.") from exc
    if lower.tzinfo is not None or upper.tzinfo is not None:
        raise ValueError("Dates must be timezone-naive because this dataset has no timezone metadata.")
    if len(end or "") == 10 and end:
        upper += pd.Timedelta(days=1) - pd.Timedelta(nanoseconds=1)
    if lower > upper:
        raise ValueError("Start date must be on or before the end date.")
    first_day, last_day = df.index.min().normalize(), df.index.max().normalize()
    if lower.normalize() < first_day or upper.normalize() > last_day:
        raise ValueError(f"Requested dates are outside the dataset coverage ({first_day.date()} to {last_day.date()}).")
    df = df.loc[lower:upper]
    return df
