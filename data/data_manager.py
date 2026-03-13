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
        "revenu_mensuel_cible": 0.0,  # Legacy, kept for backward compatibility
        "revenus_mensuels": {},  # New: revenus par catégorie {"Salaire": 500000, ...}
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


def rename_category(type_: str, old_name: str, new_name: str) -> bool:
    """Rename a category. Returns True if renamed, False if new name already exists or old not found."""
    data = _load()
    key = "depenses" if type_ == "depense" else "revenus"
    
    # Check if old category exists
    if old_name not in data["categories"][key]:
        return False
    
    # Check if new name already exists
    if new_name in data["categories"][key]:
        return False
    
    # Rename in categories list
    data["categories"][key] = [new_name if c == old_name else c for c in data["categories"][key]]
    
    # Update all transactions with this category
    for tx in data["transactions"]:
        if tx["categorie"] == old_name:
            tx["categorie"] = new_name
    
    # Update budget limites (for depenses)
    if type_ == "depense" and old_name in data["budget"].get("limites", {}):
        data["budget"]["limites"][new_name] = data["budget"]["limites"].pop(old_name)
    
    # Update budget objectifs (for revenus)
    if type_ == "revenu" and old_name in data["budget"].get("objectifs", {}):
        data["budget"]["objectifs"][new_name] = data["budget"]["objectifs"].pop(old_name)
    
    # Update revenus_mensuels (for revenus)
    if type_ == "revenu" and old_name in data["budget"].get("revenus_mensuels", {}):
        data["budget"]["revenus_mensuels"][new_name] = data["budget"]["revenus_mensuels"].pop(old_name)
    
    _save(data)
    return True


def get_budget() -> dict:
    return _load()["budget"]


def save_budget(revenus_mensuels: dict, limites: dict, objectifs: dict) -> None:
    data = _load()
    data["budget"]["revenus_mensuels"] = revenus_mensuels
    # Calculer le total pour backward compatibility
    data["budget"]["revenu_mensuel_cible"] = sum(revenus_mensuels.values())
    data["budget"]["limites"] = limites
    data["budget"]["objectifs"] = objectifs
    _save(data)
