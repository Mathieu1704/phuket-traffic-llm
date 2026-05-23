"""calendar_features.csv + weekly_events.csv → event chunks."""
import pandas as pd
from pathlib import Path

CAL_PATH = Path(__file__).resolve().parents[3] / "data" / "phuket_calendar_features.csv"
EVT_PATH = Path(__file__).resolve().parents[3] / "data" / "phuket_weekly_events.csv"

IMPACT_TRAFFIC = {
    "High": "strong traffic impact — expect significant congestion",
    "Medium": "moderate traffic impact — above-average volumes expected",
    "Low": "minor traffic impact",
}


def textualize() -> list[dict]:
    chunks = []

    # Calendar / holidays
    cal = pd.read_csv(CAL_PATH, parse_dates=["date"])
    for _, r in cal.iterrows():
        impact_label = IMPACT_TRAFFIC.get(str(r["impact"]).strip(), "some traffic impact")
        text = (
            f"[{r['date'].strftime('%d %b %Y')}] {r['event_name']} ({r['type']}):\n"
            f"  Area affected: {r['affected_area']}\n"
            f"  Impact level: {r['impact']} — {impact_label}\n"
            f"  Note: Thai public holidays generate island-wide travel surges, "
            f"especially on Airport Road and Patong Hill"
        )
        chunks.append({
            "text": text,
            "metadata": {
                "source": "events",
                "event_type": "holiday",
                "date": str(r["date"].date()),
                "year": r["date"].year,
                "month": r["date"].month,
                "impact": str(r["impact"]),
            },
        })

    # Weekly local events (markets, festivals)
    evt = pd.read_csv(EVT_PATH, parse_dates=["date"])
    for _, r in evt.iterrows():
        impact_label = IMPACT_TRAFFIC.get(str(r["impact"]).strip(), "some local traffic impact")
        hours = ""
        if pd.notna(r.get("start_time")) and pd.notna(r.get("end_time")):
            hours = f" ({r['start_time']}–{r['end_time']})"
        text = (
            f"[{r['date'].strftime('%d %b %Y')}] {r['event_name']} ({r['type']}){hours}:\n"
            f"  Location: {r['location']}\n"
            f"  Impact: {r['impact']} — {impact_label}"
        )
        chunks.append({
            "text": text,
            "metadata": {
                "source": "events",
                "event_type": "local_event",
                "date": str(r["date"].date()),
                "year": r["date"].year,
                "month": r["date"].month,
                "impact": str(r["impact"]),
            },
        })

    return chunks
