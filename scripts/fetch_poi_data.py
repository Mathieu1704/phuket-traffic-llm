import requests
import pandas as pd
import time

def fetch_osm_pois():
    print("🌍 Démarrage de l'extraction des POI via OpenStreetMap...")

    # Requête Overpass QL (Langage de requête OSM)
    # On cherche dans la "bounding box" de Phuket
    # node, way, relation = les types d'objets sur la carte
    overpass_query = """
    [out:json][timeout:25];
    (
      // 1. Tourisme & Hôtels (Gros générateurs de trafic taxi)
      node["tourism"~"hotel|resort|attraction"](7.75,98.20,8.20,98.45);
      way["tourism"~"hotel|resort|attraction"](7.75,98.20,8.20,98.45);
      
      // 2. Shopping (Malls & Marchés)
      node["shop"~"mall|department_store|supermarket"](7.75,98.20,8.20,98.45);
      way["shop"~"mall|department_store|supermarket"](7.75,98.20,8.20,98.45);
      
      // 3. Transport (Aéroports, Ports, Gares routières)
      node["aeroway"="aerodrome"](7.75,98.20,8.20,98.45);
      node["amenity"="bus_station"](7.75,98.20,8.20,98.45);
      node["man_made"="pier"](7.75,98.20,8.20,98.45);
      
      // 4. Éducation (Bouchons le matin/soir)
      node["amenity"~"school|university"](7.75,98.20,8.20,98.45);
    );
    out center;
    """

    url = "https://overpass-api.de/api/interpreter"
    
    try:
        response = requests.get(url, params={'data': overpass_query})
        data = response.json()
        
        poi_list = []
        for element in data['elements']:
            # Récupérer le nom (s'il existe)
            name = element.get('tags', {}).get('name', 'Unknown')
            category = ""
            
            tags = element.get('tags', {})
            
            # Classification simplifiée pour ton TFE
            if 'tourism' in tags: category = 'Tourism/Hotel'
            elif 'shop' in tags: category = 'Shopping'
            elif 'aeroway' in tags or 'man_made' in tags: category = 'Transport Hub'
            elif 'amenity' in tags and 'school' in tags.get('amenity'): category = 'Education'
            else: category = 'Other'

            # Coordonnées (lat/lon)
            lat = element.get('lat') or element.get('center', {}).get('lat')
            lon = element.get('lon') or element.get('center', {}).get('lon')

            if name != 'Unknown' and lat:
                poi_list.append({
                    "name": name,
                    "category": category,
                    "latitude": lat,
                    "longitude": lon,
                    "type": element['type']
                })

        # Création du DataFrame
        df = pd.DataFrame(poi_list)
        
        # Sauvegarde
        filename = "phuket_poi_data.csv"
        df.to_csv(filename, index=False)
        print(f"✅ Terminé ! {len(df)} POIs trouvés et sauvegardés dans '{filename}'.")
        print("   Exemple de lieux trouvés :")
        print(df[['name', 'category']].head())

    except Exception as e:
        print(f"❌ Erreur lors de la requête OSM : {e}")

if __name__ == "__main__":
    fetch_osm_pois()