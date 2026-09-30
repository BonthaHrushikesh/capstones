"""Warm and summarize the current in-memory Isolation Forest detector."""
from __future__ import annotations

import json

from energy_assistant.anomaly import _isolation_forest_output


def main() -> None:
    candidates, scores = _isolation_forest_output()
    print(json.dumps({
        "model": "IsolationForest",
        "persistence": "in-memory cache; no pickle artifact is produced",
        "hours_scored": len(scores),
        "candidate_hours": int(candidates.sum()),
        "score_min": float(scores.min()),
        "score_max": float(scores.max()),
    }, indent=2))


if __name__ == "__main__":
    main()
