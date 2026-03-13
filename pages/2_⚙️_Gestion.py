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
    rename_category,
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
                "Montant (FCFA)", min_value=0.01, step=0.01, format="%.2f", key="montant_tx"
            )
            date_tx = st.date_input("Date", value=date.today(), key="date_tx")
        description = st.text_input("Description (optionnel)", key="desc_tx")
        submitted = st.form_submit_button("✅ Enregistrer la transaction")

    if submitted:
        type_code = "depense" if type_tx == "Dépense" else "revenu"
        add_transaction(type_code, montant, categorie, description, date_tx)
        st.success(f"Transaction enregistrée : {type_tx} de **{montant:,.2f} FCFA** ({categorie})")
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
        df["montant_str"] = df["montant"].apply(lambda x: f"{float(x):,.2f} FCFA")

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
            f"{t['date']} – {t['type']} – {t['categorie']} – {float(t['montant']):,.2f} FCFA"
            for t in sorted(transactions, key=lambda x: x["date"], reverse=True)
        ]
        id_map = {
            f"{t['date']} – {t['type']} – {t['categorie']} – {float(t['montant']):,.2f} FCFA": t["id"]
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
    st.subheader("� Revenus mensuels par catégorie")
    st.caption("Définissez vos revenus mensuels attendus pour chaque source (Salaire, Freelance, etc.).")

    current_revenus_mensuels = budget.get("revenus_mensuels", {})
    current_limites = budget.get("limites", {})
    current_objectifs = budget.get("objectifs", {})

    rev_categories = categories.get("revenus", [])
    new_revenus_mensuels = {}
    cols_rev = st.columns(3)
    for i, cat in enumerate(rev_categories):
        with cols_rev[i % 3]:
            new_revenus_mensuels[cat] = st.number_input(
                f"{cat} (FCFA/mois)",
                min_value=0.0,
                step=1000.0,
                format="%.0f",
                value=float(current_revenus_mensuels.get(cat, 0.0)),
                key=f"rev_mens_{cat}",
                help="Montant mensuel attendu pour cette source de revenu",
            )
    
    # Calculer le total des revenus
    total_revenus = sum(new_revenus_mensuels.values())
    st.markdown(f"**💵 Total revenus mensuels : {total_revenus:,.0f} FCFA**")

    st.markdown("---")
    st.subheader("🔴 Limites de dépenses par catégorie")
    st.caption("Définissez un plafond mensuel de dépenses par catégorie.")

    dep_categories = categories.get("depenses", [])
    new_limites = {}
    cols_lim = st.columns(3)
    for i, cat in enumerate(dep_categories):
        with cols_lim[i % 3]:
            new_limites[cat] = st.number_input(
                f"{cat} (FCFA/mois)",
                min_value=0.0,
                step=1000.0,
                format="%.0f",
                value=float(current_limites.get(cat, 0.0)),
                key=f"lim_{cat}",
                help="0 = pas de limite définie",
            )
    
    # Calculer le total des limites et vérifier le dépassement
    total_limites = sum(new_limites.values())
    st.markdown(f"**📊 Total limites de dépenses : {total_limites:,.0f} FCFA**")
    
    # Alerte de dépassement
    if total_revenus > 0 and total_limites > total_revenus:
        depassement = total_limites - total_revenus
        pct_depassement = (depassement / total_revenus) * 100
        st.error(
            f"⚠️ **Attention : Dépassement de budget !** "
            f"Vos limites de dépenses ({total_limites:,.0f} FCFA) dépassent vos revenus "
            f"({total_revenus:,.0f} FCFA) de **{depassement:,.0f} FCFA** (+{pct_depassement:.1f}%)"
        )
    elif total_revenus > 0 and total_limites > 0:
        reste = total_revenus - total_limites
        pct_epargne = (reste / total_revenus) * 100
        if reste >= 0:
            st.success(
                f"✅ **Budget équilibré !** "
                f"Il vous reste **{reste:,.0f} FCFA** ({pct_epargne:.1f}%) pour l'épargne ou imprévus."
            )
    elif total_revenus == 0 and total_limites > 0:
        st.warning("⚠️ Définissez vos revenus mensuels pour vérifier l'équilibre de votre budget.")

    st.markdown("---")
    st.subheader("🟢 Objectifs de revenus par catégorie")
    st.caption("Définissez un objectif annuel de revenus par catégorie.")

    new_objectifs = {}
    cols_obj = st.columns(3)
    for i, cat in enumerate(rev_categories):
        with cols_obj[i % 3]:
            new_objectifs[cat] = st.number_input(
                f"{cat} (FCFA/an)",
                min_value=0.0,
                step=10000.0,
                format="%.0f",
                value=float(current_objectifs.get(cat, 0.0)),
                key=f"obj_{cat}",
                help="0 = pas d'objectif défini",
            )

    st.markdown("")
    if st.button("💾 Enregistrer le budget", key="btn_save_budget"):
        active_revenus = {k: v for k, v in new_revenus_mensuels.items() if v > 0}
        active_limites = {k: v for k, v in new_limites.items() if v > 0}
        active_objectifs = {k: v for k, v in new_objectifs.items() if v > 0}
        save_budget(active_revenus, active_limites, active_objectifs)
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
                c1, c2, c3 = st.columns([4, 1, 1])
                c1.markdown(f"- {cat}")
                if c2.button("✏️", key=f"edit_dep_{cat}", help=f"Modifier {cat}"):
                    st.session_state[f"editing_dep_{cat}"] = True
                if c3.button("🗑️", key=f"del_dep_{cat}", help=f"Supprimer {cat}"):
                    delete_category("depense", cat)
                    st.success(f"Catégorie « {cat} » supprimée.")
                    st.rerun()
                
                # Edition form
                if st.session_state.get(f"editing_dep_{cat}", False):
                    with st.form(f"form_edit_dep_{cat}"):
                        new_name = st.text_input("Nouveau nom", value=cat, key=f"new_name_dep_{cat}")
                        col_save, col_cancel = st.columns(2)
                        save_btn = col_save.form_submit_button("💾 Enregistrer")
                        cancel_btn = col_cancel.form_submit_button("❌ Annuler")
                    
                    if save_btn:
                        if new_name.strip() and new_name.strip() != cat:
                            ok = rename_category("depense", cat, new_name.strip())
                            if ok:
                                st.success(f"✅ Catégorie renommée en « {new_name.strip()} »")
                                st.session_state[f"editing_dep_{cat}"] = False
                                st.rerun()
                            else:
                                st.error("Ce nom existe déjà ou erreur lors du renommage.")
                        elif new_name.strip() == cat:
                            st.session_state[f"editing_dep_{cat}"] = False
                            st.rerun()
                        else:
                            st.error("Le nom ne peut pas être vide.")
                    if cancel_btn:
                        st.session_state[f"editing_dep_{cat}"] = False
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
                c1, c2, c3 = st.columns([4, 1, 1])
                c1.markdown(f"- {cat}")
                if c2.button("✏️", key=f"edit_rev_{cat}", help=f"Modifier {cat}"):
                    st.session_state[f"editing_rev_{cat}"] = True
                if c3.button("🗑️", key=f"del_rev_{cat}", help=f"Supprimer {cat}"):
                    delete_category("revenu", cat)
                    st.success(f"Catégorie « {cat} » supprimée.")
                    st.rerun()
                
                # Edition form
                if st.session_state.get(f"editing_rev_{cat}", False):
                    with st.form(f"form_edit_rev_{cat}"):
                        new_name = st.text_input("Nouveau nom", value=cat, key=f"new_name_rev_{cat}")
                        col_save, col_cancel = st.columns(2)
                        save_btn = col_save.form_submit_button("💾 Enregistrer")
                        cancel_btn = col_cancel.form_submit_button("❌ Annuler")
                    
                    if save_btn:
                        if new_name.strip() and new_name.strip() != cat:
                            ok = rename_category("revenu", cat, new_name.strip())
                            if ok:
                                st.success(f"✅ Catégorie renommée en « {new_name.strip()} »")
                                st.session_state[f"editing_rev_{cat}"] = False
                                st.rerun()
                            else:
                                st.error("Ce nom existe déjà ou erreur lors du renommage.")
                        elif new_name.strip() == cat:
                            st.session_state[f"editing_rev_{cat}"] = False
                            st.rerun()
                        else:
                            st.error("Le nom ne peut pas être vide.")
                    if cancel_btn:
                        st.session_state[f"editing_rev_{cat}"] = False
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
