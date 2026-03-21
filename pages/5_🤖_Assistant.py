"""
Assistant IA – Chatbot Anthropic dédié au suivi des dépenses.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from data.auth import get_user_preferences
from data.data_manager import get_transactions, get_budget, get_categories
from utils.components import check_authentication, get_shared_css

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Assistant IA – Suivi de Dépenses",
    page_icon="🤖",
    layout="wide",
)

st.markdown(f"<style>{get_shared_css()}</style>", unsafe_allow_html=True)

# ── Authentication ────────────────────────────────────────────────────────────
username = check_authentication()

# ── Agent configuration ───────────────────────────────────────────────────────
AGENT_DESCRIPTION = (
    "Je suis votre assistant personnel de gestion financière. "
    "Je vous aide à optimiser vos dépenses, analyser vos habitudes "
    "et atteindre vos objectifs budgétaires."
)

SYSTEM_PROMPT = """Tu es un assistant financier personnel expert en gestion de budget et en suivi des dépenses.
Ton rôle est d'aider l'utilisateur à :
- Analyser ses habitudes de dépenses et identifier les tendances
- Optimiser son budget par catégorie
- Recevoir des conseils pratiques et personnalisés pour économiser
- Comprendre ses revenus et dépenses mensuels
- Atteindre ses objectifs financiers

Réponds toujours en français, de manière claire, concise et bienveillante.
Utilise les données fournies dans le contexte pour donner des conseils personnalisés.
Si les données sont absentes, fournis des conseils généraux de bonne gestion financière.
"""

SUGGESTED_QUERIES = [
    "Comment puis-je réduire mes dépenses alimentaires ?",
    "Analyse mes dépenses du mois dernier",
    "Quelles catégories dépassent mon budget ?",
    "Conseils pour économiser sur le transport",
    "Comment optimiser mon budget mensuel ?",
]


def _build_context(username: str) -> str:
    """Build a text summary of the user's financial data to inject into the prompt."""
    from datetime import date, timedelta

    transactions = get_transactions()
    budget = get_budget()

    today = date.today()
    current_month = today.strftime("%Y-%m")
    last_month = (today.replace(day=1) - timedelta(days=1)).strftime("%Y-%m")

    def summarise(month: str) -> dict:
        txs = [t for t in transactions if str(t["date"]).startswith(month)]
        rev = sum(t["montant"] for t in txs if t["type"] == "revenu")
        dep = sum(t["montant"] for t in txs if t["type"] == "depense")
        cats: dict[str, float] = {}
        for t in txs:
            if t["type"] == "depense":
                cats[t["categorie"]] = cats.get(t["categorie"], 0.0) + t["montant"]
        return {"revenus": rev, "depenses": dep, "categories": cats}

    this = summarise(current_month)
    last = summarise(last_month)

    limites = budget.get("limites", {})
    budget_lines = (
        "\n".join(f"  - {cat}: {lim:,.0f} FCFA" for cat, lim in limites.items())
        if limites
        else "  Aucun budget défini"
    )

    context = f"""=== Données financières de {username} ===

Mois en cours ({current_month}) :
  Revenus : {this['revenus']:,.0f} FCFA
  Dépenses : {this['depenses']:,.0f} FCFA
  Solde : {this['revenus'] - this['depenses']:+,.0f} FCFA
  Dépenses par catégorie :
""" + "\n".join(f"    - {c}: {v:,.0f} FCFA" for c, v in this["categories"].items()) + f"""

Mois précédent ({last_month}) :
  Revenus : {last['revenus']:,.0f} FCFA
  Dépenses : {last['depenses']:,.0f} FCFA

Limites de budget mensuelles :
{budget_lines}
"""
    return context


def _send_message(api_key: str, model: str, messages: list) -> str:
    """Send a message to the Anthropic API and return the response text."""
    try:
        import anthropic

        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model=model,
            max_tokens=1024,
            system=SYSTEM_PROMPT + "\n\n" + _build_context(username),
            messages=messages,
        )
        return response.content[0].text
    except ImportError:
        return (
            "❌ Le module `anthropic` n'est pas installé. "
            "Veuillez exécuter `pip install anthropic` et redémarrer l'application."
        )
    except Exception:  # noqa: BLE001
        return "❌ Une erreur s'est produite lors de la communication avec l'API Anthropic. Vérifiez votre clé API et réessayez."


# ── UI ────────────────────────────────────────────────────────────────────────
st.title("🤖 Assistant IA – Gestion Financière")
st.markdown(
    f"""
    <div style="background:linear-gradient(135deg,#1B3A5C,#2E6DA4); color:#fff;
                padding:16px 20px; border-radius:12px; margin-bottom:1.5rem;">
        <strong>🤖 Votre Assistant Personnel</strong><br/>
        <span style="opacity:0.9; font-size:0.9rem;">{AGENT_DESCRIPTION}</span>
    </div>
    """,
    unsafe_allow_html=True,
)

# Retrieve API key & model from preferences
prefs = get_user_preferences(username)
api_key = prefs.get("anthropic_api_key", "")
model = prefs.get("anthropic_model", "claude-3-haiku-20240307")

if not api_key:
    st.warning(
        "⚙️ Aucune clé API Anthropic configurée. "
        "Veuillez la renseigner dans le **sidebar → 🤖 Configuration IA**."
    )

# ── Suggested queries ─────────────────────────────────────────────────────────
st.markdown("**💡 Requêtes suggérées :**")
cols = st.columns(len(SUGGESTED_QUERIES))
for col, query in zip(cols, SUGGESTED_QUERIES):
    with col:
        if st.button(query, key=f"suggest_{query[:20]}", use_container_width=True):
            st.session_state.setdefault("chat_messages", [])
            st.session_state["chat_messages"].append({"role": "user", "content": query})
            st.session_state["pending_send"] = True

st.markdown("---")

# ── Chat history ──────────────────────────────────────────────────────────────
if "chat_messages" not in st.session_state:
    st.session_state["chat_messages"] = []

# Display existing messages
for msg in st.session_state["chat_messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Auto-send if a suggested query was clicked
if st.session_state.pop("pending_send", False) and api_key:
    last_user_msg = st.session_state["chat_messages"][-1]
    with st.chat_message("user"):
        st.markdown(last_user_msg["content"])
    with st.chat_message("assistant"):
        with st.spinner("Réflexion en cours…"):
            reply = _send_message(api_key, model, st.session_state["chat_messages"])
        st.markdown(reply)
    st.session_state["chat_messages"].append({"role": "assistant", "content": reply})

# Standard chat input
if prompt := st.chat_input("Posez votre question financière…"):
    st.session_state["chat_messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    if not api_key:
        with st.chat_message("assistant"):
            st.warning(
                "⚙️ Veuillez d'abord configurer votre clé API Anthropic dans le sidebar."
            )
    else:
        with st.chat_message("assistant"):
            with st.spinner("Réflexion en cours…"):
                reply = _send_message(api_key, model, st.session_state["chat_messages"])
            st.markdown(reply)
        st.session_state["chat_messages"].append({"role": "assistant", "content": reply})

# ── Clear button ──────────────────────────────────────────────────────────────
if st.session_state["chat_messages"]:
    if st.button("🗑️ Effacer la conversation", key="clear_chat"):
        st.session_state["chat_messages"] = []
        st.rerun()
