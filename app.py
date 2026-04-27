"""
Main entry point for the Suivi de Dépenses – Budget Personnel app.
With authentication system.
"""

import streamlit as st
from data.auth import (
    authenticate, register_user, validate_session, logout, user_exists,
    change_password, get_user_preferences, save_user_preferences,
    mark_notifications_read,
)
from utils.notifications import generate_notifications, get_unread_count, get_notifications
from utils.email_service import send_weekly_report, should_send_weekly_report

st.set_page_config(
    page_title="Suivi de Dépenses",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Initialize session state ──────────────────────────────────────────────────
if "session_token" not in st.session_state:
    st.session_state.session_token = None
if "username" not in st.session_state:
    st.session_state.username = None

# ── Global warm blue/grey theme injected via CSS ──────────────────────────────
st.markdown(
    """
    <style>
    /* ── Base colours ── */
    :root {
        --blue-dark:   #1B3A5C;
        --blue-mid:    #2E6DA4;
        --blue-light:  #5B9BD5;
        --grey-dark:   #3D4B5C;
        --grey-mid:    #7A8C9E;
        --grey-light:  #C8D4DF;
        --warm-white:  #F4F7FB;
        --accent:      #F0A500;
        --green:       #2ECC71;
        --red:         #E74C3C;
    }

    /* ── App background ── */
    .stApp {
        background-color: var(--warm-white);
    }

    /* ── Sidebar ── */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, var(--blue-dark) 0%, var(--blue-mid) 100%);
    }
    section[data-testid="stSidebar"] * {
        color: #FFFFFF !important;
    }
    section[data-testid="stSidebar"] .stRadio > label {
        color: #FFFFFF !important;
    }

    /* ── Page title ── */
    h1 {
        color: var(--blue-dark);
        font-weight: 700;
    }
    h2, h3 {
        color: var(--blue-mid);
    }

    /* ── Metric cards ── */
    div[data-testid="metric-container"] {
        background: #FFFFFF;
        border: 1px solid var(--grey-light);
        border-radius: 12px;
        padding: 16px 20px;
        box-shadow: 0 2px 8px rgba(27,58,92,0.08);
    }
    div[data-testid="metric-container"] label {
        color: var(--grey-mid) !important;
        font-size: 0.82rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    div[data-testid="metric-container"] [data-testid="stMetricValue"] {
        color: var(--blue-dark) !important;
        font-size: 1.7rem !important;
        font-weight: 700 !important;
    }

    /* ── Buttons ── */
    .stButton > button {
        background-color: var(--blue-mid);
        color: #FFFFFF;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        padding: 0.45rem 1.2rem;
        transition: background 0.2s;
    }
    .stButton > button:hover {
        background-color: var(--blue-dark);
        color: #FFFFFF;
    }

    /* ── Tabs ── */
    .stTabs [data-baseweb="tab"] {
        color: var(--grey-dark);
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        color: var(--blue-mid) !important;
        border-bottom: 3px solid var(--blue-mid) !important;
    }

    /* ── Dataframe ── */
    .stDataFrame {
        border-radius: 10px;
        overflow: hidden;
    }

    /* ── Divider ── */
    hr {
        border-color: var(--grey-light);
    }
    
    /* ── Login card ── */
    .login-card {
        background: white;
        padding: 2rem;
        border-radius: 16px;
        box-shadow: 0 4px 20px rgba(27,58,92,0.12);
        max-width: 400px;
        margin: 2rem auto;
    }
    .login-header {
        text-align: center;
        margin-bottom: 1.5rem;
    }
    .login-header h2 {
        color: var(--blue-dark);
        margin: 0.5rem 0;
    }
    .login-header p {
        color: var(--grey-mid);
        font-size: 0.9rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def show_login_page():
    """Display the login/register page."""
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown(
            """
            <div class="login-header">
                <span style="font-size:4rem;">💰</span>
                <h2>Suivi de Dépenses</h2>
                <p>Budget Personnel</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        
        # Check if first user (for onboarding)
        has_users = user_exists()
        
        if not has_users:
            st.info("👋 Bienvenue ! Créez votre compte pour commencer.")
        
        tab_login, tab_register = st.tabs(["🔐 Connexion", "📝 Inscription"])
        
        with tab_login:
            with st.form("login_form"):
                username = st.text_input("👤 Nom d'utilisateur", key="login_username")
                password = st.text_input("🔑 Mot de passe", type="password", key="login_password")
                submitted = st.form_submit_button("Se connecter", use_container_width=True)
                
                if submitted:
                    if not username or not password:
                        st.error("Veuillez remplir tous les champs.")
                    else:
                        success, result = authenticate(username, password)
                        if success:
                            st.session_state.session_token = result
                            st.session_state.username = username
                            st.success("✅ Connexion réussie !")
                            st.rerun()
                        else:
                            st.error(result)
        
        with tab_register:
            with st.form("register_form"):
                new_username = st.text_input("👤 Nom d'utilisateur", key="reg_username")
                new_email = st.text_input("📧 Email (optionnel)", key="reg_email")
                new_password = st.text_input("🔑 Mot de passe", type="password", key="reg_password")
                confirm_password = st.text_input("🔑 Confirmer le mot de passe", type="password", key="reg_confirm")
                new_api_key = st.text_input(
                    "🤖 Clé API Anthropic (optionnel)",
                    type="password",
                    key="reg_api_key",
                    help="Nécessaire pour utiliser l'assistant IA. Vous pouvez la configurer plus tard.",
                )
                submitted = st.form_submit_button("Créer un compte", use_container_width=True)
                
                if submitted:
                    if not new_username or not new_password:
                        st.error("Veuillez remplir le nom d'utilisateur et le mot de passe.")
                    elif new_password != confirm_password:
                        st.error("Les mots de passe ne correspondent pas.")
                    else:
                        success, message = register_user(new_username, new_password, new_email, new_api_key)
                        if success:
                            st.success(message)
                        else:
                            st.error(message)


def show_authenticated_home():
    """Display the home page for authenticated users."""
    username = st.session_state.username

    # ── Auto-generate notifications on load ───────────────────────────────────
    if not st.session_state.get("notifications_generated"):
        generate_notifications(username)
        st.session_state["notifications_generated"] = True

    # ── Auto-send weekly report if due (silent, non-blocking) ────────────────
    if should_send_weekly_report(username):
        try:
            send_weekly_report(username)
        except Exception:  # noqa: BLE001
            pass  # Failures are silent on auto-send; user can retry manually

    # ── Sidebar ───────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown(
            f"""
            <div style="text-align:center; padding: 1rem 0 0.5rem;">
                <span style="font-size:2.4rem;">💰</span>
                <h2 style="margin:0; font-size:1.15rem; font-weight:700;">
                    Suivi de Dépenses
                </h2>
                <p style="font-size:0.75rem; opacity:0.75; margin:0;">Budget Personnel</p>
            </div>
            <hr style="border-color:rgba(255,255,255,0.25); margin: 0.5rem 0 1rem;" />
            <div style="text-align:center; padding: 0.5rem;">
                <p style="margin:0; font-size:0.85rem;">👤 Connecté en tant que</p>
                <p style="margin:0; font-weight:700;">{username}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("---")

        # ── 🤖 AI Configuration ───────────────────────────────────────────────
        prefs = get_user_preferences(username)
        with st.expander("🤖 Configuration IA"):
            ai_key = st.text_input(
                "Clé API Anthropic",
                value=prefs.get("anthropic_api_key", ""),
                type="password",
                key="sidebar_api_key",
            )
            ai_model = st.selectbox(
                "Modèle",
                options=[
                    "claude-3-haiku-20240307",
                    "claude-3-sonnet-20240229",
                    "claude-3-opus-20240229",
                ],
                index=[
                    "claude-3-haiku-20240307",
                    "claude-3-sonnet-20240229",
                    "claude-3-opus-20240229",
                ].index(prefs.get("anthropic_model", "claude-3-haiku-20240307")),
                key="sidebar_ai_model",
            )
            if st.button("💾 Sauvegarder IA", key="save_ai_config"):
                prefs["anthropic_api_key"] = ai_key
                prefs["anthropic_model"] = ai_model
                save_user_preferences(username, prefs)
                st.success("✅ Configuration IA sauvegardée.")

        # ── 🔔 Notifications ──────────────────────────────────────────────────
        unread = get_unread_count(username)
        notif_label = f"🔔 Notifications ({unread} non lues)" if unread else "🔔 Notifications"
        with st.expander(notif_label):
            notifications = get_notifications(username)
            read_ids = set(prefs.get("notifications_read", []))
            if not notifications:
                st.info("Aucune notification.")
            else:
                for notif in notifications[:5]:
                    is_read = notif["id"] in read_ids
                    opacity = "0.6" if is_read else "1"
                    st.markdown(
                        f'<div style="opacity:{opacity}; margin-bottom:8px;">'
                        f'<strong>{notif["title"]}</strong><br/>'
                        f'<span style="font-size:0.85rem;">{notif["message"]}</span>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
            if notifications:
                if st.button("✅ Tout marquer comme lu", key="mark_read_btn"):
                    mark_notifications_read(username)
                    st.rerun()
            if st.button("🔄 Rafraîchir", key="refresh_notifs_btn"):
                generate_notifications(username)
                st.rerun()

        # ── 📧 Email reports ──────────────────────────────────────────────────
        with st.expander("📧 Rapports par email"):
            email_enabled = st.toggle(
                "Activer les rapports hebdomadaires",
                value=prefs.get("email_reports_enabled", False),
                key="email_toggle",
            )
            if email_enabled:
                smtp_cfg = prefs.get("smtp_config") or {}
                smtp_server = st.text_input("Serveur SMTP", value=smtp_cfg.get("server", "smtp.gmail.com"), key="smtp_server")
                smtp_port = st.number_input("Port SMTP", value=int(smtp_cfg.get("port", 587)), min_value=1, max_value=65535, key="smtp_port")
                smtp_email = st.text_input("Email expéditeur", value=smtp_cfg.get("email", ""), key="smtp_email")
                smtp_password = st.text_input("Mot de passe SMTP", value=smtp_cfg.get("password", ""), type="password", key="smtp_password")
                if st.button("💾 Sauvegarder SMTP", key="save_smtp_btn"):
                    prefs["email_reports_enabled"] = True
                    prefs["smtp_config"] = {
                        "server": smtp_server,
                        "port": smtp_port,
                        "email": smtp_email,
                        "password": smtp_password,
                    }
                    save_user_preferences(username, prefs)
                    st.success("✅ Configuration email sauvegardée.")
                if st.button("📤 Envoyer maintenant", key="send_report_btn"):
                    ok, msg = send_weekly_report(username)
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)
            else:
                if prefs.get("email_reports_enabled", False):
                    prefs["email_reports_enabled"] = False
                    save_user_preferences(username, prefs)

        st.markdown("---")

        # Logout button
        if st.button("🚪 Déconnexion", use_container_width=True):
            logout(st.session_state.session_token)
            st.session_state.session_token = None
            st.session_state.username = None
            st.session_state.notifications_generated = False
            st.rerun()

        # Change password
        with st.expander("🔐 Changer le mot de passe"):
            old_pwd = st.text_input("Ancien mot de passe", type="password", key="old_pwd")
            new_pwd = st.text_input("Nouveau mot de passe", type="password", key="new_pwd")
            confirm_pwd = st.text_input("Confirmer", type="password", key="confirm_pwd")
            if st.button("Modifier", key="change_pwd_btn"):
                if new_pwd != confirm_pwd:
                    st.error("Les mots de passe ne correspondent pas.")
                else:
                    success, msg = change_password(username, old_pwd, new_pwd)
                    if success:
                        st.success(msg)
                    else:
                        st.error(msg)

    # Main content
    st.title("💰 Suivi de Dépenses – Budget Personnel")
    st.markdown(
        f"""
        Bienvenue **{username}** dans votre application de gestion de budget personnel.

        Utilisez le menu de navigation sur la gauche pour accéder aux pages.
        """,
        unsafe_allow_html=True,
    )
    
    # Quick stats preview
    st.markdown("---")
    st.subheader("🚀 Accès rapide")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            """
            <div style="background:white; padding:1.5rem; border-radius:12px; text-align:center; 
                        box-shadow: 0 2px 8px rgba(27,58,92,0.08);">
                <span style="font-size:2rem;">📊</span>
                <h4 style="margin:0.5rem 0;">Dashboard</h4>
                <p style="color:#7A8C9E; font-size:0.85rem;">Voir les KPIs et graphiques</p>
            </div>
            """,
            unsafe_allow_html=True
        )
    with col2:
        st.markdown(
            """
            <div style="background:white; padding:1.5rem; border-radius:12px; text-align:center;
                        box-shadow: 0 2px 8px rgba(27,58,92,0.08);">
                <span style="font-size:2rem;">➕</span>
                <h4 style="margin:0.5rem 0;">Nouvelle transaction</h4>
                <p style="color:#7A8C9E; font-size:0.85rem;">Ajouter une dépense ou revenu</p>
            </div>
            """,
            unsafe_allow_html=True
        )
    with col3:
        st.markdown(
            """
            <div style="background:white; padding:1.5rem; border-radius:12px; text-align:center;
                        box-shadow: 0 2px 8px rgba(27,58,92,0.08);">
                <span style="font-size:2rem;">📄</span>
                <h4 style="margin:0.5rem 0;">Exporter</h4>
                <p style="color:#7A8C9E; font-size:0.85rem;">Générer un rapport PDF/Excel</p>
            </div>
            """,
            unsafe_allow_html=True
        )


# ── Main logic ────────────────────────────────────────────────────────────────
# Check if user is authenticated
if st.session_state.session_token:
    valid, username = validate_session(st.session_state.session_token)
    if valid:
        st.session_state.username = username
        show_authenticated_home()
    else:
        st.session_state.session_token = None
        st.session_state.username = None
        show_login_page()
else:
    show_login_page()
