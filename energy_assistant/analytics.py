from __future__ import annotations

import numpy as np
import pandas as pd
import json
from pathlib import Path

from .data import METERS, POWER, hourly_data, minute_data, select_hours
from .forecasting import forecast


def summary(start: str | None = None, end: str | None = None) -> dict:
    frame = select_hours(start, end).dropna(subset=[POWER])
    if frame.empty:
        return {"error": "No readings found for this date range."}
    series = frame[POWER]
    peak_at = series.idxmax()
    minimum_at = series.idxmin()
    by_hour = series.groupby(frame.index.hour).mean()
    by_weekday = series.groupby(frame.index.dayofweek).mean()
    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    daily = frame.groupby(frame.index.date).agg(mean_kw=(POWER, "mean"), peak_kw=(POWER, "max"))
    daily["energy_kwh"] = frame.groupby(frame.index.date)["total_energy_kwh"].sum()
    monthly = frame.groupby(frame.index.to_period("M"))[POWER].mean()
    change = None
    daily_delta = daily["mean_kw"].diff().dropna()
    if not daily_delta.empty:
        change_day = daily_delta.idxmax()
        current_pos = daily.index.get_loc(change_day)
        prior_day = daily.index[current_pos - 1]
        metering_cols = [f"Sub_metering_{i}_kwh" for i in (1, 2, 3)]
        by_day_meter = frame.groupby(frame.index.date)[metering_cols].sum()
        meter_delta = by_day_meter.loc[change_day] - by_day_meter.loc[prior_day]
        change = {"date": str(change_day), "previous_date": str(prior_day),
                  "mean_kw_change": round(float(daily_delta.loc[change_day]), 3),
                  "submeter_kwh_change": {f"submeter_{i+1}": round(float(meter_delta.iloc[i]), 2) for i in range(3)}}
    sub_kwh = {f"submeter_{n}": float(frame[f"Sub_metering_{n}_kwh"].sum()) for n in (1, 2, 3)}
    total_kwh = float(frame["total_energy_kwh"].sum())
    sub_kwh["other"] = max(0.0, total_kwh - sum(sub_kwh.values()))
    measurement_means = {
        "reactive_power_kw": round(float(frame["Global_reactive_power"].mean()), 3),
        "voltage_v": round(float(frame["Voltage"].mean()), 2),
        "current_a": round(float(frame["Global_intensity"].mean()), 2),
    }
    return {
        "start": frame.index.min().isoformat(), "end": frame.index.max().isoformat(), "hours": int(len(frame)),
        "mean_kw": round(float(series.mean()), 3), "max_kw": round(float(series.max()), 3),
        "max_at": peak_at.isoformat(), "min_kw": round(float(series.min()), 3), "min_at": minimum_at.isoformat(),
        "p95_kw": round(float(series.quantile(.95)), 3),
        "peak_hours": [int(x) for x in by_hour.nlargest(3).index],
        "hourly_profile": [{"hour": int(hour), "mean_kw": round(float(value), 3)} for hour, value in by_hour.items()],
        "weekday_profile": [{"weekday": day_names[int(day)], "mean_kw": round(float(value), 3)} for day, value in by_weekday.items()],
        "top_weekday": day_names[int(by_weekday.idxmax())], "total_energy_kwh": round(total_kwh, 1), "largest_daily_rise": change,
        "measurement_means": measurement_means,
        "energy_mix_kwh": {k: round(v, 1) for k, v in sub_kwh.items()},
        "daily": [{"date": str(k), "mean_kw": round(float(v.mean_kw), 3), "peak_kw": round(float(v.peak_kw), 3),
                   "energy_kwh": round(float(v.energy_kwh), 2)} for k,v in daily.iterrows()],
        "monthly": [{"month": str(k), "mean_kw": round(float(v), 3)} for k,v in monthly.items()],
        "evidence": [f"{len(frame):,} hourly readings; mean active power {series.mean():.3f} kW",
                     f"Peak hourly mean {series.max():.3f} kW at {peak_at}",
                     f"Estimated active energy in this range: {total_kwh:,.1f} kWh"]
    }


def evaluation(start: str | None = None, end: str | None = None) -> dict:
    series = select_hours(start, end)[POWER].dropna()
    if len(series) < 48:
        raise ValueError("Choose at least 48 hours for forecast evaluation; the forecast itself can use a shorter range.")
    n_test = min(24 * 28, max(24, len(series) // 5))
    split = len(series) - n_test
    seasonal_period = 168 if split >= 168 else 24
    actual = series.iloc[split:].to_numpy()
    # Use a weekly baseline when history supports it; otherwise fall back to daily seasonality.
    predicted = series.iloc[split - seasonal_period:len(series) - seasonal_period].to_numpy()
    error = actual - predicted
    return {"model": f"{seasonal_period}-hour seasonal-naive", "train_hours": int(split), "test_hours": int(n_test),
            "mae_kw": round(float(np.abs(error).mean()), 4), "rmse_kw": round(float(np.sqrt(np.mean(error ** 2))), 4),
            "mape_percent": round(float((np.abs(error) / np.maximum(actual, .1)).mean() * 100), 2),
              "note": "Final chronological holdout; MAPE denominator is floored at 0.1 kW."}


def timeseries(window: str = "7d", horizon: int = 24,
               start: str | None = None, end: str | None = None) -> dict:
    """Return observed hourly demand, robust anomaly markers, and a historical baseline forecast."""
    hours = select_hours(start, end).dropna(subset=[POWER])
    durations = {"1h": 1, "6h": 6, "24h": 24, "7d": 168, "30d": 720, "1y": 8760}
    if window not in durations:
        raise ValueError("Window must be one of 1h, 6h, 24h, 7d, 30d, or 1y.")
    window_hours = durations[window]
    view = hours.tail(window_hours)
    # Downsample longer windows for a legible, bounded browser chart.
    if window == "30d":
        view = view.resample("4h").mean(numeric_only=True).dropna(subset=[POWER])
    elif window == "1y":
        view = view.resample("D").mean(numeric_only=True).dropna(subset=[POWER])
    actual = [{"timestamp": ts.isoformat(), "kw": round(float(row[POWER]), 3)}
              for ts, row in view.iterrows()]
    # Use the same cached Isolation Forest + robust statistical screen as the investigation page.
    from .anomaly import detect
    active_start = view.index.min() if not view.empty else hours.index.max()
    active_end = view.index.max() if not view.empty else hours.index.max()
    screen = detect(start, end, limit=100)
    anomaly_points = [{"timestamp": item["timestamp"], "kw": item["observed_kw"],
                       "baseline_kw": item["baseline_kw"], "score": item["score"]}
                      for item in screen["flags"]
                      if active_start <= pd.Timestamp(item["timestamp"]) <= active_end]
    forecast_result = forecast(horizon, start, end)
    return {"window": window, "actual": actual, "anomalies": anomaly_points,
            "forecast": forecast_result["forecast"], "forecast_model": forecast_result["model"],
            "forecast_caveat": forecast_result["caveat"],
            "scope": {"start": actual[0]["timestamp"] if actual else None,
                      "end": actual[-1]["timestamp"] if actual else None}}


def data_quality() -> dict:
    """Summarize quality from the cleaned records and preparation report, without mock metrics."""
    frame = minute_data()
    report_path = Path(__file__).resolve().parents[1] / "data" / "processed" / "data_quality_report.json"
    report = json.loads(report_path.read_text(encoding="utf-8")) if report_path.exists() else {}
    missing = int(frame[list(METERS)].isna().sum().sum())
    duplicates = int(frame.index.duplicated().sum())
    return {"status": "ready", "records_processed": int(len(frame)),
            "valid_numeric_records": int(frame[list(METERS)].notna().all(axis=1).sum()),
            "missing_values_after_cleaning": missing, "duplicate_timestamps": duplicates,
            "invalid_timestamps_removed": int(report.get("invalid_timestamps_removed", 0)),
            "date_start": frame.index.min().isoformat(), "date_end": frame.index.max().isoformat(),
            "sampling_frequency": "1 minute", "cleaning_applied": bool(report),
            "missing_values_before_by_column": report.get("missing_measurements_before_by_column", {}),
            "cleaning_rules": report.get("cleaning_rules", [])}
