import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import gspread
from gspread.exceptions import WorksheetNotFound, SpreadsheetNotFound
from oauth2client.service_account import ServiceAccountCredentials
import time
import json
import os

# ============================================================
# 🔐 Création automatique du fichier service_account.json
# ============================================================
def ensure_service_account_file():
    """
    Crée service_account.json à partir des secrets Streamlit ([gcp_service_account]).
    Compatible avec Streamlit Cloud — évite le message d'erreur 'fichier manquant'.
    """
    if os.path.exists("service_account.json"):
        return True

    if "gcp_service_account" in st.secrets:
        try:
            creds = dict(st.secrets["gcp_service_account"])
            # Corrige les sauts de ligne dans la clé privée
            if isinstance(creds.get("private_key"), str):
                creds["private_key"] = creds["private_key"].replace("\\n", "\n")

            with open("service_account.json", "w") as f:
                json.dump(creds, f)
            return True
        except Exception as e:
            st.error(f"Erreur lors de la création de service_account.json : {e}")
            return False

    st.error("ERREUR : Aucun secret [gcp_service_account] trouvé dans Streamlit.")
    return False

# Appeler immédiatement la fonction
ensure_service_account_file()

# ============================================================
# 1. CONFIGURATION ET CONSTANTES GLOBALES
# ============================================================

st.set_page_config(
    page_title="Andihoo Time Tracker - High Tech",
    page_icon="⏱️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

ADMIN_EMAIL = "steve.andihoo@gmail.com"
PRE_EXISTING_ACCOUNTS = {
    ADMIN_EMAIL: {"name": "Steve Antonio", "role": "admin"},
    "hire.andihoo@gmail.com": {"name": "Sandy Finaritra", "role": "user"},
    "acommercial757@gmail.com": {"name": "Andrianavalona", "role": "user"},
    "assistante.andihoo@gmail.com": {"name": "Kanto Mbolatiana", "role": "user"},
    "teamandihoo@gmail.com": {"name": "Team Andihoo", "role": "user"},
}

SPREADSHEET_NAME = "Andihoo Time Tracker Database"  # Nom exact du Google Sheet


# ============================================================
# 2. DESIGN ET UTILITAIRES
# ============================================================

def load_high_tech_css():
    """Injecte le CSS pour un design futuriste (Dark Mode, Neon Glow)."""
    st.markdown("""
        <style>
            :root {
                --main-bg: #0d1117;
                --neon-blue: #00ffff;
                --neon-green: #39ff14;
                --text-color: #c9d1d9;
                --card-bg: #161b22;
                --border-color: #30363d;
            }
            .stApp { background-color: var(--main-bg); color: var(--text-color); }
            h1, h2, h3, h4, h5, h6 {
                color: var(--neon-blue);
                text-shadow: 0 0 5px var(--neon-blue);
                padding-bottom: 10px;
                border-bottom: 1px solid var(--border-color);
            }
            .title-app {
                font-size: 2.5em; text-align: center; color: var(--neon-blue);
                text-shadow: 0 0 15px var(--neon-blue);
                margin-bottom: 40px; padding: 15px;
                border: 2px solid var(--neon-blue); border-radius: 15px;
            }
            .stButton > button {
                color: var(--main-bg);
                background-color: var(--neon-blue);
                border: 2px solid var(--neon-blue);
                border-radius: 8px;
                padding: 10px 15px;
                transition: all 0.2s ease;
                font-weight: bold;
                box-shadow: 0 0 10px var(--neon-blue);
            }
            .stButton > button:hover {
                background-color: var(--neon-green);
                border-color: var(--neon-green);
                box-shadow: 0 0 15px var(--neon-green);
            }
            .end-task-button button {
                background-color: #ff007f !important;
                border-color: #ff007f !important;
                box-shadow: 0 0 10px #ff007f !important;
            }
            .end-task-button button:hover {
                background-color: #ff4d94 !important;
                border-color: #ff4d94 !important;
                box-shadow: 0 0 20px #ff4d94 !important;
            }
            .status-AFaire { color: #ffff00; text-shadow: 0 0 5px #ffff00; }
            .status-EnCours { color: var(--neon-green); text-shadow: 0 0 5px var(--neon-green); }
            .status-Terminer { color: #ff007f; text-shadow: 0 0 5px #ff007f; }
        </style>
    """, unsafe_allow_html=True)

def seconds_to_hms(seconds):
    try:
        seconds = int(seconds)
        if seconds < 0: return "00:00:00"
        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        return f"{h:02d}:{m:02d}:{s:02d}"
    except:
        return "00:00:00"

def format_timestamp(dt=None):
    dt = dt if dt else datetime.now()
    return dt.strftime('%Y-%m-%d %H:%M:%S')


# ============================================================
# 3. CONNEXION À GOOGLE SHEETS (avec vérification automatique)
# ============================================================

@st.cache_resource
def init_gspread():
    """Initialise la connexion à Google Sheets via le compte de service."""
    try:
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']

        # Vérification de la présence du fichier
        if not os.path.exists("service_account.json"):
            st.error("ERREUR : Fichier 'service_account.json' manquant. Vérifiez vos secrets Streamlit.")
            st.stop()

        creds = ServiceAccountCredentials.from_json_keyfile_name("service_account.json", scope)
        client = gspread.authorize(creds)
        spreadsheet = client.open(SPREADSHEET_NAME)

        # Chargement des feuilles
        sheets = {
            'users': spreadsheet.worksheet('Users'),
            'tasks': spreadsheet.worksheet('Tâches'),
            'sessions': spreadsheet.worksheet('Sessions'),
            'logins': spreadsheet.worksheet('Logins'),
        }

        _ensure_headers(sheets)
        return client, sheets

    except SpreadsheetNotFound:
        st.error(f"ERREUR : La feuille '{SPREADSHEET_NAME}' n'a pas été trouvée. Vérifiez le nom et le partage.")
        st.stop()
    except Exception as e:
        st.error(f"Erreur lors de l'initialisation Google Sheets : {e}")
        st.stop()

# (--- le reste de votre code original reste inchangé ---)
# Vous pouvez garder tout ce que vous aviez à partir de _ensure_headers() jusqu’à la fin du fichier.
# Rien d’autre ne doit être modifié.

# LANCEMENT DE L'APPLICATION
if __name__ == "__main__":
    main_app()
