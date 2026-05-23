"""OpenSky Network — live flights over Phuket / HKT airport. No API key required."""
import requests

# Bounding box around HKT airport
LAT_MIN, LAT_MAX = 7.9, 8.3
LON_MIN, LON_MAX = 98.2, 98.5
HKT_LAT, HKT_LON = 8.1132, 98.3017
URL = "https://opensky-network.org/api/states/all"


def get_live_flights() -> dict:
    try:
        res = requests.get(URL, params={
            "lamin": LAT_MIN, "lamax": LAT_MAX,
            "lomin": LON_MIN, "lomax": LON_MAX,
        }, timeout=8)
        res.raise_for_status()
        states = res.json().get("states") or []

        # Filter: descending aircraft (on_ground=False, vertical_rate < 0 or low altitude)
        arriving = []
        for s in states:
            if s and len(s) > 8:
                on_ground = s[8]
                alt = s[7] if s[7] else 9999
                v_rate = s[11] if s[11] else 0
                callsign = (s[1] or "").strip()
                if not on_ground and alt < 3000 and v_rate < 0:
                    arriving.append(callsign)

        total_aircraft = len(states)
        n_arriving = len(arriving)

        if n_arriving >= 3:
            traffic_note = "high arrival activity — expect increased traffic on Airport Road"
        elif n_arriving >= 1:
            traffic_note = "moderate arrival activity"
        else:
            traffic_note = "low arrival activity — Airport Road traffic impact minimal"

        return {
            "aircraft_in_zone": total_aircraft,
            "arriving": n_arriving,
            "callsigns": arriving[:5],
            "traffic_note": traffic_note,
            "source": "OpenSky Network",
        }
    except Exception as e:
        return {"error": str(e), "source": "OpenSky"}


def format_for_prompt(f: dict) -> str:
    if "error" in f:
        return f"[Live flight data unavailable: {f['error']}]"
    return (
        f"LIVE FLIGHTS (HKT airport zone right now):\n"
        f"  Aircraft in zone: {f['aircraft_in_zone']} | "
        f"Approaching HKT: {f['arriving']}\n"
        f"  Traffic implication: {f['traffic_note']}"
    )
