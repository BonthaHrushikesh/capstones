from __future__ import annotations

import pandas as pd
import numpy as np
from functools import lru_cache
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from .data import POWER, hourly_data, select_hours


@lru_cache(maxsize=1)
def _isolation_forest_output() -> tuple[pd.Series, pd.Series]:
    """Fit once on chronological household measurements plus cyclic calendar features."""
    frame = hourly_data().dropna(subset=[POWER]).copy()
    columns = [POWER, "Global_reactive_power", "Voltage", "Global_intensity"]
    hour_angle = frame.index.hour.to_numpy() * (2 * 3.141592653589793 / 24)
    weekday_angle = frame.index.dayofweek.to_numpy() * (2 * 3.141592653589793 / 7)
    values = frame[columns].to_numpy(dtype=float)
    features = pd.DataFrame(values, index=frame.index, columns=columns)
    features["hour_sin"], features["hour_cos"] = np.sin(hour_angle), np.cos(hour_angle)
    features["weekday_sin"], features["weekday_cos"] = np.sin(weekday_angle), np.cos(weekday_angle)
    scaled = StandardScaler().fit_transform(features)
    detector = IsolationForest(n_estimators=120, contamination=0.01, random_state=42, n_jobs=1)
    labels = detector.fit_predict(scaled)
    scores = detector.decision_function(scaled)
    return pd.Series(labels == -1, index=frame.index), pd.Series(scores, index=frame.index)


def detect(start: str | None = None, end: str | None = None, limit: int = 25) -> dict:
    # GUARDRAIL SHOWCASE 4: cap work/result size for callers outside the HTTP API.
    limit = min(max(int(limit), 1), 200)
    df = select_hours(start, end).dropna(subset=[POWER]).copy()
    if df.empty:
        return {"count": 0, "flags": [], "method": "weekday-hour robust MAD",
                "caveat": "No hourly observations were available in the selected date range."}
    slot = df.index.dayofweek * 24 + df.index.hour
    grouped = df[POWER].groupby(slot)
    baseline = grouped.transform("median")
    mad = grouped.transform(lambda values: (values - values.median()).abs().median())
    global_scale = float((df[POWER] - df[POWER].median()).abs().median()) * 1.4826
    scale = (mad * 1.4826).where(mad > 1e-9, max(global_scale, 1e-5))
    score = (df[POWER] - baseline) / scale
    try:
        iso_flag, iso_score = _isolation_forest_output()
        in_scope = iso_flag.reindex(df.index, fill_value=False)
        combined = (score.abs() >= 4.5) | in_scope
        detector_method = "Isolation Forest + weekday-hour robust MAD"
    except (ValueError, RuntimeError, ImportError):
        in_scope = pd.Series(False, index=df.index)
        iso_score = pd.Series(float("nan"), index=df.index)
        combined = score.abs() >= 4.5
        detector_method = "weekday-hour robust MAD (Isolation Forest fallback)"
    flagged = score[combined].sort_values(key=lambda values: values.abs(), ascending=False)
    full_power = hourly_data()[POWER].dropna()
    def context_value(timestamp, offset_hours):
        at = timestamp - pd.Timedelta(hours=offset_hours)
        value = full_power.asof(at)
        return round(float(value), 3) if pd.notna(value) else None
    flags = [{"timestamp": ts.isoformat(), "observed_kw": round(float(df.at[ts, POWER]), 3),
              "baseline_kw": round(float(baseline.at[ts]), 3), "score": round(float(score.at[ts]), 2),
              "deviation_kw": round(float(df.at[ts, POWER] - baseline.at[ts]), 3),
              "isolation_forest_candidate": bool(in_scope.get(ts, False)),
              "isolation_forest_score": round(float(iso_score.get(ts, float("nan"))), 4)
                  if pd.notna(iso_score.get(ts, float("nan"))) else None,
              "previous_hour_kw": context_value(ts, 1), "previous_day_kw": context_value(ts, 24),
              "previous_week_kw": context_value(ts, 168)} for ts in flagged.head(limit).index]
    return {"count": int(combined.sum()), "flags": flags, "method": detector_method, "threshold": 4.5,
            "scope_hours": int(len(df)), "caveat": "Statistical screening candidates; not verified equipment faults."}
