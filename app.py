"""
Main entry point for the Suivi de Dépenses – Budget Personnel app.
"""

import streamlit as st

st.set_page_config(
    page_title="Suivi de Dépenses",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

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
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Sidebar navigation / branding ─────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        """
        <div style="text-align:center; padding: 1rem 0 0.5rem;">
            <span style="font-size:2.4rem;">💰</span>
            <h2 style="margin:0; font-size:1.15rem; font-weight:700;">
                Suivi de Dépenses
            </h2>
            <p style="font-size:0.75rem; opacity:0.75; margin:0;">Budget Personnel</p>
        </div>
        <hr style="border-color:rgba(255,255,255,0.25); margin: 0.5rem 0 1rem;" />
        """,
        unsafe_allow_html=True,
    )

# ── Home / landing content ─────────────────────────────────────────────────────
st.title("💰 Suivi de Dépenses – Budget Personnel")
st.markdown(
    """
    Bienvenue dans votre application de gestion de budget personnel.

    Utilisez le menu de navigation sur la gauche pour accéder aux pages :

    | Page | Description |
    |------|-------------|
    | 📊 **Dashboard** | Visualisez vos dépenses, revenus, tendances et limites de budget |
    | ⚙️ **Gestion** | Définissez votre budget, fixez des limites/objectifs et gérez vos catégories |
    """,
    unsafe_allow_html=True,
)
