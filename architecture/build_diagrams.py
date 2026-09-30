"""Build the layered architecture and workflow SVG sheets from editable Python source."""
from __future__ import annotations

from html import escape
from pathlib import Path
from textwrap import wrap

ROOT = Path(__file__).resolve().parent
WIDTH, HEIGHT = 2700, 1600

COLORS = {
    "source": ("#edf4ff", "#7394c2", "#28517f"),
    "data": ("#edf8f3", "#66a68b", "#276a4e"),
    "analysis": ("#fff7e7", "#c89c38", "#81600d"),
    "api": ("#edf7fa", "#5d9eab", "#23606b"),
    "ai": ("#f4f0ff", "#8d78c6", "#5b438f"),
    "ui": ("#eef7f2", "#68a388", "#296b4f"),
    "storage": ("#f1f3f6", "#9299a4", "#535d6a"),
    "guard": ("#fff1ee", "#cf806e", "#8b4537"),
    "neutral": ("#ffffff", "#ccd2dc", "#273244"),
}


class Diagram:
    def __init__(self, title: str, subtitle: str, page: str):
        self.parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-label="{escape(title)}">',
            f"<title>{escape(title)}</title>",
            '<defs><marker id="arrow" markerWidth="12" markerHeight="12" refX="10" refY="6" orient="auto"><path d="M0 0 L12 6 L0 12 Z" fill="#667085"/></marker>',
            '<style>text{font-family:Segoe UI,Arial,sans-serif}.canvas{fill:#f5f6f8}.ink{fill:#172033}.muted{fill:#526071}.label{font-size:18px;font-weight:700;letter-spacing:1.3px}.title{font-size:42px;font-weight:750}.subtitle{font-size:21px}.card-title{font-size:23px;font-weight:700}.body{font-size:18px}.small{font-size:16px}.tiny{font-size:14px}.center{text-anchor:middle}.panel{fill:#fff;stroke:#d8dde5;stroke-width:2}.arrow{fill:none;stroke:#667085;stroke-width:3;marker-end:url(#arrow)}.flowline{fill:none;stroke:#8791a0;stroke-width:2.5}</style></defs>',
            f'<rect class="canvas" width="{WIDTH}" height="{HEIGHT}"/>',
            f'<text x="55" y="58" class="label" fill="#765a12">AI-POWERED SMART GRID ENERGY INTELLIGENCE ASSISTANT</text>',
            f'<text x="55" y="112" class="title ink">{escape(title)}</text>',
            f'<text x="55" y="151" class="subtitle muted">{escape(subtitle)}</text>',
            f'<text x="2645" y="58" text-anchor="end" class="small muted">{escape(page)}</text>',
        ]

    def rect(self, x, y, w, h, fill="#fff", stroke="#d8dde5", radius=15, stroke_width=2):
        self.parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width}"/>')

    def text(self, x, y, value, cls="body ink", anchor="start", color=None):
        style = f' class="{cls}" text-anchor="{anchor}"'
        if color:
            style += f' fill="{color}"'
        self.parts.append(f'<text x="{x}" y="{y}"{style}>{escape(str(value))}</text>')

    def panel(self, x, y, w, h, title, kind="neutral"):
        fill, stroke, accent = COLORS[kind]
        self.rect(x, y, w, h, "#ffffff", "#d7dce4", 18)
        self.rect(x, y, w, 52, fill, fill, 16, 0)
        self.rect(x, y + 40, w, 12, fill, fill, 0, 0)
        self.rect(x, y, 8, h, accent, accent, 4, 0)
        self.text(x + 28, y + 35, title, "label", color=accent)

    def card(self, x, y, w, h, title, lines=(), kind="neutral", center=False, title_size=23, line_size=26):
        fill, stroke, accent = COLORS[kind]
        self.rect(x, y, w, h, fill, stroke, 13, 2)
        if center:
            tx, anchor = x + w / 2, "middle"
        else:
            tx, anchor = x + 21, "start"
        title_lines = wrap(title, width=max(12, int((w - 36) / (title_size * .58)))) or [title]
        for index, title_line in enumerate(title_lines):
            self.text(tx, y + 34 + index * (title_size + 5), title_line, "card-title", anchor, accent)
        font_size = 18 if line_size >= 17 else 16
        max_chars = max(14, int((w - 42) / (font_size * .53)))
        content_y = y + 70 + (len(title_lines) - 1) * (title_size + 5)
        row = 0
        for line in lines:
            for wrapped in wrap(line, width=max_chars) or [""]:
                self.text(tx, content_y + row * line_size, wrapped, "body muted" if line_size >= 17 else "small muted", anchor)
                row += 1

    def chip(self, x, y, w, label, kind="neutral"):
        fill, stroke, accent = COLORS[kind]
        self.rect(x, y, w, 42, fill, stroke, 21, 1.5)
        self.text(x + w / 2, y + 27, label, "small", "middle", accent)

    def arrow(self, x1, y1, x2, y2, label=None, label_y=None):
        self.parts.append(f'<path d="M{x1} {y1} L{x2} {y2}" class="arrow"/>')
        if label:
            self.text((x1 + x2) / 2, label_y or min(y1, y2) - 12, label, "tiny muted", "middle")

    def flow_card(self, x, y, w, h, number, title, lines, kind):
        self.card(x, y, w, h, title, lines, kind, center=True, title_size=21, line_size=18)
        self.rect(x + w / 2 - 20, y - 13, 40, 30, COLORS[kind][2], COLORS[kind][2], 15, 0)
        self.text(x + w / 2, y + 8, number, "small", "middle", "#ffffff")

    def save(self, filename: str):
        self.parts.append("</svg>")
        (ROOT / filename).write_text("\n".join(self.parts), encoding="utf-8")


def overview():
    d = Diagram(
        "Complete Workflow Architecture",
        "End-to-end system view. Follow the numbered flow, then use the lower panels for component and storage detail.",
        "1 / 3  SYSTEM OVERVIEW",
    )
    nodes = [
        (210, "Raw energy data", ["UCI household CSV", "Date, time, 7 meters"], "source"),
        (220, "Data ingestion", ["Read semicolon CSV", "Combine date + time"], "source"),
        (245, "Clean + validate", ["Timestamps and numbers", "Remove duplicates, fill gaps"], "data"),
        (245, "Time-series prep", ["Datetime index, minute rows", "Hourly means and kWh fields"], "data"),
        (375, "Analytics + AI engine", ["Energy analytics", "Anomaly detection", "Forecasting + evaluation"], "analysis"),
        (220, "Structured results", ["Metrics, trends, evidence", "Forecasts, caveats, trace"], "analysis"),
        (220, "API / backend", ["FastAPI routes", "Validate and return JSON"], "api"),
        (235, "AI assistant", ["Understand question", "Select evidence + explain"], "ai"),
        (235, "Web dashboard", ["Charts, tables, AI chat", "Date-scoped pages"], "ui"),
        (175, "User insights", ["Review evidence", "Plan next steps"], "ui"),
    ]
    x, y, gap, h = 38, 220, 16, 190
    for index, (w, title, lines, kind) in enumerate(nodes):
        d.flow_card(x, y, w, h, str(index + 1), title, lines, kind)
        if index < len(nodes) - 1:
            d.arrow(x + w + 2, y + h / 2, x + w + gap - 4, y + h / 2)
        x += w + gap

    d.panel(38, 465, 830, 555, "DATA INPUT, QUALITY AND PREPARATION", "data")
    d.card(65, 535, 375, 160, "Source columns", [
        "Date + Time; Global Active Power",
        "Global Reactive Power; Voltage",
        "Global Intensity; Sub-metering 1-3",
        "Raw source file is optional at runtime",
    ], "source")
    d.card(462, 535, 375, 160, "Cleaning rules", [
        "Drop invalid timestamps; keep last duplicate",
        "Coerce seven meter columns to numeric",
        "Interpolate internal gaps up to 5 minutes",
        "Median-fill remaining missing readings",
    ], "data")
    d.card(65, 720, 772, 145, "Quality report + API checks", [
        "Loaded/cleaned records, missing values, duplicates, invalid times",
        "Date coverage and applied cleaning rules; API reports 1-minute sampling",
        "Runtime validates schema, numeric data, timestamps, and date bounds",
    ], "data")
    d.card(65, 890, 772, 115, "Time-series preparation", [
        "Datetime index; hour/weekday/date/month groupings; hourly means",
        "Active energy = sum / 60; sub-meter Wh = hourly sum / 1000; Other = residual",
    ], "data")

    d.panel(892, 465, 930, 555, "ANALYTICS AND MACHINE-LEARNING MODULES", "analysis")
    d.card(918, 535, 425, 205, "Energy analytics", [
        "Mean, max, P95, peak timestamp and hours",
        "Weekday profile; daily and monthly trends",
        "Total kWh; estimated sub-meter mix",
        "Voltage, current, and reactive-power means",
    ], "analysis")
    d.card(1360, 535, 435, 205, "Anomaly detection", [
        "Weekday-hour median + robust MAD score",
        "Isolation Forest candidate signal",
        "Combine candidates; rank by MAD score",
        "Unusual patterns are review candidates",
    ], "analysis")
    d.card(918, 765, 425, 205, "Forecasting", [
        "Check continuity and history sufficiency",
        "168-hour weekly, 24-hour daily fallback",
        "Recent median / insufficient-history fallback",
        "Bound horizon to 1-168 hours; stale warning",
    ], "analysis")
    d.card(1360, 765, 435, 205, "Forecast evaluation", [
        "Chronological train/test holdout",
        "MAE, RMSE, MAPE; minimum 48 hours",
        "MAPE denominator floor: 0.1 kW",
        "Evaluation baseline is computed separately",
    ], "analysis")

    d.panel(1845, 465, 817, 555, "APPLICATION AND USER EXPERIENCE", "api")
    d.card(1870, 535, 765, 135, "API / backend", [
        "GET summary, trends, anomalies, forecast, evaluation, quality, search",
        "POST /api/ask; date/parameter validation; HTTP error handling",
        "JSON responses connect React pages to Python calculations",
    ], "api")
    d.card(1870, 690, 765, 145, "AI Energy Intelligence Assistant", [
        "Rule-based query understanding; identify intent and parameters",
        "Call requested backend calculations; rank keyword evidence",
        "Build factual answer + trace; optional LLM phrasing is grounding-checked",
    ], "ai")
    d.card(1870, 855, 765, 135, "Web dashboard", [
        "Overview / Analytics / Anomalies / Forecast / Insights / Reports",
        "Data Quality / Evaluation / AI Chat; renders charts and tables",
        "Responses and feedback are shown in the browser",
    ], "ui")

    d.panel(38, 1050, 1280, 310, "DATA STORAGE", "storage")
    d.card(62, 1120, 295, 190, "Raw", ["Original semicolon CSV", "Not bundled; optional", "for preprocessing"], "storage")
    d.card(375, 1120, 295, 190, "Processed", ["Cleaned minute CSV", "Hourly DataFrame is", "derived in memory"], "storage")
    d.card(688, 1120, 295, 190, "Metadata", ["Quality JSON", "Cleaning rules and", "source date coverage"], "storage")
    d.card(1001, 1120, 295, 190, "Results", ["Returned as API JSON", "No results database", "Chat evaluation in browser"], "storage")

    d.panel(1345, 1050, 1317, 310, "GUARDRAILS AND RELIABILITY", "guard")
    d.chip(1370, 1120, 290, "Missing / invalid data checks", "guard")
    d.chip(1675, 1120, 290, "Duplicate and date validation", "guard")
    d.chip(1980, 1120, 290, "History and continuity checks", "guard")
    d.chip(2285, 1120, 340, "Stale forecast warning", "guard")
    d.chip(1370, 1180, 290, "Anomaly API cap: 200", "guard")
    d.chip(1675, 1180, 290, "Dashboard requests up to 100", "guard")
    d.chip(1980, 1180, 290, "MAPE floor: 0.1 kW", "guard")
    d.chip(2285, 1180, 340, "Chronological holdout + errors", "guard")
    d.text(1380, 1285, "Limits shown match the implementation; anomaly flags are not confirmed faults.", "small muted")
    d.text(55, 1510, "Runtime note: the included cleaned CSV is read by FastAPI; agent modules run in-process and are not separate services.", "small muted")
    d.save("project-architecture.svg")


def analytics_detail():
    d = Diagram(
        "Analytics and AI Engine - Technical Detail",
        "The four modules share date-scoped hourly data. Branch steps and limits below follow the Python implementation.",
        "2 / 3  ANALYTICS ENGINE",
    )
    d.panel(38, 200, 1280, 600, "A. ENERGY ANALYTICS", "analysis")
    d.card(68, 275, 390, 155, "Input", ["Selected hourly data", "Global_active_power", "Sub-meter energy fields"], "data")
    d.arrow(470, 350, 520, 350)
    d.card(535, 250, 750, 260, "Demand statistics", [
        "Mean active power; maximum hourly mean and timestamp",
        "P95 demand; minimum; top three clock-hour averages",
        "Weekday profile; daily and monthly trends; daily change",
        "Total estimated kWh; sub-meter 1/2/3 + Other residual",
        "Voltage, current (Global Intensity), reactive-power means",
    ], "analysis")
    d.arrow(910, 520, 910, 565)
    d.card(225, 585, 900, 160, "Energy insights", [
        "Structured summary, hourly profiles, daily/monthly series, evidence strings",
        "Used by dashboard pages, Copilot, composed insight and decision routes",
    ], "analysis")
    d.card(1160, 585, 130, 160, "API", ["JSON", "metrics"], "api", center=True)

    d.panel(1360, 200, 1302, 600, "B. ANOMALY DETECTION", "analysis")
    d.card(1390, 275, 260, 135, "Hourly demand", ["Apply selected dates", "Drop missing power"], "data")
    d.arrow(1660, 343, 1690, 343)
    d.card(1700, 275, 285, 135, "Weekday + hour", ["Group matching slots", "Calculate slot median"], "analysis")
    d.arrow(1995, 343, 2025, 343)
    d.card(2035, 275, 260, 135, "Robust deviation", ["MAD x 1.4826", "Flag |score| >= 4.5"], "analysis")
    d.arrow(2305, 343, 2335, 343)
    d.card(2345, 275, 285, 135, "Isolation Forest", ["Cached hourly model", "Separate candidate flag"], "analysis")
    d.card(1410, 465, 540, 220, "Combine and rank", [
        "Candidate = MAD threshold OR Isolation Forest flag",
        "Sort candidates by absolute MAD score",
        "Return observed, baseline, score, and prior-hour/day/week values",
    ], "analysis")
    d.arrow(1980, 575, 2025, 575)
    d.card(2040, 465, 570, 220, "Result limit and meaning", [
        "API accepts limit 1-200; direct function caps at 200",
        "Dashboard currently requests up to 100 results",
        "Anomaly result is a statistical review candidate, not a fault",
    ], "guard")
    d.text(1410, 735, "Fallback: if Isolation Forest cannot run, use weekday-hour MAD alone.", "small muted")

    d.panel(38, 835, 1280, 600, "C. FORECASTING", "analysis")
    d.card(68, 915, 315, 145, "Select history", ["Filter date range", "Exclude hours <45 minutes", "Require at least 3 points"], "data")
    d.arrow(390, 988, 425, 988)
    d.card(435, 915, 340, 145, "History continuity", ["168 continuous hours?", "Else 24 continuous hours?", "Else use median fallback"], "analysis")
    d.arrow(785, 988, 820, 988)
    d.card(830, 890, 455, 205, "Fallback hierarchy", [
        "1. Weekly seasonal-naive: repeat prior 168-hour pattern",
        "2. Daily seasonal: repeat prior 24-hour pattern",
        "3. Recent median when >=24 hourly points",
        "4. Insufficient-history placeholder below that",
    ], "analysis")
    d.card(68, 1120, 1217, 225, "Forecast output and safeguards", [
        "Generate next N hours; horizon is bounded to 1-168 hours",
        "Return model, fallback_used, history_end, mean and hourly values",
        "Warn if latest selected reading is older than 7 days",
        "Caveat: historical baseline only; no weather or occupancy inputs",
    ], "api")

    d.panel(1360, 835, 1302, 600, "D. FORECAST EVALUATION", "analysis")
    d.card(1390, 915, 315, 160, "Historical series", ["Selected hourly power", "At least 48 hours required"], "data")
    d.arrow(1710, 995, 1745, 995)
    d.card(1755, 915, 365, 160, "Chronological split", ["Final 24 to 672 hours held out", "Train only on earlier values", "No future-data leakage"], "analysis")
    d.arrow(2125, 995, 2160, 995)
    d.card(2170, 915, 445, 160, "Seasonal-naive predictions", ["168-hour lag if training >=168 hours", "Otherwise 24-hour lag"], "analysis")
    d.arrow(2390, 1085, 2390, 1120)
    d.card(1485, 1140, 1030, 185, "Evaluation metrics", [
        "MAE: average absolute error | RMSE: error with larger misses weighted more",
        "MAPE: percentage error; denominator is floored at 0.1 kW near zero",
        "Forecast evaluation is a separate holdout calculation, not the live forecast output",
    ], "analysis")
    d.save("analytics-engine.svg")


def application_flow():
    d = Diagram(
        "API, Assistant and Dashboard Workflow",
        "A request enters FastAPI, the Copilot selects supported local evidence, and React displays structured results.",
        "3 / 3  REQUEST AND USER FLOW",
    )
    d.panel(38, 200, 820, 540, "API / APPLICATION LAYER", "api")
    d.card(68, 275, 355, 205, "Request path", [
        "GET focused analytics endpoints",
        "POST /api/ask(question, dates, context)",
        "Validate request length and date parameters",
        "Apply topic, date and context guardrails",
        "Map data errors to HTTP responses",
    ], "api")
    d.card(448, 275, 375, 205, "Response shape", [
        "Endpoint-specific JSON metrics",
        "Copilot: answer + evidence + trace",
        "NLP interpretation + search results",
        "Forecast model and caveats",
        "No results database; results returned to caller",
    ], "api")
    d.card(68, 510, 755, 185, "Important routes", [
        "GET /api/summary, /trends, /anomalies, /forecast, /evaluation",
        "GET /api/data-quality, /search, /agents/insight, /agents/decision",
        "POST /api/ask; FastAPI also serves the built React app",
    ], "api")

    d.panel(885, 200, 835, 540, "AI ENERGY INTELLIGENCE ASSISTANT", "ai")
    d.card(915, 275, 775, 245, "Question understanding", [
        "Rule-based token normalization, synonyms, intents and parameter extraction",
        "Supported focus: date scope, sub-meter, measurement, weekday, forecast horizon",
        "Guardrails ask for clarification when the dataset cannot answer the request",
        'Example: "What were the peak demand hours?"',
        'Example: "Did anything unusual happen yesterday?"',
        'Example: "What is the expected demand for the next 24 hours?"',
        'Example: "How much energy was consumed this month?"',
    ], "ai")
    d.card(915, 545, 370, 155, "Evidence-first answer", [
        "Call only the requested calculations; rank keyword evidence; compose facts + limits + trace",
    ], "analysis")
    d.card(1300, 545, 390, 155, "Optional language model", [
        "No key = local answer; configured model may rephrase; unsupported numbers are rejected",
    ], "ai")

    d.panel(1748, 200, 914, 540, "FRONTEND / PRESENTATION LAYER", "ui")
    d.card(1778, 275, 420, 205, "Dashboard sections", [
        "Overview: average, max, total energy, P95",
        "Analytics: demand, daily/monthly, peak hours",
        "Anomalies: time, observed, baseline, score",
        "Forecast: history, values, model, caveat",
    ], "ui")
    d.card(2218, 275, 414, 205, "More dashboard sections", [
        "Data Quality: records, missing, duplicates, rate",
        "AI Chat: question, answer, evidence, rating",
        "Insights, reports and CSV export",
        "Date scope passed to backend endpoints",
    ], "ui")
    d.card(1778, 510, 854, 185, "How results are shown", [
        "React pages call the JSON API through services/api.ts",
        "Charts, tables, metrics and evidence panels render returned values",
        "Chat evaluation and feedback are saved in browser localStorage",
    ], "ui")

    d.panel(38, 780, 2624, 410, "EXAMPLE END-TO-END QUERY FLOW", "analysis")
    d.text(70, 840, 'User asks: "What is the expected electricity demand for tomorrow?"', "card-title ink")
    steps = [
        ("Question", "Tomorrow demand", "source"),
        ("Understand", "Natural language", "ai"),
        ("Intent", "Forecast", "ai"),
        ("Parameter", "Horizon = 24h", "ai"),
        ("API", "POST /api/ask", "api"),
        ("Compute", "Forecast module", "analysis"),
        ("Check", "History continuity", "guard"),
        ("Choose model", "168h weekly; else 24h / median", "analysis"),
        ("Predict", "Generate 24 hourly values", "analysis"),
        ("Guard", "Freshness + caveat", "guard"),
        ("Return", "Structured JSON", "api"),
        ("Explain", "Grounded answer", "ai"),
        ("Display", "Chart + explanation", "ui"),
    ]
    x, y, w, h, gap = 65, 890, 185, 210, 14
    for index, (title, line, kind) in enumerate(steps):
        d.card(x, y, w, h, title, [line], kind, center=True, title_size=20, line_size=19)
        if index < len(steps) - 1:
            d.arrow(x + w + 1, y + h / 2, x + w + gap - 3, y + h / 2)
        x += w + gap

    d.panel(38, 1220, 2624, 275, "GUARDRAILS AND RELIABILITY", "guard")
    guardrails = [
        "Schema / missing values", "Invalid timestamps / duplicates", "Date coverage + timezone",
        "Min 3 forecast points", "168h / 24h continuity", "Horizon <=168 hours",
        "Stale data >7 days", "Anomaly limit <=200", "Chronological holdout",
        "MAPE floor 0.1 kW", "Grounded numeric response", "HTTP error handling",
    ]
    gx, gy, chip_w, chip_gap = 70, 1295, 400, 22
    for index, label in enumerate(guardrails):
        row, col = divmod(index, 6)
        d.chip(gx + col * (chip_w + chip_gap), gy + row * 65, chip_w, label, "guard")
    d.text(70, 1465, "The source is one household of historical data. No live grid, weather, occupancy, appliance events or verified fault labels are present.", "small muted")
    d.save("assistant-workflow.svg")


if __name__ == "__main__":
    overview()
    analytics_detail()
    application_flow()
    print("Created three architecture SVG sheets.")
