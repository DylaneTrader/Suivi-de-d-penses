"""
Calendrier intelligent – Vue calendaire des transactions avec insights.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import date, timedelta
import calendar
import pandas as pd
import streamlit as st

from data.data_manager import get_transactions

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Calendrier – Suivi de Dépenses",
    page_icon="📅",
    layout="wide",
)

# ── Shared CSS ────────────────────────────────────────────────────────────────
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
    
    /* Calendar styles */
    .calendar-day {
        border: 1px solid var(--grey-light);
        border-radius: 8px;
        padding: 8px;
        min-height: 90px;
        background: #FFFFFF;
        margin: 2px;
        transition: all 0.2s;
    }
    .calendar-day:hover {
        box-shadow: 0 4px 12px rgba(27,58,92,0.15);
        transform: translateY(-2px);
    }
    .calendar-day.today {
        border: 2px solid var(--blue-mid);
        background: linear-gradient(135deg, #F4F7FB 0%, #E8F0F8 100%);
    }
    .calendar-day.has-expense {
        border-left: 4px solid var(--red);
    }
    .calendar-day.has-income {
        border-left: 4px solid var(--green);
    }
    .calendar-day.has-both {
        border-left: 4px solid var(--blue-mid);
    }
    .day-number {
        font-weight: 700;
        color: var(--blue-dark);
        font-size: 1.1rem;
    }
    .day-expense {
        color: var(--red);
        font-size: 0.85rem;
        font-weight: 600;
    }
    .day-income {
        color: var(--green);
        font-size: 0.85rem;
        font-weight: 600;
    }
    .weekday-header {
        text-align: center;
        font-weight: 700;
        color: var(--blue-dark);
        padding: 10px;
        background: linear-gradient(135deg, #1B3A5C 0%, #2E6DA4 100%);
        color: white !important;
        border-radius: 8px;
        margin: 2px;
    }
    .calendar-empty {
        background: #F8F9FA;
        opacity: 0.5;
    }
    .insight-card {
        background: linear-gradient(135deg, #FFFFFF 0%, #F4F7FB 100%);
        border: 1px solid var(--grey-light);
        border-radius: 12px;
        padding: 16px;
        margin: 8px 0;
    }
    .insight-title {
        color: var(--blue-mid);
        font-weight: 600;
        font-size: 0.9rem;
        margin-bottom: 8px;
    }
    .insight-value {
        color: var(--blue-dark);
        font-weight: 700;
        font-size: 1.3rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Load data ─────────────────────────────────────────────────────────────────
transactions = get_transactions()

# Build DataFrame
if transactions:
    df = pd.DataFrame(transactions)
    df["date"] = pd.to_datetime(df["date"])
    df["montant"] = pd.to_numeric(df["montant"], errors="coerce").fillna(0)
else:
    df = pd.DataFrame(columns=["id", "type", "montant", "categorie", "description", "date"])

# ── Page header ───────────────────────────────────────────────────────────────
st.title("📅 Calendrier Intelligent")

today = date.today()

# Month/Year selector
col_nav1, col_nav2, col_nav3, col_nav4 = st.columns([1, 2, 2, 1])

with col_nav1:
    if st.button("◀️ Mois précédent"):
        if "cal_month" not in st.session_state:
            st.session_state.cal_month = today.month
            st.session_state.cal_year = today.year
        if st.session_state.cal_month == 1:
            st.session_state.cal_month = 12
            st.session_state.cal_year -= 1
        else:
            st.session_state.cal_month -= 1
        st.rerun()

with col_nav4:
    if st.button("Mois suivant ▶️"):
        if "cal_month" not in st.session_state:
            st.session_state.cal_month = today.month
            st.session_state.cal_year = today.year
        if st.session_state.cal_month == 12:
            st.session_state.cal_month = 1
            st.session_state.cal_year += 1
        else:
            st.session_state.cal_month += 1
        st.rerun()

# Initialize session state
if "cal_month" not in st.session_state:
    st.session_state.cal_month = today.month
    st.session_state.cal_year = today.year

current_month = st.session_state.cal_month
current_year = st.session_state.cal_year

# French month names
months_fr = {
    1: "Janvier", 2: "Février", 3: "Mars", 4: "Avril",
    5: "Mai", 6: "Juin", 7: "Juillet", 8: "Août",
    9: "Septembre", 10: "Octobre", 11: "Novembre", 12: "Décembre",
}

with col_nav2:
    selected_month = st.selectbox(
        "Mois",
        list(months_fr.keys()),
        format_func=lambda x: months_fr[x],
        index=current_month - 1,
        key="month_select",
        label_visibility="collapsed",
    )
    if selected_month != current_month:
        st.session_state.cal_month = selected_month
        st.rerun()

with col_nav3:
    years_available = list(range(today.year - 5, today.year + 2))
    selected_year = st.selectbox(
        "Année",
        years_available,
        index=years_available.index(current_year) if current_year in years_available else len(years_available) - 1,
        key="year_select",
        label_visibility="collapsed",
    )
    if selected_year != current_year:
        st.session_state.cal_year = selected_year
        st.rerun()

st.markdown(f"### 📆 {months_fr[current_month]} {current_year}")

# ── Filter data for current month ─────────────────────────────────────────────
if not df.empty:
    df_month = df[
        (df["date"].dt.month == current_month) & 
        (df["date"].dt.year == current_year)
    ]
else:
    df_month = df

# ── Monthly KPIs ──────────────────────────────────────────────────────────────
depenses_mois = df_month[df_month["type"] == "depense"]["montant"].sum() if not df_month.empty else 0.0
revenus_mois = df_month[df_month["type"] == "revenu"]["montant"].sum() if not df_month.empty else 0.0
solde_mois = revenus_mois - depenses_mois
nb_transactions = len(df_month)

col_k1, col_k2, col_k3, col_k4 = st.columns(4)
col_k1.metric("💸 Dépenses du mois", f"{depenses_mois:,.0f} FCFA")
col_k2.metric("💰 Revenus du mois", f"{revenus_mois:,.0f} FCFA")
col_k3.metric("📊 Solde", f"{solde_mois:,.0f} FCFA", delta_color="normal")
col_k4.metric("📝 Transactions", f"{nb_transactions}")

st.markdown("---")

# ── Build calendar ────────────────────────────────────────────────────────────
cal = calendar.Calendar(firstweekday=0)  # Monday first
month_days = cal.monthdayscalendar(current_year, current_month)

# Aggregate transactions by day
daily_data = {}
if not df_month.empty:
    for _, row in df_month.iterrows():
        day = row["date"].day
        if day not in daily_data:
            daily_data[day] = {"depenses": 0, "revenus": 0, "transactions": []}
        if row["type"] == "depense":
            daily_data[day]["depenses"] += row["montant"]
        else:
            daily_data[day]["revenus"] += row["montant"]
        daily_data[day]["transactions"].append(row)

# Weekday headers
weekdays = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]
header_cols = st.columns(7)
for i, day_name in enumerate(weekdays):
    header_cols[i].markdown(
        f'<div class="weekday-header">{day_name}</div>',
        unsafe_allow_html=True,
    )

# Calendar grid
for week in month_days:
    cols = st.columns(7)
    for i, day in enumerate(week):
        with cols[i]:
            if day == 0:
                st.markdown(
                    '<div class="calendar-day calendar-empty">&nbsp;</div>',
                    unsafe_allow_html=True,
                )
            else:
                # Determine day style
                is_today = (
                    day == today.day and 
                    current_month == today.month and 
                    current_year == today.year
                )
                
                data = daily_data.get(day, {"depenses": 0, "revenus": 0, "transactions": []})
                has_expense = data["depenses"] > 0
                has_income = data["revenus"] > 0
                
                # Build CSS classes
                classes = ["calendar-day"]
                if is_today:
                    classes.append("today")
                if has_expense and has_income:
                    classes.append("has-both")
                elif has_expense:
                    classes.append("has-expense")
                elif has_income:
                    classes.append("has-income")
                
                # Build content
                content = f'<div class="day-number">{day}</div>'
                if has_expense:
                    content += f'<div class="day-expense">-{data["depenses"]:,.0f}</div>'
                if has_income:
                    content += f'<div class="day-income">+{data["revenus"]:,.0f}</div>'
                
                st.markdown(
                    f'<div class="{" ".join(classes)}">{content}</div>',
                    unsafe_allow_html=True,
                )

st.markdown("---")

# ── Smart Insights ────────────────────────────────────────────────────────────
st.subheader("🧠 Insights Intelligents")

if df_month.empty:
    st.info("Aucune transaction pour ce mois. Ajoutez des données via la page **⚙️ Gestion**.")
else:
    col_ins1, col_ins2 = st.columns(2)
    
    with col_ins1:
        # Jour avec le plus de dépenses
        if daily_data:
            max_expense_day = max(
                [(d, v["depenses"]) for d, v in daily_data.items() if v["depenses"] > 0],
                key=lambda x: x[1],
                default=(None, 0)
            )
            if max_expense_day[0]:
                st.markdown(
                    f"""
                    <div class="insight-card">
                        <div class="insight-title">📉 Jour avec le plus de dépenses</div>
                        <div class="insight-value">{max_expense_day[0]} {months_fr[current_month]}</div>
                        <div style="color: #E74C3C; font-weight: 600;">{max_expense_day[1]:,.0f} FCFA</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        
        # Catégorie la plus dépensière
        if not df_month[df_month["type"] == "depense"].empty:
            top_cat = (
                df_month[df_month["type"] == "depense"]
                .groupby("categorie")["montant"]
                .sum()
                .idxmax()
            )
            top_cat_amount = (
                df_month[df_month["type"] == "depense"]
                .groupby("categorie")["montant"]
                .sum()
                .max()
            )
            st.markdown(
                f"""
                <div class="insight-card">
                    <div class="insight-title">🏷️ Catégorie principale de dépenses</div>
                    <div class="insight-value">{top_cat}</div>
                    <div style="color: #7A8C9E;">{top_cat_amount:,.0f} FCFA ({top_cat_amount/depenses_mois*100:.1f}%)</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        
        # Moyenne journalière
        days_with_expense = len([d for d, v in daily_data.items() if v["depenses"] > 0])
        if days_with_expense > 0:
            avg_daily = depenses_mois / days_with_expense
            st.markdown(
                f"""
                <div class="insight-card">
                    <div class="insight-title">📊 Moyenne des jours avec dépenses</div>
                    <div class="insight-value">{avg_daily:,.0f} FCFA/jour</div>
                    <div style="color: #7A8C9E;">Sur {days_with_expense} jours actifs</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    
    with col_ins2:
        # Jour avec le plus de revenus
        max_income_day = max(
            [(d, v["revenus"]) for d, v in daily_data.items() if v["revenus"] > 0],
            key=lambda x: x[1],
            default=(None, 0)
        )
        if max_income_day[0]:
            st.markdown(
                f"""
                <div class="insight-card">
                    <div class="insight-title">📈 Jour avec le plus de revenus</div>
                    <div class="insight-value">{max_income_day[0]} {months_fr[current_month]}</div>
                    <div style="color: #2ECC71; font-weight: 600;">{max_income_day[1]:,.0f} FCFA</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        
        # Tendance semaine
        df_month_sorted = df_month.copy()
        df_month_sorted["week"] = df_month_sorted["date"].dt.isocalendar().week
        weekly_expenses = (
            df_month_sorted[df_month_sorted["type"] == "depense"]
            .groupby("week")["montant"]
            .sum()
        )
        if len(weekly_expenses) >= 2:
            trend = weekly_expenses.iloc[-1] - weekly_expenses.iloc[-2]
            trend_emoji = "📉" if trend < 0 else "📈"
            trend_color = "#2ECC71" if trend < 0 else "#E74C3C"
            st.markdown(
                f"""
                <div class="insight-card">
                    <div class="insight-title">{trend_emoji} Tendance hebdomadaire</div>
                    <div class="insight-value" style="color: {trend_color};">{trend:+,.0f} FCFA</div>
                    <div style="color: #7A8C9E;">vs semaine précédente</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        
        # Prévision fin de mois
        days_passed = min(today.day, calendar.monthrange(current_year, current_month)[1])
        if current_month == today.month and current_year == today.year and days_passed > 0:
            total_days = calendar.monthrange(current_year, current_month)[1]
            projected = (depenses_mois / days_passed) * total_days
            st.markdown(
                f"""
                <div class="insight-card">
                    <div class="insight-title">🔮 Projection fin de mois</div>
                    <div class="insight-value">{projected:,.0f} FCFA</div>
                    <div style="color: #7A8C9E;">Si le rythme actuel se maintient</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

st.markdown("---")

# ── Daily details (selected day) ──────────────────────────────────────────────
st.subheader("📋 Détails par jour")

if not df_month.empty:
    available_days = sorted(daily_data.keys())
    if available_days:
        selected_day = st.selectbox(
            "Sélectionner un jour pour voir les détails",
            available_days,
            format_func=lambda x: f"{x} {months_fr[current_month]} {current_year}",
            key="day_select",
        )
        
        day_transactions = daily_data[selected_day]["transactions"]
        
        col_d1, col_d2, col_d3 = st.columns(3)
        col_d1.metric(
            f"💸 Dépenses du {selected_day}",
            f"{daily_data[selected_day]['depenses']:,.0f} FCFA"
        )
        col_d2.metric(
            f"💰 Revenus du {selected_day}",
            f"{daily_data[selected_day]['revenus']:,.0f} FCFA"
        )
        col_d3.metric(
            "📝 Nombre de transactions",
            len(day_transactions)
        )
        
        if day_transactions:
            st.markdown("##### Transactions du jour")
            for tx in day_transactions:
                emoji = "💸" if tx["type"] == "depense" else "💰"
                color = "#E74C3C" if tx["type"] == "depense" else "#2ECC71"
                sign = "-" if tx["type"] == "depense" else "+"
                desc = f" – {tx['description']}" if tx["description"] else ""
                st.markdown(
                    f"""
                    <div style="background: white; padding: 12px 16px; border-radius: 8px; 
                                margin: 8px 0; border-left: 4px solid {color};
                                box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                        <span style="font-weight: 600;">{emoji} {tx['categorie']}</span>
                        <span style="float: right; color: {color}; font-weight: 700;">
                            {sign}{float(tx['montant']):,.0f} FCFA
                        </span>
                        <div style="color: #7A8C9E; font-size: 0.85rem; margin-top: 4px;">
                            {desc if desc else "Pas de description"}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
    else:
        st.info("Aucune transaction avec des montants pour ce mois.")
else:
    st.info("Sélectionnez un mois avec des transactions pour voir les détails journaliers.")
