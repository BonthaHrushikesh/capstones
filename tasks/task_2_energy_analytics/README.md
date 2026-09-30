# Task 2 – Energy Analytics, Anomaly Detection & Forecasting

## 1. Objective
This task implements the core energy intelligence layer for the smart-grid assistant. The project analyzes historical energy demand, identifies unusual consumption patterns, and produces short-term demand forecasts using the processed household energy dataset.

The implementation is already integrated into the active application and uses the dataset stored in:

- `data/processed/household_power_consumption_cleaned.csv`

## 2. Dataset Used
The runtime dataset used by the assistant is the same production dataset used throughout the project:

- `data/processed/household_power_consumption_cleaned.csv`

This dataset contains timestamped power-consumption measurements, including active power, reactive power, voltage, current intensity, and sub-meter readings.

## 3. Implemented Capabilities
The project includes the following functional components:

### 3.1 Analytics
The analytics layer is implemented in `energy_assistant/analytics.py`.

It provides:
- summary statistics for the selected time range
- peak-demand detection
- hourly, daily, and monthly energy patterns
- largest daily change detection
- energy-mix aggregation by sub-meter
- measurement summaries for voltage, current, and reactive power

### 3.2 Anomaly Detection
The anomaly detection logic is implemented in `energy_assistant/anomaly.py`.

It uses:
- robust weekday-hour median baseline comparison
- median absolute deviation scoring
- Isolation Forest as a secondary detection signal
- a guardrail to limit result volume for API consumers

This allows the system to highlight unusual consumption behavior without treating all flagged points as confirmed equipment faults.

### 3.3 Forecasting
The forecasting logic is implemented in `energy_assistant/forecasting.py`.

It provides:
- short-horizon hourly demand forecast generation
- weekly seasonal-naive forecasting when adequate history exists
- daily seasonal fallback behavior when full weekly continuity is absent
- median-based fallback strategies for limited historical data
- guardrails for short/unstable history and stale data warnings

### 3.4 Evaluation Metrics
The evaluation function is in `energy_assistant/analytics.py` and produces:
- MAE
- RMSE
- MAPE

This evaluation is based on a chronological holdout strategy to assess the forecasting approach on unseen recent data.

## 4. Requirement Coverage
The implemented solution satisfies the task requirements as follows:

| Requirement | Status |
|---|---|
| identify consumption trends | ✅ Implemented |
| peak-demand periods | ✅ Implemented |
| seasonal patterns | ✅ Implemented |
| unusual consumption behavior | ✅ Implemented |
| changes in energy demand | ✅ Implemented |
| anomaly detection | ✅ Implemented |
| time-series forecasting | ✅ Implemented |
| forecast evaluation using MAE, RMSE, MAPE | ✅ Implemented |

## 5. Files Relevant to This Task
- `energy_assistant/analytics.py`
- `energy_assistant/anomaly.py`
- `energy_assistant/forecasting.py`
- `energy_assistant/data.py`
- `data/processed/household_power_consumption_cleaned.csv`

## 6. Result
This task is satisfied in the current project codebase. The project already contains the analytics, anomaly detection, and forecasting functionality required for the assignment, and it is working against the repository’s real processed energy dataset.

The solution is production-ready for the current project scope and remains aligned with the original task specification.
