AGENT_PROFILES = [
    {
        "name": "Energy Data Analyst",
        "role": "Historical consumption and operational data specialist",
        "focus": "Loads the smart-grid dataset, validates timestamps, filters time ranges, and extracts summary signals such as mean demand, peak hours and daily trends.",
        "function": "Builds the evidence base from raw smart-grid observations and flags the key metrics that drive the other agents.",
        "badge": "DATA"
    },
    {
        "name": "Anomaly Investigator",
        "role": "Deviation and abnormal behavior specialist",
        "focus": "Screens for unusual demand hours, compares each reading with a typical weekday/hour baseline, and ranks the strongest outlier signals.",
        "function": "Identifies suspicious periods and provides the evidence needed for engineering review or operational follow-up.",
        "badge": "ANOMALY"
    },
    {
        "name": "Forecast Specialist",
        "role": "Demand prediction and horizon planning specialist",
        "focus": "Uses historical patterns to estimate upcoming demand and create a forward-looking operational baseline for the next planning window.",
        "function": "Generates forecasted demand values and explains how the near-term operating outlook is formed.",
        "badge": "FORECAST"
    },
    {
        "name": "Insight Synthesizer",
        "role": "Evidence-backed insight and narrative specialist",
        "focus": "Combines findings from the analytics and specialist agents into a coherent, source-grounded answer to the user’s question.",
        "function": "Translates data findings into readable insight statements and explains how the answer was derived from the underlying evidence.",
        "badge": "INSIGHT"
    },
    {
        "name": "Decision Guide",
        "role": "Operational recommendation specialist",
        "focus": "Converts the final evidence and forecast into practical actions for demand management, response planning, and operational review.",
        "function": "Provides the recommended next step for grid operators, energy teams, and business users based on the computed signals.",
        "badge": "ACTION"
    }
]
