"""tomtom_phuket/processed/segments_all.csv → segment-level narrative chunks."""
import pandas as pd
from pathlib import Path

DATA_PATH = Path(__file__).resolve().parents[3] / "tomtom_phuket" / "processed" / "segments_all.csv"

ROUTE_CORR_ID = {
    "Airport Road": 0,
    "Patong Hill": 1,
    "Phuket Town to Rawai": 2,
    "Bypass Road": 3,
}


def _corr_id(route_name: str) -> int:
    for key, cid in ROUTE_CORR_ID.items():
        if key.lower() in route_name.lower():
            return cid
    return -1


def textualize() -> list[dict]:
    df = pd.read_csv(DATA_PATH)
    chunks = []

    # Group by route × timeset × daterange → one chunk per group
    group_cols = ["route_name", "timeset_name", "daterange_name"]
    for keys, grp in df.groupby(group_cols):
        route, timeset, daterange = keys
        cid = _corr_id(route)

        spd_med = grp["median_speed"].mean()
        spd_harm = grp["harmonic_avg_speed"].mean()
        ttr = grp["travel_time_ratio"].mean()
        p15 = grp["speed_p15"].mean()
        p85 = grp["speed_p85"].mean()
        cong = grp["congestion_ratio"].mean()
        n_segs = len(grp)

        text = (
            f"[TomTom Segment Data] {route} — {timeset} | {daterange}:\n"
            f"  Segments analysed: {n_segs}\n"
            f"  Median speed: {spd_med:.1f} km/h | Harmonic avg: {spd_harm:.1f} km/h\n"
            f"  Speed range P15–P85: {p15:.1f}–{p85:.1f} km/h\n"
            f"  Travel time ratio: {ttr:.2f} | Congestion ratio: {cong:.2f}"
        )
        chunks.append({
            "text": text,
            "metadata": {
                "source": "traffic_segments",
                "corridor_id": cid,
                "route_name": route,
                "timeset": timeset,
                "daterange": daterange,
            },
        })
    return chunks
