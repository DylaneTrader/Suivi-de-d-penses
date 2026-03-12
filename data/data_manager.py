"""
Data manager module for the budget tracking application.
Handles persistence using a local JSON file.
"""

import json
import os
import uuid
from datetime import date

DATA_FILE = os.path.join(os.path.dirname(__file__), "budget_data.json")

DEFAULT_CATEGORIES = {
    "depenses": ["Alimentation", "Transport", "Logement", "Santé", "Loisirs", "Vêtements", "Autre"],
    "revenus": ["Salaire", "Freelance", "Investissements", "Autre"],
}

DEFAULT_DATA = {
    "transactions": [],
    "categories": DEFAULT_CATEGORIES,
    "budget": {
        "revenu_mensuel_cible": 0.0,
        "limites": {},
        "objectifs": {},
    },
}


def _load() -> dict:
    if not os.path.exists(DATA_FILE):
        _save(DEFAULT_DATA)
        return DEFAULT_DATA
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    # Ensure all keys exist (backwards compatibility)
    for key, value in DEFAULT_DATA.items():
        if key not in data:
            data[key] = value
    if "depenses" not in data["categories"]:
        data["categories"]["depenses"] = DEFAULT_CATEGORIES["depenses"]
    if "revenus" not in data["categories"]:
        data["categories"]["revenus"] = DEFAULT_CATEGORIES["revenus"]
    return data


def _save(data: dict) -> None:
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)


def get_all_data() -> dict:
    return _load()


def get_transactions() -> list:
    return _load()["transactions"]


def add_transaction(type_: str, montant: float, categorie: str, description: str, date_: date) -> None:
    data = _load()
    data["transactions"].append(
        {
            "id": str(uuid.uuid4()),
            "type": type_,
            "montant": montant,
            "categorie": categorie,
            "description": description,
            "date": str(date_),
        }
    )
    _save(data)


def delete_transaction(transaction_id: str) -> None:
    data = _load()
    data["transactions"] = [t for t in data["transactions"] if t["id"] != transaction_id]
    _save(data)


def get_categories() -> dict:
    return _load()["categories"]


def add_category(type_: str, name: str) -> bool:
    """Add a new category. Returns True if added, False if already exists."""
    data = _load()
    key = "depenses" if type_ == "depense" else "revenus"
    if name in data["categories"][key]:
        return False
    data["categories"][key].append(name)
    _save(data)
    return True


def delete_category(type_: str, name: str) -> None:
    data = _load()
    key = "depenses" if type_ == "depense" else "revenus"
    data["categories"][key] = [c for c in data["categories"][key] if c != name]
    _save(data)


def get_budget() -> dict:
    return _load()["budget"]


def save_budget(revenu_mensuel_cible: float, limites: dict, objectifs: dict) -> None:
    data = _load()
    data["budget"]["revenu_mensuel_cible"] = revenu_mensuel_cible
    data["budget"]["limites"] = limites
    data["budget"]["objectifs"] = objectifs
    _save(data)
