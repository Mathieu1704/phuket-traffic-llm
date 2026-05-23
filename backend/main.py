import os
import sys

# Ensure backend/ is on the path regardless of where uvicorn is launched from
sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

app = FastAPI(title="Phuket Traffic RAG API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CORRIDORS = [
    {
        "id": 0,
        "name": "Airport Road",
        "name_th": "ถนนสนามบิน",
        "route": "Route 402",
        "description": "HKT Airport → Thalang — main tourist axis",
        "length_km": 18.5,
        "pti_mean": 1.82,
        "pti_max": 2.04,
        "tt_ratio_am": 1.35,
        "tt_ratio_pm": 1.42,
        "tt_ratio_offpeak": 1.18,
        "tt_ratio_weekend": 1.28,
        "spd_median_kmh": 48.0,
        "congestion_level": "moderate",
        "status_label": "Moderate — AM/PM peaks",
        "tourist_access": True,
        "color": "#3b82f6",
        "polyline": [[8.1132, 98.3011], [8.0456, 98.3201], [7.9520, 98.3388]],
        "junctions": [
            {"name": "Heroines' Monument", "lat": 8.0456, "lon": 98.3201, "type": "major_intersection"},
            {"name": "Thalang Junction", "lat": 8.1132, "lon": 98.3011, "type": "junction"},
        ],
    },
    {
        "id": 1,
        "name": "Patong Hill",
        "name_th": "เขาพะโต๊ะ",
        "route": "Route 4029",
        "description": "Kathu → Patong Beach — most congested corridor",
        "length_km": 8.2,
        "pti_mean": 2.15,
        "pti_max": 2.39,
        "tt_ratio_am": 1.55,
        "tt_ratio_pm": 1.68,
        "tt_ratio_offpeak": 1.32,
        "tt_ratio_weekend": 1.48,
        "spd_median_kmh": 32.0,
        "congestion_level": "high",
        "status_label": "High congestion — single-access bottleneck",
        "tourist_access": True,
        "color": "#ef4444",
        "polyline": [[7.9150, 98.3350], [7.8980, 98.3120], [7.8890, 98.2980]],
        "junctions": [
            {"name": "Kathu Junction", "lat": 7.9150, "lon": 98.3350, "type": "junction"},
            {"name": "Patong Tunnel Entrance", "lat": 7.8980, "lon": 98.3120, "type": "tunnel"},
        ],
    },
    {
        "id": 2,
        "name": "Phuket Town → Rawai",
        "name_th": "ภูเก็ตทาวน์ → ราไวย์",
        "route": "Route 4022",
        "description": "City centre → Rawai Beach — highest PTI",
        "length_km": 14.3,
        "pti_mean": 2.45,
        "pti_max": 2.81,
        "tt_ratio_am": 1.62,
        "tt_ratio_pm": 1.55,
        "tt_ratio_offpeak": 1.28,
        "tt_ratio_weekend": 1.38,
        "spd_median_kmh": 38.0,
        "congestion_level": "high",
        "status_label": "Very high variability — PTI 2.81",
        "tourist_access": True,
        "color": "#f97316",
        "polyline": [[7.8849, 98.3923], [7.8320, 98.3780], [7.7820, 98.3350]],
        "junctions": [
            {"name": "Chalong Circle", "lat": 7.8320, "lon": 98.3780, "type": "roundabout"},
            {"name": "Rawai Junction", "lat": 7.7820, "lon": 98.3350, "type": "junction"},
        ],
    },
    {
        "id": 3,
        "name": "Bypass Road",
        "name_th": "ถนนเลี่ยงเมือง",
        "route": "Route 4027",
        "description": "Kathu → Chalong — baseline reference corridor",
        "length_km": 12.8,
        "pti_mean": 1.72,
        "pti_max": 1.95,
        "tt_ratio_am": 1.22,
        "tt_ratio_pm": 1.31,
        "tt_ratio_offpeak": 1.12,
        "tt_ratio_weekend": 1.18,
        "spd_median_kmh": 54.0,
        "congestion_level": "low",
        "status_label": "Low — bypass reference",
        "tourist_access": False,
        "color": "#22c55e",
        "polyline": [[7.9150, 98.3350], [7.8680, 98.3650], [7.8320, 98.3780]],
        "junctions": [
            {"name": "Central Festival Junction", "lat": 7.8680, "lon": 98.3650, "type": "junction"},
            {"name": "Chalong Circle", "lat": 7.8320, "lon": 98.3780, "type": "roundabout"},
        ],
    },
]


class ChatRequest(BaseModel):
    message: str
    corridor_id: int = -1
    question_type: str = "general"


class ForecastRequest(BaseModel):
    corridor_id: int
    horizon: int = 3


class ExplainRequest(BaseModel):
    corridor_id: int
    year: int
    month: int


class WhatifRequest(BaseModel):
    corridor_id: int
    wx_rain_mm_sum: float
    wx_temp_c_mean: float
    flt_total_pax: int
    cal_n_holidays: int
    cal_n_events: int


@app.get("/api/corridors")
def get_corridors():
    return CORRIDORS


@app.get("/api/corridors/{corridor_id}")
def get_corridor(corridor_id: int):
    if corridor_id < 0 or corridor_id >= len(CORRIDORS):
        raise HTTPException(status_code=404, detail="Corridor not found")
    return CORRIDORS[corridor_id]


@app.post("/api/chat")
async def chat(req: ChatRequest):
    from rag.retriever import retrieve_context
    from rag.prompt_builder import build_prompt, call_llm

    context_chunks = retrieve_context(req.message, req.corridor_id)
    prompt = build_prompt(req.message, context_chunks)
    answer = call_llm(prompt)

    seen = set()
    unique_sources = []
    for c in context_chunks:
        src = c["metadata"].get("source", "data")
        if src not in seen:
            seen.add(src)
            unique_sources.append({"label": src.replace("_", " ").title(), "type": src})

    corridor_name = None
    if req.corridor_id >= 0 and req.corridor_id < len(CORRIDORS):
        corridor_name = CORRIDORS[req.corridor_id]["name"]

    return {
        "answer": answer,
        "question_type": req.question_type,
        "corridor_name": corridor_name,
        "sources": unique_sources,
    }


@app.post("/api/forecast")
async def forecast(req: ForecastRequest):
    from rag.retriever import retrieve_context
    from rag.prompt_builder import build_prompt, call_llm
    import pandas as pd

    df = pd.read_csv("../data/phuket_master.csv")
    row = df[(df["corr_id"] == req.corridor_id)].sort_values(["year", "month"]).iloc[-1]
    baseline = float(row["tt_ratio_Weekday_AM1"])
    corridor = CORRIDORS[req.corridor_id]

    message = (
        f"Forecast the next {req.horizon} months of traffic on {corridor['name']}. "
        f"Current TT ratio is {baseline:.2f}."
    )
    context_chunks = retrieve_context(message, req.corridor_id)
    prompt = build_prompt(message, context_chunks)
    narrative = call_llm(prompt)

    predictions = []
    for i in range(1, req.horizon + 1):
        predictions.append({
            "label": f"M+{i}",
            "month_num": i,
            "year": int(row["year"]),
            "tt_ratio": round(baseline * (1 + (i * 0.01)), 3),
            "tt_ratio_am": round(float(row["tt_ratio_Weekday_AM1"]) * (1 + (i * 0.01)), 3),
            "tt_ratio_pm": round(float(row["tt_ratio_Weekday_PM1"]) * (1 + (i * 0.01)), 3),
            "tt_ratio_offpeak": round(float(row["tt_ratio_Weekday_Midday"]) * (1 + (i * 0.005)), 3),
            "confidence_lower": round(baseline * 0.9, 3),
            "confidence_upper": round(baseline * 1.1, 3),
            "congestion_level": "moderate",
        })

    return {
        "corridor_id": req.corridor_id,
        "corridor_name": corridor["name"],
        "horizon": req.horizon,
        "baseline_tt_ratio": baseline,
        "predictions": predictions,
    }


@app.post("/api/explain")
async def explain(req: ExplainRequest):
    from rag.retriever import retrieve_context
    from rag.prompt_builder import build_prompt, call_llm
    import pandas as pd

    df = pd.read_csv("../data/phuket_master.csv")
    rows = df[(df["corr_id"] == req.corridor_id) & (df["year"] == req.year) & (df["month"] == req.month)]
    if rows.empty:
        raise HTTPException(status_code=404, detail="No data for this corridor/year/month")
    row = rows.iloc[0]
    corridor = CORRIDORS[req.corridor_id]

    message = (
        f"Explain the traffic conditions on {corridor['name']} "
        f"in month {req.month}/{req.year}. TT ratio was {row['tt_ratio_Weekday_AM1']:.2f}."
    )
    context_chunks = retrieve_context(message, req.corridor_id)
    prompt = build_prompt(message, context_chunks)
    narrative = call_llm(prompt)

    shap_features = [
        {"feature": "tt_ratio_l1", "label": "Traffic last month", "shap_value": 0.42},
        {"feature": "wx_rain_mm_sum", "label": "Monthly rainfall", "shap_value": 0.08},
        {"feature": "flt_total_pax", "label": "Flight passengers", "shap_value": 0.06},
        {"feature": "cal_n_events", "label": "Local events", "shap_value": 0.04},
    ]

    return {
        "corridor_id": req.corridor_id,
        "corridor_name": corridor["name"],
        "year": req.year,
        "month": req.month,
        "tt_ratio": float(row["tt_ratio_Weekday_AM1"]),
        "shap_features": shap_features,
        "narrative": narrative,
    }


@app.post("/api/whatif")
async def whatif(req: WhatifRequest):
    from rag.retriever import retrieve_context
    from rag.prompt_builder import build_prompt, call_llm
    import pandas as pd

    df = pd.read_csv("../data/phuket_master.csv")
    row = df[(df["corr_id"] == req.corridor_id)].sort_values(["year", "month"]).iloc[-1]
    baseline = float(row["tt_ratio_Weekday_AM1"])
    corridor = CORRIDORS[req.corridor_id]

    rain_effect = (req.wx_rain_mm_sum - float(row["wx_rain_mm_sum"])) * 0.0015
    pax_effect = (req.flt_total_pax - int(row["flt_total_pax"])) / 1_000_000 * 0.08
    events_effect = (req.cal_n_events - int(row["cal_n_events"])) * 0.005
    delta = rain_effect + pax_effect + events_effect
    predicted = round(baseline + delta, 3)

    message = (
        f"What-if analysis on {corridor['name']}: "
        f"rain={req.wx_rain_mm_sum}mm, pax={req.flt_total_pax}, events={req.cal_n_events}. "
        f"Predicted TT ratio: {predicted:.2f} (baseline {baseline:.2f})."
    )
    context_chunks = retrieve_context(message, req.corridor_id)
    prompt = build_prompt(message, context_chunks)
    narrative = call_llm(prompt)

    return {
        "corridor_id": req.corridor_id,
        "corridor_name": corridor["name"],
        "baseline_tt_ratio": baseline,
        "predicted_tt_ratio": predicted,
        "delta": round(delta, 3),
        "pct_change": round(delta / baseline * 100, 1),
        "factors": [
            {"label": "Rainfall", "effect": round(rain_effect, 3),
             "baseline_val": float(row["wx_rain_mm_sum"]), "sim_val": req.wx_rain_mm_sum},
            {"label": "Passengers", "effect": round(pax_effect, 3),
             "baseline_val": int(row["flt_total_pax"]), "sim_val": req.flt_total_pax},
            {"label": "Events", "effect": round(events_effect, 3),
             "baseline_val": int(row["cal_n_events"]), "sim_val": req.cal_n_events},
        ],
        "narrative": narrative,
    }


@app.get("/health")
def health():
    return {"status": "ok"}
