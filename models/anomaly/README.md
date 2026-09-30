# Anomaly screening notes

The runtime detector in `energy_assistant/anomaly.py` combines a weekday-and-hour median absolute deviation score with Isolation Forest candidates. The Isolation Forest is fitted once per process and cached in memory; no model artifact is required.

This dataset has no verified fault labels, so detection precision, recall, and confirmed fault accuracy cannot be measured. A flagged hour is a statistical review candidate, not proof of an equipment fault.
