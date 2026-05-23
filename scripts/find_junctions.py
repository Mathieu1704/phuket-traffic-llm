import requests
import json
import time

CORRIDORS = [
    {
        "name": "Airport Road (Route 402)",
        "bbox": (7.9975, 98.2900, 8.1132, 98.3400),
        "highway": "402",
    },
    {
        "name": "Patong Hill (Route 4029)",
        "bbox": (7.8800, 98.2900, 7.9300, 98.3400),
        "highway": "4029",
    },
    {
        "name": "Phuket Town to Rawai (Route 4022)",
        "bbox": (7.7700, 98.3200, 7.9000, 98.4100),
        "highway": "4022",
    },
    {
        "name": "Bypass Road (Route 4027)",
        "bbox": (7.8800, 98.3300, 7.9600, 98.4100),
        "highway": "4027",
    },
]

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

def find_junctions(corridor):
    s, w, n, e = corridor["bbox"]
    ref = corridor["highway"]

    query = f"""
[out:json][timeout:30];
(
  node["highway"="traffic_signals"]({s},{w},{n},{e});
  node["highway"="junction"]({s},{w},{n},{e});
  node["junction"="yes"]({s},{w},{n},{e});
);
out body;
"""
    time.sleep(5)
    r = requests.post(OVERPASS_URL, data={"data": query}, timeout=60)
    if not r.text.strip():
        print("  [WARNING] Empty response from Overpass API, skipping.")
        return []
    data = r.json()
    nodes = data.get("elements", [])

    results = []
    for node in nodes:
        tags = node.get("tags", {})
        name = tags.get("name") or tags.get("name:en") or tags.get("ref") or "unnamed"
        results.append({
            "name": name,
            "lat": node["lat"],
            "lon": node["lon"],
            "type": tags.get("highway", tags.get("junction", "?")),
        })

    return results


def find_named_roads(corridor):
    s, w, n, e = corridor["bbox"]

    query = f"""
[out:json][timeout:30];
way["highway"]["name"]({s},{w},{n},{e});
out tags;
"""
    time.sleep(5)
    r = requests.post(OVERPASS_URL, data={"data": query}, timeout=60)
    if not r.text.strip():
        return []
    data = r.json()
    ways = data.get("elements", [])

    names = set()
    for way in ways:
        tags = way.get("tags", {})
        name = tags.get("name") or tags.get("name:en")
        if name:
            names.add(name)
    return sorted(names)


print("=" * 60)
print("JUNCTIONS & INTERSECTIONS ON PHUKET CORRIDORS")
print("=" * 60)

for corridor in CORRIDORS:
    print(f"\n--- {corridor['name']} ---")
    junctions = find_junctions(corridor)
    if junctions:
        print(f"  {len(junctions)} junction(s) found:")
        for j in junctions:
            print(f"    [{j['type']}] {j['name']}  ({j['lat']:.4f}, {j['lon']:.4f})")
    else:
        print("  No junctions found in this bbox.")
