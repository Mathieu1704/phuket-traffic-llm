"""phuket_social_trends.csv → weekly Google Trends chunks."""
import pandas as pd
from pathlib import Path

DATA_PATH = Path(__file__).resolve().parents[3] / "data" / "phuket_social_trends.csv"

MONTH_NAMES = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]


def textualize() -> list[dict]:
    df = pd.read_csv(DATA_PATH, parse_dates=["week_start"])

    # Pivot to wide format: one row per (week, all keywords)
    pivot = df.pivot_table(
        index=["week_start", "year", "month", "week_of_year", "season"],
        columns="keyword",
        values="interest_score",
        aggfunc="mean",
    ).reset_index()
    pivot.columns.name = None

    chunks = []
    for _, r in pivot.iterrows():
        yr = int(r["year"])
        mn_name = MONTH_NAMES[int(r["month"]) - 1]
        week_str = r["week_start"].strftime("%d %b %Y")

        keywords = ["Phuket", "Phuket beach", "Phuket hotel", "Phuket flight", "Phuket vacation"]
        scores = {k: round(float(r[k]), 0) for k in keywords if k in r and pd.notna(r.get(k))}

        if not scores:
            continue

        avg_score = sum(scores.values()) / len(scores)
        if avg_score > 70:
            trend_note = "high search interest — anticipate increased tourist arrivals in ~2 weeks"
        elif avg_score > 50:
            trend_note = "moderate search interest"
        else:
            trend_note = "low search interest — off-peak booking period"

        score_str = " | ".join(f"'{k}': {int(v)}" for k, v in scores.items())
        text = (
            f"[Week of {week_str}] Google Trends — Phuket keywords:\n"
            f"  {score_str}\n"
            f"  Season: {r['season']} ({mn_name} {yr})\n"
            f"  Interpretation: {trend_note}"
        )
        chunks.append({
            "text": text,
            "metadata": {
                "source": "social_trends",
                "year": yr,
                "month": int(r["month"]),
                "week_of_year": int(r["week_of_year"]),
                "avg_score": round(avg_score, 1),
            },
        })
    return chunks
