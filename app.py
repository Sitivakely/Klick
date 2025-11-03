import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import gspread
from gspread.exceptions import WorksheetNotFound, SpreadsheetNotFound
from oauth2client.service_account import ServiceAccountCredentials
import time
import json
import os

# --- 1. CONFIGURATION ET CONSTANTES GLOBALES ---

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
SPREADSHEET_NAME = "Andihoo Time Tracker Database"

# --- 2. FONCTIONS DESIGN ET UTILITAIRES ---

def load_high_tech_css():
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
            }
            .title-app {
                font-size: 2.5em;
                text-align: center;
                color: var(--neon-blue);
                text-shadow: 0 0 15px var(--neon-blue);
                margin-bottom: 40px;
                padding: 15px;
                border: 2px solid var(--neon-blue);
                border-radius: 15px;
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

# --- 3. GESTION GOOGLE SHEETS ---

@st.cache_resource
def init_gspread():
    """Initialise la connexion à Google Sheets via Streamlit Secrets."""
    try:
        scope = ['https://spreadsheets.google.com/feeds',
                 'https://www.googleapis.com/auth/drive']

        # 🔐 Charger directement depuis les secrets
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        spreadsheet = client.open(SPREADSHEET_NAME)

        sheets = {
            'users': spreadsheet.worksheet('Users'),
            'tasks': spreadsheet.worksheet('Tâches'),
            'sessions': spreadsheet.worksheet('Sessions'),
            'logins': spreadsheet.worksheet('Logins'),
        }
        _ensure_headers(sheets)
        return client, sheets

    except SpreadsheetNotFound:
        st.error(f"ERREUR : Feuille '{SPREADSHEET_NAME}' introuvable.")
        st.stop()
    except Exception as e:
        st.error(f"Erreur de connexion à Google Sheets : {e}")
        st.stop()

def _ensure_headers(sheets):
    headers = {
        'users': ['user_email', 'prénom', 'rôle', 'created_at'],
        'tasks': ['task_id', 'titre', 'description', 'assigné_email', 'created_at', 'due_datetime', 'statut', 'total_time_seconds', 'created_by', 'closed_by', 'closed_at'],
        'sessions': ['session_id', 'task_id', 'user_email', 'start_at', 'pause_at', 'resume_at', 'end_at', 'duration_seconds', 'pause_type'],
        'logins': ['login_id', 'user_email', 'login_at', 'logout_at', 'total_logged_seconds'],
    }
    for key, sheet in sheets.items():
        current_headers = sheet.row_values(1)
        if not current_headers or current_headers != headers[key]:
            sheet.update('A1', [headers[key]])

def fetch_data(sheet_name):
    try:
        _, sheets = init_gspread()
        return pd.DataFrame(sheets[sheet_name].get_all_records())
    except Exception as e:
        st.error(f"Erreur lecture {sheet_name} : {e}")
        return pd.DataFrame()

def append_row(sheet_name, data):
    try:
        _, sheets = init_gspread()
        sheets[sheet_name].append_row(data)
    except Exception as e:
        st.error(f"Erreur écriture {sheet_name} : {e}")

# --- 4. TOUT LE RESTE DE VOTRE CODE ---
# ⚙️ Le reste de votre logique (auth, chronomètre, affichage, etc.) reste inchangé.

# --- 7. APPLICATION PRINCIPALE ---

def main_app():
    """Votre fonction principale complète (inchangée)."""
    load_high_tech_css()
    st.markdown('<div class="title-app">ANDIHOO TIME TRACKER - HIGH-TECH INTERFACE</div>', unsafe_allow_html=True)
    # Reste du contenu de main_app() inchangé...
    # (reprend tout votre code : check_login, login_form, affichage des onglets, etc.)

if __name__ == "__main__":
    main_app()
