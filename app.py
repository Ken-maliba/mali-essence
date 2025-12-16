import flet as ft
from datetime import datetime
from supabase import create_client, Client
import os

# --- 1. CONFIGURATION SUPABASE ---
SUPABASE_URL = "https://bxhieuqyarmajfiudhaw.supabase.co"
SUPABASE_KEY = "sb_publishable_SzBqrCTbXLLF8QKneLpVtA_fW-TxCP3"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def essence_mali(page: ft.Page):
    page.title = "Dispo Essence Bamako (Plan B)"
    page.window_width = 390
    page.window_height = 844
    page.bgcolor = "white"
    page.scroll = "auto"

    liste_complete_stations = []

    # En-tête
    titre = ft.Text("⛽ Info Carburant", size=24, weight="bold", color="blue")
    sous_titre = ft.Text("Bamako - En temps réel", size=14, color="grey")

    barre_recherche = ft.TextField(
        hint_text="🔎 Chercher...",
        border_radius=10,
        bgcolor="white",
        prefix_icon="search",
        on_change=lambda e: filtrer_liste()
    )

    divider = ft.Divider(height=10, thickness=1)
    colonne_stations = ft.Column()

    def charger_donnees():
        colonne_stations.controls.clear()
        colonne_stations.controls.append(ft.ProgressBar(width=200, color="blue"))
        page.update()

        try:
            reponse = supabase.table('stations').select("*").order('id').execute()
            nonlocal liste_complete_stations
            liste_complete_stations = reponse.data
            filtrer_liste()
        except Exception as e:
            colonne_stations.controls.clear()
            colonne_stations.controls.append(ft.Text(f"Erreur : {e}", color="red"))
            page.update()

    def filtrer_liste():
        colonne_stations.controls.clear()
        texte_recherche = barre_recherche.value.lower() if barre_recherche.value else ""

        for station in liste_complete_stations:
            nom = station['nom'].lower()
            quartier = station['quartier'].lower()

            if texte_recherche in nom or texte_recherche in quartier:
                creer_carte(station)

        if len(colonne_stations.controls) == 0:
            colonne_stations.controls.append(ft.Text("Rien trouvé...", italic=True, color="grey"))
        page.update()

    # --- NOUVELLE LOGIQUE D'AFFICHAGE ---
    def creer_carte(data):
        # 1. Définition des couleurs
        if data['statut'] == "Disponible":
            theme_color = "
