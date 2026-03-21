"""
Notification system for the budget tracking application.
Generates and manages user notifications based on spending patterns.
"""

from datetime import date, datetime, timedelta
from data.auth import add_notification, get_user_preferences, clear_notifications
from data.data_manager import get_transactions, get_budget


def generate_notifications(username: str) -> None:
    """
    Generate notifications for a user based on their spending data.
    Clears old notifications and recreates them fresh.
    """
    clear_notifications(username)

    transactions = get_transactions()
    budget = get_budget()
    today = date.today()
    current_month = today.strftime("%Y-%m")

    # ── Budget overage alerts ──────────────────────────────────────────────────
    limites = budget.get("limites", {})
    monthly_depenses: dict[str, float] = {}
    for tx in transactions:
        if tx["type"] == "depense" and str(tx["date"]).startswith(current_month):
            cat = tx["categorie"]
            monthly_depenses[cat] = monthly_depenses.get(cat, 0.0) + tx["montant"]

    for cat, limite in limites.items():
        if limite > 0:
            spent = monthly_depenses.get(cat, 0.0)
            if spent > limite:
                pct = int((spent / limite) * 100)
                add_notification(
                    username,
                    "budget_alert",
                    f"⚠️ Dépassement – {cat}",
                    f"Vous avez dépensé {spent:,.0f} FCFA sur {cat} ce mois ({pct}% du budget).",
                )
            elif spent >= 0.8 * limite:
                pct = int((spent / limite) * 100)
                add_notification(
                    username,
                    "budget_warning",
                    f"📊 Alerte budget – {cat}",
                    f"Vous avez consommé {pct}% de votre budget {cat} ce mois.",
                )

    # ── No transactions this week reminder ─────────────────────────────────────
    week_start = today.toordinal() - today.weekday()
    recent = [
        tx for tx in transactions
        if date.fromisoformat(str(tx["date"])).toordinal() >= week_start
    ]
    if not recent:
        add_notification(
            username,
            "reminder",
            "📝 Rappel de saisie",
            "Vous n'avez pas enregistré de transactions cette semaine. "
            "Pensez à mettre à jour votre budget !",
        )

    # ── Negative trend alert ───────────────────────────────────────────────────
    last_month = (today.replace(day=1) - timedelta(days=1)).strftime("%Y-%m")
    depenses_this = sum(
        tx["montant"] for tx in transactions
        if tx["type"] == "depense" and str(tx["date"]).startswith(current_month)
    )
    depenses_last = sum(
        tx["montant"] for tx in transactions
        if tx["type"] == "depense" and str(tx["date"]).startswith(last_month)
    )
    if depenses_last > 0 and depenses_this > depenses_last * 1.2:
        pct = int(((depenses_this - depenses_last) / depenses_last) * 100)
        add_notification(
            username,
            "trend_alert",
            "📈 Tendance à la hausse",
            f"Vos dépenses ce mois sont en hausse de {pct}% par rapport au mois dernier.",
        )

    # ── Personalised tip ──────────────────────────────────────────────────────
    if monthly_depenses:
        top_cat = max(monthly_depenses, key=monthly_depenses.get)
        add_notification(
            username,
            "tip",
            "💡 Conseil personnalisé",
            f"Votre plus grosse dépense ce mois est en « {top_cat} » "
            f"({monthly_depenses[top_cat]:,.0f} FCFA). "
            "Cherchez des opportunités d'économies dans cette catégorie.",
        )


def get_unread_count(username: str) -> int:
    """Return the number of unread notifications for a user."""
    prefs = get_user_preferences(username)
    notifications = prefs.get("notifications", [])
    read_ids = set(prefs.get("notifications_read", []))
    return sum(1 for n in notifications if n["id"] not in read_ids)


def get_notifications(username: str) -> list[dict]:
    """Return all notifications for a user, newest first."""
    prefs = get_user_preferences(username)
    notifications = prefs.get("notifications", [])
    return list(reversed(notifications))
