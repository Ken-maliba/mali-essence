import flet as ft
from datetime import datetime
from supabase import create_client, Client
import os

# --- 1. CONFIGURATION SUPABASE ---
SUPABASE_URL = "https://bxhieuqyarmajfiudhaw.supabase.co"
SUPABASE_KEY = "sb_publishable_SzBqrCTbXLLF8QKneLpVtA_fW-TxCP3"

# Connexion au Cloud
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def essence_mali(page: ft.Page):
    # --- Config de la fenêtre ---
    page.title = "Dispo Essence Bamako (V2)"
    page.window_width = 390
    page.window_height = 844
    page.bgcolor = "white"
    page.scroll = "auto"

    # --- En-tête ---
    titre = ft.Text("⛽ Info Carburant", size=24, weight="bold", color="blue")
    sous_titre = ft.Text("Bamako - En temps réel", size=14, color="grey")
    divider = ft.Divider(height=20, thickness=1)

    colonne_stations = ft.Column()

    # --- FONCTION DE CHARGEMENT ---
    def charger_donnees():
        colonne_stations.controls.clear()
        try:
            reponse = supabase.table('stations').select("*").order('id').execute()
            for station in reponse.data:
                creer_carte(station)
        except Exception as e:
            colonne_stations.controls.append(ft.Text(f"Erreur : {e}", color="red"))
        page.update()

    # --- FONCTION CRÉATION DE CARTE (Modifiée pour le bouton Rouge) ---
    def creer_carte(data):

        # 1. On détermine la couleur et le style selon le statut
        if data['statut'] == "Disponible":
            theme_color = "green"
            bg_color = "green50"  # Fond vert très clair
            icone_visuel = "check_circle"
        elif data['statut'] == "Rupture":
            theme_color = "red"
            bg_color = "red50"  # Fond rouge très clair
            icone_visuel = "cancel"  # Une croix
        else:
            theme_color = "grey"
            bg_color = "blue50"  # Fond par défaut
            icone_visuel = "circle_outlined"

        heure_txt = data['heure'] if data['heure'] else "-"

        # 2. Fonction générique pour mettre à jour (évite de répéter le code)
        def changer_statut(nouveau_statut):
            maintenant = datetime.now().strftime("%H:%M")

            # Envoi vers Supabase
            supabase.table('stations').update({
                "statut": nouveau_statut,
                "heure": maintenant
            }).eq("id", data['id']).execute()

            # Message de confirmation
            page.snack_bar = ft.SnackBar(ft.Text(f"Statut mis à jour pour {data['nom']} !"))
            page.snack_bar.open = True

            # Rechargement
            charger_donnees()

        # 3. Les boutons d'action
        # Bouton VERT (Oui)
        btn_oui = ft.IconButton(
            icon="local_gas_station",
            icon_color="green",
            bgcolor="white",
            tooltip="Il y a de l'essence !",
            on_click=lambda e: changer_statut("Disponible")
        )

        # Bouton ROUGE (Non)
        btn_non = ft.IconButton(
            icon="highlight_off",
            icon_color="red",
            bgcolor="white",
            tooltip="Rupture de stock",
            on_click=lambda e: changer_statut("Rupture")
        )

        # 4. Assemblage de la carte
        carte = ft.Container(
            padding=15,
            margin=5,
            bgcolor=bg_color,  # La couleur change selon le statut
            border_radius=10,
            content=ft.Row(
                controls=[
                    # Partie Gauche : Infos Texte
                    ft.Column(
                        controls=[
                            ft.Text(data['nom'], weight="bold", size=16),
                            ft.Text(data['quartier'], italic=True, size=12, color="grey"),
                            ft.Row([
                                ft.Icon(icone_visuel, color=theme_color, size=16),
                                ft.Text(data['statut'], color=theme_color, weight="bold", size=12),
                            ])
                        ],
                        expand=True
                    ),
                    # Partie Droite : Les Boutons et l'Heure
                    ft.Column(
                        controls=[
                            ft.Text(f"MàJ : {heure_txt}", size=10, color="grey"),
                            ft.Row([btn_oui, btn_non], alignment="center")  # Les deux boutons côte à côte
                        ],
                        horizontal_alignment="center"
                    )
                ],
                alignment="spaceBetween"
            )
        )
        colonne_stations.controls.append(carte)

    # --- LANCEMENT ---
    page.add(titre, sous_titre, divider, colonne_stations)
    charger_donnees()


# view=ft.WEB_BROWSER : Ouvre dans le navigateur
# On récupère le port donné par le Cloud, sinon on utilise 8550 par défaut
port = int(os.environ.get("PORT", 8550))

# view=ft.WEB_BROWSER est important pour le web
ft.app(target=essence_mali, view=ft.WEB_BROWSER, host="0.0.0.0", port=port)