"""
Dashboard page – progression YTD, monthly trends, category histograms, budget limits.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import date
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

from data.data_manager import get_transactions, get_budget, get_categories

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Dashboard – Suivi de Dépenses",
    page_icon="📊",
    layout="wide",
)

# ── Shared CSS (duplicated so each page is standalone) ────────────────────────
st.markdown(
    """
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
    .stTabs [aria-selected="true"] { color: var(--blue-mid) !important; border-bottom: 3px solid var(--blue-mid) !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Plotly colour palette ─────────────────────────────────────────────────────
BLUE_PALETTE = ["#1B3A5C", "#2E6DA4", "#5B9BD5", "#89B8E0", "#B6D4F0"]
GREEN = "#2ECC71"
RED = "#E74C3C"
ACCENT = "#F0A500"


def build_df(transactions: list) -> pd.DataFrame:
    if not transactions:
        return pd.DataFrame(columns=["id", "type", "montant", "categorie", "description", "date", "mois", "annee"])
    df = pd.DataFrame(transactions)
    df["date"] = pd.to_datetime(df["date"])
    df["mois"] = df["date"].dt.to_period("M")
    df["annee"] = df["date"].dt.year
    df["montant"] = pd.to_numeric(df["montant"], errors="coerce").fillna(0)
    return df


def get_ytd_df(df: pd.DataFrame, year: int) -> pd.DataFrame:
    return df[df["annee"] == year]


# ── Load data ─────────────────────────────────────────────────────────────────
transactions = get_transactions()
budget = get_budget()
categories = get_categories()

df_all = build_df(transactions)

today = date.today()
current_year = today.year
current_month = today.month
months_fr = {
    1: "Janv.", 2: "Févr.", 3: "Mars", 4: "Avr.",
    5: "Mai", 6: "Juin", 7: "Juil.", 8: "Août",
    9: "Sept.", 10: "Oct.", 11: "Nov.", 12: "Déc.",
}

df_ytd = get_ytd_df(df_all, current_year) if not df_all.empty else df_all

# ── Page header ───────────────────────────────────────────────────────────────
st.title("📊 Dashboard")
st.caption(f"Données au {today.strftime('%d/%m/%Y')} — Année {current_year}")

# ═══════════════════════════════════════════════════════════════════════════════
# 1. KPI CARDS (top row)
# ═══════════════════════════════════════════════════════════════════════════════
depenses_ytd = df_ytd[df_ytd["type"] == "depense"]["montant"].sum() if not df_ytd.empty else 0.0
revenus_ytd = df_ytd[df_ytd["type"] == "revenu"]["montant"].sum() if not df_ytd.empty else 0.0
solde_ytd = revenus_ytd - depenses_ytd

# Current month KPIs
df_month = df_ytd[df_ytd["date"].dt.month == current_month] if not df_ytd.empty else df_ytd
depenses_mois = df_month[df_month["type"] == "depense"]["montant"].sum() if not df_month.empty else 0.0
revenus_mois = df_month[df_month["type"] == "revenu"]["montant"].sum() if not df_month.empty else 0.0

col1, col2, col3, col4 = st.columns(4)
col1.metric("💸 Dépenses YTD", f"{depenses_ytd:,.2f} FCFA", delta=None)
col2.metric("💰 Revenus YTD", f"{revenus_ytd:,.2f} FCFA", delta=None)
col3.metric(
    "📈 Solde YTD",
    f"{solde_ytd:,.2f} FCFA",
    delta=f"{solde_ytd:+,.2f} FCFA",
    delta_color="normal",
)
col4.metric(
    f"🗓️ Dépenses {months_fr[current_month]}",
    f"{depenses_mois:,.2f} FCFA",
    delta=None,
)

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════════════════
# 2. YTD PROGRESSION (cumulative area chart)
# ═══════════════════════════════════════════════════════════════════════════════
st.subheader("📈 Progression depuis le début de l'année (cumulée)")

if df_ytd.empty:
    st.info("Aucune transaction enregistrée pour cette année. Ajoutez des données via la page **Gestion**.")
else:
    df_sorted = df_ytd.sort_values("date")
    df_dep = df_sorted[df_sorted["type"] == "depense"].copy()
    df_rev = df_sorted[df_sorted["type"] == "revenu"].copy()

    df_dep["cumul"] = df_dep["montant"].cumsum()
    df_rev["cumul"] = df_rev["montant"].cumsum()

    fig_ytd = go.Figure()
    fig_ytd.add_trace(
        go.Scatter(
            x=df_rev["date"], y=df_rev["cumul"],
            name="Revenus cumulés", mode="lines+markers",
            line=dict(color=GREEN, width=2.5),
            fill="tozeroy", fillcolor="rgba(46,204,113,0.12)",
        )
    )
    fig_ytd.add_trace(
        go.Scatter(
            x=df_dep["date"], y=df_dep["cumul"],
            name="Dépenses cumulées", mode="lines+markers",
            line=dict(color=RED, width=2.5),
            fill="tozeroy", fillcolor="rgba(231,76,60,0.12)",
        )
    )
    fig_ytd.update_layout(
        height=340,
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(244,247,251,1)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor="#E0E8F0", ticksuffix=" FCFA"),
        font=dict(color="#3D4B5C"),
    )
    st.plotly_chart(fig_ytd, use_container_width=True)

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════════════════
# 3. MONTHLY PROGRESSION (grouped bar chart)
# ═══════════════════════════════════════════════════════════════════════════════
st.subheader("📅 Progression mensuelle")

if df_ytd.empty:
    st.info("Aucune donnée disponible.")
else:
    df_monthly = (
        df_ytd.groupby([df_ytd["date"].dt.month, "type"])["montant"]
        .sum()
        .reset_index()
    )
    df_monthly.columns = ["mois_num", "type", "montant"]
    df_monthly["mois_label"] = df_monthly["mois_num"].map(months_fr)

    all_months = list(range(1, current_month + 1))
    months_labels = [months_fr[m] for m in all_months]

    dep_vals = []
    rev_vals = []
    for m in all_months:
        row_dep = df_monthly[(df_monthly["mois_num"] == m) & (df_monthly["type"] == "depense")]
        row_rev = df_monthly[(df_monthly["mois_num"] == m) & (df_monthly["type"] == "revenu")]
        dep_vals.append(row_dep["montant"].values[0] if not row_dep.empty else 0)
        rev_vals.append(row_rev["montant"].values[0] if not row_rev.empty else 0)

    fig_monthly = go.Figure()
    fig_monthly.add_trace(
        go.Bar(
            name="Revenus", x=months_labels, y=rev_vals,
            marker_color=GREEN, opacity=0.85,
        )
    )
    fig_monthly.add_trace(
        go.Bar(
            name="Dépenses", x=months_labels, y=dep_vals,
            marker_color=RED, opacity=0.85,
        )
    )
    fig_monthly.update_layout(
        barmode="group",
        height=320,
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(244,247,251,1)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor="#E0E8F0", ticksuffix=" FCFA"),
        font=dict(color="#3D4B5C"),
    )
    st.plotly_chart(fig_monthly, use_container_width=True)

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════════════════
# 4. HISTOGRAMS BY CATEGORY
# ═══════════════════════════════════════════════════════════════════════════════
st.subheader("📊 Dépenses et revenus par catégorie (YTD)")

col_dep, col_rev = st.columns(2)

with col_dep:
    st.markdown("#### 💸 Dépenses par catégorie")
    if df_ytd.empty or df_ytd[df_ytd["type"] == "depense"].empty:
        st.info("Aucune dépense enregistrée.")
    else:
        df_cat_dep = (
            df_ytd[df_ytd["type"] == "depense"]
            .groupby("categorie")["montant"]
            .sum()
            .reset_index()
            .sort_values("montant", ascending=True)
        )
        fig_dep = px.bar(
            df_cat_dep, x="montant", y="categorie", orientation="h",
            color="montant",
            color_continuous_scale=["#89B8E0", "#2E6DA4", "#1B3A5C"],
            labels={"montant": "Montant (FCFA)", "categorie": "Catégorie"},
        )
        fig_dep.update_coloraxes(showscale=False)
        fig_dep.update_layout(
            height=max(240, 40 * len(df_cat_dep)),
            margin=dict(l=10, r=10, t=10, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(244,247,251,1)",
            font=dict(color="#3D4B5C"),
            xaxis=dict(ticksuffix=" FCFA", showgrid=True, gridcolor="#E0E8F0"),
            yaxis=dict(showgrid=False),
        )
        st.plotly_chart(fig_dep, use_container_width=True)

with col_rev:
    st.markdown("#### 💰 Revenus par catégorie")
    if df_ytd.empty or df_ytd[df_ytd["type"] == "revenu"].empty:
        st.info("Aucun revenu enregistré.")
    else:
        df_cat_rev = (
            df_ytd[df_ytd["type"] == "revenu"]
            .groupby("categorie")["montant"]
            .sum()
            .reset_index()
            .sort_values("montant", ascending=True)
        )
        fig_rev = px.bar(
            df_cat_rev, x="montant", y="categorie", orientation="h",
            color="montant",
            color_continuous_scale=["#A8E6CF", "#2ECC71", "#1A8040"],
            labels={"montant": "Montant (FCFA)", "categorie": "Catégorie"},
        )
        fig_rev.update_coloraxes(showscale=False)
        fig_rev.update_layout(
            height=max(240, 40 * len(df_cat_rev)),
            margin=dict(l=10, r=10, t=10, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(244,247,251,1)",
            font=dict(color="#3D4B5C"),
            xaxis=dict(ticksuffix=" FCFA", showgrid=True, gridcolor="#E0E8F0"),
            yaxis=dict(showgrid=False),
        )
        st.plotly_chart(fig_rev, use_container_width=True)

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════════════════
# 5. BUDGET LIMITS INFO
# ═══════════════════════════════════════════════════════════════════════════════
st.subheader("🎯 Limites & objectifs budgétaires")

limites = budget.get("limites", {})
objectifs = budget.get("objectifs", {})
revenus_mensuels = budget.get("revenus_mensuels", {})
revenu_cible = sum(revenus_mensuels.values()) if revenus_mensuels else budget.get("revenu_mensuel_cible", 0.0)
total_limites = sum(limites.values()) if limites else 0.0

if not limites and not objectifs and revenu_cible == 0:
    st.info("Aucun budget défini. Rendez-vous sur la page **⚙️ Gestion** pour configurer vos limites et objectifs.")
else:
    if revenu_cible > 0:
        dep_mois_pct = (depenses_mois / revenu_cible * 100) if revenu_cible else 0
        c1, c2 = st.columns(2)
        c1.metric("💰 Revenus mensuels prévus", f"{revenu_cible:,.0f} FCFA")
        c2.metric(
            f"📊 Dépenses / Revenus ({months_fr[current_month]})",
            f"{depenses_mois:,.0f} FCFA",
            delta=f"{dep_mois_pct:.1f} %",
            delta_color="inverse",
        )
        
        # Alerte dépassement budget
        if total_limites > revenu_cible:
            depassement = total_limites - revenu_cible
            st.error(
                f"⚠️ **Budget déséquilibré !** Vos limites de dépenses ({total_limites:,.0f} FCFA) "
                f"dépassent vos revenus prévus de **{depassement:,.0f} FCFA**"
            )

    if limites:
        st.markdown("##### 🔴 Limites de dépenses par catégorie (mois en cours)")
        rows = []
        for cat, limit in limites.items():
            spent = (
                df_month[
                    (df_month["type"] == "depense") & (df_month["categorie"] == cat)
                ]["montant"].sum()
                if not df_month.empty
                else 0.0
            )
            pct = (spent / limit * 100) if limit > 0 else 0
            status = "✅" if pct <= 80 else ("⚠️" if pct <= 100 else "🔴")
            rows.append(
                {
                    "Catégorie": cat,
                    "Limite (FCFA)": f"{limit:,.0f}",
                    "Dépensé (FCFA)": f"{spent:,.0f}",
                    "Utilisation": f"{pct:.1f} %",
                    "Statut": status,
                }
            )
        st.dataframe(
            pd.DataFrame(rows),
            hide_index=True,
            use_container_width=True,
        )

        # Progress bars
        for row in rows:
            cat = row["Catégorie"]
            limit = limites[cat]
            spent_val = float(row["Dépensé (FCFA)"].replace(",", "").replace(" ", ""))
            pct_val = min(spent_val / limit, 1.0) if limit > 0 else 0
            color = "#2ECC71" if pct_val <= 0.8 else ("#F0A500" if pct_val <= 1.0 else "#E74C3C")
            st.markdown(
                f"<div style='display:flex;align-items:center;gap:10px;margin-bottom:4px;'>"
                f"<span style='width:130px;font-size:0.85rem;color:#3D4B5C;'>{cat}</span>"
                f"<div style='flex:1;background:#E0E8F0;border-radius:6px;height:14px;'>"
                f"<div style='width:{pct_val*100:.1f}%;background:{color};border-radius:6px;height:14px;'></div>"
                f"</div>"
                f"<span style='font-size:0.8rem;color:#3D4B5C;width:55px;text-align:right;'>"
                f"{pct_val*100:.1f}%</span>"
                f"</div>",
                unsafe_allow_html=True,
            )

    if objectifs:
        st.markdown("##### 🟢 Objectifs d'épargne / revenus")
        obj_rows = []
        for cat, obj in objectifs.items():
            earned = (
                df_ytd[
                    (df_ytd["type"] == "revenu") & (df_ytd["categorie"] == cat)
                ]["montant"].sum()
                if not df_ytd.empty
                else 0.0
            )
            pct = (earned / obj * 100) if obj > 0 else 0
            status = "✅" if pct >= 100 else ("🏃" if pct >= 50 else "🔵")
            obj_rows.append(
                {
                    "Catégorie": cat,
                    "Objectif (FCFA)": f"{obj:,.0f}",
                    "Atteint (FCFA)": f"{earned:,.0f}",
                    "Progression": f"{pct:.1f} %",
                    "Statut": status,
                }
            )
        st.dataframe(
            pd.DataFrame(obj_rows),
            hide_index=True,
            use_container_width=True,
        )

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════════════════
# 6. RECENT TRANSACTIONS TABLE
# ═══════════════════════════════════════════════════════════════════════════════
st.subheader("🧾 Dernières transactions")

if df_all.empty:
    st.info("Aucune transaction. Ajoutez-en via la page **⚙️ Gestion**.")
else:
    df_display = (
        df_all.sort_values("date", ascending=False)
        .head(20)
        .assign(
            Type=lambda d: d["type"].map({"depense": "💸 Dépense", "revenu": "💰 Revenu"}),
            Date=lambda d: d["date"].dt.strftime("%d/%m/%Y"),
            Montant=lambda d: d["montant"].map(lambda x: f"{x:,.0f} FCFA"),
        )
        [["Date", "Type", "categorie", "Montant", "description"]]
        .rename(columns={"categorie": "Catégorie", "description": "Description"})
    )
    st.dataframe(df_display, hide_index=True, use_container_width=True)
