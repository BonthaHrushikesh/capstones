"""Optional OpenAI-compatible language layer, grounded in local analytical evidence."""
from __future__ import annotations

import json
import os
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def _plain_english_fallback(factual_answer: str) -> str:
    """Make the local, evidence-only answer easier to read without changing facts."""
    replacements = (
        (r"\bestimated active energy\b", "estimated energy use"),
        (r"\bactive power\b", "power use"),
        (r"\bmean household\b", "average household"),
        (r"\bhourly mean demand\b", "average demand for one hour"),
        (r"\bclock-hours\b", "times of day"),
        (r"\bselected range\b", "chosen dates"),
        (r"\bselected household-data scope\b", "chosen dates"),
        (r"\bstatistical review candidates\b", "unusual readings worth checking"),
        (r"\bweekday/hour baseline\b", "usual level for that day and hour"),
        (r"\bdoes not establish a cause\b", "does not show the cause"),
        (r"\bphysical cause\b", "reason"),
        (r"\bsub-meter\b", "submeter"),
    )
    answer = factual_answer.strip()
    for pattern, replacement in replacements:
        answer = re.sub(pattern, replacement, answer, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", answer)


def explain_with_llm(question: str, factual_answer: str, evidence: dict) -> tuple[str, dict]:
    """Use an optional LLM, with a clear local answer when no provider is configured."""
    local_answer = _plain_english_fallback(factual_answer)
    api_key = os.getenv("LLM_API_KEY", "").strip()
    base_url = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    model = os.getenv("LLM_MODEL", "gpt-4o-mini").strip()
    status = {"enabled": bool(api_key), "provider": model if api_key else "local plain-English response",
              "used": False, "message": "LLM is not configured; returned a clear answer from local evidence."}
    if not api_key:
        return local_answer, status

    payload = {"model": model, "temperature": 0.1, "max_tokens": 280,
               "messages": [
                   {"role": "system", "content": (
                       "You explain household electricity analytics in simple everyday English. Answer the user's question first, then give only the useful detail in two to four short sentences. "
                       "Use familiar words: say 'power use' instead of 'active power', 'chosen dates' instead of 'selected range', and 'unusual reading worth checking' instead of technical detection jargon. "
                       "Use only the supplied computed answer and evidence; preserve dates, units, quantities, and important limits. "
                       "Do not add numbers, physical causes, appliance-level claims, grid conditions, or facts. Keep observed, detected, and forecast values distinct. "
                       "If the data cannot show a cause, say that plainly. Do not mention hidden reasoning or unrequested analysis.")},
                   {"role": "user", "content": json.dumps({"question": question,
                       "computed_answer": factual_answer, "evidence": evidence}, ensure_ascii=False)}
               ]}
    request = Request(f"{base_url}/chat/completions", data=json.dumps(payload).encode("utf-8"),
                      headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                      method="POST")
    try:
        with urlopen(request, timeout=12) as response:
            data = json.loads(response.read().decode("utf-8"))
        generated = data["choices"][0]["message"]["content"].strip()
        if not generated or len(generated) > 3000:
            raise ValueError("Provider returned an empty or oversized answer.")
        # GUARDRAIL: reject any numeral the deterministic answer/evidence did not contain.
        allowed = {token.replace(",", "") for token in re.findall(r"\d[\d,]*(?:\.\d+)?%?", factual_answer + json.dumps(evidence))}
        emitted = {token.replace(",", "") for token in re.findall(r"\d[\d,]*(?:\.\d+)?%?", generated)}
        if not emitted.issubset(allowed):
            raise ValueError("Generated answer introduced a number absent from the evidence.")
        status.update({"used": True, "message": "Configured language model phrased the response from computed evidence."})
        return generated, status
    except (HTTPError, URLError, TimeoutError, KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError) as exc:
        status["message"] = f"LLM unavailable or rejected by grounding guardrail; used local answer ({type(exc).__name__})."
        return local_answer, status
