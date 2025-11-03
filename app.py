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

# Configuration de la page Streamlit
st.set_page_config(
    page_title="Andihoo Time Tracker - High Tech",
    page_icon="⏱️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Constantes d'environnement (pour l'authentification simplifiée)
ADMIN_EMAIL = "steve.andihoo@gmail.com"
PRE_EXISTING_ACCOUNTS = {
    ADMIN_EMAIL: {"name": "Steve Antonio", "role": "admin"},
    "hire.andihoo@gmail.com": {"name": "Sandy Finaritra", "role": "user"},
    "acommercial757@gmail.com": {"name": "Andrianavalona", "role": "user"},
    "assistante.andihoo@gmail.com": {"name": "Kanto Mbolatiana", "role": "user"},
    "teamandihoo@gmail.com": {"name": "Team Andihoo", "role": "user"},
}
SPREADSHEET_NAME = "Andihoo Time Tracker Database" # Assurez-vous que ce nom correspond à votre feuille Google Sheet

# --- 2. FONCTIONS D'UTILITAIRES ET DESIGN ---

def load_high_tech_css():
    """Injecte le CSS pour un design futuriste (Dark Mode, Neon Glow)."""
    st.markdown("""
        <style>
            /* Variables de couleur */
            :root {
                --main-bg: #0d1117;
                --orange: #f09c20;
                --neon-green: #39ff14;
                --text-color: #c9d1d9;
                --card-bg: #161b22;
                --border-color: #30363d;
            }

            /* Fond de page général */
            .stApp {
                background-color: var(--main-bg);
                color: var(--text-color);
            }

            /* Titres */
            h1, h2, h3, h4, h5, h6 {
                color: var(--neon-blue);
                text-shadow: 0 0 5px var(--neon-blue);
                padding-bottom: 10px;
                border-bottom: 1px solid var(--border-color);
            }

            /* Conteneurs principaux */
            .stContainer, .stTabs, .stCard {
                background-color: var(--card-bg);
                border: 1px solid var(--border-color);
                border-radius: 10px;
                padding: 20px;
                box-shadow: 0 0 15px rgba(0, 255, 255, 0.2); /* Effet Glow */
                margin-bottom: 20px;
            }

            /* Boutons (Chronomètre) */
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

            /* Bouton "Terminer" Tâche */
            .end-task-button button {
                background-color: #ff007f !important; /* Rose Vif */
                border-color: #ff007f !important;
                box-shadow: 0 0 10px #ff007f !important;
            }
            .end-task-button button:hover {
                background-color: #ff4d94 !important;
                border-color: #ff4d94 !important;
                box-shadow: 0 0 20px #ff4d94 !important;
            }
            
            /* Indicateurs de statut */
            .status-AFaire { color: #ffff00; text-shadow: 0 0 5px #ffff00; }
            .status-EnCours { color: var(--neon-green); text-shadow: 0 0 5px var(--neon-green); }
            .status-Terminer { color: #ff007f; text-shadow: 0 0 5px #ff007f; }
            
            /* Titre de l'application */
            .title-app {
                font-size: 2.5em;
                text-align: center;
                color: var(--neon-blue);
                text-shadow: 0 0 15px var(--neon-blue), 0 0 20px rgba(0, 255, 255, 0.5);
                margin-bottom: 40px;
                padding: 15px;
                border: 2px solid var(--neon-blue);
                border-radius: 15px;
            }
        </style>
        """, unsafe_allow_html=True)

def seconds_to_hms(seconds):
    """Convertit un nombre de secondes en format HH:MM:SS."""
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
    """Formate la date et l'heure au format standard pour les logs."""
    dt = dt if dt else datetime.now()
    return dt.strftime('%Y-%m-%d %H:%M:%S')

# --- 3. GESTION DES DONNÉES GOOGLE SHEETS (Back-end) ---

@st.cache_resource
def init_gspread():
    """Initialise la connexion à Google Sheets via les secrets Streamlit (sans fichier local)."""
    try:
        scope = ['https://spreadsheets.google.com/feeds',
                 'https://www.googleapis.com/auth/drive']

        # Charger directement les credentials depuis Streamlit Secrets (clé : gcp_service_account)
        if "gcp_service_account" not in st.secrets:
            st.error("ERREUR : Secrets 'gcp_service_account' introuvables dans Streamlit. Vérifiez Settings -> Secrets.")
            st.stop()

        creds_dict = dict(st.secrets["gcp_service_account"])

        # Si la clé privée contient des séquences '\n', les convertir en sauts de ligne réels
        pk = creds_dict.get("private_key", "")
        if isinstance(pk, str) and "\\n" in pk:
            creds_dict["private_key"] = pk.replace("\\n", "\n")

        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        spreadsheet = client.open(SPREADSHEET_NAME)

        # Chargement des feuilles (Worksheets)
        sheets = {
            'users': spreadsheet.worksheet('Users'),
            'tasks': spreadsheet.worksheet('Tâches'),
            'sessions': spreadsheet.worksheet('Sessions'),
            'logins': spreadsheet.worksheet('Logins'),
        }

        # Assurer que les en-têtes sont corrects
        _ensure_headers(sheets)

        return client, sheets
    except SpreadsheetNotFound:
        st.error(f"ERREUR : La feuille de calcul nommée '{SPREADSHEET_NAME}' n'a pas été trouvée. Veuillez vérifier le nom et le partage.")
        st.stop()
    except Exception as e:
        st.error(f"Erreur lors de l'initialisation de Google Sheets. Vérifiez vos APIs et vos secrets. Détail: {e}")
        st.stop()
def _ensure_headers(sheets):
    """Vérifie et initialise les en-têtes si les feuilles sont vides."""
    headers = {
        'users': ['user_email', 'prénom', 'rôle', 'created_at'],
        'tasks': ['task_id', 'titre', 'description', 'assigné_email', 'created_at', 'due_datetime', 'statut', 'total_time_seconds', 'created_by', 'closed_by', 'closed_at'],
        'sessions': ['session_id', 'task_id', 'user_email', 'start_at', 'pause_at', 'resume_at', 'end_at', 'duration_seconds', 'pause_type'],
        'logins': ['login_id', 'user_email', 'login_at', 'logout_at', 'total_logged_seconds'],
    }
    
    for key, sheet in sheets.items():
        try:
            # Lire la première ligne pour vérifier les en-têtes
            current_headers = sheet.row_values(1)
            if not current_headers or current_headers != headers[key]:
                # Si vide ou incorrect, met à jour
                sheet.update('A1', [headers[key]])
        except Exception as e:
            # En cas d'erreur (feuille inexistante, etc.), on arrête
            st.error(f"Erreur critique lors de la vérification des en-têtes de la feuille '{key}'. Détail: {e}")
            st.stop()


def fetch_data(sheet_name):
    """Récupère toutes les données d'une feuille."""
    try:
        _, sheets = init_gspread()
        sheet = sheets.get(sheet_name)
        if not sheet:
             st.warning(f"Feuille {sheet_name} non trouvée.")
             return pd.DataFrame()

        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        
        # S'assurer que les colonnes existent, même si la feuille est vide
        if df.empty:
            headers = {
                'users': ['user_email', 'prénom', 'rôle', 'created_at'],
                'tasks': ['task_id', 'titre', 'description', 'assigné_email', 'created_at', 'due_datetime', 'statut', 'total_time_seconds', 'created_by', 'closed_by', 'closed_at'],
                'sessions': ['session_id', 'task_id', 'user_email', 'start_at', 'pause_at', 'resume_at', 'end_at', 'duration_seconds', 'pause_type'],
                'logins': ['login_id', 'user_email', 'login_at', 'logout_at', 'total_logged_seconds'],
            }
            return pd.DataFrame(columns=headers.get(sheet_name, []))

        return df
    except Exception as e:
        st.error(f"Erreur de lecture de Google Sheet ({sheet_name}). Vérifiez vos permissions. Détail: {e}")
        return pd.DataFrame()

def append_row(sheet_name, data):
    """Ajoute une ligne de données à la feuille spécifiée."""
    try:
        _, sheets = init_gspread()
        sheet = sheets[sheet_name]
        sheet.append_row(data)
        st.session_state['data_last_update'] = datetime.now() # Force la mise à jour
    except Exception as e:
        st.error(f"Erreur d'écriture dans Google Sheet ({sheet_name}). Détail: {e}")


def update_row_by_id(sheet_name, df, id_column, id_value, data_dict):
    """Met à jour une ligne basée sur une valeur d'ID (nécessite une recherche de ligne)."""
    try:
        _, sheets = init_gspread()
        sheet = sheets[sheet_name]
        
        # Recherche de l'index de la ligne dans le DataFrame actuel
        try:
            row_index = df.index[df[id_column] == id_value].tolist()[0]
            # Les indices gspread sont basés sur 1, donc +2 pour la position dans la feuille
            # (1 pour l'en-tête, +1 pour l'index 0)
            sheet_row_num = row_index + 2
        except IndexError:
            st.warning(f"Ligne non trouvée pour l'ID {id_value} dans {sheet_name}.")
            return

        # Création de la ligne de données à mettre à jour (liste de toutes les valeurs)
        updated_row_data = df.loc[row_index].to_dict()
        updated_row_data.update(data_dict)
        
        # Conversion du dictionnaire en liste de valeurs dans l'ordre des colonnes
        # C'est une méthode simplifiée pour Streamlit: on assume l'ordre des colonnes
        headers = sheet.row_values(1)
        values_to_update = [str(updated_row_data.get(h, '')) for h in headers]
        
        # Mise à jour de la ligne complète
        sheet.update(f'A{sheet_row_num}', [values_to_update])
        st.session_state['data_last_update'] = datetime.now()
    except Exception as e:
        st.error(f"Erreur de mise à jour dans Google Sheet ({sheet_name}). Détail: {e}")

# --- 4. LOGIQUE D'AUTHENTIFICATION ET DE GESTION DES SESSIONS ---

def check_login():
    """Vérifie l'état de la connexion et gère la logique de l'utilisateur."""
    
    # 1. Initialisation des états si non présents
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
        st.session_state['user_email'] = None
        st.session_state['user_name'] = None
        st.session_state['user_role'] = None
        st.session_state['global_pause'] = False
        st.session_state['global_pause_start'] = None
        st.session_state['active_task_id'] = None
        st.session_state['task_timer_start'] = None
        st.session_state['task_last_session_id'] = None
        st.session_state['data_last_update'] = datetime.now()
        
    # 2. Si déjà connecté, logiquement on ne fait rien de plus.
    if st.session_state['logged_in']:
        # Vérification et arrêt automatique de la pause globale après 1 heure
        if st.session_state['global_pause'] and st.session_state['global_pause_start']:
            pause_start_dt = datetime.strptime(st.session_state['global_pause_start'], '%Y-%m-%d %H:%M:%S')
            if datetime.now() - pause_start_dt > timedelta(hours=1):
                # Arrêt de la pause globale après 1 heure
                toggle_global_pause(pause_type='auto_stop')
        return

    # 3. Fonction de déconnexion
def logout():
    """Déconnecte l'utilisateur et log l'événement."""
    if st.session_state.get('logged_in'):
        # Log de l'événement de déconnexion
        df_logins = fetch_data('logins')
        last_login_row = df_logins[df_logins['user_email'] == st.session_state['user_email']].tail(1)
        
        if not last_login_row.empty:
            login_id = last_login_row['login_id'].values[0]
            login_at_str = last_login_row['login_at'].values[0]
            
            # Calcul du temps total de connexion
            login_at_dt = datetime.strptime(login_at_str, '%Y-%m-%d %H:%M:%S')
            logout_at_str = format_timestamp()
            total_seconds = (datetime.now() - login_at_dt).total_seconds()
            
            # Mise à jour de la feuille Logins
            update_row_by_id(
                'logins', 
                df_logins, 
                'login_id', 
                login_id, 
                {'logout_at': logout_at_str, 'total_logged_seconds': int(total_seconds)}
            )
        
        # Réinitialisation des états
        st.session_state['logged_in'] = False
        st.session_state['user_email'] = None
        st.session_state['user_name'] = None
        st.session_state['user_role'] = None
        st.rerun()

def login_form():
    """Affiche le formulaire d'authentification et gère la connexion/création de compte."""
    st.markdown('<p class="title-app">SYSTÈME D\'AUTHENTIFICATION BIOMÉTRIQUE V2.0</p>', unsafe_allow_html=True)
    
    with st.form("login_form"):
        email = st.text_input("Adresse Gmail", placeholder="votre.email@gmail.com").strip().lower()
        submitted = st.form_submit_button("Se connecter")

        if submitted:
            if not email:
                st.error("Veuillez entrer une adresse email valide.")
                return

            df_users = fetch_data('users')
            user_data = df_users[df_users['user_email'] == email]
            
            # Simulation d'un utilisateur préexistant (hardcodé)
            pre_existing_user = PRE_EXISTING_ACCOUNTS.get(email)

            if not user_data.empty:
                # CAS 1 : Utilisateur trouvé dans Google Sheets
                st.session_state['user_email'] = email
                st.session_state['user_name'] = user_data['prénom'].values[0]
                st.session_state['user_role'] = user_data['rôle'].values[0]
                st.session_state['logged_in'] = True
                st.success(f"Bienvenue, {st.session_state['user_name']} (Rôle : {st.session_state['user_role']})")
                
                # Log de la connexion
                log_new_login(email)
                st.rerun()

            elif pre_existing_user:
                # CAS 2 : Utilisateur connu dans le code, mais pas encore dans Google Sheets (Première connexion)
                log_new_user(email, pre_existing_user['name'], pre_existing_user['role'])
                
                st.session_state['user_email'] = email
                st.session_state['user_name'] = pre_existing_user['name']
                st.session_state['user_role'] = pre_existing_user['role']
                st.session_state['logged_in'] = True
                st.success(f"Compte préexistant synchronisé. Bienvenue, {st.session_state['user_name']} (Rôle : {st.session_state['user_role']})")

                # Log de la connexion
                log_new_login(email)
                st.rerun()
                
            else:
                # CAS 3 : Nouvel utilisateur, demande du prénom pour la création de compte
                st.warning("Email non reconnu. Veuillez saisir votre prénom pour créer un compte.")
                new_user_name = st.text_input("Votre prénom", key="new_user_name_input")
                
                if st.button("Créer un Compte"):
                    if new_user_name:
                        # Rôle par défaut pour les nouveaux utilisateurs
                        log_new_user(email, new_user_name, 'user')
                        
                        st.session_state['user_email'] = email
                        st.session_state['user_name'] = new_user_name
                        st.session_state['user_role'] = 'user'
                        st.session_state['logged_in'] = True
                        st.success(f"Compte créé et synchronisé. Bienvenue, {new_user_name} (Rôle : user)")

                        # Log de la connexion
                        log_new_login(email)
                        st.rerun()
                    else:
                        st.error("Veuillez saisir votre prénom.")

def log_new_user(email, name, role):
    """Enregistre un nouvel utilisateur dans la feuille Users."""
    new_user_data = [
        email, 
        name, 
        role, 
        format_timestamp()
    ]
    append_row('users', new_user_data)
    
def log_new_login(email):
    """Enregistre un événement de connexion dans la feuille Logins."""
    login_id = 'L' + datetime.now().strftime('%Y%m%d%H%M%S') + str(int(time.time() * 1000) % 1000)
    login_data = [
        login_id,
        email,
        format_timestamp(),
        '', # logout_at
        0   # total_logged_seconds
    ]
    append_row('logins', login_data)

# --- 5. LOGIQUE DE CHRONOMÈTRE ET GESTION DE TÂCHES ---

def toggle_global_pause(pause_type='global'):
    """Active ou désactive la pause globale et gère l'arrêt du chronomètre de tâche."""
    if not st.session_state['logged_in']: return

    df_sessions = fetch_data('sessions')
    
    if not st.session_state['global_pause']:
        # DÉMARRER LA PAUSE GLOBALE
        st.session_state['global_pause'] = True
        st.session_state['global_pause_start'] = format_timestamp()
        
        # Si une tâche est en cours, la mettre en pause automatiquement
        if st.session_state['active_task_id']:
            task_id = st.session_state['active_task_id']
            session_id = st.session_state['task_last_session_id']
            
            # Calculer la durée de la session active
            start_dt = datetime.strptime(st.session_state['task_timer_start'], '%Y-%m-%d %H:%M:%S')
            duration = (datetime.now() - start_dt).total_seconds()
            
            # Mettre à jour la ligne de session (pause_at, duration)
            update_row_by_id(
                'sessions', 
                df_sessions, 
                'session_id', 
                session_id, 
                {'pause_at': st.session_state['global_pause_start'], 'duration_seconds': duration}
            )
            
            # Mettre à jour l'état local de la tâche
            st.session_state['active_task_id'] = None
            st.session_state['task_timer_start'] = None
            st.session_state['task_last_session_id'] = None
        
        st.info("PAUSE GLOBALE ACTIVÉE (max 1 heure). Le chronomètre de tâche a été arrêté.")

        # Log de la session de pause globale (simulée comme une session de tâche)
        pause_session_id = 'P' + datetime.now().strftime('%Y%m%d%H%M%S') + str(int(time.time() * 1000) % 1000)
        pause_data = [
            pause_session_id,
            'GLOBAL_PAUSE',
            st.session_state['user_email'],
            st.session_state['global_pause_start'],
            '', # pause_at
            '', # resume_at
            '', # end_at
            0,  # duration_seconds (sera mise à jour lors de l'arrêt)
            'global'
        ]
        append_row('sessions', pause_data)
        st.session_state['global_pause_session_id'] = pause_session_id
    
    else:
        # ARRÊTER LA PAUSE GLOBALE
        st.session_state['global_pause'] = False
        pause_end_time = format_timestamp()
        
        # Mettre à jour la session de pause globale
        global_pause_session_id = st.session_state.get('global_pause_session_id')
        if global_pause_session_id:
            df_sessions = fetch_data('sessions') # Recharger pour avoir la ligne de pause
            pause_start_dt = datetime.strptime(st.session_state['global_pause_start'], '%Y-%m-%d %H:%M:%S')
            total_duration = (datetime.now() - pause_start_dt).total_seconds()
            
            update_row_by_id(
                'sessions', 
                df_sessions, 
                'session_id', 
                global_pause_session_id, 
                {'end_at': pause_end_time, 'duration_seconds': int(total_duration)}
            )
        
        st.session_state['global_pause_start'] = None
        st.session_state['global_pause_session_id'] = None

        if pause_type != 'auto_stop':
            st.success("PAUSE GLOBALE DÉSACTIVÉE. Vous pouvez reprendre vos tâches.")
        else:
            st.warning("PAUSE GLOBALE ARRÊTÉE AUTOMATIQUEMENT (Limite de 1h atteinte).")
    
    st.rerun()


def start_task(task_id, df_tasks):
    """Démarre le chronomètre pour une tâche."""
    
    if st.session_state['global_pause']:
        st.error("Impossible de commencer la tâche : la PAUSE GLOBALE est activée. Veuillez la désactiver d'abord.")
        return
        
    if st.session_state['active_task_id']:
        st.error(f"Veuillez d'abord mettre en PAUSE la tâche active : {st.session_state['active_task_id']}")
        return
    
    df_sessions = fetch_data('sessions')
    
    # 1. Mettre à jour le statut dans Google Sheets (si 'À faire')
    task_row = df_tasks[df_tasks['task_id'] == task_id].iloc[0].to_dict()
    if task_row['statut'] == 'À faire':
        update_row_by_id('tasks', df_tasks, 'task_id', task_id, {'statut': 'En cours'})

    # 2. Créer une nouvelle ligne dans 'Sessions'
    session_id = 'S' + datetime.now().strftime('%Y%m%d%H%M%S') + str(int(time.time() * 1000) % 1000)
    start_time_str = format_timestamp()
    
    new_session_data = [
        session_id,
        task_id,
        st.session_state['user_email'],
        start_time_str,
        '', # pause_at
        '', # resume_at
        '', # end_at
        0,  # duration_seconds
        'mission' # pause_type
    ]
    append_row('sessions', new_session_data)
    
    # 3. Mettre à jour l'état local
    st.session_state['active_task_id'] = task_id
    st.session_state['task_timer_start'] = start_time_str
    st.session_state['task_last_session_id'] = session_id
    st.toast(f"Tâche {task_id} démarrée !", icon="🚀")
    st.rerun()

def pause_task(task_id, df_tasks):
    """Met en pause le chronomètre de la tâche active."""
    if st.session_state['active_task_id'] != task_id: return
    
    df_sessions = fetch_data('sessions')
    
    # 1. Calculer la durée de la session
    start_dt = datetime.strptime(st.session_state['task_timer_start'], '%Y-%m-%d %H:%M:%S')
    pause_time_str = format_timestamp()
    duration = (datetime.now() - start_dt).total_seconds()
    
    # 2. Mettre à jour la ligne de session (pause_at, duration)
    session_id = st.session_state['task_last_session_id']
    update_row_by_id(
        'sessions', 
        df_sessions, 
        'session_id', 
        session_id, 
        {'pause_at': pause_time_str, 'duration_seconds': int(duration)}
    )
    
    # 3. Mettre à jour l'état local
    st.session_state['active_task_id'] = None
    st.session_state['task_timer_start'] = None
    st.session_state['task_last_session_id'] = None
    st.toast(f"Tâche {task_id} mise en PAUSE.", icon="⏸️")
    st.rerun()

def resume_task(task_id, df_tasks):
    """Reprend le chronomètre pour une tâche mise en pause (crée une nouvelle session)."""
    if st.session_state['active_task_id']:
        st.error(f"Veuillez d'abord mettre en PAUSE la tâche active : {st.session_state['active_task_id']}")
        return
        
    df_sessions = fetch_data('sessions')
    
    # 1. Créer une nouvelle ligne dans 'Sessions' (avec resume_at)
    session_id = 'S' + datetime.now().strftime('%Y%m%d%H%M%S') + str(int(time.time() * 1000) % 1000)
    resume_time_str = format_timestamp()
    
    new_session_data = [
        session_id,
        task_id,
        st.session_state['user_email'],
        resume_time_str, # start_at (est la même que resume_at pour une nouvelle session)
        '', # pause_at
        resume_time_str, # resume_at
        '', # end_at
        0,  # duration_seconds
        'mission'
    ]
    append_row('sessions', new_session_data)
    
    # 2. Mettre à jour l'état local
    st.session_state['active_task_id'] = task_id
    st.session_state['task_timer_start'] = resume_time_str
    st.session_state['task_last_session_id'] = session_id
    st.toast(f"Tâche {task_id} reprise !", icon="▶️")
    st.rerun()

def complete_task(task_id, df_tasks):
    """Termine la tâche : arrête le chrono (si actif) et met à jour le statut."""
    
    # Si la tâche est active, la mettre en pause/terminer la session
    if st.session_state['active_task_id'] == task_id:
        df_sessions = fetch_data('sessions')
        
        start_dt = datetime.strptime(st.session_state['task_timer_start'], '%Y-%m-%d %H:%M:%S')
        end_time_str = format_timestamp()
        duration = (datetime.now() - start_dt).total_seconds()
        
        # Mettre à jour la dernière session (end_at, duration)
        session_id = st.session_state['task_last_session_id']
        update_row_by_id(
            'sessions', 
            df_sessions, 
            'session_id', 
            session_id, 
            {'end_at': end_time_str, 'duration_seconds': int(duration)}
        )
        
        # Réinitialiser l'état local
        st.session_state['active_task_id'] = None
        st.session_state['task_timer_start'] = None
        st.session_state['task_last_session_id'] = None

    # 2. Mettre à jour le statut de la tâche dans 'Tâches' (seulement l'admin peut modifier si 'Terminer')
    task_row = df_tasks[df_tasks['task_id'] == task_id].iloc[0].to_dict()
    is_admin_closing = st.session_state['user_role'] == 'admin'

    if task_row['statut'] == 'Terminer' and not is_admin_closing:
        st.error("Seul un administrateur peut modifier une tâche déjà terminée.")
        return

    # Calculer le temps total (nécessite le Reporting DF pour la somme)
    df_sessions_all = fetch_data('sessions')
    task_sessions = df_sessions_all[
        (df_sessions_all['task_id'] == task_id) & 
        (df_sessions_all['pause_type'] == 'mission')
    ]
    total_time_seconds = task_sessions['duration_seconds'].astype(float).sum()

    # Mise à jour de la tâche
    update_row_by_id(
        'tasks', 
        df_tasks, 
        'task_id', 
        task_id, 
        {
            'statut': 'Terminer', 
            'closed_at': format_timestamp(), 
            'closed_by': st.session_state['user_email'],
            'total_time_seconds': int(total_time_seconds)
        }
    )
    
    st.toast(f"Tâche {task_id} TERMINÉE et verrouillée.", icon="✅")
    st.rerun()
    
# --- 6. INTERFACES UTILISATEUR ---

def display_task_list(df_tasks, df_sessions):
    """Affiche la liste des tâches avec les chronomètres et les actions."""

    st.markdown("## Tâches en Attente et en Cours")
    st.divider()

    # Filtrer les tâches assignées à l'utilisateur ou non terminées
    user_email = st.session_state['user_email']
    
    # Afficher TOUTES les tâches non-terminées ET les tâches terminées qui sont assignées à l'utilisateur
    filtered_tasks = df_tasks[
        (df_tasks['statut'] != 'Terminer') | 
        (df_tasks['assigné_email'] == user_email)
    ].sort_values(by='created_at', ascending=False).reset_index(drop=True)
    
    if filtered_tasks.empty:
        st.info("Aucune tâche à afficher. L'administrateur peut en créer une nouvelle.")
        return

    # Boucle sur les tâches pour l'affichage
    for index, task in filtered_tasks.iterrows():
        task_id = task['task_id']
        current_status = task['statut']
        assigned_to = task['assigné_email']
        
        # Calcul du temps total déjà passé
        total_time_spent = df_sessions[
            (df_sessions['task_id'] == task_id) & 
            (df_sessions['pause_type'] == 'mission')
        ]['duration_seconds'].astype(float).sum()
        
        # Vérification si cette tâche est ACTIVE dans la session de l'utilisateur
        is_active = st.session_state['active_task_id'] == task_id
        
        # Colonnes d'affichage
        col1, col2, col3, col4, col5 = st.columns([1.5, 3, 2, 2, 3])

        with col1:
            st.markdown(f"<span class='status-{current_status.replace(' ', '')}'>**{current_status}**</span>", unsafe_allow_html=True)
            
        with col2:
            st.markdown(f"**{task['titre']}**", help=task['description'])
            st.caption(f"Pour: {assigned_to} | Limite: {task['due_datetime']}")
        
        with col3:
            # Chronomètre Affichage
            display_time = total_time_spent
            if is_active:
                # Ajout du temps de la session en cours
                start_dt = datetime.strptime(st.session_state['task_timer_start'], '%Y-%m-%d %H:%M:%S')
                current_session_duration = (datetime.now() - start_dt).total_seconds()
                display_time += current_session_duration
                st.markdown(f"**EN COURS...** ({seconds_to_hms(display_time)})", unsafe_allow_html=True)
            else:
                st.markdown(f"**Total Passé :** {seconds_to_hms(display_time)}")

        with col4:
            # Boutons Chronomètre
            if current_status == 'Terminer':
                st.markdown("`Terminée le: " + task['closed_at'][:10] + "`")
            elif is_active:
                st.button("⏸️ Pause Mission", key=f"pause_{task_id}", on_click=pause_task, args=(task_id, df_tasks))
            else:
                # Tâche non active
                if current_status == 'En cours':
                    st.button("▶️ Reprendre", key=f"resume_{task_id}", on_click=resume_task, args=(task_id, df_tasks))
                else: # À faire
                    st.button("▶️ Commencer", key=f"start_{task_id}", on_click=start_task, args=(task_id, df_tasks))

        with col5:
            # Bouton Terminer
            if current_status != 'Terminer':
                # La vérification de rôle est faite dans la fonction complete_task
                st.markdown('<div class="end-task-button">', unsafe_allow_html=True)
                st.button("✅ Terminer la Tâche", key=f"complete_{task_id}", on_click=complete_task, args=(task_id, df_tasks))
                st.markdown('</div>', unsafe_allow_html=True)
            elif st.session_state['user_role'] == 'admin':
                st.button("🔄 Modifier (Admin)", key=f"admin_mod_{task_id}")
                # Implémenter la modification pour Admin ici (pourrait ouvrir un modal ou un formulaire)
            st.markdown("---") # Séparateur visuel

def admin_task_management(df_tasks, df_users):
    """Interface pour les admins : Ajout/Modification/Suppression de tâches."""
    st.markdown("### ⚙️ Création de Nouvelle Tâche")
    
    with st.form("new_task_form"):
        title = st.text_input("Titre de la Tâche")
        description = st.text_area("Description")
        
        # Liste des employés (Users dans Google Sheet)
        user_options = df_users['user_email'].unique().tolist()
        assignee = st.selectbox("Assigner à", options=user_options, index=user_options.index(st.session_state['user_email']) if st.session_state['user_email'] in user_options else 0)
        
        col_date, col_time = st.columns(2)
        with col_date:
            due_date = st.date_input("Date Limite", min_value=datetime.now().date())
        with col_time:
            due_time = st.time_input("Heure Limite", value=datetime.now().time())
            
        submitted = st.form_submit_button("Créer la Tâche")

        if submitted:
            if title and description:
                task_id = 'T' + datetime.now().strftime('%Y%m%d%H%M%S')
                due_datetime_str = f"{due_date} {due_time}"
                
                new_task_data = [
                    task_id, 
                    title, 
                    description, 
                    assignee, 
                    format_timestamp(), 
                    due_datetime_str, 
                    'À faire', 
                    0, # total_time_seconds
                    st.session_state['user_email'], 
                    '', # closed_by
                    ''  # closed_at
                ]
                append_row('tasks', new_task_data)
                st.success(f"Tâche {task_id} créée pour {assignee}.")
            else:
                st.error("Veuillez remplir le titre et la description.")

    # Section de suppression de tâche (Admin only)
    st.markdown("### 🗑️ Suppression de Tâche (Admin)")
    task_to_delete = st.selectbox("Sélectionner la Tâche à Supprimer", options=df_tasks['task_id'].tolist())
    
    if st.button("Confirmer la Suppression (IRRÉVERSIBLE)"):
        # *Note technique : gspread ne supporte pas delete_row facilement sans index. 
        # Pour simplifier et éviter la complexité des index gspread, nous allons 
        # SIMULER la suppression en mettant le statut à 'DELETED' dans cette version simple. 
        # Pour une vraie suppression, il faudrait utiliser des fonctions plus complexes.
        update_row_by_id('tasks', df_tasks, 'task_id', task_to_delete, {'statut': 'DELETED'})
        st.success(f"Tâche {task_to_delete} marquée comme supprimée.")
        st.rerun()

def display_reporting(df_tasks, df_sessions, df_logins, df_users):
    """Affiche les métriques de reporting."""
    st.markdown("## Rapport d'Activité Général")
    
    # 1. TEMPS TOTAL PASSÉ PAR TÂCHE
    task_times = df_tasks.copy()
    task_times['total_time_seconds'] = pd.to_numeric(task_times['total_time_seconds'], errors='coerce').fillna(0)
    task_times['Temps Total'] = task_times['total_time_seconds'].apply(seconds_to_hms)
    
    task_report = task_times[['task_id', 'titre', 'assigné_email', 'statut', 'Temps Total', 'closed_at']]
    st.markdown("### 1. Durée de Traitement des Tâches Terminées")
    st.dataframe(
        task_report[task_report['statut'] == 'Terminer'],
        use_container_width=True,
        hide_index=True
    )

    # 2. TEMPS DE CONNEXION PAR UTILISATEUR
    st.markdown("### 2. Temps Total de Connexion (Login → Logout)")
    logins_report = df_logins.copy()
    logins_report['total_logged_seconds'] = pd.to_numeric(logins_report['total_logged_seconds'], errors='coerce').fillna(0)
    
    user_login_summary = logins_report.groupby('user_email')['total_logged_seconds'].sum().reset_index()
    user_login_summary['Temps Connecté Total'] = user_login_summary['total_logged_seconds'].apply(seconds_to_hms)
    
    # Jointure pour afficher le prénom/rôle
    user_map = df_users.set_index('user_email')[['prénom', 'rôle']].to_dict('index')
    user_login_summary['Prénom'] = user_login_summary['user_email'].apply(lambda x: user_map.get(x, {}).get('prénom', x))
    
    st.dataframe(
        user_login_summary[['Prénom', 'user_email', 'Temps Connecté Total']],
        use_container_width=True,
        hide_index=True
    )
    
    # 3. TEMPS DE PAUSE
    st.markdown("### 3. Temps Total de Pause (Mission vs. Global)")
    
    pause_sessions = df_sessions[df_sessions['pause_at'] != '']
    pause_sessions['duration_seconds'] = pd.to_numeric(pause_sessions['duration_seconds'], errors='coerce').fillna(0)
    
    # Calcul des pauses mission (bouton pause dans la tâche)
    mission_pauses = pause_sessions[pause_sessions['pause_type'] == 'mission']
    mission_pause_summary = mission_pauses.groupby('user_email')['duration_seconds'].sum().reset_index()
    mission_pause_summary['Type'] = 'Mission'
    
    # Calcul des pauses globales (bouton général)
    global_pauses = pause_sessions[pause_sessions['pause_type'] == 'global']
    global_pause_summary = global_pauses.groupby('user_email')['duration_seconds'].sum().reset_index()
    global_pause_summary['Type'] = 'Globale'
    
    combined_pauses = pd.concat([mission_pause_summary, global_pause_summary])
    
    # Ajout du nom d'utilisateur
    combined_pauses['Prénom'] = combined_pauses['user_email'].apply(lambda x: user_map.get(x, {}).get('prénom', x))
    combined_pauses['Durée Totale'] = combined_pauses['duration_seconds'].apply(seconds_to_hms)
    
    st.dataframe(
        combined_pauses[['Prénom', 'user_email', 'Type', 'Durée Totale']],
        use_container_width=True,
        hide_index=True
    )


# --- 7. APPLICATION PRINCIPALE (Structure de Streamlit) ---

def main_app():
    """Fonction principale de l'application connectée."""
    
    # Chargement du design
    load_high_tech_css()
    
    st.markdown('<div class="title-app">ANDIHOO TIME TRACKER</div>', unsafe_allow_html=True)
    
    # Vérification et Affichage du formulaire de connexion si non connecté
    check_login()
    if not st.session_state['logged_in']:
        login_form()
        return

    # Barre de statut (Déconnexion, Pause Globale)
    with st.container():
        col_status, col_pause, col_logout = st.columns([3, 2, 1])
        
        with col_status:
            st.markdown(f"**Connecté :** {st.session_state['user_name']} ({st.session_state['user_role']})")
            
        with col_pause:
            # Bouton de Pause Globale
            pause_label = "▶️ Reprendre le Travail" if st.session_state['global_pause'] else "⏸️ Pause Globale (1h max)"
            st.button(pause_label, on_click=toggle_global_pause, key="global_pause_btn", use_container_width=True)

        with col_logout:
            st.button("🔴 Déconnexion", on_click=logout, key="logout_btn", use_container_width=True)

    st.markdown("---")
    
    # Rechargement des données (déclenché après chaque action d'écriture)
    df_tasks = fetch_data('tasks')
    df_sessions = fetch_data('sessions')
    df_users = fetch_data('users')
    df_logins = fetch_data('logins')

    # Affichage des Onglets
    tab1, tab2, tab3 = st.tabs(["📋 Tâches", "📈 Reporting", "👥 Administration"])

    with tab1:
        display_task_list(df_tasks, df_sessions)

    with tab2:
        display_reporting(df_tasks, df_sessions, df_logins, df_users)
        
    with tab3:
        if st.session_state['user_role'] == 'admin':
            admin_task_management(df_tasks, df_users)
        else:
            st.warning("Accès Administrateur requis pour cette section.")

    # Actualisation automatique du chronomètre (à mettre à jour toutes les 1s)
    if st.session_state['active_task_id']:
        time.sleep(1)
        st.rerun()

# Lancement de l'application
if __name__ == "__main__":
    main_app()




