"""phuket_public_transport.csv + phuket_ferry_schedule.csv → route summary chunks."""
import pandas as pd
from pathlib import Path

PT_PATH = Path(__file__).resolve().parents[3] / "data" / "phuket_public_transport.csv"
FERRY_PATH = Path(__file__).resolve().parents[3] / "data" / "phuket_ferry_schedule.csv"

CORR_ID_MAP = {
    "Airport Road": 0,
    "Route 402": 0,
    "Patong Hill": 1,
    "Route 4029": 1,
    "Phuket Town": 2,
    "Route 4022": 2,
    "Bypass Road": 3,
    "Route 4027": 3,
}


def _corr_id(corridor_str: str) -> int:
    if not isinstance(corridor_str, str):
        return -1
    for key, cid in CORR_ID_MAP.items():
        if key.lower() in corridor_str.lower():
            return cid
    return -1


def textualize() -> list[dict]:
    chunks = []

    # Public transport — aggregate by route × day_type
    pt = pd.read_csv(PT_PATH, parse_dates=["date"])
    pt["day_type"] = pt["is_weekend"].map({1: "Weekend", 0: "Weekday"})

    for (route_name, day_type), grp in pt.groupby(["route_name", "day_type"]):
        pax = grp["est_passengers"].mean()
        cars_avoided = grp["cars_avoided"].mean()
        freq = grp["frequency_min"].median()
        fare = grp["fare_thb"].median()
        corridor = grp["corridor"].iloc[0] if "corridor" in grp.columns else "unknown"
        cid = _corr_id(corridor)
        n_trips = len(grp)

        text = (
            f"[Smart Bus] {route_name} — {day_type}:\n"
            f"  Corridor served: {corridor}\n"
            f"  Frequency: every {freq:.0f} min | Fare: {fare:.0f} THB\n"
            f"  Est. passengers/day: {pax:.0f} | Cars avoided: {cars_avoided:.0f}\n"
            f"  Note: this route reduces private car demand on {corridor}"
        )
        chunks.append({
            "text": text,
            "metadata": {
                "source": "transport",
                "transport_type": "bus",
                "route_name": route_name,
                "day_type": day_type,
                "corridor_id": cid,
            },
        })

    # Ferry — aggregate by route × day_type
    ferry = pd.read_csv(FERRY_PATH, parse_dates=["date"])
    ferry["day_type"] = ferry["is_weekend"].map({1: "Weekend", 0: "Weekday"})

    for (route, day_type), grp in ferry.groupby(["route", "day_type"]):
        pax = grp["est_passengers"].mean()
        road_veh = grp["est_road_vehicles_generated"].mean()
        pier = grp["pier"].iloc[0] if "pier" in grp.columns else "Rassada Pier"
        corridor_impact = grp["corridor_impact"].iloc[0] if "corridor_impact" in grp.columns else "unknown"
        cid = _corr_id(corridor_impact)

        text = (
            f"[Ferry] {route} — {day_type}:\n"
            f"  Departure pier: {pier}\n"
            f"  Est. passengers/day: {pax:.0f} | "
            f"Est. road vehicles generated: {road_veh:.0f}\n"
            f"  Corridor impact: {corridor_impact}\n"
            f"  Note: ferry arrivals generate road traffic near {pier}"
        )
        chunks.append({
            "text": text,
            "metadata": {
                "source": "transport",
                "transport_type": "ferry",
                "route": route,
                "day_type": day_type,
                "corridor_id": cid,
            },
        })

    return chunks
