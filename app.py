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
    page.title = "Dispo Essence Bamako (Pro)"
    page.window_width = 390
    page.window_height = 844
    page.bgcolor = "white"
    page.scroll = "auto"

    liste_complete_stations = []

    # --- En-tête ---
    titre = ft.Text("⛽ Info Carburant", size=24, weight="bold", color="blue")
    sous_titre = ft.Text("Bamako - En temps réel", size=14, color="grey")

    barre_recherche = ft.TextField(
        hint_text="🔎 Chercher (ex: Faladié, Shell...)",
        border_radius=10,
        bgcolor="white",
        prefix_icon="search",
        on_change=lambda e: filtrer_liste()
    )

    divider = ft.Divider(height=10, thickness=1)
    colonne_stations = ft.Column()

    # --- CHARGEMENT ---
    def charger_donnees():
        colonne_stations.controls.clear()
        colonne_stations.controls.append(ft.ProgressBar(width=200, color="blue"))
        page.update()

        try:
            # On récupère TOUT (y compris la nouvelle colonne code_secret)
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
            colonne_stations.controls.append(ft.Text("Aucune station trouvée...", italic=True, color="grey"))
        page.update()

    # --- CRÉATION DE CARTE ---
    def creer_carte(data):
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

        # --- NOUVEAU : Vérification du Code Unique ---
        def demander_code(nouveau_statut):
            champ_code = ft.TextField(password=True, text_align="center", hint_text="Code Gérant")

            def valider_code(e):
                # ICI : On compare avec le code SPECIFIQUE de cette station
                code_attendu = data.get('code_secret')  # Récupère le code de la base

                if code_attendu and champ_code.value == code_attendu:
                    # C'est gagné
                    dlg_modal.open = False
                    page.update()

                    maintenant = datetime.now().strftime("%H:%M")
                    supabase.table('stations').update({
                        "statut": nouveau_statut,
                        "heure": maintenant
                    }).eq("id", data['id']).execute()

                    page.snack_bar = ft.SnackBar(ft.Text(f"Validé ! Statut changé."))
                    page.snack_bar.open = True
                    charger_donnees()
                else:
                    # Code faux
                    champ_code.error_text = "Code incorrect pour cette station !"
                    page.update()

            dlg_modal = ft.AlertDialog(
                modal=True,
                title=ft.Text("🔒 Accès Gérant"),
                content=ft.Column([
                    ft.Text(f"Entrez le code pour {data['nom']}"),
                    champ_code
                ], height=100),
                actions=[
                    ft.TextButton("Annuler", on_click=lambda e: fermer_dialog(dlg_modal)),
                    ft.ElevatedButton("Valider", on_click=valider_code, bgcolor="blue", color="white"),
                ],
                actions_alignment="end",
            )

            page.dialog = dlg_modal
            dlg_modal.open = True
            page.update()

        def fermer_dialog(dlg):
            dlg.open = False
            page.update()

        btn_oui = ft.IconButton(
            icon="local_gas_station",
            icon_color="green",
            bgcolor="white",
            tooltip="Disponible",
            on_click=lambda e: demander_code("Disponible")
        )

        btn_non = ft.IconButton(
            icon="highlight_off",
            icon_color="red",
            bgcolor="white",
            tooltip="Rupture",
            on_click=lambda e: demander_code("Rupture")
        )

        carte = ft.Container(
            padding=15,
            margin=5,
            bgcolor=bg_color,
            border_radius=10,
            content=ft.Row(
                controls=[
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
                    ft.Column(
                        controls=[
                            ft.Text(f"MàJ : {heure_txt}", size=10, color="grey"),
                            ft.Row([btn_oui, btn_non], alignment="center")
                        ],
                        horizontal_alignment="center"
                    )
                ],
                alignment="spaceBetween"
            )
        )
        colonne_stations.controls.append(carte)

    page.add(titre, sous_titre, barre_recherche, divider, colonne_stations)
    charger_donnees()


port = int(os.environ.get("PORT", 8550))
ft.app(target=essence_mali, view=ft.WEB_BROWSER, host="0.0.0.0", port=port)
