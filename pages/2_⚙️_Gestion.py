"""
Gestion page – budget definition, limits/objectives, category management, transaction entry.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import date
import streamlit as st

from data.data_manager import (
    get_categories,
    get_budget,
    get_transactions,
    add_transaction,
    delete_transaction,
    add_category,
    delete_category,
    save_budget,
)

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Gestion – Suivi de Dépenses",
    page_icon="⚙️",
    layout="wide",
)

# ── Shared CSS ────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    :root {
        --blue-dark:  #1B3A5C;
        --blue-mid:   #2E6DA4;
        --grey-mid:   #7A8C9E;
        --grey-light: #C8D4DF;
        --warm-white: #F4F7FB;
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
    """,
    unsafe_allow_html=True,
)

# ── Load data ─────────────────────────────────────────────────────────────────
categories = get_categories()
budget = get_budget()

# ── Page header ───────────────────────────────────────────────────────────────
st.title("⚙️ Gestion")

tab_transactions, tab_budget, tab_categories = st.tabs(
    ["💳 Transactions", "🎯 Budget & Limites", "🏷️ Catégories"]
)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 – TRANSACTIONS
# ═══════════════════════════════════════════════════════════════════════════════
with tab_transactions:
    st.subheader("➕ Ajouter une transaction")

    with st.form("form_transaction", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            type_tx = st.selectbox(
                "Type", ["Dépense", "Revenu"], key="type_tx"
            )
            cat_list = (
                categories.get("depenses", [])
                if type_tx == "Dépense"
                else categories.get("revenus", [])
            )
            categorie = st.selectbox("Catégorie", cat_list, key="cat_tx")
        with c2:
            montant = st.number_input(
                "Montant (€)", min_value=0.01, step=0.01, format="%.2f", key="montant_tx"
            )
            date_tx = st.date_input("Date", value=date.today(), key="date_tx")
        description = st.text_input("Description (optionnel)", key="desc_tx")
        submitted = st.form_submit_button("✅ Enregistrer la transaction")

    if submitted:
        type_code = "depense" if type_tx == "Dépense" else "revenu"
        add_transaction(type_code, montant, categorie, description, date_tx)
        st.success(f"Transaction enregistrée : {type_tx} de **{montant:,.2f} €** ({categorie})")
        st.rerun()

    st.markdown("---")
    st.subheader("📋 Historique des transactions")

    transactions = get_transactions()
    if not transactions:
        st.info("Aucune transaction enregistrée.")
    else:
        import pandas as pd

        df = pd.DataFrame(transactions).sort_values("date", ascending=False)
        df["date"] = pd.to_datetime(df["date"]).dt.strftime("%d/%m/%Y")
        df["type_label"] = df["type"].map({"depense": "💸 Dépense", "revenu": "💰 Revenu"})
        df["montant_str"] = df["montant"].apply(lambda x: f"{float(x):,.2f} €")

        df_display = df[["date", "type_label", "categorie", "montant_str", "description"]].rename(
            columns={
                "date": "Date",
                "type_label": "Type",
                "categorie": "Catégorie",
                "montant_str": "Montant",
                "description": "Description",
            }
        )
        st.dataframe(df_display, hide_index=True, use_container_width=True)

        st.markdown("##### 🗑️ Supprimer une transaction")
        ids = [t["id"] for t in transactions]
        labels = [
            f"{t['date']} – {t['type']} – {t['categorie']} – {float(t['montant']):,.2f} €"
            for t in sorted(transactions, key=lambda x: x["date"], reverse=True)
        ]
        id_map = {
            f"{t['date']} – {t['type']} – {t['categorie']} – {float(t['montant']):,.2f} €": t["id"]
            for t in transactions
        }
        selected_label = st.selectbox("Sélectionner la transaction à supprimer", labels, key="del_tx")
        if st.button("🗑️ Supprimer", key="btn_del_tx"):
            delete_transaction(id_map[selected_label])
            st.success("Transaction supprimée.")
            st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 – BUDGET & LIMITS / OBJECTIVES
# ═══════════════════════════════════════════════════════════════════════════════
with tab_budget:
    st.subheader("💶 Revenu mensuel cible")

    current_revenu_cible = budget.get("revenu_mensuel_cible", 0.0)
    current_limites = budget.get("limites", {})
    current_objectifs = budget.get("objectifs", {})

    revenu_cible = st.number_input(
        "Revenu mensuel cible (€)",
        min_value=0.0,
        step=100.0,
        format="%.2f",
        value=float(current_revenu_cible),
        key="revenu_cible",
        help="Référence pour calculer le taux d'utilisation mensuel de votre budget.",
    )

    st.markdown("---")
    st.subheader("🔴 Limites de dépenses par catégorie")
    st.caption("Définissez un plafond mensuel de dépenses par catégorie.")

    dep_categories = categories.get("depenses", [])
    new_limites = {}
    cols_lim = st.columns(3)
    for i, cat in enumerate(dep_categories):
        with cols_lim[i % 3]:
            new_limites[cat] = st.number_input(
                f"{cat} (€/mois)",
                min_value=0.0,
                step=10.0,
                format="%.2f",
                value=float(current_limites.get(cat, 0.0)),
                key=f"lim_{cat}",
                help="0 = pas de limite définie",
            )

    st.markdown("---")
    st.subheader("🟢 Objectifs de revenus par catégorie")
    st.caption("Définissez un objectif annuel de revenus par catégorie.")

    rev_categories = categories.get("revenus", [])
    new_objectifs = {}
    cols_obj = st.columns(3)
    for i, cat in enumerate(rev_categories):
        with cols_obj[i % 3]:
            new_objectifs[cat] = st.number_input(
                f"{cat} (€/an)",
                min_value=0.0,
                step=100.0,
                format="%.2f",
                value=float(current_objectifs.get(cat, 0.0)),
                key=f"obj_{cat}",
                help="0 = pas d'objectif défini",
            )

    st.markdown("")
    if st.button("💾 Enregistrer le budget", key="btn_save_budget"):
        active_limites = {k: v for k, v in new_limites.items() if v > 0}
        active_objectifs = {k: v for k, v in new_objectifs.items() if v > 0}
        save_budget(revenu_cible, active_limites, active_objectifs)
        st.success("✅ Budget enregistré avec succès !")
        st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 – CATEGORIES
# ═══════════════════════════════════════════════════════════════════════════════
with tab_categories:
    col_dep_cat, col_rev_cat = st.columns(2)

    with col_dep_cat:
        st.subheader("💸 Catégories de dépenses")

        dep_cats = categories.get("depenses", [])
        if dep_cats:
            for cat in dep_cats:
                c1, c2 = st.columns([4, 1])
                c1.markdown(f"- {cat}")
                if c2.button("🗑️", key=f"del_dep_{cat}", help=f"Supprimer {cat}"):
                    delete_category("depense", cat)
                    st.success(f"Catégorie « {cat} » supprimée.")
                    st.rerun()
        else:
            st.info("Aucune catégorie de dépenses.")

        st.markdown("##### ➕ Nouvelle catégorie de dépenses")
        with st.form("form_add_dep_cat", clear_on_submit=True):
            new_dep_cat = st.text_input("Nom de la catégorie", key="new_dep_cat_input")
            add_dep_cat = st.form_submit_button("Ajouter")
        if add_dep_cat:
            if new_dep_cat.strip():
                ok = add_category("depense", new_dep_cat.strip())
                if ok:
                    st.success(f"✅ Catégorie « {new_dep_cat.strip()} » ajoutée.")
                    st.rerun()
                else:
                    st.warning(f"La catégorie « {new_dep_cat.strip()} » existe déjà.")
            else:
                st.error("Le nom de la catégorie ne peut pas être vide.")

    with col_rev_cat:
        st.subheader("💰 Catégories de revenus")

        rev_cats = categories.get("revenus", [])
        if rev_cats:
            for cat in rev_cats:
                c1, c2 = st.columns([4, 1])
                c1.markdown(f"- {cat}")
                if c2.button("🗑️", key=f"del_rev_{cat}", help=f"Supprimer {cat}"):
                    delete_category("revenu", cat)
                    st.success(f"Catégorie « {cat} » supprimée.")
                    st.rerun()
        else:
            st.info("Aucune catégorie de revenus.")

        st.markdown("##### ➕ Nouvelle catégorie de revenus")
        with st.form("form_add_rev_cat", clear_on_submit=True):
            new_rev_cat = st.text_input("Nom de la catégorie", key="new_rev_cat_input")
            add_rev_cat = st.form_submit_button("Ajouter")
        if add_rev_cat:
            if new_rev_cat.strip():
                ok = add_category("revenu", new_rev_cat.strip())
                if ok:
                    st.success(f"✅ Catégorie « {new_rev_cat.strip()} » ajoutée.")
                    st.rerun()
                else:
                    st.warning(f"La catégorie « {new_rev_cat.strip()} » existe déjà.")
            else:
                st.error("Le nom de la catégorie ne peut pas être vide.")
