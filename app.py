import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json
import os
import hashlib # Pour hacher les mots de passe (sécurité de base)

# --- 1. CONFIGURATION, CONSTANTES ET STYLE --
# Le code Streamlit est exécuté de haut en bas à chaque interaction, 
# d'où l'importance de l'initialisation de st.session_state

st.set_page_config(
    page_title="Andihoo Time Tracker - High Tech",
    page_icon="⏱️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Constantes et Mots de Passe (Simulation de DB)
GENERIC_PASSWORD = "Andihoo2025"
ADMIN_EMAIL = "steve.andihoo@gmail.com"

# Structure utilisateur initiale avec mot de passe générique haché temporairement
def hash_password(password):
    """Simple hachage pour la simulation en mémoire."""
    return hashlib.sha256(password.encode()).hexdigest()

INITIAL_USER_CREDENTIALS = {
    ADMIN_EMAIL: {"name": "Steve Antonio", "role": "admin", "password_hash": hash_password(GENERIC_PASSWORD), "needs_pw_change": True},
    "hire.andihoo@gmail.com": {"name": "Sandy Finaritra", "role": "user", "password_hash": hash_password(GENERIC_PASSWORD), "needs_pw_change": True},
    "acommercial757@gmail.com": {"name": "Andrianavalona", "role": "user", "password_hash": hash_password(GENERIC_PASSWORD), "needs_pw_change": True},
    "assistante.andihoo@gmail.com": {"name": "Kanto Mbolatiana", "role": "user", "password_hash": hash_password(GENERIC_PASSWORD), "needs_pw_change": True},
    "teamandihoo@gmail.com": {"name": "Team Andihoo", "role": "user", "password_hash": hash_password(GENERIC_PASSWORD), "needs_pw_change": True},
}

# Injection de style pour des couleurs plus douces mais vives
# Couleurs: #3E8EDE (Bleu Vibrant), #E6F3FF (Arrière-plan léger), #1E5088 (Texte foncé)
st.markdown("""
<style>
    /* Couleur de fond plus douce et texte plus foncé */
    .stApp {
        background-color: #E6F3FF; 
        color: #1E5088;
    }
    
    /* Boutons et Accents Vifs */
    .stButton>button, .stDownloadButton>button {
        background-color: #3E8EDE; /* Bleu Vibrant */
        color: white !important;
        border-radius: 8px;
        border: 1px solid #1E5088;
        transition: background-color 0.3s;
    }
    .stButton>button:hover {
        background-color: #5AA1E2;
        border: 1px solid #1E5088;
    }
    
    /* Inputs et Saisie */
    .stTextInput>div>div>input, .stSelectbox>div>div {
        border-radius: 8px;
        border: 1px solid #CCCCCC;
        background-color: white;
    }
    
    /* Titres et en-têtes */
    h1, h2, h3 {
        color: #1E5088;
    }
    
    /* Barres de progression (vibrant) */
    .stProgress > div > div > div > div {
        background-color: #FF6B6B; /* Rouge Corail */
    }
    
    /* Conteneurs et cartes */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    .css-1r65dft { /* Conteneur de la barre latérale */
        background-color: #E6F3FF; 
    }
</style>
""", unsafe_allow_html=True)


# --- 2. INITIALISATION DU STATE ET DONNÉES (Simulation de DB en mémoire) ---

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'user_email' not in st.session_state:
    st.session_state['user_email'] = None
if 'user_role' not in st.session_state:
    st.session_state['user_role'] = None
if 'user_name' not in st.session_state:
    st.session_state['user_name'] = None
if 'global_pause' not in st.session_state:
    st.session_state['global_pause'] = False
if 'active_task' not in st.session_state:
    st.session_state['active_task'] = None
if 'users' not in st.session_state:
    st.session_state['users'] = INITIAL_USER_CREDENTIALS
if 'needs_pw_change' not in st.session_state:
    st.session_state['needs_pw_change'] = False


# Simulation de la base de données (tâches, sessions, etc.)
# Dans une application réelle, ces fonctions feraient des appels Firestore/gspread
def get_dummy_data():
    """Crée des données factices pour simuler les collections tasks et sessions."""
    
    # Données des Tâches
    tasks_data = [
        {'id': 1, 'task_name': 'Développement Front-end', 'category': 'Dev', 'status': 'To Do'},
        {'id': 2, 'task_name': 'Réunion client B', 'category': 'Commercial', 'status': 'In Progress'},
        {'id': 3, 'task_name': 'Rédaction de la doc technique', 'category': 'R&D', 'status': 'Done'},
    ]
    df_tasks = pd.DataFrame(tasks_data)
    
    # Données des Sessions (simule des sessions de travail)
    sessions_data = [
        {'task_id': 2, 'user_email': 'hire.andihoo@gmail.com', 'start_time': datetime.now() - timedelta(hours=3), 'end_time': datetime.now() - timedelta(hours=2)},
        {'task_id': 1, 'user_email': ADMIN_EMAIL, 'start_time': datetime.now() - timedelta(minutes=30), 'end_time': None}, # Tâche active
    ]
    df_sessions = pd.DataFrame(sessions_data)
    
    # Simuler les utilisateurs
    df_users = pd.DataFrame(st.session_state['users']).T.reset_index().rename(columns={'index': 'email'})
    df_users['name'] = df_users['name'].apply(lambda x: x if x else 'N/A')
    
    # Données de Connexion (pour le Reporting, simulé)
    df_logins = pd.DataFrame([
        {'user_email': ADMIN_EMAIL, 'timestamp': datetime.now() - timedelta(days=1)},
        {'user_email': 'hire.andihoo@gmail.com', 'timestamp': datetime.now() - timedelta(hours=5)},
    ])
    
    return df_tasks, df_sessions, df_users, df_logins

# Récupération des données (Simulation)
def fetch_data(collection_name):
    df_tasks, df_sessions, df_users, df_logins = get_dummy_data()
    if collection_name == 'tasks':
        return df_tasks
    elif collection_name == 'sessions':
        return df_sessions
    elif collection_name == 'users':
        return df_users
    elif collection_name == 'logins':
        return df_logins
    return pd.DataFrame() # Retourne un DataFrame vide par défaut


# --- 3. FONCTIONS D'AUTHENTIFICATION ET DE GESTION DE L'ÉTAT ---

def login(email, password):
    """Vérifie les identifiants et met à jour l'état de la session."""
    user_creds = st.session_state['users'].get(email)
    
    if not user_creds:
        st.error("Email ou mot de passe incorrect.")
        return
        
    # Vérification du mot de passe
    if hash_password(password) == user_creds['password_hash']:
        st.session_state['logged_in'] = True
        st.session_state['user_email'] = email
        st.session_state['user_name'] = user_creds['name']
        st.session_state['user_role'] = user_creds['role']
        st.session_state['needs_pw_change'] = user_creds['needs_pw_change']
        st.success(f"Bienvenue, {user_creds['name']}!")
        # Marquer l'utilisateur comme ayant changé son mot de passe initialement pour la session courante
        if password == GENERIC_PASSWORD:
             st.session_state['needs_pw_change'] = True
        else:
             st.session_state['needs_pw_change'] = False
             
        st.rerun()
    else:
        st.error("Email ou mot de passe incorrect.")

def logout():
    """Déconnecte l'utilisateur."""
    st.session_state['logged_in'] = False
    st.session_state['user_email'] = None
    st.session_state['user_role'] = None
    st.session_state['user_name'] = None
    st.session_state['active_task'] = None
    st.session_state['needs_pw_change'] = False
    st.session_state['global_pause'] = False
    st.rerun()

def process_password_change(old_password, new_password, confirm_password):
    """Gère le changement de mot de passe."""
    user_email = st.session_state['user_email']
    user_data = st.session_state['users'].get(user_email)

    if not user_data:
        st.error("Erreur de session. Veuillez vous reconnecter.")
        logout()
        return

    # 1. Vérifier l'ancien mot de passe
    if hash_password(old_password) != user_data['password_hash']:
        st.error("L'ancien mot de passe est incorrect.")
        return

    # 2. Vérifier la confirmation du nouveau mot de passe
    if new_password != confirm_password:
        st.error("Le nouveau mot de passe et sa confirmation ne correspondent pas.")
        return

    # 3. Vérifier les critères de complexité (Simple)
    if len(new_password) < 8 or not any(c.isupper() for c in new_password) or not any(c.islower() for c in new_password) or not any(c.isdigit() for c in new_password):
        st.error("Le mot de passe doit contenir au moins 8 caractères, dont une majuscule, une minuscule et un chiffre.")
        return

    # 4. Mise à jour du mot de passe (Simulation)
    user_data['password_hash'] = hash_password(new_password)
    user_data['needs_pw_change'] = False
    st.session_state['users'][user_email] = user_data
    st.session_state['needs_pw_change'] = False # Mettre à jour l'état de la session

    st.success("Félicitations ! Votre mot de passe a été mis à jour. Vous pouvez maintenant accéder à l'application.")
    st.rerun()


# --- 4. FONCTIONS DE GESTION DES TÂCHES ET DE L'INTERFACE UTILISATEUR ---

def toggle_global_pause():
    """Active/Désactive la pause globale."""
    st.session_state['global_pause'] = not st.session_state['global_pause']
    if st.session_state['global_pause']:
        st.toast("⏸️ Pause Globale Activée ! Reprise dans 1h max.")
        # Arrêter la tâche active (si applicable) - Logique simplifiée
        if st.session_state['active_task']:
            st.session_state['active_task'] = None
    else:
        st.toast("▶️ Reprise du Travail ! Pensez à relancer votre tâche.")
        
# --- Fonctions d'affichage simplifiées pour la démo ---
def display_task_list(df_tasks, df_sessions):
    st.header("📋 Liste des Tâches")
    st.info("Affichage simplifié des tâches. Les fonctionnalités de démarrage/arrêt ne sont pas incluses dans cette démo.")
    st.dataframe(df_tasks, use_container_width=True)

def display_reporting(df_tasks, df_sessions, df_logins, df_users):
    st.header("📈 Reporting Simplifié")
    total_time = len(df_sessions) * 60 # 60 minutes par ligne pour la démo
    st.metric("Temps Total Traqué (Min. estimé)", f"{total_time:,} min")
    
    st.subheader("Utilisateurs")
    st.dataframe(df_users[['email', 'name', 'role']], use_container_width=True)

def admin_task_management(df_tasks, df_users):
    st.header("👥 Administration")
    st.info("Gestion simplifiée des utilisateurs et des tâches (Admin uniquement).")
    st.dataframe(df_users[['email', 'name', 'role', 'needs_pw_change']], use_container_width=True)


# --- 5. LOGIQUE D'AFFICHAGE PRINCIPALE ---

# --- Écran de Changement de Mot de Passe ---
if st.session_state['logged_in'] and st.session_state['needs_pw_change']:
    st.title("🚨 Changement de Mot de Passe Obligatoire")
    st.warning("Pour votre sécurité, vous devez changer le mot de passe générique avant d'accéder à l'application.")

    with st.form("password_change_form"):
        old_password = st.text_input("Ancien Mot de Passe", type="password")
        new_password = st.text_input("Nouveau Mot de Passe (8+ chars, Maj/Min/Chiffre)", type="password")
        confirm_password = st.text_input("Confirmer le Nouveau Mot de Passe", type="password")
        
        submitted = st.form_submit_button("Changer le Mot de Passe et Accéder")
        
        if submitted:
            process_password_change(old_password, new_password, confirm_password)

    st.button("🔴 Déconnexion", on_click=logout)

# --- Écran de Connexion ---
elif not st.session_state['logged_in']:
    col_logo, col_login = st.columns([1, 2])
    
    with col_logo:
        st.image("https://placehold.co/100x100/3E8EDE/FFFFFF?text=Logo", width=150)
        st.markdown("## Andihoo Time Tracker")
        st.markdown("Application de suivi du temps de travail.")

    with col_login:
        st.title("🔑 Connexion Requise")
        
        with st.form("login_form"):
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Mot de Passe", type="password", key="login_password")
            
            submitted = st.form_submit_button("Se Connecter")
            
            if submitted:
                # La fonction login() gère la validation et le reroute
                login(email, password)

# --- Écran Principal de l'Application ---
else:
    # Header de l'application
    col_info, col_pause, col_logout = st.columns([4, 1.5, 1])

    with col_info:
        st.header("⏱️ Tableau de Bord Andihoo")
        st.markdown(f"**Connecté en tant que:** {st.session_state['user_name']} ({st.session_state['user_role']})")
        
    with col_pause:
        # Bouton de Pause Globale
        pause_label = "▶️ Reprendre le Travail" if st.session_state['global_pause'] else "⏸️ Pause Globale"
        st.button(pause_label, on_click=toggle_global_pause, key="global_pause_btn", use_container_width=True)

    with col_logout:
        st.button("🔴 Déconnexion", on_click=logout, key="logout_btn", use_container_width=True)

    st.markdown("---")
    
    # Rechargement des données (Simulation)
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
            st.warning("Accès restreint. Seuls les administrateurs peuvent accéder à cette section.")

# --- Note importante pour l'utilisateur sur la persistance ---
st.sidebar.caption("⚠️ NOTE IMPORTANTE:")
st.sidebar.info("""
Ce code simule les mots de passe et les données en mémoire (st.session_state). 

**Les changements de mot de passe ne sont PAS persistants** et seront réinitialisés après le redémarrage de l'application.

Pour une application réelle, il est **obligatoire** d'utiliser une base de données persistante (comme **Firebase Firestore**) pour stocker les mots de passe hachés de manière sécurisée et les états d'utilisateur (`needs_pw_change`).
""")
