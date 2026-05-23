"""TomTom Traffic Flow API — real-time speed on the 4 Phuket corridors."""
import os
import requests

API_KEY = os.getenv("TOMTOM_API_KEY", "")
URL = "https://api.tomtom.com/traffic/services/4/flowSegmentData/relative0/10/json"

# Representative midpoint coordinates per corridor
CORRIDOR_POINTS = {
    0: {"name": "Airport Road (Route 402)",       "lat": 8.06874, "lon": 98.34287},
    1: {"name": "Patong Hill (Route 4029)",        "lat": 7.90253, "lon": 98.30995},
    2: {"name": "Phuket Town → Rawai (Route 4022)","lat": 7.84358, "lon": 98.34948},
    3: {"name": "Bypass Road (Route 4027)",        "lat": 7.91697, "lon": 98.34194},
}


def _congestion_label(ttr: float) -> str:
    if ttr < 1.15: return "smooth"
    if ttr < 1.35: return "moderate"
    if ttr < 1.55: return "congested"
    return "very congested"


def get_flow(corridor_id: int) -> dict:
    if not API_KEY:
        return {"error": "TOMTOM_API_KEY not set"}
    pt = CORRIDOR_POINTS.get(corridor_id)
    if not pt:
        return {"error": f"Unknown corridor_id {corridor_id}"}
    try:
        res = requests.get(URL, params={
            "point": f"{pt['lat']},{pt['lon']}",
            "unit": "KMPH",
            "key": API_KEY,
        }, timeout=6)
        res.raise_for_status()
        d = res.json().get("flowSegmentData", {})

        current_speed = float(d.get("currentSpeed", 0))
        free_flow = float(d.get("freeFlowSpeed", 1))
        ttr = round(free_flow / current_speed, 2) if current_speed > 0 else None
        confidence = float(d.get("confidence", 0))

        return {
            "corridor_id": corridor_id,
            "corridor_name": pt["name"],
            "current_speed_kmh": current_speed,
            "free_flow_speed_kmh": free_flow,
            "tt_ratio": ttr,
            "congestion_level": _congestion_label(ttr) if ttr else "unknown",
            "confidence": confidence,
            "source": "TomTom Traffic Flow API",
        }
    except Exception as e:
        return {"error": str(e), "corridor_id": corridor_id, "source": "TomTom Flow"}


def get_all_corridors() -> list[dict]:
    return [get_flow(cid) for cid in CORRIDOR_POINTS]


def format_for_prompt(flows: list[dict]) -> str:
    lines = ["LIVE TRAFFIC (TomTom real-time):"]
    for f in flows:
        if "error" in f:
            lines.append(f"  {f.get('corridor_name', f.get('corridor_id', '?'))}: unavailable")
        else:
            lines.append(
                f"  {f['corridor_name']}: {f['current_speed_kmh']:.0f} km/h "
                f"(TT ratio {f['tt_ratio']} — {f['congestion_level']})"
            )
    return "\n".join(lines)
