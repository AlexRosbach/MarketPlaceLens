from __future__ import annotations

import json
import os
import base64
import hashlib
import sqlite3
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterator

from .config import settings


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def encode_list(value: list[str] | None) -> str:
    return json.dumps(value or [])


def decode_list(value: str | None) -> list[str]:
    if not value:
        return []
    try:
        loaded = json.loads(value)
    except json.JSONDecodeError:
        return []
    return [str(item) for item in loaded if str(item).strip()]


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    Path(os.path.dirname(settings.db_path) or ".").mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(settings.db_path, timeout=30)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA busy_timeout = 30000")
    db.execute("PRAGMA foreign_keys = ON")
    try:
        yield db
        db.commit()
    finally:
        db.close()


def init_db() -> None:
    with connect() as db:
        db.execute("PRAGMA journal_mode = WAL")
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS watch_profiles (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              name TEXT NOT NULL,
              enabled INTEGER NOT NULL DEFAULT 1,
              source_type TEXT NOT NULL DEFAULT 'html',
              search_url TEXT NOT NULL,
              poll_interval_minutes INTEGER NOT NULL DEFAULT 60,
              include_keywords TEXT NOT NULL DEFAULT '[]',
              exclude_keywords TEXT NOT NULL DEFAULT '[]',
              required_keywords TEXT NOT NULL DEFAULT '[]',
              excluded_categories TEXT NOT NULL DEFAULT '[]',
              min_price REAL,
              max_price REAL,
              max_listing_age_days INTEGER NOT NULL DEFAULT 365,
              location_hint TEXT NOT NULL DEFAULT '',
              notify_telegram INTEGER NOT NULL DEFAULT 1,
              notify_webhook INTEGER NOT NULL DEFAULT 0,
              user_id INTEGER REFERENCES users(id),
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL,
              last_run_at TEXT
            );

            CREATE TABLE IF NOT EXISTS listings (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              source_type TEXT NOT NULL,
              source_listing_id TEXT NOT NULL,
              profile_id INTEGER NOT NULL REFERENCES watch_profiles(id) ON DELETE CASCADE,
              title TEXT NOT NULL,
              price_text TEXT NOT NULL DEFAULT '',
              price_value REAL,
              location_text TEXT NOT NULL DEFAULT '',
              category_text TEXT NOT NULL DEFAULT '',
              posted_at_text TEXT NOT NULL DEFAULT '',
              description_snippet TEXT NOT NULL DEFAULT '',
              listing_url TEXT NOT NULL,
              thumbnail_url TEXT NOT NULL DEFAULT '',
              content_hash TEXT NOT NULL,
              first_seen_at TEXT NOT NULL,
              last_seen_at TEXT NOT NULL,
              status TEXT NOT NULL DEFAULT 'new',
              watchlisted INTEGER NOT NULL DEFAULT 0,
              user_hidden INTEGER NOT NULL DEFAULT 0,
              contacted INTEGER NOT NULL DEFAULT 0,
              availability_status TEXT NOT NULL DEFAULT 'unknown',
              availability_checked_at TEXT,
              score INTEGER NOT NULL DEFAULT 0,
              filter_reason TEXT NOT NULL DEFAULT '',
              notified_at TEXT,
              UNIQUE(profile_id, source_listing_id),
              UNIQUE(profile_id, content_hash)
            );

            CREATE TABLE IF NOT EXISTS app_settings (
              key TEXT PRIMARY KEY,
              value TEXT NOT NULL DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS auth_sessions (
              token_hash TEXT PRIMARY KEY,
              user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
              password_hash TEXT NOT NULL,
              expires_at INTEGER NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_auth_sessions_expires ON auth_sessions(expires_at);
            CREATE TABLE IF NOT EXISTS users (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              username TEXT NOT NULL UNIQUE,
              password_hash TEXT NOT NULL,
              role TEXT NOT NULL DEFAULT 'user',
              enabled INTEGER NOT NULL DEFAULT 1,
              display_name TEXT NOT NULL DEFAULT '',
              buyer_location TEXT NOT NULL DEFAULT '',
              contact_hint TEXT NOT NULL DEFAULT '',
              inquiry_signature TEXT NOT NULL DEFAULT '',
              default_watchlist_id INTEGER REFERENCES watchlists(id),
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL,
              last_login_at TEXT
            );

            CREATE TABLE IF NOT EXISTS watchlists (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              name TEXT NOT NULL UNIQUE,
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS listing_watchlists (
              listing_id INTEGER NOT NULL REFERENCES listings(id) ON DELETE CASCADE,
              watchlist_id INTEGER NOT NULL REFERENCES watchlists(id) ON DELETE CASCADE,
              created_at TEXT NOT NULL,
              PRIMARY KEY (listing_id, watchlist_id)
            );

            CREATE TABLE IF NOT EXISTS run_logs (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              profile_id INTEGER REFERENCES watch_profiles(id) ON DELETE SET NULL,
              profile_name TEXT NOT NULL DEFAULT '',
              status TEXT NOT NULL,
              fetched INTEGER NOT NULL DEFAULT 0,
              new_count INTEGER NOT NULL DEFAULT 0,
              hidden_count INTEGER NOT NULL DEFAULT 0,
              duplicate_count INTEGER NOT NULL DEFAULT 0,
              notified_count INTEGER NOT NULL DEFAULT 0,
              error_message TEXT NOT NULL DEFAULT '',
              started_at TEXT NOT NULL,
              finished_at TEXT NOT NULL
            );
            """
        )
        ensure_column(db, "listings", "watchlisted", "INTEGER NOT NULL DEFAULT 0")
        ensure_column(db, "listings", "user_hidden", "INTEGER NOT NULL DEFAULT 0")
        ensure_column(db, "listings", "contacted", "INTEGER NOT NULL DEFAULT 0")
        ensure_column(db, "listings", "availability_status", "TEXT NOT NULL DEFAULT 'unknown'")
        ensure_column(db, "listings", "availability_checked_at", "TEXT")
        ensure_column(db, "listings", "ai_assessment_text", "TEXT NOT NULL DEFAULT ''")
        ensure_column(db, "listings", "ai_assessed_at", "TEXT")
        ensure_column(db, "listings", "ai_assessment_key", "TEXT NOT NULL DEFAULT ''")
        ensure_column(db, "listings", "target_price", "REAL")
        ensure_column(db, "watch_profiles", "notify_webhook", "INTEGER NOT NULL DEFAULT 0")
        ensure_column(db, "watch_profiles", "user_id", "INTEGER REFERENCES users(id)")
        ensure_column(db, "watch_profiles", "max_listing_age_days", "INTEGER NOT NULL DEFAULT 365")
        ensure_column(db, "watch_profiles", "consecutive_failures", "INTEGER NOT NULL DEFAULT 0")
        ensure_column(db, "watch_profiles", "retry_after", "TEXT")
        ensure_column(db, "users", "display_name", "TEXT NOT NULL DEFAULT ''")
        ensure_column(db, "users", "buyer_location", "TEXT NOT NULL DEFAULT ''")
        ensure_column(db, "users", "contact_hint", "TEXT NOT NULL DEFAULT ''")
        ensure_column(db, "users", "inquiry_signature", "TEXT NOT NULL DEFAULT ''")
        ensure_column(db, "users", "default_watchlist_id", "INTEGER REFERENCES watchlists(id)")
        db.execute(
            """
            DELETE FROM listings
            WHERE source_type = 'kleinanzeigen'
              AND (
                listing_url NOT LIKE '%/s-anzeige/%'
                OR lower(title) LIKE '%passwort vergessen%'
                OR lower(listing_url) LIKE '%passwort-vergessen%'
                OR lower(listing_url) LIKE '%/m-passwort%'
                OR lower(title) LIKE '%erstelle ein konto%'
                OR lower(title) LIKE '%konto erstellen%'
                OR lower(title) LIKE '%registrieren%'
                OR lower(listing_url) LIKE '%konto-erstellen%'
                OR lower(listing_url) LIKE '%registrieren%'
                OR lower(listing_url) LIKE '%/m-benutzer-anmeldung%'
              )
            """
        )
        db.executescript("""
            CREATE INDEX IF NOT EXISTS idx_listings_profile_status_checked ON listings(profile_id, status, availability_checked_at);
            CREATE INDEX IF NOT EXISTS idx_listings_first_seen ON listings(first_seen_at DESC);
            CREATE INDEX IF NOT EXISTS idx_profiles_enabled_run ON watch_profiles(enabled, last_run_at);
            CREATE INDEX IF NOT EXISTS idx_profiles_owner ON watch_profiles(user_id);
            CREATE INDEX IF NOT EXISTS idx_run_logs_profile_finished ON run_logs(profile_id, finished_at DESC);
            CREATE TABLE IF NOT EXISTS listing_price_history (
                id INTEGER PRIMARY KEY, listing_id INTEGER NOT NULL REFERENCES listings(id) ON DELETE CASCADE,
                price_value REAL NOT NULL, observed_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_price_history_listing ON listing_price_history(listing_id, observed_at DESC);
            CREATE TABLE IF NOT EXISTS notification_outbox (
                id INTEGER PRIMARY KEY, listing_id INTEGER NOT NULL REFERENCES listings(id) ON DELETE CASCADE,
                channel TEXT NOT NULL, event_key TEXT NOT NULL, reason TEXT NOT NULL,
                state TEXT NOT NULL DEFAULT 'pending', attempts INTEGER NOT NULL DEFAULT 0,
                next_attempt_at TEXT NOT NULL, UNIQUE(listing_id, channel, event_key)
            );
            CREATE INDEX IF NOT EXISTS idx_notification_due ON notification_outbox(state, next_attempt_at);
        """)
        ensure_admin_user(db)
        assign_unowned_profiles_to_admin(db)
        default_watchlist_id = ensure_default_watchlist(db)
        db.execute(
            """
            INSERT OR IGNORE INTO listing_watchlists(listing_id, watchlist_id, created_at)
            SELECT id, ?, ?
            FROM listings
            WHERE watchlisted = 1
            """,
            (default_watchlist_id, utc_now()),
        )
        defaults = {
            "setup_complete": "0",
            "telegram_bot_token": settings.telegram_bot_token,
            "telegram_chat_id": settings.telegram_chat_id,
            "webhook_url": settings.webhook_url,
            "global_rate_limit_seconds": "20",
            "default_watchlist_id": str(default_watchlist_id),
            "ai_enabled": "0",
            "ai_listing_assessments_enabled": "0",
            "ai_listing_assessments_auto_enabled": "0",
            "ai_listing_assessments_new_enabled": "0",
            "ai_provider": "openai",
            "ai_api_key": "",
            "ai_base_url": "",
            "ai_model": "gpt-4o-mini",
            "ai_tone": "normal",
        }
        for key, value in defaults.items():
            db.execute(
                "INSERT OR IGNORE INTO app_settings(key, value) VALUES (?, ?)",
                (key, value),
            )


def row_to_profile(row: sqlite3.Row) -> dict[str, Any]:
    data = dict(row)
    for key in ["include_keywords", "exclude_keywords", "required_keywords", "excluded_categories"]:
        data[key] = decode_list(data.get(key))
    data["enabled"] = bool(data["enabled"])
    data["notify_telegram"] = bool(data["notify_telegram"])
    data["notify_webhook"] = bool(data.get("notify_webhook", False))
    return data


def row_to_listing(row: sqlite3.Row) -> dict[str, Any]:
    data = dict(row)
    data["watchlisted"] = bool(data.get("watchlisted", False))
    data["user_hidden"] = bool(data.get("user_hidden", False))
    data["contacted"] = bool(data.get("contacted", False))
    data["watchlists"] = []
    return data


def ensure_column(db: sqlite3.Connection, table: str, column: str, definition: str) -> None:
    columns = {row["name"] for row in db.execute(f"PRAGMA table_info({table})").fetchall()}
    if column not in columns:
        db.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def ensure_default_watchlist(db: sqlite3.Connection) -> int:
    now = utc_now()
    row = db.execute("SELECT id FROM watchlists ORDER BY id LIMIT 1").fetchone()
    if row:
        return int(row["id"])
    cursor = db.execute(
        "INSERT INTO watchlists(name, created_at, updated_at) VALUES (?, ?, ?)",
        ("Watchlist", now, now),
    )
    return int(cursor.lastrowid)


def ensure_admin_user(db: sqlite3.Connection) -> None:
    now = utc_now()
    row = db.execute("SELECT id FROM users WHERE role = 'admin' LIMIT 1").fetchone()
    if row:
        return
    if len(settings.admin_password) < 8 or settings.admin_password.lower() == "admin":
        return
    password_hash = hash_password_for_bootstrap(settings.admin_password)
    db.execute(
        """
        INSERT OR IGNORE INTO users(username, password_hash, role, enabled, created_at, updated_at)
        VALUES (?, ?, 'admin', 1, ?, ?)
        """,
        (settings.admin_username, password_hash, now, now),
    )
    db.execute(
        "INSERT INTO app_settings(key, value) VALUES ('setup_complete', '1') ON CONFLICT(key) DO UPDATE SET value = '1'"
    )


def assign_unowned_profiles_to_admin(db: sqlite3.Connection) -> None:
    row = db.execute("SELECT id FROM users WHERE role = 'admin' ORDER BY id LIMIT 1").fetchone()
    if not row:
        return
    db.execute("UPDATE watch_profiles SET user_id = ? WHERE user_id IS NULL", (row["id"],))


def hash_password_for_bootstrap(password: str) -> str:
    salt = os.urandom(16)
    iterations = 260000
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return ".".join(
        [
            "pbkdf2_sha256",
            str(iterations),
            base64.urlsafe_b64encode(salt).decode("ascii"),
            base64.urlsafe_b64encode(digest).decode("ascii"),
        ]
    )
