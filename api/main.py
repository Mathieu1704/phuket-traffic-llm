"""
Phuket Traffic LLM — API with RAG backend
/api/chat uses ChromaDB + Ollama (llama3.1) for grounded answers.
All other endpoints (forecast, explain, whatif) keep their original logic.
"""

import asyncio
import datetime
import os
import random
import sys

# Suppress HuggingFace unauthenticated warning — must be set before any HF import
os.environ["HUGGINGFACE_HUB_VERBOSITY"] = "error"
os.environ["HF_HUB_DISABLE_IMPLICIT_TOKEN"] = "1"

# Add backend/ to path so rag.* and live.* modules are importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

# Load TomTom key for live data modules
os.environ.setdefault("TOMTOM_API_KEY",
    open(os.path.join(os.path.dirname(__file__), "..", "tomtom_phuket", ".env"))
    .read().split("TOMTOM_API_KEY=")[1].split("\n")[0].strip()
    if os.path.exists(os.path.join(os.path.dirname(__file__), "..", "tomtom_phuket", ".env"))
    else ""
)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "backend", ".env"))

app = FastAPI(title="Phuket Traffic LLM API — Mock", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Static data — corridors (from TomTom processed + sensors/phuket_corridors_intersections.json)
# ---------------------------------------------------------------------------

CORRIDORS = [
    {
        "id": 0,
        "name": "Airport Road",
        "name_th": "ถนนสนามบิน",
        "route": "402",
        "description": "HKT Airport → Thalang",
        "length_km": 12.4,
        "pti_mean": 2.04,
        "pti_max": 2.31,
        "tt_ratio_am": 1.18,
        "tt_ratio_pm": 1.24,
        "tt_ratio_offpeak": 1.08,
        "tt_ratio_weekend": 1.15,
        "spd_median_kmh": 58.2,
        "congestion_level": "low",
        "status_label": "Smooth",
        "tourist_access": True,
        "color": "#22c55e",
        "polyline": [
            # Extracted from TomTom segment shapes — RDP simplified (ε=0.0003°)
            [8.1144, 98.30253], [8.11491, 98.30572], [8.1161, 98.30617],
            [8.11611, 98.30852], [8.12166, 98.30841], [8.12243, 98.31064],
            [8.12399, 98.3115],  [8.12438, 98.31232], [8.1247, 98.31622],
            [8.12435, 98.32102], [8.1233, 98.32314],  [8.1224, 98.32378],
            [8.1212, 98.32713],  [8.12119, 98.32962], [8.11994, 98.33604],
            [8.12302, 98.33618], [8.12565, 98.33693], [8.10281, 98.33466],
            [8.0946, 98.33797],  [8.08637, 98.34228], [8.07658, 98.34409],
            [8.06874, 98.34287], [8.0455, 98.33614],  [8.0361, 98.33387],
            [8.02786, 98.33323], [8.02415, 98.33405], [8.01594, 98.33842],
            [8.01034, 98.34057], [8.00712, 98.34254], [8.00521, 98.34048],
            [7.9969, 98.33637],  [7.99591, 98.33373], [7.99715, 98.33262],
            [7.99695, 98.33237],
        ],
        "junctions": [
            {"name": "Airport Junction",  "lat": 8.1144,  "lon": 98.30253, "type": "T-junction"},
            {"name": "Baan Don Junction", "lat": 8.06874, "lon": 98.34287, "type": "at-grade"},
            {"name": "Heroines Monument", "lat": 8.00521, "lon": 98.34048, "type": "roundabout"},
            {"name": "Tha Rua Junction",  "lat": 7.99695, "lon": 98.33237, "type": "complex"},
        ],
    },
    {
        "id": 1,
        "name": "Patong Hill",
        "name_th": "เขาพะโต๊ะ",
        "route": "4029",
        "description": "Kathu → Patong Beach",
        "length_km": 7.8,
        "pti_mean": 2.39,
        "pti_max": 2.81,
        "tt_ratio_am": 1.45,
        "tt_ratio_pm": 1.62,
        "tt_ratio_offpeak": 1.21,
        "tt_ratio_weekend": 1.58,
        "spd_median_kmh": 32.4,
        "congestion_level": "high",
        "status_label": "Congested",
        "tourist_access": True,
        "color": "#ef4444",
        "polyline": [
            # Extracted from TomTom segment shapes — RDP simplified (ε=0.0003°)
            [7.91998, 98.31721], [7.91982, 98.31797], [7.91883, 98.31863],
            [7.91891, 98.31921], [7.91992, 98.32],    [7.92175, 98.32026],
            [7.92418, 98.32679], [7.92407, 98.32883], [7.9209, 98.33097],
            [7.91899, 98.33166], [7.91811, 98.33119], [7.91618, 98.33156],
            [7.9107, 98.33381],  [7.9047, 98.32577],  [7.90442, 98.32425],
            [7.90599, 98.32419], [7.90535, 98.323],   [7.9037, 98.32252],
            [7.90272, 98.32136], [7.90322, 98.3189],  [7.90284, 98.31755],
            [7.9038, 98.31301],  [7.90342, 98.31195], [7.90387, 98.31148],
            [7.90253, 98.30995], [7.90147, 98.31044], [7.90148, 98.30769],
            [7.89969, 98.3071],  [7.89964, 98.3059],  [7.89685, 98.30135],
            [7.8972, 98.29966],  [7.89263, 98.2982],  [7.89281, 98.29747],
            [7.89392, 98.29808],
        ],
        "junctions": [
            {"name": "Kathu Junction",    "lat": 7.91998, "lon": 98.31721, "type": "signalised"},
            {"name": "Sam Kong Jct",      "lat": 7.9107,  "lon": 98.33381, "type": "signalised"},
            {"name": "Patong Hill Summit","lat": 7.90253, "lon": 98.30995, "type": "bottleneck"},
            {"name": "Patong Beachfront", "lat": 7.89392, "lon": 98.29808, "type": "T-junction"},
        ],
    },
    {
        "id": 2,
        "name": "Phuket Town → Rawai",
        "name_th": "ภูเก็ตทาวน์ → ราไวย์",
        "route": "4022",
        "description": "Centre-ville → Rawai Beach",
        "length_km": 15.2,
        "pti_mean": 2.81,
        "pti_max": 3.12,
        "tt_ratio_am": 1.68,
        "tt_ratio_pm": 1.52,
        "tt_ratio_offpeak": 1.31,
        "tt_ratio_weekend": 1.44,
        "spd_median_kmh": 28.7,
        "congestion_level": "very_high",
        "status_label": "Very congested",
        "tourist_access": True,
        "color": "#f97316",
        "polyline": [
            # Extracted from TomTom segment shapes — RDP simplified (ε=0.0003°)
            [7.88532, 98.39278], [7.88454, 98.39244], [7.88466, 98.39078],
            [7.88296, 98.39077], [7.88318, 98.38744], [7.88201, 98.38713],
            [7.87958, 98.38461], [7.87936, 98.38134], [7.87507, 98.37884],
            [7.87229, 98.37787], [7.87106, 98.37556], [7.86872, 98.37413],
            [7.86737, 98.37386], [7.86623, 98.37191], [7.86258, 98.36995],
            [7.85829, 98.36468], [7.8565, 98.35891],  [7.85447, 98.35655],
            [7.84867, 98.35164], [7.84358, 98.34948], [7.83466, 98.34806],
            [7.83201, 98.34564], [7.82953, 98.34414], [7.82507, 98.34287],
            [7.82225, 98.3409],  [7.79812, 98.33471], [7.79402, 98.33141],
            [7.79166, 98.3306],  [7.7822, 98.32931],  [7.78135, 98.33296],
            [7.78151, 98.33581], [7.78123, 98.33618], [7.78097, 98.33585],
        ],
        "junctions": [
            {"name": "Phuket Town Centre",   "lat": 7.88532, "lon": 98.39278, "type": "roundabout"},
            {"name": "Chalong Circle",       "lat": 7.84358, "lon": 98.34948, "type": "5-arm roundabout"},
            {"name": "Wat Chalong Junction", "lat": 7.83466, "lon": 98.34806, "type": "signalised"},
            {"name": "Big Buddha Junction",  "lat": 7.82225, "lon": 98.3409,  "type": "T-junction"},
            {"name": "Rawai Market",         "lat": 7.78097, "lon": 98.33585, "type": "T-junction"},
        ],
    },
    {
        "id": 3,
        "name": "Bypass Road",
        "name_th": "ถนนบายพาส",
        "route": "4027",
        "description": "Kathu → Chalong",
        "length_km": 18.6,
        "pti_mean": 1.95,
        "pti_max": 2.08,
        "tt_ratio_am": 1.11,
        "tt_ratio_pm": 1.18,
        "tt_ratio_offpeak": 1.03,
        "tt_ratio_weekend": 1.09,
        "spd_median_kmh": 68.5,
        "congestion_level": "low",
        "status_label": "Smooth",
        "tourist_access": False,
        "color": "#3b82f6",
        "polyline": [
            # Extracted from TomTom segment shapes — RDP simplified (ε=0.0003°)
            [7.94265, 98.34582], [7.94, 98.34848],    [7.93884, 98.34807],
            [7.93794, 98.34831], [7.93772, 98.35015], [7.93634, 98.34873],
            [7.93633, 98.34682], [7.9342, 98.34402],  [7.93527, 98.34096],
            [7.93369, 98.33961], [7.93486, 98.33775], [7.93753, 98.33703],
            [7.93734, 98.33507], [7.93659, 98.33435], [7.93401, 98.33306],
            [7.93194, 98.33358], [7.9307, 98.33327],  [7.93047, 98.33418],
            [7.92928, 98.33514], [7.92529, 98.33344], [7.92386, 98.33328],
            [7.92211, 98.33413], [7.92196, 98.335],   [7.92144, 98.33517],
            [7.92178, 98.33682], [7.9214, 98.33856],  [7.91697, 98.34194],
            [7.91741, 98.34469], [7.91606, 98.34553], [7.91632, 98.3462],
            [7.91587, 98.34695], [7.91272, 98.34673], [7.90864, 98.34811],
            [7.90792, 98.35063], [7.90821, 98.3533],  [7.90611, 98.35695],
            [7.90482, 98.36353], [7.90678, 98.37181], [7.90708, 98.37718],
            [7.90676, 98.37793], [7.90401, 98.37763], [7.90269, 98.37798],
            [7.90172, 98.38058], [7.89967, 98.38269], [7.89383, 98.38577],
            [7.89427, 98.38952], [7.89059, 98.39011], [7.89107, 98.39185],
            [7.89025, 98.39561], [7.89056, 98.39845],
        ],
        "junctions": [
            {"name": "Bypass North",         "lat": 7.94265, "lon": 98.34582, "type": "signalised"},
            {"name": "Koh Kaew Junction",    "lat": 7.93527, "lon": 98.34096, "type": "signalised"},
            {"name": "Central Festival Jct", "lat": 7.91697, "lon": 98.34194, "type": "signalised"},
            {"name": "Chalong Circle",       "lat": 7.89056, "lon": 98.39845, "type": "5-arm roundabout"},
        ],
    },
]

# ---------------------------------------------------------------------------
# SHAP feature importance per corridor (from notebooks/05_baselines.ipynb)
# ---------------------------------------------------------------------------

SHAP_FEATURES: dict[int, list[dict]] = {
    0: [
        {"feature": "flt_total_pax", "label": "Flight passengers", "shap_value": 0.312},
        {"feature": "is_high_season", "label": "High season", "shap_value": 0.241},
        {"feature": "soc_phuket_flight", "label": "Google Trends — flights", "shap_value": 0.189},
        {"feature": "month_cos", "label": "Monthly cyclicity (cos)", "shap_value": 0.143},
        {"feature": "cal_n_holidays", "label": "Public holidays", "shap_value": 0.112},
        {"feature": "wx_rain_mm_sum", "label": "Rainfall (mm)", "shap_value": -0.089},
        {"feature": "wx_wind_kmh", "label": "Wind speed", "shap_value": -0.054},
        {"feature": "flt_domestic", "label": "Domestic flights", "shap_value": 0.048},
        {"feature": "cal_n_events", "label": "Local events", "shap_value": 0.037},
        {"feature": "soc_phuket_hotel", "label": "Google Trends — hotels", "shap_value": 0.029},
    ],
    1: [
        {"feature": "is_high_season", "label": "High season", "shap_value": 0.421},
        {"feature": "flt_total_pax", "label": "Flight passengers", "shap_value": 0.298},
        {"feature": "cal_high_impact", "label": "High-impact events", "shap_value": 0.187},
        {"feature": "wx_rain_mm_sum", "label": "Rainfall (mm)", "shap_value": -0.152},
        {"feature": "soc_phuket_beach", "label": "Google Trends — beach", "shap_value": 0.134},
        {"feature": "month_sin", "label": "Monthly cyclicity (sin)", "shap_value": 0.098},
        {"feature": "wx_temp_c_mean", "label": "Average temperature", "shap_value": 0.076},
        {"feature": "cal_n_events", "label": "Local events", "shap_value": 0.065},
        {"feature": "flt_domestic", "label": "Domestic flights", "shap_value": 0.043},
        {"feature": "wx_wind_kmh", "label": "Wind speed", "shap_value": -0.031},
    ],
    2: [
        {"feature": "wx_rain_mm_sum", "label": "Rainfall (mm)", "shap_value": -0.387},
        {"feature": "is_high_season", "label": "High season", "shap_value": 0.354},
        {"feature": "flt_total_pax", "label": "Flight passengers", "shap_value": 0.276},
        {"feature": "cal_n_holidays", "label": "Public holidays", "shap_value": 0.198},
        {"feature": "soc_phuket_vacation", "label": "Google Trends — vacation", "shap_value": 0.167},
        {"feature": "cal_high_impact", "label": "High-impact events", "shap_value": 0.143},
        {"feature": "wx_temp_c_mean", "label": "Average temperature", "shap_value": 0.089},
        {"feature": "month_cos", "label": "Monthly cyclicity (cos)", "shap_value": 0.071},
        {"feature": "flt_domestic", "label": "Domestic flights", "shap_value": 0.058},
        {"feature": "soc_phuket_hotel", "label": "Google Trends — hotels", "shap_value": 0.041},
    ],
    3: [
        {"feature": "flt_total_pax", "label": "Flight passengers", "shap_value": 0.189},
        {"feature": "cal_n_holidays", "label": "Public holidays", "shap_value": 0.156},
        {"feature": "is_high_season", "label": "High season", "shap_value": 0.134},
        {"feature": "wx_rain_mm_sum", "label": "Rainfall (mm)", "shap_value": -0.098},
        {"feature": "soc_phuket", "label": "Google Trends — Phuket", "shap_value": 0.087},
        {"feature": "month_sin", "label": "Monthly cyclicity (sin)", "shap_value": 0.065},
        {"feature": "cal_n_events", "label": "Local events", "shap_value": 0.054},
        {"feature": "wx_temp_c_mean", "label": "Average temperature", "shap_value": 0.043},
        {"feature": "wx_wind_kmh", "label": "Wind speed", "shap_value": -0.032},
        {"feature": "flt_domestic", "label": "Domestic flights", "shap_value": 0.028},
    ],
}

# Seasonal tt_ratio multipliers (index 0 = Jan)
SEASONAL = [1.25, 1.22, 1.18, 1.05, 0.95, 0.88, 0.90, 0.92, 0.98, 1.10, 1.15, 1.28]
MONTHS_FR = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
MONTHS_FR_LONG = ["","January","February","March","April","May","June",
                  "July","August","September","October","November","December"]


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    message: str
    corridor_id: int = 0
    question_type: str = "nowcast"  # nowcast | forecast | explain | whatif | decision
    model: str = "ollama"           # ollama | gpt-4o-mini | claude-haiku
    refine: bool = True             # run refine agent on the raw answer
    charts: bool = True             # ask LLM to generate a chart JSON if applicable


class ForecastRequest(BaseModel):
    corridor_id: int = 0
    horizon: int = 3  # months ahead (1-12)


class ExplainRequest(BaseModel):
    corridor_id: int = 0
    year: int = 2024
    month: int = 1


class WhatifRequest(BaseModel):
    corridor_id: int = 0
    wx_rain_mm_sum: float = 150.0
    wx_temp_c_mean: float = 29.0
    flt_total_pax: float = 120000.0
    cal_n_holidays: int = 2
    cal_n_events: int = 5


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _congestion_label(ttr: float) -> str:
    if ttr < 1.15:
        return "low"
    if ttr < 1.35:
        return "moderate"
    if ttr < 1.55:
        return "high"
    return "very high"


def _mock_chat_answer(req: ChatRequest, corridor: dict) -> str:
    """
    *** REPLACE THIS FUNCTION with your fine-tuned LLM inference ***
    signature: (prompt: str) -> str
    """
    ttr = corridor["tt_ratio_am"]
    level = _congestion_label(ttr)
    f = SHAP_FEATURES[req.corridor_id]

    if req.question_type == "nowcast":
        return (
            f"On corridor **{corridor['name']}** ({corridor['description']}), "
            f"the current travel time ratio (TTR) is **{ttr}** during the AM peak. "
            f"Congestion is **{level}** — median speed at {corridor['spd_median_kmh']} km/h. "
            f"The average PTI of {corridor['pti_mean']} indicates that the trip can take up to "
            f"{int(corridor['pti_mean'] * 100 - 100)}% longer than free-flow time.\n\n"
            f"**Dominant factors this month:** {f[0]['label']} (+{f[0]['shap_value']:.2f}), "
            f"{f[1]['label']} (+{f[1]['shap_value']:.2f})."
        )

    if req.question_type == "forecast":
        future_ttr = round(ttr * SEASONAL[(datetime.datetime.now().month + 1) % 12], 2)
        return (
            f"**Forecast M+1 to M+3 — {corridor['name']}**\n\n"
            f"The model anticipates a TTR of **{future_ttr}** next month "
            f"({'increase' if future_ttr > ttr else 'decrease'} vs current {ttr}). "
            f"The {'high' if future_ttr > 1.3 else 'low'} tourist season "
            f"is the main driver of this trend, amplified by international HKT flights "
            f"({random.randint(120, 180)}k passengers expected).\n\n"
            f"**Recommendation:** travel before 08:00 or after 20:00 to avoid peak hours."
        )

    if req.question_type == "explain":
        return (
            f"**Causal analysis — {corridor['name']}**\n\n"
            f"SHAP analysis identifies **{f[0]['label']}** as the dominant feature "
            f"(impact = +{f[0]['shap_value']:.3f} on TTR). "
            f"**{f[1]['label']}** reinforces congestion (+{f[1]['shap_value']:.3f}), "
            f"while **{f[5]['label']}** has a moderating effect "
            f"({f[5]['shap_value']:.3f} — rain discourages non-essential tourist travel).\n\n"
            f"The predicted TTR is **{ttr}** — level: **{level}**."
        )

    if req.question_type == "whatif":
        return (
            f"**Alternative scenario — {corridor['name']}**\n\n"
            f"If rainfall increases by +50 mm and flights decrease by 10%, "
            f"the model predicts a TTR of **{round(ttr * 0.94, 2)}** "
            f"(vs {ttr} baseline, i.e. -6%). "
            f"The dominant effect is the reduction of tourist inflows due to weather."
        )

    # decision (default)
    return (
        f"**Best time slot on {corridor['name']}:**\n\n"
        f"- Optimal: **06:00–08:00** (TTR ≈ {round(corridor['tt_ratio_offpeak'] * 0.95, 2)})\n"
        f"- Acceptable: **20:00–22:00** (TTR ≈ {round(corridor['tt_ratio_offpeak'], 2)})\n"
        f"- Avoid: **07:30–09:00** and **16:30–18:30** (peak TTR ≈ {corridor['tt_ratio_pm']})\n\n"
        f"Note: during high season (Nov–Mar), the AM peak is consistently 15–20% longer."
    )


NOWCAST_KEYWORDS = {
    "now", "current", "currently", "today", "right now", "live",
    "at the moment", "this morning", "tonight", "conditions",
}


def _is_nowcast(message: str) -> bool:
    msg = message.lower()
    return any(kw in msg for kw in NOWCAST_KEYWORDS)


def _get_live_context() -> tuple[str, list[dict]]:
    """Fetch live weather + flights and return (context_text, sources)."""
    lines = []
    sources = []
    try:
        from live.weather import get_current_weather, format_for_prompt as fmt_wx
        w = get_current_weather()
        if "error" not in w:
            lines.append(fmt_wx(w))
            sources.append({"label": "Live Weather (Open-Meteo)", "type": "weather_live"})
    except Exception:
        pass
    try:
        from live.flights import get_live_flights, format_for_prompt as fmt_fl
        f = get_live_flights()
        if "error" not in f:
            lines.append(fmt_fl(f))
            sources.append({"label": "Live Flights (OpenSky)", "type": "flights_live"})
    except Exception:
        pass
    return "\n\n".join(lines), sources


def _rag_chat_answer(
    message: str, corridor_id: int,
    model: str = "ollama", refine: bool = True, charts: bool = True
) -> tuple[str, list[dict], dict | None]:
    """RAG answer via ChromaDB + LLM. Injects live data for nowcast questions."""
    try:
        from rag.retriever import retrieve_context
        from rag.prompt_builder import build_prompt, call_llm, refine_answer, parse_chart_from_response

        context_chunks = retrieve_context(message, corridor_id)
        live_text, live_sources = _get_live_context() if _is_nowcast(message) else ("", [])

        prompt = build_prompt(message, context_chunks, live_context=live_text, include_chart=charts)
        raw = call_llm(prompt, model=model)

        answer, chart_data = parse_chart_from_response(raw) if charts else (raw, None)

        if refine and not answer.startswith("[LLM unavailable") and not answer.startswith("["):
            answer = refine_answer(answer, model=model)

        seen = set()
        sources = []
        for c in context_chunks:
            src = c["metadata"].get("source", "data")
            if src not in seen:
                seen.add(src)
                sources.append({"label": src.replace("_", " ").title(), "type": src})
        sources.extend(live_sources)
        return answer, sources, chart_data
    except Exception:
        return None, [], None


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/api/health")
async def health():
    return {"status": "ok", "model": "mock-llm-v0.1", "version": "0.1.0"}


@app.get("/api/corridors")
async def get_corridors():
    return CORRIDORS


@app.get("/api/corridors/{corridor_id}")
async def get_corridor(corridor_id: int):
    corridor = next((c for c in CORRIDORS if c["id"] == corridor_id), None)
    if corridor is None:
        return {"error": "Corridor not found"}
    return corridor


@app.post("/api/chat")
async def chat(req: ChatRequest):
    corridor = CORRIDORS[req.corridor_id]

    # Try RAG + LLM first; fall back to mock if unavailable
    rag_answer, rag_sources, chart_data = _rag_chat_answer(
        req.message, req.corridor_id,
        model=req.model, refine=req.refine, charts=req.charts,
    )
    if rag_answer and not rag_answer.startswith("[LLM unavailable") and not rag_answer.startswith("[OpenAI") and not rag_answer.startswith("[Anthropic"):
        answer = rag_answer
        sources = rag_sources
        used_model = req.model
    else:
        await asyncio.sleep(0.8)
        answer = _mock_chat_answer(req, corridor)
        sources = [
            {"label": "TomTom MOVE — Août 2024", "type": "traffic"},
            {"label": "AOT Flights 2022–2024", "type": "flights"},
            {"label": "Open-Meteo Archive", "type": "weather"},
            {"label": "Google Trends (pytrends)", "type": "social"},
        ]
        used_model = "mock-llm-v0.1"
        chart_data = None

    return {
        "answer": answer,
        "question_type": req.question_type,
        "corridor_id": req.corridor_id,
        "corridor_name": corridor["name"],
        "model": used_model,
        "sources": sources,
        "chart_data": chart_data,
    }


@app.post("/api/forecast")
async def forecast(req: ForecastRequest):
    """
    *** PLUG-IN POINT: replace with ML model .predict(X_future) ***
    """
    await asyncio.sleep(0.5)
    corridor = CORRIDORS[req.corridor_id]
    base = corridor["tt_ratio_am"]
    current_month = datetime.datetime.now().month

    predictions = []
    for i in range(req.horizon):
        m_idx = (current_month + i) % 12
        factor = SEASONAL[m_idx] + random.uniform(-0.02, 0.02)
        ttr = round(base * factor, 3)
        predictions.append({
            "label": MONTHS_FR[m_idx],
            "month_num": m_idx + 1,
            "year": datetime.datetime.now().year + (current_month + i) // 12,
            "tt_ratio": ttr,
            "tt_ratio_am": round(ttr * 1.08, 3),
            "tt_ratio_pm": round(ttr * 1.12, 3),
            "tt_ratio_offpeak": round(ttr * 0.88, 3),
            "confidence_lower": round(ttr * 0.93, 3),
            "confidence_upper": round(ttr * 1.07, 3),
            "congestion_level": "high" if ttr > 1.5 else "moderate" if ttr > 1.2 else "low",
        })

    return {
        "corridor_id": req.corridor_id,
        "corridor_name": corridor["name"],
        "horizon": req.horizon,
        "baseline_tt_ratio": base,
        "predictions": predictions,
    }


@app.post("/api/explain")
async def explain(req: ExplainRequest):
    """
    *** PLUG-IN POINT: replace with SHAP explainer on real model output ***
    """
    await asyncio.sleep(0.6)
    corridor = CORRIDORS[req.corridor_id]
    features = SHAP_FEATURES[req.corridor_id]
    f = features

    narrative = (
        f"For **{corridor['name']}** in {MONTHS_FR_LONG[req.month]} {req.year}, "
        f"SHAP analysis identifies **{f[0]['label']}** as the dominant factor "
        f"(impact = {f[0]['shap_value']:+.3f} on TTR). "
        f"**{f[1]['label']}** reinforces congestion ({f[1]['shap_value']:+.3f}), "
        f"while **{f[5]['label']}** has a moderating effect "
        f"({f[5]['shap_value']:+.3f}). "
        f"Predicted TTR: **{corridor['tt_ratio_am']}** — {_congestion_label(corridor['tt_ratio_am'])}."
    )

    return {
        "corridor_id": req.corridor_id,
        "corridor_name": corridor["name"],
        "year": req.year,
        "month": req.month,
        "tt_ratio": corridor["tt_ratio_am"],
        "shap_features": features,
        "narrative": narrative,
    }


@app.post("/api/whatif")
async def whatif(req: WhatifRequest):
    """
    *** PLUG-IN POINT: replace with model.predict(modified_features) ***
    """
    await asyncio.sleep(0.7)
    corridor = CORRIDORS[req.corridor_id]
    baseline = corridor["tt_ratio_am"]

    rain_effect   = -0.0015 * (req.wx_rain_mm_sum - 150)
    flight_effect =  0.0002 * (req.flt_total_pax - 120_000) / 100
    holiday_effect = 0.035  * (req.cal_n_holidays - 2)
    event_effect  =  0.010  * (req.cal_n_events - 5)
    temp_effect   =  0.005  * (req.wx_temp_c_mean - 29)

    total_delta = rain_effect + flight_effect + holiday_effect + event_effect + temp_effect
    predicted   = round(max(1.0, baseline + total_delta), 3)
    pct_change  = round((predicted - baseline) / baseline * 100, 1)

    factors = [
        {"label": "Rainfall (mm)",        "effect": round(rain_effect, 4),    "baseline_val": 150,     "sim_val": req.wx_rain_mm_sum},
        {"label": "Flight passengers",    "effect": round(flight_effect, 4),  "baseline_val": 120000,  "sim_val": req.flt_total_pax},
        {"label": "Public holidays",      "effect": round(holiday_effect, 4), "baseline_val": 2,       "sim_val": req.cal_n_holidays},
        {"label": "Local events",         "effect": round(event_effect, 4),   "baseline_val": 5,       "sim_val": req.cal_n_events},
        {"label": "Temperature (°C)",     "effect": round(temp_effect, 4),    "baseline_val": 29,      "sim_val": req.wx_temp_c_mean},
    ]
    dominant = max(factors, key=lambda x: abs(x["effect"]))

    narrative = (
        f"In this scenario on **{corridor['name']}**, TTR would change from **{baseline}** to **{predicted}** "
        f"({'↑' if pct_change > 0 else '↓'} {abs(pct_change):.1f}%). "
        f"Dominant factor: **{dominant['label']}** (Δ = {dominant['effect']:+.4f}). "
        f"{'Increased tourist pressure worsens congestion on this corridor.' if predicted > baseline else 'The simulated conditions reduce pressure on this corridor.'}"
    )

    return {
        "corridor_id": req.corridor_id,
        "corridor_name": corridor["name"],
        "baseline_tt_ratio": baseline,
        "predicted_tt_ratio": predicted,
        "delta": round(total_delta, 4),
        "pct_change": pct_change,
        "factors": factors,
        "narrative": narrative,
    }
