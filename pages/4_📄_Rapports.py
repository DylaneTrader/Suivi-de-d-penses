"""
Rapports page – Export PDF/Excel des rapports mensuels/annuels.
"""

import sys
import os
import io
from datetime import date, datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import streamlit as st

from data.data_manager import get_transactions, get_budget, get_categories
from data.auth import validate_session

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Rapports – Suivi de Dépenses",
    page_icon="📄",
    layout="wide",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    :root {
        --blue-dark:  #1B3A5C;
        --blue-mid:   #2E6DA4;
        --grey-mid:   #7A8C9E;
        --grey-light: #C8D4DF;
        --warm-white: #F4F7FB;
        --green:      #2ECC71;
        --red:        #E74C3C;
    }
    .stApp { background-color: var(--warm-white); }
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1B3A5C 0%, #2E6DA4 100%);
    }
    section[data-testid="stSidebar"] * { color: #FFFFFF !important; }
    h1 { color: var(--blue-dark); font-weight: 700; }
    h2, h3 { color: var(--blue-mid); }
    .stButton > button {
        background-color: var(--blue-mid); color: #FFF;
        border: none; border-radius: 8px; font-weight: 600;
    }
    .stButton > button:hover { background-color: var(--blue-dark); }
    .report-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(27,58,92,0.08);
        margin-bottom: 1rem;
    }
    .report-title {
        font-weight: 700;
        color: var(--blue-dark);
        font-size: 1.1rem;
        margin-bottom: 0.5rem;
    }
    .report-desc {
        color: var(--grey-mid);
        font-size: 0.9rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Auth check ────────────────────────────────────────────────────────────────
if "session_token" not in st.session_state or not st.session_state.session_token:
    st.warning("🔐 Veuillez vous connecter pour accéder à cette page.")
    st.stop()

valid, username = validate_session(st.session_state.session_token)
if not valid:
    st.warning("🔐 Session expirée. Veuillez vous reconnecter.")
    st.stop()

# ── Sidebar user info ─────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        f"""
        <div style="text-align:center; padding: 1rem 0;">
            <span style="font-size:2rem;">💰</span>
            <h3 style="margin:0.5rem 0;">Suivi de Dépenses</h3>
            <p style="font-size:0.8rem; opacity:0.8;">👤 {username}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ── Load data ─────────────────────────────────────────────────────────────────
transactions = get_transactions()
budget = get_budget()
categories = get_categories()

if transactions:
    df = pd.DataFrame(transactions)
    df["date"] = pd.to_datetime(df["date"])
    df["montant"] = pd.to_numeric(df["montant"], errors="coerce").fillna(0)
    df["mois"] = df["date"].dt.to_period("M")
    df["annee"] = df["date"].dt.year
else:
    df = pd.DataFrame(columns=["id", "type", "montant", "categorie", "description", "date"])

# ── Page header ───────────────────────────────────────────────────────────────
st.title("📄 Rapports & Exports")
st.caption("Générez et exportez vos rapports financiers en PDF ou Excel")

# ── Report configuration ──────────────────────────────────────────────────────
st.subheader("⚙️ Configuration du rapport")

col1, col2 = st.columns(2)

with col1:
    report_type = st.selectbox(
        "Type de rapport",
        ["Mensuel", "Annuel", "Personnalisé"],
        key="report_type"
    )

with col2:
    export_format = st.selectbox(
        "Format d'export",
        ["Excel (.xlsx)", "CSV", "PDF (Résumé)"],
        key="export_format"
    )

# Date range selection
st.markdown("##### 📅 Période")
today = date.today()

if report_type == "Mensuel":
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        months_fr = {
            1: "Janvier", 2: "Février", 3: "Mars", 4: "Avril",
            5: "Mai", 6: "Juin", 7: "Juillet", 8: "Août",
            9: "Septembre", 10: "Octobre", 11: "Novembre", 12: "Décembre",
        }
        selected_month = st.selectbox("Mois", list(months_fr.keys()), 
                                       format_func=lambda x: months_fr[x],
                                       index=today.month - 1)
    with col_m2:
        selected_year = st.selectbox("Année", range(today.year - 5, today.year + 1),
                                      index=5)
    
    start_date = date(selected_year, selected_month, 1)
    if selected_month == 12:
        end_date = date(selected_year + 1, 1, 1)
    else:
        end_date = date(selected_year, selected_month + 1, 1)
    
    report_title = f"Rapport {months_fr[selected_month]} {selected_year}"

elif report_type == "Annuel":
    selected_year = st.selectbox("Année", range(today.year - 5, today.year + 1), index=5)
    start_date = date(selected_year, 1, 1)
    end_date = date(selected_year + 1, 1, 1)
    report_title = f"Rapport Annuel {selected_year}"

else:  # Personnalisé
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        start_date = st.date_input("Date début", value=date(today.year, 1, 1))
    with col_d2:
        end_date = st.date_input("Date fin", value=today)
    report_title = f"Rapport du {start_date.strftime('%d/%m/%Y')} au {end_date.strftime('%d/%m/%Y')}"

# ── Filter data ───────────────────────────────────────────────────────────────
if not df.empty:
    df_filtered = df[
        (df["date"] >= pd.Timestamp(start_date)) & 
        (df["date"] < pd.Timestamp(end_date))
    ]
else:
    df_filtered = df

# ── Options ───────────────────────────────────────────────────────────────────
st.markdown("##### 📋 Contenu du rapport")
col_opt1, col_opt2, col_opt3 = st.columns(3)

with col_opt1:
    include_transactions = st.checkbox("Liste des transactions", value=True)
    include_summary = st.checkbox("Résumé financier", value=True)

with col_opt2:
    include_by_category = st.checkbox("Répartition par catégorie", value=True)
    include_budget_status = st.checkbox("État du budget", value=True)

with col_opt3:
    include_trends = st.checkbox("Évolution temporelle", value=True)
    include_insights = st.checkbox("Insights et recommandations", value=True)

st.markdown("---")

# ── Report preview ────────────────────────────────────────────────────────────
st.subheader("👁️ Aperçu du rapport")
st.markdown(f"### {report_title}")

if df_filtered.empty:
    st.info("Aucune transaction pour cette période.")
else:
    # Summary metrics
    if include_summary:
        st.markdown("#### 📊 Résumé financier")
        depenses = df_filtered[df_filtered["type"] == "depense"]["montant"].sum()
        revenus = df_filtered[df_filtered["type"] == "revenu"]["montant"].sum()
        solde = revenus - depenses
        nb_tx = len(df_filtered)
        
        col_s1, col_s2, col_s3, col_s4 = st.columns(4)
        col_s1.metric("💸 Total Dépenses", f"{depenses:,.0f} FCFA")
        col_s2.metric("💰 Total Revenus", f"{revenus:,.0f} FCFA")
        col_s3.metric("📈 Solde", f"{solde:,.0f} FCFA")
        col_s4.metric("📝 Transactions", f"{nb_tx}")
    
    # By category
    if include_by_category:
        st.markdown("#### 🏷️ Répartition par catégorie")
        col_cat1, col_cat2 = st.columns(2)
        
        with col_cat1:
            st.markdown("**Dépenses par catégorie**")
            df_dep_cat = df_filtered[df_filtered["type"] == "depense"].groupby("categorie")["montant"].sum().reset_index()
            df_dep_cat = df_dep_cat.sort_values("montant", ascending=False)
            if not df_dep_cat.empty:
                df_dep_cat["pourcentage"] = (df_dep_cat["montant"] / df_dep_cat["montant"].sum() * 100).round(1)
                df_dep_cat["montant_fmt"] = df_dep_cat["montant"].apply(lambda x: f"{x:,.0f} FCFA")
                st.dataframe(
                    df_dep_cat[["categorie", "montant_fmt", "pourcentage"]].rename(
                        columns={"categorie": "Catégorie", "montant_fmt": "Montant", "pourcentage": "%"}
                    ),
                    hide_index=True,
                    use_container_width=True
                )
            else:
                st.info("Aucune dépense")
        
        with col_cat2:
            st.markdown("**Revenus par catégorie**")
            df_rev_cat = df_filtered[df_filtered["type"] == "revenu"].groupby("categorie")["montant"].sum().reset_index()
            df_rev_cat = df_rev_cat.sort_values("montant", ascending=False)
            if not df_rev_cat.empty:
                df_rev_cat["pourcentage"] = (df_rev_cat["montant"] / df_rev_cat["montant"].sum() * 100).round(1)
                df_rev_cat["montant_fmt"] = df_rev_cat["montant"].apply(lambda x: f"{x:,.0f} FCFA")
                st.dataframe(
                    df_rev_cat[["categorie", "montant_fmt", "pourcentage"]].rename(
                        columns={"categorie": "Catégorie", "montant_fmt": "Montant", "pourcentage": "%"}
                    ),
                    hide_index=True,
                    use_container_width=True
                )
            else:
                st.info("Aucun revenu")
    
    # Budget status
    if include_budget_status:
        st.markdown("#### 🎯 État du budget")
        limites = budget.get("limites", {})
        if limites:
            rows = []
            for cat, limite in limites.items():
                spent = df_filtered[
                    (df_filtered["type"] == "depense") & 
                    (df_filtered["categorie"] == cat)
                ]["montant"].sum()
                pct = (spent / limite * 100) if limite > 0 else 0
                status = "✅ OK" if pct <= 80 else ("⚠️ Attention" if pct <= 100 else "🔴 Dépassé")
                rows.append({
                    "Catégorie": cat,
                    "Limite": f"{limite:,.0f} FCFA",
                    "Dépensé": f"{spent:,.0f} FCFA",
                    "Utilisation": f"{pct:.1f}%",
                    "Statut": status
                })
            st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
        else:
            st.info("Aucune limite de budget définie.")
    
    # Transactions list
    if include_transactions:
        st.markdown("#### 📋 Liste des transactions")
        df_display = df_filtered.copy()
        df_display["date_fmt"] = df_display["date"].dt.strftime("%d/%m/%Y")
        df_display["type_label"] = df_display["type"].map({"depense": "💸 Dépense", "revenu": "💰 Revenu"})
        df_display["montant_fmt"] = df_display["montant"].apply(lambda x: f"{x:,.0f} FCFA")
        st.dataframe(
            df_display[["date_fmt", "type_label", "categorie", "montant_fmt", "description"]].rename(
                columns={
                    "date_fmt": "Date",
                    "type_label": "Type",
                    "categorie": "Catégorie",
                    "montant_fmt": "Montant",
                    "description": "Description"
                }
            ),
            hide_index=True,
            use_container_width=True
        )

st.markdown("---")

# ── Export buttons ────────────────────────────────────────────────────────────
st.subheader("📥 Télécharger le rapport")

col_dl1, col_dl2, col_dl3 = st.columns(3)

with col_dl1:
    # Excel export
    if not df_filtered.empty:
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            # Summary sheet
            summary_data = {
                "Métrique": ["Total Dépenses", "Total Revenus", "Solde", "Nombre de transactions"],
                "Valeur": [
                    f"{df_filtered[df_filtered['type'] == 'depense']['montant'].sum():,.0f} FCFA",
                    f"{df_filtered[df_filtered['type'] == 'revenu']['montant'].sum():,.0f} FCFA",
                    f"{df_filtered[df_filtered['type'] == 'revenu']['montant'].sum() - df_filtered[df_filtered['type'] == 'depense']['montant'].sum():,.0f} FCFA",
                    len(df_filtered)
                ]
            }
            pd.DataFrame(summary_data).to_excel(writer, sheet_name="Résumé", index=False)
            
            # Transactions sheet
            df_export = df_filtered[["date", "type", "categorie", "montant", "description"]].copy()
            df_export["date"] = df_export["date"].dt.strftime("%Y-%m-%d")
            df_export.to_excel(writer, sheet_name="Transactions", index=False)
            
            # By category sheets
            if not df_filtered[df_filtered["type"] == "depense"].empty:
                df_dep_cat = df_filtered[df_filtered["type"] == "depense"].groupby("categorie")["montant"].sum().reset_index()
                df_dep_cat.to_excel(writer, sheet_name="Dépenses par catégorie", index=False)
            
            if not df_filtered[df_filtered["type"] == "revenu"].empty:
                df_rev_cat = df_filtered[df_filtered["type"] == "revenu"].groupby("categorie")["montant"].sum().reset_index()
                df_rev_cat.to_excel(writer, sheet_name="Revenus par catégorie", index=False)
        
        excel_buffer.seek(0)
        st.download_button(
            "📥 Télécharger Excel",
            data=excel_buffer,
            file_name=f"rapport_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    else:
        st.button("📥 Télécharger Excel", disabled=True, use_container_width=True)

with col_dl2:
    # CSV export
    if not df_filtered.empty:
        csv_data = df_filtered[["date", "type", "categorie", "montant", "description"]].copy()
        csv_data["date"] = csv_data["date"].dt.strftime("%Y-%m-%d")
        csv_buffer = csv_data.to_csv(index=False)
        st.download_button(
            "📥 Télécharger CSV",
            data=csv_buffer,
            file_name=f"transactions_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    else:
        st.button("📥 Télécharger CSV", disabled=True, use_container_width=True)

with col_dl3:
    # PDF summary (text format for simplicity)
    if not df_filtered.empty:
        depenses = df_filtered[df_filtered["type"] == "depense"]["montant"].sum()
        revenus = df_filtered[df_filtered["type"] == "revenu"]["montant"].sum()
        solde = revenus - depenses
        
        pdf_content = f"""
===========================================
{report_title}
Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}
===========================================

RÉSUMÉ FINANCIER
----------------
Total Dépenses:     {depenses:>15,.0f} FCFA
Total Revenus:      {revenus:>15,.0f} FCFA
Solde:              {solde:>15,.0f} FCFA
Nb Transactions:    {len(df_filtered):>15}

DÉPENSES PAR CATÉGORIE
----------------------
"""
        df_dep = df_filtered[df_filtered["type"] == "depense"].groupby("categorie")["montant"].sum()
        for cat, montant in df_dep.items():
            pct = (montant / depenses * 100) if depenses > 0 else 0
            pdf_content += f"{cat:.<25} {montant:>12,.0f} FCFA ({pct:>5.1f}%)\n"
        
        pdf_content += """
REVENUS PAR CATÉGORIE
---------------------
"""
        df_rev = df_filtered[df_filtered["type"] == "revenu"].groupby("categorie")["montant"].sum()
        for cat, montant in df_rev.items():
            pct = (montant / revenus * 100) if revenus > 0 else 0
            pdf_content += f"{cat:.<25} {montant:>12,.0f} FCFA ({pct:>5.1f}%)\n"
        
        st.download_button(
            "📥 Télécharger Résumé (TXT)",
            data=pdf_content,
            file_name=f"resume_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.txt",
            mime="text/plain",
            use_container_width=True
        )
    else:
        st.button("📥 Télécharger Résumé", disabled=True, use_container_width=True)
