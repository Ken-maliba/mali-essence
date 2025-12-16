import flet as ft
from datetime import datetime
from supabase import create_client, Client
import os

# --- DIAGNOSTIC AU DÉMARRAGE ---
print("--- VÉRIFICATION ---")
try:
    if "fond.png" in os.listdir("assets"):
        print("✅ SUCCÈS : L'image est bien là ! Elle devrait s'afficher.")
    else:
        print("⚠️ ATTENTION : Le fichier s'appelle peut-être fond.png.png ?")
except:
    print("❌ ERREUR : Dossier assets introuvable.")
print("--------------------")

# --- 1. CONFIGURATION SUPABASE ---
SUPABASE_URL = "https://bxhieuqyarmajfiudhaw.supabase.co"
SUPABASE_KEY = "sb_publishable_SzBqrCTbXLLF8QKneLpVtA_fW-TxCP3"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def essence_mali(page: ft.Page):
    # Config Page
    page.title = "Dispo Essence Bamako"
    page.window_width = 390
    page.window_height = 844
    page.scroll = "auto"
    page.theme_mode = ft.ThemeMode.LIGHT
    
    # --- FOND D'ÉCRAN ---
    page.assets_dir = "assets"  # Le dossier
    
    page.background_image = ft.Image(
        src="/fond.png",         # <--- J'ai remis le slash "/" indispensable
        fit=ft.ImageFit.COVER,   
        opacity=0.3,             # Un peu plus visible
        repeat=ft.ImageRepeat.NO_REPEAT
    )

    # Variables
    liste_complete_stations = []

    # UI Elements
    titre = ft.Text("⛽ Info Carburant", size=24, weight="bold", color="blue")
    sous_titre = ft.Text("Bamako - En temps réel", size=14, color="grey")
    
    barre_recherche = ft.TextField(
        hint_text="🔎 Chercher...",
        border_radius=10,
        bgcolor="#E6FFFFFF", 
        prefix_icon="search", 
        content_padding=10,
        text_size=14,
        on_change=lambda e: filtrer_liste()
    )

    divider = ft.Divider(height=10, thickness=1, color="transparent")
    colonne_stations = ft.Column(spacing=10)

    # Fonctions
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
            colonne_stations.controls.append(ft.Text("Erreur connexion", color="red"))
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
                    padding=20,
                    bgcolor="#E6FFFFFF",
                    border_radius=10
                )
            )
        page.update()

    def creer_carte(data):
        statut_lower = data['statut'].lower()
        if "disponible" in statut_lower:
            theme_color = "green"; bg_color = "#F2E8F5E9"; icone_visuel = "check_circle"
        elif "rupture" in statut_lower:
            theme_color = "red"; bg_color = "#F2FFEBEE"; icone_visuel = "cancel"
        else:
            theme_color = "grey"; bg_color = "#F2E3F2FD"; icone_visuel = "circle_outlined"

        heure_txt = data['heure'] if data['heure'] else "-"
        zone_actions = ft.Container()

        def afficher_saisie(action_statut):
            champ_code = ft.TextField(password=True, width=70, text_size=12, hint_text="Code", content_padding=5, text_align="center", bgcolor="white", border_radius=5)
            choix_carburant = ft.Dropdown(width=85, text_size=12, content_padding=5, options=[ft.dropdown.Option("Essence"), ft.dropdown.Option("Gasoil"), ft.dropdown.Option("Tout")], value="Essence", bgcolor="white", border_radius=5)

            def valider_action(e):
                code_attendu = str(data.get('code_secret', ''))
                if champ_code.value == code_attendu and code_attendu:
                    selection = choix_carburant.value
                    texte_final = "Essence et Gasoil" if selection == "Tout" else selection
                    nouveau_statut_complet = f"{texte_final} : {action_statut}"
                    try:
                        maintenant = datetime.now().strftime("%H:%M")
                        supabase.table('stations').update({"statut": nouveau_statut_complet, "heure": maintenant}).eq("id", data['id']).execute()
                        page.snack_bar = ft.SnackBar(ft.Text(f"Succès !"), bgcolor="green"); page.snack_bar.open = True; charger_donnees() 
                    except:
                        page.snack_bar = ft.SnackBar(ft.Text("Erreur connexion"), bgcolor="red"); page.snack_bar.open = True; page.update()
                else:
                    champ_code.border_color = "red"; champ_code.update()

            def annuler_action(e):
                remettre_boutons()

            zone_actions.content = ft.Row(controls=[champ_code, choix_carburant, ft.IconButton(icon="check", icon_color="green", on_click=valider_action), ft.IconButton(icon="close", icon_color="grey", on_click=annuler_action)], alignment="center", spacing=5)
            zone_actions.update()

        def remettre_boutons():
            btn_oui = ft.IconButton(icon="local_gas_station", icon_color="green", bgcolor="white", tooltip="Disponible", on_click=lambda e: afficher_saisie("Disponible"))
            btn_non = ft.IconButton(icon="highlight_off", icon_color="red", bgcolor="white", tooltip="Rupture", on_click=lambda e: afficher_saisie("Rupture"))
            zone_actions.content = ft.Row([btn_oui, btn_non], alignment="center")
            if zone_actions.page: zone_actions.update()

        remettre_boutons()

        carte = ft.Container(
            padding=15, bgcolor=bg_color, border_radius=12,
            content=ft.Row(controls=[
                ft.Column(controls=[ft.Text(data['nom'], weight="bold", size=16), ft.Text(data['quartier'], italic=True, size=12, color="grey"), ft.Container(height=5), ft.Row([ft.Icon(icone_visuel, color=theme_color, size=16), ft.Text(data['statut'], color=theme_color, weight="bold", size=12)], spacing=5)], expand=True),
                ft.Column(controls=[ft.Text(f"MàJ : {heure_txt}", size=10, color="grey"), zone_actions], horizontal_alignment="center", alignment="center")
            ], alignment="spaceBetween", vertical_alignment="center")
        )
        colonne_stations.controls.append(carte)

    header_container = ft.Container(
        content=ft.Column([titre, sous_titre]),
        padding=10, bgcolor="#CCFFFFFF", border_radius=10
    )

    page.add(ft.Container(height=10), header_container, ft.Container(height=10), barre_recherche, divider, colonne_stations)
    charger_donnees()

port = int(os.environ.get("PORT", 8550))
ft.app(target=essence_mali, view=ft.WEB_BROWSER, host="0.0.0.0", port=port)
