"""Small, offline NLP layer for WattWise query intent and vocabulary normalization.

It is intentionally rule-based and explainable; it is not a general language model.
"""
from __future__ import annotations

import re

STOPWORDS = {"a", "an", "are", "at", "be", "by", "can", "did", "do", "does", "for", "from",
             "how", "i", "in", "is", "it", "me", "my", "of", "on", "or", "please", "show", "the", "there",
             "this", "to", "was", "were", "what", "when", "where", "which", "with", "would", "you", "your",
             "tell", "about", "give", "want", "like", "know", "could", "measured", "much", "many", "didnt"}

SYNONYMS = {
    "electricity": "energy", "electric": "energy", "consumption": "energy", "consumed": "energy", "consume": "energy", "usage": "energy", "used": "energy", "using": "energy",
    "load": "demand", "power": "demand", "kilowatt": "kw", "kilowatts": "kw", "kwh": "energy",
    "peak": "peak", "maximum": "peak", "max": "peak", "highest": "peak", "greatest": "peak",
    "spike": "anomaly", "outlier": "anomaly", "anomalous": "anomaly", "abnormal": "anomaly", "abnormality": "anomaly", "unusual": "anomaly", "strange": "anomaly", "weird": "anomaly", "irregular": "anomaly", "fault": "anomaly", "faulty": "anomaly", "anamoly": "anomaly", "anamolies": "anomaly", "anomoly": "anomaly", "anomolies": "anomaly", "anomalies": "anomaly",
    "forecasting": "forecast", "forcast": "forecast", "forcasting": "forecast", "predict": "forecast", "predicted": "forecast", "prediction": "forecast", "predictions": "forecast", "future": "forecast", "tomorrow": "forecast",
    "rise": "change", "rose": "change", "increased": "change", "increase": "change", "increasing": "change", "increse": "change",
    "decrease": "change", "decreased": "change", "drop": "change", "dropped": "change", "changed": "change", "change": "change", "difference": "change",
    "breakdown": "submeter", "submetering": "submeter", "submeters": "submeter", "metering": "submeter", "appliance": "submeter", "appliances": "submeter", "device": "submeter", "devices": "submeter",
    "kitchen": "submeter1", "cooking": "submeter1", "oven": "submeter1", "microwave": "submeter1", "dishwasher": "submeter1",
    "laundry": "submeter2", "washing": "submeter2", "washer": "submeter2", "dryer": "submeter2",
    "heating": "submeter3", "cooling": "submeter3", "aircon": "submeter3", "airconditioning": "submeter3",
    "amps": "current", "amperage": "current", "amperes": "current", "volts": "voltage", "volt": "voltage",
    "average": "average", "normally": "average", "typical": "average", "trend": "trend", "pattern": "trend",
}

INTENT_TERMS = {
    "anomaly": {"anomaly", "deviation", "flag", "screen", "unexpected", "suspicious"},
    "forecast": {"forecast", "expected", "horizon", "tomorrow", "future", "predict"},
    "usage_mix": {"submeter", "submeter1", "submeter2", "submeter3", "breakdown", "appliance", "device"},
    "meter_lookup": {"voltage", "reactive", "intensity", "current", "submeter", "submeter1", "submeter2", "submeter3"},
    "method_lookup": {"dataset", "source", "missing", "cleaning", "preprocessing", "measurement"},
    "change": {"change", "rise", "drop", "increase", "decrease", "difference"},
    "demand_summary": {"demand", "energy", "peak", "average", "trend", "highest", "mean", "kw", "minimum", "lowest", "daily", "weekday", "weekend", "summary", "summarize", "summarise"},
}

# Phrase rules catch natural questions where the important meaning is spread across words.
PHRASE_INTENTS = {
    "anomaly": (r"\b(any|are there|show me|find|detect|spot|identify).{0,35}\b(odd|strange|weird|unusual|abnormal|irregular|spike|outlier|fault|problem)s?\b",
                r"\b(out of the ordinary|not normal|doesn't look right|does not look right)\b",
                r"\b(is (it|my|the|this) (power|demand|energy|usage|reading) normal|within normal (demand|power|energy))\b"),
    "forecast": (r"\b(what|how much|how high).{0,35}\b(will|going to|expect|likely).{0,25}\b(use|consume|demand|power|energy)\b",
                 r"\b(next day|next week|coming day|in the future)\b",
                 r"\b(forecast accuracy|forecast error|mae|rmse|mape)\b"),
    "usage_mix": (r"\b(which|what).{0,30}\b(appliance|device|meter|room)\b",
                  r"\b(where|what part).{0,25}\b(energy|electricity|power|usage)\b"),
    "change": (r"\b(why|reason).{0,30}\b(increas|ris|drop|decreas|chang|spik)",
               r"\b(why|what happened).{0,35}\b(energy|electricity|power|demand|usage).{0,25}\b(high|low|up|down)\b",
               r"\b(compare|comparison|difference|changed|change over time|increase over time|decrease over time)\b"),
    "meter_lookup": (r"\b(how many|what is|what was|show).{0,25}\b(volts?|voltage|amps?|amperes|current|reactive power)\b",),
    "method_lookup": (r"\b(what does|what do|what is meant by|meaning of|define|definition of).{0,40}\b(mean|represent|sub.?meter|dataset|voltage|reactive|active power|current|other)\b",
                      r"\b(how is|how are).{0,30}\b(calculated|measured|cleaned|prepared)\b",
                      r"\b(dataset|data source|missing readings|data cleaning|preprocessing|measurement units)\b"),
    "demand_summary": (r"\b(how much|how many|tell me|give me|show me).{0,30}\b(energy|electricity|power|demand|consumption|usage)\b",
                       r"\b(when|what time|which day).{0,30}\b(peak|highest|maximum|most)\b",
                       r"\b(when|what time).{0,30}\b(use|using|consume).{0,20}\b(most|least)\b",
                       r"\b(summary|summarize|summarise).{0,30}\b(energy|electricity|power|usage|data)\b",
                       r"\b(weekday|weekdays|workday|workdays).{0,30}\b(weekend|weekends)\b|\b(weekend|weekends).{0,30}\b(weekday|weekdays|workday|workdays)\b",
                       r"\b(weekend|weekends)\b.{0,30}\b(higher|lower|more|less|compare|compared|versus|vs)\b|\b(higher|lower|more|less|compare|compared|versus|vs)\b.{0,30}\b(weekend|weekends)\b"),
}


def normalize_tokens(text: str) -> list[str]:
    """Tokenize, normalize common inflections, and map energy synonyms to canonical terms."""
    folded = text.casefold()
    folded = re.sub(r"\bsub[\s-]*meters?(?:ing)?\b", "submeter", folded)
    folded = re.sub(r"\bsubmeter\s*([123])\b", r"submeter\1", folded)
    folded = re.sub(r"\bair\s+conditioning\b", "airconditioning", folded)
    raw = re.findall(r"[a-z0-9]+", folded)
    normalized = []
    for word in raw:
        if word in STOPWORDS:
            continue
        word = SYNONYMS.get(word, word)
        if word.endswith("ies") and len(word) > 4:
            word = word[:-3] + "y"
        elif word.endswith("s") and len(word) > 4 and word not in {"gas", "this"}:
            word = word[:-1]
        # Canonicalize after light stemming too, so plural forms such as "spikes" match "spike".
        word = SYNONYMS.get(word, word)
        normalized.append(word)
    return normalized



def question_focus(text: str) -> dict:
    """Extract small, explainable entities that let answers target the actual ask."""
    folded = (text or "").casefold()
    tokens = set(normalize_tokens(text or ""))
    submeter = next((number for number in (1, 2, 3) if f"submeter{number}" in tokens), None)
    appliance_aliases = (
        ("dishwasher", (r"\bdishwasher\b",), 1),
        ("oven", (r"\boven\b",), 1),
        ("microwave", (r"\bmicrowave\b",), 1),
        ("washing machine", (r"\bwashing\s+machine\b", r"\bwasher\b"), 2),
        ("tumble dryer", (r"\btumble\s+dryer\b", r"\bdryer\b"), 2),
        ("refrigerator", (r"\brefrigerator\b", r"\bfridge\b"), 2),
        ("lighting", (r"\blighting\b",), 2),
        ("water heating", (r"\bwater\s+heating\b", r"\bwater\s+heater\b"), 3),
        ("air conditioning", (r"\bair\s*conditioning\b", r"\baircon\b"), 3),
    )
    appliance = next((name for name, patterns, _ in appliance_aliases
                      if any(re.search(pattern, folded) for pattern in patterns)), None)
    if submeter is None and appliance:
        submeter = next(number for name, patterns, number in appliance_aliases if name == appliance)
    measurement = next((name for name, terms in (
        ("voltage", {"voltage"}),
        ("current", {"current", "intensity"}),
        ("reactive_power", {"reactive"}),
        ("active_power", {"active"}),
    ) if tokens & terms), None)
    weekdays = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")
    weekday = next((day.title() for day in weekdays if re.search(rf"\b{day}\b", folded)), None)
    horizon = 24
    if re.search(r"\b(next|coming)\s+week\b", folded):
        horizon = 168
    else:
        match = re.search(r"\b(?:next|for|in)\s+(\d{1,3})\s*(hours?|days?)\b", folded)
        if match:
            horizon = int(match.group(1)) * (24 if match.group(2).startswith("day") else 1)
    horizon_was_capped = horizon > 168
    horizon = min(max(horizon, 1), 168)
    return {
        "submeter": submeter,
        "appliance": appliance,
        "measurement": measurement,
        "weekday": weekday,
        "peak_hours": bool(re.search(
            r"\b(peak|highest|maximum|most)\b.{0,24}\b(hours?|times?|periods?)\b"
            r"|\bwhen\b.{0,32}\b(peak|highest|maximum|most)\b"
            r"|\bwhen\b.{0,30}\b(use|using|consume).{0,16}\b(most|least)\b",
            folded,
        )),
        "peak_demand": bool(re.search(r"\b(peak|highest|maximum|max)\b.{0,24}\b(demand|power|load|consumption|energy)\b|\b(demand|power|load|consumption|energy)\b.{0,24}\b(peak|highest|maximum|max)\b", folded)),
        "average_demand": bool(tokens & {"average", "mean", "typical"}) and bool(tokens & {"demand", "energy", "kw", "active"}),
        "minimum": bool(tokens & {"minimum", "lowest", "least", "minimum"}),
        "total_energy": bool(re.search(r"\b(total|overall)\s+(energy|electricity|power|usage|consumption)\b|\bhow much\s+(energy|electricity|power)\b|\b(energy|electricity|power)\s+(used|consumed)\b|\bhow much\b.{0,35}\b(use|used|consume|consumed)\b", folded)),
        "weekend_comparison": bool(re.search(r"\b(weekend|weekends)\b.{0,32}\b(weekday|weekdays|workday|workdays|higher|lower|more|less|compare|compared|versus|vs)\b|\b(weekday|weekdays|workday|workdays|higher|lower|more|less|compare|compared|versus|vs)\b.{0,32}\b(weekend|weekends)\b", folded)),
        "forecast_accuracy": bool(re.search(r"\b(accuracy|accurate|error|mae|rmse|mape)\b", folded)) and bool(re.search(r"\b(forecast|prediction|model|mae|rmse|mape)\b", folded)),
        "appliance_group_question": bool(re.search(r"\b(appliance|device)s?\b", folded)) and appliance is None,
        "trend": bool(tokens & {"trend", "pattern", "over", "change"}),
        "definition": bool(re.search(r"\b(what does\b.{0,30}\bmean|what is meant by|meaning of|define|definition of|explain)\b", folded)
                            or re.search(r"\bwhat is (?:the )?(?:voltage|reactive power|active power|current)(?:[?.!]|$)", folded)
                            or re.search(r"\bwhat is (?:the )?sub.?meter\s*[123](?:[?.!]|$|\s+(?:used for|measured by|responsible for))", folded)),
        "forecast_horizon_hours": horizon,
        "forecast_horizon_was_capped": horizon_was_capped,
    }


def understand(text: str) -> dict:
    """Return explainable intent labels, confidence, and tokens for an incoming query."""
    tokens = normalize_tokens(text)
    token_set = set(tokens)
    scores = {name: len(token_set & terms) for name, terms in INTENT_TERMS.items()}
    matched_phrases = {}
    for intent, patterns in PHRASE_INTENTS.items():
        hits = [pattern for pattern in patterns if re.search(pattern, text, flags=re.IGNORECASE)]
        if hits:
            scores[intent] += len(hits)
            matched_phrases[intent] = len(hits)
    active = [name for name, score in scores.items() if score]
    total_hits = sum(scores.values())
    confidence = min(0.94, 0.5 + 0.09 * total_hits) if active else 0.0
    if len(active) == 1:
        confidence = min(0.95, confidence + 0.1)
    return {"tokens": tokens, "intents": active, "intent_scores": scores,
            "matched_phrases": matched_phrases, "focus": question_focus(text),
            "confidence": round(confidence, 2), "confidence_kind": "uncalibrated heuristic score, not a probability",
            "method": "offline synonym, spelling, phrase, and weighted keyword intent rules"}
