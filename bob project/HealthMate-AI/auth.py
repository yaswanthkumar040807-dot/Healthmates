"""
HealthMate AI — Authentication Module
Handles registration, login, and password hashing.
"""
import re
import logging
from typing import Optional, Tuple

import bcrypt

import database as db

logger = logging.getLogger(__name__)

_USERNAME_RE = re.compile(r"^[a-zA-Z0-9_]{3,30}$")
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode(), hashed.encode())
    except Exception:
        return False


def validate_registration(username: str, email: str, password: str, confirm: str) -> Tuple[bool, str]:
    if not _USERNAME_RE.match(username):
        return False, "Username must be 3–30 characters: letters, digits, or underscores."
    if not _EMAIL_RE.match(email):
        return False, "Please enter a valid email address."
    if len(password) < 8:
        return False, "Password must be at least 8 characters."
    if password != confirm:
        return False, "Passwords do not match."
    return True, ""


def register_user(username: str, email: str, password: str, confirm: str) -> Tuple[bool, str]:
    ok, msg = validate_registration(username, email, password, confirm)
    if not ok:
        return False, msg

    existing = db.get_user_by_username(username)
    if existing:
        return False, "That username is already taken."

    try:
        pw_hash = hash_password(password)
        db.create_user(username, email, pw_hash)
        logger.info("New user registered: %s", username)
        return True, "Account created successfully."
    except Exception as exc:
        logger.error("Registration error: %s", exc)
        return False, "Registration failed. Please try again."


def login_user(username: str, password: str) -> Tuple[bool, str, Optional[int]]:
    if not username or not password:
        return False, "Please enter your username and password.", None

    user = db.get_user_by_username(username)
    if not user:
        return False, "Invalid username or password.", None

    if not verify_password(password, user["password_hash"]):
        return False, "Invalid username or password.", None

    return True, "Login successful.", user["id"]
