import pandas as pd
from datetime import date, timedelta

def generate_market_events():
    print("🎪 Génération des événements hebdomadaires (Marchés)...")
    
    start_date = date(2023, 1, 1)
    end_date = date(2024, 12, 31)
    
    events = []
    
    current_date = start_date
    while current_date <= end_date:
        # 1. Phuket Walking Street (Lard Yai) - Tous les dimanches
        if current_date.weekday() == 6: # 6 = Dimanche
            events.append({
                "date": current_date,
                "event_name": "Sunday Walking Street (Lard Yai)",
                "type": "Night Market",
                "impact": "High",
                "location": "Phuket Town",
                "start_time": "16:00",
                "end_time": "22:00"
            })
            
        # 2. Chillva Market - Lundi à Samedi (Impact moyen, mais constant)
        # On va mettre juste le Samedi pour ne pas surcharger, car c'est le plus gros jour
        if current_date.weekday() == 5: # 5 = Samedi
            events.append({
                "date": current_date,
                "event_name": "Chillva Market Peak",
                "type": "Night Market",
                "impact": "Medium",
                "location": "Phuket Town",
                "start_time": "18:00",
                "end_time": "23:00"
            })

        # 3. Naka Market (Weekend Market) - Samedi et Dimanche
        if current_date.weekday() in [5, 6]:
            events.append({
                "date": current_date,
                "event_name": "Naka Weekend Market",
                "type": "Night Market",
                "impact": "High",
                "location": "Phuket Town (West)",
                "start_time": "16:00",
                "end_time": "23:00"
            })

        current_date += timedelta(days=1)
        
    df = pd.DataFrame(events)
    filename = "phuket_weekly_events.csv"
    df.to_csv(filename, index=False)
    print(f"✅ Terminé ! {len(df)} événements de marché générés dans '{filename}'.")

if __name__ == "__main__":
    generate_market_events()