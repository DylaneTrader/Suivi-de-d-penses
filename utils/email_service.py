"""
Email service for weekly budget reports.
Sends HTML email summaries via SMTP.
"""

import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import date, timedelta
from data.auth import (
    get_user_preferences,
    get_user_email,
    save_user_preferences,
    set_last_weekly_report,
)
from data.data_manager import get_transactions, get_budget


# ── Default SMTP configuration ─────────────────────────────────────────────────
DEFAULT_SMTP = {
    "server": "smtp.gmail.com",
    "port": 587,
    "email": "",
    "password": "",
}


def _transactions_for_period(transactions: list, start: date, end: date) -> list:
    """Filter transactions within [start, end] inclusive."""
    return [
        tx for tx in transactions
        if start <= date.fromisoformat(str(tx["date"])) <= end
    ]


def _build_html_report(username: str, week_start: date, week_end: date) -> str:
    """Build an HTML weekly report for the given user and week."""
    transactions = get_transactions()
    budget = get_budget()

    this_week = _transactions_for_period(transactions, week_start, week_end)
    prev_start = week_start - timedelta(days=7)
    prev_end = week_end - timedelta(days=7)
    last_week = _transactions_for_period(transactions, prev_start, prev_end)

    # Totals
    rev_this = sum(t["montant"] for t in this_week if t["type"] == "revenu")
    dep_this = sum(t["montant"] for t in this_week if t["type"] == "depense")
    rev_last = sum(t["montant"] for t in last_week if t["type"] == "revenu")
    dep_last = sum(t["montant"] for t in last_week if t["type"] == "depense")

    solde_this = rev_this - dep_this

    def pct_change(new, old, higher_is_bad: bool = True):
        if old == 0:
            return "—"
        delta = ((new - old) / old) * 100
        sign = "+" if delta > 0 else ""
        color = "#E74C3C" if (delta > 0) == higher_is_bad else "#2ECC71"
        return f'<span style="color:{color}">{sign}{delta:.1f}%</span>'

    # Top 3 categories
    cat_spend: dict[str, float] = {}
    for t in this_week:
        if t["type"] == "depense":
            cat_spend[t["categorie"]] = cat_spend.get(t["categorie"], 0.0) + t["montant"]
    top3 = sorted(cat_spend.items(), key=lambda x: x[1], reverse=True)[:3]
    top3_rows = "".join(
        f"<tr><td style='padding:6px 12px;'>{cat}</td>"
        f"<td style='padding:6px 12px; text-align:right;'>{amount:,.0f} FCFA</td></tr>"
        for cat, amount in top3
    ) or "<tr><td colspan='2' style='padding:6px 12px; color:#7A8C9E;'>Aucune dépense cette semaine</td></tr>"

    # Budget alerts
    limites = budget.get("limites", {})
    month_str = week_start.strftime("%Y-%m")
    monthly_dep: dict[str, float] = {}
    for t in transactions:
        if t["type"] == "depense" and str(t["date"]).startswith(month_str):
            monthly_dep[t["categorie"]] = monthly_dep.get(t["categorie"], 0.0) + t["montant"]

    alerts_html = ""
    for cat, limite in limites.items():
        if limite > 0 and monthly_dep.get(cat, 0) > limite:
            alerts_html += (
                f"<li>⚠️ <strong>{cat}</strong> : {monthly_dep[cat]:,.0f} FCFA dépensés "
                f"sur {limite:,.0f} FCFA de budget.</li>"
            )
    alerts_section = (
        f"<ul style='margin:0; padding-left:20px;'>{alerts_html}</ul>"
        if alerts_html
        else "<p style='color:#2ECC71;'>✅ Aucun dépassement de budget ce mois.</p>"
    )

    html = f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
      <meta charset="UTF-8" />
      <title>Rapport hebdomadaire – Suivi de Dépenses</title>
    </head>
    <body style="font-family:Arial,sans-serif; background:#F4F7FB; margin:0; padding:20px;">
      <div style="max-width:600px; margin:0 auto; background:#fff; border-radius:12px;
                  box-shadow:0 4px 20px rgba(27,58,92,0.12); overflow:hidden;">
        <!-- Header -->
        <div style="background:linear-gradient(135deg,#1B3A5C,#2E6DA4); padding:24px; text-align:center;">
          <h1 style="color:#fff; margin:0; font-size:1.5rem;">💰 Rapport Hebdomadaire</h1>
          <p style="color:rgba(255,255,255,0.8); margin:4px 0 0;">
            {week_start.strftime("%d/%m/%Y")} – {week_end.strftime("%d/%m/%Y")}
          </p>
          <p style="color:rgba(255,255,255,0.7); margin:2px 0 0; font-size:0.9rem;">
            Bonjour <strong>{username}</strong> 👋
          </p>
        </div>

        <!-- Summary -->
        <div style="padding:24px;">
          <h2 style="color:#1B3A5C; margin-top:0;">📊 Résumé de la semaine</h2>
          <table style="width:100%; border-collapse:collapse;">
            <tr style="background:#F4F7FB;">
              <th style="padding:10px 12px; text-align:left; color:#7A8C9E; font-size:0.85rem;">Indicateur</th>
              <th style="padding:10px 12px; text-align:right; color:#7A8C9E; font-size:0.85rem;">Cette semaine</th>
              <th style="padding:10px 12px; text-align:right; color:#7A8C9E; font-size:0.85rem;">Variation</th>
            </tr>
            <tr>
              <td style="padding:10px 12px; border-top:1px solid #C8D4DF;">💰 Revenus</td>
              <td style="padding:10px 12px; text-align:right; border-top:1px solid #C8D4DF; font-weight:700;
                         color:#2ECC71;">{rev_this:,.0f} FCFA</td>
              <td style="padding:10px 12px; text-align:right; border-top:1px solid #C8D4DF;">
                {pct_change(rev_this, rev_last, higher_is_bad=False)}</td>
            </tr>
            <tr style="background:#F4F7FB;">
              <td style="padding:10px 12px; border-top:1px solid #C8D4DF;">💸 Dépenses</td>
              <td style="padding:10px 12px; text-align:right; border-top:1px solid #C8D4DF; font-weight:700;
                         color:#E74C3C;">{dep_this:,.0f} FCFA</td>
              <td style="padding:10px 12px; text-align:right; border-top:1px solid #C8D4DF;">
                {pct_change(dep_this, dep_last)}</td>
            </tr>
            <tr>
              <td style="padding:10px 12px; border-top:1px solid #C8D4DF; font-weight:700;">📈 Solde net</td>
              <td style="padding:10px 12px; text-align:right; border-top:1px solid #C8D4DF; font-weight:700;
                         color:{'#2ECC71' if solde_this >= 0 else '#E74C3C'};">
                {solde_this:+,.0f} FCFA</td>
              <td style="padding:10px 12px; border-top:1px solid #C8D4DF;"></td>
            </tr>
          </table>

          <!-- Top 3 categories -->
          <h2 style="color:#1B3A5C; margin-top:24px;">🏆 Top 3 des catégories de dépenses</h2>
          <table style="width:100%; border-collapse:collapse;">
            <tr style="background:#F4F7FB;">
              <th style="padding:6px 12px; text-align:left; color:#7A8C9E; font-size:0.85rem;">Catégorie</th>
              <th style="padding:6px 12px; text-align:right; color:#7A8C9E; font-size:0.85rem;">Montant</th>
            </tr>
            {top3_rows}
          </table>

          <!-- Budget alerts -->
          <h2 style="color:#1B3A5C; margin-top:24px;">⚠️ Alertes budget du mois</h2>
          {alerts_section}

          <!-- Tip -->
          <div style="background:#F4F7FB; border-left:4px solid #2E6DA4; padding:12px 16px;
                      border-radius:4px; margin-top:24px;">
            <strong style="color:#1B3A5C;">💡 Conseil</strong>
            <p style="margin:4px 0 0; color:#3D4B5C; font-size:0.9rem;">
              Pensez à revoir vos abonnements et dépenses récurrentes chaque mois
              pour identifier les économies potentielles.
            </p>
          </div>
        </div>

        <!-- Footer -->
        <div style="background:#F4F7FB; padding:16px 24px; text-align:center;
                    color:#7A8C9E; font-size:0.8rem;">
          Suivi de Dépenses – Budget Personnel<br/>
          Ce rapport est généré automatiquement chaque lundi.
        </div>
      </div>
    </body>
    </html>
    """
    return html


def send_weekly_report(username: str) -> tuple[bool, str]:
    """
    Send the weekly report email for a user.
    Returns (success, message).
    """
    prefs = get_user_preferences(username)
    email = get_user_email(username)

    if not email:
        return False, "Aucune adresse email configurée pour cet utilisateur."

    if not prefs.get("email_reports_enabled", False):
        return False, "Les rapports par email sont désactivés."

    smtp_cfg = prefs.get("smtp_config") or {}
    server = smtp_cfg.get("server") or DEFAULT_SMTP["server"]
    port = int(smtp_cfg.get("port") or DEFAULT_SMTP["port"])
    smtp_email = smtp_cfg.get("email") or ""
    smtp_password = smtp_cfg.get("password") or ""

    if not smtp_email or not smtp_password:
        return False, "Configuration SMTP incomplète (email/mot de passe manquant)."

    # Week: Mon–Sun of previous week
    today = date.today()
    week_start = today - timedelta(days=today.weekday() + 7)
    week_end = week_start + timedelta(days=6)

    html_body = _build_html_report(username, week_start, week_end)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = (
        f"📊 Rapport hebdomadaire – {week_start.strftime('%d/%m')} au {week_end.strftime('%d/%m/%Y')}"
    )
    msg["From"] = smtp_email
    msg["To"] = email
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP(server, port) as smtp:
            smtp.ehlo()
            smtp.starttls(context=context)
            smtp.login(smtp_email, smtp_password)
            smtp.sendmail(smtp_email, email, msg.as_string())
        set_last_weekly_report(username)
        return True, f"Rapport envoyé avec succès à {email}."
    except smtplib.SMTPAuthenticationError:
        return False, "Échec d'authentification SMTP. Vérifiez vos identifiants."
    except smtplib.SMTPConnectError:
        return False, "Impossible de se connecter au serveur SMTP. Vérifiez le serveur et le port."
    except Exception:  # noqa: BLE001
        return False, "Une erreur inattendue s'est produite lors de l'envoi de l'email."


def should_send_weekly_report(username: str) -> bool:
    """
    Return True if today is Monday and the report hasn't been sent this week.
    """
    today = date.today()
    if today.weekday() != 0:  # 0 = Monday
        return False
    prefs = get_user_preferences(username)
    last_sent = prefs.get("last_weekly_report")
    if not last_sent:
        return True
    last_date = date.fromisoformat(str(last_sent)[:10])
    # Don't send twice in the same week
    return last_date < today - timedelta(days=7)
