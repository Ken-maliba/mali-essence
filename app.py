import flet as ft
from datetime import datetime
from supabase import create_client, Client
import os

# --- 1. CONFIGURATION SUPABASE ---
SUPABASE_URL = "https://bxhieuqyarmajfiudhaw.supabase.co"
SUPABASE_KEY = "sb_publishable_SzBqrCTbXLLF8QKneLpVtA_fW-TxCP3"

# Connexion sécurisée
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def essence_mali(page: ft.Page):
    # --- Configuration de la page ---
    page.title = "Dispo Essence Bamako"  # Titre officiel
    page.window_width = 390
    page.window_height = 844
    page.bgcolor = "white"
    page.scroll = "auto"
    page.theme_mode = ft.ThemeMode.LIGHT

    # Variables
    liste_complete_stations = []

    # --- UI : En-tête ---
    titre = ft.Text("⛽ Info Carburant", size=24, weight="bold", color="blue")
    sous_titre = ft.Text("Bamako - En temps réel", size=14, color="grey")

    # Barre de recherche
    barre_recherche = ft.TextField(
        hint_text="🔎 Chercher (ex: Faladié, Shell...)",
        border_radius=10,
        bgcolor="white",
        prefix_icon="search",
        content_padding=10,
        text_size=14,
        on_change=lambda e: filtrer_liste()
    )

    divider = ft.Divider(height=10, thickness=1, color="transparent")
    colonne_stations = ft.Column(spacing=10)

    # --- FONCTIONS LOGIQUES ---
    def charger_donnees():
        colonne_stations.controls.clear()
        colonne_stations.controls.append(ft.ProgressBar(width=200, color="blue"))
        page.update()

        try:
            # Récupération des données depuis Supabase
            reponse = supabase.table('stations').select("*").order('id').execute()
            nonlocal liste_complete_stations
            liste_complete_stations = reponse.data
            filtrer_liste()
        except Exception as e:
            colonne_stations.controls.clear()
            colonne_stations.controls.append(ft.Text("Erreur de connexion internet.", color="red"))
            page.update()

    def filtrer_liste():
        colonne_stations.controls.clear()
        texte_recherche = barre_recherche.value.lower() if barre_recherche.value else ""

        compteur = 0
        for station in liste_complete_stations:
            nom = station['nom'].lower()
            quartier = station['quartier'].lower()

            if texte_recherche in nom or texte_recherche in quartier:
                creer_carte(station)
                compteur += 1

        if compteur == 0:
            colonne_stations.controls.append(
                ft.Container(
                    content=ft.Text("Aucune station trouvée...", italic=True, color="grey"),
                    alignment=ft.alignment.center,
                    padding=20
                )
            )
        page.update()

    # --- CRÉATION DE LA CARTE (Mode Sécurisé) ---
    def creer_carte(data):
        # 1. Couleurs et Icônes
        if data['statut'] == "Disponible":
            theme_color = "green"
            bg_color = "green50"
            icone_visuel = "check_circle"
        elif data['statut'] == "Rupture":
            theme_color = "red"
            bg_color = "red50"
            icone_visuel = "cancel"
        else:
            theme_color = "grey"
            bg_color = "blue50"
            icone_visuel = "circle_outlined"

        heure_txt = data['heure'] if data['heure'] else "-"

        # Zone dynamique (Boutons <-> Mot de passe)
        zone_actions = ft.Container()

        # A. Mode Saisie du Code
        def afficher_saisie(nouveau_statut):
            champ_code = ft.TextField(
                password=True,
                width=80,
                text_size=12,
                hint_text="Code",
                content_padding=5,
                text_align="center",
                bgcolor="white",
                border_radius=5
            )

            def valider_action(e):
                code_attendu = str(data.get('code_secret', ''))

                if champ_code.value == code_attendu and code_attendu:
                    # Mise à jour Supabase
                    maintenant = datetime.now().strftime("%H:%M")
                    try:
                        supabase.table('stations').update({
                            "statut": nouveau_statut,
                            "heure": maintenant
                        }).eq("id", data['id']).execute()

                        page.snack_bar = ft.SnackBar(ft.Text(f"Succès ! Station {nouveau_statut}"), bgcolor="green")
                        page.snack_bar.open = True
                        charger_donnees()
                    except:
                        page.snack_bar = ft.SnackBar(ft.Text("Erreur de connexion"), bgcolor="red")
                        page.snack_bar.open = True
                        page.update()
                else:
                    champ_code.border_color = "red"
                    champ_code.update()

            def annuler_action(e):
                remettre_boutons()

            zone_actions.content = ft.Row(
                controls=[
                    champ_code,
                    ft.IconButton(icon="check", icon_color="green", on_click=valider_action, tooltip="Valider"),
                    ft.IconButton(icon="close", icon_color="grey", on_click=annuler_action, tooltip="Annuler"),
                ],
                alignment="center",
                spacing=0
            )
            zone_actions.update()

        # B. Mode Boutons Normaux
        def remettre_boutons():
            btn_oui = ft.IconButton(
                icon="local_gas_station",
                icon_color="green",
                bgcolor="white",
                tooltip="Mettre en Disponible",
                on_click=lambda e: afficher_saisie("Disponible")
            )
            btn_non = ft.IconButton(
                icon="highlight_off",
                icon_color="red",
                bgcolor="white",
                tooltip="Signaler une Rupture",
                on_click=lambda e: afficher_saisie("Rupture")
            )

            zone_actions.content = ft.Row([btn_oui, btn_non], alignment="center")

            # Sécurité anti-crash
            if zone_actions.page:
                zone_actions.update()

        # Initialisation
        remettre_boutons()

        # Structure Visuelle
        carte = ft.Container(
            padding=15,
            bgcolor=bg_color,
            border_radius=12,
            content=ft.Row(
                controls=[
                    # Infos Station
                    ft.Column(
                        controls=[
                            ft.Text(data['nom'], weight="bold", size=16, color="black"),
                            ft.Text(data['quartier'], italic=True, size=12, color="grey"),
                            ft.Container(height=5),
                            ft.Row([
                                ft.Icon(icone_visuel, color=theme_color, size=16),
                                ft.Text(data['statut'], color=theme_color, weight="bold", size=12),
                            ], spacing=5)
                        ],
                        expand=True
                    ),
                    # Actions
                    ft.Column(
                        controls=[
                            ft.Text(f"MàJ : {heure_txt}", size=10, color="grey"),
                            zone_actions
                        ],
                        horizontal_alignment="center",
                        alignment="center"
                    )
                ],
                alignment="spaceBetween",
                vertical_alignment="center"
            )
        )
        colonne_stations.controls.append(carte)

    # --- LANCEMENT ---
    page.add(
        ft.Container(content=titre, padding=ft.padding.only(top=10)),
        sous_titre,
        ft.Container(height=10),
        barre_recherche,
        divider,
        colonne_stations
    )
    charger_donnees()


# Configuration Serveur
port = int(os.environ.get("PORT", 8550))
ft.app(target=essence_mali, view=ft.WEB_BROWSER, host="0.0.0.0", port=port)
