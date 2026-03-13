"""
Shared components and utilities for the application.
Includes authentication checks, alerts, and common UI elements.
"""

import streamlit as st
from data.auth import validate_session, logout, get_user_preferences, save_user_preferences


def check_authentication():
    """
    Check if user is authenticated.
    If not, redirect to login page.
    Returns username if authenticated, None otherwise.
    """
    if "session_token" not in st.session_state or not st.session_state.session_token:
        st.warning("🔐 Veuillez vous connecter pour accéder à cette page.")
        st.page_link("app.py", label="➡️ Aller à la page de connexion", icon="🏠")
        st.stop()
        return None
    
    valid, result = validate_session(st.session_state.session_token)
    if not valid:
        st.session_state.session_token = None
        st.warning(f"🔐 {result}")
        st.page_link("app.py", label="➡️ Aller à la page de connexion", icon="🏠")
        st.stop()
        return None
    
    return result


def show_user_menu(username: str):
    """Display user menu in sidebar."""
    with st.sidebar:
        st.markdown("---")
        st.markdown(f"👤 **{username}**")
        if st.button("🚪 Déconnexion", key="logout_btn"):
            logout(st.session_state.session_token)
            st.session_state.session_token = None
            st.rerun()


def get_alert_style():
    """Return CSS for alert styling."""
    return """
    <style>
    .alert-warning {
        background: linear-gradient(135deg, #FFF3CD 0%, #FFE6A5 100%);
        border: 1px solid #F0A500;
        border-left: 4px solid #F0A500;
        border-radius: 8px;
        padding: 12px 16px;
        margin: 8px 0;
    }
    .alert-danger {
        background: linear-gradient(135deg, #F8D7DA 0%, #F5C6CB 100%);
        border: 1px solid #E74C3C;
        border-left: 4px solid #E74C3C;
        border-radius: 8px;
        padding: 12px 16px;
        margin: 8px 0;
    }
    .alert-success {
        background: linear-gradient(135deg, #D4EDDA 0%, #C3E6CB 100%);
        border: 1px solid #2ECC71;
        border-left: 4px solid #2ECC71;
        border-radius: 8px;
        padding: 12px 16px;
        margin: 8px 0;
    }
    .alert-info {
        background: linear-gradient(135deg, #D1ECF1 0%, #BEE5EB 100%);
        border: 1px solid #5B9BD5;
        border-left: 4px solid #5B9BD5;
        border-radius: 8px;
        padding: 12px 16px;
        margin: 8px 0;
    }
    .alert-title {
        font-weight: 700;
        margin-bottom: 4px;
    }
    .alert-body {
        font-size: 0.9rem;
    }
    </style>
    """


def show_alert(title: str, message: str, alert_type: str = "info"):
    """Display a styled alert."""
    st.markdown(get_alert_style(), unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="alert-{alert_type}">
            <div class="alert-title">{title}</div>
            <div class="alert-body">{message}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


def format_currency(amount: float, currency: str = "FCFA") -> str:
    """Format a number as currency."""
    return f"{amount:,.0f} {currency}"


def get_shared_css():
    """Return the shared CSS for all pages."""
    return """
    <style>
    :root {
        --blue-dark:  #1B3A5C;
        --blue-mid:   #2E6DA4;
        --blue-light: #5B9BD5;
        --grey-mid:   #7A8C9E;
        --grey-light: #C8D4DF;
        --warm-white: #F4F7FB;
        --green:      #2ECC71;
        --red:        #E74C3C;
        --accent:     #F0A500;
    }
    .stApp { background-color: var(--warm-white); }
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1B3A5C 0%, #2E6DA4 100%);
    }
    section[data-testid="stSidebar"] * { color: #FFFFFF !important; }
    h1 { color: var(--blue-dark); font-weight: 700; }
    h2, h3 { color: var(--blue-mid); }
    div[data-testid="metric-container"] {
        background: #FFFFFF;
        border: 1px solid var(--grey-light);
        border-radius: 12px;
        padding: 16px 20px;
        box-shadow: 0 2px 8px rgba(27,58,92,0.08);
    }
    div[data-testid="metric-container"] label { color: var(--grey-mid) !important; }
    div[data-testid="metric-container"] [data-testid="stMetricValue"] {
        color: var(--blue-dark) !important; font-weight: 700 !important;
    }
    .stButton > button {
        background-color: var(--blue-mid); color: #FFF;
        border: none; border-radius: 8px; font-weight: 600;
    }
    .stButton > button:hover { background-color: var(--blue-dark); }
    .stTabs [data-baseweb="tab"] { font-weight: 600; }
    .stTabs [aria-selected="true"] { 
        color: var(--blue-mid) !important; 
        border-bottom: 3px solid var(--blue-mid) !important; 
    }
    </style>
    """
