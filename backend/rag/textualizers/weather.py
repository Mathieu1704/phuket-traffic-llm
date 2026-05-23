"""phuket_weather_history_2023_2024.csv → daily aggregate chunks."""
import pandas as pd
from pathlib import Path

DATA_PATH = Path(__file__).resolve().parents[3] / "data" / "phuket_weather_history_2023_2024.csv"

MONTH_NAMES = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]


def textualize() -> list[dict]:
    df = pd.read_csv(DATA_PATH, parse_dates=["timestamp"])
    df["date"] = df["timestamp"].dt.date
    df["year"] = df["timestamp"].dt.year
    df["month"] = df["timestamp"].dt.month
    df["day"] = df["timestamp"].dt.day

    # Aggregate to daily means (average across all 4 locations)
    daily = (
        df.groupby(["year", "month", "day"])
        .agg(temp_mean=("temp_c", "mean"), rain_sum=("rain_mm", "sum"), wind_mean=("wind_kmh", "mean"))
        .reset_index()
    )

    # Then aggregate to monthly for concise chunks
    monthly = (
        daily.groupby(["year", "month"])
        .agg(
            temp_mean=("temp_mean", "mean"),
            rain_total=("rain_sum", "sum"),
            rain_days=("rain_sum", lambda x: (x > 1).sum()),
            wind_mean=("wind_mean", "mean"),
        )
        .reset_index()
    )

    chunks = []
    for _, r in monthly.iterrows():
        mn = MONTH_NAMES[int(r["month"]) - 1]
        yr = int(r["year"])
        rain = float(r["rain_total"])
        temp = float(r["temp_mean"])
        wind = float(r["wind_mean"])
        rain_days = int(r["rain_days"])

        if rain > 300:
            condition = "heavy monsoon — strong rain impact on traffic"
        elif rain > 150:
            condition = "moderate rain — some wet-road slowdowns expected"
        elif rain > 50:
            condition = "light rain — minimal traffic impact"
        else:
            condition = "dry conditions — good driving conditions"

        text = (
            f"[{mn} {yr}] Phuket weather summary:\n"
            f"  Average temperature: {temp:.1f}°C\n"
            f"  Total rainfall: {rain:.0f}mm over {rain_days} rainy days\n"
            f"  Average wind: {wind:.1f} km/h\n"
            f"  Conditions: {condition}"
        )
        chunks.append({
            "text": text,
            "metadata": {
                "source": "weather",
                "year": yr,
                "month": int(r["month"]),
                "rain_mm": round(rain, 1),
                "temp_c": round(temp, 1),
            },
        })
    return chunks
