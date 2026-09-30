from pathlib import Path
import os

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import analytics, anomaly, forecasting
from .agents import ask
from .agent_team.decision_guide_agent import run as decision_guide_agent_run
from .agent_team.insight_synthesizer_agent import run as insight_synthesizer_agent_run
from .data import DataSourceError, minute_data
from .keyword_search import search as keyword_search
from .nlp import understand
from .web_ui import HTML
from .workflow import evaluate_query_routing


def synthesize_insight(start: str | None = None, end: str | None = None) -> dict:
    return insight_synthesizer_agent_run(start=start, end=end)


def guide_decision(start: str | None = None, end: str | None = None) -> dict:
    return decision_guide_agent_run(start=start, end=end)

app = FastAPI(title="GridSense AI", version="1.0", description="Evidence-backed household energy intelligence.")
FRONTEND_ROOT = Path(__file__).resolve().parents[1] / "frontend"
FRONTEND_DIST = FRONTEND_ROOT / "dist"
FRONTEND_DIST.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=FRONTEND_DIST), name="static")


class AskBody(BaseModel):
    question: str = Field(min_length=1, max_length=1000)
    start: str | None = Field(default=None, max_length=40)
    end: str | None = Field(default=None, max_length=40)
    context: str | None = Field(default=None, max_length=600)


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
@app.get("/ui", response_class=HTMLResponse, include_in_schema=False)
@app.get("/demo", response_class=HTMLResponse, include_in_schema=False)
def home(): return HTML


@app.get("/health")
def health(): return {"status": "ok", "service": "WattWise"}


@app.get("/ready")
def ready():
    # GUARDRAIL SHOWCASE 6: distinguish a live process from one with usable data.
    try:
        frame = minute_data()
        return {"status": "ready", "records": len(frame), "data_start": frame.index.min().isoformat(),
                "data_end": frame.index.max().isoformat()}
    except DataSourceError as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@app.get("/api/summary")
def get_summary(start: str | None = Query(default=None, max_length=40), end: str | None = Query(default=None, max_length=40)):
    try:
        result = analytics.summary(start, end)
        if "error" in result: raise HTTPException(404, result["error"])
        return result
    except DataSourceError as exc: raise HTTPException(503, str(exc))
    except ValueError as exc: raise HTTPException(422, str(exc))


@app.get("/api/trends")
def get_trends(window: str = Query("7d", pattern="^(1h|6h|24h|7d|30d|1y)$"),
               horizon: int = Query(24, ge=1, le=24),
               start: str | None = Query(default=None, max_length=40), end: str | None = Query(default=None, max_length=40)):
    try: return analytics.timeseries(window, horizon, start, end)
    except DataSourceError as exc: raise HTTPException(503, str(exc))
    except ValueError as exc: raise HTTPException(422, str(exc))


@app.get("/api/data-quality")
def get_data_quality():
    try: return analytics.data_quality()
    except DataSourceError as exc: raise HTTPException(503, str(exc))


@app.get("/api/llm-status")
def get_llm_status():
    return {"enabled": bool(os.getenv("LLM_API_KEY", "").strip()),
            "model": os.getenv("LLM_MODEL", "gpt-4o-mini") if os.getenv("LLM_API_KEY", "").strip() else None,
            "mode": "configured provider" if os.getenv("LLM_API_KEY", "").strip() else "grounded local fallback"}


@app.get("/api/anomalies")
def get_anomalies(start: str | None = Query(default=None, max_length=40), end: str | None = Query(default=None, max_length=40), limit: int = Query(15, ge=1, le=200)):
    try: return anomaly.detect(start, end, limit)
    except DataSourceError as exc: raise HTTPException(503, str(exc))
    except ValueError as exc: raise HTTPException(422, str(exc))


@app.get("/api/forecast")
def get_forecast(horizon: int = Query(24, ge=1, le=168), start: str | None = Query(default=None, max_length=40), end: str | None = Query(default=None, max_length=40)):
    try: return forecasting.forecast(horizon, start, end)
    except DataSourceError as exc: raise HTTPException(503, str(exc))
    except ValueError as exc: raise HTTPException(422, str(exc))


@app.get("/api/evaluation")
def get_evaluation(start: str | None = Query(default=None, max_length=40), end: str | None = Query(default=None, max_length=40)):
    try:
        routing = evaluate_query_routing()
        return {**analytics.evaluation(start, end),
                "anomaly_evaluation": "Not measurable against true faults: dataset has no labeled anomalies.",
                "query_evaluation": routing,
                "groundedness": "Answers return source statistics, specialist trace, methods, and caveats."}
    except DataSourceError as exc: raise HTTPException(503, str(exc))
    except ValueError as exc: raise HTTPException(422, str(exc))


@app.post("/api/ask")
def ask_question(body: AskBody):
    # GUARDRAIL SHOWCASE 7: reject whitespace-only requests and bound input length at the schema.
    if not body.question.strip(): raise HTTPException(422, "Question cannot contain only whitespace.")
    try: return ask(body.question, body.start, body.end, body.context)
    except DataSourceError as exc: raise HTTPException(503, str(exc))
    except ValueError as exc: raise HTTPException(422, str(exc))


@app.get("/api/agents/insight")
def get_insight_report(start: str | None = Query(default=None, max_length=40), end: str | None = Query(default=None, max_length=40)):
    """Run the dedicated insight specialist across analyst, anomaly, and forecast evidence."""
    try: return synthesize_insight(start, end)
    except DataSourceError as exc: raise HTTPException(503, str(exc))
    except ValueError as exc: raise HTTPException(422, str(exc))


@app.get("/api/agents/decision")
def get_decision_guide(start: str | None = Query(default=None, max_length=40), end: str | None = Query(default=None, max_length=40)):
    """Run the dedicated decision guide using demand and anomaly evidence."""
    try: return guide_decision(start, end)
    except DataSourceError as exc: raise HTTPException(503, str(exc))
    except ValueError as exc: raise HTTPException(422, str(exc))


@app.get("/api/search")
def search_energy_evidence(q: str = Query(min_length=1, max_length=200), limit: int = Query(8, ge=1, le=20), start: str | None = Query(default=None, max_length=40), end: str | None = Query(default=None, max_length=40)):
    """Natural-language query understanding plus ranked keyword retrieval."""
    # NLP / retrieval showcase: intent extraction decides which evidence collections to search.
    parsed = understand(q)
    if not parsed["tokens"]:
        return {"query": q, "normalized_terms": [], "result_count": 0, "results": [], "nlp": parsed,
                "message": "Enter a few energy-related keywords to search the evidence."}
    try:
        summary = analytics.summary(start, end)
        anomalies = anomaly.detect(start, end, limit=25) if "anomaly" in parsed["intents"] else None
        future = forecasting.forecast(24, start, end) if "forecast" in parsed["intents"] else None
        results = keyword_search(q, summary, anomalies, future, limit)
        return {**results, "nlp": parsed}
    except DataSourceError as exc: raise HTTPException(503, str(exc))
    except ValueError as exc: raise HTTPException(422, str(exc))
