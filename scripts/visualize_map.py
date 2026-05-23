import pandas as pd
import folium
from folium.plugins import MarkerCluster

def create_interactive_map():
    print("🗺️ Génération de la carte interactive...")

    # 1. Charger les données
    try:
        df = pd.read_csv("phuket_poi_data.csv")
    except FileNotFoundError:
        print("❌ Erreur : Le fichier 'phuket_poi_data.csv' est introuvable.")
        return

    # 2. Créer la carte centrée sur Phuket
    m = folium.Map(location=[7.95, 98.33], zoom_start=11, tiles="CartoDB positron") 
    # 'CartoDB positron' est un fond de carte très propre pour les thèses.
    # Tu peux aussi essayer tiles="OpenStreetMap" pour plus de détails.

    # 3. Créer un cluster (pour regrouper les points quand on dézoome)
    marker_cluster = MarkerCluster().add_to(m)

    # 4. Ajouter les points avec des couleurs différentes
    for index, row in df.iterrows():
        
        # Choix de la couleur selon la catégorie
        color = "gray"
        icon_type = "info-sign"
        
        cat = row['category']
        if cat == "Tourism/Hotel":
            color = "blue"      # Bleu pour les touristes
            icon_type = "home"
        elif cat == "Shopping":
            color = "red"       # Rouge pour le shopping (zones chaudes)
            icon_type = "shopping-cart"
        elif cat == "Education":
            color = "green"     # Vert pour les écoles
            icon_type = "book"
        elif cat == "Transport Hub":
            color = "black"     # Noir pour aéroport/ports
            icon_type = "plane"

        # Création du popup (texte quand on clique)
        popup_text = f"<b>{row['name']}</b><br>Type: {cat}"

        folium.Marker(
            location=[row['latitude'], row['longitude']],
            popup=popup_text,
            icon=folium.Icon(color=color, icon=icon_type)
        ).add_to(marker_cluster)

    # 5. Sauvegarder
    output_file = "phuket_poi_map.html"
    m.save(output_file)
    print(f"✅ Carte générée avec succès : {output_file}")
    print("👉 Ouvre ce fichier dans ton navigateur (Chrome/Safari) pour voir la carte !")

if __name__ == "__main__":
    create_interactive_map()