"""Report chronological holdout metrics for the deterministic seasonal baseline."""
from __future__ import annotations

import json

from energy_assistant.analytics import evaluation


if __name__ == "__main__":
    print(json.dumps(evaluation(), indent=2))
