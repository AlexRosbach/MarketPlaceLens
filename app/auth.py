from __future__ import annotations

import base64
import os
import hmac
from hashlib import sha256
import hashlib
import secrets
import time

from .config import settings
from .database import connect


COOKIE_NAME = "marketplacelens_session"
PASSWORD_ITERATIONS = 260000


SESSION_TTL = 14 * 24 * 60 * 60


def create_session(username: str) -> str:
    token = secrets.token_urlsafe(32)
    digest = hmac.new(settings.session_secret.encode(), token.encode(), sha256).hexdigest()
    with connect() as db:
        db.execute("DELETE FROM auth_sessions WHERE expires_at <= ?", (int(time.time()),))
        db.execute("""INSERT INTO auth_sessions(token_hash, user_id, password_hash, expires_at)
                      SELECT ?, id, password_hash, ? FROM users WHERE username = ? AND enabled = 1""",
                   (digest, int(time.time()) + SESSION_TTL, username))
    return token


def revoke_session(value: str | None) -> None:
    if value and len(value) <= 128:
        digest = hmac.new(settings.session_secret.encode(), value.encode(), sha256).hexdigest()
        with connect() as db:
            db.execute("DELETE FROM auth_sessions WHERE token_hash = ?", (digest,))


def valid_session(value: str | None) -> bool:
    return current_user_from_session(value) is not None


def current_user_from_session(value: str | None) -> dict | None:
    if not value or len(value) > 128:
        return None
    digest = hmac.new(settings.session_secret.encode(), value.encode(), sha256).hexdigest()
    try:
        with connect() as db:
            row = db.execute("""
                SELECT u.id, u.username, u.role, u.enabled, u.display_name, u.buyer_location,
                       u.contact_hint, u.inquiry_signature
                FROM auth_sessions s JOIN users u ON u.id = s.user_id
                WHERE s.token_hash = ? AND s.expires_at > ? AND u.enabled = 1
                  AND s.password_hash = u.password_hash
                """, (digest, int(time.time()))).fetchone()
    except Exception:
        return None
    return dict(row) if row else None


def valid_credentials(username: str, password: str) -> bool:
    try:
        with connect() as db:
            row = db.execute(
                "SELECT password_hash, enabled FROM users WHERE username = ?",
                (username,),
            ).fetchone()
    except Exception:
        row = None
    if row:
        return bool(row["enabled"]) and verify_password(password, row["password_hash"])
    return False


def get_stored_password_hash() -> str:
    try:
        with connect() as db:
            row = db.execute("SELECT value FROM app_settings WHERE key = 'admin_password_hash'").fetchone()
    except Exception:
        return ""
    return row["value"] if row else ""


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PASSWORD_ITERATIONS)
    return ".".join(
        [
            "pbkdf2_sha256",
            str(PASSWORD_ITERATIONS),
            base64.urlsafe_b64encode(salt).decode("ascii"),
            base64.urlsafe_b64encode(digest).decode("ascii"),
        ]
    )


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        algorithm, iterations, salt, digest = stored_hash.split(".", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        expected = base64.urlsafe_b64decode(digest.encode("ascii"))
        actual = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            base64.urlsafe_b64decode(salt.encode("ascii")),
            int(iterations),
        )
    except Exception:
        return False
    return hmac.compare_digest(actual, expected)
