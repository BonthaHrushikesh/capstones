"""Run lightweight readiness checks across data, routing, evaluation, and frontend build."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from energy_assistant.data import minute_data
from energy_assistant.workflow import evaluate_query_routing
from energy_assistant.analytics import evaluation

def main() -> None:
    frame = minute_data()
    routing = evaluate_query_routing()
    metrics = evaluation()
    report = {
        "data_ready": not frame.empty,
        "rows": len(frame),
        "frontend_built": (ROOT / "frontend" / "dist" / "index.html").exists(),
        "query_routing": routing,
        "forecast_evaluation": metrics,
    }
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
