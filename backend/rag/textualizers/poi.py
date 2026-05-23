"""phuket_poi_data.csv → geographic cluster chunks (one per category × zone)."""
import pandas as pd
from pathlib import Path

DATA_PATH = Path(__file__).resolve().parents[3] / "data" / "phuket_poi_data.csv"

# Rough geographic zones based on lat/lon
ZONES = {
    "North (Airport / Thalang)": lambda lat, lon: lat > 8.0,
    "Patong Beach": lambda lat, lon: lon < 98.31 and 7.87 < lat < 7.94,
    "Phuket Town": lambda lat, lon: 98.37 < lon < 98.42 and 7.86 < lat < 7.92,
    "Chalong / Rawai (South)": lambda lat, lon: lat < 7.86,
    "Central (Kathu / Bypass)": lambda lat, lon: True,  # catch-all
}

CORRIDOR_ACCESS = {
    "North (Airport / Thalang)": "Airport Road (Route 402)",
    "Patong Beach": "Patong Hill (Route 4029)",
    "Phuket Town": "Phuket Town → Rawai (Route 4022)",
    "Chalong / Rawai (South)": "Phuket Town → Rawai (Route 4022)",
    "Central (Kathu / Bypass)": "Bypass Road (Route 4027)",
}


def _assign_zone(lat: float, lon: float) -> str:
    for zone_name, test in ZONES.items():
        if test(lat, lon):
            return zone_name
    return "Central (Kathu / Bypass)"


def textualize() -> list[dict]:
    df = pd.read_csv(DATA_PATH)
    df["zone"] = df.apply(lambda r: _assign_zone(r["latitude"], r["longitude"]), axis=1)

    chunks = []
    for (zone, category), group in df.groupby(["zone", "category"]):
        count = len(group)
        corridor = CORRIDOR_ACCESS.get(zone, "multiple corridors")
        names_sample = ", ".join(group["name"].dropna().head(5).tolist())

        text = (
            f"[POI] {zone} — {category.title()}:\n"
            f"  Count: {count} {category} points of interest\n"
            f"  Examples: {names_sample}\n"
            f"  Main road access: {corridor}\n"
            f"  Note: concentration of {category} POIs in this zone generates "
            f"recurring demand on {corridor}"
        )
        chunks.append({
            "text": text,
            "metadata": {
                "source": "poi",
                "zone": zone,
                "category": category,
                "count": count,
            },
        })
    return chunks
