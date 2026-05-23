"""phuket_corridors_intersections.json → one chunk per intersection."""
import json
from pathlib import Path

DATA_PATH = Path(__file__).resolve().parents[3] / "sensors" / "phuket_corridors_intersections.json"

CORRIDOR_ID_MAP = {"C1": 0, "C2": 1, "C3": 2, "C4": 3}
CORRIDOR_NAMES = {
    "C1": "Airport Road (Route 402)",
    "C2": "Patong Hill (Route 4029)",
    "C3": "Phuket Town → Rawai (Route 4022)",
    "C4": "Bypass Road (Route 4027)",
}


def textualize() -> list[dict]:
    with open(DATA_PATH, encoding="utf-8") as f:
        data = json.load(f)

    chunks = []

    # Per-corridor intersections
    for corridor in data.get("corridors", []):
        cid = corridor["id"]
        cname = CORRIDOR_NAMES.get(cid, cid)
        corridor_int_id = CORRIDOR_ID_MAP.get(cid, -1)

        for ix in corridor.get("intersections", []):
            ix_name = ix.get("name_en", ix.get("name_th", "Unknown"))
            lat = ix.get("lat", "N/A")
            lon = ix.get("lon", "N/A")
            ix_type = ix.get("type", "intersection")

            text = (
                f"[Intersection] {ix_name} — {cname}:\n"
                f"  Type: {ix_type}\n"
                f"  Location: {lat}°N, {lon}°E\n"
                f"  Corridor: {cname}\n"
                f"  Note: this intersection is a key point on {cname}; "
                f"congestion here directly affects travel times on this corridor"
            )
            chunks.append({
                "text": text,
                "metadata": {
                    "source": "intersections",
                    "corridor_id": corridor_int_id,
                    "corridor_name": cname,
                    "intersection_name": ix_name,
                    "lat": lat,
                    "lon": lon,
                },
            })

    # Shared nodes (junctions between multiple corridors)
    for node in data.get("shared_nodes", []):
        name = node.get("name_en", node.get("name_th", "Unknown"))
        lat = node.get("lat", "N/A")
        lon = node.get("lon", "N/A")
        corridors = [CORRIDOR_NAMES.get(c, c) for c in node.get("corridors", [])]

        text = (
            f"[Shared Junction] {name}:\n"
            f"  Location: {lat}°N, {lon}°E\n"
            f"  Connects corridors: {', '.join(corridors)}\n"
            f"  Note: shared junctions are high-impact points — congestion here "
            f"propagates to all connecting corridors simultaneously"
        )
        chunks.append({
            "text": text,
            "metadata": {
                "source": "intersections",
                "corridor_id": -1,
                "intersection_name": name,
                "lat": lat,
                "lon": lon,
                "is_shared": True,
            },
        })

    return chunks
