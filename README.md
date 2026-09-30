# GridSense AI

GridSense AI turns historical electricity meter readings into demand analytics, anomaly review candidates, short-horizon forecasts, and evidence-backed answers. It is a demonstration and decision-support tool for one household; it is not a live utility-grid control system.

See [the complete project workflow architecture](architecture/architecture.md) for the end-to-end data, dashboard, API, and Copilot flows.

## Quick start

Requirements: Python 3.10+ and Node.js 20+.

From the project root in PowerShell:

~~~
python -m pip install -r requirements.txt
cd frontend
npm ci
npm run build
cd ..
python run.py
~~~

Open <http://127.0.0.1:8001>. The API reference is at <http://127.0.0.1:8001/docs>. Build the frontend before launching the API; FastAPI serves the built React app from frontend/dist.

For frontend hot reload, keep python run.py running in one terminal and run npm run dev from frontend in another. Open the Vite URL shown in the terminal (normally <http://127.0.0.1:5173>); its /api proxy connects to FastAPI on port 8001.

## Dataset and preparation

The runtime dataset is data/processed/household_power_consumption_cleaned.csv. It contains 2,075,259 one-minute observations from one household, from 2006-12-16 through 2010-11-26. The original UCI text file is not included. The cleaned runtime CSV and quality report are included so the project can run without downloading the raw file.

If you have the original semicolon-delimited file, place it at data/raw/household_power_consumption.txt and run:

~~~
python scripts/preprocess.py
~~~

Use --input and --output to supply different paths. Preparation parses day-first timestamps, removes invalid timestamps, keeps the last duplicate, interpolates internal gaps up to five minutes, median-fills remaining missing meter values, and writes a quality report beside the output. It does not modify the source file.

## What the dashboard provides

- Overview: date-scoped demand KPIs, trend chart, anomaly summary, and Copilot entry point.
- Energy Analytics: hourly, weekday, daily, and sub-meter group summaries.
- Anomaly Detection: ranked unusual-hour candidates with comparison evidence.
- Demand Forecast: historical seasonal baseline forecasts and chronological holdout metrics.
- AI Copilot: natural-language questions, computed evidence, retrieved references, and an agent trace.
- Insights: combined analyst findings and cautious next-step guidance.
- Reports: daily summary and CSV export.
- Data Quality & Evaluation: cleaned-data checks, forecast metrics, and saved Copilot feedback.

## How the analysis works

The backend resamples minute readings into hourly records. Demand summaries use Global_active_power; sub-meter totals are converted from watt-hours to kWh and grouped as reported by the dataset.

Anomaly screening combines Isolation Forest candidates with a weekday-and-hour median absolute deviation (MAD) score. A flag means “review this reading,” not “a fault occurred.” The dataset has no verified fault labels, so fault-detection accuracy cannot be measured.

Forecasts use a weekly seasonal-naive baseline when continuous history is available, with daily and median fallbacks for shorter or incomplete histories. Forecasts use historical readings and are not predictions of present-day demand. Evaluation uses a chronological holdout and reports MAE, RMSE, and MAPE; the UI and API include the evaluation caveat.

On the included dataset, the current 672-hour holdout reports MAE 0.7145 kW, RMSE 1.0031 kW, and MAPE 84.97%. The relatively high MAPE means this baseline should be presented as a simple reference, not as a high-accuracy predictor; percentage error is especially sensitive when actual demand is low.

Copilot classifies supported question intents with transparent rules, applies date and topic guardrails, computes only the relevant evidence, and retrieves related passages with intent-aware keyword ranking. The default response is deterministic and local. An optional OpenAI-compatible model can rephrase a computed answer; it cannot access the dataset directly, and a numeric grounding check rejects unsupported numbers before falling back to the local answer.

The five named agents are Python modules called in-process. They are not separate deployed services or autonomous external agents.

## API

Key endpoints: /health, /ready, /api/summary, /api/trends, /api/data-quality, /api/anomalies, /api/forecast, /api/evaluation, /api/ask, /api/search, /api/llm-status, /api/agents/insight, and /api/agents/decision.

Set ENERGY_DATA_PATH to point to a different cleaned CSV with the required timestamp and meter columns. Date inputs must be timezone-naive and inside the dataset’s recorded coverage.

## Optional language-model phrasing

The app works without a provider key. To enable OpenAI-compatible phrasing, set these environment variables before starting the backend:

~~~
$env:LLM_API_KEY="your-provider-key"
$env:LLM_BASE_URL="https://api.openai.com/v1"
$env:LLM_MODEL="gpt-4o-mini"
python run.py
~~~

The key stays in the backend environment. Never commit real secrets.

## Validation

From the project root:

~~~
python -m pytest
python scripts/validate_project.py
npm --prefix frontend run typecheck
npm --prefix frontend run build
~~~

## Project layout

- energy_assistant/: data loading, analytics, anomaly detection, forecasting, API, NLP, retrieval, guardrails, and agent modules.
- frontend/src/: React pages, reusable components, API client, and styles.
- data/processed/: runtime cleaned dataset and preparation report.
- tasks/: coursework-specific preparation and analytics artifacts.
- tests/: Python tests for API, data, analytics, anomalies, forecasts, and agent routing.
- architecture/: architecture notes and diagram source.

## Scope and limitations

The source contains one historical household, not regions or a modern live grid. It has no weather, occupancy, tariffs, individual appliance event labels, or verified fault labels. Sub-meter readings describe groups, not exact appliance usage. Statistical anomaly flags do not prove equipment faults; forecasts are planning baselines and can perform poorly on low or changing demand. Do not present the results as regional grid conditions or current consumption.

