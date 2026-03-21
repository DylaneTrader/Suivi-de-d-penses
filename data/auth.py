"""
Authentication module for user management.
Handles user registration, login, and session management.
"""

import json
import os
import hashlib
import secrets
import uuid
from datetime import datetime, timedelta

AUTH_FILE = os.path.join(os.path.dirname(__file__), "users.json")

DEFAULT_AUTH_DATA = {
    "users": {},
    "sessions": {},
}


def _hash_password(password: str, salt: str = None) -> tuple[str, str]:
    """Hash a password with a salt."""
    if salt is None:
        salt = secrets.token_hex(16)
    hashed = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000
    ).hex()
    return hashed, salt


def _load_auth() -> dict:
    """Load authentication data from file."""
    if not os.path.exists(AUTH_FILE):
        _save_auth(DEFAULT_AUTH_DATA)
        return DEFAULT_AUTH_DATA
    with open(AUTH_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_auth(data: dict) -> None:
    """Save authentication data to file."""
    with open(AUTH_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)


def register_user(username: str, password: str, email: str = "", anthropic_api_key: str = "") -> tuple[bool, str]:
    """
    Register a new user.
    Returns (success, message).
    """
    data = _load_auth()
    
    # Validate username
    if not username or len(username) < 3:
        return False, "Le nom d'utilisateur doit contenir au moins 3 caractères."
    
    if username.lower() in [u.lower() for u in data["users"].keys()]:
        return False, "Ce nom d'utilisateur existe déjà."
    
    # Validate password
    if not password or len(password) < 6:
        return False, "Le mot de passe doit contenir au moins 6 caractères."
    
    # Hash password
    hashed_password, salt = _hash_password(password)
    
    # Create user
    data["users"][username] = {
        "password_hash": hashed_password,
        "salt": salt,
        "email": email,
        "created_at": datetime.now().isoformat(),
        "last_login": None,
        "preferences": {
            "theme": "light",
            "widgets": ["depenses_ytd", "revenus_ytd", "solde", "depenses_mois"],
            "anthropic_api_key": anthropic_api_key,
            "anthropic_model": "claude-3-haiku-20240307",
            "notifications": [],
            "notifications_read": [],
            "email_reports_enabled": bool(email),
            "smtp_config": {},
            "last_weekly_report": None,
        }
    }
    
    _save_auth(data)
    return True, "Compte créé avec succès ! Vous pouvez maintenant vous connecter."


def authenticate(username: str, password: str) -> tuple[bool, str]:
    """
    Authenticate a user.
    Returns (success, message or session_token).
    """
    data = _load_auth()
    
    if username not in data["users"]:
        return False, "Nom d'utilisateur ou mot de passe incorrect."
    
    user = data["users"][username]
    hashed_password, _ = _hash_password(password, user["salt"])
    
    if hashed_password != user["password_hash"]:
        return False, "Nom d'utilisateur ou mot de passe incorrect."
    
    # Update last login
    data["users"][username]["last_login"] = datetime.now().isoformat()
    
    # Create session token
    session_token = secrets.token_hex(32)
    data["sessions"][session_token] = {
        "username": username,
        "created_at": datetime.now().isoformat(),
        "expires_at": (datetime.now() + timedelta(days=7)).isoformat(),
    }
    
    _save_auth(data)
    return True, session_token


def validate_session(session_token: str) -> tuple[bool, str]:
    """
    Validate a session token.
    Returns (valid, username or error message).
    """
    if not session_token:
        return False, "Session invalide."
    
    data = _load_auth()
    
    if session_token not in data["sessions"]:
        return False, "Session expirée. Veuillez vous reconnecter."
    
    session = data["sessions"][session_token]
    expires_at = datetime.fromisoformat(session["expires_at"])
    
    if datetime.now() > expires_at:
        # Clean up expired session
        del data["sessions"][session_token]
        _save_auth(data)
        return False, "Session expirée. Veuillez vous reconnecter."
    
    return True, session["username"]


def logout(session_token: str) -> None:
    """Logout user by invalidating session."""
    data = _load_auth()
    if session_token in data["sessions"]:
        del data["sessions"][session_token]
        _save_auth(data)


def change_password(username: str, old_password: str, new_password: str) -> tuple[bool, str]:
    """Change user password."""
    data = _load_auth()
    
    if username not in data["users"]:
        return False, "Utilisateur introuvable."
    
    user = data["users"][username]
    hashed_old, _ = _hash_password(old_password, user["salt"])
    
    if hashed_old != user["password_hash"]:
        return False, "Ancien mot de passe incorrect."
    
    if len(new_password) < 6:
        return False, "Le nouveau mot de passe doit contenir au moins 6 caractères."
    
    hashed_new, new_salt = _hash_password(new_password)
    data["users"][username]["password_hash"] = hashed_new
    data["users"][username]["salt"] = new_salt
    
    _save_auth(data)
    return True, "Mot de passe modifié avec succès."


def get_all_users() -> list:
    """Get list of all usernames (for admin purposes)."""
    data = _load_auth()
    return list(data["users"].keys())


def user_exists() -> bool:
    """Check if at least one user exists."""
    data = _load_auth()
    return len(data["users"]) > 0


def get_user_email(username: str) -> str:
    """Get a user's email address."""
    data = _load_auth()
    if username in data["users"]:
        return data["users"][username].get("email", "")
    return ""


def _ensure_new_prefs(prefs: dict) -> dict:
    """Ensure new preference fields exist with default values (backward-compat)."""
    defaults = {
        "anthropic_api_key": "",
        "anthropic_model": "claude-3-haiku-20240307",
        "notifications": [],
        "notifications_read": [],
        "email_reports_enabled": False,
        "smtp_config": {},
        "last_weekly_report": None,
    }
    for key, val in defaults.items():
        if key not in prefs:
            prefs[key] = val
    return prefs


def get_user_preferences(username: str) -> dict:
    """Get user preferences."""
    data = _load_auth()
    if username in data["users"]:
        prefs = data["users"][username].get("preferences", {})
        return _ensure_new_prefs(prefs)
    return _ensure_new_prefs({})


def save_user_preferences(username: str, preferences: dict) -> None:
    """Save user preferences."""
    data = _load_auth()
    if username in data["users"]:
        data["users"][username]["preferences"] = preferences
        _save_auth(data)


def add_notification(username: str, notif_type: str, title: str, message: str) -> None:
    """Add a notification to a user's preferences."""
    data = _load_auth()
    if username not in data["users"]:
        return
    prefs = data["users"][username].get("preferences", {})
    prefs = _ensure_new_prefs(prefs)
    notif = {
        "id": str(uuid.uuid4()),
        "type": notif_type,
        "title": title,
        "message": message,
        "created_at": datetime.now().isoformat(),
    }
    prefs["notifications"].append(notif)
    data["users"][username]["preferences"] = prefs
    _save_auth(data)


def mark_notifications_read(username: str) -> None:
    """Mark all notifications as read for a user."""
    data = _load_auth()
    if username not in data["users"]:
        return
    prefs = data["users"][username].get("preferences", {})
    prefs = _ensure_new_prefs(prefs)
    all_ids = [n["id"] for n in prefs["notifications"]]
    prefs["notifications_read"] = list(set(prefs.get("notifications_read", []) + all_ids))
    data["users"][username]["preferences"] = prefs
    _save_auth(data)


def clear_notifications(username: str) -> None:
    """Remove all notifications for a user."""
    data = _load_auth()
    if username not in data["users"]:
        return
    prefs = data["users"][username].get("preferences", {})
    prefs = _ensure_new_prefs(prefs)
    prefs["notifications"] = []
    prefs["notifications_read"] = []
    data["users"][username]["preferences"] = prefs
    _save_auth(data)


def set_last_weekly_report(username: str) -> None:
    """Record that the weekly report was sent now."""
    data = _load_auth()
    if username not in data["users"]:
        return
    prefs = data["users"][username].get("preferences", {})
    prefs = _ensure_new_prefs(prefs)
    prefs["last_weekly_report"] = datetime.now().isoformat()
    data["users"][username]["preferences"] = prefs
    _save_auth(data)
